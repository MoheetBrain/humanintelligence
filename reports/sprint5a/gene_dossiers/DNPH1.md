Sprint-5 dossier: `reports/sprint5/gene_dossiers/DNPH1.md` (read that first; this file only records what Sprint 5A changes).

## Sprint 5A addendum (2026-09-24)

**Net effect:** the class is unchanged at CAUSAL_GENE_MODERATE (L55168, L3). Direction improves from D4 to **D3** (RESOLVED_ON_ROWS_ONLY_NOT_ROBUST; 4 rows, 2 cohort units, all LOWER). Rank B moves 2 → 3, because the neighbouring neuronal kinase TTBK1 was promoted to MODERATE (rank B 4; see `TTBK1.md`). DNPH1 remains the statistically better-supported expression gene at this locus; TTBK1 is the biologically more plausible one.

- **Single-cell coloc.**
  - SingleBrain: excitatory **0.927**, inhibitory **0.855** (2 strong rows), oligodendrocyte 0.798, all LOWER. AGREES with bulk (CommonMind, ROSMAP).
  - Bryois: pseudo-bulk 0.479, excitatory 0.316. This is below the strong threshold in the smaller resource.
- **Direction table (5A).** Sources: Sprint-4 bulk coloc (CommonMind, ROSMAP) + SingleBrain. Units: commonmind; rosmap. SingleBrain overlaps ROSMAP donors, so it adds no unit.
- **brainSCOPE typed evidence.** No DNPH1 row.
- **Developmental timing (Wen 2024).**
  - **ADULT+DEVELOPMENTAL**: prenatal devBrain coloc EUR PP.H4 0.92 and Tri2 0.92; Walker 2019 neocortex 0.92 (Walker is a subset of devBrain, not independent).
  - Adult: CommonMind and ROSMAP coloc; GTEx V11 overlap.
  - Direction LOWER at every stage.
- **GTEx V11.** 6 brain tissues (caudate, cerebellum, frontal cortex BA9, hippocampus, nucleus accumbens, putamen), all LOWER. AGREES with Sprint 4.
- **AlphaGenome vs measured.** No DNPH1 rows.
- **Multi-trait coloc (HyPrColoc).**
  - ALL: cognition + DNPH1@ROSMAP + PTK7@ROSMAP, posterior 0.525, candidate rs7832 (SNP posterior 0.149).
  - GWAS-only: no cluster.
  - The posterior is moderate and the cluster is two-gene.
- **LAVA local rg.** L55168 Davies–Zabaneh rho 0.029 (−0.39 to 0.46), p 0.88. No local sharing with extreme IQ.
- **Fine-mapping (5A).** No credible set in any Sprint-5A SuSiE or PolyFun run at L55168 (plain 1000G top rs78652437 PIP 0.091). The variant layer remains unresolved.
- **Integrated class change.** CAUSAL_GENE_MODERATE → CAUSAL_GENE_MODERATE; D4 → D3; rank B 2 → 3 (`class_changes.csv`).

**Flag (no edit):** the locus now carries two MODERATE genes, and TTBK1's QTL class rests on one SingleBrain oligodendrocyte row. The biological disconnect noted in Sprint 5 remains: DNPH1 is a nucleotide-salvage enzyme with no brain literature. The new data strengthen DNPH1's expression evidence only.
