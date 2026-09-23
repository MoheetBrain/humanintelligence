# Sprint 5 — Human cognition causal gene resolution

*2026-09-23 · branch `sprint-5/causal-cognition-gene-resolution` (from `e50eb4f`) · protocol frozen at `1a08f10` before any new data stream, with 2 disclosed amendments (A1: residual labels; A2: a numerical-defect fix) · all computational · **chemistry / intervention gate CLOSED**.*

## Bottom line

**Most loci are real, but at none of the strongest is the causal gene resolved.** This matches success condition **D** of the brief, and condition **E** also applies: a new data layer changed the interpretation.

1. **Two loci carry strong independent (UK-Biobank-free) support: ATXN2L (16p11.2) and AKAP6 (14q12).**
   - Fourteen more signals are moderate. The label genes are NT5DC2, SFMBT1, DPP4, BTN2A1, EXT1, EXOC4, DCC, KCNJ3, SLC39A8, DDN, NKIRAS1, FOXO6, UBE2E1 and ZSCAN31.
   - This comes from 152 signals scored by a frozen Bayes factor on the G&C replication sample.
   - Rank intervals are wide: the #1 locus spans ranks 1–17, and beyond the top 3 most span about 1–100.
2. **No gene reaches CAUSAL_GENE_HIGH. Two reach CAUSAL_GENE_MODERATE: KIFC2 (8q24.3) and DNPH1 (6p21.1).**
   - Both sit at loci that are only weakly replicated (L3).
   - Both depend on the Sprint-5 brain enhancer-to-gene layer combined with adult brain eQTL colocalisation.
   - At the two strong loci, gene assignment stays split: TUFM/EIF3C/SH2B1 at 16p11.2, and AKAP6/NPAS3 at 14q12.
3. **No adult molecular direction is resolved for a credible causal gene (no gene in stratum D1).**
   - RPS26 and RHEBL1 (cognition allele → higher expression) and WBP2NL (→ lower) meet the unchanged Sprint-4 direction rule.
   - brainSCOPE adds concordant cell-type evidence for RPS26 and WBP2NL.
   - None of the three has a credible gene assignment at a replicated locus.
4. **Rare-coding evidence and common-variant evidence do not meet.**
   - KDM5B, ANKRD12, RC3H2 and CACNA1A are exome-wide rare-coding genes: carriers of damaging variants do worse. All four come from UK Biobank.
   - None lies in a common-variant locus, and every matched-null convergence test is null. With 4–8 genes these tests are underpowered.
   - The rare-coding evidence shows that losing these genes impairs cognition. It is not evidence for enhancement.
5. **The verified math-53 stream mostly runs *against* general cognition, by construction.**
   - It is a self-report / course-taking factor fixed orthogonal to g.
   - The only shared gene is **SLC39A8**, through one variant: rs13107325, A391T.
6. **Blocked by access, and never counted as null:**
   - AlphaGenome (needs an API key);
   - brainSCOPE colocalisation (only significant pairs are public; genotypes are controlled);
   - within-family Gate A (no OpenGWAS token).

## What Sprint 5 added

