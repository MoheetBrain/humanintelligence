# Codex ⇄ Claude handoff contract (v1.0)

**Purpose:** let this repository ingest an external agent's analysis **without trusting
its prose summary**. Codex and Claude remain independent scientific agents; this document
is the interface, not a request for agreement on conclusions.

**Status:** normative for X01 (retrospectively) and X02 (prospectively).

What exists, stated precisely, because this document demands artefacts of others and must
meet the same standard:

* **Built and tested** — `schemas/external_analysis.schema.json`, `schemas/x02_*.schema.json`
  (5 files), and `pipelines/integration/ingest_x02.py` with 14 tests in
  `tests/test_x02_ingestion.py`. The X02 adapter validates a delivery end to end; its
  `--emit` path is deliberately unimplemented, because nothing may be written into the
  graph before a real delivery is inspected.
* **Not built** — there is no `ingest_external_analysis.py`. An earlier version of this
  sentence named one; X01 was ingested by hand into a single record, which is what an
  unverified external report warrants. Corrected 2026-09-18 after a red-team pass found
  the reference dangling.

---

## 0. The one rule that generates all the others

**A number without an artefact is not a result.**

Claude's evidence contract (`docs/DATA_CONTRACT.md`, principle P2) binds every
substantive claim to a machine-verified source. An external analysis is no exception,
and being external makes it stricter rather than looser: Claude did not watch the
analysis run, so the artefact is the only thing that can be checked. A prose figure —
"β ≈ 0.097, nominal P ≈ 0.011" — has nothing to verify against, cannot fail a check, and
will be recorded as `unverified_external_report`: visible, attributed, and **inert**. It
will not support a facet grade, will not create a biological-layer edge, and will not
move a target's rank.

This is not a judgement about Codex's competence. The same rule applied to Claude's own
agents in Sprint 1, where it caught five contract defects and one silent data-loss bug,
and where it forced an atlas to overturn two of its own published statements.

## 1. Delivery mechanism (any one)

1. **Push the branch** to `origin` (preferred). Never force-push a branch Claude has
   audited.
2. **`git bundle`** — `git bundle create astra.bundle <branch>` plus the bundle's sha256.
3. **A path to a local clone**, read-only.

Claude will not rebase, cherry-pick or rewrite Codex history. Ingestion is additive:
Codex's artefacts are copied into `analyses/external/<analysis_id>/` with provenance,
and Codex's branch remains the source of record.

## 2. Universal requirements (every delivered analysis)

A manifest at the analysis root, `analysis_manifest.json`:

```json
{
  "analysis_id": "X02",
  "title": "GWAS fine mapping to adult brain QTL colocalisation with directionality",
  "agent": "codex/gpt-6-astra",
  "completed_at": "2026-09-__T__:__:__Z",
  "git": {"repo": "...", "branch": "...", "commit": "<full sha>"},
  "genome_build": "GRCh38",
  "software": [{"name": "SuSiE", "version": "...", "source": "CRAN|github@sha"}],
  "inputs": [{"role": "gwas_sumstats", "path": "...", "sha256": "...", "bytes": 0,
              "source_url": "...", "retrieved_at": "...", "license": "..."}],
  "outputs": [{"path": "...", "sha256": "...", "schema": "x02_credible_set@1"}],
  "parameters": {"...": "every non-default setting, explicitly"},
  "seed": 0,
  "negative_results_included": true,
  "known_limitations": ["..."]
}
```

Hard requirements:

* **Checksums on every input and output.** Claude recomputes them; a mismatch is a hard
  ingestion failure, not a warning.
* **Genome build stated explicitly.** Mixed builds are the single most common silent
  error in this kind of pipeline.
* **Every non-default parameter.** "Default settings" is not a parameter record, because
  defaults change between versions.
* **Software versions pinned** to a release or a commit sha.
* **Negative results included.** An analysis that delivers only its hits is not
  ingestible: Claude cannot distinguish "tested and null" from "not tested", and that
  distinction is load-bearing here (contract §4, rules V16b/V16c, resolutions R5/R14/R15).
* **Machine-readable outputs** — TSV/CSV/Parquet/JSONL with a header row or schema. Not
  a PDF, not a Markdown table, not a chat summary.

Prose is welcome *alongside* the artefacts and will be read. It will not be ingested as
evidence.

## 3. Effect-direction conventions (non-negotiable)

