# Cognitive Power Atlas

**Curated by `agent:power`, Sprint 1, 2026-09-17. Branch `sprint-1/foundation`.**

This atlas maps the hypothesis that **adult human neural computation may be
power-limited** — and treats it as a hypothesis with rivals, not as a premise.

The short version of what the evidence says: **on the human evidence retrieved here,
the null hypothesis cannot be rejected.** In healthy, rested, well-fed adults at
normal substrate baseline, randomised trials of the best-studied energetic
intervention in this space show no cognitive effect. Where human benefit appears, it
appears in *low-baseline* or *stressed* states — vegetarians, sleep deprivation, acute
hypoxia — and in *older adults*. That is the signature of a state-dependent
constraint, not of a global supply ceiling in a healthy adult.

---

## 1. Scope

**In scope.** Glucose oxidation; lactate and the astrocyte–neuron lactate shuttle;
MCT1/MCT2/MCT4; ketone bodies; creatine, phosphocreatine and the creatine-kinase
shuttle; ion-pump and receptor costs; myelination economics; sparse coding; biophysical
energy budgets; activity-dependent energy routing; klotho as a systemic modifier.

**In scope but returned nothing usable this sprint** — recorded as gaps, not as
absence of constraint: mitochondrial spare capacity and OXPHOS; neurovascular
coupling; oxygen extraction; reactive oxygen species; thermal burden. Five of the
twelve variables in `state_model/power.yaml` and nine of the ten in
`state_model/efficiency.yaml` therefore remain `unknown` in
`state_variable_annotations.yaml`.

**Out of scope.** Facets owned by other agents (human genetics, safety liability,
developmental confound, tractability, cross-species convergence). This agent graded
only the six facets the contract assigns to the lead atlas.

---

## 2. Search and curation method

1. **Every citation was found through a tool call**, never from memory. Discovery was
   PubMed (`search_articles`, `get_article_metadata`), ClinicalTrials.gov
   (`get_trial_details`) and ChEMBL (`compound_search`). Species taxonomy identifiers
   were resolved live from NCBI E-utilities.
2. **Every claim was written from text actually retrieved** — abstract minimum.
   `extraction.basis` and `extraction.content_checked` are set honestly; exactly one
   claim in this atlas carries `content_checked: false` (`CLM:power:CKB:002`, a
   secondary report) and says so in its `risks`.
3. **Every source was machine-verified against its registry of record** via
   `scripts/fetch_source_metadata.py --agent power`, which compares the transcribed
   title and year against the registry answer and snapshots the raw response.
4. **No effect size appears that is not verbatim in the retrieved text**, and all of
   them live in `effect_size.as_reported`.
5. **Searches were run deliberately for negative and null results**, not only for
   positives. Ten claims carry contradicting or null evidence, and seventeen qualify.
6. **Every one of the 16 level-0 facets carries a `search_basis`** naming the queries
   run, the scope, and what would have counted as a hit (contract §5.2). A zero in this
   atlas is an audited finding, not a shrug — and one of them
   (`KL` / `human_intervention_evidence`) records a human trial that the search *did*
   return and explains, in the record, why it still grades 0.
7. **Every one of the 51 evidence items carries `endpoint_measured`**, so an endpoint
   nobody measured is never mistaken for an endpoint that was measured and came back
   null: 43 `measured`, 6 `not_measured_in_protocol` (the biophysical models and the two
   critical reviews — nothing was measured in those, which is the point), 1
   `measured_but_not_reported` (a terminated trial with no posted results), 1 `unknown`.
8. **The two genuine nulls use the `NO_DETECTED_EFFECT_ON` relation** with
   `negated_relation` naming what was tested and found absent, so a performed,
   reported null compiles into the graph instead of vanishing.

### Deliberate exclusions
* **No doses, regimens, routes, products or sourcing** appear anywhere in this atlas,
  including where the source abstract reported them (`docs/COMPUTATIONAL_ONLY_POLICY.md`).
* **No probabilities and no scores.** Ordinal levels only.
* Preprints were not used to carry any claim.

---

## 3. Coverage

### 3.1 Targets

