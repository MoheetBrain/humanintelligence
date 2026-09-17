"""Convergence and centrality over a synthetic graph.

``agent:ontology`` owns the real graph compiler (Phase 2). These tests build the
graph by hand against the documented interface — node attribute ``node_type``, edge
attribute ``relation``, optional ``provenance_class`` — so the module is verified
before the compiler exists and will keep working when it arrives.

The graph used throughout::

    TGT:ALPHA --TARGETS--> PROT:X --NEGATIVELY_REGULATES--> SV:plasticity.ltp_threshold
    TGT:BETA  --MODULATES------------------------------->  SV:plasticity.ltp_threshold
    TGT:GAMMA --MODULATES------------------------------->  SV:workspace.capacity
    SV:plasticity.ltp_threshold --IMPLEMENTS--> PRIM:pattern_separation
    SV:orphan.unreached  (no edges at all)

So ALPHA and BETA converge on the LTP threshold (two distinct targets, by paths of
length 2 and 1), GAMMA converges alone on workspace capacity, and the primitive
inherits ALPHA and BETA at one hop further out.
"""

from __future__ import annotations

import networkx as nx
import pytest

from blueprint.ranking.convergence import (
    convergence_table,
    state_variable_centrality,
    state_variable_convergence,
)

LTP = "SV:plasticity.ltp_threshold"
CAPACITY = "SV:workspace.capacity"
PRIMITIVE = "PRIM:pattern_separation"
ORPHAN = "SV:stability.orphan_variable"


@pytest.fixture
def graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("TGT:ALPHA", node_type="Target")
    g.add_node("TGT:BETA", node_type="Target")
    g.add_node("TGT:GAMMA", node_type="Target")
    g.add_node("PROT:X", node_type="Protein")
    g.add_node(LTP, node_type="StateVariable")
    g.add_node(CAPACITY, node_type="StateVariable")
    g.add_node(PRIMITIVE, node_type="ComputationalPrimitive")
    g.add_node(ORPHAN, node_type="StateVariable")

    g.add_edge("TGT:ALPHA", "PROT:X", relation="TARGETS", provenance_class="claim_derived")
    g.add_edge("PROT:X", LTP, relation="NEGATIVELY_REGULATES", provenance_class="claim_derived")
    g.add_edge("TGT:BETA", LTP, relation="MODULATES", provenance_class="claim_derived")
    g.add_edge("TGT:GAMMA", CAPACITY, relation="MODULATES", provenance_class="reference_data")
    g.add_edge(LTP, PRIMITIVE, relation="IMPLEMENTS", provenance_class="ontology_axiom")
    return g


# ---------------------------------------------------------------------------
# Convergence
# ---------------------------------------------------------------------------


def test_counts_distinct_targets_reaching_each_state_variable(graph) -> None:
    convergence = state_variable_convergence(graph)
    assert convergence[LTP]["n_converging_targets"] == 2
    assert convergence[LTP]["converging_targets"] == ("TGT:ALPHA", "TGT:BETA")
    assert convergence[CAPACITY]["n_converging_targets"] == 1


def test_convergence_follows_multi_hop_paths(graph) -> None:
    """ALPHA reaches the LTP threshold through a protein, not directly. Counting only
    direct edges would understate convergence and miss the shared mechanism."""
    convergence = state_variable_convergence(graph)
    assert convergence[LTP]["shortest_path_lengths"] == {"TGT:ALPHA": 2, "TGT:BETA": 1}


def test_computational_primitives_are_convergence_sinks_too(graph) -> None:
    convergence = state_variable_convergence(graph)
    assert convergence[PRIMITIVE]["n_converging_targets"] == 2
    assert convergence[PRIMITIVE]["shortest_path_lengths"]["TGT:ALPHA"] == 3


def test_unconverged_sinks_are_reported_with_zero_not_omitted(graph) -> None:
    """Absence of convergence is a result. Omitting the node would make a curation
    gap invisible."""
    convergence = state_variable_convergence(graph)
    assert ORPHAN in convergence
    assert convergence[ORPHAN]["n_converging_targets"] == 0
    assert convergence[ORPHAN]["converging_targets"] == ()


def test_max_depth_bounds_the_reachability_count(graph) -> None:
    """With a cutoff of 1, only the directly-connected target counts."""
    shallow = state_variable_convergence(graph, max_depth=1)
    assert shallow[LTP]["converging_targets"] == ("TGT:BETA",)
    assert shallow[PRIMITIVE]["n_converging_targets"] == 0


def test_relations_filter_restricts_traversal(graph) -> None:
    """Restricting to MODULATES drops the ALPHA -> PROT:X -> LTP route entirely."""
    filtered = state_variable_convergence(graph, relations={"MODULATES"})
    assert filtered[LTP]["converging_targets"] == ("TGT:BETA",)
    assert filtered[CAPACITY]["converging_targets"] == ("TGT:GAMMA",)


def test_claim_derived_paths_are_counted_separately(graph) -> None:
    """Contract V17: an edge declares its provenance class. Convergence supported by
    claims is a different statement from convergence supplied by reference data, and
    the table must let a reader tell them apart."""
    convergence = state_variable_convergence(graph)
    assert convergence[LTP]["n_claim_derived_paths"] == 2
    assert convergence[CAPACITY]["n_claim_derived_paths"] == 0  # reference_data only
    assert convergence[PRIMITIVE]["n_claim_derived_paths"] == 0  # ontology_axiom only


def test_a_node_without_a_node_type_is_skipped_not_guessed(graph) -> None:
    graph.add_node("MYSTERY:1")
    graph.add_edge("MYSTERY:1", LTP, relation="MODULATES")
    convergence = state_variable_convergence(graph)
    assert "MYSTERY:1" not in convergence[LTP]["converging_targets"]
    assert "MYSTERY:1" not in convergence


