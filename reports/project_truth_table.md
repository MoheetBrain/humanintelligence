# Project truth table

**Generated 2026-09-18 by `pipelines/reports/build_truth_table.py` — do not hand-edit.** Machine-readable twin: [`project_truth_table.csv`](project_truth_table.csv).

> One row per tracked hypothesis, stating what is established, what contradicts it, and what would kill it. The statuses are judgements made by reading the repository's records; every row names the artefacts it rests on.

## The headline

**`SUPPORTED`: 0.** No hypothesis in this project has adult human causal evidence that has replicated. The strongest *human* result in the repository is a replicated **null** (GABRA5). That is not a failure of the search — it is the finding.

| status | n | meaning |
|---|---|---|
| `SUPPORTED` | 0 | adult human causal evidence, replicated |
| `PROMISING_BUT_UNRESOLVED` | 1 | real evidence, decisive question still open |
| `DOWNGRADED` | 11 | was rated higher; a specific finding lowered it |
| `UNRESOLVED` | 7 | insufficient evidence either way |
| `CONTRADICTED_IN_STUDIED_CONTEXT` | 3 | tested in humans and failed **in that context** |
| `NOT_ASSESSED` | 4 | no evidence in this repository at all |

**The two states that are easiest to confuse** are the last two. `CONTRADICTED_IN_STUDIED_CONTEXT` means someone looked and the answer was no, in a specific population. `NOT_ASSESSED` means nobody looked. Neither is a statement that the biology is wrong, and collapsing them is this project's most persistent bug.

---

## SUPPORTED — none

## PROMISING_BUT_UNRESOLVED (1)

### PDE4B inhibition enhances adult human memory

**Why:** Ranks first in the cohort and still cannot be promoted. Roflumilast is a PAN-PDE4 inhibitor: as evidence about the ENDPOINT it is directly relevant, as evidence about THIS GENE it is not — which is why above_baseline_enhancement was downgraded 3->2. The dose-response inversion is unexplained and is the kind of finding that usually means the mechanism is not what it appears.

**Supporting:** two randomised human studies with cognitive endpoints (roflumilast, healthy young adults and 60-80s); human_intervention_evidence level 3 — the joint-highest here

**Contradictory:** a clinical null in schizophrenia (working memory); benefit occurred at the LOWEST of three doses

| modality | state |
|---|---|
| human genetics | positional GWAS; causal_gene_attribution level 1; three of four credible sets are educational attainment |
| human molecular | bulk expression only; no QTL colocalisation |
| human intervention | measured, positive in healthy adults; 141 registry studies, 113 tested a non-cognitive endpoint |
| animal causal | weak — no PDE4B-SELECTIVE perturbation evidence (level 1) |
| comparative | none |
| adult relevance | DEMONSTRATED IN ADULTS — the strongest adult evidence in the cohort |
| developmental relevance | low risk (developmental_confound_risk level 0 / counter 3) |
| replication | two studies, same compound class, same group lineage |

**Next kill test:** A PDE4B-SELECTIVE agent with a cognitive endpoint in healthy adults. Until one exists, the gene attribution is family-level, not gene-level.

**Depends on:** `CLM:brakes:PDE4B:001-003; AUD:red_team:PDE4B:001; evidence/registry_searches/PDE4B.yaml`

## DOWNGRADED (11)

### ADGRB1 is a cognition-relevant target (nominated externally)

**Why:** A gene-based test can be significant where no single variant is, so the sub-threshold variant evidence does not refute the external claim. But this repository's own variant-level evidence is WEAK and must not be described as strong until the gene-based result is delivered and verified. The branch that was to deliver it does not exist.

**Supporting:** a gene-based claim attributed to an external analysis whose artefacts have never been delivered

**Contradictory:** this repository's own check found ONE association, one study, p=2e-07 — BELOW the 5e-08 genome-wide threshold

| modality | state |
|---|---|
| human genetics | one sub-threshold variant-level association; positional only |
| human molecular | none |
| human intervention | none |
| animal causal | none |
| comparative | none |
| adult relevance | unknown |
| developmental relevance | unknown |
| replication | none |

**Next kill test:** Obtain the gene-based statistic with its artefact and cohort; until then the claim is unverifiable rather than wrong.

**Depends on:** `targets/discovered/discovered_registry.yaml; docs/integration/CODEX_BRANCH_AUDIT.md`

### HCN1 blockade enhances adult human cognition (dendritic brake)

**Why:** The best-covered target is also the clearest case of two failures. Its comparative counter-evidence is HIGHER than its supporting level, and the human-versus-rodent dendritic difference caps translation of its strongest animal evidence. Separately, three of its five apparent evidence modalities trace to two papers, so its breadth is partly double-counting.

**Supporting:** the repository's best-covered target — facet coverage 1.00, 21 claims, 15 independent sources; adult-inducible rodent perturbation; comparative evidence assessed

