# Project Status

*Snapshot generated 2026-09-17 (UTC) — Sprint 1, mid-run: contracts amended, five
domain/infrastructure agents in flight.*

## Project Objective

Build a fully computational causal-control framework for adult human cognitive
capacity: identify the smallest set of **adult-modifiable biological control
parameters** that determine how much useful computation, learning, abstraction,
working memory, transfer and durable knowledge a healthy adult human brain can
achieve.

Not a nootropics list, not a search for an "intelligence gene". All work here is
computational (`docs/COMPUTATIONAL_ONLY_POLICY.md`); external wet-lab, animal and
clinical results are ingested as evidence with provenance and are never repeated,
planned or recommended by this project.

## Current Stage

Sprint 1 — *infrastructure and first evidence ingestion*. Type system, schemas,
validators, ranking/uncertainty model and three of four atlases have landed. The
genetics atlas has not yet merged its authored records into the contract paths, so the
repository does **not** currently validate. No red-team audit has run, so no ranking
has been produced.

## Current Branch

`sprint-1/foundation` (base `main` @ `9f0d552`, which contained only a README).
One commit so far: the scaffolding/contracts commit.

## Current System Architecture

Three linked graph layers compiled from curated records:

1. **Evidence graph** — Paper / Preprint / Dataset / DatabaseRelease / Experiment /
   Measurement / ClinicalTrial / Claim / Replication / Audit / Species.
2. **Biological causal graph** — Variant → Gene → Transcript → Protein →
   MolecularProcess → CellType → BrainRegion → Circuit → StateVariable →
   ComputationalPrimitive → CognitivePhenotype.
3. **Intervention graph** — Compound / Drug / Biologic / RNAIntervention /
   GeneRegulation / MetabolicIntervention / Neurotechnology / Target / Mechanism /
   StateVariable / DesiredEffect / AdverseEffect.

Every layer-2 and layer-3 edge derives from a claim carrying provenance; only
identifier/ontology facts are claim-free (`reference_data`, `ontology_axiom`). Null
results are representable as first-class `NO_DETECTED_EFFECT_ON` edges and are excluded
from support counts.

Storage: curated YAML → Parquet → DuckDB → NetworkX, with Neo4j deferred to an
exporter. Execution: a blackboard — the repository is the shared medium, agents own
disjoint path sets, the orchestrator enforces gates and performs all commits.

## Capabilities Implemented

* **Contract v0.1.0** (`docs/DATA_CONTRACT.md`), amended four times during the run in
  response to defects found in use: separate evidence/counter-evidence grading,
  null-result edges (V16b), polarity-aware methodological caps (§5.4), duplicate source
  registration policy (§1.3).
* **Machine-checked provenance**: PubMed ESummary, ClinicalTrials.gov v2, GWAS Catalog
  v2, DOI→PMID resolution, and snapshot-based verification for database releases.
  Immutable raw snapshots plus a sha256 manifest; full offline rebuild.
* **HGNC identifier resolution** — no agent hand-writes an accession.
* **Formal ontology**: node/edge type system with domain/range constraints,
  24 computational primitives, state-variable type system, controlled vocabularies.
* **12 JSON Schemas** + pydantic record models + a 24-rule validator with
  actionable messages (including nearest-declared-id suggestions on dangling refs).
* **State model**: 100 state variables across 8 domains + a dynamics specification.
* **Ranking + uncertainty model**: facet rubric, facet→dimension spec, ordinal→Beta
  mapping, Monte Carlo rank intervals, polarity-aware caps, information-gain priority,
  convergence/centrality analysis.
* **Chemistry gate** (`src/blueprint/pharmacology/gates.py`) — virtual pharmacology
  refuses targets that have not survived integration and audit.
* Pre-commit gate combining the Commit Continuity Protocol with repository validation.

## Work Completed to Date

1. Scaffolding, contracts, ownership map, task DAG, policy documents (commit 1).
2. Verified reachability of every provenance API the design depends on; recorded working
   query patterns in `docs/API_RECIPES.md` (including the Open Targets
   trait → GWAS study → credible set → L2G/colocalisation route).
3. Spawned 5 of 7 planned subagents; 3 atlases and the ranking model have produced
   records. All five were interrupted by a session usage limit and have been resumed
   with precise remaining-work instructions.
4. Triaged 581 validator violations; fixed the contract/tooling share (intervention
   schema too narrow for real ChEMBL data, V6 failing open on cross-agent duplicates,
   database releases unverifiable by literature registry).
5. Recorded 12 architecture decisions with rationale and consequences
   (`docs/DECISIONS.md`).

## Important Files and Artifacts

| Path | Role |
|------|------|
| `docs/DATA_CONTRACT.md` | authoritative record/ID/validation contract (v0.1.0, amended) |
| `docs/DECISIONS.md` | D001–D012, including the defects found in use |
| `docs/API_RECIPES.md` | verified live query patterns for all five external APIs |
| `ontology/`, `schemas/`, `state_model/` | type system, 12 schemas, 100 state variables |
| `graph/validate_graph.py` | 24-rule validator, `--strict`/`--json`/`--root`/`--update-lock` |
| `models/ranking/`, `models/uncertainty/` | facet rubric, ranking spec, ordinal→Beta model |
| `scripts/fetch_source_metadata.py` | citation verification, offline rebuild |
| `scripts/fetch_gene_identifiers.py` | HGNC resolution |
| `data/raw/MANIFEST.jsonl` | checksummed manifest of every raw snapshot |

