# SUOX — gene dossier (Sprint 5, literature red-team batch 1)

Scope: we describe the target and appraise the evidence. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Our numbers come from `data/sprint5/dossier_evidence_packets.json` and are not changed here.

## 1. Verdict

**LIKELY_QTL_PASSENGER (locus L319, stratum L4_DISCORDANT; CONTESTED).** SUOX shares the RPS26/ERBB3 12q13.2 haplotype. The primary
FOCUS run gives RPS26 0.99 vs SUOX 0.015, and SUOX is absent from brainSCOPE. The locus does not replicate outside UKB. One thing
cuts the other way: the Open Targets 26.06 refresh switched the locus assignment from RPS26 to SUOX (L2G 0.914), driven by a pQTL
colocalisation feature. That is not a vote under our frozen rules, but it is a documented disagreement. The passenger label stands.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L319 (12q13.2), stratum **L4_DISCORDANT**, log10BF_independent −0.3451, rank 134 (64–140), gc_aligned_z −0.8346, panel A |
| V2G classes | QTL (1 class; 3 GTEx rows, 1 cohort unit). RPS26 holds 2 classes, so SUOX is CONTESTED |
| FOCUS | primary SUOX **0.015** vs RPS26 0.99 → **focus_contradiction True**. Other configs: GTEx cerebellum SUOX 0.31–0.33 (cv_r2 0.39); GTEx v8 EUR cortex SUOX 0.299 (cv_r2 0.12). TWAS z for SUOX is negative (−5.5), for RPS26 positive (+5.8) |
| Open Targets L2G 26.06 | **SUOX 0.9143** (CHANGED from Sprint-4 RPS26); second RPS26 0.7007; rank-1 majority RPS26 (0.462); top SHAP **pQtlColocClppMaximum** (QTL). Per protocol, L2G is mapped to its SHAP class (QTL) and is never an extra vote |
| OT L2G feature detail (`data/sprint5/ot_l2g_features.parquet`) | For SUOX, pQtlColocH4Maximum = **0.945** (Intelligence MTAG, GCST005316), 0.953 (cognitive EA, GCST90011875), 0.82–0.91 in 4 other cognition credible sets, but CLPP max only 0.004–0.018. For RPS26, pQTL features are 0 (probably not measured on the proteomic panels; not verified). eQtlColocH4Maximum ≈ 0.99 for **both** genes. The pQTL tissue and study were not retrieved |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 3 GTEx rows, cognition-increasing allele → LOWER SUOX (opposite sign to RPS26) |
| brainSCOPE | SUOX **absent from all 24 pseudobulk matrices** (not tested) |
| Expression | GTEx brain median 10.4 TPM; ADULT_DYNAMIC |
| Perturbation | P5; LOEUF 1.128 |
| Leave-one-class-out | **POSITIONAL_ONLY** |
| Ranks | B 47; E 58; A 134; C 4; D 36 |

## 3. Three questions, kept separate

- **A. Is SUOX a causal cognition gene? Not supported.** Biallelic LoF causes isolated sulfite oxidase deficiency, a devastating neonatal neurometabolic disease. That is DISEASE_ONLY and says nothing about common-variant cognition.
- **B. Is it a natural high-cognition gene? Not supported.** The locus is discordant outside UKB.
- **C. Is it adult-modifiable? Not credible.** The direction is rows-only, the gene assignment is contested, and there are no single-cell data.

## 4. Causal hypothesis chain

