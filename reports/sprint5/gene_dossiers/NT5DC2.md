# NT5DC2: literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `LOCUS_HIGH_GENE_UNRESOLVED`. This is an EXPLICIT-INSPECTION dossier (brief Panel A / Q14), outside the frozen promotion rule.**
- The 3p21.1 locus is among our best-supported outside UKB (rank 3–4; G&C z ≈ 3). **NT5DC2 is best described as the locus label, not an established causal gene.**
- Its support is one evidence class: ENCODE-rE2G links that it mostly shares with STAB1 and UQCC5.
- Every gene-resolving method in our pipeline points elsewhere:
  - Open Targets L2G → STAB1;
  - FOCUS → GNL3 or NEK4;
  - BrainSCOPE cell-type eQTLs → GLT8D1 and PBRM1;
  - NT5DC2 is absent from all BrainSCOPE matrices.
- The literature is similarly split across GLT8D1, SFMBT1, GNL3, NEK4, ITIH3 and NT5DC2.

## 2. Our computed evidence (packet and tables; unchanged)

| Item | Value |
|---|---|
| Loci | L51460 (packet primary; rank 4, 1–46; log10BF_independent 0.815; gc_aligned_z 2.805) and L91869 (rank 3, 1–35; log10BF 0.972; gc_aligned_z 3.095; Gate B `G&C_SUPPORTED`, FDR 0.048). Both share lead **rs6778735**: cognition-increasing allele **C**; davies_z −7.717 for effect allele T. |
| Other lineages | Zabaneh aligned z 1.371. GenLang PIQ aligned z −0.234 (PARTIAL_OVERLAP). |
| NT5DC2 classes | ENHANCER_LINK only: 5 units (rs12489828, rs6778735, rs7614981, rs7636227, rs7639267). **STAB1 and UQCC5 each get 3 units from the same three variants.** Only rs6778735 (PIP 0.20) and rs7639267 are NT5DC2-specific. |
| Open Targets L2G 26.06 | **STAB1 0.682** (CHANGED_ASSIGNMENT from NT5DC2) vs NT5DC2 0.636. Rank-1 majority NT5DC2 in only 52.9% of credible sets. MULTI_GENE_AMBIGUITY. Top SHAP: enhancer E2G. L2G features show eQTL and sQTL coloc H4 ≈ 0.99 for **both** NT5DC2 and STAB1 (non-discriminating; tissue not resolved in the feature). |
| FOCUS (Sprint 4) | NT5DC2 PIP 0.0002. **GNL3 0.988** (cerebellar hemisphere, joint config). NEK4 0.97 (CMC DLPFC). SPCS1 0.548 (GTEx v8 cortex). NULL.MODEL 0.75–0.78. |
| BrainSCOPE | NT5DC2 `GENE_NOT_IN_ANY_BRAINSCOPE_MATRIX`. rs6778735 tested in 24 cell types. Core significant genes **GLT8D1, PBRM1** (L2/3 IT, L6 IT). GRN element targets GLT8D1, NISCH, SPCS1, WDR82. |
| Direction | `UNRESOLVED_NO_STRONG_COLOC` (0 rows) |
| Expression | GTEx brain TPM 11.88; `PRENATAL_DOMINANT` |
| Modifiability | Not computed in the packet (null) |

**Exploratory check I ran (local sumstats):**
- Savage 2018: rs6778735 T stdBeta −0.0182 (z −6.56).
- GenLang PIQ: T +0.0025 (SE 0.0107). Expected z −1.70 vs observed +0.23. Heterogeneity z −1.87, p 0.06, assuming SD scale.
- G&C TMA: T beta +0.0061 (SE 0.0020), p 0.002. That is concordant (T slower).

## 3. Three separate questions

- **A. Causal cognition gene? NOT SUPPORTED for NT5DC2.** The locus is real; the gene is unresolved. No human perturbation of NT5DC2 exists, and it has no Mendelian disease.
- **B. Natural high-cognition gene? The locus is replicated outside UKB (moderate: G&C z ≈ 3); the gene is not attributable.** Rahman 2026 (the G&C source) itself names NT5DC2, but that is the same data and positional labelling.
- **C. Adult-modifiable? NOT TESTABLE.**
  - No adult-brain QTL for NT5DC2 in BrainSCOPE and no Sprint-4 direction rows.
  - In vitro, NT5DC2 knockdown raises catecholamine synthesis (PC12D). That is a mechanism, not a cognition direction.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| rs6778735 or other credible variants → regulatory element | INFERRED | E2G brain biosamples. SuSiE PIP spread thin (0.20 at the lead; CS size 18–21). |
