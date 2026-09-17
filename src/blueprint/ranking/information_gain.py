"""Which facet, if resolved, would most change the ranking.

Method (``models/ranking/ranking_spec_v0_1.yaml`` §7): for every target and every
applicable facet, re-score that target with the facet's level moved one step up and
one step down (clipped to 0..4), holding every other facet and every other target
fixed and **reusing the same random draws**. The rank swing between the two
perturbations is how unresolved that facet leaves the target's position.

Two things make this cheap enough to sweep exhaustively. First, only one target's
composite changes per perturbation, so the other targets' composite draws are reused
from the baseline run. Second, a target's rank within a draw is just
``1 + #{others with a higher composite}`` plus half the ties, which is a vectorised
comparison against the cached matrix rather than a re-sort.

What this measures, and what it does not
----------------------------------------
It measures the sensitivity of *this model's ranking* to *this facet's grade*. It is
not a measure of scientific importance, and it structurally favours facets with large
weights and dimensions with few inputs (D3 has one facet, so that facet always looks
influential). Read the output as "where is the ranking unresolved", and treat the
honest_limitation note in the spec as part of the result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

import numpy as np

from blueprint.ranking.inputs import RepositoryInputs, TargetInput
from blueprint.ranking.rubric import ModelSpec
from blueprint.ranking.score import (
    CohortResult,
    composite_from_dimensions,
    dimension_draws,
    facet_contribution_draws,
)
from blueprint.ranking.uncertainty import beta_draws, quantile, rng_for

__all__ = [
    "FacetInformationGain",
    "TargetInformationGain",
    "facet_information_gain",
    "most_informative_facet",
    "repository_next_analyses",
]

#: Levels used as the "down" and "up" cases for a facet nobody has graded yet.
#: Perturbing an ungraded facet from the prior has no defined baseline level, so the
#: spec's one-level-perturbation rule is applied to the two levels that bracket the
#: uninformative prior: level 1 ("weak or indirect") and level 3 ("substantial").
UNASSESSED_DOWN_LEVEL = 1
UNASSESSED_UP_LEVEL = 3


@dataclass(frozen=True, slots=True)
class FacetInformationGain:
    """Rank movement for one (target, facet) pair under a one-level perturbation."""

    target_id: str
    facet: str
    baseline_status: str
    baseline_level: int | None
    level_down: int
    level_up: int
    rank_median_down: float
    rank_median_up: float
    rank_swing: float
    interval_reduction: float
    unresolved_multiplier: float
    value: float

    @property
    def is_unresolved(self) -> bool:
        """True when the facet has not been graded at all."""
        return self.baseline_status == "not_assessed"


@dataclass(frozen=True, slots=True)
class TargetInformationGain:
    """Per-facet gains for one target, plus the winner."""

    target_id: str
    baseline_rank_median: float
    baseline_rank_width: float
    facets: tuple[FacetInformationGain, ...]

    @property
    def best(self) -> FacetInformationGain | None:
        """The facet whose resolution would most reduce this target's rank uncertainty."""
        return self.facets[0] if self.facets else None


def _rank_of(own: np.ndarray, others: np.ndarray) -> np.ndarray:
    """Rank of one target per draw against a cached matrix of the others.

    Args:
        own: Composite draws for the target, shape ``(n_draws,)``.
        others: Composite draws for every other target, shape
            ``(n_others, n_draws)``.

    Returns:
        Ranks per draw with 1 = best, ties averaged — consistent with
        :func:`blueprint.ranking.uncertainty.average_ranks`, so a perturbation of
        zero reproduces the baseline rank exactly.
    """
    if others.size == 0:
        return np.ones_like(own)
    greater = np.count_nonzero(others > own[None, :], axis=0)
    equal = np.count_nonzero(others == own[None, :], axis=0)
    return 1.0 + greater + equal / 2.0


def _perturbed_composite(
    spec: ModelSpec,
    target: TargetInput,
    contributions: Mapping[str, np.ndarray],
    facet: str,
    level: int,
    *,
    n_draws: int,
    seed: int,
) -> np.ndarray:
    """Composite draws for ``target`` with ``facet`` forced to ``level``.

    Reuses every other facet's cached draws, and re-draws only the perturbed facet —
    from the same ``(seed, target, facet)`` stream, so the perturbation changes the
    distribution rather than the random numbers.
    """
    assessment = target.facet(facet)
    facet_spec = spec.facets[facet]
    alpha, beta = spec.beta_parameters(level, assessment.counter_level)
    rng = rng_for(seed, target.target_id, facet)
    draws = beta_draws(alpha, beta, n_draws, rng)
    contribution = 1.0 - draws if facet_spec.is_inverse else draws

    perturbed_contributions = dict(contributions)
    perturbed_contributions[facet] = contribution
    perturbed_target = replace(
        target,
        facets={**dict(target.facets), facet: assessment.with_level(level)},
    )
    dimensions = dimension_draws(spec, perturbed_target, perturbed_contributions)
    composite, _ = composite_from_dimensions(spec, perturbed_target, dimensions)
    return composite


