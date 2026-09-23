# Sprint 5 — PsychENCODE brainSCOPE single-cell brain QTL research log

Scope: acquire and analyse the public brainSCOPE (Emani et al., *Science* 2024) single-cell QTL data for the
Sprint-5 cognition credible-set variants (`data/sprint5/query_variants_cognition.csv`) and candidate genes.
No accounts, logins, click-through terms or controlled-access requests were used.

---

## Entry 1 — 2026-09-23 21:05–21:08 UTC — What does brainSCOPE publish, and where?

- **Question:** Which brainSCOPE files are public (QTL types, callsets, enhancer–gene links), and in what form?
- **Searches / sources:** WebSearch "brainSCOPE PsychENCODE single-cell eQTL download files cell type eQTL 388
  brains"; fetched `brainscope.gersteinlab.org` index, `key_resource_files.html`, `integrative_files.html`,
  `output-sig-eQTL.html`, `output-reg-celltype.html`, `raw_data_files.html` and the Apache directory listing
  `https://brainscope.gersteinlab.org/data/` (+ sub-directories).
- **Accepted:** the portal's own file listings (primary source, dated 2023-04 to 2024-12).
- **Findings:** public, no-login files include the core scQTL callset (`sig_QTLs/[ct]_sig_QTLs.dat`, 17 cell
  types), eGene lists, LD-pruned callset, "aggregated" class callsets, conditional top hits, Bayesian scQTLs,
  isoform-usage QTLs (sQTLseekeR2), dynamic eQTLs, tested-SNP lists (`candidate_SNPs_for_QTL_calls`, 24 cell
  types), QTL covariates, pseudobulk expression matrices, scCRE peaks, GRNs and `eQTL_edge` files. Raw FASTQs and
  genotypes are Synapse controlled-access.
- **Conclusion:** only SIGNIFICANT scQTL pairs are published; no full nominal summary statistics exist on the portal.

## Entry 2 — 2026-09-23 21:06–21:12 UTC — Primary paper and supplement: N, build, method, thresholds

- **Question:** N, ancestry, cohorts, genome build, annotation, QTL method, thresholds, effect-allele convention.
- **Sources:** PubMed (PMID 38781369 → PMC11365579; preprint PMID 38562822 → PMC10983939); full text via NCBI
  efetch XML (PMC HTML is bot-protected; eScholarship PDF returned 0 bytes / HTML → rejected); bioRxiv
  supplementary PDF `.../2024.03.18.585576/DC1/embed/media-1.pdf` (37.5 MB, read with pdftotext; kept in
  interim, sha256 in PROVENANCE.json); GitHub `gersteinlab/PsychENCODE_SingleCell_Integrative` (README, scQTL
  README, LICENSE); portal code tarball `core_scqtl_processing_code.tar.gz`.
- **Verified facts (with section):**
  - 388 adults, DLPFC, 12 cohorts (8 PsychENCODE: CMC, UCLA-ASD, SZBDMulti-Seq, MultiomeBrain, DevBrain, IsoHuB,
    PTSDBrainomics, LIBD; 4 external: ROSMAP, Ma-Sestan, Velmeshev, Girgenti-snMultiome); 182 controls; >2.8 M
    nuclei; 28 harmonised cell types (main text).
  - Genotypes: array/WES/WGS/snRNA calls lifted to **hg38**, REF fixed to hg38 with plink2; TOPMed imputation
    (Minimac4, Eagle 2.4, R2>0.3); MAF>=0.05; **1.95 M SNPs, 383 individuals** (supp. §1). Public tested-SNP list
    = 1,953,861 IDs (L6b) — consistent.
  - scQTL method (supp. §4.1 + code): pseudobulk mean UMI per individual × cell type (>50 nuclei of that type,
    >300 total), log(CPM+1), genes with >10% non-zero; QTLtools cis, **1 Mb around TSS**, `--normal`; covariates
    sex, age, diagnosis, cohort, 5 genotype PCs, 100 expression PCs (20 for small types); 10,000 permutations,
    beta-approximated gene p, Storey **q<=0.05 per cell type**; per-gene nominal threshold F⁻¹(pt) (GTEx scheme).
    `pull_sig_QTLs.py` confirms the public files contain only pairs with nominal p <= gene threshold.
  - Columns of `_sig_QTLs.dat`: gene symbol, chr, TSS, TSS, strand, n cis variants, distance, `chr:pos:REF:ALT`,
    chr, pos, pos, nominal p, r², slope, best-hit flag (supp. §4.1). **No SE is published.**
  - Isoform-usage QTLs (supp. §4.5): sQTLseekeR2, TSS ±5 kb, 22 cell types; files list isoGenes with beta
    p<0.05 **without FDR filtering** (paper: 21 isoGenes at FDR<0.05). No caQTLs and no leafcutter-type sQTLs exist.
  - Gene annotation: genes identified by **symbol only**; the GTF/GENCODE release for the TSS coordinates is **not
    stated** (CellRanger v6.0 used for counts; GENCODE 43 is cited only for conservation). Not resolved.
  - Licence: portal says output files are "fully open source"; no explicit data licence found. Code: "MIT License
    for Academic Use".
