# Module report — can the cognition gene universe be compressed?

*Sprint 3, Part L. Generated from `reports/gene_tournament/biological_modules.csv`, `modules_summary.json`, `module_tail_engagement.csv`, `pathway_replication.csv` and `red_team_modules.csv` by the orchestrator. Every number below is read from those files.*

## Short answer

**Partly, and less than it looks.** The 1,272 genes at MAGMA gene-level FDR<0.01 (565 LD blocks) fall into **11 modules** under Louvain clustering of a fused annotation + STRING graph (resolution 1.0, chosen as the most modular solution in the 5–20 range). The top 5 modules hold 72% of the FDR<0.01 gene-level evidence and the top 10 hold 97% — but the second number is close to tautological, because Louvain assigns almost every gene (only 35 unassigned, 2.5% of evidence).

What actually matters is whether the partition is **real**, and three tests say it is only partly real:

* **Methods disagree.** Adjusted Rand index between Louvain, hierarchical and NMF partitions: 0.24, 0.19, 0.19. Three reasonable methods produce three different partitions.
* **The network drives the structure.** Removing STRING changes the partition most (ARI 0.36); removing any single annotation source leaves ARI 0.54–0.80. STRING edges include text-mining, so well-studied genes are better connected.
* **Boundaries do not transfer across GWAS.** Re-deriving modules from Savage 2018 recovers each Davies module at Jaccard 0.07–0.48.

**The synaptic SIGNAL survives every test that could be run at adequate power; the synaptic MODULE as a bounded unit does not.** These are different
claims and the difference is the finding:

* **Signal — survives.** Synaptic sets are the only ones passing global FDR after conditioning on gene size, gene
  density, LD, annotation density and LoF constraint (6 of 6,200 sets; the M01 label "synapse" has global FDR 0.034;
  no other module's label set has global FDR below 0.36). The enrichment reproduces in Savage 2018 (6/6 sets, same
  sign, P≤9e-4 — an overlapping sample, so reproducibility rather than independence). M01 is the only module nominally
  more engaged at the extreme tail than other cognition genes (P=0.012).
* **Signal — not independently replicated.** In the UKB-free extreme-IQ sample all six sets have the same sign and
  none is significant (P 0.18–0.50), at 65× less power. Untested, not refuted.
* **Module — downgraded.** M01's membership is unstable (bootstrap co-clustering 0.57; best Savage-derived
  counterpart Jaccard 0.24) and its tail engagement does not survive Bonferroni across 12 modules (0.14). The red team
  therefore downgrades M01 as a unit while the pathway result stands.

Consequently **only one module meets the sprint's evidence bar** (global-FDR label enrichment, or Bonferroni-surviving
tail engagement), and Part M's "minimal control set" collapses to a single gene — the strongest-evidence member of
that one module. That is a restatement of the top gene, not a discovered set of control nodes.

## Modules

| Rank | Module | Label | Genes / loci | Evidence share | Bootstrap stability | Savage Jaccard | Tail engagement vs other cognition genes (P) | Label enrichment, conditioned (P) | Red team |
|---|---|---|---|---|---|---|---|---|---|
| 1 | M01 | Synaptic | 310 / 240 | 31.8% | 0.57 | 0.24 | 0.012 | 3.05e-05 | DOWNGRADED |
| 2 | M04 | Transcription factors (RNA pol II) | 126 / 95 | 10.5% | 0.84 | 0.34 | 0.365 | 0.188 | RETAINED_WITH_CAVEATS |
| 3 | M08 | RNA binding / splicing | 77 / 62 | 6.6% | 0.83 | 0.32 | 0.49 | 0.0645 | RETAINED_WITH_CAVEATS |
| 4 | M06 | Chromatin modification | 93 / 57 | 6.3% | 0.77 | 0.39 | 0.649 | 0.0129 | RETAINED_WITH_CAVEATS |
| 5 | M02 | Mitochondrial / RNA binding / translation | 195 / 115 | 11.3% | 0.43 | 0.39 | 0.607 | 0.154 | DOWNGRADED |
| 5 | M11 | Ser/Thr protein kinases | 18 / 18 | 1.9% | 0.81 | 0.48 | 0.339 | 0.283 | RETAINED_WITH_CAVEATS |
| 7 | M03 | Ubiquitin–proteasome / neddylation | 141 / 97 | 9.9% | 0.31 | 0.30 | 0.48 | 0.597 | DOWNGRADED |
| 7 | M05 | Transmembrane transport / Golgi | 96 / 72 | 8.0% | 0.39 | 0.13 | 0.654 | 0.178 | DOWNGRADED |
| 7 | M07 | Cell cycle / mitosis | 81 / 72 | 5.7% | 0.55 | 0.37 | 0.917 | 0.0621 | DOWNGRADED |
| 7 | M09 | Immune / complement / cell surface (MHC-adjacent) | 77 / 49 | 4.7% | 0.61 | 0.32 | 0.989 | 0.00232 | RETAINED_WITH_CAVEATS |
| — | M10 | Olfactory receptors (gene-cluster ARTEFACT) | 23 / 10 | 0.7% | 0.91 | 0.07 | 0.531 | 0.612 | DOWNGRADED |

