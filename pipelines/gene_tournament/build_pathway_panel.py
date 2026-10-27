#!/usr/bin/env python3
"""Sprint 3, Part K (hypothesis layer) -- the brief's named hypotheses, tested and replicated.

Three outputs
-------------
``pathway_hypothesis_panel.csv``
    One pre-named anchor set per hypothesis in the brief (synaptic organisation, dendritic
    integration, axon guidance, myelination, oligodendrocyte, astrocyte, mitochondria/OXPHOS,
    neurovascular, translation, activity-dependent transcription, ion channels, GPCRs,
    neuromodulators, chromatin/development), read from the conditioned MAGMA run and
    Bonferroni-corrected across the 14 anchors. Cell-type hypotheses are ALSO given X01's
    cell-type expression result, because GO process terms are the wrong instrument for
    "astrocyte biology" -- X01's gene-level input is verified in this repository; its
    cell-property layer was not re-derived here, and every such row says so.

``pathway_replication.csv``
    The sets surviving global FDR (conditioned) re-tested, same conditioning, in Savage 2018
    (overlapping sample: shares UK Biobank) and Zabaneh 2018 extreme-IQ (UKB-free, 65x less
    power). Replication in Savage is reproducibility, not independence.

Anchor corrections recorded here rather than silently
-----------------------------------------------------
* activity-dependent transcription: the first anchor, GO:0070374, is "positive regulation of
  ERK1 and ERK2 cascade" -- WRONG. GO has no clean activity-dependent-transcription set; the
  nearest honest proxy, "cellular response to calcium ion", is used and labelled a proxy.
* astrocyte, neuromodulators: first anchors were not in the tested size range.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "reports" / "gene_tournament"
SETS = REPO_ROOT / "data" / "gene_tournament" / "pathway_sets"
WORK = REPO_ROOT / "data" / "interim" / "magma_sets"
GENES_RAW = REPO_ROOT / "data" / "interim" / "magma_replication"
MAGMA_BIN = Path("/path/to/user/Documents/ChatGPT/intelligence-codex/research/"
                 "extreme_cognition/x01/genetics_tools/bin/magma")
X01 = Path("/path/to/user/Documents/ChatGPT/intelligence-codex/reports/astra/x01/"
           "cell_enrichment_results.parquet")

ANCHORS = {  # hypothesis -> (set id, note)
    "synaptic_organisation": ("GO_0050808", ""),
    "dendritic_integration": ("GO_0030425", ""),
    "axon_guidance": ("GO_0007411", ""),
    "myelination": ("GO_0042552", ""),
    "oligodendrocyte": ("GO_0048709", ""),
    "astrocyte": ("GO_0097449", "GO astrocyte sets are small process terms; see the X01 cell-type row"),
    "mitochondria_OXPHOS": ("GO_0006119", ""),
    "neurovascular": ("GO_0001525", ""),
    "protein_translation": ("GO_0006412", ""),
    "activity_dependent_transcription": ("GO_0071277", "PROXY: GO has no clean set; first anchor "
                                          "GO:0070374 (ERK1/2 cascade) was wrong"),
    "ion_channels": ("GO_0005216", ""),
    "GPCRs": ("GO_0004930", ""),
    "neuromodulators": ("GO_0030594", "serotonin-receptor family sets nominal only"),
    "chromatin_development": ("GO_0006338", ""),
}
CELL_CLASSES = {"astrocyte": "astrocyte_celltype", "oligodendrocyte": "oligodendrocyte_celltype",
                "opc": "OPC_celltype", "cortical_hippocampal_pyramidal": "pyramidal_celltype",
                "cortical_interneuron": "interneuron_celltype",
                "microglia_macrophage": "microglia_celltype", "vascular": "vascular_celltype"}


def panel(e: pd.DataFrame) -> pd.DataFrame:
    cond, plain = e[e.conditioning == "cond_annotation"], e[e.conditioning == "plain"]
    rows = []
    for hyp, (sid, note) in ANCHORS.items():
        a = cond[cond.SET == sid].sort_values("P").head(1)
        ap = plain[plain.SET == sid].sort_values("P").head(1)
        rows.append({"hypothesis": hyp, "anchor_set": sid.replace("_", ":"),
                     "anchor_name": a.NAME.iloc[0] if len(a) else "NOT_IN_TESTED_SETS",
                     "anchor_ngenes": float(a.NGENES.iloc[0]) if len(a) else np.nan,
                     "anchor_P_plain": float(ap.P.iloc[0]) if len(ap) else np.nan,
                     "anchor_P_conditioned": float(a.P.iloc[0]) if len(a) else np.nan,
                     "anchor_beta_conditioned": float(a.BETA.iloc[0]) if len(a) else np.nan,
                     "anchor_note": note,
                     "test_type": "MAGMA gene-set, conditioned (size, density, LD, annotation density, LOEUF)"})
    r = pd.DataFrame(rows)
    r["anchor_P_bonf14"] = (r.anchor_P_conditioned * len(ANCHORS)).clip(upper=1)
    r["verdict"] = np.where(r.anchor_P_bonf14 < 0.05, "SURVIVES",
                            np.where(r.anchor_P_conditioned < 0.05, "NOMINAL_ONLY", "DOES_NOT_SURVIVE"))
    if X01.exists():
        x = pd.read_parquet(X01)
        x = x[(x.primary_specification == True) & (x.level == "broad")  # noqa: E712
              & x.atlas.isin(["atlas_a", "atlas_b"]) & x.model.isin(["broad_marginal", "broad_joint"])]
        cells = []
        for cls, hyp in CELL_CLASSES.items():
            s = x[x.broad_class == cls]
            get = lambda m, a: s[(s.model == m) & (s.atlas == a)].p.min()  # noqa: E731
            v = {"A_marg": get("broad_marginal", "atlas_a"), "A_joint": get("broad_joint", "atlas_a"),
                 "B_marg": get("broad_marginal", "atlas_b"), "B_joint": get("broad_joint", "atlas_b")}
            present = [q for q in v.values() if not np.isnan(q)]
            nsig = sum(q < 0.05 for q in present)
            if present and nsig == len(present):
                verdict = "CONSISTENT_NOMINAL"
            elif v["A_joint"] < 0.05 and v["B_joint"] < 0.05:
                verdict = "CROSS_ATLAS_JOINT_NOMINAL"
            elif nsig:
                verdict = "INCONSISTENT_ACROSS_ATLAS_OR_MODEL"
            else:
                verdict = "DOES_NOT_SURVIVE"
            cells.append({"hypothesis": hyp, "anchor_set": f"X01 broad class: {cls}", "anchor_name": cls,
                          "anchor_P_plain": v["A_marg"], "anchor_P_conditioned": v["A_joint"],
                          "anchor_note": (f"atlasA(Siletti) marginal P={v['A_marg']:.3g}, joint P={v['A_joint']:.3g}; "
                                          f"atlasB(Allen cortex) marginal P={v['B_marg']:.3g}, joint P={v['B_joint']:.3g}"),
                          "verdict": verdict,
                          "test_type": "X01 MAGMA gene-property (Codex); gene-level input VERIFIED here, "
                                       "cell-property layer NOT re-derived"})
        r = pd.concat([r, pd.DataFrame(cells)], ignore_index=True)
    return r


def replication(e: pd.DataFrame) -> pd.DataFrame:
    sig = e[(e.conditioning == "cond_annotation") & (e.FDR_global < 0.05)]
    covar = WORK / "gene_covariates.txt"
    names = covar.read_text().splitlines()[0].split("\t")[1:] if covar.exists() else []
    rows = []
    for tag, label in (("savage2018_intelligence_10kb", "Savage 2018 (overlapping: shares UKB)"),
                       ("zabaneh_extremeIQ_10kb", "Zabaneh 2018 extreme IQ (UKB-free, N_eff 4,300)")):
        raw = GENES_RAW / f"{tag}.genes.raw"
        for src in sorted(sig.source_file.unique()):
            if not raw.exists() or not MAGMA_BIN.exists() or not names:
                for _, s in sig[sig.source_file == src].iterrows():
                    rows.append({"set": s.SET, "name": s.NAME, "dataset": label, "status": "NOT_RUN (inputs absent)"})
                continue
            out = WORK / f"replication_{src}_{tag}"
            subprocess.run([str(MAGMA_BIN), "--gene-results", str(raw), "--set-annot",
                            str(SETS / f"{src}.setannot"), "--gene-covar", str(covar),
                            "--model", "condition-hide=" + ",".join(names), "--out", str(out)],
                           capture_output=True, text=True, timeout=3600)
            res = pd.read_csv(out.with_suffix(".gsa.out"), sep=r"\s+", comment="#")
            res = res.set_index("VARIABLE")
            for _, s in sig[sig.source_file == src].iterrows():
                hit = res.loc[s.SET] if s.SET in res.index else None
                rows.append({"set": s.SET, "name": s.NAME, "discovery_P": s.P, "discovery_beta": s.BETA,
                             "dataset": label,
                             "beta": float(hit.BETA) if hit is not None else np.nan,
                             "P": float(hit.P) if hit is not None else np.nan,
                             "status": "ok" if hit is not None else "set_absent"})
    rep = pd.DataFrame(rows)
    rep["same_sign"] = np.sign(rep.get("beta", np.nan)) == np.sign(rep.get("discovery_beta", np.nan))
    return rep


def main() -> int:
    e = pd.read_csv(OUT / "pathway_enrichment.csv")
    p = panel(e)
    p.to_csv(OUT / "pathway_hypothesis_panel.csv", index=False)
    rep = replication(e)
    rep.to_csv(OUT / "pathway_replication.csv", index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 50)
    print(p[["hypothesis", "anchor_name", "anchor_P_conditioned", "verdict"]].to_string(index=False))
    print()
    print(rep[["name", "dataset", "discovery_P", "beta", "P", "same_sign"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
