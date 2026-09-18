# The Goal-Gated Plasticity & Retrieval Hypothesis

**Status: THEORY NODE.** Not a finding, not a validated mechanism, not a recommendation
about any compound, device or protocol. Recorded 2026-09-18, originating from the project
lead. Machine-readable form:
[`goal_gated_plasticity_retrieval.yaml`](goal_gated_plasticity_retrieval.yaml).

**Computational-only.** Everything below specifies what a limitation would have to *be*,
so that candidate mechanisms can be evaluated computationally. Nothing here is a dose, a
device, a regimen or a protocol (`docs/COMPUTATIONAL_ONLY_POLICY.md`), and "broader than a
pill" is **not** a licence to propose hardware or self-experimentation — see §8.

---

## 1. The question, and the hypothesis

> **The question.** How do we give a human more control over what gets learned, what
> becomes permanent, and what can later be reconstructed on demand?
>
> That is broader than IQ, broader than memory, and broader than a pill.
>
> **The hypothesis.** Human cognitive capacity is limited partly by an **imperfect
> interface between conscious goals and the brain's plasticity and retrieval machinery**.
>
> The brain can already perform extraordinary one-shot encoding, abstraction and
> cue-triggered reconstruction. The problem is that we cannot reliably issue a command
> like: *this representation is important → encode its structure deeply → consolidate it →
> make it retrievable indefinitely.*

## 2. Why this is a different claim, not a restatement

Almost every enhancement programme — including this repository's own seed list — treats
cognition as **capacity-limited**: not enough plasticity, not enough consolidation, not
enough metabolic headroom, too much of some brake. The intervention follows directly:
raise the capacity.

This hypothesis says the binding constraint is somewhere else entirely. It is a claim
about **controllability**, and it relocates the deficit from the machinery to the
*interface* to the machinery:

| | capacity framing | interface framing |
|---|---|---|
| What's missing | the ability to encode deeply | the ability to *direct* deep encoding at will |
| Evidence that would support it | ceiling effects, resource depletion | the same person encoding far better when salience is **imposed** than when it is merely **intended** |
| Intervention target | the plasticity parameter | the addressing channel |
| What "more" means | more plasticity everywhere | the same plasticity, aimed |

The two framings make **opposite predictions about headroom**. Under the capacity framing,
peak observed performance is near the system's limit. Under the interface framing, peak
observed performance — achieved involuntarily, under conditions the person did not choose —
is a **demonstration of available headroom that voluntary control cannot reach**.

### 2.1 The appeal to existence proofs, and its honest status

The hypothesis leans on a class of phenomena in which encoding, consolidation or retrieval
is dramatically better than ordinary voluntary performance: vivid one-shot encoding of
surprising or emotionally charged events, expert chunking within a domain, and
cue-triggered reconstruction of material the person could not deliberately recall.

**This repository holds no evidence for any of these.** They are named here as the
phenomena the hypothesis appeals to, not as established facts within the project. Treating
them as established would be exactly the error the selective-encoding node's guards warn
about, arriving through a different door — an elegant frame recruiting half-remembered
literature as support. Each is recorded as `appealed_to_not_verified` in the YAML, and each
would need retrieval, verification and a source record before it could carry any weight.

The hypothesis's core structure does **not** depend on which of them survives. It depends
only on the claim that **involuntary performance exceeds voluntary performance**, which is
a measurable quantity (§3) rather than a literature appeal.

## 3. The decisive quantity

Where the selective-encoding hypothesis measures a *contrast between materials*, this one
measures a *contrast between routes to the same material*:

```
control_gap = performance_when_salience_is_IMPOSED
            − performance_when_salience_is_merely_INTENDED
```

Same person, same material, same delay. One condition makes the material matter by
external means the participant does not control; the other asks the participant to make it
matter by intending it.

Three consequences, and they are the useful part:

* **`control_gap > 0` is the hypothesis.** It quantifies the headroom that exists in the
  machinery and is unreachable by voluntary command. The larger it is, the more the
  limitation is an interface problem.
* **`control_gap ≈ 0` refutes it**, and does so in a way that matters: it would mean
  voluntary control already reaches whatever the machinery can do, so the deficit is
  capacity after all and the whole framing collapses back into the conventional one.
* **It is measurable without any intervention.** This is the hypothesis's best property.
  Its central claim can be tested in unmodified humans, before any mechanism is
  identified and without anything being administered. Almost nothing else in this
  repository has that.

## 4. Three control channels, not one

The question names three things, and they are separable failures requiring separable
mechanisms. Conflating them is how "memory enhancement" becomes an incoherent target.

| | Channel | The command that cannot currently be issued | Fails as |
|---|---|---|---|
| **C1** | **Gating** — what gets learned | *this, not that* | encoding the wrong things; inability to make intended material stick |
| **C2** | **Persistence** — what becomes permanent | *keep this indefinitely* | the forgetting curve applying to material you decided mattered |
| **C3** | **Retrieval** — what can be reconstructed on demand | *give it back now* | knowing that you know, and not being able to produce it |

**C3 is the channel this project has most neglected, and it may be the most tractable.**
The repository's entire seed list is oriented at encoding and consolidation. But a trace
that exists and cannot be addressed is, from the person's point of view, identical to one
that was never stored — and the failure is not obviously a *storage* failure at all. If
C3 is where the practical deficit lies, then most of this repository's targets are aimed
at the wrong channel.

