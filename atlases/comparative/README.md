# Comparative Intelligence Atlas

**Owner:** `agent:comparative` · **Sprint 1** · **Branch:** `sprint-1/foundation` · written 2026-09-17

---

## 1. Scope

This atlas asks one question: **does evidence collected in a non-human animal transfer to
an adult human?** It answers it in two directions, which are the two facets this agent
owns under `docs/DATA_CONTRACT.md` §5.3:

- `cross_species_convergence` — how strong the evidence is that a mechanism recurs across
  lineages.
- `human_lineage_divergence_risk` — how strong the evidence is that human biology diverges
  enough to undermine non-human causal evidence. This feeds dimension **D6**
  (P(human translation)) **inversely**: more evidence of divergence means less confidence
  in translation.

It owns no target dossier and no other facet.

**The failure mode this atlas is built against.** The comparative-cognition literature
selects its species because they are already famous for being clever, then measures
something correlated with being large or well-studied, then describes the result in human
cognitive vocabulary. Every structural choice here is a defence against that:

- No non-human result is described in human cognitive vocabulary anywhere. `phenotype_class`
  is an `animal_*` or cellular category on every non-human claim, never a human class.
- Every claim records the **phylogenetic control actually used**, in
  `context.phylogenetic_control`, with `none` reserved for analyses established to be
  uncontrolled and `not_reported` where only an abstract was retrievable, and
  `context.phylogenetic_control_basis` saying which methods sentence was read.
- A between-species claim reporting `phylogenetic_control: none` or `not_reported` is
  **capped at level 2**, and the cap is **polarity-aware at facet level** (contract §5.4):
  it constrains `level` on a normal-polarity facet and `counter_level` on an
  inverse-polarity one, never the reverse. Every such claim
  must name an alternative explanation — shared ancestry, allometry, sampling bias,
  publication bias towards charismatic species, or measurement heterogeneity. See
  `phylogenetic_controls.md`; the cap is executable via
  `pipelines/comparative/check_phylogenetic_cap.py`.
- **Absence is recorded as evidence.** Where a cognitively impressive lineage lacks a
  proposed mechanism, that is a claim, not a gap to be skipped.
- Human-lineage specialisations are flagged as **developmental** wherever they are, because
  this project cares about adult modifiability.

---

## 2. Search method

**Discovery** was PubMed via MCP (`search_articles`, `get_article_metadata`,
`get_full_text_article`), with two PMC page fetches for methods detail. Topic areas
searched: avian and mammalian neuron counts and cellular scaling rules; elephant and
cetacean brain composition; brain-energetics constraints; human-versus-rodent cortical
pyramidal neuron physiology, h-current and dendritic integration; cephalopod RNA recoding
and genome architecture; human-specific gene duplications and human accelerated regions;
cross-species self-regulation and detour tasks; detour-task construct validity; avian
pallial circuit architecture; and target-specific sweeps for RGS14 and GABRA5.

**Verification** was `scripts/fetch_source_metadata.py --agent comparative` against PubMed
ESummary. **20 of 20 sources verified, title similarity 1.0 on every one, no retractions.**
No identifier in this atlas was written from memory. Two sources
(`SRC:PMID:30340039`, `SRC:PMID:20837545`) are registered **both here and by
`agent:brakes`**, which contract §1.3 allows and prefers: every agent's claims stay
self-contained and no agent depends on a file it cannot edit. Deduplication happens
downstream (the store, the graph compiler and `independent_source_count` all dedupe by
`source_id`), so duplication cannot inflate an evidence count. The hard error is
*divergence*, and both registrations were checked field-by-field against
`evidence/sources/brakes.yaml`: identical on title, year, first author, container and DOI.

**Taxids** were resolved by `pipelines/comparative/fetch_taxonomy.py` against the NCBI
taxonomy API, snapshotted to `data/raw/ncbi_taxonomy/2026-09-17/`, indexed to
`data/interim/comparative_species_taxonomy.jsonl`: **26 of 26 species resolved**, and the
resolver reproduces all 26 offline from snapshots. The strict matcher refused a synonym
hit for the Eurasian jackdaw (*Corvus monedula* in every source, *Coloeus monedula* in
NCBI), which was corrected only after a separate lookup confirmed taxid 30423.