- **Rejected:** assuming the scQTL N = 388 (it is per cell type, see Entry 4).

## Entry 3 — 2026-09-23 21:15 UTC — Effect-allele convention (empirical check)

- **Question:** Is the slope per copy of ALT in `chr:pos:REF:ALT`?
- **Method:** `pipelines/sprint5/brainscope_allele_check.py` compares brainSCOPE core slopes with eQTL Catalogue
  (ALT-coded, GRCh38) adult-brain bulk betas (CommonMind, ROSMAP, 14 GTEx brain tissues; bulk p<1e-6) already
  extracted in Sprint 4, matching gene symbol + hg38 chr:pos:REF:ALT.
- **Result:** 108,485 matched rows (5,602 unique gene–variant pairs, 32 genes); sign concordance **99.99%**; 0
  matches with REF/ALT swapped. Output `data/sprint5/brainscope_allele_check.json`.
- **Conclusion:** build = GRCh38 and effect allele = ALT, both verified. (The CommonMind/ROSMAP part of this check is
  not independent of brainSCOPE because of donor overlap, but GTEx-only concordance is also ≥99.9% in every tissue.)

## Entry 4 — 2026-09-23 21:16–21:25 UTC — Sample sizes and cohort overlap with our bulk eQTL sources

- **Sources:** public QTL covariate files (`qtl_covariates/*.bed`: one column per individual, cohort indicator
  rows), `PEC2_sample_metadata.txt`; WebSearch on Ruzicka et al. 2024 (PMID 38781388) for the SZBDMulti-Seq cohort.
- **Findings:**
  - N per cell type (core callsets): L2.3.IT 346, Oligo 339, L5.IT 333, L6.IT 328, L4.IT 319, Astro 315,
    Chandelier/Pvalb 313, OPC 295, Vip 294, Sst/Sst.Chodl 278, Lamp5 223, Micro/PVM 207, L6.CT 202, L6b 171,
    Lamp5.Lhx6 163, L5.6.NP 160, PC 97. Union across the 17 types = 352 individuals.
  - 7 cell types have tested-SNP lists but **no core callset** (Endo/VLMC 128, Immune 36, L5.ET 28, L6.IT.Car3
    123, Pax6 36, SMC 23, Sncg 145): residual df after covariates is ≤21 or negative. These are NOT "tested, no
    eQTL".
  - Metadata ancestry (1000G): EUR-majority, with AFR/AMR/EAS minorities (counts in PROVENANCE.json).
  - **Overlap:** all 100 brainSCOPE CMC donors are `CMC_MSSM_*` (25–93 per cell type in the QTL covariates; 94 in
    the union) → likely overlap with CommonMind DLPFC bulk eQTLs (eQTL Catalogue QTD000075). 46 ROSMAP donors
    (43 in the union) → likely overlap with ROSMAP bulk eQTLs. No GTEx donors. SZBDMulti-Seq = 24 control / 24
    SCZ / 24 BPD ("SZBD-Kellis"); brain bank not stated — design resembles the McLean cohort, overlap with CMC
    judged unlikely but **unverified**. Individual-level overlap cannot be confirmed without controlled IDs.
- **Conclusion:** brainSCOPE–CommonMind/ROSMAP agreement is not independent replication; GTEx agreement is.

## Entry 5 — 2026-09-23 21:08–21:30 UTC — Data acquisition

- Script `pipelines/sprint5/brainscope_fetch.py` (curl, 8 parallel workers; ~0.36 MB/s per connection).
  187 records, 0 failures, all in `data/interim/sprint5/brainscope/` (gitignored), 1.6 GB on disk (GRNs 1.0 GB,
  tested-SNP lists 215 MB, aggregated callsets 173 MB, core callset zip 27 MB).
