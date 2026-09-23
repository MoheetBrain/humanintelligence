# Extreme-IQ continuity — reassessment of the Sprint-3 "1.13x" result

*2026-09-23 · Sprint 3.1 · data: Zabaneh 2018 extreme IQ (GCST005626; 1,238 Duke TIP cases, 8,172 HRS controls) vs Davies 2018 (N=282,014). Code: `pipelines/sprint3_1/extreme_tail_reassessment.py`.*

## What Sprint 3 computed

For the 375 population-Bonferroni genes, Sprint 3 predicted the extreme-tail mean MAGMA gene Z as:

> rest-of-genome mean + (Davies mean Z of the 375 − genome mean) / √(282,014 / 4,300)

It found the observed shift to be 1.13× the prediction, and wrote "continuous … no upper-tail amplification is required".

## Why the ratio cannot carry that conclusion

1. **Extreme ascertainment.**
   - Cases are roughly the top 0.03% (mean standardised trait value i ≈ 3.7). Controls are unselected.
   - The case-control non-centrality is N_eff·i²/4 times the per-person quantitative-trait value. The equivalent population N is therefore about 14,600, not 4,300.
   - With that N the same arithmetic gives 0.61×.
   - Cases were selected on SAT scores at about age 12. Measurement error and regression to the mean lower the effective i, which pushes the ratio back toward 1.
2. **Winner's curse.** The 375 genes were selected on Davies Z, which inflates the predicted shift. Re-evaluating them in Savage 2018 reduces, but cannot remove, this, because Savage shares UK Biobank.
3. **Non-linearity.** MAGMA gene Z is the probit of a P-value from a sum of squared SNP z-scores, so it does not scale with √N. The proper expectation needs LD-aware subsampling to the equivalent N (the Sprint-4 calibration method). It is not attempted here.
4. **Sample overlap.** Zabaneh's controls are the Health and Retirement Study.
   - **Verified from source** (`literature_curation.json`): HRS is a contributing cohort of Davies 2018 (Supplementary Note 2; about 7,400 with cognitive data).
   - Zabaneh's cases AND controls are both inside Savage 2018 (its "HiQ/HRS" cohort).
   - The shared individuals are Zabaneh CONTROLS, whose extreme-IQ phenotype is constant. Under a standard regression, the noise covariance they induce with Davies' mean-centred cognition statistic is approximately zero. So the bias toward continuity is expected to be small, but it is not formally estimated here.
   - If HRS contributes to Davies, shared noise inflates every agreement statistic toward continuity.

### Sensitivity table

| population Z source | scenario | equivalent N | predicted shift | observed shift | observed / predicted |
|---|---|---|---|---|---|
| Davies Z (selection sample; Sprint 3) | Sprint-3 assumption: N_eff = 4,300 | 4,300 | 0.577 | 0.652 | **1.13** |
| Davies Z (selection sample; Sprint 3) | ascertainment-equivalent N, cases = top 0.03% (i = 3.69) | 14,613 | 1.064 | 0.652 | **0.61** |
| Davies Z (selection sample; Sprint 3) | ascertainment-equivalent N, cases = top 0.3% (i = 3.05) | 9,998 | 0.880 | 0.652 | **0.74** |
| Davies Z (selection sample; Sprint 3) | ascertainment-equivalent N, cases = top 3% (i = 2.27) | 5,530 | 0.654 | 0.652 | **1.00** |
| Savage Z for the same genes (winner's-curse sensitivity; overlaps UKB) | Sprint-3 assumption: N_eff = 4,300 | 4,300 | 0.522 | 0.652 | **1.25** |
| Savage Z for the same genes (winner's-curse sensitivity; overlaps UKB) | ascertainment-equivalent N, cases = top 0.03% (i = 3.69) | 14,613 | 0.962 | 0.652 | **0.68** |
| Savage Z for the same genes (winner's-curse sensitivity; overlaps UKB) | ascertainment-equivalent N, cases = top 0.3% (i = 3.05) | 9,998 | 0.795 | 0.652 | **0.82** |
| Savage Z for the same genes (winner's-curse sensitivity; overlaps UKB) | ascertainment-equivalent N, cases = top 3% (i = 2.27) | 5,530 | 0.592 | 0.652 | **1.10** |

Range: 0.61–1.25. The number straddles 1, so it cannot distinguish continuity from attenuation or amplification.

## A second error: "121/159 loci agree in sign" was not a sign test

MAGMA gene Z is unsigned. "Positive extreme-tail Z" meant *above-median association*, not the same allele direction. The 62% background rate reflects genome-wide inflation of gene Z.

## The defensible evidence: allele-direction concordance at the 159 loci

Method:

- Davies lead SNP per locus (the rule frozen in the Sprint-4 protocol);
- cognition-increasing allele looked up in Zabaneh, z = ln OR / SE, aligned by allele;
- palindromic SNPs excluded.

Result:

- **112 of 136 testable loci concordant (82%); one-sided binomial P = 4.3e-15.**
- Loci not testable: 3 absent, 20 palindromic, 0 with mismatched alleles.
- Continuity predicts, using Tweedie-shrunk Davies z to reduce winner's curse:
  - N_eff 4,300: 97.5 (72%).
  - equivalent N, top 0.03%: 114.2 (84%).
  - equivalent N, top 3%: 100.8 (74%).

The observed concordance sits inside the range continuity predicts, well above chance. Per-locus table: `extreme_tail_locus_direction.csv`.

## Corrected conclusion

**No strong evidence for a distinct common-variant architecture in the extreme tail.** Supporting this:

- the same alleles push in the same direction (sign test above);
- no gene is tail-specific (0 genome-wide significant genes);
- the published LDSC genetic correlations (Zabaneh 2018, Table 2):
  - rg 0.75 (SE 0.13) with Childhood IQ (Benyamin et al. 2014, Childhood Intelligence Consortium (CHI).
  - rg 0.8 (SE 0.08) with Cognitive performance (Davies et al. 2015, CHARGE consortium, N=53,949).
  - rg 0.79 (SE 0.08) with College completion (Okbay et al. 2016 educational attainment).
  - rg 0.79 (SE 0.07) with Years of education (Okbay et al. 2016 educational attainment).
  - rg 0.86 (SE 0.1) with Verbal-numerical reasoning (VNR-UKB) (Davies et al. 2016, UK Biobank N=112,151).
  - LDSC rg is not biased by sample overlap.

Not established:

- that effect *magnitudes* scale exactly as a continuous model predicts (the ratio is not identifiable from these data);
- anything about rare variants.

The HRS/Davies overlap question remains open and biases toward this conclusion. The earlier wording "1.13x … proves continuity" is withdrawn.

### Curated literature (PMID-verified)

- Extreme high IQ and normal-range IQ share most of their common-variant architecture: rg 0.80 (SE 0.08) against CHARGE cognitive performance and 0.86 (SE 0.10) against UK Biobank verbal-numerical reasoning, by LD Score regression.
- Liability-scale SNP heritability 0.33 (SE 0.02) by GCTA at assumed prevalence 0.0003; 0.42 (SE 0.06) by LD Score regression.
- The only genome-wide significant locus, ADAM12, did not replicate in normal-range GWAS and may be specific to the extreme or be a false positive from the separately-genotyped case-control design.
- Zabaneh controls are HRS, which is inside Davies 2018 and Davies 2015; Zabaneh cases and controls are both inside Savage 2018. Neither pair is independent.

