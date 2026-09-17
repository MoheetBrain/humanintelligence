"""Polarity-aware methodological caps — contract §5.4.

The bug this file exists to prevent is real and was found in this repository:
``agent:comparative`` applied "a claim with ``phylogenetic_control: none`` may not be
graded above level 2" to ``human_lineage_divergence_risk``, an inverse-polarity facet.
Capping the *risk* grade made a target with documented human/mouse physiological
divergence look **more** translatable than its evidence supports — a methodological
weakness turned into an optimistic conclusion.

The rule (contract §5.4): a cap applies only in the direction that disfavours the
target. Normal polarity caps ``level``; inverse polarity caps ``counter_level`` and
**never** ``level``.

The headline test is :func:`test_polarity_aware_cap_cannot_flatter_a_target`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from blueprint.ranking.caps import (
    CapApplication,
    MethodologicalCap,
    apply_methodological_cap,
    apply_methodological_caps,
    cap_field_for,
    caps_from_records,
)
from blueprint.ranking.rubric import SpecError, load_model_spec
from blueprint.ranking.score import expected_composite, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    GATE_FREE_LEVELS,
    INVERSE_FACETS,
    NORMAL_FACETS,
    make_inputs,
    make_target,
)

DRAWS = 4000

#: The motivating case: the comparative agent's phylogenetic-control rule.
PHYLOGENETIC_CAP_LEVEL = 2
PHYLOGENETIC_REASON = "phylogenetic_control: none — convergence not phylogenetically corrected"


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


# ---------------------------------------------------------------------------
# The headline test
# ---------------------------------------------------------------------------


def test_polarity_aware_cap_cannot_flatter_a_target(spec) -> None:
    """A methodological cap on an inverse-polarity facet must not improve the target.

    Setup is the real case. ``human_lineage_divergence_risk`` is graded 4 — replicated
    direct human-versus-model comparisons showing a divergence that bears on the
    mechanism — from claims that carry no phylogenetic control. The comparative rule
    would cap that grade at 2.

    Three things must hold:

    1. ``level`` is untouched. A weak method cannot establish the ABSENCE of a risk,
       so the risk grade stands.
    2. ``counter_level`` is what the cap constrains.
    3. The target's composite does not RISE. This is the assertion that would have
       caught the original bug: capping the risk raised D6 and made the target look
       more translatable.
    """
    facet_name = "human_lineage_divergence_risk"
    before = make_target(
        "TGT:DIVERGENT",
        levels={**GATE_FREE_LEVELS, facet_name: 4, "cross_species_convergence": 3},
        counter_levels={facet_name: 4},
    )
    cap = MethodologicalCap(
        facet=facet_name,
        max_level=PHYLOGENETIC_CAP_LEVEL,
        reason=PHYLOGENETIC_REASON,
        imposed_by="agent:comparative",
    )
    after, records = apply_methodological_caps(spec, before, [cap])
    record = records[0]

    # 1. the risk grade is untouched
    assert after.facet(facet_name).level == 4, (
        "the cap lowered `level` on an inverse-polarity facet, which converts a "
        "methodological weakness into an optimistic conclusion (contract §5.4)"
    )
    assert record.field_capped == "counter_level"
    assert record.polarity == "inverse"

    # 2. the counter grade is what moved
    assert before.facet(facet_name).counter_level == 4
    assert after.facet(facet_name).counter_level == PHYLOGENETIC_CAP_LEVEL
    assert record.applied is True

    # 3. the target is not flattered
    composite_before = expected_composite(spec, before)
    composite_after = expected_composite(spec, after)
    assert composite_after <= composite_before, (
        f"the cap raised the composite ({composite_before:.6f} -> {composite_after:.6f}); "
        "a methodological weakness must never improve a target's standing"
    )
    assert composite_after < composite_before, (
        "the cap should have bitten on counter_level and lowered the composite"
    )


def test_the_wrong_implementation_would_have_flattered_the_target(spec) -> None:
    """Demonstrates that the bug was reachable, so the test above is not vacuous.

    Applying the cap to ``level`` — the naive ``min(level, 2)`` a call site would
    write — visibly RAISES the composite on the same fixture. The assertion here is
    on the wrong behaviour, to document what the correct behaviour is avoiding.
    """
    from dataclasses import replace

    facet_name = "human_lineage_divergence_risk"
    before = make_target(
        "TGT:DIVERGENT",
        levels={**GATE_FREE_LEVELS, facet_name: 4, "cross_species_convergence": 3},
        counter_levels={facet_name: 4},
    )
    wrong_facets = dict(before.facets)
    wrong_facets[facet_name] = replace(
        wrong_facets[facet_name], level=PHYLOGENETIC_CAP_LEVEL
    )
    wrongly_capped = replace(before, facets=wrong_facets)

    assert expected_composite(spec, wrongly_capped) > expected_composite(spec, before), (
        "the naive cap-on-level implementation no longer flatters the target, so this "
        "regression test has lost its meaning and should be re-derived"
    )


@pytest.mark.parametrize("facet_name", INVERSE_FACETS)
def test_no_inverse_facet_can_have_its_level_capped(spec, facet_name) -> None:
    """Every inverse facet, not just the one that triggered the amendment."""
    target = make_target("TGT:PROBE", levels={**GATE_FREE_LEVELS, facet_name: 4}, counter_levels={facet_name: 4})
    capped, records = apply_methodological_caps(
        spec, target, [MethodologicalCap(facet_name, 1, "synthetic weak method")]
    )
    assert capped.facet(facet_name).level == 4
    assert capped.facet(facet_name).counter_level == 1
    assert records[0].field_capped == "counter_level"
    assert expected_composite(spec, capped) <= expected_composite(spec, target)


@pytest.mark.parametrize("facet_name", NORMAL_FACETS)
def test_a_normal_facet_has_its_level_capped_and_is_not_flattered(spec, facet_name) -> None:
    """Normal polarity: a weak method cannot establish strong support."""
    target = make_target("TGT:PROBE", levels={**GATE_FREE_LEVELS, facet_name: 4}, counter_levels={facet_name: 4})
    capped, records = apply_methodological_caps(
        spec, target, [MethodologicalCap(facet_name, PHYLOGENETIC_CAP_LEVEL, PHYLOGENETIC_REASON)]
    )
    assert capped.facet(facet_name).level == PHYLOGENETIC_CAP_LEVEL
    assert capped.facet(facet_name).counter_level == 4, "the cap touched counter_level on a normal facet"
    assert records[0].field_capped == "level"
    assert expected_composite(spec, capped) <= expected_composite(spec, target)


@pytest.mark.parametrize("facet_name", ALL_FACETS)
def test_a_cap_never_raises_the_composite_for_any_facet(spec, facet_name) -> None:
    """The invariant in its most general form: no cap, on any facet, at any limit,
    may improve a target."""
    for limit in range(5):
        target = make_target(
            "TGT:PROBE",
            levels={**GATE_FREE_LEVELS, facet_name: 4},
            counter_levels={facet_name: 4},
        )
        capped, _ = apply_methodological_caps(
            spec, target, [MethodologicalCap(facet_name, limit, "synthetic weak method")]
        )
        assert expected_composite(spec, capped) <= expected_composite(spec, target) + 1e-12, (
            f"{facet_name}: cap at {limit} raised the composite"
        )


def test_the_invariant_holds_on_the_sampled_path_too(spec) -> None:
    """Not only analytically: the reported rank must not improve either."""
    facet_name = "human_lineage_divergence_risk"
    before = make_target(
        "TGT:DIVERGENT",
        levels={**GATE_FREE_LEVELS, facet_name: 4, "cross_species_convergence": 3},
        counter_levels={facet_name: 4},
    )
    after, _ = apply_methodological_caps(
        spec, before, [MethodologicalCap(facet_name, PHYLOGENETIC_CAP_LEVEL, PHYLOGENETIC_REASON)]
    )
    rival = make_target("TGT:RIVAL", levels={**GATE_FREE_LEVELS, "cross_species_convergence": 3})

    uncapped = score_cohort(make_inputs([before, rival]), spec, n_draws=DRAWS)
    capped = score_cohort(make_inputs([after, rival]), spec, n_draws=DRAWS)
    assert (
        capped.ranks["TGT:DIVERGENT"].rank_median >= uncapped.ranks["TGT:DIVERGENT"].rank_median
    )


# ---------------------------------------------------------------------------
# Mechanics of the single helper
# ---------------------------------------------------------------------------


def test_cap_field_for_maps_polarity_to_field() -> None:
    assert cap_field_for("normal") == "level"
    assert cap_field_for("inverse") == "counter_level"
    assert cap_field_for("direct") == "level"  # deprecated alias, normalised


def test_cap_field_for_refuses_to_guess() -> None:
    """Guessing a polarity is how the original bug becomes reachable again."""
    with pytest.raises(SpecError, match="unknown polarity"):
        cap_field_for("reversed")


def test_a_non_binding_cap_changes_nothing_and_says_so(spec) -> None:
    target = make_target("TGT:PROBE", levels={"tractability": 1})
    capped, records = apply_methodological_caps(
        spec, target, [MethodologicalCap("tractability", 3, "synthetic weak method")]
    )
    assert capped.facet("tractability").level == 1
    assert records[0].applied is False
    assert "not binding" in records[0].summary


def test_a_cap_does_not_manufacture_an_assessment(spec) -> None:
    """An unassessed facet is not capped into being assessed: "nobody looked" must not
    become "someone looked and found at most this much"."""
    target = make_target("TGT:PROBE", levels={"tractability": 2})
    capped, records = apply_methodological_caps(
        spec, target, [MethodologicalCap("above_baseline_enhancement", 1, "synthetic weak method")]
    )
    assessment = capped.facet("above_baseline_enhancement")
    assert assessment.assessment_status == "not_assessed"
    assert assessment.level is None
    assert records[0].applied is False


def test_a_cap_on_an_inverse_facet_with_no_counter_grade_does_nothing(spec) -> None:
    """There is nothing to cap: the risk grade is out of bounds by rule, and no
    ``counter_level`` was recorded. Manufacturing one would assert that somebody
    looked for the absence of the risk."""
    target = make_target("TGT:PROBE", levels={"safety_liability_burden": 3})
    capped, records = apply_methodological_caps(
        spec, target, [MethodologicalCap("safety_liability_burden", 1, "synthetic weak method")]
    )
    assert capped.facet("safety_liability_burden").level == 3
    assert capped.facet("safety_liability_burden").counter_level is None
    assert records[0].applied is False


def test_the_lowest_cap_wins_when_several_apply(spec) -> None:
    """Caps ratchet down only, so imposing two cannot undo the stricter one."""
    target = make_target("TGT:PROBE", levels={**GATE_FREE_LEVELS, "tractability": 4})
    capped, records = apply_methodological_caps(
        spec,
        target,
        [
            MethodologicalCap("tractability", 3, "weak method A"),
            MethodologicalCap("tractability", 1, "weak method B"),
        ],
    )
    assert capped.facet("tractability").level == 1
    assert len(records) == 1
    assert records[0].max_level == 1


def test_a_cap_must_state_a_reason() -> None:
    """An unexplained cap is not auditable."""
    with pytest.raises(ValueError, match="must state its reason"):
        MethodologicalCap("tractability", 2, "   ")


def test_a_cap_level_must_be_on_the_scale() -> None:
    with pytest.raises(ValueError, match="outside 0..4"):
        MethodologicalCap("tractability", 7, "synthetic")


def test_capping_an_unknown_facet_is_an_error(spec) -> None:
    target = make_target("TGT:PROBE", levels={"tractability": 2})
    with pytest.raises(SpecError, match="cannot cap unknown facet"):
        apply_methodological_caps(spec, target, [MethodologicalCap("not_a_facet", 2, "synthetic")])


def test_a_mismatched_assessment_is_an_error(spec) -> None:
    target = make_target("TGT:PROBE", levels={"tractability": 4})
    with pytest.raises(SpecError, match="but was given an assessment of"):
        apply_methodological_cap(
            spec,
            target.facet("tractability"),
            MethodologicalCap("transfer_breadth", 2, "synthetic"),
        )


def test_cap_applications_are_reportable(spec) -> None:
    target = make_target("TGT:PROBE", levels={**GATE_FREE_LEVELS, "cross_species_convergence": 4})
    _, records = apply_methodological_caps(
        spec, target, [MethodologicalCap("cross_species_convergence", 2, PHYLOGENETIC_REASON)]
    )
    record = records[0]
    assert isinstance(record, CapApplication)
    assert record.reason == PHYLOGENETIC_REASON
    assert "cross_species_convergence" in record.summary
    assert "level 4 -> 2" in record.summary.replace("level ", "level ")


def test_caps_can_be_built_from_curated_records(spec) -> None:
    caps = caps_from_records(
        [
            {
                "facet": "cross_species_convergence",
                "max_level": 2,
                "reason": PHYLOGENETIC_REASON,
                "imposed_by": "agent:comparative",
            },
            {"facet": "tractability"},  # incomplete: skipped, never defaulted
            {"facet": "transfer_breadth", "max_level": 1},  # no reason: skipped
        ]
    )
    assert len(caps) == 1
    assert caps[0].facet == "cross_species_convergence"
    assert caps[0].imposed_by == "agent:comparative"


# ---------------------------------------------------------------------------
# The rubric is the polarity authority (contract §5.4)
# ---------------------------------------------------------------------------


def test_the_rubric_publishes_polarity_in_a_stable_shape(spec) -> None:
    """Other agents' checkers read this file, so the keys they read are asserted here."""
    document = yaml.safe_load(Path(spec.paths["rubric"]).read_text(encoding="utf-8"))
    assert "THIS FILE IS THE SOURCE OF TRUTH FOR FACET POLARITY" in Path(
        spec.paths["rubric"]
    ).read_text(encoding="utf-8")
    for entry in document["facets"]:
        assert entry["polarity"] in ("normal", "inverse"), entry["facet"]
        assert entry["methodological_cap_applies_to"] in ("level", "counter_level"), entry["facet"]
        expected = "counter_level" if entry["polarity"] == "inverse" else "level"
        assert entry["methodological_cap_applies_to"] == expected, entry["facet"]


