# ANKRD12: literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `CODING_CAUSAL_LOF_ONLY`, with `DEVELOPMENTAL_CAUSAL_ONLY_flag = true`.**
- ANKRD12 has the strongest UKB PTV–fluid-intelligence signal of any gene in the batch.
- It has no Mendelian disease, no independent gene-level replication and almost no neural biology in the literature.
- UKB exome studies show the same PTVs associated with neuroticism, depression, loneliness, alcohol intake, daytime sleepiness, deprivation and income. The cognition signal may therefore be one face of a broad behavioural/SES pleiotropy, not a specific cognition mechanism.

## 2. Our computed evidence (packet; unchanged)

| Item | Value |
|---|---|
| Locus | none. Panel B. rank_B 17, rank_E 5, rank_D 1 (P2). |
| GTEx adult-brain TPM | 5.83. `PRENATAL_DOMINANT`. |
| Chen 2023 PTV VNR/FI | beta −0.694 (SE 0.126), p 3.77e-8, 53 carriers, exome-wide |
| Chen 2023 PTV EDU | beta −0.31 (SE 0.069), p 6.26e-6. FDR-significant only. |
| Chen 2023 PTV RT | beta +0.101 (SE 0.081), p 0.21 (null) |
| Genebass pLoF FI (20016) | burden p 5.28e-14, exome-wide. Same UKB participants. |
| Genebass pLoF second FI field | p 2.44e-5. Partly the same participants. |
| Wu 2025 pLoF EduYears | p 2.33e-16. TDI beta +0.071, p 4.6e-18. SES only. |
| Replication | not at gene level. The 8-gene set replicated. NFID DD/ID OR 2.39, p 0.24 (null). |
| Disease | none in DDG2P or OMIM. SCZ exome signal (per Chen). PheWAS dysarthria. BRaVa 2026: asthma/COPD. |
| Modifiability | Nuclear ankyrin-repeat co-repressor. No structure, no pocket, no probes, no clinical candidates. LOEUF 0.583. |

## 3. Three separate questions

- **A. Causal cognition gene? SUPPORTED only weakly (UKB-only LoF).**
  - The FI association is exome-wide in two analyses of the same UKB exomes.
  - The independent NFID DD/ID single-gene test is null (OR 2.39, p 0.24), and RT is null.
  - There is no Mendelian ID syndrome.
- **B. Natural high-cognition gene? NOT SUPPORTED.** There is no common locus and no GoF data.
- **C. Adult-modifiable? NOT TESTABLE.**
  - No adult perturbation data exist in any species.
  - No animal model exists in the literature. I found no Ankrd12 knockout behaviour paper.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| Rare PTV → ANKRD12 LoF | EVIDENCED (assumed NMD) | PTV burden |
| LoF → brain cell type | MISSING | Kang 2024 notes cerebellar expression and glial-differentiation pathway enrichment (annotation only) |
| Molecular mechanism | INFERRED | UniProt: may recruit HDACs to p160 coactivator / nuclear-receptor complexes (co-repressor) |
| Direction LoF → lower FI | EVIDENCED in UKB only | Chen; Genebass |
| LoF → cognition specifically (not general health/SES) | MISSING | Same PTVs associate with ≥7 non-cognitive UKB traits |

## 5. Literature red-team (all rows marked [A] use the same UKB 450k exomes)

