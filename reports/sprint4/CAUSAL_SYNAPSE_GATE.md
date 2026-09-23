# Sprint 4 — Direct-Effect Causal Synapse Gate

*2026-09-23 · branch `sprint-4/causal-synapse-bridge` · protocol frozen at `db86aef` before any new data (`research/sprint4/protocol.md`, JSON sha256 `44eb27217ec4c7a7…`) · all computational · chemistry gate **CLOSED**.*

## Decision: **RETRY**

Decided by the frozen precedence (STOP > PIVOT > RETRY-if-Gate-A-untestable > CONTINUE > ESCALATE > RETRY):

- **STOP_CURRENT_HYPOTHESIS:** not met — requires the PIVOT condition in BOTH gates; Gate A untestable
- **PIVOT:** not met — Gate B: 0 of 6 frozen sets INCONSISTENT beyond noise (needs >=3 with simulated power >=0.5 at f_gc_lower=0.752); Gate A untestable
- **RETRY:** MET — all six frozen sets are NOT_TESTABLE in Gate A because the within-sibship data need an OpenGWAS JWT (access), which ranks above CONTINUE/ESCALATE in the frozen precedence
- **CONTINUE:** cannot be assessed — requires >=1 set DIRECT_EFFECT_SUPPORTED in Gate A
- **ESCALATE:** not assigned — superseded by RETRY in the frozen precedence

## The fifteen answers

**1. Were the OpenGWAS family data available?** **No.**

- `OPENGWAS_JWT` is absent. OpenGWAS automated download requires it, and no account was created.
- The dataset identities were verified from public metadata: ieu-b-4837 is the sibling estimate (N=9,997) and ieu-b-4838 the population estimate (N=22,593), from Howe 2022, GRCh37.
- All Gate-A code, up to the download boundary, is written and tested on synthetic GWAS-VCFs.

**2. Direct-effect attenuation of the cognition signal.**

- **Not measured: NOT_TESTABLE.**
- What the data *would* have to show was computed before any family data existed (frozen PUMAS-style calibration below).
- Howe 2022's genome-wide figure is 21.6% shrinkage (95% CI 6.4–36.8), from a P<1e-5 score; our frozen f=0.78 matches it.
- A larger family-GWAS estimate (Tan et al. 2024) puts the direct–population genetic correlation for cognition at 0.54. If that holds, the direct fraction may be lower than f=0.78, and power lower than calibrated.

**3. The six frozen synaptic sets.**

| set | Gate A (within-family) | Gate B: G&C TMA β (P) | Gate B class | expected β if f=0.752 [2.5%, 97.5%], power (n=9,997) |
|---|---|---|---|---|
| `GO_0042734` presynaptic membrane | NOT_TESTABLE | +0.050 (0.238) | CONCORDANT_BUT_UNDERPOWERED | +0.014 [-0.100, +0.138], power 10% |
| `GO_0099560` synaptic membrane adhesion | NOT_TESTABLE | -0.093 (0.761) | INCONSISTENT / SIGN_DISCORDANT_WITHIN_NOISE | +0.037 [-0.147, +0.228], power 5% |
| `GO_0099056` integral component of presynaptic memb | NOT_TESTABLE | +0.059 (0.226) | CONCORDANT_BUT_UNDERPOWERED | +0.004 [-0.116, +0.202], power 10% |
| `GO_0099508` voltage-gated ion channel activity inv | NOT_TESTABLE | +0.336 (0.068) | CONCORDANT_BUT_UNDERPOWERED | -0.010 [-0.389, +0.434], power 10% |
| `GO_0045202` synapse | NOT_TESTABLE | +0.027 (0.137) | CONCORDANT_BUT_UNDERPOWERED | +0.002 [-0.039, +0.035], power 2% |
| `SYNGO_synprocess` process in the synapse | NOT_TESTABLE | +0.052 (0.031) | INDEPENDENT_SUPPORT | -0.004 [-0.038, +0.052], power 8% |

Pre-data expectation for Gate A: the Davies GWAS subsampled to the within-family effective N (≈4,999 for sibling pairs), with LD-aware noise, then run through the identical MAGMA pipeline. Each cell gives the median simulated set β [2.5%, 97.5%] and power at P<0.05:

