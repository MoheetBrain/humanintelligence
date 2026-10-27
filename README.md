# Hamiltonian Labs — Human Cognition Genetics

**An open computational framework for investigating the genetic and molecular mechanisms of human cognitive capacity.**

Can human cognitive genetics identify plausible biological mechanisms that remain modifiable after neuronal maturation? This research programme follows published genetic associations through candidate genes, molecular regulation, brain cell types and developmental timing. The purpose is to identify testable hypotheses and the evidence still missing between inherited differences and an adult biological mechanism.

**No intelligence-enhancing intervention, IQ increase or cognitive-enhancement treatment has been demonstrated.** This is computational, hypothesis-generating research. The intervention gate remains closed.

Maintained by **[MoheetBrain](https://github.com/MoheetBrain)**, **[Hamiltonian Labs](https://www.hamiltonianlabs.co/)**. Initial curated public release: **v0.1.0**, 27 October 2026; scientific execution snapshot: 24 September 2026.

## Start here

| Question | Read |
|---|---|
| What was done? | [Methodology and implementation](METHODOLOGY.md) |
| Which people, phenotypes and sources? | [Datasets, overlap and rights](DATASETS.md) |
| What survives the audit? | [Results](RESULTS.md) and [release data index](data/release/README.md) |
| What cannot be concluded? | [Limitations and corrections](LIMITATIONS.md) |
| What can I reproduce? | [Reproducibility](REPRODUCIBILITY.md) |
| Where is the earlier research? | [Research history](CHANGELOG.md), [Sprint 5A report](reports/sprint5a/SPRINT5A_FINAL.md), [foundational truth table](reports/project_truth_table.md) |

## Evidence at a glance

| Stage | Verified committed result | Interpretation |
|---|---|---|
| Earlier genome-wide gene screen | 18,418 genes; 375 Bonferroni-significant genes in 159 LD-defined loci | Associated genes are correlated within loci; they are not 375 established causal genes. |
| Within-family comparison | 109/146 testable lead alleles concordant; 13/159 untestable | Aggregate directional support; only 34 loci meet the historical direct-support class. Shared cohorts limit independence. |
| Sprint 5A locus integration | 152 signals: 11 L1, 27 L2, 63 L3, 42 discordant, 9 untestable | A different denominator from the 159-locus screen. Locus labels are not causal-gene names. |
| Gene adjudication | 531 assessment rows (including a FOCUS null-model placeholder); DNPH1, TTBK1 and FAM131A moderate; **0 high-confidence genes** | Competing assignments and limited molecular evidence remain. |
| Adult candidate gate | **0 D1 gene directions; 0 qualifying adult candidates** | Adult expression or colocalisation alone is insufficient. |

The public release excludes AlphaGenome sequence-model votes because the historical directional aggregation applied the raw-score sign twice. A regression-tested code correction and cached-evidence re-adjudication preserve the three moderate candidates and empty adult shortlist. **Historical AlphaGenome agreement counts are withdrawn; complete corrected predictions have not been reproduced.** See the [correction](docs/corrections/ALPHAGENOME_DIRECTION.md).

## Data and populations

The primary discovery input is the **282,014-participant public subset** of Davies et al. general cognitive function (the full publication reports 300,486). Supporting sources include Savage intelligence (269,867), a Duke TIP exceptional-intelligence case-control GWAS (1,238 cases, 8,172 controls), Howe within-sibship estimates, Genes & Cognition executive function, GenLang performance IQ, UK Biobank arithmetic items and 53 published Giannelis mathematical-factor variants.

Most cognition discovery evidence concerns people of European ancestry. Hamiltonian Labs did not recruit or identify exceptional individuals. It analysed published summary resources. General cognition, executive function, performance IQ, mathematics self-report and educational attainment are distinct phenotypes. UKB, HRS and BATS overlap several GWAS; ROSMAP/CommonMind donors recur across molecular resources. These datasets cannot be added up as independent participants or replications. [Study definitions and citations](DATASETS.md).

## Computational approach

The implemented work combines GWAS harmonisation, MAGMA gene/set tests, LD-aware loci, within-family comparisons, SuSiE/PolyFun sensitivity fine-mapping, bulk and single-cell brain eQTL colocalisation, FOCUS, developmental context, LDSC, Genomic SEM, LAVA, HyPrColoc, PoPS and rare-coding evidence. An evidence graph records shared inputs and separates association, gene attribution and direction. Frozen project protocols, dated corrections and negative findings are retained. These were repository protocol freezes, not an externally registered clinical or experimental study.

The early claim of uniquely presynaptic enrichment was corrected: broader neuronal/developmental covariates and annotation propagation matter. No common–rare convergence or replicated positive-dosage enhancement mechanism was established. Missing tests are labelled untestable rather than negative.

## Inspect and reproduce

[Release tables](data/release/README.md) include the complete corrected gene evidence matrix, locus confidence, uncertainty, excluded evidence and an intentionally empty adult-candidate CSV. Historical Sprint 5 top-ten and “top-twenty” tables remain accessible with explicit status; the latter actually contains **25 entries** from two Pareto layers.

```bash
git clone https://github.com/MoheetBrain/humanintelligence.git
cd humanintelligence
git checkout v0.1.0
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-release-lock.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python scripts/release/smoke.py
```

The smoke check is offline and does not download data. [Detailed reproduction](REPRODUCIBILITY.md) distinguishes output verification, cached-evidence re-adjudication and expensive/restricted upstream analyses. This release **does not claim an end-to-end independent reproduction**.

## Citation, contribution and rights

Use [CITATION.cff](CITATION.cff) and cite the original datasets/methods. No project DOI has been issued; [Zenodo instructions](docs/ZENODO.md) describe the deposit boundary. This repository is not a peer-reviewed publication.

[Contributions](CONTRIBUTING.md) are welcome on allele alignment, cohort independence, causal-gene alternatives, reproducibility and the AlphaGenome correction. Use GitHub issues for scientific questions and [private reporting](SECURITY.md) for sensitive discoveries.

Project-authored code is [MIT-licensed](LICENSE). Third-party resources retain their own terms; **some data and derivatives are noncommercial or otherwise restricted**. Read [DATA_LICENSE.md](DATA_LICENSE.md) before reuse. The code licence does not relicense those resources.

Programming, literature discovery, evidence curation and historical analyses used AI assistance. The release audit checked source records, tabular counts, code and automated tests, and re-ran the cached classification without suspect model votes. There has been no independent laboratory validation, external replication of the whole pipeline or comprehensive human expert review of every literature annotation. See [validation scope](reports/release/VALIDATION.md) and [security audit](docs/security/AUDIT.md).