**Contradictory:** adult human layer-5 dendrites couple more weakly to the soma and carry LOWER channel density than rat, measured directly; the two direct human-versus-rodent h-current comparisons DISAGREE IN SIGN by cortical layer; adult HCN1-null mice are more seizure-susceptible

| modality | state |
|---|---|
| human genetics | L2G ranks HCN1 at 2 credible sets with a COMPETING candidate gene (MRPS30) at the same loci and no QTL corroboration; causal_gene_attribution 2 / counter 2 |
| human molecular | no colocalisation (measured and absent) |
| human intervention | none — 1 registry study, non-cognitive endpoint; the only tool compound (ZD7288) is not a clinical agent |
| animal causal | strong (level 3 / counter 2), including adult-inducible |
| comparative | ASSESSED — cross_species_convergence 2 / counter 3; human_lineage_divergence_risk 3 |
| adult relevance | adult-inducible rodent perturbation exists |
| developmental relevance | one key knockout is forebrain-restricted but NOT time-restricted to adulthood |
| replication | within rodents yes; across species the sign is contested |

**Next kill test:** Resolve the layer-specific sign disagreement in human tissue before any further investment; and resolve HCN1 vs MRPS30 at the credible sets.

**Depends on:** `CLM:brakes:HCN1:001-006; CLM:comparative:HCN1:001-004; AUD:red_team:HCN1:001; atlases/convergence/dependency_rules.yaml D007`

### RGS14 suppression enhances adult cognition (CA2 plasticity brake)

**Why:** The headline finding is the life-stage mismatch: lifelong absence of a plasticity brake during the window when it is normally installed is a DEVELOPMENTAL manipulation, and an adult test of it says nothing about blocking the protein in an adult brain. Its only human-relevant evidence is a single review presenting no human cognitive phenotype.

**Supporting:** germline knockout mice show enhanced CA2 LTP and enhanced spatial and object-recognition memory

**Contradictory:** RGS14 protein is UNDETECTABLE in mouse brain at birth and rises through the first postnatal weeks — the knockout removes it during the period it is being installed

| modality | state |
|---|---|
| human genetics | measured and ABSENT — an explicit evidence_gap claim records that a systematic sweep across 22 cognitive traits returned no association |
| human molecular | bulk expression only |
| human intervention | none — 1 registry study, non-cognitive endpoint; NO intervention record exists for RGS14 anywhere in the repository |
| animal causal | germline knockout ONLY; adult_onset_perturbation level 0 |
| comparative | assessed — convergence 2, divergence risk 1 / counter 2 |
| adult relevance | read-out is adult; the PERTURBATION is lifelong |
| developmental relevance | HIGH RISK — developmental_confound_risk level 3 / counter 0 |
| replication | one 2010 paper supplies three claims across two atlases |

**Next kill test:** An adult-onset, time-restricted RGS14 suppression in animals. Without it, nothing here transfers to an adult intervention.

**Depends on:** `CLM:brakes:RGS14:001-004; AUD:red_team:RGS14:001; SRC:PMID:20837545`

### CRTC1 activation enhances memory (allocation / CREB coactivation)

**Why:** Carries the cohort's only unresolved CRITICAL red-team finding — educational attainment mistaken for intelligence — which gated its composite score. It is simultaneously the target the selective-encoding hypothesis most directly names (SE2, activity as the address) and one with essentially no human evidence. That combination is exactly what the hypothesis's guards exist to stop from becoming a promotion.

**Supporting:** two adult-inducible AAV overexpression studies in mouse dentate gyrus — the cleanest ADULT-ONSET animal perturbation in the cohort

**Contradictory:** its human genetic support was a single 'self-reported maths ability' association from an educational-attainment GWAS

| modality | state |
|---|---|
| human genetics | DOWNGRADED 3->1 by a CRITICAL red-team finding; no non-education corroboration; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | NO MATCHING TRIAL FOUND — complete screen of ClinicalTrials.gov (21 records examined, 21 total). NOT a biological null: nobody has tested it, so there is nothing to have failed |
| animal causal | adult-inducible overexpression (level 2); transfer_breadth 0; dose_response_knowledge 0 |
| comparative | none |
| adult relevance | adult-onset perturbation demonstrated in animals |
| developmental relevance | low risk (level 0 / counter 2) |
| replication | two studies from a closely related line of work |

**Next kill test:** Any human genetic association with a NON-EDUCATION cognitive measure; and an animal study measuring whether enhancement is confined to task-engaged representations (the SE6 test).

**Depends on:** `CLM:alphacognition:CRTC1:001-003; AUD:red_team:CRTC1:001; evidence/registry_searches/CRTC1.yaml`

### GPR158 antagonism enhances adult cognition

**Why:** Deprioritised by audit for overclaiming. A target whose DESIRABLE DIRECTION OF MANIPULATION is unknown cannot be a candidate, whatever its evidence volume — you cannot design an intervention when agonism and antagonism are both defensible.

