# Handoff — `agent:power` (Cognitive Power Atlas)

**Sprint 1 · 2026-09-17 · branch `sprint-1/foundation` · run_id `sprint1-power-01`**

---

## 1. Headline

**The null hypothesis cannot be rejected.** On the human evidence I retrieved, H0 —
"cognition is not power-limited in healthy, rested, well-fed adults" — is the most
parsimonious reading, and **H1 (global supply limitation) is actively weakened** by it.

The decisive records are human and randomised:

* `CLM:power:creatine_human:002` — pooled RCTs of the best-studied energetic
  intervention in this space: memory benefit in older adults (SMD 0.88), and an
  estimate centred essentially on zero in the 11–31 year band (SMD 0.03, 95% CI
  −0.14 to 0.20, I² = 0%, P = 0.72).
* `CLM:power:creatine_human:003` — an independent randomised null on *every* cognitive
  task in young, healthy, omnivorous, physically active adults, whose
  physical-performance arm confirmed the intervention was biologically active in the
  same participants.
* `CLM:power:SLC6A8:002` — deleting the creatine transporter in **adult** mice produced
  no cognitive deficit, while the *same* deletion neonatally did.

Where human benefit does appear, it appears in **low-baseline or stressed states**:
vegetarians (`:001`), sleep deprivation (`:004`), acute hypoxia (`:005`), and older
adults. That is the signature of **H2 (local/transient mismatch)** or **H5 (allocation
limitation)**, not of a global supply ceiling. The response shape for
`SV:power.phosphocreatine_reserve` is therefore annotated `state_dependent` with five
claim refs — not `linear`, not `threshold`.

**H4 (thermal/ROS) is unaddressed in either direction.** I searched and curated
nothing for it. That is a gap, not a verdict.

---

## 2. Real numbers

| Quantity | Value |
|---|---|
| Sources registered | **41** |
| Sources reaching `status: verified` | **41** (100%; zero failures, zero dropped) |
| Registries used | PubMed (40), ClinicalTrials.gov (1) |
| Claims written | **49** |
| Claims contradicting or nulling the power-limitation reading | **10** |
| Claims that only *qualify* | 17 |
| Evidence items by role | supports 23 · qualifies 18 · contradicts 8 · null_result 2 |
| Claims with `status: contested` | 3 |
| Evidence items with `content_checked: false` | **1** |
| Facet gradings | **42** (40 `assessed`, 2 `not_assessed`) |
| Target dossiers | 7 |
| Intervention entities | 8 |
| State variables annotated with claim support | 6 of 22 (16 left `unknown`) |

### Claims per target / topic

| File | Claims | Human-relevant | Contradicting or null |
|---|---|---|---|
| `SLC6A8` (deep) | 6 | 1 | 1 (`:002`, null) |
| `CKB` (deep) | 6 | 2 | 1 (`:006`) |
| `SLC16A7` / MCT2 (deep) | 5 | **0 — none exists** | 0 in-file; see §6 |
| `HCAR1` (deep) | 6 | **0 — none exists** | 2 (`:001`, `:004`) |
| `SLC16A1` / MCT1 (shallow) | 4 | 2 | 1 (`:003`) |
| `SLC16A3` / MCT4 (shallow) | 3 | **0 — none exists** | 0 in-file; see §6 |
| `KL` (shallow) | 4 | 3 | 1 (`:003`) |
| `astrocyte_neuron_lactate_shuttle` (topic) | 5 | 0 | 2 (`:002`, `:003`) |
| `brain_energy_budget` (topic) | 5 | 0 | 1 (`:003`) |
| `creatine_supplementation_human` (topic) | 5 | 5 | 1 (`:003`, null) |

All four deep targets exceed the ≥4-claim floor; all three shallow targets exceed ≥2.

### The 10 counter-claims, named

`CLM:power:SLC6A8:002` (adult-onset deletion null) · `CLM:power:creatine_human:003`
(randomised human null) · `CLM:power:CKB:006` (phosphocreatine *higher* in early
Alzheimer's) · `CLM:power:SLC16A1:003` (human MCT1 loss of function is a metabolic,
not cognitive, syndrome) · `CLM:power:KL:003` (same "protective" haplotype, *higher*
dementia incidence) · `CLM:power:HCAR1:001` (receptor activation *lowers* cortical
gain; nulls are more active at baseline) · `CLM:power:HCAR1:004` (receptor deletion
*raises* endurance; the axis causes central fatigue) · `CLM:power:anls:002` (the
shuttle was never actually measured; the tools are not specific) ·
`CLM:power:anls:003` (dorsal hippocampus used direct glucose uptake, not lactate) ·
`CLM:power:budget:003` (myelination need not save energy).

### Facets `not_assessed`, and why

Exactly two, both `transfer_breadth`:

* `atlases/power/assessments/SLC16A1.yaml`
* `atlases/power/assessments/SLC16A3.yaml`

**Reason:** both are declared-shallow dossiers, no retrieved study for either target
measured more than one endpoint family, and my searches were not directed at breadth.
I recorded `not_assessed` with `level: null` rather than `0`, because `0` means
"searched, found nothing" and I did not search this facet for these two targets.
Writing `0` there would have been a contract violation.

Everything else is `assessed`, including the many honest zeros. Note the shape of
those zeros — they are the atlas's main finding:

