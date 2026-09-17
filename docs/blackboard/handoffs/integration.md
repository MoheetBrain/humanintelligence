# Handoff — `agent:integration` (Causal Integration / Ranking)

**Stage 2 complete.** The ranking has been run over all 27 audited targets and
published: `reports/target_ranking_v0_1.csv`, its sidecar, and the narrative at
`reports/integration_v0_1.md`. 388 of my tests pass; 0 ownership violations; 0 validator
violations in my lane; reruns are byte-identical.

**The headline is a negative result.** No target in this repository currently has a
defensible causal case for adult human cognitive enhancement: 17 of 27 targets sit at
causal-gene attribution level 0, nothing in the cohort exceeds level 2, the highest D1
median is 0.544, and `tier_1_analyse_next` is **empty** — no target ranks in the top
quartile even at the pessimistic end of its own rank interval. §1 of the narrative leads
with this. The table's job is to say where further *computational* analysis is better
value, and it does not carry a claim about biology.

Sections 3 onward below describe the model as built in Stage 1 and remain current.

---

## 1. Tests — real counts

```
.venv/bin/python -m pytest tests/test_ranking_*.py tests/test_uncertainty_*.py -m "not network" -q
382 passed in 7.21s
```

| File | Tests | What it holds the model to |
|---|---:|---|
| `test_ranking_monotonicity.py` | 66 | better evidence never scores worse; worse never scores better; per facet, per level transition, analytic and sampled |
| `test_ranking_polarity_caps.py` | 63 | contract §5.4 polarity-aware caps and the `symmetric_caps` counterfactual |
| `test_ranking_spec_consistency.py` | 37 | rubric ↔ spec ↔ contract agreement, plus every failure path |
| `test_ranking_pharmacology_gate.py` | 26 | gate G5 refusals and the inactive interfaces |
| `test_ranking_convergence.py` | 22 | convergence and centrality on a synthetic graph; direction-blindness |
| `test_ranking_cli.py` | 20 | end-to-end, both readers, and the refusal to invent data |
| `test_uncertainty_statistics.py` | 18 | hand-computed Kendall tau-b and quantile fixtures |
| `test_ranking_not_assessed.py` | 18 | contract P8, and the three "no support" states staying distinct |
| `test_ranking_gates.py` | 19 | every gate binds, and every gate releases |
| `test_ranking_audit.py` | 16 | downgrades applied, counted, and downgrade-only |
| `test_uncertainty_levels.py` | 16 | the level → Beta ladder's declared properties |
| `test_ranking_determinism.py` | 15 | byte-identical CSV; report format |
| `test_ranking_evidence_basis.py` | 13 | R7 `source_refs`, R8 dimension inputs, `evidence_gap` neutralisation |
| `test_ranking_information_gain.py` | 13 | the perturbation sweep |
| `test_ranking_sensitivity.py` | 13 | aggregation sensitivity |
| `test_ranking_invariance.py` | 7 | contract P5 |

**Proved by test, not asserted:**

* duplicated-evidence invariance — duplicate source ids *within* a claim and N extra
  claims citing one paper both leave every rank and every composite unchanged;
* paper-count invariance — 150 level-1 claim references lose to 15 level-3 ones, and
  two targets with identical levels and 20× different citation volume score the same;
* monotonicity — for all 15 facets at all 4 level transitions, polarity-aware, strictly,
  plus `counter_level` monotonicity and monotonicity under all four aggregations;
* gates — every declared gate is reachable, binds, and *releases* when the evidence
  that motivated it arrives; no gate is unreachable;
* `not_assessed` — wider than every assessed level, median strictly between level 1 and
  level 2, weight retained in the denominator;
* audit downgrades — lower the affected dimension, appear in `n_downgrades`, ratchet
  down only, and an upgrade cannot be constructed;
* determinism — identical CSV *and* sidecar bytes across runs; a target's draws do not
  depend on cohort size or order;
* Kendall tau-b — against five hand-computed fixtures including ties and the undefined
  case;
* the polarity-aware cap cannot flatter a target, **and** the naive implementation
  demonstrably would (so the regression test is not vacuous);
* gate G5 refuses a `deprioritise` verdict, an unresolved critical finding, an
  unaudited target, an unranked target, low coverage, and a caller trying to lower its
  own floor;
