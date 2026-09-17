"""The ``graph/validate_graph.py`` CLI: exit codes, output shapes and the lock.

The CLI is what ``make validate`` and the git hook run, so its exit code is the gate.
These tests drive it as a subprocess — the way it is actually invoked — rather than
calling ``main()`` in-process, because an import-time or argument-parsing regression
would not show up in-process.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

from tests.conftest import REPO_ROOT

CLI = REPO_ROOT / "graph" / "validate_graph.py"
RootFactory = Callable[[str | None], Path]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI as a subprocess, the way make and the git hook do."""
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


# ------------------------------------------------------------- exit codes --------

def test_empty_tree_exits_zero(make_root: RootFactory) -> None:
    """Zero records is a correct state for Sprint 1, and the summary says so."""
    root = make_root(None)
    result = run_cli("--root", str(root), "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 sources, 0 claims" in result.stdout
    assert "PASS" in result.stdout
    assert "an empty repository is a correct state" in result.stdout.lower()


def test_minimal_valid_tree_exits_zero_under_strict(make_root: RootFactory) -> None:
    """The control tree must pass the gate that G2/G3 use."""
    result = run_cli("--root", str(make_root("valid_minimal")), "--strict")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 sources, 1 claims" in result.stdout


@pytest.mark.parametrize(
    ("case", "rule"),
    [
        ("v3_illegal_triple", "V3"),
        ("v5_claim_without_evidence", "V5"),
        ("v6_unverified_source", "V6"),
        ("v9_handwritten_probability", "V9"),
        ("v12_audit_upgrade", "V12"),
        ("v13_deleted_claim_in_lock", "V13"),
        ("v16_efficacy_from_binding", "V16"),
        ("v16b_null_without_null_evidence", "V16b"),
        ("v20_prohibited_work", "V20"),
        ("v21_human_facet_without_human_evidence", "V21"),
    ],
)
def test_violating_tree_exits_one_and_names_the_rule(
    make_root: RootFactory, case: str, rule: str
) -> None:
    """Exit 1 and name the rule, so a curator knows what to read."""
    result = run_cli("--root", str(make_root(case)), "--strict")
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"{rule}:" in result.stdout, f"{rule} not named in output"
    assert "FAIL" in result.stdout


def test_warnings_alone_exit_zero_without_strict(make_root: RootFactory) -> None:
    """Without --strict a warning is reported but does not fail the run."""
    root = make_root("valid_minimal")
    for path in (root / "data" / "interim" / "source_verification").glob("*.jsonl"):
        path.unlink()
    lenient = run_cli("--root", str(root))
    assert lenient.returncode == 0, lenient.stdout
    assert "warning" in lenient.stdout
    strict = run_cli("--root", str(root), "--strict")
    assert strict.returncode == 1
    assert "--strict: warnings are treated as errors." in strict.stdout


# ------------------------------------------------------------ output shapes ------

def test_quiet_prints_nothing(make_root: RootFactory) -> None:
    """--quiet is for scripts that only want the exit code."""
    result = run_cli("--root", str(make_root("v3_illegal_triple")), "--quiet")
    assert result.returncode == 1
    assert result.stdout == ""


def test_json_is_machine_readable(make_root: RootFactory) -> None:
    """--json must be parseable and carry the whole violation list."""
    result = run_cli("--root", str(make_root("v3_illegal_triple")), "--json", "--strict")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["strict"] is True
    assert payload["counts"]["claims"] == 1
    assert "V3" in payload["by_rule"]
    group = payload["by_rule"]["V3"]
    assert group["count"] == len(group["violations"])
    assert group["description"]
    violation = group["violations"][0]
    assert {"rule", "severity", "path", "message"} <= set(violation)
    assert violation["record_id"] == "CLM:ontology:PLACEHOLDER:001"


def test_json_on_an_empty_tree_is_still_valid_json(make_root: RootFactory) -> None:
    """A consumer must not have to special-case the empty repository."""
    result = run_cli("--root", str(make_root(None)), "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["by_rule"] == {}
    assert payload["totals"]["violations"] == 0


def test_human_output_groups_by_rule_and_caps_examples(make_root: RootFactory) -> None:
    """An agent needs the SHAPE of the problem, not a thousand lines."""
    root = make_root("valid_minimal")
    # Twelve claims, each with the same illegal triple, to exceed the example cap.
    source = (root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml").read_text(
        encoding="utf-8"
    )
    broken = source.replace("predicate: EXPRESSED_IN", "predicate: TARGETS").replace(
        "claim_type: expression", "claim_type: mechanistic"
    )
    for index in range(1, 13):
        body = broken.replace(
            "claim_id: CLM:ontology:PLACEHOLDER:001",
            f"claim_id: CLM:ontology:PLACEHOLDER:{index:03d}",
        )
        (root / "evidence" / "claims" / "ontology" / f"CASE{index}.yaml").write_text(
            body, encoding="utf-8"
        )
    (root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml").unlink()

    result = run_cli("--root", str(root), "--strict")
    assert result.returncode == 1
    assert "V3: 12 violation(s)" in result.stdout
    assert "and 2 more under V3" in result.stdout
    assert "use --json for the full list" in result.stdout

    capped = run_cli("--root", str(root), "--strict", "--max-examples", "2")
    assert "and 10 more under V3" in capped.stdout


def test_summary_reports_verification_and_shared_sources(make_root: RootFactory) -> None:
    """The summary must be honest about what was and was not verified."""
    result = run_cli("--root", str(make_root("valid_minimal")), "--strict")
    assert "sources verified: verified=1" in result.stdout
    assert "sources registered by more than one agent" in result.stdout


# -------------------------------------------------------------- rule selection ---

def test_rule_selection_runs_only_that_rule(make_root: RootFactory) -> None:
    """--rule is how a curator iterates on one class of problem."""
    result = run_cli("--root", str(make_root("v3_illegal_triple")), "--rule", "V3", "--json")
    payload = json.loads(result.stdout)
    assert payload["rules_run"] == ["V3"]
    assert set(payload["by_rule"]) == {"V3"}


def test_unknown_rule_id_is_rejected(make_root: RootFactory) -> None:
    """A typo'd rule id must not silently validate nothing."""
    result = run_cli("--root", str(make_root(None)), "--rule", "V999")
    assert result.returncode == 2
    assert "unknown rule id" in result.stderr


def test_list_rules_reports_the_implemented_set() -> None:
    """--list-rules is what the handoff table is generated from."""
    result = run_cli("--list-rules")
    assert result.returncode == 0
    assert "rule(s) implemented" in result.stdout
    for rule in ("V1", "V5", "V9", "V16", "V16b", "V21", "ONT1", "ONT2"):
        assert f"  {rule} " in result.stdout or f"  {rule:6s}" in result.stdout


def test_list_rules_json_is_parseable() -> None:
    """A consumer should be able to read the rule catalogue without scraping text."""
    result = run_cli("--list-rules", "--json")
    catalogue = json.loads(result.stdout)
    assert len(catalogue) >= 24
    assert catalogue["V16"].startswith("No efficacy assertion")


# ----------------------------------------------------------------- the lock ------

def test_update_lock_creates_the_lock_with_its_header(make_root: RootFactory) -> None:
    """The lock explains itself, because it is append-only and hand-editing breaks it."""
    root = make_root("valid_minimal")
    lock = root / "evidence" / "claims" / "claim_registry.lock"
    assert not lock.exists()

    result = run_cli("--root", str(root), "--update-lock", "--strict")
    assert result.returncode == 0, result.stdout
    assert lock.is_file()
    body = lock.read_text(encoding="utf-8")
    assert "APPEND-ONLY" in body
    assert "CLM:ontology:PLACEHOLDER:001" in body
    assert "appended 1 claim id" in result.stdout


def test_update_lock_only_appends(make_root: RootFactory) -> None:
    """Provenance is append-only (contract P6): the lock is never rewritten."""
    root = make_root("valid_minimal")
    lock = root / "evidence" / "claims" / "claim_registry.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(
        "# existing header\nCLM:ontology:HISTORIC:001\nCLM:ontology:PLACEHOLDER:001\n",
        encoding="utf-8",
    )

    result = run_cli("--root", str(root), "--update-lock")
    body = lock.read_text(encoding="utf-8")
    assert body.startswith("# existing header\n")
    assert "CLM:ontology:HISTORIC:001" in body, "an existing id must never be removed"
    assert body.count("CLM:ontology:PLACEHOLDER:001") == 1, "no duplicate append"
    assert "lock up to date" in result.stdout
    # The historic id no longer resolves, which is exactly what V13 exists to catch.
    assert result.returncode == 1
    assert "V13" in result.stdout


def test_update_lock_is_idempotent(make_root: RootFactory) -> None:
    """Running it twice must not change the file the second time."""
    root = make_root("valid_minimal")
    lock = root / "evidence" / "claims" / "claim_registry.lock"
    run_cli("--root", str(root), "--update-lock", "--quiet")
    first = lock.read_text(encoding="utf-8")
    run_cli("--root", str(root), "--update-lock", "--quiet")
    assert lock.read_text(encoding="utf-8") == first


def test_lock_survives_a_validation_failure(make_root: RootFactory) -> None:
    """--update-lock must record ids even when the run fails; provenance comes first."""
    root = make_root("v3_illegal_triple")
    result = run_cli("--root", str(root), "--update-lock", "--strict")
    assert result.returncode == 1
    lock = root / "evidence" / "claims" / "claim_registry.lock"
    assert "CLM:ontology:PLACEHOLDER:001" in lock.read_text(encoding="utf-8")


# ---------------------------------------------------------------- the real tree --

def test_cli_runs_on_the_real_repository() -> None:
    """The CLI must not crash on the live tree, whatever the records currently say.

    The exit code is deliberately NOT asserted: domain agents are writing records
    concurrently and a violation is the gate working, not a test failure. What is
    asserted is that the validator produces a report rather than a traceback.
    """
    result = run_cli("--json")
    assert result.returncode in (0, 1), result.stderr
    payload = json.loads(result.stdout)
    assert payload["counts"]["state_variables"] >= 100
    assert len(payload["rules_run"]) >= 24
    assert "Traceback" not in result.stderr


def test_no_rule_raised_on_the_real_repository() -> None:
    """A rule that raises reports itself; that must never happen on the live tree."""
    result = run_cli("--json")
    payload = json.loads(result.stdout)
    engine_bugs = [
        violation
        for group in payload["by_rule"].values()
        for violation in group["violations"]
        if "validator bug" in violation["message"]
    ]
    assert not engine_bugs, engine_bugs


def test_deterministic_output(make_root: RootFactory) -> None:
    """Two runs over one tree must produce byte-identical JSON (contract P7)."""
    root = make_root("v3_illegal_triple")
    first = run_cli("--root", str(root), "--json", "--strict").stdout
    second = run_cli("--root", str(root), "--json", "--strict").stdout
    assert first == second
