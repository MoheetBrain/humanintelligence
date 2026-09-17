"""Value types for compiled graph nodes and edges.

Design rules:

* **Attributes are sorted and JSON-serialisable.** The compiler's output has to be
  byte-identical across runs, so nothing here carries a set, a dict with unsorted keys
  or an object that renders by memory address.
* **A node is identified by its id alone.** Duplicate registration across agents
  collapses here: two source records for one `source_id` merge into one node whose
  `registered_by` lists both agents (contract §1.3). Deduplication belongs to the
  compiler and the store, never to the registry.
* **An edge carries why it exists.** `provenance_class` is mandatory and
  `claim_derived` edges carry their claim ids (contract V17). `is_null_result` and
  `negated_relation` travel with the edge so no consumer has to re-derive them from the
  relation name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

# Layer names, in the order the README presents them.
LAYERS: tuple[str, ...] = ("evidence", "biological", "intervention")


def _clean(value: Any) -> Any:
    """Coerce a value into a deterministic, JSON-serialisable form."""
    if isinstance(value, dict):
        return {str(k): _clean(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, set):
        return sorted(_clean(item) for item in value)
    return value


@dataclass
class GraphNodeRecord:
    """One node in the compiled graph."""

    id: str
    node_type: str
    layer: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)
    provenance_class: str = "reference_data"
    source_refs: list[str] = field(default_factory=list)

    def merge(self, other: GraphNodeRecord) -> None:
        """Fold another record for the same id into this one.

        Used when two agents register the same source, and when a node is reached both
        as a claim subject and as a claim object. Later attributes do not overwrite
        earlier ones: a node's identity is its id, and the first record to define an
        attribute owns it. Lists union and sort, so the result is order-independent —
        which matters because the compiler must not depend on which agent it read first.
        """
        if other.id != self.id:  # pragma: no cover - programming error
            raise ValueError(f"cannot merge {other.id!r} into {self.id!r}")
        for key, value in other.attributes.items():
            existing = self.attributes.get(key)
            if existing is None:
                self.attributes[key] = value
            elif isinstance(existing, list) and isinstance(value, list):
                self.attributes[key] = sorted({*map(str, existing), *map(str, value)})
        self.source_refs = sorted({*self.source_refs, *other.source_refs})
        if not self.label and other.label:
            self.label = other.label

    def as_dict(self) -> dict[str, Any]:
        """Deterministic mapping for Parquet, JSON and GraphML."""
        return {
            "id": self.id,
            "node_type": self.node_type,
            "layer": self.layer,
            "label": self.label,
            "provenance_class": self.provenance_class,
            "source_refs": sorted(self.source_refs),
            "attributes": _clean(self.attributes),
        }


@dataclass
class GraphEdgeRecord:
    """One edge in the compiled graph.

    ``is_null_result`` is stored rather than derived so that no consumer — a query, an
    exporter, the HTML report — has to know which relation names are null relations in
    order to avoid counting one as support.
    """

    subject: str
    predicate: str
    object: str
    provenance_class: str
    layer: str
    claim_ids: list[str] = field(default_factory=list)
    direction: str | None = None
    direction_context: str | None = None
    negated_relation: str | None = None
    is_null_result: bool = False
    asserts_effect: bool = False
    evidence_count: int = 0
    distinct_source_count: int = 0
    source_ids: list[str] = field(default_factory=list)
    basis: str | None = None
    reference_source: str | None = None
    claim_types: list[str] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str, str]:
        """The identity of an edge: one edge per (subject, predicate, object)."""
        return (self.subject, self.predicate, self.object)

    @property
    def counts_as_support(self) -> bool:
        """Whether this edge may be counted as evidence FOR its object.

        False for a null result, and false for a direction-bearing edge whose direction
        does not assert a change. A `CONSTRAINS` edge with `direction: no_change` is not
        support, and neither is one with `direction: unclear` — the whole point of
        recording direction is that the graph must not read an absent sign as positive.
        """
        if self.is_null_result:
            return False
        if self.direction in {"no_change", "unclear", None}:
            return False
        return bool(self.claim_ids)

    def merge(self, other: GraphEdgeRecord) -> None:
        """Fold another edge with the same key into this one.

        Two claims can license the same triple; the edge then carries both claim ids and
        the union of their evidence. Directions that DISAGREE collapse to ``unclear``
        rather than to whichever was read first — a graph that silently picked one sign
        from two conflicting claims would be asserting something neither claim does.
        """
        if other.key != self.key:  # pragma: no cover - programming error
            raise ValueError(f"cannot merge {other.key} into {self.key}")
        self.claim_ids = sorted({*self.claim_ids, *other.claim_ids})
        self.claim_types = sorted({*self.claim_types, *other.claim_types})
        self.source_ids = sorted({*self.source_ids, *other.source_ids})
        self.evidence_count += other.evidence_count
        self.distinct_source_count = len(self.source_ids)
        self.is_null_result = self.is_null_result or other.is_null_result
        self.asserts_effect = self.asserts_effect or other.asserts_effect
        if self.direction != other.direction:
            if self.direction is None:
                self.direction = other.direction
            elif other.direction is not None:
                self.direction = "unclear"
        if other.direction_context and not self.direction_context:
            self.direction_context = other.direction_context
        if other.negated_relation and not self.negated_relation:
            self.negated_relation = other.negated_relation
        if other.basis and not self.basis:
            self.basis = other.basis
        if other.reference_source and not self.reference_source:
            self.reference_source = other.reference_source

    def as_dict(self) -> dict[str, Any]:
        """Deterministic mapping for Parquet, JSON and GraphML."""
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "provenance_class": self.provenance_class,
            "layer": self.layer,
            "claim_ids": sorted(self.claim_ids),
            "claim_types": sorted(self.claim_types),
            "direction": self.direction,
            "direction_context": self.direction_context,
            "negated_relation": self.negated_relation,
            "is_null_result": self.is_null_result,
            "asserts_effect": self.asserts_effect,
            "counts_as_support": self.counts_as_support,
            "evidence_count": self.evidence_count,
            "distinct_source_count": self.distinct_source_count,
            "source_ids": sorted(self.source_ids),
            "basis": self.basis,
            "reference_source": self.reference_source,
        }


def sort_nodes(nodes: Iterable[GraphNodeRecord]) -> list[GraphNodeRecord]:
    """Nodes in a stable order: layer, then type, then id."""
    order = {name: index for index, name in enumerate(LAYERS)}
    return sorted(nodes, key=lambda n: (order.get(n.layer, 99), n.node_type, n.id))


def sort_edges(edges: Iterable[GraphEdgeRecord]) -> list[GraphEdgeRecord]:
    """Edges in a stable order: subject, predicate, object."""
    return sorted(edges, key=lambda e: e.key)
