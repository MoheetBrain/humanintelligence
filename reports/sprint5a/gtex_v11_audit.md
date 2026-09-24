# GTEx audit — which versions the project used, and what GTEx V11 adds

*Sprint 5A, agent A — 2026-09-24 (UTC). Branch `sprint-5a/open-data-exhaustion`.*

## Summary

- **Versions used before this sprint:** GTEx **v8** (via the eQTL Catalogue and the GTEx API) and GTEx **v10** (median TPM only). GTEx V11 had never been used.
- **V11 status:** V11 is openly released.
  - Release date: 2026-01-15.
  - Annotation: GENCODE v47.
  - Donors and samples: the same as v10.
- **What was fetched:** the 13 brain tissues' open eQTL and sQTL files, plus the V11 eQTL SuSiE archive.
- **What the lookup found:** 18 genes that already had a Sprint-4 direction agree in V11, 3 are tissue-mixed, and **none conflict**.
  - This is a lookup, not colocalisation.
  - The mixed genes are DCC, CLCN2 and RECQL4.
  - V11 is not an independent replication, because it is a superset of the v8 donors.

## 1. GTEx versions actually used in the repository (before Sprint 5A)

| Where | GTEx release | Annotation | What it was used for | Evidence (file) |
|---|---|---|---|---|
| Sprints 1–2 (alphacognition), 2026-09-17 | **v8** (GTEx Portal API v2, dataset `gtex_v8`) | GENCODE **v26** (API `gencodeVersion=v26`) | Median TPM per tissue | `pipelines/alphacognition/fetch_expression.py`; `data/raw/gtex/2026-09-17/*.json` (1,674 records, all `"datasetId": "gtex_v8"`) |
| Gene tournament / Sprint 3 (`brain_expr_gtex`, developmental classification) | **v10** median TPM (`GTEx_Analysis_v10_RNASeQCv2.4.2_gene_median_tpm.gct.gz`) | GENCODE **v39** | Adult-brain expression covariate | `data/raw/brain_expression/PROVENANCE.json` (GCS `adult-gtex/bulk-gex/v10/...`) |
| Same record (downloaded, kept for comparison) | **v8** median TPM (`GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz`) | GENCODE **v26** | Not used in the scores | `data/raw/brain_expression/PROVENANCE.json` |
| Sprint 3 V2G (Open Targets) and Sprint 4 Gate-C colocalisation | **v8 donors**, reprocessed by the **eQTL Catalogue r7** (13 GTEx brain `ge` datasets + CommonMind + ROSMAP + Braineac2) | Catalogue's own uniform re-annotation (believed to be GENCODE v39 / Ensembl 105; **not re-verified in this audit**; gene IDs are used unversioned) | Adult bulk eQTL colocalisation and direction | `data/raw/sprint4/eqtl_catalogue/PROVENANCE.json` (release r7; r8 beta = GTEx v10, parquet-only, explicitly *not used*) |

**Conclusion:**
- **eQTLs:** every project eQTL inference so far rests on **GTEx v8 donors**, through eQTL Catalogue r7.
- **Expression:** expression covariates use **GTEx v10** TPM.
- **V11:** never used before this sprint.

## 2. GTEx V11 — release status and what is open

Checked 2026-09-24 against the public GCS bucket `gs://adult-gtex` (JSON listing API), the V11 `description.tsv` files and `README_eQTL_v11.txt`.

- **Release:** objects were created on **2026-01-15**, and the per-tissue counts files were added on 2026-05-26.
  - The GTEx portal's `metadata/dataset` API still lists only v7, v8 and v10.
- **What V11 is:** V10 re-quantified with **GENCODE v47**. It adds **no new donors or samples** compared with V10.
  - V10 has 943 eQTL subjects; v8 had 838.