| set | f=1.0, n=4,999 | f=0.78, n=4,999 | f=0.78, n=9,997 | null (f=0) |
|---|---|---|---|---|
| `GO_0042734` | +0.011 [-0.102, +0.138], power 10% | +0.003 [-0.108, +0.136], power 10% | +0.016 [-0.099, +0.139], power 10% | +0.004 [-0.120, +0.130], power 10% |
| `GO_0099560` | +0.033 [-0.147, +0.224], power 2% | +0.023 [-0.157, +0.212], power 2% | +0.039 [-0.146, +0.230], power 5% | -0.006 [-0.165, +0.189], power 2% |
| `GO_0099056` | +0.002 [-0.119, +0.202], power 10% | -0.006 [-0.125, +0.205], power 10% | +0.005 [-0.115, +0.201], power 10% | -0.004 [-0.141, +0.203], power 10% |
| `GO_0099508` | -0.012 [-0.383, +0.439], power 8% | -0.022 [-0.409, +0.456], power 8% | -0.008 [-0.392, +0.439], power 10% | -0.026 [-0.393, +0.529], power 5% |
| `GO_0045202` | +0.001 [-0.039, +0.035], power 2% | -0.001 [-0.040, +0.036], power 0% | +0.002 [-0.039, +0.035], power 2% | +0.001 [-0.041, +0.028], power 2% |
| `SYNGO_synprocess` | -0.004 [-0.039, +0.052], power 8% | -0.002 [-0.042, +0.050], power 8% | -0.004 [-0.037, +0.052], power 8% | -0.006 [-0.051, +0.046], power 5% |

Replicates completed per scenario: n22593_f0: 40, n22593_f0.78: 40, n22593_f1: 40, n4999_f0.78: 40, n4999_f1: 40, n9997_f0.752: 40, n9997_f0.78: 40, n9997_f1: 40 (frozen target 40).

**4. The independent G&C result** (NIHR BioResource Genes & Cognition, N=9,932, G&C-only files):

- **Phenotype:** EXECUTIVE_FUNCTION (trail making B, TMA; higher = slower), not GENERAL_COGNITION. rg(TMA, intelligence) = −0.752.
- **Pipeline positive control (PASS):** NT5DC2 rs7639267 G allele, β=0.00616 (SE 0.00198, P=0.0018). Published: 0.0062 (0.002, 0.0018).
- **Sets:**
  - 1 of 6 frozen sets reach P<0.05 on TMA (process in the synapse, P=0.031); none is Bonferroni over 6.
  - 5 of 6 are positive.
  - Synaptic membrane adhesion is negative.
- **Loci (the strongest independent result).** At the 145 testable Sprint-3 lead SNPs, **109 (75%) have the cognition-increasing allele also speeding trail making** (one-sided binomial P=5.0e-10).
  - Continuity expects 74%–80%.
  - The effect-size slope is 0.122 (SE 0.014, P=6.0e-19). The upper bound ignoring winner's curse is 0.141.

**5. How many of the 159 loci retain direct-effect support?** **None can be assessed:** Gate A is NOT_TESTABLE. Independent (Gate B) support per the frozen rule: **33** loci (≈14.5 expected by chance). At BH-FDR<0.05, 4 loci.

**6. Survivor genes/loci** (33 Gate-B survivors, plus stress tests and control; full table `direct_effect_survivors.csv`). By BH q among testable loci:

| locus | top gene | TMA aligned z | one-sided P | BH q |
|---|---|---|---|---|
| L51327 | ATXN2L | 3.44 | 2.9e-04 | 0.021 |
| L64067 | AKAP6 | 3.52 | 2.2e-04 | 0.021 |
| L91869 | NT5DC2 | 3.09 | 9.8e-04 | 0.048 |
| L2131 | EXT1 | 3.00 | 0.001 | 0.049 |
| L51460 | SFMBT1 | 2.81 | 0.003 | 0.073 |
| L1803 | DPP4 | 2.74 | 0.003 | 0.075 |
| L83594 | NUDT12 | 1.96 | 0.025 | 0.186 |
| L55168 | CUL9 | 1.96 | 0.025 | 0.186 |
| L8911 | CACNA1I | 1.99 | 0.023 | 0.186 |
| L403314 | SMG7 | 2.16 | 0.015 | 0.186 |
| L7009 | DDN | 2.30 | 0.011 | 0.186 |
| L6319 | CPN1 | 2.01 | 0.022 | 0.186 |

