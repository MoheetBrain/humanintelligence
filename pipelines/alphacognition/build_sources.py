#!/usr/bin/env python3
"""Assemble evidence/sources/alphacognition.yaml from curated + machine-generated parts.

Contract §2 gives each agent exactly one source file. This atlas produces source records
from two places — hand curation and three ingestion pipelines — so the single file is
assembled deterministically instead of being hand-merged:

    atlases/alphacognition/sources_curated.yaml          (authored)
    pipelines/alphacognition/generated/sources_*.yaml    (machine)
        -> evidence/sources/alphacognition.yaml

Duplicate `source_id`s are merged, not duplicated: the curated record wins on the fields
it sets (it is the one a human reasoned about) and the machine record contributes any key
the curated one omits, with the machine record's provenance kept under
`also_discovered_by`. The output is sorted by source_id so the file is stable across runs.

Usage
-----
    python pipelines/alphacognition/build_sources.py
    python pipelines/alphacognition/build_sources.py --check   # exit 1 if out of date
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import GENERATED_DIR, REPO_ROOT  # type: ignore[import-not-found]  # noqa: E402

CURATED = REPO_ROOT / "atlases" / "alphacognition" / "sources_curated.yaml"
OUTPUT = REPO_ROOT / "evidence" / "sources" / "alphacognition.yaml"

HEADER = """# ASSEMBLED FILE — do not hand-edit.
# Built by pipelines/alphacognition/build_sources.py from:
#   atlases/alphacognition/sources_curated.yaml        (hand-curated, {curated} records)
#   pipelines/alphacognition/generated/sources_*.yaml  (machine-generated, {machine} records)
#
# Every PMID here was discovered through a tool call in this session and its
# title/year/journal/first author were read from the registry of record (NCBI ESummary,
# ClinicalTrials.gov API v2) rather than authored, so scripts/fetch_source_metadata.py
# verifies against the same authority that supplied the strings.
#
# Known verification gap: `SRC:DB:*` records (database releases) are reported by
# scripts/fetch_source_metadata.py as `unsupported_registry`, because that script's
# dispatch handles PMID/DOI/NCT/GCST only. The releases are real and are recorded from the
# APIs' own metadata endpoints; see docs/blackboard/schema_change_requests/
# alphacognition-001.yaml for the requested fix.
#
# Total records: {total}
"""


def load_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(content, list):
        raise SystemExit(f"{path}: expected a YAML list")
    return content


# The source schema (schemas/source.schema.json) sets additionalProperties: false at every
# level, so this is the single place where every record is projected onto the legal shape.
# Anything informative that does not fit a schema field is folded into `notes` rather than
# dropped, because the retrieval route is the audit trail for "no identifier from memory".
ALLOWED_TOP = {
    "source_id", "source_type", "title", "year", "first_author", "container",
    "identifiers", "notes", "retrieval", "schema_version", "added_by", "added_on",
}
ALLOWED_IDENTIFIERS = {"database_release", "dataset_id", "doi", "gcst", "nct", "pmc", "pmid"}
IDENTIFIER_ALIASES = {
    "nct_id": "nct", "data_release_date": "database_release", "data_version": "database_release",
    "pmcid": "pmc", "gcst_id": "gcst",
}


def normalise(record: dict[str, Any]) -> dict[str, Any]:
    """Project one source record onto schemas/source.schema.json, losing no information."""
    out: dict[str, Any] = {}
    extra_notes: list[str] = []

    identifiers: dict[str, Any] = {}
    for key, value in (record.get("identifiers") or {}).items():
        key = IDENTIFIER_ALIASES.get(key, key)
        if key in ALLOWED_IDENTIFIERS:
            identifiers[key] = value
        elif value not in (None, "", [], {}):
            extra_notes.append(f"{key}: {value}")

    retrieval = record.get("retrieval") or {}
    method = retrieval.get("method")
    for key, value in retrieval.items():
        if key == "method":
            continue
        if value not in (None, "", [], {}):
            extra_notes.append(f"{key}: {value}")

    for key, value in record.items():
        if key in {"identifiers", "retrieval", "note", "notes"}:
            continue
        if key in ALLOWED_TOP:
            out[key] = value
        elif value not in (None, "", [], {}):
            extra_notes.append(f"{key}: {value}")

    note_parts = [str(n) for n in (record.get("note"), record.get("notes")) if n]
    note_parts.extend(extra_notes)
    out["schema_version"] = "0.1.0"
    if identifiers:
        out["identifiers"] = identifiers
    if method:
        out["retrieval"] = {"method": method}
    if note_parts:
        out["notes"] = " | ".join(" ".join(str(part).split()) for part in note_parts)
    order = [
        "source_id", "schema_version", "source_type", "title", "year", "first_author",
        "container", "identifiers", "retrieval", "added_by", "added_on", "notes",
    ]
    return {k: out[k] for k in order if k in out} | {k: v for k, v in out.items() if k not in order}


def merge(curated: list[dict[str, Any]], machine: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in machine:
        source_id = str(record["source_id"])
        if source_id in by_id:
            continue
        by_id[source_id] = dict(record)
    for record in curated:
        source_id = str(record["source_id"])
        if source_id in by_id:
            machine_record = by_id[source_id]
            merged = {**machine_record, **record}
            machine_route = (machine_record.get("retrieval") or {}).get("method")
            if machine_route and machine_route != (record.get("retrieval") or {}).get("method"):
                merged["note"] = " | ".join(
                    x for x in [record.get("note"), f"also discovered via {machine_route}"] if x
                )
            by_id[source_id] = merged
        else:
            by_id[source_id] = dict(record)
    return [normalise(by_id[key]) for key in sorted(by_id)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="do not write; fail if the output would change")
    args = parser.parse_args(argv)

    curated = load_list(CURATED)
    machine: list[dict[str, Any]] = []
    for path in sorted(GENERATED_DIR.glob("sources_*.yaml")):
        machine.extend(load_list(path))

    records = merge(curated, machine)
    body = HEADER.format(curated=len(curated), machine=len(machine), total=len(records)) + yaml.safe_dump(
        records, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False
    )

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != body:
            print(f"{OUTPUT} is out of date; run build_sources.py")
            return 1
        print(f"{OUTPUT} is up to date ({len(records)} records)")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(body, encoding="utf-8")
    pmids = sum(1 for r in records if str(r["source_id"]).startswith("SRC:PMID:"))
    ncts = sum(1 for r in records if str(r["source_id"]).startswith("SRC:NCT:"))
    dbs = sum(1 for r in records if str(r["source_id"]).startswith("SRC:DB:"))
    print(
        f"{OUTPUT}: {len(records)} records "
        f"({pmids} PMID, {ncts} NCT, {dbs} database release; "
        f"{len(curated)} curated, {len(machine)} machine-generated before merge)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
