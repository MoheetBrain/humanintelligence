# Sprint 5A — Agent C notes: functional fine-mapping (PolyFun + SuSiE) and PoPS

Branch `sprint-5a/open-data-exhaustion`. Nothing committed by this agent. All large files are under
`data/interim/sprint5a/` (gitignored). Every download has URL, UTC time, bytes and sha256 in
`data/raw/sprint5a/<resource>/PROVENANCE.json`.

Standing caveats (apply to everything below):

* PolyFun priors are functional-enrichment priors estimated in UK Biobank from 15 traits (none is
  cognition). A PIP that rises because of the prior is a statement about annotation, not about cognition.
  Nothing here is causal evidence and nothing here is used to relax any Sprint-4/5 threshold.
* PoPS is genome-wide, feature-based gene prioritisation. It is **not** local causal evidence and must
  **not** be counted as a variant-to-gene vote in the Sprint-5 evidence matrix.
* The Davies 2018 GWAS (N=282,014) is ~79% UK Biobank. The PolyFun priors were estimated in UKB, and the
  UKB LD panel is from UKB. That overlap is a strength for LD matching and a weakness for independence.

---

## Step 1 — 2026-09-24T08:39Z — Where are PolyFun's precomputed priors, and may we use them?

**Question.** What file is "approach 1", where is it hosted, under what licence, and what exactly does it contain?

**Sources accepted.**
* `omerwe/polyfun` wiki page "1. Computing prior causal probabilities with PolyFun" (cloned wiki repo
  `https://github.com/omerwe/polyfun.wiki.git`; the rendered GitHub wiki page failed to load through the
  web fetcher, so the markdown source was read directly). Approach 1 = "precomputed prior causal
  probabilities of 19 million imputed UK Biobank SNPs with MAF>0.1%, based on a meta-analysis of 15 UK
  Biobank traits", extracted with `extract_snpvar.py` (CHR, BP hg19, A1, A2 keys; output `SNPVAR`, per-SNP
  heritability proportional to the prior causal probability).
* `extract_snpvar.py` source (commit 8b17b4e): the files are `snpvar_meta.chr1_7.parquet` and
  `snpvar_meta.chr8_22.parquet`, **stored in the code repository itself**; the script truncates the ratio
  max/min prior at q=100 (genome-wide) and refuses to run if any requested SNP lacks a prior unless
  `--allow-missing`, which then drops those SNPs.
* Licence: MIT (repository LICENSE; GitHub API `license.key = mit`).

**Rejected.** None needed. Approaches 2/3 (re-estimating priors from our sumstats) were not used: approach 3
needs large individual-level data, and approach 2 on Davies would re-use a UKB-dominated GWAS to make its own
prior (circular for this purpose).

**Data acquired.** `git clone https://github.com/omerwe/polyfun.git` at commit
`8b17b4ec87fde11f8d216c049c08d1420cd25de6` into `data/interim/sprint5a/tools/polyfun/`.
`snpvar_meta.chr1_7.parquet` 74,142,426 B sha256 `cc19d9ca…fe7f1`; `snpvar_meta.chr8_22.parquet`
75,417,733 B sha256 `89846a37…e59c`. Full hashes in `data/raw/sprint5a/polyfun/PROVENANCE.json`.

**Conclusion.** Approach 1 is usable, public, MIT-licensed, hg19 like Davies. Only 13 distinct prior bins exist
(most SNPs have bin 0 before truncation), so after the q=100 truncation the prior is effectively a 13-level
functional weighting with max/min = 100 in every locus.

**Uncertainty.** The per-SNP heritabilities describe a "typical" polygenic trait. The PolyFun authors
recommend approach 1 only when the trait has typical enrichments (coding/conserved strongly enriched). We have
no cognition-specific check of that assumption.

## Step 2 — 2026-09-24T08:45Z — Environments

