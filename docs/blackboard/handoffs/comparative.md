# Handoff — `agent:comparative` (Comparative Intelligence Atlas)

**Sprint 1** · branch `sprint-1/foundation` · run_id `sprint1-comparative-01` · 2026-09-17

---

## 1. Species panel — taxids and how each was resolved

**26 of 26 species resolved, exit 0.** Every taxid came from the NCBI taxonomy API via
`pipelines/comparative/fetch_taxonomy.py`, which accepts a candidate only when the
registry's own `scientificname` matches the queried name exactly **and** the rank is
`species`. Responses are snapshotted immutably under
`data/raw/ncbi_taxonomy/2026-09-17/` (31 files, each with a `data/raw/MANIFEST.jsonl`
line); the derived index is `data/interim/comparative_species_taxonomy.jsonl`. Nothing
was typed from memory. `--offline` reproduced all 26 from snapshots with no network.

**13 panel members:** *Homo sapiens* 9606 · *Pan troglodytes* 9598 · *Macaca mulatta*
9544 · *Mus musculus* 10090 · *Rattus norvegicus* 10116 · *Tursiops truncatus* 9739 ·
*Loxodonta africana* 9785 · *Corvus moneduloides* 1196302 · *Corvus corax* 56781 ·
*Psittacus erithacus* 57247 · *Nestor notabilis* 176057 · *Octopus vulgaris* 6645 ·
*Octopus bimaculoides* 37653.

**13 `cited_only` species** (named in claim contexts, not panel members):
*Balaenoptera acutorostrata* 9767 · *Coloeus monedula* 30423 · *Phasianus colchicus*
9054 · *Columba livia* 8932 · *Tyto alba* 56313 · *Pan paniscus* 9597 ·
*Gorilla gorilla* 9593 · *Callithrix jacchus* 9483 · *Suncus etruscus* 109475 ·
*Meriones unguiculatus* 10047 · *Cavia porcellus* 10141 · *Oryctolagus cuniculus* 9986 ·
*Mustela putorius* 9668.

Three resolution decisions worth knowing:

- **The guard caught a real error.** Every source calls the Eurasian jackdaw
  *Corvus monedula*; NCBI's accepted name is *Coloeus monedula*. The strict matcher
  **refused** the synonym hit and exited non-zero rather than accept it. Taxid 30423 was
  written only after a separate lookup confirmed the accepted name. A resolver taking the
  first hit would have recorded a taxid under a name NCBI does not accept.
- ***Octopus bimaculoides* was added beyond the required panel**, because the cephalopod
  reference genome and the RNA-recoding work are in that species, not in the panel's
  *O. vulgaris*. Keeping both prevents silently attributing a molecular finding to the
  species the behavioural literature is built on.
- **No orangutan taxid was written.** `SRC:PMID:27152224` reports an orangutan
  cylinder-task score but the retrieved text gives only the common name, and *Pongo*
  contains more than one species. Guessing would have been a fabricated identifier.

`genome_assembly` is `not_verified_this_session` on all 13 panel species. Accessions are
identifiers, and the NCBI assembly endpoint was not queried because its snapshot path
(`data/raw/ncbi_assembly/**`) is not owned by this agent. **Requested as a follow-up.**

## 2. Claims created

**21 claims, 25 evidence items, 20 sources — all 20 verified, title similarity 1.0, no
retractions.** Two (`SRC:PMID:30340039`, `SRC:PMID:20837545`) are dual-registered with
`agent:brakes` under contract §1.3 — see §11.

| Phylogenetic control | Claims |
|---|---|
| `other` (real control, estimator not extractable) | 2 |
| `outgroup_comparison` | 1 |
| `none` (established uncontrolled, or n ≤ 2 making it impossible) | 14 |
| `not_reported` (only an abstract retrievable) | 4 |

**Only 3 of 21 claims carry a real phylogenetic control, and none uses PGLS, a
phylogenetic mixed model, sister-taxon contrasts or ancestral state reconstruction.**
Two are `other`: `SELF_REGULATION:001` (abstract states phylogenetic analysis was used,
estimator not extractable) and `SELF_REGULATION:002` (phylogenetic regression supplies
body-mass residuals only; the AIC-favoured model has no phylogenetic term). One is
`outgroup_comparison`: `HAR:001`, a designed human-versus-chimpanzee comparison over a
region set defined by a multi-species substitution test.

