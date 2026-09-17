"""The rubric, the ranking spec and the contract must agree.

The model has no numeric constants of its own: everything comes from three YAML
files. That makes the loader's cross-checks the only thing standing between an
editing slip and a report full of numbers nobody defined. These tests exercise those
checks, including the failure paths, and pin the facet catalogue against
``docs/DATA_CONTRACT.md`` §5 so a drift between contract and model is a build failure
rather than a discrepancy someone notices later.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from blueprint.ranking.rubric import (
    DIMENSION_IDS,
    HUMAN_PROPOSITION_FACETS,
    LEVELS,
    SpecError,
    load_model_spec,
)
from blueprint.ranking.synthetic import ALL_FACETS, NORMAL_FACETS, INVERSE_FACETS

RELPATHS = {
    "rubric": "models/ranking/facet_rubric_v0_1.yaml",
    "ranking": "models/ranking/ranking_spec_v0_1.yaml",
    "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
}

#: The contract's facet catalogue (docs/DATA_CONTRACT.md §5), transcribed as
#: {facet: (owner-ish, dimensions)}. Transcribed rather than parsed so that a change
#: to either document has to be made deliberately in both places.
#:
#: Two edges are approved by R8 (docs/blackboard/RESOLUTIONS.md) and marked below:
#: `dose_response_knowledge -> D3` and `tractability -> D5`. They are recorded here so
#: the model's edge set stays pinned to an authority rather than drifting freely.
CONTRACT_FACET_TABLE = {
    "human_genetic_association": ("alphacognition", {"D1"}),
    "causal_gene_attribution": ("alphacognition", {"D1"}),
    "human_phenotype_specificity": ("alphacognition", {"D1", "D4"}),
    "adult_expression_and_timing": ("alphacognition", {"D2"}),
    "mechanistic_causal_perturbation": ("lead_atlas", {"D1"}),
    "adult_onset_perturbation": ("lead_atlas", {"D2"}),
    "above_baseline_enhancement": ("lead_atlas", {"D3"}),
    "transfer_breadth": ("lead_atlas", {"D4"}),
    "dose_response_knowledge": ("lead_atlas", {"D3", "D5"}),      # D3 added by R8
    "human_intervention_evidence": ("lead_atlas", {"D6"}),
    "cross_species_convergence": ("comparative", {"D6"}),
    "human_lineage_divergence_risk": ("comparative", {"D6"}),
    "safety_liability_burden": ("red_team", {"D5"}),
    "developmental_confound_risk": ("red_team", {"D2"}),
    "tractability": ("integration", {"D5", "D6"}),                # D5 added by R8
}


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


@pytest.fixture
def spec_copy(tmp_path, spec) -> Path:
    """A writable copy of the three spec files, for failure-path tests."""
    root = tmp_path / "repo"
    for name, relpath in RELPATHS.items():
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(spec.paths[name], destination)
    return root


def _edit(root: Path, name: str, mutate) -> None:
    path = root / RELPATHS[name]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Agreement with the contract
# ---------------------------------------------------------------------------


def test_the_facet_catalogue_matches_the_contract(spec) -> None:
    assert set(spec.facets) == set(CONTRACT_FACET_TABLE)
    assert len(spec.facets) == 15


def test_every_facet_feeds_exactly_the_contract_dimensions(spec) -> None:
    for facet_name, (_, dimensions) in CONTRACT_FACET_TABLE.items():
        assert set(spec.facets[facet_name].feeds) == dimensions, facet_name
        assert set(spec.facets[facet_name].weights) == dimensions, facet_name


def test_the_spec_adds_no_off_table_facet_dimension_edges(spec) -> None:
    """The facet -> dimension edge set is fixed by the contract; only the weights are
    the model's choice. An extra edge here would be a schema change smuggled into a
    weights file."""
    declared = {
        (facet, dimension)
        for facet, (_, dimensions) in CONTRACT_FACET_TABLE.items()
        for dimension in dimensions
    }
    actual = {
        (facet, dimension)
        for facet, facet_spec in spec.facets.items()
        for dimension in facet_spec.weights
    }
    assert actual == declared


def test_the_human_proposition_facet_set_is_the_contract_set(spec) -> None:
    """Contract §5.3 fixes which facets require human evidence for level >= 3."""
    assert HUMAN_PROPOSITION_FACETS == {
        "human_genetic_association",
        "human_phenotype_specificity",
        "human_intervention_evidence",
        "adult_expression_and_timing",
    }
    for facet_name, facet_spec in spec.facets.items():
        assert facet_spec.human_proposition == (facet_name in HUMAN_PROPOSITION_FACETS), facet_name


def test_the_inverse_facet_set_matches_the_fixture_constants(spec) -> None:
    """``blueprint.ranking.synthetic`` hardcodes the inverse set for test readability;
    it must not drift from the rubric."""
    loaded = {name for name, facet in spec.facets.items() if facet.is_inverse}
    assert loaded == set(INVERSE_FACETS)
    assert set(NORMAL_FACETS) == set(ALL_FACETS) - loaded


def test_every_facet_has_criteria_for_all_five_levels(spec) -> None:
    for facet_name, facet_spec in spec.facets.items():
        assert set(facet_spec.level_criteria) == set(LEVELS), facet_name
        for level, text in facet_spec.level_criteria.items():
            assert len(text) > 40, f"{facet_name} level {level} criterion is too thin to grade against"


def test_every_facet_states_a_proposition_and_counter_guidance(spec) -> None:
    for facet_name, facet_spec in spec.facets.items():
        assert facet_spec.proposition, facet_name
        assert facet_spec.counter_level_guidance, facet_name


def test_level_semantics_are_unchanged_from_the_contract(spec) -> None:
    """The rubric refines per-facet criteria but must not redefine the scale."""
    levels = {int(entry["level"]): entry["meaning"] for entry in spec.raw["rubric"]["levels"]}
    assert levels[0].startswith("searched, nothing found")
    assert levels[1].startswith("weak or indirect only")
    assert levels[2].startswith("moderate")
    assert levels[3].startswith("substantial")
    assert levels[4].startswith("strong")
    assert spec.versions["scale"] == "evidence_strength_v1"


# ---------------------------------------------------------------------------
# Internal consistency
# ---------------------------------------------------------------------------


def test_facet_weights_sum_to_one_within_each_dimension(spec) -> None:
    for dimension in DIMENSION_IDS:
        total = sum(f.weights[dimension] for f in spec.facets_for(dimension))
        assert total == pytest.approx(1.0), dimension


def test_dimension_weights_sum_to_one(spec) -> None:
    assert sum(spec.dimension_weights.values()) == pytest.approx(1.0)


def test_every_dimension_has_at_least_one_facet(spec) -> None:
    for dimension in DIMENSION_IDS:
        assert spec.facets_for(dimension), dimension


def test_no_dimension_has_a_single_input(spec) -> None:
    """R8 resolved D3's single-input defect; nothing may reintroduce one.

    A one-facet dimension is not an aggregate — it is a relabelling of one grader's
    ordinal judgement carrying a composite weight, with no internal cross-check and no
    way for two lines of evidence to disagree.
    """
    for dimension in DIMENSION_IDS:
        assert len(spec.facets_for(dimension)) >= 2, (
            f"{dimension} has a single input facet; see R8 in docs/blackboard/RESOLUTIONS.md"
        )


def test_the_d3_resolution_and_its_deferred_limitation_are_recorded(spec) -> None:
    """The fix is recorded, and so is what was deferred rather than solved."""
    text = Path(spec.paths["ranking"]).read_text(encoding="utf-8")
    assert "R8" in text
    assert "dose_response_knowledge" in text
    assert "healthy_baseline_arm_quality" in text, "the deferred alternative must stay recorded"
    assert "ROADMAP.md" in text
    assert {f.facet for f in spec.facets_for("D3")} == {
        "above_baseline_enhancement",
        "dose_response_knowledge",
    }
    weights = {f.facet: f.weights["D3"] for f in spec.facets_for("D3")}
    assert weights["above_baseline_enhancement"] > weights["dose_response_knowledge"], (
        "the facet that measures the proposition directly must outweigh the precondition"
    )


def test_tractability_is_the_only_database_gradable_facet(spec) -> None:
    """R7 / contract §5.2: `source_refs`-only grading stays narrow, and the flag is
    published in the rubric for agent:ontology's schema generator to read."""
    assert spec.database_gradable_facets == ("tractability",)
    assert spec.facets["tractability"].database_gradable is True


