# Sprint 5: mathematics-genetics audit (math-53 re-verification)

Written 2026-09-23 (UTC) by a research subagent. Everything here comes from primary sources that were
downloaded or read in this session. The raw files and their hashes are in `data/raw/sprint5/math/PROVENANCE.json`.
The search log is in `research/sprint5/math_notes.md`.

## 1. Verdict on the "math-53" claim

| Claim as quoted to us | What the primary source says | Status |
|---|---|---|
| 53 genome-wide significant SNPs | Supp Table S2 has **exactly 53** lead SNPs. They came from a GCTA-COJO conditional and joint analysis at P<5e-8. COJO was run on 78 PLINK clump leads (r²<0.1, 1-Mb window, 1000G EUR panel), which were drawn from 5,203 genome-wide significant variants. The COJO LD reference was the MCTFR parents. | **Confirmed (53)** |
| "quantitative-ability factor" | Gq is a latent Genomic-SEM factor. Its only two indicators are **self-rated math ability** (23andMe, 5-point item, N=564,698, mean 4.71 on a 1–5 scale, which the authors call a ceiling effect) and **highest math class taken** (23andMe, 8-point item, N=430,445, age ≥25). No objective math test enters the GWAS. The authors write that the indicators "may also reflect an interest in mathematics". | **Mislabelled if taken as "ability"**: it is a self-report and course-taking proxy |
| "orthogonal to general intelligence" | Three factors are **fixed to be uncorrelated**: g (indicated by CP, SRM, HM and EA), Gq (SRM and HM) and NonCog (EA and HM). The SNP is regressed on all three at once, and every indicator residual variance is fixed to 0. The g factor is anchored only by CP, which loads only on g. So "orthogonal" means orthogonal to CP-defined g, a UK-Biobank-based verbal-numerical reasoning score. The abstract uses the phrase "orthogonal by design". | **Confirmed, but only by model construction** |
| "orthogonal to educational/non-cognitive covariance" | Yes. The NonCog factor (indicated by EA and HM) is also fixed orthogonal to Gq. | Confirmed |
| Heterogeneity | One SNP (rs13107325, a missense variant in SLC39A8) fails QSNP (P=2.7e-15), and its effects on the two indicators have opposite signs. So **52 of 53** are consistent with acting through the factor. | Caveat |

**Sample and overlap with our general-cognition GWAS (Davies 2018):**
- The math indicators come only from 23andMe, so they share no participants with UK Biobank.
- The g anchor (CP) is UK-Biobank-based. The paper text describes CP as the SSGAC meta-analysis (UKB plus COGENT, N=257,841). The authors' public OSF code (`MATH_Syntax.txt`) instead runs LDSC and `userGWAS` on `CP1_single_gwide_sumstats.txt`, labelled `CP_UKB` with N=222,914, which would be UKB only. This is an **unresolved discrepancy** between the text and the code. Either way, CP is dominated by UK Biobank and uses the same verbal-numerical reasoning test as the UKB component of Davies 2018.
- EA is the SSGAC EA3 GWAS excluding 23andMe and MCTFR (N=762,524). It includes UKB.
- The effective N of the latent GWAS is 343,237. All samples are of European ancestry.
- Every Gq SNP effect is effectively (math indicator effect) minus (loading × CP-derived g effect). This makes the Gq summary statistics **statistically dependent on UKB CP**, so a look-up of Gq SNPs in Davies 2018 is not an independent replication test.

**Summary statistics:** these are **not public**.
- The Data-availability statement says the 23andMe GWAS "must be requested from 23andMe".
- The public OSF project (osf.io/txyqr) holds only code and the supplementary tables. Its xlsx is byte-identical to the journal's MOESM2.
- The GWAS Catalog REST API returns no study for PMID 40975749.
- Nothing was downloaded to `data/interim/sprint5/math/`, because no genome-wide file exists publicly.

## 2. Math-53 against our 159 general-cognition loci (details in `reports/sprint5/math53_gene_mapping.csv`)

**Build check:** the Table S2 positions match Ensembl GRCh37 for 53 of 53 SNPs. All 53 also map to GRCh38.

**Locus overlap:** 6 of 53 SNPs fall inside a locus interval, 10 lie within 500 kb of a Sprint-3 lead, and **11 are in either category**.

| Null model | Expected count ("either" category) | One-sided P | Fold |
|---|---|---|---|
| A: fraction of Davies SNPs covered (5.3%) | 2.81 | 8.8e-5 (binomial) | 3.9 |
| B: 10,000 draws of 53 Davies SNPs matched on MAF bin × gene-density quintile | 3.10 (95th percentile 6) | 3.0e-4 (empirical) | 3.55 |

