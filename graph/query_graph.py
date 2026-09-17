#!/usr/bin/env python3
"""Query the DuckDB evidence store: canned questions, or free-form SQL.

Usage
-----
    python graph/query_graph.py --list                    # the canned queries
    python graph/query_graph.py coverage                  # run one by name
    python graph/query_graph.py nulls --json
    python graph/query_graph.py --sql "SELECT * FROM v_coverage_by_facet"
    python graph/query_graph.py --views                   # the views in the store
    python graph/query_graph.py --tables                  # tables and row counts

Design rules:

* **Read-only.** The connection is opened read-only, so a query can never mutate the
  store. Rebuilding is ``make store``, not a side effect of asking a question.
* **The canned queries are the ones worth asking.** Several exist to expose a weakness
  rather than to summarise a strength: ``nulls`` lists performed attempts that found
  nothing, ``gaps`` lists endpoints nobody measured, ``reporting-gaps`` lists registered
  trials that completed without posting results, and ``thin`` ranks targets by how
  little evidence they have rather than how much.
* **A support count is never shown alone.** ``coverage`` puts the claim count next to
  the null, gap and not-assessed counts, because a well-connected target is not a
  well-evidenced one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from blueprint.store.build import connect  # noqa: E402

# name -> (one-line description, SQL). Ordered for --list.
QUERIES: dict[str, tuple[str, str]] = {
    "coverage": (
        "Per target: claims, sources, human evidence, graded/not-assessed facets, "
        "nulls, gaps. Read the gaps before the counts.",
        """
        SELECT symbol, claim_count AS claims, distinct_source_count AS sources,
               human_claim_count AS human, facets_graded AS graded,
               facets_not_assessed AS not_assessed, facets_zero AS zeros,
               null_result_count AS nulls, evidence_gap_count AS gaps,
               reporting_gap_count AS reporting_gaps, coverage_note
        FROM v_claims_per_target
        ORDER BY claims DESC, symbol
        """,
    ),
    "thin": (
        "Targets with the LEAST evidence first — the honest ordering for a "
        "preliminary graph.",
        """
        SELECT symbol, claims, sources, human, graded, not_assessed, nulls, gaps,
               coverage_note
        FROM (
            SELECT symbol, claim_count AS claims, distinct_source_count AS sources,
                   human_claim_count AS human, facets_graded AS graded,
                   facets_not_assessed AS not_assessed, null_result_count AS nulls,
                   evidence_gap_count AS gaps, coverage_note
            FROM v_claims_per_target
        )
        ORDER BY human ASC, claims ASC, sources ASC, symbol
        """,
    ),
    "nulls": (
        "Performed attempts that detected NO effect. A finding, never support.",
        "SELECT * FROM v_null_results_by_target",
    ),
    "gaps": (
        "Endpoints that were never measured (claim_type: evidence_gap). Graph-inert: "
        "no biological or intervention edge.",
        "SELECT * FROM v_evidence_gaps",
    ),
    "reporting-gaps": (
        "Registered interventions that completed without posted results — publication "
        "bias as data.",
        "SELECT * FROM v_reporting_gaps",
    ),
    "facets": (
        "Per facet: assessed, not assessed, searched-and-found-nothing, strong, with "
        "counter-evidence.",
        "SELECT * FROM v_coverage_by_facet",
    ),
    "species": (
        "Evidence items by species, life stage and baseline — where the translation "
        "distance lives.",
        "SELECT * FROM v_evidence_by_species_and_life_stage LIMIT 40",
    ),
    "shared-sources": (
        "Sources registered by more than one agent. What citation-dependence auditing "
        "needs.",
        "SELECT * FROM v_sources_shared_across_agents",
    ),
    "uncited-sources": (
        "Sources registered but cited by no claim (rule V22, informational).",
        "SELECT * FROM v_uncited_sources",
    ),
    "edges": (
        "Edges by layer and provenance class, with null and support counts.",
        "SELECT * FROM v_edges_by_provenance",
    ),
    "unsupported": (
        "Claim-derived edges that do NOT count as support, with the reason. Not "
        "oversights.",
        "SELECT * FROM v_unsupported_edges LIMIT 60",
    ),
    "measurability": (
        "State variables per domain by best available human proxy, and how many have an "
        "unknown response shape.",
        "SELECT * FROM v_state_variable_measurability",
    ),
    "human-relevance": (
        "Claims by translation.human_relevance — how much is human evidence at all.",
        "SELECT * FROM v_claims_by_human_relevance",
    ),
    "audits": (
        "Audit records per target, with checks flagged and failed and the verdict.",
        """
        SELECT scope_id, audited_by, verdict, check_count, checks_flagged,
               checks_failed, finding_count, critical_findings, major_findings,
               adjustment_count, claim_status_change_count
        FROM audits
        ORDER BY scope_id
        """,
    ),
    "effect-claims": (
        "Every edge that asserts an effect, with the claim types behind it (rule V16).",
        """
        SELECT subject, predicate, object, direction, claim_ids, claim_types,
               distinct_source_count
        FROM edges
        WHERE asserts_effect
        ORDER BY subject, predicate, object
        """,
    ),
}


def _render_table(columns: list[str], rows: list[tuple]) -> str:
    """Render rows as a fixed-width table."""
    if not rows:
        return "(no rows)"
    cells = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in cells:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], min(len(value), 58))
    lines = ["  ".join(c.ljust(widths[i])[: widths[i]] for i, c in enumerate(columns))]
    lines.append("  ".join("-" * w for w in widths))
    for row in cells:
        lines.append("  ".join(v.ljust(widths[i])[: widths[i]] for i, v in enumerate(row)))
    lines.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", nargs="?", help="a canned query name (see --list)")
    parser.add_argument("--sql", help="free-form SQL (read-only)")
    parser.add_argument("--list", action="store_true", help="list the canned queries")
    parser.add_argument("--views", action="store_true", help="list the views in the store")
    parser.add_argument("--tables", action="store_true", help="list tables with row counts")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--limit", type=int, default=0, help="cap the rows printed")
    parser.add_argument("--root", default=None, help="repository root (default: discovered)")
    args = parser.parse_args(argv)

    if args.list:
        width = max(len(name) for name in QUERIES)
        print(f"{len(QUERIES)} canned queries:")
        for name, (description, _sql) in QUERIES.items():
            print(f"  {name.ljust(width)}  {description}")
        return 0

    try:
        connection = connect(args.root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        if args.tables:
            rows = connection.execute(
                "SELECT table_name, table_type FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_type, table_name"
            ).fetchall()
            payload = []
            for name, kind in rows:
                count = connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                payload.append({"name": name, "type": kind, "rows": count})
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(_render_table(["name", "type", "rows"],
                                    [(p["name"], p["type"], p["rows"]) for p in payload]))
            return 0

        if args.views:
            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'VIEW' ORDER BY table_name"
            ).fetchall()
            names = [r[0] for r in rows]
            if args.json:
                print(json.dumps(names, indent=2))
            else:
                print(f"{len(names)} view(s):")
                for name in names:
                    print(f"  {name}")
            return 0

        if args.sql:
            sql = args.sql
            description = "free-form SQL"
        elif args.query:
            if args.query not in QUERIES:
                print(
                    f"unknown query {args.query!r}; known: {sorted(QUERIES)}",
                    file=sys.stderr,
                )
                return 2
            description, sql = QUERIES[args.query]
        else:
            parser.print_help()
            return 0

        if args.limit:
            sql = f"SELECT * FROM ({sql}) LIMIT {int(args.limit)}"
        try:
            cursor = connection.execute(sql)
        except Exception as exc:  # noqa: BLE001 - a user's SQL error is not a crash
            print(f"query failed: {exc}", file=sys.stderr)
            return 1
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()

        if args.json:
            print(
                json.dumps(
                    [dict(zip(columns, row)) for row in rows],
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )
        else:
            if args.query:
                print(f"# {description}")
                print()
            print(_render_table(columns, rows))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
