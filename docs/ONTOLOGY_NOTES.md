# Ontology design notes — Phase 1

Written by `agent:ontology`. This is the design record for the type system, the
schemas, the validators and their tests: what was built, where it deviates from
`docs/DATA_CONTRACT.md` and why, which contract rules are fully versus partially
implemented, and every judgement call a reviewer should challenge.

**THE CONTRACT IS FROZEN** as of the orchestrator's ruling at the end of this phase.
Nothing further changes except a demonstrable correctness bug of the kind R5, R9, R11
and R13 were — where the schema forces an agent to record something untrue. Ordinary
awkwardness is no longer sufficient grounds. Where this document and
`docs/DATA_CONTRACT.md` disagree, the contract wins and the disagreement is a bug to be
reported.

---

## 1. Module layout

```
src/blueprint/
  __init__.py              version 0.1.0; the design rules the package obeys
  paths.py                 repo-root discovery + canonical paths; every function takes
                           an optional `root`, so tests point the library at a fixture
                           tree with no monkeypatching
  violations.py            the single Violation type (rule, severity, path, message)
  vocab.py                 controlled-vocabulary access; validates subsets at load
  ids.py                   id parse/validate, prefix<->type compatibility, constructors
  ontology.py              load + index ontology/*.yaml; is_legal_triple; explain_triple
  sync_schema_enums.py     --check / --write: proves schema enums match the vocabularies
  schemas.py               load JSON Schemas, validate a record, structured violations
  records.py               pydantic v2 models enforcing what JSON Schema cannot
  loaders.py               load every record into typed collections; empty-tolerant
  verification.py          read the source-verification index; status_for(source_id)
  policy.py                computational-only checks (V20) + the action_type enum
  validate.py              the rule engine: rules as small functions in a registry
graph/
  validate_graph.py        the CLI (--strict, --json, --quiet, --root, --rule,
                           --update-lock, --list-rules)
```

Phase 2 modules (`blueprint/graph/`, `blueprint/store/`, `graph/build_graph.py`,
`graph/query_graph.py`, `graph/export_graph.py`, `blueprint/reports/`) slot in beside
these and consume `loaders`, `ontology` and `records` without changing them.

### Design rules the package obeys

* **Every path is injectable.** No module reads a hard-coded absolute path.
* **An empty repository is valid.** Every loader returns an empty collection rather than
  raising, and the validator exits 0 on a tree with no records. A build that failed on
  emptiness would pressure agents into writing records to make it pass.
* **The ontology is data.** `blueprint.ontology` hard-codes no node type, relation or
  prefix. Adding a node type is a YAML edit.
* **Rules are a registry of small functions.** Adding a rule is one decorated function.
* **Rules never raise.** A rule that fails reports a violation against itself; one
  broken rule must not take down the report an agent needs.
* **Determinism.** Loaders sort inputs; writers use sorted keys and LF endings.

---

## 2. Single source of truth, and the drift test

`ontology/vocabularies.yaml` holds every enumerated value in the contract (69
vocabularies). The JSON Schemas carry the same lists inline, so a schema file is
self-contained and usable by any JSON Schema tool.

Two representations of one fact drift, so the binding is **declared in the schema**: an
`enum` carries a sibling `$comment` of the form `vocabulary: <name>` (optionally
`vocabulary: <name> (<subset_key>)`). `blueprint.sync_schema_enums --check` walks every
schema, compares each declared enum to its vocabulary, and **also** reports any
vocabulary that no schema binds and that is not listed as deliberately unbound. It runs
both as rule ONT1 in the validator and as a test. There is no second list to maintain:
adding an enum with the right comment enrols it automatically.

Three-way drift is covered too: the state-variable enums are declared with their
semantics in `ontology/state_variables.yaml` and again in `vocabularies.yaml`, and
`tests/test_ontology.py::test_state_variable_type_system_agrees_with_vocabularies`
asserts they agree. `action_type` is compared against `docs/TASK_DAG.yaml`, which is
authoritative.

---

## 3. Contract rule implementation status

