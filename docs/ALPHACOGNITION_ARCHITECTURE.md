# AlphaCognition Architecture — v0.1 built, v0.2+ designed

**Owner:** `agent:alphacognition`. **Written:** 2026-09-17. **Status:** v0.1 sections describe
code that exists and ran; v0.2+ sections are design only and are labelled as such.

This document is the pipeline design for the human-genetics half of the Intelligence
Blueprint, plus an honest account of where the inferential chain breaks. It is deliberately
front-loaded with the warnings, because the warnings are the load-bearing part: every stage
below can be built correctly and still produce a conclusion that is worthless if §1 is
forgotten.

---

## 1. Mandatory warnings

These are not caveats. They are the reasons this repository exists, and each one is
enforced by a required field rather than by prose.

### 1.1 A GWAS effect size is not an intervention effect size

A per-allele beta from a cognitive GWAS describes the average difference in a phenotype
between people who inherited one allele and people who inherited another, across an entire
life course, in a specific population, conditional on everything else about them being as it
happened to be. It does not describe what happens if you change that gene's activity in an
adult.

Concretely, a GWAS Catalog `beta` field for a cognitive trait looks like
`"4.76 z-score increase"` — a string, in units the study chose, for one variant, in one
analysis. The catalogue reports these verbatim and so do we (`effect_size.as_reported`),
because the moment such a value is normalised into "a number" it invites arithmetic that has
no meaning: summing them, comparing them across studies, or treating them as the expected
benefit of an intervention. **Enforcement:** `effect_size.as_reported` is a verbatim string
or null; `effect_size.value` is populated only when the source states it explicitly;
`pipelines/alphacognition/fetch_gwas_catalog.py` never computes a number.

### 1.2 Heritability is not modifiability

A trait can be highly heritable and completely unresponsive to any intervention we can
build, and a trait can be barely heritable and trivially modifiable. Heritability is a
variance decomposition in a population at a time; modifiability is a causal property of a
mechanism. Nothing in this pipeline estimates heritability, and no facet level anywhere in
this atlas is raised because a trait is heritable. **Enforcement:** the facet
`adult_onset_perturbation` requires adult-onset perturbation claims, not genetic
architecture.

### 1.3 A locus is not a gene

The GWAS Catalog's `mapped_genes` field is positional annotation: the gene or genes whose
coordinates overlap or lie nearest the associated variant. In a gene-dense region this is
frequently the wrong gene, and in a gene-poor region it may be the only candidate for no
better reason than distance. Fine mapping narrows the variant set; locus-to-gene models rank
candidate genes; colocalisation with a molecular QTL supports a gene assignment. None of
these is a proof, and the first is not even an argument.

**Enforcement:** `causal_attribution.basis: gwas_association_only` and
`causal_attribution.locus_to_gene_resolved: no` on every claim derived from positional
mapping; `ontology/edges.yaml` forbids writing `MAPS_TO_GENE` from positional overlap; the
`causal_gene_attribution` facet is capped at level 1 when positional mapping is all there is.

**The v0.1 result:** across the 27 seed targets, **no target reached level 3 on
`causal_gene_attribution`**, because not one seed gene had a molecular-QTL colocalisation
supporting its assignment at a cognitive-trait credible set. This is the single most
important honest output of the milestone. Genes that "come up in intelligence GWAS" are, on
current public evidence, genes that happen to sit near intelligence-associated variants.

### 1.4 Cognitive GWAS are overwhelmingly European-ancestry

Every large discovery cohort behind the trait panel — UK Biobank, COGENT, CHARGE, SSGAC and
their descendants — is predominantly of European ancestry. Two consequences:

* **Transportability is unestablished.** Allele frequencies, LD structure and environmental
  context all differ across populations, so neither the association nor a fine-mapped
  credible set nor an L2G assignment built on that LD structure can be assumed to hold
  elsewhere.
* **Fine mapping inherits the problem.** Credible sets are defined against a reference LD
  panel. Open Targets reports `ldPopulationStructure` per study, and for the cognitive
  studies retrieved here it is dominated by `nfe` (non-Finnish European) with relative
  sample size 1.

