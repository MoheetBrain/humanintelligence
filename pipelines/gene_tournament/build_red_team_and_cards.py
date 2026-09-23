#!/usr/bin/env python3
"""Sprint 3, Parts P and Q -- kill tests for every top gene and module, then gene cards.

Part P runs ten kill tests per TOP50 gene. Each returns PASS / FAIL / FLAG /
UNDERPOWERED / NOT_COMPUTABLE, and NOT_COMPUTABLE is never scored as a pass. The brief's
instruction is to search for reasons the top gene is NOT causal, so the tests are written
to find failures, and a gene that fails three or more is DOWNGRADED in the output.

Part Q writes one concise card per TOP50 gene answering the brief's fourteen questions,
each answer drawn from a file produced earlier in the sprint -- no field is written from
memory, and an unanswerable field says so.
"""

from __future__ import annotations

import glob
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

OUT = REPO_ROOT / "reports" / "gene_tournament"
DATA = REPO_ROOT / "data" / "gene_tournament"


def load():
    nat = pd.read_csv(OUT / "TOP50_HUMAN_COGNITION_GENES.csv")
    ad = pd.read_csv(OUT / "TOP50_ADULT_MODIFIABLE_GENES.csv")
    b = pd.read_csv(OUT / "direct_cognition_rank.csv")
    ext = pd.read_csv(OUT / "extreme_tail_rank.csv").rename(columns={"GENE": "entrez_id"})
    g = pd.read_csv(OUT / "fine_mapping_support.csv")
    h = pd.read_csv(OUT / "adult_brain_directionality.csv")
    cs = pd.read_csv(DATA / "opentargets_credible_sets.csv").rename(columns={"GENE": "entrez_id"})
    dev = pd.read_parquet(DATA / "developmental_classification.parquet")
    return nat, ad, b, ext, g, h, cs, dev


def strict_ancestry() -> dict[int, set[str]]:
    """Non-European discovery ancestry among a gene's STRICT studies."""
    meta = {json.loads(l)["accession_id"]: json.loads(l) for l in (DATA / "study_metadata.jsonl").open()}
    u = pd.read_parquet(DATA / "master_gene_universe.parquet")
    out = {}
    for eid, studies in zip(pd.to_numeric(u.entrez_id, errors="coerce"), u.strict_studies.fillna("")):
        if pd.isna(eid):
            continue
        anc = set()
        for s in str(studies).split("|"):
            for d in (meta.get(s, {}).get("discovery_ancestry") or []):
                txt = str(d)
                if "European" not in txt and "NR" not in txt:
                    anc.add(txt.split("(")[0].strip()[:40])
        out[int(eid)] = anc
    return out


