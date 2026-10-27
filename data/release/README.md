# Public research data — v0.1.0

These are hypotheses and evidence records, not enhancement targets. The corrected release excludes unresolved AlphaGenome sequence-model votes. Exact original scientific values are preserved where unchanged; the complete original files remain in historical directories.

| File | Scope |
|---|---|
| [gene_assessments.csv](gene_assessments.csv) | Complete 531-row cached re-adjudication, including competing genes, uncertainty, direction and mechanical rank fields. The inherited `NULL.MODEL` row is a FOCUS placeholder, not a biological gene. |
| [locus_confidence.csv](locus_confidence.csv) | Exact historical Sprint 5A 152-signal locus table, including rank intervals and cohort-sensitive support. |
| [evidence_units.parquet](evidence_units.parquet) | Complete 1,603-unit inherited evidence table; three AlphaGenome units marked unresolved. Join historical dependencies by unit ID with [dependency graph](../sprint5a/s5_integrated/evidence_dependency_graph.parquet). |
| [adult_candidates.csv](adult_candidates.csv) | Header-only, zero qualifying rows. This is an intended result. |
| [decision.json](decision.json) | Current closed intervention gate, with valid JSON nulls and corrected access/status descriptions. |
| [negative_results.csv](negative_results.csv) | Complete original Sprint 5 negative record plus current release negatives; **filter `analysis_stage`**. Historical access/biology statements may be superseded. |
| [correction_changes.csv](correction_changes.csv) | Every changed adjudication field, including competitor counts and mechanically shifted ranks. |
| [source_manifest.json](source_manifest.json) | Dataset/resource bibliography, populations, uses, limits and rights. |
| [catalogue_publications.json](catalogue_publications.json) | Complete 132-publication metadata lookup for tournament/QTL provenance; not a list of new analyses. |
| [provenance_index.json](provenance_index.json) | Acquisition-record locations and release-byte checksums. |
| [historical_output_index.csv](historical_output_index.csv) | Complete report navigation with stage and unresolved-status labels. |
| [data_dictionary.csv](data_dictionary.csv) | Every column in the principal release data tables; dtype and missingness plus interpretation. |

CSV is UTF-8, comma-delimited with quoted fields as needed; embedded JSON/semicolon lists remain intact. Empty values mean missing/not applicable, never a zero effect. Parquet preserves typed identifiers and values. `locus_id` is project-specific; gene symbols, Ensembl/HGNC/Entrez IDs and rsIDs retain their original roles. Original full gene identifiers are in the [18,418-gene screen](../../reports/gene_tournament/direct_cognition_rank.csv).

The historical [top ten](../../reports/sprint5/TOP10_CAUSAL_GENE_CANDIDATES.csv) and [top-twenty-labelled panel](../../reports/sprint5/TOP20_RESEARCH_PRIORITY_GENES.csv) predate 5A; the latter has 25 entries. The [5A shortlists](../../reports/sprint5a) and dossiers are preserved but AlphaGenome directional fields are unresolved. Use [RESULTS.md](../../RESULTS.md) for current interpretation.

No combined-data permissive licence is asserted. [DATA_LICENSE.md](../../DATA_LICENSE.md) and source terms apply, including BrainSpan restrictions on developmental fields. [Rebuild commands](../../REPRODUCIBILITY.md) · [Correction](../../docs/corrections/ALPHAGENOME_DIRECTION.md).
