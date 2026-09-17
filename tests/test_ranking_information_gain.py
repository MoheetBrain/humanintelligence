"""Information gain: which facet's resolution would most move a target's rank.

The claim being tested is narrow and should stay narrow: the sweep measures the
sensitivity of *this model's ranking* to *one facet's grade*. These tests check that
the perturbation arithmetic is right (the baseline is reproduced exactly when nothing
is perturbed), that the ordering is deterministic, that unassessed facets are
preferred at equal influence, and that a facet with no influence reports zero rather
than being silently dropped.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.information_gain import (
    facet_information_gain,
    most_informative_facet,
    repository_next_analyses,
)
from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    GATE_FREE_LEVELS,
    normal_uniform_target,
    make_inputs,
    make_target,
)

DRAWS = 2000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


@pytest.fixture
def cohort():
    """A cohort with several targets clustered closely, so ranks can actually move."""
    return make_inputs(
        [
            make_target("TGT:A", levels=dict.fromkeys(ALL_FACETS, 2)),
            make_target("TGT:B", levels=dict.fromkeys(ALL_FACETS, 2) | {"tractability": 3}),
            make_target("TGT:C", levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 2}),
            normal_uniform_target("TGT:D", 3),
        ]
    )


def test_every_target_and_applicable_facet_is_swept(spec, cohort) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, cohort)
    assert set(gains) == {t.target_id for t in result.targets}
    for target_id, entry in gains.items():
        assert {g.facet for g in entry.facets} == set(ALL_FACETS), target_id


def test_not_applicable_facets_are_excluded_from_the_sweep(spec) -> None:
    """A facet that does not apply cannot be resolved, so it carries no gain."""
    inputs = make_inputs(
        [
            make_target(
                "TGT:A",
                levels=dict.fromkeys(ALL_FACETS, 2),
                not_applicable=["transfer_breadth"],
            ),
            normal_uniform_target("TGT:B", 2),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    assert "transfer_breadth" not in {g.facet for g in gains["TGT:A"].facets}


def test_the_baseline_rank_reproduces_the_cohort_rank(spec, cohort) -> None:
    """The perturbation machinery ranks one target against a cached matrix of the
    others. If that shortcut disagreed with the full re-sort, every reported gain
    would be measured against the wrong baseline."""
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, cohort)
    for target_id, entry in gains.items():
        assert entry.baseline_rank_median == pytest.approx(result.ranks[target_id].rank_median)


def test_baseline_rank_width_matches_the_reported_rank_interval(spec, cohort) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, cohort)
    for target_id, entry in gains.items():
        summary = result.ranks[target_id]
        assert entry.baseline_rank_width == pytest.approx(summary.rank_p95 - summary.rank_p05)


def test_the_sweep_is_deterministic(spec, cohort) -> None:
    first = facet_information_gain(score_cohort(cohort, spec, n_draws=DRAWS, seed=3), cohort)
    second = facet_information_gain(score_cohort(cohort, spec, n_draws=DRAWS, seed=3), cohort)
    for target_id in first:
        assert [g.facet for g in first[target_id].facets] == [
            g.facet for g in second[target_id].facets
        ]
        assert [g.value for g in first[target_id].facets] == [
            g.value for g in second[target_id].facets
        ]


def test_gains_are_sorted_by_descending_value(spec, cohort) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, cohort)
    for entry in gains.values():
        values = [g.value for g in entry.facets]
        assert values == sorted(values, reverse=True)


def test_an_unassessed_facet_is_perturbed_from_the_bracketing_levels(spec) -> None:
    """An ungraded facet has no baseline level, so the sweep uses levels 1 and 3 —
    the grades that bracket the uninformative prior."""
    inputs = make_inputs(
        [
            make_target("TGT:A", levels={"tractability": 2}),
            normal_uniform_target("TGT:B", 2),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    unassessed = next(g for g in gains["TGT:A"].facets if g.facet == "above_baseline_enhancement")
    assert unassessed.baseline_status == "not_assessed"
    assert unassessed.baseline_level is None
    assert (unassessed.level_down, unassessed.level_up) == (1, 3)


def test_an_assessed_facet_is_perturbed_by_one_level_and_clipped(spec) -> None:
    inputs = make_inputs(
        [
            make_target("TGT:A", levels={"above_baseline_enhancement": 0, "tractability": 4}),
            normal_uniform_target("TGT:B", 2),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    floored = next(g for g in gains["TGT:A"].facets if g.facet == "above_baseline_enhancement")
    ceilinged = next(g for g in gains["TGT:A"].facets if g.facet == "tractability")
    assert (floored.level_down, floored.level_up) == (0, 1)
    assert (ceilinged.level_down, ceilinged.level_up) == (3, 4)


def test_an_unassessed_facet_is_preferred_at_equal_influence(spec) -> None:
    """The spec's ``unresolved_multiplier``: assessing an unexamined facet is worth
    more than overturning an existing grade, at equal rank influence."""
    multipliers = spec.information_gain["unresolved_multiplier"]
    assert float(multipliers["not_assessed"]) > float(multipliers["assessed"])

    inputs = make_inputs(
        [
            make_target("TGT:A", levels=dict.fromkeys(ALL_FACETS, 2)),
            make_target("TGT:B", levels=dict.fromkeys(ALL_FACETS, 2)),
            make_target("TGT:C", levels={"transfer_breadth": 2}),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    for entry in gains.values():
        for gain in entry.facets:
            expected = float(multipliers[gain.baseline_status])
            assert gain.unresolved_multiplier == pytest.approx(expected)
            assert gain.value == pytest.approx(gain.rank_swing * expected)


def test_an_isolated_target_reports_zero_movement_not_a_missing_facet(spec) -> None:
    """A target far from every neighbour cannot move. Reporting 0.0 against a named
    facet is the honest answer; dropping the facet would look like a data gap."""
    inputs = make_inputs(
        [
            normal_uniform_target("TGT:TOP", 4, inverse_level=0),
            normal_uniform_target("TGT:BOTTOM", 0, inverse_level=4),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    top = gains["TGT:TOP"]
    assert top.facets
    assert all(g.rank_swing == pytest.approx(0.0) for g in top.facets)
    facet_name, value = most_informative_facet(top)
    assert facet_name in ALL_FACETS
    assert value == pytest.approx(0.0)


def test_a_closely_contested_pair_produces_real_movement(spec) -> None:
    """The complement of the test above: when two targets are near each other, a
    one-level change in a heavily-weighted facet must actually swap them."""
    inputs = make_inputs(
        [
            make_target("TGT:A", levels=dict.fromkeys(ALL_FACETS, 2)),
            make_target("TGT:B", levels=dict.fromkeys(ALL_FACETS, 2)),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, inputs)
    assert max(g.rank_swing for g in gains["TGT:A"].facets) > 0.0


def test_most_informative_facet_handles_a_missing_entry() -> None:
    assert most_informative_facet(None) == ("", 0.0)


def test_repository_next_analyses_is_ranked_and_capped(spec, cohort) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    gains = facet_information_gain(result, cohort)
    rows = repository_next_analyses(gains, limit=7)
    assert len(rows) == 7
    values = [float(row["value"]) for row in rows]
    assert values == sorted(values, reverse=True)
    for row in rows:
        assert set(row) == {
            "target_id",
            "facet",
            "baseline_status",
            "baseline_level",
            "rank_swing",
            "interval_reduction",
            "value",
        }
        assert row["target_id"] in gains
        assert row["facet"] in ALL_FACETS
