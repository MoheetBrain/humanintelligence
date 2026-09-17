"""Table specifications and row builders for the evidence store.

Design rules:

* **One row per record, flattened only where flattening is lossless.** Nested blocks
  that a query needs to filter on (``context``, ``translation``, ``uncertainty``) are
  flattened into columns; everything else is kept as a JSON string so nothing is
  silently dropped.
* **Rows are sorted and columns are ordered.** Two builds over one tree produce
  byte-identical Parquet, which is what makes the manifest checksums meaningful.
* **Nulls stay null.** A missing value is never coerced to ``0`` or ``""`` (contract
  P8): ``not_assessed`` and ``unknown`` are first-class and must survive the round trip
  into SQL, because a query that cannot tell "zero" from "nobody looked" will mislead.
* **Every list becomes a JSON string plus a count column.** DuckDB can query the JSON,
  and the count is there because that is what almost every question actually wants.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from blueprint import loaders
from blueprint.graph.compile import CompiledGraph


def _json(value: Any) -> str:
    """Deterministic JSON for a nested value."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _list_of(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return sorted(str(v) for v in value)
    return [str(value)]


def sources_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per registered source, with its registering agents."""
    rows: list[dict[str, Any]] = []
    for source_id, record in repo.sources.items():
        raw = record.raw
        identifiers = raw.get("identifiers") or {}
        registrations = repo.shared_sources.get(source_id, (record.path.split("#")[0],))
        rows.append(
            {
                "source_id": source_id,
                "source_type": raw.get("source_type"),
                "title": raw.get("title"),
                "year": raw.get("year"),
                "first_author": raw.get("first_author"),
                "container": raw.get("container"),
                "pmid": identifiers.get("pmid"),
                "doi": identifiers.get("doi"),
                "nct_id": identifiers.get("nct_id") or identifiers.get("nct"),
                "gcst": identifiers.get("gcst"),
                "pmcid": identifiers.get("pmcid") or identifiers.get("pmc"),
                "added_by": raw.get("added_by"),
                "added_on": raw.get("added_on"),
                "retrieval_method": (raw.get("retrieval") or {}).get("method"),
                # Duplicate registration across agents is allowed and preferred
                # (contract §1.3); the store deduplicates to one row and records how
                # many agents registered it, so duplication cannot inflate a count.
                "registration_count": len(registrations),
                "registered_in_files": _json(sorted(registrations)),
                "is_shared_across_agents": source_id in repo.shared_sources,
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["source_id"])


def claims_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per claim, with the fields a query needs flattened out."""
    rows: list[dict[str, Any]] = []
    for claim_id, record in repo.claims.items():
        raw = record.raw
        context = raw.get("context") or {}
        translation = raw.get("translation") or {}
        uncertainty = raw.get("uncertainty") or {}
        attribution = raw.get("causal_attribution") or {}
        evidence = [i for i in (raw.get("evidence") or []) if isinstance(i, dict)]
        sources = sorted({str(i["source_id"]) for i in evidence if i.get("source_id")})
        rows.append(
            {
                "claim_id": claim_id,
                "agent": claim_id.split(":")[1] if claim_id.count(":") > 1 else None,
                "topic": claim_id.split(":")[2] if claim_id.count(":") > 2 else None,
                "statement": raw.get("statement"),
                "subject": raw.get("subject"),
                "predicate": raw.get("predicate"),
                "object": raw.get("object"),
                "claim_type": raw.get("claim_type"),
                "direction": raw.get("direction"),
                "direction_context": raw.get("direction_context"),
                "negated_relation": raw.get("negated_relation"),
                "phenotype_class": raw.get("phenotype_class"),
                "life_stage": context.get("life_stage"),
                "baseline_context": context.get("baseline_context"),
                "species": _json(_list_of(context.get("species"))),
                "species_count": context.get("species_count"),
                "phylogenetic_control": context.get("phylogenetic_control"),
                "causal_basis": attribution.get("basis"),
                "locus_to_gene_resolved": attribution.get("locus_to_gene_resolved"),
                "adult_relevance": translation.get("adult_relevance"),
                "healthy_baseline": translation.get("healthy_baseline"),
                "supra_normal": translation.get("supra_normal"),
                "human_relevance": translation.get("human_relevance"),
                "general_intelligence_relevance": translation.get(
                    "general_intelligence_relevance"
                ),
                "uncertainty_representation": uncertainty.get("representation"),
                "uncertainty_level": uncertainty.get("level"),
                "calibration_status": uncertainty.get("calibration_status"),
                "status": raw.get("status"),
                "evidence_count": len(evidence),
                "distinct_source_count": len(sources),
                "source_ids": _json(sources),
                "created_by": (raw.get("provenance") or {}).get("created_by"),
                "created_on": (raw.get("provenance") or {}).get("created_on"),
                "method": (raw.get("provenance") or {}).get("method"),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["claim_id"])


def evidence_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per evidence item, keyed to its claim."""
    rows: list[dict[str, Any]] = []
    for claim_id, record in repo.claims.items():
        local = claim_id.split(":", 1)[1] if ":" in claim_id else claim_id
        for position, item in enumerate(record.raw.get("evidence") or [], start=1):
            if not isinstance(item, dict):
                continue
            effect = item.get("effect_size") or {}
            sample = item.get("sample_size") or {}
            extraction = item.get("extraction") or {}
            rows.append(
                {
                    "evidence_id": item.get("evidence_id") or f"EVD:{local}#{position}",
                    "claim_id": claim_id,
                    "position": position,
                    "source_id": item.get("source_id"),
                    "design": item.get("design"),
                    "species": item.get("species"),
                    "population": item.get("population"),
                    "endpoint": item.get("endpoint"),
                    "endpoint_category": item.get("endpoint_category"),
                    "endpoint_measured": item.get("endpoint_measured", "unknown"),
                    "effect_direction": item.get("effect_direction"),
                    "effect_metric": effect.get("metric"),
                    "effect_as_reported": effect.get("as_reported"),
                    "effect_value": effect.get("value"),
                    "effect_p_value": effect.get("p_value"),
                    "sample_size_value": sample.get("value"),
                    "sample_size_reported_as": sample.get("reported_as"),
                    "replication_status": item.get("replication_status"),
                    "evidence_role": item.get("evidence_role"),
                    "extraction_basis": extraction.get("basis"),
                    "extracted_by": extraction.get("extracted_by"),
                    "content_checked": extraction.get("content_checked"),
                    "note": item.get("note"),
                }
            )
    return sorted(rows, key=lambda r: (r["claim_id"], r["position"]))


def targets_rows(repo: loaders.Repository, compiled: CompiledGraph) -> list[dict[str, Any]]:
    """One row per dossier, with compile-time identifiers and coverage attached.

    The coverage columns are here rather than in a separate table because the point of
    them is that a reader cannot see a target without also seeing how thin its evidence
    is — and a join is a step a reader can skip.
    """
    rows: list[dict[str, Any]] = []
    for target_id, record in repo.targets.items():
        raw = record.raw
        identifiers = compiled.target_identifiers.get(target_id, {})
        coverage = compiled.target_coverage.get(target_id, {})
        hypothesis = raw.get("control_point_hypothesis") or {}
        rows.append(
            {
                "target_id": target_id,
                "symbol": raw.get("symbol"),
                "lead_atlas": raw.get("lead_atlas"),
                "seed_origin": raw.get("seed_origin"),
                "dossier_depth": raw.get("dossier_depth"),
                "target_class": raw.get("target_class"),
                "status": raw.get("status"),
                "developmental_confound": raw.get("developmental_confound"),
                "hgnc_id": identifiers.get("hgnc_id"),
                "ensembl_gene_id": identifiers.get("ensembl_gene_id"),
                "entrez_id": identifiers.get("entrez_id"),
                "uniprot_ids": _json(identifiers.get("uniprot_ids") or []),
                "identifier_provenance": identifiers.get("identifier_provenance"),
                "proposed_modulation": hypothesis.get("proposed_modulation"),
                "mechanism_chain_length": len(hypothesis.get("mechanism_chain") or []),
                "known_liability_count": len(raw.get("known_liabilities") or []),
                # --- honesty columns: never present a score without these ---
                "claim_count": coverage.get("claim_count", 0),
                "distinct_source_count": coverage.get("distinct_source_count", 0),
                "human_claim_count": coverage.get("human_claim_count", 0),
                "facets_graded": coverage.get("facets_graded", 0),
                "facets_not_assessed": coverage.get("facets_not_assessed", 0),
                "facets_zero": coverage.get("facets_zero", 0),
                "null_result_count": coverage.get("null_result_count", 0),
                "evidence_gap_count": coverage.get("evidence_gap_count", 0),
                "reporting_gap_count": coverage.get("reporting_gap_count", 0),
                "reporting_gap_refs": _json(coverage.get("reporting_gap_refs") or []),
                "audit_count": coverage.get("audit_count", 0),
                "audit_verdicts": _json(coverage.get("audit_verdicts") or []),
                "audit_checks_flagged": coverage.get("audit_checks_flagged", 0),
                "audit_checks_failed": coverage.get("audit_checks_failed", 0),
                "audit_critical_findings": coverage.get("audit_critical_findings", 0),
                "audit_major_findings": coverage.get("audit_major_findings", 0),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["target_id"])


def assessments_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per graded facet.

    ``level`` stays nullable: ``not_assessed`` must not become ``0`` in SQL, because the
    contract spends real effort keeping "nobody looked" and "searched and found nothing"
    apart and a coerced zero would erase that in every downstream query.
    """
    rows: list[dict[str, Any]] = []
    for record in repo.assessments:
        raw = record.raw
        target_id = raw.get("target_id")
        for facet in raw.get("facets") or []:
            if not isinstance(facet, dict):
                continue
            rows.append(
                {
                    "target_id": target_id,
                    "facet": facet.get("facet"),
                    "assessed_by": raw.get("assessed_by"),
                    "assessed_on": raw.get("assessed_on"),
                    "rubric": raw.get("rubric"),
                    "assessment_status": facet.get("assessment_status"),
                    "level": facet.get("level"),
                    "counter_level": facet.get("counter_level"),
                    "rationale": facet.get("rationale"),
                    "counter_rationale": facet.get("counter_rationale"),
                    "search_basis": facet.get("search_basis"),
                    "limiting_factor": facet.get("limiting_factor"),
                    "evidence_basis": facet.get("evidence_basis"),
                    "claim_ref_count": len(facet.get("claim_refs") or []),
                    "counter_claim_ref_count": len(facet.get("counter_claim_refs") or []),
                    "source_ref_count": len(facet.get("source_refs") or []),
                    "reporting_gap_count": len(facet.get("reporting_gap_refs") or []),
                    "claim_refs": _json(_list_of(facet.get("claim_refs"))),
                    "counter_claim_refs": _json(_list_of(facet.get("counter_claim_refs"))),
                    "source_refs": _json(_list_of(facet.get("source_refs"))),
                    "reporting_gap_refs": _json(_list_of(facet.get("reporting_gap_refs"))),
                    "record_path": record.path,
                }
            )
    return sorted(rows, key=lambda r: (str(r["target_id"]), str(r["facet"])))


def audits_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per audit record."""
    rows: list[dict[str, Any]] = []
    for audit_id, record in repo.audits.items():
        raw = record.raw
        scope = raw.get("scope") or {}
        checks = [c for c in (raw.get("checks") or []) if isinstance(c, dict)]
        findings = [f for f in (raw.get("findings") or []) if isinstance(f, dict)]
        rows.append(
            {
                "audit_id": audit_id,
                "scope_kind": scope.get("kind"),
                "scope_id": scope.get("id"),
                "audited_by": raw.get("audited_by"),
                "audited_on": raw.get("audited_on"),
                "verdict": raw.get("verdict"),
                "check_count": len(checks),
                "checks_failed": sum(1 for c in checks if c.get("result") == "fail"),
                "checks_flagged": sum(1 for c in checks if c.get("result") == "flag"),
                "checks_passed": sum(1 for c in checks if c.get("result") == "pass"),
                "checks_not_applicable": sum(
                    1 for c in checks if c.get("result") == "not_applicable"
                ),
                "finding_count": len(findings),
                "critical_findings": sum(1 for f in findings if f.get("severity") == "critical"),
                "major_findings": sum(1 for f in findings if f.get("severity") == "major"),
                "adjustment_count": len(raw.get("adjustments") or []),
                "claim_status_change_count": len(raw.get("claim_status_changes") or []),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["audit_id"])


def interventions_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per intervention entity."""
    rows: list[dict[str, Any]] = []
    for intervention_id, record in repo.interventions.items():
        raw = record.raw
        rows.append(
            {
                "intervention_id": intervention_id,
                "node_type": raw.get("node_type"),
                "label": raw.get("label") or raw.get("preferred_name") or raw.get("name"),
                "modality": raw.get("modality"),
                "chembl_id": raw.get("chembl_id") or (raw.get("identifiers") or {}).get("chembl_id"),
                "max_clinical_phase": (raw.get("max_clinical_phase") or {}).get("value"),
                "first_approval_year": raw.get("first_approval_year"),
                "database_source_id": raw.get("database_source_id"),
                "blood_brain_barrier": raw.get("blood_brain_barrier"),
                "efficacy_status": raw.get("efficacy_status"),
                # The only legal value is `omitted_by_policy`; carried into SQL so the
                # absence of dose information is an explicit column rather than a gap a
                # reader might read as an oversight.
                "dose_information": raw.get("dose_information", "omitted_by_policy"),
                "target_count": len(raw.get("targets") or []),
                "claim_ref_count": len(
                    (raw.get("cited_by_claims") or raw.get("claim_refs") or raw.get("supports_effect_claims") or [])
                ),
                "known_liability_count": len(raw.get("known_liabilities") or []),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["intervention_id"])


def state_variables_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per state variable, including the polarity and shape fields."""
    rows: list[dict[str, Any]] = []
    for sv_id, record in repo.state_variables.items():
        raw = record.raw
        shape = raw.get("response_shape") or {}
        proxies = [p for p in (raw.get("measurement_proxies") or []) if isinstance(p, dict)]
        rows.append(
            {
                "state_variable_id": sv_id,
                "domain": sv_id.split(":", 1)[1].split(".", 1)[0],
                "name": raw.get("name"),
                "definition": raw.get("definition"),
                "kind": raw.get("kind"),
                "timescale": raw.get("timescale"),
                "level": raw.get("level"),
                "units": raw.get("units"),
                "response_shape": shape.get("shape"),
                "response_shape_basis": shape.get("basis"),
                "desirability": raw.get("desirability"),
                "polarity": raw.get("polarity"),
                "polarity_note": raw.get("polarity_note"),
                "safety_coupling_basis": raw.get("safety_coupling_basis"),
                "safety_coupling_count": len(raw.get("safety_coupling") or []),
                "proxy_count": len(proxies),
                "best_proxy_status": _best_proxy(proxies),
                "status": raw.get("status"),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: r["state_variable_id"])


_PROXY_ORDER = (
    "established_human_proxy",
    "research_proxy",
    "animal_only_proxy",
    "theoretical_construct",
)


def _best_proxy(proxies: list[dict[str, Any]]) -> str | None:
    """The strongest measurability grade among a variable's proxies, or ``None``.

    ``None`` when the list is empty, and an empty list is informative: it says nothing
    measures this variable yet, which must not be coerced into a weak-but-present grade.
    """
    statuses = {str(p.get("status")) for p in proxies}
    for candidate in _PROXY_ORDER:
        if candidate in statuses:
            return candidate
    return None


def annotations_rows(repo: loaders.Repository) -> list[dict[str, Any]]:
    """One row per state-variable annotation."""
    rows: list[dict[str, Any]] = []
    for record in repo.state_variable_annotations:
        raw = record.raw
        model = record.model
        shape = raw.get("response_shape") or {}
        couplings = getattr(model, "safety_couplings", []) if model is not None else []
        all_refs = getattr(model, "all_claim_refs", []) if model is not None else []
        rows.append(
            {
                "state_variable_id": raw.get("state_variable") or raw.get("state_variable_id"),
                "domain": raw.get("domain"),
                "annotated_by": raw.get("annotated_by"),
                "annotated_on": raw.get("annotated_on"),
                "proposed_response_shape": raw.get("proposed_response_shape") or shape.get("shape"),
                "response_shape_basis": shape.get("basis"),
                "shape_rationale": raw.get("shape_rationale") or shape.get("rationale"),
                "desirability_note": raw.get("desirability_note"),
                "safety_coupling_count": len(couplings),
                "coupled_to": _json(sorted(c.couples_to for c in couplings)),
                "claim_ref_count": len(all_refs),
                "claim_refs": _json(sorted(all_refs)),
                "record_path": record.path,
            }
        )
    return sorted(rows, key=lambda r: (str(r["state_variable_id"]), str(r["annotated_by"])))


def node_rows(compiled: CompiledGraph) -> list[dict[str, Any]]:
    """One row per compiled graph node."""
    return [
        {
            "id": node.id,
            "node_type": node.node_type,
            "layer": node.layer,
            "label": node.label,
            "provenance_class": node.provenance_class,
            "source_ref_count": len(node.source_refs),
            "source_refs": _json(sorted(node.source_refs)),
            "attributes": _json(node.attributes),
        }
        for node in compiled.nodes
    ]


def edge_rows(compiled: CompiledGraph) -> list[dict[str, Any]]:
    """One row per compiled graph edge, with the null-result flag as a column."""
    return [
        {
            "subject": edge.subject,
            "predicate": edge.predicate,
            "object": edge.object,
            "layer": edge.layer,
            "provenance_class": edge.provenance_class,
            "direction": edge.direction,
            "direction_context": edge.direction_context,
            "negated_relation": edge.negated_relation,
            "is_null_result": edge.is_null_result,
            "asserts_effect": edge.asserts_effect,
            "counts_as_support": edge.counts_as_support,
            "claim_count": len(edge.claim_ids),
            "claim_ids": _json(sorted(edge.claim_ids)),
            "claim_types": _json(sorted(edge.claim_types)),
            "evidence_count": edge.evidence_count,
            "distinct_source_count": edge.distinct_source_count,
            "source_ids": _json(sorted(edge.source_ids)),
            "basis": edge.basis,
            "reference_source": edge.reference_source,
        }
        for edge in compiled.edges
    ]


# Table name -> builder. The builders take (repo, compiled) so a caller does not have to
# know which of the two each table needs.
TABLES: dict[str, Callable[[loaders.Repository, CompiledGraph], list[dict[str, Any]]]] = {
    "sources": lambda repo, _c: sources_rows(repo),
    "claims": lambda repo, _c: claims_rows(repo),
    "evidence_items": lambda repo, _c: evidence_rows(repo),
    "targets": lambda repo, compiled: targets_rows(repo, compiled),
    "assessments": lambda repo, _c: assessments_rows(repo),
    "audits": lambda repo, _c: audits_rows(repo),
    "interventions": lambda repo, _c: interventions_rows(repo),
    "state_variables": lambda repo, _c: state_variables_rows(repo),
    "annotations": lambda repo, _c: annotations_rows(repo),
    "nodes": lambda _r, compiled: node_rows(compiled),
    "edges": lambda _r, compiled: edge_rows(compiled),
}
