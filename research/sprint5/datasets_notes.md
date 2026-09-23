# Sprint 5: research log for new cognition datasets, the extreme-IQ re-audit and tools discovery

Agent: research subagent. Date: 2026-09-23. All timestamps are UTC.

- No accounts were created, no logins were used, no API keys were used and no terms were accepted.
- Outputs:
  - `data/sprint5/cohort_overlap_ledger.csv`
  - `data/sprint5/extreme_iq_datasets.csv`
  - `research/sprint5/tools_review.md`
- Raw search extracts are in `data/raw/sprint5/cognition_gwas_search/` and `data/raw/sprint5/extreme_iq/`, with sha256
  values below.

---

### S1 — 21:17Z — GWAS Catalog v2, systematic cognition sweep

- **Question:** which cognition GWAS were curated for 2024–2026, and which have full summary statistics without UKB?
- **Terms:** 19 EFO IDs:
  - intelligence EFO_0004337; cognitive function EFO_0008354; cognition EFO_0003925; cognitive domain EFO_0009098;
  - verbal-numerical reasoning EFO_0008394; reasoning EFO_0004350; reaction time EFO_0008393;
  - executive function EFO_0009332 and EFO_0007046; mathematical ability EFO_0004875; processing speed EFO_0004363;
  - memory EFO_0004874, EFO_0009591, EFO_0004335 and EFO_0004333;
  - reading EFO_0005229 and EFO_0005301; cognitive decline EFO_0007710; cognitive inhibition EFO_0007969.
- **Source:** `https://www.ebi.ac.uk/gwas/rest/api/v2/studies?efo_id=…` plus `/v2/publications/{pmid}`.
- **Result:** 834 studies and 139 publications. Studies published in 2024 or later (19 publications) are almost all UK
  Biobank only:
  - Li 2024; Schoeler 2025; Karczewski 2025 (Pan-UKB); Hu 2025; Londono-Correa 2026; Dong 2026; Jung 2024; Carey 2024.
  - The rest are small or clinical (ADNI, Chinese, Japanese).
  - Perry 2025 (executive function, GenomicSEM) includes UKB, CHARGE, ALSPAC and the NIHR BioResource.
- **Accepted, UKB-free and open at any date:**
  - GenLang performance IQ (Eising 2022, GCST90104472, N=18,722, GRCh37, CC0);
  - CHIC childhood IQ (Benyamin 2014, GCST001837, N=12,441).
- **Rejected:**
  - Coleman 2019 GCST007044. The catalog labels it "extremely high intelligence", but its README says it is the Sniekers
    2017 + HiQ meta-analysis, so it contains UKB.
- **Data acquired (small metadata only):**
  - `gwascatalog_v2_cognition_studies_2026-09-23.csv` (sha256 cce5d8a3…6517);
  - `gwascatalog_v2_cognition_raw_2026-09-23.json.gz` (a07a5e89…328a);
  - GCST90104472 metadata YAML and README;
  - GCST001837 metadata YAML.
  - The full summary-statistic files (478 MB and 77 MB) were **not** downloaded. Their sizes and md5 values are recorded in
    the ledger.
- **Conclusion:** no new (2024–2026), UKB-free, open, >10k general-cognition GWAS is curated in the GWAS Catalog.
- **Uncertainty:** the catalog lags publication by months, and its cohort field is often empty for older studies.
- **Next search triggered:** OpenGWAS metadata and literature searches.

### S2 — 21:22Z — OpenGWAS public metadata (no JWT)

- **Question:** are there cognition datasets on OpenGWAS since 2022?
- **Source:** `https://opengwas.io/data/gwasinfo/gwasinfo.json`.
  - Public, 9,072,142 bytes, Last-Modified 2026-09-23 12:35 GMT.
  - Stored at `data/interim/sprint5/cognition_gwas_search/opengwas_gwasinfo.json` (gitignored; sha256 d207f63f…e21e).
  - `api.opengwas.io/api/gwasinfo` returned **401 (JWT required)**, so it was not used.
- **Result:**
  - The newest cognition entries are Howe 2022 ieu-b-4837 and ieu-b-4838 (within-family).
  - There are no 2023–2026 cognition datasets.
  - Subset saved: `opengwas_gwasinfo_cognition_subset_2026-09-23.csv` (01c42fee…692b).
