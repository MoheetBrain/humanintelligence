#!/usr/bin/env python3
"""Sprint 5 — AlphaGenome output files (status rows while access is blocked) and the variant-level
AlphaGenome x Open Targets x brainSCOPE x QTL convergence table (brief section 9).

AlphaGenome: pipelines/sprint5/alphagenome_query.py is invoked for both variant sets; without
ALPHAGENOME_API_KEY it exits 3 (NOT_TESTABLE). Every variant then gets a NOT_TESTABLE status row carrying
the blocker — never a null/negative score. If the key is present the query script writes real scores and
this script reads them.

Convergence (one row per credible variant, PIP >= 0.1 at a Gate-C locus): AlphaGenome gene/direction,
Open Targets L2G gene + SHAP driver class, brain E2G gene, brainSCOPE gene/cell/direction (lookup),
adult bulk QTL-coloc gene(s) (Sprint 4, PP.H4 >= 0.8), FOCUS primary gene, coding consequence.
agreement_count = number of sources naming the modal gene; independence_count = number of DISTINCT
independence classes among them (L2G folded into its driver class; FOCUS, bulk coloc and brainSCOPE share
eQTL cohorts/donors -> one QTL class).

Output: reports/sprint5/alphagenome_cognition_variants.parquet, reports/sprint5/alphagenome_variant_predictions.parquet,
        reports/sprint5/alphagenome_math53.csv, reports/sprint5/v2g_convergence.csv
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

AG = C.REPO_ROOT / "pipelines/sprint5/alphagenome_query.py"


def alphagenome(variants: Path, out: Path) -> tuple[str, pd.DataFrame | None]:
    if not os.environ.get("ALPHAGENOME_API_KEY"):
        prov = json.loads((C.DATA / "alphagenome_provenance.json").read_text())
        return f"NOT_TESTABLE: {prov.get('access_status')} — {prov.get('user_action_one_line')}", None
    p = subprocess.run([sys.executable, str(AG), "--variants", str(variants), "--out", str(out)], capture_output=True, text=True)
    if p.returncode != 0 or not out.exists():
        return f"FAILED rc={p.returncode}: {p.stdout[-300:]} {p.stderr[-300:]}", None
    return "OK", pd.read_parquet(out)


def status_rows(v: pd.DataFrame, status: str) -> pd.DataFrame:
    return pd.DataFrame({"rsid": v.rsid, "chr38": v.chr38, "pos38": v.pos38, "allele_string": v.allele_string,
                         "status": status, "avi_score": None, "predicted_expression_gene": None,
                         "predicted_direction": None, "splicing": None, "chromatin_accessibility": None,
                         "histone_tf": None, "brain_tracks": None, "feature_attribution": None,
                         "note": "access blocked: NOT_TESTABLE is never NO_EFFECT"})


def main() -> int:
    C.load_rules()
    qv = pd.read_csv(C.DATA / "query_variants_cognition.csv").drop_duplicates("rsid")
    mv = pd.read_csv(C.DATA / "math53_variants.csv")
    st_c, ag_c = alphagenome(C.DATA / "query_variants_cognition.csv", C.WORK / "alphagenome_cognition_raw.parquet")
    st_m, ag_m = alphagenome(C.DATA / "math53_variants.csv", C.WORK / "alphagenome_math53_raw.parquet")
    cog = ag_c if ag_c is not None else status_rows(qv, st_c)
    math = ag_m if ag_m is not None else status_rows(mv, st_m)
    cog.to_parquet(C.OUT / "alphagenome_cognition_variants.parquet", index=False)
    pd.concat([cog.assign(variant_set="cognition_credible"), math.assign(variant_set="math53")], ignore_index=True) \
        .to_parquet(C.OUT / "alphagenome_variant_predictions.parquet", index=False)
    math.to_csv(C.OUT / "alphagenome_math53.csv", index=False)
    print("AlphaGenome:", st_c[:160])

    # ---- convergence table
    v = pd.read_parquet(C.DATA / "v2g_rows_opentargets.parquet")
    gate = set(pd.read_csv(C.S4_DATA / "gate_c_loci.csv").locus_id)
    v = v[(v.pip_max >= 0.1)]
    v = v[v.locus_id.astype(str).str.split(";").apply(lambda s: bool(set(s) & gate))]
    cs = pd.read_parquet(C.DATA / "ot_variant_credible_sets.parquet")
    l2g = pd.read_parquet(C.DATA / "ot_l2g_features.parquet")
    from build_opentargets_refresh import feature_class
    top = l2g[l2g["rank"] == 1].merge(cs[["rsid", "studyLocusId"]].drop_duplicates(), on="studyLocusId")
    top["cls"] = top.top_shap_feature.astype(str).map(feature_class)
    best = top.sort_values("score", ascending=False).drop_duplicates("rsid").set_index("rsid")
    bs = pd.read_csv(C.OUT / "brainscope_variant_lookup.csv", low_memory=False)
    bs = bs[bs.status == "SIGNIFICANT"]
    bsg = bs.groupby("rsid").apply(lambda g: g.sort_values("pval").iloc[0][["gene", "cell_type", "aligned_direction"]]) if len(bs) else pd.DataFrame()
    co = pd.read_parquet(C.S4_OUT / "adult_brain_susie_coloc.parquet")
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    co = co[co["PP.H4"] >= 0.8].assign(gene=lambda d: d.gene_id.map(sym))
    bulk = co.groupby("locus_id").gene.apply(lambda s: ";".join(sorted(set(s.dropna()))))
    fo = pd.read_csv(C.S4_OUT / "joint_gene_tissue_finemapping.csv")
    fo = fo[fo.analysis_config == "joint_brain_gene_x_tissue_p1e-3"].groupby(["locus_id", "gene"]).gene_pip.sum().reset_index()
    fo_top = fo.sort_values("gene_pip", ascending=False).drop_duplicates("locus_id").set_index("locus_id")
    rows = []
    for r in v.itertuples():
        lids = [x for x in str(r.locus_id).split(";") if x in gate]
        lid = lids[0]
        rec = {"variant": r.rsid, "locus_id": lid, "PIP": round(float(r.pip_max), 3),
               "AlphaGenome_gene": "NOT_TESTABLE", "AlphaGenome_direction": "NOT_TESTABLE",
               "OT_L2G_gene": best.gene.get(r.rsid), "OT_driver": best.cls.get(r.rsid),
               "OT_E2G_brain_gene": r.e2g_brain_best if isinstance(r.e2g_brain_best, str) else None,
               "brainSCOPE_gene": bsg.gene.get(r.rsid) if len(bsg) else None,
               "brainSCOPE_cell": bsg.cell_type.get(r.rsid) if len(bsg) else None,
               "brainSCOPE_direction": bsg.aligned_direction.get(r.rsid) if len(bsg) else None,
               "adult_bulk_QTL_gene": bulk.get(lid), "joint_finemap_gene": fo_top.gene.get(lid) if lid in fo_top.index else None,
               "coding_consequence": f"{r.most_severe}:{r.coding_genes}" if isinstance(r.coding_genes, str) and r.coding_genes else None}
        votes = []  # (gene, class)
        if rec["OT_L2G_gene"]:
            votes.append((rec["OT_L2G_gene"], {"POSITIONAL": "POSITIONAL", "CODING": "CODING", "QTL": "QTL", "ENHANCER": "ENHANCER_LINK"}.get(rec["OT_driver"], "OTHER")))
        if rec["OT_E2G_brain_gene"]:
            votes.append((rec["OT_E2G_brain_gene"], "ENHANCER_LINK"))
        if rec["brainSCOPE_gene"]:
            votes.append((rec["brainSCOPE_gene"], "QTL"))
        for g in str(rec["adult_bulk_QTL_gene"] or "").split(";"):
            if g:
                votes.append((g, "QTL"))
        if rec["joint_finemap_gene"]:
            votes.append((rec["joint_finemap_gene"], "QTL"))
        if isinstance(r.coding_genes, str) and r.coding_genes:
            for g in r.coding_genes.split(";"):
                votes.append((g, "CODING"))
        cnt = Counter(g for g, _ in votes)
        if cnt:
            modal, n = cnt.most_common(1)[0]
            rec["modal_gene"] = modal
            rec["agreement_count"] = n
            rec["independence_count"] = len({c for g, c in votes if g == modal and c not in ("POSITIONAL", "OTHER")})
            rec["competing_genes"] = ";".join(sorted(set(cnt) - {modal}))
        else:
            rec.update(modal_gene=None, agreement_count=0, independence_count=0, competing_genes=None)
        rows.append(rec)
    out = pd.DataFrame(rows).sort_values(["independence_count", "agreement_count", "PIP"], ascending=False)
    out.to_csv(C.OUT / "v2g_convergence.csv", index=False)
    print(out.head(25).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
