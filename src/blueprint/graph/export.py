"""Exporters: GraphML, node-link JSON and Neo4j CSV + Cypher.

Design rules:

* **Deterministic.** Nodes and edges are written in sorted order with sorted attribute
  keys, so an export can be diffed between runs and checked into a review.
* **GraphML takes scalars only.** The format has no container type, so nested
  attributes are serialised to JSON strings and the key is suffixed ``_json`` to say so.
  Silently dropping them would make the export look complete when it is not.
* **The null-result flag survives every format.** ``is_null_result``,
  ``negated_relation`` and ``counts_as_support`` are exported everywhere, because a
  consumer that cannot tell a null from a positive edge will count it as support.
* **Neo4j is export-only** (decision D006). The CSV headers and the ``LOAD CSV`` script
  are generated from one specification, so the script cannot drift from the files it
  loads — and a test asserts they agree.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from blueprint.graph.compile import CompiledGraph

# Neo4j CSV columns, in order. One specification drives the headers, the row writer and
# the Cypher script, so the three cannot disagree.
NEO4J_NODE_COLUMNS: tuple[str, ...] = (
    "id:ID",
    "label",
    "node_type",
    "layer",
    "provenance_class",
    "source_refs",
    "attributes_json",
    ":LABEL",
)
NEO4J_EDGE_COLUMNS: tuple[str, ...] = (
    ":START_ID",
    ":END_ID",
    ":TYPE",
    "layer",
    "provenance_class",
    "direction",
    "direction_context",
    "negated_relation",
    "is_null_result:boolean",
    "asserts_effect:boolean",
    "counts_as_support:boolean",
    "evidence_count:int",
    "distinct_source_count:int",
    "claim_ids",
    "basis",
)

# GraphML attribute declarations: key -> (name, type). Nested values go out as JSON
# strings under a `_json` name so nothing is lost and the reader is told.
_GRAPHML_NODE_ATTRS: tuple[tuple[str, str, str], ...] = (
    ("n_label", "label", "string"),
    ("n_type", "node_type", "string"),
    ("n_layer", "layer", "string"),
    ("n_prov", "provenance_class", "string"),
    ("n_sources", "source_refs_json", "string"),
    ("n_attrs", "attributes_json", "string"),
)
_GRAPHML_EDGE_ATTRS: tuple[tuple[str, str, str], ...] = (
    ("e_pred", "predicate", "string"),
    ("e_layer", "layer", "string"),
    ("e_prov", "provenance_class", "string"),
    ("e_dir", "direction", "string"),
    ("e_dirctx", "direction_context", "string"),
    ("e_negates", "negated_relation", "string"),
    ("e_null", "is_null_result", "boolean"),
    ("e_effect", "asserts_effect", "boolean"),
    ("e_support", "counts_as_support", "boolean"),
    ("e_evidence", "evidence_count", "int"),
    ("e_sources", "distinct_source_count", "int"),
    ("e_claims", "claim_ids_json", "string"),
    ("e_basis", "basis", "string"),
)


@dataclass
class ExportResult:
    """Paths written by an export run, with their sizes."""

    files: dict[str, int]

    def summary(self) -> str:
        width = max((len(name) for name in self.files), default=0)
        return "\n".join(
            f"  {name.ljust(width)}  {size:>9,} bytes" for name, size in self.files.items()
        )


def _csv_escape(value: Any) -> str:
    """Escape one CSV field (RFC 4180: double the quotes, quote when needed)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    if any(ch in text for ch in ',"\n\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def _write_csv(path: Path, header: tuple[str, ...], rows: list[list[Any]]) -> None:
    lines = [",".join(header)]
    lines.extend(",".join(_csv_escape(cell) for cell in row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def export_node_link_json(compiled: CompiledGraph, path: Path) -> None:
    """Node-link JSON: the interchange format everything else can read."""
    payload = {
        "format": "blueprint-node-link/0.1.0",
        "directed": True,
        "multigraph": True,
        "counts": compiled.counts(),
        "notes": [
            "Null-result edges carry is_null_result: true and are EXCLUDED from "
            "counts_as_support. A consumer that counts them as support has inverted "
            "the finding.",
            "claim_type: evidence_gap produces an evidence-layer record and no "
            "biological or intervention edge, so an absence of measurement never "
            "appears as a finding about biology.",
            "Nothing here is a safety or efficacy claim. A well-connected node is not a "
            "well-evidenced one.",
        ],
        "nodes": [node.as_dict() for node in compiled.nodes],
        "edges": [edge.as_dict() for edge in compiled.edges],
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def export_graphml(compiled: CompiledGraph, path: Path) -> None:
    """GraphML, with nested attributes serialised to JSON strings."""
    ET.register_namespace("", "http://graphml.graphdrawing.org/xmlns")
    root = ET.Element(
        "{http://graphml.graphdrawing.org/xmlns}graphml",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
    )
    comment = ET.Comment(
        " Intelligence Blueprint graph export. Null-result edges carry "
        "is_null_result=true and counts_as_support=false; a consumer that treats them "
        "as support has inverted the finding. Nothing here is a safety or efficacy "
        "claim. "
    )
    root.append(comment)

    for key, name, attr_type in _GRAPHML_NODE_ATTRS:
        ET.SubElement(
            root,
            "{http://graphml.graphdrawing.org/xmlns}key",
            {"id": key, "for": "node", "attr.name": name, "attr.type": attr_type},
        )
    for key, name, attr_type in _GRAPHML_EDGE_ATTRS:
        ET.SubElement(
            root,
            "{http://graphml.graphdrawing.org/xmlns}key",
            {"id": key, "for": "edge", "attr.name": name, "attr.type": attr_type},
        )

    graph = ET.SubElement(
        root,
        "{http://graphml.graphdrawing.org/xmlns}graph",
        {"id": "intelligence_blueprint", "edgedefault": "directed"},
    )

    def add_data(parent: ET.Element, key: str, value: Any) -> None:
        if value is None or value == "":
            return
        element = ET.SubElement(parent, "{http://graphml.graphdrawing.org/xmlns}data", {"key": key})
        if isinstance(value, bool):
            element.text = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            element.text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        else:
            element.text = str(value)

    for node in compiled.nodes:
        element = ET.SubElement(
            graph, "{http://graphml.graphdrawing.org/xmlns}node", {"id": node.id}
        )
        payload = node.as_dict()
        add_data(element, "n_label", payload["label"])
        add_data(element, "n_type", payload["node_type"])
        add_data(element, "n_layer", payload["layer"])
        add_data(element, "n_prov", payload["provenance_class"])
        add_data(element, "n_sources", payload["source_refs"])
        add_data(element, "n_attrs", payload["attributes"])

    for index, edge in enumerate(compiled.edges):
        element = ET.SubElement(
            graph,
            "{http://graphml.graphdrawing.org/xmlns}edge",
            {"id": f"e{index}", "source": edge.subject, "target": edge.object},
        )
        payload = edge.as_dict()
        add_data(element, "e_pred", payload["predicate"])
        add_data(element, "e_layer", payload["layer"])
        add_data(element, "e_prov", payload["provenance_class"])
        add_data(element, "e_dir", payload["direction"])
        add_data(element, "e_dirctx", payload["direction_context"])
        add_data(element, "e_negates", payload["negated_relation"])
        add_data(element, "e_null", payload["is_null_result"])
        add_data(element, "e_effect", payload["asserts_effect"])
        add_data(element, "e_support", payload["counts_as_support"])
        add_data(element, "e_evidence", payload["evidence_count"])
        add_data(element, "e_sources", payload["distinct_source_count"])
        add_data(element, "e_claims", payload["claim_ids"])
        add_data(element, "e_basis", payload["basis"])

    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    # Normalise the trailing newline so the file is byte-stable across runs.
    text = path.read_text(encoding="utf-8")
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")


def export_neo4j(compiled: CompiledGraph, directory: Path) -> dict[str, int]:
    """Neo4j CSV import files plus the ``LOAD CSV`` script that reads them.

    Export-only per decision D006: nothing in this repository reads Neo4j back.
    """
    directory.mkdir(parents=True, exist_ok=True)
    nodes_path = directory / "neo4j_nodes.csv"
    edges_path = directory / "neo4j_edges.csv"
    cypher_path = directory / "neo4j_import.cypher"

    node_rows: list[list[Any]] = []
    for node in compiled.nodes:
        payload = node.as_dict()
        node_rows.append(
            [
                payload["id"],
                payload["label"],
                payload["node_type"],
                payload["layer"],
                payload["provenance_class"],
                ";".join(payload["source_refs"]),
                json.dumps(payload["attributes"], sort_keys=True, ensure_ascii=False),
                # Two labels: the node type and its layer, so a Cypher query can filter
                # on either without parsing a property.
                f"{payload['node_type']};Layer_{payload['layer'].capitalize()}",
            ]
        )
    _write_csv(nodes_path, NEO4J_NODE_COLUMNS, node_rows)

    edge_rows: list[list[Any]] = []
    for edge in compiled.edges:
        payload = edge.as_dict()
        edge_rows.append(
            [
                payload["subject"],
                payload["object"],
                payload["predicate"],
                payload["layer"],
                payload["provenance_class"],
                payload["direction"],
                payload["direction_context"],
                payload["negated_relation"],
                payload["is_null_result"],
                payload["asserts_effect"],
                payload["counts_as_support"],
                payload["evidence_count"],
                payload["distinct_source_count"],
                ";".join(payload["claim_ids"]),
                payload["basis"],
            ]
        )
    _write_csv(edges_path, NEO4J_EDGE_COLUMNS, edge_rows)

    cypher_path.write_text(_cypher_script(), encoding="utf-8", newline="\n")
    return {
        str(nodes_path.name): nodes_path.stat().st_size,
        str(edges_path.name): edges_path.stat().st_size,
        str(cypher_path.name): cypher_path.stat().st_size,
    }


def _cypher_script() -> str:
    """The ``LOAD CSV`` script, generated from the column specifications.

    Generated rather than hand-written so it cannot drift from the CSV headers. A
    mismatch between the two is silent: the import succeeds and the properties are null.
    """
    node_props = []
    for column in NEO4J_NODE_COLUMNS:
        if column in {"id:ID", ":LABEL"}:
            continue
        node_props.append(f"  n.{column} = row.`{column}`")

    edge_props = []
    for column in NEO4J_EDGE_COLUMNS:
        if column in {":START_ID", ":END_ID", ":TYPE"}:
            continue
        name = column.split(":")[0]
        if column.endswith(":boolean"):
            edge_props.append(f"  r.{name} = toBoolean(row.`{column}`)")
        elif column.endswith(":int"):
            edge_props.append(f"  r.{name} = toInteger(row.`{column}`)")
        else:
            edge_props.append(f"  r.{name} = row.`{column}`")

    return f"""// Intelligence Blueprint — Neo4j import (EXPORT-ONLY, decision D006).
//
// Nothing in this repository reads Neo4j back; this script exists so the graph can be
// explored in a tool that is good at it. Generated by blueprint.graph.export from the
// same column specification as the CSV headers, so the two cannot drift.
//
// READ THIS BEFORE QUERYING:
//   * `is_null_result = true` marks a PERFORMED attempt that detected NO effect. It is
//     a finding, and it is NOT evidence for its target. Any query that means "evidence
//     for" must filter `r.counts_as_support = true`, not merely follow relationships.
//   * `claim_type: evidence_gap` claims produce no biological or intervention
//     relationship at all, so an absence of measurement never appears as a finding.
//   * A relationship with `direction` of `no_change` or `unclear` asserts no change.
//   * Nothing in this graph is a safety or efficacy claim.
//
// Usage: place neo4j_nodes.csv and neo4j_edges.csv in the import directory, then run
// this script with cypher-shell.

CREATE CONSTRAINT blueprint_node_id IF NOT EXISTS
FOR (n:BlueprintNode) REQUIRE n.id IS UNIQUE;

// ---------------------------------------------------------------------- nodes --
LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
MERGE (n:BlueprintNode {{id: row.`id:ID`}})
SET
{",\\n".join(node_props)};

// Apply the node-type and layer labels from the :LABEL column.
LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
MATCH (n:BlueprintNode {{id: row.`id:ID`}})
CALL apoc.create.addLabels(n, split(row.`:LABEL`, ';')) YIELD node
RETURN count(node);

// ---------------------------------------------------------------------- edges --
LOAD CSV WITH HEADERS FROM 'file:///neo4j_edges.csv' AS row
MATCH (a:BlueprintNode {{id: row.`:START_ID`}})
MATCH (b:BlueprintNode {{id: row.`:END_ID`}})
CALL apoc.merge.relationship(a, row.`:TYPE`, {{}}, {{}}, b) YIELD rel AS r
SET
{",\\n".join(edge_props)};

// ------------------------------------------------------------------- examples --
// Evidence FOR a phenotype — note the counts_as_support filter:
//   MATCH (s)-[r]->(p:CognitivePhenotype)
//   WHERE r.counts_as_support = true
//   RETURN s.id, type(r), r.direction, r.claim_ids;
//
// The nulls, which the query above deliberately excludes:
//   MATCH (s)-[r]->(o)
//   WHERE r.is_null_result = true
//   RETURN s.id, type(r), o.id, r.negated_relation, r.claim_ids;
"""


def export_all(compiled: CompiledGraph, directory: Path) -> ExportResult:
    """Write every format into ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    files: dict[str, int] = {}

    json_path = directory / "intelligence_graph_v0_1.json"
    export_node_link_json(compiled, json_path)
    files[json_path.name] = json_path.stat().st_size

    graphml_path = directory / "intelligence_graph_v0_1.graphml"
    export_graphml(compiled, graphml_path)
    files[graphml_path.name] = graphml_path.stat().st_size

    files.update(export_neo4j(compiled, directory))
    return ExportResult(files=dict(sorted(files.items())))


def load_node_link_json(path: Path) -> dict[str, Any]:
    """Read back a node-link export, for the round-trip test."""
    return json.loads(path.read_text(encoding="utf-8"))
