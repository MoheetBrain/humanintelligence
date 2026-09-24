# Project Status

*Snapshot 2026-09-24 (UTC) — **Sprint 5A (open-data exhaustion + causal integration) IN PROGRESS.***

- **Branch.** `sprint-5a/open-data-exhaustion`.
- **Protocol.** `e097067`, frozen before any Sprint-5A result.
- **Interruption.** The machine rebooted at about 09:58Z. The killed jobs were resumed from their on-disk state:
  - the Gate-A calibration (16 of 120 replicates had finished);
  - LAVA;
  - three research agents.

**Done so far:**

- **Open Targets 26.06, re-verified live.** 979 cognition credible sets.
  - The top L2G call is driven by distance or gene density in 755 sets, and by biological features in 224.
  - 126k QTL colocalisations: eQTL, tuQTL, sQTL, single-cell eQTL and pQTL.
- **AlphaGenome Atlas, run with the user's key.** The key was supplied through the environment only.
  - 317 cognition variants and 53 math SNPs queried; 573 strong brain-expression predictions.
  - Against measured human QTLs: 9 agree and 19 disagree (all 28 comparable pairs).
- **Multivariable LDSC across 5 traits.**
  - rg with Davies g: executive function 0.82; PIQ 0.68; extreme IQ 0.87; arithmetic 0.77.
  - A common factor fits (CFI 0.99). Loadings: g 0.97, extreme IQ 0.88, arithmetic 0.79, executive function 0.79, PIQ 0.74.
  - Significant trait-specific genetic variance for arithmetic (0.37) and PIQ (0.45); none for extreme IQ (0.22, P = 0.19).
- **Phenotype model, canonical inputs and historical foundations** written up.
- **USER_ACCESS_REQUIRED** drafted.

**Running:**

- Gate A: frozen within-family analysis, post-data calibration.
- LAVA local genetic correlation.
- brainSCOPE typed evidence, PsychENCODE developmental data and the GTEx V11 audit.
- Single-cell eQTL colocalisation and multi-trait colocalisation.
- PolyFun fine-mapping and PoPS.

*Previous snapshot below (Sprint 5 complete).*

*Snapshot 2026-09-23 (UTC) — **Sprint 5 (Human Cognition Causal Gene Resolution) COMPLETE. Loci are
real; the causal gene is unresolved at every strong locus. No adult direction is resolved for a credible
gene. Chemistry / intervention gate CLOSED.** Branch `sprint-5/causal-cognition-gene-resolution` (from
`sprint-4/causal-synapse-bridge` @ `e50eb4f`; protocol freeze `1a08f10`). Not merged to main.
Sprints 1–4 complete.*

***Sprint-5 headline results*** (evidence: `reports/sprint5/SPRINT5_FINAL.md`)

1. **Locus confidence (frozen Bayes factor; G&C is the only counted UKB-free lineage).** 152 signals.
   - **L1 (strong):** ATXN2L (16p11.2) and AKAP6 (14q12).
   - **L2 (moderate):** 14 signals — NT5DC2, SFMBT1, DPP4, BTN2A1, EXT1, EXOC4, DCC, KCNJ3, SLC39A8, DDN, NKIRAS1, FOXO6, UBE2E1, ZSCAN31.
   - **Other strata:** L3 75; discordant 49; not testable 12.
   - Rank intervals are wide.
   - **GenLang performance IQ** (N 18.7k) replicates the locus set (106/141, slope 0.17). It shares the BATS cohort with Davies, so it is sensitivity only.
2. **Gene assignment.** No CAUSAL_GENE_HIGH gene.
   - **CAUSAL_GENE_MODERATE:** KIFC2 and DNPH1, both at weak (L3) loci, via brain enhancer–gene links plus adult eQTL colocalisation.
   - **At the L1 loci the gene is unresolved:** TUFM/EIF3C/SH2B1 at 16p11.2; AKAP6/NPAS3 at 14q12.
   - **Open Targets 26.06** (still the current release): 117 of 130 L2G calls are positional.
   - **Strongest single arrow:** SLC39A8 A391T (missense, PIP ≈ 1). GenLang is sign-discordant there, and the knock-in mouse is null.
3. **Direction.** No gene reaches D1.
   - RPS26 ↑, RHEBL1 ↑ and WBP2NL ↓ meet the unchanged rule, but each fails gene credibility or locus replication.
   - **brainSCOPE** (17 DLPFC cell types): colocalisation NOT_TESTABLE (public data are significant-only). Tagging: RPS26 ↑ and WBP2NL ↓ (10 cell types each), CYP2D6 ↑ (6), DHRS11 ↓ (4). No cell-type discordance.
   - **GRN sensitivity:** RHEBL1 would reach D1 only via a GRN element that links 9 genes. Not counted.
