#!/usr/bin/env python3
"""Sprint 4, Gate C steps 2–4 — adult-brain QTL colocalisation and direction resolution.

Inputs
  * Gate-C loci and candidate genes: data/sprint4/gate_c_query_genes.csv
  * adult-brain gene-level QTL summary statistics from the eQTL Catalogue (fetch_eqtl_catalogue.py):
    data/interim/sprint4/eqtl/<locus>__<dataset>.parquet, dataset metadata
    data/sprint4/eqtl_catalogue_brain_datasets.csv (adult_status, quant_method)
  * Davies 2018 z (GWAS side); SuSiE-RSS fits from gate_c_finemap.py (lbf + SNP order)
  * Sprint-3 Open Targets colocalisations (compact file) for evidence pooling

Colocalisation (frozen priors p1=p2=1e-4, p12=5e-6; strong PP.H4 >= 0.8):
  * coloc.abf for every (locus, gene-level molecular trait, adult dataset) pair — single-signal;
  * coloc.susie (coloc::coloc.bf_bf) where the QTL side has SuSiE lbfs (eQTL Catalogue) and the GWAS side
    has a SuSiE fit — multi-signal.
Harmonisation: rsID match; QTL beta is for the ALT allele (eQTL Catalogue), re-expressed for the Davies
effect allele; strand flips only for non-palindromic SNPs; palindromic SNPs with MAF > 0.40 dropped.

Direction (frozen rule, unchanged): >= 3 strong gene-level adult-brain eQTL/pQTL colocalisations and
>= 80% polarity-adjusted sign agreement. Evidence is pooled per (gene, QTL dataset): strong if the Sprint-3
OT COLOC h4 >= 0.8 OR our PP.H4 >= 0.8; polarity from our harmonised analysis when available, else OT's
betaRatioSignAverage; a disagreement between the two is reported and the pair counts as disagreeing.
Counting: primary = rows as in Sprint 3; robustness = distinct QTL COHORT units (GTEx tissues share donors).
A gene is DIRECTION_RESOLVED only if both hold; RESOLVED_ON_ROWS_ONLY is reported, never promoted.

Outputs: reports/sprint4/adult_brain_susie_coloc.parquet, reports/sprint4/directionality_resolution.csv
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gene_tournament"))
import common as C  # noqa: E402
import loci_tools as LT  # noqa: E402

EQTL_DIR = C.WORK / "eqtl"
LBF_DIR = C.WORK / "eqtl_lbf"
SUSIE_DIR = C.WORK / "susie"
GENE_LEVEL = {"ge", "microarray"}
R_COLOC = r'''
suppressMessages(library(coloc))
args <- commandArgs(trailingOnly = TRUE)
d <- read.delim(args[1], stringsAsFactors = FALSE)
p1 <- as.numeric(args[3]); p2 <- as.numeric(args[4]); p12 <- as.numeric(args[5])
res <- list()
for (pid in unique(d$pair_id)) {
  x <- d[d$pair_id == pid, ]
  x <- x[is.finite(x$beta1) & is.finite(x$varbeta1) & x$varbeta1 > 0 & is.finite(x$beta2) &
         is.finite(x$varbeta2) & x$varbeta2 > 0 & x$maf2 > 0 & x$maf2 < 0.5, ]
  if (nrow(x) < 50) next
  r <- tryCatch(suppressWarnings(suppressMessages(coloc.abf(
         dataset1 = list(beta = x$beta1, varbeta = x$varbeta1, type = "quant", N = x$n1[1], MAF = x$maf1, snp = x$snp),
         dataset2 = list(beta = x$beta2, varbeta = x$varbeta2, type = "quant", N = x$n2[1], MAF = x$maf2, snp = x$snp),
         p1 = p1, p2 = p2, p12 = p12))), error = function(e) NULL)
  if (is.null(r)) next
  s <- r$summary
  top <- r$results[which.max(r$results$SNP.PP.H4), ]
  w <- r$results$SNP.PP.H4
  sgn <- sign(x$beta2[match(r$results$snp, x$snp)] / x$beta1[match(r$results$snp, x$snp)])
  res[[pid]] <- data.frame(pair_id = pid, nsnps = s[["nsnps"]], PP.H0 = s[["PP.H0.abf"]], PP.H1 = s[["PP.H1.abf"]],
                           PP.H2 = s[["PP.H2.abf"]], PP.H3 = s[["PP.H3.abf"]], PP.H4 = s[["PP.H4.abf"]],
                           top_snp = top$snp, top_snp_pp_h4 = top$SNP.PP.H4,
                           weighted_sign_ratio = sum(w * sgn, na.rm = TRUE) / sum(w[!is.na(sgn)]))
}
out <- if (length(res)) do.call(rbind, res) else data.frame()
write.table(out, args[2], sep = "\t", row.names = FALSE, quote = FALSE)
'''


R_BFBF = r'''
suppressMessages(library(coloc))
args <- commandArgs(trailingOnly = TRUE)
d1 <- read.delim(args[1], check.names = FALSE); d2 <- read.delim(args[2], check.names = FALSE)
p1 <- as.numeric(args[4]); p2 <- as.numeric(args[5]); p12 <- as.numeric(args[6])
res <- list()
g <- as.matrix(d1[, -1, drop = FALSE]); rownames(g) <- d1[[1]]
for (pid in unique(d2$pair_id)) {
  x <- d2[d2$pair_id == pid, ]
  q <- as.matrix(x[, -(1:2), drop = FALSE]); rownames(q) <- x$component
  common <- intersect(colnames(g), colnames(q))
  if (length(common) < 50) next
  r <- tryCatch(suppressWarnings(suppressMessages(coloc.bf_bf(g[, common, drop = FALSE], q[, common, drop = FALSE],
                p1 = p1, p2 = p2, p12 = p12))), error = function(e) NULL)
  if (is.null(r) || is.null(r$summary)) next
  s <- as.data.frame(r$summary)
  s$pair_id <- pid
  res[[pid]] <- s[, c("pair_id", "nsnps", "hit1", "hit2", "PP.H0.abf", "PP.H1.abf", "PP.H2.abf", "PP.H3.abf", "PP.H4.abf", "idx1", "idx2")]
}
out <- if (length(res)) do.call(rbind, res) else data.frame()
write.table(out, args[3], sep = "\t", row.names = FALSE, quote = FALSE)
'''


def run_coloc_susie(frozen: dict, davies: pd.DataFrame) -> pd.DataFrame:
    """coloc.susie via coloc.bf_bf: GWAS SuSiE credible-set components x QTL SuSiE credible-set components."""
    pri = frozen["rules"]["gate_c"]["coloc"]["priors"]
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    meta = pd.read_csv(C.DATA / "eqtl_catalogue_brain_datasets.csv")
    adult = set(meta[(meta.adult_status == "ADULT") & meta.quant_method.isin(GENE_LEVEL)].dataset_id)
    work = C.WORK / "coloc_susie"
    work.mkdir(parents=True, exist_ok=True)
    (work / "bfbf.R").write_text(R_BFBF)
    dz = davies.set_index("Markername")
    out = []
    for locus_id, lq in q.groupby("locus_id"):
        d = SUSIE_DIR / locus_id
        if not (d / "lbf.tsv").exists() or not (d / "fit.json").exists():
            continue
        fit = json.loads((d / "fit.json").read_text())
        comps = [int(str(c["name"]).lstrip("L")) for c in fit.get("cs", [])]
        if not comps:
            continue
        snps = pd.read_csv(d / "snps.tsv", sep="\t")
        lbf = pd.read_csv(d / "lbf.tsv", sep="\t", header=None)
        g = lbf.iloc[[k - 1 for k in comps]].copy()
        g.columns = snps.snp.tolist()
        g = g.loc[:, ~g.columns.duplicated()]
        g.insert(0, "component", [f"L{k}" for k in comps])
        genes = set(lq.ensembl_gene_id)
        qrows = []
        for ds in adult:
            cs_f, lbf_f = LBF_DIR / f"{locus_id}__{ds}.credible_sets.parquet", LBF_DIR / f"{locus_id}__{ds}.parquet"
            ss_f = EQTL_DIR / f"{locus_id}__{ds}.parquet"
            if not (cs_f.exists() and lbf_f.exists() and ss_f.exists()):
                continue
            cs = pd.read_parquet(cs_f)
            cs = cs[cs.gene_id.astype(str).str.split(".").str[0].isin(genes)]
            if cs.empty:
                continue
            lb = pd.read_parquet(lbf_f)
            v2r = pd.read_parquet(ss_f, columns=["variant", "rsid"]).dropna().drop_duplicates("variant")
            v2r = dict(zip(v2r.variant, v2r.rsid))
            for trait, ct in cs.groupby("molecular_trait_id"):
                ks = sorted({int(str(c).rsplit("_L", 1)[1]) for c in ct.cs_id})
                lt = lb[lb.molecular_trait_id == trait].copy()
                lt["rsid"] = lt.variant.map(v2r)
                lt = lt.dropna(subset=["rsid"]).drop_duplicates("rsid")
                if lt.empty:
                    continue
                for k in ks:
                    row = lt.set_index("rsid")[f"lbf_variable{k}"]
                    qrows.append(pd.DataFrame([row.values], columns=row.index).assign(
                        pair_id=f"{locus_id}|{ds}|{trait}", component=f"L{k}"))
        if not qrows:
            continue
        qq = pd.concat(qrows, ignore_index=True)
        cols = ["pair_id", "component"] + [c for c in qq.columns if c not in ("pair_id", "component")]
        qq = qq[cols].fillna(0.0)   # variants absent from a QTL region carry lbf 0 (no evidence)
        f1, f2, fo = work / f"{locus_id}.gwas.tsv", work / f"{locus_id}.qtl.tsv", work / f"{locus_id}.out.tsv"
        g.to_csv(f1, sep="\t", index=False)
        qq.to_csv(f2, sep="\t", index=False)
        subprocess.run([str(C.RSCRIPT), str(work / "bfbf.R"), str(f1), str(f2), str(fo), str(pri["p1"]),
                        str(pri["p2"]), str(pri["p12"])], capture_output=True, text=True, timeout=7200, check=False)
        if not fo.exists() or fo.stat().st_size == 0:
            continue
        r = pd.read_csv(fo, sep="\t")
        for row in r.to_dict("records"):
            _, ds, trait = row["pair_id"].split("|", 2)
            ss = pd.read_parquet(EQTL_DIR / f"{locus_id}__{ds}.parquet")
            ss = ss[ss.molecular_trait_id == trait]
            h = harmonise(ss, davies)
            top = h[h.rsid == row["hit1"]]
            qtl_cog = np.nan
            if len(top):
                t0 = top.iloc[0]
                qtl_cog = float(t0.beta2) * (1 if float(t0.Zscore) > 0 else -1)
            out.append({"locus_id": locus_id, "dataset_id": ds, "molecular_trait_id": trait,
                        "gene_id": str(ss.gene_id.iloc[0]).split(".")[0] if len(ss) else trait,
                        "method": "coloc.susie (coloc.bf_bf; multi-signal)", "nsnps": row["nsnps"],
                        "PP.H0": row["PP.H0.abf"], "PP.H1": row["PP.H1.abf"], "PP.H2": row["PP.H2.abf"],
                        "PP.H3": row["PP.H3.abf"], "PP.H4": row["PP.H4.abf"], "top_snp": row["hit1"],
                        "qtl_lead_snp": row["hit2"], "gwas_component": f"L{row['idx1']}",
                        "qtl_component": f"L{row['idx2']}",
                        "qtl_effect_of_cognition_allele_at_top": qtl_cog,
                        "weighted_sign_ratio_qtl_over_gwas": np.sign(qtl_cog) if pd.notna(qtl_cog) else np.nan})
    return pd.DataFrame(out)


def harmonise(qtl: pd.DataFrame, davies: pd.DataFrame) -> pd.DataFrame:
    m = qtl.merge(davies, left_on="rsid", right_on="Markername", how="inner")
    ea, oa = m.Effect_allele.str.upper(), m.Other_allele.str.upper()
    alt, ref = m.alt.astype(str).str.upper(), m.ref.astype(str).str.upper()
    comp = {"A": "T", "T": "A", "C": "G", "G": "C"}
    pal = [frozenset({a, b}) in LT.PALINDROMIC for a, b in zip(ea, oa)]
    s = np.where((alt == ea) & (ref == oa), 1, np.where((alt == oa) & (ref == ea), -1, 0))
    flip_alt = alt.map(comp)
    flip_ref = ref.map(comp)
    s = np.where((s == 0) & ~np.array(pal) & (flip_alt == ea) & (flip_ref == oa), 1, s)
    s = np.where((s == 0) & ~np.array(pal) & (flip_alt == oa) & (flip_ref == ea), -1, s)
    m["s"] = s
    m = m[(m.s != 0) & ~(np.array(pal) & (m.maf > 0.40))].copy()
    m["beta2"] = m.beta * m.s                        # QTL effect of the Davies EFFECT allele
    m["varbeta2"] = m.se ** 2
    return m


def gwas_beta(z: np.ndarray, maf: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Standardised effect and variance from z (sdY = 1): beta = z / sqrt(2p(1-p)(n + z^2))."""
    denom = np.sqrt(2 * maf * (1 - maf) * (n + z ** 2))
    b = z / denom
    # var(beta) = 1 / (2p(1-p)(n + z^2)) — written without dividing by z so z = 0 stays finite
    return b, 1.0 / denom ** 2


