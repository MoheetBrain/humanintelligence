# Cognitive Brake Atlas

**Owner:** `agent:brakes` · **Sprint:** 1 · **Run:** `sprint1-brakes-01` · **Date:** 2026-09-17

This atlas maps the **endogenous biological limits** on adult human cognition: brakes on
arousal, excitation, working-memory gain, excitability homeostasis, plasticity, critical
periods, consolidation and translation.

---

## 1. Scope and the one idea that organises it

A brake is a mechanism whose normal operation *limits* a capacity: it raises a threshold,
reduces a gain, shortens a window, closes a period, or arrests a process.

**A brake usually exists for a reason.** Every target dossier here records what the brake
plausibly protects and how releasing it couples to a safety state variable. "Release the
brake" is a hypothesis with a stated cost, never an implied recommendation. Nothing in
this atlas is a protocol, a dose, or advice; see
[`docs/COMPUTATIONAL_ONLY_POLICY.md`](../../docs/COMPUTATIONAL_ONLY_POLICY.md).

The discipline is not decorative. Of the fourteen targets curated here, the evidence
points *away* from brake release in at least four:

| Target | What happened when the brake was reduced |
|--------|------------------------------------------|
| `KCNQ2` / `KCNQ3` | Adult-onset M-current suppression in healthy mice produced spontaneous seizures and **impaired** spatial memory (`CLM:brakes:KCNQ2:001`). |
| `ADORA1` | Conditional receptor deletion blunted the slow-wave rebound and made working memory **fail** under sleep restriction (`CLM:brakes:ADORA1:001`). |
| `RTN4R` | Two independent loss-of-function mouse lines showed **reduced** working memory and mildly impaired spatial cognition (`CLM:brakes:RTN4R:002`, `:003`). |
| `HCN1` | The same deletion that improved learning made adult mice **more seizure-prone** with an excitation–inhibition imbalance (`CLM:brakes:HCN1:005`). |

And in the two cases where an adult manipulation *did* help, it helped conditionally:
reopening the cortical critical period restored vision in amblyopic mice and **degraded
acuity** in healthy ones when the reopened cortex was deprived (`CLM:brakes:OTX2:001`);
reducing α5 inhibition in CA1 improved two memory domains and **impaired context
discrimination** in the same animals (`CLM:brakes:GABRA5:001`–`:003`).

---

## 2. What is here

| Artefact | Path | Count |
|----------|------|-------|
| Source registrations | [`../../evidence/sources/brakes.yaml`](../../evidence/sources/brakes.yaml) | 53, **53 verified**, all cited |
| Claims | [`../../evidence/claims/brakes/`](../../evidence/claims/brakes/) | 57 across 14 targets |
| Target dossiers | [`../../targets/candidates/`](../../targets/candidates/) | 14 |
| Facet assessments | [`assessments/`](assessments/) | 14 × 6 owned facets (73 graded, 11 `not_assessed`) |
| Intervention entities | [`interventions/`](interventions/) | 16 |
| Brake taxonomy | [`brake_taxonomy.yaml`](brake_taxonomy.yaml) | 9 classes, definitional only |
| State-variable annotations | [`state_variable_annotations.yaml`](state_variable_annotations.yaml) | 19, all with claim refs |
| Schema-change request | [`brakes-001.yaml`](../../docs/blackboard/schema_change_requests/brakes-001.yaml) | 4 items, all approved (R2–R5) |
| Builders and self-check | [`../../pipelines/brake_atlas/`](../../pipelines/brake_atlas/) | 3 scripts |

Dossiers and assessments are **generated** from `pipelines/brake_atlas/build_dossiers.py`;
intervention entities from `build_interventions.py`. Edit the builders, not the YAML.
`check_atlas.py` reproduces every quantitative claim made in this README.

---

## 3. Method

### 3.1 How sources were found

Every identifier in this atlas was obtained from a tool response in the curation session.
Nothing was cited from memory, including papers this agent recognised.

* **PubMed** (bio-research MCP server): 26 keyword searches, then
  `get_article_metadata` on every candidate before any claim was written. Searches
  covered, per target: the mechanism, the loss-of-function phenotype, the human
  pharmacology where any exists, and — separately and deliberately — the **null and
  contradicting** literature.
