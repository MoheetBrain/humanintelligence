#!/usr/bin/env python3
"""Sprint 5 — variant-to-gene mapping of the 53 verified math (Gq) SNPs, and test M3.

Runs AFTER math53_analysis.py (which writes the positional mapping) and fetch_opentargets_refresh.py
--prefix otmath. Adds, per math SNP: coding genes (VEP), brain E2G genes, brain QTL credible-set genes
(membership with variant PIP >= 0.01), the top L2G gene of the credible sets containing it and that call's
SHAP class, brainSCOPE hits (if reports/sprint5/brainscope_math53_lookup.csv exists) and AlphaGenome status.
M3 (frozen): overlap of math-mapped genes (NON-positional mapping only) with cognition candidate genes
(genes holding a CODING / QTL / ENHANCER_LINK unit at a Sprint-4 Gate-C locus).
Output: columns appended to reports/sprint5/math53_gene_mapping.csv; data/sprint5/math_m3_overlap.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from build_opentargets_refresh import feature_class, is_brain  # noqa: E402


def main() -> int:
    C.load_rules()
    mp = pd.read_csv(C.OUT / "math53_gene_mapping.csv")
    mp = mp[[c for c in mp.columns if not c.startswith("v2g_")]]
    ann = pd.read_parquet(C.DATA / "otmath_variant_annotation.parquet")
    e2g = pd.read_parquet(C.DATA / "otmath_e2g.parquet")
    cs = pd.read_parquet(C.DATA / "otmath_variant_credible_sets.parquet")
    l2g = pd.read_parquet(C.DATA / "otmath_l2g_features.parquet")
    coding = ann.groupby("rsid").coding_genes.apply(lambda s: ";".join(sorted({g for x in s for g in str(x).split(";") if g and g != "None"})))
    eb = e2g[e2g.biosample.map(is_brain)]
    e2gg = eb.groupby("rsid").gene.apply(lambda s: ";".join(sorted(set(s.dropna()))))
    q = cs[cs.study_type.isin(["eqtl", "sqtl", "pqtl", "sceqtl", "tuqtl"]) & cs.biosample.map(is_brain)
           & (pd.to_numeric(cs.variant_pip, errors="coerce") >= 0.01)]
    qg = q.groupby("rsid").apply(lambda g: ";".join(sorted({f"{x.qtl_gene}[{x.study_type}]" for x in g.itertuples() if x.qtl_gene})))
    gw = cs[cs.study_type == "gwas"][["rsid", "studyLocusId", "trait"]]
    lt = l2g[l2g["rank"] == 1].merge(gw, on="studyLocusId", how="inner", suffixes=("", "_cs"))
    lt["cls"] = lt.top_shap_feature.astype(str).map(feature_class)
    best = lt.sort_values("score", ascending=False).drop_duplicates("rsid").set_index("rsid")
    mp["v2g_coding_genes"] = mp.rsid.map(coding)
    mp["v2g_brain_e2g_genes"] = mp.rsid.map(e2gg)
    mp["v2g_brain_qtl_cs_genes"] = mp.rsid.map(qg)
    mp["v2g_ot_l2g_top_gene"] = mp.rsid.map(best.gene)
    mp["v2g_ot_l2g_score"] = mp.rsid.map(best.score)
    mp["v2g_ot_l2g_trait"] = mp.rsid.map(best.trait)
    mp["v2g_ot_l2g_shap_class"] = mp.rsid.map(best.cls)
    bs = C.OUT / "brainscope_math53_variant_lookup.csv"
    if bs.exists():
        b = pd.read_csv(bs)
        bb = b[b.status == "SIGNIFICANT"]
        mp["v2g_brainscope"] = mp.rsid.map(bb.groupby("rsid").apply(
            lambda g: ";".join(sorted({f"{x.gene}[{x.cell_type}:{x.aligned_direction}]" for x in g.itertuples()}))))
    else:
        mp["v2g_brainscope"] = "NOT_RUN"
    ag = json.loads((C.DATA / "alphagenome_provenance.json").read_text()) if (C.DATA / "alphagenome_provenance.json").exists() else {}
    mp["v2g_alphagenome"] = str(ag.get("access_status", ag.get("status", "see alphagenome_provenance.json")))[:120]

    def non_positional(r) -> set[str]:
        s = set()
        if isinstance(r.get("v2g_brainscope"), str) and r["v2g_brainscope"] != "NOT_RUN":
            s |= {x.split("[")[0] for x in r["v2g_brainscope"].split(";")}
        for col in ("v2g_coding_genes", "v2g_brain_e2g_genes"):
            if isinstance(r[col], str):
                s |= set(r[col].split(";"))
        if isinstance(r["v2g_brain_qtl_cs_genes"], str):
            s |= {x.split("[")[0] for x in r["v2g_brain_qtl_cs_genes"].split(";")}
        if isinstance(r["v2g_ot_l2g_top_gene"], str) and r["v2g_ot_l2g_shap_class"] != "POSITIONAL":
            s.add(r["v2g_ot_l2g_top_gene"])
        return {x for x in s if x and not x.startswith("ENSG")}
    mp["v2g_nonpositional_genes"] = mp.apply(lambda r: ";".join(sorted(non_positional(r))), axis=1)
    mp.to_csv(C.OUT / "math53_gene_mapping.csv", index=False)
    units = pd.read_parquet(C.DATA / "evidence_units.parquet") if (C.DATA / "evidence_units.parquet").exists() else None
    cog = set()
    if units is not None:
        cog = set(units[units.v2g_class.isin(["CODING", "QTL", "ENHANCER_LINK"])].gene.dropna())
    mg = {g for x in mp.v2g_nonpositional_genes for g in str(x).split(";") if g}
    ov = sorted(mg & cog)
    res = {"n_math_snps": int(len(mp)), "n_math_nonpositional_genes": len(mg), "n_cognition_candidate_genes": len(cog),
           "overlap_genes": ov,
           "overlap_detail": mp[mp.v2g_nonpositional_genes.fillna("").apply(lambda s: bool(set(s.split(";")) & set(ov)))][
               ["rsid", "overlap_class", "g_direction_vs_davies", "v2g_nonpositional_genes", "in_cognition_locus"]].to_dict("records"),
           "caveat": "math Gq is fixed orthogonal to g and partly built from UKB-containing CP/EA GWAS; 15 of 35 Sprint-4 "
                     "fine-mapped loci already use 23andMe math credible sets -> gene overlap is not independent support"}
    (C.DATA / "math_m3_overlap.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "overlap_detail"}, indent=1))
    print(mp[["rsid", "nearest_gene_label_only", "overlap_class", "v2g_coding_genes", "v2g_brain_e2g_genes",
              "v2g_ot_l2g_top_gene", "v2g_ot_l2g_shap_class"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
