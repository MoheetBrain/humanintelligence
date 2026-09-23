#!/usr/bin/env python3
"""Sprint 3.1 -- rank-dependency audit of the Sprint 3 consensus Top-50 gene lists.

The question
------------
Robust Rank Aggregation asks whether a gene ranks better across dimensions than it would
if the dimensions were unrelated. That null is only meaningful if the dimensions are
independent observations. In Sprint 3 most of them are not: direct association (MAGMA on
Davies 2018), replication (catalog units + Savage 2018), fine-mapping (credible sets of
the same studies), the GWAS half of colocalisation, and colocalisation-derived direction
all descend from UK-Biobank-containing cognition GWAS, and module membership was built on
genes SELECTED by Davies significance. RRA may therefore be counting one association
several times. This script records, per gene and per dimension, where each rank came
from, and recomputes the consensus under dependence-aware schemes.

What it does
------------
1. Reproduces the original consensus by calling ``build_consensus.part_g_h``,
   ``module_rank`` and ``consensus`` exactly as ``build_consensus.main`` does, and checks
   the reproduced Top-50s (gene order and consensus_rank) against the committed CSVs.
   ``part_g_h`` is pointed at a temporary directory holding symlinks to its two inputs,
   because with the 178 MB coloc file present it would REWRITE the committed compact
   file; nothing under data/ or reports/gene_tournament/ is written.
2. Builds a study registry with an audited UK Biobank status per GWAS accession, from
   the files only (see ``audit_ukb_status``).
3. For every gene in scope (union of both Top-50s plus 14 named genes) and every
   dimension: value, rank, lineage class (fixed vocabulary), lineage sources.
4. Re-aggregates under ORIGINAL, LINEAGE_COLLAPSED (best / mean), INDEPENDENT_ONLY,
   LEAVE_LINEAGE_OUT (plus a supplementary variant that also folds the selection-derived
   module dimension into the lineage), with the same eligibility set, the same RRA
   function and the same top-600 -> one-gene-per-LD-block -> head(50) rule.

What it does NOT do
-------------------
No new evidence, no new dimension, no weighted score. Every scheme only regroups the
normalised ranks the original already computed. Ranks are TRIAGE, not truth: a gene that
survives every scheme is better supported than one that does not, and nothing more.

Usage
-----
    PYTHONPATH=src .venv/bin/python pipelines/sprint3_1/rank_dependency_audit.py
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "pipelines" / "gene_tournament"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
import build_consensus as bc  # noqa: E402
from _provenance import utc_now  # noqa: E402
from rank_aggregation import normalised_ranks, rra_score  # noqa: E402

GT_DATA = REPO_ROOT / "data" / "gene_tournament"
GT_OUT = REPO_ROOT / "reports" / "gene_tournament"
OUT = REPO_ROOT / "reports" / "sprint3_1"
CSV_OUT = OUT / "rank_dependency_audit.csv"
JSON_OUT = OUT / "rank_dependency_audit_summary.json"

NAMED_GENES = ["NEGR1", "DCC", "EXOC4", "NT5DC2", "BSN", "SYT1", "NSF", "ERBB3", "GRIA4",
               "KCNJ3", "RIMS2", "CADM2", "PTPRT", "MEF2C"]

# ---------------------------------------------------------------- vocabulary ----------
SAME = "SAME_GWAS_SIGNAL_UKB"
OVERLAP = "OVERLAPPING_SAMPLE_REPLICATION"
INDEP_COHORT = "INDEPENDENT_COHORT"
INDEP_MOLECULAR = "INDEPENDENT_MOLECULAR_DATASET"
INDEP_PERTURB = "INDEPENDENT_PERTURBATION"
DERIVED = "DERIVED_FROM_SELECTION"
EXPRESSION = "EXPRESSION_ANNOTATION"
ABSENT = "ABSENT"
UNDETERMINED = "UNDETERMINED"   # allowed by the brief when the files cannot decide
VOCAB = [SAME, OVERLAP, INDEP_COHORT, INDEP_MOLECULAR, INDEP_PERTURB, DERIVED, EXPRESSION, ABSENT]
VOCAB_WITH_UNDETERMINED = VOCAB + [UNDETERMINED]
SAME_LINEAGE_CLASSES = {SAME, OVERLAP}

DIM_COL = {"direct": "dim_direct", "replication": "dim_replication", "finemap": "dim_finemap",
           "coloc": "dim_coloc", "positive_human": "dim_positive", "direction": "dim_direction",
           "adult_modifiability": "dim_adult_mod", "module": "dim_module",
           "extreme": "dim_extreme", "math": "dim_math"}
PRIMARY_DIMS = ["direct", "replication", "finemap", "coloc", "positive_human", "direction",
                "adult_modifiability", "module"]
SENSITIVITY_DIMS = ["extreme", "math"]      # enter only consensus_rank_all_dimensions
ALL_DIMS = PRIMARY_DIMS + SENSITIVITY_DIMS

# Dimensions whose evidence descends from the UKB-containing cognition-GWAS lineage.
# "direction" is included: it is computed from the same colocalisation records as "coloc".
LINEAGE_DIMS = {"direct", "replication", "finemap", "coloc", "direction"}
# Dimension-level class of every dimension (per-gene classes are computed below).
DIMENSION_CLASS = {"direct": SAME, "replication": OVERLAP, "finemap": SAME, "coloc": SAME,
                   "direction": SAME, "positive_human": INDEP_PERTURB,
                   "adult_modifiability": EXPRESSION, "module": DERIVED,
                   "extreme": OVERLAP, "math": SAME}
INDEPENDENT_EVIDENCE_CLASSES = {INDEP_COHORT, INDEP_PERTURB}

# ------------------------------------------------ study-level UKB determinations -------
# Each entry is a statement found IN THIS REPOSITORY. It is verified at run time: if the
# quoted text is no longer in the file the determination is dropped (-> UKB_UNKNOWN).
DOCUMENTED_UKB_PMIDS = {
    "29844566": ("Davies 2018", "pipelines/gene_tournament/analyse_extreme_tail.py",
                 "Davies 2018 is a CHARGE+COGENT+UKB"),
    "29942086": ("Savage 2018", "pipelines/gene_tournament/build_gene_ranks.py",
                 "both contain UK Biobank"),
}
DOCUMENTED_OVERLAP_STUDIES = {
    "GCST005626": ("Zabaneh 2018 extreme IQ", "pipelines/gene_tournament/analyse_extreme_tail.py",
                   "HRS is a CHARGE cohort"),
}
COHORT_PLACEHOLDERS = {"", "NR", "OTHER", "MULTIPLE"}
UKB_TOKEN = re.compile(r"^(UKB|UKBB|UK ?BIOBANK)$", re.I)
UKB_TEXT = re.compile(r"\bUKB\b|UK Biobank", re.I)
UKB_CONFIRMED, UKB_FREE, UKB_OVERLAP_POSSIBLE, UKB_UNKNOWN = (
    "UKB_CONFIRMED", "UKB_FREE_VERIFIED", "UKB_FREE_OVERLAP_POSSIBLE", "UKB_UNKNOWN")
STATUS_TO_CLASS = {UKB_CONFIRMED: SAME, UKB_FREE: INDEP_COHORT, UKB_OVERLAP_POSSIBLE: OVERLAP,
                   UKB_UNKNOWN: UNDETERMINED}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rk(x):
    """Rank for JSON: int, or None when the gene has no rank under a scheme."""
    return None if x is None or pd.isna(x) else int(x)


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "NA"
    return f"{x:.{nd}g}" if isinstance(x, float) else str(x)


# ======================================================================================
# 1. Reproduce the original consensus with the original functions
# ======================================================================================
def load_like_main():
    """The first lines of build_consensus.main(), verbatim in effect."""
    core = pd.read_csv(GT_OUT / "direct_cognition_rank.csv")
    ext = pd.read_csv(GT_OUT / "extreme_tail_rank.csv")[["GENE", "Z_ext"]].rename(columns={"GENE": "entrez_id"})
    mth = pd.read_csv(GT_OUT / "math_gene_rank.csv")[["entrez_id", "A_raw_math_Z_objective_item", "math_class"]].rename(
        columns={"A_raw_math_Z_objective_item": "Z_fi4"})
    core = core.merge(ext, on="entrez_id", how="left").merge(mth, on="entrez_id", how="left")
    cand = pd.read_csv(GT_DATA / "candidate_genes_for_annotation.csv")
    dev = pd.read_parquet(GT_DATA / "developmental_classification.parquet")
    con = pd.read_csv(REPO_ROOT / "data/interim/gnomad_constraint.tsv", sep="\t").rename(columns={"GENE": "entrez_id"})
    cg = pd.read_csv(sorted(glob.glob(str(REPO_ROOT / "data/raw/clingen/*/ClinGen_gene_curation_list_GRCh38.tsv")))[-1],
                     sep="\t", skiprows=5)
    cg.columns = [c.lstrip("#").strip() for c in cg.columns]
    hi3 = set(cg[cg["Haploinsufficiency Score"].astype(str) == "3"]["Gene ID"].astype(int))
    ts3 = set(cg[cg["Triplosensitivity Score"].astype(str) == "3"]["Gene ID"].astype(int))
    con["clingen_hi3"] = con.entrez_id.isin(hi3)
    con["clingen_ts3"] = con.entrez_id.isin(ts3)
    cons = con[["entrez_id", "oe_lof_upper", "pLI", "clingen_hi3", "clingen_ts3"]]
    return core, cand, dev, cons, cg


def run_part_g_h_readonly(cand):
    """Call bc.part_g_h without letting it rewrite the committed compact coloc file."""
    original = bc.DATA
    with tempfile.TemporaryDirectory() as td:
        for name in ("opentargets_credible_sets.csv", "opentargets_brain_coloc_compact.csv.gz"):
            os.symlink(original / name, Path(td) / name)
        bc.DATA = Path(td)
        try:
            g, h = bc.part_g_h(cand)
        finally:
            bc.DATA = original
    return g, h


def compare_top50(top: pd.DataFrame, ref: pd.DataFrame) -> dict:
    ours = list(zip(top.gene, [int(x) for x in top.consensus_rank]))
    theirs = list(zip(ref.gene, [int(x) for x in ref.consensus_rank]))
    mism = [{"position": i + 1, "reproduced": a, "committed": b}
            for i, (a, b) in enumerate(zip(ours, theirs)) if a != b]
    return {"reproduced_exactly": ours == theirs and len(ours) == len(theirs),
            "n_reproduced": len(ours), "n_committed": len(theirs),
            "same_gene_set": set(top.gene) == set(ref.gene),
            "n_position_mismatches": len(mism), "mismatches": mism[:20]}


# ======================================================================================
# 2. Scheme machinery (re-uses normalised_ranks + rra_score exactly as consensus() does)
# ======================================================================================
def rho_from_columns(cols: list[np.ndarray], n_rows: int) -> np.ndarray:
    if not cols:
        return np.full(n_rows, np.nan)
    R = np.column_stack(cols)
    return np.array([rra_score(r)[0] for r in R])


def collapse(arrays: list[np.ndarray], how: str) -> np.ndarray:
    """Collapse several normalised-rank columns into ONE list, then re-rank it.

    Re-ranking matters: the minimum of k uniform ranks is not uniform, so feeding the raw
    minimum to RRA would re-introduce exactly the multiple counting being removed.
    """
    M = np.column_stack(arrays)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        v = np.nanmin(M, axis=1) if how == "best" else np.nanmean(M, axis=1)
    return normalised_ranks(v, higher_is_better=False)


def ld_leads(t: pd.DataFrame, rho: np.ndarray) -> pd.DataFrame:
    """build_consensus.consensus()'s selection: top 600 by rho, one lead per LD block (all leads)."""
    rank = pd.Series(rho, index=t.index).rank(method="min")
    top_idx = np.argsort(rho)[:600]
    top_idx = top_idx[~np.isnan(rho[top_idx])]        # a gene with no evidence cannot lead
    sub = t.iloc[top_idx].copy()
    sub["consensus_rank"] = rank.iloc[top_idx].astype(int).to_numpy()
    sub = sub.sort_values("consensus_rank")
    return sub.loc[sub.groupby("ld_block_r0.2").consensus_rank.idxmin()].sort_values("consensus_rank")


