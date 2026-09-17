# Intervention entities cited by the Cognitive Power Atlas

One file per `ID_LOCAL`, named exactly as the identifier's local part. Contract
`docs/DATA_CONTRACT.md` §1.2 and §2.

**Every identifier in these files was seen in a tool response during the curation
session** (ChEMBL `compound_search` for ChEMBL ids, PubMed for the literature).
Where a tool returned no identifier, the field is `null` and the record says so
rather than guessing. `CPD:` and `METAB:` slugs are the contract's permitted
fallback when no accession exists.

**These records describe what other people administered in studies this atlas
ingested.** Per `docs/COMPUTATIONAL_ONLY_POLICY.md` they carry no dose, no route
detail, no regimen and no sourcing, and nothing here is a recommendation.