* `hi-polyfun` (conda-forge): python 3.11, pandas 2.2.3 (first built with pandas 3.0.6, which broke
  PolyFun's `finemapper.py` — read-only array under copy-on-write; downgraded), numpy 2.4.6, scipy 1.17.1,
  rpy2 3.5.11 (3.6 removed `numpy2ri.activate`, which finemapper uses), R with susieR 0.14.2. Python 3.8/3.9
  (PolyFun's yml) was not solvable on osx-arm64 with pandas-plink.
* susieR 0.11.92 from the CRAN archive
  (`https://cran.r-project.org/src/contrib/Archive/susieR/susieR_0.11.92.tar.gz`, 2,208,011 B, sha256
  `6bac024f…09cf2`, fetched 08:56:50Z) installed into a private library
  `data/interim/sprint5a/tools/Rlib_susie0.11.92`, used only for PolyFun's `finemapper.py`, which calls the
  pre-0.12 `susie_suff_stat(bhat=, shat=, R=)` API. Our own SuSiE runs use susieR 0.14.2, exactly as Sprint 4.
* `hi-pops`: python 3.9, numpy 1.21.6, pandas 1.3.5, scipy 1.7.3, scikit-learn 0.24.2 (scikit-learn pinned to
  PoPS' requirements.txt; the numpy/pandas/scipy pins of requirements.txt have no osx-arm64 builds).
* Nothing was pip-installed into the repo `.venv`.

## Step 3 — 2026-09-24T08:47–09:00Z — PolyFun + SuSiE-RSS at the 36 Gate-C loci (1000G LD)

**Question.** With the Sprint-4 LD, SNP set and SuSiE settings held fixed, what changes when the PolyFun
priors are used as `prior_weights`?

**Method.** `pipelines/sprint5a/polyfun_susie.py` + `polyfun_susie.R`. For each locus the Sprint-4 function
`locus_inputs` rebuilds the SNP set and 1000G-EUR LD; the script refuses to proceed unless the SNP list and z
equal `data/interim/sprint4/susie/<locus>/snps.tsv`. The R script fits plain and PolyFun SuSiE in one process
(`susie_rss`, L=10, coverage 0.95, min_abs_corr 0.5, estimate_residual_variance=FALSE, max_iter 1000; the only
change is `prior_weights`). SNPs absent from the PolyFun set (0–6 per locus) get the genome-wide floor prior
(max/100) instead of being dropped, so the SNP sets stay identical. Coding/regulatory annotation: Ensembl
GRCh37 VEP REST (`https://grch37.rest.ensembl.org/vep/human/id`, public).

**Reproduction check.** Plain fits reproduce Sprint 4 exactly: max |PIP difference| = 0.0 at all 36 loci, and
the 1,491 plain credible-set rows equal Sprint 4's 1,491. estimate_s_rss 0.014–0.101 (no locus > 0.2; AKAP6
highest at 0.101). NEGR1 (L257194) does not converge in 1000 iterations in either fit — as in Sprint 4.

(results: see Step 6)

## Step 4 — 2026-09-24T08:41–08:50Z — PoPS inputs

**Question.** Where are the published PoPS feature matrices, how large, under what licence; can our MAGMA
results be used?

**Sources accepted.** `FinucaneLab/pops` README at commit `76eb86cba10254490003c8f4dc7ff5ce492d3667` (PoPS
v0.2; GPL-3.0): "To download the full set of feature files used to generate the results in the manuscript"
→ Dropbox shared link to `PoPS.features.txt.gz`. Paper: Weeks et al. 2023 Nat Genet 55:1267.

**Data acquired.** `PoPS.features.txt.gz` 7,552,217,751 B (= HTTP Content-Length), sha256
`507b4231cad3f637ba6f99d0cffeb4c8a856e7a920fec416a7a63106d603e1c2`, 57,742 features × 18,383 genes
(download 08:41:51Z–≈08:50Z; public link, no sign-in). No separate licence file accompanies the matrix; the
code is GPL-3.0; used locally, not redistributed.

**MAGMA.** `data/interim/magma_replication/davies2018_10kb.genes.raw` already existed (MAGMA v1.10, 10 kb,
1000G EUR, Davies N=282,014). Checked against the committed `davies2018_10kb.genes.out`: same 18,418 genes in
the same order, |ΔZ| ≤ 5e-5 (rounding). So MAGMA was **not** regenerated. PoPS keys on Ensembl ids; our
MAGMA is Entrez-keyed. `pipelines/sprint5a/pops_prep.py magma` re-keys via the committed
`gene_id_map.tsv` (unique mappings only): 18,418 → 18,154 mapped → 17,566 in PoPS' gene annotation → 17,554
after dropping 6 Ensembl ids hit by two Entrez genes. The `.genes.raw` gene–gene correlation lists were
rebuilt for the retained subset; PoPS' own parser recovers exactly the MAGMA sub-matrix (max |Δ| = 0.0).

**Feature munging.** `pops_prep.py features` streams the gz into PoPS' chunked NumPy format (12 chunks,
float64; boolean columns → 1/0 as pandas `.astype(float64)` does in `munge_feature_directory.py`). Check: all
508 features of PoPS' bundled example matrix are present and identical (max |Δ| = 1.4e-14). The bundled
example (schizophrenia) reproduces PoPS' shipped output to 4.8e-15 in the `hi-pops` env.

## Step 5 — UKB LD panel sensitivity (PolyFun's published UKB LD)

**Question.** Does the LD panel (1000G EUR, n=503, out-of-sample) drive the PolyFun result, and does
PolyFun's own `finemapper.py` agree?

**Source.** `s3://broad-alkesgroup-ukbb-ld/UKBB_LD/` (AWS Open Data; documented in the PolyFun wiki
"3. Functionally-informed fine-mapping with finemapper"): N=337K unrelated British-ancestry UKB, 3 Mb regions,
`.npz` (sparse LD) + `.gz` (SNP list). One region per locus with the lead in the middle Mb (PolyFun convention).
Each `.npz` is 0.69–1.45 GB. Single S3 connections ran at ~0.2 MB/s from here, so `aria2c` (16 range
connections × 3 files) was used. Provenance: `data/raw/sprint5a/ukb_ld/PROVENANCE.json`.
16 of 17 regions downloaded (16.3 GB); `chr6_27000001_30000001.npz` (ZSCAN31, L64288) returns HTTP 404 — PolyFun
does not publish LD overlapping the extended MHC (its own `LONG_RANGE_LD_REGIONS` lists chr6:25.5–33.5 Mb);
neighbouring start positions are also 404. ZSCAN31 therefore has no UKB-LD sensitivity (blocker, recorded).

Two UKB-LD analyses (`pipelines/sprint5a/ukb_ld_sensitivity.py`):
* `run` — the 1000G SNP set (minus 0–5 SNPs absent from UKB), same z, same `polyfun_susie.R` (frozen settings),
  plain and PolyFun priors; only the LD panel changes.
* `finemapper` — PolyFun's own `finemapper.py --method susie --max-num-causal 10` on all Davies SNVs in lead ±500 kb
  present in the UKB LD file (2,578–5,087 SNPs), functional (`SNPVAR` from `extract_snpvar.py --allow-missing`) and
  `--non-funct`. finemapper's defaults differ from our frozen settings (residual variance estimated, max_iter 100,
  susieR 0.11.92), so it is a method sensitivity, not a replicate.

