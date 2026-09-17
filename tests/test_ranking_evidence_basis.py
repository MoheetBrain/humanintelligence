"""Database-graded facets (R7) and evidence gaps — contract §5.2 and §4.1 as amended.

Two amendments land here. A facet flagged ``database_gradable`` may rest on
``source_refs`` instead of ``claim_refs``; and ``claim_type: evidence_gap`` — "the study
never measured this endpoint" — may never contribute to a ``counter_level``, because the
question was not asked. Both are ways of keeping "nobody looked" distinct from "it was
tested and failed", which is the distinction the whole evidence layer is built on.
"""

from __future__ import annotations

import json

import pytest

from blueprint.ranking.inputs import (
    NON_COUNTING_CLAIM_TYPES,
    ClaimRecord,
    FacetAssessment,
    RepositoryInputs,
)
from blueprint.ranking.report import write_report
from blueprint.ranking.rubric import DIMENSION_IDS, load_model_spec
from blueprint.ranking.score import evidence_state_counts, score_cohort
from blueprint.ranking.synthetic import GATE_FREE_LEVELS, facet, make_inputs, make_target

DRAWS = 2000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


# ---------------------------------------------------------------------------
# R7 — database-graded facets
# ---------------------------------------------------------------------------


def test_only_tractability_may_be_graded_from_a_database_release(spec) -> None:
    """The permission is narrow on purpose: a database annotation cannot carry the
    provenance a claim reference does."""
    assert spec.database_gradable_facets == ("tractability",)


def test_a_source_graded_facet_scores_like_any_other(spec) -> None:
    """``source_refs`` is a provenance route, not a discount. A level-3 tractability
    grade must weigh the same whether its evidence is a paper or a pinned release."""
    from dataclasses import replace

    claim_graded = make_target("TGT:CLAIMS", levels={**GATE_FREE_LEVELS, "tractability": 3})
    source_graded = make_target("TGT:SOURCES", levels={**GATE_FREE_LEVELS, "tractability": 3})
    facets = dict(source_graded.facets)
    facets["tractability"] = FacetAssessment(
        facet="tractability",
        assessment_status="assessed",
        level=3,
        counter_level=0,
        source_refs=("SRC:DB:opentargets:26.06",),
        evidence_basis="database_release",
    )
    source_graded = replace(source_graded, facets=facets)

    result = score_cohort(make_inputs([claim_graded, source_graded]), spec, n_draws=DRAWS)
    rows = {t.target_id: t for t in result.targets}
    assert rows["TGT:CLAIMS"].dimensions["D6"].median == pytest.approx(
        rows["TGT:SOURCES"].dimensions["D6"].median, abs=0.02
    )


def test_a_source_graded_facet_contributes_no_independent_sources_via_claims(spec) -> None:
    """``independent_source_count`` counts sources reached THROUGH CLAIMS, so a
    database-graded facet does not inflate it. The database release is registered as a
    source in its own right and is visible in the assessment record, which is where a
    reader should look for it."""
    from dataclasses import replace

    target = make_target("TGT:PROBE", levels={"tractability": 3})
    facets = dict(target.facets)
    facets["tractability"] = FacetAssessment(
        facet="tractability",
        assessment_status="assessed",
        level=3,
        source_refs=("SRC:DB:opentargets:26.06",),
        evidence_basis="database_release",
    )
    target = replace(target, facets=facets)
    inputs = make_inputs([target])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    assert result.targets[0].independent_source_count == 0
    assert result.targets[0].claim_count == 0
    # but the facet IS assessed, so it counts towards coverage
    assert result.targets[0].facets_assessed == 1


def test_the_repository_tractability_assessments_are_database_graded(spec) -> None:
    """The real records this agent wrote: ``source_refs``, no ``claim_refs``, and the
    data version named in the rationale (contract §5.2 requires the field values)."""
    from blueprint.ranking.inputs import from_repository

    inputs = from_repository(".")
    graded = [
        t for t in inputs.targets if t.facet("tractability").assessment_status == "assessed"
    ]
    assert graded, "no tractability assessments found in the repository"
    for target in graded:
        assessment = target.facet("tractability")
        assert assessment.evidence_basis == "database_release", target.target_id
        assert assessment.source_refs, target.target_id
        assert not assessment.claim_refs, target.target_id
        assert "data version" in (assessment.rationale or ""), target.target_id
        assert "SRC:DB:opentargets" in assessment.source_refs[0], target.target_id


