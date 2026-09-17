"""Command-line entry point for the ranking model.

Invoked through ``models/ranking/rank_targets.py``, which is what the ``Makefile``
calls (``make rank``).

Exit codes
----------
``0``  A report was written, **or** there is genuinely nothing to rank yet and
       ``--require-data`` was not passed. The pre-data state is expected in Sprint 1
       and is reported loudly on stderr rather than treated as a build failure.
``2``  Bad invocation, or the specification files are missing or inconsistent.
``3``  Nothing to rank and ``--require-data`` was passed (the strict/CI form).
``4``  The requested repository reader is unavailable.

The one behaviour this CLI will never have: producing a report from data it does not
have. With no facet assessments in the repository it prints what is missing, names
who owns the missing artefacts, and stops.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blueprint.ranking.information_gain import facet_information_gain
from blueprint.ranking.inputs import (
    RepositoryInputs,
    RepositoryLoaderUnavailable,
    from_repository,
    from_repository_direct,
)
from blueprint.ranking.report import write_report
from blueprint.ranking.rubric import SpecError, load_model_spec
from blueprint.ranking.score import cap_sensitivity, score_cohort

__all__ = ["build_parser", "main"]

DEFAULT_ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    """The argument parser, exposed so tests can exercise it directly."""
    parser = argparse.ArgumentParser(
        prog="rank_targets",
        description=(
            "Run the uncertainty + ranking model over audited targets and write "
            "reports/target_ranking_v0_1.csv (PRELIMINARY). Offline; no network access."
        ),
        epilog=(
            "The output is a prioritisation of what to analyse next computationally. "
            "It is not a claim about biology, efficacy or safety, and it contains no "
            "protocol, dose, route or regimen."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root (default: the repository containing this module).",
    )
    parser.add_argument(
        "--reader",
        choices=("auto", "loaders", "direct"),
        default="auto",
        help=(
            "Where inputs come from. 'loaders' uses blueprint.loaders (owned by "
            "agent:ontology); 'direct' uses the contract-literal YAML fallback; "
            "'auto' (default) prefers loaders and falls back to direct, recording "
            "which was used in the report sidecar."
        ),
    )
    parser.add_argument("--seed", type=int, default=None, help="Override the spec's master seed.")
    parser.add_argument(
        "--draws", type=int, default=None, help="Override the spec's Monte Carlo draw count."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Override the output directory (default: <root>/reports).",
    )
    parser.add_argument(
        "--generated-on",
        default=None,
        help="ISO date stamped on every row (default: today, UTC). For reproducible diffs.",
    )
    parser.add_argument(
        "--no-cap-sensitivity",
        action="store_true",
        help=(
            "Skip the polarity_aware-vs-symmetric_caps sensitivity run (contract §5.4). "
            "Faster, but leaves rank_delta_symmetric_caps empty and the asymmetry "
            "unmeasured."
        ),
    )
    parser.add_argument(
        "--no-information-gain",
        action="store_true",
        help="Skip the information-gain sweep (faster; leaves most_informative_facet empty).",
    )
    parser.add_argument(
        "--no-audit-adjustments",
        action="store_true",
        help=(
            "Do not apply red-team downgrades to input levels. Diagnostic only: use it "
            "to measure what the audit changed, never to produce a published report."
        ),
    )
    parser.add_argument(
        "--require-data",
        action="store_true",
        help="Exit 3 instead of 0 when there is nothing to rank (for CI).",
    )
    return parser


def _load_inputs(root: Path, reader: str) -> tuple[RepositoryInputs | None, int]:
    """Load inputs per the ``--reader`` choice. Returns ``(inputs, exit_code)``."""
    if reader in ("loaders", "auto"):
        try:
            return from_repository(root), 0
        except RepositoryLoaderUnavailable as error:
            if reader == "loaders":
                print(f"error: {error}", file=sys.stderr)
                return None, 4
            print(
                "notice: blueprint.loaders is not available yet; falling back to the "
                "contract-literal YAML reader (recorded as reader=direct_yaml_fallback "
                "in the report sidecar).",
                file=sys.stderr,
            )
    return from_repository_direct(root), 0


def _report_nothing_to_rank(inputs: RepositoryInputs, root: Path) -> None:
    """Explain precisely what is missing, and who owns it."""
    n_targets = len(inputs.targets)
    n_claims = len(inputs.claims)
    print(
        "\n".join(
            [
                "",
                "=" * 78,
                "NOTHING TO RANK YET — no report was written, and no data was invented.",
                "=" * 78,
                f"repository            : {root}",
                f"reader                : {inputs.reader}",
                f"targets in registry   : {n_targets}",
                f"claims resolvable     : {n_claims}",
                "facet assessments     : 0 targets carry a graded facet",
                "",
                "The ranking model consumes facet assessments at",
                "  atlases/{domain}/assessments/{SYMBOL}.yaml   (owners: agent:alphacognition,",
                "                                                agent:brakes, agent:power,",
                "                                                agent:comparative)",
                "and red-team audits at",
                "  evidence/audits/red_team/{SYMBOL}.yaml       (owner: agent:red_team)",
                "",
                "Until those exist there is nothing to aggregate. This is the expected",
                "Sprint-1 pre-data state, not an error: the model refuses to emit a table",
                "of priors dressed up as a result.",
                "",
                "The model itself is exercised by its own test suite on synthetic inputs:",
                "  .venv/bin/python -m pytest tests/test_ranking_*.py tests/test_uncertainty_*.py",
                "=" * 78,
                "",
            ]
        ),
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the ranking model end-to-end. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    try:
        spec = load_model_spec(root)
    except SpecError as error:
        print(f"error: specification problem\n{error}", file=sys.stderr)
        return 2

    inputs, code = _load_inputs(root, args.reader)
    if inputs is None:
        return code

    for note in inputs.notes:
        print(f"warning: {note}", file=sys.stderr)

    if not inputs.targets_with_assessments:
        _report_nothing_to_rank(inputs, root)
        return 3 if args.require_data else 0

    result = score_cohort(
        inputs,
        spec,
        n_draws=args.draws,
        seed=args.seed,
        apply_audit_adjustments=not args.no_audit_adjustments,
    )
    gains = (
        None
        if args.no_information_gain
        else facet_information_gain(
            result, inputs, apply_audit_adjustments=not args.no_audit_adjustments
        )
    )
    caps = (
        None
        if args.no_cap_sensitivity
        else cap_sensitivity(
            inputs,
            spec,
            n_draws=args.draws,
            seed=args.seed,
            apply_audit_adjustments=not args.no_audit_adjustments,
        )
    )
    artefacts = write_report(
        result,
        inputs,
        gains,
        root=root,
        reports_dir=args.reports_dir,
        generated_on=args.generated_on,
        caps=caps,
    )

    unaudited = [t.target_id for t in result.targets if not t.is_audited]
    print(
        "\n".join(
            [
                f"wrote {artefacts.csv_path} ({artefacts.n_rows} rows, status=PRELIMINARY)",
                f"wrote {artefacts.meta_path}",
                f"reader={inputs.reader} seed={result.seed} draws={result.n_draws} "
                f"calibration={spec.versions.get('calibration_status')}",
                f"composite operator: {spec.primary_aggregation} "
                "(conjunction of six conditions, joint probability under independence)",
                "pairwise aggregation sensitivity (Kendall tau-b): "
                + ", ".join(
                    f"{k}={v:.3f}" for k, v in sorted(result.pairwise_sensitivity.items())
                ),
            ]
        )
    )
    _report_coverage(result, artefacts.meta, file=sys.stderr)
    _report_disclosures(artefacts.meta, file=sys.stderr)
    _report_cap_sensitivity(caps, file=sys.stderr)
    if unaudited:
        print(
            f"warning: {len(unaudited)} ranked target(s) carry no red-team audit and are "
            f"tiered as tier_3_insufficient_coverage: {', '.join(unaudited)}",
            file=sys.stderr,
        )
    print(
        "reminder: this table prioritises further COMPUTATIONAL analysis. It is not a "
        "claim about biology or safety and contains no protocol, dose or regimen.",
        file=sys.stderr,
    )
    return 0


def _report_disclosures(meta, *, file) -> None:
    """Print the report's disclosures where a reader of the numbers will see them.

    A caveat that lives only in `models/` is a caveat nobody reads. Both of these
    change how a score should be read and neither is visible from the numbers.
    """
    disclosures = meta.get("disclosures") or []
    if not disclosures:
        return
    lines = ["", "-" * 78, "DISCLOSURES — these change how the numbers should be read", "-" * 78]
    for index, entry in enumerate(disclosures, 1):
        lines.append(f"{index}. [{entry.get('severity', '').upper()}] {entry.get('id')}")
        lines.append(f"   applies to: {entry.get('applies_to')}")
        statement = str(entry.get("statement", ""))
        words, current = statement.split(), ""
        for word in words:
            if len(current) + len(word) + 1 > 74:
                lines.append(f"   {current}")
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            lines.append(f"   {current}")
    lines.append("-" * 78)
    print("\n".join(lines), file=file)

def _report_cap_sensitivity(caps, *, file) -> None:
    """State the capping asymmetry and what it cost, per contract §5.4.

    The contract's two obligations are that the asymmetry is stated wherever ranks are
    reported, and that its size is measured rather than assumed. This prints both.
    """
    if caps is None:
        print(
            "warning: cap sensitivity was not computed (--no-cap-sensitivity), so the "
            "precautionary capping asymmetry required by contract §5.4 is unmeasured for "
            "this run.",
            file=file,
        )
        return
    lines = [
        "",
        "-" * 78,
        "CAPPING ASYMMETRY (contract §5.4) — measured, not assumed",
        "-" * 78,
        "Methodological-weakness caps bite only in the direction that favours the",
        "target. That is a precaution against over-optimism, and it is not neutral: it",
        "under-ranks a promising target whose evidence is weak in BOTH directions.",
        "",
        f"caps derived                : {caps.n_caps_derived}",
        f"policy re-application       : {'no-op (graders had already applied §5.4)' if caps.polarity_aware_was_a_no_op else 'CHANGED A GRADE — a grader did not apply §5.4'}",
        f"tau-b polarity vs symmetric : "
        + ("undefined" if caps.kendall_tau_b != caps.kendall_tau_b else f"{caps.kendall_tau_b:.3f}"),
        f"rank movement threshold     : {caps.threshold} positions",
    ]
    if caps.rank_delta:
        lines.append("rank_delta (symmetric - polarity_aware; negative = precaution costs rank):")
        for target_id, delta in caps.rank_delta.items():
            flag = "  <-- SENSITIVE" if target_id in caps.sensitive_targets else ""
            lines.append(f"  {target_id:22s} {delta:+.2f}{flag}")
    else:
        lines.append("rank_delta                  : no target had a methodological cap derived")
    if caps.sensitive_targets:
        lines += [
            "",
            "FINDING: rank is sensitive to the precautionary capping rule for "
            + ", ".join(caps.sensitive_targets),
            "This is a finding about the method, not a defect: read those targets'",
            "phylogenetic_control evidence directly rather than trusting the rank.",
        ]
    lines.append("-" * 78)
    print("\n".join(lines), file=file)

def _report_coverage(result, meta, *, file) -> None:
    """Print the coverage picture prominently enough that it cannot be skimmed past.

    Sparse coverage is the Sprint-1 norm and the single most important caveat on the
    table: a rank computed from a third of the facet catalogue is largely a statement
    about curation order. The block below is printed on every successful run, and the
    same numbers are in the report sidecar under ``coverage_summary``.
    """
    summary = meta.get("coverage_summary") or {}
    if not summary.get("n_targets"):
        return
    slots = int(summary.get("total_facet_slots", 0)) or 1
    assessed = int(summary.get("total_facets_assessed", 0))
    below = summary.get("targets_below_min_coverage") or []
    lines = [
        "",
        "-" * 78,
        "COVERAGE — read this before reading the ranking",
        "-" * 78,
        f"facet slots filled          : {assessed}/{slots} ({assessed / slots:.1%})",
        f"coverage min / median / max : {summary.get('coverage_min')} / "
        f"{summary.get('coverage_median')} / {summary.get('coverage_max')}",
        f"below min_coverage ({summary.get('min_coverage_threshold')})    : "
        f"{summary.get('n_targets_below_min_coverage')}/{summary.get('n_targets')} targets"
        + (f" -> {', '.join(below)}" if below and len(below) <= 12 else ""),
        f"unaudited targets           : {summary.get('n_targets_unaudited')}/{summary.get('n_targets')}",
        f"facets 'searched, nothing found' : {summary.get('total_facets_level_zero')}"
        "   (a documented negative, NOT the same as not_assessed)",
        f"facets with counter_level >= 2   : {summary.get('total_facets_contradicted')}"
        "   (tested and contradicted)",
        f"facets never graded              : {summary.get('total_facets_not_assessed')}"
        "   (nobody looked; scored as wide and uninformative)",
        "",
        "A rank computed from sparse coverage is mostly a statement about curation",
        "order. Per-facet state for every target is in the sidecar under",
        "`evidence_state`, so the three states above stay distinguishable.",
        "-" * 78,
    ]
    print("\n".join(lines), file=file)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
