#!/usr/bin/env python3
"""Sprint 5 — per-locus Open Targets refresh table and per-variant V2G evidence rows.

Inputs: the variant-level Open Targets pull (fetch_opentargets_refresh.py) and the Sprint-3/4 assignments.
For every locus with a cognition credible set in Open Targets:
  CURRENT_OPEN_TARGETS_ASSIGNMENT = top L2G gene over the locus's direct-cognition GWAS credible sets
  (Sprint-3 study tiers direct_strict / direct_mtag; if none, any classified cognition study, flagged),
  with the SHAP contribution of every feature grouped into POSITIONAL / CODING / QTL / ENHANCER / OTHER.
  OLD_SPRINT4_ASSIGNMENT = the Sprint-3 fine-mapping L2G gene carried into Sprint 4 (max score), plus the
  Sprint-3 MAGMA locus label.
Flags follow the frozen protocol (STABLE / CHANGED / POSITIONAL_ONLY / MULTI_GENE_AMBIGUITY).

Also writes data/sprint5/v2g_rows_opentargets.parquet: per credible variant (PIP >= 0.1), the coding
genes, brain E2G genes, and brain QTL credible-set genes (shared-credible-set membership, not coloc).

Output: reports/sprint5/opentargets_refresh.csv, data/sprint5/v2g_rows_opentargets.parquet
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

BRAIN_RX = re.compile(r"brain|cortex|gyrus|caudate|neur|astrocyte|hippoc|cerebell|putamen|thalam|frontal|"
                      r"oligodend|microgl|spinal cord|amygdal|pons|medulla|temporal|parietal|occipital|striat|"
                      r"midbrain|nucleus accumbens|substantia|glutamat|gaba|dopamin|seroton|ependym|floor plate",
                      re.I)
NOT_BRAIN_RX = re.compile(r"renal|lung|liver|gastrocnemius|kidney", re.I)


def feature_class(name: str) -> str:
    if name.startswith(("distance", "geneCount", "proteinGeneCount")):
        return "POSITIONAL"
    if name.startswith("vep"):
        return "CODING"
    if "Qtl" in name:
        return "QTL"
    if name.startswith("e2g"):
        return "ENHANCER"
    return "OTHER"


def is_brain(s) -> bool:
    return isinstance(s, str) and bool(BRAIN_RX.search(s)) and not NOT_BRAIN_RX.search(s)


def main() -> int:
    qv = pd.read_csv(C.DATA / "query_variants_cognition.csv")
    qv["susie_pip"] = pd.to_numeric(qv.susie_pip, errors="coerce")
    qv["ot_pip"] = pd.to_numeric(qv.ot_pip, errors="coerce")
    locus_of = qv.groupby("rsid").locus_id.apply(lambda s: sorted(set(s))).to_dict()
    cs = pd.read_parquet(C.DATA / "ot_variant_credible_sets.parquet")
    l2g = pd.read_parquet(C.DATA / "ot_l2g_features.parquet")
    ann = pd.read_parquet(C.DATA / "ot_variant_annotation.parquet")
    e2g = pd.read_parquet(C.DATA / "ot_e2g.parquet")
    sc = pd.read_csv(C.GT_DATA / "study_classification.csv").set_index("accession_id")
    fm = pd.read_parquet(C.S4_OUT / "locus_finemapping.parquet")
    loci = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv").drop_duplicates("locus_id").set_index("locus_id")

    cs["tier"] = cs.study_id.map(sc.tier)
    cog = cs[(cs.study_type == "gwas") & cs.tier.notna()].copy()
    cog = cog.explode("locus_ids") if False else cog
    cog["locus_id"] = cog.rsid.map(locus_of)
    cog = cog.explode("locus_id")
    rows = []
    for lid, g in cog.groupby("locus_id"):
        prim = g[g.tier.isin(["direct_strict", "direct_mtag"])]
        basis = "direct_strict/direct_mtag"
        if prim.empty:
            prim, basis = g, "any classified cognition-channel study (no direct-tier set) - FLAGGED"
        sl = set(prim.studyLocusId)
        L = l2g[l2g.studyLocusId.isin(sl)].copy()
        rec = {"locus_id": lid, "locus_label_magma": loci.top_gene.get(lid), "n_cognition_credible_sets": len(sl),
               "assignment_basis": basis, "studies": ";".join(sorted(set(prim.study_id)))[:300]}
        # OLD (Sprint-3 fine-mapping rows carried into Sprint 4)
        old = fm[(fm.locus_id == lid) & fm.source.str.contains("Open Targets")].copy()
        old["top_l2g_score"] = pd.to_numeric(old.top_l2g_score, errors="coerce")
        if len(old) and old.top_l2g_score.notna().any():
            o = old.loc[old.top_l2g_score.idxmax()]
            rec.update({"OLD_SPRINT4_ASSIGNMENT": o.top_l2g_gene, "old_score": o.top_l2g_score,
                        "old_driver": o.l2g_driver})
        else:
            rec.update({"OLD_SPRINT4_ASSIGNMENT": None})
        if L.empty:
            rec["CURRENT_OPEN_TARGETS_ASSIGNMENT"] = None
            rec["flags"] = "NO_L2G_FOR_COGNITION_SETS"
            rows.append(rec)
            continue
        best = L.groupby("gene").score.max().sort_values(ascending=False)
        top, s1 = best.index[0], float(best.iloc[0])
        s2 = float(best.iloc[1]) if len(best) > 1 else 0.0
        trow = L[L.gene == top].sort_values("score", ascending=False).iloc[0]
        feats = json.loads(trow.features_json)
        by = {}
        for n, (v, sh) in feats.items():
            by[feature_class(n)] = by.get(feature_class(n), 0.0) + (sh or 0.0)
        # set-level majority of rank-1 genes
        r1 = L[L["rank"] == 1].gene.value_counts()
        rec.update({"CURRENT_OPEN_TARGETS_ASSIGNMENT": top, "current_score": round(s1, 4),
                    "second_gene": best.index[1] if len(best) > 1 else None, "second_score": round(s2, 4),
                    "rank1_majority_gene": r1.index[0], "rank1_majority_frac": round(float(r1.iloc[0] / r1.sum()), 3),
                    "top_shap_feature": trow.top_shap_feature,
                    "top_shap_class": feature_class(str(trow.top_shap_feature)),
                    **{f"shap_{k.lower()}": round(v, 4) for k, v in by.items()},
                    "positive_shap_classes": ";".join(sorted(k for k, v in by.items() if v > 0.01))})
        flags = []
        old_g = rec.get("OLD_SPRINT4_ASSIGNMENT")
        if old_g:
            flags.append("STABLE_ASSIGNMENT" if old_g == top else "CHANGED_ASSIGNMENT")
        else:
            flags.append("NO_OLD_ASSIGNMENT")
        if rec["top_shap_class"] == "POSITIONAL":
            flags.append("POSITIONAL_ONLY")
        if s1 < 0.5 or (s1 - s2) < 0.1:
            flags.append("MULTI_GENE_AMBIGUITY")
        rec["flags"] = ";".join(flags)
        rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(C.OUT / "opentargets_refresh.csv", index=False)
    print(out["flags"].str.split(";").explode().value_counts().to_string())

    # ---- per-variant V2G rows (credible variants only) ----
    v = qv.groupby("rsid").agg(locus_id=("locus_id", lambda s: ";".join(sorted(set(s)))),
                               susie_pip=("susie_pip", "max"), ot_pip=("ot_pip", "max")).reset_index()
    cogpip = cog.groupby("rsid").variant_pip.max()
    v["ot_cog_pip"] = v.rsid.map(cogpip)
    v["pip_max"] = v[["susie_pip", "ot_pip", "ot_cog_pip"]].max(axis=1)
    a = ann.groupby("rsid").agg(coding_genes=("coding_genes", lambda s: ";".join(sorted({g for x in s for g in str(x).split(";") if g}))),
                                most_severe=("most_severe", "first"), variant_id=("variant_id", "first"))
    v = v.merge(a, on="rsid", how="left")
    eb = e2g[e2g.biosample.map(is_brain)]
    eg = eb.groupby("rsid").apply(lambda g: ";".join(f"{x}" for x in sorted(set(g.gene.dropna()))))
    v["e2g_brain_genes"] = v.rsid.map(eg)
    v["e2g_brain_best"] = v.rsid.map(eb.sort_values("score", ascending=False).drop_duplicates("rsid").set_index("rsid").gene)
    q = cs[cs.study_type.isin(["eqtl", "sqtl", "pqtl", "sceqtl", "scsqtl", "tuqtl"]) & cs.biosample.map(is_brain)
           & (pd.to_numeric(cs.variant_pip, errors="coerce") >= 0.01)]
    qg = q.groupby("rsid").apply(lambda g: ";".join(sorted({f"{x.qtl_gene}[{x.study_type}]" for x in g.itertuples() if x.qtl_gene})))
    v["brain_qtl_cs_genes"] = v.rsid.map(qg)
    v.to_parquet(C.DATA / "v2g_rows_opentargets.parquet", index=False)
    print(v[v.pip_max >= 0.1].shape[0], "credible variants with PIP>=0.1;",
          int(v[v.pip_max >= 0.1].coding_genes.fillna("").str.len().gt(0).sum()), "coding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
