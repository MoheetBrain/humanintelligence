#!/usr/bin/env python3
"""Emit `evidence_gap` claims for the coverage gaps this atlas's sweeps actually found.

Why this exists
---------------
A facet graded `assessed` with `level: 0` means "searched, nothing found" (contract §5.3).
The assessment schema requires an assessed facet to cite evidence, and there is no ordinary
claim to cite for something that was not found. Resolution R5 supplies the mechanism:
`claim_type: evidence_gap` is a **graph-inert** record that says a measurement does not
exist, contributes nothing for or against the proposition, may never raise a
`counter_level`, and counts towards a coverage gap.

So every level-0 grade in this atlas points at a record that states, with a named source,
exactly which search was performed and what it did not contain. That is strictly more
informative than an empty `claim_refs`, and it is what stops "nobody looked" from being
indistinguishable from "it was tested and failed".

Two kinds are emitted:

**A — genetics sweep gap** (`CLM:alphacognition:gap.{GENE}:001`), for any seed gene with no
cognitive-trait association in GWAS Catalog release 2026-09-13 **and** no cognitive-trait
locus-to-gene candidacy in Open Targets 26.06. Sources: the two pinned database releases.

**B — lead-atlas literature gap** (`CLM:alphacognition:gap.{SYMBOL}:002`), for the six
targets this agent leads, naming the facet propositions for which no study retrieved in this
session measured the relevant endpoint at all. Its source is the target's own primary study,
with `endpoint_measured: not_measured_in_protocol` — because the honest statement is not
"no paper exists" in the abstract but "the studies that do exist did not measure this".

Both kinds use `predicate: ABOUT` onto the phenotype that was not measured, anchored on a
claim that does exist, which is the same shape `agent:brakes` used for its trial-level gaps.

Usage
-----
    python pipelines/alphacognition/build_coverage_gaps.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # type: ignore[import-not-found]  # noqa: E402
    AGENT,
    CLAIMS_DIR,
    GENERATED_DIR,
    REPO_ROOT,
    SCHEMA_VERSION,
    resolve_species_id,
    seed_gene_symbols,
    write_yaml_doc,
)
from _provenance import INTERIM_DIR  # type: ignore[import-not-found]  # noqa: E402

OUT_PATH = CLAIMS_DIR / "coverage_gaps.yaml"
SUMMARY_PATH = GENERATED_DIR / "coverage_gap_summary.json"
GWAS_RELEASE = "SRC:DB:gwas_catalog:2026-09-13"
OT_RELEASE = "SRC:DB:opentargets:26.06"

# Kind B: the six targets this agent leads, the primary study whose protocol did not measure
# the endpoint, and the facet propositions that therefore have no measurement behind them.
LEAD_GAPS: dict[str, dict[str, Any]] = {
    "CRTC1": {
        "anchor": "CLM:alphacognition:CRTC1:001",
        "source_id": "SRC:PMID:23223304",
        "design": "overexpression",
        "species_key": "mouse",
        "population": "mice receiving local viral CRTC1 overexpression in dorsal dentate gyrus",
        "facets": ["transfer_breadth", "dose_response_knowledge", "human_intervention_evidence"],
        "endpoint": "context fear memory only; no second cognitive domain, no transfer measure, no dose or expression-level series, and no human participants",
        "detail": "no study retrieved for CRTC1 measured a second cognitive domain, a transfer endpoint, a dose- or expression-level-response relation, or any human endpoint. The rodent studies that do exist used a single viral overexpression level in a single paradigm.",
    },
    "GRIN2B": {
        "anchor": "CLM:alphacognition:GRIN2B:001",
        "source_id": "SRC:PMID:10485705",
        "design": "overexpression",
        "species_key": "mouse",
        "population": "transgenic mice with forebrain-specific NR2B overexpression and wild-type littermates",
        "facets": ["dose_response_knowledge", "human_intervention_evidence"],
        "endpoint": "behavioural learning and memory at one transgenic expression level; no dose or expression-level series and no human interventional endpoint",
        "detail": "transgenic overexpression has one level by construction, so no retrieved GRIN2B study measured a dose- or expression-response relation — which for a gene whose excess function causes human disease is the most consequential gap in this dossier. No human interventional study of GRIN2B for a cognitive endpoint exists.",
    },
    "CHRM1": {
        "anchor": "CLM:alphacognition:CHRM1:004",
        "source_id": "SRC:PMID:39880004",
        "design": "meta_analysis",
        "species_key": "human",
        "population": "adults with schizophrenia experiencing acute psychosis, pooled from three double-blind randomised placebo-controlled trials",
        "facets": [],
        "endpoint": "PANSS total and subscale scores, discontinuation and adverse events; NO cognitive endpoint of any kind",
        "detail": "the largest human M1 dataset by sample size measured no cognitive endpoint at all, so with respect to cognition it is a gap and not a null. This record exists so that the approval it supports can never be read as cognitive evidence in either direction.",
    },
    "GRM5": {
        "anchor": "CLM:alphacognition:GRM5:001",
        "source_id": "SRC:PMID:37651202",
        "design": "rct_parallel",
        "species_key": "human",
        "population": "3- to 6-year-old children with fragile X syndrome; no healthy comparison arm",
        "facets": ["above_baseline_enhancement", "transfer_breadth"],
        "endpoint": "communication and cognitive/language measures in a deficit population; no healthy-baseline arm and no far-transfer or real-world endpoint",
        "detail": "no retrieved study of mGluR5 modulation included a healthy baseline, in any species, so supra-normal potential has never been measured. The human trial's own multi-endpoint null is separately recorded as measured counter-evidence in CLM:alphacognition:GRM5:001 and is NOT part of this gap.",
    },
    "DRD1": {
        "anchor": "CLM:alphacognition:DRD1:001",
        "source_id": "SRC:PMID:12454947",
        "design": "pharmacological_perturbation",
        "species_key": "mouse",
        "population": "male C57BL/6 mice performing a spatial working memory task",
        "facets": ["transfer_breadth", "human_intervention_evidence"],
        "endpoint": "spatial working memory only; no second cognitive domain and no human participants",
        "detail": "the primary DRD1 source measured one cognitive domain in one species. No primary human interventional study of D1 agonism with a cognitive endpoint was retrieved; the only human-facing record is a narrative review.",
    },
    "HTR2A": {
        "anchor": "CLM:alphacognition:HTR2A:002",
        "source_id": "SRC:PMID:35217796",
        "design": "rct_crossover",
        "species_key": "human",
        "population": "28 healthy subjects receiving placebo, LSD and psilocybin in a crossover design",
        "facets": ["above_baseline_enhancement"],
        "endpoint": "self-rated subjective and autonomic effects; no objective cognitive performance test capable of showing improvement above baseline",
        "detail": "no retrieved study measured objective cognitive performance above a healthy baseline under 5-HT2A agonism. The measured cognitive null in CLM:alphacognition:HTR2A:003 is separate and IS counter-evidence; this record covers only the enhancement endpoint nobody measured.",
    },
}

TAXA = {"human": "Homo sapiens", "mouse": "Mus musculus"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evidence_item(
    *,
    source_id: str,
    design: str,
    species: str | None,
    population: str,
    endpoint: str,
    endpoint_category: str,
    basis: str,
    date: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "design": design,
        "species": species,
        "population": population,
        "sample_size": {"reported_as": None, "value": None, "unit": None},
        "endpoint": endpoint,
        "endpoint_category": endpoint_category,
        "endpoint_measured": "not_measured_in_protocol",
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
        "evidence_role": "qualifies",
        "extraction": {
            "basis": basis,
            "extracted_by": AGENT,
            "extracted_on": date,
            "content_checked": True,
        },
    }


def gap_shell(
    *,
    claim_id: str,
    statement: str,
    anchor: str,
    obj: str,
    phenotype_class: str,
    species: str | None,
    life_stage: str,
    baseline_context: str,
    evidence: list[dict[str, Any]],
    human_relevance: str,
    alternatives: list[str],
    risks: list[str],
    date: str,
    run_id: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "schema_version": SCHEMA_VERSION,
        "statement": statement,
        "subject": anchor,
        "predicate": "ABOUT",
        "object": obj,
        "claim_type": "evidence_gap",
        "direction": "unclear",
        "context": {
            "species": [species] if species else [],
            "life_stage": life_stage,
            "baseline_context": baseline_context,
            "brain_regions": [],
            "cell_types": [],
        },
        "phenotype_class": phenotype_class,
        "causal_attribution": {
            "basis": "computational_prediction" if claim_id.endswith(":001") else "theoretical_argument",
            "locus_to_gene_resolved": "not_applicable",
            "alternative_explanations": alternatives,
        },
        "evidence": evidence,
        "translation": {
            "adult_relevance": "unknown",
            "healthy_baseline": "unknown",
            "supra_normal": "untested",
            "human_relevance": human_relevance,
            "general_intelligence_relevance": "unknown",
        },
        "uncertainty": {
            "representation": "ordinal_grade",
            "scale": "evidence_strength_v1",
            "level": 0,
            "rationale": (
                "an evidence_gap claim carries no evidential weight for or against any proposition "
                "by construction; level 0 records that the search was performed and the measurement "
                "does not exist"
            ),
            "calibration_status": "uncalibrated_subjective",
        },
        "risks": risks,
        "confounders": [],
        "dependencies": [],
        "status": "active",
        "provenance": {
            "created_by": AGENT,
            "created_on": date,
            "method": "derived_from_claims",
            "run_id": run_id,
            "pipeline": "pipelines/alphacognition/build_coverage_gaps.py",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", default="2026-09-17")
    parser.add_argument("--run-id", default="sprint1-alphacognition-gaps-01")
    args = parser.parse_args(argv)

    human = resolve_species_id("Homo sapiens", offline=True)
    gwas = read_jsonl(INTERIM_DIR / "gwas_catalog_associations.jsonl")
    l2g = read_jsonl(INTERIM_DIR / "opentargets_l2g.jsonl")
    pleio = {r["gene_symbol"]: r for r in read_jsonl(INTERIM_DIR / "gwas_catalog_gene_pleiotropy.jsonl")}

    cognitive_genes = {r["gene_symbol"] for r in gwas if not r["is_educational_attainment"]}
    l2g_cognitive_genes = {
        str(h["symbol"])
        for r in l2g
        if not r.get("is_educational_attainment")
        for h in (r.get("seed_gene_l2g_hits") or [])
    }

    claims: list[dict[str, Any]] = []

    # --- kind A: the genetics sweep found no cognitive signal for this gene ---------------
    for gene in seed_gene_symbols():
        if gene in cognitive_genes or gene in l2g_cognitive_genes:
            continue
        row = pleio.get(gene) or {}
        total = row.get("associations_total")
        other = row.get("distinct_other_traits")
        claims.append(
            gap_shell(
                claim_id=f"CLM:{AGENT.split(':')[1]}:gap.{gene}:001",
                statement=(
                    f"A systematic sweep of GWAS Catalog release 2026-09-13 for {gene} across all 22 "
                    f"queried cognitive-panel traits, and of Open Targets 26.06 locus-to-gene "
                    f"predictions across the same panel, returned no association and no candidate-gene "
                    f"ranking for {gene} on any cognitive-ability trait. The catalogue does record "
                    f"{total} association(s) for this gene symbol across {other} distinct other "
                    f"trait(s), so the gene is not absent from the catalogue — no cognitive endpoint "
                    f"has been measured in relation to it. This is an absence of measurement, not a "
                    f"measured absence of effect."
                ),
                anchor=f"CLM:{AGENT.split(':')[1]}:expr.{gene}:001",
                obj="PHENO:g_factor",
                phenotype_class="g_factor",
                species=human,
                life_stage="adult",
                baseline_context="mixed",
                human_relevance="human_genetic",
                evidence=[
                    evidence_item(
                        source_id=GWAS_RELEASE,
                        design="database_release",
                        species=human,
                        population="GWAS Catalog release 2026-09-13, all catalogued studies",
                        endpoint=(
                            f"queried: mapped_gene={gene} x each of the 22 panel EFO trait ids. "
                            f"No cognitive-ability association record returned."
                        ),
                        endpoint_category="not_applicable",
                        basis="database_record",
                        date=args.date,
                    ),
                    evidence_item(
                        source_id=OT_RELEASE,
                        design="database_release",
                        species=human,
                        population="Open Targets Platform data version 26.06, GWAS credible sets for the 22 panel traits",
                        endpoint=(
                            f"queried: every fine-mapped GWAS credible set for the panel traits; "
                            f"{gene} appears in no l2GPredictions row for a cognitive-panel trait."
                        ),
                        endpoint_category="not_applicable",
                        basis="database_record",
                        date=args.date,
                    ),
                ],
                alternatives=[
                    "the catalogue records only associations that passed a genome-wide threshold, so "
                    "absence here is uninformative about small effects",
                    "positional annotation means a real signal acting through this gene could be "
                    "catalogued under a neighbouring gene instead",
                    "cognitive GWAS are overwhelmingly European-ancestry, so absence in this data is "
                    "absence in one ancestry group",
                ],
                risks=[
                    "read as a null this would be a serious misreading: nothing here was tested and "
                    "found absent; the measurement does not exist",
                    "this record is graph-inert and may never raise any facet's counter_level",
                ],
                date=args.date,
                run_id=args.run_id,
            )
        )

    # --- kind B: the studies that exist did not measure these endpoints ------------------
    for symbol, spec in sorted(LEAD_GAPS.items()):
        species = resolve_species_id(TAXA[spec["species_key"]], offline=True)
        facets = spec["facets"]
        facet_text = (
            "It therefore supplies no measurement behind the level-0 grades on "
            + ", ".join(f"`{f}`" for f in facets)
            + "."
            if facets
            else "It supplies no cognitive measurement of any kind."
        )
        claims.append(
            gap_shell(
                claim_id=f"CLM:{AGENT.split(':')[1]}:gap.{symbol}:002",
                statement=(
                    f"Coverage gap for {symbol}: {spec['detail']} {facet_text} Absence of measurement "
                    f"is not measured absence, and this record asserts no effect and no null."
                ),
                anchor=spec["anchor"],
                obj="PHENO:g_factor",
                phenotype_class="g_factor",
                species=species,
                life_stage="adult",
                baseline_context="mixed",
                human_relevance=(
                    "direct_human_interventional" if spec["species_key"] == "human" else "rodent_only"
                ),
                evidence=[
                    evidence_item(
                        source_id=spec["source_id"],
                        design=spec["design"],
                        species=species,
                        population=spec["population"],
                        endpoint=spec["endpoint"],
                        endpoint_category="not_applicable",
                        basis="abstract",
                        date=args.date,
                    )
                ],
                alternatives=[
                    "this is a statement about what the retrieved studies measured, not about what the "
                    "target does",
                    "the searches run in this session are recorded in evidence/sources/alphacognition.yaml; "
                    "a study this agent did not find would change the picture",
                ],
                risks=[
                    "read as a null this would be a serious misreading",
                    "this record is graph-inert and may never raise any facet's counter_level",
                ],
                date=args.date,
                run_id=args.run_id,
            )
        )

    claims.sort(key=lambda c: c["claim_id"])
    write_yaml_doc(
        OUT_PATH,
        f"""# MACHINE-GENERATED — do not hand-edit.
# Produced by pipelines/alphacognition/build_coverage_gaps.py
#
# claim_type `evidence_gap` (contract §4.1, resolution R5): every record here states that a
# MEASUREMENT DOES NOT EXIST. It is GRAPH-INERT — no biological or intervention edge is
# compiled from it — it asserts no effect and no null, and it may never contribute to any
# facet's counter_level. It exists so that a level-0 facet grade points at a record naming the
# search that was performed and what it did not contain, instead of at an empty list.
#
# Records: {len(claims)}
#   kind A (gap.*:001) — the genetics sweep found no cognitive signal for this gene
#   kind B (gap.*:002) — the studies that do exist did not measure these endpoints
""",
        claims,
    )

    summary = {
        "generated_on": args.date,
        "claims_written": len(claims),
        "kind_a_genetics_sweep_gaps": sum(1 for c in claims if c["claim_id"].endswith(":001")),
        "kind_b_lead_atlas_gaps": sum(1 for c in claims if c["claim_id"].endswith(":002")),
        "genes_with_no_cognitive_genetic_signal": sorted(
            c["claim_id"].split(".")[1].split(":")[0] for c in claims if c["claim_id"].endswith(":001")
        ),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