def test_every_numeric_parameter_is_labelled_subjective(spec) -> None:
    """Hard rule: no weight may appear without being labelled a subjective choice.

    The only permitted alternative label is ``structural``, for a parameter that is
    forced by the model's shape rather than chosen (a ``not_applicable`` multiplier
    of zero is not an opinion). Tier thresholds are exempted here because they are
    labelled subjective in the block comment above them rather than inline.
    """
    text = Path(spec.paths["ranking"]).read_text(encoding="utf-8")
    assert "SUBJECTIVE, UNCALIBRATED MODELLING" in text
    for line in text.splitlines():
        match = re.match(r"^\s{4,}([a-z_0-9]+):\s*(0\.\d+|1\.00)\s*(#.*)?$", line)
        if match and match.group(1) not in {"min_coverage", "top_fraction", "mid_fraction"}:
            comment = match.group(3)
            assert comment, f"unlabelled numeric parameter: {line.strip()}"
            assert any(
                token in comment.lower() for token in ("subjective", "structural")
            ), f"not labelled subjective or structural: {line.strip()}"


def test_specs_declare_their_calibration_status(spec) -> None:
    assert spec.versions["calibration_status"] == "uncalibrated_subjective"
    for name in ("rubric", "uncertainty"):
        document = yaml.safe_load(Path(spec.paths[name]).read_text(encoding="utf-8"))
        assert document["calibration_status"] == "uncalibrated_subjective"


