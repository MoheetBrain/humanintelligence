#!/usr/bin/env python3
"""Compile the three-layer graph and report what it contains.

Usage
-----
    python graph/build_graph.py                 # compile and print a summary
    python graph/build_graph.py --json          # machine-readable counts
    python graph/build_graph.py --store         # also build the Parquet/DuckDB store
    python graph/build_graph.py --report        # also write the interactive HTML report
    python graph/build_graph.py --all           # compile, store and report
    python graph/build_graph.py --root PATH     # compile a fixture tree
    python graph/build_graph.py --warnings      # show every skipped record

Design rules:

* **Deterministic.** Two runs over one tree produce identical output, including the
  Parquet bytes and the HTML apart from its generation date.
* **Honest counts.** The summary states null-result edges and support edges separately,
  and says plainly when the graph is sparse. A sparse graph with provenance is the
  honest output of this contract (decision D004); a dense graph without it would not be.
* **Re-runnable.** Records are still arriving from five agents; this is meant to be run
  again rather than run once.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from blueprint.graph import compile_graph  # noqa: E402
from blueprint.graph.compile import CompiledGraph  # noqa: E402
from blueprint.graph.traversal import null_result_edges, support_edges  # noqa: E402

# Below this many claim-derived layer-2/3 edges, the graph is sparse enough that saying
# so matters more than the numbers do.
SPARSE_THRESHOLD = 400


def format_summary(compiled: CompiledGraph, *, show_warnings: bool = False) -> str:
    """A human-readable summary of what was compiled."""
    counts = compiled.counts()
    lines: list[str] = []
    lines.append(f"nodes: {counts['nodes']}   edges: {counts['edges']}")
    lines.append("")

    lines.append("by layer:")
    for layer in ("evidence", "biological", "intervention"):
        nodes = counts["nodes_by_layer"].get(layer, 0)
        edges = counts["edges_by_layer"].get(layer, 0)
        lines.append(f"  {layer:14s} {nodes:5d} nodes   {edges:5d} edges")
    lines.append("")

    lines.append("edges by provenance class:")
    for name, value in counts["edges_by_provenance_class"].items():
        lines.append(f"  {name:16s} {value:5d}")
    lines.append("")

    nulls = counts["null_result_edges"]
    supports = counts["support_edges"]
    lines.append(f"null-result edges:      {nulls:5d}  (marked, and excluded from every support count)")
    lines.append(f"edges counted as support: {supports:3d}  (a claim-derived edge whose direction asserts a change)")
    lines.append(f"effect-asserting edges:   {counts['effect_asserting_edges']:3d}  (gated by contract V16)")
    lines.append("")

    lines.append("inputs:")
    for name, value in counts["inputs"].items():
        lines.append(f"  {name:22s} {value:5d}")
    lines.append("")

    claim_derived = counts["edges_by_provenance_class"].get("claim_derived", 0)
    biological_and_intervention = (
        counts["edges_by_layer"].get("biological", 0)
        + counts["edges_by_layer"].get("intervention", 0)
    )
    if biological_and_intervention < SPARSE_THRESHOLD:
        lines.append(
            f"NOTE: the causal graph is SPARSE — {biological_and_intervention} edges across "
            f"layers 2 and 3, of which {claim_derived} carry a claim. That is the honest "
            "output of a contract that refuses an edge without provenance (decision "
            "D004), not a failure of the compiler. A denser graph would mean either more "
            "evidence or a lower bar."
        )
    if compiled.warnings:
        lines.append("")
        lines.append(f"{len(compiled.warnings)} record(s) not compiled into layer 2/3:")
        shown = compiled.warnings if show_warnings else compiled.warnings[:10]
        for warning in shown:
            lines.append(f"  - {warning}")
        if not show_warnings and len(compiled.warnings) > len(shown):
            lines.append(
                f"  ... and {len(compiled.warnings) - len(shown)} more (--warnings for all)"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    parser.add_argument("--json", action="store_true", help="machine-readable counts on stdout")
    parser.add_argument("--quiet", action="store_true", help="print nothing; exit code only")
    parser.add_argument("--warnings", action="store_true", help="show every skipped record")
    parser.add_argument("--store", action="store_true", help="also build the Parquet/DuckDB store")
    parser.add_argument("--report", action="store_true", help="also write the HTML report")
    parser.add_argument("--export", action="store_true", help="also write GraphML/JSON/Neo4j")
    parser.add_argument("--all", action="store_true", help="store + report + export")
    args = parser.parse_args(argv)

    compiled = compile_graph(args.root)

    extras: dict[str, str] = {}
    if args.store or args.all:
        from blueprint.store import build_store

        result = build_store(args.root, compiled=compiled)
        extras["store"] = str(result.duckdb_path)
        extras["store_manifest"] = str(result.manifest_path)
    if args.report or args.all:
        from blueprint.reports import write_graph_report

        extras["report"] = str(write_graph_report(args.root, compiled=compiled))
    if args.export or args.all:
        from blueprint.graph.export import export_all
        from blueprint import paths as _paths

        directory = _paths.resolve_root(args.root) / "data" / "processed" / "export"
        export_result = export_all(compiled, directory)
        extras["export"] = str(directory)
        extras["export_files"] = ", ".join(export_result.files)

    if args.json:
        payload = compiled.counts()
        payload["warnings"] = compiled.warnings
        payload["artefacts"] = extras
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif not args.quiet:
        print(format_summary(compiled, show_warnings=args.warnings))
        if extras:
            print()
            print("wrote:")
            for name, value in sorted(extras.items()):
                print(f"  {name:16s} {value}")

    # Exit 0 even when records were skipped: the validator is what fails a build over a
    # bad record, and a compiler that refused to run would leave an agent with no graph
    # to look at while it fixed one.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
