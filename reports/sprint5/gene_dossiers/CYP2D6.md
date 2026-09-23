# CYP2D6 — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Known drugs and probes are listed as facts; nothing here designs,
doses or recommends any intervention. Written 2026-09-23 (UTC). Section 2 numbers come from
`data/sprint5/dossier_evidence_packets.json` and are reproduced unchanged.

## 1. Verdict

**V2G_SUPPORTED_WEAK_LOCUS (locus L1565, stratum L3).** CYP2D6 wins our primary FOCUS configuration (PIP 0.811) and is
brainSCOPE-significant in 6 interneuron/excitatory classes, but the GWAS lead rs28670611 is in **complete LD (r²=1.00, CEU)**
with the CYP2D6 coding/haplotype SNP rs1135840 (S486T), so the "eQTL" is being read across star-allele and copy-number
haplotypes with a 92%-identical paralog (CYP2D7) next door — the configuration in which short-read expression estimates are
least trustworthy. I treat the CYP2D6 assignment as **not yet distinguishable from a structural/mapping artefact**.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L1565, MAGMA label SEPTIN3, stratum **L3**, log10BF_independent 0.3144, locus rank 34 (interval 8–109), gc_aligned_z 1.384, panel A |
| Lead SNP | rs28670611 (effect allele T, Davies z −6.635; cognition-increasing allele C) |
| Credible sets | 15 cognition credible sets across 13 studies (direct_strict / direct_mtag) — much better supported as a *locus* than my 17q loci |
| V2G classes | QTL only, n_classes 1, class_detail {"QTL": 2}. Other genes with classes: NAGA, PHETA2, SEPTIN3, WBP2NL (max 1 class each) |
| FOCUS | **primary PIP 0.811**; next best NAGA 0.09; focus_contradiction False; contested False |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 13 rows, row agreement 0.846, 2 cohort units (gtex; rosmap), 5 pooled pairs. Majority: cognition-increasing allele → **HIGHER** CYP2D6 |
| brainSCOPE | 34 tests, **12 SIGNIFICANT** (6 cell types × 2 query sets): Chandelier/Pvalb, L2/3 IT, L5 IT, Lamp5, Sst/Sst-Chodl, Vip — all HIGHER, cross-cell-type consistency ALL_HIGHER, bulk-vs-cell-type AGREE |
| brainSCOPE LD detail | eQTL leads tag the GWAS lead well in Chandelier (r² 0.923) and Vip (r² 0.986), moderately in Sst (0.657) and Lamp5 (0.795), but **not** in L2/3 IT (0.194) or L5 IT (0.186) — in those two the gene's best hit is a different signal |
| Independence note (ours) | "brainSCOPE includes CMC_MSSM (CommonMind) and ROSMAP donors: agreement with CommonMind/ROSMAP bulk eQTLs is NOT independent replication; GTEx donors are not in brainSCOPE" |
| Expression | GTEx adult brain median **2.319 TPM** (low); developmental class UNKNOWN |
| Perturbation | P5 (none); rare_coding_rows empty; LOEUF 1.706 |
| Dosage (Collins 2022) | pHaplo 0.382, pTriplo 0.345 |
| Open Targets L2G 26.06 | locus assignment **SEPTIN3** 0.8518 (stable vs Sprint 4); second CYP2D7 0.5562; rank-1 majority gene **CYP2D7** (0.533); top SHAP distanceSentinelFootprintNeighbourhood; flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Leave-one-class-out | POSITIONAL_ONLY |
| Ranks | B causal-gene 34; E research priority 17 (Pareto layer 2); A locus 34; C direction 4; D perturbation 36 |

FOCUS configuration detail (`reports/sprint4/joint_gene_tissue_finemapping.csv`, per-config PIP sums): CYP2D6 wins
`joint_brain_gene_x_tissue_p1e-3` (0.811) and its intercept variant (0.760), but **WBP2NL wins all four brain-prioritised
configurations** (0.915, 0.890, 0.874, 0.857), and in the GTEx-v8-cortex-only configuration two unannotated lncRNAs
(ENSG00000232710 at 22:42.136–42.140 Mb, inside the CYP2D6/CYP2D7 interval; ENSG00000270083, sense-intronic to NDUFA6) beat
CYP2D6 (0.445/0.428 vs 0.073). CYP2D6's best TWAS models are in nucleus accumbens (cv_r² 0.474) and caudate (0.540).

## 3. Three questions, kept separate

- **A. Is CYP2D6 a causal cognition gene? Not supported.** One QTL class, no human perturbation evidence (P5), no rare-variant
  signal. The functional-imaging literature (section 5) is suggestive of a CNS role for the *enzyme*, but it is small-N,
  attention-focused and does not establish causation for general cognition.
