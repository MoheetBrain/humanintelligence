# Decision Record

Architecture decisions with their rationale, the alternatives considered, and the
consequences accepted. New decisions are appended; superseded decisions are marked, not
deleted.

---

## D001 — Identifiers and citations are fetched from authorities, never typed

*2026-09-17 · accepted*

**Context.** Every record in this repository is produced by a language model. The
dominant failure mode of LLM-assembled knowledge graphs is a confident, well-formatted
citation to a paper that does not exist, or to a real paper that says something else.

**Decision.** Gene identifiers come from HGNC; citations are verified against PubMed,
ClinicalTrials.gov and the GWAS Catalog. Raw responses are snapshotted immutably with
sha256 manifests. Verification compares the agent's claimed title to the registry title
by normalised similarity, and the validator treats anything other than `verified` as a
defect.

**Alternatives.** (a) Trust the agents and spot-check — rejected, because spot-checking
does not scale and a single fabricated identifier poisons downstream analysis.
(b) Require a human reviewer per claim — rejected for Sprint 1 as it makes the
blackboard useless, and it does not remove the need for mechanical verification.

**Consequences.** Network access is required to *add* evidence, but not to rebuild
anything. Legitimately abbreviated titles will produce false mismatches that need
reconciliation. Sources without a registry (books, some datasets) are explicitly
`unsupported_registry` rather than silently accepted.

---

## D002 — No hand-written probabilities anywhere in curated records

*2026-09-17 · accepted*

**Context.** The project brief prohibits fake precision. In practice, an LLM asked for
a confidence will produce `0.85` for anything.

**Decision.** Curated records may express uncertainty only as an ordinal level on a
published rubric (`evidence_strength_v1`, levels 0–4). Every number in a report must be
produced by a named model under `models/` and must carry `calibration_status`. The
validator rejects float probabilities in curated YAML (rule V9).

**Alternatives.** (a) Allow subjective probabilities with a `subjective: true` flag —
rejected, because the flag gets ignored downstream and the number does not.
(b) Allow verbal confidence labels only — rejected, because they cannot be propagated
through an uncertainty model.

**Consequences.** The ranking model must map ordinal levels to distributions, and that
mapping is itself a subjective choice — but it is *one* documented, versioned,
testable choice rather than hundreds of invisible ones.

---

## D003 — Evidence and counter-evidence are graded separately

*2026-09-17 · accepted (amends the initial facet design)*

**Context.** A single confidence score cannot distinguish "nobody has looked" from "it
was tested and it failed". Those are opposite epistemic situations, and the second is
exactly what this project must not lose.

**Decision.** Each facet carries `level` (supporting-evidence strength),
`counter_level` (contradicting-evidence strength), and `assessment_status`
(`assessed` / `not_assessed` / `not_applicable`) with `level: null` when not assessed.
Writing `0` for an unexamined facet is a contract violation.

**Consequences.** Every assessment is roughly twice the work, and the ranking model
must define how counter-evidence reduces a dimension. In exchange, a failed human trial
can visibly outweigh a pile of encouraging rodent studies.

---

## D004 — Every biological and interventional edge is compiled from a claim

*2026-09-17 · accepted*

**Decision.** Layers 2 and 3 of the graph contain no edge that is not derived from a
claim with provenance, except identifier/ontology facts labelled `reference_data` or
`ontology_axiom`. Binding relations cannot support effect edges (rule V16).

**Alternatives.** Curating a mechanism graph directly and attaching citations later —
rejected, because "later" never arrives and unsourced edges are indistinguishable from
sourced ones once drawn.

**Consequences.** The graph is sparser and less impressive-looking than a
literature-mined graph, and every edge can be interrogated back to a verified source.

---

## D005 — Blackboard with disjoint path ownership, not a chat swarm

*2026-09-17 · accepted*

**Decision.** Seven subagents write disjoint artefact sets; no agent-to-agent messaging;
the orchestrator enforces gates and performs all commits. Handoffs are files.

**Rationale.** Agent-to-agent discussion produces citation cascades: agent B cites
agent A's summary, which was itself an inference, and the provenance chain silently
becomes circular. Files with provenance cannot cascade invisibly.

**Consequences.** Coordination is slower and duplication is possible (two agents may
both cite the same paper — deduplicated at source level in the store and the ranking
model). Ownership enforcement is post-hoc, via `scripts/check_ownership.py`.

---

## D006 — File-first storage (YAML → Parquet → DuckDB → NetworkX), Neo4j deferred

*2026-09-17 · accepted*

**Decision.** Curated records are YAML in Git; derived tables are Parquet/DuckDB and are
gitignored and rebuildable; the graph is compiled in memory with NetworkX; Neo4j is an
export target only.