**Supporting:** germline knockout, ADULT-INDUCIBLE genetic perturbation, and an osteocalcin-CA3 memory pathway in aged animals

**Contradictory:** THE DIRECTION IS UNRESOLVED: one literature makes GPR158 an excitability brake (suppress it), another makes it the receptor for a memory-PROMOTING hormone (preserve it). One of its two level-3 genetic records is an MTAG combining education and intelligence.

| modality | state |
|---|---|
| human genetics | positional plus one L2G credible set on intelligence; causal_gene_attribution 2 |
| human molecular | bulk expression only |
| human intervention | not_measured — 33 registry studies, 29 tested a non-cognitive endpoint; human_intervention_evidence level 0 |
| animal causal | present including adult-inducible; above_baseline_enhancement level 0 / counter 1 |
| comparative | none |
| adult relevance | adult-inducible perturbation exists |
| developmental relevance | HIGH RISK — developmental_confound_risk level 3 |
| replication | no |

**Next kill test:** Resolve the direction: an adult-onset manipulation that measures cognition while distinguishing the brake role from the osteocalcin-receptor role.

**Depends on:** `CLM:brakes:GPR158:001-003; AUD:red_team:GPR158:001`

### Klotho (KL) elevation enhances adult and aged cognition

**Why:** The adult-relevance profile is the best in the cohort and the evidence quality does not match it. A non-monotonic dose response with a conflicted author, plus an opposite-direction human cohort, is the signature of a finding that will not replicate. Its stated mechanism is synaptic and glutamatergic, which does not link it to any power-domain state variable the atlas placed it in.

**Supporting:** human observational association with executive function; mouse overexpression; administration in AGED NON-HUMAN PRIMATES; adult_onset_perturbation level 3

**Contradictory:** DOSE-RESPONSE INVERSION — benefit at a low dose and NONE at a high dose in primates, on a study with a commercially interested author. A 527-person cohort found the same KL-VS variant reported as protective elsewhere associated in the OPPOSITE direction. Its lead claim is flagged `contested`.

| modality | state |
|---|---|
| human genetics | MEASURED AND ABSENT on the cognitive panel (explicit evidence_gap claim); support is candidate-variant association only; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | A completed early-phase-1 study in 14 adults aged 50-80 DOES exist (NCT07285629) with five NIH Toolbox cognitive secondary outcomes — NO RESULTS POSTED. Graded 0, and the grading reasons are recorded so a later agent can disagree with them |
| animal causal | mouse and non-human primate; above_baseline_enhancement 2 / counter 3 |
| comparative | none |
| adult relevance | adult and aged throughout — its strongest feature |
| developmental relevance | not a developmental confound |
| replication | contradicted rather than replicated in human cohorts |

**Next kill test:** The posted results of NCT07285629; and an independent replication of the KL-VS cognitive association in a cohort that did not generate it.

**Depends on:** `CLM:power:KL:001-004; AUD:red_team:KL:001; SRC:NCT:NCT07285629`

### CHRM1 (M1 muscarinic) agonism enhances adult human cognition

**Why:** Carries the heaviest systemic liability burden in the cohort (safety level 4: the full peripheral cholinergic toxidrome plus liver-failure annotations, corroborated by 52% discontinuation) and is the only target gated on safety alone. The single most promising human cognitive result in the repository sits on top of a withdrawn trial and a toxicology signal.

**Supporting:** THE REPOSITORY'S ONLY HEALTHY-ADULT HUMAN COGNITIVE RESULT — HTL0018318 improved working memory in 36 healthy young and 50 healthy elderly adults; xanomeline efficacy in Alzheimer's; adult_expression_and_timing level 3

**Contradictory:** the phase 2 of that very compound was WITHDRAWN BEFORE ENROLLING ANYONE, pending an unexpected animal toxicology finding. 52% of patients in a high-dose arm discontinued for adverse events. A clinical-harm meta-analysis. M1-null mice show a BIDIRECTIONAL phenotype including normal or enhanced memory on some tasks.

| modality | state |
|---|---|
| human genetics | MEASURED AND ABSENT on the cognitive panel; causal_gene_attribution 0 |
| human molecular | bulk expression only; the largest human M1 dataset by sample size measured NO cognitive endpoint at all — a gap, not a null |
| human intervention | MEASURED AND POSITIVE in healthy adults, level 3, but the result is a single exploratory, unreplicated, developer-affiliated secondary analysis carrying three facets |
| animal causal | germline knockout, bidirectional |
| comparative | none |
| adult relevance | healthy young and elderly adults — the cleanest adult relevance here |
| developmental relevance | not a developmental confound |
| replication | NONE — one secondary analysis |

**Next kill test:** The outcome of the toxicology investigation, and any replication of the healthy-adult working-memory effect by a non-affiliated group.

**Depends on:** `CLM:alphacognition:CHRM1:001-005; AUD:red_team:CHRM1:001; SRC:NCT:NCT03592862`

### GRIN2B (NR2B) elevation enhances adult human cognition