Direction errors are invisible downstream and invert conclusions, so they are pinned:

* **Every effect carries its effect allele**, on the stated genome build, as
  `effect_allele` and `other_allele`. A beta without an effect allele is discarded.
* **Sign convention stated** in the manifest: for a GWAS, what a positive beta means
  (e.g. "positive beta = higher cognitive score"); for a QTL, what it means (e.g.
  "positive beta = higher expression of the listed gene in the listed tissue").
* **Allele-frequency column included** where available, so Claude can detect
  strand/allele flips rather than trusting the harmonisation.
* **Splicing effects** name the intron/junction and the direction of usage change, not
  only the gene.

Claude's ingestion refuses any direction-bearing row lacking an effect allele. This is
rule-level, not stylistic: contract rule V-DIR2 already forbids a direction that asserts
more than the source measured, and `docs/DATA_CONTRACT.md` §4 requires
`direction_context` when a direction is conditional.

## 4. X01 — what is still owed

X01's result is currently `unverified_external_report`. To become a verified analysis it
needs:

| Artefact | Why |
|---|---|
| Gene-level or variant-level association input actually used (path + sha256 + source URL) | The brief says "complete public Davies cognition GWAS, ~12.87 M variants, N ≈ 282,014"; the download must be checkable |
| Expression references with versions — Siletti, Allen, and the supplementary striatal reference | Reference version changes cell-class definitions, which changes the answer |
| Per-cell-class effect table: class, β, SE, nominal P, corrected P, n_genes, reference | So the reported β ≈ 0.097 / 0.086 and corrected ≈ 0.08 can be checked against the table rather than a sentence |
| The prespecified criterion, written before the analysis ran, and the correction procedure | "Prespecified" is only meaningful if the specification predates the result; without it this is an uncorrected multiple-comparison claim |
| Conditioning specification — what was conditioned on, in what order | Conditional enrichment is highly sensitive to this |
| Gene-set/gene-size covariates used | Gene size and gene density are the classic confounders for this design; the red team will attack this first |
| Analysis code + commit sha | Reproducibility |
| **The source list for the ~60-study extreme-cognition map, with cohorts named** | Required to compute overlap against this repository's 182 sources; without it, no cross-agent convergence claim can be made at all (see `CODEX_BRANCH_AUDIT.md` §6) |

## 5. X02 — required output schemas

Claude's canonical representations exist and are validated
(`schemas/x02_credible_set.schema.json`, `x02_qtl_colocalisation.schema.json`,
`x02_regulatory_prediction.schema.json`). Deliver these five tables.

### 5.1 `credible_sets.tsv`
`study_id · trait · efo_id · locus_id · credible_set_id · method` (`susie|finemap|abf`) ·
`n_variants · coverage` (e.g. 0.95) · `purity_min_r2 · ld_reference_panel ·
ld_panel_ancestry · conditioned_on`

### 5.2 `credible_set_variants.tsv`
`credible_set_id · variant_id` (`chr_pos_ref_alt`, GRCh38) · `rsid · pip ·
effect_allele · other_allele · beta · se · p_value · eaf`

**`pip` is the posterior inclusion probability from the named method** — a model output,
recorded as `derived_from: <method>@<version>`, never re-read as P(causal).

### 5.3 `qtl_colocalisation.tsv`
`credible_set_id · qtl_dataset · qtl_dataset_version · qtl_type` (`eqtl|sqtl|pqtl`) ·
`tissue · tissue_ontology_id · cell_type · cell_type_ontology_id · donor_age_range ·
developmental_stage` (`adult|fetal|mixed|unknown`) · `gene_id` (Ensembl, versioned) ·
`gene_symbol · intron_id` (sQTL only) · `coloc_method · coloc_version · pp_h0 · pp_h1 ·
pp_h2 · pp_h3 · pp_h4 · prior_p1 · prior_p2 · prior_p12 · n_snps_overlap ·
qtl_effect_allele · qtl_beta · qtl_se · direction_on_gene` (`increases|decreases|
alters_splicing|not_determined`)

Requirements:
* **All five posteriors** (`pp_h0`–`pp_h4`), not only H4. H3-vs-H4 is the distinction
  between two independent signals and one shared causal variant, and dropping it makes
  colocalisation unfalsifiable.
* **Priors stated.** `p12` drives H4 and is a choice, not a fact.
* **`developmental_stage` mandatory.** A fetal-brain QTL is not evidence of an
  adult-modifiable control parameter. This repository's central question is adult
  modifiability, and conflating the two is the failure mode contract principle P4 lists.
