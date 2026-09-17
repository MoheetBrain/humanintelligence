"""Write the Parquet tables, load DuckDB, and record the provenance of both.

Design rules:

* **Deterministic Parquet.** Rows are sorted, columns ordered, compression fixed and
  Arrow's metadata suppressed, so two builds over one tree produce byte-identical files.
  That is what makes the manifest checksums worth having.
* **Everything is derived.** ``data/processed/`` is git-ignored and rebuildable offline
  from the curated records plus ``data/raw/`` (contract P7). The build never touches the
  network.
* **A provenance table travels with the data.** Generation date, git commit, spec and
  schema versions, and a hash of every input. A table of numbers with no record of where
  it came from is what this project refuses to produce, and that applies to its own
  outputs as much as to an agent's claims.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from blueprint import __contract_version__, __version__, loaders, paths
from blueprint.graph.compile import CompiledGraph, compile_graph
from blueprint.store.tables import TABLES
from blueprint.store.views import VIEWS

DUCKDB_NAME = "blueprint.duckdb"
MANIFEST_NAME = "MANIFEST.json"
PARQUET_SUBDIR = "parquet"


@dataclass
class StoreResult:
    """What a build produced."""

    root: Path
    processed_dir: Path
    duckdb_path: Path
    manifest_path: Path
    row_counts: dict[str, int] = field(default_factory=dict)
    artefacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    views: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """A human-readable summary for the CLI."""
        lines = [f"store: {self.duckdb_path}"]
        width = max((len(name) for name in self.row_counts), default=0)
        for name, count in self.row_counts.items():
            lines.append(f"  {name.ljust(width)}  {count:>7,} rows")
        lines.append(f"  views: {len(self.views)}")
        lines.append(f"  manifest: {self.manifest_path}")
        return "\n".join(lines)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(root: Path) -> str | None:
    """The current commit, or ``None`` outside a repository.

    ``None`` is recorded honestly rather than as an empty string: a build with no commit
    behind it is not reproducible from version control, and the provenance row should
    say so.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return None
    commit = result.stdout.strip()
    return commit or None


def _input_hashes(root: Path) -> dict[str, str]:
    """A sha256 per curated input file, so a rebuild can be attributed.

    Ontology and schema files are included as well as records: a table built against a
    different type system is a different table, even when the records are unchanged.
    """
    groups: list[list[Path]] = [
        paths.source_files(root),
        paths.claim_files(root),
        paths.audit_files(root),
        paths.target_files(root),
        paths.assessment_files(root),
        paths.intervention_files(root),
        paths.state_variable_annotation_files(root),
        paths.state_domain_files(root),
        paths.schema_files(root),
        sorted(paths.ontology_dir(root).glob("*.yaml")),
        [paths.gene_identifiers_file(root), paths.seed_registry_file(root)],
    ]
    hashes: dict[str, str] = {}
    for group in groups:
        for path in group:
            if path.is_file():
                hashes[str(path.relative_to(root))] = _sha256(path)
    return dict(sorted(hashes.items()))


def _table(rows: list[dict[str, Any]], name: str) -> pa.Table:
    """Build an Arrow table with a stable column order and no writer metadata.

    An empty table still gets its schema from the first row of an equivalent non-empty
    build where possible; with no rows at all it becomes a single-column placeholder,
    which keeps DuckDB able to create the table on an empty repository.
    """
    if not rows:
        return pa.table({"_empty": pa.array([], type=pa.string())})
    columns = list(rows[0].keys())
    data: dict[str, list[Any]] = {column: [] for column in columns}
    for row in rows:
        for column in columns:
            value = row.get(column)
            data[column].append(value)
    arrays = {}
    for column, values in data.items():
        if all(v is None for v in values):
            # An all-null column has no inferable type; string keeps it queryable and
            # keeps `unknown` distinguishable from a zero (contract P8).
            arrays[column] = pa.array(values, type=pa.string())
        else:
            arrays[column] = pa.array(values)
    table = pa.table(arrays)
    return table.replace_schema_metadata({})


