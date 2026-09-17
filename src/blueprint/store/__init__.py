"""The Parquet + DuckDB evidence store.

Everything here is DERIVED and rebuildable offline from the curated records plus the
immutable snapshots in ``data/raw/`` (contract P7). ``data/processed/`` is git-ignored;
``data/processed/MANIFEST.json`` records a sha256 per artefact so a rebuild can be
checked against the one it replaced.

The store carries a ``provenance`` table recording the generation date, the git commit,
the spec and schema versions and a hash of every input. A table of numbers with no
record of where it came from is exactly what this project refuses to produce.

Modules:

* :mod:`blueprint.store.tables` the table specifications and row builders
* :mod:`blueprint.store.views`  SQL views over the tables
* :mod:`blueprint.store.build`  writes Parquet, loads DuckDB, writes the manifest
"""

from __future__ import annotations

from blueprint.store.build import StoreResult, build_store

__all__ = ["StoreResult", "build_store"]