* `human_intervention_evidence` is **0 for five of seven targets**. The only non-zero
  is `SLC6A8` at level 2, and even that intervenes on the *substrate*, not the gene.
* `above_baseline_enhancement` **never exceeds 2**, and in both cases where it reaches
  2 (`HCAR1`, `KL`) the `counter_level` is **3** — the contradicting evidence is
  stronger than the supporting evidence.
* `SLC6A8` carries the atlas's only `0 / 2` on `adult_onset_perturbation`: the
  experiment was done, designed to answer exactly this, and came back negative.

---

## 3. Exact commands run, with real output

```
$ .venv/bin/python scripts/fetch_source_metadata.py --agent power
power: 41/41 verified -> data/interim/source_verification/power.jsonl
41/41 sources verified
                                                          # exit 0, no failures
```
Run twice: once on the first 37 sources (37/37) and again after appending 4 more
(41/41). Every title and year I transcribed matched its registry record on the first
attempt; **no identifier needed "correcting", and none was guessed.**

```
$ .venv/bin/python scripts/check_ownership.py --agent power --paths <39 hand-authored files>
all 39 path(s) owned as expected                          # exit 0
```

⚠️ **Note for the orchestrator:** `check_ownership.py --agent power` with *no*
`--paths` reports **840 violations**. That is not a lane breach by me — with the tree
uncommitted, `changed_paths()` returns every file in the repository, so it classifies
`agent:ontology`'s `state_model/`, `agent:brakes`'s 14 dossiers, and the ambiguous
`tests/test_ranking*.py` and `tests/test_uncertainty*.py` globs (claimed by **both**
`agent:integration` and `agent:ontology` in `docs/OWNERSHIP.yaml` — a real ambiguity
worth fixing). Passing only my paths also flags
`data/interim/source_verification/power.jsonl` as `generated_only`, which is correct:
the script wrote it, I did not hand-edit it.

```
$ ls graph/
(empty)
```
`graph/validate_graph.py` **does not exist yet**, so `--strict` could not be run. In
its place I wrote and ran a self-check in my scratchpad implementing the rules I can
check locally — V2 (id patterns), V3 (triple legality against
`ontology/edges.yaml` domain/range **and** `allowed_claim_types`), V4 (every claim ref
in every assessment, dossier, annotation, `competing_models.yaml` and `metrics.yaml`
resolves), V5 (≥1 evidence item, every source registered **and** verified), V7, V8
(`translation.*` complete), V9 (no bare float in (0,1) outside
`effect_size`/`p_value`), V10 (`ordinal_grade`, level ∈ 0..4), V11 (facet ownership and
level/status rules), plus every `SV:` id resolving in `state_model/`:

```
sources registered=41  verified=41  unverified=[]
claims=49  facet gradings=42
evidence_role counts={'supports': 23, 'qualifies': 18, 'contradicts': 8, 'null_result': 2}
PASS: no contract violations detected by this self-check
```

**`pytest` was NOT run** — `agent:ontology` owns `tests/` and was writing it
concurrently. **No git command was run at any point.** **No dependency was installed.**

Five triples failed my first self-check pass and were corrected before this note was
written, all of them ontology-legality failures rather than evidence failures:
`MODULATES` does not admit `claim_type: methodological`; `PREDICTS` excludes a
`MolecularProcess` subject; `POSITIVELY_REGULATES` does not admit `association`;
`MODULATES` excludes `MetabolicIntervention` from its domain (×2); and
`direction: state_dependent` is not in the contract's `direction` enum.

---

## 4. Blocking issue filed: nulls have no legal triple

`docs/blackboard/schema_change_requests/power-001.yaml` (`blocking: false`).

**No predicate in `ontology/edges.yaml` admits `claim_type: clinical_null`, and no
intervention-layer predicate admits a no-effect assertion from a
`MetabolicIntervention`, `Compound`, `Drug` or `Biologic` node at all.** The only
relation whose domain holds the intervention node types and whose range holds
`StateVariable` is `CHANGES_STATE`, which carries `asserts_effect: true` and is
documented as "THE EFFICACY RELATION".

The consequence biases the compiled graph in exactly the direction this repository
exists to resist: **a positive trial compiles into an edge; a null trial of the same
intervention cannot.** A ranking model consuming compiled edges would see only the
positives. This is not hypothetical — it hit the two most decision-relevant records I
have (`creatine_human:002`, `creatine_human:003`).

**Workaround applied:** those two claims use `subject: MECH:creatine_substrate_loading`
(a `Mechanism` node, which *is* in the `MODULATES` domain) with
`direction: no_change` and `evidence_role: null_result`. Semantically defensible — the
mechanism was engaged and the variable did not move — but it loses the fact that the
manipulation was a randomised human intervention on a named substance, and it forces
`claim_type: causal_perturbation` onto a record whose true type is `clinical_null`.

Secondary: `claim_type: methodological` is also admitted by no predicate, so the
published critique of the lactate shuttle (`CLM:power:anls:002`) had to be filed as
`theoretical_construct`.

---

## 5. For the red team — attack these first, in this order

1. **`CLM:power:HCAR1:004` — my worst interpretive leap.** A weight-loaded swimming
   endurance endpoint in male mice, mapped by me onto
   `SV:cognition.sustained_attention_stability`. The study measures neither cognition
   nor information processing. I flagged this in `alternative_explanations` and in the
   claim's own `risks`, but it is still a construct jump I made and it should probably
   be downgraded or re-pointed at a motor state variable.