**Measured versus unmeasured (rule V16c).** All 25 evidence items carry
`endpoint_measured`. Twenty-four are `measured`; the single exception is
`CLM:comparative:NEURON_SCALING:006`, a biophysical model whose endpoint is a computed
quantity rather than a measurement, recorded as `not_measured_in_protocol`. The
distinction matters because a measured absence is evidence and an absence of measurement
is a gap, and this atlas trades heavily in the former.

**What this means for reliability.** 16 of 25 evidence items were extracted from abstracts
and 9 from full text; `extraction.basis` says which on every item. One full text could not
be retrieved because the PMC page returned a CAPTCHA, which this agent did not attempt to
bypass — the affected claim (`CLM:comparative:CEPHALOPOD_RNA_EDITING:001`) carries an empty
species list and says why.

---

## 3. Coverage: species × evidence type

Counts are of curated claims in `evidence/claims/comparative/`, not of the literature.

| Species | taxid | Clade | Cognitive | Neuroanatomical | Molecular | Role |
|---|---|---|---|---|---|---|
| *Homo sapiens* | 9606 | hominid | 0 | 6 | 3 | reference target |
| *Pan troglodytes* | 9598 | hominid | 1 | 0 | 2 | closest outgroup |
| *Macaca mulatta* | 9544 | cercopithecid | 1 | 1 | 0 | translational model |
| *Mus musculus* | 10090 | murid | 0 | 5 | 2 | primary causal model |
| *Rattus norvegicus* | 10116 | murid | 0 | 3 | 0 | primary causal model |
| *Tursiops truncatus* | 9739 | odontocete | **0** | **0** | **0** | **no evidence curated** |
| *Loxodonta africana* | 9785 | proboscidean | 0 | 1 | 0 | negative control |
| *Corvus moneduloides* | 1196302 | corvid | 2 | 0 | 0 | convergence test |
| *Corvus corax* | 56781 | corvid | 2 | 0 | 0 | convergence test |
| *Psittacus erithacus* | 57247 | psittacid | 0 | 1 | 0 | convergence test |
| *Nestor notabilis* | 176057 | psittacid | 0 | 1 | 0 | convergence test |
| *Octopus vulgaris* | 6645 | octopod | **0** | **0** | **0** | **no evidence curated** |
| *Octopus bimaculoides* | 37653 | octopod | 0 | 0 | 2 | molecular reference |

13 panel species; 11 carry at least one claim. The two that carry none — the bottlenose
dolphin and the common octopus — are the two with the strongest popular cognitive
narratives. That asymmetry is the most important thing this table records. Thirteen
further `cited_only` species appear in claim contexts and are listed in
`species_panel.yaml`.

## 4. Coverage: target × facets

| Target | Lead atlas | `cross_species_convergence` | `human_lineage_divergence_risk` |
|---|---|---|---|
| **HCN1** | brakes | **2** (counter 3) | **3** (counter 1) |
| **RGS14** | brakes | **2** (counter 0) | **1** (counter 2) |
| **KCNQ2** | brakes | `not_assessed` | **1** (counter 0) |
| **KCNQ3** | brakes | `not_assessed` | **1** (counter 0) |
| 23 others | various | `not_assessed` | `not_assessed` |

**4 of 27 seed targets assessed on at least one facet; 6 of 54 facets graded.** Every
ungraded facet is `assessment_status: not_assessed` with `level: null` and a
target-specific reason. **None is 0.** Contract §5.2 makes writing 0 for unexamined
evidence a violation, because level 0 means "searched, nothing found" — a positive finding
about the literature. Per contract P8, `agent:integration` must treat these as wide and
uninformative, never as zero.

Sparse coverage is the honest result of one sprint that prioritised depth on the one
target with real human-versus-rodent data (HCN1) over a thin sweep of all 27. The targets
most worth doing next, because comparative evidence demonstrably exists for them, are
**GRIN2B** (rodent-versus-primate NMDA subunit switch), **DRD1** (cortical dopamine
innervation differs markedly between rodents and primates, bearing directly on the
inverted-U the seed registry flags), **KL** (the seed registry itself records non-human
primate administration studies) and **ADORA1** (a caffeine literature spanning many
species).

