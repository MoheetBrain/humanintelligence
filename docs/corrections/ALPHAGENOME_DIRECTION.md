# AlphaGenome directional-aggregation correction

**Status: code regression fixed; historical directional outputs unresolved and excluded.** Recorded 27 October 2026 against Sprint 5A `49effbaa3bcde35f58bc770d0e122a57c05e526d`.

## Defect

In [alphagenome_summarise.py](../../pipelines/sprint5a/alphagenome_summarise.py), `direction_for_cognition_increasing_allele` is already calculated from the raw signed score and REF/ALT orientation. `cog_sign` therefore already represents the oriented direction. Aggregation multiplied it by `sign(raw_score)` again. The raw sign was squared, so negative effects could become positive and direction could instead track the allele orientation. Expression aggregation, its consistency summaries, and signed chromatin/histone/TF/CAGE top-track calls were affected.

The code now aggregates `cog_sign` directly. A zero score stays zero and is reported as no direction. [Regression tests](../../tests/test_alphagenome_orientation.py) cover positive/negative scores with both REF- and ALT-increasing alleles, zero and two signed modalities. These are synthetic correctness tests, not validation of model biology.

## Exclusion and measured impact

The 1,681,704 original cognition prediction rows and the math raw predictions are not committed. Recovering them would require the original workspace or fresh service calls. No expensive model call was made for this release. Therefore the historical **9-agree/19-disagree** comparison and all AlphaGenome directional/agreement claims remain withdrawn. Unsigned magnitude counts (e.g. 573 strong variant–gene expression pairs) remain historical descriptive values, not a validated direction or evidence of reliability.

The old comparator merge also joins by gene rather than a fully matched locus/variant/allele key. Repairing the sign alone would not independently validate the comparisons. A future reinstatement must check track semantics, allele mapping, gene/locus correspondence, duplicate alleles, ties and independent cohort identity.

The [graph builder](../../pipelines/sprint5/build_evidence_graph.py) now fails closed for the unresolved sequence-model stream. The [release re-adjudication script](../../scripts/release/rebuild_assessments.py) marks the three cached `SEQUENCE_MODEL` units for **CYP2D6, NEGR1 and GGNBP2** unresolved, then reruns the existing classification/decision stages in a temporary directory. It leaves the historical output files intact.

[Exact field changes](../../data/release/correction_changes.csv): each of those genes loses one class and the `SEQUENCE_MODEL` label. Competitor counts change for genes sharing their loci; seven mechanical rank positions and CYP2D6’s leave-one-class-out label also change. Unaffected scientific values are preserved exactly as text from the historical table; sub-floating-point serialization differences are not treated as biological changes. No gene class or direction stratum changes. DNPH1, TTBK1 and FAM131A remain moderate; there are no high-confidence or D1 genes and no qualifying adult candidates. [Machine-readable validation](../../reports/release/correction_validation.json).

## Affected historical artifacts

Every `alphagenome_*` output in `reports/sprint5a/`, the original `data/sprint5a/s5_integrated/evidence_units.parquet`, integrated gene matrices/rankings, variant–gene hypotheses, and narrative agreement/direction statements in Sprint 5A reports/dossiers are historical and subject to this notice. Exact original values remain available for forensic reproducibility; they are not the release evidence layer. Root documentation and `data/release/` take precedence.