def test_source_and_sink_types_are_configurable(graph) -> None:
    """Convergence of Proteins onto state variables, rather than Targets."""
    convergence = state_variable_convergence(graph, source_types=("Protein",))
    assert convergence[LTP]["converging_targets"] == ("PROT:X",)


# ---------------------------------------------------------------------------
# Centrality
# ---------------------------------------------------------------------------


def test_degrees_are_reported_for_state_variable_nodes(graph) -> None:
    centrality = state_variable_centrality(graph)
    assert centrality[LTP]["in_degree"] == 2
    assert centrality[LTP]["out_degree"] == 1
    assert centrality[LTP]["degree"] == 3
    assert centrality[ORPHAN]["degree"] == 0


def test_betweenness_is_positive_for_a_brokering_state_variable(graph) -> None:
    """The LTP threshold lies on every path from ALPHA/BETA to the primitive, so it
    brokers. The orphan brokers nothing."""
    centrality = state_variable_centrality(graph)
    assert centrality[LTP]["betweenness"] > 0.0
    assert centrality[ORPHAN]["betweenness"] == pytest.approx(0.0)
    assert centrality[CAPACITY]["betweenness"] == pytest.approx(0.0)


def test_betweenness_is_computed_over_the_whole_graph(graph) -> None:
    """Not over the induced subgraph of state variables: brokerage depends on paths
    through nodes of every type, and the induced subgraph would answer a different
    question (and give the LTP threshold a betweenness of zero here)."""
    centrality = state_variable_centrality(graph)
    induced = nx.betweenness_centrality(graph.subgraph([LTP, CAPACITY, PRIMITIVE, ORPHAN]))
    assert centrality[LTP]["betweenness"] > induced[LTP]


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------


def test_table_is_sorted_by_convergence_then_betweenness(graph) -> None:
    rows = convergence_table(graph)
    assert rows[0].node == LTP
    counts = [row.n_converging_targets for row in rows]
    assert counts == sorted(counts, reverse=True)


def test_table_excludes_unconverged_sinks_by_default(graph) -> None:
    rows = convergence_table(graph)
    assert ORPHAN not in {row.node for row in rows}
    with_orphans = convergence_table(graph, min_converging_targets=0)
    assert ORPHAN in {row.node for row in with_orphans}


def test_table_rows_are_json_ready(graph) -> None:
    import json

    rows = convergence_table(graph)
    payload = json.dumps([row.as_row() for row in rows])
    assert LTP in payload


def test_table_is_deterministic(graph) -> None:
    first = [row.node for row in convergence_table(graph)]
    second = [row.node for row in convergence_table(graph)]
    assert first == second


def test_works_on_a_multidigraph(graph) -> None:
    """Parallel edges (two claims asserting the same relation) are one relation for
    convergence purposes — contract P5 applied to the graph."""
    multi = nx.MultiDiGraph(graph)
    multi.add_edge("TGT:BETA", LTP, relation="MODULATES", provenance_class="claim_derived")
    convergence = state_variable_convergence(multi)
    assert convergence[LTP]["n_converging_targets"] == 2


def test_empty_graph_returns_empty_results() -> None:
    empty = nx.DiGraph()
    assert state_variable_convergence(empty) == {}
    assert state_variable_centrality(empty) == {}
    assert convergence_table(empty) == ()


# ---------------------------------------------------------------------------
# State-variable polarity (state_model/{safety,stability}.yaml)
# ---------------------------------------------------------------------------


def test_convergence_and_centrality_are_direction_blind(graph) -> None:
    """Safety variables declare `risk` or `margin`, which point opposite ways.

    Every function in this module counts structure and never reads a sign, so adding a
    risk variable and a margin variable with identical topology must produce identical
    convergence and centrality. If that ever stops being true, something in here has
    started reading a direction it is not entitled to guess at.
    """
    for node in ("SV:safety.seizure_risk", "SV:safety.dose_limiting_tolerability_margin"):
        graph.add_node(node, node_type="StateVariable")
        graph.add_edge("TGT:ALPHA", node, relation="CONSTRAINS", provenance_class="claim_derived")

    convergence = state_variable_convergence(graph)
    risk = convergence["SV:safety.seizure_risk"]
    margin = convergence["SV:safety.dose_limiting_tolerability_margin"]
    assert risk["converging_targets"] == margin["converging_targets"]
    assert risk["n_claim_derived_paths"] == margin["n_claim_derived_paths"]

    centrality = state_variable_centrality(graph)
    assert (
        centrality["SV:safety.seizure_risk"] == centrality["SV:safety.dose_limiting_tolerability_margin"]
    )


def test_polarity_is_read_from_the_declaration_not_the_name() -> None:
    """The reader exists so a future directional function cannot guess."""
    from blueprint.ranking.convergence import state_variable_polarity

    assert state_variable_polarity("SV:safety.seizure_risk") == "risk"
    assert state_variable_polarity("SV:safety.dose_limiting_tolerability_margin") == "margin"
    # Domains that declare no polarity return None rather than a default:
    assert state_variable_polarity("SV:power.atp_availability") is None


def test_polarity_reader_rejects_a_malformed_identifier() -> None:
    from blueprint.ranking.convergence import state_variable_polarity

    with pytest.raises(ValueError, match="not a state-variable id"):
        state_variable_polarity("seizure_risk")


def test_polarity_reader_tolerates_an_absent_state_model(tmp_path) -> None:
    from blueprint.ranking.convergence import state_variable_polarity

    assert state_variable_polarity("SV:safety.seizure_risk", state_model_root=str(tmp_path)) is None
