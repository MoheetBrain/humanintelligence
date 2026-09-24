# Sprint 5A research log

*Branch `sprint-5a/open-data-exhaustion`, 2026-09-24 (UTC). Times are approximate unless a file timestamp confirms them.*

1. **Audit (§0).** brainSCOPE first appears as a data source in Sprint 5, as a lead-variant lookup. Before that it was only cited in the Codex atlas. Result: Q1 = "only in a limited way".
2. **Protocol freeze.** The protocol was frozen at `e097067` (`protocol.md`, `protocol_rules.json` sha 1c1aa071…) before any Sprint-5A result. The frozen rules cover:
   - single-cell eQTL collapses into the QTL class, and ROSMAP-donor single-cell rows never create a new cohort unit;
   - brainSCOPE is typed evidence only, and never counts as colocalisation;
   - PolyFun and PoPS are never a vote;
   - AlphaGenome counts only where it agrees with a measured QTL;
   - GTEx V11 creates no new unit;
   - Gate A counts as the WITHIN_FAMILY lineage.
3. **Historical foundations** (`historical_foundations.md`). SMPY 2006 and Ciba 1993 were read with page numbers. They were used to design the phenotype model (`phenotype_model.md`: restriction of range, continuity) and never as evidence.
4. **Canonical inputs.** Frozen in `data/sprint5a/canonical_inputs.*`. Allele frequencies come from the 1000G EUR reference (`g1000_freq.py`), because the Howe VCFs carry no AF.
5. **Open Targets 26.06** (`opentargets_credible_set_refresh.py`). 979 cognition credible sets. The first pull returned only GWAS–GWAS colocalisations; it was refetched with QTL study types (126k colocalisations).
6. **AlphaGenome.** The user's key was used via the environment only. 317 cognition variants and 53 math SNPs were queried.
   - Two bugs were fixed before the final run: the "6.0" chromosome formatting and missing alleles (48 of 60 were filled from Davies).
   - Comparators: measured QTL sources are PRIMARY and Open Targets is SECONDARY.
7. **About 09:58Z: the machine rebooted** and every job was killed. The calibration, LAVA and the three agents were resumed from verified on-disk state. Checkpoint commit `173944d`.
8. **LDSC + Genomic SEM** (5 traits). Zabaneh's chrX SEs were mis-scaled (mean χ² 71), so Z was recomputed from P. lavaan was pinned to 0.6-19. The Heywood fallback fit was discarded.
9. **LAVA.** 48 bivariate tests, with overlap taken from the LDSC intercepts. Blanks are read as NA.
10. **Agent A** (brainSCOPE, developmental timing, GTEx V11, GENCODE) and **Agent B** (single-cell eQTL colocalisation, HyPrColoc) finished. See `agentA_notes.md` and `agentB_notes.md`.
11. **Agent C** (PolyFun/SuSiE, UKB LD sensitivity, PoPS). PoPS was run leave-one-chromosome-out; PoPS was interrupted by the reboot and by one user-requested stop, and resumed each time. See `agentC_notes.md`.
12. **Gate A** (`pipelines/sprint4/gate_a_within_family.py`), using the frozen Sprint-4 analysis.
    - Plumbing fixes: POST `gwasinfo` (v4 API); the `.syngo` path; AF from the reference.
    - 120/120 calibration replicates.
    - 109/146 loci concordant.
    - The frozen precedence (`gate_a_decision.py`) gives **CONTINUE**.
    - Update block U-S5A-1 was appended to `reports/sprint4/CAUSAL_SYNAPSE_GATE.md`.
13. **Integrated Sprint-5 rerun** (`rerun_sprint5_integrated.sh`, with `S5A_INTEGRATION=1`).
    - Adds the WF lineage, the single-cell units, the AlphaGenome units and the 5A direction file.
    - Sprint-5 outputs stay byte-identical when the flag is off (tested).
    - Unit IDs for E2G/CODING were made locus-specific to fix duplicates.
    - The comparison uses a NaN-safe diff.
14. **Convergence and shortlists** (`convergence_and_shortlists.py`).
    - Inverted math-proxy SNPs are labelled as not convergence.
    - Shortlist C is empty; near misses are listed separately.
15. **Variant–gene–cell table** (`build_variant_table.py`) and **10 dossiers** (`gene_dossiers/`, notes in `dossier_notes_5a.md`).
16. **Final report** (`reports/sprint5a/SPRINT5A_FINAL.md`) and **USER_ACCESS_REQUIRED** (10 rows).