2. **`CLM:power:SLC16A1:003` — argument from a non-cognitive presentation.** I read
   "human MCT1 loss of function presents as ketoacidosis, not as a cognitive
   syndrome" as evidence against a cognitive bottleneck. The cohort was **ascertained
   by ketoacidosis**, so any cognitive phenotype would be systematically
   under-detected. Absence of evidence, dressed as evidence of absence. Check whether
   `evidence_role: contradicts` is defensible or should become `qualifies`.
3. **`CLM:power:CKB:002` — the one `content_checked: false` in the atlas.** I could only
   reach the CKB behavioural phenotype as a one-sentence secondary report inside
   another paper's abstract. Automatic downgrade applies. If CKB's rank depends on it,
   the primary paper must be retrieved first.
4. **`CLM:power:creatine_human:001` (Rae) versus `:002` (pooled).** A single 2003
   crossover trial reporting p < 0.0001 on Raven's APM, in a population the later
   pooled analysis covers and finds null. I marked it `status: contested` with
   `replication_status: conflicting`, but a reader wanting a positive result will
   quote it. Check for a practice-effect confound in the crossover, and for
   small-study effects in the 2003 report.
5. **The ANLS strand as a whole.** I registered the founding result
   (`anls:001`, `status: contested`) and the published critique (`anls:002`) with
   opposite `evidence_role` and withdrew neither. If you think that fence-sitting is
   wrong, say which side and why — but note that **four of my seven targets
   (`SLC16A1`, `SLC16A3`, `SLC16A7`, and `HCAR1` via lactate signalling) inherit the
   shuttle's credibility**, so a downgrade of `anls:001` should cascade.
6. **Duplicated evidence.** `SRC:PMID:21376239` (Suzuki 2011) carries evidence in
   `anls:001`, `SLC16A1:001`, `SLC16A3:001` **and** `SLC16A7:001`, and
   `SRC:PMID:31286064` and `SRC:PMID:32693190` each appear in three files. Those are
   genuinely different transporter-specific findings within one paper, but this is
   precisely the duplicated-evidence inflation the ranking invariance test exists to
   catch. Verify the ranking is invariant to it.
7. **`CLM:power:KL:004`** reports a benefit at a low dose and **none at a high dose**.
   Any consumer that reads klotho as monotonically beneficial has committed a
   dose-response inversion. Also note the primate study's author list includes a
   commercial developer of klotho therapeutics, which I recorded in
   `atlases/power/interventions/klotho_protein.yaml`.
8. **`competing_models.yaml`'s `current_evidence_direction` labels are my readings**,
   not measurements, of a small deliberately curated set. The rodent mechanistic
   literature I used was not designed to discriminate H0–H5. Attack the mapping, not
   just the individual claims.

Two things I do **not** think you will find: a fabricated identifier (all 41 sources
verified against their registries on the first pass) and a dose or regimen (none
appears anywhere, including where source abstracts reported them).

---

## 6. Honest gaps, stated as gaps

1. **`SLC16A7` and `SLC16A3` have no contradicting or null claim in their own files.**
   Their countervailing evidence lives in the topic file (`anls:002`, `anls:003`) and
   is wired in through `counter_claim_refs` in their facet assessments. That satisfies
   the requirement in substance, but a reader opening only `SLC16A7.yaml` will see
   five supporting-or-qualifying claims and no counterweight. The file header says so
   in capitals; a structural fix would be better.
2. **Zero human evidence for `SLC16A7`, `SLC16A3` and `HCAR1`.** The target with the
   best mechanistic evidence in the atlas (`SLC16A7`, mechanistic level 3, adult-onset
   level 3) has **no human data of any kind**. That combination — strong mechanism,
   zero translation — is the most important thing `agent:integration` needs to see.
3. **No gain-of-function experiment exists anywhere in this atlas.** Not one study, in
   any species, raises transport capacity, kinase activity or receptor expression
   above wild type. The entire base is loss-of-function plus substrate loading. Every
   `proposed_modulation: increase_activity` in my dossiers is therefore a hypothesis
   with **zero** supporting evidence, and `SLC16A7.yaml` says that explicitly.
4. **Remit items that returned nothing usable:** mitochondrial spare capacity and
   OXPHOS; neurovascular coupling; oxygen extraction; ROS; thermal burden. Sixteen of
   22 power/efficiency state variables remain `unknown`. Awkwardly, this includes
   *every* variable H2 and H4 depend on — so the hypothesis most compatible with the
   observed human state-dependence (H2) has an entirely unpopulated central variable.
5. **`KL` may not belong in a power atlas at all.** Its reported mechanism is synaptic
   and glutamatergic (GluN2B, LTP), not metabolic. Nothing links it to any power- or
   efficiency-domain state variable. Its presence here is inherited from
   `targets/seed_registry.yaml`, and `targets/candidates/KL.yaml` says so.
6. **`identifiers: {}` in all seven dossiers**, awaiting
   `scripts/fetch_gene_identifiers.py`. HGNC snapshots for all seven symbols already
   exist under `data/raw/hgnc/2026-09-17/`, so this should resolve cleanly.
7. **I did not write an NCBI taxonomy snapshot.** Species taxids (9606, 10090, 10116,
   9544) were resolved live from NCBI E-utilities this session, so no identifier came
   from memory — but `data/raw/ncbi_taxonomy/**` belongs to `agent:comparative`, so I
   stayed out of it. **`agent:comparative` should snapshot those four taxids** to make
   my claims offline-rebuildable per P7.
