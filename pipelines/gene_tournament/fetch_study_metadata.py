#!/usr/bin/env python3
"""Sprint 3, Part A/B — per-study metadata, so studies can be classified before counting.

Why a trait label is not enough
-------------------------------
The Sprint-3 channel map separates educational attainment from cognition by EFO trait.
That separation leaks. Inside the *direct-cognition* EFO terms the Catalog files:

* MTAG analyses that borrow statistical power from educational attainment;
* a GenomicSEM decomposition titled "Cognitive aspects of educational attainment", which
  is a component *of EA*, not a cognitive test;
* cross-trait pleiotropy scans ("ADHD or autism spectrum disorder or intelligence");
* multivariate personality-and-cognition analyses;
* "cognitive resilience to Alzheimer's disease pathology", a clinical construct.

Counting these as direct cognition would reintroduce, study by study, the EA
contamination the channel map exists to stop. This module fetches each study's own record
(sample description, cohorts, ancestry) so that ``classify_studies.py`` can decide
admissibility from what the study *is*, not from the ontology node it was filed under.

Usage
-----
    python pipelines/gene_tournament/fetch_study_metadata.py
    python pipelines/gene_tournament/fetch_study_metadata.py --offline
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import http_get_json, iter_snapshots, read_snapshot, write_snapshot  # noqa: E402

STUDIES = "https://www.ebi.ac.uk/gwas/rest/api/v2/studies/{}"
REGISTRY = "gwas_catalog_tournament_studies"
OUT = REPO_ROOT / "data" / "gene_tournament" / "study_metadata.jsonl"


def accessions() -> dict[str, dict]:
    seen: dict[str, dict] = {}
    for path in glob.glob(str(REPO_ROOT / "data/raw/gwas_catalog_tournament/*/EFO_*.json.gz")):
        payload = json.loads(gzip.open(path, "rt").read())
        for assoc in (payload.get("_embedded") or {}).get("associations") or []:
            acc = assoc.get("accession_id")
            if acc and acc not in seen:
                seen[acc] = {"pubmed_id": str(assoc.get("pubmed_id") or ""),
                             "first_author": assoc.get("first_author") or "",
                             "reported_trait": "; ".join(assoc.get("reported_trait") or [])}
    return seen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    base = accessions()
    records = {}
    if args.offline:
        for path in iter_snapshots(REGISTRY):
            payload = read_snapshot(path)
            if payload.get("accession_id"):
                records[payload["accession_id"]] = payload
    else:
        for i, acc in enumerate(sorted(base)):
            try:
                payload = http_get_json(STUDIES.format(acc))
                write_snapshot(REGISTRY, payload, url=STUDIES.format(acc),
                               query={"accession": acc}, name_hint=acc, compress=True)
                records[acc] = payload
            except Exception as error:  # noqa: BLE001 - recorded per study, never as absence
                records[acc] = {"accession_id": acc, "_fetch_error": f"{type(error).__name__}: {error}"}
            if i % 50 == 0:
                print(f"  {i:4d}/{len(base)}")
            time.sleep(0.15)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as handle:
        for acc in sorted(base):
            rec = records.get(acc, {"_fetch_error": "not_fetched"})
            row = {**base[acc], "accession_id": acc,
                   "initial_sample_size": rec.get("initial_sample_size"),
                   "replication_sample_size": rec.get("replication_sample_size"),
                   "cohort": rec.get("cohort"),
                   "discovery_ancestry": rec.get("discovery_ancestry"),
                   "full_summary_stats_available": rec.get("full_summary_stats_available"),
                   "disease_trait": rec.get("disease_trait"),
                   "fetch_error": rec.get("_fetch_error")}
            handle.write(json.dumps(row, default=str) + "\n")
    n_err = sum(1 for r in records.values() if r.get("_fetch_error"))
    print(f"studies: {len(base)}   fetched: {len(base) - n_err}   errors: {n_err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
