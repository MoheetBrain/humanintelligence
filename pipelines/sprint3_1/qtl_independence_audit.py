#!/usr/bin/env python3
"""Sprint 3.1 — collapse correlated brain-QTL colocalisations into independent signal units.

Sprint 3 counted colocalisation ROWS toward the direction rule (>=3 strong gene-level brain
eQTL/pQTL colocalisations, >=80% polarity-adjusted agreement). A row is one GWAS study x one
QTL dataset x one molecular trait. Rows are not independent when:

* several GWAS studies share participants (every cognition GWAS here contains UK Biobank) and
  tag the same locus signal -> one GWAS signal, however many papers report it;
* one QTL cohort is measured in several tissues (GTEx donors are shared across its brain
  tissues) or with several quantification methods -> one QTL cohort.

An independent unit is therefore (GWAS signal group, QTL cohort). GWAS signal groups are
formed from the lead variants by LD in 1000 Genomes EUR (r^2 >= 0.5 joins two leads); a lead
absent from the reference (e.g. an indel) forms its own group and is flagged.

The direction threshold is NOT changed: it is re-applied, as frozen, to units instead of rows
(>= 3 units, >= 80% agreement). Nothing is relaxed.

Output: ``reports/sprint3_1/negr1_qtl_independence_audit.csv`` (NEGR1 primary; SYT1 as the
second Sprint-4 stress test) and a JSON summary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipelines" / "gene_tournament"))
import build_consensus as bc  # noqa: E402

BFILE = "data/external/x01/genetics_tools/reference/g1000_eur"
OUT = REPO / "reports" / "sprint3_1"
GENES = ["NEGR1", "SYT1"]
MIN_UNITS, MIN_AGREE, STRENGTH = 3, 0.8, 0.8   # frozen Sprint-3 rule, unchanged
UKB_GWAS_NOTE = ("all cognition GWAS in this table contain UK Biobank participants "
                 "(Sniekers 2017, Savage 2018, Davies 2018, Hatoum 2022/2023 and the UKB field-20016 "
                 "fluid-intelligence analyses)")


def ld_r2(rsids: list[str]) -> pd.DataFrame:
    from bed_reader import open_bed
    bim = pd.read_csv(BFILE + ".bim", sep="\t", header=None, usecols=[1], names=["snp"])
    idx = bim.index[bim.snp.isin(rsids)].to_numpy()
    if len(idx) == 0:
        return pd.DataFrame()
    with open_bed(BFILE + ".bed") as b:
        g = b.read(index=np.s_[:, idx], dtype="float32")
    g = np.where(np.isnan(g), np.nanmean(g, axis=0), g)
    r = np.corrcoef(g.T) if g.shape[1] > 1 else np.array([[1.0]])
    names = bim.snp.iloc[idx].tolist()
    return pd.DataFrame(r ** 2, index=names, columns=names)


def signal_groups(leads: list[str]) -> tuple[dict[str, str], pd.DataFrame]:
    leads = sorted(set(leads))
    r2 = ld_r2(leads)
    parent = {v: v for v in leads}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for a in r2.index:
        for b in r2.columns:
            if a < b and r2.loc[a, b] >= 0.5:
                parent[find(a)] = find(b)
    groups = {v: find(v) for v in leads}
    return groups, r2


def audit(gene: str, co: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    d = co[co.current_symbol == gene].copy()
    d["trait_class"] = d.gwas_trait.map(bc.classify_trait)
    d["strength"] = d.apply(bc.coloc_strength, axis=1)
    d["polarity"] = np.where(d.gwas_trait.astype(str).str.contains(bc.NEG_POLARITY_RX), -1, 1)
    d = d[d.trait_class == "direct_cognition"].copy()
    d["rule_eligible_sprint3"] = ((d.strength >= STRENGTH)
                                  & d.qtl_study_type.astype(str).str.match(r"(eqtl|pqtl)$")
                                  & ~d.qtl_molecular_trait.astype(str).str.contains(r"_\d+_\d+$")
                                  & d.beta_ratio_sign_average.notna())
    # The Sprint-3 rule text says "gene-level" but its regex only excluded exon traits, so
    # transcript-level (ENST) eQTLs were counted. Strict eligibility keeps ENSG gene-level traits
    # from gene-expression datasets only; both counts are reported.
    d["gene_level_strict"] = (d.qtl_molecular_trait.astype(str).str.startswith("ENSG")
                              & ~d.qtl_study_id.astype(str).str.contains(r"_(?:tx|txrev|exon|leafcutter)_"))
    d["rule_eligible_strict_gene_level"] = d.rule_eligible_sprint3 & d.gene_level_strict
    d["signed_direction"] = np.sign(d.beta_ratio_sign_average) * d.polarity
    groups, r2 = signal_groups(d.gwas_variant_rsid.dropna().tolist())
    in_ref = set(r2.index)
    d["gwas_signal_group"] = d.gwas_variant_rsid.map(groups)
    d["lead_in_1000G_EUR"] = d.gwas_variant_rsid.isin(in_ref)
    d["qtl_cohort"] = d.qtl_study_id.astype(str).str.split("_").str[0]
    d["independent_unit"] = d.gwas_signal_group + " x " + d.qtl_cohort
    d["gene"] = gene
    d["ukb_overlap_gwas"] = True
    summary_extra = {"sprint3_rows_counted_strict_gene_level": int(d.rule_eligible_strict_gene_level.sum()),
                     "sprint3_rows_transcript_or_splice_level": int((d.rule_eligible_sprint3 & ~d.gene_level_strict).sum())}
    elig = d[d.rule_eligible_strict_gene_level]
    units = []
    for unit, g in elig.groupby("independent_unit"):
        signs = g.signed_direction.to_numpy()
        units.append({"unit": unit, "n_rows": int(len(g)), "n_positive": int((signs > 0).sum()),
                      "n_negative": int((signs < 0).sum()),
                      "unit_direction": int(np.sign(signs.sum())) if signs.sum() != 0 else 0,
                      "internally_consistent": bool(len(set(signs)) == 1),
                      "gwas_studies": sorted(g.gwas_study_id.unique().tolist()),
                      "qtl_datasets": sorted(g.qtl_study_id.unique().tolist())})
    n_units = len(units)
    dirs = [u["unit_direction"] for u in units if u["unit_direction"] != 0]
    agree = max((np.array(dirs) > 0).mean(), (np.array(dirs) < 0).mean()) if dirs else float("nan")
    summary = {
        "gene": gene, **summary_extra,
        "units_counted_from": "strict gene-level rule-eligible rows",
        "sprint3_rows_counted": int(d.rule_eligible_sprint3.sum()),
        "sprint3_row_agreement": float(max((d[d.rule_eligible_sprint3].signed_direction > 0).mean(),
                                           (d[d.rule_eligible_sprint3].signed_direction < 0).mean()))
        if d.rule_eligible_sprint3.any() else None,
        "n_direct_cognition_brain_colocs_all_strengths": int(len(d)),
        "n_gwas_signal_groups_all_rows": int(d.gwas_signal_group.nunique()),
        "gwas_leads": sorted(d.gwas_variant_rsid.dropna().unique().tolist()),
        "leads_absent_from_1000G": sorted(set(d.gwas_variant_rsid.dropna()) - in_ref),
        "lead_ld_r2": r2.round(3).to_dict(),
        "qtl_cohorts_all_rows": sorted(d.qtl_cohort.unique().tolist()),
        "independent_units": units,
        "n_independent_units": n_units,
        "n_units_directionally_concordant": int(max((np.array(dirs) > 0).sum(), (np.array(dirs) < 0).sum())) if dirs else 0,
        "unit_agreement": None if not dirs else float(agree),
        "direction_resolved_under_frozen_rule_on_units": bool(n_units >= MIN_UNITS and dirs and agree >= MIN_AGREE),
        "near_resolution": bool(n_units >= MIN_UNITS - 1 and dirs and agree >= MIN_AGREE),
        "frozen_rule": f">= {MIN_UNITS} strong gene-level brain eQTL/pQTL colocalisations, >= {MIN_AGREE:.0%} "
                       "polarity-adjusted agreement (unchanged; applied to independent units)",
        "ukb_note": UKB_GWAS_NOTE,
    }
    cols = ["gene", "gwas_study_id", "gwas_trait", "gwas_pubmed_id", "gwas_variant_rsid", "lead_in_1000G_EUR",
            "gwas_signal_group", "ukb_overlap_gwas", "qtl_study_id", "qtl_cohort", "qtl_biosample_name",
            "qtl_study_type", "qtl_molecular_trait", "colocalisation_method", "h4", "clpp", "strength",
            "beta_ratio_sign_average", "polarity", "signed_direction", "gwas_beta", "qtl_beta",
            "rule_eligible_sprint3", "gene_level_strict", "rule_eligible_strict_gene_level", "independent_unit"]
    return d[cols].sort_values(["rule_eligible_strict_gene_level", "rule_eligible_sprint3", "strength"],
                               ascending=[False, False, False]), summary


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    co = pd.read_csv(REPO / "data" / "gene_tournament" / "opentargets_brain_coloc_compact.csv.gz")
    frames, summaries = [], {}
    for gene in GENES:
        f, s = audit(gene, co)
        frames.append(f)
        summaries[gene] = s
    table = pd.concat(frames, ignore_index=True)
    table.to_csv(OUT / "negr1_qtl_independence_audit.csv", index=False, float_format="%.6g")
    (OUT / "negr1_qtl_independence_audit_summary.json").write_text(
        json.dumps(summaries, indent=1, default=str) + "\n", encoding="utf-8")
    for gene, s in summaries.items():
        print(gene, {k: s[k] for k in ("sprint3_rows_counted", "sprint3_row_agreement",
                                       "sprint3_rows_counted_strict_gene_level", "n_independent_units",
                                       "n_units_directionally_concordant", "unit_agreement",
                                       "direction_resolved_under_frozen_rule_on_units", "near_resolution",
                                       "leads_absent_from_1000G", "n_gwas_signal_groups_all_rows")})
        for u in s["independent_units"]:
            print("   ", u)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def recount_all_genes() -> pd.DataFrame:
    """Sprint-3 row count vs strict gene-level rows vs independent QTL cohorts, every gene.

    Units here are approximated as distinct (lead variant, QTL cohort) pairs without LD
    grouping (LD is computed only for the audited genes above), which can only OVER-count units.
    """
    co = pd.read_csv(REPO / "data" / "gene_tournament" / "opentargets_brain_coloc_compact.csv.gz")
    co["trait_class"] = co.gwas_trait.map(bc.classify_trait)
    co = co[co.trait_class == "direct_cognition"].copy()
    co["strength"] = co.apply(bc.coloc_strength, axis=1)
    co["polarity"] = np.where(co.gwas_trait.astype(str).str.contains(bc.NEG_POLARITY_RX), -1, 1)
    elig = ((co.strength >= STRENGTH) & co.qtl_study_type.astype(str).str.match(r"(eqtl|pqtl)$")
            & ~co.qtl_molecular_trait.astype(str).str.contains(r"_\d+_\d+$") & co.beta_ratio_sign_average.notna())
    strict = (co.qtl_molecular_trait.astype(str).str.startswith("ENSG")
              & ~co.qtl_study_id.astype(str).str.contains(r"_(?:tx|txrev|exon|leafcutter)_"))
    co["sign"] = np.sign(co.beta_ratio_sign_average) * co.polarity
    co["cohort"] = co.qtl_study_id.astype(str).str.split("_").str[0]
    rows = []
    for gene, g in co.groupby("current_symbol"):
        e, s = g[elig.loc[g.index]], g[(elig & strict).loc[g.index]]
        agree = lambda x: float(max((x > 0).mean(), (x < 0).mean())) if len(x) else np.nan  # noqa: E731
        units = s.groupby(["gwas_variant_rsid", "cohort"]).sign.sum().apply(np.sign)
        units = units[units != 0]
        rows.append({"gene": gene, "sprint3_rows": len(e), "sprint3_agreement": agree(e.sign),
                     "sprint3_resolved": bool(len(e) >= 3 and agree(e.sign) >= 0.8),
                     "strict_gene_level_rows": len(s), "strict_agreement": agree(s.sign),
                     "max_units_upper_bound": int(len(units)), "unit_agreement": agree(units),
                     "resolved_on_units": bool(len(units) >= 3 and agree(units) >= 0.8),
                     "distinct_qtl_cohorts_strict": int(s.cohort.nunique())})
    return pd.DataFrame(rows).sort_values("sprint3_rows", ascending=False)


if __name__ == "__main__" and "--all" in sys.argv:
    t = recount_all_genes()
    t.to_csv(OUT / "direction_rule_recount_all_genes.csv", index=False, float_format="%.4g")
    print(t.head(25).to_string(index=False))
    print("genes resolved: sprint3 rows", int(t.sprint3_resolved.sum()), "| units", int(t.resolved_on_units.sum()))
