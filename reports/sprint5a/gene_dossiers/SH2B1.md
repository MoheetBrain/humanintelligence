# SH2B1 — gene dossier (Sprint 5A, new gene)

Scope: this dossier characterises the gene and appraises the evidence. Nothing here designs, doses or recommends an intervention; known modulators are listed as facts only.
Written 2026-09-24 (UTC). Our numbers are copied from the Sprint-5A outputs and are not changed here.
Companion dossier for the same locus: `reports/sprint5/gene_dossiers/TUFM.md` (Sprint 5).

## 1. Verdict

**LOCUS_HIGH_GENE_UNRESOLVED (L51327, stratum L1, locus rank 1, interval 1–17). Of the seven 16p11.2 genes that now carry a class, SH2B1 is the best-supported candidate, but it has not been shown to be the effector.**

SH2B1 is the only gene at our strongest locus whose direction agrees across all four sources:
- single-nucleus colocalisation (12 strong rows, two resources);
- brainSCOPE (9 cell types);
- GTEx V11 (3 brain tissues);
- an independent mouse perturbation of hippocampal ERK and working memory (Du 2023).

Four things keep it from being called the causal gene:
- the credible set is diffuse (63 variants; top plain PIP 0.106 at rs4072401, and only 0.039 at the lead rs62037363);
- the haplotype block spans about 1 Mb;
- five other genes colocalise with the same lead;
- the two single-nucleus resources are not independent of each other (SingleBrain includes the Bryois donors, and both include ROSMAP), so they count as one cohort unit.

In Sprint 5, SH2B1 had no class. It is now `QTL` (D3). The class label is unchanged.

## 2. Our computed evidence (unchanged numbers)

| Field | Value (source) |
|---|---|
| Locus | L51327, **L1**, log10BF_independent 1.24, locus rank 1 (1–17), gc_aligned_z 3.441, Zabaneh aligned z 2.43 (sensitivity; HRS overlap), GenLang PIQ aligned z 0.587 (`locus_confidence_rank.csv`) |
| Matrix | classes **QTL** (n = 1); gene_class LOCUS_HIGH_GENE_UNRESOLVED; direction D3 (RESOLVED_ON_ROWS_ONLY_NOT_ROBUST, 12 rows, 1 cohort unit); perturbation P5; rank B 9, **rank E 1**, rank A 1, rank C 4, rank D 36. Other genes with classes: AC138894.1, EIF3C, LAT, NFATC2IP, NPIPB9, TUFM (`causal_gene_evidence_matrix.csv`) |
| Class change | Sprint 5: no class, D4 → Sprint 5A: QTL, D3 (`class_changes.csv`) |
| Single-cell coloc | best PP.H4 0.886; 12 strong rows. Bryois: excitatory 0.886, pseudo-bulk 0.855, inhibitory 0.839. SingleBrain: inhibitory 0.886, astrocyte 0.871, excitatory 0.863. Every strong row: cognition-increasing allele → **HIGHER** SH2B1 (6 of 6 coloc.susie rows at rs62037363). Bulk Sprint-4: UNRESOLVED_NO_STRONG_COLOC (`sc_eqtl_coloc_summary.csv`) |
| brainSCOPE | DIRECT_VARIANT_GENE_OVERLAP + CELL_SPECIFIC_QTL_SUPPORT in Astro, Chandelier/Pvalb, Endo/VLMC, L2/3 IT, L6 CT, Lamp5, Lamp5.Lhx6, PC, Sncg; all HIGHER (consistency 1.0). STARR enhancer variant: yes; CRISPR-validated: no; coloc NOT_TESTABLE_WITH_PUBLIC_OUTPUT (`brainscope_gene_summary.csv`) |
| GTEx V11 | 3 brain tissues (cerebellar hemisphere, cerebellum, hypothalamus), all HIGHER; max V11 SuSiE PIP of a query variant 0.042 |
| Timing | ADULT (QTL overlap only). No prenatal devBrain coloc; direction consistent across stages (`regulatory_timing.csv`) |
| Fine-mapping | plain SuSiE (1000G): one CS of 63 variants, top rs4072401 PIP 0.106; rs62037363 0.039. The SH2B1 missense rs7498665 (p.Thr484Ala) is in the CS at PIP 0.009 (plain) / 0.051 (PolyFun) — below the CODING threshold of 0.1 (`functional_finemapping*.csv`) |
| Multi-trait coloc | ALL run: COG + TUFM/EIF3C/NPIPB9 eQTLs, posterior 0.557, candidate rs62037363 (SNP posterior 0.04). SH2B1 was not an eQTL trait there (no Sprint-4 bulk coloc). GWAS-only: no cluster (`multitrait_coloc.csv`) |
| LAVA | L51327 Davies–UKB FI4 rho 0.14, p 0.52 (`lava_bivariate_core5.csv`) |
| AlphaGenome | no SH2B1 rows |
| Constraint (gnomAD v4 API) | pLI 1.0, LOEUF 0.369, mis_z 1.21 |