def facet_information_gain(
    result: CohortResult,
    inputs: RepositoryInputs,
    *,
    apply_audit_adjustments: bool = True,
) -> dict[str, TargetInformationGain]:
    """Sweep every (target, facet) pair and rank the facets by rank movement.

    Args:
        result: A scored cohort from :func:`blueprint.ranking.score.score_cohort`.
        inputs: The same inputs that produced ``result``.
        apply_audit_adjustments: Must match the flag used for ``result``, so the
            perturbation baseline is the same evidence state that was ranked.

    Returns:
        ``{target_id: TargetInformationGain}`` with each target's facets sorted by
        descending value. Ties break on facet name, for determinism only.
    """
    spec = result.spec
    cohort = inputs.with_audit_adjustments_applied() if apply_audit_adjustments else inputs
    by_id = {t.target_id: t for t in cohort.targets}
    index = result.target_index()
    matrix = result.composite_matrix
    q05, q50, q95 = spec.quantiles
    multipliers = spec.information_gain.get("unresolved_multiplier", {})

    output: dict[str, TargetInformationGain] = {}
    for scored in result.targets:
        target = by_id.get(scored.target_id)
        if target is None:  # pragma: no cover - cohort and result always agree
            continue
        row = index[scored.target_id]
        others = np.delete(matrix, row, axis=0)
        baseline_ranks = _rank_of(scored.composite_draws, others)
        baseline_median = quantile(baseline_ranks, q50)
        baseline_width = quantile(baseline_ranks, q95) - quantile(baseline_ranks, q05)

        contributions = facet_contribution_draws(
            spec, target, n_draws=result.n_draws, seed=result.seed
        )
        gains: list[FacetInformationGain] = []
        for facet_name in spec.facet_names:
            assessment = target.facet(facet_name)
            multiplier = float(multipliers.get(assessment.assessment_status, 0.0))
            if not assessment.is_applicable or multiplier <= 0.0:
                continue

            if assessment.is_assessed and assessment.level is not None:
                level_down = max(0, int(assessment.level) - 1)
                level_up = min(4, int(assessment.level) + 1)
            else:
                level_down, level_up = UNASSESSED_DOWN_LEVEL, UNASSESSED_UP_LEVEL

            widths: list[float] = []
            medians: dict[str, float] = {}
            for label, level in (("down", level_down), ("up", level_up)):
                composite = _perturbed_composite(
                    spec,
                    target,
                    contributions,
                    facet_name,
                    level,
                    n_draws=result.n_draws,
                    seed=result.seed,
                )
                ranks = _rank_of(composite, others)
                medians[label] = quantile(ranks, q50)
                widths.append(quantile(ranks, q95) - quantile(ranks, q05))

            rank_swing = abs(medians["up"] - medians["down"])
            interval_reduction = baseline_width - min(widths)
            gains.append(
                FacetInformationGain(
                    target_id=scored.target_id,
                    facet=facet_name,
                    baseline_status=assessment.assessment_status,
                    baseline_level=assessment.level,
                    level_down=level_down,
                    level_up=level_up,
                    rank_median_down=medians["down"],
                    rank_median_up=medians["up"],
                    rank_swing=rank_swing,
                    interval_reduction=interval_reduction,
                    unresolved_multiplier=multiplier,
                    value=rank_swing * multiplier,
                )
            )

        gains.sort(key=lambda g: (-g.value, -g.interval_reduction, g.facet))
        output[scored.target_id] = TargetInformationGain(
            target_id=scored.target_id,
            baseline_rank_median=baseline_median,
            baseline_rank_width=baseline_width,
            facets=tuple(gains),
        )
    return output


def most_informative_facet(gains: TargetInformationGain | None) -> tuple[str, float]:
    """``(facet_name, value)`` for one target, or ``("", 0.0)`` when undefined.

    A value of exactly ``0.0`` with a named facet means "resolving this facet would
    not move this target's rank at all", which happens when the target's composite
    is far from any neighbour. That is a real and reportable answer, not a failure.
    """
    if gains is None or gains.best is None:
        return "", 0.0
    return gains.best.facet, gains.best.value


def repository_next_analyses(
    gains: Mapping[str, TargetInformationGain],
    *,
    limit: int = 25,
) -> tuple[dict[str, object], ...]:
    """The highest-value next analyses across the whole repository.

    Args:
        gains: Output of :func:`facet_information_gain`.
        limit: Maximum number of rows to return.

    Returns:
        Plain dictionaries (JSON-ready for the report sidecar), sorted by descending
        value then by target id and facet name so the list is deterministic.
    """
    rows: list[dict[str, object]] = []
    for target_id in sorted(gains):
        for gain in gains[target_id].facets:
            rows.append(
                {
                    "target_id": target_id,
                    "facet": gain.facet,
                    "baseline_status": gain.baseline_status,
                    "baseline_level": gain.baseline_level,
                    "rank_swing": round(gain.rank_swing, 4),
                    "interval_reduction": round(gain.interval_reduction, 4),
                    "value": round(gain.value, 4),
                }
            )
    rows.sort(key=lambda r: (-float(r["value"]), str(r["target_id"]), str(r["facet"])))
    return tuple(rows[:limit])


def gains_as_table(gains: Mapping[str, TargetInformationGain]) -> Sequence[dict[str, object]]:
    """Every (target, facet) gain as flat rows, for diagnostics and tests."""
    return repository_next_analyses(gains, limit=10**9)
