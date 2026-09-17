"""The CLI must run end-to-end, and must refuse to invent data.

Each test builds a throwaway repository under ``tmp_path`` (the three spec files plus
whatever curated records the case needs) so nothing here reads or writes the real
repository's ``reports/``.
"""

from __future__ import annotations

import csv
import io
import json
import shutil
from pathlib import Path

import pytest
import yaml

from blueprint.ranking.cli import build_parser, main
from blueprint.ranking.inputs import RepositoryLoaderUnavailable, from_repository, from_repository_direct
from blueprint.ranking.rubric import load_model_spec

RELPATHS = (
    "models/ranking/facet_rubric_v0_1.yaml",
    "models/ranking/ranking_spec_v0_1.yaml",
    "models/uncertainty/uncertainty_spec_v0_1.yaml",
)


@pytest.fixture(scope="module")
def real_spec():
    return load_model_spec()


@pytest.fixture
def repo(tmp_path, real_spec) -> Path:
    """A throwaway repository containing only the model specs."""
    root = tmp_path / "repo"
    source_root = Path(real_spec.paths["ranking"]).parents[2]
    for relpath in RELPATHS:
        destination = root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source_root / relpath, destination)
    (root / "targets").mkdir(parents=True, exist_ok=True)
    return root


def _write_registry(root: Path, symbols) -> None:
    (root / "targets").mkdir(parents=True, exist_ok=True)
    (root / "targets" / "seed_registry.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "0.1.0",
                "targets": [
                    {"target_id": f"TGT:{symbol}", "symbol": symbol, "lead_atlas": "brakes"}
                    for symbol in symbols
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_assessment(root: Path, symbol: str, facets) -> None:
    path = root / "atlases" / "brakes" / "assessments" / f"{symbol}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "target_id": f"TGT:{symbol}",
                "assessed_by": "agent:brakes",
                "assessed_on": "2026-09-17",
                "rubric": "facet_rubric_v0_1",
                "facets": facets,
            }
        ),
        encoding="utf-8",
    )


def _write_claim(root: Path, claim_id: str, source_ids) -> None:
    path = root / "evidence" / "claims" / "brakes" / "SYNTHETIC.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.is_file():
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    existing.append(
        {
            "claim_id": claim_id,
            "status": "active",
            "evidence": [{"source_id": source_id} for source_id in source_ids],
        }
    )
    path.write_text(yaml.safe_dump(existing), encoding="utf-8")


def _write_audit(root: Path, symbol: str, *, verdict: str, adjustments=()) -> None:
    path = root / "evidence" / "audits" / "red_team" / f"{symbol}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            [
                {
                    "audit_id": f"AUD:red_team:{symbol}:001",
                    "scope": {"kind": "target", "id": f"TGT:{symbol}"},
                    "audited_by": "agent:red_team",
                    "audited_on": "2026-09-17",
                    "checks": [{"check": "overclaiming", "result": "pass"}],
                    "findings": [],
                    "adjustments": list(adjustments),
                    "verdict": verdict,
                }
            ]
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Pre-data behaviour — the state the repository is actually in
# ---------------------------------------------------------------------------


def test_exits_zero_and_writes_nothing_when_there_are_no_assessments(repo, capsys) -> None:
    """The requirement: exit with a clear message rather than inventing data."""
    _write_registry(repo, ["GABRA5", "HCN1"])
    code = main(["--root", str(repo)])
    captured = capsys.readouterr()

    assert code == 0
    assert "NOTHING TO RANK YET" in captured.err
    assert "no data was invented" in captured.err
    assert "atlases/{domain}/assessments" in captured.err
    assert not (repo / "reports" / "target_ranking_v0_1.csv").exists()


def test_require_data_turns_the_pre_data_state_into_a_failure(repo) -> None:
    """The strict form, for CI: exit 3 when there is nothing to rank."""
    _write_registry(repo, ["GABRA5"])
    assert main(["--root", str(repo), "--require-data"]) == 3


