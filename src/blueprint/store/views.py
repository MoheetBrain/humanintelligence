"""SQL views over the store.

Each view answers a question somebody actually needs to ask, and several exist
specifically to make a weakness visible rather than to summarise a strength:

* ``v_claims_per_target`` puts the claim count next to the null-result, evidence-gap and
  reporting-gap counts, so a well-connected target cannot be read as a well-evidenced
  one.
* ``v_null_results_by_target`` lists the performed attempts that found nothing. Without
  a view of its own, a null is a row in a table nobody queries.
* ``v_coverage_by_facet`` shows graded versus not-assessed versus zero per facet. A
  facet nobody examined and a facet searched with nothing found are different states
  and this is where that shows.
* ``v_reporting_gaps`` surfaces registered interventions that completed without posted
  results — publication bias as data rather than as a remark.
* ``v_shared_sources`` is what the red team's citation-dependence check needs: which
  sources more than one agent leaned on.
* ``v_unsupported_edges`` lists claim-derived edges that do NOT count as support, with
  the reason, so nobody concludes an edge was overlooked.
"""

from __future__ import annotations

# View name -> SQL. Ordered so a view may depend on one defined before it.
VIEWS: dict[str, str] = {
    "v_claims_per_target": """
        SELECT
            t.target_id,
            t.symbol,
            t.lead_atlas,
            t.dossier_depth,
            t.claim_count,
            t.human_claim_count,
            t.distinct_source_count,
            t.facets_graded,
            t.facets_not_assessed,
            t.facets_zero,
            t.null_result_count,
            t.evidence_gap_count,
            t.reporting_gap_count,
            CASE
                WHEN t.claim_count = 0 THEN 'no claims'
                WHEN t.human_claim_count = 0 THEN 'no human evidence'
                WHEN t.facets_graded = 0 THEN 'no facet graded'
                ELSE 'has graded evidence'
            END AS coverage_note
        FROM targets t
        ORDER BY t.target_id
    """,
    "v_evidence_by_species_and_life_stage": """
        SELECT
            c.life_stage,
            e.species,
            c.baseline_context,
            COUNT(*) AS evidence_items,
            COUNT(DISTINCT c.claim_id) AS claims,
            COUNT(DISTINCT e.source_id) AS distinct_sources,
            SUM(CASE WHEN e.endpoint_measured = 'measured' THEN 1 ELSE 0 END)
                AS endpoints_measured,
            SUM(CASE WHEN e.endpoint_measured = 'not_measured_in_protocol' THEN 1 ELSE 0 END)
                AS endpoints_not_measured
        FROM evidence_items e
        JOIN claims c ON c.claim_id = e.claim_id
        GROUP BY c.life_stage, e.species, c.baseline_context
        ORDER BY evidence_items DESC, c.life_stage, e.species
    """,
    "v_null_results_by_target": """
        SELECT
            c.topic AS target_topic,
            c.claim_id,
            c.subject,
            c.predicate,
            c.object,
            c.negated_relation,
            c.claim_type,
            c.human_relevance,
            c.distinct_source_count,
            (
                SELECT COUNT(*) FROM evidence_items e
                WHERE e.claim_id = c.claim_id
                  AND e.endpoint_measured = 'measured'
                  AND e.evidence_role IN ('null_result', 'contradicts')
            ) AS qualifying_evidence_items
        FROM claims c
        WHERE c.predicate = 'NO_DETECTED_EFFECT_ON'
        ORDER BY c.topic, c.claim_id
    """,
    "v_evidence_gaps": """
        SELECT
            c.claim_id,
            c.topic AS target_topic,
            c.object AS unmeasured_endpoint,
            c.statement,
            c.distinct_source_count
        FROM claims c
        WHERE c.claim_type = 'evidence_gap'
        ORDER BY c.claim_id
    """,
    "v_reporting_gaps": """
        SELECT
            a.target_id,
            a.facet,
            a.assessed_by,
            a.level,
            a.reporting_gap_count,
            a.reporting_gap_refs,
            a.search_basis
        FROM assessments a
        WHERE a.reporting_gap_count > 0
        ORDER BY a.target_id, a.facet
    """,
    "v_sources_shared_across_agents": """
        SELECT
            s.source_id,
            s.title,
            s.year,
            s.registration_count,
            s.registered_in_files,
            (SELECT COUNT(DISTINCT e.claim_id) FROM evidence_items e
             WHERE e.source_id = s.source_id) AS citing_claims
        FROM sources s
        WHERE s.is_shared_across_agents
        ORDER BY s.registration_count DESC, s.source_id
    """,
    "v_uncited_sources": """
        SELECT
            s.source_id,
            s.added_by,
            s.title,
            s.year
        FROM sources s
        WHERE NOT EXISTS (
            SELECT 1 FROM evidence_items e WHERE e.source_id = s.source_id
        )
        ORDER BY s.added_by, s.source_id
    """,
    "v_coverage_by_facet": """
        SELECT
            a.facet,
            COUNT(*) AS rows_written,
            SUM(CASE WHEN a.assessment_status = 'assessed' THEN 1 ELSE 0 END) AS assessed,
            SUM(CASE WHEN a.assessment_status = 'not_assessed' THEN 1 ELSE 0 END)
                AS not_assessed,
            SUM(CASE WHEN a.level = 0 THEN 1 ELSE 0 END) AS searched_found_nothing,
            SUM(CASE WHEN a.level >= 3 THEN 1 ELSE 0 END) AS substantial_or_strong,
            SUM(CASE WHEN a.counter_level >= 1 THEN 1 ELSE 0 END) AS with_counter_evidence,
            SUM(a.reporting_gap_count) AS reporting_gaps
        FROM assessments a
        GROUP BY a.facet
        ORDER BY a.facet
    """,
    "v_edges_by_provenance": """
        SELECT
            layer,
            provenance_class,
            COUNT(*) AS edges,
            SUM(CASE WHEN is_null_result THEN 1 ELSE 0 END) AS null_results,
            SUM(CASE WHEN counts_as_support THEN 1 ELSE 0 END) AS support_edges,
            SUM(CASE WHEN asserts_effect THEN 1 ELSE 0 END) AS effect_asserting
        FROM edges
        GROUP BY layer, provenance_class
        ORDER BY layer, provenance_class
    """,
    "v_unsupported_edges": """
        SELECT
            subject,
            predicate,
            object,
            direction,
            is_null_result,
            claim_ids,
            CASE
                WHEN is_null_result
                    THEN 'null result: a performed attempt that found no effect'
                WHEN direction IS NULL
                    THEN 'no direction stated, so nothing is asserted to have changed'
                WHEN direction IN ('no_change', 'unclear')
                    THEN 'direction ' || direction || ' does not assert a change'
                ELSE 'other'
            END AS why_not_support
        FROM edges
        WHERE claim_count > 0 AND NOT counts_as_support
        ORDER BY subject, predicate, object
    """,
    "v_state_variable_measurability": """
        SELECT
            domain,
            COUNT(*) AS variables,
            SUM(CASE WHEN best_proxy_status = 'established_human_proxy' THEN 1 ELSE 0 END)
                AS established_human,
            SUM(CASE WHEN best_proxy_status = 'research_proxy' THEN 1 ELSE 0 END)
                AS research_grade,
            SUM(CASE WHEN best_proxy_status = 'animal_only_proxy' THEN 1 ELSE 0 END)
                AS animal_only,
            SUM(CASE WHEN best_proxy_status = 'theoretical_construct' THEN 1 ELSE 0 END)
                AS theoretical,
            SUM(CASE WHEN best_proxy_status IS NULL THEN 1 ELSE 0 END) AS no_proxy_at_all,
            SUM(CASE WHEN response_shape = 'unknown' THEN 1 ELSE 0 END) AS shape_unknown
        FROM state_variables
        GROUP BY domain
        ORDER BY domain
    """,
    "v_claims_by_human_relevance": """
        SELECT
            human_relevance,
            general_intelligence_relevance,
            COUNT(*) AS claims,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN status <> 'active' THEN 1 ELSE 0 END) AS not_active
        FROM claims
        GROUP BY human_relevance, general_intelligence_relevance
        ORDER BY claims DESC, human_relevance
    """,
}