- Null B draws MAF from the UKB FI1 EAF and gene density from NCBI37.3 genes within ±500 kb.
- Inside-interval only, under null B: 6 observed vs 1.36 expected (P=0.0026).
- Within 500 kb of a lead only, under null B: 10 observed vs 2.61 expected (P=2e-4).
- LD-score matching was not possible because there is no LD-score reference in the repo.

**Sign concordance with Davies 2018:**
- All 53 SNPs were found in Davies and aligned by allele label. None is palindromic.
- For the math-increasing allele, the Davies z is positive at only **17 of 53** SNPs (binomial P=0.013; mean aligned z = −1.23).
- Among the 27 SNPs with Davies P<0.05, 6 are positive (P=0.006).
- Among the 13 SNPs with Davies P<0.05/53, **2 are positive and 11 are inverted** (P=0.022).

So the math-53 overlap with g loci is real, but it runs **mostly in the opposite direction**. The math-raising allele usually lowers Davies g, as at NEGR1 (rs7542974: Gq z=+6.8, Davies z=−6.35) and SLC39A8.

**Interpretation:** this pattern is what residualisation predicts. Gq-hat ≈ SRM-hat − λ·g-hat, and g-hat is estimated from UKB CP, which shares participants and the test with Davies. Strong g loci where the self-reported math effect is smaller than g predicts therefore enter Gq with inverted sign. The inverted overlap **must not be read as evidence that math-specific alleles lower g biologically**, and it is not evidence of shared causal genes.

**Objective arithmetic look-up (UKB fluid-intelligence items; Jiang 2021 fastGWA-GLMM):**
- These are binary items near ceiling. The GWAS Catalog reports 2,938 controls for FI1 numeric addition and 12,637 for FI4 positional arithmetic. Cases are assumed to be correct answers; this was not verified against UKB coding, so if it is wrong the signs flip.
- FI1: 27 of 52 SNPs aligned positive, mean z = +0.16, 1 of 52 at P<0.05.
- FI4: 24 of 52 positive, mean z = −0.09, 7 of 52 at P<0.05, of which only 2 are positive.
- There is **no replication signal on objective arithmetic items**. Power is limited, the items are g-loaded, and the sample is UKB.

**Per-SNP classes.** The rule is in the CSV `notes` column and is applied in this order:

| Class | Count | Rule | Detail |
|---|---|---|---|
| MATH_PROXY_ONLY | — | Checked first: QSNP P<5e-8 | Assigns rs13107325 to MATH_PROXY_ONLY; it is part of the 18 below |
| GENERAL_G_SHARED | **12** | Davies P at the SNP < 0.05/53 | 10 inverted, 2 concordant (rs4675617 near SATB2; rs685149 near CTNND1) |
| MATH_SPECIFIC_ORTHOGONAL | **23** | Davies P≥0.05 **and** outside all 159 loci **and** more than 500 kb from every lead | Specific only relative to Davies g. The phenotype is still a self-report proxy, and a null Davies result is not proof of no g effect. |
| MATH_PROXY_ONLY | **18** | QSNP SNP, nominal Davies signal, or inside or near a g locus without a SNP-level g signal | |

**Strongest math-specific (orthogonal-class) loci.** Genes are nearest-gene labels only, not causal assignments.

| SNP | GRCh37 position | Nearest gene / PoPS gene | Gq P | Davies P |
|---|---|---|---|---|
| rs72976151 | chr2:233,781,567 | NGEF / NGEF | 1.3e-15 | 0.90 |
| rs1451336 | chr6:98,742,599 | none within 500 kb (gene desert) | 5.5e-15 | 0.48 |
| rs17314727 | chr5:93,228,046 | FAM172A / NR2F1 | 3.0e-14 | 0.39 |
| rs968653 | chr2:58,296,890 | VRK2 / FANCL | 3.8e-13 | 0.82 |
| rs12830284 | chr12:60,423,137 | SLC16A7 | 7.1e-13 | 0.20 |
| rs34962646 | chr18:32,775,076 | ZNF397 / DTNA | 1.3e-12 | 0.67 |

rs968653 and rs17314727 have QSNP P of 8e-4 and 0.33. None of them is significant at the paper's QSNP threshold.

**Circularity warning for the project:** 15 of the 35 loci in `reports/sprint4/locus_finemapping.parquet` already carry Open Targets credible sets from the 23andMe "Self-reported math ability" and "Highest math class taken" GWAS (Lee 2018). These are the same indicators that underlie Gq. Math-53 look-ups therefore must not be counted as independent support at those loci.

## 3. Dataset audit (Task B)

