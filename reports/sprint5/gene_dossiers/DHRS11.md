# DHRS11 — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Known compounds are listed as facts; nothing here designs, doses or
recommends any intervention. Written 2026-09-23 (UTC). Section 2 numbers come from
`data/sprint5/dossier_evidence_packets.json`, unchanged.

## 1. Verdict

**LIKELY_QTL_PASSENGER (locus L79922, stratum L3).** DHRS11 wins our primary FOCUS configuration (0.803) and has a consistent
LOWER direction across 21 rows and 4 cortical excitatory/inhibitory cell types, but the win is configuration-fragile (GGNBP2
takes 0.821 in the GTEx-cortex-only run, ZNHIT3 0.506 in the brain-prioritised run), Open Targets assigns the locus to GGNBP2,
and the gene itself is an NADP-dependent steroid reductase with no neural literature whatsoever.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L79922, MAGMA label DHRS11, stratum **L3**, log10BF_independent 0.3591, locus rank 25 (interval 10–90), gc_aligned_z 1.792, panel A |
| Lead SNP | rs1005552 (effect allele T, Davies z −5.532; cognition-increasing allele C) |
| Credible sets | 12 cognition credible sets across 11 studies (direct_strict/direct_mtag) |
| V2G classes | QTL only; n_classes 1; class_detail {"QTL": 1}. Other genes with classes: GGNBP2, MYO19 (max 2 classes — **more than DHRS11**) |
| FOCUS | primary PIP **0.803**; best other TADA2A 0.24; focus_contradiction False; **contested True** |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: **21 rows** (the most of my six), row agreement 1.0, but **1** cohort unit (gtex), 11 pooled pairs. Majority: cognition-increasing allele → **LOWER** DHRS11 |
| brainSCOPE | 17 tests, **4 SIGNIFICANT**, all LOWER: Chandelier/Pvalb (rs35751000, p 1.3e-7), L2/3 IT (rs1005551, p 1.0e-12), L5 IT (rs12937411, p 2.5e-9, r² 0.842 vs GWAS lead, EQTL_LEAD_IN_GWAS_CREDIBLE_SET), L6 IT (rs1075218, p 1.5e-8, r² 0.821, in credible set). Two leads are indels whose LD was not computable. Cross-cell-type ALL_LOWER; bulk AGREE |
| Expression | GTEx adult brain median 14.70 TPM; developmental class **ADULT_DYNAMIC** |
| Perturbation | P5 (none); rare_coding_rows empty; **LOEUF 0.907** — the most LoF-constrained of my six |
| Dosage (Collins 2022) | pHaplo 0.230, pTriplo 0.633 |
| Open Targets L2G 26.06 | locus → **GGNBP2** 0.8955 (stable vs Sprint 4); second **DHRS11** 0.7858; rank-1 majority GGNBP2 (0.417); top SHAP distanceSentinelFootprintNeighbourhood (POSITIONAL); flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Leave-one-class-out | POSITIONAL_ONLY |
| Ranks | B causal-gene 43; E research priority 34 (Pareto layer 3); A locus 25; C direction 4; D perturbation 36 |

FOCUS configuration detail (`reports/sprint4/joint_gene_tissue_finemapping.csv`): DHRS11 leads the two joint gene×tissue
configurations (0.803, 0.805) and the 1/n-genes prior run (0.571), but **ZNHIT3 wins** `brain_prioritized_gene_p1e-3`
(0.506 vs DHRS11 0.442) and its intercept variant, and **GGNBP2 wins** the GTEx-v8-cortex-only configurations (0.653 and 0.821
vs DHRS11 0.315 and 0.149). Other genes reaching non-trivial PIP across configurations: SYNRG (0.42), ACACA (0.36), TADA2A
(0.24–0.26), DUSP14 (0.28), MYO19, C17orf50, PLXDC1. This is the most gene-dense contested locus of my six.

Locus geography (Ensembl GRCh38): the lead rs1005552 (17:36,593,168) sits inside DHRS11 (36,591,782–36,600,809); within ±150 kb
lie ZNHIT3, MYO19, PIGW, GGNBP2 and MRM1.

## 3. Three questions, kept separate

- **A. Is DHRS11 a causal cognition gene? Not supported.** One QTL class, no human perturbation evidence (P5), no rare-variant
  signal, and no published neural or behavioural work on this gene in any species.
- **B. Is it a natural high-cognition gene? Not supported (weak).** L3: concordant but weak outside UKB (log10BF 0.359, z 1.792).
- **C. Is it adult-modifiable? Not testable, though it is the best-placed of my six to become testable.** The developmental class
  is ADULT_DYNAMIC and expression is decent (14.7 TPM), but the direction rests on a single cohort unit (GTEx) and the gene
  assignment is contested.

## 4. Explicit causal chain

