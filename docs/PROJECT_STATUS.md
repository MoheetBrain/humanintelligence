# Project Status

*Snapshot generated 2026-09-17 (UTC) — **Sprint 1 complete.** All ten deliverables
exist. Repository validates with 0 errors and 0 warnings; 832 tests pass. The headline
result is negative: no target has a defensible causal case for adult cognitive
enhancement, and `tier_1_analyse_next` is empty.*

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

Sprint 1 — *infrastructure and first evidence ingestion*. The type system, 12 schemas,
a 31-rule validator, the state model, the ranking/uncertainty model, `THEORY.md` and all
four evidence atlases are complete. **The repository validates with zero errors** (39
warnings, all of them known incompleteness waiting on the red team). Two deliverables
all 27 targets are audited (30 audit records), the graph compiler, DuckDB/Parquet store,
exporters and all four reports are built, and the post-audit ranking has been run and
published as PRELIMINARY. **Sprint 1 is complete.** The next sprint's first task is not a
feature: three of the four atlases never ran a target-directed registry search, so the
repository's zeros are currently less trustworthy than its ones.

## Current Branch

`sprint-1/foundation` (base `main` @ `9f0d552`, which contained only a README).
Two commits so far: the scaffolding/contracts commit and the contract-amendment/tooling commit.

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

* **Contract v0.1.0** (`docs/DATA_CONTRACT.md`), amended repeatedly during the run in
  response to defects the agents found in use — 16 rulings recorded in
  `docs/blackboard/RESOLUTIONS.md`. The substantive ones: separate
  evidence/counter-evidence grading; null-result edges (V16b) and the symmetry rule that
  a null must be expressible wherever the positive claim is (V16b-sym); the
  measured-absence versus absence-of-measurement distinction (`evidence_gap`, V16c);
  polarity-aware methodological caps (§5.4) with the precautionary asymmetry declared and
  measured; `search_basis` instead of demanding a citation for the absence of evidence;
  `reporting_gap_refs` for completed-but-unreported trials; `preclinical_harm` so animal
  harm cannot wear a clinical label; duplicate source registration policy (§1.3).
* **Machine-checked provenance**: PubMed ESummary, ClinicalTrials.gov v2, GWAS Catalog
  v2, DOI→PMID resolution, and snapshot-based verification for database releases.
  Immutable raw snapshots plus a sha256 manifest; full offline rebuild.
* **HGNC identifier resolution** — no agent hand-writes an accession.
* **Formal ontology**: node/edge type system with domain/range constraints,
  24 computational primitives, state-variable type system, controlled vocabularies.
* **12 JSON Schemas** + pydantic record models + a **31-rule validator** with
  actionable messages (including nearest-declared-id suggestions on dangling refs).
* **Provenance for tool-mediated data** (`scripts/record_tool_snapshot.py`), so MCP tool
  payloads can be snapshotted and verified like an HTTP fetch.
* **State model**: 101 state variables across 8 domains + a dynamics specification.
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
5. Recorded 13 architecture decisions (`docs/DECISIONS.md`) and 16 schema-change
   rulings (`docs/blackboard/RESOLUTIONS.md`), each with rationale, alternatives and the
   cost the fix accepts.
6. Drove the repository from 581 validation violations to **zero errors**, with the
   majority of the fixes landing on the contract rather than on the records — five
   separate constraints turned out to forbid a true record.
7. Ruled that the ranking composite must be **conjunctive** rather than additive, since
   the six dimensions are conditions that must all hold; this moved ranks by up to nine
   places and exposed three further defects (a tautological sensitivity variant, an inert
   composite gate, and the fact that principle P8 does not hold at the composite).
8. Completed all four evidence atlases and the red team's launch; the red team is
   running.

## Important Files and Artifacts

