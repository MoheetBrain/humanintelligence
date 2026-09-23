# DCC — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**LOCUS_HIGH_GENE_UNRESOLVED (locus L1630, stratum L2).** DCC is the only protein-coding gene in its 18q21.2 window. It has the
richest neurobiology of this batch: Mendelian disease, adult-synapse mouse genetics, and a pan-psychiatric pleiotropic GWAS hub.
Our V2G support is thin, though: 3 GTEx coloc rows in one cohort unit, no brainSCOPE signal, low adult expression. DCC is a
plausible neurodevelopmental effector whose adult, cognition-specific role is not demonstrated.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L1630 (MAGMA label DCC), stratum **L2**, log10BF_independent 0.5972, locus rank 9 (3–81), gc_aligned_z 2.163, panels A;C |
| V2G classes | QTL (1 class; 3 GTEx rows, 1 cohort unit). No other gene in the locus has any class |
| FOCUS | packet PIP 0.0 and no contradiction. No L1630 rows in the Sprint-4 joint FOCUS table, so "not evaluated" |
| Open Targets L2G 26.06 | DCC 0.7879 (stable; no second gene scored); rank-1 majority DCC (1.0 over 17 credible sets); top SHAP proteinGeneCount500kb (POSITIONAL), with positive CODING SHAP 0.176. Flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 3 rows (2 pooled pairs), GTEx only. Cognition-increasing allele → HIGHER DCC |
| brainSCOPE | 209 credible variants, 208 tested. **DCC not significant in any of 17 core cell types**, and no other gene was significant at this locus |
| Expression | GTEx adult brain median **1.213 TPM**; developmental class **PRENATAL_DOMINANT**. DEVELOPMENTAL_CAUSAL_ONLY flag = False only because one adult GTEx coloc exists |
| Perturbation | **P4**, DD/ID disease gene (DISEASE_ONLY); LOEUF 0.414 (constrained) |
| Ranks | B 11; E 9; A 9; C 4; D 12 |

## 3. Three questions, kept separate

- **A. Is DCC a causal cognition gene? Not supported for common-variant cognition. Supported as a neurodevelopmental disease gene.** Biallelic LoF causes developmental split-brain syndrome with intellectual impairment. Heterozygous LoF usually gives mirror movements with normal intellect. That is DISEASE_ONLY evidence and cannot be inverted.
- **B. Is it a natural high-cognition gene? Supported at locus level (moderate, L2).** The gene assignment is positional: DCC is the only gene nearby.
- **C. Is it adult-modifiable? Weak.** Adult expression is low, brainSCOPE is null, and the direction comes from one cohort. Mouse data do show an adult synaptic role (Horn 2013), so an adult arrow is plausible but unmeasured in humans.

## 4. Causal hypothesis chain

credible variants (diffuse: top rs11662271 PIP 0.084; 209 variants) —[INFERRED]→
intronic/distal DCC regulatory element —[MISSING: no ENHANCER_LINK class]→
DCC expression —[EVIDENCED, weak: GTEx coloc 3 rows, 1 unit; brainSCOPE null]→
cell type —[MISSING: no single-cell eQTL. Prenatal-dominant expression suggests a developmental window our adult data cannot reach]→
direction (cognition allele → higher DCC) —[INFERRED: rows only]→
cognition —[INFERRED: adult forebrain DCC deletion impairs LTP and spatial/recognition memory in mice (Horn 2013). Human LoF → callosal/midline wiring defects]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 20431009; doi:10.1126/science.1186463 (Srour 2010) | Heterozygous DCC mutations cause congenital mirror movements | DISEASE_ONLY | Haploinsufficiency usually spares intellect, so gene dosage does not map simply onto cognition |
| PMID 28250456; doi:10.1038/ng.3804 (Jamuar 2017) | Biallelic DCC LoF → developmental split-brain syndrome (HGPPS2 with impaired intellectual development) | DISEASE_ONLY | Severe developmental; basis of our P4 |
| PMID 28250454; doi:10.1038/ng.3794 (Marsh 2017) | DCC mutations cause isolated agenesis of the corpus callosum *without intellectual disability*, with incomplete penetrance | CONTRADICTING (for dosage → cognition) | Heterozygous LoF alters wiring but largely not intelligence |
| PMID 36889039; doi:10.1016/j.cortex.2023.01.008 (Knight 2023) | Within one DCC family, carriers range from near-normal cognition to severe impairment | DISEASE_ONLY | Variable expressivity |
| PMID 23291093; doi:10.1016/j.celrep.2012.12.005 (Horn 2013) | Deleting DCC from adult forebrain neurons abolishes LTP and impairs spatial and recognition memory (Src–NMDAR) | SUPPORTING (MECHANISTIC, adult) | Mouse; direction consistent with "more DCC → better memory". Not human cognition |
| PMID 27773352; doi:10.1016/j.biopsych.2016.08.017 (Torres-Berrío 2017) | DCC is raised in depressed-suicide PFC; miR-218 regulates Dcc and stress susceptibility | MECHANISTIC_ONLY / DISEASE_ONLY | Here *higher* DCC goes with depression-like vulnerability, which cuts against a simple "higher = better" reading |
| PMID 31659271; doi:10.1038/s41380-019-0561-7 (Vosberg 2020) | Netrin-1/DCC controls adolescent mesocortical dopamine maturation; DCC variants associate with depression, schizophrenia and substance use | MECHANISTIC_ONLY | Review; developmental/adolescent window |
| PGC Cross-Disorder 2019, Cell, doi:10.1016/j.cell.2019.11.020 (PMC7077032) | The 18q21.2 DCC locus is the most pleiotropic of 109 loci across 8 psychiatric disorders and colocalises with DCC brain eQTL | NON-INDEPENDENT (eQTL) / pleiotropy | Uses GTEx/PsychENCODE-era eQTL resources that overlap ours. Shows the locus is not cognition-specific |
| PMID 32184385 (Transl Psychiatry 2020) | Multi-omics integration supports DCC as a depression risk gene | NON-INDEPENDENT | Same eQTL resources |
| PMID 35115383; doi:10.1523/ENEURO.0216-18.2021 | Dcc+/− mice show only subtle locomotor differences | MECHANISTIC_ONLY | No cognitive phenotype reported |