def test_an_empty_repository_does_not_crash(repo, capsys) -> None:
    code = main(["--root", str(repo)])
    assert code == 0
    assert "NOTHING TO RANK YET" in capsys.readouterr().err


def test_missing_specs_exit_two_with_a_clear_message(tmp_path, capsys) -> None:
    code = main(["--root", str(tmp_path)])
    assert code == 2
    assert "specification file missing" in capsys.readouterr().err


def test_the_shared_loaders_are_used_when_available(repo) -> None:
    """``agent:ontology`` landed ``blueprint.loaders.load_repository``, so the
    production path is live and must be the one taken, recorded by name."""
    _write_registry(repo, ["GABRA5"])
    inputs = from_repository(repo)
    assert inputs.reader == "blueprint.loaders.load_repository"
    assert {t.symbol for t in inputs.targets} == {"GABRA5"}


def test_loader_reader_reads_assessments_audits_and_claims(repo) -> None:
    """The projection from ``loaders.Repository`` onto the ranking inputs must carry
    the four things the model needs: levels, counter levels, claim -> source links and
    audit adjustments."""
    _write_registry(repo, ["GABRA5"])
    _write_claim(repo, "CLM:brakes:GABRA5:001", ["SRC:PMID:1", "SRC:PMID:2"])
    _write_assessment(
        repo,
        "GABRA5",
        [
            {
                "facet": "mechanistic_causal_perturbation",
                "assessment_status": "assessed",
                "level": 3,
                "counter_level": 2,
                "claim_refs": ["CLM:brakes:GABRA5:001"],
            }
        ],
    )
    _write_audit(
        repo,
        "GABRA5",
        verdict="retain_with_downgrade",
        adjustments=[
            {
                "kind": "facet",
                "target_id": "TGT:GABRA5",
                "facet": "mechanistic_causal_perturbation",
                "from_level": 3,
                "to_level": 1,
                "reason": "synthetic",
            }
        ],
    )
    inputs = from_repository(repo)
    target = inputs.targets[0]
    assessment = target.facet("mechanistic_causal_perturbation")
    assert (assessment.level, assessment.counter_level) == (3, 2)
    assert inputs.source_ids_for(["CLM:brakes:GABRA5:001"]) == ("SRC:PMID:1", "SRC:PMID:2")
    assert target.audit.verdict == "retain_with_downgrade"
    assert target.audit.n_downgrades == 1


def test_from_repository_never_falls_back_silently(repo, monkeypatch) -> None:
    """If neither loader entry point exists, :func:`from_repository` must raise with
    an actionable message rather than quietly using the YAML fallback: a report has
    to say which reader produced it."""
    from blueprint import loaders

    monkeypatch.delattr(loaders, "load_repository", raising=False)
    monkeypatch.delattr(loaders, "load_ranking_inputs", raising=False)
    with pytest.raises(RepositoryLoaderUnavailable) as error:
        from_repository(repo)
    message = str(error.value)
    assert "neither load_ranking_inputs" in message
    assert "--reader direct" in message
    assert "No data is invented" in message


def test_auto_reader_falls_back_and_says_so(repo, monkeypatch, capsys) -> None:
    from blueprint import loaders

    monkeypatch.delattr(loaders, "load_repository", raising=False)
    monkeypatch.delattr(loaders, "load_ranking_inputs", raising=False)
    _write_registry(repo, ["GABRA5"])
    code = main(["--root", str(repo)])
    captured = capsys.readouterr()
    assert code == 0
    assert "falling back to the contract-literal YAML reader" in captured.err


