"""Load the JSON Schemas and validate records against them, returning violations.

Design rules:

* Validation returns STRUCTURED VIOLATIONS, not exceptions and not raw jsonschema
  errors. Each violation carries the contract rule id (``V1`` for a schema failure), a
  JSON-pointer-ish path into the record, and a message an agent can act on.
* Schemas are compiled once per root and cached. ``jsonschema`` compilation is the
  expensive part of validating a few hundred records.
* Errors are reported in DEPTH ORDER, deepest first, because the deepest error is
  almost always the actionable one: a top-level ``anyOf``/``allOf`` failure tells an
  agent nothing useful.
* A missing schema file is a violation, not a crash. An incomplete repository must
  still produce a report.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from blueprint import paths
from blueprint.violations import Violation, error

# Record kind -> schema stem. The kinds are what loaders and the rule engine speak.
SCHEMA_FOR_KIND: dict[str, str] = {
    "source": "source",
    "claim": "claim",
    "evidence": "evidence",
    "target": "target",
    "assessment": "assessment",
    "audit": "audit",
    "intervention": "intervention",
    "state_variable": "state_variable",
    "state_variable_annotation": "state_variable_annotation",
    "node": "node",
    "edge": "edge",
    "verification": "verification",
    "external_analysis": "external_analysis",
    # X02 row kinds: one row of a delivered external table, validated by
    # pipelines/integration/ingest_x02.py before anything is compiled into the graph.
    "x02_credible_set": "x02_credible_set",
    "x02_credible_set_variant": "x02_credible_set_variant",
    "x02_qtl_colocalisation": "x02_qtl_colocalisation",
    "x02_regulatory_prediction": "x02_regulatory_prediction",
    "x02_negative_result": "x02_negative_result",
}


class SchemaUnavailable(FileNotFoundError):
    """Raised by :func:`load_schema` when a schema file does not exist."""


@lru_cache(maxsize=64)
def load_schema(name: str, root: Path | str | None = None) -> dict[str, Any]:
    """Load one schema document by bare name (``"claim"``)."""
    path = paths.schema_file(name, root)
    if not path.is_file():
        raise SchemaUnavailable(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=64)
def validator_for(name: str, root: Path | str | None = None) -> Draft202012Validator:
    """Compiled validator for schema ``name``.

    Raises :class:`jsonschema.exceptions.SchemaError` when the schema itself is
    invalid, which is a repository bug and should stop the run loudly.
    """
    schema = load_schema(name, root)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def available_kinds(root: Path | str | None = None) -> list[str]:
    """Record kinds whose schema file exists, sorted."""
    return sorted(
        kind
        for kind, stem in SCHEMA_FOR_KIND.items()
        if paths.schema_file(stem, root).is_file()
    )


def _pointer(error_path: Any) -> str:
    """Render a jsonschema error path as a slash-separated pointer."""
    parts = [str(part) for part in error_path]
    return "/" + "/".join(parts) if parts else "/"


def validate_record(
    record: Any,
    kind: str,
    *,
    source_path: str,
    record_id: str | None = None,
    root: Path | str | None = None,
    rule: str = "V1",
) -> list[Violation]:
    """Validate ``record`` against the schema for ``kind``.

    ``source_path`` is the repository-relative file the record came from and is used to
    build a locator of the form ``path#/pointer/into/record``. Returns an empty list
    when the record conforms.
    """
    stem = SCHEMA_FOR_KIND.get(kind)
    if stem is None:
        return [
            error(
                rule,
                source_path,
                f"no schema is registered for record kind {kind!r}; known kinds: "
                f"{sorted(SCHEMA_FOR_KIND)}",
                record_id=record_id,
            )
        ]
    try:
        validator = validator_for(stem, root)
    except SchemaUnavailable as exc:
        return [error(rule, source_path, str(exc), record_id=record_id)]
    except SchemaError as exc:  # pragma: no cover - a repository bug, surfaced verbatim
        return [
            error(
                rule,
                str(paths.schema_file(stem, root)),
                f"schema {stem!r} is not a valid JSON Schema: {exc.message}",
            )
        ]

    errors = sorted(
        validator.iter_errors(record),
        key=lambda e: (-len(e.absolute_path), list(map(str, e.absolute_path))),
    )
    violations: list[Violation] = []
    for item in errors:
        pointer = _pointer(item.absolute_path)
        detail = item.message
        if item.validator == "additionalProperties":
            detail = (
                f"{item.message} — every object in these schemas sets "
                "additionalProperties: false, so an unexpected key is a contract "
                "violation, not an extension"
            )
        violations.append(
            error(
                rule,
                f"{source_path}#{pointer}",
                detail,
                record_id=record_id,
                context={"schema": stem, "keyword": str(item.validator)},
            )
        )
    return violations


def validate_many(
    records: list[tuple[Any, str, str | None]],
    kind: str,
    *,
    root: Path | str | None = None,
) -> list[Violation]:
    """Validate a list of ``(record, source_path, record_id)`` tuples of one kind."""
    out: list[Violation] = []
    for record, source_path, record_id in records:
        out.extend(
            validate_record(
                record, kind, source_path=source_path, record_id=record_id, root=root
            )
        )
    return out


def schema_id(name: str, root: Path | str | None = None) -> str:
    """The ``$id`` of schema ``name`` (must end ``/v0_1_0/<name>``)."""
    return str(load_schema(name, root).get("$id", ""))
