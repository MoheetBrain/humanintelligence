"""Gate G5 — virtual pharmacology may act only on targets that survived review.

``docs/BLACKBOARD_PROTOCOL.md`` §3 defines the gate; these tests are what make it real.
The refusals matter more than the passes: a gate that can be talked past is not a gate,
and the failure mode being guarded against is a chemistry programme aimed at a target
whose causal case was never established (``ROADMAP.md``, opening paragraph).

This file is named ``test_ranking_*`` to sit in this agent's lane
(``docs/OWNERSHIP.yaml``), which also owns ``src/blueprint/pharmacology/**``.
"""

from __future__ import annotations

import pytest

from blueprint.pharmacology import GATE_ID, SPRINT
from blueprint.pharmacology.gates import (
    DEMOTING_VERDICTS,
    MINIMUM_COVERAGE,
    eligible_for_chemistry,
    explain_gate,
)
from blueprint.pharmacology.interfaces import (
    GateNotPassedError,
    NOT_IMPLEMENTED_MESSAGE,
    detect_pockets,
    dock_ligands,
    multi_objective_optimise,
    predict_admet,
    require_gate,
    retrieve_structures,
)

TARGET = {"target_id": "TGT:EXAMPLE", "symbol": "EXAMPLE"}


def _row(**overrides):
    """A ranking row that passes the gate, before overrides."""
    row = {
        "coverage": 0.80,
        "red_team_verdict": "retain",
        "tier": "tier_1_analyse_next",
        "unresolved_critical_findings": 0,
    }
    row.update(overrides)
    return row


def _audit(**overrides):
    audit = {"audit_id": "AUD:red_team:EXAMPLE:001", "verdict": "retain", "findings": []}
    audit.update(overrides)
    return audit


# ---------------------------------------------------------------------------
# Refusals — the point of the gate
# ---------------------------------------------------------------------------


def test_the_gate_refuses_a_target_with_a_deprioritise_verdict() -> None:
    """The headline requirement. A red-team demotion is categorical: no amount of
    favourable evidence elsewhere reopens the door."""
    eligible, reason = eligible_for_chemistry(
        TARGET,
        _row(red_team_verdict="deprioritise", tier="tier_4_deprioritised_by_audit"),
        [_audit(verdict="deprioritise")],
    )
    assert eligible is False
    assert "deprioritise" in reason
    assert "demoted by audit" in reason


def test_a_deprioritise_verdict_in_the_audit_alone_is_enough() -> None:
    """Even with a stale ranking row that still says ``retain``: the audit records are
    the authority on the verdict, and disagreement must fail closed."""
    eligible, reason = eligible_for_chemistry(
        TARGET, _row(red_team_verdict="retain"), [_audit(verdict="deprioritise")]
    )
    assert eligible is False
    assert "deprioritise" in reason


@pytest.mark.parametrize("verdict", sorted(DEMOTING_VERDICTS))
def test_every_demoting_verdict_refuses(verdict) -> None:
    eligible, _ = eligible_for_chemistry(TARGET, _row(red_team_verdict=verdict), [_audit(verdict=verdict)])
    assert eligible is False


def test_the_gate_refuses_an_unresolved_critical_finding() -> None:
    """A disputed evidence base is not a foundation for chemistry."""
    eligible, reason = eligible_for_chemistry(
        TARGET, _row(unresolved_critical_findings=1), [_audit()]
    )
    assert eligible is False
    assert "unresolved critical" in reason
    assert "under active dispute" in reason


def test_an_unresolved_critical_finding_in_the_audit_alone_is_enough() -> None:
    eligible, reason = eligible_for_chemistry(
        TARGET,
        _row(),
        [_audit(findings=[{"severity": "critical", "description": "synthetic"}])],
    )
    assert eligible is False
    assert "unresolved critical" in reason


def test_a_resolved_critical_finding_does_not_refuse() -> None:
    eligible, _ = eligible_for_chemistry(
        TARGET,
        _row(),
        [
            _audit(
                findings=[
                    {"severity": "critical", "resolution_status": "resolved", "description": "x"}
                ]
            )
        ],
    )
    assert eligible is True


