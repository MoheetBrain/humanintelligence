# Data Contract v0.1.0 — Intelligence Blueprint

**Status:** authoritative for Sprint 1. Frozen once the Ontology/Graph Architect has
formalised it into `ontology/`, `schemas/` and the validators; after that, changes go
through `docs/blackboard/schema_change_requests/`.

This document is the single shared contract between all agents working on this
repository. Every curated record must conform to it. The validator
(`graph/validate_graph.py`) is the executable form of this document; where the two
disagree, that is a bug to be reported, not a licence to improvise.

---

## 0. Non-negotiable principles

| # | Principle | Mechanism |
|---|-----------|-----------|
| P1 | **Computational only.** No wet-lab, in-vitro, ex-vivo, animal or human experiment is performed, planned or requested by this project. External experimental results may be *ingested as evidence*. | `docs/COMPUTATIONAL_ONLY_POLICY.md`, `action_type` enum in `docs/TASK_DAG.yaml`, red-team check `proposes_prohibited_work` |
| P2 | **Every substantive biological claim carries provenance.** A claim without at least one evidence item bound to a registered, machine-verified source is invalid. | validator rules V5–V8 |
| P3 | **No fake precision.** Hand-written numeric probabilities/scores are forbidden anywhere in curated records. Numbers appear only (a) as effect sizes copied from a source (`as_reported`), or (b) as outputs of a named model implementation under `models/`. | validator rule V9 |
| P4 | **Association ≠ causation; locus ≠ gene; development ≠ adulthood; rescue ≠ enhancement; animal memory ≠ human intelligence; education ≠ intelligence.** Each distinction is a *required field*, not a prose caveat. | `claim_type`, `causal_attribution`, `life_stage`, `baseline_context`, `endpoint_category`, `phenotype_class` |
| P5 | **Paper count is not evidence quality.** Ranking consumes ordinal, rubric-defined evidence levels and is tested to be invariant to duplicated evidence. | `models/ranking/ranking_spec_v0_1.yaml`, `tests/test_ranking_invariance.py` |
| P6 | **The red team can downgrade, never delete.** Provenance is append-only; withdrawal is a status change with a reason, never a deletion. | validator rules V12–V14, `evidence/claims/claim_registry.lock` |
| P7 | **Reproducible and offline-rebuildable.** Network steps write immutable snapshots to `data/raw/`; every derived artefact is rebuilt from those snapshots with no network. | `Makefile`, `data/raw/MANIFEST.jsonl`, `tests/test_raw_immutability.py` |
| P8 | **Unknown is a first-class value.** `unknown` / `not_assessed` must never be silently coerced to zero, and must widen uncertainty rather than lower a score by stealth. | `models/uncertainty/`, `coverage` columns in reports |

---

## 1. Identifier conventions

All node identifiers are `PREFIX:local_id`. `local_id` is `[A-Za-z0-9._:+-]+`.
Prefixes are closed: a new prefix requires an ontology change.

### 1.1 Biological causal layer

| Prefix | Node types allowed | Local id form | Example |
|--------|-------------------|---------------|---------|
| `GENE` | Gene | HGNC-approved symbol (uppercase) | `GENE:GABRA5` |
| `VAR` | Variant | dbSNP rsID, or `chr{c}_{pos}_{ref}_{alt}` (GRCh38) | `VAR:rs141426703` |
| `TX` | Transcript | Ensembl transcript id | `TX:ENST00000370447` |
| `PROT` | Protein, Receptor, IonChannel, Transporter, Enzyme | UniProt accession preferred, else gene symbol | `PROT:P31644` |
| `COMPLEX` | Protein complex (multi-gene functional unit) | snake_case slug | `COMPLEX:eif2b` |
| `PROC` | MolecularProcess | `GO:` id preferred, else snake_case slug | `PROC:GO:0006413` |
| `PATHWAY` | Pathway | `REACT:` id preferred, else slug | `PATHWAY:REACT:R-HSA-72613` |
| `CELL` | CellType | Cell Ontology `CL:` id preferred, else slug | `CELL:CL:0000679` |
| `REGION` | BrainRegion | `UBERON:` id preferred, else slug | `REGION:UBERON:0001954` |
| `CIRCUIT` | Circuit | snake_case slug | `CIRCUIT:ca3_ca1_schaffer_collateral` |
| `NET` | Network | snake_case slug | `NET:frontoparietal_control` |
| `SV` | StateVariable | `{domain}.{name}` (domain ∈ state_model files) | `SV:plasticity.ltp_threshold` |
| `PRIM` | ComputationalPrimitive | snake_case name from `ontology/computational_primitives.yaml` | `PRIM:pattern_separation` |
| `PHENO` | CognitivePhenotype | snake_case slug | `PHENO:general_cognitive_ability` |
| `SPECIES` | Species | `NCBITaxon:{taxid}` (taxid resolved via NCBI, never from memory) | `SPECIES:NCBITaxon:9606` |

