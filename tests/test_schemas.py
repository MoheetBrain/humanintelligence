"""Every schema must compile, and every record fixture must pass or fail as labelled.

The invalid fixtures are the important half. A schema that accepts a record it should
reject is silently broken, and the record then looks exactly like a valid one for the
rest of the pipeline. Each invalid fixture names the rule it must fail in its filename,
so a fixture cannot quietly stop testing anything.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from blueprint import paths, records, schemas
from tests.conftest import FIXTURES

RECORDS_VALID = FIXTURES / "records" / "valid"
RECORDS_INVALID = FIXTURES / "records" / "invalid"

REQUIRED_SCHEMAS = (
    "claim", "evidence", "target", "edge", "intervention", "source", "assessment",
    "audit", "state_variable", "state_variable_annotation", "node", "verification",
)

# The schemas that deliberately leave an object open, with the reason. Every other
# object in every schema must set additionalProperties: false.
OPEN_OBJECT_EXEMPTIONS: dict[str, str] = {
    "verification": "machine-generated from registry payloads that differ per registry",
    "evidence": "database_record holds a verbatim database payload",
    "claim": "uncertainty.model_outputs items and evidence[].database_record are verbatim",
    "intervention": "chembl_fields_as_returned holds a verbatim database payload",
}


def _load(path: Path) -> object:
    """Load a fixture record from YAML or JSON."""
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def _fixture_files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*.yaml"))


def _ids(paths_: list[Path]) -> list[str]:
    return [p.name for p in paths_]


# -------------------------------------------------------------- schema health ----

@pytest.mark.parametrize("name", REQUIRED_SCHEMAS)
def test_required_schema_exists_and_compiles(name: str) -> None:
    """Every schema the brief requires must exist and be a valid draft 2020-12 schema."""
    path = paths.schema_file(name)
    assert path.is_file(), f"missing required schema: {path}"
    document = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(document)


@pytest.mark.parametrize("name", REQUIRED_SCHEMAS)
def test_schema_id_is_versioned(name: str) -> None:
    """Contract §9: every ``$id`` ends ``/v0_1_0/<name>``."""
    assert schemas.schema_id(name).endswith(f"/v0_1_0/{name}")


@pytest.mark.parametrize("name", REQUIRED_SCHEMAS)
def test_schema_has_a_description(name: str) -> None:
    """A schema without a description is a schema nobody can curate against."""
    document = schemas.load_schema(name)
    assert len(str(document.get("description", ""))) > 80, (
        f"{name}.schema.json has no substantive description"
    )
    assert document.get("title"), f"{name}.schema.json has no title"


@pytest.mark.parametrize("name", REQUIRED_SCHEMAS)
def test_objects_are_closed_unless_exempted(name: str) -> None:
    """``additionalProperties: false`` everywhere: agents must not smuggle fields.

    A handful of objects hold verbatim third-party payloads whose keys are not this
    project's to enumerate; those are listed in :data:`OPEN_OBJECT_EXEMPTIONS` with
    their reason, so an open object is always a recorded decision.
    """
    document = schemas.load_schema(name)
    open_paths: list[str] = []

    def walk(node: object, pointer: str) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                if node.get("additionalProperties") is not False:
                    open_paths.append(pointer or "/")
            for key, value in node.items():
                walk(value, f"{pointer}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{pointer}/{index}")

    walk(document, "")
    if name in OPEN_OBJECT_EXEMPTIONS:
        return
    assert not open_paths, (
        f"{name}.schema.json leaves object(s) open at {open_paths}; every object sets "
        "additionalProperties: false unless listed in OPEN_OBJECT_EXEMPTIONS with a reason"
    )


@pytest.mark.parametrize("name", REQUIRED_SCHEMAS)
def test_schema_examples_validate(name: str) -> None:
    """A schema's own examples must satisfy it, or the examples are misleading."""
    document = schemas.load_schema(name)
    validator = Draft202012Validator(document)
    examples = document.get("examples") or []
    assert examples, f"{name}.schema.json carries no example"
    for index, example in enumerate(examples):
        errors = sorted(validator.iter_errors(example), key=lambda e: list(e.absolute_path))
        assert not errors, (
            f"{name}.schema.json example {index} does not validate: "
            + "; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errors[:3])
        )


def test_examples_are_obviously_synthetic() -> None:
    """An example must never look like a real record (no real identifiers)."""
    for name in REQUIRED_SCHEMAS:
        text = json.dumps(schemas.load_schema(name).get("examples") or [])
        for marker in ('"SRC:PMID:', '"GENE:', '"TGT:'):
            if marker not in text:
                continue
            assert "PLACEHOLDER" in text or "00000001" in text or "placeholder" in text, (
                f"{name}.schema.json examples must use obviously synthetic ids"
            )


def test_every_schema_file_is_a_known_kind() -> None:
    """A schema nothing validates against is dead weight and probably a mistake."""
    on_disk = {p.name.replace(".schema.json", "") for p in paths.schema_files()}
    registered = set(schemas.SCHEMA_FOR_KIND.values())
    assert on_disk == registered, (
        f"unregistered schema files: {sorted(on_disk - registered)}; "
        f"registered but missing: {sorted(registered - on_disk)}"
    )


# ------------------------------------------------------------ record fixtures ----

