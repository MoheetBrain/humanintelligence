Sprint-5 dossier: `reports/sprint5/gene_dossiers/RHEBL1.md` (read that first; this file only records what Sprint 5A changes).

## Sprint 5A addendum (2026-09-24)

**Net effect:** no class change (LOCUS_HIGH_GENE_UNRESOLVED; L7009, L2; QTL class with 4 rows; direction **D2** DIRECTION_RESOLVED; rank B 25, rank E 2). Sprint 5A adds consistent single-nucleus, prenatal and GTEx V11 support for the RHEBL1 **expression** direction. It does not resolve the gene-assignment problem raised in Sprint 5: FOCUS favoured PFKM (0.77 vs RHEBL1 0.22), and Open Targets favours DDN.

- **Single-cell coloc.**
  - SingleBrain excitatory neurons **0.864** (1 strong row); cognition-increasing allele → **HIGHER**. AGREES with bulk DIRECTION_RESOLVED.
  - Bryois: pseudo-bulk 0.642, excitatory 0.506.
  - Competitors in single-nucleus data: DDN-AS1 0.675, DRC2 0.558, LMBR1L 0.461. No other strong gene.
- **Direction (5A table).** DIRECTION_RESOLVED: 8 rows, 3 cohort units (CommonMind, GTEx, ROSMAP). SingleBrain adds a row but not a unit.
- **brainSCOPE typed evidence.** REGULATORY_ELEMENT_SUPPORT + GRN_SUPPORT only. NO_ALLELIC_EVIDENCE (no QTL to test).
- **Developmental timing (Wen 2024).**
  - **ADULT+DEVELOPMENTAL**: devBrain EUR coloc PP.H4 0.81; Walker 2019 0.94 (a subset of devBrain).
  - Adult: CommonMind, GTEx DLPFC/NAc/putamen and ROSMAP coloc; GTEx V11 11 tissues.
  - Direction HIGHER at every stage.
- **GTEx V11.** 11 brain tissues, all HIGHER. AGREES with Sprint 4. Max V11 SuSiE PIP 0.366.
- **AlphaGenome vs measured.** No RHEBL1 rows.
- **Multi-trait coloc (HyPrColoc).**
  - ALL: cognition + RHEBL1@GTEx-putamen + LMBR1L@GTEx-amygdala, posterior 0.573, candidate rs2241726 (SNP posterior 0.554).
  - GWAS-only: no cluster.
  - The cluster includes a second gene (LMBR1L).
- **LAVA local rg.** No bivariate row: in the univariate step, none of TMA, GenLang or FI4 showed local heritability at L7009 (p ≥ 0.078; Zabaneh absent), so local sharing is untestable.
- **Integrated class change.** None (`class_changes.csv` has no RHEBL1 row).

**No class flag.** The Sprint-5 verdict holds: the eQTL direction is the cleanest in the project, and the effector gene is unresolved. PFKM and DDN still need a joint multi-gene test with RHEBL1, using the same LD reference.