* the composite gate still binds under the conjunctive operator, **and** the
  unconverted cap is shown to be inert — so the dimension-equivalent conversion is
  demonstrably load-bearing rather than decorative;
* the product is never above the minimum, and the minimum never above the weighted
  mean, so the three operators stand in the expected strictness order.

**Asserted but NOT proved by test:** that the subjective weights and priors are *good*.
They are uncalibrated. Nothing in the suite tests accuracy, only coherence and the
declared invariances.

---

## 2. The composite is CONJUNCTIVE (ruling implemented)

The six dimensions are **conditions that must all hold**, not capacity factors to be
averaged. The primary composite is therefore the **product** of the six gated
dimensions — their joint probability under an explicit independence assumption —
because a weighted mean lets five favourable conditions compensate for one that fails,
which is the inference this project must not license.

* **Primary:** `product`. Unweighted, because a conjunction has no weights.
* **Variants:** `minimum` (strictest conjunction) and `weighted_additive` (the
  compensatory counterfactual — the superseded primary, weights **unchanged on
  purpose** so any ranking change is attributable to the operator, not to retuning).
* **`geometric_mean` removed**, not forgotten: it is a strictly monotone transform of
  `product`, so it induced an identical ordering and reported tau-b 1.0 by
  construction. Carrying it overstated how many independent operators the ordering had
  been tested against. The loader now refuses to carry both.
* **All three pairwise tau-b** reported, plus every target's median rank under every
  operator (`sensitivity.rank_by_aggregation`), so a reader sees *which* targets the
  operator choice moves.

**The ranking did change, and that is the finding.** Measured on the current
(pre-audit) cohort, product versus the superseded additive primary:

```
pairwise tau-b   product vs minimum            0.757
                 product vs weighted_additive  0.818
                 minimum vs weighted_additive  0.599
mean |rank move| 1.35 positions over 27 targets
max  |rank move| 7.0   (TGT:SLC16A7: additive rank 9 -> product rank 16)
>= 3 positions   5 targets (SLC16A7, EIF2S1, RGS14, OTX2, HDAC2)
```

SLC16A7 is the clearest case: it did comparatively well under compensation and falls
seven places once one weak condition can no longer be paid for by the others.

**Three consequences accepted and recorded in the spec:**

1. A single near-zero dimension drives the composite to near zero. That is the point.
2. An *unassessed* dimension now pulls the composite down more than it did, because
   Beta(1,1) contributes a factor centred at 0.5 to a product of six. Conjunctive
   semantics partially conflate "this condition fails" with "nobody checked" — a real
   cost, mitigated by the required coverage columns and `tier_3_insufficient_coverage`,
   **not** by the effect being small.
3. **The composite's own interval width is no longer a measure of epistemic
   uncertainty.** A product's spread is dominated by the magnitude of its smallest
   factor, not its uncertainty: a level-0 facet (mean 0.200) yields a *wider relative*
   composite interval than an unassessed facet (mean 0.500), although the unassessed
   facet is strictly more uncertain. Contract P8's "unknown widens" therefore holds at
   the facet and dimension levels and **not** on the composite width. This surfaced as
   a test failure after the operator change; the property is now asserted where it
   holds and the artefact is pinned where it does not
   (`test_the_conjunctive_composite_width_is_not_an_uncertainty_measure`). It is why
   the rank interval is the headline output.

**One follow-on fix the operator change forced.** The composite-level gate
(`unresolved_critical_finding_caps_composite`, cap 0.35) was **inert** under a product:
six sub-1 dimensions already sit far below 0.35, so an unresolved critical finding
would have capped nothing. The cap is now declared
`cap_scale: dimension_equivalent` — "the composite value if every dimension were
0.35" — and converts per operator (0.35^6 under product, 0.35 under the others). A gate
that silently stops binding when the operator changes is enforcement that looks present
and is not; three tests now cover it, including one asserting the unconverted cap would
be inert.

---

## 3. The six dimensions, one line each

Weights are subjective, justified in comments in `models/ranking/ranking_spec_v0_1.yaml`.
They now drive only the `weighted_additive` variant; the primary composite is unweighted.
Facet → dimension edges follow contract §5 plus the two edges approved by R8.

* **D1 P(causal cognition relevance)** — `causal_gene_attribution` 0.30 ·
  `human_genetic_association` 0.25 · `mechanistic_causal_perturbation` 0.25 ·
  `human_phenotype_specificity` 0.20
