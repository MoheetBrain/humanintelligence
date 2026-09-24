# TTBK1 — gene dossier (Sprint 5A, new gene)

Scope: this dossier characterises the gene and appraises the evidence. Nothing here designs, doses or recommends an intervention; known modulators are listed as facts only.
Written 2026-09-24 (UTC). Our numbers are copied from the Sprint-5A outputs and are not changed here.
Companion dossier for the same locus: `reports/sprint5/gene_dossiers/DNPH1.md` (Sprint 5; see also the DNPH1 Sprint-5A addendum).

## 1. Verdict

**CAUSAL_GENE_MODERATE under the frozen rules (L55168, stratum L3, locus rank 24, interval 10–82). The label is technically valid but statistically fragile. TTBK1 is biologically the more plausible brain gene at this locus, and the weakest-evidenced part of the call is the QTL class that promoted it.**

What changed in Sprint 5A:
- TTBK1 moved from V2G_SUPPORTED_WEAK_LOCUS to CAUSAL_GENE_MODERATE (rank B 26 → 4).
- The promotion rests on a single SingleBrain oligodendrocyte colocalisation (PP.H4 0.862, LOWER) plus a Sprint-5 enhancer link.

Why that is fragile:
- There is no bulk, GTEx V11, devBrain or brainSCOPE support for TTBK1 at this signal.
- Bryois oligodendrocytes give only 0.141.
- The locus is weak (L3, log10BF 0.368), and no Sprint-5A fine-mapping run (plain or PolyFun; 1000G or UKB LD) produced a credible set.

Why the biology still favours TTBK1 over DNPH1:
- TTBK1 is a CNS-restricted tau/TDP-43 kinase.
- Its overexpression impairs learning in mice.

## 2. Our computed evidence (unchanged numbers)

| Field | Value (source) |
|---|---|
| Locus | L55168 (label CUL9), **L3**, log10BF_independent 0.3679, rank 24 (10–82); G&C z 1.96 |
| Matrix | classes **ENHANCER_LINK; QTL** (2); gene_class CAUSAL_GENE_MODERATE; direction **D4** (UNRESOLVED, 1 row, 1 unit, LOWER); P5; developmental_class MIXED; rank B 4, rank E 19, rank A 24, rank C 22. Other genes: DNPH1 (ENHANCER_LINK;QTL, MODERATE, rank B 3), CUL9, SLC22A7, CRIP3 (ENHANCER_LINK, weak) |
| Class change | Sprint 5: V2G_SUPPORTED_WEAK_LOCUS, ENHANCER_LINK, D5, rank B 26 → Sprint 5A: CAUSAL_GENE_MODERATE, ENHANCER_LINK;QTL, D4, rank B 4 (`class_changes.csv`) |
| Single-cell coloc | SingleBrain: oligodendrocyte **0.862** (1 strong row, coloc.abf, LOWER at rs111342015), excitatory 0.766, microglia 0.160, others < 0.04. Bryois: oligodendrocyte 0.141, all others < 0.07. Bulk: UNRESOLVED_NO_STRONG_COLOC |
| Competitor (single-cell) | DNPH1: SingleBrain excitatory **0.927**, inhibitory 0.855, oligodendrocyte 0.798 (LOWER; agrees with bulk). SRF 0.581, CUL9 0.553 |
| Variant table | rs16868993 PIP 0.284; rs111342015 PIP 0.264 (E2G → TTBK1). `largest_contradiction`: "single-cell direction disagrees with bulk" (`variant_gene_cell_hypotheses.parquet`) |
| Fine-mapping (5A) | **No credible set** in any Sprint-5A run. Plain SuSiE 1000G: 0 CS, top rs78652437 PIP 0.091. PolyFun: 0 CS, top rs75187159 0.148. UKB-LD plain: 0 CS, top rs111342015 0.087 (`functional_finemapping_summary.csv`). The table PIPs above (0.28/0.26) come from the integrated variant table and are not re-derived here |
| Timing | UNKNOWN (no devBrain, GTEx V11 or brainSCOPE evidence for TTBK1) |
| Multi-trait coloc | L55168 ALL: COG + DNPH1@ROSMAP + PTK7@ROSMAP, posterior 0.525, rs7832. TTBK1 was not a trait (no bulk coloc). GWAS-only: no cluster |
| LAVA | L55168 Davies–Zabaneh rho 0.029, p 0.88 |
| brainSCOPE / AlphaGenome / GTEx V11 | no TTBK1 rows |
| Constraint (gnomAD v4) | pLI 1.0, LOEUF 0.417, mis_z 2.86 |

