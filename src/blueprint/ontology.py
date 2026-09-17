"""Load and index ``ontology/*.yaml``; answer legality questions about triples.

Design rules:

* The ontology is DATA. This module indexes it and answers questions; it hard-codes no
  node type, relation or prefix. A new node type is a YAML edit.
* ``is_legal_triple`` is the executable form of contract rule V3, and it resolves the
  parent chain in ``nodes.yaml``: a ``Receptor`` subject is accepted wherever
  ``Protein`` is declared, and a ``Protein`` subject is NOT accepted where ``Receptor``
  is required. Subtyping is one-directional on purpose.
* Errors are ACTIONABLE. ``explain_triple`` returns a message naming which side failed
  and what the legal alternatives are, because the audience is an agent curating a
  record, not a compiler.
* Loading is cached per root and the index is immutable once built.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from blueprint import paths


class OntologyError(ValueError):
    """Raised when the ontology files are internally inconsistent or unreadable."""


@dataclass(frozen=True)
class NodeType:
    """One declared node type."""

    name: str
    layer: str
    description: str
    id_prefixes: tuple[str, ...]
    id_pattern: str
    parent: str | None
    required_attributes: tuple[str, ...]
    optional_attributes: tuple[str, ...]
    shared_with_layers: tuple[str, ...] = ()

    @property
    def layers(self) -> tuple[str, ...]:
        """Home layer plus any layers this type is shared with."""
        return (self.layer, *self.shared_with_layers)


@dataclass(frozen=True)
class EdgeType:
    """One declared relation."""

    name: str
    layers: tuple[str, ...]
    description: str
    domain: tuple[str, ...]
    range: tuple[str, ...]
    requires_claim: bool
    allowed_provenance_classes: tuple[str, ...]
    allowed_claim_types: tuple[str, ...]
    asserts_effect: bool
    asserts_absence_of_effect: bool
    requires_multiple_species: bool
    negatable: bool
    effect_asserting_ranges: tuple[str, ...]
    directional: bool
    inverse: str | None
    semantics: str


@dataclass(frozen=True)
class Primitive:
    """One computational primitive working definition."""

    id: str
    name: str
    definition: str
    related_state_variables: tuple[str, ...]
    human_measurement_paradigms: tuple[str, ...]
    animal_analogue_caveat: str
    definition_status: str


@dataclass(frozen=True)
class DefinitionalEdge:
    """One claim-free ontology axiom from ``ontology/definitional_edges.yaml``."""

    subject: str
    predicate: str
    object: str
    provenance_class: str
    basis: str
    defined_by: str


@dataclass(frozen=True)
class Ontology:
    """Indexed, immutable view of the ontology files."""

    root: Path
    prefixes: tuple[str, ...]
    layers: tuple[str, ...]
    nodes: dict[str, NodeType]
    edges: dict[str, EdgeType]
    groups: dict[str, tuple[str, ...]]
    primitives: dict[str, Primitive]
    definitional_edges: tuple[DefinitionalEdge, ...]
    provenance_classes: tuple[str, ...]
    _prefix_index: dict[str, tuple[str, ...]] = field(default_factory=dict)
    _pattern_cache: dict[str, re.Pattern[str]] = field(default_factory=dict)

    # ----------------------------------------------------------- node queries ---

    def node_types_for_prefix(self, prefix: str) -> tuple[str, ...]:
        """Node type names that declare ``prefix``, sorted."""
        return self._prefix_index.get(prefix, ())

    def compiled_id_pattern(self, node_type: str) -> re.Pattern[str]:
        """Compiled ``id_pattern`` of ``node_type`` (compiled once, then cached)."""
        cached = self._pattern_cache.get(node_type)
        if cached is not None:
            return cached
        spec = self.nodes.get(node_type)
        if spec is None:
            raise OntologyError(f"unknown node type {node_type!r}")
        compiled = re.compile(spec.id_pattern)
        self._pattern_cache[node_type] = compiled
        return compiled

    def ancestors(self, node_type: str) -> tuple[str, ...]:
        """``node_type`` followed by its parent chain, nearest first."""
        if node_type not in self.nodes:
            raise OntologyError(f"unknown node type {node_type!r}")
        chain: list[str] = []
        current: str | None = node_type
        seen: set[str] = set()
        while current is not None:
            if current in seen:
                raise OntologyError(f"cyclic parent chain at {current!r}")
            seen.add(current)
            chain.append(current)
            current = self.nodes[current].parent
        return tuple(chain)

    def descendants(self, node_type: str) -> tuple[str, ...]:
        """``node_type`` plus every node type that inherits from it, sorted."""
        out = {node_type}
        changed = True
        while changed:
            changed = False
            for name, spec in self.nodes.items():
                if spec.parent in out and name not in out:
                    out.add(name)
                    changed = True
        return tuple(sorted(out))

    def is_subtype_of(self, node_type: str, candidate_parent: str) -> bool:
        """Whether ``node_type`` is ``candidate_parent`` or inherits from it."""
        return candidate_parent in self.ancestors(node_type)

    # ---------------------------------------------------------- edge queries ---

    def expand_types(self, names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        """Expand group names into node type names, preserving order and de-duping."""
        out: list[str] = []
        for name in names:
            members = self.groups.get(name)
            candidates = members if members is not None else (name,)
            for candidate in candidates:
                if candidate not in out:
                    out.append(candidate)
        return tuple(out)

    def edge_domain(self, predicate: str) -> tuple[str, ...]:
        """Declared subject types of ``predicate``, groups expanded."""
        return self.expand_types(self._edge(predicate).domain)

    def edge_range(self, predicate: str) -> tuple[str, ...]:
        """Declared object types of ``predicate``, groups expanded."""
        return self.expand_types(self._edge(predicate).range)

    def _edge(self, predicate: str) -> EdgeType:
        spec = self.edges.get(predicate)
        if spec is None:
            raise OntologyError(
                f"unknown relation {predicate!r}. Relations are closed; see "
                f"ontology/edges.yaml. Known: {sorted(self.edges)}"
            )
        return spec

    def _accepts(self, node_type: str, declared: tuple[str, ...]) -> bool:
        """Whether ``node_type`` satisfies one side of a relation declaration."""
        if node_type not in self.nodes:
            return False
        allowed = set(self.expand_types(declared))
        return any(ancestor in allowed for ancestor in self.ancestors(node_type))

    def is_legal_triple(self, subject_type: str, predicate: str, object_type: str) -> bool:
        """Whether ``(subject_type, predicate, object_type)`` is a legal edge (V3).

        A subtype is accepted wherever its ancestor is declared. Unknown node types and
        unknown relations are illegal rather than an error, so a caller validating many
        triples gets a uniform boolean; use :meth:`explain_triple` for the reason.
        """
        spec = self.edges.get(predicate)
        if spec is None:
            return False
        return self._accepts(subject_type, spec.domain) and self._accepts(
            object_type, spec.range
        )

    def explain_triple(self, subject_type: str, predicate: str, object_type: str) -> str | None:
        """``None`` when the triple is legal, otherwise an actionable explanation."""
        spec = self.edges.get(predicate)
        if spec is None:
            close = sorted(
                name for name in self.edges if predicate.upper() in name or name in predicate.upper()
            )
            hint = f" Did you mean one of {close}?" if close else ""
            return (
                f"unknown relation {predicate!r}: relations are closed (ontology/"
                f"edges.yaml).{hint}"
            )
        problems: list[str] = []
        if subject_type not in self.nodes:
            problems.append(f"unknown subject node type {subject_type!r}")
        elif not self._accepts(subject_type, spec.domain):
            problems.append(
                f"{subject_type} is not a legal subject for {predicate}; its domain is "
                f"{sorted(self.expand_types(spec.domain))}"
            )
        if object_type not in self.nodes:
            problems.append(f"unknown object node type {object_type!r}")
        elif not self._accepts(object_type, spec.range):
            problems.append(
                f"{object_type} is not a legal object for {predicate}; its range is "
                f"{sorted(self.expand_types(spec.range))}"
            )
        if not problems:
            return None
        return "; ".join(problems)

    def legal_predicates(self, subject_type: str, object_type: str) -> tuple[str, ...]:
        """Every relation that would make this subject/object pair legal, sorted."""
        return tuple(
            sorted(
                name
                for name in self.edges
                if self.is_legal_triple(subject_type, name, object_type)
            )
        )

    def effect_asserting_predicates(self) -> tuple[str, ...]:
        """Relations whose ``asserts_effect`` is true (the V16 gate), sorted."""
        return tuple(sorted(name for name, spec in self.edges.items() if spec.asserts_effect))

    def effect_asserting_object_types(self) -> tuple[str, ...]:
        """Node types that make any edge into them an efficacy assertion (V16).

        ``DesiredEffect`` and its subtypes: the contract requires that an edge whose
        range is a desired effect be treated exactly like ``CHANGES_STATE``.
        """
        if "DesiredEffect" not in self.nodes:
            return ()
        return self.descendants("DesiredEffect")

    def asserts_effect(self, predicate: str, object_type: str | None = None) -> bool:
        """Whether an edge of ``predicate`` into ``object_type`` asserts an effect.

        True when the relation itself asserts an effect (``CHANGES_STATE``), when the
        object type is in the relation's ``effect_asserting_ranges`` (a regulation
        relation reaching a phenotype), or when the object is a ``DesiredEffect``.
        This is the whole surface that contract rule V16 gates.
        """
        spec = self.edges.get(predicate)
        if spec is None:
            return False
        if spec.asserts_absence_of_effect:
            # A null result is not an efficacy assertion, and demanding
            # efficacy-grade evidence for one would be backwards. Rule V16b governs it.
            return False
        if spec.asserts_effect:
            return True
        if object_type is None or object_type not in self.nodes:
            return False
        ancestors = set(self.ancestors(object_type))
        if ancestors & set(self.effect_asserting_object_types()):
            return True
        return bool(ancestors & set(self.expand_types(spec.effect_asserting_ranges)))

    def negatable_predicates(self) -> tuple[str, ...]:
        """Relations that ``NO_DETECTED_EFFECT_ON`` may negate, sorted."""
        return tuple(sorted(name for name, spec in self.edges.items() if spec.negatable))

    def negatable_union(self) -> tuple[frozenset[str], frozenset[str]]:
        """The union of every negatable relation's domain and range (rule V16b-sym).

        Derived, never listed: a hand-maintained list would drift the first time
        somebody added a relation, and the consequence of drift is an ontology in which
        a positive edge is expressible and its corresponding null is not — which biases
        the graph towards positive findings.
        """
        domain: set[str] = set()
        range_: set[str] = set()
        for name in self.negatable_predicates():
            domain |= set(self.edge_domain(name))
            range_ |= set(self.edge_range(name))
        return frozenset(domain), frozenset(range_)

    def requires_multiple_species(self, predicate: str) -> bool:
        """Whether ``predicate`` states something BETWEEN species (rule V3b)."""
        spec = self.edges.get(predicate)
        return bool(spec and spec.requires_multiple_species)

    def between_species_predicates(self) -> tuple[str, ...]:
        """Relations that state something between species, sorted."""
        return tuple(
            sorted(name for name, spec in self.edges.items() if spec.requires_multiple_species)
        )

    def asserts_absence_of_effect(self, predicate: str) -> bool:
        """Whether ``predicate`` reports a null result (rule V16b, never support)."""
        spec = self.edges.get(predicate)
        return bool(spec and spec.asserts_absence_of_effect)

    def null_result_predicates(self) -> tuple[str, ...]:
        """Relations that report a null result, sorted."""
        return tuple(
            sorted(name for name, spec in self.edges.items() if spec.asserts_absence_of_effect)
        )

    def effect_asserting_ranges(self, predicate: str) -> tuple[str, ...]:
        """Object types for which ``predicate`` is an effect assertion, groups expanded."""
        spec = self.edges.get(predicate)
        return self.expand_types(spec.effect_asserting_ranges) if spec else ()

    def allowed_claim_types(self, predicate: str) -> tuple[str, ...]:
        """``allowed_claim_types`` of ``predicate`` (empty means no claim required)."""
        return self._edge(predicate).allowed_claim_types

    def requires_claim(self, predicate: str) -> bool:
        """Whether ``predicate`` is an empirical relation needing a claim."""
        return self._edge(predicate).requires_claim

    def allowed_provenance_classes(self, predicate: str) -> tuple[str, ...]:
        """Provenance classes ``predicate`` may carry in the compiled graph (V17)."""
        return self._edge(predicate).allowed_provenance_classes

    def semantics(self, predicate: str) -> str:
        """The misuse warning attached to ``predicate``, for error messages."""
        return self._edge(predicate).semantics


def _expand(names: tuple[str, ...], groups: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Expand group names to node type names, for load-time consistency checks."""
    out: list[str] = []
    for name in names:
        for candidate in groups.get(name, (name,)):
            if candidate not in out:
                out.append(candidate)
    return tuple(out)