8. **`docs/OWNERSHIP.yaml` has a real ambiguity:** `tests/test_ranking*.py` and
   `tests/test_uncertainty*.py` are claimed by both `agent:integration` and
   `agent:ontology`. Flagging for the orchestrator; not my lane to fix.

---

## 7. What downstream agents need

**`agent:integration`** — Consume the ordinal facet levels in
`atlases/power/assessments/`, never the constructs in `metrics.yaml`: both
`cognitive_power_reserve` and `neural_efficiency` are `theoretical_construct` with
`units: null`, and `metrics.yaml` carries a `do_not_do` list explaining why no proxy
identifies either. **Nothing under `atlases/` may produce a number.** Note that my
`counter_level` exceeds `level` on `above_baseline_enhancement` for both `HCAR1` and
`KL` — if your aggregation cannot express "tested and failed" differently from
"nobody looked", it will get those two backwards. Read
`competing_models.yaml` before weighting anything in the power domain: H1, the version
of the hypothesis a ranking model would implicitly assume, is the one my evidence
weakens.

**`agent:ontology`** — `power-001` is the request that matters; nulls currently cannot
compile. Also note `state_model/safety.yaml` has no variable corresponding to
acid-base failure, which is why `AE:ketoacidosis` in the `SLC16A1` dossier has no
safety coupling.

**`agent:alphacognition`** — `H1.T2` in `competing_models.yaml` proposes a
summary-statistics Mendelian randomisation from perfusion and metabolic traits to
fluid intelligence. That is your lane; I proposed it and did not execute it. Please
keep educational attainment out of it. `KL` also has human genotype associations I
recorded only as `association` with `basis: human_observational_association` — the
`human_genetic_association` and `causal_gene_attribution` facets are yours to grade.

**`agent:brakes`** — `CLM:power:CKB:001` (creatine-kinase deficiency suppressing
pentylenetetrazole seizures) touches `SV:safety.seizure_risk`, which your `KCNQ2`,
`KCNQ3` and `HCN1` work also touches. `CLM:power:HCAR1:001` reports HCAR1 functionally
cross-talking with adenosine A1 receptors, which is your `ADORA1` lane.

---

## 8. Can H0 be rejected? My honest read

**No.**

Not because the evidence is thin — though it is — but because the best-designed human
experiments available point the other way. The one intervention in this space with
repeated randomised human trials and a `g`-proximal endpoint produces **no detectable
cognitive effect in rested, fed, young adults at normal substrate baseline**, while
producing a clear physical-performance effect in the same participants. Deleting a
supply gene in an **adult** mouse produces no cognitive deficit, while deleting it
developmentally does. Human loss of function at the one lactate-axis gene with a
defined human phenotype presents as a metabolic, not a cognitive, disorder. And the
human brain's measured cortical signalling rate is inferred to be several-fold
**lower** than the rat's, which is the wrong direction for a species running at its
energetic ceiling.

What the evidence *does* support is narrower and more interesting than the hypothesis
I was asked to model: **energy handling looks like a state-dependent constraint that
binds when baseline is low or the system is stressed, and an allocation policy the
brain actively adjusts rather than a ceiling it presses against.** The single cleanest
mechanistic demonstration in the atlas — food-restricted mouse cortex reducing synaptic
ATP use by 29% while *holding spike rate constant* and paying for it with a 32%
broadening of orientation tuning, all reversed by leptin — is not a brain running out
of energy. It is a brain **choosing to spend less**, under hormonal instruction. That
is H5, and it is nearly indistinguishable from H0 on any supply intervention, which is
why `competing_models.yaml` records that no test I proposed separates them except
`H5.T1` and `H5.T2`.

Two caveats on my own conclusion. First, **H0 and "no constraint exists" are not the
same claim.** H2 and H4 could each be true and would be invisible to everything I
retrieved: no human method in `metrics.yaml` resolves the spatial or temporal scale at
which a local supply–demand mismatch would occur, and I found no thermal or oxidative
evidence at all. Second, **this is a reading of 41 sources curated by one agent in one
sprint**, not a systematic review. The absence of a positive result in a small
deliberately assembled set is weak evidence. It should be attacked, not trusted — and
§5 is my best attempt to make that easy.

---

# Round 2 — migration onto the amended contract

**2026-09-17, second pass.** `docs/blackboard/RESOLUTIONS.md` R5, R9, R10, R11, R12 and
amended `docs/DATA_CONTRACT.md` §5.2 / §5.4 / §5.5 read in full before editing. The
orchestrator's diagnosis was right: almost all of the 212 violations in these files were
the schema demanding things the contract now agrees it should not have demanded.

## 9. What changed, by category

### R11 — `search_basis` on every level-0 facet: **16 written**

| Target | Facets given a `search_basis` |
|---|---|
| `CKB` | `adult_onset_perturbation`, `above_baseline_enhancement`, `transfer_breadth`, `dose_response_knowledge`, `human_intervention_evidence` (5) |
| `SLC16A7` | `above_baseline_enhancement`, `dose_response_knowledge`, `human_intervention_evidence` (3) |
| `SLC16A3` | `above_baseline_enhancement`, `dose_response_knowledge`, `human_intervention_evidence` (3) |
| `SLC16A1` | `above_baseline_enhancement`, `human_intervention_evidence` (2) |
| `SLC6A8` | `adult_onset_perturbation` (1) |
| `HCAR1` | `human_intervention_evidence` (1) |
| `KL` | `human_intervention_evidence` (1) |

