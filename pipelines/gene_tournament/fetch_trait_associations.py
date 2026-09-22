#!/usr/bin/env python3
"""Sprint 3, Part A — fetch every cognitive-trait association the Catalog holds.

Why this exists rather than reusing the Sprint-2 sweep
------------------------------------------------------
The Sprint-2 discovery sweep (``pipelines/discovery/sweep_cognition_genes.py``) answered
one question — *which genes are mapped to cognition-associated variants at all?* — and
kept only counts. The gene tournament needs the statistics the aggregation discarded:
per-association p-value, effect direction, **effect allele**, and the study accession
that distinguishes one analysis from another.

It also needs traits the sweep never requested. The sweep ran ``--primary`` only, so
mathematical ability (EFO_0004875), visuospatial function (EFO_0803533) and the whole
educational-attainment proxy channel were never fetched. A tournament that ranks genes
for *mathematical* cognition cannot be built from a sweep that never asked about maths.

What this fetch is, and is not
------------------------------
GWAS Catalog associations are **curated top hits**, not genome-wide summary statistics.
Every gene-level quantity derived from them inherits three hard limits, recorded in the
output and repeated in every downstream report:

* **Ascertainment.** A variant is here because it passed a significance filter in a
  paper the Catalog curated. Absence of an association is not evidence of no effect.
* **Positional mapping.** ``mapped_genes`` means a variant lies in or near the gene.
  It is the weakest available claim about causality, and it is size-biased: long genes
  and gene-dense loci accumulate hits for reasons that are not biology.
* **No gene-based test is possible from these data.** MAGMA, PASCAL and VEGAS all
  require full genome-wide summary statistics plus an LD reference panel. Neither is
  in this repository. The tournament therefore reports a *catalogue-level* ranking and
  says so; it does not report a gene_Z it did not compute.

Usage
-----
    python pipelines/gene_tournament/fetch_trait_associations.py          # network
    python pipelines/gene_tournament/fetch_trait_associations.py --offline
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
    write_snapshot,
)

GWAS_V2 = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
METADATA = "https://www.ebi.ac.uk/gwas/rest/api/v2/metadata"
PANEL = REPO_ROOT / "atlases" / "alphacognition" / "cognitive_trait_panel.yaml"
REGISTRY = "gwas_catalog_tournament"
PAGE = 500
MAX_PAGES = 40


def panel_traits() -> list[dict[str, Any]]:
    """Every trait in the panel except those the panel marks ``excluded``.

    ``excluded`` traits are excluded here too, and the reason is carried into the
    universe artefact rather than left implicit: they are vague umbrella terms whose
    member studies are already counted under a specific trait, so including them would
    double-count the same analysis under two names.
    """
    panel = yaml.safe_load(PANEL.read_text(encoding="utf-8"))
    return [t for t in panel["traits"] if t.get("use_in_ranking") != "excluded"]


def fetch_trait(efo_id: str) -> tuple[list[dict[str, Any]], bool]:
    """Every association for one EFO trait, paginated, each page snapshotted gzipped.

    Returns the rows and whether the trait was read to exhaustion. A capped trait is
    reported as capped; it is never silently truncated, because a truncated fetch that
    looks complete is how a gene acquires a false zero.
    """
    rows: list[dict[str, Any]] = []
    complete = False
    for page in range(MAX_PAGES):
        params = {"efo_id": efo_id, "size": PAGE, "page": page}
        payload = http_get_json(GWAS_V2, params=params)
        write_snapshot(
            REGISTRY, payload, url=GWAS_V2, query=params,
            name_hint=f"{efo_id}_p{page}", compress=True,
        )
        batch = (payload.get("_embedded") or {}).get("associations") or []
        rows.extend(batch)
        info = payload.get("page") or {}
        total_pages = info.get("totalPages")
        if total_pages is not None and page + 1 >= total_pages:
            complete = True
            break
        if not batch:
            complete = True
            break
        time.sleep(0.2)
    return rows, complete


def load_offline() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in iter_snapshots(REGISTRY):
        if "release" in path.name:
            continue
        payload = read_snapshot(path)
        rows.extend((payload.get("_embedded") or {}).get("associations") or [])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="rebuild from snapshots")
    args = parser.parse_args(argv)

    traits = panel_traits()
    if args.offline:
        rows = load_offline()
        print(f"offline: {len(rows)} association records from snapshots")
        return 0

    try:
        meta = http_get_json(METADATA)
        release = meta.get("data_release_date")
        write_snapshot(REGISTRY, meta, url=METADATA, query={"endpoint": "metadata"},
                       name_hint="release", compress=True)
        print(f"GWAS Catalog data release: {release}\n")
    except Exception as error:  # noqa: BLE001 - absence is recorded, not fatal
        release = f"unavailable: {type(error).__name__}"
        print(f"! release metadata unavailable ({error})\n")

    total = 0
    capped: list[str] = []
    for trait in traits:
        efo = trait["efo_id"]
        batch, complete = fetch_trait(efo)
        total += len(batch)
        if not complete:
            capped.append(efo)
        flag = "" if complete else "  <-- CAPPED"
        print(f"  {efo:16s} {str(trait['use_in_ranking']):11s} "
              f"{str(trait['label'])[:40]:42s} {len(batch):5d}{flag}")
    print(f"\n{total} association records across {len(traits)} traits "
          f"(release {release})")
    if capped:
        print(f"CAPPED (incomplete): {capped}")
    print(f"fetched_at {utc_now()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
