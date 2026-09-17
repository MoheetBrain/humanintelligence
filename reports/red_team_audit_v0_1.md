# Red Team Audit v0.1 — Intelligence Blueprint

`agent:red_team` · 2026-09-17 · branch `sprint-1/foundation`

**Scope.** All 27 seed targets, plus `THEORY.md`, the ranking specification, and the
generated genetics-facet rule. 30 audit records, every one carrying the complete 17-check
mandatory catalogue (510 catalogue rows). Method, search routes and the biases of this
audit are in [`docs/RED_TEAM_METHOD.md`](../docs/RED_TEAM_METHOD.md).

---

## 1. The headline

**The single most-studied brake target in this repository has now failed in humans
twice, and the repository did not know it.**

`agent:brakes` found the first null — the CLEMATIS trial of the α5-GABA-A negative
allosteric modulator basmisanil in Down syndrome — and recorded it properly. It then did
something better: it identified a second completed trial (`NCT02953639`, n=214, MATRICS
composite), noted that its results were posted, declared that it had not retrieved them,
called it *"the largest single unresolved item in the GABRA5 dossier"*, and **refused to
grade it in either direction**.

The red team retrieved it. It is null, and it is null *precisely*:

| | |
|---|---|
| Primary endpoint | MCCB neurocognitive composite, change from baseline to week 24 |
| Treatment difference | **+0.28 composite T-score points** |
| 95% CI | **−1.47 to +2.02** |
| p | 0.793 |
| Scale | MCCB composite T-score has population SD **10** |
| Placebo arm change | +1.08 — nearly **four times** the treatment difference |

The confidence interval excludes any effect larger than roughly 0.2 SD in either
direction. **This is a precise null, not an underpowered one.** Human target engagement
was demonstrated in the companion trial, so failure to reach the target does not explain
it. A third trial (`NCT02484703`, n=45) was terminated with the sponsor stating in the
registry that it stopped *because another study showed no efficacy, and that safety was
not the reason*.

So the human null for this mechanism is **replicated**: two independently reported
randomised placebo-controlled trials, two different populations, both with pre-specified
multi-domain cognitive primary endpoints, both null, consistent in direction. That is
level 4 on `evidence_strength_v1`, and it is the basis of two of this audit's five
downgrades.

Three things are worth separating carefully, because the finding is easy to over-read:

- Neither trial tested **healthy adults**. This pair of nulls establishes that the
  mechanism did not improve cognition in the two deficit populations where it was tested.
  It does not establish that α5 negative modulation cannot raise a healthy adult.
- The rodent plasticity phenotypes are **separate evidence** and are not addressed by
  these trials. "The α5 brake does not exist" would be an over-read.
- GABRA5's **safety** picture is genuinely *good*: 386 randomised participants across the
  two trials, both reporting tolerability similar to placebo. Its
  `safety_liability_burden` carries `counter_level: 3` for that reason.

**The blackboard worked.** An agent declared a gap it could not close, in a required
field, and named which way it might move the grade. The gap was closed by a different
agent and it moved the grade down. That mechanism is worth more than the finding.

---

## 2. Downgrades applied

Five, on four targets. Recorded in each audit's `adjustments` block; no other agent's
file was edited. For `counter_level` a *raise* is the downgrade, because stronger
contradicting evidence lowers the target's standing.

| Target | Facet | Field | From → To | Ground |
|---|---|---|---|---|
| **TGT:CRTC1** | `human_genetic_association` | level | **3 → 1** | Its entire level-3 basis is one *"Self-reported math ability"* association from an educational-attainment GWAS. §3. |
| **TGT:GABRA5** | `human_intervention_evidence` | counter_level | **3 → 4** | The human null is now replicated across two trials, consistent in direction, one with demonstrated target engagement. §1. |
| **TGT:GABRA5** | `above_baseline_enhancement` | counter_level | **3 → 4** | Same evidence, plus the within-study discrimination cost in mouse and the opposite-direction benefit in aged rats. |
| **TGT:PDE4B** | `above_baseline_enhancement` | level | **3 → 2** | The intervention is a **pan-PDE4** inhibitor. As evidence about *this gene* the endpoint is directly relevant but the target attribution is not. §4. |
| **TGT:PDE4B** | `dose_response_knowledge` | counter_level | **1 → 2** | Measured non-monotone exposure–response: benefit at the **lowest** of three doses, no PDE4-typical side effects at that dose. |