| Target | Depth | Claims | Facets graded | Human evidence present? | Strongest human record |
|---|---|---|---|---|---|
| `SLC6A8` | deep | 6 | 6/6 (all assessed) | **yes** — monogenic disorder + registry record; substrate-level RCTs | 50-participant natural-history cohort (`CLM:power:SLC6A8:001`) |
| `CKB` | deep | 6 | 6/6 (all assessed) | **indirect only** — 31P-MRS pool associations, not CKB-specific | conflicting 31P-MRS results (`CLM:power:CKB:005`, `:006`) |
| `SLC16A7` (MCT2) | deep | 5 | 6/6 (all assessed) | **none** | — |
| `HCAR1` | deep | 6 | 6/6 (all assessed) | **none** | — |
| `SLC16A1` (MCT1) | shallow | 5 | 5/6 (1 `not_assessed`) | **yes** — NEJM rare-variant series, case series, and a phase 1 MCT1-inhibitor trial | MCT1 deficiency (`CLM:power:SLC16A1:003`); evidence gap (`CLM:power:SLC16A1:005`) |
| `SLC16A3` (MCT4) | shallow | 3 | 5/6 (1 `not_assessed`) | **none** | — |
| `KL` (klotho) | shallow | 4 | 6/6 (all assessed) | **yes** — cohort associations *and* a contradicting prospective cohort | dementia-incidence cohort (`CLM:power:KL:003`) |

A trial-registry search added in the second round found a completed human klotho
intervention with cognitive secondary endpoints (`SRC:NCT:NCT07285629`) that has posted
no results, is uncontrolled, has fourteen participants, and co-administers follistatin
so klotho's own contribution is unidentifiable. It licenses no claim and is recorded in
the `search_basis` of that facet rather than being graded as evidence.

### 3.2 Cross-target topics

| Topic file | Claims | Role in the atlas |
|---|---|---|
| `astrocyte_neuron_lactate_shuttle.yaml` | 5 | The contested mechanism. Founding result and published critique both registered, with opposite `evidence_role`. |
| `brain_energy_budget.yaml` | 5 | All model outputs, labelled as such. Includes the result that myelination need not save energy. |
| `creatine_supplementation_human.yaml` | 5 | The human evidence base, and the state-dependence finding. |

Two trials are recorded as gaps rather than as evidence, and they are gaps of different
kinds. `SRC:NCT:NCT01791595` gave an MCT1 inhibitor to 53 people, posted results, and
**never measured cognition** — an *evidence gap* (`CLM:power:SLC16A1:005`, graph-inert).
`SRC:NCT:NCT01455376` measured neurocognitive function as its **primary** outcome and
**never posted results** — a *reporting gap* (`reporting_gap_refs` on the HCAR1 facet).
A bare `level: 0` had been covering both, plus genuine absence of enquiry.

**Totals: 44 sources registered, 44 verified. 50 claims. 42 facet gradings across 7
targets (40 `assessed`, 2 `not_assessed`), of which 16 are honest zeros carrying a
`search_basis`.**

### 3.3 Facet levels at a glance

`level` grades supporting evidence; `counter_level` grades contradicting evidence.
They are independent: `0/0` means "nobody looked", `0/3` means "it was tested and it
failed". Conflating those two is the failure mode the contract's two-column design
exists to prevent.

| Target | mechanistic | adult-onset | above-baseline | transfer | dose-response | human intervention |
|---|---|---|---|---|---|---|
| `SLC6A8` | 3 / 2 | **0 / 2** | 1 / 3 | 1 / 2 | 1 / 0 | 2 / 3 |
| `CKB` | 2 / 2 | 0 / 0 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 1 |
| `SLC16A7` | 3 / 2 | 3 / 0 | 0 / 1 | 1 / 0 | 0 / 0 | **0 / 0** |
| `HCAR1` | 3 / 1 | 3 / 1 | **2 / 3** | 1 / 2 | 1 / 0 | **0 / 0** |
| `SLC16A1` | 2 / 2 | 2 / 0 | 0 / 2 | — | 1 / 0 | 0 / 0 |
| `SLC16A3` | 2 / 2 | 2 / 0 | 0 / 0 | — | 0 / 0 | **0 / 0** |
| `KL` | 3 / 0 | 3 / 0 | **2 / 3** | 2 / 1 | 2 / 0 | 0 / 0 |

Three patterns are worth reading off this table directly:

* **`above_baseline_enhancement` never exceeds 2, and where it reaches 2 the
  counter-level is 3.** Both times (`HCAR1`, `KL`) the contradicting evidence is
  stronger than the supporting evidence.
* **`human_intervention_evidence` is 0 for five of seven targets.** The two non-zero
  entries are `SLC6A8` at level 2 — and even that intervenes on the *substrate*, not
  the gene — and `CKB` at 0 with a counter-level of 1.
* **`SLC6A8` has the atlas's only `0 / 2` on adult-onset perturbation**: an
  adult-onset experiment exists, was designed to answer exactly this question, and
  came back negative.

---

## 4. The two analytic deliverables

