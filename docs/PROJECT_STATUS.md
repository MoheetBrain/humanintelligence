# Project Status

*Snapshot generated 2026-09-17 (UTC) — Sprint 1, scaffolding commit.*

## Project Objective

Build a fully computational causal-control framework for adult human cognitive
capacity: identify the smallest set of **adult-modifiable biological control
parameters** that determine how much useful computation, learning, abstraction,
working memory, transfer and durable knowledge a healthy adult human brain can
achieve.

This is not a nootropics list and not a search for an "intelligence gene". All work
performed here is computational (see `docs/COMPUTATIONAL_ONLY_POLICY.md`); external
wet-lab, animal and clinical results are ingested as evidence with provenance and are
never repeated, planned or recommended by this project.

## Current Stage

Sprint 1 — *infrastructure and first evidence ingestion*. Scaffolding and contracts
complete; ontology/schemas not yet written; no evidence records exist yet.

## Current Branch

`sprint-1/foundation` (base: `main` @ `9f0d552`, which contained only a README).

## Current System Architecture

Three linked graph layers, compiled from curated records:

1. **Evidence graph** — Paper / Dataset / ClinicalTrial / Claim / Audit nodes;
   `REPORTS`, `SUPPORTS`, `CONTRADICTED_BY`, `REPLICATED_BY`, `FAILED_TO_REPLICATE_BY`.
2. **Biological causal graph** — Variant → Gene → Transcript → Protein →
   MolecularProcess → CellType → BrainRegion → Circuit → StateVariable →
   ComputationalPrimitive → CognitivePhenotype.
3. **Intervention graph** — Compound / Drug / Biologic / RNAIntervention /
   GeneRegulation / MetabolicIntervention / Neurotechnology / Target / Mechanism /
   StateVariable / DesiredEffect / AdverseEffect.

Every biological or interventional edge is derived from a claim that carries
provenance; only identifier/ontology edges are claim-free, and those are labelled
`reference_data` or `ontology_axiom`.

Storage for Sprint 1 is deliberately file-first: curated YAML → Parquet → DuckDB →
NetworkX, with Neo4j export deferred to an exporter interface.

Execution model is a **blackboard**: the repository is the shared medium, agents own
disjoint path sets, and the orchestrator enforces gates
(`docs/BLACKBOARD_PROTOCOL.md`).

## Capabilities Implemented

* Repository scaffold, dependency pinning (`pyproject.toml`), reproducible `Makefile`
  split into network (`fetch-*`) and offline targets.
* Data contract v0.1.0 (`docs/DATA_CONTRACT.md`): identifier conventions, record
  schemas, controlled vocabularies, 20 validation rules.
* Blackboard protocol, path-ownership map and ownership checker
  (`scripts/check_ownership.py`).
* Seed target registry: 27 targets (13 deep / 14 shallow dossiers) with lead-atlas
  assignment, no hand-written accessions.
* **Machine-checked citation verification** (`scripts/fetch_source_metadata.py`):
  PubMed ESummary, ClinicalTrials.gov v2, GWAS Catalog v2 and DOI→PMID resolution,
  with immutable raw snapshots, title-similarity matching, retraction flags and an
  offline rebuild path.
* **Machine-resolved gene identifiers** (`scripts/fetch_gene_identifiers.py`): HGNC as
  the naming authority; alias/withdrawn symbols reported rather than guessed.
* Commit-continuity + validation pre-commit gate (`.githooks/pre-commit`,
  installed via `scripts/install-git-hooks.sh`).
* Task DAG with a closed, computational-only `action_type` enum.

## Work Completed to Date

1. Cloned the remote repository (contained only `README.md`), created
   `sprint-1/foundation`.
2. Created the Python 3.12 environment and installed pydantic 2.13.5, PyYAML 6.0.3,
   jsonschema 4.26.0, pandas 3.0.5, duckdb 1.5.5, pyarrow 25.0.1, networkx 3.6.1,
   pytest 9.1.1.
3. Confirmed reachability of every provenance API the design depends on: NCBI
   E-utilities, ClinicalTrials.gov v2, Open Targets GraphQL, HGNC REST, GWAS Catalog
   REST v2 (release 2026-09-13).
4. Wrote the contracts, ownership map, task DAG, agent registry and policy documents.
5. Resolved all 31 seed gene symbols against HGNC (31/31 approved) and recorded 31
   immutable raw snapshots plus a manifest.

## Important Files and Artifacts

| Path | Role |
|------|------|
| `docs/DATA_CONTRACT.md` | authoritative record/ID/validation contract |
| `docs/BLACKBOARD_PROTOCOL.md` | agent roles, gates, anti-hallucination rules |
| `docs/OWNERSHIP.yaml` | path ownership per agent |
| `docs/TASK_DAG.yaml` | task graph, statuses, computational-only action enum |
| `docs/AGENT_REGISTRY.yaml` | which agents ran and what they were responsible for |
| `targets/seed_registry.yaml` | 27 seed targets with lead-atlas assignment |
| `scripts/fetch_source_metadata.py` | citation verification against registries |
| `scripts/fetch_gene_identifiers.py` | HGNC identifier resolution |
| `data/raw/MANIFEST.jsonl` | checksummed manifest of every raw snapshot |
| `.githooks/pre-commit` | continuity + validation gate |

