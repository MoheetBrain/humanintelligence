# Sprint 3.1 — Synaptic Signal Recon / Correction Pass

*2026-09-23 · branch `sprint-3.1/synaptic-recon` from Sprint-3 commit `04c70ef` · all computational · chemistry gate CLOSED.*

**Scope.** This pass audits the strongest Sprint-3 result: "synaptic biology survives unbiased testing, with a possible presynaptic skew". It checks that claim against direct presynaptic-versus-postsynaptic tests, alternative covariate conditioning, dependence in the ranking, the direction evidence and the extreme-tail arithmetic.

What it does NOT do:

- It is not a new discovery sprint.
- It does not re-run the gene tournament.
- It does not look at within-family or independent-cohort data. Those belong to Sprint 4, whose protocol was frozen before this pass began (`sprint-4/causal-synapse-bridge`, commit `db86aef`).

Every number below is read from a file in `reports/sprint3_1/` by `pipelines/sprint3_1/write_recon_report.py`.

## Final verdict

**1. Does broad synaptic enrichment survive?** **Yes, but it is about half the size Sprint 3 implied.**

- SynGO "synapse" (1,602 genes) is enriched under every conditioning specification: P = 1.0e-08 with MAGMA's internal covariates only, and 0.010 after conditioning on generic neuronal expression.
- Its effect falls by 55% along the way, from β 0.155 to 0.070.
- It survives conditioning on a neuron-specific background set (joint model P = 0.001), on brain-expressed genes (P = 4.1e-04) and on propagated "neuron projection" (P = 8.7e-04).

**2. Does presynaptic-specific enrichment survive?** **No, not as a compartment effect.**

- Whole SynGO presynapse is weaker than postsynapse in every specification. In spec D, marginally: pre β 0.085 (P = 0.016) vs post β 0.126 (P = 2.4e-04).
- Fitted jointly, pre falls to β +0.031 (P = 0.469) while post keeps β +0.114 (P = 0.004).
- Conditioned on generic synapse membership, presynapse adds nothing: β -0.033 (P = 0.527).
- What survives is membrane-level. The presynaptic-membrane, presynaptic-membrane-integral, synaptic-adhesion and presynaptic voltage-gated-channel sets all stay nominal:
  - after neuronal-expression conditioning (4 of these 4 at P < 1e-4);
  - after leaving out any single locus (worst-case P = 1.9e-04).
- But presynaptic-membrane-only genes do not differ from postsynaptic-membrane-only genes: contrast β +0.136, P = 0.405.

**3. Is postsynaptic biology genuinely weaker?** **No.** Every direct contrast is non-significant, and the point estimates favour postsynapse:

- pre-only minus post-only genes: β -0.056, P = 0.432;
- presynaptic minus postsynaptic process genes: β -0.001, P = 0.991;
- propagated GO compartments fitted jointly: post β +0.129 (P = 0.003) vs pre β +0.042 (P = 0.359).

Sprint 3's "presynaptic rather than postsynaptic" came from reading significant-versus-non-significant as a difference.

**4. Does conditioning on LOEUF materially change the biological interpretation?** **Yes, in breadth. Not in which biology survives.**

LOEUF is the main reason broad synaptic sets looked weaker than the membrane/adhesion sets in Sprint 3:

- Adding LOEUF (spec C) moves SynGO synapse from P = 1.0e-08 to 1.3e-04.
- Global-FDR survivors fall from 69 (spec A) to 13 (spec C).
- The membrane and adhesion sets barely move.

Constraint is plausibly biology: synaptic genes are LoF-intolerant. So conditioning on it removes true signal as well as confounding. Neither the constrained nor the unconstrained specification is "the" answer. Both are reported (matrix below).

**5. Are Top-50 ranks materially inflated by dependent evidence?** **Yes.**

- In the evidence layers these ranks rest on, direct association, replication, fine-mapping, the GWAS half of colocalisation, and direction all descend from one UK-Biobank-containing GWAS lineage. Module membership is derived from selection on it.
- Collapsing that lineage keeps 24 (best-rank rule) or 17 (mean-rank rule) of the natural Top-50.
- Leaving it out keeps 5 natural and 14 adult genes.
- An independent-only ranking keeps 0.
- Only 1 natural Top-50 gene (MACROD2) has a verified UK-Biobank-free cohort unit.
- Top-50 ranks are TRIAGE, not posterior truth.

**6. Does NEGR1 remain the best causal-audit locus?** **Yes, as an audit locus, but its direction evidence is much thinner than reported.**

- The Sprint-3 "3 of 4 strong brain colocalisations" collapse to 1 independent unit: one ROSMAP DLPFC eQTL dataset × one lead variant, echoed by four overlapping UK-Biobank-containing GWAS.
- The discordant row uses a multi-allelic indel lead (rs66495454, -/TCC/TCCT), which is harmonisation-fragile.
- The locus also carries a second, weakly linked signal: rs12128707, r² = 0.05 with the Davies lead in 1000G EUR.

NEGR1 is **not** near resolution. It stays the best *audit* locus because:

- its gene-level signal is strong and single-gene;
- it has a gene-level adult-brain eQTL;
- it is a Sprint-4 stress test.

A new result from the same audit: after correcting an eligibility defect (below), RPS26 at the ERBB3 locus (12q13.2) meets the unchanged direction threshold on independent adult cohorts. It is a Sprint-4 Gate-C priority, not a target.

**7. Which genes retain genuine independent support?** **Almost none, in the sense of independent cognition cohorts.**

- MACROD2 has a UK-Biobank-free cohort unit (AWI-Gen+HAALSI).
- SOWAHC and SEPTIN10 have perturbation support (2q12.3 duplication).
- Independent *molecular* support (strong colocalisation in a separate QTL cohort) exists for:
  - RPS26 (4 adult cohorts, direction-concordant);
  - NEGR1 (1 unit);
  - SYT1 (transcript-level only).
  But the GWAS half of each colocalisation is the same UK-Biobank lineage.
- Independent-cohort testing of the synaptic sets and of loci is Sprint 4 Gate B (Genes & Cognition) and Gate A (within-family).

**8. Which abstraction fits best?** **BROAD SYNAPTIC ORGANISATION, specifically synaptic membrane / trans-synaptic adhesion, on top of a substantial generic-neuronal component.** Not presynaptic release.

