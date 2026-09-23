# RPS26 — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**V2G_SUPPORTED_WEAK_LOCUS (locus L319, stratum L4_DISCORDANT).** Within this locus, RPS26 has the best gene-level evidence in our
matrix: FOCUS PIP 0.994, 30 concordant bulk colocs across 3 cohorts, and single-cell eQTLs in 8 brainSCOPE cell types, all pointing
the same way. But the association does not replicate outside UKB (aligned z −0.83). The RPS26 rs1131017 eQTL is also one of the
strongest and most promiscuous cis-eQTLs in the genome. It colocalises with type 1 diabetes, PCOS, ADHD, autoimmune disease and
dozens of other traits. Strong colocalisation here is expected under pleiotropy and says little about cognition.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L319 (MAGMA label ERBB3; 12q13.2), stratum **L4_DISCORDANT**, log10BF_independent **−0.3451**, locus rank 134 (64–140), gc_aligned_z **−0.8346**, panels A;C |
| V2G classes | ENHANCER_LINK (1) + QTL (3); n_classes 2. Other genes with classes: ERBB3, SUOX (max 1) |
| Enhancer link | ENCODE-rE2G brain: rs1131017 → RPS26, score 0.455 |
| QTL | 30 rows (Open Targets Sprint 3; GTEx ×26, CommonMind ×2, ROSMAP ×2); 15 pooled pairs; agreement 1.0 |
| FOCUS (primary) | **RPS26 0.994**; SUOX 0.01. Other configs: GTEx v8 EUR cortex RPS26 0.701 (cv_r2 0.67); accumbens ~0.69; lead rs772921 (Davies z 6.46) |
| Open Targets L2G 26.06 | Current **SUOX 0.9143** (changed from RPS26); second RPS26 0.7007; rank-1 majority RPS26 (0.462, 13 credible sets); top SHAP **pQtlColocClppMaximum** (QTL). Flag CHANGED_ASSIGNMENT. In the feature table, SUOX pQTL-coloc H4 reaches 0.95, while RPS26 pQTL features are 0 (likely unmeasured). Both genes have eQTL-coloc H4 ≈ 0.99 |
| Direction | **D2 / DIRECTION_RESOLVED**: cognition-increasing allele → HIGHER RPS26 (CommonMind, GTEx, ROSMAP) |
| brainSCOPE | 16/16 credible variants tested; RPS26 significant and HIGHER in Chandelier/Pvalb, L2/3 IT, L4 IT, L5 IT, L6 IT, Lamp5, Oligo, Vip (eQTL lead in the GWAS credible set; best-hit r² ≈ 0.72 with the GWAS lead). L6 CT and Sst are also significant, with moderate LD only. Not significant: Astro, Micro, OPC, PC, L5/6 NP, L6b, Lamp5.Lhx6. Bulk and cell-type directions AGREE |
| Expression | GTEx brain median 114.1 TPM; MIXED |
| Perturbation | P5; LOEUF **0.32** (constrained) |
| Leave-one-class-out | V2G_SUPPORTED_WEAK_LOCUS (unchanged) |
| Ranks | B 21; E 14; A **134**; C **1**; D 36 |

## 3. Three questions, kept separate

- **A. Is RPS26 a causal cognition gene? Not supported.** Human LoF causes Diamond–Blackfan anaemia (DBA10), which is not a cognitive phenotype. There is no cognitive perturbation evidence.
- **B. Is it a natural high-cognition gene? Not supported.** The locus is discordant in the UKB-free replication (z −0.83, log10BF −0.35).
- **C. Is it adult-modifiable? The adult direction is robust, but the association it would modify is not credible.** The eQTL is real and cell-type-broad. What is doubtful is the cognition association.

## 4. Causal hypothesis chain

