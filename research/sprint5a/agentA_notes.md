# Sprint 5A — Agent A research log: brainSCOPE gap-fill, PsychENCODE developmental QTLs, GTEx V11

- **Branch:** `sprint-5a/open-data-exhaustion`. Nothing was committed.
- **Access used:** none. No accounts, sign-ins, terms acceptance or tokens were used at any point.
- **Times:** all times are UTC on 2026-09-24.
- **Where the data lives:** large raw files are in `data/interim/sprint5a/` (gitignored). The committed provenance is `data/raw/sprint5a/{brainscope,psychencode_dev,gtex_v11,gencode}/PROVENANCE.json`.
- **Protocol:** the frozen protocol in `research/sprint5a/protocol_rules.json` decides how each result may count:
  - brainSCOPE direct and cell-specific rows are a direction layer only;
  - GRN rows are never a vote;
  - developmental QTLs are a timing flag only;
  - GTEx V11 belongs to the bulk QTL class and is not a new independence unit.

---

## A1 — 08:33–08:40 · Which brainSCOPE files are public now? (gap-fill)

- **Question:** Is each of the 13 requested file families public, and which ones were missing from Sprint 5?
- **Sources:**
  - live Apache listings of `https://brainscope.gersteinlab.org/data/` and its sub-directories (`conditional_qtls/`, `meta_qtls/`, `bcCRE/`, `validation/`, `bayesian_qtl/`, `atac_peaks/`, `sig_QTLs/`, `sig_eGenes/`);
  - bioRxiv supplement text from Sprint 5 (`supp.txt`), §2.4, §4.1, §4.2 and §5.3.
- **Accepted:** the portal listings, as the primary source.
- **Already present from Sprint 5:** PEC2 metadata, sig_QTLs, sig_eGenes, SNPs.dat.gz, conditional top variants, bayesian_scQTLs, scCRE peaks (the zip is identical to `atac_peaks/*.bed`), GRNs and eqtl_edge.
  - The Sprint-5 sha256 hashes were re-verified: **163 MATCH** (24 reduced pseudobulk files skipped by design). This was repeated after the reboot with the same result.
- **Newly downloaded** by `pipelines/sprint5a/brainscope_gapfill_fetch.py`:

  | File | Size |
  |---|---|
  | `conditional.[ct].txt` (17 cell types) | 230 MB |
  | `metaQTLs.txt` | 208 MB |
  | `adult_bcCREs.bed` (253,638 b-cCREs, hg38) | 14 MB |
  | `crispr_validation_results.xlsx` | 9.6 kB |
  | `starrseq_enhancers_merged.bed` | 0.2 MB |

- **Not downloaded:** `snrna_expr_matrices.zip` (7.8 GB), as instructed.
- **CRISPR table contents:** TaqMan qPCR results for 4 enhancer knockouts in primary NPCs.
  - The targets are NGEF (0.45×), RORB (0.56×), PLEKHO1 (0.16×) and TOM1L2 (0.42×).
  - Enhancers are given only as ENCODE-v2 IDs (EH37E…) **without coordinates**, so only a gene-level flag is possible.

## A2 — 08:36–08:50 · Can any brainSCOPE output support Bayesian colocalisation?

**Evidence** (from the files; see `reports/sprint5a/brainscope_coloc_testability.json`)

| Output | What it contains | Enough for colocalisation? |
|---|---|---|
| `[ct]_sig_QTLs.dat` | Only pairs with nominal p ≤ the gene's threshold, and no SE. Sprint 5 confirmed this from `pull_sig_QTLs.py`. | No |
| `conditional.[ct].txt` | 100% of rows are forward- or backward-significant. Median fraction of cis variants listed per gene × cell type is **3.1%**. Only 20 of 11,661 gene × cell-type units list all cis variants (tiny cis windows). | No |
| `bayesian_scQTLs.dat` | One "anchor" eSNP per eGene (the primary-callset top eSNP), re-estimated across 24 cell types. Columns are posterior mean β and SD only: **no PIP** and no other variants. 8,966 gene–SNP pairs; at most 12 SNPs per gene, which come from different anchors. | No |
| `metaQTLs.txt` | Union of core (1,454,253), LD-pruned (1,827), Conditional (27,036), Bayesian (78,191) and dynamic (19,502) significant entries. | No |