Each names the queries actually run, the scope, and what would have counted as a hit.
Writing them changed the atlas twice over, because making a zero auditable forced me to
check it:

* **I had not searched ClinicalTrials.gov for most of these targets.** The zeros were
  PubMed-only. I ran the missing registry searches rather than write a `search_basis`
  that described a search I had not done.
* **One of those searches found something.** `SRC:NCT:NCT07285629` — a *completed*
  early-phase-1 human klotho intervention in 14 healthy adults aged 50–80, whose
  secondary outcomes are five NIH Toolbox cognitive measures at four timepoints. My
  previous handoff said no human klotho intervention existed. **That was wrong, and it
  was wrong because I had only searched the literature.** The facet still grades 0 and
  the record says why: no results are posted (`has_results: false`), it is
  non-placebo-controlled at n=14, and klotho is co-administered with follistatin so
  klotho's own contribution is unidentifiable by design. But "graded 0 because a
  completed trial reported nothing" is a different statement from "graded 0 because
  nobody has tried", and only the first is true.
* The lactate-axis zeros are now concrete too: a registry search returned 19 human
  trials manipulating lactate against cognitive endpoints, and **none** targets a
  monocarboxylate transporter or the lactate receptor — they manipulate circulating
  substrate. `SRC:NCT:NCT01455376` is registered as the example.

**Rubric gap found.** `evidence_strength_v1` level 0 means *searched, nothing found*,
and level 1 means *weak evidence exists*. There is no value for **"a trial exists,
completed, and reported nothing"**, which is now the state of the KL human-intervention
facet. I graded it 0 and put the whole story in `search_basis`; a reader who only reads
the integer will draw the wrong conclusion. Worth a rubric value in Sprint 2.

### R5 — `endpoint_measured` on every evidence item: **51 written**

`measured` 43 · `not_measured_in_protocol` 6 · `measured_but_not_reported` 1 ·
`unknown` 1.

The six `not_measured_in_protocol` are the four biophysical energy-budget models and the
two critical reviews — nothing was measured in any of them, which is exactly the point
those records exist to make. The single `measured_but_not_reported` is
`SRC:NCT:NCT02931682`, terminated with no posted results against a specified Bayley-4
primary outcome. The `unknown` is `CLM:power:CKB:002`, my one `content_checked: false`
record, where I read a secondary summary rather than the primary paper and therefore
cannot assert what was measured.

**Claims retyped to `evidence_gap`: zero.** I checked both nulls against V16c
individually rather than assuming:

* `CLM:power:creatine_human:003` — Stroop and Trail Making **were** administered
  pre- and post-exercise. A measured absence. Stays a null.
* `CLM:power:SLC6A8:002` — Morris water maze, novel object recognition and conditioned
  fear **were** run on the adult-onset knockouts. A measured absence, and a designed
  one. Stays a null.

Both therefore satisfy V16c with `endpoint_measured: measured` and
`evidence_role: null_result`. Neither is an absence of measurement, so neither may be
demoted to graph-inert — which matters, because these two are the load-bearing records
behind this atlas's H0 reading.

### R9 — `power-001` resolved: **2 claims migrated to `NO_DETECTED_EFFECT_ON`**

| Claim | Now | `negated_relation` | Was |
|---|---|---|---|
| `CLM:power:creatine_human:003` | `METAB:creatine_monohydrate_supplementation` → `SV:cognition.attentional_control`, `clinical_null` | `CHANGES_STATE` | `MECH:creatine_substrate_loading -MODULATES->`, `causal_perturbation` |
| `CLM:power:SLC6A8:002` | `PROT:SLC6A8` → `SV:cognition.learning_rate`, `causal_perturbation` | `POSITIVELY_REGULATES` | `PROT:SLC6A8 -MODULATES->` |

The first regains its real subject: it is a randomised human trial of an administered
substance, and the `MECH:` workaround had hidden that. The second gains something it
never had — it now states *which* positive claim it negates (`CLM:power:SLC6A8:003`'s
assertion that the transporter positively regulates learning rate), so the adult-onset
null is legible as a rebuttal of the developmental result rather than as an isolated
shrug. `MECH:creatine_substrate_loading` survives as the subject of
`CLM:power:creatine_human:002` only, which is not a null.

### R10 — `direction_context`: **1 claim**

`CLM:power:creatine_human:002` moves from `direction: unclear` to
`direction: state_dependent` with an explicit context. This is the claim R10 was written
for. Under the old vocabulary I had been forced to record "we know it varies and we know
what with" as "we do not know". The context now names the three dependencies the
evidence actually shows: **substrate baseline** (positive in vegetarians, null in
omnivores), **age band** (positive 66–76, null 11–31), and **imposed energetic stress**
(positive under sleep deprivation and hypoxia), with the claim ids for each.

### R12 — `attributes`: **1 record**

`aav_slc6a8_intracisternal_gene_therapy.yaml` moves `vector_serotype` out of
`identifiers` into `attributes`, with the honest value
`"not_stated_in_retrieved_text"`, plus `vector_platform` and `delivery_route`. The
information no longer has to be either dropped or smuggled into a field that means
something else.

