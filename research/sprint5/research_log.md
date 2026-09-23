# Sprint 5 research log (living)

This is the orchestrator's log. Each entry records:

- the time (UTC);
- the question;
- the search terms or queries;
- the sources inspected;
- whether each source was accepted or rejected, and why;
- the data acquired;
- the conclusion;
- the remaining uncertainty;
- the next search the result triggered.

Subagents kept their own logs, and their entries are merged by reference:

- `brainscope_notes.md`
- `math_notes.md`
- `rare_coding_notes.md`
- `alphagenome_notes.md`
- `datasets_notes.md`

---

### R01 · 2026-09-23T20:55Z · Gate A availability

- **Question.** Do the Howe 2022 within-sibship files (ieu-b-4837/4838) exist locally, or is `OPENGWAS_JWT` set?
- **Queries.** `ls data/interim/sprint4/opengwas/`; `echo ${OPENGWAS_JWT:+yes}`.
- **Sources.** The local filesystem and the environment.
- **Accepted or rejected.** Not applicable.
- **Acquired.** Nothing.
- **Conclusion.** The directory is absent and the JWT is unset, so Gate A stays **NOT_TESTABLE**. No account was created.
- **Remaining uncertainty.** None about access.
- **Next.** Continue every other stage. Record the blocker in the final report.

### R02 · 2026-09-23T21:03Z · A GRCh38 coordinate spine for every per-variant layer

- **Question.** brainSCOPE, AlphaGenome and Open Targets use GRCh38, but the Sprint-4 SuSiE sets are GRCh37 rsIDs. How do we put them on one coordinate system?
- **Query.** Ensembl REST `POST /variation/homo_sapiens` with 1,573 rsIDs, in batches of 200.
- **Sources.** Ensembl REST (accepted: canonical rsID→GRCh38 mapping, with alleles).
- **Acquired.** `data/sprint5/query_variants_cognition.csv`: 1,915 rows. 1,572 of 1,573 rsIDs mapped; one had no primary-assembly mapping and was kept and flagged.
- **Conclusion.** One query list now serves every layer.
- **Remaining uncertainty.** Multi-allelic records create several candidate variant IDs per rsID.
- **Next.** Open Targets variant-level pull.

### R03 · 2026-09-23T21:05Z · What is the *current* Open Targets release?

- **Question.** Which release did Sprint 3/4 use, and is there a newer one?
- **Query.** GraphQL `meta { apiVersion dataVersion dataPrefix }`.
- **Sources.** `api.platform.opentargets.org` (accepted: the primary source). Sprint-3 provenance `data/gene_tournament/opentargets_provenance.json`.
- **Acquired.** The live API reports release **26.06** (API 26.6.3, prefix platform2606). Sprint 3 used 26.06 as well, retrieved 2026-09-22.
- **Conclusion.** No newer release exists on 2026-09-23. The "refresh" therefore cannot show release-driven changes. Any CHANGED_ASSIGNMENT flag reflects *broader credible-set coverage*: every cognition credible set containing any locus credible variant, rather than the lead-matched sets Sprint 3 used.
- **What Sprint 3 had not pulled, and was now fetched:**
  - enhancer-to-gene links (ENCODE-rE2G);
  - variantEffect functional predictions;
  - transcript consequences;
  - the full per-feature L2G SHAP contributions;
  - single-cell QTL credible-set membership.
- **Remaining uncertainty.** A later release (26.09 or later) could change L2G.
- **Next.** Classify SHAP drivers.

### R04 · 2026-09-23T21:12Z · Are the current Open Targets locus-to-gene calls biological or positional?

