# Schema-change request resolutions — Sprint 1

Decided by `agent:orchestrator`. Each request was filed by an agent that hit a real
limit of the contract, worked around it, and recorded what the workaround lost. That is
the blackboard working as intended: three of the four contract amendments in this sprint
came from defects found in use rather than from design review.

---

## R1 — `alphacognition-001` item 1: database releases cannot satisfy V6 · **RESOLVED (differently)**

*Filed blocking for gate G3.* Correct diagnosis: the contract required every source to
reach `status: verified`, while `SRC:DB:*` sources fell through to
`unsupported_registry`, making the requirement and the tooling mutually unsatisfiable.

Resolved in `scripts/fetch_source_metadata.py`, but not as proposed. Rather than
re-reading the release string out of the pipeline's own snapshot (which would verify a
record against itself), a release is verified against **manifest integrity**: the
snapshot must exist in `data/raw/MANIFEST.jsonl` and its sha256 must still match the
file on disk. Status `release_verified_by_snapshot`, accepted by V6 for `SRC:DB:*` and
`SRC:DATASET:*` only. `snapshot_missing_or_altered` remains a violation and deliberately
overlaps rule V19.

*Consequence for the filer:* `SRC:DB:gtex:v8` will only verify once a GTEx snapshot
exists under `data/raw/`; register it after the fetch, not before.

## R2 — `brakes-001` item 1: three missing computational primitives · **APPROVED**

Four brake classes in that atlas are defined by what they do to gain and to the
integration window, and the primitive set had no term for either. Borrowing
`pattern_separation` for gain control and `relational_binding` for temporal integration
was a real loss of meaning.

Adding `PRIM:gain_control`, `PRIM:temporal_integration`,
`PRIM:dendritic_coincidence_detection`, each marked
`origin: agent_proposed_sprint1` to distinguish them from the brief-supplied set. The
brief listed its 24 primitives as an opening set, so extension is expected; attribution
keeps the provenance of the ontology itself visible. The brake atlas then re-points the
HCN1, KCNQ2, KCNQ3 and GPR158 dossiers off the borrowed primitives.

## R3 — `brakes-001` item 2: no state variable for dose-limiting tolerability · **APPROVED**

For two consolidation brakes the binding human constraint is not an organ-specific risk
but the margin between the exposure that produces an effect and the exposure at which
adverse events become dose-limiting. That was the most decision-relevant safety fact in
the atlas and it had nowhere to live, so it was visible only in prose — meaning the
ranking model would have read a narrow safety profile as a favourable one.

Adding `SV:safety.dose_limiting_tolerability_margin`
(`desirability: higher_is_better_within_range`, `response_shape: unknown`).

## R4 — `brakes-001` item 3: risk-versus-margin polarity convention · **APPROVED, and mechanised**

The atlas first wrote its excitability constraint as a seizure *threshold* (the
electrophysiology convention) and had to invert six coupling directions when
re-pointing to `SV:safety.seizure_risk`. `direction: increases` against a threshold and
against a risk mean opposite things, and the error is silent.

The convention is documented, and it is also enforced: every safety and stability state
variable declares `polarity: risk | margin`, the validator warns when an id ending in
`_margin` declares `risk` (or vice versa), and annotations are read relative to the
declared polarity. A convention that is only written down will be broken by the next
agent.

## R5 — `brakes-001` item 4: absence of measurement ≠ measured absence · **APPROVED — the most consequential item in this batch**

The contract could express "tested and found no effect" but not "the only human trial of
this mechanism never measured a cognitive endpoint". Two claims in the brake atlas were
recorded as `clinical_null` with a caveat in a required field, and read mechanically they
look like failed trials. They are not.

Three changes:

1. `evidence.endpoint_measured`: `measured | not_measured_in_protocol |
   measured_but_not_reported | unknown`. This is where the fact lives.
2. `claim_type: evidence_gap` — **graph-inert**: it creates an evidence-layer record and
   no biological or intervention edge, because an absence of measurement is not a
   finding about biology. It may never contribute to a facet's `counter_level`; it
   counts towards a coverage gap.
3. Rule **V16c**: `NO_DETECTED_EFFECT_ON` requires at least one evidence item with
   `endpoint_measured: measured` *and* `evidence_role ∈ {null_result, contradicts}`. If
   every evidence item is `not_measured_in_protocol`, the claim must be `evidence_gap`.