def kill_tests(top: pd.DataFrame, b, ext, h, cs, dev, anc) -> pd.DataFrame:
    bb = b.set_index("entrez_id"); ee = ext.set_index("entrez_id")
    hh = h.drop_duplicates("entrez_id").set_index("entrez_id"); cc = cs.set_index("entrez_id")
    dd = dev.dropna(subset=["entrez_id"]).copy()
    dd["entrez_id"] = pd.to_numeric(dd.entrez_id, errors="coerce")
    dd = dd.dropna(subset=["entrez_id"]).drop_duplicates("entrez_id").set_index("entrez_id")
    rows = []
    for _, r in top.iterrows():
        e = r.entrez_id
        x = bb.loc[e] if e in bb.index else None
        units = int(x.number_of_independent_cohorts_upper_bound) if x is not None else 0
        t = {}
        t["leave_one_cohort_out"] = ("PASS" if units >= 2 else "FAIL" if units == 1 else
                                     "NOT_COMPUTABLE (no catalog units; MAGMA is one meta-analysis without per-cohort statistics)")
        t["exclude_EA"] = ("FLAG (brain colocalisation only with EA traits)" if hh.get("colocalisation_class", pd.Series()).get(e) == "EA_proxy_only"
                           else "PASS (gene-level test is on cognition; strict tier excludes EA)")
        z, p = (ee.Z_ext.get(e), ee.P_ext.get(e)) if e in ee.index else (np.nan, np.nan)
        t["exclude_UKB"] = ("PASS (UKB-free extreme-IQ sample, P<0.05)" if z > 0 and p < 0.05 else
                            "UNDERPOWERED (UKB-free extreme-IQ sample same sign, P>=0.05)" if z > 0 else
                            "FAIL (UKB-free extreme-IQ sample opposite sign)" if z <= 0 else "NOT_COMPUTABLE")
        a = anc.get(int(e), set())
        t["ancestry_sensitivity"] = (f"PARTIAL (strict non-European study: {sorted(a)[0]})" if a else
                                     "NOT_COMPUTABLE (all gene-level evidence European-ancestry)")
        block_n = int((b["ld_block_r0.2"] == r["ld_block_r0.2"]).sum())
        t["gene_size_LD_matched_null"] = ("FLAG (0 kb window changes the call)" if x is not None and x.window_0kb_agrees == "call_changes" else
                                          f"FLAG (LD block of {block_n} genes: causal gene unresolvable)" if block_n > 10 else "PASS")
        if x is not None and pd.notna(x.gene_Z_savage) and x.gene_Z > 0:
            ratio = x.gene_Z_savage / x.gene_Z
            t["winners_curse"] = (f"PASS (Savage/Davies Z ratio {ratio:.2f}; overlapping samples, so optimistic)" if ratio >= 0.6
                                  else f"FLAG (Savage/Davies Z ratio {ratio:.2f})")
        else:
            t["winners_curse"] = "NOT_COMPUTABLE"
        if e in cc.index and pd.notna(cc.loc[e].n_colocalisations_total) and cc.loc[e].n_colocalisations_total > 0:
            tot = cc.loc[e].n_colocalisations_total; cog = cc.loc[e].n_cognition_coloc or 0
            frac = 1 - cog / tot
            t["pleiotropy_phewas"] = (f"FLAG ({frac:.0%} of {int(tot)} colocalisations are non-cognition traits)"
                                      if frac > 0.9 and tot > 100 else f"PASS ({frac:.0%} non-cognition of {int(tot)})")
        else:
            t["pleiotropy_phewas"] = "NOT_COMPUTABLE (not in Open Targets candidate set)"
        chr_ = x.CHR if x is not None else None
        if chr_ == 6 and x is not None and 25_000_000 <= x.START <= 34_000_000:
            t["pleiotropy_phewas"] += "; MHC region"
        cls = dd.developmental_class.get(e, "UNKNOWN") if e in dd.index else "UNKNOWN"
        t["developmental_only"] = ("FAIL for adult intervention (PRENATAL_DOMINANT)" if cls == "PRENATAL_DOMINANT" else
                                   "FLAG (DEVELOPMENTAL)" if cls == "DEVELOPMENTAL" else
                                   "NOT_COMPUTABLE (UNKNOWN)" if cls == "UNKNOWN" else f"PASS ({cls})")
        t["negative_clinical_evidence"] = "NOT_COMPUTABLE (registry not searched for non-seed genes)"
        t["cohort_dependence_audit"] = (f"FLAG ({units} strict unit(s); 0 confirmed UKB-free)"
                                        if x is not None and x.n_strict_ukb_free_units == 0 else
                                        f"PASS ({units} strict units, {int(x.n_strict_ukb_free_units)} confirmed UKB-free)" if x is not None else "NOT_COMPUTABLE")
        caveat = hh.locus_caveat.get(e) if "locus_caveat" in hh.columns and e in hh.index else None
        if isinstance(caveat, str) and caveat:
            t["pleiotropy_phewas"] += "; FLAG 17q21.31 inversion (coloc not gene-specific)"
        if r.gene in {"APOE", "TOMM40", "APOC1"}:
            t["cohort_dependence_audit"] = "FLAG (APOE region: ageing/Alzheimer's pathology confound)"
        fails = sum(v.startswith("FAIL") for v in t.values())
        fails += sum("FLAG 17q21.31" in v for v in t.values())
        flags = sum(v.startswith("FLAG") for v in t.values())
        nc = sum(v.startswith("NOT_COMPUTABLE") for v in t.values())
        verdict = "DOWNGRADED" if fails + flags >= 3 else "RETAINED_WITH_CAVEATS" if fails + flags else "RETAINED"
        rows.append({"gene": r.gene, "entrez_id": e, "consensus_rank": r.consensus_rank,
                     **t, "n_fail": fails, "n_flag": flags, "n_not_computable": nc,
                     "red_team_verdict": verdict})
    return pd.DataFrame(rows)


