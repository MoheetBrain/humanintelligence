#!/usr/bin/env python3
"""Compare Sprint-5 vs Sprint-5A (integrated rerun) gene classes, strata and ranks -> reports/sprint5a/class_changes.csv"""
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
a = pd.read_csv(R / "reports/sprint5/causal_gene_evidence_matrix.csv")
b = pd.read_csv(R / "reports/sprint5a/s5_integrated/causal_gene_evidence_matrix.csv")
cols = ["gene", "locus_id", "gene_class", "classes", "locus_stratum", "direction_stratum", "perturbation_stratum", "rank_B_causal_gene"]
m = a[cols].merge(b[cols], on="gene", how="outer", suffixes=("_s5", "_s5a"))
def _s(col):
    return m[col].astype(object).where(m[col].notna(), "").astype(str)
diff = pd.Series(False, index=m.index)
for c in ("gene_class", "locus_stratum", "classes", "direction_stratum"):
    diff |= _s(c + "_s5") != _s(c + "_s5a")
ch = m[diff]
ch.to_csv(R / "reports/sprint5a/class_changes.csv", index=False)
la = pd.read_csv(R / "reports/sprint5/locus_confidence_rank.csv")
lb = pd.read_csv(R / "reports/sprint5a/s5_integrated/locus_confidence_rank.csv")
print("locus strata S5:", la.locus_stratum.value_counts().to_dict())
print("locus strata S5A:", lb.locus_stratum.value_counts().to_dict())
print("gene classes S5A:", b.gene_class.value_counts().to_dict())
print(len(ch), "genes changed class/stratum/classes/direction")
print(ch[ch.gene_class_s5 != ch.gene_class_s5a][["gene", "gene_class_s5", "gene_class_s5a", "classes_s5a", "locus_stratum_s5a"]].to_string(index=False))
