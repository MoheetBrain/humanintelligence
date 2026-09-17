# Phylogenetic controls: what they are, what they fix, and what none of them fix

**Owner:** `agent:comparative` · **Sprint 1** · written 2026-09-17

This is the method document for the comparative atlas. It exists because the dominant
failure mode of the comparative-cognition literature is not fraud or incompetence — it is
treating species as independent data points. Everything below follows from that one
problem.

---

## 1. The problem: species are not independent observations

An ordinary regression assumes its data points are independent draws. Species are not.
Two species resemble each other partly because they inherited the resemblance from a
shared ancestor, and the closer they are, the more of the resemblance is inherited.

The practical consequences are severe and they all point the same way — towards
**apparent** evidence:

- **Pseudoreplication.** Sample 24 parrots and songbirds and you may have measured one
  ancestral character state 24 times. The n looks like 24; the number of independent
  evolutionary events may be 2. `CLM:comparative:NEURON_SCALING:001` is exactly this
  shape: 28 avian species, of which 11 are parrots and 13 are songbirds.
- **Clade-driven fits.** A relationship fitted across a taxonomically lopsided sample can
  be a within-clade relationship with outgroups along for the ride. In
  `CLM:comparative:HCN1:003`, five of the nine non-human species (mouse, gerbil, rat,
  guinea pig, rabbit) are Glires, and the headline conductance exponent rests on n = 5,
  all of them Glires. In `CLM:comparative:SELF_REGULATION:001`, 23 of 36 species are
  primates, and the authors said so themselves.
- **Inflated significance.** Non-independence shrinks the true degrees of freedom, so an
  uncorrected p-value is smaller than it should be, sometimes by a lot.
- **More species looks like better evidence.** This is why the atlas needs a hard rule
  rather than a caution: without one, a 28-species uncontrolled study outranks a
  4-species controlled one in every automated summary.

---

## 2. The controls that exist, and what each one actually buys

| Control | What it does | What it fixes | What it does not fix |
|---|---|---|---|
| **PGLS** (phylogenetic generalised least squares) | Regression with a residual covariance matrix derived from the phylogeny, usually under Brownian motion or Ornstein–Uhlenbeck | Non-independence of residuals; restores honest degrees of freedom and standard errors | Wrong tree, wrong branch lengths, wrong evolutionary model; measurement error; construct validity |
| **Phylogenetic mixed model** | Phylogeny as a random effect, so within- and between-species variance are separated | As PGLS, plus repeated measures per species and unbalanced designs; can carry measurement error explicitly | Same model-misspecification risks; needs more data than most comparative datasets have |
| **Sister-taxa contrasts** / independent contrasts | Compares closely related pairs that differ in the trait | Removes most shared-ancestry confounding with minimal model assumptions; the cleanest logic available | Throws away most of the data; needs sister pairs that actually differ; a single pair is a single observation whatever the species count |
| **Ancestral state reconstruction** | Infers ancestral values, so gains and losses can be counted | Lets "convergence" be distinguished from "shared inheritance" — the distinction that makes a convergence claim a convergence claim | Reconstructions are highly uncertain deep in a tree, and uncertainty is routinely dropped when the reconstruction is reused downstream |
| **Allometric / body-size correction** | Regresses the trait on body or neuron size and works with residuals | Genuine size confounding, which is usually the largest single confound | **Nothing phylogenetic.** This is the most common substitution in practice and it is not a phylogenetic control. `CLM:comparative:HCN1:003` has a real and careful allometric control and no phylogenetic control at all. |

---

## 3. What none of them fix

A perfectly specified PGLS still cannot repair any of the following, and this atlas
treats all four as live on every claim:

1. **Construct validity across clades.** A phylogenetic model corrects the error
   structure of the comparison; it says nothing about whether the thing being compared is
   the same thing. Whether a cylinder detour task measures the same capacity in a pheasant
   chick, a raven and a gorilla is a question about psychology, not statistics.
   `CLM:comparative:SELF_REGULATION:003` is the atlas's worked example: the task's scores
   partly index acquisition of a motor routine, and in the original multi-species dataset
   four of seven bird species improved measurably across the ten test trials. The
   flagship phylogenetically-modelled comparative-cognition result therefore rests on an
   instrument whose construct validity has been challenged by direct experiment. No
   amount of phylogenetic correction touches this.

