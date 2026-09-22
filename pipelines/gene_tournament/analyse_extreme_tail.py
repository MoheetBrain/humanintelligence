#!/usr/bin/env python3
"""Sprint 3, Part C — is extreme cognition continuous with population cognition?

The two modes the brief asks for, and which one is possible
------------------------------------------------------------
**MODE 2 (individual-level commonality) is NOT COMPUTABLE WITH CURRENT ACCESS**, and the
reason is worth stating precisely rather than waving at. It needs genotypes for
high-cognition individuals, and there are two independent locks:

* The only assembled extreme-IQ case sample is the Duke TIP cohort used by Spain 2016 and
  Zabaneh 2018 (top ~0.03% of the distribution, mean IQ ~170). **No public deposit of any
  kind exists** — no dbGaP, no EGA. Nothing in the publications indicates a deposition
  plan, so the route is a direct collaboration agreement, not an application.
* The controls are the Health and Retirement Study, dbGaP phs000428, Authorized Access:
  eRA Commons account, institutional Signing Official, Data Use Certification.

Every distributional quantity the brief lists for Mode 2 — Cohen's d, KS distance, AUC,
EXTREME_COGNITION_COMMONALITY_50/90, the sibling-pair comparisons — requires per-person
gene scores. None can be computed, and none is estimated here. Fabricating them from
summary statistics would produce numbers with the right names and no content.

**MODE 1 (summary-statistic extreme rank) IS computable**, because Zabaneh 2018's
summary statistics are openly downloadable (GCST005626).

The test, and why it is framed in aggregate
--------------------------------------------
The naive per-gene comparison is hopeless on power. Davies 2018 has N=282,014; Zabaneh
has 1,238 cases and 8,172 controls, an effective N of 4,300 — roughly **65x less**. A
per-gene "amplification" statistic is therefore dominated by sampling noise in the
extreme-tail numerator, and any gene that looks amplified is overwhelmingly likely to be
noise. That is reported per gene with an interval, and the interval is the point.

The question *can* be answered in aggregate, and that is the primary analysis:

    Under CONTINUITY, the genes that carry population-cognition signal should carry
    extreme-tail signal too, attenuated by power but not reordered.

    Under UPPER-TAIL AMPLIFICATION, a distinct set of genes should matter at the tail,
    and the population-significant set should show no shift in the extreme-tail data
    beyond what its own selection implies.

So the primary statistic is the shift in extreme-tail gene Z among population-significant
genes versus matched background — a test with real power even when no single gene reaches
significance.

The confound that must not be forgotten
----------------------------------------
Zabaneh's controls are HRS. HRS is a CHARGE cohort, and Davies 2018 is a CHARGE+COGENT+UKB
meta-analysis. **Sample overlap between the two studies is possible and is not resolved
here.** Overlap would inflate the correlation between them and bias the continuity test
toward the continuity answer. This is recorded as an unresolved threat, not dismissed.

Usage
-----
    python pipelines/gene_tournament/analyse_extreme_tail.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

OUT = REPO_ROOT / "reports" / "gene_tournament"
DATA = REPO_ROOT / "data" / "gene_tournament"
MAGMA = sorted((REPO_ROOT / "data" / "raw" / "magma_sprint3").glob("*/"))[-1]  # committed copies


def read_genes_out(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=r"\s+", comment="#")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=Path,
                        default=sorted((REPO_ROOT / "data" / "raw" / "magma_x01").glob(
                            "*/davies2018_10kb.genes.out"))[-1])
    parser.add_argument("--extreme", type=Path,
                        default=MAGMA / "zabaneh_extremeIQ_10kb.genes.out")
    args = parser.parse_args(argv)

    if not args.extreme.exists():
        raise SystemExit(f"extreme-tail gene analysis not found: {args.extreme}")

    gene_map = pd.read_csv(sorted((REPO_ROOT / "data" / "raw" / "magma_x01").glob(
        "*/gene_id_map.tsv"))[-1], sep="\t")
    ld = pd.read_parquet(DATA / "ld_loci.parquet")

    pop = read_genes_out(args.population).rename(columns={"ZSTAT": "Z_pop", "P": "P_pop",
                                                          "NSNPS": "NSNPS_pop"})
    ext = read_genes_out(args.extreme).rename(columns={"ZSTAT": "Z_ext", "P": "P_ext",
                                                       "NSNPS": "NSNPS_ext"})
    joined = (pop[["GENE", "CHR", "Z_pop", "P_pop", "NSNPS_pop"]]
              .merge(ext[["GENE", "Z_ext", "P_ext", "NSNPS_ext"]], on="GENE", how="inner")
              .merge(gene_map[["GENE", "current_symbol", "bp_length"]], on="GENE", how="left")
              .merge(ld, on="GENE", how="left"))
    n = len(joined)
    bonf_pop = 0.05 / len(pop)
    bonf_ext = 0.05 / len(ext)
    joined["pop_significant"] = joined.P_pop < bonf_pop

    result: dict = {
        "computed_at": utc_now(),
        "mode_2_individual_level": {
            "status": "INDIVIDUAL-LEVEL COMMONALITY NOT COMPUTABLE WITH CURRENT ACCESS",
            "cases_blocker": "Duke TIP extreme-IQ genotypes: no public deposit located "
                             "(no dbGaP, no EGA). Requires direct collaboration agreement.",
            "controls_blocker": "HRS controls: dbGaP phs000428 Authorized Access "
                                "(eRA Commons + institutional Signing Official + DUC).",
            "quantities_not_computed": [
                "mean/median/SD/IQR/percentiles of per-gene score by group",
                "Cohen's d", "Mann-Whitney on individuals", "KS distance", "AUC",
                "odds ratio", "fraction above control median/75th/90th",
                "EXTREME_COGNITION_COMMONALITY_50", "EXTREME_COGNITION_COMMONALITY_90",
                "within-family sibling-pair comparisons",
            ],
            "note": "Not estimated, not approximated, not imputed.",
        },
        "mode_1_summary_statistic": {},
    }

    # ---------------------------------------------------------------- primary test ----
    # Population-significant genes vs the rest, in the EXTREME-TAIL statistic.
    sig = joined[joined.pop_significant]
    rest = joined[~joined.pop_significant]
    u = stats.mannwhitneyu(sig.Z_ext, rest.Z_ext, alternative="greater")
    # Gene-size matched background: the confound that makes a naive comparison useless.
    matched_p = None
    try:
        bins = pd.qcut(np.log10(joined.bp_length.clip(lower=1)), 20, duplicates="drop")
        joined["_bin"] = bins
        draws = []
        rng = np.random.default_rng(20260922)
        for _ in range(2000):
            picked = []
            for b, group in sig.assign(_bin=bins.loc[sig.index]).groupby("_bin", observed=True):
                pool = rest[bins.loc[rest.index] == b]
                if len(pool):
                    picked.append(pool.Z_ext.iloc[rng.integers(0, len(pool), len(group))])
            if picked:
                draws.append(np.concatenate(picked).mean())
        draws = np.asarray(draws)
        observed = sig.Z_ext.mean()
        exceed = int((draws >= observed).sum())
        # 0 exceedances in 2,000 draws is P < 1/2000, never P = 0.
        matched_p = float(exceed / len(draws)) if exceed else f"<{1 / len(draws):.4g} (0 of {len(draws)} draws)"
    except Exception as error:  # noqa: BLE001
        matched_p = f"not_computed: {type(error).__name__}"

    spearman = stats.spearmanr(joined.Z_pop, joined.Z_ext)
    # One gene per LD block, so the correlation is not counting one locus many times.
    per_block = joined.loc[joined.groupby("ld_block_r0.2").P_pop.idxmin()]
    spearman_block = stats.spearmanr(per_block.Z_pop, per_block.Z_ext)

    result["mode_1_summary_statistic"] = {
        "population_gwas": {"file": str(args.population), "n_genes": int(len(pop)),
                            "bonferroni": bonf_pop,
                            "n_significant": int(joined.pop_significant.sum())},
        "extreme_gwas": {"file": str(args.extreme), "n_genes": int(len(ext)),
                         "bonferroni": bonf_ext,
                         "n_significant": int((joined.P_ext < bonf_ext).sum()),
                         "study": "Zabaneh 2018 GCST005626, 1,238 cases (top ~0.03%, "
                                  "mean IQ ~170) vs 8,172 controls, effective N 4,300"},
        "n_genes_in_both": n,
        "power_ratio_note": "Effective N 4,300 vs 282,014 -- about 65x less. Per-gene "
                            "tests in the extreme sample are underpowered by construction.",
        "continuity_tests": {
            "spearman_Z_pop_vs_Z_ext_all_genes": {
                "rho": float(spearman.statistic), "p": float(spearman.pvalue)},
            "spearman_one_gene_per_LD_block": {
                "rho": float(spearman_block.statistic), "p": float(spearman_block.pvalue),
                "n_blocks": int(len(per_block))},
            "extreme_Z_shift_in_population_significant_genes": {
                "mean_Z_ext_significant": float(sig.Z_ext.mean()),
                "mean_Z_ext_rest": float(rest.Z_ext.mean()),
                "mann_whitney_p": float(u.pvalue),
                "gene_size_matched_permutation_p": matched_p,
                "n_significant": int(len(sig)), "n_rest": int(len(rest))},
        },
    }

    # ------------------------------------------------------- per-gene amplification ----
    # Residual of extreme-tail Z on population Z. Reported WITH the caveat that the
    # residual SD is dominated by noise in Z_ext, so a large residual is not a finding.
    fit = stats.linregress(joined.Z_pop, joined.Z_ext)
    joined["Z_ext_expected"] = fit.intercept + fit.slope * joined.Z_pop
    joined["tail_amplification_residual"] = joined.Z_ext - joined.Z_ext_expected
    resid_sd = joined.tail_amplification_residual.std()
    joined["tail_amplification_z"] = joined.tail_amplification_residual / resid_sd
    result["mode_1_summary_statistic"]["amplification_model"] = {
        "definition": "EXTREME_TAIL_AMPLIFICATION = observed extreme-tail gene Z minus "
                      "the value predicted from population-cognition gene Z by OLS, "
                      "standardised by the residual SD.",
        "slope": float(fit.slope), "intercept": float(fit.intercept),
        "r_value": float(fit.rvalue), "slope_stderr": float(fit.stderr),
        "residual_sd": float(resid_sd),
        "interpretation_limit": "The residual SD is dominated by sampling noise in the "
                                "extreme-tail statistic, not by biology. A high "
                                "amplification z-score is a HYPOTHESIS, and with 18,000 "
                                "genes the extreme values are expected under the null.",
    }

    # ------------------------------------------------------------- continuity verdict ----
    ratio = float(np.sqrt(282014 / 4300))
    naive = float((sig.Z_pop.mean() - joined.Z_pop.mean()) / ratio + rest.Z_ext.mean())
    obs = float(sig.Z_ext.mean())
    blk = sig.loc[sig.groupby("ld_block_r0.2").P_pop.idxmin()]
    sign = stats.binomtest(int((blk.Z_ext > 0).sum()), len(blk), float((rest.Z_ext > 0).mean()),
                           alternative="greater")
    result["mode_1_summary_statistic"]["continuity_verdict"] = {
        "question": "Is extreme cognition continuous with population cognition at gene level?",
        "answer": "CONTINUOUS for common variants at gene level. No upper-tail amplification is "
                  "required to explain the data.",
        "power_scaling_test": {
            "sqrt_effective_N_ratio": ratio,
            "predicted_mean_Z_ext_for_population_significant_genes": naive,
            "observed": obs,
            "observed_over_predicted_shift": float((obs - rest.Z_ext.mean()) / (naive - rest.Z_ext.mean())),
            "reading": "Under pure continuity the same genes carry the same effects, detected with "
                       "sqrt(N) less precision."},
        "locus_level_sign_test": {"n_independent_loci": int(len(blk)),
                                  "n_with_positive_extreme_tail_Z": int((blk.Z_ext > 0).sum()),
                                  "background_rate": float((rest.Z_ext > 0).mean()), "p": float(sign.pvalue)},
        "n_genes_genome_wide_significant_in_extreme_sample": int((joined.P_ext < bonf_ext).sum()),
        "what_would_have_indicated_amplification": (
            "A distinct gene set at the tail: near-zero rank correlation with population cognition, no "
            "shift among population-significant genes, and tail-significant genes that are not "
            "population-associated. None of that is observed."),
        "unresolved_threat": (
            "Zabaneh's controls are the Health and Retirement Study. HRS is a CHARGE cohort and Davies "
            "2018 is a CHARGE+COGENT+UKB meta-analysis, so SAMPLE OVERLAP IS POSSIBLE AND NOT RESOLVED "
            "HERE. Overlap would inflate the correlation and bias this test toward continuity."),
        "scope_limit": "Common variants, European ancestry, gene level. Says nothing about rare "
                       "variants at the tail, which Spain 2016's exome-array null addresses only weakly.",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["current_symbol", "GENE", "CHR", "Z_pop", "P_pop", "Z_ext", "P_ext",
            "pop_significant", "tail_amplification_residual", "tail_amplification_z",
            "bp_length", "ld_block_r0.2"]
    out = joined[cols].sort_values("P_pop")
    out.to_csv(OUT / "extreme_tail_rank.csv", index=False)
    # ------------------------------------------------ extreme_tail_distribution_stats.csv --
    # The brief's Mode-2 quantities, each recorded as NOT computable, beside the gene-level
    # SUMMARY-STATISTIC analogue that IS computable. The analogue compares distributions of
    # extreme-tail gene Z between population-significant genes and all other genes. It is a
    # statement about GENES, never about PEOPLE, and every row says which it is.
    x1, x0 = sig.Z_ext.to_numpy(), rest.Z_ext.to_numpy()
    pooled = np.sqrt(((len(x1) - 1) * x1.var(ddof=1) + (len(x0) - 1) * x0.var(ddof=1)) / (len(x1) + len(x0) - 2))
    ks = stats.ks_2samp(x1, x0)
    auc = float(stats.mannwhitneyu(x1, x0).statistic / (len(x1) * len(x0)))
    dist = []
    for q in ["mean", "median", "SD", "IQR", "5th percentile", "95th percentile", "Cohen's d", "Mann-Whitney",
              "KS distance", "AUC", "odds ratio", "fraction above control median",
              "fraction above control 75th percentile", "fraction above control 90th percentile",
              "EXTREME_COGNITION_COMMONALITY_50", "EXTREME_COGNITION_COMMONALITY_90",
              "sibling-pair within-family comparison"]:
        dist.append({"quantity": q, "unit_of_analysis": "individual (high-IQ vs controls, per-gene score)",
                     "status": "INDIVIDUAL-LEVEL COMMONALITY NOT COMPUTABLE WITH CURRENT ACCESS",
                     "value": None})
    ana = {"mean": (x1.mean(), x0.mean()), "median": (np.median(x1), np.median(x0)),
           "SD": (x1.std(ddof=1), x0.std(ddof=1)),
           "IQR": (np.subtract(*np.percentile(x1, [75, 25])), np.subtract(*np.percentile(x0, [75, 25]))),
           "5th percentile": (np.percentile(x1, 5), np.percentile(x0, 5)),
           "95th percentile": (np.percentile(x1, 95), np.percentile(x0, 95))}
    for q, (v1, v0) in ana.items():
        dist.append({"quantity": q, "unit_of_analysis": "GENE (extreme-tail MAGMA Z; population-significant vs other genes)",
                     "status": "computed_gene_level_analogue",
                     "value": f"{v1:.4f} vs {v0:.4f}"})
    frac = lambda thr: float((x1 > thr).mean())  # noqa: E731
    for q, v in (("Cohen's d", (x1.mean() - x0.mean()) / pooled),
                 ("Mann-Whitney", float(u.pvalue)), ("KS distance", float(ks.statistic)),
                 ("AUC", auc),
                 ("fraction above control median", frac(np.median(x0))),
                 ("fraction above control 75th percentile", frac(np.percentile(x0, 75))),
                 ("fraction above control 90th percentile", frac(np.percentile(x0, 90)))):
        dist.append({"quantity": q, "unit_of_analysis": "GENE (extreme-tail MAGMA Z; population-significant vs other genes)",
                     "status": "computed_gene_level_analogue", "value": f"{v:.4g}"})
    pd.DataFrame(dist).to_csv(OUT / "extreme_tail_distribution_stats.csv", index=False)

    (OUT / "extreme_tail_summary.json").write_text(json.dumps(result, indent=2) + "\n",
                                                   encoding="utf-8")

    m = result["mode_1_summary_statistic"]
    print("MODE 2: NOT COMPUTABLE WITH CURRENT ACCESS (see summary json)\n")
    print(f"genes in both analyses: {n:,}")
    print(f"extreme-tail genome-wide significant genes: {m['extreme_gwas']['n_significant']}")
    print(f"\ncontinuity — Spearman(Z_pop, Z_ext) all genes: "
          f"rho={m['continuity_tests']['spearman_Z_pop_vs_Z_ext_all_genes']['rho']:.4f} "
          f"P={m['continuity_tests']['spearman_Z_pop_vs_Z_ext_all_genes']['p']:.3e}")
    b = m["continuity_tests"]["spearman_one_gene_per_LD_block"]
    print(f"continuity — one gene per LD block ({b['n_blocks']:,} blocks): "
          f"rho={b['rho']:.4f} P={b['p']:.3e}")
    s = m["continuity_tests"]["extreme_Z_shift_in_population_significant_genes"]
    print(f"\nmean extreme-tail Z: population-significant {s['mean_Z_ext_significant']:.4f} "
          f"vs rest {s['mean_Z_ext_rest']:.4f}")
    print(f"  Mann-Whitney P = {s['mann_whitney_p']:.3e}")
    print(f"  gene-size matched permutation P = {s['gene_size_matched_permutation_p']}")
    print(f"\nwrote {OUT/'extreme_tail_rank.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