- **About the Bayesian rows in `metaQTLs`:** they are a subset of the Bayesian file. The excluded rows have *higher* |β/SD|, which suggests the excluded pairs are those already in the core callset. This is an inference, not documented.
- **Conclusion:** **COLOC NOT TESTABLE with public output.** No colocalisation was fabricated, and no "significant-only" pseudo-coloc was run. Every QTL locus × gene × cell type has a `COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT` row.
- **Blocker:** full nominal statistics require author release or the controlled genotypes (Synapse syn51111084 and AD Knowledge Portal syn53479857). This needs PI approval and a data-use certificate.

## A3 — 09:45–11:25 · Typed brainSCOPE evidence (`pipelines/sprint5a/brainscope_typed_evidence.py`)

**Inputs**
- 1,773 locus × variant rows, covering 1,624 unique variants in 212 "loci":
  - 159 cognition loci, of which 36 are Gate-C;
  - 53 math-53 leads.

**Rules**
- Exactly one evidence type per row.
- Direction is always for the trait-increasing allele. The slope is per ALT allele, as verified in Sprint 5.
- LD-proxy directions carry the **signed** 1000G EUR r.
- Palindromic variants are excluded from direction consensus.

**LD mapping change (09:45)**
- Ensembl REST `overlap/region` calls were taking 7.5 s and then timing out at 30 s. The first run spent more than 60 minutes on 1,952 lookups and was abandoned.
- Replacement: offline UCSC `hg38ToHg19.over.chain.gz` point liftover, then a match on (chr, pos37, allele set) to the 1000G EUR `.bim` (`pipelines/sprint5a/liftover_map.py`).
- Validation:
  - 1,351 of 1,354 query variants lift to their recorded GRCh37 position.
  - Against the Sprint-5 Ensembl cache, 121 of 128 agree. The 7 disagreements are rsID merges, and the 1000G ID is the one needed for LD.
- Coverage: 21,026 of 23,258 signal-variant rows and 1,597 of 1,603 query variants were mapped. 45,746 query × signal pairs lacked LD (unmapped indels, or absent from 1000G).

**Row counts** (`reports/sprint5a/brainscope_typed_evidence.parquet`, 28,186 rows)

| Evidence type | Rows |
|---|---|
| CELL_SPECIFIC_QTL_SUPPORT | 19,020 |
| DIRECT_VARIANT_GENE_OVERLAP | 6,021 |
| GRN_SUPPORT | 1,106 |
| REGULATORY_ELEMENT_SUPPORT | 1,023 |
| COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT | 1,016 |

**Gene summary** (`reports/sprint5a/brainscope_gene_summary.csv`)
- 179 locus × gene rows. Best evidence: DIRECT 113, REGULATORY 54, CELL_SPECIFIC 10, GRN 2.
- At the Gate-C loci: DIRECT 37, CELL_SPECIFIC 2, REGULATORY 45, GRN 2.

**Main findings**

| Gene | Locus | Direction | Cell types and support | Notes |
|---|---|---|---|---|
| WBP2NL | L1565 | LOWER | All classes; the query variant is the primary signal (r² = 1) | — |
| RPS26 | L319 | HIGHER | All classes; r² = 1 | — |
| CYP2D6 | L1565 | HIGHER | Excitatory, inhibitory and glia; r² 0.99 | — |
| NAGA | L1565 | LOWER | L5/L6 IT only | Not in LD with a signal lead |
| DHRS11 | L79922 | LOWER | All classes; r² = 1 | — |
| GOSR1 | L84282 | HIGHER | Direct in L2/3 IT; LD support across many types, r² 0.996 | — |
| SH2B1 | L51327 | HIGHER | Direct in 9 cell types including Astro, Chandelier/Pvalb, L2/3 IT, L6 CT, Lamp5 and PC; primary signal r² = 1; also GRN and regulatory rows | — |
| CWF19L1 | L6319 | HIGHER | r² 0.82 | — |
| 16p11.2 NPIPB7, NPIPB9 and AC133550.3 | L51327 | HIGHER | — | — |
| SGF29, SULT1A2 | L51327 | LOWER | — | — |
| GLT8D1, PBRM1 | L51460 / L91869 | HIGHER | r² 0.93 | — |
| MUSTN1 | L51460 | LOWER | — | — |
| ITIH4 | L51460 | LOWER | — | Not in LD with a signal lead |
| FAM160A1 (FHIP1A) | L5188 | HIGHER | r² 0.84 | — |
| EXOC4 | L60412 | LOWER | L5 IT only; no LD with a signal lead | Distinct signal |
| NEGR1 | L257194 | HIGHER | Lamp5 only; no LD with a signal lead; also GRN promoter links | — |

