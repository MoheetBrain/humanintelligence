"""Builders for synthetic ranking inputs, used by the model's own test suite.

The mathematics in this package is tested against inputs constructed here rather
than against repository records, for two reasons. First, the properties being
tested — duplicated-evidence invariance, monotonicity, gate behaviour,
``not_assessed`` handling, determinism — are properties of the *model*, and must hold
before any real data exists and regardless of what the atlases eventually curate.
Second, the schemas and loaders are owned by another agent and are landing in
parallel; a model test that depended on them would be testing the wrong thing.

Nothing here is data. Every target built by this module is a fixture with an obvious
fake identifier, and no function in this module reads or writes the repository.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from blueprint.ranking.inputs import (
    AuditAdjustment,
    AuditSummary,
    ClaimRecord,
    FacetAssessment,
    RepositoryInputs,
    TargetInput,
)

__all__ = [
    "ALL_FACETS",
    "GATE_FREE_LEVELS",
    "INVERSE_FACETS",
    "NORMAL_FACETS",
    "claim",
    "facet",
    "make_inputs",
    "make_target",
    "normal_uniform_target",
    "uniform_target",
]

#: The 15 facets of the v0.1 catalogue (contract §5). Duplicated here deliberately:
#: if the rubric and this list ever disagree, a test should fail rather than adapt.
ALL_FACETS: tuple[str, ...] = (
    "adult_expression_and_timing",
    "adult_onset_perturbation",
    "above_baseline_enhancement",
    "causal_gene_attribution",
    "cross_species_convergence",
    "developmental_confound_risk",
    "dose_response_knowledge",
    "human_genetic_association",
    "human_intervention_evidence",
    "human_lineage_divergence_risk",
    "human_phenotype_specificity",
    "mechanistic_causal_perturbation",
    "safety_liability_burden",
    "tractability",
    "transfer_breadth",
)

#: The three inverse-polarity facets (contract §5.4): their
#: proposition is a RISK or a DISTANCE, so a HIGHER level is WORSE for the target.
#: Duplicated from the contract on purpose — ``test_ranking_spec_consistency.py``
#: asserts this set equals the loaded rubric's, so a silent drift fails the build.
INVERSE_FACETS: tuple[str, ...] = (
    "developmental_confound_risk",
    "human_lineage_divergence_risk",
    "safety_liability_burden",
)

#: The twelve normal-polarity facets (contract §5.4): a higher level is better for
#: the target. "normal" is the contract's word; the codebase does not say "direct".
NORMAL_FACETS: tuple[str, ...] = tuple(f for f in ALL_FACETS if f not in INVERSE_FACETS)

#: A facet configuration under which no gate in ranking_spec_v0_1 binds, so that a
#: test can isolate the weighting arithmetic from the caps. Human-proposition
#: evidence is present (releases both D6 gates), and both risk facets are graded at
#: level 0, i.e. "searched, nothing found" (releases the D2 and D5 gates).
GATE_FREE_LEVELS: Mapping[str, int] = {
    "human_genetic_association": 3,
    "human_phenotype_specificity": 3,
    "human_intervention_evidence": 2,
    "adult_expression_and_timing": 3,
    "developmental_confound_risk": 0,
    "safety_liability_burden": 0,
}


def facet(
    name: str,
    level: int | None = None,
    *,
    counter_level: int | None = None,
    status: str | None = None,
    claim_refs: Sequence[str] = (),
    counter_claim_refs: Sequence[str] = (),
) -> FacetAssessment:
    """One synthetic facet assessment.

    Args:
        name: Facet name.
        level: Supporting level; ``None`` means the facet was not assessed.
        counter_level: Contradicting level.
        status: Override the status. Defaults to ``assessed`` when ``level`` is given
            and ``not_assessed`` otherwise; pass ``"not_applicable"`` explicitly.
        claim_refs: Supporting claim ids.
        counter_claim_refs: Contradicting claim ids.
    """
    if status is None:
        status = "assessed" if level is not None else "not_assessed"
    return FacetAssessment(
        facet=name,
        assessment_status=status,  # type: ignore[arg-type]
        level=level,
        counter_level=counter_level,
        claim_refs=tuple(claim_refs),
        counter_claim_refs=tuple(counter_claim_refs),
        assessed_by="agent:test_fixture",
        rationale="synthetic fixture; not evidence",
    )


def make_target(
    target_id: str,
    *,
    symbol: str | None = None,
    levels: Mapping[str, int | None] | None = None,
    counter_levels: Mapping[str, int] | None = None,
    not_applicable: Iterable[str] = (),
    claim_refs: Mapping[str, Sequence[str]] | None = None,
    counter_claim_refs: Mapping[str, Sequence[str]] | None = None,
    verdict: str | None = "retain",
    audit_ids: Sequence[str] = ("AUD:test:001",),
    adjustments: Sequence[AuditAdjustment] = (),
    unresolved_critical_findings: int = 0,
    lead_atlas: str = "brakes",
    dossier_depth: str = "deep",
) -> TargetInput:
    """A synthetic target.

    Facets named in ``levels`` are assessed at that level (``None`` leaves them
    ``not_assessed``); facets in ``not_applicable`` are marked as such; every other
    facet of the catalogue is left ``not_assessed``, which is what the contract says
    an unexamined facet is.
    """
    levels = dict(levels or {})
    counter_levels = dict(counter_levels or {})
    claim_refs = dict(claim_refs or {})
    counter_claim_refs = dict(counter_claim_refs or {})
    not_applicable_set = set(not_applicable)

    facets: dict[str, FacetAssessment] = {}
    for name in ALL_FACETS:
        if name in not_applicable_set:
            facets[name] = facet(name, None, status="not_applicable")
            continue
        facets[name] = facet(
            name,
            levels.get(name),
            counter_level=counter_levels.get(name),
            claim_refs=claim_refs.get(name, ()),
            counter_claim_refs=counter_claim_refs.get(name, ()),
        )

    return TargetInput(
        target_id=target_id,
        symbol=symbol or target_id.removeprefix("TGT:"),
        lead_atlas=lead_atlas,
        dossier_depth=dossier_depth,
        facets=facets,
        audit=AuditSummary(
            verdict=verdict,
            audit_ids=tuple(audit_ids) if verdict is not None else (),
            adjustments=tuple(adjustments),
            unresolved_critical_findings=unresolved_critical_findings,
        ),
    )


def uniform_target(target_id: str, level: int | None, **kwargs) -> TargetInput:
    """A target with **every** catalogue facet at the same level, inverse ones included.

    Note what this means: ``uniform_target(..., 4)`` is not "the best possible
    target". It is a target with strong evidence of *everything*, including strong
    evidence of a safety liability and of a developmental confound, so its D2 and D5
    gates bind. That is correct model behaviour and is asserted directly in
    ``test_ranking_gates.py``; use :func:`normal_uniform_target` when you want a
    monotone evidence-strength ladder.
    """
    kwargs.setdefault("levels", dict.fromkeys(ALL_FACETS, level))
    return make_target(target_id, **kwargs)


def normal_uniform_target(
    target_id: str,
    level: int | None,
    *,
    inverse_level: int | None = 0,
    **kwargs,
) -> TargetInput:
    """Normal-polarity facets at ``level``; inverse (risk) facets at ``inverse_level``.

    This is the fixture that makes "more evidence ranks higher" a coherent statement:
    it varies the twelve facets whose propositions are about the target working, and
    holds the three risk facets fixed so their opposite polarity does not confound
    the comparison.
    """
    levels: dict[str, int | None] = dict.fromkeys(NORMAL_FACETS, level)
    levels.update(dict.fromkeys(INVERSE_FACETS, inverse_level))
    kwargs.setdefault("levels", levels)
    return make_target(target_id, **kwargs)


def claim(claim_id: str, source_ids: Sequence[str], *, status: str = "active") -> ClaimRecord:
    """A synthetic claim carrying only its identity and its source ids."""
    return ClaimRecord(claim_id=claim_id, source_ids=tuple(source_ids), status=status)


def make_inputs(
    targets: Sequence[TargetInput],
    claims: Sequence[ClaimRecord] = (),
) -> RepositoryInputs:
    """A synthetic cohort, tagged ``reader='synthetic'`` so it can never be mistaken
    for repository data in a report sidecar."""
    return RepositoryInputs(
        targets=tuple(targets),
        claims={c.claim_id: c for c in claims},
        reader="synthetic",
        notes=("synthetic fixture cohort; contains no evidence",),
    )