## 3. Three questions, kept separate

- **A. Is TTBK1 a causal cognition gene? Not shown.** Only overexpression models exist:
  - human TTBK1 transgene → spatial learning impairment and reduced NMDA receptor expression (Sato 2008);
  - adult-onset pan-neuronal expression → cerebellar degeneration and cognitive and motor deficits (McMillan 2020).
  Both are MECHANISTIC_ONLY and are not inverted into "less TTBK1 improves cognition".
- **B. Natural high-cognition locus? Weak (L3; G&C z 1.96).**
- **C. Adult-modifiable? Partial, single unit (D4).** One oligodendrocyte row gives cognition-increasing allele → LOWER TTBK1.

## 4. Causal chain

- **credible variants → element (E2G → TTBK1 at rs111342015).** EVIDENCED as one enhancer link; the variant PIP is 0.26.
- **element → TTBK1 expression.** Weakly EVIDENCED: one coloc row in one cell type in one resource.
  - The dominant expression signal at the locus is DNPH1 (4 non-positional layers, 2 bulk cohorts, prenatal coloc).
  - TTBK1 has 2 layers.
- **TTBK1 → cell type.** INFERRED and contradictory. The coloc cell type is oligodendrocyte, but TTBK1 is described as neuron-specific (cortical/hippocampal neurons; Sato 2006).
  - Excitatory neurons reach only 0.766.
  - An oligodendrocyte-only eQTL for a neuronal kinase needs checking; low oligodendrocyte expression can inflate apparent effects.
- **cell → function.** MISSING for physiological dosage. Published data are from overexpression or disease.
- **direction (LOWER) → cognition.** INFERRED at most. It is coherent with the overexpression models, but that is not evidence that physiological reduction helps.

## 5. Red-team

| Source | Claim | Category | Shares data? |
|---|---|---|---|
| Sato 2006, *J Neurochem* PMID 16923168 doi:10.1111/j.1471-4159.2006.04059.x | TTBK1 is a neuron-specific tau kinase that phosphorylates and aggregates tau | MECHANISTIC_ONLY | No |
| Sato 2008, *J Neurosci* PMID 19118186 doi:10.1523/JNEUROSCI.3417-08.2008 | Human TTBK1 transgenic mice: age-dependent spatial learning impairment, CDK5/p35 activation, NMDA receptor downregulation | MECHANISTIC_ONLY (overexpression) | No |
| McMillan 2020, *Acta Neuropathol Commun* PMID 33228809 doi:10.1186/s40478-020-01073-7 | Adult-onset pan-neuronal TTBK1 → severe cerebellar neurodegeneration with motor and cognitive phenotypes | MECHANISTIC_ONLY | No |
| Taylor 2018, *Mol Neurodegener* PMID 29409526 doi:10.1186/s13024-018-0237-9 | TTBK1/2 phosphorylate TDP-43 and tau and drive neurodegeneration | DISEASE_ONLY / MECHANISTIC_ONLY | No |
| Vázquez-Higuera 2011, *Neurobiol Aging* PMID 20096481 doi:10.1016/j.neurobiolaging.2009.12.021; Yu 2011 PMID 21219968 | TTBK1 SNPs (rs2651206, rs7764257) associated with late-onset AD (Spanish, Han Chinese candidate-gene studies) | DISEASE_ONLY (small candidate studies) | No |
| Bashore 2023, *Sci Rep* PMID 37059819 doi:10.1038/s41598-023-32854-4 | TTBK1 and TTBK2 modulation affects ciliogenesis | MECHANISTIC_ONLY | No |
| Our Sprint-5A single-cell coloc | DNPH1 is stronger (0.927 excitatory, 2 strong rows, agreeing with bulk and prenatal) | CONTRADICTING (alternative gene) | Same SingleBrain donors |
| Our HyPrColoc | Cognition clusters with the DNPH1 and PTK7 eQTLs (0.525) | CONTRADICTING / NON-INDEPENDENT | Same GWAS |
| Sprint-5 DNPH1 dossier | DNPH1 has no brain literature; TTBK1 is the neuron-specific neighbour | SUPPORTING (plausibility only) | n/a |

