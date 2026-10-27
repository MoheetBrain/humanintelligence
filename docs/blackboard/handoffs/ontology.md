# Handoff — `agent:ontology`, Sprint 1 (Phases 1 and 2)

**THE CONTRACT IS FROZEN.** `docs/DATA_CONTRACT.md` v0.1.0 is authoritative for the rest
of Sprint 1, as ruled by the orchestrator. Nothing further changes except a demonstrable
correctness bug of the kind R5, R9, R11 and R13 were — where the schema forces an agent
to record something *untrue*. Ordinary awkwardness is no longer sufficient grounds:
five agents have each adapted their records two or three times, and further churn costs
more than it returns. Where this note and the contract disagree, **the contract wins**
and the disagreement is a bug to report, not a licence to improvise.

Phase 1 delivered the type system, schemas, validators and tests. Phase 2 delivered the
graph compiler, the Parquet/DuckDB store, the exporters and the interactive HTML report.
Both are complete and verified; §7 below has the Phase-2 numbers.

---

## 1. Commands run, and their real output

```
$ .venv/bin/python graph/validate_graph.py --strict
repository: /path/to/user/humanintelligence
records:    182 sources, 293 claims, 400 evidence items, 27 targets, 129 assessments, 30 audits
ontology:   101 state variables, 125 definitional edges, 36 intervention entities, 43 annotations
registry:   27 seed targets, 289 locked claim ids, 11 sources registered by more than one agent
sources verified: release_verified_by_snapshot=4, verified=178
rules run:  32
TOTAL: 2 finding(s) across 1 rule(s) — 0 error, 0 warning, 2 info
PASS — nothing failing. Info findings are not defects in any state of the repository.
```                                                           # exit 0

**The repository now PASSES under `--strict`.** Zero errors, zero warnings; the single
remaining finding is informational (V22: three sources registered but not yet cited).
The 39 warnings in the previous run were all "the red team has not finished yet", and
the red team has since landed 30 audits and 27 more facet assessments, which cleared
them. Gate G4 is satisfied: every seed target has a full audit.

