"""Generated reports.

``reports/`` is generated-only: no agent hand-edits anything in it. This package holds
the generators.

* :mod:`blueprint.reports.layout`     deterministic node placement
* :mod:`blueprint.reports.graph_html` the self-contained interactive graph report

The one rule that governs everything here: **a picture must not flatten a null result
back into an ordinary edge.** The data model spent this sprint making nulls
first-class, and a visualisation that draws a performed-and-found-nothing edge the same
way it draws a positive one would undo that at the last step, where it matters most —
because a reader trusts a picture faster than a table.
"""

from __future__ import annotations

from blueprint.reports.graph_html import render_graph_report, write_graph_report

__all__ = ["render_graph_report", "write_graph_report"]
