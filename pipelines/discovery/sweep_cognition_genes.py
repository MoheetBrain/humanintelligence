#!/usr/bin/env python3
"""Genome-wide discovery sweep: which genes do cognition GWAS actually implicate?

Why this exists
---------------
Sprint 1 ranked 27 targets, every one supplied by the project brief. That is not
discovery, and a ranking over a hand-picked list cannot detect its own anchoring. This
sweep asks the GWAS Catalog the question the other way round — *which genes are mapped to
cognition-associated variants at all?* — and subtracts the seed list to see what the
brief never mentioned.

What the output is, and is not
------------------------------
GWAS Catalog ``mapped_genes`` are **positional**. A gene appears here because an
associated variant sits in or near it, which is the weakest available claim about
causality:

* not a causal gene — ``causal_attribution.basis: gwas_association_only``,
  ``locus_to_gene_resolved: no``;
* not an adult mechanism — an association says nothing about when a gene acts;
* not a direction — nothing here says whether more or less of the gene would help;
* not a target — a discovered gene enters the registry as a HYPOTHESIS and faces the same
  contract, red team and gates as a seeded one.

Gene-size and gene-density artefacts are the known failure mode: long genes and
gene-dense loci accumulate positional hits for reasons unrelated to biology. The output
therefore reports **distinct studies** and **distinct traits** beside the raw association
count, and the report says plainly that ranking by association count would largely be
measuring gene length.

Following X01's methodological instruction, this sweep is cell-class-agnostic and
genome-wide: no pyramidal gate and no prefilter of any kind.

Usage
-----
    python pipelines/discovery/sweep_cognition_genes.py --primary
    python pipelines/discovery/sweep_cognition_genes.py --primary --offline
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import (  # noqa: E402
    http_get_json,
    iter_snapshots,
    read_snapshot,
    utc_now,
    write_jsonl,
    write_snapshot,
)

GWAS_V2 = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
METADATA = "https://www.ebi.ac.uk/gwas/rest/api/v2/metadata"
PANEL = REPO_ROOT / "atlases" / "alphacognition" / "cognitive_trait_panel.yaml"
SEED_REGISTRY = REPO_ROOT / "targets" / "seed_registry.yaml"
OUT = REPO_ROOT / "data" / "interim" / "discovery_cognition_genes.jsonl"
PAGE = 500

SKIP_SYMBOLS = {"na", "nan", "intergenic", "none", ""}


def panel_traits(use: set[str]) -> list[dict[str, Any]]:
    panel = yaml.safe_load(PANEL.read_text(encoding="utf-8"))
    return [t for t in panel["traits"] if t.get("use_in_ranking") in use]


def seed_symbols() -> set[str]:
    registry = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for target in registry["targets"]:
        symbols.add(str(target["symbol"]))
        for member in target.get("member_genes") or []:
            symbols.add(str(member))
    return symbols


def fetch_trait(efo_id: str) -> list[dict[str, Any]]:
    """Every association for one EFO trait, paginated, each page snapshotted gzipped."""
    rows: list[dict[str, Any]] = []
    page = 0
    while True:
        params = {"efo_id": efo_id, "size": PAGE, "page": page}
        payload = http_get_json(GWAS_V2, params=params)
        write_snapshot(
            "gwas_catalog_sweep",
            payload,
            url=GWAS_V2,
            query=params,
            name_hint=f"{efo_id}_p{page}",
            compress=True,
        )
        batch = (payload.get("_embedded") or {}).get("associations") or []
        rows.extend(batch)
        info = payload.get("page") or {}
        total_pages = int(info.get("totalPages") or 1)
        page += 1
        time.sleep(0.2)
        if page >= total_pages or not batch:
            break
    return rows


def load_offline() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in iter_snapshots("gwas_catalog_sweep"):
        payload = read_snapshot(path)
        rows.extend((payload.get("_embedded") or {}).get("associations") or [])
    return rows


def aggregate(rows: list[dict[str, Any]], trait_class: dict[str, str]) -> dict[str, dict[str, Any]]:
    genes: dict[str, dict[str, Any]] = {}
    for assoc in rows:
        efos = [t.get("efo_id") for t in (assoc.get("efo_traits") or []) if t.get("efo_id")]
        mapped = assoc.get("mapped_genes") or []
        for symbol in mapped:
            symbol = str(symbol).strip()
            if symbol.lower() in SKIP_SYMBOLS:
                continue
            entry = genes.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "n_associations": 0,
                    "studies": set(),
                    "pubmed_ids": set(),
                    "efo_traits": set(),
                    "phenotype_classes": set(),
                    "reported_traits": set(),
                    "strongest_p_as_reported": None,
                    "multi_gene_rows": 0,
                },
            )
            entry["n_associations"] += 1
            if assoc.get("accession_id"):
                entry["studies"].add(str(assoc["accession_id"]))
            if assoc.get("pubmed_id"):
                entry["pubmed_ids"].add(str(assoc["pubmed_id"]))
            for efo in efos:
                entry["efo_traits"].add(efo)
                if trait_class.get(efo):
                    entry["phenotype_classes"].add(trait_class[efo])
            for reported in assoc.get("reported_trait") or []:
                entry["reported_traits"].add(str(reported))
            if len(mapped) > 1:
                entry["multi_gene_rows"] += 1
            p = assoc.get("p_value")
            if p is not None:
                current = entry["strongest_p_as_reported"]
                try:
                    if current is None or float(p) < float(current):
                        entry["strongest_p_as_reported"] = p
                except (TypeError, ValueError):
                    pass
    return genes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--primary", action="store_true",
        help="sweep traits marked use_in_ranking: primary (the default set)",
    )
    parser.add_argument(
        "--include-supporting", action="store_true",
        help="also sweep 'supporting' traits; their phenotype_classes are recorded so a "
             "gene resting only on a supporting trait is visible as such",
    )
    parser.add_argument("--offline", action="store_true", help="rebuild from snapshots")
    args = parser.parse_args(argv)

    use = {"primary"} | ({"supporting"} if args.include_supporting else set())
    if not use:
        use = {"primary"}
    traits = panel_traits(use)
    trait_class = {t["efo_id"]: t.get("phenotype_class") for t in traits}

    release = None
    if not args.offline:
        # The release date is provenance, not data. If the metadata endpoint is down the
        # sweep still runs, but the absence is RECORDED in every output row rather than
        # left blank — an unpinned release is a real limitation on reproducibility.
        try:
            meta = http_get_json(METADATA)
            release = meta.get("data_release_date")
            write_snapshot(
                "gwas_catalog_sweep", meta, url=METADATA,
                query={"endpoint": "metadata"}, name_hint="release", compress=True,
            )
            print(f"GWAS Catalog data release: {release}\n")
        except Exception as error:
            release = f"unavailable: {type(error).__name__}"
            print(f"! release metadata unavailable ({error}); recording it as unpinned\n")

    rows: list[dict[str, Any]] = []
    if args.offline:
        rows = load_offline()
    else:
        for trait in traits:
            batch = fetch_trait(trait["efo_id"])
            print(f"  {trait['efo_id']:16s} {str(trait['label'])[:40]:42s} {len(batch):5d} associations")
            rows.extend(batch)

    genes = aggregate(rows, trait_class)
    seeds = seed_symbols()
    out_rows = [
        {
            "symbol": symbol,
            "in_seed_registry": symbol in seeds,
            "n_associations": entry["n_associations"],
            "n_distinct_studies": len(entry["studies"]),
            "n_distinct_efo_traits": len(entry["efo_traits"]),
            "n_multi_gene_rows": entry["multi_gene_rows"],
            "phenotype_classes": sorted(c for c in entry["phenotype_classes"] if c),
            "efo_traits": sorted(entry["efo_traits"]),
            "studies": sorted(entry["studies"]),
            "pubmed_ids": sorted(entry["pubmed_ids"]),
            "reported_traits": sorted(entry["reported_traits"])[:8],
            "strongest_p_as_reported": entry["strongest_p_as_reported"],
            "gwas_catalog_release": release,
            "swept_on": utc_now(),
            "causal_attribution_note": (
                "POSITIONAL MAPPING ONLY. This gene is listed because an associated variant "
                "lies in or near it. Not a causal gene, not a direction, not an adult "
                "mechanism, not a target."
            ),
        }
        for symbol, entry in genes.items()
    ]
    out_rows.sort(key=lambda r: (-r["n_distinct_studies"], -r["n_distinct_efo_traits"], r["symbol"]))
    write_jsonl(OUT, out_rows)

    novel = [r for r in out_rows if not r["in_seed_registry"]]
    print(f"\nassociations swept:        {len(rows)}")
    print(f"distinct mapped genes:     {len(out_rows)}")
    print(f"already in seed registry:  {len(out_rows) - len(novel)}")
    print(f"NOT in seed registry:      {len(novel)}")
    print(f"written to {OUT.relative_to(REPO_ROOT)}")
    print("\ntop novel genes by distinct studies (NOT a ranking of causal plausibility):")
    for row in novel[:15]:
        print(
            f"  {row['symbol']:14s} studies={row['n_distinct_studies']:2d} "
            f"traits={row['n_distinct_efo_traits']} assoc={row['n_associations']:3d} "
            f"classes={','.join(row['phenotype_classes'])[:44]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
