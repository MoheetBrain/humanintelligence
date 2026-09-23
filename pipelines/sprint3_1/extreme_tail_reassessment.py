#!/usr/bin/env python3
"""Sprint 3.1, part 7 — how fragile is the Sprint-3 "1.13x" continuity ratio?

Sprint 3 predicted the extreme-IQ (Zabaneh 2018) mean gene Z of the 375 population-Bonferroni
genes as  rest_mean + (mean Z_pop(sig) - mean Z_pop(all)) / sqrt(N_pop / N_eff),  with
N_eff = 4,300 (the case-control effective N), and reported observed/predicted shift = 1.13.

Three things that simple scaling ignores are quantified here as a sensitivity table:

1. **Extreme ascertainment.** Cases are the top ~0.03% of a (roughly normal) trait; controls
   are unselected. For a variant of per-allele effect beta (SD units) the case-control
   non-centrality is 2pq beta^2 i^2 N_eff / 4, where i is the mean standardised trait value of
   cases (truncated-normal mean). A population GWAS of size N has 2pq beta^2 N. The
   *equivalent* population N is therefore N_eff * i^2 / 4 — larger than N_eff when i > 2.
   Measurement error and regression to the mean (cases were selected on SAT at ~12 years)
   lower the effective i, so several selection fractions are shown.
2. **Winner's curse.** The 375 genes were selected on Davies Z, so their Davies mean Z is
   inflated; re-evaluating the same genes in Savage 2018 reduces (does not remove, since both
   contain UK Biobank) the inflation.
3. **Non-linearity.** MAGMA gene Z is the probit of a gene P-value from a sum of squared SNP z,
   so it does not scale linearly with sqrt(N). No closed-form fix is attempted; the ratio is
   therefore reported as indicative only. The rigorous expectation needs LD-aware subsampling
   of the population GWAS to the extreme study's equivalent N (the Sprint-4 calibration method).

4. **The Sprint-3 "121/159 loci same sign" was not a sign test.** MAGMA gene Z is unsigned
   (probit of a P-value), so "positive extreme-tail Z" meant "above-median association", not
   "same allele direction". A genuine locus-direction test is added here: at each of the 159
   Sprint-3 loci the Davies lead SNP's cognition-increasing allele is looked up in Zabaneh
   (log OR / SE), palindromic SNPs excluded, and concordance compared with 50% (null) and with
   the concordance expected under continuity (Tweedie-shrunk Davies z scaled to the extreme
   study's equivalent N).

Output: reports/sprint3_1/extreme_tail_reassessment.json (read by the markdown report).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "reports" / "sprint3_1"
N_POP, N_EFF_CC = 282014, 4300


def mean_liability_of_top(fraction: float) -> float:
    t = stats.norm.isf(fraction)
    return float(stats.norm.pdf(t) / fraction)


def read_genes(path: Path) -> pd.DataFrame:
    g = pd.read_csv(path, sep=r"\s+")
    return g[["GENE", "ZSTAT", "P"]]


LEADS_JSON = Path("/private/tmp/claude-501/-Users-moheet-Documents-ChatGPT-HUMAN-INTELLIGENCE---/"
                  "224f2c4f-7825-4f2f-9903-e47dd7525078/scratchpad/sprint4/frozen_hypotheses.json")
LEADS_CSV = OUT / "sprint3_loci_lead_snps.csv"
PALINDROMIC = {frozenset("AT"), frozenset("CG")}


def tweedie(z_all: np.ndarray, z_eval: np.ndarray) -> np.ndarray:
    """E[mu | z] = z + d/dz log f(z), f a Gaussian KDE of genome-wide z (every 50th SNP)."""
    kde = stats.gaussian_kde(z_all)
    h = 1e-3
    return z_eval + (np.log(kde(z_eval + h)) - np.log(kde(z_eval - h))) / (2 * h)


def locus_direction_test() -> dict:
    if not LEADS_CSV.exists():
        loci = json.loads(LEADS_JSON.read_text())["loci"]
        pd.DataFrame([{k: l[k] for k in ("locus_id", "chr", "lead_snp", "lead_effect_allele", "lead_other_allele",
                                         "lead_davies_z", "lead_davies_p", "cognition_increasing_allele", "top_gene")}
                      for l in loci]).to_csv(LEADS_CSV, index=False)
    leads = pd.read_csv(LEADS_CSV)
    davies = pd.read_csv("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/"
                         "inputs/davies2018_open_complete.txt", sep=r"\s+", usecols=["Zscore"]).Zscore.to_numpy()
    zab = pd.read_csv(REPO / "data/interim/sumstats/GCST005626_zabaneh_extremeIQ_b37.tsv.gz", sep="\t",
                      usecols=["variant_id", "effect_allele", "other_allele", "odds_ratio", "standard_error"])
    m = leads.merge(zab, left_on="lead_snp", right_on="variant_id", how="left")
    ea, oa = m.effect_allele.str.upper(), m.other_allele.str.upper()
    cog = m.cognition_increasing_allele.str.upper()
    other = np.where(cog == m.lead_effect_allele.str.upper(), m.lead_other_allele.str.upper(),
                     m.lead_effect_allele.str.upper())
    pal = [frozenset({a, b}) in PALINDROMIC for a, b in zip(m.lead_effect_allele.str.upper(),
                                                              m.lead_other_allele.str.upper())]
    z = np.log(m.odds_ratio) / m.standard_error
    sign = np.where((ea == cog) & (oa == other), 1, np.where((ea == other) & (oa == cog), -1, 0))
    m["zabaneh_z_aligned"] = z * sign
    m["status"] = np.where(m.variant_id.isna(), "ABSENT", np.where(pal, "PALINDROMIC_EXCLUDED",
                                                                   np.where(sign == 0, "ALLELE_MISMATCH", "TESTABLE")))
    t = m[m.status == "TESTABLE"].copy()
    conc = int((t.zabaneh_z_aligned > 0).sum())
    n = int(len(t))
    mu = tweedie(davies[::50], np.abs(t.lead_davies_z.to_numpy()))
    expected = {}
    for label, neq in (("N_eff 4,300", N_EFF_CC),
                       ("equivalent N, top 0.03%", N_EFF_CC * mean_liability_of_top(0.0003) ** 2 / 4),
                       ("equivalent N, top 3%", N_EFF_CC * mean_liability_of_top(0.03) ** 2 / 4)):
        pc = stats.norm.cdf(np.clip(mu, 0, None) * np.sqrt(neq / N_POP))
        expected[label] = {"expected_concordant": float(pc.sum()), "expected_fraction": float(pc.mean())}
    m[["locus_id", "top_gene", "lead_snp", "cognition_increasing_allele", "lead_davies_z", "status",
       "zabaneh_z_aligned"]].to_csv(OUT / "extreme_tail_locus_direction.csv", index=False, float_format="%.4g")
    return {"n_loci": int(len(m)), "n_testable": n, "n_absent": int((m.status == "ABSENT").sum()),
            "n_palindromic_excluded": int((m.status == "PALINDROMIC_EXCLUDED").sum()),
            "n_allele_mismatch": int((m.status == "ALLELE_MISMATCH").sum()),
            "n_concordant": conc, "fraction_concordant": conc / n if n else None,
            "binomial_P_vs_half_one_sided": float(stats.binomtest(conc, n, 0.5, alternative="greater").pvalue) if n else None,
            "expected_under_continuity": expected,
            "mean_aligned_z": float(t.zabaneh_z_aligned.mean()),
            "note": "signed allele-direction test; the Sprint-3 121/159 statistic was unsigned gene-level Z"}


def main() -> int:
    raw3 = REPO / "data" / "raw" / "magma_sprint3" / "2026-09-22"
    pop = read_genes(REPO / "data" / "raw" / "magma_x01" / "2026-09-22" / "davies2018_10kb.genes.out")
    ext = read_genes(raw3 / "zabaneh_extremeIQ_10kb.genes.out")
    sav = read_genes(raw3 / "savage2018_intelligence_10kb.genes.out")
    j = pop.merge(ext, on="GENE", suffixes=("_pop", "_ext")).merge(
        sav.rename(columns={"ZSTAT": "ZSTAT_sav", "P": "P_sav"}), on="GENE", how="left")
    sig = j.P_pop < 0.05 / len(pop)
    rest_ext = j.loc[~sig, "ZSTAT_ext"].mean()
    obs_shift = j.loc[sig, "ZSTAT_ext"].mean() - rest_ext
    rows = []
    for label, zcol in (("Davies Z (selection sample; Sprint 3)", "ZSTAT_pop"),
                        ("Savage Z for the same genes (winner's-curse sensitivity; overlaps UKB)", "ZSTAT_sav")):
        dz = j.loc[sig, zcol].mean() - j[zcol].mean()
        for scen, n_equiv, i_val in [("Sprint-3 assumption: N_eff = 4,300", N_EFF_CC, None)] + [
                (f"ascertainment-equivalent N, cases = top {frac * 100:g}% (i = {mean_liability_of_top(frac):.2f})",
                 N_EFF_CC * mean_liability_of_top(frac) ** 2 / 4, mean_liability_of_top(frac))
                for frac in (0.0003, 0.003, 0.03)]:
            pred_shift = dz / np.sqrt(N_POP / n_equiv)
            rows.append({"population_z_source": label, "scenario": scen, "equivalent_N": round(n_equiv),
                         "mean_liability_i": i_val, "predicted_shift": pred_shift,
                         "observed_shift": obs_shift, "observed_over_predicted": obs_shift / pred_shift})
    table = pd.DataFrame(rows)
    out = {
        "n_population_bonferroni_genes": int(sig.sum()),
        "observed_mean_Z_ext_significant": float(j.loc[sig, "ZSTAT_ext"].mean()),
        "observed_mean_Z_ext_rest": float(rest_ext),
        "sensitivity": table.to_dict(orient="records"),
        "ratio_range": [float(table.observed_over_predicted.min()), float(table.observed_over_predicted.max())],
        "note": ("Ratios span both sides of 1 depending on assumptions no one can pin down from summary "
                 "statistics (effective selection intensity, winner's curse, probit non-linearity). The "
                 "ratio therefore cannot prove continuity OR amplification."),
    }
    out["locus_direction_test"] = locus_direction_test()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "extreme_tail_reassessment.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    pd.set_option("display.width", 220)
    print(json.dumps(out["locus_direction_test"], indent=1))
    print(table[["population_z_source", "scenario", "equivalent_N", "predicted_shift", "observed_shift",
                 "observed_over_predicted"]].round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
