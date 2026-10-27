# Datasets and provenance

This guide documents the actual research resources, as distinct from datasets only found by a search. The machine-readable [source manifest](data/release/source_manifest.json) contains full author lists, titles, DOI/year, populations, phenotype definitions, uses, scripts, outputs and source terms for each analytical/resource family. Unknown quantities are explicitly stated rather than inferred. Research snapshot: 24 September 2026; release metadata checks: 27 October 2026.

**Hamiltonian Labs recruited no participants.** The programme used published summary statistics, molecular association summaries, annotation databases and literature. Participant genotypes, clinical records and identifiable exceptional individuals are not release data.

## Cohort and phenotype boundaries

- Davies discovery analysed the public N=282,014 file, not all 300,486 participants in the publication. Savage shares UKB/COGENT. Do not sum their participant counts.
- Zabaneh cases were selected from approximately the top 0.03% via above-level SAT/ACT testing in Duke TIP. Its HRS controls overlap Davies. This is a sensitivity dataset, not independent replication or identified high-IQ individuals.
- G&C executive function is the counted non-UKB recruitment lineage; individual participant overlap has not been comprehensively checked. Howe within-family estimates share some UKB/Generation Scotland people with discovery: they add a family-design contrast, not a disjoint sample.
- GenLang PIQ includes BATS (1,414/18,722 = 7.6%) shared with Davies. Mathematics self-report/course-taking (Gq), objective arithmetic and education are distinct from general intelligence.
- Molecular study names are not independent donor sets. ROSMAP/CommonMind recur in bulk, Bryois, SingleBrain and brainSCOPE. GTEx versions reuse donors. Transcript-level rows are not independent gene-level evidence.
- Most cognitive discovery and reference LD are European. Molecular cross-ancestry inputs do not make the whole analysis ancestry-general.

## Complete record indexes

- [419 tournament study metadata records](data/gene_tournament/study_metadata.jsonl): phenotype, accession, cohort/ancestry strings, sample-size descriptions and full-summary availability. Search inclusion is not evidence of execution.
- [Study classification implementation](pipelines/gene_tournament/classify_studies.py) and [phenotype model](research/sprint5a/phenotype_model.md) separate direct cognition, proxies, clinical and excluded evidence.
- [132-publication bibliography](data/release/catalogue_publications.json): verified publication metadata for all unique PMIDs in the tournament and selected QTL metadata; original titles, full authors, years and DOI where assigned.
- [Selected QTL assay inventory](data/sprint4/eqtl_catalogue_brain_datasets.csv): QTD/QTS identifiers, tissue, assay, sample size, adult/fetal classification, eligibility/exclusion, PMID and exact URLs. [Complete R7 catalogue metadata](data/raw/sprint4/eqtl_catalogue/metadata/dataset_metadata_r7.tsv) includes resources not used.
- [brainSCOPE file inventory](data/sprint5/brainscope_datasets.csv): cell-specific sample sizes, significance scope, build/alleles and hashes.
- [Cohort overlap ledger](data/sprint5/cohort_overlap_ledger.csv): includes candidate-only/unavailable studies and dated provisional findings; the 5A update takes precedence on completed within-family access.
- [Acquisition/provenance index](data/release/provenance_index.json): every committed provenance/manifest record, plus a pointer to the raw snapshot spine. Original and sanitised file hashes are distinguished.

## Analytical and reference resources

### Davies general cognitive function (`davies2018`)

