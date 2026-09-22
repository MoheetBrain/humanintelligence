#!/usr/bin/env python3
"""Sprint 3, Parts L, M, O -- can ~1,300 cognition genes be compressed into a few modules?

What goes in
------------
The 1,272 genes at MAGMA gene-level FDR < 0.01 (Davies 2018, N=282,014), representing
565 LD blocks. Two independent descriptions of each gene:

* **Annotation profile** -- membership across GO BP/CC/MF, Reactome and SynGO sets
  (10-2000 genes), IDF-weighted so that a gene sharing a small specific set with
  another counts more than two genes sharing "cytoplasm". Cosine similarity, kNN graph.
* **Interaction profile** -- STRING v12 functional-association edges (score >= 400).

The fused graph averages the two. Three clustering methods are run on it -- Louvain
(graph), agglomerative (annotation cosine), NMF (annotation matrix) -- and their agreement
is reported, because a module that one method finds and two do not is a method artefact.

Stability, three ways
---------------------
1. Gene bootstrap: 80% of genes resampled 100 times; a module's stability is the mean rate
   at which its member pairs are co-clustered when both are drawn.
2. Leave-one-annotation-source-out: the whole pipeline without GO BP, CC, MF, Reactome,
   SynGO, or STRING in turn; ARI against the full solution.
3. Leave-study-out: modules re-derived from Savage 2018 FDR<0.01 genes instead of Davies,
   and each Davies module matched to its best Savage counterpart by Jaccard.

What a module is NOT
--------------------
A module is a cluster of genes that are annotated alike and/or interact. It is not a
pathway that has been shown to act, not a causal unit, and not a target. Genes that are
barely annotated cannot be placed well by an annotation-based method, and their
exclusion is the method's bias, not a finding: the fraction of genetic evidence that ends
up UNASSIGNED is reported as prominently as the modules themselves.

Weighted genetic evidence (Q12)
-------------------------------
Each LD block contributes its lead gene's chi-square (Z^2) ONCE, split equally across its
member genes in the input set. A module's share is the sum over its genes. This is a share
of the gene-level association evidence at FDR<0.01 -- NOT a share of heritability, which
is overwhelmingly carried by sub-threshold loci this analysis does not see.
"""

from __future__ import annotations

import glob
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.decomposition import NMF
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import normalize

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

DATA = REPO_ROOT / "data" / "gene_tournament"
OUT = REPO_ROOT / "reports" / "gene_tournament"
SETS = REPO_ROOT / "data" / "gene_tournament" / "pathway_sets"  # committed (2.3 MB)
SEED = 20260922
KNN = 15
MIN_MODULE = 10
SOURCES = ["go_bp_human", "go_cc_human", "go_mf_human", "reactome_human", "syngo"]


def load_sets() -> tuple[dict[str, list[int]], dict[str, str], dict[str, str]]:
    members, names, source = {}, {}, {}
    for src in SOURCES:
        path = SETS / f"{src}.setannot"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            parts = line.split()
            key = f"{src}:{parts[0]}"
            members[key] = [int(x) for x in parts[1:]]
            source[key] = src
        nt = pd.read_csv(SETS / f"{src}.setannot.names.tsv", sep="\t", dtype=str)
        for sid, desc in zip(nt.set_name, nt.description):
            names[f"{src}:{sid}"] = desc
    return members, names, source


def annotation_matrix(genes: list[int], members, source, drop_source=None):
    idx = {g: i for i, g in enumerate(genes)}
    cols, rows, vals, keys = [], [], [], []
    n_genome = 19000
    for key, mem in members.items():
        if drop_source and source[key] == drop_source:
            continue
        hit = [idx[g] for g in mem if g in idx]
        if len(hit) < 3:
            continue
        w = math.log(n_genome / len(mem))
        c = len(keys)
        keys.append(key)
        rows += hit
        cols += [c] * len(hit)
        vals += [w] * len(hit)
    m = sparse.csr_matrix((vals, (rows, cols)), shape=(len(genes), len(keys)))
    return m, keys