**Enforcement:** every machine claim carries an ancestry string in `risks`, copied from the
source record (`discovery_ancestry` in GWAS Catalog, `ldPopulationStructure` in Open
Targets); every generated facet assessment carries the ancestry limitation in
`limiting_factor`.

### 1.5 Single-cohort dependence

Within the European-ancestry literature, a handful of cohorts dominate, and UK Biobank
dominates the largest traits in this panel. Reaction time (`EFO_0008393`), verbal-numerical
reasoning (`EFO_0008394`) and educational attainment (`EFO_0011015`) are all traits where a
single cohort supplies most of the sample. The consequence is that two "independent"
associations can be the same 300,000 people analysed twice.

**Enforcement and audit route:** `data/interim/gwas_catalog_associations.jsonl` carries
`accession_id`, `pubmed_id`, `first_author` and `initial_sample_size_as_reported` per row,
and `data/interim/opentargets_l2g.jsonl` carries `study_id`, `pubmed_id`, `n_samples` and
`initial_sample_size_as_reported` per credible set. The red team's `citation_dependence` and
`duplicated_evidence` checks can group by cohort description directly from those columns.
Claim-level `provenance.supporting_pubmed_ids` and `provenance.supporting_study_ids` make the
same grouping possible per claim. Nothing in this atlas de-duplicates cohorts automatically:
that is a ranking-invariance concern and belongs to `agent:integration`.

### 1.6 Educational attainment is not an intelligence endpoint

Stated in full in `atlases/alphacognition/cognitive_trait_panel.yaml`. Four traits in the
panel (`EFO_0011015`, `EFO_0004784`, `EFO_0005300`, `EFO_0005299`) carry
`phenotype_class: educational_attainment` and `use_in_ranking: proxy_only`, every claim
derived from them carries
`translation.general_intelligence_relevance: educational_attainment_proxy`, and every count
reported anywhere in this atlas separates cognitive from EA associations.

### 1.7 An L2G score is somebody else's model output

Open Targets' locus-to-gene score, and colocalisation `h4`/`clpp`, are published outputs of
published models at a named data version. They are not this project's probabilities, they
are not calibrated as P(causal), and they are not comparable across data versions. They
appear in claims only inside `uncertainty.model_outputs[]` with `derived_from` and
`data_version`, alongside an `interpretation_limits` string; `effect_size.metric` stays
`not_extracted`. They are never thresholded into a decision here.

---

## 2. What exists in v0.1 (code that ran on 2026-09-17)

| Stage | Module | Input | Output | Access status |
|---|---|---|---|---|
| Trait panel | `atlases/alphacognition/cognitive_trait_panel.yaml` (curated) | GWAS Catalog `/v2/efo-traits`, Open Targets `diseases(efoIds:)` | 24 EFO terms, 22 queried | **verified working** |
| Association ingestion | `pipelines/alphacognition/fetch_gwas_catalog.py` | 31 seed gene symbols x 22 traits | `data/interim/gwas_catalog_associations.jsonl`, `evidence/claims/alphacognition/gwas_catalog_derived.yaml` | **verified working** |
| Gene pleiotropy | `pipelines/alphacognition/fetch_gene_pleiotropy.py` | 31 gene symbols, unfiltered | `data/interim/gwas_catalog_gene_pleiotropy.jsonl` | **verified working** |
| Fine mapping + L2G + coloc | `pipelines/alphacognition/fetch_opentargets_genetics.py` | 22 traits -> studies -> credible sets | `data/interim/opentargets_l2g.jsonl`, `evidence/claims/alphacognition/opentargets_l2g_derived.yaml` | **verified working** |
| Adult brain expression | `pipelines/alphacognition/fetch_expression.py` | 31 gene symbols | `data/interim/adult_brain_expression.jsonl`, `evidence/claims/alphacognition/expression_derived.yaml` | **verified working (bulk only)** |
| Source assembly | `pipelines/alphacognition/build_sources.py` | curated + generated fragments | `evidence/sources/alphacognition.yaml` | **verified working** |
| Facet assessment | `pipelines/alphacognition/build_assessments.py` | the four derived tables + `lead_atlas_facets.yaml` | `atlases/alphacognition/assessments/{SYMBOL}.yaml` x 27 | **verified working** |

