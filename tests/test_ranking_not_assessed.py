"""``not_assessed`` handling — contract P8, "unknown is a first-class value".

The failure mode this guards against is the most seductive one available to a ranking
model: quietly treating "nobody looked" as either zero (which punishes honest gaps)
or as neutral-and-narrow (which rewards them). The required behaviour is that an
unassessed facet **widens** the interval, sits between a documented absence of
evidence and moderate real evidence, and keeps its weight in the denominator so a
sparsely-curated target cannot look fully characterised.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.inputs import FacetAssessment
from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import coverage_of, expected_composite, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    GATE_FREE_LEVELS,
    facet,
    make_inputs,
    make_target,
)

DRAWS = 8000

#: A high-weight direct facet, so the effect under test is well clear of Monte Carlo
#: error: it is the sole input to D3 and D3 carries 0.15 of the composite.
PROBE = "above_baseline_enhancement"


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def _target(level, *, name="TGT:PROBE", status=None):
    levels = dict(GATE_FREE_LEVELS)
    if level is None and status is None:
        levels.pop(PROBE, None)
    else:
        levels[PROBE] = level
    target = make_target(name, levels=levels)
    if status is not None:
        facets = dict(target.facets)
        facets[PROBE] = facet(PROBE, None, status=status)
        from dataclasses import replace

        target = replace(target, facets=facets)
    return target


def _scored(spec, target):
    return score_cohort(make_inputs([target]), spec, n_draws=DRAWS).targets[0]


# ---------------------------------------------------------------------------
# Width
# ---------------------------------------------------------------------------


def _relative_width(row) -> float:
    """Interval width relative to the median, for diagnostics."""
    return (row.composite_p95 - row.composite_p05) / row.composite_median


def _d3_width(row) -> float:
    """Width of the D3 interval. `PROBE` is a D3 facet, and dimensions stay on [0, 1]
    under every composite operator, so this is the scale-stable place to assert the
    uncertainty property."""
    score = row.dimensions["D3"]
    return score.p95 - score.p05


def test_not_assessed_produces_a_wider_interval_than_level_zero(spec) -> None:
    """The core requirement: an unasked question is less informative than a recorded
    negative search, so it must widen the reported interval.

    Asserted on the DIMENSION the facet feeds. See
    :func:`test_the_conjunctive_composite_width_is_not_an_uncertainty_measure` for why
    the composite's own width is the wrong place to assert this.
    """
    assert _d3_width(_scored(spec, _target(None))) > _d3_width(_scored(spec, _target(0)))


def test_not_assessed_is_wider_than_every_assessed_level(spec) -> None:
    """Not just wider than level 0: wider than any grade at all."""
    unassessed = _d3_width(_scored(spec, _target(None)))
    for level in range(5):
        assert unassessed > _d3_width(_scored(spec, _target(level))), level


def test_the_conjunctive_composite_width_is_not_an_uncertainty_measure(spec) -> None:
    """A real consequence of the conjunctive (product) composite, pinned deliberately.

    Under a product, the spread of the composite is dominated by the MAGNITUDE of its
    smallest factor rather than by how uncertain that factor is. A level-0 facet
    (Beta(1,4), mean 0.200) therefore produces a composite whose relative width EXCEEDS
    that of an unassessed facet (Beta(1,1), mean 0.500), even though the unassessed
    facet is strictly the more uncertain of the two.

    So "unknown widens the interval" holds at the facet level
    (tests/test_uncertainty_levels.py) and at the dimension level (above), and does NOT
    hold on the composite's own width under this operator. That is a limitation of the
    operator, not a defect in the uncertainty model, and it is why coverage is a
    required report column rather than something a reader is expected to infer from
    interval width. It is also why the RANK interval — which is scale-free — is the
    headline output.
    """
    unassessed = _scored(spec, _target(None))
    level_zero = _scored(spec, _target(0))
    assert _relative_width(level_zero) > _relative_width(unassessed), (
        "the product composite no longer shows this artefact, so the caveat above and "
        "the corresponding note in ranking_spec_v0_1.yaml should be re-derived"
    )
    # and the ordering of the medians is still correct, which is what matters:
    assert unassessed.composite_median > level_zero.composite_median


def test_more_unassessed_facets_means_a_wider_composite(spec) -> None:
    """Coverage and interval width must move together: a sparsely assessed target
    cannot present a tight interval."""
    dense = make_target("TGT:DENSE", levels=dict.fromkeys(ALL_FACETS, 2))
    sparse = make_target("TGT:SPARSE", levels={PROBE: 2})
    dense_row = _scored(spec, dense)
    sparse_row = _scored(spec, sparse)
    assert dense_row.coverage > sparse_row.coverage
    assert _relative_width(sparse_row) > _relative_width(dense_row)


def test_more_unassessed_facets_means_a_wider_rank_interval(spec) -> None:
    """The consequence a reader actually sees: an under-curated target has no
    resolved rank."""
    cohort = [
        make_target("TGT:DENSE", levels=dict.fromkeys(ALL_FACETS, 2)),
        make_target("TGT:SPARSE", levels={PROBE: 2}),
        make_target("TGT:OTHER_A", levels=dict.fromkeys(ALL_FACETS, 1)),
        make_target("TGT:OTHER_B", levels=dict.fromkeys(ALL_FACETS, 3)),
    ]
    result = score_cohort(make_inputs(cohort), spec, n_draws=DRAWS)
    dense = result.ranks["TGT:DENSE"]
    sparse = result.ranks["TGT:SPARSE"]
    assert (sparse.rank_p95 - sparse.rank_p05) >= (dense.rank_p95 - dense.rank_p05)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


def test_not_assessed_does_not_outscore_a_genuine_level_two(spec) -> None:
    """Absence of assessment is not rewarded. Asserted analytically (exact) and on
    the sampled path (as reported)."""
    assert expected_composite(spec, _target(None)) <= expected_composite(spec, _target(2))
    unassessed = _scored(spec, _target(None))
    level_two = _scored(spec, _target(2))
    assert unassessed.composite_median <= level_two.composite_median


def test_not_assessed_scores_above_a_documented_absence_of_evidence(spec) -> None:
    """Absence of assessment is not punished either. A target nobody examined must
    not be ranked below one that was examined and came up empty — that would make
    curation effort look like a liability."""
    assert expected_composite(spec, _target(None)) > expected_composite(spec, _target(0))


def test_not_assessed_sits_strictly_between_level_one_and_level_two(spec) -> None:
    """The precise claim the uncertainty spec makes about where "unknown" lands."""
    unknown = expected_composite(spec, _target(None))
    assert expected_composite(spec, _target(1)) < unknown < expected_composite(spec, _target(2))


def test_a_fully_unassessed_target_does_not_beat_a_moderately_assessed_one(spec) -> None:
    """The strongest form: a target with nothing graded at all must not outrank a
    target graded at level 2 across the board."""
    cohort = [
        make_target("TGT:NOTHING_GRADED", levels={PROBE: 2}),
        make_target("TGT:ALL_MODERATE", levels=dict.fromkeys(ALL_FACETS, 2)),
    ]
    result = score_cohort(make_inputs(cohort), spec, n_draws=DRAWS)
    assert result.ranks["TGT:ALL_MODERATE"].rank_median < result.ranks["TGT:NOTHING_GRADED"].rank_median


# ---------------------------------------------------------------------------
# Structure: weight retention, not_applicable, coverage
# ---------------------------------------------------------------------------


def test_unassessed_facets_keep_their_weight_in_the_denominator(spec) -> None:
    """If unassessed facets were dropped, a target with one strong facet and fourteen
    unexamined ones would score as if fully characterised. The check: a target with
    only ``PROBE`` at level 4 must not reach the composite of a target with every
    facet at level 4."""
    one_strong_facet = make_target("TGT:ONE", levels={PROBE: 4})
    all_strong = make_target(
        "TGT:ALL", levels={**dict.fromkeys(ALL_FACETS, 4), "safety_liability_burden": 0,
                           "developmental_confound_risk": 0, "human_lineage_divergence_risk": 0}
    )
    assert expected_composite(spec, one_strong_facet) < expected_composite(spec, all_strong)


def test_not_applicable_is_removed_from_both_numerator_and_denominator(spec) -> None:
    """``not_applicable`` differs from ``not_assessed``: it drops out entirely rather
    than contributing an uninformative prior, and it does not depress coverage."""
    unassessed = make_target("TGT:UNASSESSED", levels={PROBE: 3})
    excluded = make_target("TGT:EXCLUDED", levels={PROBE: 3}, not_applicable=["transfer_breadth"])

    _, _, unassessed_applicable = coverage_of(spec, unassessed)
    excluded_coverage, _, excluded_applicable = coverage_of(spec, excluded)
    assert excluded_applicable == unassessed_applicable - 1

    unassessed_coverage, _, _ = coverage_of(spec, unassessed)
    assert excluded_coverage > unassessed_coverage

    # D4 is fed by transfer_breadth and human_phenotype_specificity; excluding the
    # former must leave D4 driven entirely by the latter.
    dims = score_cohort(make_inputs([excluded]), spec, n_draws=DRAWS).targets[0].dimensions
    assert dims["D4"].n_applicable == 1


def test_coverage_counts_assessed_over_applicable(spec) -> None:
    target = make_target(
        "TGT:PARTIAL",
        levels={PROBE: 3, "tractability": 2, "transfer_breadth": 1},
        not_applicable=["cross_species_convergence"],
    )
    coverage, assessed, applicable = coverage_of(spec, target)
    assert (assessed, applicable) == (3, 14)
    assert coverage == pytest.approx(3 / 14)


def test_an_assessed_facet_must_carry_a_level() -> None:
    """The contract forbids writing 0 for unexamined evidence (§5.2), and forbids an
    assessed facet with a null level. Both are enforced at construction."""
    with pytest.raises(ValueError, match="must carry a level"):
        FacetAssessment(facet=PROBE, assessment_status="assessed", level=None)
    with pytest.raises(ValueError, match="must be null"):
        FacetAssessment(facet=PROBE, assessment_status="not_assessed", level=0)


def test_a_facet_absent_from_the_record_is_not_assessed_not_zero(spec) -> None:
    """A facet nobody wrote down at all reads as ``not_assessed``."""
    target = make_target("TGT:PROBE", levels={PROBE: 2})
    assert target.facet("a_facet_that_was_never_written").assessment_status == "not_assessed"
    assert target.facet("a_facet_that_was_never_written").level is None


# ---------------------------------------------------------------------------
# The three "no support" states must stay distinguishable in the ARTEFACTS
# ---------------------------------------------------------------------------


def test_the_three_no_support_states_are_distinguishable_in_the_csv(spec) -> None:
    """Contract §5.2 forbids collapsing them, and a report that showed only a level
    column would collapse two of them.

    ``agent:power`` produced exactly this pattern: ``human_intervention_evidence`` at
    level 0 for five of seven targets, and ``above_baseline_enhancement`` at level 2
    with ``counter_level`` 3. A reader must be able to tell those apart from a facet
    nobody graded, from the CSV alone.
    """
    import csv
    import io

    from blueprint.ranking.report import render_csv

    cohort = [
        # nobody looked at D3's facet
        make_target("TGT:UNEXAMINED", levels={"tractability": 2}),
        # searched D3's facet and found nothing
        make_target("TGT:SEARCHED", levels={"tractability": 2, PROBE: 0}),
        # graded D3's facet, then contradicted it
        make_target(
            "TGT:CONTRADICTED",
            levels={"tractability": 2, PROBE: 2},
            counter_levels={PROBE: 3},
        ),
    ]
    result = score_cohort(make_inputs(cohort), spec, n_draws=DRAWS)
    rows = {
        row["target_id"]: row
        for row in csv.DictReader(
            io.StringIO(render_csv(result, generated_on="2026-09-17").decode("utf-8"))
        )
    }

    unexamined, searched, contradicted = (
        rows["TGT:UNEXAMINED"],
        rows["TGT:SEARCHED"],
        rows["TGT:CONTRADICTED"],
    )

    # nobody looked: blank level, blank counter, zero assessed
    assert (unexamined["d3_level"], unexamined["d3_counter_level"]) == ("", "")
    assert unexamined["d3_n_assessed"] == "0"
    assert unexamined["d3_n_level_zero"] == "0"

    # searched and found nothing: an explicit 0, and counted as a documented negative
    assert (searched["d3_level"], searched["d3_counter_level"]) == ("0", "")
    assert searched["d3_n_assessed"] == "1"
    assert searched["d3_n_level_zero"] == "1"

    # tested and contradicted: level AND counter_level both present
    assert (contradicted["d3_level"], contradicted["d3_counter_level"]) == ("2", "3")
    assert contradicted["d3_n_assessed"] == "1"
    assert contradicted["d3_n_level_zero"] == "0"

    # and the target-level counts separate them too
    assert unexamined["facets_level_zero"] == "0"
    assert searched["facets_level_zero"] == "1"
    assert contradicted["facets_contradicted"] == "1"
    assert int(unexamined["facets_not_assessed"]) > int(searched["facets_not_assessed"])


def test_the_three_states_score_in_the_right_order(spec) -> None:
    """Not merely distinguishable: ordered the way the contract's semantics require.

    ``tested and contradicted`` must sit lowest, ``searched and found nothing`` above
    it, and ``nobody looked`` above both (an uninformative prior, not a penalty).
    """
    unexamined = _target(None, name="TGT:UNEXAMINED")
    searched = _target(0, name="TGT:SEARCHED")
    contradicted = make_target(
        "TGT:CONTRADICTED",
        levels={**GATE_FREE_LEVELS, PROBE: 1},
        counter_levels={PROBE: 3},
    )
    values = {
        "contradicted": expected_composite(spec, contradicted),
        "searched": expected_composite(spec, searched),
        "unexamined": expected_composite(spec, unexamined),
    }
    assert values["contradicted"] < values["searched"] < values["unexamined"]


def test_the_sidecar_records_per_facet_evidence_state(spec, tmp_path) -> None:
    """Full recoverability: the per-facet state is in the artefacts, not only in the
    source records."""
    import json

    from blueprint.ranking.report import write_report

    cohort = make_inputs(
        [
            make_target(
                "TGT:MIXED",
                levels={"tractability": 2, PROBE: 0, "transfer_breadth": 2},
                counter_levels={"transfer_breadth": 3},
            )
        ]
    )
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    artefacts = write_report(
        result,
        cohort,
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
    )
    meta = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))
    facets = meta["evidence_state"]["TGT:MIXED"]["facets"]

    assert facets[PROBE] == {
        "status": "assessed",
        "level": 0,
        "counter_level": None,
        "polarity": "normal",
        "n_claim_refs": 0,
        "n_counter_claim_refs": 0,
        "reporting_gap_refs": [],
        "limiting_factor": None,
    }
    assert facets["transfer_breadth"]["level"] == 2
    assert facets["transfer_breadth"]["counter_level"] == 3
    assert facets["adult_onset_perturbation"]["status"] == "not_assessed"
    assert facets["adult_onset_perturbation"]["level"] is None
    assert facets["safety_liability_burden"]["polarity"] == "inverse"


def test_the_sidecar_makes_sparse_coverage_impossible_to_overlook(spec, tmp_path) -> None:
    """Sparse coverage is the Sprint-1 norm; the summary must state it in numbers."""
    import json

    from blueprint.ranking.report import write_report

    cohort = make_inputs(
        [
            make_target("TGT:SPARSE_A", levels={"tractability": 2}),
            make_target("TGT:SPARSE_B", levels={"tractability": 1, PROBE: 0}),
            make_target("TGT:DENSE", levels=dict.fromkeys(ALL_FACETS, 2)),
        ]
    )
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    artefacts = write_report(
        result,
        cohort,
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
    )
    summary = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))["coverage_summary"]

    assert summary["n_targets"] == 3
    assert summary["min_coverage_threshold"] == float(spec.tiers["min_coverage"])
    assert summary["n_targets_below_min_coverage"] == 2
    assert set(summary["targets_below_min_coverage"]) == {"TGT:SPARSE_A", "TGT:SPARSE_B"}
    assert summary["total_facet_slots"] == 45
    assert summary["total_facets_assessed"] == 18
    assert summary["total_facets_not_assessed"] == 27
    assert summary["total_facets_level_zero"] == 1
    assert "statement about curation" in summary["reading"]