Davies G et al. (2018). *Study of 300,486 individuals identifies 148 independent genetic loci influencing general cognitive function.*. [DOI](https://doi.org/10.1038/s41467-018-04362-x). Full author metadata is in the source manifest.

**Phenotype / selection:** General cognitive factor from cohort batteries; UKB verbal-numerical reasoning. Population cohorts; not selected for exceptional intelligence.
**Population / N:** European ancestry; 57 population-based cohorts; CHARGE, COGENT, UK Biobank; adults aged 16–102. 282,014 in the public file analysed; 300,486 in full publication.
**Obtained and used:** GRCh37 SNP summary statistics; MAGMA gene results and gene correlations. Primary discovery, gene screen, LD loci, colocalisation and cross-trait analyses.
**Implementation:** [pipelines/gene_tournament/ingest_magma_gene_analysis.py](pipelines/gene_tournament/ingest_magma_gene_analysis.py), [pipelines/sprint4/gate_c_coloc.py](pipelines/sprint4/gate_c_coloc.py).
**Dependent outputs:** [reports/gene_tournament/direct_cognition_rank.csv](reports/gene_tournament/direct_cognition_rank.csv), [reports/sprint5a/s5_integrated/locus_confidence_rank.csv](reports/sprint5a/s5_integrated/locus_confidence_rank.csv).
**Dependence / limitations:** HRS/BATS/UKB overlap other datasets; public subset differs from full article; association is not intervention effect.
**Rights/access:** Public subset CC-BY-4.0 per acquisition record; full restricted file is not redistributed. [Official source](https://doi.org/10.7488/ds/2558).
**Provenance:** [data/raw/magma_x01/2026-09-22/davies2018_open_complete.txt.provenance.json](data/raw/magma_x01/2026-09-22/davies2018_open_complete.txt.provenance.json).

### Savage intelligence (`savage2018`)

Savage JE et al. (2018). *Genome-wide association meta-analysis in 269,867 individuals identifies new genetic and functional links to intelligence.*. [DOI](https://doi.org/10.1038/s41588-018-0152-6). Full author metadata is in the source manifest.

**Phenotype / selection:** Intelligence, harmonised across cognitive tests. Population cognitive cohorts, not an exceptional-only sample.
**Population / N:** European ancestry, including UKB and COGENT. 269,867.
**Obtained and used:** SNP summary statistics and MAGMA outputs. Sensitivity, rank comparison and pathway replication.
**Implementation:** [pipelines/gene_tournament/ingest_magma_gene_analysis.py](pipelines/gene_tournament/ingest_magma_gene_analysis.py), [pipelines/gene_tournament/build_gene_ranks.py](pipelines/gene_tournament/build_gene_ranks.py).
**Dependent outputs:** [reports/gene_tournament/direct_cognition_rank.csv](reports/gene_tournament/direct_cognition_rank.csv).
**Dependence / limitations:** Shares discovery cohorts with Davies; not independent replication.
**Rights/access:** Summary-statistic source terms; article licence is not automatically the data licence; no full source download bundled. [Official source](https://www.ebi.ac.uk/gwas/studies/GCST006250).
**Provenance:** [data/raw/magma_sprint3/2026-09-22/PROVENANCE.json](data/raw/magma_sprint3/2026-09-22/PROVENANCE.json).

### Zabaneh exceptional intelligence (`zabaneh2018`)

Zabaneh D et al. (2018). *A genome-wide association study for extremely high intelligence.*. [DOI](https://doi.org/10.1038/mp.2017.121). Full author metadata is in the source manifest.

**Phenotype / selection:** Extreme positive cognitive ability, case-control. Top 1% of TIP’s top ~3%: approximately top 0.03%; selected using SAT/ACT at age 12. Approximate mean IQ 170 is a study characterisation, not an individual measurement supplied to this project.
**Population / N:** US Duke TIP cases of European ancestry and population HRS controls. 1,238 cases + 8,172 controls in analysed GWAS.
**Obtained and used:** GCST005626 summary statistics; MAGMA and allele-harmonised comparisons. Exceptional-tail continuity and sensitivity; LDSC/LAVA.
**Implementation:** [pipelines/sprint3_1/extreme_tail_reassessment.py](pipelines/sprint3_1/extreme_tail_reassessment.py), [pipelines/sprint5a/prep_ldsc_inputs.py](pipelines/sprint5a/prep_ldsc_inputs.py).
**Dependent outputs:** [reports/sprint3_1/extreme_tail_locus_direction.csv](reports/sprint3_1/extreme_tail_locus_direction.csv), [reports/sprint5a/cross_phenotype_convergence.csv](reports/sprint5a/cross_phenotype_convergence.csv).
**Dependence / limitations:** HRS controls overlap Davies; ascertainment and range restriction; paper Methods gives 8,185 genotyped controls before final analysis versus 8,172 in abstract/analysis.
**Rights/access:** Article CC-BY-NC-SA-4.0; GCST summary files follow their repository terms; no article or individual genotypes bundled. [Official source](https://www.ebi.ac.uk/gwas/studies/GCST005626).
**Provenance:** [data/sprint5/extreme_iq_datasets.csv](data/sprint5/extreme_iq_datasets.csv), [data/raw/sprint5/extreme_iq/GCST005626_README.txt](data/raw/sprint5/extreme_iq/GCST005626_README.txt).

### Howe within-sibship cognition (`howe2022`)

Howe LJ et al. (2022). *Within-sibship genome-wide association analyses decrease bias in estimates of direct genetic effects.*. [DOI](https://doi.org/10.1038/s41588-022-01062-7). Full author metadata is in the source manifest.

**Phenotype / selection:** Within-sibship and population cognitive-ability effects. Family-based recruitment; not exceptional intelligence.
**Population / N:** Predominantly European family cohorts; includes UKB, Generation Scotland and twins. OpenGWAS sibling metadata N=9,997; population N=22,593; paper cognition N=27,638; project SE-derived effective N=11,257.411764705881.
**Obtained and used:** GWAS-VCF for ieu-b-4837 and ieu-b-4838 acquired externally using JWT; aggregate locus results committed. Within-family direct-effect sensitivity; a counted design lineage under frozen rules.
**Implementation:** [pipelines/sprint4/gate_a_within_family.py](pipelines/sprint4/gate_a_within_family.py), [pipelines/sprint5a/gate_a_decision.py](pipelines/sprint5a/gate_a_decision.py).
**Dependent outputs:** [reports/sprint4/within_family_locus_concordance.csv](reports/sprint4/within_family_locus_concordance.csv), [reports/sprint4/decision_gate_a_update.json](reports/sprint4/decision_gate_a_update.json).
**Dependence / limitations:** Shared participants with discovery; the two counted lineages are not disjoint cohorts; 109/146 is not 109 significant loci.
**Rights/access:** OpenGWAS access terms and source study terms; credentials and full VCFs absent from release; reacquire through official access. [Official source](https://gwas.mrcieu.ac.uk/datasets/ieu-b-4837/).
**Provenance:** [data/sprint4/gate_a_access.json](data/sprint4/gate_a_access.json), [data/raw/sprint4/opengwas_metadata/gwasinfo_ieu-b-4837_4838.json](data/raw/sprint4/opengwas_metadata/gwasinfo_ieu-b-4837_4838.json).

### Genes & Cognition executive function (`genc`)

Rahman MS et al. (2026). *Genetic landscape of adult executive function reveals a cell-type-specific developmental origin.*. [DOI](https://doi.org/10.1038/s41467-026-71738-9). Full author metadata is in the source manifest.

**Phenotype / selection:** Trail-making time: TMA primary, TMN/TMD supporting; higher time is worse. Volunteers assessed for cognition, not selected as exceptional individuals.
**Population / N:** NIHR BioResource G&C; UKB-free recruitment; individual overlap unverified. 9,932 in project replication.
**Obtained and used:** Open Zenodo GWAS summary files. Main non-UKB replication; effect polarity reversed for better performance.
**Implementation:** [pipelines/sprint4/gate_b_genc.py](pipelines/sprint4/gate_b_genc.py).
**Dependent outputs:** [reports/sprint4/genc_independent_loci.csv](reports/sprint4/genc_independent_loci.csv).
**Dependence / limitations:** Executive function differs from general intelligence; TMA/TMN/TMD use the same people and count once.
**Rights/access:** Zenodo record terms; public summary statistics; no participant data. [Official source](https://doi.org/10.5281/zenodo.11066096).
**Provenance:** [data/sprint5/cohort_overlap_ledger.csv](data/sprint5/cohort_overlap_ledger.csv).

### GenLang performance IQ (`genlang`)

Eising E et al. (2022). *Genome-wide analyses of individual differences in quantitatively assessed reading- and language-related skills in up to 34,000 people.*. [DOI](https://doi.org/10.1073/pnas.2202764119). Full author metadata is in the source manifest.

**Phenotype / selection:** Nonverbal/performance IQ, z-standardised within cohorts. Developmental cohorts; no exceptional-IQ selection.
**Population / N:** Childhood to young-adult cohorts, approximately ages 5–26; includes dyslexia-enriched cohorts; predominantly European. 18,722 for performance IQ, not 34,000 (paper-wide maximum).
**Obtained and used:** GCST90104472 GRCh37 full summary statistics (historically fetched after discovery search). Sensitivity replication and cross-trait modelling.
**Implementation:** [pipelines/sprint5/locus_confidence.py](pipelines/sprint5/locus_confidence.py), [pipelines/sprint5a/prep_ldsc_inputs.py](pipelines/sprint5a/prep_ldsc_inputs.py).
**Dependent outputs:** [reports/sprint5a/s5_integrated/locus_confidence_rank.csv](reports/sprint5a/s5_integrated/locus_confidence_rank.csv).
**Dependence / limitations:** BATS contributes 1,414 (7.6%) and overlaps Davies; CLDRC/IBG overlap ambiguous; not counted independent.
**Rights/access:** CC0 in committed GWAS metadata; retain source citation. [Official source](https://www.ebi.ac.uk/gwas/studies/GCST90104472).
**Provenance:** [data/raw/sprint5/cognition_gwas_search/GCST90104472_README.txt](data/raw/sprint5/cognition_gwas_search/GCST90104472_README.txt), [research/sprint5/genlang_overlap.md](research/sprint5/genlang_overlap.md).

### UK Biobank arithmetic items (`ukb_arithmetic`)

Jiang L et al. (2021). *A generalized linear mixed model association tool for biobank-scale data.*. [DOI](https://doi.org/10.1038/s41588-021-00954-4). Full author metadata is in the source manifest.

**Phenotype / selection:** FI4 positional arithmetic GCST90042729; FI1 numeric addition GCST90042726. Population biobank, not exceptional selection.
**Population / N:** UK Biobank, European-ancestry analysis; middle/older-aged volunteers. FI4 mean per-SNP N=114,552 (MAGMA provenance); FI1 per-item N not independently reconciled.
**Obtained and used:** Item summary statistics, MAGMA gene tables and allele data. Math sensitivity; FI4 LDSC, Genomic SEM and LAVA.
**Implementation:** [pipelines/gene_tournament/build_gene_ranks.py](pipelines/gene_tournament/build_gene_ranks.py), [pipelines/sprint5a/prep_ldsc_inputs.py](pipelines/sprint5a/prep_ldsc_inputs.py).
**Dependent outputs:** [reports/gene_tournament/math_gene_rank.csv](reports/gene_tournament/math_gene_rank.csv), [reports/sprint5a/lava_bivariate_core5.csv](reports/sprint5a/lava_bivariate_core5.csv).
**Dependence / limitations:** Objective single items are not comprehensive mathematics tests; ceiling/floor; UKB shared with Davies.
**Rights/access:** Accession-specific GWAS terms; no participant records. [Official source](https://www.ebi.ac.uk/gwas/studies/GCST90042729).
**Provenance:** [data/raw/magma_sprint3/2026-09-22/PROVENANCE.json](data/raw/magma_sprint3/2026-09-22/PROVENANCE.json), [data/sprint5a/phenotype_datasets.csv](data/sprint5a/phenotype_datasets.csv).

### Giannelis mathematical factor (`giannelis`)

Giannelis A et al. (2025). *A genetic common factor underlying self-reported math ability and highest math class taken.*. [DOI](https://doi.org/10.1038/s41380-025-03237-0). Full author metadata is in the source manifest.

**Phenotype / selection:** Self-rated mathematics and highest mathematics class, genomic SEM Gq orthogonal to g. Volunteer questionnaire respondents.
**Population / N:** 23andMe questionnaires, with cognition/education anchors containing UKB; not exceptional IQ. Item sample sizes approximately 430,000–565,000; 53 published variants used.
**Obtained and used:** Published 53-variant supplement; public code and supplementary tables, not full factor GWAS. Variant mapping and descriptive math overlap.
**Implementation:** [pipelines/sprint5/math53_analysis.py](pipelines/sprint5/math53_analysis.py), [pipelines/sprint5a/convergence_and_shortlists.py](pipelines/sprint5a/convergence_and_shortlists.py).
**Dependent outputs:** [data/sprint5/math53_variants.csv](data/sprint5/math53_variants.csv), [reports/sprint5/math53_gene_mapping.csv](reports/sprint5/math53_gene_mapping.csv).
**Dependence / limitations:** Self-report/course-taking proxy; factor orthogonalisation explains inverted effects; no full Gq coloc possible.
**Rights/access:** Article/supplement CC-BY-4.0 per provenance; 23andMe GWAS requires application and is not bundled. [Official source](https://doi.org/10.1038/s41380-025-03237-0).
**Provenance:** [data/raw/sprint5/math/PROVENANCE.json](data/raw/sprint5/math/PROVENANCE.json).

### Rare-coding cognition / Chen (`rare_coding`)

Chen CY et al. (2023). *The impact of rare protein coding genetic variation on adult cognitive function.*. [DOI](https://doi.org/10.1038/s41588-023-01398-8). Full author metadata is in the source manifest.

**Phenotype / selection:** Verbal-numerical reasoning, reaction time; educational attainment separately labelled proxy. Population biobank; not exceptional selection.
**Population / N:** UKB exome participants; Finnish replication at gene-set level. Trait-specific approximately 159,000–394,000; do not sum phenotypes.
**Obtained and used:** Published burden tables and Genebass summaries. Loss-of-function evidence and common–rare overlap null tests.
**Implementation:** [pipelines/sprint5/build_rare_coding_tables.py](pipelines/sprint5/build_rare_coding_tables.py).
**Dependent outputs:** [reports/sprint5/rare_coding_evidence.csv](reports/sprint5/rare_coding_evidence.csv), [reports/sprint5/common_rare_convergence.csv](reports/sprint5/common_rare_convergence.csv).
**Dependence / limitations:** UKB-only gene-level evidence; loss does not show benefit from gain; RC3H2 small carrier count; CACNA1A threshold caveat.
**Rights/access:** Published summary results; no exome records or carrier identifiers; source-specific terms. [Official source](https://doi.org/10.1038/s41588-023-01398-8).
**Provenance:** [data/raw/sprint5/rare_coding/PROVENANCE.json](data/raw/sprint5/rare_coding/PROVENANCE.json).

### Genebass (`genebass`)

Karczewski KJ et al. (2022). *Systematic single-variant and gene-based association testing of thousands of phenotypes in 394,841 UK Biobank exomes.*. [DOI](https://doi.org/10.1016/j.xgen.2022.100168). Full author metadata is in the source manifest.

**Phenotype / selection:** Thousands of UKB phenotypes including cognition and education. Biobank.
**Population / N:** UK Biobank exome cohort. 394,841 maximum; phenotype-specific N differs.
**Obtained and used:** Public association queries, curated burden summaries. Rare-coding and dosage cross-checks.
**Implementation:** [pipelines/sprint5/build_rare_coding_tables.py](pipelines/sprint5/build_rare_coding_tables.py).
**Dependent outputs:** [reports/sprint5/rare_coding_evidence.csv](reports/sprint5/rare_coding_evidence.csv).
**Dependence / limitations:** Same UKB lineage as common variants, not an independent replication.
**Rights/access:** CC-BY-4.0 association results; no re-identification; per provenance. [Official source](https://genebass.org/).
**Provenance:** [data/raw/sprint5/rare_coding/PROVENANCE.json](data/raw/sprint5/rare_coding/PROVENANCE.json).

### Gene-dosage / CNV literature (`codage`)

Huguet G et al. (2024). *Effects of gene dosage on cognitive ability: A function-based association study across brain and non-brain processes.*. [DOI](https://doi.org/10.1016/j.xgen.2024.100721). Full author metadata is in the source manifest.

**Phenotype / selection:** Cognitive ability and CNV gene dosage. Varies by source; no Hamiltonian Labs participants.
**Population / N:** Multi-cohort literature including UKB; cohort-specific details in source. No single pooled N used by release; published summary findings extracted.
**Obtained and used:** Published CNV tables and literature annotations. Evaluate positive-dosage claims; correct 2q12.3 overinterpretation.
**Implementation:** [pipelines/sprint5/build_rare_coding_tables.py](pipelines/sprint5/build_rare_coding_tables.py).
**Dependent outputs:** [reports/sprint5/cnv_positive_dosage.csv](reports/sprint5/cnv_positive_dosage.csv).
**Dependence / limitations:** Nominal/unreplicated increases; no replicated positive-dosage target.
**Rights/access:** Full-text CC-BY-NC-ND-4.0 removed from release; bibliographic and factual result annotations retained. [Official source](https://doi.org/10.1016/j.xgen.2024.100721).
**Provenance:** [data/raw/sprint5/rare_coding/PROVENANCE.json](data/raw/sprint5/rare_coding/PROVENANCE.json).

### GTEx adult expression and eQTL (`gtex`)

GTEx Consortium. (2020). *The GTEx Consortium atlas of genetic regulatory effects across human tissues.*. [DOI](https://doi.org/10.1126/science.aaz1776). Full author metadata is in the source manifest.

**Phenotype / selection:** Adult tissue expression and cis-eQTL; not cognition. Tissue donors, not high-IQ selection.
**Population / N:** Adult postmortem donors; ancestry composition per release, not inferred from GWAS. V10/V11 tissue-specific N; not the v8 paper total; see dataset metadata.
**Obtained and used:** Median TPM, regional eQTL statistics; V11 lookup and GENCODE ID map. Adult brain context, bulk coloc and cross-version sensitivity.
**Implementation:** [pipelines/gene_tournament/build_developmental_classification.py](pipelines/gene_tournament/build_developmental_classification.py), [pipelines/sprint4/fetch_eqtl_catalogue.py](pipelines/sprint4/fetch_eqtl_catalogue.py), [pipelines/sprint5a/gtex_v11_lookup.py](pipelines/sprint5a/gtex_v11_lookup.py).
**Dependent outputs:** [data/gene_tournament/developmental_classification.parquet](data/gene_tournament/developmental_classification.parquet), [reports/sprint4/directionality_resolution.csv](reports/sprint4/directionality_resolution.csv), [reports/sprint5a/gtex_v11_gene_direction.csv](reports/sprint5a/gtex_v11_gene_direction.csv).
**Dependence / limitations:** V10/V11 reuse donors; no new cohort independence; version differences and gene IDs; expression does not establish adult modifiability.
**Rights/access:** GTEx Portal licence; attribution required; this release is a historical snapshot, not current/most accurate portal data. [Official source](https://gtexportal.org/home/license).
**Provenance:** [data/raw/brain_expression/PROVENANCE.json](data/raw/brain_expression/PROVENANCE.json), [data/raw/sprint5a/gtex_v11/PROVENANCE.json](data/raw/sprint5a/gtex_v11/PROVENANCE.json).

### CommonMind (`commonmind`)

Hoffman GE et al. (2019). *CommonMind Consortium provides transcriptomic and epigenomic data for Schizophrenia and Bipolar Disorder.*. [DOI](https://doi.org/10.1038/s41597-019-0183-6). Full author metadata is in the source manifest.

**Phenotype / selection:** DLPFC bulk molecular QTL. Brain donors, not cognition-selected.
**Population / N:** Postmortem psychiatric/control cohorts; study-specific ancestry. 590 donors in eQTL Catalogue study inventory; individual assays differ.
**Obtained and used:** Regional eQTL Catalogue summary statistics. Adult bulk coloc and direction.
**Implementation:** [pipelines/sprint4/fetch_eqtl_catalogue.py](pipelines/sprint4/fetch_eqtl_catalogue.py), [pipelines/sprint4/gate_c_coloc.py](pipelines/sprint4/gate_c_coloc.py).
**Dependent outputs:** [reports/sprint4/directionality_resolution.csv](reports/sprint4/directionality_resolution.csv).
**Dependence / limitations:** Overlaps brainSCOPE MSSM donors; disease and cell composition affect transferability.
**Rights/access:** eQTL Catalogue summary terms; underlying genotypes remain controlled. [Official source](https://www.ebi.ac.uk/eqtl/Studies/).
**Provenance:** [data/raw/sprint4/eqtl_catalogue/PROVENANCE.json](data/raw/sprint4/eqtl_catalogue/PROVENANCE.json), [data/sprint4/eqtl_catalogue_brain_datasets.csv](data/sprint4/eqtl_catalogue_brain_datasets.csv).

### ROSMAP (`rosmap`)

Ng B et al. (2017). *An xQTL map integrates the genetic architecture of the human brain's transcriptome and epigenome.*. [DOI](https://doi.org/10.1038/nn.4632). Full author metadata is in the source manifest.

**Phenotype / selection:** DLPFC expression and other molecular QTL. Ageing/brain-donation cohorts, not exceptional intelligence.
**Population / N:** Older postmortem Religious Orders Study / Memory and Aging Project donors. Assay-specific N in committed Catalogue metadata.
**Obtained and used:** Regional bulk QTL statistics; overlap lineage. Bulk coloc and independent-unit accounting.
**Implementation:** [pipelines/sprint4/gate_c_coloc.py](pipelines/sprint4/gate_c_coloc.py), [pipelines/sprint5a/direction_recount.py](pipelines/sprint5a/direction_recount.py).
**Dependent outputs:** [reports/sprint5a/directionality_resolution_5a.csv](reports/sprint5a/directionality_resolution_5a.csv).
**Dependence / limitations:** Donors recur in Bryois, SingleBrain and brainSCOPE; multiple rows are not multiple replications.
**Rights/access:** eQTL Catalogue summary terms; raw participant data controlled and excluded. [Official source](https://www.ebi.ac.uk/eqtl/Studies/).
**Provenance:** [data/raw/sprint4/eqtl_catalogue/metadata/dataset_metadata_r7.tsv](data/raw/sprint4/eqtl_catalogue/metadata/dataset_metadata_r7.tsv).

### eQTL Catalogue: all selected bulk/developmental assays (`eqtl_catalogue`)

eQTL Catalogue: all selected bulk/developmental assays (versioned resource). *eQTL Catalogue: all selected bulk/developmental assays (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Gene, transcript and splicing cis-QTL. Tissue datasets; no cognitive participant recruitment.
**Population / N:** GTEx, CommonMind, ROSMAP, Braineac2, Young_2019; developmental/BrainSeq/iPSC kept distinct. 648 regional adult-brain QTL files historically queried; not 648 independent cohorts.
**Obtained and used:** R7 metadata, tabix regional summary statistics, QTD identifiers. Harmonised adult QTL, fetal sensitivity, FOCUS inputs.
**Implementation:** [pipelines/sprint4/fetch_eqtl_catalogue.py](pipelines/sprint4/fetch_eqtl_catalogue.py), [pipelines/sprint5/dev_qtl_coloc.py](pipelines/sprint5/dev_qtl_coloc.py).
**Dependent outputs:** [reports/sprint4/directionality_resolution.csv](reports/sprint4/directionality_resolution.csv), [reports/sprint5/developmental_qtl_coloc.csv](reports/sprint5/developmental_qtl_coloc.csv).
**Dependence / limitations:** Transcript-level and gene-level evidence differ; source-labelled duplicate cohorts collapsed; per-assay PMID and N in manifest.
**Rights/access:** Catalogue summary terms (source attribution); access-controlled underlying genotype/expression not bundled. [Official source](https://www.ebi.ac.uk/eqtl/Licence/).
**Provenance:** [data/raw/sprint4/eqtl_catalogue/PROVENANCE.json](data/raw/sprint4/eqtl_catalogue/PROVENANCE.json), [data/sprint4/eqtl_catalogue_brain_datasets.csv](data/sprint4/eqtl_catalogue_brain_datasets.csv).

### Young microglial eQTL (`young`)

Young AMH et al. (2021). *A map of transcriptional heterogeneity and regulatory variation in human microglia.*. [DOI](https://doi.org/10.1038/s41588-021-00875-2). Full author metadata is in the source manifest.

**Phenotype / selection:** Microglial expression / eQTL. Clinical tissue, not cognitive extremes.
**Population / N:** Human surgical brain tissue donors; clinical ascertainment. 104 in Catalogue.
**Obtained and used:** Regional QTL statistics under Catalogue label Young_2019 (published 2021). Adult cell-specific/bulk sensitivity.
**Implementation:** [pipelines/sprint4/fetch_eqtl_catalogue.py](pipelines/sprint4/fetch_eqtl_catalogue.py).
**Dependent outputs:** [reports/sprint4/directionality_resolution.csv](reports/sprint4/directionality_resolution.csv).
**Dependence / limitations:** Study label year differs from final publication; clinical context; not a cognition GWAS.
**Rights/access:** Catalogue summary terms; participant data controlled. [Official source](https://doi.org/10.1038/s41588-021-00875-2).
**Provenance:** [data/sprint4/eqtl_catalogue_brain_datasets.csv](data/sprint4/eqtl_catalogue_brain_datasets.csv).

### PsychENCODE brainSCOPE (`brainscope`)

Emani PS et al. (2024). *Single-cell genomics and regulatory networks for 388 human brains.*. [DOI](https://doi.org/10.1126/science.adi5199). Full author metadata is in the source manifest.

**Phenotype / selection:** Single-nucleus eQTL, regulatory elements, GRN and CRISPR annotations. Postmortem donors, not exceptional cognitive performers.
**Population / N:** 388 adult DLPFC donors, mixed clinical/control; multiple ancestries per source, project did not estimate ancestry effects. 388 donors; 17 cell types; per-cell usable N in brainscope_datasets.csv.
**Obtained and used:** Public significant/conditional QTL tables, candidate SNPs, bcCRE, CRISPR and GRN; no participant-level genotypes. Cell-specific tagging, LD separation and full-statistic testability audit.
**Implementation:** [pipelines/sprint5/brainscope_lookup.py](pipelines/sprint5/brainscope_lookup.py), [pipelines/sprint5a/brainscope_typed_evidence.py](pipelines/sprint5a/brainscope_typed_evidence.py).
**Dependent outputs:** [reports/sprint5a/brainscope_typed_evidence.parquet](reports/sprint5a/brainscope_typed_evidence.parquet), [reports/sprint5a/brainscope_coloc_testability.json](reports/sprint5a/brainscope_coloc_testability.json).
**Dependence / limitations:** Significant-only outputs cannot support new colocalisation; shared CommonMind/ROSMAP donors; GRN links are not enhancer votes.
**Rights/access:** Public portal derived summaries; no broad relicence; full association/participant resources require Synapse access; obtain source terms before reuse. [Official source](https://brainscope.gersteinlab.org/data/).
**Provenance:** [data/raw/sprint5a/brainscope/PROVENANCE.json](data/raw/sprint5a/brainscope/PROVENANCE.json), [data/sprint5/brainscope_datasets.csv](data/sprint5/brainscope_datasets.csv).

### Bryois single-cell eQTL (`bryois`)

Bryois J et al. (2022). *Cell-type-specific cis-eQTLs in eight human brain cell types identify novel risk genes for psychiatric and neurological disorders.*. [DOI](https://doi.org/10.1038/s41593-022-01128-z). Full author metadata is in the source manifest.

**Phenotype / selection:** Cell-type cis-eQTL in 8 cell types plus pseudo-bulk. Brain donors, not high-IQ sample.
**Population / N:** ROSMAP and Roche brain cohorts; AD/MS/control tissue; ancestry as source. 192 donors in publication (196 preprint).
**Obtained and used:** Full nominal statistics, SNP positions and alleles; selected chromosomes. Single-cell coloc.abf/coloc.susie.
**Implementation:** [pipelines/sprint5a/fetch_sc_eqtl.py](pipelines/sprint5a/fetch_sc_eqtl.py), [pipelines/sprint5a/sc_eqtl_coloc.py](pipelines/sprint5a/sc_eqtl_coloc.py).
**Dependent outputs:** [reports/sprint5a/sc_eqtl_coloc.parquet](reports/sprint5a/sc_eqtl_coloc.parquet).
**Dependence / limitations:** ROSMAP donor overlap; SE inferred from beta/p; disease/cell composition; exact overlap unresolved.
**Rights/access:** CC-BY-4.0 Zenodo 7276971. [Official source](https://doi.org/10.5281/zenodo.7276971).
**Provenance:** [data/raw/sprint5a/bryois2022/PROVENANCE.json](data/raw/sprint5a/bryois2022/PROVENANCE.json).

### SingleBrain meta-analysis (`singlebrain`)

Jang B et al. (2025). *SingleBrain: A Meta-Analysis of Single-Nucleus eQTLs Linking Genetic Risk to Brain Disorders*. [DOI](https://doi.org/10.1101/2025.03.06.25323424). Full author metadata is in the source manifest.

**Phenotype / selection:** Single-nucleus eQTL. Postmortem tissue.
**Population / N:** Meta-analysis of brain donors, including ROSMAP; not independently recruited by project. 757 donors per historical provenance.
**Obtained and used:** Range-fetched full nominal QTL windows with byte-range hashes. Single-cell coloc and HyPrColoc support.
**Implementation:** [pipelines/sprint5a/fetch_sc_eqtl.py](pipelines/sprint5a/fetch_sc_eqtl.py), [pipelines/sprint5a/sc_eqtl_coloc.py](pipelines/sprint5a/sc_eqtl_coloc.py).
**Dependent outputs:** [reports/sprint5a/sc_eqtl_coloc.parquet](reports/sprint5a/sc_eqtl_coloc.parquet).
**Dependence / limitations:** Preprint version used; overlapping donors; not independent of Bryois/ROSMAP.
**Rights/access:** CC-BY-4.0 per Zenodo record/provenance. [Official source](https://doi.org/10.5281/zenodo.14908182).
**Provenance:** [data/raw/sprint5a/singlebrain/PROVENANCE.json](data/raw/sprint5a/singlebrain/PROVENANCE.json), [research/sprint5a/agentB_notes.md](research/sprint5a/agentB_notes.md).

### Wen / devBrain developmental xQTL (`devbrain`)

Wen C et al. (2024). *Cross-ancestry atlas of gene, isoform, and splicing regulation in the developing human brain.*. [DOI](https://doi.org/10.1126/science.adh0829). Full author metadata is in the source manifest.

**Phenotype / selection:** Fetal neocortical gene/isoform/splicing regulation. Developing brain tissue, 4–39 post-conception weeks overall.
**Population / N:** Cross-ancestry cohort; project trimester eQTL uses European subset. 672 unique samples; 654 genotype+RNA QC; EUR trimester 1 N=143, trimester 2 N=145.
**Obtained and used:** Full nominal eQTL windows and effect-allele BIM mapping. Timing and fetal colocalisation sensitivity.
**Implementation:** [pipelines/sprint5a/devbrain_fetch_small.py](pipelines/sprint5a/devbrain_fetch_small.py), [pipelines/sprint5a/devbrain_timing.py](pipelines/sprint5a/devbrain_timing.py).
**Dependent outputs:** [reports/sprint5a/regulatory_timing.csv](reports/sprint5a/regulatory_timing.csv).
**Dependence / limitations:** Not adult manipulation evidence; ancestries not pooled indiscriminately; third trimester EUR N=4 unused.
**Rights/access:** CC-BY-4.0 Zenodo 12729266. [Official source](https://doi.org/10.5281/zenodo.12729266).
**Provenance:** [data/raw/sprint5a/psychencode_dev/PROVENANCE.json](data/raw/sprint5a/psychencode_dev/PROVENANCE.json).

### BrainSpan developmental expression (`brainspan`)

Kang HJ et al. (2011). *Spatio-temporal transcriptome of the human brain.*. [DOI](https://doi.org/10.1038/nature10523). Full author metadata is in the source manifest.

**Phenotype / selection:** Expression across developmental age and brain region. Tissue donors, not cognition-selected.
**Population / N:** Human developing/adult postmortem brain; source-specific samples. Adult age window: 93 tissue samples from 6 donors; full release donor N not reconciled here.
**Obtained and used:** RPKM matrix and sample metadata acquired externally; gene-level derivative committed. Developmental expression classification.
**Implementation:** [pipelines/gene_tournament/build_developmental_classification.py](pipelines/gene_tournament/build_developmental_classification.py).
**Dependent outputs:** [data/gene_tournament/developmental_classification.parquet](data/gene_tournament/developmental_classification.parquet).
**Dependence / limitations:** RPKM/TPM cannot be numerically mixed; expression timing is not causal adult function; age-window averages weight samples rather than donors.
**Rights/access:** Allen Institute research/noncommercial terms; downstream BrainSpan columns retain restrictions; not CC-BY or MIT. [Official source](https://alleninstitute.org/legal/terms-of-use).
**Provenance:** [data/raw/brain_expression/PROVENANCE.json](data/raw/brain_expression/PROVENANCE.json).

### Open Targets Genetics / Platform 26.06 (`opentargets`)

Open Targets Genetics / Platform 26.06 (versioned resource). *Open Targets Genetics / Platform 26.06 (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Credible sets, locus-to-gene features, molecular colocalisation. Aggregated source studies.
**Population / N:** Underlying heterogeneous GWAS and QTL studies; N/ancestry per study. 979 cognition credible sets in refresh; 755 positional top L2G calls; counts are not people.
**Obtained and used:** API/Parquet credible sets, L2G/SHAP features, QTL joins. Fine-mapping support and competing gene labels.
**Implementation:** [pipelines/gene_tournament/fetch_gwas_credible_sets.py](pipelines/gene_tournament/fetch_gwas_credible_sets.py), [pipelines/sprint5a/opentargets_credible_set_refresh.py](pipelines/sprint5a/opentargets_credible_set_refresh.py).
**Dependent outputs:** [reports/sprint5a/opentargets_2606_refresh.parquet](reports/sprint5a/opentargets_2606_refresh.parquet).
**Dependence / limitations:** Distance-driven L2G is not biological evidence; constituent datasets overlap project inputs.
**Rights/access:** Open Targets/source terms retained; no blanket relicensing of upstream study data. [Official source](https://platform.opentargets.org/).
**Provenance:** [data/sprint5a/opentargets_2606_provenance.json](data/sprint5a/opentargets_2606_provenance.json).

### AlphaGenome Atlas 0.9.0 (`alphagenome`)

AlphaGenome Atlas 0.9.0 (versioned resource). *AlphaGenome Atlas 0.9.0 (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** In-silico predicted regulatory effects, not measured human phenotypes. Variant selection from credible sets.
**Population / N:** Model trained on molecular data; no project participant sample. 317 cognition variants + 53 math variants; 532 variant-allele queries for cognition.
**Obtained and used:** Cached prediction summaries; raw 1,681,704 prediction rows not committed. Historical regulatory support; excluded from release gene voting after sign defect.
**Implementation:** [pipelines/sprint5/alphagenome_query.py](pipelines/sprint5/alphagenome_query.py), [pipelines/sprint5a/alphagenome_summarise.py](pipelines/sprint5a/alphagenome_summarise.py).
**Dependent outputs:** [reports/sprint5a/alphagenome_variant_predictions.parquet](reports/sprint5a/alphagenome_variant_predictions.parquet), [data/release/correction_changes.csv](data/release/correction_changes.csv).
**Dependence / limitations:** Signed aggregation defect; gene-only comparator joins also insufficient to validate variant-specific direction; no end-to-end corrected rerun.
**Rights/access:** Service/noncommercial terms in historical protocol; no new predictions or API access; historical files carry source terms and unresolved status. [Official source](https://www.alphagenomedocs.com/).
**Provenance:** [data/sprint5a/alphagenome_provenance.json](data/sprint5a/alphagenome_provenance.json), [docs/corrections/ALPHAGENOME_DIRECTION.md](docs/corrections/ALPHAGENOME_DIRECTION.md).

### PolyFun functional priors (`polyfun`)

Weissbrod O et al. (2020). *Functionally informed fine-mapping and polygenic localization of complex trait heritability.*. [DOI](https://doi.org/10.1038/s41588-020-00735-5). Full author metadata is in the source manifest.

**Phenotype / selection:** Functional annotations and SNP priors. Reference model.
**Population / N:** Published UKB-based prior/reference resources; not independent cognition subjects. Five variants cross PIP 0.5 only under priors.
**Obtained and used:** Published approach-1 priors; SuSiE inputs. Sensitivity fine-mapping.
**Implementation:** [pipelines/sprint5a/polyfun_susie.py](pipelines/sprint5a/polyfun_susie.py), [pipelines/sprint5a/polyfun_susie.R](pipelines/sprint5a/polyfun_susie.R).
**Dependent outputs:** [reports/sprint5a/functional_finemapping_summary.csv](reports/sprint5a/functional_finemapping_summary.csv).
**Dependence / limitations:** Prior-only PIP support never counted as primary coding evidence.
**Rights/access:** MIT repository per audited provenance; data-specific terms still apply. [Official source](https://github.com/omerwe/polyfun).
**Provenance:** [data/raw/sprint5a/polyfun/PROVENANCE.json](data/raw/sprint5a/polyfun/PROVENANCE.json).

### PoPS feature matrix (`pops`)

Weeks EM et al. (2023). *Leveraging polygenic enrichments of gene features to predict genes underlying complex traits and diseases.*. [DOI](https://doi.org/10.1038/s41588-023-01443-6). Full author metadata is in the source manifest.

**Phenotype / selection:** Polygenic gene features and expression/pathway annotations. Reference features.
**Population / N:** Reference annotations, not a new participant cohort. 57,742 features; 550 genes in 159 target loci; 158 loci scored.
**Obtained and used:** Feature matrices acquired externally; LOCO scores committed. Orthogonal gene-priority sensitivity, never a V2G vote.
**Implementation:** [pipelines/sprint5a/pops_prep.py](pipelines/sprint5a/pops_prep.py), [pipelines/sprint5a/run_pops.sh](pipelines/sprint5a/run_pops.sh), [pipelines/sprint5a/pops_collect.py](pipelines/sprint5a/pops_collect.py).
**Dependent outputs:** [reports/sprint5a/pops_scores.csv](reports/sprint5a/pops_scores.csv).
**Dependence / limitations:** 94/158 loci have one scored gene; rankings there uninformative; reuses Davies MAGMA.
**Rights/access:** External code GPL-3.0; matrix has no separate licence established, not redistributed; project-authored wrappers MIT. [Official source](https://github.com/FinucaneLab/pops).
**Provenance:** [data/raw/sprint5a/pops/PROVENANCE.json](data/raw/sprint5a/pops/PROVENANCE.json), [research/sprint5a/agentC_notes.md](research/sprint5a/agentC_notes.md).

### 1000 Genomes EUR / UKB LD / LDetect (`ld_reference`)

1000 Genomes EUR / UKB LD / LDetect (versioned resource). *1000 Genomes EUR / UKB LD / LDetect (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Linkage disequilibrium reference. Reference panels.
**Population / N:** European reference samples; mismatch to every GWAS cohort possible. Reference-specific N; not study N.
**Obtained and used:** External PLINK reference and UKB LD matrices; LDetect block intervals committed. LD loci, SuSiE, LAVA and sensitivity.
**Implementation:** [pipelines/sprint4/loci_tools.py](pipelines/sprint4/loci_tools.py), [pipelines/sprint5a/ukb_ld_sensitivity.py](pipelines/sprint5a/ukb_ld_sensitivity.py).
**Dependent outputs:** [data/gene_tournament/ld_loci.parquet](data/gene_tournament/ld_loci.parquet), [reports/sprint5a/functional_finemapping_summary.csv](reports/sprint5a/functional_finemapping_summary.csv).
**Dependence / limitations:** LD mismatches and numerical regularisation; no participant PLINK genotype files distributed.
**Rights/access:** Download reference panels under their terms; only block intervals and derived statistics bundled. [Official source](https://www.internationalgenome.org/).
**Provenance:** [data/raw/sprint5a/ukb_ld/PROVENANCE.json](data/raw/sprint5a/ukb_ld/PROVENANCE.json).

### GWAS Catalog cognition discovery inventory (`gwas_catalog`)

GWAS Catalog cognition discovery inventory (versioned resource). *GWAS Catalog cognition discovery inventory (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** 22 cognition-related trait channels; EA, ageing and MTAG separated. Published studies; some clinical/ageing or proxy only.
**Population / N:** Heterogeneous source populations; ancestry strings per study. 419 study metadata records in tournament; 834-study later search inventory.
**Obtained and used:** Study metadata JSONL and association API snapshots. Study classification, strict independent units and candidate source discovery.
**Implementation:** [pipelines/gene_tournament/classify_studies.py](pipelines/gene_tournament/classify_studies.py), [pipelines/gene_tournament/fetch_study_metadata.py](pipelines/gene_tournament/fetch_study_metadata.py).
**Dependent outputs:** [data/gene_tournament/study_metadata.jsonl](data/gene_tournament/study_metadata.jsonl), [reports/gene_tournament/cognitive_breadth.csv](reports/gene_tournament/cognitive_breadth.csv).
**Dependence / limitations:** Being found by search does not mean a full GWAS was analysed; incomplete metadata and cohort overlap.
**Rights/access:** Catalog metadata EBI terms; summary statistics accession-specific CC0/legacy terms; dates and original studies retained. [Official source](https://www.ebi.ac.uk/gwas/docs/faq/).
**Provenance:** [data/raw/MANIFEST.jsonl](data/raw/MANIFEST.jsonl), [data/gene_tournament/study_metadata.jsonl](data/gene_tournament/study_metadata.jsonl), [data/sprint5/cohort_overlap_ledger.csv](data/sprint5/cohort_overlap_ledger.csv).

### Educational-attainment proxy channel (`ea_proxy`)

Lee JJ et al. (2018). *Gene discovery and polygenic prediction from a genome-wide association study of educational attainment in 1.1 million individuals.*. [DOI](https://doi.org/10.1038/s41588-018-0147-3). Full author metadata is in the source manifest.

**Phenotype / selection:** Education; distinct cognitive-performance sub-study where labelled. Population/consumer genetics cohorts.
**Population / N:** UKB/COGENT/23andMe and other cohorts depending phenotype. 1.1 million is paper-wide EA, not project cognition sample.
**Obtained and used:** Catalog association annotations; no controlled 23andMe summary files. Proxy-only evidence channel, excluded from direct cognition vote.
**Implementation:** [pipelines/gene_tournament/classify_studies.py](pipelines/gene_tournament/classify_studies.py).
**Dependent outputs:** [reports/gene_tournament/math_gene_rank.csv](reports/gene_tournament/math_gene_rank.csv).
**Dependence / limitations:** Education is socially mediated and not intelligence; discovery overlap.
**Rights/access:** Study-specific source terms; controlled files absent. [Official source](https://doi.org/10.1038/s41588-018-0147-3).
**Provenance:** [data/gene_tournament/study_metadata.jsonl](data/gene_tournament/study_metadata.jsonl), [data/sprint5a/phenotype_datasets.csv](data/sprint5a/phenotype_datasets.csv).

### Gene Ontology / Reactome / SynGO / HPA (`pathways`)

Gene Ontology / Reactome / SynGO / HPA (versioned resource). *Gene Ontology / Reactome / SynGO / HPA (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Pathway, synaptic and cell-expression annotations. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Competitive gene-set analysis and covariate conditioning.
**Implementation:** [pipelines/gene_tournament/run_pathway_enrichment.py](pipelines/gene_tournament/run_pathway_enrichment.py), [pipelines/sprint3_1/run_recon_magma.py](pipelines/sprint3_1/run_recon_magma.py).
**Dependent outputs:** [reports/gene_tournament/pathway_enrichment.csv](reports/gene_tournament/pathway_enrichment.csv), [reports/sprint3_1/SYNAPTIC_RECON_REPORT.md](reports/sprint3_1/SYNAPTIC_RECON_REPORT.md).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** GO/Reactome/SynGO/HPA retain individual attribution/licence terms in provenance; no blanket data licence. [Official source](https://www.syngoportal.org/).
**Provenance:** [data/raw/pathway_annotations/PROVENANCE.json](data/raw/pathway_annotations/PROVENANCE.json).

### HGNC / Ensembl / NCBI taxonomy / GENCODE (`identifiers`)

HGNC / Ensembl / NCBI taxonomy / GENCODE (versioned resource). *HGNC / Ensembl / NCBI taxonomy / GENCODE (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Gene IDs, gene models, orthology and species taxonomy. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Stable identifiers and cross-species mapping.
**Implementation:** [scripts/fetch_gene_identifiers.py](scripts/fetch_gene_identifiers.py), [pipelines/sprint5a/gencode_id_map.py](pipelines/sprint5a/gencode_id_map.py).
**Dependent outputs:** [data/raw/magma_x01/2026-09-22/gene_id_map.tsv](data/raw/magma_x01/2026-09-22/gene_id_map.tsv).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** Resource-specific reuse/attribution terms; no participant data. [Official source](https://www.genenames.org/).
**Provenance:** [data/raw/MANIFEST.jsonl](data/raw/MANIFEST.jsonl), [data/raw/sprint5a/gencode/PROVENANCE.json](data/raw/sprint5a/gencode/PROVENANCE.json).

### ClinGen / gnomAD / Gene2Phenotype (`safety`)

ClinGen / gnomAD / Gene2Phenotype (versioned resource). *ClinGen / gnomAD / Gene2Phenotype (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Dosage sensitivity, loss-of-function constraint and disease annotations. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Safety/constraint context only; not proof of safe gain.
**Implementation:** [pipelines/sprint5/build_rare_coding_tables.py](pipelines/sprint5/build_rare_coding_tables.py).
**Dependent outputs:** [reports/sprint5/rare_coding_evidence.csv](reports/sprint5/rare_coding_evidence.csv).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** Resource terms retained; DDG2P dump and participant genotypes not bundled. [Official source](https://search.clinicalgenome.org/kb/gene-dosage).
**Provenance:** [data/raw/sprint5/rare_coding/PROVENANCE.json](data/raw/sprint5/rare_coding/PROVENANCE.json).

### STRING interactions (`string`)

STRING interactions (versioned resource). *STRING interactions (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Protein functional associations. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Gene-module construction.
**Implementation:** [pipelines/gene_tournament/build_modules.py](pipelines/gene_tournament/build_modules.py).
**Dependent outputs:** [reports/gene_tournament/biological_modules.csv](reports/gene_tournament/biological_modules.csv).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** Source-specific terms; scores indicate functional association, not causal interaction. [Official source](https://string-db.org/).
**Provenance:** [data/raw/string/2026-09-22/PROVENANCE.json](data/raw/string/2026-09-22/PROVENANCE.json).

### PubMed / ClinicalTrials.gov / ChEMBL / Open Targets target annotations (`foundational`)

PubMed / ClinicalTrials.gov / ChEMBL / Open Targets target annotations (versioned resource). *PubMed / ClinicalTrials.gov / ChEMBL / Open Targets target annotations (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Published mechanistic, intervention, comparative and registry evidence. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Foundational atlases, null/negative evidence and pharmacology gates.
**Implementation:** [scripts/fetch_source_metadata.py](scripts/fetch_source_metadata.py), [pipelines/integration/fetch_target_annotations.py](pipelines/integration/fetch_target_annotations.py).
**Dependent outputs:** [reports/project_truth_table.md](reports/project_truth_table.md), [reports/red_team_audit_v0_1.md](reports/red_team_audit_v0_1.md).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** Bibliographic facts/registry summaries and curated annotations; third-party source terms; unnecessary contact details removed. [Official source](https://clinicaltrials.gov/).
**Provenance:** [data/raw/MANIFEST.jsonl](data/raw/MANIFEST.jsonl).

### SMPY / Duke TIP and Ciba 1993 volume (`historical`)

SMPY / Duke TIP and Ciba 1993 volume (versioned resource). *SMPY / Duke TIP and Ciba 1993 volume (versioned resource; no single study publication assigned)*. Full author metadata is in the source manifest.

**Phenotype / selection:** Historical psychometrics and phenotype definition. Reference/curated literature.
**Population / N:** Not a new human cognitive cohort. Not applicable; any original-study N stays attached to its source.
**Obtained and used:** Public annotations or source metadata; per-file acquisition records. Motivation and restriction-of-range context, not genetic evidence.
**Implementation:** [research/sprint5a/historical_foundations.md](research/sprint5a/historical_foundations.md).
**Dependent outputs:** [research/sprint5a/phenotype_model.md](research/sprint5a/phenotype_model.md).
**Dependence / limitations:** Do not count related databases as independent evidence. Full citation-level source records remain in atlases and provenance..
**Rights/access:** Copyrighted literature not bundled; page citations only. [Official source](https://doi.org/10.1111/j.1745-6916.2006.00019.x).
**Provenance:** [research/sprint5a/historical_foundations.md](research/sprint5a/historical_foundations.md).

### Braineac2 (`braineac2`)

Guelfi S et al. (2020). *Regulatory sites for splicing in human basal ganglia are enriched for disease-relevant information.*. [DOI](https://doi.org/10.1038/s41467-020-14483-x). Full author metadata is in the source manifest.

**Phenotype / selection:** Expression/splicing QTL in putamen and substantia nigra. Brain donors, not cognition-selected.
**Population / N:** Human basal ganglia postmortem tissue; ancestry per source. Catalogue assay-specific N; 167 tissue samples / 110 donors in current study inventory (older release notes differ).
**Obtained and used:** Regional eQTL Catalogue summary statistics. Adult bulk coloc and direction.
**Implementation:** [pipelines/sprint4/fetch_eqtl_catalogue.py](pipelines/sprint4/fetch_eqtl_catalogue.py), [pipelines/sprint4/gate_c_coloc.py](pipelines/sprint4/gate_c_coloc.py).
**Dependent outputs:** [reports/sprint4/directionality_resolution.csv](reports/sprint4/directionality_resolution.csv).
**Dependence / limitations:** Brain region and assay matter; eQTL Catalogue versions give differing donor inventories; use exact QTD metadata.
**Rights/access:** eQTL Catalogue summary terms; underlying genotypes remain controlled. [Official source](https://www.ebi.ac.uk/eqtl/Studies/).
**Provenance:** [data/raw/sprint4/eqtl_catalogue/PROVENANCE.json](data/raw/sprint4/eqtl_catalogue/PROVENANCE.json), [data/sprint4/eqtl_catalogue_brain_datasets.csv](data/sprint4/eqtl_catalogue_brain_datasets.csv).

## Access-blocked or candidate-only resources

Tan larger family GWAS, full brainSCOPE associations, TGFM controlled GTEx inputs, 23andMe full Gq GWAS, AstraZeneca PheWAS and individual-level rare-variant burden analyses were not completed from those inputs. Other studies in the overlap ledger may have been searched or assessed for eligibility only. Do not label a search hit as a new analysis. [Access queue](reports/sprint5a/USER_ACCESS_REQUIRED.md).

Reacquire exact versions from the recorded source URLs and verify the original hashes; do not silently replace them with current releases. If a missing licence, ancestry or sample-size detail matters to reuse, verify it with the original steward. No new permission is implied by this catalogue. [Reproduction](REPRODUCIBILITY.md) · [Rights](DATA_LICENSE.md).