* **D2 P(adult modifiability)** — `adult_onset_perturbation` 0.45 ·
  `developmental_confound_risk` 0.30 *(inverse)* · `adult_expression_and_timing` 0.25
* **D3 P(supra-normal potential)** — `above_baseline_enhancement` 0.75 ·
  `dose_response_knowledge` 0.25 *(added by R8)*
* **D4 P(far transfer potential)** — `transfer_breadth` 0.60 ·
  `human_phenotype_specificity` 0.40
* **D5 P(safe controllable window)** — `safety_liability_burden` 0.55 *(inverse)* ·
  `dose_response_knowledge` 0.30 · `tractability` 0.15 *(added by R8)*
* **D6 P(human translation)** — `human_intervention_evidence` 0.35 · `tractability` 0.25
  · `cross_species_convergence` 0.20 · `human_lineage_divergence_risk` 0.20 *(inverse)*

Composite weights: D1 0.25 · D2 0.20 · D3 0.15 · D5 0.15 · D6 0.15 · D4 0.10.
Per-dimension input counts are now published in the report sidecar under
`dimension_inputs`, so a thin dimension cannot hide again (R8).

---

## 4. The level → Beta mapping

`level ↦ Beta(1 + s, 1 + f)` — a uniform prior plus supporting and non-supporting
pseudo-observations.

| state | α | β | mean | median | sd |
|---|---:|---:|---:|---:|---:|
| `not_assessed` | 1 | 1 | 0.500 | 0.500 | 0.289 |
| 0 searched, nothing found | 1 | 4 | 0.200 | 0.159 | 0.163 |
| 1 weak or indirect | 2 | 4 | 0.333 | 0.314 | 0.178 |
| 2 moderate | 5 | 4 | 0.556 | 0.560 | 0.157 |
| 3 substantial | 8 | 3 | 0.727 | 0.741 | 0.129 |
| 4 strong | 13 | 3 | 0.813 | 0.826 | 0.095 |

`counter_level` adds failure-side pseudo-counts (0, 1, 4, 7, 12), mirroring the
supporting ladder. Consequences the tests pin: `not_assessed` is strictly the widest;
level 0 is narrower *and* lower than `not_assessed`; and level 1 with `counter_level` 3
(Beta(2,11), mean 0.154) sits below level 0 with no counter-evidence (mean 0.200), so
"tested and contradicted" is distinguishable from "nobody found anything". Monte Carlo:
4000 draws, seed 20260917, streams keyed on `(seed, target_id, facet)`.

---

## 5. The Stage-2 run

```
27 rows, status=PRELIMINARY, reader=blueprint.loaders.load_repository
seed 20260917, 4000 draws, composite operator = product
facet slots filled            343/405 (84.7%)
coverage min/median/max       0.733 / 0.867 / 1.000   (below min_coverage: 0/27)
audited                       27/27          (gate G4 met)
tiers                         tier_1: 0 | tier_2: 13 | tier_4: 5 | tier_5: 9
facets never graded           62
facets level 0                85   (documented negative search)
facets counter_level >= 2     83   (tested and contradicted)
reporting gaps                3    (KL, HCAR1, SLC16A1)
pairwise tau-b                product/minimum 0.719 | product/additive 0.765
                              minimum/additive 0.473
cap sensitivity               6 caps derived, policy re-application a no-op,
                              tau-b 0.994, HCN1 -1.00, nothing over the 2.0 threshold
```

**Gates fired, all for the first time:** `no_human_intervention_caps_d6` 23 ·
`unresolved_critical_finding_caps_composite` 3 (CRTC1, GABRA5, GRM5) ·
`safety_liability_caps_d5` 2 (CHRM1, KCNQ2) · `developmental_confound_caps_d2` 2
(OTX2, SLC6A8) · `no_human_evidence_caps_d6` 0 (released for every target).

**The dimension-equivalent cap conversion is confirmed load-bearing.** The composite
cap converts to 0.35^6 = 0.001838 under the product operator, and all three
critical-finding targets sit exactly there. Applied as a raw 0.35 it would have bound
on **0 of 27 rows**. The gate that was inert before the fix is enforcing now.

**How much the audit moved the ranking** (same seed and draws):

