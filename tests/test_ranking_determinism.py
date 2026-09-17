"""Determinism and report format.

``models/uncertainty/uncertainty_spec_v0_1.yaml`` §4 makes byte-level determinism a
MANDATORY property, not an aspiration: a report that cannot be diffed between runs
cannot be reviewed, and a Monte Carlo ranking that shuffles on re-run invites readers
to treat sampling noise as new information.

The format tests are here too, because "machine-readable" is part of the same
promise: no comment lines, one header, fixed column order, fixed float precision.
"""

from __future__ import annotations

import csv
import io
import json

import numpy as np
import pytest

from blueprint.ranking.information_gain import facet_information_gain
from blueprint.ranking.report import CSV_COLUMNS, ROW_STATUS, render_csv, write_report
from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import facet_contribution_draws, score_cohort
from blueprint.ranking.synthetic import (
    ALL_FACETS,
    claim,
    normal_uniform_target,
    make_inputs,
    make_target,
)

DRAWS = 1500


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


@pytest.fixture
def cohort():
    return make_inputs(
        [
            make_target(
                "TGT:ALPHA",
                levels=dict.fromkeys(ALL_FACETS, 2) | {"safety_liability_burden": 1},
                claim_refs={"tractability": ["CLM:i:001"]},
            ),
            normal_uniform_target("TGT:BETA", 3),
            normal_uniform_target("TGT:GAMMA", 1, verdict="deprioritise"),
            make_target("TGT:DELTA", levels={"tractability": 2}, verdict=None),
        ],
        [claim("CLM:i:001", ["SRC:DB:opentargets:2026.06"])],
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_two_runs_with_the_same_seed_give_identical_csv_bytes(spec, cohort) -> None:
    first = render_csv(
        score_cohort(cohort, spec, n_draws=DRAWS, seed=1234),
        generated_on="2026-09-17",
    )
    second = render_csv(
        score_cohort(cohort, spec, n_draws=DRAWS, seed=1234),
        generated_on="2026-09-17",
    )
    assert first == second


def test_two_runs_with_different_seeds_give_different_bytes(spec, cohort) -> None:
    """Otherwise the determinism test above would be vacuous."""
    first = render_csv(score_cohort(cohort, spec, n_draws=DRAWS, seed=1), generated_on="2026-09-17")
    second = render_csv(score_cohort(cohort, spec, n_draws=DRAWS, seed=2), generated_on="2026-09-17")
    assert first != second


def test_written_files_are_byte_identical_across_runs(spec, cohort, tmp_path) -> None:
    """End-to-end through :func:`write_report`, including the information-gain sweep."""
    outputs = []
    for _ in range(2):
        result = score_cohort(cohort, spec, n_draws=DRAWS, seed=99)
        gains = facet_information_gain(result, cohort)
        artefacts = write_report(
            result,
            cohort,
            gains,
            root=tmp_path,
            reports_dir=tmp_path / "reports",
            generated_on="2026-09-17",
            generated_at="2026-09-17T00:00:00Z",
        )
        outputs.append((artefacts.csv_path.read_bytes(), artefacts.meta_path.read_bytes()))
    assert outputs[0][0] == outputs[1][0]
    assert outputs[0][1] == outputs[1][1]


def test_a_target_draw_does_not_depend_on_the_rest_of_the_cohort(spec) -> None:
    """Streams are keyed by ``(seed, target_id, facet)``, so adding a target to the
    cohort must not perturb any other target's distribution. Without this, every
    report row would change whenever curation added an unrelated target."""
    alpha = normal_uniform_target("TGT:ALPHA", 3)
    small = make_inputs([alpha])
    large = make_inputs([alpha, normal_uniform_target("TGT:BETA", 1), normal_uniform_target("TGT:GAMMA", 4)])

    small_row = score_cohort(small, spec, n_draws=DRAWS, seed=7).targets[0]
    large_row = next(
        t for t in score_cohort(large, spec, n_draws=DRAWS, seed=7).targets if t.target_id == "TGT:ALPHA"
    )
    assert small_row.composite_median == large_row.composite_median
    assert np.array_equal(small_row.composite_draws, large_row.composite_draws)


def test_facet_draws_are_reproducible_for_a_fixed_key(spec) -> None:
    target = normal_uniform_target("TGT:ALPHA", 3)
    first = facet_contribution_draws(spec, target, n_draws=64, seed=5)
    second = facet_contribution_draws(spec, target, n_draws=64, seed=5)
    assert set(first) == set(second)
    for facet_name in first:
        assert np.array_equal(first[facet_name], second[facet_name])


# ---------------------------------------------------------------------------
# CSV format
# ---------------------------------------------------------------------------


def test_csv_is_machine_readable_with_no_comment_lines(spec, cohort) -> None:
    payload = render_csv(score_cohort(cohort, spec, n_draws=DRAWS), generated_on="2026-09-17")
    text = payload.decode("utf-8")
    lines = text.splitlines()
    assert lines, "empty CSV"
    assert not any(line.startswith("#") for line in lines)
    assert not any(line.strip() == "" for line in lines)
    assert "\r" not in text

    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 4
    assert list(rows[0]) == list(CSV_COLUMNS)


def test_column_order_is_fixed(spec, cohort) -> None:
    payload = render_csv(score_cohort(cohort, spec, n_draws=DRAWS), generated_on="2026-09-17")
    header = payload.decode("utf-8").splitlines()[0]
    assert header == ",".join(CSV_COLUMNS)


def test_every_row_carries_its_own_provenance(spec, cohort) -> None:
    """A row torn out of the CSV must still say what it is."""
    result = score_cohort(cohort, spec, n_draws=DRAWS, seed=4242)
    payload = render_csv(result, generated_on="2026-09-17")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    for row in rows:
        assert row["status"] == ROW_STATUS == "PRELIMINARY"
        assert row["calibration_status"] == "uncalibrated_subjective"
        assert row["rubric_version"]
        assert row["ranking_spec_version"]
        assert row["uncertainty_spec_version"]
        assert row["model_run_seed"] == "4242"
        assert row["generated_on"] == "2026-09-17"
        assert row["n_draws"] == str(DRAWS)


def test_rows_are_ordered_by_median_rank(spec, cohort) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    payload = render_csv(result, generated_on="2026-09-17")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    ranks = [float(row["rank_median"]) for row in rows]
    assert ranks == sorted(ranks)


def test_all_required_columns_are_present(spec) -> None:
    """The deliverable's required column set, checked by name so a rename is caught."""
    required = {
        "status",
        "coverage",
        "independent_source_count",
        "red_team_verdict",
        "n_downgrades",
        "composite_median",
        "composite_p05",
        "composite_p95",
        "rank_median",
        "rank_p05",
        "rank_p95",
        "tier",
        "most_informative_facet",
        "calibration_status",
        "dossier_depth",
        "model_run_seed",
        "generated_on",
    }
    required |= {f"d{n}_level" for n in range(1, 7)}
    required |= {f"d{n}_median" for n in range(1, 7)}
    assert required <= set(CSV_COLUMNS)


def test_floats_are_written_at_fixed_precision(spec, cohort) -> None:
    payload = render_csv(score_cohort(cohort, spec, n_draws=DRAWS), generated_on="2026-09-17")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    for row in rows:
        for column in ("coverage", "composite_median", "rank_median", "d1_median"):
            assert len(row[column].split(".")[1]) == 4, (column, row[column])


def test_an_unassessed_dimension_level_is_blank_not_zero(spec) -> None:
    """Writing 0 for "no facet feeding this dimension was assessed" would be the same
    contract violation the facet records forbid."""
    inputs = make_inputs([make_target("TGT:SPARSE", levels={"tractability": 2})])
    payload = render_csv(score_cohort(inputs, spec, n_draws=DRAWS), generated_on="2026-09-17")
    row = next(iter(csv.DictReader(io.StringIO(payload.decode("utf-8")))))
    assert row["d3_level"] == ""
    assert row["d3_n_assessed"] == "0"
    assert row["d6_level"] == "2"  # tractability feeds D6


# ---------------------------------------------------------------------------
# Sidecar
# ---------------------------------------------------------------------------


def test_sidecar_records_spec_hashes_seed_and_reader(spec, cohort, tmp_path) -> None:
    result = score_cohort(cohort, spec, n_draws=DRAWS, seed=11)
    artefacts = write_report(
        result,
        cohort,
        facet_information_gain(result, cohort),
        root=tmp_path,
        reports_dir=tmp_path / "reports",
        generated_on="2026-09-17",
        generated_at="2026-09-17T00:00:00Z",
    )
    meta = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))

    assert meta["status"] == "PRELIMINARY"
    assert meta["produced_by"] == "agent:integration"
    assert set(meta["model"]["spec_sha256"]) == {"ranking", "rubric", "uncertainty"}
    assert all(len(h) == 64 for h in meta["model"]["spec_sha256"].values())
    assert meta["model"]["calibration_status"] == "uncalibrated_subjective"
    assert meta["run"]["seed"] == 11
    assert meta["run"]["n_draws"] == DRAWS
    assert meta["run"]["reader"] == "synthetic"
    assert meta["run"]["n_targets_ranked"] == 4
    assert set(meta["sensitivity"]["aggregation_kendall_tau_b"]) == {
        "minimum",
        "weighted_additive",
    }
    assert set(meta["sensitivity"]["pairwise_aggregation_kendall_tau_b"]) == {
        "product__vs__minimum",
        "product__vs__weighted_additive",
        "minimum__vs__weighted_additive",
    }
    assert meta["sensitivity"]["primary_aggregation"] == "product"
    assert set(meta["sensitivity"]["rank_by_aggregation"]) == {
        "product",
        "minimum",
        "weighted_additive",
    }
    assert [d["id"] for d in meta["disclosures"]] == [
        "independence_assumption_narrows_every_interval"
    ] or "tractability_level_3_is_family_precedent_only" in {
        d["id"] for d in meta["disclosures"]
    }
    assert meta["information_gain"]["top_next_analyses"]
    assert "Not a claim about biology" in meta["interpretation"]["what_this_is"]
    assert meta["columns"] == list(CSV_COLUMNS)


def test_sidecar_reports_gates_that_fired(spec, tmp_path) -> None:
    inputs = make_inputs(
        [
            normal_uniform_target("TGT:CLEAN", 3),
            make_target(
                "TGT:LIABLE",
                levels=dict.fromkeys(ALL_FACETS, 3) | {"safety_liability_burden": 4},
            ),
        ]
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    artefacts = write_report(
        result, inputs, root=tmp_path, reports_dir=tmp_path / "reports", generated_on="2026-09-17"
    )
    meta = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))
    assert "safety_liability_caps_d5" in meta["gates_triggered"]["TGT:LIABLE"]


def test_git_commit_is_null_when_unavailable(spec, cohort, tmp_path) -> None:
    """A missing ``.git`` must produce ``null``, not a crash and not a fabricated hash."""
    result = score_cohort(cohort, spec, n_draws=DRAWS)
    artefacts = write_report(
        result, cohort, root=tmp_path, reports_dir=tmp_path / "reports", generated_on="2026-09-17"
    )
    meta = json.loads(artefacts.meta_path.read_text(encoding="utf-8"))
    assert meta["run"]["git_commit"] is None