### 1.2 Intervention layer

| Prefix | Node types | Local id form | Example |
|--------|-----------|---------------|---------|
| `TGT` | Target | gene symbol or complex slug | `TGT:GABRA5` |
| `CPD` | Compound (research probe, not approved drug) | `CHEMBL{n}` preferred, else slug | `CPD:CHEMBL1234567` |
| `DRUG` | Drug (approved somewhere for some indication) | `CHEMBL{n}` preferred, else INN slug | `DRUG:caffeine` |
| `BIO` | Biologic | slug | `BIO:klotho_protein` |
| `RNAI` | RNAIntervention | slug | `RNAI:shrna_hdac2` |
| `GREG` | GeneRegulation | slug | `GREG:aav_crtc1_overexpression` |
| `METAB` | MetabolicIntervention | slug | `METAB:creatine_monohydrate_supplementation` |
| `NTECH` | Neurotechnology | slug | `NTECH:tdcs_dlpfc` |
| `MECH` | Mechanism | slug | `MECH:alpha5_gabaa_negative_allosteric_modulation` |
| `EFFECT` | DesiredEffect | slug | `EFFECT:increased_working_memory_capacity` |
| `AE` | AdverseEffect | slug (MedDRA-like plain term) | `AE:seizure` |

### 1.3 Evidence layer

| Prefix | Node type | Local id form | Example |
|--------|-----------|---------------|---------|
| `SRC:PMID` | Paper | PubMed id | `SRC:PMID:29942086` |
| `SRC:DOI` | Paper / Preprint | DOI (lowercased) | `SRC:DOI:10.1101/2021.01.01.425001` |
| `SRC:NCT` | ClinicalTrial | NCT id | `SRC:NCT:NCT02024789` |
| `SRC:GCST` | Dataset (GWAS Catalog study) | GCST accession | `SRC:GCST:GCST006269` |
| `SRC:DB` | DatabaseRelease | `{db}:{release}` | `SRC:DB:gwas_catalog:2026-09-13` |
| `SRC:DATASET` | Dataset (other) | slug | `SRC:DATASET:gtex_v8_brain` |
| `CLM` | Claim | `{domain}:{target_or_topic}:{nnn}` | `CLM:brakes:GABRA5:001` |
| `EVD` | Measurement / Experiment (evidence item) | `{claim_local}#{n}` — derived, not hand-written | `EVD:brakes:GABRA5:001#1` |
| `AUD` | Audit | `{auditor}:{scope_slug}:{nnn}` | `AUD:red_team:GABRA5:001` |

Preferred source ranking: PMID > DOI > NCT > GCST. A paper that has a PMID **must**
be registered under its PMID (prevents the same paper appearing twice under two ids).

---

## 2. Record types, owners and locations