rs1131017 (RPS26 5'UTR/promoter) and LD block —[EVIDENCED: FOCUS 0.994; eQTL lead inside GWAS credible set]→
promoter/5'UTR element —[EVIDENCED: rE2G 0.455; allele-specific translation (Li 2013)]→
RPS26 expression (higher) —[EVIDENCED: 30 bulk rows + 8 single-cell types, concordant]→
cell type —[EVIDENCED but non-specific: neurons and oligodendrocytes alike, consistent with a ubiquitous housekeeping eQTL]→
direction —[EVIDENCED]→
cognition —[**CONTRADICTED at the association level**: no replication outside UKB. No mechanism links RPS26 dosage to cognition]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 38812329; doi:10.31083/j.fbl2905185 (Ryu 2024) | Of 4,007 GWAS-signal/eQTL pairs involving RNA-polymerase or ribosomal-protein genes, 83.4% involve RP genes, and **RPS26 alone accounts for 32.9%**, across all tissues | CONTRADICTING (specificity) | Direct evidence that RPS26 coloc is a pleiotropic "magnet". Coloc with cognition is weak evidence of trait-specific causality |
| PMID 23900168; doi:10.1038/ncomms3260 (Li 2013) | rs1131017 in the RPS26 5'UTR changes ribosomal loading and protein level; it is in high LD with the 12q13 T1D locus | MECHANISTIC_ONLY | Defines the functional variant class; immune context |
| PMID 38453145; doi:10.1093/hmg/ddae024 (Michalek 2024) | Multi-ancestry T1D GWAS: IKZF4–RPS26–ERBB3 genome-wide significant | DISEASE_ONLY (pleiotropy) | Same haplotype, autoimmune trait |
| PMID 28248954; doi:10.1371/journal.pgen.1006643 (Kasela 2017) | The rs1131017 region is a trans-regulatory locus in CD4+/CD8+ T cells | MECHANISTIC_ONLY | Immune trans effects |
| PMID 37072791; doi:10.1186/s13059-023-02897-x (Li 2023) | rs1131017 is a co-eQTL that alters RPS26 co-expression with ribosomal and T-cell activation genes | MECHANISTIC_ONLY | Single-cell immune |
| PMID 33664499; doi:10.1038/s41431-021-00835-8 (Censin 2021) | PCOS signals colocalise with ERBB3, IKZF4, RPS26 and SUOX | NON-INDEPENDENT (pleiotropy) | Same eQTL panels; shows several genes are co-nominated |
| PMIDs 39510315, 40739630 (2024–25) | ADHD TWAS (fetal brain / iPSC neurons) nominates RPS26 | NON-INDEPENDENT | FUSION weights from overlapping eQTL panels; psychiatric, not cognition |
| PMID 42386713; doi:10.1038/s41398-026-04175-3 (Yu 2026) | Cognition–autoimmune pleiotropy SMR nominates RPS26, ERBB3, SH2B1, SULT1A1 and others | NON-INDEPENDENT | Cognitive GWAS inputs likely overlap UKB/Davies. Supports "pleiotropic immune locus" more than a cognition gene |
| PMID 20116044; doi:10.1016/j.ajhg.2009.12.015 (Doherty 2010) | Heterozygous RPS26 mutations cause Diamond–Blackfan anaemia | DISEASE_ONLY | Haploinsufficiency → erythroid failure, craniofacial and growth defects |
| PMID 28759050; doi:10.1038/nsmb.3442 (Ferretti 2017) | Rps26 recognises Kozak −4 elements. Rps26-deficient ribosomes preferentially translate stress-response mRNAs | MECHANISTIC_ONLY | Yeast. Suggests dosage can shift translation specificity |

Shared data: every coloc/TWAS/SMR row (Ryu, Censin, ADHD TWAS, Yu, and our 30 QTL rows) reuses GTEx-era eQTL. Together they are one eQTL lineage. Paper count here measures pleiotropy, not independent support.

## 6. Modifiability characterisation (facts only)

- Protein: eS26, a 40S small-subunit ribosomal protein near the mRNA exit channel and E-site, cytosolic and ER-associated. Its "ligand" is mRNA/rRNA context (Kozak −4 recognition).
- Tractability: Open Targets "Approved Drug; Structure with Ligand; High-Quality Ligand", clinical candidates 5. As the packet notes, these reflect whole-ribosome binders (e.g. aminoglycoside/translation-inhibitor chemotypes in ribosome structures), **not** RPS26-selective agents. We found no RPS26-selective modulator. 0 high-quality probes.
- Not extracellular.

## 7. Pleiotropy and safety

LOEUF 0.32 (constrained). Haploinsufficiency causes DBA (bone-marrow failure, malformations, cancer predisposition). The eQTL
haplotype is associated with T1D, other autoimmune disease, PCOS, pre-eclampsia, diabetic complications and ADHD. Any "raise RPS26" direction would sit in a haematological and immune pleiotropy context.

## 8. Largest contradiction

This is the strongest gene-level mechanism in the batch (a fine-mapped eQTL with a cell-type-concordant direction) attached to a locus that **fails replication outside UKB** (z −0.83). And the eQTL is the most promiscuous RP eQTL documented (32.9% of RP GWAS–eQTL pairs). The combination is what a pleiotropic, possibly UKB-specific association would look like.

## 9. Missing arrow and single best next computation

Missing: a cognition association at L319 that is independent of UKB.
**Next computation:** run a PheWAS-style "colocalisation-promiscuity" null for L319. Colocalise the RPS26 brain eQTL against a panel of ≥50 non-cognitive GWAS (Open Targets credible sets) and compute the fraction with PP.H4 ≥ 0.8. Then rerun coloc of the RPS26 eQTL against the **UKB-free** cognition replication statistics alone. If the UKB-free PP.H4 is low while many unrelated traits colocalise, RPS26 should be recorded as a pleiotropic passenger for cognition.
