#!/usr/bin/env python3
"""Sprint 4, Gate C step 4 — direction resolution under the UNCHANGED Sprint-3 rule.

Rule (frozen): >= 3 strong (>= 0.8) gene-level adult-brain eQTL/pQTL colocalisations with >= 80%
polarity-adjusted sign agreement. Counted two ways and both reported:
  * rows (the Sprint-3 primary unit: GWAS study x QTL dataset x molecular trait);
  * independent QTL-COHORT units (a cohort's majority sign; GTEx tissues share donors) — robustness.
DIRECTION_RESOLVED requires both; RESOLVED_ON_ROWS_ONLY_NOT_ROBUST is reported and never promoted.

Evidence pooled per (gene, QTL dataset): strong if the Sprint-3 Open Targets COLOC/eCAVIAR strength >= 0.8
OR our coloc PP.H4 >= 0.8; polarity from our harmonised analysis when available, else OT's
betaRatioSignAverage x trait polarity; if both exist and disagree, the pair counts with sign 0
(disagreeing). Gene-level only: ENSG traits from ge/microarray datasets; exon/tx/txrev/leafcutter
excluded. Adult only: datasets classified ADULT in data/sprint4/eqtl_catalogue_brain_datasets.csv (OT
study ids are mapped by cohort prefix; unmapped cohorts are excluded, never assumed adult).

Output: reports/sprint4/directionality_resolution.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gene_tournament"))
import common as C  # noqa: E402


def resolve(rows: pd.DataFrame, frozen: dict) -> dict:
    d = frozen["rules"]["gate_c"]["direction_rule"]
    k, a = int(d["min_strong_gene_level_colocs"]), float(d["min_sign_agreement"])
    s = rows["sign"].to_numpy(float)
    n = int(len(s))
    agree_rows = float(max((s > 0).mean(), (s < 0).mean())) if n else float("nan")
    maj = int(np.sign(s.sum())) if n else 0
    units = rows.groupby("cohort")["sign"].sum().apply(np.sign)
    u = units.to_numpy(float)
    agree_units = float(max((u > 0).mean(), (u < 0).mean())) if len(u) else float("nan")
    res_rows = bool(n >= k and agree_rows >= a)
    res_units = bool(len(u) >= k and agree_units >= a)
    label = ("DIRECTION_RESOLVED" if res_rows and res_units else
             "RESOLVED_ON_ROWS_ONLY_NOT_ROBUST" if res_rows else
             "UNRESOLVED_NO_STRONG_COLOC" if n == 0 else "UNRESOLVED")
    return {"n_rows": n, "row_agreement": agree_rows, "majority_sign": maj, "resolved_rows": res_rows,
            "n_cohort_units": int(len(u)), "unit_agreement": agree_units, "resolved_units": res_units,
            "label": label}


def adult_cohorts() -> dict[str, str]:
    meta = pd.read_csv(C.DATA / "eqtl_catalogue_brain_datasets.csv")
    out = {}
    for r in meta.itertuples():
        out[str(r.study_label).lower().split("_")[0]] = r.adult_status
    return out


def ot_rows(genes: set[str], cohorts: dict[str, str]) -> pd.DataFrame:
    import build_consensus as bc
    co = pd.read_csv(C.REPO_ROOT / "data" / "gene_tournament" / "opentargets_brain_coloc_compact.csv.gz")
    co = co[co.current_symbol.isin(genes)].copy()
    co["trait_class"] = co.gwas_trait.map(bc.classify_trait)
    co = co[co.trait_class == "direct_cognition"]
    co["strength"] = co.apply(bc.coloc_strength, axis=1)
    co["polarity"] = np.where(co.gwas_trait.astype(str).str.contains(bc.NEG_POLARITY_RX), -1, 1)
    strict = (co.qtl_molecular_trait.astype(str).str.startswith("ENSG")
              & ~co.qtl_study_id.astype(str).str.contains(r"_(?:tx|txrev|exon|leafcutter)_")
              & co.qtl_study_type.astype(str).str.match(r"(eqtl|pqtl)$"))
    co = co[(co.strength >= 0.8) & strict & co.beta_ratio_sign_average.notna()].copy()
    co["cohort"] = co.qtl_study_id.astype(str).str.split("_").str[0].str.lower()
    co["adult_status"] = co.cohort.map(cohorts).fillna("UNMAPPED")
    co["sign"] = np.sign(co.beta_ratio_sign_average) * co.polarity
    co["dataset_id"] = co.qtl_study_id
    co["source"] = "Open Targets (Sprint 3)"
    return co.rename(columns={"current_symbol": "gene"})[
        ["gene", "gwas_study_id", "gwas_trait", "dataset_id", "cohort", "adult_status", "qtl_biosample_name",
         "strength", "sign", "source"]]


def main() -> int:
    frozen = C.load_frozen()
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    locus_of = q.groupby("gene").locus_id.first().to_dict()
    cohorts = adult_cohorts()
    meta = pd.read_csv(C.DATA / "eqtl_catalogue_brain_datasets.csv").set_index("dataset_id")
    ot = ot_rows(set(q.gene), cohorts)
    ours = pd.read_parquet(C.OUT / "adult_brain_susie_coloc.parquet") if (C.OUT / "adult_brain_susie_coloc.parquet").exists() \
        else pd.DataFrame(columns=["gene_id", "dataset_id", "PP.H4", "weighted_sign_ratio_qtl_over_gwas"])
    ours = ours[ours["PP.H4"] >= 0.8].copy()
    ours["gene"] = ours.gene_id.map(sym)
    ours["cohort"] = ours.dataset_id.map(lambda d: str(meta.loc[d, "study_label"]).lower().split("_")[0] if d in meta.index else "?")
    ours["adult_status"] = "ADULT"
    ours["sign"] = np.sign(ours.weighted_sign_ratio_qtl_over_gwas)
    ours["source"] = "Sprint 4 coloc.abf (Davies x eQTL Catalogue)"
    ours["gwas_study_id"] = "Davies2018_open"
    rows = pd.concat([ot[ot.adult_status == "ADULT"], ours[["gene", "gwas_study_id", "dataset_id", "cohort",
                                                           "adult_status", "sign", "source"]]], ignore_index=True)
    # pooling per (gene, dataset): our polarity wins when present; disagreement -> sign 0
    pooled = []
    for (g, ds), grp in rows.groupby(["gene", "dataset_id"]):
        mine = grp[grp.source.str.startswith("Sprint 4")].sign
        theirs = grp[grp.source.str.startswith("Open Targets")].sign
        if len(mine) and len(theirs) and np.sign(mine.sum()) != np.sign(theirs.sum()):
            s = 0
        elif len(mine):
            s = int(np.sign(mine.sum()))
        else:
            s = int(np.sign(theirs.sum()))
        pooled.append({"gene": g, "dataset_id": ds, "cohort": grp.cohort.iloc[0], "sign": s})
    pooled = pd.DataFrame(pooled, columns=["gene", "dataset_id", "cohort", "sign"])
    out = []
    for g in sorted(set(q.gene)):
        r_rows = rows[rows.gene == g]
        r = resolve(r_rows, frozen)
        p = pooled[pooled.gene == g]
        rp = resolve(p, frozen) if len(p) else None
        direction = ("cognition-increasing allele -> HIGHER expression" if r["majority_sign"] > 0 else
                     "cognition-increasing allele -> LOWER expression" if r["majority_sign"] < 0 else "none")
        out.append({"gene": g, "locus_id": locus_of.get(g), **{f"rows_{k}": v for k, v in r.items()},
                    "pooled_pairs": int(len(p)), "pooled_pair_agreement": rp["row_agreement"] if rp else None,
                    "label": r["label"],
                    "direction_statement": (f"{direction} in adult brain ({', '.join(sorted(set(r_rows.cohort)))})"
                                            if r["label"] == "DIRECTION_RESOLVED" else
                                            f"not resolved ({r['label']}); majority: {direction}" if len(r_rows) else
                                            "no strong gene-level adult-brain colocalisation"),
                    "tissues_or_cohorts": ";".join(sorted(set(r_rows.cohort))),
                    "sources": ";".join(sorted(set(r_rows.source)))})
    res = pd.DataFrame(out).sort_values(["rows_n_rows"], ascending=False)
    res.to_csv(C.OUT / "directionality_resolution.csv", index=False, float_format="%.4g")
    rows.to_csv(C.DATA / "direction_evidence_rows.csv", index=False)
    print(res.head(15).to_string(index=False))
    print(res.label.value_counts().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