## 5. Claim inventory

**21 claims, 25 evidence items, 20 verified sources** (two of them also registered by `agent:brakes`, per contract §1.3). Evidence levels: ten at 1, ten at
2, one at 3.

| File | Claims | Content |
|---|---|---|
| `NEURON_SCALING.yaml` | 6 | avian and mammalian neuron counts, cellular scaling, metabolic constraint |
| `HCN1.yaml` | 4 | human-versus-rodent h-current, both directions, plus the derived tension claim |
| `SELF_REGULATION.yaml` | 3 | cross-clade detour-task performance and its construct validity |
| `HUMAN_LINEAGE.yaml` | 3 | SRGAP2C, CTNND2, human accelerated regions — all developmental |
| `CEPHALOPOD.yaml` | 2 | RNA recoding, genome architecture |
| `CORTICAL_NEURON_PHYSIOLOGY.yaml` | 1 | human-versus-rat dendritic compartmentalisation |
| `RGS14.yaml` | 1 | conserved CA2 localisation, mouse and adult human |
| `AVIAN_CIRCUIT.yaml` | 1 | repeated column-like circuit in pigeon and barn owl pallium |

**Phylogenetic control: 3 of 21 claims report any** — two `other` (a phylogenetic
analysis whose estimator was not extractable, and a phylogenetic regression used only for
body-mass residuals) and one `outgroup_comparison`. The remaining 18 are `none` (14) or
`not_reported` (4). **Not one claim in this atlas uses PGLS, a phylogenetic mixed model,
sister-taxon contrasts or ancestral state reconstruction.** Fifteen are between-species
and uncontrolled, and are capped at level 2.

**Ten of 21 claims are deflationary or negative** — they carry at least one evidence item
whose `evidence_role` is `contradicts`, `qualifies` or `null_result`:

| Claim | What it deflates |
|---|---|
| `NEURON_SCALING:002` | "bird brains are densely packed" — galliforms have ~half the neurons of parrots and songbirds at equal brain mass |
| `NEURON_SCALING:003` | total-neuron-count accounts of cognition — the elephant cortex holds ~a third of the human cortical count while its brain holds three times the total |
| `NEURON_SCALING:004` | human cellular exceptionalism — the human brain has the cells expected of a primate brain of its size |
| `NEURON_SCALING:005` | published cetacean neuron counts — ~fourfold disagreement between stereology and the isotropic fractionator in the same species |
| `NEURON_SCALING:006` | free-lunch readings of neuron number — it is metabolically priced |
| `SELF_REGULATION:002` | absolute brain volume as a cross-clade predictor — corvids match great apes with brains 26–94× smaller |
| `SELF_REGULATION:003` | the instrument behind both flagship results — detour scores index motor response learning too |
| `HCN1:004` | any single-direction summary of human-versus-rodent h-current |
| `HAR:001` | enhancer hijacking — human-specific HAR targets converged on no function |
| `CEPHALOPOD_GENOME:001` | whole-genome duplication and a novel neural toolkit in octopus — neither found |

---

## 6. What this atlas cannot support

Read this section before citing anything above.

1. **It cannot distinguish convergence from shared inheritance — for any mechanism.**
   Doing so requires ancestral state reconstruction and no source curated here performed
   one. Wherever this atlas says "convergent", read **"present in more than one lineage,
   by an unknown evolutionary route"**. `AVIAN_CIRCUIT:001` is the worked example: a
   repeated pallial circuit motif in two birds is either an independent solution or a
   conserved amniote plan, and two species with no reconstruction cannot tell them apart.

2. **It cannot support any statement that a non-human species is more or less
   intelligent than another.** No claim here measures general cognitive ability in any
   species, including humans. The only behavioural claims concern one detour task, and
   `SELF_REGULATION:003` shows that task is contaminated by motor response learning.

3. **It cannot support quantitative cross-clade neuron counts.** `NEURON_SCALING:005`
   records a roughly fourfold method disagreement on one species. Any downstream ranking
   of species by neuron count is unsupported by this repository, and any statement about
   **dolphin** neuron numbers is doubly unsupported: the only cetacean claim is a
   mysticete (northern minke whale), and *Tursiops truncatus* has zero curated claims.

