# Theory

Two conceptual models organise this project: the **Cognitive Power Envelope
Hypothesis**, which says what capacity depends on, and the **OPEN → WRITE → SELECT →
LOCK** cycle, which says how durable change is supposed to happen. Both are hypotheses.
Neither is a finding.

## 0. How to read this document

* **No probabilities appear anywhere in it.** Every number in this repository comes
  from a named model under `models/` and carries a calibration status (README §4,
  contract P3). A theory document that assigned confidences to its own claims would be
  the exact failure this repository is built to avoid.
* **Empirical statements cite claim ids, and nothing else.** Citations live in the
  evidence layer: a claim id resolves to a claim, which resolves to a
  machine-verified source. PMIDs deliberately do not appear here. If a statement
  should be empirical and has no claim behind it, it is written as an explicit
  `[EVIDENCE REQUIRED: …]` hook rather than asserted.
* **Structural statements are marked as such.** Where a sentence is a modelling choice
  rather than an empirical claim, it says so.
* **The theory endorses no target.** Every target named below is named as a *case*, and
  several are named because the evidence goes against the theory.

---

## 1. The Cognitive Power Envelope Hypothesis

### 1.1 The proposition

Useful cognitive work available to a healthy adult brain is hypothesised to depend on
six factors, not one:

| Factor | What it is | State domain |
|---|---|---|
| **POWER** | energy supply and delivery available to spend on computation | `power` |
| **EFFICIENCY** | how much of that power becomes useful information processing rather than overhead | `efficiency` |
| **WORKSPACE** | how much can be held online, protected from interference, and manipulated | `workspace` |
| **LEARNING** | the rate and precision with which synaptic and circuit change can be induced | `plasticity` |
| **CONSOLIDATION** | conversion of labile change into durable, retrievable, integrated knowledge | `consolidation` |
| **STABILITY** | homeostatic and dynamical regulation keeping the other five inside their operating range | `stability` |

The hypothesis is that these are **separable** and that a limitation in any one of them
is not compensable by abundance in the others. That is the substantive content. The
arithmetic that follows is a choice about how to express it.

### 1.2 Multiplicativity is a MODELLING CHOICE, not a law

Written multiplicatively:

```
CAPACITY  ~  POWER x EFFICIENCY x WORKSPACE x LEARNING x CONSOLIDATION x STABILITY
```

**This form is asserted as a modelling convenience, and it is very likely wrong in
detail.** No evidence in this repository establishes it, no parameter of it has been
fitted, and the ranking model in `models/ranking/` does **not** use it (its primary
composite is additive, and the disagreement between the two is measured every run as a
Kendall tau-b against multiplicative variants — `ranking_spec_v0_1.yaml` §5).

What multiplicativity *implies*, if taken seriously:

1. **Any factor near zero dominates.** A brain with no consolidation has no capacity,
   however much power it has.
2. **No factor substitutes for another.** Doubling POWER cannot buy WORKSPACE.
3. **Returns to improving a factor depend on all the others.** The same increment in
   LEARNING is worth more in a brain whose other factors are high — which is the
   opposite of what an intervention aimed at a deficit would predict.
4. **Interventions interact.** Two independently modest improvements compound.

Claims (1) and (2) are the ones the hypothesis genuinely wants. Claims (3) and (4) are
*consequences of the arithmetic* that nothing in this repository supports, and they are
the reason the form must be labelled rather than assumed.

### 1.3 The alternatives, and what would distinguish them

| Form | What it says | Signature in data |
|---|---|---|
| **Multiplicative** `prod f_i` | any factor near zero dominates; factors compound | interventions on two different factors produce a *super-additive* effect; effect of improving one factor scales with the level of the others |
| **Additive** `sum w_i f_i` | factors substitute; a deficit in one can be paid for by another | intervention effects add with no interaction; improving one factor has the same effect regardless of the others |
| **Minimum / Liebig-limiting** `min f_i` | only the currently limiting factor matters | improving a non-limiting factor produces *nothing*; effects appear abruptly when the limiting factor changes identity |
| **Hierarchical / nested** | some factors gate others (e.g. STABILITY gates everything; CONSOLIDATION gates the value of LEARNING) | improving a gated factor has no effect until the gating factor is adequate; ordering effects in intervention sequence |
| **Saturating** `prod g(f_i)` with `g` concave | factors compound but each saturates | diminishing returns within each factor; a ceiling that does not move when one factor is pushed further |

