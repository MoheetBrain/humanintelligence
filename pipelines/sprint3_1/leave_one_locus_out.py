#!/usr/bin/env python3
"""Sprint 3.1 — leave-one-locus-out robustness of the six Sprint-3 synaptic sets.

For each frozen set and each LD block (|r|>=0.2 gene blocks) holding a Bonferroni gene of that
set, every gene of the block is excluded (``--settings gene-exclude``) and the SynGO gene-set
analysis re-run with the Sprint-3 covariates on the full universe (spec D). A set whose
enrichment disappears when one locus is removed is a one-locus result, whatever its P.

Output: reports/sprint3_1/leave_one_locus_out.csv
"""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_recon as AR  # noqa: E402
import run_recon_magma as RR  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WORK = RR.WORK / "lolo"
OUT = REPO / "reports" / "sprint3_1" / "leave_one_locus_out.csv"


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(REPO / "data/raw/magma_x01/2026-09-22/davies2018_10kb.genes.out", sep=r"\s+")
    ld = pd.read_parquet(REPO / "data/gene_tournament/ld_loci.parquet")[["GENE", "ld_block_r0.2"]]
    sym = pd.read_csv(REPO / "data/raw/magma_x01/2026-09-22/gene_id_map.tsv", sep="\t",
                      usecols=["GENE", "current_symbol"])
    g = g.merge(ld, on="GENE").merge(sym, on="GENE")
    bonf = g[g.P < 0.05 / len(g)]
    syn = {p[0]: {int(x) for x in p[1:]} for p in
           (ln.split() for ln in (REPO / "data/gene_tournament/pathway_sets/syngo.setannot").read_text().splitlines()) if p}
    jobs, meta = [], []
    for sid in AR.FROZEN6:
        blocks = bonf[bonf.GENE.isin(syn[sid])]
        for block, grp in blocks.groupby("ld_block_r0.2"):
            excl = g[g["ld_block_r0.2"] == block].GENE
            f = WORK / f"excl_{block}.txt"
            if not f.exists():
                f.write_text("\n".join(map(str, excl)) + "\n")
            out = WORK / f"syngo__D__minus_{block}"
            cmd = RR.magma_cmd(RR.COLLECTIONS["syngo"], "D", out) + ["--settings", f"gene-exclude={f}"]
            jobs.append((cmd, out))
            meta.append({"set": sid, "excluded_block": int(block),
                         "excluded_set_genes": ",".join(grp.sort_values("P").current_symbol),
                         "n_genes_excluded": int(len(excl)), "out": out})
    uniq = {str(o): (c, o) for c, o in jobs}
    with ThreadPoolExecutor(max_workers=14) as ex:
        list(ex.map(RR.run, uniq.values()))
    full = AR.read_gsa(RR.WORK / "syngo__D.gsa.out").set_index("VARIABLE")
    rows = []
    for m in meta:
        res = AR.read_gsa(m["out"].with_suffix(".gsa.out")).set_index("VARIABLE")
        rows.append({k: v for k, v in m.items() if k != "out"} | {
            "full_beta": float(full.loc[m["set"], "BETA"]), "full_P": float(full.loc[m["set"], "P"]),
            "loo_beta": float(res.loc[m["set"], "BETA"]), "loo_P": float(res.loc[m["set"], "P"])})
    t = pd.DataFrame(rows)
    worst = t.sort_values("loo_P").groupby("set").tail(1).set_index("set")
    t["set_worst_loo_P"] = t.set.map(worst.loo_P)
    t["set_worst_block_genes"] = t.set.map(worst.excluded_set_genes)
    t.to_csv(OUT, index=False, float_format="%.4g")
    print(t.groupby("set").agg(n_loci=("excluded_block", "size"), full_P=("full_P", "first"),
                               worst_loo_P=("loo_P", "max")).to_string())
    print(worst[["excluded_set_genes", "loo_P"]].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
