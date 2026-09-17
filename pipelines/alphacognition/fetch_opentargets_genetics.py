#!/usr/bin/env python3
"""Locus-to-gene evidence for the cognitive trait panel, via Open Targets Platform.

The route (docs/API_RECIPES.md §5.2)
-----------------------------------
    trait EFO  ->  studies(diseaseIds:)                      GWAS studies for the trait
               ->  credibleSets(studyIds:, studyTypes:[gwas]) fine-mapped credible sets
               ->  l2GPredictions                             candidate genes per locus
               ->  colocalisation                             QTL support, where any exists

It is deliberately *not* the `target { credibleSets }` route, which returns molecular
QTL credible sets for the gene with empty L2G predictions and would answer a different
question.

What an L2G score is and is not
-------------------------------
`l2GPredictions.rows[].score` is the output of Open Targets' own locus-to-gene model. It
is **their** model output at a named data version, not this project's probability and not
a calibrated P(gene is causal for the trait). It is therefore never written into a
numeric field of a claim. It appears only inside `uncertainty.model_outputs[]` labelled
`derived_from: open_targets_l2g` with the data version, and `effect_size.metric` stays
`not_extracted` (contract P3, and the explicit instruction in API_RECIPES §5.2).
Colocalisation `h4`/`clpp` are treated identically.

Outputs
-------
``data/raw/opentargets_genetics/<UTC date>/*.json``  immutable snapshots (+ MANIFEST lines)
``data/interim/opentargets_l2g.jsonl``               tidy derived table
``evidence/claims/alphacognition/opentargets_l2g_derived.yaml``  machine claims
``pipelines/alphacognition/generated/sources_opentargets.yaml``  source records to merge
``pipelines/alphacognition/generated/opentargets_summary.json``  run counts

Note on the snapshot directory: ``data/raw/opentargets/**`` belongs to agent:integration
under docs/OWNERSHIP.yaml, so this pipeline writes ``data/raw/opentargets_genetics/``
instead, and a schema-change request asks for that path to be assigned.

Usage
-----
    python pipelines/alphacognition/fetch_opentargets_genetics.py
    python pipelines/alphacognition/fetch_opentargets_genetics.py --offline
    python pipelines/alphacognition/fetch_opentargets_genetics.py --traits EFO_0004337
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
    gene_to_target,
    queried_traits,
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
    ncbi_params,
    ncbi_sleep,
    scrub_query,
    utc_date,
    write_snapshot,
)

GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RAW_REGISTRY = "opentargets_genetics"
STUDY_PAGE = 200
CS_PAGE = 200
MAX_CS_PAGES = 40
COLOC_BATCH = 10

DERIVED_PATH = INTERIM_DIR / "opentargets_l2g.jsonl"
CLAIMS_PATH = CLAIMS_DIR / "opentargets_l2g_derived.yaml"
SOURCES_PATH = GENERATED_DIR / "sources_opentargets.yaml"
SUMMARY_PATH = GENERATED_DIR / "opentargets_summary.json"

META_FRAGMENT = "meta { apiVersion { x y z } dataVersion { year month iteration } }"

# The same DatabaseRelease is registered by agent:integration, and validator rule V4 rejects
# two registrations of one identifier with divergent `title` strings. The string below is
# agent:integration's, adopted verbatim so the identifier is unambiguous; this atlas used the
# genetics endpoints (studies / credibleSets / l2GPredictions / colocalisation /
# baselineExpression) rather than the target-annotation endpoints its wording describes, which
# is recorded in the source record's notes instead of by diverging from the shared title.
OPENTARGETS_RELEASE_TITLE = (
    "Open Targets Platform data release 26.06 \u2014 target annotations "
    "(tractability buckets, chemical probes, safety liabilities)."
)

STUDIES_QUERY = """
query Studies($efo: [String!], $index: Int!, $size: Int!) {
  studies(diseaseIds: $efo, page: {index: $index, size: $size}) {
    count
    rows {
      id studyType projectId traitFromSource condition
      pubmedId publicationFirstAuthor publicationDate publicationJournal publicationTitle
      nSamples nCases nControls initialSampleSize hasSumstats
      ldPopulationStructure { ldPopulation relativeSampleSize }
      diseases { id name }
    }
  }
  __META__
}
""".replace("__META__", META_FRAGMENT)

CREDIBLE_SETS_QUERY = """
query CredibleSets($ids: [String!], $index: Int!, $size: Int!) {
  credibleSets(studyIds: $ids, studyTypes: [gwas], page: {index: $index, size: $size}) {
    count
    rows {
      studyLocusId region finemappingMethod confidence
      pValueMantissa pValueExponent beta standardError
      variant { id rsIds }
      study { id studyType projectId traitFromSource pubmedId nSamples }
      l2GPredictions(page: {index: 0, size: 10}) {
        count
        rows { score target { approvedSymbol id } }
      }
      colocalisation(page: {index: 0, size: 1}) { count }
    }
  }
  __META__
}
""".replace("__META__", META_FRAGMENT)

COLOC_QUERY = """
query Coloc($ids: [String!]) {
  credibleSets(studyLocusIds: $ids, page: {index: 0, size: 20}) {
    count
    rows {
      studyLocusId
      study { id traitFromSource pubmedId }
      colocalisation(page: {index: 0, size: 100}) {
        count
        rows {
          h4 clpp colocalisationMethod numberColocalisingVariants
          otherStudyLocus {
            studyLocusId
            variant { id rsIds }
            study {
              id studyType projectId condition
              target { approvedSymbol id }
              biosample { biosampleId biosampleName }
            }
          }
        }
      }
    }
  }
  __META__
}
""".replace("__META__", META_FRAGMENT)


# ----------------------------------------------------------------- network ----
def graphql(query: str, variables: dict[str, Any], *, name_hint: str) -> dict[str, Any]:
    """POST a GraphQL query, snapshot the response, return the parsed body.

    GraphQL errors are raised rather than swallowed: a silently empty result set would
    be indistinguishable from "no evidence exists", which is exactly the confusion this
    repository is built to prevent.
    """
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL,
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
        url=GRAPHQL_URL,
        query={"operation": name_hint, "variables": variables},
        name_hint=name_hint,
    )
    if payload.get("errors"):
        raise RuntimeError(f"Open Targets GraphQL error for {name_hint}: {payload['errors']}")
    return payload


def data_version_of(payload: dict[str, Any]) -> str | None:
    meta = ((payload.get("data") or {}).get("meta") or {}).get("dataVersion") or {}
    year, month, iteration = meta.get("year"), meta.get("month"), meta.get("iteration")
    if not year or not month:
        return None
    return f"{year}.{month}" + (f".{iteration}" if iteration else "")


def api_version_of(payload: dict[str, Any]) -> str | None:
    meta = ((payload.get("data") or {}).get("meta") or {}).get("apiVersion") or {}
    if not meta.get("x"):
        return None
    return f"{meta.get('x')}.{meta.get('y')}.{meta.get('z')}"


def fetch_pubmed_titles(pmids: list[str]) -> dict[str, dict[str, Any]]:
    """Batched ESummary so source records carry registry-supplied titles."""
    out: dict[str, dict[str, Any]] = {}
    for start in range(0, len(pmids), 150):
        chunk = pmids[start : start + 150]
        if not chunk:
            continue
        query = ncbi_params({"db": "pubmed", "retmode": "json", "id": ",".join(chunk)})
        payload = http_get_json(f"{EUTILS}/esummary.fcgi", params=query)
        ncbi_sleep()
        write_snapshot(
            "pubmed_esummary",
            payload,
            url=f"{EUTILS}/esummary.fcgi",
            query=scrub_query(query),
            name_hint=f"otg_n{len(chunk)}",
        )
        for pmid, record in (payload.get("result") or {}).items():
            if pmid == "uids" or not isinstance(record, dict) or record.get("error"):
                continue
            out[pmid] = record
    return out


# ------------------------------------------------------------ offline rebuild --
def load_offline() -> dict[str, Any]:
    """Classify committed snapshots by the GraphQL data keys they contain."""
    studies_by_trait: dict[str, list[dict[str, Any]]] = {}
    credible_sets: dict[str, dict[str, Any]] = {}
    coloc: dict[str, dict[str, Any]] = {}
    versions: dict[str, str] = {}

    for path in snapshots(RAW_REGISTRY):
        payload = read_json(path)
        data = payload.get("data") or {}
        version = data_version_of(payload)
        if version:
            versions["data_version"] = version
        api = api_version_of(payload)
        if api:
            versions["api_version"] = api
        if "studies" in data and data["studies"]:
            for row in data["studies"].get("rows") or []:
                for disease in row.get("diseases") or []:
                    studies_by_trait.setdefault(str(disease["id"]), [])
                    if row["id"] not in {s["id"] for s in studies_by_trait[str(disease["id"])]}:
                        studies_by_trait[str(disease["id"])].append(row)
        if "credibleSets" in data and data["credibleSets"]:
            for row in data["credibleSets"].get("rows") or []:
                if "l2GPredictions" in row:
                    credible_sets[str(row["studyLocusId"])] = row
                if "colocalisation" in row and (row.get("colocalisation") or {}).get("rows") is not None:
                    coloc[str(row["studyLocusId"])] = row
    return {
        "studies_by_trait": studies_by_trait,
        "credible_sets": credible_sets,
        "coloc": coloc,
        "versions": versions,
    }


def load_pubmed_offline() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in snapshots("pubmed_esummary"):
        payload = read_json(path)
        for pmid, record in (payload.get("result") or {}).items():
            if pmid == "uids" or not isinstance(record, dict) or record.get("error"):
                continue
            if record.get("title"):
                out.setdefault(pmid, record)
    return out


# ------------------------------------------------------------- row assembly ----
def ancestry_summary(study: dict[str, Any]) -> str:
    parts = study.get("ldPopulationStructure") or []
    if not parts:
        return "not reported in the study record"
    return "; ".join(
        f"{p.get('ldPopulation')} (relative sample size {p.get('relativeSampleSize')})" for p in parts
    )


def qtl_coloc_for_gene(coloc_record: dict[str, Any], symbol: str) -> list[dict[str, Any]]:
    """Molecular-QTL colocalisations whose QTL gene is ``symbol``."""
    out: list[dict[str, Any]] = []
    for row in ((coloc_record or {}).get("colocalisation") or {}).get("rows") or []:
        other = row.get("otherStudyLocus") or {}
        study = other.get("study") or {}
        if str(study.get("studyType")) == "gwas":
            continue
        target = study.get("target") or {}
        if str(target.get("approvedSymbol")) != symbol:
            continue
        biosample = study.get("biosample") or {}
        out.append(
            {
                "other_study_locus_id": other.get("studyLocusId"),
                "other_study_id": study.get("id"),
                "qtl_study_type": study.get("studyType"),
                "qtl_project_id": study.get("projectId"),
                "qtl_gene_symbol": target.get("approvedSymbol"),
                "qtl_gene_ensembl_id": target.get("id"),
                "qtl_biosample_id": biosample.get("biosampleId"),
                "qtl_biosample_name": biosample.get("biosampleName"),
                "colocalisation_method": row.get("colocalisationMethod"),
                "h4_model_output": row.get("h4"),
                "clpp_model_output": row.get("clpp"),
                "number_colocalising_variants": row.get("numberColocalisingVariants"),
            }
        )
    return out


def derived_rows(
    traits: list[dict[str, Any]],
    studies_by_trait: dict[str, list[dict[str, Any]]],
    credible_sets: dict[str, dict[str, Any]],
    coloc: dict[str, dict[str, Any]],
    *,
    data_version: str | None,
) -> list[dict[str, Any]]:
    """One row per credible set, with its top L2G genes and any seed-gene coloc."""
    seed = set(seed_gene_symbols())
    trait_by_efo = {t["efo_id"]: t for t in traits}
    study_index: dict[str, tuple[str, dict[str, Any]]] = {}
    for efo_id, rows in studies_by_trait.items():
        for row in rows:
            study_index.setdefault(str(row["id"]), (efo_id, row))

    rows_out: list[dict[str, Any]] = []
    for study_locus_id, record in credible_sets.items():
        study = record.get("study") or {}
        study_id = str(study.get("id"))
        efo_id, study_full = study_index.get(study_id, (None, {}))
        trait = trait_by_efo.get(efo_id) if efo_id else None
        predictions = sorted(
            ((record.get("l2GPredictions") or {}).get("rows") or []),
            key=lambda p: -(p.get("score") or 0),
        )
        top_genes = [
            {
                "symbol": (p.get("target") or {}).get("approvedSymbol"),
                "ensembl_gene_id": (p.get("target") or {}).get("id"),
                "l2g_score_model_output": p.get("score"),
            }
            for p in predictions
        ]
        seed_hits = [g for g in top_genes if g["symbol"] in seed]
        seed_coloc = {
            str(g["symbol"]): qtl_coloc_for_gene(coloc.get(study_locus_id, {}), str(g["symbol"]))
            for g in seed_hits
        }
        rows_out.append(
            {
                "study_locus_id": study_locus_id,
                "study_id": study_id,
                "study_type": study.get("studyType"),
                "project_id": study.get("projectId"),
                "trait_from_source": study.get("traitFromSource"),
                "efo_id": efo_id,
                "efo_label": trait["label"] if trait else None,
                "phenotype_class": trait["phenotype_class"] if trait else None,
                "use_in_ranking": trait["use_in_ranking"] if trait else None,
                "is_educational_attainment": bool(trait.get("is_educational_attainment")) if trait else None,
                "pubmed_id": str(study.get("pubmedId")) if study.get("pubmedId") else None,
                "n_samples": study.get("nSamples"),
                "initial_sample_size_as_reported": study_full.get("initialSampleSize"),
                "ld_population_structure": study_full.get("ldPopulationStructure") or [],
                "ancestry_summary": ancestry_summary(study_full),
                "region": record.get("region"),
                "variant_id": (record.get("variant") or {}).get("id"),
                "rs_ids": (record.get("variant") or {}).get("rsIds") or [],
                "finemapping_method": record.get("finemappingMethod"),
                "finemapping_confidence": record.get("confidence"),
                "p_value_mantissa": record.get("pValueMantissa"),
                "p_value_exponent": record.get("pValueExponent"),
                "beta_as_reported": record.get("beta"),
                "standard_error_as_reported": record.get("standardError"),
                "l2g_prediction_count": (record.get("l2GPredictions") or {}).get("count"),
                "top_l2g_genes": top_genes,
                "seed_gene_l2g_hits": seed_hits,
                "colocalisation_count": (record.get("colocalisation") or {}).get("count"),
                "seed_gene_qtl_colocalisations": seed_coloc,
                "open_targets_data_version": data_version,
                "model_output_provenance": "open_targets_l2g",
                "snapshot_dir": f"data/raw/{RAW_REGISTRY}/",
            }
        )
    rows_out.sort(key=lambda r: (str(r["efo_id"]), str(r["study_id"]), str(r["study_locus_id"])))
    return rows_out


# ------------------------------------------------------------------- claims ----
def build_claims(
    rows: list[dict[str, Any]],
    *,
    data_version: str | None,
    api_version: str | None,
    run_id: str,
    species: str | None,
) -> list[dict[str, Any]]:
    """One claim per (seed gene, trait) that Open Targets' L2G model implicates."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        for hit in row["seed_gene_l2g_hits"]:
            if not row["efo_id"]:
                continue
            grouped.setdefault((str(hit["symbol"]), str(row["efo_id"])), []).append(row)

    claims: list[dict[str, Any]] = []
    per_gene: dict[str, int] = {}
    for gene, efo_id in sorted(grouped):
        group = sorted(grouped[(gene, efo_id)], key=lambda r: str(r["study_locus_id"]))
        head = group[0]
        phenotype_class = head["phenotype_class"]
        is_ea = bool(head["is_educational_attainment"])
        has_qtl_coloc = any(r["seed_gene_qtl_colocalisations"].get(gene) for r in group)
        per_gene[gene] = per_gene.get(gene, 0) + 1
        claim_id = f"CLM:{AGENT.split(':')[1]}:l2g.{gene}:{claim_number(per_gene[gene])}"

        evidence: list[dict[str, Any]] = []
        model_outputs: list[dict[str, Any]] = []
        for row in group:
            hit = next(h for h in row["seed_gene_l2g_hits"] if h["symbol"] == gene)
            colocs = row["seed_gene_qtl_colocalisations"].get(gene) or []
            evidence.append(
                {
                    "source_id": f"SRC:PMID:{row['pubmed_id']}"
                    if row["pubmed_id"]
                    else f"SRC:DB:opentargets:{data_version}",
                    "design": "colocalisation" if colocs else "fine_mapping",
                    "species": species,
                    "population": row["ancestry_summary"],
                    "sample_size": {
                        "reported_as": row["initial_sample_size_as_reported"],
                        "value": row["n_samples"] if isinstance(row["n_samples"], int) else None,
                        "unit": "individuals",
                    },
                    "endpoint": (
                        f"{row['trait_from_source']} — fine-mapped credible set "
                        f"{row['study_locus_id']} (study {row['study_id']}, variant "
                        f"{row['variant_id']}, rsIDs {', '.join(row['rs_ids']) or 'not reported'}, "
                        f"method {row['finemapping_method']})"
                    ),
                    "endpoint_category": phenotype_class,
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
                        "registry": "opentargets_platform",
                        "data_version": data_version,
                        "api_version": api_version,
                        "study_locus_id": row["study_locus_id"],
                        "study_id": row["study_id"],
                        "finemapping_method": row["finemapping_method"],
                        "finemapping_confidence": row["finemapping_confidence"],
                        "l2g_candidate_gene_count": row["l2g_prediction_count"],
                        "l2g_ranked_candidates": [g["symbol"] for g in row["top_l2g_genes"]],
                        "colocalisation_count": row["colocalisation_count"],
                        "qtl_colocalisations_for_this_gene": colocs,
                        "snapshot_registry": f"data/raw/{RAW_REGISTRY}/",
                    },
                    "note": (
                        "p-value mantissa/exponent and beta are left in the derived table rather than "
                        "copied here because the credible-set record reports them per lead variant, "
                        "not as an effect of the gene."
                    ),
                }
            )
            model_outputs.append(
                {
                    "kind": "locus_to_gene_score",
                    "derived_from": "open_targets_l2g",
                    "data_version": data_version,
                    "study_locus_id": row["study_locus_id"],
                    "gene": gene,
                    "value_as_published": hit["l2g_score_model_output"],
                    "rank_among_candidates_at_locus": [g["symbol"] for g in row["top_l2g_genes"]].index(gene) + 1,
                    "candidates_at_locus": len(row["top_l2g_genes"]),
                    "interpretation_limits": (
                        "This is Open Targets' published model output. It is not this project's "
                        "probability, not a calibrated P(causal gene), and not an effect size. It may "
                        "not be compared across data versions or thresholded into a decision here."
                    ),
                }
            )
            for coloc in colocs:
                model_outputs.append(
                    {
                        "kind": "colocalisation_posterior",
                        "derived_from": "open_targets_colocalisation",
                        "data_version": data_version,
                        "study_locus_id": row["study_locus_id"],
                        "qtl_study_id": coloc["other_study_id"],
                        "qtl_study_type": coloc["qtl_study_type"],
                        "qtl_biosample_name": coloc["qtl_biosample_name"],
                        "method": coloc["colocalisation_method"],
                        "h4_as_published": coloc["h4_model_output"],
                        "clpp_as_published": coloc["clpp_model_output"],
                        "interpretation_limits": (
                            "Published colocalisation posterior from Open Targets. Colocalisation with a "
                            "QTL supports the gene assignment at this locus; it does not establish that "
                            "changing the gene changes the trait."
                        ),
                    }
                )

        basis = "colocalisation_qtl" if has_qtl_coloc else "finemapped_credible_set"
        loci = sorted({r["study_locus_id"] for r in group})
        studies = sorted({r["study_id"] for r in group})
        pmids = sorted({r["pubmed_id"] for r in group if r["pubmed_id"]})
        competing = sorted(
            {
                g["symbol"]
                for r in group
                for g in r["top_l2g_genes"]
                if g["symbol"] and g["symbol"] != gene
            }
        )
        statement = (
            f"Open Targets Platform (data version {data_version}) ranks {gene} among the "
            f"locus-to-gene candidate genes for {len(loci)} fine-mapped GWAS credible set(s) of "
            f"'{head['efo_label']}' ({efo_id})"
            + (
                ", and at least one of those loci colocalises with a molecular QTL for this gene"
                if has_qtl_coloc
                else ", with no molecular-QTL colocalisation for this gene at those loci"
            )
            + f". {len(competing)} other gene(s) are candidates at the same loci."
        )
        claims.append(
            {
                "claim_id": claim_id,
                "schema_version": SCHEMA_VERSION,
                "statement": statement,
                "subject": f"GENE:{gene}",
                "predicate": "ASSOCIATED_WITH",
                "object": f"PHENO:{phenotype_class}",
                "claim_type": "association",
                "direction": "unclear",
                "context": {
                    "species": [species] if species else [],
                    "life_stage": "adult",
                    "baseline_context": "mixed",
                    "brain_regions": [],
                    "cell_types": [],
                },
                "phenotype_class": phenotype_class,
                "causal_attribution": {
                    "basis": basis,
                    "locus_to_gene_resolved": "partial",
                    "alternative_explanations": [
                        f"locus-to-gene is a statistical model: {len(competing)} competing candidate "
                        f"gene(s) at the same loci ({', '.join(competing) or 'none'})",
                        "fine mapping identifies credible variant sets, not mechanisms; the assigned "
                        "gene may still be the wrong one",
                        "European-ancestry LD structure dominates the fine mapping, so the credible set "
                        "may not transfer to other ancestries",
                    ]
                    + (
                        []
                        if has_qtl_coloc
                        else [
                            "no molecular-QTL colocalisation supports this assignment, so it rests on the "
                            "L2G model's feature weighting alone"
                        ]
                    ),
                },
                "evidence": evidence,
                "translation": {
                    "adult_relevance": "unknown",
                    "healthy_baseline": "mixed",
                    "supra_normal": "untested",
                    "human_relevance": "human_genetic",
                    "general_intelligence_relevance": (
                        "educational_attainment_proxy"
                        if is_ea
                        else {
                            "g_factor": "g_or_fluid_measured",
                            "fluid_reasoning": "g_or_fluid_measured",
                            "working_memory": "single_domain_cognitive",
                            "processing_speed": "single_domain_cognitive",
                            "episodic_memory": "single_domain_cognitive",
                            "executive_function": "single_domain_cognitive",
                            "clinical_cognitive_composite": "multi_domain_cognitive",
                        }.get(str(phenotype_class), "unknown")
                    ),
                },
                "uncertainty": {
                    "representation": "ordinal_grade",
                    "scale": "evidence_strength_v1",
                    "level": 2 if has_qtl_coloc else 1,
                    "rationale": (
                        "fine-mapped human genetic evidence with QTL colocalisation support for the gene "
                        "assignment, but still an association: no perturbation of this gene has been "
                        "shown to change the trait"
                        if has_qtl_coloc
                        else "fine-mapped human genetic evidence, gene assignment from a published "
                        "statistical model with competing candidates and no QTL corroboration"
                    ),
                    "calibration_status": "model_derived_uncalibrated",
                    "model_outputs": model_outputs,
                },
                "risks": [
                    "an L2G score is not a probability this project computed and must not be thresholded "
                    "into a causal decision",
                    "fine mapping and colocalisation establish which gene a signal acts through, never "
                    "that intervening on that gene would move the trait",
                    f"single-ancestry dependence: {head['ancestry_summary']}",
                ]
                + (["educational attainment is not an intelligence endpoint"] if is_ea else []),
                "confounders": ["LD structure", "gene density at the locus", "QTL tissue availability"],
                "dependencies": [],
                "status": "active",
                "provenance": {
                    "created_by": AGENT,
                    "created_on": utc_date(),
                    "method": "database_ingestion",
                    "run_id": run_id,
                    "pipeline": "pipelines/alphacognition/fetch_opentargets_genetics.py",
                    "database_release": f"SRC:DB:opentargets:{data_version}",
                    "supporting_study_locus_ids": loci,
                    "supporting_study_ids": studies,
                    "supporting_pubmed_ids": pmids,
                },
            }
        )
    return claims


