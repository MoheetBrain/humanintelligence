#!/usr/bin/env python3
"""Orthology AVAILABILITY audit across the Comparative Intelligence 2.0 species panel.

What this is
------------
For every seed and discovered gene, ask Ensembl Compara which panel species have an
orthologue call, and of what type (one-to-one, one-to-many, many-to-many). The output
answers one question and only one:

    In which species is a cross-species comparison of this gene even POSSIBLE?

What this is NOT
----------------
This is not evidence about cognition, not a selection scan, and not a convergence
result. An orthologue is a statement about shared ancestry, not about function, and
certainly not about whether a gene does the same job in two brains built on different
plans.

The three interpretation traps this script is written to avoid
--------------------------------------------------------------
1. **Absence of an orthologue call is not absence of a gene.** It can mean the species
   is missing from Compara, the assembly is fragmentary at that locus, or the gene tree
   could not be resolved. The panel spans GRCh38.p14 to turTru1, a low-coverage draft,
   and assembly quality predicts gene absence far better than biology does. Every
   absence is therefore emitted as ``not_assessable``, never as a negative result.

2. **Species absent from Compara are not species absent from the analysis by accident.**
   Both avian convergence candidates (New Caledonian crow, budgerigar) are absent from
   Compara while both avian *controls* (chicken, zebra finch) are present. A run over
   "the birds available" would return a null for birds that is pure absence of
   measurement. This script refuses to emit any avian aggregate for that reason; see
   ``species_registry.yaml`` -> ``avian_arm_is_unavailable``.

3. **A one-to-one orthologue is not a functional equivalent.** It licenses the
   comparison; it does not license the conclusion.

Usage
-----
    python pipelines/comparative/orthology_audit.py
    python pipelines/comparative/orthology_audit.py --offline
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
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

ENSEMBL = "https://rest.ensembl.org/homology/symbol/human"
REGISTRY = REPO_ROOT / "atlases" / "comparative_v2" / "species_registry.yaml"
SEED_REGISTRY = REPO_ROOT / "targets" / "seed_registry.yaml"
DISCOVERED = REPO_ROOT / "targets" / "discovered" / "discovered_registry.yaml"
OUT = REPO_ROOT / "data" / "interim" / "comparative_v2_orthology.jsonl"

# Not a gene. It is a five-subunit complex used as a target abstraction elsewhere in the
# repository, and asking Ensembl for it would produce a spurious "absent everywhere" row.
NOT_A_GENE = {"EIF2B_COMPLEX"}


def panel_species() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(species with orthology available, species in the panel but NOT in Compara)."""
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    rows = registry["species"]
    available = [s for s in rows if s.get("orthology_available") and s["ensembl_species"] != "homo_sapiens"]
    unavailable = [s for s in rows if not s.get("orthology_available")]
    return available, unavailable


def gene_list() -> list[dict[str, str]]:
    """Seed and discovered symbols, each tagged with where it came from."""
    genes: dict[str, str] = {}
    seed = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8"))
    for target in seed["targets"]:
        genes.setdefault(str(target["symbol"]), "seed")
        for member in target.get("member_genes") or []:
            genes.setdefault(str(member), "seed_member")
    discovered = yaml.safe_load(DISCOVERED.read_text(encoding="utf-8"))
    for target in discovered["targets"]:
        genes.setdefault(str(target["symbol"]), f"discovered:{target.get('seed_origin')}")
    return [
        {"symbol": s, "origin": o}
        for s, o in sorted(genes.items())
        if s not in NOT_A_GENE
    ]


def fetch(symbol: str, species: list[str]) -> dict[str, Any] | None:
    params = {
        "content-type": "application/json",
        "type": "orthologues",
        "format": "condensed",
        "target_species": species,
    }
    try:
        payload = http_get_json(f"{ENSEMBL}/{symbol}", params=params, timeout=90, retries=2)
    except urllib.error.HTTPError as error:
        # The body names the cause (an unknown gene symbol, or a species missing from
        # Compara). Recording it verbatim is the difference between a real absence and
        # a silent one.
        detail = error.read().decode("utf-8", "replace")[:200]
        print(f"  {symbol:12s} HTTP {error.code}: {detail}")
        return {"_error": f"HTTP {error.code}", "_detail": detail}
    except Exception as error:  # noqa: BLE001
        print(f"  {symbol:12s} {type(error).__name__}")
        return {"_error": type(error).__name__}
    write_snapshot(
        "ensembl_compara", payload, url=f"{ENSEMBL}/{symbol}",
        query={"symbol": symbol, "type": "orthologues", "species": species},
        name_hint=f"orth_{symbol}", compress=True,
    )
    return payload


