#!/usr/bin/env python3
"""Empirical check of the brainSCOPE effect-allele convention (slope per copy of ALT in chr:pos:REF:ALT).

Compares signs of brainSCOPE core scQTL slopes with bulk eQTL Catalogue betas (ALT allele, GRCh38) for the
same (gene, variant) in the Sprint-4 adult-brain extracts (CommonMind DLPFC QTD000075, ROSMAP, GTEx
cortex). If the convention is ALT-coded, sign concordance among strong pairs should be far above 50%
(the paper reports consistent direction for scQTL/bulk overlappers, Fig. 4B). A value near 0% would mean
REF-coded; near 50% would mean unrelated/uninformative.

Output: data/sprint5/brainscope_allele_check.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brainscope_data as BD  # noqa: E402
import common as C  # noqa: E402


def main() -> None:
    genes = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv", usecols=["gene", "ensembl_gene_id"]).drop_duplicates()
    ens2sym = dict(zip(genes.ensembl_gene_id, genes.gene))
    meta = pd.read_csv(C.S4_DATA / "eqtl_catalogue_brain_datasets.csv")
    keep = meta[(meta.quant_method == "ge") & (meta.adult_status == "ADULT")]
    keep = keep[keep.study_label.isin(["CommonMind", "ROSMAP", "GTEx"])]
    ds_label = dict(zip(keep.dataset_id, keep.study_label + ":" + keep.sample_group.astype(str)))
    frames = []
    for p in sorted((C.S4_WORK / "eqtl").glob("*.parquet")):
        ds = p.stem.split("__")[1]
        if ds not in ds_label:
            continue
        d = pd.read_parquet(p, columns=["dataset_id", "gene_id", "chromosome", "position", "ref", "alt", "beta",
                                        "pvalue"])
        d = d[d.pvalue < 1e-6]
        frames.append(d)
    bulk = pd.concat(frames, ignore_index=True)
    bulk["gene"] = bulk.gene_id.map(ens2sym)
    bulk["chr"] = bulk.chromosome.astype(str)
    sc = BD.sig_core()
    m = sc.merge(bulk, left_on=["gene", "chr", "pos", "ref", "alt"], right_on=["gene", "chr", "position", "ref", "alt"],
                 suffixes=("_sc", "_bulk"))
    m_flip = sc.merge(bulk, left_on=["gene", "chr", "pos", "ref", "alt"],
                      right_on=["gene", "chr", "position", "alt", "ref"], suffixes=("_sc", "_bulk"))
    res = {"created_utc": C.utc_now(),
           "n_pairs_same_ref_alt": int(len(m)),
           "n_pairs_swapped_ref_alt": int(len(m_flip)),
           "sign_concordance_same_ref_alt": float((m.beta_sc * m.beta_bulk > 0).mean()) if len(m) else None,
           "n_unique_gene_variant": int(m[["gene", "var_id"]].drop_duplicates().shape[0]),
           "n_genes": int(m.gene.nunique()),
           "by_dataset": {ds_label[k]: {"n": int(len(g)), "concordance": float((g.beta_sc * g.beta_bulk > 0).mean())}
                          for k, g in m.groupby("dataset_id")},
           "by_cell_type": {k: {"n": int(len(g)), "concordance": float((g.beta_sc * g.beta_bulk > 0).mean())}
                            for k, g in m.groupby("cell_type")},
           "bulk_filter": "eQTL Catalogue gene-level adult brain (CommonMind/ROSMAP/GTEx) pairs with p < 1e-6 from "
                          "Sprint-4 locus extracts (data/interim/sprint4/eqtl); matching on gene symbol via "
                          "data/sprint4/gate_c_query_genes.csv and hg38 chr:pos:REF:ALT",
           "interpretation": ""}
    c = res["sign_concordance_same_ref_alt"]
    if c is None:
        res["interpretation"] = "NOT_TESTABLE: no overlapping pairs"
    elif c >= 0.8:
        res["interpretation"] = "CONSISTENT_WITH_ALT_CODED_SLOPE"
    elif c <= 0.2:
        res["interpretation"] = "CONSISTENT_WITH_REF_CODED_SLOPE"
    else:
        res["interpretation"] = "INCONCLUSIVE"
    out = C.DATA / "brainscope_allele_check.json"
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k not in ("by_cell_type",)}, indent=2))


if __name__ == "__main__":
    main()