`structural_biology` is also added to `evidence.design`; recording a cryo-EM structure
as `narrative_review` described what was read, not what was done.

## R6 — `comparative-001`: phylogenetic control, species count, between-species relation · **APPROVED**

Of 20 comparative claims, 18 rest on analyses with no phylogenetic control, in several
cases confirmed from the methods text. Without a field for it, a result that survived a
phylogenetic mixed model and an uncontrolled cross-species regression look identical to
the validator and to the ranking model.

`context.phylogenetic_control` (with `not_reported` distinct from `none` — the
implementing agent's enum was better than the proposal, which forced those two states to
share a value), `context.species_count` (a count, not a score, so safe under P3/V9), and
relations for stating a between-species difference or conservation without borrowing a
causal relation that overstates the evidence.

## R7 — `integration-001`: nowhere legal to write a database-derived facet grade · **APPROVED (option A + `source_refs`)**

`agent:integration` owns the `tractability` facet but had no contract-legal location to
write an assessment, and no legal way to satisfy the `claim_refs` requirement for a
grade derived from a pinned database release. Its interim behaviour — publish a
`suggested_level` in a derived index, write no assessment, leave the facet
`not_assessed` — under-used real data it already held, and was the right call: it chose
to lose information rather than abuse the schema.

1. `atlases/{agent}/assessments/{SYMBOL}.yaml` is now a legal location for non-domain
   agents that own facets (`agent:integration`, `agent:red_team`), with
   `atlases/integration/**` added to that agent's lane. Rule V11 already restricts each
   agent to the facets it owns, so attribution is unaffected.
2. A facet may cite `source_refs: [SRC:DB:…]` in place of `claim_refs` when it carries
   `evidence_basis: database_release`. Permitted **only** for facets flagged
   `database_gradable: true` in the rubric — at present `tractability` alone — and the
   rationale must name the exact field values used.

The rejected alternative (a `tractability_annotation` claim type) is rejected for the
filer's own reason: it would place a non-biological annotation in the claim layer, where
every downstream consumer treats records as evidence about biology.

## R8 — `integration-002`: dimension D3 has a single input · **APPROVED**

D3 (supra-normal potential) was fed by one facet, carrying 0.15 of the composite: not an
aggregate but a relabelling of one grader's ordinal judgement, with no cross-check and
no way for two lines of evidence to disagree. It was also the dimension most sensitive
to a one-level change, which made the information-gain sweep structurally over-value it.

`dose_response_knowledge` becomes a secondary input to D3 — "can this move a healthy
adult above baseline" is not answerable without the shape of the exposure–response
relation, and an inverted-U whose optimum sits at the healthy baseline is exactly a case
where supra-normal potential is absent. `tractability` becomes a secondary input to D5,
since a target whose only known modulators hit the whole family has a narrower
controllable window by construction, and the rubric already collects family selectivity.

The alternative — a new `healthy_baseline_arm_quality` facet — is attractive and
deferred to Sprint 2, because adopting it now would require every atlas to re-grade.

Additionally, `reports/target_ranking_v0_1.meta.json` must expose the input count per
dimension, so a single-input dimension can never again be invisible.

## R9 — `comparative-002`: a null that cannot be expressed · **APPROVED, generalised**

`NO_DETECTED_EFFECT_ON` was given the domain of the intervention-style relations, so a
genuine cross-clade null — a performed test in which absolute brain volume predicted
nothing about self-regulation — could not use it, because the tested predictor is a
`BrainRegion`. The claim therefore still compiles as `CONSTRAINS` with
`direction: unclear`, and any traversal that ignores `direction` reads the comparative
atlas's most-cited deflationary result as *support* for "bigger brain, better
inhibition". That is precisely the drift V16b was created to prevent, left unprevented.

Fixed as a general rule rather than a one-off domain patch (**V16b-sym**): the domain
and range of `NO_DETECTED_EFFECT_ON` must be at least the union of the domains and
ranges of every relation it can negate. A null must be expressible wherever the
corresponding positive claim is expressible; otherwise the ontology is structurally
biased towards positive findings. Claims using it must also name the relation they
negate in `negated_relation`, so the record states what was tested and found absent.