### ChEMBL numerics: **3 V9 warnings cleared, and a provenance problem surfaced**

Moved to the canonical `max_clinical_phase` slot — but with `value: null` and the figure
in `as_reported` as a string. **I could not honestly name a `database_source_id`.** V9
exempts `max_clinical_phase.value` only when a pinned `SRC:DB:*` release is named, and
under R1 a `SRC:DB:*` source verifies only against a snapshot in
`data/raw/MANIFEST.jsonl` whose sha256 still matches. ChEMBL was reached here through an
MCP tool that **writes no snapshot**, so no pinned release exists to point at, and
`data/raw/chembl/**` has no owner in `docs/OWNERSHIP.yaml` for me to write one into.
Rather than invent a release string, I asserted no number. The limitation is recorded in
both files under `attributes.provenance_limitation`.

**This is a real gap, not a formatting quibble:** any agent using the ChEMBL MCP tools
will hit it, and the effect is that ChEMBL facts can only enter this repository as
unprovenanced strings. Two possible fixes: give `data/raw/chembl/**` an owner and wrap
the ChEMBL calls in a snapshot-writing script, or let `max_clinical_phase.as_reported`
be the canonical home for tool-sourced values and drop `value` entirely.

### Triples and gradings corrected

* **V3, 1 fixed.** `CPD:slc6a8_corrector_tool_compound POTENTIATES PROT:SLC6A8` →
  **`UPREGULATES`**. `POTENTIATES` means allosteric enhancement of the response to an
  endogenous signal; what the paper measured was a trafficking corrector putting more
  functional transporter at the cell surface and restoring uptake. `UPREGULATES` is what
  was measured. The old relation read better and was wrong.
* **V16, 2 claims fixed.** `CLM:power:SLC6A8:001` and `CLM:power:SLC16A1:004` both had
  `CONSTRAINS` into `PHENO:general_cognitive_ability` on `claim_type: association`. The
  rule asked me to decide whether the relation was too strong or the claim type too
  weak. **The relation was too strong in both cases:** nobody perturbed anything in
  either study — one is a natural-history cohort, the other a three-patient case series
  — so `association` is the correct type and a capacity assertion is not licensed. Both
  are now `ASSOCIATED_WITH`. The monogenic strength has not been lost; it lives in
  `causal_attribution.basis: monogenic_disorder` and in `uncertainty.level: 3`, which is
  where it belongs.
* **V16, 1 dossier fixed.** `targets/candidates/KL.yaml` asserted
  `direction: increases` on `SV:cognition.attentional_control` from an observational
  genotype association. Now `direction: unclear` with
  `asserted_relation: associated_with` and a comment explaining that the association's
  own direction is recorded in `CLM:power:KL:002`, not asserted as an effect in the
  dossier.

### `counter_level` changes: **1, downward**

| Facet | Was | Now | Why |
|---|---|---|---|
| `KL` / `mechanistic_causal_perturbation` | `counter_level: 1` | **`0`** | It had `counter_level: 1` with an **empty** `counter_claim_refs`. The schema refused it, correctly, and the refusal exposed an over-grade of mine: nothing contradicts the klotho mechanism. What I had put there was a *scope* objection — nothing links klotho to a power-domain variable — which is a limitation, not counter-evidence. It has moved to `limiting_factor`. |

No other `counter_level` moved. **No counter_level was derived from an `evidence_gap`
claim**, because this atlas has none, so V16c forced no reductions.

### `clinical_harm` → `preclinical_harm`: **0 retypings needed**

Audited all 49 claims: `clinical_harm` is used **zero** times, so nothing was wearing a
clinical label on animal evidence. The nearest candidates were checked individually —
`CLM:power:CKB:001` is animal but its type is `causal_perturbation` and its direction is
seizure *suppression*, and `CLM:power:KL:003` uses `INCREASES_RISK` into `AE:dementia`
but is a human prospective cohort typed `association`. Current distribution:
`causal_perturbation` 27 · `association` 9 · `theoretical_construct` 6 ·
`clinical_efficacy` 3 · `mechanistic` 2 · `pharmacodynamic` 1 · `clinical_null` 1.

### Also fixed, found by the schemas rather than assigned

* `causal_attribution.locus_to_gene_resolved` was `True` in 3 claims — bare `yes` in
  YAML parses as a boolean. Now `"yes"`.
* `general_intelligence_relevance: clinical_cognitive_composite` in 3 claims — that is a
  `phenotype_class` value, not a `general_intelligence_relevance` value. Now
  `multi_domain_cognitive`.
* `phenotype_class`/`endpoint_category: multi_domain_cognitive` in `KL:001` and `KL:004`
  — the same confusion in the other direction. `KL:001` is now `not_reported`, which is
  the honest value: the retrieved abstract says "enhanced cognition" without naming a
  domain. `KL:004` is `episodic_memory`.
* `identifiers.nct_id` → `nct` in the source registry.
* `mechanism_class: substrate_provision` added to `MECH:creatine_substrate_loading`.
* `status_reason` added to the 3 self-contested claims, which halved the V14 warnings
  from 6 to 3 **without un-contesting anything** — the audit-record half of each warning
  is still open, which is correct, because it is the red team's to close.

## 10. Final state — my files only

