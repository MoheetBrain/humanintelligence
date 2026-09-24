#!/usr/bin/env python3
"""Sprint 5A — developmental (Wen et al. 2024 Science 384:eadh0829, PsychENCODE devBrain) eQTL lookup +
colocalisation for the 36 Gate-C loci, and a regulatory-TIMING classification combining it with adult evidence.

devBrain data (Zenodo 12729266, CC-BY-4.0, open, no login), FULL cis nominal statistics (all tested pairs,
1 Mb window, FastQTL; hg19; rsIDs; slope per A1 of the matching .bim = effect allele):
  * EUR all (4-39 PCW, mostly Tri1/Tri2), N = 292, 50 HCPs
  * Tri1 EUR (4-13 PCW), N = 143;  Tri2 EUR (14-26 PCW), N = 145
Significance: gene is an eGene (permutation qval <= 0.05 in that analysis) and variant nominal p <= the gene's
pval_nominal_threshold. Proxy support: the dataset's lead eQTL variant for the gene has r2 >= 0.8 (1000G EUR) with
a cognition credible-set variant. Colocalisation: coloc.abf with the frozen Sprint-4 priors (p1 = p2 = 1e-4,
p12 = 5e-6) and the Sprint-4 R code path (gate_c_coloc.R_COLOC); strong = PP.H4 >= 0.8.

Timing classes (never inferred from expression level):
  PRENATAL_ONLY          prenatal-tissue support (devBrain EUR/Tri1/Tri2 or Walker 2019 fetal cortex) AND the gene
                         was assessed in adult brain without support (adult "absence" = not detected, low power
                         possible)
  DEVELOPMENTAL          developmental support only from fetal-derived in-vitro cells (Aygun 2021), or prenatal
                         support where adult evidence could not be assessed
  ADOLESCENT             requires adolescent-resolved QTL data; no open adolescent-specific QTL dataset exists here,
                         so this class is NEVER assigned (BrainSeq spans prenatal-85 y and is sensitivity-only)
  ADULT                  adult support (Sprint-4 adult bulk coloc strong, GTEx V11 query-variant eQTL, or
                         brainSCOPE DIRECT/CELL_SPECIFIC) and devBrain tested without prenatal support
  ADULT+DEVELOPMENTAL    both
  UNKNOWN                no support at any stage, or not testable
Support levels: COLOC (PP.H4 >= 0.8, locus-wide) > QTL_OVERLAP (query variant or r2>=0.8 proxy significant).
Outputs: reports/sprint5a/regulatory_timing.csv, reports/sprint5a/devbrain_qtl_coloc.csv,
         reports/sprint5a/devbrain_qtl_lookup.csv, data/raw/sprint5a/psychencode_dev/PROVENANCE.json (separately)
"""
from __future__ import annotations

import gzip
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "pipelines" / "sprint5"))
import brainscope_lookup as BL  # noqa: E402
from brainscope_typed_evidence import Plink  # noqa: E402

DEV = ROOT / "data/interim/sprint5a/psychencode_dev"
OUT = ROOT / "reports/sprint5a"
WORK = ROOT / "data/interim/sprint5a/devbrain_coloc"
RSCRIPT = Path("/opt/homebrew/Caskroom/miniforge/base/envs/hi-sprint4/bin/Rscript")
DAVIES = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/inputs/"
              "davies2018_open_complete.txt")
