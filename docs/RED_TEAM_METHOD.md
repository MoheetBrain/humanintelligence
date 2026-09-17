# Red Team Method — Sprint 1

How `agent:red_team` searched, what it could not search, and the biases of its own
method. Written so that the next auditor can reproduce the audit, and so that a reader
can discount it correctly.

---

## 1. The asymmetry, and what it costs

The red team has one asymmetric power and one hard limit: **it may lower a confidence
level, and it may never raise one or delete provenance.** An auditor that can do both is
a second opinion; the asymmetry is what makes this one a falsifier.

That asymmetry has a cost and it should be stated before the findings. A falsifier with
no power to promote will, over many sprints, drift the repository pessimistic: every
error it catches in the optimistic direction gets corrected, and every error in the
pessimistic direction stays. Three deliberate counterweights were used here:

1. **`pass` is a real verdict and was used 131 times** across 510 catalogue rows. Where
   an atlas's handling holds up, this audit says so in the same register it uses for
   failures — see `negative_clinical_evidence: pass` on ADORA1 and SLC6A8,
   `provenance_integrity: pass` on the genetics facet rule, and the whole THEORY.md audit.
2. **Counter-evidence was graded as carefully as evidence.** On `safety_liability_burden`
   the counter side is where a target's defence lives, and GABRA5 carries
   `counter_level: 3` there on the strength of two randomised human trials reporting good
   tolerability — a favourable finding that a pessimistic auditor would have omitted.
3. **Two grades were revised UPWARD in severity late in the run** (CHRM1 and KCNQ2 safety,
   3 → 4) after reading the ranking spec's gate thresholds. Both are flagged in their own
   records as consequential, and the KCNQ2 grade is flagged as the audit's most
   contestable so it can be overridden without re-deriving it.

Where this audit could not decide, it says so rather than resolving the tie downward. The
clearest case is `CLM:power:anls:001`: asked to pick a side on the astrocyte-neuron
lactate shuttle, the red team declined, because the published critique is a
methodological argument rather than a failed replication.

---

## 2. Search strategy

### 2.1 Order of work: independent search first

Per the blackboard protocol, the red team read the domain atlases' conclusions as
**targets for falsification, not as authority**. The independent searching was done
*before* the atlas records were read in detail, so that the search terms were driven by
the mechanisms in `targets/seed_registry.yaml` rather than by what each atlas had already
found. That ordering is why the two largest findings are things no atlas had:
a published trial result and a registry withdrawal reason.

### 2.2 The registry-first move, which is the method's single most productive choice

**The highest-yield decision in this audit was to search trial registries before, and
independently of, the literature.** Four of the five most consequential findings came
from `ClinicalTrials.gov` API v2 fields that no literature search can return:

| Finding | Field |
|---|---|
| α5-GABA-A NAM: paediatric trial stopped because another trial showed no efficacy | `whyStopped` |
| CHRM1: phase 2 withdrawn for an unexpected animal toxicology finding | `whyStopped` |
| KCNQ2/KCNQ3: retigabine withdrawn from market | `whyStopped` |
| GRM5: AFQ056 failed efficacy in two named studies | `whyStopped` |
| GABRA5: the MCCB composite treatment difference and its confidence interval | `resultsSection` |

`docs/API_RECIPES.md` §3 says `whyStopped` "is often the most informative field in the
whole record for a red-team audit." That is an understatement. A programme that stops
generates no paper, so **a literature-only search is systematically blind to the
outcomes most damaging to a target** — see §5.1.

Filters used: `filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED` for programme fates,
then unfiltered searches by intervention name to catch COMPLETED trials that reported no
benefit. Both were needed: the decisive GABRA5 trial is COMPLETED, not terminated, and
would have been missed by a terminated-only filter.

### 2.3 What was searched, by route

* **ClinicalTrials.gov API v2** — by intervention for every mechanism with plausible
  clinical history: basmisanil/RG1662/RO5186582, HTL0018318, DNL343/ABBV-CLS-7262/ISRIB,
  retigabine/ezogabine, mavoglurant/AFQ056/basimglurant, AZD3965, exogenous lactate.
  Every record relied on was re-fetched from the API into
  `data/raw/ctgov_v2/2026-09-17/` through the repository's own
  `scripts/_provenance.write_snapshot`, so `whyStopped` and `resultsSection` are on disk
  with a sha256 in `data/raw/MANIFEST.jsonl` and the audit is rebuildable offline.
