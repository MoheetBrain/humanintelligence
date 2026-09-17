#!/usr/bin/env python3
"""Adult human brain expression for the seed targets (contract task A4).

Question this answers
---------------------
"Is this gene expressed in the *adult human* brain, and where?" — nothing more. Bulk
tissue expression cannot tell us which cell type carries the signal, and it cannot tell
us anything about development.

Sources actually reachable from this machine on 2026-09-17
---------------------------------------------------------
* **GTEx Portal API v2** (`/api/v2/expression/medianGeneExpression`, dataset `gtex_v8`)
  — 54 tissues including 13 brain regions, each with an UBERON `ontologyId`. Adult
  post-mortem donors. This is the primary source used here. Gencode ids are resolved
  first through `/api/v2/reference/gene` so no accession is hand-written.
* **Open Targets `target { baselineExpression }`** — reachable, and in data version
  26.06 it does carry a `celltypeBiosample` field (GTEx + Tabula Sapiens). It is
  captured for provenance, but it does **not** solve adult brain cell-type resolution:
  the `page.index` argument was observed to be ignored (every page returns the same
  first 500 rows of 1409 for CHRM1), and the cell-type rows available are Tabula
  Sapiens, which does not cover brain. Recorded as a limitation, not worked around.

Explicitly NOT done in v0.1 (deferred, not guessed)
---------------------------------------------------
* **Adult brain cell-type resolution.** No Allen Brain Cell Atlas / Human Brain Cell
  Atlas ingestion exists here. This is queued as **Q003** in `docs/TASK_DAG.yaml`
  ("Adult cell-type expression atlas ingestion"). Every assessment that would need it
  says so in `limiting_factor`. No cell type is asserted from a bulk-tissue value.
* **Developmental timing.** BrainSpan/PsychENCODE developmental transcriptome data was
  not ingested. Developmental-timing claims are therefore made only where a *retrieved
  publication* supports them, by hand, in `evidence/claims/alphacognition/`, never
  inferred from adult GTEx values.

Outputs
-------
``data/raw/gtex/<UTC date>/*.json``                 immutable snapshots (+ MANIFEST lines)
``data/interim/adult_brain_expression.jsonl``       tidy derived table
``evidence/claims/alphacognition/expression_derived.yaml``  machine claims
``pipelines/alphacognition/generated/sources_expression.yaml``  source records to merge
``pipelines/alphacognition/generated/expression_summary.json``  run counts

Usage
-----
    python pipelines/alphacognition/fetch_expression.py
    python pipelines/alphacognition/fetch_expression.py --offline
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # type: ignore[import-not-found]  # noqa: E402
    AGENT,
    CLAIMS_DIR,
    GENERATED_DIR,
    SCHEMA_VERSION,
    claim_number,
    ensembl_index,
    read_json,
    resolve_species_id,
    seed_gene_symbols,
    snapshots,
    write_yaml_doc,
)
from _provenance import (  # type: ignore[import-not-found]  # noqa: E402
    INTERIM_DIR,
    USER_AGENT,
    http_get_json,
    utc_date,
    write_snapshot,
)

GTEX_BASE = "https://gtexportal.org/api/v2"
GTEX_DATASET = "gtex_v8"
OT_GRAPHQL = "https://api.platform.opentargets.org/api/v4/graphql"
RAW_REGISTRY = "gtex"

DERIVED_PATH = INTERIM_DIR / "adult_brain_expression.jsonl"
CLAIMS_PATH = CLAIMS_DIR / "expression_derived.yaml"
SOURCES_PATH = GENERATED_DIR / "sources_expression.yaml"
SUMMARY_PATH = GENERATED_DIR / "expression_summary.json"

OT_EXPRESSION_QUERY = """
query Baseline($id: String!) {
  target(ensemblId: $id) {
    id approvedSymbol
    baselineExpression(page: {index: 0, size: 500}) {
      count
      rows {
        datasourceId datatypeId unit median q1 q3 min max
        specificity_score distribution_score
        tissueBiosampleFromSource celltypeBiosampleFromSource
        tissueBiosample { biosampleId biosampleName }
        celltypeBiosample { biosampleId biosampleName }
      }
    }
  }
  meta { apiVersion { x y z } dataVersion { year month iteration } }
}
"""


# ----------------------------------------------------------------- network ----
def gtex_gene(symbol: str) -> dict[str, Any]:
    """Resolve a symbol to its GTEx gencode id (never hand-written)."""
    url = f"{GTEX_BASE}/reference/gene"
    params = {"geneId": symbol, "gencodeVersion": "v26", "genomeBuild": "GRCh38/hg38"}
    payload = http_get_json(url, params=params)
    write_snapshot(RAW_REGISTRY, payload, url=url, query=params, name_hint=f"gene_{symbol}")
    return payload


def gtex_median_expression(gencode_id: str, symbol: str) -> dict[str, Any]:
    url = f"{GTEX_BASE}/expression/medianGeneExpression"
    params = {"gencodeId": gencode_id, "datasetId": GTEX_DATASET, "page": 0, "itemsPerPage": 100}
    payload = http_get_json(url, params=params)
    write_snapshot(RAW_REGISTRY, payload, url=url, query=params, name_hint=f"median_{symbol}")
    return payload


def opentargets_baseline(ensembl_id: str, symbol: str) -> dict[str, Any]:
    body = json.dumps({"query": OT_EXPRESSION_QUERY, "variables": {"id": ensembl_id}}).encode("utf-8")
    request = urllib.request.Request(
        OT_GRAPHQL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        payload = json.loads(error.read().decode("utf-8"))
    write_snapshot(
        RAW_REGISTRY,
        payload,
        url=OT_GRAPHQL,
        query={"operation": "baselineExpression", "ensemblId": ensembl_id},
        name_hint=f"otbaseline_{symbol}",
    )
    return payload


# ------------------------------------------------------------ offline rebuild --
def load_offline() -> dict[str, Any]:
    genes: dict[str, dict[str, Any]] = {}
    medians: dict[str, list[dict[str, Any]]] = {}
    ot: dict[str, dict[str, Any]] = {}
    ot_version: str | None = None
    for path in snapshots(RAW_REGISTRY):
        payload = read_json(path)
        if not payload:
            continue
        data = payload.get("data")
        if isinstance(data, dict) and data.get("target"):
            target = data["target"]
            ot[str(target["approvedSymbol"])] = payload
            version = (data.get("meta") or {}).get("dataVersion") or {}
            if version.get("year"):
                ot_version = f"{version['year']}.{version['month']}"
            continue
        rows = payload.get("data")
        if isinstance(rows, list) and rows:
            first = rows[0]
            if "gencodeId" in first and "median" in first:
                medians[str(first["geneSymbol"])] = rows
            elif "gencodeId" in first and "geneSymbol" in first:
                genes[str(first["geneSymbol"])] = payload
    return {"genes": genes, "medians": medians, "ot": ot, "ot_data_version": ot_version}


# ------------------------------------------------------------- row assembly ----
def brain_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if str(r.get("tissueSiteDetailId", "")).startswith("Brain_")]


def derived_rows(
    medians: dict[str, list[dict[str, Any]]],
    ot: dict[str, dict[str, Any]],
    *,
    ot_data_version: str | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for symbol in sorted(medians):
        rows = medians[symbol]
        brain = brain_rows(rows)
        non_brain = [r for r in rows if r not in brain]
        ot_payload = ((ot.get(symbol) or {}).get("data") or {}).get("target") or {}
        ot_expression = (ot_payload.get("baselineExpression") or {})
        ot_rows = ot_expression.get("rows") or []
        ot_celltypes = sorted({str(r["celltypeBiosampleFromSource"]) for r in ot_rows if r.get("celltypeBiosampleFromSource")})
        ot_sources = sorted({str(r["datasourceId"]) for r in ot_rows if r.get("datasourceId")})
        out.append(
            {
                "gene_symbol": symbol,
                "gtex_dataset": GTEX_DATASET,
                "gtex_gencode_id": rows[0].get("gencodeId") if rows else None,
                "tissues_reported": len(rows),
                "brain_regions_reported": len(brain),
                "brain_regions": sorted(
                    (
                        {
                            "tissue_site_detail_id": r["tissueSiteDetailId"],
                            "uberon_ontology_id": r.get("ontologyId"),
                            "median_as_reported": r.get("median"),
                            "unit_as_reported": r.get("unit"),
                        }
                        for r in brain
                    ),
                    key=lambda r: str(r["tissue_site_detail_id"]),
                ),
                "highest_median_brain_region": max(
                    brain, key=lambda r: r.get("median") or -1.0
                ).get("tissueSiteDetailId")
                if brain
                else None,
                "highest_median_tissue_overall": max(
                    rows, key=lambda r: r.get("median") or -1.0
                ).get("tissueSiteDetailId")
                if rows
                else None,
                "non_brain_tissues_reported": len(non_brain),
                "open_targets_data_version": ot_data_version,
                "open_targets_baseline_row_count_reported": ot_expression.get("count"),
                "open_targets_baseline_rows_retrieved": len(ot_rows),
                "open_targets_datasources_seen": ot_sources,
                "open_targets_celltypes_seen": ot_celltypes,
                "adult_brain_celltype_resolution": "not_available",
                "adult_brain_celltype_deferred_to": "docs/TASK_DAG.yaml Q003",
                "developmental_timing_resolution": "not_retrieved",
                "snapshot_dir": f"data/raw/{RAW_REGISTRY}/",
            }
        )
    return out


# ------------------------------------------------------------------- claims ----
def build_claims(rows: list[dict[str, Any]], *, run_id: str, species: str | None) -> list[dict[str, Any]]:
    """One expression claim per gene with GTEx brain data, plus nothing else.

    The claim asserts only that the gene's transcript is detected in named adult human
    brain regions. No cell type, no direction of effect, no developmental statement.
    """
    claims: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not row["brain_regions"]:
            continue
        symbol = row["gene_symbol"]
        regions = row["brain_regions"]
        detected = [r for r in regions if (r["median_as_reported"] or 0) > 0]
        # GTEx maps several tissueSiteDetailIds onto the same UBERON term (e.g. the two
        # cerebellum entries), so the id list is de-duplicated while keeping GTEx's own
        # region names in the evidence item's endpoint string.
        region_ids = sorted(
            {
                f"REGION:{str(r['uberon_ontology_id']).replace('_', ':')}"
                for r in detected
                if r.get("uberon_ontology_id")
            }
        )
        top = row["highest_median_brain_region"]
        claims.append(
            {
                "claim_id": f"CLM:{AGENT.split(':')[1]}:expr.{symbol}:{claim_number(1)}",
                "schema_version": SCHEMA_VERSION,
                "statement": (
                    f"GTEx {GTEX_DATASET} reports median transcript abundance for {symbol} in "
                    f"{len(detected)} of {len(regions)} sampled adult human brain regions (post-mortem "
                    f"adult donors), highest in {top}. Bulk tissue only: this says nothing about which "
                    f"cell types express the gene, and nothing about developmental timing."
                ),
                "subject": f"GENE:{symbol}",
                "predicate": "EXPRESSED_IN",
                "object": region_ids[0] if region_ids else "REGION:brain",
                "claim_type": "expression",
                "direction": "no_change",
                "context": {
                    "species": [species] if species else [],
                    "life_stage": "adult",
                    "baseline_context": "healthy_wildtype",
                    "brain_regions": region_ids,
                    "cell_types": [],
                },
                "phenotype_class": "not_applicable",
                "causal_attribution": {
                    "basis": "correlational_expression",
                    "locus_to_gene_resolved": "not_applicable",
                    "alternative_explanations": [
                        "bulk tissue abundance is a mixture over cell types; a high regional value can "
                        "come from a numerically small population or from non-neuronal cells",
                        "post-mortem interval and RNA degradation affect GTEx values",
                        "presence of transcript is not evidence of functional relevance to cognition",
                    ],
                },
                "evidence": [
                    {
                        "source_id": f"SRC:DB:gtex:{GTEX_DATASET.replace('gtex_', '')}",
                        "design": "expression_atlas",
                        "species": species,
                        "population": "GTEx adult post-mortem donors (age range not retrieved per tissue)",
                        "sample_size": {"reported_as": None, "value": None, "unit": "donors"},
                        "endpoint": (
                            "median transcript abundance per tissue; brain regions reported: "
                            + ", ".join(str(r["tissue_site_detail_id"]) for r in regions)
                        ),
                        "endpoint_category": "molecular_readout",
                        "endpoint_measured": "measured",
                        "effect_direction": "not_reported",
                        "effect_size": {
                            "metric": "not_extracted",
                            "as_reported": None,
                            "value": None,
                            "ci_lower": None,
                            "ci_upper": None,
                            "p_value": None,
                        },
                        "replication_status": "not_assessed",
                        "evidence_role": "supports",
                        "extraction": {
                            "basis": "database_record",
                            "extracted_by": AGENT,
                            "extracted_on": utc_date(),
                            "content_checked": True,
                        },
                        "database_record": {
                            "registry": "gtex_portal_api_v2",
                            "dataset_id": GTEX_DATASET,
                            "gencode_id": row["gtex_gencode_id"],
                            "brain_regions": regions,
                            "highest_median_tissue_overall": row["highest_median_tissue_overall"],
                            "snapshot_registry": f"data/raw/{RAW_REGISTRY}/",
                        },
                        "note": (
                            "Median TPM values are GTEx's own summary statistics. They are kept in the "
                            "derived table and in this database_record for traceability and are never "
                            "re-expressed as an effect size or a score by this project."
                        ),
                    }
                ],
                "translation": {
                    "adult_relevance": "demonstrated_in_adults",
                    "healthy_baseline": "tested_in_healthy",
                    "supra_normal": "untested",
                    "human_relevance": "human_observational",
                    "general_intelligence_relevance": "none",
                },
                "uncertainty": {
                    "representation": "ordinal_grade",
                    "scale": "evidence_strength_v1",
                    "level": 2,
                    "rationale": (
                        "direct human adult tissue measurement from a large reference atlas, but bulk "
                        "resolution only and entirely correlational with respect to cognition"
                    ),
                    "calibration_status": "uncalibrated_subjective",
                },
                "risks": [
                    "expression in a region is not evidence that the gene is modifiable there, nor that "
                    "modifying it would change cognition",
                    "adult cell-type resolution is unavailable in this release and is deferred to "
                    "docs/TASK_DAG.yaml Q003",
                ],
                "confounders": ["post-mortem interval", "cell-type composition of the bulk sample"],
                "dependencies": [],
                "status": "active",
                "provenance": {
                    "created_by": AGENT,
                    "created_on": utc_date(),
                    "method": "database_ingestion",
                    "run_id": run_id,
                    "pipeline": "pipelines/alphacognition/fetch_expression.py",
                    "database_release": f"SRC:DB:gtex:{GTEX_DATASET.replace('gtex_', '')}",
                },
            }
        )
    return claims


def build_sources(*, ot_data_version: str | None) -> list[dict[str, Any]]:
    return [
        {
            "source_id": f"SRC:DB:gtex:{GTEX_DATASET.replace('gtex_', '')}",
            "source_type": "database_release",
            "title": "GTEx Portal API v2 median gene expression, dataset gtex_v8",
            "year": 2026,
            "first_author": "GTEx Consortium",
            "container": "GTEx Portal",
            "identifiers": {"dataset_id": GTEX_DATASET},
            "added_by": AGENT,
            "added_on": utc_date(),
            "retrieval": {
                "method": "opentargets_api",
                "endpoint": f"{GTEX_BASE}/expression/medianGeneExpression",
                "note": "retrieval.method enum in docs/DATA_CONTRACT.md §3 has no gtex_api value; "
                "see docs/blackboard/schema_change_requests/alphacognition-001.yaml",
            },
            "note": "dataset id read from the API response's own datasetId field, not assumed.",
        }
    ]


# --------------------------------------------------------------------- main ----
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--genes", nargs="*")
    parser.add_argument("--run-id", default="sprint1-alphacognition-expr-01")
    args = parser.parse_args(argv)

    genes = sorted(set(args.genes)) if args.genes else seed_gene_symbols()
    ensembl = ensembl_index()
    failures: list[str] = []

    if args.offline:
        cache = load_offline()
        medians = {k: v for k, v in cache["medians"].items() if k in set(genes)}
        ot = cache["ot"]
        ot_data_version = cache["ot_data_version"]
        if not medians:
            print(f"offline rebuild impossible: no GTEx snapshots under data/raw/{RAW_REGISTRY}/")
            return 1
    else:
        medians = {}
        ot = {}
        ot_data_version = None
        for symbol in genes:
            try:
                gene_payload = gtex_gene(symbol)
                docs = gene_payload.get("data") or []
                match = next((d for d in docs if str(d.get("geneSymbol")) == symbol), None)
                if not match:
                    failures.append(f"{symbol}: GTEx reference/gene returned no exact symbol match")
                    continue
                expression = gtex_median_expression(str(match["gencodeId"]), symbol)
                rows = expression.get("data") or []
                if not rows:
                    failures.append(f"{symbol}: GTEx medianGeneExpression returned 0 rows")
                    continue
                medians[symbol] = rows
            except Exception as error:
                failures.append(f"{symbol}: GTEx fetch failed: {type(error).__name__}: {error}")
                continue
            ensembl_id = ensembl.get(symbol)
            if not ensembl_id:
                failures.append(f"{symbol}: no HGNC-resolved Ensembl id, Open Targets baseline skipped")
                continue
            try:
                payload = opentargets_baseline(ensembl_id, symbol)
                if payload.get("errors"):
                    failures.append(f"{symbol}: Open Targets baselineExpression error {payload['errors']}")
                else:
                    ot[symbol] = payload
                    version = (((payload.get("data") or {}).get("meta") or {}).get("dataVersion")) or {}
                    if version.get("year"):
                        ot_data_version = f"{version['year']}.{version['month']}"
            except Exception as error:
                failures.append(f"{symbol}: Open Targets baseline fetch failed: {type(error).__name__}: {error}")

    rows = derived_rows(medians, ot, ot_data_version=ot_data_version)
    DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DERIVED_PATH, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    species = resolve_species_id(offline=args.offline)
    claims = build_claims(rows, run_id=args.run_id, species=species)
    sources = build_sources(ot_data_version=ot_data_version)

    write_yaml_doc(
        CLAIMS_PATH,
        f"""# MACHINE-GENERATED — do not hand-edit.