**What would distinguish them.** All five make the same prediction about a single
intervention on a single factor, which is why the single-intervention literature cannot
settle this. They differ on three things:

1. **Factorial interventions.** Two interventions targeting *different* factors, tested
   alone and together, in the same healthy participants. Additive predicts no
   interaction; multiplicative predicts super-additivity; minimum predicts that one of
   the two does nothing at all. This is the decisive design and essentially no such
   study exists for any pair of factors in this table.
   `[EVIDENCE REQUIRED: a factorial intervention study crossing two distinct envelope factors in healthy adults, with a measure of the factors themselves and not only of the outcome]`
2. **Baseline dependence.** Whether an intervention's effect depends on the
   participant's level of the *other* factors. Multiplicative and hierarchical predict
   it does; additive predicts it does not.
   `[EVIDENCE REQUIRED: an intervention study stratified on measured baseline levels of factors other than the one intervened on]`
3. **Which factor is limiting, and whether it changes.** The minimum form predicts
   effects that appear and disappear as the limiting factor changes identity — under
   sleep deprivation, under stress, at age.

Until a factorial design exists, the choice of form is **not identifiable from the
available evidence**, and this document treats it as undetermined rather than settled.

### 1.4 The POWER factor may not be limiting at all in healthy adults

This is the clearest case where the evidence currently runs against the envelope's
usefulness, and it belongs in the theory rather than in a footnote.

`agent:power` could not reject the null hypothesis that healthy, rested, well-fed adult
cognition is **not** power-limited:

* A parallel-group placebo-controlled trial in young healthy physically active adults
  found no effect on attentional control despite an effect on physical performance
  (`CLM:power:creatine_human:003`).
* A systematic review and meta-analysis of randomised trials in healthy individuals
  found a small overall effect at best (`CLM:power:creatine_human:002`).
* Where benefits do appear, they appear in **low-baseline or stressed states**: in
  vegetarians, whose baseline is lower (`CLM:power:creatine_human:001`), and under
  twenty-one hours of total sleep deprivation (`CLM:power:creatine_human:004`).
* Adult-onset loss of the creatine transporter produced no learning deficit, while
  developmental loss of the same transporter did (`CLM:power:SLC6A8:002` versus
  `CLM:power:SLC6A8:003`), and the human deficiency syndrome is a developmental one
  (`CLM:power:SLC6A8:001`).

The reading that survives this is not a *ceiling* the brain presses against but an
**allocation policy** the brain adjusts: energy use is redistributed to the structures
doing the work rather than raised globally (`CLM:power:anls:003`), and the fraction of
metabolism spent on signalling rather than housekeeping is itself a parameter
(`CLM:power:budget:001`, `CLM:power:budget:004`).

**Consequence for the theory, stated plainly.** If POWER is not limiting in healthy
adults, then in the multiplicative form POWER is a factor near its own ceiling, and the
envelope's practical content reduces to the other five. The hypothesis is not thereby
refuted — a non-limiting factor is exactly what a multiplicative model predicts you
should stop pushing — but the *project's* interest in POWER as a control point is
substantially weakened, and the correct conclusion is that the power atlas's dominant
result is a negative one. Anyone reading a high `P(supra-normal potential)` for a power
target should read this section first.

### 1.5 Falsification

The hypothesis is falsified, as a useful framework, by any of the following:

