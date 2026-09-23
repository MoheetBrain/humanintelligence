# GOSR1 — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Numbers in section 2 come from `data/sprint5/dossier_evidence_packets.json` and are reproduced unchanged.

## 1. Verdict

**V2G_SUPPORTED_WEAK_LOCUS (locus L84282, stratum L3).** GOSR1 is the only annotated gene carrying evidence at a weak,
low-credible-set 17q11.2 locus, and it has the single cleanest variant→gene arrow of my six genes (the GWAS lead itself is the
brainSCOPE eQTL lead in L2/3 IT neurons, r²=0.996) — but that arrow rests on one cell type, one cohort unit, and a Golgi SNARE
with no cognition-relevant perturbation evidence in any species.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L84282, MAGMA label GOSR1, stratum **L3**, log10BF_independent 0.3212, locus rank 31 (interval 13–88), gc_aligned_z 1.816, panel A |
| Lead SNP | rs7212107 (cognition-increasing allele C; Davies z −5.04, Tweedie-corrected 3.832) |
| Credible sets | Only **1** cognition credible set, from **one** study (GCST006571 = Lee 2018 educational attainment MTAG, an EA *proxy* channel). `assignment_basis` is flagged: "any classified cognition-channel study (no direct-tier set) - FLAGGED" |
| V2G classes | QTL only (1 unit); n_classes 1; **no other gene in the locus carries any class** (max_classes_other_gene_in_locus 0) |
| FOCUS | primary PIP 0.0, no contradiction recorded. `joint_gene_tissue_finemapping.csv` has **no rows for L84282** — read as "not evaluated", not as evidence against |
| Open Targets L2G 26.06 | GOSR1 0.4306; second gene CPD 0.1251; rank-1 majority gene GOSR1 (fraction 1.0); top SHAP = distanceSentinelTssNeighbourhood (POSITIONAL); flags NO_OLD_ASSIGNMENT; POSITIONAL_ONLY; **MULTI_GENE_AMBIGUITY** |
| Direction | D3 / RESOLVED_ON_ROWS_ONLY_NOT_ROBUST: 9 rows, row agreement 1.0, but **1** cohort unit (GTEx only), 9 pooled pairs. Majority: cognition-increasing allele → **HIGHER** GOSR1 |
| brainSCOPE | 17 gene×cell-type tests, **1 SIGNIFICANT**: L2/3 IT (n=346), aligned direction HIGHER, eQTL lead = rs7212107 itself (p 3.5e-7, aligned beta +0.40), gene best hit chr17:30538951:A:G p 4.3e-8, r² vs GWAS lead 0.996 (EQTL_LEAD_TAGS_GWAS_LEAD_R2_GE_0.8), bulk-vs-cell-type AGREE. Independence note: brainSCOPE contains CMC_MSSM and ROSMAP donors, so it is not independent of CommonMind/ROSMAP bulk — but here bulk is **GTEx**, whose donors are not in brainSCOPE, so this pairing is closer to independent than for my 22q13 genes |
| Expression | GTEx adult brain median 7.143 TPM; developmental class MIXED |
| Perturbation | P5 (none); rare_coding_rows empty; LOEUF (lof_oe_upper) 1.753 — LoF-tolerant |
| Dosage sensitivity (Collins 2022 rCNV) | pHaplo 0.135, pTriplo 0.277 — not dosage sensitive |
| Leave-one-class-out | POSITIONAL_ONLY (dropping the single QTL class leaves nothing) |
| Ranks | B causal-gene 32; E research priority 16 (Pareto layer 2); A locus 31; C direction 4; D perturbation 36 |
| Gate A / within-family | NOT_TESTABLE (OPENGWAS_JWT absent; Howe 2022 files absent). Gate B: G&C_SUPPORTED, FDR 0.2189 |

## 3. Three questions, kept separate

- **A. Is GOSR1 a causal cognition gene? Not supported.** One QTL class at a locus whose only credible set comes from an
  educational-attainment proxy MTAG. No human perturbation evidence (P5), no rare-variant signal, no animal cognition data.
  The packet's own answer is "no human perturbation evidence".
- **B. Is it a natural high-cognition gene? Not supported (weak).** L3 stratum, "concordant but weak outside UKB"
  (log10BF_independent 0.32, gc_aligned_z 1.816). One EA-proxy credible set is a thin foundation for a cognition claim.
