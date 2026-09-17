"""Access to the controlled vocabularies in ``ontology/vocabularies.yaml``.

Design rules:

* ``ontology/vocabularies.yaml`` is the SINGLE SOURCE OF TRUTH for every enumerated
  value in the contract. The JSON Schemas carry the same lists inline so that a schema
  file is self-contained, and :mod:`blueprint.sync_schema_enums` proves the two agree.
* A vocabulary may declare ``same_values_as: other`` (``endpoint_category`` reuses
  ``phenotype_class``). Resolution happens here, once, so no caller special-cases it.
* Auxiliary keys on a vocabulary (``human_evidence_values``, ``passing_values``,
  ``efficacy_licensing_values``, ...) are SUBSETS used by validator rules. They are
  checked to be subsets of ``values`` at load time, so a typo in the ontology fails
  fast instead of silently disabling a rule.
* Loads are cached per root. YAML parsing is not free and the validator asks for
  vocabularies in inner loops.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from blueprint import paths

# Keys that hold a subset of `values` and are therefore checked at load time.
SUBSET_KEYS: tuple[str, ...] = (
    "passing_values",
    "efficacy_licensing_values",
    "allowed_in_curated_records",
    "human_values",
    "non_human_values",
    "human_evidence_values",
    "adult_values",
    "developmental_values",
    "healthy_values",
    "deficit_values",
    "association_only_values",
    "adult_perturbation_values",
    "developmentally_confounded_values",
    "human_interventional_values",
    "secondary_report_values",
    "secondary_values",
    "independent_values",
    "requires_superseding_audit",
    "requires_null_level",
    "requires_claim_refs",
    "requires_empty_list",
    "requires_rationale",
    "resolved_values",
    "unresolved_values",
    "controlled_values",
    "snapshot_verified_values",
    "graph_inert_values",
    "human_harm_values",
    "harm_values",
    "evidential_classes",
    "tool_mediated_values",
    "measured_values",
    "gap_values",
    "margin_suffixes",
    "risk_suffixes",
    "source_refs_only_values",
    "excluded_from_intelligence_endpoints",
    "graph_compiled_values",
    "constraint_domains",
    "state_vector_values",
    "parameter_values",
    "human_proposition_facets",
    "defaults",
)


class VocabularyError(LookupError):
    """Raised when a vocabulary or one of its keys does not exist."""


@lru_cache(maxsize=8)
def load(root: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load and validate every vocabulary, keyed by name.

    Resolves ``same_values_as`` indirection and verifies that each subset key is
    genuinely a subset of ``values``. Raises :class:`VocabularyError` when the
    ontology is internally inconsistent — a broken vocabulary must never degrade
    silently into a rule that accepts everything.
    """
    path = paths.vocabularies_file(root)
    if not path.is_file():
        raise VocabularyError(f"vocabulary file not found: {path}")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = document.get("vocabularies") or {}

    resolved: dict[str, dict[str, Any]] = {}
    for name, spec in raw.items():
        if not isinstance(spec, dict):
            raise VocabularyError(f"vocabulary {name!r} is not a mapping")
        entry = dict(spec)
        alias = entry.pop("same_values_as", None)
        if alias is not None:
            source = raw.get(alias)
            if source is None or "values" not in source:
                raise VocabularyError(f"vocabulary {name!r} aliases unknown {alias!r}")
            entry["values"] = list(source["values"])
            entry["aliased_from"] = alias
            for key in SUBSET_KEYS:
                if key in source and key not in entry:
                    entry[key] = list(source[key])
        if "values" not in entry:
            raise VocabularyError(f"vocabulary {name!r} has no `values`")
        resolved[name] = entry

    for name, entry in resolved.items():
        allowed = set(entry["values"])
        for key in SUBSET_KEYS:
            subset = entry.get(key)
            if subset is None:
                continue
            unknown = sorted(str(v) for v in subset if v not in allowed)
            if unknown:
                raise VocabularyError(
                    f"vocabulary {name!r} key {key!r} contains values not in `values`: "
                    f"{unknown}"
                )
    return resolved


def names(root: Path | str | None = None) -> list[str]:
    """Every vocabulary name, sorted."""
    return sorted(load(root))


def values(name: str, root: Path | str | None = None) -> list[str]:
    """The allowed values of vocabulary ``name``, in declaration order."""
    table = load(root)
    if name not in table:
        raise VocabularyError(f"unknown vocabulary {name!r}; known: {sorted(table)}")
    return list(table[name]["values"])


def value_set(name: str, root: Path | str | None = None) -> set[str]:
    """The allowed values of vocabulary ``name`` as a set, for membership tests."""
    return set(values(name, root))


def subset(name: str, key: str, root: Path | str | None = None) -> list[str]:
    """An auxiliary subset such as ``("facet", "human_proposition_facets")``.

    Returns an empty list when the key is absent, because an absent subset means
    "no values qualify", which is the safe reading for every rule that uses one.
    """
    table = load(root)
    if name not in table:
        raise VocabularyError(f"unknown vocabulary {name!r}; known: {sorted(table)}")
    return list(table[name].get(key) or [])


def meta(name: str, key: str, root: Path | str | None = None) -> Any:
    """Any non-subset attribute of a vocabulary (``default``, ``ordinal``, ...)."""
    table = load(root)
    if name not in table:
        raise VocabularyError(f"unknown vocabulary {name!r}; known: {sorted(table)}")
    return table[name].get(key)


def facet_catalogue(root: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """The facet catalogue keyed by facet name (owners, dimensions, inverse flags)."""
    entries = meta("facet", "catalogue", root) or []
    return {entry["facet"]: entry for entry in entries}


def facet_owners(facet: str, root: Path | str | None = None) -> list[str]:
    """Agent ids permitted to write ``facet``; ``lead_atlas`` is returned verbatim."""
    entry = facet_catalogue(root).get(facet)
    return list(entry.get("owners") or []) if entry else []


def is_human_proposition_facet(facet: str, root: Path | str | None = None) -> bool:
    """Whether rule V21 applies to ``facet`` (its proposition is about humans)."""
    return facet in set(subset("facet", "human_proposition_facets", root))


def human_evidence_values(root: Path | str | None = None) -> set[str]:
    """``translation.human_relevance`` values that count as human evidence (V21)."""
    return set(subset("translation_human_relevance", "human_evidence_values", root))


def efficacy_licensing_claim_types(root: Path | str | None = None) -> set[str]:
    """``claim_type`` values that may license an effect assertion (V16)."""
    return set(subset("claim_type", "efficacy_licensing_values", root))
