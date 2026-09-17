#!/usr/bin/env python3
"""Ingest Open Targets Platform target annotations (network) — ``make fetch-tractability``.

What this pipeline does
-----------------------
For every seed target with a resolved Ensembl gene id, it runs the verified Open
Targets GraphQL query from ``docs/API_RECIPES.md`` §5.1 and writes the response
verbatim to an immutable snapshot under ``data/raw/opentargets/{UTC date}/``, with a
line in ``data/raw/MANIFEST.jsonl``. It then derives, **offline from those
snapshots**, a tractability index at
``data/interim/opentargets_tractability.jsonl``.

What it deliberately does not do
--------------------------------
* It does not grade anything. Level assignment for the ``tractability`` facet is a
  separate, reviewable step (``derive_tractability_facets``), and it reads only the
  snapshot, never the network.
* It does not treat Open Targets prose as evidence. ``safetyLiabilities`` arrive with
  PMIDs; those PMIDs are emitted as *candidate source registrations* for the red team
  to verify and cite, because "Open Targets says so" is not provenance
  (``docs/API_RECIPES.md`` §5.1).
* It writes no claim and no assessment. Those are curated records, authored
  deliberately, not generated.

Data version pinning
--------------------
Every snapshot carries ``meta.dataVersion``. The pinned release is registered as
``SRC:DB:opentargets:{year}.{month:02d}`` in ``evidence/sources/integration.yaml``,
and a tractability grade derived from an unrecorded data version is not admissible
(rubric ``tractability.provenance_rule``).

Usage::

    .venv/bin/python pipelines/integration/fetch_target_annotations.py            # fetch + derive
    .venv/bin/python pipelines/integration/fetch_target_annotations.py --offline  # derive only
    .venv/bin/python pipelines/integration/fetch_target_annotations.py --symbols GABRA5 HCN1
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _provenance import (  # noqa: E402  (path set above so the shared helpers import)
    INTERIM_DIR,
    USER_AGENT,
    iter_snapshots,
    utc_now,
    write_jsonl,
    write_snapshot,
)

REGISTRY = "opentargets"
ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
IDENTIFIER_INDEX = INTERIM_DIR / "gene_identifiers.jsonl"
TRACTABILITY_INDEX = INTERIM_DIR / "opentargets_tractability.jsonl"
SAFETY_CANDIDATES = INTERIM_DIR / "opentargets_safety_pmid_candidates.jsonl"

#: Verified against the live endpoint on 2026-09-17 (docs/API_RECIPES.md §5.1).
QUERY = """
query TargetAnnotations($id: String!) {
  meta { apiVersion { x y z } dataVersion { year month iteration } }
  target(ensemblId: $id) {
    id
    approvedSymbol
    biotype
    tractability { modality label value }
    safetyLiabilities { event eventId datasource literature }
    chemicalProbes { id drugId isHighQuality probeMinerScore }
  }
}
"""

# Open Targets tractability buckets, grouped by what they actually license.
#
# The groups below are the rubric's ``tractability`` level criteria expressed as data.
# They are a judgement about MODALITY MATURITY and nothing else: no group says
# anything about a target's biology, its safety, or whether it should be modulated.
#
# Buckets are matched on the ``(modality, label)`` PAIR, because the same label means
# different things in different modalities: ``SM/Approved Drug`` is a small-molecule
# precedent, while ``AB/GO CC high conf`` is a confident prediction that the protein
# is extracellular — an antibody-tractability prior, not a tool.
#
# The vocabulary below is the set actually returned for this cohort in data version
# 26.06 (28 buckets per target), plus the clinical labels the API documents. An
# unrecognised pair falls through to ``unclassified`` and is reported rather than
# silently counted, so a vocabulary change in a later release is visible.

#: Clinical or approved precedent for the target or a close family member -> level 3.
CLINICAL_PAIRS = frozenset(
    {
        ("SM", "Approved Drug"),
        ("SM", "Advanced Clinical"),
        ("SM", "Phase 1 Clinical"),
        ("SM", "Clinical Precedence"),
        ("OC", "Approved Drug"),
        ("OC", "Advanced Clinical"),
        ("OC", "Phase 1 Clinical"),
        ("OC", "Clinical Precedence"),
        ("AB", "Approved Drug"),
        ("AB", "Advanced Clinical"),
        ("AB", "Phase 1 Clinical"),
        ("AB", "Clinical Precedence"),
        ("PR", "Literature"),
    }
)

#: A characterised chemical or structural tool actually exists -> level 2.
TOOL_PAIRS = frozenset(
    {
        ("SM", "High-Quality Ligand"),
        ("SM", "Structure with Ligand"),
        ("SM", "High-Quality Pocket"),
    }
)

#: Prediction, family membership or localisation prior only -> level 1.
#:
#: ``SM/Druggable Family`` is here because family membership is a PRIOR, not a tool
#: (rubric level 1: "being a member of a druggable family is a PRIOR, not a tool").
#: ``SM/Med-Quality Pocket`` is here because a medium-confidence pocket does not give
#: anyone a tool. All ``AB/*`` localisation buckets are predictions of accessibility.
#: ``PR/Small Molecule Binder`` is a PROTAC-bucket flag that a binder exists
#: somewhere; when a real ligand exists it also shows as ``SM/High-Quality Ligand``,
#: so treating the flag alone as prediction-grade is the conservative reading.
PREDICTED_PAIRS = frozenset(
    {
        ("SM", "Druggable Family"),
        ("SM", "Med-Quality Pocket"),
        ("AB", "GO CC high conf"),
        ("AB", "GO CC med conf"),
        ("AB", "UniProt loc high conf"),
        ("AB", "UniProt loc med conf"),
        ("AB", "UniProt SigP or TMHMM"),
        ("AB", "Human Protein Atlas loc"),
        ("PR", "Database Ubiquitination"),
        ("PR", "UniProt Ubiquitination"),
        ("PR", "Half-life Data"),
        ("PR", "Small Molecule Binder"),
    }
)


def load_ensembl_ids(symbols: list[str] | None) -> list[tuple[str, str]]:
    """``[(symbol, ensembl_gene_id)]`` from the HGNC-resolved identifier index.

    Identifiers are never hand-written (contract §7): a symbol missing from the index
    is skipped and reported, not guessed.
    """
    if not IDENTIFIER_INDEX.is_file():
        raise SystemExit(
            f"{IDENTIFIER_INDEX} does not exist.\n"
            "Run `make fetch-identifiers` first: Open Targets is queried by Ensembl gene id, "
            "and this project never hand-writes an accession (contract §7)."
        )
    wanted = set(symbols) if symbols else None
    pairs: list[tuple[str, str]] = []
    for line in IDENTIFIER_INDEX.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        symbol = row.get("symbol") or row.get("queried_symbol")
        ensembl = row.get("ensembl_gene_id")
        if not symbol or not ensembl:
            continue
        if wanted is not None and symbol not in wanted:
            continue
        pairs.append((str(symbol), str(ensembl)))
    return sorted(set(pairs))


def post_graphql(query: str, variables: dict[str, Any], *, timeout: int = 60) -> Any:
    """POST a GraphQL query and parse the JSON response.

    ``scripts/_provenance`` only wraps GET, so this is the one POST helper the
    project needs; it follows the same rules (declared user agent, no credentials).
    """
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch(symbols: list[str] | None) -> list[Path]:
    """Fetch annotations for each seed target and snapshot every response."""
    written: list[Path] = []
    for symbol, ensembl_id in load_ensembl_ids(symbols):
        try:
            payload = post_graphql(QUERY, {"id": ensembl_id})
        except Exception as error:  # noqa: BLE001 - record the failure, never a guess
            print(f"  {symbol:16s} FETCH FAILED: {error}", file=sys.stderr)
            continue
        if payload.get("errors"):
            print(f"  {symbol:16s} GRAPHQL ERRORS: {payload['errors']}", file=sys.stderr)
            continue
        if not (payload.get("data") or {}).get("target"):
            print(f"  {symbol:16s} no target record for {ensembl_id}", file=sys.stderr)
            continue
        snapshot = write_snapshot(
            REGISTRY,
            payload,
            url=ENDPOINT,
            query={"operation": "TargetAnnotations", "ensemblId": ensembl_id, "symbol": symbol},
            name_hint=symbol,
        )
        written.append(snapshot)
        data_version = _data_version(payload)
        buckets = len((payload["data"]["target"].get("tractability") or []))
        print(f"  {symbol:16s} -> {snapshot.relative_to(REPO_ROOT)}  ({buckets} buckets, {data_version})")
    return written


def _data_version(payload: dict[str, Any]) -> str:
    """``{year}.{month:02d}`` from ``meta.dataVersion``, or ``unknown``."""
    version = ((payload.get("data") or {}).get("meta") or {}).get("dataVersion") or {}
    year, month = version.get("year"), version.get("month")
    if year is None or month is None:
        return "unknown"
    return f"{int(year)}.{int(month):02d}"


def _api_version(payload: dict[str, Any]) -> str:
    version = ((payload.get("data") or {}).get("meta") or {}).get("apiVersion") or {}
    parts = [version.get("x"), version.get("y"), version.get("z")]
    return ".".join(str(p) for p in parts if p is not None) or "unknown"


def classify_tractability(buckets: list[dict[str, Any]], probes: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise the tractability evidence available for one target.

    Returns the *inputs* a rubric grade needs — which bucket classes are present,
    how many high-quality probes exist — plus a ``suggested_level`` that is an
    explicit reading of ``facet_rubric_v0_1.yaml``'s ``tractability`` criteria. The
    suggestion is a starting point for a curated assessment, not an assessment: a
    level only becomes real when an agent writes it into an assessment record with a
    rationale and claim references.
    """
    positive = {
        (str(b.get("modality", "")), str(b.get("label", ""))) for b in buckets if b.get("value")
    }
    modalities = sorted({modality for modality, _ in positive if modality})
    high_quality_probes = [p for p in probes if p.get("isHighQuality")]

    clinical = sorted(positive & CLINICAL_PAIRS)
    tools = sorted(positive & TOOL_PAIRS)
    predicted = sorted(positive & PREDICTED_PAIRS)
    unclassified = sorted(positive - CLINICAL_PAIRS - TOOL_PAIRS - PREDICTED_PAIRS)

    has_clinical = bool(clinical)
    has_tool = bool(tools) or bool(high_quality_probes)
    has_predicted = bool(predicted)

    if has_clinical:
        # Level 4 additionally requires a published family selectivity profile AND
        # documented human CNS exposure, neither of which Open Targets reports. The
        # database alone therefore can never justify more than 3 — stated here so
        # that nobody later reads a bucket as a level-4 grade.
        suggested = 3
        basis = (
            "clinical or approved precedent in this release "
            f"({', '.join(f'{m}/{l}' for m, l in clinical)}); level 4 additionally needs a "
            "published family selectivity profile and documented human CNS exposure, which "
            "this source does not report"
        )
    elif has_tool:
        detail = ", ".join(f"{m}/{l}" for m, l in tools) or "high-quality chemical probe"
        suggested = 2
        basis = f"characterised chemical or structural tool ({detail}), no clinical precedent in this release"
    elif has_predicted:
        suggested = 1
        basis = (
            "prediction, family membership or localisation prior only "
            f"({', '.join(f'{m}/{l}' for m, l in predicted)}); a druggable family is a prior, not a tool"
        )
    else:
        suggested = 0
        basis = (
            "no positive tractability bucket in this release"
            if buckets
            else "no tractability buckets returned for this target"
        )

    return {
        "positive_buckets": [f"{modality}/{label}" for modality, label in sorted(positive)],
        "modalities": modalities,
        "clinical_buckets": [f"{m}/{l}" for m, l in clinical],
        "tool_buckets": [f"{m}/{l}" for m, l in tools],
        "predicted_buckets": [f"{m}/{l}" for m, l in predicted],
        "unclassified_buckets": [f"{m}/{l}" for m, l in unclassified],
        "n_high_quality_probes": len(high_quality_probes),
        "high_quality_probe_ids": sorted(str(p.get("id")) for p in high_quality_probes if p.get("id")),
        "has_clinical_precedence": has_clinical,
        "has_characterised_tool": has_tool,
        "has_prediction_only": has_predicted and not (has_tool or has_clinical),
        "suggested_level": suggested,
        "suggested_level_basis": basis,
        "suggested_level_is_not_an_assessment": (
            "A curated facet assessment is the only place a level becomes real; it needs a "
            "rationale and claim references (contract §5.2). See "
            "docs/blackboard/schema_change_requests/integration-001.yaml for the open question "
            "about where agent:integration may write the tractability assessment."
        ),
    }


