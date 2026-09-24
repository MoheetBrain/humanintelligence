# FAM131A — gene dossier (Sprint 5A, new gene)

Scope: this dossier characterises the gene and appraises the evidence. Nothing here designs, doses or recommends an intervention; known modulators are listed as facts only.
Written 2026-09-24 (UTC). Our numbers are copied from the Sprint-5A outputs and are not changed here.

## 1. Verdict

**CAUSAL_GENE_MODERATE under the frozen rules (L8646, stratum L3, locus rank 30, interval 10–97). This is the most fragile of the Sprint-5A promotions.**

What changed in Sprint 5A:
- FAM131A moved from V2G_SUPPORTED_WEAK_LOCUS to CAUSAL_GENE_MODERATE (rank B 30 → 5).

What the promotion rests on:
- a Sprint-5 enhancer link;
- two single-nucleus colocalisation rows that are one test in one cell type in one resource (Bryois excitatory neurons, n = 192; coloc.abf 0.975 and coloc.susie 0.983; LOWER).

Why it is fragile:
- SingleBrain, which contains the Bryois donors plus about 560 more, gives only 0.324 in excitatory neurons.
- There is no bulk, GTEx V11, devBrain or brainSCOPE signal for FAM131A.
- CLCN2 colocalises at the same SNP (rs11920716): 4 strong rows, both resources, opposite sign, and a well-characterised brain disease gene. The frozen rules nonetheless label CLCN2 LIKELY_QTL_PASSENGER because it has one class.

FAM131A is a brain-enriched but essentially uncharacterised protein. The gene assignment at 3q27.1 is unresolved.

## 2. Our computed evidence (unchanged numbers)

| Field | Value (source) |
|---|---|
| Locus | L8646 (label CLCN2), **L3**, log10BF_independent 0.3256, rank 30 (10–97); G&C z 1.65; a math-53 SNP lies in the locus |
| Matrix | classes **ENHANCER_LINK; QTL** (2); CAUSAL_GENE_MODERATE; direction **D4** (UNRESOLVED, 2 rows, 1 unit, LOWER); P5; developmental_class ADULT_DYNAMIC; rank B 5, rank E 20, rank A 30, rank C 22. Other gene: CLCN2 (QTL; LIKELY_QTL_PASSENGER, rank B 60) |
| Class change | Sprint 5: V2G_SUPPORTED_WEAK_LOCUS (ENHANCER_LINK, D5, rank B 30) → Sprint 5A: CAUSAL_GENE_MODERATE (ENHANCER_LINK;QTL, D4, rank B 5). CLCN2: V2G_SUPPORTED_WEAK_LOCUS (rank B 31) → LIKELY_QTL_PASSENGER (rank B 60) |
| Single-cell coloc | Bryois: excitatory **0.983** (coloc.susie) / 0.975 (abf), pseudo-bulk 0.278. SingleBrain: excitatory **0.324**, others < 0.06. 2 strong rows, LOWER at rs11920716 |
| Competitor at same SNP | CLCN2: best 0.944 (SingleBrain oligodendrocyte). 4 strong rows: Bryois oligodendrocyte +, SingleBrain oligodendrocyte +, SingleBrain excitatory −. Overall MIXED, majority HIGHER, AGREE with bulk |
| Variant table | rs73189617 PIP 0.814; rs11920716 0.270 (integrated). `largest_contradiction`: "single-cell direction disagrees with bulk" |
| Fine-mapping (5A) | plain SuSiE 1000G: one CS of **5** variants, top rs11920716 PIP 0.270 (CLCN2/EIF2B5 intron); rs73189617 0.264. PolyFun: rs11920716 0.421 |
| Timing | UNKNOWN (no devBrain, GTEx V11 or bulk evidence for FAM131A) |
| brainSCOPE / GTEx V11 / AlphaGenome | no FAM131A rows |
| Multi-trait coloc | L8646 not in the HyPrColoc locus set |
| LAVA | L8646 Davies–Zabaneh rho 0.370 (0.046–0.745), p 0.030 (HRS-overlap caveat) |
| Constraint (gnomAD v4) | pLI 0.0, LOEUF 0.861, mis_z 2.10 (missense-constrained) |

## 3. Three questions, kept separate

- **A. Is FAM131A a causal cognition gene? Not shown.** No perturbation study of FAM131A exists in any organism (PubMed returned 4 unrelated hits).
- **B. Natural high-cognition locus? Weak (L3).**
  - Local rg with Zabaneh extreme IQ is nominal: rho 0.37, p 0.03. It overlaps HRS controls and is not an independent replication.