* **`competing_models.yaml`** — six falsifiable models (H0 no limit, H1 global supply,
  H2 local/transient mismatch, H3 efficiency, H4 thermal/ROS, H5 allocation), each
  with discriminating predictions, computational-only tests on already-collected
  public data, claim-referenced evidence pointers, and `status: untested`. It states
  plainly that H0 is currently the most parsimonious reading of the human evidence,
  that H1 is *weakened* by it, and that H4 is unaddressed in either direction.
* **`metrics.yaml`** — `cognitive_power_reserve` and `neural_efficiency` as
  **theoretical constructs**: definitions, `units: null`, candidate proxies with
  modality and honest measurability grade, a per-proxy identifiability problem, an
  explicit "currently not measurable" list, and a `do_not_do` list. No formula is
  presented as validated and no constant appears anywhere in the file.

---

## 5. What this atlas cannot currently answer

Stated plainly, because a coverage gap recorded as a gap is a result and a coverage
gap left implicit is a defect.

1. **Whether a healthy rested adult human is power-limited at all.** H0 cannot be
   rejected and H0 cannot be confirmed. No experiment in this atlas measures energetic
   headroom in a working human brain, because — per `metrics.yaml` — the *attainable*
   term of the reserve construct has never been measured in a person.
2. **Whether the astrocyte–neuron lactate shuttle operates as described.** Both the
   founding causal work and a published critique arguing the shuttle was never
   actually measured are registered here, neither withdrawn. `CLM:power:anls:001` has
   `status: contested`. This atlas does not treat the shuttle as settled physiology.
3. **Anything about MCT2, MCT4 or HCAR1 in humans.** Zero human records for all three.
   The target with the best mechanistic evidence in the atlas (`SLC16A7`) has no human
   data of any kind.
4. **Whether raising any of these variables above normal does anything.** Not one
   experiment retrieved, in any species, raises transport capacity, kinase activity or
   receptor expression above wild type. The entire evidence base is loss-of-function
   plus substrate loading.
5. **Thermal and oxidative limits (H4).** No claim, in either direction.
6. **Neurovascular coupling and local supply–demand matching (H2).** No claim — which
   is awkward, because H2 is among the hypotheses most compatible with the observed
   human state-dependence.
7. **Dose–response for anything.** The only non-monotonic result in the atlas
   (`CLM:power:KL:004`, low klotho dose effective, high dose not) rests on two dose
   levels in one study.
8. **Transfer breadth.** No study anywhere in this atlas measures far transfer or an
   untrained real-world endpoint.
9. **Whether klotho belongs in a *power* atlas.** Its reported mechanism is synaptic
   and glutamatergic, not metabolic. Its presence here is inherited from the seed
   registry, and `targets/candidates/KL.yaml` says so.
10. **What the one human klotho intervention found.** `SRC:NCT:NCT07285629` completed and
    measured five NIH Toolbox cognitive outcomes; no results are posted. Until they are,
    the most translationally advanced target in this atlas has a registered human
    cognitive read-out that nobody can see.
11. **Whether MCT1 inhibition affects human cognition.** A phase 1 trial dosed 53 people
    with an MCT1 inhibitor and measured no cognitive endpoint at all. The question has
    not been answered because it was not asked — and its dose-limiting toxicities were
    haematological, cardiac and ophthalmic, which `agent:red_team` should assess.

---

## 6. Files

```
atlases/power/
  README.md                          this file
  competing_models.yaml              H0–H5, falsifiable, untested
  metrics.yaml                       two theoretical constructs, no validated formulae
  state_variable_annotations.yaml    6 of 22 variables claim-annotated; 16 `unknown`
  assessments/{7 targets}.yaml       6 owned facets each, evidence vs counter-evidence
  interventions/{8 entities}.yaml    identifiers from tools only; `null` where none exists
evidence/sources/power.yaml          41 sources, 41 verified
evidence/claims/power/*.yaml         49 claims across 7 targets + 3 topics
targets/candidates/{7 targets}.yaml  dossiers; `identifiers: {}` for HGNC to fill
docs/blackboard/schema_change_requests/power-001.yaml
docs/blackboard/handoffs/power.md
```

## 7. How to attack this atlas

Start with `docs/blackboard/handoffs/power.md` §"For the red team", which names the
specific over-reaches this agent is most likely to have committed, in priority order.
The two strongest candidates are the interpretive leap from a rodent motor-endurance
endpoint to `SV:cognition.sustained_attention_stability` in `CLM:power:HCAR1:004`,
and the reading of a non-cognitive human presentation as evidence against a cognitive
bottleneck in `CLM:power:SLC16A1:003`.
