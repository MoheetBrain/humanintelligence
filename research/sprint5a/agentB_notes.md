# Sprint 5A — Agent B notes (single-cell eQTL colocalisation; multi-trait colocalisation)

Branch `sprint-5a/open-data-exhaustion`. No commits were made. No accounts, sign-ins, terms or tokens were used.
The machine rebooted during the run, at about 2026-09-24T09:58Z. Every download was then re-verified (details below).
Times are UTC.

## Search log

### S1 — 08:38Z. Where are the Bryois 2022 summary statistics?
- **Terms.** `zenodo.org/api/records/5543734`. It redirects (302) to record 7276971.
- **Accepted.** Zenodo record 10.5281/zenodo.7276971 (concept DOI 10.5281/zenodo.5543734), licence CC-BY-4.0, no login.
  - Layout: `<CellType>.<chr>.gz` for 8 cell types plus `pb` (tissue-like pseudo-bulk, added February 2023) × 22 chromosomes, and `snp_pos.txt(.gz)`.
  - Columns (no header): Gene_id (`SYMBOL_ENSG`), SNP_id (rsID), distance to TSS, nominal p, beta.
  - `snp_pos.txt` columns: SNP, SNP_id_hg38, SNP_id_hg19, effect_allele, other_allele, MAF.
  - The beta is per copy of `effect_allele`. Both builds are present, so the GRCh37 match to Davies is direct (rsID join, hg19 window).
  - No SE is distributed. I recovered it as |beta| / qnorm(p/2, upper). This is exact for the Wald/linear-model test fastQTL uses, but the rounding of p propagates into SE.
- **Rejected.** Nature full text (paywall redirect to idp.nature.com). No PMC copy exists (Europe PMC shows PMID 35915177 with no PMCID).

### S2 — 08:40Z. Bryois cohorts, build and methods
- **Source.** medRxiv preprint 10.1101/2021.10.09.21264604 (full-text PDF, read locally).
- **Datasets.** Five datasets:
  - Roche_MS: 83 individuals (29 controls, 54 MS), white matter and grey matter.
  - Roche_AD: 40 individuals, temporal cortex and deep white matter.
  - Three published ROSMAP datasets:
    - Mathys 2019 (ref 14);
    - Zhou 2020 (ref 15);
    - Cain / "Columbia_AD" (ref 16).
    - These are prefrontal cortex. Their genotypes come from ROSMAP whole-genome sequencing.
- **Individuals after QC.** 196 in the preprint, 192 in the published paper.
- **Genotypes.** Imputed to HRC r1.1, lifted to GRCh38, MAF > 5%.
- **eQTL model.** fastQTL, 1 Mb cis window. Covariates: 3 genotype PCs, disease, study, and 90 expression PCs.
- **Uncertainty.** The per-dataset donor counts are in Table S1, which I could not extract, so the exact ROSMAP share of the 192 is not stated here.
- **Overlap.** The ROSMAP donors (Mathys/Zhou/Cain) overlap the ROSMAP DLPFC bulk eQTL (eQTL Catalogue QTD000434) used in Sprint 4. The Roche donors overlap none of our bulk sets. Overlap with brainSCOPE exists only through ROSMAP, if brainSCOPE includes ROSMAP donors, which I did not verify.

### S3 — 08:45Z. Other open single-nucleus brain QTL full summary statistics?
- **Terms.** "SingleBrain meta-analysis single-nucleus eQTL", "Fujita 2024 data availability". Sources: PMC11908325 and web search.
- **Accepted: SingleBrain** (Raj lab; medRxiv 2025.03.06.25323424). Zenodo 10.5281/zenodo.14908182, CC-BY-4.0, open.
  - It is an mmQTL meta-analysis of four cohorts:
    - Fujita 2024 (ROSMAP, 424 donors);
    - Mathys 2023 (ROSMAP);
    - Gabitto (SEA-AD, MTG);
    - Bryois (Roche cohort).
  - 983 samples from 757 unique donors. 7 major cell types plus subtypes.
  - Build hg38 with rsIDs. Columns include fixed_beta, fixed_sd, fixed_z, Random_Z and P. The beta is per copy of `Allele` (= alt). No MAF column.
  - Files are BGZF, about 4.5 GB per major cell type.
