"""Exports and the HTML report must not lose the distinction between a null and a positive.

The HTML tests are the most important in this file. A reader trusts a picture faster
than a table, so a report that drew a performed-and-found-nothing edge the same way it
drew a positive one would undo the whole sprint's work at the last step — and nobody
would notice, because the picture would look fine.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree as ET

import pytest

from blueprint.graph import compile_graph
from blueprint.graph.compile import CompiledGraph
from blueprint.graph.export import (
    NEO4J_EDGE_COLUMNS,
    NEO4J_NODE_COLUMNS,
    export_all,
    export_graphml,
    export_neo4j,
    export_node_link_json,
    load_node_link_json,
)
from blueprint.graph.traversal import null_result_edges
from blueprint.reports.graph_html import render_graph_report
from tests.conftest import REPO_ROOT

RootFactory = Callable[[str | None], Path]
GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"


@pytest.fixture(scope="module")
def live() -> CompiledGraph:
    return compile_graph()


@pytest.fixture(scope="module")
def exported(live: CompiledGraph, tmp_path_factory) -> Path:
    directory = tmp_path_factory.mktemp("export")
    export_all(live, directory)
    return directory


# ------------------------------------------------------- node-link JSON --------

def test_node_link_round_trip(live: CompiledGraph, exported: Path) -> None:
    """Export and read back: every node and edge survives."""
    payload = load_node_link_json(exported / "intelligence_graph_v0_1.json")
    assert len(payload["nodes"]) == len(live.nodes)
    assert len(payload["edges"]) == len(live.edges)
    assert payload["directed"] is True and payload["multigraph"] is True

    original = {(e.subject, e.predicate, e.object): e.as_dict() for e in live.edges}
    for entry in payload["edges"]:
        key = (entry["subject"], entry["predicate"], entry["object"])
        assert key in original, f"{key} appeared from nowhere"
        assert entry == original[key], f"{key} changed in the round trip"


def test_node_link_json_states_what_a_null_edge_means(exported: Path) -> None:
    """A consumer reading the file alone must be told, not left to infer."""
    payload = load_node_link_json(exported / "intelligence_graph_v0_1.json")
    notes = " ".join(payload["notes"]).lower()
    assert "is_null_result" in notes
    assert "excluded" in notes
    assert "evidence_gap" in notes
    assert "safety or efficacy claim" in notes


def test_null_flags_survive_json(live: CompiledGraph, exported: Path) -> None:
    payload = load_node_link_json(exported / "intelligence_graph_v0_1.json")
    nulls = [e for e in payload["edges"] if e["is_null_result"]]
    assert len(nulls) == len(null_result_edges(live.edges))
    for entry in nulls:
        assert entry["counts_as_support"] is False
        assert entry["negated_relation"], "a null edge lost what it negates"


def test_json_export_is_deterministic(live: CompiledGraph, tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    export_node_link_json(live, first)
    export_node_link_json(live, second)
    assert first.read_bytes() == second.read_bytes()


# --------------------------------------------------------------- GraphML -------

def test_graphml_parses_and_declares_its_keys(live: CompiledGraph, exported: Path) -> None:
    tree = ET.parse(exported / "intelligence_graph_v0_1.graphml")
    assert len(tree.findall(f".//{GRAPHML_NS}node")) == len(live.nodes)
    assert len(tree.findall(f".//{GRAPHML_NS}edge")) == len(live.edges)
    declared = {
        key.get("attr.name") for key in tree.findall(f".//{GRAPHML_NS}key")
    }
    for required in ("is_null_result", "counts_as_support", "negated_relation", "predicate"):
        assert required in declared, f"GraphML does not declare {required}"


def test_graphml_carries_the_null_flag(live: CompiledGraph, exported: Path) -> None:
    """GraphML has no container type, so the flag must still arrive as a scalar."""
    text = (exported / "intelligence_graph_v0_1.graphml").read_text(encoding="utf-8")
    expected = len(null_result_edges(live.edges))
    if expected:
        assert text.count('key="e_null">true') == expected


def test_graphml_warns_the_reader_in_a_comment(exported: Path) -> None:
    text = (exported / "intelligence_graph_v0_1.graphml").read_text(encoding="utf-8")
    assert "inverted the finding" in text
    assert "safety or efficacy" in text


def test_graphml_export_is_deterministic(live: CompiledGraph, tmp_path: Path) -> None:
    first, second = tmp_path / "a.graphml", tmp_path / "b.graphml"
    export_graphml(live, first)
    export_graphml(live, second)
    assert first.read_bytes() == second.read_bytes()


# ------------------------------------------------------------------ Neo4j ------

def test_neo4j_csv_headers_match_the_specification(exported: Path) -> None:
    node_header = (exported / "neo4j_nodes.csv").read_text(encoding="utf-8").splitlines()[0]
    edge_header = (exported / "neo4j_edges.csv").read_text(encoding="utf-8").splitlines()[0]
    assert node_header.split(",") == list(NEO4J_NODE_COLUMNS)
    assert edge_header.split(",") == list(NEO4J_EDGE_COLUMNS)


def test_cypher_script_reads_every_csv_column(exported: Path) -> None:
    """A header the script does not read imports as null, silently.

    The script is generated from the same column specification as the headers, and this
    is the test that proves the generation actually covers them.
    """
    cypher = (exported / "neo4j_import.cypher").read_text(encoding="utf-8")
    structural = {"id:ID", ":LABEL", ":START_ID", ":END_ID", ":TYPE"}
    for column in (*NEO4J_NODE_COLUMNS, *NEO4J_EDGE_COLUMNS):
        if column in structural:
            # Structural columns are referenced by name in the MATCH/MERGE clauses.
            assert f"`{column}`" in cypher, f"{column} is not referenced at all"
            continue
        assert f"row.`{column}`" in cypher, f"{column} is never read by the Cypher script"


def test_cypher_script_typecasts_declared_types(exported: Path) -> None:
    """A `:boolean` header read as a string would make every filter true."""
    cypher = (exported / "neo4j_import.cypher").read_text(encoding="utf-8")
    for column in NEO4J_EDGE_COLUMNS:
        if column.endswith(":boolean"):
            assert f"toBoolean(row.`{column}`)" in cypher
        if column.endswith(":int"):
            assert f"toInteger(row.`{column}`)" in cypher


def test_cypher_script_tells_the_reader_how_to_query_support(exported: Path) -> None:
    """Somebody will write a "what supports this" query; it must say to filter."""
    cypher = (exported / "neo4j_import.cypher").read_text(encoding="utf-8")
    assert "counts_as_support = true" in cypher
    assert "EXPORT-ONLY" in cypher
    assert "is_null_result" in cypher


def test_neo4j_rows_match_the_graph(live: CompiledGraph, exported: Path) -> None:
    node_lines = (exported / "neo4j_nodes.csv").read_text(encoding="utf-8").splitlines()
    edge_lines = (exported / "neo4j_edges.csv").read_text(encoding="utf-8").splitlines()
    assert len(node_lines) - 1 == len(live.nodes)
    assert len(edge_lines) - 1 == len(live.edges)


def test_neo4j_csv_quotes_embedded_commas(live: CompiledGraph, tmp_path: Path) -> None:
    """Claim statements contain commas; an unquoted field would shift every column."""
    export_neo4j(live, tmp_path)
    text = (tmp_path / "neo4j_nodes.csv").read_text(encoding="utf-8")
    header_width = len(NEO4J_NODE_COLUMNS)
    import csv

    with open(tmp_path / "neo4j_nodes.csv", encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            assert len(row) == header_width, f"row has {len(row)} fields: {row[:2]}"
    assert '"' in text, "no field needed quoting, which is implausible"


# ------------------------------------------------------------------- HTML ------

@pytest.fixture(scope="module")
def html(live: CompiledGraph) -> str:
    return render_graph_report(live)


def test_html_has_no_remote_references(html: str) -> None:
    """Self-contained: no CDN script, remote stylesheet, web font or remote image.

    The report has to work from a USB stick, in an air-gapped review, and in five years.
    """
    remote = re.findall(r'(?:src|href)\s*=\s*["\'](?:https?:)?//[^"\']*', html)
    assert not remote, f"remote references found: {remote[:5]}"
    assert not re.search(r"<script[^>]*\ssrc\s*=", html), "external script tag"
    assert "<link" not in html, "external stylesheet link"
    assert "@import" not in html, "CSS @import"
    assert "fonts.googleapis" not in html and "cdn." not in html


def test_html_embeds_its_data(html: str) -> None:
    """The data travels with the page, so it renders with no network at all."""
    assert 'id="graph-data"' in html
    match = re.search(
        r'<script id="graph-data" type="application/json">(.*?)</script>', html, re.S
    )
    assert match, "no embedded data block"
    payload = json.loads(match.group(1))
    assert payload["nodes"] and payload["edges"]
    assert payload["counts"]["nodes"] == len(payload["nodes"])


def test_html_marks_null_results_visually_distinct(html: str, live: CompiledGraph) -> None:
    """THE TEST THIS FILE EXISTS FOR.

    A picture that flattened a null back into an ordinary edge would undo the data
    model's whole position, and a reader would never know.
    """
    # A distinct style, not merely a different colour.
    assert ".edge-null" in html
    null_rule = re.search(r"\.edge-null\s*\{([^}]*)\}", html)
    assert null_rule, "no .edge-null rule"
    body = null_rule.group(1)
    assert "stroke-dasharray" in body, "null edges are not dashed"
    assert "--null" in body or "#b3261e" in body, "null edges are not distinctly coloured"
    # And they are drawn on top, so an ordinary edge cannot hide one.
    assert "Nulls last so they are never hidden" in html


def test_html_legend_says_what_a_null_edge_means(html: str) -> None:
    """A distinct style with no explanation is a puzzle, not a disclosure."""
    assert "performed and reported attempt that detected" in html
    assert "an untested relationship has no edge" in html.lower()
    assert "never count as support" in html
    # And the legend actually lists it as a swatch.
    assert re.search(r"border-top-color:var\(--null\)[^>]*></span>\s*null result", html)


def test_html_offers_a_nulls_only_view(html: str) -> None:
    """A reader who wants to see only what failed must be able to."""
    assert 'id="nulls-only"' in html
    assert "Show only null results" in html


def test_html_states_the_disclaimer_and_counts(html: str, live: CompiledGraph) -> None:
    counts = live.counts()
    assert "Nothing in this graph is a safety or efficacy claim" in html
    assert "well-connected node is\n    not a well-evidenced one" in html or (
        "well-connected node is not a well-evidenced one" in html.replace("\n    ", " ")
    )
    assert f"{counts['nodes']} nodes" in html
    assert f"<strong>{counts['null_result_edges']} null-result edges</strong>" in html
    assert "PRELIMINARY" in html


def test_html_shows_coverage_next_to_anything_score_like(html: str) -> None:
    """Per the brief: no well-connected node without how thin its evidence is."""
    assert "Evidence coverage" in html
    assert "honest counterweight to how connected" in html
    for label in (
        "claims",
        "distinct sources",
        "human-evidence claims",
        "facets not assessed",
        "facets at 0 (searched, nothing found)",
        "null results",
        "evidence gaps (never measured)",
        "reporting gaps (completed, unpublished)",
    ):
        assert label in html, f"coverage box missing {label!r}"


def test_html_explains_direction_free_edges(html: str) -> None:
    """An edge that exists but asserts nothing must not read as support."""
    assert "Claim-derived but not support" in html
    assert "An absent\n        sign is not a positive one." in html or (
        "An absent sign is not a positive one." in html.replace("\n        ", " ")
    )


def test_html_is_deterministic(live: CompiledGraph) -> None:
    """Two renders differ only where the generation date appears."""
    first = render_graph_report(live)
    second = render_graph_report(live)
    assert first == second


def test_html_embeds_provenance_for_the_side_panel(html: str) -> None:
    """Clicking a node must show claim statements and source titles without a request."""
    match = re.search(
        r'<script id="graph-data" type="application/json">(.*?)</script>', html, re.S
    )
    payload = json.loads(match.group(1))
    assert payload["claims"], "no claim statements embedded"
    assert payload["sources"], "no source titles embedded"
    sample = next(iter(payload["sources"].values()))
    assert "t" in sample, "source entry has no title"
    # Links are built from the stored identifiers, so they cannot drift from the
    # identifier that was verified against the registry.
    with_links = [s for s in payload["sources"].values() if s.get("url")]
    assert with_links, "no resolvable source links were built from the identifiers"
    assert any("pubmed" in s["url"] or "clinicaltrials" in s["url"] or "doi.org" in s["url"]
               for s in with_links)


# --------------------------------------------------------------------- CLIs ----

def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "graph" / script), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_build_graph_cli_runs(make_root: RootFactory) -> None:
    result = _run("build_graph.py", "--root", str(make_root("valid_minimal")))
    assert result.returncode == 0, result.stderr
    assert "nodes:" in result.stdout
    assert "null-result edges" in result.stdout


def test_build_graph_cli_json(make_root: RootFactory) -> None:
    result = _run("build_graph.py", "--root", str(make_root("valid_minimal")), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "edges_by_provenance_class" in payload
    assert "null_result_edges" in payload


def test_build_graph_cli_reports_sparseness(make_root: RootFactory) -> None:
    """A sparse graph is the honest output of decision D004, and it says so."""
    result = _run("build_graph.py", "--root", str(make_root("valid_minimal")))
    assert "SPARSE" in result.stdout
    assert "refuses an edge without provenance" in result.stdout


def test_export_graph_cli_writes_every_format(make_root: RootFactory, tmp_path: Path) -> None:
    root = make_root("valid_minimal")
    result = _run("export_graph.py", "--root", str(root), "--out", str(tmp_path))
    assert result.returncode == 0, result.stderr
    for name in (
        "intelligence_graph_v0_1.json",
        "intelligence_graph_v0_1.graphml",
        "neo4j_nodes.csv",
        "neo4j_edges.csv",
        "neo4j_import.cypher",
    ):
        assert (tmp_path / name).is_file(), f"{name} not written"


def test_export_graph_cli_html_only(make_root: RootFactory) -> None:
    root = make_root("valid_minimal")
    result = _run("export_graph.py", "--root", str(root), "--only", "html")
    assert result.returncode == 0, result.stderr
    report = root / "reports" / "intelligence_graph_v0_1.html"
    assert report.is_file()
    assert "no external script" in result.stdout


def test_query_graph_cli_lists_and_runs(make_root: RootFactory) -> None:
    from blueprint.store.build import build_store

    root = make_root("valid_minimal")
    build_store(root)

    listing = _run("query_graph.py", "--list")
    assert listing.returncode == 0
    assert "coverage" in listing.stdout and "nulls" in listing.stdout

    ran = _run("query_graph.py", "edges", "--root", str(root), "--json")
    assert ran.returncode == 0, ran.stderr
    json.loads(ran.stdout)

    unknown = _run("query_graph.py", "not-a-query", "--root", str(root))
    assert unknown.returncode == 2
    assert "unknown query" in unknown.stderr


def test_query_graph_cli_free_form_sql(make_root: RootFactory) -> None:
    from blueprint.store.build import build_store

    root = make_root("valid_minimal")
    build_store(root)
    result = _run(
        "query_graph.py", "--root", str(root), "--sql",
        "SELECT COUNT(*) AS n FROM edges WHERE is_null_result",
    )
    assert result.returncode == 0, result.stderr
    assert "n" in result.stdout


def test_query_graph_cli_without_a_store_is_actionable(make_root: RootFactory) -> None:
    result = _run("query_graph.py", "coverage", "--root", str(make_root(None)))
    assert result.returncode == 2
    assert "make store" in result.stderr
