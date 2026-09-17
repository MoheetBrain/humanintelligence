# Handoff — `agent:alphacognition`, AlphaCognition v0.1

**Written:** 2026-09-17. **Branch:** `sprint-1/foundation`.
**Scope:** the human-genetics ingestion infrastructure for all 27 seed targets, plus lead-atlas
dossiers for the six targets assigned to this atlas (`GRIN2B`, `CRTC1`, `CHRM1` deep; `GRM5`,
`DRD1`, `HTR2A` shallow), plus `docs/ALPHACOGNITION_ARCHITECTURE.md`.

---

## 0. Correction after red-team audit — educational attainment was being laundered into fluid reasoning

**The defect.** `atlases/alphacognition/cognitive_trait_panel.yaml` marked "mathematical
ability" (`EFO_0004875`) as `use_in_ranking: supporting`, with the explicit note that it is
"never a stand-alone basis for a facet level". `pipelines/alphacognition/build_assessments.py`
branched on `phenotype_class` alone and **never read `use_in_ranking`**. The guard was inert.
The records behind that trait are *"Self-reported math ability"* and *"Highest math class
taken"* from **PMID 30038396 — a 1.1-million-person educational attainment GWAS** — and they
were awarding fluid-reasoning-grade facet levels. That is the
`educational_attainment_mistaken_for_intelligence` failure principle P4 exists to block, and it
survived because **the guard lived in data while the decision lived in code**. It was in my
lane; the fix is too.

**The fix, structural rather than local.**
1. Eligibility now lives in **one** function every consumer imports — `_common.trait_use` and
   `_common.partition_by_eligibility` — and it **fails closed**: `primary` may carry a grade
   alone, `supporting` may only corroborate, `proxy_only` may not contribute to an
   intelligence-relevant facet at all, and anything else *including a missing field* is treated
   as `proxy_only`.
2. The two trait-dependent rules are extracted as pure functions
   (`genetic_association_level`, `causal_attribution_level`), and `build_assessments.py` now
   **cross-checks the level its prose branch produced against the rule function and aborts on
   divergence**. Guard-versus-decision drift is the bug class that just occurred, so it is now a
   hard error. It fired immediately on CRTC1 during development and forced the rule to be
   stated properly rather than the prose adjusted.
3. `build_coverage_gaps.py` uses the same eligibility function, so a gene whose only panel hit
   is a `supporting` or `proxy_only` trait now correctly receives a coverage-gap record.
4. **Test:** `pipelines/alphacognition/test_facet_guardrails.py`, 12 cases, all passing. Run
   against the pre-fix behaviour (guard stubbed to permissive) **4 of them fail**, including the
   exact finding — *"a `supporting` trait alone produced level 3; it may only corroborate"*. It
   also asserts panel-level invariants: every trait declares an eligibility, and every
   EA-classed trait is `proxy_only`. It sits in `pipelines/alphacognition/` because
   `docs/OWNERSHIP.yaml` gives `tests/**` to `agent:ontology`; relocation under a carve-out is
   requested as item 8 of the schema-change request.

**Grades moved: 10 of 144, all 10 downward. None upward.**

| Target | Facet | level/counter |
|---|---|---|
| CRTC1 | `human_genetic_association` | **3 → 1** |
| CRTC1 | `causal_gene_attribution` | 2 → 0 |
| CRTC1 | `human_phenotype_specificity` | 2 → 1 |
| DRD1 | `causal_gene_attribution` | 2 → 0 (counter 2 → 0) |
| GRIN2B | `causal_gene_attribution` | 2 → 1 (counter 2 → 0) |
| KCNQ3 | `causal_gene_attribution` | 1 → 0 |
| KCNQ3 | `human_phenotype_specificity` | 2 → 1 |
| OTX2 | `causal_gene_attribution` | 2 → 1 |
| PDE4B | `causal_gene_attribution` | 2 → 1 (counter 2 → 0) |
| SLC16A7 | `causal_gene_attribution` | 2 → 1 |