- Pseudobulk expression matrices (743.7 MB compressed) were **streamed, not stored**: only gene coordinate
  columns + sample counts were kept (sha256 of both source and reduced file recorded).
- Full per-file URL / UTC / bytes / sha256: `data/raw/sprint5/brainscope/PROVENANCE.json`; dataset table
  `data/sprint5/brainscope_datasets.csv` (209 rows: 198 PUBLIC, 7 NOT_PUBLISHED, 4 BLOCKED).

## Entry 6 — 2026-09-23 21:41 UTC — "Aggregated" callsets are not a separate analysis

- **Check:** the sorted contents of `aggregated_qtl/excitatory__sig_QTLs.dat` are byte-identical to the
  concatenation of the 7 excitatory core files (928,054 lines); `inhibatory` = the 5 inhibitory core files
  (284,689); `non_neuronal` = Astro+OPC+Oligo+Micro.PVM (240,990; md5 match).
- **Decision:** excluded from the lookup to avoid double counting (the portal describes them as a separate
  aggregated analysis; the files do not support that).

## Entry 7 — 2026-09-23 21:40–21:53 UTC — Lookup, directionality, LD proxies

- **Script:** `pipelines/sprint5/brainscope_lookup.py --variants <csv> --out-prefix <path>` (helpers
  `brainscope_data.py`, `brainscope_ld.py`). Reusable for another variant list: needs `rsid, chr38, pos38`;
  alignment from `davies_z` + `davies_effect_allele` (other allele from the Davies 2018 file by rsID), from the
  Davies file directly when the input z is missing, or from `increasing_allele[, other_allele]`.
- **Rules:** trait-increasing allele = Davies effect allele if z>0 else the other allele; A/T and C/G variants
  flagged `PALINDROMIC_AMBIGUOUS` and excluded from direction consensus (3,808 lookup rows); SE derived from p and
  residual df (`se_derived`, approximate); "TESTED_NOT_SIGNIFICANT" = variant in the tested SNP list, gene in the
  cell type's matrix, TSS within 1 Mb, pair absent from the significant list — **not evidence of no effect**.
- **Coverage:** 1,914 input rows → 1,572 unique variants in 159 loci; 1,191 tested in ≥1 core cell type; 381 not
  tested in any cell type (mostly MAF<0.05 in this multi-ancestry cohort, multi-allelic sites or indels);
  375 variants are significant eSNPs for ≥1 gene. 31 variants had no allele information (no Davies record).
- **LD proxies:** eQTL best hit (per gene × cell type) mapped hg38→rsID via Ensembl REST overlap (cached),
  r² with the locus GWAS lead in 1000G EUR (503 individuals, PLINK .bed read with numpy). 93 of 314 significant
  gene×cell-type rows are `LD_NOT_COMPUTABLE` (indel best hits, rsID not found, or absent from 1000G).
- **Colocalisation:** **NOT_TESTABLE** for every locus × gene × cell type (1,116 rows in
  `reports/sprint5/brainscope_coloc.parquet`): coloc.abf needs all tested variants; only significant pairs are
  public and genotypes are controlled. No "significant-only" pseudo-coloc was attempted (it would be biased).

## Entry 8 — Results summary (2026-09-23 21:53 UTC)

Directions are for the cognition-increasing allele. All within-cell-type directions were 100% consistent across
the significant query variants, and no gene showed opposite directions across cell types.