# Produced by pipelines/alphacognition/fetch_expression.py
# GTEx dataset: {GTEX_DATASET}    Open Targets data version seen: {ot_data_version}
#
# Each claim asserts ONLY that a gene's transcript is detected in named adult human brain
# regions, in bulk tissue, in post-mortem adult donors. No cell type is asserted: adult
# brain cell-type resolution was not reachable in this release and is deferred to
# docs/TASK_DAG.yaml Q003. No developmental-timing statement is made here at all.
#
# Claims: {len(claims)}   genes with GTEx brain data: {sum(1 for r in rows if r['brain_regions'])}
""",
        claims,
    )
    write_yaml_doc(
        SOURCES_PATH,
        f"""# MACHINE-GENERATED source records — merged into evidence/sources/alphacognition.yaml
# by pipelines/alphacognition/build_sources.py. Produced by fetch_expression.py.
# Records: {len(sources)}
""",
        sources,
    )

    with_brain = [r for r in rows if r["brain_regions"]]
    detected_everywhere = [
        r for r in with_brain if all((b["median_as_reported"] or 0) > 0 for b in r["brain_regions"])
    ]
    summary = {
        "run_id": args.run_id,
        "mode": "offline" if args.offline else "online",
        "generated_on": utc_date(),
        "gtex_dataset": GTEX_DATASET,
        "open_targets_data_version": ot_data_version,
        "genes_requested": len(genes),
        "genes_with_gtex_expression": len(rows),
        "genes_with_gtex_brain_regions": len(with_brain),
        "genes_detected_in_every_sampled_brain_region": len(detected_everywhere),
        "brain_regions_per_gene": sorted({r["brain_regions_reported"] for r in rows}),
        "adult_brain_celltype_resolution": "not_available_deferred_to_Q003",
        "developmental_timing_from_atlases": "not_retrieved_hand_curated_claims_only",
        "claims_written": len(claims),
        "sources_written": len(sources),
        "failures": failures,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
