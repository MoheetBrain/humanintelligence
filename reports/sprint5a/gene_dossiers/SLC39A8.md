Sprint-5 dossier: `reports/sprint5/gene_dossiers/SLC39A8.md` (read that first; this file only records what Sprint 5A changes).

## Sprint 5A addendum (2026-09-24)

**Net effect:** no class change (LOCUS_HIGH_GENE_UNRESOLVED; CODING class from the missense rs13107325, A391T, PIP ≈ 1; L64116, L2; perturbation P4; direction D5; rank B 23). Sprint 5A strengthens the reading that this locus does **not** act through expression, and adds local-rg evidence that its cognition association is carried mainly by UKB-overlapping traits.

- **Single-cell coloc.**
  - Best PP.H4 **0.037** (Bryois pericytes); SingleBrain ≤ 0.030. No strong row.
  - PP.H3 reaches 1.0 for some gene × cell-type pairs: distinct causal variants for expression and cognition.
  - This is consistent with a coding (protein-function) mechanism rather than a regulatory one.
- **brainSCOPE typed evidence.** No SLC39A8 row.
- **Developmental timing (Wen 2024).** UNKNOWN: no prenatal or adult expression evidence at this signal.
- **GTEx V11.** No SLC39A8 row.
- **AlphaGenome vs measured.**
  - rs13107325: predicted **DOWN** expression, strong in 40/40 brain tracks (top astrocyte total RNA-seq; max quantile 0.9996).
  - Comparator: **NO_OBSERVED_QTL_FOR_GENE**. The prediction is unconfirmed, so under the protocol it carries no weight.
  - The missense effect on ZIP8 manganese/zinc transport is not a sequence-model output.
- **Multi-trait coloc (HyPrColoc).** L64116 ALL and GWAS-only: **no cluster**. The eQTL traits SLC39A8@GTEx-amygdala, BANK1 and NFKB1 did not join cognition.
- **LAVA local rg (L64116).**
  - Davies–UKB FI4: rho **0.583** (0.206–1.0), p 0.0049.
  - Davies–G&C TMA: rho 0.164, p 0.40.
  - Davies–GenLang PIQ: rho −0.189, p 0.32.
  - Local sharing is detected only with the UKB-derived FI4 trait, which overlaps Davies. The two cohorts independent of UKB show none.
  - This matches the Sprint-5 note that the association is weak or contradicted outside UKB.
- **Integrated class change.** None (`class_changes.csv` has no SLC39A8 row).

**No class flag.** The Sprint-5 caveats stand: a pleiotropic missense variant (Mn homeostasis, lipids, schizophrenia, BMI and more), with DISEASE_ONLY recessive LoF (CDG type IIn, with intellectual disability).
