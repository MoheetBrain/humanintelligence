"""Prove that the JSON Schema enums match ``ontology/vocabularies.yaml``.

Why this exists
---------------
The contract's enumerated values need two representations: ``ontology/vocabularies.yaml``
(the single source of truth, with semantics and subsets) and the ``enum`` keywords
inside ``schemas/*.json`` (so a schema file is self-contained and usable by any JSON
Schema tool). Two representations of one fact drift. This module makes drift impossible
to commit:

* ``--check`` walks every schema, finds every ``enum`` that declares its origin in a
  sibling ``$comment`` of the form ``vocabulary: <name>``, and compares it to the
  vocabulary. ``tests/test_ontology.py`` runs this, so a divergence fails the suite.
* ``--write`` rewrites the schemas from the vocabularies, so fixing drift is mechanical
  rather than a hand-edit across twelve files.

Design rules:

* The BINDING IS DECLARED IN THE SCHEMA, not in a table here. Adding an enum to a
  schema with the right ``$comment`` enrols it automatically; there is no second list
  to keep in step. A ``$comment`` naming an unknown vocabulary is a failure, not a
  silent skip.
* A comment may name a subset, ``vocabulary: <name> (<subset_key>)``, which is how
  ``uncertainty.representation`` binds to ``allowed_in_curated_records``.
* Comments that do not start with ``vocabulary:`` are ignored: schemas also carry
  enums derived from ``ontology/nodes.yaml`` and ``ontology/edges.yaml``, which
  :func:`check_ontology_derived_enums` covers separately.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from blueprint import ontology, paths, vocab

COMMENT_RE = re.compile(r"^vocabulary:\s*(?P<name>[a-z0-9_]+)\s*(?:\((?P<subset>[a-z0-9_]+)\))?")

# Enums whose values come from the ontology rather than from a vocabulary. The key is
# the marker written in the schema's `$comment`; the value resolves the expected list.
ONTOLOGY_DERIVED: dict[str, str] = {
    "ontology/nodes.yaml: node type names": "node_types",
    "ontology/nodes.yaml: layers": "layers",
    "ontology/edges.yaml: relation names": "relations",
    "ontology/nodes.yaml: intervention-layer entity types": "intervention_entity_types",
    "vocabulary: agent_id (bare names, orchestrator excluded)": "agent_bare_names",
}


def _walk(node: Any, pointer: str = "") -> list[tuple[str, dict[str, Any]]]:
    """Yield ``(json_pointer, mapping)`` for every mapping in a JSON document."""
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(node, dict):
        found.append((pointer or "/", node))
        for key, value in node.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            found.extend(_walk(value, f"{pointer}/{escaped}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_walk(value, f"{pointer}/{index}"))
    return found


def _expected_ontology_values(kind: str, root: Path | str | None) -> list[str]:
    """Resolve an ontology-derived enum marker to its expected value list."""
    index = ontology.load(root)
    if kind == "node_types":
        return sorted(index.nodes)
    if kind == "layers":
        return list(index.layers)
    if kind == "relations":
        return sorted(index.edges)
    if kind == "intervention_entity_types":
        excluded = {"Target", "DesiredEffect", "AdverseEffect", "StateVariable", "StateDomain"}
        return sorted(
            name
            for name, spec in index.nodes.items()
            if "intervention" in spec.layers and name not in excluded
        )
    if kind == "agent_bare_names":
        return [
            agent.split(":", 1)[1]
            for agent in vocab.values("agent_id", root)
            if agent != "agent:orchestrator"
        ]
    raise KeyError(f"unknown ontology-derived enum kind {kind!r}")


def check(root: Path | str | None = None) -> list[str]:
    """Return a list of human-readable drift problems; empty means in sync.

    Checks both directions of the contract:

    1. every schema ``enum`` that declares a vocabulary matches that vocabulary; and
    2. every vocabulary is referenced by at least one schema, so a vocabulary cannot be
       added and then quietly never enforced.
    """
    problems: list[str] = []
    referenced: set[str] = set()

    for schema_path in paths.schema_files(root):
        try:
            document = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{schema_path.name}: not valid JSON: {exc}")
            continue
        for pointer, mapping in _walk(document):
            if "enum" not in mapping:
                continue
            comment = str(mapping.get("$comment", "")).strip()
            if not comment:
                problems.append(
                    f"{schema_path.name}{pointer}: enum has no `$comment` declaring its "
                    "origin, so it cannot be checked against ontology/vocabularies.yaml"
                )
                continue
            if comment in ONTOLOGY_DERIVED:
                expected = _expected_ontology_values(ONTOLOGY_DERIVED[comment], root)
                if comment.startswith("vocabulary: agent_id"):
                    referenced.add("agent_id")
                actual = list(mapping["enum"])
                if actual != expected:
                    problems.append(
                        f"{schema_path.name}{pointer}: enum does not match "
                        f"{comment!r}\n    schema:   {actual}\n    ontology: {expected}"
                    )
                continue
            match = COMMENT_RE.match(comment)
            if match is None:
                problems.append(
                    f"{schema_path.name}{pointer}: `$comment` {comment!r} does not name a "
                    "vocabulary or a known ontology-derived enum"
                )
                continue
            name = match.group("name")
            subset_key = match.group("subset")
            referenced.add(name)
            try:
                expected = (
                    vocab.subset(name, subset_key, root)
                    if subset_key
                    else vocab.values(name, root)
                )
            except vocab.VocabularyError as exc:
                problems.append(f"{schema_path.name}{pointer}: {exc}")
                continue
            actual = list(mapping["enum"])
            if actual != expected:
                problems.append(
                    f"{schema_path.name}{pointer}: enum drifted from vocabulary {name!r}"
                    + (f" subset {subset_key!r}" if subset_key else "")
                    + f"\n    schema:     {actual}\n    vocabulary: {expected}"
                )

    # Vocabularies that no schema enforces. Some are used only by the rule engine or by
    # other ontology files, so this is reported as informational drift rather than
    # silently accepted: an unreferenced vocabulary is usually a forgotten binding.
    unreferenced = sorted(set(vocab.names(root)) - referenced - _NON_SCHEMA_VOCABULARIES)
    for name in unreferenced:
        problems.append(
            f"vocabulary {name!r} is not bound to any schema enum and is not listed in "
            "blueprint.sync_schema_enums._NON_SCHEMA_VOCABULARIES; either bind it or "
            "record deliberately why it is not enforced by a schema"
        )
    return problems


# Vocabularies deliberately not bound to a schema enum, with the reason. Keeping this
# list explicit is what stops "no schema uses it" from becoming invisible.
_NON_SCHEMA_VOCABULARIES: set[str] = {
    # consumed by the rule engine and reports, not by a record field
    "violation_severity",          # validator output, not a record
    "dimension",                   # ranking model (agent:integration), not a record field
    "evidence_strength_v1",        # expressed as integer minimum/maximum in schemas
    "state_domain",               # expressed inside the SV id_pattern
    "task_status",                 # docs/TASK_DAG.yaml only
    "action_type",                 # docs/TASK_DAG.yaml; enforced by blueprint.policy
    "uncertainty_representation",  # bound through its allowed_in_curated_records subset
}


def write(root: Path | str | None = None) -> list[Path]:
    """Rewrite every schema's declared enums from the vocabularies.

    Returns the schema files that changed. Formatting is normalised (2-space indent,
    sorted keys, LF ending) so the output is byte-deterministic.
    """
    changed: list[Path] = []
    for schema_path in paths.schema_files(root):
        original = schema_path.read_text(encoding="utf-8")
        document = json.loads(original)
        for _, mapping in _walk(document):
            if "enum" not in mapping:
                continue
            comment = str(mapping.get("$comment", "")).strip()
            if comment in ONTOLOGY_DERIVED:
                mapping["enum"] = _expected_ontology_values(ONTOLOGY_DERIVED[comment], root)
                continue
            match = COMMENT_RE.match(comment)
            if match is None:
                continue
            name = match.group("name")
            subset_key = match.group("subset")
            try:
                mapping["enum"] = (
                    vocab.subset(name, subset_key, root)
                    if subset_key
                    else vocab.values(name, root)
                )
            except vocab.VocabularyError:
                continue
        updated = json.dumps(document, indent=2, sort_keys=True) + "\n"
        if updated != original:
            schema_path.write_text(updated, encoding="utf-8", newline="\n")
            changed.append(schema_path)
    return changed


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``--check`` reports drift, ``--write`` fixes it."""
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--check", action="store_true", help="report drift and exit non-zero")
    parser.add_argument("--write", action="store_true", help="rewrite schema enums from vocabularies")
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    args = parser.parse_args(argv)

    if args.write:
        changed = write(args.root)
        for path in changed:
            print(f"updated {path}")
        print(f"{len(changed)} schema file(s) updated")

    problems = check(args.root)
    for problem in problems:
        print(problem)
    if problems:
        print(f"\n{len(problems)} schema/vocabulary drift problem(s)")
        return 1
    print("schemas and ontology/vocabularies.yaml agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
