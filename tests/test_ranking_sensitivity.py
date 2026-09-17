"""Sensitivity of the ranking to the aggregation choice.

``ranking_spec_v0_1.yaml`` §5 chooses a weighted arithmetic mean as the primary
composite while THEORY.md argues the underlying biology is plausibly multiplicative.
That disagreement is deliberate and is not hidden: every run reports a Kendall tau-b
between the primary ranking and each multiplicative variant, so a reader can see
whether the ordering is a property of the evidence or of the aggregation function.

These tests check that the sensitivity analysis is actually performed, that it is
reported for every declared alternative, and that it behaves as expected in cases
where the answer is known by construction.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import composite_from_dimensions, dimension_draws, facet_contribution_draws, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    NORMAL_FACETS,
    normal_uniform_target,
    make_inputs,
    make_target,
)
from blueprint.ranking.uncertainty import kendall_tau_b

DRAWS = 3000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def test_every_declared_variant_is_reported(spec) -> None:
    inputs = make_inputs([normal_uniform_target(f"TGT:L{level}", level) for level in range(5)])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    assert set(result.sensitivity) == set(spec.alternative_aggregations)
    assert set(result.sensitivity) == {"minimum", "weighted_additive"}


def test_all_operator_pairs_are_compared(spec) -> None:
    """Pairwise, not variant-against-primary: the primary is not privileged when the
    question is whether the ordering is a property of the operator at all."""
    inputs = make_inputs([normal_uniform_target(f"TGT:L{level}", level) for level in range(5)])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    assert set(result.pairwise_sensitivity) == {
        "product__vs__minimum",
        "product__vs__weighted_additive",
        "minimum__vs__weighted_additive",
    }
    assert set(result.rank_by_aggregation) == {"product", "minimum", "weighted_additive"}
    for operator, ranks in result.rank_by_aggregation.items():
        assert set(ranks) == {t.target_id for t in result.targets}, operator


def test_tau_b_values_are_in_range(spec) -> None:
    inputs = make_inputs([normal_uniform_target(f"TGT:L{level}", level) for level in range(5)])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    for name, value in result.sensitivity.items():
        assert not math.isnan(value), name
        assert -1.0 - 1e-12 <= value <= 1.0 + 1e-12, name


def test_a_monotone_cohort_agrees_across_all_aggregations(spec) -> None:
    """When one target dominates another on every dimension, no aggregation function
    can disagree about their order. Every pairwise tau-b must be 1 — if one is not, the
    implementation of that operator is wrong."""
    inputs = make_inputs([normal_uniform_target(f"TGT:L{level}", level) for level in range(5)])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    for name, value in result.pairwise_sensitivity.items():
        assert value == pytest.approx(1.0), f"{name} disagreed with a dominance ordering"


def test_the_aggregation_choice_can_change_the_order(spec) -> None:
    """Otherwise reporting tau-b would be theatre.

    ``TGT:BALANCED`` is moderate everywhere. ``TGT:SPIKY`` is excellent on the
    heavily-weighted dimensions and very weak on one. The additive primary can let
    the strengths pay for the weakness; the minimum (Liebig) variant cannot. A tau-b
    below 1 on at least one variant is the expected, and reportable, result.
    """
    balanced = make_target(
        "TGT:BALANCED",
        levels=dict.fromkeys(NORMAL_FACETS, 2)
        | {"safety_liability_burden": 2, "developmental_confound_risk": 2, "human_lineage_divergence_risk": 2},
    )
    spiky = make_target(
        "TGT:SPIKY",
        levels=dict.fromkeys(NORMAL_FACETS, 4)
        | {
            "above_baseline_enhancement": 0,
            "safety_liability_burden": 0,
            "developmental_confound_risk": 0,
            "human_lineage_divergence_risk": 0,
        },
    )
    third = normal_uniform_target("TGT:MIDDLE", 3, inverse_level=1)
    result = score_cohort(make_inputs([balanced, spiky, third]), spec, n_draws=DRAWS)

    orders = {}
    for method in ("product", "minimum"):
        composites = []
        for target in sorted(
            (balanced, spiky, third), key=lambda t: t.target_id
        ):
            contributions = facet_contribution_draws(spec, target, n_draws=DRAWS, seed=result.seed)
            dimensions = dimension_draws(spec, target, contributions)
            draws, _ = composite_from_dimensions(spec, target, dimensions, method=method)
            composites.append(float(np.median(draws)))
        orders[method] = composites

    # The spiky target's zero on D3 costs it differently under the two conjunctions.
    conjunctive = orders["product"]
    liebig = orders["minimum"]
    assert (
        np.argmax(conjunctive) != np.argmax(liebig)
        or kendall_tau_b(conjunctive, liebig) < 1.0
        or kendall_tau_b(
            [r.rank_median for r in result.ranks.values()],
            [result.rank_by_aggregation["weighted_additive"][tid] for tid in result.ranks],
        )
        < 1.0
    )


def test_sensitivity_is_undefined_for_a_single_target(spec) -> None:
    """tau-b needs at least two observations; one target must give nan rather than a
    misleading 1.0."""
    result = score_cohort(make_inputs([normal_uniform_target("TGT:ONLY", 3)]), spec, n_draws=DRAWS)
    assert all(math.isnan(v) for v in result.sensitivity.values())
    assert all(math.isnan(v) for v in result.pairwise_sensitivity.values())


def test_all_operators_are_computable_and_bounded(spec) -> None:
    target = normal_uniform_target("TGT:PROBE", 3)
    contributions = facet_contribution_draws(spec, target, n_draws=500, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    for method in ("product", "minimum", "weighted_additive", "geometric_mean"):
        draws, _ = composite_from_dimensions(spec, target, dimensions, method=method)
        assert draws.shape == (500,)
        assert np.all((draws >= 0.0) & (draws <= 1.0)), method


def test_product_is_never_above_the_geometric_mean(spec) -> None:
    """A sanity check on the two multiplicative variants: for six values in (0,1),
    the product is at most the geometric mean."""
    target = normal_uniform_target("TGT:PROBE", 3)
    contributions = facet_contribution_draws(spec, target, n_draws=500, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    product, _ = composite_from_dimensions(spec, target, dimensions, method="product")
    geometric, _ = composite_from_dimensions(spec, target, dimensions, method="geometric_mean")
    assert np.all(product <= geometric + 1e-12)


def test_minimum_is_never_above_the_weighted_mean(spec) -> None:
    target = normal_uniform_target("TGT:PROBE", 3)
    contributions = facet_contribution_draws(spec, target, n_draws=500, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    minimum, _ = composite_from_dimensions(spec, target, dimensions, method="minimum")
    additive, _ = composite_from_dimensions(spec, target, dimensions, method="weighted_additive")
    assert np.all(minimum <= additive + 1e-12)


def test_the_product_is_never_above_the_minimum(spec) -> None:
    """A product of six values in (0, 1) is at most the smallest of them, so the
    conjunctive primary is strictly harsher than Liebig's law — which is the expected
    ordering of the two conjunctions and worth pinning."""
    target = normal_uniform_target("TGT:PROBE", 3)
    contributions = facet_contribution_draws(spec, target, n_draws=500, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    product, _ = composite_from_dimensions(spec, target, dimensions, method="product")
    minimum, _ = composite_from_dimensions(spec, target, dimensions, method="minimum")
    assert np.all(product <= minimum + 1e-12)


def test_composite_gates_apply_to_every_aggregation(spec) -> None:
    """Sensitivity must isolate the aggregation function, so the same caps apply to
    all variants — otherwise a tau-b would mix an aggregation difference with a
    gating difference."""
    gate = next(
        g for g in spec.gates if g.gate_id == "unresolved_critical_finding_caps_composite"
    )
    target = normal_uniform_target("TGT:DISPUTED", 4, unresolved_critical_findings=1)
    contributions = facet_contribution_draws(spec, target, n_draws=500, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    for method in ("product", "minimum", "weighted_additive", "geometric_mean"):
        draws, gates = composite_from_dimensions(spec, target, dimensions, method=method)
        assert "unresolved_critical_finding_caps_composite" in gates, method
        # The cap is declared dimension-equivalent, so it converts per operator.
        assert np.all(draws <= gate.cap_for(method) + 1e-12), method


def test_unknown_aggregation_method_is_rejected(spec) -> None:
    from blueprint.ranking.rubric import SpecError

    target = normal_uniform_target("TGT:PROBE", 3)
    contributions = facet_contribution_draws(spec, target, n_draws=10, seed=1)
    dimensions = dimension_draws(spec, target, contributions)
    with pytest.raises(SpecError, match="unknown aggregation method"):
        composite_from_dimensions(spec, target, dimensions, method="harmonic_mean")


def test_full_catalogue_cohort_reports_a_usable_sensitivity_table(spec) -> None:
    """A realistic mixed cohort: the table must be complete and finite."""
    cohort = [
        make_target(f"TGT:T{index:02d}", levels=dict.fromkeys(ALL_FACETS, index % 5))
        for index in range(10)
    ]
    result = score_cohort(make_inputs(cohort), spec, n_draws=DRAWS)
    assert len(result.sensitivity) == 2
    assert len(result.pairwise_sensitivity) == 3
    for name, value in result.pairwise_sensitivity.items():
        assert math.isfinite(value), name
