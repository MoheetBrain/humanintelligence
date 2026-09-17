#!/usr/bin/env python3
"""Ingest GWAS Catalog v2 associations for the seed genes x the cognitive trait panel.

What this pipeline is
---------------------
A *positional* association ingester. It asks the GWAS Catalog which of its
associations have a seed gene in ``mapped_genes`` for a trait in
``atlases/alphacognition/cognitive_trait_panel.yaml``, and records what the catalogue
says, verbatim.

What this pipeline is emphatically NOT
--------------------------------------
Evidence that the gene is causal for the trait. ``mapped_genes`` is nearest-gene /
positional annotation. Every claim this script writes therefore carries
``causal_attribution.basis: gwas_association_only`` and
``causal_attribution.locus_to_gene_resolved: no``, and the ``ASSOCIATED_WITH``
predicate (never ``MODULATES``, never ``MAPS_TO_GENE``). Locus-to-gene evidence comes
from ``fetch_opentargets_genetics.py``, and even that is a model output, not a proof.

Outputs
-------
``data/raw/gwas_catalog/<UTC date>/*.json``      immutable snapshots (+ MANIFEST lines)
``data/raw/pubmed_esummary/<UTC date>/*.json``   titles for the studies' PMIDs
``data/interim/gwas_catalog_associations.jsonl`` tidy derived table, one row per association
``evidence/claims/alphacognition/gwas_catalog_derived.yaml``  machine claims
``pipelines/alphacognition/generated/sources_gwas_catalog.yaml``  source records to merge
``pipelines/alphacognition/generated/gwas_catalog_summary.json``  run counts

Usage
-----
    python pipelines/alphacognition/fetch_gwas_catalog.py
    python pipelines/alphacognition/fetch_gwas_catalog.py --offline
    python pipelines/alphacognition/fetch_gwas_catalog.py --genes GRIN2B CHRM1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # type: ignore[import-not-found]  # noqa: E402
    AGENT,
    CLAIMS_DIR,
    GENERATED_DIR,
    REPO_ROOT,
    SCHEMA_VERSION,
    claim_number,
    ensembl_index,
    queried_traits,
    resolve_species_id,
    read_json,
    seed_gene_symbols,
    self_href_params,
    snapshots,
    write_yaml_doc,
)
from _provenance import (  # type: ignore[import-not-found]  # noqa: E402
    INTERIM_DIR,
    http_get_json,
    ncbi_params,
    ncbi_sleep,
    scrub_query,
    utc_date,
    write_snapshot,
)

GWAS_BASE = "https://www.ebi.ac.uk/gwas/rest/api/v2"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RAW_REGISTRY = "gwas_catalog"
PAGE_SIZE = 100
MAX_PAGES = 20

DERIVED_PATH = INTERIM_DIR / "gwas_catalog_associations.jsonl"
CLAIMS_PATH = CLAIMS_DIR / "gwas_catalog_derived.yaml"
SOURCES_PATH = GENERATED_DIR / "sources_gwas_catalog.yaml"
SUMMARY_PATH = GENERATED_DIR / "gwas_catalog_summary.json"



# ----------------------------------------------------------------- network ----
def fetch_metadata() -> dict[str, Any]:
    url = f"{GWAS_BASE}/metadata"
    payload = http_get_json(url)
    write_snapshot(RAW_REGISTRY, payload, url=url, query={"endpoint": "metadata"}, name_hint="metadata")
    return payload


def fetch_efo_trait(efo_id: str) -> dict[str, Any]:
    url = f"{GWAS_BASE}/efo-traits/{efo_id}"
    payload = http_get_json(url)
    write_snapshot(RAW_REGISTRY, payload, url=url, query={"efo_trait_id": efo_id}, name_hint=f"trait_{efo_id}")
    return payload


def fetch_associations(gene: str, efo_id: str) -> list[dict[str, Any]]:
    """All association rows for one (mapped_gene, efo_id) pair, paginating."""
    rows: list[dict[str, Any]] = []
    url = f"{GWAS_BASE}/associations"
    for page in range(MAX_PAGES):
        params = {"mapped_gene": gene, "efo_id": efo_id, "page": page, "size": PAGE_SIZE}
        payload = http_get_json(url, params=params)
        write_snapshot(
            RAW_REGISTRY,
            payload,
            url=url,
            query=params,
            name_hint=f"assoc_{gene}_{efo_id}_p{page}",
        )
        batch = ((payload.get("_embedded") or {}).get("associations")) or []
        rows.extend(batch)
        page_info = payload.get("page") or {}
        if page + 1 >= int(page_info.get("totalPages") or 1) or not batch:
            break
    return rows


def fetch_study(accession: str) -> dict[str, Any]:
    url = f"{GWAS_BASE}/studies/{accession}"
    payload = http_get_json(url)
    write_snapshot(RAW_REGISTRY, payload, url=url, query={"accession": accession}, name_hint=f"study_{accession}")
    return payload


def fetch_pubmed_titles(pmids: list[str]) -> dict[str, dict[str, Any]]:
    """One batched ESummary call so the source records carry registry-supplied titles.

    The PMIDs come from GWAS Catalog association records; the titles come from
    PubMed. Nothing is authored here, which is the point: an id the catalogue reports
    but PubMed does not know would come back without a title and be dropped.
    """
    out: dict[str, dict[str, Any]] = {}
    if not pmids:
        return out
    chunk_size = 150
    for start in range(0, len(pmids), chunk_size):
        chunk = pmids[start : start + chunk_size]
        query = ncbi_params({"db": "pubmed", "retmode": "json", "id": ",".join(chunk)})
        payload = http_get_json(f"{EUTILS}/esummary.fcgi", params=query)
        ncbi_sleep()
        write_snapshot(
            "pubmed_esummary",
            payload,
            url=f"{EUTILS}/esummary.fcgi",
            query=scrub_query(query),
            name_hint=f"gwas_n{len(chunk)}",
        )
        for pmid, record in (payload.get("result") or {}).items():
            if pmid == "uids" or not isinstance(record, dict) or record.get("error"):
                continue
            out[pmid] = record
    return out


# --------------------------------------------------------- snapshot rebuilds ---
def load_snapshots_offline() -> dict[str, Any]:
    """Reconstruct every GWAS Catalog response class from committed snapshots."""
    metadata: dict[str, Any] = {}
    traits: dict[str, dict[str, Any]] = {}
    studies: dict[str, dict[str, Any]] = {}
    associations: dict[tuple[str, str], dict[int, list[dict[str, Any]]]] = {}

    for path in snapshots(RAW_REGISTRY):
        payload = read_json(path)
        if not payload:
            continue
        if payload.get("data_release_date"):
            metadata = payload
            continue
        if payload.get("accession_id") and payload.get("disease_trait") is not None:
            studies[str(payload["accession_id"])] = payload
            continue
        if payload.get("efo_id") and payload.get("uri"):
            traits[str(payload["efo_id"])] = payload
            continue
        params = self_href_params(payload)
        if "mapped_gene" in params and "efo_id" in params:
            key = (params["mapped_gene"], params["efo_id"])
            page = int(params.get("page") or 0)
            batch = ((payload.get("_embedded") or {}).get("associations")) or []
            associations.setdefault(key, {})[page] = batch
    return {"metadata": metadata, "traits": traits, "studies": studies, "associations": associations}


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
def association_rows(
    gene: str,
    trait: dict[str, Any],
    raw_rows: list[dict[str, Any]],
    *,
    release: str,
) -> list[dict[str, Any]]:
    """Project catalogue association records onto the derived table schema."""
    rows: list[dict[str, Any]] = []
    for record in raw_rows:
        efo_traits = record.get("efo_traits") or []
        rows.append(
            {
                "gene_symbol": gene,
                "efo_id": trait["efo_id"],
                "efo_label": trait["label"],
                "phenotype_class": trait["phenotype_class"],
                "use_in_ranking": trait["use_in_ranking"],
                "is_educational_attainment": bool(trait.get("is_educational_attainment")),
                "association_id": record.get("association_id"),
                "accession_id": record.get("accession_id"),
                "pubmed_id": str(record.get("pubmed_id")) if record.get("pubmed_id") else None,
                "first_author": record.get("first_author"),
                "reported_trait": record.get("reported_trait") or [],
                "association_efo_traits": [t.get("efo_id") for t in efo_traits],
                "p_value": record.get("p_value"),
                "pvalue_mantissa": record.get("pvalue_mantissa"),
                "pvalue_exponent": record.get("pvalue_exponent"),
                "beta_as_reported": record.get("beta"),
                "range_as_reported": record.get("range"),
                "risk_frequency_as_reported": record.get("risk_frequency"),
                "snp_effect_allele": record.get("snp_effect_allele") or [],
                "rs_ids": [a.get("rs_id") for a in (record.get("snp_allele") or []) if a.get("rs_id")],
                "locations": record.get("locations") or [],
                "mapped_genes": record.get("mapped_genes") or [],
                "multi_snp_haplotype": record.get("multi_snp_haplotype"),
                "snp_interaction": record.get("snp_interaction"),
                "gwas_catalog_release": release,
                "locus_to_gene_resolved": "no",
                "mapping_basis": "gwas_catalog_mapped_genes_positional",
            }
        )
    return rows


def study_design(study: dict[str, Any]) -> str:
    """``gwas`` or ``gwas_meta_analysis`` from what the study record actually says.

    The catalogue does not carry an explicit "is a meta-analysis" boolean in v2, so
    the decision is made from the study's own free-text sample description: a
    pooled/multi-cohort description ("up to N", "meta-analysis", multiple countries
    listed) is reported as a meta-analysis. Where the record does not support the
    distinction, the conservative ``gwas`` is used.
    """
    text = " ".join(
        [
            str(study.get("initial_sample_size") or ""),
            str(study.get("replication_sample_size") or ""),
            " ".join(study.get("discovery_ancestry") or []),
        ]
    ).lower()
    if "meta-analys" in text or study.get("pooled") is True or text.startswith("up to "):
        return "gwas_meta_analysis"
    if str(study.get("qualifier") or "").strip().lower() == "at least":
        return "gwas_meta_analysis"
    return "gwas"


def ancestry_note(study: dict[str, Any]) -> str:
    parts = study.get("discovery_ancestry") or []
    return "; ".join(str(p) for p in parts) if parts else "not reported in the study record"


# ------------------------------------------------------------------- claims ----
def build_claims(
    rows: list[dict[str, Any]],
    studies: dict[str, dict[str, Any]],
    *,
    release: str,
    run_id: str,
    species: str | None,
) -> list[dict[str, Any]]:
    """One claim per (gene, trait) with the supporting associations as evidence items."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["gene_symbol"], row["efo_id"]), []).append(row)

    claims: list[dict[str, Any]] = []
    per_gene_index: dict[str, int] = {}
    for gene, efo_id in sorted(grouped):
        group = sorted(grouped[(gene, efo_id)], key=lambda r: (str(r["accession_id"]), str(r["association_id"])))
        per_gene_index[gene] = per_gene_index.get(gene, 0) + 1
        claim_id = f"CLM:{AGENT.split(':')[1]}:gwas.{gene}:{claim_number(per_gene_index[gene])}"
        head = group[0]
        is_ea = bool(head["is_educational_attainment"])
        phenotype_class = head["phenotype_class"]
        reported = sorted({r for row in group for r in (row["reported_trait"] or [])})
        accessions = sorted({str(row["accession_id"]) for row in group})
        pmids = sorted({row["pubmed_id"] for row in group if row["pubmed_id"]})

        evidence: list[dict[str, Any]] = []
        for index, row in enumerate(group, start=1):
            study = studies.get(str(row["accession_id"]), {})
            design = study_design(study) if study else "gwas"
            reported_here = ", ".join(row["reported_trait"] or []) or head["efo_label"]
            alleles = ", ".join(row["snp_effect_allele"] or []) or "not reported"
            evidence.append(
                {
                    "source_id": f"SRC:PMID:{row['pubmed_id']}" if row["pubmed_id"] else f"SRC:DB:gwas_catalog:{release}",
                    "design": design,
                    "species": species,
                    "population": ancestry_note(study),
                    "sample_size": {
                        "reported_as": study.get("initial_sample_size"),
                        "value": None,
                        "unit": "individuals",
                    },
                    "endpoint": f"{reported_here} (GWAS Catalog association {row['association_id']}, "
                    f"variant {', '.join(row['rs_ids']) or 'not reported'}, effect allele {alleles})",
                    "endpoint_category": phenotype_class,
                    "endpoint_measured": "measured",
                    "effect_direction": "not_reported",
                    "effect_size": {
                        "metric": "beta" if row["beta_as_reported"] else "p_value_only",
                        "as_reported": row["beta_as_reported"],
                        "value": None,
                        "ci_lower": None,
                        "ci_upper": None,
                        "p_value": row["p_value"],
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
                        "registry": "gwas_catalog",
                        "release": release,
                        "accession_id": row["accession_id"],
                        "association_id": row["association_id"],
                        "risk_frequency_as_reported": row["risk_frequency_as_reported"],
                        "mapped_genes": row["mapped_genes"],
                        "mapping_basis": row["mapping_basis"],
                        "snapshot_registry": f"data/raw/{RAW_REGISTRY}/",
                    },
                }
            )

        statement = (
            f"The GWAS Catalog (release {release}) reports {len(group)} genome-wide association "
            f"record(s) for the trait '{head['efo_label']}' ({efo_id}) at loci whose positional "
            f"gene annotation includes {gene}; the studies' own wording for the trait is "
            f"{'; '.join(reported) or 'not reported'}. Positional mapping is not a causal gene assignment."
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
                    "basis": "gwas_association_only",
                    "locus_to_gene_resolved": "no",
                    "alternative_explanations": [
                        "the catalogue's mapped_genes field is positional (nearest-gene) annotation, "
                        "so the causal gene at this locus may be any gene in the LD block",
                        "linkage disequilibrium means the reported variant need not be the causal variant",
                        "population stratification and assortative mating are not excluded by the "
                        "catalogue record alone",
                    ]
                    + (
                        [
                            "educational attainment is a social-institutional outcome and is exposed to "
                            "indirect (parental) genetic effects, so an association here need not act on "
                            "the carrier's cognition at all"
                        ]
                        if is_ea
                        else []
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
                        }.get(phenotype_class, "unknown")
                    ),
                },
                "uncertainty": {
                    "representation": "ordinal_grade",
                    "scale": "evidence_strength_v1",
                    "level": 1,
                    "rationale": (
                        "database ingestion of positional associations: the association itself is a "
                        "catalogued human genetic result, but nothing here attributes it to this gene, "
                        "and per-allele GWAS effects are not intervention effects"
                    ),
                    "calibration_status": "uncalibrated_subjective",
                },
                "risks": [
                    "GWAS per-allele effect sizes are not intervention effect sizes and must never be "
                    "read as the expected effect of modulating this gene",
                    "discovery cohorts are overwhelmingly European-ancestry, so transportability is "
                    "unestablished: " + "; ".join(sorted({ancestry_note(studies.get(a, {})) for a in accessions})),
                ]
                + (["educational attainment is not an intelligence endpoint"] if is_ea else []),
                "confounders": ["linkage disequilibrium", "population structure", "assortative mating"]
                + (["family socioeconomic environment", "cohort education policy"] if is_ea else []),
                "dependencies": [],
                "status": "active",
                "provenance": {
                    "created_by": AGENT,
                    "created_on": utc_date(),
                    "method": "database_ingestion",
                    "run_id": run_id,
                    "pipeline": "pipelines/alphacognition/fetch_gwas_catalog.py",
                    "database_release": f"SRC:DB:gwas_catalog:{release}",
                    "supporting_accessions": accessions,
                    "supporting_pubmed_ids": pmids,
                },
            }
        )
    return claims


