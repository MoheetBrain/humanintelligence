"""The three-layer graph compiler.

Compiles the curated records into a NetworkX graph, deterministically. The compiler is
where this sprint's three rulings about *not letting the graph drift positive* are
actually enforced, so they are restated here rather than left in a design document:

1. **`claim_type: evidence_gap` is graph-inert.** It produces an evidence-layer record
   and NO layer-2/3 edge, because an absence of measurement is not a finding about
   biology. Contract V16c.
2. **`NO_DETECTED_EFFECT_ON` edges are marked, not hidden.** They carry
   `is_null_result: true` and `negated_relation`, and they are excluded from every
   support count and from every traversal that means "evidence for". Contract V16b /
   V16b-sym. They are not dropped: a graph in which a positive trial compiles into an
   edge and an equally well-powered null compiles into nothing is biased by
   construction, which is the asymmetry the null relation was created to remove.
3. **Direction is not optional.** A `CONSTRAINS` edge with `direction: no_change` is not
   support. :mod:`blueprint.graph.traversal` refuses to treat a direction-bearing edge
   as positive unless its direction says so.

Every edge carries a `provenance_class`, and `claim_derived` edges carry the claim ids
that licensed them (contract V17). Duplicate source registration across agents collapses
to one node with the registering agents as an attribute (contract §1.3).

Modules:

* :mod:`blueprint.graph.model`     node/edge value types and layer assignment
* :mod:`blueprint.graph.reference` reference-data edges from the identifier index
* :mod:`blueprint.graph.compile`   the compiler itself
* :mod:`blueprint.graph.traversal` null-aware, direction-aware traversal helpers
"""

from __future__ import annotations

from blueprint.graph.compile import CompiledGraph, compile_graph
from blueprint.graph.model import GraphEdgeRecord, GraphNodeRecord

__all__ = ["CompiledGraph", "compile_graph", "GraphEdgeRecord", "GraphNodeRecord"]
