# Reproducibility

The release preserves a completed research snapshot, not a containerised end-to-end rerun. The exact checks performed are in [VALIDATION.md](reports/release/VALIDATION.md). Large raw downloads, external tools and controlled-access data remain outside Git.

## Environment

Python >=3.11 is declared by the original project; this release was validated with Python **3.12.14**. Use the observed [release dependency lock](requirements-release-lock.txt) for reproducibility. The earlier [requirements-lock.txt](requirements-lock.txt) is retained as historical; it did not include every scientific dependency. Neither lock pins an OS or R environment.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-release-lock.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python scripts/fetch_gene_identifiers.py --offline
.venv/bin/python scripts/release/smoke.py
.venv/bin/python -m pytest -q -m 'not network and not slow'
```

Run commands from the repository root. The offline identifier step is required for graph tests in a fresh clone. The external LD integration test explicitly skips when its PLINK reference is unavailable; the skip is not proof of LD-calibration reproduction. Network tests are never implied by an offline pass.

## Level 1 — inspect and check the committed results

`scripts/release/smoke.py` uses the standard library to verify release checksums, key denominators, the empty adult-candidate table, correction status, source/document links and absence of accidentally committed environment values. It does not run model calls or download inputs. `data/release/README.md` lists current tables; historical files retain their original scientific values with status notices.

## Level 2 — regenerate corrected public gene assessments

```bash
.venv/bin/python scripts/release/rebuild_assessments.py
.venv/bin/python scripts/release/build_catalogue.py
```

The first command stages existing Sprint 5A report/data inputs in a temporary directory, excludes the three unresolved AlphaGenome units, then invokes the original classifier and decision logic. It writes `data/release/gene_assessments.csv`, `locus_confidence.csv`, `negative_results.csv`, `evidence_units.parquet`, `adult_candidates.csv`, `correction_changes.csv`, `decision.json` and `reports/release/correction_validation.json`. It does not refit GWAS, LD, fine-mapping or gene ranks for publicity. Any rank fields are inherited mechanical classifier outputs.

The second command rebuilds the human-readable dataset guide, complete source/provenance index, output inventory and column dictionary from the committed source registry and table schemas. `scripts/release/build_manifest.py` refreshes `RELEASE_MANIFEST.json` after an intentional change; do not use it to conceal unexplained scientific drift. Rebuilds can produce different Parquet bytes across library versions even where values match; use the release lock and compare content.

## Level 3 — upstream research execution (not reproduced for this release)

| Stage | Required external material / execution |
|---|---|
| MAGMA and LD-aware tests | Download MAGMA 1.10 under its terms and an appropriate 1000 Genomes EUR PLINK reference. Place the historical X01 layout at `data/external/x01/` (`inputs/`, `genetics_tools/bin/`, `genetics_tools/reference/`, `genetics_tools/results/`), or set `COGNITION_X01_ROOT` for the Sprint-4 common path helper. Some older wrappers assume that relative layout and the repository-root working directory. No claim of complete portability is made for all historical wrappers. |
| Davies summary GWAS | Acquire the **public subset** from [DataShare](https://doi.org/10.7488/ds/2558). Verify SHA-256 `01990c3e30661db518579d8f84dfddd7f79bc9b476e8a65b45d28c0489ca6573` against the historical file before replay; the full-publication dataset differs. |
| Within-family Gate A | Acquire `ieu-b-4837` and `ieu-b-4838` through OpenGWAS, using `OPENGWAS_JWT` in the environment only. The original VCF hashes are in `data/sprint4/gate_a_access.json`. `gate_a_within_family.py fetch` / `analyse` are expensive upstream steps, not smoke tests. |
| G&C, GenLang, Zabaneh, arithmetic | Use exact accession/record URLs in `source_manifest.json`, `cohort_overlap_ledger.csv` and acquisition provenance. Preserve effect alleles, genome build and phenotype polarity. Do not substitute newer files silently. |
| QTL / fine-mapping / FOCUS | Reacquire the recorded eQTL Catalogue and external reference/weight files. R, SuSiE/coloc, PLINK/tabix and FOCUS are external; historical dependency versions are in scripts/logs where available, but no complete R lock exists. `COGNITION_R_ENV` points the Sprint-4/5 helpers to an environment containing `bin/Rscript` and `bin/tabix`. Other historical scripts may require local path adaptation. |
| Single-cell / devBrain / GTEx | Use per-file URLs, ranges, timestamps and checksums under `data/raw/sprint5a/*/PROVENANCE.json`. Range hashes identify fetched bytes, not complete multi-GB files. Public eQTL summaries do not authorise participant genotype access. |
| LDSC / Genomic SEM / LAVA / HyPrColoc / PolyFun / PoPS | Inputs, scripts and provenance are linked in METHODOLOGY.md. External packages, LD matrices and PoPS feature matrices must be acquired separately. The HyPrColoc cast patch is preserved; apply it only to the documented upstream version. No complete environment lock or replay claim is made. |
| AlphaGenome | `ALPHAGENOME_API_KEY` and service terms are required for new calls. Prefer recovering the historical raw Parquet files. Run corrected aggregation only after checking track/allele semantics; a complete variant/locus-aware observed-QTL comparison must be validated before restoring any evidence vote. |
| Controlled sources | Full brainSCOPE association data: Synapse/data-use approval; TGFM: controlled GTEx/dbGaP inputs; 23andMe Gq: application; larger family GWAS: source registration. These inputs are absent. See `reports/sprint5a/USER_ACCESS_REQUIRED.md`. |

## Seeds and frozen configuration

Use the exact `research/sprint4/frozen_hypotheses.json`, `research/sprint5/protocol_rules.json`, `research/sprint5a/protocol_rules.json` and ranking configuration under `models/`. Scripts contain deterministic seeds (for example LD calibration uses `20260923` in the regression check); there is no single global seed that replaces all stage-specific settings. Protocol hash guards reject changes. The release amended the Sprint-4 protocol checksum solely to remove machine paths, with an explicit dated note; scientific thresholds/set membership were unchanged.

MAGMA permutation noise and external model/runtime changes can prevent byte-identical historical replay. Cached tests and checksum verification must not be reported as an independently reproduced scientific analysis.

## Credentials, storage and data integrity

`.env.example` contains names and empty assignments only. Do not commit `.env`, raw tokens, controlled human data or private local paths. Use source terms before fetching or redistributing any data. Keep large inputs under the ignored `data/interim/` or `data/external/` directories.

Per-source acquisition `sha256` values describe downloaded objects. In the central raw manifest, `sha256` checks the distributed snapshot and `original_download_sha256` preserves the original when privacy minimisation changed it. Privacy-minimised snapshots can differ: `docs/security/sanitisation_manifest.json` records original and release hashes and is authoritative for that transformation. The release manifest checks distributed bytes. This distinction avoids falsely claiming that a redacted file is the original downloaded object.

The inherited `make tournament` help text called the target offline, but one called fetcher can access Open Targets if its caches are incomplete. **Do not use it as an offline smoke check.** The explicit release commands above are the supported fast path.
