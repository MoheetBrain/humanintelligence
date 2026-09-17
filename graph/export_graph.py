#!/usr/bin/env python3
"""Export the compiled graph: GraphML, node-link JSON, Neo4j CSV + Cypher, and the HTML.

Usage
-----
    python graph/export_graph.py                 # every machine format
    python graph/export_graph.py --html          # also write the interactive report
    python graph/export_graph.py --only html     # the report alone
    python graph/export_graph.py --out DIR       # write the machine formats elsewhere
    python graph/export_graph.py --root PATH     # export a fixture tree

Design rules:

* **Deterministic.** Nodes and edges are written sorted with sorted attribute keys, so
  an export can be diffed between runs.
* **The null-result flag survives every format.** ``is_null_result``,
  ``negated_relation`` and ``counts_as_support`` are exported everywhere, because a
  consumer that cannot tell a null from a positive edge will count it as support — and
  that is the one mistake this whole layer exists to prevent.
* **Neo4j is export-only** (decision D006). Nothing here reads Neo4j back. The CSV
  headers and the ``LOAD CSV`` script are generated from one specification so they
  cannot drift.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from blueprint import paths  # noqa: E402
from blueprint.graph import compile_graph  # noqa: E402
from blueprint.graph.export import export_all, export_graphml, export_neo4j, export_node_link_json  # noqa: E402

FORMATS = ("json", "graphml", "neo4j", "html")


def default_output_dir(root: Path) -> Path:
    """``data/processed/export/`` — derived, git-ignored, rebuilt by ``make reports``."""
    return paths.data_dir(root) / "processed" / "export"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    parser.add_argument("--out", default=None, help="output directory for machine formats")
    parser.add_argument(
        "--html",
        action="store_true",
        help="also write reports/intelligence_graph_v0_1.html",
    )
    parser.add_argument(
        "--only",
        choices=FORMATS,
        help="write just this format",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    root = paths.resolve_root(args.root)
    compiled = compile_graph(root)
    out_dir = Path(args.out) if args.out else default_output_dir(root)

    written: dict[str, int] = {}
    wants = {args.only} if args.only else {"json", "graphml", "neo4j"}
    if args.html or args.only == "html":
        wants.add("html")

    if wants & {"json", "graphml", "neo4j"}:
        out_dir.mkdir(parents=True, exist_ok=True)

    if wants == {"json", "graphml", "neo4j"}:
        written.update(export_all(compiled, out_dir).files)
    else:
        if "json" in wants:
            path = out_dir / "intelligence_graph_v0_1.json"
            export_node_link_json(compiled, path)
            written[path.name] = path.stat().st_size
        if "graphml" in wants:
            path = out_dir / "intelligence_graph_v0_1.graphml"
            export_graphml(compiled, path)
            written[path.name] = path.stat().st_size
        if "neo4j" in wants:
            written.update(export_neo4j(compiled, out_dir))

    html_path: Path | None = None
    if "html" in wants:
        from blueprint.reports import write_graph_report

        html_path = write_graph_report(root, compiled=compiled)

    if not args.quiet:
        counts = compiled.counts()
        print(
            f"graph: {counts['nodes']} nodes, {counts['edges']} edges "
            f"({counts['null_result_edges']} null-result, "
            f"{counts['support_edges']} counted as support)"
        )
        if written:
            print(f"machine formats -> {out_dir}")
            width = max(len(name) for name in written)
            for name, size in sorted(written.items()):
                print(f"  {name.ljust(width)}  {size:>9,} bytes")
        if html_path is not None:
            print(f"report -> {html_path}  {html_path.stat().st_size:,} bytes")
            print(
                "  self-contained: no external script, stylesheet or font; "
                "null-result edges are dashed red with a legend that says what they mean"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
