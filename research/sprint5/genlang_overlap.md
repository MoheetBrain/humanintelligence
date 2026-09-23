# GenLang performance IQ and CHIC childhood IQ: cohort overlap with Davies et al. 2018

Date: 2026-09-23. Machine-readable version: `data/sprint5/genlang_overlap.json`.

**Rule.** A dataset counts as an independent lineage only if its cohort list contains none of UK Biobank, HRS, 23andMe or any Davies-2018 cohort.

## Verdicts

| Pair | Verdict | Overlapping cohorts |
|---|---|---|
| GenLang PIQ (GCST90104472) vs Davies 2018 | **PARTIAL_OVERLAP**, so not an independent lineage | **BATS** confirmed (1,414 of 18,722 = 7.6%). CLDRC vs IBG (Colorado) is ambiguous. |
| CHIC 2014 (GCST001837) vs Davies 2018 | **PARTIAL_OVERLAP**, so not an independent lineage | **LBC1921, LBC1936, QIMR/BATS** confirmed (3,163 of 12,441 discovery = 25.4%). UMN in the replication set is probably MCTFR, but replication is not in the summary statistics. |
| GenLang PIQ vs CHIC | **OVERLAPPING** | **ALSPAC, TEDS, BATS/QIMR, Raine**: 61.7% of GenLang PIQ and 88.7% of CHIC discovery. NTR is shared too, but it is CHIC replication only. |

Neither GenLang PIQ nor CHIC contains UK Biobank, HRS or 23andMe. The overlap comes only through BATS, which is in the CHARGE part of Davies, and through LBC1921 and LBC1936 for CHIC.

This corrects the project's earlier provisional call. `data/sprint5/cohort_overlap_ledger.csv` marks GenLang PIQ `independent_of_davies2018 = Y` and says it is "Not in Davies 2018 COGENT table". That check covered only COGENT. BATS is a CHARGE cohort in Davies. The ledger row should be updated. This report does not edit it.

## 1. GenLang performance IQ cohorts (Eising 2022, Dataset S1)

Source: Eising et al. PNAS 2022, PMID 35998220, PMC9436320. The source is Dataset S1 (`pnas.2202764119.sd01.xlsx`, Performance IQ columns), cross-checked with the Performance IQ column of Dataset S3.

| Cohort | Design | Country | Age (y) | PIQ test | N |
|---|---|---|---|---|---|
| ALSPAC | Population birth cohort | UK | 7, 8 or 13 | WISC | 5,448 |
| ASTON | Case/control | UK | 5–18 | BAS | 170 |
| BATS | Family (twins), QIMR | Australia | 11–26 | MAB | 1,414 |
| BCBL | Population | Spain | 6–16 | KBIT | 1,236 |
| CLDRC | Case/control (RD/ADHD twins) | USA (Colorado) | 8–18 | WISC | 717 |
| ELVS | Population | Australia | 5, 7 or 11 | "WAIS" (as printed) | 480 |
| Iowa | Population | USA | 6–10 | WISC | 408 |
| NTR | Family (twins) | Netherlands | 9 | WISC and WAIS | 1,086 |
| Raine Study | Population | Australia | 9–12 | Raven CPM | 1,189 |
| SLIC | Case/control | UK | 8–16 | WISC | 480 |
| SYS (Saguenay) | Family | Canada | 11–18 | WISC III | 1,011 |
| TEDS | Family (twins) | UK | 7 or 12 | WISC | 3,492 |
| Toronto | Family | Canada | 6–16 | WISC III/IV | 614 |
| UK Dyslexia | Case/control | UK | 6–18 | BAS | 874 |
| York | Family (dyslexia risk) | UK | 7–10 | other | 103 |
| **Total (15 cohorts)** | | | **5–26** | | **18,722** (sum verified) |

- **Not in PIQ.** PNC, ABCD, PING, GRaD, Neurodys, Fiola and Generation R contribute only to other GenLang traits. PNC is also in Davies (COGENT), but it has no PIQ data.
- **Ascertainment.** Four PIQ cohorts are case/control for dyslexia, language impairment or learning disability: ASTON, CLDRC, SLIC and UK Dyslexia. Together they have N = 2,241 (12.0%).

## 2. Davies 2018 cohort list

Source: Davies et al. Nat Commun 2018, PMID 29844566, PMC5974083. The list comes from Supplementary Data 18 (`41467_2018_4362_MOESM21_ESM.xlsx`). It has 66 rows summing to 300,485, against the paper's stated 300,486, so it is effectively complete. CHARGE and COGENT assignments come from the sections of Supplementary Note 1.