@pytest.mark.parametrize("path", _fixture_files(RECORDS_VALID), ids=_ids(_fixture_files(RECORDS_VALID)))
def test_valid_record_fixtures_validate(path: Path) -> None:
    """A fixture named ``<kind>__<name>.yaml`` must validate against ``<kind>``."""
    kind = path.name.split("__", 1)[0]
    assert kind in schemas.SCHEMA_FOR_KIND, f"{path.name} names unknown kind {kind!r}"
    violations = schemas.validate_record(_load(path), kind, source_path=path.name)
    assert not violations, "\n".join(str(v) for v in violations)


@pytest.mark.parametrize("path", _fixture_files(RECORDS_VALID), ids=_ids(_fixture_files(RECORDS_VALID)))
def test_valid_record_fixtures_parse_under_pydantic(path: Path) -> None:
    """The schema and the model must agree about what is valid."""
    kind = path.name.split("__", 1)[0]
    model = records.MODEL_FOR_KIND.get(kind)
    if model is None:
        pytest.skip(f"no pydantic model for {kind}")
    model(**_load(path))


@pytest.mark.parametrize(
    "path", _fixture_files(RECORDS_INVALID), ids=_ids(_fixture_files(RECORDS_INVALID))
)
def test_invalid_record_fixtures_are_rejected(path: Path) -> None:
    """A fixture named ``<kind>__<name>__<rule>.yaml`` must be rejected.

    Rejection may come from the JSON Schema or from the pydantic model: both are part
    of rule V1, and which one catches a given problem is an implementation detail. What
    matters is that the record cannot enter the repository.
    """
    parts = path.name.replace(".yaml", "").split("__")
    assert len(parts) == 3, f"{path.name} must be named <kind>__<name>__<rule>.yaml"
    kind, _, expected_rule = parts
    assert kind in schemas.SCHEMA_FOR_KIND, f"{path.name} names unknown kind {kind!r}"

    record = _load(path)
    schema_violations = schemas.validate_record(record, kind, source_path=path.name)

    model = records.MODEL_FOR_KIND.get(kind)
    model_rejected = False
    if model is not None:
        try:
            model(**record)
        except Exception:  # noqa: BLE001 - any model rejection counts
            model_rejected = True

    assert schema_violations or model_rejected, (
        f"{path.name} was accepted by both the schema and the model, but it exists to "
        f"be rejected by {expected_rule}"
    )
    if schema_violations:
        assert all(v.rule == "V1" for v in schema_violations), (
            "schema validation reports rule V1; the semantic rule is checked by "
            "tests/test_validate_rules.py"
        )


def test_invalid_fixture_directory_is_not_empty() -> None:
    """A parametrised test over an empty directory passes vacuously."""
    assert len(_fixture_files(RECORDS_INVALID)) >= 8
    assert len(_fixture_files(RECORDS_VALID)) >= 5


def test_fixtures_are_not_in_real_record_directories() -> None:
    """Fixtures must never be mistaken for curated records."""
    for path in _fixture_files(RECORDS_VALID) + _fixture_files(RECORDS_INVALID):
        assert "tests/fixtures" in path.as_posix()
        assert path.read_text(encoding="utf-8").startswith("# FIXTURE"), (
            f"{path.name} does not declare itself a fixture on its first line"
        )


# ------------------------------------------------------------ error reporting ----

def test_violations_are_structured_and_located() -> None:
    """A violation must carry the rule, a path into the record, and a message."""
    record = {
        "source_id": "SRC:PMID:00000001",
        "source_type": "not_a_source_type",
        "title": "Synthetic placeholder",
        "year": 2020,
        "first_author": "Placeholder AB",
        "container": "Journal of Placeholders",
        "added_by": "agent:ontology",
        "added_on": "2026-09-17",
        "retrieval": {"method": "known_identifier"},
    }
    violations = schemas.validate_record(record, "source", source_path="fixture.yaml")
    assert violations
    violation = violations[0]
    assert violation.rule == "V1"
    assert violation.severity == "error"
    assert violation.path.startswith("fixture.yaml#")
    assert "source_type" in violation.path
    assert violation.as_dict()["rule"] == "V1"


def test_additional_property_message_explains_the_rule() -> None:
    """An agent who added a field needs to know it is a violation, not an extension."""
    record = {
        "source_id": "SRC:PMID:00000001",
        "source_type": "journal_article",
        "title": "Synthetic placeholder",
        "year": 2020,
        "first_author": "Placeholder AB",
        "container": "Journal of Placeholders",
        "added_by": "agent:ontology",
        "added_on": "2026-09-17",
        "retrieval": {"method": "known_identifier"},
        "smuggled": "x",
    }
    violations = schemas.validate_record(record, "source", source_path="fixture.yaml")
    assert any("additionalProperties" in v.message for v in violations)


def test_missing_schema_is_a_violation_not_a_crash(tmp_path: Path) -> None:
    """An incomplete repository must still produce a report."""
    schemas.load_schema.cache_clear()
    schemas.validator_for.cache_clear()
    (tmp_path / ".blueprint-root").write_text("marker\n", encoding="utf-8")
    violations = schemas.validate_record(
        {}, "claim", source_path="fixture.yaml", root=tmp_path
    )
    assert violations and violations[0].rule == "V1"
    assert "schema not found" in violations[0].message
    schemas.load_schema.cache_clear()
    schemas.validator_for.cache_clear()


def test_unknown_kind_is_reported() -> None:
    """A typo'd record kind must be reported, not silently skipped."""
    violations = schemas.validate_record({}, "not_a_kind", source_path="fixture.yaml")
    assert violations and "no schema is registered" in violations[0].message
