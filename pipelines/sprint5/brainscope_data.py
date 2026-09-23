"""Loaders for the public brainSCOPE (Emani et al., Science 2024; PMID 38781369) scQTL files.

All inputs are read from data/interim/sprint5/brainscope/ as written by brainscope_fetch.py.

Verified file conventions (supplementary section 4.1 of the bioRxiv supplement + core_scqtl_processing_code):
  * QTLtools cis (1 Mb around the TSS) linear regression on log(CPM+1) pseudobulk (QTLtools --normal),
    covariates: sex, age, diagnosis, cohort, 5 genotype PCs, 100 (or 20) expression PCs.
  * [celltype]_sig_QTLs.dat are SIGNIFICANT PAIRS ONLY: every variant with nominal p <= the gene-specific
    beta-derived threshold for eGenes at q <= 0.05 (10,000 permutations). No full nominal summary statistics
    are public, so SE is not published; we derive |t| from the nominal p and the residual df.
  * Columns: gene symbol, gene chr, TSS, TSS, strand, n variants in cis, distance, variant id
    (chr:pos:REF:ALT, hg38), variant chr, pos, pos, nominal p, r^2, slope, best-hit flag.
  * Genotypes were lifted to hg38 and REF fixed to the hg38 reference with plink2 (supplement §1), so REF/ALT
    are hg38 reference/alternate. QTLtools regresses on the VCF dosage = count of the ALT allele, hence the
    slope is the effect of each copy of ALT (checked empirically against CommonMind bulk eQTLs, see
    brainscope_allele_check.py).
"""

from __future__ import annotations

import gzip
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from . import common as C  # type: ignore
except ImportError:  # executed as a script from pipelines/sprint5
    import common as C  # type: ignore

BS = C.WORK / "brainscope"
BASE_URL = "https://brainscope.gersteinlab.org"

SIG_CT = ["Astro", "Chandelier__Pvalb", "L2.3.IT", "L4.IT", "L5.6.NP", "L5.IT", "L6.CT", "L6.IT", "L6b",
          "Lamp5.Lhx6", "Lamp5", "Micro.PVM", "OPC", "Oligo", "PC", "Sst__Sst.Chodl", "Vip"]
NOCALL_CT = ["Endo__VLMC", "Immune", "L5.ET", "L6.IT.Car3", "Pax6", "SMC", "Sncg"]
ALL_CT = SIG_CT + NOCALL_CT
AGG_CT = {"excitatory": "excitatory__sig_QTLs.dat", "inhibitory": "inhibatory__sig_QTLs.dat",
          "non_neuronal": "non_neuronal__sig_QTLs.dat"}
COV_PCS = {"Immune": 20, "L5.ET": 20, "PC": 20, "Pax6": 20, "SMC": 20}

CELL_CLASS = {
    "L2.3.IT": "excitatory", "L4.IT": "excitatory", "L5.IT": "excitatory", "L5.6.NP": "excitatory",
    "L6.CT": "excitatory", "L6.IT": "excitatory", "L6b": "excitatory", "L5.ET": "excitatory",
    "L6.IT.Car3": "excitatory", "excitatory": "excitatory",
    "Chandelier__Pvalb": "inhibitory", "Lamp5": "inhibitory", "Lamp5.Lhx6": "inhibitory",
    "Sst__Sst.Chodl": "inhibitory", "Vip": "inhibitory", "Pax6": "inhibitory", "Sncg": "inhibitory",
    "inhibitory": "inhibitory",
    "Astro": "glia", "Oligo": "glia", "OPC": "glia", "Micro.PVM": "glia", "Immune": "glia",
    "PC": "other", "SMC": "other", "Endo__VLMC": "other", "non_neuronal": "glia+other",
}
# GRN (eQTL_edge) file cell-type names -> scQTL cell-type names
EDGE_TO_QTL = {"Ast": "Astro", "Chandelier": "Chandelier__Pvalb", "Pvalb": "Chandelier__Pvalb", "End": "Endo__VLMC",
               "VLMC": "Endo__VLMC", "Immune": "Immune", "Mic": "Micro.PVM", "Oli": "Oligo", "OPC": "OPC",
               "Sst": "Sst__Sst.Chodl", "Vip": "Vip", "Lamp5": "Lamp5", "Lamp5.Lhx6": "Lamp5.Lhx6", "Pax6": "Pax6",
               "Sncg": "Sncg", "L2.3.IT": "L2.3.IT", "L4.IT": "L4.IT", "L5.6.NP": "L5.6.NP", "L5.ET": "L5.ET",
               "L5.IT": "L5.IT", "L6.CT": "L6.CT", "L6.IT": "L6.IT", "L6.IT.Car3": "L6.IT.Car3", "L6b": "L6b"}