def top50_leads(t: pd.DataFrame, rho: np.ndarray) -> pd.DataFrame:
    """... then head(50), exactly as consensus() returns ``lead.head(50)``."""
    return ld_leads(t, rho).head(50)


def cutoff_ties(leads: pd.DataFrame) -> dict:
    """Is top-50 membership at the cut decided by evidence or by the sort's tie-breaking?"""
    if len(leads) < 50:
        return {"cutoff_rank": None, "n_leads_at_cutoff_rank": 0, "n_leads_at_cutoff_included": 0,
                "membership_at_cutoff_decided_by_tie_break": False}
    cut = int(leads.consensus_rank.iloc[49])
    at = leads[leads.consensus_rank == cut]
    inc = int((leads.head(50).consensus_rank == cut).sum())
    return {"cutoff_rank": cut, "n_leads_at_cutoff_rank": int(len(at)), "n_leads_at_cutoff_included": inc,
            "membership_at_cutoff_decided_by_tie_break": bool(len(at) > inc)}


def scheme_definitions(names: list[str]) -> dict[str, dict]:
    lineage = [n for n in names if n in LINEAGE_DIMS]
    rest = [n for n in names if n not in LINEAGE_DIMS]
    rest_no_module = [n for n in rest if n != "module"]
    indep = [n for n in names if DIMENSION_CLASS[n] in INDEPENDENT_EVIDENCE_CLASSES]
    return {
        "ORIGINAL": {"lists": [[n] for n in names], "collapse": None,
                     "description": "reproduction of build_consensus.consensus()"},
        "LINEAGE_COLLAPSED_BEST": {"lists": [lineage] + [[n] for n in rest], "collapse": "best",
                                   "description": f"{'+'.join(lineage)} -> ONE list (best normalised rank, re-ranked); "
                                                  f"kept separate: {', '.join(rest)}"},
        "LINEAGE_COLLAPSED_MEAN": {"lists": [lineage] + [[n] for n in rest], "collapse": "mean",
                                   "description": f"{'+'.join(lineage)} -> ONE list (mean normalised rank, re-ranked); "
                                                  f"kept separate: {', '.join(rest)}"},
        "INDEPENDENT_ONLY": {"lists": [[n] for n in indep], "collapse": None,
                             "description": "only dimensions whose dimension-level class is INDEPENDENT_COHORT or "
                                            f"INDEPENDENT_PERTURBATION: {indep or 'NONE'}"},
        "LEAVE_LINEAGE_OUT": {"lists": [[n] for n in rest], "collapse": None,
                              "description": f"drop {'+'.join(lineage)}; keep {', '.join(rest)}"},
        # Supplementary: module membership was built on Davies-selected genes, so it is not
        # independent of the lineage either. Folding it in is the stricter reading.
        "SUPP_LINEAGE_PLUS_MODULE_COLLAPSED_BEST": {
            "lists": [lineage + ["module"]] + [[n] for n in rest_no_module], "collapse": "best",
            "description": f"{'+'.join(lineage + ['module'])} -> ONE list (best); kept: {', '.join(rest_no_module) or 'none'}"},
        "SUPP_LINEAGE_PLUS_MODULE_COLLAPSED_MEAN": {
            "lists": [lineage + ["module"]] + [[n] for n in rest_no_module], "collapse": "mean",
            "description": f"{'+'.join(lineage + ['module'])} -> ONE list (mean); kept: {', '.join(rest_no_module) or 'none'}"},
    }


def run_schemes(t: pd.DataFrame, names: list[str], top_committed: pd.DataFrame) -> dict:
    base = {n: normalised_ranks(t[DIM_COL[n]].to_numpy(float), True) for n in names}
    out = {}
    for scheme, spec in scheme_definitions(names).items():
        cols = []
        for group in spec["lists"]:
            if len(group) == 1:
                cols.append(base[group[0]])
            else:
                cols.append(collapse([base[n] for n in group], spec["collapse"]))
        rho = rho_from_columns(cols, len(t))
        rank = pd.Series(rho, index=t.index).rank(method="min")
        leads = ld_leads(t, rho)
        cut = cutoff_ties(leads)
        at_cut = set(leads[leads.consensus_rank == cut["cutoff_rank"]].gene) if cut["cutoff_rank"] else set()
        out[scheme] = {"spec": spec, "rho": rho, "rank": rank, "top50": leads.head(50),
                       "cutoff": cut, "leads_at_cutoff": at_cut}
    # --- the ORIGINAL scheme must be the original computation, not an approximation
    o = out["ORIGINAL"]
    assert np.array_equal(o["rho"], t.rra_rho.to_numpy(), equal_nan=True), "ORIGINAL rho differs from consensus()"
    assert (o["rank"].astype(int) == t.consensus_rank).all(), "ORIGINAL rank differs from consensus()"
    assert list(o["top50"].gene) == list(top_committed.gene), "ORIGINAL top-50 differs from consensus() output"
    return out