def build_sources(
    rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    pubmed: dict[str, dict[str, Any]],
    *,
    data_version: str | None,
) -> list[dict[str, Any]]:
    cited: set[str] = set()
    for claim in claims:
        for item in claim["evidence"]:
            source = str(item["source_id"])
            if source.startswith("SRC:PMID:"):
                cited.add(source.split(":")[-1])
    sources: list[dict[str, Any]] = [
        {
            "source_id": f"SRC:DB:opentargets:{data_version}",
            "source_type": "database_release",
            "title": OPENTARGETS_RELEASE_TITLE,
            "year": 2000 + int(str(data_version).split(".")[0]) if data_version else None,
            "first_author": "Open Targets",
            "container": "Open Targets Platform",
            "identifiers": {"data_version": data_version},
            "added_by": AGENT,
            "added_on": utc_date(),
            "retrieval": {"method": "opentargets_api", "endpoint": GRAPHQL_URL},
            "note": "Data version read from the GraphQL meta.dataVersion block on every response by "
            "pipelines/alphacognition/fetch_opentargets_genetics.py. Title string adopted verbatim "
            "from agent:integration's registration of the same release so the identifier does not "
            "diverge (rule V4); this atlas used the genetics endpoints (studies, credibleSets, "
            "l2GPredictions, colocalisation, baselineExpression), not the target-annotation ones.",
        }
    ]
    for pmid in sorted(cited):
        record = pubmed.get(pmid)
        if not record or not record.get("title"):
            continue
        article_ids = {item.get("idtype"): item.get("value") for item in record.get("articleids") or []}
        authors = record.get("authors") or []
        first_author = authors[0].get("name") if authors and isinstance(authors[0], dict) else None
        pubdate = str(record.get("pubdate") or record.get("epubdate") or "")
        year = next((int(t) for t in pubdate.split() if t.isdigit() and len(t) == 4), None)
        study_ids = sorted({r["study_id"] for r in rows if r["pubmed_id"] == pmid})
        sources.append(
            {
                "source_id": f"SRC:PMID:{pmid}",
                "source_type": "journal_article",
                "title": str(record["title"]).rstrip("."),
                "year": year,
                "first_author": first_author or record.get("sortfirstauthor"),
                "container": record.get("source"),
                "identifiers": {"pmid": pmid, "doi": article_ids.get("doi")},
                "added_by": AGENT,
                "added_on": utc_date(),
                "retrieval": {
                    "method": "pubmed_metadata",
                    "discovered_via": "opentargets_api",
                    "open_targets_study_ids": study_ids,
                },
                "note": "Publication behind an Open Targets GWAS study whose fine-mapped credible sets "
                "were used; title/year/journal come from PubMed ESummary.",
            }
        )
    return sources