| counterfactual | tau-b vs published | mean move | max |
|---|---|---|---|
| without the 5 adjustments | 0.997 | 0.07 | 1.0 |
| red-team facets blanked | 0.763 | 2.11 | 7.0 (KCNQ2, CHRM1) |

The adjustments barely move the order because the atlases had already applied most of
them; the audit's *facet contributions* move it substantially. A comparison against the
Stage-1 pre-audit run is **not attributable** — the operator change, the
educational-attainment fix and the audit are confounded — and the narrative says so
rather than quoting a tau-b across them.

**A defect this run exposed in my own code.** Three of the five audit adjustments raise
`counter_level` rather than lowering `level` — the natural way to record a null that is
now replicated. My input type enforced V12 as "`to_level < from_level`" and rejected all
three as forbidden upgrades, silently discarding the downgrades the red team was making.
The shared record model in `blueprint.records` already had the right rule; mine did not.
Fixed: an adjustment names the field it moves, `level` must decrease, `counter_level`
must increase, both lower standing, and a test asserts no repository adjustment raises a
composite. Worth recording because it failed *closed* — it kept the old grade and
produced no error, so nothing would have surfaced it but reconciling the counts.

---

## 6. What would change the table (Sprint 2)

In order of how much they would move it:

1. **A causal-gene attribution above level 2 for any target.** 17 of 27 at level 0,
   none above 2, so D1 (cohort median 0.346, max 0.544) is the binding dimension for
   the whole cohort. `ROADMAP.md` Sprint 2's exit criterion — fine-mapping,
   colocalisation or an allelic series instead of positional mapping — is the single
   highest-value piece of work available anywhere in this repository.
2. **Any above-healthy-baseline result with a healthy comparison arm.** D3's cohort
   median is 0.277, graded largely from studies that had no healthy arm at all.
3. **Far-transfer measurement.** `transfer_breadth` is the most frequent
   highest-value next analysis (9 of 27 targets) precisely because almost nothing has
   measured it.
4. **A dependence model for the intervals.** It would not move the ordering, but it
   would stop the intervals being wrong in a known direction.

**Information gain re-checked, and it improved.** Pre-audit the sweep named
`safety_liability_burden` for all 27 targets — unanimity that was a symptom of the
binding gap rather than a result. With the audit landed it resolves into five distinct
facets: `transfer_breadth` 9 · `above_baseline_enhancement` 6 ·
`human_phenotype_specificity` 6 · `dose_response_knowledge` 4 ·
`safety_liability_burden` 2. Repository-wide top rows: KCNQ3
`dose_response_knowledge` (7.00), KCNQ3 `transfer_breadth` (6.00), then
`transfer_breadth` for EIF2S1, HDAC2 and PTPN5 (5.00 each). That the metric stopped
being unanimous the moment the real gap was filled is a useful check on it.

---

## 7. Judgement calls a reviewer should challenge

1. **The conjunctive primary is now a ruling, and its costs are real.** Resolved in
   favour of `product`; see §2. What remains arguable is not the operator but its three
   accepted costs — an unassessed dimension is penalised almost like a failed one, the
   composite's interval width stops measuring uncertainty, and composite magnitudes
   become uninterpretable. `minimum vs weighted_additive` at tau-b 0.599 is still the
   number that says the ordering is materially operator-dependent.
2. **Every weight and cap is invented.** D1 0.25, the 0.25 D2 cap, the 0.20 D5 cap, the
   0.35 D6 cap, the tier fractions, the 2.0-position cap-sensitivity threshold. All
   labelled subjective; none fitted.
3. **`not_assessed` = Beta(1,1).** Maximum entropy, no smuggled base rate — but it also
   means an unexamined facet scores above a documented negative search. Defensible; not
   obviously right. Under the conjunctive composite this matters more than it did: a
   factor centred at 0.5 in a product of six is a substantial penalty, so the prior's
   *location* now moves ranks as much as its width does.
4. **Facet draws are modelled as independent.** They are not: facets share claims,
   sources, cohorts and one grader. **Every reported interval is too narrow by an
   unknown amount.** This is the largest single weakness in the model.
5. **The level-4 mean is 0.813, not higher.** A judgement that replicated human results
   in this literature are routinely overturned.
6. **D4 is weighted lowest (0.10)** because transfer evidence is near-absent, so the
   dimension is near-uniform and carries little signal. Contingent on current coverage;
   revisit when transfer evidence exists.
