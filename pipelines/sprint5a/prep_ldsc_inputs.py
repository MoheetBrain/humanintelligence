#!/usr/bin/env python3
"""Standardise cognition summary statistics for GenomicSEM/LDSC/LAVA: columns SNP A1 A2 Z N P (A1 = effect allele;
Z oriented so that positive = higher/better cognition). Outputs gzipped TSVs under data/interim/sprint5a/ldsc/inputs/.
Traits: DAVIES (g), GENC_TMA (executive function; trail-making TIME -> sign flipped), GENLANG_PIQ (performance IQ),
ZABANEH_XIQ (extreme IQ case-control; Z = sign(ln OR) x probit(P/2) because the file's chrX SEs are mis-scaled; N_eff = 4/(1/Nca + 1/Nco)), UKB_FI4 (positional arithmetic item),
HOWE_POP / HOWE_WF (only when --howe is passed, after the frozen Gate A has finished)."""
import argparse
import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

R = Path(__file__).resolve().parents[2]
OUT = R / "data/interim/sprint5a/ldsc/inputs"
OUT.mkdir(parents=True, exist_ok=True)
DAV = Path("data/external/x01/inputs/davies2018_open_complete.txt")


def write(name, df):
    df = df.dropna(subset=["SNP", "A1", "A2", "Z", "N"])
    df = df[df.SNP.astype(str).str.startswith("rs")].drop_duplicates("SNP", keep=False)
    df["A1"], df["A2"] = df.A1.str.upper(), df.A2.str.upper()
    df[["SNP", "A1", "A2", "Z", "N", "P"]].to_csv(OUT / f"{name}.tsv.gz", sep="\t", index=False, compression="gzip")
    print(name, len(df), f"mean chi2 {np.mean(df.Z ** 2):.3f}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--howe", action="store_true")
    a = ap.parse_args()
    if not a.howe:
        d = pd.read_csv(DAV, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore", "P-value"])
        write("DAVIES", pd.DataFrame({"SNP": d.Markername, "A1": d.Effect_allele, "A2": d.Other_allele, "Z": d.Zscore,
                                      "N": 282014, "P": d["P-value"]}))
        t = pd.read_csv(R / "data/interim/sprint4/genc/tma_gwas_gc.txt", sep="\t", usecols=["SNP", "A1", "A2", "BETA", "SE", "P", "N"])
        write("GENC_TMA", pd.DataFrame({"SNP": t.SNP, "A1": t.A1, "A2": t.A2, "Z": -t.BETA / t.SE, "N": t.N, "P": t.P}))
        g = pd.read_csv(R / "data/interim/sprint5/genlang/GCST90104472_buildGRCh37.tsv", sep="\t")
        write("GENLANG_PIQ", pd.DataFrame({"SNP": g.variant_id, "A1": g.effect_allele, "A2": g.other_allele,
                                           "Z": g.beta / g.standard_error, "N": g.N, "P": g.p_value}))
        z = pd.read_csv(R / "data/interim/sumstats/GCST005626_zabaneh_extremeIQ_b37.tsv.gz", sep="\t")
        write("ZABANEH_XIQ", pd.DataFrame({"SNP": z.variant_id, "A1": z.effect_allele, "A2": z.other_allele,
                                           "Z": np.sign(np.log(z.odds_ratio)) * stats.norm.isf(z.p_value.clip(1e-300, 1) / 2),
                                           "N": 4 / (1 / 1238 + 1 / 8172),
                                           "P": z.p_value}))
        f = pd.read_csv(R / "data/interim/sumstats/GCST90042729_FI4_positional_arithmetic.tsv.gz", sep="\t",
                        usecols=["variant_id", "effect_allele", "other_allele", "N", "beta", "standard_error", "p_value"])
        write("UKB_FI4", pd.DataFrame({"SNP": f.variant_id, "A1": f.effect_allele, "A2": f.other_allele,
                                       "Z": f.beta / f.standard_error, "N": f.N, "P": f.p_value}))
    else:
        sys.path.insert(0, str(R / "pipelines/sprint4"))
        import gate_a_within_family as G
        for tag, gid in (("HOWE_POP", "ieu-b-4838"), ("HOWE_WF", "ieu-b-4837")):
            df, _ = G.parse_gwas_vcf(G.VCF_DIR / f"{gid}.vcf.gz")
            write(tag, pd.DataFrame({"SNP": df.SNP, "A1": df.EA, "A2": df.OA, "Z": df.BETA / df.SE, "N": df.N, "P": df.P}))


if __name__ == "__main__":
    main()
