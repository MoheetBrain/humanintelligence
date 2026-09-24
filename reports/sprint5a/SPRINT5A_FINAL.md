# Sprint 5A — Open-data exhaustion and causal cognition integration

*2026-09-24 · branch `sprint-5a/open-data-exhaustion` (from `e88c2fb`). The integration rules were frozen at `e097067` before any Sprint-5A result, and the frozen Sprint-5 rules were rerun unchanged on the new inputs. All work is computational. **The chemistry / intervention gate is CLOSED.***

## Bottom line

1. **The cognition loci act directly within families.** This is the first within-family test in the project.
   - Gate A was run with the user's OpenGWAS token (Howe 2022, N_eff = 11,257) using the frozen Sprint-4 analysis.
   - **109 of 146 testable lead alleles are concordant.** Binomial P = 1e-9; within-family/population slope 0.69.
   - Under the frozen Sprint-4 precedence the decision moves from RETRY to **CONTINUE**. The set-level trigger, however, is a single nominal P = 0.018 at 7.5% power, so it is fragile.
2. **Adding within-family data changes the locus ranking.** L1 loci go from 2 to **11**:
   - DPP4 (now #1), ATXN2L, SFMBT1, NT5DC2, BTN2A1, AKAP6, KCNJ3, EXT1, SORT1/ATXN7L2, NEGR1 and CPN1.
   - EXOC4 falls to L3.
   - The KIFC2 (8q24.3) and CYP2D6 (22q13.2) loci become discordant (L4).
3. **Genes are still harder than loci.** Three genes reach CAUSAL_GENE_MODERATE, all at independently replicated (L2) loci:
   - **DNPH1 and TTBK1** are tied at 6p21.1.
   - **FAM131A** is at 3q27.1.
   - None reaches HIGH. The red team rates TTBK1 and FAM131A as fragile.
   - At 8 of the 11 L1 loci the gene is unresolved. AKAP6/NPAS3, EXT1 and DPP4 have no QTL colocalisation at all.
4. **At the strongest locus family (16p11.2) SH2B1 has become the leading gene.**
   - It colocalises in two independent-label single-cell datasets (PP.H4 up to 0.89).
   - It is a primary brainSCOPE signal in 9 cell types.
   - Every source agrees: the cognition allele → **higher** SH2B1.
   - Its direction is resolved on rows only, because all the single-cell data share ROSMAP donors.
5. **No gene has a resolved beneficial direction for a credible causal gene (no D1).** Adult shortlist C is **empty by the rules**. DNPH1, TTBK1 and FAM131A meet 3 of the 4 adult criteria; each lacks a resolved direction.
6. **brainSCOPE is now fully integrated, and colocalisation is conclusively not testable from public files.** It sharpens cell type and direction but changes no gene class.
7. **AlphaGenome is only weakly reliable here.** Where measured human QTLs exist, its direction calls agree 9 times and disagree 19 times, so it carries weight only when measured data agree.
8. **Math and general cognition do not convincingly converge at gene level.**
   - The genetic factor built from quantitative-ability items (Gq) is **inverted** against g at 10 of 12 shared SNPs.
   - The objective arithmetic item shares local genetics with g only at KCNJ3 (Bonferroni significant).
   - Arithmetic carries its own genetic variance beyond g (residual 0.37).

## What Sprint 5A added (all open data, downloaded by the project)

| Layer | Result |
|---|---|
| **Gate A: within-family** (Howe 2022 via the user's JWT) | 109/146 concordant (P = 1e-9); slope 0.69; locus classes 34 DIRECT_SUPPORTED, 75 concordant-underpowered, 28 discordant-within-noise, 9 discordant-beyond-noise, 13 not testable; 1/6 synaptic sets direct-supported; frozen decision **CONTINUE** (fragile at set level) |
| **Locus confidence** with the within-family lineage (the frozen Sprint-5 rule) | L1 11, L2 27, L3 63, L4 42, NT 9 (was 2/14/75/49/12). Within-family IVW slope 0.16 on EB-shrunk z; 104/140 concordant |
| **brainSCOPE** (Emani 2024; conditional, meta, bcCRE, CRISPR and GRN files added) | Colocalisation not testable (significant-only and conditional-only files). Typed evidence: WBP2NL ↓ and DHRS11 ↓ (query variant = lead signal, r² = 1); RPS26 ↑; CYP2D6 ↑; **SH2B1 ↑ in 9 cell types (primary signal)**; GOSR1 ↑. EXOC4 and NEGR1 cell-type eQTLs are **separate** signals. NT5DC2, TUFM and SUOX are absent from the expression matrices. The CRISPR table contains only **NGEF**, at a math locus. |
| **Single-cell eQTL colocalisation** (Bryois 2022, 192 donors; SingleBrain meta-analysis, 757 donors; both include ROSMAP donors) | 4,700 coloc.abf + 919 coloc.susie tests; 141 strong rows covering 42 locus–gene pairs. SH2B1 ↑ (both datasets); TUFM ↑ in single cells versus ↓ in bulk (**conflict**); GNL3 ↓ (Bryois only); KIFC2, ZFTRAF1 and PPP1R16A at one SNP; DNPH1 ↓ (excitatory neurons). AKAP6/NPAS3 ≤ 0.06; SLC39A8 0.04 (a distinct causal variant, consistent with its missense lead). |
| **Multi-trait colocalisation** (HyPrColoc) | No GWAS-only clusters (the small GWAS are under-powered). Cognition + eQTL clusters: DCC 0.93, NEGR1 0.83, KIFC2/ZFTRAF1/RECQL4 0.80, WBP2NL/NAGA 0.71, NT5DC2 0.63. The studies overlap, so these are descriptive. |
| **Developmental eQTL** (Wen 2024 devBrain, open full statistics) | Adult + developmental, same direction at every stage: RHEBL1 ↑, CLCN2 ↑, DNPH1 ↓, EIF3C ↓, NT5DC2 ↓. Adult only: DCC, TUFM, KIFC2, SH2B1, EXOC4, EXT1. In fetal data GNL3 colocalises (0.98) and NT5DC2 does not (0.42). |
| **GTEx V11** (2026, GENCODE 47; same donors as V10) | Of 21 Sprint-4 directions, 18 agree, 3 are mixed, 0 flip. Lookup only. A GENCODE ID map covers 357 genes. |
| **Open Targets 26.06** (re-verified live, per credible set) | 979 cognition credible sets. The top L2G gene is driven by distance or gene density in **755** and by biological features in 224. 126k QTL colocalisations. |
| **AlphaGenome Atlas** (user's key, via environment only) | 317 cognition variants and 53 math SNPs. 573 strong brain-expression predictions. Versus measured QTLs: **agrees** for CYP2D6, NEGR1 and GGNBP2; **disagrees** for RPS26, DHRS11, KIFC2, SUOX, NPIPB9 and NT5DC2. |
| **PolyFun + SuSiE** (published UKB functional priors) | Priors roughly halve credible sets and produce 5 variants with PIP > 0.5 (AKAP6 rs3925864, EXT1 rs10110572, rs9755750, BTN2A1 rs36162392, KCNJ3 rs2591173), but **only with the prior** (plain PIPs 0.07–0.29). They are candidates, not causal variants. The only coding variant with PIP > 0.5 is SLC39A8 A391T, which already had it without priors. |
| **LDSC + Genomic SEM** (5 traits) | rg with g: EF 0.82, PIQ 0.68, extreme IQ 0.87, arithmetic 0.77. The common factor fits (CFI 0.99). Arithmetic (0.37) and PIQ (0.45) carry specific genetic variance; extreme IQ does not (0.22, P = 0.19). |
| **LAVA local rg** (overlap-corrected) | Bonferroni-significant sharing with g: **EXT1 ↔ executive function** (ρ 0.91), **DPP4 ↔ PIQ** (0.82), **KCNJ3 ↔ arithmetic** (0.63). Extreme IQ is only nominal (DPP4 P = 0.0012, EXT1, FOXO6, CLCN2, THRB). |
| **PoPS** (Weeks 2023; leave-one-chromosome-out on Davies MAGMA; 57,742 features) | Ranks genes by their features within 159 loci (550 genes). This is **orthogonal prioritisation, never a vote**. See §PoPS. |
| **Historical foundations** | SMPY 2006 and the Ciba 1993 volume, read with page citations. Restriction of range and the continuity hypothesis were used to design the phenotype model, never as evidence. |

**Methods evaluated but not run** (reasons in `research/sprint5a/agentC_notes.md` and `tools_review.md`):

| Method | Reason |
|---|---|
| TGFM | needs dbGaP GTEx genotypes |
| cTWAS | genome-wide compute; the inputs are public, so this is scheduled work |
| Multi-ancestry fine-mapping | no powered non-EUR cognition summary statistics |
| Rare-variant burden (SAIGE-GENE+, STAAR) | needs individual-level WGS |
| Factor GWAS | the common factor is 97% Davies, so it would reproduce Davies' loci |

## The 15 questions

**1. Was brainSCOPE actually used before Sprint 5A?** **Only in a limited way.**

- **Before Sprint 5:** it appeared only as a cited resource in the Codex atlas. It was never analysed.
- **In Sprint 5:** it was used as a lead-variant lookup.
- **In Sprint 5A:** it was integrated fully (typed evidence, conditional, meta, bcCRE and CRISPR files), and colocalisation was shown to be not testable from the public files.

**2. What changed after adding brainSCOPE?**

- **Cell-type resolution and direction:**
  - RPS26 ↑ and WBP2NL ↓ across many cell types;
  - DHRS11 ↓ in neurons;
  - SH2B1 ↑ in 9 cell types.
- **Two apparent leads were exposed as separate signals:** the NEGR1 and EXOC4 cell-type eQTLs.
- **No gene class changed.** brainSCOPE's element–gene links are GRN or promoter-proximity links, which are not a vote under the frozen rules.

**3. Which loci now have adult cell-specific support?** These come from single-cell colocalisation; the cell datasets share ROSMAP donors.

| Locus | Gene | Evidence |
|---|---|---|
| 16p11.2 | **SH2B1** ↑ | SingleBrain + Bryois; also brainSCOPE |
| 16p11.2 | TUFM | ↑ in single cells versus ↓ in bulk, so conflicted |
| 3p21.1 | GNL3 ↓ | Bryois only |
| 6p21.1 | **DNPH1** ↓ | excitatory neurons |
| 8q24.3 | KIFC2 / ZFTRAF1 / PPP1R16A | same SNP |
| 22q13.2 | WBP2NL, NAGA | — |
| 17q12 | DHRS11 | — |
| NEGR1 | NEGR1 | — |
| 12q13.12 | RHEBL1 | — |
| 3q27.1 | CLCN2 / FAM131A | — |

**4. Which loci remain merely positional?**

- **14q12 AKAP6/NPAS3:** an L1 locus with no QTL colocalisation. Its only evidence is a weak AKAP6 missense variant and an NPAS3 enhancer link.
- **EXT1:** L1, no gene-level evidence of any class.
- **DPP4:** L1, only an enhancer link.
- **BTN2A1, KCNJ3, CPN1, SORT1/ATXN7L2 and CACNA1I.**
- **Open Targets overall:** 755 of 979 top L2G calls are positional.

**5. What did AlphaGenome predict?**

- **Cognition variants:** 573 strong brain-expression predictions. The strongest variant-impact scores are rs62131236 (SIX3), **rs13107325 (SLC39A8 A391T; impact score 0.994)** and rs7963801 (SYT1 locus).
- **Math SNPs:** 32 of the 53 have a strong brain prediction. Many top genes are small-RNA or pseudogene entries (RN7SL, RNU6, MIR), which carry little meaning.
- These are predictions, not measured biology.

**6. Which AlphaGenome predictions were independently supported by human QTL data?**

- **Agree:** CYP2D6 (bulk, brainSCOPE and fetal data), NEGR1 (bulk) and GGNBP2 (bulk).
- **Disagree:** RPS26 (a very robust measured eQTL), DHRS11, KIFC2, SUOX, NPIPB9 and NT5DC2 (fetal).
- The disagreements outnumber the agreements (9 agreeing and 19 disagreeing comparison rows), so predictions without measured agreement get no weight.

**7. Did any of the 53 math SNPs map convincingly to genes?** **Few.**

- **SLC39A8 A391T:** a missense variant, shared with general cognition.
- **NGEF (rs72976151):** the strongest math-specific locus (P = 1.3e-15). NGEF is the only project gene that appears in brainSCOPE's CRISPR-validation table. This is measured evidence at the element level, not yet a colocalisation.
- **MKNK2:** AlphaGenome predicts an expression and splicing effect.
- **CILP2 / SUGP1:** Open Targets L2G, driven by QTLs.
- **The rest are positional.** The Gq summary statistics are not public, so no colocalisation or fine-mapping is possible.

**8. Do math and general-cognition genetics converge?**

- **Not at the gene level.**
- **At the genome-wide level, partly:** arithmetic loads 0.79 on the common factor but keeps specific variance of 0.37.
- **Locally:** a single Bonferroni-significant locus, KCNJ3 ↔ the arithmetic item.
- **The Gq math factor is inverted against g** at 10 of 12 shared SNPs, an artefact of how it was constructed.

**9. Did better statistics change the candidate ordering?** **Yes.**

- **The within-family lineage:**
  - lifts 9 more loci to L1;
  - makes DPP4 the top locus;
  - demotes the KIFC2 and CYP2D6 loci to discordant;
  - drops EXOC4 to L3.
- **The CAUSAL_GENE_MODERATE set changes:**

  | Stage | Genes |
  |---|---|
  | Sprint 5 | KIFC2, DNPH1 |
  | Mid-5A | + CYP2D6, PPP1R16A, TTBK1, FAM131A |
  | Final | **DNPH1, TTBK1, FAM131A** |

- **The stable EB shrinkage** (Sprint 5, amendment A2) and **PolyFun** do not change any class.

**10. Which genes have the strongest causal-gene evidence?** This is shortlist A.

- **Human perturbation:** rare loss-of-function burden in KDM5B, ANKRD12, RC3H2 and CACNA1A. Carriers score lower. The data are UKB only and show loss of function, not enhancement.
- **Coding:** SLC39A8 A391T (PIP ≈ 1). The locus is L2 and concordant within families (z = 1.32).
- **Regulatory, CAUSAL_GENE_MODERATE:**
  - **DNPH1**: enhancer link + adult bulk + excitatory-neuron colocalisation + developmental data, all ↓;
  - TTBK1: tied with DNPH1;
  - FAM131A: fragile, as its single-cell colocalisation does not replicate.

**11. Which genes retain adult activity?**

- **Adult + developmental:** DNPH1, RHEBL1, CLCN2, EIF3C and NT5DC2.
- **Adult only:** SH2B1, DCC, TUFM, KIFC2, EXOC4 and EXT1.
- **Unknown:** AKAP6, NPAS3, SLC39A8, MEF2C and KDM5B.
- These classes come from regulatory evidence, never from expression level alone.

**12. Is any beneficial molecular direction genuinely resolved?** **No.**

- RPS26, RHEBL1 and WBP2NL meet the direction rule, but none is a credible causal gene.
- SH2B1 (↑) is resolved on rows only: all its single-cell data share ROSMAP donors.
- DNPH1 (↓) is near-resolved (D3).
- A "beneficial direction" would only mean the expression change that tracks the cognition-increasing allele. It never means an enhancement recommendation.

**13. Top three candidates for a dedicated deep dive:**

1. **SH2B1 (16p11.2).**
   - **For:** the strongest locus family (L1, within-family z = 1.74). Adult single-cell colocalisation in two resources, a primary brainSCOPE signal in 9 cell types, a consistent ↑ direction, and independent mouse working-memory literature.
   - **Missing:** a second evidence class that is not a QTL, and an independent cohort unit for direction. Five other genes share the signal.
2. **DNPH1 (6p21.1).**
   - **For:** the only CAUSAL_GENE_MODERATE gene at a replicated locus with a concordant ↓ direction across adult bulk, excitatory neurons and development.
   - **Missing:** separation from TTBK1, and any brain biology.
3. **SLC39A8 A391T (4q24).**
   - **For:** the only high-PIP coding variant at a replicated, within-family-concordant locus. It is also in the math stream.
   - **Missing:** a brain mechanism, and replication beyond UKB-lineage traits (GenLang is discordant). It is highly pleiotropic.

**14. Which exact missing dataset would most change the conclusion?**

- **Full cell-type association statistics for brainSCOPE:** 388 DLPFC donors, 17 cell types (Synapse, data-use certificate).
- Gene assignment is now the bottleneck, and brainSCOPE is the only large adult cortical cell-type resource whose colocalisation remains untestable.
- A close second is a **larger within-family GWAS** (Tan 2025), to sharpen which of the 11 L1 loci act directly.

**15. Which gated dataset should the user obtain first?**

- **If an institutional PI can sign a Synapse data-use certificate:** brainSCOPE (item 1 of `USER_ACCESS_REQUIRED.md`).
- **If not:** the Tan 2025 family GWAS (SSGAC portal, registration only, no PI approval), which is the fastest high-value unlock.

## PoPS (a genome-wide, orthogonal layer; never counted)

`pops_scores.csv` holds leave-one-chromosome-out scores, so the model never trained on the chromosome it scored.

- **Where PoPS agrees with the project's gene calls:**
  - 14q12: AKAP6 ranks #1 (99.5th percentile) and NPAS3 #2 (97th).
  - DCC (98th percentile genome-wide), NEGR1 (96th), SORT1 (93rd), EXT1 (82nd) and KCNJ3 (77th) score high. Each is the only scored gene in its locus, so their rank within the locus carries no information. **94 of the 158 scored loci have a single scored gene.**
  - 16p11.2: ATXN2L #2, TUFM #3, SH2B1 #4 of 21. NFATC2IP is #1, so the locus is not resolved.
- **Where PoPS disagrees:**
  - 6p21.1: SRF (99.4th percentile) is #1; TTBK1 is #2 and DNPH1 #7 of 18.
  - 3q27.1: EIF4G1 is #1; CLCN2 is #4 and FAM131A #5 of 17.
  - DPP4 is last at its locus (2.5th percentile). SLC4A10 is #1 there.
  - SLC39A8 is 9.5th percentile, as expected for a missense-driven signal.
  - NT5DC2 is #11–13 at 3p21.1.
- **Genome-wide top genes** are synaptic and adhesion genes: PTPRD, NCAM1, CTNNA2, AKAP6, EPHA5, SYT1. This matches Sprint 3.1's trans-synaptic adhesion core.
- **PoPS reflects gene features, not local variant-to-gene evidence.** It therefore changes no class. It is a reason to test SRF (6p21.1) and SLC4A10 (DPP4 locus) as alternative genes, not a result.

## Three shortlists (rules in `research/sprint5a/protocol_rules.json`)

- **A. Causal cognition genes** (`SHORTLIST_A_causal_cognition_genes.csv`):
  - LoF perturbation: KDM5B, ANKRD12, RC3H2, CACNA1A;
  - coding: SLC39A8;
  - regulatory CAUSAL_GENE_MODERATE: DNPH1, TTBK1 (tied), FAM131A.
- **B. Exceptional / quantitative** (`SHORTLIST_B_exceptional_quantitative.csv`):
  - KCNJ3: arithmetic ↔ g, Bonferroni significant;
  - BTN2A1: a math-proxy SNP that is concordant, not inverted.
  - In both, the gene is **unresolved**.
  - Extreme-IQ sharing is only nominal (DPP4, EXT1, FOXO6, CLCN2, THRB), and the extreme-IQ controls overlap Davies.
- **C. Adult-modifiable research candidates** (`SHORTLIST_C_adult_modifiable.csv`): **empty, and not forced.**
  - DNPH1, TTBK1 and FAM131A each meet 3 of 4 criteria and lack direction D1.
  - Near-misses are in `SHORTLIST_C_near_misses_NOT_qualifying.csv`.

## Dependency-aware evidence (section 10)

The protocol forbids fake calibrated probabilities. The five requested quantities are therefore reported as components, each with its uncertainty:

| Quantity | Reported as | Where |
|---|---|---|
| P(real locus) | Summed log10 BF across the counted lineages (G&C + within-family), with 5–95% rank intervals | `s5_integrated/locus_confidence_rank.csv` |
| P(causal variant \| locus) | Max PIP: plain SuSiE, plus PolyFun as a sensitivity | — |
| P(causal gene) | The ordinal gene class and the number of **distinct** independence classes. Bulk, single-cell and brainSCOPE collapse to one QTL class; L2G and FOCUS never vote. | — |
| P(adult-active mechanism) | Adult single-cell coloc > adult bulk coloc > brainSCOPE lookup > expression | — |
| P(direction resolved) | The unchanged D1–D5 strata. Single-cell rows can never create a new cohort unit. | — |

`variant_gene_cell_hypotheses.parquet` holds 1,331 variant × gene rows with every requested column. **Its layer count is not an independence count.**

## Integrity notes

- **Frozen rules.** Nothing was relaxed. The Sprint-5 pipeline was rerun unchanged (`rerun_sprint5_integrated.sh`), and Sprint-5 outputs are byte-identical when the 5A inputs are switched off (a tested property).
- **Plumbing fixes, all disclosed:**
  - Gate A: OpenGWAS v4 endpoint; `.syngo` path; AF from the reference.
  - `decide.py` could not evaluate a testable Gate A, so the frozen precedence was applied literally in `gate_a_decision.py`.
  - Zabaneh chrX SEs were mis-scaled, so Z was taken from P.
  - GenomicSEM needed lavaan 0.6-19.
- **Interruptions.** A machine reboot, and one mistaken stop, interrupted the Gate-A calibration, PoPS and the agents. Every job resumed from verified on-disk state (sha256 and row counts checked). The seeded calibration skipped finished replicates.
- **PoPS caveats.**
  - chr1–5 ran with OpenBLAS and chr6–22 with Apple Accelerate. Both reproduce PoPS' bundled example to about 1e-15. The planned direct chr1 cross-check failed on a command-line error and was **not rerun**.
  - 29 genes (30 rows) are missing from PoPS' annotation and so have no score.
- **UK Biobank LD sensitivity.** The 5 PolyFun variants with PIP > 0.5 hold up. NEGR1's 7 near-certain variants under 1000G LD disappear under UK Biobank LD.
- **Credentials.** The OpenGWAS token and AlphaGenome key were used only as environment variables. A test scans the tracked files for them. **Please rotate both**, since they appeared in chat.

## Files

- **Key outputs** in `reports/sprint5a/`:
  - `SPRINT5A_FINAL.md`, `USER_ACCESS_REQUIRED.md`
  - `SHORTLIST_*.csv`, `cross_phenotype_convergence.csv`, `variant_gene_cell_hypotheses*.{parquet,csv}`
  - `s5_integrated/*` (the integrated rerun: matrix, Top-10/20, negative results, decision; its 20 auto-generated dossiers are regenerable and not committed)
  - `brainscope_*`, `sc_eqtl_coloc*`, `multitrait_coloc.csv`, `regulatory_timing.csv`, `gtex_v11_*`
  - `alphagenome_*`, `opentargets_2606_*`, `functional_finemapping*`, `pops_scores.csv`
  - `ldsc_*`, `genomicsem_*`, `lava_*`
  - `directionality_resolution_5a.csv`, `class_changes.csv`, `gene_dossiers/` (10)
- **Sprint 4:** `reports/sprint4/within_family_*`, `decision_gate_a_update.json`, and the Gate-A update block in `CAUSAL_SYNAPSE_GATE.md`.
- **Research record** in `research/sprint5a/`: protocol, historical foundations, phenotype model, and the agent and dossier notes.