- **Access limit.** Zenodo served about 0.5 MB/s per connection (about 1.6 MB/s aggregate) and allows 133 API requests/min. A full 32 GB download was impractical, so I fetched byte ranges from the BGZF files (see D2).
- **Rejected: Fujita 2024 cell-type eQTL summary statistics** (Synapse syn52335732). Synapse download needs an account and a data-use certificate. Recorded blocker: NOT_ACCESSED (account/DUC required). Fujita data still enters through SingleBrain.
  - The Menon shiny app (vmenon.shinyapps.io) is interactive only; not used.
- **Not pursued.**
  - Kosoy/MiGA microglia: MiGA is bulk sorted microglia. SingleBrain's MiGA3 file covers it, but it is not single-nucleus, so I excluded it to keep the cell-type layer clean.
  - Brain sQTL: out of scope for gene-level expression direction.
- **Checked.** eQTL Catalogue r7 lists no single-cell brain datasets (Sprint 4 `data/sprint4/eqtl_catalogue_brain_datasets.csv`).

### S4 — 08:52Z. HyPrColoc install
- **Source.** GitHub jrs95/hyprcoloc master @0348bbd, tarball sha256 recorded in `data/raw/sprint5a/hyprcoloc/PROVENANCE.json`.
- **Problem.** It failed to compile against Eigen 3.4 (RcppEigen 0.3.4.0.2).
- **Fix.** I added (int) casts on the RHO() indices (`pipelines/sprint5a/hyprcoloc_eigen_cast.patch`). No numerical logic changed.
- **Check.** The package example reproduces the documented 3 clusters.
- **Environment side-effect.** An unpinned `mamba install` upgraded R to 4.5.3. I reverted it to R 4.4.3 and verified coloc 5.2.3 and susieR 0.14.2 afterwards.

## Data acquired

- **D1. Bryois 2022.** 145 files: snp_pos plus 9 sets (8 cell types and pb) × 16 chromosomes carrying Gate-C loci.
  - 3.74 GB, downloaded 08:48–09:18Z.
  - Every file's md5 matches Zenodo. sha256 and bytes are recorded in `data/raw/sprint5a/bryois2022/PROVENANCE.json`.
  - After the reboot, all 145 files were re-hashed: 145/145 match sha256 and size.
  - One transient md5 failure (Microglia.14) was re-downloaded and verified.
- **D2. SingleBrain.** 252 locus windows (36 loci × 7 cell types). Each window is GRCh38 lead ± 500 kb, taken from the Sprint-4 eQTL Catalogue provenance.
  - Fetched by HTTP byte ranges on the BGZF file: 2,326 requests, 1.12 GB, 08:50–09:54Z.
  - Per range, the provenance records the byte offsets, the sha256 of the fetched bytes, and the Zenodo whole-file md5 as identity.
  - A whole-file sha256 was **not** computed, because the whole file was never downloaded.
  - Every window reached a record past the window end, so each window is complete. After the reboot, the row counts of all 252 extracts matched the provenance.
- **D3. Big files.** All under `data/interim/sprint5a/{bryois,singlebrain,sc_long,sc_coloc,hyprcoloc}` (gitignored).

## Method decisions (why)

- **Frozen Sprint-4 conventions reused.**
  - Code reused as-is: `harmonise()`, `gwas_beta()`, `R_COLOC` and `R_BFBF`, imported from `pipelines/sprint4/gate_c_coloc.py`.
  - Priors 1e-4 / 1e-4 / 5e-6. Strong means PP.H4 ≥ 0.8.
  - Palindromic SNPs with MAF > 0.40 dropped.
  - No threshold was relaxed.
- **Gene universe.** Every gene in the QTL files whose Ensembl GRCh38 TSS lies in lead ± 500 kb, plus all Gate-C query genes.
- **QTL N.** Bryois 192. SingleBrain 757 (unique donors). N is used only for the SuSiE fits, because coloc.abf gets beta and var(beta) directly.
- **SingleBrain MAF.** SingleBrain has no MAF, so I used 1000G EUR MAF. This affects only the abf prior on the effect-size variance.
- **coloc.susie.**
  - QTL side: susie_rss on the sc-eQTL z, using the Sprint-4 1000G EUR LD (the gate_c_finemap code path), L = 10.
  - Run only when the pair's minimum eQTL p is below 1e-4.
  - Out-of-sample LD with small N is a limitation, and rsID matching limits the SNP set to 1000G EUR.

## Conclusions and uncertainty
(Results section written after the runs; see bottom.)