4. **Developmental eQTL.** NT5DC2 ↓ (fetal 0.95), DNPH1 ↓ (3 datasets), RHEBL1 ↑, CLCN2 ↑.
5. **Rare coding.** KDM5B, ANKRD12, RC3H2 and CACNA1A: UK Biobank only, loss of function only. No common–rare convergence (T1–T5 null, underpowered). No positive-dosage evidence replicates: 2q12.3 is nominal.
6. **Math-53** (Giannelis 2025; verified). A self-report factor, orthogonal to g by construction; mostly inverted against g. The only gene overlap is SLC39A8, via the same variant.
7. **Access-blocked, all NOT_TESTABLE:**
   - AlphaGenome (API key);
   - Gate A (JWT);
   - brainSCOPE colocalisation (Synapse);
   - TGFM (dbGaP);
   - 23andMe math summary statistics.
8. **Defect fixed.** The Sprint-4 KDE-Tweedie shrinkage was unstable in the tail and was replaced by empirical-Bayes shrinkage (amendment A2). A Sprint-4 correction block was added; no decision changed.

***Sprint-4 headline results*** (evidence: `reports/sprint4/CAUSAL_SYNAPSE_GATE.md`)
1. **Gate A (within-sibship, Howe 2022) NOT_TESTABLE** — `OPENGWAS_JWT` absent; no account created. All
   code to the download boundary is written and tested; one user action unlocks it.
2. **Frozen pre-data power calibration (320 LD-aware subsampled GWAS, 40 per scenario)**: set-level
   enrichment power at N 5–10k is 2–12.5% even for a fully direct effect — indistinguishable from the null.
   The locus-level sign test is ~100% powered. So Gate A will decide the loci, not the sets.
3. **Gate B (independent UKB-free Genes & Cognition, N=9,932, executive function)**: pipeline positive
   control NT5DC2 rs7639267 PASS; **109/145 Sprint-3 lead alleles concordant (P=5e-10; slope 0.122, SE
   0.014)**; 33 loci G&C_SUPPORTED (~14.5 expected by chance; 4 at FDR<0.05); frozen sets: 1/6 nominal
   (process in the synapse, P=0.031), 4 concordant-underpowered, adhesion sign-discordant within noise.
4. **Gate C**: SuSiE on 36 loci; 648 adult-brain QTL files (GTEx, CommonMind, ROSMAP, Braineac2, Young
   2019; BrainSeq/fetal/iPSC excluded); 4,531 coloc.abf + 590 coloc.susie tests (28 loci); 87 strong. Direction
   resolved under the unchanged rule on independent cohorts: **RPS26**, **RHEBL1** (cognition allele →
   higher expression) and **WBP2NL** (→ lower; likely passenger, FOCUS favours CYP2D6). RPS26 lacks independent cognition support; RHEBL1's gene attribution is unstable in
   FOCUS (primary favours PFKM). NEGR1's best FOCUS model is a pseudogene; SYT1 has no strong gene-level coloc.
5. **Decision RETRY** (frozen precedence: Gate A untestable). Chemistry gate CLOSED.

***Sprint-3.1 headline results*** (evidence: `reports/sprint3_1/SYNAPTIC_RECON_REPORT.md`)
1. **Broad synaptic enrichment survives every covariate specification**, but ~55% of its effect is
   absorbed by generic neuronal expression, and it is **not presynaptic**: direct joint/contrast tests
   show postsynapse ≥ presynapse; release machinery (active zone, vesicle cycle, priming, Ca²⁺-release,
   SNARE) is not enriched. The robust core is **synaptic-membrane / trans-synaptic adhesion** (CDH9,
   PTPRF, CADM2, NCAM1, PTPRD, LRRC4; channels KCNJ3, SCN2A) — nominal after neuronal conditioning and
   leave-one-locus-out.
2. **Two Sprint-3 method defects corrected**: conditioned runs silently dropped 1,349 unannotated genes
   (17,069-gene universe); GO sets were unpropagated. With propagated GO, **neurodevelopmental sets (CNS
   neuron differentiation, neuron migration) also survive global FDR in every specification** — synaptic
   biology is not the only survivor.
3. **Top-50 ranks count one UK-Biobank GWAS lineage several times** (leave-lineage-out keeps 5/50
   natural, 14/50 adult; only MACROD2 has a verified UKB-free cohort unit); a trailing-space bug had
   counted a UKB study as UKB-free.