| Record | Path pattern | Format | Written by |
|--------|--------------|--------|-----------|
| Source registration | `evidence/sources/{agent}.yaml` | YAML list | each agent, own file only |
| Claim | `evidence/claims/{agent}/{TARGET_OR_TOPIC}.yaml` | YAML list | each agent, own dir only |
| Audit | `evidence/audits/{auditor}/{TARGET_OR_TOPIC}.yaml` | YAML list | red team only |
| Target dossier | `targets/candidates/{TARGET_ID_LOCAL}.yaml` | YAML doc | lead atlas for that target |
| Seed registry | `targets/seed_registry.yaml` | YAML doc | orchestrator only |
| Facet assessment | `atlases/{domain}/assessments/{TARGET_ID_LOCAL}.yaml` | YAML doc | domain agent for its own facets |
| Intervention entity | `atlases/{domain}/interventions/{ID_LOCAL}.yaml` | YAML doc | domain agent that cites it |
| State-variable annotation | `atlases/{domain}/state_variable_annotations.yaml` | YAML list | domain agent |
| State-variable definition | `state_model/{domain}.yaml` | YAML doc | ontology architect |
| Ontology | `ontology/*.yaml` | YAML doc | ontology architect |
| Definitional edges | `ontology/definitional_edges.yaml` | YAML list | ontology architect |
| Raw API snapshot | `data/raw/{source}/{YYYY-MM-DD}/*.json` | JSON | any agent, append-only |
| Derived tables | `data/interim/`, `data/processed/` | JSONL/Parquet/DuckDB | code only, never hand-edited |

Ownership is enforced by `scripts/check_ownership.py` against `docs/OWNERSHIP.yaml`.

---

## 3. Source record

```yaml
- source_id: SRC:PMID:29942086
  source_type: journal_article      # journal_article | review | meta_analysis | systematic_review
                                    # | preprint | clinical_trial_registration | dataset
                                    # | database_release | book_chapter | regulatory_document
  title: "Genome-wide association meta-analysis in 269,867 individuals identifies new genetic and functional links to intelligence."
  year: 2018                        # publication year as printed
  first_author: "Savage JE"         # surname + initials, or organisation for datasets
  container: "Nat Genet"            # journal / registry / database name
  identifiers:
    pmid: "29942086"
    doi: "10.1038/s41588-018-0152-6"
  added_by: agent:alphacognition
  added_on: "2026-09-17"            # ISO date, UTC
  retrieval:
    method: pubmed_search           # pubmed_search | pubmed_metadata | ctgov_api | gwas_catalog_api
                                    # | opentargets_api | hgnc_api | known_identifier
```

Rules:

* `title`, `year`, `first_author`, `container` are what the agent *believes*; they are
  then **machine-checked** against the registry snapshot (§7). A mismatch is a hard
  validation failure, not a warning. This is the anti-fabrication mechanism: an
  invented PMID either fails to resolve or resolves to a different title.
* Never paste abstracts or any passage from a source into this repository. Store
  identifiers, titles and your own one-sentence paraphrase only.

---

## 4. Claim record

A claim is one machine-readable assertion plus the evidence for it. The triple
`(subject, predicate, object)` **must** be a legal edge in `ontology/edges.yaml`.