**Why:** The repository's CLEAREST life-stage mismatch. Constitutive developmental overexpression enhances rodent memory while human variants in the same gene cause neurodevelopmental disorder. Both can be true — dose and direction and timing differ — but the animal result cannot be cited as adult human evidence.

**Supporting:** forebrain NR2B overexpression enhances rodent memory across three claims; 19 claims total

**Contradictory:** HUMAN VARIANTS IN THE SAME GENE CAUSE NEURODEVELOPMENTAL DISORDER — 86 individuals with de novo pathogenic variants, plus a rare-variant burden result, both locus-to-gene-resolved and both in the DELETERIOUS direction

| modality | state |
|---|---|
| human genetics | the only target here with resolved rare-variant human genetics — and it is developmental and deleterious; GWAS is positional, L2G sets are educational attainment and mathematical ability; causal_gene_attribution 1 |
| human molecular | bulk expression; the NR2B-to-NR2A developmental switch is itself evidence that adult and juvenile biology differ |
| human intervention | not_measured for enhancement — 257 registry studies, 141 with non-cognitive endpoints, 17 completed-unreported reporting gaps, 27 with posted results awaiting extraction |
| animal causal | strong (level 3 / counter 2) but adult_onset_perturbation only level 1 |
| comparative | none |
| adult relevance | animal read-out is adult; the manipulation is constitutive |
| developmental relevance | HIGHEST RISK — developmental_confound_risk level 3; the human genetics is prenatal and postnatal-developmental |
| replication | rodent enhancement replicated; human direction is opposite |

**Next kill test:** Adult-onset, time-restricted NR2B elevation with a cognitive read-out and a safety assessment; and extraction of the 27 trials with posted results already in the queue.

**Depends on:** `CLM:alphacognition:GRIN2B:001-006; AUD:red_team:GRIN2B:001`

### OTX2 modulation reopens adult plasticity

**Why:** Deprioritised by audit. Critical-period biology describes how plasticity CLOSES during development; reopening it in an adult is a different intervention with different risks, and the developmental evidence does not license it.

**Supporting:** developmental critical-period biology; human_genetic_association level 3

**Contradictory:** a major developmental_effect_mistaken_for_adult finding; gated by developmental_confound_caps_d2

| modality | state |
|---|---|
| human genetics | level 3 association but causal_gene_attribution 1; no signal in the current Open Targets release |
| human molecular | bulk expression only |
| human intervention | NO MATCHING TRIAL FOUND — complete screen (2 records examined, 2 total). Nobody has tested it |
| animal causal | developmental |
| comparative | none |
| adult relevance | the core problem — the biology is a CRITICAL-PERIOD mechanism |
| developmental relevance | the evidence IS developmental |
| replication | not applicable |

**Next kill test:** An adult-onset manipulation demonstrating reopened plasticity WITHOUT loss of stability — SE7 in the selective-encoding framing.

**Depends on:** `AUD:red_team:OTX2:001; evidence/registry_searches/OTX2.yaml`

### ADORA1 (adenosine A1) antagonism enhances cognition

**Why:** The clearest case of restoration being read as enhancement: most human adenosine cognitive data compares caffeine against a withdrawn or sleep-deprived baseline, which measures rescue. It also has the repository's largest reporting-gap burden — 37 completed trials with cognitive outcomes in protocol and nothing posted. This is the ONLY target whose registry screen remains partial (1,000-record cap).

**Supporting:** animal causal work and a large human intervention literature (caffeine and relatives); level 2

**Contradictory:** a major RESCUE-MISTAKEN-FOR-ENHANCEMENT finding — reversing a deficit is not raising a healthy baseline; counter level 3

| modality | state |
|---|---|
| human genetics | none; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | the largest registry footprint in the repository — 434 studies, 323 with non-cognitive endpoints, 37 COMPLETED-UNREPORTED reporting gaps, 3 with posted results awaiting extraction |
| animal causal | present |
| comparative | none |
| adult relevance | adult human exposure is ubiquitous |
| developmental relevance | not the issue here |
| replication | extensive, and mostly on the wrong question |

**Next kill test:** A non-withdrawn, non-sleep-deprived healthy-adult baseline with a cognitive endpoint; and retrieval of the 37 unreported results.

**Depends on:** `CLM:brakes:ADORA1:001-007; AUD:red_team:ADORA1:001; evidence/registry_searches/ADORA1.yaml`

### CONVERGENCE — the repository's targets are supported by multiple independent evidence modalities

**Why:** The apparent breadth was an artefact of filing one observation in two places: atlas facet grades counted beside the claims they are computed FROM, one expression dataset counted per target, GWAS Catalog and Open Targets L2G counted as two observations of the same summary statistics, and null trials counted as a separate modality. The correction removes a modality precisely from the best-evidenced targets.

**Supporting:** before correction, all 27 targets appeared in two or more modalities and several in five

**Contradictory:** after removing double-counting, NO target exceeds THREE independent modalities, and three targets rest on animal evidence alone