## Step 5b — 2026-09-24 ~09:55Z — machine reboot; recovery and two bugs found on restart

**What was lost.** All processes were killed. At that moment: Goal-A 1000G outputs were complete (written
08:59Z); PoPS LOCO had finished chr1–3 (chr4–6 were mid-fit); UKB LD downloads had all finished (09:50Z) and the
UKB `run` step had completed 2 loci.

**Validation after reboot (10:02–10:07Z).**
* `functional_finemapping.parquet`/`_summary.csv`: 36 loci × 2 methods, all 36 `fit_sprint5a.json` error-free, no
  VEP gaps — kept.
* PoPS chr1–3: `.preds` 18,383 genes each, no NaN; `.marginals` 57,742 features; `.coefs` complete — kept.
  chr4–6 logs moved to `data/interim/sprint5a/pops/loco/killed_by_reboot/`; rerun.
* Munged feature chunks: all 12 load, shapes (18,383 × cols) correct, file sizes exact — kept.
* UKB LD: all 33 files present, byte counts equal to provenance, all 33 sha256 recomputed — 0 mismatches.
* The scratchpad (outside the repo) was wiped by the reboot; nothing needed from it.

**Coordinator constraint.** PoPS limited to ≤3 threads/processes (MAGMA calibration running). `run_pops.sh` now
runs one chromosome at a time with `OMP/OPENBLAS/VECLIB_MAXIMUM_THREADS=3`. With OpenBLAS a chromosome took ~24
min (almost all in `RidgeCV` fitting, with the machine compressing/swapping memory). From chr6 on PoPS runs in env
`hi-pops-accel` (same python/numpy/pandas/scipy/scikit-learn versions; Apple Accelerate BLAS/LAPACK): ~9 min per
chromosome. Accelerate reproduces PoPS' shipped example output to 4.1e-15 (the same check OpenBLAS passed at
4.8e-15). numpy 1.21 + Accelerate prints spurious "divide by zero/overflow in matmul" RuntimeWarnings; a direct
Gram-matrix check gave max |Δ| = 0.0 and all-finite values. A planned chr1 OpenBLAS-vs-Accelerate recompute was
NOT completed (see Step 7).

