"""Tests for the Sprint 3.1 rank-dependency audit (pipelines/sprint3_1/rank_dependency_audit.py).

Run:  PYTHONPATH=src .venv/bin/python -m pytest -q pipelines/sprint3_1/test_rank_dependency_audit.py

The tests read the committed outputs; if they are missing, the audit is run once first.
The ORIGINAL-scheme check compares against the Sprint 3 Top-50 CSVs directly, not against
the audit's own reproduction report, so it cannot pass by the audit agreeing with itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "reports" / "sprint3_1" / "rank_dependency_audit.csv"
SUMMARY = ROOT / "reports" / "sprint3_1" / "rank_dependency_audit_summary.json"
NAMED = ["NEGR1", "DCC", "EXOC4", "NT5DC2", "BSN", "SYT1", "NSF", "ERBB3", "GRIA4",
         "KCNJ3", "RIMS2", "CADM2", "PTPRT", "MEF2C"]
# The fixed vocabulary from the Sprint 3.1 brief, plus UNDETERMINED (allowed when the
# files cannot decide, and then a reason must be recorded).
VOCAB = {"SAME_GWAS_SIGNAL_UKB", "OVERLAPPING_SAMPLE_REPLICATION", "INDEPENDENT_COHORT",
         "INDEPENDENT_MOLECULAR_DATASET", "INDEPENDENT_PERTURBATION", "DERIVED_FROM_SELECTION",
         "EXPRESSION_ANNOTATION", "ABSENT"}
ALLOWED = VOCAB | {"UNDETERMINED"}
REQUIRED_SCHEMES = ["ORIGINAL", "LINEAGE_COLLAPSED_BEST", "LINEAGE_COLLAPSED_MEAN",
                    "INDEPENDENT_ONLY", "LEAVE_LINEAGE_OUT"]


@pytest.fixture(scope="module")
def outputs():
    if not (CSV.exists() and SUMMARY.exists()):
        subprocess.run([sys.executable, str(ROOT / "pipelines" / "sprint3_1" / "rank_dependency_audit.py")],
                       check=True, cwd=ROOT)
    return pd.read_csv(CSV), json.loads(SUMMARY.read_text())


def test_csv_exists_contains_named_genes_and_is_small(outputs):
    audit, _ = outputs
    assert CSV.exists()
    assert CSV.stat().st_size < 5 * 1024 * 1024
    missing = sorted(set(NAMED) - set(audit.gene))
    assert not missing, f"named genes missing from the audit: {missing}"
    for col in ("n_dimensions_present", "n_dimensions_same_gwas_lineage", "n_independent_units",
                "dependence_note"):
        assert col in audit.columns
        assert audit.loc[audit.gene.isin(NAMED), col].notna().all()


def test_lineage_classes_are_from_the_fixed_vocabulary(outputs):
    audit, _ = outputs
    single = [c for c in audit.columns if c.endswith("_lineage_class")]
    multi = [c for c in audit.columns if c.endswith("_lineage_classes_all")]
    assert len(single) >= 10 and len(multi) >= 10
    for c in single:
        bad = set(audit[c].dropna()) - ALLOWED
        assert not bad, f"{c} has values outside the vocabulary: {bad}"
    for c in multi:
        for v in audit[c].dropna():
            bad = set(str(v).split("|")) - ALLOWED
            assert not bad, f"{c} has values outside the vocabulary: {bad}"
    # UNDETERMINED is only acceptable with a stated reason
    for c in single:
        dim = c[: -len("_lineage_class")]
        src = f"{dim}_lineage_sources"
        if src in audit.columns:
            und = audit[audit[c] == "UNDETERMINED"]
            assert und[src].fillna("").str.len().gt(20).all(), f"{c}: UNDETERMINED without a reason"


def test_original_scheme_reproduces_committed_top50(outputs):
    audit, summary = outputs
    rep = summary["reproduction"]
    if rep["discrepancy_flag"]:
        # Allowed by the brief, but only if the discrepancy is actually recorded.
        assert rep["ORIGINAL_reproduces_committed_top50"] is False
        assert rep["natural"]["n_position_mismatches"] or rep["adult"]["n_position_mismatches"] \
            or not rep["natural"]["same_gene_set"] or not rep["adult"]["same_gene_set"]
        return
    assert rep["ORIGINAL_reproduces_committed_top50"] is True
    for gate, name in (("natural", "TOP50_HUMAN_COGNITION_GENES.csv"),
                       ("adult", "TOP50_ADULT_MODIFIABLE_GENES.csv")):
        ref = pd.read_csv(ROOT / "reports" / "gene_tournament" / name)
        cols = [f"rank_{gate}_ORIGINAL", f"in_top50_{gate}_ORIGINAL", f"top50_position_{gate}_ORIGINAL"]
        m = ref[["gene", "consensus_rank"]].merge(audit[["gene"] + cols], on="gene", how="left")
        assert m[cols[0]].notna().all(), f"{gate}: committed Top-50 gene missing from the audit"
        assert (m[cols[0]].astype(int) == m.consensus_rank.astype(int)).all(), f"{gate}: consensus_rank differs"
        assert m[cols[1]].astype(bool).all()
        assert m[cols[2]].astype(int).tolist() == list(range(1, 51)), f"{gate}: Top-50 order differs"
        sch = summary[f"sensitivity_{gate}"]["schemes"]
        assert sch["ORIGINAL"]["top50_genes_in_order"] == ref.gene.tolist()
        assert sch["ORIGINAL"]["top50_overlap_with_original"] == 50


def test_required_schemes_are_reported(outputs):
    audit, summary = outputs
    for gate in ("natural", "adult"):
        sch = summary[f"sensitivity_{gate}"]["schemes"]
        for s in REQUIRED_SCHEMES:
            assert s in sch, f"{gate}: scheme {s} missing"
            assert f"rank_{gate}_{s}" in audit.columns and f"in_top50_{gate}_{s}" in audit.columns
            assert 0 <= sch[s]["top50_overlap_with_original"] <= 50
        assert summary[f"sensitivity_{gate}"]["spearman_between_schemes"]
