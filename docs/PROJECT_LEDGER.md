# Project Ledger

Append-only chronological record. One entry per commit. Entries are never rewritten
or deleted except to correct a demonstrable factual error, and such a correction is
documented inside the entry itself.

---

## 2026-09-17T14:35Z — Sprint 1 scaffolding, contracts and provenance tooling

* **Branch:** `sprint-1/foundation` (created from `main` @ `9f0d552`)
* **Project stage:** Sprint 1 — infrastructure and first evidence ingestion
* **Objective of the change:** establish the repository skeleton, the machine-readable
  contracts that all agents must obey, and the provenance tooling that makes citation
  fabrication detectable before any scientific record is written.

### Files and systems changed

* Added `pyproject.toml` (deps pinned by lower bound: pydantic, PyYAML, jsonschema,
  pandas, pyarrow, duckdb, networkx; pytest as dev extra), `Makefile` (network vs
  offline target separation), `.gitignore`.
* Added contracts: `docs/DATA_CONTRACT.md` (v0.1.0), `docs/BLACKBOARD_PROTOCOL.md`,
  `docs/OWNERSHIP.yaml`, `docs/TASK_DAG.yaml`, `docs/AGENT_REGISTRY.yaml`,
  `docs/COMPUTATIONAL_ONLY_POLICY.md`.
* Added `targets/seed_registry.yaml`: 27 seed targets (14 brakes, 7 power,
  6 neuromodulatory/plasticity), 13 deep + 14 shallow dossier assignments.
* Added provenance tooling: `scripts/_provenance.py`, `scripts/fetch_source_metadata.py`
  (PubMed/CT.gov/GWAS Catalog/DOI verification with immutable snapshots and offline
  rebuild), `scripts/fetch_gene_identifiers.py` (HGNC resolution),
  `scripts/check_ownership.py`.
* Added `.githooks/pre-commit` and `scripts/install-git-hooks.sh`; installed via
  `core.hooksPath`.
* Created the directory skeleton required by the brief (ontology, schemas, state_model,
  atlases, graph, data, evidence, targets, models, pipelines, src, tests, reports, docs).
* Added first raw data: `data/raw/hgnc/2026-09-17/*.json` (31 files) and
  `data/raw/MANIFEST.jsonl` (31 checksummed entries).

### What was completed

Scaffolding and contracts only. No ontology, schema, validator, graph, model or
evidence record exists yet. The seed registry is a work assignment, not a result.

### Decisions made and why

1. Identifiers and citations are fetched from authorities (HGNC, PubMed,
   ClinicalTrials.gov, GWAS Catalog) and verified by title similarity, because
   fabricated accessions are the dominant failure mode for LLM-curated evidence.
2. Curated records may not contain hand-written probabilities; only ordinal evidence
   levels. Numbers appear solely as outputs of named models under `models/`. This
   implements the brief's prohibition on fake precision as an enforceable rule.
3. Graph edges in layers 2 and 3 are compiled from claims, so no edge can exist without
   provenance.
4. Red-team adjustments are downgrade-only and the claim registry is append-only, so
   audits cannot erase evidence.
5. Blackboard architecture with disjoint path ownership and no agent-to-agent messaging,
   to avoid citation cascades between agents.
6. 27 seed targets with explicit depth tiers, so breadth does not silently become
   shallow-everywhere.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Seed symbol resolution | `.venv/bin/python scripts/fetch_gene_identifiers.py` | 31/31 resolved to HGNC-approved records; snapshots + manifest written |
| Provenance API reachability | ad-hoc `urllib` probes | NCBI E-utilities, ClinicalTrials.gov v2, Open Targets GraphQL, HGNC REST, GWAS Catalog REST v2 all reachable |
| PubMed metadata via MCP | `get_article_metadata` for PMIDs 29942086, 30038396 | titles/DOIs returned and matched expectations |
| Python environment | `uv pip install` + import check | pydantic 2.13.5, PyYAML 6.0.3, jsonschema 4.26.0, pandas 3.0.5, duckdb 1.5.5, pyarrow 25.0.1, networkx 3.6.1, pytest 9.1.1 on CPython 3.12.14 |
| Script syntax | `ast.parse` on `scripts/fetch_source_metadata.py` | parsed |
| `make test` | — | **not run: no tests exist yet** |
| `make validate` | — | **not run: validator not written yet** |

### Failures or unresolved uncertainty

* `scripts/fetch_source_metadata.py` is unexercised end-to-end (no source files yet);
  only the HGNC sibling script has run against a live API.
* The title-similarity threshold (0.90) and the ±1-year tolerance are judgement calls
  with no empirical calibration.
* ClinicalTrials.gov official titles will often differ from how an agent paraphrases a
  trial; expect verification friction there.
* Whether 27 targets can each receive honest facet coverage inside Sprint 1 is
  unproven; the depth tiers are an attempt to bound this, not a guarantee.

### Effect on the overall project

The repository now has an enforceable contract and a provenance spine. Every
subsequent agent output can be checked mechanically rather than trusted.

### Next intended step

Spawn the Ontology/Graph Architect to produce `ontology/`, `schemas/`, `state_model/`,
pydantic models, validators and their tests (gate G1), then freeze the schema and
release the domain agents in parallel.

---

## 2026-09-17T18:10Z — Contract amendments and tooling hardening (mid-run checkpoint)

* **Branch:** `sprint-1/foundation`
* **Project stage:** Sprint 1 — infrastructure and first evidence ingestion, mid-run
* **Objective of the change:** checkpoint the orchestrator's own work — four contract
  amendments forced by defects the agents found in use, plus hardening of the
  provenance and ownership tooling — while five agents are still in flight. Agent
  records are deliberately **not** included in this commit because the repository does
  not yet validate.

### Files and systems changed

* `docs/DATA_CONTRACT.md`: §5.2 facet assessments now grade supporting and
  contradicting evidence separately (`level` / `counter_level` / `assessment_status`,
  `level: null` when not assessed); new §5.3 defining the shared ordinal scale
  `evidence_strength_v1`; new §5.4 making methodological-weakness caps polarity-aware
  and declaring the precautionary asymmetry with an obligation to measure it; new
  §1.3 paragraph allowing duplicate source registration across agents while making
  field divergence a hard error; new rule V16b requiring null results to be
  representable as `NO_DETECTED_EFFECT_ON` edges; `direction` enum gained
  `state_dependent`.
* `scripts/fetch_source_metadata.py`: offline lookups for ClinicalTrials.gov, GWAS
  Catalog and DOI sources; snapshot-based verification for `SRC:DB:*` / `SRC:DATASET:*`
  (`release_verified_by_snapshot`, checked against the manifest sha256);
  `ACCEPTED_STATUSES` so a release counts as verified.
* `scripts/check_ownership.py`: most-specific-glob-wins resolution; `.gitkeep`
  placeholders exempted.
* `docs/OWNERSHIP.yaml`: pharmacology interfaces reassigned to `agent:integration`;
  report paths scoped per owner; HGNC snapshot paths assigned.
* `docs/TASK_DAG.yaml`, `docs/AGENT_REGISTRY.yaml`: real task statuses and a spawn log.
* `docs/DECISIONS.md` (new): D001–D012, including the three defects found in use.
* `docs/API_RECIPES.md` (new): query patterns verified against all five live APIs,
  including the Open Targets trait → GWAS study → credible set → L2G/colocalisation
  route and the trap that `target { credibleSets }` returns molecular QTL sets with
  empty L2G predictions.
* `ROADMAP.md`, `CONTRIBUTING.md`, `requirements-lock.txt` (new); `Makefile` gained an
  `index-sources` target so `make validate` rebuilds the verification index offline.

### What was completed

Orchestrator-side work only. Five agents were spawned, produced substantial records, and
were then interrupted by a session usage limit; all five have been resumed with
precise remaining-work instructions.

### Decisions made and why

1. **D010 polarity-aware caps.** `agent:comparative` found that a uniform
   "no phylogenetic control ⇒ cap at level 2" rule, applied to the inverse-polarity
   facet `human_lineage_divergence_risk`, made a target with documented human/mouse
   divergence look *more* translatable. Caps now bite only in the direction that
   favours the target.
2. **D011 declare and measure the asymmetry.** The corrected rule lets weak evidence
   raise doubt but not establish support. That is deliberate for a domain whose
   dominant risk is over-optimism, and it is not neutral, so the ranking spec must
   carry a `symmetric_caps` sensitivity variant and the report must expose
   `rank_delta_symmetric_caps`.
3. **D012 duplicate source registration allowed.** Treating cross-agent duplicates as
   violations pushed an agent into deleting its registrations and depending on another
   agent's file, which it could not edit. Duplication is now informational;
   divergence on registry-verified fields is the hard error.
4. **Null results need first-class edges (V16b).** `agent:power` found that a positive
   trial compiled into an edge while an equally well-powered null trial could not.
5. **Database releases are verified against their own snapshot,** not a literature
   registry, because there is no registry that could answer for them.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **508 passed** in 10.28 s |
| Validator | `.venv/bin/python graph/validate_graph.py` | **FAIL**: 235 V1 + ~180 V4 violations (genetics atlas mid-merge) |
| Offline provenance rebuild | `scripts/fetch_source_metadata.py --all --offline` | **117/117 verified**, no network |
| Live verification | `scripts/fetch_source_metadata.py --agent power` | 41/41 verified |
| Independent spot-check | live PubMed ESummary, PMID 14561278 | matches the stored record exactly (similarity 1.0, DOI 10.1098/rspb.2003.2492) |
| Release verification | `scripts/fetch_source_metadata.py --agent integration` | 1/1, `release_verified_by_snapshot`, 149 manifest snapshots |
| Ownership | `scripts/check_ownership.py --paths …` | clean |

### Failures or unresolved uncertainty

* The repository **does not validate** at this commit; that is why no agent records are
  included in it. The staged paths are documentation and tooling only, so the
  pre-commit validation gate does not fire — this is the gate working as intended, not
  a bypass.
* 0 audit records exist, so gate G4 is unmet and no ranking has been or may be produced.
* `THEORY.md` (Deliverable 2) and the graph/store/export layer (Deliverables 5, 6, 9)
  do not exist yet.