## Data Sources and Provenance

| Source | Access | Status |
|--------|--------|--------|
| HGNC REST | public | 31/31 seed symbols resolved |
| NCBI E-utilities (pubmed, taxonomy) | public, optional `NCBI_API_KEY` | in use; 115 literature sources verified |
| ClinicalTrials.gov v2 | public | in use (trial verification, terminated-trial search) |
| GWAS Catalog REST v2 (release 2026-09-13) | public | ingestion pipeline written |
| Open Targets GraphQL (data version 26.06) | public | tractability/safety/credible sets |
| AlphaGenome | **requires key — absent** | interface-only, deferred (Q001) |

## Decisions and Rationale

See `docs/DECISIONS.md` for the full record. The four that shaped this run most:
identifiers and citations are fetched, never typed (D001); no hand-written
probabilities anywhere in curated records (D002); evidence and counter-evidence graded
separately (D003); methodological-weakness caps are polarity-aware and the resulting
precautionary asymmetry is declared and measured rather than hidden (D010, D011).

## Verification and Test Results

All results below were executed; none are projected.

| Check | Command | Result (2026-09-17) |
|-------|---------|---------------------|
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **508 passed** in 10.28 s |
| Validator | `.venv/bin/python graph/validate_graph.py` | **FAIL** — 235 V1 + ~180 V4 violations, dominated by the genetics atlas not having merged its sources (mid-flight) |
| Source verification (offline rebuild, no network) | `scripts/fetch_source_metadata.py --all --offline` | **117/117 verified** from committed snapshots |
| Source verification (live) | `scripts/fetch_source_metadata.py --agent power` | 41/41 verified |
| Independent citation spot-check | live PubMed ESummary for PMID 14561278 | title/journal/DOI match the stored record exactly (similarity 1.0) |
| Seed symbol resolution | `scripts/fetch_gene_identifiers.py` | 31/31 HGNC-approved |
| Ownership | `scripts/check_ownership.py --paths …` | clean after specificity fix |
| Record counts (validator census) | — | 116 sources, 251 claims, 328 evidence items, 27 targets, 48 assessments, 0 audits |

## Known Failures and Limitations

* **The repository does not currently validate.** ~180 V4 violations are the genetics
  atlas's unmerged sources; 235 V1 violations are a mix of schema gaps already fixed and
  agent-side record shape errors awaiting the resumed agents.
* **No red-team audit exists** (0 audit records), so gate G4 is unmet and no ranking
  table has been generated. Nothing in `reports/` yet.
* **`THEORY.md` does not exist yet** (Sprint-1 Deliverable 2, assigned to the
  integration agent, in flight).
* **The graph compiler, DuckDB store, exporters and the interactive HTML report are not
  built** (ontology agent Phase 2, not yet started).
* Five agents were interrupted mid-task by a session usage limit; their work is resumed
  but unfinished, so all counts above are provisional.
* The power atlas could not reject the hypothesis that healthy, rested, well-fed adult
  cognition is **not** power-limited. That is a finding, and it weakens the POWER factor
  of the project's own organising hypothesis.
* Coverage is uneven by construction: the comparative atlas could honestly assess only
  4 of 27 targets; the rest are `not_assessed` with null levels.

## Risks and Technical Debt

| Risk | Status |
|------|--------|
| Hallucinated citations | mitigated and now exercised: 117/117 verified, one independent spot-check passed |
| Hallucinated mechanism behind a real citation | partially mitigated (`extraction.content_checked`); depends on the red team |
| Seed-list anchoring (27 brief-supplied targets) | declared in the registry; ranking must expose `dossier_depth` and `coverage` |
| Precautionary asymmetry under-ranking good targets | declared (D011); `symmetric_caps` sensitivity variant required before any ranking is published |
| Ranking read as a safety or efficacy claim | report must carry PRELIMINARY plus rank intervals; not yet produced, so not yet demonstrated |
| Cross-agent citation dependence (shared cohorts, shared sources) | 2 shared sources already detected by the validator; red team owns the check |
| Session usage limits interrupting long agent runs | observed; mitigated by resumable agents and frequent orchestrator checkpoints |

## Current Blockers

None external. AlphaGenome remains deferred for want of an API key, which was already
planned for a later sprint.

## Exact Next Actions

1. Genetics atlas: run its merge scripts so `evidence/sources/alphacognition.yaml` and
   `atlases/alphacognition/assessments/` exist, then verify sources and clear V4.
2. Ontology agent: finish the outstanding test files, triage the remaining V1
   violations into schema-side versus record-side, write its handoff note.
3. Integration agent: `THEORY.md`, `models/causal/` interfaces,
   `docs/PHARMACOLOGY_INTERFACES.md`, and confirm the `symmetric_caps` variant.
4. Get `graph/validate_graph.py --strict` to exit 0, then commit the atlases.
5. Spawn the red team (agent 7 of 7) once the atlases are stable; require the full
   mandatory check catalogue for all 27 targets (gate G4).
6. Ontology agent Phase 2: graph compiler, DuckDB/Parquet store, exporters,
   `reports/intelligence_graph_v0_1.html`.
7. Integration Stage 2: the post-audit ranking run producing
   `reports/target_ranking_v0_1.csv` (PRELIMINARY) with rank intervals.
8. Orchestrator: `reports/sprint1_summary.md`, README status refresh, final test run.
