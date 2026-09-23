# SLC39A8 (ZIP8) / rs13107325 (p.Ala391Thr): literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `LOCUS_HIGH_GENE_UNRESOLVED`. This is an EXPLICIT-INSPECTION dossier (brief Panel A / Q14), outside the frozen promotion rule.**
- Biologically, rs13107325 is the most convincing causal-variant-to-gene link in the batch:
  - a missense variant with PIP ≈ 1;
  - hypomorphic Mn/Zn transport in cell and knock-in mouse models;
  - a recessive LoF disease with intellectual disability.
- It is also one of the most pleiotropic variants in the human genome.
- Outside UK Biobank its cognition association is weak or contradicted:
  - GenLang: wrong sign, heterogeneous with Savage at p ≈ 0.005;
  - Zabaneh: z 0.08;
  - G&C: only z 1.91.
- It fails Genomic-SEM heterogeneity in the math-53 GWAS.
- It stays "gene plausible, cognition-specificity unproven".

## 2. Our computed evidence (packet and locus table; unchanged)

| Item | Value |
|---|---|
| Locus | L64116. Lead **rs13107325** (GRCh38 4:102267552 C>T; missense A391T). Davies effect allele **T**, davies_z **−8.332**, so the **cognition-increasing allele is C (Ala391, major; T frequency ≈ 0.065 in Savage)**. Tweedie z 7.444. Stratum L2, log10BF_independent 0.575, rank 11 (2–102). |
| Fine-mapping | SuSiE-Davies PIP 0.926 (CS size 2). OT credible-set PIP 0.68–1.00 across 7 cognition studies. CODING class 0.99997. |
| Independent lineages | gc_aligned_z **1.911** (G&C TMA, p ≈ 0.056). Gate B `G&C_SUPPORTED`, FDR 0.193. Zabaneh aligned z **0.077**. GenLang PIQ aligned z **−0.337** (PARTIAL_OVERLAP). |
| OT L2G 26.06 | SLC39A8 0.931, but top SHAP is **positional** (distance 0.53 vs coding 0.33). BANK1 second (0.056). |
| FOCUS | primary PIP 0.0. Sprint-4 direction `UNRESOLVED_NO_STRONG_COLOC` (0 rows). |
| BrainSCOPE | `VARIANT_NOT_TESTED` in all 17 core cell types |
| Math-53 audit | rs13107325 fails QSNP (P = 2.7e-15), with **opposite-sign effects on the two math indicators**. It is assigned MATH_PROXY_ONLY. |
| Perturbation stratum | P4 (DD/ID disease gene, DISEASE_ONLY) |
| Modifiability | Plasma-membrane and lysosomal Mn²⁺/Zn²⁺/Fe²⁺/Cd²⁺-bicarbonate symporter. No pocket or probes. OT safety liability "alcoholism". LOEUF 0.602. |

**Allele-direction and heterogeneity check I ran for this dossier (local sumstats; exploratory arithmetic, not a frozen test):**
- **Savage 2018:** T z −9.49, stdBeta −0.0526, which agrees with the Davies direction (T lowers).
- **GenLang PIQ:** T beta +0.0069 (SE 0.0205), p 0.74. If the Savage effect held, the expected z is −2.57; observed is +0.34. Heterogeneity z −2.80, **p 0.005**. This assumes both betas are on an SD scale, and the phenotypes differ (PIQ vs VNR-heavy g).
- **G&C TMA:** C beta −0.0071 (SE 0.0037), p 0.056. That is concordant (C faster).

## 3. Three separate questions

- **A. Causal cognition gene? NOT SUPPORTED for cognition specifically. The gene is supported as the causal gene for the variant.**
  - Variant → gene is strong (PIP ≈ 1, missense, functional hypomorph).
  - The recessive LoF disease includes ID with cerebellar atrophy (DISEASE_ONLY).
  - UKB rare variants were only nominally associated with poorer cognition (Smart 2025, not significant after correction).
- **B. Natural high-cognition gene? Locus moderately supported; heterogeneous outside UKB.**
  - In our data the common C (Ala391) allele is the cognition-increasing allele, and T (Thr391) lowers cognition. Smart 2025 independently confirms this direction in UKB (non-independent).
  - T is a derived allele, present essentially only in Europeans and under reported recent positive selection. It cannot be replicated in AFR/EAS.
