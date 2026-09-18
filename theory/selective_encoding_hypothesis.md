# The Selective Encoding Hypothesis

**Status: THEORY NODE.** Not a finding, not a validated mechanism, not a recommendation
about any compound. Recorded 2026-09-18, originating from the project lead.
Machine-readable form: [`selective_encoding_criteria.yaml`](selective_encoding_criteria.yaml).

**Computational-only.** Everything below specifies what a mechanism would have to *do*,
so that candidate mechanisms can be evaluated computationally. Nothing here is a dose, a
route, a regimen or a protocol, and none of it is advice
(`docs/COMPUTATIONAL_ONLY_POLICY.md`).

---

## 1. The hypothesis

> The optimal durable cognitive enhancer should not globally strengthen memory. It should
> increase the **contrast** between goal-relevant and incidental encoding, by amplifying
> activity-dependent plasticity **only within task-engaged representations**.
>
> The decisive phenotype is improved retention and transfer of explicitly prioritised
> information *without* proportional enhancement of unattended or low-value information.
>
> The desired mechanism should make one or a few episodes sufficient to create a durable,
> compressed, retrievable representation — not merely make every experience memorable.

Candidate mechanism families: top-down attentional gating, hippocampal encoding-state
control, synaptic tagging and capture, neuronal memory allocation, neuromodulatory
persistence signals, and the consolidation processes that follow.

## 2. Why this is a sharper instrument than it first appears

The hypothesis looks like a refinement of "make memory better". It is not. It changes the
**measured quantity**, and that change disqualifies most of the evidence that a
conventional programme would treat as supportive.

### 2.1 The decisive quantity is a contrast, not a level

What matters is the difference between what happens to prioritised material and what
happens to incidental material encountered in the same session:

```
selectivity_gain = (prioritised_treated − prioritised_control)
                 − (incidental_treated  − incidental_control)
```

Two consequences follow immediately, and they are the useful part:

* **A global memory enhancer scores exactly zero** on this quantity, however large its
  main effect, because both terms rise together. "It improved recall" is not evidence for
  this hypothesis — it is evidence for a different and weaker one.
* **A pure selectivity mechanism can score positive with no main effect at all** on total
  material retained. Such a mechanism would look like a failure under a conventional
  total-recall endpoint.

So the hypothesis makes a specific methodological demand: within-session manipulation of
item value or task relevance, retention tested **separately** for prioritised and
incidental items, at a delay long enough for consolidation to matter. A study reporting
only total recall is not weak evidence here. It is *silent* — `not_assessable`, which the
repository's contract treats as a different state from `no_effect` (resolutions R5, R11,
R14).

That reclassification is worth more than it sounds. It means most of the existing
"cognitive enhancer" literature cannot speak to this hypothesis either way, and that
absence should be recorded as a coverage gap rather than read as equipoise.

### 2.2 The seven requirements are a filter, not a wish list

| | Requirement | The interesting part |
|---|---|---|
| SE1 | Enter a voluntary encoding mode | Goal state must move a plasticity threshold, not just arousal |
| SE2 | **Use activity as the address** | The crux — see below |
| SE3 | Convert transient understanding into a stable trace | Potentiation that decays is not enhancement |
| SE4 | Encode latent structure, not sensory detail | A schema, not a photograph of page 73 |
| SE5 | Maintain an efficient index | Retrievable from partial cues, or it may as well be absent |
| SE6 | Preserve selectivity | Incidental material must *not* come along |
| SE7 | Keep forgetting available | Forgetting is a function; removing it may make cognition worse |

**SE2 is the crux, and it is where the hypothesis earns its keep.** A systemically
administered agent reaches every synapse. The selectivity therefore cannot come from the
agent's distribution — it has to come from the *substrate* being in a permissive state
only where recent activity has marked it. That is precisely the logic of synaptic tagging
and capture and of neuronal memory allocation: the agent supplies a resource, and activity
decides where the resource is captured.

## 3. The hypothesis's own internal tension — and why that is its main prediction