**Rationale.** Sprint 1's bottleneck is epistemic hygiene, not query performance. YAML
diffs are reviewable; a graph database's contents are not.

**Consequences.** No interactive Cypher until the exporter is used; some queries are
awkward. Revisit when the graph exceeds what NetworkX handles comfortably.

---

## D007 — The red team runs after the atlases and can only downgrade

*2026-09-17 · accepted*

**Decision.** The auditor searches independently for contradiction, cannot raise any
level, cannot delete provenance (append-only claim registry lock), and must complete a
fixed check catalogue per target.

**Rationale.** An auditor that can both promote and demote becomes a second opinion
rather than a falsifier. Asymmetry is the point.

**Consequences.** Anything wrongly downgraded needs new *evidence* to recover, not an
argument. That is the intended cost.

---

## D008 — Virtual pharmacology is gated in code, not by convention

*2026-09-17 · accepted*

**Decision.** `blueprint.pharmacology.gates.eligible_for_chemistry()` refuses targets
that have not survived causal integration and red-team review; the interface modules
raise `NotImplementedError` naming the gate.

**Rationale.** The predictable failure mode of a project like this is jumping to
molecule design against a favourite target. A convention would not survive enthusiasm;
a function call that returns `False` does.

---

## D009 — Seed targets are work assignments, not a shortlist

*2026-09-17 · accepted*

**Decision.** `targets/seed_registry.yaml` records `seed_origin: user_seed_list` for
every brief-supplied target, assigns explicit `dossier_depth`, and expects downgrades.
The ranking report must carry `dossier_depth` and `coverage` so that a shallow entry
cannot be mistaken for a well-supported one.

**Consequences.** The first ranking is substantially a measure of *how much evidence was
gathered per target*, and must be read that way. Breaking that anchoring requires
agent-proposed additions and systematic coverage in later sprints.

---

## D010 — Methodological-weakness caps are polarity-aware

*2026-09-17 · accepted (corrects a defect found in use)*

**Context.** The comparative atlas applies a rule that a claim with no phylogenetic
control may not be graded above level 2. Applied uniformly, it capped
`human_lineage_divergence_risk` — an **inverse-polarity** facet where a higher level
means *more* risk that human biology diverges enough to invalidate non-human causal
evidence. The cap therefore made a target with documented human/mouse physiological
divergence look *more* translatable. `agent:comparative` applied the rule as written
and escalated rather than deciding unilaterally, which is how the defect surfaced.

**Decision.** A cap imposed for methodological weakness applies only in the direction
that favours the target: `level` for normal-polarity facets, `counter_level` for
inverse-polarity facets. Weak method cannot establish strong support, and equally it
cannot establish the absence of a risk. Every facet declares `polarity` in
`models/ranking/facet_rubric_v0_1.yaml`, caps go through one polarity-aware helper, and
a named test fails the old behaviour.

**Consequences.** Inverse facets can carry a high risk level on weakly controlled
evidence — deliberately, because the alternative is systematic optimism. The
uncertainty model must not treat a capped `counter_level` as evidence of safety.

---

## D011 — The precautionary asymmetry is declared and measured, not hidden

*2026-09-17 · accepted*

**Context.** D010 makes caps bite only in the direction that favours a target. The
consequence, raised by `agent:comparative` when it asked whether a normal-polarity
facet's `counter_level` is also capped (it is not), is that methodologically weak
evidence can raise doubt about a target while being unable to establish support for it.

**Decision.** Keep the asymmetry — the dominant risk in this problem domain is
over-optimism about cognitive enhancement — but declare it wherever ranks are reported
and **measure** it: `models/ranking/ranking_spec_v0_1.yaml` carries a `symmetric_caps`
sensitivity variant, the report exposes `rank_delta_symmetric_caps` per target, and
targets whose rank is sensitive to the capping rule are named in the report narrative.

**Consequences.** A genuinely promising target with weak evidence in both directions
will be under-ranked, and we will be able to say by how much. An undeclared asymmetry
would have been indistinguishable from a bug.

---

## D012 — Duplicate source registration is allowed; divergence is a hard error

*2026-09-17 · accepted (reverses an earlier validator behaviour)*

**Context.** The validator initially treated the same PMID registered by two agents as a
violation. In practice that pushed an agent into deleting its own registrations and
pointing its claims at another agent's file — a cross-lane dependency it could not
edit, which would break silently if the other agent withdrew the source.

**Decision.** Each agent registers every source it cites, in its own file. Duplication
is informational (and useful input to the red team's citation-dependence check).
Deduplication happens downstream in the store, the graph compiler and
`independent_source_count`. Divergence between two registrations of the same
`source_id` on verified registry fields is a hard error, since it means one was written
from a different record.

**Consequences.** Slightly more redundant YAML, in exchange for self-contained agent
lanes and no silent cross-lane breakage.