def knn_graph(m: sparse.csr_matrix, genes: list[int], k: int = KNN) -> nx.Graph:
    x = normalize(m, norm="l2", axis=1)
    sim = (x @ x.T).toarray()
    np.fill_diagonal(sim, 0)
    g = nx.Graph()
    g.add_nodes_from(genes)
    for i in range(len(genes)):
        if not sim[i].any():
            continue
        top = np.argpartition(-sim[i], min(k, len(genes) - 1))[:k]
        for j in top:
            if sim[i, j] > 0:
                g.add_edge(genes[i], genes[j], w_ann=float(sim[i, j]))
    return g


def string_graph(sym_to_gene: dict[str, int]) -> nx.Graph:
    path = sorted(glob.glob(str(REPO_ROOT / "data/raw/string/*/string_network_fdr01_genes_score400.tsv.gz")))[-1]
    t = pd.read_csv(path, sep="\t", compression="gzip")
    g = nx.Graph()
    for a, b, s in zip(t.preferredName_A, t.preferredName_B, t.score):
        if a in sym_to_gene and b in sym_to_gene:
            g.add_edge(sym_to_gene[a], sym_to_gene[b], w_str=float(s))
    return g


def fuse(ann: nx.Graph | None, st: nx.Graph | None, genes: list[int]) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(genes)
    for src, attr in ((ann, "w_ann"), (st, "w_str")):
        if src is None:
            continue
        for u, v, d in src.edges(data=True):
            w = 0.5 * d[attr]
            if g.has_edge(u, v):
                g[u][v]["weight"] += w
            else:
                g.add_edge(u, v, weight=w)
    return g


def louvain(g: nx.Graph, resolution: float, seed: int = SEED) -> dict[int, int]:
    comms = nx.community.louvain_communities(g, weight="weight", resolution=resolution, seed=seed)
    lab = {}
    for i, c in enumerate(sorted(comms, key=len, reverse=True)):
        for n in c:
            lab[n] = i if len(c) >= MIN_MODULE else -1
    return lab


def relabel(lab: dict[int, int]) -> dict[int, int]:
    sizes = Counter(v for v in lab.values() if v >= 0)
    order = {old: new for new, (old, _) in enumerate(sizes.most_common())}
    return {k: order.get(v, -1) for k, v in lab.items()}


def tail_engagement() -> pd.DataFrame:
    """Is any module MORE engaged at the extreme tail than other cognition genes?

    Module genes were selected on Davies significance, so against the whole genome every
    module looks tail-engaged -- continuity alone produces that. The informative comparison
    is within the FDR<0.01 set, with extreme-tail Z residualised on population Z so that a
    module is not credited merely for holding stronger population hits.
    """
    mem = pd.read_csv(DATA / "module_membership.csv")
    ext = pd.read_csv(OUT / "extreme_tail_rank.csv")[["GENE", "Z_ext", "Z_pop"]].rename(columns={"GENE": "entrez_id"})
    d = mem.merge(ext, on="entrez_id", how="left").dropna(subset=["Z_ext"])
    fit = stats.linregress(d.Z_pop, d.Z_ext)
    d["Z_ext_resid"] = d.Z_ext - (fit.intercept + fit.slope * d.Z_pop)
    rows = []
    for mod, grp in d.groupby("module"):
        other = d[d.module != mod]
        u = stats.mannwhitneyu(grp.Z_ext_resid, other.Z_ext_resid, alternative="greater")
        rows.append({"module": mod, "n": len(grp), "mean_Z_ext": grp.Z_ext.mean(),
                     "mean_resid_vs_other_cognition_genes": grp.Z_ext_resid.mean(),
                     "MWU_P_more_tail_engaged": u.pvalue})
    r = pd.DataFrame(rows).sort_values("MWU_P_more_tail_engaged")
    r["bonferroni"] = (r.MWU_P_more_tail_engaged * len(r)).clip(upper=1)
    r.to_csv(OUT / "module_tail_engagement.csv", index=False)
    return r