- **CHARGE.** 3C-Dijon, AgeCoDe (Basel, DietBB), AGES, Airwave, ARIC, ASPS, ASPS-Fam, BASE-II, **BATS**, Betula, CHS, CROATIA-Korčula, ELSA, EPOZ, ERF, FHS, FinnTwin, Generation Scotland, GENOA, HARMONY, HCS, **HRS**, **LBC1921**, **LBC1936**, LIFE-Adult, OATS, ORCADES, PROSPER (IE, NL, SC), ROSMAP 1/2, RS I/II/III, SATSA+GENDER, Sydney MAS, Understanding Society, VETSA, YFS.
- **COGENT.** ACPRC, ADNI, ASPIS, CAMH, DCC, DNS, DUBLIN, GENADA, HBCS, **IBG**, LOAD, LOGOS, LLFS, **MCTFR**, Munich, GCAP, NCNG, **PNC**, TOP, UCLA (CNP), ZHH.
- **UK Biobank.** Four sub-samples: Assessment Centre, T2, MRI and Web-based.

**Childhood and adolescent cohorts in Davies:**

| Cohort | Consortium | Ages (y) | N |
|---|---|---|---|
| BATS | CHARGE | 16–22.3 | 2,253 |
| IBG (Colorado LTS + CTS) | COGENT | 12–19 | 299 |
| PNC | COGENT | 8–21 | 4,470 |
| ZHH | COGENT | 8–78 | 176 |
| MCTFR | COGENT | 17–65 | 5,446 |

**Absent from Davies:** ALSPAC, TEDS, NTR/Netherlands Twin Register, Raine, Generation R, Saguenay, Toronto, Iowa, ELVS, BCBL, and CLDRC by name.

## 3. CHIC (Benyamin 2014) cohorts

Source: Benyamin et al. Mol Psychiatry 2014, PMID 23358156, PMC3935975. The source is the Methods section "Participants" and Table 1. The full text came via NCBI efetch. The Supplementary Note is not open access.

| Stage | Cohort | Country | N | IQ measure | Mean age (y) |
|---|---|---|---|---|---|
| Discovery | ALSPAC | UK | 5,517 | WISC-III | 9 |
| Discovery | LBC1921 | UK | 464 | Moray House Test No. 12 | 11 |
| Discovery | LBC1936 | UK | 947 | Moray House Test No. 12 | 11 |
| Discovery | QIMR (Brisbane Adolescent Twin Study) | Australia | 1,752 | MAB full-scale IQ | 16 |
| Discovery | Raine | Australia | 936 | g score | 10 |
| Discovery | TEDS | UK | 2,825 | g score | 12 |
| Replication | Generation R | Netherlands | 1,442 | SON-R 2.5–7 | 6 |
| Replication | NTR | Netherlands | 739 | RAKIT, WISC-R, WISC-R-III, WAIS-III | 13 |
| Replication | UMN (Minnesota) | USA | 3,367 | WISC-R, WAIS-R | 14 |

- **Sample sizes.** Discovery is 12,441 and replication is 5,548; both sums were verified.
- **What the summary statistics contain.** The GWAS Catalog gives GCST001837 an initial sample of 12,441 and a separate replication sample of 5,548. The summary statistics therefore cover the **discovery cohorts only**.

## 4. Cohort-by-cohort intersections

### GenLang PIQ vs Davies 2018

| Cohort | Status | GenLang source | Davies source | Note |
|---|---|---|---|---|
| BATS | **CONFIRMED** | S1 row BATS: family-based, Australia, 11–26 y, MAB, N 1,414 | SD18 row BATS (N 2,253, 16–22.3 y); SI Note 1 CHARGE "BATS."; SI Note 2 "Brisbane Adolescent Twins Study (BATS)", QIMR Berghofer (SI p.40) | Same QIMR twin cohort and the same MAB test. Individual overlap is highly likely. |
| CLDRC vs IBG | **AMBIGUOUS** | S1 row CLDRC (N 717). Gialluisi 2014 (PMC4165772): twins from 27 Colorado school districts selected on RD/ADHD, Illumina OmniExpress | SI Note 2 "IBG": Colorado Longitudinal Twin Sample and Colorado Twin Sample, population registries, Affymetrix 6.0, N 299, ages 12–19 | Both are Colorado twin samples at the IBG. Recruitment frames and arrays differ, so they are probably different people, but overlap is not excluded. At most 299 people could be shared. |
| PNC | Not relevant to PIQ | S1: word reading only | SD18 PNC (COGENT) | Relevant only if other GenLang traits are used. |
| All other PIQ cohorts | Absent from Davies | S1 | SD18 (complete list) | |

### CHIC vs Davies 2018

| Cohort | Status | CHIC stage | Source |
|---|---|---|---|
| LBC1921 | **CONFIRMED** | Discovery | CHIC Table 1 "LBC21-Lothians"; Davies SD18 LBC1921 (N 459). CHIC uses the age-11 Moray House score of the same people. |
| LBC1936 | **CONFIRMED** | Discovery | CHIC Table 1 "LBC36-Lothians"; Davies SD18 LBC1936 (N 934) |
| QIMR / BATS | **CONFIRMED** | Discovery | CHIC Methods: "the Brisbane Adolescent Twin Study, Queensland Institute of Medical Research (QIMR; N = 1752)"; Davies SD18 BATS |
| UMN vs MCTFR | **PROBABLE** | Replication (not in summary statistics) | CHIC Table 1 "UMN-Minnesota", WISC-R/WAIS-R, Illumina 660W-Quad. Davies SI MCTFR: University of Minnesota twin and adoption families, abbreviated WISC-R/WAIS-R FSIQ. The names differ, but it is the same institution, instrument and age band. |