def test_explicit_loaders_reader_exits_four_when_unavailable(repo, monkeypatch, capsys) -> None:
    from blueprint import loaders

    monkeypatch.delattr(loaders, "load_repository", raising=False)
    monkeypatch.delattr(loaders, "load_ranking_inputs", raising=False)
    _write_registry(repo, ["GABRA5"])
    code = main(["--root", str(repo), "--reader", "loaders"])
    assert code == 4
    assert "--reader direct" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# With data
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reader", ["direct", "loaders"])
def test_writes_a_report_when_assessments_exist(repo, capsys, reader) -> None:
    """Both readers must produce the same report from the same records."""
    _write_registry(repo, ["GABRA5", "HCN1", "ADORA1"])
    _write_claim(repo, "CLM:brakes:GABRA5:001", ["SRC:PMID:1", "SRC:PMID:1", "SRC:PMID:2"])
    _write_assessment(
        repo,
        "GABRA5",
        [
            {
                "facet": "mechanistic_causal_perturbation",
                "assessment_status": "assessed",
                "level": 3,
                "counter_level": 1,
                "claim_refs": ["CLM:brakes:GABRA5:001"],
                "rationale": "synthetic",
            },
            {
                "facet": "adult_onset_perturbation",
                "assessment_status": "assessed",
                "level": 2,
                "claim_refs": ["CLM:brakes:GABRA5:001"],
            },
            {"facet": "transfer_breadth", "assessment_status": "not_assessed", "level": None},
        ],
    )
    _write_assessment(
        repo,
        "HCN1",
        [{"facet": "mechanistic_causal_perturbation", "assessment_status": "assessed", "level": 1}],
    )
    _write_audit(repo, "GABRA5", verdict="retain_with_downgrade")

    code = main(
        ["--root", str(repo), "--reader", reader, "--draws", "600", "--generated-on", "2026-09-17"]
    )
    captured = capsys.readouterr()
    assert code == 0, captured.err

    csv_path = repo / "reports" / "target_ranking_v0_1.csv"
    meta_path = repo / "reports" / "target_ranking_v0_1.meta.json"
    assert csv_path.is_file() and meta_path.is_file()

    rows = list(csv.DictReader(io.StringIO(csv_path.read_text(encoding="utf-8"))))
    assert {row["target_id"] for row in rows} == {"TGT:GABRA5", "TGT:HCN1"}
    gabra5 = next(row for row in rows if row["target_id"] == "TGT:GABRA5")

    assert gabra5["status"] == "PRELIMINARY"
    assert gabra5["calibration_status"] == "uncalibrated_subjective"
    assert gabra5["red_team_verdict"] == "retain_with_downgrade"
    assert gabra5["independent_source_count"] == "2"  # SRC:PMID:1 cited twice counts once
    assert gabra5["claim_count"] == "1"
    assert gabra5["d1_level"] == "3"
    assert gabra5["generated_on"] == "2026-09-17"

    unaudited = next(row for row in rows if row["target_id"] == "TGT:HCN1")
    assert unaudited["red_team_verdict"] == "not_audited"
    assert unaudited["tier"] == "tier_3_insufficient_coverage"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["run"]["reader"] == (
        "direct_yaml_fallback" if reader == "direct" else "blueprint.loaders.load_repository"
    )
    assert meta["run"]["n_targets_in_cohort"] == 3
    assert meta["run"]["n_targets_ranked"] == 2
    assert "reminder: this table prioritises further COMPUTATIONAL analysis" in captured.err


def test_audit_downgrades_from_disk_reach_the_report(repo) -> None:
    _write_registry(repo, ["GABRA5"])
    _write_assessment(
        repo,
        "GABRA5",
        [{"facet": "above_baseline_enhancement", "assessment_status": "assessed", "level": 3}],
    )
    _write_audit(
        repo,
        "GABRA5",
        verdict="retain_with_downgrade",
        adjustments=[
            {
                "kind": "facet",
                "target_id": "TGT:GABRA5",
                "facet": "above_baseline_enhancement",
                "from_level": 3,
                "to_level": 1,
                "reason": "rescue mistaken for enhancement",
            }
        ],
    )
    assert main(["--root", str(repo), "--draws", "600", "--generated-on", "2026-09-17"]) == 0
    rows = list(
        csv.DictReader(
            io.StringIO((repo / "reports" / "target_ranking_v0_1.csv").read_text(encoding="utf-8"))
        )
    )
    assert rows[0]["n_downgrades"] == "1"
    assert rows[0]["d3_level"] == "1"