**Consistency**
- Within each gene, cell-type directions are 100% consistent. The exceptions are CRHR1 (17q21.31 inversion), STAU1, EPHA5-AS1 and YJEFN3 (math).
- Directions match Sprint 5 for every overlapping gene.

**Signal types**
- 68 QTL genes are supported through a **primary** signal and 5 through a **secondary** conditional signal. Among Gate-C genes, the secondary-signal genes are AL513166.1 (NEGR1 locus), SH3D19 and PCNX4.

**Genes with no allelic evidence**
- RHEBL1 has only regulatory and GRN rows: an excitatory-neuron enhancer in open chromatin, with no allelic evidence.
- NT5DC2, TUFM and SUOX are absent from every pseudobulk matrix. This is not due to renaming; see A8.

**CRISPR**
- Only NGEF (a math locus, rs72976151, regulatory row) appears. No cognition-locus gene is in the CRISPR table.

**Caveats**
- REGULATORY rows link genes by scGRNom correlation GRNs or by promoter proximity. Neither is an activity-based ABC/rE2G link, so under the protocol they are annotation, not ENHANCER_LINK.
- 1000G EUR LD is applied to a multi-ancestry (EUR-majority) cohort.
- The bug fix at 11:0x was in how the boolean flags were serialised; the analysis itself was not changed.

## A4 — 08:41–08:47 · PsychENCODE Phase-II developmental resources

**Searches**
- WebSearch: "devBrainHub PsychENCODE developing brain xQTL Wen 2024 summary statistics download".
- Zenodo API: record 12729266, plus searches for part 2.
- GitHub API: README of `gandallab/devBrain_xQTL`.
- devBrainHub JavaScript bundle, to find its API endpoints.
- NCBI esummary/efetch: PMID 38781368 and PMC12147038.

**Paper (accepted):** Wen C et al. 2024, *Science* 384:eadh0829.
- 672 samples; 654 after QC; 4–39 PCW.
- EUR N = 292 (AMR 164, AFR 145, SEA 29, EA 24).
- Tri1 EUR (4–13 PCW) N = 143; Tri2 EUR (14–26 PCW) N = 145; Tri3 N = 4, not analysed.
- FastQTL, 1 Mb cis window, HCP covariates.
- Build hg19. The paper states GENCODE v29lift37 (STAR); the GitHub README states a Salmon v33lift37 index.

**Resources**

| Resource | Access | Statistics | Decision |
|---|---|---|---|
| Zenodo 12729266 ("part 1", CC-BY-4.0) | **Open** | eQTL nominal files (EUR 2.86 GB, ALL 4.05 GB, AFR, AMR, Tri1 1.97 GB, Tri2 1.94 GB) are **full cis statistics**: p up to 1.0, verified. Also permutation tables, isoQTL (ALL nominal 16.2 GB, AFR 15.1 GB, grouped permutation), EUR/ALL `.bim` (A1 = effect allele), PrediXcan/FUSION weights. | **Acquired** |
| devBrain sQTL summary statistics | Not in Zenodo part 1. Listed on a Galaxy public history (`usegalaxy.org/u/cindywen/h/devbrainsumstats`) and on Synapse syn50897018.5 (sign-in required). | — | Synapse needs an account plus terms: blocked. The Galaxy history was not probed further. |
| devBrainHub API (`/api/devmeta/{eqtl,isoqtl,sqtl}/extra/<gene>`) | Open JSON | Per-gene full cis table (β, −log10 p) | Not used for inference: the analysis behind "devmeta" is undocumented. Zenodo files were preferred. |
| Walker 2019, Aygun 2021, BrainSeq | eQTL Catalogue r7 | — | Already colocalised in Sprint 5. **Walker 2019 is a subset of devBrain**, so the two are not independent. |