| Element → NT5DC2 | INFERRED, not specific | The same elements link to STAB1 and UQCC5. OT L2G prefers STAB1. |
| Element → other genes | EVIDENCED in other data | GLT8D1/PBRM1 cell-type eQTLs (BrainSCOPE); GNL3/NEK4 TWAS-FOCUS; SFMBT1/GLT8D1/NEK4 via rs2535629 editing (Li Y 2022) |
| NT5DC2 → cell type | MISSING | Not in any BrainSCOPE matrix |
| NT5DC2 → dopamine/TH | EVIDENCED in cell lines | Nakashima 2019, 2020; Yamaguchi 2024, 2025 (PC12D) |
| → Cognition direction | MISSING | |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Rahman 2026 Nat Commun, PMID 42069759, doi:10.1038/s41467-026-71738-9 | Executive-function GWAS (UKB + G&C). NT5DC2 is "independently replicated" before meta-analysis. | NON-INDEPENDENT | **Same G&C data as our gc_aligned_z** [G&C-shared B]. The gene name is a positional label. |
| Savage 2018, PMID 29942086; Davies 2018, PMID 29844566 | 3p21.1 genome-wide for intelligence | SUPPORTING (locus) | [UKB-shared A] |
| Nakashima 2019 BBRC, PMID 31279527, doi:10.1016/j.bbrc.2019.06.156 | NT5DC2 binds tyrosine hydroxylase. siRNA knockdown increases dopamine, noradrenaline and adrenaline synthesis. | MECHANISTIC_ONLY | PC12D cells |
| Nakashima 2020 J Neural Transm, PMID 32778969; Yamaguchi 2024 BBRC, PMID 38382359; Yamaguchi 2025 Mol Biol Rep, PMID 40751758 | NT5DC2 modulates TH phosphorylation and MAO activity | MECHANISTIC_ONLY | Same group; cell line |
| Singgih 2021 Transl Psychiatry, PMID 33462198, doi:10.1038/s41398-020-01149-x | Pan-neuronal knockdown of fly cNT5-II orthologs impairs habituation learning (dNT5A, dNT5C) | MECHANISTIC_ONLY | The fly ortholog is not one-to-one with NT5DC2 |
| Chen Y 2024 AJHG, PMID 39362218, doi:10.1016/j.ajhg.2024.09.001 | Non-EUR brain eQTLs prioritise NT5DC2 as an SCZ risk gene | SUPPORTING (gene, SCZ) | Independent eQTL resource, but SCZ not cognition. EAS/AA-driven. |
| Yang CP 2018 Nat Commun, PMID 29483533, doi:10.1038/s41467-018-03247-3 | GLT8D1 prioritised as the 3p21.1 SCZ gene (Sherlock/SMR) | CONTRADICTING (alternative gene) | Agrees with our BrainSCOPE GLT8D1 |
| Li Y 2022 Adv Sci, PMID 34978167, doi:10.1002/advs.202104786 | rs2535629 (ITIH3 intron) regulates GLT8D1, SFMBT1 and NEK4; SFMBT1 favoured | CONTRADICTING (alternative gene) | CRISPR-validated |
| Meng 2020 Mol Psychiatry, PMID 32826963 | GNL3 is the BD risk gene at 3p21.1 (CRISPRi in NPCs) | CONTRADICTING (alternative gene) | Agrees with our FOCUS GNL3 |
| Yang Z 2020 Mol Psychiatry, PMID 31723243, doi:10.1038/s41380-019-0592-0 | 3p21.1 psychiatric risk alleles predict worse cognition. NEK4, GNL3 and PBRM1 expression affects spine density. | CONTRADICTING (alternative genes) / SUPPORTING (locus-cognition) | Multi-gene convergence model |
| Witt SH 2014 Transl Psychiatry, PMID 25136889 | STAB1 is a BD candidate from state-trait expression | MECHANISTIC_ONLY | Weak; supports STAB1 as an alternative |
| NT5DC2 cancer literature (e.g. PMIDs 32382041, 30978441) | Pro-proliferative (EGFR stabilisation, Fyn) | MECHANISTIC_ONLY | Non-neural |

## 6. Modifiability characterisation (facts only)

- **Protein:** 5′-nucleotidase domain-containing protein 2, a haloacid dehalogenase (HAD)-type phosphatase fold of the cytosolic 5′-nucleotidase II family. It is cytosolic.
- **Catalytic activity:** not firmly established as a nucleotidase.
- **PPIs:** reported with TH (and 14-3-3 context), EGFR, TEAD4 and ACSL3.
- **Known modulators, probes, clinical programmes:** none found. OT modifiability was not computed in our packet.
- **Other:** no extracellular domain. The oncology literature treats NT5DC2 as a tumour-promoting factor (knockdown studies only).

## 7. Pleiotropy and safety

- The 3p21.1 region is one of the most pleiotropic psychiatric loci: SCZ, BD, MDD, cross-disorder, EA/cognition, plus metabolic and height signals in the wider region.
- NT5DC2 itself: dopamine/catecholamine synthesis regulation (in vitro) and roles in cancer proliferation.

## 8. Largest contradiction

"NT5DC2" is the MAGMA/positional label, but its only class (E2G) is shared with two neighbours, and every gene-resolving method points to a different gene:
- OT L2G → STAB1;
- FOCUS → GNL3/NEK4;
- BrainSCOPE → GLT8D1/PBRM1;
- published CRISPR work → SFMBT1/GLT8D1/NEK4 or GNL3.

The G&C "replication" also appears in Rahman 2026, which is the same dataset, so it cannot count twice.

## 9. Missing arrow and single best next computation

- **Missing arrow:** a shared causal variant between cognition and the expression of one specific gene in adult brain.
- **Best next computation:**
  - Run coloc-SuSiE between Davies cognition (L51460/L91869 region, with UKB-matched LD) and all-gene eQTL/sQTL credible sets from an adult-cortex bulk resource that includes NT5DC2 (e.g. MetaBrain cortex, PsychENCODE, or the non-EUR brain eQTLs of Chen 2024). Include NT5DC2, STAB1, GLT8D1, GNL3, NEK4, PBRM1 and SFMBT1.
  - Report PP.H4 per gene and the allele-aligned direction.
  - A gene is credible only if it alone reaches H4 ≥ 0.8 on the cognition credible set.
