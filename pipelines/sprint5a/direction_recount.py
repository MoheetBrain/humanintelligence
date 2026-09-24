#!/usr/bin/env python3
"""Sprint 5A — recount adult-brain direction under the UNCHANGED Sprint-4 rule (>= 3 strong gene-level adult colocs,
>= 80% agreement, on rows AND independent QTL-cohort units; frozen resolve() imported from Sprint 4), adding the
Sprint-5A single-cell eQTL colocalisations (Bryois 2022, SingleBrain; PP.H4 >= 0.8) as rows. Because both single-cell
resources contain ROSMAP donors (and SingleBrain contains Bryois), every single-cell row is assigned to the existing
'rosmap' cohort unit (conservative: they can never create a new independent unit).
Output: reports/sprint5a/directionality_resolution_5a.csv (same columns as the Sprint-4 table)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "pipelines/sprint4"))
import common as C4  # noqa: E402
from gate_c_direction import resolve  # noqa: E402

frozen = C4.load_frozen()
rows = pd.read_csv(R / "data/sprint4/direction_evidence_rows.csv")
sc = pd.read_parquet(R / "reports/sprint5a/sc_eqtl_coloc.parquet")
sc = sc[(sc["PP.H4"] >= 0.8) & sc.qtl_effect_of_cognition_allele_at_top.notna()]
add = pd.DataFrame({"gene": sc.gene, "gwas_study_id": "Davies2018_open", "dataset_id": sc.source + ":" + sc.cell_type,
                    "cohort": "rosmap", "adult_status": "ADULT", "sign": np.sign(sc.qtl_effect_of_cognition_allele_at_top),
                    "source": "Sprint 5A single-cell coloc (" + sc.source + ")"})
allr = pd.concat([rows, add], ignore_index=True)
q = pd.read_csv(R / "data/sprint4/gate_c_query_genes.csv")
locus_of = q.groupby("gene").locus_id.first().to_dict()
locus_of.update(sc.groupby("gene").locus_id.first().to_dict())
out = []
for g in sorted(set(allr.gene.dropna())):
    rr = allr[allr.gene == g]
    r = resolve(rr, frozen)
    d = ("cognition-increasing allele -> HIGHER expression" if r["majority_sign"] > 0 else
         "cognition-increasing allele -> LOWER expression" if r["majority_sign"] < 0 else "none")
    out.append({"gene": g, "locus_id": locus_of.get(g), **{f"rows_{k}": v for k, v in r.items()}, "label": r["label"],
                "direction_statement": (f"{d} in adult brain ({', '.join(sorted(set(rr.cohort)))})" if r["label"] == "DIRECTION_RESOLVED"
                                        else f"not resolved ({r['label']}); majority: {d}"),
                "tissues_or_cohorts": ";".join(sorted(set(rr.cohort))), "sources": ";".join(sorted(set(rr.source))),
                "n_single_cell_rows": int(rr.source.str.contains("single-cell").sum())})
res = pd.DataFrame(out).sort_values("rows_n_rows", ascending=False)
res.to_csv(R / "reports/sprint5a/directionality_resolution_5a.csv", index=False, float_format="%.4g")
old = pd.read_csv(R / "reports/sprint4/directionality_resolution.csv").set_index("gene").label
res["label_sprint4"] = res.gene.map(old)
print(res.label.value_counts().to_dict())
print(res[res.label != res.label_sprint4.fillna("")][["gene", "locus_id", "label_sprint4", "label", "rows_n_rows", "rows_row_agreement",
                                                       "rows_n_cohort_units", "n_single_cell_rows"]].head(30).to_string(index=False))
