#!/usr/bin/env python3
"""Sprint 3, Part R -- orthology for tournament genes, run only AFTER the human ranking.

Reuses the Sprint-2 Comparative 2.0 orthology audit (Ensembl Compara) on the LD-block lead
genes of the human ranking. Comparative evidence is ORTHOGONAL support at most: it may not
promote a gene the human evidence does not already support.

What is computed: orthology AVAILABILITY per species (one-to-one / other / no call).
What is NOT computed, and why (unchanged from Sprint 2, recorded in
atlases/comparative_v2/): selection scans and pathway convergence need a species tree,
trait covariates (brain/body size, lifespan, generation time, ecology, sociality) from
citable sources, and an operable avian/cephalopod arm. None exists yet. Corvids, parrots,
orca and octopus are absent from Ensembl Compara; a "no orthologue" there is a database
fact, never a biological one.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "pipelines" / "comparative"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
import orthology_audit as oa  # noqa: E402

OUT = REPO_ROOT / "reports" / "gene_tournament" / "comparative_top_genes.csv"


def main() -> int:
    # Only the genes the HUMAN ranking put on top -- comparative work never nominates.
    tops = [REPO_ROOT / "reports/gene_tournament" / n for n in
            ("TOP50_HUMAN_COGNITION_GENES.csv", "TOP50_ADULT_MODIFIABLE_GENES.csv")]
    genes = []
    for path in tops:
        for g in pd.read_csv(path).gene.dropna():
            if g not in genes:
                genes.append(g)
    genes += [g for g in ["EDAR", "SH3RF3", "SEPTIN10", "SOWAHC"] if g not in genes]
    available, unavailable = oa.panel_species()
    species = [s["ensembl_species"] for s in available]
    offline = "--offline" in sys.argv
    from _provenance import read_snapshot  # noqa: E402
    rows = []
    for i, sym in enumerate(genes):
        snaps = sorted((REPO_ROOT / "data" / "raw" / "ensembl_compara").glob(f"*/orth_{sym}_*.json*"))
        if offline:
            if not snaps:
                rows.append({"gene": sym, "query_status": "NOT_QUERIED (Ensembl run incomplete at build time)"})
                continue
            payload = read_snapshot(snaps[-1])
            s = oa.summarise(payload, species) if payload else {"query_status": "empty_snapshot"}
            rows.append({"gene": sym, **{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in s.items()}})
            continue
        try:
            payload = oa.fetch(sym, species)
            s = oa.summarise(payload, species) if payload else {"query_status": "no_response"}
        except Exception as error:  # noqa: BLE001 -- a failed query is recorded, never a negative
            s = {"query_status": f"failed: {type(error).__name__}"}
        rows.append({"gene": sym, **{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in s.items()}})
        if i % 25 == 0:
            print(f"  {i}/{len(genes)}", flush=True)
        time.sleep(0.1)
    frame = pd.DataFrame(rows)
    frame["species_not_in_compara"] = "|".join(s.get("common_name", s.get("ensembl_species", "?")) for s in unavailable)
    frame["interpretation"] = ("orthology availability only; no selection, no convergence, no function; "
                               "comparative evidence may not override weak human evidence")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    print(frame.head(3).T.to_string()[:1500])
    print(f"wrote {OUT} ({len(frame)} genes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