def _as_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a YAML scalar/sequence/None into a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise OntologyError(f"ontology file not found: {path}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced verbatim
        raise OntologyError(f"{path} is not valid YAML: {exc}") from exc


@lru_cache(maxsize=8)
def load(root: Path | str | None = None) -> Ontology:
    """Load and index the ontology for ``root``, validating its self-consistency.

    Raises :class:`OntologyError` on a duplicate node type, an unknown parent, an
    uncompilable ``id_pattern``, an undeclared prefix, an unknown node type in a
    relation's domain or range, a dangling ``inverse``, or a provenance class outside
    the declared set. A broken ontology must fail loudly: every downstream rule trusts
    this index.
    """
    resolved = paths.resolve_root(root)
    nodes_doc = _load_yaml(paths.nodes_file(resolved))
    edges_doc = _load_yaml(paths.edges_file(resolved))
    primitives_doc = _load_yaml(paths.primitives_file(resolved))
    axioms_doc = _load_yaml(paths.definitional_edges_file(resolved))

    prefixes = _as_tuple(nodes_doc.get("prefixes"))
    layers = _as_tuple(nodes_doc.get("layers"))
    provenance_classes = _as_tuple(edges_doc.get("provenance_classes"))

    nodes: dict[str, NodeType] = {}
    for entry in nodes_doc.get("nodes") or []:
        name = entry["name"]
        if name in nodes:
            raise OntologyError(f"duplicate node type {name!r} in ontology/nodes.yaml")
        node = NodeType(
            name=name,
            layer=entry["layer"],
            description=str(entry.get("description", "")).strip(),
            id_prefixes=_as_tuple(entry.get("id_prefixes")),
            id_pattern=entry["id_pattern"],
            parent=entry.get("parent"),
            required_attributes=_as_tuple(entry.get("required_attributes")),
            optional_attributes=_as_tuple(entry.get("optional_attributes")),
            shared_with_layers=_as_tuple(entry.get("shared_with_layers")),
        )
        for layer in node.layers:
            if layers and layer not in layers:
                raise OntologyError(f"node type {name!r} uses undeclared layer {layer!r}")
        for prefix in node.id_prefixes:
            if prefixes and prefix not in prefixes:
                raise OntologyError(f"node type {name!r} uses undeclared prefix {prefix!r}")
        try:
            re.compile(node.id_pattern)
        except re.error as exc:
            raise OntologyError(f"node type {name!r} has an uncompilable id_pattern: {exc}") from exc
        nodes[name] = node

    for name, node in nodes.items():
        if node.parent is not None and node.parent not in nodes:
            raise OntologyError(f"node type {name!r} has unknown parent {node.parent!r}")

    groups = {
        str(key): _as_tuple(value) for key, value in (edges_doc.get("groups") or {}).items()
    }
    for group, members in groups.items():
        unknown = sorted(m for m in members if m not in nodes)
        if unknown:
            raise OntologyError(f"group {group!r} names unknown node types {unknown}")

    edges: dict[str, EdgeType] = {}
    for entry in edges_doc.get("edges") or []:
        name = entry["name"]
        if name in edges:
            raise OntologyError(f"duplicate relation {name!r} in ontology/edges.yaml")
        edge = EdgeType(
            name=name,
            layers=_as_tuple(entry.get("layers")),
            description=str(entry.get("description", "")).strip(),
            domain=_as_tuple(entry.get("domain")),
            range=_as_tuple(entry.get("range")),
            requires_claim=bool(entry.get("requires_claim", False)),
            allowed_provenance_classes=_as_tuple(entry.get("allowed_provenance_classes")),
            allowed_claim_types=_as_tuple(entry.get("allowed_claim_types")),
            asserts_effect=bool(entry.get("asserts_effect", False)),
            asserts_absence_of_effect=bool(entry.get("asserts_absence_of_effect", False)),
            requires_multiple_species=bool(entry.get("requires_multiple_species", False)),
            negatable=bool(entry.get("negatable", False)),
            effect_asserting_ranges=_as_tuple(entry.get("effect_asserting_ranges")),
            directional=bool(entry.get("directional", True)),
            inverse=entry.get("inverse"),
            semantics=str(entry.get("semantics", "")).strip(),
        )
        unknown_effect_ranges = sorted(
            item for item in edge.effect_asserting_ranges if item not in nodes
        )
        if unknown_effect_ranges:
            raise OntologyError(
                f"relation {name!r} effect_asserting_ranges names unknown node types "
                f"{unknown_effect_ranges}"
            )
        outside_range = sorted(
            item
            for item in edge.effect_asserting_ranges
            if item not in set(_expand(edge.range, groups))
        )
        if outside_range:
            raise OntologyError(
                f"relation {name!r} effect_asserting_ranges {outside_range} are not in "
                "its declared range, so the gate could never fire"
            )
        for side, declared in (("domain", edge.domain), ("range", edge.range)):
            unknown = sorted(
                item
                for item in declared
                if item not in nodes and item not in groups
            )
            if unknown:
                raise OntologyError(
                    f"relation {name!r} {side} names unknown node types/groups {unknown}"
                )
        if not edge.domain or not edge.range:
            raise OntologyError(f"relation {name!r} has an empty domain or range")
        bad_classes = sorted(
            c for c in edge.allowed_provenance_classes if provenance_classes and c not in provenance_classes
        )
        if bad_classes:
            raise OntologyError(
                f"relation {name!r} allows undeclared provenance classes {bad_classes}"
            )
        if edge.requires_claim and not edge.allowed_claim_types:
            raise OntologyError(
                f"relation {name!r} sets requires_claim: true but lists no "
                "allowed_claim_types, which would let any claim type license it"
            )
        edges[name] = edge

    for name, edge in edges.items():
        if edge.inverse is not None and edge.inverse not in edges:
            raise OntologyError(
                f"relation {name!r} names inverse {edge.inverse!r}, which is not a "
                "declared relation. Use null when the inverse is not materialised."
            )

    primitives: dict[str, Primitive] = {}
    for entry in primitives_doc.get("primitives") or []:
        pid = entry["id"]
        if pid in primitives:
            raise OntologyError(f"duplicate primitive {pid!r}")
        primitives[pid] = Primitive(
            id=pid,
            name=entry.get("name", ""),
            definition=str(entry.get("definition", "")).strip(),
            related_state_variables=_as_tuple(entry.get("related_state_variables")),
            human_measurement_paradigms=_as_tuple(entry.get("human_measurement_paradigms")),
            animal_analogue_caveat=str(entry.get("animal_analogue_caveat", "")).strip(),
            definition_status=entry.get("definition_status", ""),
        )

    axioms = tuple(
        DefinitionalEdge(
            subject=entry["subject"],
            predicate=entry["predicate"],
            object=entry["object"],
            provenance_class=entry.get("provenance_class", ""),
            basis=str(entry.get("basis", "")).strip(),
            defined_by=entry.get("defined_by", ""),
        )
        for entry in axioms_doc.get("edges") or []
    )

    prefix_index: dict[str, list[str]] = {}
    for name, node in nodes.items():
        for prefix in node.id_prefixes:
            prefix_index.setdefault(prefix, []).append(name)

    return Ontology(
        root=resolved,
        prefixes=prefixes,
        layers=layers,
        nodes=nodes,
        edges=edges,
        groups=groups,
        primitives=primitives,
        definitional_edges=axioms,
        provenance_classes=provenance_classes,
        _prefix_index={k: tuple(sorted(v)) for k, v in prefix_index.items()},
    )


def is_legal_triple(
    subject_type: str,
    predicate: str,
    object_type: str,
    root: Path | str | None = None,
) -> bool:
    """Module-level convenience wrapper over :meth:`Ontology.is_legal_triple`."""
    return load(root).is_legal_triple(subject_type, predicate, object_type)


def explain_triple(
    subject_type: str,
    predicate: str,
    object_type: str,
    root: Path | str | None = None,
) -> str | None:
    """Module-level convenience wrapper over :meth:`Ontology.explain_triple`."""
    return load(root).explain_triple(subject_type, predicate, object_type)