Every network stage writes an immutable snapshot under `data/raw/` with a `MANIFEST.jsonl`
line before interpreting anything, and every stage has `--offline` to rebuild its derived
table from those snapshots with no network. Offline classification is by *payload shape*
(GWAS Catalog HAL responses embed the query in `_links.self.href`; study records carry
`accession_id`; GraphQL responses carry their operation's data key), so no side index can
drift out of sync with the snapshot directory.

### 2.1 Interfaces

```python
# fetch_gwas_catalog.py
fetch_associations(gene: str, efo_id: str) -> list[dict]        # paginated, snapshots each page
association_rows(gene, trait, raw_rows, *, release) -> list[dict]
study_design(study: dict) -> Literal["gwas", "gwas_meta_analysis"]
build_claims(rows, studies, *, release, run_id, species) -> list[dict]

# fetch_opentargets_genetics.py
graphql(query: str, variables: dict, *, name_hint: str) -> dict # raises on GraphQL errors
derived_rows(traits, studies_by_trait, credible_sets, coloc, *, data_version) -> list[dict]
qtl_coloc_for_gene(coloc_record: dict, symbol: str) -> list[dict]

# fetch_expression.py
gtex_gene(symbol: str) -> dict                                  # symbol -> gencodeId
gtex_median_expression(gencode_id: str, symbol: str) -> dict

# _common.py
resolve_species_id(name="Homo sapiens", *, offline=False) -> str | None   # NCBI taxonomy
```

Contract for every derived table: one JSON object per line, keys sorted, deterministic row
order, no computed statistics, `*_as_reported` for anything the source stated numerically.

### 2.2 Why the facet rules are code

`build_assessments.py` applies one written-down rule to 27 targets instead of 27
hand-written judgements. The full rule set is in that module's docstring. It is still a
curatorial decision — the mapping from evidence pattern to ordinal level was chosen by this
agent against `docs/DATA_CONTRACT.md` §5.3 — but it is auditable, re-runnable, and the
generated `rationale` strings quote the counts each grade came from. Level 4 is unreachable
for all four genetics facets in v0.1, and each file says why in `limiting_factor`.

---

## 3. The designed pipeline (v0.2+), stage by stage

Each stage lists: **in / out / source and access status verified today / interface / where
the chain breaks.**

### Stage 1 — Trait and endpoint definition
* **In:** EFO; study-level trait descriptions.
* **Out:** trait panel with `phenotype_class` and `use_in_ranking`.
* **Source / access:** GWAS Catalog `/v2/efo-traits?trait=` — **working**. Open Targets
  `diseases(efoIds:)` — **working**.
* **Interface:** `atlases/alphacognition/cognitive_trait_panel.yaml` (see §2).
* **Breaks:** substring search cannot prove completeness; EFO grouping terms cannot be given
  a single `phenotype_class`; the contract's `far_transfer`, `metacognition` and
  `learning_rate` classes have **no corresponding GWAS trait at all**, so those facets are
  permanently unreachable from genetics and must stay `not_assessed` rather than be inferred
  from a correlated endpoint. `EFO_0004335` ("short-term memory") is mapped to
  `working_memory`, which is an approximation and is flagged as one.

### Stage 2 — Association ingestion
* **In:** gene symbols x trait EFO ids.
* **Out:** `data/interim/gwas_catalog_associations.jsonl`; positional association claims.
* **Source / access:** GWAS Catalog REST v2, release `2026-09-13`, EFO `v3.93.0` — **working**.
* **Interface:** §2.1.
* **Breaks:** positional mapping (§1.3); the catalogue records only associations that passed
  a threshold, so absence of a catalogued negative is uninformative; `beta` is free text and
  effect alleles are often `?`, so **direction consistency across studies cannot be
  established**, which is why level 4 on `human_genetic_association` is never awarded.

### Stage 3 — Fine mapping
* **In:** trait EFO -> `studies(diseaseIds:)` -> `credibleSets(studyIds:, studyTypes:[gwas])`.
* **Out:** credible sets with `finemappingMethod`, `confidence`, lead variant, rsIDs.
* **Source / access:** Open Targets Platform GraphQL, API `26.6.3`, data `26.06` — **working**.
  Root `credibleSets` accepts `studyIds`, `studyLocusIds`, `variantIds`, `studyTypes`,
  `regions`; batching all of a trait's study ids into one call with `size: 200` is what makes
  this tractable (13,730 credible sets across 716 GWAS studies for 22 traits).
* **Interface:** §2.1.
* **Breaks:** credible sets are LD-panel-dependent (§1.4); `finemappingMethod` varies
  (`PICS` from a reported top hit versus `SuSiE-inf` from summary statistics) and those are
  not equivalent in reliability — a PICS set "based on reported top hit" is little more than
  an LD expansion. The derived table keeps the method string per row precisely so a consumer
  cannot pool them silently.

### Stage 4 — AlphaGenome variant-effect prediction (**interface only; not runnable here**)
* **In:** credible-set variants (GRCh38 coordinates, ref/alt) + a genomic window.
* **Out:** predicted regulatory effect tracks per variant per tissue/assay, cached.
* **Source / access:** requires `ALPHAGENOME_API_KEY`. **This environment does not have that
  variable set, so the module must be interface-only.**
* **Design:**
  ```python
  # pipelines/alphacognition/alphagenome_interface.py   (v0.2, NOT YET WRITTEN)
  class AlphaGenomeUnavailable(RuntimeError): ...

  def require_api_key() -> str:
      key = os.environ.get("ALPHAGENOME_API_KEY")
      if not key:
          raise AlphaGenomeUnavailable(
              "ALPHAGENOME_API_KEY is not set. AlphaGenome predictions are unavailable in "
              "this environment. No prediction will be produced and no placeholder value "
              "will be written. Set the variable and re-run, or run with --skip-alphagenome "
              "to continue without this stage."
          )

  def predict_variant_effects(variants: list[VariantSpec], *, window: int) -> list[Path]:
      """Return snapshot paths. Raises AlphaGenomeUnavailable when no key is present."""
  ```
  * **Fail loudly, never fabricate.** The module raises `AlphaGenomeUnavailable` with the
    message above. It must never return zeros, means, random values, or a "predicted" track
    of any kind when the key is absent. A downstream stage that finds no AlphaGenome snapshot
    records `alphagenome_status: not_run` and continues; it does not impute.
  * **Cache / snapshot layout:**
    `data/raw/alphagenome/<YYYY-MM-DD>/<model_version>/<chrom>/<variant_id>_<window>.json`,
    one `MANIFEST.jsonl` line per file with `sha256`, the model version, the window size and
    the requested output tracks. Model version is part of the path because predictions are
    not comparable across model versions, and the path must make that impossible to ignore.
    Derived table: `data/interim/alphagenome_variant_effects.jsonl`, one row per
    (variant, tissue, assay) with the prediction labelled
    `derived_from: alphagenome`, `model_version: <...>` — exactly the treatment L2G scores
    get (§1.7).
  * **No credentials on disk, ever.** The key is read from the environment, never written to
    a snapshot, a manifest, a log line or a derived table (contract V18); the manifest query
    dict goes through `scripts/_provenance.scrub_query`.
* **What AlphaGenome can and cannot tell us — precisely:**
  * **Can:** predict, from sequence, the effect of a variant on molecular regulatory
    readouts — chromatin accessibility, histone marks, transcription-factor binding, RNA
    expression and splicing — in the cell types and assays its training data covers. It is a
    variant-to-molecular-function predictor.
  * **Cannot, and must never be presented as:** (a) a predictor of cognition, intelligence,
    or any behavioural phenotype — it has never seen a cognitive measurement; (b) evidence
    that a variant is causal *for a trait* — it predicts a molecular consequence, which is a
    different proposition from trait causality; (c) a substitute for the locus-to-gene step —
    a predicted regulatory effect on gene X does not establish that the trait association
    acts through gene X, only that the variant plausibly affects X; (d) evidence about adult
    human brain cell types it was not trained on; (e) an effect size. Its outputs are model
    predictions and carry `causal_attribution.basis: computational_prediction`, which the
    contract ranks below every experimental basis.
  * **Consequence for facet levels:** an AlphaGenome prediction can *raise* the plausibility
    of a fine-mapped assignment and can *never* on its own move `causal_gene_attribution`
    above level 1, because the facet's proposition is about the human genetic signal and
    §5.3 requires human evidence for levels 3-4.

### Stage 5 — Brain eQTL / sQTL
* **In:** credible-set variants; brain tissues.
* **Out:** variant -> gene -> tissue molecular associations.
* **Source / access:** Open Targets carries QTL credible sets (`studyTypes`:
  `eqtl, pqtl, sqtl, tuqtl, sceqtl, scpqtl, scsqtl, sctuqtl`) — **reachable**, and
  `target { credibleSets }` returns mostly molecular-QTL sets for a gene (confirmed in
  `docs/API_RECIPES.md` §5.2). GTEx brain eQTL via the GTEx API and PsychENCODE/MetaBrain
  bulk-brain eQTL resources — **not ingested in v0.1, access not verified**. This is task
  `T00x`/`Q002` territory in `docs/TASK_DAG.yaml`.
* **Interface (design):** `data/interim/brain_qtl.jsonl` with
  `{variant_id, gene, tissue, qtl_type, study_id, source_release, effect_as_reported}`.
* **Breaks:** brain eQTL sample sizes are small relative to blood; bulk-brain eQTL averages
  over cell types, so a real neuronal eQTL can be invisible and a glial one can dominate; an
  eQTL in adult post-mortem tissue may not exist in the developmental window when the trait
  variance was generated.

### Stage 6 — Colocalisation
* **In:** GWAS credible set + QTL credible set at the same locus.
* **Out:** posterior support for a shared causal variant, per gene per tissue.
* **Source / access:** Open Targets `credibleSet { colocalisation }` — **working**. Returns
  `h4`, `clpp`, `colocalisationMethod` (e.g. `COLOC_PIP_ECAVIAR`),
  `numberColocalisingVariants`, and `otherStudyLocus.study { studyType, target, biosample }`.
* **Interface:** `qtl_coloc_for_gene(coloc_record, symbol)` (§2.1) filters to
  `studyType != gwas` with `target.approvedSymbol == symbol`.
* **Breaks — and this is where v0.1 actually stopped:** for the 70 cognitive-trait credible
  sets in which a seed gene appeared among L2G candidates, **zero** had a molecular-QTL
  colocalisation for that same gene. The colocalisations that exist at those loci are
  GWAS-to-GWAS (trait-to-trait), which speak to pleiotropy, not to gene assignment. Reasons
  this is unsurprising: brain QTL coverage is thin; a coloc posterior requires both signals
  to be well-powered; and the relevant tissue or cell type may not be in any QTL catalogue.
  **A zero here is a statement about the state of public data, not about the genes.**

### Stage 7 — Adult cell-type expression
* **In:** gene list.
* **Out:** expression per adult human brain cell type and region.
* **Source / access:** GTEx v8 via GTEx API v2 `/expression/medianGeneExpression` —
  **working**, 54 tissues including 13 brain regions with UBERON `ontologyId`s, but
  **bulk tissue only**. Open Targets `baselineExpression` — **reachable and it does expose
  `celltypeBiosample`**, but (a) its cell-type rows come from Tabula Sapiens, which does not
  cover brain, and (b) `page.index` was observed to be ignored, so only the first 500 of
  1,409 rows are retrievable for CHRM1. Allen Brain Cell Atlas / Human Brain Cell Atlas —
  **not ingested, access not verified**.
* **Status: deferred, explicitly.** Adult brain cell-type resolution is queued as **Q003** in
  `docs/TASK_DAG.yaml` ("Adult cell-type expression atlas ingestion"). Every
  `adult_expression_and_timing` facet in this atlas names Q003 in `limiting_factor`, level 4
  is unreachable, and **no claim anywhere asserts a cell type**.
* **Breaks:** bulk abundance is a mixture; a high regional median can come from a small
  population or from non-neuronal cells; post-mortem interval degrades RNA; presence of
  transcript is not functional relevance.

### Stage 8 — Developmental timing
* **In:** gene list.
* **Out:** prenatal-versus-postnatal expression trajectory per gene.
* **Source / access:** BrainSpan / PsychENCODE developmental transcriptome —
  **not ingested in v0.1, access not verified from this machine.**
* **Status: deferred.** The only developmental-timing claim in this atlas
  (`CLM:alphacognition:GRIN2B:006`) comes from a retrieved *publication*, is rodent, is
  indirect, and is graded level 1 and labelled as such. No developmental statement anywhere
  is inferred from adult GTEx values.
* **Breaks:** a prenatal-biased gene can still have an adult function; a flat trajectory does
  not imply adult modifiability; human developmental tissue is scarce and donor numbers per
  window are small.

### Stage 9 — Causal perturbation evidence (hand curation)
* **In:** literature search per target.
* **Out:** `evidence/claims/alphacognition/{SYMBOL}.yaml`.
* **Source / access:** PubMed / PMC / ClinicalTrials.gov v2 / ChEMBL via MCP — **working**.
* **Breaks:** publication bias toward positive results; `life_stage` and `baseline_context`
  are the fields that stop rescue being read as enhancement and development as adulthood;
  species distance is not a number and is recorded as `translation.human_relevance`.

### Stage 10 — Cross-species evidence
Owned by `agent:comparative`. This atlas contributes `context.species` (NCBI taxid resolved
at runtime, never hand-written) and `translation.human_relevance` on every claim.

### Stage 11 — Safety / pleiotropy
* **In:** target list.
* **Out:** adverse-event and pleiotropy annotations.
* **Source / access:** Open Targets `target { safetyLiabilities { event eventId datasource
  literature } }` — **reachable** and confirmed in `docs/API_RECIPES.md` §5.1 (GRIN2B returns
  `convulsions`, `dizziness`, `pain` with a PMID). **Not ingested by this agent** —
  deliberately, because safety is `agent:red_team`'s lane and because the right move is to
  register the PMIDs Open Targets supplies as sources rather than to cite "Open Targets says
  so". This atlas contributes the pleiotropy denominator instead
  (`data/interim/gwas_catalog_gene_pleiotropy.jsonl`).
* **Breaks:** absence of a catalogued liability is not evidence of safety; pleiotropy measured
  positionally is locus pleiotropy, not gene pleiotropy (§1.3).

### Stage 12 — Druggability / tractability
Owned by `agent:integration`. Open Targets `target { tractability }` and `chemicalProbes` are
confirmed reachable (`docs/API_RECIPES.md` §5.1). This atlas records intervention entities
for the compounds it cites, with ChEMBL ids taken only from tool responses, under
`atlases/alphacognition/interventions/`. A mechanism record is never efficacy (contract V16),
and ChEMBL's `disease_efficacy` flag is a curation of intended mechanism, not of trial
outcome — `atlases/alphacognition/interventions/CHEMBL3087515.yaml` (mavoglurant) is the
worked example: `disease_efficacy: true`, and the human trial was null.

---

## 4. Where the whole chain breaks, in one place

1. **Stage 2 -> 3.** An association can be real and the gene assignment wrong. Mitigated by
   fine mapping, never eliminated.
2. **Stage 3 -> 6.** Fine mapping plus L2G plus coloc can identify the right gene and still
   say nothing about whether *changing* that gene changes the trait. Gene identification and
   causal sufficiency are different propositions. In v0.1 the chain does not even reach the
   end of this link: no seed gene has QTL-supported assignment at a cognitive locus.
3. **Stage 6 -> 9.** Even with a gene identified, the direction and magnitude of a useful
   intervention are not derivable from the association. Common variation acts lifelong and in
   tiny increments; an intervention acts now and in large ones.
4. **Stage 7/8.** Adult expression does not establish adult modifiability, and a
   developmental-biased gene may have had its effect before anyone could intervene.
5. **Stage 9.** A rodent enhancement is a rodent enhancement. `GRIN2B` is the case study: two
   independent rodent overexpression studies show enhancement above wild-type, and the human
   evidence for perturbing the same gene is a neurodevelopmental encephalopathy.
6. **Everywhere.** Ancestry (§1.4) and single-cohort dependence (§1.5) limit how far any of
   it generalises.

**The design rule that follows:** no stage in this pipeline may ever raise an intervention
recommendation. The pipeline's output is a graded, referenced, contradiction-carrying
description of what is known. Nothing in it licenses an intervention on any gene, and the
`ASSOCIATED_WITH` predicate used by every machine claim cannot compile into a
`CHANGES_STATE` edge (contract V16, `ontology/edges.yaml`).

---

## 5. Defects filed, and how they were resolved

`docs/blackboard/schema_change_requests/alphacognition-001.yaml` was filed with seven items.
`docs/blackboard/RESOLUTIONS.md` records the outcomes; the state after them is:

| # | Item | Outcome |
|---|---|---|
| 1 | `SRC:DB:*` sources could never reach `status: verified`, so V6 and the brief's own instruction to register database releases were mutually unsatisfiable | **Resolved (R1), differently and better.** A release is now verified against *manifest integrity* — the snapshot must be in `data/raw/MANIFEST.jsonl` and its sha256 must still match the file — giving `release_verified_by_snapshot`. The proposal (re-read the release string from the pipeline's own snapshot) would have verified a record against itself. All four of this atlas's database releases now verify: `gwas_catalog:2026-09-13`, `opentargets:26.06`, `gtex:v8`, `chembl:ChEMBL_37`. |
| 2 | `fetch_source_metadata.py` cannot verify `SRC:GCST:*` against REST **v2** (no `publication` object; `disease_trait` not `reported_trait`) | Open. Not blocking: this atlas registers study PMIDs instead, which contract §3 prefers, and keeps GCST accessions in `evidence[].database_record.accession_id`. |
| 3 | No predicate could carry `claim_type: clinical_null` into a `CognitivePhenotype`, so a negative cognitive trial had no legal triple | **Resolved.** `ontology/edges.yaml` now has `NO_DETECTED_EFFECT_ON` (`asserts_absence_of_effect: true`, excluded from support counts). `CLM:alphacognition:GRM5:001` and `CLM:alphacognition:HTR2A:003` use it. |
| 4 | No `gtex_api` value in `retrieval.method` | Open; `known_identifier`/`opentargets_api` with an explicit note. Cosmetic. |
| 5 | `check_ownership.py --agent` treats a pipeline write to `data/interim/` as a violation | Open; the flags are reported rather than avoided. |
| 6 | `data/raw/opentargets_genetics/**` unowned | Open; also `data/raw/chembl/**`, added for the ChEMBL release snapshot that rule V9 requires. |
| 7 | `expression_atlas` used for an immunoblot measurement | Open; R5 added `structural_biology` to `evidence.design` but no targeted-quantification value. |

