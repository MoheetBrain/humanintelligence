Sprint-5 dossier: `reports/sprint5/gene_dossiers/CYP2D6.md` (read that first; this file only records what Sprint 5A changes).

## Sprint 5A addendum (2026-09-24)

**Net effect: promoted from V2G_SUPPORTED_WEAK_LOCUS to CAUSAL_GENE_MODERATE** (L1565, L3; classes QTL;SEQUENCE_MODEL; rank B 34 → 6; direction D3 unchanged). The promotion comes entirely from the new **SEQUENCE_MODEL** class (AlphaGenome). The Sprint-5 red flag is not addressed by any Sprint-5A layer, and several layers inherit it. That flag is that the lead rs28670611 is in complete LD with the CYP2D6 star-allele SNP rs1135840, next to the 92%-identical CYP2D7, so short-read expression is least trustworthy here.

- **Single-cell coloc.**
  - Bryois inhibitory neurons **0.849** (1 strong row, HIGHER); astrocytes 0.789; oligodendrocytes 0.665.
  - SingleBrain: essentially untestable (only endothelial tested, 0.016). CYP2D6 appears to be absent or filtered in most SingleBrain cell types.
  - At the same locus, WBP2NL (12 strong rows, LOWER), NDUFA6 (3), NAGA (2) and SMIM45 (1) colocalise more strongly and more reproducibly.
- **brainSCOPE typed evidence.** DIRECT_VARIANT_GENE_OVERLAP + CELL_SPECIFIC_QTL_SUPPORT (Chandelier/Pvalb, L2/3 IT, L5 IT, Lamp5, Sst.Chodl, Vip), all HIGHER. This was already known in Sprint 5; coloc is NOT_TESTABLE_WITH_PUBLIC_OUTPUT.
- **Developmental timing (Wen 2024).**
  - **ADULT+DEVELOPMENTAL**: devBrain coloc EUR 0.96, Tri1 0.91, Tri2 0.83; Walker 2019 0.86 (a subset of devBrain).
  - Adult: GTEx and ROSMAP coloc.
  - Direction HIGHER, consistent.
- **GTEx V11.** 13 brain tissues, all HIGHER. AGREES with Sprint 4. Max V11 SuSiE PIP 0.356.
- **AlphaGenome vs measured.**
  - rs28670611: predicted UP, strong in **1/20** brain tracks.
  - rs5758605: UP, strong in 9/20.
  - PRIMARY_MEASURED comparators (bulk coloc, brainSCOPE, Walker): AGREE, 6 rows. SECONDARY_OT: 2 agree, 4 disagree.
- **Multi-trait coloc (HyPrColoc).**
  - ALL: cognition + NAGA@GTEx-NAc + WBP2NL@GTEx-amygdala, posterior 0.714, rs133326.
  - **CYP2D6@GTEx-spinal-cord was a trait and was NOT in the cluster.**
  - GWAS-only: no cluster.
- **LAVA local rg.** L1565 Davies–Zabaneh rho 0.207, p 0.33. No evidence of local sharing.
- **Integrated class change.** V2G_SUPPORTED_WEAK_LOCUS (QTL) → CAUSAL_GENE_MODERATE (QTL;SEQUENCE_MODEL); rank B 34 → 6.

**Flag for class review (no edit).** The protocol requires "observed human QTL agreement" for SEQUENCE_MODEL to carry weight. Here, the observed QTLs it agrees with are the same short-read measurements whose reliability at CYP2D6/CYP2D7 was questioned in Sprint 5. The AlphaGenome RNA-seq tracks are also trained on short-read data. The SEQUENCE_MODEL class is therefore not independent of the QTL class, and the promotion effectively double-counts one evidence line. In addition, HyPrColoc excluded CYP2D6 from the cognition cluster, and WBP2NL has the stronger single-nucleus colocalisation.
