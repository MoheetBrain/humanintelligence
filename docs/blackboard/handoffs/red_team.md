# Handoff — `agent:red_team`, Red Team / Evidence Auditor v0.1

**Written:** 2026-09-17. **Branch:** `sprint-1/foundation`. **Run:** `sprint1-red-team-01`.
**Scope:** all 27 seed targets, plus `THEORY.md`, `models/ranking/ranking_spec_v0_1.yaml`
and `pipelines/alphacognition/build_assessments.py`.

Full report: [`reports/red_team_audit_v0_1.md`](../../../reports/red_team_audit_v0_1.md).
Method, search routes and this audit's own biases:
[`docs/RED_TEAM_METHOD.md`](../../RED_TEAM_METHOD.md).

---

## 1. The headline finding

**The repository's most-studied brake target has now failed in humans twice, and the
repository did not know it.**

`agent:brakes` found the first null (CLEMATIS, `SRC:PMID:35123401`) and recorded it
properly. It then identified a second completed trial — `NCT02953639`, n=214, MATRICS
composite — noted its results were posted, declared it had **not** retrieved them, called
it *"the largest single unresolved item in the GABRA5 dossier"*, and refused to grade it
in either direction. That refusal was correct behaviour.

I retrieved it. It is null, and precisely so: primary MCCB neurocognitive composite
treatment difference **+0.28 T-score points, 95% CI −1.47 to +2.02, p = 0.793**, on a
scale whose population SD is 10. The interval excludes anything above ~0.2 SD in either
direction — **a precise null, not an underpowered one**. The placebo arm itself improved
by +1.08, nearly four times the treatment difference. Human target engagement was
demonstrated in the companion trial, so failing to reach the target does not explain it. A
third trial (`NCT02484703`, n=45) was terminated with the sponsor stating in the registry
that it stopped *because another study showed no efficacy, and that safety was not the
reason*.

So the human null for the α5-GABA-A mechanism is now **replicated**: two independently
reported randomised trials, two populations, both with pre-specified multi-domain
cognitive primaries, both null, consistent in direction. Recorded as
`CLM:red_team:GABRA5:001`.

Three limits, because this is easy to over-read: neither trial tested **healthy adults**;
the rodent plasticity phenotypes are separate evidence and are untouched by these trials;
and GABRA5's **safety** picture is genuinely good — 386 randomised participants, both
trials reporting tolerability similar to placebo, which is why its
`safety_liability_burden` carries `counter_level: 3`.

---

## 2. Real numbers

| | |
|---|---|
| Targets audited | **27 / 27** (rule V15) |
| Audit records | **30** — 27 `scope.kind: target`, 1 `document`, 2 `model` |
| Complete 17-check catalogue | **30 / 30** → 510 catalogue rows |
| Check results | 131 `pass` · 246 `flag` · 60 `fail` · 73 `not_applicable` |
| Findings | **57** — **4 critical** · 32 major · 13 minor · 8 info |
| Downgrades applied | **5**, on 4 targets |
| Claim statuses changed | **5**, all `active` → `contested` |
| Verdicts | 3 `retain` · 19 `retain_with_downgrade` · 3 `deprioritise` · 2 `insufficient_evidence` |
| Sources registered | **17** · **17 verified**, first pass, zero failures |
| Claims added | **13** |
| `safety_liability_burden` | 0×11 · 1×5 · 2×5 · 3×4 · 4×2 |
| `developmental_confound_risk` | 0×6 · 1×4 · 2×8 · 3×7 · 4×2 |
| `--strict` in my files | **0 errors, 0 warnings** |
| `check_ownership.py` | 84 paths, **0 violations** |

**Critical findings (4):** GABRA5 `negative_clinical_evidence`; CRTC1 and the genetics
facet rule `educational_attainment_mistaken_for_intelligence`; GRM5
`model_organism_translation_failure`.

### Downgrades (all in `adjustments`; no other agent's file was edited)

For `counter_level` a **raise is the downgrade** — stronger contradicting evidence lowers
the target's standing.

| Target | Facet | Field | From → To |
|---|---|---|---|
| TGT:CRTC1 | `human_genetic_association` | level | **3 → 1** |
| TGT:GABRA5 | `human_intervention_evidence` | counter_level | **3 → 4** |
| TGT:GABRA5 | `above_baseline_enhancement` | counter_level | **3 → 4** |
| TGT:PDE4B | `above_baseline_enhancement` | level | **3 → 2** |
| TGT:PDE4B | `dose_response_knowledge` | counter_level | **1 → 2** |

### Claim statuses changed (all `contested`, none `withdrawn`)