2. **Measurement heterogeneity.** Different laboratories, protocols, fixatives,
   antibodies, counting methods and brain-region definitions. This is not hypothetical
   here: `CLM:comparative:NEURON_SCALING:005` records a roughly fourfold disagreement
   between the isotropic fractionator and stereology on the cortical neuron count of the
   *same* species. When two accepted methods disagree fourfold, a cross-species
   regression on pooled published counts is measuring method as much as biology.

3. **Publication and sampling bias towards charismatic species.** The comparative panel
   is not a random sample of animals. It is a sample of animals someone already thought
   were interesting, in which positive results are more publishable. Corvids, parrots,
   dolphins, elephants and octopuses are in the literature *because* the narrative
   existed first. A phylogenetic model applied to a biased sample returns a
   well-calibrated estimate of a biased quantity.

4. **The species-versus-individual leap.** A relationship that holds across species says
   nothing about variation within one. Absolute brain volume predicting task score across
   36 species is not evidence that brain volume predicts cognitive ability among humans,
   and this project is about intervening within a species.

---

## 4. The rule this atlas applies

> **A claim whose proposition is a between-species comparison and which reports
> `context.phylogenetic_control` of `none` or `not_reported` may not be graded above
> ordinal level 2, however many species it covers and however large the reported
> difference. The same cap applies at facet level — but only to the field that favours
> the target, per contract §5.4.**

### 4a. The cap is polarity-aware (contract §5.4)

This atlas got this wrong first time, and the correction matters more than the original
rule. The first version applied the cap to `level` on every facet. For
`cross_species_convergence` that is right. For `human_lineage_divergence_risk` it is
backwards, because that facet is **inverse-polarity**: it feeds dimension D6 *inversely*,
so suppressing it makes a target look **more** translatable. Applying a methodological
cap to a risk facet converts "we measured this badly" into "the risk is smaller", which
is the opposite of caution.

`agent:comparative` escalated rather than resolving it unilaterally, and contract §5.4
now states the general rule:

| Facet polarity | Cap constrains | Why |
|---|---|---|
| **Normal** (`cross_species_convergence`, and most facets) | `level` | weak method cannot establish strong **support** |
| **Inverse** (`human_lineage_divergence_risk`, `safety_liability_burden`, `developmental_confound_risk`) | `counter_level`, **never** `level` | weak method cannot establish the **absence of a risk** |

The symmetric consequence is that `counter_level` on a *normal*-polarity facet is
**not** capped: weak comparative method is no reason to discount evidence *against* a
target. That is why `atlases/comparative/assessments/HCN1.yaml` carries
`cross_species_convergence` with `level: 2` (capped, correctly) and `counter_level: 3`
(uncapped, resting on the same body of evidence as the divergence-risk level).

`models/ranking/facet_rubric_v0_1.yaml` is the source of truth for polarity once
`agent:integration` publishes it; the checker reads it automatically if present and
otherwise falls back to the contract §5.4 table.

**What changed in this atlas's records:** `HCN1`'s `human_lineage_divergence_risk`
restored from 2 to **3**. `HCN1`'s `cross_species_convergence` `counter_level` raised
from 2 to **3**. `KCNQ2`, `KCNQ3` and `RGS14` levels unchanged — their levels were set by
evidentiary distance, not by the cap — with two inaccurate `limiting_factor` sentences
corrected. No claim-level grade changed: claims have no polarity, so the claim-level cap
is unaffected by §5.4.

The vocabulary is `schemas/claim.schema.json` (`context.phylogenetic_control`), which is
authoritative: `none` · `outgroup_comparison` · `sister_taxon_comparison` ·
`phylogenetic_comparative_model` · `ancestral_state_reconstruction` · `other` ·
`not_reported`. `agent:ontology` added the field, plus
`phylogenetic_control_basis` and `species_count`, in response to
`docs/blackboard/schema_change_requests/comparative-001.yaml`; this atlas then conformed
to the enum it chose rather than the one the request proposed.

