# Intelligence Blueprint

**A fully computational causal-control framework for adult human cognitive capacity.**

The scientific objective is to identify the **smallest set of adult-modifiable
biological control parameters** that determine how much useful computation, learning,
abstraction, working memory, transfer and durable knowledge a healthy adult human
brain can achieve.

This is **not** a nootropics list, and **not** a search for an "intelligence gene".
It is an attempt to build the causal map, the evidence accounting, and the uncertainty
model that would be needed before anyone could sensibly reason about cognitive
capacity as a control problem.

---

## 1. The computational-only constraint

All work in this repository is computational. No wet-lab, in-vitro, ex-vivo, animal or
human experiment is performed, planned, designed or recommended here — including
self-experimentation. Existing experimental results are **ingested as evidence with
provenance**; ingesting a result never implies endorsement of repeating or acting on
it. No output contains a dose, route, regimen or protocol.

The policy and the mechanisms that enforce it (closed action-type enum, red-team
check, chemistry gate) are in [`docs/COMPUTATIONAL_ONLY_POLICY.md`](docs/COMPUTATIONAL_ONLY_POLICY.md).

Permitted work: computational analysis, data integration, causal inference, knowledge
graph construction, structural bioinformatics, cheminformatics, virtual screening,
molecular simulation, machine learning, statistical genetics, comparative genomics,
and literature/evidence synthesis.

## 2. Architecture — three linked graph layers

**Layer 1 — Evidence graph (epistemology).**
`Paper`, `Dataset`, `Experiment`, `ClinicalTrial`, `Claim`, `Replication`, `Audit`,
`Species`, `Measurement`, related by `REPORTS`, `SUPPORTS`, `CONTRADICTED_BY`,
`REPLICATED_BY`, `FAILED_TO_REPLICATE_BY`. Every substantive biological claim lives
here first.

**Layer 2 — Biological causal graph.**
`Variant → Gene → Transcript → Protein → MolecularProcess → CellType → BrainRegion →
Circuit → StateVariable → ComputationalPrimitive → CognitivePhenotype`.

**Layer 3 — Intervention graph.**
`Compound`, `Drug`, `Biologic`, `RNAIntervention`, `GeneRegulation`,
`MetabolicIntervention`, `Neurotechnology`, `Target`, `Mechanism`, `StateVariable`,
`DesiredEffect`, `AdverseEffect`, related by `TARGETS`, `AGONISES`, `ANTAGONISES`,
`POTENTIATES`, `NEGATIVELY_MODULATES`, `INHIBITS`, `UPREGULATES`, `DOWNREGULATES`,
`CHANGES_STATE`, `INCREASES_RISK`, `DECREASES_RISK`.

**Binding rule:** every edge in layers 2 and 3 is compiled from a claim that carries
provenance. Edges without a claim exist only for identifier/ontology facts and are
labelled `reference_data` or `ontology_axiom`. Binding to a target is never treated as
efficacy.

## 3. The dynamic state model

Cognitive capacity is represented as a dynamical system, not a score:

```
X(t+1) = F(X(t), U(t), E(t), Θ) + noise
```

`X` latent biological/cognitive state · `U` intervention · `E`
experience/environment/task · `Θ` slower individual biological parameters.

State domains (`state_model/`): **cognition · power · efficiency · plasticity ·
workspace · consolidation · stability · safety**.

Two rules apply to every state variable:

* **Maximising is not assumed to be good.** Each variable carries a response-shape
  field (`linear`, `threshold`, `inverted_u`, `u_shaped`, `state_dependent`,
  `unknown`), defaulting to `unknown` until evidence says otherwise.
* **Safety variables are constraints, not costs to be traded away.**

## 4. Evidence principles

1. **Provenance or silence.** A claim without a machine-verified source is not written.
2. **Citations are verified, not remembered.** Every PMID/NCT/GCST/DOI is checked
   against its registry, with the raw response snapshotted immutably and titles
   matched by similarity. A fabricated identifier fails validation
   (`scripts/fetch_source_metadata.py`).
3. **Identifiers are fetched, never typed.** HGNC is the authority for gene
   identifiers (`scripts/fetch_gene_identifiers.py`).
4. **No fake precision.** Curated records may express only ordinal evidence levels.
   Every number in a report comes from a named model under `models/`, labelled with its
   calibration status. `0.85` never appears because it "feels right".
5. **Six distinctions are required fields, not caveats:** association vs causation,
   locus vs gene, development vs adulthood, rescue vs enhancement, animal memory vs
   human intelligence, educational attainment vs intelligence.
6. **Paper count is not evidence quality.** The ranking model is tested to be
   invariant to duplicated evidence.
7. **The red team can downgrade, never delete.** Provenance is append-only.
8. **Unknown is a first-class value** that widens uncertainty rather than quietly
   lowering a score.

## 5. Execution model — a blackboard, not a swarm

The Git repository is the shared blackboard. Agents never chat; they read and write
structured artefacts in lanes they own, and the orchestrator enforces gates. Roles,
ownership and gates: [`docs/BLACKBOARD_PROTOCOL.md`](docs/BLACKBOARD_PROTOCOL.md),
[`docs/OWNERSHIP.yaml`](docs/OWNERSHIP.yaml),
[`docs/AGENT_REGISTRY.yaml`](docs/AGENT_REGISTRY.yaml).

## 6. First milestone — AlphaCognition v0.1

Rank candidate adult-modifiable causal control points of cognition using human
genetics plus mechanistic evidence, reporting for each target an explicit,
**uncalibrated** uncertainty over six dimensions:

`P(causal cognition relevance)` · `P(adult modifiability)` ·
`P(supra-normal potential)` · `P(far transfer potential)` ·
`P(safe controllable window)` · `P(human translation)`

These are **subjective, model-derived and explicitly uncalibrated**. The deliverable is
a ranked table with rank intervals and a red-team audit attached to every row —
`reports/target_ranking_v0_1.csv`, marked PRELIMINARY.

## 7. Repository layout

```
ontology/      node, edge, primitive and state-variable type system
schemas/       JSON Schemas for every record type
state_model/   state variables per domain + dynamics specification
atlases/       per-domain evidence work: assessments, interventions, annotations
evidence/      sources, claims, audits (the epistemic core)
targets/       seed registry + per-target dossiers
graph/         CLI entry points: build / validate / query / export
models/        ranking, causal and uncertainty model specifications + code
pipelines/     reproducible ingestion pipelines per domain
src/blueprint/ the library behind the CLIs
data/          raw (immutable snapshots) / interim / processed
reports/       generated deliverables
docs/          contracts, protocol, status, ledger, decisions
tests/         validation, determinism and model-behaviour tests
scripts/       provenance tooling and repository checks
```

## 8. Quickstart

```bash
make setup            # create .venv and install the project
make hooks            # install the commit-continuity + validation git hooks
make fetch-identifiers  # resolve seed gene identifiers from HGNC (network)
make fetch-sources      # verify every cited source against its registry (network)
make build            # validate records, build Parquet/DuckDB store, compile the graph
make rank reports     # run the ranking model and generate reports/
make test             # offline test suite
```

Optional environment variables (never committed): `NCBI_API_KEY` (raises the NCBI rate
limit), `ALPHAGENOME_API_KEY` (not used in Sprint 1).

## 9. Current status

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the authoritative snapshot
and [`docs/PROJECT_LEDGER.md`](docs/PROJECT_LEDGER.md) for the chronological record.
Sprint 1 is in progress; nothing in `reports/` should be read as a finding about
biology until it carries a red-team audit and an explicit uncertainty statement.