**Acquired**
- Small files: EUR/ALL/AFR/AMR/Tri1/Tri2 permutation tables, isoQTL grouped permutation, EUR/ALL `.bim` files and READMEs (`pipelines/sprint5a/devbrain_fetch_small.py`).
- Nominal files: EUR, Tri1 and Tri2 (`pipelines/sprint5a/devbrain_parallel_fetch.py`).
  - Zenodo throughput is about 0.6 MB/s per connection, so parallel byte-range requests were used: 24 connections before the reboot, 2 afterwards.
  - Each file was md5-verified against Zenodo, hashed with sha256, filtered to the 249 query Ensembl IDs, and then deleted.
- A first streaming attempt (single connection plus BSD `grep -F -w -f`) was too slow: CPU-bound grep and an estimated 70+ minutes. It was abandoned; nothing from it was kept.

## A5 — 11:25–11:40 · Developmental lookup, colocalisation and timing (`pipelines/sprint5a/devbrain_timing.py`)

**Method**
- **Significance:** the gene is an eGene (q ≤ 0.05) and the variant's p is at or below the gene's threshold. A lead-variant proxy counts if it has r² ≥ 0.8 with a credible-set variant.
- **Colocalisation:** coloc.abf with the frozen Sprint-4 priors (1e-4, 1e-4, 5e-6).
  - MAF from 1000G EUR. devBrain variants were mapped to 1000G by position and allele set: 176,223 of 197,323.
  - N = 292 / 143 / 145 for EUR / Tri1 / Tri2.

**Strong colocalisation (PP.H4 ≥ 0.8)**

| Gene | Locus | Datasets (PP.H4) | Direction |
|---|---|---|---|
| CLCN2 | L8646 | EUR 0.98; Tri2 0.98 | HIGHER |
| DNPH1 | L55168 | EUR 0.92; Tri2 0.92 | LOWER |
| EIF3C | L51327 | EUR 0.86 | LOWER |
| RHEBL1 | L7009 | EUR 0.81 | HIGHER |
| CYP2D6 | L1565 | EUR, Tri1, Tri2 | HIGHER |
| NAGA | L1565 | EUR, Tri1, Tri2 | LOWER |
| WBP2NL | L1565 | EUR, Tri2 | LOWER |
| CWF19L1 | L6319 | EUR, Tri1 | HIGHER |
| **GNL3** | L51460 / L91869 | EUR 0.98; Tri1 0.98; Tri2 0.89 | LOWER |

- **NT5DC2 versus GNL3:** NT5DC2 reaches only PP.H4 0.42 in devBrain EUR, even though Walker 2019 colocalised it at 0.95 in Sprint 5. At this locus devBrain favours **GNL3** over NT5DC2. This is a gene-assignment ambiguity; it does not settle which gene is causal.

**Timing classes** (`reports/sprint5a/regulatory_timing.csv`, 274 locus × gene rows)

| Class | Rows |
|---|---|
| ADULT+DEVELOPMENTAL | 20 |
| ADULT | 81 |
| PRENATAL_ONLY | 6 |
| UNKNOWN | 167 |
| ADOLESCENT | never assigned |

- PRENATAL_ONLY covers LAP3 ×2, HMGN4, STAB1 ×2 and UQCC5, all on QTL overlap only.
- ADOLESCENT is never assigned because no open adolescent-resolved QTL data exist. BrainSeq spans prenatal to 85 years and is used as a sensitivity check only.

**Candidate genes**

| Class | Genes |
|---|---|
| ADULT+DEVELOPMENTAL (colocalisation, same direction at every stage) | RHEBL1 ↑, CLCN2 ↑, DNPH1 ↓, EIF3C ↓, NT5DC2 ↓ |
| ADULT only | DCC ↑ (adult coloc; V11 mixed), TUFM ↓, KIFC2 ↓, SH2B1 ↑, EXOC4 ↓, EXT1 |
| UNKNOWN | AKAP6, NPAS3, SLC39A8, MEF2C (lead-only locus; no significant developmental or adult QTL), KDM5B (no common locus) |

