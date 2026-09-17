"""Shared helpers for the AlphaCognition ingestion pipelines.

Everything here is deterministic and offline-capable. The only network access lives
in the two fetch scripts, and every response they receive is written immutably under
``data/raw/`` by ``scripts/_provenance.write_snapshot`` before it is interpreted.

Design notes
------------
* ``scripts/`` is not a package, so the provenance helpers are imported by putting
  ``scripts/`` on ``sys.path``. This is the same trick the orchestrator's own scripts
  use when they run each other.
* Snapshots are classified on rebuild by *payload shape*, not by filename. GWAS
  Catalog responses carry ``_links.self.href`` (which contains the exact query) and
  study records carry ``accession_id``, so a snapshot directory is self-describing
  and ``--offline`` never needs a side index that could drift.
* No value produced here is a probability, a score, or a number this project
  computed. Effect sizes are copied verbatim into ``as_reported`` strings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _provenance import (  # type: ignore[import-not-found]  # noqa: E402
    RAW_DIR,
    http_get_json,
    iter_snapshots,
    ncbi_params,
    ncbi_sleep,
    scrub_query,
    write_snapshot,
)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

PANEL_PATH = REPO_ROOT / "atlases" / "alphacognition" / "cognitive_trait_panel.yaml"
SEED_REGISTRY = REPO_ROOT / "targets" / "seed_registry.yaml"
GENE_IDENTIFIERS = REPO_ROOT / "data" / "interim" / "gene_identifiers.jsonl"
GENERATED_DIR = Path(__file__).resolve().parent / "generated"
CLAIMS_DIR = REPO_ROOT / "evidence" / "claims" / "alphacognition"

AGENT = "agent:alphacognition"
SCHEMA_VERSION = "0.1.0"

# Seed entries that are complexes rather than single genes (see fetch_gene_identifiers).
NON_GENE_SYMBOLS = {"EIF2B_COMPLEX"}


# --------------------------------------------------------------------- inputs --
def load_panel() -> list[dict[str, Any]]:
    """Every trait in the curated panel, in file order."""
    data = yaml.safe_load(PANEL_PATH.read_text(encoding="utf-8"))
    return list(data.get("traits") or [])


def queried_traits() -> list[dict[str, Any]]:
    """Panel traits the pipelines actually iterate, sorted by EFO id for determinism."""
    return sorted((t for t in load_panel() if t.get("queried")), key=lambda t: t["efo_id"])


def load_seed_targets() -> list[dict[str, Any]]:
    """The seed registry's target list."""
    data = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8"))
    return list(data.get("targets") or [])


def seed_gene_symbols() -> list[str]:
    """Every gene symbol implied by the seed registry, complex members included."""
    symbols: set[str] = set()
    for target in load_seed_targets():
        symbol = str(target.get("symbol", "")).strip()
        if symbol and symbol not in NON_GENE_SYMBOLS:
            symbols.add(symbol)
        for member in target.get("member_genes") or []:
            symbols.add(str(member).strip())
    return sorted(symbols)


def gene_to_target() -> dict[str, str]:
    """Map each gene symbol to the ``TGT:`` id that represents it.

    A complex member maps to the complex's target id; that is the unit the seed
    registry assigns, and it keeps claims attached to something a dossier exists for.
    """
    mapping: dict[str, str] = {}
    for target in load_seed_targets():
        target_id = str(target["target_id"])
        symbol = str(target.get("symbol", "")).strip()
        if symbol and symbol not in NON_GENE_SYMBOLS:
            mapping[symbol] = target_id
        for member in target.get("member_genes") or []:
            mapping[str(member).strip()] = target_id
    return mapping


def ensembl_index() -> dict[str, str]:
    """Symbol -> Ensembl gene id, from the HGNC-resolved index (never hand-written)."""
    index: dict[str, str] = {}
    if not GENE_IDENTIFIERS.exists():
        return index
    for line in GENE_IDENTIFIERS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == "approved_symbol" and row.get("ensembl_gene_id"):
            index[str(row["symbol"])] = str(row["ensembl_gene_id"])
    return index


