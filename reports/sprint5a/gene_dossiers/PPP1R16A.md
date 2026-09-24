# PPP1R16A — gene dossier (Sprint 5A, new gene)

Scope: this dossier characterises the gene and appraises the evidence. Nothing here designs, doses or recommends an intervention; known modulators are listed as facts only.
Written 2026-09-24 (UTC). Our numbers are copied from the Sprint-5A outputs and are not changed here.
Companion dossiers for the same locus: `reports/sprint5/gene_dossiers/KIFC2.md`, `ZFTRAF1.md` (Sprint 5), and the KIFC2 Sprint-5A addendum.

## 1. Verdict

**CAUSAL_GENE_MODERATE under the frozen rules (L65265, stratum L3, locus rank 22, interval 7–99). PPP1R16A is tied with KIFC2 for the lead at a weak, gene-dense 8q24.3 locus, and the gene is not identified.**

For:
- PPP1R16A has 8 strong single-nucleus colocalisation rows across both resources: Bryois excitatory neurons and pseudo-bulk; SingleBrain excitatory neurons and microglia; best PP.H4 0.987.
- Every row is in one direction: the cognition-increasing allele gives HIGHER PPP1R16A.

Against:
- At the same lead variant (rs750472, a FOXH1 5′UTR SNP), ZFTRAF1 (0.991, 12 rows), KIFC2 (0.979), LRRC24 (0.903) and RECQL4 (0.892) also colocalise.
- Their directions differ: ZFTRAF1, KIFC2 and RECQL4 go LOWER; PPP1R16A and LRRC24 go HIGHER.
- That is the signature of one shared regulatory haplotype that moves several neighbouring genes, and colocalisation cannot pick among them.
- The literature on PPP1R16A in brain is essentially absent.

## 2. Our computed evidence (unchanged numbers)

| Field | Value (source) |
|---|---|
| Locus | L65265 (label FOXH1), **L3**, log10BF_independent 0.3795, rank 22 (7–99); G&C z 1.67; Zabaneh aligned z −0.00 (`locus_confidence_rank.csv`, variant table) |
| Matrix | classes **ENHANCER_LINK; QTL** (2); CAUSAL_GENE_MODERATE; direction **D3** (RESOLVED_ON_ROWS_ONLY_NOT_ROBUST, 8 rows, 1 cohort unit, HIGHER); P5; developmental_class MIXED; **rank B 2**, **rank E 3**, rank A 22, rank C 4. Others: KIFC2 (ENHANCER_LINK;QTL, rank B 1), FOXH1 (ENHANCER_LINK), ZFTRAF1, RECQL4, LRRC24 (QTL; LIKELY_QTL_PASSENGER) |
| Class change | Sprint 5: V2G_SUPPORTED_WEAK_LOCUS (ENHANCER_LINK, D5, rank B 24) → Sprint 5A: CAUSAL_GENE_MODERATE (ENHANCER_LINK;QTL, D3, rank B 2) |
| Single-cell coloc | Bryois: excitatory **0.935**, pseudo-bulk 0.896, glia < 0.09. SingleBrain: microglia **0.987**, excitatory **0.941**, inhibitory 0.763, oligodendrocyte 0.711, OPC 0.320. 8 strong rows, all HIGHER (coloc.susie hit rs750472 in all four susie rows). Sprint-4 bulk: no strong coloc |
| brainSCOPE | REGULATORY_ELEMENT_SUPPORT + GRN_SUPPORT only (20 cell types); **no allelic evidence**; coloc NO_QTL_EVIDENCE_TO_TEST |
| Timing | UNKNOWN (no devBrain, GTEx V11 or bulk-coloc evidence for PPP1R16A) |
| GTEx V11 | no PPP1R16A row |
| AlphaGenome | rs11777703: EXPRESSION_RNA_SEQ, strong in 10/20 brain tracks (max quantile 0.998; top: substantia nigra), predicted **UP**. Comparators are SECONDARY_OT only: 2 of 3 DISAGREE (observed DOWN), 1 AGREE |
| Fine-mapping | plain SuSiE 1000G: one CS of 38, top **rs750472** PIP 0.151 (FOXH1 5′UTR); PolyFun: CS 23, top rs11777703 0.345; rs11542372 (CYHR1/ZFTRAF1 ncRNA exon) 0.053. Variant table lists rs2291133 PIP 0.848 and rs11774212 0.721 (integrated source, not re-derived) |
| Multi-trait coloc | ALL: COG + ZFTRAF1@ROSMAP + RECQL4@CommonMind + KIFC2@ROSMAP, posterior 0.803, rs750472 (SNP posterior 0.468). PPP1R16A was not a trait (no Sprint-4 bulk coloc). GWAS-only: no cluster |
| LAVA | no bivariate row for L65265 in the output |
| Constraint (gnomAD v4) | pLI 0.0, LOEUF 1.092, mis_z −0.98 (unconstrained) |

## 3. Three questions, kept separate

- **A. Is PPP1R16A a causal cognition gene? Not shown.** No human or animal perturbation linking PPP1R16A to brain function was found.
- **B. Natural high-cognition locus? Weak (L3; G&C z 1.67; Zabaneh 0.00).**
- **C. Adult-modifiable? Rows only (D3).** Adult neurons and microglia show cognition-increasing allele → HIGHER PPP1R16A. This is one cohort unit, and the opposite direction holds for three neighbouring genes at the same SNP.

## 4. Causal chain

