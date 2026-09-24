#!/usr/bin/env python3
"""Sprint 5 — Rank A: locus confidence ("how certain is the human cognition association?").

Frozen statistic (research/sprint5/protocol_rules.json, locus_confidence):
  BF = exp(b*zs*zr - (b*zs)^2/2) per independent replication lineage, summed on log10 scale over
  independent lineages only; zr = replication z aligned to the cognition-increasing allele; zs = EB-shrunk
  Davies z (amendment A2: normal scale mixture fitted to every 50th genome-wide Davies SNP); b = 0.122 for G&C
  (fixed in Sprint 4; estimated there on RAW Davies z, so b*zs slightly under-predicts zr: conservative).
Lineages: G&C (UKB-free, trail making TMA, counts); Zabaneh 2018 extreme IQ (sensitivity only: HRS
controls are inside Davies); within-family (NOT_TESTABLE: no JWT).
Unit of ranking = GWAS signal (unique lead SNP); the 159 Sprint-3 LD loci collapse to 152 signals because
several loci share one lead SNP. Rank uncertainty: 2,000 draws zr* ~ N(zr, 1) -> 5th-95th percentile rank.

Output: reports/sprint5/locus_confidence_rank.csv
"""

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
ZAB = C.REPO_ROOT / "data/interim/sumstats/GCST005626_zabaneh_extremeIQ_b37.tsv.gz"
GENLANG = C.REPO_ROOT / "data/interim/sprint5/genlang/GCST90104472_buildGRCh37.tsv"
GENLANG_OVERLAP = C.DATA / "genlang_overlap.json"
PAL = {frozenset("AT"), frozenset("CG")}


def stratum(x: float) -> str:
    if not np.isfinite(x):
        return "NT"
    return "L1" if x >= 1 else "L2" if x >= 0.5 else "L3" if x >= 0 else "L4_DISCORDANT"


def log10bf(b: float, zs: np.ndarray, zr: np.ndarray) -> np.ndarray:
    mu = b * zs
    return (mu * zr - mu ** 2 / 2) / np.log(10)


