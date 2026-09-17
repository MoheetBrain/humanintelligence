#!/usr/bin/env python3
"""Give MCP-tool-derived data the same provenance as HTTP-derived data.

Why this exists
---------------
The provenance spine assumes a registry response can be snapshotted immutably and
checked against ``data/raw/MANIFEST.jsonl``. That holds for anything fetched over HTTP
by the ``fetch_*`` scripts. It does **not** hold for data an agent obtains through an
MCP tool (ChEMBL, PubMed, ClinicalTrials.gov wrappers): the tool returns a payload to
the agent's context and writes nothing to disk, so the data arrives unprovenanced.

`agent:power` hit the consequence squarely: rule V9 exempts a database-derived number
only when the record names a pinned ``SRC:DB:*`` source, and under resolution R1 such a
source verifies only against a manifest snapshot. With no snapshot possible, ChEMBL
clinical-development facts could enter the repository *only* as unprovenanced strings.

This script closes that hole. An agent pipes the tool payload in, names the registry and
the release, and gets a snapshot plus a manifest entry indistinguishable from an HTTP
fetch — except that ``retrieval.method`` records that it came via a tool, which is a
material difference a reader should be able to see.

Usage
-----
    some_tool_output.json | python scripts/record_tool_snapshot.py \\
        --registry chembl --release ChEMBL_37 --tool mcp:chembl.get_mechanism \\
        --query '{"target_chembl_id": "CHEMBL224"}'

Prints the snapshot path and the source id to register. Exit 1 if the payload is not
valid JSON — an unparseable payload is not evidence.

Honesty boundary
----------------
This records *what the tool returned*, not that the tool returned it truthfully. It
makes an agent's database read reproducible and attributable; it cannot make it correct.
A snapshot recorded here carries `provenance_class: tool_mediated`, and the red team
should treat a tool-mediated database fact as weaker than the same fact read from a
primary source the agent actually opened.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from _provenance import (  # type: ignore[import-not-found]
    REPO_ROOT,
    utc_now,
    write_snapshot,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--registry", required=True, help="registry name, e.g. chembl, pubmed, ctgov")
    parser.add_argument("--release", help="release/version string, e.g. ChEMBL_37 (becomes part of the source id)")
    parser.add_argument("--tool", required=True, help="the MCP tool that produced this payload")
    parser.add_argument("--query", default="{}", help="JSON object describing what was asked for")
    parser.add_argument("--file", help="read the payload from this file instead of stdin")
    args = parser.parse_args(argv)

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    try:
        payload: Any = json.loads(raw)
    except ValueError as error:
        print(f"payload is not valid JSON ({error}); an unparseable payload is not evidence", file=sys.stderr)
        return 1

    try:
        query = json.loads(args.query)
        if not isinstance(query, dict):
            raise ValueError("query must be a JSON object")
    except ValueError as error:
        print(f"--query must be a JSON object: {error}", file=sys.stderr)
        return 1

    envelope = {
        "provenance_class": "tool_mediated",
        "tool": args.tool,
        "registry": args.registry,
        "release": args.release,
        "query": query,
        "recorded_at": utc_now(),
        "payload": payload,
    }
    snapshot = write_snapshot(
        args.registry,
        envelope,
        url=f"mcp://{args.tool}",
        query={"tool": args.tool, "release": args.release, **query},
        name_hint=(args.release or "tool").replace(":", "-"),
    )

    source_id = f"SRC:DB:{args.registry}:{args.release}" if args.release else None
    print(f"snapshot: {snapshot.relative_to(REPO_ROOT)}")
    if source_id:
        print(f"register: {source_id}")
        print("  source_type: database_release")
        print(f"  retrieval.method: mcp_tool ({args.tool})")
    else:
        print("no --release given, so no SRC:DB id is implied; pass --release to make the")
        print("release citable and verifiable under rule V6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