- NT5DC2 has no adult-bulk colocalisation; its adult support is V11 overlap only.
- DCC, TUFM, KIFC2, SH2B1 and EXOC4 were tested in devBrain without prenatal support.

**Uncertainty**
- Timing is based on QTL presence, never on expression level.
- "Absent in adult" means not detected.
- devBrain is fetal cortex only, and is mostly Tri1–Tri2.

## A6 — 08:47–08:55 · GTEx audit and V11

- **Searches:**
  - WebSearch "GTEx V11 release 2026 GENCODE 47";
  - GTEx API `metadata/dataset` (lists only v7, v8 and v10) and `dataset/fileList` (legacy; stops at v9);
  - GCS JSON listing of `gs://adult-gtex` (`bulk-qtl/v11`, `bulk-gex/v11`), `description.tsv` and `README_eQTL_v11.txt`.
- **Repository usage:**
  - GTEx v8: the API medians (GENCODE v26) and the eQTL Catalogue r7 GTEx datasets;
  - GTEx v10: median TPM (GENCODE v39);
  - V11: never used before this sprint.
- **V11 release:** open since **2026-01-15**, annotated with GENCODE v47. It has the same donors as V10.
  - Open files: significant pairs, eGenes/sGenes, SuSiE, apaQTL and TPM.
  - All-pairs statistics are in the **requester-pays** bucket `gs://gtex-resources`. That is a blocker: it needs a Google Cloud account with billing and egress costs.
- **Fetched:**
  - brain-tissue members of the eQTL and sQTL tars, fetched by HTTP range after walking the tar headers (26 + 26 members);
  - the SuSiE tar (183 MB);
  - the median TPM file.
- **Lookup:** 71,443 rows. Of the 21 genes that had a Sprint-4 direction:
  - 18 agree;
  - 3 are mixed (DCC, CLCN2, RECQL4);
  - **0 conflict**.
- **Details:** `reports/sprint5a/gtex_v11_audit.md`.

## A7 — 09:01–09:06 · GENCODE map

- **Sources:** GTFs for v26, v29lift37, v39, v40 and v47 from the EBI FTP (`pipelines/sprint5a/gencode_fetch.py`).
- **Output:** `data/sprint5a/gencode_id_map.csv`, 357 genes.
  - 48 have a symbol that differs across releases (for example FAM160A1 → FHIP1A and CYHR1 → ZFTRAF1).
  - 33 are absent from at least one release.
- **Candidate genes:** all 16 have stable IDs and symbols; only the version suffixes change.
- **brainSCOPE symbols:** brainSCOPE uses clone-style lncRNA symbols (for example AC007384.1) that exist only in older releases. The map resolves these through the fallback order v47 → v40 → v39 → v26 → v29lift37.

## A8 — Blockers and open questions

**Blockers**

| Blocker | Location | What the user must do | PI approval or secure compute? |
|---|---|---|---|
| brainSCOPE full nominal scQTL statistics | Not public | Ask the authors, or apply for controlled genotypes (syn51111084, syn53479857) | **Yes** |
| devBrain sQTL summary statistics | Synapse syn50897018 | Create a Synapse account and accept the terms | Possibly |
| GTEx V11 all-pairs statistics | `gs://gtex-resources`, requester-pays | Attach a Google Cloud billing account and pay egress | No |

**Open questions**
- Why NT5DC2, TUFM and SUOX are absent from brainSCOPE's matrices is unexplained. The GENCODE history rules out renaming.
- The CRISPR enhancers have no coordinates, so element-level overlap cannot be tested.

## A9 — ~10:00 · Machine reboot

- **What happened:** all processes were killed while the typed-evidence run, the devBrain Tri1 filter and the Tri2 download were in progress.
- **Verification:** `pipelines/sprint5a/verify_agentA_downloads.py` found **96/96 MATCH** (sha256 and bytes) for every logged download. The Sprint-5 re-verification again gave 163/163 MATCH.
- **Repairs:**
  - The partial Tri1 filtered file was deleted and regenerated from the full file, whose md5 matched.
  - Tri2 was re-downloaded from scratch with 2 connections, to respect the 3-worker limit.
  - The typed-evidence and timing pipelines were re-run from the beginning.