def test_the_flat_polarity_index_agrees_with_the_facet_list(spec) -> None:
    document = yaml.safe_load(Path(spec.paths["rubric"]).read_text(encoding="utf-8"))
    index = document["polarity_index"]
    from_facets = {entry["facet"]: entry["polarity"] for entry in document["facets"]}
    assert index == from_facets
    assert {name for name, p in index.items() if p == "inverse"} == set(INVERSE_FACETS)


def test_the_rubric_states_the_cap_rule_and_names_the_single_implementation(spec) -> None:
    document = yaml.safe_load(Path(spec.paths["rubric"]).read_text(encoding="utf-8"))
    rule = document["methodological_cap_rule"]
    assert "cap `counter_level`, NEVER `level`" in rule
    assert "caps.py" in rule


def test_the_loader_rejects_a_contradictory_cap_field(tmp_path, spec) -> None:
    """Declaring ``methodological_cap_applies_to: level`` on an inverse facet must
    fail at load time, not produce a model that flatters targets."""
    root = tmp_path / "repo"
    relpaths = {
        "rubric": "models/ranking/facet_rubric_v0_1.yaml",
        "ranking": "models/ranking/ranking_spec_v0_1.yaml",
        "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
    }
    for name, relpath in relpaths.items():
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spec.paths[name], destination)

    path = root / relpaths["rubric"]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in document["facets"]:
        if entry["facet"] == "safety_liability_burden":
            entry["methodological_cap_applies_to"] = "level"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    with pytest.raises(SpecError, match="optimistic conclusion"):
        load_model_spec(root)