def build_sources(
    rows: list[dict[str, Any]],
    studies: dict[str, dict[str, Any]],
    pubmed: dict[str, dict[str, Any]],
    *,
    release: str,
) -> list[dict[str, Any]]:
    """Source records for the database release and every study PMID that resolved."""
    sources: list[dict[str, Any]] = [
        {
            "source_id": f"SRC:DB:gwas_catalog:{release}",
            "source_type": "database_release",
            "title": f"GWAS Catalog REST API v2 data release {release}",
            "year": int(release.split("-")[0]),
            "first_author": "EMBL-EBI GWAS Catalog",
            "container": "GWAS Catalog",
            "identifiers": {"data_release_date": release},
            "added_by": AGENT,
            "added_on": utc_date(),
            "retrieval": {"method": "gwas_catalog_api", "endpoint": f"{GWAS_BASE}/metadata"},
            "note": "Release recorded by pipelines/alphacognition/fetch_gwas_catalog.py from /v2/metadata.",
        }
    ]
    wanted = sorted({row["pubmed_id"] for row in rows if row["pubmed_id"]})
    for pmid in wanted:
        record = pubmed.get(pmid)
        if not record or not record.get("title"):
            continue
        article_ids = {item.get("idtype"): item.get("value") for item in record.get("articleids") or []}
        authors = record.get("authors") or []
        first_author = authors[0].get("name") if authors and isinstance(authors[0], dict) else None
        pubdate = str(record.get("pubdate") or record.get("epubdate") or "")
        year = None
        for token in pubdate.split():
            if token.isdigit() and len(token) == 4:
                year = int(token)
                break
        accessions = sorted({str(row["accession_id"]) for row in rows if row["pubmed_id"] == pmid})
        sample_sizes = sorted(
            {str(studies.get(a, {}).get("initial_sample_size")) for a in accessions if studies.get(a)}
        )
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
                    "discovered_via": "gwas_catalog_api",
                    "gwas_catalog_accessions": accessions,
                    "gwas_catalog_initial_sample_size": sample_sizes,
                },
                "note": "Discovered as the publication behind a GWAS Catalog study; title/year/journal "
                "come from PubMed ESummary, not from the catalogue and not from the agent.",
            }
        )
    return sources


