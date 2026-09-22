"""X02 ingestion readiness: prove the adapter refuses what it must refuse.

"Ready to ingest X02" is worthless as an assertion and cheap as a test. Each test below
breaks one property of a well-formed delivery and requires the adapter to refuse it, so
the refusals are demonstrable rather than described. The failure modes chosen are the
ones that would silently invert or inflate a conclusion downstream:

* a checksum mismatch — the artefact is not the one the manifest describes;
* a beta with no effect allele — a direction relative to nothing;
* a colocalisation reporting H4 without H3 — unfalsifiable by construction;
* an empty negative-results table — "tested and null" collapses into "never tested";
* a stated direction that contradicts its own effect size;
* an sQTL with no named junction.

The last two tests cover the other half of readiness: that an *unverified* external
analysis stays inert, enforced by rule V-EXT rather than by convention.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "x02_delivery_valid"
ADAPTER = REPO_ROOT / "pipelines" / "integration" / "ingest_x02.py"

sys.path.insert(0, str(REPO_ROOT / "pipelines" / "integration"))
from ingest_x02 import check_delivery  # noqa: E402


@pytest.fixture()
def delivery(tmp_path: Path) -> Path:
    """A private, writable copy of the synthetic delivery."""
    target = tmp_path / "delivery"
    shutil.copytree(FIXTURE, target)
    return target


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _refix_checksums(delivery: Path) -> None:
    """Recompute the manifest's output checksums after editing a table."""
    import hashlib

    manifest_path = delivery / "analysis_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest["outputs"]:
        path = delivery / entry["path"]
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        entry["bytes"] = path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def _errors(delivery: Path) -> list[str]:
    return check_delivery(delivery).errors


# --------------------------------------------------------------- the happy path ---
def test_the_synthetic_delivery_is_accepted(delivery: Path) -> None:
    report = check_delivery(delivery)
    assert report.accepted, report.errors
    assert report.counts["negative_results.tsv"] == 2


def test_the_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--self-test"],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ACCEPTED" in result.stdout


# ------------------------------------------------------------------- refusals ----
def test_a_checksum_mismatch_is_refused(delivery: Path) -> None:
    """The artefact must be the one the manifest describes, or nothing is ingested."""
    table = delivery / "credible_sets.tsv"
    table.write_text(table.read_text() + "\n")  # content changes, manifest does not
    errors = _errors(delivery)
    assert any("CHECKSUM MISMATCH" in message for message in errors), errors


def test_a_beta_without_an_effect_allele_is_refused(delivery: Path) -> None:
    """A direction with no allele inverts silently under a strand flip."""
    path = delivery / "credible_set_variants.tsv"
    rows = _rows(path)
    fieldnames = list(rows[0])
    rows[0]["effect_allele"] = ""
    _write(path, rows, fieldnames)
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("effect_allele" in message for message in errors), errors


def test_a_colocalisation_without_h3_is_refused(delivery: Path) -> None:
    """H3 versus H4 is the distinction between two signals and one shared variant."""
    path = delivery / "qtl_colocalisation.tsv"
    rows = _rows(path)
    fieldnames = list(rows[0])
    rows[0]["pp_h3"] = ""
    _write(path, rows, fieldnames)
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("pp_h3" in message or "posterior vector" in message for message in errors), errors


def test_an_empty_negative_results_table_is_refused(delivery: Path) -> None:
    """No negatives means "not tested" and "tested and null" are indistinguishable."""
    path = delivery / "negative_results.tsv"
    rows = _rows(path)
    _write(path, [], list(rows[0]))
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("negative" in message.lower() for message in errors), errors


def test_a_direction_contradicting_its_own_beta_is_refused(delivery: Path) -> None:
    path = delivery / "qtl_colocalisation.tsv"
    rows = _rows(path)
    fieldnames = list(rows[0])
    rows[0]["direction_on_gene"] = "decreases"  # qtl_beta is positive
    _write(path, rows, fieldnames)
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("contradicts its own effect size" in message for message in errors), errors