**The filer's refusal to migrate `CEPHALOPOD_GENOME:001` is upheld and is the right
instinct.** Its "negatives" are an absent whole-genome duplication and an unremarkable
gene repertoire — nobody tested whether protocadherin expansion affects structural
plasticity rate. A null edge there would manufacture a finding out of a gap, which
V16b explicitly forbids. The refusal is recorded in the claim so that a later agent
does not "fix" the omission.

## R10 — `direction: state_dependent` versus `unclear` · **AMENDED**

The same agent declined `state_dependent` for a claim whose sign depends on cortical
layer, on the ground that the vocabulary defined `state_dependent` as depending on
*physiological state*, and kept `unclear`. Correct under the wording, but the outcome is
bad: "we know it varies, and we know what it varies with" was recorded identically to
"we do not know".

`state_dependent` now covers a **known and specified** dependency — physiological state,
cell subpopulation, cortical layer, compartment or task condition — and a new required
companion field `direction_context` names it. `unclear` is reserved for genuine
ignorance. The distinction is the difference between a characterised interaction and a
shrug.

## R11 — Level 0 required a citation for the absence of evidence · **SCHEMA DEFECT, fixed**

Found by the orchestrator while triaging 212 V1 violations in the already-finished power
atlas. The assessment schema required `claim_refs` on every assessed facet. But
`level: 0` on the shared scale means *searched, nothing found* — there is by definition
nothing to cite, and the power atlas's honest records ("Searched and found nothing.
Every creatine-kinase perturbation retrieved is a germline knockout…") were being
rejected for it.

Demanding evidence for the absence of evidence is incoherent, and the pressure it
creates is worse than the gap it closes: an agent facing that error either invents a
tangential citation or silently converts a truthful 0 into `not_assessed`, which is a
different epistemic state and one the contract works hard to keep distinct.

`claim_refs` is now required only when `level >= 1`, and `counter_claim_refs` only when
`counter_level >= 1`. A zero is audited differently: it requires a non-empty `rationale`
plus a new required `search_basis` naming what was searched, at what scope, and what
would have counted as a hit. A zero with no `search_basis` fails validation. The zero
therefore remains accountable without being asked for an impossible citation.

## R12 — Closed objects rejected legitimate domain detail · **SCHEMA DEFECT, fixed**

`additionalProperties: false` everywhere is the right default, but it rejected an AAV
construct's `vector_serotype` and similar real domain metadata the schema never
anticipated. That forces an agent either to drop real information or to misuse a field
that means something else.

Intervention and target records now carry an optional `attributes` mapping with
**string-only** values — string-only because a number in an unvalidated bag would escape
rule V9's provenance requirement. It is explicitly a holding area: anything in
`attributes` that proves decision-relevant must graduate to a validated field through a
schema-change request. State-variable annotation records may likewise carry an empty
`couplings` list when `basis: not_asserted_pending_claims`, which is the honest record
for "looked, nothing to assert yet".

## R13 — `clinical_harm` was being used for animal harm · **VOCABULARY DEFECT, fixed**

Found by `agent:brakes`, which recorded increased seizure susceptibility in mice as
`clinical_harm` because no other value fitted, and flagged the forced label itself:
"science solid, label forced".

`clinical_harm` is now reserved for harm observed in humans, and `preclinical_harm`
added for harm observed in a non-human model. The distinction is not cosmetic: a mouse
finding wearing a clinical label makes animal evidence read as clinical evidence, which
is the laundering direction principle P4 exists to block. It is also the direction that
is easiest to let slide, because over-stating a *harm* feels safe — it costs the project
its credibility rather than anyone's safety, so nobody pushes back.

## R14 — A level 0 could not distinguish "nobody tried" from "tried, nothing published" · **APPROVED**

Found by `agent:power` while writing the `search_basis` fields that resolution R11
required — and the discovery is the strongest argument for R11 that could have been
made. Forced to state what it had actually searched, the agent found that its zeros were
literature-only and it had barely searched the trial registry. Running the missing
searches turned up a **completed** human klotho intervention with cognitive secondary
endpoints, after it had reported in its previous handoff that no human klotho
intervention existed. The facet still grades 0 — no posted results, uncontrolled, n=14,
with a co-administered agent making the contribution unidentifiable — but as the agent
put it, "graded 0 because a completed trial reported nothing" is a different statement
from "graded 0 because nobody tried", and only the first is true.

The generalisation is the part worth keeping: **a literature-only search systematically
misses the category that matters most for a translation facet — interventions performed
and never published.**

