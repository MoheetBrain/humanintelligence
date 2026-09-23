# DNPH1 — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**CAUSAL_GENE_MODERATE (locus L55168, stratum L3).** DNPH1 leads a weak 6p21.1 locus on two classes: two adult-brain eQTL cohorts
and one enhancer link. We found no literature connecting DNPH1 to brain function or cognition. It is a well-characterised cancer
drug-discovery enzyme with a neuron-specific neighbour, TTBK1, in the same locus. The MODERATE call is technically correct under
our frozen rules, but it is biologically unanchored.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L55168 (MAGMA label CUL9), stratum **L3**, log10BF_independent 0.3679, locus rank 24 (10–82), gc_aligned_z 1.959, panel A |
| V2G classes | QTL (2) + ENHANCER_LINK (1). Other genes with classes: CRIP3, CUL9, SLC22A7, **TTBK1** (max 1 each) |
| QTL | Strong colocs in CommonMind and ROSMAP (2 rows, 2 cohort units, agreement 1.0) |
| Enhancer link | ENCODE-rE2G brain: rs111342015 → DNPH1 score 0.264 (the lowest E2G score among batch-1 genes) |
| FOCUS | packet PIP 0.0 and no contradiction. No L55168 rows in `joint_gene_tissue_finemapping.csv`, so "not evaluated" |
| Open Targets L2G 26.06 | DNPH1 0.7145 (stable); second CUL9 0.5349; rank-1 majority DNPH1 (0.667); top SHAP distanceSentinelTss (POSITIONAL), with positive QTL SHAP 0.373. Only **3** cognition credible sets (GCST90264174; GCST90446169; GCST90503115). Flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Direction | D4 / UNRESOLVED: 2 rows, 2 units; the cognition-increasing allele → LOWER DNPH1, below the ≥3-row threshold |
| brainSCOPE | 3 locus variants with no SuSiE PIP; **0 tested** in brainSCOPE |
| Expression | GTEx brain median 43.71 TPM; developmental class MIXED |
| Perturbation | P5; LOEUF 1.914 (highly LoF-tolerant) |
| Leave-one-class-out | V2G_SUPPORTED_WEAK_LOCUS |
| Ranks | B 2; E 4; A 24; C 13; D 36 |

## 3. Three questions, kept separate

- **A. Is DNPH1 a causal cognition gene? Not supported.** There is no perturbation evidence in any species that links DNPH1 to neural or cognitive phenotypes.
- **B. Is it a natural high-cognition gene? Not supported (weak).** The locus is L3 (z 1.96), with only 3 Open Targets credible sets.
- **C. Is it adult-modifiable? Partial, single-unit.** Two adult cohorts agree on sign (lower DNPH1 goes with the cognition-increasing allele), but that falls below the direction rule.

## 4. Causal hypothesis chain

