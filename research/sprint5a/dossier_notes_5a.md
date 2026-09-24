# Sprint 5A — dossier research notes (gene dossiers batch 5A)

Written 2026-09-24. All times are UTC. No accounts, no commits.

## Tools and sources
- **PubMed.**
  - E-utilities esearch/esummary/efetch, anonymous (script: scratchpad `lit/pm.py`).
  - Plugin PubMed MCP, for one SH2B1 search and one metadata fetch.
- **Other databases.**
  - UniProt REST: function, isoforms, PDB cross-references.
  - Human Protein Atlas JSON: tissue and single-nucleus specificity.
  - gnomAD GraphQL API, v4 GRCh38: LOEUF, pLI, mis_z. The project file `data/interim/gnomad_constraint.tsv` is keyed by Entrez ID, and these genes were absent from it.
- **Web.** WebSearch, used twice (FAM131A, PPP1R16A).
- **Computed evidence (read-only).** `reports/sprint5a/{s5_integrated/causal_gene_evidence_matrix.csv, variant_gene_cell_hypotheses.parquet, sc_eqtl_coloc_summary.csv, brainscope_gene_summary.csv, regulatory_timing.csv, directionality_resolution_5a.csv, multitrait_coloc.csv, alphagenome_vs_observed.csv, gtex_v11_gene_direction.csv, lava_*_core5.csv, class_changes.csv, functional_finemapping*.{parquet,csv}}` and `reports/sprint5/locus_confidence_rank.csv`.
- **Citation check.** Every cited PMID's first author, year and journal was checked with one esummary call (11:39Z). Wrong first-author names in the draft were corrected: Jiang 2018, Ren 2007, Argetsinger 2023, Bochukova 2010 and Politei 2024.

## Per gene

### SH2B1 — 11:29–11:36Z
- **Search terms.**
  - `SH2B1 16p11.2 deletion obesity developmental delay`
  - `SH2B1[tiab] AND (brain OR neuron OR neuronal)`
  - `SH2B1[tiab] AND (cognition OR memory OR intelligence OR learning)`
  - `SH2B1[tiab] AND (mutation OR variants) AND obesity AND behaviour`
  - `Sh2b1 knockout mice leptin hypothalamus`
  - `SH2B1 isoforms alpha beta gamma delta`
  - `SH2B1 rs7498665 Thr484Ala functional`
  - `distal 16p11.2 deletion …` (2 variants)
- **Accepted.**
  - Du 2023 (38434247; UKB plus mouse): key.
  - Doche 2012 (23160192), Pearce 2014 (24971614), Bachmann-Gagescu 2010 (20808231), Bochukova 2010 (19966786), Xu 2026 (42764254).
  - Jiang 2018 (29180441), Chen 2015 (25586189), Argetsinger 2023 (36799031), Ren 2007 (17235396), Willer 2009 (19079261), Politei 2024 (39284294; modulator fact only).
- **Rejected.**
  - Parkinson/MPTP (35390677): off-question.
  - AD amyloid (27802221): single study, off-question.
  - Zebrafish obesity screen (39948378): no cognition readout.
  - Cognition–immune pleiotropy (42386713): GWAS-derived, non-independent, not needed.
  - Tibetan and Mexican candidate SNP studies: small.
- **Computed-evidence facts added.** The SH2B1 missense rs7498665 is in the L51327 credible set (PIP 0.009 plain / 0.051 PolyFun). Davies z +8.674 with effect allele A.
- **Uncertainty.** The BMI-risk allele mapping (G = Ala484) is taken from published convention and was not re-derived.

### GNL3 — 11:33–11:37Z
- **Search terms.**
  - `GNL3[tiab] AND (brain OR neural OR neuron OR neurogenesis)`
  - `nucleostemin neural stem cell`
  - `GNL3 schizophrenia bipolar 3p21.1`
  - `nucleostemin knockout mice`
  - `GNL3[tiab] AND (p53 OR MDM2 OR telomere)`
  - `NT5DC2 dopamine`
  - `GLT8D1 schizophrenia`
- **Accepted.**
  - Meng 2020 (32826963), Yang 2020 (31723243), Wolter 2023 (36307327; abstract re-read to confirm GNL3 is the named gene).
  - Meng L 2013 (23798389), Nomura 2009 (19418458).
  - Yang CP 2018 (29483533), Li 2022 (34978167), Nakashima 2019/2020 (31279527, 32778969), Qu 2026 (41699659).
- **Rejected.**
  - Cancer prognosis papers: DISEASE_ONLY and off-question; mentioned only generically.
  - Panda MSC, marrow stromal: irrelevant.
- **Uncertainty.** LD between our lead rs6778735 and the published functional SNPs (rs10865973, rs12635140, rs4687644, rs71052682) was **not** computed.

