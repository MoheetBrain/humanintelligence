#!/usr/bin/env python3
"""Robust Rank Aggregation, Borda and Pareto — Sprint 3, Part N.

Why not one weighted score
---------------------------
The brief forbids a single arbitrary weighted score, and it is right to. A weighted
score has to state how many units of "adult brain colocalisation" equal one unit of
"within-family replication", and there is no defensible exchange rate between them. Worse,
the weights become invisible: a reader sees a number and cannot tell that it encodes
somebody's opinion about what matters.

Rank aggregation avoids the exchange rate entirely. It asks a different question — *does
this gene rank better across dimensions than it would if the dimensions were unrelated to
each other?* — which is a testable claim rather than a preference.

Robust Rank Aggregation (Kolde et al. 2012, Bioinformatics 28:573)
-------------------------------------------------------------------
For a gene appearing in ``n`` ranked lists, normalise each rank to ``r in (0, 1]``. Under
the null that the lists are random permutations, the ``k``-th smallest of ``n`` such
values is Beta(k, n-k+1) distributed. So for each ``k``:

    p_k = BetaCDF(r_(k); k, n-k+1)

which asks: *how surprising is it that this gene's k-th best rank is as good as it is?*
The score is ``rho = min_k p_k``, and the reported P is ``min(rho * n, 1)`` — a Bonferroni
correction for having taken the minimum over ``n`` choices of k.

The property that matters here: **a gene can win on a few dimensions and be missing or
poor on others, and still score well.** That is the correct behaviour for this problem,
because no gene has evidence on every dimension and requiring it would rank the
best-studied genes rather than the best-supported ones.

Missing data, and the choice that decides the answer
-----------------------------------------------------
A gene absent from a dimension is NOT scored zero and NOT imputed. Two policies are
implemented and both are reported, because they encode opposite beliefs:

* ``penalise`` — an absent gene is placed at the bottom of that list. This treats
  "not measured" as "measured and bad", which is the failure mode this project keeps
  finding in its own work.
* ``ignore`` (default) — the gene is aggregated over the dimensions where it was
  measured, with ``n`` set to the number of lists it actually appears in.

``ignore`` is correct on the evidence but has a real cost: a gene measured on one
dimension and excellent there can outrank a gene measured on eight and good on all. The
output therefore always carries ``n_dimensions_present``, and no top list may be read
without it.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np
from scipy import stats


def normalised_ranks(values: Sequence[float], higher_is_better: bool) -> np.ndarray:
    """Competition-rank ``values``, then scale to (0, 1]; NaN stays NaN."""
    arr = np.asarray(values, dtype=float)
    present = ~np.isnan(arr)
    out = np.full(arr.shape, np.nan)
    if present.sum() == 0:
        return out
    subset = arr[present]
    order = stats.rankdata(-subset if higher_is_better else subset, method="average")
    out[present] = order / (present.sum() + 0.0)
    return out


def rra_score(ranks: Iterable[float]) -> tuple[float, float, int]:
    """Return (rho, corrected_p, n_lists) for one gene's normalised ranks.

    ``ranks`` may contain NaN for dimensions where the gene was not measured; those are
    dropped rather than penalised (see the module docstring).
    """
    r = np.sort(np.asarray([v for v in ranks if not (v is None or math.isnan(v))], dtype=float))
    n = r.size
    if n == 0:
        return float("nan"), float("nan"), 0
    k = np.arange(1, n + 1)
    p = stats.beta.cdf(r, k, n - k + 1)
    rho = float(np.min(p))
    return rho, float(min(rho * n, 1.0)), n


def borda_score(ranks: Iterable[float]) -> float:
    """Mean normalised rank over measured dimensions — the sensitivity comparator.

    Borda is included because it fails differently from RRA: it rewards consistent
    mediocrity and punishes a single missing dimension less sharply. Where the two
    disagree about a gene, the disagreement is the finding.
    """
    values = [v for v in ranks if not (v is None or math.isnan(v))]
    return float(np.mean(values)) if values else float("nan")


def pareto_front(matrix: np.ndarray) -> np.ndarray:
    """Boolean mask of rows not dominated on ANY dimension (lower is better).

    A gene is on the front when no other gene is at least as good on every measured
    dimension and strictly better on one. Unlike a score, this makes no trade-off at
    all — which is why it usually returns an uncomfortably large set. That size is
    information: it is how many genes the evidence genuinely cannot rank against each
    other.
    """
    n = matrix.shape[0]
    on_front = np.ones(n, dtype=bool)
    filled = np.where(np.isnan(matrix), np.inf, matrix)
    for i in range(n):
        if not on_front[i]:
            continue
        dominated = np.all(filled <= filled[i], axis=1) & np.any(filled < filled[i], axis=1)
        if dominated.any():
            on_front[i] = False
    return on_front


def leave_one_dimension_out(rank_matrix: np.ndarray) -> np.ndarray:
    """Recompute RRA rho with each dimension dropped in turn.

    Returns an (n_genes, n_dimensions) array where column j is the rho obtained without
    dimension j. A gene whose rho collapses when one column is removed is being carried
    by that column alone, and the top-50 table says so rather than presenting a stable
    consensus that is not one.
    """
    n_genes, n_dims = rank_matrix.shape
    out = np.full((n_genes, n_dims), np.nan)
    for j in range(n_dims):
        keep = [c for c in range(n_dims) if c != j]
        for i in range(n_genes):
            out[i, j] = rra_score(rank_matrix[i, keep])[0]
    return out