QTL_COLS = ["gene", "gene_chr", "tss", "tss2", "strand", "n_var_cis", "dist", "var_id", "var_chr", "var_pos",
            "var_pos2", "pval", "r2", "beta", "best_hit"]


def _split_var(df: pd.DataFrame, col: str = "var_id") -> pd.DataFrame:
    parts = df[col].str.split(":", n=3, expand=True)
    df["chr"] = parts[0].str.replace("chr", "", regex=False)
    df["pos"] = parts[1].astype(np.int64)
    df["ref"] = parts[2]
    df["alt"] = parts[3]
    return df


def _read_qtltools(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None, names=QTL_COLS, dtype={"gene": str, "var_id": str},
                     engine="c")
    return _split_var(df)


@lru_cache(maxsize=None)
def sig_core() -> pd.DataFrame:
    """Primary (core) callset, 17 cell types, significant pairs only."""
    zf = BS / "sig_QTLs.zip"
    frames = []
    with zipfile.ZipFile(zf) as z:
        for ct in SIG_CT:
            with z.open(f"sig_QTLs/{ct}_sig_QTLs.dat") as fh:
                d = _read_qtltools(fh)  # type: ignore[arg-type]
            d["cell_type"] = ct
            frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out["callset"] = "core"
    return out


@lru_cache(maxsize=None)
def sig_ld_pruned() -> pd.DataFrame:
    frames = []
    for ct in SIG_CT:
        p = BS / "sig_QTLs_LD_pruned" / f"{ct}_sig_QTLs.dat"
        if p.exists() and p.stat().st_size:
            d = _read_qtltools(p)
            d["cell_type"] = ct
            frames.append(d)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=QTL_COLS)
    out["callset"] = "ld_pruned"
    return out


@lru_cache(maxsize=None)
def sig_aggregated() -> pd.DataFrame:
    frames = []
    for ct, fn in AGG_CT.items():
        p = BS / "aggregated_qtl" / fn
        if p.exists() and p.stat().st_size:
            d = _read_qtltools(p)
            d["cell_type"] = ct
            frames.append(d)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=QTL_COLS)
    out["callset"] = "aggregated"
    return out


@lru_cache(maxsize=None)
def bayesian() -> pd.DataFrame:
    p = BS / "bayesian_scQTLs.dat"
    d = pd.read_csv(p, sep="\t")
    d = d.rename(columns={"cellType": "cell_type", "eGene": "gene", "eSNP": "var_id",
                          "posterior_mean_of_eff_size_beta": "beta", "sd_of_post_mean": "sd"})
    d = _split_var(d)
    d["callset"] = "bayesian"
    return d


@lru_cache(maxsize=None)
def egenes() -> dict[str, set]:
    out = {}
    with zipfile.ZipFile(BS / "sig_eGenes.zip") as z:
        for ct in SIG_CT:
            with z.open(f"sig_eGenes/{ct}_sig_eGenes.dat") as fh:
                out[ct] = {ln.decode().strip() for ln in fh if ln.strip()}
    return out


@lru_cache(maxsize=None)
def conditional_top() -> pd.DataFrame:
    frames = []
    for ct in SIG_CT:
        p = BS / "conditional_top_hits" / f"conditional_top_variants_per_signal_{ct}.txt"
        d = pd.read_csv(p, sep=r"\s+")
        d["cell_type"] = ct
        frames.append(d)
    d = pd.concat(frames, ignore_index=True).rename(columns={"phe_id": "gene"})
    return _split_var(d)