4. **It cannot support an adult intervention hypothesis from any human-lineage
   specialisation.** SRGAP2C, CTNND2 and the HAR interactome act during prenatal or
   postnatal development, mostly by slowing it. `translation.adult_relevance` is
   `developmental_only` on two of the three. These claims raise divergence risk; they are
   not target proposals, and none of the three genes is in `targets/seed_registry.yaml`.

5. **It cannot support "human neurons are like this".** Every human electrophysiology
   measurement here comes from epilepsy or tumour neurosurgical tissue.
   `baseline_context` is `disease_population` on all of them. In `HCN1:003` the confound is
   structural: only the human arm was diseased, and no analysis in the source removes it.

6. **It cannot support a single-direction claim about human versus rodent HCN1.** The two
   direct comparisons disagree in sign by cortical layer. `HCN1:004` exists to block that
   summary.

7. **The graph-edge conventions here are weaker than they look.** `ontology/edges.yaml`
   has no relation meaning "this property differs between species", so anatomical and
   behavioural claims borrow `CONSTRAINS`, `MODULATES`, `IMPLEMENTS` or `PREDICTS` with
   `direction: unclear` and the real content in `statement` and `risks`. The compiled
   graph will therefore carry capacity and modulation edges whose claims are purely
   descriptive. One instance of this overreach was caught mechanically:
   `CLM:comparative:DENDRITE:001` originally asserted
   `CELL:layer5_pyramidal_neuron MODULATES PRIM:composition`, which
   `graph/validate_graph.py --strict` correctly flagged under V16 as an efficacy-grade
   assertion that `theoretical_construct` cannot license. It now points at
   `SV:workspace.dendritic_integration_gain`, which the source measured directly. The one
   remaining edge into a computational primitive is
   `CLM:comparative:AVIAN_CIRCUIT:001` via `IMPLEMENTS`, the relation designed for it.

   **(Resolved for the null case.)** `CLM:comparative:SELF_REGULATION:002` is the one
   genuine null in this atlas — a performed cross-clade comparison in which absolute brain
   volume predicted nothing. It originally compiled as a `CONSTRAINS` edge with
   `direction: unclear`, so a traversal ignoring `direction` could read a deflationary
   result as *support* for brain size → inhibition. That was filed as
   `comparative-002.yaml`, **approved and generalised as V16b-sym**
   (`docs/blackboard/RESOLUTIONS.md` R9): the null relation's domain and range must be at
   least the union of those of every relation it can negate, so a null is expressible
   wherever the positive is. It is now
   `REGION:brain -NO_DETECTED_EFFECT_ON-> PRIM:distractor_suppression` with
   `negated_relation: CONSTRAINS` and `direction: no_change`, and no traversal may count
   it as support. The remaining descriptive-edge overreach in §6.7's first paragraph is
   unaffected and still stands. Requested properly in
   `docs/blackboard/schema_change_requests/comparative-001.yaml`; until then, treat every
   comparative edge as suspect by construction. Two `causal_attribution.basis` values and
   one `evidence.design` value are also enum approximations, flagged in the affected
   claims' `risks`.

8. **(Resolved 2026-09-17.)** This section previously recorded that the cap suppressed
   `HCN1`'s `human_lineage_divergence_risk` to 2 where the evidence read as 3, making the
   target look *more* translatable than warranted. That defect was escalated rather than
   worked around, and **contract §5.4 now makes methodological caps polarity-aware**: on
   an inverse-polarity facet the cap constrains `counter_level`, never `level`. `HCN1`'s
   divergence risk is restored to **3**, and its `cross_species_convergence`
   `counter_level` raised to **3** for the same reason (the cap does not bind
   `counter_level` on a normal-polarity facet). `KCNQ2`, `KCNQ3` and `RGS14` levels were
   set by evidentiary distance rather than the cap and are unchanged. The regression is
   guarded mechanically: `check_phylogenetic_cap.py --legacy-rule` reinstates the old
   behaviour and now exits 1. **What remains outstanding** is that
   `models/ranking/facet_rubric_v0_1.yaml` must implement caps through a polarity-aware
   helper, per §5.4; until it does, the polarity table lives in this atlas's checker.