DAVIES_N = 282014
PRI = {"p1": 1e-4, "p2": 1e-4, "p12": 5e-6}
DATASETS = {  # name: (nominal filtered file, header?, permutation file, N, stage, ages)
    "devBrain_EUR": ("filtered__devBrain_eQTL_EUR_nominal_50HCP_FDR_0.05.txt", True,
                     "devBrain_eQTL_EUR_permutation_50HCP_FDR_0.05.txt.gz", 292, "PRENATAL", "4-39 PCW (Tri1 N=216 / Tri2 N=433 across all ancestries; EUR N=292)"),
    "devBrain_Tri1_EUR": ("filtered__trimester1_eQTL_EUR_nominal_FDR_0.05.txt", False,
                          "trimester1_eQTL_EUR_permutation_FDR_0.05.txt", 143, "PRENATAL_TRI1", "4-13 PCW"),
    "devBrain_Tri2_EUR": ("filtered__trimester2_eQTL_EUR_nominal_FDR_0.05.txt", False,
                          "trimester2_eQTL_EUR_permutation_FDR_0.05.txt", 145, "PRENATAL_TRI2", "14-26 PCW"),
}
EXTRA = {"MEF2C": ("ENSG00000081189", "L4208"), "KDM5B": ("ENSG00000117139", None)}
CANDIDATES = "NT5DC2 DNPH1 RHEBL1 CLCN2 DCC EXT1 MEF2C KDM5B EXOC4 AKAP6 NPAS3 TUFM SH2B1 EIF3C KIFC2 SLC39A8".split()
R_COLOC = r'''
suppressMessages(library(coloc))
args <- commandArgs(trailingOnly = TRUE)
d <- read.delim(args[1], stringsAsFactors = FALSE)
p1 <- as.numeric(args[3]); p2 <- as.numeric(args[4]); p12 <- as.numeric(args[5])
res <- list()
for (pid in unique(d$pair_id)) {
  x <- d[d$pair_id == pid, ]
  x <- x[is.finite(x$beta1) & is.finite(x$varbeta1) & x$varbeta1 > 0 & is.finite(x$beta2) &
         is.finite(x$varbeta2) & x$varbeta2 > 0 & x$maf > 0 & x$maf < 0.5, ]
  if (nrow(x) < 50) next
  r <- tryCatch(suppressWarnings(suppressMessages(coloc.abf(
         dataset1 = list(beta = x$beta1, varbeta = x$varbeta1, type = "quant", N = x$n1[1], MAF = x$maf, snp = x$snp),
         dataset2 = list(beta = x$beta2, varbeta = x$varbeta2, type = "quant", N = x$n2[1], MAF = x$maf, snp = x$snp),
         p1 = p1, p2 = p2, p12 = p12))), error = function(e) NULL)
  if (is.null(r)) next
  s <- r$summary
  top <- r$results[which.max(r$results$SNP.PP.H4), ]
  res[[pid]] <- data.frame(pair_id = pid, nsnps = s[["nsnps"]], PP.H0 = s[["PP.H0.abf"]], PP.H1 = s[["PP.H1.abf"]],
                           PP.H2 = s[["PP.H2.abf"]], PP.H3 = s[["PP.H3.abf"]], PP.H4 = s[["PP.H4.abf"]],
                           top_snp = top$snp, top_snp_pp_h4 = top$SNP.PP.H4)
}
out <- if (length(res)) do.call(rbind, res) else data.frame()
write.table(out, args[2], sep = "\t", row.names = FALSE, quote = FALSE)
'''


