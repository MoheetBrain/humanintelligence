# Gene cards — Top 50 adult-modifiable candidates

> **CORRECTED 2026-09-23 (Sprint 3.1, C9).** "Adult-modifiable" in this file's title and in `TOP50_ADULT_MODIFIABLE_GENES.csv` / `red_team_top50_adult.csv` means only **ADULT-EXPRESSION-COMPATIBLE** (adult-brain expressed; not prenatal-dominant in BrainSpan). Expression is not modifiability. Tiered evidence: `reports/sprint3_1/adult_evidence_hierarchy.csv` (ADULT_EXPRESSED / ADULT_EXPRESSION_DYNAMIC / ADULT_FUNCTIONAL_EVIDENCE / ADULT_CAUSAL_EVIDENCE / ADULT_INTERVENTION_READY; no gene reaches ADULT_CAUSAL_EVIDENCE). File names are kept for provenance.

Generated 2026-09-22T20:33:31Z by `pipelines/gene_tournament/build_red_team_and_cards.py`. Every answer is drawn from a Sprint-3 artefact; an unanswerable field says so. Nothing here is a target nomination, a direction of benefit, or a reason to intervene. The chemistry gate is closed.

## 1. ERBB3  ·  rank interval 1-55  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 2.99e-08 (Davies 2018, N=282,014); Savage P = 2.8e-06; 3 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** fluid_reasoning, general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = 0.24, P = 0.4 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Group enriched: committed oligodendrocyte precursor: 315.9;oligodendrocyte: 330.4;oligodendrocyte precursor cell: 87.7 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: ERBB3|RAB5B|RPS26|SUOX
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 2. NEGR1  ·  rank interval 1-126  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.49e-16 (Davies 2018, N=282,014); Savage P = 3.0e-18; 6 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 0.97, P = 0.17 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs66495454 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENSG00000172260.15_1_71935079_71935311
- **Direction?** UNRESOLVED: 4 strong gene-level brain QTL colocs, 75% sign agreement — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 3. DDN  ·  rank interval 1-140  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.22e-11 (Davies 2018, N=282,014); Savage P = 4.5e-14; 4 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition, processing_speed
- **Extreme-tail evidence?** Z = 1.58, P = 0.057 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: eccentric medium spiny neuron: 27.2 (HPA v25.1, expression specificity only)
- **Module?** M04
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: DDN|KMT2D|PRKAG1|RHEBL1|KCNH3
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 4. OGA  ·  rank interval 2-513  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 5.79e-11 (Davies 2018, N=282,014); Savage P = 1.3e-13; 4 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** executive_function, general_cognition
- **Extreme-tail evidence?** Z = 1.86, P = 0.031 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M07
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** LD block shared with: OGA|KCNIP2|PSD|HPS6|NPM3|FBXL15|CUEDC2|ATP5MK|NFKB2
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 5. STAB1  ·  rank interval 3-626  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 4.12e-13 (Davies 2018, N=282,014); Savage P = 2.5e-10; 4 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** executive_function, general_cognition, memory
- **Extreme-tail evidence?** Z = 1.42, P = 0.077 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs7639267 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENST00000481626
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** neocortex
- **Cell type?** Cell type enriched: central nervous system macrophage: 88.0 (HPA v25.1, expression specificity only)
- **Module?** M09
- **Developmental / adult?** DEVELOPMENTAL
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** LD block shared with: STAB1|TWF2|UQCC5|GNL3|GLT8D1|MUSTN1|SPCS1|PPM1M; developmental class DEVELOPMENTAL
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 6. SYT1  ·  rank interval 1-112  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 3.29e-07 (Davies 2018, N=282,014); Savage P = 1.6e-03; 4 strict cohort unit(s); rank carried most by *coloc*.
- **Which phenotype?** fluid_reasoning, general_cognition
- **Extreme-tail evidence?** Z = 0.74, P = 0.23 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs62741560 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENST00000552624
- **Direction?** UNRESOLVED: 15 strong gene-level brain QTL colocs, 60% sign agreement — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:SYT1: HI score 1; TS score 0
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 6. NSF  ·  rank interval 1-129  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 6.41e-09 (Davies 2018, N=282,014); Savage P = 3.4e-06; 3 strict cohort unit(s); rank carried most by *coloc*.
- **Which phenotype?** executive_function, general_cognition, processing_speed
- **Extreme-tail evidence?** Z = 0.97, P = 0.17 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs2137113 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENSG00000073969
- **Direction?** UNRESOLVED: 1 strong gene-level brain QTL colocs, 100% sign agreement — never read as 'activate the gene'
- **Brain region?** neocortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: NSF|WNT3|PLEKHM1|ARHGAP27
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 8. PDE1C  ·  rank interval 1-222  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 7.32e-05 (Davies 2018, N=282,014); Savage P = 1.1e-03; 6 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 0.26, P = 0.4 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: oligodendrocyte: 1534.9 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 9. ATXN2L  ·  rank interval 4-156  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 9.10e-15 (Davies 2018, N=282,014); Savage P = 1.6e-14; 5 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** executive_function, fluid_reasoning, general_cognition
- **Extreme-tail evidence?** Z = 2.07, P = 0.019 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs12928404 colocalised
- **Adult brain molecular evidence?** moderate — sqtl: 16:28835187:28835549:clu_22535_+
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** cerebellum
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M08
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** LD block shared with: ATXN2L|RABEP2|SH2B1|TUFM|NFATC2IP|NUPR1|CLN3|SULT1A1|SPNS1|LAT
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 10. BSN  ·  rank interval 3-106  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 7.70e-14 (Davies 2018, N=282,014); Savage P = 5.0e-10; 5 strict cohort unit(s); rank carried most by *replication*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 3.10, P = 0.00097 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: BSN|RBM6
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 11. GRIA4  ·  rank interval 9-188  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.28e-05 (Davies 2018, N=282,014); Savage P = 4.8e-08; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 1.41, P = 0.079 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 12. COL16A1  ·  rank interval 4-360  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 5.56e-12 (Davies 2018, N=282,014); Savage P = 8.7e-09; 3 strict cohort unit(s); rank carried most by *coloc*.
- **Which phenotype?** executive_function, fluid_reasoning, general_cognition
- **Extreme-tail evidence?** Z = -0.28, P = 0.61 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs1474182 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENSG00000084636.18_1_31669811_31670555
- **Direction?** UNRESOLVED: 2 strong gene-level brain QTL colocs, 50% sign agreement — never read as 'activate the gene'
- **Brain region?** cerebellum
- **Cell type?** Cell type enhanced: astrocyte: 180.3;committed oligodendrocyte precursor: 201.0 (HPA v25.1, expression specificity only)
- **Module?** M05
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:COL16A1: HI score 40; TS score 0
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** none recorded
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 13. PEF1  ·  rank interval 5-327  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 2.75e-14 (Davies 2018, N=282,014); Savage P = 1.0e-11; 5 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** executive_function, general_cognition
- **Extreme-tail evidence?** Z = 0.32, P = 0.38 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs2271927 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENSG00000162517
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M03
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: PEF1|HCRTR1|TINAGL1
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 14. SHANK3  ·  rank interval 4-190  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 1.21e-06 (Davies 2018, N=282,014); Savage P = 1.5e-06; 3 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 2.63, P = 0.0043 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: endothelial cell: 303.3 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:SHANK3: HI score 3; TS score 0
- **Human safety?** ClinGen haploinsufficient (HI=3): loss causes disorder
- **Strongest contradiction?** 0 confirmed UKB-free units; significance depends on 10 kb window
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 14. KCNJ3  ·  rank interval 4-116  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 6.03e-12 (Davies 2018, N=282,014); Savage P = 3.4e-08; 4 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** executive_function, general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = -0.26, P = 0.6 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 16. GFAP  ·  rank interval 1-1351  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 3.88e-03 (Davies 2018, N=282,014); Savage P = 5.0e-04; 1 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 1.35, P = 0.089 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enriched: astrocyte: 1723.3 (HPA v25.1, expression specificity only)
- **Module?** not in FDR<0.01 module set
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: GFAP|C1QL1|RUNDC3A|GRN; rank carried by 'adult_modifiability' (LODO worst 996)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 17. RIMS2  ·  rank interval 18-194  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.64e-05 (Davies 2018, N=282,014); Savage P = 1.6e-07; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 0.61, P = 0.27 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 18. TRIM37  ·  rank interval 10-389  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 9.99e-13 (Davies 2018, N=282,014); Savage P = 4.4e-13; 3 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 1.42, P = 0.078 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M03
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:TRIM37: HI score 30; TS score 0
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: TRIM37|PPM1E
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 19. CADM2  ·  rank interval 6-206  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.02e-07 (Davies 2018, N=282,014); Savage P = 1.1e-07; 6 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = 2.10, P = 0.018 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 20. CPD  ·  rank interval 19-224  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 4.75e-06 (Davies 2018, N=282,014); Savage P = 1.1e-06; 1 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** mathematical_cognition
- **Extreme-tail evidence?** Z = 2.26, P = 0.012 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: endothelial cell: 443.5 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: CPD|GOSR1
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 21. PITPNM2  ·  rank interval 14-252  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 3.59e-06 (Davies 2018, N=282,014); Savage P = 5.7e-06; 2 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 3.08, P = 0.0011 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: choroid plexus epithelial cell: 289.5 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 22. FOXO3  ·  rank interval 1-298  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 6.75e-10 (Davies 2018, N=282,014); Savage P = 6.1e-16; 7 strict cohort unit(s); rank carried most by *replication*.
- **Which phenotype?** executive_function, fluid_reasoning, general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = 1.43, P = 0.077 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M04
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** rank carried by 'replication' (LODO worst 207)
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 23. SEPTIN4  ·  rank interval 5-454  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 1.97e-13 (Davies 2018, N=282,014); Savage P = 3.6e-13; 1 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 1.17, P = 0.12 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs8070135 colocalised
- **Adult brain molecular evidence?** moderate — sqtl: 17:58526313:58526932:clu_41248_-
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** Ammon's horn
- **Cell type?** Group enriched: Bergmann glia: 991.8;oligodendrocyte: 296.5 (HPA v25.1, expression specificity only)
- **Module?** M09
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: SEPTIN4|MTMR4|RNF43|SUPT4H1|TSPOAP1; rank carried by 'direct' (LODO worst 254)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 24. BAIAP2  ·  rank interval 11-222  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 4.17e-06 (Davies 2018, N=282,014); Savage P = 1.3e-06; 3 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition, mathematical_cognition, memory
- **Extreme-tail evidence?** Z = -0.31, P = 0.62 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: BAIAP2|LMTK1
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 25. SYT7  ·  rank interval 15-228  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 4.42e-06 (Davies 2018, N=282,014); Savage P = 4.9e-05; 2 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 0.60, P = 0.28 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 26. PLEKHA1  ·  rank interval 6-397  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 2.63e-04 (Davies 2018, N=282,014); Savage P = 6.1e-05; 2 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** executive_function, general_cognition
- **Extreme-tail evidence?** Z = -2.10, P = 0.98 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** none recorded
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 27. DTNBP1  ·  rank interval 27-293  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 2.11e-05 (Davies 2018, N=282,014); Savage P = 1.4e-05; 1 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = -1.50, P = 0.93 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 28. MEF2C  ·  rank interval 3-589  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.19e-12 (Davies 2018, N=282,014); Savage P = 1.6e-12; 7 strict cohort unit(s); rank carried most by *replication*.
- **Which phenotype?** executive_function, fluid_reasoning, general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 1.92, P = 0.027 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs34316 colocalised
- **Adult brain molecular evidence?** weak — eqtl: ENST00000515715
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Cell type enhanced: central nervous system macrophage: 3465.1 (HPA v25.1, expression specificity only)
- **Module?** M03
- **Developmental / adult?** DEVELOPMENTAL
- **Known perturbations?** CLINGEN:MEF2C: HI score 3; TS score 1
- **Human safety?** ClinGen haploinsufficient (HI=3): loss causes disorder
- **Strongest contradiction?** developmental class DEVELOPMENTAL; rank carried by 'replication' (LODO worst 287)
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 29. EEA1  ·  rank interval 25-218  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 3.20e-06 (Davies 2018, N=282,014); Savage P = 6.3e-08; 3 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 2.26, P = 0.012 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 30. ANKS1B  ·  rank interval 20-258  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.06e-06 (Davies 2018, N=282,014); Savage P = 1.6e-05; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** executive_function, general_cognition
- **Extreme-tail evidence?** Z = -0.16, P = 0.56 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:ANKS1B: HI score 1; TS score Not yet evaluated
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 32. SPARCL1  ·  rank interval 2-1550  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 5.50e-03 (Davies 2018, N=282,014); Savage P = 1.7e-01; 0 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general cognition (MAGMA) only
- **Extreme-tail evidence?** Z = 1.07, P = 0.14 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: astrocyte: 1412.7 (HPA v25.1, expression specificity only)
- **Module?** not in FDR<0.01 module set
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; rank carried by 'adult_modifiability' (LODO worst 1547)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 33. FAM43B  ·  rank interval 23-273  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.36e-09 (Davies 2018, N=282,014); Savage P = 4.1e-05; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = -0.23, P = 0.59 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: FAM43B|CAMK2N1
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 34. SCN2A  ·  rank interval 17-234  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 2.13e-06 (Davies 2018, N=282,014); Savage P = 2.4e-05; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 0.48, P = 0.32 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** EA_proxy_only
- **Direction?** no brain QTL colocalisation with a DIRECT cognition GWAS — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** CLINGEN:SCN2A: HI score 3; TS score 0
- **Human safety?** ClinGen haploinsufficient (HI=3): loss causes disorder
- **Strongest contradiction?** 0 confirmed UKB-free units; significance depends on 10 kb window; no direct-cognition brain colocalisation
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 35. UBA7  ·  rank interval 2-929  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 4.50e-15 (Davies 2018, N=282,014); Savage P = 5.0e-10; 0 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** general cognition (MAGMA) only
- **Extreme-tail evidence?** Z = 2.09, P = 0.018 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: central nervous system macrophage: 45.7 (HPA v25.1, expression specificity only)
- **Module?** M03
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: UBA7|IP6K1|RHOA|NCKIPSD|CAMKV|GPX1|AMT|TCTA|NICN1|DAG1|GMPPB|APEH|USP4|MON1A|RBM5|RNF123|NDUFAF3|KLHDC8B|UQCRC1|SLC25A20; rank carried by 'direct' (LODO worst 809)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 35. CKB  ·  rank interval 2-413  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 2.44e-06 (Davies 2018, N=282,014); Savage P = 1.9e-10; 2 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 0.58, P = 0.28 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M02
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: CKB|TRMT61A|BAG5; rank carried by 'adult_modifiability' (LODO worst 373)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 37. RTN1  ·  rank interval 36-273  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 1.43e-08 (Davies 2018, N=282,014); Savage P = 5.9e-09; 1 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 2.65, P = 0.0041 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 38. APOE  ·  rank interval 1-1584  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 6.53e-03 (Davies 2018, N=282,014); Savage P = 1.8e-02; 2 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** executive_function, general_cognition, memory, processing_speed
- **Extreme-tail evidence?** Z = 0.49, P = 0.31 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: astrocyte: 1133.9;Bergmann glia: 1030.8;central nervous system macrophage: 624.3;vascular associated smooth muscle cell: 882.6 (HPA v25.1, expression specificity only)
- **Module?** not in FDR<0.01 module set
- **Developmental / adult?** DEVELOPMENTAL
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; developmental class DEVELOPMENTAL; rank carried by 'finemap' (LODO worst 1115)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 39. CACNA1I  ·  rank interval 18-282  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 7.31e-09 (Davies 2018, N=282,014); Savage P = 3.2e-09; 3 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** fluid_reasoning, general_cognition, processing_speed
- **Extreme-tail evidence?** Z = 0.41, P = 0.34 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 40. SORT1  ·  rank interval 7-236  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 1.60e-10 (Davies 2018, N=282,014); Savage P = 8.0e-10; 1 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = -1.01, P = 0.84 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: oligodendrocyte: 865.7 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 41. MGAT3  ·  rank interval 6-533  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 5.00e-10 (Davies 2018, N=282,014); Savage P = 7.3e-12; 4 strict cohort unit(s); rank carried most by *replication*.
- **Which phenotype?** general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = 1.05, P = 0.15 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs760713 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENSG00000128268.12_22_39477513_39477739
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M05
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: MGAT3|SYNGR1|ATF4|RPS19BP1|TAB1; rank carried by 'replication' (LODO worst 178)
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 41. DHRS11  ·  rank interval 6-306  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 5.00e-10 (Davies 2018, N=282,014); Savage P = 7.4e-09; 4 strict cohort unit(s); rank carried most by *coloc*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = 2.36, P = 0.0092 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs2285640 colocalised
- **Adult brain molecular evidence?** strong — eqtl: ENSG00000278535.5_17_36599694_36599763
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** cerebellum
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M02
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: DHRS11|GGNBP2|MYO19|ZNHIT3
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); test direction in a second brain QTL dataset

