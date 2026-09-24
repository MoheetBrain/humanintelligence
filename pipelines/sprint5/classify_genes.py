#!/usr/bin/env python3
"""Sprint 5 — gene evidence classes and the four dependency-aware ranks (B-E), per the frozen protocol.

Candidate universe (four panels, none privileged):
  A  every gene in the 36 Sprint-4 Gate-C loci (33 G&C-supported + NEGR1/SYT1 stress tests + 12q13.2)
  B  rare-coding genes (exome-wide incl. EA proxy, and suggestive) and CNV genes
  C  old leads (NEGR1 SYT1 MEF2C RPS26 RHEBL1 WBP2NL ERBB3 BSN CADM2 DCC EXOC4 NT5DC2)
  D  math-53 non-positional genes
Per gene, V2G classes are counted from data/sprint5/evidence_units.parquet (one vote per CLASS, never per
row): CODING, RARE_CODING, QTL (bulk + brainSCOPE collapsed when donors overlap), ENHANCER_LINK,
SEQUENCE_MODEL, DOSAGE_CNV. L2G / FOCUS / nearest gene never vote; FOCUS is the contradiction check.
Outputs: reports/sprint5/causal_gene_evidence_matrix.csv, TOP10_CAUSAL_GENE_CANDIDATES.csv,
         TOP20_RESEARCH_PRIORITY_GENES.csv, data/sprint5/gene_classes.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

PANEL_C = ["NEGR1", "SYT1", "MEF2C", "RPS26", "RHEBL1", "WBP2NL", "ERBB3", "BSN", "CADM2", "DCC", "EXOC4", "NT5DC2"]
CLASSES = ["CODING", "RARE_CODING", "QTL", "QTL_SC", "ENHANCER_LINK", "SEQUENCE_MODEL", "DOSAGE_CNV"]
GENE_ORDER = ["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE", "LOCUS_HIGH_GENE_UNRESOLVED", "CODING_CAUSAL_LOF_ONLY",
              "V2G_SUPPORTED_WEAK_LOCUS", "LIKELY_QTL_PASSENGER", "POSITIVE_DOSAGE_NOMINAL_ONLY",
              "RARE_CODING_SUGGESTIVE_ONLY", "RARE_CODING_EA_PROXY_ONLY", "POSITIONAL_ONLY", "CONTRADICTED",
              "PANEL_ONLY_NO_LOCUS_DATA", "NOT_TESTABLE"]
LOCUS_ORDER = {"L1": 0, "L2": 1, "L3": 2, "L4_DISCORDANT": 3, "NT": 4, None: 5}
DIR_ORDER = {"D1": 0, "D2": 1, "D3": 2, "D4": 3, "D5": 4}
PERT_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "P5": 4}


def locus_table() -> pd.DataFrame:
    lc = pd.read_csv(C.OUT / "locus_confidence_rank.csv")
    rows = []
    for r in lc.itertuples():
        for lid in str(r.labels).split(";"):
            rows.append({"locus_id": lid, "signal": r.lead_snp, "locus_stratum": r.locus_stratum,
                         "log10BF_independent": r.log10BF_independent, "locus_rank": r.rank,
                         "locus_rank_p05": r.rank_p05, "locus_rank_p95": r.rank_p95, "gc_aligned_z": r.gc_aligned_z})
    return pd.DataFrame(rows).set_index("locus_id")


def main() -> int:
    rules = C.load_rules()
    units = pd.read_parquet(C.DATA / "evidence_units.parquet")
    edges = pd.read_parquet(C.DATA / "evidence_dependency_graph.parquet")
    lt = locus_table()
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    gate_loci = set(q.locus_id)
    dev = pd.read_parquet(C.GT_DATA / "developmental_classification.parquet").drop_duplicates("gene_symbol").set_index("gene_symbol")
    d5a = C.REPO_ROOT / "reports/sprint5a/directionality_resolution_5a.csv"
    dirs = pd.read_csv(d5a if (C.S5A and d5a.exists()) else C.S4_OUT / "directionality_resolution.csv").set_index("gene")
    rare = pd.read_csv(C.OUT / "rare_coding_evidence.csv")
    cnv = pd.read_csv(C.OUT / "cnv_positive_dosage.csv")
    sets = json.loads((C.DATA / "rare_coding_gene_sets.json").read_text())
    focus = pd.read_csv(C.S4_OUT / "joint_gene_tissue_finemapping.csv")
    focus = focus[focus.analysis_config == "joint_brain_gene_x_tissue_p1e-3"].groupby(["locus_id", "gene"]).gene_pip.sum()
    math = pd.read_csv(C.OUT / "math53_gene_mapping.csv")
    sc_dir = C.OUT / "cell_specific_directionality.csv"
    scd = pd.read_csv(sc_dir) if sc_dir.exists() else pd.DataFrame()
    donors_overlap = not edges[(edges.edge_type == "SHARES_DONORS") & (edges.from_unit == "QTLCOHORT_brainscope")].empty

    # ---- universe
    uni: dict[str, dict] = {}

    def add(g, panel, lid=None):
        if not isinstance(g, str) or not g or g.startswith("ENSG") or g == "nan":
            return
        d = uni.setdefault(g, {"gene": g, "panels": set(), "loci": set()})
        d["panels"].add(panel)
        if lid:
            d["loci"].add(lid)
    for r in q.itertuples():
        add(r.gene, "A", r.locus_id)
    for g in sets.get("exome_wide_cognition_incl_EA_proxy", []) + sets.get("suggestive_cognition", []):
        add(g, "B")
    for r in cnv.itertuples():
        if str(r.verdict).startswith("NOMINAL") and isinstance(r.genes, str) and len(r.genes.split(";")) <= 6:
            for g in r.genes.replace(",", ";").split(";"):
                add(g.strip().split(" (")[0], "B_CNV")
    for g in PANEL_C:
        add(g, "C")
    for s in math.v2g_nonpositional_genes.dropna():
        for g in str(s).split(";"):
            add(g, "D")
    # attach loci from V2G units (e.g. E2G genes outside the query list)
    v2g = units[units.stream.isin(["V2G", "V2G_DEVELOPMENTAL"]) & units.gene.notna()]
    for r in v2g.itertuples():
        if r.locus_id in gate_loci:
            add(r.gene, "A", r.locus_id)

    # ---- per (locus, gene) classes
    def classes_at(g: str, lid: str) -> dict:
        u = v2g[(v2g.gene == g) & (v2g.locus_id == lid)]
        cl = {}
        cod = u[u.v2g_class == "CODING"]
        if len(cod):
            cl["CODING"] = float(pd.to_numeric(cod.value, errors="coerce").max())
        qb = u[(u.v2g_class == "QTL") & (u.cohort != "brainSCOPE")]
        qs = u[(u.v2g_class == "QTL") & (u.cohort == "brainSCOPE")]
        if len(qb):
            cl["QTL"] = int(qb.independence_unit.nunique())
        if len(qs):
            cl["QTL" if donors_overlap else "QTL_SC"] = cl.get("QTL", 0) + int(qs.assay.nunique()) if donors_overlap else int(qs.assay.nunique())
        if len(u[u.v2g_class == "ENHANCER_LINK"]):
            cl["ENHANCER_LINK"] = int(len(u[u.v2g_class == "ENHANCER_LINK"]))
        if len(u[(u.v2g_class == "SEQUENCE_MODEL") & (u.status == "OK")]):
            cl["SEQUENCE_MODEL"] = 1
        if g in sets.get("exome_wide_cognition", []):
            cl["RARE_CODING"] = 1
        return cl

    per_locus = {}
    for g, d in uni.items():
        for lid in d["loci"]:
            per_locus[(lid, g)] = classes_at(g, lid)
    rows = []
    for g, d in uni.items():
        best = None
        for lid in sorted(d["loci"]) or [None]:
            cl = per_locus.get((lid, g), {}) if lid else {}
            if lid is None and g in sets.get("exome_wide_cognition", []):
                cl = {"RARE_CODING": 1}
            n = len(cl)
            others = {h: len(c) for (l2, h), c in per_locus.items() if l2 == lid and h != g}
            max_other = max(others.values(), default=0)
            focus_loci = set(focus.index.get_level_values(0))
            fpip = (float(focus.get((lid, g), 0.0)) if lid in focus_loci else np.nan) if lid else np.nan
            fother = focus.loc[lid].drop(g, errors="ignore") if lid in focus.index.get_level_values(0) else pd.Series(dtype=float)
            focus_contra = bool(len(fother) and fother.max() >= 0.5 and fpip < 0.2)
            contested = bool(max_other > n or focus_contra)
            ls = lt.loc[lid] if lid in lt.index else None
            rec = {"gene": g, "locus_id": lid, "classes": ";".join(sorted(cl)), "n_classes": n,
                   "class_detail": json.dumps(cl), "max_classes_other_gene_in_locus": max_other,
                   "other_genes_with_classes": ";".join(sorted(h for h, v in others.items() if v)),
                   "focus_primary_pip": round(fpip, 3) if np.isfinite(fpip) else None,
                   "focus_primary_other_best": (f"{fother.idxmax()}:{fother.max():.2f}" if len(fother) else None),
                   "focus_contradiction": focus_contra, "contested": contested,
                   "locus_stratum": ls.locus_stratum if ls is not None else None,
                   "log10BF_independent": float(ls.log10BF_independent) if ls is not None else np.nan,
                   "locus_rank": ls.locus_rank if ls is not None else None,
                   "locus_rank_interval": f"{ls.locus_rank_p05}-{ls.locus_rank_p95}" if ls is not None else None,
                   "gc_aligned_z": ls.gc_aligned_z if ls is not None else np.nan}
            key = (n, -LOCUS_ORDER.get(rec["locus_stratum"], 5))
            if best is None or key > best[0]:
                best = (key, rec)
        rec = best[1]
        rec["panels"] = ";".join(sorted(d["panels"]))
        rec["all_loci"] = ";".join(sorted(d["loci"]))
        rows.append(rec)
    m = pd.DataFrame(rows)

    cnv_genes = {g.strip().split(" (")[0] for r in cnv.itertuples() if str(r.verdict).startswith("NOMINAL") and isinstance(r.genes, str)
                 for g in r.genes.replace(",", ";").split(";")}

    # ---- gene class (precedence as frozen + amendment A1)
    def gene_class(r) -> str:
        cl = set(r.classes.split(";")) - {""}
        ls = r.locus_stratum
        dct = json.loads(r.class_detail)
        tpm = dev.adult_brain_median_tpm.get(r.gene, np.nan)
        has_locus = isinstance(r.locus_id, str) and r.locus_id != "nan"
        if ls == "L4_DISCORDANT" and np.isfinite(r.gc_aligned_z) and r.gc_aligned_z < -1.96:
            return "CONTRADICTED"
        strong_coding = "RARE_CODING" in cl or dct.get("CODING", 0) >= 0.5
        if ls in ("L1", "L2") and strong_coding and len(cl) >= 2 and not r.contested:
            return "CAUSAL_GENE_HIGH"
        if ls in ("L1", "L2", "L3") and ((len(cl) >= 2 and not r.contested) or cl == {"RARE_CODING"}):
            return "CAUSAL_GENE_MODERATE"
        if ("QTL" in cl or "QTL_SC" in cl) and (r.contested or (np.isfinite(tpm) and tpm < 1)):
            return "LIKELY_QTL_PASSENGER"
        if ls in ("L1", "L2"):
            return "LOCUS_HIGH_GENE_UNRESOLVED"
        if r.gene in sets.get("exome_wide_cognition", []) and not has_locus:
            return "CODING_CAUSAL_LOF_ONLY"
        # --- amendment A1 residual labels (below every frozen class)
        if cl and has_locus:
            return "V2G_SUPPORTED_WEAK_LOCUS"
        if r.gene in cnv_genes:
            return "POSITIVE_DOSAGE_NOMINAL_ONLY"
        if r.gene in sets.get("suggestive_cognition", []):
            return "RARE_CODING_SUGGESTIVE_ONLY"
        if r.gene in sets.get("exome_wide_cognition_incl_EA_proxy", []):
            return "RARE_CODING_EA_PROXY_ONLY"
        if has_locus:
            return "POSITIONAL_ONLY"
        return "PANEL_ONLY_NO_LOCUS_DATA"
    m["gene_class"] = m.apply(gene_class, axis=1)
    m["adult_brain_median_tpm_gtex"] = m.gene.map(dev.adult_brain_median_tpm)
    m["developmental_class"] = m.gene.map(dev.developmental_class)
    devq = v2g[v2g.v2g_class == "QTL_DEVELOPMENTAL"].groupby("gene").cohort.apply(lambda s: ";".join(sorted(set(s))))
    m["developmental_qtl"] = m.gene.map(devq)
    adult_q = m.classes.str.contains("QTL")
    m["DEVELOPMENTAL_CAUSAL_ONLY_flag"] = (~adult_q) & (m.developmental_class.eq("PRENATAL_DOMINANT") | m.developmental_qtl.notna()) & m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE", "CODING_CAUSAL_LOF_ONLY"])

    # ---- direction stratum (frozen rule + brainSCOPE cell-type layer; brainSCOPE is NOT an independent cohort)
    tags = {"EQTL_LEAD_IN_GWAS_CREDIBLE_SET", "EQTL_LEAD_TAGS_GWAS_LEAD_R2_GE_0.8"}
    sct = scd[(scd.status == "SIGNIFICANT") & scd.ld_tagging.isin(tags)] if len(scd) else pd.DataFrame(columns=["gene"])
    sc_cells = sct.groupby("gene").cell_type.apply(lambda s: ";".join(sorted(set(s)))).to_dict() if len(sct) else {}
    sc_dirs = sct.groupby("gene").aligned_direction.apply(lambda s: set(s) - {"NOT_ALIGNABLE"}).to_dict() if len(sct) else {}

    def dstrat(r):
        lab = dirs.label.get(r.gene) if r.gene in dirs.index else None
        sd = sc_dirs.get(r.gene, set())
        discordant = len(sd) > 1
        units_ok = r.gene in dirs.index and dirs.rows_n_cohort_units.get(r.gene, 0) >= 2 and dirs.rows_unit_agreement.get(r.gene, 0) >= 0.8
        bulk_sign = dirs.rows_majority_sign.get(r.gene, 0) if r.gene in dirs.index else 0
        sc_agrees = bool(sd) and not discordant and ((bulk_sign > 0 and sd == {"HIGHER"}) or (bulk_sign < 0 and sd == {"LOWER"}))
        if lab == "DIRECTION_RESOLVED" and not discordant:
            return "D1" if r.gene_class in ("CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE") else "D2"
        if lab in ("RESOLVED_ON_ROWS_ONLY_NOT_ROBUST",) or (units_ok and sc_agrees) or (lab == "DIRECTION_RESOLVED" and discordant):
            return "D3"
        if (isinstance(lab, str) and lab.startswith("UNRESOLVED") and lab != "UNRESOLVED_NO_STRONG_COLOC") or sd:
            return "D4"
        return "D5"
    m["direction_stratum"] = m.apply(dstrat, axis=1)
    m["direction_label_sprint4"] = m.gene.map(dirs.label)
    m["brainscope_tagging_celltypes"] = m.gene.map(sc_cells)
    m["brainscope_direction"] = m.gene.map(lambda g: ";".join(sorted(sc_dirs.get(g, set()))) or None)
    m["direction_statement"] = m.gene.map(dirs.direction_statement)
    m["direction_n_rows"] = m.gene.map(dirs.rows_n_rows)
    m["direction_n_cohort_units"] = m.gene.map(dirs.rows_n_cohort_units)

    # ---- perturbation stratum
    ew = set(sets.get("exome_wide_cognition", []))
    ea = set(sets.get("exome_wide_cognition_incl_EA_proxy", [])) - ew
    sug = set(sets.get("suggestive_cognition", []))
    cnvg = {}
    for r in cnv.itertuples():
        if str(r.verdict).startswith("NOMINAL") and isinstance(r.genes, str):
            for g in r.genes.replace(",", ";").split(";"):
                cnvg[g.strip().split(" (")[0]] = r.region_or_gene
    dd = set(sets.get("dd_id_confirmed", []) or [])

    def pstrat(g):
        if g in ew:
            return "P2"  # all exome-wide hits are UK Biobank discoveries; no non-overlapping second cohort -> not P1
        if g in cnvg:
            return "P3"
        if g in dd:
            return "P4"
        return "P5"
    m["perturbation_stratum"] = m.gene.map(pstrat)
    m["perturbation_note"] = m.gene.map(lambda g: "exome-wide PTV burden, carriers WORSE (UKB only; LoF, not GoF)" if g in ew else
                                        "EA_PROXY-only rare-coding (not counted as cognition)" if g in ea else
                                        "suggestive rare-coding only" if g in sug else
                                        f"positive-dosage CNV nominal/unreplicated: {cnvg[g]}" if g in cnvg else
                                        "DD/ID disease gene (DISEASE_ONLY)" if g in dd else "")

    # ---- ranks
    m["gene_class_order"] = m.gene_class.map({c: i for i, c in enumerate(GENE_ORDER)}).fillna(len(GENE_ORDER))
    # amendment A3 (interpretation): causal-gene confidence is ranked only for genes with >=1 V2G class or a
    # rare-coding perturbation; genes without gene-level evidence cannot hold causal-gene confidence and are
    # represented by their locus entity (LOCUS_..._GENE_UNRESOLVED) in the research-priority ranking.
    m["has_gene_level_evidence"] = (m.n_classes > 0) | m.gene.isin(sets.get("exome_wide_cognition", []))
    m = m.sort_values(["has_gene_level_evidence", "gene_class_order", "n_classes", "log10BF_independent"],
                      ascending=[False, True, False, False]).reset_index(drop=True)
    m["rank_B_causal_gene"] = np.where(m.has_gene_level_evidence, np.arange(1, len(m) + 1), np.nan)
    # leave-one-class-out stratum range (rank uncertainty for B)
    def loco(r):
        cl = [c for c in r.classes.split(";") if c]
        if not cl:
            return r.gene_class
        outs = set()
        for drop in cl:
            rest = [c for c in cl if c != drop]
            rr = r.copy()
            rr["classes"] = ";".join(rest)
            dct = json.loads(r.class_detail)
            dct.pop(drop, None)
            rr["class_detail"] = json.dumps(dct)
            outs.add(gene_class(rr))
        return ";".join(sorted(outs))
    m["gene_class_leave_one_class_out"] = m.apply(loco, axis=1)
    # ---- research-priority entities: genes with gene-level / direction / perturbation evidence + unresolved loci
    ent = m[m.has_gene_level_evidence | m.direction_stratum.isin(["D1", "D2", "D3", "D4"])
            | m.perturbation_stratum.isin(["P1", "P2", "P3"])].copy()
    ent["entity_type"] = "GENE"
    lc = pd.read_csv(C.OUT / "locus_confidence_rank.csv")
    resolved_loci = set(m[m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].locus_id.dropna())
    loc_rows = []
    for r in lc[lc.locus_stratum.isin(["L1", "L2"])].itertuples():
        lids = str(r.labels).split(";")
        if set(lids) & resolved_loci:
            continue
        cands = m[m.locus_id.isin(lids) & (m.n_classes > 0)].gene.tolist()
        loc_rows.append({"gene": f"{r.top_gene_labels} locus (gene unresolved)", "entity_type": "LOCUS",
                         "locus_id": ";".join(lids), "gene_class": "LOCUS_HIGH_GENE_UNRESOLVED",
                         "gene_class_order": GENE_ORDER.index("LOCUS_HIGH_GENE_UNRESOLVED"), "n_classes": 0,
                         "classes": "", "locus_stratum": r.locus_stratum, "log10BF_independent": r.log10BF_independent,
                         "locus_rank": r.rank, "locus_rank_interval": f"{r.rank_p05}-{r.rank_p95}",
                         "gc_aligned_z": r.gc_aligned_z, "direction_stratum": "D5", "perturbation_stratum": "P5",
                         "other_genes_with_classes": ";".join(cands), "panels": "A"})
    ent = pd.concat([ent, pd.DataFrame(loc_rows)], ignore_index=True)
    ax = pd.DataFrame({"a": ent.locus_stratum.map(LOCUS_ORDER).fillna(5), "b": ent.gene_class_order,
                       "c": ent.direction_stratum.map(DIR_ORDER), "d": ent.perturbation_stratum.map(PERT_ORDER)}).to_numpy()
    layer = np.zeros(len(ent), int)
    remaining = set(range(len(ent)))
    lv = 0
    while remaining:
        lv += 1
        front = [i for i in remaining if not any(np.all(ax[j] <= ax[i]) and np.any(ax[j] < ax[i]) for j in remaining if j != i)]
        for i in front:
            layer[i] = lv
        remaining -= set(front)
    ent["pareto_layer_E"] = layer
    ent["n_axes_at_best"] = (ax == ax.min(axis=0)).sum(axis=1)
    ent = ent.sort_values(["pareto_layer_E", "n_axes_at_best", "log10BF_independent"], ascending=[True, False, False])
    ent["rank_E_research_priority"] = np.arange(1, len(ent) + 1)
    m = m.merge(ent[ent.entity_type == "GENE"][["gene", "pareto_layer_E", "rank_E_research_priority"]], on="gene", how="left")
    m["rank_A_locus"] = m.locus_rank
    m["rank_C_direction"] = m.direction_stratum.map(DIR_ORDER).rank(method="min").astype(int)
    m["rank_D_perturbation"] = m.perturbation_stratum.map(PERT_ORDER).rank(method="min").astype(int)
    m["question_A_causal_cognition_gene"] = np.where(m.perturbation_stratum.isin(["P1", "P2"]),
                                                     "human LoF burden impairs cognition (UKB)", "no human perturbation evidence")
    m["question_B_natural_high_cognition"] = m.locus_stratum.map({"L1": "locus replicated outside UKB (strong)", "L2": "locus replicated outside UKB (moderate)",
                                                                  "L3": "concordant but weak outside UKB", "L4_DISCORDANT": "not replicated / discordant",
                                                                  "NT": "not testable outside UKB"}).fillna("no common locus")
    m["question_C_adult_modifiable"] = m.direction_stratum.map({"D1": "adult direction resolved for a credible causal gene",
                                                                "D2": "adult eQTL direction resolved but gene assignment not credible",
                                                                "D3": "near-resolved (rows only)", "D4": "partial/single-unit",
                                                                "D5": "no adult direction evidence"})
    m["panels"] = m.panels
    m.to_csv(C.OUT / "causal_gene_evidence_matrix.csv", index=False, float_format="%.4g")
    top10 = m[m.has_gene_level_evidence].sort_values("rank_B_causal_gene").head(10)
    top10.to_csv(C.OUT / "TOP10_CAUSAL_GENE_CANDIDATES.csv", index=False, float_format="%.4g")
    top20 = pd.DataFrame()
    for lv in sorted(ent.pareto_layer_E.unique()):
        top20 = pd.concat([top20, ent[ent.pareto_layer_E == lv]])
        if len(top20) >= 20:
            break
    top20.to_csv(C.OUT / "_top20_core.csv", index=False, float_format="%.4g")
    ent.to_csv(C.OUT / "research_priority_entities.csv", index=False, float_format="%.4g")
    summ = {"n_genes": int(len(m)), "gene_class_counts": m.gene_class.value_counts().to_dict(),
            "direction_strata": m.direction_stratum.value_counts().to_dict(),
            "perturbation_strata": m.perturbation_stratum.value_counts().to_dict(),
            "pareto_layers_used_for_top20": int(top20.pareto_layer_E.max()), "top20_n": int(len(top20)),
            "brainscope_donor_overlap_collapsed": donors_overlap}
    (C.DATA / "gene_classes.json").write_text(json.dumps(summ, indent=2, default=str))
    print(json.dumps(summ, indent=1, default=str))
    pd.set_option("display.width", 250)
    print(top20[["rank_E_research_priority", "pareto_layer_E", "gene", "gene_class", "classes", "locus_stratum", "direction_stratum", "perturbation_stratum"]].to_string(index=False))
    print(m.sort_values("rank_B_causal_gene").head(25)[["rank_B_causal_gene", "gene", "locus_id", "gene_class", "classes", "contested",
                                                         "locus_stratum", "direction_stratum", "perturbation_stratum",
                                                         "gene_class_leave_one_class_out"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