def test_the_loader_rejects_a_drifted_polarity_index(tmp_path, spec) -> None:
    root = tmp_path / "repo"
    relpaths = {
        "rubric": "models/ranking/facet_rubric_v0_1.yaml",
        "ranking": "models/ranking/ranking_spec_v0_1.yaml",
        "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
    }
    for name, relpath in relpaths.items():
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spec.paths[name], destination)

    path = root / relpaths["rubric"]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["polarity_index"]["safety_liability_burden"] = "normal"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    with pytest.raises(SpecError, match="polarity_index disagrees"):
        load_model_spec(root)


def test_the_deprecated_direct_alias_still_loads(tmp_path, spec) -> None:
    """A checker or record written against the earlier spelling must not break."""
    root = tmp_path / "repo"
    relpaths = {
        "rubric": "models/ranking/facet_rubric_v0_1.yaml",
        "ranking": "models/ranking/ranking_spec_v0_1.yaml",
        "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
    }
    for name, relpath in relpaths.items():
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spec.paths[name], destination)

    path = root / relpaths["rubric"]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in document["facets"]:
        if entry["facet"] == "tractability":
            entry["polarity"] = "direct"
    document["polarity_index"]["tractability"] = "direct"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    loaded = load_model_spec(root)
    assert loaded.facets["tractability"].polarity == "normal"