def summarise(payload: dict[str, Any], species: list[str]) -> dict[str, Any]:
    if payload.get("_error"):
        return {
            "query_status": "failed",
            "error": payload["_error"],
            "detail": payload.get("_detail"),
            "one2one": [],
            "other_orthology": [],
            "no_call": species,
        }
    homologies = (payload.get("data") or [{}])[0].get("homologies") or []
    by_species: dict[str, set[str]] = {}
    for hom in homologies:
        name = hom.get("species")
        if name in species:
            by_species.setdefault(name, set()).add(str(hom.get("type", "")))
    one2one = sorted(s for s, kinds in by_species.items() if any("one2one" in k for k in kinds))
    other = sorted(set(by_species) - set(one2one))
    return {
        "query_status": "ok",
        "one2one": one2one,
        "other_orthology": other,
        "no_call": sorted(set(species) - set(by_species)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--offline", action="store_true", help="rebuild from snapshots")
    args = parser.parse_args(argv)

    available, unavailable = panel_species()
    species = [s["ensembl_species"] for s in available]
    genes = gene_list()

    print(f"panel species with orthology available: {len(species)}")
    print(f"panel species absent from Compara:      {len(unavailable)} "
          f"({', '.join(s['ensembl_species'] for s in unavailable)})")
    print(f"genes to audit:                         {len(genes)}\n")

    offline = {}
    if args.offline:
        for path in iter_snapshots("ensembl_compara"):
            payload = read_snapshot(path)
            data = (payload.get("data") or [{}])[0]
            if data.get("id"):
                offline[path.stem.split("_")[1]] = payload

    rows: list[dict[str, Any]] = []
    for gene in genes:
        symbol = gene["symbol"]
        payload = offline.get(symbol) if args.offline else fetch(symbol, species)
        if payload is None:
            payload = {"_error": "no_snapshot"}
        summary = summarise(payload, species)
        rows.append(
            {
                "symbol": symbol,
                "origin": gene["origin"],
                **summary,
                "n_one2one": len(summary["one2one"]),
                "species_queried": species,
                "species_not_in_compara": [s["ensembl_species"] for s in unavailable],
                "audited_on": utc_now(),
                "interpretation": (
                    "ORTHOLOGY AVAILABILITY ONLY. Presence of a one-to-one orthologue means a "
                    "cross-species comparison is possible, NOT that the gene has the same "
                    "function. Species listed in no_call are NOT_ASSESSABLE: assembly quality "
                    "and gene-tree resolution explain absence better than biology does."
                ),
                "avian_arm_status": (
                    "INOPERABLE. Both avian convergence candidates (corvus_moneduloides, "
                    "melopsittacus_undulatus) are absent from Ensembl Compara while both avian "
                    "controls (gallus_gallus, taeniopygia_guttata) are present. No avian "
                    "convergence claim may be drawn from these rows in either direction."
                ),
            }
        )
        if not args.offline:
            flags = "".join(
                "1" if s in summary["one2one"] else ("x" if s in summary["other_orthology"] else ".")
                for s in species
            )
            print(f"  {symbol:12s} 1:1={len(summary['one2one']):2d}/{len(species)}  {flags}")
            time.sleep(0.25)

    write_jsonl(OUT, rows)
    ok = [r for r in rows if r["query_status"] == "ok"]
    full = [r for r in ok if r["n_one2one"] == len(species)]
    print(f"\ngenes queried successfully: {len(ok)}/{len(rows)}")
    print(f"1:1 orthologue in ALL {len(species)} available species: {len(full)}")
    print(f"written to {OUT.relative_to(REPO_ROOT)}")
    print("\nREMINDER: this is a data-availability audit. It contains no evidence about "
          "cognition and supports no claim about any target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