Two `none` values were **established from methods text**, not assumed:
`NEURON_SCALING:001` (reduced major axis regression to power functions) and `HCN1:003`
(Pearson/Spearman correlation, ANCOVA, ordinary log-log linear regression). Both
statements came from retrieving the papers' methods, not from inference.

**10 of 21 claims are deflationary or negative:** `NEURON_SCALING:002` (galliforms have
~half the neurons of parrots/songbirds at equal brain mass — "bird brain" is not a unit) ·
`:003` (elephant cortex ~⅓ the human cortical count while its brain holds 3× the total —
absence of the mechanism in a cognitively impressive lineage) · `:004` (the human brain is
cellularly unexceptional for a primate of its size) · `:005` (~fourfold
stereology-versus-fractionator disagreement on the same cetacean species) · `:006`
(neuron number is metabolically priced) · `SELF_REGULATION:002` (corvids match great apes
with brains 26–94× smaller) · `:003` (the detour task indexes motor response learning) ·
`HCN1:004` (the two human-versus-rodent h-current results disagree in sign by layer) ·
`HAR:001` (enhancer hijacking tested and not supported) · `CEPHALOPOD_GENOME:001` (no
whole-genome duplication; core neuronal gene repertoire broadly similar to other
invertebrate bilaterians).

Evidence levels: ten at 1, ten at 2, one at 3 (`SELF_REGULATION:003`, exempt from the cap
because it is a single-species claim about a measurement instrument).

## 3. Targets assessed and not assessed

**4 of 27 seed targets; 6 of 54 facets graded.**

| Target | `cross_species_convergence` | `human_lineage_divergence_risk` | Why assessable |
|---|---|---|---|
| **HCN1** | 2 (counter 3) | **3** (counter 1) | the only target with direct quantitative adult-human-versus-rodent measurements of its own biophysics |
| **RGS14** | 2 (counter 0) | 1 (counter 2) | RGS-14 is a CA2-specific marker in adult human hippocampus as in mouse |
| **KCNQ2** | `not_assessed` | 1 (counter 0) | aggregate Kv conductance only, not subunit-resolved |
| **KCNQ3** | `not_assessed` | 1 (counter 0) | as KCNQ2 |

**23 targets are `not_assessed` on both facets, with `level: null` and a target-specific
reason. None is 0.** Level 0 means "searched, nothing found", which is a positive finding
about the literature; that is not what happened for those 23, and writing 0 would be a
contract §5.2 violation. **`agent:integration` must treat these as wide and
uninformative, never as zero (contract P8).**

Sparse coverage is the deliberate result of preferring depth on the one target with real
human-versus-rodent data over a thin sweep of all 27. **Highest-value next targets**,
because comparative evidence demonstrably exists: **GRIN2B** (rodent-versus-primate NMDA
subunit switch), **DRD1** (cortical dopamine innervation differs markedly between rodents
and primates — directly relevant to the inverted-U the seed registry flags), **KL** (the
seed registry itself records non-human-primate administration studies), **ADORA1** (a
caffeine literature spanning many species).

## 4. Exact commands run, with real results

| Command | Result |
|---|---|
| `.venv/bin/python pipelines/comparative/fetch_taxonomy.py` | `resolved 26/26 species`, exit 0 |
| `.venv/bin/python pipelines/comparative/fetch_taxonomy.py --offline` | `resolved 26/26 species`, exit 0 — offline rebuild verified |
| `.venv/bin/python scripts/fetch_source_metadata.py --agent comparative` | `20/20 sources verified`, exit 0; similarity 1.0 on all, `retraction_flag: false` on all |
| `.venv/bin/python pipelines/comparative/check_phylogenetic_cap.py --verbose` | `cap respected by every claim and facet`, exit 0 |
| `.venv/bin/python scripts/check_ownership.py --agent comparative --paths <75 own paths>` | `all 75 path(s) owned as expected`, exit 0 |
| `jsonschema` validation against `schemas/*.json` | 21 claims + 20 sources + 27 assessments + 2 annotations = **70 records, 0 errors** |
| `data/raw/MANIFEST.jsonl` checksum re-verification | **31 of 31** `ncbi_taxonomy` snapshots match their recorded sha256 |
| anti-fabrication sweep (own script, ad hoc) | 0 cited sources unverified · 0 registered-but-uncited · 0 stray PMIDs · 0 unresolved taxids · 0 hand-written floats in (0,1) · 0 human `phenotype_class` values on a non-human claim · 0 claims with an incomplete `translation` block |