```
$ .venv/bin/python graph/validate_graph.py --strict            # filtered to power files
4 findings, 0 errors:
  V14  3 warnings — CLM:power:KL:001, CLM:power:anls:001, CLM:power:creatine_human:001
                    contested with no audit record yet. LEFT DELIBERATELY for the red
                    team, per the orchestrator's instruction. Nothing un-contested.
  V22  1 warning  — SRC:NCT:NCT07285629 and SRC:NCT:NCT01455376 cited by no claim.
                    DELIBERATE. They ground `search_basis` prose. Registering them means
                    both identifiers are machine-verified against ClinicalTrials.gov
                    rather than sitting unverified in a prose field; a registry record
                    with no posted results licenses no claim, and `source_refs` is
                    restricted to database-gradable facets so there is no structured
                    slot for them. The warning is the correct price for doing it properly.

$ .venv/bin/python scripts/fetch_source_metadata.py --agent power
43/43 sources verified                                          # exit 0

$ .venv/bin/python scripts/check_ownership.py --agent power --paths <40 files>
all 40 path(s) owned as expected                                # exit 0
```

**Schema errors in `agent:power` records: 0** (verified independently by validating each
record against its own landed schema in `schemas/`, outside the repo-wide run).

`pytest` not run. No git command run. No dependency installed.

## 11. What this round changed about the science

Only one thing, and it is a correction to my own previous handoff: **I claimed no human
klotho intervention existed, and one does.** It has reported nothing, so the atlas's
conclusions do not move — but the reason my zero was wrong is worth recording, because
it generalises. I had searched the *literature* thoroughly and the *trial registry*
hardly at all, and a literature-only search systematically misses exactly the category
that matters most for a translation facet: interventions that were performed and never
published. Four of my remaining `human_intervention_evidence` zeros are now backed by
registry searches as well as literature searches. `SLC16A7` — the target with the
strongest mechanism in this atlas — still has zero human records after both.

The H0 reading in §8 stands unchanged, and the two records it rests on are now stronger
than they were: both are `NO_DETECTED_EFFECT_ON` edges with `endpoint_measured: measured`,
so they compile into the graph as findings instead of disappearing, and no traversal may
count them as support.

---

# Round 3 — `reporting_gap_refs`, and a second thing the search found

## 12. DO NOT TIDY THESE. They are deliberate.

Three items in these files look like loose ends and are not. Each is recorded here so a
later reader does not close them.

1. **Three `contested` claims with no audit record (V14 warnings).** `CLM:power:KL:001`,
   `CLM:power:anls:001`, `CLM:power:creatine_human:001`. Each is self-contested by
   `agent:power` on curation and carries a `status_reason` saying so and naming the
   opposing record. The missing half is the red team's audit, which is **theirs to
   supply, not mine to remove**. Do not un-contest any of them to clear a warning.
2. **Two registered sources cited by no claim (V22 warning).**
   `SRC:NCT:NCT07285629` and `SRC:NCT:NCT01455376`. They exist so that the NCT
   identifiers named in `search_basis` and `reporting_gap_refs` are **machine-verified
   against ClinicalTrials.gov** rather than sitting unverified in a prose field. A
   registration with no posted results licenses no claim — that is the whole point of
   calling it a reporting gap — and `source_refs` is restricted to database-gradable
   facets, so there is no structured slot for them on a facet. Deleting them would trade
   two verified identifiers for two unverified strings.
3. **`CLM:power:SLC16A1:005` has the triple `CLM:power:SLC16A1:005 -ABOUT-> TGT:SLC16A1`,
   i.e. the claim is its own subject.** That is the sanctioned form for a graph-inert
   record, and I got it wrong first: I wrote
   `CPD:CHEMBL3335793 -CHANGES_STATE-> SV:cognition.general_cognitive_ability` and rule
   V3c rejected it. The rejection was correct and its docstring says why — attaching a
   gap to a causal or interventional relation asserts exactly what the record refuses to
   assert. Do not "repair" it into a causal relation.

## 13. `reporting_gap_refs` — 2 written, and why not more

| Facet | Ref | Justification |
|---|---|---|
| `KL` / `human_intervention_evidence` | `SRC:NCT:NCT07285629` | Completed klotho intervention, five NIH Toolbox cognitive secondary outcomes, `has_results: false`. The canonical case. |
| `HCAR1` / `human_intervention_evidence` | `SRC:NCT:NCT01455376` | Completed 2010, interventional, exogenous lactate infusion, neurocognitive **primary** outcome, 60 participants, no results posted in sixteen years. Lactate is this receptor's endogenous ligand, so target engagement is direct rather than by proxy. |

**I deliberately did not list `NCT01455376` on the three MCT facets**, though the
coordinator's note invited me to check them. It infuses circulating lactate, which
engages those transporters' *substrate* rather than the transporters, and listing one
shared trial against four lactate-axis targets would turn one gap into a
`reporting_gap_count` of four. Each of the three `search_basis` fields names the trial
and states that it is listed on HCAR1 only, with the reason, so a red-team reviewer who
thinks the attribution is too narrow can add it. I would rather be wrong in a way that is
visible in the record than inflate a publication-bias metric.

**I also did not list `SRC:NCT:NCT02931682`** (the creatine-transporter-deficiency
study) anywhere in `reporting_gap_refs`. It reached primary completion with 50
participants against a specified Bayley-4 primary outcome and posted no results, so in
substance it is a reporting gap — but the field is defined for *registered
interventions* that *completed*, and this study is **observational** and **terminated**.
It is already captured structurally where it belongs, as
`endpoint_measured: measured_but_not_reported` on the evidence item in
`CLM:power:SLC6A8:001`. If the red team reads the field's scope more broadly, this is the
first record to add.