### Recovery after the reboot (about 09:58Z; resumed at 11:01Z)
- **Checks run.** `/private/tmp/.../scratchpad/verify.py` checked three things:
  - Bryois: 145/145 files match the recorded sha256 and size.
  - SingleBrain: all 252 window extracts are present, every window reached its end, and every row count matches the provenance.
  - Extraction: all 324 Bryois per-locus extracts in `sc_long` are readable.
- **Nothing was truncated**, so nothing was re-fetched.
- **One LD cache directory** (`sc_coloc/ld/L84282`) was incomplete. I deleted and rebuilt it.
- **Code change.** `sc_eqtl_coloc.py` now filters Davies to the locus window before `harmonise()` (a speed fix; the result is identical). I then re-ran it with ≤ 3 threads.

## Results

### A. Single-cell eQTL colocalisation
Outputs: `reports/sprint5a/sc_eqtl_coloc.parquet` and `reports/sprint5a/sc_eqtl_coloc_summary.csv`.

- **Tests.**
  - 4,700 locus × gene × cell-type pairs were harmonised (36 loci, 436 genes, 16 source × cell-type sets).
  - 4,700 coloc.abf and 919 coloc.susie comparisons, for 5,619 rows in total.
  - 141 rows are strong (PP.H4 ≥ 0.8), covering 42 locus × gene combinations; 256 rows are ≥ 0.5.
- **16p11.2 (L51327, L1).**
  - SH2B1 is strong in 12 rows:
    - Bryois: excitatory neurons, inhibitory neurons, pseudo-bulk.
    - SingleBrain: excitatory neurons, inhibitory neurons, astrocytes.
    - Best PP.H4 0.886. The cognition-increasing allele gives HIGHER SH2B1 in every strong row.
    - Sprint-4 bulk had no strong SH2B1 coloc. The ROSMAP bulk beta at rs62037363 has the same sign as the single-cell data.
  - TUFM is strong in SingleBrain only (excitatory neurons, inhibitory neurons, OPC; best 0.888).
    - Direction is HIGHER, which **disagrees** with Sprint-4 bulk (GTEx hippocampus and ROSMAP: LOWER).
    - I checked this against raw alleles at rs62037363 (Davies effect allele T, z = +8.8):
      - SingleBrain C-allele beta is −0.13, so T gives higher TUFM.
      - ROSMAP bulk C-allele beta is +0.14, so T gives lower TUFM.
    - This is a genuine discordance between the nuclear and bulk estimates, even though the donors overlap (ROSMAP). TUFM direction stays unresolved.
  - EIF3C best is 0.75 (moderate). ATXN2L best is 0.37.
  - Other strong genes: NFATC2IP (−), LAT (−), NPIPB9 (+, Bryois oligodendrocytes), AC138894.1 (−).
  - **Uncertainty.** 16p11.2 has extended LD. Several genes colocalise with the same lead, so coloc cannot pick among them.
- **14q12 (L64067).** AKAP6 best 0.06; NPAS3 best 0.03. PP.H3 reaches 1.0 for some pairs (distinct causal variants). No single-cell support.
- **3p21.1 (L91869 / L51460; overlapping windows, not independent).**
  - GNL3 is strong in Bryois pseudo-bulk (0.958, coloc.susie) and Bryois inhibitory neurons (0.87). Direction LOWER.
  - NT5DC2 best 0.64 (SingleBrain OPC, moderate, LOWER). STAB1 best 0.03.
- **DCC (L1630).** Best 0.75 (SingleBrain excitatory neurons, coloc.susie). Moderate only; its direction does not qualify as a strong-row call.
- **EXOC4 (L60412).** Best 0.60 (moderate).
- **SLC39A8 (L64116).** Best 0.04; PP.H3 = 1.0 for some pairs. This fits the missense lead rs13107325 not acting through expression.
- **KIFC2 (L65265).** 0.979 in SingleBrain excitatory neurons. Direction LOWER, which agrees with the bulk majority.
  - The same locus also shows ZFTRAF1 (0.99; 12 strong rows across 6 cell-type sets; LOWER; agrees with bulk) and PPP1R16A (0.99; HIGHER).
  - So several genes share one lead (rs750472), and the gene is not identified.
