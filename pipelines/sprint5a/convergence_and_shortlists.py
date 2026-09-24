#!/usr/bin/env python3
"""Sprint 5A sections 13-14 — dependency-aware cross-phenotype convergence and the three shortlists.

Convergence is NOT an intersection count. Per locus it uses:
  * LAVA local genetic correlation (overlap-corrected via LDSC cross-trait intercepts) between Davies g and
    executive function (G&C), performance IQ (GenLang), extreme IQ (Zabaneh), objective arithmetic (UKB FI4);
    significant = Bonferroni over all bivariate tests; nominal P < 0.05 reported separately;
  * HyPrColoc cognition + brain-eQTL clusters (overlapping samples -> descriptive);
  * math-53 (Gq, self-report proxy; UKB-containing anchors) SNPs inside the locus;
  * rare-coding exome-wide genes inside the locus; adult single-cell eQTL colocalisation genes.
Every category states its dependence (UKB: Davies/FI4/math anchors/rare coding; HRS: Davies/Zabaneh; BATS: Davies/GenLang).

Shortlists (frozen Sprint-5A protocol):
  A causal cognition genes: human perturbation (exome-wide LoF) + CAUSAL_GENE_MODERATE/HIGH + single-variant coding PIP>=0.5
  B exceptional/quantitative: loci whose EXTREME or ARITHMETIC local rg with g is significant, with the gene status there
  C adult-modifiable research candidates: adult intervention gate criteria 1-4 (independent locus L1/L2, credible gene
    MODERATE+, adult brain QTL, direction D1). Not forced: empty is reported as empty, near-misses listed separately.
Outputs: reports/sprint5a/cross_phenotype_convergence.csv, reports/sprint5a/SHORTLIST_{A,B,C}_*.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
O5A, O5, D5 = R / "reports/sprint5a", R / "reports/sprint5", R / "data/sprint5"
INT = O5A / "s5_integrated"


def main() -> int:
    lava = pd.read_csv(O5A / "lava_bivariate_core5.csv")
    nb = len(lava)
    lava["bonf"] = lava.p < 0.05 / nb
    lc = pd.read_csv(INT / "locus_confidence_rank.csv")
    loc = pd.read_csv(R / "data/sprint5a/lava_loci.tsv", sep="\t")
    m = pd.read_csv(INT / "causal_gene_evidence_matrix.csv")
    sc = pd.read_parquet(O5A / "sc_eqtl_coloc.parquet")
    sc = sc[sc["PP.H4"] >= 0.8]
    mt = pd.read_csv(O5A / "multitrait_coloc.csv")
    math = pd.read_csv(O5 / "math53_gene_mapping.csv")
    rare = json.loads((D5 / "rare_coding_gene_sets.json").read_text())
    strat = {l: r for r in lc.itertuples() for l in str(r.labels).split(";")}
    pair = {("DAVIES", "GENC_TMA"): "GENERAL+EXECUTIVE", ("DAVIES", "GENLANG_PIQ"): "GENERAL+PERFORMANCE_IQ",
            ("DAVIES", "ZABANEH_XIQ"): "GENERAL+EXTREME", ("DAVIES", "UKB_FI4"): "GENERAL+ARITHMETIC(objective item)"}
    dep = {"GENERAL+EXECUTIVE": "independent sample (G&C UKB-free)", "GENERAL+PERFORMANCE_IQ": "BATS shared with Davies (7.6%)",
           "GENERAL+EXTREME": "HRS controls inside Davies", "GENERAL+ARITHMETIC(objective item)": "UKB in both (intercept 0.12, corrected by LAVA)"}
    rows = []
    for L in loc.itertuples():
        lv = lava[lava.locus == L.LOC]
        s = strat.get(L.LOC)
        rec = {"locus_id": L.LOC, "label_only": L.label, "locus_stratum": s.locus_stratum if s is not None else None,
               "log10BF_independent": s.log10BF_independent if s is not None else np.nan}
        for (a, b), name in pair.items():
            x = lv[((lv.phen1 == a) & (lv.phen2 == b)) | ((lv.phen1 == b) & (lv.phen2 == a))]
            rec[f"{name}_rho"] = float(x.rho.iloc[0]) if len(x) else np.nan
            rec[f"{name}_p"] = float(x.p.iloc[0]) if len(x) else np.nan
            rec[f"{name}_call"] = ("SHARED_BONFERRONI" if len(x) and x.bonf.iloc[0] and x.rho.iloc[0] > 0 else
                                   "SHARED_NOMINAL" if len(x) and x.p.iloc[0] < 0.05 and x.rho.iloc[0] > 0 else
                                   "OPPOSITE_NOMINAL" if len(x) and x.p.iloc[0] < 0.05 else
                                   "NOT_SHARED_AT_THIS_POWER" if len(x) else "NOT_TESTABLE (no local h2 in both)")
        mi = math[math.in_cognition_locus.astype(str).str.contains(L.LOC, na=False)]
        rec["math53_snps_in_locus"] = ";".join(f"{r.rsid}({r.g_direction_vs_davies})" for r in mi.itertuples()) or None
        genes_here = set(m[m.locus_id == L.LOC].gene)
        rec["rare_coding_gene_in_locus"] = ";".join(sorted(genes_here & set(rare["exome_wide_cognition"]))) or None
        scg = sc[sc.locus_id == L.LOC]
        rec["adult_single_cell_coloc_genes"] = ";".join(sorted(set(scg.gene))) or None
        mtx = mt[(mt.locus_id == L.LOC) & (mt.cog_and_eqtl_cluster.astype(str).str.lower() == "true")] if "cog_and_eqtl_cluster" in mt.columns else mt.iloc[0:0]
        rec["multitrait_cog_eqtl_cluster"] = ";".join(sorted(set(mtx.traits_clustered.astype(str))))[:200] or None
        cats = [k for k in pair.values() if rec[f"{k}_call"] == "SHARED_BONFERRONI"]
        conc = mi[~mi.g_direction_vs_davies.astype(str).str.contains("INVERT", na=False)]
        if len(conc):
            cats.append("GENERAL+MATH_PROXY(Gq; dependent)")
        elif len(mi):
            cats.append("MATH_PROXY_INVERTED_vs_GENERAL (not convergence)")
        if rec["rare_coding_gene_in_locus"]:
            cats.append("GENERAL+RARE_CODING")
        if rec["adult_single_cell_coloc_genes"] and any(("ARITHMETIC" in c or "MATH_PROXY(Gq" in c) for c in cats):
            cats.append("GENERAL+MATH+ADULT_CELL_QTL")
        if rec["adult_single_cell_coloc_genes"] and "GENERAL+EXTREME" in cats:
            cats.append("EXTREME+ADULT_CELL_QTL")
        rec["convergence_categories"] = ";".join(cats) or "NONE_AT_BONFERRONI"
        rec["dependence_notes"] = " | ".join(f"{c}: {dep[c]}" for c in cats if c in dep)
        rows.append(rec)
    cv = pd.DataFrame(rows).sort_values("log10BF_independent", ascending=False)
    cv["n_bivariate_tests"] = nb
    cv.to_csv(O5A / "cross_phenotype_convergence.csv", index=False, float_format="%.4g")

    # ---------------- shortlists
    a_rows = []
    for r in m.itertuples():
        why = []
        if r.gene in rare["exome_wide_cognition"]:
            why.append("exome-wide rare LoF burden (UKB): carriers score lower")
        if r.gene_class in ("CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"):
            why.append(f"{r.gene_class} ({r.classes}) at {r.locus_id} [{r.locus_stratum}]")
        cd = json.loads(r.class_detail) if isinstance(r.class_detail, str) else {}
        if cd.get("CODING", 0) >= 0.5:
            why.append(f"credible missense PIP={cd['CODING']:.2f} at {r.locus_id} [{r.locus_stratum}]")
        if why:
            tie = [g for g in str(r.other_genes_with_classes).split(";") if g and g in set(m[(m.locus_id == r.locus_id) & (m.n_classes >= r.n_classes)].gene)] \
                if isinstance(r.locus_id, str) else []
            a_rows.append({"gene": r.gene, "evidence": " + ".join(why), "gene_class_5a": r.gene_class, "locus_id": r.locus_id,
                           "locus_stratum": r.locus_stratum, "direction_stratum": r.direction_stratum,
                           "tied_with_same_class_count": ";".join(tie) or None,
                           "evidence_kind": ("HUMAN_PERTURBATION_LOF" if r.gene in rare["exome_wide_cognition"] else
                                             "CODING_VARIANT" if cd.get("CODING", 0) >= 0.5 else "REGULATORY_V2G")})
    A = pd.DataFrame(a_rows)
    order = {"HUMAN_PERTURBATION_LOF": 0, "CODING_VARIANT": 1, "REGULATORY_V2G": 2}
    A = A.sort_values(["evidence_kind", "locus_stratum"], key=lambda s: s.map(order) if s.name == "evidence_kind" else s)
    A.to_csv(O5A / "SHORTLIST_A_causal_cognition_genes.csv", index=False)
    B = cv[cv.convergence_categories.str.contains("EXTREME|ARITHMETIC|MATH_PROXY\\(Gq", regex=True)].copy()
    B["gene_status_at_locus"] = B.locus_id.map(lambda l: "; ".join(f"{x.gene}:{x.gene_class}" for x in m[(m.locus_id == l) & (m.n_classes > 0)].itertuples()) or "gene unresolved (no V2G class)")
    B.to_csv(O5A / "SHORTLIST_B_exceptional_quantitative.csv", index=False)
    crit = m.assign(c1=m.locus_stratum.isin(["L1", "L2"]), c2=m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"]),
                    c3=m.classes.astype(str).str.contains("QTL"), c4=m.direction_stratum.eq("D1"))
    crit["n_met_1to4"] = crit[["c1", "c2", "c3", "c4"]].sum(axis=1)
    Cq = crit[crit.n_met_1to4 == 4]
    near = crit[(crit.n_met_1to4 >= 2) & (crit.c1 | crit.c2)].sort_values("n_met_1to4", ascending=False)
    near = near.assign(missing=near.apply(lambda r: ";".join(k for k, v in (("independent_locus_L1L2", r.c1), ("credible_gene_MODERATE+", r.c2),
                                                                              ("adult_brain_QTL", r.c3), ("direction_D1", r.c4)) if not v), axis=1))
    Cq.to_csv(O5A / "SHORTLIST_C_adult_modifiable.csv", index=False)
    near[["gene", "locus_id", "gene_class", "classes", "locus_stratum", "direction_stratum", "n_met_1to4", "missing"]].to_csv(
        O5A / "SHORTLIST_C_near_misses_NOT_qualifying.csv", index=False)
    print("convergence categories:", cv.convergence_categories.value_counts().to_dict())
    print("A:", A[["gene", "evidence_kind", "gene_class_5a", "locus_stratum"]].to_string(index=False))
    print("B:", B[["locus_id", "label_only", "convergence_categories", "gene_status_at_locus"]].to_string(index=False))
    print("C qualifying:", len(Cq)); print(near[["gene", "locus_id", "n_met_1to4", "missing"]].head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
