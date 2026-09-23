#!/usr/bin/env python3
"""Sprint 3.1 — collect the recon MAGMA runs into the two report tables.

``reports/sprint3_1/pre_vs_post_joint_tests.csv``
    Every marginal (one-sided) recon-set result and every joint/contrast model (two-sided),
    per conditioning specification. Joint models are matched by their variable SET, because
    MAGMA renumbers models in its own order.

``reports/sprint3_1/pathway_conditioning_sensitivity.csv``
    Theme x specification matrix: the pre-chosen anchor set's beta/SE/P and global-FDR q, the
    number of theme-family sets at global FDR < 0.05, and the six frozen Sprint-3 sets.

Nothing here re-thresholds a Sprint-3 result; conclusions are written by the report script.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_inputs as BI  # noqa: E402
import run_recon_magma as RR  # noqa: E402

WORK = RR.WORK
OUT = REPO / "reports" / "sprint3_1"
SPEC_ORDER = ["A", "B", "C", "D", "E", "E2", "D_S3"]
SPEC_LABEL = {"A": "MAGMA internal covariates only", "B": "A + annotation density", "C": "A + LOEUF",
              "D": "A + annotation density + LOEUF (Sprint-3 covariates, full universe)",
              "E": "D + neuronal expression (level + neuron-vs-glia specificity)",
              "E2": "E + GTEx adult-brain expression", "D_S3": "exact Sprint-3 run (17,069-gene universe)"}
FROZEN6 = ["GO_0042734", "GO_0099560", "GO_0099056", "GO_0099508", "GO_0045202", "SYNGO_synprocess"]
LANDSCAPE = ["syngo", "go_bp_prop", "go_cc_prop", "go_mf_prop", "reactome"]
CONTRASTS = {  # model variable set -> (contrast variable, meaning)
    frozenset({"PRE_ONLY", "PRE_AND_POST", "PRE_OR_POST"}): ("PRE_ONLY", "pre-only minus post-only genes"),
    frozenset({"POST_ONLY", "PRE_AND_POST", "PRE_OR_POST"}): ("POST_ONLY", "post-only minus pre-only genes"),
    frozenset({"PREMEMB_ONLY", "PREPOSTMEMB_BOTH", "PREPOSTMEMB_UNION"}):
        ("PREMEMB_ONLY", "presynaptic-membrane-only minus postsynaptic-membrane-only genes"),
    frozenset({"PREPROC_ONLY", "PREPOSTPROC_BOTH", "PREPOSTPROC_UNION"}):
        ("PREPROC_ONLY", "presynaptic-process-only minus postsynaptic-process-only genes"),
    frozenset({"RELEASE_ONLY", "RELEASE_AND_ORG", "RELEASE_OR_ORG"}):
        ("RELEASE_ONLY", "release-machinery-only minus organisation/trafficking-only genes"),
}


def read_gsa(path: Path) -> pd.DataFrame:
    rows = [ln.split() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]
    header, body = rows[0], rows[1:]
    ncol = len(header)
    frame = pd.DataFrame([r[:ncol] for r in body], columns=header)
    if "FULL_NAME" in header:  # abbreviated names
        frame["VARIABLE"] = [r[ncol - 1] if len(r) >= ncol else r[0] for r in body]
    for c in ("NGENES", "BETA", "BETA_STD", "SE", "P", "MODEL"):
        if c in frame:
            frame[c] = pd.to_numeric(frame[c], errors="coerce")
    return frame


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    order = np.argsort(p)
    q = p[order] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1)
    return out


def joint_table() -> pd.DataFrame:
    models = {frozenset(m.split()): m for m in RR.JOINT_MODELS}
    frames = []
    for spec in SPEC_ORDER:
        path = WORK / f"recon_joint__{spec}.gsa.out"
        if not path.exists():
            continue
        g = read_gsa(path)
        for mid, grp in g.groupby("MODEL"):
            key = frozenset(grp.VARIABLE)
            label = models.get(key, " ".join(sorted(key)))
            contrast = CONTRASTS.get(key)
            for r in grp.itertuples():
                frames.append({
                    "spec": spec, "spec_label": SPEC_LABEL[spec], "analysis": "joint_two_sided",
                    "model": label, "variable": r.VARIABLE, "ngenes": r.NGENES, "beta": r.BETA,
                    "se": r.SE, "P": r.P,
                    "is_contrast_term": bool(contrast and contrast[0] == r.VARIABLE),
                    "interpretation": (contrast[1] if contrast and contrast[0] == r.VARIABLE else
                                       f"{r.VARIABLE} conditional on the other set(s) in the model")})
        marg = read_gsa(WORK / f"recon__{spec}.gsa.out")
        for r in marg.itertuples():
            frames.append({"spec": spec, "spec_label": SPEC_LABEL[spec], "analysis": "marginal_one_sided",
                           "model": r.VARIABLE, "variable": r.VARIABLE, "ngenes": r.NGENES, "beta": r.BETA,
                           "se": r.SE, "P": r.P, "is_contrast_term": False,
                           "interpretation": "set vs all other genes (competitive, one-sided)"})
    out = pd.DataFrame(frames)
    out["z"] = out.beta / out.se
    return out


def marginal_difference(tab: pd.DataFrame, a: str, b: str, spec: str) -> dict:
    """Naive difference of two marginal betas ignoring their covariance (reported only as a
    contrast to the proper joint-model test, never as the test)."""
    m = tab[(tab.spec == spec) & (tab.analysis == "marginal_one_sided")].set_index("variable")
    d = m.loc[a, "beta"] - m.loc[b, "beta"]
    se = float(np.hypot(m.loc[a, "se"], m.loc[b, "se"]))
    return {"diff": float(d), "se_naive": se, "P_naive_two_sided": float(2 * stats.norm.sf(abs(d / se)))}


def landscape(spec: str) -> pd.DataFrame:
    frames = []
    for coll in LANDSCAPE:
        path = WORK / f"{coll}__{spec}.gsa.out"
        if not path.exists():
            continue
        g = read_gsa(path)
        g["collection"] = coll
        frames.append(g[["VARIABLE", "NGENES", "BETA", "SE", "P", "collection"]])
    land = pd.concat(frames, ignore_index=True)
    land["q_global"] = bh(land.P.to_numpy())
    return land


def names_lookup() -> dict[str, str]:
    names = {}
    for p in [REPO / "data/gene_tournament/pathway_sets/syngo.setannot.names.tsv",
              REPO / "data/gene_tournament/pathway_sets/reactome_human.setannot.names.tsv",
              *(REPO / "data/sprint3_1").glob("go_*_prop.setannot.names.tsv")]:
        t = pd.read_csv(p, sep="\t", dtype=str)
        names.update(dict(zip(t.set_name, t.description)))
    return names


def sensitivity_matrix() -> tuple[pd.DataFrame, dict]:
    names = names_lookup()
    rows, extra = [], {}
    for spec in [s for s in SPEC_ORDER if s != "D_S3"]:
        land = landscape(spec)
        land["NAME"] = land.VARIABLE.map(names).fillna("")
        extra[spec] = {"n_sets": int(len(land)), "n_q_lt_0.05": int((land.q_global < 0.05).sum())}
        for theme, (src, sid) in BI.THEME_ANCHORS.items():
            coll = src
            hit = land[(land.collection == coll) & (land.VARIABLE == sid)]
            fam_rx = BI.THEME_REGEX.get(theme)
            fam = land[land.NAME.str.contains(fam_rx, case=False, regex=True)] if fam_rx else land.iloc[0:0]
            best = fam.sort_values("P").head(1)
            rows.append({
                "theme": theme, "spec": spec, "spec_label": SPEC_LABEL[spec], "anchor_set": sid,
                "anchor_collection": coll, "anchor_name": names.get(sid, ""),
                "anchor_ngenes": int(hit.NGENES.iloc[0]) if len(hit) else np.nan,
                "anchor_beta": float(hit.BETA.iloc[0]) if len(hit) else np.nan,
                "anchor_se": float(hit.SE.iloc[0]) if len(hit) else np.nan,
                "anchor_P": float(hit.P.iloc[0]) if len(hit) else np.nan,
                "anchor_q_global": float(hit.q_global.iloc[0]) if len(hit) else np.nan,
                "family_regex": fam_rx or "",
                "family_n_sets": int(len(fam)),
                "family_n_q_lt_0.05": int((fam.q_global < 0.05).sum()),
                "family_n_P_lt_0.001": int((fam.P < 1e-3).sum()),
                "family_best_set": f"{best.collection.iloc[0]}:{best.VARIABLE.iloc[0]} {best.NAME.iloc[0]}" if len(best) else "",
                "family_best_P": float(best.P.iloc[0]) if len(best) else np.nan,
                "family_best_q": float(best.q_global.iloc[0]) if len(best) else np.nan,
            })
        for sid in FROZEN6:
            hit = land[(land.collection == "syngo") & (land.VARIABLE == sid)]
            rows.append({"theme": f"FROZEN_S3::{sid}", "spec": spec, "spec_label": SPEC_LABEL[spec],
                         "anchor_set": sid, "anchor_collection": "syngo", "anchor_name": names.get(sid, ""),
                         "anchor_ngenes": int(hit.NGENES.iloc[0]), "anchor_beta": float(hit.BETA.iloc[0]),
                         "anchor_se": float(hit.SE.iloc[0]), "anchor_P": float(hit.P.iloc[0]),
                         "anchor_q_global": float(hit.q_global.iloc[0])})
        top = land.sort_values("P").head(15)
        extra[spec]["top15"] = [f"{r.collection}:{r.VARIABLE} {r.NAME} P={r.P:.2e} q={r.q_global:.3f}"
                                for r in top.itertuples()]
    mat = pd.DataFrame(rows)

    def verdict(g: pd.DataFrame) -> str:
        sig = (g.anchor_P < 0.05).to_numpy()
        fam = (g.get("family_n_q_lt_0.05", pd.Series([0] * len(g))).fillna(0) > 0).to_numpy()
        if sig.all() and fam.all():
            return "ROBUST: anchor nominal and >=1 family set at global FDR in every specification"
        if sig.all():
            return "ANCHOR_NOMINAL_IN_ALL_SPECS (family FDR varies)"
        if sig.any() or fam.any():
            return "SPECIFICATION_DEPENDENT"
        return "NOT_SUPPORTED_IN_ANY_SPEC (absence of enrichment in this GWAS, not proof of irrelevance)"
    v = mat.groupby("theme").apply(verdict, include_groups=False).rename("theme_verdict")
    mat = mat.merge(v, left_on="theme", right_index=True)
    return mat, extra


def s3_reproduction() -> dict:
    """D_S3 must reproduce the committed Sprint-3 syngo numbers exactly."""
    g = read_gsa(WORK / "syngo__D_S3.gsa.out").set_index("VARIABLE")
    e = pd.read_csv(REPO / "reports/gene_tournament/pathway_enrichment.csv")
    e = e[(e.conditioning == "cond_annotation") & (e.source_file == "syngo")].set_index("SET")
    out = {}
    for sid in FROZEN6:
        out[sid] = {"sprint3_P": float(e.loc[sid, "P"]), "rerun_P": float(g.loc[sid, "P"]),
                    "sprint3_beta": float(e.loc[sid, "BETA"]), "rerun_beta": float(g.loc[sid, "BETA"]),
                    "identical": bool(np.isclose(e.loc[sid, "P"], g.loc[sid, "P"], rtol=1e-3)
                                      and np.isclose(e.loc[sid, "BETA"], g.loc[sid, "BETA"], rtol=1e-3))}
    return out


def set_drivers() -> pd.DataFrame:
    """Top genes (by Davies gene P) in the membrane/adhesion sets and their exclusive parts."""
    g = pd.read_csv(REPO / "data/raw/magma_x01/2026-09-22/davies2018_10kb.genes.out", sep=r"\s+")
    sym = pd.read_csv(REPO / "data/raw/magma_x01/2026-09-22/gene_id_map.tsv", sep="\t", usecols=["GENE", "current_symbol"])
    ld = pd.read_parquet(REPO / "data/gene_tournament/ld_loci.parquet")[["GENE", "ld_block_r0.2"]]
    g = g.merge(sym, on="GENE").merge(ld, on="GENE")
    recon = {p[0]: {int(x) for x in p[1:]} for p in
             (ln.split() for ln in (REPO / "data/sprint3_1/recon_sets.setannot").read_text().splitlines()) if p}
    syn = {p[0]: {int(x) for x in p[1:]} for p in
           (ln.split() for ln in (REPO / "data/gene_tournament/pathway_sets/syngo.setannot").read_text().splitlines()) if p}
    named = {"PREMEMB_ONLY": recon["PREMEMB_ONLY"], "POSTMEMB_ONLY": recon["POSTMEMB_ONLY"],
             "PREPOSTMEMB_BOTH": recon["PREPOSTMEMB_BOTH"], **{s: syn[s] for s in FROZEN6[:4]}}
    bonf = 0.05 / len(g)
    rows = []
    for name, genes in named.items():
        x = g[g.GENE.isin(genes)].sort_values("P")
        for rank, r in enumerate(x.head(10).itertuples(), 1):
            rows.append({"set": name, "n_genes": len(x), "n_bonferroni": int((x.P < bonf).sum()),
                         "n_bonferroni_loci": int(x[x.P < bonf]["ld_block_r0.2"].nunique()),
                         "rank": rank, "gene": r.current_symbol, "davies_P": r.P,
                         "ld_block_r0.2": getattr(r, "_10", None)})
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    set_drivers().to_csv(OUT / "set_drivers.csv", index=False, float_format="%.3g")
    jt = joint_table()
    jt.to_csv(OUT / "pre_vs_post_joint_tests.csv", index=False, float_format="%.6g")
    mat, extra = sensitivity_matrix()
    mat.to_csv(OUT / "pathway_conditioning_sensitivity.csv", index=False, float_format="%.6g")
    summary = {"s3_reproduction": s3_reproduction(), "landscape": extra,
               "naive_marginal_differences": {spec: {
                   "PRE_minus_POST": marginal_difference(jt, "PRE", "POST", spec),
                   "PREMEMB_minus_POSTMEMB": marginal_difference(jt, "PREMEMB", "POSTMEMB", spec)}
                   for spec in SPEC_ORDER}}
    (OUT / "recon_magma_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary["s3_reproduction"], indent=0)[:900])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