```yaml
- claim_id: CLM:brakes:GABRA5:001
  statement: >-
    One-sentence paraphrase in the agent's own words, stating who measured what in
    which species and what changed. No quoted source text.
  subject: GENE:GABRA5            # node id; node must be declarable under the ontology
  predicate: NEGATIVELY_REGULATES # from ontology/edges.yaml
  object: SV:plasticity.ltp_threshold
  claim_type: causal_perturbation # see §4.1
  direction: decreases            # increases | decreases | no_change | bidirectional
                                  # | inverted_u | u_shaped | unclear
  context:
    species: [SPECIES:NCBITaxon:10090]
    life_stage: adult             # prenatal | postnatal_developmental | adolescent | adult
                                  # | aged | mixed | not_reported
    baseline_context: healthy_wildtype   # healthy_wildtype | disease_model | disease_population
                                  # | sleep_deprived_or_stressed | aged | mixed | not_reported
    brain_regions: [REGION:UBERON:0001954]
    cell_types: []
  phenotype_class: animal_memory_task    # see §4.2 — mandatory whenever object is a
                                  # CognitivePhenotype or a cognitive StateVariable
  causal_attribution:             # mandatory for every claim
    basis: adult_pharmacological_perturbation  # see §4.3
    locus_to_gene_resolved: not_applicable     # yes | no | partial | not_applicable
    alternative_explanations: ["off-target activity at other GABA-A subtypes not excluded"]
  evidence:
    - source_id: SRC:PMID:xxxxxxxx
      design: pharmacological_perturbation     # see §4.4
      species: SPECIES:NCBITaxon:10090
      population: "adult male C57BL/6J mice"
      sample_size:
        reported_as: "n = 10 per group"        # verbatim from the source, or null
        value: 10                              # integer or null — never estimated
        unit: animals
      endpoint: "novel object recognition discrimination index"
      endpoint_category: animal_recognition_memory   # see §4.2
      effect_direction: increase                # increase | decrease | no_change | mixed | not_reported
      effect_size:
        metric: not_extracted                   # not_extracted | beta | odds_ratio | hazard_ratio
                                                # | cohens_d | smd | correlation_r | percent_change
                                                # | p_value_only | mean_difference
        as_reported: null                       # verbatim string from the source, or null
        value: null                             # only if as_reported gives it explicitly
        ci_lower: null
        ci_upper: null
        p_value: null
      replication_status: single_study          # single_study | replicated_independent
                                                # | replicated_same_group | failed_replication
                                                # | conflicting | not_assessed
      evidence_role: supports                   # supports | contradicts | qualifies | null_result
      extraction:
        basis: abstract                         # abstract | full_text | database_record
                                                # | registry_record | secondary_report
        extracted_by: agent:brakes
        extracted_on: "2026-09-17"
        content_checked: true                   # false ⇒ red team downgrades automatically
  translation:
    adult_relevance: demonstrated_in_adults     # demonstrated_in_adults | plausible_untested
                                                # | developmental_only | contradicted | unknown
    healthy_baseline: tested_in_healthy         # tested_in_healthy | disease_model_only
                                                # | deficit_state_only | mixed | unknown
    supra_normal: enhancement_above_healthy_baseline  # enhancement_above_healthy_baseline
                                                # | rescue_only | no_enhancement_observed
                                                # | contradicted | untested
    human_relevance: rodent_only                # direct_human_interventional | human_genetic
                                                # | human_observational | nonhuman_primate
                                                # | rodent_only | other_species_only
                                                # | in_vitro_only | computational_only
    general_intelligence_relevance: animal_task_only  # g_or_fluid_measured | multi_domain_cognitive
                                                # | single_domain_cognitive
                                                # | educational_attainment_proxy
                                                # | animal_task_only | none | unknown
  uncertainty:
    representation: ordinal_grade               # ordinal_grade only in curated records
    scale: evidence_strength_v1                 # defined in models/uncertainty/
    level: 2                                    # integer 0..4, rubric-defined
    rationale: "single rodent study, no replication, healthy baseline"
    calibration_status: uncalibrated_subjective # uncalibrated_subjective | model_derived_uncalibrated
                                                # | empirically_calibrated
  risks: ["sedation confound not excluded"]
  confounders: ["arousal", "locomotor activity"]
  dependencies: []                              # claim_ids this claim's interpretation relies on
  status: active                                # active | contested | downgraded | withdrawn
  provenance:
    created_by: agent:brakes
    created_on: "2026-09-17"
    method: literature_curation                 # literature_curation | database_ingestion
                                                # | derived_from_claims
    run_id: sprint1-brakes-01
```

### 4.1 `claim_type`
`association` · `causal_perturbation` · `mechanistic` · `expression` · `pharmacology_binding`
· `pharmacodynamic` · `clinical_efficacy` · `clinical_null` · `clinical_harm` · `safety`
· `comparative_evolutionary` · `theoretical_construct` · `methodological`

### 4.2 `phenotype_class` / `endpoint_category`
Human: `g_factor` · `fluid_reasoning` · `working_memory` · `processing_speed`
· `episodic_memory` · `executive_function` · `learning_rate` · `far_transfer`
· `metacognition` · `educational_attainment` · `clinical_cognitive_composite`
· `neuroimaging_proxy` · `electrophysiological_proxy` · `metabolic_proxy`.
Non-human: `animal_spatial_memory` · `animal_recognition_memory` · `animal_fear_conditioning`
· `animal_reversal_learning` · `animal_working_memory` · `animal_operant_task`
· `synaptic_plasticity_ltp_ltd` · `cellular_excitability` · `molecular_readout`.
Other: `not_applicable` · `not_reported`.

