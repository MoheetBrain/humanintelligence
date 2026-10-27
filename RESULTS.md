# Results — v0.1.0

The authoritative scientific snapshot is Sprint 5A commit `49effbaa3bcde35f58bc770d0e122a57c05e526d` (24 September 2026), with the 27 October release corrections described below. Earlier sprints are historical. Results are statistical hypotheses, not demonstrations of cognitive enhancement.

## Denominators and verification

| Quantity | Value | Committed source |
|---|---:|---|
| MAGMA gene screen | 18,418 | [direct_cognition_rank.csv](reports/gene_tournament/direct_cognition_rank.csv) |
| Bonferroni-significant genes | 375 | `bonferroni_davies` in the same table; threshold 0.05/18,418 |
| LD blocks containing these genes | 159 | Distinct `ld_block_r0.2` among significant genes; [construction](data/gene_tournament/ld_loci_summary.json) |
| Within-family testable leads | 146/159 | [locus comparisons](reports/sprint4/within_family_locus_concordance.csv) |
| Concordant within-family leads | 109/146 | 34 `DIRECT_SUPPORTED` + 75 `CONCORDANT_UNDERPOWERED`; 28 discordant within noise, 9 beyond noise, 13 untestable |
| Aggregate sign P | 9.90182838346704e-10 | [Gate A decision](reports/sprint4/decision_gate_a_update.json) |
| Within-family/population beta slope | 0.6890683409498615 | Same decision; **not** the later EB-z slope |
| Effective within-family N | 11,257.411764705881 | Estimated from SE ratios; not the 9,997 metadata participant count |
| Later integrated signals | 152 | [locus table](data/release/locus_confidence.csv); 159 blocks are collapsed by shared lead SNPs in `locus_confidence.py` |
| Later locus strata | L1 11; L2 27; L3 63; L4 42; NT 9 | Same table; 140 testable later within-family rows, 104 concordant; this is a distinct deduplicated analysis |
| Assessment rows (including the historical FOCUS `NULL.MODEL` placeholder) | 531 | [release evidence matrix](data/release/gene_assessments.csv) |
| Moderate / high-confidence genes | 3 / 0 | DNPH1, TTBK1, FAM131A; cached re-adjudication with AlphaGenome excluded |
| D1 / adult-gate qualifiers | 0 / 0 | [empty adult CSV](data/release/adult_candidates.csv), [decision](data/release/decision.json) |

The historical `CONTINUE` decision concerns the statistical research programme. Its set-level trigger is nominal P=0.018 across six tested sets (Bonferroni threshold 0.0083), with 7.5% simulated power. It does not authorise an intervention or establish each locus as directly causal. The within-family lineage overlaps discovery participants; its design answers a different question from disjoint-cohort replication.

## Key gene hypotheses

| Candidate | Why it remains interesting | Why it is unresolved |
|---|---|---|
| **DNPH1** | Moderate; 6p21.1 L2; enhancer links plus adult/excitatory and developmental QTL support; lower-expression association across measured sources | Tied with TTBK1; no D1; limited brain mechanism; PoPS favours SRF in the locus |
| **TTBK1** | Moderate at the same L2 locus; kinase biology provides context | Shares locus and competing links with DNPH1; red-team fragile; no robust adult direction |
| **FAM131A** | Moderate at 3q27.1 L2; multiple evidence classes | Single-cell signal does not replicate; CLCN2/EIF4G1 compete; no D1 |
| **SLC39A8** | rs13107325/A391T has PIP near 1 without functional priors; a concrete coding-to-gene link at L2 | Pleiotropic ZIP8/metal-ion biology; discordant GenLang sensitivity; no brain mechanism or intervention direction; one class does not satisfy the frozen high-confidence rule |
| **SH2B1** | L1 16p11.2; measured single-cell and brainSCOPE associations favour higher expression | Shared ROSMAP donors; QTL is one evidence class; neighbouring genes remain; row-level agreement is not independent-cohort D1 |
| **DCC** | L2; guidance-related biology, adult rodent literature and descriptive HyPrColoc posterior about 0.93 | Strong mechanistic literature is not a human causal-gene assignment; cohort/phenotype overlap and weak robust direction |
| **TUFM** | Adult molecular support at 16p11.2 | Single-cell higher-expression versus bulk lower-expression conflict |
| **NEGR1** | L1 locus, cell-type evidence and descriptive sharing | Gene assignment contested; FOCUS favours RPL31P12; distinct brainSCOPE signal; AlphaGenome vote removed |
| **KIFC2 / CYP2D6** | Previously prominent molecular hypotheses | Loci fall to discordant L4 in 5A; competitors and CYP2D6 structural complexity; historical rankings superseded |
| **AKAP6 / NPAS3; DPP4; EXT1** | Strong L1 locus support; useful gene-feature hypotheses | Missing decisive QTL/variant-to-gene evidence. A locus name is not an adjudicated gene |

[Ten historical Sprint 5A dossiers](reports/sprint5a/gene_dossiers) retain supporting literature and contrary evidence. Their AlphaGenome directional statements are subject to the release correction.

## Corrections and negative findings

- **AlphaGenome:** the signed effect was multiplied twice. Three model units (CYP2D6, NEGR1, GGNBP2) are excluded in the release matrix. Class counts, competitor-class summaries, seven mechanical rank positions and one leave-one-class-out label change; gene classes, D1 and adult-gate results do not. The historical 9-agree/19-disagree comparison is withdrawn. [Correction and exact changes](docs/corrections/ALPHAGENOME_DIRECTION.md).
- **Sprint 3 → 3.1:** conditioned MAGMA previously lost 1,349 unannotated genes and GO ancestors were missing. Corrected analyses retain neurodevelopmental as well as synaptic enrichment. Presynaptic specificity and the “1.13×” tail-continuity claim were withdrawn. [Thirteen correction blocks](reports/GENE_TOURNAMENT_FINAL.md).
- **Sprint 4 → 5:** KDE-Tweedie tail shrinkage was unstable; stable empirical-Bayes shrinkage was introduced after the first ranks were viewed. The original defective output remains labelled in `data/sprint5/`. [Sprint 5 amendments](reports/sprint5/SPRINT5_FINAL.md).
- **Access labels:** inherited Sprint 5A `decision.json` hard-coded historical “JWT/API key absent” strings. The release decision now correctly points to completed Gate A and excludes AlphaGenome for the directional defect.
- **Nulls:** common–rare convergence was underpowered and null; positive-dosage findings do not establish a replicated beneficial mechanism; presynaptic release machinery was not specifically enriched; brainSCOPE public files cannot establish colocalisation.
- **Math:** Gq is a self-report/course-taking factor made orthogonal to g. Ten of 12 shared variants have inverted signs. Objective arithmetic has a separate phenotype and only one Bonferroni-significant local-sharing result with g (KCNJ3 label; gene unresolved).

## Historical rankings

[Sprint 5 top ten](reports/sprint5/TOP10_CAUSAL_GENE_CANDIDATES.csv) and [top-twenty-labelled panel](reports/sprint5/TOP20_RESEARCH_PRIORITY_GENES.csv) are **historical**, before completed within-family/sc-eQTL integration. The latter includes 25 entities because Pareto layers 1–2 were retained together. Neither is a current list of enhancement targets. The release does not generate a publicity ranking.

The Sprint 5A shortlists A/B/C are also retained as the original research record. The current corrected matrix and decision live exclusively under [data/release](data/release/README.md). All upstream genome-wide results are inherited; only the checks and cached re-adjudication listed in [validation](reports/release/VALIDATION.md) were performed for this release.
