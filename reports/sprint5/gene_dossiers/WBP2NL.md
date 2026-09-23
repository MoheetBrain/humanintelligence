# WBP2NL — gene dossier (Sprint 5, literature red-team batch 3)

Scope: target characterisation and evidence appraisal only. Nothing here designs, doses or recommends any intervention.
Written 2026-09-23 (UTC). Section 2 numbers come from `data/sprint5/dossier_evidence_packets.json`, unchanged.

## 1. Verdict

**LIKELY_QTL_PASSENGER (locus L1565, stratum L3) — and this is the classification I would most want re-examined.** WBP2NL has
by far the cleanest molecular evidence at 22q13.2 (direction fully resolved across 3 cohort units, significant in 10/10 tested
brainSCOPE cell types, all LOWER, with eQTL leads *inside the GWAS credible set*), yet it is demoted because the primary FOCUS
configuration prefers CYP2D6 — while four other FOCUS configurations put WBP2NL first at PIP 0.86–0.92. Against that stands a
hard biological fact: the gene is testis/sperm-enriched with an adult-brain median of 0.54 TPM.

## 2. Our computed evidence (from the packet)

| Field | Value |
|---|---|
| Locus | L1565 (MAGMA label SEPTIN3), stratum **L3**, log10BF_independent 0.3144, locus rank 34 (interval 8–109), gc_aligned_z 1.384, panels **A;C** |
| Lead SNP | rs28670611 (effect allele T, Davies z −6.635) |
| V2G classes | QTL only; n_classes 1; class_detail {"QTL": 3} — three QTL units, the most at this locus. Other genes with classes: CYP2D6, NAGA, PHETA2, SEPTIN3 |
| FOCUS | primary PIP **0.086**; best other CYP2D6 0.81; **focus_contradiction True**; contested True |
| Direction | **D2 / DIRECTION_RESOLVED** — the only fully resolved direction among my six genes. 6 rows, row agreement 1.0, **3 cohort units** (commonmind, gtex, rosmap), unit agreement 1.0, 4 pooled pairs. Statement: cognition-increasing allele → **LOWER** WBP2NL in adult brain |
| brainSCOPE | 34 tests, **20 SIGNIFICANT**; 10 distinct cell types, all LOWER (ALL_LOWER): Astro, Chandelier/Pvalb, L2/3 IT, L4 IT, L5 IT, L6 IT, Lamp5, Oligo, Sst/Sst-Chodl, Vip. p-values down to 4.9e-26 (L2/3 IT), effect sizes −0.47 to −0.81 |
| brainSCOPE LD detail | In 8 of 10 cell types the eQTL lead is flagged **EQTL_LEAD_IN_GWAS_CREDIBLE_SET** with r² 0.83–0.84 vs the GWAS lead (Lamp5 and Oligo are the exceptions, r² 0.29–0.31) |
| Independence caveat (ours) | brainSCOPE shares CMC_MSSM (CommonMind) and ROSMAP donors with two of the three bulk units, so the 3-unit direction is less independent than the number suggests; only GTEx is donor-disjoint from brainSCOPE |
| Expression | GTEx adult brain median **0.5388 TPM** — the lowest of my six genes; developmental class UNKNOWN |
| Perturbation | P5 (none); rare_coding_rows empty; LOEUF 1.473 |
| Dosage (Collins 2022) | pHaplo 0.460, pTriplo 0.249 |
| Leave-one-class-out | POSITIONAL_ONLY |
| Ranks | B causal-gene 44; **E research priority 13** (Pareto layer 2 — the best E rank of my six); A locus 34; **C direction 1**; D perturbation 36 |

FOCUS configuration detail (`reports/sprint4/joint_gene_tissue_finemapping.csv`): WBP2NL is the top gene in
`brain_prioritized_gene_p1e-3` (0.915), `brain_prioritized_proxy_tissue_fallback_p1e-3` (0.890),
`brain_prioritized_gene_prior_1_over_ngenes_grch37` (0.874) and `brain_prioritized_gene_p1e-3_intercept` (0.857) — in every case
from the **CommonMind DLPFC** model (TWAS z −6.47, cv_r² 0.346, r(pred expr, lead effect allele) 0.834). It is CYP2D6 that wins
only the two joint gene×tissue configurations. The protocol's primary configuration is the joint one; that choice, not the data,
is what makes WBP2NL a passenger.

## 3. Three questions, kept separate

- **A. Is WBP2NL a causal cognition gene? Not supported.** Despite the strong molecular evidence, there is no human perturbation
  evidence (P5), no rare-variant signal, no mammalian cognitive phenotype, and the protein's only characterised mammalian
  function is in sperm/oocyte biology — which is itself disputed (section 5).
- **B. Is it a natural high-cognition gene? Not supported (weak).** The locus is L3: concordant but weak outside UKB.
- **C. Is it adult-modifiable? The packet's own answer is the right one: "adult eQTL direction resolved but gene assignment not
  credible."** Direction is the one thing we *do* have; assignment is what we lack.

