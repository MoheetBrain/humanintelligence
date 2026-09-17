"""Red-team audit effects: downgrades are applied, counted, and downgrade-only.

Contract P6 ("the red team can downgrade, never delete") and rule V12
("``to_level < from_level``") are structural commitments. These tests check that an
audit actually changes the numbers, that the change appears in ``n_downgrades``, that
an upgrade cannot be expressed at all, and that re-auditing can only ratchet a grade
down.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.inputs import AuditAdjustment, AuditSummary
from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import assign_tier, score_cohort
from blueprint.ranking.synthetic import (
    GATE_FREE_LEVELS,
    normal_uniform_target,
    make_inputs,
    make_target,
)

DRAWS = 4000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def _adjust(facet: str, from_level: int, to_level: int, audit_id: str = "AUD:red_team:T:001"):
    return AuditAdjustment(
        audit_id=audit_id,
        target_id="TGT:AUDITED",
        facet=facet,
        from_level=from_level,
        to_level=to_level,
        reason="synthetic fixture: rescue mistaken for enhancement",
    )


def test_a_downgrade_lowers_the_affected_dimension_and_is_counted(spec) -> None:
    """The headline requirement: an audit downgrade must move the number and be
    visible in the report as ``n_downgrades``."""
    target = make_target(
        "TGT:AUDITED",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 3},
        verdict="retain_with_downgrade",
        adjustments=(_adjust("above_baseline_enhancement", 3, 1),),
    )
    inputs = make_inputs([target])

    with_audit = score_cohort(inputs, spec, n_draws=DRAWS).targets[0]
    without_audit = score_cohort(
        inputs, spec, n_draws=DRAWS, apply_audit_adjustments=False
    ).targets[0]

    # above_baseline_enhancement is the sole input to D3.
    assert with_audit.dimensions["D3"].median < without_audit.dimensions["D3"].median
    assert with_audit.composite_median < without_audit.composite_median
    assert with_audit.n_downgrades == 1
    assert with_audit.red_team_verdict == "retain_with_downgrade"


def test_a_downgrade_is_reflected_in_the_reported_dimension_level(spec) -> None:
    """``d3_level`` must show the downgraded grade, not the atlas's original claim."""
    target = make_target(
        "TGT:AUDITED",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 4},
        adjustments=(_adjust("above_baseline_enhancement", 4, 1),),
    )
    scored = score_cohort(make_inputs([target]), spec, n_draws=DRAWS).targets[0]
    assert scored.dimensions["D3"].level == 1


def test_a_downgrade_changes_the_ranking(spec) -> None:
    """Not merely the score: the audit must be able to move a target's position."""
    audited = make_target(
        "TGT:AUDITED",
        levels=dict.fromkeys(("above_baseline_enhancement", "transfer_breadth"), 4)
        | {**GATE_FREE_LEVELS, "mechanistic_causal_perturbation": 4},
        adjustments=(
            _adjust("above_baseline_enhancement", 4, 0),
            _adjust("mechanistic_causal_perturbation", 4, 0),
        ),
    )
    rival = make_target(
        "TGT:RIVAL",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 2, "mechanistic_causal_perturbation": 2},
    )
    inputs = make_inputs([audited, rival])

    before = score_cohort(inputs, spec, n_draws=DRAWS, apply_audit_adjustments=False)
    after = score_cohort(inputs, spec, n_draws=DRAWS)

    assert before.ranks["TGT:AUDITED"].rank_median < before.ranks["TGT:RIVAL"].rank_median
    assert after.ranks["TGT:AUDITED"].rank_median > after.ranks["TGT:RIVAL"].rank_median


def test_multiple_downgrades_are_all_counted(spec) -> None:
    target = make_target(
        "TGT:AUDITED",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 3, "transfer_breadth": 3},
        adjustments=(
            _adjust("above_baseline_enhancement", 3, 1),
            _adjust("transfer_breadth", 3, 2),
        ),
    )
    scored = score_cohort(make_inputs([target]), spec, n_draws=DRAWS).targets[0]
    assert scored.n_downgrades == 2


def test_the_lowest_downgrade_wins_when_audits_disagree(spec) -> None:
    """Provenance is append-only, so re-auditing can only ratchet a grade down.

    Two audits touch the same facet with different targets (level 2 and level 0). The
    model takes the lowest, so a later, more lenient audit cannot silently undo an
    earlier stricter one — that would require an explicit record, which the contract
    handles as a new audit finding, not as an overwrite.
    """
    target = make_target(
        "TGT:AUDITED",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 4},
        adjustments=(
            _adjust("above_baseline_enhancement", 4, 2, audit_id="AUD:red_team:T:001"),
            _adjust("above_baseline_enhancement", 4, 0, audit_id="AUD:red_team:T:002"),
        ),
    )
    adjusted = target.with_audit_adjustments_applied()
    assert adjusted.facet("above_baseline_enhancement").level == 0


