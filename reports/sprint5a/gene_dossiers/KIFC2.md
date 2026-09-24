Sprint-5 dossier: `reports/sprint5/gene_dossiers/KIFC2.md` (read that first; this file only records what Sprint 5A changes).

## Sprint 5A addendum (2026-09-24)

**Net effect:** the class is unchanged at CAUSAL_GENE_MODERATE (L65265, L3; rank B 1, rank E 18; direction D4, UNRESOLVED). Sprint 5A adds one more expression row. It also adds a new co-leader at the same locus (PPP1R16A, rank B 2) and shows that the 8q24.3 haplotype moves at least five genes. KIFC2's lead is therefore weaker in relative terms, not stronger.

- **Single-cell coloc.**
  - SingleBrain excitatory neurons PP.H4 **0.979** (coloc.susie; 1 strong row); cognition-increasing allele → **LOWER** KIFC2. This AGREES with the Sprint-4 ROSMAP bulk row.
  - Bryois: inhibitory 0.505, excitatory 0.064, pseudo-bulk 0.035. No second resource at ≥ 0.8.
  - Same SNP (rs750472): ZFTRAF1 0.991 (12 rows, LOWER), PPP1R16A 0.987 (8 rows, HIGHER), LRRC24 0.903 (HIGHER), RECQL4 0.892 (LOWER).
- **Direction (Sprint-5A table).** UNRESOLVED: 2 rows (ROSMAP bulk + SingleBrain), 1 cohort unit, both LOWER. SingleBrain shares ROSMAP donors, so no new unit is added.
- **brainSCOPE typed evidence.** No KIFC2 row.
- **Developmental timing (Wen 2024 devBrain).** timing_class **ADULT**. No prenatal coloc. Adult evidence: ROSMAP DLPFC coloc and GTEx V11 overlap, direction LOWER, consistent.
- **GTEx V11.** 4 brain tissues (cortex, frontal cortex BA9, hypothalamus, putamen), all LOWER. AGREES with Sprint 4. Max V11 SuSiE PIP of a query variant 0.217.
- **AlphaGenome vs measured.**
  - Predicted **UP** (strong; top track astrocyte total RNA-seq; rs112422823; max quantile 0.9998).
  - PRIMARY_MEASURED comparator: **DISAGREE** (2 rows). SECONDARY_OT: 2 agree, 2 disagree.
  - The sequence model contradicts the measured direction.
- **Multi-trait coloc (HyPrColoc).**
  - ALL run: cognition + ZFTRAF1@ROSMAP + RECQL4@CommonMind + KIFC2@ROSMAP share a variant, posterior 0.803, candidate rs750472 (SNP posterior 0.468).
  - GWAS-only: no cluster.
  - Sharing is at the haplotype level, not specific to KIFC2.
- **LAVA local rg.** No bivariate row for L65265 in `lava_bivariate_core5.csv`. Univariate: Davies p 9.9e-20; Zabaneh p 0.003; TMA, GenLang and FI4 not significant.
- **Integrated class change.** None (`class_changes.csv` has no KIFC2 row).

**Flag (no edit):** KIFC2 (rank B 1) and PPP1R16A (rank B 2) tie on two classes each, with opposite expression directions at the same SNP. ZFTRAF1 has the strongest, most replicated colocalisation but sits as LIKELY_QTL_PASSENGER. The locus should be read as gene-unresolved.
