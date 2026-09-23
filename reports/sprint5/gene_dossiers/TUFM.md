# TUFM — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**LOCUS_HIGH_GENE_UNRESOLVED (locus L51327, stratum L1, locus rank 1).** This is our strongest replicated locus outside UKB. It sits in the
distal 16p11.2 SH2B1/ATXN2L/TUFM haplotype block, one of the most pleiotropic eQTL regions in the genome. TUFM's claim rests on
GTEx-only colocalisation. Our own brainSCOPE lookup and a published cross-species study both point to **SH2B1**, which our
classification does not surface. The UNRESOLVED label is honest. If anything, TUFM is the less likely effector.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L51327 (MAGMA label ATXN2L), stratum **L1**, log10BF_independent 1.24, locus rank **1** (1–17), gc_aligned_z 3.441, panel A |
| V2G classes | QTL (1 class; 5 GTEx rows, 1 cohort unit). Other genes with classes: EIF3C, NPIPB9 (1 each) |
| FOCUS | packet PIP 0.0 and no contradiction. No L51327 rows in the Sprint-4 joint FOCUS table, so "not evaluated" |
| Open Targets L2G 26.06 | TUFM 0.5086 (stable); second SULT1A1 0.4703; rank-1 majority across 18 credible sets = **SH2B1** (0.333); top SHAP distanceSentinelTss (POSITIONAL). Flags STABLE_ASSIGNMENT; POSITIONAL_ONLY; **MULTI_GENE_AMBIGUITY** |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 5 rows (4 pooled pairs), all GTEx. Cognition-increasing allele → LOWER TUFM |
| brainSCOPE | TUFM is **absent from all 24 pseudobulk matrices** (GENE_NOT_IN_ANY_BRAINSCOPE_MATRIX, 63 lookup rows). At the same credible variants (67 of 69 tested), significant single-cell eQTLs hit **SH2B1** (71 SIGNIFICANT rows across ~17 cell types, all aligned HIGHER), NPIPB9 (248 rows; L2/3, L4, L5 IT and Oligo; all HIGHER), NPIPB7 and AC133550.3. Source: `reports/sprint5/brainscope_variant_lookup.csv` / `_summary.csv` |
| Expression | GTEx brain median 99.98 TPM; MIXED |
| Perturbation | P5; LOEUF 0.703 |
| Ranks | B 4; E **1**; A 1; C 4; D 36 |

## 3. Three questions, kept separate

- **A. Is TUFM a causal cognition gene? Not supported.** Human LoF causes infantile mitochondrial encephalopathy (COXPD4). That is DISEASE_ONLY evidence and is never inverted into enhancement. No common-variant-scale perturbation exists.
- **B. Is it a natural high-cognition locus? Supported at locus level (strong, L1).** It is not supported for TUFM as the gene.
- **C. Is it adult-modifiable? Not testable for TUFM.** The direction rests on GTEx rows only, from one cohort unit. TUFM cannot be assessed in brainSCOPE.

## 4. Causal hypothesis chain (for TUFM)

credible variants (PIP diffuse: top rs62037363 0.039, rs3888190 0.035; 69 variants, ΣPIP 0.955) —[INFERRED: extended LD block, ~1 Mb r² > 0.7 per Volckmar 2015]→
regulatory element —[MISSING: no TUFM ENHANCER_LINK class]→
TUFM expression —[EVIDENCED, single resource: GTEx coloc; not measurable in brainSCOPE]→
cell type —[MISSING]→
direction (cognition allele → lower TUFM) —[INFERRED: rows-only]→
cognition —[MISSING, and the disease direction is opposite: severe LoF → encephalopathy. That says nothing about common-variant dosage]