- Release machinery is not enriched:
  - union of active zone, vesicle cycle, docking/priming, Ca²⁺-triggered release and SNARE cycle: P = 0.104;
  - release-only vs organisation-only contrast: β -0.017, P = 0.823.
- Synapse formation/adhesion is the only machinery category nominal in spec D (P = 0.027).
- Trafficking is not supported:
  - vesicle cycle P = 0.223;
  - receptor trafficking P = 0.371.
- About 55% of the broad synapse effect is absorbed by generic neuronal expression (Model C's share).

So:

- **PRESYNAPTIC RELEASE: rejected as the primary system.**
- **BROAD SYNAPTIC ORGANISATION: best fit, narrowed to membrane/adhesion.**
- **TRAFFICKING: not supported.**
- **GENERIC NEURONAL BIOLOGY: a large share, not the whole.**

**9. What previous wording must be corrected?** See *Corrections* below. There are 13 items, each with a dated correction block in the affected file. The most important:

- "presynaptic rather than postsynaptic";
- "synaptic biology is the only pathway signal" (propagated GO makes neurodevelopmental sets robust too);
- "1.13x … continuous";
- "121/159 loci agree in sign" (that statistic was unsigned);
- "NEGR1 3/4, closest clean case";
- "adult-modifiable".

**10. What single result is solid enough to build the next causal-genetics sprint around?** Common-variant association with cognition is enriched in **synaptic-membrane / trans-synaptic adhesion genes**:

- presynaptic membrane;
- integral presynaptic membrane;
- synapse adhesion between pre- and post-synapse;
- voltage-gated channels regulating presynaptic potential.

This enrichment:

- survives every covariate specification here, including generic neuronal expression;
- survives leave-one-locus-out;
- is carried by adhesion loci (CDH9, PTPRF, CADM2, NCAM1, PTPRD, LRRC4) and a few channel loci (KCNJ3, SCN2A).

It is still a single-lineage (UK-Biobank-containing) finding. Sprint 4's frozen Gates A/B test exactly these sets. The allele-direction continuity of the extreme tail at the Sprint-3 loci is the second solid result:

- 112 of 136 testable loci are concordant, P = 4.3e-15;
- continuity expects 72%–84%.

## 1. Presynaptic versus postsynaptic, tested directly

Sprint 3 found presynaptic-membrane sets significant and the postsynaptic density not, and read that as "presynaptic rather than postsynaptic". Significant-versus-non-significant is not a comparison. The direct tests below use MAGMA joint and contrast models (two-sided).

A contrast is estimated by reparametrisation:

- the model {PRE_ONLY, PRE_AND_POST, PRE_OR_POST} gives PRE_ONLY a coefficient equal to (pre-only genes) minus (post-only genes);
- the same is done for membranes, processes, and release vs organisation.

Presynapse and postsynapse come from SynGO 1.3 (curated, propagated). Specs are defined in §2; spec D is Sprint 3's covariates on the full gene universe.

| test (two-sided unless marked) | A | C | D | E (neuronal-conditioned) |
|---|---|---|---|---|
| marginal presynapse (one-sided) | +0.125 (P=5.1e-04) | +0.078 (P=0.021) | +0.085 (P=0.016) | +0.034 (P=0.197) |
| marginal postsynapse (one-sided) | +0.178 (P=1.1e-07) | +0.116 (P=4.5e-04) | +0.126 (P=2.4e-04) | +0.081 (P=0.014) |
| joint: presynapse given postsynapse | +0.040 (P=0.349) | +0.024 (P=0.575) | +0.031 (P=0.469) | -0.003 (P=0.950) |
| joint: postsynapse given presynapse | +0.160 (P=3.8e-05) | +0.106 (P=0.007) | +0.114 (P=0.004) | +0.082 (P=0.041) |
| presynapse given generic synapse | -0.046 (P=0.383) | -0.036 (P=0.490) | -0.033 (P=0.527) | -0.047 (P=0.375) |
| postsynapse given generic synapse | +0.071 (P=0.195) | +0.043 (P=0.430) | +0.046 (P=0.400) | +0.040 (P=0.461) |
| **contrast** pre-only − post-only genes | -0.091 (P=0.205) | -0.056 (P=0.433) | -0.056 (P=0.432) | -0.066 (P=0.353) |
| marginal presynaptic membrane (one-sided) | +0.440 (P=1.8e-07) | +0.392 (P=2.9e-06) | +0.397 (P=2.3e-06) | +0.344 (P=3.9e-05) |
| marginal postsynaptic membrane (one-sided) | +0.373 (P=1.5e-05) | +0.319 (P=1.8e-04) | +0.324 (P=1.5e-04) | +0.267 (P=0.002) |
| **contrast** pre-membrane-only − post-membrane-only | +0.126 (P=0.439) | +0.136 (P=0.402) | +0.136 (P=0.405) | +0.140 (P=0.387) |
| **contrast** pre-process-only − post-process-only | -0.015 (P=0.874) | -0.001 (P=0.994) | -0.001 (P=0.991) | -0.017 (P=0.860) |
| GO CC (propagated) presynapse, joint | +0.054 (P=0.231) | +0.035 (P=0.435) | +0.042 (P=0.359) | +0.006 (P=0.900) |
| GO CC (propagated) postsynapse, joint | +0.168 (P=7.4e-05) | +0.123 (P=0.004) | +0.129 (P=0.003) | +0.091 (P=0.036) |
| synapse given neuron-specific top-20% set | +0.139 (P=6.6e-07) | +0.087 (P=0.002) | +0.097 (P=0.001) | +0.069 (P=0.022) |
| synapse given brain-expressed top-50% set | +0.130 (P=3.1e-06) | +0.093 (P=0.001) | +0.105 (P=4.1e-04) | +0.067 (P=0.028) |
| synapse given neuron projection (propagated) | +0.140 (P=2.2e-06) | +0.091 (P=0.002) | +0.103 (P=8.7e-04) | +0.064 (P=0.042) |

**Answers:**

- **Does presynaptic enrichment remain after conditioning on generic neuronal/synaptic expression?**
  - For the whole presynaptic compartment, **no**:
    - marginal P = 0.197 in spec E;
    - P = 0.527 conditional on synapse.
  - For the presynaptic-membrane sets, **yes** (P = 3.9e-05 in spec E), but the postsynaptic membrane also remains (P = 0.002), and the two do not differ.
- **Is the presynaptic β larger than the postsynaptic β?** No. At compartment level the point estimates are reversed and the contrast is null. At membrane level the presynaptic point estimate is higher but the contrast is null.

**Corrected statement:** BROAD SYNAPTIC ENRICHMENT, CONCENTRATED IN SYNAPTIC-MEMBRANE / TRANS-SYNAPTIC ADHESION GENES; NO DEMONSTRATED PRESYNAPTIC SKEW. The brief's fallback wording, "broad synaptic enrichment with possible presynaptic skew", is itself too generous: no specification shows a skew.

Membrane-level detail, where the "presynaptic" sets come from:

- Genes annotated to BOTH synaptic membranes carry the largest joint coefficient:
  - +0.302 beyond the union;
  - these genes are cadherins, NCAM1, CTNNA2 and CACNA1E (`set_drivers.csv`).
- The top single set in specs A–D is propagated GO "synaptic membrane".

## 2. Conditioning sensitivity

Specifications, all on the **same 18,418-gene universe**:

- **A:** MAGMA internal covariates (gene size, density, inverse MAC, and their logs).
- **B:** A + annotation density.
- **C:** A + LOEUF.
- **D:** A + both, i.e. Sprint 3's covariates.
- **E:** D + generic neuronal expression, from the Siletti 2022 adult whole-brain atlas: level plus neuron-vs-glia specificity.
- **E2:** E + GTEx adult-brain expression.

Two input corrections come first:

- **Gene-universe defect in Sprint 3.** Its covariate file omitted the 1,349 genes that carry no annotation, so MAGMA silently dropped them from every conditioned run. Conditioned and unconditioned results were therefore computed on different backgrounds (17,069 vs 18,418 genes). Here unannotated genes get annotation density 0, and missing LOEUF (n = 1017) is imputed to the median. The exact Sprint-3 run is reproduced to the last digit as `D_S3` (6/6 sets identical).
- **GO sets were not propagated in Sprint 3.** gene2go lists direct annotations only; SynGO sets are rolled up. Sprint 3 therefore compared complete synaptic sets against truncated non-synaptic ones:
  - neurogenesis: 79 genes direct vs 1010 propagated;
  - neuron projection: 285 vs 1239;
  - chromatin organisation: 203 vs 738.
  Here GO is propagated on is_a/part_of (true-path rule).

### Sensitivity matrix — pre-chosen anchor set per theme

Anchor P (one-sided competitive), with the number of theme-family sets at global FDR < 0.05 in brackets.

| theme | anchor (genes) | A | B | C | D | E | E2 | verdict |
|---|---|---|---|---|---|---|---|---|
| synapse | `GO_0045202` (1602) | 1.0e-08 [29] | 4.5e-07 [25] | 1.3e-04 [6] | 4.6e-05 [8] | 0.010 [2] | 0.027 [3] | ROBUST |
| presynapse | `GO_0098793` (810) | 5.1e-04 [5] | 0.004 [4] | 0.021 [3] | 0.016 [3] | 0.197 [1] | 0.313 [2] | SPECIFICATION_DEPENDENT |
| postsynapse | `GO_0098794` (1031) | 1.1e-07 [13] | 3.0e-06 [11] | 4.5e-04 [3] | 2.4e-04 [3] | 0.014 [0] | 0.028 [0] | ANCHOR_NOMINAL_IN_ALL_SPECS (family FDR varies) |
| postsynaptic_density | `GO_0014069` (343) | 3.9e-05 [0] | 2.1e-04 [0] | 0.003 [0] | 0.003 [0] | 0.032 [0] | 0.042 [0] | ANCHOR_NOMINAL_IN_ALL_SPECS (family FDR varies) |
| dendrite | `GO_0030425` (590) | 2.8e-06 [7] | 2.3e-05 [5] | 2.1e-04 [3] | 1.5e-04 [3] | 0.005 [0] | 0.008 [0] | ANCHOR_NOMINAL_IN_ALL_SPECS (family FDR varies) |
| neurogenesis | `GO_0022008` (1010) | 3.8e-05 [7] | 2.5e-04 [6] | 0.002 [1] | 0.002 [1] | 0.002 [1] | 0.003 [1] | ROBUST |
| axon_guidance | `GO_0007411` (169) | 0.003 [0] | 0.005 [0] | 0.015 [0] | 0.014 [0] | 0.021 [0] | 0.019 [0] | ANCHOR_NOMINAL_IN_ALL_SPECS (family FDR varies) |
| neuron_projection | `GO_0043005` (1239) | 4.0e-04 [0] | 0.003 [0] | 0.009 [0] | 0.007 [0] | 0.099 [0] | 0.126 [0] | SPECIFICATION_DEPENDENT |
| axon | `GO_0030424` (628) | 1.0e-03 [0] | 0.004 [0] | 0.015 [0] | 0.012 [0] | 0.117 [0] | 0.150 [0] | SPECIFICATION_DEPENDENT |
| chromatin | `GO_0006325` (738) | 0.001 [1] | 0.004 [0] | 0.085 [0] | 0.081 [0] | 0.054 [0] | 0.045 [0] | SPECIFICATION_DEPENDENT |
| translation | `GO_0006412` (359) | 0.192 [0] | 0.265 [0] | 0.286 [0] | 0.278 [0] | 0.485 [0] | 0.595 [0] | NOT_SUPPORTED_IN_ANY_SPEC (absence of enrichment in this GWAS, not proof of irrelevance) |
| mitochondria | `GO_0005739` (1646) | 0.711 [0] | 0.787 [0] | 0.397 [0] | 0.384 [0] | 0.717 [0] | 0.816 [0] | NOT_SUPPORTED_IN_ANY_SPEC (absence of enrichment in this GWAS, not proof of irrelevance) |
| oxidative_phosphorylation | `GO_0006119` (89) | 0.277 [0] | 0.297 [0] | 0.177 [0] | 0.175 [0] | 0.355 [0] | 0.480 [0] | NOT_SUPPORTED_IN_ANY_SPEC (absence of enrichment in this GWAS, not proof of irrelevance) |
| myelin | `GO_0042552` (84) | 0.092 [0] | 0.130 [0] | 0.193 [0] | 0.188 [0] | 0.127 [0] | 0.145 [0] | NOT_SUPPORTED_IN_ANY_SPEC (absence of enrichment in this GWAS, not proof of irrelevance) |

### The six frozen Sprint-3 sets under every specification

P, with global q in brackets.

| set | A | B | C | D | E | E2 | worst leave-one-locus-out P (spec D) |
|---|---|---|---|---|---|---|---|
| `GO_0042734` presynaptic membrane | 1.8e-07 (0.000) | 7.2e-07 (0.001) | 2.9e-06 (0.008) | 2.3e-06 (0.008) | 3.9e-05 (0.054) | 4.2e-05 (0.051) | 1.0e-05 |
| `GO_0099560` synaptic membrane adhesion | 2.1e-07 (0.000) | 3.9e-07 (0.001) | 2.8e-06 (0.008) | 2.7e-06 (0.008) | 2.0e-05 (0.039) | 1.7e-05 (0.034) | 1.9e-05 |
| `GO_0099056` integral component of presynaptic membra | 4.8e-07 (0.001) | 1.8e-06 (0.002) | 4.9e-06 (0.009) | 4.1e-06 (0.008) | 3.3e-05 (0.054) | 3.2e-05 (0.044) | 1.9e-05 |
| `GO_0099508` voltage-gated monoatomic ion channel act | 1.3e-06 (0.001) | 1.9e-06 (0.002) | 3.3e-06 (0.008) | 3.2e-06 (0.008) | 1.1e-05 (0.033) | 1.1e-05 (0.034) | 1.9e-04 |
| `GO_0045202` synapse | 1.0e-08 (0.000) | 4.5e-07 (0.001) | 1.3e-04 (0.062) | 4.6e-05 (0.034) | 0.010 (0.651) | 0.027 (0.766) | 7.5e-05 |
| `SYNGO_synprocess` process in the synapse | 1.0e-08 (0.000) | 4.3e-07 (0.001) | 8.4e-05 (0.058) | 2.9e-05 (0.026) | 0.006 (0.541) | 0.015 (0.663) | 4.9e-05 |

**Reading the matrix:**

- **Synapse (broad)** is enriched in every specification. The specification changes its size, not its existence.
- **Membrane/adhesion sets** are nearly invariant to LOEUF and to annotation density. They attenuate modestly with neuronal expression (q ≈ 0.03–0.05 in E).
- **Neurodevelopmental biology** is robust in every specification once GO is propagated. CNS neuron differentiation and neuron migration are among the top global hits, at q < 0.05 in all of A–E2. Sprint 3 missed this because its GO sets were truncated.
- **Postsynapse, PSD, dendrite, axon guidance** are nominal in every specification but do not always reach global FDR.
- **Chromatin** is specification-dependent.
- **Translation, mitochondria, OXPHOS, myelin** are not enriched in any specification. That is an absence of common-variant enrichment in this GWAS, not a proof of irrelevance.
- A theme is never declared dead because one specification removes it. Verdicts require all specifications.

- Spec A: 9,714 sets tested; 69 at global FDR < 0.05. Top: GO_0045202 synapse; SYNGO_synprocess process in the synapse; GO_0097060 synaptic membrane; GO_0098794 postsynapse; GO_0042734 presynaptic membrane.
- Spec B: 9,714 sets tested; 54 at global FDR < 0.05. Top: GO_0097060 synaptic membrane; GO_0099560 synaptic membrane adhesion; SYNGO_synprocess process in the synapse; GO_0045202 synapse; GO_0042734 presynaptic membrane.
- Spec C: 9,714 sets tested; 13 at global FDR < 0.05. Top: GO_0097060 synaptic membrane; GO_0099560 synaptic membrane adhesion; GO_0042734 presynaptic membrane; GO_0099508 voltage-gated monoatomic ion channel activity involved in regulation of presynaptic membrane potential; GO_0099056 integral component of presynaptic membrane (GO:0099056).
- Spec D: 9,714 sets tested; 15 at global FDR < 0.05. Top: GO_0097060 synaptic membrane; GO_0042734 presynaptic membrane; GO_0099560 synaptic membrane adhesion; GO_0099508 voltage-gated monoatomic ion channel activity involved in regulation of presynaptic membrane potential; GO_0099056 integral component of presynaptic membrane (GO:0099056).
- Spec E: 9,714 sets tested; 5 at global FDR < 0.05. Top: GO_0021953 central nervous system neuron differentiation; GO_0099508 voltage-gated monoatomic ion channel activity involved in regulation of presynaptic membrane potential; GO_0110156 mRNA methylguanosine-cap decapping; GO_0001764 neuron migration; GO_0099560 synaptic membrane adhesion.
- Spec E2: 9,714 sets tested; 7 at global FDR < 0.05. Top: GO_0021953 central nervous system neuron differentiation; GO_0099508 voltage-gated monoatomic ion channel activity involved in regulation of presynaptic membrane potential; GO_0110156 mRNA methylguanosine-cap decapping; GO_0001764 neuron migration; GO_0099560 synaptic membrane adhesion.

## 3. Dependence in the Top-50 ranking

Full table: `rank_dependency_audit.csv` (79 genes × per-dimension lineage). The ORIGINAL scheme reproduces both committed Top-50 lists exactly (50/50 genes, 0 position mismatches).

| scheme | natural Top-50 overlap | adult Top-50 overlap |
|---|---|---|
| LINEAGE_COLLAPSED_BEST | 24 | 32 |
| LINEAGE_COLLAPSED_MEAN | 17 | 29 |
| INDEPENDENT_ONLY | 0 | 0 |
| LEAVE_LINEAGE_OUT | 5 | 14 |
| SUPP_LINEAGE_PLUS_MODULE_COLLAPSED_BEST | 21 | 24 |
| SUPP_LINEAGE_PLUS_MODULE_COLLAPSED_MEAN | 21 | 20 |

What this shows:

- **Lineage.** Direct, replication, fine-mapping, the GWAS half of colocalisation, and direction all descend from UK-Biobank-containing cognition GWAS. Module membership is computed on genes selected by Davies significance.
- **Genuinely independent units in the Top-50.** Natural 11 genes / adult 9 genes have ≥1 unit. Most of those are a strong colocalisation in a separate QTL cohort, whose GWAS half is still the same lineage. Excluding QTL datasets leaves 3 / 3.
- **Pipeline defect.** Sprint 3's `n_strict_ukb_free_units` counted Perry 2025 (PMID 39891803) as UK-Biobank-free. Its cohort field reads "UKB " with a trailing space, so the exact-match test missed it. The count is overstated for 11 natural Top-50 genes.
- **Ties decide the tails.** In the natural list, 18 LD-block leads tie at rank 51 and 13 got in by sort order. The module dimension puts all 310 M01 genes at rank 1.

### The fourteen named genes

| gene | original rank (nat / adult) | dims sharing the UKB-GWAS lineage | independent units | verdict |
|---|---|---|---|---|
| NEGR1 | 2 / 2 | direct, replication, finemap, coloc, direction | 1 |  |
| DCC | 1 / — | direct, replication, finemap, coloc | 0 |  |
| EXOC4 | 3 / — | direct, replication, finemap, coloc | 0 |  |
| NT5DC2 | 4 / — | direct, replication, finemap, coloc | 0 |  |
| BSN | 11 / 10 | direct, replication, finemap | 0 |  |
| SYT1 | 14 / 6 | direct, replication, finemap, coloc, direction | 4 |  |
| NSF | 14 / 6 | direct, replication, finemap, coloc, direction | 1 |  |
| ERBB3 | 7 / 1 | direct, replication, finemap | 0 |  |
| GRIA4 | 82 / 11 | direct, replication | 0 |  |
| KCNJ3 | 46 / 14 | direct, replication, finemap | 0 |  |
| RIMS2 | 88 / 17 | direct, replication | 0 |  |
| CADM2 | 51 / 19 | direct, replication, finemap | 0 |  |
| PTPRT | 51 / 45 | direct, replication | 0 |  |
| MEF2C | 21 / 28 | direct, replication, finemap, coloc | 1 |  |

## 4. "Adult-modifiable" → ADULT-EXPRESSION-COMPATIBLE

Sprint 3's adult gate was expression-based:

- GTEx adult brain TPM ≥ 1;
- not prenatal-dominant in BrainSpan.

Adult expression is not modifiability. The Sprint-3 list `TOP50_ADULT_MODIFIABLE_GENES.csv` is **relabelled ADULT-EXPRESSION-COMPATIBLE**. The file name is kept for provenance, and a correction block is added to the final report.

The replacement hierarchy (`adult_evidence_hierarchy.csv`) records each tier separately, so no tier is inferred from a lower one:

| tier | meaning | genes reaching it (of those assessed) |
|---|---|---|
| ADULT_EXPRESSED | GTEx adult brain expression | 54 |
| ADULT_EXPRESSION_DYNAMIC | Sprint-3 class ADULT_DYNAMIC | 36 |
| ADULT_FUNCTIONAL_EVIDENCE | curated adult-age functional evidence (species stated) | 1 of 1 curated |
| ADULT_CAUSAL_EVIDENCE | human adult causal chain: direction-resolved adult-brain QTL AND independent-cohort support | 0 |
| ADULT_INTERVENTION_READY | never assigned by this project | 0 |

**DCC, the test case.** Expression timing and functional timing are separate dimensions.

- **Expression timing:** PRENATAL_DOMINANT (BrainSpan prenatal/adult log2 ratio 2.8; adult brain TPM 1.2).
- **Functional timing:** of 19 curated DCC/netrin-1 items, 8 carry ADULT_FUNCTIONAL_EVIDENCE: rodent in vivo or slice work; one item adds human post-mortem expression (PMID-verified, species per item in `literature_curation.json`). Some items delete netrin-1, the ligand, rather than DCC:
  - Horn 2013 (PMID 23291093; mouse in vivo and acute hippocampal slice; conditional forebrain neuro): DCC is enriched in dendritic spines; forebrain neuronal deletion abolishes LTP, spares LTD, shortens spines, impairs spatial and recognition memory via Src-NMDAR.
  - Glasgow 2018 (PMID 30282026; rodent acute hippocampal slice; mouse conditional netrin-1 deletion in): Depolarisation and NMDAR activity release dendritic netrin-1; neuronal netrin-1 is required for adult CA1 LTP and potentiates transmission by recruiting GluA1 AMPARs.
  - Wong 2019 (PMID 30770464; mouse in vivo; conditional netrin-1 deletion in hippocampal and neocor): Adult mice lacking neuronal netrin-1 show impaired spatial memory, no anxiety-like phenotype and reduced self-grooming.
  - Glasgow 2020 (PMID 32264905; mouse in vivo and acute slice; CA1-specific R4ag11-CaMKIIa-Cre and CA3): CA1 DCC loss impairs spatial memory, alters spine morphology and weakens spontaneous EPSCs but spares LTP; CA3 DCC loss impairs Schaffer-collateral LTP and object-place memory.
  - Glasgow 2024 (PMID 38377003; mouse in vivo and entorhinal cortical slice; conditional netrin-1 or D): Deleting netrin-1 or DCC impairs short-term spatial memory and cholinergic persistent firing; muscarinic activation recruits DCC to the plasma membrane.
  - Mahmud 2025 (PMID 41362369; adult male mouse in vivo; AAV-CaMKII-Cre knockout of floxed Dcc in pre): Chronic social defeat cuts apical, not basal, spine density in prefrontal pyramidal neurons; adult DCC knockout prevents both spine loss and depression-like behaviour.
  - Torres-Berrio 2016 (PMID 27773352; human adult post-mortem prefrontal cortex; adult mouse defeat-stress m): DCC is raised and miR-218 lowered in the prefrontal cortex of stress-susceptible mice and of people with major depression; Dcc upregulation in adult mice causes vulnerability.
  - Yetnikoff 2010 (PMID 20345916; adult mouse and adult rat in vivo (VTA, pharmacological DCC blockade a): Repeated amphetamine raises VTA DCC in adults; DCC activation in the VTA at pretreatment is required for behavioural sensitisation and spinophilin increases.
- **Separated reading.** Expression: Prenatal-dominant. DCC expression peaks in early prenatal development (stated in the cross-disorder GWAS, PMID 31835028) and is classically described as downregulated during maturation (PMID 15730872). It is nevertheless demonstrably present in the adult brain: in dendritic spines of adult pyramidal neurons (PMID 23291093), throughout the adult hippocampus (PMID 32264905) and in adult ventral midbrain dopamine neuron
  Function: Adult-functional in rodents, developmental in humans. In adult rodents DCC and netrin-1 are required for hippocampal LTP, spine morphology, AMPAR insertion, spatial and recognition memory, entorhinal persistent firing, VTA drug plasticity and stress-induced prefrontal spine remodelling (PMIDs 23291093, 30282026, 30770464, 32264905, 38377003, 20345916, 41362369). In humans, every established DCC phenotype is developme

So "prenatal-dominant expression" must not be read as "development-only function". DCC is ADULT_EXPRESSED (weakly) with ADULT_FUNCTIONAL_EVIDENCE from animal work. It has no adult human causal evidence, and its LoF phenotype (mirror movements, callosal agenesis) is developmental. LoF impairment is never inverted into enhancement.

## 5. NEGR1 direction audit (and SYT1)

The threshold is frozen and unchanged: ≥3 strong gene-level adult-brain eQTL/pQTL colocalisations and ≥80% polarity-adjusted agreement. What changes is the counting unit, from rows to (GWAS signal group × QTL cohort). Rows are not independent:

- every cognition GWAS here contains UK Biobank;
- GTEx tissues share donors.

| gene | Sprint-3 rows (agreement) | strict gene-level rows | independent units | concordant units | resolved on units? |
|---|---|---|---|---|---|
| NEGR1 | 4 (75%) | 4 | 1 | 1 | no |
| SYT1 | 15 (60%) | 0 | 0 | 0 | no |

**NEGR1.** The four rows are one QTL dataset (ROSMAP DLPFC, gene-level) × one lead variant (rs66495454), reported by four GWAS:

- Sniekers 2017;
- three UK-Biobank field-20016 fluid-intelligence analyses.

The one discordant row is Sniekers. Its lead is a **multi-allelic insertion** (-/TCC/TCCT) absent from 1000G EUR, so its allele coding across studies is fragile and the discordance is plausibly a harmonisation artefact. The unit's majority direction: cognition-increasing allele → higher NEGR1 expression.

Independent units: **1**; the frozen rule needs 3. NEGR1 is **not near resolution**. The locus also holds weakly linked leads:

- rs12128707 has r² = 0.045 with the Davies lead rs3101338 and 0.15 with the rs2815752/rs3101336 CNV-tagging pair.

So "one NEGR1 signal" is itself uncertain: 3 GWAS signal groups appear across all rows.

**NEGR1: what the literature adds (PMID-verified; `literature_curation.json`).**

- The obesity-associated upstream deletion acts via an 8-kb deletion that removes a repressor site; its direction evidence (higher NEGR1) comes from lymphoblastoid cells, not brain.
- A depression-risk allele is reported to raise NEGR1 in brain.
- Whether either haplotype is the cognition signal is UNVERIFIED.
- Functionally, both knockout and overexpression impair neuronal phenotypes. So even a resolved eQTL direction would not license "increase NEGR1": the dose-response may be non-monotonic.

**SYT1.** All 15 Sprint-3 rows are **transcript-level (ENST) eQTLs**, not gene-level. The Sprint-3 rule's text said "gene-level", but its regex excluded only exon traits. Under strict gene-level eligibility SYT1 has **0** qualifying colocalisations.

**Genome-wide recount** (`direction_rule_recount_all_genes.csv`) under strict gene-level eligibility and unit counting:

- Genes resolved under the Sprint-3 row count: 0.
- Genes resolved on units: 1 — **RPS26**:
  - 38 strict gene-level rows, 100% agreement;
  - 6 QTL cohorts;
  - adult cohorts: GTEx, BrainSeq, CommonMind, ROSMAP (Walker and Aygün are fetal; Jerber is iPSC-derived neurons, so they are excluded as non-adult);
  - cognition-increasing allele → higher RPS26 expression.

RPS26 failed in Sprint 3 only because transcript-level rows diluted its agreement (72 rows, 69%). Caveats that stop this being a target claim:

- the lead rs1131017 is palindromic (C/G);
- RPS26 is a ribosomal gene with one of the strongest ubiquitous eQTLs in the genome, a known colocalisation "hub";
- 12q13.2 is a dense pleiotropic locus (ERBB3, SUOX, RAB5B, CDK2, IKZF4 all Bonferroni at gene level); ERBB3, a Top-50 gene, has no strong colocalisation;
- the GWAS half is still the UK-Biobank lineage.

The eligibility definition was **frozen in the Sprint-4 protocol before this audit** ("gene-level only, exon/transcript/splice excluded"), so Sprint 4 Gate C tests RPS26 under a rule that was not tuned to it.

## 6. Synaptic system map and model comparison

Per-gene, per-category map: `synaptic_system_map.csv`. It keeps two evidence layers side by side:

- **Annotation:** membership of the pre-registered SynGO/propagated-GO machinery sets.
- **Literature:** PMID-verified, species and evidence type stated.

Genetic evidence (MAGMA P, fine-mapping driver, direction units) sits on every row.

| gene | Davies P | SynGO compartment | literature compartment | categories (annotation / literature) |
|---|---|---|---|---|
| NEGR1 | 1.5e-16 | postsynaptic | both | — / synapse formation adhesion, receptor trafficking, postsynaptic plasticity structure, activity dependent remodelling, non synaptic or other |
| EXOC4 | 4.8e-15 | both | both, but not synapse-specific | vesicle cycle trafficking, receptor trafficking / vesicle cycle trafficking, receptor trafficking, non synaptic or other |
| BSN | 7.7e-14 | presynaptic | presynaptic | active zone organisation, vesicle cycle trafficking / active zone organisation, vesicle docking priming, ca triggered release |
| SYT1 | 3.3e-07 | both | presynaptic | active zone organisation, vesicle cycle trafficking, ca triggered release, snare cycle / vesicle cycle trafficking, ca triggered release, non synaptic or other |
| NSF | 6.4e-09 | both | both | vesicle cycle trafficking, snare cycle / snare cycle, receptor trafficking, postsynaptic plasticity structure |
| DCC | 1.0e-22 | postsynaptic | both | — / synapse formation adhesion, receptor trafficking, postsynaptic plasticity structure, activity dependent remodelling, non synaptic or other |
| RIMS2 | 1.6e-05 | presynaptic | presynaptic | active zone organisation, vesicle cycle trafficking, vesicle docking priming, ca triggered release / active zone organisation, vesicle docking priming, ca triggered release, non synaptic or other |
| CADM2 | 1.0e-07 | postsynaptic | both | synapse formation adhesion / synapse formation adhesion, non synaptic or other |
| PTPRT | 1.9e-08 | postsynaptic | both | — / synapse formation adhesion, postsynaptic plasticity structure |
| GRIA4 | 1.3e-05 | both | postsynaptic | active zone organisation / receptor trafficking, postsynaptic plasticity structure, non synaptic or other |
| KCNJ3 | 6.0e-12 | presynaptic | postsynaptic and extrasynaptic | — / activity dependent remodelling, non synaptic or other |
| ERBB3 | 3.0e-08 | not in SynGO | non-neuronal | — / non synaptic or other |
| MEF2C | 1.2e-12 | not in SynGO | nuclear | postsynaptic plasticity structure / activity dependent remodelling, non synaptic or other |
| NT5DC2 | 1.1e-14 | not in SynGO | non-synaptic, cytoplasmic | — / non synaptic or other |
| RPS26 | 6.2e-08 | both | nan | — / — |

Curator's critical notes (from the PMID-verified literature layer):

- **NEGR1:** NEGR1 is an adhesion molecule, not a release-machinery protein. Its links to vesicle biology are interactome-level (PMID 40382479) and have not been shown to alter release itself. Direction of effect is bidirectional in the literature: both knockout (PMID 30651602) and overexpression (PMID 40382479)
- **EXOC4:** EXOC4 is the weakest synapse-specific gene in this set. The exocyst is a general polarised-trafficking machine, and the cleanest genetic test (Drosophila sec5, PMID 12575951) explicitly dissociates exocyst function from neurotransmitter release. Its neuronal specificity, where it exists, is postsyna
- **BSN:** Bassoon is a scaffold, not a fusion protein. Its phenotype is bandwidth and reliability of release, not release competence per se.
- **SYT1:** SYT1 is the most mechanistically specific presynaptic gene here: a calcium sensor with human loss-of-function phenotypes. Its disorder is severe neurodevelopmental, which matters when interpreting common-variant cognition signals at the same locus.
- **NSF:** NSF is genuinely dual-compartment, which makes locus-level inference ambiguous: a cognition association at NSF could act through presynaptic SNARE recycling or through postsynaptic AMPA receptor maintenance. NSF also lies on chromosome 17q21.31, next to the MAPT/KANSL1 inversion polymorphism (PMID 2
- **DCC:** DCC's synaptic role is real but secondary to its guidance role, and the guidance role is the one anchored in human genetics. See dcc_adult_function for the full timing analysis.
- **RIMS2:** Most mouse mechanism comes from combined alpha-RIM deletion or pan-RIM conditional knockouts, so RIM1 and RIM2 functions are partly redundant and not cleanly separable. The human phenotype for RIMS2 specifically is retinal and pancreatic as well as neurodevelopmental.
- **CADM2:** CADM2's human signal is broad and behavioural rather than cognition-specific, and the strongest synaptogenic mechanism in the family was demonstrated for SynCAM1. Do not treat CADM1 evidence as CADM2 evidence.
- **PTPRT:** The mechanism rests largely on one culture study; there is no in vivo conditional knockout evidence in this curation, and PTPRT is also a well-known tumour suppressor, so its phosphatase substrates are not synapse-exclusive.
- **GRIA4:** GRIA4 is the receptor itself, not machinery that moves or releases transmitter. If a synaptic-machinery hypothesis is meant to be about release or trafficking rather than receptor composition, GRIA4 should be scored in its own category and not counted as evidence for presynaptic mechanisms.
- **KCNJ3:** KCNJ3 is an inhibitory effector channel, not synaptic machinery. Much of the classical electrophysiology was done on GIRK2 (KCNJ6) knockouts; the cleanest KCNJ3-specific in vivo statement here is PMID 16339040. Categorising KCNJ3 under any vesicle or adhesion category would be an error; non_synaptic
- **ERBB3:** ERBB3 belongs in a myelination or glial axis, not a synaptic-machinery axis. Including it in a synaptic gene set would inflate an apparent synaptic signal.
- **MEF2C:** MEF2C is a nuclear transcription factor. It reaches synapses only through its target genes, so it should not be scored as synaptic machinery; it is an upstream regulator of synapse number.
- **NT5DC2:** NT5DC2 is not a synaptic protein by any direct evidence. It sits in a dopamine-synthesis regulatory role in a cell line, and the fly data explicitly report no change in synapse morphology. Its presence in a synaptic gene list should be treated as a locus-level artefact until direct neuronal evidence

**Model comparison** (spec D, and spec E for neuronal conditioning; one-sided marginal unless marked):

| machinery category | D | E |
|---|---|---|
| synapse formation adhesion (189) | +0.153 (P=0.027) | +0.115 (P=0.074) |
| active zone organisation (117) | +0.091 (P=0.188) | +0.013 (P=0.448) |
| vesicle cycle trafficking (282) | +0.048 (P=0.223) | -0.011 (P=0.570) |
| vesicle docking priming (18) | -0.633 (P=0.988) | -0.762 (P=0.997) |
| ca triggered release (79) | +0.076 (P=0.278) | -0.012 (P=0.538) |
| snare cycle (51) | +0.072 (P=0.306) | +0.023 (P=0.437) |
| receptor trafficking (178) | +0.025 (P=0.371) | -0.015 (P=0.575) |
| postsynaptic plasticity structure (279) | +0.056 (P=0.192) | +0.006 (P=0.462) |
| activity dependent remodelling (130) | +0.093 (P=0.161) | +0.030 (P=0.375) |
| generic neuronal projection (1239) | +0.079 (P=0.007) | +0.042 (P=0.099) |
| release-machinery union | +0.068 (P=0.104) | +0.010 (P=0.430) |
| organisation/trafficking union | +0.089 (P=0.026) | +0.045 (P=0.163) |
| **contrast** release-only − organisation-only (two-sided) | -0.017 (P=0.823) | -0.036 (P=0.645) |
| neuron-specific top-20% set | +0.092 (P=1.2e-06) | (conditioned away) |

**MODEL A — presynaptic release is the primary system.** **Rejected.**

Every release category is null:

- active zone;
- vesicle cycle;
- docking/priming;
- Ca²⁺-triggered release;
- SNARE.

The release-only vs organisation-only contrast is null, and pre vs post is null. Of the named genes:

- SYT1, RIMS2 and BSN are genuine release/active-zone genes, but they are 3 loci among 159;
- KCNJ3, which drives the "presynaptic voltage-gated channel" set, is a GIRK channel best known for somatodendritic inhibition.

**MODEL B — broad synaptic organisation + membrane/vesicle trafficking.** **Supported for organisation (membrane/adhesion); not for trafficking.**

- Synapse formation/adhesion is the only nominal machinery category.
- The adhesion and membrane sets survive every specification.
- Their drivers are adhesion molecules: CDH9, PTPRF, CADM2, NCAM1, PTPRD, LRRC4, cadherins.
- Vesicle and receptor trafficking are null.
- EXOC4 and NSF are trafficking genes, but general-purpose ones.

**MODEL C — generic neuronal biology / annotation structure.** **Partly true.**

- Neuronal expression absorbs about 55% of the broad synapse effect.
- The neuron-specific background set is itself strongly enriched.
- Unpropagated GO had tilted Sprint 3 toward SynGO.

But it is not the whole story:

- synapse remains nominal conditional on neuron-specific genes, brain-expressed genes and neuron projection;
- the adhesion/membrane core stays at P ≈ 1e-5.

**Chosen abstraction:** BROAD SYNAPTIC ORGANISATION (synaptic-membrane / trans-synaptic adhesion), on a large generic-neuronal base. This is not the most convenient model for a target programme: adhesion molecules are developmental and structural as much as adult-plastic.

## 7. Extreme tail: the 1.13x result

Full reassessment: `extreme_tail_reassessment.md`. In short:

- The observed/predicted ratio ranges from **0.61 to 1.25** under defensible assumptions about ascertainment and winner's curse, so it proves neither continuity nor amplification.
- The Sprint-3 "121/159 loci same sign" was an unsigned gene-level statistic, not a sign test.
- A genuine allele-direction test gives 112/136 (82%) concordant, P = 4.3e-15. That is within the 72%–84% expected under continuity.

**Corrected wording:** NO STRONG EVIDENCE FOR A DISTINCT COMMON-VARIANT ARCHITECTURE IN THE EXTREME TAIL. The same alleles point the same way. Magnitudes are not pinned down.

## Corrections to previous wording (dated 2026-09-23)

Each item is also written as a dated correction block into the affected file; the original text is kept.

| id | where | previous wording | corrected |
|---|---|---|---|
| C1 | GENE_TOURNAMENT_FINAL.md headline 3, §H.3, Q16; PROJECT_STATUS | "presynaptic rather than postsynaptic" | broad synaptic enrichment concentrated in synaptic-membrane/adhesion genes; no demonstrated presynaptic skew; postsynapse not weaker (§1) |
| C2 | GENE_TOURNAMENT_FINAL.md headline 3; truth-table synaptic row | "the only pathway signal that survives" | with propagated GO, CNS neuron differentiation and neuron migration also survive global FDR in every specification (§2) |
| C3 | run_pathway_enrichment.py (method) | conditioned runs silently used 17,069 genes | covariates must cover all 18,418 genes; Sprint-3 numbers reproduced and kept, full-universe results added (§2) |
| C4 | build_pathway_sets.py (method) | GO sets from direct gene2go annotations | GO sets must be propagated before comparing themes against SynGO (§2) |
| C5 | GENE_TOURNAMENT_FINAL.md headline 2, §D, §H.2, Q4; truth-table continuity row | "1.13x … proves continuity" | ratio spans 0.61–1.25 under plausible assumptions; replaced by the signed locus-direction test (§7) |
| C6 | GENE_TOURNAMENT_FINAL.md headline 2, §D, Q4 | "121/159 independent loci agree in sign" | that statistic was unsigned gene-level Z > 0; signed test: 112/136 concordant (§7) |
| C7 | GENE_TOURNAMENT_FINAL.md §F, Q8 | "NEGR1 (3 of 4, 75%) is the closest clean case" | 1 independent unit; not near resolution (§5) |
| C8 | build_consensus.py direction rule | "gene-level" eligibility admitted transcript-level eQTLs | strict gene-level eligibility; SYT1 has 0 qualifying colocs; RPS26 meets the unchanged threshold (§5) |
| C9 | TOP50_ADULT_MODIFIABLE_GENES.csv, GENE_TOURNAMENT_FINAL.md §B | "adult-modifiable" | ADULT-EXPRESSION-COMPATIBLE; five-tier hierarchy (§4) |
| C10 | build_master_universe.py (n_strict_ukb_free_units) | Perry 2025 counted as UKB-free | cohort string "UKB " (trailing space) missed; UKB-free units overstated for 11 natural Top-50 genes (§3) |
| C11 | TOP50 lists | consensus ranks as ordering | ranks are triage; one lineage counted several times; tails decided by ties (§3) |
| C12 | DCC developmental class | PRENATAL_DOMINANT read as development-only | expression timing and functional timing recorded separately (§4) |
| C13 | GENE_TOURNAMENT_FINAL.md §H.3 | "presynaptic voltage-gated channels" as presynaptic biology | that 17-gene set is driven by KCNJ3 (GIRK1, classically somatodendritic) and SCN2A; leave-KCNJ3-out P rises 59-fold, to 1.9e-04 (§1, §6) |

## Files, methods, verification

- **Inputs**, all from Sprint 3 and none new:
  - Davies 2018 `.genes.raw` (the verified X01 gene layer);
  - SynGO 1.3, gene2go and go-basic.obo (local snapshots from 2026-09-22);
  - Siletti 2022 superclusters (read-only from the Codex worktree);
  - GTEx v10 medians; Open Targets colocalisation compact file; Zabaneh 2018 and Savage 2018 gene-level results; Zabaneh allele-level summary statistics (GCST005626, sha256 `44ddca30…`).
- **Software:** MAGMA v1.10 (same binary as Sprint 3); Python 3.12 (pandas, numpy, scipy, bed-reader).
- **Code:** `pipelines/sprint3_1/`:
  - `build_inputs.py`, `run_recon_magma.py`, `analyse_recon.py`, `leave_one_locus_out.py`;
  - `qtl_independence_audit.py`, `extreme_tail_reassessment.py`, `build_system_map.py`;
  - `rank_dependency_audit.py` (subagent);
  - `write_recon_report.py`;
  - tests `test_sprint3_1.py`, `test_rank_dependency_audit.py`.
- **Literature:** `data/sprint3_1/literature_curation.json` (subagent; PMIDs verified by metadata lookup).
- **Limits:**
  - everything rests on UK-Biobank-containing European-ancestry GWAS;
  - the neuronal covariate is one atlas (bulk-pseudobulk superclusters);
  - theme regex families are coarse;
  - joint-model P-values are MAGMA's (normal-theory, gene-correlation-adjusted).

*Generated 2026-09-23T09:21Z by `pipelines/sprint3_1/write_recon_report.py`.*
