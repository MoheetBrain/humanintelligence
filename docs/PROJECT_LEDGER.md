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
