"""The compiler must not let the graph drift positive.

Every test here defends one of the three rulings this sprint spent its effort on. The
data model was made to distinguish a measured absence from an absence of measurement,
and a null from a positive; the compiler is the last place that distinction can be lost
before a reader sees it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from blueprint import loaders, ontology, vocab
from blueprint.graph import compile_graph
from blueprint.graph.compile import CompiledGraph
from blueprint.graph.model import GraphEdgeRecord
from blueprint.graph.traversal import (
    ASSERTING_DIRECTIONS,
    direction_free_edges,
    evidence_summary,
    null_result_edges,
    support_edges,
    supported_paths,
    why_not_supported,
)

RootFactory = Callable[[str | None], Path]


@pytest.fixture(scope="module")
def live() -> CompiledGraph:
    """The real repository's compiled graph, compiled once."""
    return compile_graph()


# ------------------------------------------------------------- determinism -----

def test_compile_is_deterministic(make_root: RootFactory) -> None:
    """Two compiles over one tree produce identical node and edge sequences."""
    root = make_root("valid_minimal")
    first = compile_graph(root)
    second = compile_graph(root)
    assert [n.as_dict() for n in first.nodes] == [n.as_dict() for n in second.nodes]
    assert [e.as_dict() for e in first.edges] == [e.as_dict() for e in second.edges]
    assert first.counts() == second.counts()


def test_compile_output_is_byte_identical(make_root: RootFactory) -> None:
    """Serialised twice, the graph is byte-for-byte the same (contract P7)."""
    root = make_root("valid_minimal")

    def serialise(graph: CompiledGraph) -> str:
        return json.dumps(
            {
                "nodes": [n.as_dict() for n in graph.nodes],
                "edges": [e.as_dict() for e in graph.edges],
            },
            sort_keys=True,
            indent=2,
        )

    assert serialise(compile_graph(root)) == serialise(compile_graph(root))


def test_nodes_and_edges_are_sorted(live: CompiledGraph) -> None:
    """A stable order is what makes an export diffable."""
    keys = [e.key for e in live.edges]
    assert keys == sorted(keys)
    layers = {"evidence": 0, "biological": 1, "intervention": 2}
    ordering = [(layers.get(n.layer, 9), n.node_type, n.id) for n in live.nodes]
    assert ordering == sorted(ordering)


# --------------------------------------- RULING 1: evidence_gap is graph-inert --

def test_evidence_gap_produces_no_biological_or_intervention_edge(live: CompiledGraph) -> None:
    """An absence of measurement is not a finding about biology (contract V16c).

    A gap claim gets its evidence-layer record and nothing in layers 2 or 3.
    """
    graph_inert = set(vocab.subset("claim_type", "graph_inert_values"))
    assert graph_inert, "no claim type is marked graph-inert"
    gap_claims = {
        node.id
        for node in live.nodes
        if node.node_type == "Claim" and node.attributes.get("claim_type") in graph_inert
    }
    if not gap_claims:
        pytest.skip("no evidence_gap claims in the repository yet")

    offenders = [
        edge.as_dict()
        for edge in live.edges
        if edge.layer in {"biological", "intervention"}
        and set(edge.claim_ids) & gap_claims
    ]
    assert not offenders, (
        f"{len(offenders)} layer-2/3 edge(s) were compiled from an evidence_gap claim: "
        f"{offenders[:2]}"
    )


def test_evidence_gap_claim_still_appears_in_the_evidence_layer(live: CompiledGraph) -> None:
    """Graph-inert means no BIOLOGICAL edge, not invisible.

    The gap is a finding about the evidence base and must remain readable.
    """
    graph_inert = set(vocab.subset("claim_type", "graph_inert_values"))
    gaps = [
        node
        for node in live.nodes
        if node.node_type == "Claim" and node.attributes.get("claim_type") in graph_inert
    ]
    if not gaps:
        pytest.skip("no evidence_gap claims in the repository yet")
    for node in gaps:
        assert node.layer == "evidence"
        assert node.attributes.get("is_graph_inert") is True
        assert node.attributes.get("statement")


# ------------------------------- RULING 2: nulls are marked and never support --