* **PubMed** — targeted searches for published trial outcomes and for pooled analyses,
  including deliberate searches for *nulls*: creatine cognition meta-analyses, PDE4
  healthy-volunteer cognition, HDAC-inhibitor cognition trials.
* **Open Targets Platform 26.06 GraphQL** — `safetyLiabilities` for all 31 gene symbols
  covering the 27 targets, in two batched queries, capturing `event`, `datasource`,
  `literature`, and critically `effects { direction dosing }`. **The direction field is
  what makes these usable**: it distinguishes a liability of activating a target from a
  liability of inhibiting it, and the proposed direction of manipulation is what a
  liability grade is about. Six targets returned non-empty lists; 21 returned nothing.
* **Mechanical scans over the whole repository** — a single read-only script over all 290
  curated claims and 129 assessments, answering ten questions at once (null evidence on
  positive relations; `evidence_gap` versus measured-null typing; educational-attainment
  endpoints; `content_checked: false`; source fan-in; facet distributions and level-0
  `search_basis` presence; population-string grouping for cohort concentration; clinical
  claim types on non-human evidence; seizure/excitability sign chains; status and
  translation distributions). **This is how the systematic findings were found.** A
  sample of records would not have revealed that five claims launder an
  educational-attainment measure, or that two papers carry 40 of 290 claims.

### 2.4 Verification

Every identifier in `evidence/sources/red_team.yaml` was seen in a tool response in this
session; none was written from memory. All 17 reached `status: verified` on the first pass
of `scripts/fetch_source_metadata.py --agent red_team`. No identifier was ever "corrected"
by guessing — see §4.3 for the one registration that was wrong and how it was fixed.

---

## 3. What could not be searched

Stated as limits on the audit, not as properties of the evidence.

1. **Non-US and non-indexed trial registries.** Only ClinicalTrials.gov was queried. WHO
   ICTRP, EudraCT and national registries were not, so a programme run only outside the US
   would have been missed entirely. Given that §2.2 shows registry search to be the
   highest-yield route, this is the largest single gap in the method.
2. **Full text.** Almost every extraction is from an abstract or a registry record.
   `extraction.basis: full_text` appears nowhere in the red-team claims. So where an
   abstract omits a caveat that the methods section contains, this audit inherits the
   omission. The GABRA5 posted results are the exception and are the strongest record
   here precisely because they are primary numbers rather than a summary.
3. **The underlying rows of the two safety curation reviews.** `SRC:PMID:28216264` and
   `SRC:PMID:23197038` were read as abstracts and their Open Targets-derived rows were
   read as data, but the reviews' own source tables were not opened. So every
   safety-liability claim in this audit describes *what the curation says*, which is why
   each is graded 1 or 2 and never higher.
4. **Brain QTL resources beyond Open Targets.** PsychENCODE and MetaBrain were not
   reachable, so the genetics headline — zero of 27 targets with molecular-QTL
   colocalisation — could not be independently tested against a wider QTL catalogue. The
   audit therefore records that gene attribution is *unresolved* rather than confirming it
   is *absent*.
5. **`CLM:brakes:RGS14:004`'s primary evidence.** This is the brake atlas's only
   review-only claim and simultaneously RGS14's only human-relevant evidence. The review's
   primary sources were not retrieved, so whether it says what the claim says is
   **unverified by this audit** and is recorded as an open item rather than a cleared one.
6. **`CLM:power:CKB:002`'s primary paper.** The one `content_checked: false` record in the
   power atlas rests on a one-sentence secondary report. It remains unretrieved, so the
   automatic downgrade stands.
7. **Dose and regimen detail.** No dose appears in any red-team record except where a
   source states it verbatim in an `as_reported` string, per contract P3.

---

## 4. Biases of this method

### 4.1 It is biased towards mechanisms that reached the clinic

The audit's power comes from registry and trial evidence, which exists only for targets
someone took into humans. GABRA5, CHRM1, GRM5, KCNQ2/3, PDE4B and SLC16A1 were audited
hard because there was something to audit. **Eleven of 27 targets received
`safety_liability_burden: 0`** — "searched, found nothing" — and for those the audit is
thin in a way that must not be mistaken for a clean bill of health. Every one of those
zeros carries a `search_basis` stating that an empty Open Targets list means *that source
is silent*, and contract §5.4 is invoked explicitly: on an inverse-polarity facet the
weakness of the search does **not** lower the level, because weak evidence cannot
establish the absence of a risk.

