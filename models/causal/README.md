# Causal models — interfaces only (Sprint 1)

## The one thing to read before anything else

**No causal effect is estimated anywhere in Sprint 1.**

The ranking model in `models/ranking/` is an **evidence-accounting device**, not a
causal estimator. It reads ordinal grades that other agents assigned to other
people's published evidence, maps those grades to subjective Beta distributions, and
aggregates them under declared weights. At no point does it identify a causal effect,
estimate an effect size, or compute anything that could be read as "how much would
modulating this target change cognition". It cannot: it never touches individual-level
data, never fits a model to observations, and its inputs are integers between 0 and 4.

A high `P(causal cognition relevance)` in `reports/target_ranking_v0_1.csv` means
*the evidence base for a causal claim is comparatively more complete and more
favourable*. It does not mean a causal effect has been estimated, and it does not
license the sentence "this target causally affects cognition".

This directory specifies the interfaces for the Sprint-2 work that would actually
attempt identification, so that the boundary between accounting and estimation is
recorded before anyone crosses it.

---

## Why the distinction matters here specifically

This project's whole failure mode is a confident chemistry programme aimed at a target
whose causal case was never established (`ROADMAP.md`, opening paragraph). The most
likely route to that failure is not a bad estimate — it is a **ranking mistaken for an
estimate**. A table of numbers between 0 and 1 with six column headings beginning
"P(" reads like posterior probabilities. It is not. The guardrails:

| Guardrail | Where |
|---|---|
| `status: PRELIMINARY` on every row | `src/blueprint/ranking/report.py` |
| `calibration_status: uncalibrated_subjective` on every row | same |
| "not a claim about biology" in the report sidecar | `build_meta()` |
| No hand-written probability outside a labelled spec file | contract P3, rule V9 |
| This document | you are reading it |

---

## What each Sprint-2 method can and cannot identify

`causal_model_interface.yaml` is the machine-readable form of this table; the prose
below is what a reviewer should read first.

### Colocalisation (eQTL/sQTL/pQTL × GWAS)

**Identifies:** whether a trait association signal and a molecular signal at the same
locus are consistent with sharing a single causal variant.

**Does not identify:** that the gene mediates the trait. Colocalisation is a statement
about two *signals*, not about a mediation path. A shared causal variant is
compatible with the gene being irrelevant and the variant acting on something else in
the region, and with the molecular phenotype being downstream of the trait rather than
upstream.

**Assumptions that break it:** a single causal variant per trait per locus (the
standard formulation); the tissue/cell type assayed being the causal one; and adequate
power in the molecular dataset. Brain eQTL sample sizes are small relative to
cognitive GWAS, so a null colocalisation is very often a power statement. Bayesian
colocalisation posteriors are also sensitive to the prior on shared causality, which
is a choice, not a datum.

**How it is recorded here:** as a source-reported model output with
`derived_from` naming the method and its data version, never as this project's
probability (contract P3; `docs/API_RECIPES.md` §5.2 says the same about Open Targets
L2G scores).

### Mendelian randomisation

**Identifies:** under three assumptions, the causal effect of an exposure on an
outcome, using genetic variants as instruments.

**The three assumptions, and which one is most at risk here:**

1. **Relevance** — the instrument is associated with the exposure. Testable, and
   usually satisfiable.
2. **Independence / exchangeability** — the instrument is not associated with
   confounders of the exposure-outcome relation. Population structure and assortative
   mating both threaten it; in cognitive phenotypes, assortative mating is
   substantial and is *not* fixed by standard ancestry adjustment.
3. **Exclusion restriction** — the instrument affects the outcome only through the
   exposure. **This is the assumption most at risk for every exposure this project
   cares about**, because brain-expressed genes are overwhelmingly pleiotropic and
   because a variant in a cognition-associated locus plausibly acts through many
   routes at once. It is also the assumption that cannot be tested directly.