def test_the_gate_refuses_an_unaudited_target() -> None:
    """Gate G4 / validator rule V15: every seed target needs an audit first."""
    eligible, reason = eligible_for_chemistry(TARGET, _row(red_team_verdict="not_audited"), [])
    assert eligible is False
    assert "no red-team audit" in reason


def test_the_gate_refuses_a_target_with_no_ranking_row() -> None:
    """No row means the target never went through causal integration at all."""
    eligible, reason = eligible_for_chemistry(TARGET, None, [_audit()])
    assert eligible is False
    assert "not been through causal integration" in reason


def test_the_gate_refuses_insufficient_coverage() -> None:
    eligible, reason = eligible_for_chemistry(TARGET, _row(coverage=0.1), [_audit()])
    assert eligible is False
    assert "below the required" in reason


def test_the_gate_refuses_a_target_the_ranking_model_itself_demoted() -> None:
    for tier in ("tier_3_insufficient_coverage", "tier_4_deprioritised_by_audit"):
        eligible, reason = eligible_for_chemistry(TARGET, _row(tier=tier), [_audit()])
        assert eligible is False, tier
        assert "does not regard this row" in reason


def test_a_refusal_names_every_failing_condition() -> None:
    """A refusal nobody understands gets worked around."""
    decision = explain_gate(
        TARGET,
        _row(coverage=0.05, red_team_verdict="deprioritise", tier="tier_4_deprioritised_by_audit",
             unresolved_critical_findings=2),
        [_audit(verdict="deprioritise")],
    )
    assert decision.eligible is False
    assert set(decision.failures) == {
        "no_demoting_verdict",
        "no_unresolved_critical_finding",
        "meets_minimum_coverage",
        "not_tiered_insufficient",
    }
    for fragment in ("deprioritise", "unresolved critical", "below the required", "tier"):
        assert fragment in decision.reason


def test_the_gate_cannot_be_weakened_by_its_caller() -> None:
    """A caller that can lower the floor is not a gate."""
    with pytest.raises(ValueError, match="below the gate's floor"):
        eligible_for_chemistry(TARGET, _row(), [_audit()], minimum_coverage=0.0)


def test_the_coverage_floor_matches_the_ranking_model_threshold() -> None:
    """A target the ranking model calls under-curated must not pass the chemistry gate."""
    from blueprint.ranking.rubric import load_model_spec

    assert MINIMUM_COVERAGE == float(load_model_spec().tiers["min_coverage"])


# ---------------------------------------------------------------------------
# Passing, and what passing does not mean
# ---------------------------------------------------------------------------


def test_a_fully_reviewed_target_passes() -> None:
    eligible, reason = eligible_for_chemistry(TARGET, _row(), [_audit()])
    assert eligible is True
    assert "passes gate G5" in reason


def test_passing_states_what_it_does_not_mean() -> None:
    """The reason string is the only thing a downstream reader may see."""
    _, reason = eligible_for_chemistry(TARGET, _row(), [_audit()])
    assert "IN-SILICO analysis only" in reason
    assert "not a claim that the target is validated" in reason
    assert "protocol, dose, route or sourcing route" in reason


def test_the_decision_is_truthy_and_carries_every_check() -> None:
    decision = explain_gate(TARGET, _row(), [_audit()])
    assert bool(decision) is True
    assert decision.failures == ()
    assert set(decision.checks) == {
        "has_ranking_row",
        "has_red_team_audit",
        "no_demoting_verdict",
        "no_unresolved_critical_finding",
        "meets_minimum_coverage",
        "not_tiered_insufficient",
    }
    assert all(decision.checks.values())


