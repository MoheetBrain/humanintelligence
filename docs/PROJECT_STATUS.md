# Project Status

*Snapshot 2026-09-22 (UTC) — **Sprint 3 (Gene Tournament) complete and red-teamed.**
Sprints 1 and 2 remain complete. Repository validates with 0 errors / 0 warnings / 3 info;
**879 tests pass, 0 fail**; ownership check clean (819 paths).*

***Sprint-3 headline results***
1. **The cognition gene universe can be ranked, but only coarsely.** A verified gene-level
   analysis of general cognition (MAGMA, Davies 2018, N=282,014) finds 375 Bonferroni genes =
   **159 independent LD loci**. Beyond the top ~20 the consensus ranking is unstable (39 of the
   top 50 have rank intervals reaching past 200; ranks 51+ tie).
2. **Extreme cognition is continuous with ordinary cognition at gene level** — the extreme-IQ
   sample (IQ~170) shows 1.13x the shift pure power-scaling predicts; 121/159 loci agree in sign
   (P=9e-05); 0 genes are significant in the tail. Individual-level commonality is **not
   computable with current access**.
3. **Synaptic biology is the only pathway signal surviving an unbiased, fully conditioned test**
   (6 of 6,200 sets at global FDR, presynaptic/adhesion rather than postsynaptic). Reproduced in an
   overlapping meta-analysis; untested (not refuted) in the only UK-Biobank-free sample. Myelin,
   energy, astrocytes, ion channels, GPCRs, neuromodulators, translation, chromatin: do not survive.
4. **No gene has a directionally resolved adult-brain effect**, and 91% of locus-to-gene calls are
   driven by distance or gene density. The chemistry gate stays closed because there is no
   direction to push in.
5. **The hand-picked seed list fails the genome test**: 1 of 25 seeds passes Bonferroni (CKB).

## Current Stage

**Sprint 3 — Human intelligence gene tournament + biological compression. All parts A–S
delivered**, with explicit NOT_COMPUTABLE records where access blocks a part:

| Part | Deliverable | State |
|---|---|---|
| A | `data/gene_tournament/master_gene_universe.parquet` | done — 9,221 gene strings; EA a separate proxy channel; 419 studies tiered |
| B | `direct_cognition_rank.csv` | done — MAGMA (verified) + Savage + catalog strict units |
| C | `extreme_tail_rank.csv`, `extreme_tail_distribution_stats.csv` | Mode 1 done; **Mode 2 NOT COMPUTABLE** |
| D | `cognitive_breadth.csv` | done — breadth by distinct cohort units (bipartite matching) |
| E | `math_gene_rank.csv` | done — A/B/C separate; **0 math-specific genes identifiable** |
| F | `within_family_rank.csv` | **NOT COMPUTABLE** (OpenGWAS registration; 0 catalog hits) |
| G | `fine_mapping_support.csv` | done — study-first GWAS credible sets + L2G with SHAP drivers |
| H | `adult_brain_directionality.csv` | done — 0 genes direction-resolved at pre-set rule |
| I | two rankings inside the TOP50 files | done — natural vs adult-gated |
| J | `positive_human_perturbations.csv` | done — 2q12.3 corrected; ClinGen as safety |
| K | `pathway_enrichment.csv`, `pathway_hypothesis_panel.csv`, `pathway_replication.csv` | done |
| L | `biological_modules.csv`, `module_report.md` | done — 11 modules; boundaries unstable |
| M | `minimal_control_set.csv` | done — collapses to one gene; no control set |
| N | `TOP50_HUMAN_COGNITION_GENES.csv`, `TOP50_ADULT_MODIFIABLE_GENES.csv` | done — RRA + Borda + Pareto + LODO + bootstrap |
| O | `TOP10_COGNITION_MODULES.csv` | done |
| P | `red_team_top50_*.csv`, `red_team_modules.csv` | done — 19/50 and 16/50 downgraded |
| Q | `GENE_CARDS_TOP50_*.md` | done |
| R | `comparative_top_genes.csv` | **partial** — 30/83 genes (Ensembl REST slow/failing); selection & convergence NOT computed |
| S | 20 questions | answered in `reports/GENE_TOURNAMENT_FINAL.md` |

## Project Objective

Build a fully computational causal-control framework for adult human cognitive capacity:
identify the smallest set of **adult-modifiable biological control parameters** that determine
how much useful computation, learning, abstraction, working memory, transfer and durable
knowledge a healthy adult brain can achieve. Not a nootropics list, not a search for an
"intelligence gene". All work is computational (`docs/COMPUTATIONAL_ONLY_POLICY.md`).