## Data Sources and Provenance

| Source | Access | Use | Snapshot location |
|--------|--------|-----|-------------------|
| HGNC REST | public, no key | gene identifier resolution | `data/raw/hgnc/<date>/` |
| NCBI E-utilities | public, optional `NCBI_API_KEY` | citation verification, taxonomy | `data/raw/pubmed_esummary/<date>/` |
| ClinicalTrials.gov API v2 | public | trial verification, failed/terminated trials | `data/raw/ctgov_v2/<date>/` |
| GWAS Catalog REST v2 | public (release 2026-09-13) | cognitive-trait associations | `data/raw/gwas_catalog/<date>/` |
| Open Targets Platform GraphQL | public | tractability, safety annotations | `data/raw/opentargets/<date>/` |
| AlphaGenome | **requires API key — absent** | variant effect prediction | not retrieved |

No credentials are stored in the repository; keys are read from environment variables
and scrubbed from manifests.

## Decisions and Rationale

1. **Identifiers are fetched, never typed.** Hallucinated accessions are the most
   likely failure mode of an LLM-assembled knowledge graph, so HGNC/PubMed/CT.gov are
   the authorities and mismatches fail validation.
2. **No hand-written probabilities.** Curated records may only express ordinal
   evidence levels; every number in a report must come from a named model under
   `models/`. This directly implements the brief's prohibition on fake precision.
3. **Every edge needs a claim.** The biological and intervention layers are compiled
   from claims, so provenance cannot be lost in graph construction.
4. **Red team can downgrade but not delete.** Enforced by validator rules plus an
   append-only claim registry lock.
5. **File-first storage.** YAML/JSONL → Parquet → DuckDB → NetworkX keeps Sprint 1
   diffable, testable and offline-reproducible; Neo4j remains an export target.
6. **Blackboard, not swarm.** Seven domain/infra agents write disjoint artefacts; no
   agent-to-agent chat, so no citation cascades between agents.

## Verification and Test Results

| Check | Command | Result (2026-09-17) |
|-------|---------|---------------------|
| HGNC resolution of seed symbols | `.venv/bin/python scripts/fetch_gene_identifiers.py` | **31/31 approved symbols**; snapshots + manifest written |
| Provenance API reachability | ad-hoc `urllib` probes (NCBI, CT.gov, Open Targets, HGNC, GWAS Catalog) | all five reachable |
| PubMed metadata retrieval | MCP PubMed `get_article_metadata` on two known PMIDs | returned matching titles + DOIs |
| Script syntax | `python -c "ast.parse(...)"` on `scripts/fetch_source_metadata.py` | parsed |
| Test suite | `make test` | **not run — no tests exist yet** |
| Validator | `make validate` | **not run — validator not written yet** |

## Known Failures and Limitations

* No ontology, schema, validator, graph, store, ranking model or evidence record
  exists yet; the repository is scaffolding plus provenance tooling.
* `scripts/fetch_source_metadata.py` has not yet been exercised against a real source
  file (none exists); only its syntax and design have been checked.
* Title-similarity verification will flag legitimately abbreviated titles; the
  threshold (0.90) is a judgement call and may need tuning.
* ClinicalTrials.gov verification compares against official/brief titles, which agents
  frequently paraphrase; expect mismatches to need manual reconciliation.
* AlphaGenome cannot be used in this environment (no API key).

## Risks and Technical Debt

| Risk | Mitigation status |
|------|-------------------|
| Hallucinated citations | mitigated by registry verification; **not yet exercised** |
| Hallucinated mechanisms with real citations | partially mitigated (`extraction.content_checked`); relies on red-team audit |
| Parallel agents writing outside their lanes | ownership checker written; enforcement is post-hoc |
| Ranking model producing authoritative-looking numbers from weak evidence | contract forbids hand-written numbers; report must carry PRELIMINARY marking and rank intervals |
| Seed-list anchoring (the 27 targets are the brief's examples) | registry marks `seed_origin: user_seed_list`; agents may propose additions; red team may deprioritise any of them |
| Single-cohort dependence (UK Biobank dominates cognitive GWAS) | to be recorded per claim and audited as `citation_dependence` |

## Current Blockers

None. The AlphaGenome module is deferred (no API key), which was already planned for a
later sprint.

## Exact Next Actions

1. Spawn the Ontology/Graph Architect: `ontology/`, `schemas/`, `state_model/`,
   pydantic models, validators, tests (gate G1).
2. Freeze the schema, then spawn AlphaCognition, Brakes, Power, Comparative and the
   ranking-model half of Integration in parallel.
3. Run `make fetch-sources` per agent; every source must reach `status: verified`.
4. Spawn the Red Team after the atlases land; require full check coverage per target.
5. Run the integration pass, build the graph, generate
   `reports/intelligence_graph_v0_1.html` and `reports/target_ranking_v0_1.csv`.
6. Run `make test`; record real results in this document and in the ledger.