**Not run, and why:**

- **`graph/validate_graph.py --strict`** — **was run**; it landed late in the session. See
  §10. Zero violations remain in `agent:comparative` files.
- **`pytest`** — not run; `tests/**` is owned by another agent.
- **Nothing installed**; `.venv/bin/python` only; no git commands.

## 5. What failed, what is uncertain, what I could not do

- **One full text was unobtainable.** The PMC page for `SRC:PMID:28388405` (cephalopod
  RNA recoding) returned a **CAPTCHA**, which I did not attempt to bypass. That claim
  therefore has `extraction.basis: abstract`, an **empty `context.species`** because the
  coleoid species could not be enumerated, and `phylogenetic_control: not_reported`.
- **Two PMC methods sections were read through an automated page fetch** rather than
  transcribed by me (`SRC:PMID:27298365` species list and regression method). Flagged in
  that claim's `risks`.
- **Enum gaps forced three understatements.** `causal_attribution.basis` has no
  `animal_observational_association` or `animal_randomised_intervention`, and
  `evidence.design` has no `animal_behavioural_experiment`. Using the `human_*` values on
  animal studies would have been species laundering, so
  `SELF_REGULATION:001/:002/:003` carry `theoretical_argument`, which understates all
  three designs — one of them a genuine randomised manipulation. Flagged in each claim's
  `risks` and in the change request.
- **No orthology reference data was ingested.** Open Targets homologues were queried
  interactively (HCN1: 1:1 orthologues in chimpanzee, macaque, mouse, rat at ~95–99.5%
  identity, data version 26.06) but **no numbers entered curated records**, because
  `data/raw/opentargets/**` belongs to `agent:integration` and an un-snapshotted number
  would be unreproducible. Note for whoever picks this up: Open Targets homologues cover
  only standard model species — **no birds, no cephalopods, no cetaceans, no elephant** —
  so it would add little to this panel.
- **Two panel species have zero claims**, and they are the two with the strongest popular
  cognitive narratives: *Tursiops truncatus* and *Octopus vulgaris*.
- **`graph/validate_graph.py` never appeared**, so `--strict` was never run.

## 6. Schema change request

`docs/blackboard/schema_change_requests/comparative-001.yaml`, non-blocking,
**`status: partially_satisfied`**.

`agent:ontology` independently added `context.phylogenetic_control`,
`context.phylogenetic_control_basis` and `context.species_count` to
`schemas/claim.schema.json` during the same sprint, with a **better enum** than the one
requested — it includes `not_reported`, which fixes a real defect in my proposal (the
proposed enum forced "reported as uncontrolled" and "not stated in retrieved text" to
share the value `none`). This atlas conformed to the schema's vocabulary, not its own
proposal. Still outstanding: the `DIFFERS_BETWEEN_SPECIES` relation, the animal
`causal_attribution.basis` and `evidence.design` values, and the facet-rubric encoding of
the cap.

## 7. What the red team should attack first

In priority order. The first three are where I think I am most likely to be wrong.

1. **`CLM:comparative:DENDRITE:001`'s edge into `PRIM:composition`, and
   `CLM:comparative:AVIAN_CIRCUIT:001`'s into `PRIM:composition`.** Both map a measured
   anatomical or biophysical finding onto a computational primitive by **my** argument,
   not the source's. Neither source measured a computation. These are the two weakest
   records in the atlas and I have said so in their `risks`. Test whether they should
   exist as graph edges at all.
2. **Every `CONSTRAINS` and `MODULATES` edge from a purely descriptive claim.**
   `ontology/edges.yaml` has no between-species relation, so six neuron-count claims
   assert `REGION:x CONSTRAINS SV:efficiency.information_throughput_per_unit_energy` when
   all they measured was a cell count. `direction: unclear` and
   `claim_type: theoretical_construct` are doing the load-bearing work. If the compiled
   graph reads these as capacity assertions, that is a defect this atlas created.
3. **`CLM:comparative:HCN1:003`'s structural confound.** Human outlier status is
   inseparable from the fact that only the human arm used diseased (epilepsy/tumour)
   tissue. No analysis in the source removes it, and I could not either. If that confound
   explains the result, the HCN1 divergence-risk assessment should fall.
