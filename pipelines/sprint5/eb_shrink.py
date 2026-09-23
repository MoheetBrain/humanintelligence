"""Stable winner's-curse shrinkage for GWAS z-scores (Sprint 5 amendment A2).

Estimand: E[mu | z] (the same quantity the Sprint-4 KDE-Tweedie targeted).
Model: z = mu + e, e ~ N(0,1); mu ~ sum_k pi_k N(0, s_k^2) on a fixed grid s_k (ash-style scale mixture,
k=0 is a point mass at 0). pi fitted by EM on genome-wide z (every 50th Davies SNP).
Posterior mean: E[mu|z] = sum_k w_k(z) * z * s_k^2/(1+s_k^2), w_k(z) ∝ pi_k N(z; 0, 1+s_k^2).
Monotone in |z|, sign-preserving, well defined in the extreme tail (the KDE gradient was not: Sprint-4
Tweedie mapped z=8.33 -> -1.99 and z=6.23 -> 8.88).
"""

from __future__ import annotations

import numpy as np
from scipy import stats

GRID = np.array([0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0])


def fit(z_all: np.ndarray, iters: int = 500) -> np.ndarray:
    z = np.asarray(z_all, float)
    z = z[np.isfinite(z)]
    sd = np.sqrt(1 + GRID ** 2)
    L = stats.norm.pdf(z[:, None], 0, sd[None, :])
    pi = np.full(len(GRID), 1 / len(GRID))
    for _ in range(iters):
        w = L * pi
        w /= w.sum(1, keepdims=True)
        new = w.mean(0)
        if np.max(np.abs(new - pi)) < 1e-9:
            pi = new
            break
        pi = new
    return pi


def posterior_mean(z_eval: np.ndarray, pi: np.ndarray) -> np.ndarray:
    z = np.asarray(z_eval, float)
    sd = np.sqrt(1 + GRID ** 2)
    lw = np.log(np.maximum(pi, 1e-300))[None, :] + stats.norm.logpdf(z[:, None], 0, sd[None, :])
    lw -= lw.max(1, keepdims=True)
    w = np.exp(lw)
    w /= w.sum(1, keepdims=True)
    shrink = GRID ** 2 / (1 + GRID ** 2)
    return (w * shrink[None, :]).sum(1) * z


def shrink(z_all: np.ndarray, z_eval: np.ndarray) -> np.ndarray:
    return posterior_mean(z_eval, fit(z_all))