# ---------------------------------------------------------------------------
# The symmetric_caps sensitivity variant (contract §5.4, final paragraph)
# ---------------------------------------------------------------------------


def test_symmetric_mode_caps_both_fields(spec) -> None:
    """The counterfactual: caps applied to ``level`` and ``counter_level`` alike."""
    from blueprint.ranking.caps import cap_fields_for

    assert cap_fields_for("inverse", "polarity_aware") == ("counter_level",)
    assert cap_fields_for("normal", "polarity_aware") == ("level",)
    assert cap_fields_for("inverse", "symmetric") == ("level", "counter_level")
    assert cap_fields_for("normal", "symmetric") == ("level", "counter_level")


def test_an_unknown_cap_mode_is_rejected(spec) -> None:
    from blueprint.ranking.caps import cap_fields_for

    with pytest.raises(SpecError, match="unknown cap mode"):
        cap_fields_for("normal", "whatever")  # type: ignore[arg-type]


def test_symmetric_mode_flatters_the_target_and_that_is_the_point(spec) -> None:
    """Symmetric capping is the behaviour §5.4 forbids as policy.

    It is implemented anyway, as a measured counterfactual. The assertion here is that
    it does flatter the target — otherwise the sensitivity analysis would be measuring
    nothing.
    """
    facet_name = "human_lineage_divergence_risk"
    target = make_target(
        "TGT:DIVERGENT",
        levels={**GATE_FREE_LEVELS, facet_name: 4},
        counter_levels={facet_name: 4},
    )
    cap = MethodologicalCap(facet_name, PHYLOGENETIC_CAP_LEVEL, PHYLOGENETIC_REASON)

    policy, _ = apply_methodological_caps(spec, target, [cap], mode="polarity_aware")
    symmetric, records = apply_methodological_caps(spec, target, [cap], mode="symmetric")

    assert policy.facet(facet_name).level == 4
    assert symmetric.facet(facet_name).level == PHYLOGENETIC_CAP_LEVEL
    assert records[0].mode == "symmetric"
    assert set(records[0].fields_capped) == {"level", "counter_level"}
    # `field_capped` still reports what the POLICY would have done, in either mode.
    assert records[0].field_capped == "counter_level"
    assert expected_composite(spec, symmetric) > expected_composite(spec, policy)


