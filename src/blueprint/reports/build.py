"""Build every report this package owns. Entry point for ``make reports``.

Today that is the interactive graph report. It is a separate entry point from
``graph/export_graph.py --html`` on purpose: the exporter is the graph-specific path,
and this is where a future report is added without touching the exporter's CLI.

Both call :func:`blueprint.reports.write_graph_report`, which is deterministic, so
running them in sequence is idempotent rather than contradictory.

The ranking CSV and the audit summary under ``reports/*.md`` belong to
``agent:integration`` and ``agent:red_team``; this module does not write them.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from blueprint import paths
from blueprint.graph import compile_graph
from blueprint.graph.compile import CompiledGraph
from blueprint.reports.graph_html import write_graph_report


@dataclass
class ReportsResult:
    """What a reports build produced."""

    files: dict[str, int] = field(default_factory=dict)
    counts: dict[str, object] = field(default_factory=dict)

    def summary(self) -> str:
        lines: list[str] = []
        width = max((len(name) for name in self.files), default=0)
        for name, size in sorted(self.files.items()):
            lines.append(f"  {name.ljust(width)}  {size:>9,} bytes")
        nulls = self.counts.get("null_result_edges")
        if nulls is not None:
            lines.append(
                f"  {nulls} null-result edge(s) rendered distinctly (dashed red) with a "
                "legend stating that they are performed attempts that found nothing and "
                "are excluded from every support count"
            )
        return "\n".join(lines)


def build_reports(
    root: Path | str | None = None, *, compiled: CompiledGraph | None = None
) -> ReportsResult:
    """Write every report, returning the paths and sizes."""
    resolved = paths.resolve_root(root)
    graph = compiled if compiled is not None else compile_graph(resolved)
    html = write_graph_report(resolved, compiled=graph)
    return ReportsResult(
        files={str(html.relative_to(resolved)): html.stat().st_size},
        counts=graph.counts(),
    )


def main(argv: list[str] | None = None) -> int:
    """``python -m blueprint.reports.build``."""
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = build_reports(args.root)
    if not args.quiet:
        print("reports written:")
        print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