| Layer | Source | Result |
|---|---|---|
| Open Targets refresh | Platform **26.06** (the current release, the same one Sprint 3 used) | 130 loci. **117 of 130 top L2G calls are driven by positional features.** 6 assignments change once all credible sets are included (e.g. 12q13.2 → SUOX via a pQTL; 3p21.1 → STAB1 via an enhancer link). 22,856 enhancer–gene (E2G) links. Only 3 of 224 credible variants with PIP ≥ 0.1 are coding. |
| brainSCOPE (Emani 2024) | 17 DLPFC cell types, 97–346 donors each | Colocalisation NOT_TESTABLE. Lead-variant tagging: RPS26 ↑ (10 cell types), WBP2NL ↓ (10), CYP2D6 ↑ (6), DHRS11 ↓ (4 neuronal), SH2B1 ↑ and GOSR1 ↑ (L2/3 IT). No gene flips direction across cell types. |
| Developmental eQTL | fetal neocortex (Walker 2019); fetal-derived progenitors and neurons (Aygün 2021); BrainSeq (mixed age) | 20 strong colocalisations out of 969 tests. NT5DC2 ↓ (fetal 0.95, BrainSeq 0.97); DNPH1 ↓ in all 3 datasets; RHEBL1 ↑ (same direction as adult); CLCN2 ↑ (0.99). |
| Rare coding | Chen 2023, Genebass, Wu 2025, DDG2P | 4 exome-wide cognition genes and 4 EA-proxy genes, all UK Biobank, all loss of function. |
| Positive dosage | 2q12.3 duplication and others | 2q12.3 remains nominal and unreplicated. Every other duplication lowers cognition. The RIMS1 kindred is confounded. |
| Math-53 | Giannelis 2025, *Mol Psychiatry*, Supplementary Table S2 | 53 SNPs verified, GRCh37. Summary statistics are not public (23andMe). |
| New lineage | GenLang performance IQ (N = 18,722) | 106 of 141 concordant, slope 0.173. It shares the BATS cohort with Davies 2018, so it is **sensitivity only**. |
| AlphaGenome | alphagenome 0.9.0 | **NOT_TESTABLE**: an API key is required. |

**Two defects were found and fixed.**

1. **Unstable winner's-curse shrinkage.** The Sprint-4 kernel-density Tweedie estimate was unstable in the tail: it mapped z = 8.33 to −1.99. It was replaced by an empirical-Bayes normal mixture (amendment A2).
   - A dated correction block was added to the Sprint-4 report.
   - Effect on Sprint 4: the expected concordance band moves from 74–80% to 75–82%. No decision changed.
2. **A wrong independence entry in the cohort-overlap ledger.** GenLang's independence was first recorded wrongly and has been corrected.

## Answers to the 25 questions

**1. Strongest independent human cognition loci.**
Scored as the summed log10 Bayes factor on G&C, the only counted UKB-free lineage. GenLang and Zabaneh are shown for sensitivity only.

| Rank | Signal (label) | G&C z | log10 BF | GenLang z | Stratum |
|---|---|---|---|---|---|
| 1 | rs62037363 (ATXN2L, 16p11.2) | 3.44 | 1.24 | 0.59 | L1 |
| 2 | rs2239647 (AKAP6, 14q12) | 3.52 | 1.00 | **2.76** | L1 |
| 3 | rs6778735 (NT5DC2, 3p21.1) | 3.09 | 0.97 | −0.23 | L2 |
| 4 | rs7646741 (SFMBT1, 3p21.1) | 2.81 | 0.81 | −0.12 | L2 |
| 5 | rs2284871 (DPP4) | 2.74 | 0.77 | 1.24 | L2 |
| 7 | rs7814022 (EXT1) | 3.00 | 0.63 | 0.93 | L2 |
| 8 | rs10258052 (EXOC4) | 2.35 | 0.62 | **3.04** | L2 |
| 9 | rs11662271 (DCC) | 2.16 | 0.60 | 1.32 | L2 |

The most robust loci across both lines are AKAP6 and EXOC4. See `locus_confidence_rank.csv` for the rest. Strata: L1 2, L2 14, L3 75, discordant 49, not testable 12.

**2. Genes with the strongest evidence of being the actual causal gene.** None reaches CAUSAL_GENE_HIGH.

- **KIFC2 (CAUSAL_GENE_MODERATE).**
  - Evidence: a brain enhancer link from the PIP 0.85 variant rs2291133, plus adult eQTL colocalisation.
  - Against: the locus is weak (L3), ZFTRAF1 and RECQL4 compete, and the knockout mouse is normal.
- **DNPH1 (CAUSAL_GENE_MODERATE).**
  - Evidence: an enhancer link plus 2 adult eQTL cohorts, and 3 developmental colocalisations, all "cognition allele → lower".
  - Against: the locus is weak (L3) and there is no brain literature.