| Rule | Status | Notes |
|------|--------|-------|
| V1 | **full** | JSON Schema + pydantic. Both report as V1; which one catches a given problem is an implementation detail. |
| V2 | **full** | Prefix + `id_pattern` per node type, wherever a record names a node. |
| V3 | **full** | `is_legal_triple` with subtype resolution. Messages name the triple, the failing side and the legal alternatives. |
| V3b | **full** | *(added, R6)* A between-species relation needs ≥2 species; warns when `phylogenetic_control` is absent. |
| V4 | **full** | Claim→source, assessment→claim, audit→claim/target, dossier→claim/SV/primitive, annotation→SV/claim, primitive↔SV. Includes a "closest declared id" hint. |
| V5 | **full** | |
| V6 | **full** | Grouped by `source_id`, **worst status wins**, registry-field divergence is a hard error, `release_verified_by_snapshot` accepted for `SRC:DB:*`/`SRC:DATASET:*` only. |
| V7 | **full** | `phenotype_class` required when the object is a CognitivePhenotype or a cognitive StateVariable (`cognition`/`workspace`/`consolidation` domains). |
| V8 | **full** | |
| V9 | **full, one narrowing** | See deviation D7: a non-probability number in an unapproved slot is a **warning**, not an error. A float in (0,1) is always an error. |
| V10 | **full** | Plus a pydantic guard rejecting a float or `bool` level before coercion can hide it. |
| V11 | **full** | Ownership from the facet catalogue, `lead_atlas` resolved through the dossier. Also enforces R7's rubric-driven `source_refs` rule. |
| V12 | **full** | Downgrade-only, polarity-aware for `counter_level` (see D2). |
| V13 | **full** | |
| V14 | **partial** | The `withdrawn` + superseding-audit requirement is enforced. `contested`/`downgraded` without an audit is a **warning**, because the red team runs after the atlases and the audits do not exist yet. Re-run after the red team to see these clear. |
| V15 | **partial** | Full mandatory check catalogue is enforced per audit. "Seed target has no audit" is a **warning** until the red team has run; `--strict` escalates it. Gate G4 is the real check. |
| V16 | **full** | Gates `CHANGES_STATE`, any edge into `DesiredEffect`, and — via `effect_asserting_ranges` — a regulation relation reaching a CognitivePhenotype or ComputationalPrimitive. That last part closes the route round the gate. |
| V16b | **full** | *(added)* A null edge needs `null_result`/`contradicts` evidence. |
| V16b-sym | **full** | *(added, R9)* The null relation's domain/range is a superset of the union of every `negatable` relation's, **derived** from the flag rather than listed. Claims must name `negated_relation`, and the triple must be legal under it. |
| V16c | **full** | *(added, R5)* A measured absence is not an absence of measurement. |
| V17 | **partial** | Every edge-shaped record that exists today — the 125 definitional axioms — is checked, along with each relation's `allowed_provenance_classes`. **Compiled-graph edges arrive in Phase 2**; the rule is written to cover them without change. |
| V18 | **full** | Word-bounded credential patterns over curated record text. Scoped to records, not the whole tree: `.gitignore` and the pre-commit hook cover untracked files. |
| V19 | **full** | sha256 of every `MANIFEST.jsonl` entry, plus missing-file detection. |
| V20 | **full, heuristic** | The closed `action_type` enum is exact. The text scan is a heuristic with known limits — see §5. |
| V21 | **full** | *(§5.3)* Human-proposition facets need human evidence at level ≥3, threshold read from the vocabulary. |
| V22 | **full** | *(added)* Registered-but-uncited sources. **Informational**, never escalated. |
| V23 | **full** | *(added, R13)* `clinical_harm` requires human evidence; non-human harm is `preclinical_harm`. |
| V3c | **full** | *(added)* A claim's `claim_type` must be in its relation's `allowed_claim_types` — for **every** relation, not only the effect-asserting ones. This was the gap that let the validator accept `preclinical_harm` on `INCREASES_RISK` while `ontology/edges.yaml` rejected it, and pushed an atlas into building a local check that mirrored the validator. A record could then pass one tool and fail another depending on which agent ran which. `tests/test_ontology.py` now asserts the two agree for every relation, and that every claim type is admitted by at least one relation — a claim type no relation accepts is unusable by construction, and that class of gap appeared twice. |
| ONT1 | **full** | Schema/vocabulary drift. |
| ONT2 | **full** | State-variable type conformance, no invented dynamics, polarity convention. |

**Not implemented:** nothing in the contract's V1–V23 list is unimplemented. V14, V15
and V17 are *partial* for the reasons above, all of which are "the input does not exist
yet" rather than "the check was skipped".

---

## 4. Deviations from the contract

Each of these is a place where I did something the contract does not literally say.

**D1 — `layer` is singular, with `shared_with_layers`.** The contract's prose says
"Species (shared)". Rather than duplicate the type or make `layer` a list, a node
declares its home layer plus the layers it is shared with. `Species` is
evidence+biological; `StateVariable` and `StateDomain` are biological+intervention.

