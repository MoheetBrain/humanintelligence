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