| # | Observation | Why it falsifies |
|---|---|---|
| F1 | A factorial intervention crossing two distinct factors in healthy adults shows **purely additive** effects, replicated | Kills the multiplicative form and with it the "no substitution" claim, which is the hypothesis's main content |
| F2 | Interventions improving a **non-limiting** factor reliably improve capacity anyway | Kills separability: the factors are not doing independent work |
| F3 | The six factors do not separate empirically — measured proxies for them load on a single dimension | The factorisation is a description of our vocabulary, not of the biology |
| F4 | Every attempt to raise one factor moves a safety variable by a comparable amount | The envelope has no interior, which is the premise of the whole programme (`ROADMAP.md` falsification #3) |
| F5 | Capacity is set by distributed, redundant architecture with no small controlling set | The "control parameter" framing is wrong; the signature is a ranked table whose top targets never converge as causal evidence improves (`ROADMAP.md` falsification #1) |
| F6 | Each factor's ceiling is set by the same upstream quantity | The six factors are one factor with six proxies |

F5 is testable inside this repository and is being tested by construction: if the
ranking's top targets keep reshuffling as evidence accumulates, and rank intervals do
not narrow, that is the signature of failure rather than of insufficient data.

---

## 2. OPEN → WRITE → SELECT → LOCK

> **Sprint-2 addition — see [`theory/selective_encoding_hypothesis.md`](theory/selective_encoding_hypothesis.md).**
> The *Selective Encoding Hypothesis* is a sharper and more falsifiable statement of this
> cycle's SELECT and LOCK phases. Its central move is to make the decisive quantity a
> **contrast** — prioritised versus incidental retention within the same session — rather
> than a level. That reclassifies most existing "cognitive enhancer" evidence as silent
> rather than supportive, and it excludes, as a class, any mechanism whose action is a
> tonic shift in a plasticity parameter, because such a mechanism cannot know which
> synapses mattered. Machine-readable criteria:
> [`theory/selective_encoding_criteria.yaml`](theory/selective_encoding_criteria.yaml).


### 2.1 The cycle

A conceptual model of how a durable change to knowledge or capacity is supposed to
happen. It is a **description of phases**, not a mechanism, and not a schedule.

```
   OPEN ──────────► WRITE ──────────► SELECT ──────────► LOCK
   permit change    induce change     keep what is       stabilise it
                                      worth keeping      against further change
     │                 │                  │                   │
     └─── failure: ────┴──── failure: ────┴──── failure: ──────┴── failure:
          nothing can       change is          everything is      nothing can be
          change            induced but        kept, including    changed again;
          (gate shut)       unselective        noise              knowledge ossifies
```

### 2.2 What each phase means computationally

**OPEN — the permissive state.** Whether the substrate will accept change at all.
Computationally: raising the gain on plasticity induction relative to its threshold.
The clearest experimental handles are the machinery that *holds the gate shut*:
perineuronal-net and critical-period machinery (`CLM:brakes:OTX2:001`,
`CLM:brakes:OTX2:002`), tonic inhibition setting the induction threshold
(`CLM:brakes:GABRA5:005`), and constitutive suppressors of potentiation at specific
synapses (`CLM:brakes:RGS14:001`).
State variables: `SV:plasticity.critical_period_permissiveness`,
`SV:plasticity.ltp_threshold`, `SV:plasticity.ltp_magnitude`.
Primitives: none directly — OPEN is a precondition, not a computation.

**WRITE — induction.** Change is actually induced in the substrate, with a magnitude
and a spatial pattern. Computationally: the encoding step. Releasing an inhibitory or
transcriptional brake raises the magnitude of induced potentiation
(`CLM:brakes:GABRA5:005`, `CLM:brakes:HDAC2:003`), and transcriptional brakes set how
much of the plasticity gene programme is accessible when induction happens
(`CLM:brakes:HDAC2:001`).
State variables: `SV:plasticity.ltp_magnitude`,
`SV:consolidation.plasticity_gene_accessibility`.
Primitives: `PRIM:pattern_separation` (write *where*, distinctly), and binding.

**SELECT — what survives.** Most of what is written should not be kept. Selection is
the phase this project most often finds missing from the literature, because it is the
phase an enhancement study is least likely to measure. Computationally: competition
between traces, and the tagging that decides which are eligible for stabilisation. The
load-bearing observation is that releasing an induction brake can *cost* selectivity:
CA1-restricted deletion of the alpha5 subunit impaired discrimination between two
highly similar contexts (`CLM:brakes:GABRA5:003`).
State variables: `SV:workspace.interference_susceptibility`,
`SV:consolidation.memory_allocation_selectivity`, `SV:consolidation.engram_stability`.
Primitives: `PRIM:pattern_separation`, `PRIM:distractor_suppression`.

**LOCK — stabilisation.** The selected change becomes durable and is protected from
subsequent overwriting. Computationally: protein-synthesis-dependent stabilisation and
the closing of the reconsolidation window. Translational control is the clearest handle:
learning reduces the inhibitory phosphorylation that gates cap-dependent translation
(`CLM:brakes:EIF2S1:001`), removing that signal in specific hippocampal cell types
changes consolidation (`CLM:brakes:EIF2B_COMPLEX:005`), and interfering with the
astrocytic supply used during stabilisation prevents it
(`CLM:power:anls:001`, `CLM:power:anls:005`).
State variables: `SV:consolidation.consolidation_protein_synthesis_capacity`,
`SV:consolidation.reconsolidation_window_width`, `SV:plasticity.critical_period_permissiveness`
(read as the long-run lock).
Primitives: consolidation and schema integration.

### 2.3 Why "open the gate wider" is not a strategy

The single most tempting inference from the brake literature is that releasing brakes
increases capacity. The cycle above is structured to make the cost visible, and there
are three distinct reasons the inference fails.

**Interference.** OPEN and SELECT trade against each other. A substrate that accepts
change more readily also accepts change it should have rejected. The alpha5 case is the
cleanest instance in this repository: the same manipulation that augments induced
potentiation (`CLM:brakes:GABRA5:005`) impairs discrimination between highly similar
contexts (`CLM:brakes:GABRA5:003`). A capacity measure that only looks at induction will
record this as an improvement.

**Instability.** OPEN and STABILITY trade against each other. Excitability brakes are
load-bearing for dynamical regulation, not incidental to it: expressing
dominant-negative KCNQ2 subunits produced spontaneous seizures together with impaired
spatial memory (`CLM:brakes:KCNQ2:001`), while the same channel is physiologically
modulated by cholinergic input (`CLM:brakes:KCNQ2:002`). The safety cost and the
cognitive cost arrived together.

**Safety coupling.** Some energetic and excitability variables are coupled to harm
variables directly, so "more capacity" and "more risk" are not separable dimensions of
the same manipulation: brain creatine-kinase function and seizure susceptibility are
coupled in the same animals (`CLM:power:CKB:001`). Where such coupling exists, safety is
a **constraint on the admissible region**, not a cost to be traded against benefit
(README §3) — and the ranking model enforces that with hard caps rather than weights,
because a weight can always be out-argued.

**And the gate is not simply "open" or "shut".** Two further complications the strategy
ignores. The machinery is often *state-dependent*: the eIF2B-stabilising mechanism stops
working when the integrated stress response is already high
(`CLM:brakes:EIF2B_COMPLEX:003`), so the same manipulation does different things in
different states. And dose-response is not assumed monotone: a single systemic
administration of a low but not a high dose improved episodic memory in one case
(`CLM:power:KL:004`). A strategy of "more" has no defence against an inverted U.

**The correct framing.** The object of interest is not the width of the gate but the
**timing and selectivity of the whole cycle**. An intervention that opened the gate,
wrote selectively, selected correctly and then locked would be valuable; an intervention
that only opens the gate is, on the evidence above, as likely to degrade capacity as to
raise it.

### 2.4 What the cycle is not

* Not a schedule, and not a protocol. It names phases; it prescribes nothing, and no
  output of this repository may turn it into a procedure
  (`docs/COMPUTATIONAL_ONLY_POLICY.md`).
* Not established as four discrete phases. The phases may overlap, recur, or not be
  separable at all.
  `[EVIDENCE REQUIRED: evidence that permissiveness, induction, selection and stabilisation are separately manipulable in an adult human, rather than a single graded process described four ways]`
* Not demonstrated to run in adults for most of the machinery above. Several of the
  clearest handles are developmental: RGS14 protein is undetectable at birth and rises
  through the first postnatal weeks (`CLM:brakes:RGS14:003`), and OTX2's role was
  characterised in postnatal development (`CLM:brakes:OTX2:002`). The
  development-versus-adulthood distinction is a required field on every claim
  (contract P4) precisely because this literature makes the substitution easy.

---

## 3. Why a dynamical system rather than a score

Cognitive capacity is represented as

```
X(t+1) = F(X(t), U(t), E(t), Theta) + noise
```

with `X` the latent biological and cognitive state, `U` an intervention, `E`
experience/environment/task demand, and `Theta` slower individual parameters
(README §3).

### 3.1 What the framing buys

A score answers "how much?". The questions this project actually needs answered are all
about *trajectories*, and a score cannot express any of them:

* **Persistence.** Does an effect remain when `U` stops, or does the state return to its
  previous operating point? A single-timepoint effect size cannot distinguish a durable
  change from a temporary displacement.
* **State dependence.** The same `U` does different things at different `X`. This is not
  hypothetical: the eIF2B mechanism is inactive at high integrated-stress-response
  levels (`CLM:brakes:EIF2B_COMPLEX:003`), and the caffeine literature is a study in
  effects that depend on the state the intervention itself created — improvements after
  overnight abstinence (`CLM:brakes:ADORA1:003`) sit beside null results in
  controlled-baseline designs (`CLM:brakes:ADORA1:004`).
* **Shape.** Monotone, threshold, inverted-U or U-shaped. `E` carries task demand, so an
  effect that only appears under load is expressible here and invisible in a score.
* **Constraint violation.** Whether a trajectory leaves the admissible region on a
  safety variable. A score has nowhere to put that.
* **Allocation versus capacity.** The power atlas's best-supported reading — a policy
  the brain adjusts rather than a ceiling it presses against (§1.4) — is a statement
  about `F`, and is not expressible as a level of `X` at all.

### 3.2 The identifiability problem

The framing is honest about what it buys and must be equally honest about what it costs.
**As written, `F` is not identifiable from the data available to this project**, for
five separate reasons:

1. **`X` is latent.** It is observed only through proxies, and `ontology/state_variables.yaml`
   records a `measurability` field per variable precisely so that a variable with no
   human proxy cannot silently acquire one. Several have none.
2. **`Theta` is confounded with `X(0)`.** A cross-sectional difference between people
   cannot separate a slow parameter from an initial condition.
3. **`F` is unknown in form.** Any fit is therefore a *joint* claim about the functional
   form and the parameters, and a good fit supports neither on its own.
4. **Sampling is inadequate.** Public longitudinal cognitive and imaging data has
   neither the sampling frequency nor the intervention variation to separate a genuine
   state change from measurement drift.
5. **Measurement changes the state.** Repeated cognitive testing produces practice
   effects, so an uncontrolled trajectory confounds learning with state change.

`ROADMAP.md` Sprint 3 therefore puts a no-free-lunch **predictive baseline** before
anything mechanistic, and commits to demoting unidentifiable parameters regardless of
biological appeal. The interfaces and their identification limits are specified in
`models/causal/`, which states plainly that **no causal effect is estimated in Sprint 1**
and that the ranking model is an evidence-accounting device rather than a causal
estimator.

**So the present-day use of the dynamical framing is mostly negative.** It says which
quantities the project is not entitled to talk about yet. That is a smaller claim than
it looks, and it is the honest one.

---

## 4. What this theory forbids

A theory that forbids nothing explains nothing. This section is the one to hold the
project to.

### 4.1 Predictions that would falsify it

Beyond F1–F6 in §1.5:

| # | If this is observed | The theory is wrong about |
|---|---|---|
| F7 | Releasing an induction brake improves selectivity as well as induction, replicated | the OPEN↔SELECT trade-off, which is the cycle's main content |
| F8 | Adult-onset manipulation reproduces developmental phenotypes across the board | nothing — but it would remove the project's central constraint and make the adult-modifiability dimension vacuous |
| F9 | Every state variable turns out to have a monotone response, with no inverted-U anywhere | the "maximising is not assumed to be good" premise, and the response-shape machinery built on it |
| F10 | A single upstream quantity predicts cognitive capacity better than any combination of the six factors | the factorisation entirely |
| F11 | Interventions on separate factors show *sub*-additive effects (each blunts the other) | all five candidate forms in §1.3, including the minimum |

### 4.2 Inferences this theory does NOT license

* **No target is endorsed.** The theory names mechanisms and cases. It does not
  identify anything as worth modulating, and a high rank in
  `reports/target_ranking_v0_1.csv` means "this control point deserves more
  computational scrutiny", never "this is safe or effective to modulate"
  (`docs/COMPUTATIONAL_ONLY_POLICY.md`).
* **No state variable should be maximised.** Every state variable carries a
  `response_shape` defaulting to `unknown`, and a monotone "higher is better" reading
  must be licensed by evidence for that variable specifically. `CLM:power:KL:004` and
  the caffeine dose-response literature are in this document because they are the
  standing counterexamples.
* **Safety variables are constraints, not costs.** They may not be traded against a
  benefit at any exchange rate. Safety and stability variables also declare a
  `polarity` (`risk` or `margin`) which point in opposite directions, so a directional
  reading of one must consult the declaration rather than the variable's name.
* **A brake is not a target because it is a brake.** "This mechanism suppresses
  plasticity" licenses "releasing it changes plasticity", and nothing about whether that
  is good, adult-available, transferable, or survivable.
* **Animal memory is not human intelligence, and educational attainment is not
  intelligence.** Most of the mechanistic claims cited above are rodent; several are
  developmental; none of them is a human cognitive-capacity result. Contract P4 makes
  these required record fields rather than prose caveats.
* **Convergence is not corroboration.** That several targets converge on one state
  variable is a fact about what has been curated, and may reflect curation attention
  rather than biology. The convergence analysis in
  `src/blueprint/ranking/convergence.py` reports claim-derived path counts separately
  for exactly this reason.
* **Cross-species conservation does not license human inference by itself.** Where
  direct human-versus-model comparisons exist they can disagree in sign within one
  target: the two direct human-versus-rodent h-current comparisons for HCN1 disagree by
  cortical layer (`CLM:comparative:HCN1:004`), against a background of a conserved
  allometric relationship across mammals (`CLM:comparative:HCN1:003`). A conserved gene
  is not a conserved mechanism. Comparative task measures can also fail to replicate
  across studies of the same paradigm (`CLM:comparative:SELF_REGULATION:001` versus
  `CLM:comparative:SELF_REGULATION:002`).
* **The multiplicative form licenses no arithmetic.** It may not be used to compute a
  capacity, to multiply effect sizes, or to argue that two interventions compound. It is
  a statement about non-substitutability, and §1.3 says what would be needed to earn
  more than that.

### 4.3 What the theory would need in order to become a model

Recorded so the gap stays visible:

1. A human proxy for each of the six factors, with a stated measurement error.
   `[EVIDENCE REQUIRED: a validated human proxy for the LEARNING and CONSOLIDATION factors that is not a task score, since a task score confounds the factor with WORKSPACE and with practice]`
2. A factorial intervention crossing at least two factors (§1.3).
3. Response shapes established per state variable rather than assumed
   (`ROADMAP.md` Sprint 3).
4. An identifiability analysis saying which parameters of `F` are estimable from
   available data, and demotion of those that are not.

Until those exist, this document is a **framework for organising evidence**, and the
deliverable it supports is a ranked table of what to analyse next with an explicit
uncalibrated interval — not a claim about how cognition works.