def test_spec_files_are_hashed_for_provenance(spec) -> None:
    assert set(spec.sha256) == {"rubric", "ranking", "uncertainty"}
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in spec.sha256.values())


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------


def test_a_facet_in_the_spec_but_not_the_rubric_is_an_error(spec_copy) -> None:
    """The headline requirement from the deliverable: a weighted facet with no level
    criteria would produce a number nobody defined."""
    _edit(spec_copy, "rubric", lambda d: d["facets"].pop(0))
    with pytest.raises(SpecError, match="absent from facet_rubric"):
        load_model_spec(spec_copy)


def test_a_facet_in_the_rubric_but_not_the_spec_is_an_error(spec_copy) -> None:
    def mutate(document):
        for dimension in ("D5", "D6"):
            document["facet_weights"][dimension].pop("tractability", None)

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="never weighted in ranking_spec"):
        load_model_spec(spec_copy)


def test_a_partial_feeds_mismatch_is_an_error(spec_copy) -> None:
    """Dropping one of a facet's two dimensions must fail, not silently narrow it."""

    def mutate(document):
        document["facet_weights"]["D6"].pop("tractability")

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="disagrees with the dimensions"):
        load_model_spec(spec_copy)


def test_a_feeds_mismatch_is_an_error(spec_copy) -> None:
    def mutate(document):
        for entry in document["facets"]:
            if entry["facet"] == "tractability":
                entry["feeds"] = ["D5"]

    _edit(spec_copy, "rubric", mutate)
    with pytest.raises(SpecError, match="disagrees with the dimensions"):
        load_model_spec(spec_copy)


def test_a_polarity_typo_is_an_error(spec_copy) -> None:
    def mutate(document):
        for entry in document["facets"]:
            if entry["facet"] == "safety_liability_burden":
                entry["polarity"] = "reversed"

    _edit(spec_copy, "rubric", mutate)
    with pytest.raises(SpecError, match="polarity must be"):
        load_model_spec(spec_copy)


def test_contradicting_the_contracts_human_proposition_set_is_an_error(spec_copy) -> None:
    def mutate(document):
        for entry in document["facets"]:
            if entry["facet"] == "tractability":
                entry["human_proposition"] = True

    _edit(spec_copy, "rubric", mutate)
    with pytest.raises(SpecError, match="contradicts contract"):
        load_model_spec(spec_copy)


def test_a_missing_level_criterion_is_an_error(spec_copy) -> None:
    def mutate(document):
        for entry in document["facets"]:
            if entry["facet"] == "tractability":
                entry["level_criteria"].pop(4)

    _edit(spec_copy, "rubric", mutate)
    with pytest.raises(SpecError, match="level_criteria missing levels"):
        load_model_spec(spec_copy)


def test_a_zero_weight_is_rejected(spec_copy) -> None:
    """A zero weight would hide a facet -> dimension edge that the contract declares.
    Removing the facet is the honest way to express "this does not feed here"."""

    def mutate(document):
        document["facet_weights"]["D6"]["tractability"] = 0.0

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="weights must be positive"):
        load_model_spec(spec_copy)