credible variant (rs111342015 region; SuSiE PIP unavailable) —[MISSING: no fine-mapped PIP at this locus in our SuSiE set]→
enhancer —[EVIDENCED, weak: rE2G 0.264]→
DNPH1 expression —[EVIDENCED: CommonMind + ROSMAP coloc PP.H4 ≥ 0.8]→
cell type —[MISSING: not tested in brainSCOPE]→
direction (cognition allele → lower DNPH1) —[INFERRED: 2 rows]→
cognition —[MISSING: no mechanism links nucleotide-pool sanitation to neural function. Post-mitotic neurons do little genomic DNA replication, although the enzyme is expressed]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 33833118; doi:10.1126/science.abb4542 (Fugger 2021) | DNPH1 removes cytotoxic hmdUMP. Losing or inhibiting it sensitises BRCA-deficient cells to PARP inhibitors (SMUG1-dependent) | MECHANISTIC_ONLY | Defines the function. Cancer cell lines, with no neural data |
| PMID 41231215; doi:10.1042/BCJ20253400 (Carberry 2025) | Catalytic mechanism and energy landscape of N-ribosidic bond cleavage | MECHANISTIC_ONLY | Structural enzymology, relevant to tractability |
| PMID 41194588; doi:10.1021/acs.jmedchem.5c02356 (Barlaam 2025) | Non-nucleoside DNPH1 inhibitor series | MECHANISTIC_ONLY (pharmacology fact) | Oncology programme; no CNS data |
| PMID 41531952; doi:10.1021/acsmedchemlett.5c00651 (Whitehurst 2025) | Diverse non-nucleotide DNPH1 inhibitors | MECHANISTIC_ONLY | Same therapeutic context |
| PMID 41183227; doi:10.1021/acs.jmedchem.5c02337 (Anderson 2025) | DNPH1 PROTAC degraders | MECHANISTIC_ONLY | Tool compounds |
| PMIDs 41847111, 42772593 (2026) | DNPH1 over-expressed in breast/prostate/lung tumours; context-dependent roles in melanoma | DISEASE_ONLY | Oncology |
| PMID 41571964 (GeroScience 2026) | Gene × air-pollution interaction GWAS for AD in UKB prioritises both DNPH1 and TTBK1 | NON-INDEPENDENT | UKB-based; positional/eQTL mapping of the same region; AD, not cognition |
| TTBK1 literature (e.g. OMIM *619415; PMC7684928) | TTBK1 is a neuron-specific tau kinase in the same locus; transgenic over-expression causes cognitive/motor phenotypes | CONTRADICTING (alternative gene) | Stronger neural prior than DNPH1. In our matrix TTBK1 has one class (ENHANCER_LINK, no QTL) and is labelled V2G_SUPPORTED_WEAK_LOCUS, so the frozen rule prefers DNPH1 |

Independence: the only genetic rows are our own (CommonMind, ROSMAP, E2G). We found no published cognition GWAS gene-level
analysis naming DNPH1. We found no DNPH1 brain or behaviour study (PubMed searched 2026-09-23).

## 6. Modifiability characterisation (facts only)

- Protein: cytosolic/nuclear homodimeric hydrolase, 2'-deoxynucleoside 5'-phosphate N-hydrolase (ChEMBL CHEMBL3351218). Endogenous substrate 5-hmdUMP; products 5-hydroxymethyluracil and 2-deoxyribose-5-phosphate.
- Structure: several PDB entries (e.g. 4P5E, 8OS9, 8OSC, 8QHQ, 8RPS, 9DA1–9DA6), including ligand-bound structures. Open Targets tractability: "Structure with Ligand; High-Quality Ligand"; PROTAC "Small Molecule Binder".
- Known modulators (fact only): nucleotide-mimetic and non-nucleoside inhibitor series and PROTACs, all from oncology (PARP-inhibitor sensitisation). There are 0 clinical candidates and 0 high-quality probes in our packet. We found no CNS-penetrance data.
- Not extracellular; not an antibody target.

## 7. Pleiotropy and safety

LOEUF 1.914 (tolerant); no Mendelian disease listed. The mechanistic safety concern follows from biology: DNPH1 loss lets hmdU
into genomic DNA and raises genotoxicity in HR-deficient cells (Fugger 2021). Several MR or colocalisation studies list DNPH1 as a
plasma-protein candidate for breast cancer and insomnia (PMIDs 42145630, 41367007, 41398839). This suggests a pQTL or eQTL at the
region with pleiotropic hits, which we did not verify.

## 8. Largest contradiction

The frozen class count prefers DNPH1 (2 classes) over TTBK1 (1 class). TTBK1 is neuron-specific and has in-vivo cognitive
phenotypes, while DNPH1 has none. With 3 credible sets and an L3 locus, the class count may reflect which eQTL resources measure
which gene well, not biology.

## 9. Missing arrow and single best next computation

Missing: the fine-mapped variant and the cell type.
**Next computation:** re-run SuSiE for L55168 on Davies 2018 z-scores with 1000G EUR LD, since the current SuSiE set has no PIP here. Then compute coloc.abf and the coloc.susie aligned sign for DNPH1 **and TTBK1**, using all eQTL Catalogue adult-brain datasets plus the brainSCOPE pseudobulk matrices where the variants are present. This decides whether the DNPH1 over TTBK1 preference survives a like-for-like test.