def test_the_gate_accepts_a_scored_row_object_as_well_as_a_mapping() -> None:
    """The row may arrive as a CSV dict or as a TargetScore; both must work."""
    from blueprint.ranking.rubric import load_model_spec
    from blueprint.ranking.score import score_cohort
    from blueprint.ranking.synthetic import GATE_FREE_LEVELS, make_inputs, make_target

    spec = load_model_spec()
    target = make_target("TGT:EXAMPLE", levels={**GATE_FREE_LEVELS}, verdict="retain")
    scored = score_cohort(make_inputs([target]), spec, n_draws=500).targets[0]
    decision = explain_gate(TARGET, scored, [_audit()])
    # The tier is not on TargetScore, so `not_tiered_insufficient` passes vacuously;
    # what matters is that the coverage and verdict were read off the object.
    assert decision.checks["meets_minimum_coverage"] is True
    assert decision.checks["no_demoting_verdict"] is True


# ---------------------------------------------------------------------------
# The interfaces stay inactive
# ---------------------------------------------------------------------------


def test_every_interface_refuses_without_a_gate_decision() -> None:
    """Gate G5 cannot be satisfied by passing a truthy value."""
    for function in (retrieve_structures, predict_admet, detect_pockets):
        with pytest.raises(GateNotPassedError, match="cannot be satisfied by passing a truthy value"):
            function("TGT:EXAMPLE", True)  # type: ignore[arg-type]


def test_every_interface_refuses_a_failed_gate_decision() -> None:
    refused = explain_gate(TARGET, _row(red_team_verdict="deprioritise"), [_audit(verdict="deprioritise")])
    with pytest.raises(GateNotPassedError, match="refused by gate G5"):
        retrieve_structures("TGT:EXAMPLE", refused)


def test_every_interface_raises_not_implemented_once_the_gate_passes() -> None:
    passed = explain_gate(TARGET, _row(), [_audit()])
    calls = [
        (retrieve_structures, ("TGT:EXAMPLE", passed)),
        (detect_pockets, ((), passed)),
        (predict_admet, ((), passed)),
        (multi_objective_optimise, ((), passed)),
    ]
    for function, args in calls:
        with pytest.raises(NotImplementedError) as error:
            function(*args)
        message = str(error.value)
        assert "interface only and is not implemented" in message
        assert "G5" in message
        assert "Sprint 4" in message
        assert "in silico" in message
        assert "protocol, dose, route or sourcing route" in message


def test_the_not_implemented_message_names_the_gate_and_the_sprint() -> None:
    message = NOT_IMPLEMENTED_MESSAGE.format(name="anything")
    assert "G5" in message and "Sprint 4" in message
    assert GATE_ID == "G5"
    assert SPRINT == 4


def test_require_gate_returns_the_decision_unchanged_on_a_pass() -> None:
    passed = explain_gate(TARGET, _row(), [_audit()])
    assert require_gate(passed, what="test") is passed


def test_docking_is_gated_like_everything_else() -> None:
    from blueprint.pharmacology.interfaces import Pocket

    refused = explain_gate(TARGET, _row(coverage=0.0), [_audit()])
    pocket = Pocket(pocket_id="p1", structure_identifier="s1", residues=())
    with pytest.raises(GateNotPassedError):
        dock_ligands((), pocket, refused)


def test_no_interface_signature_mentions_a_dose_or_a_route() -> None:
    """A crude but load-bearing check: the vocabulary of exposure must not appear in
    this module's public surface, because the shape of an API is what invites the next
    person to fill it in."""
    import inspect

    from blueprint.pharmacology import interfaces

    forbidden = ("dose", "regimen", "route_of_administration", "posology", "sourcing")
    for name, obj in vars(interfaces).items():
        if name.startswith("_") or not callable(obj) or not hasattr(obj, "__code__"):
            continue
        signature = str(inspect.signature(obj)).lower()
        for token in forbidden:
            assert token not in signature, f"{name} signature mentions {token!r}"


def test_the_multi_objective_interface_separates_constraints_from_objectives() -> None:
    """Safety is a constraint, not a cost (README §3). The signature must make that
    structurally expressible, so an implementation can refuse the wrong configuration."""
    import inspect

    from blueprint.pharmacology.interfaces import MultiObjectiveResult, multi_objective_optimise

    parameters = inspect.signature(multi_objective_optimise).parameters
    assert "objectives" in parameters
    assert "hard_constraints" in parameters
    assert "constraints_enforced" in MultiObjectiveResult.__dataclass_fields__