def load_nominal(fn: str, header: bool) -> pd.DataFrame:
    cols = ["pid", "sid", "dist", "npval", "slope"] + (["fdr"] if header else [])
    d = pd.read_csv(DEV / fn, sep=r"\s+", header=None, names=cols, dtype={"pid": str, "sid": str})
    d = d[d.pid != "pid"]
    for c in ("dist", "npval", "slope"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def load_perm(fn: str) -> pd.DataFrame:
    return pd.read_csv(DEV / fn, sep=r"\s+")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    genes = pd.read_csv(ROOT / "data/sprint4/gate_c_query_genes.csv")
    loci = genes.drop_duplicates("locus_id")[["locus_id", "chr", "lead_snp", "lead_pos_grch37", "cognition_increasing_allele"]]
    qv = pd.read_csv(ROOT / "data/sprint5/query_variants_cognition.csv")
    qv = qv[qv.locus_id.isin(set(genes.locus_id) | {"L4208"})]
    cs = qv.groupby("locus_id").rsid.apply(set).to_dict()
    # bim (hg19, A1 = effect allele) restricted to the loci windows
    bim_rows = []
    wins = {(str(r.chr), int(r.lead_pos_grch37)) for r in loci.itertuples()}
    l4208 = qv[qv.locus_id == "L4208"].iloc[0]
    if pd.notna(l4208.pos37):
        wins.add((str(int(l4208.chr37)), int(l4208.pos37)))
    else:  # MEF2C locus lead has no GRCh37 position recorded -> offline UCSC liftOver of the GRCh38 position
        import liftover_map as LM
        c37, p37, _ = LM.Lift().point(str(int(l4208.chr38)), int(l4208.pos38))
        wins.add((c37, p37))
    wbc: dict[str, list[int]] = {}
    for wc, wp in wins:
        wbc.setdefault(wc, []).append(wp)
    with gzip.open(DEV / "Variants_for_EUR_xQTLmapping_A1effect_A2other.hg19.sorted.removeRel.bim.gz", "rt") as fh:
        for line in fh:
            f = line.split()
            if len(f) < 6 or not f[3].isdigit():
                continue
            c = f[0]
            wl = wbc.get(c)
            if wl is None:
                continue
            p = int(f[3])
            if any(abs(p - wp) <= 1_500_000 for wp in wl):
                bim_rows.append((f[1], c, p, f[4].upper(), f[5].upper()))
    bim = pd.DataFrame(bim_rows, columns=["sid", "chr", "pos37", "A1", "A2"]).drop_duplicates("sid", keep=False)
    print("bim rows in windows:", len(bim), flush=True)
    dav = pd.read_csv(DAVIES, sep=" ", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"], dtype=str)
    dav = dav[dav.Markername.isin(set(bim.sid))].drop_duplicates("Markername", keep=False)
    dav["Effect_allele"], dav["Other_allele"] = dav.Effect_allele.str.upper(), dav.Other_allele.str.upper()
    dav["Zscore"] = dav.Zscore.astype(float)
    # 1000G EUR MAF + LD
    # devBrain sid -> 1000G EUR rsID by (chr, hg19 pos, allele set) (rsID merges make name matching lossy)
    tmp = WORK / "_pos.txt"
    tmp.write_text("\n".join(f"{c}\t{p}" for c, p in zip(bim.chr, bim.pos37)) + "\n")
    g1k = subprocess.run(["awk", "BEGIN{FS=\"\\t\"} NR==FNR{w[$1\":\"$2]=1; next} (($1\":\"$4) in w)"
                          "{print $1\"\\t\"$4\"\\t\"$2\"\\t\"$5\"\\t\"$6}", str(tmp),
                          "/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/"
                          "genetics_tools/reference/g1000_eur.bim"], capture_output=True, text=True, check=True).stdout
    gpos = {}
    for line in g1k.splitlines():
        c, p, rs, a1, a2 = line.split("\t")
        gpos.setdefault((c, int(p)), []).append((rs, {a1.upper(), a2.upper()}))
    g1k_of = {}
    for r in bim.itertuples(index=False):
        for rs, al in gpos.get((r.chr, r.pos37), []):
            if al == {r.A1, r.A2}:
                g1k_of[r.sid] = rs
                break
    bim["g1k"] = bim.sid.map(g1k_of)
    pl = Plink()
    pl.load_rsids(set(bim.g1k.dropna()))
    maf = {}
    for sid, rs in g1k_of.items():
        d = pl.dosage(rs)
        if d is not None:
            f = np.nanmean(d) / 2
            maf[sid] = min(f, 1 - f)
    print("1000G MAF for", len(maf), "of", len(bim), flush=True)

    gene_sets = {r.locus_id: g for r, g in [(r, genes[genes.locus_id == r.locus_id]) for r in loci.itertuples()]}
    targets = [(r.locus_id, r.ensembl_gene_id, r.gene) for r in genes.itertuples()]
    targets.append(("L4208", EXTRA["MEF2C"][0], "MEF2C"))
    lookup_rows, coloc_rows = [], []
    for ds, (nf, hdr, pf, n, stage, ages) in DATASETS.items():
        if not (DEV / nf).exists():
            print("MISSING", nf, flush=True)
            continue
        nom = load_nominal(nf, hdr)
        perm = load_perm(pf).set_index("pid")
        nom = nom.merge(bim, on="sid", how="inner")
        long = []
        for loc, ensg, sym in targets:
            e = nom[nom.pid == ensg]
            if e.empty:
                lookup_rows.append({"dataset": ds, "stage": stage, "locus_id": loc, "gene": sym, "ensembl_gene_id": ensg,
                                    "status": "GENE_NOT_TESTED_IN_DATASET"})
                continue
            pr = perm.loc[ensg] if ensg in perm.index else None
            thr = float(pr.pval_nominal_threshold) if pr is not None else np.nan
            q = float(pr.qval) if pr is not None else np.nan
            is_egene = bool(q <= 0.05) if pr is not None else False
            lead = str(pr.sid) if pr is not None else None
            csv = cs.get(loc, set())
            # direct credible-set hits
            h = e[e.sid.isin(csv)].merge(dav, left_on="sid", right_on="Markername", how="left")
            for x in h.itertuples(index=False):
                inc = x.Effect_allele if (isinstance(x.Effect_allele, str) and x.Zscore > 0) else \
                    (x.Other_allele if isinstance(x.Other_allele, str) else None)
                oth = x.Other_allele if inc == x.Effect_allele else x.Effect_allele
                st, inc_b = BL.match_alleles(inc, oth, x.A2, x.A1)  # (ref, alt) := (A2, A1): alt = effect allele
                sgn = 1 if inc_b == x.A1 else (-1 if inc_b == x.A2 else 0)
                sig = is_egene and x.npval <= thr
                lookup_rows.append({"dataset": ds, "stage": stage, "ages": ages, "N": n, "locus_id": loc, "gene": sym,
                                    "ensembl_gene_id": ensg, "rsid": x.sid, "match": "CREDIBLE_SET_VARIANT",
                                    "npval": x.npval, "slope_A1": x.slope, "A1_effect": x.A1, "A2_other": x.A2,
                                    "cognition_increasing_allele": inc, "alignment_status": st,
                                    "aligned_slope": x.slope * sgn if sgn else np.nan, "gene_qval": q,
                                    "pval_nominal_threshold": thr, "is_egene": is_egene,
                                    "status": "SIGNIFICANT" if sig else "TESTED_NOT_SIGNIFICANT"})
            # lead-variant proxy (r2 >= 0.8 with any credible-set variant)
            if is_egene and lead:
                best = (0.0, None, None)
                for v in csv:
                    if v == lead:
                        best = (1.0, v, 1.0)
                        break
                    gv, gl = g1k_of.get(v), g1k_of.get(lead)
                    rr = pl.signed_r(gv, gl) if gv and gl else None
                    if rr is not None and rr * rr > best[0]:
                        best = (rr * rr, v, rr)
                if best[0] >= 0.8:
                    lr = e[e.sid == lead]
                    x = lr.iloc[0] if len(lr) else None
                    dv = dav[dav.Markername == best[1]]
                    aligned = np.nan
                    if x is not None and len(dv):
                        dv = dv.iloc[0]
                        inc = dv.Effect_allele if dv.Zscore > 0 else dv.Other_allele
                        gq, gl = g1k_of.get(best[1]), g1k_of.get(lead)
                        s_q = 1 if (gq in pl.index and inc == pl.index[gq][2]) else (
                            -1 if gq in pl.index and inc == pl.index[gq][3] else 0)
                        s_l = 1 if gl in pl.index and x.A1 == pl.index[gl][2] else (
                            -1 if gl in pl.index and x.A1 == pl.index[gl][3] else 0)
                        if best[1] == lead:
                            s_l = s_q = 1
                            aligned = float(x.slope) * (1 if inc == x.A1 else (-1 if inc == x.A2 else np.nan))
                        elif s_q and s_l:
                            aligned = float(x.slope) * np.sign(best[2]) * s_q * s_l
                    lookup_rows.append({"dataset": ds, "stage": stage, "ages": ages, "N": n, "locus_id": loc,
                                        "gene": sym, "ensembl_gene_id": ensg, "rsid": lead,
                                        "match": f"LEAD_PROXY_r2={best[0]:.2f}_with_{best[1]}",
                                        "npval": float(pr.npval), "slope_A1": float(pr.slope),
                                        "aligned_slope": aligned, "gene_qval": q, "pval_nominal_threshold": thr,
                                        "is_egene": True, "status": "SIGNIFICANT_LEAD_PROXY"})
            # coloc input
            m = e.merge(dav, left_on="sid", right_on="Markername", how="inner")
            if m.empty:
                continue
            s = np.where((m.A1 == m.Effect_allele) & (m.A2 == m.Other_allele), 1,
                         np.where((m.A1 == m.Other_allele) & (m.A2 == m.Effect_allele), -1, 0))
            pal = np.array([frozenset((a, b)) in BL.PAL for a, b in zip(m.A1, m.A2)])
            m["maf"] = m.sid.map(maf)
            m = m[(s != 0)].assign(s=s[s != 0])
            m = m[~(pal[s != 0] & (m.maf > 0.4))]
            m = m[m.maf.notna() & (m.npval > 0)]
            z2 = stats.norm.isf(m.npval / 2)
            se = np.abs(m.slope) / z2
            m["beta2"] = m.slope * m.s          # effect of the Davies EFFECT allele
            m["varbeta2"] = se ** 2
            den = np.sqrt(2 * m.maf * (1 - m.maf) * (DAVIES_N + m.Zscore ** 2))
            m["beta1"], m["varbeta1"] = m.Zscore / den, 1 / den ** 2
            m["n1"], m["n2"] = DAVIES_N, n
            m["pair_id"] = f"{loc}|{ds}|{ensg}|{sym}"
            long.append(m[["pair_id", "sid", "beta1", "varbeta1", "beta2", "varbeta2", "maf", "n1", "n2", "Zscore"]]
                        .rename(columns={"sid": "snp"}))
        if long:
            L = pd.concat(long, ignore_index=True)
            inp, outp = WORK / f"{ds}.in.tsv", WORK / f"{ds}.out.tsv"
            L.to_csv(inp, sep="\t", index=False)
            (WORK / "coloc.R").write_text(R_COLOC)
            r = subprocess.run([str(RSCRIPT), str(WORK / "coloc.R"), str(inp), str(outp), str(PRI["p1"]), str(PRI["p2"]),
                                str(PRI["p12"])], capture_output=True, text=True, timeout=7200)
            if r.returncode != 0:
                print(r.stderr[-2000:], flush=True)
            res = pd.read_csv(outp, sep="\t") if outp.exists() and outp.stat().st_size else pd.DataFrame()
            top = L.set_index(["pair_id", "snp"])
            for row in res.to_dict("records"):
                loc, _, ensg, sym = row["pair_id"].split("|")
                t = top.loc[(row["pair_id"], row["top_snp"])]
                qtl_cog = float(t.beta2) * (1 if float(t.Zscore) > 0 else -1)
                coloc_rows.append({"locus_id": loc, "dataset": ds, "stage": stage, "ages": ages, "N": n, "gene": sym,
                                   "ensembl_gene_id": ensg, **{k: row[k] for k in ("nsnps", "PP.H0", "PP.H1", "PP.H2",
                                                                                     "PP.H3", "PP.H4")},
                                   "top_snp": row["top_snp"], "top_snp_pp_h4": row["top_snp_pp_h4"],
                                   "qtl_effect_of_cognition_allele_at_top": qtl_cog,
                                   "strong": row["PP.H4"] >= 0.8,
                                   "direction": "HIGHER" if qtl_cog > 0 else "LOWER"})
        print(ds, "done", flush=True)
    lk = pd.DataFrame(lookup_rows)
    co = pd.DataFrame(coloc_rows)
    lk.to_csv(OUT / "devbrain_qtl_lookup.csv", index=False, float_format="%.4g")
    co.to_csv(OUT / "devbrain_qtl_coloc.csv", index=False, float_format="%.4g")
    classify(lk, co, genes)


def _dir(vals) -> str:
    v = [x for x in vals if x in ("HIGHER", "LOWER", "MIXED")]
    if not v:
        return "NA"
    return v[0] if len(set(v)) == 1 else "MIXED"


def _agg(ev: list[str]) -> str | None:
    """collapse repeated 'QTL_OVERLAP:<ds>(<status>)' items to one per dataset with a count"""
    from collections import Counter
    c = Counter(ev)
    return ";".join(f"{k} x{n}" if n > 1 else k for k, n in c.items()) or None


def classify(lk: pd.DataFrame, co: pd.DataFrame, genes: pd.DataFrame) -> None:
    s5 = pd.read_csv(ROOT / "reports/sprint5/developmental_qtl_coloc.csv")
    a4 = pd.read_parquet(ROOT / "reports/sprint4/adult_brain_susie_coloc.parquet")
    meta = pd.read_csv(ROOT / "data/sprint4/eqtl_catalogue_brain_datasets.csv").set_index("dataset_id")
    sym = dict(zip(genes.ensembl_gene_id, genes.gene))
    sym[EXTRA["MEF2C"][0]] = "MEF2C"
    a4["gene"] = a4.gene_id.map(sym)
    a4["study"] = a4.dataset_id.map(meta.study_label) + ":" + a4.dataset_id.map(meta.tissue_label)
    d4 = pd.read_csv(ROOT / "reports/sprint4/directionality_resolution.csv")
    v11 = pd.read_csv(OUT / "gtex_v11_gene_direction.csv")
    bs = pd.read_csv(OUT / "brainscope_gene_summary.csv")
    bs = bs[bs.trait.str.startswith("cognition")]
    targets = [(r.locus_id, r.gene, r.ensembl_gene_id) for r in genes.itertuples()]
    targets.append(("L4208", "MEF2C", EXTRA["MEF2C"][0]))
    targets.append(("NO_COMMON_LOCUS", "KDM5B", EXTRA["KDM5B"][0]))
    rows = []
    for loc, g, ensg in targets:
        ev_pre, ev_vitro, ev_adult, ev_mixed, src, dirs = [], [], [], [], [], {}
        tested_pre = tested_adult = False
        # devBrain coloc + lookup
        c = co[(co.locus_id == loc) & (co.gene == g)] if len(co) else pd.DataFrame()
        for r in (c.to_dict("records") if len(c) else []):
            tested_pre = True
            if r["strong"]:
                ev_pre.append(f"COLOC:{r['dataset']}(PP.H4={r['PP.H4']:.2f})")
                dirs.setdefault("prenatal", []).append(r["direction"])
        l = lk[(lk.locus_id == loc) & (lk.gene == g)] if len(lk) else pd.DataFrame()
        if len(l):
            tested_pre = tested_pre or (l.status != "GENE_NOT_TESTED_IN_DATASET").any()
            for r in l[l.status.isin(["SIGNIFICANT", "SIGNIFICANT_LEAD_PROXY"])].itertuples():
                ev_pre.append(f"QTL_OVERLAP:{r.dataset}({r.status})")
                if pd.notna(r.aligned_slope) and r.alignment_status != "PALINDROMIC_AMBIGUOUS":
                    dirs.setdefault("prenatal", []).append("HIGHER" if r.aligned_slope > 0 else "LOWER")
        # Sprint-5 eQTL Catalogue developmental coloc (Walker fetal = prenatal tissue, overlaps devBrain samples)
        s = s5[(s5.locus_id == loc) & (s5.gene == g)]
        for r in s.to_dict("records"):
            lab = f"COLOC:{r['study_label']}:{r['sample_group']}(PP.H4={r['PP.H4']:.2f})"
            r = pd.Series(r)
            if r.stage_class == "DEVELOPMENTAL_FETAL":
                tested_pre = True
                if r.strong:
                    ev_pre.append(lab)
                    dirs.setdefault("prenatal", []).append("HIGHER" if "HIGHER" in r.direction else "LOWER")
            elif r.stage_class == "DEVELOPMENTAL_IN_VITRO" and r.strong:
                ev_vitro.append(lab)
                dirs.setdefault("in_vitro_fetal_derived", []).append("HIGHER" if "HIGHER" in r.direction else "LOWER")
            elif r.stage_class == "MIXED_AGE_SENSITIVITY" and r.strong:
                ev_mixed.append(lab)
                dirs.setdefault("mixed_age_BrainSeq", []).append("HIGHER" if "HIGHER" in r.direction else "LOWER")
        # adult: Sprint-4 bulk coloc (single + susie), directionality, V11, brainSCOPE
        a = a4[(a4.locus_id == loc) & (a4.gene == g)]
        if len(a):
            tested_adult = True
            for r in a[a["PP.H4"] >= 0.8].itertuples():
                ev_adult.append(f"COLOC:{r.study}")
                dirs.setdefault("adult_bulk", []).append("HIGHER" if r.qtl_effect_of_cognition_allele_at_top > 0 else "LOWER")
        v = v11[(v11.locus_id == loc) & (v11.gene == g)]
        for r in v.itertuples():
            tested_adult = True
            ev_adult.append(f"QTL_OVERLAP:GTEx_V11({r.n_tissues_sig} tissues)")
            if r.v11_direction_cognition_allele in ("HIGHER", "LOWER", "MIXED"):
                dirs.setdefault("adult_gtex_v11", []).append(r.v11_direction_cognition_allele)
        b = bs[(bs.locus_id == loc) & (bs.gene == g)]
        for r in b.itertuples():
            tested_adult = True
            if r.best_evidence_type in ("DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT"):
                ev_adult.append(f"QTL_OVERLAP:brainSCOPE({r.best_evidence_type};{r.celltypes_direct or r.celltypes_cell_specific_ld})")
                if r.direction_cognition_or_math_allele in ("HIGHER", "LOWER", "MIXED"):
                    dirs.setdefault("adult_brainscope", []).append(r.direction_cognition_or_math_allele)
        dd = d4[(d4.locus_id == loc) & (d4.gene == g)]
        adult_label = dd.label.iloc[0] if len(dd) else None
        tested_adult = tested_adult or len(dd) > 0
        pre = bool(ev_pre)
        adult = bool(ev_adult)
        if (pre or ev_vitro) and adult:
            cls = "ADULT+DEVELOPMENTAL"
        elif pre and tested_adult:
            cls = "PRENATAL_ONLY"
        elif pre or ev_vitro:
            cls = "DEVELOPMENTAL"
        elif adult and tested_pre:
            cls = "ADULT"
        elif adult:
            cls = "ADULT"  # developmental not testable -> noted
        else:
            cls = "UNKNOWN"
        best = "COLOC" if any(e.startswith("COLOC") for e in ev_pre + ev_adult + ev_vitro) else (
            "QTL_OVERLAP" if (ev_pre or ev_adult) else "NONE")
        stage_dirs = {k: _dir(v) for k, v in dirs.items()}
        concord = [v for v in stage_dirs.values() if v in ("HIGHER", "LOWER")]
        rows.append({"locus_id": loc, "gene": g, "ensembl_gene_id": ensg, "is_candidate": g in CANDIDATES,
                     "timing_class": cls, "strongest_evidence_type": best,
                     "prenatal_evidence": _agg(ev_pre),
                     "in_vitro_fetal_derived_evidence": _agg(ev_vitro),
                     "mixed_age_brainseq_evidence_sensitivity_only": _agg(ev_mixed),
                     "adult_evidence": ";".join(sorted(set(ev_adult))) or None,
                     "sprint4_adult_direction_label": adult_label,
                     "direction_prenatal": stage_dirs.get("prenatal", "NA"),
                     "direction_in_vitro": stage_dirs.get("in_vitro_fetal_derived", "NA"),
                     "direction_mixed_age": stage_dirs.get("mixed_age_BrainSeq", "NA"),
                     "direction_adult_bulk_coloc": stage_dirs.get("adult_bulk", "NA"),
                     "direction_adult_gtex_v11": stage_dirs.get("adult_gtex_v11", "NA"),
                     "direction_adult_brainscope": stage_dirs.get("adult_brainscope", "NA"),
                     "direction_consistent_across_stages": (len(set(concord)) == 1) if concord else None,
                     "prenatal_tested": tested_pre, "adult_tested": tested_adult,
                     "adolescent_tested": False,
                     "sources": "devBrain Wen2024 (Zenodo 12729266) EUR/Tri1/Tri2; Sprint5 eQTL Catalogue r7 Walker2019/"
                                "Aygun2021/BrainSeq coloc; Sprint4 adult bulk coloc + directionality; GTEx V11 lookup; "
                                "brainSCOPE typed evidence",
                     "notes": ("Walker 2019 samples are a subset of devBrain (not independent). " if any("Walker" in e for e in ev_pre) else "")
                              + ("ADULT but devBrain not testable. " if cls == "ADULT" and not tested_pre else "")
                              + ("KDM5B: rare-coding gene, no common cognition locus -> no variant to test. " if g == "KDM5B" else "")})
    out = pd.DataFrame(rows).sort_values(["is_candidate", "timing_class", "locus_id", "gene"], ascending=[False, True, True, True])
    out.to_csv(OUT / "regulatory_timing.csv", index=False)
    print(out.timing_class.value_counts())
    print(out[out.is_candidate][["locus_id", "gene", "timing_class", "strongest_evidence_type", "direction_prenatal",
                                 "direction_adult_bulk_coloc", "direction_adult_gtex_v11", "direction_adult_brainscope"]].to_string())


if __name__ == "__main__":
    if "--classify-only" in sys.argv:
        classify(pd.read_csv(OUT / "devbrain_qtl_lookup.csv"), pd.read_csv(OUT / "devbrain_qtl_coloc.csv"),
                 pd.read_csv(ROOT / "data/sprint4/gate_c_query_genes.csv"))
    else:
        main()