# ---------------------------------------------------------------------------
# evidence_gap
# ---------------------------------------------------------------------------


def test_evidence_gap_is_recognised_as_a_non_counting_claim_type() -> None:
    assert NON_COUNTING_CLAIM_TYPES == frozenset({"evidence_gap"})
    assert ClaimRecord("CLM:x", claim_type="evidence_gap").is_evidence_gap
    assert not ClaimRecord("CLM:x", claim_type="clinical_null").is_evidence_gap
    assert not ClaimRecord("CLM:x").is_evidence_gap


def test_an_evidence_gap_only_counter_level_is_dropped(spec) -> None:
    """"The trial never measured this endpoint" is not evidence against anything.

    Counting it would turn a gap in the literature into a penalty, which inverts what a
    gap means.
    """
    target = make_target(
        "TGT:GAPPED",
        levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 2},
        counter_levels={"human_intervention_evidence": 4},
        counter_claim_refs={"human_intervention_evidence": ["CLM:b:gap"]},
    )
    inputs = RepositoryInputs(
        targets=(target,),
        claims={"CLM:b:gap": ClaimRecord("CLM:b:gap", ("SRC:NCT:NCT1",), claim_type="evidence_gap")},
    )
    neutralised, report = inputs.with_evidence_gaps_neutralised()
    assert report == {"TGT:GAPPED": ("human_intervention_evidence",)}
    assert neutralised.targets[0].facet("human_intervention_evidence").counter_level is None
    # and the level is untouched: a gap says nothing about the supporting evidence
    assert neutralised.targets[0].facet("human_intervention_evidence").level == 2


def test_dropping_an_evidence_gap_counter_level_raises_the_dimension(spec) -> None:
    """The effect must be real, or the amendment would be decorative."""
    with_gap = make_target(
        "TGT:GAPPED",
        levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 2},
        counter_levels={"human_intervention_evidence": 4},
        counter_claim_refs={"human_intervention_evidence": ["CLM:b:gap"]},
    )
    inputs = RepositoryInputs(
        targets=(with_gap,),
        claims={"CLM:b:gap": ClaimRecord("CLM:b:gap", ("SRC:NCT:NCT1",), claim_type="evidence_gap")},
    )
    scored = score_cohort(inputs, spec, n_draws=DRAWS)
    assert scored.evidence_gap_facets == {"TGT:GAPPED": ("human_intervention_evidence",)}

    # Same record with a real tested null instead of a gap: the counter_level stands.
    real_null = RepositoryInputs(
        targets=(with_gap,),
        claims={"CLM:b:gap": ClaimRecord("CLM:b:gap", ("SRC:NCT:NCT1",), claim_type="clinical_null")},
    )
    scored_null = score_cohort(real_null, spec, n_draws=DRAWS)
    assert scored_null.evidence_gap_facets == {}
    assert (
        scored.targets[0].dimensions["D6"].median > scored_null.targets[0].dimensions["D6"].median
    )


def test_one_real_counter_claim_keeps_the_counter_level(spec) -> None:
    """A facet keeps its grade whenever at least one counter-claim is a real result:
    the grade may rest on that one."""
    target = make_target(
        "TGT:MIXED",
        levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 2},
        counter_levels={"human_intervention_evidence": 3},
        counter_claim_refs={"human_intervention_evidence": ["CLM:gap", "CLM:null"]},
    )
    inputs = RepositoryInputs(
        targets=(target,),
        claims={
            "CLM:gap": ClaimRecord("CLM:gap", claim_type="evidence_gap"),
            "CLM:null": ClaimRecord("CLM:null", claim_type="clinical_null"),
        },
    )
    _, report = inputs.with_evidence_gaps_neutralised()
    assert report == {}