- **DNPH1 (L55168).** SingleBrain excitatory neurons 0.927 and inhibitory neurons 0.855. Direction LOWER, which agrees with the bulk majority.
- **Other strong colocs.**
  - WBP2NL (L1565): 12 rows, LOWER, agrees with bulk DIRECTION_RESOLVED.
  - DHRS11 (L79922): LOWER; agrees.
  - MYO19 (L79922): LOWER.
  - NEGR1 (L257194): SingleBrain OPC and oligodendrocytes, HIGHER; agrees.
  - RHEBL1 (L7009): SingleBrain excitatory neurons 0.864, HIGHER; agrees with bulk DIRECTION_RESOLVED.
  - SLC4A10 (L1803): SingleBrain OPC 0.96, HIGHER.
  - NR1D2 (3p24): OPC 0.97, HIGHER. L7068, L9975 and L7324 share this window.
  - FAM131A and CLCN2 (L8646): CLCN2 is MIXED across cell types.
  - KMT2E and SRPK2 (L6733); GOSR1 (L84282).
- **Single-cell vs bulk direction.**
  - Where both are comparable: AGREE for ZFTRAF1, WBP2NL, MYO19, DHRS11, NEGR1, CLCN2, DNPH1, NAGA, GOSR1, NPIPB9, KIFC2, RHEBL1 and CYP2D6.
  - DISAGREE for TUFM, RECQL4 and GGNBP2.
- **Independence.** SingleBrain includes the Bryois (Roche) donors and ROSMAP donors, and Bryois includes ROSMAP. Per the Sprint-5A protocol, single-cell coloc collapses into the bulk QTL class; it adds cell-type and direction information, not a new independent vote.

### B. Multi-trait colocalisation (HyPrColoc)
Output: `reports/sprint5a/multitrait_coloc.csv`.

- **Scope.** 22 loci (16 L1/L2 plus 6 named; L7009 is in both lists), with two runs per locus:
  - ALL: 5 GWAS traits plus up to 3 eQTL traits;
  - GWAS_ONLY.
- **GWAS_ONLY runs.** No cluster at any locus.
  - The secondary GWAS (TMA, PIQ, XIQ, FI4) have max |z| of only about 2–4.3 in these windows.
  - HyPrColoc cannot show sharing at that power. This is **NOT_TESTABLE at power**, not evidence against sharing.
- **ALL runs: clusters of cognition + a brain-eQTL gene** (posterior; candidate SNP):
  - DCC: cognition + DCC in GTEx cerebellum (0.93; rs6508220).
  - NEGR1: cognition + NEGR1 in ROSMAP (0.83; rs1620977).
  - L65265: cognition + ZFTRAF1, RECQL4 and KIFC2 (0.80; rs750472).
  - WBP2NL/NAGA (L1565): 0.71; rs133326.
  - L51460: cognition + NT5DC2 in CommonMind (0.63; rs7636227).
  - RHEBL1 + LMBR1L (L7009): 0.57.
  - 16p11.2: cognition + TUFM, EIF3C and NPIPB9 (0.56; rs62037363; SNP posterior only 0.04).
  - DNPH1 + PTK7 (0.52; rs7832).
  - ZSCAN9 (0.51).
  - SUOX, RPS26 and ERBB3 (L319; 0.51; rs11171739).
  - 3p24: THRB (0.44).
  - L91869: NT5DC2 + GLYCTK (0.26).
  - DHRS11 (0.28): cluster also includes XIQ_zabaneh.
- **No cluster:** L64067 (AKAP6/NPAS3), L1803, L3123, L2131, L60412 (EXOC4), L3760, L64116 (SLC39A8), L100132074.
- **Caveats.**
  - HyPrColoc assumes the studies are independent. Davies ⊃ UKB/HRS/BATS, so FI4, the Zabaneh controls and GenLang/BATS overlap Davies. Clusters involving only those traits would be overlap-confounded; none occurred except XIQ at DHRS11.
  - The eQTL traits were chosen from the Sprint-4 pairwise colocs, so they confirm existing signals rather than discover new ones. The multi-gene clusters do not identify a single gene.

## Blockers
- **Fujita 2024 cell-type summary statistics** (Synapse syn52335732): account and data-use certificate required. Not accessed.
- **Bryois Table S1** (exact per-cohort donor counts): not extracted.
- **SingleBrain** has no whole-file sha256 (range access; md5 identity recorded), no MAF (1000G EUR MAF used), and an effective N of 757 assumed for SuSiE.
