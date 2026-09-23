# Sprint 5: math research log (math-53 verification and math re-audit)

All times are UTC on 2026-09-23. They are taken from download timestamps or the system clock, and are accurate to a few minutes.
The analysis scripts are in the session scratchpad and were **not** added to the repo, because this task was restricted to the output paths:
`math53_analysis.py` and `write_outputs.py` under `/private/tmp/claude-501/.../scratchpad/`.
Their logic is fully described below and in the `notes` column of `reports/sprint5/math53_gene_mapping.csv`. If the analysis should be reproducible from the repo, move them to `pipelines/sprint5/`.

---

### S1. 21:04 — Locate the primary math-53 source
- **Question:** Which paper is "math-53", and does it really report 53 SNPs?
- **Search terms:** WebSearch "Giannelis quantitative ability GWAS genome-wide significant SNPs mathematical ability genomic SEM".
- **Sources inspected:**
  - Giannelis, Willoughby, Edwards, McGue & Lee, *Mol Psychiatry* 2025;30:5701–5709, doi:10.1038/s41380-025-03237-0, PMID 40975749, PMC12602337 (CC BY 4.0).
  - Also returned: news-medical coverage. **Rejected** as secondary.
- **Accepted:** the primary paper.
- **Data acquired:** EuropePMC full-text XML.
- **Conclusion:** The abstract reports 53 SNPs for a latent trait "orthogonal by design with general intelligence".
- **Uncertainty:** none about identity.
- **Next:** get the supplement.

### S2. 21:05–21:08 — Supplement and methods
- **Question:** What are the exact per-SNP statistics, the model, the sample and the independence criteria?
- **Sources:**
  - EuropePMC `PMC12602337/supplementaryFiles`, a ZIP containing MOESM1 (Supplementary Information PDF) and MOESM2 (Tables S1–S12 xlsx).
- **Accepted:** Table S2 (53 rows, verbatim) and the SI methods.
- **Key facts extracted:**
  - Pipeline: PLINK clumping (P<5e-8 primary, 1e-4 secondary, r²<0.1, 1-Mb window, 1000G EUR) gave 78 clumps from 5,203 GWS variants. GCTA-COJO (LD reference = MCTFR parents) then gave 53 SNPs.
  - QSNP threshold was 5e-8. Only rs13107325 was significant.
  - Model: DWLS, unit-loading identification, all residual variances fixed to 0, factors orthogonal.
  - SNP filters: the SI says the 1000G reference was restricted to MAF>0.005. The OSF code calls `sumstats()` with maf.filter=0.01 and info.filter=0.6. About 5.93M SNPs remain.
  - Effective N = 343,237.
- **Conclusion:**
  - The count is verified as 53.
  - The phenotype is a self-report and course-taking proxy, not objective ability.
  - "Orthogonal" holds only by model constraint.

### S3. 21:08 — Are summary statistics public?
- **Question:** Can we do genome-wide look-ups?
- **Sources:**
  - Paper Data-availability section.
  - OSF API: user search found A. Giannelis (5y4kx) and J.J. Lee (pr759). Project `txyqr` has the paper's title.
  - OSF file listing: `Supplementary Material/math_GWAS_supplementary_tables.xlsx`; `Code/{MATH_Syntax.txt, README_for_OSF.txt, bio_annot.R, Manhattan_custom.R, RG_plots.R}`.
  - GWAS Catalog REST `studies/search/findByPublicationIdPubmedId?pubmedId=40975749` and `/api/v2/studies?pubmed_id=40975749` both returned **0 studies**.
- **Conclusion:** **Not public.**
  - The README says the 23andMe inputs must be obtained from 23andMe.
  - The OSF xlsx is byte-identical to MOESM2 (sha256 ade0be69…).
- **Data acquired:** OSF README and MATH_Syntax (hashes in PROVENANCE.json).
- **Blocker:** access to the 23andMe summary statistics requires an application to 23andMe. That is out of scope; no account or terms were used.

### S4. 21:09 — The authors' code contradicts the text on the CP input
- **Finding:** `MATH_Syntax.txt` runs LDSC and `userGWAS` with `CP1_single_gwide_sumstats.txt`, labelled `CP_UKB` with a comment "N … 222914". It also contains `munge("GWAS_CP_all.txt", …, 257828)`, but that file is not used in the LDSC/GWAS `traits` or `files` lists.
- **Contrast:** The SI says the SSGAC CP (N=257,841, UKB plus COGENT) was used for "most analyses".
- **Status:** Unresolved. The OSF code may be a later rerun or a different version.
- **Effect on us:** None on the UKB-overlap conclusion. Either way, the g anchor is UKB-dominated.