def main() -> int:
    rules = C.load_rules()["locus_confidence"]
    loci = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv")
    dav = pd.read_csv(DAVIES, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    dav = dav.drop_duplicates("Markername", keep=False)
    z_all = dav.Zscore.to_numpy(float)[::50]
    sig = loci.drop_duplicates("lead_snp").copy()
    sig["labels"] = sig.lead_snp.map(loci.groupby("lead_snp").locus_id.apply(lambda s: ";".join(s)))
    sig["top_gene_labels"] = sig.lead_snp.map(loci.groupby("lead_snp").top_gene.apply(lambda s: ";".join(s)))
    za = sig.davies_z.abs().to_numpy(float)
    sig["davies_abs_z"] = za
    # amendment A2: stable EB scale-mixture shrinkage (the KDE-Tweedie of Sprint 4 was unstable in the tail)
    sig["davies_z_tweedie"] = EB.shrink(z_all, za)
    # --- G&C lineage
    b = 0.122
    zr = np.where(sig.TMA_status == "TESTABLE", sig.TMA_aligned_z, np.nan)
    sig["gc_aligned_z"] = zr
    sig["log10BF_gc"] = log10bf(b, sig.davies_z_tweedie.to_numpy(), zr)
    # --- Zabaneh (sensitivity only)
    zab = pd.read_csv(ZAB, sep="\t", usecols=["variant_id", "effect_allele", "other_allele", "odds_ratio", "standard_error"])
    zab = zab[zab.variant_id.isin(sig.lead_snp)].drop_duplicates("variant_id", keep=False).set_index("variant_id")
    zz = []
    for r in sig.itertuples():
        if r.lead_snp not in zab.index:
            zz.append((np.nan, "ABSENT"))
            continue
        x = zab.loc[r.lead_snp]
        ea, oa = str(x.effect_allele).upper(), str(x.other_allele).upper()
        cog = str(r.cognition_increasing_allele).upper()
        z = np.log(float(x.odds_ratio)) / float(x.standard_error)
        if frozenset({ea, oa}) in PAL:
            zz.append((np.nan, "PALINDROMIC_NO_FREQ"))
        elif cog == ea:
            zz.append((z, "OK"))
        elif cog == oa:
            zz.append((-z, "OK"))
        else:
            zz.append((np.nan, "ALLELE_MISMATCH"))
    sig["zabaneh_aligned_z"], sig["zabaneh_status"] = zip(*zz)
    ok = np.isfinite(sig.zabaneh_aligned_z)
    x, y = sig.davies_z_tweedie[ok].to_numpy(), sig.zabaneh_aligned_z[ok].to_numpy()
    bz = float((x * y).sum() / (x * x).sum())
    sig["log10BF_zabaneh_sensitivity"] = log10bf(bz, sig.davies_z_tweedie.to_numpy(), sig.zabaneh_aligned_z.to_numpy())
    sig["zabaneh_slope_ivw"] = bz
    # --- GenLang performance IQ (Eising 2022; new Sprint-5 lineage). Slope estimated by IVW over ALL testable
    # signals before any locus is inspected (frozen rule); it counts as independent only if the cohort-overlap
    # verdict (data/sprint5/genlang_overlap.json) is INDEPENDENT, otherwise sensitivity only.
    sys.path.insert(0, str(C.REPO_ROOT / "pipelines" / "sprint4"))
    oth = dav.set_index("Markername")
    gl = pd.read_csv(GENLANG, sep="\t", usecols=["variant_id", "effect_allele", "other_allele", "effect_allele_frequency",
                                                  "beta", "standard_error"])
    gl = gl[gl.variant_id.isin(sig.lead_snp)].drop_duplicates("variant_id", keep=False).set_index("variant_id")
    PALS = {frozenset("AT"), frozenset("CG")}
    COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}
    gz = []
    for r in sig.itertuples():
        if r.lead_snp not in gl.index or r.lead_snp not in oth.index:
            gz.append((np.nan, "ABSENT"))
            continue
        x, d = gl.loc[r.lead_snp], oth.loc[r.lead_snp]
        cog = str(r.cognition_increasing_allele).upper()
        e1, o1 = str(d.Effect_allele).upper(), str(d.Other_allele).upper()
        other = o1 if cog == e1 else e1
        ea, oa, eaf = str(x.effect_allele).upper(), str(x.other_allele).upper(), float(x.effect_allele_frequency)
        z = float(x.beta) / float(x.standard_error)
        if frozenset({cog, other}) in PALS and 0.40 <= eaf <= 0.60:
            gz.append((np.nan, "UNRESOLVED_HARMONISATION"))
        elif ea == cog and oa == other:
            gz.append((z, "OK"))
        elif ea == other and oa == cog:
            gz.append((-z, "OK"))
        elif frozenset({cog, other}) not in PALS and COMP.get(ea) == cog and COMP.get(oa) == other:
            gz.append((z, "OK_STRAND_FLIP"))
        elif frozenset({cog, other}) not in PALS and COMP.get(ea) == other and COMP.get(oa) == cog:
            gz.append((-z, "OK_STRAND_FLIP"))
        else:
            gz.append((np.nan, "ALLELE_MISMATCH"))
    sig["genlang_piq_aligned_z"], sig["genlang_status"] = zip(*gz)
    okg = np.isfinite(sig.genlang_piq_aligned_z)
    xg, yg = sig.davies_z_tweedie[okg].to_numpy(), sig.genlang_piq_aligned_z[okg].to_numpy()
    bg = float((xg * yg).sum() / (xg * xg).sum())
    seg = float(1 / np.sqrt((xg * xg).sum()))
    sig["genlang_slope_ivw"] = bg
    sig["genlang_slope_se"] = seg
    sig["log10BF_genlang"] = log10bf(bg, sig.davies_z_tweedie.to_numpy(), sig.genlang_piq_aligned_z.to_numpy())
    verdict = (json.loads(GENLANG_OVERLAP.read_text()).get("verdicts", {}).get("genlang_piq_vs_davies2018", {})
               .get("verdict", "PENDING")) if GENLANG_OVERLAP.exists() else "PENDING"
    sig["genlang_independence_verdict"] = verdict
    genlang_counts = str(verdict).upper().startswith("INDEPENDENT") and bg > 0
    # --- within-family lineage (Sprint 5A only): frozen Gate-A locus output; slope by IVW over all testable
    # loci before any locus is inspected (Sprint-5 rule for a new lineage); counts as replication (Sprint-5 rule)
    wf_counts = False
    sig["wf_aligned_z"], sig["log10BF_wf"], sig["wf_slope_ivw"] = np.nan, np.nan, np.nan
    wff = C.S4_OUT / "within_family_locus_concordance.csv"
    if C.S5A and wff.exists():
        w = pd.read_csv(wff)
        if "wf_aligned_z" in w.columns and (w.status == "TESTABLE").any():
            wz = w[w.status == "TESTABLE"].drop_duplicates("lead_snp").set_index("lead_snp").wf_aligned_z
            sig["wf_aligned_z"] = sig.lead_snp.map(wz)
            okw = np.isfinite(sig.wf_aligned_z)
            xw, yw = sig.davies_z_tweedie[okw].to_numpy(), sig.wf_aligned_z[okw].to_numpy()
            bw = float((xw * yw).sum() / (xw * xw).sum())
            sig["wf_slope_ivw"] = bw
            sig["log10BF_wf"] = log10bf(bw, sig.davies_z_tweedie.to_numpy(), sig.wf_aligned_z.to_numpy())
            wf_counts = bw > 0
            sig["within_family"] = "TESTED (Howe 2022 ieu-b-4837; frozen Sprint-4 Gate A; UKB/GS siblings overlap Davies)"
    # --- independent total (G&C [+ GenLang if INDEPENDENT] [+ within-family in Sprint 5A])
    sig["log10BF_independent"] = (sig.log10BF_gc.fillna(0) + (sig.log10BF_genlang.fillna(0) if genlang_counts else 0)
                                  + (sig.log10BF_wf.fillna(0) if wf_counts else 0))
    has_any = sig.log10BF_gc.notna() | (genlang_counts & okg) | (wf_counts & np.isfinite(sig.wf_aligned_z))
    sig.loc[~has_any, "log10BF_independent"] = np.nan
    sig["independent_lineages_counted"] = "G&C" + (" + GenLang PIQ" if genlang_counts else "") + (" + within-family" if wf_counts else "")
    sig["within_family"] = "NOT_TESTABLE (OPENGWAS_JWT absent; Howe 2022 files absent)"
    sig["locus_stratum"] = sig.log10BF_independent.map(stratum)
    # --- rank + uncertainty
    rng = np.random.default_rng(20260923)
    base = sig.log10BF_independent.to_numpy()
    sig["rank"] = pd.Series(-np.nan_to_num(base, nan=-99)).rank(method="min").to_numpy().astype(int)
    draws = np.empty((2000, len(sig)))
    t = np.isfinite(zr)
    for i in range(2000):
        zs_ = zr + rng.standard_normal(len(zr))
        v = np.where(t, log10bf(b, sig.davies_z_tweedie.to_numpy(), zs_), -99)
        draws[i] = pd.Series(-v).rank(method="min").to_numpy()
    sig["rank_p05"] = np.percentile(draws, 5, axis=0).astype(int)
    sig["rank_p95"] = np.percentile(draws, 95, axis=0).astype(int)
    sig["p_top10"] = (draws <= 10).mean(0)
    sig["p_top20"] = (draws <= 20).mean(0)
    cols = ["rank", "rank_p05", "rank_p95", "p_top10", "p_top20", "lead_snp", "labels", "top_gene_labels", "chr",
            "cognition_increasing_allele", "davies_z", "davies_z_tweedie", "gc_aligned_z", "log10BF_gc",
            "zabaneh_aligned_z", "zabaneh_status", "log10BF_zabaneh_sensitivity", "zabaneh_slope_ivw",
            "genlang_piq_aligned_z", "genlang_status", "log10BF_genlang", "genlang_slope_ivw", "genlang_slope_se",
            "genlang_independence_verdict", *(["wf_aligned_z", "log10BF_wf", "wf_slope_ivw"] if C.S5A else []),
            "independent_lineages_counted", "log10BF_independent", "locus_stratum", "within_family", "gate_b_locus_class", "gate_b_FDR_primary"]
    out = sig[cols].sort_values("rank")
    out.to_csv(C.OUT / "locus_confidence_rank.csv", index=False, float_format="%.4g")
    print(out.locus_stratum.value_counts().to_dict(), "zabaneh slope", round(bz, 4), "n", int(ok.sum()))
    print("GenLang slope", round(bg, 4), "SE", round(seg, 4), "n", int(okg.sum()), "concordant",
          int((sig.genlang_piq_aligned_z[okg] > 0).sum()), "verdict", verdict, "counted", genlang_counts)
    print(out.head(20)[["rank", "rank_p05", "rank_p95", "lead_snp", "top_gene_labels", "gc_aligned_z",
                        "log10BF_gc", "zabaneh_aligned_z", "locus_stratum"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
