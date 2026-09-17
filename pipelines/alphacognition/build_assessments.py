#!/usr/bin/env python3
"""Generate the four genetics facet assessments for all 27 seed targets.

Why these facets are generated rather than hand-written
-------------------------------------------------------
`human_genetic_association`, `causal_gene_attribution`, `human_phenotype_specificity` and
`adult_expression_and_timing` are judgements about a *systematic* evidence sweep: the whole
seed set against the whole cognitive trait panel, plus one expression atlas. A hand-written
grade per target would be 27 inconsistent applications of the same rule. The rule is
therefore written down once, here, and applied deterministically, so it can be audited and
re-run. The rationale strings quote the actual counts each target's grade came from.

This does NOT make the grades objective. The mapping from evidence pattern to ordinal level
is a curatorial decision by agent:alphacognition, taken against the level semantics in
docs/DATA_CONTRACT.md §5.3, and it is stated in full in the generated files and in
docs/ALPHACOGNITION_ARCHITECTURE.md. The lead-atlas facets for the six targets this agent
leads are NOT generated: they are hand-written into the same files by a merge step, because
they rest on individually-read papers.

Level rules (evidence_strength_v1 semantics in brackets)
--------------------------------------------------------
human_genetic_association — proposition: this gene is associated with human cognitive ability.
  0  [searched, nothing found]      no association on any panel trait, and none on any other trait
  1  [weak/indirect]                associations only on educational-attainment or literacy traits,
                                    or only clinical-proxy traits, or only Open Targets L2G
                                    candidacy with no catalogued genome-wide association
  2  [one human study, relevant]    >=1 catalogued association on a single-domain cognitive trait
                                    (processing speed, memory, executive function)
  3  [one human genetic result,     >=1 catalogued association on a g_factor or fluid_reasoning
      directly relevant endpoint]   trait
  4  never awarded in v0.1          would require replicated human evidence CONSISTENT IN
                                    DIRECTION; the catalogue's `beta` strings are heterogeneous
                                    free text and effect alleles are frequently reported as "?",
                                    so direction consistency is not establishable from this data.

causal_gene_attribution — proposition: the human signal is attributable to THIS gene.
  0  no human cognitive-trait signal exists, so there is nothing to attribute
  1  a signal exists but attribution rests on positional (nearest-gene) annotation only
  2  Open Targets' L2G model ranks this gene at >=1 fine-mapped credible set for a
     cognitive-panel trait (partial, model-based, with competing candidates at the locus)
  3  L2G candidacy PLUS a molecular-QTL colocalisation for this same gene at the same locus
  4  never awarded in v0.1 (would need an independently replicated gene-resolved assignment,
     e.g. rare-variant burden or Mendelian randomisation with this gene as the exposure)
  Cap: if the only L2G candidacy is on educational-attainment traits, the level cannot exceed 1,
  because EA is not an intelligence endpoint.

human_phenotype_specificity — proposition: the human signal picks out cognitive ability rather
than being a broadly pleiotropic locus or an education proxy.
  0  no catalogued association for this gene at all
  1  the gene has catalogued associations but none on a cognitive-panel trait, OR its only
     panel associations are educational-attainment/literacy
  2  >=1 cognitive-panel association AND the gene also carries associations with traits outside
     the panel, so cognition-specificity is qualified
  3  >=1 cognitive-panel association on a g_factor/fluid_reasoning trait AND no catalogued
     association outside the cognitive/EA panel
  4  never awarded in v0.1

adult_expression_and_timing — proposition: the gene is expressed in the adult human brain and
its cognitive relevance is not confined to development.
  0  no expression data retrieved
  1  GTEx brain data exists but the transcript is not detected in every sampled brain region
  2  detected in all sampled adult human brain regions (GTEx v8, adult post-mortem donors)
  3  the above PLUS a referenced claim showing an adult-onset effect on cognition in humans
  4  never awarded in v0.1: adult human brain CELL-TYPE resolution was not reachable
     (deferred to docs/TASK_DAG.yaml Q003), so the timing proposition cannot be strongly met.

Counter-levels use the same scale and are graded only from evidence this sweep can see.
Where contradicting evidence of a given kind was not systematically searched, that is stated
in `counter_rationale` and `limiting_factor` rather than represented as a 0 without comment.

Usage
-----
    python pipelines/alphacognition/build_assessments.py
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
    GENERATED_DIR,
    REPO_ROOT,
    load_panel,
    load_seed_targets,
)
from _provenance import INTERIM_DIR  # type: ignore[import-not-found]  # noqa: E402

ASSESS_DIR = REPO_ROOT / "atlases" / "alphacognition" / "assessments"
LEAD_FACETS_PATH = REPO_ROOT / "atlases" / "alphacognition" / "lead_atlas_facets.yaml"
GWAS_TABLE = INTERIM_DIR / "gwas_catalog_associations.jsonl"
L2G_TABLE = INTERIM_DIR / "opentargets_l2g.jsonl"
EXPR_TABLE = INTERIM_DIR / "adult_brain_expression.jsonl"
PLEIO_TABLE = INTERIM_DIR / "gwas_catalog_gene_pleiotropy.jsonl"
SUMMARY_PATH = GENERATED_DIR / "assessment_summary.json"

RUBRIC = "facet_rubric_v0_1"
AGENT = "agent:alphacognition"

DIRECTLY_RELEVANT = {"g_factor", "fluid_reasoning"}
SINGLE_DOMAIN = {"processing_speed", "episodic_memory", "working_memory", "executive_function"}
PROXY = {"educational_attainment", "clinical_cognitive_composite"}

# A level-0 grade means SEARCHED AND FOUND NOTHING, so the schema asks for accountability
# rather than a citation: what was searched, at what scope, and what would have counted.
SEARCH_BASIS = {
    "human_genetic_association": (
        "Searched: GWAS Catalog REST v2 release 2026-09-13, every gene symbol of this target x "
        "each of the 22 queried EFO trait ids in atlases/alphacognition/cognitive_trait_panel.yaml "
        "(682 gene-trait pairs across the seed set), plus the same gene unfiltered by trait; plus "
        "Open Targets 26.06 locus-to-gene predictions over every fine-mapped GWAS credible set for "
        "those 22 traits (716 studies, 13,730 credible sets). A hit would have been one catalogued "
        "genome-wide association record with this gene in `mapped_genes` for a panel trait."
    ),
    "causal_gene_attribution": (
        "Searched: Open Targets 26.06 trait -> studies(diseaseIds:) -> credibleSets(studyTypes:[gwas]) "
        "-> l2GPredictions and colocalisation, over all 22 panel traits (716 GWAS studies, 13,730 "
        "credible sets), plus every GWAS Catalog association for this gene. A hit would have been "
        "this gene appearing in an l2GPredictions row for a cognitive-panel trait, or a "
        "molecular-QTL colocalisation for this gene at such a locus."
    ),
    "human_phenotype_specificity": (
        "Searched: every catalogued GWAS Catalog association for this gene symbol, unfiltered by "
        "trait (GET /v2/associations?mapped_gene=SYMBOL, release 2026-09-13), which supplies the "
        "denominator, partitioned against the 22-trait cognitive panel. A hit would have been at "
        "least one association with a cognitive-panel trait."
    ),
    "adult_expression_and_timing": (
        "Searched: GTEx Portal API v2 median gene expression, dataset gtex_v8, all 54 tissues "
        "including 13 brain regions, plus Open Targets 26.06 baselineExpression. A hit would have "
        "been detectable median transcript abundance in adult human brain tissue."
    ),
    "mechanistic_causal_perturbation": (
        "Searched: PubMed for perturbation studies of this target with a cognitive or plasticity "
        "readout (knockout, knockdown, overexpression, pharmacological and inducible designs). A "
        "hit would have been a study in which perturbing the target changed a cognition-relevant "
        "measure. Search strings are recorded per source in evidence/sources/alphacognition.yaml."
    ),
    "adult_onset_perturbation": (
        "Searched: PubMed for perturbations initiated in adulthood (adult-inducible genetic, "
        "pharmacological, acute circuit) for this target. A hit would have been a perturbation "
        "begun after development with a cognitive readout."
    ),
    "above_baseline_enhancement": (
        "Searched: PubMed for studies of this target reporting performance ABOVE an intact healthy "
        "baseline, in any species. A hit would have been a healthy-baseline arm improving on a "
        "cognitive measure; a deficit-state or disease-model improvement would NOT have counted."
    ),
    "transfer_breadth": (
        "Searched: the endpoint lists of every study retrieved for this target, for a second "
        "cognitive domain or an explicit transfer measure. A hit would have been improvement on "
        "two or more distinct cognitive domains, or on an untrained real-world endpoint."
    ),
    "dose_response_knowledge": (
        "Searched: the retrieved studies for a dose series, an exposure-response relation or an "
        "expression-level-response relation with a cognitive readout. A hit would have been three "
        "or more exposure levels with a cognitive endpoint, or an explicitly characterised "
        "response shape."
    ),
    "human_intervention_evidence": (
        "Searched: PubMed for human interventional studies of this target with a cognitive "
        "endpoint, and ClinicalTrials.gov API v2 for registered trials. A hit would have been a "
        "randomised or open-label human study reporting a cognitive endpoint. A trial that "
        "measured no cognitive endpoint is a coverage gap, not a hit and not a miss (R5)."
    ),
}

ANCESTRY_LIMIT = (
    "cognitive GWAS discovery samples are overwhelmingly European-ancestry, so neither the "
    "association nor any locus-to-gene assignment built on it is established as transportable"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def gene_members() -> dict[str, list[str]]:
    """target_id -> the gene symbols whose evidence it inherits."""
    out: dict[str, list[str]] = {}
    for target in load_seed_targets():
        symbol = str(target["symbol"])
        members = [str(m) for m in (target.get("member_genes") or [])]
        out[str(target["target_id"])] = members or [symbol]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", default="2026-09-17")
    args = parser.parse_args(argv)

    panel = {t["efo_id"]: t for t in load_panel()}
    gwas = read_jsonl(GWAS_TABLE)
    l2g = read_jsonl(L2G_TABLE)
    expr = {r["gene_symbol"]: r for r in read_jsonl(EXPR_TABLE)}
    pleio = {r["gene_symbol"]: r for r in read_jsonl(PLEIO_TABLE)}
    lead = yaml.safe_load(LEAD_FACETS_PATH.read_text(encoding="utf-8")) if LEAD_FACETS_PATH.exists() else {}

    gwas_by_gene: dict[str, list[dict[str, Any]]] = {}
    for row in gwas:
        gwas_by_gene.setdefault(str(row["gene_symbol"]), []).append(row)

    l2g_by_gene: dict[str, list[dict[str, Any]]] = {}
    for row in l2g:
        for hit in row.get("seed_gene_l2g_hits") or []:
            l2g_by_gene.setdefault(str(hit["symbol"]), []).append(row)

    # ---- index the generated claim ids by gene, straight out of the claim files ----
    def index_claims() -> dict[str, dict[str, list[str]]]:
        idx: dict[str, dict[str, list[str]]] = {
            "gwas": {}, "gwas_cognitive": {}, "l2g": {}, "l2g_cognitive": {}, "expr": {},
            "gap": {}, "gap_lead": {}
        }
        files = {
            "gap": REPO_ROOT / "evidence/claims/alphacognition/coverage_gaps.yaml",
            "gwas": REPO_ROOT / "evidence/claims/alphacognition/gwas_catalog_derived.yaml",
            "l2g": REPO_ROOT / "evidence/claims/alphacognition/opentargets_l2g_derived.yaml",
            "expr": REPO_ROOT / "evidence/claims/alphacognition/expression_derived.yaml",
        }
        for kind, path in files.items():
            if not path.exists():
                continue
            for claim in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
                if kind == "gap":
                    # coverage-gap claims are anchored on another claim, so the gene is in the id
                    local = str(claim["claim_id"]).split(":")[2]           # gap.<SYMBOL>
                    gene = local.split(".", 1)[1]
                    bucket = "gap_lead" if str(claim["claim_id"]).endswith(":002") else "gap"
                    idx[bucket].setdefault(gene, []).append(str(claim["claim_id"]))
                    continue
                gene = str(claim["subject"]).split(":", 1)[1]
                idx[kind].setdefault(gene, []).append(str(claim["claim_id"]))
                if kind in {"gwas", "l2g"} and claim.get("phenotype_class") != "educational_attainment":
                    idx[f"{kind}_cognitive"].setdefault(gene, []).append(str(claim["claim_id"]))
        return idx

    claim_index = index_claims()
    members = gene_members()
    targets = {str(t["target_id"]): t for t in load_seed_targets()}
    distribution: dict[str, dict[str, int]] = {}
    written: list[str] = []

    for target_id, target in sorted(targets.items()):
        symbol = str(target["symbol"])
        genes = members[target_id]

        # ---- evidence counts -------------------------------------------------
        rows = [r for g in genes for r in gwas_by_gene.get(g, [])]
        cognitive = [r for r in rows if not r["is_educational_attainment"]]
        ea = [r for r in rows if r["is_educational_attainment"]]
        direct = [r for r in cognitive if r["phenotype_class"] in DIRECTLY_RELEVANT]
        domain = [r for r in cognitive if r["phenotype_class"] in SINGLE_DOMAIN]
        proxy_only_rows = [r for r in cognitive if r["phenotype_class"] in PROXY]
        pmids = sorted({r["pubmed_id"] for r in rows if r["pubmed_id"]})
        cognitive_pmids = sorted({r["pubmed_id"] for r in cognitive if r["pubmed_id"]})
        traits_hit = sorted({r["efo_label"] for r in cognitive})

        l2g_rows = [r for g in genes for r in l2g_by_gene.get(g, [])]
        l2g_cognitive = [r for r in l2g_rows if not r.get("is_educational_attainment")]
        l2g_ea = [r for r in l2g_rows if r.get("is_educational_attainment")]
        coloc_rows = [
            r
            for r in l2g_cognitive
            for g in genes
            if (r.get("seed_gene_qtl_colocalisations") or {}).get(g)
        ]
        competitors = sorted(
            {
                str(c["symbol"])
                for r in l2g_cognitive
                for c in (r.get("top_l2g_genes") or [])
                if c.get("symbol") and c["symbol"] not in genes
            }
        )

        pleio_rows = [pleio.get(g) for g in genes if pleio.get(g)]
        other_trait_assoc = sum(int(p["associations_other_traits"]) for p in pleio_rows) if pleio_rows else None
        total_assoc = sum(int(p["associations_total"]) for p in pleio_rows) if pleio_rows else None
        distinct_other = sum(int(p["distinct_other_traits"]) for p in pleio_rows) if pleio_rows else None

        expr_rows = [expr.get(g) for g in genes if expr.get(g)]
        brain_regions = max((int(e["brain_regions_reported"]) for e in expr_rows), default=0)
        detected_all = bool(expr_rows) and all(
            all((b["median_as_reported"] or 0) > 0 for b in e["brain_regions"]) for e in expr_rows
        )

        # Claim references are READ BACK from the generated claim files, never reconstructed
        # from a numbering convention, so a reference can never dangle (contract V4).
        gwas_claim_refs = sorted({c for g in genes for c in claim_index["gwas"].get(g, [])})
        l2g_claim_refs = sorted({c for g in genes for c in claim_index["l2g"].get(g, [])})
        l2g_cognitive_claim_refs = sorted({c for g in genes for c in claim_index["l2g_cognitive"].get(g, [])})
        expr_claim_refs = sorted({c for g in genes for c in claim_index["expr"].get(g, [])})
        gwas_cognitive_claim_refs = sorted({c for g in genes for c in claim_index["gwas_cognitive"].get(g, [])})
        # A level-0 grade means "searched, nothing found". It cites the graph-inert evidence_gap
        # record that names the search and what it did not contain (R5), never an empty list.
        gap_claim_refs = sorted({c for g in genes for c in claim_index["gap"].get(g, [])})
        gap_lead_refs = sorted(claim_index["gap_lead"].get(symbol, []))

        def with_fallback(*candidates: list[str]) -> list[str]:
            for candidate in candidates:
                if candidate:
                    return candidate
            return []

        # ---- facet 1: human_genetic_association ------------------------------
        if not rows and not l2g_rows and not (total_assoc or 0):
            hga_level, hga_reason = 0, (
                "searched: every seed gene x all 22 queried panel traits in GWAS Catalog release "
                "2026-09-13, plus Open Targets 26.06 locus-to-gene predictions across the same "
                "panel, plus all catalogued traits for the gene. Nothing found."
            )
        elif direct:
            hga_level, hga_reason = 3, (
                f"{len(direct)} catalogued genome-wide association record(s) on a g_factor or "
                f"fluid_reasoning trait ({', '.join(sorted({r['efo_label'] for r in direct}))}) "
                f"across {len(sorted({r['pubmed_id'] for r in direct if r['pubmed_id']}))} "
                f"publication(s); one human genetic result with a directly relevant endpoint"
            )
        elif domain:
            hga_level, hga_reason = 2, (
                f"{len(domain)} catalogued association record(s) on single-domain cognitive traits "
                f"({', '.join(sorted({r['efo_label'] for r in domain}))}); a relevant but not "
                f"directly relevant human endpoint"
            )
        elif proxy_only_rows or ea or l2g_rows or (total_assoc or 0):
            bits = []
            if ea:
                bits.append(f"{len(ea)} educational-attainment/literacy association(s)")
            if proxy_only_rows:
                bits.append(f"{len(proxy_only_rows)} clinical-proxy association(s)")
            if l2g_rows:
                bits.append(
                    f"locus-to-gene candidacy at {len(l2g_rows)} credible set(s) "
                    f"({len(l2g_cognitive)} on cognitive traits, {len(l2g_ea)} on educational attainment)"
                )
            if not rows and (total_assoc or 0):
                bits.append(f"{total_assoc} catalogued association(s) on non-panel traits only")
            hga_level, hga_reason = 1, (
                "weak or indirect only: " + "; ".join(bits) + ". No catalogued genome-wide "
                "association on a cognitive-ability trait."
            )
        else:
            hga_level, hga_reason = 0, "searched, nothing found"

        hga_claims = with_fallback(
            (gwas_cognitive_claim_refs or gwas_claim_refs) + l2g_claim_refs, gap_claim_refs
        )

        # ---- facet 2: causal_gene_attribution --------------------------------
        if not cognitive and not l2g_cognitive:
            cga_level, cga_reason = 0, (
                "no cognitive-trait human genetic signal was found for this gene, so there is no "
                "attribution question to answer yet"
            )
            cga_limit = "nothing to attribute"
        elif coloc_rows:
            cga_level, cga_reason = 3, (
                f"Open Targets L2G candidacy at {len(l2g_cognitive)} cognitive-trait credible set(s) "
                f"with molecular-QTL colocalisation for this gene at {len(coloc_rows)} of them"
            )
            cga_limit = "colocalisation supports the gene assignment, not a causal effect on the trait"
        elif l2g_cognitive:
            cga_level, cga_reason = 2, (
                f"Open Targets' locus-to-gene model (data version 26.06) ranks this gene among the "
                f"candidates at {len(l2g_cognitive)} fine-mapped credible set(s) for cognitive-panel "
                f"traits, with {len(competitors)} competing candidate gene(s) at the same loci "
                f"({', '.join(competitors[:8])}{'...' if len(competitors) > 8 else ''}); no "
                f"molecular-QTL colocalisation for this gene was found at those loci"
            )
            cga_limit = (
                "attribution is a published statistical model's output with competing candidates and "
                "no QTL corroboration; not a demonstrated gene-level effect"
            )
        elif l2g_ea and not cognitive:
            cga_level, cga_reason = 1, (
                f"locus-to-gene candidacy exists at {len(l2g_ea)} credible set(s) but only for "
                f"educational-attainment traits, which are not intelligence endpoints, so the level "
                f"is capped at 1"
            )
            cga_limit = "educational attainment is not an intelligence endpoint"
        else:
            cga_level, cga_reason = 1, (
                f"{len(cognitive)} cognitive-trait association record(s) exist, but attribution to "
                f"this gene rests entirely on the GWAS Catalog's positional (nearest-gene) "
                f"annotation: locus_to_gene_resolved is 'no' on every one of them, and no "
                f"fine-mapped credible set for a cognitive trait ranks this gene"
            )
            cga_limit = "a locus is not a gene; no fine-mapping or colocalisation evidence for this gene"

        # ---- facet 3: human_phenotype_specificity ----------------------------
        if total_assoc in (None, 0):
            hps_level, hps_reason = 0, (
                "searched: all catalogued GWAS Catalog associations for this gene symbol "
                "(unfiltered by trait). None found, so there is no phenotype profile to assess."
            )
        elif not cognitive:
            hps_level, hps_reason = 1, (
                f"the gene carries {total_assoc} catalogued association(s) across "
                f"{distinct_other} distinct non-cognitive trait(s) and none on a cognitive-panel "
                f"trait; whatever this locus does, the catalogue does not connect it to cognition"
            )
        elif direct and not other_trait_assoc:
            hps_level, hps_reason = 3, (
                f"all {total_assoc} catalogued association(s) for this gene fall inside the "
                f"cognitive/educational panel, including {len(direct)} on a directly relevant "
                f"cognitive-ability trait; the catalogued signal is cognition-specific"
            )
        elif ea and not direct and not domain:
            hps_level, hps_reason = 1, (
                f"the gene's only panel associations are educational-attainment or literacy "
                f"({len(ea)} record(s)), alongside {other_trait_assoc} non-panel association(s)"
            )
        else:
            hps_level, hps_reason = 2, (
                f"{len(cognitive)} cognitive-panel association(s) ({len(direct)} directly relevant, "
                f"{len(domain)} single-domain) alongside {other_trait_assoc} association(s) with "
                f"{distinct_other} distinct trait(s) outside the panel; cognition-specificity is "
                f"qualified by that pleiotropy"
            )

        # ---- facet 4: adult_expression_and_timing ----------------------------
        adult_human_claim = (lead.get(symbol) or {}).get("adult_human_onset_claim_refs") or []
        if not expr_rows:
            aet_level, aet_reason = 0, "no expression data was retrieved for this gene"
        elif not detected_all:
            aet_level, aet_reason = 1, (
                f"GTEx v8 reports {brain_regions} brain region(s) for this gene but the transcript "
                f"is not detected above zero median in all of them"
            )
        elif adult_human_claim:
            aet_level, aet_reason = 3, (
                f"detected in all {brain_regions} sampled adult human brain regions (GTEx v8, adult "
                f"post-mortem donors), AND an adult-onset human effect on a cognitive endpoint is "
                f"referenced ({', '.join(adult_human_claim)})"
            )
        else:
            aet_level, aet_reason = 2, (
                f"detected in all {brain_regions} sampled adult human brain regions (GTEx v8, adult "
                f"post-mortem donors); direct human adult tissue measurement, but bulk-tissue "
                f"resolution and no evidence that the gene's cognitive relevance extends into "
                f"adulthood"
            )

        dev_counter = (lead.get(symbol) or {}).get("developmental_counter") or {}

        facets: list[dict[str, Any]] = [
            {
                "facet": "human_genetic_association",
                "assessment_status": "assessed",
                "level": hga_level,
                "rationale": hga_reason,
                "claim_refs": hga_claims,
                "counter_level": 0,
                "counter_rationale": (
                    "No study reporting a null or opposite-direction association for this gene on a "
                    "panel trait was found by this sweep. That is a property of the sweep, not of the "
                    "literature: the GWAS Catalog records associations that passed a significance "
                    "threshold and does not record non-associations, so absence of a catalogued "
                    "negative is uninformative and is recorded as 0 for that reason."
                ),
                "counter_claim_refs": [],
                "limiting_factor": (
                    "level 4 is unreachable from this evidence: the catalogue's `beta` field is "
                    f"heterogeneous free text and effect alleles are often reported as '?', so "
                    f"direction consistency across studies cannot be established. "
                    f"{ANCESTRY_LIMIT}."
                ),
            },
            {
                "facet": "causal_gene_attribution",
                "assessment_status": "assessed",
                "level": cga_level,
                "rationale": cga_reason,
                "claim_refs": with_fallback(
                    l2g_cognitive_claim_refs + gwas_cognitive_claim_refs,
                    l2g_claim_refs + gwas_claim_refs,
                    gap_claim_refs,
                ),
                "counter_level": 2 if competitors else 0,
                "counter_rationale": (
                    f"{len(competitors)} other gene(s) are ranked as candidates at the same "
                    f"cognitive-trait credible set(s), which is direct evidence against a confident "
                    f"assignment to this gene"
                )
                if competitors
                else (
                    "no competing gene assignment was found, because no fine-mapped cognitive-trait "
                    "credible set implicates this gene at all"
                ),
                "counter_claim_refs": l2g_cognitive_claim_refs if competitors else [],
                "limiting_factor": cga_limit,
            },
            {
                "facet": "human_phenotype_specificity",
                "assessment_status": "assessed",
                "level": hps_level,
                "rationale": hps_reason,
                "claim_refs": with_fallback(gwas_claim_refs, l2g_claim_refs, gap_claim_refs),
                "counter_level": 2 if (other_trait_assoc or 0) and cognitive else 0,
                "counter_rationale": (
                    f"the same positional locus carries {other_trait_assoc} catalogued association(s) "
                    f"with {distinct_other} distinct non-cognitive trait(s), which argues against "
                    f"reading the cognitive hit as specific to this gene's cognitive function"
                )
                if (other_trait_assoc or 0) and cognitive
                else "no contradicting pleiotropy evidence applies at this level",
                "counter_claim_refs": [],
                "limiting_factor": (
                    "specificity is assessed from positional annotation, so 'this gene is pleiotropic' "
                    "and 'this locus is gene-dense' are not separated. Mendelian randomisation and "
                    "pan-phenome gene-level testing were not run in v0.1."
                ),
            },
            {
                "facet": "adult_expression_and_timing",
                "assessment_status": "assessed",
                "level": aet_level,
                "rationale": aet_reason,
                "claim_refs": expr_claim_refs + list(adult_human_claim),
                "counter_level": int(dev_counter.get("level", 0)),
                "counter_rationale": dev_counter.get(
                    "rationale",
                    "no evidence that this gene's action is confined to development was retrieved. "
                    "Developmental-restriction evidence was NOT systematically searched for this "
                    "target: no human developmental transcriptome (BrainSpan/PsychENCODE) was "
                    "ingested in v0.1, so this 0 means 'not found by the sweep that was run'.",
                ),
                "counter_claim_refs": list(dev_counter.get("claim_refs", [])),
                "limiting_factor": (
                    "adult human brain CELL-TYPE resolution is unavailable in this release and is "
                    "deferred to docs/TASK_DAG.yaml Q003; developmental timing was not ingested from "
                    "any atlas. Level 4 is therefore unreachable for every target in v0.1."
                ),
            },
        ]

        # lead-atlas facets, hand-written, merged in for the six targets this agent leads.
        # A hand-written level-0 grade with no claim to cite gets the target's kind-B
        # coverage-gap record, which names the study whose protocol did not measure the endpoint.
        for facet in (lead.get(symbol) or {}).get("facets") or []:
            facet = dict(facet)
            if facet.get("assessment_status") == "assessed" and not facet.get("claim_refs"):
                facet["claim_refs"] = list(gap_lead_refs)
            facets.append(facet)

        for facet in facets:
            if facet.get("level") == 0 and not facet.get("search_basis"):
                facet["search_basis"] = SEARCH_BASIS[str(facet["facet"])]
            # Contradicting evidence must be IDENTIFIED, not merely described. Where this sweep
            # produced no citable counter-claim, the point becomes a limiting_factor and the
            # counter_level returns to 0 rather than resting on uncited evidence.
            if (facet.get("counter_level") or 0) >= 1 and not facet.get("counter_claim_refs"):
                extra = str(facet.get("counter_rationale") or "").strip()
                facet["counter_level"] = 0
                facet["counter_rationale"] = (
                    "No citable contradicting claim exists in this atlas for this facet. The "
                    "observation that would have argued against it is recorded in limiting_factor "
                    "instead, because a counter-grade may not rest on evidence no record identifies."
                )
                facet["counter_claim_refs"] = []
                if extra:
                    facet["limiting_factor"] = (
                        str(facet.get("limiting_factor") or "").rstrip(". ")
                        + ". Uncited observation that would argue against this facet: "
                        + extra
                    )
            distribution.setdefault(str(facet["facet"]), {})
            key = "not_assessed" if facet["level"] is None else f"level_{facet['level']}"
            distribution[facet["facet"]][key] = distribution[facet["facet"]].get(key, 0) + 1

        # schemas/assessment.schema.json sets additionalProperties: false and has no slot for
        # per-target evidence counts, and rule V9 rejects bare numeric fields anyway. The counts
        # the grades were computed from therefore go into `notes` as prose: they stay visible and
        # auditable without pretending to be structured numeric data this project computed.
        lead_facets = (lead.get(symbol) or {}).get("facets") or []
        owner = str(target.get("lead_atlas", ""))
        not_owned = (
            []
            if lead_facets
            else [
                "mechanistic_causal_perturbation",
                "adult_onset_perturbation",
                "above_baseline_enhancement",
                "transfer_breadth",
                "dose_response_knowledge",
                "human_intervention_evidence",
            ]
        )
        notes = (
            f"Evidence basis for the four genetics facets. Genes covered by this target: "
            f"{', '.join(genes)}. GWAS Catalog release 2026-09-13, {len(panel)} panel terms of "
            f"which 22 queried; Open Targets data version 26.06; GTEx dataset gtex_v8. "
            f"Association records for this target: {len(rows)} total, of which {len(cognitive)} on "
            f"cognitive-panel traits ({len(direct)} on a g_factor/fluid_reasoning trait, "
            f"{len(domain)} single-domain) and {len(ea)} on educational-attainment or literacy "
            f"traits, across {len(pmids)} distinct publications ({len(cognitive_pmids)} for the "
            f"cognitive associations). Cognitive traits hit: "
            f"{', '.join(traits_hit) if traits_hit else 'none'}. "
            f"Fine-mapped credible sets in which Open Targets' L2G model ranks this gene: "
            f"{len(l2g_rows)} in total, {len(l2g_cognitive)} on cognitive-panel traits, with "
            f"{len(coloc_rows)} molecular-QTL colocalisations for this gene at those loci and "
            f"{len(competitors)} competing candidate gene(s) there"
            + (f" ({', '.join(competitors)})" if competitors else "")
            + f". Unfiltered GWAS Catalog sweep for this gene symbol: {total_assoc} catalogued "
            f"association(s) in total, {other_trait_assoc} of them with traits outside the "
            f"cognitive/educational panel, spanning {distinct_other} distinct such trait(s). "
            f"GTEx reports {brain_regions} brain region(s); detected above zero median in all of "
            f"them: {detected_all}. Adult brain cell-type resolution was not available in this "
            f"release and is deferred to docs/TASK_DAG.yaml Q003. "
            f"The level rules applied here are in pipelines/alphacognition/build_assessments.py; "
            f"lead-atlas facets for this target are "
            + ("hand-written in atlases/alphacognition/lead_atlas_facets.yaml."
               if lead_facets else f"owned by agent:{owner} and are not graded here.")
        )

        doc = {
            "target_id": target_id,
            "schema_version": "0.1.0",
            "assessed_by": AGENT,
            "assessed_on": args.date,
            "rubric": RUBRIC,
            "scale": "evidence_strength_v1",
            "facets": facets,
            "facets_not_owned_by_this_agent": not_owned,
            "notes": " ".join(notes.split()),
            "provenance": {
                "created_by": AGENT,
                "created_on": args.date,
                "method": "derived_from_claims",
                "pipeline": "pipelines/alphacognition/build_assessments.py",
                "run_id": "sprint1-alphacognition-facets-01",
            },
        }
        ASSESS_DIR.mkdir(parents=True, exist_ok=True)
        header = (
            "# Facet assessment — generated file.\n"
            "# The four genetics facets are produced deterministically by\n"
            "# pipelines/alphacognition/build_assessments.py from the derived tables under\n"
            "# data/interim/; the level rules are in that script's docstring. Lead-atlas facets, where\n"
            "# present, are hand-written in atlases/alphacognition/lead_atlas_facets.yaml and merged in.\n"
            "# Re-run the script rather than editing this file.\n"
        )
        (ASSESS_DIR / f"{symbol}.yaml").write_text(
            header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8"
        )
        written.append(symbol)

    summary = {
        "generated_on": args.date,
        "targets_assessed": len(written),
        "facet_level_distribution": distribution,
        "gwas_rows_in_table": len(gwas),
        "l2g_rows_in_table": len(l2g),
        "expression_rows_in_table": len(expr),
        "pleiotropy_rows_in_table": len(pleio),
        "lead_atlas_facet_targets": sorted(k for k, v in (lead or {}).items() if (v or {}).get("facets")),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