- **B. Is it a natural high-cognition gene? Not supported (weak).** "Concordant but weak outside UKB": log10BF 0.31, z 1.384.
  Note the locus *is* well-populated with credible sets; it is the out-of-UKB replication that is weak.
- **C. Is it adult-modifiable? Not testable as posed.** The adult direction is rows-only across 2 cohort units, and — decisively
  — CYP2D6 expression is measured on haplotypes that also change the protein and the gene's copy number, so "expression" is not
  a clean modifiable quantity here. Characterisation only; no intervention is proposed.

## 4. Explicit causal chain

1. variant rs28670611 → element — **MISSING/CONFOUNDED**. In 1000G CEU (Ensembl LD REST, 2026-09-23) rs28670611 is r²=**1.000**
   with rs1135840 (CYP2D6 S486T missense), r²=0.980 with rs1058164, r²=0.863 with rs133330, r²=0.842 with rs5758605 and
   rs2142694; weaker with the known functional variants rs16947 (*2 R296C, r²=0.367), rs1065852 (*10, 0.246), rs3892097
   (*4 splice, 0.226), rs28371725 (*41, 0.106) and the distal enhancer rs5758550/rs133333 (0.167). So the signal sits on a long
   star-allele haplotype, not on an isolated regulatory element.
2. element → CYP2D6 transcript — **EVIDENCED but artefact-prone**. 2 QTL units + 12 brainSCOPE hits. But CYP2D6 lies 8.5 kb from
   CYP2D7 (22:42,140,203–42,149,500) and CYP2D8P, and star alleles include gene deletions, duplications and CYP2D6/CYP2D7 hybrids
   (PMID 29875422 finds structural variation in 28.1% of samples). Several brainSCOPE "CYP2D6" best hits (chr22:42,199,252 and
   42,202,945) lie **beyond CYP2D7/CYP2D8P**, i.e. outside the gene body and past its paralogues.
3. CYP2D6 → cell type — **EVIDENCED (6 cell types)**, though 2 of the 6 leads are not in LD with the GWAS lead (r²≈0.19).
4. direction (cognition allele → HIGHER) — **INFERRED**, rows-only; the two agreeing cohort units (ROSMAP bulk and brainSCOPE)
   share donors, so this is closer to one unit than two.
5. CYP2D6 level → cognition — **MISSING**. No perturbation evidence. The enzyme's CNS literature concerns drug metabolism,
   neurotoxin inactivation and attention-related imaging, not cognitive ability.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 27046643; doi:10.1038/mp.2016.45 (Davies 2016, Mol Psychiatry) | In UK Biobank (N=112,151) the strongest chromosome-22 signal for verbal–numerical reasoning includes CYP2D6 | SUPPORTING — but **NON-INDEPENDENT** | This is UK Biobank, the same cohort our Gate-B/Gate-C machinery is trying to get away from, and the gene naming is positional. It restates our locus, it does not replicate it |