This produces a specific, uncomfortable ranking artefact worth naming: **the
best-characterised targets accumulate the most damaging findings, and the least
characterised ones look clean.** An audit of this shape penalises knowledge. The
counterweight available in the contract is that `not_assessed` and level-0 are kept
distinct and that coverage is a required report column; the counterweight *not* available
is any way to mark "this target is unaudited because nobody has tried it" as worse than a
low grade.

### 4.2 It is biased towards what a database field can express

`whyStopped` gave four findings; "Company Decision" gave none. Two fosigotifator
terminations and one withdrawn expanded-access programme are recorded as *context* and
deliberately **not** as claims, because a sponsor's silence is not evidence about
biology. So the ISR-inhibitor class carries real unfavourable clinical history that this
audit can see but cannot grade. That is the honest outcome and it means the EIF2B_COMPLEX
and EIF2S1 safety grades are less informative than the underlying reality.

### 4.3 It made three errors of its own, all caught by the validator

Recorded because an auditor that reports only other agents' errors is not credible.

1. **A reporting gap typed as an `evidence_gap`** (V16c). The lactate-infusion trial
   `NCT01455376` declared a neurocognitive primary outcome and never published; that is a
   *reporting* gap, whose mechanism is `reporting_gap_refs` on a facet, never a claim.
   The draft claim `CLM:red_team:SLC16A1:002` was removed — it had never been locked, so
   no provenance was deleted — and the fact now lives in the `publication_bias` checks on
   SLC16A1 and HCAR1, in `reporting_gap_refs` on SLC16A1's safety facet, and in §5.2 of
   the report.
2. **An illegal triple** (V3): `GENE:SLC16A1 -ABOUT-> PHENO:clinical_cognitive_composite`.
   `ABOUT` has an evidence-layer domain, so a Gene cannot be its subject. Removed with the
   claim.
3. **A divergent duplicate registration** (V4): `SRC:NCT:NCT01455376` was registered with
   the registry's `briefTitle` while `agent:power` had used the `officialTitle`.
   `fetch_source_metadata.py` verifies against `officialTitle` first, so **agent:power's
   registration was the correct one and the red team's was wrong.** Corrected to match
   field for field, with the correction noted at the record. The identifier was never
   guessed at; the exact title was re-read from the snapshot on disk.

Two lessons generalise. The first is that duplicate registration is safe only because
divergence is a hard error — that rule caught a real copy error within minutes. The
second is that `evidence_gap` is easy to over-apply: it is tempting to file any absence
under it, and the distinction R5 drew between an absence of measurement and an absence of
reporting is doing real work.

### 4.4 It cannot audit its own facet grades

The red team owns `safety_liability_burden` and `developmental_confound_risk` for all 27
targets and audits everything except those. Nobody graded them independently and nobody
checked them. The most exposed judgements, in order:

1. **KCNQ2 `safety_liability_burden: 4`**, which fires `safety_liability_caps_d5`. It
   rests partly on a market withdrawal whose cause is undisclosed and whose direction of
   modulation is the *opposite* of the one this project proposes. At level 3 the gate would
   not fire. Flagged in the record itself as the audit's most contestable grade.
2. **CHRM1 `safety_liability_burden: 4`**, which also fires that gate. Defensible on two
   independent human studies, but the second is a small 10-day healthy-volunteer study.
3. **The eleven level-0 safety grades**, for the reason in §4.1.
4. **Three `developmental_confound_risk` grades converted from `unknown` to a searched 0**
   (DRD1, HTR2A, plus PDE4B graded 0 on a clean search). A searched zero over a thin
   curated literature is much weaker than a searched zero over a thick one, and each
   `limiting_factor` says so — but they are recorded on the same 0–4 scale and a consumer
   reading the level alone cannot tell them apart.

### 4.5 One agent, one session, no independent replication

Every judgement here is one agent's. The check catalogue was applied by a generator
(written in the session scratchpad, since `docs/OWNERSHIP.yaml` gives the red team no
`pipelines/` lane) so that 27 targets got the *same* 17 questions rather than 27
inconsistent readings — the same reasoning `agent:alphacognition` gave for generating its
genetics facets. The per-target judgements inside that scaffold are hand-written. The
generator carries two self-checks that both fired during the run and caught real errors:
an assertion that every seed target has an audit and no audit exists for a non-seed
target, and an assertion that every claim id referenced anywhere resolves against the
claim set. The second caught a reference to the claim removed in §4.3.