SE1–SE3 ask for **more** plasticity in the addressed representations. SE6–SE7 ask for
plasticity to stay **low** everywhere else — including for material processed seconds
apart in the same session, and (SE7) for the addressed material itself once its value has
passed.

Any mechanism whose action is a *tonic shift in a plasticity parameter* — threshold,
gain, transcription, translation — satisfies SE1–SE3 and violates SE6–SE7 **by
construction**. It cannot know which synapses matter, because nothing about its action
depends on which synapses were active.

This gives the hypothesis a strong structural prediction:

> The viable mechanism space is restricted to mechanisms whose *effect* is **gated by
> activity**, rather than determined by exposure alone.

That is a real, falsifiable claim about where to look. It is a **prediction, not a
filter**, and the distinction is not pedantic — an earlier version of this file got it
wrong in a way worth recording.

### 3.1 Why this does *not* license excluding a candidate (correction, 2026-09-18)

This section previously said the prediction "rules out a whole class of candidate before
any ranking runs — including several of this repository's seed targets whose only
established action is to raise a plasticity or consolidation parameter tonically." A
red-team pass found three things wrong with that, and it is retracted:

1. **It inverted the file's own guard.** §8 forbids this hypothesis from licensing target
   selection on conceptual fit. Exclusion is selection with the sign reversed. A framework
   that may not promote a candidate on elegance may not demote one on elegance either.
2. **It converted "not measured" into "does not exist".** "Whose *only known* action is
   tonic" is a statement about this repository's coverage, not about a molecule. Every
   criterion SE1–SE7 is recorded as `not_assessed_in_repository` or
   `partially_addressed` — nothing here has been assessed for activity-gating at all. This
   is precisely the measured-absence/absence-of-measurement confusion the project treats
   as its recurring bug class, and the elegance of the framework is exactly what made it
   invisible.
3. **§2.2 refutes it directly.** The tagging-and-capture logic is that *the agent supplies
   a resource and activity decides where it is captured*. That describes a **tonically
   acting agent producing selective outcomes** — the very thing the exclusion would rule
   out. A translation-capacity mechanism (`EIF2B_COMPLEX`, `EIF2S1`) is tonic in action and
   could still be captured selectively. Whether it is, is an empirical question nobody here
   has answered.

The corrected form is narrower and still useful:

> A mechanism whose action is tonic satisfies SE1–SE3 but is **predicted to fail SE6**
> *unless* the resource it supplies is captured in an activity-dependent way. Whether
> capture is activity-gated is the measurement that decides it — and for every target in
> this repository, that measurement has not been made.

That still tells us where to look. It no longer pretends to tell us what to discard.

## 4. What it would take to falsify it

Per-criterion falsifiers are in the YAML. The hypothesis as a whole fails if any of these
hold:

1. **Selectivity is unobtainable.** Every mechanism that raises prioritised retention
   raises incidental retention proportionally, so `selectivity_gain` is never
   distinguishable from zero. SE6 is then not a design requirement but a physical
   constraint.
2. **The contrast is already maximal.** Healthy adult encoding is already near a
   selectivity ceiling set by attention, and there is no headroom to amplify. The
   hypothesis would then be correct in principle and empty in practice — the same shape
   of result as Sprint 1's finding on the POWER factor.
3. **Selectivity and structure come apart.** SE4 is satisfied only by mechanisms that
   violate SE6 — i.e. schema extraction requires broad encoding followed by selection,
   rather than selective encoding up front. This is the possibility I would bet on as the
   most likely partial refutation, and it is testable.
4. **Forgetting proves load-bearing in a way that caps the benefit.** Satisfying SE1–SE5
   reliably degrades SE7 enough to produce net interference. That would be a refutation of
   the design target, not a tuning problem.

## 5. Where SE4 is weakest, stated plainly

SE4 — encode the latent structure rather than the surface — has **no established
molecular control parameter**. There is no known mechanism that selectively favours schema
extraction over veridical detail, and it is entirely possible that this trade-off is
architectural (a property of how hippocampal and cortical systems divide labour over time)
rather than pharmacological.