- **C. Adult-modifiable? NOT TESTABLE.**
  - No adult-brain QTL or direction data (BrainSCOPE did not test the variant).
  - Adult Mn/Zn physiology is modifiable in principle, but no evidence links it to cognition in healthy adults.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| rs13107325 → ZIP8 A391T protein change | EVIDENCED | Missense, PIP ≈ 1 |
| A391T → reduced Mn (and Zn) uptake | EVIDENCED | Cell: loss of Mn-responsive surface accumulation (Nishito 2024). Knock-in mouse: lower blood, liver and kidney Mn (Sunuwar 2020). Human: lower blood Mn (Ng 2015). |
| Reduced Mn → Mn-dependent glycosyltransferases → N-glycan defect | EVIDENCED (mouse brain, human plasma) | Mealer 2022; Sunuwar 2020 |
| → Brain cell type | INFERRED | Knock-in mice show reduced cortical spine density (Li 2022). Tseng 2021 reports reduced NMDA/AMPA sEPSCs, BBB and immune effects. The expression site (endothelium/BBB vs neurons) is unresolved. |
| Direction T → lower cognition | EVIDENCED in UKB-heavy data | Davies; Savage; Smart 2025 |
| Direction outside UKB | CONTRADICTED/weak | GenLang wrong sign; Zabaneh ≈ 0; G&C nominal |
| → Cognition specifically (vs SCZ, BMI, Crohn's, BP pathways) | MISSING | Highly pleiotropic. Math QSNP failure. |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Davies 2018 Nat Commun, PMID 29844566; Savage 2018 Nat Genet, PMID 29942086 | rs13107325 genome-wide for cognition/intelligence | SUPPORTING (locus) | **[UKB-shared A]** |
| Smart 2025 AJMG-B, PMID 40530585, doi:10.1002/ajmg.b.33037 | The SCZ-risk T allele is associated with poorer cognition, FI and education in UKB, but **not with symptom severity or cognition within SCZ cohorts** (N = 1,232). Rare variants nominal. | NON-INDEPENDENT (UKB) + CONTRADICTING (null in SCZ cohorts, low power) | [A] |
| Park 2015 AJHG, PMID 26637979; Boycott 2015 AJHG, PMID 26637978 | Biallelic SLC39A8 LoF causes a type-II CDG with Mn deficiency, ID and cerebellar atrophy | DISEASE_ONLY | Independent of UKB. LoF direction agrees (less function, worse). |
| Sunuwar 2020 JCI Insight, PMID 32897876, doi:10.1172/jci.insight.140978 | A391T knock-in mouse is hypomorphic: lower Mn, colitis susceptibility, altered N-glycans. Ranked top-10 pleiotropic SNP. | MECHANISTIC_ONLY | |
| Mealer 2022 Mol Psychiatry, PMID 35260802, doi:10.1038/s41380-022-01490-1 | Knock-in alters brain protein N-glycosylation (region-specific) | MECHANISTIC_ONLY | |
| Li S 2022 Transl Psychiatry, PMID 36056013, doi:10.1038/s41398-022-02137-z | Knock-in: brain and blood Zn dysregulated, cortical spine density reduced. Full text (PMC9440106): **no behavioural or cognitive abnormalities** on open field, light-dark, elevated plus maze, novel object recognition, Y-maze, 3-chamber social approach or tail suspension (adult males). | CONTRADICTING (null cognitive phenotype) / MECHANISTIC | Key mouse null for cognition. Checked against the full text. |
| Tseng 2021 Transl Psychiatry, PMID 33608496 | A391T is LoF for Zn transport, reducing glutamatergic sEPSCs and BBB integrity | MECHANISTIC_ONLY | Pfizer authors |
| Nishito 2024 BBB, PMID 38821503 | A391T loses Mn-responsive surface accumulation, so Mn uptake falls | MECHANISTIC_ONLY | |
| Pickrell 2016 Nat Genet, PMID 27182965 | rs13107325 shared across many of 42 traits | NON-INDEPENDENT (pleiotropy) | |
| Li M 2016 Schizophr Bull, PMID 26006263 | T is derived, absent in Asians and Africans, under recent positive selection in Europeans (linked to BP and cold adaptation) | CONTRADICTING (ancestry-limited replication) | |
| Luo 2019 JAMA Psychiatry, PMID 30649180 | T is associated with putamen volume in adolescents (multi-cohort, including UKB) | MECHANISTIC_ONLY | Partly [A] |
| Hermann 2021 Front Genet, PMID 33790950 | rs13107325 is associated with 22 UKB brain-MRI phenotypes | NON-INDEPENDENT | [A] |
| Nakata 2020 PNAS, PMID 33139556 | A391T raises Crohn's risk through Mn and barrier defects | DISEASE_ONLY (pleiotropy) | |
| Tomar 2026 HGG Adv, PMID 40963256 | N-acetylglucosamine corrected the N-glycan and colitis phenotype in A391T mice | MECHANISTIC_ONLY | Gut model only |
| Our math-53 audit (`research/sprint5/math_audit.md`) | Fails QSNP. Opposite signs on self-rated math vs highest math class. | CONTRADICTING (single-factor action) | Internal |

## 6. Modifiability characterisation (facts only)

- **Protein:** a ZIP (SLC39) family metal-ion importer. It has 8 predicted TM helices and is an electroneutral M²⁺/(HCO₃⁻)₂ symporter (UniProt). It sits on the apical, basolateral and plasma membranes and on lysosomes, and is highly expressed in endothelium, lung and liver.
- **Structure:** no human ZIP8 experimental structure is recorded in our packet. Prokaryotic ZIP homolog (BbZIP) structures exist. I did not verify the TM position of A391.
- **Endogenous substrates:** Mn²⁺, Zn²⁺, Fe²⁺, Cd²⁺ (toxicant) and selenite.
- **Known modulators and probes:** none. OT small-molecule tractability is none; antibody tractability is positive (surface).
- **Disease-context facts:**
  - Mn and galactose supplementation have been used in SLC39A8-CDG (rare-disease clinical reports).
  - N-acetylglucosamine has been tested in A391T mice (gut).
  - None concerns cognition.

## 7. Pleiotropy and safety

- **Traits for the T allele (literature):** higher schizophrenia and Crohn's disease risk, higher BMI, lower blood Mn, altered HDL and lipids, lower blood pressure (hypotension in knock-in mice), scoliosis, alcohol-related traits, osteoarthritis, many brain-MRI traits, and gut microbiome composition.
- **Biallelic LoF:** a severe CDG.
- **Toxicology:** ZIP8 mediates cellular Cd uptake.
- **Dosage:** metal-transport dosage has disease consequences in both directions (Mn deficiency; Zn-mediated kidney disease, PNAS 2025, PMID 40956895).

## 8. Largest contradiction

- The variant-to-gene arrow is near-certain, but cognition-specificity is not established:
  - The most independent child-cognition lineage (GenLang) shows the opposite sign, heterogeneous with Savage at p ≈ 0.005.
  - The extreme-IQ sample (Zabaneh) shows nothing.
  - A391T knock-in mice showed no behavioural or cognitive abnormality on a 7-test battery (Li S 2022, full text).
  - The variant fails the single-factor test in the math GWAS.
- The UKB cognition signal could be mediated by, or confounded with, its other traits (BMI, SCZ liability, vascular/BP, SES), not by a direct neural cognitive mechanism.

## 9. Missing arrow and single best next computation

- **Missing arrow:** whether the rs13107325 effect on cognition is direct, or mediated by or shared with its pleiotropic traits, and whether it holds outside UKB.
- **Best next computation:**
  - Run a single-variant multivariable decomposition at rs13107325. Use allele-aligned summary effects on cognition (Davies, GenLang, G&C), SCZ (PGC3), BMI, SBP, HDL and blood Mn.
  - Fit a pleiotropy-aware test: a MR-PRESSO/MV-MR-style residual for cognition after conditioning on the genome-wide rg-predicted effect from those traits.
  - Add a formal random-effects heterogeneity test across the non-UKB lineages, with SD-scale harmonisation.