- **SLC39A8** has the single strongest variant-to-gene arrow: the rs13107325 A391T missense variant has PIP ≈ 1.00 at an L2 locus.
  - It holds only one evidence class, so it stays gene-unresolved under the frozen rule.
  - GenLang's sign is discordant, and the knock-in mouse has no behavioural phenotype.

**3. Genes with human rare-coding causal evidence.**

- **Exome-wide for cognition:** KDM5B, ANKRD12, RC3H2, CACNA1A. Protein-truncating variant carriers do worse. All are UK Biobank; there is no gene-level replication outside it, only the 8-gene set replicated in Finnish cohorts. Caveats:
  - RC3H2 rests on 16 carriers.
  - CACNA1A's P (1.33e-6) sits above Chen's stated study-wide threshold.
- **EA-proxy only:** ADGRB2, GIGYF1, SLC8A1, BCAS3.

**4. Genes in BOTH common-regulatory and rare-coding evidence.** **None.**

- 0 of 4 rare-coding genes lie in the 159 loci.
- The matched-null tests were:

  | Test | P |
  |---|---|
  | T1 (mean MAGMA z) | 0.43 |
  | T3 (FDR pathway membership) | 0.63 |
  | T4 (developmental timing) | 0.10 |
  | T5 (cell type) | 0.58 |

- These tests are underpowered, so this is **not** evidence of separate biology.

**5. Genes recurring across general cognition and quantitative-math genetics.**

- **SLC39A8 only**, through the same variant, rs13107325. That variant fails the math factor's heterogeneity test, so it is labelled MATH_PROXY_ONLY.
- 12 of 53 math SNPs are in general-cognition loci, against 3.1 expected (P = 3e-4). But 10 of those 12 are **inverted**: the math-raising allele lowers g (for example NEGR1, rs7542974).
- This inversion is expected from a factor built orthogonal to g. It is not shared biology.

**6. Math-53 variants with strong AlphaGenome predicted effects.** **NOT_TESTABLE** (API key). Nothing is inferred.

**7. Variants with AlphaGenome + Open Targets + brainSCOPE convergence.** None: AlphaGenome is not testable.

- Without AlphaGenome, the best convergence is at most **2 independent classes**, at 6 variants:
  - NEGR1 rs3101336 / rs3128341 / rs3101338;
  - GGNBP2 rs3736166;
  - KIFC2 rs2291133;
  - RPS26 rs1131017.
- Each is an enhancer link plus QTL, and in each a competing gene is named. See `v2g_convergence.csv`.

**8. Genes with adult cell-specific brain QTL evidence.** These come from lead-variant tagging only; colocalisation is not testable.

| Gene | Cell types | Direction (cognition allele) |
|---|---|---|
| RPS26 | 10 | higher |
| WBP2NL | 10 | lower |
| CYP2D6 | 6, mostly inhibitory | higher |
| DHRS11 | L5/L6 IT | lower |
| SH2B1 | L2/3 IT | higher |
| GOSR1 | L2/3 IT | higher |

brainSCOPE shares donors with CommonMind and ROSMAP, so it is not an independent cohort.

**9. Genes with a robust beneficial molecular direction.** **None at D1.**

- **Closest case, RHEBL1.** RHEBL1 would reach D1 only if the brainSCOPE GRN element→gene links were counted as an enhancer-link class. They are not counted, because the frozen class requires a chromatin enhancer–gene model and these are TF-network inferences.
  - The single element involved links **9 genes** (RHEBL1, DDN, PRKAG1, CACNB3, ARF3, KCNH3, RND1, SPATS2, TUBA1B), so it does not discriminate between them (`data/sprint5/grn_sensitivity.csv`).
  - Against RHEBL1 more generally:
    - it passes the FOCUS contradiction check by only 0.02;
    - it is null in brainSCOPE;
    - it is dispensable in mouse brain.

