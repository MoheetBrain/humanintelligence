#!/usr/bin/env python3
"""Sensitivity: would brainSCOPE GRN element->gene links (not counted as ENHANCER_LINK under the frozen
definition: they are TF-network inferences partly built from expression in the eQTL donors, not a
chromatin activity-by-contact model) change any gene class? Credible variants PIP >= 0.1 at Gate-C loci;
previous symbols mapped to current (CYHR1 -> ZFTRAF1). Output: data/sprint5/grn_sensitivity.csv"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

ALIAS = {"CYHR1": "ZFTRAF1"}


def main() -> int:
    g = pd.read_csv(C.OUT / "brainscope_enhancer_gene_links.csv")
    v = pd.read_parquet(C.DATA / "v2g_rows_opentargets.parquet")[["rsid", "pip_max"]]
    g = g.merge(v, on="rsid", how="left")
    g = g[g.pip_max >= 0.1]
    g["gene"] = g.target_gene.replace(ALIAS)
    m = pd.read_csv(C.OUT / "causal_gene_evidence_matrix.csv")
    gate = set(pd.read_csv(C.S4_DATA / "gate_c_loci.csv").locus_id)
    rows = []
    for (lid, gene), x in g.groupby(["locus_id", "gene"]):
        if lid not in gate:
            continue
        cur = m[(m.gene == gene)]
        ncls = int(cur.n_classes.iloc[0]) if len(cur) else 0
        cls = str(cur.classes.iloc[0]) if len(cur) else ""
        has_enh = "ENHANCER_LINK" in cls
        rows.append({"locus_id": lid, "gene": gene, "element_types": ";".join(sorted(set(x.element_type))),
                     "cell_types": ";".join(sorted(set(x.cell_type)))[:200], "max_pip": round(x.pip_max.max(), 3),
                     "current_class": cur.gene_class.iloc[0] if len(cur) else "NOT_IN_UNIVERSE", "current_classes": cls,
                     "would_gain_class": not has_enh, "n_classes_if_counted": ncls + (0 if has_enh else 1)})
    out = pd.DataFrame(rows).sort_values("n_classes_if_counted", ascending=False)
    out.to_csv(C.DATA / "grn_sensitivity.csv", index=False)
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