* **PubMed Central** full text: one article (`PMC7497110`) was read in full because the
  distinction between a developmental and an adult manipulation could not be settled from
  its abstract. That reading changed the record: the CA1-restricted α5 deletion is
  progressive from about four weeks of age, so `causal_attribution.basis` is
  `conditional_developmental_knockout` and not `adult_inducible_genetic_perturbation`.
* **ClinicalTrials.gov API v2** (c-trials MCP server): intervention searches for
  `basmisanil OR RO5186582` and `DNL343`, then full records for `NCT02024789`,
  `NCT02953639` and `NCT05842941`.
* **Open Targets Platform GraphQL** (API 26.6.3, data version 26.06): `safetyLiabilities`
  and `tractability` for six targets. Where Open Targets attributed an adverse event to a
  target on the authority of a publication, **that publication was registered as the
  source** rather than citing the database — and the resulting claims carry
  `content_checked: false`, because the underlying table row was not read.
* **ChEMBL** (chembl MCP server): `compound_search` for ten compounds. Six returned an
  identifier and six did not; the six that did not have `chembl_id: null` with
  `identifier_provenance` saying why. No ChEMBL identifier was guessed.

Gene, protein and species identifiers were **not** written by this agent. `identifiers`
is `{}` in every dossier, for HGNC to fill. Species taxids were taken from the
machine-resolved index `data/interim/comparative_species_taxonomy.jsonl`.

### 3.2 How the negative evidence was hunted

The brief required actively searching for failure, on the principle that a brake atlas
which finds only encouraging results has searched badly. Programmes checked, with what
was actually found rather than what was assumed:

| Programme | Found |
|-----------|-------|
| α5-GABA-A negative allosteric modulators in humans | Basmisanil met no cognitive endpoint in a 6-month randomised trial in Down syndrome **despite EEG target engagement** (`CLM:brakes:GABRA5:004`). Three of four registered phase II programmes are recorded as terminated and the completed schizophrenia-cognition study has posted results that were **not retrieved**; those four registry records are registered and verified but carry **no claim** (see §3.4). |
| eIF2B activators / ISR inhibitors in humans | A 249-participant phase 2/3 regimen exists and completed — measuring motor function and survival, with **no cognitive endpoint at all**. Registered and verified, carries **no claim**. Separately, hypomorphic mutations in the eIF2B subunits cause an adult-onset human leukoencephalopathy with executive deficits, mean onset in the thirties (`CLM:brakes:EIF2B_COMPLEX:006`) — the human evidence that this brake is load-bearing. |
| HDAC inhibitors for cognition | A randomised phase 2a trial of an HDAC inhibitor in a CNS indication failed to move **its own pharmacodynamic biomarker**, with exposure not rising proportionally with dose (`CLM:brakes:HDAC2:004`). |
| PDE4 inhibitors and dose-limiting tolerability | Benefit at the **lowest** of three doses; adverse events and no benefit at the highest; and a working-memory null alongside a verbal-memory gain in the same programme (`CLM:brakes:PDE4B:001`–`:003`). |
| KCNQ openers | Retigabine's programme-level urinary-retention liability and black-box warning — which constrain the **opening** direction, recorded explicitly so it is not misread as a brake-release liability (`CLM:brakes:KCNQ2:003`). |
| Adenosine-antagonist cognitive claims | The sceptical human literature: benefit only after 8 h abstinence and not after 4 or 6 h; equal effect from one, two or three doses; **no effect in non-consumers** (`CLM:brakes:ADORA1:004`–`:006`). |
| STEP inhibitors | Two studies, one laboratory, one covalent chemotype, **both deficit-reversal**, no healthy-baseline arm, no human exposure (`CLM:brakes:PTPN5:001`, `:002`). |
| Nogo/NgR1 manipulation in adults | Adult blockade works — for **post-stroke repair, with a motor endpoint**; the cognitive evidence from loss-of-function lines runs the other way (`CLM:brakes:RTN4R:002`–`:004`). |

