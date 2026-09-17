"""Traversal helpers that cannot accidentally read an absent sign as support.

Why this module exists
----------------------
The obvious way to ask "what is the evidence for X" is to walk the incoming edges and
count them. Done naively that counts a `NO_DETECTED_EFFECT_ON` edge as evidence FOR the
thing it found no effect on, and counts a `CONSTRAINS` edge with `direction: no_change`
as if it asserted a change. Both mistakes are easy, silent, and undo the work this
sprint spent making nulls first-class.

So the helpers here are the supported way to traverse, and the unsupported way is
spelled out too: :func:`support_edges` excludes null results and direction-free edges,
:func:`null_result_edges` returns them separately so a consumer can show them, and
:func:`evidence_summary` returns both counts side by side because a support count
presented alone is misleading.

Nothing here scores anything. Counting edges is not evidence quality (contract P5), and
these functions return counts and edge lists, never a ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from blueprint.graph.model import GraphEdgeRecord

# Direction values that assert a change. Everything else — `no_change`, `unclear`,
# `bidirectional` and an absent direction — does not, and must not be counted as
# support for the object.
ASSERTING_DIRECTIONS: frozenset[str] = frozenset(
    {"increases", "decreases", "inverted_u", "u_shaped", "state_dependent"}
)


@dataclass(frozen=True)
class EvidenceSummary:
    """Support and non-support counts for one node, reported together.

    Presented together on purpose: a support count on its own invites the reader to
    treat a well-connected node as a well-evidenced one, and this project's whole
    position is that those are different properties.
    """

    node_id: str
    support_edge_count: int
    null_result_count: int
    contradicting_count: int
    direction_free_count: int
    effect_asserting_count: int
    distinct_source_count: int
    claim_count: int

    @property
    def has_only_null_or_direction_free_evidence(self) -> bool:
        """True when nothing incoming actually asserts a change.

        The state a reader most needs flagged: edges exist, so the node looks connected,
        but not one of them says anything changed.
        """
        return self.support_edge_count == 0 and (
            self.null_result_count > 0 or self.direction_free_count > 0
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "support_edge_count": self.support_edge_count,
            "null_result_count": self.null_result_count,
            "contradicting_count": self.contradicting_count,
            "direction_free_count": self.direction_free_count,
            "effect_asserting_count": self.effect_asserting_count,
            "distinct_source_count": self.distinct_source_count,
            "claim_count": self.claim_count,
            "has_only_null_or_direction_free_evidence": (
                self.has_only_null_or_direction_free_evidence
            ),
        }


def asserts_a_change(edge: GraphEdgeRecord) -> bool:
    """Whether ``edge`` asserts that something changed.

    An edge with no direction at all is treated as NOT asserting a change. That is the
    conservative reading and it is the right one: a relation that can carry a direction
    and does not is a claim whose sign the curator declined to state.
    """
    if edge.is_null_result:
        return False
    if edge.direction is None:
        return False
    return edge.direction in ASSERTING_DIRECTIONS


def support_edges(edges: Iterable[GraphEdgeRecord]) -> list[GraphEdgeRecord]:
    """Edges that may be counted as evidence FOR their object.

    Excludes null results, edges with no asserting direction, and edges with no claim
    behind them (an axiom or a reference-data edge is structure, not evidence).
    """
    return [
        edge
        for edge in edges
        if edge.claim_ids and asserts_a_change(edge) and not edge.is_null_result
    ]


def null_result_edges(edges: Iterable[GraphEdgeRecord]) -> list[GraphEdgeRecord]:
    """Edges reporting a performed attempt that detected no effect.

    Returned separately rather than filtered away, because a null is a finding: the
    point of the relation is that a well-powered null should be as visible as a positive.
    """
    return [edge for edge in edges if edge.is_null_result]


def direction_free_edges(edges: Iterable[GraphEdgeRecord]) -> list[GraphEdgeRecord]:
    """Claim-derived edges whose direction does not assert a change."""
    return [
        edge
        for edge in edges
        if edge.claim_ids and not edge.is_null_result and not asserts_a_change(edge)
    ]


def incoming(edges: Iterable[GraphEdgeRecord], node_id: str) -> list[GraphEdgeRecord]:
    """Edges whose object is ``node_id``."""
    return [edge for edge in edges if edge.object == node_id]


def outgoing(edges: Iterable[GraphEdgeRecord], node_id: str) -> list[GraphEdgeRecord]:
    """Edges whose subject is ``node_id``."""
    return [edge for edge in edges if edge.subject == node_id]


def evidence_summary(edges: Iterable[GraphEdgeRecord], node_id: str) -> EvidenceSummary:
    """Summarise what the incoming edges of ``node_id`` actually say."""
    into = incoming(edges, node_id)
    supports = support_edges(into)
    nulls = null_result_edges(into)
    direction_free = direction_free_edges(into)
    claims: set[str] = set()
    sources: set[str] = set()
    for edge in into:
        claims.update(edge.claim_ids)
        sources.update(edge.source_ids)
    return EvidenceSummary(
        node_id=node_id,
        support_edge_count=len(supports),
        null_result_count=len(nulls),
        contradicting_count=sum(1 for e in into if e.predicate == "CONTRADICTS"),
        direction_free_count=len(direction_free),
        effect_asserting_count=sum(1 for e in into if e.asserts_effect),
        distinct_source_count=len(sources),
        claim_count=len(claims),
    )


def supported_paths(
    edges: Iterable[GraphEdgeRecord],
    start: str,
    end: str,
    *,
    max_depth: int = 6,
) -> list[list[GraphEdgeRecord]]:
    """Every path from ``start`` to ``end`` along SUPPORT edges only.

    "Evidence for" traversal, so null results and direction-free edges are not walked.
    A path returned here is a chain in which every link asserts a change; a chain
    containing a null or an unsigned link is not that, and returning it would be exactly
    the drift the null relation exists to prevent.

    Paths are returned shortest-first and are capped by ``max_depth``: the causal chain
    is eleven levels deep, so an uncapped search over a dense region is unbounded work
    for no benefit.
    """
    usable = support_edges(edges)
    by_subject: dict[str, list[GraphEdgeRecord]] = {}
    for edge in usable:
        by_subject.setdefault(edge.subject, []).append(edge)
    for bucket in by_subject.values():
        bucket.sort(key=lambda e: e.key)

    found: list[list[GraphEdgeRecord]] = []
    # Breadth-first so shorter chains come out first, with the visited set held per path
    # rather than globally: two different chains may legitimately share a node.
    queue: list[tuple[str, list[GraphEdgeRecord], frozenset[str]]] = [
        (start, [], frozenset({start}))
    ]
    while queue:
        node, path, seen = queue.pop(0)
        if len(path) >= max_depth:
            continue
        for edge in by_subject.get(node, []):
            if edge.object in seen:
                continue
            extended = [*path, edge]
            if edge.object == end:
                found.append(extended)
                continue
            queue.append((edge.object, extended, seen | {edge.object}))
    return found


def why_not_supported(edge: GraphEdgeRecord) -> str | None:
    """Explain, in one sentence, why an edge is not counted as support.

    Returns ``None`` when the edge IS support. Exists so a report or a query can tell a
    reader why an edge they can see is not being counted, rather than leaving them to
    infer that it was overlooked.
    """
    if edge.is_null_result:
        return (
            f"{edge.predicate} reports a performed attempt that detected no effect"
            + (f" (negating {edge.negated_relation})" if edge.negated_relation else "")
            + ". A null is a finding, but it is not evidence FOR the object."
        )
    if not edge.claim_ids:
        return (
            f"a {edge.provenance_class} edge is structure, not evidence: it carries no "
            "claim, so there is nothing to count."
        )
    if edge.direction is None:
        return "the claim states no direction, so it does not assert that anything changed."
    if edge.direction not in ASSERTING_DIRECTIONS:
        return (
            f"direction is {edge.direction!r}, which does not assert a change. "
            "`no_change` and `unclear` must never read as positive."
        )
    return None