```
$ .venv/bin/python -m pytest -m "not network"
832 passed in 75s
```
(All 832 repository-wide; **449** of them are in the nine files I own — the six Phase-1
files plus `test_graph_compile.py` (26), `test_store.py` (14) and `test_export.py` (32).
The remainder are `agent:integration`'s ranking and uncertainty suites.)

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

## 2. Triage of the remaining violations — 0 errors, 0 warnings

| # | Rule | Severity | Owner | Where | Why, in one line |
|---|------|----------|-------|-------|------------------|
| 2 | V22 | info | `agent:power` (2), `agent:red_team` (1) | `evidence/sources/{power,red_team}.yaml` | Sources registered but cited by no claim, assessment or intervention. Never an error: registering before curating is a legitimate order of work. Reported per FILE — one of the three is registered by both agents, and each can only edit its own. |

**SCHEMA-SIDE: ZERO. RECORD-SIDE: ZERO.** Every V1, V3c, V6, V14, V15 and V23 violation
is gone. The split over Phase 1 was:

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

### Phase 2 — `src/blueprint/graph/`, `src/blueprint/store/`, `src/blueprint/reports/`
| File | Purpose |
|---|---|
| `graph/model.py` | `GraphNodeRecord` / `GraphEdgeRecord`; order-independent merges. Disagreeing directions collapse to `unclear` rather than to whichever was read first. |
| `graph/compile.py` | The three-layer compiler. Enforces the three rulings; computes per-target coverage. |
| `graph/reference.py` | Reference-data edges (`ENCODES`, `TRANSCRIBED_AS`) and dossier identifiers, from `data/interim/gene_identifiers.jsonl` only (contract §7). |
| `graph/traversal.py` | Null-aware, direction-aware traversal. `support_edges`, `null_result_edges`, `why_not_supported`, `supported_paths`. |
| `graph/export.py` | GraphML, node-link JSON, Neo4j CSV + Cypher generated from one column spec. |
| `store/tables.py` | 11 table builders; nulls stay null, lists become JSON plus a count. |
| `store/views.py` | 12 SQL views, several of which exist to expose a weakness. |
| `store/build.py` | Deterministic Parquet, DuckDB load, provenance table, `MANIFEST.json`. |
| `reports/layout.py` | A dependency-free Fruchterman–Reingold layout (SciPy is not a dependency, so `nx.spring_layout` is unusable above 500 nodes). |
| `reports/graph_html.py` | The self-contained report: 1.65 MB, zero remote references. |
| `reports/build.py` | `make reports` entry point. |

### Phase 2 — CLIs
`graph/build_graph.py` (`--json --store --report --export --all --warnings`) ·
`graph/export_graph.py` (`--html --only --out`) ·
`graph/query_graph.py` (15 canned queries, `--sql`, `--tables`, `--views`, `--json`).

### `tests/` — 429 tests in nine files plus 25 fixture trees
`test_ontology.py` (37) · `test_ids.py` (74) · `test_schemas.py` (91) ·
`test_validate_rules.py` (~90) · `test_state_model.py` (48) · `test_validator_cli.py` (29) ·
`test_graph_compile.py` (26) · `test_store.py` (14) · `test_export.py` (32).
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
8. **A ClinicalTrials.gov record has two titles. Register the `officialTitle`.** The
   API returns both `briefTitle` (a short label) and `officialTitle` (the full
   protocol title), and they are not the same string. The red team registered a trial
   from `briefTitle` while `agent:power` had registered the same trial from
   `officialTitle`, and the §1.3 divergence rule fired — correctly, since two
   registrations of one id disagreed about what the registry said. The divergence check
   compares normalised titles with a similarity threshold, so punctuation and subscript
   differences are absorbed, but a brief-versus-official mismatch is a genuinely
   different string and will keep tripping it. `scripts/fetch_source_metadata.py`
   verifies against `officialTitle`.
9. **`direction` has THREE values that are routinely confused.** `no_change` = MEASURED
   and no change was found (a finding, and rule V-DIR2 requires a measured endpoint);
   `unclear` = a direction exists and we do not know it; `not_applicable` = no direction
   applies at all. An `expression`, `theoretical_construct`, `evidence_gap` or
   `methodological` claim takes `not_applicable` — using `no_change` makes a record
   nobody measured for a change read as a measured null.

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


---

## 7. Phase 2 — the graph, the store, the exports and the report

### Graph statistics (current tree)

| | nodes | edges |
|---|---|---|
| evidence layer | 905 | 1256 |
| biological layer | 304 | 366 |
| intervention layer | 75 | 81 |
| **total** | **1284** | **1703** |

Edges by provenance class: **636 claim-derived**, **942 reference-data**,
**125 ontology-axiom**, **0 tool-mediated**. These counts move between runs while
agents write; they were taken from the final build of this session. The last figure is zero because no agent has
yet registered a `SRC:DB:*` release through `scripts/record_tool_snapshot.py` and then
cited it as the basis of a compiled edge; the class and its vocabulary are in place, so
the first one will compile without a code change.

Of the 636 claim-derived edges: **10 are null results**, **130 count as support**, and
**34 assert an effect** (gated by V16). The remaining ~496 are claim-derived but not
support — they state no direction, or state `no_change`/`unclear`. That is not an
oversight and `v_unsupported_edges` explains each one, because somebody will otherwise
conclude an edge was overlooked.

### THE GRAPH IS SPARSE, AND THAT IS THE ANSWER

447 edges across layers 2 and 3, of which 99 count as evidence for anything. Twenty-seven
targets, and the thinnest four (`EIF2S1`, `KCNQ3`, `OTX2`, `PTPN5`) have two claims, two
sources and **no human evidence at all**. `make graph` prints the sparseness note itself
rather than leaving a reader to work it out.

This is the honest output of decision D004. A contract that refuses an edge without
provenance, refuses efficacy from binding, refuses a null recorded as a gap and refuses a
direction the curator did not state produces a small graph. A denser one would mean
either more evidence or a lower bar, and nothing in this repository lowered the bar to
get a better-looking picture.

### Store

`data/processed/blueprint.duckdb`, rebuilt by `make store`, git-ignored. 11 tables plus
`provenance`, and 12 views:

| table | rows | | view | rows |
|---|---|---|---|---|
| nodes | 1275 | | v_unsupported_edges | 528 |
| edges | 1682 | | v_evidence_by_species_and_life_stage | 49 |
| assessments | 405 | | v_claims_per_target | 27 |
| evidence_items | 394 | | v_evidence_gaps | 26 |
| claims | 290 | | v_claims_by_human_relevance | 22 |
| sources | 182 | | v_coverage_by_facet | 15 |
| state_variables | 101 | | v_null_results_by_target | 13 |
| annotations | 43 | | v_sources_shared_across_agents | 11 |
| interventions | 36 | | v_state_variable_measurability | 8 |
| audits | 30 | | v_edges_by_provenance | 7 |
| targets | 27 | | v_reporting_gaps | 3 |
| provenance | 13 | | v_uncited_sources | 3 |

`data/processed/MANIFEST.json` records a sha256 per artefact. Parquet is byte-identical
across builds (`provenance.parquet` excepted — it embeds a timestamp by design), which
is what makes those checksums worth having.

### The three rulings, and where each is enforced

1. **`evidence_gap` is graph-inert.** `compile.py` emits the evidence-layer Claim node,
   its `REPORTS` chain and its `ABOUT` edge, and returns before any layer-2/3 edge.
   Asserted by `test_evidence_gap_produces_no_biological_or_intervention_edge`, and the
   mirror test checks the claim is still *visible* in the evidence layer — graph-inert
   means no biological edge, not invisible. 26 gaps are recorded.
2. **`NO_DETECTED_EFFECT_ON` is marked, never dropped.** Every null edge carries
   `is_null_result: true` and its `negated_relation`; `counts_as_support` is false;
   `supported_paths` will not route through one; the flag survives JSON, GraphML and the
   Neo4j CSV, and the Cypher script tells the reader to filter on
   `counts_as_support = true`. Dropping them instead would restore exactly the bias the
   relation was created to remove.
3. **Direction is load-bearing.** `no_change`, `unclear` and an absent direction are all
   non-support, and `why_not_supported()` explains which. Two claims licensing one
   triple with opposite signs collapse to `unclear` rather than picking a winner.

### The report — `reports/intelligence_graph_v0_1.html`, 1.65 MB

Self-contained: **zero remote references**, no external script, stylesheet, font or
image; data embedded as sorted JSON; layout computed in Python so the file is
diffable. Pan, zoom, search, filter by layer / node type / edge class, click a node for
a side panel, hover an edge for its relation, direction and claim ids.

**Null-result edges are dashed red, drawn last so an ordinary edge cannot hide one, with
a legend that states what they mean** and a "show only null results" button. There is a
second legend note for claim-derived-but-not-support edges, because an absent sign is
not a positive one and a reader would otherwise assume it was.

**No score-like figure appears without its coverage.** Every target panel shows claims,
distinct sources, human-evidence claims, facets graded, facets not assessed, facets at 0,
null results, evidence gaps and `reporting_gap_count` — with the zeros in red — above
anything else, under the heading "the honest counterweight to how connected this target
looks. Read them first." The red team's verdict is attached to the same panel (all 27
targets are `retain_with_downgrade`), and a target with no audit gets an explicit
NOT YET AUDITED note rather than silence.