## Per-module detail

### M01 — Synaptic

* **Top genes by association:** DCC, NEGR1, EXOC4, AMIGO3, BSN, PPM1E, PTPRO, HCRTR1, GBF1, APEH, MST1R, MON1A, CLN3, KCNJ3, CRHR1
* **Pathway labels (share of module genes):** process in the synapse (37%) ; synapse (GO:0045202) (41%) ; postsynapse (GO:0098794) (25%) ; synapse organization (GO:0050808) (17%) ; presynapse (GO:0098793) (20%)
* **Developmental timing:** 32% adult-dynamic, 19% prenatal/developmental, 92% adult-expressed
* **Phenotypes:** mean 1.03 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.61; 31 shared g/math genes
* **Independent cohorts:** 470 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 7 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

### M04 — Transcription factors (RNA pol II)

* **Top genes by association:** SFMBT1, DDN, FOXO6, PITX3, FOXP1, RAI1, NFATC2IP, ATXN1L, RBL2, ATXN7L2, ZNF821, FOXH1, FOXO3, POU6F2, CSRNP3
* **Pathway labels (share of module genes):** DNA-binding transcription factor activity, RNA polymerase II-specific (63%) ; RNA polymerase II cis-regulatory region sequence-specific DNA binding (60%) ; regulation of transcription by RNA polymerase II (63%) ; DNA-binding transcription factor activity (42%) ; regulation of DNA-templated transcription (51%)
* **Developmental timing:** 17% adult-dynamic, 44% prenatal/developmental, 94% adult-expressed
* **Phenotypes:** mean 0.96 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.41; 6 shared g/math genes
* **Independent cohorts:** 180 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 13 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** RETAINED_WITH_CAVEATS

### M08 — RNA binding / splicing

* **Top genes by association:** ATXN2L, STAU1, RBM6, SND1, RBM5, AFF3, ELAVL2, LSM4, ZNF638, SRPK2, RBM12, RBFOX1, NOVA1, SMG7, RALYL
* **Pathway labels (share of module genes):** RNA binding (65%) ; Metabolism of RNA (40%) ; nucleic acid binding (38%) ; nuclear speck (26%) ; Processing of Capped Intron-Containing Pre-mRNA (23%)
* **Developmental timing:** 4% adult-dynamic, 38% prenatal/developmental, 95% adult-expressed
* **Phenotypes:** mean 0.74 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.68; 6 shared g/math genes
* **Independent cohorts:** 83 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 4 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** RETAINED_WITH_CAVEATS

### M06 — Chromatin modification

* **Top genes by association:** TET2, SGF29, PBRM1, KANSL1, H2BC15, H2AC16, H2AC15, H1-5, H3C11, H4C13, RUNX1T1, H2AC13, KMT2D, H3C10, H2BC13
* **Pathway labels (share of module genes):** Chromatin modifying enzymes (52%) ; Chromatin organization (55%) ; chromosome (56%) ; structural constituent of chromatin (37%) ; HATs acetylate histones (38%)
* **Developmental timing:** 1% adult-dynamic, 45% prenatal/developmental, 70% adult-expressed
* **Phenotypes:** mean 0.90 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.42; 5 shared g/math genes
* **Independent cohorts:** 118 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 11 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** RETAINED_WITH_CAVEATS

### M02 — Mitochondrial / RNA binding / translation

* **Top genes by association:** NT5DC2, RABEP2, SH2B1, AMT, UQCC5, GPX1, ABT1, TUFM, GNL3, STIMATE, APOBR, SPCS1, MUSTN1, HMGN4, WBP2NL
* **Pathway labels (share of module genes):** mitochondrion (35%) ; mitochondrial inner membrane (16%) ; mitochondrial matrix (16%) ; RNA binding (17%) ; Translation (10%)
* **Developmental timing:** 19% adult-dynamic, 22% prenatal/developmental, 92% adult-expressed
* **Phenotypes:** mean 0.55 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.64; 12 shared g/math genes
* **Independent cohorts:** 154 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 1 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

### M11 — Ser/Thr protein kinases

* **Top genes by association:** TEX14, NEK4, PRKD1, SPEG, GRK6, TLK2, SBK1, MARK3, TESK2, MAST4, KLHDC8B, LMTK1, SPEGNB, TTBK1, MAST3
* **Pathway labels (share of module genes):** protein kinase activity (89%) ; protein serine kinase activity (78%) ; protein serine/threonine kinase activity (78%) ; ATP binding (89%) ; intracellular signal transduction (44%)
* **Developmental timing:** 33% adult-dynamic, 17% prenatal/developmental, 94% adult-expressed
* **Phenotypes:** mean 1.11 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.70; 2 shared g/math genes
* **Independent cohorts:** 28 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 0 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** RETAINED_WITH_CAVEATS