9. **Orthology reference data is absent.** Cross-species orthology was checked
   interactively via Open Targets during curation, but its snapshot path
   (`data/raw/opentargets/**`) belongs to `agent:integration`, so no orthology numbers
   entered curated records — an un-snapshotted number would be unreproducible. Note
   separately that Open Targets homologues cover only standard model species: no birds,
   no cephalopods, no cetaceans, no elephant. Orthology would add little to this panel
   even if ingested.

10. **Genome assemblies are unverified.** `genome_assembly` is
    `not_verified_this_session` on all 13 panel species. Accessions are identifiers and
    this agent will not write one it has not seen in a tool response; the NCBI assembly
    endpoint was not queried because its snapshot path is outside this agent's lane.

---

## 7. Files

| Path | What it is |
|---|---|
| `species_panel.yaml` | the panel, with taxid provenance and a narrative-risk note per species |
| `phylogenetic_controls.md` | the method: what controls exist, what none fix, and the cap rule |
| `assessments/{SYMBOL}.yaml` | 27 files, one per seed target, two facets each |
| `state_variable_annotations.yaml` | 2 coupling annotations; no response-shape or safety-coupling change requested |
| `../../evidence/sources/comparative.yaml` | 20 sources, all verified (2 dual-registered with `agent:brakes`) |
| `../../evidence/claims/comparative/*.yaml` | 21 claims in 8 files |
| `../../pipelines/comparative/fetch_taxonomy.py` | taxid resolver, `--offline` capable |
| `../../pipelines/comparative/check_phylogenetic_cap.py` | makes the cap rule executable |
| `../../pipelines/comparative/migrate_null_and_direction.py` | applied the R9/R10 migrations; idempotent, and refuses to run until the ontology support exists |

## 8. Reproduce the checks

```bash
.venv/bin/python pipelines/comparative/fetch_taxonomy.py --offline      # 26/26 from snapshots
.venv/bin/python scripts/fetch_source_metadata.py --agent comparative   # 20/20 verified
.venv/bin/python pipelines/comparative/check_phylogenetic_cap.py        # exit 0
.venv/bin/python pipelines/comparative/check_phylogenetic_cap.py --legacy-rule  # exit 1, by design
.venv/bin/python pipelines/comparative/migrate_null_and_direction.py    # exit 0, already applied
.venv/bin/python graph/validate_graph.py --strict                       # 0 violations in this atlas
.venv/bin/python scripts/check_ownership.py --agent comparative --paths <own paths>
```

All 70 records (21 claims, 20 sources, 27 assessments, 2 annotations) validate against
`schemas/*.json` as produced by `agent:ontology`, with zero errors.

`graph/validate_graph.py --strict` landed late in the run and **was** executed. It found
5 violations in this atlas's files, all fixed: one V16 (a `MODULATES` edge into a
`ComputationalPrimitive`, retargeted to the state variable the source actually measured),
two V4 duplicate source registrations, and two V9 warnings about a `sample_size.value`
with no verbatim wording. The two V4s were then **un-fixed on instruction**, because
contract §1.3 changed to prefer duplicate registration, and the validator was updated to
match — repo-wide duplicate-source-id violations are now zero. **Current count: 0
violations in `agent:comparative` files.** Repo-wide violations from other agents'
records are not this atlas's to fix.

**`NO_DETECTED_EFFECT_ON` (V16b) was evaluated against all five claims here that carry
null or contradicting evidence, and exactly one migrated:** `SELF_REGULATION:002`, a
measured cross-clade absence, now carries the null relation with
`negated_relation: CONSTRAINS`. The other four should not, and re-checking them after the domain widened
does not change that, because V16b requires a **measured absence** and these report
measured presences: `NEURON_SCALING:003` is a difference detected (elephant cortex about
a third of the human cortical count), `NEURON_SCALING:005` is a fourfold measurement
conflict, `SELF_REGULATION:003` found a positive effect of response learning, and
`CEPHALOPOD_GENOME:001` — eligible today — was **refused on honesty grounds** because
nobody tested whether protocadherin expansion affects structural plasticity, so a null
edge there would manufacture a finding out of a gap. `RESOLUTIONS.md` R9 upholds that
refusal explicitly so a later agent does not "fix" it.
