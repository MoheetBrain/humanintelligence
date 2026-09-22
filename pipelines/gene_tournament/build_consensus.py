#!/usr/bin/env python3
"""Sprint 3, Parts G, H, I, M, N, O -- directionality, control sets, consensus, top systems.

Part G  fine_mapping_support.csv       Open Targets credible sets + L2G for 400 candidates
Part H  adult_brain_directionality.csv brain-QTL x GWAS colocalisation, EA separated,
                                       trait polarity applied, direction stated only when
                                       the API's own concordance field supports it
Part I  natural_intelligence_rank / adult_modifiable_cognition_rank (inside the two TOP50s)
Part M  minimal_control_set.csv        weighted set cover vs centrality vs controllability
Part N  TOP50_HUMAN_COGNITION_GENES.csv / TOP50_ADULT_MODIFIABLE_GENES.csv
Part O  TOP10_COGNITION_MODULES.csv

The consensus is rank aggregation, never a weighted sum (see rank_aggregation.py). Every
row carries its rank INTERVAL and the dimension that carries it, so an unstable rank looks
unstable.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "pipelines" / "gene_tournament"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402
from rank_aggregation import borda_score, normalised_ranks, pareto_front, rra_score  # noqa: E402

DATA = REPO_ROOT / "data" / "gene_tournament"
OUT = REPO_ROOT / "reports" / "gene_tournament"
SEED = 20260922
POSITIVE_CNV_GENES = {"EDAR", "SH3RF3", "SEPTIN10", "SOWAHC"}

# ------------------------------------------------------------------ trait handling ----
# "Highest math class taken" is course-taking -- an attainment proxy, not a cognitive test.
# It slipped through as direct cognition on the first run and was caught on audit.
EA_RX = re.compile(r"educat|qualification|college|degree|school|years of|a levels|gcse|"
                   r"class taken|course", re.I)
CROSS_RX = re.compile(r"factor analysis|multivariate|pleiotrop|\bor\b|MTAG", re.I)
CLIN_RX = re.compile(r"alzheimer|dementia|schizo|bipolar|autis|adhd|parkinson|decline|impair", re.I)
NEG_POLARITY_RX = re.compile(r"reaction time|time to complete|decline|impair|errors|incorrect", re.I)
COG_RX = re.compile(r"cognit|intellig|fluid|reasoning|memory|reaction time|processing speed|"
                    r"executive|numeric|arithmetic|math|verbal|trail making|symbol digit|pairs matching", re.I)


def classify_trait(trait: str) -> str:
    t = str(trait or "")
    if EA_RX.search(t):
        return "educational_attainment_proxy"
    if CROSS_RX.search(t):
        return "cross_trait_or_factor"
    if CLIN_RX.search(t):
        return "clinical_or_ageing"
    if COG_RX.search(t):
        return "direct_cognition"
    return "other"


def coloc_strength(row) -> float:
    """One comparable number per colocalisation: H4 for COLOC, CLPP-derived for eCAVIAR.

    CLPP is not a posterior of shared causality on the H4 scale; it is mapped to bands
    (>=0.1 strong, >=0.01 moderate) and the band's floor is used, which understates it.
    """
    method = str(row.get("colocalisation_method") or "")
    if "ECAVIAR" in method.upper():
        c = row.get("clpp")
        if pd.isna(c):
            return np.nan
        return 0.9 if c >= 0.1 else (0.6 if c >= 0.01 else 0.1)
    return row.get("h4")


def part_g_h(cand: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cs = pd.read_csv(DATA / "opentargets_credible_sets.csv")
    # The fetcher's "cognition" file is 178 MB and admits EA traits. It is compacted here to
    # brain QTL rows whose GWAS side is direct cognition or EA (kept separately), which is
    # what Part H uses; the compact file is committed so Part H rebuilds offline.
    big, compact = DATA / "opentargets_cognition_coloc.csv", DATA / "opentargets_brain_coloc_compact.csv.gz"
    if big.exists():
        co = pd.read_csv(big)
        co = co[co.qtl_is_brain == True].copy()  # noqa: E712
        co["trait_class"] = co.gwas_trait.map(classify_trait)
        keep = ["GENE", "current_symbol", "h4", "h3", "clpp", "colocalisation_method", "qtl_study_type",
                "qtl_study_id", "qtl_biosample_name", "qtl_is_brain", "qtl_molecular_trait", "qtl_beta",
                "gwas_study_id", "gwas_trait", "gwas_pubmed_id", "gwas_beta", "gwas_variant_rsid",
                "beta_ratio_sign_average", "trait_class"]
        co = co[co.trait_class.isin(["direct_cognition", "educational_attainment_proxy"])][keep]
        co.to_csv(compact, index=False, compression="gzip")
    co = pd.read_csv(compact)
    co["trait_class"] = co.gwas_trait.map(classify_trait)
    co["strength"] = co.apply(coloc_strength, axis=1)
    co["polarity"] = np.where(co.gwas_trait.astype(str).str.contains(NEG_POLARITY_RX), -1, 1)

    # Part G comes from fetch_gwas_credible_sets.py (study-first GWAS credible sets + L2G).
    # Read, never rewritten here: the gene-first QTL route cannot see GWAS credible sets.
    g = pd.read_csv(OUT / "fine_mapping_support.csv")
    sym2eid = dict(zip(cand.current_symbol, cand.GENE))
    core_map = pd.read_csv(OUT / "direct_cognition_rank.csv")[["gene", "entrez_id"]].dropna()
    sym2eid.update(dict(zip(core_map.gene, core_map.entrez_id)))
    g["entrez_id"] = g.gene.map(sym2eid)

    rows = []
    for (eid, sym), grp in co.groupby(["GENE", "current_symbol"]):
        brain = grp[grp.qtl_is_brain == True]  # noqa: E712
        direct = brain[brain.trait_class == "direct_cognition"]
        ea = brain[brain.trait_class == "educational_attainment_proxy"]
        best = direct.sort_values("strength", ascending=False).head(1)
        rec = {"entrez_id": eid, "gene": sym,
               "n_brain_coloc_direct_cognition": int((direct.strength >= 0.8).sum()),
               "n_brain_coloc_EA_proxy_only": int((ea.strength >= 0.8).sum()),
               "max_strength_brain_direct_cognition": float(direct.strength.max()) if len(direct) else np.nan,
               "max_strength_brain_EA_proxy": float(ea.strength.max()) if len(ea) else np.nan}
        if len(best):
            b = best.iloc[0]
            strength = float(b.strength)
            klass = ("strong" if strength >= 0.8 else "moderate" if strength >= 0.5 else "weak")
            # DIRECTION RULE (tightened on audit): the first version read direction from the
            # single best colocalisation, and for most genes that sign was contradicted by
            # the gene's other brain colocalisations (COL16A1: 15% of 272 concordant). Now:
            # gene-level expression/protein QTLs only, strong colocalisations only, trait
            # polarity applied, and >= 80% agreement across >= 3 of them.
            gl = direct[(direct.strength >= 0.8) & direct.qtl_study_type.astype(str).str.match(r"(eqtl|pqtl)$")
                        & ~direct.qtl_molecular_trait.astype(str).str.contains(r"_\d+_\d+$")
                        & direct.beta_ratio_sign_average.notna()]
            signs = np.sign(gl.beta_ratio_sign_average) * gl.polarity
            n_gl = int(len(signs))
            agree = float(max((signs > 0).mean(), (signs < 0).mean())) if n_gl else float("nan")
            majority = (1 if (signs > 0).mean() >= 0.5 else -1) if n_gl else 0
            resolved = bool(n_gl >= 3 and agree >= 0.8)
            if resolved:
                direction = ("cognition-increasing allele -> HIGHER " if majority > 0 else
                             "cognition-increasing allele -> LOWER ") + "gene expression in adult brain"
            elif n_gl:
                direction = f"UNRESOLVED: {n_gl} strong gene-level brain QTL colocs, {agree:.0%} sign agreement"
            else:
                direction = "UNRESOLVED: no strong gene-level (non-exon) brain eQTL/pQTL colocalisation"
            inversion = bool(str(b.qtl_molecular_trait).find("_17_4") >= 0 or sym in {
                "NSF", "KANSL1", "LRRC37A", "ARL17A", "ARL17B", "MAPT", "CRHR1", "PLEKHM1", "STH", "LRRC37A2"})
            rec.update({"colocalisation_class": klass, "brain_region": b.qtl_biosample_name,
                        "cell_type": ("single-cell QTL" if "sc" in str(b.qtl_study_type) else "bulk tissue (no cell type)"),
                        "molecular_phenotype": f"{b.qtl_study_type}: {b.qtl_molecular_trait}",
                        "qtl_study": b.qtl_study_id, "gwas_trait": b.gwas_trait, "gwas_pubmed": b.gwas_pubmed_id,
                        "gwas_variant_rsid": b.gwas_variant_rsid,
                        "method": b.colocalisation_method, "h4": b.h4, "clpp": b.clpp,
                        "n_strong_gene_level_brain_colocs": n_gl, "sign_agreement": agree,
                        "direction_statement": direction, "direction_resolved": resolved,
                        "cognition_increasing_allele_expression": ("higher" if majority > 0 else "lower") if resolved else "unresolved",
                        "locus_caveat": ("17q21.31 inversion haplotype: eQTLs of many genes share one signal; "
                                         "colocalisation is not gene-specific") if inversion else "",
                        "effect_consistency": f"{agree:.0%} of {n_gl} strong gene-level brain colocs agree" if n_gl else "n/a"})
        else:
            rec.update({"colocalisation_class": ("EA_proxy_only" if len(ea) else "none_with_direct_cognition"),
                        "direction_resolved": False,
                        "direction_statement": "no brain QTL colocalisation with a DIRECT cognition GWAS"})
        rows.append(rec)
    h = pd.DataFrame(rows)
    h["forbidden_inference"] = "association -> activate gene; expression direction -> efficacy"
    queried = set(cs.GENE)
    missing = cand[~cand.GENE.isin(queried)]
    h = pd.concat([h, pd.DataFrame({"entrez_id": missing.GENE, "gene": missing.current_symbol,
                                    "colocalisation_class": "NOT_QUERIED", "direction_resolved": False})],
                  ignore_index=True)
    return g, h


def module_rank(mods: pd.DataFrame) -> pd.DataFrame:
    m = mods.copy()
    # Tail engagement is tested against OTHER cognition genes (module_tail_engagement.csv),
    # not the genome: module genes were selected on Davies significance, so a genome-level
    # comparison credits every module with continuity it inherited from that selection.
    te = pd.read_csv(OUT / "module_tail_engagement.csv").set_index("module")
    m["tail_engagement_P_vs_other_cognition_genes"] = m.module.map(te.MWU_P_more_tail_engaged)
    m["tail_engagement_bonferroni"] = m.module.map(te.bonferroni)
    m["extreme_tail_vs_genome_NOTE"] = "inherited from gene selection (continuity); not module-specific"
    m["artefact_flag"] = m.pathway_labels.str.contains("olfactory", case=False)
    dims = {"weighted_evidence_share": True, "tail_engagement_P_vs_other_cognition_genes": False,
            "label_best_enrichment_P_conditioned": False, "bootstrap_stability": True,
            "leave_study_out_best_jaccard_savage": True, "n_independent_loci": True,
            "mean_distinct_unit_domains": True}
    R = np.column_stack([normalised_ranks(m[c].to_numpy(float), hib) for c, hib in dims.items()])
    m["module_rra_p"] = [rra_score(r)[1] for r in R]
    m.loc[m.artefact_flag, "module_rra_p"] = 1.0
    m["module_rank"] = m.module_rra_p.rank(method="min").astype(int)
    return m.sort_values("module_rank")


def part_m(mods: pd.DataFrame, dev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    mem = pd.read_csv(DATA / "module_membership.csv").dropna(subset=["gene"])
    # "Strongly supported": stable, reproducible from Savage, not an artefact, AND either
    # label-enriched after conditioning or more tail-engaged than other cognition genes.
    strong = mods[(mods.bootstrap_stability >= 0.5) & (mods.leave_study_out_best_jaccard_savage >= 0.2)
                  & (~mods.artefact_flag)
                  # Same bar as the rest of the sprint: GLOBAL FDR, not a nominal label P.
                  # (A first version used nominal P and admitted M06 and M09, whose label
                  # sets have global FDR 0.74 and 0.36.)
                  & ((mods.label_best_enrichment_FDR_global < 0.05)
                     | (mods.tail_engagement_bonferroni < 0.05))]
    targets = dict(zip(strong.module, strong.weighted_evidence_share))
    st_path = sorted(glob.glob(str(REPO_ROOT / "data/raw/string/*/string_network_fdr01_genes_score400.tsv.gz")))[-1]
    t = pd.read_csv(st_path, sep="\t", compression="gzip")
    G = nx.Graph()
    G.add_nodes_from(mem.gene)
    G.add_weighted_edges_from(zip(t.preferredName_A, t.preferredName_B, t.score))
    hi = nx.Graph([(a, b) for a, b, s in zip(t.preferredName_A, t.preferredName_B, t.score) if s >= 0.7])
    gmod = dict(zip(mem.gene, mem.module))
    gene_p = dict(zip(mem.gene, mem.gene_P))
    msize = mem.module.value_counts().to_dict()
    adult_ok = set(dev[(dev.adult_expressed == True) & (dev.developmental_class != "PRENATAL_DOMINANT")].gene_symbol)  # noqa: E712

    covers = {}
    for gene in mem.gene:
        c = set()
        if gmod.get(gene) in targets:
            c.add(gmod[gene])
        if gene in hi:
            nb = [gmod.get(n) for n in hi.neighbors(gene)]
            for mod in targets:
                need = max(3, int(0.05 * msize.get(mod, 0)))
                if sum(1 for x in nb if x == mod) >= need:
                    c.add(mod)
        covers[gene] = c

    def greedy(pool):
        chosen, covered, curve = [], set(), []
        while True:
            gain = {g: sum(targets[m] for m in covers[g] - covered) for g in pool if g not in chosen}
            if not gain or max(gain.values()) <= 0:
                break
            # Coverage ties across every member of a module, so the pick within a module is
            # arbitrary with respect to coverage. The first version broke ties on SYMBOL
            # LENGTH and chose STH. Ties now go to the strongest association (lowest P).
            best = max(gain, key=lambda g: (gain[g], -gene_p.get(g, 1.0), str(g)))
            chosen.append(best)
            covered |= covers[best]
            curve.append(sum(targets[m] for m in covered) / sum(targets.values()))
        return chosen, curve

    set_all, curve_all = greedy(list(mem.gene))
    set_adult, curve_adult = greedy([g for g in mem.gene if g in adult_ok])
    btw = nx.betweenness_centrality(G, weight=None, seed=SEED, k=min(500, G.number_of_nodes()))
    pr = nx.pagerank(G, weight="weight")
    deg = dict(G.degree())
    ann = dict(zip(mem.gene, mem.n_annotations_in_matrix))
    rho = stats.spearmanr([deg[g] for g in mem.gene], [ann.get(g, 0) for g in mem.gene]).statistic
    # structural controllability on the bidirected graph (no directed causal graph exists)
    D = nx.DiGraph()
    for a, b in G.edges():
        D.add_edge(a, b); D.add_edge(b, a)
    B = nx.Graph()
    B.add_nodes_from([("o", n) for n in D], bipartite=0)
    B.add_nodes_from([("i", n) for n in D], bipartite=1)
    B.add_edges_from((("o", a), ("i", b)) for a, b in D.edges())
    mm = nx.bipartite.hopcroft_karp_matching(B, top_nodes=[("o", n) for n in D])
    n_match = sum(1 for k in mm if k[0] == "o")
    n_driver = max(D.number_of_nodes() - n_match, 1)

    rows = []
    for rank_, g in enumerate(set_adult, 1):
        rows.append({"method": "weighted_set_cover_adult_active", "rank": rank_, "gene": g,
                     "module": gmod.get(g), "modules_covered": "|".join(sorted(covers[g])),
                     "cumulative_evidence_coverage": curve_adult[rank_ - 1]})
    for rank_, g in enumerate(set_all, 1):
        rows.append({"method": "weighted_set_cover_any_timing", "rank": rank_, "gene": g,
                     "module": gmod.get(g), "modules_covered": "|".join(sorted(covers[g])),
                     "cumulative_evidence_coverage": curve_all[rank_ - 1]})
    for name, score in (("betweenness", btw), ("pagerank_diffusion", pr), ("degree", deg)):
        for rank_, (g, s) in enumerate(sorted(score.items(), key=lambda kv: -kv[1])[:15], 1):
            rows.append({"method": name, "rank": rank_, "gene": g, "module": gmod.get(g),
                         "score": s, "annotation_count": ann.get(g, 0)})
    rows.append({"method": "structural_controllability_bidirected", "rank": None, "gene": None,
                 "score": n_driver,
                 "note": "minimum driver nodes on the STRING graph treated as bidirected. STRING "
                         "is undirected and non-causal, so this number reflects topology only "
                         "and is NOT a count of control points."})
    summary = {"strongly_supported_modules": targets,
               "adult_active_set": set_adult, "adult_active_coverage_curve": curve_adult,
               "any_timing_set": set_all, "any_timing_coverage_curve": curve_all,
               "spearman_degree_vs_annotation_count": float(rho),
               "n_driver_nodes_bidirected": n_driver, "n_nodes": D.number_of_nodes(),
               "centrality_is_not_causality": True}
    return pd.DataFrame(rows), summary


def consensus(core, g, h, mods_ranked, dev, cons, gate_adult: bool):
    # Entrez ids with no current HGNC symbol cannot be reported by name; they are dropped
    # here and counted in consensus_summary.json rather than silently lost.
    t = core.dropna(subset=["gene"]).copy()
    t["dim_direct"] = -np.log10(t.gene_P)
    t["dim_extreme"] = t.Z_ext
    t["dim_replication"] = t.number_of_independent_cohorts_upper_bound + t.gene_Z_savage.fillna(0) / 100
    t["dim_math"] = t.Z_fi4
    gg = g.dropna(subset=["entrez_id"]).sort_values("fine_mapping_score", ascending=False).drop_duplicates("entrez_id")
    t = t.merge(gg[["entrez_id", "fine_mapping_score"]], on="entrez_id", how="left")
    t = t.merge(h[["entrez_id", "max_strength_brain_direct_cognition", "direction_resolved",
                   "direction_statement", "brain_region", "colocalisation_class"]], on="entrez_id", how="left")
    t["dim_finemap"] = t.fine_mapping_score
    t["dim_coloc"] = t.max_strength_brain_direct_cognition
    t["dim_direction"] = np.where(t.colocalisation_class.isna() | (t.colocalisation_class == "NOT_QUERIED"), np.nan,
                                  np.where(t.direction_resolved == True, 1.0, 0.0))  # noqa: E712
    dmap = {"ADULT_DYNAMIC": 3, "MIXED": 2, "ADOLESCENT": 2, "DEVELOPMENTAL": 1, "PRENATAL_DOMINANT": 0}
    dv = dev.dropna(subset=["entrez_id"]).copy()
    dv["entrez_id"] = pd.to_numeric(dv.entrez_id, errors="coerce")
    dv = dv.dropna(subset=["entrez_id"]).drop_duplicates("entrez_id")
    t = t.merge(dv[["entrez_id", "developmental_class", "adult_expressed", "adult_brain_max_tpm"]], on="entrez_id", how="left")
    t["dim_adult_mod"] = t.developmental_class.map(dmap) + np.log10(t.adult_brain_max_tpm.fillna(0) + 1) / 10
    t["dim_positive"] = np.where(t.gene.isin(POSITIVE_CNV_GENES), 1.0, np.nan)
    mem = pd.read_csv(DATA / "module_membership.csv")[["entrez_id", "module"]]
    t = t.merge(mem, on="entrez_id", how="left")
    mr = dict(zip(mods_ranked.module, mods_ranked.module_rank))
    t["dim_module"] = -t.module.map(mr)
    t = t.merge(cons, on="entrez_id", how="left")
    t["dim_safety"] = t.oe_lof_upper - np.where(t.clingen_hi3.fillna(False), 1.0, 0.0)

    # ELIGIBILITY: a gene must carry real cognition association (MAGMA gene FDR<0.05) to be
    # ranked at all. Without this floor, a dimension unrelated to cognition evidence
    # (safety, adult expression) or a noisy one could carry a gene with no association.
    p = t.gene_P.to_numpy(); o = np.argsort(p); n_ = len(p)
    q = p[o] * n_ / (np.arange(n_) + 1); q = np.minimum.accumulate(q[::-1])[::-1]
    fdr = np.empty(n_); fdr[o] = np.minimum(q, 1)
    t["gene_FDR"] = fdr
    t = t[t.gene_FDR < 0.05].copy()

    # PRIMARY dimensions: only those with >=1 gene passing their own multiple-testing
    # threshold. Extreme-tail (Zabaneh) and objective-arithmetic (FI4) have ZERO such genes;
    # their per-gene ranks are statistically indistinguishable from a permutation, and RRA
    # -- which rewards one extreme rank -- crowned them in the first run (30 of 50 genes
    # "carried by" them). They remain separately reported ranks and enter the
    # all-dimensions SENSITIVITY aggregation. RULE ADOPTED AFTER OBSERVING THAT RUN, and
    # disclosed as such. Safety is a FLAG, never a promoting dimension.
    if gate_adult:
        t = t[(t.adult_expressed == True) & (t.developmental_class != "PRENATAL_DOMINANT")  # noqa: E712
              & t.developmental_class.notna() & (t.developmental_class != "UNKNOWN")].copy()
        dims = {"direct": "dim_direct", "replication": "dim_replication", "finemap": "dim_finemap",
                "coloc": "dim_coloc", "direction": "dim_direction",
                "adult_modifiability": "dim_adult_mod", "module": "dim_module"}
    else:
        dims = {"direct": "dim_direct", "replication": "dim_replication", "finemap": "dim_finemap",
                "coloc": "dim_coloc", "positive_human": "dim_positive", "module": "dim_module"}
    sens_dims = {**dims, "extreme": "dim_extreme", "math": "dim_math"}
    Rs = np.column_stack([normalised_ranks(t[c].to_numpy(float), True) for c in sens_dims.values()])
    t["consensus_rank_all_dimensions"] = stats.rankdata([rra_score(r)[0] for r in Rs], method="min").astype(int)
    for nm, col in (("extreme", "dim_extreme"), ("math", "dim_math"), ("safety", "dim_safety")):
        t[f"rank_{nm}"] = t[col].rank(ascending=False, method="min")
    names = list(dims)
    R = np.column_stack([normalised_ranks(t[c].to_numpy(float), True) for c in dims.values()])
    rra = np.array([rra_score(r) for r in R])
    t["rra_rho"], t["rra_p"], t["n_dimensions_present"] = rra[:, 0], rra[:, 1], rra[:, 2]
    t["borda"] = [borda_score(r) for r in R]
    t["consensus_rank"] = t.rra_rho.rank(method="min").astype(int)
    t["borda_rank"] = t.borda.rank(method="min").astype(int)
    for j, nm in enumerate(names):
        t[f"rank_{nm}"] = pd.Series(R[:, j], index=t.index).rank(method="min")

    top_idx = np.argsort(t.rra_rho.to_numpy())[:600]
    lodo = np.full((len(top_idx), len(names)), np.nan)
    for j in range(len(names)):
        keep = [c for c in range(len(names)) if c != j]
        rho_all = np.array([rra_score(r[keep])[0] for r in R])
        ranks = stats.rankdata(rho_all, method="min")
        lodo[:, j] = ranks[top_idx]
    rng = np.random.default_rng(SEED)
    boot = np.full((len(top_idx), 200), np.nan)
    for b in range(200):
        cols = rng.integers(0, len(names), len(names))
        rho_b = np.array([rra_score(r[cols])[0] for r in R])
        boot[:, b] = stats.rankdata(rho_b, method="min")[top_idx]
    sub = t.iloc[top_idx].copy()
    sub["rank_interval"] = [f"{int(np.nanpercentile(boot[i], 5))}-{int(np.nanpercentile(boot[i], 95))}" for i in range(len(top_idx))]
    sub["rank_interval_upper"] = [np.nanpercentile(boot[i], 95) for i in range(len(top_idx))]
    sub["lodo_worst_rank"] = lodo.max(axis=1)
    sub["carried_by"] = [names[int(np.nanargmax(lodo[i]))] for i in range(len(top_idx))]
    front = pareto_front(np.column_stack([t.iloc[top_idx][f"rank_{n}"].to_numpy(float) for n in names]))
    sub["pareto_front"] = front
    sub = sub.sort_values("consensus_rank")
    lead = sub.loc[sub.groupby("ld_block_r0.2").consensus_rank.idxmin()].sort_values("consensus_rank")
    blockmates = sub.groupby("ld_block_r0.2").gene.apply(lambda s: "|".join(s))
    lead["ld_block_mates_in_top600"] = lead["ld_block_r0.2"].map(blockmates)
    return t, lead.head(50), names


def main() -> int:
    core = pd.read_csv(OUT / "direct_cognition_rank.csv")
    ext = pd.read_csv(OUT / "extreme_tail_rank.csv")[["GENE", "Z_ext"]].rename(columns={"GENE": "entrez_id"})
    mth = pd.read_csv(OUT / "math_gene_rank.csv")[["entrez_id", "A_raw_math_Z_objective_item", "math_class"]].rename(
        columns={"A_raw_math_Z_objective_item": "Z_fi4"})
    core = core.merge(ext, on="entrez_id", how="left").merge(mth, on="entrez_id", how="left")
    cand = pd.read_csv(DATA / "candidate_genes_for_annotation.csv")
    dev = pd.read_parquet(DATA / "developmental_classification.parquet")
    con = pd.read_csv(REPO_ROOT / "data/interim/gnomad_constraint.tsv", sep="\t").rename(columns={"GENE": "entrez_id"})
    cg = pd.read_csv(sorted(glob.glob(str(REPO_ROOT / "data/raw/clingen/*/ClinGen_gene_curation_list_GRCh38.tsv")))[-1], sep="\t", skiprows=5)
    cg.columns = [c.lstrip("#").strip() for c in cg.columns]
    hi3 = set(cg[cg["Haploinsufficiency Score"].astype(str) == "3"]["Gene ID"].astype(int))
    ts3 = set(cg[cg["Triplosensitivity Score"].astype(str) == "3"]["Gene ID"].astype(int))
    con["clingen_hi3"] = con.entrez_id.isin(hi3)
    con["clingen_ts3"] = con.entrez_id.isin(ts3)
    cons = con[["entrez_id", "oe_lof_upper", "pLI", "clingen_hi3", "clingen_ts3"]]

    g, h = part_g_h(cand)
    h.to_csv(OUT / "adult_brain_directionality.csv", index=False)

    mods = module_rank(pd.read_csv(OUT / "biological_modules.csv"))
    mset, msum = part_m(mods, dev)
    mset.to_csv(OUT / "minimal_control_set.csv", index=False)

    full_nat, top_nat, dims_nat = consensus(core, g, h, mods, dev, cons, gate_adult=False)
    full_ad, top_ad, dims_ad = consensus(core, g, h, mods, dev, cons, gate_adult=True)

    def dossier(top, names):
        tt = top.copy()
        tt["safety_flags"] = np.select(
            [tt.clingen_hi3 == True, tt.pLI >= 0.9],  # noqa: E712
            ["ClinGen haploinsufficient (HI=3): loss causes disorder", "LoF-intolerant (pLI>=0.9)"], "")
        tt["major_support"] = tt.apply(lambda r: "; ".join(x for x in [
            f"MAGMA P={r.gene_P:.1e}",
            f"Savage P={r.gene_P_savage:.1e}" if pd.notna(r.gene_P_savage) else "",
            f"{int(r.number_of_independent_cohorts_upper_bound)} strict cohort units",
            f"brain coloc {r.colocalisation_class}" if isinstance(r.colocalisation_class, str) else "",
            f"module {r.module}" if isinstance(r.module, str) else ""] if x), axis=1)
        tt["major_counterevidence"] = tt.apply(lambda r: "; ".join(x for x in [
            "0 confirmed UKB-free units" if r.n_strict_ukb_free_units == 0 else "",
            "significance depends on 10 kb window" if r.window_0kb_agrees == "call_changes" else "",
            "Monte-Carlo-unstable significance" if r.monte_carlo_unstable_significance else "",
            f"LD block shared with: {r.ld_block_mates_in_top600}" if "|" in str(r.ld_block_mates_in_top600) else "",
            f"developmental class {r.developmental_class}" if r.developmental_class in ("PRENATAL_DOMINANT", "DEVELOPMENTAL") else "",
            "no direct-cognition brain colocalisation" if r.colocalisation_class in ("none_with_direct_cognition", "EA_proxy_only") else "",
            f"rank carried by '{r.carried_by}' (LODO worst {int(r.lodo_worst_rank)})" if r.lodo_worst_rank > 150 else ""] if x), axis=1)
        tt["next_kill_test"] = tt.apply(lambda r: (
            "within-sibship direction check (needs OpenGWAS registration)" if r.number_of_independent_cohorts_upper_bound >= 3 else
            "replication in a UKB-free cohort") + ("; SuSiE-coloc on eQTL Catalogue brain data" if r.colocalisation_class != "strong" else "; test direction in a second brain QTL dataset"), axis=1)
        col = {"gene": "gene", "consensus_rank": "consensus_rank", "rank_interval": "rank_interval",
               "rank_direct": "direct_cognition_rank", "rank_extreme": "extreme_tail_rank",
               "rank_math": "math_rank", "rank_finemap": "fine_mapping_rank", "rank_coloc": "coloc_rank",
               "rank_adult_modifiability": "adult_modifiability_rank", "rank_positive_human": "positive_human_rank",
               "rank_module": "module_rank"}
        for k in list(col):
            if k not in tt:
                tt[k] = np.nan
        tt["family_rank"] = "NOT_COMPUTABLE"
        keep = ["gene", "entrez_id", "consensus_rank", "rank_interval", "rra_p", "borda_rank",
                "consensus_rank_all_dimensions",
                "pareto_front", "n_dimensions_present", "carried_by", "lodo_worst_rank"] + \
               [k for k in col if k.startswith("rank_")] + \
               ["family_rank", "safety_flags", "number_of_independent_cohorts_upper_bound",
                "n_strict_ukb_free_units", "developmental_class", "module", "colocalisation_class",
                "direction_statement", "brain_region", "ld_block_r0.2", "ld_block_mates_in_top600",
                "major_support", "major_counterevidence", "next_kill_test"]
        return tt[keep].rename(columns={k: v for k, v in col.items() if k.startswith("rank_")}).rename(
            columns={"number_of_independent_cohorts_upper_bound": "number_independent_cohorts"})

    dossier(top_nat, dims_nat).to_csv(OUT / "TOP50_HUMAN_COGNITION_GENES.csv", index=False)
    dossier(top_ad, dims_ad).to_csv(OUT / "TOP50_ADULT_MODIFIABLE_GENES.csv", index=False)

    top10 = mods[~mods.artefact_flag].head(10).copy()
    mem = pd.read_csv(DATA / "module_membership.csv")
    u = pd.read_parquet(DATA / "master_gene_universe.parquet")
    strict_map = dict(zip(pd.to_numeric(u.entrez_id, errors="coerce"), u.strict_studies.fillna("")))
    n_studies = {}
    for mod, grp in mem.groupby("module"):
        s = set()
        for e in grp.entrez_id:
            s |= set(x for x in str(strict_map.get(e, "")).split("|") if x)
        n_studies[mod] = len(s)
    top10["n_independent_studies_strict"] = top10.module.map(n_studies)
    top10["cross_species_support"] = "see comparative_top_genes.csv (orthology only; selection/convergence NOT computed)"
    top10["counterevidence"] = top10.apply(lambda r: "; ".join(x for x in [
        f"bootstrap stability {r.bootstrap_stability:.2f}" if r.bootstrap_stability < 0.6 else "",
        f"Savage re-derivation Jaccard {r.leave_study_out_best_jaccard_savage:.2f}" if r.leave_study_out_best_jaccard_savage < 0.3 else "",
        "labels not enriched after conditioning" if not (r.label_best_enrichment_P_conditioned < 0.05) else "",
        "not more tail-engaged than other cognition genes" if r.tail_engagement_P_vs_other_cognition_genes >= 0.05 else "",
        "cross-method ARI 0.19-0.24 for the whole partition"] if x), axis=1)
    top10.to_csv(OUT / "TOP10_COGNITION_MODULES.csv", index=False)

    # rank robustness summary
    def robustness(full, top):
        t50 = set(top.gene)
        b50 = set(full.sort_values("borda_rank").drop_duplicates("ld_block_r0.2").head(50).gene)
        a50 = set(full.sort_values("consensus_rank_all_dimensions").drop_duplicates("ld_block_r0.2").head(50).gene)
        return {"n_eligible_genes_FDR_lt_0.05": int(len(full)),
                "top50_overlap_rra_vs_borda": len(t50 & b50),
                "top50_overlap_primary_vs_all_dimensions": len(t50 & a50),
                "n_top50_rank_interval_upper_gt_200": int((top.rank_interval_upper > 200).sum()),
                "n_top50_on_pareto_front": int(top.pareto_front.sum()),
                "carried_by_counts": top.carried_by.value_counts().to_dict()}
    summary = {"built_at": utc_now(), "dimensions_natural": dims_nat, "dimensions_adult": dims_ad,
               "natural": robustness(full_nat, top_nat), "adult": robustness(full_ad, top_ad),
               "minimal_control_set": msum,
               "adult_gate": "adult_expressed AND developmental_class not in {PRENATAL_DOMINANT, UNKNOWN}",
               "within_family_dimension": "NOT_COMPUTABLE -- absent from every aggregation",
               "n_magma_genes_without_symbol_excluded": int(core.gene.isna().sum())}
    (OUT / "consensus_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