- **credible variants (rs750472 / rs11777703 / rs11542372; CS of 23–38) → regulatory element.** INFERRED. The lead is a FOXH1 5′UTR variant; ENHANCER_LINK classes exist for PPP1R16A, KIFC2 and FOXH1.
- **element → PPP1R16A expression.** EVIDENCED (8 single-nucleus rows, 2 resources, HIGHER). It is equally EVIDENCED for ZFTRAF1 (LOWER) and KIFC2 (LOWER).
- **PPP1R16A → cell type.** EVIDENCED as descriptive: excitatory neurons and microglia. The spread across cell types (5 types ≥ 0.7 in SingleBrain) looks like a haplotype effect, not a cell-specific one.
- **cell → function.** MISSING. The known function (PP1 regulatory subunit, membrane-anchored; inhibits PP1 toward myosin and phosphorylase) has no neural study.
- **direction → cognition.** MISSING.

## 5. Red-team

| Source | Claim | Category | Shares data? |
|---|---|---|---|
| Skinner 2001, *Biochem J* PMID 11336659 doi:10.1042/0264-6021:3560257 | Cloning of MYPT3 (PPP1R16A): a prenylated, membrane-targeted PP1 myosin-targeting subunit | MECHANISTIC_ONLY | No |
| Yong 2006, *JBC* PMID 16920702 doi:10.1074/jbc.M607287200 | PKA phosphorylates MYPT3 and regulates PP1 activity | MECHANISTIC_ONLY | No |
| Sueyoshi 2008, *Mol Pharmacol* PMID 18202305 doi:10.1124/mol.107.042960 | PPP1R16A, the membrane subunit of PP1β, signals nuclear translocation of the CAR receptor (liver) | MECHANISTIC_ONLY (non-brain) | No |
| Wang 2024, *Brief Bioinform* PMID 39406522 | Brain transcription/methylation multi-omics for ADHD lists PPP1R16A | NON-INDEPENDENT / DISEASE_ONLY (not verified beyond the abstract search) | Brain QTL resources likely overlap |
| Our Sprint-5A single-cell coloc | ZFTRAF1 0.991 (12 rows, LOWER), KIFC2 0.979 (LOWER), RECQL4 0.892 (LOWER) at the same SNP | CONTRADICTING (alternative genes, opposite directions) | Same donors |
| Our HyPrColoc | Cognition clusters with ZFTRAF1, RECQL4 and KIFC2 (0.803), and PPP1R16A was not testable as a trait | NON-INDEPENDENT | Same GWAS |
| AlphaGenome vs OT | Predicted UP; OT secondary comparators mostly DOWN | CONTRADICTING (weak; secondary tier) | n/a |
| Sprint-5 KIFC2 dossier | The KIFC2 knockout mouse shows no overt phenotype; no cognition literature | CONTRADICTING the alternative (weakens KIFC2 as well) | n/a |

No brain-specific functional literature for PPP1R16A was found (PubMed title/abstract search; UniProt Q96I34 function by similarity only).

## 6. Modifiability characterisation (facts only)

- **Protein.** Protein phosphatase 1 regulatory subunit 16A (MYPT3; 528 aa, UniProt Q96I34).
  - Structure: ankyrin repeats and a C-terminal CAAX prenylation motif.
  - Membrane-anchored; inhibits PP1 toward phosphorylase and myosin substrates (by similarity).
- **Expression.** HPA: low tissue specificity, plasma membrane. GTEx adult brain median 31.48 TPM.
- **Structure.** No experimental structure listed in UniProt.
- **Known modulators (fact only).** None specific found. General PP1/PKA pathway tools exist but are not PPP1R16A-directed.
- **Location.** Membrane, cytoplasmic face; not extracellular.

## 7. Pleiotropy and safety

- **Constraint.** Unconstrained (pLI 0, LOEUF 1.09); no Mendelian disease.
- **Locus neighbours.** RECQL4 LoF causes Rothmund–Thomson, Baller–Gerold and RAPADILINO syndromes. FOXH1 is a developmental TF. They share the haplotype, so any locus-level effect cannot be attributed to PPP1R16A.
- **Other species.** In cattle, PPP1R16A variants are proxies (Akiyama 2025, PMID 41009945) for the DGAT1 milk-fat locus (LD artefact in another species). This is not relevant to human biology, but it shows how often this gene is assigned positionally.

## 8. Largest contradiction

Five genes colocalise with one 8q24.3 haplotype at PP.H4 ≥ 0.89, in two opposite directions. PPP1R16A's rank B 2 comes from class counting (QTL + ENHANCER_LINK), which KIFC2 also satisfies. ZFTRAF1 has the strongest and most replicated colocalisation but only one class. The ranking is a property of the classification rules, not evidence that PPP1R16A is causal.

## 9. Missing arrow and single best next COMPUTATION

- **Missing.** Which of the 8q24.3 genes mediates the cognition signal.
- **Next computation.** Multi-gene fine-mapping of the expression signals at L65265 (FOCUS or cTWAS) using SingleBrain excitatory and microglia z-scores for PPP1R16A, ZFTRAF1, KIFC2, RECQL4 and LRRC24 together, with UKB LD. Also add PPP1R16A as a HyPrColoc eQTL trait from SingleBrain.
- **What would move the call.** If gene PIP concentrated on one gene (≥ 0.5), the tie would break. If not, the locus stays gene-unresolved in practice, whatever the class labels say.