| modality | state |
|---|---|
| human genetics | largely one or two cohorts; UK Biobank recurs under many source ids |
| human molecular | ONE GTEx v8 bulk-tissue run populates the column for essentially every target |
| human intervention | present for 20 of 27; power-atlas targets were searched by a different route and carry no A-G code |
| animal causal | the most widely present modality, and the least transferable |
| comparative | 23 of 27 assessments are not_assessed |
| adult relevance | not applicable |
| developmental relevance | not applicable |
| replication | seven distinct double-counting mechanisms identified and verified |

**Next kill test:** Build the convergence scorer and the validator rule. The rules are encoded but NOT enforced, so the double-counts can be reintroduced with nothing firing.

**Depends on:** `atlases/convergence/dependency_rules.yaml; reports/convergence_v0_2.md`

## UNRESOLVED (7)

### 2q12.3 DUPLICATION is associated with higher cognitive performance

**Why:** The rarest and most valuable KIND of evidence available (a variant associated with HIGHER performance), and currently a single unreplicated association with no effect size in hand. LOEUF was recorded for the eight genes and is the WRONG METRIC — it measures loss-of-function intolerance and the variant is a duplication; triplosensitivity is the right metric and is absent.

**Supporting:** one CNV-GWAS association, N=258,292 (Huguet 2024, PMID 39667348), verified independently via PubMed

**Contradictory:** none identified — and no replication either

| modality | state |
|---|---|
| human genetics | CNV association only; breakpoints, carrier count and effect size all UNKNOWN to this repository; driver gene unresolved across 8 protein-coding genes in a 2 Mb cytoband |
| human molecular | none |
| human intervention | not applicable — a natural variant, not an intervention |
| animal causal | none |
| comparative | none |
| adult relevance | not stated in the retrieved source |
| developmental relevance | not stated |
| replication | NONE — described by its authors as first-of-its-kind |

**Next kill test:** Obtain the supplementary CNV coordinates, carrier count and effect size; then ask whether the cohort overlaps this repository's existing cognitive-GWAS base, which would make it non-independent.

**Depends on:** `atlases/positive_genetics/2q12_3_duplication.yaml; SRC:PMID:39667348`

### GRM3 is a cognition-relevant target

**Why:** Variant-level support is real and is the strongest of the three externally nominated genes. It is still positional: no causal gene, no direction, no adult mechanism. Entered the registry as an UNRANKED hypothesis.

**Supporting:** GWAS Catalog: 4 distinct studies, 5 associations, strongest p=4e-13 — independently checked in this repository

**Contradictory:** one contributing study (PMID 30038396) is an EDUCATIONAL ATTAINMENT GWAS, not an intelligence GWAS

| modality | state |
|---|---|
| human genetics | positional mapping only; causal_attribution basis gwas_association_only, locus_to_gene_resolved: no |
| human molecular | none |
| human intervention | none |
| animal causal | none |
| comparative | none |
| adult relevance | unknown — an association says nothing about when a gene acts |
| developmental relevance | unknown |
| replication | 4 studies, but cohort overlap uncomputed; the sweep's publication set is small and heavily shared |

**Next kill test:** Fine-map the loci and test whether GRM3 rather than a neighbour carries the signal; and re-run the association count excluding educational-attainment studies.

**Depends on:** `targets/discovered/discovered_registry.yaml; GWAS Catalog 2026-09-13`

### EIF2B / integrated stress response modulation enhances adult memory

**Why:** Mechanistically the best-motivated candidate for converting transient encoding into a durable trace (SE3), and the one where the human cognitive question has simply never been asked. Its retyping from clinical_null to evidence_gap is the correct call and matters: a trial that never measured cognition cannot have failed at it. Tractability is the only 'not_assessed' in the cohort.

**Supporting:** ISRIB-class adult PHARMACOLOGICAL perturbation in rodents; an ADULT-ONSET human monogenic disease (vanishing white matter, 33 genetically confirmed patients) — the complex's only locus-to-gene-resolved human record

**Contradictory:** two terminated fosigotifator trials (ALS, major depressive disorder) that no atlas had recorded until the red team found them

| modality | state |
|---|---|
| human genetics | monogenic disease only; NO GWAS-level support; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | not_measured — 6 registry studies, all non-cognitive endpoints. The ALS platform trial specified ALSFRS, NOT a cognitive endpoint, so it is an evidence_gap and explicitly NOT a clinical null |
| animal causal | adult pharmacological plus conditional knockout |
| comparative | none |
| adult relevance | adult-onset human disease; adult rodent pharmacology |
| developmental relevance | one knockout is developmental, read out in adults |
| replication | no human cognitive test has been run |

**Next kill test:** Any ISR-modulating agent with a cognitive primary endpoint in adults. The two terminated trials tell us about ALS and depression, not memory.

**Depends on:** `CLM:brakes:EIF2B_COMPLEX:001-006; AUD:red_team:EIF2B_COMPLEX:001`