## 14. The search found a second thing, and it is more important than the first

Running the *target-directed* registry search that the first round never ran —
interventions matching monocarboxylate, MCT1, MCT2, MCT4, GPR81, HCAR1 or lactate
receptor, no condition filter, 20 trials, all screened — returned a direct hit:

**`SRC:NCT:NCT01791595`. AZD3965, a monocarboxylate transporter 1 inhibitor, given to
53 patients in a completed Cancer Research UK phase 1 trial that posted its results.
Every primary outcome is a dose-limiting-toxicity or adverse-event measure. Every
secondary outcome is pharmacokinetic, a cell-death marker, or tumour response. There is
no cognitive endpoint anywhere in the protocol.**

This is `evidence_gap`'s canonical case, written in the contract as "the only human trial
of this mechanism never included a cognitive endpoint", and it is now
`CLM:power:SLC16A1:005` — this atlas's only `evidence_gap` claim. Graph-inert, cited in
no `counter_claim_refs`, and `level` stays 0 because a gap is not supporting evidence.

**The distinction R5 and R14 draw together turns out to matter for two different trials
in the same facet family, in opposite directions:**

* `NCT01791595` — results posted, cognition **never measured**. An **evidence gap**. The
  question was not asked.
* `NCT01455376` — cognition measured as the **primary** outcome, results **never
  posted**. A **reporting gap**. The question was asked and the answer is unavailable.

A single `level: 0` had been covering both, plus genuine absence of enquiry, and the
three are now distinguishable in the data.

**I corrected a second false statement of my own.** The `SLC16A1`
`human_intervention_evidence` rationale used to read "no human intervention on MCT1 with
any cognitive endpoint was retrieved". That was false: an MCT1 intervention exists. The
rationale now says so, says why the grade is still 0, and says that the first-round
wording was wrong **because the first-round search was literature-only**. That is the
second time R11's requirement to state what I actually searched has caught me asserting a
zero I had not earned — first for klotho, now for MCT1.

**A safety signal I must not grade.** The AZD3965 trial's dose-limiting toxicities were
haematological, **cardiac** and **ophthalmic**, and patients with known retinal disease
were excluded at screening. This is the only first-in-human safety read-out for any
target in this atlas. `safety_liability_burden` is `agent:red_team`'s facet and I have
not touched it; the fact is flagged in `targets/candidates/SLC16A1.yaml` `open_questions`,
in `CLM:power:SLC16A1:005` `alternative_explanations`, and in
`atlases/power/interventions/CHEMBL3335793.yaml` `notes`.

## 15. ChEMBL provenance — tooling now exists, but my lane does not reach it

`scripts/record_tool_snapshot.py` does exactly what my last handoff asked for, and I did
**not** use it. `write_snapshot("chembl", …)` writes to `data/raw/chembl/<date>/`, and
`docs/OWNERSHIP.yaml` assigns `data/raw/chembl/**` to **`agent:alphacognition`**. It is
not in `shared_append_only`, unlike `data/raw/pubmed_esummary/**`,
`data/raw/pubmed_esearch/**`, `data/raw/gwas_catalog_study/**` and
`data/raw/MANIFEST.jsonl`. Writing the snapshot would have been a lane violation, so the
three ChEMBL clinical-development facts stay as provenanced strings in
`max_clinical_phase.as_reported` with `value: null`.

**One-line fix for the orchestrator:** add `data/raw/chembl/**` — and probably
`data/raw/ctgov_v2/**`, currently `agent:red_team`'s — to `shared_append_only` with the
comment `# written by scripts/record_tool_snapshot.py`. The script is the only writer,
snapshots are immutable and manifest-checked, and the append-only pattern already exists
for every other registry. Until then, the new script is unusable by any agent whose
registry of interest sits in someone else's lane, which is most of them.

## 16. Rubric gap, for Sprint 2

`evidence_strength_v1` has no level meaning **"a trial exists, completed, and reported
nothing"**. `reporting_gap_refs` is the structured workaround and it works, but a reader
who consumes only the integer still draws the wrong conclusion from `KL` /
`human_intervention_evidence: 0`. R14 records this as an accepted limitation and defers
the scale to Sprint 2 because changing it forces every atlas to re-grade; noting it here
so it is not lost. The same now applies to `SLC16A1`, whose 0 covers "asked the wrong
question" rather than "did not ask".

## 17. Final state — my files only

```
$ .venv/bin/python graph/validate_graph.py --strict            # filtered to power files
4 findings, 0 errors — all three listed in §12 as deliberate:
  V14  3 warnings  contested claims awaiting red-team audit records
  V22  1 warning   2 registry sources cited by no claim

$ .venv/bin/python scripts/fetch_source_metadata.py --agent power
44/44 sources verified                                          # exit 0

$ .venv/bin/python scripts/check_ownership.py --agent power --paths <40 files>
all 40 path(s) owned as expected                                # exit 0
```

Schema errors in `agent:power` records: **0**. 50 claims, 44 sources, 42 facet gradings,
16 audited zeros, 2 `reporting_gap_refs`, 1 `evidence_gap`, 2 `NO_DETECTED_EFFECT_ON`.

`pytest` not run. No git command run. No dependency installed. Nothing written outside
`agent:power`'s lane.
