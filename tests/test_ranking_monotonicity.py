"""Monotonicity: better evidence never scores worse, contradiction never scores better.

Polarity matters, and the test statements say so explicitly. For the twelve
``direct`` facets, a higher level means more support for the dimension, so the
composite must not fall. For the three ``inverse`` facets
(``safety_liability_burden``, ``developmental_confound_risk``,
``human_lineage_divergence_risk``) the proposition graded is a RISK, so a higher
level is *worse* for the target and the composite must not rise. A test that
asserted "higher level always raises the composite" would be asserting that the
model ignores the inverse polarity the contract requires.

Two proof strategies are used, deliberately.

``expected_composite`` is the analytic composite built from the Beta *means*. Being
deterministic, it lets monotonicity be asserted **strictly** for every facet at every
level transition, including the lowest-weighted facets whose effect on the composite
is smaller than Monte Carlo error at any practical draw count.

``score_cohort`` is the sampled path that actually produces reports. It is checked at
coarse granularity (level 0 versus level 4) where the effect exceeds sampling noise,
to confirm the sampler agrees with the analytic statement. Testing only the sampled
path would leave small-weight facets unverified; testing only the analytic path would
leave the sampler unverified.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import expected_composite, expected_dimensions, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    NORMAL_FACETS,
    GATE_FREE_LEVELS,
    INVERSE_FACETS,
    normal_uniform_target,
    make_inputs,
    make_target,
)

DRAWS = 4000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def _probe(facet_name: str, level: int, counter: int | None = None):
    """A gate-free target with one facet set to ``level``.

    The gate-free baseline is what makes a *strict* monotonicity claim meaningful:
    with a cap binding, raising a level correctly produces no change at all, and a
    strict assertion would be testing the wrong property.
    """
    levels = dict(GATE_FREE_LEVELS)
    levels[facet_name] = level
    return make_target(
        "TGT:PROBE",
        levels=levels,
        counter_levels={facet_name: counter} if counter is not None else None,
    )


# ---------------------------------------------------------------------------
# Analytic, exhaustive, strict
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("facet_name", NORMAL_FACETS)
def test_raising_a_direct_facet_level_never_lowers_the_composite(spec, facet_name) -> None:
    """Every one-step transition 0->1->2->3->4, for all twelve normal-polarity facets."""
    previous = None
    for level in range(5):
        value = expected_composite(spec, _probe(facet_name, level))
        if previous is not None:
            assert value >= previous, (
                f"{facet_name}: composite fell when level rose to {level} "
                f"({previous:.6f} -> {value:.6f})"
            )
        previous = value


@pytest.mark.parametrize("facet_name", INVERSE_FACETS)
def test_raising_an_inverse_facet_level_never_raises_the_composite(spec, facet_name) -> None:
    """Stronger evidence that a risk is real must never improve a target."""
    previous = None
    for level in range(5):
        value = expected_composite(spec, _probe(facet_name, level))
        if previous is not None:
            assert value <= previous, (
                f"{facet_name}: composite rose when RISK evidence strengthened to {level} "
                f"({previous:.6f} -> {value:.6f})"
            )
        previous = value


@pytest.mark.parametrize("facet_name", ALL_FACETS)
def test_every_facet_actually_moves_the_composite(spec, facet_name) -> None:
    """The inequality is strict: no facet in the catalogue is inert.

    A facet that could be raised with no effect on any dimension would be a facet
    the model silently ignores, which would make its rubric criteria decorative.
    """
    low = expected_composite(spec, _probe(facet_name, 1))
    high = expected_composite(spec, _probe(facet_name, 3))
    assert low != high, f"{facet_name}: changing the level did not change the composite"
    if facet_name in INVERSE_FACETS:
        assert high < low
    else:
        assert high > low


@pytest.mark.parametrize("facet_name", ALL_FACETS)
def test_raising_counter_level_never_helps_the_graded_proposition(spec, facet_name) -> None:
    """Contradicting evidence is never netted off into support.

    For a normal-polarity facet, more counter-evidence must not raise the composite. For an
    inverse (risk) facet, ``counter_level`` grades evidence that the risk is *not*
    real, so it must not lower the composite. Both readings are the same rule:
    evidence against a proposition never strengthens that proposition.
    """
    inverse = spec.facets[facet_name].is_inverse
    previous = None
    for counter in range(5):
        value = expected_composite(spec, _probe(facet_name, 3, counter))
        if previous is not None:
            if inverse:
                assert value >= previous, f"{facet_name}: inverse facet fell as counter_level rose"
            else:
                assert value <= previous, f"{facet_name}: direct facet rose as counter_level rose"
        previous = value


def test_counter_level_strictly_lowers_a_direct_facet(spec) -> None:
    clean = expected_composite(spec, _probe("mechanistic_causal_perturbation", 3))
    contested = expected_composite(spec, _probe("mechanistic_causal_perturbation", 3, 4))
    assert contested < clean


def test_monotonicity_holds_dimension_by_dimension(spec) -> None:
    """Not just in aggregate: each facet's own dimensions must move the right way."""
    for facet_name, facet_spec in spec.facets.items():
        low = expected_dimensions(spec, _probe(facet_name, 1))
        high = expected_dimensions(spec, _probe(facet_name, 3))
        for dimension in facet_spec.feeds:
            if facet_spec.is_inverse:
                assert high[dimension] <= low[dimension], f"{facet_name} -> {dimension}"
            else:
                assert high[dimension] >= low[dimension], f"{facet_name} -> {dimension}"


