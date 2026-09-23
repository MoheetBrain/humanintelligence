#!/usr/bin/env python3
"""Quantify the effect of the Sprint-4 KDE-Tweedie defect (amendment A2) on the two Sprint-4 quantities that
used it: (1) Gate B expected concordance fraction (gate_b_genc.py), (2) Gate A locus sign-test power
(decide.py power_findings). Recomputes both with the stable EB estimator; writes
data/sprint5/sprint4_tweedie_correction.json. Nothing in Sprint 4's decision logic depended on these values
(they are descriptive expectations), which the output states explicitly."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import eb_shrink as EB  # noqa: E402

DAVIES = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/inputs/davies2018_open_complete.txt")


def kde_tweedie(z_all, z_eval):
    kde = stats.gaussian_kde(z_all)
    h = 1e-3
    return z_eval + (np.log(kde(z_eval + h)) - np.log(kde(z_eval - h))) / (2 * h)


def main() -> int:
    z_all = pd.read_csv(DAVIES, sep=r"\s+", usecols=["Zscore"]).Zscore.to_numpy()[::50]
    loci = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv")
    tp = loci[loci.TMA_status == "TESTABLE"]
    za = np.abs(tp.davies_z.to_numpy())
    out = {"created_utc": C.utc_now()}
    for name, mu in (("sprint4_kde_tweedie", kde_tweedie(z_all, za)), ("eb_scale_mixture", EB.shrink(z_all, za))):
        exp = {f"f={f}": float(stats.norm.cdf(np.clip(mu, 0, None) * f * np.sqrt(9932 / 282014)).mean()) for f in (1.0, 0.752)}
        fr = pd.read_csv(C.REPO_ROOT / "research/sprint4/frozen_hypotheses.json") if False else None
        frozen = json.loads((C.REPO_ROOT / "research/sprint4/frozen_hypotheses.json").read_text())
        L = pd.DataFrame(frozen["loci"])
        m2 = np.clip((kde_tweedie if name.startswith("sprint4") else EB.shrink)(z_all, np.abs(L.lead_davies_z.to_numpy())), 0, None)
        pw = {}
        for n in (4999, 9997):
            pc = stats.norm.cdf(m2 * 0.78 * np.sqrt(n / 282014))
            k = len(pc)
            crit = int(stats.binom.ppf(0.95, k, 0.5)) + 1
            sims = np.random.default_rng(1).binomial(1, pc, size=(4000, k)).sum(axis=1)
            pw[f"n{n}"] = {"expected_concordance": float(pc.mean()), "power": float((sims >= crit).mean())}
        out[name] = {"gate_b_expected_concordance": exp, "gate_a_locus_sign_test": pw,
                     "n_negative_or_nonmonotone_mu": int((mu < 0).sum())}
    out["observed_gate_b_concordance"] = float((tp.TMA_aligned_z > 0).mean())
    out["decision_impact"] = ("none: both quantities are descriptive expectations; Sprint-4 gates used the observed "
                              "binomial concordance test and frozen set-level rules, not these expectations")
    (C.DATA / "sprint4_tweedie_correction.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