def test_null_result_edges_are_marked(live: CompiledGraph) -> None:
    """Every null edge carries the flag and the relation it negates."""
    predicates = set(ontology.load().null_result_predicates())
    nulls = [e for e in live.edges if e.predicate in predicates]
    assert nulls, "no null-result edges in the repository"
    for edge in nulls:
        assert edge.is_null_result is True
        assert edge.claim_ids, "a null edge must carry its claim"
        assert edge.negated_relation, (
            f"{edge.key} does not say what it negates; a null edge should state what was "
            "tested, not merely that something was absent (contract V16b-sym)"
        )


def test_null_result_edges_never_count_as_support(live: CompiledGraph) -> None:
    """The ruling, asserted directly."""
    for edge in null_result_edges(live.edges):
        assert edge.counts_as_support is False
        assert edge not in support_edges(live.edges)
        assert why_not_supported(edge) is not None


def test_support_edges_exclude_nulls_and_unsigned_edges(live: CompiledGraph) -> None:
    """A support edge asserts a change; nothing else does."""
    for edge in support_edges(live.edges):
        assert not edge.is_null_result
        assert edge.direction in ASSERTING_DIRECTIONS
        assert edge.claim_ids
    counted = len(support_edges(live.edges))
    assert counted < len([e for e in live.edges if e.claim_ids]), (
        "every claim-derived edge is being counted as support, which means the filter "
        "is not filtering"
    )


def test_supported_paths_never_traverse_a_null(live: CompiledGraph) -> None:
    """"Evidence for" traversal must not route through a null result.

    A chain containing a performed-and-found-nothing link is not a chain of evidence,
    and returning one would be exactly the drift the null relation prevents.
    """
    nulls = null_result_edges(live.edges)
    if not nulls:
        pytest.skip("no null-result edges to route around")
    sample = nulls[0]
    paths = supported_paths(live.edges, sample.subject, sample.object, max_depth=4)
    for path in paths:
        assert all(not edge.is_null_result for edge in path)
        assert all(edge.direction in ASSERTING_DIRECTIONS for edge in path)


def test_evidence_summary_reports_support_and_nulls_together(live: CompiledGraph) -> None:
    """A support count presented alone is misleading, so it never is."""
    nulls = null_result_edges(live.edges)
    if not nulls:
        pytest.skip("no null-result edges")
    summary = evidence_summary(live.edges, nulls[0].object)
    payload = summary.as_dict()
    assert payload["null_result_count"] >= 1
    assert "support_edge_count" in payload
    assert "has_only_null_or_direction_free_evidence" in payload


# ----------------------------- RULING 3: direction is load-bearing -------------

def test_no_change_and_unclear_are_not_support() -> None:
    """A CONSTRAINS edge with direction: no_change is not support."""
    for direction in ("no_change", "unclear", None):
        edge = GraphEdgeRecord(
            subject="GENE:PLACEHOLDER",
            predicate="CONSTRAINS",
            object="PRIM:planning",
            provenance_class="claim_derived",
            layer="biological",
            claim_ids=["CLM:ontology:PLACEHOLDER:001"],
            direction=direction,
        )
        assert edge.counts_as_support is False, f"direction {direction!r} counted as support"
        assert why_not_supported(edge) is not None


def test_an_asserting_direction_is_support() -> None:
    """The filter must admit what it is meant to admit."""
    edge = GraphEdgeRecord(
        subject="GENE:PLACEHOLDER",
        predicate="NEGATIVELY_REGULATES",
        object="SV:plasticity.ltp_threshold",
        provenance_class="claim_derived",
        layer="biological",
        claim_ids=["CLM:ontology:PLACEHOLDER:001"],
        direction="decreases",
    )
    assert edge.counts_as_support is True
    assert why_not_supported(edge) is None


def test_direction_free_edges_are_the_majority_and_that_is_reported(live: CompiledGraph) -> None:
    """Most claim-derived edges state no asserting direction. That must be visible.

    If a reader assumed every edge was support, the graph would look far stronger than
    it is — which is why `direction_free_edges` exists as a first-class query rather
    than as a subtraction the reader has to do.
    """
    free = direction_free_edges(live.edges)
    supports = support_edges(live.edges)
    assert free, "no direction-free edges, which would be surprising"
    assert len(free) + len(supports) + len(null_result_edges(live.edges)) == len(
        [e for e in live.edges if e.claim_ids]
    ), "the three categories must partition the claim-derived edges"


