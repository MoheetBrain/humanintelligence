# Handoff — `agent:brakes` (Cognitive Brake Atlas)

**Run:** `sprint1-brakes-01` · **Branch:** `sprint-1/foundation` · **Date:** 2026-09-17
**Revision:** post-resolution. Resolutions R2–R5 (this agent's `brakes-001`) were approved
and applied; §5 and §7 record what changed and §11 what remains.

Full method, coverage table and gap list: [`atlases/brakes/README.md`](../../../atlases/brakes/README.md).
This note reports numbers, commands and uncertainty.

---

## 1. Sources: 53 registered, **53/53 verified**, 0 failures, 0 uncited

`evidence/sources/brakes.yaml` — 50 PubMed records, 6 ClinicalTrials.gov records.

* **No `title_mismatch`, no `not_found`, no `year_mismatch`, no `retracted`.**
* Lowest title similarity across all 56: **0.9931** (`SRC:PMID:41881181`); threshold is 0.90.
* No source was repaired by guessing. Two searches returned zero results and were left as
  zero (`alpha5IA inverse agonist humans alcohol`, `human cortical pyramidal neuron
  dendrite h-current species comparison`); both gaps are recorded as facet limitations
  rather than filled.
* **Every registered source is now cited** (rule V22 clear). Of the five that were not:
  `SRC:NCT:NCT05842941` is cited by the `evidence_gap` claim; `SRC:PMID:25751008`
  (Soh & Lynch 2015) was cited from `CLM:brakes:GABRA5:006`, because it asserts the same
  paradox that claim records — cognitive impairment reversed by *both* positive and
  negative α5 modulation — and adds that no α5-selective compound has been marketed,
  attributing that to unsuccessful trials and human toxicity, which is recorded as a
  review-level assertion this agent did not trace to individual programmes.
* **Three registrations were removed, not cited: a dropped claim, not a missing one.**
  `SRC:NCT:NCT02484703`, `SRC:NCT:NCT05307679` and `SRC:NCT:NCT02953639` were retrieved
  and machine-verified on 2026-09-17 and then deregistered, because the claim that would
  have cited them (`CLM:brakes:GABRA5:009`) could not be written honestly — see the audit
  item in §5. The identifiers, their enrolments and their statuses are preserved in the
  GABRA5 facet prose, in the README and in §5, so nothing is lost and the red team can
  re-retrieve all three in one `get_trial_details` call. A note at the removal site in
  `evidence/sources/brakes.yaml` records the same thing, so the deletion is not silent.

## 2. Claims: 57 across 14 targets

| Target | Depth | Claims | Contradicting evidence items | null/harm claims | Human-relevant claim |
|--------|-------|-------:|-----------------------------:|-----------------:|:--------------------:|
| GABRA5 | deep | 8 | 2 | 1 | yes (interventional) |
| ADORA1 | deep | 7 | 1 | 2 | yes (interventional) |
| EIF2B_COMPLEX | deep | 6 | 0 | 0 | yes (genetic) |
| HCN1 | deep | 6 | 1 | 1 | yes (observational, ex vivo) |
| HDAC2 | deep | 5 | 1 | 1 | yes (interventional) |
| RGS14 | deep | 4 | 0 | 0 | yes (expression only) |
| RTN4R | shallow | 4 | 2 | 0 | yes (genetic) |
| GPR158 | shallow | 3 | 1 | 0 | no |
| KCNQ2 | shallow | 3 | 1 | 0 | yes (interventional) |
| PDE4B | shallow | 3 | 0 | 1 | yes (interventional) |
| EIF2S1 | shallow | 2 | 0 | 0 | no |
| KCNQ3 | shallow | 2 | 1 | 0 | no |
| OTX2 | shallow | 2 | 0 | 0 | no |
| PTPN5 | shallow | 2 | 0 | 0 | no |

All six deep dossiers meet ≥4 claims **and** carry a human-relevant claim.
All eight shallow dossiers meet ≥2 claims.

**Negative and contradicting evidence.** 10 evidence items carry
`evidence_role: contradicts` and 5 carry `evidence_role: null_result` — the five reported
nulls were retagged from `contradicts` to `null_result`, which is the precise label for a
study that ran and found nothing. 5 claims use the `NO_DETECTED_EFFECT_ON` null edge, each
with `negated_relation: CHANGES_STATE`. 6 claims are `clinical_null` (5) or `clinical_harm`
(1), and 1 is an `evidence_gap`. By `claim_type`: causal_perturbation 23, pharmacodynamic 8,
mechanistic 6, clinical_null 5, clinical_efficacy 4, safety 4, expression 4,
preclinical_harm 1, comparative_evolutionary 1, evidence_gap 1. **No claim is
`pharmacology_binding`**, so rule V16 cannot be tripped by a binding record here.

**`endpoint_measured` (R5) is set on all 60 evidence items**: 54 `measured`, 8 `unknown`
(curated database rows and narrative reviews, which measure nothing), 1
`not_measured_in_protocol`, 1 `measured_but_not_reported`. All five `NO_DETECTED_EFFECT_ON`
claims pass V16c: each has an item that is both `measured` and a null/contradicting role.

**Extraction honesty.** 3 evidence items read from full text, 54 from abstract, 1 from a
registry record, 2 from a database record. **Two claims carry
`content_checked: false`** and should be downgraded automatically:
`CLM:brakes:GABRA5:008` and `CLM:brakes:ADORA1:007`. Both are safety mappings read from
the Open Targets Platform response rather than from the source publication's own table.

**Enhancement accounting.** Of 56 claims, only 11 assert
`supra_normal: enhancement_above_healthy_baseline`; 16 say
`no_enhancement_observed`, 6 `rescue_only`, 5 `contradicted`, 18 `untested`. Ten of the
eleven enhancement claims are rodent; the eleventh pair is `PDE4B` in healthy human
adults with a pan-PDE4 inhibitor that does not isolate PDE4B.

## 3. Other artefacts

14 target dossiers · 14 facet assessments (6 owned facets each) · 16 intervention
entities · 9-class brake taxonomy · 19 state-variable annotations, every one with claim
refs · 3 builder/check scripts in `pipelines/brake_atlas/`.

## 4. Facets: 73/84 graded, 11 `not_assessed`, 20 zeros with a `search_basis`

**Level distribution across the 73 graded facets: 0 × 20, 1 × 16, 2 × 25, 3 × 12, 4 × 0.**
No facet in this atlas reaches level 4. Level 4 requires replicated human evidence bearing
directly on the facet's proposition and consistent in direction, and nothing here meets
that bar — not even `PDE4B`, whose three human studies share authorship.


`transfer_breadth` for EIF2S1, GPR158, HDAC2, KCNQ2, KCNQ3, OTX2, PTPN5, RTN4R (8) and
`dose_response_knowledge` for GPR158, KCNQ3, RGS14 (3).

**Why, in each case:** this agent did not review transfer or graded-manipulation evidence
for those targets, so per the contract they are `not_assessed` with `level: null` rather
than graded `0`. "Nobody looked" and "it was tested and failed" must not be
representable the same way. Where a search *was* run and found nothing, the facet is
graded **0** with a rationale saying so — that applies to
`adult_onset_perturbation` for RGS14 and EIF2S1, `dose_response_knowledge` for HCN1,
OTX2 and RTN4R, `above_baseline_enhancement` for KCNQ2, KCNQ3, OTX2, PTPN5, RTN4R and
GPR158, and `human_intervention_evidence` for seven targets.

No facet owned by another agent was written. Each assessment lists the nine
non-owned facets explicitly so the omission is visible rather than accidental.

## 5. What resolutions R2–R5 changed in this atlas

All four items of `brakes-001` were approved. The atlas is re-pointed onto the new
vocabulary rather than left on its workarounds. Applied changes:

**R5 — absence of measurement (the consequential one).**
`CLM:brakes:EIF2B_COMPLEX:004` is restored as **`claim_type: evidence_gap`**. It records
that the only phase 2/3 human trial of an eIF2B activator specified motor-function and
mortality outcomes and no cognitive endpoint. It is graph-inert, carries
`endpoint_measured: not_measured_in_protocol`, and uses the evidence-layer relation
`ABOUT` (`CLM:… ABOUT PHENO:clinical_cognitive_composite`) because no biological or
intervention relation admits `evidence_gap` and `MODULATES` into a phenotype is
efficacy-grade under V16. It appears in **no** facet's `claim_refs` or
`counter_claim_refs`.

**`CLM:brakes:GABRA5:009` could not be made honestly, and remains unused.** The
coordinator asked for both claims to be retyped, and this one cannot be. Its three
evidence items are `unknown`, `unknown`, `measured`. V16c requires every evidence item of
an `evidence_gap` to report an unmeasured endpoint, so the claim is neither an
`evidence_gap` nor a null, and setting those items to `not_measured_in_protocol` to make it
validate would have asserted something this agent does not know. The claim id is left
permanently unused.

> ### AUDIT ITEM FOR `agent:red_team` — basmisanil programme attrition
>
> **What could not be determined.** Whether the two terminated basmisanil phase II
> studies — `NCT02484703` (paediatric Down syndrome, n=45, terminated) and `NCT05307679`
> (Dup15q, n=7, terminated) — administered and recorded their protocol-specified cognitive
> endpoints before stopping. Their registry records state status and enrolment but give no
> `whyStopped` text and no results, so "endpoint measured" is genuinely `unknown` rather
> than `not_measured_in_protocol` or `measured`. Separately, `NCT02953639` (schizophrenia
> cognition, n=214, MATRICS Consensus Cognitive Battery, completed) **has results posted on
> the registry** and this agent did not retrieve them; that is an extraction limit of this
> atlas, not a property of the evidence.
>
> **What would settle it.** For the two terminated studies: the `resultsSection` of each
> ClinicalTrials.gov v2 record, or the sponsor's own disclosure, showing whether any
> cognitive outcome was collected. For the completed study: retrieving its posted
> `resultsSection` and reading the MCCB neurocognitive composite change from baseline to
> week 24. That third one is the single largest unresolved item in the whole atlas — it is
> the only study located anywhere here that ran a standard multi-domain cognitive battery
> against an α5 mechanism, and it could move
> `GABRA5.human_intervention_evidence` in either direction.
>
> **Why it is not a claim.** A terminated trial is not a reported null and an unread result
> is not a negative one. Encoding either as a claim would put a finding about *this agent's
> search* into the layer where every consumer reads records as findings about biology.

**Audit of the other null-flavoured claims (requested).** All five remaining
`NO_DETECTED_EFFECT_ON` claims are genuine tested nulls, not unmeasured endpoints:
`ADORA1:004`, `ADORA1:005`, `GABRA5:004`, `HDAC2:004`, `PDE4B:003`. Each has an evidence
item that is both `endpoint_measured: measured` and `evidence_role: null_result`. None
required retyping.

**Facet levels changed by this work — one, downward.**
`EIF2B_COMPLEX.human_intervention_evidence` went **level 1 → 0**. It previously rested on
the DNL343 trial as weak supporting evidence; now that the trial is correctly recorded as
an unmeasured endpoint, nothing supports the facet and the honest grade is "searched,
nothing found". No `counter_level` anywhere drew on either gap claim, so no counter_level
came down; `GABRA5.human_intervention_evidence` keeps `counter_level: 3` carried entirely
by the CLEMATIS trial (`CLM:brakes:GABRA5:004`) on its own, and its `counter_rationale`
now says so explicitly. One level moved **up** for an unrelated reason:
`EIF2B_COMPLEX.mechanistic_causal_perturbation` counter_level 1 → 2, when the human
genetic vanishing-white-matter claim (`CLM:brakes:EIF2B_COMPLEX:006`) was added.

**R2 — gain and timing primitives.** Seven dossiers re-pointed off the borrowed terms
(GABRA5, HCN1, ADORA1, PTPN5, KCNQ2, KCNQ3, GPR158) and five brake classes in the
taxonomy. `PRIM:gain_control` is now used 12 times, `PRIM:temporal_integration` 5,
`PRIM:dendritic_coincidence_detection` 2. The atlas's claim that HCN1, KCNQ2 and KCNQ3
are timing and gain brakes is now in the primitive lists, not only in prose.

**R3 — `SV:safety.dose_limiting_tolerability_margin`.** The PDE4B annotation moved off
`SV:safety.insomnia_risk` (which covered one of four reported adverse events) onto the
margin variable, `direction: inverse`. The HDAC2 annotation gained an evidenced coupling
to the same variable citing `CLM:brakes:HDAC2:005`, replacing the unevidenced coupling to
`SV:safety.proliferative_risk` that had been removed earlier. The standalone
`SV:safety.insomnia_risk` annotation became the margin annotation, citing three claims.
**For `agent:integration`:** do not read a measured margin as a favourable safety
profile. PDE4B scores well on adult onset, human intervention and dose-response precisely
because its margin was measured, and the margin is narrow.

**R5 also — `structural_biology`.** `CLM:brakes:EIF2B_COMPLEX:002` moved off
`narrative_review`, which described what was read rather than what was done.

**Other validator-driven fixes in the same pass.** `negated_relation: CHANGES_STATE`
added to all five null edges (rule V16b-sym: a null edge must say what was tested).
`direction_context` added to the two `direction: state_dependent` claims (rule V-DIR):
phosphorylated-eIF2α concentration for the translational brake, baseline inhibitory tone
and age for α5. Two further claim directions were moved from `unclear`/`bidirectional` to
`state_dependent` now that the value is legal.

**R7 then R11 — how the twenty level-0 facets are now justified.** R7 (filed by
`agent:integration`) briefly required every assessed facet to cite `claim_refs` or
`source_refs`. Twenty facets graded **level 0** had neither. They were **not** downgraded
to `not_assessed` — that would have destroyed the §5.3 distinction between "searched,
nothing found" and "nobody looked" — so they were given *boundary* claim refs naming what
had been found instead. **R11 then superseded that**, and correctly: `claim_refs` is
required only at `level >= 1`, because a citation for the absence of evidence is
incoherent. All twenty level-0 facets now carry **`search_basis`** instead, naming the
queries actually run, the scope, and what would have counted as a hit — including the
scope limit that for the nine `human_intervention_evidence` zeros only PubMed and
ClinicalTrials.gov were searched, not EudraCT, ISRCTN, WHO ICTRP or company disclosures.
Their `claim_refs` are now empty and the "what was found instead" sentence stayed in the
`rationale`. **No level changed at any point in this sequence**; the zeros became
auditable.

**Coordinator item 3 applied.** Two dossier state variables moved from `direction:
unclear` to `state_dependent`, because the dependency is known rather than unknown:
`HCN1` dendritic temporal summation (depends on disease state — the h-current is
chronically elevated in the fragile-X model) and `GPR158` cAMP signalling capacity
(depends on brain region — prefrontal suppression versus CA3 hormone transduction). Each
is now licensed by a `causal_perturbation` claim ref as rule V16 requires, and the context
sentence lives in the dossier's `open_questions`, because `direction_context` is a claim
field and the dossier state-variable object has no such key.

**Coordinator item 4 not needed.** `attributes` was offered for domain metadata the schema
does not model. This atlas has one such field, `brake_class` on each dossier, and the
target schema already declares it, so nothing was moved.

## 6. Exact commands run, with real results

Final run, after resolutions R2–R5 and R7 were applied and `agent:ontology` had landed the
vocabulary:

```
$ .venv/bin/python scripts/fetch_source_metadata.py --agent brakes
brakes: 56/56 verified -> data/interim/source_verification/brakes.jsonl
56/56 sources verified                                                  [exit 0]
No title_mismatch, not_found, year_mismatch or retracted. Lowest title
similarity across all 56: 0.9931 (SRC:PMID:41881181); threshold is 0.90.

$ .venv/bin/python scripts/check_ownership.py --agent brakes --paths <67 own paths>
all 67 path(s) owned as expected                                        [exit 0]
Run with --paths as instructed. Without it the script classifies every other
agent's uncommitted file in the shared tree and exits non-zero on their paths.

$ .venv/bin/python graph/validate_graph.py --strict
TOTAL: 378 violation(s) across 8 rule(s) — 342 error, 36 warning  [exit 1, FAIL]
Violations on brakes-owned paths: 0.
Verified by filtering --json output to atlases/brakes, evidence/{claims,sources}/brakes,
pipelines/brake_atlas and the 14 owned targets/candidates files. Rules firing repo-wide:
V1, V3, V9, V14, V15, V16, V16b-sym, V16c — all in other agents' lanes. NOT MINE TO FIX;
reported so the orchestrator sees them.

$ .venv/bin/python pipelines/brake_atlas/build_dossiers.py
validated 14 targets against 57 registered claims
wrote 14 dossiers and 14 assessments                                    [exit 0]

$ .venv/bin/python pipelines/brake_atlas/build_interventions.py
wrote 16 intervention entities                                          [exit 0]

$ .venv/bin/python pipelines/brake_atlas/check_atlas.py --coverage
PASS: 0 problem(s)                                                      [exit 0]
totals: claims=57 contradicting_evidence_items=10 null_result_evidence_items=5
        NO_DETECTED_EFFECT_ON_claims=5 evidence_gap_claims=1
        null_or_harm_claims=6 targets_with_human_claim=9/14 facets_graded=73/84
```

**JSON Schema validation** against `schemas/` as published by `agent:ontology`, run inside
`check_atlas.py`: sources 56/0 errors, claims 57/0, targets 14/0, assessments 14/0,
interventions 16/0, state-variable annotations 19/0. **Total 0.**

`check_atlas.py` also enforces locally, ahead of the graph validator: V16c, the ban on
citing an `evidence_gap` claim in any facet, the presence of `endpoint_measured` on every
evidence item, declared-depth satisfaction, facet ownership, and that every `SV:` and
`PRIM:` id used is declared by `agent:ontology`.

**`pytest` was NOT run**, per instruction. No test result is claimed anywhere in this
atlas.

## 7. What the validator and schemas changed in this atlas

The ontology and schemas appeared mid-run and were applied rather than worked around.
Recorded here because the red team should know the records were revised, not authored
once:

* **7 predicates** re-pointed. `ANTAGONISES`, `NEGATIVELY_MODULATES` and `INHIBITS` take a
  molecular object, not a state variable or phenotype; 14 claims were moved to
  `CHANGES_STATE` (effects) or `NO_DETECTED_EFFECT_ON` (nulls). One safety claim
  (`CLM:brakes:HDAC2:005`) was re-pointed to `INCREASES_RISK → AE:headache`, which is what
  that study actually establishes.
* **6 state variables and 7 primitives** renamed onto ids `agent:ontology` declares. **Two
  renames inverted a sign** — seizure *threshold* → seizure *risk*, interference *control*
  → interference *susceptibility* — and every affected `direction` field was inverted with
  them. That inversion is the most likely place for a residual error in this atlas; see §9.
* **3 dossier state-variable directions** set to `unclear` because their only cited claims
  were `expression` or `mechanistic`, which rule V16 says cannot license a direction
  (`HCN1` dendritic summation, `RGS14` critical-period permissiveness, `GPR158` cAMP
  capacity).
* **4 unevidenced safety couplings** deleted from the state-variable annotations. The
  validator requires every coupling to cite a claim; the plausible-but-unmeasured
  couplings now appear in `desirability_note` prose instead.
* **Two YAML boolean traps** caught: `locus_to_gene_resolved: no` and `: yes` parse as
  booleans. Both are now quoted. Worth other agents checking.
* **`CLM:brakes:HCN1:005` retyped `clinical_harm` → `preclinical_harm`** (R13, rule V23).
  The other four safety-flavoured claims were checked for the same shape and are correct:
  `HDAC2:005` and `KCNQ2:003` rest on human trial data, and `GABRA5:008` / `ADORA1:007` are
  `safety` rather than a clinical label, with `human_relevance: other_species_only`
  recording that the underlying safety-pharmacology assays are non-human.
* **Intervention records rewritten to the canonical shape.** ChEMBL clinical-development
  facts now sit in `max_clinical_phase: {value, as_reported, source}` and the integer
  `first_approval_year`, not in ad-hoc fields; the ad-hoc `approval` object is gone and its
  verbatim string moved into a structured `notes` array. Rule V9 exempts those two numeric
  slots only because `max_clinical_phase.source` names where they came from —
  `database_source_id` was **not** used, because it must resolve to a registered source and
  a `SRC:DB:chembl:34` registration could not be verified: `fetch_source_metadata.py`
  verifies a database release against an immutable snapshot in `data/raw/`, and the ChEMBL
  MCP tools write no snapshot. Registering an unverifiable source to fill a field would
  break V6, which matters more. All 16 records also gained `role_in_atlas` and
  `scope_limits`, and five gained `direction_warning` — the retigabine record now states in
  a required field that it acts in the *opposite* direction to brake release.

## 8. Notes for specific agents

**`agent:ontology`** — one small inconsistency to close: `graph/validate_graph.py` accepts
`preclinical_harm` on `INCREASES_RISK`, but `ontology/edges.yaml` does not list it in that
relation's `allowed_claim_types`, so a naive reader of the ontology would reject a claim the
validator passes. `pipelines/brake_atlas/check_atlas.py` mirrors the validator with a
comment marking the workaround for removal. Separately,
[`schema_change_requests/brakes-001.yaml`](../schema_change_requests/brakes-001.yaml),
4 non-blocking items: (1) primitives for gain control, temporal integration and dendritic
coincidence detection; (2) a generic dose-limiting-tolerability safety variable; (3) a
one-line note that safety variables are *risks* unless their id ends `_margin`, which
would have saved this agent a sign inversion; (4) a structural-biology `design` term and a
way to say "endpoint not measured" that is distinct from a tested null.

**`agent:comparative`** — `CLM:brakes:HCN1:006` records direct recordings from adult human
layer-5 dendrites showing weaker dendrite-to-soma coupling and lower ion-channel density
than rat. It caps the translation of this atlas's strongest dendritic result and the
cross-species facets are yours, not graded here.

**`agent:integration`** — three mechanisms in this atlas are gated by an internal state
nobody can currently measure in a living human: phosphorylated eIF2α level
(`EIF2B_COMPLEX`, `EIF2S1`), baseline inhibitory tone (`GABRA5`), withdrawal status
(`ADORA1`). A target whose useful direction depends on an unmeasurable state is not a
control point yet, whatever its rank. Also: `PDE4B` scores well on adult onset, human
intervention and dose-response, but the `mechanistic_causal_perturbation` facet is
deliberately **level 1** because no PDE4B-selective evidence was reviewed. Do not let the
human facets carry a gene-level conclusion the mechanism facet refuses.

**`agent:red_team`** — see §9 and §10.

## 9. The three claims I am least confident about

1. **`CLM:brakes:GABRA5:008`** (and its twin `CLM:brakes:ADORA1:007`). Target-to-adverse-event
   mappings read from the Open Targets Platform response, attributed to a curation review
   whose relevant table row **was not read**. Both carry `content_checked: false` and
   `uncertainty.level: 1`. They exist because a brake atlas that omits seizure and cardiac
   liability is worse than one that records them weakly, but they are the weakest records
   here and should be downgraded or replaced with the primary rows.
2. **`CLM:brakes:RGS14:004`** — the only claim in the atlas supported by a **review
   alone**, with no primary source beside it. It is an expression claim (`level: 1`,
   `evidence_role: qualifies`) and it is also the *only* human-relevant evidence for
   RGS14, which makes that dossier's human column look better than it is.
3. **`CLM:brakes:HCN1:005`** — *resolved, and no longer on this list for its original
   reason.* It was typed `clinical_harm` because the enum had no animal-harm type; this
   atlas flagged the forced label, resolution R13 added `claim_type: preclinical_harm`, and
   the claim is now retyped. Rule V23 enforces it. The residual uncertainty is only the
   ordinary one: a single study, a provoked seizure model, and a germline null.

Runner-up, and the one most likely to be *wrong in direction* rather than weak: the
inverted sign convention described in §7. Every claim, dossier field and annotation
touching `SV:safety.seizure_risk` or `SV:workspace.interference_susceptibility` was
hand-inverted from a threshold/control framing. Resolution R4 now has safety variables
declare `polarity`, so this is checkable rather than trusted — but the inversions
themselves were done by hand before that landed and deserve an independent pass.

## 10. What the red team should attack first

1. **The `evidence_gap` record and the unused id.** `CLM:brakes:EIF2B_COMPLEX:004` is the
   atlas's one `evidence_gap`; confirm it appears in no facet's `claim_refs` or
   `counter_claim_refs` and that nothing downstream reads it as a null.
   `CLM:brakes:GABRA5:009` is permanently unused — see §5 for why it could not be written
   honestly — and its content survives only as facet prose. Confirm "not measured" has not
   leaked back anywhere as a null result, and that the five uncited-but-registered sources
   are not being counted as support.
2. **The sign inversions** on `SV:safety.seizure_risk` and
   `SV:workspace.interference_susceptibility`. Six coupling directions and several
   dossier fields were inverted by hand.
3. **`CLM:brakes:GABRA5:001`–`:003`**, which come from one paper read in full text. Check
   that the enhancement claims and the discrimination-cost claim are proportionate to each
   other, and that `causal_attribution.basis: conditional_developmental_knockout` is right
   (the full text says the CA1 deletion is progressive from ~4 weeks).
4. **`PDE4B`** — the only above-baseline human enhancement in the atlas. All three studies
   have overlapping authorship, the benefit is at the *lowest* of three doses, and the
   drug is not PDE4B-selective. `above_baseline_enhancement: 3` is the highest enhancement
   grade anywhere here and is the most consequential number to challenge.
5. **The eleven `not_assessed` facets against the twenty graded `0`.** Check the split is
   genuine rather than convenient: `not_assessed` should mean this agent never looked, and
   `0` should mean it looked and found nothing. Every zero now carries a `search_basis`
   naming the queries and the scope limit, so the zeros are the auditable half — test them
   against the searches the README §3.1 claims were run. The eleven `not_assessed` have no
   such accountability by design, and `transfer_breadth` accounts for eight of them, which
   is the weakest part of this atlas's coverage.
6. **`GPR158`** — this atlas records its sign as unresolved and grades
   `mechanistic_causal_perturbation` at level 1 with `counter_level` 2. If that is right,
   the target arguably does not belong in a brake atlas at all, and saying so would be a
   legitimate finding.
7. **`CLM:brakes:EIF2B_COMPLEX:006`** — the human genetic claim added late in the run.
   Check that a progressive leukoencephalopathy has not been laundered into an
   "eIF2B is required for cognition" statement broader than the source supports.
8. **Uncited registered sources.** Confirm 56/56 verification is not being used to imply
   56 supported claims. 5 sources support nothing, by design.