The three channels also fail on **different timescales** — C1 during the episode, C2 over
hours to days, C3 at an arbitrary later moment — which means one intervention is unlikely
to address all three, and a candidate should be required to say which channel it claims.

## 5. Relationship to the Selective Encoding Hypothesis

These are complementary, and the distinction is worth keeping sharp
([`selective_encoding_hypothesis.md`](selective_encoding_hypothesis.md)):

* **Selective Encoding** is a specification of the **desired phenotype** — what a mechanism
  must *do*: raise prioritised encoding without raising incidental encoding.
* **Goal-Gated Plasticity & Retrieval** is a claim about **where the deficit is** — an
  interface, not a capacity — and it adds the **retrieval** channel, which selective
  encoding touches only at SE5.

They meet at one point and it is the important one: **SE2 ("use activity as the address")
is the mechanism-level statement of C1.** Selective encoding says addressing must come from
activity rather than from a drug's distribution; this hypothesis says the *goal* is what
should set that activity, and that the goal-to-activity link is the weak step.

Held together, they say something neither says alone:

> The problem is not that the brain cannot encode deeply and selectively. It is that
> **volition is a poor addressing mechanism**, and salience is a good one that we do not
> control.

Where they could come apart, which is what makes them worth keeping separate: selective
encoding could be satisfied by a mechanism that improves selectivity *without* any increase
in voluntary control — for example one that simply sharpens whatever gating already
operates. That would satisfy SE1–SE7 and leave `control_gap` untouched.

## 6. What would falsify it

1. **No control gap.** Measured performance under imposed salience does not exceed
   performance under intended salience, once effort, arousal and time-on-task are matched.
   The headroom is then imaginary.
2. **The gap is a resource, not an interface.** Imposed-salience encoding turns out to
   *spend* something — and to degrade later encoding proportionally. Then the machinery is
   budgeted, not merely badly addressed, and the ceiling is real.
3. **The gap is already closable behaviourally.** Existing strategies (elaboration,
   spacing, testing, deliberate structuring) close most of it. The hypothesis would then be
   true and uninteresting — the interface exists, it is called *studying*, and it works.
   **This is the most likely partial refutation and it should be tested first**, because it
   is the cheapest and it would reframe the whole programme.
4. **The channels do not separate.** C1, C2 and C3 turn out to be one mechanism, so
   "control over what becomes permanent" is not a distinct thing to intervene on.
5. **Volitional access is architecturally impossible.** There is no channel by which a goal
   state could address plasticity at representational resolution — the required information
   is not available to the systems that would have to use it.

## 7. What changes because of this hypothesis

1. **A new measurement that needs no intervention.** `control_gap` can be estimated in
   unmodified humans. It should be estimated *before* any mechanism is pursued, because its
   size bounds the entire opportunity.
2. **Candidates must declare a channel.** A target claiming to help should say whether it
   acts on C1, C2 or C3. "Improves memory" is not a channel.
3. **Retrieval becomes a first-class target class.** The repository currently has none, and
   under this framing that is a structural gap rather than an oversight.
4. **Non-pharmacological mechanisms become admissible as *objects of computational
   analysis*.** If the deficit is an interface, then behavioural and training routes are
   candidate mechanisms in exactly the same sense as molecular ones, and should be analysed
   by the same contract — same evidence standards, same red team, same refusal to treat
   conceptual fit as evidence. (Analysed. Not performed — see §8.)
5. **It offers an alternative to Sprint 1's negative result.** Sprint 1 found the POWER
   envelope may not be limiting in healthy adults. An interface limit is precisely the kind
   of constraint that would remain binding even when no capacity is exhausted, which makes
   this hypothesis a live successor rather than a change of subject.

## 8. Guards

* **"Broader than a pill" is not a licence to propose hardware.** The phrase widens the
  space of mechanisms that may be *analysed*; it does not widen what may be *done*. No
  output derived from this file may propose a device, an implant, a stimulation protocol,
  a training regimen to follow, a dose, a route, or any form of self-experimentation. The
  computational-only policy applies unchanged and applies with more force here, because
  this framing is the one most likely to invite a neurotech proposal.
* **The existence proofs are unverified.** §2.1's phenomena are appealed to, not
  established, and no claim in this repository currently supports any of them. They must be
  retrieved and verified before they carry weight, and the hypothesis must not borrow
  credibility from them meanwhile.
* **It must not be promoted above the human genetic evidence.** No target has adult causal
  attribution above level 2, and an attractive reframing does not change that.
* **It must not license target selection on conceptual fit — in either direction.** A
  mechanism that fits the interface framing elegantly and has no adult human evidence is a
  hypothesis, not a candidate; and a mechanism that fits it badly may not be demoted for
  that reason. This is the exact error the selective-encoding node had to retract
  (`selective_encoding_hypothesis.md` §3.1), and it is recorded here in advance rather
  than after.
* **Red team should audit claims citing this file with extra suspicion**, for the same
  reason as its companion: a well-formed frame generates confirmatory reading.

---

*Cross-references:* [`selective_encoding_hypothesis.md`](selective_encoding_hypothesis.md)
(the phenotype specification, of which C1 is the mechanism-level counterpart at SE2);
`THEORY.md` §2 (OPEN → WRITE → SELECT → LOCK), whose phases map onto C1–C3;
[`../reports/project_truth_table.md`](../reports/project_truth_table.md), where this
appears as a tracked hypothesis with a status and a next kill test.