### EIF2S1 (eIF2alpha) modulation enhances adult memory

**Why:** Audited as insufficient_evidence with zero contradicted facets — nothing is wrong with it, there is simply not enough. It also should not be counted as independent support for the ISR hypothesis: EIF2S1 and EIF2B_COMPLEX are the SUBSTRATE and the GEF of one pathway and share their mechanistic rationale.

**Supporting:** conditional developmental knockout and in-vitro pharmacodynamics

**Contradictory:** none directly — the problem is absence, not contradiction

| modality | state |
|---|---|
| human genetics | MEASURED AND ABSENT — an explicit evidence_gap claim records a systematic sweep of GWAS Catalog across 22 cognitive traits and of Open Targets L2G returning no association |
| human molecular | bulk expression only |
| human intervention | not_measured — 10 registry studies, none with a cognitive endpoint |
| animal causal | developmental conditional knockout only; adult_onset_perturbation level 0 |
| comparative | none |
| adult relevance | plausible but untested |
| developmental relevance | the only causal evidence is developmental |
| replication | no |

**Next kill test:** An adult-onset perturbation with a cognitive read-out. The developmental knockout cannot answer the adult question.

**Depends on:** `CLM:alphacognition:gap.EIF2S1:001; AUD:red_team:EIF2S1:001`

### HDAC2 inhibition enhances adult memory (transcriptional gating)

**Why:** Liability is INHERITED FROM THE ONCOLOGY HDAC-INHIBITOR CLASS — thrombocytopenia, hepatotoxicity, fatigue, hypoacusis — while target-level annotation returns nothing, so the safety picture looks cleaner at the gene than it is in practice. The trichostatin result is the more interesting problem: potentiation that decays is not enhancement.

**Supporting:** germline knockout and acute circuit perturbation in adult rats; adult_onset_perturbation level 2

**Contradictory:** trichostatin A enhanced an intermediate phase of LTP but had NO EFFECT on persistence — the property SE3 actually requires. A phase 2a null (FRM-0334) — on a MOLECULAR readout, not cognition

| modality | state |
|---|---|
| human genetics | MEASURED AND ABSENT on the cognitive panel; L2G support is educational-attainment-only; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | not_measured — 159 registry studies, 117 non-cognitive endpoints. The four terminations are ADMINISTRATIVE (recruitment, staffing, mis-registration), not mechanism failures |
| animal causal | level 2 / counter 1; above_baseline_enhancement only level 1 |
| comparative | none |
| adult relevance | adult rodent and adult human records |
| developmental relevance | moderate (level 2 / counter 2) |
| replication | no |

**Next kill test:** An HDAC2-selective agent (not a pan-inhibitor) with a persistence endpoint at a consolidation-relevant delay.

**Depends on:** `CLM:brakes:HDAC2:001-005; AUD:red_team:HDAC2:001`

### RTN4R (Nogo receptor) blockade reopens adult plasticity

**Why:** One of three targets resting on a SINGLE evidence modality after the convergence correction. Animal-only evidence for a developmental mechanism is the weakest configuration in the repository.

**Supporting:** animal causal evidence only — the sole modality it has

**Contradictory:** a major developmental_effect_mistaken_for_adult finding

| modality | state |
|---|---|
| human genetics | none on the cognitive panel; causal_gene_attribution 0 |
| human molecular | bulk expression only |
| human intervention | NO MATCHING TRIAL FOUND — complete screen (15 records examined, 15 total) |
| animal causal | present — and it is the ONLY evidence modality for this target |
| comparative | none |
| adult relevance | unestablished |
| developmental relevance | the evidence is developmental |
| replication | no |

**Next kill test:** Any human evidence of any kind.

**Depends on:** `AUD:red_team:RTN4R:001; evidence/registry_searches/RTN4R.yaml`

### X01 — cell-type enrichment implicates specific neuronal populations

**Why:** Recorded verbatim, cited by nothing, and mechanically prevented from supporting any claim, facet or assessment. Two nominal P-values near 0.011 are not proof, and P=0.08 is not a demonstration that pyramidal cells do not matter. Two of its METHODOLOGICAL instructions were adopted as safe before verification (no pyramidal-only gate; extreme cognition treated as continuous) because they only ever WIDEN what gets examined.

**Supporting:** an external analysis reporting a pyramidal-cell association (beta ~0.097, nominal P ~0.011) in one dataset

**Contradictory:** a second reported figure is P=0.08, which is not evidence of absence any more than P=0.011 is proof of presence

| modality | state |
|---|---|
| human genetics | cohort overlap with this repository's genetics base is UNRESOLVABLE pending a source list |
| human molecular | INERT — provenance_class external_analysis_unverified, excluded from evidential_classes and enforced inert by validator rule V-EXT |
| human intervention | not applicable |
| animal causal | not applicable |
| comparative | not applicable |
| adult relevance | unstated |
| developmental relevance | unstated |
| replication | none; no artefacts delivered |

