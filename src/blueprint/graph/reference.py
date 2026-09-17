"""Reference-data edges and identifiers from the machine-resolved index.

Contract §7: agents never hand-write HGNC, Ensembl, UniProt or taxonomy identifiers.
They are resolved by ``scripts/fetch_gene_identifiers.py`` into
``data/interim/gene_identifiers.jsonl``, and this module is the only place the compiler
reads them from.

Two jobs:

* **Gene→Protein `ENCODES` and Gene→Transcript `TRANSCRIBED_AS` edges**, labelled
  ``provenance_class: reference_data`` and pinned to the snapshot each identifier came
  from. ``ontology/edges.yaml`` restricts `ENCODES` to `reference_data`, so these edges
  *cannot* legitimately arrive from anywhere else — in particular not from
  ``definitional_edges.yaml``, which is why that file contains none.
* **Filling a target dossier's `identifiers: {}`** at compile time. Dossiers are
  authored with an empty identifiers block on purpose; this is where it gets populated.

Nothing here reaches the network. The index is derived from immutable snapshots and is
rebuildable offline (contract P7).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from blueprint import paths
from blueprint.graph.model import GraphEdgeRecord, GraphNodeRecord


@dataclass
class IdentifierIndex:
    """HGNC-resolved identifiers, keyed by gene symbol."""

    by_symbol: dict[str, dict[str, Any]] = field(default_factory=dict)
    snapshot_paths: tuple[str, ...] = ()

    def get(self, symbol: str) -> dict[str, Any] | None:
        """The resolved record for ``symbol``, matching the queried or approved name."""
        return self.by_symbol.get(symbol.strip().upper())

    def identifiers_for(self, symbol: str) -> dict[str, Any]:
        """The dossier-shaped identifiers block for ``symbol``, or an empty one.

        Mirrors the contract's §5.1 field names exactly, so a compiled dossier and a
        hand-authored one have the same shape.
        """
        record = self.get(symbol)
        if record is None:
            return {}
        return {
            "hgnc_id": record.get("hgnc_id"),
            "ensembl_gene_id": record.get("ensembl_gene_id"),
            "uniprot_ids": sorted(record.get("uniprot_ids") or []),
            "entrez_id": record.get("entrez_id"),
            "identifier_provenance": record.get("snapshot"),
        }

    @property
    def symbols(self) -> list[str]:
        return sorted(self.by_symbol)


def load_identifier_index(root: Path | str | None = None) -> IdentifierIndex:
    """Load ``data/interim/gene_identifiers.jsonl``.

    Returns an empty index when the file is absent: the identifier pipeline is a network
    step, and a repository that has not run it must still compile (contract P7 separates
    the two).
    """
    path = paths.gene_identifiers_file(root)
    if not path.is_file():
        return IdentifierIndex()
    by_symbol: dict[str, dict[str, Any]] = {}
    snapshots: set[str] = set()
    for line in sorted(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("status") != "approved_symbol":
            # A non-approved symbol resolved to nothing usable; skipping it is safer
            # than compiling an edge from a name HGNC did not confirm.
            continue
        for key in (record.get("symbol"), record.get("queried_symbol")):
            if isinstance(key, str) and key:
                by_symbol[key.strip().upper()] = record
        if isinstance(record.get("snapshot"), str):
            snapshots.add(record["snapshot"])
    return IdentifierIndex(by_symbol=dict(sorted(by_symbol.items())),
                           snapshot_paths=tuple(sorted(snapshots)))


def reference_nodes_and_edges(
    index: IdentifierIndex, *, release_source_id: str | None = None
) -> tuple[list[GraphNodeRecord], list[GraphEdgeRecord]]:
    """Compile Gene/Protein/Transcript nodes and their reference-data edges.

    ``release_source_id`` is the pinned ``SRC:DB:*`` id for the identifier release, when
    one has been registered. It is recorded on every edge because a reference-data edge
    with no pinned release is not reproducible (contract P7), and the edge schema
    requires it.
    """
    nodes: dict[str, GraphNodeRecord] = {}
    edges: dict[tuple[str, str, str], GraphEdgeRecord] = {}

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

    for symbol in index.symbols:
        record = index.get(symbol)
        if record is None or record.get("symbol") != symbol:
            # Index both the approved symbol and any alias, but emit edges once, from
            # the approved symbol only.
            continue
        snapshot = record.get("snapshot")
        gene_id = f"GENE:{symbol}"
        add_node(
            GraphNodeRecord(
                id=gene_id,
                node_type="Gene",
                layer="biological",
                label=symbol,
                provenance_class="reference_data",
                source_refs=[s for s in (release_source_id,) if s],
                attributes={
                    "symbol": symbol,
                    "hgnc_id": record.get("hgnc_id"),
                    "ensembl_gene_id": record.get("ensembl_gene_id"),
                    "entrez_id": record.get("entrez_id"),
                    "gene_name": record.get("gene_name"),
                    "locus_type": record.get("locus_type"),
                    "location": record.get("location"),
                    "identifier_provenance": snapshot,
                    "alias_symbols": sorted(record.get("alias_symbols") or []),
                },
            )
        )

        for accession in sorted(record.get("uniprot_ids") or []):
            protein_id = f"PROT:{accession}"
            add_node(
                GraphNodeRecord(
                    id=protein_id,
                    node_type="Protein",
                    layer="biological",
                    label=accession,
                    provenance_class="reference_data",
                    source_refs=[s for s in (release_source_id,) if s],
                    attributes={
                        "uniprot_accession": accession,
                        "gene_id": gene_id,
                        "identifier_provenance": snapshot,
                    },
                )
            )
            add_edge(
                GraphEdgeRecord(
                    subject=gene_id,
                    predicate="ENCODES",
                    object=protein_id,
                    provenance_class="reference_data",
                    layer="biological",
                    reference_source=release_source_id,
                    basis=f"HGNC/UniProt cross-reference in {snapshot}",
                )
            )

        for transcript in sorted(record.get("mane_select") or []):
            if not transcript.startswith("ENST"):
                # MANE Select lists an RefSeq id alongside the Ensembl one; only the
                # Ensembl form is a legal TX local id (contract §1.1).
                continue
            transcript_id = f"TX:{transcript}"
            add_node(
                GraphNodeRecord(
                    id=transcript_id,
                    node_type="Transcript",
                    layer="biological",
                    label=transcript,
                    provenance_class="reference_data",
                    source_refs=[s for s in (release_source_id,) if s],
                    attributes={
                        "gene_id": gene_id,
                        "mane_select": True,
                        "identifier_provenance": snapshot,
                    },
                )
            )
            add_edge(
                GraphEdgeRecord(
                    subject=gene_id,
                    predicate="TRANSCRIBED_AS",
                    object=transcript_id,
                    provenance_class="reference_data",
                    layer="biological",
                    reference_source=release_source_id,
                    basis=f"Ensembl MANE Select in {snapshot}",
                )
            )

    return list(nodes.values()), list(edges.values())