`CLM:alphacognition:gwas.CRTC1:002` · `CLM:power:HCAR1:004` — my own findings.
`CLM:power:KL:001` · `CLM:power:anls:001` · `CLM:power:creatine_human:001` — three
self-declared contestations that had no audit record behind them and were therefore
unreviewable under **V14**. Ratifying them cleared the three V14 warnings. In every case
the experiment is real and correctly described; what is in dispute is what it licenses.

### The two grades I reconsidered late, and in which direction

Both moved **up in severity** (worse for the target), after reading the ranking spec's
gate thresholds:

- **TGT:CHRM1 `safety_liability_burden` 3 → 4.** Two independent human studies, consistent
  in direction: a 343-patient randomised trial with 52% discontinuation and 12.6% syncope
  at the effective dose, plus a healthy-volunteer study reporting dose-related cholinergic
  events and blood-pressure/pulse increases.
- **TGT:KCNQ2 `safety_liability_burden` 3 → 4.** Human LoF variants in *this* gene cause
  neonatal epileptic encephalopathy, and the only modulator of this channel family ever
  marketed was **withdrawn from market**.

Both now fire `safety_liability_caps_d5` (cap 0.20, the lowest in the spec). **The KCNQ2
grade is flagged in its own record as my most contestable judgement**: it rests partly on
a withdrawal whose cause is undisclosed and whose direction of modulation is the opposite
of the one proposed. At level 3 the gate would not fire. I recorded the reasoning in full
so it can be overridden without re-deriving it.

---

## 3. For `agent:integration` — read this before running the ranking

**Gates my grades now fire:**

- `developmental_confound_caps_d2` → **TGT:SLC6A8** (4 / counter 0), **TGT:OTX2** (4 / 1)
- `safety_liability_caps_d5` → **TGT:CHRM1** (4 / 1), **TGT:KCNQ2** (4 / 0)
- `unresolved_critical_finding_caps_composite` → **TGT:GABRA5**, **TGT:CRTC1**, **TGT:GRM5**
- `deprioritise` verdicts → **TGT:GPR158**, **TGT:OTX2**, **TGT:GRM5**
- `insufficient_evidence` verdicts → **TGT:EIF2S1**, **TGT:PTPN5**

**The one structural exposure in the spec** (`AUD:red_team:RANKING_MODEL:001#f1`): D1
aggregates **additively**, so a level-3 positional GWAS association contributes support at
weight 0.25 regardless of the gene-attribution grade beside it — and
`causal_gene_attribution` reaches 3 or 4 for **no** target (0×14, 1×1, 2×12). There are
gates for developmental confound, absent human evidence, absent human intervention and
high safety liability, but **no gate on unresolved gene attribution** — so the item your
own spec calls *"the single weakest link in the whole evidence chain"* is the one thing
fully tradeable within its dimension. A gate analogous to `no_human_evidence_caps_d6`
would close it; on current grades it would apply to all 27 targets, which is both the
argument for and against adding it now.

**Also:** §5.4 of the report — the ranking is invariant to duplicated *evidence* but not
to duplicated *targets*. Up to seven of 27 seed targets are fewer than seven independent
evidence bases (three MCTs share all founding sources; KCNQ2/KCNQ3 are one experiment with
one construct; EIF2S1/EIF2B_COMPLEX are one pathway). And `CLM:power:anls:001` is a
**single point of failure beneath four targets** — a downgrade of it should cascade to all
four, not to none.

**Things I checked and found sound, so you can rely on them:** `not_assessed` handling
(five numbered rules, never coerced to 0, Beta(1,1), kept in the denominator, provably not
rewarded, visible via `coverage`) — this answers `agent:comparative`'s §7.7 worry
directly; the R8 fix that makes `dose_response_knowledge` a secondary D3 input, which
closes the DRD1 inverted-U trap; the `cap_scale_note` on the composite gate, which catches
"enforcement that looks present and is not"; and the `symmetric_caps` sensitivity variant
the contract mandates.

---

## 4. Items routed to me, and what I found

Answering each thing forwarded during the run.

**`NCT02953639` posted results — retrieved.** §1. It moved the facet *down*.
**`NCT02484703` and `NCT05307679`** — `agent:brakes`' `unknown` determination is
**confirmed**: `NCT02484703` has no `resultsSection`, so whether its cognitive endpoints
were administered before termination genuinely cannot be determined. `NCT05307679` (n=7,
Dup15q) has results, but its primary is **Vineland-3 adaptive behaviour — not a cognitive
endpoint** — reported as medians with full ranges and no statistical analysis. Neither can
contribute in either direction. `CLM:brakes:GABRA5:009` was correctly left permanently
unused; its content belongs in an audit finding, which is where it now is.

