#!/usr/bin/env python3
"""Sprint 4, Gate C step 1 — variant-level fine-mapping of the Gate-C loci.

Two sources, kept separate:
  * PRIMARY: the Open Targets GWAS credible sets already fetched in Sprint 3 (study-first; SuSiE-inf on
    each GWAS with in-sample-matched LD by Open Targets) — re-read, not recomputed;
  * SENSITIVITY (frozen settings): susieR::susie_rss on Davies 2018 z (n=282,014), window lead +/-500 kb,
    LD from 1000 Genomes EUR (503 people), L=10, coverage 0.95, min_abs_corr 0.5,
    estimate_residual_variance=FALSE; LD-mismatch diagnostics estimate_s_rss (flag s>0.2) and
    kriging_rss outliers (logLR>2 & |z|>2).
Out-of-sample LD with N=282k is exactly the situation in which SuSiE-RSS can produce spurious extra
signals, so the diagnostics are reported beside every credible set and the OT sets stay primary.
The lead SNP or nearest gene is never equated with the causal gene: this step outputs variants only.

Output: reports/sprint4/locus_finemapping.parquet (+ data/sprint4/finemap_diagnostics.json)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

WIN = 500_000
R_SCRIPT = r'''
suppressMessages(library(susieR))
args <- commandArgs(trailingOnly = TRUE)
d <- args[1]
z <- scan(file.path(d, "z.txt"), quiet = TRUE)
p <- length(z)
R <- matrix(readBin(file.path(d, "R.bin"), "double", n = p * p), p, p)
n <- as.numeric(args[2])
s <- tryCatch(estimate_s_rss(z, R, n = n), error = function(e) NA)
kr <- tryCatch(kriging_rss(z, R, n = n)$conditional_dist, error = function(e) NULL)
nout <- if (is.null(kr)) NA else sum(kr$logLR > 2 & abs(kr$z) > 2)
fit <- tryCatch(susie_rss(z = z, R = R, n = n, L = 10, coverage = 0.95, min_abs_corr = 0.5,
                          estimate_residual_variance = FALSE, max_iter = 1000),
                error = function(e) e)
if (inherits(fit, "error")) {
  writeLines(paste0('{"error": "', gsub('"', "'", conditionMessage(fit)), '"}'), file.path(d, "fit.json"))
} else {
  cs <- fit$sets$cs
  pur <- fit$sets$purity
  out <- list(pip = as.numeric(fit$pip), s = s, kriging_outliers = nout, converged = fit$converged,
              cs = if (is.null(cs)) list() else lapply(names(cs), function(k) list(name = k, idx = as.integer(cs[[k]]),
                    min_abs_corr = if (is.null(pur)) NA else pur[k, "min.abs.corr"])))
  writeLines(jsonlite::toJSON(out, auto_unbox = TRUE, digits = 8, na = "null"), file.path(d, "fit.json"))
  lbf <- fit$lbf_variable
  write.table(lbf, file.path(d, "lbf.tsv"), sep = "\t", row.names = FALSE, col.names = FALSE)
}
'''


def locus_inputs(chrom: str, lead_pos: int, davies: pd.DataFrame, bim: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    from bed_reader import open_bed
    b = bim[(bim.chr == chrom) & bim.pos.between(lead_pos - WIN, lead_pos + WIN)]
    m = b.merge(davies, left_on="snp", right_on="Markername", how="inner")
    ea, oa = m.Effect_allele.str.upper(), m.Other_allele.str.upper()
    m["sign"] = np.where((ea == m.a1) & (oa == m.a2), 1, np.where((ea == m.a2) & (oa == m.a1), -1, 0))
    m = m[m.sign != 0].sort_values("bed_index").reset_index(drop=True)
    with open_bed(str(C.BFILE) + ".bed") as bed:
        idx = m.bed_index.to_numpy()
        x = bed.read(index=np.s_[:, idx.min():idx.max() + 1], dtype="float32")[:, idx - idx.min()]
    mu = np.nanmean(x, axis=0)
    x = np.where(np.isnan(x), mu, x)
    maf = np.minimum(mu / 2, 1 - mu / 2)
    keep = maf >= 0.01
    m, x = m[keep].reset_index(drop=True), x[:, keep]
    x = (x - x.mean(axis=0)) / x.std(axis=0)
    r = (x.T @ x) / x.shape[0]
    m["z_a1"] = m.Zscore * m.sign            # z for the bim A1 allele (the allele R is coded in)
    m["maf_1000g"] = maf[keep]
    return m, r.astype(np.float64)


def run_locus(locus: dict, davies: pd.DataFrame, bim: pd.DataFrame, work: Path) -> tuple[pd.DataFrame, dict]:
    d = work / locus["locus_id"]
    d.mkdir(parents=True, exist_ok=True)
    m, r = locus_inputs(locus["chr"], int(locus["lead_pos_grch37"]), davies, bim)
    np.savetxt(d / "z.txt", m.z_a1.to_numpy())
    # SNP order + allele coding travel with the lbf matrix so coloc.susie can pair them with QTL lbfs
    m[["snp", "chr", "pos", "a1", "a2", "z_a1", "maf_1000g"]].to_csv(d / "snps.tsv", sep="\t", index=False)
    r.T.tofile(d / "R.bin")  # column-major for R
    (d / "run.R").write_text(R_SCRIPT)
    proc = subprocess.run([str(C.RSCRIPT), str(d / "run.R"), str(d), str(C.DAVIES_N)],
                          capture_output=True, text=True, timeout=7200)
    fit = json.loads((d / "fit.json").read_text()) if (d / "fit.json").exists() else {"error": proc.stderr[-500:]}
    (d / "R.bin").unlink(missing_ok=True)
    diag = {"locus_id": locus["locus_id"], "n_snps": int(len(m)), "estimate_s_rss": fit.get("s"),
            "ld_mismatch_flag": bool(fit.get("s") is not None and fit.get("s") > 0.2),
            "kriging_outliers": fit.get("kriging_outliers"), "converged": fit.get("converged"),
            "error": fit.get("error"), "n_credible_sets": len(fit.get("cs", []))}
    rows = []
    pip = np.array(fit.get("pip", [np.nan] * len(m)), float)
    for cs in fit.get("cs", []):
        idx = np.atleast_1d(np.array(cs["idx"])) - 1  # auto_unbox turns 1-variant sets into scalars
        for i in idx:
            rows.append({"locus_id": locus["locus_id"], "source": "SuSiE-RSS sensitivity (Davies, 1000G EUR LD)",
                         "credible_set": cs["name"], "cs_min_abs_corr": cs.get("min_abs_corr"),
                         "cs_size": int(len(idx)), "variant": m.snp[i], "chr": locus["chr"], "pos_grch37": int(m.pos[i]),
                         "pip": float(pip[i]), "davies_z": float(m.Zscore[i]), "effect_allele": m.Effect_allele[i].upper(),
                         "ld_mismatch_flag": diag["ld_mismatch_flag"], "estimate_s_rss": diag["estimate_s_rss"]})
    return pd.DataFrame(rows), diag


def ot_sets(loci: list[dict]) -> pd.DataFrame:
    """Open Targets GWAS credible sets from Sprint 3 at each locus (primary source), one row per set.

    A set belongs to a locus when any of its L2G-ranked genes is a Bonferroni gene of the locus on the
    same chromosome (OT positions are GRCh38, so positions are not compared across builds)."""
    path = C.REPO_ROOT / "data" / "gene_tournament" / "gwas_credible_sets_l2g.csv"
    if not path.exists():
        return pd.DataFrame()
    cs = pd.read_csv(path)
    rows = []
    for l in loci:
        genes = {g["symbol"] for g in l["bonferroni_genes"]}
        sub = cs[(cs.chromosome.astype(str) == str(l["chr"])) & cs.gene.isin(genes)]
        for sl, g in cs[cs.study_locus_id.isin(sub.study_locus_id)].groupby("study_locus_id"):
            top = g.sort_values("l2g_score", ascending=False).iloc[0]
            rows.append({"locus_id": l["locus_id"], "source": "Open Targets GWAS credible set (Sprint 3, primary)",
                         "study_id": top.study_id, "trait": top.trait, "method": top.method,
                         "credible_set": sl, "variant": top.lead_rsids, "lead_variant_grch38": top.lead_variant,
                         "pip": top.lead_pip, "lead_consequence": top.lead_consequence,
                         "top_l2g_gene": top.gene, "top_l2g_score": top.l2g_score,
                         "l2g_driver": top.dominant_shap_feature, "positional_driven": top.positional_driven})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loci", default=str(C.DATA / "gate_c_loci.csv"),
                    help="CSV with locus_id (subset of the frozen 159)")
    args = ap.parse_args(argv)
    frozen = C.load_frozen()
    want = set(pd.read_csv(args.loci).locus_id)
    loci = [l for l in frozen["loci"] if l["locus_id"] in want]
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    davies = davies.drop_duplicates("Markername", keep=False)
    bim = pd.read_csv(str(C.BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                      names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
    bim["bed_index"] = np.arange(len(bim))
    frames, diags = [], []
    for l in loci:
        f, d = run_locus(l, davies, bim, C.WORK / "susie")
        frames.append(f)
        diags.append(d)
        print(d, flush=True)
    susie = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    ot = ot_sets(loci)
    out = pd.concat([ot.astype(str) if len(ot) else ot, susie.astype(str) if len(susie) else susie],
                    ignore_index=True)
    C.OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(C.OUT / "locus_finemapping.parquet", index=False)
    (C.DATA / "finemap_diagnostics.json").write_text(json.dumps(
        {"computed_at": C.utc_now(), "settings": frozen["rules"]["gate_c"]["fine_mapping"], "loci": diags},
        indent=1, default=str) + "\n", encoding="utf-8")
    print(f"{len(susie)} SuSiE credible-set variant rows; {len(ot)} OT rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