### GenLang PIQ vs CHIC

| Cohort | GenLang PIQ N | CHIC N (stage) | Status |
|---|---|---|---|
| ALSPAC | 5,448 | 5,517 (discovery) | CONFIRMED |
| TEDS | 3,492 | 2,825 (discovery) | CONFIRMED |
| BATS / QIMR | 1,414 | 1,752 (discovery) | CONFIRMED; the name differs ("QIMR" in CHIC) |
| Raine | 1,189 | 936 (discovery) | CONFIRMED |
| NTR | 1,086 | 739 (replication only) | CONFIRMED by name. CHIC uses both "Netherlands Twin Registry" and "Netherlands Twin Register". |

The GenLang summary statistics and the CHIC summary statistics are not independent of each other. Individual-level overlap within each shared cohort is probably large but not total, because the waves and QC differ.

## 5. Summary-statistics facts

### GenLang PIQ (GCST90104472)

- **Files.** `GCST90104472_buildGRCh37.tsv` (md5 `d59615f32e99632c7316b15a87edd574`, 7,872,714 SNPs).
- **Columns.** `variant_id p_value chromosome base_pair_location effect_allele other_allele effect_allele_frequency beta standard_error N`
- **Build: GRCh37.** The metadata says so, and 4 of 4 tested rsIDs match Ensembl GRCh37 positions exactly.
- **Harmonised copy.** `harmonised/GCST90104472.h.tsv.gz` is on GRCh38, harmonised against Ensembl release 95, with 99.81% of sites harmonised (run on 2024-09-15).
- **Sign convention.** `beta` is per copy of `effect_allele` on the per-cohort z-scored PIQ, so **positive beta means higher PIQ**.
  - The paper and README state no reversal.
  - Empirical check: 1-Mb-clumped Davies GWS leads (Supplementary Data 1, n=145) were aligned to Allele1 on the Davies Z. Of 121 matched non-palindromic SNPs, 95 were concordant (78.5%, binomial P = 1e-10). Of the 26 with P < 0.05, 25 were concordant.
- **Ancestry and age.** European only (N = 18,722). Recruited in the UK, USA, Canada, Netherlands, Australia and Spain. Ages 5–26.
- **Phenotype.** Nonverbal subtests of general intelligence batteries, z-scored within each cohort.
- **Analysis.** A linear model adjusted for family structure, age, age², sex and PCs, followed by a METAL fixed-effects meta-analysis with genomic control.

### CHIC (GCST001837)

- **File and columns.** `CHIC_Summary_Benyamin2014 2.txt` has 1,380,158 rows. Columns: `SNP CHR BP A1 A2 FREQ_A1 EFFECT_A1 SE P`.
- **Sign convention.** Positive `EFFECT_A1` means higher IQ. Empirical check: 31 of 34 Davies leads were concordant (91%, P = 4e-7), inflated by the LBC and BATS overlap.
- **Build: not GRCh37.**
  - The `BP` values match **NCBI35/hg17**: 7 of 7 tested rsIDs match UCSC hg17 snp125 exactly. Only 1 of 7 matches hg18, on chr16 where hg17 and hg18 coincide, and 0 of 7 match GRCh37.
  - The paper says imputation used HapMap r22 Build 36, but the deposited coordinates are hg17.
  - Join on rsID, or lift over from hg17. The GWAS Catalog `genome_assembly` field is empty.

## Limitations

- Membership is judged by cohort name. Individual-level overlap needs genotypes and cannot be measured here.
- The CLDRC vs IBG relationship cannot be resolved from public text.
- The CHIC Supplementary Note is not open access.
- Davies SD18 sums to 300,485, one fewer than the paper's 300,486.

## Sources

- **Eising 2022.** Full text: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9436320/fullTextXML. Supplement: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9436320/supplementaryFiles
- **Davies 2018.** Full text: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5974083/fullTextXML. Supplement: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5974083/supplementaryFiles
- **Benyamin 2014.** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=3935975&rettype=xml
- **Gialluisi 2014 (CLDRC).** https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4165772/fullTextXML
- **GWAS Catalog, GenLang PIQ.** https://www.ebi.ac.uk/gwas/rest/api/studies/GCST90104472 and http://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90104001-GCST90105000/GCST90104472/
- **GWAS Catalog, CHIC.** https://www.ebi.ac.uk/gwas/rest/api/studies/GCST001837 and http://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST001001-GCST002000/GCST001837/