### 5.1 R5: measured absence versus absence of measurement

`docs/blackboard/RESOLUTIONS.md` R5 introduced `evidence.endpoint_measured`
(`measured | not_measured_in_protocol | measured_but_not_reported | unknown`), the graph-inert
`claim_type: evidence_gap`, and rule **V16c**. This is the most consequential amendment for this
atlas and it has been applied substantively, with one tooling caveat.

**Applied.** Every counter-grade in `atlases/alphacognition/lead_atlas_facets.yaml` was re-audited
against the distinction, and two were wrong:

* **GRIN2B `human_intervention_evidence`** had `counter_level: 1` resting on the statement that an
  objectifiable beneficial memantine response in GRIN2B patients remains to be demonstrated. That
  is an absence of measurement. Corrected to `counter_level: 0` with the point moved to
  `limiting_factor` as a coverage gap.
* **CHRM1 `human_intervention_evidence`** had `counter_level: 1` resting partly on the
  xanomeline-trospium psychosis programme being the largest human M1 dataset. Those three trials
  measured PANSS and adverse events and measured **no cognitive endpoint at all**, so with respect
  to cognition they are an evidence gap, not evidence against a cognitive effect — an approval in
  an indication with no cognitive endpoint says nothing either way. Corrected to
  `counter_level: 0`, moved to `limiting_factor`.

