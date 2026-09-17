# API recipes (verified against live endpoints on 2026-09-17)

Working query patterns for the public APIs this project depends on. Every pattern
below was executed successfully from this machine on 2026-09-17; the notes record what
the response actually contained, not what the documentation promises.

Use these instead of improvising, and snapshot every response via
`scripts/_provenance.write_snapshot` so the result is reproducible offline.

---

## 1. HGNC — gene identifiers (authority for symbols)

```
GET https://rest.genenames.org/fetch/symbol/{SYMBOL}      Accept: application/json
GET https://rest.genenames.org/search/alias_symbol/{S}+OR+prev_symbol/{S}
```
Returns `response.docs[0]` with `hgnc_id`, `ensembl_gene_id`, `uniprot_ids`,
`entrez_id`, `locus_type`, `mane_select`. Already wrapped by
`scripts/fetch_gene_identifiers.py`; the resolved index is
`data/interim/gene_identifiers.jsonl` (31/31 seed symbols approved).

## 2. NCBI E-utilities — citation verification and taxonomy

```
GET /entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=PMID1,PMID2,...   (≤200 ids)
GET /entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={DOI}[DOI]
GET /entrez/eutils/esearch.fcgi?db=taxonomy&retmode=json&term={species+name}
GET /entrez/eutils/esummary.fcgi?db=taxonomy&retmode=json&id={taxid}
```
Base `https://eutils.ncbi.nlm.nih.gov`. Always send `tool=intelligence-blueprint`;
`api_key` from `NCBI_API_KEY` raises the limit from 3/s to 10/s. An invalid PMID comes
back as a record containing `error`, with an empty title — that is how fabricated
identifiers are caught. Retraction shows up in `pubtype` as `Retracted Publication`.
Wrapped by `scripts/fetch_source_metadata.py`.

**Species taxids must be resolved this way, never from memory** (contract §1.1).

## 3. ClinicalTrials.gov API v2 — trials, including the failed ones

```
GET https://clinicaltrials.gov/api/v2/studies/{NCT_ID}
GET https://clinicaltrials.gov/api/v2/studies?query.intr={drug}&query.cond={condition}
    &filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED&pageSize=50
```
Useful fields: `protocolSection.identificationModule.{nctId,briefTitle,officialTitle}`,
`statusModule.{overallStatus,whyStopped,startDateStruct}`,
`designModule.{phases,enrollmentInfo.count}`, `outcomesModule`,
`sponsorCollaboratorsModule.leadSponsor.name`, and `resultsSection` when results were
posted. `whyStopped` is often the most informative field in the whole record for a
red-team audit.

## 4. GWAS Catalog REST API v2 — associations by gene and trait

```
GET https://www.ebi.ac.uk/gwas/rest/api/v2/metadata
GET https://www.ebi.ac.uk/gwas/rest/api/v2/associations?mapped_gene={SYMBOL}&efo_id={EFO}&size=50
GET https://www.ebi.ac.uk/gwas/rest/api/v2/associations?mapped_gene={SYMBOL}&size=50
```
`/metadata` reports the data release (2026-09-13 at time of writing) — record it as the
`SRC:DB:gwas_catalog:{release}` source. Association rows carry `accession_id`
(GCST), `pubmed_id`, `first_author`, `p_value`, `beta` as a string such as
`"4.76 z-score increase"`, `efo_traits[]`, `reported_trait[]`, `mapped_genes[]`,
`snp_effect_allele[]`, `risk_frequency`, `ci_lower/ci_upper`.

**Two traps:**
* `mapped_genes` is **positional mapping**, not a causal gene. Any claim built from it
  must use `causal_attribution.basis: gwas_association_only` and
  `locus_to_gene_resolved: no`.
* `reported_trait` distinguishes "General cognitive ability" from "Educational
  attainment". Keep them apart (`phenotype_class`), always.

Verified example: `mapped_gene=GRIN2B&efo_id=EFO_0004337` returns 1 association
(GCST006269, PMID 29844566, Davies G, reported trait "General cognitive ability").

## 5. Open Targets Platform GraphQL — fine mapping, coloc, tractability, safety