**Verified independently, and the damage was wider than reported.** The red team predicted
CRTC1 would fall and that GRIN2B, OTX2, PDE4B and SLC16A7 would survive on other evidence.
That is correct **for `human_genetic_association`** — those four do have primary-trait
associations and hold their grade. It is **not** correct for `causal_gene_attribution`: the same
laundering was running through the locus-to-gene path, and checking it directly rather than
trusting the summary showed that **every one of the 12 genes previously reported as having
"L2G candidacy on a cognitive trait" was in fact on `mathematical ability` or on educational
attainment itself**. Of the 70 seed-gene credible sets: **20 on primary cognitive traits
(intelligence, cognitive function measurement, episodic memory), 14 on `supporting` traits (all
"mathematical ability"), 36 on `proxy_only` or unmapped traits.**

**Corrected count: 6 seed genes — not 12 — have locus-to-gene candidacy on a primary cognitive
trait: CKB, GABRA5, GPR158, GRM5, HCN1, HTR2A.** A latent bug was fixed in the same place:
credible sets whose study mapped to no panel trait carried `is_educational_attainment: None`,
which the old filter read as falsy and therefore counted as cognitive. Fail-closed eligibility
removes them.

A separate rule, **V-DIR2**, landed during the same pass and is also fixed: the 31 expression
claims carried `direction: no_change`, which would assert a null result GTEx never reported.
They now carry `direction: not_applicable` — a tissue abundance measurement asserts no
direction at all.

---

## 1. The headline finding

**Not one of the 27 seed targets has locus-to-gene evidence strong enough to attribute a
cognitive GWAS signal to it.**

`causal_gene_attribution` across all 27 targets, after the §0 correction: **level 0 × 17,
level 1 × 4, level 2 × 6, level 3 × 0, level 4 × 0.** Nobody reached level 3 because **zero**
seed genes have a molecular-QTL colocalisation supporting their assignment at any
cognitive-trait credible set. Of the **20** primary-cognitive-trait credible sets in which Open
Targets' L2G model ranks a seed gene, none has a QTL coloc for that gene; the colocalisations
that do exist at those loci are GWAS-to-GWAS, which speak to pleiotropy rather than to gene
assignment.

Read together with `human_genetic_association` (level 3 × 8, level 2 × 1, level 1 × 18), the
picture is: eight of these genes sit near a variant associated with a directly relevant
cognitive endpoint, six are ranked by a statistical model as one of several candidates at such a
locus, and **none** of them has been shown to be the gene the signal acts through. Genes that "come up in
intelligence GWAS" are, on current public evidence, genes that happen to be near
intelligence-associated variants. This is a statement about the state of public data, not about
the genes — brain QTL coverage is thin and the relevant cell types are largely absent from QTL
catalogues.

Level 4 is unreachable for all four genetics facets in v0.1, and every assessment says why in
`limiting_factor`.

---

## 2. Real numbers

### Trait panel — `atlases/alphacognition/cognitive_trait_panel.yaml`
* **24 EFO terms**, **22 queried**, 2 excluded (EFO grouping/process terms that cannot carry a
  single `phenotype_class`).
* 9 `primary`, 6 `supporting`, 7 `proxy_only`. **4 are educational-attainment or literacy**
  (`EFO_0011015`, `EFO_0004784`, `EFO_0005300`, `EFO_0005299`), all
  `phenotype_class: educational_attainment`, `use_in_ranking: proxy_only`.
* Every id was returned by a tool call (GWAS Catalog `/v2/efo-traits?trait=`, cross-checked
  against Open Targets `diseases(efoIds:)`); the substring that returned each one is recorded.
* Registry versions seen: GWAS Catalog release **2026-09-13**, EFO **v3.93.0**, Open Targets
  API **26.6.3** / data **26.06**, GTEx dataset **gtex_v8**, ChEMBL **ChEMBL_37**.

### GWAS Catalog ingestion (31 gene symbols × 22 traits = 682 pairs)
* **68 association records** retrieved: **40 on cognitive traits**, **28 on
  educational-attainment or literacy traits**.
* **12 of 31 genes** have any association; **11 have ≥1 cognitive-trait association**: CKB, CRTC1,
  GPR158, GRIN2B, GRM5, HCN1, HTR2A, KCNQ3, OTX2, PDE4B, SLC16A7.