**`CLM:brakes:GABRA5:008` / `CLM:brakes:ADORA1:007` — retain, do not withdraw.** I read
the underlying source (`SRC:PMID:28216264`): it is a literature curation effort over 70
targets, exactly as both claims say. **Their description of their own source is exact** and
`content_checked: false` was the appropriate flag. Two residual defects: (a) both have
`context.species` human with `translation.human_relevance: other_species_only` — the
curation table attributes no species at row level, so `unknown` is honest for both fields;
(b) **`ADORA1:007` conflates directions** — in the underlying annotation every cardiac and
lethal event belongs to A1 *activation* and only convulsions to *inhibition*, so the record
attaches agonist liabilities to an antagonist strategy. Conservative in effect, wrong in
fact, and the same class of silent sign error you flagged about yourself.
`CLM:red_team:ADORA1:001` records the direction-resolved version.

**`CLM:brakes:HCN1:005` retype — verified correct.** `clinical_harm` → `preclinical_harm`
by direct inspection: species mouse, `human_relevance: rodent_only`, `basis:
germline_knockout`, design knockout. A repository-wide scan found **exactly one** instance
of animal evidence wearing a clinical label — this one — so the pattern is isolated.

**The hand-inverted signs — chains verified correct, but `direction` has two meanings.**
Suppressing the M-current raises intrinsic excitability and produced spontaneous seizures,
so the excitability→`seizure_risk` coupling of `direct` is right, and the variable declares
`polarity: risk` with an id ending `_risk`. Verified against `SRC:PMID:15608631`. **But**
`CLM:brakes:GABRA5:001` uses `direction` as the sign of the *regulation* while
`CLM:brakes:KCNQ2:001` uses it as the *observed change* — both cannot be right under one
convention. Worse, `CLM:brakes:GABRA5:003`'s object is
`SV:workspace.interference_susceptibility` while its measured endpoint is a *discrimination
ratio*, the polarity inverse; nothing marks the inversion, so a mechanical reader taking
`object` + `effect_direction` concludes the deletion *improved* interference control — the
opposite of the paper's finding, which is the **cost** that makes `transfer_breadth`
counter_level 3. This is a **contract defect** (§4 does not disambiguate `direction` for
regulation claims) as much as an atlas one, and needs a schema-change request that is not
mine to file. Report §5.6.

**`CLM:brakes:RGS14:004` — NOT cleared.** I did not retrieve the review's primary sources,
so whether it says what the claim says is **unverified by this audit**. Recorded as an open
item, not a cleared one. It remains RGS14's only human-relevant evidence.

**The R5 null-vs-gap determinations — all four verified, independently.** GRM5 and HTR2A
are genuine **measured nulls** (`endpoint_measured: measured` + `evidence_role:
null_result` + `NO_DETECTED_EFFECT_ON`, so V16c is satisfied) and keeping `level 0 /
counter_level 3` is right. CHRM1 and GRIN2B are genuine **evidence gaps**, so lowering
their counter_levels 1 → 0 was correct even though that is the direction that flatters the
target. `CLM:brakes:EIF2B_COMPLEX:004`'s retyping also verified.

**`HTR2A:003`'s `MODULATES` → `NO_DETECTED_EFFECT_ON` migration — verified, and it
mattered.** As `MODULATES`, a measured human null would have compiled as *support*. A
repository-wide scan found **no remaining case** of a measured human null wearing a
positive relation. 25 claims do carry contradicting or null evidence on non-null relations,
but in each the claim's own assertion is a positive finding that happens to contradict a
*different* proposition — correct use.

**`agent:alphacognition`'s four nominations.** `CHRM1:001` — the record is scrupulously
caveated and every caveat checks out; the defect is the **structural dependence** on it,
and I found what happened next: the phase 2 was **withdrawn for an unexpected animal
toxicology finding** (`CLM:red_team:CHRM1:001`), which nothing in the repository recorded.
`GRIN2B:001` — confirmed as the repository's clearest life-stage mismatch. UK Biobank
concentration — quantified, report §5.3. The generated-facet rule — audited as a rule, and
it contains one defect, §5 below.

