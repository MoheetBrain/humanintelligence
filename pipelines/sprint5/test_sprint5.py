"""Guard tests for Sprint 5 (offline; read committed outputs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Sprint 4 and Sprint 5 both ship a module named `common`; import Sprint-5's under isolation and restore
# whatever was loaded before, so neither sprint's tests shadow the other's in one pytest session.
_HERE = str(Path(__file__).resolve().parent)
_saved = {k: sys.modules.pop(k) for k in ("common", "eb_shrink", "build_opentargets_refresh", "locus_confidence")
          if k in sys.modules}
sys.path.insert(0, _HERE)
import common as C  # noqa: E402
import eb_shrink as EB  # noqa: E402
from build_opentargets_refresh import feature_class  # noqa: E402
from locus_confidence import log10bf, stratum  # noqa: E402
sys.path.remove(_HERE)
for _k in ("common",):
    sys.modules.pop(_k, None)
sys.modules.update(_saved)


def test_rules_hash_matches_protocol():
    assert C.recorded_rules_hash() == C.sha256_file(C.RULES_JSON)
    rules = C.load_rules()
    assert "amendments" in rules and {a["id"] for a in rules["amendments"]} >= {"A1", "A2"}


def test_eb_shrink_monotone_sign_preserving_and_shrinks():
    rng = np.random.default_rng(0)
    z_all = np.concatenate([rng.standard_normal(20000), rng.normal(0, 3, 500)])
    pi = EB.fit(z_all)
    z = np.linspace(-12, 12, 241)
    mu = EB.posterior_mean(z, pi)
    assert np.all(np.diff(mu) >= -1e-9)
    assert np.all(np.sign(mu[z != 0]) == np.sign(z[z != 0]))
    assert np.all(np.abs(mu) <= np.abs(z) + 1e-12)


def test_bayes_factor_properties():
    assert log10bf(0.12, np.array([5.0]), np.array([0.0]))[0] < 0
    zs = np.array([6.0, 6.0])
    lo, hi = log10bf(0.12, zs, np.array([1.0, 3.0]))
    assert hi > lo
    assert stratum(1.2) == "L1" and stratum(0.6) == "L2" and stratum(0.1) == "L3" and stratum(-0.1) == "L4_DISCORDANT"
    assert stratum(float("nan")) == "NT"


def test_l2g_feature_classes():
    assert feature_class("distanceSentinelTssNeighbourhood") == "POSITIONAL"
    assert feature_class("proteinGeneCount500kb") == "POSITIONAL"
    assert feature_class("vepMaximum") == "CODING"
    assert feature_class("eQtlColocH4Maximum") == "QTL"
    assert feature_class("e2gMeanNeighbourhood") == "ENHANCER"


@pytest.fixture(scope="module")
def matrix():
    return pd.read_csv(C.OUT / "causal_gene_evidence_matrix.csv")


def test_moderate_or_high_needs_two_classes_or_rare(matrix):
    sets = json.loads((C.DATA / "rare_coding_gene_sets.json").read_text())
    for r in matrix[matrix.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].itertuples():
        cl = set(str(r.classes).split(";")) - {"", "nan"}
        assert len(cl) >= 2 or cl == {"RARE_CODING"}, r.gene
        assert not r.contested, r.gene
        assert r.locus_stratum in ("L1", "L2", "L3"), r.gene
    for r in matrix[matrix.gene_class == "CODING_CAUSAL_LOF_ONLY"].itertuples():
        assert r.gene in sets["exome_wide_cognition"]


def test_ea_proxy_never_counted_as_rare_coding_class(matrix):
    sets = json.loads((C.DATA / "rare_coding_gene_sets.json").read_text())
    ea_only = set(sets["exome_wide_cognition_incl_EA_proxy"]) - set(sets["exome_wide_cognition"])
    sub = matrix[matrix.gene.isin(ea_only)]
    assert not sub.classes.astype(str).str.contains("RARE_CODING").any()
    assert set(sub.perturbation_stratum) <= {"P4", "P5"}


def test_not_testable_is_never_negative():
    ag = pd.read_parquet(C.OUT / "alphagenome_cognition_variants.parquet")
    if "status" in ag.columns:
        assert ag.status.astype(str).str.startswith(("NOT_TESTABLE", "OK")).all()
    neg = pd.read_csv(C.OUT / "negative_results.csv")
    nt = neg[neg.status.astype(str).str.contains("NOT_TESTABLE")]
    assert not nt.result.astype(str).str.contains("NO_EFFECT").any()
    assert (neg.category == "GATE_A_WITHIN_FAMILY").any()


def test_dependency_graph_integrity():
    u = pd.read_parquet(C.DATA / "evidence_units.parquet")
    e = pd.read_parquet(C.DATA / "evidence_dependency_graph.parquet")
    v2g = u[(u.stream == "V2G") & (u.status == "OK")]
    has_parent = set(e[e.edge_type == "DERIVED_FROM"].from_unit)
    assert v2g.unit_id.isin(has_parent).all()
    assert (u[u.v2g_class.astype(str).str.startswith("NOT_A_CLASS:L2G")].independence_unit == "AGGREGATOR").all()
    assert ((e.edge_type == "SHARES_COHORT") & (e.from_unit == "LIN_ZABANEH")).any()
    assert u.unit_id.is_unique


def test_top20_and_top10_outputs():
    t = pd.read_csv(C.OUT / "TOP20_RESEARCH_PRIORITY_GENES.csv")
    assert len(t) >= 20
    need = {"gene_or_locus", "why_entered", "independent_human_evidence_streams", "coding_evidence",
            "common_regulatory_evidence", "math_evidence", "extreme_iq_evidence", "brainSCOPE", "AlphaGenome",
            "Open_Targets", "adult_QTL", "developmental_QTL", "cell_type", "direction", "human_perturbation",
            "pleiotropy_safety", "largest_contradiction", "missing_causal_arrow", "single_best_next_computation"}
    assert need <= set(t.columns)
    t10 = pd.read_csv(C.OUT / "TOP10_CAUSAL_GENE_CANDIDATES.csv")
    assert len(t10) == 10 and t10.has_gene_level_evidence.all()


def test_math53_verified_and_labelled():
    m = pd.read_csv(C.DATA / "math53_variants.csv")
    assert len(m) == 53 and m.rsid.is_unique
    assert m.build.astype(str).str.startswith("GRCh37").all()
    mp = pd.read_csv(C.OUT / "math53_gene_mapping.csv")
    assert set(mp.overlap_class) <= {"GENERAL_G_SHARED", "MATH_SPECIFIC_ORTHOGONAL", "MATH_PROXY_ONLY", "IMAGING_ONLY", "NOT_GENETIC"}


def test_chemistry_gate_closed():
    d = json.loads((C.OUT / "decision.json").read_text())
    assert d["chemistry_gate"] == "CLOSED"
    assert all(not r["6_safety_acceptable"] for r in d["gate_table"])


def test_genlang_not_counted_when_overlapping():
    lc = pd.read_csv(C.OUT / "locus_confidence_rank.csv")
    ov = json.loads((C.DATA / "genlang_overlap.json").read_text())["verdicts"]["genlang_piq_vs_davies2018"]["verdict"]
    if ov != "INDEPENDENT":
        assert (lc.independent_lineages_counted == "G&C").all()