Endpoint: `POST https://api.platform.opentargets.org/api/v4/graphql`
(`Content-Type: application/json`, body `{"query": ..., "variables": ...}`).
Always capture `meta { apiVersion { x y z } dataVersion { year month iteration } }`
alongside the data so the snapshot is attributable to a data release.

### 5.1 Target annotations (tractability, safety, probes)

```graphql
query T($id: String!) {
  target(ensemblId: $id) {
    approvedSymbol biotype
    tractability { modality label value }
    safetyLiabilities { event eventId datasource literature }
    chemicalProbes { id drugId isHighQuality probeMinerScore }
    mousePhenotypes { modelPhenotypeLabel targetInModel }
    baselineExpression(page: {index: 0, size: 100}) { count }
    prioritisation { items { key value } }
  }
}
```
Confirmed responses: `GABRA5` → tractability `SM/Approved Drug`,
`SM/Structure with Ligand`, `SM/High-Quality Ligand`, `SM/Druggable Family`;
`safetyLiabilities` including `decreased memory` and `decreased convulsions` with
`literature: "28216264"`; high-quality chemical probes `BI-1030` and `RO4938581`.
`GRIN2B` → safety events `convulsions`, `dizziness`, `pain` (same source).
Safety liabilities come with PMIDs — register those PMIDs as sources rather than
citing "Open Targets says so".

### 5.2 GWAS studies for a trait, then fine-mapped credible sets with L2G and coloc

```graphql
query S($efo: [String!]) {
  studies(diseaseIds: $efo, page: {index: 0, size: 50}) {
    count
    rows { id traitFromSource projectId pubmedId publicationFirstAuthor nSamples studyType }
  }
}
```
```graphql
query CS($studyIds: [String!]) {
  credibleSets(studyIds: $studyIds, studyTypes: [gwas], page: {index: 0, size: 100}) {
    count
    rows {
      studyLocusId region finemappingMethod confidence
      pValueMantissa pValueExponent beta standardError
      variant { id rsIds }
      study { id traitFromSource pubmedId nSamples }
      l2GPredictions(page: {index: 0, size: 5}) { count rows { score target { approvedSymbol id } } }
      colocalisation(page: {index: 0, size: 10}) { count }
    }
  }
}
```
Root-level `credibleSets` accepts `studyIds`, `studyTypes`, `variantIds`, `regions`.
`StudyTypeEnum` = `gwas, eqtl, pqtl, sqtl, tuqtl, sceqtl, scpqtl, scsqtl, sctuqtl`.

**Important:** `target(...) { credibleSets }` returns mostly **molecular QTL** credible
sets for that gene (confirmed: GABRA5 → 34 sets, nearly all `eqtl`/`tuqtl`), with empty
`l2GPredictions`. For locus-to-gene evidence you must go the other way: trait → GWAS
studies → GWAS credible sets → `l2GPredictions`. L2G `score` is a **published model
output**, so record it as `model_derived` with `derived_from: open_targets_l2g` and the
data version — it is not our probability and not a calibrated causal probability.

## 6. ChEMBL (via MCP tools available in this session)

`compound_search`, `target_search`, `get_mechanism`, `get_bioactivity`, `get_admet`.
Use for intervention entity records (mechanism of action, max clinical phase) and to
avoid hand-writing ChEMBL ids. A binding or mechanism record is **never** efficacy
evidence (contract rule V16).

## 7. Literature search (MCP tools available in this session)

* `mcp__plugin_bio-research_pubmed__search_articles` / `get_article_metadata` /
  `get_full_text_article` (PMC open access only).
* `mcp__plugin_bio-research_c-trials__*` for trial search, including
  `search_by_sponsor` and `analyze_endpoints`.
* `mcp__a6d73e05-...__search_preprints` (bioRxiv/medRxiv) — date/category search only,
  no keyword search; treat preprints as `source_type: preprint` and never let a
  preprint carry a claim on its own.
* Amass `search_amass_biomedcore_records` / `search_amass_trialcore_records` for
  cross-linked publication/trial discovery.

Whatever the discovery route, the **verification** route is always
`scripts/fetch_source_metadata.py`. Discovery tools may paraphrase; the registry
snapshot is what the repository trusts.