def test_an_sqtl_without_a_named_junction_is_refused(delivery: Path) -> None:
    path = delivery / "qtl_colocalisation.tsv"
    rows = _rows(path)
    fieldnames = list(rows[0])
    rows[0]["qtl_type"] = "sqtl"
    rows[0]["intron_id"] = ""
    _write(path, rows, fieldnames)
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("intron_id" in message for message in errors), errors


def test_a_missing_manifest_is_refused(delivery: Path) -> None:
    (delivery / "analysis_manifest.json").unlink()
    errors = _errors(delivery)
    assert any("analysis_manifest.json is missing" in message for message in errors), errors


def test_an_analysis_claiming_no_negatives_is_refused(delivery: Path) -> None:
    """The manifest must assert that negatives are included, not merely ship a table."""
    manifest_path = delivery / "analysis_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["negative_results_included"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    errors = _errors(delivery)
    assert any("negative_results_included" in message for message in errors), errors


def test_a_credible_set_reference_that_does_not_resolve_is_refused(delivery: Path) -> None:
    path = delivery / "credible_set_variants.tsv"
    rows = _rows(path)
    fieldnames = list(rows[0])
    rows[0]["credible_set_id"] = "CS_DOES_NOT_EXIST"
    _write(path, rows, fieldnames)
    _refix_checksums(delivery)
    errors = _errors(delivery)
    assert any("does not declare" in message for message in errors), errors


# ------------------------------------------- the unverified analysis stays inert ---
def test_x01_is_recorded_as_unverified_and_licenses_nothing() -> None:
    """X01's figures exist in the repository but may not support anything."""
    import yaml

    record = yaml.safe_load(
        (REPO_ROOT / "analyses" / "external" / "X01_cell_type_enrichment.yaml").read_text()
    )
    # R20: the delivery state may advance once artefacts exist; the LICENSING invariant may not.
    assert record["verification_status"] in {"unverified_external_report",
                                             "artefacts_received_pending_check"}
    assert record["provenance_class"] == "external_analysis_unverified"
    assert record["outstanding_artefacts"], "an unverified analysis must say what is missing"
    assert record["interpretation_guards"], "both over-readings must be written down"
    for result in record["reported_results"]:
        assert result["claim_refs"] == [], (
            f"{result['result_id']} licenses a claim while unverified"
        )
        # Every reported figure is a verbatim string, never a typed number.
        assert result["value_as_reported"] is None or isinstance(
            result["value_as_reported"], str
        )


def test_v_ext_refuses_a_claim_that_cites_an_unverified_analysis(make_root) -> None:
    """Rule V-EXT, not convention, keeps an unverified figure out of the evidence chain.

    The fixture tree contains one claim whose evidence names ``ANALYSIS:X01`` and one
    unverified external-analysis record. V-EXT must fire. Without this rule a number
    transcribed from a task description would acquire the authority of a measured
    result, and the repository's provenance guarantees would fail precisely where an
    external collaborator is involved.
    """
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from blueprint import validate

    root = make_root("v_ext_claim_cites_unverified_analysis")
    report = validate.run(root, strict=True, only=("V-EXT",))
    fired = [v for v in report.violations if v.rule == "V-EXT"]
    assert fired, "V-EXT did not fire on a claim citing an unverified external analysis"
    assert any("cannot fail a check" in v.message for v in fired), [v.message for v in fired]
    assert all(v.severity == "error" for v in fired)


def test_v_ext_is_silent_when_nothing_cites_the_analysis() -> None:
    """The real repository records X01 and cites it nowhere, so V-EXT must not fire."""
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from blueprint import validate

    report = validate.run(REPO_ROOT, strict=True, only=("V-EXT",))
    assert [v for v in report.violations if v.rule == "V-EXT"] == []
