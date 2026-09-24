# GNL3 — gene dossier (Sprint 5A, new gene)

Scope: this dossier characterises the gene and appraises the evidence. Nothing here designs, doses or recommends an intervention; known modulators are listed as facts only.
Written 2026-09-24 (UTC). Our numbers are copied from the Sprint-5A outputs and are not changed here.
Locus note: L51460 (SFMBT1 label) and L91869 (NT5DC2 label) overlap on 3p21.1 and share one signal (lead rs6778735 in both). They are **not** two independent loci. Companion dossier: `reports/sprint5/gene_dossiers/NT5DC2.md`.

## 1. Verdict

**LOCUS_HIGH_GENE_UNRESOLVED (L51460, stratum L2, locus rank 4, interval 1–46). GNL3 is a credible, mainly developmental candidate at a gene-dense psychiatric locus. It is not established.**

For:
- GNL3 now carries the only QTL class at the locus (Bryois single-nucleus coloc: pseudo-bulk 0.958, inhibitory neurons 0.871).
- Prenatal-brain colocalisation is strong (devBrain PP.H4 0.98).
- GTEx V11 shows the same direction in 12 of 12 brain tissues: the cognition-increasing allele gives LOWER GNL3.
- Published CRISPRi and organoid work ties this haplotype to GNL3 expression and neural progenitor proliferation (bipolar-disorder framing).

Against:
- The larger SingleBrain meta, which contains the Bryois donors, does not replicate strongly (inhibitory 0.537).
- HyPrColoc clustered cognition with the **NT5DC2** CommonMind eQTL, not the GNL3 ROSMAP eQTL.
- STAB1, NT5DC2 and UQCC5 each carry an ENHANCER_LINK class.

## 2. Our computed evidence (unchanged numbers)

| Field | Value (source) |
|---|---|
| Locus | L51460 (label SFMBT1), **L2**, log10BF_independent 0.8148, rank 4 (1–46), gc_aligned_z 2.805, Davies z −7.227. L91869 (label NT5DC2), L2, rank 3, gc_aligned_z 3.095 (`locus_confidence_rank.csv`) |
| Matrix (L51460) | classes **QTL** (1); LOCUS_HIGH_GENE_UNRESOLVED; direction **D3** (RESOLVED_ON_ROWS_ONLY_NOT_ROBUST, 6 rows, 1 cohort unit, majority LOWER); P5; developmental_class DEVELOPMENTAL; rank B 18, rank E 23, rank A 4, rank C 4. Others: STAB1, NT5DC2, UQCC5 (ENHANCER_LINK each) |
| Class change | Sprint 5: no class, D5 → Sprint 5A: QTL, D3 (`class_changes.csv`) |
| Single-cell coloc | Bryois: pseudo-bulk **0.958** (coloc.susie), inhibitory **0.871**, excitatory 0.338, glia < 0.05. SingleBrain: inhibitory 0.537, all others < 0.05. 3 strong rows, all Bryois, all **LOWER** (rs13081028 abf; rs6778735 susie). Sprint-4 bulk: UNRESOLVED_NO_STRONG_COLOC (`sc_eqtl_coloc_summary.csv`) |
| Competitors (single-cell) | NEK4 0.755, SPCS1 0.690, NT5DC2 0.639, GLT8D1 0.569; no other strong gene |
| Timing | **ADULT+DEVELOPMENTAL**. devBrain Wen 2024 coloc: EUR 0.98, Tri1 0.98, Tri2 0.89; prenatal direction **LOWER**; GTEx V11 LOWER; consistent across stages (`regulatory_timing.csv`) |
| GTEx V11 | 12 brain tissues significant, all LOWER; SuSiE credible sets in 11; max PIP of a query variant 0.186; min p 3e-23 |
| brainSCOPE | no GNL3 row (the brainSCOPE layer at this locus points to GLT8D1, ITIH4, PBRM1) |
| Fine-mapping | plain SuSiE (1000G): CS of 18 (L91869) / 21 (L51460) variants; top rs6778735 PIP 0.203 (NT5DC2 intron); rs13081028 0.089 (STAB1 intron). Coding variants rising under PolyFun: STAB1 rs7630214 and ITIH3 rs35271262 (≤ 0.15) |
| Multi-trait coloc | L51460 ALL: COG + NT5DC2@CommonMind, posterior 0.632, rs7636227. L91869 ALL: COG + NT5DC2 + GLYCTK, 0.262. **GNL3@ROSMAP was tested and did not cluster**. GWAS-only: no cluster |
| LAVA | L51460 Davies–FI4 rho 0.374, p 0.035 (UKB overlap) |
| AlphaGenome | no GNL3 rows |
| Constraint (gnomAD v4) | pLI 0.0, LOEUF 1.318 (LoF-tolerant in heterozygotes) |

