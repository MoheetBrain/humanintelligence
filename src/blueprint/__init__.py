"""The library behind the Intelligence Blueprint CLIs.

Design rules (see docs/DATA_CONTRACT.md and docs/ONTOLOGY_NOTES.md):

* **Every path is injectable.** No module reads a hard-coded absolute path. Functions
  that touch the repository take an optional ``root``, so a test can point the whole
  library at a fixture tree (``tests/fixtures/...``) without monkeypatching.
* **An empty repository is valid.** Sprint 1 starts with zero records. Every loader
  returns an empty collection rather than raising, and the validator exits 0 with an
  honest "0 claims, 0 sources" summary. Absence of records is never reported as an
  error, because the alternative is agents inventing records to make a build pass.
* **Deterministic.** Loaders sort their inputs; writers use sorted keys and LF
  endings. Two runs over the same tree produce byte-identical output.
* **The ontology is data, not code.** Node types, relations, vocabularies and rules
  are YAML/JSON; this package only indexes and enforces them. Adding a node type must
  never require a code change.
* **No network.** Nothing in this package opens a socket. Registry verification reads
  snapshots written by ``scripts/fetch_source_metadata.py``.

Phase 1 (this sprint) provides the type system, schemas, records, loaders and the
rule engine. Phase 2 adds ``blueprint.store`` (Parquet/DuckDB), ``blueprint.compile``
(the NetworkX three-layer compiler), ``blueprint.export`` and ``blueprint.reports``;
those modules are named in docs/ONTOLOGY_NOTES.md and deliberately not written yet.
"""

from __future__ import annotations

__version__ = "0.1.0"
__contract_version__ = "0.1.0"
__all__ = ["__version__", "__contract_version__"]
