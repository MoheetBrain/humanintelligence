# KIFC2 — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**CAUSAL_GENE_MODERATE (locus L65265, stratum L3).** KIFC2 wins on class count at a weak, gene-dense 8q24.3 locus, and that lead
rests on two enhancer links and a single ROSMAP colocalisation. The literature adds almost no independent support for a
cognition role. The single knockout mouse study found no overt phenotype. Treat KIFC2 as the best-supported gene at a weak locus, not as an established cognition gene.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L65265 (MAGMA label FOXH1), stratum **L3**, log10BF_independent 0.3795, locus rank 22 (interval 7–99), gc_aligned_z 1.668, panel A |
| V2G classes | ENHANCER_LINK (2) + QTL (1); n_classes 2. Other genes with classes: FOXH1, PPP1R16A, RECQL4, ZFTRAF1 (max 1 class each) |
| Enhancer links | ENCODE-rE2G (Open Targets 26.06, brain biosamples): rs2291133 → KIFC2 score 0.848; rs112422823 → KIFC2 score 0.407 |
| QTL | 1 strong coloc (PP.H4 ≥ 0.8), ROSMAP only (Sprint 4 coloc.abf, Davies × eQTL Catalogue) |
| FOCUS | packet records primary PIP 0.0 and no contradiction. `joint_gene_tissue_finemapping.csv` has **no rows for L65265**, so read this as "not evaluated", not as evidence against |
| Open Targets L2G 26.06 | KIFC2 0.6535 (stable vs Sprint 4); second ZFTRAF1 0.4886; rank-1 majority across credible sets = **ZFTRAF1** (0.5); top SHAP = distanceSentinelFootprintNeighbourhood (POSITIONAL); flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Direction | D4 / UNRESOLVED: 1 row, 1 cohort unit; majority says the cognition-increasing allele → LOWER KIFC2 |
| brainSCOPE | 39 credible variants at L65265, **0 tested** (none in the brainSCOPE SNP lists); no single-cell direction |
| Expression | GTEx adult brain median 95.13 TPM; developmental class ADULT_DYNAMIC |
| Perturbation | P5 (none); rare-coding rows none; LOEUF 1.267 (LoF-tolerant) |
| Leave-one-class-out | **V2G_SUPPORTED_WEAK_LOCUS**. Losing either class removes the MODERATE call |
| Ranks | B causal-gene 1; E research priority 3; A locus 22; C direction 13; D perturbation 36 |

## 3. Three questions, kept separate

- **A. Is KIFC2 a causal cognition gene? Not supported.** Only V2G evidence exists: one eQTL cohort and two chromatin links. There is no human perturbation evidence (P5). The mouse knockout is normal (Yang 2001).
- **B. Is it a natural high-cognition gene? Not supported (weak).** The locus is L3: concordant but weak outside UKB (log10BF 0.38, z 1.67). The gene-level direction is unresolved.
- **C. Is it adult-modifiable? Not testable at present.** The adult direction rests on one ROSMAP row. Expression is adult-dynamic and high, but there is no adult perturbation data.

## 4. Causal hypothesis chain