| V11 product | Open? | Size | Notes |
|---|---|---|---|
| Gene TPM, reads, median TPM (`bulk-gex/v11/rna-seq/`) | **OPEN** | 10 MB (median TPM) to 22 GB | median TPM file downloaded (10.1 MB) |
| `GTEx_Analysis_v11_eQTL.tar` (per tissue `*.eGenes.txt.gz` + `*.eQTLs.signif_pairs.parquet`) | **OPEN** | 3.29 GB (all tissues) | **brain members only** fetched by HTTP byte range (26 members) |
| `GTEx_Analysis_v11_sQTL.tar` (LeafCutter sGenes + signif pairs) | **OPEN** | 2.57 GB | brain members only (26) |
| `GTEx_Analysis_v11_eQTL_SuSiE.tar` (fine-mapping) | **OPEN** | 183 MB | downloaded whole |
| apaQTL (new data type), expression/phenotype matrices, covariates | **OPEN** | 21 MB – 19 GB | not needed; not fetched |
| **All-pairs (nominal) eQTL / sQTL / apaQTL** | **Requester-pays** GCS bucket `gs://gtex-resources` | ~hundreds of GB | **BLOCKER:** the user needs a Google Cloud account with billing enabled and pays egress. No PI approval is needed. Not done by the agent. |
| Individual-level genotypes and expression | Controlled (dbGaP phs000424 / AnVIL) | — | Needs PI / dbGaP approval |

**Consequence:** V11 cannot be colocalised with open data. Only significant pairs and SuSiE credible sets are open, and the all-pairs files are requester-pays.

## 3. V11 lookup of the cognition credible-set variants (GRCh38)

**Method**
- Script: `pipelines/sprint5a/gtex_v11_lookup.py`. Outputs:
  - `reports/sprint5a/gtex_v11_lookup.csv` (eQTL rows only, slimmed to stay under 5 MiB)
  - `reports/sprint5a/gtex_v11_lookup_full.parquet` (eQTL and sQTL rows, all columns)
  - `reports/sprint5a/gtex_v11_gene_direction.csv`
  - `reports/sprint5a/gtex_v11_susie_query_overlap.csv`
- Input variants: 1,914 cognition query rows. These are Davies-2018 SuSiE credible sets, Open Targets credible sets and locus leads, covering 159 loci; 36 of them are Gate-C loci.
- Matching: exact hg38 position plus allele matching.
- Direction:
  - The slope is per ALT allele, as documented in the GTEx README.
  - It is aligned to the cognition-increasing allele: the Davies effect allele if z > 0, otherwise the other allele.
  - Palindromic variants are excluded from the direction calls.
- Per gene: one call per tissue (the majority over credible-set variants), then one gene-level call:
  - HIGHER or LOWER if all tissues agree;
  - MIXED otherwise.

**Results**
- 71,443 lookup rows: 33,247 eQTL and 38,196 sQTL.
  - 68,465 of them are at the Gate-C loci: 32 of the 36 loci and 202 genes.
- V11 eQTL gene-level directions versus Sprint 4 (`reports/sprint4/directionality_resolution.csv`):
  - **18 genes AGREE, 0 CONFLICT, 3 are V11-MIXED** (DCC, CLCN2, RECQL4).
  - 501 locus×gene pairs had no Sprint-4 direction; V11 adds rows-level evidence only for these.
  - ZFTRAF1 has a Sprint-4 rows-only direction, but none of its query variants is a significant V11 eQTL.

**Candidate genes (V11 eQTL; direction is for the cognition-increasing allele)**