- **Question.** For each locus, which feature class drives the top L2G gene?
- **Queries.** A variant-level GraphQL pull: 2,646 variant IDs → 1,264 found in Open Targets; 129,136 credible-set memberships; 22,856 E2G links. Then L2G with features for the 979 cognition-study credible sets.
- **Sources.** Open Targets 26.06 (accepted).
- **Acquired.** `data/sprint5/ot_*.parquet` and `reports/sprint5/opentargets_refresh.csv` (130 loci).
- **Conclusion.**
  - In **117 of 130 loci** the top L2G gene's largest SHAP feature is positional: distance, or gene/protein count.
  - Among the 33 Gate-C loci only three are driven otherwise:
    - 12q13.2 → **SUOX**, by pQTL colocalisation;
    - 3p21.1 (NT5DC2 / SFMBT1 labels) → **STAB1**, by enhancer E2G.
  - The Open Targets locus-to-gene layer therefore cannot resolve genes at these loci.
  - Only **3 of 224** credible variants with PIP ≥ 0.1 are coding:
    - **SLC39A8 rs13107325** (missense, PIP ≈ 1.00);
    - ERLIN1 rs2862954 (PIP 0.35);
    - AKAP6 rs1051695 (PIP 0.11).
- **Remaining uncertainty.** E2G biosample coverage of adult brain is thin: DLPFC, caudate, posterior cingulate, astrocytes.
- **Next.** Brain-restricted E2G per credible variant, and QTL colocalisation.

### R05 · 2026-09-23T21:15Z · Locus confidence under the frozen Bayes-factor rule

- **Question.** How certain is each association outside UK Biobank?
- **Method.** The G&C TMA aligned z (Sprint 4), Tweedie-shrunk Davies z, and the frozen BF.
- **Sources.** Zabaneh 2018 sumstats (local copy; sensitivity only).
- **Conclusion.**
  - The 159 LD loci collapse to **152 signals** (shared lead SNPs).
  - Strata:

    | Stratum | Signals |
    |---|---|
    | L1 | 3 (AKAP6 rs2239647, ATXN2L rs62037363, DPP4 rs2284871 labels) |
    | L2 | 10 |
    | L3 | 77 |
    | L4 (discordant) | 50 |
    | Not testable | 12 |

  - The Zabaneh IVW slope is 0.20 over 131 signals: concordant, but not independent.
  - Rank intervals beyond the top 3 span roughly 1–100. Beyond the top few, locus ordering is not statistically resolved.
- **Remaining uncertainty.** The within-family lineage is missing.
- **Next.** Variant-to-gene classes.

### R06 · 2026-09-23T21:20Z · Math-53: verify the source before using it (subagent; details in `math_notes.md`, `math_audit.md`)

- **Question.** Do 53 genome-wide significant quantitative-ability SNPs exist? What exactly is the phenotype, and is it independent of our general-cognition GWAS?
- **Sources.**
  - Giannelis et al. 2025, *Mol Psychiatry* (PMID 40975749; PMC12602337): full text, Supplementary Tables S1–S12 and OSF code. **Accepted.**
  - GWAS Catalog: no entry.
- **Acquired.** Supplementary Table S2 as the 53 COJO leads (`data/raw/sprint5/math/giannelis2025_tableS2.csv`, sha256 030f88c0…), GRCh37, verified against Ensembl.
- **Conclusion.**
  - **The count of 53 is verified.** The phenotype, Gq, is a genomic-SEM factor built from two 23andMe self-report / course-taking indicators, fixed orthogonal to g by design.
  - The model's anchors, CP and EA, contain UK Biobank.
  - The summary statistics are **not public** (23andMe).
  - **Overlap with the 159 loci:** 11 of 53 SNPs fall in or near a general-cognition locus, against 3.1 expected (P = 3e-4).
  - **Direction:** only 17 of 53 math-raising alleles also raise Davies g (P = 0.013), and 11 of 13 Bonferroni-significant Davies SNPs are inverted. This is the signature of partialling g out of the model, not of shared biology.
  - The objective UKB arithmetic items (FI1, FI4) show no signal.
- **Remaining uncertainty.** Genuine inversion cannot be separated from the modelling artefact without the 23andMe per-SNP effects.
- **Next.** Variant-to-gene (V2G) mapping of the 53, and the cross-domain gene test M3.

### R07 · 2026-09-23T21:26Z · Rare-coding and positive-dosage evidence (subagent; `rare_coding_notes.md`)