**7. Did NT5DC2 replicate as the pipeline positive control?** **Yes.**

- rs7639267 reproduces the published G&C estimate: PASS.
- The NT5DC2 locus lead (rs6778735) is also G&C-supported: aligned z = 3.09.
- NT5DC2 stays PRENATAL_DOMINANT. The curated literature finds no direct synaptic function, so replication does not make it an adult target.

**8. Fine-mapped survivor loci.**

- SuSiE-RSS sensitivity ran on 36 Gate-C loci: 35 converged, 0 flagged for LD mismatch (s > 0.2).
- The Open Targets GWAS credible sets stay primary, since out-of-sample 1000G LD with N=282k over-splits signals (NEGR1 gave 6 sets in the first run).
- Variants only: no lead SNP or nearest gene is equated with a causal gene.
- Per-locus sets: `locus_finemapping.parquet`.

**9. Adult-brain colocalisations.**

- 19 adult gene-level brain QTL datasets from the eQTL Catalogue: Braineac2, CommonMind, GTEx, ROSMAP, Young_2019.
- BrainSeq, Walker 2019, Aygün 2021, Jerber 2021 and Schwartzentruber 2018 were excluded as non-adult.
- 4780 locus × gene × dataset pairs were tested with coloc.abf.
- **68 pairs are strong (PP.H4 ≥ 0.8)**, covering 20 genes: CLCN2, CYP2D6, DCC, DHRS11, DNPH1, EIF3C, FHIP1A, GGNBP2, GOSR1, KIFC2, MYO19, NAGA, NEGR1, NPIPB9, RECQL4, RHEBL1, SUOX, TUFM, WBP2NL, ZFTRAF1.

**10. Directionally resolved genes** (unchanged rule: ≥3 strong gene-level adult-brain colocs, ≥80% agreement, confirmed on independent QTL cohorts):

- **RPS26** (L319): cognition-increasing allele -> HIGHER expression in adult brain (commonmind, gtex, rosmap). 30 rows, 100% agreement; 3 cohorts, 100% agreement.
- **RHEBL1** (L7009): cognition-increasing allele -> HIGHER expression in adult brain (commonmind, gtex, rosmap). 4 rows, 100% agreement; 3 cohorts, 100% agreement.
- Resolved on rows only, not robust across cohorts: DHRS11, CYP2D6, GOSR1, NAGA, NEGR1, TUFM, ZFTRAF1, SUOX, DCC.
- NEGR1: RESOLVED_ON_ROWS_ONLY_NOT_ROBUST (5 rows; 1 cohort units).
- SYT1: UNRESOLVED_NO_STRONG_COLOC (0 rows; 0 cohort units).
- RPS26: DIRECTION_RESOLVED (30 rows; 3 cohort units).

**11. Joint gene/tissue fine-mapping** (FOCUS, pyfocus 0.803; GTEx v7 PredictDB and CommonMind FUSION adult-brain weights, GRCh37, with 1000G EUR LD). Six loci: three prespecified (L319, L91869, L257194) and three added AFTER the colocalisation results as the multi-gene loci carrying the strongest direction evidence (L7009 RHEBL1, L79922 DHRS11, L1565 CYP2D6/NAGA) — a disclosed, post-hoc choice. Gene PIP is summed over tissue models within each configuration; the primary configuration is joint_brain_gene_x_tissue_p1e-3:

