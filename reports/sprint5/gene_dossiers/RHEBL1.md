# RHEBL1 — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**LOCUS_HIGH_GENE_UNRESOLVED (locus L7009, stratum L2).** RHEBL1 has the cleanest adult-brain direction in this batch (D2: 7 rows,
3 cohort units, 100% agreement). Independent 2026 GWAS of infant temperament and of a reading/ADHD common factor also colocalise
the 12q13.12 locus with RHEBL1 cortex eQTL. But the gene assignment is fragile on three counts. The primary FOCUS run favours PFKM
(0.77 vs 0.22). Open Targets now favours DDN. And the mouse paralog data suggest Rheb2 is dispensable for brain mTORC1.
The eQTL is real; whether RHEBL1 is the effector is unresolved.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L7009 (MAGMA label DDN), stratum **L2**, log10BF_independent 0.574, locus rank 12 (4–74), gc_aligned_z 2.296, panels A;C |
| V2G classes | QTL (1 class; class_detail QTL = 3). Other gene with a class: DDN (ENHANCER_LINK, 1) |
| QTL rows | 7 strong colocs: GTEx ×4 tissues, ROSMAP ×2, CommonMind ×1 (Sprint 4 coloc.abf) |
| FOCUS (primary config joint_brain_gene_x_tissue_p1e-3) | RHEBL1 **0.22** vs **PFKM 0.77**. focus_contradiction False and contested False, because the contested rule needs this gene < 0.2: **RHEBL1 escapes CONTESTED by 0.02** |
| FOCUS (other configs, `joint_gene_tissue_finemapping.csv`) | gtexv8_eur brain cortex RHEBL1 PIP 0.998/0.974 (twas z 5.62), but model cv_r2 only 0.073. GTEx frontal cortex BA9 0.219 (cv_r2 0.028). Competing genes in cerebellum/muscle: DDN 1.00 (muscle), RP1-228P16.1 0.99, FMNL3 0.88, PFKM 0.79 |
| Open Targets L2G 26.06 | Current assignment **DDN** 0.5868 (changed from Sprint-4 PRKAG1); second PRKAG1 0.5618; rank-1 majority DDN (0.444, 18 credible sets). RHEBL1 is not in the top two. Flags CHANGED_ASSIGNMENT; POSITIONAL_ONLY; MULTI_GENE_AMBIGUITY |
| Direction | **D2 / DIRECTION_RESOLVED**: cognition-increasing allele → HIGHER RHEBL1 in adult brain (CommonMind, GTEx, ROSMAP; 7 rows, 5 pooled pairs, agreement 1.0) |
| brainSCOPE | 23 credible variants, 22 tested; RHEBL1 **not significant in any of 17 cell types**; no gene significant at this locus. Top SuSiE variant rs10875914 PIP 0.265 |
| Expression | GTEx brain median **2.016 TPM** (low); ADULT_DYNAMIC |
| Perturbation | P5; LOEUF 1.092 (tolerant) |
| Ranks | B 14; E **2**; A 12; C **1**; D 36 |

## 3. Three questions, kept separate

- **A. Is RHEBL1 a causal cognition gene? Not supported.** There is no perturbation evidence, and paralog mouse genetics argue that RHEB1, not RHEBL1, carries brain mTORC1 function.
- **B. Is it a natural high-cognition gene? Locus supported (moderate, L2); gene not supported.** The packet already states "gene assignment not credible".
- **C. Is it adult-modifiable? The direction is resolved in adult bulk brain, but the cell type and the gene identity are unresolved.** The bulk eQTL does not reappear in any brainSCOPE cell type, which is odd for a gene with a strong bulk eQTL. It may reflect low expression (2 TPM) and dropout in pseudobulk.

## 4. Causal hypothesis chain

