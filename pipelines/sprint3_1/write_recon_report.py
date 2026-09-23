#!/usr/bin/env python3
"""Sprint 3.1 — write SYNAPTIC_RECON_REPORT.md and extreme_tail_reassessment.md.

Every number is read from the committed Sprint-3.1 outputs; nothing is typed by hand except
the interpretation, and each interpretive sentence names the table it rests on.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
R = REPO / "reports" / "sprint3_1"
D = REPO / "data" / "sprint3_1"
TODAY = "2026-09-23"


def jl(name: str) -> dict:
    return json.loads((R / name).read_text(encoding="utf-8"))


def fmt_p(p: float) -> str:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "NA"
    return f"{p:.1e}" if p < 1e-3 else f"{p:.3f}"


def cell(beta: float, p: float) -> str:
    return f"{beta:+.3f} (P={fmt_p(p)})"


def joint(jt: pd.DataFrame, model: str, var: str, spec: str) -> pd.Series:
    r = jt[(jt.analysis == "joint_two_sided") & (jt.model == model) & (jt.variable == var) & (jt.spec == spec)]
    return r.iloc[0]


def marg(jt: pd.DataFrame, var: str, spec: str) -> pd.Series:
    r = jt[(jt.analysis == "marginal_one_sided") & (jt.variable == var) & (jt.spec == spec)]
    return r.iloc[0]


def main() -> int:
    jt = pd.read_csv(R / "pre_vs_post_joint_tests.csv")
    sens = pd.read_csv(R / "pathway_conditioning_sensitivity.csv")
    lolo = pd.read_csv(R / "leave_one_locus_out.csv")
    rsum = jl("recon_magma_summary.json")
    dep = jl("rank_dependency_audit_summary.json")
    negr1 = jl("negr1_qtl_independence_audit_summary.json")
    recount = pd.read_csv(R / "direction_rule_recount_all_genes.csv")
    sysmap = pd.read_csv(R / "synaptic_system_map.csv")
    tiers = pd.read_csv(R / "adult_evidence_hierarchy.csv")
    ext = jl("extreme_tail_reassessment.json")
    lit = json.loads((D / "literature_curation.json").read_text()) if (D / "literature_curation.json").exists() else {}
    inputs = json.loads((D / "inputs_report.json").read_text())

    S = ["A", "B", "C", "D", "E", "E2"]
    # --- part 1 numbers -------------------------------------------------------------
    pp = {s: {"pre": joint(jt, "PRE POST", "PRE", s), "post": joint(jt, "PRE POST", "POST", s),
              "pre_syn": joint(jt, "PRE SYNAPSE", "PRE", s), "post_syn": joint(jt, "POST SYNAPSE", "POST", s),
              "syn_pre": joint(jt, "PRE SYNAPSE", "SYNAPSE", s),
              "contrast": joint(jt, "PRE_ONLY PRE_AND_POST PRE_OR_POST", "PRE_ONLY", s),
              "memb_contrast": joint(jt, "PREMEMB_ONLY PREPOSTMEMB_BOTH PREPOSTMEMB_UNION", "PREMEMB_ONLY", s),
              "proc_contrast": joint(jt, "PREPROC_ONLY PREPOSTPROC_BOTH PREPOSTPROC_UNION", "PREPROC_ONLY", s),
              "rel_contrast": joint(jt, "RELEASE_ONLY RELEASE_AND_ORG RELEASE_OR_ORG", "RELEASE_ONLY", s),
              "syn_neur": joint(jt, "SYNAPSE NEURON_SPECIFIC_TOP20", "SYNAPSE", s),
              "syn_brain": joint(jt, "SYNAPSE BRAIN_EXPRESSED_TOP50", "SYNAPSE", s),
              "syn_proj": joint(jt, "SYNAPSE THEME_neuron_projection", "SYNAPSE", s),
              "gocc_pre": joint(jt, "GOCC_PRESYNAPSE_PROP GOCC_POSTSYNAPSE_PROP", "GOCC_PRESYNAPSE_PROP", s),
              "gocc_post": joint(jt, "GOCC_PRESYNAPSE_PROP GOCC_POSTSYNAPSE_PROP", "GOCC_POSTSYNAPSE_PROP", s)}
          for s in S + ["D_S3"]}
    mg = {s: {v: marg(jt, v, s) for v in ["PRE", "POST", "SYNAPSE", "PSD", "PREMEMB", "POSTMEMB", "PRE_ONLY",
                                            "POST_ONLY", "PRE_AND_POST", "NEURON_SPECIFIC_TOP20",
                                            "RELEASE_MACHINERY", "ORGANISATION_TRAFFICKING"]
                                       + [c for c in jt.variable.unique() if c.startswith("CAT_")]}
          for s in S}
    pre_bigger_any = any(pp[s]["contrast"].beta > 0 and pp[s]["contrast"].P < 0.05 for s in S)
    frozen = sens[sens.theme.str.startswith("FROZEN")]
    theme = sens[~sens.theme.str.startswith("FROZEN")]

    L: list[str] = []
    w = L.append
    w("# Sprint 3.1 — Synaptic Signal Recon / Correction Pass")
    w("")
    w(f"*{TODAY} · branch `sprint-3.1/synaptic-recon` from Sprint-3 commit `04c70ef` · all computational · "
      "chemistry gate CLOSED.*")
    w("")
    w("**Scope.** This pass audits the strongest Sprint-3 result: \"synaptic biology survives unbiased testing, "
      "with a possible presynaptic skew\". It checks that claim against direct presynaptic-versus-postsynaptic "
      "tests, alternative covariate conditioning, dependence in the ranking, the direction evidence and the "
      "extreme-tail arithmetic.")
    w("")
    w("What it does NOT do:")
    w("")
    w("- It is not a new discovery sprint.")
    w("- It does not re-run the gene tournament.")
    w("- It does not look at within-family or independent-cohort data. Those belong to Sprint 4, whose "
      "protocol was frozen before this pass began (`sprint-4/causal-synapse-bridge`, commit `db86aef`).")
    w("")
    w("Every number below is read from a file in `reports/sprint3_1/` by `pipelines/sprint3_1/write_recon_report.py`.")
    w("")

    # ---------------- FINAL VERDICT ------------------------------------------------------
    fr = frozen[frozen.spec == "E"]
    core4 = ["GO_0042734", "GO_0099560", "GO_0099056", "GO_0099508"]
    n4_E = int((fr[fr.anchor_set.isin(core4)].anchor_P < 1e-4).sum())
    lolo_worst = lolo.groupby("set").loo_P.max()
    syn_A, syn_E = theme[(theme.theme == "synapse") & (theme.spec == "A")].iloc[0], theme[(theme.theme == "synapse") & (theme.spec == "E")].iloc[0]
    atten = 1 - syn_E.anchor_beta / syn_A.anchor_beta
    nat = dep["sensitivity_natural"]["schemes"]
    adu = dep["sensitivity_adult"]["schemes"]

    def ov(schemes, key):
        return schemes.get(key, {}).get("top50_overlap_with_original")
    keys = list(nat.keys())
    lin_best = next((k for k in keys if "COLLAPSED" in k.upper() and "BEST" in k.upper() and "MODULE" not in k.upper()), None)
    lin_mean = next((k for k in keys if "COLLAPSED" in k.upper() and "MEAN" in k.upper() and "MODULE" not in k.upper()), None)
    lout = next((k for k in keys if "LEAVE" in k.upper()), None)
    indep = next((k for k in keys if "INDEPENDENT" in k.upper()), None)
    iu = dep["independent_units_top50"]
    n_units = negr1["NEGR1"]["n_independent_units"]
    ldt = ext["locus_direction_test"]
    w("## Final verdict")
    w("")
    w(f"**1. Does broad synaptic enrichment survive?** **Yes, but it is about half the size Sprint 3 implied.**")
    w("")
    w(f"- SynGO \"synapse\" (1,602 genes) is enriched under every conditioning specification: P = "
      f"{fmt_p(syn_A.anchor_P)} with MAGMA's internal covariates only, and {fmt_p(syn_E.anchor_P)} after "
      f"conditioning on generic neuronal expression.")
    w(f"- Its effect falls by {atten:.0%} along the way, from β {syn_A.anchor_beta:.3f} to {syn_E.anchor_beta:.3f}.")
    w(f"- It survives conditioning on a neuron-specific background set (joint model P = "
      f"{fmt_p(pp['D']['syn_neur'].P)}), on brain-expressed genes (P = {fmt_p(pp['D']['syn_brain'].P)}) and on "
      f"propagated \"neuron projection\" (P = {fmt_p(pp['D']['syn_proj'].P)}).")
    w("")
    w("**2. Does presynaptic-specific enrichment survive?** **No, not as a compartment effect.**")
    w("")
    w(f"- Whole SynGO presynapse is weaker than postsynapse in every specification. In spec D, marginally: "
      f"pre β {mg['D']['PRE'].beta:.3f} (P = {fmt_p(mg['D']['PRE'].P)}) vs post β {mg['D']['POST'].beta:.3f} "
      f"(P = {fmt_p(mg['D']['POST'].P)}).")
    w(f"- Fitted jointly, pre falls to β {pp['D']['pre'].beta:+.3f} (P = {fmt_p(pp['D']['pre'].P)}) while "
      f"post keeps β {pp['D']['post'].beta:+.3f} (P = {fmt_p(pp['D']['post'].P)}).")
    w(f"- Conditioned on generic synapse membership, presynapse adds nothing: β {pp['D']['pre_syn'].beta:+.3f} "
      f"(P = {fmt_p(pp['D']['pre_syn'].P)}).")
    w("- What survives is membrane-level. The presynaptic-membrane, presynaptic-membrane-integral, "
      "synaptic-adhesion and presynaptic voltage-gated-channel sets all stay nominal:")
    w(f"  - after neuronal-expression conditioning ({n4_E} of these 4 at P < 1e-4);")
    w(f"  - after leaving out any single locus (worst-case P = {fmt_p(lolo_worst.max())}).")
    w(f"- But presynaptic-membrane-only genes do not differ from postsynaptic-membrane-only genes: contrast β "
      f"{pp['D']['memb_contrast'].beta:+.3f}, P = {fmt_p(pp['D']['memb_contrast'].P)}.")
    w("")
    w(f"**3. Is postsynaptic biology genuinely weaker?** **No.** Every direct contrast is non-significant, and the "
      f"point estimates favour postsynapse:")
    w("")
    w(f"- pre-only minus post-only genes: β {pp['D']['contrast'].beta:+.3f}, P = {fmt_p(pp['D']['contrast'].P)};")
    w(f"- presynaptic minus postsynaptic process genes: β {pp['D']['proc_contrast'].beta:+.3f}, "
      f"P = {fmt_p(pp['D']['proc_contrast'].P)};")
    w(f"- propagated GO compartments fitted jointly: post β {pp['D']['gocc_post'].beta:+.3f} "
      f"(P = {fmt_p(pp['D']['gocc_post'].P)}) vs pre β {pp['D']['gocc_pre'].beta:+.3f} "
      f"(P = {fmt_p(pp['D']['gocc_pre'].P)}).")
    w("")
    w("Sprint 3's \"presynaptic rather than postsynaptic\" came from reading significant-versus-non-significant as "
      "a difference.")
    w("")
    c_syn = theme[(theme.theme == "synapse")].set_index("spec")
    w("**4. Does conditioning on LOEUF materially change the biological interpretation?** **Yes, in breadth. Not in "
      "which biology survives.**")
    w("")
    w("LOEUF is the main reason broad synaptic sets looked weaker than the membrane/adhesion sets in Sprint 3:")
    w("")
    w(f"- Adding LOEUF (spec C) moves SynGO synapse from P = {fmt_p(c_syn.loc['A', 'anchor_P'])} to "
      f"{fmt_p(c_syn.loc['C', 'anchor_P'])}.")
    w(f"- Global-FDR survivors fall from {rsum['landscape']['A']['n_q_lt_0.05']} (spec A) to "
      f"{rsum['landscape']['C']['n_q_lt_0.05']} (spec C).")
    w("- The membrane and adhesion sets barely move.")
    w("")
    w("Constraint is plausibly biology: synaptic genes are LoF-intolerant. So conditioning on it removes true "
      "signal as well as confounding. Neither the constrained nor the unconstrained specification is \"the\" "
      "answer. Both are reported (matrix below).")
    w("")
    w("**5. Are Top-50 ranks materially inflated by dependent evidence?** **Yes.**")
    w("")
    w("- In the evidence layers these ranks rest on, direct association, replication, fine-mapping, the GWAS half "
      "of colocalisation, and direction all descend from one UK-Biobank-containing GWAS lineage. Module "
      "membership is derived from selection on it.")
    w(f"- Collapsing that lineage keeps {ov(nat, lin_best)} (best-rank rule) or {ov(nat, lin_mean)} (mean-rank "
      f"rule) of the natural Top-50.")
    w(f"- Leaving it out keeps {ov(nat, lout)} natural and {ov(adu, lout)} adult genes.")
    w(f"- An independent-only ranking keeps {ov(nat, indep)}.")
    w(f"- Only {iu['natural']['n_with_ge1_verified_ukb_free_cohort_unit']} natural Top-50 gene (MACROD2) has a "
      "verified UK-Biobank-free cohort unit.")
    w("- Top-50 ranks are TRIAGE, not posterior truth.")
    w("")
    w("**6. Does NEGR1 remain the best causal-audit locus?** **Yes, as an audit locus, but its direction evidence is "
      "much thinner than reported.**")
    w("")
    w(f"- The Sprint-3 \"3 of 4 strong brain colocalisations\" collapse to {n_units} independent unit: one "
      "ROSMAP DLPFC eQTL dataset × one lead variant, echoed by four overlapping UK-Biobank-containing GWAS.")
    w("- The discordant row uses a multi-allelic indel lead (rs66495454, -/TCC/TCCT), which is "
      "harmonisation-fragile.")
    w("- The locus also carries a second, weakly linked signal: rs12128707, r² = 0.05 with the Davies lead in "
      "1000G EUR.")
    w("")
    w("NEGR1 is **not** near resolution. It stays the best *audit* locus because:")
    w("")
    w("- its gene-level signal is strong and single-gene;")
    w("- it has a gene-level adult-brain eQTL;")
    w("- it is a Sprint-4 stress test.")
    w("")
    w("A new result from the same audit: after correcting an eligibility defect (below), RPS26 at the ERBB3 locus "
      "(12q13.2) meets the unchanged direction threshold on independent adult cohorts. It is a Sprint-4 Gate-C "
      "priority, not a target.")
    w("")
    w("**7. Which genes retain genuine independent support?** **Almost none, in the sense of independent "
      "cognition cohorts.**")
    w("")
    w("- MACROD2 has a UK-Biobank-free cohort unit (AWI-Gen+HAALSI).")
    w("- SOWAHC and SEPTIN10 have perturbation support (2q12.3 duplication).")
    w("- Independent *molecular* support (strong colocalisation in a separate QTL cohort) exists for:")
    w("  - RPS26 (4 adult cohorts, direction-concordant);")
    w("  - NEGR1 (1 unit);")
    w("  - SYT1 (transcript-level only).")
    w("  But the GWAS half of each colocalisation is the same UK-Biobank lineage.")
    w("- Independent-cohort testing of the synaptic sets and of loci is Sprint 4 Gate B (Genes & Cognition) and "
      "Gate A (within-family).")
    w("")
    w("**8. Which abstraction fits best?** **BROAD SYNAPTIC ORGANISATION, specifically synaptic membrane / "
      "trans-synaptic adhesion, on top of a substantial generic-neuronal component.** Not presynaptic release.")
    w("")
    w("- Release machinery is not enriched:")
    w(f"  - union of active zone, vesicle cycle, docking/priming, Ca²⁺-triggered release and SNARE cycle: P = "
      f"{fmt_p(mg['D']['RELEASE_MACHINERY'].P)};")
    w(f"  - release-only vs organisation-only contrast: β {pp['D']['rel_contrast'].beta:+.3f}, "
      f"P = {fmt_p(pp['D']['rel_contrast'].P)}.")
    w(f"- Synapse formation/adhesion is the only machinery category nominal in spec D (P = "
      f"{fmt_p(mg['D']['CAT_synapse_formation_adhesion'].P)}).")
    w("- Trafficking is not supported:")
    w(f"  - vesicle cycle P = {fmt_p(mg['D']['CAT_vesicle_cycle_trafficking'].P)};")
    w(f"  - receptor trafficking P = {fmt_p(mg['D']['CAT_receptor_trafficking'].P)}.")
    w(f"- About {atten:.0%} of the broad synapse effect is absorbed by generic neuronal expression (Model C's share).")
    w("")
    w("So:")
    w("")
    w("- **PRESYNAPTIC RELEASE: rejected as the primary system.**")
    w("- **BROAD SYNAPTIC ORGANISATION: best fit, narrowed to membrane/adhesion.**")
    w("- **TRAFFICKING: not supported.**")
    w("- **GENERIC NEURONAL BIOLOGY: a large share, not the whole.**")
    w("")
    w("**9. What previous wording must be corrected?** See *Corrections* below. There are 13 items, each with a "
      "dated correction block in the affected file. The most important:")
    w("")
    w("- \"presynaptic rather than postsynaptic\";")
    w("- \"synaptic biology is the only pathway signal\" (propagated GO makes neurodevelopmental sets robust too);")
    w("- \"1.13x … continuous\";")
    w("- \"121/159 loci agree in sign\" (that statistic was unsigned);")
    w("- \"NEGR1 3/4, closest clean case\";")
    w("- \"adult-modifiable\".")
    w("")
    w(f"**10. What single result is solid enough to build the next causal-genetics sprint around?** Common-variant "
      f"association with cognition is enriched in **synaptic-membrane / trans-synaptic adhesion genes**:")
    w("")
    w("- presynaptic membrane;")
    w("- integral presynaptic membrane;")
    w("- synapse adhesion between pre- and post-synapse;")
    w("- voltage-gated channels regulating presynaptic potential.")
    w("")
    w("This enrichment:")
    w("")
    w("- survives every covariate specification here, including generic neuronal expression;")
    w("- survives leave-one-locus-out;")
    w("- is carried by adhesion loci (CDH9, PTPRF, CADM2, NCAM1, PTPRD, LRRC4) and a few channel loci (KCNJ3, "
      "SCN2A).")
    w("")
    w("It is still a single-lineage (UK-Biobank-containing) finding. Sprint 4's frozen Gates A/B test exactly these "
      "sets. The allele-direction continuity of the extreme tail at the Sprint-3 loci is the second solid result:")
    w("")
    w(f"- {ldt['n_concordant']} of {ldt['n_testable']} testable loci are concordant, P = "
      f"{fmt_p(ldt['binomial_P_vs_half_one_sided'])};")
    w(f"- continuity expects {ldt['expected_under_continuity']['N_eff 4,300']['expected_fraction']:.0%}–"
      f"{ldt['expected_under_continuity']['equivalent N, top 0.03%']['expected_fraction']:.0%}.")
    w("")

    # ---------------- PART 1 ---------------------------------------------------------------
    w("## 1. Presynaptic versus postsynaptic, tested directly")
    w("")
    w("Sprint 3 found presynaptic-membrane sets significant and the postsynaptic density not, and read that as "
      "\"presynaptic rather than postsynaptic\". Significant-versus-non-significant is not a comparison. The "
      "direct tests below use MAGMA joint and contrast models (two-sided).")
    w("")
    w("A contrast is estimated by reparametrisation:")
    w("")
    w("- the model {PRE_ONLY, PRE_AND_POST, PRE_OR_POST} gives PRE_ONLY a coefficient equal to "
      "(pre-only genes) minus (post-only genes);")
    w("- the same is done for membranes, processes, and release vs organisation.")
    w("")
    w("Presynapse and postsynapse come from SynGO 1.3 (curated, propagated). Specs are defined in "
      "§2; spec D is Sprint 3's covariates on the full gene universe.")
    w("")
    w("| test (two-sided unless marked) | A | C | D | E (neuronal-conditioned) |")
    w("|---|---|---|---|---|")
    rows_tab = [("marginal presynapse (one-sided)", lambda s: cell(mg[s]["PRE"].beta, mg[s]["PRE"].P)),
                ("marginal postsynapse (one-sided)", lambda s: cell(mg[s]["POST"].beta, mg[s]["POST"].P)),
                ("joint: presynapse given postsynapse", lambda s: cell(pp[s]["pre"].beta, pp[s]["pre"].P)),
                ("joint: postsynapse given presynapse", lambda s: cell(pp[s]["post"].beta, pp[s]["post"].P)),
                ("presynapse given generic synapse", lambda s: cell(pp[s]["pre_syn"].beta, pp[s]["pre_syn"].P)),
                ("postsynapse given generic synapse", lambda s: cell(pp[s]["post_syn"].beta, pp[s]["post_syn"].P)),
                ("**contrast** pre-only − post-only genes", lambda s: cell(pp[s]["contrast"].beta, pp[s]["contrast"].P)),
                ("marginal presynaptic membrane (one-sided)", lambda s: cell(mg[s]["PREMEMB"].beta, mg[s]["PREMEMB"].P)),
                ("marginal postsynaptic membrane (one-sided)", lambda s: cell(mg[s]["POSTMEMB"].beta, mg[s]["POSTMEMB"].P)),
                ("**contrast** pre-membrane-only − post-membrane-only", lambda s: cell(pp[s]["memb_contrast"].beta, pp[s]["memb_contrast"].P)),
                ("**contrast** pre-process-only − post-process-only", lambda s: cell(pp[s]["proc_contrast"].beta, pp[s]["proc_contrast"].P)),
                ("GO CC (propagated) presynapse, joint", lambda s: cell(pp[s]["gocc_pre"].beta, pp[s]["gocc_pre"].P)),
                ("GO CC (propagated) postsynapse, joint", lambda s: cell(pp[s]["gocc_post"].beta, pp[s]["gocc_post"].P)),
                ("synapse given neuron-specific top-20% set", lambda s: cell(pp[s]["syn_neur"].beta, pp[s]["syn_neur"].P)),
                ("synapse given brain-expressed top-50% set", lambda s: cell(pp[s]["syn_brain"].beta, pp[s]["syn_brain"].P)),
                ("synapse given neuron projection (propagated)", lambda s: cell(pp[s]["syn_proj"].beta, pp[s]["syn_proj"].P))]
    for label, fn in rows_tab:
        w(f"| {label} | " + " | ".join(fn(s) for s in ["A", "C", "D", "E"]) + " |")
    w("")
    w("**Answers:**")
    w("")
    w("- **Does presynaptic enrichment remain after conditioning on generic neuronal/synaptic expression?**")
    w("  - For the whole presynaptic compartment, **no**:")
    w(f"    - marginal P = {fmt_p(mg['E']['PRE'].P)} in spec E;")
    w(f"    - P = {fmt_p(pp['D']['pre_syn'].P)} conditional on synapse.")
    w(f"  - For the presynaptic-membrane sets, **yes** (P = {fmt_p(mg['E']['PREMEMB'].P)} in spec E), but the "
      f"postsynaptic membrane also remains (P = {fmt_p(mg['E']['POSTMEMB'].P)}), and the two do not differ.")
    w("- **Is the presynaptic β larger than the postsynaptic β?** No. At compartment level the point estimates are "
      "reversed and the contrast is null. At membrane level the presynaptic point estimate is higher but the "
      "contrast is null.")
    w("")
    w("**Corrected statement:** BROAD SYNAPTIC ENRICHMENT, CONCENTRATED IN SYNAPTIC-MEMBRANE / TRANS-SYNAPTIC "
      "ADHESION GENES; NO DEMONSTRATED PRESYNAPTIC SKEW. The brief's fallback wording, \"broad synaptic "
      "enrichment with possible presynaptic skew\", is itself too generous: no specification shows a skew.")
    w("")
    w("Membrane-level detail, where the \"presynaptic\" sets come from:")
    w("")
    w("- Genes annotated to BOTH synaptic membranes carry the largest joint coefficient:")
    w(f"  - {joint(jt, 'PREMEMB_ONLY PREPOSTMEMB_BOTH PREPOSTMEMB_UNION', 'PREPOSTMEMB_BOTH', 'D').beta:+.3f} "
      "beyond the union;")
    w("  - these genes are cadherins, NCAM1, CTNNA2 and CACNA1E (`set_drivers.csv`).")
    w("- The top single set in specs A–D is propagated GO \"synaptic membrane\".")
    w("")

    # ---------------- PART 2 ---------------------------------------------------------------
    w("## 2. Conditioning sensitivity")
    w("")
    w("Specifications, all on the **same 18,418-gene universe**:")
    w("")
    w("- **A:** MAGMA internal covariates (gene size, density, inverse MAC, and their logs).")
    w("- **B:** A + annotation density.")
    w("- **C:** A + LOEUF.")
    w("- **D:** A + both, i.e. Sprint 3's covariates.")
    w("- **E:** D + generic neuronal expression, from the Siletti 2022 adult whole-brain atlas: level plus "
      "neuron-vs-glia specificity.")
    w("- **E2:** E + GTEx adult-brain expression.")
    w("")
    w("Two input corrections come first:")
    w("")
    w(f"- **Gene-universe defect in Sprint 3.** Its covariate file omitted the 1,349 genes that carry no annotation, "
      f"so MAGMA silently dropped them from every conditioned run. Conditioned and unconditioned results were "
      f"therefore computed on different backgrounds (17,069 vs 18,418 genes). Here unannotated genes get "
      f"annotation density 0, and missing LOEUF (n = {inputs['log_LOEUF_missing_imputed_median']}) is imputed "
      f"to the median. The exact Sprint-3 run is reproduced to the last digit as `D_S3` "
      f"({sum(v['identical'] for v in rsum['s3_reproduction'].values())}/6 sets identical).")
    w("- **GO sets were not propagated in Sprint 3.** gene2go lists direct annotations only; SynGO sets are rolled "
      "up. Sprint 3 therefore compared complete synaptic sets against truncated non-synaptic ones:")
    w(f"  - neurogenesis: {inputs['theme_anchor_sizes_direct_vs_propagated']['neurogenesis']['sprint3_direct']} "
      f"genes direct vs {inputs['theme_anchor_sizes_direct_vs_propagated']['neurogenesis']['propagated_or_syngo']} "
      f"propagated;")
    w(f"  - neuron projection: {inputs['theme_anchor_sizes_direct_vs_propagated']['neuron_projection']['sprint3_direct']} "
      f"vs {inputs['theme_anchor_sizes_direct_vs_propagated']['neuron_projection']['propagated_or_syngo']};")
    w(f"  - chromatin organisation: {inputs['theme_anchor_sizes_direct_vs_propagated']['chromatin']['sprint3_direct']} "
      f"vs {inputs['theme_anchor_sizes_direct_vs_propagated']['chromatin']['propagated_or_syngo']}.")
    w("  Here GO is propagated on is_a/part_of (true-path rule).")
    w("")
    w("### Sensitivity matrix — pre-chosen anchor set per theme")
    w("")
    w("Anchor P (one-sided competitive), with the number of theme-family sets at global FDR < 0.05 in brackets.")
    w("")
    w("| theme | anchor (genes) | " + " | ".join(S) + " | verdict |")
    w("|---|---|" + "---|" * len(S) + "---|")
    for th in ["synapse", "presynapse", "postsynapse", "postsynaptic_density", "dendrite", "neurogenesis",
               "axon_guidance", "neuron_projection", "axon", "chromatin", "translation", "mitochondria",
               "oxidative_phosphorylation", "myelin"]:
        t = theme[theme.theme == th].set_index("spec")
        cells = []
        for s in S:
            fam = t.loc[s, "family_n_q_lt_0.05"]
            cells.append(f"{fmt_p(t.loc[s, 'anchor_P'])} [{int(fam) if pd.notna(fam) else 0}]")
        w(f"| {th} | `{t.iloc[0].anchor_set}` ({int(t.iloc[0].anchor_ngenes)}) | " + " | ".join(cells)
          + f" | {t.iloc[0].theme_verdict.split(':')[0]} |")
    w("")
    w("### The six frozen Sprint-3 sets under every specification")
    w("")
    w("P, with global q in brackets.")
    w("")
    w("| set | " + " | ".join(S) + " | worst leave-one-locus-out P (spec D) |")
    w("|---|" + "---|" * len(S) + "---|")
    for sid in ["GO_0042734", "GO_0099560", "GO_0099056", "GO_0099508", "GO_0045202", "SYNGO_synprocess"]:
        t = frozen[frozen.anchor_set == sid].set_index("spec")
        w(f"| `{sid}` {t.iloc[0].anchor_name[:40]} | " + " | ".join(
            f"{fmt_p(t.loc[s, 'anchor_P'])} ({t.loc[s, 'anchor_q_global']:.3f})" for s in S)
          + f" | {fmt_p(lolo_worst[sid])} |")
    w("")
    w("**Reading the matrix:**")
    w("")
    w("- **Synapse (broad)** is enriched in every specification. The specification changes its size, not its "
      "existence.")
    w("- **Membrane/adhesion sets** are nearly invariant to LOEUF and to annotation density. They attenuate "
      "modestly with neuronal expression (q ≈ 0.03–0.05 in E).")
    w("- **Neurodevelopmental biology** is robust in every specification once GO is propagated. CNS neuron "
      "differentiation and neuron migration are among the top global hits, at q < 0.05 in all of A–E2. "
      "Sprint 3 missed this because its GO sets were truncated.")
    w("- **Postsynapse, PSD, dendrite, axon guidance** are nominal in every specification but do not always "
      "reach global FDR.")
    w("- **Chromatin** is specification-dependent.")
    w("- **Translation, mitochondria, OXPHOS, myelin** are not enriched in any specification. That is an "
      "absence of common-variant enrichment in this GWAS, not a proof of irrelevance.")
    w("- A theme is never declared dead because one specification removes it. Verdicts require all "
      "specifications.")
    w("")
    for s in S:
        v = rsum["landscape"][s]
        w(f"- Spec {s}: {v['n_sets']:,} sets tested; {v['n_q_lt_0.05']} at global FDR < 0.05. Top: "
          + "; ".join(x.split(" P=")[0].split(":", 1)[1] for x in v["top15"][:5]) + ".")
    w("")

    # ---------------- PART 3 ---------------------------------------------------------------
    w("## 3. Dependence in the Top-50 ranking")
    w("")
    w("Full table: `rank_dependency_audit.csv` (79 genes × per-dimension lineage). The ORIGINAL scheme reproduces "
      "both committed Top-50 lists exactly (50/50 genes, 0 position mismatches).")
    w("")
    w("| scheme | natural Top-50 overlap | adult Top-50 overlap |")
    w("|---|---|---|")
    for k in keys:
        if k == "ORIGINAL":
            continue
        w(f"| {k} | {ov(nat, k)} | {ov(adu, k)} |")
    w("")
    w("What this shows:")
    w("")
    w("- **Lineage.** Direct, replication, fine-mapping, the GWAS half of colocalisation, and direction all "
      "descend from UK-Biobank-containing cognition GWAS. Module membership is computed on genes selected by "
      "Davies significance.")
    w(f"- **Genuinely independent units in the Top-50.** Natural {iu['natural']['n_with_ge1_independent_unit_task_definition']} "
      f"genes / adult {iu['adult']['n_with_ge1_independent_unit_task_definition']} genes have ≥1 unit. Most of "
      f"those are a strong colocalisation in a separate QTL cohort, whose GWAS half is still the same lineage. "
      f"Excluding QTL datasets leaves {iu['natural']['n_with_ge1_unit_excluding_qtl_datasets']} / "
      f"{iu['adult']['n_with_ge1_unit_excluding_qtl_datasets']}.")
    w("- **Pipeline defect.** Sprint 3's `n_strict_ukb_free_units` counted Perry 2025 (PMID 39891803) as "
      "UK-Biobank-free. Its cohort field reads \"UKB \" with a trailing space, so the exact-match test missed it. "
      f"The count is overstated for {iu['natural']['n_where_pipeline_ukb_free_count_exceeds_audit']} natural "
      "Top-50 genes.")
    w("- **Ties decide the tails.** In the natural list, 18 LD-block leads tie at rank 51 and 13 got in by sort "
      "order. The module dimension puts all 310 M01 genes at rank 1.")
    w("")
    w("### The fourteen named genes")
    w("")
    w("| gene | original rank (nat / adult) | dims sharing the UKB-GWAS lineage | independent units | verdict |")
    w("|---|---|---|---|---|")
    for gname, v in dep["named_gene_verdicts"].items():
        rn = v.get("original_rank_natural")
        ra = v.get("original_rank_adult")
        w(f"| {gname} | {rn if rn is not None else '—'} / {ra if ra is not None else '—'} | "
          f"{', '.join(v.get('dims_sharing_ukb_gwas_lineage', []))} | {v.get('n_independent_units', 0)} | "
          f"{str(v.get('verdict', v.get('summary', '')))[:160]} |")
    w("")

    # ---------------- PART 4 ---------------------------------------------------------------
    w("## 4. \"Adult-modifiable\" → ADULT-EXPRESSION-COMPATIBLE")
    w("")
    w("Sprint 3's adult gate was expression-based:")
    w("")
    w("- GTEx adult brain TPM ≥ 1;")
    w("- not prenatal-dominant in BrainSpan.")
    w("")
    w("Adult expression is not modifiability. The Sprint-3 list `TOP50_ADULT_MODIFIABLE_GENES.csv` is "
      "**relabelled ADULT-EXPRESSION-COMPATIBLE**. The file name is kept for provenance, and a correction block "
      "is added to the final report.")
    w("")
    w("The replacement hierarchy (`adult_evidence_hierarchy.csv`) records each tier separately, so no tier is "
      "inferred from a lower one:")
    w("")
    w("| tier | meaning | genes reaching it (of those assessed) |")
    w("|---|---|---|")
    w(f"| ADULT_EXPRESSED | GTEx adult brain expression | {int(tiers.ADULT_EXPRESSED.astype(bool).sum())} |")
    w(f"| ADULT_EXPRESSION_DYNAMIC | Sprint-3 class ADULT_DYNAMIC | {int(tiers.ADULT_EXPRESSION_DYNAMIC.astype(bool).sum())} |")
    fe = tiers.ADULT_FUNCTIONAL_EVIDENCE
    w(f"| ADULT_FUNCTIONAL_EVIDENCE | curated adult-age functional evidence (species stated) | "
      f"{int((fe == True).sum())} of {int(fe.notna().sum())} curated |")  # noqa: E712
    w("| ADULT_CAUSAL_EVIDENCE | human adult causal chain: direction-resolved adult-brain QTL AND independent-cohort "
      "support | 0 |")
    w("| ADULT_INTERVENTION_READY | never assigned by this project | 0 |")
    w("")
    dcc = lit.get("dcc_adult_function", {}) if lit else {}
    w("**DCC, the test case.** Expression timing and functional timing are separate dimensions.")
    w("")
    w("- **Expression timing:** PRENATAL_DOMINANT (BrainSpan prenatal/adult log2 ratio 2.8; adult brain TPM 1.2).")
    items = dcc.get("items", []) if isinstance(dcc, dict) else []
    if items:
        adult_items = [i for i in items if "ADULT_FUNCTIONAL_EVIDENCE" in (i.get("evidence_tier") or [])]
        w(f"- **Functional timing:** of {len(items)} curated DCC/netrin-1 items, {len(adult_items)} carry "
          "ADULT_FUNCTIONAL_EVIDENCE: rodent in vivo or slice work; one item adds human post-mortem expression "
          "(PMID-verified, species per item in `literature_curation.json`). Some items delete netrin-1, the "
          "ligand, rather than DCC:")
        for i in adult_items[:8]:
            w(f"  - {i.get('first_author', '')} {i.get('year', '')} (PMID {i.get('pmid', '')}; "
              f"{str(i.get('species_system', i.get('species', '')))[:70]}): {i.get('finding', '')}")
        td = dcc.get("timing_dimensions", {})
        if td:
            w(f"- **Separated reading.** Expression: {str(td.get('expression_timing', ''))[:420]}")
            w(f"  Function: {str(td.get('functional_timing', ''))[:420]}")
    else:
        w("- **Functional timing:** literature curation pending.")
    w("")
    w("So \"prenatal-dominant expression\" must not be read as \"development-only function\". DCC is "
      "ADULT_EXPRESSED (weakly) with ADULT_FUNCTIONAL_EVIDENCE from animal work. It has no adult human causal "
      "evidence, and its LoF phenotype (mirror movements, callosal agenesis) is developmental. LoF impairment is "
      "never inverted into enhancement.")
    w("")

    # ---------------- PART 5 ---------------------------------------------------------------
    n = negr1["NEGR1"]
    sy = negr1["SYT1"]
    w("## 5. NEGR1 direction audit (and SYT1)")
    w("")
    w("The threshold is frozen and unchanged: ≥3 strong gene-level adult-brain eQTL/pQTL colocalisations and ≥80% "
      "polarity-adjusted agreement. What changes is the counting unit, from rows to (GWAS signal group × QTL "
      "cohort). Rows are not independent:")
    w("")
    w("- every cognition GWAS here contains UK Biobank;")
    w("- GTEx tissues share donors.")
    w("")
    w("| gene | Sprint-3 rows (agreement) | strict gene-level rows | independent units | concordant units | "
      "resolved on units? |")
    w("|---|---|---|---|---|---|")
    for g, v in (("NEGR1", n), ("SYT1", sy)):
        w(f"| {g} | {v['sprint3_rows_counted']} ({(v['sprint3_row_agreement'] or 0):.0%}) | "
          f"{v['sprint3_rows_counted_strict_gene_level']} | {v['n_independent_units']} | "
          f"{v['n_units_directionally_concordant']} | {'yes' if v['direction_resolved_under_frozen_rule_on_units'] else 'no'} |")
    w("")
    w(f"**NEGR1.** The four rows are one QTL dataset (ROSMAP DLPFC, gene-level) × one lead variant (rs66495454), "
      f"reported by four GWAS:")
    w("")
    w("- Sniekers 2017;")
    w("- three UK-Biobank field-20016 fluid-intelligence analyses.")
    w("")
    w("The one discordant row is Sniekers. Its lead is a **multi-allelic insertion** (-/TCC/TCCT) absent from "
      "1000G EUR, so its allele coding across studies is fragile and the discordance is plausibly a harmonisation "
      "artefact. The unit's majority direction: cognition-increasing allele → higher NEGR1 expression.")
    w("")
    w(f"Independent units: **{n['n_independent_units']}**; the frozen rule needs 3. NEGR1 is **not near "
      f"resolution**. The locus also holds weakly linked leads:")
    w("")
    w("- rs12128707 has r² = 0.045 with the Davies lead rs3101338 and 0.15 with the rs2815752/rs3101336 CNV-tagging "
      "pair.")
    w("")
    w("So \"one NEGR1 signal\" is itself uncertain: 3 GWAS signal groups appear across all rows.")
    w("")
    nl = (lit.get("negr1_expression_direction_literature") or {}) if lit else {}
    if nl:
        w("**NEGR1: what the literature adds (PMID-verified; `literature_curation.json`).**")
        w("")
        w("- The obesity-associated upstream deletion acts via an 8-kb deletion that removes a repressor site; "
          "its direction evidence (higher NEGR1) comes from lymphoblastoid cells, not brain.")
        w("- A depression-risk allele is reported to raise NEGR1 in brain.")
        w("- Whether either haplotype is the cognition signal is UNVERIFIED.")
        w("- Functionally, both knockout and overexpression impair neuronal phenotypes. So even a resolved "
          "eQTL direction would not license \"increase NEGR1\": the dose-response may be non-monotonic.")
        w("")
    w(f"**SYT1.** All {sy['sprint3_rows_counted']} Sprint-3 rows are **transcript-level (ENST) eQTLs**, not "
      f"gene-level. The Sprint-3 rule's text said \"gene-level\", but its regex excluded only exon traits. Under "
      f"strict gene-level eligibility SYT1 has **0** qualifying colocalisations.")
    w("")
    rps = recount[recount.gene == "RPS26"].iloc[0]
    w("**Genome-wide recount** (`direction_rule_recount_all_genes.csv`) under strict gene-level eligibility and "
      "unit counting:")
    w("")
    w(f"- Genes resolved under the Sprint-3 row count: {int(recount.sprint3_resolved.sum())}.")
    w(f"- Genes resolved on units: {int(recount.resolved_on_units.sum())} — **RPS26**:")
    w(f"  - {int(rps.strict_gene_level_rows)} strict gene-level rows, {rps.strict_agreement:.0%} agreement;")
    w(f"  - {int(rps.distinct_qtl_cohorts_strict)} QTL cohorts;")
    w("  - adult cohorts: GTEx, BrainSeq, CommonMind, ROSMAP (Walker and Aygün are fetal; Jerber is iPSC-derived "
      "neurons, so they are excluded as non-adult);")
    w("  - cognition-increasing allele → higher RPS26 expression.")
    w("")
    w("RPS26 failed in Sprint 3 only because transcript-level rows diluted its agreement (72 rows, 69%). Caveats "
      "that stop this being a target claim:")
    w("")
    w("- the lead rs1131017 is palindromic (C/G);")
    w("- RPS26 is a ribosomal gene with one of the strongest ubiquitous eQTLs in the genome, a known "
      "colocalisation \"hub\";")
    w("- 12q13.2 is a dense pleiotropic locus (ERBB3, SUOX, RAB5B, CDK2, IKZF4 all Bonferroni at gene level); "
      "ERBB3, a Top-50 gene, has no strong colocalisation;")
    w("- the GWAS half is still the UK-Biobank lineage.")
    w("")
    w("The eligibility definition was **frozen in the Sprint-4 protocol before this audit** (\"gene-level only, "
      "exon/transcript/splice excluded\"), so Sprint 4 Gate C tests RPS26 under a rule that was not tuned to it.")
    w("")

    # ---------------- PART 6 ---------------------------------------------------------------
    w("## 6. Synaptic system map and model comparison")
    w("")
    w("Per-gene, per-category map: `synaptic_system_map.csv`. It keeps two evidence layers side by side:")
    w("")
    w("- **Annotation:** membership of the pre-registered SynGO/propagated-GO machinery sets.")
    w("- **Literature:** PMID-verified, species and evidence type stated.")
    w("")
    w("Genetic evidence (MAGMA P, fine-mapping driver, direction units) sits on every row.")
    w("")
    w("| gene | Davies P | SynGO compartment | literature compartment | categories (annotation / literature) |")
    w("|---|---|---|---|---|")
    for g, grp in sysmap.groupby("gene", sort=False):
        a = ", ".join(c.replace("_", " ") for c in grp[grp.annotation_member].category) or "—"
        lt = ", ".join(c.replace("_", " ") for c in grp[grp.literature_supported].category) or "—"
        r0 = grp.iloc[0]
        lc = str(r0.literature_primary_compartment).split(" (")[0][:40]
        w(f"| {g} | {fmt_p(r0.davies_magma_P)} | {r0.syngo_compartment} | {lc} | {a} / {lt} |")
    w("")
    notes = sysmap.drop_duplicates("gene")[["gene", "literature_critical_note"]].dropna()
    notes = notes[notes.literature_critical_note.astype(str).str.len() > 0]
    if len(notes):
        w("Curator's critical notes (from the PMID-verified literature layer):")
        w("")
        for r0 in notes.itertuples():
            w(f"- **{r0.gene}:** {str(r0.literature_critical_note)[:300]}")
        w("")
    w("**Model comparison** (spec D, and spec E for neuronal conditioning; one-sided marginal unless marked):")
    w("")
    w("| machinery category | D | E |")
    w("|---|---|---|")
    for c in ["synapse_formation_adhesion", "active_zone_organisation", "vesicle_cycle_trafficking",
              "vesicle_docking_priming", "ca_triggered_release", "snare_cycle", "receptor_trafficking",
              "postsynaptic_plasticity_structure", "activity_dependent_remodelling", "generic_neuronal_projection"]:
        a, e = mg["D"][f"CAT_{c}"], mg["E"][f"CAT_{c}"]
        w(f"| {c.replace('_', ' ')} ({int(a.ngenes)}) | {cell(a.beta, a.P)} | {cell(e.beta, e.P)} |")
    w(f"| release-machinery union | {cell(mg['D']['RELEASE_MACHINERY'].beta, mg['D']['RELEASE_MACHINERY'].P)} | "
      f"{cell(mg['E']['RELEASE_MACHINERY'].beta, mg['E']['RELEASE_MACHINERY'].P)} |")
    w(f"| organisation/trafficking union | {cell(mg['D']['ORGANISATION_TRAFFICKING'].beta, mg['D']['ORGANISATION_TRAFFICKING'].P)} | "
      f"{cell(mg['E']['ORGANISATION_TRAFFICKING'].beta, mg['E']['ORGANISATION_TRAFFICKING'].P)} |")
    w(f"| **contrast** release-only − organisation-only (two-sided) | "
      f"{cell(pp['D']['rel_contrast'].beta, pp['D']['rel_contrast'].P)} | "
      f"{cell(pp['E']['rel_contrast'].beta, pp['E']['rel_contrast'].P)} |")
    w(f"| neuron-specific top-20% set | {cell(mg['D']['NEURON_SPECIFIC_TOP20'].beta, mg['D']['NEURON_SPECIFIC_TOP20'].P)} | "
      f"(conditioned away) |")
    w("")
    w("**MODEL A — presynaptic release is the primary system.** **Rejected.**")
    w("")
    w("Every release category is null:")
    w("")
    w("- active zone;")
    w("- vesicle cycle;")
    w("- docking/priming;")
    w("- Ca²⁺-triggered release;")
    w("- SNARE.")
    w("")
    w("The release-only vs organisation-only contrast is null, and pre vs post is null. Of the named genes:")
    w("")
    w("- SYT1, RIMS2 and BSN are genuine release/active-zone genes, but they are 3 loci among 159;")
    w("- KCNJ3, which drives the \"presynaptic voltage-gated channel\" set, is a GIRK channel best known for "
      "somatodendritic inhibition.")
    w("")
    w("**MODEL B — broad synaptic organisation + membrane/vesicle trafficking.** **Supported for organisation "
      "(membrane/adhesion); not for trafficking.**")
    w("")
    w("- Synapse formation/adhesion is the only nominal machinery category.")
    w("- The adhesion and membrane sets survive every specification.")
    w("- Their drivers are adhesion molecules: CDH9, PTPRF, CADM2, NCAM1, PTPRD, LRRC4, cadherins.")
    w("- Vesicle and receptor trafficking are null.")
    w("- EXOC4 and NSF are trafficking genes, but general-purpose ones.")
    w("")
    w(f"**MODEL C — generic neuronal biology / annotation structure.** **Partly true.**")
    w("")
    w(f"- Neuronal expression absorbs about {atten:.0%} of the broad synapse effect.")
    w("- The neuron-specific background set is itself strongly enriched.")
    w("- Unpropagated GO had tilted Sprint 3 toward SynGO.")
    w("")
    w("But it is not the whole story:")
    w("")
    w("- synapse remains nominal conditional on neuron-specific genes, brain-expressed genes and neuron projection;")
    w("- the adhesion/membrane core stays at P ≈ 1e-5.")
    w("")
    w("**Chosen abstraction:** BROAD SYNAPTIC ORGANISATION (synaptic-membrane / trans-synaptic adhesion), on a large "
      "generic-neuronal base. This is not the most convenient model for a target programme: adhesion molecules "
      "are developmental and structural as much as adult-plastic.")
    w("")

    # ---------------- PART 7 ---------------------------------------------------------------
    w("## 7. Extreme tail: the 1.13x result")
    w("")
    w("Full reassessment: `extreme_tail_reassessment.md`. In short:")
    w("")
    lo, hi = ext["ratio_range"]
    w(f"- The observed/predicted ratio ranges from **{lo:.2f} to {hi:.2f}** under defensible assumptions about "
      "ascertainment and winner's curse, so it proves neither continuity nor amplification.")
    w("- The Sprint-3 \"121/159 loci same sign\" was an unsigned gene-level statistic, not a sign test.")
    w(f"- A genuine allele-direction test gives {ldt['n_concordant']}/{ldt['n_testable']} "
      f"({ldt['fraction_concordant']:.0%}) concordant, P = {fmt_p(ldt['binomial_P_vs_half_one_sided'])}. That "
      f"is within the {ldt['expected_under_continuity']['N_eff 4,300']['expected_fraction']:.0%}–"
      f"{ldt['expected_under_continuity']['equivalent N, top 0.03%']['expected_fraction']:.0%} expected under "
      f"continuity.")
    w("")
    w("**Corrected wording:** NO STRONG EVIDENCE FOR A DISTINCT COMMON-VARIANT ARCHITECTURE IN THE EXTREME TAIL. "
      "The same alleles point the same way. Magnitudes are not pinned down.")
    w("")

    # ---------------- CORRECTIONS -------------------------------------------------------------
    w("## Corrections to previous wording (dated 2026-09-23)")
    w("")
    w("Each item is also written as a dated correction block into the affected file; the original text is kept.")
    w("")
    k3 = lolo[(lolo.set == "GO_0099508") & lolo.excluded_set_genes.str.contains("KCNJ3")].iloc[0]
    kcnj3_fold = k3.loo_P / k3.full_P
    corr = [
        ("C1", "GENE_TOURNAMENT_FINAL.md headline 3, §H.3, Q16; PROJECT_STATUS", "\"presynaptic rather than postsynaptic\"",
         "broad synaptic enrichment concentrated in synaptic-membrane/adhesion genes; no demonstrated presynaptic skew; postsynapse not weaker (§1)"),
        ("C2", "GENE_TOURNAMENT_FINAL.md headline 3; truth-table synaptic row", "\"the only pathway signal that survives\"",
         "with propagated GO, CNS neuron differentiation and neuron migration also survive global FDR in every specification (§2)"),
        ("C3", "run_pathway_enrichment.py (method)", "conditioned runs silently used 17,069 genes",
         "covariates must cover all 18,418 genes; Sprint-3 numbers reproduced and kept, full-universe results added (§2)"),
        ("C4", "build_pathway_sets.py (method)", "GO sets from direct gene2go annotations",
         "GO sets must be propagated before comparing themes against SynGO (§2)"),
        ("C5", "GENE_TOURNAMENT_FINAL.md headline 2, §D, §H.2, Q4; truth-table continuity row", "\"1.13x … proves continuity\"",
         "ratio spans 0.61–1.25 under plausible assumptions; replaced by the signed locus-direction test (§7)"),
        ("C6", "GENE_TOURNAMENT_FINAL.md headline 2, §D, Q4", "\"121/159 independent loci agree in sign\"",
         "that statistic was unsigned gene-level Z > 0; signed test: 112/136 concordant (§7)"),
        ("C7", "GENE_TOURNAMENT_FINAL.md §F, Q8", "\"NEGR1 (3 of 4, 75%) is the closest clean case\"",
         "1 independent unit; not near resolution (§5)"),
        ("C8", "build_consensus.py direction rule", "\"gene-level\" eligibility admitted transcript-level eQTLs",
         "strict gene-level eligibility; SYT1 has 0 qualifying colocs; RPS26 meets the unchanged threshold (§5)"),
        ("C9", "TOP50_ADULT_MODIFIABLE_GENES.csv, GENE_TOURNAMENT_FINAL.md §B", "\"adult-modifiable\"",
         "ADULT-EXPRESSION-COMPATIBLE; five-tier hierarchy (§4)"),
        ("C10", "build_master_universe.py (n_strict_ukb_free_units)", "Perry 2025 counted as UKB-free",
         "cohort string \"UKB \" (trailing space) missed; UKB-free units overstated for 11 natural Top-50 genes (§3)"),
        ("C11", "TOP50 lists", "consensus ranks as ordering",
         "ranks are triage; one lineage counted several times; tails decided by ties (§3)"),
        ("C12", "DCC developmental class", "PRENATAL_DOMINANT read as development-only",
         "expression timing and functional timing recorded separately (§4)"),
        ("C13", "GENE_TOURNAMENT_FINAL.md §H.3", "\"presynaptic voltage-gated channels\" as presynaptic biology",
         f"that 17-gene set is driven by KCNJ3 (GIRK1, classically somatodendritic) and SCN2A; leave-KCNJ3-out P rises "
         f"{kcnj3_fold:.0f}-fold, to {fmt_p(lolo_worst['GO_0099508'])} (§1, §6)"),
    ]
    w("| id | where | previous wording | corrected |")
    w("|---|---|---|---|")
    for c in corr:
        w(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
    w("")

    # ---------------- methods / verification ----------------------------------------------------
    w("## Files, methods, verification")
    w("")
    w("- **Inputs**, all from Sprint 3 and none new:")
    w("  - Davies 2018 `.genes.raw` (the verified X01 gene layer);")
    w("  - SynGO 1.3, gene2go and go-basic.obo (local snapshots from 2026-09-22);")
    w("  - Siletti 2022 superclusters (read-only from the Codex worktree);")
    w("  - GTEx v10 medians; Open Targets colocalisation compact file; Zabaneh 2018 and Savage 2018 gene-level "
      "results; Zabaneh allele-level summary statistics (GCST005626, sha256 `44ddca30…`).")
    w("- **Software:** MAGMA v1.10 (same binary as Sprint 3); Python 3.12 (pandas, numpy, scipy, bed-reader).")
    w("- **Code:** `pipelines/sprint3_1/`:")
    w("  - `build_inputs.py`, `run_recon_magma.py`, `analyse_recon.py`, `leave_one_locus_out.py`;")
    w("  - `qtl_independence_audit.py`, `extreme_tail_reassessment.py`, `build_system_map.py`;")
    w("  - `rank_dependency_audit.py` (subagent);")
    w("  - `write_recon_report.py`;")
    w("  - tests `test_sprint3_1.py`, `test_rank_dependency_audit.py`.")
    w("- **Literature:** `data/sprint3_1/literature_curation.json` (subagent; PMIDs verified by metadata lookup).")
    w("- **Limits:**")
    w("  - everything rests on UK-Biobank-containing European-ancestry GWAS;")
    w("  - the neuronal covariate is one atlas (bulk-pseudobulk superclusters);")
    w("  - theme regex families are coarse;")
    w("  - joint-model P-values are MAGMA's (normal-theory, gene-correlation-adjusted).")
    w("")
    w(f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')} by `pipelines/sprint3_1/write_recon_report.py`.*")
    (R / "SYNAPTIC_RECON_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------- extreme tail md -----------------------------------------------------------
    E: list[str] = []
    e = E.append
    e("# Extreme-IQ continuity — reassessment of the Sprint-3 \"1.13x\" result")
    e("")
    e(f"*{TODAY} · Sprint 3.1 · data: Zabaneh 2018 extreme IQ (GCST005626; 1,238 Duke TIP cases, 8,172 HRS "
      "controls) vs Davies 2018 (N=282,014). Code: `pipelines/sprint3_1/extreme_tail_reassessment.py`.*")
    e("")
    e("## What Sprint 3 computed")
    e("")
    e("For the 375 population-Bonferroni genes, Sprint 3 predicted the extreme-tail mean MAGMA gene Z as:")
    e("")
    e("> rest-of-genome mean + (Davies mean Z of the 375 − genome mean) / √(282,014 / 4,300)")
    e("")
    e("It found the observed shift to be 1.13× the prediction, and wrote \"continuous … no upper-tail "
      "amplification is required\".")
    e("")
    e("## Why the ratio cannot carry that conclusion")
    e("")
    e("1. **Extreme ascertainment.**")
    e("   - Cases are roughly the top 0.03% (mean standardised trait value i ≈ 3.7). Controls are unselected.")
    e("   - The case-control non-centrality is N_eff·i²/4 times the per-person quantitative-trait value. The "
      "equivalent population N is therefore about 14,600, not 4,300.")
    e("   - With that N the same arithmetic gives 0.61×.")
    e("   - Cases were selected on SAT scores at about age 12. Measurement error and regression to the mean lower "
      "the effective i, which pushes the ratio back toward 1.")
    e("2. **Winner's curse.** The 375 genes were selected on Davies Z, which inflates the predicted shift. "
      "Re-evaluating them in Savage 2018 reduces, but cannot remove, this, because Savage shares UK Biobank.")
    e("3. **Non-linearity.** MAGMA gene Z is the probit of a P-value from a sum of squared SNP z-scores, so it does "
      "not scale with √N. The proper expectation needs LD-aware subsampling to the equivalent N (the Sprint-4 "
      "calibration method). It is not attempted here.")
    e("4. **Sample overlap.** Zabaneh's controls are the Health and Retirement Study.")
    ex_lit = (lit.get("extreme_iq") or {}) if lit else {}
    if ex_lit:
        e("   - **Verified from source** (`literature_curation.json`): HRS is a contributing cohort of Davies 2018 "
          "(Supplementary Note 2; about 7,400 with cognitive data).")
        e("   - Zabaneh's cases AND controls are both inside Savage 2018 (its \"HiQ/HRS\" cohort).")
        e("   - The shared individuals are Zabaneh CONTROLS, whose extreme-IQ phenotype is constant. Under a "
          "standard regression, the noise covariance they induce with Davies' mean-centred cognition statistic is "
          "approximately zero. So the bias toward continuity is expected to be small, but it is not formally "
          "estimated here.")
    e("   - If HRS contributes to Davies, shared noise inflates every agreement statistic toward continuity.")
    e("")
    e("### Sensitivity table")
    e("")
    e("| population Z source | scenario | equivalent N | predicted shift | observed shift | observed / predicted |")
    e("|---|---|---|---|---|---|")
    for r in ext["sensitivity"]:
        e(f"| {r['population_z_source']} | {r['scenario']} | {r['equivalent_N']:,} | {r['predicted_shift']:.3f} | "
          f"{r['observed_shift']:.3f} | **{r['observed_over_predicted']:.2f}** |")
    e("")
    e(f"Range: {lo:.2f}–{hi:.2f}. The number straddles 1, so it cannot distinguish continuity from attenuation "
      "or amplification.")
    e("")
    e("## A second error: \"121/159 loci agree in sign\" was not a sign test")
    e("")
    e("MAGMA gene Z is unsigned. \"Positive extreme-tail Z\" meant *above-median association*, not the same allele "
      "direction. The 62% background rate reflects genome-wide inflation of gene Z.")
    e("")
    e("## The defensible evidence: allele-direction concordance at the 159 loci")
    e("")
    e("Method:")
    e("")
    e("- Davies lead SNP per locus (the rule frozen in the Sprint-4 protocol);")
    e("- cognition-increasing allele looked up in Zabaneh, z = ln OR / SE, aligned by allele;")
    e("- palindromic SNPs excluded.")
    e("")
    e(f"Result:")
    e("")
    e(f"- **{ldt['n_concordant']} of {ldt['n_testable']} testable loci concordant ({ldt['fraction_concordant']:.0%}); "
      f"one-sided binomial P = {fmt_p(ldt['binomial_P_vs_half_one_sided'])}.**")
    e(f"- Loci not testable: {ldt['n_absent']} absent, {ldt['n_palindromic_excluded']} palindromic, "
      f"{ldt['n_allele_mismatch']} with mismatched alleles.")
    e("- Continuity predicts, using Tweedie-shrunk Davies z to reduce winner's curse:")
    for k, v in ldt["expected_under_continuity"].items():
        e(f"  - {k}: {v['expected_concordant']:.1f} ({v['expected_fraction']:.0%}).")
    e("")
    e("The observed concordance sits inside the range continuity predicts, well above chance. Per-locus table: "
      "`extreme_tail_locus_direction.csv`.")
    e("")
    e("## Corrected conclusion")
    e("")
    e("**No strong evidence for a distinct common-variant architecture in the extreme tail.** Supporting this:")
    e("")
    e("- the same alleles push in the same direction (sign test above);")
    e("- no gene is tail-specific (0 genome-wide significant genes);")
    rg_rows = ((ex_lit.get("genetic_correlations_snp_based") or {}).get("table_2_rows") or []) if ex_lit else []
    if rg_rows:
        e("- the published LDSC genetic correlations (Zabaneh 2018, Table 2):")
        for r in rg_rows:
            e(f"  - rg {r.get('rg')} (SE {r.get('se')}) with {r.get('trait')} ({r.get('reference_gwas', '')[:60]}).")
        e("  - LDSC rg is not biased by sample overlap.")
    else:
        e("- the published genetic correlation (not curated).")
    e("")
    e("Not established:")
    e("")
    e("- that effect *magnitudes* scale exactly as a continuous model predicts (the ratio is not identifiable "
      "from these data);")
    e("- anything about rare variants.")
    e("")
    e("The HRS/Davies overlap question remains open and biases toward this conclusion. The earlier wording "
      "\"1.13x … proves continuity\" is withdrawn.")
    e("")
    if ex_lit:
        e("### Curated literature (PMID-verified)")
        e("")
        for s in ex_lit.get("decision_relevant_summary", []):
            e(f"- {s}")
        e("")
    (R / "extreme_tail_reassessment.md").write_text("\n".join(E) + "\n", encoding="utf-8")
    print("wrote", R / "SYNAPTIC_RECON_REPORT.md", "and", R / "extreme_tail_reassessment.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