* Whether the resumed agents can clear all 415 outstanding violations is unproven.
* The power atlas's inability to reject "not power-limited in healthy rested adults"
  weakens the POWER factor of the project's own organising hypothesis. This must be
  reflected in `THEORY.md` rather than smoothed over.

### Effect on the overall project

The contract is now materially better than the one written before any data existed:
three of the four amendments came from agents hitting real defects, which is the
blackboard architecture doing what it was chosen for. Provenance verification has been
exercised end to end, including a fully offline rebuild.

### Next intended step

Get `graph/validate_graph.py --strict` to exit 0 with the resumed agents' records, then
commit the atlases, spawn the red team, and only then allow the first ranking run.

---

## 2026-09-17T22:10Z — Four evidence atlases, type system, models, THEORY.md, red-team audit of all 27 targets, graph compiler, DuckDB store and interactive graph report

* **Branch:** `sprint-1/foundation`
* **Project stage:** Sprint 1 — infrastructure and first evidence ingestion
* **Objective of the change:** land the substantive Sprint-1 content — the formal type
  system, 12 JSON Schemas, the 31-rule validator, the state model, the
  ranking/uncertainty model, `THEORY.md`, and all four evidence atlases — in the first
  state where the repository validates with zero errors.

### Files and systems changed

* `ontology/` (6 files): node and edge type systems with domain/range constraints, 27
  computational primitives (24 from the brief plus three agent-proposed), the
  state-variable type system, controlled vocabularies, definitional edges.
* `schemas/` (12 JSON Schemas) and `src/blueprint/` (ids, ontology, schemas, records,
  loaders, validate, verification, policy, vocab, violations, ranking/, pharmacology/).
* `graph/validate_graph.py`: 31 rules with `--strict`, `--json`, `--root`, `--update-lock`.
* `state_model/` (9 files): 101 state variables across 8 domains plus `dynamics.yaml`.
* `models/ranking/` (facet rubric, ranking spec, CLI), `models/uncertainty/`,
  `models/causal/` (Sprint-2 interfaces, no estimation).
* `THEORY.md`: Cognitive Power Envelope and OPEN→WRITE→SELECT→LOCK as conceptual models,
  each with an explicit falsification section.
* Four atlases: `atlases/{brakes,power,comparative,alphacognition}/`, `evidence/sources/`,
  `evidence/claims/`, `targets/candidates/` (27 dossiers), plus
  `atlases/integration/assessments/` (27 tractability grades from a pinned release).
* `pipelines/`: GWAS Catalog and Open Targets genetics ingestion, taxonomy resolution,
  atlas self-checks, migration scripts.
* `scripts/record_tool_snapshot.py` (new): provenance for MCP-tool-derived payloads.
* `evidence/claims/claim_registry.lock` (new): 289 locked claim ids, so V13 protects
  provenance rather than nothing.
* `.githooks/pre-commit`: the validation gate now blocks on **errors** only.
* `docs/blackboard/RESOLUTIONS.md`: R1–R16. `docs/DECISIONS.md`: D001–D013.

### What was completed

Deliverables 1–9 of the Sprint-1 list. The red team audited all 27 seed targets (29
records: 20 retain-with-downgrade, 4 retain, 3 deprioritise, 2 insufficient-evidence; 5
downgrades applied; 4 critical, 31 major, 11 minor, 7 info findings). The graph compiler,
DuckDB/Parquet store and `reports/intelligence_graph_v0_1.html` (1.6 MB, self-contained,
zero remote references, null-result edges rendered distinctly) are built. Two export
CLIs remain.
Deliverable 10 (ranked table) is deliberately **unpublished**: the pre-audit table was
generated and then deleted, because a ranking with no audit behind it, computed under a
superseded aggregation operator, is exactly the artefact that gets read as a result.

### Decisions made and why

1. **The ranking composite is conjunctive (D013).** The six dimensions are conditions
   that must all hold, and a weighted mean lets five strong dimensions compensate for a
   near-zero sixth — the inference this project must not license. Product under an
   explicit (and knowingly false) independence assumption, with `minimum` and
   `weighted_additive` as reported variants at unchanged weights. Ranks moved by up to
   nine places; `SLC16A7` fell from 9 to 16 because it had scored on compensation.
2. **Five contract constraints turned out to forbid a true record** and were fixed:
   demanding a citation for the absence of evidence (R11); no way to express a null
   result as an edge (V16b) or to express one where the positive claim was expressible
   (V16b-sym); no way to distinguish a tested null from an unmeasured endpoint (R5); no
   way to record a completed-but-unreported trial (R14); `sample_size` forbidding the
   zero enrolment of a withdrawn trial.
3. **The pre-commit gate blocks on errors, not warnings.** Requiring zero warnings
   would mean no commit until an entire sprint finishes, which destroys incremental
   history. Invalidity must never reach history; incompleteness is what this ledger and
   `docs/PROJECT_STATUS.md` record.
4. **Raw snapshot directories are shared append-only (R16).** They are keyed by
   registry, not by agent; per-agent ownership made the new tool-snapshot script
   unusable by whichever agent did not own the registry it needed.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **740 passed, 0 failed** (35.6 s), re-run after the audit landed |
| Validator | `.venv/bin/python graph/validate_graph.py` | **PASS (warnings only)** — 0 errors, 39 warnings, 31 rules |
| Ownership | `.venv/bin/python scripts/check_ownership.py` | all **1550** paths owned as expected |
| Source verification | `scripts/fetch_source_metadata.py --all --offline` | 117/117 at the time of the last full offline run; per-agent live runs: brakes 53/53, power 44/44, comparative 20/20, genetics 58/58 |
| Manifest integrity (V19) | sha256 of every entry vs disk | 1119 entries, **0 mismatches** |
| Claim registry | `--update-lock` | 289 ids locked |
| Independent citation spot-check | live PubMed ESummary, PMID 14561278 | matches stored record exactly |

### Failures or unresolved uncertainty

* **Gate G4 is met**: all 27 targets audited. 12 warnings remain — 9 red-team sources
  awaiting their end-of-run verification pass (V6), 3 self-declared contested claims
  (V14), 2 deliberate registry-only registrations (V22).
* **The post-audit ranking has not been run**, so the 4 critical findings and 5
  downgrades are recorded but not yet reflected in any target ordering.
* **Zero of 27 targets reach level 3 on `causal_gene_attribution`; zero have QTL
  colocalisation** supporting their gene assignment at any cognitive-trait credible set.
* The power atlas **cannot reject** the hypothesis that healthy, rested, well-fed adult
  cognition is not power-limited, weakening the POWER factor of this project's own
  organising hypothesis. `THEORY.md` §1.4 says so explicitly.
* Principle **P8 does not hold at the composite** under a product: a level-0 facet
  yields a wider relative interval than an unassessed facet, though the latter is more
  uncertain. Asserted where it holds, pinned where it does not; this is why the rank
  interval is the headline output.
* The independence assumption in the composite is **false in a known direction**, so
  every reported interval is narrower than reality by an unquantified amount.
* Ten contract deviations survive in the implementation (`docs/ONTOLOGY_NOTES.md` §4),
  two material: V9's non-probability case is a warning rather than an error, and three
  field spellings survive because unifying them would invalidate ~60 records. v0.2.0
  must pick one each.
* `arousal_level`'s `polarity` is nominal — it is non-monotone, so neither `risk` nor
  `margin` is honest, and the rule required a binary.
* `database_gradable` is unset in the facet rubric, so R7's `source_refs`-only grading
  is currently licensed for no facet; the validator fails closed, which blocks the
  intended use until `agent:integration` sets the flag.
* The V20 prohibited-work text heuristic has known holes in both directions, pinned by
  12 cases from real records.
* A literature-only search systematically misses interventions performed and never
  published. This was found twice, in the same atlas, by forcing zeros to declare what
  they searched — and both times it overturned a statement that atlas had already made.

### Effect on the overall project

The repository now holds a machine-checked evidence base: 182 sources (all verified or
release-verified), 289 claims, 392 evidence items, 27 target dossiers, 102 facet
assessments, and a type system strict enough that five of its own constraints had to be
corrected when they forbade true records. The most valuable outputs of the sprint are
negative: no target has causal-gene evidence at level 3, nothing in the brake atlas
reaches level 4, and the power hypothesis is not currently supportable in healthy adults.

### Next intended step

Finish the red-team audit (gate G4), then the graph compiler, DuckDB/Parquet store,
exporters and `reports/intelligence_graph_v0_1.html`, then the post-audit ranking run
that produces `reports/target_ranking_v0_1.csv` marked PRELIMINARY.

---

## 2026-09-17T23:55Z — Sprint 1 complete: post-audit ranking published, all ten deliverables exist

* **Branch:** `sprint-1/foundation`
* **Project stage:** Sprint 1 complete; Sprint 2 not started
* **Objective of the change:** run the post-audit ranking, publish the four reports, and
  close Sprint 1 with an honest account of what the repository can and cannot support.

### Files and systems changed

* `reports/target_ranking_v0_1.csv` + `.meta.json`: 27 rows, every row `PRELIMINARY`,
  conjunctive (product) primary composite with `minimum` and `weighted_additive` variants.
* `reports/integration_v0_1.md`, `reports/red_team_audit_v0_1.md`,
  `reports/intelligence_graph_v0_1.html`, `reports/sprint1_summary.md`.
* `graph/query_graph.py`, `graph/export_graph.py`; `src/blueprint/graph/`,
  `src/blueprint/store/`; DuckDB store (11 tables + provenance, 12 views).
* `pyproject.toml`: `testpaths` now includes `pipelines`, so agent-owned guardrail tests
  actually execute. `Makefile`: `PY ?= PYTHONPATH=src .venv/bin/python` so
  `python -m blueprint.…` works in a tree that skipped `make setup`; project installed
  editable.