**`educational_attainment` is never treated as an intelligence endpoint.** The ranking
spec weights it separately and lower.

### 4.3 `causal_attribution.basis`
`gwas_association_only` · `gene_based_association` · `finemapped_credible_set`
· `colocalisation_qtl` · `mendelian_randomisation` · `rare_variant_burden`
· `monogenic_disorder` · `germline_knockout` · `conditional_developmental_knockout`
· `adult_inducible_genetic_perturbation` · `adult_pharmacological_perturbation`
· `acute_circuit_perturbation` · `human_randomised_intervention`
· `human_observational_association` · `in_vitro_perturbation` · `correlational_expression`
· `computational_prediction` · `theoretical_argument`

### 4.4 `evidence.design`
`gwas` · `gwas_meta_analysis` · `gene_based_test` · `fine_mapping` · `eqtl` · `sqtl`
· `colocalisation` · `mendelian_randomisation` · `polygenic_score_analysis`
· `rare_variant_association` · `clinical_case_series` · `rct_parallel` · `rct_crossover`
· `open_label_trial` · `observational_cohort` · `case_control` · `meta_analysis`
· `systematic_review` · `narrative_review` · `knockout` · `conditional_knockout`
· `knockdown` · `overexpression` · `pharmacological_perturbation` · `optogenetic`
· `chemogenetic` · `electrophysiology` · `in_vivo_imaging` · `expression_atlas`
· `single_cell_atlas` · `comparative_genomics` · `comparative_anatomy`
· `phylogenetic_comparative_analysis` · `biophysical_model` · `simulation`
· `registry_record` · `database_release`

---

## 5. Target dossier and facet assessment

### 5.1 Target dossier (`targets/candidates/{SYMBOL}.yaml`)

```yaml
target_id: TGT:GABRA5
symbol: GABRA5
lead_atlas: brakes
seed_origin: user_seed_list          # user_seed_list | agent_proposed
dossier_depth: deep                 # deep | shallow  (declared, then checked)
identifiers:                         # MACHINE-FILLED from HGNC — leave {} when authoring
  hgnc_id: null
  ensembl_gene_id: null
  uniprot_ids: []
  entrez_id: null
  identifier_provenance: null
target_class: receptor_subunit
represented_entities: [GENE:GABRA5, PROT:P31644]
member_genes: []                     # for complexes only
control_point_hypothesis:
  statement: "..."
  proposed_modulation: decrease_activity   # decrease_activity | increase_activity
                                           # | restore_toward_setpoint | context_dependent | unknown
  mechanism_chain: [CLM:..., CLM:...]      # claim ids forming the asserted chain
  state_variables:
    - id: SV:workspace.distractor_resistance
      asserted_relation: modulates
      direction: increases
      response_shape: unknown
      claim_refs: [CLM:...]
  computational_primitives: [PRIM:pattern_separation]
known_liabilities: [AE:seizure]
developmental_confound: high         # high | moderate | low | unknown — with rationale below
developmental_confound_rationale: "..."
open_questions: ["..."]
status: seed_hypothesis              # seed_hypothesis | under_review | downgraded | deprioritised
provenance: {created_by: ..., created_on: ..., run_id: ...}
```

### 5.2 Facet assessment (`atlases/{domain}/assessments/{SYMBOL}.yaml`)

Facets are the *only* place where an agent expresses a graded judgement, and every
grade needs a rubric level, a rationale and claim references.

```yaml
target_id: TGT:GABRA5
assessed_by: agent:brakes
assessed_on: "2026-09-17"
rubric: facet_rubric_v0_1
facets:
  - facet: mechanistic_causal_perturbation
    level: 3
    rationale: "..."
    claim_refs: [CLM:brakes:GABRA5:001, CLM:brakes:GABRA5:004]
    limiting_factor: "no adult-inducible genetic evidence"
```

