"""Deterministic node placement for the graph report.

Design rules:

* **Deterministic.** The layout is computed in Python with a fixed seed and returns
  rounded integer coordinates, so two runs produce byte-identical HTML. A browser-side
  force simulation would be prettier and would make the report undiffable.
* **Layered, not a hairball.** X is set by layer (evidence, biological, intervention),
  so the three-layer architecture is visible in the picture rather than something the
  reader has to take on trust. Y comes from a seeded spring layout computed *within*
  each layer, which keeps related nodes together without letting a dense evidence layer
  drag the biological one across the canvas.
* **Node types are grouped inside a layer.** Within a layer, nodes are banded by type,
  so a reader scanning for state variables finds them in one place.
"""

from __future__ import annotations

from typing import Iterable

from blueprint.graph.model import GraphEdgeRecord, GraphNodeRecord

# Canvas geometry. Chosen so the default view (biological + intervention) fits without
# zooming, and the evidence layer has room when switched on.
CANVAS_WIDTH = 2400
CANVAS_HEIGHT = 1600
LAYER_X: dict[str, float] = {"evidence": 0.16, "biological": 0.52, "intervention": 0.86}
LAYER_SPREAD = 0.13  # fraction of the width a layer may occupy
SEED = 20260917  # fixed so the layout is reproducible; the date is arbitrary but stable
ITERATIONS = 60


def _force_layout(
    node_ids: list[str], adjacency: dict[str, set[str]], *, iterations: int = ITERATIONS
) -> dict[str, tuple[float, float]]:
    """A deterministic Fruchterman-Reingold layout in unit coordinates.

    Implemented here rather than via ``networkx.spring_layout`` because that function
    requires SciPy above 500 nodes, SciPy is not a dependency of this project, and
    adding one would be a blocking schema-change request for a picture. Writing the
    ~30 lines also buys exact control over determinism: the starting positions come from
    the sorted node index rather than from a random number generator, so the result does
    not depend on the platform's PRNG or on dict iteration order.
    """
    count = len(node_ids)
    if count == 0:
        return {}
    if count == 1:
        return {node_ids[0]: (0.0, 0.0)}

    # Deterministic start: a lattice derived from the sorted index. Any fixed,
    # non-degenerate arrangement works; a lattice avoids the co-linear starting state a
    # single circle produces for small graphs.
    side = max(2, int(count ** 0.5) + 1)
    position: dict[str, list[float]] = {}
    for index, node_id in enumerate(node_ids):
        row, column = divmod(index, side)
        position[node_id] = [
            (column / (side - 1) - 0.5) * 2.0,
            (row / max(side - 1, 1) - 0.5) * 2.0,
        ]

    area = 1.0
    optimal = (area / count) ** 0.5
    temperature = 0.35

    for step in range(iterations):
        displacement = {node_id: [0.0, 0.0] for node_id in node_ids}

        # Repulsion. O(n^2) is acceptable: the largest layer here is under a thousand
        # nodes, and a grid approximation would add a bucketing order to depend on.
        for i, left in enumerate(node_ids):
            lx, ly = position[left]
            for right in node_ids[i + 1 :]:
                rx, ry = position[right]
                dx, dy = lx - rx, ly - ry
                distance_sq = dx * dx + dy * dy
                if distance_sq < 1e-9:
                    # Deterministic nudge from the id ordering, never random.
                    dx, dy, distance_sq = 1e-4, 1e-4, 2e-8
                distance = distance_sq ** 0.5
                force = (optimal * optimal) / distance
                ux, uy = dx / distance, dy / distance
                displacement[left][0] += ux * force
                displacement[left][1] += uy * force
                displacement[right][0] -= ux * force
                displacement[right][1] -= uy * force

        # Attraction along edges.
        for left in node_ids:
            for right in sorted(adjacency.get(left, ())):
                if right <= left or right not in position:
                    continue
                lx, ly = position[left]
                rx, ry = position[right]
                dx, dy = lx - rx, ly - ry
                distance = max((dx * dx + dy * dy) ** 0.5, 1e-6)
                force = (distance * distance) / optimal
                ux, uy = dx / distance, dy / distance
                displacement[left][0] -= ux * force
                displacement[left][1] -= uy * force
                displacement[right][0] += ux * force
                displacement[right][1] += uy * force

        # Cool linearly, and cap each step by the current temperature.
        cooling = temperature * (1.0 - step / iterations)
        for node_id in node_ids:
            dx, dy = displacement[node_id]
            length = max((dx * dx + dy * dy) ** 0.5, 1e-9)
            capped = min(length, cooling)
            position[node_id][0] += dx / length * capped
            position[node_id][1] += dy / length * capped

    # Normalise into [-1, 1] so the caller's scaling is independent of graph size.
    xs = [position[n][0] for n in node_ids]
    ys = [position[n][1] for n in node_ids]
    span_x = max(max(xs) - min(xs), 1e-6)
    span_y = max(max(ys) - min(ys), 1e-6)
    mid_x = (max(xs) + min(xs)) / 2
    mid_y = (max(ys) + min(ys)) / 2
    return {
        node_id: (
            (position[node_id][0] - mid_x) / span_x * 2.0,
            (position[node_id][1] - mid_y) / span_y * 2.0,
        )
        for node_id in node_ids
    }