* `docs/DATA_CONTRACT.md`: principle **P9** (a guard is not a guard until code reads it),
  `direction: not_applicable`, rule **V-DIR2**. `docs/DECISIONS.md`: **D014** (the
  sprint's dominant error mode). `docs/blackboard/RESOLUTIONS.md`: R17–R19.
* Genetics atlas corrected after the laundering fix; 31 `expression` claims moved from
  `direction: no_change` to `not_applicable`.

### What was completed

**All ten Sprint-1 deliverables.** README, THEORY.md, formal ontology, JSON schemas +
validators, graph compiler, DuckDB/Parquet store, seed dataset (27 targets), red-team
audit of every target, interactive graph visualisation, and the ranked table.

### Decisions made and why

1. **P9 and D014 recorded as standing lessons.** Five times this sprint a "we looked and
   found nothing" value was used for "there was nothing to look for", across four agents
   and the contract itself; and separately an eligibility guard written in data was never
   read by the code that consumed it, laundering educational attainment into fluid
   reasoning across 10 grades. Both are recorded as reusable review questions rather than
   as individual fixes.
2. **Agent-owned guardrail tests must run.** The genetics agent wrote a 12-case guardrail
   test that pytest never discovered. A guard that does not run is decoration, so
   `testpaths` was widened rather than the test relocated into another agent's lane.
3. **The ranking is published, the interpretation is constrained.** Tier 1 is empty and
   the narrative leads with what the table cannot support, because a ranked CSV is the
   artefact most likely to be read as a recommendation.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **838 passed, 0 failed** (71 s) |
| Validator | `graph/validate_graph.py --strict` | **exit 0, PASS** — 0 errors, 0 warnings, 2 info, 32 rules |
| Ownership | `scripts/check_ownership.py` | all paths owned as expected |
| Store | `make store` | 11 tables + provenance, 12 views; nodes 1284, edges 1703 |
| Graph | `make graph` | 1284 nodes / 1703 edges; 636 claim-derived, 942 reference-data, 125 axiom, 10 null-result |
| Reports | `make reports` | graph HTML 1.67 MB, **0 remote references**, byte-identical across renders |
| Ranking | `models/ranking/rank_targets.py` | 27 rows; **tier_1 empty**; gates fired: D6 cap 23, critical-finding cap 3, safety cap 2, developmental cap 2 |
| Guardrail test | `pytest pipelines/alphacognition/test_facet_guardrails.py` | 12 passed; 4 fail if the guard is stubbed permissive |
| Manifest integrity | sha256 per entry vs disk | 0 mismatches |

### Failures or unresolved uncertainty

* **Three of four atlases never ran a target-directed registry search.** Four of the red
  team's five headline findings came from `whyStopped`/`resultsSection` fields no
  literature search returns, and the power atlas overturned two of its own published
  statements this way. The repository's zeros are currently less trustworthy than its
  ones. This is the top Sprint-2 action.
* **The ranking model was silently discarding red-team downgrades** until this run:
  three of five adjustments raise `counter_level` rather than lowering `level`, and the
  ranking's input type rejected those as forbidden upgrades. It failed closed and logged
  nothing; only reconciling counts against the audit surfaced it. Fixed, with a test.
* **The ordering is materially operator-dependent**: tau-b 0.719 product/minimum, 0.765
  product/additive, **0.473** minimum/additive.
* **Every interval is too narrow** by an unquantified amount (dimension independence
  assumed and known false).
* **P8 does not hold at the composite** under a product; asserted where it holds, pinned
  where it does not.
* No tau-b was quoted against the Stage-1 ordering: the operator change, the laundering
  fix and the audit are confounded, and a single number would invite a causal reading it
  cannot carry.
* The red team's findings were written against genetics grades that subsequently fell, so
  a re-audit on corrected records is queued.
* 5 `causal_perturbation` claims still carry `direction: unclear`; 10 implementation
  deviations survive (`docs/ONTOLOGY_NOTES.md` §4), two material.
* AlphaGenome never called (no key); module is interface-only by construction.

### Effect on the overall project

Sprint 1 delivered an instrument and a negative result. The instrument caught five
contract defects, one silent data-loss bug in the ranking, one laundering bug that had
inflated a third of the genetics grades, a tautological sensitivity variant, an inert
gate and a mislabelled severity count — most of them found by agents auditing their own
or each other's work against machine-checkable rules. The result is that no seed target
has a defensible causal case for adult cognitive enhancement, `tier_1_analyse_next` is
empty, and the most-studied brake target carries a replicated human null.

### Next intended step

Sprint 2, starting with target-directed registry searches across the three atlases that
never ran one, then brain QTL colocalisation to resolve `causal_gene_attribution` above
level 2 or accept that it cannot be resolved with current public data.

---

## 2026-09-18T11:30Z — Sprint 2 part 1: Codex branch audit (absent), X01 ingested as inert, X02 ingestion built, target-directed registry searches

* **Branch:** `sprint-2/causal-bridge` (from `sprint-1/foundation` @ `24f4f92`)
* **Project stage:** Sprint 2 — integrate external analyses, close the human causal bridge
* **Objective of the change:** audit the Codex/Astra branch, make the repository able to
  ingest X01/X02 without trusting prose, and run the target-directed registry searches
  that Sprint 1 identified as its top outstanding risk.

### Files and systems changed

* `docs/integration/CODEX_BRANCH_AUDIT.md` (new): the branch does not exist; the search
  is documented so the negative result is auditable.
* `docs/integration/CODEX_HANDOFF_CONTRACT.md` (new): exactly what Codex must deliver for
  X01/X02, in machine-ingestible form, with what Claude will refuse and why.
* `ontology/nodes.yaml` +6 types (CredibleSet, MolecularQTL, ColocalisationResult,
  RegulatoryPrediction, DevelopmentalStage, DatasetAnalysis), +6 prefixes;
  `ontology/edges.yaml` +10 relations including the `TESTED_FOR_COLOCALISATION_WITH` /
  `COLOCALISES_WITH` pair; ontology_version 0.2.0.
* `ontology/vocabularies.yaml` +12 vocabularies; `claim_type` gained
  `computational_prediction`; `provenance_class` gained `external_analysis_verified` and
  `external_analysis_unverified` (the latter excluded from `evidential_classes`).
* `schemas/` +6 (external_analysis, x02_credible_set, x02_credible_set_variant,
  x02_qtl_colocalisation, x02_regulatory_prediction, x02_negative_result).
* `analyses/external/X01_cell_type_enrichment.yaml` (new): X01 recorded as
  `unverified_external_report`, every figure a verbatim string, licensing nothing.
* `src/blueprint/validate.py`: rule **V-EXT**; `paths.py`, `schemas.py`, `loaders.py`
  wired for external analyses.
* `pipelines/integration/ingest_x02.py` (new) + `tests/fixtures/x02_delivery_valid/` +
  `tests/test_x02_ingestion.py` (14 tests).
* `pipelines/registry_search/` (new): `target_search_terms.yaml`, `search_registry.py`,
  `extract_results.py`; `evidence/registry_searches/` (20 records + 5 extractions);
  `evidence/sources/orchestrator.yaml` (41 verified trial sources).
* Four facets gained `reporting_gap_refs` (ADORA1, DRD1, GRIN2B, HTR2A).
* `reports/registry_search_v0_2.md` (new); `docs/OWNERSHIP.yaml` extended.

### What was completed

Tasks A, B, C, D and J. Tasks E, F, G, H and I are not started at this commit.

### Decisions made and why

1. **X01's figures are recorded but inert.** The only record of X01 is the task
   description's prose. A number with no artefact cannot fail a check, so it may not
   support a claim (rule V-EXT). This is the standard the brief itself sets for X02,
   applied to X01.
2. **X01's methodological instruction is adopted anyway** — no pyramidal-only gate —
   because it constrains our method rather than asserting Codex's finding, so it costs
   nothing if the finding is later refuted.
3. **A null must be representable wherever a positive is.** `COLOCALISES_WITH` is paired
   with `TESTED_FOR_COLOCALISATION_WITH`, and an X02 delivery with an empty
   negative-results table is refused, because "tested and did not colocalise" and "never
   tested" are different states.
4. **No gene association may license an intervention direction.** None of the ten new
   relations asserts an effect, and the intervention-layer direction relations remain
   reachable only from pharmacological claims about actual compounds.
5. **Positive-versus-null is not assigned mechanically** in the registry search; the five
   trials with posted cognitive results are extracted verbatim for judgement.
6. **G (no trial identified) is never a biological null.** Each such record says so in
   words, and no `counter_level` was raised anywhere by this search.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `.venv/bin/python -m pytest -q -m "not network"` | **852 passed, 0 failed** (80 s) |
| Validator | `graph/validate_graph.py --strict` | **exit 0** — 0 errors, 0 warnings, 3 info; 33 rules |
| Schema/vocabulary drift | `blueprint.sync_schema_enums --check` | schemas and vocabularies agree |
| X02 adapter | `ingest_x02.py --self-test` | ACCEPTED on the synthetic fixture; 14 tests prove the refusals |
| Registry search | `search_registry.py --all` | 20 records, **360 studies classified**, 84 queries |
| Results extraction | `extract_results.py --queued` | 5 trials extracted verbatim |
| Source verification | `fetch_source_metadata.py --agent orchestrator` | **41/41 verified** against ClinicalTrials.gov |
| Branch search | `git branch --all`, GitHub branches API, `git worktree list`, `git fsck`, filesystem sweep, Codex session index | **no Codex/Astra branch exists** |

### Failures or unresolved uncertainty

* **The Codex/Astra branch does not exist**, so X01 cannot be verified, its method cannot
  be audited, and cross-agent evidence dependence cannot be computed. Codex reportedly
  assembled ~60 extreme-cognition studies; without that source list, overlap against this
  repository's 182 sources is unknowable and **any convergence claim spanning the two
  bodies of evidence is refused rather than caveated**.
* Two classifier bugs were found by reading output rather than trusting counts — `wais`
  matching inside "waist circumference", and a mechanism phrase matched by its first
  token hitting a "Community Reintegration Workshop". Both had inflated findings by about
  half. Fixed; the second required two attempts because the first fix over-corrected and
  dropped a genuinely relevant D1 trial.
* The registry search is term-bounded and ClinicalTrials.gov-only. Targets with no named
  clinical modulator are searched by gene symbol and mechanism phrase alone, which is
  weak; `no_trial_identified` means *not found with these terms*.
* Four assessment files were re-emitted by script, so inline comments below their headers
  were lost. The record content is unchanged apart from the two fields named in each
  file's new header note.
* `--emit` on the X02 adapter is deliberately unimplemented: the canonical record's shape
  depends on what a real delivery contains, and generating one from a fixture would bake
  a guess into the repository.

### Effect on the overall project

The repository can now accept an external analysis without believing its prose, and the
distinction is enforced by a rule rather than a convention. The zeros that Sprint 1
flagged as its weakest claims are now classified against a registry, with three targets
explicitly recorded as never tested rather than as failed.

### Next intended step

Tasks E (systematic target discovery), F (positive human natural experiments), G
(comparative intelligence 2.0), H (convergence layer), I (project truth table), then a
red-team pass over all new claims.

---

## 2026-09-18T14:10Z — Sprint 2 part 2: Selective Encoding Hypothesis, genome-wide discovery sweep, 2q12.3 watchlist

* **Branch:** `sprint-2/causal-bridge`
* **Project stage:** Sprint 2 — Tasks E and F, plus a project-lead theory node
* **Objective of the change:** record the Selective Encoding Hypothesis as a usable
  compass, break seed-list anchoring with a genome-wide sweep, and open the positive
  human natural-experiment watchlist.

### Files and systems changed

* `theory/selective_encoding_hypothesis.md` and `theory/selective_encoding_criteria.yaml`
  (new): the project lead's hypothesis, recorded as a THEORY NODE with seven criteria
  SE1–SE7, a decisive quantity expressed as a difference-in-differences, per-criterion
  falsifiers, the internal SE1–SE3 versus SE6–SE7 tension, and four guards. Cross-linked
  from `THEORY.md` §2.
* `pipelines/discovery/sweep_cognition_genes.py` (new) + gzipped snapshots under
  `data/raw/gwas_catalog_sweep/` + `data/interim/discovery_cognition_genes.jsonl`.
* `targets/discovered/discovered_registry.yaml` (new): 21 candidates, unranked by design.
* `atlases/positive_genetics/2q12_3_duplication.yaml` (new) + Ensembl and Open Targets
  snapshots + `data/interim/2q12_3_gene_annotations.json`.
* `scripts/_provenance.py`: gzip snapshot support (`compress=True`, `read_snapshot`), so a
  paginated API dump costs ~10x less repository space with byte-for-byte recovery.
* `evidence/sources/orchestrator.yaml`: +1 source (Huguet 2024), 42/42 verified.

### What was completed

Tasks E and F. Tasks G, H and I remain, as does the red-team pass.

### Decisions made and why

1. **The Selective Encoding Hypothesis is recorded in two forms** — prose and
   machine-readable criteria — so candidates can be scored against SE1–SE7 and rescored
   as evidence changes, rather than the hypothesis being admired and forgotten.
2. **Its decisive quantity is a contrast, not a level.** A global memory enhancer scores
   zero on it however large its main effect; a pure selectivity mechanism can score
   positive with no main effect at all. Consequence: most existing cognitive-enhancer
   evidence is `not_assessable` for this hypothesis rather than supportive of it.
3. **Codex's three named genes were checked independently rather than ingested.** GRM3
   holds up at variant level (4 studies, p = 4e-13, though one contributing study is an
   educational-attainment GWAS). GABBR1 has one genome-wide-significant study. **ADGRB1
   rests on a single association at p = 2e-07, below the conventional threshold** — which
   does not refute a gene-based claim, but means this repository's own variant-level
   evidence for it is weak and may not be described as strong.
4. **Non-coding positional labels are excluded as artefacts, not ranked as candidates.**
   22 of the top 60 sweep hits were microRNA, Y_RNA, lincRNA, antisense or pseudogene
   labels.
5. **LOEUF is recorded for the 2q12.3 genes together with the reason it does not answer
   the question.** The variant is a duplication; LOEUF measures intolerance to loss. The
   correct metric is triplosensitivity and it is absent from the retrieved data.

### Tests and verification actually executed

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `pytest -q -m "not network"` | **852 passed, 0 failed** |
| Validator | `graph/validate_graph.py` | **0 errors, 0 warnings, 3 info** |
| Discovery sweep | `sweep_cognition_genes.py --primary` | 10,741 associations, 4,459 distinct mapped genes |
| Source verification | `fetch_source_metadata.py --agent orchestrator` | **42/42 verified** |
| Huguet 2024 verification | PubMed retrieval of PMID 39667348 | exists; abstract states the 2q12.3 claim attributed to it |
| 2q12.3 gene content | Ensembl REST overlap, GRCh38 | 53 gene features, 8 protein-coding |
| Constraint/expression | Open Targets GraphQL | retrieved for all 8 genes |

### Failures or unresolved uncertainty

* **The anchoring result is severe and should not be softened**: only **9 of 31** seed
  genes appear anywhere in 10,741 cognition associations, and the best of them (CKB, 5
  studies) would rank outside the top 500 in this sweep, while 151 non-seed genes have
  ≥10 distinct studies.
* The sweep ranks by distinct studies, which is still confounded by gene size, gene
  density and study overlap. It is a coverage measure, not a causal ranking, and the
  registry says so.
* The 2q12.3 duplication breakpoints, carrier count and effect size are all **unknown to
  this repository**; the eight genes listed are the CYTOBAND's content over a 2 Mb window,
  not the duplicated interval's.
* No replication of the 2q12.3 finding has been identified.
* The Open Targets schema cost four failed queries before I read the error body instead of
  guessing field names; a brain-tissue filter also matched "cortex of kidney", which is
  the same substring class of bug found twice in Task B.
* SE4 (encode latent structure, not detail) has no identified molecular control parameter
  and is flagged as the hypothesis's most likely point of failure by underspecification.

### Effect on the overall project

The project now has a compass with falsifiers attached, and a quantified answer to
whether its target list reflects the genetics: it does not.

### Next intended step

Task G (comparative intelligence 2.0), Task H (convergence layer), Task I (project truth
table), then a red-team pass over all Sprint-2 claims.

---

## 2026-09-18T18:05Z — Sprint 2 part 3: comparative v2, convergence layer, truth table, red-team pass — and three pipeline defects that changed the numbers fourfold

**Branch:** `sprint-2/causal-bridge` · **Stage:** Sprint 2 complete (tasks A–J), red-teamed

### Objective of the change

Close Sprint 2: build the species-first comparative programme (G), the convergence layer
(H) and the project truth table (I), then run the red-team pass over every Sprint-2
artefact and act on what it found rather than merely recording it.

### Files and systems changed

* **New — comparative v2:** `atlases/comparative_v2/{species_registry,trait_covariates,
  selection_signals,pathway_convergence,negative_controls}.yaml`,
  `pipelines/comparative/orthology_audit.py`.
* **New — convergence:** `atlases/convergence/dependency_rules.yaml`,
  `reports/convergence_v0_2.md`.
* **New — truth table:** `pipelines/reports/build_truth_table.py`,
  `reports/project_truth_table.{md,csv}`.
* **New — theory:** `theory/goal_gated_plasticity_retrieval.{md,yaml}`.
* **New — audit:** `evidence/audits/red_team/SPRINT2_ARTEFACTS.yaml` (15 findings).
* **Fixed:** `pipelines/registry_search/search_registry.py` (pagination, `RAN_STATUSES`
  wired in, `no_matching_trial_found` rename); all 20 `evidence/registry_searches/*.yaml`
  regenerated.
* **Corrected:** `atlases/positive_genetics/2q12_3_duplication.yaml` (LOEUF decile,
  SLC5A7 promotion removed), `theory/selective_encoding_hypothesis.md` +
  `selective_encoding_criteria.yaml` (structural exclusion **retracted**),
  `docs/integration/CODEX_HANDOFF_CONTRACT.md` (dangling adapter reference),
  `docs/PROJECT_STATUS.md` (GABRA5 "independently re-retrieved" wording),
  `reports/registry_search_v0_2.md` (all counts), `THEORY.md` (§2 cross-links).

### What was completed

Tasks G, H and I, the red-team pass, and seven corrections arising from it.

### Decisions made and why

1. **Fixed the pipeline rather than annotating it.** The red team found the registry
   search fetched one page of 50 per query and never paginated, while recording the
   registry's `totalCount` as `total_hits` — so `kept 25 of 1934` meant 25 of the **50**
   examined. Two further defects: `RAN_STATUSES` was defined and never referenced (dead
   safety code), so 95 not-yet-started trials were filed `tested_wrong_endpoint`; and 15
   trials with an empty outcomes module were recorded as having measured no cognitive
   outcome. All three convert absence of measurement into measured absence. Re-ran the
   whole search: **1,534 studies (was 360), 72 reporting gaps (was 8), 40 posted-result
   trials (was 5)**. Added `n_examined` and `screen_coverage` per query so a partial screen
   can never again read as a complete one.
2. **Did NOT re-attach the 72 reporting-gap refs.** The facets still carry the original 8
   and are *known* to be stale. Re-attaching 72 refs across seven facet files is a
   structural edit that belongs in its own change, not bolted onto a bug fix. Flagged
   prominently in the report rather than half-done.
3. **Retracted the selective-encoding "structural exclusion".** The red team showed it
   inverted the file's own guard (exclusion is selection with the sign reversed), converted
   "not assessed in this repository" into "this molecule acts tonically", and contradicted
   the file's own tagging-and-capture logic, which describes a tonic agent producing
   selective outcomes. Demoted to a prediction naming a measurement.
4. **Encoded the convergence dependency rules as an artefact, not prose.** Seven verified
   double-counting mechanisms (D001–D009) with the shared source named in each case.
5. **Comparative v2 computes nothing and says so.** `selection_signals` and
   `pathway_convergence` are `NOT_COMPUTED`; `trait_covariates` is a schema with zero
   values, because filling brain masses and lifespans from memory would corrupt exactly the
   control variables the design exists to protect.
6. **Recorded the new project-lead hypothesis** (Goal-Gated Plasticity & Retrieval) as a
   theory node with its guards fixed in advance, including the one the companion node had
   to retract.

### Tests and verification actually executed

| Check | Command | Result |
|---|---|---|
| Test suite | `pytest -q` | **852 passed** in 79s |
| Validator | `graph/validate_graph.py --strict` | **PASS** — 0 error, 0 warning, 3 info |
| Registry re-run | `search_registry.py --all` | exit 0; 20 records; 1,534 studies |
| Screen coverage | recomputed from records | 19/20 `complete`, ADORA1 `partial_capped` |
| Ensembl Compara membership | one orthology query per species | 11/13 present; crow and budgerigar **absent** |
| Species metadata | Ensembl `info/genomes` | 14/14 taxids and assemblies retrieved, snapshotted |
| Filesystem clone sweep (re-run) | `find /Users -maxdepth 6 -name .git` | 69 repos; exactly 1 with a humanintelligence remote — the repo itself |
| Truth table build | `build_truth_table.py` | 26 rows; `SUPPORTED`: **0** |

### Failures or unresolved uncertainty

* **The convergence correction is the sprint's most important result and it is negative.**
  No target exceeds three independent modalities; three (HCAR1, SLC16A3, RTN4R) rest on
  animal evidence alone. HCN1, the best-covered target, had three of its five apparent
  modalities trace to two papers.
* **The dependency rules are NOT enforced.** No validator rule and no scoring script
  applies them; `independent_source_count` de-duplicates by `source_id` only and cannot
  detect same-claim, same-sumstats or same-cohort duplication. A future agent can
  reintroduce every double-count with nothing firing. This is the largest piece of
  technical debt Sprint 2 created.
* **The comparative avian arm is inoperable**, and dangerously so: both convergent-cognition
  birds are absent from Compara while both avian *controls* are present, so a scan over
  "available birds" would return a null that is absence of measurement.
* **Eight genes failed the orthology audit** with errors rather than returning "no
  orthologue" — recorded as `query_status: failed`, not as absence.
* Eight red-team findings are **recorded and not fixed** (f8–f15): cohort overlap uncomputed
  in the discovered registry; an educational-attainment GWAS contributing to all 18
  discovery entries but flagged in one; ADHD symptom scales and a paediatric trial in the
  extraction queue; stale facet refs; an X01 working assumption laundered as a
  methodological constraint; three externally nominated genes whose provenance survives only
  in free text; silent truncation of study lists; and implicit ranking by list order.
* The ADORA1 screen remains capped at 1,000 records against 1,934 matches.

### Effect on the overall project

Sprint 2 is complete, and its net effect is to make the repository's evidence base look
**weaker and more honest** than it did at the start of the sprint. The truth table records
26 hypotheses of which zero are `SUPPORTED`; convergence turned out to be largely
double-counting; and the one pipeline that produced new evidence was systematically
under-screening. The project now has a compass (two theory nodes), a map (the truth table),
and a mechanism for detecting when it is fooling itself (the dependency rules).

### Next intended step

Re-attach the 72 reporting-gap refs; build the convergence scorer and its validator rule;
extract and red-team the 40 trials with posted cognitive results; then decide whether the
comparative programme is worth continuing given the avian resource gap.

---

## 2026-09-18T18:40Z — Truth table completed to the brief's row specification

**Branch:** `sprint-2/causal-bridge` · **Stage:** Sprint 2 complete

### Objective of the change

The first truth table covered targets and theory nodes but omitted 13 of the
architecture-level hypotheses the brief listed explicitly — the field-level claims this
project's target selection silently assumes.

### Files and systems changed

`pipelines/reports/build_truth_table.py`, regenerating
`reports/project_truth_table.{md,csv}`; `docs/PROJECT_STATUS.md` counts.

### What was completed

Added: cognition substantially genetic; single genius gene; extreme IQ qualitatively
distinct; pyramidal specificity; synaptic biology; developmental wiring; adult synaptic
control; astrocyte dominance; energy dominance; myelin/network timing; classical
neuromodulator dominance; math biology beyond g; activity-gated plasticity. **39 rows, 16
columns exactly as specified.**

### Decisions made and why

1. **`SUPPORTED` is now 1, not 0** — *cognition is substantially genetic*. Recording it as
   supported is more honest than a clean zero, and the row states why it changes nothing:
   heritability is a claim about variance in a population, not modifiability in a person.
   The only supported hypothesis is the one that cannot tell you what to do.
2. **"Synaptic biology" is recorded as UNRESOLVED and untestable from this evidence base.**
   The preponderance of synaptic evidence here measures the seed list's selection criterion,
   not biology. The discovery sweep — the first unbiased look — mostly implicates genes no
   atlas covers.
3. **"Myelin / network timing" is NOT_ASSESSED with zero artefacts**, and the row says the
   absence is a selection artefact rather than a judgement. Adult myelination is
   activity-dependent, which places it inside the mechanism class both theory nodes point at.
4. **"Single genius gene" is CONTRADICTED_IN_STUDIED_CONTEXT, stated precisely**: refuted
   for common variation, NOT refuted for rare large-effect variants — which exist, act in
   the deleterious direction, and cause neurodevelopmental disorder.

### Tests and verification actually executed

| Check | Command | Result |
|---|---|---|
| Truth table build | `build_truth_table.py` | 39 rows; SUPPORTED 1, PROMISING 2, DOWNGRADED 13, UNRESOLVED 11, CONTRADICTED 4, NOT_ASSESSED 8 |
| Column conformance | CSV header vs brief | exact match, 16 columns |
| Test suite | `pytest -q` | 852 passed |
| Validator | `validate_graph.py --strict` | PASS — 0 error, 0 warning, 3 info |

### Failures or unresolved uncertainty

* Three architecture rows (extreme cognition, myelin/network timing, math beyond g) have
  **zero supporting artefacts**. They are coverage gaps, not judgements.
* "Developmental wiring" is the most uncomfortable row: the project's premise is adult
  modifiability, and every close examination of a target's causal evidence finds the
  perturbation happened during development. That asymmetry is real and systematic.

### Effect on the overall project

The truth table now covers the field-level assumptions, not just the targets — which is
what makes it usable as a map rather than a scoreboard.

### Next intended step

Unchanged: re-attach the 72 reporting-gap refs, build the convergence scorer and its
validator rule, extract and red-team the 40 trials with posted cognitive results.

## 2026-09-22T21:10Z — Sprint 3: human cognition gene tournament + biological compression

**Branch:** `sprint-3/gene-tournament` (from `sprint-2/causal-bridge` @ `daa7354`) · **Stage:** Sprint 3 complete

### Objective of the change

Rank the whole human cognition gene universe rather than a hand-picked list, test whether its
thousands of signals compress into a few biological modules and adult-modifiable control points,
and answer the brief's twenty questions — computationally, with explicit NOT_COMPUTABLE records
wherever access blocks a part.

### Files and systems changed

New: `pipelines/gene_tournament/` (20 pipeline modules + 1 guard-test module), `atlases/gene_tournament/`,
`data/gene_tournament/`, `reports/gene_tournament/`, `reports/GENE_TOURNAMENT_FINAL.md`, raw
snapshot trees `data/raw/{gwas_catalog_tournament,gwas_catalog_tournament_studies,magma_x01,
magma_sprint3,hgnc_complete,clingen,string,opentargets_gwas_cs,europepmc_fulltext,
brain_expression,pathway_annotations,opentargets_tournament}` (bulk files gitignored, provenance
committed). Changed: `analyses/external/X01_cell_type_enrichment.yaml`,
`docs/integration/CODEX_BRANCH_AUDIT.md`, `atlases/positive_genetics/2q12_3_duplication.yaml`,
`targets/discovered/discovered_registry.yaml`, `pipelines/reports/build_truth_table.py` (+ regenerated
truth table), `tests/test_x02_ingestion.py` (one assertion, R20), `docs/OWNERSHIP.yaml`,
`docs/blackboard/RESOLUTIONS.md` (R20), `Makefile` (`identifiers`, `tournament`), `.gitignore`, `data/processed/MANIFEST.json` (refreshed by `make build`; stale at the Sprint-2 tip, audits 30 -> 31),
`docs/PROJECT_STATUS.md`.

### What was completed

* **Work location resolved.** The session's folder was an empty worktree; the Sprint 1–2 work lived
  only on `origin/sprint-2/causal-bridge`. Checked it out, rebuilt `.venv`, rebuilt the gitignored
  identifier index offline (two graph tests failed on the fresh clone until then) and added that
  step to `make build`.
* **Codex/Astra branch found** — local, never pushed, a linked worktree. Audited read-only. X01 is a
  real MAGMA 1.10 run; I recomputed the 518 MB input's sha256 (match) and re-ran the gene analysis
  from an independently built p-value file: **REPRODUCED_WITHIN_MONTE_CARLO_ERROR**.
* Parts A–S delivered (see `docs/PROJECT_STATUS.md` table). Key results: 375 Bonferroni genes = 159
  loci; extreme-tail continuity (1.13x prediction; 121/159 loci; 0 tail-significant genes); only
  synaptic sets survive the conditioned, global-FDR pathway test (6/6,200); 91% of L2G calls
  positional; 0 direction-resolved genes; 1/25 seeds Bonferroni; 11 modules with unstable
  boundaries; the "minimal control set" collapses to one gene.

### Decisions made and why

1. **Verify external work by recomputation, not by audit prose.** The replication criterion was
   first written as exact equality and returned DISCREPANT; MAGMA's gene P for strong genes comes
   from adaptive permutation, so the criterion now separates deterministic fields (NSNPS/NPARAM,
   identical for all genes) from stochastic ones — and reports the 4 genes that flip Bonferroni.
2. **EA separated at study level** (419 studies tiered) because trait labels leak: GenomicSEM EA
   decompositions, MTAG-with-EA and pleiotropy scans are filed under cognition EFO terms.
3. **Global FDR is primary for pathways**; within-collection FDR gave SynGO an advantage.
4. **Consensus dimensions restricted to those with ≥1 gene passing their own threshold; safety is a
   flag.** Adopted after the all-dimensions run was carried by near-noise dimensions (30/50 genes)
   and by LoF tolerance. Disclosed as post hoc; all-dimensions ranks kept in every row.
5. **Direction rule tightened** (≥3 strong gene-level brain colocs, ≥80% polarity-adjusted
   agreement) after the single-best-coloc rule was contradicted by most genes' other colocs.
6. **Module tail engagement measured against other cognition genes**, not the genome — the genome
   comparison credited every module with continuity inherited from gene selection.
7. **Part M's module bar aligned to global FDR**; nominal P had admitted two modules.
8. Truth-table changes applied as a **layer** so prior judgements stay readable.

### Tests and verification actually executed

* `PYTHONPATH=src .venv/bin/python -m pytest -q -m "not network"` → **879 passed, 0 failed** (81.9 s).
* `pytest pipelines/gene_tournament/test_gene_tournament.py` → 27 passed.
* `PYTHONPATH=src .venv/bin/python graph/validate_graph.py --strict` → **PASS**, 0 error / 0 warning / 3 info.
* `PYTHONPATH=src .venv/bin/python scripts/check_ownership.py` → all 819 paths owned as expected.
* X01 replication check, checksum checks, fetch-completeness audits: see `docs/PROJECT_STATUS.md`.
* Not run: `make tournament` end-to-end in a fresh clone (each stage was run individually after its
  last change); network tests (`-m network`).

### Results

Final report `reports/GENE_TOURNAMENT_FINAL.md`. Truth table: SUPPORTED 1, PROMISING 3, DOWNGRADED 13,
UNRESOLVED 13, CONTRADICTED 5, NOT_ASSESSED 4 (seven status changes, all evidenced in the rows).

### Failures and unresolved uncertainty

* **Errors of my own found and fixed during the sprint**: the Sprint-2 "branch does not exist"
  verdict; the 2q12.3 gene list (wrong genome build); an activity-dependent-transcription anchor
  that was actually the ERK cascade; an L2G support count inflated 602 vs 34 by an object-dtype `~`;
  a study classifier matching trait rules against sample text; a set-cover tie-break by symbol length
  (picked STH); a module report claiming M01 "survives everything" while the red team downgraded it.
* Part F and Part C Mode 2 not computable; Part R partial (30/83); X01 cell layer not re-derived;
  HRS/CHARGE overlap unresolved; all evidence European-ancestry.
* Subagent usage: 5 agents spawned (max allowed 8); the Open Targets agent hit a usage limit
  mid-run and its script was completed by the orchestrator.

### Effect on the overall project

The project's premise is sharpened rather than advanced: the human genetics points at synaptic
(presynaptic) biology and at a continuous polygenic architecture, but supplies **no gene with a
known direction of effect**, so no adult-modifiable control parameter can yet be named and the
chemistry gate remains closed for a concrete reason.

### Next intended step

UKB-free replication of the synaptic sets and the continuity result (§J of the final report), then
re-derivation of X01's cell layer and SuSiE-coloc for the direction near-misses.

## 2026-09-23T09:05Z — Sprint 4 protocol freeze (pre-registration before any new data)

**Branch:** `sprint-4/causal-synapse-bridge` (from `04c70ef`) · **Stage:** Sprint 4 start.

**Objective.** Freeze the primary hypothesis and every decision threshold before the within-family
(Howe 2022) or Genes & Cognition data are read, so that no threshold can move after results are seen.

**Files and systems changed.** `pipelines/sprint4/common.py` (paths, hashing, `load_frozen` that
refuses to run on a changed JSON), `pipelines/sprint4/freeze_protocol.py`,
`research/sprint4/frozen_hypotheses.json`, `research/sprint4/protocol.md`,
`data/sprint4/gene_covariates.txt` (byte-identical copy of the Sprint-3 covariates, sha256
`1335148e…`), `data/raw/sprint4/ldetect/EUR_fourier_ls-all.bed` (LDetect EUR blocks, 1,703),
`data/raw/sprint4/opengwas_metadata/gwasinfo_headers.txt`, `docs/OWNERSHIP.yaml` (Sprint-4/3.1 paths claimed), `docs/PROJECT_STATUS.md`, this ledger.
New conda env `hi-sprint4` outside the repo.

**Completed.** Six sets frozen with Entrez membership and hashes; 159 loci frozen with rule-chosen
lead SNPs (103 genome-wide significant; NT5DC2 locus lead rs6778735, SYT1 rs7963801, NEGR1
rs3101338); Gate A/B/C rules, PUMAS-style LD-aware subsampling for power calibration, unchanged
Sprint-3 direction rule, decision precedence, chemistry-gate criteria.

**Decisions and why.** (1) Freeze committed to git so the pre-registration is timestamped. (2) Set
betas are declared unsigned enrichment, with allele direction tested at loci only — MAGMA gene
statistics come from P-values. (3) The OpenGWAS website's no-login "trial" VCF link was found but
NOT used: the site states automated access needs a JWT and the brief forbids registration. (4)
Sprint 3.1 (user request mid-sprint) is run on its own branch before Sprint 4 continues; it reads
only Sprint-3 data, so it cannot contaminate the freeze.

**Tests and verification executed.** `freeze_protocol.py` ran (159 loci, 6 sets; Davies input
sha256 re-verified = `01990c3e…`); `load_frozen()` verified the recorded hash. Full test suite not
re-run for this commit (no existing code changed; new code is exercised by the freeze run) — Sprint-4
tests are added with the analyses.

**Failures / uncertainty.** `OPENGWAS_JWT` absent (Gate A blocked). f = 0.78 shrinkage taken from
the brief, pending verification from the Howe 2022 text (allowed only as a pre-data amendment).

**Effect on project.** Sprint 4 can no longer be tuned to its results.

**Next.** Sprint 3.1 correction pass; then Sprint 4 Gates B and C and the pre-data power calibration.

## 2026-09-23T10:25Z — Sprint 3.1: synaptic recon / correction pass

**Branch:** `sprint-3.1/synaptic-recon` (from `04c70ef`) · **Stage:** Sprint 3.1 (user request received
mid-Sprint-4; Sprint 4's protocol had already been frozen and pushed on its own branch, `db86aef`).

**Objective.** Audit the strongest Sprint-3 result ("synaptic biology survives, with a possible presynaptic
skew") until it can serve as a foundation: direct pre-vs-post tests, conditioning sensitivity, dependence in
the Top-50 ranking, adult terminology, NEGR1 direction independence, a synaptic system map, and the extreme-
tail 1.13x derivation. No new discovery sprint, no new tournament, no chemistry.

**Files and systems changed.** New: `pipelines/sprint3_1/` (build_inputs, run_recon_magma, analyse_recon,
leave_one_locus_out, qtl_independence_audit, extreme_tail_reassessment, build_system_map,
rank_dependency_audit [subagent], correction_blocks, write_recon_report, two test files);
`data/sprint3_1/` (full-universe covariates incl. Siletti neuronal expression, propagated GO BP/CC/MF,
recon sets, literature_curation.json [subagent]); `reports/sprint3_1/` (SYNAPTIC_RECON_REPORT.md,
pre_vs_post_joint_tests.csv, pathway_conditioning_sensitivity.csv, rank_dependency_audit.csv,
negr1_qtl_independence_audit.csv, synaptic_system_map.csv, extreme_tail_reassessment.md + supporting
tables). Modified: `write_final_report.py` and `build_red_team_and_cards.py` (re-insert dated correction
blocks on regeneration), `reports/GENE_TOURNAMENT_FINAL.md` (11 correction blocks; no text removed),
`GENE_CARDS_TOP50_ADULT.md` (relabel block), `build_truth_table.py` (Sprint-3.1 layer on 7 rows; no status
changes), truth table md/csv, OWNERSHIP, this ledger, PROJECT_STATUS.

**Completed / results.** See PROJECT_STATUS headline. Key numbers: pre-only minus post-only contrast
β −0.056 (P=0.43, spec D); synapse β 0.155 → 0.070 with neuronal conditioning; four membrane/adhesion
sets P<1e-4 in every spec, worst leave-one-locus-out P 1.9e-4; release-machinery union P=0.10; propagated
neurodevelopmental sets q<0.05 in all specs; NEGR1 1 independent unit; RPS26 resolved on units; extreme
tail ratio 0.61–1.25, signed test 112/136 (P=4e-15).

**Decisions and why.** (1) Full 18,418-gene universe for every spec, Sprint-3 run reproduced exactly as
`D_S3`. (2) GO propagated before comparing themes with SynGO. (3) Contrasts by reparametrised MAGMA joint
models; joint models matched by variable set because MAGMA renumbers them. (4) Direction threshold kept
frozen; only the counting unit (independent GWAS signal × QTL cohort) and gene-level eligibility (the
rule's own text; also frozen in the Sprint-4 protocol before this audit) changed. (5) Corrections as dated
blocks re-inserted by the report writers, so regeneration cannot lose them.

**Tests and verification executed.** `pytest pipelines/sprint3_1/` → 20 passed; D_S3 reproduction 6/6
identical; `write_final_report.py` regeneration reproduces the corrected report byte-for-byte apart from
the timestamp line. Full suite, validator and ownership check: see commit message (run before commit).

**Failures / uncertainty.** All inferences still rest on UK-Biobank-containing European GWAS; neuronal
covariate from one atlas; theme regex families coarse; HRS overlap bias argued small (shared individuals are
Zabaneh controls with constant phenotype) but not estimated. Subagents used: 2 (limit 2).

**Effect on project.** The foundation for causal work is narrower and firmer: synaptic-membrane /
adhesion enrichment (not presynaptic release), plus neurodevelopmental enrichment, and one direction-
resolved-on-units gene (RPS26) whose biology argues caution.

**Next.** Merge into Sprint 4; run the frozen power calibration and Gates B/C.

## 2026-09-23T17:00Z — Sprint 4: direct-effect causal synapse gate (decision RETRY; chemistry CLOSED)

**Branch:** `sprint-4/causal-synapse-bridge` · **Stage:** Sprint 4 complete.

**Objective.** Test, under a protocol frozen before any new data, whether the Sprint-3 synaptic signal is a
direct inherited cognition effect (Gate A, within-sibship), whether it holds outside UK Biobank (Gate B,
Genes & Cognition), and whether any survivor locus yields a variant → adult-brain gene → direction chain
(Gate C).

**Files and systems changed.** `pipelines/sprint4/` (power_calibration, gate_a_within_family, gate_b_genc,
loci_tools, classify, gate_c_finemap, gate_c_coloc, gate_c_direction, decide, write_sprint4_report,
fetch_eqtl_catalogue [subagent], joint_gene_tissue/ [subagent; FOCUS], tests); `research/sprint4/
literature_facts.md`; `data/sprint4/` (calibration replicates and summary, Gate B summary, locus/gene
query lists, eQTL dataset table, diagnostics, provenance); `data/raw/sprint4/` (G&C MAGMA gene results,
eQTL Catalogue provenance + metadata, OpenGWAS metadata extract); `reports/sprint4/` (all 13 required
outputs + within_family_summary.md, genc_summary.md); truth-table Sprint-4 layer (3 rows, no status
change); PROJECT_STATUS; this ledger. External envs (outside repo): `hi-sprint4` (R, susieR, coloc),
`hi-focus` (pyfocus 0.803).

**Completed / results.** See PROJECT_STATUS headline: Gate A NOT_TESTABLE; calibration 320/320; G&C
positive control PASS, 109/145 loci concordant (P=5e-10), sets 1/6 nominal at 2–12.5% power; SuSiE 36 loci;
68 strong adult-brain colocs; RPS26 and RHEBL1 direction-resolved on independent cohorts, neither clearing
the chemistry criteria; decision RETRY.

**Decisions and why.** (1) Protocol frozen and pushed before data. (2) Frozen f=0.78 kept (matches Howe
21.6%); f_gc_lower = verified rg 0.752 per the frozen rule. (3) Calibration re-ordered by decision priority
after a filename bug (Path.with_suffix on tags like `f0.78`) had marked every fractional-f run FAILED; the
MAGMA gene results were intact and were salvaged — no result changed, only the bookkeeping. (4) BrainSeq
excluded as non-adult per eQTL Catalogue metadata. (5) Direction counted on rows AND independent cohorts;
DIRECTION_RESOLVED needs both (stricter, not a relaxation). (6) FOCUS extended post hoc to three multi-gene
loci carrying the strongest coloc direction evidence — disclosed in the report.

**Tests and verification executed.** `pytest -m "not network"` → 935 passed; `pipelines/sprint4/
test_sprint4.py` 21 passed; validator --strict PASS; ownership 54/54. G&C md5 = Zenodo listing (3/3).

**Failures / uncertainty.** Gate A blocked (access). coloc.susie 25/36 loci (lbf network timeouts; retry
running). TGFM/cTWAS blocked (dbGaP / genome-wide scope). Two subagents stopped early on a usage limit;
their deliverables (fetcher, FOCUS CSV/provenance) were complete and were verified and extended by the
orchestrator. G&C–UKB non-overlap is by design, not explicitly stated in the source. Two arbitrary G&C rows
were displayed after the freeze while checking the format.

**Effect on project.** The Sprint-3 LOCI now replicate outside UK Biobank; the SET-level synaptic claim is
untestable at current open sample sizes; no gene has a clean causal chain, so the chemistry gate stays shut.

**Next.** Unlock Gate A (one user action); fold in remaining coloc.susie.

## 2026-09-23T19:30Z — Sprint 4 follow-up: complete coloc.susie folded in

**Branch:** `sprint-4/causal-synapse-bridge` · **Stage:** Sprint 4 complete.

**Objective.** Fold in the eQTL Catalogue SuSiE lbf retry (1,296/1,296 records OK) so multi-signal
colocalisation covers every locus that has a GWAS credible set.

**Changes / results.** coloc.susie now 590 pairs on 28 loci (was 249 on 25); strong colocs 87 (was 68).
Direction re-resolved under the unchanged rule: RPS26, RHEBL1 and now WBP2NL (22q13.2; cognition allele ->
LOWER expression, 3 independent adult cohorts). WBP2NL fails the credible locus-to-gene criterion (FOCUS
primary favours CYP2D6) and is testis-enriched: likely passenger. Decision unchanged (RETRY); chemistry gate
unchanged (CLOSED). Reports, survivors, negative results and decision.json regenerated.

**Verification.** pytest sprint4 tests + full suite rerun (see commit message); validator; ownership.

**Next.** Unlock Gate A (user action).

## 2026-09-23T21:20Z — Sprint 5 protocol freeze (causal cognition gene resolution)

**Branch:** `sprint-5/causal-cognition-gene-resolution` (new, from `e50eb4f`) · **Stage:** Sprint 5 start.

**Objective.** Fix every Sprint-5 evidence class, independence rule, ranking stratum, convergence test and
gate before integrating any new data stream, so labels cannot be tuned to results.

**Files / systems changed.** `research/sprint5/protocol.md`, `research/sprint5/protocol_rules.json`
(sha256 0f464218…), `pipelines/sprint5/common.py` (load_rules hash check; stdlib HTTP helper),
`pipelines/sprint5/build_query_variants.py`, `data/sprint5/query_variants_cognition.csv` + provenance,
`docs/OWNERSHIP.yaml` (Sprint-5 paths), status and ledger.

**Completed.** Gate A re-checked: files absent and no JWT, so NOT_TESTABLE is preserved. Query list built:
1,915 rows, 1,573 rsIDs, 1,572 mapped to GRCh38 (Ensembl REST), 1 with no primary mapping (kept, flagged).

**Decisions and why.**
- Bulk and single-cell QTLs collapse into one class if donors overlap. This avoids counting the same donors twice.
- L2G is folded into the class of its SHAP driver. It aggregates features that are already counted.
- FOCUS is a contradiction check only, because it uses the same eQTL cohorts.
- The Zabaneh extreme-IQ data are sensitivity-only, because of the HRS overlap with Davies.

**Tests.** None run for this commit beyond the script executing (exit 0). The protocol hash is checked by
`load_rules` at run time.

**Failures / uncertainty.** None yet. Research subagents are running (brainSCOPE, math, rare coding/CNV,
AlphaGenome/datasets/tools).

**Effect.** Sprint 5 has a pre-registered rulebook.

**Next.** Open Targets current-release refresh; evidence graph; integrate subagent streams.

## 2026-09-23T~22:55Z — Sprint 5 complete: causal cognition gene resolution

**Branch:** `sprint-5/causal-cognition-gene-resolution` · **Stage:** Sprint 5 complete.

*Correction to the previous entry:* its heading time ("21:20Z") was approximate. The protocol-freeze commit `1a08f10` was made at about 21:10Z.

**Objective.** Resolve variant → gene → cell → timing → direction for the replicated cognition loci under a pre-registered rulebook, and rank genes and loci without double-counting dependent evidence.

**Files / systems.**

- `pipelines/sprint5/*`: 27 scripts, plus the tests.
- `reports/sprint5/*`: 27 required outputs plus 20 dossiers.
- `data/sprint5/*`
- `research/sprint5/*`: protocol, amendments A1–A2, research log R01–R17, subagent logs.
- `data/raw/sprint5/*` (provenance).
- A Sprint-4 correction block in `CAUSAL_SYNAPSE_GATE.md`.
- `docs/PROJECT_STATUS.md`.

**Completed.**

- **Open Targets 26.06 variant layer.** 117 of 130 L2G calls are positional; 22,856 E2G links.
- **Locus Bayes factors on G&C.** L1: ATXN2L and AKAP6. L2: 14 signals.
- **GenLang sensitivity lineage.** 106 of 141 concordant; it overlaps Davies through BATS.
- **brainSCOPE lookup.** 17 cell types; colocalisation NOT_TESTABLE; RPS26 ↑ and WBP2NL ↓ in 10 cell types each.
- **Developmental colocalisation.** 20 strong of 969 tests; NT5DC2 ↓ fetal.
- **Rare coding.** KDM5B, ANKRD12, RC3H2 and CACNA1A; UKB only; loss of function.
- **CNV re-audit.** 2q12.3 is nominal.
- **Math-53 verified** (Giannelis 2025). Inverted against g; SLC39A8 is the only shared gene.
- **Convergence tests T1–T5:** null.
- **Evidence graph:** 1,460 units, 2,146 edges.
- **Gene classes:** 2 CAUSAL_GENE_MODERATE (KIFC2, DNPH1); none HIGH; no gene at D1.
- **Modifiability map; decision.json** (chemistry gate CLOSED).
- **20 red-team dossiers.**

**Decisions and why.**

- **Amendment A1:** residual labels for candidates that fit no frozen class.
- **Amendment A2:** the KDE-Tweedie estimate is unstable in the tail (it mapped 8.33 to −1.99), so it was replaced by empirical-Bayes shrinkage. Disclosed as post-view. The effect on Sprint 4 is descriptive only.
- **Interpretation A3:** causal-gene rank only for genes with gene-level evidence.
- **GRN links not counted** as ENHANCER_LINK. The sensitivity result is disclosed.
- **Literature files kept local-only** (copyright).
- **The Bryois 2022 single-cell colocalisation was deferred** (tens of GB of downloads; ROSMAP donor overlap). It is the recorded next computation.

**Tests executed.**

- Full suite: 947 passed.
- `test_sprint5.py`: 12 passed.
- Sprint 4 and Sprint 5 guards in both orders: 33 passed each.
- Validator --strict: PASS.
- Ownership: OK.

**Failures / uncertainty.**

- **Crashes, fixed and rerun:**
  - the developmental colocalisation crashed once on an empty harmonisation;
  - the full pytest run failed until a Sprint-4/5 `common` module collision was isolated;
  - a duplicate evidence-unit ID was found.
- **Earlier mistakes, corrected before commit:**
  - the amendment timestamps were first written with incorrect clock times;
  - the ledger first marked GenLang as independent.
- **Access blocks:** Gate A, AlphaGenome and brainSCOPE colocalisation.

**Effect.** The project now knows its loci replicate but its genes do not resolve. The next information has to come from within-family data and from cell-type colocalisation.

**Next.** Gate A user action; coloc.susie against Bryois 2022 at the 16 L1/L2 loci.

## 2026-09-24T~09:05Z — Sprint 5A start: protocol freeze, Gate A data fetched, historical foundations

**Branch:** `sprint-5a/open-data-exhaustion` (new, from `e88c2fb`) · **Stage:** Sprint 5A start.

**Objective.** Freeze the Sprint-5A integration rules before any new results, and unlock Gate A with the user's OpenGWAS token.

**Files / systems.**

- `research/sprint5a/protocol.md` and `protocol_rules.json` (sha256 1c1aa071…).
- `research/sprint5a/historical_foundations.md`.
- `pipelines/sprint5a/g1000_freq.py`.
- `pipelines/sprint4/gate_a_within_family.py`: OpenGWAS v4 POST gwasinfo; `.syngo` gsa path fix; AF from the reference; EB sensitivity column.
- `research/sprint4/protocol.md`: implementation note, not a rule change.
- `data/sprint4/gate_a_access.json`: status FETCHED; contains no token or URLs.
- `docs/OWNERSHIP.yaml`, status and ledger.

**Completed.**

- Both Howe VCFs fetched and identity-checked: 6,719,302 variants each.
- The 1000G EUR A1 frequencies were computed for 22.7M SNPs. They match the Sprint-4 MAFs to within 1e-8.
- brainSCOPE provenance audit: first analytic use was Sprint 5.

**Decisions and why.**

- The VCFs have no AF, so AF is taken from the project LD reference. This is needed for the frozen effective-N filter and the palindromic-SNP rule.
- The frozen KDE-Tweedie estimate is kept as the primary Gate-A expectation, with EB as a disclosed sensitivity, because the rules were frozen.
- The token is passed only through the environment and never written to disk.

**Tests.** `pytest pipelines/sprint4/test_sprint4.py`: 21 passed after the patch.

**Failures / uncertainty.**

- The first Gate-A fetch failed with a 404; the endpoint changed in API v4.
- The first analyse run crashed on the `.syngo` path bug before any result was produced.
- The parse check displayed 3 arbitrary chromosome-1 rows of each VCF; this is disclosed.

**Next.** Gate-A results; integrate the agent streams.

## 2026-09-24T~10:05Z — Sprint 5A checkpoint (after an unexpected reboot)

**Branch:** `sprint-5a/open-data-exhaustion` · **Stage:** Sprint 5A in progress.

**Objective.** Commit and push the finished Sprint-5A layers after a machine reboot killed every running job, and record the resume.

**Files.**

- `pipelines/sprint5a/`:
  - `opentargets_credible_set_refresh.py`
  - `alphagenome_summarise.py`
  - `prep_ldsc_inputs.py`
  - `genomicsem_lava.R`
  - `build_canonical_inputs.py`
- `reports/sprint5a/`:
  - `opentargets_2606_refresh.parquet` and `opentargets_2606_colocs.parquet`
  - `alphagenome_*`
  - `ldsc_*`
  - `genomicsem_commonfactor_*`
  - `USER_ACCESS_REQUIRED.md`
- `data/sprint5a/`: provenance, canonical inputs, phenotype datasets, AlphaGenome query lists, LAVA loci.
- `research/sprint5a/phenotype_model.md`.

**Completed.**

- **Open Targets 26.06**, re-verified live. The first pull fetched only GWAS–GWAS colocalisations; it was refetched with QTL study types.
- **AlphaGenome Atlas** queries, run with the user's key through the environment only; the key is never written.
  - A chromosome "6.0" formatting bug was fixed before the rerun.
  - 60 missing cognition alleles were filled from Davies (48 resolved).
- **Zabaneh chrX SE mis-scaling found.** LDSC now uses Z = sign(log OR) × probit(P/2).
- **GenomicSEM** needed lavaan 0.6-19; 0.7.2 breaks it.
- **LDSC and common factor** results: see the status document.

**Decisions.**

- AlphaGenome direction calls get no weight unless measured data agree. The measured comparators are Sprint-4 bulk colocalisation, brainSCOPE and developmental colocalisation; Open Targets is a secondary comparator.
- A factor GWAS is not run: the common factor is dominated by Davies (loading 0.97, N 282k), so it would reproduce Davies' loci.

**Tests.** Not run for this checkpoint. The full suite runs at sprint end.

**Failures / uncertainty.**

- A reboot at about 09:58Z killed:
  - the Gate-A calibration (16 of 120 replicates done; resumed, seeded, finished replicates skipped);
  - LAVA (resumed);
  - three agents (resumed from their transcripts).
- The earlier GenomicSEM fallback fit (a Heywood case) was discarded.

**Next.** Finish Gate A, LAVA and the agent streams; then integration, shortlists, dossiers and the report.

## 2026-09-24T~13:00Z — Sprint 5A complete (open-data exhaustion + causal cognition integration)

**Branch:** `sprint-5a/open-data-exhaustion` · **Stage:** Sprint 5A complete.

**Objective.** Finish every open computational layer, run Gate A with the frozen analysis, rerun the frozen Sprint-5 classifier on the integrated evidence, and deliver the shortlists, dossiers, the final report and the gated-data queue.

**Files and systems changed.**

- **`pipelines/sprint4/gate_a_within_family.py`:** POST `gwasinfo`; `.syngo` path; AF filled from the 1000G reference; EB sensitivity columns.
- **`pipelines/sprint5/{common,locus_confidence,build_evidence_graph,classify_genes}.py`:** env-gated S5A hooks. With the hooks off, the Sprint-5 outputs are byte-identical.
- **`pipelines/sprint5a/*`:** about 40 scripts covering:
  - brainSCOPE, devBrain, GENCODE and GTEx V11;
  - single-cell colocalisation and HyPrColoc;
  - PolyFun and PoPS;
  - the integrated rerun, compare, direction recount, variant table, convergence/shortlists, the Gate-A decision and tests.
- **`reports/sprint4/`:** Gate-A outputs regenerated; `decision_gate_a_update.json`; update block U-S5A-1 in `CAUSAL_SYNAPSE_GATE.md`.
- **`reports/sprint5a/`:** all layer outputs, `s5_integrated/`, shortlists A/B/C, 10 dossiers, `SPRINT5A_FINAL.md`, `USER_ACCESS_REQUIRED.md`.
- **`data/sprint5a/`:** small derived data and provenance. **`data/raw/sprint5a/*/PROVENANCE.json`:** URL and sha256 for every large download (the files themselves stay in the gitignored `data/interim`).
- **`research/sprint5a/`:** agent notes, dossier notes, research log.

**Completed.**

- **Gate A:** 109/146 loci concordant (P 9.9e-10; slope 0.69). The frozen precedence gives **CONTINUE**; the set level is fragile (synapse P 0.018 at 7.5% power).
- **Integrated rerun:**
  - L1 11 / L2 27 / L3 63 / L4 42 / NT 9;
  - MODERATE: DNPH1, TTBK1 (tied) and FAM131A;
  - KIFC2 and CYP2D6 drop because their loci fall to L4;
  - SH2B1 is resolved on rows only; TUFM is unresolved (single cells conflict with bulk).
- **Shortlists:** C is empty, not forced. brainSCOPE colocalisation is not testable.
- **Other layers:** single-cell colocalisation, HyPrColoc, developmental timing, GTEx V11, Open Targets 26.06, AlphaGenome, LDSC/GenomicSEM, LAVA, PolyFun and PoPS are all complete.

**Decisions and why.**

- **`decide.py` was not rerun.** It hard-codes the untestable Gate-A branch and re-fetches. The frozen precedence was applied literally in `gate_a_decision.py` instead.
- **The within-family columns are written only when S5A is on**, so Sprint 5 stays reproducible.
- **Inverted math-proxy SNPs are labelled "not convergence".**
- **PoPS and PolyFun are reported but never counted.**

**Tests and verification actually executed.**

- `PYTHONPATH=src .venv/bin/python -m pytest -q -m "not network"`: **961 passed**, 0 failed (95.8 s). It includes the Sprint-5A guards: no credentials in tracked files; brainSCOPE colocalisation never fabricated; AlphaGenome weighted only where measured data agree; single-cell data never create cohort units; shortlist C not forced; Sprint-5 outputs untouched; dossier cap.
- `graph/validate_graph.py --strict`: PASS (0 errors, 0 warnings, 3 info).
- `scripts/check_ownership.py`: all 191 paths owned as expected.
- **Pre-commit scans:** no staged file over 5 MiB; no credential pattern outside the test's own literal strings; no personal email; no `.env`, `interim`, PDF or venv paths.

**Results.** See `reports/sprint5a/SPRINT5A_FINAL.md` and `docs/PROJECT_STATUS.md`.

**Failures and unresolved uncertainty.**

- The reboot (~09:58Z) and one user-requested stop interrupted the jobs; all resumed from verified state.
- **PoPS:** chr1–5 used OpenBLAS and chr6–22 Accelerate; the direct chr1 cross-check failed on a command-line error and was not rerun. 29 genes are unscored.
- **PoPS within-locus rank is uninformative at 94/158 single-gene loci.** An earlier draft of the final report cited such ranks; it was corrected before this commit.
- TTBK1 and FAM131A are fragile MODERATE calls.
- Nine loci are discordant beyond noise within families.
- The single-cell data share ROSMAP donors.
- AlphaGenome disagrees with measured QTLs 19 times against 9 agreements.
- TGFM, multi-ancestry fine-mapping and rare-variant burden were not run (access or data); cTWAS is not yet run (compute).

**Effect on the project.**

- This is the first within-family evidence: the loci act directly.
- Gene assignment and direction remain the bottleneck, so the chemistry / intervention gate stays CLOSED.

**Next.**

- The user should rotate both credentials.
- Obtain brainSCOPE full statistics (Synapse DUC), or the Tan 2025 family GWAS.
- Run genome-wide cTWAS.
- Separate DNPH1 from TTBK1.
