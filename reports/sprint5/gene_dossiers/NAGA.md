# NAGA — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Known compounds are listed as facts; nothing here designs, doses or
recommends any intervention. Written 2026-09-23 (UTC). Section 2 numbers come from
`data/sprint5/dossier_evidence_packets.json`, unchanged.

## 1. Verdict

**LIKELY_QTL_PASSENGER (locus L1565, stratum L3).** NAGA is the only gene at 22q13.2 with a real Mendelian anchor
(Schindler/Kanzaki disease, DDG2P "definitive") and the only one with an independent published brain-eQTL→psychiatric-phenotype
mechanism (schizophrenia, via the NDUFA6 missense variant rs1801311), and the sign of that mechanism is concordant with ours —
but it loses our own FOCUS by an order of magnitude (0.089 vs CYP2D6 0.811), its direction is rows-only, and it is significant in
just 1 of 17 brainSCOPE cell types.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L1565 (MAGMA label SEPTIN3), stratum **L3**, log10BF_independent 0.3144, locus rank 34 (interval 8–109), gc_aligned_z 1.384, panel A |
| Lead SNP | rs28670611 (effect allele T, Davies z −6.635) |
| V2G classes | QTL only; n_classes 1; class_detail {"QTL": 2}. Other genes with classes: CYP2D6, PHETA2, SEPTIN3, WBP2NL |
| FOCUS | primary PIP **0.089**; best other CYP2D6 0.81; **focus_contradiction True**; contested True |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 8 rows, row agreement 1.0, **2** cohort units (gtex; rosmap), 5 pooled pairs. Majority: cognition-increasing allele → **LOWER** NAGA |
| brainSCOPE | 34 tests, **2 SIGNIFICANT** (one cell type × 2 query sets): L5 IT (n=333), LOWER, eQTL lead rs28579115 p 2.6e-7, aligned beta −0.386; gene best hit chr22:42067362:C:T p 2.1e-7, r² vs GWAS lead 0.572 (EQTL_LEAD_MODERATE_LD). Cross-cell-type ALL_LOWER, bulk-vs-cell-type AGREE. `brainscope_tagging_celltypes` is null in the packet because the single hit did not meet the tagging threshold |
| Expression | GTEx adult brain median 5.874 TPM; developmental class MIXED |
| Perturbation | **P4** — the only gene of my six above P5. `perturbation_note`: "DD/ID disease gene (DISEASE_ONLY)". Rank D perturbation 12 (vs 36 for the others) |
| Rare coding | rare_coding_rows empty. NAGA is in our `dd_confirmed_definitive_or_strong` and `dd_id_confirmed` sets, sourced from DDG2P: G2P00058, NAGA-related Kanzaki disease, biallelic_autosomal, **definitive**, absent gene product, loss of function |
| Dosage (Collins 2022) | pHaplo 0.388, pTriplo 0.467 |
| LOEUF | 1.121 |
| Open Targets L2G 26.06 | locus → SEPTIN3 0.8518; second CYP2D7 0.5562; rank-1 majority CYP2D7; POSITIONAL_ONLY |
| Leave-one-class-out | POSITIONAL_ONLY |
| Ranks | B causal-gene 45; E research priority 18 (Pareto layer 2); A locus 34; C direction 4; **D perturbation 12** |

## 3. Three questions, kept separate

- **A. Is NAGA a causal cognition gene? Not supported.** The packet's answer, "no human perturbation evidence", is correct for
  *cognition as a quantitative trait*. What exists is a recessive lysosomal disease (DISEASE_ONLY), which is a different
  question: biallelic enzyme ablation causing neuroaxonal dystrophy says little about whether common variation shifting NAGA
  mRNA by a fraction of an SD moves cognitive ability.
- **B. Is it a natural high-cognition gene? Not supported (weak).** L3 locus; concordant but weak outside UKB.
- **C. Is it adult-modifiable? Not testable.** Direction is rows-only across 2 cohort units that partly share donors with
  brainSCOPE; developmental class MIXED; and gene assignment at the locus is contested (FOCUS 0.089).

## 4. Explicit causal chain

1. variant rs28670611 → element — **MISSING**. No enhancer link, no scATAC peak, and the brainSCOPE eQTL lead (rs28579115) is
   only r²=0.57 with the GWAS lead.