Result, out of 57 claims: **10 contradicting evidence items**, **5 `null_result` evidence
items** on reported nulls, **5 `NO_DETECTED_EFFECT_ON` null edges**, **6 `clinical_null`
or `preclinical_harm` claims**, and **1 `evidence_gap`** record. All 53 registered sources
are cited by a claim.

### 3.3 What was excluded, and why

* **Preprints.** None cited. `docs/API_RECIPES.md` §7 forbids a preprint carrying a claim
  on its own, and no case arose where a preprint was the only evidence for something
  load-bearing.
* **Reviews as sole support for an effect claim.** Reviews appear only as `qualifies`
  evidence beside a primary study — with **one exception**, `CLM:brakes:RGS14:004`, which
  is an *expression* claim supported by a review alone, graded level 1, and flagged in the
  handoff note as one of the three claims this agent is least confident about.
* **Effect sizes not stated verbatim.** Every number in `effect_size.as_reported` is a
  verbatim string from retrieved text. Where a source gave no number, the field is `null`
  and `metric` is `not_extracted`. No effect size was reconstructed.
* **Facets owned by other agents.** Genetics, comparative, safety-liability-burden,
  developmental-confound-risk and tractability facets are **not** written here, even where
  this atlas holds relevant evidence. Where such evidence exists it is recorded as a
  claim and pointed at the owning agent — for instance `CLM:brakes:HCN1:006`
  (human-versus-rat dendritic coupling) explicitly says the cross-species facets belong to
  `agent:comparative`.
* **Anything resembling a protocol.** No dose, route, regimen or schedule is recommended
  anywhere. Doses appear only inside `as_reported` strings describing what someone else
  already did.

### 3.4 Vocabulary this atlas asked for and now uses

Four gaps were filed as [`brakes-001.yaml`](../../docs/blackboard/schema_change_requests/brakes-001.yaml)
and all four were approved (resolutions R2–R5). The atlas has been re-pointed onto the
new vocabulary rather than left on its workarounds:

* **R2 — gain and timing primitives.** `PRIM:gain_control`, `PRIM:temporal_integration`
  and `PRIM:dendritic_coincidence_detection` now exist. Seven dossiers (GABRA5, HCN1,
  ADORA1, PTPN5, KCNQ2, KCNQ3, GPR158) and five brake classes were re-pointed off the
  borrowed `pattern_separation` and `relational_binding`. The claim that HCN1, KCNQ2 and
  KCNQ3 are *timing and gain* brakes now appears in the primitive lists, not only in
  taxonomy prose.
* **R3 — `SV:safety.dose_limiting_tolerability_margin`.** The PDE4B annotation moved off
  `SV:safety.insomnia_risk`, which covered one of four reported adverse events, and the
  HDAC2 tolerability evidence gained a home instead of an unevidenced coupling to
  proliferative risk. This matters for ranking: PDE4B scores well on adult onset, human
  intervention and dose-response *because* its margin was measured, and the margin is
  narrow.
* **R4 — risk-versus-margin polarity.** Safety variables now declare `polarity`, so the
  six coupling directions this atlas inverted by hand when moving from a seizure
  *threshold* to a seizure *risk* are checkable rather than trusted.
* **R5 — absence of measurement.** See §3.5.
* **R11 — `search_basis` on a zero.** All **20** level-0 facets now carry one. A level-0
  grade means *searched and found nothing*, so there is nothing to cite; the zero is made
  auditable instead by naming the queries run, the scope, and what would have counted as a
  hit. Each also names its scope limit — for the nine `human_intervention_evidence` zeros,
  that PubMed and ClinicalTrials.gov were searched and EudraCT, ISRCTN, WHO ICTRP and
  company disclosures were not. These zeros are load-bearing findings in this atlas, not
  filler: they are the record that the enhancement question has not been asked for
  `PTPN5` and `GPR158`, and that adult manipulation has never been attempted for `RGS14`.

### 3.5 Encoding decisions a reader should know about

* **No `CHANGES_STATE` edge is built from binding data.** Contract rule V16 cannot fire in
  this atlas: every `CHANGES_STATE` claim is `causal_perturbation`, `pharmacodynamic` or
  `clinical_efficacy`, and no claim in the atlas is of type `pharmacology_binding`.