def test_a_neutralised_facet_is_reported_not_silently_removed(spec, tmp_path) -> None:
    target = make_target(
        "TGT:GAPPED",
        levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 2},
        counter_levels={"human_intervention_evidence": 4},
        counter_claim_refs={"human_intervention_evidence": ["CLM:b:gap"]},
    )
    inputs = RepositoryInputs(
        targets=(target, make_target("TGT:OTHER", levels={**GATE_FREE_LEVELS})),
        claims={"CLM:b:gap": ClaimRecord("CLM:b:gap", claim_type="evidence_gap")},
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    artefacts = write_report(
        result,
        inputs,
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
    )
    meta = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))
    assert meta["evidence_gap_facets"] == {"TGT:GAPPED": ["human_intervention_evidence"]}


def test_a_gap_does_not_count_as_contradicted_in_the_coverage_state(spec) -> None:
    """``facets_contradicted`` must not include a facet whose only counter-evidence is
    a gap — it belongs to the coverage story, not the contradiction story."""
    target = make_target(
        "TGT:GAPPED",
        levels={**GATE_FREE_LEVELS, "human_intervention_evidence": 2},
        counter_levels={"human_intervention_evidence": 4},
        counter_claim_refs={"human_intervention_evidence": ["CLM:b:gap"]},
    )
    inputs = RepositoryInputs(
        targets=(target,),
        claims={"CLM:b:gap": ClaimRecord("CLM:b:gap", claim_type="evidence_gap")},
    )
    before = evidence_state_counts(spec, target)
    neutralised, _ = inputs.with_evidence_gaps_neutralised()
    after = evidence_state_counts(spec, neutralised.targets[0])
    assert before["contradicted"] == 1
    assert after["contradicted"] == 0
    assert after["assessed"] == before["assessed"]


# ---------------------------------------------------------------------------
# R8 — per-dimension input counts
# ---------------------------------------------------------------------------


def test_the_sidecar_publishes_the_input_count_per_dimension(spec, tmp_path) -> None:
    """R8: a single-input dimension must never again be invisible in the report."""
    inputs = make_inputs([make_target("TGT:A", levels={**GATE_FREE_LEVELS})])
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    artefacts = write_report(
        result,
        inputs,
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
    )
    block = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))["dimension_inputs"]
    assert set(block) == set(DIMENSION_IDS)
    for dimension, entry in block.items():
        assert entry["n_input_facets"] == len(spec.facets_for(dimension))
        assert entry["n_input_facets"] >= 2, dimension
        assert entry["single_input_warning"] is None
        assert entry["composite_weight"] == spec.dimension_weights[dimension]
        assert set(entry["facets"]) == {f.facet for f in spec.facets_for(dimension)}


def test_d3_is_now_a_genuine_aggregate(spec) -> None:
    """R8's substance: two independent lines can now disagree inside D3."""
    strong_enhancement_no_shape = make_target(
        "TGT:NO_SHAPE",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 4, "dose_response_knowledge": 0},
    )
    moderate_both = make_target(
        "TGT:BOTH",
        levels={**GATE_FREE_LEVELS, "above_baseline_enhancement": 3, "dose_response_knowledge": 3},
    )
    result = score_cohort(
        make_inputs([strong_enhancement_no_shape, moderate_both]), spec, n_draws=DRAWS
    )
    rows = {t.target_id: t for t in result.targets}
    # Under the old single-facet D3, level 4 would have beaten level 3 unconditionally.
    assert rows["TGT:BOTH"].dimensions["D3"].median > rows["TGT:NO_SHAPE"].dimensions["D3"].median
    assert rows["TGT:NO_SHAPE"].dimensions["D3"].n_assessed == 2


def test_tractability_now_bounds_the_controllable_window(spec) -> None:
    """R8: a target with no characterised modality has a narrower D5 by construction."""
    untractable = make_target(
        "TGT:UNTRACTABLE",
        levels={**GATE_FREE_LEVELS, "dose_response_knowledge": 3, "tractability": 0},
    )
    tractable = make_target(
        "TGT:TRACTABLE",
        levels={**GATE_FREE_LEVELS, "dose_response_knowledge": 3, "tractability": 3},
    )
    result = score_cohort(make_inputs([untractable, tractable]), spec, n_draws=DRAWS)
    rows = {t.target_id: t for t in result.targets}
    assert rows["TGT:TRACTABLE"].dimensions["D5"].median > rows["TGT:UNTRACTABLE"].dimensions["D5"].median