def run_coloc(frozen: dict) -> pd.DataFrame:
    pri = frozen["rules"]["gate_c"]["coloc"]["priors"]
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    meta = pd.read_csv(C.DATA / "eqtl_catalogue_brain_datasets.csv")
    adult = meta[(meta.adult_status == "ADULT") & meta.quant_method.isin(GENE_LEVEL)]
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    davies = davies.drop_duplicates("Markername", keep=False)
    work = C.WORK / "coloc"
    work.mkdir(parents=True, exist_ok=True)
    (work / "coloc.R").write_text(R_COLOC)
    results = []
    for locus_id, lq in q.groupby("locus_id"):
        genes = set(lq.ensembl_gene_id)
        cog = lq.cognition_increasing_allele.iloc[0]
        frames = []
        for ds in adult.dataset_id:
            f = EQTL_DIR / f"{locus_id}__{ds}.parquet"
            if not f.exists():
                continue
            e = pd.read_parquet(f)
            e = e[e.gene_id.str.split(".").str[0].isin(genes)]
            if e.empty:
                continue
            h = harmonise(e, davies)
            h["n2"] = (h.an.max() / 2) if "an" in h and h.an.notna().any() else np.nan
            h["maf1"] = h.maf
            b1, v1 = gwas_beta(h.Zscore.to_numpy(float), h.maf.clip(1e-4, 0.5).to_numpy(float), C.DAVIES_N)
            h["beta1"], h["varbeta1"], h["n1"] = b1, v1, C.DAVIES_N
            h["maf2"] = h.maf
            h["pair_id"] = locus_id + "|" + ds + "|" + h.molecular_trait_id.astype(str)
            frames.append(h[["pair_id", "rsid", "beta1", "varbeta1", "maf1", "n1", "beta2", "varbeta2", "maf2", "n2",
                             "Zscore", "Effect_allele", "Other_allele", "gene_id"]].rename(columns={"rsid": "snp"}))
        if not frames:
            continue
        long = pd.concat(frames, ignore_index=True).drop_duplicates(["pair_id", "snp"])
        inp, outp = work / f"{locus_id}.in.tsv", work / f"{locus_id}.out.tsv"
        long.to_csv(inp, sep="\t", index=False)
        subprocess.run([str(C.RSCRIPT), str(work / "coloc.R"), str(inp), str(outp), str(pri["p1"]), str(pri["p2"]),
                        str(pri["p12"])], capture_output=True, text=True, timeout=7200, check=False)
        if not outp.exists() or outp.stat().st_size == 0:
            continue
        r = pd.read_csv(outp, sep="\t")
        if r.empty:
            continue
        top = long.set_index(["pair_id", "snp"])
        gene_of = long.drop_duplicates("pair_id").set_index("pair_id").gene_id
        for row in r.to_dict("records"):
            key = (row["pair_id"], row["top_snp"])
            qtl_cog = np.nan
            if key in top.index:
                t = top.loc[key]
                ea = str(t.Effect_allele).upper()
                # the cognition-increasing allele AT THE TOP SHARED VARIANT (Davies z sign), then the QTL
                # effect of that allele: > 0 means the cognition-increasing allele raises expression
                cog_is_ea = float(t.Zscore) > 0
                qtl_cog = float(t.beta2) * (1 if cog_is_ea else -1)
            _, ds, trait = row["pair_id"].split("|", 2)
            results.append({"locus_id": locus_id, "dataset_id": ds, "molecular_trait_id": trait,
                            "gene_id": str(gene_of[row["pair_id"]]).split(".")[0],
                            "method": "coloc.abf (single-signal)", "nsnps": row["nsnps"],
                            **{k: row[k] for k in ("PP.H0", "PP.H1", "PP.H2", "PP.H3", "PP.H4")},
                            "top_snp": row["top_snp"], "top_snp_pp_h4": row["top_snp_pp_h4"],
                            "qtl_effect_of_cognition_allele_at_top": qtl_cog,
                            "weighted_sign_ratio_qtl_over_gwas": row["weighted_sign_ratio"],
                            "cognition_increasing_allele_lead": cog})
    return pd.DataFrame(results)


def main() -> int:
    frozen = C.load_frozen()
    prev = C.OUT / "adult_brain_susie_coloc.parquet"
    if "--susie-only" in sys.argv and prev.exists():
        res = pd.read_parquet(prev)
        res = res[res.method.str.startswith("coloc.abf")]
    else:
        res = run_coloc(frozen)
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    davies = davies.drop_duplicates("Markername", keep=False)
    sus = run_coloc_susie(frozen, davies)
    res = pd.concat([res, sus], ignore_index=True)
    C.OUT.mkdir(parents=True, exist_ok=True)
    res.to_parquet(C.OUT / "adult_brain_susie_coloc.parquet", index=False)
    print(len(res), "coloc rows;", int((res.get("PP.H4", pd.Series(dtype=float)) >= 0.8).sum()), "strong")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