def hpa_brain_cells() -> dict[str, str]:
    path = sorted(glob.glob(str(REPO_ROOT / "data/raw/pathway_annotations/*/proteinatlas.tsv.zip")))
    if not path:
        return {}
    with zipfile.ZipFile(path[-1]) as z:
        name = [n for n in z.namelist() if n.endswith(".tsv")][0]
        t = pd.read_csv(z.open(name), sep="\t", usecols=["Gene", "RNA single nuclei brain specificity",
                                                          "RNA single nuclei brain specific nCPM"])
    return {g: f"{s}: {c}" if isinstance(c, str) else str(s)
            for g, s, c in zip(t.Gene, t["RNA single nuclei brain specificity"], t["RNA single nuclei brain specific nCPM"])}


def cards(top: pd.DataFrame, red: pd.DataFrame, b, ext, h, dev, title: str) -> str:
    hpa = hpa_brain_cells()
    bb = b.set_index("entrez_id"); ee = ext.set_index("entrez_id"); rr = red.set_index("entrez_id")
    hh = h.drop_duplicates("entrez_id").set_index("entrez_id")
    brd = pd.read_csv(OUT / "cognitive_breadth.csv").set_index("entrez_id")
    pj = pd.read_csv(OUT / "positive_human_perturbations.csv")
    lines = [f"# {title}", "",
             f"Generated {utc_now()} by `pipelines/gene_tournament/build_red_team_and_cards.py`. Every answer "
             "is drawn from a Sprint-3 artefact; an unanswerable field says so. Nothing here is a target "
             "nomination, a direction of benefit, or a reason to intervene. The chemistry gate is closed.", ""]
    for _, r in top.iterrows():
        e = r.entrez_id; x = bb.loc[e]; k = rr.loc[e]
        hx = hh.loc[e] if e in hh.index else None
        doms = brd.domains.get(e, "") if e in brd.index else ""
        doms = doms if isinstance(doms, str) else ""
        cg = pj[pj.genes.astype(str).str.split("|").apply(lambda gs: r.gene in gs)]
        causal = (f"fine-mapped variant {hx.get('gwas_variant_rsid', '')} colocalised" if hx is not None and isinstance(hx.get("gwas_variant_rsid", None), str)
                  else "not resolved (no direct-cognition brain colocalisation with a shared variant)")
        lines += [f"## {int(r.consensus_rank)}. {r.gene}  ·  rank interval {r.rank_interval}  ·  red team: **{k.red_team_verdict}**", "",
                  f"- **Why here?** MAGMA gene P = {x.gene_P:.2e} (Davies 2018, N=282,014); Savage P = {x.gene_P_savage:.1e}; "
                  f"{int(x.number_of_independent_cohorts_upper_bound)} strict cohort unit(s); rank carried most by *{r.carried_by}*.",
                  f"- **Which phenotype?** {doms.replace('|', ', ') if doms else 'general cognition (MAGMA) only'}",
                  f"- **Extreme-tail evidence?** Z = {ee.Z_ext.get(e, float('nan')):.2f}, P = {ee.P_ext.get(e, float('nan')):.2g} "
                  "(Zabaneh 2018, IQ~170 vs controls; UKB-free; underpowered per gene)",
                  f"- **Causal variant?** {causal}",
                  f"- **Adult brain molecular evidence?** {hx.colocalisation_class if hx is not None else 'not queried'}"
                  + (f" — {hx.molecular_phenotype}" if hx is not None and isinstance(hx.get('molecular_phenotype'), str) else ""),
                  f"- **Direction?** {hx.direction_statement if hx is not None and isinstance(hx.get('direction_statement'), str) else 'unresolved'}"
                  " — never read as 'activate the gene'",
                  f"- **Brain region?** {hx.brain_region if hx is not None and isinstance(hx.get('brain_region'), str) else 'none from colocalisation'}",
                  f"- **Cell type?** {hpa.get(r.gene, 'no HPA single-nucleus brain record')} (HPA v25.1, expression specificity only)",
                  f"- **Module?** {r.module if isinstance(r.module, str) else 'not in FDR<0.01 module set'}",
                  f"- **Developmental / adult?** {r.developmental_class}",
                  f"- **Known perturbations?** " + ("; ".join(f"{c.evidence_id}: {c.effect}" for _, c in cg.iterrows()) or "none in the positive-perturbation table"),
                  f"- **Human safety?** {r.safety_flags if isinstance(r.safety_flags, str) and r.safety_flags else 'no ClinGen HI=3 / pLI>=0.9 flag'}",
                  f"- **Strongest contradiction?** {r.major_counterevidence if isinstance(r.major_counterevidence, str) and r.major_counterevidence else 'none recorded'}",
                  f"- **Next computation?** {r.next_kill_test}", ""]
    return "\n".join(lines)