* 32 unique GCST accessions, 22 unique PubMed ids.
* Unfiltered pan-trait sweep (`fetch_gene_pleiotropy.py`): 29 of 31 genes have catalogued
  associations, **1,948 associations in total** — so ~96% of the catalogued signal at these loci
  is with something other than cognition. That denominator is what makes
  `human_phenotype_specificity` assessable at all.

### Open Targets locus-to-gene (22 traits → 716 GWAS studies → 13,730 credible sets)
* **70 credible sets** rank a seed gene among L2G candidates; **34 of those are cognitive-trait**
  credible sets.
* **15 seed genes** have L2G candidacy on any panel trait; **6 on a PRIMARY cognitive trait**
  (CKB, GABRA5, GPR158, GRM5, HCN1, HTR2A). Trait breakdown of the 70 seed-gene credible sets:
  **20 primary** (intelligence 10, cognitive function measurement 9, episodic memory 1),
  **14 `supporting`** (all "mathematical ability"), **36 `proxy_only` or unmapped** (educational
  attainment 23, self-reported educational attainment 13). The nine genes whose only candidacy
  is on supporting or EA traits — CRTC1, DRD1, GRIN2B, OTX2, PDE4B, SLC16A7, EIF2B4, EIF2S1,
  HDAC2 — get no attribution credit for it; see §0.
* **0 seed genes** have any molecular-QTL colocalisation.

### Expression
* GTEx v8 brain data for **31/31 genes**, 13 brain regions each; **30/31 detected above zero
  median in every sampled region**. Bulk tissue only.
* **Adult brain cell-type resolution: not available, deferred to `docs/TASK_DAG.yaml` Q003.** No
  claim in this atlas asserts a cell type. Open Targets `baselineExpression` does expose
  `celltypeBiosample` in 26.06, but its cell-type rows are Tabula Sapiens (no brain) and its
  `page.index` argument is ignored (only the first 500 of 1,409 rows are retrievable for CHRM1).

### Claims
| | count |
|---|---|
| hand-curated | **21** (GRIN2B 6, CHRM1 5, CRTC1 3, HTR2A 3, DRD1 2, GRM5 2) |
| machine-generated from databases | **104** (GWAS Catalog 38, Open Targets L2G 35, expression 31) |
| machine-generated coverage gaps (`claim_type: evidence_gap`, graph-inert) | **27** (21 genetics-sweep gaps, 6 lead-atlas literature gaps) |
| **total** | **152** |

`endpoint_measured` across all 240 evidence items: **189 `measured`, 48
`not_measured_in_protocol`, 3 `unknown`** (two ClinicalTrials.gov registry records and one
narrative review). The 48 unmeasured items are all inside `evidence_gap` claims, which is what
rule V16c requires and what keeps them out of every `counter_level`.

### Sources
**58 registered, 58 verified.** 54 `verified` (52 PMID + 2 NCT, checked against PubMed ESummary
and ClinicalTrials.gov v2) and 4 `release_verified_by_snapshot` (the database releases, under R1).
**No failures, nothing dropped, no identifier "corrected".** Every PMID was found by a tool search
in this session and its title/year/journal/first author read from PubMed rather than authored, so
the verifier checks against the same authority that supplied the strings.

### Validator
`.venv/bin/python graph/validate_graph.py --strict` → **0 violations in any file owned by this
agent** (2 remain repository-wide, all in other agents' lanes, dominated by V15 red-team audit
coverage, which has not run yet). This was re-run after each of the four schema amendments that
landed mid-session (`NO_DETECTED_EFFECT_ON` + `negated_relation`, `endpoint_measured`,
the assessed-facet-must-cite-evidence rule, and `search_basis` for level-0 grades) and the
records were migrated to each, not worked around.

---

## 3. Commands run, with real results

