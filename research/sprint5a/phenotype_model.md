# Sprint 5A phenotype model

Cognition is **not** modelled as one scalar. Each dataset maps to one node and records its measure type (`data/sprint5a/phenotype_datasets.csv`).

| Node | What it is | Genetic data in the project | Measure types present |
|---|---|---|---|
| GENERAL_COGNITION_g | latent general ability | Davies (discovery), Howe within-family, GenLang PIQ, rare coding (VNR/FI) | objective ability |
| EXECUTIVE_FUNCTION | set-shifting / processing speed | G&C trail making (UKB-free) | objective ability |
| WORKING_MEMORY | — | none separate (inside g batteries) | — |
| LEARNING_RATE | speed of assimilation (SMPY: the top 1 in 10,000 learn at least 2× the pace of the top 1 in 200) | **none** | — |
| MEMORY_RETENTION | — | rare-coding prospective memory only (non-monotone coding) | objective, but uninterpretable direction |
| QUANTITATIVE_MATHEMATICAL_REASONING | math reasoning | Giannelis Gq (self-report + course-taking **proxy**); UKB FI arithmetic items (objective single items) | self-report / achievement, and single objective items |
| SPATIAL_REASONING | 3-D visualisation (SMPY: talent searches miss about 50% of the top 1%) | **none** | — |
| EXTREME_POSITIVE_COGNITION | positive tail | Zabaneh 2018 (Duke TIP vs HRS controls) | exceptional positive tail, case–control |
| EDUCATIONAL_ATTAINMENT | **labelled proxy only** | Lee 2018; the EA-proxy rare-coding genes | education |

Clinical cognitive decline and dementia phenotypes are excluded; they were already tiered out in Sprint 3.

## Rules

1. **Evidence keeps its node.** Evidence for one node is never relabelled as another. Math proxy is not g; EA is not cognition; extreme-tail is not a generic intelligence result.
2. **Convergence across nodes must account for dependence.**
   - It is judged with local sharing and colocalisation, and discounted for overlapping samples (UKB, HRS, BATS, 23andMe).
   - Counting intersections is not enough.
3. **Nodes with no genetic data are recorded as gaps, not zeros.** This covers LEARNING_RATE, SPATIAL_REASONING and objective above-level quantitative reasoning.