1. variant rs1005552 → element — **INFERRED**. The variant is intronic in DHRS11 with no enhancer link in our tables; in L5 IT
   and L6 IT the brainSCOPE eQTL leads are flagged as members of the GWAS credible set (r² 0.842 and 0.821 vs the lead;
   rs1005552–rs12937411 r²=0.861 in CEU, Ensembl LD REST 2026-09-23), so the variant-level overlap is real but the element is not
   identified.
2. element → DHRS11 transcript — **EVIDENCED**. 21 coloc rows (GTEx) + 4 brainSCOPE cell types.
3. DHRS11 → cell type — **EVIDENCED, cortical**: two IT excitatory classes (L5, L6), one upper-layer (L2/3), one inhibitory
   (Chandelier/Pvalb); 13 of 17 tests not significant.
4. direction (cognition allele → LOWER) — **INFERRED**. Unanimous over 21 rows and 4 cell types, but one cohort unit only, and
   brainSCOPE shares donors with CommonMind/ROSMAP (though our bulk unit here is GTEx, which is donor-disjoint from brainSCOPE —
   so this pairing is closer to two real units than the label suggests).
5. DHRS11 level → cognition — **MISSING**. No cognitive, behavioural or neuronal perturbation of DHRS11 exists.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 26920053; doi:10.1016/j.bbrc.2016.01.190 (Endo 2016) | Human DHRS11 is a novel 17β-hydroxysteroid dehydrogenase: reduces the 17-keto group of estrone and androstenes and the 3-keto group of 3,17-/3,20-diketosteroids; NADPH-dependent | MECHANISTIC_ONLY | The defining enzymology, and the source of our packet's `function_summary` — so the packet and this paper are **one** evidence line |
| PMID 31926269; doi:10.1016/j.jsbmb.2020.105586 (Endo 2020) | DHRS11 vs AKR1C isoforms: substrate and reaction specificity, incl. reduction of 11-oxygenated androgens (11KA4, 11K-Adione) | MECHANISTIC_ONLY | Same group; count with the row above |
| PMID 36430833; doi:10.3390/ijms232214356 (Kudo 2022); PMID 41015102; doi:10.1016/j.steroids.2025.109692 (Tanio 2025); PMID 41679198; doi:10.1016/j.ejmech.2026.118649 (Miyamoto 2026) | Kobochromone A and synthetic derivatives (best: WH23, IC₅₀ 37 nM) inhibit DHRS11, suppress androgen-driven proliferation and AR expression in luminal-AR triple-negative breast cancer cells; H210 hydrogen bond validated by mutagenesis | MECHANISTIC_ONLY / DISEASE_ONLY | Establishes that DHRS11 is genuinely druggable (section 6). All oncology, all one group, none in brain |
| PMID 36759259; doi:10.1016/j.biopsych.2022.11.002 (Ge 2023, Biol Psychiatry) | Brain-pQTL Mendelian randomisation prioritises **brain DHRS11** as a candidate target for multiple sclerosis risk | SUPPORTING (existence of a brain pQTL) / DISEASE_ONLY | Useful in one way only: it confirms DHRS11 has a measurable *protein* QTL in human brain (ROSMAP/Banner pQTL panels). The phenotype is MS, not cognition, and the brain-pQTL panels partly overlap the resources behind our eQTLs |
| PMID 37639066; doi:10.1007/s12035-023-03587-2 (Ma 2024) | Two-stage brain PWAS nominates DHRS11 among ALS risk genes in the discovery stage, but it **fails validation** (only SARM1 and BCS1L replicate) | **CONTRADICTING** | A failed replication of a brain DHRS11 disease association, in the same pQTL framework as Ge 2023. Note Ge 2023 and Ma 2024 use the **same ROSMAP/Banner brain pQTL data** — they are **NON-INDEPENDENT of each other**, and the later one does not replicate |
| PMID 28335020; doi:10.1093/brain/awx040 (Anttonen 2017, Brain) | Biallelic **ZNHIT3** p.S31L causes PEHO syndrome — severe infantile encephalopathy with near-total cerebellar granule-neuron loss; zebrafish knockdown recapitulates microcephaly and oedema | **CONTRADICTING (alternative gene at the locus)** | ZNHIT3 is 90 kb from our lead, has a definitive severe neurodevelopmental Mendelian phenotype, and **beats DHRS11 in our own brain-prioritised FOCUS configuration (0.506 vs 0.442)**. On prior biology it is the far more plausible cognition gene in this interval |
| PMID 41857137; doi:10.1038/s41418-026-01707-8 (Chen 2026, Cell Death Differ) | Znhit3 regulates p53/p21 signalling and governs cerebellar granule-cell development | MECHANISTIC_ONLY (for ZNHIT3) | Strengthens the alternative-gene case |
| PMID 38216274; doi:10.1016/j.tjog.2023.10.005 (Chen 2024) and the 17q12 microdeletion literature | Recurrent 17q12 deletions (HNF1B-containing, ~1.4 Mb) cause renal cysts/MODY5 and carry a well-documented neurodevelopmental burden | DISEASE_ONLY / locus context | The recurrent 17q12 deletion interval is centred on HNF1B (~37.7 Mb), **distal to** our 36.59 Mb lead, so it does not contain DHRS11. I record it to prevent a tempting but wrong attribution |
| Our `opentargets_refresh.csv` | L2G assigns **GGNBP2** 0.8955, DHRS11 second at 0.7858, rank-1 majority GGNBP2 (0.417); POSITIONAL_ONLY | CONTRADICTING (alternative gene) — **NON-INDEPENDENT** | Same Davies/OT credible sets as ours |
| Our matrix | GGNBP2 carries **2** classes (ENHANCER_LINK + QTL) to DHRS11's 1; GGNBP2's V2G includes a 5'UTR coding variant rs3736166 with pip_max 1.0 | CONTRADICTING (internal) | On class count GGNBP2 outranks DHRS11; DHRS11 wins only on FOCUS in one configuration family |
| Our FOCUS table | ZNHIT3 0.506 and GGNBP2 0.821 win other configurations | CONTRADICTING (internal) | The 0.803 is not stable |