def test_an_unreachable_gate_condition_key_is_rejected(spec_copy) -> None:
    """A mistyped condition key would silently produce a gate that never fires."""

    def mutate(document):
        document["gates"][0]["condition"] = {"levl_at_least": 4}

    _edit(spec_copy, "ranking", mutate)
    loaded = load_model_spec(spec_copy)
    from blueprint.ranking.score import expected_dimensions
    from blueprint.ranking.synthetic import make_target

    with pytest.raises(SpecError, match="unrecognised condition keys"):
        expected_dimensions(loaded, make_target("TGT:PROBE", levels={"tractability": 2}))


def test_an_out_of_range_cap_is_rejected(spec_copy) -> None:
    def mutate(document):
        document["gates"][0]["cap"] = 1.5

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match=r"cap must be in \[0, 1\]"):
        load_model_spec(spec_copy)


def test_removing_all_gates_is_rejected(spec_copy) -> None:
    _edit(spec_copy, "ranking", lambda d: d.__setitem__("gates", []))
    with pytest.raises(SpecError, match="declares no gates"):
        load_model_spec(spec_copy)


def test_removing_the_sensitivity_alternatives_is_rejected(spec_copy) -> None:
    """Sensitivity analysis is mandatory: without it there is no way to tell whether
    the ranking is a property of the aggregation choice."""

    def mutate(document):
        document["composite"]["variants_for_sensitivity"] = []

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="sensitivity analysis is mandatory"):
        load_model_spec(spec_copy)


def test_the_primary_composite_is_conjunctive(spec) -> None:
    """The six dimensions are conditions that must ALL hold, so the composite is their
    product under an explicit independence assumption — not a weighted mean, which
    would let five favourable conditions compensate for one that fails."""
    assert spec.primary_aggregation == "product"
    assert set(spec.alternative_aggregations) == {"minimum", "weighted_additive"}
    text = Path(spec.paths["ranking"]).read_text(encoding="utf-8")
    assert "MUST ALL HOLD" in text
    assert "joint_probability_under_independence" in text
    assert "truth_value: false" in text, "the independence assumption must be declared false"
    assert "TOO NARROW" in text, "the interval consequence must be stated"


def test_geometric_mean_is_not_carried_as_a_variant(spec) -> None:
    """It is a strictly monotone transform of the product, so comparing them is a
    tautology that overstates how many operators the ordering was tested against."""
    assert "geometric_mean" not in spec.alternative_aggregations
    assert "geometric_mean" != spec.primary_aggregation


def test_the_loader_refuses_product_and_geometric_mean_together(spec_copy) -> None:
    def mutate(document):
        document["composite"]["variants_for_sensitivity"].append(
            {"id": "geometric_mean", "formula": "x"}
        )

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="tautology"):
        load_model_spec(spec_copy)


def test_the_loader_refuses_the_primary_as_its_own_variant(spec_copy) -> None:
    def mutate(document):
        document["composite"]["variants_for_sensitivity"].append({"id": "product"})

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="both the primary and a sensitivity variant"):
        load_model_spec(spec_copy)


def test_the_loader_refuses_a_dimension_equivalent_cap_on_a_dimension_gate(spec_copy) -> None:
    """Dimensions all live on [0, 1] whatever the composite operator is, so the
    indirection is meaningless there and would hide a mistake."""

    def mutate(document):
        document["gates"][0]["cap_scale"] = "dimension_equivalent"

    _edit(spec_copy, "ranking", mutate)
    with pytest.raises(SpecError, match="only a COMPOSITE gate"):
        load_model_spec(spec_copy)


def test_a_missing_spec_file_is_reported_clearly(tmp_path) -> None:
    with pytest.raises(SpecError, match="specification file missing"):
        load_model_spec(tmp_path)


def test_a_negative_seed_is_rejected(spec_copy) -> None:
    def mutate(document):
        document["monte_carlo"]["seed"] = -1

    _edit(spec_copy, "uncertainty", mutate)
    with pytest.raises(SpecError, match="determinism requirement"):
        load_model_spec(spec_copy)


def test_a_declared_facet_count_mismatch_is_rejected(spec_copy) -> None:
    _edit(spec_copy, "rubric", lambda d: d.__setitem__("facet_count", 14))
    with pytest.raises(SpecError, match="facet_count says 14"):
        load_model_spec(spec_copy)