Facets now carry `reporting_gap_refs: [SRC:NCT:…]` for registered interventions that
completed without posted results, and `search_basis` must mention them. It is not
counter-evidence and may never raise `counter_level`; it is a finding about the evidence
base, feeding the red team's `publication_bias` check and surfaced per target as
`reporting_gap_count` in the ranking report.

*Related rubric gap, accepted as a known limitation:* `evidence_strength_v1` still has
no level meaning "a trial exists, completed, and reported nothing". A reader who reads
only the integer will draw the wrong conclusion, which is why `reporting_gap_refs` is
structured rather than left in prose. Revisiting the scale itself is deferred to
Sprint 2 (it would force every atlas to re-grade).

## R15 — A level 0 was covering three different situations · **APPROVED (clarification)**

`agent:power`, running the target-directed registry search its first round had skipped,
found that a single `level: 0` on one facet family was covering three distinct states:

1. **Genuine absence of enquiry** — nobody has tested it.
2. **Evidence gap** — `SRC:NCT:NCT01791595` (AZD3965, an MCT1 inhibitor, 53 patients,
   completed, **results posted**) reported every primary outcome as toxicity or adverse
   events and every secondary as pharmacokinetic, cell-death or tumour response. It
   reported results but **never asked the cognitive question**.
3. **Reporting gap** — `SRC:NCT:NCT01455376` (interventional lactate infusion, n=60,
   completed 2010) had a **neurocognitive primary outcome** and has posted nothing in
   sixteen years. It asked the question and never reported.

The contract already distinguishes all three (`evidence_gap` for 2, `reporting_gap_refs`
for 3, a plain audited zero for 1) — the gap was that no one had applied them inside a
single facet before. Recorded here because the three-way distinction is easy to collapse
back into "no evidence", and because it took a target-directed registry search rather
than a literature search to see it at all.

*Scope judgement upheld:* the agent declined to list the shared lactate trial against
the three MCT facets as well as HCAR1, on the ground that it engages those transporters'
*substrate* rather than the transporters, and that listing one trial four times would
turn one gap into a `reporting_gap_count` of four. Each affected `search_basis` names the
trial and says where it is listed and why, so the red team can widen the scope if it
reads it differently. Inflating a bias count by re-counting one study is the same error
as inflating evidence by re-citing one paper.

## R16 — Raw snapshot directories were owned per agent, breaking the new tooling · **FIXED**

`scripts/record_tool_snapshot.py` (added so MCP-tool-derived data can be provenanced at
all) writes to `data/raw/<registry>/`. But `docs/OWNERSHIP.yaml` had assigned those
directories to individual agents — `data/raw/chembl/**` to `agent:alphacognition`,
`data/raw/ctgov_v2/**` to `agent:red_team` — so the agent that needed a registry
usually did not own it, and writing there would have been a lane violation. The script
was therefore unusable by almost everyone, and `agent:power` correctly refused to use it
rather than cross a lane.

Raw snapshots are keyed by **registry, not by agent**; they are immutable once written;
and attribution already lives in `MANIFEST.jsonl`, which records the tool, query and
timestamp per entry. `data/raw/**` is now `shared_append_only`.

## R17 — The declared-gap mechanism worked, and it produced the sprint's most important finding

*Not a schema change; recorded because it is the clearest evidence about whether this
architecture earns its overhead.*

`agent:brakes` could not determine whether three α5-GABA-A trials had recorded their
protocol cognitive endpoints. Rather than guess, it left claim id
`CLM:brakes:GABRA5:009` permanently unused and wrote a marked audit item naming exactly
what it could not determine and exactly what would settle it — including that
`NCT02953639` (n=214, MATRICS composite, completed) **had results posted that it had not
retrieved**, calling that the largest unresolved item in its atlas and noting it could
move the facet either way.

`agent:red_team` retrieved them. The α5-GABA-A negative-modulation mechanism produced a
treatment difference of **+0.28 MCCB composite T-score points (95% CI −1.47 to +2.02,
p = 0.793)** on a scale whose population standard deviation is 10, with target engagement
demonstrated in the companion trial. That is not an absence of evidence; it is a
*precise* null. Together with CLEMATIS, the human null on this mechanism is
**replicated**.

