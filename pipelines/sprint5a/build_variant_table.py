#!/usr/bin/env python3
"""Sprint 5A section 12 — one canonical table, one row per variant x gene hypothesis (cell types listed per row).

Variants: the 317 AlphaGenome-queried cognition variants (credible variants PIP >= 0.1 at Gate-C loci + every
Sprint-3 locus lead; data/sprint5a/alphagenome_query_cognition.csv). Genes: every gene named for that variant or its
locus by ANY layer (L2G, E2G, bulk coloc, single-cell coloc, brainSCOPE typed evidence, developmental coloc/timing,
GTEx V11 lookup, AlphaGenome strong prediction, FOCUS, coding consequence). Nothing is inferred from nearest gene.
Every column records its own source; NOT_TESTABLE is written explicitly (TGFM, cTWAS).

Output: reports/sprint5a/variant_gene_cell_hypotheses.parquet (+ .csv of the rows with >= 2 non-positional layers)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
O5, O5A, D5, D5A = R / "reports/sprint5", R / "reports/sprint5a", R / "data/sprint5", R / "data/sprint5a"


def rd(p: Path, **kw):
    if not p.exists():
        return None
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, low_memory=False, **kw)


def join(vals) -> str | None:
    vals = [str(v) for v in vals if v is not None and str(v) not in ("", "nan", "None", "<NA>")]
    return ";".join(sorted(set(vals))) or None


def main() -> int:
    q = pd.read_csv(D5A / "alphagenome_query_cognition.csv")
    qv = pd.read_csv(D5 / "query_variants_cognition.csv")
    qv["susie_pip"] = pd.to_numeric(qv.susie_pip, errors="coerce")
    v2g = pd.read_parquet(D5 / "v2g_rows_opentargets.parquet").set_index("rsid")
    lc = pd.read_csv(O5A / "s5_integrated/locus_confidence_rank.csv") if (O5A / "s5_integrated/locus_confidence_rank.csv").exists() \
        else pd.read_csv(O5 / "locus_confidence_rank.csv")
    sig_of = {l: r for r in lc.itertuples() for l in str(r.labels).split(";")}
    cs = pd.read_parquet(D5 / "ot_variant_credible_sets.parquet")
    gw = cs[cs.study_type == "gwas"]
    otl = pd.read_parquet(O5A / "opentargets_2606_refresh.parquet")
    otl = otl.assign(v=otl.variants_json.map(lambda s: [x.get("rsids") for x in json.loads(s)]))
    # variant -> OT L2G rank-1 genes of cognition credible sets containing it
    l2g_of = {}
    for r in otl[otl.l2g_rank == 1].itertuples():
        for rs in (x for lst in r.v if lst for x in lst):
            l2g_of.setdefault(rs, []).append((r.gene, r.driver, r.study_id))
    bulk = pd.read_csv(R / "data/sprint4/direction_evidence_rows.csv")
    q4 = pd.read_csv(R / "data/sprint4/gate_c_query_genes.csv")
    locus_of_gene = q4.groupby("gene").locus_id.first().to_dict()
    bulk["locus_id"] = bulk.gene.map(locus_of_gene)
    dirr = pd.read_csv(O5A / "directionality_resolution_5a.csv").set_index("gene")
    sc = rd(O5A / "sc_eqtl_coloc.parquet")
    sc = sc[sc["PP.H4"] >= 0.8] if sc is not None else pd.DataFrame(columns=["locus_id", "gene"])
    bs = rd(O5A / "brainscope_typed_evidence.parquet")
    bs = bs[bs.evidence_type.isin(["DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT", "REGULATORY_ELEMENT_SUPPORT", "GRN_SUPPORT"])] \
        if bs is not None else pd.DataFrame(columns=["rsid", "gene"])
    dev = pd.read_csv(O5 / "developmental_qtl_coloc.csv")
    dev = dev[dev["PP.H4"] >= 0.8]
    tim = rd(O5A / "regulatory_timing.csv")
    tim = tim.set_index(["locus_id", "gene"]) if tim is not None else None
    gt = rd(O5A / "gtex_v11_gene_direction.csv")
    ag = rd(O5A / "alphagenome_variant_predictions.parquet")
    ag = ag[(ag.set == "cognition_credible") & (ag.modality == "EXPRESSION_RNA_SEQ") & ag.strong] if ag is not None else pd.DataFrame()
    agv = rd(O5A / "alphagenome_vs_observed.csv")
    fo = pd.read_csv(R / "reports/sprint4/joint_gene_tissue_finemapping.csv")
    fo = fo[fo.analysis_config == "joint_brain_gene_x_tissue_p1e-3"].groupby(["locus_id", "gene"]).gene_pip.sum()
    pops = rd(O5A / "pops_scores.csv")
    pops = pops.drop_duplicates("gene").set_index("gene") if pops is not None else None
    rare = json.loads((D5 / "rare_coding_gene_sets.json").read_text())
    cnv = pd.read_csv(O5 / "cnv_positive_dosage.csv")
    cnvg = {g.strip().split(" (")[0] for r in cnv.itertuples() if isinstance(r.genes, str) for g in r.genes.replace(",", ";").split(";")}
    mod = pd.read_csv(O5 / "modifiability_map.csv").set_index("gene")
    m5 = pd.read_csv(O5A / "s5_integrated/causal_gene_evidence_matrix.csv").drop_duplicates("gene").set_index("gene")
    wf = rd(R / "reports/sprint4/within_family_locus_concordance.csv")
    wf = wf.drop_duplicates("locus_id").set_index("locus_id") if wf is not None else None
    math = pd.read_csv(O5 / "math53_gene_mapping.csv")
    math_loci = {l for x in math.in_cognition_locus.dropna() for l in str(x).split(";")}
    lava = rd(O5A / "lava_bivariate_core5.csv")

    rows = []
    for r in q.itertuples():
        rs, lids = r.rsid, [x for x in str(r.locus_id).split(";") if x and x != "nan"]
        lid = lids[0] if lids else None
        s = sig_of.get(lid)
        pip_s = qv[qv.rsid == rs].susie_pip.max()
        vrow = v2g.loc[rs] if rs in v2g.index else None
        genes = set()
        l2g = l2g_of.get(rs, [])
        genes |= {g for g, _, _ in l2g if isinstance(g, str)}
        if vrow is not None:
            genes |= set(str(vrow.e2g_brain_genes or "").split(";")) | set(str(vrow.coding_genes or "").split(";"))
        genes |= set(bulk[bulk.locus_id.isin(lids)].gene) | set(sc[sc.locus_id.isin(lids)].gene) | set(bs[bs.rsid == rs].gene)
        genes |= set(dev[dev.locus_id.isin(lids)].gene) | set(ag[ag.rsid == rs].gene if len(ag) else [])
        genes |= {g for (l, g) in fo.index if l in lids and fo[(l, g)] >= 0.1}
        genes = {g for g in genes if isinstance(g, str) and g and g not in ("nan", "None")}
        for g in sorted(genes):
            b = bulk[(bulk.gene == g) & bulk.locus_id.isin(lids)]
            scg = sc[(sc.gene == g) & sc.locus_id.isin(lids)]
            bsg = bs[(bs.rsid == rs) & (bs.gene == g)]
            dvg = dev[(dev.gene == g) & dev.locus_id.isin(lids)]
            agg = ag[(ag.rsid == rs) & (ag.gene == g)] if len(ag) else pd.DataFrame()
            agc = agv[(agv.rsid == rs) & (agv.gene == g) & (agv.comparator_tier == "PRIMARY_MEASURED")] if agv is not None else pd.DataFrame()
            gtg = gt[(gt.gene == g) & gt.locus_id.isin(lids)] if gt is not None else pd.DataFrame()
            ti = tim.loc[(lid, g)] if tim is not None and (lid, g) in tim.index else None
            if isinstance(ti, pd.DataFrame):
                ti = ti.iloc[0]
            mm = m5.loc[g] if g in m5.index else None
            layers = {"E2G": vrow is not None and g in str(vrow.e2g_brain_genes or "").split(";"),
                      "CODING": vrow is not None and g in str(vrow.coding_genes or "").split(";"),
                      "BULK_QTL": len(b) > 0, "SC_QTL": len(scg) > 0,
                      "BRAINSCOPE": len(bsg[bsg.evidence_type.isin(["DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT"])]) > 0,
                      "DEV_QTL": len(dvg) > 0, "ALPHAGENOME_AGREE": len(agc[agc.agreement == "AGREE"]) > 0}
            rows.append({
                "locus_id": ";".join(lids), "variant_id": rs, "gene": g, "variant_grch38": f"{r.chr38}:{r.pos38}:{r.allele_string}",
                "build": "GRCh38 (GRCh37 source GWAS)", "effect_allele": r.cognition_increasing_allele,
                "cognition_direction": "effect_allele = cognition-increasing (Davies 2018)",
                "PIP": np.nanmax([pip_s, vrow.pip_max if vrow is not None else np.nan]) if (pd.notna(pip_s) or vrow is not None) else np.nan,
                "GWAS_sources": join(gw[gw.rsid == rs].study_id)[:300] if len(gw[gw.rsid == rs]) else None,
                "independent_GWAS_units": (f"G&C z={s.gc_aligned_z:.2f}" + (f"; within-family z={s.wf_aligned_z:.2f}" if "wf_aligned_z" in lc.columns and pd.notna(getattr(s, "wf_aligned_z", np.nan)) else "")) if s is not None else None,
                "locus_stratum": s.locus_stratum if s is not None else None,
                "extreme_IQ_support": f"Zabaneh z={s.zabaneh_aligned_z:.2f} (sensitivity; HRS overlap)" if s is not None and pd.notna(s.zabaneh_aligned_z) else None,
                "math_support": "math-53 SNP in this locus" if lid in math_loci else None,
                "within_family_support": (wf.loc[lid, "classification"] if wf is not None and lid in wf.index else "NOT_TESTABLE"),
                "coding_consequence": (vrow.most_severe if layers["CODING"] else None),
                "rare_variant_support": ("exome-wide LoF (UKB)" if g in rare["exome_wide_cognition"] else
                                         "EA-proxy only" if g in rare["exome_wide_cognition_incl_EA_proxy"] else None),
                "CNV_support": "nominal positive-dosage CNV member" if g in cnvg else None,
                "AlphaGenome_gene": g if len(agg) else None,
                "AlphaGenome_direction": join(agg.direction_cognition_allele) if len(agg) else None,
                "AlphaGenome_feature": join(agg.top_track)[:200] if len(agg) else None,
                "AlphaGenome_vs_measured": join(agc.agreement) if len(agc) else None,
                "OT_L2G_gene": join([x for x, _, _ in l2g if x == g]) or None,
                "OT_L2G_features": join([d for x, d, _ in l2g if x == g]),
                "E2G_gene": g if layers["E2G"] else None,
                "bulk_brain_eQTL_gene": g if len(b) else None,
                "bulk_brain_direction": ({1: "HIGHER", -1: "LOWER"}.get(int(np.sign(b.sign.sum())), "MIXED") if len(b) else None),
                "brainSCOPE_gene": g if len(bsg) else None,
                "brainSCOPE_celltype": join(bsg.cell_type)[:200] if len(bsg) else None,
                "brainSCOPE_direction": join(bsg.aligned_direction) if len(bsg) else None,
                "brainSCOPE_evidence_type": join(bsg.evidence_type) if len(bsg) else None,
                "single_cell_coloc_celltypes": join(scg.source + ":" + scg.cell_type)[:200] if len(scg) else None,
                "single_cell_coloc_direction": join(np.where(scg.qtl_effect_of_cognition_allele_at_top > 0, "HIGHER", "LOWER")) if len(scg) else None,
                "developmental_QTL_gene": g if len(dvg) else None,
                "developmental_direction": join(dvg.direction) if len(dvg) else None,
                "developmental_stage": (ti.timing_class if ti is not None else join(dvg.stage_class) if len(dvg) else None),
                "gtex_v11_direction": join(gtg.v11_direction_cognition_allele) if len(gtg) else None,
                "sQTL": None, "pQTL": None,
                "FOCUS_gene_pip": float(fo[(lid, g)]) if lid is not None and (lid, g) in fo.index else None,
                "TGFM_gene": "NOT_TESTABLE (dbGaP GTEx genotypes)", "cTWAS_gene": "NOT_RUN (genome-wide compute; public inputs)",
                "PoPS_gene_score": float(pops.loc[g].pops_score) if pops is not None and g in pops.index and "pops_score" in pops.columns else None,
                "human_perturbation": (mm.perturbation_note if mm is not None and isinstance(mm.perturbation_note, str) and mm.perturbation_note else None),
                "pleiotropy": None,
                "safety": (str(mod.loc[g].safety_liabilities) if g in mod.index and isinstance(mod.loc[g].safety_liabilities, str) else None),
                "adult_function_evidence": ("adult sc-eQTL coloc" if len(scg) else "adult bulk coloc" if len(b) else
                                            "brainSCOPE adult cell-type QTL (lookup)" if layers["BRAINSCOPE"] else None),
                "direction_label_5a": dirr.label.get(g) if g in dirr.index else None,
                "gene_class_5a": mm.gene_class if mm is not None else None,
                "n_nonpositional_layers": int(sum(layers.values())), "layers": ";".join(k for k, v in layers.items() if v),
                "largest_contradiction": (f"FOCUS favours {mm.focus_primary_other_best}" if mm is not None and bool(mm.focus_contradiction) else
                                          "AlphaGenome direction disagrees with measured QTL" if len(agc[agc.agreement == "DISAGREE"]) else
                                          "single-cell direction disagrees with bulk" if g in dirr.index and dirr.label.get(g) == "UNRESOLVED" and len(scg) else None),
            })
    # sQTL / pQTL from Open Targets 26.06 colocs (H4 >= 0.8, brain for sQTL, any tissue for pQTL)
    co = pd.read_parquet(O5A / "opentargets_2606_colocs.parquet")
    co = co[co.h4 >= 0.8]
    sq = co[co.qtl_type == "sqtl"].groupby("qtl_gene").biosample.apply(lambda s: ";".join(sorted(set(map(str, s))))[:150])
    pq = co[co.qtl_type == "pqtl"].groupby("qtl_gene").qtl_project.apply(lambda s: ";".join(sorted(set(map(str, s))))[:150])
    out = pd.DataFrame(rows)
    out["sQTL"] = out.gene.map(sq)
    out["pQTL"] = out.gene.map(pq)
    if lava is not None:
        lv = lava[lava.p < 0.05 / len(lava)]
        out["local_rg_sharing_bonferroni"] = out.locus_id.map(lambda l: join(lv[lv.locus.isin(str(l).split(";"))].apply(
            lambda x: f"{x.phen1}~{x.phen2}:{x.rho:.2f}", axis=1)) if len(lv) else None)
    out.to_parquet(O5A / "variant_gene_cell_hypotheses.parquet", index=False)
    top = out[out.n_nonpositional_layers >= 2].sort_values(["n_nonpositional_layers", "PIP"], ascending=False)
    top.to_csv(O5A / "variant_gene_cell_hypotheses_top.csv", index=False)
    print(len(out), "variant x gene rows;", len(top), "with >= 2 non-positional layers")
    print(top.groupby(["locus_id", "gene"]).agg(n_var=("variant_id", "nunique"), max_layers=("n_nonpositional_layers", "max"),
                                                 layers=("layers", "first")).sort_values("max_layers", ascending=False).head(30).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
