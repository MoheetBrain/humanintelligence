#!/usr/bin/env python3
"""Sprint 3.1 — inputs for the synaptic recon pass (no association data are read here).

Builds, from local Sprint-3 inputs only:

1. ``gene_covariates_full.txt`` — every gene in the Davies ``.genes.raw`` (18,418), so that
   every conditioning specification uses the SAME gene universe:
     * ``log_annotation_density`` — 0 for genes with no annotation. Sprint 3 left such genes
       out of its covariate file, so MAGMA silently dropped 1,349 genes from every
       conditioned run (the log shows "found 1349 genes not present in all input files").
       The conditioned and unconditioned Sprint-3 results were therefore computed on
       different backgrounds.
     * ``log_LOEUF`` — gnomAD v2.1.1; missing values imputed to the median, and counted.
     * ``neuron_expr`` / ``neuron_specificity`` — generic neuronal expression from the Siletti
       2022 adult human whole-brain atlas (31 superclusters, log2(1+CPM); read-only from the
       Codex worktree): mean over neuronal superclusters, and neuronal minus non-neuronal
       mean. Missing -> median, counted.
     * ``brain_expr_gtex`` — log2(1 + mean adult-brain median TPM), GTEx v10.
2. ``go_{bp,cc,mf}_prop.setannot`` — GO sets PROPAGATED up the is_a/part_of hierarchy
   (true-path rule). Sprint 3's GO sets came from gene2go direct annotations only, so
   "neurogenesis" held 79 genes and "neuron projection" 285, while SynGO sets (curated and
   already rolled up) were complete: an annotation-structure asymmetry favouring SynGO.
3. ``recon_sets.setannot`` — presynapse/postsynapse decompositions, a neuron-specific
   background set, theme anchors, and machinery categories for the system map.

Every choice of set and category is fixed here, before any MAGMA result of Sprint 3.1 is
produced.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipelines" / "gene_tournament"))
import build_pathway_sets as bps  # noqa: E402

RAW_ANN = REPO / "data" / "raw" / "pathway_annotations" / "2026-09-22"
SETS = REPO / "data" / "gene_tournament" / "pathway_sets"
GENES_RAW = REPO / "data" / "interim" / "magma_replication" / "davies2018_10kb.genes.raw"
GENE_MAP = REPO / "data" / "raw" / "magma_x01" / "2026-09-22" / "gene_id_map.tsv"
SILETTI = Path("data/external/x01/"
               "atlas_a/gene_expression_supercluster.parquet")
OUT = REPO / "data" / "sprint3_1"

NEURONAL = ["Amygdala excitatory", "CGE interneuron", "Cerebellar inhibitory",
            "Deep-layer corticothalamic and 6b", "Deep-layer intratelencephalic",
            "Deep-layer near-projecting", "Eccentric medium spiny neuron", "Hippocampal CA1-3",
            "Hippocampal CA4", "Hippocampal dentate gyrus", "LAMP5-LHX6 and Chandelier",
            "Lower rhombic lip", "MGE interneuron", "Mammillary body", "Medium spiny neuron",
            "Midbrain-derived inhibitory", "Thalamic excitatory", "Upper rhombic lip",
            "Upper-layer intratelencephalic"]
NON_NEURONAL = ["Astrocyte", "Bergmann glia", "Choroid plexus", "Committed oligodendrocyte precursor",
                "Ependymal", "Fibroblast", "Microglia", "Oligodendrocyte", "Oligodendrocyte precursor",
                "Vascular"]
# "Miscellaneous" and "Splatter" are heterogeneous by the atlas's own description: excluded.

# Theme anchors for the conditioning-sensitivity matrix: one pre-chosen, propagated set per theme.
THEME_ANCHORS = {
    "synapse": ("syngo", "GO_0045202"),
    "presynapse": ("syngo", "GO_0098793"),
    "postsynapse": ("syngo", "GO_0098794"),
    "postsynaptic_density": ("syngo", "GO_0014069"),
    "dendrite": ("go_cc_prop", "GO_0030425"),
    "neurogenesis": ("go_bp_prop", "GO_0022008"),
    "axon_guidance": ("go_bp_prop", "GO_0007411"),
    "chromatin": ("go_bp_prop", "GO_0006325"),
    "translation": ("go_bp_prop", "GO_0006412"),
    "mitochondria": ("go_cc_prop", "GO_0005739"),
    "oxidative_phosphorylation": ("go_bp_prop", "GO_0006119"),
    "myelin": ("go_bp_prop", "GO_0042552"),
    "neuron_projection": ("go_cc_prop", "GO_0043005"),
    "axon": ("go_cc_prop", "GO_0030424"),
}
# Name regexes defining theme FAMILIES (for counting how many sets of a theme survive).
THEME_REGEX = {
    "synapse": r"synap",
    "presynapse": r"presynap|synaptic vesicle|active zone|neurotransmitter secretion|exocytosis",
    "postsynapse": r"postsynap|dendritic spine|neurotransmitter receptor",
    "dendrite": r"dendrit",
    "neurogenesis": r"neurogenesis|neuron differentiation|neural precursor|neuroblast",
    "axon_guidance": r"axon guidance|axonogenesis|axon extension|neuron projection guidance",
    "chromatin": r"chromatin|histone|nucleosome",
    "translation": r"translation|ribosom",
    "mitochondria": r"mitochondri|oxidative phosphorylation|respiratory chain|electron transport",
    "myelin": r"myelin|oligodendrocyte",
}
# Synaptic machinery categories (SynGO / propagated GO), fixed before running.
MACHINERY = {
    "synapse_formation_adhesion": [("syngo", "GO_0007416"), ("syngo", "GO_0099560"), ("syngo", "GO_0051963")],
    "active_zone_organisation": [("syngo", "GO_0048786"), ("syngo", "GO_0099054"), ("syngo", "GO_0098831")],
    "vesicle_cycle_trafficking": [("syngo", "GO_0099504"), ("syngo", "GO_0008021"), ("syngo", "GO_0048488")],
    "vesicle_docking_priming": [("syngo", "GO_0016082"), ("go_bp_prop", "GO_0016081")],
    "ca_triggered_release": [("syngo", "GO_0016079"), ("syngo", "GO_0099502"), ("syngo", "GO_2000300")],
    "snare_cycle": [("go_bp_prop", "GO_0035493"), ("go_bp_prop", "GO_0035494"), ("go_cc_prop", "GO_0031201")],
    "receptor_trafficking": [("syngo", "GO_0099072"), ("syngo", "GO_0099645"), ("syngo", "GO_0098884"),
                             ("syngo", "GO_0099637")],
    "postsynaptic_plasticity_structure": [("syngo", "GO_0099173"), ("syngo", "GO_0099010"),
                                          ("go_bp_prop", "GO_0048167")],
    "activity_dependent_remodelling": [("syngo", "GO_0099563"), ("go_bp_prop", "GO_0060291"),
                                       ("go_bp_prop", "GO_0048168")],
    "generic_neuronal_projection": [("go_cc_prop", "GO_0043005"), ("go_cc_prop", "GO_0030424")],
}
RELEASE_CATS = ["active_zone_organisation", "vesicle_cycle_trafficking", "vesicle_docking_priming",
                "ca_triggered_release", "snare_cycle"]
ORGANISATION_CATS = ["synapse_formation_adhesion", "receptor_trafficking",
                     "postsynaptic_plasticity_structure", "activity_dependent_remodelling"]


def read_setannot(path: Path) -> dict[str, set[int]]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split()
        if p:
            out[p[0]] = {int(g) for g in p[1:]}
    return out


def parse_obo_relations(path: Path) -> dict[str, set[str]]:
    """{GO id: set of direct parents via is_a and part_of} for non-obsolete terms."""
    parents: dict[str, set[str]] = defaultdict(set)
    cur, obsolete = None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line == "[Term]":
            cur, obsolete = None, False
        elif line.startswith("[") and line.endswith("]"):
            cur = None
        elif cur is None and line.startswith("id: GO:"):
            cur = line[4:].strip()
        elif cur and line.startswith("is_obsolete: true"):
            obsolete = True
            parents.pop(cur, None)
        elif cur and not obsolete and line.startswith("is_a: "):
            parents[cur].add(line[6:].split()[0])
        elif cur and not obsolete and line.startswith("relationship: part_of "):
            parents[cur].add(line.split()[2])
    return parents


def ancestors(term: str, parents: dict[str, set[str]], memo: dict[str, set[str]]) -> set[str]:
    if term in memo:
        return memo[term]
    out: set[str] = set()
    stack = list(parents.get(term, ()))
    while stack:
        t = stack.pop()
        if t in out:
            continue
        out.add(t)
        stack.extend(parents.get(t, ()))
    memo[term] = out
    return out


def build_propagated_go(universe: set[int]) -> tuple[dict, dict, dict]:
    sets_ns, g2g_names, _ = bps.parse_gene2go(str(RAW_ANN / "gene2go_human_9606.tsv.gz"), "9606", "all")
    terms = bps.parse_go_obo(str(RAW_ANN / "go-basic.obo"))
    parents = parse_obo_relations(RAW_ANN / "go-basic.obo")
    memo: dict[str, set[str]] = {}
    out, stats = {}, {}
    for key, sets in sets_ns.items():
        prop: dict[str, set[int]] = defaultdict(set)
        for go_id, genes in sets.items():
            for t in {go_id} | ancestors(go_id, parents, memo):
                # keep propagation inside the namespace (part_of can cross namespaces rarely)
                if terms.get(t, (None, None))[1] and bps.GO_NAMESPACE_TO_KEY.get(terms[t][1]) != key:
                    continue
                prop[t] |= genes
        prop = {t: g & universe for t, g in prop.items()}
        out[key] = prop
        stats[key] = {"n_terms_direct": len(sets), "n_terms_propagated": len(prop)}
    names = {t: v[0] for t, v in terms.items()}
    names.update({k: v for k, v in g2g_names.items() if k not in names})
    return out, names, stats


def write_setannot(sets: dict[str, set[int]], path: Path, min_size: int = 10, max_size: int = 2000,
                   force: set[str] | None = None) -> int:
    force = force or set()
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for sid in sorted(sets):
            genes = sorted(sets[sid])
            if (min_size <= len(genes) <= max_size) or (sid in force and len(genes) >= min_size):
                fh.write(sid.replace(":", "_") + " " + " ".join(map(str, genes)) + "\n")
                n += 1
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(GENES_RAW, sep=r"\s+", comment="#", header=None, usecols=[0], names=["GENE"])
    universe = set(raw.GENE.astype(int))
    report: dict = {"n_genes_universe": len(universe)}

    # --- 1. covariates on the full universe -------------------------------------------
    counts: dict[int, int] = defaultdict(int)
    for path in sorted(SETS.glob("*.setannot")):
        for genes in read_setannot(path).values():
            for g in genes:
                counts[g] += 1
    cov = pd.DataFrame({"GENE": sorted(universe)})
    cov["n_annotations"] = cov.GENE.map(counts).fillna(0).astype(int)
    cov["log_annotation_density"] = np.log10(cov.n_annotations + 1)
    con = pd.read_csv(REPO / "data" / "interim" / "gnomad_constraint.tsv", sep="\t")[["GENE", "log_LOEUF"]]
    cov = cov.merge(con, on="GENE", how="left")
    report["log_LOEUF_missing_imputed_median"] = int(cov.log_LOEUF.isna().sum())
    cov["log_LOEUF"] = cov.log_LOEUF.fillna(cov.log_LOEUF.median())

    gm = pd.read_csv(GENE_MAP, sep="\t", usecols=["GENE", "ensembl_gene_id"]).dropna()
    sil = pd.read_parquet(SILETTI)
    neur = sil[NEURONAL].mean(axis=1)
    non = sil[NON_NEURONAL].mean(axis=1)
    ex = pd.DataFrame({"ensembl_gene_id": sil.index, "neuron_expr": neur.values,
                       "neuron_specificity": (neur - non).values})
    ex = gm.merge(ex, on="ensembl_gene_id", how="inner").groupby("GENE", as_index=False)[
        ["neuron_expr", "neuron_specificity"]].mean()
    cov = cov.merge(ex, on="GENE", how="left")
    for col in ("neuron_expr", "neuron_specificity"):
        report[f"{col}_missing_imputed_median"] = int(cov[col].isna().sum())
        cov[col] = cov[col].fillna(cov[col].median())

    dev = pd.read_parquet(REPO / "data" / "gene_tournament" / "developmental_classification.parquet",
                          columns=["entrez_id", "adult_brain_median_tpm"]).dropna(subset=["entrez_id"])
    dev = dev.groupby("entrez_id", as_index=False).adult_brain_median_tpm.mean()
    dev = dev.rename(columns={"entrez_id": "GENE"})
    dev["GENE"] = dev.GENE.astype(int)
    cov = cov.merge(dev, on="GENE", how="left")
    cov["brain_expr_gtex"] = np.log2(1 + cov.adult_brain_median_tpm)
    report["brain_expr_gtex_missing_imputed_median"] = int(cov.brain_expr_gtex.isna().sum())
    cov["brain_expr_gtex"] = cov.brain_expr_gtex.fillna(cov.brain_expr_gtex.median())
    keep = ["GENE", "log_annotation_density", "log_LOEUF", "neuron_expr", "neuron_specificity", "brain_expr_gtex"]
    cov[keep].to_csv(OUT / "gene_covariates_full.txt", sep="\t", index=False, float_format="%.6g")
    report["covariate_correlations_spearman"] = cov[keep[1:]].corr(method="spearman").round(3).to_dict()

    # --- 2. propagated GO -----------------------------------------------------------
    prop, names, pstats = build_propagated_go(universe)
    report["go_propagation"] = pstats
    anchors_needed = {sid for (src, sid) in THEME_ANCHORS.values() if src.endswith("_prop")}
    anchors_needed |= {sid for cats in MACHINERY.values() for (src, sid) in cats if src.endswith("_prop")}
    for key in ("bp", "cc", "mf"):
        force = {a.replace("_", ":") for a in anchors_needed}
        n = write_setannot(prop[key], OUT / f"go_{key}_prop.setannot", force=force)
        report[f"go_{key}_prop_sets_written"] = n
        with (OUT / f"go_{key}_prop.setannot.names.tsv").open("w", encoding="utf-8") as fh:
            fh.write("set_name\tdescription\n")
            for t in sorted(prop[key]):
                fh.write(f"{t.replace(':', '_')}\t{names.get(t, '')}\n")
    all_sets = {"syngo": read_setannot(SETS / "syngo.setannot")}
    for key in ("bp", "cc", "mf"):
        all_sets[f"go_{key}_prop"] = {t.replace(":", "_"): g for t, g in prop[key].items()}
    for key in ("bp", "cc", "mf"):
        all_sets[f"go_{key}_direct"] = read_setannot(SETS / f"go_{key}_human.setannot")

    # --- 3. recon sets ---------------------------------------------------------------
    syn = all_sets["syngo"]
    pre, post, synapse = syn["GO_0098793"], syn["GO_0098794"], syn["GO_0045202"]
    recon: dict[str, set[int]] = {
        "PRE": pre, "POST": post, "SYNAPSE": synapse,
        "PRE_ONLY": pre - post, "POST_ONLY": post - pre, "PRE_AND_POST": pre & post,
        "PRE_OR_POST": pre | post,
        "PREMEMB": syn["GO_0042734"], "POSTMEMB": syn["GO_0045211"],
        "PREMEMB_ONLY": syn["GO_0042734"] - syn["GO_0045211"],
        "POSTMEMB_ONLY": syn["GO_0045211"] - syn["GO_0042734"],
        "PREPOSTMEMB_BOTH": syn["GO_0042734"] & syn["GO_0045211"],
        "PREPOSTMEMB_UNION": syn["GO_0042734"] | syn["GO_0045211"],
        "PSD": syn["GO_0014069"], "PRE_PROCESS": syn["SYNGO_presynprocess"],
        "POST_PROCESS": syn["SYNGO_postsynprocess"],
        "PREPROC_ONLY": syn["SYNGO_presynprocess"] - syn["SYNGO_postsynprocess"],
        "POSTPROC_ONLY": syn["SYNGO_postsynprocess"] - syn["SYNGO_presynprocess"],
        "PREPOSTPROC_BOTH": syn["SYNGO_presynprocess"] & syn["SYNGO_postsynprocess"],
        "PREPOSTPROC_UNION": syn["SYNGO_presynprocess"] | syn["SYNGO_postsynprocess"],
        "GOCC_PRESYNAPSE_PROP": all_sets["go_cc_prop"].get("GO_0098793", set()),
        "GOCC_POSTSYNAPSE_PROP": all_sets["go_cc_prop"].get("GO_0098794", set()),
        "GOCC_SYNAPSE_PROP": all_sets["go_cc_prop"].get("GO_0045202", set()),
    }
    spec = cov.set_index("GENE").neuron_specificity
    recon["NEURON_SPECIFIC_TOP20"] = set(spec[spec >= spec.quantile(0.8)].index.astype(int))
    bexp = cov.set_index("GENE").brain_expr_gtex
    recon["BRAIN_EXPRESSED_TOP50"] = set(bexp[bexp >= bexp.quantile(0.5)].index.astype(int))
    for theme, (src, sid) in THEME_ANCHORS.items():
        recon[f"THEME_{theme}"] = all_sets[src].get(sid, set())
    for cat, members in MACHINERY.items():
        u: set[int] = set()
        for src, sid in members:
            u |= all_sets[src].get(sid, set())
        recon[f"CAT_{cat}"] = u
    rel = set().union(*(recon[f"CAT_{c}"] for c in RELEASE_CATS))
    org = set().union(*(recon[f"CAT_{c}"] for c in ORGANISATION_CATS))
    recon.update({"RELEASE_MACHINERY": rel, "ORGANISATION_TRAFFICKING": org,
                  "RELEASE_ONLY": rel - org, "ORGANISATION_ONLY": org - rel,
                  "RELEASE_AND_ORG": rel & org, "RELEASE_OR_ORG": rel | org})
    recon = {k: v & universe for k, v in recon.items()}
    write_setannot(recon, OUT / "recon_sets.setannot", min_size=5, max_size=20000)
    report["recon_set_sizes"] = {k: len(v) for k, v in recon.items()}
    report["theme_anchor_sizes_direct_vs_propagated"] = {
        th: {"propagated_or_syngo": len(all_sets[src].get(sid, set())),
             "sprint3_direct": len(all_sets.get(src.replace("_prop", "_direct"), {}).get(sid, set()))
             if src.endswith("_prop") else None}
        for th, (src, sid) in THEME_ANCHORS.items()}
    report["plan"] = {"theme_anchors": THEME_ANCHORS, "theme_regex": THEME_REGEX,
                      "machinery": MACHINERY, "release_categories": RELEASE_CATS,
                      "organisation_categories": ORGANISATION_CATS,
                      "neuronal_superclusters": NEURONAL, "non_neuronal_superclusters": NON_NEURONAL,
                      "siletti_source": str(SILETTI)}
    (OUT / "inputs_report.json").write_text(json.dumps(report, indent=1, default=list) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("n_genes_universe", "log_LOEUF_missing_imputed_median",
                                             "neuron_expr_missing_imputed_median",
                                             "brain_expr_gtex_missing_imputed_median", "go_propagation",
                                             "theme_anchor_sizes_direct_vs_propagated")}, indent=1))
    print({k: v for k, v in report["recon_set_sizes"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