def test_caps_are_derived_from_the_claims_method_not_declared(spec) -> None:
    """A cap is a statement about how a study was done, so it is read off the study.

    ``atlases/comparative/phylogenetic_controls.md`` §4: a facet resting only on claims
    with ``phylogenetic_control`` of ``none`` or ``not_reported`` is capped at level 2.
    """
    from blueprint.ranking.caps import derive_phylogenetic_caps
    from blueprint.ranking.inputs import ClaimRecord, RepositoryInputs

    target = make_target(
        "TGT:PROBE",
        levels={"cross_species_convergence": 4, "transfer_breadth": 4},
        claim_refs={
            "cross_species_convergence": ["CLM:c:001", "CLM:c:002"],
            "transfer_breadth": ["CLM:b:001"],
        },
    )
    inputs = RepositoryInputs(
        targets=(target,),
        claims={
            "CLM:c:001": ClaimRecord("CLM:c:001", ("SRC:PMID:1",), phylogenetic_control="none"),
            "CLM:c:002": ClaimRecord(
                "CLM:c:002", ("SRC:PMID:2",), phylogenetic_control="not_reported"
            ),
            # no phylogenetic_control field: a non-comparative claim, never capped
            "CLM:b:001": ClaimRecord("CLM:b:001", ("SRC:PMID:3",)),
        },
    )
    caps = derive_phylogenetic_caps(spec, target, inputs)
    assert [c.facet for c in caps] == ["cross_species_convergence"]
    assert caps[0].max_level == 2
    assert "phylogenetic_control" in caps[0].reason
    assert caps[0].imposed_by == "agent:comparative"