- **C. Is it adult-modifiable? Not testable.** The adult direction is RESOLVED_ON_ROWS_ONLY_NOT_ROBUST (9 rows, 1 cohort unit);
  the developmental class is MIXED, so we cannot say the window is adult. Modality tractability is absent (section 6).

## 4. Explicit causal chain

1. variant rs7212107 → regulatory element — **INFERRED**. The variant is a GOSR1 intronic variant; we have no element-level
   assay (no ENCODE-rE2G link, no scATAC peak recorded for this locus in our tables).
2. element → GOSR1 transcript — **EVIDENCED (single method, single cell type)**. brainSCOPE L2/3 IT: the GWAS lead *is* the eQTL
   lead, r²=0.996 with the gene's best hit; plus 9 GTEx bulk coloc rows.
3. GOSR1 → cell type — **EVIDENCED, narrow**. Significant in 1 of 17 cell types tested (L2/3 IT); 16 tested-not-significant.
4. direction: cognition-increasing allele → HIGHER GOSR1 — **INFERRED**. Consistent across 9 rows and agreeing with the single
   cell type, but only one cohort unit, so the protocol does not call it resolved.
5. GOSR1 level → cognition — **MISSING**. No perturbation in human, mouse, fly or cell models ties GOSR1 dosage to learning,
   memory or any cognitive measure.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 10198168; doi:10.1006/geno.1998.5649 (Bui 1999) | GS28/GOSR1 is a Golgi Qb-SNARE; mapped to chromosome 17 | MECHANISTIC_ONLY | Founding characterisation; nothing about brain or cognition |
| PMID 12388752; doi:10.1091/mbc.e02-01-0004 (Xu 2002); PMID 15215310; doi:10.1091/mbc.e03-12-0876 (Tai 2004) | GS28 forms the syntaxin-5/Ykt6/GS15 SNARE complex driving ER→Golgi and endosome→TGN transport | MECHANISTIC_ONLY | Cell-free/HeLa biochemistry. Establishes essential housekeeping function, which argues *against* a graded cognition-specific role |
| PMID 21860593; doi:10.4196/kjpp.2011.15.3.149 (Lee 2011) | GS28 protects neuronal cells from H₂O₂ death under glutathione depletion, via p38 MAPK restraint | MECHANISTIC_ONLY | The only neuronal GOSR1 study I found. Cell line, oxidative-stress paradigm, single group, not replicated. It is the source of the "protective" clause in our UniProt function text, so our packet text and this paper are the **same evidence**, not two |
| PMID 28516910; doi:10.1038/ncomms15353 (Lu 2017, Nat Commun) | 17q11.2 is genome-wide significant for brain epigenetic ageing rate; lead rs2054847 has cis-eQTLs for EFCAB5 (strongest), **GOSR1 (p 5.5e-12)**, CRLF3 and BLMH | SUPPORTING (weak) / alternative-gene warning | Independent GWAS and phenotype, and it confirms GOSR1 is a real brain cis-eGene. But rs2054847 (17:30204995) is only r²=0.37 / D'=0.80 with our rs7212107 in 1000G CEU (Ensembl LD REST, queried 2026-09-23), so it is a **different, partly-correlated signal**, and the authors themselves favoured EFCAB5 over GOSR1 |
| PMID 23449775; doi:10.1093/brain/awt021 (Boissé Lomax 2013); PMID 41261947; doi:10.1002/jimd.70115 (Polet 2025) | Biallelic **GOSR2** variants cause North Sea progressive myoclonus epilepsy with ataxia, areflexia and scoliosis | DISEASE_ONLY (paralog) | This is the closest "SNARE dosage matters in brain" anchor, but it is the *paralog* GOSR2 (Qb-SNARE of a different complex). Using it for GOSR1 is a category error; I record it only as biological plausibility |
| PMID 31010806; doi:10.1128/MCB.00037-19 (Kerins 2019) | Genome-wide CRISPR screen: GOSR1 loss disrupts autophagy and converges on NRF2 | MECHANISTIC_ONLY | Cancer cell lines; shows GOSR1 is functionally non-redundant in cells, again a housekeeping argument |
| PMIDs 28638266, 22397410, 21696638 | GS28 nuclear expression predicts colorectal cancer prognosis; GS28–MDM2–p53 complexes modulate cisplatin apoptosis | DISEASE_ONLY | Oncology context only; relevant to section 7 |
| Our `opentargets_refresh.csv` (Open Targets 26.06) | L2G assigns GOSR1 at 0.43 with CPD second at 0.13; flagged MULTI_GENE_AMBIGUITY and POSITIONAL_ONLY | CONTRADICTING (internal, and **NON-INDEPENDENT**) | It uses the same Davies/OT credible sets as our V2G layer, so it cannot corroborate; its value is that it says the assignment is distance-driven |
| Our own packet | Only 1 credible set, from an EA-proxy study (GCST006571) | CONTRADICTING (internal) | The locus barely qualifies as a cognition locus under our own channel rules |