## Current Branch

`sprint-3/gene-tournament`, branched from `sprint-2/causal-bridge` (`daa7354`). Canonical clone:
**`/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠`** (remote
`github.com/MoheetBrain/humanintelligence`). The earlier clone at `/Users/moheet/humanintelligence`
no longer exists. A second, **Codex-owned** linked worktree exists at
`/Users/moheet/Documents/ChatGPT/intelligence-codex` (branch `agent/codex-positive-genetics`,
local and never pushed); it was audited read-only and never modified.

## Current System Architecture

Three linked graph layers compiled from curated records (evidence graph; biological causal graph
Variant → Gene → … → CognitivePhenotype; intervention graph), a blackboard execution model with
disjoint path ownership (`docs/OWNERSHIP.yaml`), and an immutable provenance spine
(`data/raw/` + sha256 `MANIFEST.jsonl`). Storage: curated YAML → Parquet → DuckDB → NetworkX.

**Sprint 3 adds a gene-tournament layer** (`pipelines/gene_tournament/`, orchestrator-owned):

```
GWAS Catalog (22 traits) ─► study tiers ─► master universe ─┐
MAGMA gene analyses (Davies✓, Savage, Zabaneh, FI4) ─► LD blocks ─┼─► per-dimension ranks (B–J)
Open Targets (credible sets/L2G; brain coloc) ────────────────┤         │
GTEx v10 + BrainSpan (timing) ─ ClinGen/gnomAD (dosage) ──────┘         ▼
MAGMA gene-set (GO/Reactome/SynGO, conditioned) ─► pathway panel ─► modules (L) ─► control set (M)
                                                                     └► RRA consensus (N) ─► red team (P) ─► cards (Q)
```

## Capabilities Implemented

* All Sprint 1–2 capabilities (contract v0.1.0 + amendments R1–R20, 33-rule validator,
  provenance tooling, HGNC resolution, ranking/uncertainty model, chemistry gate, registry
  search, discovery sweep, comparative v2, convergence dependency rules, truth table).
* **Sprint 3:**
  * **Independent recomputation of an external analysis**: X01's MAGMA gene layer re-derived from
    the raw 518 MB summary statistics; verdict logic separates deterministic agreement
    (NSNPS/NPARAM) from MAGMA's stochastic permutation noise.
  * **Study-level evidence tiers** (strict / MTAG / clinical-ageing / excluded EA-or-cross-trait /
    proxy) so EA cannot leak into direct cognition through trait labels.
  * **LD-aware locus blocks** from MAGMA gene–gene correlations.
  * **Extreme-tail continuity test** with power-scaling prediction and size-matched permutation.
  * **Conditioned competitive gene-set analysis** (size, density, LD, annotation density, LoF
    constraint) with **global FDR** and cross-dataset replication.
  * **Study-first fine-mapping** with L2G SHAP-driver classification (positional vs biological).
  * **Directionality rule** requiring cross-colocalisation sign agreement with trait polarity.
  * **Rank aggregation**: RRA, Borda, Pareto, leave-one-dimension-out, dimension bootstrap.
  * **Module compression** (Louvain/hierarchical/NMF, bootstrap, leave-source-out, leave-study-out).
  * `make tournament` rebuilds Parts A–Q from committed inputs.

## Work Completed to Date

1. **Sprint 1** (complete): scaffolding, contracts, four evidence atlases, type system, ranking
   model, red-team audit, graph layer, reports; `tier_1_analyse_next` empty.
2. **Sprint 2** (complete): registry searches (1,534 studies after fixing three pipeline defects),
   discovery sweep, 2q12.3 watchlist, comparative v2, convergence layer, truth table (39 rows), X02
   ingestion readiness, two theory nodes.
3. **Sprint 3** (complete, this branch):
   * Located the real work location; restored the canonical tree; rebuilt the gitignored identifier
     index offline and added it to `make build`.
   * **Found the Codex/Astra branch** Sprint 2 declared nonexistent; audited it read-only;
     independently verified X01's gene-level layer; corrected the audit, the X01 record and the
     GRM3/ADGRB1/GABBR1 attribution.
   * Built Parts A–S (table above) and the final report `reports/GENE_TOURNAMENT_FINAL.md`.
   * **Corrected the 2q12.3 atlas**: the Sprint-2 gene list came from the hg38 cytoband for an hg19
     label; the verified duplication is EDAR/SH3RF3/SEPTIN10/SOWAHC.
   * Applied a **Sprint-3 layer to the truth table** (7 status changes; seed rows gain verified
     gene-level results).

## Important Files and Artifacts