rs10875914 (PIP 0.265) and LD partners —[EVIDENCED: SuSiE]→
regulatory element —[MISSING: no RHEBL1 ENHANCER_LINK. The only E2G link at the locus is rs1054442 (PIP 0.067) → **DDN**, score 0.994]→
RHEBL1 expression (higher) —[EVIDENCED: 7 bulk colocs, 3 units]→
cell type —[MISSING: brainSCOPE null in all 17 cell types]→
direction (higher RHEBL1 ↔ higher cognition) —[EVIDENCED at the bulk level]→
cognition —[MISSING: no functional link. The expected effect would be a small increase in mTORC1/NF-κB signalling (INFERRED from overexpression biology)]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 42386913; doi:10.1038/s41562-026-02486-5 (Hollowell 2026, Nat Hum Behav) | Infant/toddler temperament GWAS (n ≈ 44–73k): the activity locus colocalises with adult cortex RHEBL1 eQTL (PP 0.93) | SUPPORTING (locus + eQTL gene) / partly NON-INDEPENDENT | GWAS cohorts are non-UKB paediatric samples, so the association lineage is independent. The eQTL reference (adult cortex) likely overlaps GTEx/MetaBrain, so the gene assignment is not independent of ours. The phenotype is temperament/activity, not cognition |
| PMID 42393086; doi:10.1038/s41539-026-00433-7 (Wang 2026) | A reading-disorder + ADHD common-factor GWAS finds a 12q locus (rs7969091); T-SEM implicates RHEBL1 and **LMBR1L** | NON-INDEPENDENT (TWAS weights) | Adds a second candidate (LMBR1L). We have not computed LD between rs7969091 and our lead rs10875914 |
| PMID 33263727; doi:10.1001/jamapsychiatry.2020.3738 (Li 2021) | Han Chinese + EUR bipolar meta-analysis: new locus near RHEBL1 (rs7969091, P = 3.1×10⁻⁸) | DISEASE_ONLY (pleiotropy) | Independent ancestry. Positional naming |
| PMID 21238928; doi:10.1016/j.devcel.2010.11.020 (Zou 2011) | "Rheb1, but not Rheb2, is critical for embryonic survival and mTORC1 signalling"; neural Rheb1 deletion abolishes brain mTORC1 | CONTRADICTING (functional relevance) | Rheb2/Rhebl1 cannot compensate in brain, so RHEBL1 dosage has an uncertain neural effect |
| PMID 32518628; doi:10.12688/f1000research.22367.1 (Angarola 2020) | RHEBL1 can activate mTORC1 when over-expressed; its membrane targeting differs from RHEB | MECHANISTIC_ONLY | Review |
| PMID 38338768; doi:10.3390/ijms25031489 (2024 review) | Rheb1/Rheb2 in neuronal mTOR signalling and cancer | MECHANISTIC_ONLY | Mostly RHEB1 data |
| PMIDs 40369227, 42332182 | RHEBL1 over-expression in cancers (pan-cancer, OSCC) | DISEASE_ONLY | Oncology context |
| Our FOCUS / Open Targets (internal) | PFKM (FOCUS 0.77) and DDN (L2G 0.587, E2G) compete | CONTRADICTING (alternative genes) | Same eQTL cohorts (FOCUS) and same credible sets (L2G), so NON-INDEPENDENT of our QTL class, but they disagree with it |

Shared data: the temperament coloc, the reading/ADHD T-SEM and our QTL rows all use adult-cortex eQTL panels that overlap GTEx. Counted together they are one gene-assignment lineage, not three. The temperament and bipolar GWAS are independent association lineages for the locus.

## 6. Modifiability characterisation (facts only)

- Protein: small Ras-superfamily GTPase (Rheb subfamily), C-terminally farnesylated (CAAX). It sits on the cytoplasmic side of endomembranes; not extracellular despite the packet's membrane flag. Endogenous ligand GTP/GDP. Its GAP is the TSC1/TSC2 complex. It binds SmgGDS (PMID 33574130).
- Structure: "Structure with Ligand; Med-Quality Pocket" (Open Targets). GTPase nucleotide pockets are generally hard to target selectively.
- Known modulators (fact only): no RHEBL1-selective compounds found. Farnesyltransferase inhibitors (e.g. lonafarnib, tipifarnib) block CAAX processing of RHEB-family proteins non-selectively. Rapalogs act downstream on mTORC1. Neither is RHEBL1-specific. 0 probes, 0 clinical candidates.

## 7. Pleiotropy and safety

LOEUF 1.092 (tolerant); no Mendelian disease. The locus is pleiotropic across temperament/activity, reading/ADHD and bipolar disorder. An mTORC1-activating direction ("higher RHEBL1") shares a pathway with TSC-spectrum pathology (epilepsy, ID, tumours) via RHEB. That is a paralog/pathway caution, not a gene-specific one.

## 8. Largest contradiction

Our best-resolved adult direction (rank C = 1) is attached to a gene that (a) loses the primary FOCUS comparison to PFKM 0.22 vs 0.77, (b) is not
Open Targets' assignment (DDN), (c) shows no single-cell eQTL in any brainSCOPE cell type, and (d) is functionally dispensable for brain
mTORC1 in mice. The non-contested status depends on a 0.02 margin under the contested threshold.

## 9. Missing arrow and single best next computation

Missing: gene identity. Bulk eQTL colocalisation cannot separate RHEBL1, PFKM, DDN and LMBR1L when they share one haplotype.
**Next computation:** conditional/joint colocalisation at L7009, i.e. coloc.susie with per-gene SuSiE eQTL credible sets for RHEBL1, PFKM, DDN, LMBR1L, DHH and PRKAG1 in GTEx cortex, CommonMind and ROSMAP. Add LD (1000G EUR) between rs10875914 and the published rs7969091. Report whether RHEBL1's eQTL credible set is the one shared with the cognition credible set, rather than a correlated one.