**Next kill test:** Delivery of the artefacts named in the handoff contract, with the source list that would make cohort overlap resolvable.

**Depends on:** `analyses/external/X01_cell_type_enrichment.yaml; V-EXT`

## CONTRADICTED_IN_STUDIED_CONTEXT (3)

### GABRA5 (alpha5-GABA-A) negative allosteric modulation enhances cognition

**Why:** The most informative result in the repository, and it is negative. This is not absence of evidence; it is a PRECISE null that bounds the effect below roughly 0.2 SD in the studied population. The status says 'in studied context' deliberately: the trials were in cognitive impairment associated with schizophrenia and Down syndrome, so they do not strictly refute the mechanism in healthy adults — but nobody may cite the rodent data as though the human trials had not happened.

**Supporting:** conditional CA1 deletion and NAM pharmacology in rodents; 16 independent sources, the second-largest evidence base here

**Contradictory:** REPLICATED HUMAN NULL. Basmisanil phase 2b in CIAS: MCCB composite treatment differences -0.36 (p=0.730) and +0.28 (p=0.793). A second independently reported trial also failed. Two rodent compounds acting as POSITIVE modulators improved memory in aged rats — the opposite direction.

| modality | state |
|---|---|
| human genetics | positional; causal_gene_attribution 2 / counter 2 |
| human molecular | bulk expression only |
| human intervention | MEASURED AND NULL, replicated. level 1 / counter 4 — the counter was raised by red-team audit |
| animal causal | strong but contradicted (level 3 / counter 2); one rodent claim records a COST — impaired context discrimination |
| comparative | none |
| adult relevance | adult human trials |
| developmental relevance | animal perturbation is conditional-developmental |
| replication | THE NULL IS REPLICATED — two trials, not one trial reached twice |

**Next kill test:** Already run, twice. The only remaining question is whether healthy adults differ from the studied populations, and that question does not justify a new trial on this evidence.

**Depends on:** `CLM:red_team:GABRA5:001; SRC:NCT:NCT02953639; SRC:NCT:NCT02484703; evidence/registry_searches/results/GABRA5.yaml`

### GRM5 (mGluR5) modulation enhances cognition

**Why:** One of the most-cited model-to-human translation failures in neuroscience: a mechanism with excellent mouse data that did not transfer. Deprioritised by audit with its composite gated by an unresolved critical finding.

**Supporting:** animal causal evidence and positional human genetics (causal_gene_attribution 2)

**Contradictory:** AFQ056 in 148 adults with fragile X: study treatment FAILED to demonstrate efficacy. Carries a CRITICAL model_organism_translation_failure finding

| modality | state |
|---|---|
| human genetics | positional; causal_gene_attribution 2 / counter 2 |
| human molecular | bulk expression only |
| human intervention | MEASURED AND NULL in the studied population; level 0 / counter 3 |
| animal causal | present and strongly contradicted by the human result |
| comparative | none |
| adult relevance | adult human trial |
| developmental relevance | fragile X is a developmental condition |
| replication | the mGluR5 programme failed broadly across sponsors |

**Next kill test:** None warranted on current evidence. The informative work is post-mortem: WHY the mouse-to-human transfer failed, since that lesson generalises to other targets here.

**Depends on:** `CLM:red_team:GRM5:001; SRC:NCT:NCT01348087; AUD:red_team:GRM5:001`

### Any current target is ready for chemistry, docking or a lead compound

**Why:** This row exists to be cited when the question is asked. Virtual pharmacology remains gated, and the gate is not procedural caution — it is that no target has a causal gene assignment strong enough to design against. Docking a molecule into a protein this repository cannot show is the right protein would produce confident output with no epistemic content.

**Supporting:** none

**Contradictory:** highest causal-gene attribution anywhere in the cohort is 2; 17 of 27 seed targets sit at level 0; tier_1_analyse_next is EMPTY; zero molecular-QTL colocalisation repository-wide

| modality | state |
|---|---|
| human genetics | no target has a defensible adult causal gene assignment |
| human molecular | no colocalisation anywhere — measured and absent (70/70 L2G records) |
| human intervention | the best human evidence is a replicated NULL (GABRA5) |
| animal causal | strong and repeatedly shown not to transfer |
| comparative | not computed |
| adult relevance | no target has demonstrated adult causal control |
| developmental relevance | several leading targets are developmental mechanisms |
| replication | not applicable |

**Next kill test:** Raise ANY target to causal-gene level 3 with adult human evidence. Nothing downstream is justified before that.

**Depends on:** `reports/sprint1_summary.md; reports/target_ranking_v0_1.csv`

## NOT_ASSESSED (4)

### SELECTIVE ENCODING — an enhancer should raise the contrast between prioritised and incidental encoding, not memory globally

**Why:** All seven criteria SE1-SE7 are not_assessed_in_repository or partially_addressed. The hypothesis changes the MEASURED QUANTITY to a difference-in-differences, which makes most existing enhancer evidence not_assessable rather than supportive. A global memory enhancer scores zero on it however large its main effect.