- **Question.** Which genes carry exome-wide rare-coding evidence for cognition? Is there any positive human dosage evidence?
- **Sources (accepted).**
  - Chen 2023 *Nat Genet* supplementary tables.
  - Genebass (Karczewski 2022), CC BY 4.0.
  - Wu 2025 *PNAS*.
  - Kingdom 2024.
  - The 2q12.3 primary paper and its forward citations.
  - CNV population studies.
  - DDG2P.
- **Sources rejected.** The AstraZeneca PheWAS portal (requires accepting terms).
- **Conclusion.**
  - **Exome-wide for direct cognition:** KDM5B, ANKRD12, RC3H2, CACNA1A. **EA-proxy only:** ADGRB2, GIGYF1, SLC8A1, BCAS3.
  - All are UK Biobank discoveries. In every case, loss-of-function carriers do worse, so this is evidence of LoF impairment, **not** of an enhancement direction.
  - No gene replicated outside UKB; only the 8-gene set replicated, in Finnish cohorts.
  - **2q12.3 duplication:** NOMINAL_UNREPLICATED. None of its 5 citing papers re-tests it, and SEPTIN10 is predicted triplosensitive.
  - Every other duplication lowers cognition.
  - The RIMS1 "enhancement" kindred is confounded by a PROM1 variant.
- **Remaining uncertainty.** No non-UKB exome study of gene-level adult cognition exists.
- **Next.** Convergence tests T1–T5.

### R08 · 2026-09-23T21:31Z · Do rare-coding and common-variant genes converge? (frozen T1–T5)

- **Method.** Matched null of 10,000 gene sets drawn from gene-length × NSNPS × LOEUF strata.
- **Result (4 exome-wide cognition genes).**

  | Test | Observed | Null / comparison | P |
  |---|---|---|---|
  | T1: mean Davies MAGMA z | 1.46 | 1.38 | 0.43 |
  | T2: genes inside the 159 loci | 0 of 4 | 0.06 expected | 1.0 |
  | T3: genes in FDR-significant common sets | 1 | 0.88 | 0.63 |
  | T4: prenatal-dominant genes | 2 of 4 | 53 of 373 common genes | 0.10 |
  | T5: cell-type-enriched genes | 0 of 4 | — | — |

  The 8-gene set including EA proxies is also null.
- **Conclusion.** No detectable convergence. With 4–8 genes the tests are underpowered, so this is **NOT** evidence of separate biology.
- **Next.** None available: no larger non-UKB rare-variant cognition gene list exists.

### R09 · 2026-09-23T21:35Z · Discovered numerical defect: KDE-Tweedie shrinkage

- **Finding.** While classifying SLC39A8, its locus came out "discordant" despite G&C z = +1.91. The cause is the Sprint-4 KDE-Tweedie estimate, which maps z = 8.33 to −1.99 because the KDE gradient is unstable in the sparse tail. It is also non-monotone elsewhere (z = 6.23 → 8.88).
- **Action.** Amendment A2 replaces it with an empirical-Bayes normal scale mixture with the same estimand. The locus ranks were recomputed. The defective version is kept at `data/sprint5/locus_confidence_rank_KDE_TWEEDIE_DEFECTIVE.csv`.
- **Sprint-4 impact** (`data/sprint5/sprint4_tweedie_correction.json`):
  - The expected G&C concordance band moves from 74–80% to 75–82%. The observed 75.2% is still inside it.
  - Gate-A sign-test power is unchanged at about 100%.
  - No decision changes. A dated correction block goes into the Sprint-4 report.

### R10 · 2026-09-23T21:40Z · AlphaGenome access (subagent; `alphagenome_notes.md`)

- **Sources.** PyPI `alphagenome` 0.9.0 (2026-09-08), the DeepMind documentation and the Atlas page.
- **Conclusion.** Tissue- and track-level scores need an API key (Google sign-in plus acceptance of non-commercial terms). The Atlas bulk files return HTTP 500 without sign-in. The ungated Hugging Face mirrors were rejected: they require accepting terms, and they carry only the tissue-agnostic, directionless impact score (AVI).
- **Status.** **NOT_TESTABLE (access).** The query script exits cleanly at the authentication boundary. The user action is recorded in the final report.