def scheme_summary(t: pd.DataFrame, res: dict) -> dict:
    orig = res["ORIGINAL"]
    orig_top = list(orig["top50"].gene)
    eid = t.entrez_id.to_numpy()
    summ = {}
    for scheme, r in res.items():
        top = list(r["top50"].gene)
        delta = (r["rank"] - orig["rank"])
        d = pd.DataFrame({"gene": t.gene.to_numpy(), "entrez_id": eid, "orig": orig["rank"].to_numpy(),
                          "new": r["rank"].to_numpy(), "delta": delta.to_numpy()})
        in_orig = d[d.gene.isin(orig_top)]
        fallers = in_orig.sort_values("delta", ascending=False, na_position="first").head(10)
        entrants = d[d.gene.isin(top) & ~d.gene.isin(orig_top)].sort_values("new").head(15)
        risers = d.dropna(subset=["delta"]).sort_values("delta").head(10)
        summ[scheme] = {
            "description": r["spec"]["description"],
            "lists": r["spec"]["lists"],
            "n_eligible_genes": int(len(t)),
            "n_genes_with_any_evidence_in_scheme": int(np.sum(~np.isnan(r["rho"]))),
            "n_genes_with_no_evidence_in_scheme": int(np.sum(np.isnan(r["rho"]))),
            "n_genes_tied_at_rank_1": int((r["rank"] == 1).sum()),
            "top50_size": len(top),
            "top50_overlap_with_original": len(set(top) & set(orig_top)),
            "top50_cutoff_ties": r["cutoff"],
            "top50_overlap_with_original_tie_robust_range": [
                # lower: original genes in this top 50 NOT via a tied cutoff slot;
                # upper: original genes that are in it, or tied at the cutoff as an LD lead.
                len((set(top) - r["leads_at_cutoff"]) & set(orig_top)),
                len((set(top) | r["leads_at_cutoff"]) & set(orig_top))],
            "original_top50_dropped": [g for g in orig_top if g not in top],
            "top50_genes_in_order": top,
            "original_top50_biggest_fallers": [
                {"gene": x.gene, "original_rank": rk(x.orig), "scheme_rank": rk(x.new),
                 "delta": rk(x.delta)} for x in fallers.itertuples()],
            "biggest_risers_all_eligible": [
                {"gene": x.gene, "original_rank": int(x.orig), "scheme_rank": int(x.new), "delta": int(x.delta)}
                for x in risers.itertuples()],
            "new_entrants_to_top50": [
                {"gene": x.gene, "original_rank": int(x.orig), "scheme_rank": int(x.new)} for x in entrants.itertuples()],
        }
    # Spearman between schemes over eligible genes (pairwise complete)
    sp = {}
    keys = list(res)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            x, y = res[a]["rank"].to_numpy(), res[b]["rank"].to_numpy()
            ok = ~np.isnan(x) & ~np.isnan(y)
            if ok.sum() >= 3 and np.nanstd(x[ok]) > 0 and np.nanstd(y[ok]) > 0:
                s = stats.spearmanr(x[ok], y[ok])
                sp[f"{a}__vs__{b}"] = {"rho": round(float(s.statistic), 4), "n": int(ok.sum())}
            else:
                sp[f"{a}__vs__{b}"] = {"rho": None, "n": int(ok.sum()),
                                      "note": "undefined: fewer than 3 shared genes or a constant ranking"}
    return {"schemes": summ, "spearman_between_schemes": sp}


# ======================================================================================
# 3. Study registry with audited UKB status
# ======================================================================================
def cohort_tokens(raw) -> list[str]:
    toks = []
    for el in (raw or []):
        for part in re.split(r"[|+,;]", str(el)):
            p = part.strip()
            if p:
                toks.append(p)
    return toks


def verify_documented() -> tuple[dict, dict, list]:
    ukb, ovl, dropped = {}, {}, []
    for store, src in ((ukb, DOCUMENTED_UKB_PMIDS), (ovl, DOCUMENTED_OVERLAP_STUDIES)):
        for key, (label, path, quote) in src.items():
            text = (REPO_ROOT / path).read_text(encoding="utf-8") if (REPO_ROOT / path).exists() else ""
            if quote in " ".join(text.split()):
                store[key] = f"{label}: {path} states '{quote}'"
            else:
                dropped.append({"key": key, "label": label, "path": path, "quote_not_found": quote})
    return ukb, ovl, dropped