| locus | configuration | top gene (PIP) | 2nd gene (PIP) | null-model PIP |
|---|---|---|---|---|
| L1565 | brain_prioritized_gene_p1e-3 | WBP2NL (0.92) | CYP2D6 (0.05) | 9.3e-06 |
| L1565 | brain_prioritized_gene_p1e-3_intercept | WBP2NL (0.86) | CYP2D6 (0.11) | 9.3e-05 |
| L1565 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | WBP2NL (0.87) | CYP2D6 (0.09) | 4.7e-07 |
| L1565 | brain_prioritized_proxy_tissue_fallback_p1e-3 | WBP2NL (0.89) | CYP2D6 (0.05) | 9.6e-06 |
| L1565 | gtexv8_eur_brain_cortex_only_p1e-3 | ENSG00000232710.1 (0.45) | ENSG00000270083.1 (0.43) | 2.1e-06 |
| L1565 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | ENSG00000232710.1 (0.32) | ENSG00000270083.1 (0.31) | 7.8e-05 |
| L1565 | joint_brain_gene_x_tissue_p1e-3 | CYP2D6 (0.81) | NAGA (0.09) | 9.4e-07 |
| L1565 | joint_brain_gene_x_tissue_p1e-3_intercept | CYP2D6 (0.76) | WBP2NL (0.13) | 1e-05 |
| L257194 | brain_prioritized_gene_p1e-3 | RPL31P12 (1.00) | NEGR1 (0.11) | 1.1e-06 |
| L257194 | brain_prioritized_gene_p1e-3_intercept | RPL31P12 (0.99) | NEGR1 (0.37) | 0.0086 |
| L257194 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | RPL31P12 (1.00) | NEGR1 (0.87) | 1.8e-09 |
| L257194 | brain_prioritized_proxy_tissue_fallback_p1e-3 | RPL31P12 (1.00) | NEGR1 (0.11) | 1.2e-06 |
| L257194 | gtexv8_eur_brain_cortex_only_p1e-3 | NULL.MODEL (1.00) | TNNI3K (0.00) | 1 |
| L257194 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | NULL.MODEL (1.00) | ENSG00000269933.1 (0.00) | 1 |
| L257194 | joint_brain_gene_x_tissue_p1e-3 | RPL31P12 (1.00) | NEGR1 (0.10) | 1e-06 |
| L257194 | joint_brain_gene_x_tissue_p1e-3_intercept | RPL31P12 (0.98) | LRRIQ3 (0.39) | 0.021 |
| L319 | brain_prioritized_gene_p1e-3 | RPS26 (0.69) | SUOX (0.31) | 0.0013 |
| L319 | brain_prioritized_gene_p1e-3_intercept | RPS26 (0.67) | SUOX (0.33) | 0.00093 |
| L319 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | RPS26 (0.70) | SUOX (0.31) | 0.00012 |
| L319 | brain_prioritized_proxy_tissue_fallback_p1e-3 | RAB5B (0.64) | RPS26 (0.25) | 0.00053 |
| L319 | gtexv8_eur_brain_cortex_only_p1e-3 | RPS26 (0.70) | SUOX (0.30) | 0.00027 |
| L319 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | NULL.MODEL (0.42) | SUOX (0.30) | 0.42 |
| L319 | joint_brain_gene_x_tissue_p1e-3 | RPS26 (0.99) | SUOX (0.01) | 7.9e-06 |
| L319 | joint_brain_gene_x_tissue_p1e-3_intercept | RPS26 (0.99) | SUOX (0.02) | 1.3e-05 |
| L7009 | brain_prioritized_gene_p1e-3 | RP1-228P16.1 (0.92) | FMNL3 (0.46) | 0.054 |
| L7009 | brain_prioritized_gene_p1e-3_intercept | RP1-228P16.1 (0.83) | NULL.MODEL (0.17) | 0.17 |
| L7009 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | RP1-228P16.1 (0.99) | FMNL3 (0.88) | 0.0011 |
| L7009 | brain_prioritized_proxy_tissue_fallback_p1e-3 | DDN (1.00) | FMNL3 (0.51) | 2.3e-05 |
| L7009 | gtexv8_eur_brain_cortex_only_p1e-3 | RHEBL1 (1.00) | MCRS1 (0.02) | 0.0014 |
| L7009 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | RHEBL1 (0.97) | NULL.MODEL (0.03) | 0.026 |
| L7009 | joint_brain_gene_x_tissue_p1e-3 | PFKM (0.77) | FMNL3 (0.28) | 0.00063 |
| L7009 | joint_brain_gene_x_tissue_p1e-3_intercept | PFKM (0.79) | RHEBL1 (0.17) | 0.011 |
| L79922 | brain_prioritized_gene_p1e-3 | ZNHIT3 (0.51) | DHRS11 (0.44) | 0.0018 |
| L79922 | brain_prioritized_gene_p1e-3_intercept | ZNHIT3 (0.50) | DHRS11 (0.43) | 0.0023 |
| L79922 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | DHRS11 (0.57) | SYNRG (0.42) | 1.7e-05 |
| L79922 | brain_prioritized_proxy_tissue_fallback_p1e-3 | DHRS11 (0.39) | ZNHIT3 (0.34) | 0.0013 |
| L79922 | gtexv8_eur_brain_cortex_only_p1e-3 | GGNBP2 (0.65) | DHRS11 (0.32) | 0.0017 |
| L79922 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | GGNBP2 (0.82) | DHRS11 (0.15) | 0.0009 |
| L79922 | joint_brain_gene_x_tissue_p1e-3 | DHRS11 (0.80) | TADA2A (0.24) | 0.00068 |
| L79922 | joint_brain_gene_x_tissue_p1e-3_intercept | DHRS11 (0.80) | TADA2A (0.26) | 0.00062 |
| L91869 | brain_prioritized_gene_p1e-3 | NEK4 (0.97) | NISCH (0.03) | 1.8e-07 |
| L91869 | brain_prioritized_gene_p1e-3_intercept | NULL.MODEL (0.74) | DNAH1 (0.05) | 0.74 |
| L91869 | brain_prioritized_gene_prior_1_over_ngenes_grch37 | NEK4 (0.97) | NISCH (0.24) | 6.2e-09 |
| L91869 | brain_prioritized_proxy_tissue_fallback_p1e-3 | NEK4 (0.68) | ITIH3 (0.30) | 1.2e-07 |
| L91869 | gtexv8_eur_brain_cortex_only_p1e-3 | SPCS1 (0.55) | PPP2R5CP (0.25) | 7e-07 |
| L91869 | gtexv8_eur_brain_cortex_only_p1e-3_intercept | NULL.MODEL (0.78) | PPM1M (0.19) | 0.78 |
| L91869 | joint_brain_gene_x_tissue_p1e-3 | GNL3 (0.99) | NEK4 (0.01) | 2e-09 |
| L91869 | joint_brain_gene_x_tissue_p1e-3_intercept | PPM1M (0.87) | NULL.MODEL (0.06) | 0.062 |