Column key:
- Geno: individual or summary-level genotype data.
- Img: brain imaging.
- ObjMath: an objective math phenotype.
- Expert: professional mathematicians.
- Long: longitudinal follow-up.

| Dataset / study | Geno | Img | ObjMath | Expert | Long | UKB / 23andMe | Class | Citation | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Giannelis et al. 2025, Gq Genomic-SEM GWAS | summary stats (not public) | no | no in GWAS; PGS check on MCTFR WRAT-Arithmetic, N=2,641, β=0.063±0.025 | no | no | 23andMe (math indicators) + UKB (CP, EA) | **MATH_PROXY_ONLY** (built to be orthogonal to g; SNP split 12 / 18 / 23 above) | Mol Psychiatry 30:5701; doi:10.1038/s41380-025-03237-0; PMID 40975749; PMC12602337 | 53 is verified. Self-report and course-taking indicators; orthogonal to g by constraint only. Small objective validation: ΔR² 0.39%, P≈0.01, holds within family. |
| Lee et al. 2018 EA3: self-rated math ability and highest math class GWAS | summary stats (23andMe, restricted) | no | no | no | no | 23andMe only | **MATH_PROXY_ONLY** (not separated from g: rg with CP 0.60 and 0.64 per Giannelis Table 1) | Nat Genet 2018; doi:10.1038/s41588-018-0147-3; PMID 30038396 | 618 and 365 GWS SNPs respectively. These are the raw inputs to Gq and are g- and EA-saturated. |
| Lee et al. 2018 cognitive performance (CP) | summary stats (public) | no | partly (UKB verbal-numerical reasoning has numeric items) | no | no | UKB + COGENT | **GENERAL_G_SHARED** | same as above | This is the g anchor of the Gq model and overlaps Davies 2018 in UKB. |
| UKB FI item GWAS: FI1 numeric addition, FI4 positional arithmetic (GCST90042726, GCST90042729) | summary stats (public, in repo `data/interim/sumstats/`) | no | **yes** (single timed arithmetic items, binary) | no | no | UKB | **GENERAL_G_SHARED** (items not g-corrected) | Jiang et al. 2021 Nat Genet; doi:10.1038/s41588-021-00954-4; PMID 34737426 | Only objective arithmetic GWAS at biobank scale in hand. Near-ceiling binary items (about 113k/3k and 103k/13k). Math-53 shows no signal here. |
| TEDS: Procopio et al. 2025 (math independent of g) | individual genotypes + twins | no | **yes** (3 math tests at age 12, about 5,000 twin pairs) | no | TEDS is longitudinal; this analysis is cross-sectional | independent of UKB and 23andMe | **MATH_SPECIFIC_ORTHOGONAL** (phenotypic g-residualisation; heritability only, no loci) | Mol Psychiatry 2025; doi:10.1038/s41380-024-02671-w; PMID 39085392 | Twin h² of about 40% and SNP h² of about 26% on average for g-corrected specific abilities. Multi-PGS predicts about 4.4% of the g-corrected variance. Supports existence of math-specific genetic variance; identifies no variants. |
| TEDS: Davis et al. 2014 | individual genotypes + twins (GCTA) | no | yes (age 12 web tests) | no | cohort longitudinal | independent | **GENERAL_G_SHARED** | Nat Commun 2014; doi:10.1038/ncomms5204; PMID 25003214 | About half of the reading–math correlation is genetic ("generalist genes"). |
| TEDS: Docherty et al. 2010, pooled-DNA math GWAS | pooled + individual (N≈2,356) | no | yes (teacher report + web tests, age 10) | no | cohort longitudinal | independent | **GENERAL_G_SHARED** (not g-corrected) | Genes Brain Behav 2010; doi:10.1111/j.1601-183X.2009.00553.x; PMID 20039944 | 10 of 43 SNPs "validated" at P<0.05. Underpowered; none genome-wide significant. |
| ALSPAC: Donati et al. 2021, KS3 national maths test GWAS | individual genotypes, N=6,017 | no | **yes** (age 13–14 national test) | no | ALSPAC is longitudinal | independent | **MATH_SPECIFIC_ORTHOGONAL** (h²SNP persists after removing IQ or other subjects; no math locus) | Sci Rep 2021; doi:10.1038/s41598-021-82877-y; PMID 33594131 | No genome-wide significant maths SNP (the only GWS hit was for science). |
| Chen et al. 2017, Chinese schoolchildren math GWAS | individual, N≈1,597 | no | yes (school math scores) | no | no | independent (East Asian) | **GENERAL_G_SHARED** (not g-corrected) | Sci Rep 2017; doi:10.1038/srep40365; PMID 28155865 | SPOCK1 SNPs at P=5.7e-10. Small sample; not replicated in European samples. |
| Zhang et al. 2023, Chinese children, 11 math categories | individual, N=1,146 | no | yes | no | no | independent | **GENERAL_G_SHARED** (not g-corrected) | Genes Brain Behav 2023; doi:10.1111/gbb.12843; PMID 36811322 | One reasoning locus near CSMD3 (P=2.0e-8). Very small; exploratory. |
| Baron-Cohen et al. 2014, high vs low math exam grades | pooled DNA, N≈602 | no | exam grades (verbal-controlled selection) | no | no | independent | **MATH_PROXY_ONLY** (underpowered, preliminary) | PLoS One 2014; doi:10.1371/journal.pone.0096374; PMID 24801482 | rs789859 (3q29). Preliminary; not replicated. |
| Add Health: Harden et al. 2020 | individual; EA PGS only | no | course-taking / tracking | no | yes | independent | **MATH_PROXY_ONLY** | npj Sci Learn 2020; doi:10.1038/s41539-020-0060-2; PMC7002519 (abstract-level only, via search snippet) | EA PGS predicts math track and persistence. No math GWAS. |
| Finland, Norway, Netherlands: Cheesman et al. 2025, educational-field GWAS | summary-level | no | no (field choice) | no | registers | **independent of UKB and 23andMe** | **MATH_PROXY_ONLY** | Nat Genet 2025; doi:10.1038/s41588-025-02391-z; PMID 41188532 | 17 variants across 7 of 10 fields. Field choice reflects interest and sorting, not ability. Not checked whether a STEM/math field has its own loci. |
| MoBa: Cheesman et al. 2025, grade-9 numeracy national tests | individual trios, N≈30,939 | no | **yes** (numeracy tests) | no | yes (register) | independent | **GENERAL_G_SHARED** (EA PGI only; no math GWAS found) | PNAS 2025; doi:10.1073/pnas.2511715122; PMID 41134622 | Best candidate independent objective-numeracy genotype resource. No numeracy GWAS summary statistics located. |
| Amalric & Dehaene 2016: 15 professional mathematicians vs 15 humanities specialists | **no** | fMRI | expert task stimuli | **yes** | no | n/a | **IMAGING_ONLY** | PNAS 2016; doi:10.1073/pnas.1603205113; PMID 27071124 | Math statements engage bilateral intraparietal, inferior-temporal and frontal regions, sparing language areas. **No genotypes collected.** |
| Amalric & Dehaene 2019 | **no** | fMRI | expert tasks | **yes** | no | n/a | **IMAGING_ONLY** | NeuroImage 2019; doi:10.1016/j.neuroimage.2019.01.001; PMID 30611876 | Replicates a distinct non-linguistic math network. No genetics. |
| BrainSCALE: Koenis et al. 2015 and 2018 | twin design (no molecular genotypes) | DTI | **no** (IQ only) | no | **yes** (ages about 10, 13, 18) | independent | **GENERAL_G_SHARED** | Hum Brain Mapp 2015 (doi:10.1002/hbm.22988, PMID 26368846); Hum Brain Mapp 2018 (doi:10.1002/hbm.23885, PMID 29139172) | Network efficiency is heritable, and its genetic correlation with IQ rises with age. Concerns intelligence, not mathematics. |

