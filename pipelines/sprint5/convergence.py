#!/usr/bin/env python3
"""Sprint 5 — rare-coding x common-regulatory convergence (frozen tests T1-T5).

Gene sets tested (from data/sprint5/rare_coding_gene_sets.json): exome-wide cognition genes (primary) and
exome-wide incl. EA proxy (secondary). Background = the 18,418-gene Davies MAGMA universe.
Matched null: 10,000 random sets, each gene drawn from the same stratum (gene-length decile x NSNPS
decile x LOEUF tertile; strata with < 5 genes merged into coarser length x LOEUF strata).
  T1  mean Davies MAGMA z (one-sided, higher)
  T2  fraction of genes inside the 159 Sprint-3 LD loci (gene span overlaps a locus span)
  T3  number of genes that are members of Sprint-3 common-variant sets at global FDR < 0.05 ('plain')
  T4  PRENATAL_DOMINANT fraction vs common Bonferroni genes (Fisher)
  T5  HPA 'RNA single nuclei brain specificity' class distribution vs common Bonferroni genes (Fisher on
      enriched/enhanced-any vs not; per-cell-type counts reported)
The protocol's power note applies: < 20 rare genes -> low power; a null is not evidence of no convergence.

Output: reports/sprint5/common_rare_convergence.csv (+ _detail.json)
"""

from __future__ import annotations

import glob
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

GENE_MAP = C.REPO_ROOT / "data/raw/magma_x01/2026-09-22/gene_id_map.tsv"
BONF = 0.05 / 18418


def load_universe() -> pd.DataFrame:
    g = pd.read_csv(C.DAVIES_GENES_OUT, sep=r"\s+")
    m = pd.read_csv(GENE_MAP, sep="\t", usecols=["GENE", "current_symbol"])
    g = g.merge(m, on="GENE", how="left")
    lo = pd.read_csv(C.REPO_ROOT / "data/interim/gnomad_constraint.tsv", sep="\t")
    g = g.merge(lo[["GENE", "oe_lof_upper"]], on="GENE", how="left")
    g["length"] = g.STOP - g.START
    g["len_dec"] = pd.qcut(g.length.rank(method="first"), 10, labels=False)
    g["snp_dec"] = pd.qcut(g.NSNPS.rank(method="first"), 10, labels=False)
    g["loeuf_t"] = pd.qcut(g.oe_lof_upper.rank(method="first"), 3, labels=False)
    g["loeuf_t"] = g.loeuf_t.fillna(-1).astype(int)
    g["stratum"] = g.len_dec.astype(str) + "_" + g.snp_dec.astype(str) + "_" + g.loeuf_t.astype(str)
    small = g.stratum.map(g.stratum.value_counts()) < 5
    g.loc[small, "stratum"] = "c" + g.loc[small, "len_dec"].astype(str) + "_" + g.loc[small, "loeuf_t"].astype(str)
    return g


def locus_spans() -> pd.DataFrame:
    loci = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv")
    u = load_universe().set_index("current_symbol")
    rows = []
    for r in loci.itertuples():
        gs = [x for x in str(r.bonferroni_genes).split(";") if x in u.index]
        if not gs:
            continue
        sub = u.loc[gs]
        rows.append({"locus_id": r.locus_id, "chr": int(sub.CHR.iloc[0]) if np.ndim(sub.CHR) else int(sub.CHR),
                     "start": int(np.min(sub.START)), "stop": int(np.max(sub.STOP))})
    return pd.DataFrame(rows)


def in_loci(g: pd.DataFrame, spans: pd.DataFrame) -> np.ndarray:
    out = np.zeros(len(g), bool)
    for s in spans.itertuples():
        out |= (g.CHR.to_numpy() == s.chr) & (g.START.to_numpy() <= s.stop) & (g.STOP.to_numpy() >= s.start)
    return out


def fdr_set_members() -> set[str]:
    p = pd.read_csv(C.GT_OUT / "pathway_enrichment.csv")
    sig = p[(p.conditioning == "plain") & (p.FDR_global < 0.05)]
    mem = set()
    for src in sig.source_file.unique():
        f = C.GT_DATA / "pathway_sets" / f"{src}.setannot"
        if not f.exists():
            f = next(iter(glob.glob(str(C.GT_DATA / "pathway_sets" / f"*{src}*.setannot"))), None)
            if f is None:
                continue
        want = set(sig[sig.source_file == src].SET)
        for line in Path(f).read_text().splitlines():
            parts = line.split()
            if parts and parts[0] in want:
                mem.update(parts[1:])
    return mem  # Entrez ids as strings