| PMID 29844566; doi:10.1038/s41467-018-04362-x (Davies 2018) | Source GWAS for our z-scores | NON-INDEPENDENT | Our own input |
| PMID 23985325; doi:10.1093/hmg/ddt417 (Wang 2013, Hum Mol Genet) | rs16947 (*2) reduces CYP2D6 expression ≥2-fold via exon-6 mis-splicing; rs5758550/rs133333 in a >100 kb downstream enhancer raise transcription >2-fold and loop to the promoter | MECHANISTIC_ONLY / CONTRADICTING for our variant | The *bona fide* regulatory variants at this gene are only weakly correlated with our lead (r² 0.17 for rs5758550; 0.37 for rs16947). If CYP2D6 expression were the cognition mediator, the enhancer haplotype — not our lead — should carry the signal |
| PMID 30520769; doi:10.1097/FPC.0000000000000363 (Ray 2019) | Haplotypes combining rs5758550 and rs16947 predict CYP2D6 activity better than *2A | MECHANISTIC_ONLY | Reinforces that expression here is a haplotype property, not a single-SNP property |
| PMID 29875422; doi:10.1038/s41436-018-0054-0 (Lee 2018, Genet Med, Stargazer) | 28.1% of HapMap samples carry CYP2D6 structural variation including CYP2D6/CYP2D7 hybrids; accurate calling needs paralog-specific copy-number analysis | **CONTRADICTING (methodological)** | This is the core red-team finding: array/short-read-based CYP2D6 expression and genotype are systematically confounded by CNV and paralog conversion. Our eQTL layer has no paralog-aware handling |
| PMID 33631352; doi:10.1016/j.jmoldx.2021.01.013 (Turner 2021) | Specific CYP2D6 haplotypes actively interfere with standard copy-number assays | CONTRADICTING (methodological) | Same point, independently |
| PMID 16169517; doi:10.1016/j.bbrc.2005.08.255 (Gaedigk 2005) | Finds **no** functional CYP2D7 transcripts in Asian, Caucasian or African-American liver/brain | CONTRADICTING | Argues against a *CYP2D7-protein* explanation — but not against CYP2D7-driven *mis-mapping* of reads, which is the artefact I am worried about |
| PMID 15051713; doi:10.1074/jbc.M402337200 (Pai 2004) | A 138delT frameshift + brain-specific splicing makes CYP2D7 functional in human brain, demethylating codeine to morphine | MECHANISTIC_ONLY, contested | Directly contradicted by Gaedigk 2005 above; I record both and rely on neither |
| PMID 11337939; doi:10.1097/00008571-200104000-00007 (Siegle 2001); PMID 12354285; doi:10.1046/j.1471-4159.2002.01069.x (Miksys 2002) | CYP2D6 mRNA/protein is expressed in human neurons (pyramidal cells, Purkinje cells), regionally variable, higher in alcoholics | MECHANISTIC_ONLY | Establishes the enzyme is genuinely present in brain — necessary but not sufficient for our chain. Note our GTEx brain median is only 2.3 TPM |
| PMID 20368706; doi:10.1038/mp.2010.42 (Kirchheiner 2011, N=188); PMID 33024081; doi:10.1038/s41398-020-01020-z (Viviani 2020, N=415) | CYP2D6 genotype groups differ in resting thalamic perfusion and in attention-network activation; the 2020 study reports "reduced cognitive efficiency in rapid metabolizers compared to poor metabolizers" | **CONTRADICTING (direction)** | These are the strongest CNS-function studies for CYP2D6, and their direction is *opposite* to ours: our cognition-increasing allele goes with HIGHER expression, whereas higher enzymatic activity is reported to go with *less* efficient on-task processing. Caveats: small N, imaging endpoints not cognitive ability, activity ≠ mRNA, and the two Viviani/Stingl papers share an author group and overlapping cohorts (mark them as one evidence line, not two) |
| PMID 42547570; doi:10.1007/s00228-026-04155-y (Lorenz 2026, ActiFE, N=872) | Anticholinergic burden from CYP2D6-metabolised drugs associates with lower MMSE only in intermediate metabolisers, and not after age/sex adjustment | DISEASE_ONLY / null | A drug-interaction effect in older adults, not a constitutive cognition effect. Its own authors call it exploratory |
| PMID 21958961; doi:10.1016/j.neurobiolaging.2011.08.014 (Mann 2012) | Brain CYP2D6 rises from fetal life to age 80 and is ~40% lower in Parkinson's cases | MECHANISTIC_ONLY / DISEASE_ONLY | Relevant to the developmental-class question (our packet says UNKNOWN); suggests adult-dynamic, but in a non-cognitive phenotype |
| PMID 32761352; doi:10.1007/s12035-020-02050-w (Stocco 2020) | Human CYP2D6 expressed in transgenic mouse brain protects against harmine neurotoxicity (ICV propranolol inhibition experiments) | MECHANISTIC_ONLY | The best in-vivo brain-CYP2D6 perturbation that exists — and its endpoint is hypothermia/tremor, not cognition. Confirms P5 is the right perturbation stratum for cognition |
| PMID 32767519; doi:10.1111/adb.12950 (Dean 2020) | In methamphetamine users, higher CYP2D6 activity score associates with thinner cortex; **no** CYP2D6 × group effect on cognition (p>0.05) | CONTRADICTING (null on cognition) | Explicitly tests cognition and finds nothing |
| Our `opentargets_refresh.csv` | Open Targets assigns the locus to SEPTIN3 (0.85), with **CYP2D7** the rank-1 majority gene across credible sets (53%) | CONTRADICTING (alternative gene) — **NON-INDEPENDENT** | Same Davies/OT credible sets as ours. Notable that the majority vote picks the *pseudogene paralog*, which is itself a symptom of the mapping problem |
| Our FOCUS table | WBP2NL wins 4/8 configurations with PIP 0.86–0.92; two unannotated lncRNAs win the GTEx-cortex-only configuration | CONTRADICTING (internal) | The 0.811 we quote is one configuration out of eight |

Rows sharing data: Davies 2016/2018 and Open Targets share our GWAS. ROSMAP bulk coloc and brainSCOPE share donors.
Kirchheiner 2011, Stingl 2011 (PMID 21248727) and Viviani 2020 come from the same Ulm/Bonn/Aachen group and overlapping samples.

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: cytochrome P450 monooxygenase (ChEMBL: Cytochrome P450 2D6 / family 2D); ER and microsome membrane,
  peripheral membrane protein; also recorded at Golgi.