### M03 — Ubiquitin–proteasome / neddylation

* **Top genes by association:** INKA1, UBA7, PEF1, TRIM37, MEF2C, NKIRAS1, TRAIP, PRKAG1, NFKB2, TRIM31, SNX29, SPPL2C, USP4, RNF123, AKTIP
* **Pathway labels (share of module genes):** protein ubiquitination (23%) ; ubiquitin protein ligase activity (18%) ; Neddylation (14%) ; Antigen processing: Ubiquitination & Proteasome degradation (15%) ; Class I MHC mediated antigen processing & presentation (16%)
* **Developmental timing:** 20% adult-dynamic, 18% prenatal/developmental, 91% adult-expressed
* **Phenotypes:** mean 0.61 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.77; 16 shared g/math genes
* **Independent cohorts:** 114 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 2 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

### M05 — Transmembrane transport / Golgi

* **Top genes by association:** DAG1, SULT1A2, GMPPB, SULT1A1, GLT8D1, COL16A1, SPNS1, ST3GAL3, ARMH3, ZSWIM6, MGAT3, TINAGL1, CYP2D6, SGCZ, SLC33A2
* **Pathway labels (share of module genes):** transmembrane transport (27%) ; Transport of small molecules (23%) ; Golgi membrane (23%) ; SLC-mediated transmembrane transport (17%) ; transmembrane transporter activity (16%)
* **Developmental timing:** 23% adult-dynamic, 12% prenatal/developmental, 83% adult-expressed
* **Phenotypes:** mean 0.77 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.49; 9 shared g/math genes
* **Independent cohorts:** 93 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 2 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

### M07 — Cell cycle / mitosis

* **Top genes by association:** CSE1L, OGA, SKA2, RAD51C, RECQL4, IST1, ALMS1, SAXO2, NCAPG, ZFYVE9, CEP57, SEH1L, CC2D1B, CEP192, XPO4
* **Pathway labels (share of module genes):** Cell Cycle (38%) ; M Phase (28%) ; Cell Cycle, Mitotic (31%) ; Mitotic Prometaphase (23%) ; Mitotic Anaphase (22%)
* **Developmental timing:** 9% adult-dynamic, 32% prenatal/developmental, 88% adult-expressed
* **Phenotypes:** mean 0.68 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.37; 3 shared g/math genes
* **Independent cohorts:** 79 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 1 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

### M09 — Immune / complement / cell surface (MHC-adjacent)

* **Top genes by association:** CD19, BTN2A1, BTN1A1, SEPTIN4, STAB1, ITIH4, IL27, BTN3A2, ITIH1, SEPTIN3, ITIH3, LAT, BTN2A2, CYSTM1, IL17D
* **Pathway labels (share of module genes):** external side of plasma membrane (30%) ; signaling receptor binding (22%) ; Adaptive Immune System (29%) ; Regulation of Complement cascade (13%) ; cell surface (23%)
* **Developmental timing:** 23% adult-dynamic, 14% prenatal/developmental, 70% adult-expressed
* **Phenotypes:** mean 0.71 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.42; 1 shared g/math genes
* **Independent cohorts:** 73 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 0 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** RETAINED_WITH_CAVEATS

### M10 — Olfactory receptors (gene-cluster ARTEFACT)

* **Top genes by association:** GPR26, OR2J2, OR12D3, GPR52, OR8B2, OR8B3, GPR61, GPR22, OR12D2, OR14J1, OR2H2, MAS1L, OR4X1, OR2B2, YAE1
* **Pathway labels (share of module genes):** G protein-coupled receptor activity (87%) ; Expression and translocation of olfactory receptors (70%) ; Olfactory Signaling Pathway (70%) ; G protein-coupled receptor signaling pathway (87%) ; olfactory receptor activity (65%)
* **Developmental timing:** 9% adult-dynamic, 17% prenatal/developmental, 30% adult-expressed
* **Phenotypes:** mean 0.35 cognitive domains per gene supported by distinct cohort units; objective-arithmetic mean Z 0.52; 0 shared g/math genes
* **Independent cohorts:** 11 strict-unit memberships summed over genes (upper bound; units repeat across genes)
* **Safety:** 0 ClinGen haploinsufficient genes
* **Cell types / regions:** not resolved per module — bulk-tissue and X01 cell-class data are set-level, not module-level
* **Red team:** DOWNGRADED

## What this does not show

* A module is a cluster of genes annotated alike and/or linked in STRING. It is **not** a pathway shown to act, not a causal unit and not a target.
* The evidence share is a share of **gene-level association evidence at FDR<0.01**, each LD block counted once. It is **not** a share of heritability, which is carried overwhelmingly by sub-threshold loci this analysis does not see.
* A module's extreme-tail support against the *whole genome* is inherited from how its genes were selected (continuity); only the comparison against other cognition genes is informative, and it is reported above.
* M10 (olfactory receptors) is a gene-family cluster — physically clustered genes sharing annotation — and is excluded from rankings.