7. **Symmetric caps are the counterfactual, not a policy.** On current data the
   asymmetry costs nothing measurable (tau-b 1.000). That is a finding about *this*
   cohort, not a general result — and the policy re-application being a no-op means the
   atlases applied §5.4 correctly, which is a cross-check that passed.
8. **Information gain is unanimous**, which flags a limitation: the metric favours a
   facet that is uniformly unassessed and heavily weighted. Read it as "where is the
   ranking unresolved", never as "what matters most scientifically".
9. **Tractability grades are generated, not hand-authored.** Deterministic from a pinned
   release with a full audit trail — but the (modality, label) → level groupings in
   `pipelines/integration/fetch_target_annotations.py` are my reading of the rubric, and
   the `AB/*` and `PR/*` buckets being classed as predictions rather than tools is the
   judgement most worth checking.
10. **`SM/Approved Drug` → level 3 for 11 targets.** The bucket means the target or a
    close family member has an approved drug; it says nothing about the modulation
    *direction* this project's hypotheses want. A reviewer should treat those 11 level-3
    grades as "a molecule exists that touches this family", nothing more.
11. **EIF2B_COMPLEX tractability is `not_assessed` on purpose** — Open Targets annotates
    genes, and collapsing five member-gene grades into one complex grade needs a
    curatorial decision about which subunit or interface a modality engages.

---

## 8. Artefacts

**Specs** — `models/ranking/facet_rubric_v0_1.yaml` (15 facets; **the polarity
authority** per contract §5.4, with a stable key contract documented in its header, a
per-facet `methodological_cap_applies_to`, a flat `polarity_index`, and
`database_gradable: true` on `tractability` alone) ·
`models/ranking/ranking_spec_v0_1.yaml` (weights, gates, `cap_variants`, tiers,
information gain) · `models/uncertainty/uncertainty_spec_v0_1.yaml` ·
`models/causal/README.md` + `causal_model_interface.yaml` (no effect is estimated in
Sprint 1).

**Code** — `src/blueprint/ranking/{inputs,rubric,uncertainty,caps,score,information_gain,convergence,report,cli,synthetic}.py`
· `src/blueprint/pharmacology/{gates,interfaces}.py` · `models/ranking/rank_targets.py`
· `pipelines/integration/{fetch_target_annotations,write_tractability_assessments}.py`.

`caps.py` is the **single** polarity-aware cap implementation required by §5.4; caps are
*derived* from `context.phylogenetic_control` on the cited claims rather than declared.

**Docs** — `THEORY.md` (33 cited claim ids, all verified to exist; 5
`[EVIDENCE REQUIRED]` hooks; zero PMIDs; zero probabilities) ·
`docs/PHARMACOLOGY_INTERFACES.md`.

**Data** — `data/raw/opentargets/2026-09-17/*.json` (31 snapshots, manifest-registered)
· `data/interim/opentargets_tractability.jsonl` ·
`data/interim/opentargets_safety_pmid_candidates.jsonl` (191 rows, **candidates for
`agent:red_team`** — those PMIDs must be registered and machine-verified before any
claim rests on them) · `evidence/sources/integration.yaml`
(`SRC:DB:opentargets:26.06`) · `atlases/integration/assessments/*.yaml` (27 files).

**Requests** — `integration-001` (R7, approved and implemented) · `integration-002`
(R8, approved and implemented).

---

## 9. Contract amendments implemented

* **§5.4 polarity-aware caps** — `polarity: normal | inverse` on every facet (`direct`
  accepted as a deprecated alias and normalised on read); one helper
  (`caps.py::apply_methodological_cap`); the loader refuses a rubric whose
  `methodological_cap_applies_to` contradicts its polarity, or whose `polarity_index`
  has drifted.
* **§5.4 `symmetric_caps`** — declared in `cap_variants`, run every time,
  `rank_delta_symmetric_caps` per CSV row (blank when no cap applies, which is *not*
  zero), tau-b and the asymmetry statement in the sidecar, threshold 2.0 rank positions,
  HCN1 as the worked example in the spec.
* **§5.2 / R7 `source_refs`** — `tractability` only, with `evidence_basis:
  database_release`; the loader refuses the flag on any other facet.
