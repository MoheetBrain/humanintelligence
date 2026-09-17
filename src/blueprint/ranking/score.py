"""Dimension scores, gates, composite, rank distribution and tiers.

The pipeline, per Monte Carlo draw, is exactly the order declared in
``models/ranking/ranking_spec_v0_1.yaml`` §4:

1. sample a belief for every applicable facet from its level -> Beta mapping;
2. invert the beliefs of ``polarity: inverse`` facets;
3. aggregate to six dimensions as a weighted mean over applicable facets;
4. cap each dimension with any gate that triggers;
5. aggregate the capped dimensions to a composite;
6. cap the composite with any composite-level gate;
7. rank targets within the draw.

Summaries (median and 90% interval) are taken across draws at the end, never
mid-pipeline: taking a median early would discard exactly the correlation between
targets that the rank interval is there to show.

No numeric constant appears in this module. Everything comes from the loaded
:class:`blueprint.ranking.rubric.ModelSpec`.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from blueprint.ranking.inputs import RepositoryInputs, TargetInput
from blueprint.ranking.rubric import (
    AGGREGATIONS,
    DIMENSION_IDS,
    HUMAN_PROPOSITION_FACETS,
    ModelSpec,
    SpecError,
)
from blueprint.ranking.uncertainty import (
    beta_draws,
    kendall_tau_b,
    quantile,
    rank_within_draws,
    rng_for,
)

__all__ = [
    "CapSensitivity",
    "CohortResult",
    "DimensionScore",
    "RankSummary",
    "TargetScore",
    "assign_tier",
    "cap_sensitivity",
    "composite_from_dimensions",
    "coverage_of",
    "dimension_draws",
    "evidence_state_counts",
    "expected_composite",
    "expected_dimensions",
    "facet_contribution_draws",
    "facet_evidence_state",
    "independent_source_count",
    "score_cohort",
]

#: Condition keys a gate may use. An unknown key is an error, so that editing the
#: spec cannot silently produce a gate that never fires.
_GATE_CONDITION_KEYS = frozenset(
    {
        "facet",
        "level_at_least",
        "level_below",
        "counter_level_at_most",
        "human_proposition_facets_max_level_below",
        "audit_unresolved_critical_findings_at_least",
        "note",
    }
)


@dataclass(frozen=True, slots=True)
class DimensionScore:
    """One dimension for one target.

    Attributes:
        dimension: ``D1``..``D6``.
        draws: Post-gate draws, shape ``(n_draws,)``.
        median: 50th percentile of ``draws``.
        p05: Lower end of the 90% interval.
        p95: Upper end of the 90% interval.
        level: Highest *assessed* supporting level among the facets feeding this
            dimension, or ``None`` when none was assessed. An evidence-depth
            indicator, not a score.
        counter_level: Highest ``counter_level`` among the feeding facets, or ``None``.
            Reported alongside ``level`` so that "graded 2 and contradicted at 3" is
            distinguishable from "nobody graded it" — two states the contract
            requires to stay distinct (§5.2) and which a single level column would
            conflate.
        n_assessed: How many feeding facets were actually graded.
        n_applicable: How many feeding facets apply to this target.
        n_level_zero: How many feeding facets were graded 0, i.e. searched and nothing
            found. A documented absence of evidence, not an absence of assessment.
        gates_applied: Ids of gates that capped this dimension.
    """

    dimension: str
    draws: np.ndarray = field(repr=False)
    median: float
    p05: float
    p95: float
    level: int | None
    counter_level: int | None
    n_assessed: int
    n_applicable: int
    n_level_zero: int = 0
    gates_applied: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TargetScore:
    """The full scored row for one target, before ranks are known."""

    target_id: str
    symbol: str
    lead_atlas: str | None
    dossier_depth: str | None
    dimensions: Mapping[str, DimensionScore]
    composite_draws: np.ndarray = field(repr=False)
    composite_median: float = 0.0
    composite_p05: float = 0.0
    composite_p95: float = 0.0
    alternative_composites: Mapping[str, np.ndarray] = field(default_factory=dict, repr=False)
    coverage: float = 0.0
    facets_assessed: int = 0
    facets_applicable: int = 0
    facets_not_assessed: int = 0
    facets_level_zero: int = 0
    facets_contradicted: int = 0
    reporting_gap_count: int = 0
    claim_count: int = 0
    independent_source_count: int = 0
    tractability_level: int | None = None
    tractability_evidence_basis: str | None = None
    red_team_verdict: str | None = None
    is_audited: bool = False
    n_downgrades: int = 0
    unresolved_critical_findings: int = 0
    gates_applied: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RankSummary:
    """Rank distribution and tier for one target."""

    target_id: str
    rank_median: float
    rank_p05: float
    rank_p95: float
    tier: str


@dataclass(frozen=True, slots=True)
class CohortResult:
    """Everything a report needs for one model run."""

    spec: ModelSpec
    seed: int
    n_draws: int
    targets: tuple[TargetScore, ...]
    ranks: Mapping[str, RankSummary]
    sensitivity: Mapping[str, float]
    composite_matrix: np.ndarray = field(repr=False, default_factory=lambda: np.zeros((0, 0)))
    gates_triggered: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    evidence_gap_facets: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    pairwise_sensitivity: Mapping[str, float] = field(default_factory=dict)
    rank_by_aggregation: Mapping[str, Mapping[str, float]] = field(default_factory=dict)

    @property
    def n_targets(self) -> int:
        """Number of ranked targets."""
        return len(self.targets)

    def target_index(self) -> Mapping[str, int]:
        """Map target id to its row in :attr:`composite_matrix`."""
        return {t.target_id: i for i, t in enumerate(self.targets)}


# ---------------------------------------------------------------------------
# Facet level
# ---------------------------------------------------------------------------


def facet_contribution_draws(
    spec: ModelSpec,
    target: TargetInput,
    *,
    n_draws: int,
    seed: int,
) -> dict[str, np.ndarray]:
    """Draws of every applicable facet's *contribution* for one target.

    A contribution is the facet belief after polarity handling: ``p`` for a
    ``direct`` facet and ``1 - p`` for an ``inverse`` one, so that a dimension can
    always aggregate contributions additively.

    Args:
        spec: The loaded model specification.
        target: The target whose facets to sample.
        n_draws: Monte Carlo draw count.
        seed: Master seed.

    Returns:
        ``{facet_name: array of shape (n_draws,)}``, omitting facets recorded as
        ``not_applicable``. Facets recorded ``not_assessed`` ARE included, drawn
        from the uninformative Beta(1, 1) — dropping them would reward absence of
        scrutiny (contract P8).
    """
    contributions: dict[str, np.ndarray] = {}
    for facet_name in spec.facet_names:
        assessment = target.facet(facet_name)
        if not assessment.is_applicable:
            continue
        facet_spec = spec.facets[facet_name]
        alpha, beta = spec.beta_parameters(assessment.level, assessment.counter_level)
        rng = rng_for(seed, target.target_id, facet_name)
        draws = beta_draws(alpha, beta, n_draws, rng)
        contributions[facet_name] = 1.0 - draws if facet_spec.is_inverse else draws
    return contributions


# ---------------------------------------------------------------------------
# Dimension level
# ---------------------------------------------------------------------------


def dimension_draws(
    spec: ModelSpec,
    target: TargetInput,
    contributions: Mapping[str, np.ndarray],
) -> dict[str, DimensionScore]:
    """Aggregate facet contributions into the six gated dimensions.

    Args:
        spec: The loaded model specification.
        target: The target (needed to evaluate gate conditions and count coverage).
        contributions: Output of :func:`facet_contribution_draws`.

    Returns:
        ``{dimension_id: DimensionScore}`` for all six dimensions. A dimension none
        of whose facets are applicable falls back to the uninformative prior draws
        of its own facets; since every facet in the v0.1 catalogue has
        ``applicability: all_targets``, that case only arises if an agent records a
        whole dimension as ``not_applicable``, and it is reported with
        ``n_applicable = 0`` so it is visible rather than silent.
    """
    n_draws = len(next(iter(contributions.values()))) if contributions else 0
    scores: dict[str, DimensionScore] = {}
    q05, q50, q95 = spec.quantiles

    for dimension in DIMENSION_IDS:
        numerator = np.zeros(n_draws, dtype=np.float64)
        weight_total = 0.0
        n_assessed = 0
        n_applicable = 0
        n_level_zero = 0
        levels: list[int] = []
        counter_levels: list[int] = []
        for facet_spec in spec.facets_for(dimension):
            draws = contributions.get(facet_spec.facet)
            if draws is None:
                continue
            weight = float(facet_spec.weights[dimension])
            numerator += weight * draws
            weight_total += weight
            n_applicable += 1
            assessment = target.facet(facet_spec.facet)
            if assessment.counter_level is not None:
                counter_levels.append(int(assessment.counter_level))
            if assessment.is_assessed:
                n_assessed += 1
                if assessment.level is not None:
                    levels.append(int(assessment.level))
                    if int(assessment.level) == 0:
                        n_level_zero += 1

        if weight_total > 0.0:
            raw = numerator / weight_total
        else:
            # No applicable facet feeds this dimension for this target. Refuse to
            # invent a value: emit the uninformative midpoint and report it as
            # having zero applicable inputs.
            raw = np.full(n_draws, 0.5, dtype=np.float64)

        capped, gates_applied = _apply_gates(spec, target, dimension, raw)
        scores[dimension] = DimensionScore(
            dimension=dimension,
            draws=capped,
            median=quantile(capped, q50) if n_draws else float("nan"),
            p05=quantile(capped, q05) if n_draws else float("nan"),
            p95=quantile(capped, q95) if n_draws else float("nan"),
            level=max(levels) if levels else None,
            counter_level=max(counter_levels) if counter_levels else None,
            n_assessed=n_assessed,
            n_applicable=n_applicable,
            n_level_zero=n_level_zero,
            gates_applied=gates_applied,
        )
    return scores


def _apply_gates(
    spec: ModelSpec,
    target: TargetInput,
    dimension: str,
    draws: np.ndarray,
    *,
    aggregation: str | None = None,
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Cap ``draws`` with every gate for ``dimension`` that triggers on ``target``.

    ``aggregation`` is needed only for ``COMPOSITE`` gates, whose caps may be declared
    on the dimension-equivalent scale and must be converted to the composite's own
    scale under the operator in use (:meth:`blueprint.ranking.rubric.Gate.cap_for`).
    """
    applied: list[str] = []
    result = draws
    for gate in spec.gates_for(dimension):
        if _gate_triggers(gate.condition, gate.gate_id, target):
            result = np.minimum(result, gate.cap_for(aggregation or spec.primary_aggregation))
            applied.append(gate.gate_id)
    return result, tuple(applied)