**Bug 1 (mine) found and fixed before any result was used.** The first post-reboot UKB `run` gave
estimate_s_rss 0.82/0.88 at 3p21.1 (NT5DC2/SFMBT1) versus ≤0.01 elsewhere. Diagnosis: after dropping duplicated
UKB SNP keys I indexed the LD matrix with `range(len(snps))` instead of the surviving row labels, so every SNP after
a duplicate in the window was paired with the wrong LD row (~80 SNPs at 52.95–53.06 Mb had LD rows uncorrelated
with 1000G). Only windows containing a duplicate were affected (ATXN2L/AKAP6 were not: identical s before/after).
Fixed (label-based lookup for both the LD row and the allele), all 18 loci rerun. After the fix s = 0.0015–0.0094
at every locus. A pre-specified allele-coding QC was added at the same time (drop a SNP if |r|>0.8 in both panels
with opposite sign); after the fix it drops **0 SNPs at all 18 loci** (`data/interim/sprint5a/ukb_ld_allele_qc.csv`).
Superseded logs: `ukb_chain_attempt*_*.log`.

**Bug 2 (orchestration).** My chain script lacked `set -e`, so after the failed attempt its `finemapper` step
started alongside the next attempt; it was killed, its partial outputs deleted, and the script now uses `set -e`.

(results: see Step 6)

## Step 6 — Goal A results (1000G + UKB LD), 2026-09-24T10:58Z

Files: `reports/sprint5a/functional_finemapping.parquet` (5,019 rows: locus, method, credible_set, variant, pip,
prior, VEP consequence), `reports/sprint5a/functional_finemapping_summary.csv` (146 rows: per locus × method),
`reports/sprint5a/functional_finemapping_pip05_robustness.csv` (every variant with PIP>0.5 in either 1000G fit,
and its PIP under all four UKB-LD analyses).

**LD fit.** estimate_s_rss: 1000G 0.014–0.101; UKB 0.0015–0.0094 at all 18 testable priority loci. UKB LD fits the
Davies z far better (expected: Davies is ~79% UKB). This makes the UKB-LD runs the more trustworthy of the two.

**Global effect of the priors (1000G, 36 loci).** Total CS variants 1,491 → 1,087; loci with ≥1 variant PIP>0.5:
4 → 11. Priority loci (19): median total CS size 21 → 10 variants; CS count 26 → 27; CS size shrank at 16/19.

**Variants with PIP > 0.5 and whether they survive (plain 1000G / PolyFun 1000G / plain UKB / PolyFun UKB /
finemapper-funct UKB / finemapper-nonfunct UKB):**