Facet catalogue and owners (levels 0–4 defined in `models/ranking/facet_rubric_v0_1.yaml`):

| Facet | Owner | Feeds |
|-------|-------|-------|
| `human_genetic_association` | alphacognition | D1 |
| `causal_gene_attribution` | alphacognition | D1 |
| `human_phenotype_specificity` | alphacognition | D1, D4 |
| `adult_expression_and_timing` | alphacognition | D2 |
| `mechanistic_causal_perturbation` | brakes / power / alphacognition (lead atlas) | D1 |
| `adult_onset_perturbation` | lead atlas | D2 |
| `above_baseline_enhancement` | lead atlas | D3 |
| `transfer_breadth` | lead atlas | D4 |
| `dose_response_knowledge` | lead atlas | D5 |
| `human_intervention_evidence` | lead atlas | D6 |
| `cross_species_convergence` | comparative | D6 |
| `human_lineage_divergence_risk` | comparative | D6 (inverse) |
| `safety_liability_burden` | red_team | D5 (inverse) |
| `developmental_confound_risk` | red_team | D2 (inverse, gate) |
| `tractability` | integration (Open Targets data) | D6 |

Dimensions: **D1** P(causal cognition relevance) · **D2** P(adult modifiability) ·
**D3** P(supra-normal potential) · **D4** P(far transfer potential) ·
**D5** P(safe controllable window) · **D6** P(human translation).

A facet with no assessment is recorded as `not_assessed` and handled by the
uncertainty model as *wide and uninformative* — never as zero.

---

## 6. Audit record (red team only)

```yaml
- audit_id: AUD:red_team:GABRA5:001
  scope: {kind: target, id: TGT:GABRA5}      # kind: target | claim | document | model
  audited_by: agent:red_team
  audited_on: "2026-09-17"
  checks:                                     # every check in the catalogue must appear
    - check: association_mistaken_for_causation
      result: flag                            # pass | flag | fail | not_applicable
      note: "..."
      evidence_refs: [SRC:PMID:...]
  findings:
    - finding_id: AUD:red_team:GABRA5:001#f1
      severity: major                         # critical | major | minor | info
      category: negative_clinical_evidence
      description: "..."
      evidence_refs: [SRC:NCT:...]
  adjustments:                                # downgrades only; validator rejects upgrades
    - kind: facet
      target_id: TGT:GABRA5
      facet: above_baseline_enhancement
      from_level: 3
      to_level: 1
      reason: "..."
  claim_status_changes:
    - claim_id: CLM:brakes:GABRA5:002
      from: active
      to: contested
      reason: "..."
  verdict: retain_with_downgrade               # retain | retain_with_downgrade
                                               # | deprioritise | insufficient_evidence
  provenance: {...}
```

Mandatory check catalogue: `association_mistaken_for_causation`,
`developmental_effect_mistaken_for_adult`, `rescue_mistaken_for_enhancement`,
`animal_memory_mistaken_for_human_intelligence`,
`educational_attainment_mistaken_for_intelligence`, `duplicated_evidence`,
`citation_dependence`, `publication_bias`, `negative_clinical_evidence`,
`dose_response_inversion`, `seizure_liability`, `psychiatric_liability`,
`systemic_adverse_effects`, `model_organism_translation_failure`, `overclaiming`,
`provenance_integrity`, `proposes_prohibited_work`.

---

## 7. Source verification artefacts (machine-generated)

`scripts/fetch_source_metadata.py` writes:

* **Immutable raw snapshot** — `data/raw/pubmed_esummary/{YYYY-MM-DD}/{batch_hash}.json`
  and `data/raw/ctgov_v2/{YYYY-MM-DD}/{nct_id}.json`, plus one line per file in
  `data/raw/MANIFEST.jsonl`:
  ```json
  {"path":"data/raw/pubmed_esummary/2026-09-17/ab12cd34.json","sha256":"…","bytes":12345,
   "retrieved_at":"2026-09-17T12:00:00Z","endpoint":"https://eutils.ncbi.nlm.nih.gov/…",
   "query":{"db":"pubmed","id":["29942086"]},"tool":"intelligence-blueprint/0.1.0"}
  ```