No independent human perturbation evidence links TTBK1 to cognition at physiological dosage.

## 6. Modifiability characterisation (facts only)

- **Protein.** Serine/threonine kinase of the casein kinase 1 superfamily (1,321 aa, UniProt Q5TCY1). Two isoforms.
  - It phosphorylates tau (e.g. Ser422) and TDP-43.
  - Expression is CNS-enriched: HPA "group enriched" brain 14.5 nTPM, pituitary 7.2; GTEx adult brain median 8.26 TPM.
- **Structure.** Kinase-domain crystal structures, apo and with inhibitors (e.g. PDB 4BTJ, 4BTK, 4BTM, 4NFM, 4NFN, 7JXX, 7Q8V, 7ZHN; Kiefer 2014 PMID 24637750).
- **Known modulators (fact only, not recommendations).**
  - Research-stage small-molecule TTBK1 inhibitors are reported:
    - selective brain-penetrant compounds in a TDP-43 model (Sanchez-Santos 2026, PMID 42593908 doi:10.1021/acs.jmedchem.6c01882);
    - acute tau-phosphorylation lowering (Dillon 2020, PMID 32255788).
  - An antisense oligonucleotide reduced hippocampal phospho-tau in PS19 mice (Yukawa 2023, PMID 37853497).
  - We found no approved drug or registered clinical candidate.
- **Location.** Intracellular.

## 7. Pleiotropy and safety

- **Constraint.** High: pLI 1.0, LOEUF 0.417, mis_z 2.86. Reduced dosage is selected against in humans. This is a caution against reading "lower TTBK1" as benign.
- **Paralog.** TTBK2 is the paralog; heterozygous TTBK2 mutations cause spinocerebellar ataxia type 11. Ciliogenesis is the documented cross-reactivity concern for non-selective inhibition (published).

## 8. Largest contradiction

The frozen rules promote TTBK1 on one oligodendrocyte colocalisation row, for a gene described as neuron-specific.

Four things point the other way:
- the Bryois oligodendrocyte value for the same gene is 0.141;
- the neighbouring gene DNPH1 has stronger and multi-source expression colocalisation (bulk, prenatal, SingleBrain excitatory and inhibitory neurons);
- HyPrColoc clusters cognition with DNPH1, not TTBK1;
- no Sprint-5A fine-mapping run produced a credible set.

The MODERATE label is legal but could come from a single noisy row.

## 9. Missing arrow and single best next COMPUTATION

- **Missing.** A second, independent expression signal for TTBK1 at this haplotype.
- **Next computation.**
  - Run coloc.susie for TTBK1 in the SingleBrain per-cohort betas (Fujita, Mathys and Gabitto separately; columns beta/sd_tissue_0–2 in the files already extracted), and in GTEx V11 brain tissues.
  - Then run HyPrColoc with DNPH1 and TTBK1 as joint traits.
- **What would move the call.** If TTBK1 fails in two of three independent SingleBrain sub-cohorts, the QTL class should be treated as not replicated (flag, not an edit).