- **Conclusion:** OpenGWAS adds nothing new. Downloading data from it still needs a JWT (blocked).

### S3 — 21:20–21:25Z — Tan et al. family-GWAS (within-family consortium)

- **Sources:**
  - medRxiv 10.1101/2024.10.01.24314703;
  - EuropePMC full text PMC12633112 (PMID 41282763);
  - SSGAC portal.
- **Result:**
  - 17 cohorts (16 European and China Kadoorie).
  - Cognitive performance: effective N 12,361 for direct effects and 26,345 for population effects.
  - DGE–population rg is 0.543 (SE 0.036).
  - The paper used UK Biobank application 11425. The per-phenotype cohort list is in Supplementary Table 1 and was not
    retrieved.
- **Access:**
  - The data availability statement says "SSGAC data portal".
  - thessgac.com shows only a login/registration page, so it is **blocked (registration)**.
- **Conclusion:** PARTIAL independence (UKB probably included). Not usable without registration.

### S4 — 21:23–21:25Z — EuropePMC literature sweeps

These queries are saved in the scratchpad only.

- **Query 1:** titles containing (GWAS OR genome-wide) and (intelligence, cognitive, cognition, IQ, school, academic,
  reasoning, processing speed, executive function), 2024–2026. 53 hits.
- **Query 2:** conscription + genome-wide + intelligence. 1 hit: Capusan 2025 JAMA Psychiatry. That paper uses Swedish
  conscription IQ phenotypically; its MR uses Lee 2018 CP; it has no new GWAS.
- **Query 3:** cognitive development or childhood intelligence + GWAS, 2023–2026. 61 hits, mostly ABCD and PRS; no new
  primary cognition GWAS with open summary statistics.
- **Query 4:** within-family / direct effects + cognition. Malawsky 2024 preprint (common and rare variants across
  development) and van den Berg 2025 (UKB imputed fluid intelligence).
- **Query 5:** biobank names (FinnGen, MoBa, HUNT, Lifelines, Estonian, MVP, All of Us, GS, BBJ, Kadoorie, Taiwan) +
  cognition. Only Kvalvik 2026 (MoBa educational milestones, which is an EA phenotype) and a Generation Scotland reading
  resource (N=1,595).
- **Accepted as ledger rows:**
  - Shinoda 2025 (Tohoku, MMSE, N=2,571);
  - Kang 2025 (harmonised cognition; FHS is in COGENT);
  - Kvalvik 2026;
  - MoBa Nature 2026 (PMID 42618792). Its summary-statistic release was not verified because the Nature page redirected to
    a login.
- **Rejected:** Mendelian randomisation and PRS-only papers, dementia and decline papers, and non-human studies.

### S5 — 21:28Z — Zenodo, CNCR/CTG and Edinburgh DataShare

- **Zenodo API.** Five queries, 25 records per page (anonymous limit). Relevant hits:
  - 10.5281/zenodo.11066096 (G&C, already used);
  - 10.5281/zenodo.21167984 (van den Berg 2026, imputed fluid intelligence; UKB);
  - 10.5281/zenodo.21938499 (CNV-GWAS autism / cognitive ability, 2026-08; cohorts not checked);
  - 10.5281/zenodo.7276971 (Bryois 2022 brain cell-type eQTL; used in the tools review).
  - No new UKB-free cognition GWAS.