Rows sharing data: the Open Targets row and our QTL/positional evidence share the Davies 2018 / Open Targets credible sets.
Lee 2011 and the packet's `function_summary` are the same primary observation. brainSCOPE and our GTEx bulk coloc use
**different donors**, so those two are not double-counting (unlike at 22q13).

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: Golgi SNAP receptor complex member 1 (GS28), a Qb-SNARE; single-pass type IV membrane protein of the Golgi
  membrane (packet `subcellular_locations`).
- Structure/pocket evidence: "none recorded". Small-molecule tractability: **none**. Antibody tractability: UniProt SigP/TMHMM
  bucket only. PROTAC bucket: "Database Ubiquitination; Half-life Data". Other modalities: none.
- High-quality chemical probes: **0**. Clinical candidates: **0**. No ChEMBL target class is recorded.
- No tool compound, inhibitor or probe specific to GS28 was found in this search. The only published perturbation handles are
  genetic (siRNA/CRISPR) and the non-selective SNARE disruptor NEM used in the classic biochemistry.
- Consequence for question C: even if the direction were resolved, there is currently no characterised way to modulate this
  target selectively. This sentence is a statement about the evidence base, not a proposal.

## 7. Pleiotropy and safety

LOEUF 1.753 and Collins pHaplo 0.135 / pTriplo 0.277: GOSR1 is LoF-tolerant and not dosage sensitive in humans, and no
Mendelian GOSR1 disease is recorded — which cuts both ways (no safety signal, but also no evidence that its dosage matters).
The 17q11.2 neighbourhood is heavily pleiotropic: SLC6A4 (serotonin transporter, 17:30.19–30.24 Mb) sits ~255 kb from our lead,
CRLF3/ATAD5/TEFM ~280–400 kb away, and NF1 (17:31.09–31.38 Mb) ~600 kb away. Any phenotype attributed to this interval must be
checked against the serotonin-transporter and NF1 literatures before being called GOSR1. Because GS28 is a core Golgi transport
SNARE, a systemic reduction would be expected to affect secretory traffic in every cell type; that is a general-biology
inference, not an observation, and it is one more reason not to treat this gene as an intervention candidate.

## 8. Largest contradiction

Our strongest single arrow (rs7212107 is itself the L2/3 IT eQTL lead, r²=0.996) sits on the weakest possible locus foundation:
one credible set, from one educational-attainment MTAG proxy study, flagged MULTI_GENE_AMBIGUITY, with locus rank interval
13–88. The independent GWAS that does implicate GOSR1 as a brain cis-eGene (Lu 2017) is at a different, only partly correlated
signal (r²=0.37) and its authors preferred EFCAB5. So the variant→gene link is good and the locus→cognition link is poor.

## 9. Missing arrow and the single best next computation

Missing arrow: **GOSR1 level → cognition** (step 5), and secondarily the element arrow (step 1).

Best next computation: re-derive the locus from the *direct-tier* cognition GWAS rather than the EA proxy — i.e. run SuSiE
fine-mapping of the Davies 2018 general-cognition summary statistics across 17:30.0–31.0 Mb and colocalise the resulting
credible set separately against GOSR1, EFCAB5, CRLF3, ATAD5 and SLC6A4 adult-brain eQTLs (eQTL Catalogue GTEx brain +
CommonMind + ROSMAP, giving ≥3 cohort units), reporting per-gene PP.H4 and aligned effect sign. This single run tests (a) whether
L84282 survives at all without the EA-proxy set, (b) whether GOSR1 beats EFCAB5 — the gene Lu 2017 preferred — and
(c) whether the HIGHER direction replicates in a second cohort unit, which is exactly what D3 currently lacks.