---

## 5. Two methodological findings that apply beyond this audit

### 5.1 A literature-only search is not a search

`agent:power` overturned **two of its own published statements** when forced to justify
its zeros — it had asserted that no human klotho intervention and no human MCT1
intervention existed, and a target-directed registry search showed both were wrong. This
audit reproduced the pattern independently and at scale: four of its five most
consequential findings are registry fields.

**The other three atlases have not been re-checked this way.** Every level-0
human-evidence grade in this repository that rests on a literature search should be
treated as provisional until a registry search has been run for that mechanism. This is
recorded as a repository-level risk in `reports/red_team_audit_v0_1.md` §5.1 and as a
`publication_bias` flag in the default check set of every target audit.

### 5.2 Two kinds of gap that must not be pooled

The lactate axis supplies a clean matched pair, and the distinction generalises to the
whole repository:

* **A measurement gap.** `NCT01791595` (AZD3965) reported in full and *never asked* the
  cognitive question — every primary outcome is toxicity, every secondary is
  pharmacokinetic, a cell-death marker or tumour response. Visible in the registry,
  representable as an `evidence_gap` claim, graph-inert, and a fact about **coverage**.
* **A reporting gap.** `NCT01455376` *asked* the question as its primary outcome,
  completed in June 2010, and has posted nothing in sixteen years. Representable only as
  `reporting_gap_refs`, never as counter-evidence, and a fact about **publication bias**.

Pooling them would lose the only distinction that matters: the first tells you the
literature has not looked, the second tells you it has looked and you cannot see what it
found. The second is the one that makes an evidence base drift positive.

A related scoping decision was upheld rather than widened. `agent:power` listed
`NCT01455376` as a reporting gap against `HCAR1` alone and not against the three MCT
targets, reasoning that the trial engages the transporters' *substrate* rather than the
transporters. **The red team upholds that** and declines to widen it: counting one
unreported study as four reporting gaps inflates a bias count by re-counting one study,
which is structurally the same error as inflating evidence by re-citing one paper. The
same discipline was applied to `CLM:red_team:SLC16A1:001`, whose retinopathy and anaemia
findings are MCT1 functions in retina and erythrocyte and are deliberately **not** cited
in the SLC16A7 or SLC16A3 safety grades.

---

## 6. Reproducing this audit

```
# Registry records (writes immutable snapshots + manifest lines)
GET https://clinicaltrials.gov/api/v2/studies/{NCT_ID}
    -> read protocolSection.statusModule.whyStopped
    -> read resultsSection.outcomeMeasuresModule and adverseEventsModule

# Programme fates by mechanism
GET .../studies?query.intr={drug}&filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED

# Target-level safety, with the direction field
POST https://api.platform.opentargets.org/api/v4/graphql
  target(ensemblId: $id) { safetyLiabilities { event datasource literature
                                               effects { direction dosing } } }

# Verification (must reach 17/17)
.venv/bin/python scripts/fetch_source_metadata.py --agent red_team

# Validation and ownership
.venv/bin/python graph/validate_graph.py --strict
.venv/bin/python scripts/check_ownership.py --agent red_team --paths <files>
```

Ensembl ids come from `data/interim/gene_identifiers.jsonl`, never hand-written.
`pytest` was **not** run, per instruction; no test result is claimed anywhere in this
audit.

---

## 7. What the next red team should do first

1. **Run a registry search for the three atlases that have not had one** (§5.1). On this
   audit's hit rate it should be expected to overturn something.
2. **Query non-US registries.** The largest gap in this method (§3.1).
3. **Open the two safety curation reviews' own tables** so the six annotated targets'
   liability grades can rest on primary rows rather than on a curation summary (§3.3).
4. **Retrieve `CLM:brakes:RGS14:004`'s review's primary sources and
   `CLM:power:CKB:002`'s primary paper.** Both are named, both are unverified, and both
   are load-bearing for their targets (§3.5, §3.6).
5. **Have somebody other than the red team grade `safety_liability_burden` and
   `developmental_confound_risk`** (§4.4), starting with the two level-4 safety grades
   that fire a ranking gate.
6. **Audit this audit's 246 `flag` results.** A flag is a judgement that something is
   worth watching, not that something is wrong, and 246 of them is too many to be
   individually load-bearing. The next auditor should test whether the flag threshold was
   set low enough to be uninformative.