**`agent:power`'s nominations.** `HCAR1:004` — agreed, contested; a construct jump cannot
be fixed by re-reading the source. `SLC16A1:003` — agreed; the cohort was ascertained by
ketoacidosis so `contradicts` overstates it and `qualifies` is defensible. `CKB:002` —
primary paper still unretrieved, automatic downgrade stands. `creatine_human:001` vs
`:002` — ratified contested, §2. **The H0 conclusion holds**, and my independent search
*corroborates* it: I reached `SRC:PMID:35984306` independently (young-adult SMD **0.03**,
I² = **0%**) and found a second pooled analysis the atlas did not cite
(`SRC:PMID:39070254`, 16 RCTs, no improvement in overall cognition or executive function).
At the creatine node the conclusion is if anything **too weak** — that is a tight null; at
the system level "cannot reject H0" is **exactly right**, since 16 of 22
power/efficiency variables remain `unknown`.

**`NCT01791595` (AZD3965) — retrieved from the primary record.** MCT1 inhibition in humans
produced **on-target ophthalmic and haematological dose-limiting toxicity**: the protocol
names haematological, cardiac and ophthalmic events as the expected DLT classes, and the
posted tables show **retinopathy in 13 patients (2 serious)** and **anaemia in 14**, with
known retinal disease excluded at screening. MCT1 is the erythrocyte lactate transporter
and is essential to retinal metabolism, so the mechanistic coherence is what makes this a
target liability rather than trial noise. `SLC16A1 safety_liability_burden: 3`. **I
deliberately did not carry it to SLC16A7 or SLC16A3** — retinal and erythrocyte lactate
transport are MCT1 functions, and extending it would manufacture two liabilities from one.

**The `NCT01455376` scope judgement — upheld, not widened.** Listing one unreported study
against four targets would inflate a bias count by re-counting one study, which is
structurally the same error as inflating evidence by re-citing one paper. I considered
widening it and declined; the reasoning is in the record.

**`CLM:comparative:NEURON_SCALING:001` — nothing downstream leans on it.** Checked
mechanically: it appears in **no** facet's `claim_refs` or `counter_claim_refs` anywhere in
the repository, and in **no** dossier. Its only references outside its own claim file are
inside the comparative atlas's own documentation — two rows of `species_panel.yaml` and two
passages of `phylogenetic_controls.md`, where that agent is describing the claim's own
phylogenetic-control problem rather than building on it. So it is a cell count in which no
bird performed a task, the comparative agent says exactly that in its own `risks`, and the
over-read it worried about **has not happened**. No adjustment needed.

---

## 5. The other critical finding: educational attainment laundered into fluid reasoning

`atlases/alphacognition/cognitive_trait_panel.yaml` classes GWAS Catalog trait
*mathematical ability* (EFO_0004875) as `phenotype_class: fluid_reasoning` **and** marks it
`use_in_ranking: supporting` with the note *"never a stand-alone basis for a facet level."*
`build_assessments.py` tests `phenotype_class` and **never reads `use_in_ranking`**, so
that restriction never fires. The records are *"Self-reported math ability"* and *"Highest
math class taken (MTAG)"* from `SRC:PMID:30038396` — a GWAS of **educational attainment**
in 1.1 million people. The rule's explicit EA cap cannot help, because the laundering
happens at the **trait→class mapping step, upstream of the cap**.

Five claims rest entirely on such records. Scope is **bounded**: **CRTC1's grade falls
3 → 1** (it is the stand-alone basis, and CRTC1 has *no* non-education cognitive
association at all); GRIN2B, OTX2, PDE4B and SLC16A7 **survive** on genuine
intelligence-trait associations, with only their rationale strings overstated. The fix is
one field.

---

## 6. Repository-level risks (report §5)

1. **A literature-only search is not a search.** `agent:power` overturned **two of its own
   published statements** when forced to justify its zeros — no human klotho intervention,
   no human MCT1 intervention — both wrong, both found by registry search. I reproduced the
   pattern: **four of my five headline findings came from a `whyStopped` or `resultsSection`
   field no literature search can return.** A programme that stops generates no paper.
   **`agent:brakes`, `agent:alphacognition` and `agent:comparative` have not been
   re-checked this way**, and on my hit rate doing so should be expected to overturn
   something. Every level-0 human-evidence grade resting on a literature search should be
   treated as provisional.
2. **Two kinds of gap must not be pooled** — a *measurement* gap (reported in full, never
   asked the question: `NCT01791595`) is a coverage fact; a *reporting* gap (asked it as
   primary, never published in 16 years: `NCT01455376`) is a publication-bias fact. Only
   the second makes an evidence base drift positive. The ranking reads the *level*, not the
   reporting-gap list, so the two zeros currently rank identically.
3. **Citation and cohort concentration** — two EA GWAS carry **40 of 290** claims; the
   largest cohort appears in 14 evidence items; only 5 claims mention UK Biobank in text,
   so it is invisible to a text search; **nothing de-duplicates cohorts**; and every Open
   Targets safety row traces to **two curation reviews**.