Reading:

- **12q13.2 (L319):** RPS26 is favoured in every configuration. ERBB3, a Top-50 gene, never appears. SUOX is the only alternative.
- **1p31.1 (NEGR1):** the best-explaining model is a pseudogene's (RPL31P12). NEGR1 stays below 0.4, and the single-tissue v8 build favours the null. So NEGR1 is not confirmed as the mediating gene.
- **3p21.1 (NT5DC2):** the top gene changes with configuration (GNL3, NEK4, PPM1M). NT5DC2 is never top. The locus is gene-ambiguous.
- **12q13.12 (L7009, RHEBL1):** the gene is ambiguous. The primary configuration favours PFKM (0.77; RHEBL1 0.22). Only the single-tissue GTEx v8 cortex build gives RHEBL1 about 1.0; other configurations pick a lncRNA or DDN. RHEBL1's direction-resolved colocalisation therefore lacks credible locus-to-gene support.
- **17q12 (L79922):** DHRS11 in the primary configuration (0.80); ZNHIT3 or GGNBP2 in others.
- **22q13.2 (L1565):** CYP2D6 in the primary configuration (0.81); WBP2NL (0.86–0.92) in the per-gene configurations. Gene-ambiguous.
- FOCUS favours genes with strong expression models (a known bias toward eQTL hubs), so none of this is causal proof.
- **TGFM blocked:** TGFM ships no pre-fit gene-tissue models (Zenodo record contains only a 128 kB code zip). Step 1 (susie_eqtl_fine_mapping_for_tgfm.py) needs either individual-level eQTL genotypes + expression, or full eQTL summary statistics PLUS in-sample eQTL genotypes; for GTEx brain tissues both require dbGaP phs000424 controlled access (registration/approval not allowed here). Step 2 requires GWAS in-sample 
- **cTWAS blocked:** Scope/time blocker, not an access blocker: cTWAS separates mediated from non-mediated (SNP) effects only after genome-wide estimation of gene and SNP prior inclusion probabilities and effect variances over all ~1,700 LD blocks, which needs genome-wide region/SNP maps and LD for every block plus multi-tissue weights; this did not fit the ~90 min / 3-thread budget alongside the running MAGMA job. A 

**12. Strongest negative finding.**