## 3. Three questions, kept separate

- **A. Is SH2B1 a causal cognition gene? Partially supported, and not by human perturbation of cognition.**
  - Human haploinsufficiency (the distal 16p11.2 BP2–BP3 deletion, rare LoF) causes obesity, insulin resistance, developmental delay and maladaptive behaviour. That is DISEASE_ONLY evidence and is not inverted into an enhancement claim.
  - The one cognition-specific perturbation is in mice: hippocampal Sh2b1 deletion impaired working memory (Du 2023).
- **B. Is L51327 a natural high-cognition locus? Yes, at locus level (L1; replicated in G&C).** The gene assignment within the locus remains unresolved.
- **C. Is it adult-modifiable? Near-resolved on rows only.**
  - In adult cortex, the cognition-increasing allele raises SH2B1 in neurons and astrocytes (single-nucleus, brainSCOPE, GTEx V11).
  - This counts as one cohort unit, so the frozen rule reads D3, not D2.

## 4. Causal chain

- **credible variants → regulatory element.** INFERRED. The CS is diffuse (63 variants, top PIP 0.106). A STARR-active variant exists in brainSCOPE but is not tied to one element.
- **regulatory element → SH2B1 expression.** EVIDENCED at eQTL level (12 single-nucleus coloc rows, 9 brainSCOPE cell types, 3 GTEx V11 tissues, all HIGHER). The same haplotype is also a colocalising eQTL for TUFM, NPIPB9, NFATC2IP, LAT and AC138894.1.
- **SH2B1 expression → cell type.** EVIDENCED as descriptive: excitatory and inhibitory neurons and astrocytes, but not microglia or oligodendrocytes (PP.H4 < 0.05).
- **cell type → circuit function.** INFERRED, from mouse work only: Sh2b1 loss in hippocampal inhibitory neurons raises ERK signalling and impairs working memory (Du 2023).
- **direction (higher SH2B1 ↔ cognition-increasing allele) → cognition.** INFERRED. It is coherent with the mouse loss-of-function direction, but no human dosage study exists at common-variant scale.
- **SH2B1 → cognition.** MISSING in humans; this is the arrow that matters.

## 5. Red-team

| Source | Claim | Category | Shares data? |
|---|---|---|---|
| Du 2023, *Research* PMID 38434247 doi:10.34133/research.0269 | UKB fluid-intelligence GWAS: SH2B1 variation affects fluid intelligence independently of metabolism, partly mediated by hippocampal volume. Hippocampal inhibitory-neuron Sh2b1 deletion impairs working memory; ERK inhibition reverses it | SUPPORTING (human arm) + MECHANISTIC_ONLY (mouse arm) | Human arm is UKB (**shares data with Davies**). Mouse arm is independent |
| Doche 2012, *JCI* PMID 23160192 doi:10.1172/JCI62696 | Rare SH2B1 LoF: hyperphagia, early obesity, insulin resistance, reduced height, and social isolation and aggression | DISEASE_ONLY | No |
| Pearce 2014, *Endocrinology* PMID 24971614 doi:10.1210/en.2014-1264 | Variants in the N-terminal region common to all isoforms impair SH2B1β-enhanced NGF neurite outgrowth, with mild developmental delay. α-isoform-only variants give hyperinsulinaemia without the behavioural phenotype | MECHANISTIC_ONLY / DISEASE_ONLY | No |
| Bachmann-Gagescu 2010, *Genet Med* PMID 20808231 doi:10.1097/GIM.0b013e3181ef4286; Bochukova 2010, *Nature* PMID 19966786 doi:10.1038/nature08689 | Distal 16p11.2 (~200 kb, incl. SH2B1) deletions: developmental delay plus obesity. The deletion covers ATXN2L, TUFM, SH2B1, ATP2A1, LAT and others | DISEASE_ONLY (multi-gene CNV) | No |
| Xu 2026, *Mol Genet Genomic Med* PMID 42764254 doi:10.1002/mgg3.70306 | Five rare monoallelic SH2B1 variants (4 de novo) with DD/ID/ASD and hyperphagia; missense variants raise EGF-induced ERK phosphorylation in vitro | DISEASE_ONLY | No |
| Jiang 2018, *FASEB J* PMID 29180441 doi:10.1096/fj.201700831R | Brain-specific Sh2b1 KO: reduced brain weight and increased aggression | MECHANISTIC_ONLY | No |
| Chen 2015, *JBC* PMID 25586189 doi:10.1074/jbc.M114.603795 | SH2B1β (the dominant isoform in hippocampal neurons) and IRSp53 promote dendrite formation and branching | MECHANISTIC_ONLY | No |
| Willer 2009, *Nat Genet* PMID 19079261 doi:10.1038/ng.287 | The SH2B1 region is a BMI locus (lead includes missense rs7498665) | NON-INDEPENDENT (pleiotropy) | Same haplotype |
| Volckmar 2015 (cited in TUFM dossier) PMID 25955518 | The BMI SNP tags a ~1 Mb block with r² > 0.7 | CONTRADICTING (resolution) | Same haplotype |
| Our Sprint-5A single-nucleus coloc | TUFM is also strong (6 rows, HIGHER, which **disagrees** with bulk TUFM LOWER) | CONTRADICTING (alternative gene) | Same ROSMAP donors |
| Ren 2007, *JCI* PMID 17235396 doi:10.1172/JCI29417 | Neuronal SH2B1 is required for energy and glucose homeostasis | DISEASE_ONLY (metabolic) | No |

