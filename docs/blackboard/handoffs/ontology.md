# Handoff — `agent:ontology`, Sprint 1 Phase 1

**THE CONTRACT IS FROZEN.** `docs/DATA_CONTRACT.md` v0.1.0 is authoritative for the rest
of Sprint 1, as ruled by the orchestrator. Nothing further changes except a demonstrable
correctness bug of the kind R5, R9, R11 and R13 were — where the schema forces an agent
to record something *untrue*. Ordinary awkwardness is no longer sufficient grounds:
five agents have each adapted their records two or three times, and further churn costs
more than it returns. Where this note and the contract disagree, **the contract wins**
and the disagreement is a bug to report, not a licence to improvise.

Phase 1 delivered the type system, schemas, validators and tests, and is complete and
verified. **Phase 2 (graph compiler, DuckDB/Parquet store, exporters, HTML report) has
NOT been started.** The Phase-1 contract-amendment stream ran to eleven further rulings
after the original brief — R1 through R14 plus the `nct_id`, `preclinical_harm`, V22,
`tool_mediated`, V3c and title-normalisation fixes — and each one needed schema, model,
rule, fixture and test changes. That work is done; Phase 2 is the next session's.

---

## 1. Commands run, and their real output

```
$ .venv/bin/python graph/validate_graph.py --strict
repository: /Users/moheet/humanintelligence
records:    182 sources, 289 claims, 392 evidence items, 27 targets, 102 assessments, 0 audits
ontology:   101 state variables, 125 definitional edges, 35 intervention entities, 43 annotations
registry:   27 seed targets, 0 locked claim ids, 9 sources registered by more than one agent
sources verified: release_verified_by_snapshot=4, verified=169
rules run:  31
TOTAL: 41 violation(s) across 4 rule(s) — 0 error, 39 warning
FAIL                                                         # exit 1, from --strict
```

**Zero errors.** The run exits 1 only because `--strict` escalates the 39 warnings, all
of which are "the red team has not finished yet". Without `--strict` the repository
passes. That is the honest reading of the gate at this point in the sprint.

