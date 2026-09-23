#!/usr/bin/env python3
"""Sprint 5 — assemble TOP20_RESEARCH_PRIORITY_GENES.csv, negative_results.csv and
evidence_dependency_summary.md from the computed layers (no new statistics here).

Every text field is rule-derived from the evidence tables (so it can be regenerated), except where a
gene dossier exists, in which case its 'Largest contradiction' / 'Missing causal arrow' sections are
quoted (first sentence) and the dossier path is given.
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


def dossier_section(gene: str, title_rx: str) -> str | None:
    f = C.OUT / "gene_dossiers" / f"{gene}.md"
    if not f.exists():
        return None
    txt = f.read_text()
    m = re.search(rf"^#+\s*\d*\.?\s*{title_rx}[^\n]*\n+(.+?)(?=\n#+\s|\Z)", txt, re.S | re.M | re.I)
    if not m:
        return None
    body = " ".join(line.strip("-* ").strip() for line in m.group(1).strip().splitlines() if line.strip())
    body = re.sub(r"\s+", " ", body)
    return body[:400]


def main() -> int:
    C.load_rules()
    m = pd.read_csv(C.OUT / "causal_gene_evidence_matrix.csv")
    ent = pd.read_csv(C.OUT / "research_priority_entities.csv")
    top = pd.read_csv(C.OUT / "_top20_core.csv")
    lc = pd.read_csv(C.OUT / "locus_confidence_rank.csv")
    mod = pd.read_csv(C.OUT / "modifiability_map.csv").set_index("gene")
    math = pd.read_csv(C.OUT / "math53_gene_mapping.csv")
    dev = pd.read_csv(C.OUT / "developmental_qtl_coloc.csv") if (C.OUT / "developmental_qtl_coloc.csv").exists() else pd.DataFrame()
    ref = pd.read_csv(C.OUT / "opentargets_refresh.csv").set_index("locus_id")
    rare = pd.read_csv(C.OUT / "rare_coding_evidence.csv")
    sig_of = {}
    for r in lc.itertuples():
        for lid in str(r.labels).split(";"):
            sig_of[lid] = r
    mg = {}
    for r in math.itertuples():
        for g in str(r.v2g_nonpositional_genes).split(";"):
            if g and g != "nan":
                mg.setdefault(g, []).append(f"{r.rsid} ({r.overlap_class})")
    rows = []
    for r in top.itertuples():
        g = r.gene
        lid = r.locus_id if isinstance(r.locus_id, str) else None
        s = sig_of.get(lid.split(";")[0]) if lid else None
        streams = []
        if s is not None:
            streams.append(f"G&C trail-making aligned z={s.gc_aligned_z:.2f} (UKB-free; counted)")
            if np.isfinite(s.genlang_piq_aligned_z):
                streams.append(f"GenLang PIQ z={s.genlang_piq_aligned_z:.2f} (sensitivity: BATS overlap)")
            if np.isfinite(s.zabaneh_aligned_z):
                streams.append(f"Zabaneh extreme-IQ z={s.zabaneh_aligned_z:.2f} (sensitivity: HRS overlap)")
            streams.append("within-family: NOT_TESTABLE")
        rr = rare[rare.gene == g]
        coding = []
        cd = json.loads(r.class_detail) if isinstance(getattr(r, "class_detail", None), str) else {}
        if "CODING" in cd:
            coding.append(f"credible missense PIP={cd['CODING']:.2f}")
        if len(rr):
            ew = rr[rr.exome_wide_significant.astype(str).str.upper().str.startswith("Y")]
            coding.append("; ".join(f"{x.study.split(' et al')[0]} {x.phenotype_class} P={x.p}" for x in ew.itertuples())[:250] or "sub-threshold rare-coding only")
        d = dev[(dev.get("gene", pd.Series(dtype=str)) == g) & (dev.get("PP.H4", pd.Series(dtype=float)) >= 0.8)] if len(dev) else pd.DataFrame()
        mrow = mod.loc[g] if g in mod.index else None
        rec = {
            "rank_E": int(r.rank_E_research_priority), "pareto_layer": int(r.pareto_layer_E),
            "gene_or_locus": g, "entity_type": r.entity_type, "locus_id": lid,
            "why_entered": f"panels {r.panels}; class {r.gene_class}; locus {r.locus_stratum}; direction {r.direction_stratum}; perturbation {r.perturbation_stratum}",
            "independent_human_evidence_streams": " | ".join(streams) or ("rare-coding (UKB only)" if len(rr) else "none"),
            "coding_evidence": "; ".join(coding) or "none",
            "common_regulatory_evidence": (r.classes if isinstance(r.classes, str) and r.classes else "none"),
            "math_evidence": "; ".join(mg.get(g, [])) or "none (no non-positional math-53 mapping)",
            "extreme_iq_evidence": (f"Zabaneh aligned z={s.zabaneh_aligned_z:.2f} (sensitivity only)" if s is not None and np.isfinite(s.zabaneh_aligned_z) else "none"),
            "brainSCOPE": (f"{r.brainscope_direction} in {r.brainscope_tagging_celltypes} (lookup; coloc NOT_TESTABLE)" if isinstance(getattr(r, "brainscope_tagging_celltypes", None), str) else "no tagging cell-type eQTL (coloc NOT_TESTABLE)"),
            "AlphaGenome": "NOT_TESTABLE (API key blocker)",
            "Open_Targets": (f"L2G {ref.CURRENT_OPEN_TARGETS_ASSIGNMENT.get(lid.split(';')[0])} ({ref.top_shap_class.get(lid.split(';')[0])}); {ref['flags'].get(lid.split(';')[0])}" if lid and lid.split(';')[0] in ref.index else "no cognition credible set"),
            "adult_QTL": (f"{r.direction_label_sprint4}; {r.direction_statement}" if isinstance(getattr(r, "direction_label_sprint4", None), str) else "no strong gene-level adult coloc"),
            "developmental_QTL": (";".join(sorted(set(d.study_label))) + " (PP.H4>=0.8)") if len(d) else "none strong (fetal/progenitor/BrainSeq tested)",
            "cell_type": (r.brainscope_tagging_celltypes if isinstance(getattr(r, "brainscope_tagging_celltypes", None), str) else "unresolved"),
            "direction": (r.direction_statement if isinstance(getattr(r, "direction_statement", None), str) else "unresolved"),
            "human_perturbation": (r.perturbation_note if isinstance(getattr(r, "perturbation_note", None), str) and r.perturbation_note else "none"),
            "pleiotropy_safety": (str(mrow.safety_liabilities) if mrow is not None and isinstance(mrow.safety_liabilities, str) else "not auto-cleared; see dossier") ,
            "largest_contradiction": dossier_section(g, "Largest contradiction") or (
                f"FOCUS primary favours {r.focus_primary_other_best}" if isinstance(getattr(r, "focus_primary_other_best", None), str) and getattr(r, "focus_contradiction", False)
                else "UKB-only discovery; LoF-only direction" if r.perturbation_stratum == "P2" else "not yet assessed"),
            "missing_causal_arrow": dossier_section(g, "Missing causal arrow") or (
                "gene assignment (variant->gene)" if r.gene_class in ("LOCUS_HIGH_GENE_UNRESOLVED", "LIKELY_QTL_PASSENGER") else
                "common-variant link and direction (rare LoF only)" if r.perturbation_stratum == "P2" else "adult direction / independent replication"),
            "single_best_next_computation": (
                "coloc.susie against open single-cell brain eQTL (Bryois 2022) + AlphaGenome brain tracks (key needed)" if r.gene_class in ("LOCUS_HIGH_GENE_UNRESOLVED", "LIKELY_QTL_PASSENGER", "CAUSAL_GENE_MODERATE") else
                "gene-based within-family test once Gate A unlocks; rare-variant replication outside UKB" if r.perturbation_stratum == "P2" else
                "replication of the CNV association outside UK Biobank" if r.perturbation_stratum == "P3" else "within-family locus test (Gate A)"),
            "dossier": f"reports/sprint5/gene_dossiers/{g}.md" if (C.OUT / "gene_dossiers" / f"{g}.md").exists() else None,
        }
        rows.append(rec)
    t20 = pd.DataFrame(rows)
    t20.to_csv(C.OUT / "TOP20_RESEARCH_PRIORITY_GENES.csv", index=False)

    # ---- negative results (first-class)
    neg = []
    def add(kind, subject, result, status, source):
        neg.append({"category": kind, "subject": subject, "result": result, "status": status, "evidence_file": source})
    for r in lc[lc.locus_stratum == "L4_DISCORDANT"].itertuples():
        add("LOCUS_NOT_REPLICATED_OUTSIDE_UKB", f"{r.lead_snp} ({r.top_gene_labels})",
            f"G&C aligned z={r.gc_aligned_z:.2f}; log10BF={r.log10BF_independent:.2f}", "NEGATIVE_AT_THIS_POWER (not NO_EFFECT)", "reports/sprint5/locus_confidence_rank.csv")
    for r in lc[lc.locus_stratum == "NT"].itertuples():
        add("LOCUS_NOT_TESTABLE", f"{r.lead_snp} ({r.top_gene_labels})", "no G&C allele alignment/proxy", "NOT_TESTABLE", "reports/sprint5/locus_confidence_rank.csv")
    for r in m[m.gene_class == "LOCUS_HIGH_GENE_UNRESOLVED"].drop_duplicates("locus_id").itertuples():
        add("LOCUS_REPLICATES_GENE_UNRESOLVED", f"{r.locus_id}", f"locus {r.locus_stratum}; no gene with >=2 V2G classes", "UNRESOLVED", "reports/sprint5/causal_gene_evidence_matrix.csv")
    for r in m[m.gene_class == "LIKELY_QTL_PASSENGER"].itertuples():
        add("LIKELY_QTL_PASSENGER", r.gene, f"QTL present but contested (FOCUS other={r.focus_primary_other_best}; other genes with classes={r.other_genes_with_classes})", "DOWNGRADED", "reports/sprint5/causal_gene_evidence_matrix.csv")
    rf = ref.reset_index()
    for r in rf[rf["flags"].astype(str).str.contains("CHANGED")].itertuples():
        add("OPEN_TARGETS_ASSIGNMENT_CHANGE", r.locus_id, f"{r.OLD_SPRINT4_ASSIGNMENT} -> {r.CURRENT_OPEN_TARGETS_ASSIGNMENT} (same release 26.06; broader credible-set coverage)", "CHANGED", "reports/sprint5/opentargets_refresh.csv")
    add("OPEN_TARGETS_POSITIONAL", "117 of 130 loci", "top L2G SHAP feature positional", "UNINFORMATIVE_FOR_GENE", "reports/sprint5/opentargets_refresh.csv")
    add("ALPHAGENOME", "all cognition + math-53 variants", "API key required", "NOT_TESTABLE", "data/sprint5/alphagenome_provenance.json")
    add("BRAINSCOPE_COLOC", "all loci x genes x cell types", "significant-only public release; genotypes controlled", "NOT_TESTABLE", "reports/sprint5/brainscope_coloc.parquet")
    add("BRAINSCOPE_NULLS", "ATXN2L AKAP6 EXT1 DCC KCNJ3 CACNA1I PTPRT CLCN2 SYT1 MEF2C RHEBL1 ERBB3 BSN KDM5B DDN SFMBT1 DPP4 ...",
        "tested in 17 cell types, no significant eQTL for the query variants", "NULL_AT_THIS_POWER", "reports/sprint5/cell_specific_directionality.csv")
    add("BRAINSCOPE_SEPARATE_EQTL", "NEGR1 (Lamp5), EXOC4 (L5 IT)", "cell-type eQTL lead not in LD with the GWAS signal (r2 0.02 / 0.12)", "NOT_THE_GWAS_SIGNAL", "reports/sprint5/cell_specific_directionality.csv")
    add("CELL_TYPE_OPPOSITE_DIRECTIONS", "all tagging genes", "no gene showed opposite significant directions across cell types or vs bulk", "NONE_FOUND", "reports/sprint5/cell_specific_directionality.csv")
    conv = pd.read_csv(C.OUT / "common_rare_convergence.csv")
    for r in conv.itertuples():
        add("COMMON_RARE_CONVERGENCE", r.gene_set, f"T1 P={r.T1_mean_z_P_one_sided:.2f}; T2 P={r.T2_frac_in_loci_P_one_sided:.2f}; T3 P={r.T3_n_in_fdr_sets_P_one_sided:.2f}; T4 P={r.T4_fisher_P}; T5 P={r.T5_fisher_P}", "NULL_UNDERPOWERED (not evidence of separate biology)", "reports/sprint5/common_rare_convergence.csv")
    for r in rare[rare.exome_wide_significant.astype(str).str.upper().str.startswith("Y")].drop_duplicates("gene").itertuples():
        add("RARE_CODING_DISEASE_TRADEOFF_OR_LOF_ONLY", r.gene, f"{r.direction}; disease: {r.disease_association}", "LOF_ONLY_NOT_ENHANCEMENT", "reports/sprint5/rare_coding_evidence.csv")
    cnv = pd.read_csv(C.OUT / "cnv_positive_dosage.csv")
    for r in cnv.itertuples():
        if r.verdict != "SUPPORTED_POSITIVE_DOSAGE":
            add("POSITIVE_DOSAGE", r.region_or_gene, str(r.direction)[:160], r.verdict, "reports/sprint5/cnv_positive_dosage.csv")
    for r in math[math.overlap_class == "MATH_SPECIFIC_ORTHOGONAL"].itertuples():
        add("MATH_LOCUS_NO_GENERAL_COGNITION_OVERLAP", r.rsid, f"Davies P={r.davies_p}; nearest label {r.nearest_gene_label_only}", "MATH_SPECIFIC_PROXY", "reports/sprint5/math53_gene_mapping.csv")
    add("MATH_DIRECTION", "math-53 vs Davies g", "17/53 math-raising alleles raise g (P=0.013); 11/13 Bonferroni SNPs inverted (model artefact of partialling g)", "INVERTED_BY_CONSTRUCTION", "data/sprint5/math53_summary.json")
    add("GATE_A_WITHIN_FAMILY", "159 loci", "OPENGWAS_JWT absent; files absent", "NOT_TESTABLE", "data/sprint4/gate_a_access.json")
    add("NEW_INDEPENDENT_LINEAGE", "GenLang PIQ (N=18,722)", "106/141 concordant, slope 0.173; BATS cohort overlaps Davies -> sensitivity only", "PARTIAL_OVERLAP", "data/sprint5/genlang_overlap.json")
    if len(dev):
        nd = dev[dev["PP.H4"] < 0.8]
        add("DEVELOPMENTAL_QTL", "36 loci x fetal/progenitor/BrainSeq", f"{int((dev['PP.H4'] >= 0.8).sum())} strong of {len(dev)} tested", "SEE_TABLE", "reports/sprint5/developmental_qtl_coloc.csv")
    gs = C.DATA / "grn_sensitivity.csv"
    if gs.exists():
        add("GRN_ENHANCER_SENSITIVITY", "RHEBL1 (L7009)",
            "counting brainSCOPE GRN element->gene links would give RHEBL1 a 2nd class (MODERATE -> D1); the element links 9 genes "
            "(RHEBL1, DDN, PRKAG1, CACNB3, ARF3, KCNH3, RND1, SPATS2, TUBA1B), i.e. non-discriminating",
            "NOT_COUNTED_UNDER_FROZEN_DEFINITION", "data/sprint5/grn_sensitivity.csv")
    add("CYP2D6_STRUCTURAL_CONFOUND", "CYP2D6 (L1565)",
        "lead rs28670611 r2=1.00 with CYP2D6 S486T (rs1135840); ~28% carry CYP2D6/CYP2D7 hybrids/CNVs; eQTL/FOCUS assignment not haplotype/CNV-adjusted",
        "GENE_CALL_UNRELIABLE", "reports/sprint5/gene_dossiers/CYP2D6.md")
    add("ALIAS_GAP", "ZFTRAF1 (CYHR1)",
        "DDG2P G2P03563 (limited confidence) and a brainSCOPE GRN promoter link are filed under the previous symbol CYHR1; perturbation "
        "stratum stays P5 because only definitive/strong DDG2P genes enter P4", "DISCLOSED", "reports/sprint5/gene_dossiers/ZFTRAF1.md")
    pd.DataFrame(neg).to_csv(C.OUT / "negative_results.csv", index=False)

    # ---- dependency summary
    u = pd.read_parquet(C.DATA / "evidence_units.parquet")
    e = pd.read_parquet(C.DATA / "evidence_dependency_graph.parquet")
    lines = ["# Evidence dependency summary (Sprint 5)", "",
             f"*Generated {C.utc_now()} from `data/sprint5/evidence_units.parquet` ({len(u)} units) and "
             f"`data/sprint5/evidence_dependency_graph.parquet` ({len(e)} edges).*", "",
             "## Why this exists", "",
             "- Many evidence streams descend from the **same UK-Biobank-dominated association signal**.",
             "- Fine-mapping, L2G, colocalisation, FOCUS, E2G overlap and brainSCOPE look-ups are therefore **not replications**.",
             "- Here every datum is a unit, and every reason two units are not independent is an edge.", "",
             "## Units by stream", "", "| stream | units |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in u.stream.value_counts().items()]
    lines += ["", "## Units by variant-to-gene class (NOT_A_CLASS = never a vote)", "", "| class | units |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in u.v2g_class.value_counts().items()]
    lines += ["", "## Dependency edges", "", "| edge type | n | meaning |", "|---|---|---|"]
    meaning = {"DERIVED_FROM": "computed from another unit's data (the GWAS signal, a QTL cohort)",
               "SHARES_COHORT": "overlapping participants (UKB lineage; HRS in Zabaneh and Davies; UKB rare-coding)",
               "SHARES_DONORS": "brainSCOPE donors include CommonMind (100 MSSM) and ROSMAP (46)",
               "AGGREGATES": "Open Targets L2G built from coding/QTL/E2G features already counted",
               "SAME_EQTL_WEIGHTS": "FOCUS built on the same GTEx/CommonMind eQTL cohorts as the coloc units"}
    lines += [f"| {k} | {v} | {meaning.get(k, '')} |" for k, v in e.edge_type.value_counts().items()]
    lin = u[u.stream == "LINEAGE"]
    lines += ["", "## Association lineages and their independence", "", "| lineage | UKB | status | counted as replication |", "|---|---|---|---|"]
    counted = {"LINEAGE:UKB": "no (discovery)", "LINEAGE:GENC": "YES",
               "LINEAGE:ZABANEH": "sensitivity only (HRS inside Davies)",
               "LINEAGE:WITHIN_FAMILY": "would count; NOT_TESTABLE",
               "LINEAGE:MATH": "no (UKB-containing CP/EA anchors; 23andMe math items)"}
    lines += [f"| {r.source_study} | {r.ukb_contributes} | {r.status} | {counted.get(r.independence_unit, '')} |" for r in lin.itertuples()]
    lines += ["| GenLang performance IQ (Eising 2022) | False | OK | sensitivity only (BATS cohort shared with Davies 2018) |", "",
              "## Consequences for this sprint", "",
              "- **Locus confidence.** Only **G&C** counts as independent. GenLang, Zabaneh and the math factor are sensitivity lines. Within-family data are NOT_TESTABLE.",
              "- **Gene assignment.** One vote per class: CODING, RARE_CODING, QTL, ENHANCER_LINK, SEQUENCE_MODEL, DOSAGE_CNV.",
              "  - Bulk eQTL cohorts, FOCUS and brainSCOPE collapse into a single QTL class, because they share donors and weights.",
              "  - L2G never votes.",
              "- **Rare coding.** Every exome-wide gene comes from UK Biobank participants.",
              "  - These are different variants, so they do not duplicate the common signal.",
              "  - They are not replication either: they are one cohort.",
              "- **Math.** The math GWAS shares UKB through its factor anchors, and 15 of 35 Sprint-4 fine-mapped loci already use 23andMe math credible sets. Math overlap is pleiotropy, not independent support.", ""]
    (C.OUT / "evidence_dependency_summary.md").write_text("\n".join(lines))
    print(t20[["rank_E", "gene_or_locus", "entity_type"]].to_string(index=False))
    print(len(neg), "negative-result rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
