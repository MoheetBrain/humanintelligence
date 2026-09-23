# NEGR1: literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `LIKELY_QTL_PASSENGER` (contested locus, L3).**
- The 1p31.1 locus is a large pleiotropic signal (cognition, BMI, depression). Our gene assignment is weak:
  - FOCUS puts PIP 1.0 on the pseudogene RPL31P12.
  - Open Targets L2G is driven by distance.
  - Cell-type eQTLs for NEGR1 do not tag the GWAS lead.
- The literature raises a sharp direction problem. At rs3101339, the allele reported to raise NEGR1 expression and depression risk is the intelligence-increasing allele in Savage 2018. Mouse NEGR1 overexpression *and* knockout both impair memory, so the dosage response is inverted-U.

## 2. Our computed evidence (packet; unchanged)

| Item | Value |
|---|---|
| Locus | L257194, lead rs3101338. Cognition-increasing allele A (davies_z +7.246). Stratum L3, log10BF_independent 0.196, rank 49 (10–126). gc_aligned_z 0.969. Gate B `NOT_SUPPORTED_AT_THIS_POWER` (FDR 0.43). |
| Classes | ENHANCER_LINK (3 units: rs3101336, rs3101338, rs3128341) + QTL (1). CONTESTED; focus_contradiction true. |
| FOCUS | NEGR1 PIP 0.102 (primary) vs RPL31P12 1.00. NEGR1 0.87 in one hippocampus config (TWAS z −2.32); NULL.MODEL 0.997 in other configs. |
| OT L2G 26.06 | NEGR1 0.898, STABLE_ASSIGNMENT but `POSITIONAL_ONLY` (top SHAP: distance) |
| Sprint-4 direction | `RESOLVED_ON_ROWS_ONLY_NOT_ROBUST`: 5 rows, 1 cohort unit (ROSMAP). Majority: cognition-increasing allele → HIGHER NEGR1. |
| BrainSCOPE | NEGR1 significant only in Lamp5 (lead rs2821260, p 1e-6). The best eQTL hit has r² 0.023 with the GWAS lead (`EQTL_LEAD_NOT_IN_LD`). 16 cell types not significant. The nearby lncRNA AL513166.1 is significant in 11 cell types, also not in LD. |
| Independent lineages | Zabaneh aligned z 2.50. GenLang PIQ aligned z 0.75 (PARTIAL_OVERLAP). |
| Modifiability | GPI-anchored IgLON adhesion molecule (extracellular). No pocket or probes. LOEUF 0.429. |

**Direction look-up I ran for this dossier (local sumstats; exploratory, not a protocol test):**
- In Savage 2018, rs3101339 allele a has z −7.76, so **C is intelligence-increasing**. rs3101338 allele A has z +9.28.
- GenLang PIQ at rs3101338: A beta +0.0097 (SE 0.013), p 0.46. That is concordant but null. Its heterogeneity with Savage is z 1.64 (p 0.10), assuming both betas are in SD units.

## 3. Three separate questions

- **A. Causal cognition gene? NOT SUPPORTED at gene level.**
  - No human perturbation of NEGR1 is tied to cognition, except rare 1p31.1 deletions that include NEGR1 with ID/learning difficulty (case reports).
  - The gene assignment is contested (RPL31P12, AL513166.1).
- **B. Natural high-cognition gene? Locus concordant but weak outside UKB; gene not resolved.** Only G&C (0.97) and Zabaneh (2.50) are weakly concordant.
- **C. Adult-modifiable? NOT SUPPORTED as a monotonic direction.**
  - Rows-only direction: cognition-increasing allele → higher NEGR1.
  - Literature: the same-direction allele is reported to raise NEGR1 and depression risk.
  - Adult vHIP overexpression in mouse impaired working memory; knockout also impairs learning.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| Variant → element | INFERRED | E2G brain links (3 variants). Upstream common deletion CNVs (Willer 2009; Wheeler 2013). rs3101339 shown regulatory by reporter/EMSA/editing (Zhang 2025). |