def test_one_properly_controlled_claim_lifts_the_cap(spec) -> None:
    """The grade may rest on the controlled claim, so the cap does not apply."""
    from blueprint.ranking.caps import derive_phylogenetic_caps
    from blueprint.ranking.inputs import ClaimRecord, RepositoryInputs

    target = make_target(
        "TGT:PROBE",
        levels={"cross_species_convergence": 4},
        claim_refs={"cross_species_convergence": ["CLM:c:001", "CLM:c:003"]},
    )
    inputs = RepositoryInputs(
        targets=(target,),
        claims={
            "CLM:c:001": ClaimRecord("CLM:c:001", ("SRC:PMID:1",), phylogenetic_control="none"),
            "CLM:c:003": ClaimRecord(
                "CLM:c:003", ("SRC:PMID:4",), phylogenetic_control="phylogenetic_regression"
            ),
        },
    )
    assert derive_phylogenetic_caps(spec, target, inputs) == ()


def test_not_reported_is_capped_alongside_none(spec) -> None:
    """Not knowing whether ancestry was modelled is not evidence that it was."""
    from blueprint.ranking.inputs import ClaimRecord

    assert ClaimRecord("CLM:x", phylogenetic_control="none").has_weak_phylogenetic_control
    assert ClaimRecord("CLM:x", phylogenetic_control="not_reported").has_weak_phylogenetic_control
    assert not ClaimRecord("CLM:x", phylogenetic_control="outgroup_comparison").has_weak_phylogenetic_control
    assert not ClaimRecord("CLM:x").has_weak_phylogenetic_control


def test_the_cap_sensitivity_run_measures_the_asymmetry(spec) -> None:
    """The contract's obligation: measured, not assumed.

    The fixture reproduces HCN1's shape — a normal-polarity facet whose
    ``counter_level`` exceeds the cap, and an inverse-polarity facet whose ``level``
    does — on claims with no phylogenetic control. Symmetric capping must move the
    target, and the run must report by how much.
    """
    from blueprint.ranking.inputs import ClaimRecord, RepositoryInputs
    from blueprint.ranking.score import cap_sensitivity

    hcn1_like = make_target(
        "TGT:HCN1_LIKE",
        levels={
            **GATE_FREE_LEVELS,
            "cross_species_convergence": 2,
            "human_lineage_divergence_risk": 3,
        },
        counter_levels={"cross_species_convergence": 3, "human_lineage_divergence_risk": 1},
        claim_refs={
            "cross_species_convergence": ["CLM:c:001"],
            "human_lineage_divergence_risk": ["CLM:c:002"],
        },
        counter_claim_refs={"cross_species_convergence": ["CLM:c:003"]},
    )
    rivals = [
        make_target(f"TGT:RIVAL{index}", levels={**GATE_FREE_LEVELS, "tractability": index % 4})
        for index in range(6)
    ]
    inputs = RepositoryInputs(
        targets=(hcn1_like, *rivals),
        claims={
            f"CLM:c:{n:03d}": ClaimRecord(
                f"CLM:c:{n:03d}", (f"SRC:PMID:{n}",), phylogenetic_control="none"
            )
            for n in (1, 2, 3)
        },
    )

    caps = cap_sensitivity(inputs, spec, n_draws=DRAWS)
    assert caps.n_caps_derived == 2
    assert "TGT:HCN1_LIKE" in caps.rank_delta
    # symmetric capping removes evidence against the target, so it ranks better:
    assert caps.rank_delta["TGT:HCN1_LIKE"] <= 0.0
    assert caps.threshold == float(spec.cap_variants["sensitivity_threshold"]["rank_positions"])
    assert caps.kendall_tau_b == caps.kendall_tau_b  # not nan
    assert any("symmetric" in key for key in caps.cap_applications)


def test_a_target_with_no_derived_cap_is_absent_from_rank_delta(spec) -> None:
    """Absent and zero are different: absent means no cap applied at all."""
    from blueprint.ranking.score import cap_sensitivity

    inputs = make_inputs(
        [
            make_target("TGT:A", levels={**GATE_FREE_LEVELS, "tractability": 2}),
            make_target("TGT:B", levels={**GATE_FREE_LEVELS, "tractability": 3}),
        ]
    )
    caps = cap_sensitivity(inputs, spec, n_draws=DRAWS)
    assert caps.rank_delta == {}
    assert caps.n_caps_derived == 0
    assert caps.sensitive_targets == ()