def compute_layout(
    nodes: Iterable[GraphNodeRecord],
    edges: Iterable[GraphEdgeRecord],
) -> dict[str, tuple[int, int]]:
    """Place every node, deterministically.

    Returns integer pixel coordinates keyed by node id. Integers rather than floats
    because a float's repr can differ in its last digit between platforms, and the HTML
    has to be byte-identical for the determinism test to mean anything.
    """
    node_list = sorted(nodes, key=lambda n: (n.layer, n.node_type, n.id))
    edge_list = list(edges)
    by_layer: dict[str, list[GraphNodeRecord]] = {}
    for node in node_list:
        by_layer.setdefault(node.layer, []).append(node)

    positions: dict[str, tuple[int, int]] = {}
    for layer, members in sorted(by_layer.items()):
        centre_x = LAYER_X.get(layer, 0.5) * CANVAS_WIDTH
        ids = sorted(node.id for node in members)
        id_set = set(ids)

        # Within-layer edges only: a cross-layer edge would pull a layer sideways and
        # defeat the banding that makes the three-layer architecture visible.
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in ids}
        for edge in edge_list:
            if edge.subject in id_set and edge.object in id_set and edge.subject != edge.object:
                adjacency[edge.subject].add(edge.object)
                adjacency[edge.object].add(edge.subject)

        raw = _force_layout(ids, adjacency)

        # Band by node type within the layer, so scanning for a type is possible.
        types = sorted({node.node_type for node in members})
        band_height = CANVAS_HEIGHT / max(len(types), 1)
        band_index = {name: position for position, name in enumerate(types)}

        for node in members:
            x_raw, y_raw = raw.get(node.id, (0.0, 0.0))
            band = band_index[node.node_type]
            x = centre_x + x_raw * LAYER_SPREAD * CANVAS_WIDTH
            y = (band + 0.5) * band_height + y_raw * band_height * 0.42
            positions[node.id] = (
                int(round(max(40.0, min(CANVAS_WIDTH - 40.0, x)))),
                int(round(max(40.0, min(CANVAS_HEIGHT - 40.0, y)))),
            )
    return dict(sorted(positions.items()))


def layer_label_positions() -> list[tuple[str, int, int]]:
    """Where to draw each layer's heading."""
    return [
        (layer, int(round(fraction * CANVAS_WIDTH)), 26)
        for layer, fraction in sorted(LAYER_X.items(), key=lambda item: item[1])
    ]