def _gate_triggers(condition: Mapping[str, object], gate_id: str, target: TargetInput) -> bool:
    """Evaluate one gate condition against a target's recorded facets and audit.

    All clauses in a condition are ANDed. ``not_assessed`` never satisfies a
    ``level_at_least`` clause and always satisfies a ``level_below`` clause: an
    unasked question is not evidence, and cannot release a ceiling.

    Raises:
        SpecError: If the condition uses an unrecognised key. Failing loudly is the
            point — a mistyped gate key would otherwise produce a gate that silently
            never fires.
    """
    unknown = set(condition) - _GATE_CONDITION_KEYS
    if unknown:
        raise SpecError(f"gate {gate_id}: unrecognised condition keys {sorted(unknown)}")

    facet_name = condition.get("facet")
    if facet_name is not None:
        assessment = target.facet(str(facet_name))
        level = assessment.level if assessment.is_assessed else None
        counter = assessment.counter_level
        if "level_at_least" in condition:
            if level is None or level < int(condition["level_at_least"]):  # type: ignore[arg-type]
                return False
        if "level_below" in condition:
            if level is not None and level >= int(condition["level_below"]):  # type: ignore[arg-type]
                return False
        if "counter_level_at_most" in condition:
            if counter is not None and counter > int(condition["counter_level_at_most"]):  # type: ignore[arg-type]
                return False

    if "human_proposition_facets_max_level_below" in condition:
        threshold = int(condition["human_proposition_facets_max_level_below"])  # type: ignore[arg-type]
        best = -1
        for name in sorted(HUMAN_PROPOSITION_FACETS):
            assessment = target.facet(name)
            if assessment.is_assessed and assessment.level is not None:
                best = max(best, int(assessment.level))
        if best >= threshold:
            return False

    if "audit_unresolved_critical_findings_at_least" in condition:
        threshold = int(condition["audit_unresolved_critical_findings_at_least"])  # type: ignore[arg-type]
        if target.audit.unresolved_critical_findings < threshold:
            return False

    return True