* **Nulls use `NO_DETECTED_EFFECT_ON`**, not a negated effect edge.
* **An endpoint that was never measured is not a failed trial.** This atlas filed the
  schema-change request that produced contract rule V16c and `claim_type: evidence_gap`
  (resolution R5, the amended §4.1). One record now uses it:
  `CLM:brakes:EIF2B_COMPLEX:004` states that the only phase 2/3 human trial of an eIF2B
  activator specified motor-function and mortality outcomes and **no cognitive endpoint**.
  It is graph-inert — it compiles to no biological or intervention edge, carries
  `endpoint_measured: not_measured_in_protocol`, and is deliberately absent from every
  facet's `claim_refs` and `counter_claim_refs`, because an absence of measurement is
  neither support nor refutation.
* **`endpoint_measured` is now set on all 60 evidence items**: 54 `measured`, 8
  `unknown` (curated database rows and narrative reviews, which measure nothing), 1
  `not_measured_in_protocol`, 1 `measured_but_not_reported`.
* **One record could not be made honestly, and became a red-team audit item instead.**
  `CLM:brakes:GABRA5:009` would have recorded that three basmisanil programmes terminated
  and that the completed 214-participant schizophrenia-cognition trial has posted results
  this agent did not retrieve. Its three evidence items are `unknown`, `unknown` and
  `measured`; under V16c that is neither an `evidence_gap` nor a null, so the claim id is
  **left permanently unused**. What could not be determined — whether the two terminated
  studies collected their protocol cognitive endpoints before stopping — and what would
  settle it are written up as an explicit audit item in the
  [handoff](../../docs/blackboard/handoffs/brakes.md) §5. The three registry records were
  retrieved and verified and then **deregistered**, because a registered source that
  nothing cites is either a dropped claim or a missing one (rule V22) and this was the
  former; their identifiers survive in prose so they can be re-retrieved in one call.
* **Null edges say what was tested.** Each of the five `NO_DETECTED_EFFECT_ON` claims
  carries `negated_relation: CHANGES_STATE` and at least one evidence item that is both
  `endpoint_measured: measured` and `evidence_role: null_result`.
* **Animal harm is not labelled clinical.** `CLM:brakes:HCN1:005` records increased
  seizure susceptibility in adult HCN1-null mice as **`preclinical_harm`**, the type this
  atlas asked for and resolution R13 added. Rule V23 now fails a `clinical_harm` claim
  whose evidence is entirely non-human, which is the direction contract P4 blocks.
* **State dependence is named, not implied.** The two `direction: state_dependent` claims
  carry `direction_context` saying what the sign depends on: phosphorylated-eIF2α level
  for the translational brake, and baseline inhibitory tone plus age for α5.
* **Node ids were aligned to the ontology, not invented.** Six state variables and seven
  primitives originally written here were re-pointed onto ids `agent:ontology` declares.
  Two of those re-pointings inverted a sign — seizure *threshold* became seizure *risk*,
  and interference *control* became interference *susceptibility* — and every affected
  `direction` field was inverted with them.

---

## 4. Coverage

Reproduce with `.venv/bin/python pipelines/brake_atlas/check_atlas.py --coverage`.

| Target | Depth | Claims | Contradicting | Null-result | Null/harm claims | Human-relevant claim | Facets graded |
|--------|-------|-------:|--------------:|------------:|-----------------:|:--------------------:|:-------------:|
| GABRA5 | deep | 8 | 2 | 1 | 1 | yes | 6/6 |
| ADORA1 | deep | 7 | 1 | 2 | 2 | yes | 6/6 |
| EIF2B_COMPLEX | deep | 6 | 0 | 0 | 0 | yes | 6/6 |
| HCN1 | deep | 6 | 1 | 0 | 1 | yes | 6/6 |
| HDAC2 | deep | 5 | 1 | 1 | 1 | yes | 5/6 |
| RGS14 | deep | 4 | 0 | 0 | 0 | yes | 5/6 |
| RTN4R | shallow | 4 | 2 | 0 | 0 | yes | 5/6 |
| GPR158 | shallow | 3 | 1 | 0 | 0 | no | 4/6 |
| KCNQ2 | shallow | 3 | 1 | 0 | 0 | yes | 5/6 |
| PDE4B | shallow | 3 | 0 | 1 | 1 | yes | 6/6 |
| EIF2S1 | shallow | 2 | 0 | 0 | 0 | no | 5/6 |
| KCNQ3 | shallow | 2 | 1 | 0 | 0 | no | 4/6 |
| OTX2 | shallow | 2 | 0 | 0 | 0 | no | 5/6 |
| PTPN5 | shallow | 2 | 0 | 0 | 0 | no | 5/6 |
| **Total** | | **57** | **10** | **5** | **6** | **9/14** | **73/84** |