4. **NEGR1's "3/4" direction evidence is 1 independent unit**; SYT1's 15 colocs are transcript-level
   (0 gene-level). Under strict gene-level eligibility on independent cohorts **RPS26** meets the
   unchanged direction rule (4 adult cohorts; ubiquitous ribosomal eQTL at pleiotropic 12q13.2) — a
   Sprint-4 Gate-C test case, not a target.
5. **"1.13x" continuity withdrawn** (ratio spans 0.61–1.25); "121/159 same sign" was unsigned. A genuine
   allele-direction test: **112/136 concordant (P=4e-15)**, within continuity expectations → "no strong
   evidence for a distinct common-variant architecture". HRS verified inside Davies 2018.
6. **"Adult-modifiable" relabelled ADULT-EXPRESSION-COMPATIBLE**; five-tier adult hierarchy; DCC has
   rodent adult functional evidence despite prenatal-dominant expression; no gene has adult causal evidence.
7. Chemistry gate CLOSED.

*Previous snapshot 2026-09-22 — Sprint 3 complete (below, kept for history; see correction blocks
C1–C13 in `reports/GENE_TOURNAMENT_FINAL.md`).*

***Sprint-3 headline results (2026-09-22; items 2 and 3 CORRECTED by Sprint 3.1)***
1. **The cognition gene universe can be ranked, but only coarsely.** 375 Bonferroni genes = 159 LD loci;
   beyond the top ~20 the consensus is unstable.
2. ~~1.13x continuity; 121/159 same sign~~ → see Sprint 3.1 item 5.
3. ~~Synaptic biology the only surviving pathway; presynaptic not postsynaptic~~ → see Sprint 3.1 items 1–2.
4. **No gene has a directionally resolved adult-brain effect** at the Sprint-3 rule; 91% of locus-to-gene
   calls positional.
5. **The hand-picked seed list fails the genome test**: 1 of 25 seeds passes Bonferroni (CKB).

## Current Stage

**Sprint 5 — complete.** Outputs are in `reports/sprint5/`: 27 required files plus 20 gene dossiers. The research log is `research/sprint5/research_log.md`.

**Sprint 4 — complete (decision RETRY).** Outputs in `reports/sprint4/` (13 required files + summaries).
coloc.susie complete (28/36 loci; the other 8 have no GWAS SuSiE credible set). TGFM and cTWAS blocked.

**Sprint 3.1 — synaptic recon / correction pass: complete** (`reports/sprint3_1/`, 7 required outputs
+ supporting tables; 13 dated correction blocks written into Sprint-3 reports without deleting text).
**Sprint 4 — protocol frozen; analyses pending** (Gate A blocked: `OPENGWAS_JWT` absent; Gate B inputs
downloaded, md5-verified; pre-data power calibration script prepared).

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

`sprint-5/causal-cognition-gene-resolution` (Sprint 5 complete; from `e50eb4f`; protocol freeze `1a08f10`).

`sprint-4/causal-synapse-bridge` (Sprint 4 complete; contains Sprint 3.1 via merge `a8e82d4`).

`sprint-3.1/synaptic-recon` (Sprint 3.1), branched from `sprint-3/gene-tournament` at `04c70ef`.
`sprint-4/causal-synapse-bridge` (`db86aef`, protocol freeze) also branches from `04c70ef` and will
merge Sprint 3.1 before its analyses. Neither is merged to main.

Previously: `sprint-3/gene-tournament`, branched from `sprint-2/causal-bridge` (`daa7354`). Canonical clone:
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

**Sprint 5** (executed 2026-09-23; commands and results):

| Check | Command | Result |
|---|---|---|
| Full suite | `PYTHONPATH=src .venv/bin/python -m pytest -q -m "not network"` | **947 passed**, 0 failed (≈84 s) |
| Sprint-5 guards | `pytest pipelines/sprint5/test_sprint5.py` | 12 passed. They cover: the rules hash; empirical-Bayes shrinkage is monotone; class invariants; EA proxies never counted; NOT_TESTABLE never recorded as negative; dependency-graph integrity; Top-10/Top-20 columns; the 53 math SNPs; chemistry gate closed; GenLang not counted. |
| Sprint 4 + Sprint 5 guards in both orders | `pytest test_sprint4.py test_sprint5.py` (and reversed) | 33 passed in each order (the module-name collision is fixed) |
| Validator | `graph/validate_graph.py --strict` | **PASS**: 0 errors, 0 warnings, 3 info |
| Ownership | `scripts/check_ownership.py` | all paths owned as expected |
| Pipeline chain | locus_confidence → evidence graph → math V2G → classify → modifiability → AlphaGenome status/convergence → tables → decide | every step exit 0 |
| Reproduction | math53_analysis.py, build_rare_coding_tables.py rerun from the repo | outputs byte-identical |
| GenLang download | md5 against the GWAS Catalog md5sum.txt | match (d59615f3…) |

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