Two things follow. First, the repository's most-studied brake target now carries
replicated human negative evidence, which is a real scientific result and the opposite of
what a seed list implies. Second — and this is why it is recorded here — the mechanism
that produced it was an agent **declining to assert something it could not verify**, in a
form precise enough for another agent to act on. A swarm that chatted would have produced
a plausible paragraph about α5 modulation. The blackboard produced a claim id left
deliberately empty, a named trial, and a retrieved 95% confidence interval.

## R18 — Educational attainment was laundered into fluid reasoning by a guard that lived in data while the decision lived in code · **CRITICAL, fix assigned**

`atlases/alphacognition/cognitive_trait_panel.yaml` marks "mathematical ability" as
`use_in_ranking: supporting`, with the explicit note that it is "never a stand-alone
basis for a facet level". But `pipelines/alphacognition/build_assessments.py` tests
`phenotype_class` and never reads `use_in_ranking`, so the guard was inert. The
underlying records are "Self-reported math ability" and "Highest math class taken" from a
1.1-million-person **educational attainment** GWAS, and they were supporting
intelligence-relevant facet levels.

This is the precise failure principle P4 exists to block, and the lesson generalises past
the fix: **a guard expressed as a data field is not a guard until some code reads it.**
The panel was written carefully, the caveat was correct, and it protected nothing. The
remedy is to make the generating code honour `use_in_ranking`, fail closed on a missing
value, and carry a test that fails the old behaviour — not merely to correct the affected
grades.

Found because `agent:alphacognition` nominated its own generated-facet rule as the thing
to attack hardest ("if it is wrong it is wrong 108 times identically") and the red team
audited the rule rather than sampling its outputs.

## R19 — `direction: no_change` was doing duty for "no direction applies" · **VOCABULARY DEFECT, fixed forward**

Found by the orchestrator while checking the compiler's report that 528 of 627
claim-derived edges are "claim-derived but not support". That number turned out to be
mostly legitimate — a GWAS association or an `evidence_gap` genuinely states no
direction — but **31 `expression` claims carried `direction: no_change`**, and an
expression claim asserts no change at all.

`no_change` means *measured, and no change was found*. Using it for *no direction
applies* makes a record nobody measured look like a measured null — the identical
conflation as R5 and V16c, one level down, and the fifth time this sprint that a value
meaning "we looked and found nothing" was pressed into service for "there was nothing to
look for". The direction enum simply had no value for the third state.

Added `direction: not_applicable`, and rule **V-DIR2**: `no_change` requires at least one
evidence item with `endpoint_measured: measured`. The 31 pre-existing records are
reported as **warnings rather than errors**, deliberately — re-opening three finished
atlases to correct a latent misread was judged a worse use of the remaining sprint than
finishing the ranking, and a warning keeps the debt in front of anyone who runs the
validator instead of buried in a summary. The precise remediation is a named Sprint-2
task.

*Also checked and found legitimate:* 5 `causal_perturbation` claims carry `unclear`,
which is a curation gap worth a Sprint-2 pass — a perturbation study that measured an
outcome should be able to state which way it moved.

## R20 — X01's verification state advanced; the test pinned the old *label*, not the *invariant* · **TEST CORRECTED (cross-owner, recorded here)**

Sprint 3 found the Codex/Astra branch the Sprint-2 audit declared nonexistent (a local,
never-pushed linked worktree). X01's artefacts therefore now exist, and its gene-level MAGMA
layer was independently re-derived and reproduced. The schema's own vocabulary has the right
state for that — `verification_status: artefacts_received_pending_check`,
`delivery.mechanism: local_clone_path` — because the **cell-type claim** is still not
re-derived here.

`tests/test_x02_ingestion.py::test_x01_is_recorded_as_unverified_and_licenses_nothing`
asserted `verification_status == unverified_external_report`. That pinned a label. The
invariant the test exists to protect is different and still holds: **X01 licenses nothing
while its claim is unverified** — `provenance_class` stays `external_analysis_unverified`,
every `reported_results[*].claim_refs` stays empty, and V-EXT still refuses any claim citing
it. The test is corrected to assert the invariant (either pre-verification state is allowed;
the licensing guards are unchanged).

`tests/**` is owned by agent:ontology. The orchestrator made this one-assertion change
directly, and records it here so the owner can review or revert it: no ontology agent ran in
Sprint 3, and leaving a test asserting a now-false delivery fact would have blocked the commit
on an obsolete label. Also: `pipelines/reports/**` was UNCLAIMED (created in Sprint 2 without
an ownership entry) and is now claimed by the orchestrator.
