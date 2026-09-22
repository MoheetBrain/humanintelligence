"""Guardrail tests for the Sprint-3 gene tournament.

Each test encodes an error that was actually made, or actually caught, during the sprint.
A guard that does not run is decoration, so these live beside the pipeline and run under
pyproject's ``testpaths``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipelines" / "gene_tournament"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import classify_studies as cs  # noqa: E402
from rank_aggregation import borda_score, pareto_front, rra_score  # noqa: E402

REPORTS = ROOT / "reports" / "gene_tournament"
DATA = ROOT / "data" / "gene_tournament"
CHANNEL_CLASS = {"general_cognition": "direct_cognition", "memory": "direct_cognition",
                 "educational_attainment": "proxy"}


# ------------------------------------------------------------------ rank aggregation --
def test_rra_rewards_consistent_top_ranks_over_middling():
    assert rra_score([0.01, 0.01, 0.01])[1] < rra_score([0.5, 0.5, 0.5])[1]


def test_rra_ignores_missing_rather_than_penalising():
    rho, p, n = rra_score([0.01, float("nan"), float("nan")])
    assert n == 1 and not math.isnan(p)


def test_borda_and_pareto_basic():
    assert borda_score([0.2, float("nan"), 0.4]) == pytest.approx(0.3)
    import numpy as np
    front = pareto_front(np.array([[0.1, 0.1], [0.2, 0.2], [0.1, 0.9]]))
    assert list(front) == [True, False, False]


# ------------------------------------------------------------------ study classifier --
def _tier(trait, sample="1,000 European ancestry individuals", channels=("general_cognition",), cohort=None, pmid="1"):
    row = {"reported_trait": trait, "disease_trait": "", "initial_sample_size": sample,
           "cohort": cohort, "pubmed_id": pmid}
    return cs.classify(row, CHANNEL_CLASS, set(channels))["tier"]


def test_ea_decomposition_filed_under_cognition_is_excluded():
    assert _tier("Cognitive aspects of educational attainment", pmid="33414549") == "excluded_ea_or_cross_trait"


def test_mtag_is_not_strict():
    assert _tier("Intelligence (MTAG)") == "direct_mtag"


def test_clinical_population_joined_by_or_is_clinical_not_cross_trait():
    assert _tier("Cognitive performance in schizophrenia or bipolar disorder") == "direct_clinical_or_ageing"


def test_or_in_sample_description_does_not_trigger_exclusion():
    # The audit bug: a sample string containing "or" sent memory studies to 'excluded'.
    assert _tier("Verbal memory performance", sample="adults or older adults") == "direct_strict"


def test_alzheimer_cohort_is_ageing_tier():
    assert _tier("Memory performance", cohort=["ADNI"]) == "direct_clinical_or_ageing"


def test_ea_channel_is_proxy():
    assert _tier("Educational attainment", channels=("educational_attainment",)) == "proxy"


# ----------------------------------------------------------------- master universe ----
@pytest.fixture(scope="module")
def universe():
    path = DATA / "master_gene_universe.parquet"
    if not path.exists():
        pytest.skip("master universe not built")
    return pd.read_parquet(path)


def test_proxy_only_genes_have_no_strict_direct_evidence(universe):
    bad = universe[universe.proxy_only & (universe.n_strict_studies > 0)]
    assert bad.empty


def test_ambiguous_aliases_are_not_silently_resolved(universe):
    amb = universe[universe.symbol_resolution == "ambiguous_alias"]
    assert (amb.hgnc_id.fillna("") == "").all()


# ------------------------------------------------------------ MAGMA verification ------
def test_x01_gene_layer_verified_by_recomputation():
    path = sorted((ROOT / "data/raw/magma_x01").glob("*/REPLICATION_CHECK.json"))
    if not path:
        pytest.skip("replication check not run")
    rec = json.loads(path[-1].read_text())
    assert rec["deterministic_agreement"]["nsnps_and_nparam_identical_for_every_gene"] is True
    assert rec["verdict"] == "REPRODUCED_WITHIN_MONTE_CARLO_ERROR"
    assert rec["monte_carlo_instability"]["n_genes_changing_significance"] >= 0


# ----------------------------------------------------------------- extreme tail -------
def test_mode_2_is_declared_not_computable():
    path = REPORTS / "extreme_tail_summary.json"
    if not path.exists():
        pytest.skip("extreme tail not run")
    s = json.loads(path.read_text())
    assert s["mode_2_individual_level"]["status"] == \
        "INDIVIDUAL-LEVEL COMMONALITY NOT COMPUTABLE WITH CURRENT ACCESS"


# ------------------------------------------------------------------ 2q12.3 ------------
def test_2q12_3_uses_the_verified_hg19_interval_genes():
    rec = yaml.safe_load((ROOT / "atlases/positive_genetics/2q12_3_duplication.yaml").read_text())
    genes = {g["symbol"] for g in rec["duplicated_interval"]["genes"]}
    assert genes == {"EDAR", "SH3RF3", "SEPTIN10", "SOWAHC"}
    assert "genes" not in rec, "the superseded cytoband gene list must not sit under 'genes'"
    assert "SLC5A7" not in genes


def test_positive_perturbations_table_uses_corrected_genes():
    path = REPORTS / "positive_human_perturbations.csv"
    if not path.exists():
        pytest.skip("Part J not built")
    j = pd.read_csv(path)
    row = j[j.evidence_id == "POSGEN:2q12.3_duplication"].iloc[0]
    assert "SLC5A7" not in row.genes and "EDAR" in row.genes


def test_lof_burden_is_never_recorded_as_positive():
    path = REPORTS / "positive_human_perturbations.csv"
    if not path.exists():
        pytest.skip("Part J not built")
    j = pd.read_csv(path)
    rp05 = j[j.evidence_id == "CODEX:RP05"].iloc[0]
    assert "NEGATIVE" in rp05.direction


# ------------------------------------------------------------------ within family -----
def test_within_family_has_no_fabricated_ranks():
    path = REPORTS / "within_family_rank.csv"
    if not path.exists():
        pytest.skip("Part F not built")
    f = pd.read_csv(path)
    assert f.within_family_rank.isna().all()
    assert (f.within_family_status == "NOT_COMPUTABLE_WITH_CURRENT_ACCESS").all()


# ----------------------------------------------------------------- pathway panel ------
def test_activity_dependent_anchor_is_not_the_erk_cascade():
    path = REPORTS / "pathway_hypothesis_panel.csv"
    if not path.exists():
        pytest.skip("panel not built")
    p = pd.read_csv(path).set_index("hypothesis")
    assert p.loc["activity_dependent_transcription", "anchor_set"] != "GO:0070374"


def test_global_fdr_is_a_correct_bh_over_all_sets_per_conditioning():
    """Global BH is NOT uniformly stricter than within-collection BH (pooling SynGO's many
    small P-values lowers GO BP's thresholds), so the guard is correctness, not an
    inequality: FDR_global must equal BH over every set in its conditioning run."""
    import numpy as np
    path = REPORTS / "pathway_enrichment.csv"
    if not path.exists():
        pytest.skip("enrichment not built")
    e = pd.read_csv(path)
    for _, grp in e.groupby("conditioning"):
        p = grp.P.to_numpy()
        o = np.argsort(p); n = len(p)
        q = p[o] * n / (np.arange(n) + 1)
        q = np.minimum.accumulate(q[::-1])[::-1]
        expect = np.empty(n); expect[o] = np.minimum(q, 1)
        assert np.allclose(expect, grp.FDR_global.to_numpy())


# ------------------------------------------------------------- directionality ---------
def test_coloc_trait_classifier_separates_ea_and_applies_polarity():
    import build_consensus as bc
    assert bc.classify_trait("Educational attainment (confirmatory factor analysis Factor 10)") == \
        "educational_attainment_proxy"
    assert bc.classify_trait("Qualifications - A levels/AS levels or equivalent") == \
        "educational_attainment_proxy"
    assert bc.classify_trait("Fluid intelligence score") == "direct_cognition"
    assert bc.NEG_POLARITY_RX.search("Reaction time")


# ------------------------------------------------------------------ top-50 files ------
@pytest.mark.parametrize("name", ["TOP50_HUMAN_COGNITION_GENES.csv", "TOP50_ADULT_MODIFIABLE_GENES.csv"])
def test_top50_one_gene_per_ld_block_and_required_columns(name):
    path = REPORTS / name
    if not path.exists():
        pytest.skip(f"{name} not built")
    t = pd.read_csv(path)
    assert len(t) <= 50
    assert t["ld_block_r0.2"].is_unique
    required = {"gene", "consensus_rank", "rank_interval", "direct_cognition_rank", "extreme_tail_rank",
                "math_rank", "family_rank", "fine_mapping_rank", "coloc_rank", "adult_modifiability_rank",
                "positive_human_rank", "module_rank", "safety_flags", "number_independent_cohorts",
                "major_support", "major_counterevidence", "next_kill_test"}
    assert required <= set(t.columns)
    assert (t.family_rank == "NOT_COMPUTABLE").all()


# ------------------------------------------------------------- later-sprint guards ----
def test_extreme_tail_distribution_stats_separates_people_from_genes():
    path = REPORTS / "extreme_tail_distribution_stats.csv"
    if not path.exists():
        pytest.skip("Part C not run")
    d = pd.read_csv(path)
    person = d[d.unit_of_analysis.str.startswith("individual")]
    assert len(person) >= 15
    assert (person.status == "INDIVIDUAL-LEVEL COMMONALITY NOT COMPUTABLE WITH CURRENT ACCESS").all()
    assert person.value.isna().all()
    assert d[d.status == "computed_gene_level_analogue"].unit_of_analysis.str.startswith("GENE").all()


def test_positional_l2g_calls_never_count_as_support():
    """Guards the object-dtype bug: `~` on a Python-bool object column returns -2/-1 (truthy),
    which first reported 602 supported genes instead of 34."""
    path = DATA / "gwas_credible_sets_l2g.csv"
    if not path.exists():
        pytest.skip("Part G not fetched")
    cs_ = pd.read_csv(path)
    top = cs_[cs_.l2g_rank == 1]
    supported = top[(top.l2g_score >= 0.5) & (~top.positional_driven.fillna(False).astype(bool))]
    g = pd.read_csv(REPORTS / "fine_mapping_support.csv")
    assert set(g[g.n_supported_loci > 0].gene) == set(supported.gene)


def test_truth_table_sprint3_layer_records_previous_status():
    csv_ = ROOT / "reports" / "project_truth_table.csv"
    t = pd.read_csv(csv_)
    syn = t[t.hypothesis.str.startswith("SYNAPTIC BIOLOGY")].iloc[0]
    assert syn.current_status == "PROMISING_BUT_UNRESOLVED"
    assert "STATUS CHANGED IN SPRINT 3: UNRESOLVED -> PROMISING_BUT_UNRESOLVED" in syn.why
    adgrb1 = t[t.hypothesis.str.startswith("ADGRB1")].iloc[0]
    assert adgrb1.current_status == "UNRESOLVED"
    assert list(t.columns)[:3] == ["hypothesis", "supporting_evidence", "contradictory_evidence"]
    assert len(t.columns) == 16


def test_compact_coloc_excludes_nothing_but_non_brain_and_non_cognition():
    path = DATA / "opentargets_brain_coloc_compact.csv.gz"
    if not path.exists():
        pytest.skip("compact coloc not built")
    c = pd.read_csv(path)
    assert c.qtl_is_brain.all()
    assert set(c.trait_class) <= {"direct_cognition", "educational_attainment_proxy"}


def test_x01_record_is_corrected_and_schema_valid():
    import jsonschema
    rec = yaml.safe_load((ROOT / "analyses/external/X01_cell_type_enrichment.yaml").read_text())
    jsonschema.validate(rec, json.loads((ROOT / "schemas/external_analysis.schema.json").read_text()))
    assert rec["delivery"]["mechanism"] == "local_clone_path"
    assert rec["verification_status"] == "artefacts_received_pending_check"
    # The cell-type claim is still not re-derived here, so it must not be marked verified.
    assert rec["provenance_class"] == "external_analysis_unverified"