4. **Duplicated targets, not duplicated evidence** — §3 above.
5. **Coverage asymmetry penalises knowledge** — the best-characterised targets accumulate
   the most damaging findings and the least characterised look clean. **HDAC2** is the
   clean demonstration: Open Targets returns *no* safety annotation while the oncology
   HDAC-inhibitor class carries thrombocytopenia and hepatotoxicity. An empty database list
   must never be graded 0, and all 11 of my level-0 safety grades carry a `search_basis`
   saying the source is **silent**, not that the target is safe.
6. **`direction` has two incompatible meanings** — §4 above.

---

## 7. Where I am weakest

1. **Nobody graded or checked my two facets.** Most exposed: **KCNQ2** and **CHRM1**
   `safety_liability_burden: 4`, both of which fire a ranking gate. KCNQ2 is flagged in its
   own record as my most contestable grade.
2. **Only ClinicalTrials.gov was queried** — no WHO ICTRP, EudraCT or national registries.
   Given that registry search produced four of five headline findings, this is the largest
   gap in my method.
3. **Almost no full text** — `extraction.basis: full_text` appears nowhere in my claims.
4. **The two safety curation reviews' own tables were never opened**, which is why no
   safety grade resting on them exceeds level 2.
5. **`CLM:brakes:RGS14:004` and `CLM:power:CKB:002` remain unverified** and are
   load-bearing for their targets.
6. **246 `flag` results is too many to be individually load-bearing.** The next auditor
   should test whether my flag threshold was set low enough to be uninformative.
7. **I made three errors of my own**, all caught by the validator and all documented in
   `docs/RED_TEAM_METHOD.md` §4.3: a reporting gap typed as an `evidence_gap` (V16c), an
   illegal `GENE -ABOUT-> PHENO` triple (V3), and a divergent duplicate registration of
   `SRC:NCT:NCT01455376` where **`agent:power`'s registration was the correct one and mine
   was wrong** (V4). All three are cleared. The draft claim was removed rather than
   repaired because a reporting gap is not a claim; its id was never locked, so no
   provenance was deleted.

---

## 8. Open items for others

- **`agent:ontology` / orchestrator** — `direction` on regulation claims needs
  disambiguating in contract §4. A schema-change request is warranted; not mine to file.
- **`agent:alphacognition`** (future sprint) — one-field fix: read `use_in_ranking`.
- **`agent:brakes`** — §4 above: retain both flagged claims; fix the two
  `human_relevance` / `context.species` inconsistencies and the `ADORA1:007` direction
  conflation.
- **Orchestrator** — one informational **V22** warning remains, not in my lane:
  `SRC:NCT:NCT01455376` and `SRC:NCT:NCT07285629` are registered by `agent:power` and cited
  by no claim of its own. Note `NCT01455376` **is** now cited, in my `reporting_gap_refs`
  on SLC16A1 — so V22 appears to attribute citation per registering file rather than per
  `source_id`. Worth confirming before anyone "fixes" a source that is in fact in use.

---

## 9. Artefact index

```
evidence/audits/red_team/{SYMBOL}.yaml            27 target audits, 17 checks each
evidence/audits/red_team/THEORY.yaml              document audit  (verdict: retain)
evidence/audits/red_team/RANKING_MODEL.yaml       model audit     (verdict: retain)
evidence/audits/red_team/GENETICS_FACET_RULE.yaml model audit     (retain_with_downgrade)
atlases/red_team/assessments/{SYMBOL}.yaml        27 files, 2 inverse-polarity facets each
evidence/sources/red_team.yaml                    17 records, 17/17 verified
evidence/claims/red_team/GABRA5.yaml              2 claims (incl. the replicated human null)
evidence/claims/red_team/CHRM1.yaml               2 claims
evidence/claims/red_team/SLC16A1.yaml             1 claim  (AZD3965 human DLTs)
evidence/claims/red_team/target_safety_liabilities.yaml   4 claims (HTR2A, DRD1, GRIN2B, ADORA1)
evidence/claims/red_team/programme_failures.yaml  4 claims (KCNQ2, GRM5, PDE4B, creatine)
docs/RED_TEAM_METHOD.md                           search strategy, limits, own biases, own errors
reports/red_team_audit_v0_1.md                    the human-readable audit
data/raw/ctgov_v2/2026-09-17/                     immutable CT.gov v2 snapshots + manifest lines
```

**`pytest` was not run**, per instruction. No test result is claimed anywhere in this
audit. No git command was run at any point. Nothing was deleted and no level was raised.
