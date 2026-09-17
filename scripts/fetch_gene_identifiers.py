#!/usr/bin/env python3
"""Resolve seed-target gene identifiers from HGNC (the naming authority of record).

No agent hand-writes an HGNC id, Ensembl gene id, UniProt accession or Entrez id in
this repository. They are fetched here, snapshotted immutably, and merged into the
graph by the builder with provenance attached.

A symbol that HGNC does not recognise as approved is reported, not guessed: the
result is ``status: not_found`` or ``status: alias_or_previous_symbol`` with the
approved symbol HGNC suggests, and the seed registry must then be corrected.

Usage
-----
    python scripts/fetch_gene_identifiers.py            # resolve every seed symbol
    python scripts/fetch_gene_identifiers.py --offline  # rebuild index from snapshots
    python scripts/fetch_gene_identifiers.py --symbols GABRA5 HCN1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from _provenance import (  # type: ignore[import-not-found]
    INTERIM_DIR,
    REPO_ROOT,
    http_get_json,
    iter_snapshots,
    utc_now,
    write_jsonl,
    write_snapshot,
)

HGNC_FETCH = "https://rest.genenames.org/fetch"
HGNC_SEARCH = "https://rest.genenames.org/search"
SEED_REGISTRY = REPO_ROOT / "targets" / "seed_registry.yaml"
OUT_PATH = INTERIM_DIR / "gene_identifiers.jsonl"

# Seed entries that are complexes / non-gene units: resolved via member_genes only.
NON_GENE_SYMBOLS = {"EIF2B_COMPLEX"}


def seed_symbols() -> list[str]:
    """Every gene symbol implied by the seed registry (targets + complex members)."""
    registry = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for target in registry.get("targets", []):
        symbol = str(target.get("symbol", "")).strip()
        if symbol and symbol not in NON_GENE_SYMBOLS:
            symbols.add(symbol)
        for member in target.get("member_genes", []) or []:
            symbols.add(str(member).strip())
    return sorted(symbols)


def fetch_symbol(symbol: str) -> tuple[dict[str, Any], str]:
    """Fetch one symbol from HGNC, returning (payload, snapshot_relpath)."""
    url = f"{HGNC_FETCH}/symbol/{symbol}"
    payload = http_get_json(url, headers={"Accept": "application/json"})
    snapshot = write_snapshot("hgnc", payload, url=url, query={"symbol": symbol}, name_hint=symbol)
    return payload, str(snapshot.relative_to(REPO_ROOT))


def fetch_alias(symbol: str) -> tuple[dict[str, Any], str]:
    """Ask HGNC whether ``symbol`` is an alias or previous symbol of something."""
    url = f"{HGNC_SEARCH}/alias_symbol/{symbol}+OR+prev_symbol/{symbol}"
    payload = http_get_json(url, headers={"Accept": "application/json"})
    snapshot = write_snapshot(
        "hgnc_search", payload, url=url, query={"alias_or_prev": symbol}, name_hint=symbol
    )
    return payload, str(snapshot.relative_to(REPO_ROOT))


def summarise(doc: dict[str, Any]) -> dict[str, Any]:
    """Project an HGNC document onto the identifier fields the graph needs."""
    return {
        "symbol": doc.get("symbol"),
        "hgnc_id": doc.get("hgnc_id"),
        "gene_name": doc.get("name"),
        "ensembl_gene_id": doc.get("ensembl_gene_id"),
        "uniprot_ids": doc.get("uniprot_ids") or [],
        "entrez_id": doc.get("entrez_id"),
        "locus_type": doc.get("locus_type"),
        "locus_group": doc.get("locus_group"),
        "location": doc.get("location"),
        "hgnc_status": doc.get("status"),
        "alias_symbols": doc.get("alias_symbol") or [],
        "prev_symbols": doc.get("prev_symbol") or [],
        "mane_select": doc.get("mane_select") or [],
    }


def resolve_online(symbols: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        row: dict[str, Any] = {"queried_symbol": symbol, "retrieved_at": utc_now(), "registry": "hgnc"}
        try:
            payload, snapshot = fetch_symbol(symbol)
        except Exception as error:
            row.update({"status": "fetch_failed", "detail": f"{type(error).__name__}: {error}"})
            rows.append(row)
            continue
        docs = (payload.get("response") or {}).get("docs") or []
        if docs:
            row.update({"status": "approved_symbol", "snapshot": snapshot, **summarise(docs[0])})
            rows.append(row)
            continue
        # Not an approved symbol: ask HGNC what it is instead.
        try:
            alias_payload, alias_snapshot = fetch_alias(symbol)
            alias_docs = (alias_payload.get("response") or {}).get("docs") or []
        except Exception as error:
            row.update({"status": "not_found", "detail": f"alias lookup failed: {error}", "snapshot": snapshot})
            rows.append(row)
            continue
        if alias_docs:
            row.update(
                {
                    "status": "alias_or_previous_symbol",
                    "snapshot": alias_snapshot,
                    "approved_symbol_suggestion": alias_docs[0].get("symbol"),
                    "detail": "seed registry should use the HGNC-approved symbol",
                }
            )
        else:
            row.update({"status": "not_found", "snapshot": snapshot, "detail": "HGNC has no such symbol"})
        rows.append(row)
    return rows


def resolve_offline(symbols: list[str]) -> list[dict[str, Any]]:
    """Rebuild the identifier index from committed HGNC snapshots."""
    index: dict[str, tuple[dict[str, Any], str]] = {}
    for path in iter_snapshots("hgnc"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for doc in (payload.get("response") or {}).get("docs") or []:
            symbol = doc.get("symbol")
            if symbol:
                index[symbol] = (summarise(doc), str(path.relative_to(REPO_ROOT)))
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        if symbol in index:
            fields, snapshot = index[symbol]
            rows.append(
                {
                    "queried_symbol": symbol,
                    "status": "approved_symbol",
                    "registry": "hgnc",
                    "snapshot": snapshot,
                    "retrieved_at": "from_snapshot",
                    **fields,
                }
            )
        else:
            rows.append(
                {
                    "queried_symbol": symbol,
                    "status": "not_checked",
                    "registry": "hgnc",
                    "detail": "no snapshot available offline; run without --offline",
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="rebuild from snapshots, no network")
    parser.add_argument("--symbols", nargs="*", help="resolve these symbols instead of the seed registry")
    args = parser.parse_args(argv)

    symbols = sorted(set(args.symbols)) if args.symbols else seed_symbols()
    rows = resolve_offline(symbols) if args.offline else resolve_online(symbols)
    write_jsonl(OUT_PATH, sorted(rows, key=lambda r: str(r.get("queried_symbol"))))

    ok = [r for r in rows if r.get("status") == "approved_symbol"]
    print(f"{len(ok)}/{len(rows)} symbols resolved to HGNC-approved records -> {OUT_PATH}")
    for row in rows:
        if row.get("status") != "approved_symbol":
            print(f"  ! {row.get('queried_symbol')}: {row.get('status')} {row.get('detail', '')}".rstrip())
            if row.get("approved_symbol_suggestion"):
                print(f"      HGNC suggests: {row['approved_symbol_suggestion']}")
    return 0 if len(ok) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