### TTBK1 — 11:34–11:38Z
- **Search terms.**
  - `TTBK1[tiab]`
  - `TTBK1 tau phosphorylation mice memory`
  - `TTBK1 TDP-43 phosphorylation`
  - `TTBK1 inhibitor`
  - `TTBK1 Alzheimer genetic association variant`
  - `Ttbk1 knockout …`
  - `TTBK1 microglia`
- **Accepted.**
  - Sato 2006 (16923168), Sato 2008 (19118186), McMillan 2020 (33228809), Taylor 2018 (29409526), Vázquez-Higuera 2011 (20096481), Yu 2011 (21219968), Bashore 2023 (37059819).
  - Modulator facts only: Kiefer 2014 (24637750), Dillon 2020 (32255788), Sanchez-Santos 2026 (42593908), Yukawa 2023 (37853497).
- **Rejected.**
  - miRNA/lncRNA/circRNA axis papers (30556160, 32891070, 42725992): low-evidence expression correlations.
  - Sevoflurane/environment papers (39892471, 39953251): not genetic.
  - In-silico inhibitor design (39065802, 39050776): not evidence.
- **Not found.** No germline Ttbk1-null behavioural study was found by these searches, so the absence is recorded, not asserted.

### PPP1R16A — 11:36–11:39Z
- **Search terms.**
  - `PPP1R16A[tiab]`
  - `MYPT3 protein phosphatase 1`
  - `PPP1R16A OR MYPT3 neuron`
  - `8q24.3 FOXH1 KIFC2 PPP1R16A cognition` (0 hits)
  - WebSearch `PPP1R16A MYPT3 brain neuron expression function knockout`
- **Accepted.** Skinner 2001 (11336659), Yong 2006 (16920702), Sueyoshi 2008 (18202305), Akiyama 2025 (41009945; cattle LD-proxy example), OMIM 609172 (via web result; not opened).
- **Rejected.**
  - Hepatocellular carcinoma, thyroid and Xiaoyao powder network-pharmacology papers (39010084, 40056710): off-question.
  - Cattle milk GWAS beyond the one LD-proxy example.
  - A USPTO patent result about "P16" and NMDA receptors: patent, and the identity with PPP1R16A was not verified.
- **Uncertain.** Wang 2024 (39406522, ADHD multi-omics) lists PPP1R16A in its abstract but was not read in full. Marked unverified.

### FAM131A — 11:37–11:40Z
- **Search terms.**
  - `FAM131A[tiab]`
  - `FAM131A OR C3orf40`
  - `CLCN2 leukoencephalopathy ClC-2 brain`
  - `3q27.1 cognition EIF2B5 CLCN2 locus` (0 hits)
  - WebSearch `FAM131A protein brain function neuron`
- **FAM131A.** All 4 PubMed hits were incidental (38956246, 39980243, 32639612, 30982271) and were rejected as content, but are recorded as absence of evidence. HPA JSON was accepted (brain tissue-enhanced, 96.5 nTPM).
- **Alternative gene (CLCN2).** Blanz 2007 (17567819) and Depienne 2013 (23707145) accepted. Other CLCN2 case reports rejected as redundant.

### Addenda: KIFC2, DNPH1, CYP2D6, SLC39A8, RHEBL1 — 11:40–11:42Z
- **No new literature searches.** The addenda state only what the Sprint-5A computed layers change, per the brief.
- **Sources.** The Sprint-5 dossiers were re-read for their verdicts: `reports/sprint5/gene_dossiers/<GENE>.md`.

## Flags raised (not edited anywhere)
1. **FAM131A.** Its promotion to CAUSAL_GENE_MODERATE rests on one Bryois cell-type test that does not replicate in SingleBrain (0.324), which includes those donors. CLCN2 at the same SNP is better replicated but is labelled LIKELY_QTL_PASSENGER.
2. **TTBK1.** Its promotion to CAUSAL_GENE_MODERATE rests on one SingleBrain oligodendrocyte row (0.862; Bryois 0.141). The locus has no credible set in any Sprint-5A fine-mapping run.
3. **CYP2D6.** Its promotion to CAUSAL_GENE_MODERATE via SEQUENCE_MODEL double-counts the short-read QTL whose reliability at CYP2D6/CYP2D7 was questioned in Sprint 5. In addition, HyPrColoc excluded CYP2D6 from the cognition cluster.
4. **PPP1R16A / KIFC2.** They tie on class count, with opposite directions at the same SNP. ZFTRAF1 has the strongest colocalisation but is labelled a passenger. The locus is gene-unresolved in substance.
5. **SH2B1.** No class change is warranted under the frozen rules. It is the only 16p11.2 gene with direction-consistent evidence plus independent (mouse) perturbation. TUFM's single-nucleus vs bulk direction discordance weakens TUFM.