rs1131017/rs772921 haplotype —[EVIDENCED: shared credible set]→
element —[MISSING: no SUOX ENHANCER_LINK]→
SUOX expression (lower) —[EVIDENCED, weak: 3 GTEx rows; FOCUS assigns the signal to RPS26]→
cell type —[MISSING: not in brainSCOPE]→
direction —[INFERRED]→
cognition —[CONTRADICTED at the locus: no replication outside UKB. MISSING mechanism: sulfite detoxification is essential but is not rate-limiting for neural function at normal activity]

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| PMID 28980090; doi:10.1007/s10545-017-0089-4 (Claerhout 2017) | Review of 47 ISOD patients: neonatal onset, seizures (84%), developmental delay (97%), ectopia lentis, brain atrophy | DISEASE_ONLY | Severe biallelic LoF. Not invertible |
| PMID 12112661; doi:10.1002/humu.9038 (Johnson 2002) | Twelve SUOX mutations in ISOD | DISEASE_ONLY | Same disease lineage |
| PMID 36303223; doi:10.1186/s13023-022-02544-x (Li 2022) | Biallelic missense → milder, later-onset ISOD; ectopia lentis can present with minimal neurological signs | DISEASE_ONLY | Residual activity partially protects, so a dose-response exists only near the null end |
| PMID 33664499; doi:10.1038/s41431-021-00835-8 (Censin 2021) | PCOS signals colocalise with ERBB3, IKZF4, RPS26 **and SUOX** | NON-INDEPENDENT | Same eQTL panels; co-nomination is expected under LD |
| PMID 40445995; doi:10.1371/journal.pone.0323683 (Zhu 2025) | Pre-eclampsia TWAS + coloc nominates RPS26, SULT1A2 and SUOX | NON-INDEPENDENT | Same pattern |
| Open Targets 26.06 (our `opentargets_refresh.csv`, `ot_l2g_features.parquet`) | L2G assigns L319 to SUOX (0.914) on pQTL coloc (H4 up to 0.95, low CLPP) | CONTRADICTING (our class) | The protein-level coloc is the one molecular layer where SUOX has evidence and RPS26 has none. Tissue not retrieved (plasma likely). Same credible sets as ours, so NON-INDEPENDENT of the association. **Flag**, not a vote |
| PMID 42200276; doi:10.1161/CIRCRESAHA.125.327427 (Kotla 2026) | CD38 suppresses endothelial SUOX; sulfite/taurine accumulation in atherothrombosis | MECHANISTIC_ONLY | Vascular, not neural |

Shared data: Censin 2021, Zhu 2025, Open Targets and our QTL rows all derive from overlapping eQTL/pQTL resources. None is independent evidence for SUOX over RPS26.

## 6. Modifiability characterisation (facts only)

- Protein: homodimeric molybdo-heme enzyme (Moco domain + cytochrome b5 domain) in the mitochondrial intermembrane space. It oxidises sulfite to sulfate, passing electrons to cytochrome c. It can reduce nitrite to NO under hypoxia (UniProt, PubMed 41337830).
- Endogenous cofactors: molybdenum cofactor (MOCS1/2/3, GPHN pathway) and heme. Substrate: sulfite from cysteine/methionine catabolism.
- Structure: "Structure with Ligand" (Open Targets); chicken and human SO structures exist. No ChEMBL human SUOX target record returned (search 2026-09-23). 0 probes, 0 clinical candidates.
- Pathway fact: fosdenopterin (cPMP) is approved for molybdenum cofactor deficiency type A (MOCS1), which restores SUOX activity indirectly. It does not act on SUOX-intrinsic ISOD and is not SUOX-targeted.
- The packet's "extracellular_or_membrane: true" refers to mitochondrial IMS localisation. SUOX is not cell-surface.

## 7. Pleiotropy and safety

LOEUF 1.128 (tolerant to heterozygous LoF; the disease is recessive). The shared haplotype carries T1D, PCOS and pre-eclampsia associations. Reduced SUOX activity leads to sulfite/S-sulfocysteine accumulation, which is neurotoxic in ISOD.

## 8. Largest contradiction

Open Targets 26.06 moved the L319 assignment **to** SUOX (0.914) on pQTL colocalisation, while our FOCUS analysis gives SUOX 0.015. The two methods use different molecular layers (a likely plasma pQTL vs brain eQTL), so this is a tissue and layer disagreement, not a direct refutation. It is secondary, though, because the locus itself fails replication outside UKB.

## 9. Missing arrow and single best next computation

Missing: any brain-relevant SUOX-specific molecular QTL independent of the RPS26 eQTL.
**Next computation:** retrieve the Open Targets pQTL colocalisation underlying the SUOX L2G feature (study ID, tissue/plasma, CLPP, lead variant). Test by conditional analysis (GCTA-COJO or coloc.susie on eQTL credible sets) whether the SUOX pQTL/eQTL signal is distinct from the RPS26 rs1131017 eQTL signal. If they are the same signal, SUOX stays a passenger. If distinct, re-examine which one the cognition credible set shares.