# --------------------------------------------------------------------- main ----
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="rebuild derived artefacts from snapshots only")
    parser.add_argument("--traits", nargs="*", help="restrict to these EFO ids")
    parser.add_argument("--run-id", default="sprint1-alphacognition-otg-01")
    args = parser.parse_args(argv)

    traits = queried_traits()
    if args.traits:
        wanted = set(args.traits)
        traits = [t for t in traits if t["efo_id"] in wanted]

    seed = set(seed_gene_symbols())
    versions: dict[str, str | None] = {"data_version": None, "api_version": None}
    studies_by_trait: dict[str, list[dict[str, Any]]] = {}
    credible_sets: dict[str, dict[str, Any]] = {}
    coloc: dict[str, dict[str, Any]] = {}
    failures: list[str] = []

    if args.offline:
        cache = load_offline()
        studies_by_trait = cache["studies_by_trait"]
        credible_sets = cache["credible_sets"]
        coloc = cache["coloc"]
        versions.update(cache["versions"])
        pubmed = load_pubmed_offline()
        if not credible_sets:
            print("offline rebuild impossible: no credibleSets snapshots under data/raw/" + RAW_REGISTRY)
            return 1
    else:
        # ---- stage 1: GWAS studies per trait ---------------------------------
        for trait in traits:
            efo_id = trait["efo_id"]
            try:
                payload = graphql(
                    STUDIES_QUERY,
                    {"efo": [efo_id], "index": 0, "size": STUDY_PAGE},
                    name_hint=f"studies_{efo_id}",
                )
            except Exception as error:
                failures.append(f"studies {efo_id}: {type(error).__name__}: {error}")
                continue
            versions["data_version"] = data_version_of(payload) or versions["data_version"]
            versions["api_version"] = api_version_of(payload) or versions["api_version"]
            rows = ((payload.get("data") or {}).get("studies") or {}).get("rows") or []
            studies_by_trait[efo_id] = [r for r in rows if r.get("studyType") == "gwas"]
            print(f"  {efo_id}: {len(studies_by_trait[efo_id])} GWAS studies (of {len(rows)} total)")

        # ---- stage 2: fine-mapped credible sets, batched per trait ------------
        for trait in traits:
            efo_id = trait["efo_id"]
            study_ids = [str(s["id"]) for s in studies_by_trait.get(efo_id, [])]
            if not study_ids:
                continue
            for index in range(MAX_CS_PAGES):
                try:
                    payload = graphql(
                        CREDIBLE_SETS_QUERY,
                        {"ids": study_ids, "index": index, "size": CS_PAGE},
                        name_hint=f"cs_{efo_id}_p{index}",
                    )
                except Exception as error:
                    failures.append(f"credibleSets {efo_id} page {index}: {type(error).__name__}: {error}")
                    break
                block = ((payload.get("data") or {}).get("credibleSets") or {})
                rows = block.get("rows") or []
                for row in rows:
                    credible_sets[str(row["studyLocusId"])] = row
                total = int(block.get("count") or 0)
                if not rows or (index + 1) * CS_PAGE >= total:
                    break
            print(f"  {efo_id}: {sum(1 for r in credible_sets.values() if str((r.get('study') or {}).get('id')) in set(study_ids))} credible sets seen")

        # ---- stage 3: colocalisation detail, only for seed-gene loci ---------
        seed_loci = sorted(
            {
                study_locus_id
                for study_locus_id, record in credible_sets.items()
                if any(
                    ((p.get("target") or {}).get("approvedSymbol")) in seed
                    for p in ((record.get("l2GPredictions") or {}).get("rows") or [])
                )
            }
        )
        print(f"  seed-gene credible sets needing colocalisation detail: {len(seed_loci)}")
        for start in range(0, len(seed_loci), COLOC_BATCH):
            chunk = seed_loci[start : start + COLOC_BATCH]
            try:
                payload = graphql(COLOC_QUERY, {"ids": chunk}, name_hint=f"coloc_b{start // COLOC_BATCH}")
            except Exception as error:
                failures.append(f"colocalisation batch {start}: {type(error).__name__}: {error}")
                continue
            for row in ((payload.get("data") or {}).get("credibleSets") or {}).get("rows") or []:
                coloc[str(row["studyLocusId"])] = row

        pmids = sorted({str(s["pubmedId"]) for rows in studies_by_trait.values() for s in rows if s.get("pubmedId")})
        try:
            pubmed = fetch_pubmed_titles(pmids)
        except Exception as error:
            failures.append(f"pubmed titles: {type(error).__name__}: {error}")
            pubmed = {}

    rows = derived_rows(
        traits, studies_by_trait, credible_sets, coloc, data_version=versions["data_version"]
    )
    DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DERIVED_PATH, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    species = resolve_species_id(offline=args.offline)
    claims = build_claims(
        rows,
        data_version=versions["data_version"],
        api_version=versions["api_version"],
        run_id=args.run_id,
        species=species,
    )
    sources = build_sources(rows, claims, pubmed, data_version=versions["data_version"])

    write_yaml_doc(
        CLAIMS_PATH,
        f"""# MACHINE-GENERATED — do not hand-edit.
# Produced by pipelines/alphacognition/fetch_opentargets_genetics.py
# Open Targets Platform data version: {versions['data_version']}  API {versions['api_version']}
#   (source SRC:DB:opentargets:{versions['data_version']})
#
# These claims record that Open Targets' locus-to-gene MODEL ranks a seed gene at a
# fine-mapped credible set for a cognitive trait. The L2G score and any colocalisation
# posterior appear only inside uncertainty.model_outputs[] with `derived_from` and the
# data version; `effect_size.metric` is `not_extracted` throughout. They are other
# people's model outputs, never this project's probabilities, and never a licence to
# intervene on the gene.
#
# Claims: {len(claims)}   credible sets in the derived table: {len(rows)}
""",
        claims,
    )
    write_yaml_doc(
        SOURCES_PATH,
        f"""# MACHINE-GENERATED source records — merged into evidence/sources/alphacognition.yaml
# by pipelines/alphacognition/build_sources.py. Produced by fetch_opentargets_genetics.py.
# Records: {len(sources)}
""",
        sources,
    )

    genes_with_l2g = sorted({str(h["symbol"]) for r in rows for h in r["seed_gene_l2g_hits"]})
    genes_with_coloc = sorted(
        {gene for r in rows for gene, hits in r["seed_gene_qtl_colocalisations"].items() if hits}
    )
    cognitive_claims = [c for c in claims if c["phenotype_class"] != "educational_attainment"]
    summary = {
        "run_id": args.run_id,
        "mode": "offline" if args.offline else "online",
        "generated_on": utc_date(),
        "open_targets_data_version": versions["data_version"],
        "open_targets_api_version": versions["api_version"],
        "species_id": species,
        "traits_queried": len(traits),
        "gwas_studies_seen": sum(len(v) for v in studies_by_trait.values()),
        "credible_sets_seen": len(credible_sets),
        "credible_sets_in_derived_table": len(rows),
        "credible_sets_with_seed_gene_l2g": sum(1 for r in rows if r["seed_gene_l2g_hits"]),
        "seed_genes_with_l2g_evidence": genes_with_l2g,
        "seed_genes_with_l2g_evidence_count": len(genes_with_l2g),
        "seed_genes_with_qtl_colocalisation": genes_with_coloc,
        "seed_genes_with_qtl_colocalisation_count": len(genes_with_coloc),
        "claims_written": len(claims),
        "claims_on_cognitive_traits": len(cognitive_claims),
        "claims_on_educational_attainment": len(claims) - len(cognitive_claims),
        "sources_written": len(sources),
        "failures": failures,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