```
curl .../gwas/rest/api/v2/metadata                      → data_release_date 2026-09-13, efo_version v3.93.0
curl .../gwas/rest/api/v2/efo-traits?trait=…            → 21 probe strings, 24 terms adopted
POST .../opentargets/api/v4/graphql (meta)              → apiVersion 26.6.3, dataVersion 26.06
curl .../gtexportal.org/api/v2/expression/medianGeneExpression → 54 tissues, 13 brain, UBERON ids
curl .../ebi.ac.uk/chembl/api/data/status.json          → ChEMBL_37, released 2026-05-01

.venv/bin/python pipelines/alphacognition/fetch_gwas_catalog.py
    → 68 associations, 38 claims, 23 source records, 682 pairs queried, 0 trait-label problems
.venv/bin/python pipelines/alphacognition/fetch_gene_pleiotropy.py
    → 31 genes, 1948 associations, 29 genes with any association
.venv/bin/python pipelines/alphacognition/fetch_opentargets_genetics.py
    → 716 GWAS studies, 13730 credible sets, 70 with a seed gene, 0 QTL colocs, 35 claims, 0 failures
.venv/bin/python pipelines/alphacognition/fetch_expression.py
    → 31/31 genes, 13 brain regions each, 30 detected everywhere, 31 claims, 0 failures
.venv/bin/python pipelines/alphacognition/fetch_expression.py --offline          → identical output
.venv/bin/python pipelines/alphacognition/fetch_opentargets_genetics.py --offline → identical output
.venv/bin/python pipelines/alphacognition/build_sources.py
    → evidence/sources/alphacognition.yaml: 58 records (52 PMID, 2 NCT, 4 database release)
.venv/bin/python pipelines/alphacognition/build_coverage_gaps.py
    → 27 evidence_gap claims (21 genetics-sweep, 6 lead-atlas)
.venv/bin/python pipelines/alphacognition/test_facet_guardrails.py
    → 12/12 passed; 4 of the 12 fail when the eligibility guard is stubbed permissive
.venv/bin/python pipelines/alphacognition/build_assessments.py
    → 27 targets assessed, 0 facets left without cited evidence
.venv/bin/python scripts/fetch_source_metadata.py --agent alphacognition
    → 58/58 sources verified
.venv/bin/python graph/validate_graph.py --strict
    → 0 violations in alphacognition-owned files (2 remain repo-wide, other agents' lanes)
.venv/bin/python scripts/check_ownership.py --agent alphacognition
    → 119 flags attributable to this agent, all UNCLAIMED-path (see §6), 0 lane violations
```

