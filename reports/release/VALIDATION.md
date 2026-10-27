# Release validation

Validation environment: Python 3.12.14 on macOS arm64, using `requirements-release-lock.txt`. Scientific source snapshot: `49effba`; release work dated 27 October 2026.

| Check | Result and boundary |
|---|---|
| Primary gene/locus/family counts | Recounted from committed CSVs: 18,418 genes; 375 significant; 159 LD loci; 109/146 within-family concordance; 152 later signals; 531 assessment rows. |
| AlphaGenome sign regression | Six checks passed, including both score signs, both allele orientations and zero; synthetic/code checks only. Raw prediction aggregation not rerun. |
| Deterministic cached rebuild | A second run reproduced all seven released data files and the correction validation JSON byte for byte under the release lock. |
| Cached-evidence re-adjudication | Completed with three sequence-model units excluded. Three moderate genes, no high/D1 genes and no adult qualifiers. Exact changed fields in `data/release/correction_changes.csv`. Upstream analysis inherited. |
| Focused historical scientific checks | 59 passed, 1 external-data skip, 1 deselected before final full-suite validation. |
| Source verification index | 235/235 source registrations verified from existing snapshots, offline; this is metadata verification, not independent paper/experiment replication. |
| Strict graph/schema/provenance validator | PASS: 0 errors, 0 warnings, 3 informational orphan-source notices. Privacy transformations preserved original and distributed hashes. |
| Gitleaks history and directory scan | 30 alerts each; all reviewed as public identifiers/cursors. No confirmed credential finding. |
| Supplemental current-tree scan | No findings; includes decoded gzip and Parquet, plus environment-template checks. |
| Complete offline suite | **966 passed, 1 skipped in 81.97s (0:01:21)**. The skip requires separately acquired 1000 Genomes EUR PLINK inputs. |
| Release smoke | PASS: all 3,415 distributed-file hashes, exact headline denominators, current classes/gates, source references and document links. |
| Citation metadata | `CITATION.cff` validates against the official CFF 1.2.0 JSON Schema. |
| Markdown navigation | Every local file target across all tracked/new Markdown files resolves. External sites were verified selectively, not exhaustively crawled. |

Initial full-suite baseline: 963 passed, 4 failed. Two failures required building the documented offline HGNC identifier index. One required an external LD reference and is now an explicit skip when absent. One secret-detector test matched its own detector string; it now searches complete token patterns. No scientific classification threshold was weakened.

No end-to-end GWAS/MAGMA/colocalisation/LDSC/SEM/LAVA/PoPS analysis, bulk download or AlphaGenome service call was performed during release preparation. Original reports of execution are historical evidence, not new independent reproduction. The corrected output preserves original textual scientific values where unchanged.