credible variant (rs2291133 / rs112422823; SuSiE PIP max 0.15 at rs750472) —[INFERRED: the PIP is spread over 39 variants, and the two E2G variants are not the top-PIP variants]→
brain enhancer element —[EVIDENCED, one method: ENCODE-rE2G scores 0.85 and 0.41]→
KIFC2 transcription —[EVIDENCED, weak: one ROSMAP coloc; FOCUS not run]→
cell type —[MISSING: brainSCOPE did not test these variants]→
direction (cognition allele → lower KIFC2) —[INFERRED: 1 row, UNRESOLVED]→
cognition —[MISSING: no human or animal perturbation linking KIFC2 dosage to cognition]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 9115736 (Saito 1997, Neuron) | KIFC2 is a neuron-specific C-terminal kinesin that moves multivesicular-body-like organelles in dendrites | MECHANISTIC_ONLY | Rodent localisation and biochemistry. Makes KIFC2 neuronally plausible but says nothing about cognition |
| PMID 11259594; doi:10.1128/MCB.21.7.2463-2466.2001 (Yang 2001) | Kifc2−/− mice are viable and fertile, with apparently normal neural development | CONTRADICTING | The only germline knockout. Its conclusion that KIFC2 is dispensable for normal neural development and behaviour relied on gross observation, not cognitive testing, so this is weak contradiction |
| PMID 32294442; doi:10.1016/j.celrep.2020.03.083 (Szczurkowska 2020) | KifC2 knockdown blocks the dendritic cGMP rise and disrupts apical dendrite development | MECHANISTIC_ONLY | In utero knockdown, so developmental. It conflicts partly with the normal knockout (acute knockdown vs germline compensation) |
| PMID 42511647; doi:10.3390/ijms27146304 (Hu 2026) | In chronic-pain mice, microglial CX3CL1→p38/NF-κB drives KIFC2 up, IL-17 exosomes, and synaptic loss / memory deficit | MECHANISTIC_ONLY | Direction matches our weak majority (lower KIFC2 goes with better cognition). But it is microglia-specific, a disease model, a single unreplicated study in an MDPI journal. It must not be counted as support |
| PMIDs 37716704, 40299549, 38658471, 37904433 | KIFC2 overexpression promotes prostate/breast/colon cancer (p65, CDK4) | DISEASE_ONLY | Cancer biology, useful only as a safety context. These studies do not share data with ours |
| Open Targets 26.06 (our `opentargets_refresh.csv`) | L2G prefers KIFC2, but most credible sets rank ZFTRAF1 first | CONTRADICTING (alternative gene) | Same GWAS inputs as ours: **NON-INDEPENDENT** of our V2G. It flags that the gene assignment is positional |
| Our matrix: ZFTRAF1 row | ZFTRAF1 has a QTL class backed by **2** coloc rows (KIFC2 has 1) and is labelled LIKELY_QTL_PASSENGER | CONTRADICTING (internal) | On eQTL evidence alone ZFTRAF1 ≥ KIFC2. KIFC2 wins only through the ENHANCER_LINK class |
| OMIM *615216 | No KIFC2 disease phenotype | — | No Mendelian anchor |

Independence: we found no independent human-genetic support for KIFC2 in cognition. The E2G links and the L2G score draw on the same Davies/Open Targets credible sets.

## 6. Modifiability characterisation (facts only)

- Protein: kinesin-14 family minus-end-directed microtubule motor. Cytoplasmic/cytoskeletal and nucleoplasmic, not extracellular or membrane.
- Structure: no ligand-bound structure recorded ("none recorded"). There is an AlphaFold model only. The motor domain has an ATPase site, a class that has been drugged in mitotic kinesins (e.g. KIF11), but none of that work involves KIFC2.
- Tractability (Open Targets): small molecule none, antibody none, PROTAC "Half-life Data" only.
- Known modulators, probes or clinical programmes: none found. ChEMBL has no KIFC2 bioactivity in this search, and there are 0 high-quality probes and 0 clinical candidates.
- Endogenous regulators: Rab4 regulates KIFC2 activity on endocytic vesicles (PMID 15181154). In one microglial study it is induced by NF-κB (PMID 42511647).

## 7. Pleiotropy and safety

LOEUF 1.267: LoF-tolerant in humans, with no Mendelian disease. The knockout mouse is viable. Cancer literature links overexpression to tumour progression, so any "increase" direction would carry an oncological context. The 8q24.3 locus also contains RECQL4 (Rothmund–Thomson/RAPADILINO), FOXH1 and other genes, so locus pleiotropy cannot be attributed to KIFC2.

## 8. Largest contradiction

The MODERATE class depends on two chromatin links plus one eQTL cohort at a gene-dense locus. Open Targets' per-credible-set majority favours ZFTRAF1, and leave-one-class-out drops KIFC2 to V2G_SUPPORTED_WEAK_LOCUS. The only in-vivo loss-of-function (Yang 2001) shows no neural phenotype.

## 9. Missing arrow and single best next computation

Missing: variant → KIFC2 in a specific brain cell type, with a direction replicated in ≥3 cohort units.
**Next computation:** a locus-level colocalisation of L65265 against every available adult-brain eQTL resource (eQTL Catalogue GTEx brain, CommonMind, ROSMAP, plus MetaBrain summary statistics if accessible), run jointly for KIFC2, ZFTRAF1, FOXH1, PPP1R16A and RECQL4. Report per-gene PP.H4 and the sign of the aligned effect. This tests whether the single ROSMAP KIFC2 coloc replicates and whether ZFTRAF1 colocalises better.
