#!/usr/bin/env python3
"""Resolve the comparative species panel's NCBI taxonomy identifiers.

Why this exists
---------------
``docs/DATA_CONTRACT.md`` §1.1 requires every ``SPECIES:NCBITaxon:{taxid}`` node id to
carry a taxid **resolved via the NCBI taxonomy API, never from memory**. An agent that
types ``9606`` from recall has fabricated an identifier even when the number happens to
be right, because nothing in the repository can tell the two cases apart. This script
makes the resolution mechanical and auditable:

1. ``esearch`` the scientific name in ``db=taxonomy`` to obtain candidate taxids.
2. ``esummary`` every candidate taxid in one batched request.
3. Accept a candidate only when the registry's ``scientificname`` matches the queried
   name after normalisation, and when ``rank`` is ``species`` (or the caller declared a
   different expected rank). Ambiguous or mismatching names are recorded as failures,
   never silently resolved to the first hit.
4. Persist every response verbatim under ``data/raw/ncbi_taxonomy/{UTC date}/`` with a
   ``data/raw/MANIFEST.jsonl`` line (``scripts/_provenance.write_snapshot``), then write
   the derived index ``data/interim/comparative_species_taxonomy.jsonl``.

``--offline`` rebuilds the derived index from existing snapshots with no network access,
which is contract principle P7. The panel document
``atlases/comparative/species_panel.yaml`` is written by hand from this index; the
``taxid_provenance`` field of each panel entry names the snapshot this script produced.

Rate limits
-----------
NCBI allows ~3 requests/second per machine without an API key, and several agents share
this repository's machine. Requests are therefore batched (one ``esearch`` per species,
one ``esummary`` for all taxids at once) and paced by ``_provenance.ncbi_sleep``.

Usage
-----
    python pipelines/comparative/fetch_taxonomy.py              # fetch + resolve
    python pipelines/comparative/fetch_taxonomy.py --offline    # rebuild index only
    python pipelines/comparative/fetch_taxonomy.py --species "Corvus corax"

Exit status is 0 only when every requested species resolved unambiguously. A non-zero
exit means the panel cannot be written for at least one species — that is a defect to
report, not a licence to guess the taxid.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _provenance import (  # type: ignore[import-not-found]  # noqa: E402
    INTERIM_DIR,
    http_get_json,
    iter_snapshots,
    ncbi_params,
    ncbi_sleep,
    normalise_title,
    scrub_query,
    utc_now,
    write_jsonl,
    write_snapshot,
)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
REGISTRY = "ncbi_taxonomy"
INDEX_PATH = INTERIM_DIR / "comparative_species_taxonomy.jsonl"

# The panel, as scientific names only. Common names and panel rationale live in
# atlases/comparative/species_panel.yaml; this file holds nothing but what is needed to
# ask NCBI the question. Order is the panel's reading order, not a ranking.
PANEL: tuple[dict[str, str], ...] = (
    {"scientific_name": "Homo sapiens", "common_name": "human", "clade": "primate_hominid"},
    {"scientific_name": "Pan troglodytes", "common_name": "chimpanzee", "clade": "primate_hominid"},
    {"scientific_name": "Macaca mulatta", "common_name": "rhesus macaque", "clade": "primate_cercopithecid"},
    {"scientific_name": "Mus musculus", "common_name": "house mouse", "clade": "rodent_murid"},
    {"scientific_name": "Rattus norvegicus", "common_name": "Norway rat", "clade": "rodent_murid"},
    {"scientific_name": "Tursiops truncatus", "common_name": "common bottlenose dolphin", "clade": "cetacean_odontocete"},
    {"scientific_name": "Loxodonta africana", "common_name": "African savanna elephant", "clade": "proboscidean"},
    {"scientific_name": "Corvus moneduloides", "common_name": "New Caledonian crow", "clade": "bird_corvid"},
    {"scientific_name": "Corvus corax", "common_name": "common raven", "clade": "bird_corvid"},
    {"scientific_name": "Psittacus erithacus", "common_name": "grey parrot", "clade": "bird_psittacid"},
    {"scientific_name": "Nestor notabilis", "common_name": "kea", "clade": "bird_psittacid"},
    {"scientific_name": "Octopus vulgaris", "common_name": "common octopus", "clade": "cephalopod_octopod"},
    # Octopus bimaculoides is a distinct species from O. vulgaris and is the one most
    # cephalopod genome/RNA-editing work was actually done in. Both are resolved so that
    # a finding in one is never silently attributed to the other.
    {"scientific_name": "Octopus bimaculoides", "common_name": "California two-spot octopus", "clade": "cephalopod_octopod"},
)

# Species that appear in a comparative claim's ``context.species`` but are not panel
# members. They are resolved here for the same reason the panel is: a claim may not name
# a species by a taxid nobody looked up. Every entry below was named in a source
# retrieved during curation.
CITED_SPECIES: tuple[dict[str, str], ...] = (
    {"scientific_name": "Balaenoptera acutorostrata", "common_name": "northern minke whale", "clade": "cetacean_mysticete"},
    # Sources call this bird Corvus monedula; NCBI's accepted scientific name is
    # Coloeus monedula, with Corvus monedula as a synonym. The strict name match in
    # ``resolve`` refused the synonym rather than silently accepting the synonym hit,
    # which is the behaviour this guard exists for.
    {"scientific_name": "Coloeus monedula", "common_name": "Eurasian jackdaw", "clade": "bird_corvid"},
    {"scientific_name": "Phasianus colchicus", "common_name": "common pheasant", "clade": "bird_galliform"},
    {"scientific_name": "Columba livia", "common_name": "rock dove", "clade": "bird_columbiform"},
    {"scientific_name": "Tyto alba", "common_name": "barn owl", "clade": "bird_strigiform"},
    {"scientific_name": "Pan paniscus", "common_name": "bonobo", "clade": "primate_hominid"},
    {"scientific_name": "Gorilla gorilla", "common_name": "western gorilla", "clade": "primate_hominid"},
    {"scientific_name": "Callithrix jacchus", "common_name": "common marmoset", "clade": "primate_callitrichid"},
    {"scientific_name": "Suncus etruscus", "common_name": "Etruscan shrew", "clade": "eulipotyphlan"},
    {"scientific_name": "Meriones unguiculatus", "common_name": "Mongolian gerbil", "clade": "rodent_murid"},
    {"scientific_name": "Cavia porcellus", "common_name": "guinea pig", "clade": "rodent_caviomorph"},
    {"scientific_name": "Oryctolagus cuniculus", "common_name": "European rabbit", "clade": "lagomorph"},
    # The laboratory ferret is the domestic form Mustela putorius furo; the species rank
    # record is Mustela putorius, which is what a SPECIES: node may legally carry.
    {"scientific_name": "Mustela putorius", "common_name": "European polecat (ferret)", "clade": "carnivoran"},
)

EXPECTED_RANK = "species"


# --------------------------------------------------------------------------- fetch
def esearch_taxonomy(name: str) -> tuple[list[str], Path]:
    """Return candidate taxids for a scientific name, plus the snapshot path."""
    query = ncbi_params({"db": "taxonomy", "retmode": "json", "term": f"{name}[Scientific Name]"})
    payload = http_get_json(f"{EUTILS}/esearch.fcgi", params=query)
    ncbi_sleep()
    snapshot = write_snapshot(
        REGISTRY,
        payload,
        url=f"{EUTILS}/esearch.fcgi",
        query=scrub_query(query),
        name_hint=f"esearch_{_slug(name)}",
    )
    ids = list(payload.get("esearchresult", {}).get("idlist", []) or [])
    return ids, snapshot


def esummary_taxonomy(taxids: list[str]) -> tuple[dict[str, Any], Path]:
    """ESummary for every taxid in one request (≤200 ids per NCBI's limit)."""
    query = ncbi_params({"db": "taxonomy", "retmode": "json", "id": ",".join(taxids)})
    payload = http_get_json(f"{EUTILS}/esummary.fcgi", params=query)
    ncbi_sleep()
    snapshot = write_snapshot(
        REGISTRY,
        payload,
        url=f"{EUTILS}/esummary.fcgi",
        query=scrub_query(query),
        name_hint=f"esummary_n{len(taxids)}",
    )
    return payload, snapshot


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()


# ------------------------------------------------------------------------ resolve
def summaries_from_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract ``{taxid: record}`` from an ESummary payload."""
    result = payload.get("result") or {}
    uids = result.get("uids") or []
    return {str(uid): result.get(str(uid), {}) for uid in uids}


def resolve(
    entries: Iterable[dict[str, str]],
    *,
    offline: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Resolve each panel entry to exactly one taxid, or record why it could not be."""
    entries = list(entries)
    summaries: dict[str, dict[str, Any]] = {}
    summary_snapshot: str | None = None
    search_snapshots: dict[str, str] = {}
    candidates: dict[str, list[str]] = {}

    if offline:
        for path in iter_snapshots(REGISTRY):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if "esearchresult" in payload:
                ids = list(payload["esearchresult"].get("idlist", []) or [])
                term = str(payload["esearchresult"].get("querytranslation", ""))
                for entry in entries:
                    if normalise_title(entry["scientific_name"]) in normalise_title(term):
                        candidates[entry["scientific_name"]] = ids
                        search_snapshots[entry["scientific_name"]] = _rel(path)
            elif "result" in payload:
                found = summaries_from_payload(payload)
                if found:
                    summaries.update(found)
                    summary_snapshot = _rel(path)
    else:
        for entry in entries:
            ids, snapshot = esearch_taxonomy(entry["scientific_name"])
            candidates[entry["scientific_name"]] = ids
            search_snapshots[entry["scientific_name"]] = _rel(snapshot)
        all_ids = sorted({i for ids in candidates.values() for i in ids})
        if all_ids:
            payload, snapshot = esummary_taxonomy(all_ids)
            summaries = summaries_from_payload(payload)
            summary_snapshot = _rel(snapshot)

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for entry in entries:
        name = entry["scientific_name"]
        ids = candidates.get(name, [])
        matched = [
            taxid
            for taxid in ids
            if normalise_title(str(summaries.get(taxid, {}).get("scientificname", "")))
            == normalise_title(name)
        ]
        row: dict[str, Any] = {
            "scientific_name": name,
            "common_name_panel": entry["common_name"],
            "clade": entry["clade"],
            "role": entry.get("role", "panel"),
            "queried_on": utc_now(),
            "candidate_taxids": ids,
            "esearch_snapshot": search_snapshots.get(name),
            "esummary_snapshot": summary_snapshot,
            "species_id": None,
            "taxid": None,
            "registry_scientific_name": None,
            "registry_common_name": None,
            "registry_rank": None,
            "registry_division": None,
            "status": "unresolved",
        }
        if len(matched) == 1:
            taxid = matched[0]
            record = summaries.get(taxid, {})
            rank = str(record.get("rank", ""))
            row.update(
                {
                    "taxid": taxid,
                    "species_id": f"SPECIES:NCBITaxon:{taxid}",
                    "registry_scientific_name": record.get("scientificname"),
                    "registry_common_name": record.get("commonname") or record.get("genbankcommonname"),
                    "registry_rank": rank or None,
                    "registry_division": record.get("division"),
                    "status": "resolved" if rank == EXPECTED_RANK else "rank_mismatch",
                }
            )
            if rank != EXPECTED_RANK:
                failures.append(f"{name}: rank {rank!r} != {EXPECTED_RANK!r}")
        elif not ids:
            row["status"] = "not_found"
            failures.append(f"{name}: no taxonomy record")
        elif not matched:
            row["status"] = "name_mismatch"
            failures.append(f"{name}: {len(ids)} candidate(s), none with a matching scientific name")
        else:
            row["status"] = "ambiguous"
            failures.append(f"{name}: {len(matched)} taxids match the scientific name")
        rows.append(row)
    return rows, failures


def _rel(path: Path) -> str:
    root = Path(__file__).resolve().parents[2]
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="rebuild the index from snapshots, no network")
    parser.add_argument(
        "--species",
        action="append",
        default=None,
        metavar="SCIENTIFIC_NAME",
        help="restrict to one panel species (repeatable); must already be in PANEL",
    )
    args = parser.parse_args(argv)

    all_entries = [dict(e, role="panel") for e in PANEL] + [
        dict(e, role="cited_only") for e in CITED_SPECIES
    ]
    entries = list(all_entries)
    if args.species:
        wanted = {normalise_title(s) for s in args.species}
        entries = [e for e in all_entries if normalise_title(e["scientific_name"]) in wanted]
        unknown = wanted - {normalise_title(e["scientific_name"]) for e in all_entries}
        if unknown:
            print(f"not in PANEL or CITED_SPECIES: {sorted(unknown)}", file=sys.stderr)
            return 2

    rows, failures = resolve(entries, offline=args.offline)
    write_jsonl(INDEX_PATH, rows)

    resolved = [r for r in rows if r["status"] == "resolved"]
    print(f"resolved {len(resolved)}/{len(rows)} species -> {_rel(INDEX_PATH)}")
    for row in rows:
        mark = "ok " if row["status"] == "resolved" else "FAIL"
        print(f"  {mark} [{row['role']:<10}] {row['scientific_name']:<28} {row['species_id'] or row['status']}")
    for failure in failures:
        print(f"  unresolved: {failure}", file=sys.stderr)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