| Element → NEGR1 | INFERRED/contested | E2G + ROSMAP rows vs FOCUS RPL31P12 and BrainSCOPE non-LD eQTLs |
| NEGR1 → cell type | MISSING | Lamp5 only, not in LD |
| Direction | CONTRADICTED/unresolved | Rows: up = cognition+. Literature: up = MDD risk and memory impairment in mouse. |
| → Cognition | MISSING | Mouse data are bidirectionally harmful |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Savage 2018 Nat Genet, PMID 29942086 | rs3101338/rs3101339 genome-wide for intelligence | SUPPORTING (locus) | Largely UKB. [UKB-shared A] with Davies 2018 (PMID 29844566) |
| Willer 2009 Nat Genet, PMID 19079261, doi:10.1038/ng.287 | NEGR1 locus for BMI. Common upstream deletion. | NON-INDEPENDENT (pleiotropy) | BMI GWAS lead rs3101336 (Locke 2015) is **in our credible set** |
| Wheeler 2013 Nat Genet, PMID 23563609 | NEGR1 deletion and severe early-onset obesity | DISEASE_ONLY | |
| Bobyn 2020 BMC Med Genet, PMID 32375678 | The ~40-kb deletion upstream of NEGR1 (predicted to remove the promoter) is common, **homozygous in ~40%** of controls | CONTRADICTING (dosage essentiality) | Loss of the upstream element is common and tolerated |
| Zhang 2025 Mol Psychiatry, PMID 40382479, doi:10.1038/s41380-025-03052-7 | rs3101339 is causal. **Risk allele C upregulates NEGR1.** vHIP overexpression causes working-memory impairment, anxiety/depression-like behaviour and spine loss. | CONTRADICTING (direction) | C = intelligence-increasing in Savage (our look-up) |
| Lee 2026 Biol Sex Differ, PMID 41588420, doi:10.1186/s13293-025-00816-2 | Negr1-/- mice have impaired spatial learning (Morris water maze) and anxiety | SUPPORTING (LoF) / MECHANISTIC | With Zhang 2025, this gives an inverted-U |
| Kim KH 2024 BPGOS, PMID 39170714 | NEGR1 regulates adult olfactory neurogenesis and affective discrimination | MECHANISTIC_ONLY | Adult function |
| Lee AW 2012 PLoS One, PMID 22844493 | Negr1 loss changes body mass in mouse | MECHANISTIC_ONLY (pleiotropy) | |
| Tassano 2020 EJMG, PMID 32209393; Genovese 2015 J Pediatr Genet, PMID 27617112 | 1p31.1 deletions affecting only NEGR1 in patients with neuro-psychiatric/learning features | DISEASE_ONLY | Few cases; variable. Family segregation unclear. |
| Kaare 2022 Brain Sci, PMID 36552158 | Negr1-/- mice have altered monoamine release and amphetamine sensitisation | MECHANISTIC_ONLY | |
| Dennis 2014 NeuroImage, PMID 25072390 | NEGR1 variant associated with white-matter integrity | MECHANISTIC_ONLY | Small imaging study |

## 6. Modifiability characterisation (facts only)

- **Protein:** an IgLON-family (three Ig domains), GPI-anchored cell-surface adhesion molecule. It is extracellular, can be shed, and forms homo- and heterophilic IgLON interactions. It interacts with FGFR2 (Szczurkowska 2018 Brain, PMID 30059965) and with NPC2 in cholesterol trafficking (Kim 2017 BBRC, PMID 27940359).
- **Enzymatic activity or small-molecule pocket:** none.
- **Antibody tractability:** positive (surface protein).
- **Known modulators, probes, clinical programmes:** none found.

## 7. Pleiotropy and safety

- **At the variant/locus level:** BMI/obesity (one of the strongest BMI loci), major depression, and white-matter and brain phenotypes.
- **At the gene level (mouse):** body mass, anxiety/depression-like behaviour, testosterone and lipid metabolism, gut permeability and microbiome, and sex-specific effects.
- **Dosage:** both overexpression and knockout harm behaviour in mouse.

## 8. Largest contradiction

- Our weak rows say the cognition-increasing allele raises NEGR1.
- Zhang 2025 says the allele that raises NEGR1 at rs3101339 is the depression-risk allele, and that raising NEGR1 in adult ventral hippocampus impairs working memory.
- By our Savage look-up, that same C allele is intelligence-*increasing*.

Either the locus acts on cognition through a different gene or element, or the NEGR1 effect is non-monotonic and trait-specific. In both cases, "higher NEGR1 = better" cannot be inferred.

## 9. Missing arrow and single best next computation

- **Missing arrow:** a shared causal variant for cognition and NEGR1 expression in adult brain, and the allele alignment across cognition, MDD and BMI.
- **Best next computation:**
  - Run an allele-aligned multi-trait colocalisation at 1p31.1 (HyPrColoc or coloc-SuSiE).
  - Inputs: Davies/Savage cognition, PGC/Howard MDD, GIANT BMI, and adult-brain NEGR1 and RPL31P12/AL513166.1 eQTLs (MetaBrain/PsychENCODE).
  - Use an LD matrix that includes the upstream deletion tag SNPs.
  - Report which trait clusters share a variant, and the sign of NEGR1 expression per cognition-increasing allele.
