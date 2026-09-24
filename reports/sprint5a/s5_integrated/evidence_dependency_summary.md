# Evidence dependency summary (Sprint 5)

*Generated 2026-09-24T12:24:15Z from `data/sprint5/evidence_units.parquet` (1603 units) and `data/sprint5/evidence_dependency_graph.parquet` (2431 edges).*

## Why this exists

- Many evidence streams descend from the **same UK-Biobank-dominated association signal**.
- Fine-mapping, L2G, colocalisation, FOCUS, E2G overlap and brainSCOPE look-ups are therefore **not replications**.
- Here every datum is a unit, and every reason two units are not independent is an edge.

## Units by stream

| stream | units |
|---|---|
| V2G | 876 |
| ASSOCIATION | 575 |
| ASSOCIATION_MATH | 53 |
| RARE_CODING | 50 |
| V2G_DEVELOPMENTAL | 20 |
| DOSAGE_CNV | 19 |
| LINEAGE | 5 |
| QTL_COHORT | 5 |

## Units by variant-to-gene class (NOT_A_CLASS = never a vote)

| class | units |
|---|---|
| NOT_A_CLASS:FOCUS | 281 |
| QTL | 269 |
| NOT_A_CLASS:L2G->POSITIONAL | 117 |
| NOT_A_CLASS:SC_EQTL_TAG | 113 |
| ENHANCER_LINK | 65 |
| RARE_CODING_SUBTHRESHOLD_OR_PROXY | 38 |
| QTL_DEVELOPMENTAL | 20 |
| DOSAGE_CNV | 19 |
| CODING | 15 |
| RARE_CODING | 12 |
| NOT_A_CLASS:L2G->ENHANCER | 6 |
| NOT_A_CLASS:L2G->CODING | 5 |
| SEQUENCE_MODEL | 3 |
| NOT_A_CLASS:L2G->QTL | 2 |

## Dependency edges

| edge type | n | meaning |
|---|---|---|
| DERIVED_FROM | 1613 | computed from another unit's data (the GWAS signal, a QTL cohort) |
| SAME_EQTL_WEIGHTS | 562 | FOCUS built on the same GTEx/CommonMind eQTL cohorts as the coloc units |
| SHARES_DONORS | 143 | brainSCOPE donors include CommonMind (100 MSSM) and ROSMAP (46) |
| AGGREGATES | 62 | Open Targets L2G built from coding/QTL/E2G features already counted |
| SHARES_COHORT | 51 | overlapping participants (UKB lineage; HRS in Zabaneh and Davies; UKB rare-coding) |

## Association lineages and their independence

| lineage | UKB | status | counted as replication |
|---|---|---|---|
| Davies 2018 (open subset) | True | OK | no (discovery) |
| NIHR BioResource Genes & Cognition (G&C-only) | False | OK | YES |
| Zabaneh 2018 extreme IQ | False | OK | sensitivity only (HRS inside Davies) |
| Howe 2022 within-sibship | True | NOT_TESTABLE | would count; NOT_TESTABLE |
| Giannelis quantitative-ability GWAS | nan | OK | no (UKB-containing CP/EA anchors; 23andMe math items) |
| GenLang performance IQ (Eising 2022) | False | OK | sensitivity only (BATS cohort shared with Davies 2018) |

## Consequences for this sprint

- **Locus confidence.** Only **G&C** counts as independent. GenLang, Zabaneh and the math factor are sensitivity lines. Within-family data are NOT_TESTABLE.
- **Gene assignment.** One vote per class: CODING, RARE_CODING, QTL, ENHANCER_LINK, SEQUENCE_MODEL, DOSAGE_CNV.
  - Bulk eQTL cohorts, FOCUS and brainSCOPE collapse into a single QTL class, because they share donors and weights.
  - L2G never votes.
- **Rare coding.** Every exome-wide gene comes from UK Biobank participants.
  - These are different variants, so they do not duplicate the common signal.
  - They are not replication either: they are one cohort.
- **Math.** The math GWAS shares UKB through its factor anchors, and 15 of 35 Sprint-4 fine-mapped loci already use 23andMe math credible sets. Math overlap is pleiotropy, not independent support.