# --------------------------------------------------------------------- main ----
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="rebuild derived artefacts from snapshots only")
    parser.add_argument("--genes", nargs="*", help="restrict to these gene symbols")
    parser.add_argument("--run-id", default="sprint1-alphacognition-gwas-01")
    args = parser.parse_args(argv)

    traits = queried_traits()
    genes = sorted(set(args.genes)) if args.genes else seed_gene_symbols()
    known_ensembl = ensembl_index()
    unresolved = [g for g in genes if g not in known_ensembl]
    if unresolved:
        print(f"note: {len(unresolved)} symbol(s) have no HGNC-resolved Ensembl id: {', '.join(unresolved)}")

    if args.offline:
        cache = load_snapshots_offline()
        metadata = cache["metadata"]
        if not metadata:
            print("offline rebuild impossible: no /v2/metadata snapshot under data/raw/gwas_catalog/")
            return 1
        release = str(metadata["data_release_date"])
        trait_records = cache["traits"]
        studies = cache["studies"]
        pubmed = load_pubmed_offline()
        raw_by_pair = {key: [r for _, batch in sorted(pages.items()) for r in batch] for key, pages in cache["associations"].items()}
    else:
        metadata = fetch_metadata()
        release = str(metadata["data_release_date"])
        trait_records = {}
        for trait in traits:
            payload = fetch_efo_trait(trait["efo_id"])
            trait_records[trait["efo_id"]] = payload
        studies = {}
        pubmed = {}
        raw_by_pair = {}
        for gene in genes:
            for trait in traits:
                raw_by_pair[(gene, trait["efo_id"])] = fetch_associations(gene, trait["efo_id"])

    # --- the panel must still describe the catalogue's own vocabulary -----------
    label_problems: list[str] = []
    for trait in traits:
        record = trait_records.get(trait["efo_id"])
        if not record:
            label_problems.append(f"{trait['efo_id']}: no trait record available")
        elif str(record.get("efo_trait")) != str(trait["label"]):
            label_problems.append(
                f"{trait['efo_id']}: panel says '{trait['label']}', catalogue says '{record.get('efo_trait')}'"
            )
    for problem in label_problems:
        print(f"  ! trait check: {problem}")

    # --- derived table ---------------------------------------------------------
    rows: list[dict[str, Any]] = []
    for gene in genes:
        for trait in traits:
            raw = raw_by_pair.get((gene, trait["efo_id"])) or []
            rows.extend(association_rows(gene, trait, raw, release=release))
    rows.sort(key=lambda r: (r["gene_symbol"], r["efo_id"], str(r["accession_id"]), str(r["association_id"])))

    # --- study records for the accessions we actually saw ----------------------
    accessions = sorted({str(row["accession_id"]) for row in rows if row["accession_id"]})
    if not args.offline:
        for accession in accessions:
            try:
                studies[accession] = fetch_study(accession)
            except Exception as error:  # recorded, never guessed
                print(f"  ! study fetch failed for {accession}: {type(error).__name__}: {error}")
        pmids = sorted({row["pubmed_id"] for row in rows if row["pubmed_id"]})
        try:
            pubmed = fetch_pubmed_titles(pmids)
        except Exception as error:
            print(f"  ! PubMed title fetch failed: {type(error).__name__}: {error}")
            pubmed = {}

    for row in rows:
        study = studies.get(str(row["accession_id"]), {})
        row["study_design"] = study_design(study) if study else "gwas"
        row["discovery_ancestry"] = study.get("discovery_ancestry") or []
        row["initial_sample_size_as_reported"] = study.get("initial_sample_size")
        row["snapshot_dir"] = f"data/raw/{RAW_REGISTRY}/"

    DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DERIVED_PATH, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    # --- claims + sources ------------------------------------------------------
    species = resolve_species_id(offline=args.offline)
    if species is None:
        print("  ! human taxid unresolved (NCBI taxonomy); claims will record context.species: []")
    claims = build_claims(rows, studies, release=release, run_id=args.run_id, species=species)
    sources = build_sources(rows, studies, pubmed, release=release)

    write_yaml_doc(
        CLAIMS_PATH,
        f"""# MACHINE-GENERATED — do not hand-edit.
# Produced by pipelines/alphacognition/fetch_gwas_catalog.py
# GWAS Catalog release: {release}   (source SRC:DB:gwas_catalog:{release})
#
# Every claim here is a POSITIONAL association record. causal_attribution.basis is
# gwas_association_only and locus_to_gene_resolved is no, without exception. Nothing in
# this file licenses an intervention on any gene, and no effect size in it has been
# reformatted: `effect_size.as_reported` is the catalogue's own string.
#
# Claims: {len(claims)}   associations covered: {len(rows)}
""",
        claims,
    )
    write_yaml_doc(
        SOURCES_PATH,
        f"""# MACHINE-GENERATED source records — merged into evidence/sources/alphacognition.yaml
# by pipelines/alphacognition/build_sources.py. Produced by fetch_gwas_catalog.py.
# PMIDs were discovered in GWAS Catalog association records; titles/years/journals come
# from PubMed ESummary. Records: {len(sources)}
""",
        sources,
    )

    ea_rows = [r for r in rows if r["is_educational_attainment"]]
    cognitive_rows = [r for r in rows if not r["is_educational_attainment"]]
    genes_with_cognitive = sorted({r["gene_symbol"] for r in cognitive_rows})
    summary = {
        "run_id": args.run_id,
        "mode": "offline" if args.offline else "online",
        "generated_on": utc_date(),
        "gwas_catalog_release": release,
        "efo_version": metadata.get("efo_version"),
        "genes_queried": len(genes),
        "traits_queried": len(traits),
        "pairs_queried": len(genes) * len(traits),
        "associations_total": len(rows),
        "associations_cognitive_traits": len(cognitive_rows),
        "associations_educational_attainment_or_literacy": len(ea_rows),
        "genes_with_any_association": len(sorted({r["gene_symbol"] for r in rows})),
        "genes_with_cognitive_trait_association": len(genes_with_cognitive),
        "genes_with_cognitive_trait_association_list": genes_with_cognitive,
        "unique_accessions": len(accessions),
        "unique_pubmed_ids": len(sorted({r["pubmed_id"] for r in rows if r["pubmed_id"]})),
        "claims_written": len(claims),
        "sources_written": len(sources),
        "trait_label_problems": label_problems,
        "symbols_without_ensembl_id": unresolved,
        "species_id": species,
        "snapshot_date": utc_date(),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