## 3. Three questions, kept separate

- **A. Is GNL3 a causal cognition gene? Not shown.**
  - Evidence is at the eQTL level only, plus published psychiatric-framed perturbation in neural progenitors.
  - Mouse germline knockout is embryonic-lethal (peri-implantation). Neural-specific loss causes DNA damage and severe brain defects.
  - Both are DISEASE_ONLY/developmental evidence, and neither is inverted.
- **B. Natural high-cognition locus? Yes, moderate (L2, replicated in G&C).**
- **C. Adult-modifiable? Rows only (D3).** An adult signal is present (GTEx V11 and Bryois inhibitory neurons), but the strongest colocalisation is prenatal. This gene is more likely a developmental effector than an adult lever.

## 4. Causal chain

- **credible variants (rs6778735 / rs13081028 cluster) → regulatory element.** INFERRED.
  - No CODING variant; the lead is intronic in NT5DC2/STAB1.
  - Published: an Alu indel rs71052682 regulates transcription at 3p21.1 (Yang 2020). Luciferase and CRISPRi on bipolar-disorder eQTL SNPs rs10865973, rs12635140 and rs4687644 change GNL3 expression (Meng 2020). Our LD to these SNPs was not computed.
- **element → GNL3 expression.** EVIDENCED: prenatal PP.H4 0.98; adult Bryois 0.958/0.871; GTEx V11 12/12 LOWER.
- **GNL3 → cell type.** EVIDENCED, weakly: inhibitory neurons in Bryois only. Prenatal progenitors are INFERRED from the literature.
- **cell → neurodevelopment.** EVIDENCED in vitro (published): GNL3 knockdown or overexpression disturbs neural progenitor proliferation and differentiation in 2D cultures and forebrain organoids (Meng 2020).
- **direction (lower GNL3 ↔ cognition-increasing allele) → cognition.** MISSING. The published psychiatric-risk alleles at 3p21.1 "predict worse cognitive function" (Yang 2020), but their allele mapping to our Davies alleles was not checked.

## 5. Red-team

| Source | Claim | Category | Shares data? |
|---|---|---|---|
| Meng 2020, *Mol Psychiatry* PMID 32826963 doi:10.1038/s41380-020-00866-5 | Integrative analyses prioritise GNL3 for bipolar disorder. Luciferase and CRISPRi show BD eQTL SNPs regulate GNL3 in human neural progenitors. Knockdown and overexpression perturb proliferation and differentiation in 2D and organoid models | SUPPORTING (gene assignment at the shared haplotype) + MECHANISTIC_ONLY | PGC GWAS plus brain eQTL (partly ROSMAP/CMC) |
| Yang 2020, *Mol Psychiatry* PMID 31723243 doi:10.1038/s41380-019-0592-0 | 3p21.1 SCZ/BD risk alleles regulate NEK4, GNL3 and PBRM1. Risk alleles predict worse cognition. Manipulating NEK4/GNL3/PBRM1 reduces mushroom spines | SUPPORTING (locus–cognition) + CONTRADICTING (multi-gene: NEK4, PBRM1) | Brain eQTL datasets overlap ours |
| Yang 2018, *Nat Commun* PMID 29483533 doi:10.1038/s41467-018-03247-3 | GLT8D1 prioritised as the 3p21.1 schizophrenia gene | CONTRADICTING (alternative gene) | Brain eQTL (overlapping) |
| Li 2022, *Adv Sci* PMID 34978167 doi:10.1002/advs.202104786 | ITIH3 intronic rs2535629 alters CTCF binding and SFMBT1 expression | CONTRADICTING (alternative gene/variant) | No |
| Nakashima 2019/2020 PMIDs 31279527, 32778969 | NT5DC2 binds tyrosine hydroxylase and regulates catecholamine synthesis | CONTRADICTING (alternative gene with neurobiology) | No |
| Meng L 2013, *PNAS* PMID 23798389 doi:10.1073/pnas.1301672110 | Neural-specific nucleostemin KO → replication-associated DNA damage and severe embryonic brain defects | DISEASE_ONLY / MECHANISTIC_ONLY | No |
| Nomura 2009, *Stem Cells* PMID 19418458 doi:10.1002/stem.44 | Germline KO arrests at implantation. Loss reduces ES- and NSC-derived cell viability | DISEASE_ONLY | No |
| Wolter 2023, *Biol Psychiatry* PMID 36307327 doi:10.1016/j.biopsych.2022.08.014 | Cellular GWAS of lithium-induced proliferation in 80 genotyped human NPC lines. The hit locus is also associated with BD, SCZ and "interindividual differences in intelligence". GNL3 is the single gene with allele-specific, lithium-induced expression. CRISPRa of GNL3 raises proliferation; CRISPRi suppresses lithium-induced proliferation. LD between their lead and our rs6778735 was not verified | SUPPORTING (gene assignment, in vitro) + MECHANISTIC_ONLY | Independent donors (in vitro) |
| Qu 2026, *Hum Genomics* PMID 41699659 doi:10.1186/s40246-026-00920-3 | Higher GNL3 is causally protective for osteoarthritis (MR) | NON-INDEPENDENT (pleiotropy, same haplotype) | eQTL resources overlap |
| Our HyPrColoc | Cognition clusters with the NT5DC2 eQTL, not the GNL3 eQTL | CONTRADICTING | Same GWAS |