def build_registry(co: pd.DataFrame, cs: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    meta = {}
    for line in (GT_DATA / "study_metadata.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        meta[r["accession_id"]] = r
    sc = pd.read_csv(GT_DATA / "study_classification.csv", dtype={"pubmed_id": str}).set_index("accession_id")
    doc_ukb, doc_ovl, dropped = verify_documented()

    recs = {}
    for acc, r in meta.items():
        recs[acc] = {"accession_id": acc, "pubmed_id": str(r.get("pubmed_id") or ""),
                     "first_author": r.get("first_author"), "trait": r.get("reported_trait"),
                     "cohort_raw": r.get("cohort"), "initial_sample_size": r.get("initial_sample_size"),
                     "source": "study_metadata.jsonl"}
    for acc, pmid, trait in co[["gwas_study_id", "gwas_pubmed_id", "gwas_trait"]].drop_duplicates().itertuples(index=False):
        recs.setdefault(acc, {"accession_id": acc, "pubmed_id": str(pmid), "first_author": None, "trait": trait,
                              "cohort_raw": None, "initial_sample_size": None,
                              "source": "opentargets_brain_coloc_compact (not in study_metadata.jsonl)"})
    for acc, trait, n in cs[["study_id", "trait", "n_samples"]].drop_duplicates("study_id").itertuples(index=False):
        recs.setdefault(acc, {"accession_id": acc, "pubmed_id": "", "first_author": None, "trait": trait,
                              "cohort_raw": None, "initial_sample_size": f"n_samples={n}",
                              "source": "gwas_credible_sets_l2g (not in study_metadata.jsonl)"})

    # PMIDs with at least one accession whose OWN cohort field lists UKB
    pmid_ukb = {r["pubmed_id"] for r in recs.values()
                if any(UKB_TOKEN.match(t) for t in cohort_tokens(r["cohort_raw"]))}
    rows = []
    for acc, r in recs.items():
        toks = cohort_tokens(r["cohort_raw"])
        named = [t for t in toks if t.upper() not in COHORT_PLACEHOLDERS]
        pipeline_status = sc.ukb_status.get(acc) if acc in sc.index else None
        tier = sc.tier.get(acc) if acc in sc.index else None
        if r["pubmed_id"] in doc_ukb:
            st, basis = UKB_CONFIRMED, "repository statement -- " + doc_ukb[r["pubmed_id"]]
        elif any(UKB_TOKEN.match(t) for t in toks):
            st, basis = UKB_CONFIRMED, f"GWAS Catalog cohort field lists UKB: {r['cohort_raw']}"
        elif UKB_TEXT.search(str(r["trait"] or "")):
            st, basis = UKB_CONFIRMED, f"trait text names a UKB data field: '{r['trait']}'"
        elif acc in doc_ovl:
            st, basis = UKB_OVERLAP_POSSIBLE, "repository statement -- " + doc_ovl[acc]
        elif named:
            st = UKB_FREE
            basis = "cohort field lists only named non-UKB cohorts: " + "+".join(sorted(set(named)))
            if any(t.upper() == "OTHER" for t in toks):
                basis += " (plus unnamed 'other'; UKB is a controlled Catalog term and would be named)"
        elif r["pubmed_id"] in pmid_ukb:
            st, basis = UKB_CONFIRMED, f"no own cohort field; a sibling accession of PMID {r['pubmed_id']} lists UKB"
        else:
            st = UKB_UNKNOWN
            basis = ("cohort field is only a placeholder " + repr(r["cohort_raw"])) if toks else \
                "no cohort recorded in the repository for this study (unknown is not UKB-free)"
        unit = (sc.independence_unit.get(acc) if acc in sc.index else None) or f"PMID:{r['pubmed_id'] or acc}"
        clean_unit = ("COHORTS:" + "+".join(sorted(set(named)))) if (named and st == UKB_FREE) else unit.strip()
        rows.append({**r, "cohort_raw": "|".join(r["cohort_raw"]) if isinstance(r["cohort_raw"], list) else r["cohort_raw"],
                     "tier": tier, "pipeline_ukb_status": pipeline_status, "audit_ukb_status": st,
                     "audit_basis": basis, "independence_unit_pipeline": unit, "independence_unit_audit": clean_unit})
    reg = pd.DataFrame(rows).set_index("accession_id")
    disagreements = reg[(reg.pipeline_ukb_status == "not_listed") & (reg.audit_ukb_status != UKB_FREE)]
    info = {"documented_determinations_verified": {**doc_ukb, **doc_ovl},
            "documented_determinations_dropped": dropped,
            "n_studies": int(len(reg)),
            "audit_status_counts": reg.audit_ukb_status.value_counts().to_dict(),
            "direct_strict_audit_status_counts": reg[reg.tier == "direct_strict"].audit_ukb_status.value_counts().to_dict(),
            "pipeline_not_listed_but_audit_not_ukb_free": [
                {"accession_id": a, "pubmed_id": x.pubmed_id, "first_author": x.first_author, "trait": x.trait,
                 "cohort_raw": x.cohort_raw, "audit_status": x.audit_ukb_status, "audit_basis": x.audit_basis}
                for a, x in disagreements.iterrows()]}
    return reg, info


# ======================================================================================
# 4. Per-gene, per-dimension lineage
# ======================================================================================
def catalog_strict_accessions() -> dict[int, list[str]]:
    """Replicates build_gene_ranks.load_catalog() (the merge that fills direct_cognition_rank)."""
    u = pd.read_parquet(GT_DATA / "master_gene_universe.parquet")
    u = u[u.symbol_resolution.isin(["approved_symbol", "alias_or_previous_symbol"])]
    u = u[u.entrez_id.astype(str).str.len() > 0].copy()
    u["entrez_id"] = pd.to_numeric(u.entrez_id, errors="coerce")
    u = u.dropna(subset=["entrez_id"]).sort_values("n_strict_studies", ascending=False).drop_duplicates("entrez_id")
    return {int(e): [s for s in str(ss or "").split("|") if s] for e, ss in zip(u.entrez_id, u.strict_studies)}


def credible_sets_with_loci() -> pd.DataFrame:
    """gwas_credible_sets_l2g.csv plus the locus clustering of fetch_gwas_credible_sets.py."""
    cs = pd.read_csv(GT_DATA / "gwas_credible_sets_l2g.csv")
    cs["positional_driven"] = cs.positional_driven.fillna(False).astype(bool)
    leads = cs.drop_duplicates("study_locus_id").sort_values(["chromosome", "position"])
    locus_id, last, n = {}, (None, -10 ** 12), 0
    for _, r in leads.iterrows():
        if r.chromosome != last[0] or r.position - last[1] > 1_000_000:
            n += 1
        locus_id[r.study_locus_id] = f"L{n:04d}"
        last = (r.chromosome, r.position)
    cs["locus"] = cs.study_locus_id.map(locus_id)
    return cs


def finemap_score(rows: pd.DataFrame) -> float:
    """fine_mapping_score of fetch_gwas_credible_sets.py for a subset of top-L2G rows."""
    if rows.empty:
        return 0.0
    sup = rows[(rows.l2g_score >= 0.5) & (~rows.positional_driven)]
    if sup.locus.nunique() == 0:
        return 0.0
    return float(rows.groupby("locus").l2g_score.max().sum())


def coloc_table() -> pd.DataFrame:
    co = pd.read_csv(GT_DATA / "opentargets_brain_coloc_compact.csv.gz")
    co["trait_class"] = co.gwas_trait.map(bc.classify_trait)
    co["strength"] = co.apply(bc.coloc_strength, axis=1)
    co["qtl_dataset"] = co.qtl_study_id.astype(str).str.extract(r"^([a-z0-9]+)_", expand=False)
    return co


def classify_value(value, driving_status: list[str], reach_free: bool) -> str:
    """Primary class of a GWAS-derived dimension value for one gene.

    Order: reachable from verified UKB-free evidence alone -> INDEPENDENT_COHORT; else any
    value-driving evidence UKB-confirmed -> SAME; else overlap-possible -> OVERLAPPING;
    else UNDETERMINED (the driving studies have no cohort record in the repository).
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ABSENT
    if reach_free:
        return INDEP_COHORT
    s = set(driving_status)
    if UKB_CONFIRMED in s:
        return SAME
    if UKB_OVERLAP_POSSIBLE in s:
        return OVERLAP
    return UNDETERMINED


def join_classes(*classes) -> str:
    order = {c: i for i, c in enumerate(VOCAB_WITH_UNDETERMINED)}
    s = {c for c in classes if c}
    return "|".join(sorted(s, key=order.get)) if s else ABSENT


def study_label(reg: pd.DataFrame, acc: str) -> str:
    if acc not in reg.index:
        return f"{acc}[{UKB_UNKNOWN}]"
    x = reg.loc[acc]
    who = f"{x.first_author or ''} PMID:{x.pubmed_id}".strip()
    return f"{acc}({who})[{x.audit_ukb_status}]"


def gene_lineage(row: pd.Series, ctx: dict) -> dict:
    """All lineage columns for one gene (row from the natural-gate consensus table)."""
    reg, cs, co_direct, strict = ctx["reg"], ctx["cs"], ctx["co_direct"], ctx["strict"]
    eid, sym = int(row.entrez_id), row.gene
    status = lambda acc: reg.audit_ukb_status.get(acc, UKB_UNKNOWN)  # noqa: E731
    unit_of = lambda acc: reg.independence_unit_audit.get(acc, f"ACC:{acc}")  # noqa: E731
    rec: dict = {}
    indep_cohort_units: dict[str, str] = {}

    # ---------------------------------------------------------------- direct ----
    v = row.dim_direct
    rec.update({"direct_value": v, "direct_lineage_class": SAME if pd.notna(v) else ABSENT,
                "direct_lineage_classes_all": SAME if pd.notna(v) else ABSENT,
                "direct_lineage_sources": (f"MAGMA 10kb gene test on Davies 2018 general cognitive function "
                                           f"(GCST006269, PMID 29844566, N=282,014 open subset; CHARGE+COGENT+UKB); "
                                           f"gene_P={fmt(row.gene_P)}")})

    # ----------------------------------------------------------- replication ----
    accs = strict.get(eid, [])
    units: dict[str, set] = {}
    for a in accs:
        units.setdefault(reg.independence_unit_pipeline.get(a, f"ACC:{a}"), set()).add(a)
    unit_status = {}
    for u, aa in units.items():
        st = {status(a) for a in aa}
        unit_status[u] = (UKB_CONFIRMED if UKB_CONFIRMED in st else UKB_FREE if st == {UKB_FREE}
                          else UKB_OVERLAP_POSSIBLE if UKB_OVERLAP_POSSIBLE in st else UKB_UNKNOWN)
    by_st = {k: sorted(u.strip() for u, s in unit_status.items() if s == k)
             for k in (UKB_CONFIRMED, UKB_FREE, UKB_OVERLAP_POSSIBLE, UKB_UNKNOWN)}
    for u, s in unit_status.items():
        if s == UKB_FREE:
            a0 = sorted(units[u])[0]
            indep_cohort_units[unit_of(a0)] = f"catalog strict: {','.join(sorted(units[u]))}"
    savage_z = row.gene_Z_savage
    v = row.dim_replication
    n_units = int(row.number_of_independent_cohorts_upper_bound)
    has_davies_unit = any(reg.pubmed_id.get(a) == "29844566" for a in accs)
    if n_units == 0 and pd.isna(savage_z):
        rcls = UNDETERMINED
    else:
        rcls = OVERLAP
    rall = join_classes(OVERLAP if pd.notna(savage_z) else None,
                        SAME if by_st[UKB_CONFIRMED] else None,
                        INDEP_COHORT if by_st[UKB_FREE] else None,
                        OVERLAP if by_st[UKB_OVERLAP_POSSIBLE] else None,
                        UNDETERMINED if by_st[UKB_UNKNOWN] else None) if rcls != UNDETERMINED else UNDETERMINED
    rec.update({
        "replication_value": v, "replication_lineage_class": rcls, "replication_lineage_classes_all": rall,
        "replication_lineage_sources": (
            f"value = {n_units} strict catalog units + Savage Z {fmt(savage_z)}/100 (Savage 2018 shares UKB with Davies); "
            f"units UKB-confirmed={len(by_st[UKB_CONFIRMED])} {by_st[UKB_CONFIRMED]}; "
            f"UKB-unknown={len(by_st[UKB_UNKNOWN])} {by_st[UKB_UNKNOWN]}; "
            f"verified UKB-free={len(by_st[UKB_FREE])} {by_st[UKB_FREE]}; "
            f"Davies-2018 discovery study counted as a 'replication' unit: {'yes' if has_davies_unit else 'no'}"),
        "catalog_units_recount_matches_pipeline": len(units) == n_units,
        "pipeline_n_strict_ukb_free_units": int(row.n_strict_ukb_free_units),
        "audit_n_verified_ukb_free_catalog_units": len(by_st[UKB_FREE]),
    })

    # --------------------------------------------------------------- finemap ----
    v = row.dim_finemap
    fm_sym = ctx["fm_symbol"].get(eid, sym)
    grows = cs[cs.gene == fm_sym]
    t1 = grows[grows.l2g_rank == 1]
    if pd.isna(v):
        rec.update({"finemap_value": v, "finemap_lineage_class": ABSENT, "finemap_lineage_classes_all": ABSENT,
                    "finemap_lineage_sources": "no Open Targets GWAS credible set with an L2G call for this gene"})
    else:
        recomputed = finemap_score(t1)
        if v > 0:
            mx = t1.groupby("locus").l2g_score.transform("max")
            driving = t1[t1.l2g_score >= mx - 1e-12]
        else:
            driving = t1 if len(t1) else grows
        free_rows = t1[t1.study_id.map(status) == UKB_FREE]
        reach_free = bool(v > 0 and finemap_score(free_rows) >= v - 1e-9)
        cls = classify_value(v, [status(s) for s in driving.study_id], reach_free)
        all_status = {status(s) for s in (t1.study_id if len(t1) else grows.study_id)}
        sup = t1[(t1.l2g_score >= 0.5) & (~t1.positional_driven)]
        for s in sup.study_id.unique():
            if status(s) == UKB_FREE:
                indep_cohort_units[unit_of(s)] = f"fine-mapping supported L2G call: {s}"
        rec.update({
            "finemap_value": v, "finemap_lineage_class": cls,
            "finemap_lineage_classes_all": join_classes(*[STATUS_TO_CLASS[s] for s in all_status]) if all_status else cls,
            "finemap_lineage_sources": (
                f"Open Targets GWAS credible sets + L2G (top-ranked calls, {t1.study_locus_id.nunique()} credible sets, "
                f"{t1.locus.nunique()} loci); value-driving studies: "
                f"{sorted({study_label(reg, s) for s in driving.study_id})}; score from verified UKB-free studies alone="
                f"{fmt(finemap_score(free_rows))}; recomputed score={fmt(recomputed)}"),
            "finemap_recomputed_matches": bool(abs(recomputed - v) < 1e-9),
        })

    # ----------------------------------------------------------------- coloc ----
    v = row.dim_coloc
    crow = co_direct[co_direct.GENE == eid]
    strong = crow[crow.strength >= 0.8]
    qtl_strong = sorted(strong.qtl_dataset.dropna().unique())
    if pd.isna(v):
        why = ("gene outside the 400 Davies-top candidates queried for colocalisation"
               if eid not in ctx["cand_ids"] else
               f"no brain QTL colocalisation with a DIRECT-cognition GWAS (class: {row.colocalisation_class})")
        rec.update({"coloc_value": v, "coloc_lineage_class": ABSENT, "coloc_lineage_classes_all": ABSENT,
                    "coloc_gwas_side_lineage_class": ABSENT, "coloc_qtl_side_lineage_class": ABSENT,
                    "coloc_gwas_side_studies": "", "coloc_qtl_datasets_strong": "",
                    "coloc_lineage_sources": why})
    else:
        driving = crow[crow.strength >= v - 1e-12]
        free = crow[crow.gwas_study_id.map(status) == UKB_FREE]
        reach_free = bool(len(free) and free.strength.max() >= v - 1e-12)
        gcls = classify_value(v, [status(s) for s in driving.gwas_study_id], reach_free)
        gall = {STATUS_TO_CLASS[status(s)] for s in crow.gwas_study_id}
        for s in strong.gwas_study_id.unique():
            if status(s) == UKB_FREE:
                indep_cohort_units[unit_of(s)] = f"strong brain coloc GWAS side: {s}"
        rec.update({
            "coloc_value": v, "coloc_lineage_class": gcls,
            "coloc_lineage_classes_all": join_classes(*gall, INDEP_MOLECULAR),
            "coloc_gwas_side_lineage_class": gcls, "coloc_qtl_side_lineage_class": INDEP_MOLECULAR,
            "coloc_gwas_side_studies": ";".join(sorted({study_label(reg, s) for s in driving.gwas_study_id})),
            "coloc_qtl_datasets_strong": "|".join(qtl_strong),
            "coloc_lineage_sources": (
                f"eCAVIAR brain QTL x direct-cognition GWAS (Open Targets 26.06); max strength {fmt(v)} reached by "
                f"{driving.gwas_study_id.nunique()} GWAS studies x {driving.qtl_dataset.nunique()} QTL datasets; "
                f"strong (>=0.8) colocs: {len(strong)} rows, QTL datasets {qtl_strong}; "
                f"value reachable from verified UKB-free GWAS alone: {reach_free}; "
                "queried only for the 400 Davies-top candidates"),
        })

    # ------------------------------------------------------------- direction ----
    v = row.dim_direction
    if pd.isna(v):
        rec.update({"direction_value": v, "direction_lineage_class": ABSENT, "direction_lineage_classes_all": ABSENT,
                    "direction_lineage_sources": "no colocalisation query / NOT_QUERIED"})
    else:
        gl = crow[(crow.strength >= 0.8) & crow.qtl_study_type.astype(str).str.match(r"(eqtl|pqtl)$")
                  & ~crow.qtl_molecular_trait.astype(str).str.contains(r"_\d+_\d+$") & crow.beta_ratio_sign_average.notna()]
        if len(gl):
            cls = classify_value(v, [status(s) for s in gl.gwas_study_id], False)
            src = (f"sign agreement over {len(gl)} strong gene-level brain eQTL/pQTL colocs (resolved={bool(v)}); "
                   f"GWAS side {sorted({study_label(reg, s) for s in gl.gwas_study_id})}")
        else:
            cls = DERIVED
            src = ("value 0 encodes 'unresolved / no qualifying colocalisation'; it exists only because the gene was "
                   f"in the Davies-top-400 coloc query (colocalisation_class={row.colocalisation_class})")
        rec.update({"direction_value": v, "direction_lineage_class": cls,
                    "direction_lineage_classes_all": join_classes(cls, INDEP_MOLECULAR if len(gl) else None),
                    "direction_lineage_sources": src})

    # ----------------------------------------------------- adult modifiability ----
    v = row.dim_adult_mod
    rec.update({"adult_modifiability_value": v,
                "adult_modifiability_lineage_class": EXPRESSION if pd.notna(v) else ABSENT,
                "adult_modifiability_lineage_classes_all": EXPRESSION if pd.notna(v) else ABSENT,
                "adult_modifiability_lineage_sources": (
                    f"GTEx v10 adult brain TPM + BrainSpan developmental class ({row.developmental_class}, "
                    f"max adult brain TPM {fmt(row.adult_brain_max_tpm)}); expression, not association"
                    if pd.notna(v) else "no developmental classification")})

    # ---------------------------------------------------------- positive human ----
    v = row.dim_positive
    rec.update({"positive_human_value": v,
                "positive_human_lineage_class": INDEP_PERTURB if pd.notna(v) else ABSENT,
                "positive_human_lineage_classes_all": INDEP_PERTURB if pd.notna(v) else ABSENT,
                "positive_human_lineage_sources": (
                    "POSGEN:2q12.3_duplication, Huguet 2024 PMID 39667348, CNV-GWAS N=258,292; unreplicated, nominal; "
                    "UKB share of the sample UNDETERMINED (atlases/positive_genetics/2q12_3_duplication.yaml; "
                    "dependency rule D005)" if pd.notna(v) else "not one of the 4 hard-coded 2q12.3 CNV genes")})

    # ------------------------------------------------------------------ module ----
    v = row.dim_module
    rec.update({"module_value": v, "module_lineage_class": DERIVED if pd.notna(v) else ABSENT,
                "module_lineage_classes_all": DERIVED if pd.notna(v) else ABSENT,
                "module_lineage_sources": (
                    f"module {row.module} (module rank {int(-v)}); modules built on the 1,272 genes at Davies-2018 MAGMA "
                    "FDR<0.01 (annotation kNN + STRING); module rank itself uses Davies weighted evidence share and "
                    "Savage leave-study-out Jaccard; every gene in a module shares one rank"
                    if pd.notna(v) else f"no ranked module (module={row.module})")})

    # --------------------------------------------------- sensitivity-only dims ----
    v = row.dim_extreme
    rec.update({"extreme_value": v, "extreme_lineage_class": OVERLAP if pd.notna(v) else ABSENT,
                "extreme_lineage_classes_all": OVERLAP if pd.notna(v) else ABSENT,
                "extreme_lineage_sources": ("Zabaneh 2018 extreme-IQ MAGMA (GCST005626): UKB-free, but controls are HRS, "
                                            "a CHARGE cohort inside Davies 2018 -- overlap possible, unresolved. "
                                            "SENSITIVITY-ONLY dimension") if pd.notna(v) else "not measured"})
    v = row.dim_math
    rec.update({"math_value": v, "math_lineage_class": SAME if pd.notna(v) else ABSENT,
                "math_lineage_classes_all": SAME if pd.notna(v) else ABSENT,
                "math_lineage_sources": ("UKB fluid-intelligence item FI4 MAGMA (UKB participants shared with Davies). "
                                         "SENSITIVITY-ONLY dimension") if pd.notna(v) else "not measured"})

    # ---------------------------------------------------------- independent units ----
    pert = []
    for pid, genes in ctx["posgen"]:
        if sym in genes:
            pert.append(f"{pid} (positive-direction CNV; UKB overlap undetermined)")
    cg = ctx["clingen"].get(eid)
    if cg is not None:
        hi, ts, mondo_hi, mondo_ts = cg
        if hi == "3":
            pert.append(f"ClinGen HI=3 ({mondo_hi or 'no MONDO'}; loss-of-function -> disorder; phenotype name not in repo)")
        if ts == "3":
            pert.append(f"ClinGen TS=3 ({mondo_ts or 'no MONDO'})")
    rec.update({
        "n_independent_cohort_units": len(indep_cohort_units),
        "independent_cohort_units": "; ".join(f"{u} <- {why}" for u, why in sorted(indep_cohort_units.items())),
        "n_independent_molecular_datasets_strong": len(qtl_strong),
        "independent_molecular_datasets_strong": "|".join(qtl_strong),
        "n_independent_perturbation_units": len(pert),
        "independent_perturbation_units": "; ".join(pert),
    })
    rec["n_independent_units"] = len(indep_cohort_units) + len(qtl_strong) + len(pert)
    rec["n_independent_units_excl_molecular"] = len(indep_cohort_units) + len(pert)
    rec["n_independent_units_excl_molecular_and_clingen"] = len(indep_cohort_units) + sum(
        1 for p in pert if not p.startswith("ClinGen"))
    return rec


def count_dims(rec: dict, dims: list[str]) -> tuple[int, int, int, int, list[str], list[str]]:
    present = [d for d in dims if rec[f"{d}_lineage_class"] != ABSENT]
    same = [d for d in present if rec[f"{d}_lineage_class"] in SAME_LINEAGE_CLASSES]
    derived = [d for d in present if rec[f"{d}_lineage_class"] == DERIVED]
    undet = [d for d in present if rec[f"{d}_lineage_class"] == UNDETERMINED]
    return len(present), len(same), len(derived), len(undet), same, present


def dependence_note(rec: dict, names_nat: list[str], names_ad: list[str]) -> str:
    parts = []
    for label, dims in (("natural", names_nat), ("adult", names_ad)):
        n, s, dv, u, same, present = count_dims(rec, dims)
        parts.append(f"{label}: {n} dims present, {s} from the UKB GWAS lineage ({','.join(same) or '-'})"
                     + (f", {dv} derived from Davies selection" if dv else "")
                     + (f", {u} lineage undetermined" if u else ""))
    ind = []
    if rec["n_independent_cohort_units"]:
        ind.append(f"{rec['n_independent_cohort_units']} verified UKB-free cohort unit(s)")
    if rec["n_independent_molecular_datasets_strong"]:
        ind.append(f"{rec['n_independent_molecular_datasets_strong']} QTL dataset(s) with strong coloc "
                   f"({rec['independent_molecular_datasets_strong']}; GWAS half is still the UKB lineage)")
    if rec["n_independent_perturbation_units"]:
        ind.append(f"perturbation: {rec['independent_perturbation_units']}")
    note = "; ".join(parts) + ". Independent: " + ("; ".join(ind) if ind else "NONE")
    if rec["pipeline_n_strict_ukb_free_units"] != rec["audit_n_verified_ukb_free_catalog_units"]:
        note += (f". Pipeline n_strict_ukb_free_units={rec['pipeline_n_strict_ukb_free_units']} but audit verifies "
                 f"{rec['audit_n_verified_ukb_free_catalog_units']} (Perry 2025 cohort string lists 'UKB ' with a "
                 "trailing space; Lahti 2022 cohort is only 'multiple')")
    return note


# ======================================================================================
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    core, cand, dev, cons, cg_raw = load_like_main()
    g, h = run_part_g_h_readonly(cand)
    h_committed = pd.read_csv(GT_OUT / "adult_brain_directionality.csv")
    mods = bc.module_rank(pd.read_csv(GT_OUT / "biological_modules.csv"))
    full_nat, top_nat, names_nat = bc.consensus(core, g, h, mods, dev, cons, gate_adult=False)
    full_ad, top_ad, names_ad = bc.consensus(core, g, h, mods, dev, cons, gate_adult=True)
    ref_nat = pd.read_csv(GT_OUT / "TOP50_HUMAN_COGNITION_GENES.csv")
    ref_ad = pd.read_csv(GT_OUT / "TOP50_ADULT_MODIFIABLE_GENES.csv")
    repro = {"natural": compare_top50(top_nat, ref_nat), "adult": compare_top50(top_ad, ref_ad),
             "part_g_h_directionality_shape_matches_committed": list(h.shape) == list(h_committed.shape)}
    repro["ORIGINAL_reproduces_committed_top50"] = bool(repro["natural"]["reproduced_exactly"]
                                                        and repro["adult"]["reproduced_exactly"])
    repro["discrepancy_flag"] = not repro["ORIGINAL_reproduces_committed_top50"]
    if repro["discrepancy_flag"]:
        print("WARNING: reproduction differs from the committed Top-50s; continuing with the reproduction "
              "as baseline. Details in the summary JSON.", file=sys.stderr)

    # ------------------------------------------------------------- schemes ----
    res_nat = run_schemes(full_nat, names_nat, top_nat)
    res_ad = run_schemes(full_ad, names_ad, top_ad)
    sch_nat = scheme_summary(full_nat, res_nat)
    sch_ad = scheme_summary(full_ad, res_ad)

    # ------------------------------------------------------------- lineage ----
    co = coloc_table()
    cs = credible_sets_with_loci()
    reg, reg_info = build_registry(co, cs)
    co_direct = co[(co.qtl_is_brain == True) & (co.trait_class == "direct_cognition")]  # noqa: E712
    gg = g.dropna(subset=["entrez_id"]).sort_values("fine_mapping_score", ascending=False).drop_duplicates("entrez_id")
    posgen = []
    ph = pd.read_csv(GT_OUT / "positive_human_perturbations.csv")
    for x in ph.itertuples():
        if str(x.evidence_id).startswith("POSGEN:") or re.search(r"rare|CNV", str(x.variant_class), re.I):
            if not str(x.evidence_id).startswith("CLINGEN:"):
                posgen.append((x.evidence_id, set(str(x.genes).split("|"))))
    clingen = {int(r["Gene ID"]): (str(r["Haploinsufficiency Score"]), str(r["Triplosensitivity Score"]),
                                   r.get("Haploinsufficiency Disease ID") if pd.notna(r.get("Haploinsufficiency Disease ID")) else "",
                                   r.get("Triplosensitivity Disease ID") if pd.notna(r.get("Triplosensitivity Disease ID")) else "")
               for _, r in cg_raw.iterrows() if str(r["Gene ID"]).isdigit()}
    ctx = {"reg": reg, "cs": cs, "co_direct": co_direct, "strict": catalog_strict_accessions(),
           "fm_symbol": dict(zip(gg.entrez_id.astype(int), gg.gene)), "cand_ids": set(cand.GENE.astype(int)),
           "posgen": posgen, "clingen": clingen}

    scope = list(dict.fromkeys(list(top_nat.gene) + list(top_ad.gene) + NAMED_GENES))
    missing = [s for s in scope if s not in set(full_nat.gene)]
    t_nat = full_nat.set_index("gene")
    t_ad = full_ad.set_index("gene")
    rows = []
    for sym in scope:
        if sym not in t_nat.index:
            rows.append({"gene": sym, "scope_note": "NOT ELIGIBLE (MAGMA gene FDR >= 0.05 or no symbol) -- no ranks"})
            continue
        r = t_nat.loc[sym]
        r = r.copy(); r["gene"] = sym
        rec = {"gene": sym, "entrez_id": int(r.entrez_id),
               "named_gene": sym in NAMED_GENES,
               "in_top50_natural_original": sym in set(top_nat.gene),
               "in_top50_adult_original": sym in set(top_ad.gene),
               "eligible_natural": True, "eligible_adult": sym in t_ad.index,
               "ld_block_r0.2": int(r["ld_block_r0.2"])}
        lin = gene_lineage(r, ctx)
        for d in ALL_DIMS:
            rec[f"{d}_value"] = lin[f"{d}_value"]
            rec[f"{d}_rank_natural"] = (t_nat.loc[sym, f"rank_{d}"] if d in names_nat or d in SENSITIVITY_DIMS else np.nan)
            rec[f"{d}_rank_adult"] = (t_ad.loc[sym, f"rank_{d}"] if (sym in t_ad.index and
                                                                    (d in names_ad or d in SENSITIVITY_DIMS)) else np.nan)
            rec[f"{d}_in_natural_consensus"] = d in names_nat
            rec[f"{d}_in_adult_consensus"] = d in names_ad
            for k in ("lineage_class", "lineage_classes_all", "lineage_sources"):
                rec[f"{d}_{k}"] = lin[f"{d}_{k}"]
        for k in ("coloc_gwas_side_lineage_class", "coloc_gwas_side_studies", "coloc_qtl_side_lineage_class",
                  "coloc_qtl_datasets_strong", "catalog_units_recount_matches_pipeline",
                  "pipeline_n_strict_ukb_free_units", "audit_n_verified_ukb_free_catalog_units",
                  "n_independent_cohort_units", "independent_cohort_units",
                  "n_independent_molecular_datasets_strong", "independent_molecular_datasets_strong",
                  "n_independent_perturbation_units", "independent_perturbation_units",
                  "n_independent_units", "n_independent_units_excl_molecular",
                  "n_independent_units_excl_molecular_and_clingen"):
            rec[k] = lin.get(k)
        rec["finemap_recomputed_matches"] = lin.get("finemap_recomputed_matches")
        n, s, dv, u, _, _ = count_dims(lin, PRIMARY_DIMS)
        rec.update({"n_dimensions_present": n, "n_dimensions_same_gwas_lineage": s,
                    "n_dimensions_derived_from_selection": dv, "n_dimensions_lineage_undetermined": u})
        for label, dims in (("natural", names_nat), ("adult", names_ad)):
            n, s, dv, u, _, _ = count_dims(lin, dims)
            rec[f"n_dimensions_present_{label}"] = n
            rec[f"n_dimensions_same_gwas_lineage_{label}"] = s
        rec["original_n_dimensions_present_natural"] = int(r.n_dimensions_present)
        rec["original_n_dimensions_present_adult"] = (int(t_ad.loc[sym, "n_dimensions_present"])
                                                      if sym in t_ad.index else np.nan)
        rec["dependence_note"] = dependence_note(lin, names_nat, names_ad)
        for label, res, tfull in (("natural", res_nat, full_nat), ("adult", res_ad, full_ad)):
            idx = tfull.index[tfull.gene == sym]
            orig_rank = res["ORIGINAL"]["rank"].loc[idx].iloc[0] if len(idx) else np.nan
            for scheme, rr in res.items():
                srank = rr["rank"].loc[idx].iloc[0] if len(idx) else np.nan
                top = list(rr["top50"].gene)
                rec[f"rank_{label}_{scheme}"] = srank
                rec[f"delta_{label}_{scheme}"] = (srank - orig_rank) if pd.notna(srank) and pd.notna(orig_rank) else np.nan
                rec[f"in_top50_{label}_{scheme}"] = sym in top
                rec[f"top50_position_{label}_{scheme}"] = (top.index(sym) + 1) if sym in top else np.nan
                cut = rr["cutoff"]
                rec[f"top50_membership_tie_decided_{label}_{scheme}"] = bool(
                    cut["membership_at_cutoff_decided_by_tie_break"] and pd.notna(srank)
                    and int(srank) == cut["cutoff_rank"])
        rows.append(rec)
    audit = pd.DataFrame(rows)
    audit.to_csv(CSV_OUT, index=False)

    # sanity: our per-gate "present" counts equal the original RRA's n_dimensions_present
    ok = audit.dropna(subset=["original_n_dimensions_present_natural"])
    nat_count_ok = bool((ok.n_dimensions_present_natural == ok.original_n_dimensions_present_natural).all())
    oka = audit.dropna(subset=["original_n_dimensions_present_adult"])
    ad_count_ok = bool((oka.n_dimensions_present_adult == oka.original_n_dimensions_present_adult).all())

    # ------------------------------------------------------------- summary ----
    def indep_stats(genes: list[str]) -> dict:
        a = audit[audit.gene.isin(genes)]
        return {"n_genes": int(len(a)),
                "n_with_ge1_independent_unit_task_definition": int((a.n_independent_units >= 1).sum()),
                "n_with_ge1_unit_excluding_qtl_datasets": int((a.n_independent_units_excl_molecular >= 1).sum()),
                "n_with_ge1_unit_excluding_qtl_and_clingen": int((a.n_independent_units_excl_molecular_and_clingen >= 1).sum()),
                "n_with_ge1_verified_ukb_free_cohort_unit": int((a.n_independent_cohort_units >= 1).sum()),
                "n_with_ge1_strong_coloc_qtl_dataset": int((a.n_independent_molecular_datasets_strong >= 1).sum()),
                "n_with_ge1_perturbation_unit": int((a.n_independent_perturbation_units >= 1).sum()),
                "n_pipeline_ukb_free_units_ge1": int((a.pipeline_n_strict_ukb_free_units >= 1).sum()),
                "n_where_pipeline_ukb_free_count_exceeds_audit": int(
                    (a.pipeline_n_strict_ukb_free_units > a.audit_n_verified_ukb_free_catalog_units).sum()),
                "median_dims_present_same_lineage": float(a.n_dimensions_same_gwas_lineage.median()),
                "genes_with_ge1_verified_ukb_free_cohort_unit": a[a.n_independent_cohort_units >= 1].gene.tolist()}

    def verdict(sym: str) -> dict:
        a = audit[audit.gene == sym]
        if a.empty or "entrez_id" not in a or pd.isna(a.iloc[0].get("entrez_id")):
            return {"status": "not eligible"}
        x = a.iloc[0]
        return {
            "original_rank_natural": rk(x.rank_natural_ORIGINAL), "in_top50_natural": bool(x.in_top50_natural_original),
            "original_rank_adult": rk(x.rank_adult_ORIGINAL), "in_top50_adult": bool(x.in_top50_adult_original),
            "dimension_classes": {d: x[f"{d}_lineage_class"] for d in PRIMARY_DIMS},
            "dims_sharing_ukb_gwas_lineage": [d for d in PRIMARY_DIMS if x[f"{d}_lineage_class"] in SAME_LINEAGE_CLASSES],
            "dims_derived_from_selection": [d for d in PRIMARY_DIMS if x[f"{d}_lineage_class"] == DERIVED],
            "n_independent_units": int(x.n_independent_units),
            "independent_cohort_units": x.independent_cohort_units or "",
            "independent_qtl_datasets_strong": x.independent_molecular_datasets_strong or "",
            "independent_perturbation_units": x.independent_perturbation_units or "",
            "pipeline_vs_audit_ukb_free_catalog_units": [int(x.pipeline_n_strict_ukb_free_units),
                                                         int(x.audit_n_verified_ukb_free_catalog_units)],
            "scheme_ranks_natural": {s: rk(x[f"rank_natural_{s}"]) for s in res_nat},
            "scheme_in_top50_natural": {s: bool(x[f"in_top50_natural_{s}"]) for s in res_nat},
            "scheme_ranks_adult": {s: rk(x[f"rank_adult_{s}"]) for s in res_ad},
            "scheme_in_top50_adult": {s: bool(x[f"in_top50_adult_{s}"]) for s in res_ad},
            "dependence_note": x.dependence_note,
        }

    inputs = [GT_OUT / "direct_cognition_rank.csv", GT_OUT / "fine_mapping_support.csv",
              GT_OUT / "TOP50_HUMAN_COGNITION_GENES.csv", GT_OUT / "TOP50_ADULT_MODIFIABLE_GENES.csv",
              GT_OUT / "biological_modules.csv", GT_OUT / "positive_human_perturbations.csv",
              GT_DATA / "gwas_credible_sets_l2g.csv", GT_DATA / "opentargets_brain_coloc_compact.csv.gz",
              GT_DATA / "study_classification.csv", GT_DATA / "study_metadata.jsonl",
              GT_DATA / "master_gene_universe.parquet", GT_DATA / "module_membership.csv",
              GT_DATA / "developmental_classification.parquet"]
    summary = {
        "built_at": utc_now(),
        "script": "pipelines/sprint3_1/rank_dependency_audit.py",
        "status_of_ranks": "TRIAGE, not truth. No evidence was added, no dimension added, no weighted score built.",
        "rank_conventions": ("rank = RRA consensus rank among ALL eligible genes (method=min), as consensus_rank in the "
                             "committed Top-50 CSVs; delta = scheme rank - ORIGINAL rank (positive = fell); in_top50 = "
                             "in the scheme's top-600 -> one-gene-per-LD-block -> head(50) list; None = no evidence "
                             "under that scheme (no rank)."),
        "inputs_sha256": {str(p.relative_to(REPO_ROOT)): sha256(p) for p in inputs},
        "reproduction": repro,
        "sanity_checks": {
            "per_gate_dimension_presence_matches_original_n_dimensions_present": {"natural": nat_count_ok,
                                                                                  "adult": ad_count_ok},
            "catalog_unit_recount_matches_pipeline_all_scope_genes": bool(
                audit.catalog_units_recount_matches_pipeline.dropna().all()),
            "finemap_score_recomputed_matches_all_scope_genes": bool(
                audit.finemap_recomputed_matches.dropna().astype(bool).all()),
            "scope_genes_not_eligible": missing,
        },
        "gene_scope": {"n_genes": int(len(audit)), "named_genes": NAMED_GENES,
                       "n_in_natural_top50": int(audit.in_top50_natural_original.sum()),
                       "n_in_adult_top50": int(audit.in_top50_adult_original.sum())},
        "lineage_vocabulary": VOCAB, "extra_value_allowed": UNDETERMINED,
        "dimension_level_lineage": {
            "direct": {"class": SAME, "basis": "MAGMA on Davies 2018 (CHARGE+COGENT+UKB); also the ELIGIBILITY FLOOR of every scheme (MAGMA FDR<0.05)"},
            "replication": {"class": OVERLAP, "basis": "strict catalog units (count includes Davies' own PMID unit and UKB-listed units) + Savage 2018 Z/100 (shares UKB)"},
            "finemap": {"class": SAME, "basis": "Open Targets GWAS credible sets + L2G of the strict-tier studies (UKB-heavy); per-gene reachability from UKB-free studies evaluated"},
            "coloc": {"class": SAME, "gwas_half": SAME, "qtl_half": INDEP_MOLECULAR,
                      "basis": "brain QTL (GTEx, ROSMAP, BrainSeq, CommonMind, ...) x direct-cognition GWAS; queried only for the 400 Davies-top genes"},
            "direction": {"class": SAME, "basis": "sign agreement over the same colocalisation records"},
            "positive_human": {"class": INDEP_PERTURB, "basis": "2q12.3 duplication CNV-GWAS (PMID 39667348); UKB share undetermined; present for 2 eligible genes (SOWAHC, SEPTIN10)"},
            "adult_modifiability": {"class": EXPRESSION, "basis": "GTEx v10 + BrainSpan; not association evidence"},
            "module": {"class": DERIVED, "basis": "modules built on Davies FDR<0.01 genes; module rank uses Davies evidence share"},
            "extreme": {"class": OVERLAP, "basis": "sensitivity-only; Zabaneh controls (HRS) are a CHARGE cohort"},
            "math": {"class": SAME, "basis": "sensitivity-only; UKB FI4 item"},
        },
        "study_registry": reg_info,
        "independent_units_top50": {"natural": indep_stats(list(top_nat.gene)),
                                    "adult": indep_stats(list(top_ad.gene)),
                                    "union": indep_stats(list(dict.fromkeys(list(top_nat.gene) + list(top_ad.gene))))},
        "sensitivity_natural": {"dimensions": names_nat, **sch_nat},
        "sensitivity_adult": {"dimensions": names_ad, **sch_ad},
        "named_gene_verdicts": {s: verdict(s) for s in NAMED_GENES},
        "caveats": [
            "Every scheme keeps the ORIGINAL eligibility floor (Davies MAGMA FDR<0.05), so even INDEPENDENT_ONLY "
            "and LEAVE_LINEAGE_OUT rank only genes the UKB-containing GWAS already selected.",
            "UKB-free is not Davies-free: Davies 2018 includes CHARGE and COGENT cohorts, and cohort membership of "
            "the 'verified UKB-free' catalog cohorts in CHARGE/COGENT is not recorded in the repository.",
            "Studies with no cohort record (e.g. Lee 2018 cognitive performance, Lam 2017, Sniekers 2017, Coleman "
            "2019) are UKB_UNKNOWN -> UNDETERMINED, never independent (dependency rule D005).",
            "The pipeline's n_strict_ukb_free_units counts Perry 2025 (PMID 39891803) as UKB-free because its "
            "cohort list element is 'UKB ' with a trailing space; the cohort string names UKB. Lahti 2022 "
            "('multiple') is unverifiable. Both are re-classified here.",
            "Strong-coloc QTL datasets are counted as independent units per the brief, but the GWAS half of every "
            "colocalisation is the same UKB-heavy lineage; ROSMAP/CommonMind/BrainSeq/GTEx donor overlap is not "
            "resolved in the repository. The QTL half is not a separate consensus dimension, so no scheme can "
            "rank on it without adding a dimension (forbidden).",
            "ClinGen HI=3/TS=3 is counted as a perturbation unit per the brief; the repository holds only the "
            "MONDO ID, so relevance to cognition (vs e.g. cardiac or cancer phenotypes) is not verified here, and "
            "HI=3 is loss-of-function harm, never evidence that raising the gene raises cognition.",
            "The module dimension gives all 310 M01 genes rank 1, so LEAVE_LINEAGE_OUT (natural) is essentially "
            "module membership with massive ties; its top 50 is decided by tie-breaking, not evidence. The same "
            "M01 floor creates rank plateaus in other schemes (e.g. many genes tie at one rank under "
            "LINEAGE_COLLAPSED_MEAN, natural): a gene AT the cutoff rank may be in or out of a top 50 by sort "
            "order alone -- see top50_cutoff_ties and top50_membership_tie_decided_* (true also for ORIGINAL).",
            "A gene outside a scheme's top 50 is not 'refuted': in_top50 is a triage flag.",
            "Collapsed lineage lists are re-ranked before RRA; using the raw minimum would reward genes measured "
            "on more lineage dimensions, which is the multiple counting being removed.",
        ],
    }
    JSON_OUT.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps({"reproduction": {k: v for k, v in repro.items() if k in (
        "ORIGINAL_reproduces_committed_top50", "discrepancy_flag")},
        "natural_overlap": {k: v["top50_overlap_with_original"] for k, v in sch_nat["schemes"].items()},
        "adult_overlap": {k: v["top50_overlap_with_original"] for k, v in sch_ad["schemes"].items()},
        "csv": str(CSV_OUT), "json": str(JSON_OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