**D2 — audit adjustments carry `field: level | counter_level`.** Filed as
`ontology-004`. After §5.2 gained `counter_level`, the red team's way to record
contradicting evidence is to *raise* it — a downgrade of standing but an increase in the
number, which the single-field V12 rule made unrecordable. Default is `level`, which
reproduces the original behaviour exactly.

**D3 — a `StateDomain` node type and an `SVDOM` prefix.** Filed as `ontology-002`.
Prefixes are closed by §1, so this is a deliberate ontology change: without it,
state-variable domain membership could not be written as a triple at all.

**D4 — the local-id charset is wider than §1 declares.** Filed as `ontology-001`. §1
says `[A-Za-z0-9._:+-]+`, but the contract's own EVD form needs `#` and its own DOI
example needs `/`. The coarse gate admits them; the narrow `id_pattern` is the real
check. Found by a test asserting that every contract example parses.

**D5 — no inverse relation is materialised.** The README mentions `CONTRADICTED_BY`.
v0.1.0 declares `inverse: null` everywhere and traverses in reverse instead, so there is
one relation to curate against rather than two that can disagree. A test asserts every
non-null `inverse` names a declared relation.

**D6 — the primitive set is 27, not 24.** Filed as `ontology-008`, approved as R2. The
brief's 24 carry `origin: project_brief_sprint1`; three carry
`origin: agent_proposed_sprint1`. Four other agent-referenced names were duplicates of
existing primitives and remain V4 errors with a "closest declared id" hint.

**D7 — V9's non-probability case is a warning.** The contract says "any numeric field
not accompanied by `derived_from` … is a failure". Taken literally that fails honest
integer counts (`coverage_summary.power_domain_variables_total`,
`max_clinical_phase: 4`), while the danger P3 names is the fabricated PROBABILITY. So a
float in (0,1) outside an approved slot is an **error**, and any other unapproved number
is a **warning** that `--strict` escalates. This is a narrowing of a contract rule and a
reviewer should check it: the risk is that a fabricated integer score (say `level: 3` in
a field nobody validates) reads as a warning rather than an error.

**D8 — several records accept two field spellings.** Three atlases independently chose
`id`/`intervention_id`, `label`/`preferred_name`/`name`, `nct`/`nct_id`, `pmc`/`pmcid`
and `state_variable`/`state_variable_id`. All are accepted in v0.1.0 with one marked
canonical, because invalidating ~60 existing records to win a naming argument costs more
than it returns. **v0.2.0 must settle on one spelling each** — this is the weakest part
of the contract and it is weak because §2 named the record paths without specifying
their fields.

**D9 — four objects are deliberately open.** `additionalProperties: false` everywhere
except: `verification` (machine-generated by another agent's script from registry
payloads that differ per registry), `evidence[].database_record` and
`intervention.chembl_fields_as_returned` (verbatim third-party payloads whose keys are
not this project's to enumerate), and `uncertainty.model_outputs[]` items (a model's own
output fields). Numbers inside the first three are admissible to V9 only when the record
names the pinned release they came from. `attributes` (R12) is closed to *string* values
for the same reason: a number in an unvalidated bag would escape V9.

**D10 — brain-region axioms use slugs, not UBERON accessions.** Contract §7 forbids
hand-writing accessions, and I had seen exactly one UBERON id (in the contract itself).
The eight region axioms therefore use snake_case slugs and are limited to gross
containment every standard atlas agrees on. Phase 2 resolves the slugs through a fetch
script, and that resolution is reference data.

---

## 5. Judgement calls a reviewer should challenge

**The V20 text heuristic.** The hard part is that a faithful evidence record *describes*
somebody else's animal or dosing study: "mice received a single injection before
training" is what a correct record looks like. Flagging that would push agents into
laundering their statements, which is worse than the risk. So a pattern fires only when
a proposal cue (`we will`, `next step is`, an imperative) co-occurs within ~160
characters with a prohibited-action cue, and not when a computational verb (`analyse`,
`review`, `in silico`) appears in the same window. A second family catches
reader-directed instructions, and those are suppressed for fields that hold verbatim
source text (`effect_size.as_reported`, `population`, `endpoint`, `database_record`).
**Known limits:** a proposal phrased without any of the cue forms passes; a quotation
that happens to contain "we will administer" is flagged. `tests/test_validate_rules.py`
pins 6 true positives and 6 true negatives drawn from real records. When the heuristic
is wrong the fix is to sharpen the pattern, not to lower the severity.

