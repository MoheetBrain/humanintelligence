# ZFTRAF1 — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Section 2 numbers come from `data/sprint5/dossier_evidence_packets.json`, unchanged.
(ZFTRAF1 was formerly **CYHR1**; several of our own tables and much of the literature use the old symbol.)

## 1. Verdict

**LIKELY_QTL_PASSENGER (locus L65265, stratum L3).** ZFTRAF1 is demoted below KIFC2 in our classifier, yet it carries **more**
eQTL units than KIFC2 (2 vs 1), is the rank-1 Open Targets gene in half of the credible sets, and — decisively for a red-team —
it acquired a Mendelian neurodevelopmental phenotype in 2024 (biallelic loss of function → global developmental delay, postnatal
microcephaly, hypotonia) that our packet does not reflect. It remains a passenger on our data, but for the wrong stated reason.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L65265 (MAGMA label FOXH1), stratum **L3**, log10BF_independent 0.3795, locus rank **22** (interval 7–99) — the best locus rank of my six; gc_aligned_z 1.668, panel A |
| Lead SNP | rs750472 (SuSiE PIP 0.151; effect allele C; Davies z −6.267) |
| V2G classes | QTL only; n_classes 1; class_detail {"QTL": **2**}. Other genes with classes: FOXH1, KIFC2, PPP1R16A, RECQL4; max_classes_other_gene_in_locus **2** (KIFC2, via ENHANCER_LINK + QTL) |
| FOCUS | primary PIP 0.0 — but `joint_gene_tissue_finemapping.csv` has **no rows at all for L65265**, so this is "not evaluated", not evidence against |
| **contested** | **True** |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 4 rows, row agreement 1.0, **2** cohort units (gtex; rosmap), 3 pooled pairs. Majority: cognition-increasing allele → **LOWER** ZFTRAF1 |
| brainSCOPE | `brainscope_tagging_celltypes` and `brainscope_direction` both **null**. Our variant summary shows 39 credible variants at L65265 with **0 tested** in the brainSCOPE eQTL call-set, so there is no single-cell direction for any gene here |
| brainSCOPE GRN (separate layer) | rs11784118 (SuSiE PIP 0.044) and rs1985022 overlap a **CYHR1 promoter element** (chr8:144,457,641–144,459,641) in 21 cell-type GRNs each, with 9–17 TFs per cell type (e.g. MEF2C, RORA, SMAD3/4, ZBTB18). `target_in_candidate_list` is **False**, i.e. this promoter link did not feed the ENHANCER_LINK class — because the class is built from Open Targets ENCODE-rE2G only |
| Open Targets V2G rows (ours) | ZFTRAF1 appears as an eQTL/sQTL/tuQTL target for ~12 credible variants at this locus, including rs11774212 (pip_max 0.72), rs112422823 (0.41) and rs750472 (0.35) |
| Expression | GTEx adult brain median 24.68 TPM; developmental class MIXED |
| Perturbation | **P5 (none)** — see section 8; rare_coding_rows empty; **LOEUF 1.163** |
| Dosage (Collins 2022 rCNV) | Listed under the **old symbol CYHR1**: pHaplo 0.169, pTriplo **0.715** (the highest pTriplo of my six genes). A symbol-keyed lookup on "ZFTRAF1" returns nothing — the same alias problem as in section 8 |
| Open Targets L2G 26.06 | locus → KIFC2 0.6535; second **ZFTRAF1 0.4886**; **rank-1 majority gene ZFTRAF1 (0.500)**; top SHAP distanceSentinelFootprintNeighbourhood (POSITIONAL); flags STABLE_ASSIGNMENT; POSITIONAL_ONLY |
| Leave-one-class-out | POSITIONAL_ONLY |
| Ranks | B causal-gene 40; E research priority 32 (Pareto layer 3); A locus 22; C direction 4; D perturbation 36 |

## 3. Three questions, kept separate

- **A. Is ZFTRAF1 a causal cognition gene? Not supported — but less unsupported than the packet says.** Our own evidence is two
  eQTL units at a weak locus, with no single-cell data. What the packet misses is that biallelic ZFTRAF1 LoF now has a published
  neurodevelopmental phenotype (PMID 38641995), which is DISEASE_ONLY evidence but is exactly the category that moved NAGA from
  P5 to P4 in our own scheme.
- **B. Is it a natural high-cognition gene? Not supported (weak).** L3: concordant but weak outside UKB (log10BF 0.38, z 1.67).
- **C. Is it adult-modifiable? Not testable.** Direction is rows-only; no cell-type data at all; developmental class MIXED; and
  the human phenotype that exists is congenital/postnatal-microcephalic, i.e. developmental rather than adult.

## 4. Explicit causal chain

