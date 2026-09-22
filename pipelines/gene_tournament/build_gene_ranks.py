#!/usr/bin/env python3
"""Sprint 3, Parts B, D, E, F, J -- per-dimension gene ranks, each kept separate.

Nothing here is combined into a score. Every output is one dimension, with the evidence
it rests on and the limits of that evidence in the same row. Consensus is Part N's job,
and it is done by rank aggregation over these files, not by weighting them.

Inputs (all produced earlier in the sprint, all with provenance)
-----------------------------------------------------------------
* MAGMA gene analyses, 10 kb window, 1000G EUR LD:
    Davies 2018 general cognitive function, open subset, N=282,014   (VERIFIED by re-run)
    Davies 2018, 0 kb window                                           (window sensitivity)
    Savage 2018 intelligence, N~269,867                                (overlapping-sample
                                                                        reproducibility --
                                                                        both contain UKB)
    UKB fluid-intelligence item FI4 "positional arithmetic", N~115k    (objective maths proxy)
* GWAS Catalog strict-tier evidence (master_gene_universe.parquet + study_classification)
* LD blocks from MAGMA gene-gene correlations (ld_loci.parquet)
* Developmental classification (GTEx v10 + BrainSpan)
* ClinGen dosage curation (FTP, GRCh38, 2026-09-22)
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

DATA = REPO_ROOT / "data" / "gene_tournament"
OUT = REPO_ROOT / "reports" / "gene_tournament"
MAGMA_DIR = sorted((REPO_ROOT / "data" / "raw" / "magma_sprint3").glob("*/"))[-1]  # committed copies
RAW_MAGMA = sorted((REPO_ROOT / "data" / "raw" / "magma_x01").glob("*/"))[-1]

COLUMN_NOTES = {
    "direct_cognition_rank.effect_direction": (
        "NOT_MEANINGFUL_AT_GENE_LEVEL: catalog betas refer to different variants and effect "
        "alleles across studies; a gene has no sign until a colocalised molecular effect gives it one."),
    "direct_cognition_rank.cross_study_heterogeneity": (
        "NOT_COMPUTABLE: needs independent gene-level statistics; the two open meta-analyses "
        "(Davies 2018, Savage 2018) both contain UK Biobank."),
    "direct_cognition_rank.number_of_independent_cohorts_upper_bound": (
        "Distinct independence units (sorted cohort list, else PubMed ID) among STRICT-tier catalog "
        "studies. An upper bound: differently labelled cohort sets can share people."),
}
DIRECT_DOMAINS = ["general_cognition", "fluid_reasoning", "working_memory",
                  "processing_speed", "memory", "executive_function",
                  "mathematical_cognition", "spatial_cognition"]


def genes_out(path: Path, tag: str) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=r"\s+", comment="#")
    return frame[["GENE", "CHR", "START", "STOP", "NSNPS", "ZSTAT", "P"]].rename(
        columns={"NSNPS": f"NSNPS_{tag}", "ZSTAT": f"Z_{tag}", "P": f"P_{tag}"})


def load_core() -> pd.DataFrame:
    dav = genes_out(RAW_MAGMA / "davies2018_10kb.genes.out", "dav")
    dav0 = genes_out(RAW_MAGMA / "davies2018_0kb.genes.out", "dav0")[["GENE", "Z_dav0", "P_dav0"]]
    sav = genes_out(MAGMA_DIR / "savage2018_intelligence_10kb.genes.out", "sav")[["GENE", "Z_sav", "P_sav"]]
    fi4 = genes_out(MAGMA_DIR / "fi4_arithmetic_10kb.genes.out", "fi4")[["GENE", "Z_fi4", "P_fi4"]]
    ext = genes_out(MAGMA_DIR / "zabaneh_extremeIQ_10kb.genes.out", "ext")[["GENE", "Z_ext", "P_ext"]]
    gmap = pd.read_csv(RAW_MAGMA / "gene_id_map.tsv", sep="\t")[
        ["GENE", "current_symbol", "ensembl_gene_id", "bp_length"]]
    ld = pd.read_parquet(DATA / "ld_loci.parquet")
    core = (dav.merge(gmap, on="GENE", how="left").merge(ld, on="GENE", how="left")
            .merge(dav0, on="GENE", how="left").merge(sav, on="GENE", how="left")
            .merge(fi4, on="GENE", how="left").merge(ext, on="GENE", how="left"))
    core = core.rename(columns={"current_symbol": "gene", "GENE": "entrez_id"})
    rep = json.loads((RAW_MAGMA / "REPLICATION_CHECK.json").read_text())
    unstable = set(rep["monte_carlo_instability"]["genes_changing_significance"])
    core["monte_carlo_unstable_significance"] = core.entrez_id.astype(str).isin(unstable)
    return core


def load_catalog() -> pd.DataFrame:
    u = pd.read_parquet(DATA / "master_gene_universe.parquet")
    u = u[u.symbol_resolution.isin(["approved_symbol", "alias_or_previous_symbol"])]
    u = u[u.entrez_id.astype(str).str.len() > 0].copy()
    u["entrez_id"] = pd.to_numeric(u.entrez_id, errors="coerce")
    u = u.dropna(subset=["entrez_id"]).sort_values("n_strict_studies", ascending=False)
    return u.drop_duplicates("entrez_id")


def strict_units_by_channel(u: pd.DataFrame) -> dict[int, dict[str, set[str]]]:
    tiers = pd.read_csv(DATA / "study_classification.csv")
    strict = tiers[tiers.tier == "direct_strict"].set_index("accession_id").independence_unit.to_dict()
    out: dict[int, dict[str, set[str]]] = {}
    for _, row in u.iterrows():
        chans = {}
        for dom in DIRECT_DOMAINS:
            studies = str(row.get(f"{dom}__studies") or "")
            units = {strict[s] for s in studies.split("|") if s in strict}
            if units:
                chans[dom] = units
        out[int(row.entrez_id)] = chans
    return out


def bonferroni(p: pd.Series) -> float:
    return 0.05 / p.notna().sum()


# ----------------------------------------------------------------------- Part B --
def part_b(core: pd.DataFrame, cat: pd.DataFrame) -> pd.DataFrame:
    b_dav, b_sav = bonferroni(core.P_dav), bonferroni(core.P_sav)
    t = core.merge(cat[["entrez_id", "hgnc_id", "locus_group", "n_strict_studies",
                        "n_strict_independence_units", "n_strict_ukb_free_units",
                        "n_direct_studies", "n_mtag_studies", "n_clinical_ageing_studies",
                        "n_excluded_ea_cross_trait_studies", "best_strict_p",
                        "n_strict_increase", "n_strict_decrease"]],
                   on="entrez_id", how="left")
    for col in ("n_strict_studies", "n_strict_independence_units", "n_strict_ukb_free_units",
                "n_direct_studies", "n_mtag_studies", "n_clinical_ageing_studies",
                "n_excluded_ea_cross_trait_studies"):
        t[col] = t[col].fillna(0).astype(int)
    t["bonferroni_davies"] = t.P_dav < b_dav
    t["bonferroni_savage"] = t.P_sav < b_sav
    t["window_0kb_agrees"] = np.where(t.P_dav0.isna(), "gene_absent_at_0kb",
                                      np.where((t.P_dav0 < b_dav) == t.bonferroni_davies,
                                               "same_call", "call_changes"))

    def status(r):
        if r.bonferroni_davies and r.bonferroni_savage and r.n_strict_independence_units >= 3:
            return "strong"
        if r.bonferroni_davies and (r.bonferroni_savage or r.n_strict_independence_units >= 2):
            return "moderate"
        if r.bonferroni_davies:
            return "single_analysis"
        if pd.notna(r.best_strict_p) and r.best_strict_p < 5e-8:
            return "catalog_only_genome_wide"
        return "none"
    t["replication_status"] = t.apply(status, axis=1)
    # Codes, not sentences: an explanation repeated in 18,418 rows made this file exceed
    # the 5 MiB commit limit. The explanations live once, in COLUMN_NOTES.
    t["effect_direction"] = "NOT_MEANINGFUL_AT_GENE_LEVEL"
    t["cross_study_heterogeneity"] = "NOT_COMPUTABLE"
    t["davies_savage_z_gap"] = (t.Z_dav - t.Z_sav).abs()
    t["direct_cognition_rank"] = t.P_dav.rank(method="min").astype("Int64")
    reps = t.loc[t.groupby("ld_block_r0.2").P_dav.idxmin()]
    t["is_ld_block_lead"] = t.index.isin(reps.index)
    t["ld_block_rank"] = np.nan
    block_rank = reps.P_dav.rank(method="min").astype(int)
    t.loc[reps.index, "ld_block_rank"] = block_rank
    cols = ["gene", "entrez_id", "hgnc_id", "ensembl_gene_id", "CHR", "START", "STOP",
            "ld_block_r0.2", "is_ld_block_lead", "ld_block_rank", "direct_cognition_rank",
            "Z_dav", "P_dav", "bonferroni_davies", "monte_carlo_unstable_significance",
            "Z_dav0", "P_dav0", "window_0kb_agrees", "Z_sav", "P_sav", "bonferroni_savage",
            "davies_savage_z_gap", "n_strict_studies", "n_strict_independence_units",
            "n_strict_ukb_free_units", "n_direct_studies", "n_mtag_studies",
            "n_clinical_ageing_studies", "n_excluded_ea_cross_trait_studies",
            "best_strict_p", "effect_direction", "cross_study_heterogeneity",
            "replication_status", "bp_length"]
    out = t[cols].rename(columns={"Z_dav": "gene_Z", "P_dav": "gene_P",
                                  "Z_dav0": "gene_Z_0kb", "P_dav0": "gene_P_0kb",
                                  "Z_sav": "gene_Z_savage", "P_sav": "gene_P_savage",
                                  "n_strict_studies": "number_of_direct_cognition_studies",
                                  "n_strict_independence_units": "number_of_independent_cohorts_upper_bound",
                                  "best_strict_p": "best_P"})
    return out.sort_values("gene_P")


# ----------------------------------------------------------------------- Part D --
def part_d(core: pd.DataFrame, cat: pd.DataFrame, units: dict) -> pd.DataFrame:
    rows = []
    ids = set(core.entrez_id) | set(cat.entrez_id.astype(int))
    sym = dict(zip(core.entrez_id, core.gene)) | {int(k): v for k, v in zip(cat.entrez_id, cat.approved_symbol)}
    for eid in ids:
        chans = units.get(int(eid), {})
        g = nx.Graph()
        for dom, us in chans.items():
            for u_ in us:
                g.add_edge(("d", dom), ("u", u_))
        matching = nx.bipartite.maximum_matching(g, top_nodes={n for n in g if n[0] == "d"}) if g.number_of_edges() else {}
        n_indep = sum(1 for k in matching if k[0] == "d")
        row = {"gene": sym.get(eid), "entrez_id": eid,
               "n_domains_with_strict_evidence": len(chans),
               "n_domains_supported_by_distinct_cohort_units": n_indep,
               "domains": "|".join(sorted(chans)),
               "learning_measures": "NOT_POPULATED (no open learning-measure GWAS in scope)"}
        for dom in DIRECT_DOMAINS:
            row[f"{dom}_strict_units"] = len(chans.get(dom, ()))
        rows.append(row)
    d = pd.DataFrame(rows)
    d = d.merge(core[["entrez_id", "Z_dav", "P_dav", "Z_fi4", "Z_ext"]], on="entrez_id", how="left")
    d["breadth_rank"] = d.n_domains_supported_by_distinct_cohort_units.rank(
        ascending=False, method="min").astype(int)
    return d.sort_values(["n_domains_supported_by_distinct_cohort_units",
                          "n_domains_with_strict_evidence", "P_dav"],
                         ascending=[False, False, True])


# ----------------------------------------------------------------------- Part E --
def catalog_math(core: pd.DataFrame) -> pd.DataFrame:
    """Best catalog p per gene for each math measure TYPE, never pooled across types."""
    import gzip
    kinds = {"GCST006573": "self_report", "GCST006574": "course_taking",
             "GCST006569": "mtag_excluded", "GCST006568": "mtag_excluded"}
    best: dict[tuple[str, str], float] = {}
    for path in glob.glob(str(REPO_ROOT / "data/raw/gwas_catalog_tournament/*/EFO_0004875_*.json.gz")):
        for a in (json.loads(gzip.open(path, "rt").read()).get("_embedded") or {}).get("associations") or []:
            kind = kinds.get(a.get("accession_id"), "objective_small_sample")
            try:
                p = float(a.get("p_value"))
            except (TypeError, ValueError):
                continue
            for g in a.get("mapped_genes") or []:
                key = (g, kind)
                if key not in best or p < best[key]:
                    best[key] = p
    frame = pd.DataFrame([{"gene": g, "kind": k, "p": p} for (g, k), p in best.items()])
    return frame.pivot_table(index="gene", columns="kind", values="p", aggfunc="min").reset_index()


def part_e(core: pd.DataFrame) -> pd.DataFrame:
    t = core[["gene", "entrez_id", "ld_block_r0.2", "Z_dav", "P_dav", "Z_fi4", "P_fi4"]].dropna(
        subset=["Z_fi4"]).copy()
    fit = stats.linregress(t.Z_dav, t.Z_fi4)
    t["math_residual_after_g"] = t.Z_fi4 - (fit.intercept + fit.slope * t.Z_dav)
    t["math_residual_z"] = t.math_residual_after_g / t.math_residual_after_g.std()
    b_fi4, b_dav = bonferroni(t.P_fi4), bonferroni(t.P_dav)

    def klass(r):
        if r.P_fi4 < b_fi4 and r.P_dav > 0.05:
            return "math_specific"
        if r.P_dav < b_dav and r.P_fi4 < 0.05 and r.Z_fi4 > 0:
            return "shared_g_math"
        if r.P_dav < b_dav and r.Z_fi4 <= 0:
            return "general_only"
        return "unresolved"
    t["math_class"] = t.apply(klass, axis=1)
    cm = catalog_math(core)
    t = t.merge(cm, on="gene", how="left")
    t = t.rename(columns={"Z_fi4": "A_raw_math_Z_objective_item", "P_fi4": "A_raw_math_P_objective_item",
                          "Z_dav": "B_g_Z", "P_dav": "B_g_P",
                          "math_residual_after_g": "C_math_residual_after_g"})
    for col in ("self_report", "course_taking", "objective_small_sample", "mtag_excluded"):
        if col in t:
            t = t.rename(columns={col: f"A_catalog_{col}_best_p"})
    t["math_rank_A_raw"] = t.A_raw_math_P_objective_item.rank(method="min").astype(int)
    t["math_rank_C_residual"] = t.math_residual_z.rank(ascending=False, method="min").astype(int)
    COLUMN_NOTES["math_gene_rank.C_model"] = (
        f"C = FI4 Z - ({fit.intercept:.3f} + {fit.slope:.3f} x g Z); C never replaces A. FI4 is one "
        "timed UKB arithmetic item: objective but low-reliability and g-saturated; FI4 and the g "
        "GWAS share UKB participants, so their noise is correlated and C is conservative.")
    return t.sort_values("A_raw_math_P_objective_item")


# ----------------------------------------------------------------------- Part F --
def part_f(b: pd.DataFrame) -> pd.DataFrame:
    top = b[b.bonferroni_davies].copy()
    top["within_family_status"] = "NOT_COMPUTABLE_WITH_CURRENT_ACCESS"
    top["reason"] = ("Howe 2022 within-sibship cognition GWAS (GCST90133149, N<=34,534) has "
                     "0 associations in the GWAS Catalog and its summary statistics sit "
                     "behind OpenGWAS authentication (HTTP 401 anonymously). Not registered "
                     "for, per project rule.")
    top["published_population_to_within_sibship_shrinkage_cognition"] = "22% (95% CI 6-37%)"
    top["published_snp_h2_cognition_population_vs_within_sibship"] = "0.24 -> 0.14"
    top["what_absence_means"] = "ABSENCE OF MEASUREMENT. Not evidence of confounding, not evidence against."
    top["within_family_rank"] = pd.NA
    return top[["gene", "entrez_id", "gene_P", "within_family_status", "within_family_rank",
                "reason", "published_population_to_within_sibship_shrinkage_cognition",
                "published_snp_h2_cognition_population_vs_within_sibship", "what_absence_means"]]


# ----------------------------------------------------------------------- Part J --
def part_j(b: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {"evidence_id": "POSGEN:2q12.3_duplication", "variant_class": "rare duplication (CNV)",
         "locus": "chr2:109,510,927-110,376,563 (hg19); 2q12.3 in hg19, 2q13 in hg38",
         "genes": "EDAR|SH3RF3|SEPTIN10|SOWAHC", "direction": "POSITIVE (higher cognition)",
         "effect": "z=0.434 (~6.5 IQ points); p=7.58e-3; 36 carriers / 258,292",
         "dosage_consistency": "reciprocal deletion z=-0.526 p=0.058 (12 carriers); per-copy p=2.65e-3",
         "replication": "none located", "clingen": "all four genes uncurated for dosage",
         "status": "watchlist_unreplicated; nominal (not Bonferroni across 596 duplicated genes)",
         "source": "PMID 39667348, full text PMC11701252 read 2026-09-22",
         "rule": "the only positive-direction human perturbation in scope"},
        {"evidence_id": "CODEX:RP02", "variant_class": "rare family variant",
         "locus": "RIMS1 R844H (CORD7)", "genes": "RIMS1",
         "direction": "reported enhanced verbal/executive performance in one kindred",
         "effect": "single kindred", "dosage_consistency": "n/a",
         "replication": "none; 2022 follow-up is Drosophila", "clingen": "n/a",
         "status": "hypothesis_only", "source": "Codex watchlist; doi 10.1136/jmg.2006.047407",
         "rule": "one family is not a population effect"},
        {"evidence_id": "CODEX:RP03", "variant_class": "common haplotype",
         "locus": "KL-VS", "genes": "KL", "direction": "mixed",
         "effect": "initial positive (n=718) vs large independent nulls (n=1,812; 320,861)",
         "dosage_consistency": "n/a", "replication": "failed at scale", "clingen": "n/a",
         "status": "not_promoted", "source": "Codex watchlist RP03",
         "rule": "consistent with the Sprint-2 KL downgrade"},
        {"evidence_id": "CODEX:RP04", "variant_class": "linkage + common SNP follow-up",
         "locus": "6q24 exceptional episodic memory", "genes": "unresolved (MOXD1 not promoted)",
         "direction": "positive (exceptional memory families)", "effect": "nominal SNP meta",
         "dosage_consistency": "n/a", "replication": "nominal only", "clingen": "n/a",
         "status": "domain_lead_only", "source": "Codex watchlist RP04", "rule": ""},
        {"evidence_id": "CODEX:RP05", "variant_class": "rare PTV burden",
         "locus": "8 exome-wide genes (Chen 2023)", "genes": "aggregate",
         "direction": "NEGATIVE (loss of function lowers cognition/EA)",
         "effect": "aggregate adverse burden", "dosage_consistency": "n/a",
         "replication": "aggregate replicated", "clingen": "n/a",
         "status": "architecture evidence, NOT positive",
         "source": "Codex watchlist RP05; doi 10.1038/s41588-023-01398-8",
         "rule": "LoF impairment is never inverted into GoF enhancement"},
    ]
    # ClinGen triplosensitivity among Bonferroni genes: a SAFETY signal, not a positive one.
    cg_path = sorted(glob.glob(str(REPO_ROOT / "data/raw/clingen/*/ClinGen_gene_curation_list_GRCh38.tsv")))[-1]
    cg = pd.read_csv(cg_path, sep="\t", skiprows=5)
    cg.columns = [c.lstrip("#").strip() for c in cg.columns]
    sig = set(b[b.bonferroni_davies].gene.dropna())
    hit = cg[cg["Gene Symbol"].isin(sig)]
    for _, r in hit.iterrows():
        rows.append({"evidence_id": f"CLINGEN:{r['Gene Symbol']}", "variant_class": "dosage curation",
                     "locus": r["cytoBand"], "genes": r["Gene Symbol"],
                     "direction": "NOT a positive perturbation",
                     "effect": f"HI score {r['Haploinsufficiency Score']}; TS score {r['Triplosensitivity Score']}",
                     "dosage_consistency": "", "replication": "", "clingen": "curated",
                     "status": "safety/dosage annotation only",
                     "source": f"ClinGen FTP {Path(cg_path).parent.name}",
                     "rule": "HI=3 or TS=3 is a dosage-harm finding; scores 30/40 are categorical "
                             "flags (AR / dosage sensitivity unlikely), not ordinal"})
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    core, cat = load_core(), load_catalog()
    units = strict_units_by_channel(cat)
    b = part_b(core, cat); b.to_csv(OUT / "direct_cognition_rank.csv", index=False)
    d = part_d(core, cat, units); d.to_csv(OUT / "cognitive_breadth.csv", index=False)
    e = part_e(core); e.to_csv(OUT / "math_gene_rank.csv", index=False)
    f = part_f(b); f.to_csv(OUT / "within_family_rank.csv", index=False)
    j = part_j(b); j.to_csv(OUT / "positive_human_perturbations.csv", index=False)
    summary = {
        "built_at": utc_now(),
        "part_b": {"n_genes": int(len(b)), "n_bonferroni_davies": int(b.bonferroni_davies.sum()),
                   "n_ld_blocks_bonferroni": int(b[b.bonferroni_davies]["ld_block_r0.2"].nunique()),
                   "replication_status": b.replication_status.value_counts().to_dict(),
                   "n_monte_carlo_unstable": int(b.monte_carlo_unstable_significance.sum()),
                   "window_0kb": b[b.bonferroni_davies].window_0kb_agrees.value_counts().to_dict()},
        "part_d": {"n_genes": int(len(d)),
                   "max_distinct_unit_domains": int(d.n_domains_supported_by_distinct_cohort_units.max()),
                   "distribution": d.n_domains_supported_by_distinct_cohort_units.value_counts().sort_index().to_dict()},
        "part_e": {"math_class": e.math_class.value_counts().to_dict(),
                   "n_fi4_bonferroni": int((e.A_raw_math_P_objective_item < bonferroni(e.A_raw_math_P_objective_item)).sum())},
        "part_f": "NOT_COMPUTABLE_WITH_CURRENT_ACCESS",
        "column_notes": COLUMN_NOTES,
        "part_j": {"n_rows": int(len(j)), "n_positive_direction": 1},
    }
    (OUT / "gene_ranks_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
