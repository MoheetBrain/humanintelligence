# SYNTHETIC X02 delivery fixture

**This is not real data and must never be ingested as evidence.** Gene ids
(`ENSG00000000001`), study ids (`SYNTHETIC_STUDY_1`) and effect sizes are invented, and
`analysis_id` is `ANALYSIS:X02-FIXTURE`.

It exists so that `pipelines/integration/ingest_x02.py` can be proven to accept a
well-formed delivery and — in `tests/test_x02_ingestion.py` — to refuse malformed ones:
a checksum mismatch, a beta with no effect allele, an H4-only colocalisation, an empty
negative-results table, and a direction that contradicts its own effect size.

Being able to demonstrate the refusals is the point. "Ready to ingest X02" is otherwise
an untestable claim.