Rows 1–3 and 9 draw on overlapping brain eQTL resources and the PGC and Davies GWAS. The only independent perturbations are in vitro or mouse developmental models.

## 6. Modifiability characterisation (facts only)

- **Protein.** GNL3 (nucleostemin), a nucleolar GTP-binding protein (549 aa, UniProt Q9BVP2). Two isoforms.
  - It maintains stem/progenitor proliferation and genome stability.
  - It stabilises MDM2 and regulates TRF1 and ribosome biogenesis.
  - HPA classes it as "Essential proteins"; nucleolar localisation.
- **Expression.** Low tissue specificity; GTEx adult brain median 23.51 TPM.
- **Structure.** Many cryo-EM structures of pre-ribosomal particles include GNL3 (e.g. PDB 8FKP–8FL4, 8INK).
- **Known modulators (fact only).** No GNL3-selective small molecule, probe or clinical compound was found. Published reports of GTP depletion causing proteasomal turnover of nucleostemin describe a mechanism, not a modulator.
- **Location.** Not extracellular.

## 7. Pleiotropy and safety

- **Constraint.** LoF-tolerant in heterozygotes (pLI 0, LOEUF 1.32), but essential in development: homozygous mouse loss is embryonic-lethal.
- **Locus pleiotropy.** Schizophrenia, bipolar disorder, depression, osteoarthritis and other traits.
- **Cancer.** High GNL3 expression is a recurrent cancer-proliferation marker (hepatocellular, colon, breast). This is DISEASE_ONLY and not interpreted directionally.

## 8. Largest contradiction

Our own multi-trait analysis clustered cognition with NT5DC2 (CommonMind), and the GNL3 ROSMAP eQTL was left out. Meanwhile GNL3's single-nucleus colocalisation is strong only in the smaller Bryois set (n = 192) and is not reproduced strongly in SingleBrain (n = 757, which includes the Bryois donors).

The gene assignment therefore depends on which eQTL resource is used.

## 9. Missing arrow and single best next COMPUTATION

- **Missing.** Whether GNL3 or NT5DC2 (or NEK4/GLT8D1) carries the cognition signal.
- **Next computation.**
  - Run HyPrColoc and coloc.susie at L91869 with GNL3, NT5DC2, NEK4, GLT8D1 and SPCS1 as simultaneous traits from each resource separately: devBrain prenatal, CommonMind, ROSMAP, GTEx V11 cortex, SingleBrain inhibitory.
  - Add an LD check of rs6778735 against the published functional SNPs (rs10865973, rs12635140, rs4687644, rs71052682).
- **What would move the call.** A consistent winner across resources.