**Not found in this session.** Each of these is a search result, not proof that nothing exists:
- a genotyped cohort of professional mathematicians;
- a large (N>50k) GWAS of an objective, g-corrected mathematics test published 2024–2026;
- public genome-wide summary statistics for any math-specific (g-orthogonal) phenotype.

The Procopio 2025 Behav Genet g-corrected Genomic-SEM test statistics (doi:10.1007/s10519-025-10213-5) cover 12 verbal and UKB non-verbal tests, and none of them is a math test.

## 4. Bottom line for Sprint 5

1. Professional-mathematician imaging (Amalric & Dehaene) is **not** mathematician genetics. No study links genotypes to mathematical expertise.
2. The only locus-level "math-specific" resource is Giannelis Gq. It is a self-report and course-taking proxy, orthogonal to g by model constraint. It depends on UKB CP, its summary statistics are unavailable, and it gives no signal on UKB objective arithmetic items.
3. Its overlap with our g loci is enriched about 3.5× but mostly sign-inverted, which is consistent with a residualisation artefact. It cannot serve as independent support for any Sprint-3 or Sprint-4 cognition gene.
4. Evidence for math-specific genetic variance at the heritability level is real: TEDS and ALSPAC show twin and SNP h² for math after g-correction. None of it resolves to loci.
