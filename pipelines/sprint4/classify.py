"""Sprint 4 — frozen classification rules as pure functions (tested in test_sprint4.py).

Every threshold comes from research/sprint4/frozen_hypotheses.json via ``common.load_frozen``; this
module never defines a threshold of its own. NOT_TESTABLE is a first-class outcome and is never
converted into an effect estimate or into "no effect".
"""

from __future__ import annotations

import math

import numpy as np

NOT_TESTABLE = "NOT_TESTABLE"


def thresholds(frozen: dict) -> dict:
    a = frozen["rules"]["gate_a"]["set_classification"]
    return {"alpha": float(a["alpha_one_sided"]), "q_low": float(a["expected_quantile_low"]),
            "power_adequate": 0.5}


def expected_distribution(sim_betas: np.ndarray, sim_ps: np.ndarray, q_low: float, alpha: float) -> dict:
    sim_betas = np.asarray(sim_betas, float)
    sim_ps = np.asarray(sim_ps, float)
    if len(sim_betas) == 0:
        return {"n_reps": 0}
    return {"n_reps": int(len(sim_betas)), "median": float(np.median(sim_betas)),
            "q_low": float(np.quantile(sim_betas, q_low)), "q_high": float(np.quantile(sim_betas, 1 - q_low)),
            "power": float((sim_ps < alpha).mean())}


def classify_set(beta: float | None, p: float | None, expected: dict | None, frozen: dict,
                 supported_label: str = "DIRECT_EFFECT_SUPPORTED") -> dict:
    """Gate A (supported_label=DIRECT_EFFECT_SUPPORTED) or Gate B (INDEPENDENT_SUPPORT) set class."""
    t = thresholds(frozen)
    if beta is None or p is None or (isinstance(beta, float) and math.isnan(beta)) or \
            (isinstance(p, float) and math.isnan(p)):
        return {"class": NOT_TESTABLE, "subtype": "no data", "can_drive_pivot": False}
    if p < t["alpha"]:
        return {"class": supported_label, "subtype": "", "can_drive_pivot": False}
    if not expected or expected.get("n_reps", 0) == 0:
        # without a calibration the rule cannot place beta against its expectation
        return {"class": "CONCORDANT_BUT_UNDERPOWERED" if beta > 0 else "INCONSISTENT",
                "subtype": "NO_CALIBRATION_AVAILABLE" if beta > 0 else "SIGN_DISCORDANT_UNCALIBRATED",
                "can_drive_pivot": False}
    adequate = expected["power"] >= t["power_adequate"]
    if beta < expected["q_low"]:
        return {"class": "INCONSISTENT", "subtype": "BEYOND_EXPECTED_NOISE", "can_drive_pivot": adequate,
                "power": expected["power"]}
    if beta > 0:
        return {"class": "CONCORDANT_BUT_UNDERPOWERED", "subtype": "", "can_drive_pivot": False,
                "power": expected["power"]}
    return {"class": "INCONSISTENT", "subtype": "SIGN_DISCORDANT_WITHIN_NOISE", "can_drive_pivot": False,
            "power": expected["power"]}


def classify_locus_wf(aligned_z: float | None, expected_z: float | None, status: str) -> str:
    if status != "TESTABLE" or aligned_z is None or (isinstance(aligned_z, float) and math.isnan(aligned_z)):
        return NOT_TESTABLE
    from scipy import stats
    if aligned_z > 0:
        return "DIRECT_SUPPORTED" if stats.norm.sf(aligned_z) < 0.05 else "CONCORDANT_UNDERPOWERED"
    if expected_z is not None and aligned_z < expected_z - 1.96:
        return "DISCORDANT_BEYOND_NOISE"
    return "DISCORDANT_WITHIN_NOISE"


def attenuation(beta_wf: float, se_wf: float, beta_pop: float, se_pop: float, seed: int, n: int = 10000) -> dict:
    """Ratio beta_wf/beta_pop with a parametric-bootstrap CI (independent normals: conservative) and a
    Fieller CI when |beta_pop/se_pop| > 2 (frozen rule)."""
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (beta_wf, se_wf, beta_pop, se_pop)):
        return {"ratio": None, "status": NOT_TESTABLE}
    rng = np.random.default_rng(seed)
    r = rng.normal(beta_wf, se_wf, n) / rng.normal(beta_pop, se_pop, n)
    out = {"ratio": beta_wf / beta_pop, "boot_ci95": [float(np.quantile(r, 0.025)), float(np.quantile(r, 0.975))]}
    if abs(beta_pop / se_pop) > 2:
        z = 1.96
        a = beta_pop ** 2 - z * z * se_pop ** 2
        b = -2 * beta_wf * beta_pop
        c = beta_wf ** 2 - z * z * se_wf ** 2
        disc = b * b - 4 * a * c
        if a > 0 and disc >= 0:
            out["fieller_ci95"] = sorted([(-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)])
    return out
