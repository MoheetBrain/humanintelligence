#!/usr/bin/env python3
"""Sprint 5 — look up GWAS variants in PsychENCODE brainSCOPE single-cell (pseudobulk) eQTLs.

Usage
  python pipelines/sprint5/brainscope_lookup.py \
      --variants data/sprint5/query_variants_cognition.csv --out-prefix reports/sprint5/brainscope \
      [--directionality-out reports/sprint5/cell_specific_directionality.csv] [--no-ld]

Required variant columns: rsid, chr38, pos38. Optional: locus_id, origin, susie_pip, chr37, pos37,
allele_string, top_gene_label and, for allele alignment, EITHER davies_z + davies_effect_allele (the Davies 2018
other allele is then read from the GWAS file by rsID, falling back to allele_string when biallelic) OR
increasing_allele [+ other_allele]. Alignment is always to the TRAIT-INCREASING allele (cognition by default).

Outputs (prefix P)
  P_variant_lookup.csv          variant x cell type x gene rows: every significant hit in any public callset
                                (core, LD-pruned, Bayesian, isoform-usage) + status rows for
                                candidate genes in cis (TESTED_NOT_SIGNIFICANT / GENE_NOT_TESTED_IN_CELLTYPE /
                                VARIANT_NOT_TESTED) for the 17 cell types with a published core callset
                                In the CSV, status rows other than SIGNIFICANT and candidate-list TESTED_NOT_SIGNIFICANT
                                are collapsed to one row per variant x gene x status (cell types listed in cell_type);
                                the full per-cell-type table is P_variant_lookup_full.parquet
  P_variant_summary.csv         one row per query variant: tested cell types, significant genes, scATAC peaks
  P_enhancer_gene_links.csv     query variants inside GRN enhancer/promoter elements -> target genes
  P_coloc.parquet               coloc status per locus x gene x cell type (NOT_TESTABLE: significant-only data)
  --directionality-out          gene x cell type (x locus) aligned directions, cross-cell-type consistency and
                                comparison with Sprint-4 bulk directions

Statistical notes
  * brainSCOPE publishes SIGNIFICANT pairs only (q<=0.05 eGenes; pairs below the gene-specific nominal
    threshold). "TESTED_NOT_SIGNIFICANT" therefore means: variant in the tested SNP list for that cell type, gene
    in that cell type's pseudobulk matrix, TSS within 1 Mb, and pair absent from the significant list. It is NOT
    evidence of no effect (power is low: n = 97 to 346 individuals in the 17 cell types with callsets).
  * SE is not published; se_derived = |beta| / t_{df}^{-1}(1 - p/2) with df = N - (non-constant covariates) - 2.
  * Slope is per copy of ALT (hg38 REF/ALT) — verified by 99.99% sign concordance with eQTL Catalogue bulk
    brain eQTLs (brainscope_allele_check.py).
  * Palindromic (A/T, C/G) variants are flagged PALINDROMIC_AMBIGUOUS and excluded from direction consensus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brainscope_data as BD  # noqa: E402
import common as C  # noqa: E402

DAVIES = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/inputs/"
              "davies2018_open_complete.txt")
CANDIDATES = ("ATXN2L AKAP6 NT5DC2 EXT1 DCC EXOC4 KCNJ3 SLC39A8 CACNA1I PTPRT CLCN2 GOSR1 DHRS11 NEGR1 SYT1 MEF2C "
              "RPS26 RHEBL1 WBP2NL ERBB3 BSN CADM2 ADGRB2 KDM5B GIGYF1 ANKRD12 SLC8A1 RC3H2 CACNA1A BCAS3 PFKM "
              "CYP2D6 NAGA SUOX GNL3 NEK4 PPM1M ZNHIT3 GGNBP2 TUFM SH2B1 DDN SFMBT1 DPP4 CUL9 SMG7 CPN1 "
              "NUDT12").split()
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}
PAL = {frozenset("AT"), frozenset("CG")}
WINDOW = 1_000_000


# ----------------------------------------------------------------------------------------------- alignment
def load_davies_alleles(rsids: set[str]) -> pd.DataFrame:
    rows = []
    for chunk in pd.read_csv(DAVIES, sep=" ", usecols=["Markername", "Effect_allele", "Other_allele", "P-value",
                                                          "Zscore"], chunksize=2_000_000, dtype=str):
        rows.append(chunk[chunk.Markername.isin(rsids)])
    d = pd.concat(rows, ignore_index=True)
    d["Effect_allele"] = d.Effect_allele.str.upper()
    d["Other_allele"] = d.Other_allele.str.upper()
    return d.drop_duplicates("Markername").set_index("Markername")


def trait_alleles(q: pd.DataFrame, davies: pd.DataFrame | None) -> pd.DataFrame:
    inc, oth, basis = [], [], []
    for r in q.itertuples(index=False):
        rs = getattr(r, "rsid")
        i_all = o_all = None
        b = "NO_ALLELE_INFO"
        if "davies_z" in q.columns and pd.notna(getattr(r, "davies_z", np.nan)) and \
                pd.notna(getattr(r, "davies_effect_allele", np.nan)):
            ea = str(r.davies_effect_allele).upper()
            oa = None
            if davies is not None and rs in davies.index:
                dv = davies.loc[rs]
                if dv.Effect_allele == ea:
                    oa = dv.Other_allele
                elif dv.Other_allele == ea:
                    oa = dv.Effect_allele
            if oa is None and isinstance(getattr(r, "allele_string", None), str):
                al = r.allele_string.upper().split("/")
                rest = [a for a in al if a != ea]
                if len(al) == 2 and len(rest) == 1:
                    oa = rest[0]
            if oa is None:
                i_all = ea if float(r.davies_z) > 0 else None
                o_all = None if float(r.davies_z) > 0 else ea
                b = "DAVIES_EA_ONLY_OTHER_ALLELE_UNKNOWN"
            else:
                i_all, o_all = (ea, oa) if float(r.davies_z) > 0 else (oa, ea)
                b = "DAVIES_Z_SIGN"
        elif davies is not None and rs in davies.index and pd.notna(davies.loc[rs, "Zscore"]):
            # variant without a Davies z in the input (e.g. Open Targets credible-set member): take z and both
            # alleles directly from the Davies 2018 file by rsID
            dv = davies.loc[rs]
            z = float(dv.Zscore)
            i_all, o_all = (dv.Effect_allele, dv.Other_allele) if z > 0 else (dv.Other_allele, dv.Effect_allele)
            b = "DAVIES_FILE_BY_RSID" if z != 0 else "DAVIES_Z_ZERO"
            if z == 0:
                i_all = o_all = None
        elif "increasing_allele" in q.columns and pd.notna(getattr(r, "increasing_allele", np.nan)):
            i_all = str(r.increasing_allele).upper()
            o_all = str(r.other_allele).upper() if "other_allele" in q.columns and \
                pd.notna(getattr(r, "other_allele", np.nan)) else None
            b = "INPUT_INCREASING_ALLELE"
        inc.append(i_all)
        oth.append(o_all)
        basis.append(b)
    q = q.copy()
    q["increasing_allele"] = inc
    q["other_allele_trait"] = oth
    q["alignment_basis"] = basis
    return q


def match_alleles(inc, oth, ref, alt):
    """Return (status, increasing allele expressed on brainSCOPE strand or None)."""
    inc = inc if isinstance(inc, str) and inc else None
    oth = oth if isinstance(oth, str) and oth else None
    if inc is None and oth is None:
        return "NO_ALLELE_INFO", None
    known = {a for a in (inc, oth) if a}
    pair = {ref, alt}
    if oth is not None and inc is not None:
        if {inc, oth} == pair:
            if frozenset(pair) in PAL:
                return "PALINDROMIC_AMBIGUOUS", inc
            return "MATCHED", inc
        if all(a in COMP for a in (inc, oth)) and {COMP[inc], COMP[oth]} == pair:
            if frozenset(pair) in PAL:
                return "PALINDROMIC_AMBIGUOUS", inc
            return "STRAND_FLIPPED", COMP[inc]
        return "ALLELE_MISMATCH", None
    # only one allele known
    a = next(iter(known))
    if a in pair:
        if frozenset(pair) in PAL:
            return "PALINDROMIC_AMBIGUOUS", inc
        return "MATCHED_ONE_ALLELE", inc if inc is not None else (alt if a == ref else ref)
    return "ALLELE_MISMATCH", None


def t_from_p(p: float, df: int) -> float:
    if not np.isfinite(p) or df is None or df <= 0 or p <= 0:
        return np.nan
    return float(stats.t.isf(p / 2.0, df))


# ----------------------------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variants", required=True)
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--directionality-out", default=None)
    ap.add_argument("--candidate-genes", default=None, help="comma list or file (one symbol per line)")
    ap.add_argument("--trait", default="cognition (Davies 2018 g)")
    ap.add_argument("--no-ld", action="store_true", help="skip Ensembl rsID mapping + 1000G EUR r^2")
    ap.add_argument("--bulk-directions", default=str(C.S4_OUT / "directionality_resolution.csv"))
    a = ap.parse_args()

    prefix = Path(a.out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    cand = CANDIDATES
    if a.candidate_genes:
        p = Path(a.candidate_genes)
        cand = p.read_text().split() if p.exists() else [g.strip() for g in a.candidate_genes.split(",") if g.strip()]

    q0 = pd.read_csv(a.variants)
    for col in ("rsid", "chr38", "pos38"):
        if col not in q0.columns:
            sys.exit(f"missing column {col}")
    if "locus_id" not in q0.columns:
        q0["locus_id"] = "NA"
    q0 = q0[q0.chr38.notna() & q0.pos38.notna()].copy()
    q0["chr38"] = q0.chr38.astype(str).str.replace("chr", "", regex=False).str.replace(r"\.0$", "", regex=True)
    q0["pos38"] = q0.pos38.astype(float).astype(np.int64)
    davies = load_davies_alleles(set(q0.rsid)) if "davies_z" in q0.columns and DAVIES.exists() else None
    q0 = trait_alleles(q0, davies)
    # unique variants (a variant can sit in several loci / origins)
    agg = {"locus_id": lambda s: ";".join(sorted(set(map(str, s)))),
           "susie_pip": "max" if "susie_pip" in q0.columns else "first",
           "origin": (lambda s: ";".join(sorted(set(map(str, s))))) if "origin" in q0.columns else "first",
           "top_gene_label": (lambda s: ";".join(sorted({str(x) for x in s if pd.notna(x)}))) if "top_gene_label"
           in q0.columns else "first",
           "increasing_allele": "first", "other_allele_trait": "first", "alignment_basis": "first"}
    agg = {k: v for k, v in agg.items() if k in q0.columns}
    qv = q0.groupby(["rsid", "chr38", "pos38"], as_index=False).agg(agg)
    positions = {(c, int(p)) for c, p in zip(qv.chr38, qv.pos38)}
    print(f"{len(q0)} input rows -> {len(qv)} unique variants", flush=True)

    # ---------------------------------------------------------------- brainSCOPE tables
    tested_v = BD.tested_variants(positions)
    cov = {ct: BD.covariates(ct) for ct in BD.ALL_CT}
    genes_ct = {ct: BD.tested_genes(ct) for ct in BD.ALL_CT}
    egenes = BD.egenes()
    core = BD.sig_core()
    ldp = BD.sig_ld_pruned()
    bay = BD.bayesian()
    iso = BD.isoqtls()
    cond = BD.conditional_top()
    grn = BD.grn_edges()
    posdf = pd.DataFrame(list(positions), columns=["chr", "pos"])

    def at_query(df):
        return df.merge(posdf, on=["chr", "pos"], how="inner") if len(df) else df

    # NOTE: the portal's "aggregated" excitatory/inhibitory/non_neuronal files were verified to be byte-identical
    # (after sorting) to concatenations of the per-cell-type core files (excitatory = 7 excitatory types,
    # inhibitory = 5 inhibitory types, non_neuronal = Astro+OPC+Oligo+Micro.PVM), so they are NOT a separate
    # analysis and are excluded here to avoid double counting.
    hits = pd.concat([at_query(core), at_query(ldp)], ignore_index=True)
    bay_q = at_query(bay)
    iso_q = at_query(iso) if len(iso) else iso
    cond_q = at_query(cond)
    grn_q = at_query(grn)
    cond_keys = {(r.cell_type, r.gene, r.var_id): int(r["rank"]) for _, r in cond_q.iterrows()}
    grn_map: dict[tuple, list[str]] = {}
    for r in grn_q.itertuples(index=False):
        grn_map.setdefault((r.cell_type, r.gene, r.var_id), []).append(f"{r.grn_cell_type}:{r.tf}:{r.cre}")

    # query variant lookup by position
    qpos = {}
    for r in qv.itertuples(index=False):
        qpos.setdefault((r.chr38, int(r.pos38)), []).append(r)

    rows = []

    def base(r, ct, callset):
        return {"locus_id": r.locus_id, "rsid": r.rsid, "origin": getattr(r, "origin", None),
                "susie_pip": getattr(r, "susie_pip", np.nan), "chr38": r.chr38, "pos38": int(r.pos38),
                "trait": a.trait, "increasing_allele": r.increasing_allele, "other_allele": r.other_allele_trait,
                "alignment_basis": r.alignment_basis, "callset": callset, "cell_type": ct,
                "cell_class": BD.CELL_CLASS.get(ct, "other"),
                "n_individuals": cov[ct]["n"] if ct in cov else np.nan}

    # ---- significant hits: QTLtools callsets (core / ld_pruned / aggregated)
    for h in hits.itertuples(index=False):
        for r in qpos.get((h.chr, int(h.pos)), []):
            st, inc_bs = match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
            if st == "ALLELE_MISMATCH":
                continue
            d = base(r, h.cell_type, h.callset)
            df_ = cov[h.cell_type]["df_resid"] if h.cell_type in cov else None
            t = t_from_p(h.pval, df_)
            aligned = h.beta if inc_bs == h.alt else (-h.beta if inc_bs == h.ref else np.nan)
            d.update({"bs_variant_id": h.var_id, "ref": h.ref, "alt": h.alt, "effect_allele": h.alt, "gene": h.gene,
                      "gene_tss38": int(h.tss), "dist_to_tss": int(h.dist), "status": "SIGNIFICANT",
                      "pval": h.pval, "r2": h.r2, "beta_alt": h.beta,
                      "se_derived": abs(h.beta) / t if t and np.isfinite(t) and t > 0 else np.nan,
                      "alignment_status": st, "aligned_beta": aligned,
                      "aligned_direction": ("HIGHER" if aligned > 0 else "LOWER") if np.isfinite(aligned) else None,
                      "best_hit_for_gene": int(h.best_hit), "n_var_in_cis": int(h.n_var_cis),
                      "conditional_signal_rank": cond_keys.get((h.cell_type, h.gene, h.var_id)),
                      "grn_edges": ";".join(grn_map.get((h.cell_type, h.gene, h.var_id), [])) or None,
                      "gene_is_egene_in_celltype": h.gene in egenes.get(h.cell_type, set())
                      if h.callset == "core" else None})
            rows.append(d)
    # ---- Bayesian callset (posterior mean / sd; no p-values)
    for h in bay_q.itertuples(index=False):
        for r in qpos.get((h.chr, int(h.pos)), []):
            st, inc_bs = match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
            if st == "ALLELE_MISMATCH":
                continue
            d = base(r, h.cell_type, "bayesian")
            aligned = h.beta if inc_bs == h.alt else (-h.beta if inc_bs == h.ref else np.nan)
            d.update({"bs_variant_id": h.var_id, "ref": h.ref, "alt": h.alt, "effect_allele": h.alt, "gene": h.gene,
                      "status": "SIGNIFICANT", "beta_alt": h.beta, "se_derived": h.sd,
                      "alignment_status": st, "aligned_beta": aligned,
                      "aligned_direction": ("HIGHER" if aligned > 0 else "LOWER") if np.isfinite(aligned) else None,
                      "notes": "Bayesian LMM callset: beta = posterior mean, se_derived = posterior SD"})
            rows.append(d)
    # ---- isoform-usage QTLs (sQTLseekeR; no signed effect)
    if len(iso_q):
        for h in iso_q.itertuples(index=False):
            for r in qpos.get((h.chr, int(h.pos)), []):
                st, _ = match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
                if st == "ALLELE_MISMATCH":
                    continue
                d = base(r, h.iso_cell_type, "isoQTL_sQTLseekeR")
                d["cell_class"] = BD.CELL_CLASS.get(h.iso_cell_type.replace("_", "."), "see_cell_type")
                d["n_individuals"] = np.nan
                # the public isoQTL files list SNPs for isoGenes with permuted beta p<0.05 but WITHOUT FDR
                # filtering (per-SNP nominal pv values up to ~0.6 are present); only fdr_bh<0.05 is called here
                iso_status = "SIGNIFICANT" if pd.notna(h.fdr_bh) and h.fdr_bh < 0.05 else "LISTED_NOT_FDR_SIGNIFICANT"
                d.update({"bs_variant_id": h.var_id, "ref": h.ref, "alt": h.alt, "gene": h.gene,
                          "status": iso_status, "pval": h.pval, "alignment_status": st,
                          "notes": f"isoform-usage QTL; unsigned (max rel. usage diff md={h.md:.3f}; "
                                   f"fdr_bh={h.fdr_bh:.3g}); file threshold = permuted p<0.05"})
                rows.append(d)

    sig = pd.DataFrame(rows)
    core_sig_keys = set()
    if len(sig):
        cs = sig[sig.callset == "core"]
        core_sig_keys = set(zip(cs.rsid, cs.cell_type, cs.gene))

    # ---- status rows for candidate genes in cis (core callset cell types only)
    cand_rows = []
    summary = []
    # precomputed gene coordinates: per cell type {gene: (chr, tss)} and across all cell types
    gpos_ct = {ct: {g_: (c_, int(t_)) for g_, c_, t_ in zip(genes_ct[ct].gene, genes_ct[ct].chr, genes_ct[ct].tss)}
               for ct in BD.ALL_CT}
    gpos_any: dict[str, set] = {}
    for ct in BD.ALL_CT:
        for g_, ct_pos in gpos_ct[ct].items():
            gpos_any.setdefault(g_, set()).add(ct_pos)
    sig_by_rs = {k: v for k, v in sig.groupby("rsid")} if len(sig) else {}
    # GRCh37 gene coordinates (NCBI 37.3, MAGMA gene.loc) for genes of interest absent from every brainSCOPE matrix
    absent_loc: dict[str, tuple[str, int]] = {}
    if C.GENE_LOC.exists():
        gl = pd.read_csv(C.GENE_LOC, sep=r"\s+", header=None, names=["id", "chr", "start", "stop", "strand", "sym"])
        for rr in gl.itertuples(index=False):
            absent_loc.setdefault(rr.sym, (str(rr.chr), int(rr.start if rr.strand == "+" else rr.stop)))
    has37 = "chr37" in q0.columns and "pos37" in q0.columns
    pos37 = {}
    if has37:
        for rr in q0.dropna(subset=["chr37", "pos37"]).itertuples(index=False):
            pos37[rr.rsid] = (str(rr.chr37).replace(".0", ""), int(float(rr.pos37)))
    for r in qv.itertuples(index=False):
        genes_interest = set(cand) | {g for g in str(getattr(r, "top_gene_label", "") or "").split(";") if g and
                                      g != "nan"}
        n_tested, n_tested_core = 0, 0
        atac = BD.peaks_overlapping(r.chr38, int(r.pos38))
        tested_in = []
        for gene in sorted(genes_interest):
            if gene in gpos_any or gene not in absent_loc or r.rsid not in pos37:
                continue
            gc, gt = absent_loc[gene]
            vc, vp = pos37[r.rsid]
            if gc == vc and abs(gt - vp) <= WINDOW:
                d = base(r, "ALL_24", "core")
                d.update({"gene": gene, "status": "GENE_NOT_IN_ANY_BRAINSCOPE_MATRIX", "cell_class": "all",
                          "n_individuals": np.nan, "dist_to_tss": vp - gt,
                          "notes": "symbol absent from all 24 pseudobulk matrices (filtered or annotation "
                                   "difference); cis status judged on GRCh37 NCBI37.3 TSS; NOT a tested null"})
                cand_rows.append(d)
        for ct in BD.ALL_CT:
            ids = tested_v[ct].get((r.chr38, int(r.pos38)), [])
            match = None
            for vid in ids:
                _, _, ref, alt = vid.split(":")
                st, inc_bs = match_alleles(r.increasing_allele, r.other_allele_trait, ref, alt)
                if st != "ALLELE_MISMATCH":
                    match = (vid, ref, alt, st, inc_bs)
                    break
            if match:
                n_tested += 1
                tested_in.append(ct)
                n_tested_core += ct in BD.SIG_CT
            if ct not in BD.SIG_CT:
                continue
            vpos = int(r.pos38)
            for gene in sorted(genes_interest):
                if (r.rsid, ct, gene) in core_sig_keys:
                    continue
                gp = gpos_ct[ct].get(gene)
                if gp is None:
                    # gene not in this cell type's matrix: emit only if it is in cis in some other cell type
                    if not any(c_ == r.chr38 and abs(t_ - vpos) <= WINDOW for c_, t_ in gpos_any.get(gene, ())):
                        continue
                    status = "GENE_NOT_TESTED_IN_CELLTYPE"
                    tss = None
                elif gp[0] != r.chr38 or abs(gp[1] - vpos) > WINDOW:
                    continue  # gene tested but TSS > 1 Mb away: not a cis pair
                else:
                    status = "TESTED_NOT_SIGNIFICANT" if match else "VARIANT_NOT_TESTED"
                    tss = gp[1]
                d = base(r, ct, "core")
                d.update({"gene": gene, "status": status,
                          "gene_tss38": tss if tss is not None else np.nan,
                          "dist_to_tss": vpos - tss if tss is not None else np.nan,
                          "bs_variant_id": match[0] if match else None, "ref": match[1] if match else None,
                          "alt": match[2] if match else None, "alignment_status": match[3] if match else None,
                          "gene_is_egene_in_celltype": gene in egenes.get(ct, set())})
                if status == "TESTED_NOT_SIGNIFICANT":
                    d["notes"] = ("EGENE_VARIANT_ABOVE_THRESHOLD" if d["gene_is_egene_in_celltype"]
                                  else "NOT_EGENE_Q_GT_0.05")
                cand_rows.append(d)
        s = sig_by_rs.get(r.rsid, pd.DataFrame())
        sc = s[s.callset == "core"] if len(s) else s
        summary.append({"rsid": r.rsid, "locus_id": r.locus_id, "chr38": r.chr38, "pos38": int(r.pos38),
                        "susie_pip": getattr(r, "susie_pip", np.nan), "top_gene_label": getattr(r, "top_gene_label", None),
                        "increasing_allele": r.increasing_allele, "other_allele": r.other_allele_trait,
                        "n_celltypes_variant_tested": n_tested, "n_core_celltypes_variant_tested": n_tested_core,
                        "tested_celltypes": ";".join(tested_in),
                        "n_core_sig_pairs": int(len(sc)),
                        "core_sig_genes": ";".join(sorted(set(sc.gene))) if len(sc) else "",
                        "core_sig_celltypes": ";".join(sorted(set(sc.cell_type))) if len(sc) else "",
                        "any_callset_sig_genes": ";".join(sorted(set(s.gene))) if len(s) else "",
                        "scATAC_peak_overlap": ";".join(atac)})
    # ---- enhancer/promoter -> target-gene links (cell-type GRNs) overlapping query variants
    grn_ov = BD.grn_overlaps(positions) if (BD.BS / "GRNs").exists() else pd.DataFrame()
    summ = pd.DataFrame(summary)
    if len(grn_ov):
        grn_ov = grn_ov.merge(qv[["rsid", "locus_id", "chr38", "pos38"]], left_on=["chr", "pos"],
                              right_on=["chr38", "pos38"]).drop(columns=["chr38", "pos38"])
        grn_ov["target_in_candidate_list"] = grn_ov.target_gene.isin(cand)
        gsum = grn_ov.groupby("rsid").apply(
            lambda g: ";".join(sorted({f"{t}({e[0]})" for t, e in zip(g.target_gene, g.element_type)})),
            include_groups=False).rename("grn_element_target_genes")
        summ = summ.merge(gsum, left_on="rsid", right_index=True, how="left")
        grn_ov.sort_values(["locus_id", "rsid", "target_gene", "grn_cell_type"]).to_csv(
            f"{prefix}_enhancer_gene_links.csv", index=False)
    summary = summ
    look = pd.concat([sig, pd.DataFrame(cand_rows)], ignore_index=True)
    look["gene_in_candidate_list"] = look.gene.isin(cand)

    # ---- cell-type specificity per (variant, gene) in the core callset
    core_rows = look[look.callset == "core"]
    spec = []
    for (rs, gene), g in core_rows.groupby(["rsid", "gene"]):
        s = g[g.status == "SIGNIFICANT"]
        ns = g[g.status == "TESTED_NOT_SIGNIFICANT"]
        ok = s[s.alignment_status.isin(["MATCHED", "STRAND_FLIPPED", "MATCHED_ONE_ALLELE"])]
        signs = set(np.sign(ok.aligned_beta.dropna()))
        spec.append({"rsid": rs, "gene": gene, "n_celltypes_sig": int(s.cell_type.nunique()),
                     "celltypes_sig": ";".join(sorted(s.cell_type.unique())),
                     "n_celltypes_tested_not_sig": int(ns.cell_type.nunique()),
                     "celltype_sign_disagreement": len(signs) > 1})
    spec = pd.DataFrame(spec)
    if len(spec):
        spec["specificity"] = np.where(spec.n_celltypes_sig == 0, "NONE_SIGNIFICANT",
                                       np.where(spec.n_celltypes_tested_not_sig > 0, "CELLTYPE_RESTRICTED",
                                                "SIGNIFICANT_IN_ALL_INFORMATIVE_TESTED"))
        look = look.merge(spec, on=["rsid", "gene"], how="left")
    cols = ["locus_id", "rsid", "origin", "susie_pip", "chr38", "pos38", "trait", "increasing_allele", "other_allele",
            "alignment_basis", "callset", "cell_type", "cell_class", "n_individuals", "gene", "gene_in_candidate_list",
            "gene_tss38", "dist_to_tss", "status", "bs_variant_id", "ref", "alt", "effect_allele", "beta_alt",
            "se_derived", "pval", "r2", "alignment_status", "aligned_beta", "aligned_direction", "best_hit_for_gene",
            "n_var_in_cis", "conditional_signal_rank", "grn_edges", "gene_is_egene_in_celltype", "n_celltypes_sig",
            "celltypes_sig", "n_celltypes_tested_not_sig", "celltype_sign_disagreement", "specificity", "notes"]
    for c in cols:
        if c not in look.columns:
            look[c] = None
    look = look[cols].sort_values(["locus_id", "gene", "cell_type", "callset", "status", "rsid"])
    look.to_parquet(f"{prefix}_variant_lookup_full.parquet", index=False)
    # compact CSV: per-cell-type rows for SIGNIFICANT and TESTED_NOT_SIGNIFICANT; the uninformative statuses
    # (VARIANT_NOT_TESTED, GENE_NOT_TESTED_IN_CELLTYPE) collapsed to one row per variant x gene x status with
    # the cell types listed in cell_type (full per-cell-type table in the parquet)
    per_ct = ((look.status == "SIGNIFICANT") | ((look.status == "TESTED_NOT_SIGNIFICANT") & look.gene_in_candidate_list)
              | (look.callset == "isoQTL_sQTLseekeR"))
    keep = look[per_ct]
    coll = look[~per_ct]
    if len(coll):
        first = coll.groupby(["rsid", "gene", "status"], as_index=False).first()
        cts = coll.groupby(["rsid", "gene", "status"]).cell_type.apply(lambda x: ";".join(sorted(set(x))))
        first["cell_type"] = first.set_index(["rsid", "gene", "status"]).index.map(cts)
        first["cell_class"] = "collapsed"
        first["n_individuals"] = np.nan
        coll = first[cols]
    compact = pd.concat([keep, coll], ignore_index=True).sort_values(["locus_id", "gene", "cell_type", "callset",
                                                                      "status", "rsid"])
    for c in ("beta_alt", "se_derived", "aligned_beta", "r2", "susie_pip"):
        compact[c] = pd.to_numeric(compact[c], errors="coerce").round(5)
    compact["pval"] = pd.to_numeric(compact.pval, errors="coerce").map(lambda v: f"{v:.4g}" if pd.notna(v) else "")
    compact = compact.drop(columns=["trait", "origin", "alignment_basis"])  # in the parquet / summary / run json
    compact.to_csv(f"{prefix}_variant_lookup.csv", index=False)
    summary.to_csv(f"{prefix}_variant_summary.csv", index=False)
    print("lookup rows:", len(look), "significant:", int((look.status == "SIGNIFICANT").sum()), flush=True)

    # ---------------------------------------------------------------- directionality per locus x gene x cell type
    q_lead = {}
    for loc, g in q0.groupby("locus_id"):
        lead = g[g.get("origin", pd.Series(index=g.index, dtype=str)) == "SPRINT3_LOCUS_LEAD"] if "origin" in g else g
        if lead.empty and "susie_pip" in g:
            lead = g.sort_values("susie_pip", ascending=False)
        if lead.empty:
            lead = g
        q_lead[loc] = lead.iloc[0]
    csig = look[(look.callset == "core") & (look.status == "SIGNIFICANT")].copy()
    csig["locus_id"] = csig.locus_id.astype(str)
    csig = csig.assign(locus_id=csig.locus_id.str.split(";")).explode("locus_id")
    good = {"MATCHED", "STRAND_FLIPPED", "MATCHED_ONE_ALLELE"}
    drows = []
    for (loc, gene, ct), g in csig.groupby(["locus_id", "gene", "cell_type"]):
        ok = g[g.alignment_status.isin(good) & g.aligned_beta.notna()]
        up, dn = int((ok.aligned_beta > 0).sum()), int((ok.aligned_beta < 0).sum())
        w = ok.susie_pip.fillna(0).astype(float)
        pipw = float((w * np.sign(ok.aligned_beta)).sum() / w.sum()) if w.sum() > 0 else np.nan
        lead = ok.sort_values("pval").iloc[0] if len(ok) else g.sort_values("pval").iloc[0]
        maj = "HIGHER" if up > dn else ("LOWER" if dn > up else ("TIE" if up else "NOT_ALIGNABLE"))
        frac = max(up, dn) / (up + dn) if up + dn else np.nan
        # eQTL best hit for this gene in this cell type
        bh = core[(core.cell_type == ct) & (core.gene == gene) & (core.best_hit == 1)]
        bh_ids = sorted(set(bh.var_id))
        in_q = any((r_.chr, int(r_.pos)) in positions for r_ in bh.itertuples())
        drows.append({"locus_id": loc, "gene": gene, "cell_type": ct, "cell_class": BD.CELL_CLASS.get(ct),
                      "n_individuals": cov[ct]["n"], "status": "SIGNIFICANT",
                      "n_sig_query_variants": int(g.rsid.nunique()), "n_aligned": up + dn,
                      "n_palindromic_excluded": int((g.alignment_status == "PALINDROMIC_AMBIGUOUS").sum()),
                      "n_increasing_allele_higher": up, "n_increasing_allele_lower": dn,
                      "aligned_direction": maj, "within_celltype_consistency": frac, "pip_weighted_sign": pipw,
                      "lead_query_rsid": lead.rsid, "lead_query_pval": lead.pval, "lead_query_aligned_beta":
                          lead.aligned_beta, "lead_query_se_derived": lead.se_derived,
                      "gene_best_hit_variant": ";".join(bh_ids), "gene_best_hit_pval": float(bh.pval.min())
                      if len(bh) else np.nan, "best_hit_in_query_set": bool(in_q),
                      "gwas_lead_rsid": q_lead[loc].rsid if loc in q_lead else None,
                      "gene_in_candidate_list": gene in cand})
    dirdf = pd.DataFrame(drows)
    # candidate genes without any significant core hit: summarise their status per cell type
    nulls = look[(look.callset == "core") & (look.status != "SIGNIFICANT") & look.gene_in_candidate_list].copy()
    nulls["locus_id"] = nulls.locus_id.astype(str)
    nulls = nulls.assign(locus_id=nulls.locus_id.str.split(";")).explode("locus_id")
    have = set(zip(dirdf.locus_id, dirdf.gene, dirdf.cell_type)) if len(dirdf) else set()
    nrows = []
    for (loc, gene, ct), g in nulls.groupby(["locus_id", "gene", "cell_type"]):
        if (loc, gene, ct) in have:
            continue
        stt = "TESTED_NOT_SIGNIFICANT" if (g.status == "TESTED_NOT_SIGNIFICANT").any() else g.status.iloc[0]
        nrows.append({"locus_id": loc, "gene": gene, "cell_type": ct, "cell_class": BD.CELL_CLASS.get(ct),
                      "n_individuals": cov.get(ct, {}).get("n"), "status": stt, "n_sig_query_variants": 0,
                      "n_query_variants_tested": int((g.status == "TESTED_NOT_SIGNIFICANT").sum()),
                      "aligned_direction": "NO_SIGNIFICANT_EQTL" if stt == "TESTED_NOT_SIGNIFICANT" else "NOT_TESTED",
                      "gene_is_egene_in_celltype": bool(g.gene_is_egene_in_celltype.iloc[0]),
                      "gwas_lead_rsid": q_lead[loc].rsid if loc in q_lead else None, "gene_in_candidate_list": True})
    dirdf = pd.concat([dirdf, pd.DataFrame(nrows)], ignore_index=True)

    # cross-cell-type consistency per (locus, gene)
    if len(dirdf):
        cc = []
        for (loc, gene), g in dirdf.groupby(["locus_id", "gene"]):
            s = g[g.aligned_direction.isin(["HIGHER", "LOWER"])]
            hi = sorted(s[s.aligned_direction == "HIGHER"].cell_type)
            lo = sorted(s[s.aligned_direction == "LOWER"].cell_type)
            lab = ("NO_SIGNIFICANT_CELLTYPE" if not hi and not lo else "ALL_HIGHER" if hi and not lo else
                   "ALL_LOWER" if lo and not hi else "CELLTYPES_DISAGREE")
            cc.append({"locus_id": loc, "gene": gene, "n_celltypes_sig_aligned": len(hi) + len(lo),
                       "celltypes_higher": ";".join(hi), "celltypes_lower": ";".join(lo),
                       "n_celltypes_tested_not_sig": int((g.status == "TESTED_NOT_SIGNIFICANT").sum()),
                       "cross_celltype_consistency": lab})
        dirdf = dirdf.merge(pd.DataFrame(cc), on=["locus_id", "gene"], how="left")
        # bulk comparison (Sprint 4)
        bp = Path(a.bulk_directions)
        if bp.exists():
            b = pd.read_csv(bp)
            b = b.rename(columns={"label": "bulk_label", "rows_majority_sign": "bulk_majority_sign",
                                  "direction_statement": "bulk_direction_statement",
                                  "tissues_or_cohorts": "bulk_cohorts"})
            b = b[["gene", "locus_id", "bulk_label", "bulk_majority_sign", "bulk_direction_statement", "bulk_cohorts"]]
            dirdf = dirdf.merge(b, on=["gene", "locus_id"], how="left")

            def agree(r):
                if pd.isna(r.get("bulk_majority_sign")) or r.aligned_direction not in ("HIGHER", "LOWER"):
                    return "NOT_COMPARABLE"
                if int(r.bulk_majority_sign) == 0:
                    return "NOT_COMPARABLE_BULK_NO_MAJORITY"
                s = 1 if r.aligned_direction == "HIGHER" else -1
                return "AGREE" if s == int(r.bulk_majority_sign) else "DISAGREE"
            dirdf["bulk_vs_celltype"] = dirdf.apply(agree, axis=1)
            dirdf["bulk_independence_note"] = ("brainSCOPE includes CMC_MSSM (CommonMind) and ROSMAP donors: "
                                               "agreement with CommonMind/ROSMAP bulk eQTLs is NOT independent "
                                               "replication; GTEx donors are not in brainSCOPE")

    # ---------------------------------------------------------------- LD: eQTL best hit vs GWAS lead
    if not a.no_ld and len(dirdf) and (dirdf.status == "SIGNIFICANT").any():
        import brainscope_ld as LD
        need = dirdf[(dirdf.status == "SIGNIFICANT")]
        bh_vars = set()
        for v in need.gene_best_hit_variant.dropna():
            for vid in str(v).split(";"):
                if vid:
                    c_, p_, r_, a_ = vid.split(":")
                    bh_vars.add((c_.replace("chr", ""), int(p_), r_, a_))
        rsmap = LD.hg38_to_rsid(sorted(bh_vars))
        # rsids of query variants at those positions
        q_by_pos = {(r.chr38, int(r.pos38)): r.rsid for r in qv.itertuples()}
        pl = LD.Plink()
        lead_rs = {str(v.rsid) for v in q_lead.values()}
        pl.load_rsids(lead_rs | {x for x in rsmap.values() if x})
        dv = load_davies_alleles({x for x in rsmap.values() if x}) if DAVIES.exists() else None
        r2s, bh_rs, gwas_p = [], [], []
        for r in dirdf.itertuples():
            if r.status != "SIGNIFICANT" or not isinstance(r.gene_best_hit_variant, str):
                r2s.append(np.nan), bh_rs.append(None), gwas_p.append(np.nan)
                continue
            best = None
            best_r2 = -1.0
            best_p = np.nan
            for vid in r.gene_best_hit_variant.split(";"):
                c_, p_, rr, aa = vid.split(":")
                key = f"{c_.replace('chr', '')}:{p_}:{rr}:{aa}"
                rs = q_by_pos.get((c_.replace("chr", ""), int(p_))) or rsmap.get(key)
                if rs is None:
                    continue
                val = pl.r2(str(r.gwas_lead_rsid), rs) if r.gwas_lead_rsid else None
                if val is not None and val > best_r2:
                    best_r2, best = val, rs
                    best_p = float(dv.loc[rs, "P-value"]) if dv is not None and rs in dv.index else np.nan
                elif best is None:
                    best = rs
                    best_p = float(dv.loc[rs, "P-value"]) if dv is not None and rs in dv.index else np.nan
            r2s.append(best_r2 if best_r2 >= 0 else np.nan)
            bh_rs.append(best)
            gwas_p.append(best_p)
        dirdf["gene_best_hit_rsid"] = bh_rs
        dirdf["r2_best_hit_vs_gwas_lead_1000G_EUR"] = r2s
        dirdf["davies_p_at_best_hit"] = gwas_p
        dirdf["ld_tagging"] = np.select(
            [dirdf.status != "SIGNIFICANT", dirdf.best_hit_in_query_set.fillna(False).astype(bool),
             dirdf["r2_best_hit_vs_gwas_lead_1000G_EUR"] >= 0.8, dirdf["r2_best_hit_vs_gwas_lead_1000G_EUR"] >= 0.5,
             dirdf["r2_best_hit_vs_gwas_lead_1000G_EUR"].notna()],
            ["NA", "EQTL_LEAD_IN_GWAS_CREDIBLE_SET", "EQTL_LEAD_TAGS_GWAS_LEAD_R2_GE_0.8",
             "EQTL_LEAD_MODERATE_LD_R2_0.5_0.8", "EQTL_LEAD_NOT_IN_LD_R2_LT_0.5"], "LD_NOT_COMPUTABLE")
    dout = Path(a.directionality_out) if a.directionality_out else Path(f"{prefix}_cell_specific_directionality.csv")
    dirdf.sort_values(["locus_id", "gene", "cell_type"]).to_csv(dout, index=False)
    print("directionality rows:", len(dirdf), flush=True)

    # ---------------------------------------------------------------- coloc status
    reason = ("brainSCOPE publishes significant SNP-gene pairs only (gene-level q<=0.05 eGenes, pairs below the "
              "gene-specific nominal threshold); no full per-variant nominal summary statistics per cell type are "
              "public, and the individual genotypes needed to regenerate them are controlled-access (Synapse "
              "syn51111084 / AD Knowledge Portal). coloc.abf requires all tested variants in the region.")
    crow = []
    for r in dirdf.itertuples():
        crow.append({"locus_id": r.locus_id, "gene": r.gene, "cell_type": r.cell_type, "qtl_source": "brainSCOPE core",
                     "method": "coloc.abf (p1=1e-4, p2=1e-4, p12=5e-6)", "status": "NOT_TESTABLE", "reason": reason,
                     "nsnps": np.nan, "PP.H0": np.nan, "PP.H1": np.nan, "PP.H2": np.nan, "PP.H3": np.nan,
                     "PP.H4": np.nan, "lookup_status": r.status,
                     "ld_tagging": getattr(r, "ld_tagging", None),
                     "r2_best_hit_vs_gwas_lead": getattr(r, "_asdict")().get("r2_best_hit_vs_gwas_lead_1000G_EUR")})
    pd.DataFrame(crow).to_parquet(f"{prefix}_coloc.parquet", index=False)
    meta = {"created_utc": C.utc_now(), "variants": a.variants, "variants_sha256": C.sha256_file(Path(a.variants)),
            "n_input_rows": int(len(q0)), "n_unique_variants": int(len(qv)), "candidate_genes": cand,
            "outputs": [f"{prefix}_variant_lookup.csv", f"{prefix}_variant_summary.csv", str(dout),
                        f"{prefix}_coloc.parquet"],
            "trait": a.trait,
            "alignment_basis_counts": q0.alignment_basis.value_counts().to_dict()}
    Path(f"{prefix}_lookup_run.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