`--offline` was exercised on **all three** network pipelines and reproduced the online output
exactly — including after the `endpoint_measured` migration, which was applied by editing the
generators and rebuilding from snapshots with no network. That is the P7 guarantee actually
tested rather than asserted. **`pytest` was not run** (not this agent's lane).

---

## 4. Facet-level distribution, all 27 targets

Supporting level (`level`) and contradicting level (`counter_level`) are graded separately, so
both are given. All 27 targets, four genetics facets:

| Facet | lvl 0 | 1 | 2 | 3 | 4 | counter 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|---|---|
| `human_genetic_association` | 0 | 18 | 1 | 8 | 0 | 27 | 0 | 0 | 0 |
| **`causal_gene_attribution`** | **17** | **4** | **6** | **0** | **0** | 23 | 0 | 4 | 0 |
| `human_phenotype_specificity` | 1 | 17 | 9 | 0 | 0 | 27 | 0 | 0 | 0 |
| `adult_expression_and_timing` | 0 | 1 | 25 | 1 | 0 | 26 | 0 | 1 | 0 |

Lead-atlas facets, 6 targets only (the other 21 carry `facets_not_owned_by_this_agent` naming
these six):

| Facet | lvl 0 | 1 | 2 | 3 | counter 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|---|
| `mechanistic_causal_perturbation` | 0 | 2 | 2 | 2 | 1 | 3 | 1 | 1 |
| `adult_onset_perturbation` | 0 | 2 | 3 | 1 | 4 | 1 | 1 | 0 |
| `above_baseline_enhancement` | 2 | 1 | 2 | 1 | 1 | 0 | 4 | 1 |
| `transfer_breadth` | 4 | 2 | 0 | 0 | 2 | 3 | 1 | 0 |
| `dose_response_knowledge` | 2 | 2 | 1 | 1 | 6 | 0 | 0 | 0 |
| `human_intervention_evidence` | 5 | 0 | 0 | 1 | 4 | 0 | 0 | 2 |

The two `counter_level: 3` entries on `human_intervention_evidence` are GRM5 and HTR2A — both at
`level: 0`. `human_phenotype_specificity` shows `counter 0` for all 27 because the pleiotropy
counts that would argue against cognition-specificity have no claim record to cite; under the
rule that contradicting evidence must be *identified* rather than described, those observations
were moved into `limiting_factor` and the counter-grade returned to 0 rather than resting on
uncited evidence. Every `level: 0` grade carries a `search_basis` naming what was searched, at
what scope, and what would have counted as a hit.

**`human_intervention_evidence` is level 0 for five of six targets.** For GRM5 and HTR2A that
level 0 sits beside `counter_level: 3` — large randomised human data exist and they are negative.
CHRM1 is the single level 3 (HTL0018318 in healthy adults).

---

## 5. R5 audit: measured absence versus absence of measurement

Requested explicitly by the coordinator. Every counter-grade was re-checked; two were wrong and
are corrected.

| Target | Facet | Category | Action |
|---|---|---|---|
| **GRM5** | `human_intervention_evidence` | **measured** | FXLEARN measured the primary Weighted Communication Scale *and* all secondary cognitive and language measures and found no between-group difference. `level: 0` / `counter_level: 3` **stands**, and `NO_DETECTED_EFFECT_ON` is legitimate under V16c. |
| **HTR2A** | `human_intervention_evidence` | **measured** | Two randomised healthy-adult studies: one measured impairment of control and cognition (dose-dependently increased), one measured cognitive empathy and moral decision-making (unchanged). `level: 0` / `counter_level: 3` **stands**. |
| **CHRM1** | `human_intervention_evidence` | **evidence gap** | The three xanomeline-trospium psychosis trials measured PANSS and adverse events and **measured no cognitive endpoint at all**. An approval in an indication with no cognitive endpoint says nothing either way. `counter_level` **corrected 1 → 0**; the point moved to `limiting_factor` as a coverage gap. |
| **GRIN2B** | `human_intervention_evidence` | **evidence gap** | The only treatment-adjacent human statement is that an objectifiable beneficial memantine response in GRIN2B patients *remains to be demonstrated* — an absence of measurement. `counter_level` **corrected 1 → 0**; moved to `limiting_factor`. |
| CRTC1, DRD1 | `human_intervention_evidence` | **no human study at all** | Already `level: 0` / `counter_level: 0` with the absence stated. Unchanged. |

All other surviving counter-grades rest on measured endpoints (CHRM1:005 rodent knockout memory
tasks; GRIN2B:004/:005 clinical phenotype; DRD1:001 dose-response; CRTC1:001 context specificity;
GRM5:002 memory; the generated facets' pleiotropy and competing-L2G counter-grades).

**Fully migrated.** When the audit was done, `endpoint_measured` and `evidence_gap` existed in
`ontology/vocabularies.yaml` but not in `schemas/evidence.schema.json`, and writing the field
failed V1. The determinations were parked in `note` strings behind an `endpoint_measured: `
prefix; the schema landed later in the session and they were **promoted into the real field**.
Final census over all 234 evidence items: **189 `measured`, 42 `not_measured_in_protocol`, 3
`unknown`**. All 42 unmeasured items sit inside `evidence_gap` claims, as rule V16c requires.

Two further consequences were applied:
* **`NO_DETECTED_EFFECT_ON` is now used for both measured cognitive nulls** —
  `CLM:alphacognition:GRM5:001` (`negated_relation: CHANGES_STATE`) and
  `CLM:alphacognition:HTR2A:003` (`negated_relation: MODULATES`). The second had been an ordinary
  `MODULATES` edge with `direction: no_change`, which would have let a measured human null compile
  as an ordinary edge and drift the graph positive.
* **24 `evidence_gap` claims** were generated (`pipelines/alphacognition/build_coverage_gaps.py`)
  so that every `level: 0` grade points at a record naming the search performed and what it did
  not contain, instead of at an empty `claim_refs`. 18 are genetics-sweep gaps (a seed gene with
  no cognitive-trait association *and* no cognitive-trait L2G candidacy, sourced to the two pinned
  database releases); 6 are lead-atlas literature gaps sourced to the target's own primary study
  with `endpoint_measured: not_measured_in_protocol` — because the honest statement is not "no
  paper exists" but "the studies that do exist did not measure this".

---

## 6. What could not be done, and why

1. **Adult brain cell-type expression — deferred to Q003, not attempted and not faked.** No Allen
   Brain Cell Atlas / Human Brain Cell Atlas ingestion exists. Named in `limiting_factor` on all 27
   `adult_expression_and_timing` facets; level 4 unreachable in consequence.
2. **Developmental timing — not ingested.** No BrainSpan/PsychENCODE. The single developmental
   claim (`CLM:alphacognition:GRIN2B:006`) comes from a retrieved publication, is rodent, is
   indirect, and is graded level 1 and labelled as such. No developmental statement anywhere is
   inferred from adult GTEx values.
3. **AlphaGenome — interface only.** `ALPHAGENOME_API_KEY` is absent from this environment. The
   design (fail-loud `AlphaGenomeUnavailable`, snapshot layout keyed on model version, derived
   table labelled `derived_from: alphagenome`) is specified in
   `docs/ALPHACOGNITION_ARCHITECTURE.md` §3 stage 4 and **no module was written that could
   produce a number**. Nothing imputes, zero-fills or placeholders a prediction.
4. **Brain eQTL/sQTL beyond Open Targets — not ingested.** PsychENCODE/MetaBrain access not
   verified from this machine. Stage 5 in the architecture doc; `Q002` territory.
5. **Safety liabilities — deliberately not ingested.** Open Targets `safetyLiabilities` is
   reachable and returns PMIDs (GRIN2B → convulsions, dizziness, pain). It belongs to
   `agent:red_team`, and the right move is to register those PMIDs as sources rather than cite
   "Open Targets says so". The GRIN2B dossier's seizure/excitotoxicity liability is flagged in
   `open_questions` as asserted from pharmacology and **not** backed by a claim here.
6. **`far_transfer`, `metacognition`, `learning_rate` are unreachable from genetics.** No GWAS
   trait vocabulary term corresponds to them. Those facets must stay `not_assessed`, never
   inferred from a correlated endpoint.
7. **Ownership flags (119, all path-assignment, 0 lane violations):** 118 files under
   `data/raw/opentargets_genetics/**` and 1 under `data/raw/chembl/**` report `UNCLAIMED`.
   `data/raw/opentargets/**` belongs to `agent:integration`, so the genetics snapshots needed their
   own directory; the ChEMBL directory holds the release snapshot that rule V9 requires to justify
   the numeric fields on intervention records. Requested in
   `docs/blackboard/schema_change_requests/alphacognition-001.yaml` item 6. `data/interim/` is no
   longer flagged (item 5 fixed upstream).
8. **`SRC:GCST:*` remains unverifiable** against GWAS Catalog REST v2 (no `publication` object;
   `disease_trait` not `reported_trait`). Worked around by registering study PMIDs, which contract
   §3 prefers anyway. Request item 2, still open, not blocking.

---

## 7. What the red team should attack first

1. **The nine level-3 `human_genetic_association` grades.** Each rests on catalogued associations
   whose gene attribution is positional. Check that no downstream consumer reads level 3 on that
   facet as "this gene affects intelligence". The rule that produced them is in
   `pipelines/alphacognition/build_assessments.py`'s docstring — attack the rule, not just the
   outputs.
2. **`CLM:alphacognition:CHRM1:001` — the only healthy-adult human cognitive result in the
   repository, and therefore the highest-leverage single citation.** It is a single unreplicated
   study, the cognitive endpoints were *exploratory pharmacodynamics in a safety and
   pharmacokinetics trial* (multiplicity uncontrolled), several authors are affiliated with the
   developer, and its effect size is recorded only as the authors' phrase *"moderate to large
   effect sizes"*. Run `citation_dependence` and `publication_bias` on it. If it does not hold,
   CHRM1's level 3 on three facets falls with it.
3. **`CLM:alphacognition:GRIN2B:001` (Tang 1999) — the most over-cited result in the
   genetic-enhancement literature.** Two independent rodent studies agree on direction, and the
   human evidence for perturbing the same gene is a neurodevelopmental encephalopathy
   (`GRIN2B:004`, 86 patients, both gain- and loss-of-function). Check
   `animal_memory_mistaken_for_human_intelligence` and
   `developmental_effect_mistaken_for_adult`; the abstract's own closing sentence proposes human
   genetic enhancement from a mouse experiment, which is recorded as the authors' inference.
4. **Single-cohort dependence.** Reaction time, verbal-numerical reasoning and educational
   attainment are all UK Biobank-dominated, so two "independent" associations can be the same
   cohort twice. Group `data/interim/gwas_catalog_associations.jsonl` by
   `initial_sample_size_as_reported` + `first_author`, and
   `data/interim/opentargets_l2g.jsonl` by `study_id` + `n_samples`. Claim-level
   `provenance.supporting_pubmed_ids` / `supporting_study_ids` allow the same grouping per claim.
   **Nothing in this atlas de-duplicates cohorts.**
5. **Ancestry.** Every cognitive study retrieved is European-ancestry-dominated
   (`nfe`, relative sample size 1 in Open Targets' `ldPopulationStructure`; GWAS Catalog
   `discovery_ancestry` strings are per-claim in `risks`). Fine-mapped credible sets inherit that
   LD structure, so the L2G assignments do too.
6. **Rescue versus enhancement on CHRM1 and CRTC1.** `CHRM1:002` (xanomeline in Alzheimer
   disease, cholinergic denervation) and `CRTC1:002` (gene therapy in a presenilin knockout) are
   both `supra_normal: rescue_only` and are exactly the records most likely to be miscited as
   enhancement. `CHRM1:003` records that the dose which produced the cognitive signal is the dose
   that produced 52% discontinuation and 12.6% syncope.
7. **`DRD1` and the ranking model.** `dose_response_knowledge` level 3 is DRD1's *strength*, and
   the finding it encodes is an **inverted U** — impairment at both low and high stimulation. A
   ranking rule that rewards "how far can this state variable be pushed" will rank DRD1 well for
   the wrong reason. Check `dose_response_inversion`.
8. **`HTR2A` liability.** The liability list comes only from the acute human study's own reported
   effects (anxiety, ego dissolution, blood pressure, heart rate). A systematic psychiatric-liability
   search — persisting perceptual changes, psychosis risk — was **not** run by this agent.
   `SV:safety.psychosis_risk` is deliberately *not* asserted because psychosis was not measured.
9. **The generated-facet rule itself — you already found one bug here, and the fix may have its
   own.** See §0. The rule is now in two pure functions with 12 tests and a generation-time
   divergence check, but the mapping from evidence pattern to ordinal level is still one agent's
   curatorial decision applied 108 times identically. Two judgement calls in the fix are worth
   attacking: (a) `causal_gene_attribution` now returns **0**, not 1, when the only L2G candidacy
   is on a `supporting`/`proxy_only` trait — I decided that partially resolving the gene behind
   an EA signal is not partial resolution of an intelligence signal, which loses the information
   that fine mapping did happen there (it survives in the rationale); (b) `supporting` traits
   corroborate but never raise a level, so a gene with five supporting-trait associations and no
   primary one scores the same as a gene with none.
10. **Registry coverage — this atlas has run no ClinicalTrials.gov *search*.** Noted from your
   report that three of four atlases never ran one and that four of your five headline findings
   came from `whyStopped` and `resultsSection`, which no literature search returns. This atlas
   fetched two NCT records **by id** (NCT02920892, NCT03604744) and never queried
   `filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED` for any target. So every `level: 0` on
   `human_intervention_evidence` here — CRTC1, DRD1, GRIN2B, GRM5, HTR2A — carries the same
   exposure `agent:power` had when it overturned two of its own statements. A terminated M1,
   D1 or mGluR5 cognition trial with an informative `whyStopped` would change those grades and
   would not have been found by anything this atlas ran. Queued as the first Sprint-2 action.

---

## 8. What other agents need to know

* **`agent:integration`:** `causal_gene_attribution` has no level 3 or 4 anywhere, so any D1
  aggregation that assumes gene-resolved genetic evidence exists will find none. `evidence_basis`
  counts are in each assessment's `notes` as prose, not as numeric fields (rule V9); the machine
  numbers are in `data/interim/*.jsonl`. L2G and colocalisation values live only in
  `uncertainty.model_outputs[]` with `derived_from` + `data_version` and must not be thresholded.
  `SRC:DB:opentargets:26.06`'s `title` in this atlas was adopted **verbatim** from your
  registration so V4 sees one unambiguous identifier; this atlas used the genetics endpoints, not
  the target-annotation ones, and says so in the record's `notes`.
* **`agent:ontology`:** `NO_DETECTED_EFFECT_ON` + `negated_relation` solved request item 3 and are
  in use on both measured nulls; `endpoint_measured` is written on all 234 evidence items;
  `search_basis` is written on every `level: 0` grade. Two notes from using them: (a) the
  assessed-facet-must-cite-evidence rule and `level: 0` meaning "searched, nothing found" are in
  tension unless an agent generates `evidence_gap` records — worth saying so in the contract,
  because the alternative an agent reaches for is a tangential citation or a quiet downgrade to
  `not_assessed`; (b) `translation.human_relevance` has no value for a record *about* a gap, so
  the gap claims take the human_relevance of the study whose protocol is being described.
* **`agent:comparative`:** every claim here carries `context.species` with taxids resolved at
  runtime from NCBI (`SPECIES:NCBITaxon:9606`, `:10090`, `:10116`) — never hand-written — and
  `translation.human_relevance` on all 125 claims.
* **`agent:brakes` / `agent:power`:** the four genetics facets are filled in for all your targets
  too, in `atlases/alphacognition/assessments/{SYMBOL}.yaml`, with
  `facets_not_owned_by_this_agent` listing the six lead-atlas facets left for you. GABRA5, HCN1,
  OTX2, PDE4B, GPR158, HDAC2, CKB, SLC16A7, EIF2S1 and EIF2B4 all have L2G candidacy worth
  reading; KCNQ3 has a cognitive-trait association but no L2G candidacy.

---

## 9. Artefact index

```
atlases/alphacognition/cognitive_trait_panel.yaml      24 EFO terms, 22 queried
atlases/alphacognition/sources_curated.yaml            23 authored source records
atlases/alphacognition/lead_atlas_facets.yaml          6 targets × 6 hand-written facets
atlases/alphacognition/assessments/{SYMBOL}.yaml       27 files (generated)
atlases/alphacognition/interventions/*.yaml            11 records (9 compounds, 2 mechanisms)
evidence/sources/alphacognition.yaml                   58 records, assembled, all verified
evidence/claims/alphacognition/{GRIN2B,CRTC1,CHRM1,GRM5,DRD1,HTR2A}.yaml   21 hand-curated claims
evidence/claims/alphacognition/{gwas_catalog,opentargets_l2g,expression}_derived.yaml  104 machine claims
targets/candidates/{GRIN2B,CRTC1,CHRM1,GRM5,DRD1,HTR2A}.yaml               6 dossiers
evidence/claims/alphacognition/coverage_gaps.yaml                          27 evidence_gap claims
pipelines/alphacognition/{_common,fetch_gwas_catalog,fetch_gene_pleiotropy,
                          fetch_opentargets_genetics,fetch_expression,
                          build_sources,build_coverage_gaps,
                          build_assessments}.py                            8 modules
pipelines/alphacognition/test_facet_guardrails.py                          12 guardrail tests
data/interim/{gwas_catalog_associations,gwas_catalog_gene_pleiotropy,
              opentargets_l2g,adult_brain_expression}.jsonl                4 derived tables
data/raw/{gwas_catalog,opentargets_genetics,gtex,chembl}/2026-09-17/       immutable snapshots
docs/ALPHACOGNITION_ARCHITECTURE.md                    v0.2+ design, warnings, AlphaGenome interface
docs/blackboard/schema_change_requests/alphacognition-001.yaml             7 items, 2 resolved
```