- **C. Adult-modifiable? Partial, single unit (D4).** One Bryois excitatory-neuron signal: cognition-increasing allele → LOWER FAM131A. It is not reproduced in the larger overlapping SingleBrain.

## 4. Causal chain

- **credible variants (5-variant CS; rs11920716 / rs73189617) → element.** INFERRED. The variants are intronic to CLCN2/EIF2B5; the enhancer link to FAM131A comes from Sprint 5.
- **element → FAM131A expression.** Weakly EVIDENCED: one cell type, one resource, not replicated in SingleBrain.
- **FAM131A → cell type (excitatory neurons).** INFERRED from a single resource. HPA shows brain enrichment (96.5 nTPM) but low cell-type specificity in single-nucleus brain.
- **cell → function.** MISSING; the protein function is unknown.
- **direction → cognition.** MISSING.

## 5. Red-team

| Source | Claim | Category | Shares data? |
|---|---|---|---|
| Our Sprint-5A single-cell coloc (SingleBrain) | FAM131A excitatory 0.324 in the 757-donor meta that includes the Bryois donors | CONTRADICTING (non-replication) | **Yes**: shares the Bryois donors |
| Our Sprint-5A single-cell coloc (CLCN2) | CLCN2 is strong at the same SNP in two resources, mainly in oligodendrocytes (+) | CONTRADICTING (alternative gene) | Same donors |
| Blanz 2007, *J Neurosci* PMID 17567819 doi:10.1523/JNEUROSCI.0338-07.2007 | ClC-2 disruption causes leukoencephalopathy (myelin vacuolation) in mice | MECHANISTIC_ONLY (supports CLCN2 as a white-matter gene) | No |
| Depienne 2013, *Lancet Neurol* PMID 23707145 doi:10.1016/S1474-4422(13)70053-X | Human ClC-2 deficiency causes white-matter oedema with variable cognitive and motor signs | DISEASE_ONLY (CLCN2) | No |
| Sprint-5 matrix (CLCN2 → LIKELY_QTL_PASSENGER) | Class-count rule demotes CLCN2 | NON-INDEPENDENT (same data) | n/a |
| HPA (proteinatlas.org ENSG00000175182) | FAM131A brain "tissue enhanced", 96.5 nTPM; subcellular location nucleolar rim / mitotic chromosome (antibody-based) | MECHANISTIC_ONLY (descriptive) | No |
| PubMed search (FAM131A / C3orf40) | 4 hits, all incidental (cancer autoantibody panel, methylation, gene fusion) | absence of evidence | n/a |

The first authors of rows 3 and 4 (Blanz 2007; Depienne 2013) were checked against PubMed esummary. The CLCN2 papers are listed only because CLCN2 is the alternative gene.

## 6. Modifiability characterisation (facts only)

- **Protein.** FAM131A (C3orf40), 366 aa, UniProt Q6UXB0. Three isoforms. No annotated function or domains in UniProt.
- **Expression.** HPA brain-enhanced. GTEx adult brain median 20.86 TPM.
- **Structure.** No experimental structure.
- **Known modulators.** None found.
- **Location.** Intracellular by HPA image annotation (nucleolar rim); not extracellular.

## 7. Pleiotropy and safety

- **Constraint.** Missense-constrained (mis_z 2.10), LoF-intolerance uncertain (LOEUF 0.861, pLI 0). No Mendelian disease.
- **Locus neighbours.**
  - CLCN2: recessive leukoencephalopathy with ataxia; dominant hyperaldosteronism with gain of function.
  - EIF2B5: vanishing white matter disease.
- The haplotype therefore sits among white-matter disease genes. That favours a glial mechanism (the CLCN2 oligodendrocyte signal) over a neuronal FAM131A one. This is INFERRED.

## 8. Largest contradiction

The promotion comes from a colocalisation that fails to replicate in a meta-analysis containing the same donors plus about 4× more. A competing gene with better replication at the same SNP (CLCN2) is labelled a passenger only because it has fewer classes.

## 9. Missing arrow and single best next COMPUTATION

- **Missing.** A replicated expression signal for FAM131A.
- **Next computation.** Run coloc.abf and coloc.susie for FAM131A and CLCN2 at L8646 on SingleBrain per-cohort betas (Fujita/ROSMAP, Mathys/ROSMAP, Gabitto/SEA-AD separately; `beta_tissue_0–2` columns already extracted in `data/interim/sprint5a/singlebrain/*__L8646.tsv`) and in GTEx V11 brain tissues.
- **What would move the call.** If FAM131A PP.H4 < 0.5 in all independent sub-cohorts, the QTL class would be a single-resource artefact. **Flag for class review; not edited here.**