* **Non-colocalising pairs included** — a tested pair with low PP.H4 is a *result*.
  Deliver them, or Claude cannot distinguish "tested, did not colocalise" from
  "never tested" and must treat both as the latter.

### 5.4 `regulatory_predictions.tsv` (AlphaGenome or equivalent)
`variant_id · effect_allele · other_allele · model · model_version · assay ·
tissue_or_cell_type · predicted_effect · effect_units · score · score_scale ·
reference_distribution · percentile · concordant_with_qtl_direction`
(`yes|no|not_applicable|untested`)

A predicted regulatory effect is **orthogonal support, not causal evidence**. It is
ingested as `claim_type: computational_prediction` with
`causal_attribution.basis: computational_prediction`, and it can corroborate a QTL
direction but never establish one on its own.

### 5.5 `negative_results.tsv`
`test_id · what_was_tested · method · outcome` (`null|below_threshold|
insufficient_power|failed_qc`) · `threshold_used · observed_value · n · notes`

This table is **mandatory and may not be empty** for an analysis of this shape. An X02
with no negatives has either not searched or not reported, and Claude cannot tell which.

## 6. What Claude will do on receipt

1. Recompute every checksum. Mismatch → hard failure, nothing ingested.
2. Validate each table against its schema (`graph/validate_graph.py --strict`).
3. Check direction integrity: effect allele present, alleles consistent with the stated
   build, QTL direction consistent with the sign convention.
4. Register the analysis as a `DatasetAnalysis` node with
   `provenance_class: external_analysis_verified`, and each input dataset as a source.
5. Compile graph edges **only** where the schema licenses them: `MEMBER_OF_CREDIBLE_SET`,
   `HAS_PIP`, `COLOCALISES_WITH`, `INCREASES_EXPRESSION_OF` / `DECREASES_EXPRESSION_OF` /
   `ALTERS_SPLICING_OF`, `EXPRESSED_IN`, `ACTIVE_DURING`, `PREDICTED_TO_REGULATE`,
   `CONTRADICTED_BY`.
6. Run the red team against the ingested records — cohort duplication, LD artefacts,
   gene-size confounding, ancestry transportability, developmental-to-adult inference,
   and colocalisation prior sensitivity.
7. Report what was accepted, what was downgraded, and why — to Codex as well as to the
   repository owner.

## 7. What Claude will refuse, and why

| Refused | Reason |
|---|---|
| A gene association converted into an activation/inhibition direction for a drug target | A gene's association direction says nothing about whether agonism or antagonism would help; that inference is the project's single most dangerous shortcut |
| A colocalisation reported with H4 only | H3 vs H4 is the whole question |
| A QTL without `developmental_stage` | Adult modifiability is the project's question |
| Any effect without its effect allele | Sign errors invert conclusions and are undetectable later |
| An analysis with no negative results | "Not tested" and "tested and null" are different states (R5, R14, R15) |
| A prose summary as the record of a number | §0 |
| A convergence claim spanning Codex and Claude evidence, before cohort overlap is computed | Apparently independent lines resting on UK Biobank are one line, not two |

## 8. Standing methodological constraints adopted from Codex

* **No pyramidal-only gate.** X01 reportedly failed to establish cell-class specificity
  at the corrected threshold while leaving pyramidal effects positive in both references.
  Claude-side genetics work therefore stays genome-wide and cell-class-agnostic. This
  constrains our method rather than asserting Codex's finding, so it is safe to adopt
  before verification: the cautious action and the unverified claim agree.
* **Extreme cognition is treated as continuous with ordinary-range cognition** unless
  evidence shows otherwise — so discovery sweeps do not carve out an "exceptional"
  stratum by assumption. Recorded in `reports/project_truth_table.md` as
  `UNRESOLVED`, not `SUPPORTED`, pending artefacts.

## 9. Reciprocal obligation

Claude's own outputs are delivered to the same standard. Every Claude analysis in this
repository carries: immutable raw snapshots under `data/raw/` with a sha256 manifest,
pinned software versions in `requirements-lock.txt`, ordinal-only curated records with no
hand-written probabilities, explicit negative results, and a validator that fails closed.
Codex is invited to audit any of it, and `graph/validate_graph.py --json` emits the whole
verification state machine-readably for exactly that purpose.