# ------------------------------------------------------------------ snapshots --
def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def self_href_params(payload: dict[str, Any]) -> dict[str, str]:
    """Query parameters embedded in a HAL response's ``_links.self.href``."""
    href = (((payload.get("_links") or {}).get("self") or {}).get("href")) or ""
    if not href:
        return {}
    return {k: v[0] for k, v in parse_qs(urlparse(href).query).items()}


def snapshots(registry: str) -> list[Path]:
    """All snapshot paths for a raw registry directory, oldest date first."""
    return iter_snapshots(registry)


def raw_dir(registry: str) -> Path:
    return RAW_DIR / registry


# ------------------------------------------------------------------- outputs ---
def write_yaml_doc(path: Path, header: str, payload: Any) -> None:
    """Write a YAML document with a comment header, deterministically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False)
    path.write_text(header.rstrip() + "\n" + body, encoding="utf-8")


def claim_number(index: int) -> str:
    """Three-digit claim ordinal required by the Claim id pattern."""
    return f"{index:03d}"


# ------------------------------------------------------------------ taxonomy ---
# Contract §1.1: "taxid resolved via NCBI, never from memory". The species id is
# therefore resolved at runtime and the response is snapshotted. The snapshot lands in
# the shared, append-only `pubmed_esearch` registry because that directory *is* the
# E-utilities esearch snapshot store; the manifest line records `db=taxonomy` and the
# exact term, so the file is self-describing. (data/raw/ncbi_taxonomy/ belongs to
# agent:comparative under docs/OWNERSHIP.yaml, so this agent must not write there;
# if that agent publishes data/interim/species_taxonomy.jsonl it is preferred.)
HUMAN_SCIENTIFIC_NAME = "Homo sapiens"
SPECIES_INDEX = REPO_ROOT / "data" / "interim" / "species_taxonomy.jsonl"


def _taxid_from_species_index(name: str) -> str | None:
    if not SPECIES_INDEX.exists():
        return None
    for line in SPECIES_INDEX.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        label = str(row.get("queried_name") or row.get("scientific_name") or "").lower()
        taxid = row.get("taxid") or row.get("tax_id")
        if taxid and name.lower() in label:
            return str(taxid)
    return None


def _taxid_from_snapshots(name: str) -> str | None:
    for path in reversed(iter_snapshots("pubmed_esearch")):
        payload = read_json(path)
        translation = json.dumps(payload.get("esearchresult", {}).get("translationstack", []))
        ids = payload.get("esearchresult", {}).get("idlist") or []
        if ids and name.lower() in translation.lower():
            return str(ids[0])
    return None


def resolve_species_id(name: str = HUMAN_SCIENTIFIC_NAME, *, offline: bool = False) -> str | None:
    """``SPECIES:NCBITaxon:{taxid}`` for ``name``, or ``None`` if unresolvable."""
    taxid = _taxid_from_species_index(name) or _taxid_from_snapshots(name)
    if taxid:
        return f"SPECIES:NCBITaxon:{taxid}"
    if offline:
        return None
    query = ncbi_params({"db": "taxonomy", "retmode": "json", "term": name})
    try:
        payload = http_get_json(f"{EUTILS}/esearch.fcgi", params=query)
    except Exception:
        return None
    ncbi_sleep()
    write_snapshot(
        "pubmed_esearch",
        payload,
        url=f"{EUTILS}/esearch.fcgi",
        query=scrub_query(query),
        name_hint=f"taxonomy_{name.replace(' ', '_').lower()}",
    )
    ids = payload.get("esearchresult", {}).get("idlist") or []
    return f"SPECIES:NCBITaxon:{ids[0]}" if ids else None