2. element → NAGA transcript — **EVIDENCED, weakly**. 2 bulk QTL units; 1 significant cell type.
3. NAGA → cell type — **EVIDENCED, very narrow**: L5 IT only, 32 of 34 tests not significant.
4. direction (cognition allele → LOWER NAGA) — **INFERRED** (rows-only). Worth noting the cross-study sign concordance: Li 2021
   reports the schizophrenia **risk** allele → **higher** NAGA. Since cognition and schizophrenia are negatively genetically
   correlated, "cognition-increasing → lower NAGA" and "SZ-risk → higher NAGA" have the same sign. That is a genuine, if soft,
   external consistency check.
5. NAGA level → cognition — **MISSING**. Li 2021's neural-stem-cell work shows NAGA affects proliferation/differentiation, which
   is a developmental cellular readout, not cognition.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 33931730; doi:10.1038/s41380-021-01125-x (Li 2021, Mol Psychiatry) | At the **22q13.2 schizophrenia locus**, the missense variant rs1801311 in NDUFA6 is the likely causal variant, acting regulatorily by disrupting YY1/TAF1/POLR2A binding; it physically interacts with the NAGA promoter and is the strongest eQTL for **NAGA** in human brain; risk allele G → **higher** NAGA; NAGA is up-regulated in schizophrenia brains; NAGA knockdown/over-expression alters neural-stem-cell proliferation and differentiation; association independently replicated in a Chinese cohort | **SUPPORTING (strongest external support for any of my six genes) — with caveats** | This is the only paper that supplies an element→gene→cell-biology chain at this locus for NAGA, and the sign is concordant with ours. Caveats: (i) the phenotype is schizophrenia, not cognition; (ii) the causal variant they nominate, rs1801311 (22:42,090,719), is only r²=0.327 (D'=0.956) with our lead rs28670611 and r²=0.364 with rs133330 in 1000G CEU (Ensembl LD REST, 2026-09-23) — i.e. a **related but distinguishable signal**; (iii) their brain-eQTL resources (CommonMind/ROSMAP-type panels) overlap ours, so this is **partially NON-INDEPENDENT** |
| DDG2P G2P00058 (retrieved in `data/raw/sprint5/rare_coding/DDG2P_panel_DD_download.csv`); OMIM 609241/609242 | Biallelic NAGA loss of function causes Schindler disease (infantile neuroaxonal dystrophy) and Kanzaki disease (angiokeratoma corporis diffusum with mild neurological involvement); confidence "definitive" | **DISEASE_ONLY** | This is what earns P4. It is recessive, complete-ablation biology at the opposite end of the dose–response curve from a common eQTL |
| PMID 15136691; doi:10.1212/01.wnl.0000123116.96441.34 (Umehara 2004) | Neurological manifestations of Kanzaki disease | DISEASE_ONLY | Adult-onset, peripheral/autonomic emphasis |
| PMID 31468281; doi:10.1007/s12031-019-01398-6 (Mohamed 2020) | A homozygous NAGA p.L280I gives 5.9% residual activity in a severely affected boy and 12.1% in his **asymptomatic** sister and cousin — "extreme intrafamilial phenotypic heterogeneity" | **CONTRADICTING** | The cleanest genotype–phenotype decoupling available for this gene: near-total enzyme loss can be clinically silent. That badly undermines any graded "less NAGA → worse/better cognition" model |
| PMID 19683538; doi:10.1016/j.jmb.2009.08.021 (Clark 2009, J Mol Biol) | 1.9 Å crystal structure of human α-NAGA; molecular basis of Schindler and Kanzaki mutations | MECHANISTIC_ONLY | Supplies the structural basis noted in section 6 |
| PMID 23045655; doi:10.1073/pnas.1203924109 (Clark 2012, PNAS) | The iminosugars DGJNAc and DGJ act as **pharmacological chaperones** for human α-NAGA in vitro and in vivo; 1.4–1.5 Å complexes explain the affinity | MECHANISTIC_ONLY (and the section-6 fact base) | Listed as existing chemistry only. These are chaperones for a recessive enzyme deficiency, an entirely different problem from common-variant expression shifts |
| PMID 35521802; doi:10.1080/15622975.2022.2070667 (Yılmaz 2023); PMID 36102137; doi:10.1080/15622975.2022.2124451 (Yılmaz 2023) | Low plasma α-NAGA concentration in schizophrenia and in bipolar disorder | **CONTRADICTING (direction) — and non-independent of each other** | These report *lower* peripheral α-NAGA in psychiatric illness, the opposite sign to Li 2021's higher brain NAGA in schizophrenia. Small case–control plasma studies from one group, two papers, one evidence line. Peripheral protein ≠ brain mRNA |
| PMID 42008923; doi:10.1016/j.ymgme.2026.110129 (Casazza 2026); PMID 32517081; doi:10.3390/cells9061411 (Naumchik 2020) | Glycoproteinoses incl. Schindler disease: clinical landscape and the role of haematopoietic cell transplant | DISEASE_ONLY | Context for section 7 |
| Our `opentargets_refresh.csv` | Locus assigned to SEPTIN3 0.85; rank-1 majority CYP2D7; POSITIONAL_ONLY | CONTRADICTING (alternative gene) — **NON-INDEPENDENT** | Same Davies/OT credible sets as ours |
| Our FOCUS table | NAGA 0.089 primary; 0.036–0.095 across the other configurations; never wins | CONTRADICTING (internal) | NAGA is stably a minor contributor, unlike WBP2NL whose rank flips by configuration |

Rows sharing data: the two Yılmaz papers; Li 2021 with our eQTL panels; Open Targets with our GWAS.

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: α-N-acetylgalactosaminidase, a lysosomal glycoside hydrolase (ChEMBL: Enzyme; Hydrolase) that removes terminal
  α-GalNAc residues from glycolipids and glycopeptides. Subcellular location: lysosome (not extracellular/membrane in the packet).
- Tractability (packet): "Structure with Ligand" for both structure/pocket and small-molecule buckets; antibody "UniProt SigP or
  TMHMM"; PROTAC "Database Ubiquitination; Half-life Data". High-quality chemical probes **0**; clinical candidates **0**.
- Existing chemistry, as fact: the iminosugars **DGJNAc** and **DGJ (migalastat)** bind and chaperone α-NAGA
  (PMID 23045655); migalastat is an approved pharmacological chaperone for a different lysosomal enzyme (α-galactosidase A in
  Fabry disease). Enzyme-replacement and haematopoietic-transplant approaches are discussed for glycoproteinoses generally
  (PMID 32517081). **All of this is recorded as existing pharmacology for a rare recessive disease; none of it is suggested for
  any cognitive purpose, and this dossier makes no dosing, self-use or intervention recommendation.**
- Direction mismatch to note: every existing modality *raises* residual enzyme activity, whereas our (unresolved) direction says
  the cognition-increasing allele goes with *lower* NAGA. Even as pure characterisation, the available chemistry points the
  wrong way.

## 7. Pleiotropy and safety

LOEUF 1.121; pHaplo 0.388 / pTriplo 0.467 — mid-range. The safety profile is dominated by the recessive disease: biallelic
ablation causes a severe infantile neuroaxonal dystrophy in some families and is clinically silent in others
(PMID 31468281), so penetrance is poorly predictable. Heterozygous carriers are not reported as affected. The packet records no
`safety_liabilities`. Locus pleiotropy at 22q13.2 is severe (CYP2D6 pharmacogenetics, NDUFA6 schizophrenia, SEPTIN3, TCF20,
WBP2NL), so phenotypes in this interval should not be attributed to NAGA without conditional analysis.

## 8. Largest contradiction

Li 2021 and our own tables disagree about which gene and which variant carry the 22q13.2 signal. Li 2021 nominates rs1801311
(NDUFA6 missense) acting on NAGA; our credible-set machinery nominates rs28670611 acting on CYP2D6 (FOCUS 0.811) with NAGA at
0.089 — and the two variants are only r²=0.33 apart, so they are *different signals in the same block*, not the same finding
re-described. Layered on top is the intrafamilial heterogeneity of Schindler disease (PMID 31468281): two relatives with 12%
residual α-NAGA activity and no symptoms at all. If near-complete enzyme loss can be phenotypically silent, a common-variant
mRNA shift is unlikely to move cognition measurably.

## 9. Missing arrow and the single best next computation

Missing arrow: **variant → element** (step 1) — we have no element, and our eQTL lead is only r²=0.57 with the GWAS lead.

Best next computation: **conditional/multi-signal fine-mapping of 22q13.2 with rs1801311 modelled explicitly.** Run SuSiE on the
Davies cognition statistics across 22:41.8–42.3 Mb allowing ≥3 causal signals, then (a) test whether the cognition credible set
containing rs28670611 is statistically distinct from the schizophrenia/NDUFA6 signal indexed by rs1801311, and (b) re-run the
NAGA, CYP2D6 and WBP2NL colocalisations conditioning on rs1801311 and on the CYP2D6 star-allele haplotype. This decides whether
NAGA's apparent support from Li 2021 is support at all — i.e. whether our cognition signal and their schizophrenia signal are
one mechanism or two neighbours — which is the single fact that would change NAGA's classification.