1. variant → element — **EVIDENCED, but from a layer our class system ignores**. rs11784118 and rs1985022 sit in a brainSCOPE
   GRN promoter element assigned to CYHR1/ZFTRAF1 across 21 cell types. Their SuSiE PIPs are low (0.044, 0.019) and the locus's
   PIP mass is spread across 39 variants (max 0.151 at rs750472), so the variant identity is weak.
2. element → ZFTRAF1 transcript — **EVIDENCED, modest**: 2 QTL units (GTEx + ROSMAP), plus eQTL/sQTL/tuQTL annotation for
   multiple credible variants in the Open Targets V2G layer. Notably much of it is **splice/transcript-usage** QTL (sQTL/tuQTL),
   not simple expression.
3. ZFTRAF1 → cell type — **MISSING**. No brainSCOPE variant at this locus was testable.
4. direction (cognition allele → LOWER) — **INFERRED**: 4 rows, 2 cohort units, rows-only.
5. ZFTRAF1 level → cognition — **MISSING for graded variation**. The Mendelian data speak to complete loss, not to dosage.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 38641995; doi:10.1016/j.gim.2024.101143 (Asif 2024, Genet Med) | **Biallelic ZFTRAF1 loss-of-function variants cause a neurodevelopmental disorder with global developmental delay, postnatal microcephaly and hypotonia** in 5 affected individuals from 3 unrelated families; ZFTRAF1 is a nucleocytoplasmic protein, completely absent in patient fibroblasts; 110 interactors enriched for mRNA processing and autophagy; patient fibroblasts show irregular protein degradation | **SUPPORTING (DISEASE_ONLY) — the single most important paper for this gene** | Independent of our GWAS entirely. It converts ZFTRAF1 from "unknown function" (our packet's `function_summary` is NaN) into a bona fide neurodevelopmental gene. It is recessive, complete-LoF biology, so it does **not** establish that common-variant dosage shifts cognition — but by our own P4 rule ("DD/ID disease gene (DISEASE_ONLY)") it should be reflected in the perturbation stratum |
| DDG2P G2P03563 (in `data/raw/sprint5/rare_coding/DDG2P_panel_DD_download.csv`) | ZFTRAF1 (previous symbol **CYHR1**), "ZFTRAF1-related neurodevelopmental disorder", biallelic_autosomal, confidence **limited**, decreased gene product level, LoF; evidence PMID 38641995; reviewed 2025-02-27 | SUPPORTING (DISEASE_ONLY), weak confidence | This is in a file we already downloaded. The confidence is "limited", not "definitive" (NAGA is definitive), which is a legitimate reason for it not to have triggered P4 — but our gene-set build keeps only `dd_confirmed_definitive_or_strong`, so the **symbol-change plus the confidence tier together** are why this never surfaced |
| PMID 10745073; doi:10.1016/s0014-5793(00)01310-7 (Menon 2000); PMID 12765788; doi:10.1016/s0300-9084(03)00007-5 (Bawumia 2003) | CYHR1/Chrp is a cysteine- and histidine-rich cytoplasmic protein that binds galectin-3 in a carbohydrate-independent manner | MECHANISTIC_ONLY | The original characterisation; same group across both papers — **one** evidence line |
| PMID 21900684; doi:10.1095/biolreprod.111.091686 (Ly-Huynh 2011) | CYHR1 is among importin-α2-interacting proteins with nuclear roles in mammalian spermatogenesis | MECHANISTIC_ONLY | Consistent with Asif 2024's nucleocytoplasmic localisation |
| PMID 26676980; doi:10.1245/s10434-015-5031-0 (Desaki 2017); PMID 41859033; doi:10.25259/Cytojournal_49_2025 (Yu 2026) | CYHR1/ZFTRAF1 as a prognostic marker and pro-metastatic factor in oesophageal squamous-cell carcinoma and lung adenocarcinoma | DISEASE_ONLY | Oncology only; relevant to section 7 |
| Multiple bovine/ovine GWAS (PMIDs 31576624, 30639022, 38203848, 39378607, 15566480, 15147413) | CYHR1 recurs in cattle milk-production GWAS on BTA14 | NON-INDEPENDENT of each other / irrelevant | These are the same BTA14 haplotype block (adjacent to DGAT1) reported repeatedly. A textbook case of a long LD block generating apparent gene hits — the same hazard as at our own 8q24.3 |
| Our `opentargets_refresh.csv` | L2G prefers KIFC2 (0.65) but the **rank-1 majority gene across credible sets is ZFTRAF1 (0.500)** | CONTRADICTING our own ordering — **NON-INDEPENDENT** | Shares our Davies/OT credible sets. It says the gene ordering at this locus is unstable |
| Our matrix (KIFC2 row) | KIFC2 is CAUSAL_GENE_MODERATE on ENHANCER_LINK(2) + QTL(1); ZFTRAF1 has QTL(2) | CONTRADICTING (internal) | On eQTL evidence alone ZFTRAF1 ≥ KIFC2. KIFC2 wins purely on the ENCODE-rE2G class, and our own brainSCOPE GRN layer puts a 21-cell-type promoter element on ZFTRAF1 that the class system does not count |
| PMID 9115736; doi:10.1016/s0896-6273(00)81243-x (Saito 1997) and the KIFC2 literature | KIFC2 is a neuron-specific dendritic kinesin | (context for the rival gene) | KIFC2's neuronal prior is stronger than ZFTRAF1's *was* — but Asif 2024 now gives ZFTRAF1 a human neurodevelopmental phenotype that KIFC2 does not have (the Kifc2 knockout mouse is normal) |

Rows sharing data: Menon 2000/Bawumia 2003 (one group); the cattle GWAS set (one haplotype block); Open Targets with our GWAS;
DDG2P with Asif 2024 (the DDG2P entry's sole evidence is that paper).

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: zinc finger TRAF-type and RING-finger containing 1; packet `protein_type` "other/unclassified"; subcellular
  locations cytoplasm, perinuclear region, nucleoplasm; not extracellular or membrane. Asif 2024 adds a nucleocytoplasmic
  distribution and interactors enriched in mRNA processing and autophagy.
- Tractability (packet): structure/pocket evidence **none recorded**; small molecule **none**; antibody **none**; PROTAC
  **none**; other modalities none. High-quality chemical probes **0**; clinical candidates **0**; no ChEMBL target class;
  `function_summary` is NaN.
- No tool compound, probe, inhibitor or clinical programme for ZFTRAF1/CYHR1 was found. Published perturbation handles are
  genetic only (patient-derived fibroblasts, siRNA in cancer lines, zebrafish work referenced in Asif 2024).
- This is, with WBP2NL, the least tractable target of my six.

## 7. Pleiotropy and safety

LOEUF 1.163 (LoF-tolerant in heterozygotes, consistent with a recessive disorder). Biallelic loss causes developmental delay,
postnatal microcephaly and hypotonia (PMID 38641995) — a serious phenotype that establishes the gene is needed for normal brain
development, and that is a safety-relevant fact about reducing it. Cancer studies report pro-tumour effects of high expression
(PMIDs 26676980, 41859033), so both directions have an adverse literature. 8q24.3 is extremely gene-dense: RECQL4
(Rothmund–Thomson/RAPADILINO), FOXH1, PPP1R16A, KIFC2, TONSL, LRRC14, GPT, CPSF1, SCRT1, HSF1, DGAT1 — locus-level phenotypes
cannot be attributed to ZFTRAF1 without conditioning.

## 8. Largest contradiction

Our packet gives ZFTRAF1 perturbation stratum **P5 ("none")** and an empty `function_summary`, while a 2024 *Genetics in
Medicine* paper and the DDG2P file already in `data/raw/sprint5/rare_coding/` describe a biallelic ZFTRAF1 neurodevelopmental
disorder with microcephaly. The mechanical cause is identifiable: DDG2P lists it under the current symbol with previous symbol
CYHR1 and confidence "limited", and our gene sets retain only definitive/strong entries — so the gene was correctly excluded
from the *definitive* set but is nonetheless mis-described as having no disease evidence. Secondarily, ZFTRAF1 has more eQTL
units than KIFC2 and is the Open Targets rank-1 majority gene at this locus, yet is classed a passenger to KIFC2 on the strength
of one enhancer-link method.

**Flag for the parent agent:** this is a candidate correction — not to the gene's class (QTL-passenger is still defensible on our
V2G evidence), but to its perturbation annotation and to the claim "no human perturbation evidence".

## 9. Missing arrow and the single best next computation

Missing arrow: **ZFTRAF1 → cell type** (step 3) — zero brainSCOPE coverage at this locus — and the terminal dosage→cognition arrow.

Best next computation: **an alias-aware re-run of the rare-variant/disease annotation layer, followed by a joint locus
colocalisation at L65265.** Step one is cheap and should come first: re-map `rare_coding_gene_sets.json` and the perturbation
stratum assignment using HGNC previous-symbol and alias tables (CYHR1→ZFTRAF1 is the instance found here; there will be others
across the 20 dossier genes), and record DDG2P confidence tiers explicitly rather than only the definitive/strong subset. The same alias gap affects the Collins rCNV join (this gene is keyed as CYHR1 there, pTriplo 0.715), so the fix should be applied to every symbol-keyed join in the packet build, not just the DD sets. Step
two: because L65265 has **no FOCUS rows and no brainSCOPE-testable variants**, run a joint gene colocalisation of the Davies
credible set at 8:144.40–144.55 Mb against ZFTRAF1, KIFC2, PPP1R16A, RECQL4 and FOXH1 eQTLs **and sQTLs** in GTEx brain,
CommonMind and ROSMAP, reporting per-gene PP.H4 and sign. The sQTL arm matters specifically here because much of ZFTRAF1's
Open Targets V2G evidence is splice/transcript-usage rather than expression, and our QTL class does not distinguish them.
