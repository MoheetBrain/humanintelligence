"""Monte Carlo machinery: ordinal levels to Beta draws, quantiles, ranks, tau-b.

Every statistic here is implemented in-repo. scipy is not available in this
environment, and pinning the definitions locally also removes any ambiguity about
which quantile convention or which tie correction produced a published number.

Determinism is a hard requirement (``models/uncertainty/uncertainty_spec_v0_1.yaml``
§4). It is achieved by keying each random stream on ``(seed, *key_parts)`` through a
hash-derived :class:`numpy.random.SeedSequence`, so a target's draws do not depend on
how many targets are in the run or the order in which they are processed. Two runs
with the same seed and inputs produce identical arrays, and adding a target to the
cohort does not perturb any other target's draws.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import numpy as np

__all__ = [
    "average_ranks",
    "beta_draws",
    "kendall_tau_b",
    "quantile",
    "rank_within_draws",
    "rng_for",
    "summarise",
]


def rng_for(seed: int, *key_parts: str) -> np.random.Generator:
    """A deterministic generator for one named random stream.

    Args:
        seed: The run's master seed (from the uncertainty spec).
        *key_parts: Stable strings identifying the stream, e.g. a target id and a
            facet name. Order matters; content does not need to be sorted.

    Returns:
        A :class:`numpy.random.Generator` that depends only on ``seed`` and
        ``key_parts``.

    The key is hashed with blake2b rather than :func:`hash`, because Python's
    ``hash`` is salted per process and would destroy reproducibility across runs.
    """
    digest = hashlib.blake2b("\x1f".join(key_parts).encode("utf-8"), digest_size=8).digest()
    return np.random.default_rng(np.random.SeedSequence([int(seed), int.from_bytes(digest, "big")]))


def beta_draws(alpha: float, beta: float, n_draws: int, rng: np.random.Generator) -> np.ndarray:
    """``n_draws`` samples from ``Beta(alpha, beta)``.

    Args:
        alpha: First Beta shape parameter; must be positive.
        beta: Second Beta shape parameter; must be positive.
        n_draws: Number of samples.
        rng: Generator obtained from :func:`rng_for`.

    Returns:
        A float64 array of shape ``(n_draws,)`` with values in ``(0, 1)``.

    Raises:
        ValueError: If either shape parameter is not positive.
    """
    if alpha <= 0.0 or beta <= 0.0:
        raise ValueError(f"Beta shape parameters must be positive, got ({alpha}, {beta})")
    return np.asarray(rng.beta(float(alpha), float(beta), size=int(n_draws)), dtype=np.float64)


def quantile(values: Sequence[float] | np.ndarray, q: float) -> float:
    """The ``q`` quantile by linear interpolation between order statistics.

    This is the "type 7" convention (the default in R and NumPy): for sorted
    ``x[0..n-1]`` and ``h = (n - 1) * q``, the result is
    ``x[floor(h)] + (h - floor(h)) * (x[floor(h) + 1] - x[floor(h)])``.

    Args:
        values: Sample values; must be non-empty.
        q: Quantile in ``[0, 1]``.

    Returns:
        The interpolated quantile as a float.

    Raises:
        ValueError: If ``values`` is empty or ``q`` is outside ``[0, 1]``.
    """
    array = np.sort(np.asarray(values, dtype=np.float64).ravel())
    if array.size == 0:
        raise ValueError("quantile of an empty sample is undefined")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q must be in [0, 1], got {q}")
    if array.size == 1:
        return float(array[0])
    position = (array.size - 1) * float(q)
    lower = int(np.floor(position))
    upper = min(lower + 1, array.size - 1)
    fraction = position - lower
    return float(array[lower] + fraction * (array[upper] - array[lower]))


def summarise(values: Sequence[float] | np.ndarray, quantiles: Sequence[float]) -> tuple[float, ...]:
    """Quantiles of ``values`` in the order given (one pass, one sort)."""
    array = np.sort(np.asarray(values, dtype=np.float64).ravel())
    return tuple(quantile(array, q) for q in quantiles)


def average_ranks(scores: np.ndarray) -> np.ndarray:
    """Ranks of ``scores`` with 1 = highest, ties resolved by average rank.

    Args:
        scores: 1-D array of composite scores, one per target.

    Returns:
        Float array of ranks, same shape as ``scores``.

    Average ranks (rather than ordinal or dense ranks) are used so that a tie does
    not silently advantage whichever target happens to come first in the cohort
    ordering. That matters: ties are common when many facets are unassessed.
    """
    scores = np.asarray(scores, dtype=np.float64).ravel()
    order = np.argsort(-scores, kind="stable")
    ordinal = np.empty(scores.size, dtype=np.float64)
    ordinal[order] = np.arange(1, scores.size + 1, dtype=np.float64)
    sorted_scores = scores[order]
    start = 0
    for index in range(1, sorted_scores.size + 1):
        if index == sorted_scores.size or sorted_scores[index] != sorted_scores[start]:
            if index - start > 1:
                tied = order[start:index]
                ordinal[tied] = ordinal[tied].mean()
            start = index
    return ordinal


def rank_within_draws(composites: np.ndarray) -> np.ndarray:
    """Rank targets within every Monte Carlo draw.

    Args:
        composites: Array of shape ``(n_targets, n_draws)``.

    Returns:
        Array of the same shape holding ranks (1 = best) per draw, ties averaged.

    Ranking *within* a draw is the whole point of the Monte Carlo: it preserves the
    correlation between targets that share a draw, so the rank interval reflects how
    often targets actually swap places rather than how wide their marginal score
    intervals are.
    """
    composites = np.asarray(composites, dtype=np.float64)
    if composites.ndim != 2:
        raise ValueError(f"composites must be 2-D (targets x draws), got shape {composites.shape}")
    ranks = np.empty_like(composites)
    for draw in range(composites.shape[1]):
        ranks[:, draw] = average_ranks(composites[:, draw])
    return ranks


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float:
    """Kendall's tau-b rank correlation, implemented here (no scipy available).

    tau-b is used rather than tau-a because ranks in this model tie routinely: many
    targets share a composite when most of their facets are unassessed, and tau-a
    would report a spuriously low correlation for what is really the same ordering.

    .. math::

        \\tau_b = \\frac{C - D}{\\sqrt{(n_0 - n_1)(n_0 - n_2)}}

    where ``C`` and ``D`` count concordant and discordant pairs,
    ``n_0 = n(n-1)/2``, ``n_1 = sum_i t_i (t_i - 1) / 2`` over tie groups in ``x``,
    and ``n_2`` is the same for ``y``.

    Args:
        x: First sequence of values (ranks or scores).
        y: Second sequence, same length as ``x``.

    Returns:
        tau-b in ``[-1, 1]``. Returns ``nan`` when either denominator factor is
        zero, i.e. when one sequence is entirely tied and no ordering exists to
        correlate. ``nan`` is returned rather than 0.0 because "undefined" and "no
        association" are different statements.

    Raises:
        ValueError: If the sequences differ in length or have fewer than 2 elements.
    """
    a = np.asarray(x, dtype=np.float64).ravel()
    b = np.asarray(y, dtype=np.float64).ravel()
    if a.size != b.size:
        raise ValueError(f"kendall_tau_b needs equal-length sequences, got {a.size} and {b.size}")
    if a.size < 2:
        raise ValueError("kendall_tau_b needs at least 2 observations")

    n = a.size
    concordant = 0
    discordant = 0
    for i in range(n - 1):
        da = a[i + 1 :] - a[i]
        db = b[i + 1 :] - b[i]
        product = np.sign(da) * np.sign(db)
        concordant += int(np.count_nonzero(product > 0))
        discordant += int(np.count_nonzero(product < 0))

    n0 = n * (n - 1) / 2.0
    n1 = _tie_correction(a)
    n2 = _tie_correction(b)
    denominator = (n0 - n1) * (n0 - n2)
    if denominator <= 0.0:
        return float("nan")
    return float((concordant - discordant) / np.sqrt(denominator))


def _tie_correction(values: np.ndarray) -> float:
    """``sum_i t_i (t_i - 1) / 2`` over the tie groups of ``values``."""
    _, counts = np.unique(values, return_counts=True)
    return float(np.sum(counts * (counts - 1) / 2.0))