- **CNCR/CTG summary statistics page** (https://cncr.nl/research/summary_statistics/): the 2024–2026 releases cover
  Alzheimer's (Uffelmann 2026), BMI, functional connectivity, alcohol and neuroimaging. None are cognition. Licence is
  CC BY-NC-SA 4.0.
- **Edinburgh DataShare** (DSpace REST search "GWAS cognitive", 19 items): no cognition GWAS items; the Davies summary
  statistics are hosted on CCACE instead.
- **Figshare:** not searched (time). This is remaining uncertainty.

### S6 — 21:30Z — FinnGen, MVP, All of Us

- **FinnGen:** the public manifests for R12 (2,470 lines) and R13 (2,755 lines; R14 returns 404) contain no cognitive-ability
  endpoint. The only related endpoints are dementia and MEMLOSS.
- **MVP:** the only cognition GWAS found is the CSP#572 SMI cohort (about 6.5k). Summary statistics are controlled.
- **All of Us:** no cognitive-test GWAS found.
- **Conclusion:** there is no large UKB-free general-cognition GWAS in these biobanks.

### S7 — 21:26–21:28Z — Overlap verification against Davies 2018

- **Sources:**
  - EuropePMC full text of Davies 2018 (PMC5974083);
  - Trampush 2017 COGENT (PMC5322272), Table 1 with 24 cohorts.
- **Result:**
  - The Davies 2018 main text names ELSA, Understanding Society, Generation Scotland and UKB.
  - The COGENT cohort list does **not** include ALSPAC, TEDS, NTR, BATS or Raine.
  - So GenLang PIQ is provisionally independent. The remaining risk is CLDRC versus IBG (both Colorado).
- **Uncertainty:** the full CHARGE cohort list is in the Davies Supplementary Data, which was not parsed.

### S8 — 21:29–21:31Z — Extreme and high-IQ re-audit

- **Sources:**
  - GWAS Catalog GCST005626 (Zabaneh) and GCST007044 (Coleman);
  - EuropePMC full text PMC5987166 (Zabaneh 2018);
  - abstracts for Spain 2016 and Coleman 2019;
  - NCBI E-utilities (db=gap) for "high intelligence", "gifted" and "Talent Identification";
  - the EGA metadata API (its search parameter was ignored and it returned the unfiltered catalogue, so this search was
    **inconclusive**);
  - EuropePMC title searches 2017–2026 (7 hits; nothing after 2019).
- **Result:**
  - The Zabaneh summary statistics are open (GRCh37, 132 MB).
  - Controls are Health and Retirement Study genotypes from dbGaP, which puts them inside Davies (CHARGE).
  - Case genotypes are not deposited anywhere I could find.
  - Coleman GCST007044 is mislabelled (it is the Sniekers + HiQ meta).
  - Spain 2016 has no summary statistics.
  - SMPY: no genetic resource found.
- **Data acquired:**
  - `data/raw/sprint5/extreme_iq/Coleman_29520040_README.txt`;
  - `data/raw/sprint5/extreme_iq/GCST005626_README.txt` and `GCST005626_meta.yaml`.
- **Conclusion:** no availability change since 2023. Zabaneh remains sensitivity-only.

### S9 — 21:31–21:38Z — Tools discovery

- **Sources:**
  - GitHub API (licence and last push) for susieR, ctwas, RSparsePro_LD, colocboost, FLAMES, ma-focus, chrombpnet, borzoi,
    fine-mapping-inf, CARMA, TGFM and polyfun;
  - the CRAN colocboost DESCRIPTION (MIT, 1.0.10, 2026-09-09);
  - the Zenodo record for Bryois 2022;
  - the public S3 listing of `broad-alkesgroup-ukbb-ld`;
  - web searches for ColocBoost, FLAMES, RSparsePro and cTWAS.
- **Conclusion:** see `tools_review.md`. The top three are:
  1. open brain single-cell eQTL with coloc;
  2. AlphaGenome, once a key is available;
  3. LD-robust re-fine-mapping (PolyFun with UKB LD, or RSparsePro).

## Remaining uncertainty and next searches

1. **GenLang PIQ independence.** Parse the Davies 2018 Supplementary Data cohort list and check whether CLDRC overlaps IBG.
   If it is clean, download GCST90104472 (478 MB, into `data/interim`) as a second UKB-free replication lineage.
   - The phenotype is nonverbal IQ in ages 5–26, and the sample includes dyslexia-ascertained cohorts.
2. **CHIC cohort list.** The full text was not retrievable (the QIMR PDF link returns HTML). It likely overlaps GenLang, so
   do not use both as independent lineages.
3. **Tan 2025 Supplementary Table 1** (cohorts per phenotype) and SSGAC access both need the user to register.
4. **Figshare and the bioRxiv/medRxiv full-text preprint sweep** were not done.
5. **MoBa Nature 2026 summary-statistic availability** is unverified.