| locus | variant | annotation | PIPs | reading |
|---|---|---|---|---|
| SLC39A8 | rs13107325 | SLC39A8 missense A391T | 0.93 / 1.00 / 0.92 / 1.00 / 1.00 / 0.89 | robust; the only coding variant >0.5; already >0.5 without priors |
| AKAP6 | rs3925864 | AKAP6 intron | 0.07 / 0.93 / 0.05 / 0.81 / 0.78 / 0.05 | prior-driven, LD-robust |
| AKAP6 | rs4261436 | AKAP6 3'UTR | 0.03 / 0.51 / 0.02 / 0.40 / 0.40 / 0.02 | prior-driven, falls <0.5 with UKB LD |
| EXT1 | rs10110572 | EXT1 intron | 0.13 / 0.90 / 0.13 / 0.88 / 0.87 / 0.13 | prior-driven, LD-robust (no CS passes purity in UKB runs) |
| EXT1 | rs73327853 | EXT1 intron, enhancer | 0.10 / 0.63 / 0.05 / 0.23 / 0.14 / 0.03 | not LD-robust |
| NKIRAS1 = UBE2E1 (same signal) | rs9755750 | RPL15 3'UTR, enhancer | 0.29 / 0.85 / 0.26 / 0.83 / 0.83 / 0.26 | prior-driven, LD-robust |
| BTN2A1 | rs36162392 (lead) | promoter/regulatory | 0.10 / 0.59 / 0.12 / 0.63 / 0.63 / 0.12 | prior-driven, LD-robust |
| KCNJ3 | rs2591173 (lead) | KCNJ3 intron | 0.15 / 0.51 / 0.16 / 0.53 / 0.51 / 0.15 | borderline |
| NEGR1 | 7 single-SNP CSs, PIP≈1 | intergenic/upstream | 1.0 / 1.0 / 0.00 / 0.00 / 0.00 / 0.00 | **1000G artefact**: all vanish with UKB LD (plain UKB: one 34-SNP CS, max PIP 0.28) |
| DDN | rs11168951 | intron (TUBA1C region) | 0.73 / 0.27 / 0.18 / 0.02 / 0.02 / 0.13 | not robust |
| non-priority | SYT1 rs7963801 0.44→0.99; ERLIN1 rs2862954 missense I/V 0.29→0.96 (CPN1 locus); L83594 rs74944275 0.50→0.26 | | 1000G only | UKB LD not run (not priority) |

**Coding variants whose PIP rises under PolyFun (1000G) at priority loci — none reaches 0.5 except SLC39A8:**
DPP4 locus: IFIH1 rs3747517 H/R 0.04→0.37 (becomes the locus max-PIP variant, also under UKB LD 0.43/0.37), GCA
rs17783344 S/A 0.01→0.23; FOXO6 rs4359027 A/P 0.06→0.16 (in CS); DCC rs2229080 R/G 0.00→0.12 and rs2270951 T/M
0.00→0.09 (in CS); EXOC4 rs6953296 Q/H 0.01→0.16; NT5DC2/SFMBT1: ITIH3 rs35271262 T/M 0.01→0.15, STAB1 rs7630214
A/P 0.01→0.11; KIFC2 locus: PPP1R16A rs11777703 splice-region/enhancer 0.10→0.34 (locus max), GPT rs1063739 H/D
0.02→0.16; DNPH1 locus: CNPY3 rs9471969 S/I 0.01→0.14, CUL9 rs2273709 H/P 0.01→0.11; DDN locus: KMT2D rs3782357
Q/H 0.03→0.10, DDN rs10783299 E/A 0.06→0.07; AKAP6 rs1051695 N/D 0.02→0.06; ATXN2L locus: SH2B1 rs7498665 T/A
0.01→0.05. These are small absolute PIPs; the rise is by construction (coding SNPs carry the highest prior bins).

**Loci that remain unresolved.** ATXN2L (max PIP 0.39 with priors, 23-SNP CS), DCC (154–242-SNP CS), ZSCAN31
(90-SNP CS; no UKB LD), FOXO6 (57+11), DPP4, EXOC4, NT5DC2/SFMBT1, KIFC2, DNPH1 (no CS in any fit).

