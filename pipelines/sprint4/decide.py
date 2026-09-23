#!/usr/bin/env python3
"""Sprint 4 — assemble the gates, the survivor table, the negative results and the ONE decision.

Reads every Gate output, applies only frozen rules (via classify.py / common.load_frozen) and writes:
  data/sprint4/power_calibration_replicates.csv, data/sprint4/power_calibration_summary.json
  reports/sprint4/within_family_power_calibration.json      (pre-data calibration; Gate A status)
  reports/sprint4/genc_independent_synaptic_sets.csv         (Gate B set classes)
  reports/sprint4/direct_effect_survivors.csv
  reports/sprint4/negative_results.csv
  reports/sprint4/decision.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify as K  # noqa: E402
import common as C  # noqa: E402

CAL_DIRS = [C.WORK / "calibration", C.WORK / "calibration_rev"]
F_GC_LOWER = 0.752
PRIMARY_FOCUS = "joint_brain_gene_x_tissue_p1e-3"
N_GC_GRID = 9997


def calibration(frozen: dict) -> tuple[pd.DataFrame, dict]:
    frames = []
    for d in CAL_DIRS:
        for p in sorted(d.glob("*.syngo.gsa.out")):
            tag = p.name.replace(".syngo.gsa.out", "")
            n = int(tag.split("_")[0][1:])
            f = float(tag.split("_")[1][1:])
            k = int(tag.split("_")[2][1:])
            t = pd.read_csv(p, sep=r"\s+", comment="#")
            t = t[t.VARIABLE.isin(C.FROZEN_SETS)]
            frames.append(pd.DataFrame({"n": n, "f": f, "rep": k, "set": t.VARIABLE, "beta": t.BETA,
                                        "se": t.SE, "P": t.P}))
    reps = pd.concat(frames, ignore_index=True).drop_duplicates(["n", "f", "rep", "set"]) if frames else \
        pd.DataFrame(columns=["n", "f", "rep", "set", "beta", "se", "P"])
    reps.to_csv(C.DATA / "power_calibration_replicates.csv", index=False, float_format="%.6g")
    th = K.thresholds(frozen)
    summ = {}
    for (n, f, s), g in reps.groupby(["n", "f", "set"]):
        e = K.expected_distribution(g.beta, g.P, th["q_low"], th["alpha"])
        e["power_bonferroni6"] = float((g.P < 0.05 / 6).mean())
        summ.setdefault(s, {})[f"n{n}_f{f:g}"] = e
    compact = {s: {"f1": v.get("n4999_f1", {}).get("median"), "f078": v.get("n4999_f0.78", {}).get("median"),
                   "power_f078": v.get("n4999_f0.78", {}).get("power"),
                   "note": "pre-data Davies-subsampled expectation at N_eff 4,999 (sibling pairs)"}
               for s, v in summ.items()}
    out = {"computed_at": C.utc_now(), "method": frozen["rules"]["gate_a"]["calibration"]["method"],
           "source": "Davies 2018 (pre-data); post-data Howe-population calibration pending Gate A data",
           "replicates_completed": {f"n{n}_f{f:g}": int(g.rep.nunique()) for (n, f), g in reps.groupby(["n", "f"])},
           "replicates_frozen": frozen["rules"]["gate_a"]["calibration"]["replicates_per_scenario"],
           "per_set": summ, "per_set_compact": compact}
    (C.DATA / "power_calibration_summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return reps, out


def gate_b_sets(frozen: dict, cal: dict) -> pd.DataFrame:
    raw = pd.read_csv(C.DATA / "genc_set_results_raw.csv")
    rows = []
    for r in raw.itertuples():
        exp_lo = cal["per_set"].get(r.set, {}).get(f"n{N_GC_GRID}_f{F_GC_LOWER:g}", {})
        exp_up = cal["per_set"].get(r.set, {}).get(f"n{N_GC_GRID}_f1", {})
        cls = K.classify_set(r.beta, r.P, exp_lo, frozen, supported_label="INDEPENDENT_SUPPORT")
        rows.append({"phenotype": r.phenotype, "primary_phenotype": r.primary, "spec": r.spec, "set": r.set,
                     "ngenes": r.ngenes, "beta": r.beta, "se": r.se, "P": r.P,
                     "bonferroni6_significant": bool(r.P < 0.05 / 6),
                     "phenotype_mismatch": "EXECUTIVE_FUNCTION (trail making) vs GENERAL_COGNITION discovery",
                     "cohort": "NIHR BioResource Genes & Cognition, N=9,932 (G&C-only file; UKB excluded)",
                     "expected_beta_median_f_lower": exp_lo.get("median"), "expected_q025_f_lower": exp_lo.get("q_low"),
                     "power_f_lower": exp_lo.get("power"), "expected_beta_median_f1_upper_bound": exp_up.get("median"),
                     "power_f1_upper_bound": exp_up.get("power"), "calibration_reps": exp_lo.get("n_reps", 0),
                     "classification": cls["class"], "subtype": cls["subtype"],
                     "can_drive_pivot": cls["can_drive_pivot"]})
    t = pd.DataFrame(rows)
    t.to_csv(C.OUT / "genc_independent_synaptic_sets.csv", index=False, float_format="%.5g")
    return t


def survivors(frozen: dict) -> pd.DataFrame:
    gc = pd.read_csv(C.DATA / "gate_c_loci.csv")
    lb = pd.read_csv(C.OUT / "genc_independent_loci.csv").set_index("locus_id")
    wf = pd.read_csv(C.OUT / "within_family_locus_concordance.csv").set_index("locus_id")
    dev = pd.read_parquet(C.REPO_ROOT / "data/gene_tournament/developmental_classification.parquet",
                          columns=["gene_symbol", "developmental_class"]).drop_duplicates("gene_symbol").set_index("gene_symbol")
    fm = pd.read_parquet(C.OUT / "locus_finemapping.parquet") if (C.OUT / "locus_finemapping.parquet").exists() else pd.DataFrame()
    dr = pd.read_csv(C.OUT / "directionality_resolution.csv") if (C.OUT / "directionality_resolution.csv").exists() else pd.DataFrame()
    coloc = pd.read_parquet(C.OUT / "adult_brain_susie_coloc.parquet") if (C.OUT / "adult_brain_susie_coloc.parquet").exists() else pd.DataFrame()
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    diag = {d["locus_id"]: d for d in json.loads((C.DATA / "finemap_diagnostics.json").read_text())["loci"]} \
        if (C.DATA / "finemap_diagnostics.json").exists() else {}
    loci = {l["locus_id"]: l for l in frozen["loci"]}
    rows = []
    for r in gc.itertuples():
        L = loci[r.locus_id]
        b = lb.loc[r.locus_id]
        genes = [g["symbol"] for g in L["bonferroni_genes"]]
        top = L["top_gene"]
        ot = fm[(fm.locus_id == r.locus_id) & fm.source.str.startswith("Open")] if len(fm) else pd.DataFrame()
        ss = fm[(fm.locus_id == r.locus_id) & fm.source.str.startswith("SuSiE")] if len(fm) else pd.DataFrame()
        l2g = ot.top_l2g_gene.value_counts().to_dict() if len(ot) else {}
        pos_driven = ot.positional_driven.astype(str).eq("True").mean() if len(ot) else float("nan")
        cl = coloc[coloc.locus_id == r.locus_id] if len(coloc) else pd.DataFrame()
        strong = cl[cl["PP.H4"] >= 0.8] if len(cl) else pd.DataFrame()
        strong_genes = sorted({sym.get(g, g) for g in strong.gene_id}) if len(strong) else []
        drl = dr[dr.locus_id == r.locus_id] if len(dr) else pd.DataFrame()
        resolved = drl[drl.label == "DIRECTION_RESOLVED"].gene.tolist() if len(drl) else []
        role = r.role
        carried = []
        if "SURVIVOR_B" in role:
            carried.append(f"B: G&C_SUPPORTED (TMA aligned one-sided P={b.TMA_one_sided_P:.2g}; "
                           f"BH q among testable loci={b.gate_b_FDR_primary:.2g})")
        if "STRESS_TEST" in role:
            carried.append("prespecified STRESS_TEST (not a survivor unless A/B/C holds)")
        if "POSITIVE_CONTROL" in role:
            carried.append("positive control (published G&C replication; prenatal-dominant)")
        if "SPRINT3_1" in role:
            carried.append("Sprint-3.1 direction candidate (RPS26 on independent adult cohorts)")
        wrong = []
        if "SURVIVOR_B" in role and b.gate_b_FDR_primary > 0.05:
            wrong.append("nominal support only: ~14.5 of 33 G&C_SUPPORTED loci expected by chance")
        wrong.append("G&C phenotype is executive function (trail making), not general cognition")
        if len(ot) and pos_driven >= 0.5:
            wrong.append("locus-to-gene is mainly positional (L2G distance/gene-density features)")
        if len(genes) > 3:
            wrong.append(f"multi-gene LD locus ({len(genes)} Bonferroni genes)")
        if diag.get(r.locus_id, {}).get("ld_mismatch_flag"):
            wrong.append("SuSiE LD-mismatch flag")
        wrong.append("Gate A (direct effect) NOT_TESTABLE: population stratification / indirect effects not excluded")
        rows.append({
            "gene": top, "locus": r.locus_id, "locus_bonferroni_genes": ";".join(genes), "chr": L["chr"],
            "lead_snp": L["lead_snp"], "role": role,
            "gate_a_result": wf.loc[r.locus_id, "classification"] if r.locus_id in wf.index else "NOT_TESTABLE",
            "gate_b_result": b.gate_b_locus_class, "gate_b_TMA_aligned_z": b.TMA_aligned_z,
            "gate_b_TMA_one_sided_P": b.TMA_one_sided_P, "gate_b_FDR": b.gate_b_FDR_primary,
            "cohort_independence": "G&C: UKB-free by recruitment (explicit no-overlap statement not found in source); "
                                   "Gate A would be UKB-overlapping (8,061 UKB siblings)",
            "adult_developmental_class": dev.loc[top, "developmental_class"] if top in dev.index else "UNKNOWN",
            "fine_mapping_status": (f"OT sets: {len(ot)} (top L2G: {', '.join(f'{k}×{v}' for k, v in list(l2g.items())[:3])}; "
                                    f"positional-driven {pos_driven:.0%}); SuSiE sensitivity: "
                                    f"{ss.credible_set.nunique() if len(ss) else 0} CS"
                                    + (f", s={diag[r.locus_id]['estimate_s_rss']:.3f}" if r.locus_id in diag and diag[r.locus_id].get('estimate_s_rss') is not None else "")),
            "brain_coloc_status": (f"{len(strong)} strong adult-brain coloc pairs; genes: {', '.join(strong_genes) or 'none'}"
                                   if len(cl) else "no adult-brain QTL data returned"),
            "direction_resolved_genes": ";".join(resolved) or "none",
            "reason_carried_forward": " | ".join(carried),
            "reason_could_still_be_wrong": "; ".join(wrong)})
    t = pd.DataFrame(rows)
    t.to_csv(C.OUT / "direct_effect_survivors.csv", index=False, float_format="%.4g")
    return t


def negative_results(sets_b: pd.DataFrame, surv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    add = lambda cat, item, detail, status: rows.append({"category": cat, "item": item, "detail": detail,  # noqa: E731
                                                         "status": status})
    for s in C.FROZEN_SETS:
        add("frozen set — direct-family test", s, "Gate A within-sibship data not accessible (OPENGWAS_JWT absent)",
            "NOT_TESTABLE (blocked by access; not evidence of absence)")
    b = sets_b[(sets_b.primary_phenotype) & (sets_b.spec == "frozen_sprint3_spec")]
    for r in b.itertuples():
        if r.classification != "INDEPENDENT_SUPPORT":
            add("frozen set — independent G&C test (TMA)", r.set,
                f"beta={r.beta:.3f}, P={r.P:.3g}; power at f_lower={r.power_f_lower if r.power_f_lower is not None else 'NA'}",
                f"{r.classification} {r.subtype}".strip())
    lb = pd.read_csv(C.OUT / "genc_independent_loci.csv")
    for r in lb.itertuples():
        if r.gate_b_locus_class == "NOT_SUPPORTED_AT_THIS_POWER":
            add("locus — no independent G&C support", f"{r.locus_id} ({r.top_gene})",
                f"TMA aligned z={r.TMA_aligned_z:.2f}" + (" (opposite direction)" if r.TMA_aligned_z < 0 else ""),
                "NOT_SUPPORTED_AT_THIS_POWER" + ("; DISCORDANT_SIGN" if r.TMA_aligned_z < 0 else ""))
        elif r.gate_b_locus_class == "NOT_TESTABLE":
            add("locus — G&C lookup not testable", f"{r.locus_id} ({r.top_gene})", str(r.TMA_status),
                "NOT_TESTABLE")
        if str(r.TMA_status) == "UNRESOLVED_HARMONISATION":
            add("unresolved allele harmonisation", f"{r.locus_id} ({r.top_gene})",
                f"palindromic lead {r.lead_snp} with allele frequency 0.40-0.60", "UNRESOLVED_HARMONISATION")
    add("locus — direct-effect (within-family) support", "all 159 loci", "Gate A data not accessible",
        "NOT_TESTABLE (blocked by access)")
    coloc = pd.read_parquet(C.OUT / "adult_brain_susie_coloc.parquet") if (C.OUT / "adult_brain_susie_coloc.parquet").exists() else pd.DataFrame()
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    if len(coloc):
        for lid, g in coloc.groupby("locus_id"):
            if (g["PP.H4"] < 0.5).all():
                add("credible signal without adult-brain QTL colocalisation", lid,
                    f"{len(g)} gene x dataset pairs tested; max PP.H4={g['PP.H4'].max():.2f}", "NO_COLOCALISATION")
            multi = sorted({sym.get(x, x) for x in g[g["PP.H4"] >= 0.8].gene_id})
            if len(multi) > 1:
                add("same signal colocalises with multiple genes", lid, ", ".join(multi), "GENE_AMBIGUOUS")
        for r in coloc[coloc["PP.H3"] >= 0.8].to_dict("records"):
            add("GWAS/QTL pair with distinct causal variants (PP.H3>=0.8)",
                f"{r['locus_id']} {sym.get(r['gene_id'], r['gene_id'])} {r['dataset_id']}",
                f"PP.H3={r['PP.H3']:.2f}, PP.H4={r['PP.H4']:.2f}", "DOES_NOT_COLOCALISE")
    dr = pd.read_csv(C.OUT / "directionality_resolution.csv") if (C.OUT / "directionality_resolution.csv").exists() else pd.DataFrame()
    for r in dr.itertuples() if len(dr) else []:
        if r.rows_n_rows >= 2 and r.rows_row_agreement < 0.8:
            add("QTL directions disagree across datasets/tissues", r.gene,
                f"{r.rows_n_rows} strong rows, {r.rows_row_agreement:.0%} agreement", "DIRECTION_INCONSISTENT")
        if r.label == "RESOLVED_ON_ROWS_ONLY_NOT_ROBUST":
            add("direction resolved on rows but not on independent cohorts", r.gene,
                f"{r.rows_n_cohort_units} cohort units", "NOT_ROBUST")
    for r in surv.itertuples():
        if str(r.adult_developmental_class) in ("PRENATAL_DOMINANT", "DEVELOPMENTAL"):
            add("development-dominant expression (survivor/stress/control)", f"{r.gene} ({r.locus})",
                str(r.adult_developmental_class), "DEVELOPMENTAL_TIMING (expression; function not assessed)")
    jg = C.OUT / "joint_gene_tissue_finemapping.csv"
    if jg.exists():
        j = pd.read_csv(jg)
        for r in j[j.status.astype(str).str.upper() == "BLOCKED"].drop_duplicates(["method"]).itertuples():
            add("analysis blocked", f"joint gene-tissue fine-mapping ({r.method})", str(r.blocker)[:300], "BLOCKED")
    add("analysis blocked", "MetaBrain eQTL", "not publicly downloadable without an access request; not used",
        "NOT_ACCESSIBLE")
    add("analysis excluded by rule", "BrainSeq, Walker 2019, Aygün 2021, Jerber 2021, Schwartzentruber 2018 QTLs",
        "non-adult samples (prenatal/childhood/iPSC); excluded from direction by the frozen adult rule", "EXCLUDED")
    t = pd.DataFrame(rows)
    t.to_csv(C.OUT / "negative_results.csv", index=False)
    return t


def chemistry_gate(surv: pd.DataFrame) -> dict:
    """Frozen: CLOSED unless one gene has ALL of independent support, credible locus-to-gene evidence,
    adult-brain molecular evidence, consistent direction and no disqualifying safety/pleiotropy signal."""
    dr = pd.read_csv(C.OUT / "directionality_resolution.csv") if (C.OUT / "directionality_resolution.csv").exists() else pd.DataFrame()
    fm = pd.read_parquet(C.OUT / "locus_finemapping.parquet") if (C.OUT / "locus_finemapping.parquet").exists() else pd.DataFrame()
    jg = pd.read_csv(C.OUT / "joint_gene_tissue_finemapping.csv") if (C.OUT / "joint_gene_tissue_finemapping.csv").exists() else pd.DataFrame()
    cands = []
    for r in dr.itertuples() if len(dr) else []:
        if r.label != "DIRECTION_RESOLVED":
            continue
        s = surv[surv.locus == r.locus_id]
        indep = bool(len(s) and (s.gate_b_result == "G&C_SUPPORTED").any())
        ot = fm[(fm.locus_id == r.locus_id) & fm.source.str.startswith("Open")] if len(fm) else pd.DataFrame()
        l2g_bio = bool(len(ot) and ((ot.top_l2g_gene == r.gene) & ot.positional_driven.astype(str).ne("True")).any())
        jgf = False
        if len(jg) and "gene_pip" in jg:
            # primary FOCUS configuration: all adult-brain gene x tissue models jointly; gene PIP = sum over tissues
            g = jg[(jg.gene == r.gene) & jg.status.astype(str).str.upper().eq("RUN")
                   & jg.analysis_config.astype(str).eq(PRIMARY_FOCUS)]
            jgf = bool(len(g) and pd.to_numeric(g.gene_pip, errors="coerce").sum() >= 0.5)
        cands.append({"gene": r.gene, "locus": r.locus_id, "independent_support": indep,
                      "credible_locus_to_gene": l2g_bio or jgf,
                      "credible_l2g_basis": ("non-positional L2G driver" if l2g_bio else "") +
                                            (" joint gene-tissue PIP>=0.5" if jgf else ""),
                      "adult_brain_molecular": True, "consistent_direction": True,
                      "safety_pleiotropy_cleared": False,
                      "safety_note": "not cleared computationally; any candidate needs a manual pleiotropy/safety review"})
    four = [c for c in cands if c["independent_support"] and c["credible_locus_to_gene"]]
    return {"status": "CLOSED", "direction_resolved_genes": cands,
            "genes_meeting_all_criteria_except_safety": [c["gene"] for c in four],
            "label_if_all_five_met": "CAUSAL_TARGET_ADJUDICATION_CANDIDATE",
            "reason": ("No gene meets all five frozen criteria (independent support, credible locus-to-gene evidence, "
                       "adult-brain molecular evidence, consistent direction, no disqualifying safety/pleiotropy "
                       "signal); safety/pleiotropy is never cleared automatically.")}


def power_findings(cal: dict, frozen: dict) -> dict:
    """What the frozen pre-data calibration implies for Gate A once it is unlocked."""
    import numpy as _np
    from scipy import stats as _st
    ps = cal["per_set"]
    set_power = {s: {k: round(v.get("power", float("nan")), 3) for k, v in d.items()} for s, d in ps.items()}
    loci = pd.DataFrame(frozen["loci"])
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Zscore"]).Zscore.to_numpy()[::50]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import loci_tools as LT
    mu = _np.clip(LT.tweedie(davies, _np.abs(loci.lead_davies_z.to_numpy())), 0, None)
    out = {"set_level_power_by_scenario": set_power}
    for n in (4999, 9997):
        pc = _st.norm.cdf(mu * 0.78 * _np.sqrt(n / C.DAVIES_N))
        k = len(pc)
        # power of a one-sided binomial sign test at alpha 0.05 over all loci, expected concordance pc
        crit = int(_st.binom.ppf(0.95, k, 0.5)) + 1
        sims = _np.random.default_rng(1).binomial(1, pc, size=(4000, k)).sum(axis=1)
        out[f"locus_sign_test_n{n}_f0.78"] = {"expected_concordance": float(pc.mean()),
                                               "power": float((sims >= crit).mean())}
    out["reading"] = ("Set-level enrichment has <=12.5% power at within-family N_eff 5-10k even if the signal "
                      "were fully direct, so a set-level Gate A cannot be decisive; the locus-level sign test is "
                      "well powered and is what unlocking Gate A would actually decide.")
    return out


def main() -> int:
    frozen = C.load_frozen()
    reps, cal = calibration(frozen)
    import subprocess
    for cmd in ("fetch", "analyse"):   # Gate A: records the access boundary, writes NOT_TESTABLE outputs
        subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "gate_a_within_family.py"), cmd],
                       check=False, capture_output=True, text=True)
    sets_b = gate_b_sets(frozen, cal)
    surv = survivors(frozen)
    neg = negative_results(sets_b, surv)
    # Gate A status
    wf_sets = pd.read_csv(C.OUT / "within_family_synaptic_sets.csv")
    gate_a_all_nt = bool((wf_sets.classification == K.NOT_TESTABLE).all())
    b = sets_b[(sets_b.primary_phenotype) & (sets_b.spec == "frozen_sprint3_spec")]
    b_beyond = int(((b.classification == "INCONSISTENT") & (b.subtype == "BEYOND_EXPECTED_NOISE")).sum())
    b_power_ok = bool((b.power_f_lower.fillna(0) >= 0.5).all())
    pivot_b = b_beyond >= 3 and b_power_ok
    pivot_a = False  # Gate A untestable
    gb = json.loads((C.DATA / "gate_b_summary.json").read_text())
    locus_binom = gb["loci"]["binomial_P_one_sided"]
    if pivot_a and pivot_b:
        decision = "STOP_CURRENT_HYPOTHESIS"
    elif pivot_a or pivot_b:
        decision = "PIVOT"
    elif gate_a_all_nt:
        decision = "RETRY"
    else:
        decision = "UNDETERMINED"
    chem = chemistry_gate(surv)
    dec = {
        "decided_at": C.utc_now(), "code_commit": C.git_head(),
        "primary_decision": decision,
        "precedence_applied": frozen["rules"]["decision"]["precedence"],
        "why": {
            "STOP_CURRENT_HYPOTHESIS": "not met — requires the PIVOT condition in BOTH gates; Gate A untestable",
            "PIVOT": f"not met — Gate B: {b_beyond} of 6 frozen sets INCONSISTENT beyond noise "
                     f"(needs >=3 with simulated power >=0.5 at f_gc_lower={F_GC_LOWER}); Gate A untestable",
            "RETRY": "MET — all six frozen sets are NOT_TESTABLE in Gate A because the within-sibship data need an "
                     "OpenGWAS JWT (access), which ranks above CONTINUE/ESCALATE in the frozen precedence",
            "CONTINUE": "cannot be assessed — requires >=1 set DIRECT_EFFECT_SUPPORTED in Gate A",
            "ESCALATE": "not assigned — superseded by RETRY in the frozen precedence",
        },
        "gate_a": {"status": "NOT_TESTABLE", "reason": "OPENGWAS_JWT absent",
                   "sets": wf_sets[["set", "classification"]].to_dict(orient="records")},
        "gate_b": {"set_classes_primary": b[["set", "classification", "subtype", "P", "power_f_lower"]].to_dict(orient="records"),
                   "locus_sign_concordance": {"concordant": gb["loci"]["n_concordant_primary"],
                                              "testable": gb["loci"]["n_testable_primary"], "binomial_P": locus_binom},
                   "n_loci_GC_SUPPORTED": gb["loci"]["n_GC_SUPPORTED"],
                   "positive_control": gb["positive_control"]["status"]},
        "survivors": {"n_gate_c_loci": int(len(surv)), "roles": surv.role.value_counts().to_dict()},
        "chemistry_gate": chem,
        "calibration_findings": power_findings(cal, frozen),
        "minimal_user_action_to_unlock_gate_a": json.loads((C.DATA / "gate_a_access.json").read_text()).get(
            "minimal_user_action") if (C.DATA / "gate_a_access.json").exists() else None,
    }
    (C.OUT / "decision.json").write_text(json.dumps(dec, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: dec[k] for k in ("primary_decision", "why")}, indent=1))
    print(sets_b[(sets_b.primary_phenotype) & (sets_b.spec == "frozen_sprint3_spec")][
        ["set", "beta", "P", "expected_beta_median_f_lower", "expected_q025_f_lower", "power_f_lower",
         "classification", "subtype", "calibration_reps"]].to_string(index=False))
    print(neg.category.value_counts().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