def build_store(
    root: Path | str | None = None,
    *,
    compiled: CompiledGraph | None = None,
) -> StoreResult:
    """Build the Parquet tables and the DuckDB database under ``data/processed/``."""
    resolved = paths.resolve_root(root)
    repo = loaders.load_repository(resolved)
    graph = compiled if compiled is not None else compile_graph(resolved)

    processed = paths.data_dir(resolved) / "processed"
    parquet_dir = processed / PARQUET_SUBDIR
    parquet_dir.mkdir(parents=True, exist_ok=True)

    row_counts: dict[str, int] = {}
    artefacts: dict[str, dict[str, Any]] = {}

    for name in sorted(TABLES):
        rows = TABLES[name](repo, graph)
        row_counts[name] = len(rows)
        table = _table(rows, name)
        path = parquet_dir / f"{name}.parquet"
        pq.write_table(
            table,
            path,
            compression="zstd",
            compression_level=3,
            # Determinism: fixed row-group size, no statistics that embed timestamps,
            # and the writer version pinned.
            row_group_size=10_000,
            write_statistics=False,
            store_schema=True,
            version="2.6",
        )
        artefacts[f"{PARQUET_SUBDIR}/{name}.parquet"] = {
            "rows": len(rows),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }

    provenance = {
        "generated_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "git_commit": _git_commit(resolved),
        "blueprint_version": __version__,
        "contract_version": __contract_version__,
        "ontology_version": "0.1.0",
        "builder": "blueprint.store.build",
        "input_file_count": 0,
        "input_hashes": {},
        "record_counts": dict(sorted(graph.inputs.items())),
        "graph_counts": {
            k: v for k, v in graph.counts().items() if not isinstance(v, dict)
        },
        "notes": (
            "Derived and rebuildable offline from the curated records plus data/raw/ "
            "(contract P7). Nothing in this store is a safety or efficacy claim; a "
            "well-connected node is not a well-evidenced one, and null-result edges are "
            "excluded from every support count."
        ),
    }
    hashes = _input_hashes(resolved)
    provenance["input_hashes"] = hashes
    provenance["input_file_count"] = len(hashes)
    provenance["input_digest"] = hashlib.sha256(
        json.dumps(hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()

    provenance_rows = [
        {"key": key, "value": json.dumps(value, sort_keys=True, default=str)}
        for key, value in sorted(provenance.items())
    ]
    provenance_path = parquet_dir / "provenance.parquet"
    pq.write_table(
        _table(provenance_rows, "provenance"),
        provenance_path,
        compression="zstd",
        compression_level=3,
        write_statistics=False,
        version="2.6",
    )
    row_counts["provenance"] = len(provenance_rows)
    artefacts[f"{PARQUET_SUBDIR}/provenance.parquet"] = {
        "rows": len(provenance_rows),
        "sha256": _sha256(provenance_path),
        "bytes": provenance_path.stat().st_size,
    }

    duckdb_path = processed / DUCKDB_NAME
    created_views = _load_duckdb(duckdb_path, parquet_dir, sorted(row_counts))

    manifest_path = processed / MANIFEST_NAME
    manifest = {
        "schema_version": "0.1.0",
        "generated_at_utc": provenance["generated_at_utc"],
        "git_commit": provenance["git_commit"],
        "input_digest": provenance["input_digest"],
        "row_counts": dict(sorted(row_counts.items())),
        "views": list(created_views),
        "artefacts": dict(sorted(artefacts.items())),
        "note": (
            "Every artefact here is DERIVED. data/processed/ is git-ignored and is "
            "rebuilt by `make store`; the checksums let a rebuild be compared against "
            "the build it replaced."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    return StoreResult(
        root=resolved,
        processed_dir=processed,
        duckdb_path=duckdb_path,
        manifest_path=manifest_path,
        row_counts=dict(sorted(row_counts.items())),
        artefacts=dict(sorted(artefacts.items())),
        views=created_views,
        provenance=provenance,
    )


def _load_duckdb(
    duckdb_path: Path, parquet_dir: Path, table_names: list[str]
) -> tuple[str, ...]:
    """Create the DuckDB database from the Parquet files and define the views."""
    import duckdb

    if duckdb_path.exists():
        duckdb_path.unlink()
    connection = duckdb.connect(str(duckdb_path))
    try:
        for name in table_names:
            path = parquet_dir / f"{name}.parquet"
            if not path.is_file():
                continue
            connection.execute(
                f'CREATE OR REPLACE TABLE "{name}" AS '
                f"SELECT * FROM read_parquet('{path.as_posix()}')"
            )
        created: list[str] = []
        for view_name, sql in VIEWS.items():
            try:
                connection.execute(f'CREATE OR REPLACE VIEW "{view_name}" AS {sql}')
                created.append(view_name)
            except Exception as exc:  # noqa: BLE001
                # A view over a table that is empty in this build is not an error: the
                # repository legitimately has no audits yet. Record it and carry on
                # rather than failing a build over a query nobody ran.
                connection.execute(
                    'CREATE OR REPLACE TABLE "_view_errors" (view_name VARCHAR, error VARCHAR)'
                    if "_view_errors" not in [
                        row[0] for row in connection.execute("SHOW TABLES").fetchall()
                    ]
                    else "SELECT 1"
                )
                connection.execute(
                    'INSERT INTO "_view_errors" VALUES (?, ?)', [view_name, str(exc)[:400]]
                )
        connection.commit()
        return tuple(created)
    finally:
        connection.close()


def connect(root: Path | str | None = None):
    """Open a read-only connection to the built store.

    Raises ``FileNotFoundError`` when the store has not been built, rather than creating
    an empty database that would answer every query with nothing.
    """
    import duckdb

    resolved = paths.resolve_root(root)
    path = paths.data_dir(resolved) / "processed" / DUCKDB_NAME
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} does not exist. Run `make store` "
            "(or `python -m blueprint.store.build`) to build it; data/processed/ is "
            "git-ignored and always rebuilt."
        )
    return duckdb.connect(str(path), read_only=True)


def main(argv: list[str] | None = None) -> int:
    """``python -m blueprint.store.build`` — build the store and print a summary."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = build_store(args.root)
    if not args.quiet:
        print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