SE4 is therefore the hypothesis's most likely point of failure *by underspecification*
rather than by refutation. It should not be quietly dropped, because it is doing real work
in the specification: without SE4 the hypothesis reduces to "remember the important things
better", which is a much less interesting claim than "acquire reusable structure from few
episodes".

## 6. How this connects to what the repository already holds

The honest position is that this hypothesis is **ahead of the evidence**, and the
repository says so:

* Sprint 1's ranking found **no seed target with causal-gene attribution above level 2**,
  17 of 27 at level 0, and `tier_1_analyse_next` empty.
* The targets that bear on SE2 and SE3 — `CRTC1` (allocation, CREB coactivation),
  `EIF2B_COMPLEX` and `EIF2S1` (translation control), `HDAC2` (transcriptional gating),
  `GRIN2B` (NMDA-dependent plasticity) — are exactly the ones whose adult human evidence
  is thinnest. Sprint 2's registry search found **no registered trial at all** for
  `CRTC1`, and the Sprint-1 audit downgraded or deprioritised several others.
* No criterion SE1–SE7 currently has a repository claim that directly addresses it. The
  YAML records each as `not_assessed_in_repository` or `partially_addressed`, which is a
  coverage statement, not a verdict.

This is the correct relationship between a compass and a map: the compass says which way
to walk, and the map still shows very little ground covered.

## 7. What changes because of this hypothesis

Concretely, and these are the reasons to keep it rather than admire it:

1. **A new endpoint requirement.** Evidence about a candidate is `not_assessable` for this
   hypothesis unless prioritised and incidental material were measured separately. Add
   that distinction when grading `transfer_breadth` and `above_baseline_enhancement`.
2. **A measurement demand, not an exclusion.** For a candidate whose known action is tonic
   — a global shift in threshold, gain, transcription or translation — the open question
   becomes whether the resource it supplies is *captured* in an activity-dependent way.
   That is a specific thing to go and measure. It is **not** grounds for discarding the
   candidate, and §3.1 records why an earlier version of this file was wrong to say it was.
3. **A search direction.** Prioritise mechanisms where activity supplies the address:
   tagging-and-capture, allocation by excitability state, and gating of the encoding state
   itself.
4. **A safety framing that is not an afterthought.** SE7 makes forgetting a *requirement*,
   not a side effect to be minimised. A candidate that abolishes normal weakening fails
   the specification even if every retention measure improves.

## 8. Guards

The attractiveness of a well-formed specification is itself a hazard. Four guards, also
encoded in the YAML:

* It must **not be promoted above the human genetic evidence**. It changes nothing about
  the fact that no target currently has a defensible adult causal case.
* It must **not license target selection on conceptual fit**. A mechanism that fits SE1–SE7
  elegantly and has no adult human causal evidence is a hypothesis, not a candidate.
* The red team should audit claims citing this file **with extra suspicion**, precisely
  because an elegant framework generates confirmatory reading.
* No output derived from it may contain a dose, regimen, route or sourcing path.

---

*Cross-references:*
[`goal_gated_plasticity_retrieval.md`](goal_gated_plasticity_retrieval.md) — the companion
hypothesis, which asks where the deficit *is* rather than what a mechanism must *do*, and
whose **C1 (gating)** channel is the goal-level counterpart of SE2. Held together, the two
say something neither says alone: the problem is not that the brain cannot encode deeply
and selectively, but that **volition is a poor addressing mechanism and salience is a good
one we do not control**. They could still come apart — a mechanism that merely sharpens
existing gating would satisfy SE1–SE7 while leaving the control gap untouched.
Also `THEORY.md` §2 (OPEN → WRITE → SELECT → LOCK), of which this is a
sharper and more falsifiable statement of the SELECT and LOCK phases; the Sprint-2 brief's
activity-gated plasticity theory node, with which it shares the activity-as-address idea;
and `reports/project_truth_table.md`, where it appears as a tracked hypothesis with a
status and a next kill test.