| gene (locus) | significant core cell types | direction | LD support (eQTL best hit vs GWAS lead) | bulk (Sprint 4) |
|---|---|---|---|---|
| WBP2NL (L1565/L6942) | 10: Astro, Chandelier/Pvalb, L2/3 IT, L4 IT, L5 IT, L6 IT, Lamp5, Oligo, Sst, Vip | LOWER | best hit in GWAS credible set in 8 types (r² 0.83–0.89); Lamp5, Oligo r² ~0.3 | DIRECTION_RESOLVED LOWER — agrees |
| RPS26 (L319) | 10: Chandelier/Pvalb, L2/3 IT, L4 IT, L5 IT, L6 CT, L6 IT, Lamp5, Oligo, Sst, Vip | HIGHER | best hit in credible set (r² 0.68–0.72 with lead) | DIRECTION_RESOLVED HIGHER — agrees |
| CYP2D6 (L1565) | 6: Chandelier/Pvalb, L2/3 IT, L5 IT, Lamp5, Sst, Vip | HIGHER | r² ≥0.8 in Chandelier/Pvalb, Vip (Lamp5 0.79); L2/3 IT, L5 IT best hits not in LD (r² ~0.2) | rows-only HIGHER — agrees |
| DHRS11 (L79922) | 4: Chandelier/Pvalb, L2/3 IT, L5 IT, L6 IT | LOWER | best hit in credible set (L5 IT, L6 IT); indel best hits elsewhere | rows-only LOWER — agrees |
| NAGA (L1565) | 1: L5 IT | LOWER | r² 0.57 | rows-only LOWER — agrees |
| SH2B1 (L51327) | 1: L2/3 IT | HIGHER | best hit rs8061590 in credible set (r² 0.99 with lead) | no bulk majority |
| GOSR1 (L84282) | 1: L2/3 IT | HIGHER | r² 0.996 | rows-only HIGHER (GTEx) — agrees |
| NEGR1 (L257194) | 1: Lamp5 (1 variant) | HIGHER | r² 0.02 — eQTL signal distinct from the GWAS lead | rows-only HIGHER (ROSMAP) — agrees |
| EXOC4 (L60412) | 1: L5 IT (2 variants) | LOWER | r² 0.12 — distinct | no bulk majority |

Other signals: NPIPB9/NPIPB7/AC133550.3 at 16p11.2 (HIGHER, L2/3 IT and others); CWF19L1 (L6319, 5 types,
HIGHER, r² 0.81); 17q21.31 genes KANSL1, LRRC37A2, ARL17B, CRHR1, MAPT (LOWER in most types, r² 0.87–0.94;
inversion region, interpret with care); PBRM1/GLT8D1 at 3p21 (HIGHER, r² 0.52–0.70). Bayesian and/or LD-pruned
callsets reproduce WBP2NL, RPS26, DHRS11, SH2B1 (both) and CYP2D6 (LD-pruned only). Isoform-usage: NEK4 rs11130324 in L2/3 IT
(fdr_bh 0.048, unsigned); ERBB3/ZNHIT3 listed but not FDR-significant.

**Nulls (tested, not significant in any of 17 core cell types; low power, not evidence of absence):** ATXN2L,
AKAP6, EXT1, DCC, KCNJ3, CACNA1I, PTPRT, CLCN2, SYT1, MEF2C, RHEBL1, ERBB3, BSN, KDM5B, PFKM, GNL3, NEK4, PPM1M,
ZNHIT3, GGNBP2, DDN, SFMBT1, DPP4, SMG7, CPN1, NUDT12. **Not testable:** SLC39A8, CADM2, ADGRB2, CUL9 (query
variants not in the tested SNP lists); NT5DC2, SUOX, TUFM (symbols absent from all 24 pseudobulk matrices);
GIGYF1, ANKRD12, SLC8A1, RC3H2, CACNA1A, BCAS3 (no query variant within 1 Mb of the TSS).

**Enhancer–gene links (GRNs):** query variants fall in GRN elements linked to ATXN2L, SH2B1, DHRS11, GGNBP2
(promoters), NEGR1 (promoter, neuronal GRNs), RHEBL1/DDN (enhancer, excitatory GRNs), CACNA1I, DPP4, SYT1
(enhancer, excitatory GRNs) — `reports/sprint5/brainscope_enhancer_gene_links.csv`. These are annotation overlaps,
not allelic evidence.

## Remaining uncertainty

- Gene annotation release for TSS coordinates is undocumented; symbol matching may miss renamed genes (e.g.
  NT5DC2, SUOX, TUFM absent from every matrix for reasons not established).
- `se_derived` assumes df = N − non-constant covariates − 2; QTLtools may drop collinear covariates.
- Donor overlap with CommonMind/ROSMAP is inferred from cohort labels, not confirmed at individual level.
- The cohort labels "Urban" and "Kreigstein" in the covariate files are not mapped to the metadata cohort names
  (probably MultiomeBrain and Velmeshev) — unverified.
- LD proxies use 1000G EUR while brainSCOPE is multi-ancestry (EUR-majority).
- Full nominal statistics would require the authors or controlled genotypes (Synapse syn51111084; AD Knowledge
  Portal syn53479857) — access blockers, not pursued.