```
$ .venv/bin/python -m pytest -m "not network"
739 passed in 36s
```
(All 739 repository-wide; **357** of them are in the six files I own, the remainder are
`agent:integration`'s ranking and uncertainty suites.)

Record counts move between runs because five agents write concurrently — intermediate
totals in one round ranged from 487 to 1227 purely from in-flight records. Only the
final run counts.

```
$ .venv/bin/python -m blueprint.sync_schema_enums --check
schemas and ontology/vocabularies.yaml agree

$ .venv/bin/python scripts/check_ownership.py --agent ontology --paths <my 149 paths>
all 149 path(s) owned as expected
```

**The `--strict` run exits 1, and every remaining item is expected.** Nothing is a
schema defect. See §2.

**Honest note on the empty-repository requirement:** the validator exits 0 on an empty
tree, which was the original definition of done, but the repository is no longer empty.
`tests/fixtures/empty` and `tests/fixtures/valid_minimal` both pass under `--strict` and
are asserted by `test_validator_cli.py`, so that property is pinned by test rather than
by the live tree.

---

## 2. Triage of the remaining 41 violations — 0 errors

| # | Rule | Severity | Owner | Where | Why, in one line |
|---|------|----------|-------|-------|------------------|
| 27 | V15 | warning | `agent:red_team` | `targets/seed_registry.yaml` | Every seed target still lacks an audit record. Expected: the red team runs after the atlases. |
| 9 | V6 | warning | `agent:red_team` | `evidence/sources/red_team.yaml` | Red-team sources awaiting the end-of-run verification pass. `make fetch-sources` clears them. |
| 3 | V14 | warning | `agent:red_team` | `evidence/claims/power/{KL,astrocyte_neuron_lactate_shuttle,creatine_supplementation_human}.yaml` | Self-declared `contested` claims waiting for the audit record that makes the contestation reviewable. |
| 2 | V22 | info | `agent:power` | `evidence/sources/power.yaml` | Deliberate registry-only registrations. Never an error. |

**SCHEMA-SIDE: ZERO. RECORD-SIDE: ZERO.** Every V1 and V3c violation is gone — the last
one, `claim_type: evidence_gap` on `CHANGES_STATE` in the power atlas, was moved to
`ABOUT` by its owner. Every remaining finding is an expected mid-run warning waiting on
the red team. The split over this phase was:

* **Schema-side, fixed by me (≈330 violations cleared without any agent touching a
  record):** intervention `mechanisms` as an array of objects; `notes` as
  string-or-array; canonical database-fact numeric slots; V6 grouping with
  worst-status-wins; duplicate registration informational; `search_basis` in place of an
  impossible citation at level 0 (R11); the `attributes` holding area (R12); annotation
  claim refs accepted per-assertion; couplings accepted as bare ids; a double-escaped
  regex in the coupling pattern; the coupling `basis` bound to the wrong vocabulary; a
  `desirability_note` no longer counted as an assertion; `identifiers.nct_id`/`pmcid`/
  `url` accepted.
* **Record-side, fixed by the owning agents during the phase:** `search_basis` and
  `counter_claim_refs` additions, one illegal `POTENTIATES → Protein` triple, two V16
  efficacy edges backed only by association claims, three `locus_to_gene_resolved` YAML
  booleans, three unapproved ChEMBL numerics, wrong-enum values.

---

## 3. File inventory

### `ontology/` — the type system (data, not code)
| File | Purpose |
|---|---|
| `nodes.yaml` | 42 node types across 3 layers, with prefixes, `id_pattern`, parents and attributes. |
| `edges.yaml` | 42 relations with domain/range, `requires_claim`, `allowed_claim_types`, `allowed_provenance_classes`, `asserts_effect`, `effect_asserting_ranges`, `negatable`, `requires_multiple_species`, and a `semantics` note on every relation that is easy to misuse. |
| `vocabularies.yaml` | 69 controlled vocabularies. **The single source of truth for every schema enum.** |
| `computational_primitives.yaml` | 27 working definitions (24 brief-supplied + 3 agent-proposed), each with an `animal_analogue_caveat`. |
| `state_variables.yaml` | The state-variable TYPE system: 8 domains and every enum with its semantics. |
| `definitional_edges.yaml` | 125 claim-free axioms: 101 domain memberships, 16 definitional primitive links, 8 gross-anatomy containments. |

### `state_model/` — the instances
101 state variables across the 8 domains, plus `dynamics.yaml` (the formal structure of
`X(t+1) = F(...)`, explicitly unfitted and unsimulated, with three conceptual hypotheses
each carrying its known problems).

### `schemas/` — 12 JSON Schemas (draft 2020-12, `$id` ending `/v0_1_0/<name>`)
`claim`, `evidence`, `source`, `target`, `assessment`, `audit`, `intervention`,
`state_variable`, `state_variable_annotation`, `node`, `edge`, `verification`.

### `src/blueprint/` — the library
`paths` · `violations` · `vocab` · `ids` · `ontology` · `sync_schema_enums` · `schemas` ·
`records` · `loaders` · `verification` · `policy` · `validate`. Layout and design rules:
`docs/ONTOLOGY_NOTES.md` §1.

### `graph/validate_graph.py` — the CLI
`--strict` `--quiet` `--json` `--root PATH` `--rule ID...` `--update-lock`
`--list-rules` `--max-examples N`.

### `tests/` — 351 tests in six files plus 25 fixture trees
`test_ontology.py` (33) · `test_ids.py` (73) · `test_schemas.py` (91) ·
`test_validate_rules.py` (82) · `test_state_model.py` (43) · `test_validator_cli.py` (29).
Fixtures are tiny: a fixture tree holds only the records under test and shares the
ontology, schemas and state model from the real repository, so a fixture cannot drift
from the type system it is testing against.

---

## 4. ID crib sheet — copy this

```
GENE:GABRA5                      HGNC-approved symbol, UPPER CASE
VAR:rs141426703                  dbSNP rsID, or chr{c}_{pos}_{ref}_{alt} (GRCh38)
TX:ENST00000370447               Ensembl transcript, exactly 11 digits
PROT:P31644                      UniProt accession preferred, else the gene symbol
COMPLEX:eif2b                    snake_case slug
PROC:GO:0006413                  GO id preferred, else snake_case slug
PATHWAY:REACT:R-HSA-72613        Reactome id preferred, else slug
CELL:CL:0000679                  Cell Ontology id preferred, else slug
REGION:UBERON:0001954            UBERON id preferred, else slug
CIRCUIT:ca3_ca1_schaffer         snake_case slug
NET:frontoparietal_control       snake_case slug
SV:plasticity.ltp_threshold      SV:{domain}.{name}; domain is one of the 8
SVDOM:power                      one of the 8 state domains
PRIM:pattern_separation          snake_case, from computational_primitives.yaml
PHENO:general_cognitive_ability  snake_case slug
SPECIES:NCBITaxon:9606           taxid from a TOOL RESPONSE, never from memory
TGT:GABRA5                       gene symbol or complex slug, UPPER CASE
CPD:CHEMBL1234567  DRUG:caffeine  BIO:klotho_protein  RNAI:shrna_hdac2
GREG:aav_crtc1_overexpression  METAB:creatine_loading  NTECH:tdcs_dlpfc
MECH:alpha5_gabaa_nam   EFFECT:increased_wm_capacity   AE:seizure
SRC:PMID:29942086                PMID preferred over DOI for any paper that has one
SRC:DOI:10.1038/s41588-...       DOI, LOWERCASED
SRC:NCT:NCT02024789              NCT + exactly 8 digits
SRC:GCST:GCST006269   SRC:DB:gwas_catalog:2026-09-13   SRC:DATASET:gtex_v8_brain
CLM:{domain}:{topic}:001         counter ZERO-PADDED to three digits
EVD:{claim_local}#1              DERIVED from the claim id — never hand-written
AUD:red_team:GABRA5:001
```

**Five traps that have each bitten a real record:**

1. `locus_to_gene_resolved: no` → **write `"no"` with quotes.** Unquoted `yes`/`no` are
   booleans in YAML 1.1 and the value never reaches the enum.
2. A claim counter is **three digits**: `:001`, not `:1`.
3. An evidence id is **derived**: `EVD:{claim_local}#{n}`, positionally. Do not invent one.
4. A source registered under `SRC:NCT:NCT02024789` **must** carry
   `identifiers.nct_id: "NCT02024789"`. The identifier that defines the source goes in
   `identifiers`, not only in the id.
5. `SPECIES:`, HGNC, Ensembl, UniProt, ChEMBL and taxid values are **fetched, never
   typed** (contract §7).
6. **An MCP tool payload must be snapshotted, not remembered.** Run
   `scripts/record_tool_snapshot.py` so the payload lands in `data/raw/` with a manifest
   line, register the release as `SRC:DB:<registry>:<release>` with
   `retrieval.method: mcp_tool`, and compiled edges from it carry
   `provenance_class: tool_mediated`. That class is deliberately distinct from
   `reference_data`: a payload a tool handed you is weaker than a record you opened
   yourself, and the red team should be able to see which. Without the snapshot the
   number is unprovenanced and V9 rejects it.
7. **An `evidence_gap` lives on `ABOUT` and nowhere else**, with the claim as its own
   subject: `CLM:{...} ABOUT PHENO:{the endpoint nobody measured}`. Attaching it to a
   causal relation asserts exactly what the record refuses to assert.

### Canonical field names for database-derived facts

| Use this | Not this | Note |
|---|---|---|
| `max_clinical_phase: {value, as_reported, source}` | `chembl_max_phase` | Accepted as a deprecated alias in v0.1.0. |
| `first_approval_year` | `chembl_first_approval` | Integer year. Accepted alias. |
| `database_source_id: SRC:DB:chembl:34` | — | **Required** for V9 to exempt the two numbers above. A database number is admissible because its provenance is VISIBLE, not because it is a number. |
| `chembl_fields_as_returned: {...}` | — | Verbatim payload. Numbers inside are exempt only when the record names a database source. |
| `attributes: {key: "string"}` | extra keys on `identifiers` | Holding area for domain metadata the schema does not model (an AAV serotype, an assay format). **String values only.** Anything decision-relevant must graduate to a real field via a schema-change request. |
| `id` / `label` | `intervention_id` / `preferred_name` / `name` | All accepted in v0.1.0; v0.2.0 settles on `id`/`label`. |

---

## 5. The three most likely ways you will get a record wrong

**1. Writing an effect where you have engagement.** `TARGETS`, `AGONISES`,
`ANTAGONISES`, `INHIBITS`, `POTENTIATES` and `NEGATIVELY_MODULATES` assert *engagement*.
None may reach a `StateVariable`, `ComputationalPrimitive`, `CognitivePhenotype` or
`DesiredEffect`, and a `pharmacology_binding` claim can never license `CHANGES_STATE`.
The route round the gate is also closed: `NEGATIVELY_REGULATES` reaching a
`CognitivePhenotype` is treated exactly like `CHANGES_STATE` and needs
`causal_perturbation`, `pharmacodynamic` or `clinical_efficacy` evidence. If your
evidence is binding, your edge is `TARGETS` and your story stops there.

**2. Recording an absence of evidence as a finding — in either direction.** Three
distinct records, three distinct claim types:
* somebody measured it and found nothing → `NO_DETECTED_EFFECT_ON`, with
  `negated_relation` naming what was tested, and ≥1 evidence item with
  `endpoint_measured: measured` **and** `evidence_role: null_result`/`contradicts`;
* the study never measured it → `claim_type: evidence_gap`, which is **graph-inert** and
  may never count as counter-evidence;
* nobody has tested it → **no record at all**. The absence of an edge is the
  representation. A null edge for an untested relationship manufactures a finding out of
  a gap.
And the mirror image: a facet graded `0` means *searched and found nothing*, so it needs
a `search_basis` and **no** `claim_refs`; a facet nobody examined is
`assessment_status: not_assessed` with `level: null`; and a zero explained by a
*completed trial that posted no results* carries `reporting_gap_refs` too — that is how
publication bias becomes visible in the data rather than staying an observation in a
handoff note. Those are four different facts and the contract works hard to keep them
apart.

**3. Letting animal or developmental evidence wear a human, adult label.** `clinical_harm`
requires human evidence — mouse harm is `preclinical_harm` (V23), and over-stating a harm
is *not* the safe error, because it misprices every safety constraint resting on it. A
human-proposition facet graded 3 or 4 needs a cited claim whose
`translation.human_relevance` is `direct_human_interventional`, `human_genetic` or
`human_observational` (V21). Developmental expression is not adult expression. And check
the primitive's `animal_analogue_caveat` before filing a rodent result against it: for
`far_transfer`, `composition` and `variable_binding` the analogue is effectively absent,
and a claim there is about a different operation.

---

## 6. Open questions

1. **Three field spellings survive** (`id`/`intervention_id`, `label`/`preferred_name`/
   `name`, `nct`/`nct_id`, `pmc`/`pmcid`, `state_variable`/`state_variable_id`). All
   accepted in v0.1.0 to avoid invalidating ~60 records. **v0.2.0 must pick one each.**
   This is the weakest part of the contract, and it is weak because §2 named the record
   paths without specifying their fields.
2. **`database_gradable` is not yet set in `models/ranking/facet_rubric_v0_1.yaml`.** My
   V11 check reads the flag from the rubric rather than hard-coding `tractability`, so
   until `agent:integration` sets it, `source_refs`-only grading is licensed for no
   facet. That is the correct fail-closed behaviour, but it blocks R7's intended use.
3. **V9's non-probability narrowing (deviation D7)** makes an unapproved *integer* a
   warning rather than an error. A fabricated integer score in an unvalidated field
   would be a warning. Worth a second opinion.
4. **`safety_coupling` is empty on all 101 state variables** by design. Couplings arrive
   only through claim-backed annotations. A reviewer may think this is too pure.
5. **`arousal_level`'s polarity is nominal** — it is non-monotone, so neither `risk` nor
   `margin` is honest. R4 required a binary; the `polarity_note` says so explicitly.
6. **The V20 text heuristic has known holes** in both directions
   (`docs/ONTOLOGY_NOTES.md` §5). It is pinned by 12 cases drawn from real records.
7. **Brain-region axioms use slugs, not UBERON accessions**, because §7 forbids
   hand-writing accessions. Phase 2 should resolve them through a fetch script.
8. **`evidence/claims/claim_registry.lock` does not exist yet.** It is outside my lane.
   Run `.venv/bin/python graph/validate_graph.py --update-lock` once to create it with
   its append-only header; after that V13 protects every claim id in it. Until it exists,
   V13 protects nothing.
