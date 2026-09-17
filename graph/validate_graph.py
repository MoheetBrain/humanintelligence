#!/usr/bin/env python3
"""Validate the ontology, schemas, records and provenance rules (contract §8).

This CLI is the executable form of docs/DATA_CONTRACT.md. Where the two disagree, that
is a bug to be reported, not a licence to improvise.

Usage
-----
    python graph/validate_graph.py                  # report; exit 1 on any error
    python graph/validate_graph.py --strict         # warnings become errors
    python graph/validate_graph.py --json           # machine-readable report on stdout
    python graph/validate_graph.py --quiet          # exit code only
    python graph/validate_graph.py --root PATH      # validate a fixture tree
    python graph/validate_graph.py --rule V16 V21   # run only these rules
    python graph/validate_graph.py --list-rules     # what is implemented
    python graph/validate_graph.py --update-lock    # append new claim ids to the lock

Design rules:

* **An empty repository exits 0.** Zero records is a correct state for Sprint 1, and the
  summary says "0 claims, 0 sources" rather than implying something is missing.
* **Human output is grouped by rule with counts, at most ten examples per rule.** An
  agent fixing records needs the shape of the problem, not a thousand lines.
* **Every message names the record and what to do.** For an illegal triple that means
  the claim id, the offending triple, which side failed and the legal alternatives —
  domain agents fix records against these messages.
* **``--update-lock`` only ever appends.** Provenance is append-only (contract P6): the
  lock is never rewritten, never sorted in place, and an id is never removed.

Phase 2 adds ``graph/build_graph.py``, ``graph/query_graph.py`` and
``graph/export_graph.py``; this file stays the validation entry point.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from a checkout without installing the package.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from blueprint import paths, validate  # noqa: E402
from blueprint.violations import Violation  # noqa: E402

MAX_EXAMPLES_PER_RULE = 10

LOCK_HEADER = (
    "# Claim registry lock — APPEND-ONLY.\n"
    "#\n"
    "# One claim id per line, in the order it was first seen. This file is the\n"
    "# mechanism behind contract P6 and rule V13: the red team can downgrade a claim,\n"
    "# never delete it. A claim id that appears here and no longer exists in\n"
    "# evidence/claims/ is a validation failure, so provenance cannot be erased by\n"
    "# quietly removing a record.\n"
    "#\n"
    "# Written only by `python graph/validate_graph.py --update-lock`, which appends\n"
    "# and never rewrites. Do not sort, deduplicate or hand-edit this file: the order\n"
    "# is history. Withdrawal is `status: withdrawn` plus a superseding audit finding\n"
    "# (rule V14), not a deletion.\n"
)


def format_report(report: validate.ValidationReport, *, max_examples: int = MAX_EXAMPLES_PER_RULE) -> str:
    """Render a human-readable report, grouped by rule id."""
    lines: list[str] = []
    counts = report.counts
    lines.append(f"repository: {report.root}")
    lines.append(
        "records:    "
        f"{counts.get('sources', 0)} sources, "
        f"{counts.get('claims', 0)} claims, "
        f"{counts.get('evidence_items', 0)} evidence items, "
        f"{counts.get('targets', 0)} targets, "
        f"{counts.get('assessments', 0)} assessments, "
        f"{counts.get('audits', 0)} audits"
    )
    lines.append(
        "ontology:   "
        f"{counts.get('state_variables', 0)} state variables, "
        f"{counts.get('definitional_edges', 0)} definitional edges, "
        f"{counts.get('interventions', 0)} intervention entities, "
        f"{counts.get('state_variable_annotations', 0)} annotations"
    )
    lines.append(
        f"registry:   {counts.get('seed_targets', 0)} seed targets, "
        f"{counts.get('locked_claim_ids', 0)} locked claim ids, "
        f"{counts.get('shared_sources', 0)} sources registered by more than one agent"
    )
    if report.verification_summary:
        detail = ", ".join(f"{k}={v}" for k, v in report.verification_summary.items())
        lines.append(f"sources verified: {detail}")
    else:
        lines.append(
            "sources verified: no verification index "
            "(run `make fetch-sources`; needs network)"
        )
    lines.append(f"rules run:  {len(report.rules_run)} ({', '.join(report.rules_run)})")
    lines.append("")

    grouped = report.by_rule()
    if not grouped:
        if counts.get("claims", 0) == 0 and counts.get("sources", 0) == 0:
            lines.append(
                "PASS — nothing to validate: 0 claims, 0 sources. An empty repository is "
                "a correct state for Sprint 1, not a missing one."
            )
        else:
            lines.append("PASS — no violations.")
        return "\n".join(lines)

    catalogue = validate.rule_catalogue()
    for rule_id, violations in grouped.items():
        # Counted per severity rather than by subtraction: `info` is neither an error
        # nor a warning, and labelling it one would misreport a finding that never
        # fails a run.
        errors = sum(1 for v in violations if v.severity == "error")
        warnings = sum(1 for v in violations if v.severity == "warning")
        infos = sum(1 for v in violations if v.severity == "info")
        headline = f"{rule_id}: {len(violations)} finding(s)"
        detail = [
            f"{count} {name}"
            for count, name in ((errors, "error"), (warnings, "warning"), (infos, "info"))
            if count
        ]
        if len(detail) > 1 or infos or warnings:
            headline += f" ({', '.join(detail)})"
        lines.append(headline)
        description = catalogue.get(rule_id)
        if description:
            lines.append(f"    {description}")
        for violation in violations[:max_examples]:
            located = violation.path
            if violation.record_id:
                located = f"{located}  [{violation.record_id}]"
            lines.append(f"  - {located}")
            lines.append(f"    {violation.message}")
        if len(violations) > max_examples:
            lines.append(
                f"  ... and {len(violations) - max_examples} more under {rule_id} "
                "(use --json for the full list)"
            )
        lines.append("")

    total_errors = sum(1 for v in report.violations if v.severity == "error")
    total_warnings = len(report.warnings)
    total_infos = len(report.infos)
    lines.append(
        f"TOTAL: {len(report.violations)} finding(s) across {len(grouped)} rule(s) — "
        f"{total_errors} error, {total_warnings} warning, {total_infos} info"
    )
    if report.strict:
        lines.append(
            "--strict: warnings are treated as errors; info findings never fail a run."
        )
    if not report.ok:
        lines.append("FAIL")
    elif total_warnings or total_infos:
        lines.append(
            "PASS — nothing failing. "
            + ("Warnings present. " if total_warnings else "")
            + ("Info findings are not defects in any state of the repository."
               if total_infos else "")
        )
    else:
        lines.append("PASS")
    return "\n".join(lines)


def update_lock(report_root: Path, claim_ids: list[str], *, quiet: bool = False) -> int:
    """Append claim ids not already in the lock. Never removes, never rewrites.

    Creates the lock with its explanatory header when it does not exist.
    ``evidence/claims/`` is not owned by ``agent:ontology``, so this is the only code
    path that writes there and it runs only when explicitly asked.
    """
    lock = paths.claim_registry_lock(report_root)
    existing: list[str] = []
    if lock.is_file():
        for line in lock.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                existing.append(stripped.split()[0])
    else:
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(LOCK_HEADER, encoding="utf-8", newline="\n")
        if not quiet:
            print(f"created {lock} (append-only)")

    known = set(existing)
    new = [claim_id for claim_id in claim_ids if claim_id not in known]
    if not new:
        if not quiet:
            print(f"lock up to date: {len(existing)} claim id(s), 0 appended")
        return 0
    with open(lock, "a", encoding="utf-8", newline="\n") as handle:
        for claim_id in new:
            handle.write(f"{claim_id}\n")
    if not quiet:
        print(f"appended {len(new)} claim id(s) to {lock} ({len(existing) + len(new)} total)")
    return len(new)


def main(argv: list[str] | None = None) -> int:
    """Run the validator. Returns 0 when clean, 1 when there are failing violations."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors (gates G2/G3 run with this)",
    )
    parser.add_argument("--quiet", action="store_true", help="print nothing; exit code only")
    parser.add_argument("--json", action="store_true", help="machine-readable report on stdout")
    parser.add_argument("--root", default=None, help="repository root to validate (default: discovered)")
    parser.add_argument(
        "--rule",
        nargs="*",
        metavar="ID",
        help="run only these rule ids (e.g. --rule V16 V21)",
    )
    parser.add_argument(
        "--update-lock",
        action="store_true",
        help="append new claim ids to evidence/claims/claim_registry.lock (never removes)",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="print the implemented rules and exit 0",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=MAX_EXAMPLES_PER_RULE,
        help=f"examples shown per rule in human output (default {MAX_EXAMPLES_PER_RULE})",
    )
    args = parser.parse_args(argv)

    if args.list_rules:
        catalogue = validate.rule_catalogue()
        if args.json:
            print(json.dumps(catalogue, indent=2, sort_keys=True))
        else:
            print(f"{len(catalogue)} rule(s) implemented:")
            for rule_id, description in catalogue.items():
                print(f"  {rule_id:6s} {description}")
        return 0

    only = tuple(args.rule) if args.rule else None
    if only:
        unknown = sorted(set(only) - set(validate.REGISTRY))
        if unknown:
            print(
                f"unknown rule id(s) {unknown}; implemented: {sorted(validate.REGISTRY)}",
                file=sys.stderr,
            )
            return 2

    report = validate.run(args.root, strict=args.strict, only=only)

    if args.update_lock:
        update_lock(report.root, sorted(validate.build_context(args.root).claims), quiet=args.quiet)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    elif not args.quiet:
        print(format_report(report, max_examples=args.max_examples))

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