def derive() -> dict[str, Any]:
    """Rebuild the tractability index from snapshots, with no network access."""
    rows: list[dict[str, Any]] = []
    safety_rows: list[dict[str, Any]] = []
    versions: Counter[str] = Counter()

    for path in iter_snapshots(REGISTRY):
        payload = json.loads(path.read_text(encoding="utf-8"))
        target = (payload.get("data") or {}).get("target")
        if not target:
            continue
        data_version = _data_version(payload)
        versions[data_version] += 1
        symbol = str(target.get("approvedSymbol") or "")
        buckets = list(target.get("tractability") or [])
        probes = list(target.get("chemicalProbes") or [])
        liabilities = list(target.get("safetyLiabilities") or [])

        summary = classify_tractability(buckets, probes)
        rows.append(
            {
                "symbol": symbol,
                "target_id": f"TGT:{symbol}",
                "ensembl_gene_id": str(target.get("id") or ""),
                "biotype": target.get("biotype"),
                "registry": REGISTRY,
                "data_version": data_version,
                "api_version": _api_version(payload),
                "source_id": f"SRC:DB:{REGISTRY}:{data_version}",
                "snapshot": str(path.relative_to(REPO_ROOT)),
                "derived_at": utc_now(),
                "derived_by": "pipelines/integration/fetch_target_annotations.py",
                "n_safety_liabilities": len(liabilities),
                **summary,
            }
        )

        for liability in liabilities:
            literature = liability.get("literature")
            pmids = (
                [str(p) for p in literature]
                if isinstance(literature, list)
                else ([str(literature)] if literature else [])
            )
            safety_rows.append(
                {
                    "symbol": symbol,
                    "target_id": f"TGT:{symbol}",
                    "event": liability.get("event"),
                    "event_id": liability.get("eventId"),
                    "datasource": liability.get("datasource"),
                    "candidate_pmids": pmids,
                    "candidate_source_ids": [f"SRC:PMID:{pmid}" for pmid in pmids],
                    "snapshot": str(path.relative_to(REPO_ROOT)),
                    "data_version": data_version,
                    "note": (
                        "CANDIDATE ONLY. agent:red_team owns safety_liability_burden. These PMIDs "
                        "must be registered and machine-verified via scripts/fetch_source_metadata.py "
                        "before any claim cites them; 'Open Targets says so' is not provenance."
                    ),
                }
            )

    rows.sort(key=lambda r: r["symbol"])
    safety_rows.sort(key=lambda r: (r["symbol"], str(r["event"])))
    write_jsonl(TRACTABILITY_INDEX, rows)
    write_jsonl(SAFETY_CANDIDATES, safety_rows)
    return {"rows": rows, "safety_rows": safety_rows, "data_versions": dict(versions)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbols", nargs="*", default=None, help="Limit to these gene symbols.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip the network step and rebuild the derived index from existing snapshots.",
    )
    args = parser.parse_args(argv)

    if not args.offline:
        print(f"fetching Open Targets annotations from {ENDPOINT}")
        fetch(args.symbols)

    outcome = derive()
    print(f"\nderived {len(outcome['rows'])} tractability rows -> {TRACTABILITY_INDEX.relative_to(REPO_ROOT)}")
    print(
        f"derived {len(outcome['safety_rows'])} candidate safety-liability rows -> "
        f"{SAFETY_CANDIDATES.relative_to(REPO_ROOT)}"
    )
    if outcome["data_versions"]:
        print("data versions in snapshots:", outcome["data_versions"])
        print(
            "register each as SRC:DB:opentargets:<version> in evidence/sources/integration.yaml "
            "before grading the tractability facet from it."
        )
    distribution = Counter(row["suggested_level"] for row in outcome["rows"])
    if distribution:
        print("suggested tractability levels (NOT assessments):", dict(sorted(distribution.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
