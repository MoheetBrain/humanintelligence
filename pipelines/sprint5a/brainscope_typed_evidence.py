#!/usr/bin/env python3
"""Sprint 5A — typed brainSCOPE (Emani et al., Science 2024) evidence for cognition credible-set variants and
the math-53 lead variants.

Every output row is ONE (variant x gene x cell type x evidence type) with exactly one evidence type:

  DIRECT_VARIANT_GENE_OVERLAP   the query variant itself is a significant scQTL for the gene in that cell type
                                (core, LD-pruned, conditional [fwd or bwd significant], Bayesian or dynamic callset)
  CELL_SPECIFIC_QTL_SUPPORT     the query variant has r2 >= 0.8 (1000G EUR, 503 individuals) with a cell-type
                                eQTL SIGNAL variant: a conditional top variant per signal (rank 0 = primary,
                                rank >= 1 = secondary), the core best hit, or the Bayesian anchor eSNP.
                                (r2 = 1 when the query variant IS the signal variant.)
  REGULATORY_ELEMENT_SUPPORT    the query variant lies in open chromatin (adult b-cCRE and/or a matching-class
                                snATAC scCRE peak) that is linked to the gene, either by a cell-type GRN element
                                (enhancer/promoter -> target gene) containing the variant, or by promoter proximity
                                (element within +/-2 kb of the gene TSS).
  GRN_SUPPORT                   the query variant lies in a GRN enhancer/promoter element whose target is the gene
                                (open chromatin not required), or is listed in the eqtl_edge file for the gene.
  COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT
                                one row per locus x gene x cell type with any DIRECT / CELL_SPECIFIC row: Bayesian
                                colocalisation is not possible because no brainSCOPE output carries locus-wide
                                per-variant statistics (see research/sprint5a/agentA_notes.md, Entry A3).

Directions: brainSCOPE slopes are per ALT allele (hg38 REF/ALT; verified in Sprint 5,
data/sprint5/brainscope_allele_check.json). aligned_beta = expression effect of the trait-increasing allele.
For LD-proxy rows the sign is carried through the SIGNED 1000G EUR r between the trait-increasing allele of the
query variant and the ALT allele of the signal variant. Regulatory / GRN rows carry no allelic direction.
A/T and C/G variants: alignment_status PALINDROMIC_AMBIGUOUS, excluded from direction consensus.

Inputs: data/interim/sprint5/brainscope (Sprint-5 downloads, sha256 re-verified) + data/interim/sprint5a/brainscope
(gap-fill: conditional.[ct].txt, metaQTLs.txt, adult_bcCREs.bed, crispr_validation_results.xlsx, STARR-seq bed).

Outputs: reports/sprint5a/brainscope_typed_evidence.parquet, reports/sprint5a/brainscope_gene_summary.csv,
         reports/sprint5a/brainscope_coloc_testability.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "pipelines" / "sprint5"))
sys.path.insert(0, str(HERE))
import brainscope_data as BD  # noqa: E402
import brainscope_ld as BLD  # noqa: E402
import brainscope_lookup as BL  # noqa: E402

S5A = ROOT / "data/interim/sprint5a/brainscope"
OUT = ROOT / "reports/sprint5a"
CACHE = S5A / "ensembl_rsid_cache.json"
WINDOW = 1_000_000
R2_MIN = 0.8
CRISPR_GENES = {"NGEF", "RORB", "PLEKHO1", "TOM1L2"}  # crispr_validation_results.xlsx (data S22), 4 enhancer KOs
PEAK_CLASS = {"excitatory": "Exc", "inhibitory": "Inh", "Astro": "Astro", "Oligo": "Oligo", "OPC": "OPC",
              "Micro.PVM": "Micro", "Immune": "Micro", "Endo__VLMC": "Endo", "PC": "Endo", "SMC": "Endo"}
GATE_C = set(pd.read_csv(ROOT / "data/sprint4/gate_c_loci.csv").locus_id)


def peak_class(ct: str) -> str | None:
    cls = BD.CELL_CLASS.get(ct)
    if cls in ("excitatory", "inhibitory"):
        return PEAK_CLASS[cls]
    return PEAK_CLASS.get(ct)


# ------------------------------------------------------------------------------------------ query variants
def query_variants() -> pd.DataFrame:
    q = pd.read_csv(ROOT / "data/sprint5/query_variants_cognition.csv")
    q = q[q.chr38.notna() & q.pos38.notna()].copy()
    davies = BL.load_davies_alleles(set(q.rsid))
    q = BL.trait_alleles(q, davies)
    q["trait"] = "cognition (Davies 2018)"
    q["gate_c_locus"] = q.locus_id.isin(GATE_C)
    m = pd.read_csv(ROOT / "data/sprint5/math53_variants.csv")
    m = m[m.chr38.notna()].copy()
    m["locus_id"] = "M53_" + m.rsid
    m["origin"] = "MATH53_LEAD"
    m["increasing_allele"] = m.math_increasing_allele.str.upper()
    m["other_allele_trait"] = np.where(m.effect_allele.str.upper() == m.increasing_allele,
                                       m.other_allele.str.upper(), m.effect_allele.str.upper())
    m["alignment_basis"] = "MATH53_INCREASING_ALLELE"
    m["trait"] = "math (Giannelis 2025 Gq)"
    m["gate_c_locus"] = False
    cols = ["locus_id", "rsid", "origin", "chr38", "pos38", "increasing_allele", "other_allele_trait",
            "alignment_basis", "trait", "gate_c_locus"]
    out = pd.concat([q.reindex(columns=cols + ["susie_pip"]), m.reindex(columns=cols)], ignore_index=True)
    out["chr38"] = out.chr38.astype(float).astype(int).astype(str)
    out["pos38"] = out.pos38.astype(float).astype(np.int64)
    return out.drop_duplicates(["locus_id", "rsid", "trait"]).reset_index(drop=True)


# ------------------------------------------------------------------------------------------ loaders (new files)
def load_conditional_full() -> pd.DataFrame:
    frames = []
    for ct in BD.SIG_CT:
        d = pd.read_csv(S5A / "conditional_qtls" / f"conditional.{ct}.txt", sep=r"\s+", dtype=str)
        d = d[d.phe_id != "phe_id"]
        d["cell_type"] = ct
        frames.append(d)
    d = pd.concat(frames, ignore_index=True).rename(columns={"phe_id": "gene"})
    for c in ("n_var_in_cis", "rank", "fwd_pval", "fwd_slope", "fwd_sig", "bwd_pval", "bwd_slope", "bwd_sig",
              "bwd_best_hit", "phe_from"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return BD._split_var(d)


def load_meta() -> pd.DataFrame:
    """metaQTLs.txt -> (analysis, cell_type, gene, var_id) for the 4 cell-type-resolved analyses + dynamic."""
    rows = []
    with open(S5A / "meta_qtls" / "metaQTLs.txt") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            a = f[0]
            if a == "Bayesian":
                rows.append((a, f[1], f[2], f[3]))
            elif a in ("Conditional", "core_set_w_LD_pruning", "core_set_wo_LD_pruning"):
                rows.append((a, f[1], f[2], f[8]))
            elif a == "dynamic_eqtl":
                g, v = f[1].split("_chr", 1)
                rows.append((a, "dynamic(all)", g, "chr" + v))
    return pd.DataFrame(rows, columns=["analysis", "cell_type", "gene", "var_id"])


def load_bccre() -> pd.DataFrame:
    d = pd.read_csv(S5A / "bcCRE" / "adult_bcCREs.bed", sep="\t", header=None,
                    names=["chr", "start", "end", "dhs_id", "ccre_id", "ccre_class"])
    d["chr"] = d.chr.str.replace("chr", "", regex=False)
    return d.sort_values(["chr", "start"]).reset_index(drop=True)


def load_starr() -> pd.DataFrame:
    d = pd.read_csv(S5A / "validation" / "starrseq_enhancers_merged.bed", sep="\t", header=None, usecols=[0, 1, 2],
                    names=["chr", "start", "end"])
    d["chr"] = d.chr.str.replace("chr", "", regex=False)
    return d.sort_values(["chr", "start"]).reset_index(drop=True)


def overlap(df: pd.DataFrame, chrom: str, pos: int) -> pd.DataFrame:
    g = df[df.chr == chrom]
    return g[(g.start < pos) & (g.end >= pos)]


# ------------------------------------------------------------------------------------------ LD machinery
def hg38_to_rsid(keys: list[str]) -> dict[str, str | None]:
    cache = {}
    for p in (ROOT / "data/interim/sprint5/brainscope/ensembl_rsid_cache.json", CACHE):
        if p.exists():
            cache.update(json.loads(p.read_text()))
    todo = [k for k in keys if k not in cache]

    def one(k):
        c, p, ref, alt = k.split(":")
        c = c.replace("chr", "")
        rs = None
        for t in range(4):
            try:
                req = urllib.request.Request(
                    f"https://rest.ensembl.org/overlap/region/human/{c}:{p}-{p}?feature=variation",
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    js = json.loads(r.read())
                for x in js:
                    al = set(x.get("alleles") or [])
                    if x.get("id", "").startswith("rs") and ref in al and alt in al and x.get("start") == int(p):
                        rs = x["id"]
                        break
                break
            except Exception:  # noqa: BLE001
                time.sleep(1.5 * (t + 1))
        time.sleep(0.08)
        return k, rs

    if todo:
        print(f"Ensembl rsID lookups: {len(todo)}", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            for k, rs in ex.map(one, todo):
                cache[k] = rs
        CACHE.write_text(json.dumps(cache))
    return {k: cache.get(k) for k in keys}


class Plink(BLD.Plink):
    def load_rsids(self, rsids):  # write the temp list under sprint5a
        import subprocess
        need = sorted(r for r in rsids if r and r not in self.index)
        if not need:
            return
        tmp = S5A / "_ld_rsids.txt"
        tmp.write_text("\n".join(need) + "\n")
        cmd = ["awk", "BEGIN{FS=\"\\t\"} NR==FNR{want[$1]=1; next} ($2 in want){print FNR-1\"\\t\"$0}",
               str(tmp), f"{self.bfile}.bim"]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            i, c, rs, _, bp, a1, a2 = line.split("\t")
            self.index.setdefault(rs, (int(i), c, a1, a2, int(bp)))

    _dcache: dict = {}

    def dosage(self, rsid):
        if rsid not in self._dcache:
            self._dcache[rsid] = super().dosage(rsid)
        return self._dcache[rsid]

    def signed_r(self, a: str, b: str):
        x, y = self.dosage(a), self.dosage(b)  # dosage = count of bim A1
        if x is None or y is None:
            return None
        ok = ~np.isnan(x) & ~np.isnan(y)
        if ok.sum() < 50 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
            return None
        return float(np.corrcoef(x[ok], y[ok])[0, 1])


def allele_sign(pl: Plink, rsid: str, allele: str) -> int:
    """+1 if `allele` is the bim A1 (counted) allele of rsid, -1 if A2, 0 if neither (strand-complement tried)."""
    if rsid not in pl.index or not isinstance(allele, str):
        return 0
    _, _, a1, a2, _ = pl.index[rsid]
    a1, a2, allele = a1.upper(), a2.upper(), allele.upper()
    if allele == a1:
        return 1
    if allele == a2:
        return -1
    comp = "".join(BL.COMP.get(ch, "N") for ch in allele)
    if frozenset((a1, a2)) not in BL.PAL:
        if comp == a1:
            return 1
        if comp == a2:
            return -1
    return 0


# ------------------------------------------------------------------------------------------ main
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    qv = query_variants()
    print(f"query variants: {len(qv)} rows, {qv.rsid.nunique()} unique, {qv.locus_id.nunique()} loci", flush=True)
    pos_set = {(r.chr38, int(r.pos38)) for r in qv.itertuples()}

    core = BD.sig_core()
    ldp = BD.sig_ld_pruned()
    bay = BD.bayesian()
    cond = load_conditional_full()
    ctop = BD.conditional_top()
    meta = load_meta()
    edges = BD.grn_edges()
    print("loaded brainSCOPE callsets", flush=True)

    # gene TSS (hg38) from core callset (gene, chr, TSS) + pseudobulk gene files
    tss = core.drop_duplicates("gene")[["gene", "gene_chr", "tss"]].copy()
    tss["gene_chr"] = tss.gene_chr.astype(str).str.replace("chr", "", regex=False)
    tss = tss.set_index("gene")

    rows: list[dict] = []

    def base(r, gene, ct, etype):
        return {"locus_id": r.locus_id, "gate_c_locus": bool(r.gate_c_locus), "trait": r.trait, "rsid": r.rsid,
                "origin": r.origin, "susie_pip": getattr(r, "susie_pip", np.nan), "chr38": r.chr38,
                "pos38": int(r.pos38), "increasing_allele": r.increasing_allele, "other_allele": r.other_allele_trait,
                "gene": gene, "cell_type": ct, "cell_class": BD.CELL_CLASS.get(ct, "other" if ct else None),
                "evidence_type": etype}

    # ---------------- DIRECT: query variant is a significant scQTL for the gene -------------------------------
    qpos = qv.set_index(["chr38", "pos38"])
    sources = []
    for name, df, beta_col, p_col in (("core", core, "beta", "pval"), ("ld_pruned", ldp, "beta", "pval"),
                                      ("bayesian", bay, "beta", None)):
        d = df[[(c, p) in pos_set for c, p in zip(df.chr, df.pos)]].copy()
        d["callset"] = name
        d["beta_alt"] = d[beta_col]
        d["pval"] = d[p_col] if p_col else np.nan
        d["rank"] = np.nan
        sources.append(d)
    dc = cond[[(c, p) in pos_set for c, p in zip(cond.chr, cond.pos)]].copy()
    dc = dc[(dc.fwd_sig == 1) | (dc.bwd_sig == 1)]
    dc["callset"] = "conditional"
    dc["beta_alt"] = dc.bwd_slope
    dc["pval"] = dc.bwd_pval
    sources.append(dc)
    hits = pd.concat(sources, ignore_index=True)
    meta_idx = meta.groupby(["gene", "var_id"]).analysis.agg(lambda s: ";".join(sorted(set(s))))
    meta_ct_idx = meta.groupby(["cell_type", "gene", "var_id"]).analysis.agg(lambda s: ";".join(sorted(set(s))))
    for h in hits.itertuples(index=False):
        for r in qpos.loc[[(h.chr, h.pos)]].reset_index().itertuples(index=False):
            st, inc_bs = BL.match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
            if st in ("ALLELE_MISMATCH",):
                continue
            sgn = 1 if inc_bs == h.alt else (-1 if inc_bs == h.ref else 0)
            ab = h.beta_alt * sgn if sgn else np.nan
            d = base(r, h.gene, h.cell_type, "DIRECT_VARIANT_GENE_OVERLAP")
            d.update({"callset": h.callset, "bs_variant_id": h.var_id, "signal_variant_id": None,
                      "signal_source": None, "signal_rank": h.rank, "beta_alt": h.beta_alt, "pval": h.pval,
                      "ld_r2": np.nan, "ld_r_signed": np.nan, "alignment_status": st, "aligned_beta": ab,
                      "metaqtl_analyses_any_ct": meta_idx.get((h.gene, h.var_id)),
                      "metaqtl_analyses_same_ct": meta_ct_idx.get((h.cell_type, h.gene, h.var_id))})
            rows.append(d)
    print(f"DIRECT rows: {len(rows)}", flush=True)

    # ---------------- CELL_SPECIFIC: r2 >= 0.8 with a cell-type signal variant ----------------------------------
    sig = []
    t = ctop.copy()
    t["signal_source"] = np.where(t["rank"] == 0, "conditional_primary", "conditional_secondary")
    t["beta_alt"] = t.bwd_slope
    t["pval"] = t.bwd_pval
    sig.append(t[["cell_type", "gene", "var_id", "chr", "pos", "ref", "alt", "rank", "signal_source", "beta_alt",
                  "pval"]])
    b = core[core.best_hit == 1].copy()
    b["rank"], b["signal_source"], b["beta_alt"] = np.nan, "core_best_hit", b.beta
    sig.append(b[["cell_type", "gene", "var_id", "chr", "pos", "ref", "alt", "rank", "signal_source", "beta_alt",
                  "pval"]])
    b = bay.copy()
    b["rank"], b["signal_source"], b["beta_alt"], b["pval"] = np.nan, "bayesian_anchor", b.beta, np.nan
    sig.append(b[["cell_type", "gene", "var_id", "chr", "pos", "ref", "alt", "rank", "signal_source", "beta_alt",
                  "pval"]])
    sig = pd.concat(sig, ignore_index=True)
    # keep signals within WINDOW of any query variant of the same chromosome
    qby = {c: np.sort(g.pos38.unique()) for c, g in qv.groupby("chr38")}

    def near(c, p):
        a = qby.get(c)
        if a is None:
            return False
        i = np.searchsorted(a, p)
        return any(abs(a[j] - p) <= WINDOW for j in (i - 1, i) if 0 <= j < len(a))

    sig = sig[[near(c, p) for c, p in zip(sig.chr, sig.pos)]].reset_index(drop=True)
    print(f"signal variants near query loci: {len(sig)} rows, {sig.var_id.nunique()} unique", flush=True)
    # hg38 -> 1000G (GRCh37) rsID by offline UCSC liftOver + allele-set match (Ensembl REST was timing out)
    import liftover_map as LM
    rsmap = LM.map_to_1000g(sorted(sig.var_id.unique()), S5A)
    sig["signal_rsid"] = sig.var_id.map(rsmap)
    qids = {}
    for r in qv.itertuples(index=False):
        if isinstance(r.increasing_allele, str) and isinstance(r.other_allele_trait, str):
            qids[r.rsid] = f"chr{r.chr38}:{int(r.pos38)}:{r.other_allele_trait}:{r.increasing_allele}"
    qmap = LM.map_to_1000g(sorted(set(qids.values())), S5A)
    qv["bim_rsid"] = [qmap.get(qids.get(rs)) or rs for rs in qv.rsid]
    print(f"signal variants mapped to 1000G: {sig.signal_rsid.notna().sum()}/{len(sig)}; query variants mapped by "
          f"position: {sum(1 for v in qids.values() if qmap.get(v))}/{len(qids)}", flush=True)
    pl = Plink()
    pl.load_rsids(set(qv.bim_rsid) | set(sig.signal_rsid.dropna()))
    ld_cache: dict[tuple[str, str], float | None] = {}
    n_ld_missing = 0
    for r in qv.itertuples(index=False):
        s = sig[(sig.chr == r.chr38) & ((sig.pos - r.pos38).abs() <= WINDOW)]
        if s.empty:
            continue
        qrs = r.bim_rsid
        inc_sign_q = allele_sign(pl, qrs, r.increasing_allele) if isinstance(r.increasing_allele, str) else 0
        st_q = "PALINDROMIC_AMBIGUOUS" if isinstance(r.increasing_allele, str) and isinstance(
            r.other_allele_trait, str) and frozenset((r.increasing_allele, r.other_allele_trait)) in BL.PAL \
            else ("MATCHED" if inc_sign_q else "NO_1000G_ALLELE_MATCH")
        for h in s.itertuples(index=False):
            if not isinstance(h.signal_rsid, str):
                n_ld_missing += 1
                continue
            key = (qrs, h.signal_rsid)
            if key not in ld_cache:
                ld_cache[key] = 1.0 if qrs == h.signal_rsid else pl.signed_r(qrs, h.signal_rsid)
            rr = ld_cache[key]
            if rr is None:
                n_ld_missing += 1
                continue
            if rr * rr < R2_MIN:
                continue
            alt_sign = allele_sign(pl, h.signal_rsid, h.alt) if qrs != h.signal_rsid else 0
            if qrs == h.signal_rsid:  # the query variant IS the signal variant: align directly
                st, inc_bs = BL.match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
                sgn = 1 if inc_bs == h.alt else (-1 if inc_bs == h.ref else 0)
                ab = h.beta_alt * sgn if sgn else np.nan
            else:
                st = st_q
                ab = h.beta_alt * np.sign(rr) * inc_sign_q * alt_sign if inc_sign_q and alt_sign else np.nan
            d = base(r, h.gene, h.cell_type, "CELL_SPECIFIC_QTL_SUPPORT")
            d.update({"callset": h.signal_source.split("_")[0] if h.signal_source != "core_best_hit" else "core",
                      "bs_variant_id": None, "signal_variant_id": h.var_id, "signal_rsid": h.signal_rsid,
                      "signal_source": h.signal_source, "signal_rank": h.rank,
                      "beta_alt": h.beta_alt, "pval": h.pval, "ld_r2": rr * rr, "ld_r_signed": rr,
                      "alignment_status": st, "aligned_beta": ab,
                      "metaqtl_analyses_any_ct": meta_idx.get((h.gene, h.var_id)),
                      "metaqtl_analyses_same_ct": meta_ct_idx.get((h.cell_type, h.gene, h.var_id))})
            rows.append(d)
    print(f"rows after CELL_SPECIFIC: {len(rows)}; signal pairs without LD: {n_ld_missing}", flush=True)

    # ---------------- GRN / REGULATORY -------------------------------------------------------------------------
    grn = BD.grn_overlaps(pos_set)
    peaks = BD.atac_peaks()
    bccre = load_bccre()
    starr = load_starr()
    ann = {}
    for c, p in pos_set:
        pk = [n for n in BD.peaks_overlapping(c, p) if n != "All.celltypes.Union"]
        bc = overlap(bccre, c, p)
        ann[(c, p)] = {"sc_peaks": pk, "bccre": ";".join(bc.ccre_id + ":" + bc.ccre_class) or None,
                       "starr": not overlap(starr, c, p).empty}
    for g in grn.itertuples(index=False):
        for r in qpos.loc[[(g.chr, int(g.pos))]].reset_index().itertuples(index=False):
            a = ann[(g.chr, int(g.pos))]
            d = base(r, g.target_gene, g.cell_type, "GRN_SUPPORT")
            d.update({"callset": "GRN_element", "link_basis": f"GRN_{g.element_type.upper()}", "element": g.element,
                      "grn_cell_type": g.grn_cell_type, "grn_tfs": g.tfs, "grn_regulation": g.regulation})
            rows.append(d)
            pc = peak_class(g.cell_type)
            open_ = [x for x in a["sc_peaks"] if x == pc]
            if open_ or a["bccre"]:
                d2 = dict(d)
                d2["evidence_type"] = "REGULATORY_ELEMENT_SUPPORT"
                d2["link_basis"] = f"GRN_{g.element_type.upper()}_IN_OPEN_CHROMATIN"
                d2["open_chromatin"] = ";".join(filter(None, [("scATAC:" + pc) if open_ else None,
                                                              ("bcCRE:" + a["bccre"]) if a["bccre"] else None]))
                rows.append(d2)
    # promoter proximity: variant in open chromatin within +/-2 kb of a gene TSS
    tss_by_chr = {c: g for c, g in tss.reset_index().groupby("gene_chr")}
    for r in qv.itertuples(index=False):
        a = ann[(r.chr38, int(r.pos38))]
        if not (a["sc_peaks"] or a["bccre"]):
            continue
        g = tss_by_chr.get(r.chr38)
        if g is None:
            continue
        for gg in g[(g.tss - r.pos38).abs() <= 2000].itertuples(index=False):
            for src in (["adult_bcCRE"] if a["bccre"] else []) + [f"scATAC_{x}" for x in a["sc_peaks"]]:
                d = base(r, gg.gene, src, "REGULATORY_ELEMENT_SUPPORT")
                d["cell_class"] = src
                d.update({"callset": "open_chromatin", "link_basis": "PROMOTER_PROXIMITY_2KB",
                          "open_chromatin": ("bcCRE:" + a["bccre"]) if src == "adult_bcCRE" else src,
                          "tss_distance": int(r.pos38 - gg.tss)})
                rows.append(d)
    # eqtl_edge: query variant is itself a GRN-embedded eQTL for the gene
    e = edges[[(c, p) in pos_set for c, p in zip(edges.chr, edges.pos)]]
    for h in e.itertuples(index=False):
        for r in qpos.loc[[(h.chr, h.pos)]].reset_index().itertuples(index=False):
            st, inc_bs = BL.match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
            if st == "ALLELE_MISMATCH":
                continue
            d = base(r, h.gene, h.cell_type, "GRN_SUPPORT")
            d.update({"callset": "eqtl_edge", "link_basis": f"EQTL_EDGE_{str(h.cre).upper()}", "bs_variant_id": h.var_id,
                      "grn_cell_type": h.grn_cell_type, "grn_tfs": h.tf, "alignment_status": st})
            rows.append(d)

    ev = pd.DataFrame(rows)
    # per-row annotations
    ev["variant_in_starr_enhancer"] = [ann.get((c, int(p)), {}).get("starr") for c, p in zip(ev.chr38, ev.pos38)]
    ev["variant_in_adult_bccre"] = [ann.get((c, int(p)), {}).get("bccre") for c, p in zip(ev.chr38, ev.pos38)]
    ev["variant_sc_peaks"] = [";".join(ann.get((c, int(p)), {}).get("sc_peaks", [])) or None
                              for c, p in zip(ev.chr38, ev.pos38)]
    ev["crispr_validated_gene"] = ev.gene.isin(CRISPR_GENES)
    ev["is_secondary_signal"] = ev.signal_rank.fillna(0).astype(float) >= 1
    ev["aligned_direction"] = np.where(ev.aligned_beta > 0, "HIGHER", np.where(ev.aligned_beta < 0, "LOWER", None))
    ev.loc[ev.alignment_status == "PALINDROMIC_AMBIGUOUS", "aligned_direction"] = "AMBIGUOUS_PALINDROMIC"

    # ---------------- COLOC rows -------------------------------------------------------------------------------
    qtl = ev[ev.evidence_type.isin(["DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT"])]
    crow = []
    for (loc, tr, gene, ct), g in qtl.groupby(["locus_id", "trait", "gene", "cell_type"]):
        best = g.sort_values(["susie_pip"], ascending=False, na_position="last").iloc[0]
        d = {k: best[k] for k in ("locus_id", "gate_c_locus", "trait", "rsid", "origin", "susie_pip", "chr38", "pos38",
                                  "increasing_allele", "other_allele", "gene", "cell_type", "cell_class")}
        d.update({"evidence_type": "COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT", "callset": "none",
                  "coloc_reason": "brainSCOPE publishes significant pairs / signal leads only (core q<=0.05 pairs; "
                                  "conditional = fwd/bwd-significant variants only, median 2.6% of cis variants per "
                                  "gene; Bayesian = one anchor eSNP per gene, posterior mean/SD, no PIP); "
                                  "full nominal statistics require controlled genotypes (Synapse syn51111084)"})
        crow.append(d)
    ev = pd.concat([ev, pd.DataFrame(crow)], ignore_index=True)
    ev["crispr_validated_gene"] = ev.gene.isin(CRISPR_GENES)
    order = ["locus_id", "gate_c_locus", "trait", "rsid", "origin", "susie_pip", "chr38", "pos38", "increasing_allele",
             "other_allele", "gene", "cell_type", "cell_class", "evidence_type", "callset", "bs_variant_id",
             "signal_variant_id", "signal_rsid", "signal_source", "signal_rank", "is_secondary_signal", "ld_r2",
             "ld_r_signed", "beta_alt", "pval", "alignment_status", "aligned_beta", "aligned_direction",
             "metaqtl_analyses_any_ct", "metaqtl_analyses_same_ct", "link_basis", "element", "open_chromatin",
             "grn_cell_type", "grn_tfs", "grn_regulation", "tss_distance", "variant_in_adult_bccre", "variant_sc_peaks",
             "variant_in_starr_enhancer", "crispr_validated_gene", "coloc_reason"]
    ev = ev.reindex(columns=order)
    ev = ev.drop_duplicates(subset=[c for c in order if c not in ("grn_tfs", "grn_regulation")]).reset_index(drop=True)
    for c in ("signal_rank", "susie_pip", "ld_r2", "ld_r_signed", "beta_alt", "pval", "aligned_beta", "tss_distance"):
        ev[c] = pd.to_numeric(ev[c], errors="coerce")
    # booleans must be fixed BEFORE the object->string cast (NaN from the COLOC rows makes them object dtype,
    # and the string "False" is truthy)
    ev["is_secondary_signal"] = ev.signal_rank.fillna(0) >= 1
    ev["variant_in_starr_enhancer"] = ev.variant_in_starr_enhancer.map(lambda x: bool(x) if isinstance(x, (bool, np.bool_)) else False)
    ev["gate_c_locus"] = ev.gate_c_locus.astype(bool)
    ev["crispr_validated_gene"] = ev.crispr_validated_gene.astype(bool)
    for c in ev.columns:
        if ev[c].dtype == object:
            ev[c] = ev[c].astype("string")
    ev.to_parquet(OUT / "brainscope_typed_evidence.parquet", index=False)
    print(ev.evidence_type.value_counts(), flush=True)

    # ---------------- gene summary -----------------------------------------------------------------------------
    rank = {"DIRECT_VARIANT_GENE_OVERLAP": 1, "CELL_SPECIFIC_QTL_SUPPORT": 2, "REGULATORY_ELEMENT_SUPPORT": 3,
            "GRN_SUPPORT": 4, "COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT": 5}
    summ = []
    for (loc, tr, gene), g in ev.groupby(["locus_id", "trait", "gene"]):
        types = sorted(set(g.evidence_type), key=rank.get)
        best = types[0] if types[0] != "COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT" else types[0]
        q = g[g.evidence_type.isin(["DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT"])]
        qd = q[q.aligned_direction.isin(["HIGHER", "LOWER"])]
        # one call per cell type: majority of rows in that cell type
        ct_dir = {}
        for ct, gg in qd.groupby("cell_type"):
            up, dn = (gg.aligned_direction == "HIGHER").sum(), (gg.aligned_direction == "LOWER").sum()
            ct_dir[ct] = "HIGHER" if up > dn else ("LOWER" if dn > up else "TIE")
        vals = [v for v in ct_dir.values() if v != "TIE"]
        if not vals:
            direction = "NO_ALLELIC_EVIDENCE" if q.empty else "UNALIGNED"
            consistency = np.nan
        else:
            nh = vals.count("HIGHER")
            direction = "HIGHER" if nh == len(vals) else ("LOWER" if nh == 0 else "MIXED")
            consistency = max(nh, len(vals) - nh) / len(vals)
        row_consistency = np.nan
        if len(qd):
            nh = (qd.aligned_direction == "HIGHER").sum()
            row_consistency = max(nh, len(qd) - nh) / len(qd)
        meta_any = sorted({a for s in q.metaqtl_analyses_any_ct.dropna() for a in str(s).split(";")})
        summ.append({
            "locus_id": loc, "trait": tr, "gate_c_locus": bool(g.gate_c_locus.iloc[0]), "gene": gene,
            "best_evidence_type": best, "evidence_types": ";".join(types),
            "n_query_variants": g.rsid.nunique(),
            "celltypes_direct": ";".join(sorted(set(g[g.evidence_type == "DIRECT_VARIANT_GENE_OVERLAP"].cell_type.dropna()))),
            "celltypes_cell_specific_ld": ";".join(sorted(set(g[g.evidence_type == "CELL_SPECIFIC_QTL_SUPPORT"].cell_type.dropna()))),
            "celltypes_regulatory": ";".join(sorted(set(g[g.evidence_type == "REGULATORY_ELEMENT_SUPPORT"].cell_type.dropna()))),
            "celltypes_grn": ";".join(sorted(set(g[g.evidence_type == "GRN_SUPPORT"].cell_type.dropna()))),
            "cell_classes_qtl": ";".join(sorted(set(q.cell_class.dropna()))),
            "direction_cognition_or_math_allele": direction,
            "celltype_direction_calls": ";".join(f"{k}:{v}" for k, v in sorted(ct_dir.items())),
            "direction_consistency_celltypes": consistency, "direction_consistency_rows": row_consistency,
            "n_palindromic_rows_excluded": int((q.alignment_status == "PALINDROMIC_AMBIGUOUS").sum()),
            "max_ld_r2_to_signal": q.ld_r2.max() if len(q) else np.nan,
            "secondary_signal_support": bool(q.is_secondary_signal.any()),
            "primary_signal_support": bool(((q.evidence_type == "CELL_SPECIFIC_QTL_SUPPORT") &
                                            (q.signal_source.isin(["conditional_primary", "core_best_hit"]))).any()),
            "metaqtl_analyses": ";".join(meta_any) or None,
            "crispr_validated_gene": gene in CRISPR_GENES,
            "starr_enhancer_variant": bool(g.variant_in_starr_enhancer.any()),
            "coloc_status": "NOT_TESTABLE_WITH_PUBLIC_OUTPUT" if len(q) else "NO_QTL_EVIDENCE_TO_TEST",
        })
    sm = pd.DataFrame(summ).sort_values(["trait", "locus_id", "best_evidence_type", "gene"])
    sm.to_csv(OUT / "brainscope_gene_summary.csv", index=False, float_format="%.4g")
    print(sm.best_evidence_type.value_counts(), flush=True)

    # ---------------- coloc-testability evidence ---------------------------------------------------------------
    cq = cond.groupby(["cell_type", "gene"]).agg(n_rows=("var_id", "size"), n_cis=("n_var_in_cis", "first"))
    cq["frac"] = cq.n_rows / cq.n_cis
    b0 = pd.read_csv(ROOT / "data/interim/sprint5/brainscope/bayesian_scQTLs.dat", sep="\t")
    testab = {
        "conditional_full_files": {
            "n_gene_celltype": int(len(cq)), "median_fraction_of_cis_variants_listed": float(cq.frac.median()),
            "n_gene_celltype_with_all_cis_variants": int((cq.frac >= 1).sum()),
            "fraction_rows_fwd_or_bwd_significant": float(((cond.fwd_sig == 1) | (cond.bwd_sig == 1)).mean())},
        "bayesian_scQTLs": {"rows": int(len(b0)), "unique_gene_snp_pairs": int(b0[["eGene", "eSNP"]].drop_duplicates().shape[0]),
                            "unique_genes": int(b0.eGene.nunique()), "columns": list(b0.columns),
                            "has_pip_column": False,
                            "max_snps_per_gene": int(b0.groupby("eGene").eSNP.nunique().max())},
        "metaQTLs_analyses": meta.analysis.value_counts().to_dict(),
        "verdict": "NOT_TESTABLE: no brainSCOPE output contains per-variant statistics for all tested variants in a "
                   "region; coloc.abf/coloc.susie would require the controlled genotypes (syn51111084) or author-"
                   "provided nominal statistics.",
    }
    (OUT / "brainscope_coloc_testability.json").write_text(json.dumps(testab, indent=2, default=str))
    print(json.dumps(testab, indent=1, default=str)[:1500])


if __name__ == "__main__":
    main()
