#!/usr/bin/env python3
"""All catalogued GWAS associations per seed gene, for phenotype-specificity assessment.

Why this exists
---------------
`fetch_gwas_catalog.py` asks a narrow question: gene x cognitive-panel trait. That cannot
answer the `human_phenotype_specificity` facet, whose proposition is *comparative* — is
the catalogued human genetic signal at this gene about cognitive ability, or is the gene
a broadly pleiotropic locus whose cognitive hit is one of many? Answering it needs the
denominator: every trait the catalogue associates with the gene.

This pipeline fetches `GET /v2/associations?mapped_gene={SYMBOL}` unfiltered (the second
pattern in docs/API_RECIPES.md §4) and partitions the traits into
cognitive-panel / educational-attainment-or-literacy / other.

Same caveats as everywhere else in this atlas: `mapped_genes` is positional annotation,
so a "pleiotropic gene" here may really be a pleiotropic *locus*. The derived table says
so in `mapping_basis` and no claim is generated from this pipeline at all — it produces
only the counts that the facet assessments cite.

Outputs
-------
``data/raw/gwas_catalog/<UTC date>/pantrait_*.json``   immutable snapshots
``data/interim/gwas_catalog_gene_pleiotropy.jsonl``    derived counts per gene
``pipelines/alphacognition/generated/pleiotropy_summary.json``

Usage
-----
    python pipelines/alphacognition/fetch_gene_pleiotropy.py
    python pipelines/alphacognition/fetch_gene_pleiotropy.py --offline
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # type: ignore[import-not-found]  # noqa: E402
    GENERATED_DIR,
    load_panel,
    read_json,
    seed_gene_symbols,
    self_href_params,
    snapshots,
)
from _provenance import (  # type: ignore[import-not-found]  # noqa: E402
    INTERIM_DIR,
    http_get_json,
    utc_date,
    write_snapshot,
)

GWAS_BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"
RAW_REGISTRY = "gwas_catalog"
PAGE_SIZE = 100
MAX_PAGES = 30

DERIVED_PATH = INTERIM_DIR / "gwas_catalog_gene_pleiotropy.jsonl"
SUMMARY_PATH = GENERATED_DIR / "pleiotropy_summary.json"


def fetch_all_for_gene(gene: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    url = f"{GWAS_BASE}/associations"
    for page in range(MAX_PAGES):
        params = {"mapped_gene": gene, "page": page, "size": PAGE_SIZE}
        payload = http_get_json(url, params=params)
        write_snapshot(
            RAW_REGISTRY, payload, url=url, query=params, name_hint=f"pantrait_{gene}_p{page}"
        )
        batch = ((payload.get("_embedded") or {}).get("associations")) or []
        rows.extend(batch)
        info = payload.get("page") or {}
        if not batch or page + 1 >= int(info.get("totalPages") or 1):
            break
    return rows


def load_offline() -> dict[str, list[dict[str, Any]]]:
    """Pan-trait snapshots are the association responses that carry NO efo_id filter."""
    out: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for path in snapshots(RAW_REGISTRY):
        payload = read_json(path)
        params = self_href_params(payload)
        if "mapped_gene" not in params or "efo_id" in params:
            continue
        gene = params["mapped_gene"]
        page = int(params.get("page") or 0)
        out.setdefault(gene, {})[page] = ((payload.get("_embedded") or {}).get("associations")) or []
    return {g: [r for _, batch in sorted(pages.items()) for r in batch] for g, pages in out.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--genes", nargs="*")
    args = parser.parse_args(argv)

    panel = load_panel()
    cognitive_efos = {
        t["efo_id"] for t in panel if t.get("queried") and not t.get("is_educational_attainment")
    }
    ea_efos = {t["efo_id"] for t in panel if t.get("is_educational_attainment")}

    genes = sorted(set(args.genes)) if args.genes else seed_gene_symbols()
    raw = load_offline() if args.offline else {g: fetch_all_for_gene(g) for g in genes}

    rows: list[dict[str, Any]] = []
    for gene in genes:
        records = raw.get(gene) or []
        cognitive = 0
        ea = 0
        other = 0
        other_traits: set[str] = set()
        cognitive_traits: set[str] = set()
        for record in records:
            efos = {str(t.get("efo_id")) for t in (record.get("efo_traits") or [])}
            labels = {str(t.get("efo_trait")) for t in (record.get("efo_traits") or [])}
            if efos & cognitive_efos:
                cognitive += 1
                cognitive_traits |= labels & {
                    str(t["label"]) for t in panel if t["efo_id"] in cognitive_efos
                }
            elif efos & ea_efos:
                ea += 1
            else:
                other += 1
                other_traits |= labels
        rows.append(
            {
                "gene_symbol": gene,
                "associations_total": len(records),
                "associations_cognitive_panel": cognitive,
                "associations_educational_or_literacy": ea,
                "associations_other_traits": other,
                "distinct_other_traits": len(other_traits),
                "other_trait_examples": sorted(other_traits)[:25],
                "cognitive_panel_traits_hit": sorted(cognitive_traits),
                "mapping_basis": "gwas_catalog_mapped_genes_positional",
                "caveat": "a pleiotropic count here describes the LOCUS, not necessarily this gene",
                "snapshot_dir": f"data/raw/{RAW_REGISTRY}/",
            }
        )
    rows.sort(key=lambda r: r["gene_symbol"])

    DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DERIVED_PATH, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    summary = {
        "mode": "offline" if args.offline else "online",
        "generated_on": utc_date(),
        "genes": len(rows),
        "genes_with_any_association": sum(1 for r in rows if r["associations_total"]),
        "genes_with_cognitive_panel_association": sum(1 for r in rows if r["associations_cognitive_panel"]),
        "genes_with_only_non_cognitive_associations": sum(
            1 for r in rows if r["associations_total"] and not r["associations_cognitive_panel"]
        ),
        "total_associations_seen": sum(r["associations_total"] for r in rows),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