## 4. Explicit causal chain

1. variant → element — **INFERRED**. No ENCODE-rE2G link or scATAC peak for WBP2NL in our tables; but in 8/10 cell types the
   eQTL lead variant is itself a member of the GWAS credible set (r² 0.83–0.84), which is the strongest variant-level overlap at
   this locus.
2. element → WBP2NL transcript — **EVIDENCED, strongly**. 3 bulk QTL units + 20 significant brainSCOPE tests, p to 4.9e-26.
3. WBP2NL → cell type — **EVIDENCED, broadly**. 10 cell types including astrocytes and oligodendrocytes; this breadth is a
   double-edged result — a pan-cell-type eQTL looks more like a general regulatory haplotype than a cell-type-specific mechanism.
4. direction (cognition allele → LOWER) — **EVIDENCED**. Unanimous across 6 rows, 3 cohort units and 10 cell types.
5. WBP2NL level → cognition — **MISSING**, and here the expression level bites: 0.54 TPM in adult brain. A transcript at that
   abundance can still be an eQTL target, but a dose–response link to cognition has no support of any kind.

## 5. Literature red-team

| Source (PMID / DOI) | Claim | Category | Note |
|---|---|---|---|
| PMID 28663133; doi:10.1016/j.ydbio.2017.06.025 (Marchak 2017, Dev Biol) | **Wbp2nl knock-down in Xenopus dorsal ectoderm reduces cranial-placode and neural-crest domains and expands neural-plate domains; over-expression induces ectopic epidermal/neural-crest genes and represses neural-plate genes, partly via down-regulating chordin** | **SUPPORTING (the only neural-development evidence that exists)** | This is the single paper that makes WBP2NL neurally plausible. It is Xenopus, embryonic ectoderm patterning, not cognition; and the direction is a patterning switch, not a graded adult effect. It cannot bridge to an adult cortical eQTL |
| PMID 26377222; doi:10.1095/biolreprod.115.131441 (Satouh 2015, Biol Reprod) | **PAWP/Wbp2nl-null mice show normal spermatogenesis, normal Ca²⁺ oscillations after ICSI and normal embryo development: "PAWP does not play an essential role in mouse fertilization"** | **CONTRADICTING** | The germline knockout is phenotypically normal in the gene's own canonical function. No cognitive or neurological phenotype was reported (nor tested), but a viable, fertile null mouse is weak evidence that this gene's dosage is consequential |
| PMID 32219949; doi:10.1111/asj.13345 (Nakai 2020) | Review weighing PLCζ vs PAWP as the sperm oocyte-activating factor; concludes the PAWP case is unsettled | CONTRADICTING (function) | Relevant because the packet's `function_summary` ("may play a role in meiotic resumption…") is the disputed claim |
| PMID 28444612; doi:10.1007/s10815-017-0902-x (Freour 2017); PMID 29271520; doi:10.1002/mrd.22950 (Freour 2018) | WBP2NL mRNA/protein in sperm is **not** related to semen parameters, fertilization rate or reproductive outcome; no association with ICSI failure | CONTRADICTING | Two papers from the same group and overlapping cohorts — count as **one** evidence line |
| PMID 30010725; doi:10.1093/biolre/ioy156 (Hamilton 2018) | The paralog WBP2 co-localises with WBP2NL in sperm and is itself a candidate oocyte-activating factor | MECHANISTIC_ONLY | Paralog redundancy — another reason a WBP2NL null is tolerable |
| PMID 38501904; doi:10.1002/cpt.3255 (Sanchez-Spitman 2024, Clin Pharmacol Ther) | GWAS of endoxifen serum concentration: 430 genome-wide-significant variants "located in **TCF20 and WBP2NL** genes (chromosome 22), which are in strong linkage disequilibrium with CYP2D6 variants" | **CONTRADICTING (this is the artefact, named)** | An independent GWAS of a phenotype that is *definitionally* CYP2D6 (tamoxifen→endoxifen conversion) lands its top hits on WBP2NL. That is a direct demonstration that WBP2NL-labelled signals at this locus can be CYP2D6 haplotype signals in disguise — and, symmetrically, that LD here defeats positional gene naming in both directions |
| PMID 31344832; doi:10.3390/jcm8081087 (Hennig 2019) | Non-CYP2D6 22q variants (incl. rs8138080) improve prediction of impaired tamoxifen metabolism beyond CYP2D6 genotype | CONTRADICTING / MECHANISTIC_ONLY | Same message: the region carries CYP2D6-activity information outside CYP2D6 itself |
| PMID 42337223; doi:10.1007/s10522-026-10466-5 (Liu 2026, Biogerontology) | SMR + colocalisation nominates **WBP2NL** as a candidate target for both physical and **cognitive frailty** (PP.H4>0.8); PheWAS found no other genome-wide phenotype associations | SUPPORTING — but **NON-INDEPENDENT and low-quality** | It uses public brain/blood eQTL panels that overlap ours (the same GTEx/brain pQTL-eQTL resources) and a cognitive-frailty GWAS that shares cohorts with the cognition GWAS family; it is an automated MR screen with no experimental follow-up. I count it as an echo of our own signal, not as replication. Its "candidate drug" list is noted only as a fact and is not endorsed here |
| PMID 32054438; doi:10.1186/s12862-019-1575-0 (Schaschl 2020) | WBP2NL is among male-reproductive genes under recent population-specific positive directional selection | MECHANISTIC_ONLY | Interesting for haplotype structure at this locus — selection can create exactly the long, high-LD haplotypes that confuse gene assignment |
| Our `causal_gene_evidence_matrix.csv` / FOCUS table | WBP2NL primary PIP 0.086 vs CYP2D6 0.811; but WBP2NL 0.86–0.92 in four brain-prioritised configurations | CONTRADICTING (internal) | The passenger call is configuration-dependent |
| Our `opentargets_refresh.csv` | Open Targets assigns the locus to SEPTIN3 (0.85), rank-1 majority CYP2D7 | CONTRADICTING — NON-INDEPENDENT | Shares our GWAS |