@lru_cache(maxsize=None)
def grn_edges() -> pd.DataFrame:
    frames = []
    for p in sorted((BS / "eQTL_edge").glob("*.eqtl_edge.txt")):
        grn_ct = p.name.replace(".eqtl_edge.txt", "")
        d = pd.read_csv(p, sep="\t")
        d.columns = ["gene", "var_id", "tf", "target", "cre"]
        d["grn_cell_type"] = grn_ct
        d["cell_type"] = EDGE_TO_QTL.get(grn_ct, grn_ct)
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    return _split_var(d)


@lru_cache(maxsize=None)
def isoqtls() -> pd.DataFrame:
    frames = []
    for p in sorted((BS / "isoqtls").glob("*_significant_sCQTLs_p0.05.txt")):
        ct = p.name.replace("_significant_sCQTLs_p0.05.txt", "")
        try:
            # sQTLseekeR output; header has one field fewer than rows (leading row id -> index)
            d = pd.read_csv(p, sep="\t")
        except pd.errors.EmptyDataError:
            continue
        d = d.reset_index(drop=True).rename(columns={"geneId": "gene", "snpId": "var_id", "pv": "pval"})
        d["iso_cell_type"] = ct
        frames.append(d)
    if not frames:
        return pd.DataFrame()
    return _split_var(pd.concat(frames, ignore_index=True))


@lru_cache(maxsize=None)
def tested_genes(ct: str) -> pd.DataFrame:
    """Genes present in the pseudobulk matrix used for QTL mapping (after the >10% non-zero filter)."""
    p = BS / "pseudobulk_genes" / f"{ct}.genes.tsv"
    d = pd.read_csv(p, sep="\t")
    d.columns = ["chr", "tss", "tss_end", "gene", "length", "strand"]
    d["chr"] = d["chr"].astype(str).str.replace("chr", "", regex=False)
    return d


@lru_cache(maxsize=None)
def covariates(ct: str) -> dict:
    pcs = COV_PCS.get(ct, 100)
    p = BS / "qtl_covariates" / f"{ct}.cov.{pcs}_expr_PCs.bed"
    d = pd.read_csv(p, sep="\t", index_col=0)
    num = d.apply(pd.to_numeric, errors="coerce")
    nonconst = int((num.nunique(axis=1) > 1).sum())
    cohort_rows = [r for r in d.index if r.startswith("cohort")]
    cohorts = {r.replace("cohort_is_", "").replace("cohort_", ""): int(num.loc[r].sum()) for r in cohort_rows}
    sample_ids = list(d.columns)
    # cohorts without an indicator row are the reference level; count samples not flagged by any row
    flagged = num.loc[cohort_rows].sum(axis=0)
    cohorts["unflagged_reference_level"] = int((flagged == 0).sum())
    return {"n": d.shape[1], "n_cov_rows": d.shape[0], "n_cov_nonconstant": nonconst,
            "df_resid": d.shape[1] - nonconst - 2, "cohort_counts": cohorts, "sample_ids": sample_ids,
            "n_expr_pcs": pcs}


def tested_variants(positions: set[tuple[str, int]]) -> dict[str, dict[tuple[str, int], list[str]]]:
    """For each of the 24 cell types: {(chr, pos): [variant ids]} restricted to the query positions."""
    out: dict[str, dict[tuple[str, int], list[str]]] = {}
    for ct in ALL_CT:
        p = BS / "candidate_SNPs" / f"{ct}.SNPs.dat.gz"
        m: dict[tuple[str, int], list[str]] = {}
        with gzip.open(p, "rt") as fh:
            for line in fh:
                vid = line.strip()
                if not vid:
                    continue
                c, pos, _ = vid.split(":", 2)
                key = (c.replace("chr", ""), int(pos))
                if key in positions:
                    m.setdefault(key, []).append(vid)
        out[ct] = m
    return out