def test_disagreeing_directions_collapse_to_unclear() -> None:
    """Two claims licensing one triple with opposite signs must not pick a winner."""
    left = GraphEdgeRecord(
        subject="GENE:A", predicate="MODULATES", object="SV:power.lactate_flux",
        provenance_class="claim_derived", layer="biological",
        claim_ids=["CLM:a:A:001"], direction="increases",
    )
    right = GraphEdgeRecord(
        subject="GENE:A", predicate="MODULATES", object="SV:power.lactate_flux",
        provenance_class="claim_derived", layer="biological",
        claim_ids=["CLM:a:A:002"], direction="decreases",
    )
    left.merge(right)
    assert left.direction == "unclear", (
        "a graph that silently picked one sign from two conflicting claims would assert "
        "something neither claim does"
    )
    assert left.counts_as_support is False
    assert left.claim_ids == ["CLM:a:A:001", "CLM:a:A:002"]


# --------------------------------------------------- provenance and identity ---

def test_every_claim_derived_edge_resolves_to_an_existing_claim(live: CompiledGraph) -> None:
    """Contract V17: a claim_derived edge carries at least one resolvable claim id."""
    repo = loaders.load_repository()
    known = set(repo.claims)
    for edge in live.edges:
        if edge.provenance_class != "claim_derived":
            continue
        assert edge.claim_ids, f"{edge.key} is claim_derived but cites no claim"
        missing = [cid for cid in edge.claim_ids if cid not in known]
        assert not missing, f"{edge.key} cites claims that do not exist: {missing}"


def test_every_edge_carries_a_declared_provenance_class(live: CompiledGraph) -> None:
    """Contract V17, over the compiled graph rather than the axiom file."""
    declared = set(ontology.load().provenance_classes)
    for edge in live.edges:
        assert edge.provenance_class in declared, (
            f"{edge.key} has provenance_class {edge.provenance_class!r}"
        )


def test_axioms_and_reference_data_carry_no_claims(live: CompiledGraph) -> None:
    """Structure is not evidence: an axiom that cited a claim would not be an axiom."""
    for edge in live.edges:
        if edge.provenance_class == "ontology_axiom":
            assert not edge.claim_ids
            assert edge.basis, f"{edge.key} is an axiom with no stated basis"
        if edge.provenance_class == "reference_data":
            assert not edge.claim_ids


def test_every_edge_is_a_legal_triple(live: CompiledGraph) -> None:
    """The compiler must not emit an edge the ontology forbids (contract V3)."""
    index = ontology.load()
    nodes = live.node_index()
    for edge in live.edges:
        subject = nodes.get(edge.subject)
        obj = nodes.get(edge.object)
        assert subject is not None, f"{edge.key} has no subject node"
        assert obj is not None, f"{edge.key} has no object node"
        explanation = index.explain_triple(subject.node_type, edge.predicate, obj.node_type)
        assert explanation is None, f"{edge.key}: {explanation}"


def test_duplicate_source_registrations_collapse_to_one_node(make_root: RootFactory) -> None:
    """Contract §1.3: duplication is allowed, and must not inflate the graph.

    Two agents registering the same paper is the preferred arrangement; the graph keeps
    one node and records both registering agents, so duplication cannot inflate a count
    while still being visible to citation-dependence auditing.
    """
    root = make_root("valid_minimal")
    original = (root / "evidence" / "sources" / "ontology.yaml").read_text(encoding="utf-8")
    (root / "evidence" / "sources" / "brakes.yaml").write_text(original, encoding="utf-8")

    graph = compile_graph(root)
    matching = [n for n in graph.nodes if n.id == "SRC:PMID:00000001"]
    assert len(matching) == 1, "a duplicate registration produced two nodes"
    registered = matching[0].attributes.get("registered_by") or []
    assert len(registered) >= 2, f"registering agents not recorded: {registered}"
    assert matching[0].attributes.get("registration_count") == len(registered)