**`not_reported` is capped alongside `none`.** Not knowing whether ancestry was modelled
cannot count for more than knowing it was not — an unverified control is not a control.
The two values stay distinct because conflating "the authors report an uncontrolled
analysis" with "the retrieved text does not say" would be the false precision contract
principle P3 forbids.

Three riders:

- **`none` and `not_reported` require a stated alternative.** Every such claim must name at least one
  alternative explanation from: shared ancestry, allometry or body-size scaling, sampling
  bias, publication bias towards charismatic species, or measurement heterogeneity. This
  is enforced, not requested.
- **Every value must say how it was established.** `context.phylogenetic_control_basis`
  records which methods sentence was read. `none` is used only where the absence is
  established — either from the methods text (`CLM:comparative:NEURON_SCALING:001`,
  reduced major axis regression to power functions; `CLM:comparative:HCN1:003`, ordinary
  log-log regression and ANCOVA) or because two species or one specimen makes a control
  impossible. `not_reported` is used where only an abstract was retrievable.
- **Single-species claims are exempt.** A claim with `context.species_count == 1` makes no
  between-species comparison, so shared ancestry is not a confound and there is nothing
  for a phylogenetic model to control. `CLM:comparative:SELF_REGULATION:003` is graded 3
  under this exemption: it is a randomised experiment in one species plus a within-species
  reanalysis, converging on a claim about a *measurement instrument*. A missing
  `species_count` (`null`) is **not** exempt — absence of a count is not evidence of a
  single species.

The rule is executable, not rhetorical: `pipelines/comparative/check_phylogenetic_cap.py`
re-derives it from the claim and assessment files and exits non-zero on any violation. The
red team should run it rather than trust this document — **including `--legacy-rule`,
which reinstates the pre-§5.4 behaviour and is expected to FAIL against the corrected
records.** That failure is the regression guard: it demonstrates mechanically that the old
uniform cap is now a violation rather than merely deprecated.

```
$ .venv/bin/python pipelines/comparative/check_phylogenetic_cap.py
21 comparative claims: 3 report a phylogenetic control, 15 are between-species with
none/not_reported and are capped at level 2.
cap respected by every claim and facet.                                    # exit 0

$ .venv/bin/python pipelines/comparative/check_phylogenetic_cap.py --legacy-rule
1 cap violation(s):
  - HCN1.yaml facet human_lineage_divergence_risk: level 3 exceeds the cap of 2; every
    supporting claim is uncontrolled (...)                                 # exit 1
```

---

## 5. What this means for the sprint-1 evidence base

Of 21 comparative claims, **3** report any phylogenetic control:

- `CLM:comparative:SELF_REGULATION:001` — `other`. The abstract states phylogenetic
  analysis was used; the estimator (PGLS versus phylogenetic mixed model) was not
  extractable, so `other` rather than `phylogenetic_comparative_model`.
- `CLM:comparative:SELF_REGULATION:002` — `other`. A phylogenetic regression supplies
  body-mass residuals, but the performance model itself carries no phylogenetic term and
  the AIC comparison favoured the absolute-volume model, which has none.
- `CLM:comparative:HAR:001` — `outgroup_comparison`. A designed human-versus-chimpanzee
  comparison, over a region set defined by a multi-species substitution test.

The remaining 18 are `none` (14) or `not_reported` (4). **Not one claim in this atlas
uses PGLS, a phylogenetic mixed model, sister-taxon contrasts or ancestral state
reconstruction.**

That is the honest state of the evidence, and it has a direct structural consequence:
**this atlas cannot currently distinguish convergence from shared inheritance for any
mechanism it records.** Distinguishing them requires ancestral state reconstruction, and
no source curated here performed one. Where this atlas says "convergent", read "present
in more than one lineage, by an unknown evolutionary route".

`CLM:comparative:AVIAN_CIRCUIT:001` makes the cost concrete. A repeated column-like
circuit in the pigeon and barn owl pallium is either (a) an independent solution to a
computational problem, which would be strong evidence that the architecture matters, or
(b) a conserved amniote pallial plan, which would be evidence of inheritance and nearly
the opposite conclusion. Two species and no ancestral reconstruction cannot tell them
apart, which is why that claim is graded 1 rather than 3.