- RPS26 (↑), RHEBL1 (↑) and WBP2NL (↓) meet the direction rule, but each fails gene credibility or independent replication (D2):
  - RPS26: the locus is not replicated outside UK Biobank.
  - RHEBL1: FOCUS favours PFKM.
  - WBP2NL: testis-enriched passenger; FOCUS favours CYP2D6.
- A "beneficial direction" here means only the expression change that tracks the cognition-increasing allele. It is not an enhancement claim.

**10. Mostly developmental genes.**

- **NT5DC2:** fetal and BrainSeq colocalisation, no adult colocalisation, prenatal-dominant expression.
- **DNPH1:** developmental colocalisation, plus adult evidence.
- **CLCN2:** fetal colocalisation 0.99.
- **DCC and EXT1:** prenatal-dominant expression. DCC has adult rodent memory evidence.
- **KDM5B:** the dossier flags the developmental-only label as too strong, because adult mouse knockdown impairs memory.

**11. Plausible adult intervention targets.** **None.** No candidate meets criteria 1–4 of the adult intervention gate together, and safety is never auto-cleared (`decision.json`).

**12. Previously exciting genes that were downgraded.**

- **NEGR1:** likely passenger.
  - FOCUS assigns the signal to the pseudogene RPL31P12 (1.00).
  - The brainSCOPE NEGR1 eQTL is not the GWAS signal (r² 0.02).
  - The literature suggests an inverted-U dosage response.
- **RPS26:** its locus does not replicate outside UK Biobank.
- **WBP2NL, SUOX, DHRS11, ZFTRAF1, NAGA:** passengers. WBP2NL is expressed at 0.54 TPM in brain and its knockout mouse is null. Two further caveats:
  - The passenger call depends on configuration: WBP2NL wins 4 of the 8 FOCUS configurations.
  - The DHRS11 call is unstable between ZNHIT3 and GGNBP2.
- **CYP2D6:** the lead variant is in perfect LD (r² = 1.00) with the CYP2D6 S486T missense variant, and about 28% of people carry CYP2D6/CYP2D7 hybrids or copy-number variants. Its eQTL and FOCUS calls are therefore unreliable until adjusted for haplotype and copy number.
- **TUFM:** ranked #1 for research priority, but it must be read as the ATXN2L *locus*.
- **SYT1, ERBB3, MEF2C, BSN, CADM2:** no gene-level evidence.

**13. Is NEGR1 still worth pursuing?** **Not as a target.**

- The locus is only L3 outside UK Biobank (G&C z 0.97).
- Gene assignment is contested.
- The direction conflicts with the literature: the allele that raises cognition raises NEGR1, and NEGR1 overexpression impairs memory.

It is worth one computation: multi-signal colocalisation against open single-cell eQTLs, to separate NEGR1 from RPL31P12.

**14. Is NT5DC2 causal or the locus label?** **Currently the label.**

- The locus replicates in G&C (L2) but not in childhood performance IQ (GenLang z −0.23).
- NT5DC2 has brain enhancer links, but they are shared with STAB1 and UQCC5.
- It has fetal and BrainSeq colocalisation with lower expression, but no adult colocalisation.
- FOCUS favours GNL3/NEK4, and Open Targets favours STAB1.
- Best hypothesis: **developmental**, NT5DC2 ↓. It is unproven.
- Rahman 2026, which names NT5DC2, uses the same G&C data as our replication, so it is not independent.

**15. Does DCC survive causal-gene adjudication?** **The locus survives (L2); the gene does not yet.**

- DCC has one evidence class: Sprint-4 adult colocalisation rows, which are not robust across cohorts.
- brainSCOPE is null in all 17 cell types, and L2G is positional.
- Heterozygous loss-of-function carriers usually have normal IQ.
- Class: LOCUS_HIGH_GENE_UNRESOLVED (D3).