**Three times I demanded a citation for the absence of evidence.** This was my most
persistent mistake and it is worth recording as a pattern rather than three bugs. I
required `claim_refs` on a level-0 facet (which means *searched and found nothing*, so
there is nothing to cite); I treated a `response_shape` block with `shape: unknown` as
an assertion; and I treated a `desirability_note` saying "no claim links sparseness to
performance" as an assertion. Each rejected an *honest* record and would have pushed an
agent into inventing a tangential citation or downgrading a truthful 0 to
`not_assessed` — a different epistemic state the whole contract works to keep distinct.
The general lesson: **before requiring evidence for a field, ask whether the field can
express "nothing to report", and if so whether the honest value trips the rule.**

**`safety_coupling` is empty on all 101 state variables.** Which variables push which
safety constraints is empirical. Several couplings look obvious (ROS production →
oxidative stress burden), and pre-filling them would be exactly the plausible-sounding
invention P2 and P3 forbid. The field is a slot that domain agents fill through
claim-backed annotations. A reviewer may reasonably think this is too pure; the
alternative is an ontology that ships with unattributed biology in it.

**Response shape is `unknown` on all 101 variables, with basis
`default_no_evidence_yet`.** Stronger than the contract requires: `agent:ontology` holds
no evidence, so it sets no shape at all, and
`test_agent_ontology_declares_no_shape_at_all` pins that. Shapes arrive as annotations.

**`arousal_level` has a nominal polarity.** R4 requires every safety and stability
variable to declare `polarity: risk | margin`. Arousal is non-monotone — too little and
too much are both bad — so neither value describes it honestly. It is recorded as
`margin` with a `polarity_note` saying the assignment is nominal, so annotations have a
declared reference direction while the response shape stays `unknown`. A binary field
was the ruling; this is the least dishonest way to satisfy it. An earlier version let a
suffix-matching fallback *guess* the polarity, which silently assigned `margin` to
`intrinsic_excitability` (where higher means *less* margin to seizure) — precisely the
silent default R4 exists to prevent. Unlisted names now fail the generator.

**`dendritic_coincidence_detection` is mechanism-laden.** The primitives file states
that a primitive says what must be computed, never what implements it. That name names
a structure. It is kept because the brake atlas needs to state coincidence-window
claims, and it should be challenged.

**V7's "cognitive state variable" test is a domain-name heuristic.** A state variable is
treated as cognitive when its domain is `cognition`, `workspace` or `consolidation`.
A cognitive variable in another domain would escape the `phenotype_class` requirement.

**A test harness bug worth knowing about.** `tests/conftest.py` symlinks the shared
`ontology/`, `schemas/`, `state_model/` and `docs/` into each fixture root. An earlier
version symlinked unconditionally, and a fixture that overrode `state_model/cognition.yaml`
wrote **through** the link and overwrote the real repository's file. It now copies a
shared directory the fixture touches, and checks every write lands inside the test root.
If you add a fixture that overrides a shared file, that is the mechanism protecting you.

---

## 6. What Phase 2 needs from me, and what it must not undo

* `blueprint.loaders.load_repository(root)` returns every record in both raw and typed
  form, plus `shared_sources` (sources registered by more than one agent) — the compiler
  must collapse those to one node and keep the registering agents as an attribute.
* `blueprint.ontology.load(root)` answers legality, subtyping, `allowed_provenance_classes`,
  `asserts_effect(predicate, object_type)`, `null_result_predicates()`,
  `negatable_union()` and `between_species_predicates()`.
* Three rulings the compiler must honour, all of them about not letting the graph drift
  positive:
  1. `claim_type: evidence_gap` is **graph-inert** — an evidence-layer record and no
     layer-2/3 edge. An absence of measurement is not a finding about biology.
  2. `NO_DETECTED_EFFECT_ON` edges carry `is_null_result: true` and `negated_relation`,
     must be rendered distinguishably, and must be **excluded from every support count
     and every traversal that means "evidence for"**.
  3. A traversal helper must not treat a direction-bearing edge as positive: a
     `CONSTRAINS` edge with `direction: no_change` is not support.
* `ENCODES` and the other reference-data edges come from
  `data/interim/gene_identifiers.jsonl`, never from `definitional_edges.yaml` — the
  ontology restricts `ENCODES` to `provenance_class: reference_data` so the file
  *cannot* contain one.
* Target dossiers' `identifiers: {}` are filled at compile time from that same index.
  Agents never hand-wrote them (contract §7).