**Supporting:** none in this repository; the hypothesis is a specification, recorded as THEORY:selective_encoding

**Contradictory:** none — no study in the repository measured the decisive quantity

| modality | state |
|---|---|
| human genetics | none |
| human molecular | none |
| human intervention | not_measured — no repository study separated prioritised from incidental material |
| animal causal | partially bearing: CRTC1, HDAC2, GRIN2B (SE2/SE3), none tested for selectivity |
| comparative | none |
| adult relevance | adult by construction |
| developmental relevance | not applicable |
| replication | not applicable — no result to replicate |

**Next kill test:** Find or design a study with within-session manipulation of item value, retention tested separately for prioritised and incidental items, at a consolidation-relevant delay. Absent that design, no candidate can be scored either way.

**Depends on:** `theory/selective_encoding_criteria.yaml; no claim records`

### GOAL-GATED PLASTICITY & RETRIEVAL — cognitive capacity is limited by an imperfect interface between conscious goals and the plasticity and retrieval machinery, not only by the machinery's capacity

**Why:** Relocates the deficit from capacity to CONTROLLABILITY, which makes the opposite prediction about headroom: peak involuntary performance becomes a demonstration of capacity that volition cannot reach, rather than evidence of a ceiling. It separates three channels — C1 gating, C2 persistence, C3 retrieval — and the repository has NO retrieval-oriented target at all, which under this framing is a structural gap rather than an oversight. It is also a live successor to Sprint 1's finding that the POWER envelope may not be limiting in healthy adults: an interface limit would still bind when no capacity is exhausted.

**Supporting:** none in this repository; recorded as THEORY:goal_gated_plasticity_retrieval. The phenomena it appeals to (one-shot encoding under imposed salience, expert chunking, cue-triggered reconstruction) are marked appealed_to_not_verified — the repository holds no evidence for any of them

**Contradictory:** none — `control_gap` has never been measured here

| modality | state |
|---|---|
| human genetics | none |
| human molecular | none |
| human intervention | not_measured — and notably, the decisive test requires NO intervention |
| animal causal | not applicable as posed — the claim is about volitional control |
| comparative | none |
| adult relevance | adult by construction |
| developmental relevance | not applicable |
| replication | not applicable — no result to replicate |

**Next kill test:** Estimate `control_gap` = performance under IMPOSED salience minus performance under merely INTENDED salience, matched for effort, arousal and time-on-task. Cheapest first: test whether existing study strategies already close it, which would make the hypothesis true and uninteresting.

**Depends on:** `theory/goal_gated_plasticity_retrieval.yaml; no claim records`

### COMPARATIVE CONVERGENCE — mechanisms recruited independently in cognitively specialised lineages are general requirements of cognition

**Why:** BOTH avian convergence candidates — New Caledonian crow and budgerigar — are absent from Ensembl Compara, while BOTH avian controls — chicken and zebra finch — are present. The available birds are the uninformative ones, so a scan would return a null for birds that is absence of MEASUREMENT of the specialised species. Octopus, the most independent lineage available anywhere, sits in a different resource entirely. Trait covariates are deliberately not ingested rather than recalled.

**Supporting:** none — no selection scan or convergence analysis has been run

**Contradictory:** not applicable

| modality | state |
|---|---|
| human genetics | not applicable |
| human molecular | not applicable |
| human intervention | not applicable |
| animal causal | not applicable |
| comparative | PANEL DEFINED, ANALYSIS NOT RUN. 11 of 13 non-human panel species have orthology available in Ensembl Compara |
| adult relevance | not applicable |
| developmental relevance | not applicable |
| replication | not applicable |

**Next kill test:** An orthology resource covering corvids and parrots. Without one, the avian arm is inoperable and no avian statement may be made in either direction.

**Depends on:** `atlases/comparative_v2/species_registry.yaml; selection_signals.yaml (NOT_COMPUTED)`

### EXTREME COGNITION provides evidence about enhancement mechanisms

**Why:** ZERO ARTEFACTS. No claim, source, assessment or target record exists. The only trace in the repository is an outstanding deliverable attributed to a branch that the branch audit establishes DOES NOT EXIST. This is a gap, not a null, and it is the largest single hole in the evidence base.

**Supporting:** none

**Contradictory:** not applicable

| modality | state |
|---|---|
| human genetics | none |
| human molecular | none |
| human intervention | none |
| animal causal | none |
| comparative | none |
| adult relevance | not applicable |
| developmental relevance | not applicable |
| replication | not applicable |

**Next kill test:** Obtain the source list, or build the evidence map independently.

**Depends on:** `docs/integration/CODEX_BRANCH_AUDIT.md; analyses/external/X01_cell_type_enrichment.yaml`

---

*Statuses are judgements, not computed values. They are recorded as such so they can be disagreed with — each row names the artefacts a disagreement would have to engage.*