Rows 1 and 8 share UKB/BMI-era data with the discovery GWAS. Only the mouse arms (rows 1, 6 and 7) are independent perturbations, and none of them is human.

## 6. Modifiability characterisation (facts only)

- **Protein.** Cytoplasmic SH2/PH-domain adaptor (756 aa, UniProt Q9NRF2). It enhances JAK2 and receptor tyrosine kinase signalling downstream of the leptin, insulin, GH, NGF, BDNF and GDNF receptors.
- **Isoforms.** Four splice isoforms: α and δ are mainly brain-expressed; β and γ are ubiquitous (Argetsinger 2023, PMID 36799031 doi:10.1210/endocr/bqad032).
- **Expression.** HPA: low tissue specificity. GTEx adult brain median 23.15 TPM.
- **Structure.** Isolated domain structures exist (e.g. the SH2 domain with JAK2 peptide). No full-length structure was found.
- **Known modulators (fact only).** No SH2B1-directed small molecule, probe or clinical compound was found. One case report describes setmelanotide (an MC4R agonist acting downstream in the leptin–melanocortin pathway, not on SH2B1) in an adult carrying an SH2B1 variant (PMID 39284294 doi:10.1159/000541267). It is recorded as a fact about the pathway, not as SH2B1 modulation.
- **Location.** Intracellular adaptor, not extracellular.

## 7. Pleiotropy and safety

- **Constraint.** High: pLI 1.0, LOEUF 0.369, so haploinsufficiency is not tolerated. Heterozygous LoF causes obesity, insulin resistance, reduced adult height, and behavioural and developmental phenotypes.
- **Locus pleiotropy.** Very pleiotropic: BMI/obesity, T2D, lipids, fatty liver, and fluid intelligence.
- **Allele direction.** The BMI-risk allele at rs7498665 in published GWAS is G (Ala484). In Davies, the cognition-increasing allele at that SNP is A (z = +8.674). The locus therefore appears to link higher cognition with lower BMI. This allele mapping is INFERRED from published allele conventions and was not re-derived here.

## 8. Largest contradiction

At the same credible variants, TUFM, NPIPB9, NFATC2IP, LAT and AC138894.1 also colocalise strongly. For TUFM, the single-nucleus direction (HIGHER) disagrees with the bulk direction (LOWER; GTEx hippocampus and ROSMAP DLPFC), even though the donors overlap.

With a 63-variant credible set and ~1 Mb LD, colocalisation cannot separate these genes. SH2B1's lead rests on convergence of direction and on independent biology (mouse), not on statistical resolution.

## 9. Missing arrow and single best next COMPUTATION

- **Missing.** Which 16p11.2 gene carries the cognition effect.
- **Next computation.** Run multi-gene fine-mapping of the L51327 expression signals, jointly across the seven colocalising genes:
  - cTWAS or FOCUS on the SingleBrain excitatory/inhibitory/astrocyte z-scores, with one LD reference (UKB LD);
  - add SH2B1 as an eQTL trait in HyPrColoc alongside TUFM/EIF3C/NPIPB9.
- **What would change the call.** If SH2B1 took the gene-level PIP (≥ 0.5) while TUFM's collapsed, the locus would have a single effector candidate. If the PIP stayed split, the locus remains gene-unresolved.