### One thing the orchestrator must fix — `make store` and `make reports` fail

Both call `$(PY) -m blueprint.…`, and `blueprint` is not importable: the project was
never installed into `.venv` (`make setup`'s editable install has not run). `make graph`
and `make validate` work because `graph/*.py` bootstrap `src` onto `sys.path`
themselves; a `-m` invocation cannot.

Two one-line fixes, either is fine, and **both are in the orchestrator's lane so I have
not applied either**:

* `PY ?= PYTHONPATH=src .venv/bin/python` in the Makefile; or
* run `make setup` (`uv pip install -e ".[dev]"`).

Verified working with the first: `PYTHONPATH=src .venv/bin/python -m blueprint.store.build`
and `-m blueprint.reports.build` both succeed. My brief forbade installing anything, so I
did not install the project to work around it.

### Phase 2 open questions

1. **`tool_mediated` has no edges yet** (see above). Nothing is wrong; it is untested
   against real data, and the first agent to use it should check the compiled edge
   carries the class rather than falling back to `reference_data`.
2. **`v_unsupported_edges` has 528 rows**, which is most of the claim-derived graph.
   That is accurate and it is also the single most misreadable number in the store: it
   is not 528 broken edges, it is 528 edges whose claims state no direction. If anything
   here needs a second opinion it is whether that many unsigned claims is a curation
   problem the domain agents should be asked about.
3. **The layout is force-directed per layer**, which is readable at this size and will
   not be at ten times it. A future version should cluster rather than place every node.
4. **Neo4j import is untested against a live Neo4j** (export-only per D006). The headers
   and the Cypher script are checked against each other, not against the database.
5. **The HTML embeds the whole graph** (1.65 MB). Fine now; at ten times the size it
   should page or pre-filter rather than grow.


---

## 8. Addendum — `direction: not_applicable`, rule V-DIR2, and the V22 attribution fix

### The V22 attribution question: CONFIRMED as a defect, and fixed

Per-`source_id` attribution was wrong. `_index_sources` keeps one record per id, so
reading `added_by` off that survivor attributed a shared uncited source to whichever
agent's file sorted first and told the other nothing. `SRC:NCT:NCT01455376` is registered
by **both** `agent:power` and `agent:red_team` and cited by neither, and only `power` was
being told. Since an agent can only edit its own file, the finding was unactionable for
one of them and invisible to the other.

V22 now reports **per registering file**, using `shared_sources` rather than the indexed
record's `added_by`. Both files are now named, and the message says why. Pinned by
`test_v22_reports_a_shared_uncited_source_to_every_registering_file`.

### `direction: not_applicable` — and the debt was paid, not tracked

Added to the vocabulary and the claim schema, with the three-way distinction written into
the vocabulary's own description because this is a documented recurring error mode:

* `no_change` — **MEASURED**, and no change was found. A finding.
* `unclear` — a direction **exists** and we do not know which way it runs.
* `not_applicable` — **no direction applies.** For `expression`,
  `theoretical_construct`, `evidence_gap` and `methodological` claims.

**Rule V-DIR2** has two limbs, both warning-only. The first is the briefed one:
`no_change` requires at least one evidence item with `endpoint_measured: measured`. The
second is what actually caught the 31 records — the coordinator's 31 `expression` claims
all *did* measure an endpoint (expression was measured in a tissue), so limb 1 passed
and the record still said the wrong thing. `no_change` on a claim type that asserts no
direction is wrong whatever was measured, because it claims a null result the study never
reported.

V-DIR2 found exactly the 31, all `expression`, all `directionless_claim_type`.
**`agent:alphacognition` then corrected all 31 to `not_applicable` while this was being
written**, so V-DIR2 now reports zero and 31 claims carry `not_applicable`. The warning
severity was chosen to avoid re-opening finished atlases; in the event the owning agent
paid the debt rather than carrying it, which is the better outcome and not one I
arranged.

### A display bug found while checking the above

The CLI headline computed `warnings = total - errors`, which labelled every `info`
finding a warning — misreporting a finding that never fails a run as one `--strict`
would escalate. Severities are now counted explicitly, the headline says
`N error, N warning, N info`, and `test_info_findings_are_labelled_info_not_warning`
pins it.

### The fifth instance of one error mode

`docs/ONTOLOGY_NOTES.md` §5 now records this as the sprint's most persistent pattern
rather than as five unrelated bugs: **five times a "we looked and found nothing" value
was pressed into service for "there was nothing to look for"** — V16c, R11, R14, the
state-variable annotation checks, and now V-DIR2. It recurred across four agents and the
contract itself, and in every case the enum simply lacked a value for the third state.
Three of the five were mine. The generalisation for the next sprint's brief: **before
requiring a value for a field, enumerate the states the field must distinguish, and check
that the honest value for each one exists and does not trip the rule.**