The two high counter-grades that survive the audit do so because the endpoint **was** measured:
**GRM5** `human_intervention_evidence` `counter_level: 3` (FXLEARN measured the primary Weighted
Communication Scale and all secondary cognitive and language measures and found no between-group
difference) and **HTR2A** `human_intervention_evidence` `counter_level: 3` (one randomised
healthy-adult study measured impairment of control and cognition, another measured cognitive
empathy and moral decision-making and found them unchanged). Both are `level: 0` with a high
counter-grade, which is the semantics the contract intends: nothing found supporting the
proposition, substantial measured evidence against it.

**Migrated in full.** When the audit was performed, `endpoint_measured` and `evidence_gap`
existed in `ontology/vocabularies.yaml` but not in `schemas/evidence.schema.json` or
`src/blueprint/records.py:EvidenceItem`, and writing the field failed V1. The determinations were
parked in the schema-legal `note` field behind an `endpoint_measured: ` prefix; the schema landed
later in the same session and they were promoted into the real field. Final census over all 234
evidence items in this atlas: **189 `measured`, 42 `not_measured_in_protocol`, 3 `unknown`** (two
ClinicalTrials.gov registry records and one narrative review — a registry record is not a
measurement and a review reports no protocol of its own). Every one of the 42 unmeasured items
sits inside an `evidence_gap` claim, which is what rule V16c requires.

