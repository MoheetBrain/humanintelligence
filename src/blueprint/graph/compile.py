"""Compile the curated records into a three-layer NetworkX graph.

Determinism
-----------
Two runs over one tree produce byte-identical output. Inputs are visited in sorted
order, node and edge attributes are sorted, merges are order-independent (list
attributes union and sort; disagreeing directions collapse to ``unclear`` rather than to
whichever was read first), and nothing depends on dict insertion order or on which
agent's file happened to be read first.

The three rulings this compiler exists to enforce
-------------------------------------------------
**`evidence_gap` is graph-inert.** A gap produces its evidence-layer Claim node, its
`REPORTS` edges from the sources and its `ABOUT` edge, and NO layer-2/3 edge. An absence
of measurement is not a finding about biology, so it must not appear as one.

**`NO_DETECTED_EFFECT_ON` is marked, not dropped.** The edge is compiled with
``is_null_result: true`` and its ``negated_relation``, and excluded from support counts.
Dropping it would restore exactly the bias it was created to remove: a positive trial
compiling into an edge while an equally well-powered null compiles into nothing.

**Direction is load-bearing.** An edge records its ``direction`` and, when the sign is
state-dependent, its ``direction_context``. ``counts_as_support`` is false for
``no_change``, ``unclear`` and absent directions, so no traversal can read an absent
sign as positive.

Provenance
----------
Every edge carries a ``provenance_class`` (contract V17). ``claim_derived`` edges carry
the claim ids that licensed them and the DISTINCT source count — deduplicated by
``source_id``, so duplicate registration across agents cannot inflate an evidence count
(contract §1.3). Duplicate source registrations collapse to one node whose
``registered_by`` attribute lists every agent that registered it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from blueprint import ids, loaders, ontology, paths, vocab
from blueprint.graph.model import (
    GraphEdgeRecord,
    GraphNodeRecord,
    sort_edges,
    sort_nodes,
)
from blueprint.graph.reference import IdentifierIndex, load_identifier_index, reference_nodes_and_edges

# Node types that carry a registered source, by source-id prefix. A source's node type
# is not recorded in the record (the record carries `source_type`), so it is derived
# from the prefix the contract assigns it (§1.3).
_SOURCE_NODE_TYPE: dict[str, str] = {
    "SRC:PMID": "Paper",
    "SRC:DOI": "Paper",
    "SRC:NCT": "ClinicalTrial",
    "SRC:GCST": "Dataset",
    "SRC:DATASET": "Dataset",
    "SRC:DB": "DatabaseRelease",
}

# `source_type` values that make a Paper a Review instead, so citation-dependence
# auditing can find evidence resting on secondary reporting.
_REVIEW_TYPES = {"review", "meta_analysis", "systematic_review", "narrative_review"}


@dataclass
class CompiledGraph:
    """The compiled graph plus the counts a report needs to be honest about it."""

    nodes: list[GraphNodeRecord]
    edges: list[GraphEdgeRecord]
    target_identifiers: dict[str, dict[str, Any]] = field(default_factory=dict)
    target_coverage: dict[str, dict[str, Any]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    inputs: dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------- summaries ---

    def counts(self) -> dict[str, Any]:
        """Node and edge counts, broken down the way the brief asks for them."""
        nodes_by_layer: dict[str, int] = {}
        nodes_by_type: dict[str, int] = {}
        for node in self.nodes:
            nodes_by_layer[node.layer] = nodes_by_layer.get(node.layer, 0) + 1
            nodes_by_type[node.node_type] = nodes_by_type.get(node.node_type, 0) + 1
        edges_by_layer: dict[str, int] = {}
        edges_by_provenance: dict[str, int] = {}
        edges_by_predicate: dict[str, int] = {}
        for edge in self.edges:
            edges_by_layer[edge.layer] = edges_by_layer.get(edge.layer, 0) + 1
            edges_by_provenance[edge.provenance_class] = (
                edges_by_provenance.get(edge.provenance_class, 0) + 1
            )
            edges_by_predicate[edge.predicate] = edges_by_predicate.get(edge.predicate, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "nodes_by_layer": dict(sorted(nodes_by_layer.items())),
            "nodes_by_type": dict(sorted(nodes_by_type.items())),
            "edges_by_layer": dict(sorted(edges_by_layer.items())),
            "edges_by_provenance_class": dict(sorted(edges_by_provenance.items())),
            "edges_by_predicate": dict(sorted(edges_by_predicate.items())),
            "null_result_edges": sum(1 for e in self.edges if e.is_null_result),
            "support_edges": sum(1 for e in self.edges if e.counts_as_support),
            "effect_asserting_edges": sum(1 for e in self.edges if e.asserts_effect),
            "inputs": dict(sorted(self.inputs.items())),
        }

    def to_networkx(self) -> nx.MultiDiGraph:
        """A ``MultiDiGraph`` keyed by predicate, with attributes attached.

        MultiDiGraph rather than DiGraph because two nodes can legitimately be joined by
        more than one relation — a compound can both `TARGETS` a protein and
        `NO_DETECTED_EFFECT_ON` a state variable downstream of it, and collapsing those
        would lose the distinction this sprint spent its effort creating.
        """
        graph = nx.MultiDiGraph()
        graph.graph["layers"] = list(dict.fromkeys(n.layer for n in self.nodes))
        for node in sort_nodes(self.nodes):
            payload = node.as_dict()
            graph.add_node(payload.pop("id"), **payload)
        for edge in sort_edges(self.edges):
            payload = edge.as_dict()
            subject = payload.pop("subject")
            obj = payload.pop("object")
            graph.add_edge(subject, obj, key=payload["predicate"], **payload)
        return graph

    def node_index(self) -> dict[str, GraphNodeRecord]:
        return {node.id: node for node in self.nodes}


def _node_type_for(node_id: str, index: ontology.Ontology, root: Path) -> str | None:
    """The most general node type an id may denote, or ``None`` when unknown."""
    if not ids.is_valid(node_id, root):
        return None
    candidates = ids.node_types_for(node_id, root)
    if not candidates:
        return None
    general = [name for name in candidates if index.nodes[name].parent is None]
    return sorted(general)[0] if general else sorted(candidates)[0]


def _layer_for(node_type: str, index: ontology.Ontology) -> str:
    """The layer a node type belongs to (its home layer)."""
    spec = index.nodes.get(node_type)
    return spec.layer if spec else "biological"


def _edge_layer(predicate: str, object_type: str | None, index: ontology.Ontology) -> str:
    """Which layer an edge belongs to.

    A relation may declare more than one layer (an intervention acting on a biological
    state variable). The OBJECT's layer decides, because that is where the edge lands
    and therefore where a reader will look for it.
    """
    spec = index.edges.get(predicate)
    if spec is None:
        return "biological"
    if len(spec.layers) == 1:
        return spec.layers[0]
    if object_type is not None:
        object_layer = _layer_for(object_type, index)
        if object_layer in spec.layers:
            return object_layer
    return spec.layers[0]


def compile_graph(root: Path | str | None = None) -> CompiledGraph:
    """Compile every curated record under ``root`` into one graph.

    Tolerant of an incomplete repository: a claim naming an unknown node type is skipped
    with a warning rather than aborting the compile, because the validator is what
    reports those and a compile that died on the first bad record would be useless
    while five agents are writing concurrently.
    """
    resolved = paths.resolve_root(root)
    repo = loaders.load_repository(resolved)
    index = ontology.load(resolved)
    identifiers = load_identifier_index(resolved)

    nodes: dict[str, GraphNodeRecord] = {}
    edges: dict[tuple[str, str, str], GraphEdgeRecord] = {}
    warnings: list[str] = []

    def add_node(node: GraphNodeRecord) -> None:
        existing = nodes.get(node.id)
        if existing is None:
            nodes[node.id] = node
        else:
            existing.merge(node)

    def add_edge(edge: GraphEdgeRecord) -> None:
        existing = edges.get(edge.key)
        if existing is None:
            edges[edge.key] = edge
        else:
            existing.merge(edge)

    def ensure_entity(node_id: str, *, provenance: str = "claim_derived") -> str | None:
        """Add a bare node for an id a record referenced, returning its type."""
        node_type = _node_type_for(node_id, index, resolved)
        if node_type is None:
            return None
        add_node(
            GraphNodeRecord(
                id=node_id,
                node_type=node_type,
                layer=_layer_for(node_type, index),
                label=node_id.split(":", 1)[1] if ":" in node_id else node_id,
                provenance_class=provenance,
            )
        )
        return node_type

    graph_inert = set(vocab.subset("claim_type", "graph_inert_values", resolved))
    null_predicates = set(index.null_result_predicates())

    # ------------------------------------------------ reference-data layer ---
    # The pinned release for the identifier index, if an agent registered one.
    release_source = next(
        (sid for sid in sorted(repo.sources) if sid.startswith("SRC:DB:hgnc")), None
    )
    ref_nodes, ref_edges = reference_nodes_and_edges(
        identifiers, release_source_id=release_source
    )
    for node in ref_nodes:
        add_node(node)
    for edge in ref_edges:
        add_edge(edge)

    # ----------------------------------------------------- evidence layer ---
    for source_id, record in repo.sources.items():
        prefix = source_id.rsplit(":", 1)[0] if source_id.count(":") > 1 else source_id
        node_type = _SOURCE_NODE_TYPE.get(prefix, "Paper")
        if node_type == "Paper" and str(record.raw.get("source_type")) in _REVIEW_TYPES:
            node_type = "Review"
        elif node_type == "Paper" and record.raw.get("source_type") == "preprint":
            node_type = "Preprint"
        registering = sorted(
            {
                str(loaded.raw.get("added_by"))
                for loaded in [record]
                if loaded.raw.get("added_by")
            }
            | _agents_registering(repo, source_id)
        )
        add_node(
            GraphNodeRecord(
                id=source_id,
                node_type=node_type,
                layer="evidence",
                label=str(record.raw.get("title") or source_id)[:120],
                provenance_class="reference_data",
                attributes={
                    "source_type": record.raw.get("source_type"),
                    "title": record.raw.get("title"),
                    "year": record.raw.get("year"),
                    "first_author": record.raw.get("first_author"),
                    "container": record.raw.get("container"),
                    "identifiers": record.raw.get("identifiers") or {},
                    # Duplicate registration across agents is allowed and preferred
                    # (contract §1.3); the graph keeps WHO registered it so the red
                    # team's citation-dependence check can see shared sources.
                    "registered_by": registering,
                    "registration_count": len(registering),
                    "retrieval_method": (record.raw.get("retrieval") or {}).get("method"),
                },
            )
        )

    for claim_id, record in repo.claims.items():
        raw = record.raw
        claim_type = str(raw.get("claim_type") or "")
        predicate = raw.get("predicate")
        subject, obj = raw.get("subject"), raw.get("object")
        evidence_items = [i for i in (raw.get("evidence") or []) if isinstance(i, dict)]
        source_ids = sorted(
            {str(i["source_id"]) for i in evidence_items if isinstance(i.get("source_id"), str)}
        )
        context = raw.get("context") or {}

        add_node(
            GraphNodeRecord(
                id=claim_id,
                node_type="Claim",
                layer="evidence",
                label=str(raw.get("statement") or claim_id)[:160],
                provenance_class="claim_derived",
                source_refs=source_ids,
                attributes={
                    "statement": raw.get("statement"),
                    "claim_type": claim_type,
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "direction": raw.get("direction"),
                    "direction_context": raw.get("direction_context"),
                    "status": raw.get("status"),
                    "phenotype_class": raw.get("phenotype_class"),
                    "species": sorted(str(s) for s in (context.get("species") or [])),
                    "life_stage": context.get("life_stage"),
                    "baseline_context": context.get("baseline_context"),
                    "causal_basis": (raw.get("causal_attribution") or {}).get("basis"),
                    "human_relevance": (raw.get("translation") or {}).get("human_relevance"),
                    "uncertainty_level": (raw.get("uncertainty") or {}).get("level"),
                    "created_by": (raw.get("provenance") or {}).get("created_by"),
                    "evidence_count": len(evidence_items),
                    "distinct_source_count": len(source_ids),
                    # Marked on the node as well as the edge, because an evidence_gap
                    # has NO layer-2/3 edge to carry the fact.
                    "is_graph_inert": claim_type in graph_inert,
                    "is_null_result": predicate in null_predicates,
                },
            )
        )

        # Evidence items, and the source -> item -> claim chain.
        for position, item in enumerate(evidence_items, start=1):
            local = claim_id.split(":", 1)[1] if ":" in claim_id else claim_id
            evidence_id = str(item.get("evidence_id") or f"EVD:{local}#{position}")
            add_node(
                GraphNodeRecord(
                    id=evidence_id,
                    node_type="Measurement",
                    layer="evidence",
                    label=str(item.get("endpoint") or evidence_id)[:120],
                    provenance_class="claim_derived",
                    source_refs=[str(item.get("source_id"))] if item.get("source_id") else [],
                    attributes={
                        "source_id": item.get("source_id"),
                        "design": item.get("design"),
                        "species": item.get("species"),
                        "population": item.get("population"),
                        "endpoint": item.get("endpoint"),
                        "endpoint_category": item.get("endpoint_category"),
                        "endpoint_measured": item.get("endpoint_measured", "unknown"),
                        "effect_direction": item.get("effect_direction"),
                        "replication_status": item.get("replication_status"),
                        "evidence_role": item.get("evidence_role"),
                        "extraction_basis": (item.get("extraction") or {}).get("basis"),
                        "content_checked": (item.get("extraction") or {}).get("content_checked"),
                        "sample_size": (item.get("sample_size") or {}).get("value"),
                    },
                )
            )
            source_id = item.get("source_id")
            if isinstance(source_id, str) and source_id in nodes:
                add_edge(
                    GraphEdgeRecord(
                        subject=source_id,
                        predicate="REPORTS",
                        object=evidence_id,
                        provenance_class="reference_data",
                        layer="evidence",
                        reference_source=source_id,
                        basis="the source contains this measurement",
                    )
                )
            role = str(item.get("evidence_role") or "supports")
            relation = {
                "supports": "SUPPORTS",
                "contradicts": "CONTRADICTS",
                "qualifies": "QUALIFIES",
                "null_result": "QUALIFIES",
            }.get(role, "SUPPORTS")
            add_edge(
                GraphEdgeRecord(
                    subject=evidence_id,
                    predicate=relation,
                    object=claim_id,
                    provenance_class="claim_derived",
                    layer="evidence",
                    claim_ids=[claim_id],
                    claim_types=[claim_type],
                    source_ids=[str(source_id)] if isinstance(source_id, str) else [],
                    evidence_count=1,
                    distinct_source_count=1 if isinstance(source_id, str) else 0,
                    basis=f"evidence_role: {role}",
                )
            )
            if isinstance(item.get("species"), str):
                if ensure_entity(item["species"], provenance="reference_data"):
                    add_edge(
                        GraphEdgeRecord(
                            subject=evidence_id,
                            predicate="MEASURED_IN",
                            object=item["species"],
                            provenance_class="reference_data",
                            layer="evidence",
                            reference_source=str(item.get("source_id") or ""),
                            basis="species of the measurement",
                        )
                    )

        # ---------------------------------------- layers 2 and 3, or not ---
        if not isinstance(predicate, str) or not isinstance(subject, str) or not isinstance(obj, str):
            continue
        subject_type = _node_type_for(subject, index, resolved)
        object_type = _node_type_for(obj, index, resolved)
        if subject_type is None or object_type is None:
            warnings.append(
                f"{claim_id}: skipped — {subject if subject_type is None else obj} "
                "matches no declared node type (the validator reports this as V2)"
            )
            continue
        ensure_entity(subject)
        ensure_entity(obj)

        spec = index.edges.get(predicate)
        if spec is None:
            warnings.append(f"{claim_id}: skipped — {predicate} is not a declared relation")
            continue
        if spec.layers == ("evidence",):
            # An evidence-layer relation (ABOUT, SUPPORTS) stays in layer 1. This is
            # also where an `evidence_gap` lands: its home relation is ABOUT.
            add_edge(
                GraphEdgeRecord(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    provenance_class="claim_derived",
                    layer="evidence",
                    claim_ids=[claim_id],
                    claim_types=[claim_type],
                    source_ids=source_ids,
                    evidence_count=len(evidence_items),
                    distinct_source_count=len(source_ids),
                    basis="evidence-layer relation; carries no biological assertion",
                )
            )
            continue

        if claim_type in graph_inert:
            # THE RULING: a gap produces its evidence-layer record and no layer-2/3
            # edge. An absence of measurement is not a finding about biology, so it
            # must not appear as one.
            warnings.append(
                f"{claim_id}: graph-inert ({claim_type}) — evidence-layer record only, "
                f"no {predicate} edge compiled (contract V16c)"
            )
            continue

        is_null = predicate in null_predicates
        add_edge(
            GraphEdgeRecord(
                subject=subject,
                predicate=predicate,
                object=obj,
                provenance_class="claim_derived",
                layer=_edge_layer(predicate, object_type, index),
                claim_ids=[claim_id],
                claim_types=[claim_type],
                direction=raw.get("direction"),
                direction_context=raw.get("direction_context"),
                negated_relation=raw.get("negated_relation"),
                is_null_result=is_null,
                asserts_effect=index.asserts_effect(predicate, object_type),
                evidence_count=len(evidence_items),
                distinct_source_count=len(source_ids),
                source_ids=source_ids,
            )
        )

    # ------------------------------------------------------------- audits ---
    for audit_id, record in repo.audits.items():
        raw = record.raw
        scope = raw.get("scope") or {}
        add_node(
            GraphNodeRecord(
                id=audit_id,
                node_type="Audit",
                layer="evidence",
                label=f"{audit_id} ({raw.get('verdict')})",
                provenance_class="claim_derived",
                attributes={
                    "scope_kind": scope.get("kind"),
                    "scope_id": scope.get("id"),
                    "audited_by": raw.get("audited_by"),
                    "audited_on": raw.get("audited_on"),
                    "verdict": raw.get("verdict"),
                    "finding_count": len(raw.get("findings") or []),
                    "adjustment_count": len(raw.get("adjustments") or []),
                    "checks_performed": sorted(
                        str(c.get("check"))
                        for c in (raw.get("checks") or [])
                        if isinstance(c, dict)
                    ),
                },
            )
        )
        scope_id = scope.get("id")
        if isinstance(scope_id, str) and scope.get("kind") in {"target", "claim"}:
            if ensure_entity(scope_id, provenance="reference_data"):
                add_edge(
                    GraphEdgeRecord(
                        subject=audit_id,
                        predicate="AUDITS",
                        object=scope_id,
                        provenance_class="reference_data",
                        layer="evidence",
                        reference_source=audit_id,
                        basis=f"audit scope: {scope.get('kind')}",
                    )
                )

    # ------------------------------------------------- state variables etc ---
    for sv_id, record in repo.state_variables.items():
        raw = record.raw
        add_node(
            GraphNodeRecord(
                id=sv_id,
                node_type="StateVariable",
                layer="biological",
                label=str(raw.get("name") or sv_id),
                provenance_class="ontology_axiom",
                attributes={
                    "domain": sv_id.split(":", 1)[1].split(".", 1)[0],
                    "definition": raw.get("definition"),
                    "kind": raw.get("kind"),
                    "timescale": raw.get("timescale"),
                    "level": raw.get("level"),
                    "units": raw.get("units"),
                    "response_shape": (raw.get("response_shape") or {}).get("shape"),
                    "response_shape_basis": (raw.get("response_shape") or {}).get("basis"),
                    "desirability": raw.get("desirability"),
                    "polarity": raw.get("polarity"),
                    "status": raw.get("status"),
                },
            )
        )
    for primitive_id, primitive in index.primitives.items():
        add_node(
            GraphNodeRecord(
                id=primitive_id,
                node_type="ComputationalPrimitive",
                layer="biological",
                label=primitive.name,
                provenance_class="ontology_axiom",
                attributes={
                    "definition": primitive.definition,
                    "definition_status": primitive.definition_status,
                    "animal_analogue_caveat": primitive.animal_analogue_caveat,
                    "human_measurement_paradigms": list(primitive.human_measurement_paradigms),
                },
            )
        )

    # ------------------------------------------------------------- axioms ---
    for axiom in index.definitional_edges:
        subject_type = ensure_entity(axiom.subject, provenance="ontology_axiom")
        object_type = ensure_entity(axiom.object, provenance="ontology_axiom")
        if subject_type is None or object_type is None:
            warnings.append(
                f"axiom {axiom.subject} -{axiom.predicate}-> {axiom.object}: skipped, "
                "an endpoint matches no declared node type"
            )
            continue
        add_edge(
            GraphEdgeRecord(
                subject=axiom.subject,
                predicate=axiom.predicate,
                object=axiom.object,
                provenance_class="ontology_axiom",
                layer=_edge_layer(axiom.predicate, object_type, index),
                basis=axiom.basis,
            )
        )

    # ----------------------------------------------- targets and dossiers ---
    target_identifiers: dict[str, dict[str, Any]] = {}
    for target_id, record in repo.targets.items():
        raw = record.raw
        symbol = str(raw.get("symbol") or target_id.split(":", 1)[-1])
        # Contract §7: dossiers are authored with `identifiers: {}` and filled HERE
        # from the machine-resolved index. Agents never hand-write an accession.
        resolved_identifiers = identifiers.identifiers_for(symbol)
        target_identifiers[target_id] = resolved_identifiers
        add_node(
            GraphNodeRecord(
                id=target_id,
                node_type="Target",
                layer="intervention",
                label=symbol,
                provenance_class="reference_data",
                attributes={
                    "symbol": symbol,
                    "lead_atlas": raw.get("lead_atlas"),
                    "dossier_depth": raw.get("dossier_depth"),
                    "status": raw.get("status"),
                    "seed_origin": raw.get("seed_origin"),
                    "target_class": raw.get("target_class"),
                    "developmental_confound": raw.get("developmental_confound"),
                    "identifiers": resolved_identifiers,
                    "identifiers_filled_at_compile_time": bool(resolved_identifiers),
                },
            )
        )
        for entity in sorted(str(e) for e in (raw.get("represented_entities") or [])):
            if ensure_entity(entity, provenance="reference_data"):
                add_edge(
                    GraphEdgeRecord(
                        subject=target_id,
                        predicate="REPRESENTS",
                        object=entity,
                        provenance_class="reference_data",
                        layer="intervention",
                        reference_source=release_source or "targets/candidates",
                        basis="dossier represented_entities",
                    )
                )

    for intervention_id, record in repo.interventions.items():
        raw = record.raw
        node_type = str(raw.get("node_type") or "")
        if node_type not in index.nodes:
            node_type = _node_type_for(intervention_id, index, resolved) or "Compound"
        add_node(
            GraphNodeRecord(
                id=intervention_id,
                node_type=node_type,
                layer="intervention",
                label=str(raw.get("label") or raw.get("preferred_name") or raw.get("name") or intervention_id),
                provenance_class="reference_data",
                attributes={
                    "modality": raw.get("modality"),
                    "registered_by": [
                        str(v)
                        for v in (
                            raw.get("recorded_by"),
                            raw.get("added_by"),
                            (raw.get("provenance") or {}).get("created_by"),
                        )
                        if v
                    ],
                    "dose_information": raw.get("dose_information", "omitted_by_policy"),
                    "blood_brain_barrier": raw.get("blood_brain_barrier"),
                    "efficacy_status": raw.get("efficacy_status"),
                },
            )
        )

    compiled = CompiledGraph(
        nodes=sort_nodes(nodes.values()),
        edges=sort_edges(edges.values()),
        target_identifiers=dict(sorted(target_identifiers.items())),
        warnings=sorted(warnings),
        inputs={
            "sources": len(repo.sources),
            "claims": len(repo.claims),
            "evidence_items": sum(len(r.raw.get("evidence") or []) for r in repo.claims.values()),
            "targets": len(repo.targets),
            "assessments": len(repo.assessments),
            "audits": len(repo.audits),
            "interventions": len(repo.interventions),
            "state_variables": len(repo.state_variables),
            "annotations": len(repo.state_variable_annotations),
            "definitional_edges": len(index.definitional_edges),
            "shared_sources": len(repo.shared_sources),
        },
    )
    compiled.target_coverage = _target_coverage(repo, compiled)
    return compiled


def _agents_registering(repo: loaders.Repository, source_id: str) -> set[str]:
    """Every agent whose source file registers ``source_id`` (contract §1.3)."""
    agents: set[str] = set()
    for owning_file in repo.shared_sources.get(source_id, ()):
        stem = owning_file.rsplit("/", 1)[-1].removesuffix(".yaml")
        agents.add(f"agent:{stem}")
    return agents


def _target_coverage(repo: loaders.Repository, compiled: CompiledGraph) -> dict[str, dict[str, Any]]:
    """Per-target evidence coverage, for the report's honesty columns.

    A reader must not be able to see a well-connected node without also seeing how thin
    its evidence is, so this computes — per target — the graded and not-assessed facet
    counts, the reporting-gap count, the null-result count and the distinct source
    count. ``reporting_gap_count`` is how publication bias becomes visible in the data
    (contract §5.2, R14) rather than staying an observation in a handoff note.
    """
    coverage: dict[str, dict[str, Any]] = {}
    symbol_to_target = {
        str(record.raw.get("symbol") or tid.split(":", 1)[-1]): tid
        for tid, record in repo.targets.items()
    }

    for target_id, record in repo.targets.items():
        coverage[target_id] = {
            "symbol": record.raw.get("symbol"),
            "lead_atlas": record.raw.get("lead_atlas"),
            "dossier_depth": record.raw.get("dossier_depth"),
            "facets_graded": 0,
            "facets_not_assessed": 0,
            "facets_zero": 0,
            "reporting_gap_count": 0,
            "reporting_gap_refs": [],
            "claim_count": 0,
            "null_result_count": 0,
            "evidence_gap_count": 0,
            "distinct_source_count": 0,
            "human_claim_count": 0,
        }

    for record in repo.assessments:
        target_id = str(record.raw.get("target_id") or "")
        entry = coverage.get(target_id)
        if entry is None:
            continue
        gaps: set[str] = set()
        for facet in record.raw.get("facets") or []:
            if not isinstance(facet, dict):
                continue
            status = facet.get("assessment_status")
            level = facet.get("level")
            if status == "assessed" and isinstance(level, int) and not isinstance(level, bool):
                entry["facets_graded"] += 1
                if level == 0:
                    entry["facets_zero"] += 1
            else:
                entry["facets_not_assessed"] += 1
            gaps.update(str(r) for r in (facet.get("reporting_gap_refs") or []))
        entry["reporting_gap_refs"] = sorted(set(entry["reporting_gap_refs"]) | gaps)
        entry["reporting_gap_count"] = len(entry["reporting_gap_refs"])

    human_values = vocab.human_evidence_values(repo.root)
    null_predicates = set(ontology.load(repo.root).null_result_predicates())
    graph_inert = set(vocab.subset("claim_type", "graph_inert_values", repo.root))

    for claim_id, record in repo.claims.items():
        raw = record.raw
        # A claim belongs to a target when its domain segment names the target's symbol,
        # or when its subject/object is an entity the target represents. The domain
        # segment is the cheap and reliable signal, since claim ids are
        # CLM:{agent}:{TARGET_OR_TOPIC}:{nnn}.
        parts = claim_id.split(":")
        topic = parts[2] if len(parts) > 3 else ""
        target_id = symbol_to_target.get(topic)
        if target_id is None:
            continue
        entry = coverage[target_id]
        entry["claim_count"] += 1
        if raw.get("predicate") in null_predicates:
            entry["null_result_count"] += 1
        if raw.get("claim_type") in graph_inert:
            entry["evidence_gap_count"] += 1
        if (raw.get("translation") or {}).get("human_relevance") in human_values:
            entry["human_claim_count"] += 1
        sources = {
            str(i.get("source_id"))
            for i in (raw.get("evidence") or [])
            if isinstance(i, dict) and isinstance(i.get("source_id"), str)
        }
        entry["distinct_source_count"] = len(
            set(entry.get("_sources", set())) | sources
        )
        entry["_sources"] = sorted(set(entry.get("_sources", [])) | sources)

    for entry in coverage.values():
        entry.pop("_sources", None)
    return dict(sorted(coverage.items()))
