"""Pathway convergence and state-variable centrality over the compiled graph.

Graph interface this module is written against
---------------------------------------------
``agent:ontology`` owns the real graph compiler (Phase 2, ``graph/build_graph.py``).
Until it lands, this module is written against a documented, minimal contract and
tested on a synthetic graph, so it will run against the real one without change:

* The graph is a :class:`networkx.DiGraph` (a ``MultiDiGraph`` also works — parallel
  edges are collapsed when counting distinct targets, because two claims asserting
  the same relation are one relation, per contract P5).
* Every node carries ``node_type``, a type name from ``ontology/nodes.yaml``
  (``Target``, ``Gene``, ``Protein``, ``StateVariable``, ``ComputationalPrimitive``,
  ``CognitivePhenotype``, ...). A node without ``node_type`` is skipped and counted
  as unusable rather than guessed at.
* Every edge carries ``relation``, a relation name from ``ontology/edges.yaml``
  (``MODULATES``, ``POSITIVELY_REGULATES``, ``NEGATIVELY_REGULATES``, ``CONSTRAINS``,
  ``CHANGES_STATE``, ``IMPLEMENTS``, ``SUPPORTS_PRIMITIVE``, ``TARGETS``, ...), and
  may carry ``provenance_class`` (contract V17).

Convergence is direction-blind, on purpose
------------------------------------------
Safety and stability state variables declare a ``polarity`` in
``state_model/{safety,stability}.yaml``: ``risk`` (higher is more harm) or ``margin``
(higher is more headroom). The two point opposite ways, so a directional reading of
such a variable must consult the declaration. Every function in this module counts
structure — how many distinct targets reach a node, how central it is — and never reads
a sign, which is why it is safe over safety variables. :func:`state_variable_polarity`
exists so that any future directional function reads the declaration instead of
guessing from a variable's name.

What convergence means here
---------------------------
Convergence counts **distinct targets that reach a state variable or computational
primitive by a directed path**. It is a structural statement about the curated
graph, not evidence: if five targets converge on one state variable, that is a fact
about what has been written down, and it may reflect curation attention rather than
biology. Every function here returns provenance-bearing counts so a reader can tell
the two apart — ``n_claim_derived_paths`` distinguishes convergence supported by
claims from convergence supplied by reference data or ontology axioms.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

__all__ = [
    "ConvergenceRow",
    "STATE_VARIABLE_POLARITIES",
    "DEFAULT_SINK_TYPES",
    "DEFAULT_SOURCE_TYPES",
    "convergence_table",
    "state_variable_centrality",
    "state_variable_convergence",
    "state_variable_polarity",
]

#: Node types treated as convergence *sources* (the things being compared).
DEFAULT_SOURCE_TYPES: tuple[str, ...] = ("Target",)

#: Node types treated as convergence *sinks* (the things converged upon).
DEFAULT_SINK_TYPES: tuple[str, ...] = ("StateVariable", "ComputationalPrimitive")

#: Default maximum directed path length from a source to a sink. Bounded because an
#: unbounded reachability count over a dense causal graph converges on "everything
#: reaches everything", which is not a finding.
DEFAULT_MAX_DEPTH = 6


@dataclass(frozen=True, slots=True)
class ConvergenceRow:
    """Convergence and centrality for one sink node."""

    node: str
    node_type: str
    n_converging_targets: int
    converging_targets: tuple[str, ...]
    n_claim_derived_paths: int
    in_degree: int
    out_degree: int
    degree: int
    betweenness: float
    shortest_path_lengths: Mapping[str, int] = field(default_factory=dict)

    def as_row(self) -> dict[str, object]:
        """A flat, JSON-ready dictionary for reports."""
        return {
            "node": self.node,
            "node_type": self.node_type,
            "n_converging_targets": self.n_converging_targets,
            "converging_targets": list(self.converging_targets),
            "n_claim_derived_paths": self.n_claim_derived_paths,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "degree": self.degree,
            "betweenness": round(self.betweenness, 6),
        }


def _nodes_of_type(graph, types: Sequence[str]) -> tuple[str, ...]:
    """Nodes whose ``node_type`` is in ``types``, sorted for determinism."""
    wanted = set(types)
    return tuple(
        sorted(node for node, data in graph.nodes(data=True) if data.get("node_type") in wanted)
    )


def state_variable_convergence(
    graph,
    *,
    source_types: Sequence[str] = DEFAULT_SOURCE_TYPES,
    sink_types: Sequence[str] = DEFAULT_SINK_TYPES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    relations: Iterable[str] | None = None,
) -> dict[str, dict[str, object]]:
    """Count distinct source nodes that reach each sink node.

    Args:
        graph: A NetworkX directed graph following the interface above.
        source_types: Node types to count as converging entities.
        sink_types: Node types to count convergence onto.
        max_depth: Maximum directed path length considered.
        relations: If given, only traverse edges whose ``relation`` is in this set.
            Use it to restrict convergence to, say, regulatory relations only.

    Returns:
        ``{sink_node: {"node_type", "converging_targets", "n_converging_targets",
        "n_claim_derived_paths", "shortest_path_lengths"}}``. Sinks with no
        converging source are included with a count of zero, so absence of
        convergence is visible rather than missing.
    """
    import networkx as nx  # noqa: PLC0415

    allowed = set(relations) if relations is not None else None
    sinks = _nodes_of_type(graph, sink_types)
    sources = _nodes_of_type(graph, source_types)

    working = _relation_filtered_view(graph, allowed) if allowed is not None else graph

    result: dict[str, dict[str, object]] = {
        sink: {
            "node_type": graph.nodes[sink].get("node_type", ""),
            "converging_targets": [],
            "n_converging_targets": 0,
            "n_claim_derived_paths": 0,
            "shortest_path_lengths": {},
        }
        for sink in sinks
    }

    sink_set = set(sinks)
    for source in sources:
        if source not in working:
            continue
        lengths = nx.single_source_shortest_path_length(working, source, cutoff=max_depth)
        for node, distance in lengths.items():
            if node in sink_set and node != source:
                entry = result[node]
                entry["converging_targets"].append(source)  # type: ignore[union-attr]
                entry["shortest_path_lengths"][source] = int(distance)  # type: ignore[index]

    for sink, entry in result.items():
        targets = sorted(set(entry["converging_targets"]))  # type: ignore[arg-type]
        entry["converging_targets"] = tuple(targets)
        entry["n_converging_targets"] = len(targets)
        entry["n_claim_derived_paths"] = _count_claim_derived_in_edges(graph, sink, allowed)
    return result


def _relation_filtered_view(graph, allowed: set[str]):
    """A subgraph view restricted to edges whose ``relation`` is allowed."""

    def keep_edge(*edge) -> bool:
        data = graph.get_edge_data(*edge)
        if data is None:
            return False
        # MultiDiGraph passes a key; DiGraph does not.
        if "relation" in data:
            return data.get("relation") in allowed
        return any(sub.get("relation") in allowed for sub in data.values())

    import networkx as nx  # noqa: PLC0415

    return nx.subgraph_view(graph, filter_edge=keep_edge)


def _count_claim_derived_in_edges(graph, node: str, allowed: set[str] | None) -> int:
    """How many incoming edges of ``node`` are ``provenance_class: claim_derived``.

    Contract V17 requires every compiled edge to declare a provenance class. This
    count is what separates "five targets converge here because five claims say so"
    from "five targets converge here because an identifier database says so".
    """
    count = 0
    for _, _, data in graph.in_edges(node, data=True):
        if allowed is not None and data.get("relation") not in allowed:
            continue
        if data.get("provenance_class") == "claim_derived":
            count += 1
    return count


def state_variable_centrality(
    graph,
    *,
    sink_types: Sequence[str] = DEFAULT_SINK_TYPES,
    normalized: bool = True,
) -> dict[str, dict[str, float]]:
    """Degree and betweenness centrality for the sink nodes.

    Args:
        graph: A NetworkX directed graph following the interface above.
        sink_types: Node types to report centrality for.
        normalized: Pass through to NetworkX betweenness normalisation.

    Returns:
        ``{node: {"in_degree", "out_degree", "degree", "betweenness"}}``.

    Betweenness is computed over the **whole** graph and then filtered, because a
    state variable's brokerage position depends on paths through nodes of every
    type; computing it on the induced subgraph would answer a different question.
    Betweenness here says "how many curated causal paths pass through this state
    variable", which is a property of the curation as much as of the biology.
    """
    import networkx as nx  # noqa: PLC0415

    betweenness = nx.betweenness_centrality(graph, normalized=normalized)
    output: dict[str, dict[str, float]] = {}
    for node in _nodes_of_type(graph, sink_types):
        output[node] = {
            "in_degree": float(graph.in_degree(node)),
            "out_degree": float(graph.out_degree(node)),
            "degree": float(graph.in_degree(node) + graph.out_degree(node)),
            "betweenness": float(betweenness.get(node, 0.0)),
        }
    return output


def convergence_table(
    graph,
    *,
    source_types: Sequence[str] = DEFAULT_SOURCE_TYPES,
    sink_types: Sequence[str] = DEFAULT_SINK_TYPES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    relations: Iterable[str] | None = None,
    min_converging_targets: int = 1,
) -> tuple[ConvergenceRow, ...]:
    """Convergence plus centrality per sink node, sorted for reporting.

    Args:
        graph: A NetworkX directed graph following the interface above.
        source_types: Node types counted as converging entities.
        sink_types: Node types counted as convergence points.
        max_depth: Maximum directed path length considered.
        relations: Optional restriction on edge ``relation`` values.
        min_converging_targets: Drop sinks below this count. Defaults to 1 so that
            unconverged state variables are excluded from the table but are still
            available from :func:`state_variable_convergence`.

    Returns:
        Rows sorted by descending convergence count, then descending betweenness,
        then node id — deterministic, so the table diffs cleanly between runs.
    """
    convergence = state_variable_convergence(
        graph,
        source_types=source_types,
        sink_types=sink_types,
        max_depth=max_depth,
        relations=relations,
    )
    centrality = state_variable_centrality(graph, sink_types=sink_types)

    rows = [
        ConvergenceRow(
            node=node,
            node_type=str(entry["node_type"]),
            n_converging_targets=int(entry["n_converging_targets"]),
            converging_targets=tuple(entry["converging_targets"]),  # type: ignore[arg-type]
            n_claim_derived_paths=int(entry["n_claim_derived_paths"]),
            in_degree=int(centrality.get(node, {}).get("in_degree", 0.0)),
            out_degree=int(centrality.get(node, {}).get("out_degree", 0.0)),
            degree=int(centrality.get(node, {}).get("degree", 0.0)),
            betweenness=float(centrality.get(node, {}).get("betweenness", 0.0)),
            shortest_path_lengths=dict(entry["shortest_path_lengths"]),  # type: ignore[arg-type]
        )
        for node, entry in convergence.items()
        if int(entry["n_converging_targets"]) >= min_converging_targets
    ]
    rows.sort(key=lambda r: (-r.n_converging_targets, -r.betweenness, r.node))
    return tuple(rows)


# ---------------------------------------------------------------------------
# State-variable polarity (state_model/{safety,stability}.yaml)
# ---------------------------------------------------------------------------

#: Declared polarities for safety and stability state variables.
#:
#: ``risk``   — higher is more harm.
#: ``margin`` — higher is more headroom before harm.
#:
#: The two point in OPPOSITE directions, so any directional reading of a safety
#: variable must consult the declaration rather than assume one. This module's
#: convergence and centrality functions are deliberately DIRECTION-BLIND: they count
#: how many distinct targets reach a node and how central it is, which are statements
#: about the shape of the curated graph and carry no sign. That is why they are safe to
#: run over safety variables without knowing the polarity — and why any future function
#: here that does read a direction must go through :func:`state_variable_polarity`
#: instead of guessing from the variable's name.
STATE_VARIABLE_POLARITIES: tuple[str, ...] = ("risk", "margin")


def state_variable_polarity(
    state_variable_id: str,
    state_model_root: str | None = None,
) -> str | None:
    """The declared polarity of a state variable, or ``None`` when it declares none.

    Args:
        state_variable_id: A ``SV:{domain}.{name}`` identifier.
        state_model_root: Directory holding ``state_model/{domain}.yaml``. Defaults to
            the repository's.

    Returns:
        ``"risk"``, ``"margin"``, or ``None`` for a variable outside the safety and
        stability domains (which do not declare a polarity).

    Raises:
        ValueError: If the identifier is not a well-formed ``SV:`` id, or the declared
            polarity is not one this module recognises. Guessing a safety variable's
            direction is exactly the error that turns a margin into a risk.
    """
    from pathlib import Path  # noqa: PLC0415

    import yaml  # noqa: PLC0415

    if not state_variable_id.startswith("SV:") or "." not in state_variable_id:
        raise ValueError(f"not a state-variable id: {state_variable_id!r}")
    domain = state_variable_id.removeprefix("SV:").split(".", 1)[0]
    root = Path(state_model_root) if state_model_root else Path(__file__).resolve().parents[3] / "state_model"
    path = root / f"{domain}.yaml"
    if not path.is_file():
        return None
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for entry in document.get("variables") or document.get("state_variables") or []:
        if not isinstance(entry, Mapping) or entry.get("id") != state_variable_id:
            continue
        polarity = entry.get("polarity")
        if polarity is None:
            return None
        if str(polarity) not in STATE_VARIABLE_POLARITIES:
            raise ValueError(
                f"{state_variable_id} declares polarity {polarity!r}; expected one of "
                f"{STATE_VARIABLE_POLARITIES}. A safety variable whose direction cannot be "
                "read must not be read directionally at all."
            )
        return str(polarity)
    return None