**Conclusion.** Functional priors roughly halve credible sets and create 5 LD-robust PIP>0.5 variants at priority
loci (AKAP6 rs3925864, EXT1 rs10110572, RPL15-3'UTR rs9755750, BTN2A1 rs36162392, KCNJ3 rs2591173), but in every
case except SLC39A8 the PIP>0.5 exists **only** with the prior (plain PIPs 0.07–0.29). They are candidates for
functional follow-up, not causal variants. The only coding variant above 0.5 is SLC39A8 A391T, which was already
there without priors. The 1000G NEGR1 "seven certain variants" are an LD-reference artefact and should not be cited.

**Uncertainty.** (i) Priors are UKB 15-trait functional enrichments, not cognition-specific. (ii) Davies ~79% UKB,
priors from UKB, UKB LD from UKB: the "robust" label means robust to LD panel, not independent evidence. (iii) The
finemapper sensitivity uses a different susieR version and estimates residual variance; agreement with our frozen
settings is reassuring but not a replication. (iv) VEP consequence is transcript-level annotation, not function.

## Step 7 — PoPS completion, stop recovery and final record (2026-09-24T12:45Z)

**Stop recovery.** The coordinator's stop at ~11:25Z terminated the chr11 fit (partial log kept in
`data/interim/sprint5a/pops/loco/killed_by_stop/`); `run_pops.sh` itself survived and finished chr12–22 (1 process ×
3 threads throughout). chr1–10 were revalidated (18,383 predictions, 57,742 marginals, complete coefficients). A
second `run_pops.sh` pass (12:39:52Z) recomputed only chr11 and ran `pops_collect.py`; it exited 0 at **12:45:01Z**.
All 22 folds: RidgeCV alpha 31,622.78; best CV score −0.518 to −0.503; 12,858–14,367 of 57,742 features selected.

**chr1 OpenBLAS vs Accelerate check: NOT RUN.** The attempt at 13:46Z failed before any computation (zsh passed the
21 held-in chromosomes as one argument; PoPS rejected it). It was not retried because the coordinator asked to finish.
chr1–5 (OpenBLAS) and chr6–22 (Accelerate) are therefore linked only by the PoPS example check (4.8e-15 vs 4.1e-15).
This is an open uncertainty, although small.

**Output.** `reports/sprint5a/pops_scores.csv`: 550 gene × locus rows over 159 loci, 520 scored. 30 rows unscored:
29 are not in PoPS' `gene_annot_jun10` or were lost in the Entrez→Ensembl re-keying (12 histone genes and ZSCAN26 at
L3123; ZSCAN26 at L64288; BOP1, CATSPERQ, SCRT1 at L65265; DHRS11, GGNBP2, MRM1, MYO19, PIGW, TBC1D3H, ZNHIT3 at
L79922; PKD1L3 L83449; STIMATE-MUSTN1 L51460; TBC1D29P L84282). One has no unique Ensembl mapping (C17orf47,
L284161; stored as "nan" in the frozen JSON, symbol taken from `gene_id_map.tsv`). 94 of 158 scored loci have only one
scored member gene, so for them "top in locus" is trivially true.

**Priority loci (PoPS top gene; Sprint-5 anchor's rank).** Agree: AKAP6, EXT1, EXOC4, DCC, KCNJ3, FOXO6, NEGR1 (EXT1,
DCC, KCNJ3, NEGR1 are single-gene loci). Disagree: ATXN2L→NFATC2IP (ATXN2L 2/21), NT5DC2→BAP1 (NT5DC2 13/19),
SFMBT1→NEK4 (8/14), DPP4→SLC4A10 (DPP4 5/5; IFIH1 3/5), BTN2A1→HMGN4 (3/26), SLC39A8→NFKB1 (SLC39A8 2/3, PoPS
score negative), DDN→CACNB3 (7/19), NKIRAS1/UBE2E1→THRB (NKIRAS1 2/5, UBE2E1 3/5, RPL15 4/5), ZSCAN31→ZSCAN12 (7/13),
L65265→LRRC24 (KIFC2 5/21, FOXH1 14/21), L55168→SRF (DNPH1 7/18, CUL9 12/18). Neither Sprint-5 CAUSAL_GENE_MODERATE
gene (KIFC2, DNPH1) is top in its locus. PoPS disagrees with the variant-level Goal-A pointers too: SLC39A8's missense
signal gets a below-median PoPS score, and RPL15 (3'UTR variant rs9755750) ranks 4/5.

**Reading.** PoPS is genome-wide, feature-based prioritisation. It is not local causal evidence and is not counted
as a variant-to-gene vote. Where PoPS and the Sprint-5 evidence disagree, nothing changes class.