- Tractability (packet): "Structure with Ligand; High-Quality Ligand; High-Quality Pocket; Druggable Family" for small molecules;
  antibody "UniProt loc med conf"; PROTAC "Half-life Data; Small Molecule Binder". High-quality chemical probes: **0**.
  Clinical candidates as a *target*: **0**.
- Existing pharmacology, stated as fact only: CYP2D6 is one of the best-characterised drug-metabolising enzymes; ~25% of
  clinically used drugs are its substrates, and a large set of approved medicines are its established inhibitors (for example
  the SSRIs paroxetine and fluoxetine, and quinidine, which are used in research as CYP2D6 inhibition probes). These are listed
  because they define the enzyme's pharmacological context; **this dossier does not suggest using any of them for any purpose.**
  In vitro, several psychotropics both inhibit and *activate* CYP2D6-catalysed dopamine formation from p-tyramine depending on
  the allozyme (PMID 34605737; doi:10.1080/00498254.2021.1989520), so "inhibitor/activator" is not even a stable label here.
- Endogenous chemistry: CYP2D6 regenerates serotonin from 5-methoxytryptamine (PMID 12618595;
  doi:10.1097/01.fpc.0000054066.98065.7b) and forms dopamine from p-tyramine — the mechanistic basis for any CNS claim.
- Practical consequence: the target is highly tractable in the medicinal-chemistry sense and completely untestable in the causal
  sense, because we cannot presently separate its expression from its haplotype/copy-number state.

## 7. Pleiotropy and safety

The packet's `safety_liabilities` field is the longest of my six genes: QTc interval, adverse events, antipsychotic-induced
extrapyramidal symptoms, bradycardia, dose of drug required, drug toxicity, gastrointestinal bleeding, opioid dependence,
sedation, tardive dyskinesia, tardive dyskinesia or parkinsonism. CYP2D6 poor-metaboliser status is a recognised
pharmacogenetic risk factor across many drug classes (PMID 34025403; doi:10.3389/fphar.2021.624104 reports more drug-related
dizziness with lower predicted activity). LOEUF 1.706 with common null alleles segregating at high frequency: loss of CYP2D6 is
compatible with normal life, which is itself an argument against a strong constitutive cognition role. Locus pleiotropy is
severe: the same 22q13.2 interval carries SEPTIN3, NAGA, NDUFA6 (schizophrenia), WBP2NL, TCF20, and is the established
endoxifen/tamoxifen-metabolism locus (PMID 38501904; doi:10.1002/cpt.3255).

## 8. Largest contradiction

Two, and they point the same way. (i) **Structural**: our lead is in perfect LD with a CYP2D6 coding variant and sits on
star-allele haplotypes that include whole-gene deletions, duplications and CYP2D6/CYP2D7 hybrids in ~28% of people
(PMID 29875422), while the paralog CYP2D7 is 8.5 kb away and is itself the rank-1 Open Targets gene in 53% of credible sets — so
a CNV/mapping artefact is a live alternative explanation for the entire "CYP2D6 eQTL". (ii) **Directional**: the best CNS
functional studies of CYP2D6 report that *higher* metaboliser activity goes with *less* efficient attentional processing
(Viviani 2020), the opposite sign to our cognition-increasing → HIGHER expression. Either would be enough to demote the gene;
together they mean the 0.811 FOCUS PIP should not be read as a gene assignment.

## 9. Missing arrow and the single best next computation

Missing arrow: **variant → element** (step 1), because the variant's effect on CYP2D6 cannot currently be separated from
haplotype structure and copy number.

Best next computation: a **paralog-aware structural-confounding test at L1565**. Concretely: (a) re-extract the CYP2D6/CYP2D7/
CYP2D8P interval (22:42.00–42.22 Mb) from the eQTL Catalogue/GTEx and brainSCOPE expression matrices and quantify what fraction
of CYP2D6-assigned reads are multi-mapping to CYP2D7 (the two are ~92% identical); (b) recompute the CYP2D6 cis-eQTL with the
star-allele/CNV haplotype (rs1135840, rs16947, rs1065852, rs3892097, rs5758550) included as covariates, and ask whether the
association with rs28670611 survives; (c) repeat the colocalisation with WBP2NL and NAGA in the same models. If the CYP2D6
signal disappears under haplotype adjustment while WBP2NL's does not, the locus should be reassigned — which is exactly the
comparison our FOCUS configurations already disagree about.