| Source | Claim | Category | Note |
|---|---|---|---|
| Chen CY 2023 Nat Genet, PMID 37231097 | PTV and VNR exome-wide | SUPPORTING | Discovery. [A] |
| Karczewski 2022 Genebass, doi:10.1016/j.xgen.2022.100168 | pLoF FI p 5e-14 | NON-INDEPENDENT | [A] |
| Wu XR 2025 PNAS, PMID 39772748 | pLoF with EduYears, income and TDI | NON-INDEPENDENT / pleiotropy | SES [A] |
| Wu 2024 Nat Hum Behav, PMID 39511343, doi:10.1038/s41562-024-02045-w | ANKRD12 is a novel neuroticism gene (rare variants) | NON-INDEPENDENT / pleiotropy | [A] |
| Li 2024 Mol Psychiatry, PMID 39472661, doi:10.1038/s41380-024-02804-1 | ANKRD12 associated with depressive symptoms | NON-INDEPENDENT / pleiotropy | [A] |
| Fei 2024 Nat Hum Behav, PMID 38177695, doi:10.1038/s41562-023-01785-5 | ANKRD12 associated with daytime sleepiness and napping, and with "cognition and inflammatory traits" | NON-INDEPENDENT / pleiotropy | [A] |
| Kang 2024 Nat Commun, PMID 38982111, doi:10.1038/s41467-024-50132-3 | ANKRD12 is an alcohol-consumption gene | NON-INDEPENDENT / pleiotropy | [A] |
| Leger 2024 ACER, PMID 39031522 | ANKRD12 is a rare-variant alcohol gene | NON-INDEPENDENT | [A] |
| Wang 2025 J Affect Disord, PMID 39842675, doi:10.1016/j.jad.2025.01.096 | ANKRD12 is a loneliness gene | NON-INDEPENDENT / pleiotropy | [A] |
| Palmer 2026 medRxiv (BRaVa), PMID 42238450 | ANKRD12 associated with asthma/COPD in 10 biobanks | CONTRADICTING specificity | Partly independent of UKB, and non-neural |
| Smirnova 2019 BMC Genomics, PMID 31291891 | Serum ANKRD12 higher in SCZ and BD | MECHANISTIC_ONLY | Small proteomics study, not causal |
| Karedath 2019 / Voellenkle 2022 (PMIDs 31185953, 36428974) | circANKRD12 in cancer and endothelial stress | MECHANISTIC_ONLY | Non-neural; a circRNA isoform caveat |

**Forward citations and failed replications:**
- Of the 8 genes, the NFID DD/ID single-gene test is weakest for ANKRD12 (p 0.24).
- I found no DD/ID de novo enrichment report for ANKRD12. The paralog ANKRD11 causes KBG syndrome, and that paralogy should not be transferred to ANKRD12.

## 6. Modifiability characterisation (facts only)

- **Protein:** a very large (~2,000 aa) nuclear protein with ankyrin repeats. It is a putative HDAC-recruiting co-repressor.
- **Enzymatic activity, extracellular domain, pocket:** none known.
- **PPIs:** reported with p160/NCOA coactivators and HDACs (UniProt).
- **Known modulators, probes, clinical programmes, patents:** none found.
- **Isoforms:** a circular RNA (circANKRD12, exons 2–8) is abundant and biologically active in non-neural cells. PTV consequences could differ for the linear and circular products.

## 7. Pleiotropy and safety

- UKB PTV carriers show broad associations: psychiatric (neuroticism, depression, loneliness), behavioural (alcohol, sleepiness), SES (income, TDI), respiratory (asthma/COPD, BRaVa) and dysarthria (PheWAS).
- Constraint is moderate (LOEUF 0.583).
- No safety data exist for any modulation.

## 8. Largest contradiction

The FI association is our strongest single rare-coding cognition signal (Genebass p 5e-14), but it has three problems:
- It has no disease correlate (not in DDG2P or OMIM).
- The NFID DD/ID test is null.
- The same UKB carriers are worse on a wide set of non-cognitive health, SES and behaviour traits.

A general liability to poor health or SES, or a participation bias among UKB carriers, would produce the same pattern without any cognition-specific mechanism.

## 9. Missing arrow and single best next computation

- **Missing arrow:** evidence that ANKRD12 LoF acts on cognition specifically, and in a non-UKB sample.
- **Best next computation:**
  - Pull the Genebass gene-level pLoF results for ANKRD12 across all phenotypes (the public PheWAS).
  - Compute the rank and standardised effect of the cognitive fields relative to every other associated trait.
  - Test whether the cognitive effect survives after regressing the gene's trait-effect vector on the genome-wide rare-burden "general factor" (e.g. the correlation of effect vectors with GIGYF1 and ADGRB2).
  - In parallel, pull the DDD/Kaplanis 2020 de novo counts for ANKRD12.
