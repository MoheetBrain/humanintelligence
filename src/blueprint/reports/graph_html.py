"""The self-contained interactive graph report.

Constraints, all deliberate:

* **No external references.** No CDN script, no remote stylesheet, no web font, no
  remote image. Everything is inline, so the file works from a USB stick, in an air-gapped
  review and in five years. ``tests/test_report_html.py`` asserts there is no ``src=`` or
  ``href=`` pointing at a remote host.
* **Deterministic.** The layout is computed in Python with a fixed seed and the data is
  embedded as sorted JSON, so two runs produce a byte-identical file apart from the
  generation timestamp, which is isolated on one line.
* **Null results are visually distinct, with a legend that says what they mean.** Dashed
  and red, drawn on top, never counted in a support total, and switchable to
  nulls-only. After the effort this sprint spent making nulls first-class in the data
  model, a picture that flattened them back into ordinary edges would undo it at the
  last step — and a reader trusts a picture faster than a table.
* **No score without its coverage.** Every target panel shows claim count, distinct
  sources, human-evidence count, graded and not-assessed facets, zeros, null results,
  evidence gaps and ``reporting_gap_count`` together. A reader must not be able to see a
  well-connected node without also seeing how thin its evidence is.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from blueprint import paths
from blueprint.graph.compile import CompiledGraph, compile_graph
from blueprint.reports.layout import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    compute_layout,
    layer_label_positions,
)

# Node types shown by default. The evidence layer is ~70% of the graph and is dominated
# by one Measurement node per evidence item, which makes the default view unreadable —
# so it is off by default and one click away, rather than absent.
DEFAULT_VISIBLE_LAYERS = ("biological", "intervention")

# Colour per layer. Chosen to stay distinguishable in greyscale print as well, because
# somebody will print this.
LAYER_COLOURS = {
    "evidence": "#6b7b8c",
    "biological": "#2f6f4f",
    "intervention": "#8a5a2b",
}


def _link_for(identifiers: dict[str, Any] | None) -> str | None:
    """A resolvable URL for a source, built from its stored identifiers.

    Built from the identifiers rather than stored as a URL, so the link cannot drift
    from the identifier that was verified against the registry.
    """
    if not isinstance(identifiers, dict):
        return None
    pmid = identifiers.get("pmid")
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    nct = identifiers.get("nct_id") or identifiers.get("nct")
    if nct:
        return f"https://clinicaltrials.gov/study/{nct}"
    doi = identifiers.get("doi")
    if doi:
        return f"https://doi.org/{doi}"
    gcst = identifiers.get("gcst")
    if gcst:
        return f"https://www.ebi.ac.uk/gwas/studies/{gcst}"
    return None


def _build_payload(compiled: CompiledGraph) -> dict[str, Any]:
    """The JSON the page embeds: nodes, edges, positions, coverage and counts."""
    positions = compute_layout(compiled.nodes, compiled.edges)
    claims = {
        node.id: node for node in compiled.nodes if node.node_type == "Claim"
    }
    sources = {
        node.id: node
        for node in compiled.nodes
        if node.layer == "evidence" and node.node_type in {
            "Paper", "Review", "Preprint", "ClinicalTrial", "Dataset", "DatabaseRelease"
        }
    }

    nodes_payload = []
    for node in compiled.nodes:
        x, y = positions.get(node.id, (0, 0))
        entry: dict[str, Any] = {
            "id": node.id,
            "t": node.node_type,
            "l": node.layer,
            "n": node.label,
            "p": node.provenance_class,
            "x": x,
            "y": y,
            "a": node.attributes,
        }
        if node.id in sources:
            link = _link_for(node.attributes.get("identifiers"))
            if link:
                entry["url"] = link
        nodes_payload.append(entry)

    edges_payload = []
    for edge in compiled.edges:
        payload = {
            "s": edge.subject,
            "r": edge.predicate,
            "o": edge.object,
            "l": edge.layer,
            "p": edge.provenance_class,
            "d": edge.direction,
            "dc": edge.direction_context,
            "null": edge.is_null_result,
            "neg": edge.negated_relation,
            "sup": edge.counts_as_support,
            "eff": edge.asserts_effect,
            "c": sorted(edge.claim_ids),
            "ec": edge.evidence_count,
            "sc": edge.distinct_source_count,
            "b": edge.basis,
        }
        edges_payload.append(payload)

    # Claim statements and source titles, so the side panel can show provenance
    # without a second request. Trimmed to what the panel displays.
    claim_detail = {
        cid: {
            "s": node.attributes.get("statement"),
            "t": node.attributes.get("claim_type"),
            "hr": node.attributes.get("human_relevance"),
            "ls": node.attributes.get("life_stage"),
            "bc": node.attributes.get("baseline_context"),
            "u": node.attributes.get("uncertainty_level"),
            "by": node.attributes.get("created_by"),
            "src": sorted(node.source_refs),
            "st": node.attributes.get("status"),
        }
        for cid, node in sorted(claims.items())
    }
    source_detail = {
        sid: {
            "t": node.attributes.get("title"),
            "y": node.attributes.get("year"),
            "a": node.attributes.get("first_author"),
            "c": node.attributes.get("container"),
            "url": _link_for(node.attributes.get("identifiers")),
            "by": node.attributes.get("registered_by") or [],
        }
        for sid, node in sorted(sources.items())
    }

    counts = compiled.counts()
    return {
        "generated_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "canvas": {"w": CANVAS_WIDTH, "h": CANVAS_HEIGHT},
        "layers": [
            {"name": name, "x": x, "y": y, "colour": LAYER_COLOURS.get(name, "#555")}
            for name, x, y in layer_label_positions()
        ],
        "default_layers": list(DEFAULT_VISIBLE_LAYERS),
        "nodes": nodes_payload,
        "edges": edges_payload,
        "claims": claim_detail,
        "sources": source_detail,
        "coverage": compiled.target_coverage,
        "counts": counts,
        "node_types": sorted({n.node_type for n in compiled.nodes}),
        "predicates": sorted({e.predicate for e in compiled.edges}),
    }


def render_graph_report(compiled: CompiledGraph) -> str:
    """Render the whole report as one HTML string."""
    payload = _build_payload(compiled)
    counts = payload["counts"]
    inputs = counts["inputs"]
    data_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    header_counts = (
        f"{inputs.get('sources', 0)} sources &middot; "
        f"{inputs.get('claims', 0)} claims &middot; "
        f"{inputs.get('evidence_items', 0)} evidence items &middot; "
        f"{inputs.get('targets', 0)} targets &middot; "
        f"{inputs.get('assessments', 0)} facet assessments &middot; "
        f"{inputs.get('audits', 0)} audits &middot; "
        f"{inputs.get('state_variables', 0)} state variables"
    )
    graph_counts = (
        f"{counts['nodes']} nodes &middot; {counts['edges']} edges "
        f"({counts['edges_by_provenance_class'].get('claim_derived', 0)} claim-derived, "
        f"{counts['edges_by_provenance_class'].get('reference_data', 0)} reference-data, "
        f"{counts['edges_by_provenance_class'].get('ontology_axiom', 0)} ontology axioms) "
        f"&middot; <strong>{counts['null_result_edges']} null-result edges</strong> "
        f"&middot; {counts['support_edges']} edges counted as support"
    )

    return _TEMPLATE.format(
        generated_on=payload["generated_on"],
        header_counts=header_counts,
        graph_counts=graph_counts,
        canvas_w=CANVAS_WIDTH,
        canvas_h=CANVAS_HEIGHT,
        data_json=data_json,
    )


def write_graph_report(
    root: Path | str | None = None,
    *,
    compiled: CompiledGraph | None = None,
    destination: Path | None = None,
) -> Path:
    """Render and write ``reports/intelligence_graph_v0_1.html``."""
    resolved = paths.resolve_root(root)
    graph = compiled if compiled is not None else compile_graph(resolved)
    target = destination or (resolved / "reports" / "intelligence_graph_v0_1.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_graph_report(graph), encoding="utf-8", newline="\n")
    return target


# ---------------------------------------------------------------------------------
# The template. Braces are doubled for `str.format`; only the named fields above are
# substituted. Everything is inline: no script src, no link href, no web font.
# ---------------------------------------------------------------------------------
_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Intelligence Blueprint — graph v0.1.0 (PRELIMINARY)</title>
<style>
  :root {{
    --bg: #fbfbf9; --ink: #1d1f21; --muted: #5b6268; --rule: #d9d6cf;
    --panel: #ffffff; --null: #b3261e; --support: #2f6f4f; --warn: #8a5a00;
    --evidence: #6b7b8c; --biological: #2f6f4f; --intervention: #8a5a2b;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  header {{ padding: 14px 18px; border-bottom: 1px solid var(--rule); background: #fff; }}
  h1 {{ margin: 0 0 4px; font-size: 17px; letter-spacing: -0.01em; }}
  .counts {{ color: var(--muted); font-size: 12.5px; }}
  .disclaimer {{ margin-top: 8px; padding: 8px 10px; border-left: 3px solid var(--warn);
    background: #fdf8ef; font-size: 12.5px; }}
  .disclaimer strong {{ color: var(--warn); }}
  main {{ display: flex; height: calc(100vh - 148px); min-height: 460px; }}
  #canvas-wrap {{ flex: 1 1 auto; overflow: hidden; position: relative; background:
    repeating-linear-gradient(0deg, #fbfbf9, #fbfbf9 39px, #f4f3ef 39px, #f4f3ef 40px); }}
  svg {{ width: 100%; height: 100%; cursor: grab; display: block; }}
  svg.dragging {{ cursor: grabbing; }}
  #controls {{ flex: 0 0 236px; border-right: 1px solid var(--rule); background: #fff;
    overflow-y: auto; padding: 12px 14px; }}
  #panel {{ flex: 0 0 340px; border-left: 1px solid var(--rule); background: var(--panel);
    overflow-y: auto; padding: 14px; }}
  fieldset {{ border: 0; border-top: 1px solid var(--rule); margin: 0 0 12px; padding: 10px 0 0; }}
  legend {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em;
    color: var(--muted); padding: 0; }}
  label {{ display: block; font-size: 12.5px; margin: 3px 0; cursor: pointer; }}
  input[type=search] {{ width: 100%; padding: 6px 8px; border: 1px solid var(--rule);
    border-radius: 3px; font: inherit; }}
  button {{ font: inherit; font-size: 12px; padding: 4px 8px; border: 1px solid var(--rule);
    border-radius: 3px; background: #fff; cursor: pointer; }}
  button:hover {{ background: #f2f1ec; }}
  .legend-row {{ display: flex; align-items: center; gap: 7px; margin: 5px 0; font-size: 12px; }}
  .swatch {{ width: 22px; height: 0; border-top-width: 2px; border-top-style: solid; flex: 0 0 22px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; flex: 0 0 10px; }}
  .null-note {{ font-size: 11.5px; color: var(--muted); margin: 6px 0 0;
    border-left: 3px solid var(--null); padding-left: 8px; }}
  .node {{ cursor: pointer; }}
  .node:hover circle {{ stroke: #000; stroke-width: 2.5; }}
  .node.selected circle {{ stroke: #000; stroke-width: 3; }}
  .node.dim {{ opacity: 0.12; }}
  .edge.dim {{ opacity: 0.05; }}
  .edge-null {{ stroke: var(--null); stroke-width: 2.1; stroke-dasharray: 7 4; }}
  .edge-support {{ stroke: var(--support); stroke-width: 1.5; }}
  .edge-plain {{ stroke: #9aa0a6; stroke-width: 0.9; }}
  .edge-axiom {{ stroke: #c9c4bb; stroke-width: 0.7; stroke-dasharray: 2 3; }}
  h2 {{ font-size: 13px; margin: 0 0 6px; }}
  .kv {{ display: grid; grid-template-columns: 116px 1fr; gap: 2px 8px; font-size: 12.5px;
    margin: 0 0 10px; }}
  .kv dt {{ color: var(--muted); }}
  .kv dd {{ margin: 0; word-break: break-word; }}
  .cov {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; margin: 8px 0; }}
  .cov div {{ border: 1px solid var(--rule); border-radius: 3px; padding: 5px 7px; font-size: 12px; }}
  .cov b {{ display: block; font-size: 16px; font-weight: 600; }}
  .cov .bad b {{ color: var(--null); }}
  .cov .warn b {{ color: var(--warn); }}
  .claim {{ border-top: 1px solid var(--rule); padding: 7px 0; font-size: 12.5px; }}
  .claim .meta {{ color: var(--muted); font-size: 11.5px; }}
  .tag {{ display: inline-block; font-size: 10.5px; padding: 1px 5px; border-radius: 9px;
    border: 1px solid var(--rule); margin-right: 4px; }}
  .tag.null {{ border-color: var(--null); color: var(--null); }}
  a {{ color: #1a4f8a; }}
  .hint {{ color: var(--muted); font-size: 12px; }}
  #tooltip {{ position: absolute; pointer-events: none; background: #1d1f21; color: #fff;
    padding: 6px 8px; border-radius: 3px; font-size: 11.5px; max-width: 320px;
    opacity: 0; transition: opacity 0.08s; z-index: 10; }}
  footer {{ padding: 8px 18px; border-top: 1px solid var(--rule); color: var(--muted);
    font-size: 11.5px; background: #fff; }}
</style>
</head>
<body>
<header>
  <h1>Intelligence Blueprint — causal graph v0.1.0 <span style="color:var(--warn)">PRELIMINARY</span></h1>
  <div class="counts">{header_counts}</div>
  <div class="counts">{graph_counts}</div>
  <div class="counts">Generated {generated_on} &middot; offline and self-contained &middot; no external scripts, styles or fonts</div>
  <div class="disclaimer">
    <strong>Nothing in this graph is a safety or efficacy claim.</strong>
    An edge records that somebody reported something, with provenance — not that it is
    true, reproducible, or applicable to a healthy adult human. A well-connected node is
    not a well-evidenced one: check the claim count, the distinct source count and the
    coverage figures in the side panel before reading anything into a node's position or
    its number of edges. <strong>Dashed red edges are null results</strong> — a performed
    attempt that detected no effect — and they are excluded from every support count.
  </div>
</header>

<main>
  <div id="controls">
    <fieldset>
      <legend>Search</legend>
      <input type="search" id="search" placeholder="node id, name, or gene symbol" autocomplete="off">
      <p class="hint" id="search-status">&nbsp;</p>
    </fieldset>

    <fieldset>
      <legend>Layers</legend>
      <div id="layer-filters"></div>
    </fieldset>

    <fieldset>
      <legend>Edges</legend>
      <label><input type="checkbox" id="show-null" checked> null results <span style="color:var(--null)">(dashed red)</span></label>
      <label><input type="checkbox" id="show-support" checked> counted as support</label>
      <label><input type="checkbox" id="show-other" checked> other claim-derived</label>
      <label><input type="checkbox" id="show-reference" checked> reference data</label>
      <label><input type="checkbox" id="show-axiom"> ontology axioms</label>
      <p style="margin:8px 0 0"><button id="nulls-only">Show only null results</button></p>
    </fieldset>

    <fieldset>
      <legend>Node types</legend>
      <p style="margin:0 0 6px"><button id="types-all">all</button> <button id="types-none">none</button></p>
      <div id="type-filters"></div>
    </fieldset>

    <fieldset>
      <legend>Legend</legend>
      <div class="legend-row"><span class="dot" style="background:var(--evidence)"></span> evidence layer</div>
      <div class="legend-row"><span class="dot" style="background:var(--biological)"></span> biological layer</div>
      <div class="legend-row"><span class="dot" style="background:var(--intervention)"></span> intervention layer</div>
      <div class="legend-row"><span class="swatch" style="border-top-color:var(--null);border-top-style:dashed"></span> null result</div>
      <div class="legend-row"><span class="swatch" style="border-top-color:var(--support)"></span> counted as support</div>
      <div class="legend-row"><span class="swatch" style="border-top-color:#9aa0a6"></span> claim-derived, not support</div>
      <div class="legend-row"><span class="swatch" style="border-top-color:#c9c4bb;border-top-style:dashed"></span> reference data / axiom</div>
      <p class="null-note">
        A <strong>null result</strong> is a performed and reported attempt that detected
        no effect. It is a finding, not a gap: an untested relationship has no edge at
        all. Null edges never count as support, and a chain containing one is not a
        chain of evidence.
      </p>
      <p class="null-note" style="border-left-color:#9aa0a6">
        <strong>Claim-derived but not support</strong> means the claim states no
        direction, or states <code>no_change</code> or <code>unclear</code>. An absent
        sign is not a positive one.
      </p>
    </fieldset>

    <fieldset>
      <legend>View</legend>
      <p style="margin:0"><button id="reset">Reset view</button></p>
      <p class="hint">Drag to pan, scroll to zoom, click a node for detail, hover an edge for its relation and claims.</p>
    </fieldset>
  </div>

  <div id="canvas-wrap">
    <svg id="graph" viewBox="0 0 {canvas_w} {canvas_h}" preserveAspectRatio="xMidYMid meet">
      <g id="viewport">
        <g id="layer-labels"></g>
        <g id="edges"></g>
        <g id="nodes"></g>
      </g>
    </svg>
    <div id="tooltip"></div>
  </div>

  <div id="panel">
    <h2>Nothing selected</h2>
    <p class="hint">Click a node to see its attributes and provenance. For a target you
    will also get its coverage figures, which are the honest counterweight to how
    connected it looks.</p>
  </div>
</main>

<footer>
  Generated by <code>blueprint.reports.graph_html</code> from the curated records. Every
  edge carries a provenance class; claim-derived edges carry the claim ids that licensed
  them. <code>claim_type: evidence_gap</code> claims appear in the evidence layer only and
  compile to no biological or intervention edge, because an absence of measurement is not
  a finding about biology.
</footer>

<script id="graph-data" type="application/json">{data_json}</script>
<script>
(function () {{
  "use strict";
  var DATA = JSON.parse(document.getElementById("graph-data").textContent);
  var svg = document.getElementById("graph");
  var viewport = document.getElementById("viewport");
  var edgesG = document.getElementById("edges");
  var nodesG = document.getElementById("nodes");
  var labelsG = document.getElementById("layer-labels");
  var panel = document.getElementById("panel");
  var tooltip = document.getElementById("tooltip");
  var wrap = document.getElementById("canvas-wrap");
  var NS = "http://www.w3.org/2000/svg";

  var nodeById = {{}};
  DATA.nodes.forEach(function (n) {{ nodeById[n.id] = n; }});

  var visibleLayers = {{}};
  DATA.layers.forEach(function (l) {{
    visibleLayers[l.name] = DATA.default_layers.indexOf(l.name) !== -1;
  }});
  var visibleTypes = {{}};
  DATA.node_types.forEach(function (t) {{ visibleTypes[t] = true; }});

  function esc(s) {{
    if (s === null || s === undefined) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}

  // ------------------------------------------------------------- filters ----
  var controls = {{
    null: document.getElementById("show-null"),
    support: document.getElementById("show-support"),
    other: document.getElementById("show-other"),
    reference: document.getElementById("show-reference"),
    axiom: document.getElementById("show-axiom")
  }};

  function edgeClass(e) {{
    if (e.null) return "edge-null";
    if (e.p === "ontology_axiom") return "edge-axiom";
    if (e.p !== "claim_derived") return "edge-plain";
    return e.sup ? "edge-support" : "edge-plain";
  }}

  function edgeEnabled(e) {{
    if (e.null) return controls.null.checked;
    if (e.p === "ontology_axiom") return controls.axiom.checked;
    if (e.p !== "claim_derived") return controls.reference.checked;
    return e.sup ? controls.support.checked : controls.other.checked;
  }}

  function nodeVisible(n) {{ return visibleLayers[n.l] && visibleTypes[n.t]; }}

  function render() {{
    while (edgesG.firstChild) edgesG.removeChild(edgesG.firstChild);
    while (nodesG.firstChild) nodesG.removeChild(nodesG.firstChild);

    var drawn = 0, drawnNull = 0;
    // Nulls last so they are never hidden under an ordinary edge.
    var ordered = DATA.edges.slice().sort(function (a, b) {{
      return (a.null ? 1 : 0) - (b.null ? 1 : 0);
    }});
    ordered.forEach(function (e) {{
      var a = nodeById[e.s], b = nodeById[e.o];
      if (!a || !b || !nodeVisible(a) || !nodeVisible(b) || !edgeEnabled(e)) return;
      var line = document.createElementNS(NS, "line");
      line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
      line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
      line.setAttribute("class", "edge " + edgeClass(e));
      line.addEventListener("mouseenter", function (ev) {{ showEdgeTip(ev, e); }});
      line.addEventListener("mouseleave", hideTip);
      edgesG.appendChild(line);
      drawn++;
      if (e.null) drawnNull++;
    }});

    DATA.nodes.forEach(function (n) {{
      if (!nodeVisible(n)) return;
      var g = document.createElementNS(NS, "g");
      g.setAttribute("class", "node");
      g.setAttribute("data-id", n.id);
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", n.x); c.setAttribute("cy", n.y);
      c.setAttribute("r", radiusFor(n));
      c.setAttribute("fill", colourFor(n));
      c.setAttribute("stroke", "#fff");
      c.setAttribute("stroke-width", "1");
      g.appendChild(c);
      if (radiusFor(n) >= 7) {{
        var label = document.createElementNS(NS, "text");
        label.setAttribute("x", n.x + radiusFor(n) + 3);
        label.setAttribute("y", n.y + 3.5);
        label.setAttribute("font-size", "9.5");
        label.setAttribute("fill", "#3a3f44");
        label.textContent = n.n.length > 30 ? n.n.slice(0, 29) + "\\u2026" : n.n;
        g.appendChild(label);
      }}
      g.addEventListener("click", function () {{ select(n.id); }});
      nodesG.appendChild(g);
    }});

    document.getElementById("search-status").textContent =
      drawn + " edges drawn (" + drawnNull + " null)";
  }}

  function colourFor(n) {{
    if (n.l === "evidence") return "var(--evidence)";
    if (n.l === "intervention") return "var(--intervention)";
    return "var(--biological)";
  }}

  function radiusFor(n) {{
    if (n.t === "Target") return 9;
    if (n.t === "StateVariable" || n.t === "ComputationalPrimitive") return 6.5;
    if (n.t === "CognitivePhenotype" || n.t === "Gene") return 6;
    if (n.t === "Measurement" || n.t === "Claim") return 3;
    return 5;
  }}

  // ---------------------------------------------------------- tooltips ------
  function showEdgeTip(ev, e) {{
    var bits = ["<strong>" + esc(e.r) + "</strong>"];
    if (e.null) {{
      bits.push('<span style="color:#ffb4ab">NULL RESULT — a performed attempt that' +
        ' detected no effect' + (e.neg ? " (negating " + esc(e.neg) + ")" : "") +
        '. Not evidence for the target; excluded from support counts.</span>');
    }}
    bits.push(esc(e.s) + " \\u2192 " + esc(e.o));
    if (e.d) bits.push("direction: " + esc(e.d) + (e.dc ? " (" + esc(e.dc) + ")" : ""));
    else if (e.p === "claim_derived") bits.push("no direction stated \\u2014 asserts no change");
    bits.push("provenance: " + esc(e.p));
    if (e.c && e.c.length) bits.push("claims: " + e.c.map(esc).join(", "));
    if (e.ec) bits.push(e.ec + " evidence item(s), " + e.sc + " distinct source(s)");
    if (!e.sup && e.c && e.c.length && !e.null) bits.push("<em>not counted as support</em>");
    tooltip.innerHTML = bits.join("<br>");
    tooltip.style.opacity = "1";
    var r = wrap.getBoundingClientRect();
    tooltip.style.left = Math.min(r.width - 330, ev.clientX - r.left + 12) + "px";
    tooltip.style.top = (ev.clientY - r.top + 12) + "px";
  }}
  function hideTip() {{ tooltip.style.opacity = "0"; }}

  // ------------------------------------------------------- side panel -------
  function select(id) {{
    var n = nodeById[id];
    if (!n) return;
    Array.prototype.forEach.call(nodesG.children, function (g) {{
      g.classList.toggle("selected", g.getAttribute("data-id") === id);
    }});
    var html = ["<h2>" + esc(n.n) + "</h2>"];
    html.push('<dl class="kv">');
    html.push("<dt>id</dt><dd><code>" + esc(n.id) + "</code></dd>");
    html.push("<dt>type</dt><dd>" + esc(n.t) + "</dd>");
    html.push("<dt>layer</dt><dd>" + esc(n.l) + "</dd>");
    html.push("<dt>provenance</dt><dd>" + esc(n.p) + "</dd>");
    if (n.url) html.push('<dt>source</dt><dd><a href="' + esc(n.url) +
      '" target="_blank" rel="noreferrer noopener">open registry record</a></dd>');
    Object.keys(n.a || {{}}).sort().forEach(function (k) {{
      var v = n.a[k];
      if (v === null || v === undefined || v === "" ||
          (Array.isArray(v) && !v.length) || k === "identifiers") return;
      var text = Array.isArray(v) ? v.join(", ") : (typeof v === "object" ? JSON.stringify(v) : String(v));
      if (text.length > 400) text = text.slice(0, 399) + "\\u2026";
      html.push("<dt>" + esc(k) + "</dt><dd>" + esc(text) + "</dd>");
    }});
    html.push("</dl>");

    // Coverage, for a target. Shown before anything that looks like a score, because a
    // reader must not see how connected a target is without seeing how thin it is.
    var cov = DATA.coverage[n.id];
    if (cov) {{
      html.push("<h2>Evidence coverage</h2>");
      html.push('<p class="hint">These are the honest counterweight to how connected' +
        " this target looks. Read them first.</p>");
      html.push('<div class="cov">');
      html.push(box("claims", cov.claim_count, cov.claim_count === 0));
      html.push(box("distinct sources", cov.distinct_source_count, cov.distinct_source_count === 0));
      html.push(box("human-evidence claims", cov.human_claim_count, cov.human_claim_count === 0));
      html.push(box("facets graded", cov.facets_graded, cov.facets_graded === 0));
      html.push(box("facets not assessed", cov.facets_not_assessed, false, cov.facets_not_assessed > 0));
      html.push(box("facets at 0 (searched, nothing found)", cov.facets_zero, false, cov.facets_zero > 0));
      html.push(box("null results", cov.null_result_count, false, cov.null_result_count > 0));
      html.push(box("evidence gaps (never measured)", cov.evidence_gap_count, false, cov.evidence_gap_count > 0));
      html.push(box("reporting gaps (completed, unpublished)", cov.reporting_gap_count, false, cov.reporting_gap_count > 0));
      html.push("</div>");
      if (cov.reporting_gap_refs && cov.reporting_gap_refs.length) {{
        html.push('<p class="hint">Registered and completed without posted results: ' +
          cov.reporting_gap_refs.map(esc).join(", ") +
          ". That is publication bias visible in the data, not an absence of attempts.</p>");
      }}
    }}

    // Incoming and outgoing edges, nulls called out.
    var into = [], out = [];
    DATA.edges.forEach(function (e) {{
      if (e.o === id) into.push(e);
      if (e.s === id) out.push(e);
    }});
    html.push(edgeList("Incoming", into));
    html.push(edgeList("Outgoing", out));
    panel.innerHTML = html.join("");
  }}

  function box(label, value, bad, warn) {{
    var cls = bad ? " class=\\"bad\\"" : (warn ? " class=\\"warn\\"" : "");
    return "<div" + cls + "><b>" + (value === undefined ? "\\u2013" : value) + "</b>" +
      esc(label) + "</div>";
  }}

  function edgeList(title, list) {{
    if (!list.length) return "";
    var nulls = list.filter(function (e) {{ return e.null; }}).length;
    var parts = ["<h2>" + title + " edges (" + list.length +
      (nulls ? ", <span style=\\"color:var(--null)\\">" + nulls + " null</span>" : "") + ")</h2>"];
    list.slice().sort(function (a, b) {{ return (b.null ? 1 : 0) - (a.null ? 1 : 0); }})
      .slice(0, 40).forEach(function (e) {{
      var tags = [];
      if (e.null) tags.push('<span class="tag null">null result</span>');
      if (e.sup) tags.push('<span class="tag">support</span>');
      if (e.eff) tags.push('<span class="tag">asserts effect</span>');
      tags.push('<span class="tag">' + esc(e.p) + "</span>");
      parts.push('<div class="claim">' + tags.join("") +
        "<div><code>" + esc(e.s) + "</code> \\u2192 <strong>" + esc(e.r) +
        "</strong> \\u2192 <code>" + esc(e.o) + "</code></div>");
      if (e.d) parts.push('<div class="meta">direction: ' + esc(e.d) +
        (e.dc ? " \\u2014 " + esc(e.dc) : "") + "</div>");
      if (e.neg) parts.push('<div class="meta">negates: ' + esc(e.neg) + "</div>");
      (e.c || []).slice(0, 4).forEach(function (cid) {{
        var c = DATA.claims[cid];
        if (!c) return;
        parts.push('<div class="meta"><code>' + esc(cid) + "</code>: " + esc(c.s) + "</div>");
        (c.src || []).slice(0, 3).forEach(function (sid) {{
          var s = DATA.sources[sid];
          if (!s) return;
          var link = s.url ? '<a href="' + esc(s.url) +
            '" target="_blank" rel="noreferrer noopener">' + esc(sid) + "</a>" : esc(sid);
          parts.push('<div class="meta">&nbsp;&nbsp;' + link + " \\u2014 " +
            esc(s.t || "") + (s.y ? " (" + esc(s.y) + ")" : "") + "</div>");
        }});
      }});
      parts.push("</div>");
    }});
    if (list.length > 40) parts.push('<p class="hint">' + (list.length - 40) +
      " more not shown.</p>");
    return parts.join("");
  }}

  // ------------------------------------------------------- pan and zoom -----
  var view = {{ x: 0, y: 0, k: 1 }};
  function applyView() {{
    viewport.setAttribute("transform",
      "translate(" + view.x + "," + view.y + ") scale(" + view.k + ")");
  }}
  var dragging = false, lastX = 0, lastY = 0;
  svg.addEventListener("mousedown", function (e) {{
    dragging = true; lastX = e.clientX; lastY = e.clientY; svg.classList.add("dragging");
  }});
  window.addEventListener("mouseup", function () {{
    dragging = false; svg.classList.remove("dragging");
  }});
  window.addEventListener("mousemove", function (e) {{
    if (!dragging) return;
    var scale = {canvas_w} / svg.getBoundingClientRect().width;
    view.x += (e.clientX - lastX) * scale;
    view.y += (e.clientY - lastY) * scale;
    lastX = e.clientX; lastY = e.clientY;
    applyView();
  }});
  svg.addEventListener("wheel", function (e) {{
    e.preventDefault();
    var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    var next = Math.max(0.2, Math.min(9, view.k * factor));
    var r = svg.getBoundingClientRect();
    var scale = {canvas_w} / r.width;
    var px = (e.clientX - r.left) * scale, py = (e.clientY - r.top) * scale;
    view.x = px - (px - view.x) * (next / view.k);
    view.y = py - (py - view.y) * (next / view.k);
    view.k = next;
    applyView();
  }}, {{ passive: false }});
  document.getElementById("reset").addEventListener("click", function () {{
    view = {{ x: 0, y: 0, k: 1 }}; applyView();
  }});

  // ------------------------------------------------------------ controls ----
  var layerBox = document.getElementById("layer-filters");
  DATA.layers.forEach(function (l) {{
    var id = "layer-" + l.name;
    var label = document.createElement("label");
    label.innerHTML = '<input type="checkbox" id="' + id + '"' +
      (visibleLayers[l.name] ? " checked" : "") + '> <span class="dot" style="display:' +
      'inline-block;background:' + l.colour + '"></span> ' + esc(l.name);
    layerBox.appendChild(label);
    label.querySelector("input").addEventListener("change", function (ev) {{
      visibleLayers[l.name] = ev.target.checked; render();
    }});
  }});

  var typeBox = document.getElementById("type-filters");
  DATA.node_types.forEach(function (t) {{
    var label = document.createElement("label");
    label.innerHTML = '<input type="checkbox" checked> ' + esc(t);
    typeBox.appendChild(label);
    label.querySelector("input").addEventListener("change", function (ev) {{
      visibleTypes[t] = ev.target.checked; render();
    }});
  }});
  document.getElementById("types-all").addEventListener("click", function () {{
    Object.keys(visibleTypes).forEach(function (t) {{ visibleTypes[t] = true; }});
    Array.prototype.forEach.call(typeBox.querySelectorAll("input"), function (i) {{ i.checked = true; }});
    render();
  }});
  document.getElementById("types-none").addEventListener("click", function () {{
    Object.keys(visibleTypes).forEach(function (t) {{ visibleTypes[t] = false; }});
    Array.prototype.forEach.call(typeBox.querySelectorAll("input"), function (i) {{ i.checked = false; }});
    render();
  }});
  Object.keys(controls).forEach(function (k) {{
    controls[k].addEventListener("change", render);
  }});
  document.getElementById("nulls-only").addEventListener("click", function () {{
    controls.null.checked = true;
    controls.support.checked = false;
    controls.other.checked = false;
    controls.reference.checked = false;
    controls.axiom.checked = false;
    render();
  }});

  var search = document.getElementById("search");
  search.addEventListener("input", function () {{
    var q = search.value.trim().toLowerCase();
    Array.prototype.forEach.call(nodesG.children, function (g) {{
      var id = g.getAttribute("data-id");
      var n = nodeById[id];
      var hit = !q || id.toLowerCase().indexOf(q) !== -1 ||
        (n.n || "").toLowerCase().indexOf(q) !== -1;
      g.classList.toggle("dim", !hit);
    }});
    Array.prototype.forEach.call(edgesG.children, function (l) {{
      l.classList.toggle("dim", !!q);
    }});
  }});
  search.addEventListener("keydown", function (e) {{
    if (e.key !== "Enter") return;
    var q = search.value.trim().toLowerCase();
    for (var i = 0; i < DATA.nodes.length; i++) {{
      var n = DATA.nodes[i];
      if (n.id.toLowerCase().indexOf(q) !== -1 || (n.n || "").toLowerCase().indexOf(q) !== -1) {{
        select(n.id);
        break;
      }}
    }}
  }});

  DATA.layers.forEach(function (l) {{
    var t = document.createElementNS(NS, "text");
    t.setAttribute("x", l.x); t.setAttribute("y", l.y);
    t.setAttribute("font-size", "15"); t.setAttribute("font-weight", "600");
    t.setAttribute("text-anchor", "middle"); t.setAttribute("fill", l.colour);
    t.textContent = l.name + " layer";
    labelsG.appendChild(t);
  }});

  applyView();
  render();
}})();
</script>
</body>
</html>
"""
