#!/usr/bin/env python3
"""Verify every cited source against its registry of record.

This is the repository's anti-fabrication mechanism. An agent writes what it
believes a source is (``evidence/sources/<agent>.yaml``); this script asks the
registry what the source actually is, keeps the raw answer forever, and writes a
verification verdict that the validator enforces.

Registries handled
------------------
``SRC:PMID:*``     PubMed ESummary (title, year, journal, DOI, publication types)
``SRC:DOI:*``      PubMed ESearch by DOI, then ESummary; unresolved DOIs are reported
``SRC:NCT:*``      ClinicalTrials.gov API v2 (title, status, phase, why-stopped)
``SRC:GCST:*``     GWAS Catalog REST API v2 study record
``SRC:DB:*``       release metadata recorded by the ingesting pipeline (not fetched here)
``SRC:DATASET:*``  not machine-verifiable; reported as ``unsupported_registry``

Usage
-----
    python scripts/fetch_source_metadata.py --all              # fetch + verify everything
    python scripts/fetch_source_metadata.py --agent brakes     # one agent's sources
    python scripts/fetch_source_metadata.py --offline          # rebuild index, no network

Exit status is 0 when every source verified, 1 when any source did not. The
non-zero exit is deliberate: an unverified citation is a defect, not a warning.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

from _provenance import (  # type: ignore[import-not-found]
    INTERIM_DIR,
    REPO_ROOT,
    FetchResult,
    http_get_json,
    iter_snapshots,
    ncbi_params,
    ncbi_sleep,
    scrub_query,
    title_similarity,
    utc_now,
    write_jsonl,
    write_snapshot,
)

SOURCES_DIR = REPO_ROOT / "evidence" / "sources"
VERIFICATION_DIR = INTERIM_DIR / "source_verification"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
GWAS_CATALOG = "https://www.ebi.ac.uk/gwas/rest/api/v2/studies"

TITLE_MATCH_THRESHOLD = 0.90
YEAR_TOLERANCE = 1  # e-pub vs print year

RETRACTION_TYPES = {"Retracted Publication", "Retraction of Publication"}


# --------------------------------------------------------------------------- IO
def load_source_files(agent: str | None) -> dict[str, list[dict[str, Any]]]:
    """Load ``evidence/sources/*.yaml``, keyed by agent name."""
    if not SOURCES_DIR.exists():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(SOURCES_DIR.glob("*.yaml")):
        name = path.stem
        if name.startswith("_") or (agent and name != agent):
            continue
        content = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(content, list):
            raise SystemExit(f"{path}: expected a YAML list of source records")
        out[name] = content
    return out


def parse_source_id(source_id: str) -> tuple[str, str]:
    """Split ``SRC:PMID:29942086`` into ``("PMID", "29942086")``."""
    parts = source_id.split(":", 2)
    if len(parts) != 3 or parts[0] != "SRC":
        raise ValueError(f"malformed source_id: {source_id!r}")
    return parts[1].upper(), parts[2]


# ---------------------------------------------------------------------- PubMed
def fetch_pubmed_batch(pmids: list[str]) -> FetchResult:
    """ESummary for up to 200 PMIDs in one request."""
    query = ncbi_params({"db": "pubmed", "retmode": "json", "id": ",".join(pmids)})
    payload = http_get_json(f"{EUTILS}/esummary.fcgi", params=query)
    ncbi_sleep()
    snapshot = write_snapshot(
        "pubmed_esummary",
        payload,
        url=f"{EUTILS}/esummary.fcgi",
        query=scrub_query(query),
        name_hint=f"n{len(pmids)}",
    )
    return FetchResult(payload=payload, snapshot=snapshot, url=f"{EUTILS}/esummary.fcgi")


def resolve_doi_to_pmid(doi: str) -> tuple[str | None, Path | None]:
    """ESearch a DOI to find its PMID (returns ``None`` when PubMed has no record)."""
    query = ncbi_params({"db": "pubmed", "retmode": "json", "term": f"{doi}[DOI]"})
    payload = http_get_json(f"{EUTILS}/esearch.fcgi", params=query)
    ncbi_sleep()
    snapshot = write_snapshot(
        "pubmed_esearch",
        payload,
        url=f"{EUTILS}/esearch.fcgi",
        query=scrub_query(query),
        name_hint="doi",
    )
    ids = payload.get("esearchresult", {}).get("idlist", [])
    return (ids[0] if ids else None), snapshot


def summarise_pubmed_record(record: dict[str, Any]) -> dict[str, Any]:
    """Extract the fields the contract verifies from one ESummary record."""
    article_ids = {item.get("idtype"): item.get("value") for item in record.get("articleids", [])}
    pubdate = str(record.get("pubdate") or record.get("epubdate") or "")
    year_match = re.search(r"\b(19|20)\d{2}\b", pubdate)
    authors = record.get("authors") or []
    first_author = authors[0].get("name") if authors and isinstance(authors[0], dict) else None
    pubtypes = list(record.get("pubtype") or [])
    return {
        "registry_title": record.get("title") or "",
        "registry_year": int(year_match.group(0)) if year_match else None,
        "registry_container": record.get("source"),
        "registry_doi": article_ids.get("doi"),
        "registry_pmid": article_ids.get("pubmed") or record.get("uid"),
        "registry_pmcid": article_ids.get("pmc"),
        "registry_first_author": first_author or record.get("sortfirstauthor"),
        "publication_types": pubtypes,
        "retraction_flag": bool(RETRACTION_TYPES.intersection(pubtypes)),
        "registry_pubdate": pubdate,
    }


# ------------------------------------------------------------ ClinicalTrials.gov
def fetch_ctgov(nct_id: str) -> FetchResult:
    """Fetch one registered study record from ClinicalTrials.gov API v2."""
    url = f"{CTGOV}/{nct_id}"
    payload = http_get_json(url)
    snapshot = write_snapshot("ctgov_v2", payload, url=url, query={"nct_id": nct_id}, name_hint=nct_id)
    return FetchResult(payload=payload, snapshot=snapshot, url=url)


def summarise_ctgov_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract verification fields from a ClinicalTrials.gov v2 study record."""
    protocol = payload.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    start = status.get("startDateStruct", {}).get("date", "") or ""
    year_match = re.search(r"\b(19|20)\d{2}\b", start)
    return {
        "registry_title": ident.get("officialTitle") or ident.get("briefTitle") or "",
        "registry_year": int(year_match.group(0)) if year_match else None,
        "registry_container": "ClinicalTrials.gov",
        "registry_doi": None,
        "registry_first_author": (
            protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name")
        ),
        "overall_status": status.get("overallStatus"),
        "why_stopped": status.get("whyStopped"),
        "phases": design.get("phases") or [],
        "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
        "publication_types": ["Clinical Trial Registration"],
        "retraction_flag": False,
    }


# ------------------------------------------------------------------ GWAS Catalog
def fetch_gwas_study(accession: str) -> FetchResult:
    """Fetch one GWAS Catalog study record (REST API v2)."""
    url = f"{GWAS_CATALOG}/{accession}"
    payload = http_get_json(url)
    snapshot = write_snapshot(
        "gwas_catalog_study", payload, url=url, query={"accession": accession}, name_hint=accession
    )
    return FetchResult(payload=payload, snapshot=snapshot, url=url)


def summarise_gwas_study(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract verification fields from a GWAS Catalog study record."""
    pub = payload.get("publication") or {}
    year = None
    date = str(pub.get("publication_date") or pub.get("publicationDate") or "")
    year_match = re.search(r"\b(19|20)\d{2}\b", date)
    if year_match:
        year = int(year_match.group(0))
    return {
        "registry_title": pub.get("title") or payload.get("reported_trait") or "",
        "registry_year": year,
        "registry_container": pub.get("journal") or "GWAS Catalog",
        "registry_doi": None,
        "registry_pmid": str(pub.get("pubmed_id")) if pub.get("pubmed_id") else None,
        "registry_first_author": pub.get("first_author") or pub.get("author"),
        "publication_types": ["Dataset"],
        "retraction_flag": False,
        "reported_trait": payload.get("reported_trait"),
        "initial_sample_size": payload.get("initial_sample_size"),
    }


# ------------------------------------------------------------------ verification
def verdict_for(record: dict[str, Any], registry_fields: dict[str, Any]) -> tuple[str, float]:
    """Compare the agent's record with the registry answer.

    Returns ``(status, title_similarity)`` where status is one of ``verified``,
    ``title_mismatch``, ``year_mismatch`` or ``retracted``.
    """
    similarity = title_similarity(record.get("title") or "", registry_fields.get("registry_title") or "")
    if registry_fields.get("retraction_flag"):
        return "retracted", similarity
    if similarity < TITLE_MATCH_THRESHOLD:
        return "title_mismatch", similarity
    claimed_year = record.get("year")
    registry_year = registry_fields.get("registry_year")
    if claimed_year and registry_year and abs(int(claimed_year) - int(registry_year)) > YEAR_TOLERANCE:
        return "year_mismatch", similarity
    return "verified", similarity


def verify_agent_sources(agent: str, records: list[dict[str, Any]], *, offline: bool) -> list[dict[str, Any]]:
    """Produce verification rows for one agent's source registrations."""
    cache = load_offline_cache() if offline else {}
    pmid_records: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []

    for record in records:
        try:
            registry, local = parse_source_id(str(record.get("source_id", "")))
        except ValueError as error:
            rows.append(
                {
                    "source_id": record.get("source_id"),
                    "agent": agent,
                    "status": "malformed_source_id",
                    "detail": str(error),
                    "checked_at": utc_now(),
                }
            )
            continue
        if registry == "PMID":
            pmid_records[local] = record
        else:
            other.append({"registry": registry, "local": local, "record": record})

    # --- PubMed, batched -----------------------------------------------------
    if pmid_records:
        summaries: dict[str, dict[str, Any]] = {}
        snapshots: dict[str, str] = {}
        if offline:
            for pmid in pmid_records:
                if pmid in cache:
                    summaries[pmid] = cache[pmid]["fields"]
                    snapshots[pmid] = cache[pmid]["snapshot"]
        else:
            pmids = sorted(pmid_records)
            for chunk in _chunks(pmids, 150):
                result = fetch_pubmed_batch(chunk)
                payload = result.payload.get("result", {})
                for pmid in chunk:
                    record = payload.get(pmid)
                    if not record or record.get("error"):
                        continue
                    summaries[pmid] = summarise_pubmed_record(record)
                    snapshots[pmid] = str(result.snapshot.relative_to(REPO_ROOT))
        for pmid, record in sorted(pmid_records.items()):
            fields = summaries.get(pmid)
            if not fields or not fields.get("registry_title"):
                rows.append(
                    {
                        "source_id": f"SRC:PMID:{pmid}",
                        "agent": agent,
                        "registry": "pubmed",
                        "status": "not_found" if not offline else "not_checked",
                        "detail": "PubMed returned no record for this identifier"
                        if not offline
                        else "no snapshot available offline",
                        "claimed_title": record.get("title"),
                        "checked_at": utc_now(),
                    }
                )
                continue
            status, similarity = verdict_for(record, fields)
            rows.append(
                {
                    "source_id": f"SRC:PMID:{pmid}",
                    "agent": agent,
                    "registry": "pubmed",
                    "status": status,
                    "title_similarity": similarity,
                    "claimed_title": record.get("title"),
                    "claimed_year": record.get("year"),
                    "snapshot": snapshots.get(pmid),
                    "checked_at": utc_now(),
                    **fields,
                }
            )

    # --- everything else, one request each -----------------------------------
    for item in other:
        registry, local, record = item["registry"], item["local"], item["record"]
        row: dict[str, Any] = {
            "source_id": record.get("source_id"),
            "agent": agent,
            "claimed_title": record.get("title"),
            "claimed_year": record.get("year"),
            "checked_at": utc_now(),
        }
        if offline:
            cached = offline_lookup(registry, local)
            if cached is None:
                row.update({"status": "not_checked", "detail": "no snapshot available offline", "registry": registry.lower()})
                rows.append(row)
                continue
            fields, snapshot_path, registry_name = cached
            status, similarity = verdict_for(record, fields)
            row.update(
                {
                    "status": status,
                    "registry": registry_name,
                    "title_similarity": similarity,
                    "snapshot": snapshot_path,
                    **fields,
                }
            )
            rows.append(row)
            continue
        try:
            if registry == "NCT":
                result = fetch_ctgov(local)
                fields = summarise_ctgov_record(result.payload)
                row["registry"] = "clinicaltrials_gov"
            elif registry == "GCST":
                result = fetch_gwas_study(local)
                fields = summarise_gwas_study(result.payload)
                row["registry"] = "gwas_catalog"
            elif registry == "DOI":
                pmid, snapshot = resolve_doi_to_pmid(local)
                row["registry"] = "pubmed_via_doi"
                if pmid is None:
                    row.update(
                        {
                            "status": "not_found",
                            "detail": "no PubMed record for this DOI; register the source by PMID if one exists",
                            "snapshot": str(snapshot.relative_to(REPO_ROOT)) if snapshot else None,
                        }
                    )
                    rows.append(row)
                    continue
                result = fetch_pubmed_batch([pmid])
                fields = summarise_pubmed_record(result.payload.get("result", {}).get(pmid, {}))
                row["resolved_pmid"] = pmid
                row["detail"] = "DOI resolves to a PubMed record; prefer registering it as SRC:PMID"
            else:
                row.update({"status": "unsupported_registry", "registry": registry.lower()})
                rows.append(row)
                continue
        except Exception as error:  # network/format failure is recorded, never guessed
            row.update({"status": "fetch_failed", "detail": f"{type(error).__name__}: {error}"})
            rows.append(row)
            continue
        status, similarity = verdict_for(record, fields)
        row.update(
            {
                "status": status,
                "title_similarity": similarity,
                "snapshot": str(result.snapshot.relative_to(REPO_ROOT)),
                **fields,
            }
        )
        rows.append(row)

    return sorted(rows, key=lambda r: str(r.get("source_id")))


def load_offline_cache() -> dict[str, dict[str, Any]]:
    """Rebuild a PMID -> summary map from the committed PubMed snapshots."""
    cache: dict[str, dict[str, Any]] = {}
    for path in iter_snapshots("pubmed_esummary"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for uid, record in (payload.get("result") or {}).items():
            if uid == "uids" or not isinstance(record, dict) or record.get("error"):
                continue
            fields = summarise_pubmed_record(record)
            if fields.get("registry_title"):
                cache[uid] = {"fields": fields, "snapshot": str(path.relative_to(REPO_ROOT))}
    return cache


def offline_lookup(registry: str, local: str) -> tuple[dict[str, Any], str, str] | None:
    """Find verification fields for a non-PubMed source in committed snapshots."""
    if registry == "NCT":
        for path in reversed(iter_snapshots("ctgov_v2")):
            payload = _read_json(path)
            nct = (payload.get("protocolSection", {}).get("identificationModule", {}) or {}).get("nctId")
            if nct == local:
                return summarise_ctgov_record(payload), str(path.relative_to(REPO_ROOT)), "clinicaltrials_gov"
    elif registry == "GCST":
        for path in reversed(iter_snapshots("gwas_catalog_study")):
            payload = _read_json(path)
            if payload.get("accession_id") == local:
                return summarise_gwas_study(payload), str(path.relative_to(REPO_ROOT)), "gwas_catalog"
    elif registry == "DOI":
        pmid = _doi_pmid_from_manifest(local)
        if pmid:
            cache = load_offline_cache()
            if pmid in cache:
                return cache[pmid]["fields"], cache[pmid]["snapshot"], "pubmed_via_doi"
    return None


def _doi_pmid_from_manifest(doi: str) -> str | None:
    """Recover a DOI->PMID resolution from the manifest + esearch snapshots."""
    manifest = REPO_ROOT / "data" / "raw" / "MANIFEST.jsonl"
    if not manifest.exists():
        return None
    for line in manifest.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("registry") != "pubmed_esearch":
            continue
        if (entry.get("query") or {}).get("term", "").lower() != f"{doi}[doi]".lower():
            continue
        payload = _read_json(REPO_ROOT / entry["path"])
        ids = payload.get("esearchresult", {}).get("idlist", [])
        if ids:
            return str(ids[0])
    return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


# ------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="verify every agent's sources")
    group.add_argument("--agent", help="verify one agent's sources (file stem in evidence/sources/)")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="rebuild the verification index from existing snapshots without network access",
    )
    args = parser.parse_args(argv)

    files = load_source_files(None if args.all else args.agent)
    if not files:
        print("no source files found in evidence/sources/ — nothing to verify")
        return 0

    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[dict[str, Any]] = []
    total = 0
    for agent, records in files.items():
        rows = verify_agent_sources(agent, records, offline=args.offline)
        write_jsonl(VERIFICATION_DIR / f"{agent}.jsonl", rows)
        total += len(rows)
        bad = [r for r in rows if r.get("status") != "verified"]
        failures.extend(bad)
        verified = len(rows) - len(bad)
        print(f"{agent}: {verified}/{len(rows)} verified -> {VERIFICATION_DIR / f'{agent}.jsonl'}")
        for row in bad:
            print(f"  ! {row.get('source_id')}: {row.get('status')} {row.get('detail', '')}".rstrip())
            if row.get("status") == "title_mismatch":
                print(f"      claimed : {row.get('claimed_title')}")
                print(f"      registry: {row.get('registry_title')}  (similarity {row.get('title_similarity')})")

    print(f"\n{total - len(failures)}/{total} sources verified")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