def test_monotonicity_survives_every_aggregation_variant(spec) -> None:
    """A sensitivity variant that inverted monotonicity would invalidate the
    sensitivity analysis itself."""
    for method in ("product", "minimum", "weighted_additive", "geometric_mean"):
        low = expected_composite(spec, normal_uniform_target("TGT:PROBE", 1), method=method)
        high = expected_composite(spec, normal_uniform_target("TGT:PROBE", 3), method=method)
        assert high >= low, method


# ---------------------------------------------------------------------------
# Sampled path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("facet_name", ALL_FACETS)
def test_sampled_composite_moves_the_right_way_from_level_zero_to_four(spec, facet_name) -> None:
    """The reported (sampled) composite agrees with the analytic statement.

    Compared at 0 versus 4, where the effect exceeds Monte Carlo error for even the
    lowest-weighted facet in the catalogue.
    """
    low_levels = dict(GATE_FREE_LEVELS) | {facet_name: 0}
    high_levels = dict(GATE_FREE_LEVELS) | {facet_name: 4}
    inputs = make_inputs(
        [
            make_target("TGT:LOW", levels=low_levels),
            make_target("TGT:HIGH", levels=high_levels),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    rows = {t.target_id: t for t in result.targets}
    if facet_name in INVERSE_FACETS:
        assert rows["TGT:HIGH"].composite_median < rows["TGT:LOW"].composite_median
    else:
        assert rows["TGT:HIGH"].composite_median > rows["TGT:LOW"].composite_median


def test_sampled_ranks_follow_evidence_strength_with_no_inversions(spec) -> None:
    """A ladder of normal-polarity strength must rank in order, 4 best and 0 worst."""
    inputs = make_inputs([normal_uniform_target(f"TGT:L{level}", level) for level in range(5)])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    medians = [result.ranks[f"TGT:L{level}"].rank_median for level in range(5)]
    assert medians == sorted(medians, reverse=True), medians
    assert result.ranks["TGT:L4"].rank_median == pytest.approx(1.0)
    assert result.ranks["TGT:L0"].rank_median == pytest.approx(5.0)


def test_sampled_ranks_follow_risk_strength_in_reverse(spec) -> None:
    """Holding benefit evidence fixed, accumulating risk evidence must demote."""
    inputs = make_inputs(
        [normal_uniform_target(f"TGT:R{risk}", 3, inverse_level=risk) for risk in range(5)]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    medians = [result.ranks[f"TGT:R{risk}"].rank_median for risk in range(5)]
    assert medians == sorted(medians), medians


def test_raising_counter_level_lowers_a_sampled_rank(spec) -> None:
    inputs = make_inputs(
        [
            normal_uniform_target("TGT:CLEAN", 3),
            normal_uniform_target(
                "TGT:CONTESTED",
                3,
                counter_levels={
                    "mechanistic_causal_perturbation": 4,
                    "adult_onset_perturbation": 4,
                },
            ),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    assert result.ranks["TGT:CLEAN"].rank_median < result.ranks["TGT:CONTESTED"].rank_median