### R11 · 2026-09-23T21:49Z · A new UKB-free replication lineage? GenLang performance IQ

- **Question.** Is there an open, UKB-free general-cognition GWAS beyond G&C?
- **Sources.**
  - The subagent's cohort-overlap ledger (`data/sprint5/cohort_overlap_ledger.csv`).
  - GWAS Catalog GCST90104472 (Eising 2022; N = 18,722; CC0).
- **Acquired.** 478 MB of summary statistics, md5 d59615f3… (matches the catalog), in `data/interim/sprint5/genlang/`.
- **Result, computed before inspecting any single locus.** 106 of 141 testable lead alleles are concordant. IVW slope on EB-shrunk Davies z = 0.173 (SE 0.017).
- **Status.** Whether GenLang counts toward independent locus confidence depends on the cohort-overlap verdict. That check is running as a separate subagent, and its verdict will be applied mechanically.
- **Next.** Apply the verdict. If the lineage is independent, the locus strata change.

### R12 · 2026-09-23T~22:00Z · brainSCOPE (subagent; `brainscope_notes.md`)

- **Question.** Do the cognition credible variants act as cell-type eQTLs in adult DLPFC? In which cell types, and in which direction?
- **Sources (accepted).**
  - Emani 2024 *Science* (PMID 38781369).
  - The brainSCOPE portal: 187 files, 1.6 GB.
  - PsychENCODE resource pages.
- **Rejected / blocked.** The Synapse genotypes (syn51111084, syn53479857) require controlled access.
- **Conclusion.**
  - 17 cell types have eQTL results, from 97–346 donors each. Only significant pairs are public, so **colocalisation is NOT_TESTABLE**.
  - brainSCOPE donors overlap CommonMind (100 MSSM) and ROSMAP (46), so it is **not** an independent QTL cohort.
  - Lead-variant tagging (lead inside the credible set, or r² ≥ 0.8):

    | Gene | Cell types | Cognition-increasing allele → expression |
    |---|---|---|
    | RPS26 | 10 | higher |
    | WBP2NL | 10 | lower |
    | CYP2D6 | 6, inhibitory neurons | higher |
    | DHRS11 | 4 neuronal | lower |
    | SH2B1 | L2/3 IT | higher |
    | GOSR1 | L2/3 IT | higher |

  - No gene has opposite directions across cell types or against the bulk direction.
  - The NEGR1 (Lamp5) and EXOC4 (L5 IT) cell-type eQTLs are **not** the GWAS signal (r² 0.02 and 0.12).

### R13 · 2026-09-23T~22:05Z · Is GenLang independent? (subagent; `genlang_overlap.md`)

- **Conclusion.** **PARTIAL_OVERLAP.** BATS (1,414 of 18,722, 7.6%) is in Davies 2018 (Supplementary Data 18). CHIC also overlaps: LBC1921, LBC1936 and QIMR/BATS make up 25.4%.
- Under the frozen rule, GenLang is **sensitivity-only**. It still replicates the locus set: 106 of 141 concordant, slope 0.173 (SE 0.017).
- Loci supported by both G&C and GenLang:

  | Locus label | G&C z | GenLang z |
  |---|---|---|
  | AKAP6 | 3.52 | 2.76 |
  | EXOC4 | 2.35 | 3.04 |
  | DCC | 2.16 | 1.32 |
  | DDN | 2.30 | 1.34 |
  | DPP4 | 2.74 | 1.24 |

- NT5DC2, SLC39A8 and UBE2E1 are **not** supported in GenLang: z = −0.23, −0.34 and −1.14.
- **Next.** No further open, UKB-free general-cognition GWAS exists (datasets_notes.md). Within-family data remain the missing lineage.

### R14 · 2026-09-23T~22:20Z · Developmental brain eQTL colocalisation