## 43. AKAP6  ·  rank interval 9-265  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.20e-06 (Davies 2018, N=282,014); Savage P = 1.2e-06; 6 strict cohort unit(s); rank carried most by *replication*.
- **Which phenotype?** executive_function, fluid_reasoning, general_cognition, mathematical_cognition, processing_speed
- **Extreme-tail evidence?** Z = 3.17, P = 0.00076 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** significance depends on 10 kb window
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 45. PTPRT  ·  rank interval 19-294  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.92e-08 (Davies 2018, N=282,014); Savage P = 6.3e-10; 2 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 0.52, P = 0.3 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Cell type enhanced: LAMP5-LHX6 and Chandelier: 2036.9 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units; rank carried by 'module' (LODO worst 157)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 46. SNCB  ·  rank interval 4-1551  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 7.19e-04 (Davies 2018, N=282,014); Savage P = 1.7e-01; 0 strict cohort unit(s); rank carried most by *adult_modifiability*.
- **Which phenotype?** general cognition (MAGMA) only
- **Extreme-tail evidence?** Z = 0.29, P = 0.39 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** not in FDR<0.01 module set
- **Developmental / adult?** ADULT_DYNAMIC
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; rank carried by 'adult_modifiability' (LODO worst 1368)
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 47. SEPTIN3  ·  rank interval 14-866  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 4.17e-11 (Davies 2018, N=282,014); Savage P = 7.2e-09; 4 strict cohort unit(s); rank carried most by *direct*.
- **Which phenotype?** fluid_reasoning, general_cognition
- **Extreme-tail evidence?** Z = 1.74, P = 0.041 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M09
- **Developmental / adult?** DEVELOPMENTAL
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: SEPTIN3|NDUFA6|L3MBTL2|DESI1|CHADL|CCDC134; developmental class DEVELOPMENTAL; rank carried by 'direct' (LODO worst 379)
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 48. NKAIN2  ·  rank interval 12-1053  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 1.84e-06 (Davies 2018, N=282,014); Savage P = 3.9e-06; 3 strict cohort unit(s); rank carried most by *module*.
- **Which phenotype?** general_cognition, memory
- **Extreme-tail evidence?** Z = -0.61, P = 0.73 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** not resolved (no direct-cognition brain colocalisation with a shared variant)
- **Adult brain molecular evidence?** not queried
- **Direction?** unresolved — never read as 'activate the gene'
- **Brain region?** none from colocalisation
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** DEVELOPMENTAL
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; significance depends on 10 kb window; developmental class DEVELOPMENTAL; rank carried by 'module' (LODO worst 199)
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 50. GRM3  ·  rank interval 19-293  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 2.20e-05 (Davies 2018, N=282,014); Savage P = 3.1e-06; 2 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 1.98, P = 0.024 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs802456 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENST00000421579
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** caudate nucleus
- **Cell type?** Cell type enhanced: pericyte: 3059.1 (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 50. ADGRB1  ·  rank interval 19-268  ·  red team: **RETAINED_WITH_CAVEATS**

- **Why here?** MAGMA gene P = 1.60e-07 (Davies 2018, N=282,014); Savage P = 1.1e-07; 2 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** general_cognition, mathematical_cognition
- **Extreme-tail evidence?** Z = 1.22, P = 0.11 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs13279697 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENSG00000181790.12_8_142479488_142479692
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M01
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units
- **Next computation?** replication in a UKB-free cohort; SuSiE-coloc on eQTL Catalogue brain data

## 50. NOVA1  ·  rank interval 19-256  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 3.24e-07 (Davies 2018, N=282,014); Savage P = 5.7e-08; 4 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = -0.19, P = 0.57 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs1245214 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENSG00000139910.20_14_26470118_26470490
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** dorsolateral prefrontal cortex
- **Cell type?** Cell type enhanced: oligodendrocyte precursor cell: 3101.9 (HPA v25.1, expression specificity only)
- **Module?** M08
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** LoF-intolerant (pLI>=0.9)
- **Strongest contradiction?** 0 confirmed UKB-free units; significance depends on 10 kb window
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data

## 50. ATXN7L2  ·  rank interval 19-264  ·  red team: **DOWNGRADED**

- **Why here?** MAGMA gene P = 4.09e-10 (Davies 2018, N=282,014); Savage P = 1.3e-10; 3 strict cohort unit(s); rank carried most by *finemap*.
- **Which phenotype?** general_cognition
- **Extreme-tail evidence?** Z = -1.33, P = 0.91 (Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)
- **Causal variant?** fine-mapped variant rs407102 colocalised
- **Adult brain molecular evidence?** moderate — eqtl: ENST00000463678
- **Direction?** UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation — never read as 'activate the gene'
- **Brain region?** cerebellum
- **Cell type?** Low cell type specificity (HPA v25.1, expression specificity only)
- **Module?** M04
- **Developmental / adult?** MIXED
- **Known perturbations?** none in the positive-perturbation table
- **Human safety?** no ClinGen HI=3 / pLI>=0.9 flag
- **Strongest contradiction?** 0 confirmed UKB-free units; LD block shared with: ATXN7L2|CYB561D1|AMIGO1|PSMA5|AMPD2|GSTM4
- **Next computation?** within-sibship direction check (needs OpenGWAS registration); SuSiE-coloc on eQTL Catalogue brain data