Rows sharing data: Endo 2016/2020 and the Kobochromone series (one group); Ge 2023 and Ma 2024 (same brain pQTL panels);
Open Targets with our GWAS.

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: dehydrogenase/reductase SDR family member 11 — a short-chain dehydrogenase/reductase acting as a 17β-HSD and
  3β-HSD. Packet subcellular locations: cytosol, Golgi, predicted secreted/secreted; flagged extracellular_or_membrane true.
- Tractability (packet): "Structure with Ligand; High-Quality Pocket" for structure and small molecule; antibody "UniProt loc
  high conf; UniProt SigP or TMHMM; GO CC med conf"; PROTAC none. High-quality chemical probes **0**; clinical candidates **0**.
- Existing chemistry, as fact: Kobochromone A (a polyphenol from *Carex kobomugi*) and 23 synthetic derivatives, of which WH23
  inhibits DHRS11 with IC₅₀ 37 nM, with a validated His210 contact (PMID 41679198). These are early oncology tool compounds with
  no CNS characterisation and no pharmacokinetic or safety package. **Listed as facts about the target's tractability only; no
  use of any of these compounds is suggested here.**
- Note on direction: our (unresolved) direction is cognition-increasing allele → LOWER DHRS11, and the available chemistry is
  inhibitory, i.e. nominally sign-compatible. I record this only to be complete; with the gene assignment contested and the
  terminal arrow missing, it carries no weight.

## 7. Pleiotropy and safety

LOEUF 0.907 makes DHRS11 the most LoF-constrained of my six, and pTriplo 0.633 suggests mild triplosensitivity — so dosage may
matter, though no Mendelian DHRS11 disease is known and the packet records no `safety_liabilities`. The biological pleiotropy is
endocrine: DHRS11 metabolises androgens (including 11-oxygenated androgens) and estrone, so altering it has an obvious
sex-steroid axis, which is a serious systemic consideration entirely separate from cognition. Locus pleiotropy at 17q12 is
substantial — ZNHIT3 (PEHO syndrome), GGNBP2, MYO19, ACACA, SYNRG, TADA2A — and the recurrent HNF1B 17q12 deletion syndrome sits
just distal.

## 8. Largest contradiction

Our FOCUS "win" for DHRS11 is an artefact of configuration choice. In the brain-prioritised configuration ZNHIT3 wins (0.506 vs
0.442); in the GTEx-cortex-only configuration GGNBP2 wins decisively (0.821 vs 0.149); Open Targets assigns the locus to GGNBP2;
and GGNBP2 carries more V2G classes than DHRS11 in our own matrix. Meanwhile ZNHIT3 — the gene our own brain-prioritised run
prefers — has a definitive Mendelian encephalopathy with cerebellar granule-neuron loss (PMID 28335020) and a 2026 paper on
granule-cell development (PMID 41857137), i.e. exactly the kind of prior biology DHRS11 completely lacks. A steroid reductase
with zero neural literature is a poor candidate to beat a neurodevelopmental Mendelian gene 90 kb away.

## 9. Missing arrow and the single best next computation

Missing arrow: **DHRS11 level → cognition** (step 5); and the gene arrow itself is contested.

Best next computation: a **multi-gene, multi-resource colocalisation of L79922 with FOCUS configuration sensitivity reported as
a band**. Concretely: colocalise the Davies cognition credible set at 17:36.4–36.8 Mb against adult-brain eQTLs for DHRS11,
ZNHIT3, GGNBP2, MYO19, TADA2A and SYNRG in eQTL Catalogue GTEx brain, CommonMind and ROSMAP separately (giving ≥3 cohort units
rather than the single GTEx unit we now have), and report per-gene PP.H4 plus the aligned effect sign, alongside the full
eight-configuration FOCUS PIP table for the same gene set. This simultaneously (a) tests whether the LOWER direction replicates
outside GTEx, which is the only thing standing between D3 and D2, and (b) settles whether DHRS11, ZNHIT3 or GGNBP2 owns the
signal — the question our own configurations currently answer three different ways.