* **Verification index** — `data/interim/source_verification.jsonl` (derived, rebuildable
  offline from the snapshots):
  ```json
  {"source_id":"SRC:PMID:29942086","status":"verified","registry":"pubmed",
   "registry_title":"Genome-wide association meta-analysis …","registry_year":2018,
   "registry_container":"Nat Genet","registry_doi":"10.1038/s41588-018-0152-6",
   "title_similarity":0.99,"publication_types":["Journal Article","Meta-Analysis"],
   "retraction_flag":false,"snapshot":"data/raw/pubmed_esummary/2026-09-17/ab12cd34.json"}
  ```
  `status` ∈ `verified` · `title_mismatch` · `year_mismatch` · `not_found` · `not_checked`
  · `retracted` · `unsupported_registry`.

Gene identifiers are resolved the same way by `scripts/fetch_gene_identifiers.py`
(HGNC REST → `data/raw/hgnc/{date}/{symbol}.json` → `data/interim/gene_identifiers.jsonl`).
**Agents never hand-write HGNC/Ensembl/UniProt/taxonomy identifiers.**

---

## 8. Validation rules (the validator must implement all of these)

| ID | Rule |
|----|------|
| V1 | Every record validates against its JSON Schema. |
| V2 | Every node id matches its prefix pattern and the prefix is legal for the node type used. |
| V3 | Every `(subject, predicate, object)` triple is legal per `ontology/edges.yaml` domain/range. |
| V4 | All cross-references resolve: claim→source, assessment→claim, audit→claim/target, dossier→claim, annotation→claim, target→gene. |
| V5 | Every claim has ≥1 evidence item; every evidence item names a registered source. |
| V6 | Every source in `evidence/sources/` has a verification record with `status = verified`; anything else fails `--strict` and is reported per source. |
| V7 | `phenotype_class` is present whenever the object is a CognitivePhenotype or a cognitive StateVariable; `causal_attribution` present on all claims. |
| V8 | `translation.*` fully populated on every claim (no missing keys; `unknown` is allowed and explicit). |
| V9 | No hand-written probability/score: any float in `(0,1)` outside `effect_size`/`p_value`/`as_reported` fields, or any numeric field not accompanied by `derived_from` pointing at an existing file under `models/`, is a failure. |
| V10 | `uncertainty.representation` in curated records is `ordinal_grade` only; `level ∈ {0..4}`. |
| V11 | Facet names, owners and levels conform to the facet catalogue; an agent may only write facets it owns. |
| V12 | Audit `adjustments` satisfy `to_level < from_level` (downgrade only) and reference existing facets/claims. |
| V13 | Every claim id present in `evidence/claims/claim_registry.lock` still exists (no deleted provenance); new ids are appended to the lock by `graph/validate_graph.py --update-lock`. |
| V14 | Withdrawal requires `status: withdrawn` **and** a superseding audit finding; records are never removed. |
| V15 | Every seed target has ≥1 audit record with the full mandatory check catalogue. |
| V16 | No efficacy assertion from binding alone: an edge into `EFFECT:*` or a `CHANGES_STATE` edge needs ≥1 claim with `claim_type ∈ {causal_perturbation, pharmacodynamic, clinical_efficacy}`. |
| V17 | Compiled graph edges each carry `provenance_class ∈ {claim_derived, reference_data, ontology_axiom}` and, when `claim_derived`, ≥1 resolvable claim id. |
| V18 | No secrets: no API keys, tokens or `.env` content in any tracked file. |
| V19 | `data/raw/` checksums match `MANIFEST.jsonl` (immutability). |
| V20 | Prohibited-work policy: no record proposes wet-lab, in-vitro, ex-vivo, animal or human experimentation by this project (`action_type` enums + red-team check). |

---

## 9. Versioning

* This contract: `v0.1.0`. Schema files carry `$id` ending in `/v0_1_0/`.
* Every record carries the `schema_version` of the contract it was written against.
* Breaking changes require a new minor version, a migration note in
  `docs/DECISIONS.md`, and a re-validation run recorded in `docs/PROJECT_LEDGER.md`.
