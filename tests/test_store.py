"""The store must round-trip the records without losing what matters.

The failure this file guards against is quiet: a table that coerces ``not_assessed`` to
``0``, drops a null-result flag, or inflates an evidence count by double-counting a
source registered twice. None of those would raise; all of them would make every
downstream query wrong in the same direction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from blueprint import loaders
from blueprint.graph import compile_graph
from blueprint.store.build import DUCKDB_NAME, MANIFEST_NAME, build_store, connect
from blueprint.store.tables import TABLES
from blueprint.store.views import VIEWS

RootFactory = Callable[[str | None], Path]


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[Path, object]:
    """A store built once from the real repository into a temporary tree.

    Built against a copy so the test never disturbs ``data/processed/`` in the working
    tree, which another agent may be reading.
    """
    import shutil

    from tests.conftest import REPO_ROOT, build_root

    root = tmp_path_factory.mktemp("store") / "root"
    build_root(root, None)
    # Bring the real records in; the shared dirs are already symlinked by build_root.
    for name in ("evidence", "targets", "atlases", "models"):
        source = REPO_ROOT / name
        if source.is_dir():
            shutil.copytree(source, root / name, symlinks=False)
    interim = root / "data" / "interim"
    interim.mkdir(parents=True, exist_ok=True)
    for name in ("gene_identifiers.jsonl",):
        source = REPO_ROOT / "data" / "interim" / name
        if source.is_file():
            shutil.copy2(source, interim / name)
    verification = REPO_ROOT / "data" / "interim" / "source_verification"
    if verification.is_dir():
        shutil.copytree(verification, interim / "source_verification")
    from tests.conftest import _clear_caches

    _clear_caches()
    result = build_store(root)
    return root, result


# ----------------------------------------------------------------- artefacts ---

def test_every_table_is_written(built) -> None:
    """Each declared table produces a Parquet file, including the provenance table."""
    root, result = built
    parquet = result.processed_dir / "parquet"
    for name in TABLES:
        assert (parquet / f"{name}.parquet").is_file(), f"{name}.parquet missing"
    assert (parquet / "provenance.parquet").is_file()
    assert result.duckdb_path.name == DUCKDB_NAME
    assert result.manifest_path.name == MANIFEST_NAME


def test_manifest_records_a_checksum_per_artefact(built) -> None:
    """A rebuild can be compared against the build it replaced."""
    _root, result = built
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["artefacts"], "no artefacts recorded"
    for name, entry in manifest["artefacts"].items():
        assert len(entry["sha256"]) == 64, f"{name} has no usable checksum"
        assert entry["bytes"] > 0
        assert "rows" in entry
    assert manifest["row_counts"]
    assert manifest["input_digest"]


def test_provenance_table_records_where_the_data_came_from(built) -> None:
    """A table of numbers with no record of its origin is what this project refuses."""
    _root, result = built
    provenance = result.provenance
    assert provenance["blueprint_version"]
    assert provenance["contract_version"]
    assert provenance["generated_on"]
    assert provenance["input_file_count"] > 0
    assert provenance["input_hashes"], "no input hashes recorded"
    # The ontology and the schemas are inputs too: a table built against a different
    # type system is a different table even when the records are unchanged.
    keys = " ".join(provenance["input_hashes"])
    assert "ontology/" in keys
    assert "schemas/" in keys
    assert "safety or efficacy claim" in provenance["notes"]


def test_build_is_deterministic(built) -> None:
    """Two builds over one tree produce byte-identical Parquet.

    Determinism is what makes the manifest checksums mean anything: without it every
    rebuild would look like a data change.
    """
    root, first = built
    parquet = first.processed_dir / "parquet"
    before = {p.name: p.read_bytes() for p in sorted(parquet.glob("*.parquet"))}

    second = build_store(root)
    after = {
        p.name: p.read_bytes() for p in sorted((second.processed_dir / "parquet").glob("*.parquet"))
    }
    # provenance.parquet embeds a timestamp by design, so it is excluded.
    for name in sorted(set(before) - {"provenance.parquet"}):
        assert before[name] == after[name], f"{name} differs between builds"


# -------------------------------------------------------------- round trips ----

def test_row_counts_match_the_records(built) -> None:
    """Every record reaches the store exactly once."""
    root, result = built
    repo = loaders.load_repository(root)
    graph = compile_graph(root)
    assert result.row_counts["sources"] == len(repo.sources)
    assert result.row_counts["claims"] == len(repo.claims)
    assert result.row_counts["targets"] == len(repo.targets)
    assert result.row_counts["state_variables"] == len(repo.state_variables)
    assert result.row_counts["nodes"] == len(graph.nodes)
    assert result.row_counts["edges"] == len(graph.edges)
    assert result.row_counts["evidence_items"] == sum(
        len(r.raw.get("evidence") or []) for r in repo.claims.values()
    )


def test_duckdb_round_trip(built) -> None:
    """Read the store back and check a value survived the trip unchanged."""
    root, _result = built
    connection = connect(root)
    try:
        repo = loaders.load_repository(root)
        claim_id = sorted(repo.claims)[0]
        expected = repo.claims[claim_id].raw
        row = connection.execute(
            "SELECT claim_type, predicate, subject, object, status, evidence_count "
            "FROM claims WHERE claim_id = ?",
            [claim_id],
        ).fetchone()
        assert row is not None, f"{claim_id} did not reach the store"
        assert row[0] == expected.get("claim_type")
        assert row[1] == expected.get("predicate")
        assert row[2] == expected.get("subject")
        assert row[3] == expected.get("object")
        assert row[4] == expected.get("status")
        assert row[5] == len(expected.get("evidence") or [])
    finally:
        connection.close()


def test_not_assessed_stays_null_never_zero(built) -> None:
    """Contract P8: `not_assessed` must not become `0` in SQL.

    The contract spends real effort keeping "nobody looked" apart from "searched and
    found nothing"; a coerced zero would erase that in every downstream query.
    """
    root, _result = built
    connection = connect(root)
    try:
        rows = connection.execute(
            "SELECT COUNT(*) FROM assessments "
            "WHERE assessment_status = 'not_assessed' AND level IS NOT NULL"
        ).fetchone()
        assert rows[0] == 0, "a not_assessed facet carries a non-null level in the store"
        nulls = connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE level IS NULL"
        ).fetchone()[0]
        zeros = connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE level = 0"
        ).fetchone()[0]
        # Both states should exist in a real repository, and they must be distinguishable.
        assert nulls + zeros > 0
        assert connection.execute(
            "SELECT COUNT(*) FROM assessments WHERE level = 0 AND search_basis IS NULL"
        ).fetchone()[0] == 0, "a level-0 facet reached the store with no search_basis"
    finally:
        connection.close()


def test_null_result_flag_survives_into_sql(built) -> None:
    """A query must be able to exclude nulls without knowing relation names."""
    root, _result = built
    graph = compile_graph(root)
    connection = connect(root)
    try:
        stored = connection.execute(
            "SELECT COUNT(*) FROM edges WHERE is_null_result"
        ).fetchone()[0]
        assert stored == sum(1 for e in graph.edges if e.is_null_result)
        # And no null edge is marked as support anywhere in SQL.
        assert connection.execute(
            "SELECT COUNT(*) FROM edges WHERE is_null_result AND counts_as_support"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_duplicate_registration_yields_one_source_row(built) -> None:
    """Deduplication belongs to the store, not to the registry (contract §1.3)."""
    root, _result = built
    repo = loaders.load_repository(root)
    connection = connect(root)
    try:
        rows = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        assert rows == len(repo.sources)
        duplicated = connection.execute(
            "SELECT COUNT(*) FROM sources WHERE registration_count > 1"
        ).fetchone()[0]
        assert duplicated == len(repo.shared_sources)
        # One row per id, whatever the registration count.
        assert connection.execute(
            "SELECT COUNT(*) FROM (SELECT source_id FROM sources GROUP BY source_id "
            "HAVING COUNT(*) > 1)"
        ).fetchone()[0] == 0
    finally:
        connection.close()


# -------------------------------------------------------------------- views ----

def test_every_view_is_created_and_queryable(built) -> None:
    """A view that fails to create is a view nobody will notice is missing."""
    root, result = built
    connection = connect(root)
    try:
        created = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'VIEW'"
            ).fetchall()
        }
        missing = sorted(set(VIEWS) - created)
        assert not missing, f"views not created: {missing}"
        for name in sorted(VIEWS):
            connection.execute(f'SELECT * FROM "{name}" LIMIT 1').fetchall()
        assert set(result.views) == set(VIEWS)
    finally:
        connection.close()


def test_coverage_view_shows_thinness_next_to_counts(built) -> None:
    """A claim count must never appear without its gap counts beside it."""
    root, _result = built
    connection = connect(root)
    try:
        columns = [
            d[0]
            for d in connection.execute("SELECT * FROM v_claims_per_target LIMIT 0").description
        ]
        for required in (
            "claim_count",
            "human_claim_count",
            "facets_not_assessed",
            "facets_zero",
            "null_result_count",
            "evidence_gap_count",
            "reporting_gap_count",
            "coverage_note",
        ):
            assert required in columns, f"v_claims_per_target lacks {required}"
    finally:
        connection.close()


def test_unsupported_edges_view_explains_itself(built) -> None:
    """Somebody will ask why an edge they can see is not being counted."""
    root, _result = built
    connection = connect(root)
    try:
        rows = connection.execute(
            "SELECT why_not_support FROM v_unsupported_edges LIMIT 20"
        ).fetchall()
        if not rows:
            pytest.skip("no unsupported claim-derived edges")
        for (reason,) in rows:
            assert reason and reason != "other", f"unexplained reason: {reason!r}"
    finally:
        connection.close()


def test_connect_without_a_build_is_an_actionable_error(tmp_path: Path) -> None:
    """A missing store must not silently answer every query with nothing."""
    (tmp_path / ".blueprint-root").write_text("marker\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError) as caught:
        connect(tmp_path)
    assert "make store" in str(caught.value)


def test_empty_repository_builds_an_empty_store(make_root: RootFactory) -> None:
    """Zero records is a correct state, and the store must reflect it without failing."""
    root = make_root(None)
    result = build_store(root)
    assert result.row_counts["claims"] == 0
    assert result.row_counts["sources"] == 0
    # The type system still lands: state variables and axiom edges.
    assert result.row_counts["state_variables"] > 0
    assert result.row_counts["edges"] > 0
    connection = connect(root)
    try:
        assert connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
    finally:
        connection.close()