| Path | Role |
|------|------|
| `docs/DATA_CONTRACT.md` | authoritative record/ID/validation contract (v0.1.0, amended) |
| `docs/DECISIONS.md` | D001–D013, including the defects found in use |
| `docs/blackboard/RESOLUTIONS.md` | R1–R16: every schema-change request and its ruling |
| `THEORY.md` | Cognitive Power Envelope + OPEN→WRITE→SELECT→LOCK, with falsification sections |
| `docs/API_RECIPES.md` | verified live query patterns for all five external APIs |
| `ontology/`, `schemas/`, `state_model/` | type system, 12 schemas, 100 state variables |
| `graph/validate_graph.py` | 31-rule validator, `--strict`/`--json`/`--root`/`--update-lock` |
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
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **740 passed, 0 failed** in 35.6 s |
| Validator | `.venv/bin/python graph/validate_graph.py --strict` | **PASS, exit 0** — 0 errors, 0 warnings, 2 info findings, 32 rules run |
| Store | `make store` | 11 tables + provenance, 12 views; nodes 1284, edges 1703 |
| Graph | `make graph` | 1284 nodes / 1703 edges; 636 claim-derived, 942 reference-data, 125 axiom |
| Reports | `make reports` | interactive graph 1.67 MB, **0 remote references**, byte-identical across renders |
| Ranking | `models/ranking/rank_targets.py` | 27 rows, all PRELIMINARY; **tier_1 empty**; gates fired 23/3/2/2 |
| Ownership | `.venv/bin/python scripts/check_ownership.py` | **all 1550 paths owned as expected** |
| Claim registry lock | `graph/validate_graph.py --update-lock` | 289 claim ids locked; V13 now protects provenance |
| Source verification (offline rebuild, no network) | `scripts/fetch_source_metadata.py --all --offline` | **117/117 verified** from committed snapshots |
| Source verification (live) | `scripts/fetch_source_metadata.py --agent power` | 41/41 verified |
| Independent citation spot-check | live PubMed ESummary for PMID 14561278 | title/journal/DOI match the stored record exactly (similarity 1.0) |
| Seed symbol resolution | `scripts/fetch_gene_identifiers.py` | 31/31 HGNC-approved |
| Ownership | `scripts/check_ownership.py --paths …` | clean after specificity fix |
| Record counts (validator census) | — | 182 sources, 290 claims, 393 evidence items, 27 targets, 129 assessments, **29 audits** |
| Audit outcomes | — | 20 retain-with-downgrade · 4 retain · 3 deprioritise · 2 insufficient-evidence; 5 downgrades applied; findings 4 critical / 31 major / 11 minor / 7 info |
| Per-atlas sources/claims | — | genetics 58/149 · brakes 53/57 · power 44/50 · comparative 20/21 · red team 17/12 (in progress) |
| Facet assessments | — | genetics 27 · comparative 27 · integration 27 · brakes 14 · power 7 · red team 0 (in progress) |

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

**None.** AlphaGenome remains deferred for want of an API key (`ALPHAGENOME_API_KEY`),
which was already planned for Sprint 2 (Q001); the module is interface-only and cannot
emit a number. Several MCP connectors in the working environment are unauthorised
(GitHub, Linear, Notion, Slack, Figma, and the bio-research Synapse/Wiley/Owkin servers);
none was needed, because every data source this sprint used is a public API requiring no
key. Synapse and Wiley would widen literature access in later sprints and need
authorising outside this session.

## Exact Next Actions

Ranked by how much they would change what this repository can honestly claim.

1. **Target-directed registry searches for the three atlases that never ran one**
   (brakes, comparative, alphacognition). Four of the red team's five headline findings
   came from `whyStopped` and `resultsSection` fields no literature search returns, and
   the power atlas overturned two of its own published statements this way. Every
   `human_intervention_evidence: 0` in those atlases carries that exposure. Until this is
   done, the repository's zeros are less trustworthy than its ones.
2. **Resolve `causal_gene_attribution` above level 2 or accept that it cannot be** —
   brain eQTL/sQTL colocalisation (GTEx, PsychENCODE, MetaBrain) for cognitive-trait
   credible sets (Q002). Seventeen of 27 targets sit at level 0 and nothing exceeds 2;
   this is the binding constraint on the entire causal case.
3. **Fix the 5 `causal_perturbation` claims carrying `direction: unclear`** where the
   study measured a direction, and re-check the other atlases for the `no_change`
   misuse that V-DIR2 now catches.
4. **Adult cell-type expression ingestion** (Allen / Human Brain Cell Atlas, Q003), to
   separate adult-expressed from developmentally-expressed targets properly rather than
   from GTEx bulk tissue.
5. **Calibrate or drop the probabilities.** Either find a calibration set for the
   ordinal→Beta mapping or restrict published output to ordinal levels and rank
   intervals. Currently every number is an uncalibrated subjective prior.
6. **Model dimension dependence**, or state the interval inflation quantitatively. The
   independence assumption is false in a known direction.
7. **Unify the three surviving field spellings** and clear the 10 implementation
   deviations in `docs/ONTOLOGY_NOTES.md` §4 as contract v0.2.0.
8. **Agent-proposed targets.** Every current target came from the brief; the seed list
   has never been tested against a systematic sweep, so its composition is an anchoring
   risk the ranking cannot detect.
9. **AlphaGenome integration** (Q001) once `ALPHAGENOME_API_KEY` exists.
10. **Re-run the red team on the corrected records.** The genetics grades fell after its
    audit, so its own findings were written against superseded levels.