def matched_null(g: pd.DataFrame, idx: np.ndarray, stat, n: int = 10000, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pools = {s: np.flatnonzero(g.stratum.to_numpy() == s) for s in g.stratum.unique()}
    strata = g.stratum.to_numpy()[idx]
    draws = np.empty(n)
    for i in range(n):
        pick = np.array([rng.choice(pools[s]) for s in strata])
        draws[i] = stat(pick)
    return draws


def hpa() -> pd.DataFrame:
    f = sorted(glob.glob(str(C.REPO_ROOT / "data/raw/pathway_annotations/*/proteinatlas.tsv.zip")))[0]
    z = zipfile.ZipFile(f)
    h = pd.read_csv(z.open(z.namelist()[0]), sep="\t", usecols=["Gene", "RNA single nuclei brain specificity",
                                                               "RNA single nuclei brain specific nCPM"])
    return h.rename(columns={"Gene": "symbol", "RNA single nuclei brain specificity": "snb_spec",
                             "RNA single nuclei brain specific nCPM": "snb_ncpm"})


def run(name: str, genes: list[str], g: pd.DataFrame, spans, fdrmem, dev, hp) -> dict:
    sym = g.current_symbol.to_numpy()
    idx = np.flatnonzero(np.isin(sym, genes))
    found = sorted(set(sym[idx]))
    res = {"gene_set": name, "n_input": len(genes), "n_in_universe": len(idx), "genes_in_universe": ";".join(found),
           "missing": ";".join(sorted(set(genes) - set(found)))}
    if len(idx) == 0:
        return res
    z = g.ZSTAT.to_numpy()
    inl = in_loci(g, spans)
    ent = g.GENE.astype(str).to_numpy()
    inset = np.isin(ent, list(fdrmem))
    for tname, f in (("T1_mean_z", lambda ix: z[ix].mean()), ("T2_frac_in_loci", lambda ix: inl[ix].mean()),
                     ("T3_n_in_fdr_sets", lambda ix: inset[ix].sum())):
        obs = float(f(idx))
        null = matched_null(g, idx, f, n=10000)
        res[f"{tname}_obs"] = obs
        res[f"{tname}_null_mean"] = float(null.mean())
        res[f"{tname}_P_one_sided"] = float((1 + (null >= obs).sum()) / (1 + len(null)))
    res["T1_genes_bonferroni"] = ";".join(sorted(sym[idx][g.P.to_numpy()[idx] < BONF]))
    res["T1_genes_P_lt_0.05"] = ";".join(sorted(sym[idx][g.P.to_numpy()[idx] < 0.05]))
    common = set(sym[g.P.to_numpy() < BONF])
    d = dev.set_index("gene_symbol").developmental_class
    a = [d.get(x) for x in found]
    b = [d.get(x) for x in common]
    t4 = [[sum(v == "PRENATAL_DOMINANT" for v in a), sum(v not in (None, "PRENATAL_DOMINANT") for v in a)],
          [sum(v == "PRENATAL_DOMINANT" for v in b), sum(v not in (None, "PRENATAL_DOMINANT") for v in b)]]
    res["T4_prenatal_rare"] = f"{t4[0][0]}/{sum(t4[0])}"
    res["T4_prenatal_common"] = f"{t4[1][0]}/{sum(t4[1])}"
    res["T4_fisher_P"] = float(stats.fisher_exact(t4)[1]) if sum(t4[0]) and sum(t4[1]) else None
    hs = hp.set_index("symbol").snb_spec
    ra = [hs.get(x) for x in found]
    rb = [hs.get(x) for x in common]
    spec = lambda v: isinstance(v, str) and ("enriched" in v.lower() or "enhanced" in v.lower())  # noqa: E731
    t5 = [[sum(map(spec, ra)), sum(v is not None and not spec(v) for v in ra)],
          [sum(map(spec, rb)), sum(v is not None and not spec(v) for v in rb)]]
    res["T5_cell_specific_rare"] = f"{t5[0][0]}/{sum(t5[0])}"
    res["T5_cell_specific_common"] = f"{t5[1][0]}/{sum(t5[1])}"
    res["T5_fisher_P"] = float(stats.fisher_exact(t5)[1]) if sum(t5[0]) and sum(t5[1]) else None
    nc = hp.set_index("symbol").snb_ncpm
    res["T5_rare_cell_types"] = "; ".join(f"{x}:{nc.get(x)}" for x in found if isinstance(nc.get(x), str))
    return res


def main() -> int:
    C.load_rules()
    sets = json.loads((C.DATA / "rare_coding_gene_sets.json").read_text())
    g = load_universe()
    spans = locus_spans()
    fdrmem = fdr_set_members()
    dev = pd.read_parquet(C.GT_DATA / "developmental_classification.parquet")
    hp = hpa()
    rows = []
    for name in ("exome_wide_cognition", "exome_wide_cognition_incl_EA_proxy", "suggestive_cognition"):
        genes = sets.get(name) or []
        if genes:
            rows.append(run(name, genes, g, spans, fdrmem, dev, hp))
            print(json.dumps({k: v for k, v in rows[-1].items() if "genes" not in k}, default=str))
    out = pd.DataFrame(rows)
    out["power_note"] = C.load_rules()["convergence_tests"]["power_note"]
    out.to_csv(C.OUT / "common_rare_convergence.csv", index=False, float_format="%.4g")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
