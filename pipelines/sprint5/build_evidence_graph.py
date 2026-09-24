#!/usr/bin/env python3
"""Sprint 5 — master evidence units and the evidence-dependency graph.

Every datum becomes one row of data/sprint5/evidence_units.parquet with: source study, cohort,
phenotype, sample size, ancestry, build, assay, variant, locus, gene, direction, method, v2g class,
independence unit, whether UK Biobank contributes, and which GWAS signal it re-uses.
Edges (data/sprint5/evidence_dependency_graph.parquet) record why two units are NOT independent:
  DERIVED_FROM     a unit computed from another unit's data (coloc/L2G/E2G/AlphaGenome from the GWAS signal)
  SHARES_COHORT    two association units share participants (UKB lineage; Zabaneh HRS inside Davies)
  SHARES_DONORS    two QTL units share donors (GTEx tissues; brainSCOPE vs CommonMind/ROSMAP if overlap)
  AGGREGATES       an aggregator (Open Targets L2G) built from other units' features
  SAME_EQTL_WEIGHTS joint fine-mapping (FOCUS) built from the same eQTL cohorts as the coloc units
Streams that are absent (e.g. AlphaGenome behind an API key) contribute a NOT_TESTABLE status unit,
never a negative unit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

UNITS: list[dict] = []
EDGES: list[dict] = []

BASE = dict(source_study=None, cohort=None, phenotype=None, n=None, ancestry="EUR", build=None, assay=None,
            variant=None, locus_id=None, gene=None, direction=None, method=None, v2g_class=None,
            stream=None, independence_unit=None, ukb_contributes=None, reuses_gwas=None, value=None, p=None,
            status="OK", notes=None)


def unit(uid: str, **kw) -> str:
    r = dict(BASE)
    r.update(kw)
    r["unit_id"] = uid
    UNITS.append(r)
    return uid


def edge(a: str, b: str, kind: str, note: str = "") -> None:
    EDGES.append({"from_unit": a, "to_unit": b, "edge_type": kind, "note": note})


def read(path: Path, **kw):
    if not path.exists():
        return None
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, **kw)


def association_units(loc: pd.DataFrame, locus_of_signal: dict) -> None:
    for lineage, uid, kw in [
        ("LINEAGE:UKB", "LIN_DAVIES", dict(source_study="Davies 2018 (open subset)", cohort="UK Biobank + CHARGE/COGENT incl. HRS",
                                          phenotype="general cognitive function", n=282014, build="GRCh37",
                                          assay="GWAS", ukb_contributes=True)),
        ("LINEAGE:GENC", "LIN_GENC", dict(source_study="NIHR BioResource Genes & Cognition (G&C-only)", cohort="G&C",
                                         phenotype="trail making A (executive function)", n=9932, build="GRCh37",
                                         assay="GWAS", ukb_contributes=False)),
        ("LINEAGE:ZABANEH", "LIN_ZABANEH", dict(source_study="Zabaneh 2018 extreme IQ", cohort="Duke TIP cases + HRS/other controls",
                                               phenotype="extremely high intelligence (case-control)", n=None, build="GRCh37",
                                               assay="GWAS", ukb_contributes=False)),
        ("LINEAGE:WITHIN_FAMILY", "LIN_HOWE", dict(source_study="Howe 2022 within-sibship", cohort="multi-cohort sibships incl. UKB",
                                                  phenotype="cognition", n=9997, build="GRCh37", assay="GWAS",
                                                  ukb_contributes=True, status="NOT_TESTABLE",
                                                  notes="OPENGWAS_JWT absent; files absent")),
    ]:
        unit(uid, stream="LINEAGE", independence_unit=lineage, **kw)
    edge("LIN_ZABANEH", "LIN_DAVIES", "SHARES_COHORT", "HRS controls are inside Davies 2018 (verified Sprint 3.1)")
    for r in loc.itertuples():
        d = unit(f"ASSOC_DAVIES_{r.lead_snp}", stream="ASSOCIATION", source_study="Davies 2018", variant=r.lead_snp,
                 locus_id=locus_of_signal[r.lead_snp], value=r.davies_z, independence_unit="LINEAGE:UKB",
                 ukb_contributes=True, reuses_gwas="Davies2018", method="GWAS lead", phenotype="general cognition",
                 direction=f"cognition-increasing allele {r.cognition_increasing_allele}")
        edge(d, "LIN_DAVIES", "DERIVED_FROM")
        if np.isfinite(r.gc_aligned_z):
            g = unit(f"ASSOC_GENC_{r.lead_snp}", stream="ASSOCIATION", source_study="G&C", variant=r.lead_snp,
                     locus_id=locus_of_signal[r.lead_snp], value=r.gc_aligned_z, independence_unit="LINEAGE:GENC",
                     ukb_contributes=False, reuses_gwas="none (independent sample)", method="aligned z at lead",
                     phenotype="trail making A", notes=f"log10BF={r.log10BF_gc:.3f}")
            edge(g, "LIN_GENC", "DERIVED_FROM")
        if np.isfinite(r.zabaneh_aligned_z):
            z = unit(f"ASSOC_ZAB_{r.lead_snp}", stream="ASSOCIATION", source_study="Zabaneh 2018", variant=r.lead_snp,
                     locus_id=locus_of_signal[r.lead_snp], value=r.zabaneh_aligned_z, independence_unit="LINEAGE:ZABANEH",
                     ukb_contributes=False, reuses_gwas="none; controls overlap Davies (HRS)",
                     method="aligned z at lead", phenotype="extreme IQ", notes="sensitivity only")
            edge(z, "LIN_ZABANEH", "DERIVED_FROM")
        unit(f"ASSOC_HOWE_{r.lead_snp}", stream="ASSOCIATION", source_study="Howe 2022", variant=r.lead_snp,
             locus_id=locus_of_signal[r.lead_snp], independence_unit="LINEAGE:WITHIN_FAMILY", status="NOT_TESTABLE",
             ukb_contributes=True, notes="never NO_EFFECT: access blocked")


def v2g_units(sym_locus: pd.DataFrame) -> None:
    lead_of = sym_locus.drop_duplicates("locus_id").set_index("locus_id").lead_snp.to_dict()

    def parent(lid):
        return f"ASSOC_DAVIES_{lead_of.get(lid)}" if lid in lead_of else "LIN_DAVIES"

    # CODING + ENHANCER (Open Targets variant layer)
    v = read(C.DATA / "v2g_rows_opentargets.parquet")
    for r in v[v.pip_max >= 0.1].itertuples():
        for lid in str(r.locus_id).split(";"):
            for gname in [x for x in str(r.coding_genes or "").split(";") if x and x != "None"]:
                u = unit(f"CODING_{r.rsid}_{gname}_{lid}", stream="V2G", v2g_class="CODING", variant=r.rsid, locus_id=lid,
                         gene=gname, method="VEP (Open Targets 26.06)", assay="sequence annotation",
                         value=r.pip_max, independence_unit="V2G:CODING", reuses_gwas="Davies2018/OT credible set",
                         notes=r.most_severe)
                edge(u, parent(lid), "DERIVED_FROM", "credible variant from the same GWAS signal")
            if isinstance(r.e2g_brain_genes, str):
                for gname in r.e2g_brain_genes.split(";"):
                    u = unit(f"E2G_{r.rsid}_{gname}_{lid}", stream="V2G", v2g_class="ENHANCER_LINK", variant=r.rsid,
                             locus_id=lid, gene=gname, method="ENCODE-rE2G via Open Targets 26.06 (brain biosamples)",
                             assay="chromatin (DNase/ATAC + contacts)", value=r.pip_max,
                             independence_unit="V2G:ENHANCER_LINK:ENCODE", reuses_gwas="Davies2018/OT credible set")
                    edge(u, parent(lid), "DERIVED_FROM")
    # QTL colocalisation (Sprint 4 coloc.abf/coloc.susie + Open Targets Sprint 3 brain coloc rows)
    rows = read(C.S4_DATA / "direction_evidence_rows.csv")
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    loc_of_gene = q.groupby("gene").locus_id.first().to_dict()
    for i, r in enumerate(rows.itertuples()):
        lid = loc_of_gene.get(r.gene)
        u = unit(f"QTL_{r.gene}_{r.dataset_id}_{i}", stream="V2G", v2g_class="QTL", gene=r.gene, locus_id=lid,
                 source_study=r.source, cohort=r.cohort, method="colocalisation PP.H4>=0.8 (gene-level, adult brain)",
                 assay="bulk brain eQTL/pQTL", direction={1: "cognition allele -> HIGHER", -1: "cognition allele -> LOWER"}.get(int(r.sign), "0"),
                 independence_unit=f"QTL_COHORT:{r.cohort}", reuses_gwas=r.gwas_study_id)
        edge(u, parent(lid), "DERIVED_FROM")
        edge(u, f"QTLCOHORT_{r.cohort}", "DERIVED_FROM")
    for c in sorted(set(rows.cohort)):
        unit(f"QTLCOHORT_{c}", stream="QTL_COHORT", cohort=c, independence_unit=f"QTL_COHORT:{c}",
             ukb_contributes=False, notes="GTEx tissues share donors" if c == "gtex" else None)
    # FOCUS (contradiction check only)
    f = read(C.S4_OUT / "joint_gene_tissue_finemapping.csv")
    if f is not None:
        f = f[(f.analysis_config == "joint_brain_gene_x_tissue_p1e-3") & f.gene.notna()]
        for r in f.groupby(["locus_id", "gene"]).gene_pip.sum().reset_index().itertuples():
            u = unit(f"FOCUS_{r.locus_id}_{r.gene}", stream="V2G", v2g_class="NOT_A_CLASS:FOCUS", gene=r.gene,
                     locus_id=r.locus_id, value=r.gene_pip, method="FOCUS joint_brain_gene_x_tissue_p1e-3",
                     independence_unit="CONTRADICTION_CHECK", reuses_gwas="Davies2018")
            edge(u, parent(r.locus_id), "DERIVED_FROM")
            for c in ("gtex", "commonmind"):
                edge(u, f"QTLCOHORT_{c}", "SAME_EQTL_WEIGHTS")
    # L2G (aggregator)
    l2g = read(C.DATA / "ot_l2g_features.parquet")
    ref = read(C.OUT / "opentargets_refresh.csv")
    for r in ref.dropna(subset=["CURRENT_OPEN_TARGETS_ASSIGNMENT"]).itertuples():
        u = unit(f"L2G_{r.locus_id}_{r.CURRENT_OPEN_TARGETS_ASSIGNMENT}", stream="V2G",
                 v2g_class=f"NOT_A_CLASS:L2G->{r.top_shap_class}", gene=r.CURRENT_OPEN_TARGETS_ASSIGNMENT,
                 locus_id=r.locus_id, value=r.current_score, method="Open Targets L2G 26.06",
                 independence_unit="AGGREGATOR", reuses_gwas="cognition credible sets", notes=r.flags)
        edge(u, parent(r.locus_id), "DERIVED_FROM")
        for other in [x for x in UNITS if x["locus_id"] == r.locus_id and x["gene"] == r.CURRENT_OPEN_TARGETS_ASSIGNMENT
                      and x["v2g_class"] in ("QTL", "ENHANCER_LINK", "CODING")]:
            edge(u, other["unit_id"], "AGGREGATES")
    # developmental QTL
    dv = read(C.OUT / "developmental_qtl_coloc.csv")
    if dv is not None and len(dv):
        for r in dv[dv["PP.H4"] >= 0.8].to_dict("records"):
            u = unit(f"DEVQTL_{r['locus_id']}_{r['gene']}_{r['dataset_id']}", stream="V2G_DEVELOPMENTAL",
                     v2g_class="QTL_DEVELOPMENTAL", gene=r["gene"], locus_id=r["locus_id"], cohort=r["study_label"],
                     method="coloc.abf PP.H4>=0.8", assay=f"{r['tissue_label']} ({r['stage_class']})",
                     value=r["PP.H4"], direction=r["direction"], independence_unit=f"QTL_COHORT:{r['study_label']}",
                     reuses_gwas="Davies2018")
            edge(u, parent(r["locus_id"]), "DERIVED_FROM")
    # brainSCOPE
    bs = read(C.OUT / "brainscope_coloc.parquet")
    lk = read(C.OUT / "brainscope_variant_lookup.csv")
    bs_prov = C.REPO_ROOT / "data/raw/sprint5/brainscope/PROVENANCE.json"
    overlap = None
    if bs_prov.exists():
        txt = bs_prov.read_text().lower()
        overlap = ("commonmind" in txt or "cmc" in txt or "rosmap" in txt)
    unit("QTLCOHORT_brainscope", stream="QTL_COHORT", cohort="brainSCOPE (PsychENCODE)",
         independence_unit="QTL_COHORT:brainscope", notes=f"donor overlap with CMC/ROSMAP documented: {overlap}")
    if overlap:
        for c in ("commonmind", "rosmap"):
            edge("QTLCOHORT_brainscope", f"QTLCOHORT_{c}", "SHARES_DONORS")
    if bs is not None and len(bs) and "PP.H4" in bs.columns:
        for i, r in enumerate(bs[bs["PP.H4"] >= 0.8].to_dict("records")):
            u = unit(f"BSCOPE_{r.get('locus_id')}_{r.get('gene')}_{r.get('cell_type')}_{i}", stream="V2G", v2g_class="QTL",
                     gene=r.get("gene"), locus_id=r.get("locus_id"), cohort="brainSCOPE",
                     assay=f"snRNA eQTL {r.get('cell_type')}", method="coloc.abf PP.H4>=0.8",
                     direction=r.get("direction"), independence_unit="QTL_COHORT:brainscope", reuses_gwas="Davies2018")
            edge(u, parent(r.get("locus_id")), "DERIVED_FROM")
            edge(u, "QTLCOHORT_brainscope", "DERIVED_FROM")
    # Sprint 5A: single-cell brain eQTL colocalisation (PP.H4 >= 0.8) -> QTL class (collapses with bulk)
    scf = C.REPO_ROOT / "reports/sprint5a/sc_eqtl_coloc.parquet"
    if C.S5A and scf.exists():
        sc = pd.read_parquet(scf)
        pcol = "PP.H4" if "PP.H4" in sc.columns else next((c for c in sc.columns if "h4" in c.lower()), None)
        gcol = next((c for c in ("gene", "gene_name", "symbol") if c in sc.columns), None)
        ccol = next((c for c in ("cell_type", "celltype", "dataset_id") if c in sc.columns), None)
        dcol = next((c for c in sc.columns if "direction" in c.lower()), None)
        if pcol and gcol:
            for i, r in enumerate(sc[sc[pcol] >= 0.8].to_dict("records")):
                u = unit(f"SCQTL_{r.get('locus_id')}_{r.get(gcol)}_{r.get(ccol)}_{i}", stream="V2G", v2g_class="QTL",
                         gene=r.get(gcol), locus_id=r.get("locus_id"), cohort="single-cell brain eQTL (Sprint 5A)",
                         assay=f"sc-eQTL {r.get('source')} {r.get(ccol)}", method=f"{r.get('method')} PP.H4>=0.8",
                         direction=("cognition allele -> HIGHER" if (r.get("qtl_effect_of_cognition_allele_at_top") or 0) > 0 else
                                    "cognition allele -> LOWER" if (r.get("qtl_effect_of_cognition_allele_at_top") or 0) < 0 else None),
                         independence_unit="QTL_COHORT:single_cell_brain", reuses_gwas="Davies2018")
                edge(u, parent(r.get("locus_id")), "DERIVED_FROM")
                edge(u, "QTLCOHORT_rosmap", "SHARES_DONORS", "single-cell brain eQTL cohorts overlap ROSMAP donors")
    # brainSCOPE lead-variant lookup (coloc NOT_TESTABLE: significant-only release). Recorded as tagging units,
    # never as a QTL-class vote; used for cell-type direction only.
    scd = read(C.OUT / "cell_specific_directionality.csv")
    if scd is not None:
        tags = {"EQTL_LEAD_IN_GWAS_CREDIBLE_SET", "EQTL_LEAD_TAGS_GWAS_LEAD_R2_GE_0.8"}
        for i, r in enumerate(scd[(scd.status == "SIGNIFICANT") & scd.ld_tagging.isin(tags)].to_dict("records")):
            u = unit(f"BSCOPE_TAG_{r['gene']}_{r['cell_type']}_{i}", stream="V2G", v2g_class="NOT_A_CLASS:SC_EQTL_TAG",
                     gene=r["gene"], locus_id=r["locus_id"], cohort="brainSCOPE", assay=f"snRNA pseudobulk eQTL {r['cell_type']}",
                     method=f"lead-variant lookup ({r['ld_tagging']}); coloc NOT_TESTABLE", direction=r["aligned_direction"],
                     independence_unit="QTL_COHORT:brainscope", reuses_gwas="Davies2018",
                     notes="significant-only public release; shares donors with CommonMind (100 MSSM) and ROSMAP (46)")
            edge(u, parent(r["locus_id"]), "DERIVED_FROM")
            edge(u, "QTLCOHORT_brainscope", "DERIVED_FROM")
    # AlphaGenome
    agv = C.REPO_ROOT / "reports/sprint5a/alphagenome_vs_observed.csv"
    if C.S5A and agv.exists():
        # Sprint-5A rule: SEQUENCE_MODEL counts only where a strong brain prediction AGREES with a measured human QTL
        a = pd.read_csv(agv)
        a = a[(a.comparator_tier == "PRIMARY_MEASURED") & (a.agreement == "AGREE")]
        for (lid, g), x in a.groupby(["locus_id", "gene"]):
            for l1 in str(lid).split(";"):
                u = unit(f"AG_{l1}_{g}", stream="V2G", v2g_class="SEQUENCE_MODEL", gene=g, locus_id=l1,
                         method="AlphaGenome Atlas 0.9.0 (|quantile|>=0.99 brain RNA) agreeing with measured QTL",
                         assay="in-silico sequence model", direction=";".join(sorted(set(x.direction_cognition_allele))),
                         value=float(x.max_abs_quantile.max()), independence_unit="MODEL:AlphaGenome",
                         reuses_gwas="Davies2018 credible variants", notes=";".join(sorted(set(x.source)))[:200])
                edge(u, parent(l1), "DERIVED_FROM")
    ag = read(C.OUT / "alphagenome_cognition_variants.parquet")
    if not C.S5A and (ag is None or not len(ag) or ("status" in ag.columns and (ag.status.astype(str).str.startswith("NOT_TESTABLE")).all())):
        unit("ALPHAGENOME_STREAM", stream="V2G", v2g_class="SEQUENCE_MODEL", status="NOT_TESTABLE",
             independence_unit="MODEL:AlphaGenome", notes="see data/sprint5/alphagenome_provenance.json")


def rare_units() -> None:
    rc = read(C.OUT / "rare_coding_evidence.csv")
    if rc is None:
        unit("RARE_STREAM", stream="RARE_CODING", status="NOT_TESTABLE", notes="rare_coding_evidence.csv absent")
        return
    for i, r in enumerate(rc.to_dict("records")):
        ukb = str(r.get("uk_biobank_contributes", "")).upper().startswith("Y")
        u = unit(f"RARE_{r.get('gene')}_{i}", stream="RARE_CODING", v2g_class="RARE_CODING" if str(r.get("exome_wide_significant", "")).upper().startswith("Y") and r.get("phenotype_class") not in ("EA_PROXY", "DD_ID_DISEASE") else "RARE_CODING_SUBTHRESHOLD_OR_PROXY",
                 gene=r.get("gene"), source_study=r.get("study"), cohort=r.get("cohort"), n=r.get("n"),
                 phenotype=r.get("phenotype"), assay="exome/WGS burden", method=r.get("variant_class"),
                 direction=r.get("direction"), p=r.get("p"), value=r.get("effect"),
                 independence_unit=f"RARE:{r.get('cohort')}", ukb_contributes=ukb,
                 reuses_gwas="none (rare variants; same participants as UKB common GWAS if UKB)",
                 notes=r.get("evidence_type"))
        if ukb:
            edge(u, "LIN_DAVIES", "SHARES_COHORT", "same UKB participants, different (rare) variants")


def cnv_units() -> None:
    cv = read(C.OUT / "cnv_positive_dosage.csv")
    if cv is None:
        return
    for i, r in enumerate(cv.to_dict("records")):
        unit(f"CNV_{i}", stream="DOSAGE_CNV", v2g_class="DOSAGE_CNV", gene=r.get("genes"), source_study=r.get("study"),
             direction=r.get("direction"), phenotype=r.get("phenotype"), p=r.get("p"),
             independence_unit=f"CNV:{r.get('study')}",
             ukb_contributes=str(r.get("uk_biobank_contributes", "")).upper().startswith("Y"), notes=r.get("verdict"))


def math_units() -> None:
    m = read(C.DATA / "math53_variants.csv")
    if m is None:
        return
    unit("LIN_MATH", stream="LINEAGE", source_study="Giannelis quantitative-ability GWAS", independence_unit="LINEAGE:MATH",
         notes="see research/sprint5/math_audit.md for cohort overlap")
    for r in m.to_dict("records"):
        u = unit(f"ASSOC_MATH_{r['rsid']}", stream="ASSOCIATION_MATH", variant=r["rsid"], source_study="Giannelis math GWAS",
                 phenotype=r.get("phenotype"), value=r.get("z"), p=r.get("p"), build=r.get("build"),
                 independence_unit="LINEAGE:MATH", notes=r.get("stream_label"))
        edge(u, "LIN_MATH", "DERIVED_FROM")


def main() -> int:
    C.load_rules()
    loc = pd.read_csv(C.OUT / "locus_confidence_rank.csv")
    s4 = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv")
    locus_of_signal = s4.groupby("lead_snp").locus_id.apply(lambda s: ";".join(s)).to_dict()
    association_units(loc, locus_of_signal)
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    s4x = s4[["locus_id", "lead_snp"]]
    v2g_units(s4x)
    rare_units()
    cnv_units()
    math_units()
    # math lineage shares UKB if the audit says so
    ma = C.RESEARCH / "math_audit.md"
    if ma.exists() and "uk biobank" in ma.read_text().lower():
        edge("LIN_MATH", "LIN_DAVIES", "SHARES_COHORT", "math GWAS includes UK Biobank participants (math_audit.md)")
    u = pd.DataFrame(UNITS)
    for col in u.columns:
        if u[col].dtype == object:
            u[col] = u[col].map(lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else str(x))
    e = pd.DataFrame(EDGES).drop_duplicates()
    u.to_parquet(C.DATA / "evidence_units.parquet", index=False)
    e.to_parquet(C.DATA / "evidence_dependency_graph.parquet", index=False)
    print(u.stream.value_counts().to_string())
    print(u.v2g_class.value_counts().to_string())
    print(e.edge_type.value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