* **§4.1 `evidence_gap`** — a `counter_level` resting *only* on `evidence_gap` claims is
  dropped before scoring and reported under `evidence_gap_facets`; one real
  counter-claim keeps the grade. Two such claims exist
  (`CLM:brakes:EIF2B_COMPLEX:004`, `CLM:brakes:GABRA5:009`); no facet currently cites
  either, so nothing is neutralised yet and the mechanism is proved on synthetic inputs.
* **State-variable `polarity: risk | margin`** — convergence and centrality are
  deliberately direction-blind and a test asserts that a risk and a margin variable with
  identical topology score identically. `convergence.state_variable_polarity()` exists so
  any future directional reading consults the declaration rather than a variable's name.

---

## 10. Published artefacts are current

`reports/target_ranking_v0_1.csv`, `reports/target_ranking_v0_1.meta.json` and
`reports/integration_v0_1.md` were all written by the Stage-2 run described in §5,
under the conjunctive primary and over the full audited cohort. Reruns are
byte-identical, so the table diffs cleanly. The earlier warning in this handoff about a
stale pre-audit CSV no longer applies — it was regenerated as the first action of
Stage 2.

Ownership is clean: `atlases/integration/**` is in the lane and
`scripts/check_ownership.py` reports 0 violations.

---

## 11. Disclosures now carried in the report narrative

Both were previously only in `models/`. A caveat buried in a spec file is a caveat
nobody reads, so both are now in the sidecar's `disclosures` block, printed by the CLI,
and — for the tractability one — visible at the row.

1. **`independence_assumption_narrows_every_interval`** (major). Facet draws are
   independent in the model and correlated in reality; three facets feed two dimensions
   each, and each domain's facets share one grader. Every interval is too narrow by an
   unknown amount, and because the composite is a product the point estimate
   *understates* a target whose dimensions are favourable together. Both directions
   known, neither size known.
2. **`tractability_level_3_is_family_precedent_only`** (major, currently 11 targets).
   A level-3 tractability grade from the pinned release means **a molecule touches this
   protein family** — nothing about direction, nothing about selectivity, nothing about
   whether the available direction is the one the control-point hypothesis needs.
   `tractability` carries 0.25 in D6 and 0.15 in D5, so it qualifies both. Visible
   three ways now: the new CSV column `tractability_caveat` (`family_precedent_only`
   for those 11 rows), the facet `rationale` in each assessment record, and the
   sidecar.

`tractability_caveat` across the 27 targets: `family_precedent_only` 11 ·
`characterised_tool` 8 · `prediction_only` 6 · `no_signal_in_release` 1 (OTX2) ·
`not_assessed` 1 (EIF2B_COMPLEX).

---

## 12. R11 conformance — `search_basis` on the tractability assessments

All 27 records regenerated; **0 validation violations in this lane** (was 1 — OTX2, the
only level-0 grade).

`search_basis` is written on **every** facet, not only the level-0 one, because for a
database-derived grade it is genuinely informative rather than boilerplate. Each names
the pinned release and Ensembl id, the snapshot path, the full 28-bucket universe
inspected across all four modalities, the hit criterion in rubric order, and the actual
result. So OTX2's zero reads *"every one of the 28 buckets is false for this target in
this release, and no chemical probe is listed"* — a statement about the release, not
about the effort — and it adds explicitly that this is **not** a claim the target is
intractable, since Open Targets reports what has been annotated and an unstudied
protein has no annotation either.

EIF2B_COMPLEX carries a `search_basis` too, recording that the search was complete and
found no complex-level record: what is `not_assessed` is not the search but the
curatorial judgement about which subunit or interface a modality engages.

---

## 13. Known failures and gaps

* **Facet draws are independent in the model and correlated in reality.** Intervals are
  too narrow; the direction of the error is known, its size is not. The highest-value
  improvement available.
* **`polarity_aware` cap re-application is a no-op on current data**, so the derivation
  path is exercised but its *effect* is only demonstrated on synthetic inputs.
* **`minimum` aggregation tau-b 0.5992** — the ordering is materially sensitive to the
  aggregation choice and any prose quoting a rank must say so.
* **Every row is pre-audit.** Nothing in `reports/` should be read as a finding.
* **No convergence analysis has run on a real graph** — the Phase-2 compiler does not
  exist yet.
* **Nothing is calibrated.** `models/uncertainty/uncertainty_spec_v0_1.yaml` §6 states
  what calibration would require; none of it has been done.