Both measured cognitive nulls now use the null relation rather than an ordinary edge:
`CLM:alphacognition:GRM5:001` (`NO_DETECTED_EFFECT_ON`, `negated_relation: CHANGES_STATE`) and
`CLM:alphacognition:HTR2A:003` (`NO_DETECTED_EFFECT_ON`, `negated_relation: MODULATES`). The
second had been a `MODULATES` edge with `direction: no_change`, which would have let a measured
human null compile into the graph as an ordinary edge.

### 5.2 Coverage gaps as first-class records

`level: 0` on the shared scale means *searched and found nothing*, and the assessment schema
requires an assessed facet to cite evidence. Those two are in tension unless the absence itself is
recorded, and the pressure the tension creates is towards either a tangential citation or a quiet
downgrade to `not_assessed` — a different epistemic state the contract works hard to keep
distinct. `pipelines/alphacognition/build_coverage_gaps.py` resolves it by emitting **24
`evidence_gap` claims**, graph-inert by construction and barred from any `counter_level`:

* **18 genetics-sweep gaps** (`CLM:alphacognition:gap.{GENE}:001`) — one per seed gene with no
  cognitive-trait association in GWAS Catalog 2026-09-13 **and** no cognitive-trait L2G candidacy
  in Open Targets 26.06. Sourced to the two pinned database releases, with the endpoint field
  naming the exact query performed. Each one also records how many associations the catalogue
  *does* hold for that gene on other traits, so "not in the catalogue" and "in the catalogue but
  never measured against cognition" cannot be confused.
* **6 lead-atlas literature gaps** (`CLM:alphacognition:gap.{SYMBOL}:002`) — sourced to the
  target's own primary study with `endpoint_measured: not_measured_in_protocol`, because the
  accurate statement is not "no paper exists" but "the studies that do exist did not measure
  this". CHRM1's is the sharpest: the largest human M1 dataset by sample size measured PANSS and
  adverse events and no cognitive endpoint at all.

Every `level: 0` grade additionally carries `search_basis` — what was searched, at what scope, and
what would have counted as a hit — so a zero is accountable without a citation standing in for
evidence that does not exist.