@lru_cache(maxsize=None)
def atac_peaks() -> dict[str, pd.DataFrame]:
    """scCRE peak calls (snATAC/snMultiome) for 7 cell classes + union; hg38 BED."""
    out = {}
    with zipfile.ZipFile(BS / "scCRE.PeakCalls.zip") as z:
        for n in z.namelist():
            if not n.lower().endswith((".bed", ".bed.bed")) or n.startswith("__MACOSX"):
                continue
            with z.open(n) as fh:
                d = pd.read_csv(fh, sep="\t", header=None, usecols=[0, 1, 2], comment="#")
            d.columns = ["chr", "start", "end"]
            d["chr"] = d["chr"].astype(str).str.replace("chr", "", regex=False)
            name = Path(n).name.split(".PeakCalls")[0]
            out[name] = d.sort_values(["chr", "start"]).reset_index(drop=True)
    return out


@lru_cache(maxsize=None)
def _peaks_by_chr() -> dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]:
    out = {}
    for name, d in atac_peaks().items():
        for c, g in d.groupby("chr"):
            out[(name, c)] = (g.start.values, g.end.values)
    return out


def peaks_overlapping(chrom: str, pos: int) -> list[str]:
    hits = []
    for name in atac_peaks():
        arr = _peaks_by_chr().get((name, chrom))
        if arr is None:
            continue
        st, en = arr
        i = np.searchsorted(st, pos, side="right")  # BED 0-based start; pos 1-based
        lo = max(0, i - 50)
        if ((st[lo:i] < pos) & (en[lo:i] >= pos)).any():
            hits.append(name)
    return hits


GRN_TO_QTL = dict(EDGE_TO_QTL)


def grn_overlaps(positions: set[tuple[str, int]]) -> pd.DataFrame:
    """Query positions falling inside a GRN enhancer or promoter interval (TF-enhancer-promoter-target links).

    Returns one row per (chr, pos, grn_cell_type, element_type, element, target gene) with the TFs collapsed.
    GRN files (data/GRNs/<ct>_GRN.txt) are hg38 intervals 'chrN:start-end'.
    """
    bychr: dict[str, np.ndarray] = {}
    for c, p in positions:
        bychr.setdefault(c, []).append(p)  # type: ignore[arg-type]
    bychr = {c: np.array(sorted(v)) for c, v in bychr.items()}
    out = []
    for f in sorted((BS / "GRNs").glob("*_GRN.txt")):
        grn_ct = f.name.replace("_GRN.txt", "")
        d = pd.read_csv(f, sep="\t", usecols=["TF", "enhancer", "promoter", "TG", "Regulation"], dtype=str)
        for etype in ("enhancer", "promoter"):
            iv = d[etype].dropna().unique()
            if not len(iv):
                continue
            s = pd.Series(iv)
            parts = s.str.extract(r"^chr([^:]+):(\d+)-(\d+)$")
            parts.columns = ["chr", "start", "end"]
            parts["element"] = s
            parts = parts.dropna()
            parts["start"] = parts.start.astype(np.int64)
            parts["end"] = parts.end.astype(np.int64)
            hit_el = []
            for c, g in parts.groupby("chr"):
                if c not in bychr:
                    continue
                qp = bychr[c]
                lo = np.searchsorted(qp, g.start.values, side="right")  # positions > start (0-based start)
                hi = np.searchsorted(qp, g.end.values, side="right")    # positions <= end
                for el, a, b in zip(g.element.values, lo, hi):
                    for p in qp[a:b]:
                        hit_el.append((el, c, int(p)))
            if not hit_el:
                continue
            h = pd.DataFrame(hit_el, columns=[etype, "chr", "pos"])
            m = d.merge(h, on=etype)
            for (el, c, p, tg), g in m.groupby([etype, "chr", "pos", "TG"]):
                out.append({"chr": c, "pos": p, "grn_cell_type": grn_ct,
                            "cell_type": GRN_TO_QTL.get(grn_ct, grn_ct), "element_type": etype, "element": el,
                            "target_gene": tg, "n_tf": int(g.TF.nunique()),
                            "tfs": ";".join(sorted(g.TF.unique())[:20]),
                            "regulation": ";".join(sorted(g.Regulation.dropna().unique()))})
    return pd.DataFrame(out)
