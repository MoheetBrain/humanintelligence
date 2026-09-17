"""Gates: the caps that no amount of favourable evidence elsewhere can trade away.

Weights permit compensation; caps do not. Contract P4 makes "development is not
adulthood" and "animal memory is not human intelligence" required distinctions rather
than caveats, and README §3 makes safety a constraint rather than a cost. These tests
check that those commitments are arithmetic rather than rhetorical, and — just as
importantly — that each gate *releases* when the evidence that motivated it arrives.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import expected_composite, expected_dimensions, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    GATE_FREE_LEVELS,
    normal_uniform_target,
    make_inputs,
    make_target,
    uniform_target,
)
from blueprint.ranking.inputs import AuditAdjustment

DRAWS = 3000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def _cap(spec, gate_id: str) -> float:
    return next(g.cap for g in spec.gates if g.gate_id == gate_id)


def _scored(spec, target):
    result = score_cohort(make_inputs([target]), spec, n_draws=DRAWS)
    return result.targets[0]


# ---------------------------------------------------------------------------
# D2: developmental confound
# ---------------------------------------------------------------------------


def test_maximal_developmental_confound_caps_d2(spec) -> None:
    """Every other D2 facet at its best, and D2 is still held at the cap."""
    cap = _cap(spec, "developmental_confound_caps_d2")
    target = make_target(
        "TGT:CONFOUNDED",
        levels={
            **GATE_FREE_LEVELS,
            "adult_onset_perturbation": 4,
            "adult_expression_and_timing": 4,
            "developmental_confound_risk": 4,
        },
    )
    scored = _scored(spec, target)
    assert scored.dimensions["D2"].p95 <= cap + 1e-9
    assert "developmental_confound_caps_d2" in scored.dimensions["D2"].gates_applied
    assert expected_dimensions(spec, target)["D2"] == pytest.approx(cap)


def test_the_d2_gate_binds_regardless_of_how_strong_the_rest_of_the_case_is(spec) -> None:
    """The point of a cap: an uncapped weighted mean would let adult-onset evidence
    at level 4 compensate for the confound. It must not."""
    cap = _cap(spec, "developmental_confound_caps_d2")
    weak_elsewhere = make_target(
        "TGT:WEAK", levels={**GATE_FREE_LEVELS, "developmental_confound_risk": 4}
    )
    strong_elsewhere = make_target(
        "TGT:STRONG",
        levels={
            **GATE_FREE_LEVELS,
            "adult_onset_perturbation": 4,
            "adult_expression_and_timing": 4,
            "developmental_confound_risk": 4,
        },
    )
    assert expected_dimensions(spec, weak_elsewhere)["D2"] == pytest.approx(cap)
    assert expected_dimensions(spec, strong_elsewhere)["D2"] == pytest.approx(cap)


def test_the_d2_gate_does_not_bind_below_the_maximal_level(spec) -> None:
    """Level 3 is "converging evidence of developmental dependence", which the spec
    deliberately does not treat as a hard ceiling."""
    target = make_target(
        "TGT:SUSPECT",
        levels={
            **GATE_FREE_LEVELS,
            "adult_onset_perturbation": 4,
            "developmental_confound_risk": 3,
        },
    )
    scored = _scored(spec, target)
    assert "developmental_confound_caps_d2" not in scored.dimensions["D2"].gates_applied
    assert scored.dimensions["D2"].median > _cap(spec, "developmental_confound_caps_d2")


def test_the_d2_gate_releases_when_adult_onset_evidence_answers_the_confound(spec) -> None:
    """``counter_level_at_most: 2`` in the gate condition: replicated adult-onset
    evidence (counter_level 3+) means the confound has been answered, and the ceiling
    lifts. Without this clause the gate would be unfalsifiable."""
    target = make_target(
        "TGT:ANSWERED",
        levels={
            **GATE_FREE_LEVELS,
            "adult_onset_perturbation": 4,
            "adult_expression_and_timing": 4,
            "developmental_confound_risk": 4,
        },
        counter_levels={"developmental_confound_risk": 4},
    )
    scored = _scored(spec, target)
    assert "developmental_confound_caps_d2" not in scored.dimensions["D2"].gates_applied
    assert scored.dimensions["D2"].median > _cap(spec, "developmental_confound_caps_d2")


# ---------------------------------------------------------------------------
# D6: human evidence
# ---------------------------------------------------------------------------


def test_a_target_with_no_human_evidence_cannot_exceed_the_d6_cap(spec) -> None:
    """Every non-human facet maxed out; D6 is still held at the no-human-evidence cap.

    This is contract P4 ("animal memory is not human intelligence") as a ceiling.
    """
    cap = _cap(spec, "no_human_evidence_caps_d6")
    levels = {
        "mechanistic_causal_perturbation": 4,
        "adult_onset_perturbation": 4,
        "above_baseline_enhancement": 4,
        "transfer_breadth": 4,
        "dose_response_knowledge": 4,
        "cross_species_convergence": 4,
        "tractability": 4,
        "causal_gene_attribution": 4,
        "human_lineage_divergence_risk": 0,
        "safety_liability_burden": 0,
        "developmental_confound_risk": 0,
    }
    target = make_target("TGT:RODENT_ONLY", levels=levels)
    scored = _scored(spec, target)
    assert scored.dimensions["D6"].p95 <= cap + 1e-9
    assert "no_human_evidence_caps_d6" in scored.dimensions["D6"].gates_applied


def test_unassessed_human_facets_do_not_release_the_d6_gate(spec) -> None:
    """An unasked question is not human evidence: ``not_assessed`` must not lift the
    ceiling, or a target could reach a high D6 by nobody ever checking."""
    target = make_target("TGT:UNCHECKED", levels={"tractability": 4, "cross_species_convergence": 4})
    scored = _scored(spec, target)
    assert "no_human_evidence_caps_d6" in scored.dimensions["D6"].gates_applied


def test_level_zero_human_evidence_does_not_release_the_d6_gate(spec) -> None:
    """"Searched, nothing found" on every human facet is not human evidence either."""
    target = make_target(
        "TGT:SEARCHED",
        levels={
            "human_genetic_association": 0,
            "human_phenotype_specificity": 0,
            "human_intervention_evidence": 0,
            "adult_expression_and_timing": 1,
            "tractability": 4,
        },
    )
    scored = _scored(spec, target)
    assert "no_human_evidence_caps_d6" in scored.dimensions["D6"].gates_applied


def test_one_human_facet_at_level_two_releases_the_hard_d6_gate(spec) -> None:
    """The gate's threshold is ``max human level < 2``, so a single moderate human
    result lifts the hard ceiling — while the softer intervention ceiling may still
    apply."""
    target = make_target(
        "TGT:SOME_HUMAN",
        levels={"human_genetic_association": 2, "tractability": 4, "cross_species_convergence": 4},
    )
    scored = _scored(spec, target)
    assert "no_human_evidence_caps_d6" not in scored.dimensions["D6"].gates_applied
    assert scored.dimensions["D6"].median > _cap(spec, "no_human_evidence_caps_d6")


def test_the_soft_d6_gate_applies_without_a_human_intervention(spec) -> None:
    """Human genetics plus conservation can look translatable without anyone ever
    having given a human a modulator with a cognitive endpoint. That gap bounds D6."""
    cap = _cap(spec, "no_human_intervention_caps_d6")
    target = make_target(
        "TGT:GENETICS_ONLY",
        levels={
            "human_genetic_association": 4,
            "human_phenotype_specificity": 4,
            "adult_expression_and_timing": 4,
            "cross_species_convergence": 4,
            "tractability": 4,
            "human_lineage_divergence_risk": 0,
        },
    )
    scored = _scored(spec, target)
    assert "no_human_intervention_caps_d6" in scored.dimensions["D6"].gates_applied
    assert scored.dimensions["D6"].p95 <= cap + 1e-9


# ---------------------------------------------------------------------------
# D5: safety
# ---------------------------------------------------------------------------


def test_maximal_safety_liability_caps_d5(spec) -> None:
    """Safety is a constraint, not a weight: a fully characterised exposure-response
    curve cannot buy back a replicated human adverse signal."""
    cap = _cap(spec, "safety_liability_caps_d5")
    target = make_target(
        "TGT:LIABLE",
        levels={**GATE_FREE_LEVELS, "dose_response_knowledge": 4, "safety_liability_burden": 4},
    )
    scored = _scored(spec, target)
    assert scored.dimensions["D5"].p95 <= cap + 1e-9
    assert "safety_liability_caps_d5" in scored.dimensions["D5"].gates_applied


def test_the_safety_cap_is_the_lowest_in_the_spec(spec) -> None:
    """A structural property of the spec, asserted so a future edit cannot quietly
    make some other ceiling harsher than the safety one."""
    caps = {g.gate_id: g.cap for g in spec.gates}
    assert caps["safety_liability_caps_d5"] == min(caps.values())


def test_an_unassessed_safety_facet_is_not_treated_as_safe(spec) -> None:
    """Absence of evidence of harm is never evidence of safety
    (docs/COMPUTATIONAL_ONLY_POLICY.md). An unassessed safety facet must score at the
    uninformative prior, strictly below a documented "searched, nothing found"."""
    unassessed = make_target("TGT:UNKNOWN_SAFETY", levels={"dose_response_knowledge": 2})
    searched = make_target(
        "TGT:SEARCHED_SAFETY",
        levels={"dose_response_knowledge": 2, "safety_liability_burden": 0},
    )
    assert (
        expected_dimensions(spec, unassessed)["D5"] < expected_dimensions(spec, searched)["D5"]
    )


# ---------------------------------------------------------------------------
# Composite: unresolved critical findings
# ---------------------------------------------------------------------------


def test_an_unresolved_critical_finding_caps_the_composite(spec) -> None:
    """The composite cap must still BIND under the conjunctive primary.

    Its value is declared on the dimension-equivalent scale precisely so that it does:
    a flat 0.35 was a real ceiling under the superseded additive composite, where rows
    sat around 0.5, and would be entirely inert against a product of six sub-1
    dimensions. A gate that silently stopped binding when the operator changed would be
    enforcement that looks present and is not.
    """
    gate = next(g for g in spec.gates if g.gate_id == "unresolved_critical_finding_caps_composite")
    cap = gate.cap_for(spec.primary_aggregation)
    clean = normal_uniform_target("TGT:CLEAN", 4, inverse_level=0)
    disputed = normal_uniform_target(
        "TGT:DISPUTED", 4, inverse_level=0, unresolved_critical_findings=1
    )
    result = score_cohort(make_inputs([clean, disputed]), spec, n_draws=DRAWS)
    rows = {t.target_id: t for t in result.targets}
    assert rows["TGT:DISPUTED"].composite_p95 <= cap + 1e-9
    assert rows["TGT:CLEAN"].composite_median > rows["TGT:DISPUTED"].composite_median
    assert "unresolved_critical_finding_caps_composite" in rows["TGT:DISPUTED"].gates_applied


def test_the_composite_cap_is_converted_for_the_operator_in_use(spec) -> None:
    """`cap: 0.35` means "as if every dimension were 0.35", per operator."""
    gate = next(g for g in spec.gates if g.gate_id == "unresolved_critical_finding_caps_composite")
    assert gate.cap_scale == "dimension_equivalent"
    assert gate.cap_for("product") == pytest.approx(0.35**6)
    assert gate.cap_for("minimum") == pytest.approx(0.35)
    assert gate.cap_for("weighted_additive") == pytest.approx(0.35)


def test_an_unconverted_composite_cap_would_be_inert(spec) -> None:
    """Demonstrates that the conversion is load-bearing, not decorative.

    The best possible target's composite under the product operator sits far below the
    raw declared cap of 0.35, so applying the cap unconverted would never bind.
    """
    best = normal_uniform_target("TGT:BEST", 4, inverse_level=0)
    composite = expected_composite(spec, best)
    assert composite < 0.35, (
        "the product composite now exceeds the raw cap, so the dimension-equivalent "
        "conversion may no longer be needed — re-derive rather than assuming"
    )


# ---------------------------------------------------------------------------
# Emergent behaviour worth pinning
# ---------------------------------------------------------------------------


def test_maximal_evidence_on_every_facet_is_not_the_top_rank(spec) -> None:
    """A target with level 4 on all fifteen facets is *not* the best target.

    Level 4 on ``safety_liability_burden`` and ``developmental_confound_risk`` means
    replicated human adverse evidence and a demonstrated developmental confound. Two
    gates bind, and the target is correctly beaten by one with the same benefit
    evidence and documented absence of those risks. This is the single most
    counter-intuitive behaviour of the model, so it is pinned by a test rather than
    left to be rediscovered as a bug.
    """
    everything = uniform_target("TGT:EVERYTHING_AT_4", 4)
    benefit_only = normal_uniform_target("TGT:BENEFIT_AT_4", 4, inverse_level=0)
    result = score_cohort(make_inputs([everything, benefit_only]), spec, n_draws=DRAWS)
    assert result.ranks["TGT:BENEFIT_AT_4"].rank_median < result.ranks["TGT:EVERYTHING_AT_4"].rank_median
    gated = next(t for t in result.targets if t.target_id == "TGT:EVERYTHING_AT_4")
    assert "safety_liability_caps_d5" in gated.gates_applied
    assert "developmental_confound_caps_d2" in gated.gates_applied


def test_every_declared_gate_is_reachable(spec) -> None:
    """No gate in the spec may be unreachable: a condition that can never fire is a
    commitment that looks enforced and is not."""
    reachable: set[str] = set()
    probes = [
        make_target("TGT:P1", levels={**GATE_FREE_LEVELS, "developmental_confound_risk": 4}),
        make_target("TGT:P2", levels={"tractability": 2}),
        make_target("TGT:P3", levels={**GATE_FREE_LEVELS, "safety_liability_burden": 4}),
        make_target(
            "TGT:P4",
            levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 0},
        ),
        normal_uniform_target("TGT:P5", 3, unresolved_critical_findings=2),
    ]
    for probe in probes:
        scored = _scored(spec, probe)
        reachable.update(scored.gates_applied)
    assert {g.gate_id for g in spec.gates} <= reachable


def test_audit_adjustment_can_itself_trigger_a_gate(spec) -> None:
    """A red-team downgrade changes input levels, so it can *release* a gate.

    Downgrading ``developmental_confound_risk`` from 4 to 1 lifts the D2 cap. This is
    correct — the gate reads the evidence grade, and the audit changed the grade —
    but it is worth pinning, because it means an audit can raise a dimension by
    lowering a risk facet. The contract's downgrade-only rule (V12) applies to
    levels, not to their downstream effect.
    """
    target = make_target(
        "TGT:ADJUSTED",
        levels={**GATE_FREE_LEVELS, "adult_onset_perturbation": 4, "developmental_confound_risk": 4},
        adjustments=(
            AuditAdjustment(
                audit_id="AUD:test:001",
                target_id="TGT:ADJUSTED",
                facet="developmental_confound_risk",
                from_level=4,
                to_level=1,
                reason="synthetic fixture",
            ),
        ),
    )
    with_audit = score_cohort(make_inputs([target]), spec, n_draws=DRAWS).targets[0]
    without_audit = score_cohort(
        make_inputs([target]), spec, n_draws=DRAWS, apply_audit_adjustments=False
    ).targets[0]

    assert "developmental_confound_caps_d2" in without_audit.gates_applied
    assert "developmental_confound_caps_d2" not in with_audit.gates_applied
    assert with_audit.dimensions["D2"].median > without_audit.dimensions["D2"].median


def test_all_fifteen_facets_are_represented_in_the_fixture_catalogue(spec) -> None:
    """The fixture builder and the rubric must agree on the facet set."""
    assert set(ALL_FACETS) == set(spec.facets)