### S5. 21:11 — Coordinate verification (Ensembl)
- POST of the 53 rsIDs to `rest.ensembl.org/variation/homo_sapiens` and `grch37.rest.ensembl.org/...` (raw JSON saved).
- **Result:** Table S2 chr:pos equals the Ensembl GRCh37 mapping for **53 of 53** SNPs. All 53 have a primary GRCh38 mapping, and there are no merged or retired rsIDs.
- **Conclusion:** the build is GRCh37. The `chr38`/`pos38`/`allele_string` columns come from GRCh38.

### S6. 21:12 — Overlap with the 159 general-cognition loci; Davies look-up; null model
- **Locus definition:** `research/sprint4/frozen_hypotheses.json` holds the 159 frozen loci, with chr, start and end in GRCh37, and `lead_pos_grch37`.
  - Each locus spans the Bonferroni MAGMA genes of one |r|≥0.2 LD block (`data/gene_tournament/ld_loci.parquet`) ±10 kb. `locus_id` = "L" + block id.
  - `ld_loci.parquet` itself holds gene→block assignments only, no coordinates. That is why the frozen coordinates were used.
  - `reports/sprint4/genc_independent_loci.csv` has no positions for its `lead_snp`, so lead positions were taken from the frozen JSON.
- **Davies 2018 open file:** read only; N=282,014 public subset, GRCh37, header `Chromosome Position Markername Effect_allele Other_allele P-value Zscore`, 12,871,897 rows.
  - All 53 SNPs were found by rsID and aligned by allele label directly. There were no strand flips and no palindromic SNPs.
- **Null model:**
  - A: SNP-weighted genome fraction.
  - B: 10,000 sets of 53 Davies SNPs, matched on MAF bin (edges 0.01/0.05/0.1/0.2/0.3/0.4/0.5; MAF from UKB FI1 EAF) × gene-density quintile (NCBI37.3 genes overlapping ±500 kb). Seed 20260923.
  - LD-score matching was not done because no LD-score reference exists in the repo.
- **Results:**

  | Category | Observed | Null A expected (P) | Null B expected (P) |
  |---|---|---|---|
  | Inside an interval | 6 | 1.28 (0.0017) | 1.36 (0.0026) |
  | Within 500 kb of a lead | 10 | 2.34 (9.6e-5) | 2.61 (2e-4) |
  | Either | 11 | 2.81 (8.8e-5) | 3.10 (3e-4); fold 3.55 |

- **Sign concordance:** Davies z for the math-increasing allele is positive at 17 of 53 SNPs (P=0.013).
  - Among the 13 SNPs with Davies P<0.05/53, only 2 are positive.
  - Spearman ρ(|Gq z|, aligned Davies z) = −0.11 (P=0.44).
- **Conclusion:** The enrichment is real but predominantly sign-inverted. This is consistent with residualisation (Gq ≈ SRM − λ·g, with g from UKB CP, which overlaps Davies), not with shared biology.
- **Remaining uncertainty:**
  - Without the SRM, HM and CP per-SNP effects, how much of the inversion is true biology (a smaller self-report effect than g predicts) versus shared UKB estimation error cannot be split.
  - The null does not match on LD score.

### S7. 21:12 — Objective arithmetic look-up (already in repo)
- **Discovery:** `data/interim/sumstats/` already contains GCST90042726 (FI1 numeric addition) and GCST90042729 (FI4 positional arithmetic).
  - GWAS Catalog REST identifies them as Jiang et al. 2021 *Nat Genet* fastGWA-GLMM (PMID 34737426).
  - They are binary items. The GWAS Catalog reports 112,934 cases / 2,938 controls for FI1 (trait label "numeric addition test - 14", UKB field 20165) and 102,666 / 12,637 for FI4 ("positional arithmetic - 5", field 20171). Cases are assumed to be people giving the correct answer (14 or 5). The sign alignment depends on this assumption, which was not verified against UKB coding.
- **Result:** 52 of 53 SNPs present (rs10863150 is missing).
  - FI1: 27 of 52 positive, mean z +0.16.
  - FI4: 24 of 52 positive, mean z −0.09.
- **Conclusion:** no support from objective UKB arithmetic items.
- **Caveats:** near-ceiling binary items, g-loaded, same UKB sample as the g anchor.