**Standard sensitivity analyses, all of which must be reported together:**
MR-Egger intercept (directional pleiotropy), weighted median (validity under up to
half of instrument weight being invalid), weighted mode, MR-PRESSO (outlier
detection), Steiger directionality filtering, leave-one-out by instrument,
heterogeneity statistics (Cochran's Q, I²), and — for anything involving an
educational or behavioural exposure — within-family MR, which is the only design that
removes assortative-mating and population-structure confounding rather than adjusting
for it.

**Does not identify:** a *modifiable* effect. MR estimates the consequence of lifelong
genetically-determined difference in the exposure, which is not the consequence of
changing the exposure in an adult. This distinction is the project's own D1-versus-D2
distinction (contract P4: development is not adulthood), and it is the single most
common misreading of MR in this literature. MR also cannot identify effects of
exposures with no valid instrument, which describes most of the state variables in
`state_model/`.

### Structural causal model of the state dynamics

The state model is `X(t+1) = F(X(t), U(t), E(t), Θ) + noise` (README §3, `THEORY.md`).
As a causal object this is a discrete-time dynamical SCM: `X` latent
biological/cognitive state, `U` intervention, `E` experience/environment/task, `Θ`
slower individual parameters, and the noise term carrying everything unmodelled.

**What it would identify, if it could be fitted:** the effect of an intervention `U`
on the state trajectory — including the parts that matter and that a single-timepoint
effect size cannot express: whether an effect persists, whether it saturates, whether
it trades against a safety variable, and whether the system returns to its previous
operating point.

**Why it is not fitted in Sprint 1, and the identifiability problem:** `X` is latent
and measured only through proxies; several state variables have no human proxy at all
(`ontology/state_variables.yaml` records `measurability` per variable precisely so
this cannot be glossed over); `Θ` is confounded with `X(0)`; `F` is unknown in form,
so any fit is a joint claim about the functional form and the parameters; and the
available public longitudinal data has neither the sampling frequency nor the
intervention variation to separate a genuine state change from measurement drift or
practice effects. `ROADMAP.md` Sprint 3 puts a no-free-lunch predictive baseline
before anything mechanistic for exactly this reason, and states that unidentifiable
parameters are demoted regardless of biological appeal.

**The honest summary:** the state model is currently a *specification of what would
need to be identified*, and its main present-day use is negative — it says which
quantities the project is not entitled to talk about yet.

---

## What would move a target from "accounted" to "estimated"

Recorded here so that the bar cannot drift downward:

1. A causal-gene attribution that is not `gwas_association_only` — fine-mapping or
   colocalisation or an allelic series (`ROADMAP.md` Sprint 2 exit criterion).
2. An MR estimate with all of the sensitivity analyses above reported, including a
   within-family design where the exposure is behavioural, and an explicit statement
   of which assumption is most at risk.
3. An adult-onset perturbation result, because a lifelong-difference estimate does not
   answer the adult-modifiability question at all.
4. A human proxy for the state variable the mechanism is supposed to move, so that the
   claim is about a measurable quantity.

Until all four exist for a target, the correct output is a rank with an interval and a
named next analysis — which is what `reports/target_ranking_v0_1.csv` is.

---

## Boundaries that apply to everything in this directory

* **Computational only.** Nothing here performs, plans, designs or recommends any
  wet-lab, in-vitro, ex-vivo, animal or human experiment, including
  self-experimentation (`docs/COMPUTATIONAL_ONLY_POLICY.md`). Published results are
  ingested as evidence; ingestion is never endorsement.
* **No protocol, dose, route or regimen** appears in any output of any model in this
  repository, and none may be derived from one.
* **Safety is a constraint, not a cost.** No causal or optimisation model here may
  trade a safety variable against a benefit; the ranking model enforces this with
  caps rather than weights, and Sprint-4 multi-objective work is specified the same
  way (`src/blueprint/pharmacology/interfaces.py`).
* **Every model output records its calibration status.** A number whose calibration
  status is unstated is not publishable from this repository.