def test_a_downgrade_never_raises_a_level(spec) -> None:
    """If an atlas already graded a facet below the audit's ``to_level``, the audit
    must not lift it."""
    target = make_target(
        "TGT:AUDITED",
        levels={"above_baseline_enhancement": 1},
        adjustments=(_adjust("above_baseline_enhancement", 4, 3),),
    )
    adjusted = target.with_audit_adjustments_applied()
    assert adjusted.facet("above_baseline_enhancement").level == 1


def test_an_upgrade_cannot_be_constructed_at_all() -> None:
    """Contract rule V12 enforced at the type level, so a malformed audit record
    cannot silently raise a score."""
    with pytest.raises(ValueError, match="not a downgrade"):
        AuditAdjustment(
            audit_id="AUD:red_team:T:001",
            target_id="TGT:AUDITED",
            facet="above_baseline_enhancement",
            from_level=1,
            to_level=3,
        )
    with pytest.raises(ValueError, match="not a downgrade"):
        AuditAdjustment(
            audit_id="AUD:red_team:T:001",
            target_id="TGT:AUDITED",
            facet="above_baseline_enhancement",
            from_level=2,
            to_level=2,
        )


def test_an_adjustment_on_an_unassessed_facet_records_the_audit_grade(spec) -> None:
    """The red team may grade a facet the lead atlas never assessed (it owns two
    facets and may downgrade others). The adjustment then supplies the level, and the
    facet stops being ``not_assessed`` — which raises coverage, correctly: someone
    did look."""
    target = make_target(
        "TGT:AUDITED",
        levels={"tractability": 2},
        adjustments=(_adjust("above_baseline_enhancement", 3, 1),),
    )
    adjusted = target.with_audit_adjustments_applied()
    assert adjusted.facet("above_baseline_enhancement").is_assessed
    assert adjusted.facet("above_baseline_enhancement").level == 1


def test_an_adjustment_cannot_revive_a_not_applicable_facet(spec) -> None:
    target = make_target(
        "TGT:AUDITED",
        levels={"tractability": 2},
        not_applicable=["above_baseline_enhancement"],
        adjustments=(_adjust("above_baseline_enhancement", 3, 1),),
    )
    adjusted = target.with_audit_adjustments_applied()
    assert adjusted.facet("above_baseline_enhancement").assessment_status == "not_applicable"


# ---------------------------------------------------------------------------
# Verdicts and tiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verdict", ["deprioritise", "insufficient_evidence"])
def test_a_demoting_verdict_forces_the_bottom_tier(spec, verdict) -> None:
    """Regardless of how well the target scores: a red-team demotion is categorical,
    not a numeric adjustment."""
    tier = assign_tier(
        spec,
        coverage=1.0,
        is_audited=True,
        verdict=verdict,
        rank_median=1.0,
        rank_p95=1.0,
        n_targets=20,
    )
    assert tier == "tier_4_deprioritised_by_audit"


def test_an_unaudited_target_is_tiered_as_insufficient(spec) -> None:
    """Gate G4/V15: every seed target needs an audit. Until it has one, its rank is
    not a basis for prioritising work, however good it looks."""
    tier = assign_tier(
        spec,
        coverage=1.0,
        is_audited=False,
        verdict=None,
        rank_median=1.0,
        rank_p95=1.0,
        n_targets=20,
    )
    assert tier == "tier_3_insufficient_coverage"


def test_low_coverage_is_tiered_as_insufficient(spec) -> None:
    tier = assign_tier(
        spec,
        coverage=float(spec.tiers["min_coverage"]) / 2,
        is_audited=True,
        verdict="retain",
        rank_median=1.0,
        rank_p95=1.0,
        n_targets=20,
    )
    assert tier == "tier_3_insufficient_coverage"


def test_tier_one_requires_the_pessimistic_end_of_the_rank_interval(spec) -> None:
    """``rank_p95``, not ``rank_median``: a target only reaches tier 1 if it ranks
    high even at the unfavourable end of its own interval."""
    top = assign_tier(
        spec, coverage=1.0, is_audited=True, verdict="retain",
        rank_median=2.0, rank_p95=3.0, n_targets=20,
    )
    wide = assign_tier(
        spec, coverage=1.0, is_audited=True, verdict="retain",
        rank_median=2.0, rank_p95=18.0, n_targets=20,
    )
    assert top == "tier_1_analyse_next"
    assert wide == "tier_2_promising_underdetermined"


def test_verdict_and_audit_state_reach_the_scored_row(spec) -> None:
    target = normal_uniform_target("TGT:AUDITED", 3, verdict="retain_with_downgrade")
    scored = score_cohort(make_inputs([target]), spec, n_draws=DRAWS).targets[0]
    assert scored.red_team_verdict == "retain_with_downgrade"
    assert scored.is_audited is True


def test_an_unaudited_summary_reports_no_verdict() -> None:
    summary = AuditSummary()
    assert summary.verdict is None
    assert summary.is_audited is False
    assert summary.is_demoted is False
    assert summary.n_downgrades == 0
