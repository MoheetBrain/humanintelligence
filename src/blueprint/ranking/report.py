"""Render ``reports/target_ranking_v0_1.csv`` and its provenance sidecar.

Two rules govern the output format.

**The CSV is machine-readable.** No comment lines, no blank lines, no merged cells,
one header row, deterministic column order, LF endings, fixed float precision. Any
caveat that would normally be a comment line is either a column (``status``,
``calibration_status``) or lives in the sidecar JSON.

**Every row carries its own provenance.** A row torn out of the CSV and pasted into a
slide still says ``PRELIMINARY``, still says ``uncalibrated_subjective``, and still
names the spec versions, the seed and the generation date that produced it.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from blueprint.ranking.information_gain import (
    TargetInformationGain,
    most_informative_facet,
    repository_next_analyses,
)
from blueprint.ranking.inputs import RepositoryInputs
from blueprint.ranking.rubric import DIMENSION_IDS
from blueprint.ranking.score import CapSensitivity, CohortResult, facet_evidence_state

__all__ = [
    "CSV_COLUMNS",
    "ReportArtefacts",
    "build_meta",
    "render_csv",
    "write_report",
]

#: Every row of every report produced in Sprint 1 carries this status.
ROW_STATUS = "PRELIMINARY"

#: Float precision for the CSV. Fixed so two runs produce identical bytes.
FLOAT_PRECISION = 4


def _dimension_columns() -> list[str]:
    """Per-dimension columns, in a fixed order.

    ``d1_level`` and ``d1_counter_level`` are BOTH present, and that is the point:
    a facet graded 2 with contradicting evidence at 3 must not be confusable with a
    facet nobody graded (contract §5.2). The first reads ``2`` / ``3``; the second
    reads blank / blank with ``d1_n_assessed = 0``.
    """
    columns: list[str] = []
    for dimension in DIMENSION_IDS:
        key = dimension.lower()
        columns.extend(
            [
                f"{key}_level",
                f"{key}_counter_level",
                f"{key}_n_assessed",
                f"{key}_n_level_zero",
                f"{key}_median",
                f"{key}_p05",
                f"{key}_p95",
            ]
        )
    return columns


#: The authoritative column order. Changing it is a report-format change.
CSV_COLUMNS: tuple[str, ...] = (
    "status",
    "rank_median",
    "rank_p05",
    "rank_p95",
    "rank_delta_symmetric_caps",
    "tier",
    "target_id",
    "symbol",
    "lead_atlas",
    "dossier_depth",
    "coverage",
    "facets_assessed",
    "facets_applicable",
    "facets_not_assessed",
    "facets_level_zero",
    "facets_contradicted",
    "reporting_gap_count",
    "claim_count",
    "independent_source_count",
    "red_team_verdict",
    "n_downgrades",
    "unresolved_critical_findings",
    *_dimension_columns(),
    "composite_median",
    "composite_p05",
    "composite_p95",
    "aggregation",
    "tractability_caveat",
    "most_informative_facet",
    "most_informative_facet_value",
    "gates_applied",
    "calibration_status",
    "rubric_version",
    "ranking_spec_version",
    "uncertainty_spec_version",
    "model_run_seed",
    "n_draws",
    "generated_on",
)


@dataclass(frozen=True, slots=True)
class ReportArtefacts:
    """Paths and bytes of what was written."""

    csv_path: Path
    meta_path: Path
    csv_bytes: bytes
    meta: Mapping[str, object]
    n_rows: int


def _fmt(value: float | None) -> str:
    """Fixed-precision float formatting; empty string for a missing value."""
    if value is None:
        return ""
    return f"{float(value):.{FLOAT_PRECISION}f}"


def render_csv(
    result: CohortResult,
    gains: Mapping[str, TargetInformationGain] | None = None,
    *,
    generated_on: str | None = None,
    caps: CapSensitivity | None = None,
) -> bytes:
    """Render the ranking table as CSV bytes.

    Args:
        result: A scored cohort.
        gains: Optional information-gain sweep, for ``most_informative_facet``.
        generated_on: ISO date stamped on every row. Defaults to today (UTC).
            Overridable so that determinism can be asserted across a date boundary.
        caps: Optional cap-variant sensitivity (contract §5.4), for
            ``rank_delta_symmetric_caps``.

    Returns:
        UTF-8 CSV bytes with LF line endings, rows sorted by median rank then
        target id.

    ``rank_delta_symmetric_caps`` is left BLANK for a target with no derived
    methodological cap, and that is not the same as ``0.0000``: blank means no cap
    applies to this target at all, zero means the caps applied and did not move it.
    """
    gains = gains or {}
    stamp = generated_on or date.today().isoformat()
    versions = result.spec.versions

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(CSV_COLUMNS), lineterminator="\n")
    writer.writeheader()

    ordered = sorted(
        result.targets,
        key=lambda t: (result.ranks[t.target_id].rank_median, t.target_id),
    )
    for scored in ordered:
        rank = result.ranks[scored.target_id]
        facet_name, facet_value = most_informative_facet(gains.get(scored.target_id))
        row: dict[str, object] = {
            "status": ROW_STATUS,
            "rank_median": _fmt(rank.rank_median),
            "rank_p05": _fmt(rank.rank_p05),
            "rank_p95": _fmt(rank.rank_p95),
            "rank_delta_symmetric_caps": (
                _fmt(caps.rank_delta[scored.target_id])
                if caps is not None and scored.target_id in caps.rank_delta
                else ""
            ),
            "tier": rank.tier,
            "target_id": scored.target_id,
            "symbol": scored.symbol,
            "lead_atlas": scored.lead_atlas or "",
            "dossier_depth": scored.dossier_depth or "",
            "coverage": _fmt(scored.coverage),
            "facets_assessed": scored.facets_assessed,
            "facets_applicable": scored.facets_applicable,
            "facets_not_assessed": scored.facets_not_assessed,
            "facets_level_zero": scored.facets_level_zero,
            "facets_contradicted": scored.facets_contradicted,
            "reporting_gap_count": scored.reporting_gap_count,
            "claim_count": scored.claim_count,
            "independent_source_count": scored.independent_source_count,
            "red_team_verdict": scored.red_team_verdict or "not_audited",
            "n_downgrades": scored.n_downgrades,
            "unresolved_critical_findings": scored.unresolved_critical_findings,
            "composite_median": _fmt(scored.composite_median),
            "composite_p05": _fmt(scored.composite_p05),
            "composite_p95": _fmt(scored.composite_p95),
            "aggregation": result.spec.primary_aggregation,
            "tractability_caveat": _tractability_caveat(scored),
            "most_informative_facet": facet_name,
            "most_informative_facet_value": _fmt(facet_value),
            "gates_applied": "|".join(scored.gates_applied),
            "calibration_status": versions.get("calibration_status", "uncalibrated_subjective"),
            "rubric_version": versions.get("rubric_version", ""),
            "ranking_spec_version": versions.get("ranking_spec_version", ""),
            "uncertainty_spec_version": versions.get("uncertainty_spec_version", ""),
            "model_run_seed": result.seed,
            "n_draws": result.n_draws,
            "generated_on": stamp,
        }
        for dimension in DIMENSION_IDS:
            score = scored.dimensions[dimension]
            key = dimension.lower()
            row[f"{key}_level"] = "" if score.level is None else score.level
            row[f"{key}_counter_level"] = "" if score.counter_level is None else score.counter_level
            row[f"{key}_n_assessed"] = score.n_assessed
            row[f"{key}_n_level_zero"] = score.n_level_zero
            row[f"{key}_median"] = _fmt(score.median)
            row[f"{key}_p05"] = _fmt(score.p05)
            row[f"{key}_p95"] = _fmt(score.p95)
        writer.writerow(row)

    return buffer.getvalue().encode("utf-8")


def _git_commit(root: Path) -> str | None:
    """The current commit hash, read from ``.git`` without invoking git.

    Agents in this repository do not run git commands (``BLACKBOARD_PROTOCOL`` §2.4),
    so the ref files are read directly. Returns ``None`` when unavailable, which is
    a legitimate state and is recorded as such.
    """
    head = root / ".git" / "HEAD"
    try:
        content = head.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if content.startswith("ref:"):
        ref = content.partition("ref:")[2].strip()
        candidate = root / ".git" / ref
        try:
            return candidate.read_text(encoding="utf-8").strip() or None
        except OSError:
            packed = root / ".git" / "packed-refs"
            try:
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(f" {ref}"):
                        return line.split(" ", 1)[0]
            except OSError:
                return None
            return None
    return content or None


def build_meta(
    result: CohortResult,
    inputs: RepositoryInputs,
    gains: Mapping[str, TargetInformationGain] | None = None,
    *,
    root: Path,
    generated_on: str | None = None,
    generated_at: str | None = None,
    caps: CapSensitivity | None = None,
) -> dict[str, object]:
    """Assemble the provenance sidecar for a run.

    Everything a reader needs to reproduce or distrust the CSV: spec hashes,
    versions, seed, draw count, which reader supplied the inputs, which gates fired,
    the aggregation sensitivity analysis, and the repository-level list of
    highest-value next analyses.
    """
    gains = gains or {}
    stamp = generated_on or date.today().isoformat()
    now = generated_at or datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    spec = result.spec
    return {
        "artefact": "reports/target_ranking_v0_1.csv",
        "status": ROW_STATUS,
        "produced_by": "agent:integration",
        "model": {
            "rubric": spec.versions.get("rubric_version"),
            "ranking_spec": spec.versions.get("ranking_spec_version"),
            "uncertainty_spec": spec.versions.get("uncertainty_spec_version"),
            "scale": spec.versions.get("scale"),
            "calibration_status": spec.versions.get("calibration_status"),
            "spec_sha256": dict(spec.sha256),
            "spec_paths": dict(spec.paths),
        },
        "run": {
            "seed": result.seed,
            "n_draws": result.n_draws,
            "n_targets_ranked": result.n_targets,
            "n_targets_in_cohort": len(inputs.targets),
            "generated_on": stamp,
            "generated_at": now,
            "git_commit": _git_commit(root),
            "reader": inputs.reader,
            "reader_notes": list(inputs.notes),
            "quantiles": list(spec.quantiles),
        },
        "interpretation": {
            "what_this_is": (
                "A prioritisation of what to analyse next computationally. Not a claim "
                "about biology, efficacy or safety, and not an endorsement of any target."
            ),
            "calibration": (
                "Uncalibrated subjective priors. The 90% intervals quantify what this "
                "model's own inputs leave undetermined, not whether the model is right."
            ),
            "aggregation": (
                f"The composite is the {result.spec.primary_aggregation.upper()} of the six "
                "gated dimensions. The dimensions are CONDITIONS THAT MUST ALL HOLD, not "
                "capacity factors to be averaged, so the composite is their joint "
                "probability under an explicit independence assumption. A target whose "
                "adult modifiability is near zero is useless however strong the other "
                "five conditions are, and a weighted mean would let them compensate for "
                "it. Absolute magnitudes are meaningless under this operator (a product "
                "of six numbers below 1); only the ordering and the interval are read."
            ),
            "independence_caveat": (
                "Facet draws are modelled as INDEPENDENT and they are not: facets share "
                "claims, sources, cohorts and a single grading agent per domain, and three "
                "facets feed two dimensions each. EVERY REPORTED INTERVAL IS THEREFORE TOO "
                "NARROW BY AN UNKNOWN AMOUNT. The direction of the error is known, its size "
                "is not. Because the composite is a product of the dimensions, the same "
                "positive dependence also means the true joint probability is HIGHER than "
                "the product of the marginals for a target whose dimensions are favourable "
                "together, so the composite understates such a target. This is the single "
                "largest known weakness in the model."
            ),
        },
        "disclosures": _disclosures(result),
        "sensitivity": {
            "primary_aggregation": result.spec.primary_aggregation,
            "operators_compared": [result.spec.primary_aggregation, *result.spec.alternative_aggregations],
            "pairwise_aggregation_kendall_tau_b": {
                name: (None if value != value else round(value, 4))  # NaN -> null
                for name, value in sorted(result.pairwise_sensitivity.items())
            },
            "aggregation_kendall_tau_b": {
                name: (None if value != value else round(value, 4))
                for name, value in sorted(result.sensitivity.items())
            },
            "rank_by_aggregation": {
                operator: dict(sorted(ranks.items()))
                for operator, ranks in sorted(result.rank_by_aggregation.items())
            },
            "reading": (
                "All PAIRWISE tau-b values over median ranks, so the primary is not "
                "privileged as a reference point. A value far from 1 means the ordering is "
                "a property of the aggregation choice rather than of the evidence. "
                "`rank_by_aggregation` gives every target's median rank under every "
                "operator, so a reader can see WHICH targets the choice moves. "
                "`geometric_mean` is deliberately absent: it is a strictly monotone "
                "transform of `product` and would report tau-b 1.0 by construction."
            ),
        },
        "gates_triggered": {k: list(v) for k, v in sorted(result.gates_triggered.items())},
        "cap_sensitivity": _cap_sensitivity_block(caps),
        "dimension_inputs": _dimension_inputs(result),
        "coverage_summary": _coverage_summary(result),
        "evidence_gap_facets": {
            k: list(v) for k, v in sorted(result.evidence_gap_facets.items())
        },
        "evidence_state": _evidence_state(result, inputs),
        "information_gain": {
            "method": spec.information_gain.get("method"),
            "top_next_analyses": list(repository_next_analyses(gains)),
            "honest_limitation": spec.information_gain.get("honest_limitation"),
        },
        "columns": list(CSV_COLUMNS),
    }


#: Per-row codes for the tractability caveat, surfaced in the CSV so the warning is
#: visible next to the D5 and D6 scores it qualifies rather than only in `models/`.
TRACTABILITY_CAVEAT_CODES = {
    "family_precedent_only": (
        "tractability >= 3 from a database release: a molecule touches this protein "
        "family, with nothing established about direction or selectivity"
    ),
    "characterised_tool": "tractability 2: a ligand, pocket or high-quality probe exists",
    "prediction_only": "tractability 1: prediction or family membership only, no tool",
    "no_signal_in_release": "tractability 0: the pinned release carries no tractability signal",
    "not_assessed": "tractability not graded: scored as wide and uninformative",
}


def _tractability_caveat(scored) -> str:
    """The caveat code for one row's ``tractability`` grade.

    D6 takes ``tractability`` at weight 0.25 and D5 at 0.15, so a level-3 grade moves
    both dimensions — and a level-3 grade derived from a database release means only
    that a molecule touches the protein family, with nothing established about
    direction or selectivity. Putting the code in the CSV means a reader of a D5 or D6
    score sees the qualification at the row, without having to open the assessment
    record or the spec.
    """
    level = scored.tractability_level
    if level is None:
        return "not_assessed"
    if level >= 3:
        return "family_precedent_only"
    if level == 2:
        return "characterised_tool"
    if level == 1:
        return "prediction_only"
    return "no_signal_in_release"


def _dimension_inputs(result: CohortResult) -> dict[str, object]:
    """Facet count and weights per dimension, so a thin dimension cannot hide.

    Required by R8 (``docs/blackboard/RESOLUTIONS.md``). D3 previously had a single
    input facet while carrying 0.15 of the composite, which made it a relabelling of
    one grader's judgement rather than an aggregate — and nothing in the report said
    so. Publishing the input count per dimension means that can never again be
    invisible, for D3 or for any dimension a later edit thins out.
    """
    spec = result.spec
    inputs: dict[str, object] = {}
    for dimension in DIMENSION_IDS:
        facets = spec.facets_for(dimension)
        inputs[dimension] = {
            "n_input_facets": len(facets),
            "composite_weight": spec.dimension_weights[dimension],
            "facets": {
                facet.facet: {
                    "weight": facet.weights[dimension],
                    "polarity": facet.polarity,
                }
                for facet in facets
            },
            "single_input_warning": (
                "this dimension has ONE input facet: it is a relabelling of one grader's "
                "ordinal judgement, with no internal cross-check"
                if len(facets) == 1
                else None
            ),
        }
    return inputs


def _disclosures(result: CohortResult) -> list[dict[str, object]]:
    """Disclosures that belong in the report narrative, not only in `models/`.

    A caveat buried in a spec file is a caveat nobody reads. These two are carried on
    every report because both change how a score should be read, and both are invisible
    from the numbers alone.
    """
    disclosures: list[dict[str, object]] = [
        {
            "id": "independence_assumption_narrows_every_interval",
            "severity": "major",
            "applies_to": "every row, every dimension, the composite and every rank interval",
            "statement": (
                "The model draws facet beliefs independently. They are not independent: "
                "facets share claims, sources and cohorts, three facets feed two dimensions "
                "each, and each domain's facets share one grading agent. Every reported 90% "
                "interval is therefore TOO NARROW by an unknown amount, and because the "
                "composite is a product of the dimensions the point estimate UNDERSTATES a "
                "target whose dimensions are favourable together. The direction of both "
                "errors is known; neither size is."
            ),
            "what_would_fix_it": (
                "A dependence model: at minimum a shared per-target grader effect, better a "
                "claim-level source-overlap copula."
            ),
            "spec_ref": "models/ranking/ranking_spec_v0_1.yaml#composite.primary.independence_assumption",
        }
    ]

    family_only = sorted(
        t.target_id for t in result.targets if (t.tractability_level or 0) >= 3
    )
    if family_only:
        disclosures.append(
            {
                "id": "tractability_level_3_is_family_precedent_only",
                "severity": "major",
                "applies_to": f"D5 and D6 for {len(family_only)} target(s): {', '.join(family_only)}",
                "statement": (
                    "These targets carry `tractability` at level 3 or above, graded from a "
                    "pinned database release. That grade means A MOLECULE TOUCHES THIS "
                    "PROTEIN FAMILY. It establishes nothing about direction (agonist, "
                    "antagonist or modulator), nothing about selectivity within the family, "
                    "and nothing about whether the available direction is the one this "
                    "project's control-point hypothesis requires. A level-3 tractability "
                    "grade is compatible with there being no usable tool for the modulation "
                    "actually wanted. `tractability` carries weight 0.25 in D6 and 0.15 in "
                    "D5, so this qualifies both dimensions for these rows."
                ),
                "visible_at_the_row": "the `tractability_caveat` column reads `family_precedent_only`",
                "record_ref": "atlases/integration/assessments/{SYMBOL}.yaml -> facets[0].rationale",
            }
        )
    return disclosures


def _cap_sensitivity_block(caps: CapSensitivity | None) -> dict[str, object]:
    """The cap-variant sensitivity section required by contract §5.4.

    The asymmetry of the capping rule is precautionary and deliberate, and it is not
    neutral: weak method can raise doubt about a target while being unable to establish
    support for it, so a promising target whose evidence is weak in both directions is
    systematically under-ranked. This block measures that rather than asserting it is
    small, and it states the asymmetry wherever ranks are reported — which is the
    contract's other obligation.
    """
    asymmetry_statement = (
        "Methodological-weakness caps apply only in the direction that favours the "
        "target (contract §5.4): a normal-polarity facet has `level` capped, an "
        "inverse-polarity facet has `counter_level` capped and never `level`. This is a "
        "precaution against over-optimism and it is not neutral — it systematically "
        "under-ranks a promising target whose evidence base is methodologically weak in "
        "both directions. `rank_delta` below measures the size of that effect."
    )
    if caps is None:
        return {
            "measured": False,
            "asymmetry_statement": asymmetry_statement,
            "note": "cap sensitivity was not computed for this run",
        }
    return {
        "measured": True,
        "asymmetry_statement": asymmetry_statement,
        "variants": ["polarity_aware (default, contract §5.4)", "symmetric_caps (counterfactual)"],
        "caps_derived_from": (
            "context.phylogenetic_control on the claims each facet cites "
            "(atlases/comparative/phylogenetic_controls.md §4)"
        ),
        "n_caps_derived": caps.n_caps_derived,
        "kendall_tau_b": (None if caps.kendall_tau_b != caps.kendall_tau_b else round(caps.kendall_tau_b, 4)),
        "threshold_rank_positions": caps.threshold,
        "rank_delta": dict(caps.rank_delta),
        "rank_delta_sign_convention": (
            "symmetric minus polarity_aware. Negative = the target ranks better under "
            "symmetric caps, i.e. the precautionary asymmetry is costing it rank. Absent "
            "= no cap was derived for this target (not the same as zero)."
        ),
        "sensitive_targets": list(caps.sensitive_targets),
        "narrative_flag": (
            "rank is sensitive to the precautionary capping rule"
            if caps.sensitive_targets
            else "no target moved by more than the threshold"
        ),
        "polarity_aware_was_a_no_op": caps.polarity_aware_was_a_no_op,
        "polarity_aware_no_op_reading": (
            "True means the grading agents had already applied contract §5.4 when they "
            "wrote their levels, so re-deriving the caps changed nothing — a cross-check "
            "that passed. False would be a finding about curation, not about the targets."
        ),
        "cap_applications": {k: list(v) for k, v in sorted(caps.cap_applications.items())},
    }


def _coverage_summary(result: CohortResult) -> dict[str, object]:
    """Cohort-level coverage, stated loudly enough that it cannot be overlooked.

    Sparse coverage is the Sprint-1 norm, not an anomaly: several atlases graded a
    handful of facets on a handful of targets and honestly left the rest
    ``not_assessed``. A ranking built on 30% coverage is mostly a report on curation
    order, and the only defence against it being read otherwise is putting the number
    where a reader trips over it.
    """
    if not result.targets:
        return {"n_targets": 0}
    coverages = sorted(t.coverage for t in result.targets)
    minimum = float(result.spec.tiers["min_coverage"])
    below = [t.target_id for t in result.targets if t.coverage < minimum]
    return {
        "n_targets": len(result.targets),
        "min_coverage_threshold": minimum,
        "coverage_min": round(coverages[0], 4),
        "coverage_median": round(coverages[len(coverages) // 2], 4),
        "coverage_max": round(coverages[-1], 4),
        "n_targets_below_min_coverage": len(below),
        "targets_below_min_coverage": below,
        "n_targets_unaudited": sum(1 for t in result.targets if not t.is_audited),
        "total_facet_slots": sum(t.facets_applicable for t in result.targets),
        "total_facets_assessed": sum(t.facets_assessed for t in result.targets),
        "total_facets_not_assessed": sum(t.facets_not_assessed for t in result.targets),
        "total_facets_level_zero": sum(t.facets_level_zero for t in result.targets),
        "total_facets_contradicted": sum(t.facets_contradicted for t in result.targets),
        "total_reporting_gaps": sum(t.reporting_gap_count for t in result.targets),
        "targets_with_reporting_gaps": [
            t.target_id for t in result.targets if t.reporting_gap_count
        ],
        "reading": (
            "coverage = facets assessed / facets applicable. Below the threshold a row is "
            "tiered tier_3_insufficient_coverage and its rank is a statement about curation "
            "rather than about the target. `level_zero` is a documented negative search and is "
            "NOT the same state as `not_assessed`."
        ),
    }


def _evidence_state(result: CohortResult, inputs: RepositoryInputs) -> dict[str, object]:
    """Per-target, per-facet status/level/counter_level, for full recoverability.

    Recorded because the three "no support" states must stay distinguishable in the
    artefacts and not only in the source records (contract §5.2): nobody looked
    (``not_assessed``), searched and found nothing (``level: 0``), and tested and
    contradicted (``counter_level >= 2``). The CSV distinguishes them per dimension;
    this block does it per facet.
    """
    adjusted = inputs.with_audit_adjustments_applied()
    by_id = {t.target_id: t for t in adjusted.targets}
    state: dict[str, object] = {}
    for scored in result.targets:
        target = by_id.get(scored.target_id)
        if target is None:  # pragma: no cover
            continue
        state[scored.target_id] = {
            "coverage": round(scored.coverage, 4),
            "facets_assessed": scored.facets_assessed,
            "facets_not_assessed": scored.facets_not_assessed,
            "facets_level_zero": scored.facets_level_zero,
            "facets_contradicted": scored.facets_contradicted,
            "facets": facet_evidence_state(result.spec, target),
        }
    return state


def write_report(
    result: CohortResult,
    inputs: RepositoryInputs,
    gains: Mapping[str, TargetInformationGain] | None = None,
    *,
    root: Path,
    reports_dir: Path | None = None,
    generated_on: str | None = None,
    generated_at: str | None = None,
    caps: CapSensitivity | None = None,
) -> ReportArtefacts:
    """Write the CSV and its ``.meta.json`` sidecar.

    Args:
        result: A scored cohort.
        inputs: The inputs that produced it (for reader provenance and counts).
        gains: Optional information-gain sweep.
        root: Repository root (used to read the git ref and to locate ``reports/``).
        reports_dir: Override the output directory.
        generated_on: ISO date stamped on every CSV row.
        generated_at: ISO timestamp for the sidecar only.

    Returns:
        A :class:`ReportArtefacts` with both paths and the CSV bytes.
    """
    target_dir = reports_dir or (root / "reports")
    target_dir.mkdir(parents=True, exist_ok=True)
    csv_path = target_dir / "target_ranking_v0_1.csv"
    meta_path = target_dir / "target_ranking_v0_1.meta.json"

    payload = render_csv(result, gains, generated_on=generated_on, caps=caps)
    meta = build_meta(
        result,
        inputs,
        gains,
        root=root,
        generated_on=generated_on,
        generated_at=generated_at,
        caps=caps,
    )

    csv_path.write_bytes(payload)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ReportArtefacts(
        csv_path=csv_path,
        meta_path=meta_path,
        csv_bytes=payload,
        meta=meta,
        n_rows=result.n_targets,
    )