4. **(Resolved — but check the correction, not the original.)** I originally recorded
   HCN1's `human_lineage_divergence_risk` at **2** where the evidence read as **3**,
   because my cap applied uniformly to `level`. That facet feeds **D6 inversely**, so the
   cap made HCN1 look *more* translatable than its evidence supports. The coordinator
   amended the contract (**§5.4**, polarity-aware caps) and the records are corrected —
   see §9 below. What the red team should now attack is **the correction**: specifically
   whether raising `cross_species_convergence`'s `counter_level` from 2 to 3 was justified
   (I did that on my own judgement, beyond the literal instruction — see §9) and whether
   level 3 rather than 4 is right for the divergence risk given that the two supporting
   results disagree in sign by layer.
5. **Duplicated-evidence inflation.** `NEURON_SCALING:001`, `:002`, `:003` and `:004`
   share the isotropic-fractionator method and largely one research programme
   (Herculano-Houzel is senior author on three). `HCN1:001` and `:002` are the same
   experiment on the same cells. `SRGAP2:001` and `CTNND2:001` share a senior author group
   and the SRGAP2C reagent. `dependencies` and `risks` say so on each, but the
   `duplicated_evidence` check should confirm the ranking does not treat them as
   independent.
6. **`CEPHALOPOD_GENOME:001`'s subject.** `COMPLEX:protocadherin_cluster
   ASSOCIATED_WITH SV:plasticity.structural_plasticity_rate` rests on gene-family size,
   not on any plasticity measurement. `locus_to_gene_resolved: "no"` is flagged, but the
   claim may not deserve to exist.
7. **The `not_assessed` handling.** Check that 46 `not_assessed` facets with `level: null`
   are not coerced to 0 anywhere downstream. That would silently downgrade 23 targets on
   two facets each.

## 8. The single claim most likely to be over-read

**`CLM:comparative:NEURON_SCALING:001`** — Olkowicz et al., *"Birds have primate-like
numbers of neurons in the forebrain"* (`SRC:PMID:27298365`).

It is the most quotable finding in this atlas and it is a **cell count**. No bird in that
study performed a cognitive task. The paper's own framing — higher "cognitive power" per
unit mass — is an inference from behavioural work on other individuals and often other
species, and "primate-like" refers to the *number*, not to any shared cognitive construct.
The analysis used reduced major axis regression with **no phylogenetic correction**, and 24
of its 28 species are parrots or songbirds — two sister clades — so the n of 28 may carry
as few as 2 independent evolutionary contrasts. The atlas grades it **level 1**.

Three things in this same atlas cut against the reading it invites:
`NEURON_SCALING:002` (galliforms have ~half the neurons at equal brain mass, so there is
no single "avian solution"), `NEURON_SCALING:004` (the human brain is cellularly
unexceptional for its clade and size, so the whole neuron-count-equals-capability frame is
weaker than it looks), and `NEURON_SCALING:005` (two accepted counting methods disagree
~fourfold on one species, so the numbers themselves are not a reliable cross-clade
variable).

Runner-up: **`CLM:comparative:HCN1:001`/`:002`**, which a reader wanting a single number
for human-versus-rodent h-current will collapse into "human HCN1 is stronger". It is
stronger in supragranular layers and weaker than allometrically predicted in layer 5.
`CLM:comparative:HCN1:004` exists solely to block that summary; if anything downstream
states a single direction, it has ignored a claim written to prevent exactly that.

---

## 9. Contract §5.4 applied — polarity-aware caps (added 2026-09-17)

The coordinator accepted the escalation in §7.4 and amended the contract. **§5.4**: a cap
imposed because the evidence is methodologically weak applies only in the direction that
favours the target — `level` on a normal-polarity facet, `counter_level` on an
inverse-polarity one (`human_lineage_divergence_risk`, `safety_liability_burden`,
`developmental_confound_risk`), **never** `level` on an inverse facet. Weak method cannot
establish the *absence* of a risk.

**Records changed. No evidence changed; only the rule did, and every change is recorded
in-place rather than overwritten.**

| File | Facet | Field | Was | Now | Why |
|---|---|---|---|---|---|
| `HCN1.yaml` | `human_lineage_divergence_risk` | `level` | 2 | **3** | restored; the cap should never have touched an inverse facet's `level` |
| `HCN1.yaml` | `cross_species_convergence` | `counter_level` | 2 | **3** | §5.4 leaves `counter_level` uncapped on a *normal*-polarity facet; it rests on the same evidence body as the restored divergence-risk level |
| `KCNQ2.yaml`, `KCNQ3.yaml` | `human_lineage_divergence_risk` | — | 1 / counter 0 | unchanged | level 1 was set by evidentiary distance (aggregate Kv, not subunit-resolved), never by the cap |
| `RGS14.yaml` | `human_lineage_divergence_risk` | — | 1 / counter 2 | unchanged | `counter_level` 2 now sits exactly AT the cap and cannot rise; `level` 1 was never cap-derived |
| `HCN1.yaml`, `RGS14.yaml` | `cross_species_convergence` | `level` | 2 | unchanged | normal-polarity; the cap on `level` was correct and stays |

**Two of my own errors corrected while doing this.** `KCNQ2.yaml` and `KCNQ3.yaml` each
contained a `limiting_factor` sentence claiming the level was "capped at 1 regardless by
the no-phylogenetic-control rule". That was simply wrong — the cap was at 2 and never set
those levels. Corrected, and the correction noted in each file's header rather than
silently patched.

**One judgement beyond the literal instruction, flagged for review.** Raising
`HCN1`'s `cross_species_convergence` `counter_level` from 2 to 3 was not requested. I made
it because §5.4's principle is symmetric: if the cap applies only in the direction that
favours the target, then on a normal-polarity facet it constrains `level` and leaves
`counter_level` free, and the counter-evidence to HCN1 convergence is substantially the
same multi-design body now grading divergence risk at 3. Leaving it at 2 would have
understated evidence *against* the target, which is the error §5.4 exists to prevent. If
`agent:integration` or `agent:red_team` judges that caps should bind `counter_level` on
normal-polarity facets too, it returns to 2 and nothing else moves; the rationale in the
file says so explicitly.

**Checker updated and the regression guarded mechanically.**
`pipelines/comparative/check_phylogenetic_cap.py` now:

- carries a **`FACET_POLARITY` table for all 15 facets**, not a hard-coded facet name, and
  **reads `models/ranking/facet_rubric_v0_1.yaml` in preference to its own table** as soon
  as `agent:integration` publishes it, with the source printed under `--verbose`;
- applies the cap to `level` or `counter_level` according to polarity, and checks the
  matching `claim_refs` / `counter_claim_refs` list;
- flags any owned facet whose polarity is unknown, rather than guessing;
- provides **`--legacy-rule`**, which reinstates the pre-§5.4 uniform behaviour. It
  **exits 1** against the corrected records, naming HCN1's restored level 3. That is the
  regression guard: the old behaviour is now mechanically a violation, not merely
  discouraged.

```
$ check_phylogenetic_cap.py                exit 0   cap respected by every claim and facet
$ check_phylogenetic_cap.py --legacy-rule  exit 1   HCN1 human_lineage_divergence_risk: level 3 exceeds the cap of 2
```

**Still outstanding for `agent:integration`:** §5.4 requires `models/ranking/` to
implement caps through a **polarity-aware helper rather than ad hoc clipping**. Until
that lands, the polarity table lives in this atlas's checker, which is the wrong place for
it. Also note that no claim-level grade changed: claims have no polarity, so the
claim-level cap is untouched by §5.4.

---

## 10. `graph/validate_graph.py --strict` — run, and what it caught (2026-09-17)

The validator did not exist when §4 was written; it landed later in the session and was
run as my remit required. It reported **5 violations in `agent:comparative` files**, all
now fixed. **Current count: 0.** Repo-wide totals include other agents' records, which are
not mine to touch.

| Rule | What it caught | Fix |
|---|---|---|
| **V16** | `CLM:comparative:DENDRITE:001` asserted `CELL:layer5_pyramidal_neuron MODULATES PRIM:composition`. A `MODULATES` edge into a `ComputationalPrimitive` is an efficacy-grade assertion, which `claim_type: theoretical_construct` cannot license. | **Retargeted to `SV:workspace.dendritic_integration_gain`**, which the source measured directly, with `claim_type: mechanistic`. I removed the overreach rather than upgrading the claim_type to match it — upgrading would have asserted a perturbation nobody performed. |
| **V4** ×2 | `SRC:PMID:30340039` and `SRC:PMID:20837545` were registered by both `agent:brakes` and me. | Removed at the time, then **restored on instruction** — contract §1.3 changed to allow and prefer duplicate registration, and the validator was updated to match. See §11. |
| **V9** ×2 (warning) | `sample_size.value` set with no verbatim `reported_as`, so the number could not be audited against the source. | `AVIAN_CIRCUIT:001`: **value set to `null`** — the abstract gives no species count I could quote, and the count lives in `context.species_count` as my own derivation. `SELF_REGULATION:003` evidence 2: **`reported_as` set to the verbatim "Only seven were birds."** from the retrieved full text. |

**The V16 catch is worth dwelling on.** That edge was the one I had already named as the
weakest record in the atlas and put first on the red team's list (§7.1). The validator
found it independently and mechanically. It is a good sign for the architecture that the
contract's own rules located the overreach I had only flagged in prose — and it means
§7.1's remaining target is now `AVIAN_CIRCUIT:001`, whose `IMPLEMENTS` edge into
`PRIM:composition` is legal (that is the relation designed for it) but still rests on
structural analogy rather than any measured computation.

**Re-run after all fixes, every check:**

```
fetch_taxonomy.py --offline                       exit 0   26/26 species
fetch_source_metadata.py --agent comparative      exit 0   18/18 verified
check_phylogenetic_cap.py                         exit 0   cap respected
check_phylogenetic_cap.py --legacy-rule           exit 1   old behaviour correctly fails
check_ownership.py --agent comparative            exit 0   75/75 paths
jsonschema vs schemas/*.json                               68 records, 0 errors
graph/validate_graph.py --strict                           0 violations in my files
ontology triple re-check (own script)                      21/21 legal triples
```

`pytest` was **not** run, per the coordinator's instruction while `agent:ontology`
finishes the suite. No git command was run at any point.

---

## 11. Duplicate source registration and the V16b null relation (2026-09-17, final round)

### 11.1 Both sources restored; §1.3 and the validator now agree

`SRC:PMID:30340039` (Beaulieu-Laroche 2018) and `SRC:PMID:20837545` (Lee 2010) are
registered **here and by `agent:brakes`**. Contract §1.3 now allows and prefers this: each
agent's claims stay self-contained, no agent depends on a file it cannot edit, and
deduplication happens downstream — the store, the graph compiler and
`independent_source_count` all dedupe by `source_id`, so duplication cannot inflate any
evidence count.

I removed these two in the previous round because the validator was still failing them
under V4. The coordinator reversed that, and the validator has since been updated:
**repo-wide duplicate-source-id violations are now 0**, down from 272 V4 violations to 10
(none mine).

**Divergence — the new hard error — was checked explicitly, not assumed.** Both of my
registrations were compared field-by-field against `evidence/sources/brakes.yaml` and are
identical on `title`, `year`, `first_author`, `container` and `doi`. A helper that
re-checks this is worth adding to the validator if it does not already exist, since
divergence can appear later when either agent edits a record.

The note at the top of `evidence/sources/comparative.yaml` was rewritten accordingly. It
now records that the shared citation **is itself a signal for the red team's
`citation_dependence` check**: both papers are load-bearing for `agent:brakes`'
mechanistic case *and* for this atlas's translation-risk case, so if either paper is
wrong, two apparently independent lines of argument move together. The three claims
concerned are `CLM:comparative:DENDRITE:001`, `CLM:comparative:HCN1:004` and
`CLM:comparative:RGS14:001`.

### 11.2 HCN1 hedge removed

The "reverts to 2 if you judge otherwise" sentence is gone from
`atlases/comparative/assessments/HCN1.yaml`'s `cross_species_convergence.counter_rationale`.
`counter_level` stands at **3**. In its place the rationale now records the contract's own
statement that the asymmetry is deliberate and *not* neutral — weak method can raise
doubt but cannot establish support, because this project's dominant risk is
over-optimism — and that the cost is a systematic under-ranking of a genuinely promising
target whose evidence is weak in both directions, which `agent:integration` measures via
the `symmetric_caps` sensitivity variant rather than assuming.

### 11.3 `NO_DETECTED_EFFECT_ON` (V16b): evaluated on all five candidates, zero migrated

All five claims carrying `null_result` or `contradicts` evidence were checked against the
relation's domain, range, `allowed_claim_types` and evidence-role requirement.

| Claim | Eligible? | Decision |
|---|---|---|
| `SELF_REGULATION:002` | **No** — `BrainRegion` not in domain | **Blocked.** The one genuine null here, and the one that most needs the relation. See below. |
| `NEURON_SCALING:003` | No — `BrainRegion` not in domain | Not migrated; also a difference detected, not a null |
| `NEURON_SCALING:005` | No — `BrainRegion` not in domain | Not migrated; a method disagreement, not a null |
| `SELF_REGULATION:003` | No — `ComputationalPrimitive` not in domain | Not migrated; it found a positive effect |
| `CEPHALOPOD_GENOME:001` | **Yes** | **Refused on honesty grounds** |

**The blocked case is a correctness problem, not a presentational one.**
`CLM:comparative:SELF_REGULATION:002` satisfies every condition V16b asks for —
`effect_direction: no_change`, `evidence_role: contradicts`, `claim_type: association` —
and is blocked solely because the tested predictor is brain volume, so its subject is
`REGION:brain`. It therefore still compiles as
`REGION:brain -CONSTRAINS-> PRIM:distractor_suppression` with `direction: unclear`, and a
traversal that does not read `direction` will count this atlas's most-cited deflationary
claim as **support** for "bigger brain implies better inhibition" — the opposite of what
the study found, and exactly the positive drift V16b was introduced to stop. Filed as
**`docs/blackboard/schema_change_requests/comparative-002.yaml`** (non-blocking), asking
for `BrainRegion`, `CellType`, `Circuit`, `Network` and `ComputationalPrimitive` in the
domain and nothing else about the relation changed.

**The refusal matters as much as the block.** `CEPHALOPOD_GENOME:001` *is* eligible today
and I did not migrate it: nobody tested whether protocadherin expansion affects structural
plasticity rate, so a null edge there would manufacture a finding out of a gap, which the
relation's own semantics forbid. Recorded in the claim's `risks` and in the change request
so a later reader does not "fix" the omission.

### 11.4 `direction: state_dependent` considered and rejected

The one candidate was `CLM:comparative:HCN1:004`, whose sign depends on cortical layer.
`ontology/vocabularies.yaml` defines `state_dependent` as a sign depending on the rest of
the **physiological** state (benefit only from a low baseline or under stress). A cortical
layer is an anatomical compartment, not a state, and `state_dependent` would imply a
state-conditional rule this atlas cannot state. `unclear` is retained — the claim exists
precisely to establish that no single direction is supported. Recorded in that claim's
`risks` so the evaluation is auditable rather than invisible.

### 11.5 ChEMBL-style database facts: not applicable

This atlas has no intervention records, no `atlases/comparative/interventions/` directory
and no database-derived numbers, so the `max_clinical_phase` / `first_approval_year`
canonical slots do not apply. Confirmed by grep across all owned files.

### 11.6 Final counts, every check re-run

```
scripts/fetch_source_metadata.py --agent comparative   exit 0   20/20 verified, similarity 1.0, no retractions
graph/validate_graph.py --strict                       exit 1   0 violations in agent:comparative files
                                                                0 duplicate-source-id violations repo-wide
pipelines/comparative/fetch_taxonomy.py --offline      exit 0   26/26 species
pipelines/comparative/check_phylogenetic_cap.py        exit 0   cap respected
pipelines/comparative/check_phylogenetic_cap.py --legacy-rule
                                                       exit 1   pre-§5.4 behaviour correctly fails
scripts/check_ownership.py --agent comparative         exit 0   75/75 paths
jsonschema vs schemas/*.json                                    70 records, 0 errors
```

**A caution on the repo-wide validator number: do not quote it from this note.** Other
agents are writing concurrently and it moves substantially between runs — three runs
during this final round returned 560, 1227 and 487 total violations, with the rule mix
shifting each time (V1 235 → 811 → 432; V9 11 → 362 → 3). Re-run the validator rather
than trusting any snapshot of that figure, including mine.

The two numbers that were stable across all three runs are the ones worth recording:
**0 violations in `agent:comparative` files**, and **0 duplicate-source-id violations
repo-wide** once §1.3 and the validator were aligned. The only other rule touching
sources, V6, had one violation in the final run and it is
`agent:alphacognition`'s (`SRC:DB:chembl:ChEMBL_37`, no verification record); all 20 of
this atlas's sources carry `status: verified`.

`pytest` not run and no git command run at any point, per instruction.

---

## 12. R9 / R10 migrations — APPLIED (2026-09-17, final state)

Both migrations from `docs/blackboard/RESOLUTIONS.md` R9 and R10 are **applied**. They
were blocked for most of this round and became possible mid-run when `agent:ontology`
landed the support: `ontology/edges.yaml` at 18:11 (the V16b-sym domain widening) and
`schemas/claim.schema.json` at 18:13 (`negated_relation`, `direction_context`).

**R9 — `CLM:comparative:SELF_REGULATION:002`**

```
REGION:brain -NO_DETECTED_EFFECT_ON-> PRIM:distractor_suppression
    negated_relation: CONSTRAINS
    direction: no_change          (was: CONSTRAINS / unclear)
    claim_type: association       (unchanged; permitted by the relation)
    evidence_role: contradicts · endpoint_measured: measured
```

`direction` moved from `unclear` to `no_change` to match the evidence item's
`effect_direction`; a null edge whose direction is "unclear" would have been a smaller
version of the same problem. No traversal may now count this edge as support, which was
the entire point of the request.

**R10 — `CLM:comparative:HCN1:004`** is now `direction: state_dependent` with
`direction_context` naming the laminar dependency: the human-versus-rodent h-current
difference reverses sign between supragranular layers (stronger in human) and layer 5
(HCN conductance below the mammalian allometric prediction), and the dependency is on
laminar position rather than physiological state. Both claims' `risks` blocks now record
*why* the value changed, replacing the notes that recorded why it could not.

**The other three were re-checked as R9 asked, and still do not migrate.** Eligibility
under the widened domain is necessary but not sufficient — V16b requires a *measured
absence*, and all three report measured presences: `NEURON_SCALING:003` (elephant cortex
about a third of the human cortical count: a difference detected), `NEURON_SCALING:005`
(fourfold stereology-versus-fractionator conflict: a measurement disagreement),
`SELF_REGULATION:003` (reinforcing a fixed motor response improved detour scores: a
positive effect). `CEPHALOPOD_GENOME:001` remains deliberately unmigrated per R9.

### 12.1 How it was applied, and why that matters for the next agent

`pipelines/comparative/migrate_null_and_direction.py` encodes both migrations rather than
leaving them as a note somebody had to remember. It checks six preconditions against
`ontology/edges.yaml` and `schemas/claim.schema.json`, refuses to run with a
per-precondition report while any is unmet, is idempotent, fails loudly if either claim's
shape has changed, and has a `--dry-run`. It genuinely refused (exit 2, naming the two
missing schema fields) until the schema landed, then applied both cleanly. It now reports
"already applied" and exits 0. The re-check reasoning for the three non-migrating claims
is in its docstring, so it is re-checkable rather than re-litigated.

### 12.2 V16c surfaced one real violation, and prompted a full pass

Migrating `SELF_REGULATION:002` immediately failed the new **V16c** — a null edge needs an
evidence item with **both** `endpoint_measured: measured` and a contradicting or null
role, because *a measured absence is not an absence of measurement*. That field did not
exist when this atlas was written.

Rather than patch the one failing item, `endpoint_measured` was set honestly on **all 25
evidence items**: 24 `measured`, and one `not_measured_in_protocol` —
`CLM:comparative:NEURON_SCALING:006`, a biophysical model whose endpoint is a computed
quantity, not a measurement. That single exception is noted in the claim's `risks`. The
distinction V16c enforces is the same one this atlas exists to police, so recording it
everywhere rather than only where a rule bites is the point.

### 12.3 Final counts — the run to trust

```
scripts/fetch_source_metadata.py --agent comparative      exit 0
    20/20 verified · all status verified · 0 retracted · min title_similarity 1.0

graph/validate_graph.py --strict                          exit 1
    430 repo-wide (V1 378, V15 27, V16b-sym 6, V14 6, V16 5, V9 3, V16c 2, V-DIR 2, V3 1)
    0 in agent:comparative files

pipelines/comparative/migrate_null_and_direction.py       exit 0   already applied
pipelines/comparative/check_phylogenetic_cap.py           exit 0   cap respected
pipelines/comparative/check_phylogenetic_cap.py --legacy-rule
                                                          exit 1   pre-§5.4 rule correctly fails
pipelines/comparative/fetch_taxonomy.py --offline         exit 0   26/26 species
scripts/check_ownership.py --agent comparative            exit 0   76/76 paths
jsonschema vs schemas/*.json                                       70 records, 0 errors
```

The repo-wide validator total moved across this round's runs (560 → 1227 → 487 → 421 →
430) as other agents write; only the figure above should be quoted, and the stable number
is **0 violations in `agent:comparative` files**. The remaining repo-wide V16b-sym (6),
V16c (2) and V-DIR (2) violations are other agents' records adapting to the same new
rules. `pytest` not run and no git command run at any point.