Competing chain with more evidence in our own data: same variants → **SH2B1** higher in ~17 brainSCOPE cell types (EVIDENCED) → Du 2023 mouse hippocampal Sh2b1 deletion impairs working memory (MECHANISTIC) → cognition (INFERRED).

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 38434247; doi:10.34133/research.0269 (Du 2023) | A UKB fluid-intelligence GWAS assigns the 16p11.2 signal to **SH2B1**. Hippocampal (inhibitory-neuron) Sh2b1 deletion impairs working memory in mice | CONTRADICTING (alternative gene) | Human arm is UKB, so NON-INDEPENDENT of the discovery GWAS but independent of our UKB-free replication. The mouse arm is independent. The strongest published contradiction to TUFM |
| PMID 25955518; doi:10.1371/journal.pone.0125660 (Volckmar 2015) | The BMI SNP rs7359397 tags a ~1 Mb r² > 0.7 block (SH2B1, APOBR, SULT1A1/2, TUFM). No non-synonymous TUFM variants were found in extremely obese youth | CONTRADICTING (resolution) | Shows the block is too wide for positional assignment |
| PMID 39896714; doi:10.1016/j.ibneur.2025.01.001 (Li 2025) | TUFM rs3088215 is shared between BMI, grey-matter volume and fluid intelligence | NON-INDEPENDENT | UKB. Positional naming of a pleiotropic SNP |
| PMID 17160893; doi:10.1086/510559 (Valente 2007) | Biallelic TUFM mutation → fatal infantile encephalopathy/leukodystrophy, defective mtDNA translation | DISEASE_ONLY | Establishes neural essentiality of severe LoF. Not a dosage-direction argument |
| PMID 41866827; doi:10.1002/ajmg.a.70136 (2026) | COXPD4 phenotype expansion | DISEASE_ONLY | Same disease lineage |
| ClinGen ISCA-37486 (distal 16p11.2 BP2–BP3 deletion) | Deletion of SH2B1/ATXN2L/TUFM and others → DD/ID and obesity; dosage-sensitive region | DISEASE_ONLY | Multi-gene CNV; not attributable to TUFM |
| PMID 26449484; PMID 34494379 | Obesity SNPs at 16p11.2 are meQTL/eQTL for TUFM, SH2B1, ATXN2L, SULT1A1/2 at the same time | NON-INDEPENDENT (pleiotropy) | Many genes share the same eQTL haplotype, so TUFM eQTL coloc is expected under LD |
| PMID 41904133; doi:10.1038/s41420-026-03075-1 (review 2026) | TUFM also regulates mitophagy and innate immunity beyond translation | MECHANISTIC_ONLY | No cognition data |
| PMID 39496783 (2024) | Tufm lactylation modulates neuronal mitophagy after TBI | MECHANISTIC_ONLY | Injury model |

Shared data: rows 1, 3 and 6 all draw on UKB and GTEx-era eQTLs. The only fully independent perturbation evidence (Du 2023, mouse) concerns SH2B1, not TUFM.

## 6. Modifiability characterisation (facts only)

- Protein: nuclear-encoded mitochondrial matrix GTPase (EF-Tu_mt; ChEMBL CHEMBL4105970). It delivers aminoacyl-tRNA to the mitoribosome A-site. It also has moonlighting roles in mitophagy (ATG5–ATG12, NLRX1) and RLR/MAVS dampening.
- Structure: human mitoribosome complexes with TUFM (e.g. PDB 7A5G, 7O9K). Open Targets: "Structure with Ligand" and PROTAC "Small Molecule Binder".
- Known modulators (fact only): no human-TUFM-selective compounds found. Bacterial EF-Tu antibiotics (kirromycin, GE2270A, enacyloxin class) act on the prokaryotic homologue. We did not verify their activity on human mitochondrial EF-Tu. 0 probes, 0 clinical candidates.
- Not extracellular.

## 7. Pleiotropy and safety

LOEUF 0.703 (moderate constraint). Biallelic LoF causes lethal infantile OXPHOS deficiency, and there is a homozygous variant with premature ovarian insufficiency (PMID 37461298). The locus is highly pleiotropic: BMI/obesity, T2D, COPD, IBD, fluid intelligence, grey-matter volume. Any locus-level effect is confounded with metabolic traits.

## 8. Largest contradiction

Our own brainSCOPE data show that the credible variants act as single-cell eQTLs for SH2B1 (HIGHER in ~17 cell types) and NPIPB9. TUFM cannot be measured there. Open Targets' credible-set majority is also SH2B1, and published mouse work ties Sh2b1 to working memory. In `causal_gene_evidence_matrix.csv`, SH2B1 at L51327 has **0 classes**. That is consistent with the frozen rules, because brainSCOPE significance tagging is NOT_A_CLASS until a PP.H4 ≥ 0.8 coloc exists, and no bulk SH2B1 coloc passed. The classification therefore cannot express this signal. **Flag for coordinator:** this is the only locus in batch 1 where our own single-cell data point clearly to a gene other than the dossier gene.

## 9. Missing arrow and single best next computation

Missing: which gene the L1 signal acts through.
**Next computation:** run coloc.abf and coloc.susie for Davies-L51327 against brainSCOPE pseudobulk eQTLs for SH2B1, NPIPB9, NPIPB7 and ATXN2L (per cell type), and against bulk GTEx/CommonMind/ROSMAP for all 16p11.2 genes including TUFM. Use one LD reference, then compare per-gene PP.H4 and aligned signs side by side. If SH2B1 PP.H4 ≥ 0.8 with ≥ 3 units, SH2B1 should enter the matrix as a competitor, and TUFM's rank-E #1 position becomes a locus rank, not a gene rank.