### S8. 21:13 — Classification rule and gene labels
- The rule is fixed before looking at the gene names:
  1. QSNP P<5e-8 → MATH_PROXY_ONLY.
  2. Davies P<0.05/53 → GENERAL_G_SHARED.
  3. Davies P≥0.05, no locus and no lead within 500 kb → MATH_SPECIFIC_ORTHOGONAL.
  4. Otherwise → MATH_PROXY_ONLY.
- **Result:** 12 / 18 / 23.
- **Nearest gene:** from `NCBI37.3.gene.loc`, all rows, 0 if the SNP lies inside the gene. It is labelled `nearest_gene_label_only`. The paper's PoPS gene is carried as `pops_gene_paper_label_only`.
- **Circularity check:** 15 of the 35 loci in `reports/sprint4/locus_finemapping.parquet` include Open Targets credible sets from 23andMe self-reported math ability or highest math class (Lee 2018). Those are the same GWAS that feed Gq.

### S9. 21:14–21:17 — Literature re-audit (Task B)
- **Searches:**
  - EuropePMC REST title queries (genome-wide/GWAS/polygenic × math/mathematics/arithmetic/numeracy/numerical/quantitative ability; 21 hits).
  - Author queries: Amalric+Dehaene, Koenis, Procopio.
  - WebSearch: MoBa numeracy GWAS; objective math GWAS 2025; SAT-math genetics; genotyped professional mathematicians.
  - GWAS Catalog study API for the FI items.
  - PMC BioC full text for Lee 2018 (math GWS counts) and Procopio 2025.
  - WebFetch of PMC4983814 (Amalric 2016 sample size).
- **Accepted (primary, abstract or full text read):**
  - Lee 2018: 225 CP, 618 Math Ability and 365 Highest Math GWS SNPs.
  - Procopio 2025 Mol Psychiatry.
  - Procopio 2025 Behav Genet.
  - Donati 2021.
  - Davis 2014.
  - Docherty 2010.
  - Chen 2017.
  - Zhang 2023.
  - Baron-Cohen 2014.
  - Amalric & Dehaene 2016: 15 mathematicians and 15 humanities specialists, no genetic data.
  - Amalric & Dehaene 2019.
  - Koenis 2015 and 2018.
  - Cheesman 2025 PNAS (MoBa).
  - Cheesman 2025 Nat Genet (educational fields).
  - Jiang 2021.
- **Accepted with lower confidence:** Harden 2020 npj Sci Learn. Only the search snippet was read, not the abstract.
- **Rejected or not used:**
  - News coverage.
  - Wikipedia.
  - Deep-phenotyping PGS preprint (bioRxiv 2020.06.03.131318). Not math-specific and not inspected.
  - Lin & Plomin 2025 preprint. It concerns g.
  - Kovas 2007 TEDS twin monograph. Not retrieved in this session, so it is not cited.
- **Conclusions:**
  - No study genotyped professional mathematicians. The mathematician fMRI work is IMAGING_ONLY.
  - Math-specific genetic variance exists at the heritability level:
    - TEDS: twin h² about 40% and SNP h² about 26% for g-corrected specific abilities (average over math, reading and language).
    - ALSPAC: h²SNP persists after removing IQ.
  - No large, g-corrected, objective-math GWAS with loci was found for 2024–2026.
- **Remaining uncertainty:** these are negative search results, not proof of absence. Places a GWAS could exist and be missed:
  - MoBa national numeracy tests (N≈31k genotyped trios exist).
  - ABCD.
  - Estonian or Finnish registries.
- **Next search:**
  - Check whether a MoBa/Norwegian numeracy GWAS or summary statistics have been released.
  - Check whether Procopio/TEDS released g-corrected math GWAS or PGS weights.
  - Ask whether SSGAC/23andMe would release SRM/HM per-SNP effects at the 53 SNPs. That would let us split true inversion from residualisation.

### Files written
- `data/raw/sprint5/math/`: MOESM1 PDF, MOESM2 xlsx, full-text XML, OSF README and syntax, Ensembl JSON (GRCh37 and GRCh38), and `PROVENANCE.json` (URL, UTC time, bytes and sha256 for each file). The supplement ZIP and the duplicate OSF xlsx are hashed but not retained.
- `data/sprint5/math53_variants.csv`: 53 rows.
- `reports/sprint5/math53_gene_mapping.csv`: 53 rows.
- `research/sprint5/math_audit.md` and this log.
- Nothing was written to `data/interim/sprint5/math/`, because no public summary statistics exist.