Rows sharing data: the two Freour papers; Liu 2026 with our own eQTL resources; Open Targets with our credible sets;
brainSCOPE with CommonMind/ROSMAP donors.

## 6. Modifiability characterisation (facts only, no recommendation)

- Protein class: WBP2 N-terminal like (PAWP), a cytosolic signalling adaptor with a PH-G domain, a predicted Thr45
  phosphorylation site and a YAP-binding (PPXY) motif (PMID 28663133). Cytosol only; not extracellular or membrane.
- Tractability (packet): structure/pocket evidence **none recorded**; small molecule **none**; antibody **none**; PROTAC
  **none**; other modalities none. High-quality chemical probes **0**; clinical candidates **0**; no ChEMBL target class.
- No tool compound, inhibitor, agonist or chemical probe for WBP2NL/PAWP was found. The literature's only perturbation handles
  are genetic (morpholino/mRNA in Xenopus, germline KO in mouse) and antibody-based detection in sperm.
- Adjacent biology worth recording as fact only: a 2026 paper reports the stilbenoid vitisin B modulating senescence "via WBP2NL
  regulation" (PMID 41577206; doi:10.1016/j.mad.2026.112159). This is a cell-senescence study, not a CNS study, and the compound
  is not a characterised WBP2NL probe. Listed for completeness; not a recommendation of any kind.
- Consequence: WBP2NL is currently the least chemically tractable of my six genes.

## 7. Pleiotropy and safety

LOEUF 1.473, pHaplo 0.460, pTriplo 0.249; no Mendelian disease; a viable, fertile knockout mouse. `safety_liabilities` records
only the generic "adverse events". The real hazard here is not toxicity but **attribution**: WBP2NL sits inside the same
high-LD 22q13.2 block as CYP2D6, NAGA, NDUFA6, SEPTIN3 and TCF20, and the endoxifen GWAS (PMID 38501904) shows that variants
labelled WBP2NL can be reporting CYP2D6 pharmacogenetics. Any phenotype attributed to WBP2NL at this locus needs the same
haplotype/CNV adjustment I propose for CYP2D6.

## 8. Largest contradiction

The gene with the best molecular evidence at this locus is the one our classifier calls a passenger, and the gene it prefers
(CYP2D6) has the weaker variant-level overlap. WBP2NL's eQTL leads are *in* the GWAS credible set in 8/10 cell types (r² 0.83)
while CYP2D6's L2/3 IT and L5 IT leads are not (r² ≈0.19); WBP2NL wins 4 of 8 FOCUS configurations at PIP 0.86–0.92. The
counter-argument is equally concrete: WBP2NL is expressed at 0.54 TPM in adult brain, its canonical function is in sperm, its
knockout mouse is normal, and an independent GWAS of a purely CYP2D6-driven pharmacokinetic trait also lands on WBP2NL — which
is precisely what a shared-haplotype artefact looks like. Both stories fit the data; our tables currently assert one.

## 9. Missing arrow and the single best next computation

Missing arrow: **variant → element** (which regulatory element, in which cell type, acts on WBP2NL), and the terminal
WBP2NL → cognition arrow.

Best next computation: a **configuration-stability and conditional-independence analysis at L1565**. Specifically: (a) report the
FOCUS gene PIPs for WBP2NL, CYP2D6, NAGA and the two lncRNAs across all eight existing configurations as a single table with a
stated primary and a sensitivity band, rather than quoting one configuration; and (b) run conditional/joint colocalisation —
regress out the CYP2D6 star-allele haplotype (rs1135840, rs16947, rs1065852, rs3892097, rs5758550) and re-test whether the
WBP2NL cis-eQTL still colocalises with the Davies cognition signal in CommonMind, GTEx and ROSMAP separately. If WBP2NL survives
haplotype adjustment and CYP2D6 does not, the locus assignment should flip; if both collapse, L1565 becomes a
"haplotype-level, gene-unresolved" locus, which is an honest and reportable outcome.