| Path | Role |
|------|------|
| `reports/GENE_TOURNAMENT_FINAL.md` | Sprint-3 final report (A–J, Part S, limits, robustness, downgrades) |
| `reports/gene_tournament/` | all per-part outputs, gene cards, red-team tables, module report |
| `data/gene_tournament/master_gene_universe.parquet` | Part A universe with per-channel and strict-tier provenance |
| `data/gene_tournament/study_classification.csv` | 419 studies tiered |
| `data/raw/magma_x01/2026-09-22/REPLICATION_CHECK.json` | X01 gene-layer verification |
| `data/raw/magma_sprint3/2026-09-22/` | committed MAGMA outputs (Savage, Zabaneh, FI4, Davies re-run) + provenance |
| `atlases/gene_tournament/phenotype_channels.yaml` | phenotype channel map; EA as proxy |
| `atlases/positive_genetics/2q12_3_duplication.yaml` | corrected (v0.3.0) |
| `analyses/external/X01_cell_type_enrichment.yaml` | corrected; artefacts_received_pending_check |
| `docs/integration/CODEX_BRANCH_AUDIT.md` | Sprint-2 verdict superseded by a correction block |
| `reports/project_truth_table.{md,csv}` | 39 rows with Sprint-3 layer |
| `docs/blackboard/RESOLUTIONS.md` | R1–R20 (R20: X01 test invariant; pipelines/reports ownership) |

## Data Sources and Provenance

| Source | Access | Use in Sprint 3 |
|--------|--------|--------|
| GWAS Catalog REST v2 (release 2026-09-13) | public | 22 traits, 33,506 associations, 419 study records — snapshotted |
| Davies 2018 open subset (Edinburgh DataShare) | public, CC-BY-4.0 | MAGMA input; sha256 recomputed (518 MB, not stored) |
| Savage 2018, Zabaneh 2018, UKB FI4 (GWAS Catalog FTP) | public | MAGMA inputs; checksums recorded (not stored) |
| MAGMA v1.10 + 1000G EUR | public (binary not redistributable) | used from the Codex worktree |
| Open Targets Platform 26.06 | public | credible sets, L2G + SHAP, brain QTL colocalisation |
| GTEx v10 median TPM; BrainSpan | public (BrainSpan non-commercial) | developmental classification |
| NCBI gene2go, GO, Reactome 97, SynGO 1.3, HPA v25.1 | public | pathway sets; HPA brain cell specificity |
| STRING v12 | CC BY 4.0 | module graph (FDR<0.01 genes) |
| ClinGen dosage (FTP, 2026-09-22) | public | safety flags; 2q12.3 recheck |
| gnomAD v2.1.1 constraint | public | covariate and safety |
| HGNC complete set | public | symbol verification |
| EuropePMC full text (PMC11701252) | open access | 2q12.3 verification |
| Ensembl Compara REST | public | Part R orthology (partial) |

Bulk raw downloads over the 5 MiB commit limit are kept out of git; each has URL + sha256 in a
committed `PROVENANCE.json`.

## Decisions and Rationale

* **Gene-based test over catalog counts** for direct cognition — counts measure gene length and
  study attention; MAGMA conditions on neither but tests signal properly per gene.
* **A gene is not a finding; an LD block is.** Every "number of genes" is reported with its block count.
* **EA separated at study level, not only trait level.**
* **Global FDR is primary** for pathways (within-collection FDR favoured the small SynGO family).
* **A dimension enters the primary consensus only if ≥1 gene passes its own multiple-testing
  threshold; safety is a flag, never a promoting dimension.** Adopted *after* an all-dimensions run
  was dominated by near-noise dimensions — disclosed as such; all-dimensions ranks retained.
* **Direction requires ≥3 strong gene-level brain colocalisations with ≥80% polarity-adjusted sign
  agreement** — set after the first version's single-best-coloc rule proved self-contradicting.
* **Nearest gene is never sufficient**: L2G calls dominated by distance/gene-density SHAP features
  do not count as support.
* **Codex branch: read-only.** Its results were verified by recomputation, not by trust.

## Verification and Test Results