def main() -> int:
    if "--tail-only" in sys.argv:
        print(tail_engagement().to_string(index=False))
        return 0
    genes_df = pd.read_csv(DATA / "module_input_genes.csv").dropna(subset=["entrez_id"])
    genes_df["entrez_id"] = genes_df.entrez_id.astype(int)
    genes = genes_df.entrez_id.tolist()
    sym = dict(zip(genes_df.entrez_id, genes_df.gene))
    sym_to_gene = {v: k for k, v in sym.items()}
    members, names, source = load_sets()

    m, keys = annotation_matrix(genes, members, source)
    ann = knn_graph(m, genes)
    st = string_graph(sym_to_gene)
    fused = fuse(ann, st, genes)
    n_annotated = int((m.getnnz(axis=1) > 0).sum())
    print(f"genes {len(genes)}; annotated {n_annotated}; sets used {len(keys)}; "
          f"STRING edges {st.number_of_edges()}; fused edges {fused.number_of_edges()}")

    # -- choose resolution: the smallest giving 5-20 modules of >= MIN_MODULE genes -----
    sweep = []
    for res in [0.3, 0.5, 0.7, 0.9, 1.0, 1.2, 1.5, 2.0]:
        lab = louvain(fused, res)
        n_mod = len({v for v in lab.values() if v >= 0})
        frac = np.mean([v >= 0 for v in lab.values()])
        q = nx.community.modularity(fused, [set(k for k, v in lab.items() if v == c) for c in set(lab.values())], weight="weight")
        sweep.append({"resolution": res, "n_modules": n_mod, "frac_assigned": frac, "modularity": q})
    sweep_df = pd.DataFrame(sweep)
    ok = sweep_df[(sweep_df.n_modules >= 5) & (sweep_df.n_modules <= 20)]
    res = float(ok.sort_values("modularity", ascending=False).resolution.iloc[0]) if len(ok) else 1.0
    lab_l = relabel(louvain(fused, res))
    k = len({v for v in lab_l.values() if v >= 0})
    print("resolution sweep:\n", sweep_df.to_string(index=False), f"\nchosen resolution {res}: {k} modules")

    # -- method agreement ---------------------------------------------------------------
    ann_rows = np.where(m.getnnz(axis=1) > 0)[0]
    xa = normalize(m[ann_rows], axis=1).toarray()
    hc = fcluster(linkage(xa, method="average", metric="cosine"), t=k, criterion="maxclust")
    nmf = NMF(n_components=k, init="nndsvda", random_state=SEED, max_iter=600).fit_transform(m[ann_rows])
    nm = nmf.argmax(axis=1)
    lab_ann = [lab_l[genes[i]] for i in ann_rows]
    agreement = {"ARI_louvain_vs_hierarchical": float(adjusted_rand_score(lab_ann, hc)),
                 "ARI_louvain_vs_NMF": float(adjusted_rand_score(lab_ann, nm)),
                 "ARI_hierarchical_vs_NMF": float(adjusted_rand_score(hc, nm))}
    print("method agreement:", agreement)

    # -- bootstrap stability --------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    pair_co, pair_n = defaultdict(int), defaultdict(int)
    mod_members = defaultdict(list)
    for gname, l in lab_l.items():
        if l >= 0:
            mod_members[l].append(gname)
    for b in range(100):
        pick = set(rng.choice(genes, size=int(0.8 * len(genes)), replace=False).tolist())
        sub = fused.subgraph(pick).copy()
        lb = louvain(sub, res, seed=SEED + b)
        for l, mem in mod_members.items():
            inside = [x for x in mem if x in pick]
            for i in range(len(inside)):
                for j in range(i + 1, len(inside)):
                    pair_n[l] += 1
                    if lb[inside[i]] == lb[inside[j]] and lb[inside[i]] >= 0:
                        pair_co[l] += 1
    stability = {l: pair_co[l] / pair_n[l] if pair_n[l] else float("nan") for l in mod_members}

    # -- leave-one-source-out -------------------------------------------------------------
    loso = {}
    for drop in SOURCES + ["STRING"]:
        if drop == "STRING":
            fg = fuse(ann, None, genes)
        else:
            m2, _ = annotation_matrix(genes, members, source, drop_source=drop)
            fg = fuse(knn_graph(m2, genes), st, genes)
        l2 = louvain(fg, res)
        loso[drop] = float(adjusted_rand_score([lab_l[x] for x in genes], [l2[x] for x in genes]))
    print("leave-one-source-out ARI:", {k2: round(v, 3) for k2, v in loso.items()})

    # -- leave-study-out: Savage-derived modules ------------------------------------------
    b = pd.read_csv(OUT / "direct_cognition_rank.csv")
    p = b.gene_P_savage.fillna(1).values
    o = np.argsort(p); n = len(p); q = p[o] * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]; fdr = np.empty(n); fdr[o] = np.minimum(q, 1)
    sav_genes = [int(x) for x in b.entrez_id[fdr < 0.01] if not pd.isna(x)]
    ms, _ = annotation_matrix(sav_genes, members, source)
    st_s = nx.Graph([(u, v, d) for u, v, d in st.edges(data=True) if u in set(sav_genes) and v in set(sav_genes)])
    ls = relabel(louvain(fuse(knn_graph(ms, sav_genes), st_s, sav_genes), res))
    sav_mods = defaultdict(set)
    for gname, l in ls.items():
        if l >= 0:
            sav_mods[l].add(gname)
    lso = {}
    for l, mem in mod_members.items():
        best = max(((len(set(mem) & s) / len(set(mem) | s), sl) for sl, s in sav_mods.items()), default=(0, None))
        lso[l] = best[0]

    # -- module evidence ------------------------------------------------------------------
    core = b.set_index("entrez_id")
    dev = pd.read_parquet(DATA / "developmental_classification.parquet")
    dev = dev.dropna(subset=["entrez_id"])
    dev["entrez_id"] = pd.to_numeric(dev.entrez_id, errors="coerce")
    dev = dev.dropna(subset=["entrez_id"]).drop_duplicates("entrez_id").set_index("entrez_id")
    ext = pd.read_csv(OUT / "extreme_tail_rank.csv").set_index("GENE")
    mth = pd.read_csv(OUT / "math_gene_rank.csv").set_index("entrez_id")
    brd = pd.read_csv(OUT / "cognitive_breadth.csv").set_index("entrez_id")
    pe = pd.read_csv(OUT / "pathway_enrichment.csv")
    pe_c = pe[pe.conditioning == "cond_annotation"].copy()
    pe_c.index = pe_c.source_file + ":" + pe_c.SET
    cg = pd.read_csv(sorted(glob.glob(str(REPO_ROOT / "data/raw/clingen/*/ClinGen_gene_curation_list_GRCh38.tsv")))[-1], sep="\t", skiprows=5)
    cg.columns = [c.lstrip("#").strip() for c in cg.columns]
    hi3 = set(cg[cg["Haploinsufficiency Score"].astype(str) == "3"]["Gene Symbol"])

    # block weights: each block's lead chi-square once, split over its members in the set
    gdf = genes_df.set_index("entrez_id")
    block_z2 = gdf.groupby("ld_block_r0.2").gene_Z.apply(lambda z: float(np.max(z) ** 2))
    block_n = gdf.groupby("ld_block_r0.2").size()
    weight = {g: block_z2[gdf.loc[g, "ld_block_r0.2"]] / block_n[gdf.loc[g, "ld_block_r0.2"]] for g in genes}
    total_w = float(sum(weight.values()))
    bg_ext = ext.Z_ext.dropna()

    rows = []
    idx = {g: i for i, g in enumerate(genes)}
    for l, mem in sorted(mod_members.items()):
        sub = m[[idx[g] for g in mem]]
        prev = np.asarray((sub > 0).sum(axis=0)).ravel() / len(mem)
        order = np.argsort(-prev * np.array([math.log(19000 / len(members[kk])) for kk in keys]))[:8]
        labels = [f"{names.get(keys[i], keys[i])} ({prev[i]:.0%})" for i in order if prev[i] > 0]
        label_sets = [keys[i] for i in order if prev[i] > 0][:5]
        enr = pe_c.reindex(label_sets)
        best_enr = enr.sort_values("P").iloc[0] if enr.P.notna().any() else None
        z_ext = ext.Z_ext.reindex(mem).dropna()
        ext_p = float(stats.mannwhitneyu(z_ext, bg_ext, alternative="greater").pvalue) if len(z_ext) > 5 else float("nan")
        dcls = dev.developmental_class.reindex(mem).fillna("NO_DATA").value_counts(normalize=True)
        blocks = gdf.loc[mem, "ld_block_r0.2"].nunique()
        rows.append({
            "module": f"M{l + 1:02d}", "n_genes": len(mem), "n_independent_loci": int(blocks),
            "genes_top_by_P": "|".join(gdf.loc[mem].sort_values("gene_P").gene.head(15)),
            "all_genes": "|".join(sorted(sym[g] for g in mem)),
            "pathway_labels": " ; ".join(labels[:5]),
            "label_best_enrichment_set": (names.get(best_enr.name, best_enr.name) if best_enr is not None else ""),
            "label_best_enrichment_P_conditioned": (float(best_enr.P) if best_enr is not None else np.nan),
            "label_best_enrichment_FDR_global": (float(best_enr.FDR_global) if best_enr is not None and "FDR_global" in best_enr else np.nan),
            "weighted_evidence": sum(weight[g] for g in mem),
            "weighted_evidence_share": sum(weight[g] for g in mem) / total_w,
            "mean_gene_Z": float(gdf.loc[mem, "gene_Z"].mean()),
            "extreme_tail_mean_Z": float(z_ext.mean()) if len(z_ext) else np.nan,
            "extreme_tail_MWU_P_vs_genome": ext_p,
            "math_mean_Z_objective_item": float(mth.A_raw_math_Z_objective_item.reindex(mem).mean()),
            "n_shared_g_math": int((mth.math_class.reindex(mem) == "shared_g_math").sum()),
            "mean_distinct_unit_domains": float(brd.n_domains_supported_by_distinct_cohort_units.reindex(mem).mean()),
            "n_strict_independence_units_sum": int(core.number_of_independent_cohorts_upper_bound.reindex(mem).fillna(0).sum()),
            "frac_adult_dynamic": float(dcls.get("ADULT_DYNAMIC", 0)),
            "frac_prenatal_or_developmental": float(dcls.get("PRENATAL_DOMINANT", 0) + dcls.get("DEVELOPMENTAL", 0)),
            "frac_adult_expressed": float(dev.adult_expressed.reindex(mem).mean()),
            "n_clingen_haploinsufficient": int(sum(sym[g] in hi3 for g in mem)),
            "positive_human_members": "|".join(sorted({"EDAR", "SH3RF3", "SEPTIN10", "SOWAHC"} & {sym[g] for g in mem})),
            "bootstrap_stability": stability[l],
            "leave_study_out_best_jaccard_savage": lso[l],
        })
    mods = pd.DataFrame(rows).sort_values("weighted_evidence", ascending=False)
    unassigned = [g for g in genes if lab_l[g] < 0]
    unassigned_w = sum(weight[g] for g in unassigned)
    shares = mods.weighted_evidence_share.sort_values(ascending=False).cumsum().to_numpy()
    cover = {f"top_{n}": float(shares[min(n, len(shares)) - 1]) for n in (5, 10, 20)}

    OUT.mkdir(parents=True, exist_ok=True)
    long = [{"gene": sym[g], "entrez_id": g, "module": (f"M{lab_l[g] + 1:02d}" if lab_l[g] >= 0 else "UNASSIGNED"),
             "gene_P": float(gdf.loc[g, "gene_P"]), "ld_block": gdf.loc[g, "ld_block_r0.2"],
             "evidence_weight": weight[g], "n_annotations_in_matrix": int(m[idx[g]].getnnz()),
             "string_degree": st.degree(g) if g in st else 0} for g in genes]
    pd.DataFrame(long).to_csv(DATA / "module_membership.csv", index=False)
    mods.to_csv(OUT / "biological_modules.csv", index=False)
    summary = {"built_at": utc_now(), "n_input_genes": len(genes), "n_input_ld_blocks": int(gdf["ld_block_r0.2"].nunique()),
               "n_genes_annotated": n_annotated, "n_sets_used": len(keys), "n_string_edges": st.number_of_edges(),
               "louvain_resolution": res, "resolution_sweep": sweep, "n_modules": k,
               "n_unassigned_genes": len(unassigned), "unassigned_evidence_share": unassigned_w / total_w,
               "weighted_evidence_captured": cover, "method_agreement_ARI": agreement,
               "leave_one_source_out_ARI": loso,
               "stability_note": "bootstrap = mean co-clustering of member pairs over 100 x 80% gene resamples",
               "evidence_share_definition": "share of FDR<0.01 gene-level association evidence (block lead Z^2 once per block); NOT heritability"}
    (OUT / "modules_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
    print(mods[["module", "n_genes", "n_independent_loci", "weighted_evidence_share", "bootstrap_stability",
                "leave_study_out_best_jaccard_savage", "extreme_tail_MWU_P_vs_genome", "pathway_labels"]].to_string(index=False))
    print(f"\nunassigned genes {len(unassigned)} carrying {unassigned_w / total_w:.1%} of evidence")
    print("evidence captured by top 5/10/20 modules:", cover)
    print(tail_engagement().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
