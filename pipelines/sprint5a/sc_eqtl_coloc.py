#!/usr/bin/env python3
"""Sprint 5A Goal A — cell-type colocalisation of Davies 2018 general cognition with open single-nucleus
brain eQTL summary statistics at the 36 Gate-C loci.

QTL sources (fetched by fetch_sc_eqtl.py; both CC-BY-4.0 on Zenodo, no login):
  * BRYOIS2022 — Bryois et al. 2022 Nat Neurosci: 8 cell types (+ 'pb' tissue-like pseudo-bulk) from
    192 donors (published N; preprint 196) — ROSMAP (Mathys 2019, Zhou 2020, Cain/Columbia) + Roche_MS +
    Roche_AD; fastQTL nominal p + beta; beta per copy of snp_pos 'effect_allele'; MAF > 5%.
    SE is not distributed; it is recovered as |beta| / qnorm(p/2, lower=FALSE) (exact for a Wald test).
  * SINGLEBRAIN — mmQTL meta-analysis of Fujita (ROSMAP), Mathys (ROSMAP), Gabitto (SEA-AD) and Bryois
    (Roche) snRNA-seq eQTLs: 983 samples / 757 unique donors, 7 major cell types; fixed-effect beta/sd
    per copy of 'Allele' (= alt); hg38 + rsID. It CONTAINS Bryois donors, so BRYOIS2022 and SINGLEBRAIN
    are NOT independent replications; both overlap the ROSMAP bulk eQTLs used in Sprint 4.

Conventions reused from pipelines/sprint4/gate_c_coloc.py: harmonise() (rsID join; QTL beta re-expressed
for the Davies EFFECT allele; strand flips only for non-palindromic SNPs; palindromic SNPs with MAF > 0.40
dropped), gwas_beta() (Davies z -> standardised beta, N = 282,014), R_COLOC (coloc.abf, >= 50 SNPs) and
R_BFBF (coloc.bf_bf). Frozen priors p1 = p2 = 1e-4, p12 = 5e-6; strong = PP.H4 >= 0.8 (moderate >= 0.5).

Window: GWAS lead +/- 500 kb (GRCh37 for Davies/1000G, GRCh38 from the Sprint-4 eQTL Catalogue fetch for
SingleBrain). Genes: every gene in the QTL files with a TSS inside the GRCh38 window (Ensembl REST
GRCh38 lookup) plus every Gate-C query gene for the locus.

coloc.susie: GWAS side = Sprint-4 SuSiE-RSS fits (data/interim/sprint4/susie/<locus>); QTL side =
susieR::susie_rss on the sc-eQTL z (aligned to the 1000G A1 allele) with 1000G EUR LD built exactly as in
gate_c_finemap.py (MAF >= 1% in 503 EUR), L = 10, coverage 0.95, min_abs_corr 0.5,
estimate_residual_variance = FALSE — run only for gene x cell type pairs whose min eQTL p < 1e-4 in the
window (no SuSiE credible set is expected below that). Direction: QTL effect of the cognition-increasing
allele (Davies effect allele if Zscore > 0) at the top shared SNP.

Outputs: reports/sprint5a/sc_eqtl_coloc.parquet, reports/sprint5a/sc_eqtl_coloc_summary.csv
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
import common as C  # noqa: E402
import gate_c_coloc as GC  # noqa: E402

INTERIM = REPO / "data" / "interim" / "sprint5a"
LONG = INTERIM / "sc_long"
WORK = INTERIM / "sc_coloc"
OUT = REPO / "reports" / "sprint5a"
RAW = REPO / "data" / "raw" / "sprint5a"
S4_PROV = REPO / "data" / "raw" / "sprint4" / "eqtl_catalogue" / "PROVENANCE.json"
WIN = 500_000
BRYOIS_CT = ["Astrocytes", "Endothelial.cells", "Excitatory.neurons", "Inhibitory.neurons", "Microglia",
             "Oligodendrocytes", "OPCs...COPs", "Pericytes", "pb"]
SB_CT = ["Ext", "IN", "Ast", "OD", "OPC", "MG", "End"]
CT_LABEL = {"Astrocytes": "astrocyte", "Endothelial.cells": "endothelial", "Excitatory.neurons": "excitatory_neuron",
            "Inhibitory.neurons": "inhibitory_neuron", "Microglia": "microglia", "Oligodendrocytes": "oligodendrocyte",
            "OPCs...COPs": "OPC", "Pericytes": "pericyte", "pb": "pseudobulk_all_nuclei",
            "Ext": "excitatory_neuron", "IN": "inhibitory_neuron", "Ast": "astrocyte", "OD": "oligodendrocyte",
            "OPC": "OPC", "MG": "microglia", "End": "endothelial"}
N_QTL = {"BRYOIS2022": 192, "SINGLEBRAIN": 757}
SUSIE_P = 1e-4


def loci() -> pd.DataFrame:
    items = json.loads(S4_PROV.read_text())["loci"]["items"]
    rows = []
    for it in items:
        c, rng = it["window_grch38"].split(":")
        a, b = rng.split("-")
        rows.append({"locus_id": it["locus_id"], "chr": str(it["chr"]), "lead_snp": it["lead_snp"],
                     "lead37": int(it["lead_pos_grch37"]), "lead38": int(it["lead_pos_grch38"]),
                     "start38": int(a), "end38": int(b)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------- extraction
def _bryois_one(args):
    ct, chrom, loc_rows, rs_by_locus = args
    f = INTERIM / "bryois" / f"{ct}.{chrom}.gz"
    if not f.exists():
        return ct, chrom, "missing"
    todo = [l for l in loc_rows if not (LONG / f"BRYOIS2022__{ct}__{l}.parquet").exists()]
    if not todo:
        return ct, chrom, "cached"
    allrs = set().union(*[rs_by_locus[l] for l in todo])
    parts = []
    for ch in pd.read_csv(f, sep=" ", header=None, names=["gene", "rsid", "dist", "p", "beta"],
                          dtype={"gene": str, "rsid": str, "dist": np.int64, "p": float, "beta": float},
                          chunksize=4_000_000):
        parts.append(ch[ch.rsid.isin(allrs)])
    d = pd.concat(parts, ignore_index=True)
    for l in todo:
        x = d[d.rsid.isin(rs_by_locus[l])].copy()
        x.to_parquet(LONG / f"BRYOIS2022__{ct}__{l}.parquet", index=False)
    return ct, chrom, f"{len(d)} rows"


def extract_bryois(L: pd.DataFrame, workers: int) -> None:
    LONG.mkdir(parents=True, exist_ok=True)
    sp = pd.read_csv(INTERIM / "bryois" / "snp_pos.txt.gz", sep="\t")
    sp[["c37", "p37"]] = sp.SNP_id_hg19.str.replace("chr", "").str.split(":", expand=True)
    sp[["c38", "p38"]] = sp.SNP_id_hg38.str.replace("chr", "").str.split(":", expand=True)
    sp["p37"] = pd.to_numeric(sp.p37, errors="coerce")   # a few SNPs lack an hg19 (or hg38) position
    sp["p38"] = pd.to_numeric(sp.p38, errors="coerce")
    rs_by_locus = {}
    for l in L.itertuples():
        m = sp[(sp.c37 == l.chr) & sp.p37.between(l.lead37 - WIN, l.lead37 + WIN)]
        rs_by_locus[l.locus_id] = set(m.SNP)
    sp.to_parquet(INTERIM / "bryois_snp_pos.parquet", index=False)
    jobs = []
    for ct in BRYOIS_CT:
        for chrom, g in L.groupby("chr"):
            jobs.append((ct, chrom, list(g.locus_id), {k: rs_by_locus[k] for k in g.locus_id}))
    with cf.ProcessPoolExecutor(workers) as ex:
        for r in ex.map(_bryois_one, jobs):
            print("bryois", *r, flush=True)


def ensembl_grch38(ids: list[str]) -> pd.DataFrame:
    cache = INTERIM / "ensembl_grch38_genes.parquet"
    have = pd.read_parquet(cache) if cache.exists() else pd.DataFrame(columns=["gene_id"])
    need = sorted(set(ids) - set(have.gene_id))
    rows = []
    for i in range(0, len(need), 900):
        body = json.dumps({"ids": need[i:i + 900]}).encode()
        req = urllib.request.Request("https://rest.ensembl.org/lookup/id", data=body,
                                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        for k, v in d.items():
            if v:
                tss = v["start"] if v["strand"] == 1 else v["end"]
                rows.append({"gene_id": k, "symbol": v.get("display_name"), "chr38": str(v["seq_region_name"]),
                             "start38": v["start"], "end38": v["end"], "strand": v["strand"], "tss38": tss,
                             "biotype": v.get("biotype"), "assembly": v.get("assembly_name")})
            else:
                rows.append({"gene_id": k, "symbol": None, "chr38": None, "start38": np.nan, "end38": np.nan,
                             "strand": np.nan, "tss38": np.nan, "biotype": None, "assembly": None})
    if rows:
        have = pd.concat([have, pd.DataFrame(rows)], ignore_index=True)
        have.to_parquet(cache, index=False)
        prov = RAW / "ensembl_grch38_gene_lookup.json"
        prov.write_text(json.dumps({"source": "https://rest.ensembl.org/lookup/id (POST, GRCh38 current release)",
                                    "utc": C.utc_now(), "n_ids_total": int(len(have)),
                                    "use": "gene TSS (strand-aware start) to decide which genes lie in the "
                                           "GRCh38 lead +/- 500 kb window"}, indent=1) + "\n")
    return have


# ------------------------------------------------------------------------------------------ harmonisation
def load_davies() -> pd.DataFrame:
    d = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Chromosome", "Position", "Markername", "Effect_allele",
                                                           "Other_allele", "Zscore"], dtype={"Chromosome": str})
    return d.drop_duplicates("Markername", keep=False)


def qtl_table(source: str, ct: str, locus: str, sp: pd.DataFrame | None, maf1kg: pd.DataFrame) -> pd.DataFrame:
    """Uniform QTL table: gene_id, rsid, alt(=effect allele), ref, beta, se, maf, p."""
    if source == "BRYOIS2022":
        f = LONG / f"BRYOIS2022__{ct}__{locus}.parquet"
        if not f.exists():
            return pd.DataFrame()
        d = pd.read_parquet(f)
        d = d[(d.beta != 0) & (d.p > 0) & (d.p < 1)].copy()
        z = norm.isf(d.p.to_numpy() / 2)
        d["se"] = np.abs(d.beta.to_numpy()) / z
        d["gene_id"] = d.gene.str.rsplit("_", n=1).str[1]
        d["symbol_src"] = d.gene.str.rsplit("_", n=1).str[0]
        s = sp if sp.index.name == "SNP" else sp.set_index("SNP")
        d["alt"] = d.rsid.map(s.effect_allele)
        d["ref"] = d.rsid.map(s.other_allele)
        d["maf"] = d.rsid.map(s.MAF)
        d["pos38"] = d.rsid.map(s.p38)
        d["tss38_from_dist"] = d.pos38 - d.dist
        return d[["gene_id", "symbol_src", "rsid", "alt", "ref", "beta", "se", "maf", "p", "tss38_from_dist"]]
    f = INTERIM / "singlebrain" / f"{ct}__{locus}.tsv"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_csv(f, sep="\t", usecols=["feature", "variant_id", "pos", "ref", "alt", "Allele", "fixed_beta",
                                          "fixed_sd", "Fixed_P"])
    for c in ("fixed_beta", "fixed_sd", "Fixed_P"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d.fixed_sd > 0) & np.isfinite(d.fixed_beta) & d.variant_id.astype(str).str.startswith("rs")].copy()
    if d.empty:
        return pd.DataFrame()
    other = np.where(d.Allele == d.alt, d.ref, np.where(d.Allele == d.ref, d.alt, None))
    d = d.assign(gene_id=d.feature.str.split(".").str[0], rsid=d.variant_id, alt=d.Allele, ref=other,
                 beta=d.fixed_beta, se=d.fixed_sd, p=d.Fixed_P, symbol_src=None, tss38_from_dist=np.nan)
    d = d[d.ref.notna() & (d.alt.str.len() == 1) & (d.ref.str.len() == 1)]
    d["maf"] = d.rsid.map(maf1kg)          # SingleBrain ships no MAF: 1000G EUR MAF (>= 1%) used
    d = d[d.maf.notna()]
    return d[["gene_id", "symbol_src", "rsid", "alt", "ref", "beta", "se", "maf", "p", "tss38_from_dist"]]


# --------------------------------------------------------------------------------------------- SuSiE (QTL)
R_SUSIE_QTL = r'''
suppressMessages(library(susieR))
args <- commandArgs(trailingOnly = TRUE)
d <- args[1]; n <- as.numeric(args[2])
snps <- read.delim(file.path(d, "snps.tsv"))
p <- nrow(snps)
R <- matrix(readBin(file.path(d, "R.bin"), "double", n = p * p), p, p)
z <- read.delim(args[3])          # pair_id, idx (1-based into snps), z_a1
out <- list()
for (pid in unique(z$pair_id)) {
  x <- z[z$pair_id == pid, ]
  idx <- x$idx
  fit <- tryCatch(susie_rss(z = x$z_a1, R = R[idx, idx, drop = FALSE], n = n, L = 10, coverage = 0.95,
                            min_abs_corr = 0.5, estimate_residual_variance = FALSE, max_iter = 1000),
                  error = function(e) NULL)
  if (is.null(fit) || is.null(fit$sets$cs)) next
  ks <- as.integer(sub("L", "", names(fit$sets$cs)))
  lbf <- fit$lbf_variable[ks, , drop = FALSE]
  colnames(lbf) <- snps$snp[idx]
  out[[pid]] <- data.frame(pair_id = pid, component = paste0("L", ks), lbf, check.names = FALSE)
}
if (length(out)) {
  allc <- unique(unlist(lapply(out, colnames)))
  out <- lapply(out, function(o) { m <- setdiff(allc, colnames(o)); for (k in m) o[[k]] <- 0; o[, allc] })
  write.table(do.call(rbind, out), args[4], sep = "\t", row.names = FALSE, quote = FALSE)
} else writeLines("", args[4])
'''


def build_ld(locus: str, chrom: str, lead37: int, davies: pd.DataFrame, bim: pd.DataFrame) -> Path:
    """1000G EUR LD for the GWAS SuSiE SNP set (same code path as gate_c_finemap.locus_inputs)."""
    d = WORK / "ld" / locus
    d.mkdir(parents=True, exist_ok=True)
    if (d / "R.bin").exists() and (d / "snps.tsv").exists():
        return d
    sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
    import gate_c_finemap as FM  # noqa: E402
    m, r = FM.locus_inputs(chrom, lead37, davies, bim)
    m[["snp", "chr", "pos", "a1", "a2", "z_a1", "maf_1000g", "Effect_allele"]].to_csv(d / "snps.tsv", sep="\t",
                                                                                     index=False)
    r.T.tofile(d / "R.bin")
    return d


# ------------------------------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--no-susie", action="store_true")
    ap.add_argument("--summary-only", action="store_true",
                    help="re-derive gene symbols + summary from the existing parquet (no recomputation)")
    a = ap.parse_args(argv)
    frozen = C.load_frozen()
    pri = frozen["rules"]["gate_c"]["coloc"]["priors"]
    strong = frozen["rules"]["gate_c"]["coloc"]["strong_pp_h4"]
    if a.summary_only:
        res = pd.read_parquet(OUT / "sc_eqtl_coloc.parquet")
        q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
        ens = symbol_table(pd.read_parquet(INTERIM / "ensembl_grch38_genes.parquet"), q)
        res["gene"] = res.gene_id.map(ens.symbol)
        res.to_parquet(OUT / "sc_eqtl_coloc.parquet", index=False)
        summarise(res, q, ens, pd.read_csv(WORK / "tested_pairs.csv"), strong)
        return 0
    L = loci()
    if a.extract:
        extract_bryois(L, a.workers)
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (WORK / "coloc.R").write_text(GC.R_COLOC)
    (WORK / "bfbf.R").write_text(GC.R_BFBF)
    (WORK / "susie_qtl.R").write_text(R_SUSIE_QTL)
    davies = load_davies()
    dz = davies.set_index("Markername")
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    sp = pd.read_parquet(INTERIM / "bryois_snp_pos.parquet", columns=["SNP", "effect_allele", "other_allele", "MAF", "p38"])
    sp = sp.drop_duplicates("SNP").set_index("SNP")
    bim = pd.read_csv(str(C.BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                      names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
    bim["bed_index"] = np.arange(len(bim))

    # ---- assemble QTL tables and the gene universe
    tables = {}
    for l in L.itertuples():
        ldd = build_ld(l.locus_id, l.chr, l.lead37, davies, bim)
        snps = pd.read_csv(ldd / "snps.tsv", sep="\t")
        maf1kg = snps.set_index("snp").maf_1000g
        for src, cts in (("BRYOIS2022", BRYOIS_CT), ("SINGLEBRAIN", SB_CT)):
            for ct in cts:
                t = qtl_table(src, ct, l.locus_id, sp, maf1kg)
                if len(t):
                    tables[(l.locus_id, src, ct)] = t
    all_genes = sorted({g for t in tables.values() for g in t.gene_id.unique()} | set(q.ensembl_gene_id))
    ens = symbol_table(ensembl_grch38(all_genes), q)

    records, long_frames, susie_z = [], [], []
    tested = []
    for l in L.itertuples():
        qg = set(q[q.locus_id == l.locus_id].ensembl_gene_id)
        ldd = WORK / "ld" / l.locus_id
        snps = pd.read_csv(ldd / "snps.tsv", sep="\t")
        snps["idx"] = np.arange(1, len(snps) + 1)
        snps["s_a1"] = np.where(snps.Effect_allele.str.upper() == snps.a1, 1, -1)
        # Davies rows of this locus window only (harmonise() merges on rsID; a genome-wide merge per
        # table was the bottleneck). Same rows as filtering after the merge.
        dav_loc = davies[(davies.Chromosome.astype(str) == l.chr) &
                         davies.Position.between(l.lead37 - WIN, l.lead37 + WIN)]
        for (loc, src, ct), t in tables.items():
            if loc != l.locus_id:
                continue
            tss = t.gene_id.map(ens.tss38)
            chr_ok = t.gene_id.map(ens.chr38).astype(str) == l.chr
            inwin = chr_ok & tss.between(l.start38, l.end38)
            t = t[inwin | t.gene_id.isin(qg)]
            if t.empty:
                continue
            h = GC.harmonise(t, dav_loc)
            # restrict to the GWAS window (GRCh37 +/- 500 kb) used by the SuSiE fit
            h = h[(h.Chromosome.astype(str) == l.chr) & h.Position.between(l.lead37 - WIN, l.lead37 + WIN)]
            if h.empty:
                continue
            b1, v1 = GC.gwas_beta(h.Zscore.to_numpy(float), h.maf.clip(1e-4, 0.5).to_numpy(float), C.DAVIES_N)
            h = h.assign(beta1=b1, varbeta1=v1, n1=C.DAVIES_N, maf1=h.maf, maf2=h.maf, n2=N_QTL[src],
                         pair_id=l.locus_id + "|" + src + "|" + ct + "|" + h.gene_id)
            h = h.drop_duplicates(["pair_id", "rsid"])
            long_frames.append(h[["pair_id", "rsid", "beta1", "varbeta1", "maf1", "n1", "beta2", "varbeta2", "maf2",
                                  "n2", "Zscore", "Effect_allele", "Other_allele", "gene_id", "p"]]
                               .rename(columns={"rsid": "snp"}))
            for gid, g in h.groupby("gene_id"):
                tested.append({"locus_id": l.locus_id, "source": src, "cell_type_raw": ct, "gene_id": gid,
                               "n_snps_harmonised": len(g), "min_qtl_p": float(g.p.min())})
                if a.no_susie or g.p.min() >= SUSIE_P:
                    continue
                m = g.merge(snps[["snp", "idx", "s_a1"]], left_on="rsid", right_on="snp")
                if len(m) < 50:
                    continue
                susie_z.append(pd.DataFrame({"locus_id": l.locus_id, "pair_id": m.pair_id.iloc[0], "idx": m.idx,
                                             "z_a1": (m.beta2 / np.sqrt(m.varbeta2)) * m.s_a1,
                                             "n": N_QTL[src]}))
    long = pd.concat(long_frames, ignore_index=True)
    tested = pd.DataFrame(tested)
    tested.to_csv(WORK / "tested_pairs.csv", index=False)
    print(len(tested), "gene x cell-type x locus pairs harmonised", flush=True)

    # ---- coloc.abf per locus
    for loc, lg in long.assign(locus=long.pair_id.str.split("|").str[0]).groupby("locus"):
        inp, outp = WORK / f"{loc}.in.tsv", WORK / f"{loc}.out.tsv"
        lg.drop(columns="locus").to_csv(inp, sep="\t", index=False)
        subprocess.run([str(C.RSCRIPT), str(WORK / "coloc.R"), str(inp), str(outp), str(pri["p1"]), str(pri["p2"]),
                        str(pri["p12"])], capture_output=True, text=True, timeout=7200, check=False)
        if not outp.exists() or outp.stat().st_size == 0:
            continue
        r = pd.read_csv(outp, sep="\t")
        if r.empty:
            continue
        top = lg.set_index(["pair_id", "snp"])
        for row in r.to_dict("records"):
            key = (row["pair_id"], row["top_snp"])
            qtl_cog = np.nan
            if key in top.index:
                t0 = top.loc[key]
                qtl_cog = float(t0.beta2) * (1 if float(t0.Zscore) > 0 else -1)
            _, src, ct, gid = row["pair_id"].split("|")
            records.append({"locus_id": loc, "source": src, "cell_type_raw": ct, "cell_type": CT_LABEL[ct],
                            "gene_id": gid, "method": "coloc.abf (single-signal)", "nsnps": row["nsnps"],
                            **{k: row[k] for k in ("PP.H0", "PP.H1", "PP.H2", "PP.H3", "PP.H4")},
                            "top_snp": row["top_snp"], "top_snp_pp_h4": row["top_snp_pp_h4"],
                            "qtl_effect_of_cognition_allele_at_top": qtl_cog,
                            "weighted_sign_ratio_qtl_over_gwas": row["weighted_sign_ratio"]})
        print("coloc.abf", loc, len(r), flush=True)

    # ---- coloc.susie
    if susie_z:
        sz = pd.concat(susie_z, ignore_index=True)
        for loc, zz in sz.groupby("locus_id"):
            gd = C.WORK / "susie" / loc
            if not (gd / "lbf.tsv").exists():
                continue
            fit = json.loads((gd / "fit.json").read_text())
            comps = [int(str(c["name"]).lstrip("L")) for c in fit.get("cs", [])]
            if not comps:
                continue
            gsn = pd.read_csv(gd / "snps.tsv", sep="\t")
            lbf = pd.read_csv(gd / "lbf.tsv", sep="\t", header=None)
            g = lbf.iloc[[k - 1 for k in comps]].copy()
            g.columns = gsn.snp.tolist()
            g = g.loc[:, ~g.columns.duplicated()]
            g.insert(0, "component", [f"L{k}" for k in comps])
            ldd = WORK / "ld" / loc
            for n, zn in zz.groupby("n"):
                zf, lf = WORK / f"{loc}.n{n}.susie_z.tsv", WORK / f"{loc}.n{n}.qtl_lbf.tsv"
                zn[["pair_id", "idx", "z_a1"]].to_csv(zf, sep="\t", index=False)
                pr = subprocess.run([str(C.RSCRIPT), str(WORK / "susie_qtl.R"), str(ldd), str(n), str(zf), str(lf)],
                                    capture_output=True, text=True, timeout=7200, check=False)
                if pr.returncode != 0:
                    print("susie_qtl failed", loc, pr.stderr[-400:], flush=True)
                if not lf.exists() or lf.stat().st_size < 5:
                    continue
                f1, fo = WORK / f"{loc}.gwas_lbf.tsv", WORK / f"{loc}.n{n}.bfbf.tsv"
                g.to_csv(f1, sep="\t", index=False)
                subprocess.run([str(C.RSCRIPT), str(WORK / "bfbf.R"), str(f1), str(lf), str(fo), str(pri["p1"]),
                                str(pri["p2"]), str(pri["p12"])], capture_output=True, text=True, timeout=7200,
                               check=False)
                if not fo.exists() or fo.stat().st_size == 0:
                    continue
                r = pd.read_csv(fo, sep="\t")
                lz = long.set_index(["pair_id", "snp"])
                for row in r.to_dict("records"):
                    _, src, ct, gid = row["pair_id"].split("|")
                    key = (row["pair_id"], row["hit1"])
                    qtl_cog = np.nan
                    if key in lz.index:
                        t0 = lz.loc[key]
                        qtl_cog = float(t0.beta2) * (1 if float(t0.Zscore) > 0 else -1)
                    records.append({"locus_id": loc, "source": src, "cell_type_raw": ct, "cell_type": CT_LABEL[ct],
                                    "gene_id": gid, "method": "coloc.susie (coloc.bf_bf; multi-signal)",
                                    "nsnps": row["nsnps"], "PP.H0": row["PP.H0.abf"], "PP.H1": row["PP.H1.abf"],
                                    "PP.H2": row["PP.H2.abf"], "PP.H3": row["PP.H3.abf"], "PP.H4": row["PP.H4.abf"],
                                    "top_snp": row["hit1"], "qtl_lead_snp": row["hit2"],
                                    "gwas_component": f"L{row['idx1']}", "qtl_component": f"L{row['idx2']}",
                                    "qtl_effect_of_cognition_allele_at_top": qtl_cog,
                                    "weighted_sign_ratio_qtl_over_gwas": np.sign(qtl_cog) if pd.notna(qtl_cog) else np.nan})
                print("coloc.susie", loc, n, len(r), flush=True)

    res = pd.DataFrame(records)
    res["gene"] = res.gene_id.map(ens.symbol)
    res["strong"] = res["PP.H4"] >= strong
    res["moderate"] = res["PP.H4"] >= frozen["rules"]["gate_c"]["coloc"]["moderate_pp_h4"]
    res["priors"] = f"p1={pri['p1']};p2={pri['p2']};p12={pri['p12']}"
    res["independence_note"] = np.where(res.source == "SINGLEBRAIN",
                                        "SingleBrain meta includes Bryois (Roche) + ROSMAP donors: not independent of BRYOIS2022 or ROSMAP bulk",
                                        "Bryois donors partly ROSMAP (Mathys/Zhou/Cain): not independent of ROSMAP bulk eQTL")
    res.to_parquet(OUT / "sc_eqtl_coloc.parquet", index=False)
    print(len(res), "rows;", int(res.strong.sum()), "strong", flush=True)
    summarise(res, q, ens, tested, strong)
    return 0


def symbol_table(ens: pd.DataFrame, q: pd.DataFrame) -> pd.DataFrame:
    """Ensembl GRCh38 lookup indexed by gene_id; symbols missing in Ensembl filled from the Gate-C query
    table, then from the Bryois 'SYMBOL_ENSG' gene labels."""
    ens = ens.drop_duplicates("gene_id").set_index("gene_id")
    fill = dict(zip(q.ensembl_gene_id, q.gene))
    for f in LONG.glob("BRYOIS2022__pb__*.parquet"):
        g = pd.read_parquet(f, columns=["gene"]).gene.drop_duplicates()
        fill.update({x.rsplit("_", 1)[1]: x.rsplit("_", 1)[0] for x in g if x.rsplit("_", 1)[1] not in fill})
    ens["symbol"] = ens.symbol.where(ens.symbol.notna(), ens.index.map(fill))
    ens["symbol"] = ens.symbol.fillna(pd.Series(ens.index, index=ens.index))
    return ens


def summarise(res: pd.DataFrame, q: pd.DataFrame, ens: pd.DataFrame, tested: pd.DataFrame, strong: float) -> None:
    bulk = pd.read_csv(C.OUT / "directionality_resolution.csv")
    bulk_key = bulk.set_index(["locus_id", "gene"])
    tested = tested.assign(gene=tested.gene_id.map(ens.symbol))
    rows = []
    for (loc, gid), g in res.groupby(["locus_id", "gene_id"]):
        sym = ens.symbol.get(gid)
        rec = {"locus_id": loc, "gene": sym, "gene_id": gid,
               "gate_c_query_gene": bool(((q.locus_id == loc) & (q.ensembl_gene_id == gid)).any()),
               "n_tests": len(g), "best_pp_h4": float(g["PP.H4"].max())}
        for src in ("BRYOIS2022", "SINGLEBRAIN"):
            s = g[g.source == src]
            best = s.groupby("cell_type")["PP.H4"].max().sort_values(ascending=False)
            rec[f"{src}_best_pp_h4_by_cell_type"] = ";".join(f"{k}={v:.3f}" for k, v in best.items())
        st = g[g["PP.H4"] >= strong]
        rec["strong_cell_types"] = ";".join(sorted({f"{r.source}:{r.cell_type}" for r in st.itertuples()}))
        rec["n_strong_rows"] = len(st)
        signs = np.sign(st.qtl_effect_of_cognition_allele_at_top.dropna())
        for src in ("BRYOIS2022", "SINGLEBRAIN"):
            ss = st[st.source == src].qtl_effect_of_cognition_allele_at_top.dropna()
            rec[f"{src}_strong_sign"] = ("NA" if ss.empty else "+" if (ss > 0).all() else "-" if (ss < 0).all()
                                         else "MIXED")
        rec["strong_directions"] = ";".join(f"{r.source}:{r.cell_type}:{r.method.split(' ')[0]}:"
                                            f"{'+' if r.qtl_effect_of_cognition_allele_at_top > 0 else '-'}"
                                            f"@{r.top_snp}" for r in st.itertuples()
                                            if pd.notna(r.qtl_effect_of_cognition_allele_at_top))
        if len(signs):
            agree = max((signs > 0).mean(), (signs < 0).mean())
            maj = 1 if (signs > 0).sum() >= (signs < 0).sum() else -1
            rec["sc_direction"] = ("cognition-increasing allele -> HIGHER expression" if maj > 0 else
                                   "cognition-increasing allele -> LOWER expression")
            rec["sc_sign_agreement_across_strong"] = float(agree)
            rec["sc_consistency"] = "CONSISTENT" if agree == 1 else "MIXED"
        else:
            maj = 0
            rec["sc_direction"] = "no strong sc coloc"
            rec["sc_sign_agreement_across_strong"] = np.nan
            rec["sc_consistency"] = "NA"
        b = bulk_key.loc[(loc, sym)] if (loc, sym) in bulk_key.index else None
        if b is not None:
            b = b.iloc[0] if isinstance(b, pd.DataFrame) else b
            rec["bulk_label"] = b.label
            rec["bulk_majority_sign"] = int(b.rows_majority_sign)
            rec["bulk_n_strong_rows"] = int(b.rows_n_rows)
            if maj == 0 or int(b.rows_majority_sign) == 0:
                rec["sc_vs_bulk"] = "NOT_COMPARABLE"
            else:
                rec["sc_vs_bulk"] = "AGREE" if maj == int(b.rows_majority_sign) else "DISAGREE"
        else:
            rec["bulk_label"], rec["bulk_majority_sign"], rec["bulk_n_strong_rows"] = "not in bulk table", np.nan, np.nan
            rec["sc_vs_bulk"] = "NOT_COMPARABLE"
        rows.append(rec)
    s = pd.DataFrame(rows).sort_values(["n_strong_rows", "best_pp_h4"], ascending=False)
    s.to_csv(OUT / "sc_eqtl_coloc_summary.csv", index=False)
    print(s.head(30).to_string(), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