All executed 2026-09-22; none projected.

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `PYTHONPATH=src .venv/bin/python -m pytest -q -m "not network"` | **879 passed, 0 failed** (81.9 s) |
| Tournament guard tests | `pytest pipelines/gene_tournament/test_gene_tournament.py` | 27 passed |
| Validator | `PYTHONPATH=src .venv/bin/python graph/validate_graph.py --strict` | **PASS** — 0 error, 0 warning, 3 info |
| Ownership | `PYTHONPATH=src .venv/bin/python scripts/check_ownership.py` | all 819 paths owned as expected |
| X01 gene-layer recomputation | `ingest_magma_gene_analysis.py --replication …matched.genes.out` | REPRODUCED_WITHIN_MONTE_CARLO_ERROR (NSNPS/NPARAM identical for 18,418 genes; Spearman 0.9999995; 4 genes flip Bonferroni) |
| Input checksum | `shasum -a 256 davies2018_open_complete.txt` | matches recorded 01990c3e…ca6573 |
| Savage checksum | `md5` vs publisher CHECKSUM file | match (fa7e947e…) |
| GWAS fetch completeness | page audit | 22/22 traits read to exhaustion |
| Open Targets coloc run | `fetch_opentargets_coloc.py` | 400/400 genes ok, 0 errors |
| Open Targets GWAS credible sets | `fetch_gwas_credible_sets.py` | 118 studies ok, 3 not in Open Targets; 2,013 credible sets |
| Offline identifier rebuild | `scripts/fetch_gene_identifiers.py --offline` | 31/31 resolved (fixed 2 graph-test failures on fresh clone) |

## Known Failures and Limitations

* **Within-family evidence absent** (Part F not computable).
* **Individual-level extreme-IQ analysis absent** (Mode 2 not computable).
* **All gene-level statistics European-ancestry; ancestry sensitivity not computable.**
* **Davies and Savage share UK Biobank** — cross-meta agreement is reproducibility, not replication;
  the only UKB-free gene-level statistic (Zabaneh) is 65x underpowered.
* **Possible HRS/CHARGE sample overlap** between Zabaneh controls and Davies is unresolved.
* **Part R partial** (30/83 genes); selection and convergence not computed.
* **Module boundaries are method-dependent** (cross-method ARI 0.19–0.24).
* **Consensus ranks beyond ~20 are unstable**; the top-50 files show intervals and ties.
* 122 MAGMA Entrez IDs without a current symbol are excluded from the consensus (1 Bonferroni).
* The X01 **cell-type layer** is not yet re-derived here.
* Catalog study classification is rule-based; memory studies without a cohort field in ageing
  cohorts can escape the clinical tier (APOE's appearance is a symptom, flagged by the red team).

## Risks and Technical Debt

| Risk | Status |
|------|--------|
| Codex worktree is local-only; its 9.5 GB of inputs are unversioned | recorded; checksums carried here for the inputs this repo used |
| MAGMA binary lives outside this repo (licence forbids vendoring) | `make tournament` uses committed MAGMA outputs; re-running MAGMA needs the binary |
| Several dimensions are coarse/tied (module, adult modifiability) | disclosed via `carried_by` and tie notes |
| Convergence dependency rules (D001–D009) still unenforced by a validator rule | carried from Sprint 2 |
| 17q21.31 inversion and 6p22/MHC regions produce non-gene-specific colocalisation | flagged in Part H and the red team |
| Several MCP connectors unauthorised (GitHub, Synapse, Wiley, etc.) | not needed this sprint |

## Current Blockers

* **No UKB-free, adequately powered cognition GWAS in open access** — blocks independent replication
  of the synaptic finding, continuity, and every top gene.
* **Within-family data require an OpenGWAS registration**, which this project does not make on its
  own authority.
* **Ensembl Compara REST is intermittently failing** (Part R partial).
* No directed causal gene graph exists, so controllability analysis is not meaningful.

## Exact Next Actions

1. **UKB-free replication** of the six synaptic sets and of the continuity result (CHARGE/COGENT
   components by application, or within-sibship data via a free OpenGWAS registration — the user's
   call). Highest expected value: one computation tests the sprint's three central claims.
2. **Re-derive X01's cell-property layer** here (MAGMA `--gene-covar` on the cell-type matrices),
   completing its verification.
3. **Resume Part R** when Ensembl recovers: `PYTHONPATH=src .venv/bin/python pipelines/gene_tournament/comparative_top_genes.py`
   (snapshots are reused), then build the species tree + trait covariates Sprint 2 left as prerequisites.
4. **SuSiE-coloc on eQTL Catalogue brain datasets** (tabix byte-range reads) for the near-miss
   direction genes (NEGR1, SYT1), to test whether any gene reaches the direction rule.
5. **Resolve HRS/CHARGE overlap** for the continuity test.
6. **Encode convergence rules D001–D009 as a validator rule** (Sprint-2 debt).
7. Merge `sprint-2/causal-bridge` and `sprint-3/gene-tournament` into `main` when reviewed
   (`main` still holds only the initial commit).
