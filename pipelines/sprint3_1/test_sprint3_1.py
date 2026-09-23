"""Guards for the Sprint 3.1 synaptic recon pass.

These run offline against committed outputs. They fail if a later edit silently changes what
the recon pass established: the fixed gene universe, the propagation of GO sets, the exact
Sprint-3 reproduction, the frozen direction thresholds, and the terminology correction.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
D31 = REPO / "data" / "sprint3_1"
R31 = REPO / "reports" / "sprint3_1"


def _sets(path: Path) -> dict[str, set[int]]:
    return {p[0]: {int(g) for g in p[1:]} for p in
            (ln.split() for ln in path.read_text(encoding="utf-8").splitlines()) if p}


def test_covariates_cover_full_universe_without_missing():
    cov = pd.read_csv(D31 / "gene_covariates_full.txt", sep="\t")
    assert len(cov) == 18418, "every gene in the Davies genes.raw must carry covariates"
    assert not cov.isna().any().any(), "missing covariates would make MAGMA drop genes (the Sprint-3 defect)"
    assert (cov.log_annotation_density >= 0).all()


def test_go_sets_are_propagated_true_path():
    cc = _sets(D31 / "go_cc_prop.setannot")
    # dendrite and axon are neuron projections; propagation must make them subsets
    assert cc["GO_0030425"] <= cc["GO_0043005"]
    assert cc["GO_0030424"] <= cc["GO_0043005"]
    bp = _sets(D31 / "go_bp_prop.setannot")
    assert len(bp["GO_0022008"]) > 500, "propagated neurogenesis should far exceed the 79 direct annotations"


def test_recon_decomposition_is_exact():
    s = _sets(D31 / "recon_sets.setannot")
    assert s["PRE_ONLY"] | s["POST_ONLY"] | s["PRE_AND_POST"] == s["PRE_OR_POST"]
    assert not (s["PRE_ONLY"] & s["POST_ONLY"])
    assert s["PRE_AND_POST"] == s["PRE"] & s["POST"]


def test_sprint3_run_reproduced_exactly():
    rep = json.loads((R31 / "recon_magma_summary.json").read_text())["s3_reproduction"]
    assert len(rep) == 6 and all(v["identical"] for v in rep.values())


def test_every_joint_model_was_matched_in_every_spec():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import run_recon_magma as RR
    jt = pd.read_csv(R31 / "pre_vs_post_joint_tests.csv")
    jt = jt[jt.analysis == "joint_two_sided"]
    for spec, grp in jt.groupby("spec"):
        assert set(RR.JOINT_MODELS) <= set(grp.model), f"unmatched joint model in spec {spec}"


def test_contrast_terms_are_two_sided_and_flagged():
    jt = pd.read_csv(R31 / "pre_vs_post_joint_tests.csv")
    c = jt[jt.is_contrast_term]
    assert set(c.variable) >= {"PRE_ONLY", "POST_ONLY", "PREMEMB_ONLY", "PREPROC_ONLY", "RELEASE_ONLY"}
    assert (c.analysis == "joint_two_sided").all()


def test_direction_thresholds_not_relaxed():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import qtl_independence_audit as Q
    assert (Q.MIN_UNITS, Q.MIN_AGREE, Q.STRENGTH) == (3, 0.8, 0.8)
    s = json.loads((R31 / "negr1_qtl_independence_audit_summary.json").read_text())
    assert s["NEGR1"]["n_independent_units"] <= s["NEGR1"]["sprint3_rows_counted"]
    assert s["NEGR1"]["direction_resolved_under_frozen_rule_on_units"] is False


def test_extreme_tail_ratio_is_reported_as_a_range_not_a_proof():
    r = json.loads((R31 / "extreme_tail_reassessment.json").read_text())
    lo, hi = r["ratio_range"]
    assert lo < 1 < hi, "the reassessment must show the ratio straddles 1 under plausible assumptions"


def test_adult_hierarchy_never_claims_intervention_readiness():
    t = pd.read_csv(R31 / "adult_evidence_hierarchy.csv")
    assert not t.ADULT_INTERVENTION_READY.astype(bool).any()
    assert not t.corrected_label.str.contains("MODIFIABLE", case=False).any()
    dcc = t[t.gene == "DCC"].iloc[0]
    assert dcc.expression_timing == "PRENATAL_DOMINANT"
    assert "functional_timing" in t.columns, "expression and functional timing must be separate columns"


@pytest.mark.parametrize("name", ["SYNAPTIC_RECON_REPORT.md", "pre_vs_post_joint_tests.csv",
                                  "pathway_conditioning_sensitivity.csv", "rank_dependency_audit.csv",
                                  "negr1_qtl_independence_audit.csv", "synaptic_system_map.csv",
                                  "extreme_tail_reassessment.md"])
def test_required_outputs_exist(name):
    assert (R31 / name).exists(), f"missing required Sprint 3.1 output {name}"