- The frozen synaptic *sets* do not independently replicate as a group in G&C: 1 of 6 is nominal, 0 of 6 Bonferroni, and adhesion is negative. This is so even though the *loci* replicate strongly.
- The calibration shows why this is uninformative rather than negative. At n≈10k, set-level power is 2–12.5% *even for a fully direct effect*, the same as under the null. The same holds for the within-family sample at N_eff 5–10k.
- **The Sprint-3 set-level signal therefore cannot be confirmed or refuted by any currently open direct-effect or UKB-free sample.** This is the sprint's most consequential negative result.
- **No gene clears the causal chain:**
  - RPS26 is direction-resolved with credible locus-to-gene evidence, but it lacks independent cognition support (G&C aligned z −0.83).
  - RHEBL1 is direction-resolved and nominally G&C-supported, but its locus-to-gene attribution is unstable (FOCUS primary PFKM).
  - NEGR1's best expression model is a pseudogene's.
  - SYT1 has no strong gene-level colocalisation.

**13. Primary decision: RETRY.**

**14. Chemistry gate: CLOSED.** No gene meets all five frozen criteria (independent support, credible locus-to-gene evidence, adult-brain molecular evidence, consistent direction, no disqualifying safety/pleiotropy signal); safety/pleiotropy is never cleared automatically.

**15. Single highest-information next action.**

Unlock Gate A: the Howe 2022 within-sibship and population VCFs. This takes one user action (below), and one command then runs the complete, frozen, pre-calibrated test.

What it would decide is the **locus-level** direct-effect question, not set-level enrichment. The frozen calibration gives:

- a locus sign test with power 100% at N_eff 5k;
- set-level power of 12.5% or less.

So Gate A can tell whether the 159 loci act *directly* (within families) or through stratification or indirect effects. That is exactly the question Gate B cannot answer.

- **Minimal user action:** Set OPENGWAS_JWT (a token from https://api.opengwas.io/profile/ after signing in) in the shell environment, then run: python pipelines/sprint4/gate_a_within_family.py fetch && python pipelines/sprint4/gate_a_within_family.py analyse
- Or, without any token: open https://gwas.mrcieu.ac.uk/datasets/ieu-b-4837/ and https://gwas.mrcieu.ac.uk/datasets/ieu-b-4838/, click 'VCF Files', and save both .vcf.gz files into data/interim/sprint4/opengwas/ (the website allows 20 datasets/day), then run the analyse command.

## Provenance and verification

- **Frozen protocol:** `research/sprint4/protocol.md` + `frozen_hypotheses.json`, committed in `db86aef` before any Howe or G&C association value was read.
  - Two arbitrary G&C rows (rs12238997, rs72631875; not at any frozen locus) were displayed while checking the file format after the freeze.
- **G&C data:** Zenodo 10.5281/zenodo.11066096, files `tm{a,n,d}_gwas_gc.txt`, md5-verified against the Zenodo listing (sha256 in `data/sprint4/gate_b_summary.json`).
  - GRCh37, A1 = effect allele, BOLT-LMM.
  - Gene-level MAGMA outputs are in `data/raw/sprint4/genc_magma/`.
- **QTL data:** eQTL Catalogue public tabix-indexed summary statistics, with provenance in `data/raw/sprint4/eqtl_catalogue/PROVENANCE.json`.
- **Software:** MAGMA v1.10 (same binary as Sprint 3); R 4.4.3 with susieR 0.14.2 and coloc 5.2.3; htslib 1.24; Python 3.12.
- **Tests:** `pipelines/sprint4/test_sprint4.py` (see the commit message for results).

## Negative results register

`negative_results.csv`, counts by category:

- GWAS/QTL pair with distinct causal variants (PP.H3>=0.8): 559
- locus — no independent G&C support: 112
- credible signal without adult-brain QTL colocalisation: 16
- locus — G&C lookup not testable: 14
- unresolved allele harmonisation: 10
- development-dominant expression (survivor/stress/control): 10
- direction resolved on rows but not on independent cohorts: 9
- frozen set — direct-family test: 6
- frozen set — independent G&C test (TMA): 5
- same signal colocalises with multiple genes: 4
- analysis blocked: 3
- locus — direct-effect (within-family) support: 1
- analysis excluded by rule: 1

*Generated 2026-09-23T15:40Z by `pipelines/sprint4/write_sprint4_report.py`.*