| Locus | Gene | V11 brain tissues significant | V11 direction | Query variant in V11 SuSiE CS | Sprint-4 label | V11 vs Sprint 4 |
|---|---|---|---|---|---|---|
| L7009 | RHEBL1 | 11 | HIGHER | many tissues | DIRECTION_RESOLVED (HIGHER) | agrees |
| L51327 | TUFM | 11 | LOWER | many tissues | rows-only LOWER | agrees |
| L51327 | EIF3C | 9 | LOWER | hypothalamus | UNRESOLVED (LOWER majority) | agrees |
| L51327 | SH2B1 | 3 | HIGHER | cerebellum, cerebellar hemisphere, hypothalamus | no Sprint-4 direction | V11 adds HIGHER |
| L55168 | DNPH1 | 6 | LOWER | — | UNRESOLVED (LOWER majority) | agrees |
| L65265 | KIFC2 | 4 | LOWER | BA9, hypothalamus | UNRESOLVED (LOWER majority) | agrees |
| L51460 / L91869 | NT5DC2 | 5 | LOWER | hypothalamus | no Sprint-4 direction | V11 adds LOWER |
| L1630 | DCC | 3 | MIXED (cerebellum and cerebellar hemisphere HIGHER; BA9 LOWER) | — | rows-only HIGHER (from strong GTEx-cerebellum coloc) | **MIXED**; agrees in cerebellum, the colocalising tissue |
| L8646 | CLCN2 | 4 | MIXED (cerebellar tissues LOWER; hippocampus HIGHER) | cerebellar hemisphere, hippocampus | UNRESOLVED (HIGHER majority) | **MIXED** |
| L2131 | EXT1 | 3 | MIXED | cerebellum | no direction | — |
| L60412 | EXOC4 | 8 | MIXED | — | no direction | — |

**Not significant for any query variant in any V11 brain tissue:** AKAP6, NPAS3, SLC39A8 and MEF2C.
- MEF2C is not a Gate-C locus gene.
- KDM5B has no common cognition locus.

**Does V11 change any Sprint-4 gene-level direction?** No gene flips sign.
- DCC, CLCN2 and RECQL4 become tissue-heterogeneous in V11.
- None of those three had a robust Sprint-4 direction: DCC is rows-only; CLCN2 and RECQL4 are UNRESOLVED.

Under the frozen protocol (`research/sprint5a/protocol_rules.json` → `new_evidence_mapping.gtex_v11`), V11 joins the **bulk QTL class**. Because it has the same GTEx donors, it is **not a new independence unit**.

## 4. GENCODE mapping

Output: `data/sprint5a/gencode_id_map.csv`, built by `pipelines/sprint5a/gencode_id_map.py` from the GENCODE GTFs (EBI FTP).

It covers every candidate gene ID used across sources:
- Sprint-4 Gate-C query genes;
- the Sprint-5A candidate list;
- brainSCOPE QTL genes, which are identified by symbol only;
- V11 hits at the Gate-C loci.

For each gene it gives, per release, the versioned ID and symbol for v26 (GTEx v8), v29lift37 (devBrain), v39 (GTEx v10 and eQTL Catalogue r7), v40 and v47 (GTEx V11). It also records:
- symbol and version changes across releases;
- absence from any release;
- whether brainSCOPE uses the same symbol.

Findings:
- All 16 candidate genes have a stable symbol and Ensembl ID from v26 through v47. Only the version suffixes change.
- Renamed genes at Gate-C loci that affect matching by symbol include:
  - FAM160A1 → FHIP1A;
  - FAM109B → PHETA2;
  - CYHR1 → ZFTRAF1;
  - TMEM110 → STIMATE;
  - SMIM4 → UQCC5;
  - SEPT3 → SEPTIN3;
  - HIST1H2BN → H2BC15;
  - ZBED9 → SCAND3;
  - LINC00634 → SMIM45.
- NT5DC2 and TUFM are absent from brainSCOPE's pseudobulk matrices, and this is **not** explained by renaming (same symbol in every release). The cause remains unexplained. SUOX (also absent in Sprint 5) is in the same position.

## 5. Uncertainty

- **Lookup, not colocalisation.** A significant V11 query variant is not evidence of a shared causal variant.
- **The same donors carry through all GTEx sources.** GTEx V11 = V10 ⊃ v8, so V11 agreement with the Sprint-4 GTEx rows is expected and is not replication. For CommonMind and ROSMAP, V11 is independent of those donors, but those cohorts were already in Sprint 4.
- **Direction calls are majorities over credible-set variants.** Credible-set variants in LD are not independent votes.