def test_the_csv_carries_the_rank_delta_column_and_leaves_it_blank_when_uncapped(spec) -> None:
    import csv
    import io

    from blueprint.ranking.inputs import ClaimRecord, RepositoryInputs
    from blueprint.ranking.report import CSV_COLUMNS, render_csv
    from blueprint.ranking.score import cap_sensitivity, score_cohort

    assert "rank_delta_symmetric_caps" in CSV_COLUMNS

    capped = make_target(
        "TGT:CAPPED",
        levels={**GATE_FREE_LEVELS, "cross_species_convergence": 2},
        counter_levels={"cross_species_convergence": 4},
        claim_refs={"cross_species_convergence": ["CLM:c:001"]},
    )
    uncapped = make_target("TGT:UNCAPPED", levels={**GATE_FREE_LEVELS, "tractability": 3})
    inputs = RepositoryInputs(
        targets=(capped, uncapped),
        claims={"CLM:c:001": ClaimRecord("CLM:c:001", ("SRC:PMID:1",), phylogenetic_control="none")},
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    caps = cap_sensitivity(inputs, spec, n_draws=DRAWS)
    rows = {
        row["target_id"]: row
        for row in csv.DictReader(
            io.StringIO(render_csv(result, generated_on="2026-09-17", caps=caps).decode("utf-8"))
        )
    }
    assert rows["TGT:CAPPED"]["rank_delta_symmetric_caps"] != ""
    assert rows["TGT:UNCAPPED"]["rank_delta_symmetric_caps"] == ""


def test_the_sidecar_states_the_asymmetry_and_reports_tau_b(spec, tmp_path) -> None:
    """Contract §5.4: the asymmetry must be stated wherever ranks are reported."""
    import json

    from blueprint.ranking.report import write_report
    from blueprint.ranking.score import cap_sensitivity, score_cohort

    inputs = make_inputs(
        [
            make_target("TGT:A", levels={**GATE_FREE_LEVELS, "tractability": 2}),
            make_target("TGT:B", levels={**GATE_FREE_LEVELS, "tractability": 3}),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    caps = cap_sensitivity(inputs, spec, n_draws=DRAWS)
    artefacts = write_report(
        result,
        inputs,
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
        caps=caps,
    )
    block = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))["cap_sensitivity"]
    assert block["measured"] is True
    assert "not neutral" in block["asymmetry_statement"]
    assert "under-ranks" in block["asymmetry_statement"]
    assert block["variants"] == [
        "polarity_aware (default, contract §5.4)",
        "symmetric_caps (counterfactual)",
    ]
    assert "kendall_tau_b" in block
    assert block["threshold_rank_positions"] == caps.threshold
    assert "negative" in block["rank_delta_sign_convention"].lower()


def test_the_spec_declares_both_variants_and_a_threshold(spec) -> None:
    ids = {entry["id"] for entry in spec.cap_variants["variants"]}
    assert ids == {"polarity_aware", "symmetric_caps"}
    assert float(spec.cap_variants["sensitivity_threshold"]["rank_positions"]) > 0
    text = Path(spec.paths["ranking"]).read_text(encoding="utf-8")
    assert "rank is sensitive to the precautionary capping rule" in text
    assert "HCN1" in text, "the spec must carry the HCN1 worked example"


def test_the_loader_requires_both_cap_variants(tmp_path, spec) -> None:
    root = tmp_path / "repo"
    relpaths = {
        "rubric": "models/ranking/facet_rubric_v0_1.yaml",
        "ranking": "models/ranking/ranking_spec_v0_1.yaml",
        "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
    }
    for name, relpath in relpaths.items():
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spec.paths[name], destination)

    path = root / relpaths["ranking"]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["cap_variants"]["variants"] = [
        v for v in document["cap_variants"]["variants"] if v["id"] != "symmetric_caps"
    ]
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    with pytest.raises(SpecError, match="symmetric_caps"):
        load_model_spec(root)
