"""Guard tests for Sprint 5A (offline; read committed outputs)."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pytest

R = Path(__file__).resolve().parents[2]
O5A, D5A = R / "reports/sprint5a", R / "data/sprint5a"


def test_protocol_hash_recorded():
    rec = re.findall(r"RULES_JSON_SHA256:\s*([0-9a-f]{64})", (R / "research/sprint5a/protocol.md").read_text())[-1]
    assert rec == hashlib.sha256((R / "research/sprint5a/protocol_rules.json").read_bytes()).hexdigest()


def test_no_credentials_in_tracked_files():
    files = subprocess.run(["git", "ls-files", "reports/sprint5a", "data/sprint5a", "pipelines/sprint5a", "research/sprint5a",
                            "data/sprint4/gate_a_access.json", "data/raw/sprint5a"],
                           cwd=R, capture_output=True, text=True).stdout.split()
    for f in files:
        p = R / f
        if p.suffix in (".parquet", ".xlsx") or not p.exists():
            continue
        txt = p.read_text(errors="ignore")
        assert not re.search(r"AI" + r"za[0-9A-Za-z_-]{35}|ey" + r"J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", txt), f


def test_brainscope_coloc_never_fabricated():
    b = pd.read_parquet(O5A / "brainscope_typed_evidence.parquet")
    assert set(b.evidence_type) <= {"DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT", "REGULATORY_ELEMENT_SUPPORT",
                                    "GRN_SUPPORT", "COLOC_NOT_TESTABLE_WITH_PUBLIC_OUTPUT"}


def test_alphagenome_weighted_only_when_measured_agrees():
    u = pd.read_parquet(D5A / "s5_integrated/evidence_units.parquet")
    ag = u[(u.v2g_class == "SEQUENCE_MODEL") & (u.status == "OK")]
    v = pd.read_csv(O5A / "alphagenome_vs_observed.csv")
    ok = set(zip(v[(v.agreement == "AGREE") & (v.comparator_tier == "PRIMARY_MEASURED")].gene, [True] * len(v)))
    assert set(ag.gene) <= {g for g, _ in ok}


def test_single_cell_rows_never_create_new_cohort_units():
    d = pd.read_csv(O5A / "directionality_resolution_5a.csv")
    s4 = pd.read_csv(R / "reports/sprint4/directionality_resolution.csv").set_index("gene")
    for r in d.itertuples():
        before = set(str(s4.loc[r.gene].tissues_or_cohorts).split(";")) if r.gene in s4.index else set()
        after = set(str(r.tissues_or_cohorts).split(";"))
        assert after - before <= {"rosmap"}, r.gene


def test_shortlist_c_not_forced():
    c = pd.read_csv(O5A / "SHORTLIST_C_adult_modifiable.csv")
    if len(c):
        assert (c.locus_stratum.isin(["L1", "L2"]) & c.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])
                & c.direction_stratum.eq("D1")).all()


def test_convergence_inverted_math_not_counted():
    c = pd.read_csv(O5A / "cross_phenotype_convergence.csv")
    inv = c[c.convergence_categories.str.contains("INVERTED", na=False)]
    assert not inv.convergence_categories.str.contains(r"GENERAL\+MATH_PROXY\(Gq", regex=True).any()


def test_sprint5_outputs_untouched_by_5a_hooks():
    diff = subprocess.run(["git", "diff", "--stat", "reports/sprint5", "data/sprint5"], cwd=R, capture_output=True, text=True).stdout
    assert diff.strip() == ""


@pytest.mark.parametrize("f", ["opentargets_2606_refresh.parquet", "alphagenome_cognition_variants.parquet",
                               "variant_gene_cell_hypotheses.parquet", "USER_ACCESS_REQUIRED.md", "SPRINT5A_FINAL.md"])
def test_required_outputs_exist(f):
    assert (O5A / f).exists()


def test_dossier_cap():
    assert len(list((O5A / "gene_dossiers").glob("*.md"))) <= 10