- **Data.** eQTL Catalogue r7, Sprint-4 fetch code: Walker 2019 fetal neocortex, Aygün 2021 progenitors and neurons, and BrainSeq DLPFC (mixed age; sensitivity only).
- **Tests.** 969 coloc.abf tests. The first run crashed on an empty harmonisation and was fixed with a guard.
- **Result.** 20 strong colocalisations (PP.H4 ≥ 0.8):

  | Gene | Datasets | Cognition-increasing allele → expression |
  |---|---|---|
  | **NT5DC2** | fetal neocortex 0.95; BrainSeq 0.97 | lower |
  | **DNPH1** | 3 datasets | lower |
  | **RHEBL1** | fetal + BrainSeq | higher (same as adult) |
  | **CLCN2** | fetal 0.99 | higher |
  | CYP2D6 / WBP2NL / NAGA | fetal | — |

- **Conclusion.**
  - NT5DC2 has *developmental* QTL colocalisation and no adult one. This fits a DEVELOPMENTAL causal hypothesis. It is **not** a V2G vote under the frozen rules, where developmental QTLs are flags only.
  - FOCUS (adult weights) favoured GNL3, so the gene call stays unresolved.

### R15 · 2026-09-23T~22:30Z · Literature red team (3 subagents; `dossier_notes_batch{1,2,3}.md`)

- **Scope.** 20 dossiers: 18 genes promoted by the frozen rule, plus 2 explicit inspections (SLC39A8, NT5DC2).
- **Flags raised. None changes a frozen class.**
  - **TUFM.** Should be presented as the ATXN2L *locus*: brainSCOPE tags SH2B1.
  - **RHEBL1.** Avoids CONTESTED by only 0.02 of FOCUS PIP.
  - **SLC39A8.** A391T is sign-discordant in GenLang, and the knock-in mouse shows no behavioural phenotype.
  - **NEGR1.** The literature direction conflicts with ours: the cognition-raising allele raises NEGR1, and NEGR1 overexpression impairs memory. This suggests an inverted-U dosage response.
  - **KDM5B.** The developmental-only flag is too strong: adult mouse knockdown impairs memory.
  - **ANKRD12.** Its UKB LoF burden is broadly pleiotropic: neuroticism, depression, deprivation.
  - **RC3H2.** Rests on 16 carriers; likely winner's curse.
  - **CACNA1A.** Gain-of-function variants are worse, so there is no beneficial direction.
  - **DCC.** Heterozygous LoF carriers usually have normal IQ.
  - **Rahman 2026** uses the same G&C data as our replication lineage, so it is NON-INDEPENDENT.

### R16 · 2026-09-23T~22:45Z · Would the brainSCOPE GRN links change anything? (sensitivity)

- **Trigger.** The batch-3 dossier found a ZFTRAF1 GRN promoter link filed under its previous symbol, CYHR1.
- **Decision (frozen definition).** GRN element→gene edges are TF-network inferences, partly derived from expression in the eQTL donors. They are not a chromatin activity-by-contact model, so they are **not counted** as ENHANCER_LINK.
- **Sensitivity** (`data/sprint5/grn_sensitivity.csv`). If they were counted, RHEBL1 would gain a second class and reach MODERATE, and therefore direction stratum D1. It would be the only gene to reach D1. But the single element involved links 9 genes, so it does not discriminate between them. **Reported, not used.**

### R17 · Saturation assessment (why the loop stopped)

Additional search now returns redundant or access-blocked resources:

- **Open Targets.** No release newer than 26.06.
- **Independent cognition GWAS.** Every open, UKB-free cognition GWAS larger than 10k either overlaps Davies (GenLang, CHIC) or is already used (G&C).
- **Extreme IQ.** No new deposits since 2023.
- **Rare coding.** No gene-level study outside UK Biobank.

The analyses that would change candidate ordering are **access-blocked**:

- within-family GWAS (JWT);
- AlphaGenome (API key);
- brainSCOPE full statistics (Synapse);
- TGFM (dbGaP);
- 23andMe math summary statistics.

One analysis is **public but not yet run**: cell-type colocalisation against the open single-cell brain eQTLs of Bryois 2022. It is the top next computation.