**16. Does EXOC4 survive?** **The locus is among the most robust:** G&C 2.35, GenLang 3.04. **The gene does not survive.**

- There is no variant-to-gene evidence of any class.
- The brainSCOPE EXOC4 eQTL is a separate signal (r² 0.12).
- EXOC4 is a positional label.

**17. ATXN2L / AKAP6 / EXT1 after deeper mapping.**

- **ATXN2L locus (16p11.2, the #1 locus):** a segmental-duplication-rich multi-gene region.
  - Evidence points to TUFM and EIF3C (adult eQTL), SH2B1 (brainSCOPE L2/3 IT, ↑) and NPIPB9 (developmental).
  - ATXN2L itself has no evidence. Unresolved.
- **AKAP6 locus (14q12):**
  - AKAP6 has a weak missense variant (rs1051695, PIP 0.11).
  - NPAS3 has a brain enhancer link, and Open Targets L2G favours NPAS3 (positionally).
  - Unresolved between AKAP6 and NPAS3. This is the locus most robust to the GenLang sensitivity check.
- **EXT1 (L2):** no evidence of any class. Positional only.

**18. Are there mathematically defensible top 10 / top 20 lists?**

**Yes as ranked hypotheses, not as established genes.**

- Every rank comes from pre-registered strata or Pareto layers, with rank uncertainty (see the rank intervals) and leave-one-class-out stability.
- No weighted total score is used.
- Only 2 of the Top-10 genes reach CAUSAL_GENE_MODERATE. Ranks 3–10 are gene hypotheses at replicated but gene-unresolved loci.
- The Top-20 is the first two Pareto layers (25 entities). The AKAP6 locus falls to layer 3 because it has no direction or perturbation evidence; this is disclosed.

**19. The single strongest gene-level hypothesis.**

The hypothesis is a chain:

> rs13107325 T (SLC39A8 **Thr391**, ~7% in Europeans) → reduced ZIP8 metal-ion (Mn²⁺) import → lower cognition.

Equivalently, Ala391 is the cognition-increasing allele. The evidence for each arrow:

- **Variant → gene:** EVIDENCED. Missense, PIP ≈ 1.
- **Association:** EVIDENCED in UK Biobank and G&C (L2), but **not** in GenLang or Zabaneh.
- **Cell type and brain direction:** MISSING.
- **Direction class:** loss of function, not gain of function.

It is the most concrete arrow in the project. It is not a target, because the variant is pleiotropic (manganese, lipids, blood pressure, schizophrenia, BMI) and its association with cognition is not specific.

**20. The single highest-information missing dataset.** **Within-family (direct-effect) cognition GWAS.**

- Howe 2022, ieu-b-4837/4838. The larger Tan 2025 family GWAS needs SSGAC registration.
- It is the only way to test the loci for direct effects. It is about 100% powered for the locus sign test.

**21. Public data to acquire next.**

1. Bryois 2022 single-cell brain eQTL (Zenodo, open), for cell-type **colocalisation**, not just lookup.
2. GTEx v10 brain eQTL. This is eQTL Catalogue r8 in parquet form: brain sample sizes grow by about 50%.
3. UK Biobank LD (the public PolyFun matrices), to re-fine-map the 16 L1/L2 loci.
4. The next Open Targets release when it appears.

**22. Analyses blocked only by credentials or access.**

| Analysis | What blocks it |
|---|---|
| Gate A | `OPENGWAS_JWT` |
| AlphaGenome | API key (Google sign-in plus acceptance of non-commercial terms) |
| brainSCOPE colocalisation | Synapse controlled access |
| TGFM | dbGaP GTEx access |
| 23andMe math summary statistics | a 23andMe application |
| Tan 2025 family GWAS | SSGAC registration |
| AstraZeneca PheWAS | acceptance of its terms |

**23. What would justify a dedicated one-gene programme.** All three of the following, at the same time:

1. A gene reaching **CAUSAL_GENE_MODERATE+ at an L1/L2 locus**.
2. **An adult direction at D1**: the unchanged rule, met on independent cohorts.
3. **Direct-effect support**: within-family data, or a truly non-UKB replication with the same sign.

No gene meets even the first today. The nearest are SLC39A8 (it would need a second evidence class and a consistent non-UKB sign) and KIFC2/DNPH1 (they would need a stronger locus).

**24. Does anything justify opening chemistry?** **No. The chemistry gate is CLOSED.**

**25. Exact next action.**

1. **User:** set `OPENGWAS_JWT`, or download the two Howe VCFs into `data/interim/sprint4/opengwas/`, then run:
   `python pipelines/sprint4/gate_a_within_family.py analyse`
   This runs the frozen, pre-calibrated locus test unchanged.
2. **Computational, in parallel:** coloc.susie of the 16 L1/L2 loci against Bryois 2022 open single-cell eQTLs. This resolves genes at 16p11.2 (TUFM/SH2B1/EIF3C) and 14q12 (AKAP6/NPAS3).

## Top 10 causal-gene candidates

From `TOP10_CAUSAL_GENE_CANDIDATES.csv`. This rank covers only genes that have gene-level evidence.

| Rank | Gene | Locus | Class | Evidence classes | Locus | Direction |
|---|---|---|---|---|---|---|
| 1 | KIFC2 | 8q24.3 | MODERATE | enhancer link + QTL | L3 | D4 |
| 2 | DNPH1 | 6p21.1 | MODERATE | enhancer link + QTL (+3 developmental colocs) | L3 | D4 |
| 3 | EIF3C | 16p11.2 | locus high, gene unresolved | QTL | L1 | D4 |
| 4 | TUFM | 16p11.2 | locus high, gene unresolved | QTL | L1 | D3 |
| 5 | AKAP6 | 14q12 | locus high, gene unresolved | coding (PIP 0.11) | L1 | D5 |
| 6 | NPAS3 | 14q12 | locus high, gene unresolved | enhancer link | L1 | D5 |
| 7 | STAB1 | 3p21.1 | locus high, gene unresolved | enhancer link | L2 | D5 |
| 8 | NT5DC2 | 3p21.1 | locus high, gene unresolved | enhancer link (+2 developmental colocs) | L2 | D5 |
| 9 | UQCC5 | 3p21.1 | locus high, gene unresolved | enhancer link | L2 | D5 |
| 10 | DPP4 | 2q24.2 | locus high, gene unresolved | enhancer link | L2 | D5 |

The exome-wide rare-coding genes (ANKRD12, CACNA1A, KDM5B, RC3H2) rank 17–20 as CODING_CAUSAL_LOF_ONLY.

## Top 20 research-priority panel

These are Pareto layers 1–2 over four axes: locus, gene, direction and perturbation. See `TOP20_RESEARCH_PRIORITY_GENES.csv` for all 19 required columns per entry.

- **Layer 1:**
  - TUFM, to be read as the ATXN2L locus;
  - RHEBL1;
  - KIFC2;
  - DNPH1;
  - ANKRD12, CACNA1A, KDM5B and RC3H2 (rare loss of function);
  - DCC.
- **Layer 2:**
  - EIF3C, SH2B1 and AC133550.3 (all at 16p11.2);
  - WBP2NL;
  - RPS26;
  - SLC39A8;
  - GOSR1;
  - CYP2D6;
  - NAGA;
  - EDAR, SH3RF3, SEPTIN10, SOWAHC, ZNF92, RIMS1 and CRB1 (positive-dosage results, all nominal or unreplicated).

This is **not** a list of "intelligence genes". It is the highest-information research queue.

## Negative results (first-class)

See `negative_results.csv`, 165 rows. The main ones:

- **49 signals** are discordant outside UK Biobank, and 12 more are not testable.
- **15 loci** replicate while their gene stays unresolved.
- **12 genes** are likely QTL passengers.
- **Open Targets:** 117 of 130 locus calls are positional, and 6 assignments changed.
- **brainSCOPE:**
  - it is null for ATXN2L, AKAP6, EXT1, DCC, KCNJ3, CACNA1I, SYT1, MEF2C and others;
  - the NEGR1 and EXOC4 cell-type eQTLs are separate signals;
  - no gene has opposite directions across cell types.
- **Convergence** tests T1–T5 are all null (underpowered).
- **Math-53:** 23 math-specific loci have no overlap with general cognition, and the math direction is inverted against g.
- **Positive dosage:** every duplication tested except 2q12.3 lowers cognition. 2q12.3 is unreplicated, and SEPTIN10 is predicted triplosensitive.
- **NOT_TESTABLE, recorded as such and never as NO_EFFECT:** Gate A, AlphaGenome and brainSCOPE colocalisation.

## Independence (why the numbers are small)

See `evidence_dependency_summary.md`. The graph has 1,460 evidence units and more than 2,000 dependency edges.

- **G&C is the only counted replication lineage.** GenLang (shares BATS), Zabaneh (HRS controls inside Davies) and the math factor (UKB-containing anchors) are sensitivity lines only.
- **The following all descend from one GWAS signal and never vote twice:**
  - bulk eQTL cohorts;
  - FOCUS;
  - brainSCOPE (shares donors);
  - Open Targets L2G (it aggregates the other features).

## Protocol, amendments and verification

- **Protocol:** `research/sprint5/protocol.md` and `protocol_rules.json`. The final hash is checked at run time.
- **Amendment A1:** residual labels added below every frozen class, before the first classification.
- **Amendment A2:** stable empirical-Bayes shrinkage. It was made **after** the first locus ranks had been viewed, and that is disclosed. The defective version is kept at `data/sprint5/locus_confidence_rank_KDE_TWEEDIE_DEFECTIVE.csv`.
- **Frozen-definition decision:** brainSCOPE GRN links are **not** counted as ENHANCER_LINK. The sensitivity result is disclosed under question 9.
- **Interpretation note A3:** causal-gene confidence is ranked only for genes with gene-level evidence. An unresolved locus enters the priority ranking as a locus entity.
- **Tests:** `pipelines/sprint5/test_sprint5.py`, plus the full suite, the validator and the ownership check. Results are in the commit message and in `docs/PROJECT_STATUS.md`.

## Files

- **Required outputs** are in `reports/sprint5/`:
  - `TOP20_RESEARCH_PRIORITY_GENES.csv`, `TOP10_CAUSAL_GENE_CANDIDATES.csv`
  - `causal_gene_evidence_matrix.csv`
  - `math53_gene_mapping.csv`
  - `alphagenome_math53.csv`, `alphagenome_cognition_variants.parquet`
  - `opentargets_refresh.csv`
  - `brainscope_coloc.parquet`
  - `cell_specific_directionality.csv`
  - `rare_coding_evidence.csv`, `cnv_positive_dosage.csv`
  - `common_rare_convergence.csv`
  - `modifiability_map.csv`
  - `negative_results.csv`
  - `evidence_dependency_summary.md`
  - `gene_dossiers/*.md` (20)
- **Additional outputs** in `reports/sprint5/`:
  - `locus_confidence_rank.csv`
  - `developmental_qtl_coloc.csv`
  - `v2g_convergence.csv`
  - `research_priority_entities.csv`
  - `decision.json`
- **Data** are in `data/sprint5/`:
  - `evidence_units.parquet`, `evidence_dependency_graph.parquet`
  - `math53_variants.csv`
  - `brainscope_datasets.csv`
  - `*_provenance.json`
  - `cohort_overlap_ledger.csv`
- **Research record** is in `research/sprint5/`:
  - `research_log.md`, plus the subagent logs;
  - `protocol.md`;
  - `math_audit.md`, `tools_review.md`, `genlang_overlap.md`.
