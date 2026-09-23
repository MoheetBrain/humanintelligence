# Sprint-4 literature facts (agent-verified 2026-09-23; to be placed in research/sprint4/ on the sprint-4 branch)
Rahman et al. 2026 Nat Commun doi:10.1038/s41467-026-71738-9, PMC13342582; SI MOESM1; peer review MOESM3.
- TMN = trail 1 (numeric), TMA = trail 2 (alphanumeric), TMD = raw TMA - raw TMN. UKB fields 20156/20157 (seconds).
- TMN, TMA log10; TMD raw seconds. Winsorised. No INT. Covariates in BOLT.
- Direction: "higher scores on all three TM measures indicate slower task completion"; no sign flip.
- N: UKB 84,238; G&C 9,932 (Table 1). European ancestry. BOLT-LMM v2.3.6; MAF>=0.05, INFO>=0.5; METAL fixed IVW.
- Build: not stated; inferred GRCh37 (rs429358 at 19:45411941; GRCh37 gene mapping).
- G&C independence from UKB: UNVERIFIED (no explicit statement found).
- Table 5 (TMA; A1 = effect allele): rs7639267 (NT5DC2) G vs T: UKB 0.0039/0.0006/4.1e-10; G&C 0.0062/0.0020/0.0018; Meta 0.0041/0.0006/5.39e-12. G = slower TMA.
  rs1217098 A vs C: G&C -0.009/0.002/9e-05; rs6975134 (EXOC4) T vs C: G&C 0.005/0.002/0.02; rs13212562 A vs G: G&C 0.006/0.003/0.042.
  Only rs7639267 and rs1217098 pass Bonferroni (0.05/9). SI Table 4 lists rs7639267 A1=T beta -0.0041 freq 0.5623 (meta) -> harmonise by allele.
- SI Table 8: rg(TMA, intelligence Davies 2018) = -0.752 (SE 0.020); rg(TMA, EA) = -0.335; rg(TMA, childhood IQ) = -0.515.
Howe et al. 2022 Nat Genet doi:10.1038/s41588-022-01062-7; Supp Table 1: cognition cohorts 9 (27,638): GS 11,352; UKB 8,061 (UKB INCLUDED); TEDS 3,172; DTR 1,158; Viking1 834; STR 814; FTC 788; MN twins 732; ORCADES 727.
- 21.6% (95% CI 6.4-36.8) shrinkage = 1 - S_W/S_P, IVW score at P<1e-5 SNPs chosen in independent UKB non-sibling GWAS; GWS-threshold score 11.7% (-8.4 to 31.8) ns. LDSC h2 0.24 -> 0.14.
- Population and within models fitted in same siblings; within model adds sibship-mean genotype; clustered SE.
- OpenGWAS N 9,997 / 22,593 differ from paper 27,638: UNVERIFIED why.
- No non-OpenGWAS mirror found. Tan et al. 2024 medRxiv 10.1101/2024.10.01.24314703: direct-population rg for cognition 0.543 (SE 0.036), eff N 12,361 direct; SSGAC login. Young 2022: 0.490 (SE 0.086), UKB only.
- gwas-vcf spec v1.0.0: ES relative to ALT; SE; LP=-log10P (optional); AF=ALT freq; SS; ID.