def test_a_deprioritise_verdict_reaches_the_tier_column(repo) -> None:
    _write_registry(repo, ["GABRA5"])
    _write_assessment(
        repo,
        "GABRA5",
        [{"facet": "mechanistic_causal_perturbation", "assessment_status": "assessed", "level": 4}],
    )
    _write_audit(repo, "GABRA5", verdict="deprioritise")
    assert main(["--root", str(repo), "--draws", "600", "--generated-on", "2026-09-17"]) == 0
    rows = list(
        csv.DictReader(
            io.StringIO((repo / "reports" / "target_ranking_v0_1.csv").read_text(encoding="utf-8"))
        )
    )
    assert rows[0]["tier"] == "tier_4_deprioritised_by_audit"


def test_cli_runs_are_byte_identical(repo) -> None:
    _write_registry(repo, ["GABRA5", "HCN1"])
    for symbol, level in (("GABRA5", 3), ("HCN1", 2)):
        _write_assessment(
            repo,
            symbol,
            [{"facet": "mechanistic_causal_perturbation", "assessment_status": "assessed", "level": level}],
        )
    args = ["--root", str(repo), "--draws", "600", "--generated-on", "2026-09-17"]
    assert main(args) == 0
    first = (repo / "reports" / "target_ranking_v0_1.csv").read_bytes()
    assert main(args) == 0
    second = (repo / "reports" / "target_ranking_v0_1.csv").read_bytes()
    assert first == second


def test_an_illegal_level_on_disk_is_reported_not_silently_accepted(repo, capsys) -> None:
    """Contract §5.2 forbids ``level: 0`` on a ``not_assessed`` facet. The reader must
    reject that record and say so rather than treat it as a documented zero."""
    _write_registry(repo, ["GABRA5"])
    _write_assessment(
        repo,
        "GABRA5",
        [
            {"facet": "mechanistic_causal_perturbation", "assessment_status": "not_assessed", "level": 0},
            {"facet": "tractability", "assessment_status": "assessed", "level": 2},
        ],
    )
    code = main(["--root", str(repo), "--draws", "600", "--generated-on", "2026-09-17"])
    captured = capsys.readouterr()
    assert code == 0
    assert "rejected facet" in captured.err
    rows = list(
        csv.DictReader(
            io.StringIO((repo / "reports" / "target_ranking_v0_1.csv").read_text(encoding="utf-8"))
        )
    )
    assert rows[0]["facets_assessed"] == "1"


@pytest.mark.parametrize("reader", ["direct", "loaders"])
def test_assessments_for_unregistered_symbols_are_reported_and_not_ranked(
    repo, capsys, reader
) -> None:
    _write_registry(repo, ["GABRA5"])
    _write_assessment(
        repo, "GABRA5", [{"facet": "tractability", "assessment_status": "assessed", "level": 2}]
    )
    _write_assessment(
        repo, "NOT_A_SEED", [{"facet": "tractability", "assessment_status": "assessed", "level": 4}]
    )
    code = main(
        ["--root", str(repo), "--reader", reader, "--draws", "600", "--generated-on", "2026-09-17"]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "absent from the seed registry" in captured.err
    rows = list(
        csv.DictReader(
            io.StringIO((repo / "reports" / "target_ranking_v0_1.csv").read_text(encoding="utf-8"))
        )
    )
    assert {row["target_id"] for row in rows} == {"TGT:GABRA5"}


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


def test_direct_reader_tags_its_provenance(repo) -> None:
    _write_registry(repo, ["GABRA5"])
    inputs = from_repository_direct(repo)
    assert inputs.reader == "direct_yaml_fallback"
    assert inputs.root == str(repo)


def test_direct_reader_returns_empty_collections_for_a_bare_repository(repo) -> None:
    inputs = from_repository_direct(repo)
    assert inputs.targets == ()
    assert inputs.claims == {}
    assert inputs.targets_with_assessments == ()


def test_parser_exposes_the_documented_options() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.reader == "auto"
    assert args.seed is None
    assert args.draws is None
    assert args.require_data is False
    assert "no protocol, dose, route or regimen" in (parser.epilog or "")