All six deep dossiers meet the ≥4-claim requirement and carry at least one
human-relevant claim. All eight shallow dossiers meet the ≥2-claim requirement.

**Graded facet levels across all 73 graded facets: twenty 0s, sixteen 1s, twenty-five 2s,
twelve 3s, and no 4s.** No facet anywhere in this atlas reaches level 4, which requires
replicated human evidence bearing directly on the facet's proposition and consistent in
direction. That is the single most honest number here.

Only one target in this atlas has randomised human interventional evidence of
above-baseline improvement in healthy adults: **`PDE4B`** — and the drug used is a
pan-PDE4 inhibitor that does not isolate PDE4B, the effect is confined to verbal recall,
and all three studies come from overlapping groups.

---

## 5. What this atlas does not yet cover

**Facets deliberately left `not_assessed` (11).** `transfer_breadth` for eight targets and
`dose_response_knowledge` for three. These are honest gaps: this agent did not review
transfer or graded-manipulation evidence for those targets, and the contract requires
`not_assessed` rather than a zero, because "nobody looked" must not be representable the
same way as "it was tested and failed".

**Specific holes, in rough order of how much they matter:**

1. **The completed basmisanil schizophrenia-cognition trial (`NCT02953639`, n=214) has
   posted results that were not retrieved.** It is the only study located anywhere in this
   atlas that ran a standard multi-domain cognitive battery against an α5 mechanism. It
   could move the GABRA5 human facets in either direction.
2. **No adult caffeine-naive enhancement trial was located.** The decisive design for
   `ADORA1` — rested, non-withdrawn, low-habitual-use adults — does not appear in the
   retrieved literature. The nearest substitute uses children.
3. **No adult-onset perturbation exists at all for `RGS14` or `EIF2S1`**, and none was
   located for `HCN1` with a stated induction age. `RGS14` has no independent replication
   of its behavioural phenotype either.
4. **No subtype-selective evidence for `PDE4B` or `KCNQ3`.** Both dossiers rest on
   evidence about a family or a heteromer. The `KCNQ3` facets are graded one level below
   the identical `KCNQ2` evidence for exactly this reason.
5. **`GPR158` has no resolved sign.** One literature makes it a prefrontal excitability
   brake; another makes it the receptor for a memory-promoting hormone in CA3. This atlas
   records the conflict rather than picking a side.
6. **No human interventional evidence for eleven of fourteen targets.** Only `GABRA5`,
   `PDE4B` and `ADORA1` have any; `EIF2B_COMPLEX` and `RTN4R` have human *genetic*
   evidence only; `HCN1` has one ex-vivo human tissue comparison; the rest have none.
7. **Dose-response is absent or weak for ten of fourteen targets.** Only `ADORA1` and
   `PDE4B` have human dose ladders, and both are non-monotone or flat — which is itself
   the finding.
8. **Cross-species translation is not assessed here.** `CLM:brakes:HCN1:006` records that
   adult human layer-5 dendrites couple more weakly than rat and have lower ion-channel
   density, which caps the translation of the atlas's strongest dendritic result. Grading
   that belongs to `agent:comparative`.
9. **No target here has a measured human state-variable readout.** Three mechanisms in
   this atlas are gated by an internal state — phosphorylated eIF2α level, baseline
   inhibitory tone, withdrawal status — that nobody can currently measure in a living
   human. An intervention that cannot be dosed without that readout is not a control point
   yet, whatever its rank.