# ---------------------------------------------------------------------------
# Composite level
# ---------------------------------------------------------------------------


def composite_from_dimensions(
    spec: ModelSpec,
    target: TargetInput,
    dimensions: Mapping[str, DimensionScore],
    *,
    method: str | None = None,
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Aggregate the six gated dimensions into a composite, then cap it.

    The default is the operator the spec declares as primary, which is ``product``:
    the six dimensions are CONDITIONS THAT MUST ALL HOLD, so the composite is their
    joint probability under an explicit independence assumption
    (``ranking_spec_v0_1.yaml`` §5). A weighted mean would let five favourable
    conditions compensate for one that fails, which is the inference this project must
    not license.

    Args:
        spec: The loaded model specification.
        target: The target (for composite-level gate conditions).
        dimensions: Output of :func:`dimension_draws`.
        method: Override the operator. ``product`` (conjunction under independence),
            ``minimum`` (strictest conjunction), ``weighted_additive`` (the
            compensatory counterfactual), or ``geometric_mean`` (order-equivalent to
            ``product``; available but not carried as a variant). Defaults to
            ``spec.primary_aggregation``.

    Returns:
        ``(draws, gate_ids)``. Composite-level gates are applied under every operator
        so that a sensitivity comparison isolates the aggregation function rather than
        mixing in a difference in gating.

    Raises:
        SpecError: If ``method`` is unknown.

    The independence assumption in ``product`` is FALSE in a known direction: the
    dimensions share facets, and the facets share claims, sources, cohorts and a
    grader. The true joint is higher than the product of the marginals for a target
    whose dimensions are favourable together, and the reported intervals are too narrow.
    Both are stated in the spec and on every report.
    """
    method = method or spec.primary_aggregation
    stacked = np.vstack([dimensions[d].draws for d in DIMENSION_IDS])

    if method == "product":
        raw = np.prod(stacked, axis=0)
    elif method == "minimum":
        raw = np.min(stacked, axis=0)
    elif method == "weighted_additive":
        weights = np.array([float(spec.dimension_weights[d]) for d in DIMENSION_IDS], dtype=np.float64)
        raw = (weights[:, None] * stacked).sum(axis=0) / weights.sum()
    elif method == "geometric_mean":
        # Computed in log space: stable, and Beta draws are strictly inside (0, 1).
        # Order-equivalent to `product`; kept callable for diagnostics only.
        raw = np.exp(np.mean(np.log(np.clip(stacked, 1e-12, 1.0)), axis=0))
    else:
        raise SpecError(
            f"unknown aggregation method {method!r}; expected one of "
            f"{sorted(AGGREGATIONS)}"
        )

    return _apply_gates(spec, target, "COMPOSITE", raw, aggregation=method)


# ---------------------------------------------------------------------------
# Analytic (draw-free) scores
# ---------------------------------------------------------------------------


def expected_dimensions(spec: ModelSpec, target: TargetInput) -> dict[str, float]:
    """The six dimensions computed from Beta *means* instead of draws.

    A deterministic, noise-free companion to :func:`dimension_draws`, used to state
    and test the model's structural properties (monotonicity in level, monotonicity
    in ``counter_level``, gate behaviour) without Monte Carlo error standing in the
    way.

    It is **not** the mean of the sampled dimension: gates are applied to the mean
    here, whereas the sampled path caps every draw and then summarises, and
    ``E[min(X, c)] <= min(E[X], c)``. So this function is an upper bound on the
    sampled mean whenever a gate binds. It is a diagnostic, not a reported number.
    """
    means: dict[str, float] = {}
    for facet_name in spec.facet_names:
        assessment = target.facet(facet_name)
        if not assessment.is_applicable:
            continue
        facet_spec = spec.facets[facet_name]
        alpha, beta = spec.beta_parameters(assessment.level, assessment.counter_level)
        mean = alpha / (alpha + beta)
        means[facet_name] = 1.0 - mean if facet_spec.is_inverse else mean

    dimensions: dict[str, float] = {}
    for dimension in DIMENSION_IDS:
        numerator = 0.0
        weight_total = 0.0
        for facet_spec in spec.facets_for(dimension):
            mean = means.get(facet_spec.facet)
            if mean is None:
                continue
            weight = float(facet_spec.weights[dimension])
            numerator += weight * mean
            weight_total += weight
        value = (numerator / weight_total) if weight_total > 0.0 else 0.5
        for gate in spec.gates_for(dimension):
            if _gate_triggers(gate.condition, gate.gate_id, target):
                value = min(value, gate.cap)
        dimensions[dimension] = value
    return dimensions


def expected_composite(
    spec: ModelSpec,
    target: TargetInput,
    *,
    method: str | None = None,
) -> float:
    """The composite computed from Beta means; see :func:`expected_dimensions`."""
    method = method or spec.primary_aggregation
    dimensions = expected_dimensions(spec, target)
    values = np.array([dimensions[d] for d in DIMENSION_IDS], dtype=np.float64)

    if method == "product":
        value = float(np.prod(values))
    elif method == "minimum":
        value = float(np.min(values))
    elif method == "weighted_additive":
        weights = np.array([float(spec.dimension_weights[d]) for d in DIMENSION_IDS], dtype=np.float64)
        value = float((weights * values).sum() / weights.sum())
    elif method == "geometric_mean":
        value = float(np.exp(np.mean(np.log(np.clip(values, 1e-12, 1.0)))))
    else:
        raise SpecError(f"unknown aggregation method {method!r}")

    for gate in spec.gates_for("COMPOSITE"):
        if _gate_triggers(gate.condition, gate.gate_id, target):
            value = min(value, gate.cap_for(method))
    return value


# ---------------------------------------------------------------------------
# Per-target derived counts
# ---------------------------------------------------------------------------


def coverage_of(spec: ModelSpec, target: TargetInput) -> tuple[float, int, int]:
    """``(coverage, facets_assessed, facets_applicable)`` for one target.

    Coverage is assessed facets divided by *applicable* facets, so recording a facet
    as ``not_applicable`` does not depress coverage, while leaving it
    ``not_assessed`` does. Coverage of a target with no applicable facets is 0.0.
    """
    state = evidence_state_counts(spec, target)
    return state["coverage"], state["assessed"], state["applicable"]


def evidence_state_counts(spec: ModelSpec, target: TargetInput) -> dict[str, float]:
    """Counts that keep the three "no support" states distinguishable.

    Contract §5.2 forbids collapsing them, and a report that showed only a coverage
    fraction would do exactly that. The three states, and the count that exposes each:

    * **nobody looked** -> ``not_assessed``: the facet is ungraded and contributes an
      uninformative prior.
    * **searched, nothing found** -> ``level_zero``: a documented, weak negative.
    * **tested and contradicted** -> ``contradicted``: graded, with ``counter_level``
      at 2 or above, which is a different and stronger statement than either.

    A fourth state sits alongside them and is counted separately: **tried, nothing
    published** -> ``reporting_gaps``, the distinct registered interventions that
    completed without posted results (contract §5.2, R14). That is a fact about
    reporting bias rather than about the target, so it never touches a level or a
    ``counter_level``.

    Returns:
        ``{"coverage", "applicable", "assessed", "not_assessed", "level_zero",
        "contradicted"}``. ``contradicted`` counts applicable facets whose
        ``counter_level`` is 2 or more, which is the rubric's threshold for
        "moderate" contradicting evidence.
    """
    applicable = 0
    assessed = 0
    level_zero = 0
    contradicted = 0
    reporting_gaps: set[str] = set()
    for facet_name in spec.facet_names:
        assessment = target.facet(facet_name)
        if not assessment.is_applicable:
            continue
        applicable += 1
        if assessment.is_assessed:
            assessed += 1
            if assessment.level == 0:
                level_zero += 1
        if assessment.counter_level is not None and int(assessment.counter_level) >= 2:
            contradicted += 1
        # Deduplicated at SOURCE level across facets, for the same reason
        # `independent_source_count` is: one unreported trial listed against three
        # facets is one reporting gap, not three (contract P5, and R15's scope
        # judgement — inflating a bias count by re-counting one study is the same
        # error as inflating evidence by re-citing one paper).
        reporting_gaps.update(assessment.reporting_gap_refs)
    return {
        "coverage": (assessed / applicable) if applicable else 0.0,
        "applicable": applicable,
        "assessed": assessed,
        "not_assessed": applicable - assessed,
        "level_zero": level_zero,
        "contradicted": contradicted,
        "reporting_gaps": len(reporting_gaps),
    }


def facet_evidence_state(spec: ModelSpec, target: TargetInput) -> dict[str, dict[str, object]]:
    """Per-facet ``{status, level, counter_level}`` for the report sidecar.

    The CSV carries per-dimension summaries; this carries the full per-facet state, so
    that a level-0-with-counter-evidence case and a ``not_assessed`` case are
    recoverable from the artefacts rather than only from the source records.
    """
    state: dict[str, dict[str, object]] = {}
    for facet_name in spec.facet_names:
        assessment = target.facet(facet_name)
        state[facet_name] = {
            "status": assessment.assessment_status,
            "level": assessment.level,
            "counter_level": assessment.counter_level,
            "polarity": spec.facets[facet_name].polarity,
            "n_claim_refs": len(assessment.claim_refs),
            "n_counter_claim_refs": len(assessment.counter_claim_refs),
            "reporting_gap_refs": list(assessment.reporting_gap_refs),
            "limiting_factor": assessment.limiting_factor,
        }
    return state


def independent_source_count(inputs: RepositoryInputs, target: TargetInput) -> tuple[int, int]:
    """``(independent_source_count, claim_count)`` for one target.

    Source-level deduplication (contract P5): the distinct set of source ids behind
    every claim this target's facets reference. Citing the same paper from five
    claims contributes one source. The gap between the two returned numbers is
    itself informative — a target with 12 claims and 3 sources is leaning on very
    few independent observations.
    """
    claim_ids = target.referenced_claim_ids()
    return len(inputs.source_ids_for(claim_ids)), len(claim_ids)


def assign_tier(
    spec: ModelSpec,
    *,
    coverage: float,
    is_audited: bool,
    verdict: str | None,
    rank_median: float,
    rank_p95: float,
    n_targets: int,
) -> str:
    """Assign an analysis-priority tier, per ``ranking_spec`` §6.

    Rules are evaluated in the spec's declared order and the first match wins.
    Every tier name says "analyse": a tier is a statement about where further
    *computational* work is worth doing, never about whether a target should be
    modulated.
    """
    tiers = spec.tiers
    if verdict in ("deprioritise", "insufficient_evidence"):
        return "tier_4_deprioritised_by_audit"
    if coverage < float(tiers["min_coverage"]) or not is_audited:
        return "tier_3_insufficient_coverage"
    top_cut = math.ceil(float(tiers["top_fraction"]) * n_targets)
    if rank_p95 <= top_cut:
        return "tier_1_analyse_next"
    mid_cut = math.ceil(float(tiers["mid_fraction"]) * n_targets)
    if rank_median <= mid_cut:
        return "tier_2_promising_underdetermined"
    return "tier_5_lower_priority"


# ---------------------------------------------------------------------------
# Cohort
# ---------------------------------------------------------------------------


def score_cohort(
    inputs: RepositoryInputs,
    spec: ModelSpec,
    *,
    n_draws: int | None = None,
    seed: int | None = None,
    apply_audit_adjustments: bool = True,
) -> CohortResult:
    """Score and rank a whole cohort.

    Args:
        inputs: The cohort. Only targets carrying at least one graded facet are
            ranked; an ungraded target would be a row of pure prior, which would be
            a statement about curation rather than about the target.
        spec: The loaded model specification.
        n_draws: Override the spec's Monte Carlo draw count (tests use fewer).
        seed: Override the spec's master seed.
        apply_audit_adjustments: Apply red-team downgrades to input levels first.
            Only set to ``False`` to measure what the audit changed.

    Returns:
        A :class:`CohortResult`. Empty input yields an empty result rather than an
        error: the caller decides how to report "nothing to rank yet".
    """
    draws = int(n_draws if n_draws is not None else spec.n_draws)
    master_seed = int(seed if seed is not None else spec.seed)

    cohort = inputs.with_audit_adjustments_applied() if apply_audit_adjustments else inputs
    # `claim_type: evidence_gap` records that an endpoint was never measured. It is a
    # coverage gap, not evidence against anything, so any counter_level resting only on
    # such claims is dropped before scoring (contract §4.1 as amended). The affected
    # facets are reported rather than silently removed.
    cohort, evidence_gap_facets = cohort.with_evidence_gaps_neutralised()
    targets = sorted(cohort.targets_with_assessments, key=lambda t: t.target_id)
    if not targets:
        return CohortResult(
            spec=spec,
            seed=master_seed,
            n_draws=draws,
            targets=(),
            ranks={},
            sensitivity={},
            composite_matrix=np.zeros((0, draws)),
            gates_triggered={},
            evidence_gap_facets=dict(evidence_gap_facets),
            pairwise_sensitivity={},
            rank_by_aggregation={},
        )

    q05, q50, q95 = spec.quantiles
    scored: list[TargetScore] = []
    alternative_names = spec.alternative_aggregations
    alternative_rows: dict[str, list[np.ndarray]] = {name: [] for name in alternative_names}
    gates_triggered: dict[str, tuple[str, ...]] = {}

    for target in targets:
        contributions = facet_contribution_draws(spec, target, n_draws=draws, seed=master_seed)
        dimensions = dimension_draws(spec, target, contributions)
        composite, composite_gates = composite_from_dimensions(spec, target, dimensions)
        state = evidence_state_counts(spec, target)
        sources, claims = independent_source_count(cohort, target)

        alternatives: dict[str, np.ndarray] = {}
        for name in alternative_names:
            alternative, _ = composite_from_dimensions(spec, target, dimensions, method=name)
            alternatives[name] = alternative
            alternative_rows[name].append(alternative)

        all_gates = tuple(
            sorted({*composite_gates, *(g for d in dimensions.values() for g in d.gates_applied)})
        )
        if all_gates:
            gates_triggered[target.target_id] = all_gates

        scored.append(
            TargetScore(
                target_id=target.target_id,
                symbol=target.symbol,
                lead_atlas=target.lead_atlas,
                dossier_depth=target.dossier_depth,
                dimensions=dimensions,
                composite_draws=composite,
                composite_median=quantile(composite, q50),
                composite_p05=quantile(composite, q05),
                composite_p95=quantile(composite, q95),
                alternative_composites=alternatives,
                coverage=float(state["coverage"]),
                facets_assessed=int(state["assessed"]),
                facets_applicable=int(state["applicable"]),
                facets_not_assessed=int(state["not_assessed"]),
                facets_level_zero=int(state["level_zero"]),
                facets_contradicted=int(state["contradicted"]),
                reporting_gap_count=int(state["reporting_gaps"]),
                claim_count=claims,
                independent_source_count=sources,
                tractability_level=(
                    target.facet("tractability").level
                    if target.facet("tractability").is_assessed
                    else None
                ),
                tractability_evidence_basis=target.facet("tractability").evidence_basis,
                red_team_verdict=target.audit.verdict,
                is_audited=target.audit.is_audited,
                n_downgrades=target.audit.n_downgrades,
                unresolved_critical_findings=target.audit.unresolved_critical_findings,
                gates_applied=all_gates,
            )
        )

    composite_matrix = np.vstack([t.composite_draws for t in scored])
    rank_matrix = rank_within_draws(composite_matrix)

    ranks: dict[str, RankSummary] = {}
    for index, target_score in enumerate(scored):
        row = rank_matrix[index]
        rank_median = quantile(row, q50)
        rank_p05 = quantile(row, q05)
        rank_p95 = quantile(row, q95)
        ranks[target_score.target_id] = RankSummary(
            target_id=target_score.target_id,
            rank_median=rank_median,
            rank_p05=rank_p05,
            rank_p95=rank_p95,
            tier=assign_tier(
                spec,
                coverage=target_score.coverage,
                is_audited=target_score.is_audited,
                verdict=target_score.red_team_verdict,
                rank_median=rank_median,
                rank_p95=rank_p95,
                n_targets=len(scored),
            ),
        )

    # Per-operator median ranks, primary first, then every declared variant. Keeping
    # the full orderings (not only a tau-b against the primary) is what lets a reader
    # see WHICH targets the operator choice moves rather than only that it moves some.
    rank_by_aggregation: dict[str, dict[str, float]] = {
        spec.primary_aggregation: {t.target_id: ranks[t.target_id].rank_median for t in scored}
    }
    for name in alternative_names:
        alternative_ranks = rank_within_draws(np.vstack(alternative_rows[name]))
        rank_by_aggregation[name] = {
            scored[i].target_id: quantile(alternative_ranks[i], q50) for i in range(len(scored))
        }

    # All PAIRWISE comparisons, not only variant-against-primary: the primary is not
    # privileged as a reference point when the question is whether the ordering is a
    # property of the operator at all.
    operator_names = [spec.primary_aggregation, *alternative_names]
    pairwise: dict[str, float] = {}
    sensitivity: dict[str, float] = {}
    for index, left in enumerate(operator_names):
        for right in operator_names[index + 1 :]:
            key = f"{left}__vs__{right}"
            if len(scored) < 2:
                pairwise[key] = float("nan")
                continue
            ordered_ids = [s.target_id for s in scored]
            pairwise[key] = kendall_tau_b(
                [rank_by_aggregation[left][tid] for tid in ordered_ids],
                [rank_by_aggregation[right][tid] for tid in ordered_ids],
            )
    # Retained for backwards compatibility: each variant against the primary.
    for name in alternative_names:
        key = f"{spec.primary_aggregation}__vs__{name}"
        sensitivity[name] = pairwise.get(key, float("nan"))

    return CohortResult(
        spec=spec,
        seed=master_seed,
        n_draws=draws,
        targets=tuple(scored),
        ranks=ranks,
        sensitivity=sensitivity,
        composite_matrix=composite_matrix,
        gates_triggered=gates_triggered,
        evidence_gap_facets=dict(evidence_gap_facets),
        pairwise_sensitivity=pairwise,
        rank_by_aggregation=rank_by_aggregation,
    )


def composite_medians(result: CohortResult) -> Sequence[float]:
    """Composite medians in cohort order (convenience for reports and tests)."""
    return [t.composite_median for t in result.targets]


@dataclass(frozen=True, slots=True)
class CapSensitivity:
    """Rank effect of the precautionary capping asymmetry (contract §5.4).

    Attributes:
        rank_delta: ``rank_median(symmetric) - rank_median(polarity_aware)`` per target
            that had a cap derived for it. Negative means the target ranks BETTER under
            symmetric caps, i.e. the precaution is costing it rank. Targets with no
            derived cap are absent, which is deliberately different from present-and-zero.
        kendall_tau_b: tau-b between the two median-rank orderings over the whole cohort.
        sensitive_targets: Targets whose ``|rank_delta|`` exceeds the spec's threshold.
        threshold: The threshold used, from the spec.
        polarity_aware_was_a_no_op: True when re-applying the policy caps changed
            nothing, i.e. the grading agents had already applied contract §5.4. A False
            here is a finding about curation, not about the targets.
        cap_applications: Per mode, per target, a one-line record of what each cap did.
        n_caps_derived: How many caps were derived across the cohort.
    """

    rank_delta: Mapping[str, float] = field(default_factory=dict)
    kendall_tau_b: float = float("nan")
    sensitive_targets: tuple[str, ...] = ()
    threshold: float = 0.0
    polarity_aware_was_a_no_op: bool = True
    cap_applications: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    n_caps_derived: int = 0


def cap_sensitivity(
    inputs: RepositoryInputs,
    spec: ModelSpec,
    *,
    n_draws: int | None = None,
    seed: int | None = None,
    apply_audit_adjustments: bool = True,
) -> CapSensitivity:
    """Measure what the polarity-aware capping asymmetry costs in rank positions.

    Contract §5.4 requires this to be measured rather than assumed. The method is a
    straight counterfactual: score the cohort twice on the same seed and the same draw
    count, once with caps applied polarity-aware (the policy) and once with them applied
    symmetrically, and report the per-target rank difference plus the Kendall tau-b
    between the two orderings.

    Args:
        inputs: The cohort.
        spec: The loaded model specification.
        n_draws: Monte Carlo draws; defaults to the spec's.
        seed: Master seed; defaults to the spec's. Both variants use the same one, so
            the difference is the capping rule and not sampling noise.
        apply_audit_adjustments: Passed through to both runs.

    Returns:
        A :class:`CapSensitivity`. With no derived caps it returns an empty result with
        ``kendall_tau_b = 1.0``, which is the truthful answer: the two variants are the
        same model.
    """
    from blueprint.ranking.caps import cap_cohort, derive_caps_for_cohort  # noqa: PLC0415

    derived = derive_caps_for_cohort(spec, inputs)
    n_caps = sum(len(caps) for caps in derived.values())
    threshold = float(
        (spec.cap_variants.get("sensitivity_threshold") or {}).get("rank_positions", 0.0)
    )

    policy_inputs, policy_records = cap_cohort(
        spec, inputs, mode="polarity_aware", caps_by_target=derived
    )
    symmetric_inputs, symmetric_records = cap_cohort(
        spec, inputs, mode="symmetric", caps_by_target=derived
    )

    policy = score_cohort(
        policy_inputs, spec, n_draws=n_draws, seed=seed,
        apply_audit_adjustments=apply_audit_adjustments,
    )
    symmetric = score_cohort(
        symmetric_inputs, spec, n_draws=n_draws, seed=seed,
        apply_audit_adjustments=apply_audit_adjustments,
    )

    shared = [t.target_id for t in policy.targets if t.target_id in symmetric.ranks]
    deltas: dict[str, float] = {}
    for target_id in shared:
        if not derived.get(target_id):
            continue
        deltas[target_id] = round(
            symmetric.ranks[target_id].rank_median - policy.ranks[target_id].rank_median, 4
        )

    if len(shared) >= 2:
        tau = kendall_tau_b(
            [policy.ranks[t].rank_median for t in shared],
            [symmetric.ranks[t].rank_median for t in shared],
        )
    else:
        tau = float("nan")

    applications = {
        f"{mode}:{target_id}": tuple(record.summary for record in records)
        for mode, record_map in (
            ("polarity_aware", policy_records),
            ("symmetric", symmetric_records),
        )
        for target_id, records in sorted(record_map.items())
    }
    no_op = not any(
        record.applied for records in policy_records.values() for record in records
    )

    return CapSensitivity(
        rank_delta=dict(sorted(deltas.items())),
        kendall_tau_b=tau,
        sensitive_targets=tuple(
            sorted(t for t, delta in deltas.items() if abs(delta) >= threshold)
        ),
        threshold=threshold,
        polarity_aware_was_a_no_op=no_op,
        cap_applications=applications,
        n_caps_derived=n_caps,
    )