Shared data: the PGC and depression-integration rows reuse bulk brain eQTL panels that overlap our GTEx rows. The Mendelian rows (Srour, Jamuar, Marsh, Knight) come from overlapping clinical cohorts and form one lineage.

## 6. Modifiability characterisation (facts only)

- Protein: single-pass type-I transmembrane receptor (Ig superfamily: 4 Ig + 6 FNIII ectodomains; intracellular P1–P3 motifs). A dependence receptor that is pro-apoptotic when unliganded. **Extracellular domain present.**
- Endogenous ligand: netrin-1 (also draxin and other netrins). Co-receptors and partners include UNC5 (repulsion), ROBO1, and the WAVE regulatory complex (PMID 39353037).
- Tractability (Open Targets): small molecule "Med-Quality Pocket". Antibody: GO CC high-confidence and signal peptide/TM. No ChEMBL target record found (search 2026-09-23). 0 probes, 0 clinical candidates.
- Existing clinical programmes act on the **ligand**, not DCC: NP137 (humanised anti-netrin-1 mAb, NETRIS Pharma / Centre Léon Bérard) in oncology trials, e.g. NCT02977195 (Phase 1, completed), NCT04652076 (Phase 1/2), NCT05605496 (Phase 2). These are listed as facts only.

## 7. Pleiotropy and safety

LOEUF 0.414 (constrained). DCC was originally described as a colorectal tumour suppressor or dependence receptor. The GWAS locus is
pan-psychiatric: MDD, schizophrenia, bipolar, ADHD, ASD, anorexia, OCD, Tourette (PGC-CDG 2019), plus neuroticism and risk-taking.
Human LoF produces midline axon-guidance defects. Any modulation would touch dopamine-circuit maturation in adolescence (Vosberg 2020).

## 8. Largest contradiction

Heterozygous DCC LoF (≈50% dosage) usually yields mirror movements or callosal agenesis **without** intellectual disability (Marsh 2017).
At the same time, the common-variant eQTL effect we attribute is small, GTEx-only, and absent in brainSCOPE's 17 cell types. That
a dosage change is what drives the cognition association is therefore weakly supported. The signal may instead reflect a
prenatal regulatory effect that adult eQTL panels cannot capture.

## 9. Missing arrow and single best next computation

Missing: the element → DCC link in a developmentally relevant tissue.
**Next computation:** colocalise L1630 (Davies and the UKB-free replication z-scores) with **fetal-brain eQTL** (e.g. O'Brien 2018 / Walker 2019 fetal cortex summary statistics) and with PsychENCODE developmental eQTL. Also intersect credible variants with fetal-cortex ATAC/Hi-C E2G links. A fetal PP.H4 ≥ 0.8 with no adult brainSCOPE signal would earn a DEVELOPMENTAL_CAUSAL_ONLY-type annotation. It would also answer question C (adult-modifiable) in the negative.