def module_kill_tests(mods: pd.DataFrame) -> pd.DataFrame:
    out = []
    for _, m in mods.iterrows():
        t = {"bootstrap_stability": "PASS" if m.bootstrap_stability >= 0.6 else "FLAG",
             "leave_study_out_savage": "PASS" if m.leave_study_out_best_jaccard_savage >= 0.3 else "FLAG",
             "cross_method_agreement": "FLAG (partition ARI 0.19-0.24)",
             "more_tail_engaged_than_other_cognition_genes": ("PASS" if m.tail_bonf < 0.05 else
                                                              "FLAG (nominal only)" if m.tail_p < 0.05 else "FAIL"),
             "label_enrichment_after_conditioning": "PASS" if m.label_best_enrichment_P_conditioned < 0.05 else "FAIL",
             "artefact_screen": "FAIL (gene-family cluster)" if "olfactory" in str(m.pathway_labels).lower() else "PASS"}
        n_bad = sum(v.startswith(("FAIL", "FLAG")) for v in t.values())
        out.append({"module": m.module, "labels": str(m.pathway_labels)[:120], **t,
                    "red_team_verdict": "DOWNGRADED" if n_bad >= 4 else "RETAINED_WITH_CAVEATS" if n_bad else "RETAINED"})
    return pd.DataFrame(out)


def main() -> int:
    nat, ad, b, ext, g, h, cs, dev = load()
    anc = strict_ancestry()
    red_nat = kill_tests(nat, b, ext, h, cs, dev, anc)
    red_ad = kill_tests(ad, b, ext, h, cs, dev, anc)
    red_nat.to_csv(OUT / "red_team_top50_human.csv", index=False)
    red_ad.to_csv(OUT / "red_team_top50_adult.csv", index=False)
    mods = pd.read_csv(OUT / "biological_modules.csv")
    te = pd.read_csv(OUT / "module_tail_engagement.csv").set_index("module")
    mods["tail_p"] = mods.module.map(te.MWU_P_more_tail_engaged)
    mods["tail_bonf"] = mods.module.map(te.bonferroni)
    mk = module_kill_tests(mods)
    mk.to_csv(OUT / "red_team_modules.csv", index=False)
    (OUT / "GENE_CARDS_TOP50_HUMAN.md").write_text(cards(nat, red_nat, b, ext, h, dev,
                                                         "Gene cards — Top 50 human cognition genes"))
    # Sprint 3.1 (2026-09-23): the C9 relabel block is re-inserted on every regeneration.
    sys.path.insert(0, str(REPO_ROOT / "pipelines" / "sprint3_1"))
    import correction_blocks  # noqa: E402
    (OUT / "GENE_CARDS_TOP50_ADULT.md").write_text(correction_blocks.apply_cards(
        cards(ad, red_ad, b, ext, h, dev, "Gene cards — Top 50 adult-modifiable candidates")))
    s = {"built_at": utc_now(),
         "human": red_nat.red_team_verdict.value_counts().to_dict(),
         "adult": red_ad.red_team_verdict.value_counts().to_dict(),
         "modules": mk.red_team_verdict.value_counts().to_dict(),
         "test_failure_counts_human": {c: int(red_nat[c].str.startswith(("FAIL", "FLAG")).sum())
                                       for c in red_nat.columns if c not in ("gene", "entrez_id", "consensus_rank", "n_fail", "n_flag", "n_not_computable", "red_team_verdict")}}
    (OUT / "red_team_summary.json").write_text(json.dumps(s, indent=2) + "\n")
    print(json.dumps(s, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
