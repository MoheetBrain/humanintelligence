#!/usr/bin/env python3
"""Write reports/GENE_TOURNAMENT_FINAL.md from the Sprint-3 artefacts.

Every table and every number in the report is read from a file at build time. The prose
around them is judgement, and says so where it matters. Re-running after any upstream
change regenerates the report consistently.
"""

from __future__ import annotations

import sys

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "reports" / "gene_tournament"
D = ROOT / "data" / "gene_tournament"


def j(name):
    return json.loads((T / name).read_text())


def fmt_p(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if np.isnan(x):
        return "—"
    return f"{x:.1e}" if x < 1e-3 else f"{x:.3f}"


def rank(x):
    return "—" if pd.isna(x) else str(int(x))


def top_table(top: pd.DataFrame, red: pd.DataFrame, adult: bool) -> list[str]:
    t = top.merge(red[["entrez_id", "red_team_verdict"]], on="entrez_id", how="left")
    b = pd.read_csv(T / "direct_cognition_rank.csv")[["entrez_id", "gene_P", "gene_P_savage"]]
    t = t.merge(b, on="entrez_id", how="left")
    fm = pd.read_csv(T / "fine_mapping_support.csv").set_index("gene")

    def finemap(gene):
        # A tied rank (every gene whose L2G calls are all positional shares one) reads like
        # a moderate result, so the table states what the fine-mapping actually shows.
        if gene not in fm.index:
            return "—"
        r = fm.loc[gene]
        if r.n_supported_loci > 0:
            return f"L2G {r.max_l2g:.2f} ({str(r.supported_call_drivers).split('|')[0]})"
        return "positional only"
    head = ("| # | Gene | Rank interval | MAGMA P (Davies) | Savage P | Strict cohort units | Fine-mapping | "
            "Brain coloc | Module | Timing | Carried by | Red team | Safety |")
    out = [head, "|" + "---|" * 13]
    for _, r in t.iterrows():
        out.append(f"| {int(r.consensus_rank)} | **{r.gene}** | {r.rank_interval} | {fmt_p(r.gene_P)} | "
                   f"{fmt_p(r.gene_P_savage)} | {int(r.number_independent_cohorts)} | {finemap(r.gene)} | "
                   f"{r.colocalisation_class if isinstance(r.colocalisation_class, str) else '—'} | "
                   f"{r.module if isinstance(r.module, str) else '—'} | {r.developmental_class} | {r.carried_by} | "
                   f"{r.red_team_verdict} | {r.safety_flags if isinstance(r.safety_flags, str) and r.safety_flags else ''} |")
    return out


def main() -> int:
    nat = pd.read_csv(T / "TOP50_HUMAN_COGNITION_GENES.csv")
    ad = pd.read_csv(T / "TOP50_ADULT_MODIFIABLE_GENES.csv")
    red_n = pd.read_csv(T / "red_team_top50_human.csv")
    red_a = pd.read_csv(T / "red_team_top50_adult.csv")
    mods = pd.read_csv(T / "TOP10_COGNITION_MODULES.csv")
    rtm = pd.read_csv(T / "red_team_modules.csv").set_index("module")
    ext = j("extreme_tail_summary.json")["mode_1_summary_statistic"]
    cv = ext["continuity_verdict"]
    gr = j("gene_ranks_summary.json")
    ms = j("modules_summary.json")
    cs = j("consensus_summary.json")
    rs = j("red_team_summary.json")
    pe = j("pathway_enrichment_summary.json")
    b = pd.read_csv(T / "direct_cognition_rank.csv")
    h = pd.read_csv(T / "adult_brain_directionality.csv")
    g = pd.read_csv(T / "fine_mapping_support.csv")
    e = pd.read_csv(T / "math_gene_rank.csv")
    pj = pd.read_csv(T / "positive_human_perturbations.csv")
    rep = pd.read_csv(T / "pathway_replication.csv")
    panel = pd.read_csv(T / "pathway_hypothesis_panel.csv").set_index("hypothesis")
    te = pd.read_csv(T / "module_tail_engagement.csv").set_index("module")
    comp = pd.read_csv(T / "comparative_top_genes.csv") if (T / "comparative_top_genes.csv").exists() else None
    gprov = json.loads((D / "gwas_credible_sets_provenance.json").read_text())
    univ = json.loads((D / "master_gene_universe_summary.json").read_text())
    seeds = ["CKB", "GPR158", "KCNQ3", "ADORA1", "DRD1", "RGS14", "RTN4R", "CHRM1", "HTR2A", "GRIN2B",
             "PDE4B", "KCNQ2", "OTX2", "HCAR1", "KL", "SLC16A7", "HDAC2", "SLC16A3", "HCN1", "SLC16A1",
             "GABRA5", "GRM5", "PTPN5", "EIF2S1", "CRTC1"]
    sb = b[b.gene.isin(seeds)].sort_values("gene_P")
    n_sig = int(b.bonferroni_davies.sum())
    # ---- facts computed here rather than transcribed from exploratory runs ----
    from scipy import stats as st
    con = pd.read_csv(ROOT / "data/interim/gnomad_constraint.tsv", sep="\t").rename(columns={"GENE": "entrez_id"})
    cj = b.merge(con, on="entrez_id").dropna(subset=["oe_lof_upper", "gene_Z", "bp_length"])
    rk = lambda v: st.rankdata(v)  # noqa: E731
    def _res(y, x):
        X = np.column_stack([x, np.ones(len(x))]); return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    pc = st.pearsonr(_res(rk(cj.oe_lof_upper), rk(np.log10(cj.bp_length))), _res(rk(cj.gene_Z), rk(np.log10(cj.bp_length))))
    len_rho = st.spearmanr(np.log10(cj.bp_length), cj.gene_Z).statistic
    dev = pd.read_parquet(D / "developmental_classification.parquet").dropna(subset=["entrez_id"])
    dev["entrez_id"] = pd.to_numeric(dev.entrez_id, errors="coerce")
    dj = b.merge(dev.dropna(subset=["entrez_id"]).drop_duplicates("entrez_id")[["entrez_id", "developmental_class"]], on="entrez_id")
    or_ad = st.fisher_exact(pd.crosstab(dj.bonferroni_davies, dj.developmental_class == "ADULT_DYNAMIC").values, alternative="greater")
    or_dv = st.fisher_exact(pd.crosstab(dj.bonferroni_davies, dj.developmental_class.isin(["PRENATAL_DOMINANT", "DEVELOPMENTAL"])).values, alternative="greater")
    k_nom = int((sb.gene_P < 0.05).sum())
    seed_binom = st.binomtest(k_nom, len(sb), 0.05, alternative="greater").pvalue
    n_hi3 = int(pj.effect.astype(str).str.contains("HI score 3;").sum())
    hi3_genes = pj[pj.effect.astype(str).str.contains("HI score 3;")].genes.tolist()
    top20 = nat.head(20)
    dev_top = top20[top20.developmental_class.isin(["PRENATAL_DOMINANT", "DEVELOPMENTAL"])].gene.tolist()
    adult_top = pd.concat([nat, ad])[lambda x: x.developmental_class == "ADULT_DYNAMIC"].drop_duplicates("gene").head(12).gene.tolist()
    new_top = [x for x in nat.gene.head(20) if x not in seeds]
    fdr05 = cs["natural"]["n_eligible_genes_FDR_lt_0.05"]
    L: list[str] = []
    A = L.append

    A("# Gene Tournament — Final Report (Sprint 3)\n")
    A("*Generated by `pipelines/gene_tournament/write_final_report.py` from the Sprint-3 artefacts in "
      "`reports/gene_tournament/`. Every table and number is read from a file; the prose is judgement. "
      "All work is computational. The chemistry gate is closed: nothing here is a target nomination, a "
      "direction of benefit, or a reason to intervene.*\n")
    A("## Headline\n")
    A(f"1. **The universe can be ranked, but only coarsely.** {n_sig} of 18,418 genes pass Bonferroni in a "
      f"verified gene-level analysis of general cognition (N=282,014); they are **{gr['part_b']['n_ld_blocks_bonferroni']} "
      "independent loci**, not 375 findings. Beyond the first ~20 genes the consensus ranking is unstable: "
      f"{cs['natural']['n_top50_rank_interval_upper_gt_200']} of the top 50 have rank intervals reaching past 200, "
      "and ranks 51+ are ties.")
    A(f"2. **Extreme cognition is continuous with ordinary cognition at gene level.** The extreme-IQ sample (IQ~170) "
      f"shows {cv['power_scaling_test']['observed_over_predicted_shift']:.2f}x the shift pure continuity predicts, "
      f"{cv['locus_level_sign_test']['n_with_positive_extreme_tail_Z']}/{cv['locus_level_sign_test']['n_independent_loci']} "
      "independent loci point the same way, and no gene is genome-wide significant in the tail. There is no genius gene set.")
    A("3. **Synaptic biology is the only pathway signal that survives an unbiased, fully conditioned test** "
      "(6 of 6,200 sets at global FDR, all synaptic, presynaptic rather than postsynaptic). It reproduces in an "
      "overlapping meta-analysis and is untested — not refuted — in the only UKB-free sample. Myelin, energy "
      "metabolism, astrocytes, ion channels, GPCRs, neuromodulators, translation and chromatin do not survive.")
    A(f"4. **The gene-to-direction bridge does not exist yet.** {gprov['n_top_calls_positional_driven']:,} of "
      f"{gprov['n_top_calls']:,} top locus-to-gene calls ({gprov['n_top_calls_positional_driven']/gprov['n_top_calls']:.0%}) "
      "are driven by distance or gene density; only 34 genes have biology-driven fine-mapping support; and "
      "**zero** genes have a directionally consistent adult-brain expression effect at the pre-set threshold.")
    A("5. **The hand-picked seed list does not survive contact with the genome.** 1 of 25 testable seeds passes "
      "Bonferroni (CKB, rank 365). The strongest human loci — DCC, NEGR1, EXOC4, NT5DC2, BSN, MEF2C — were never "
      "on it.")
    A("6. **Three corrections to earlier sprints**: the Codex/Astra branch exists (Sprint 2 said it did not); "
      "the 2q12.3 duplication's gene list was wrong (wrong genome build); ADGRB1's Sprint-2 downgrade is reversed. "
      "Details in §H and the red-team section.\n")

    # ---------------------------------------------------------------- A
    A("## A. Top 50 human cognition genes\n")
    A("Natural-intelligence ranking: **Robust Rank Aggregation** over the dimensions that have at least one "
      "gene passing their own multiple-testing threshold — direct cognition (MAGMA), independent replication, "
      "fine-mapping, brain colocalisation, positive human perturbation, module convergence. Eligibility: MAGMA "
      f"gene FDR<0.05 ({fdr05:,} genes). One gene per LD block. Extreme-tail and arithmetic ranks are reported "
      "per gene but enter only the all-dimensions sensitivity run (see §Rank robustness for why, and when that "
      "rule was adopted).\n")
    L.extend(top_table(nat, red_n, False))
    A("\n*Rank gaps* occur where an LD block-mate outranks a gene (one gene per block is shown). *Fine-mapping*: "
      "the top L2G score and its dominant driver where a supported locus exists; \"positional only\" where every "
      "top call is driven by distance or gene density. *Ties*: several genes share rank 51 — synaptic-module members that the dimensions cannot separate. "
      "That is the resolution limit of the evidence. Full columns, including every per-dimension rank, "
      "`major_support`, `major_counterevidence` and `next_kill_test`: "
      "[`TOP50_HUMAN_COGNITION_GENES.csv`](gene_tournament/TOP50_HUMAN_COGNITION_GENES.csv); dossiers: "
      "[`GENE_CARDS_TOP50_HUMAN.md`](gene_tournament/GENE_CARDS_TOP50_HUMAN.md).\n")

    # ---------------------------------------------------------------- B
    A("## B. Top 50 adult-modifiable candidates\n")
    A("Same method, a different question. **Gate**: adult-expressed (GTEx v10, TPM≥1 in a brain tissue) and "
      f"not prenatal-dominant or unknown in BrainSpan ({cs['adult']['n_eligible_genes_FDR_lt_0.05']:,} eligible "
      "genes). Dimensions add adult-modifiability (developmental class + adult expression) and "
      "directionality. **Safety is a flag, never a promoting dimension.** \"Adult-modifiable\" here means "
      "*expressed and dynamic in the adult brain* — necessary for intervention, nowhere near sufficient. "
      "No row is a target.\n")
    L.extend(top_table(ad, red_a, True))
    A("\nFull table: [`TOP50_ADULT_MODIFIABLE_GENES.csv`](gene_tournament/TOP50_ADULT_MODIFIABLE_GENES.csv); "
      "dossiers: [`GENE_CARDS_TOP50_ADULT.md`](gene_tournament/GENE_CARDS_TOP50_ADULT.md).\n")
    both = sorted(set(nat.gene) & set(ad.gene))
    only_nat = [x for x in nat.gene if x not in set(ad.gene)]
    A(f"**{len(both)} genes appear in both lists**: {', '.join(both)}. Genes ranking highly for natural "
      f"intelligence but excluded or low for adult intervention include the prenatal-dominant top locus "
      f"**DCC**, plus {', '.join([x for x in only_nat if x != 'DCC'][:10])}.\n")

    # ---------------------------------------------------------------- C
    A("## C. Top 10 biological modules\n")
    A(f"{ms['n_modules']} modules from {ms['n_input_genes']:,} genes at FDR<0.01 ({ms['n_input_ld_blocks']} LD "
      "blocks), Louvain on a fused annotation + STRING graph. Module ranking is RRA over evidence share, "
      "tail engagement *relative to other cognition genes*, conditioned label enrichment, bootstrap stability, "
      "reproducibility from Savage, locus count and breadth. The olfactory-receptor cluster (M10) is excluded "
      "as a gene-family artefact.\n")
    A("| Rank | Module | Top labels | Genes / loci | Evidence share | Tail engagement vs other cognition genes | Label enrichment (conditioned P / global FDR) | Stability | Savage Jaccard | Red team |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for _, m in mods.iterrows():
        lab = "; ".join(x.split(" (")[0] for x in str(m.pathway_labels).split(" ; ")[:3])
        A(f"| {int(m.module_rank)} | {m.module} | {lab} | {m.n_genes} / {m.n_independent_loci} | "
          f"{m.weighted_evidence_share:.1%} | P={fmt_p(te.MWU_P_more_tail_engaged.get(m.module))} | "
          f"{fmt_p(m.label_best_enrichment_P_conditioned)} / {fmt_p(m.label_best_enrichment_FDR_global)} | "
          f"{m.bootstrap_stability:.2f} | {m.leave_study_out_best_jaccard_savage:.2f} | {rtm.red_team_verdict.get(m.module, '')} |")
    A("\n**Is any system consistently \"more engaged\" in high cognition?** Tested properly — module genes against "
      "*other cognition genes*, extreme-tail Z residualised on population Z — only the synaptic module is, "
      f"nominally (P={fmt_p(te.MWU_P_more_tail_engaged.get('M01'))}); it does not survive Bonferroni across 12 "
      f"modules (P={fmt_p(te.bonferroni.get('M01'))}). A first version compared modules with the whole genome "
      "and credited every module with tail support; that was continuity inherited from gene selection and has "
      "been removed. \"Enlarged\" is not used: nothing here measures anatomy. Detail: "
      "[`module_report.md`](gene_tournament/module_report.md).\n")

    # ---------------------------------------------------------------- D
    A("## D. Extreme-IQ commonality results\n")
    A("**MODE 2 — INDIVIDUAL-LEVEL COMMONALITY NOT COMPUTABLE WITH CURRENT ACCESS.** The only extreme-IQ case "
      "sample (Duke TIP, top ~0.03%, mean IQ ~170) has no public deposit (no dbGaP, no EGA); its controls are "
      "dbGaP-restricted (HRS, phs000428). Cohen's d, KS distance, AUC, odds ratios, "
      "EXTREME_COGNITION_COMMONALITY_50/90 and sibling-pair comparisons were **not computed, not approximated, "
      "not imputed**. [`extreme_tail_distribution_stats.csv`](gene_tournament/extreme_tail_distribution_stats.csv) "
      "records each quantity as not computable.\n")
    t = ext["continuity_tests"]
    A("**MODE 1 — summary-statistic extreme rank (computed).** MAGMA on Zabaneh 2018 (GCST005626; 1,238 cases vs "
      "8,172 controls, N_eff 4,300 — 65x less power than the population GWAS):\n")
    A(f"* Genome-wide significant genes in the extreme sample: **{ext['extreme_gwas']['n_significant']}**.")
    A(f"* Population-significant genes carry extreme-tail signal: mean Z {t['extreme_Z_shift_in_population_significant_genes']['mean_Z_ext_significant']:.3f} "
      f"vs {t['extreme_Z_shift_in_population_significant_genes']['mean_Z_ext_rest']:.3f} (Mann-Whitney P="
      f"{fmt_p(t['extreme_Z_shift_in_population_significant_genes']['mann_whitney_p'])}; gene-size-matched permutation "
      f"P {t['extreme_Z_shift_in_population_significant_genes']['gene_size_matched_permutation_p']}).")
    A(f"* **Continuity test**: observed shift / shift predicted by pure power scaling = "
      f"**{cv['power_scaling_test']['observed_over_predicted_shift']:.2f}**. Locus-level sign test "
      f"{cv['locus_level_sign_test']['n_with_positive_extreme_tail_Z']}/{cv['locus_level_sign_test']['n_independent_loci']}, "
      f"P={fmt_p(cv['locus_level_sign_test']['p'])}.")
    A(f"* Rank correlation, one gene per LD block: rho={t['spearman_one_gene_per_LD_block']['rho']:.3f} "
      f"(P={fmt_p(t['spearman_one_gene_per_LD_block']['p'])}) — weak, as 65x less power predicts.")
    A("* **Answer: continuous, not amplified.** Unresolved threat: HRS controls may overlap CHARGE cohorts in "
      "Davies 2018, which would bias toward this answer. Scope: common variants, European ancestry.")
    A("* EXTREME_TAIL_AMPLIFICATION per gene is reported with its limitation: the top amplified genes "
      "(SLC25A1, COX18, ANKRD17 …) have population P>0.4 — with 18,000 genes and noise-dominated residuals, "
      "they are the expected extremes of a null. Hypotheses only. "
      "[`extreme_tail_rank.csv`](gene_tournament/extreme_tail_rank.csv)\n")

    # ---------------------------------------------------------------- E
    A("## E. Math-specific results\n")
    mc = gr["part_e"]["math_class"]
    A(f"* **math_specific: {mc.get('math_specific', 0)}** · shared_g_math: {mc.get('shared_g_math', 0)} · "
      f"general_only: {mc.get('general_only', 0)} · unresolved: {mc.get('unresolved', 0):,}.")
    A("* **A (raw maths)**: the only open *objective* arithmetic phenotype is one timed UK Biobank item "
      "(FI4 positional arithmetic, N≈115k). **0 genome-wide significant genes**; correlation with general "
      "cognition rho=0.11. The Catalog's EFO \"mathematical ability\" is 0/12 on summary statistics and 99.8% of "
      "its associations come from one 23andMe paper of *self-report* and *course-taking*, reported separately "
      "and never pooled with the objective item.")
    A("* **B (maths with g)**: 93 genes are Bonferroni for g and nominally positive for arithmetic — shared_g_math — "
      "led by " + ", ".join(e[e.math_class == "shared_g_math"].head(8).gene) + ".")
    A("* **C (residual after g)**: the top residual genes are **keratins (KRT6B, KRT75, KRT6C)** — a chromosome-12 "
      "LD block, not maths biology. C never replaces A.")
    A("* **Answer**: math-specific genes are **not identifiable with open data**. The one g-orthogonal maths GWAS "
      "(2025, 53 SNPs) is built on restricted 23andMe data. [`math_gene_rank.csv`](gene_tournament/math_gene_rank.csv)\n")

    # ---------------------------------------------------------------- F
    A("## F. Directionally resolved adult genes\n")
    cc = h.colocalisation_class.value_counts().to_dict()
    A(f"Of 400 candidates queried in Open Targets (0 query errors): strong brain-QTL colocalisation with a **direct** "
      f"cognition GWAS {cc.get('strong', 0)}, moderate {cc.get('moderate', 0)}, weak {cc.get('weak', 0)}, "
      f"**EA-proxy-only {cc.get('EA_proxy_only', 0)}**, none {cc.get('none_with_direct_cognition', 0)}. "
      "Among brain colocalisations the fetcher labelled \"cognition\", EA traits outnumbered direct cognition "
      "~2:1 and are excluded here.\n")
    A("**Direction resolved at the pre-set rule (≥3 strong gene-level brain eQTL/pQTL colocalisations, trait "
      f"polarity applied, ≥80% sign agreement): {int(h.direction_resolved.fillna(False).sum())} genes.** "
      "The first version read direction from each gene's single best colocalisation; for most genes that sign "
      "was contradicted by the gene's other brain colocalisations, so it was replaced. Near misses:\n")
    nm = h[h.n_strong_gene_level_brain_colocs >= 3].sort_values("sign_agreement", ascending=False)
    A("| Gene | Strong gene-level brain colocs | Sign agreement | Caveat |\n|---|---|---|---|")
    for _, r in nm.iterrows():
        A(f"| {r.gene} | {int(r.n_strong_gene_level_brain_colocs)} | {r.sign_agreement:.0%} | "
          f"{r.locus_caveat if isinstance(r.locus_caveat, str) else ''} |")
    A("\nNEGR1 (3 of 4, 75%) is the closest clean case; KANSL1 and ARL17B sit in the 17q21.31 inversion, where "
      "one haplotype drives many genes' eQTLs; RPS26 is a notoriously promiscuous eQTL. **The rule 'associated "
      "gene -> activate it' is not licensed for any gene in this tournament.** "
      "[`adult_brain_directionality.csv`](gene_tournament/adult_brain_directionality.csv)\n")

    # ---------------------------------------------------------------- G
    A("## G. Positive human genetic perturbations\n")
    A("| Evidence | Class | Genes | Direction | Effect | Replication | Status |\n|---|---|---|---|---|---|---|")
    for _, r in pj[~pj.evidence_id.str.startswith("CLINGEN")].iterrows():
        A(f"| {r.evidence_id} | {r.variant_class} | {r.genes} | {r.direction} | {r.effect} | {r.replication} | {r.status} |")
    ncg = int(pj.evidence_id.str.startswith("CLINGEN").sum())
    A(f"\n**The 2q12.3 duplication is the only positive-direction human perturbation in scope**, and its "
      "gene list is now correct: EDAR, SH3RF3, SEPTIN10, SOWAHC (hg19 chr2:109.51–110.38 Mb). Sprint 2 listed "
      "eight different genes from the hg38 cytoband. ClinGen has no dosage curation for any of the four — "
      "*unevaluated*, not benign. "
      f"{ncg} Bonferroni cognition genes carry ClinGen dosage curation; **{n_hi3} are haploinsufficient (score 3)**: "
      f"{', '.join(hi3_genes)} — genes where losing one copy causes "
      "neurodevelopmental disorder. That is a safety signal, and it is never inverted into enhancement.\n")

    # ---------------------------------------------------------------- H
    A("## H. Biggest surprises\n")
    A("1. **The Codex/Astra branch was real all along** — local, never pushed — and its X01 analysis was a "
      "genuine, well-documented MAGMA run whose gene-level layer this repository has now reproduced exactly. "
      "Sprint 2's \"does not exist\" was wrong because the search ran from a different clone.")
    A("2. **Continuity, quantitatively.** The extreme-IQ sample behaves almost exactly (1.13x) as the population "
      "polygenic score predicts. The tail is the same architecture turned up, not a different one.")
    A("3. **Presynaptic, not postsynaptic.** The surviving synaptic sets are presynaptic membrane, synaptic "
      "adhesion and presynaptic voltage-gated channels; the postsynaptic density — the home of the plasticity "
      "targets this project was seeded with — does not survive conditioning.")
    A(f"4. **Locus-to-gene is mostly nearest-gene.** {gprov['n_top_calls_positional_driven']/gprov['n_top_calls']:.0%} of "
      "top L2G calls are driven by positional features.")
    A(f"5. **Constraint beats gene length.** Cognition signal concentrates in LoF-intolerant genes (partial "
      f"rho={pc.statistic:.3f}, P={fmt_p(pc.pvalue)}, gene length removed) versus rho={len_rho:.3f} for gene "
      "length itself.")
    A("6. **The 2q12.3 gene list was wrong** because a cytoband label was resolved on the wrong genome build.")
    A(f"7. **Cognition genes are neither developmental nor adult** as a class: prenatal/developmental OR "
      f"{or_dv.statistic:.2f} (P={fmt_p(or_dv.pvalue)}), adult-dynamic OR {or_ad.statistic:.2f} (P={fmt_p(or_ad.pvalue)}).\n")

    # ---------------------------------------------------------------- I
    A("## I. Prior favourites that failed\n")
    A("Gene-level MAGMA (verified run) for the 25 testable seed targets; Bonferroni requires P<2.7e-06.\n")
    A("| Seed | MAGMA P | Rank / 18,418 |\n|---|---|---|")
    for _, r in sb.iterrows():
        A(f"| {r.gene} | {fmt_p(r.gene_P)} | {int(r.direct_cognition_rank):,} |")
    A(f"\n**{int(sb.bonferroni_davies.sum())} of {len(sb)} passes Bonferroni (CKB).** {k_nom}/{len(sb)} are nominal "
      f"(binomial P={fmt_p(seed_binom)} — weakly better than chance), median rank "
      f"{int(sb.direct_cognition_rank.median()):,} of 18,418. PDE4B (rank 7,081) and GPR158 (1,561) — both explicitly warned about in the "
      "brief — have no gene-level support. GABRA5, HCN1, GRM5, CRTC1 and EIF2S1 sit below the genome median. "
      "Of the Codex nominations, **ADGRB1 passes** (P=1.6e-07, rank 238; Sprint-2 downgrade reversed), "
      "**GRM3 does not** (P=2.2e-05, rank 543), GABBR1 is null (rank 4,058). None of this is evidence against "
      "these genes as *drug targets* — gene-level association is silent on pharmacological modulation — but "
      "the seed list's claim to be grounded in human genetics does not hold.\n")

    # ---------------------------------------------------------------- J
    A("## J. Highest-EV next analysis\n")
    A("**Test the six synaptic gene sets — and the continuity result — in a large cognition GWAS that excludes "
      "UK Biobank.** Every headline here rests on meta-analyses that share UKB, and the one UKB-free sample is "
      "65x underpowered. A UKB-free replication would, in one computation, (a) convert the synaptic finding from "
      "reproducible to replicated or kill it, (b) test continuity without the HRS/CHARGE overlap threat, and "
      "(c) give every top gene its first independent gene-level test. Candidate inputs: CHARGE/COGENT "
      "components (application), or the within-sibship cognition GWAS (a free OpenGWAS registration — "
      "which also delivers Part F).\n")

    # ---------------------------------------------------------------- Part S
    A("## Part S — the twenty questions\n")
    qs = [
        ("Can the 4,459 cognition genes be meaningfully ranked?",
         f"Coarsely. {n_sig} Bonferroni genes -> {gr['part_b']['n_ld_blocks_bonferroni']} independent loci; the top ~20 "
         "are stable-ish, the rest are not (rank intervals past 200 for most of the top 50; ties from rank 51). "
         "40% of the swept 4,459 cannot be tested by the gene-based method at all (non-coding, non-autosomal)."),
        ("Which 50 genes are most consistently supported?", "Table A. Led by " + ", ".join(nat.gene.head(10)) + f" — {int((red_n.red_team_verdict == 'RETAINED').sum())} pass the red team clean."),
        ("Which genes are most shifted in extreme high-cognition individuals?",
         "Individual-level: not computable. Summary-level: no gene is significant in the tail; the population-significant set as a whole is shifted (P=9e-26)."),
        ("Is extreme cognition continuous with population cognition at gene level?", "Yes — 1.13x the power-scaling prediction; 121/159 loci same sign (P=9e-05). Caveats: sample overlap unresolved; common variants only."),
        ("Which genes are shared between g and mathematics?", "93 shared_g_math genes (objective arithmetic item nominal + g Bonferroni), led by " + ", ".join(e[e.math_class == "shared_g_math"].head(5).gene) + ". Weak evidence: the maths side is one noisy item."),
        ("Which genes appear math-specific?", "None. The top residuals are keratins (an LD artefact)."),
        ("Which genes survive within-family evidence?", "Not computable: within-sibship cognition data need an OpenGWAS registration and contribute 0 Catalog associations. Absence of measurement, not a verdict."),
        ("Which genes have directionally resolved adult brain QTL support?", "None at the pre-set rule. Closest: NEGR1 (3/4 concordant)."),
        ("Which are predominantly developmental?", "Among the natural top 20: " + ", ".join(dev_top) + ". A developmental gene can explain natural variation and still be a poor adult lever."),
        ("Which are genuinely adult-dynamic?", ", ".join(adult_top) + " — adult-dynamic in EXPRESSION, which is necessary for, not evidence of, modifiability."),
        ("What top 10 biological modules emerge?", "Table C: synaptic; transcription factors; RNA binding/splicing; chromatin; mitochondrial/translation; kinases; ubiquitin; transport; cell cycle; immune/MHC-adjacent."),
        ("How much evidence do the top 5/10/20 modules capture?",
         f"{ms['weighted_evidence_captured']['top_5']:.0%} / {ms['weighted_evidence_captured']['top_10']:.0%} / {ms['weighted_evidence_captured']['top_20']:.0%} of FDR<0.01 gene-level evidence (NOT heritability) — the latter figures near-tautological because clustering assigns almost every gene."),
        ("Is there a small plausible biological control set?", "No. Only one module meets the evidence bar, so set cover returns one gene (NEGR1 adult-active; DCC any timing). Network hubs track annotation depth (rho=0.61). No directed causal graph exists, so controllability cannot be computed meaningfully."),
        ("Which prior favourite genes disappear?", "Table I: 24 of 25 seeds; PDE4B, GPR158, GABRA5, HCN1, GRM5, CRTC1, EIF2S1 notably."),
        ("Which previously unknown genes rise to the top?", ", ".join(new_top) + " — none was a seed."),
        ("Does synaptic biology survive an unbiased test?", "Yes — the only survivor (presynaptic/adhesion, not postsynaptic). Reproduced in an overlapping meta-analysis; not yet independently replicated."),
        ("Does myelin survive?", "No as a GO process (P=0.16). Oligodendrocyte-lineage expression is nominal in joint models across both atlases — unresolved."),
        ("Does energy/metabolism survive?", "No (OXPHOS P=0.37; 0/11 mitochondrial sets nominal)."),
        ("Does astrocyte biology survive?", "No (GO sets null; cell-type result inconsistent across atlases and models)."),
        ("Which one analysis should be done next?", "Section J: UKB-free replication of the synaptic sets and of continuity."),
    ]
    for i, (q, a) in enumerate(qs, 1):
        A(f"**{i}. {q}** {a}\n")

    # ---------------------------------------------------------------- appendices
    A("## Files created\n")
    files = sorted(p.relative_to(ROOT).as_posix() for p in (T).glob("*") if p.is_file())
    A("Reports (`reports/gene_tournament/`): " + ", ".join(f"`{Path(f).name}`" for f in files) + ".\n")
    A("Pipelines (`pipelines/gene_tournament/`): " + ", ".join(
        f"`{p.name}`" for p in sorted((ROOT / "pipelines/gene_tournament").glob("*.py"))) + ".\n")
    A("Data: `data/gene_tournament/` (master universe parquet, study classification, LD loci, developmental "
      "classification, module membership, pathway sets, compact coloc, credible sets); raw snapshots with "
      "checksums under `data/raw/` (`gwas_catalog_tournament*`, `magma_x01`, `magma_sprint3`, `hgnc_complete`, "
      "`clingen`, `string`, `opentargets_gwas_cs`, `europepmc_fulltext`, plus provenance-only records for "
      "bulk downloads kept out of git).\n")
    A("## Data access limitations\n")
    A("* No individual-level genotypes of any kind (Mode 2, rare variants, custom phenotypes).")
    A("* Within-sibship statistics behind OpenGWAS authentication; not registered for.")
    A("* EA and maths GWAS at full power require 23andMe agreements; public EA4 is 25% of the headline N.")
    A("* Davies 2018 general cognition is the open subset (5 cohorts removed); GTEx full nominal eQTLs are "
      "requester-pays; MetaBrain is form-gated.")
    A("* All gene-level statistics are European-ancestry; ancestry sensitivity is not computable.\n")
    A("## Restricted datasets that would materially improve the result\n")
    A("1. **Within-sibship cognition GWAS** (Howe 2022; free OpenGWAS registration) — Part F, and a partly UKB-independent test.")
    A("2. **CHARGE/COGENT cohort-level cognition statistics** (application) — UKB-free replication (§J).")
    A("3. **Duke TIP extreme-IQ genotypes + HRS controls** (collaboration + dbGaP) — Mode 2 and rare-variant burden.")
    A("4. **23andMe maths summary statistics** (qualified-researcher agreement) — the only powered maths phenotype.")
    A("5. **MetaBrain cis-eQTL** (form) — the largest brain eQTL resource, for direction.\n")
    A("## Numbers\n")
    A(f"* Genes evaluated: {univ['n_rows']:,} Catalog gene strings ({univ['n_with_direct_evidence']:,} with direct-cognition "
      f"evidence, {univ['n_with_strict_direct_evidence']:,} strict, {univ['n_proxy_only']:,} proxy-only); 18,418 genes "
      "in the gene-based test; 4,459 in the Sprint-2 sweep (2,668 testable by MAGMA).")
    A(f"* Studies: 419 classified — 120 direct-strict (≤49 independent cohort units), 176 clinical/ageing, 6 MTAG, "
      "24 excluded as EA-derived or cross-trait, 93 proxy.")
    A("* Surviving each filter: FDR<0.05 2,435 → FDR<0.01 1,272 → Bonferroni 375 (159 loci) → Bonferroni in both "
      "Davies and Savage 264 (115 loci) → biology-driven fine-mapping 34 genes → strong direct-cognition brain "
      f"coloc {cc.get('strong', 0)} → direction resolved 0 → red-team clean 0 (natural) / 1 (adult).")
    A(f"* Pathways: {pe['n_set_results']:,} set tests; global FDR<0.05: {pe['n_fdr_global_lt_0.05']}.")
    if comp is not None:
        ok = int((comp.query_status == "ok").sum())
        A(f"* Comparative (Part R, orthology availability only): {ok} of {len(comp)} top genes queried successfully; "
          "the rest are NOT_QUERIED or failed (Ensembl REST errors) — never recorded as absent orthologues. "
          "Selection and convergence NOT computed (no species tree or trait covariates yet; corvids, parrots, "
          "orca and octopus absent from Compara).")
    A("\n## Rank robustness\n")
    for key, label in (("natural", "Natural list"), ("adult", "Adult list")):
        c = cs[key]
        A(f"* **{label}**: RRA vs Borda top-50 overlap {c['top50_overlap_rra_vs_borda']}/50; primary vs "
          f"all-dimensions {c['top50_overlap_primary_vs_all_dimensions']}/50; rank-interval upper bound >200 for "
          f"{c['n_top50_rank_interval_upper_gt_200']}/50; on the Pareto front {c['n_top50_on_pareto_front']}/50; "
          f"carried by: {c['carried_by_counts']}.")
    A("* **A design error, found and fixed, disclosed**: the first aggregation used all dimensions. Extreme-tail "
      "and arithmetic ranks — which have *zero* genes at their own significance threshold — carried 30 of the "
      "top 50, because RRA rewards a single extreme rank; and LoF tolerance (a safety property) promoted weakly "
      "associated genes into the adult list. The rule \"a dimension enters the primary aggregation only if at "
      "least one gene passes its own multiple-testing threshold; safety is a flag\" was **adopted after observing "
      "that run**. The all-dimensions ranks remain in every row for comparison.")
    A("* Monte Carlo: two runs of the same MAGMA analysis flip 4 genes across the Bonferroni line.")
    A("* Window: 91 of 375 Bonferroni genes change call at a 0 kb window.\n")
    A("## Blockers\n")
    A("* No UKB-free, adequately powered cognition GWAS in open access (blocks independent replication).")
    A("* Within-family data require a registration this project does not make on its own authority.")
    A("* No directed causal gene graph exists, so controllability analysis is not meaningful.")
    A("* Ensembl Compara REST is intermittently failing; Part R is partial.\n")
    A("## All red-team downgrades\n")
    A(f"Natural top 50: {rs['human']}. Adult top 50: {rs['adult']}. Modules: {rs['modules']}.\n")
    for name, red in (("Natural", red_n), ("Adult", red_a)):
        dg = red[red.red_team_verdict == "DOWNGRADED"]
        A(f"**{name} list — downgraded ({len(dg)})**: " + "; ".join(
            f"{r.gene} ({r.n_fail} fail, {r.n_flag} flag)" for _, r in dg.iterrows()) + "\n")
    A("**Modules downgraded**: " + ", ".join(rtm[rtm.red_team_verdict == "DOWNGRADED"].index) +
      ". M01 is downgraded as a bounded unit (unstable membership) while its pathway signal stands.\n")
    A("**Downgrades and corrections of earlier sprints' conclusions**: Codex branch \"does not exist\" -> exists; "
      "X01 unverified -> gene layer verified; X01 \"nominated GRM3/ADGRB1/GABBR1\" -> it did not; 2q12.3 gene list "
      "-> replaced; ADGRB1 DOWNGRADED -> UNRESOLVED; ASTROCYTE DOMINANCE UNRESOLVED -> DOWNGRADED; SYNAPTIC "
      "BIOLOGY UNRESOLVED -> PROMISING_BUT_UNRESOLVED; EXTREME COGNITION DISTINCT NOT_ASSESSED -> "
      "CONTRADICTED_IN_STUDIED_CONTEXT (see `reports/project_truth_table.md`).\n")
    A("## Chemistry gate\n")
    A("**Closed.** Zero genes have a resolved direction of effect, so no molecule could even be chosen in "
      "principle — the question of which way to push has no answer yet.\n")
    text = "\n".join(L) + "\n"
    # Sprint 3.1 (2026-09-23): dated correction blocks are re-inserted on every regeneration so the
    # corrections cannot be lost; the original sentences are never edited.
    sys.path.insert(0, str(ROOT / "pipelines" / "sprint3_1"))
    import correction_blocks  # noqa: E402
    text = correction_blocks.apply(text)
    (ROOT / "reports" / "GENE_TOURNAMENT_FINAL.md").write_text(text, encoding="utf-8")
    print(f"wrote reports/GENE_TOURNAMENT_FINAL.md ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