**Sprint 5**

- **Not testable (access):**
  - AlphaGenome (API key);
  - brainSCOPE colocalisation (only significant pairs are public; genotypes on Synapse);
  - Gate A (JWT);
  - TGFM (dbGaP);
  - 23andMe math summary statistics.
- **Only one counted UKB-free replication lineage (G&C, N 9.9k, trail making).** GenLang, CHIC and Zabaneh all overlap Davies.
- **Rare-coding evidence is UK Biobank only.** The 4–8 gene convergence tests are underpowered.
- **brainSCOPE shares donors** with CommonMind and ROSMAP, so it is not an independent QTL cohort.
- **Amendment A2 was made after the first locus ranks were viewed** (a numerical defect). Both versions are kept.
- **The 22q13.2 CYP2D6 calls are not adjusted for CYP2D6/CYP2D7 haplotypes or copy number.**
- **GRN element→gene links are excluded from ENHANCER_LINK.** Including them would move RHEBL1 to MODERATE/D1, via one element linked to 9 genes.
- **Literature files are kept local-only for copyright reasons:** full-text XML, supplementary PDF/XLSX, the DDG2P dump. Re-download URLs and sha256 are in PROVENANCE.

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

- **Sprint 5:** OPENGWAS_JWT (Gate A); AlphaGenome API key; Synapse controlled access (brainSCOPE genotypes); dbGaP (TGFM); a 23andMe application (math summary statistics); SSGAC registration (Tan 2025 family GWAS). Nothing was requested and no account was created.

* **No UKB-free, adequately powered cognition GWAS in open access** — blocks independent replication
  of the synaptic finding, continuity, and every top gene.
* **Within-family data require an OpenGWAS registration**, which this project does not make on its
  own authority.
* **Ensembl Compara REST is intermittently failing** (Part R partial).
* No directed causal gene graph exists, so controllability analysis is not meaningful.

## Exact Next Actions

**After Sprint 5 (now):**

1. **User action: unlock Gate A.** Set `OPENGWAS_JWT`, or download the ieu-b-4837 and ieu-b-4838 VCFs into `data/interim/sprint4/opengwas/`. Then run `python pipelines/sprint4/gate_a_within_family.py analyse`. This is the highest-information missing dataset: direct effects at the locus level.
2. **Computational next step:** coloc.susie of the 16 L1/L2 loci against the open Bryois 2022 single-cell brain eQTLs (Zenodo). This resolves 16p11.2 (TUFM/SH2B1/EIF3C) and 14q12 (AKAP6/NPAS3).
3. **Optional user action: AlphaGenome API key.** Then run `ALPHAGENOME_API_KEY=... python pipelines/sprint5/alphagenome_query.py --variants data/sprint5/query_variants_cognition.csv`.
4. **Re-fine-map the L1/L2 loci** with UK Biobank LD (PolyFun public LD), and adjust CYP2D6/CYP2D7 for haplotype and copy number before any 22q13.2 gene call.


**After Sprint 4 (now):**
1. **User action to unlock Gate A**: set `OPENGWAS_JWT` (or download the two VCFs from the OpenGWAS website
   into `data/interim/sprint4/opengwas/`), then `python pipelines/sprint4/gate_a_within_family.py analyse`.
   This decides whether the 159 loci act directly within families (well powered at locus level).
3. RHEBL1 / 12q13.12: resolve the gene with a multi-tissue joint fine-mapper that is not dominated by
   single strong eQTL models (TGFM needs dbGaP GTEx access — a user decision).
4. For set-level synaptic tests out of UK Biobank, only a much larger UKB-free general-cognition GWAS would
   have power; none is openly available.

**After Sprint 3.1 (now):** merge `sprint-3.1/synaptic-recon` into `sprint-4/causal-synapse-bridge`;
run the frozen Sprint-4 pre-data power calibration; Gate B on the G&C-only files; Gate C on survivors +
NEGR1/SYT1 stress tests + RPS26 (12q13.2); Gate A the moment `OPENGWAS_JWT` is set.

Sprint-3 list (kept for history):

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