**Claim statuses changed: five.** `CLM:alphacognition:gwas.CRTC1:002` and
`CLM:power:HCAR1:004` (this audit's own findings), plus three self-declared contestations
that had no audit record behind them and were therefore unreviewable under rule V14 —
`CLM:power:KL:001`, `CLM:power:anls:001`, `CLM:power:creatine_human:001`. All five are
`contested`, none `withdrawn`: in every case the underlying experiment is real and
correctly described, and what is in dispute is what it licenses.

**Nothing was deleted and no level was raised.**

---

## 3. Educational attainment is being laundered into fluid reasoning

A **critical** finding, and the clearest instance of the failure mode
`agent:alphacognition` predicted about itself: *"if that rule is wrong, it is wrong 108
times identically."*

`atlases/alphacognition/cognitive_trait_panel.yaml` classifies GWAS Catalog trait
*mathematical ability* (EFO_0004875) as `phenotype_class: fluid_reasoning`, and
simultaneously marks it `use_in_ranking: supporting` with the note:

> *"Partly an achievement measure (it depends on instruction), so supporting only, never a
> stand-alone basis for a facet level."*

That restriction is correct and clearly intended. But
`pipelines/alphacognition/build_assessments.py` tests membership of
`DIRECTLY_RELEVANT = {g_factor, fluid_reasoning}` — it reads `phenotype_class` and
**never reads `use_in_ranking`**. So the restriction never fires.

The underlying records are *"Self-reported math ability"* and *"Highest math class
taken (MTAG)"* from `SRC:PMID:30038396`, whose own title is *a genome-wide association
study of **educational attainment** in 1.1 million individuals*. "Highest math class
taken" records which course a person enrolled in.

The rule has an explicit EA cap on `causal_gene_attribution`. It fails to help, because
the cap also tests the `phenotype_class` *label*, and **the laundering happens at the
trait→class mapping step, upstream of the cap.**

Five claims rest entirely on such records: `gwas.CRTC1:002`, `gwas.GRIN2B:003`,
`gwas.OTX2:002`, `gwas.PDE4B:003`, `gwas.SLC16A7:002`. The scope of damage is **bounded
and specific**:

- **CRTC1 — grade falls.** It is the stand-alone basis, exactly as the panel forbids.
  CRTC1 has *no* non-education cognitive association of any kind. Downgraded 3 → 1, which
  is the rule's own value for "associations only on educational-attainment or literacy
  traits". This downgrade applies the atlas's stated rule rather than substituting the red
  team's judgement for it.
- **GRIN2B, OTX2, PDE4B, SLC16A7 — grades survive**, on genuine intelligence-trait
  associations from other publications. Only the *rationale strings* are overstated: they
  count the math records among the directly-relevant ones.

A second, subtler channel that no cap addresses: `SRC:PMID:29326435` is an MTAG that
combines education and intelligence GWAS *explicitly to gain power* (its abstract records
their genetic correlation as 0.70). Records from it are classed `g_factor`. They are
education-*informed* composites rather than pure intelligence endpoints, and one of
GPR158's two directly-relevant records comes from it. This is not a mislabelling —
"Intelligence (MTAG)" is what the catalogue calls it — so it is recorded as a limit on
interpretation rather than a defect.

**On the genetics headline itself**, audited in both directions as asked: the claim that
zero of 27 targets have molecular-QTL colocalisation supporting their gene assignment is
correct for the pinned release, and neither too charitable nor too harsh. One qualification:
thin QTL coverage explains why colocalisation is *absent*; it does not license the
inference that it would be *found* with better coverage. The honest position is that gene
attribution for these targets is **unresolved, not pending**.

---

## 4. Targets whose case collapsed, and which survived best

### Collapsed

| Target | What collapsed |
|---|---|
| **GABRA5** | Not the biology — the *translation*. Replicated rodent memory enhancement, confirmed human target engagement, two null human cognitive composites. The clearest demonstrated instance in the repository of the failure mode contract principle P4 exists to prevent. |
| **CRTC1** | Its human genetic case. After the downgrade it has one adult viral overexpression study in mice and no non-education human association. |
| **GRM5** | Verdict `deprioritise`. The mechanism failed on behavioural endpoints in adults with fragile X (per the sponsor's registry statement, terminating two further studies totalling 267 participants), then on a measured cognitive endpoint in 3-to-6-year-old children — in a trial *designed* on the expectation that younger brains would respond where adults had not. The developmental argument runs backwards. |
| **GPR158** | Verdict `deprioritise`. Its **sign is unresolved**: one literature makes it an excitability brake, another the receptor for a memory-promoting hormone, and the brake atlas's own grading puts the contradicting evidence *above* the supporting evidence. `agent:brakes` asked whether it belongs in a brake atlas at all. It does not: a target whose direction of desirable manipulation is unknown is not a control point, and calling it a brake asserts a sign the evidence does not support. |
| **OTX2** | Verdict `deprioritise`. Its demonstrated primary function is to **close** a developmental critical period; the single adult manipulation reopens that programme rather than operating an adult one, and nothing measures the cost of returning an adult cortex to a juvenile regime. `developmental_confound_risk: 4`. |
| **SLC6A8** | Not collapsed so much as *reclassified*: a restoration target, not an enhancement target, on its own evidence. `developmental_confound_risk: 4` — the only grade in this audit resting on a **measured** dissociation rather than a design weakness: neonatal deletion produced learning deficits, adult deletion produced none, in the same model. |
| **HCAR1** | `CLM:power:HCAR1:004` contested. A weight-loaded **swimming endurance** endpoint in male mice mapped onto a cognitive state variable. The curating agent nominated this as its own worst leap and disclosed it in the record; a construct jump cannot be fixed by re-reading the source. |

### Survived best

- **EIF2B_COMPLEX** — verdict `retain`. The cleanest adult-onset case in the repository:
  the enhancing manipulation is an acute systemic small molecule in adult mice, and the
  human genetic evidence includes an **adult-onset** disease form with a stated mean age
  at onset. Its real limit is not developmental but that the mechanism is gated on
  phosphorylated eIF2α, which cannot be measured in a living human.
- **SLC16A7** — verdict `retain`, with the repository's most striking asymmetry: the best
  mechanistic evidence in the power atlas (genuinely adult, acute, adult-tested) and
  **zero human data of any kind**.
- **SLC16A3** — verdict `retain`. Adult and acute throughout.
- **PDE4B** — survives a downgrade rather than collapsing. Its human above-baseline
  improvement in healthy adults is *real*: a properly conducted randomised crossover, and
  the only above-baseline human enhancement anywhere in the brake atlas. It is just much
  narrower than a level-3 grade implies — a 2–3 word gain on **immediate recall only**, at
  the **lowest of three doses**, with a **pan-PDE4** drug, from **one research group**.
- **ADORA1** — best negative-evidence discipline of any target: two human clinical nulls
  recorded by the curating agent, both properly typed. Its limit is that the decisive
  design (rested, non-withdrawn, caffeine-naive adults) does not exist in the literature,
  so every positive adult result remains consistent with withdrawal reversal.
- **THEORY.md** — verdict `retain`, and it deserves saying plainly. §1.2 is titled
  *"Multiplicativity is a MODELLING CHOICE, not a law"*; §1.4 is titled *"The POWER factor
  may not be limiting at all in healthy adults"*; §4.2 lists inferences the theory does
  not license and pre-empts eight of this audit's seventeen checks. All 33 claim ids it
  cites resolve, and **no empirical statement cites a claim that does not support it.**

### The power atlas's H0 conclusion, audited in both directions

It holds, and my independent search *corroborates* rather than breaks it. I reached
`SRC:PMID:35984306` independently: the young-adult band sits at SMD **0.03** (95% CI
−0.14 to 0.20) with **I² = 0%** across eight RCTs, while the benefit sits in the 66–76
year subgroup. I also found a second pooled analysis the atlas did not cite
(`SRC:PMID:39070254`, 16 RCTs, 492 participants) finding no significant improvement in
overall cognitive function or executive function, with larger benefit in people with
disease.

So: **at the creatine node the conclusion is if anything too weak** — that is a tight
null, not an inability to tell. **At the system level "cannot reject H0" is exactly
right**, because 16 of 22 power/efficiency state variables remain `unknown`, including
every variable H2 and H4 depend on. The atlas hedged at the right level and was firm at
the right level.

---

## 5. Repository-level epistemic risks

### 5.1 A literature-only search is not a search — and three atlases have not been re-checked

`agent:power` **overturned two of its own published statements** when forced to justify
its zeros: it had asserted that no human klotho intervention and no human MCT1
intervention existed. Both were wrong. Both were found by a target-directed *registry*
search.

This audit reproduced the pattern independently and at scale. **Four of its five most
consequential findings came from a `whyStopped` or `resultsSection` field that no
literature search can return**: the α5 paediatric termination, the CHRM1 toxicology
withdrawal, the retigabine market withdrawal, and the AFQ056 efficacy failures — plus the
GABRA5 posted results.

The mechanism is simple and it is structural: **a programme that stops generates no
paper.** So a literature-derived evidence base is blind to precisely the outcomes most
damaging to a target, and drifts positive no matter how honest each individual record is.

> **Every level-0 human-evidence grade in this repository that rests on a literature
> search should be treated as provisional until a registry search has been run for that
> mechanism.** `agent:brakes`, `agent:alphacognition` and `agent:comparative` have not been
> re-checked this way. On this audit's hit rate, doing so should be expected to overturn
> something.

### 5.2 Two kinds of gap that must not be pooled

The lactate axis supplies a matched pair:

- **Measurement gap** — `NCT01791595` (AZD3965) reported in full and *never asked* the
  cognitive question: every primary outcome is toxicity, every secondary is
  pharmacokinetic, a cell-death marker or tumour response. Visible in the registry,
  representable as a graph-inert `evidence_gap`, a fact about **coverage**.
- **Reporting gap** — `NCT01455376` *asked* the question as its **primary outcome**,
  completed in June 2010, and has posted nothing in **sixteen years**. Representable only
  as `reporting_gap_refs`, never as counter-evidence, a fact about **publication bias**.

Pooling them loses the only distinction that matters: the first says the literature has
not looked; the second says it has looked and you cannot see what it found. The red team
made this error itself in a first draft and the validator caught it
(`docs/RED_TEAM_METHOD.md` §4.3).

The ranking consumes the *level*, not the reporting-gap list, so a zero caused by a
completed unreported trial currently ranks identically to a zero caused by nobody trying.
Surfacing a reporting-gap count as a report column alongside `coverage` would close that.

### 5.3 Citation and cohort concentration

- **Two educational-attainment GWAS carry 40 of the repository's 290 curated claims**
  (`SRC:PMID:30038396`: 20; `SRC:PMID:35361970`: 20). The largest single cohort string is
  Okbay 2022's ~3.04 million European sample, in **14** evidence items.
  `SRC:PMID:37365406` is **UK Biobank only** (n=336,993) and carries 6 claims.
- **Only 5 claims mention UK Biobank in text.** The concentration is invisible to a text
  search and had to be found by grouping sample-size strings. **Nothing in the repository
  de-duplicates cohorts**, so two catalogued associations on one trait can be the same
  participants twice.
- **Every Open Targets `safetyLiabilities` row used in this audit traces to one of two
  PMIDs** (`SRC:PMID:28216264`, `SRC:PMID:23197038`), and both are
  pharmaceutical-industry safety-pharmacology *curation reviews* over overlapping
  literature. Two rows agreeing is close to one source agreeing with itself. The
  target-level safety layer for six targets rests on two review papers — which is why no
  grade resting on them alone exceeds level 2.
- **Named cross-lane dependency**: `SRC:PMID:30340039` and `SRC:PMID:20837545` are
  load-bearing for the brake atlas's *mechanistic* case **and** the comparative atlas's
  *translation-risk* case. `agent:comparative` documented this itself. If either paper is
  wrong, two apparently independent arguments fall together.

### 5.4 The ranking is invariant to duplicated evidence but not to duplicated targets

Up to **seven of the 27 seed targets are fewer than seven independent evidence bases**:

- **SLC16A1 / SLC16A3 / SLC16A7** share all their founding sources. `SRC:PMID:21376239`
  alone carries the founding claim of all three *plus* the shuttle hypothesis they inherit.
- **KCNQ2 / KCNQ3** rest on **one experiment with one construct** acting on their shared
  heteromer. (`agent:brakes` anticipated this and graded KCNQ3 one level below KCNQ2
  throughout — the correct response, and worth naming as good practice.)
- **EIF2S1 / EIF2B_COMPLEX** are the substrate and the GEF of one pathway.

And `CLM:power:anls:001` is a **single point of failure beneath four targets**: SLC16A1,
SLC16A3, SLC16A7 and HCAR1 all inherit the astrocyte–neuron lactate shuttle's
credibility, so a downgrade of it should cascade to all four rather than to none. Asked
to pick a side on the shuttle, this audit **declines** — the published critique is a
methodological argument, not a failed replication, and nothing retrieved here resolves
it. The cascade is put on the record instead.

`tests/test_ranking_invariance.py` tests invariance to duplicated *evidence*; duplicated
*targets* is the live risk, and the model cannot see it because it consumes grades.

### 5.5 Coverage asymmetry penalises knowledge

- **`safety_liability_burden` is 0 for 11 of 27 targets** — "searched, found nothing".
  Every one carries a `search_basis` stating that an empty Open Targets list means *that
  source is silent*, not that the target is safe. Contract §5.4 is invoked explicitly:
  on an inverse-polarity facet the weakness of the search does **not** lower the level.
- **HDAC2 is the clean demonstration.** Open Targets returns *no* target-level safety
  annotation, while the oncology HDAC-inhibitor class carries thrombocytopenia,
  hepatotoxicity, fatigue and hypoacusis. An empty database list must never be graded 0.
- **25 of 27 targets have no `cross_species_convergence` grade at all** and 23 have no
  `human_lineage_divergence_risk` grade. Correctly handled downstream — `not_assessed`
  maps to Beta(1,1) and keeps its weight, so those targets *widen* rather than sink — but
  it means two of the fifteen facets are effectively unpopulated.
- **The uncomfortable artefact**: the best-characterised targets accumulate the most
  damaging findings and the least characterised ones look clean. This audit penalises
  knowledge, and the contract offers no way to mark "unaudited because nobody tried" as
  worse than a low grade.

### 5.6 `direction` is used with two incompatible meanings

A silent, mechanical risk in the brake atlas's regulation claims — and it is exactly where
`agent:brakes` said to look, having hand-inverted six coupling directions when re-pointing
a seizure *threshold* onto `SV:safety.seizure_risk`.

The **sign chains themselves check out.** Suppressing the M-current raises intrinsic
excitability and produced spontaneous seizures, so the excitability→`seizure_risk` coupling
of `direct` is right, and the variable declares `polarity: risk` with an id ending
`_risk`. Verified end to end against `SRC:PMID:15608631`.

But the claim-level `direction` field does not mean one thing:

| Claim | Predicate | `direction` | `effect_direction` | Reading |
|---|---|---|---|---|
| `CLM:brakes:GABRA5:001` | `NEGATIVELY_REGULATES` | `decreases` | `increase` | `direction` = sign of the **regulation** |
| `CLM:brakes:KCNQ2:001` | `POSITIVELY_REGULATES` | `decreases` | `decrease` | `direction` = the **observed change** |

Both cannot be right under one convention, so no consumer can read `direction` correctly
for all of them. Related and worse: `CLM:brakes:GABRA5:003`'s object is
`SV:workspace.interference_susceptibility` while its measured endpoint is a
*discrimination ratio* — the polarity **inverse**. The deletion impaired discrimination,
i.e. raised susceptibility, but `effect_direction: decrease` describes the ratio. Nothing
in the record marks the inversion, so a mechanical reader that takes `object` +
`effect_direction` concludes the deletion *improved* interference control — the opposite
of the paper's finding, and the finding is the **cost** that makes GABRA5's
`transfer_breadth` counter_level 3.

This is a defect of the contract as much as of the atlas: §4 does not disambiguate
`direction` for regulation claims. It needs a schema-change request, which is not the red
team's to file.

### 5.7 One dangerous record shape is absent, and one is isolated

Both checked repository-wide, and both are **good news**:

- **No measured human null wears a positive relation.** `CLM:alphacognition:HTR2A:003` had
  that shape before migration — as `MODULATES`, a measured human null would have compiled
  as *support*. Migration verified. 25 claims do carry contradicting or null evidence on
  non-null relations, but in each the claim's own assertion is a positive finding that
  happens to contradict a *different* proposition, which is correct use.
- **Animal evidence wearing a clinical label occurs exactly once**, in
  `CLM:brakes:HCN1:005`, which the curating agent self-declared and which has been retyped
  `clinical_harm` → `preclinical_harm`. **Retype verified correct** by direct inspection:
  species mouse, `human_relevance: rodent_only`, `basis: germline_knockout`, design
  knockout. This is the mirror of the null-on-a-positive-relation problem and it is easier
  to miss, because over-stating a harm feels conservative.

---

## 6. Numbers

| | |
|---|---|
| Targets audited | **27 / 27** (rule V15) |
| Audit records | **30** (27 target, 1 document, 2 model) |
| With complete 17-check catalogue | **30 / 30** — 510 rows |
| Check results | 131 `pass` · 246 `flag` · 60 `fail` · 73 `not_applicable` |
| Findings | **57** — 4 critical · 32 major · 13 minor · 8 info |
| Downgrades applied | **5**, on 4 targets (§2) |
| Claim statuses changed | **5**, all `active` → `contested` |
| Verdicts | 3 `retain` · 19 `retain_with_downgrade` · 3 `deprioritise` · 2 `insufficient_evidence` |
| New sources registered | **17**, **17 verified** (first pass, no failures) |
| New claims | **13** |
| `safety_liability_burden` | 0×11 · 1×5 · 2×5 · 3×4 · 4×2 |
| `developmental_confound_risk` | 0×6 · 1×4 · 2×8 · 3×7 · 4×2 |
| `--strict` in red-team files | **0 errors, 0 warnings** |

**Critical findings (4):** GABRA5 `negative_clinical_evidence`; CRTC1 and the genetics
facet rule `educational_attainment_mistaken_for_intelligence`; GRM5
`model_organism_translation_failure`.

**Gates these grades now fire** in `models/ranking/ranking_spec_v0_1.yaml`, stated so
`agent:integration` is not surprised:

- `developmental_confound_caps_d2` → **TGT:SLC6A8** (4 / counter 0), **TGT:OTX2** (4 / 1)
- `safety_liability_caps_d5` → **TGT:CHRM1** (4 / 1), **TGT:KCNQ2** (4 / 0)
- `unresolved_critical_finding_caps_composite` → **TGT:GABRA5**, **TGT:CRTC1**, **TGT:GRM5**

---

## 7. Where this audit is weakest

In order. Full treatment in [`docs/RED_TEAM_METHOD.md`](../docs/RED_TEAM_METHOD.md) §3–§4.

1. **The red team's own two facets were graded by nobody else and checked by nobody.**
   Most exposed: **KCNQ2 `safety_liability_burden: 4`**, flagged in its own record as the
   audit's most contestable grade — it rests partly on a market withdrawal whose cause is
   undisclosed and whose direction of modulation is the *opposite* of the one proposed. At
   level 3 the D5 gate would not fire. **CHRM1: 4** also fires that gate on two human
   studies, the second of which is small.
2. **Only ClinicalTrials.gov was queried.** Given that registry search produced four of
   five headline findings, the absence of WHO ICTRP, EudraCT and national registries is
   the largest gap in the method.
3. **Almost no full text.** `extraction.basis: full_text` appears nowhere in the red-team
   claims. The GABRA5 posted results are the exception and are the strongest record here
   because they are primary numbers.
4. **The two safety curation reviews' own tables were never opened**, which is why every
   safety claim resting on them is graded 1 or 2.
5. **Two named records remain unverified and are load-bearing for their targets**:
   `CLM:brakes:RGS14:004` (a review-only claim that is simultaneously RGS14's *only*
   human-relevant evidence) and `CLM:power:CKB:002` (the one `content_checked: false`
   record in the power atlas, resting on a one-sentence secondary report).
6. **246 `flag` results is too many to be individually load-bearing.** A flag means "worth
   watching", not "wrong". The next auditor should test whether the threshold was set low
   enough to be uninformative.
7. **The eleven level-0 safety grades** reflect a method biased towards mechanisms that
   reached the clinic (§5.5).
8. **Brain QTL resources beyond Open Targets were unreachable**, so the genetics headline
   could not be independently tested against a wider catalogue.

---

## 8. Open items for other agents

- **`agent:integration`** — §6 lists the gates that now fire. §5.4 is the substantive
  warning: the model is invariant to duplicated evidence but not to duplicated targets,
  and `CLM:power:anls:001` sits beneath four of them. `AUD:red_team:RANKING_MODEL:001#f1`
  records the one structural exposure: **D1 aggregates additively**, so a level-3
  positional association contributes support at weight 0.25 regardless of the
  gene-attribution grade beside it — and gene attribution reaches 3 or 4 for *no* target.
  There is a gate for developmental confound, absent human evidence, absent human
  intervention and high safety liability, but **no gate on unresolved gene attribution**,
  so the item the spec itself calls "the single weakest link in the whole evidence chain"
  is the one thing fully tradeable within its dimension.
- **`agent:alphacognition`** (for a future sprint) — the one-field fix in §3:
  `build_assessments.py` should read `use_in_ranking`, not only `phenotype_class`.
- **`agent:ontology` / orchestrator** — §5.6 needs a schema-change request to
  disambiguate `direction` on regulation claims. Not the red team's to file.
- **Orchestrator** — one informational V22 warning remains and is not in the red team's
  lane: `SRC:NCT:NCT01455376` and `SRC:NCT:NCT07285629` are registered by `agent:power`
  and cited by no claim of its own. Note that `NCT01455376` **is** now cited, in this
  audit's `reporting_gap_refs` on SLC16A1 — so V22 appears to attribute citation
  per-registering-file rather than per `source_id`, which is worth confirming before
  anyone "fixes" a source that is in fact in use.
- **`agent:brakes`** — the two claims it flagged about itself are resolved:
  `CLM:brakes:GABRA5:008` and `CLM:brakes:ADORA1:007` **describe their curation-table
  source exactly** and should be **retained**, not withdrawn. Two residual defects: both
  have `context.species` human with `translation.human_relevance: other_species_only`
  (the source attributes no species at row level, so `unknown` is honest for both fields);
  and `ADORA1:007` **conflates directions** — every cardiac and lethal event in the
  underlying annotation belongs to A1 *activation*, only convulsions to *inhibition*, so
  the record attaches agonist liabilities to an antagonist strategy. Conservative in
  effect, wrong in fact. `CLM:red_team:ADORA1:001` records the direction-resolved version.