def test_distinct_source_count_deduplicates(live: CompiledGraph) -> None:
    """An edge's source count is DISTINCT sources; duplication cannot inflate it."""
    for edge in live.edges:
        if not edge.source_ids:
            continue
        assert edge.distinct_source_count == len(set(edge.source_ids))


def test_target_identifiers_are_filled_at_compile_time(live: CompiledGraph) -> None:
    """Contract §7: dossiers are authored with `identifiers: {}` and filled here.

    Agents never hand-write an HGNC, Ensembl or UniProt accession, so if these are
    populated they came from the machine-resolved index.
    """
    filled = {
        target_id: identifiers
        for target_id, identifiers in live.target_identifiers.items()
        if identifiers.get("hgnc_id")
    }
    assert filled, "no target identifiers were resolved from the identifier index"
    for target_id, identifiers in filled.items():
        assert identifiers["hgnc_id"].startswith("HGNC:")
        assert identifiers["identifier_provenance"], (
            f"{target_id} has identifiers with no provenance path"
        )


def test_reference_data_edges_come_from_the_identifier_index(live: CompiledGraph) -> None:
    """ENCODES is reference data, never an axiom and never claim-derived (contract §7)."""
    encodes = [e for e in live.edges if e.predicate == "ENCODES"]
    assert encodes, "no ENCODES edges compiled from the identifier index"
    for edge in encodes:
        assert edge.provenance_class == "reference_data"
        assert not edge.claim_ids
        assert edge.basis and "UniProt" in edge.basis


# --------------------------------------------------------------- audit layer ---

def test_audits_are_compiled_when_present(live: CompiledGraph) -> None:
    """The red team's records must appear without the compiler being changed."""
    audits = [n for n in live.nodes if n.node_type == "Audit"]
    if not audits:
        pytest.skip("no audit records yet")
    for node in audits:
        assert node.layer == "evidence"
        assert node.attributes.get("verdict")
        assert node.attributes.get("checks_performed")
    audit_edges = [e for e in live.edges if e.predicate == "AUDITS"]
    assert audit_edges, "audit records exist but no AUDITS edges were compiled"
    for edge in audit_edges:
        assert edge.provenance_class == "reference_data"


# -------------------------------------------------------------- coverage -------

def test_target_coverage_reports_thinness(live: CompiledGraph) -> None:
    """Every target carries the counts that stop it being read as well-evidenced."""
    assert live.target_coverage, "no coverage computed"
    required = {
        "claim_count",
        "distinct_source_count",
        "human_claim_count",
        "facets_graded",
        "facets_not_assessed",
        "facets_zero",
        "null_result_count",
        "evidence_gap_count",
        "reporting_gap_count",
    }
    for target_id, entry in live.target_coverage.items():
        missing = sorted(required - set(entry))
        assert not missing, f"{target_id} coverage is missing {missing}"
        assert entry["reporting_gap_count"] == len(entry.get("reporting_gap_refs") or [])


def test_empty_repository_compiles_to_the_type_system_only(make_root: RootFactory) -> None:
    """With no records, the graph is the ontology: axioms and state variables."""
    graph = compile_graph(make_root(None))
    assert graph.inputs["claims"] == 0
    assert graph.inputs["sources"] == 0
    assert graph.nodes, "even an empty repository has its state variables and primitives"
    assert all(
        edge.provenance_class in {"ontology_axiom", "reference_data"} for edge in graph.edges
    ), "an empty repository produced a claim-derived edge"
    assert not null_result_edges(graph.edges)
    assert not support_edges(graph.edges)


def test_networkx_export_preserves_counts(live: CompiledGraph) -> None:
    """The MultiDiGraph must not lose an edge to key collision."""
    graph = live.to_networkx()
    assert graph.number_of_nodes() == len(live.nodes)
    assert graph.number_of_edges() == len(live.edges)
    nulls = sum(
        1 for _u, _v, data in graph.edges(data=True) if data.get("is_null_result")
    )
    assert nulls == len(null_result_edges(live.edges))
