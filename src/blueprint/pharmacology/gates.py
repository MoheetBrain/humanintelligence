"""Gate G5 — the only door into virtual pharmacology.

``docs/BLACKBOARD_PROTOCOL.md`` §3 defines gate G5: virtual pharmacology may act only
on targets that survived **causal integration** *and* **red-team review**. This module
is the executable form of that gate, and it is the only mechanism in the repository
that Sprint-4 work is permitted to consult before starting.

The gate is deliberately hard to pass and easy to read. Every refusal returns a
sentence naming the specific condition that failed, because a refusal nobody
understands gets worked around.

What passing the gate does and does not mean
--------------------------------------------
Passing means: *the evidence accounting for this target is complete enough, and has
survived enough adversarial review, that spending computational chemistry effort on it
is defensible.* It does not mean the target is validated, that modulating it is safe,
or that any of it leaves the computer. Everything downstream of this gate stays in
silico (``docs/COMPUTATIONAL_ONLY_POLICY.md``), and no output of it is ever a protocol,
a dose, a route or a sourcing route.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

__all__ = [
    "DEMOTING_VERDICTS",
    "GateDecision",
    "MINIMUM_COVERAGE",
    "eligible_for_chemistry",
    "explain_gate",
]

#: Red-team verdicts that refuse the gate outright (contract §6).
DEMOTING_VERDICTS = frozenset({"deprioritise", "insufficient_evidence"})

#: Minimum facet coverage to pass. Deliberately the same subjective threshold the
#: ranking spec uses for ``tier_3_insufficient_coverage``
#: (``models/ranking/ranking_spec_v0_1.yaml`` -> ``tiers.min_coverage``), so that a
#: target the ranking model calls under-curated cannot pass the chemistry gate. It is
#: a floor, not a target: passing it is not a coverage endorsement.
MINIMUM_COVERAGE = 0.40

#: Severities that block the gate while unresolved.
BLOCKING_SEVERITIES = frozenset({"critical"})


@dataclass(frozen=True, slots=True)
class GateDecision:
    """The full result of a gate evaluation, for auditing a refusal or a pass."""

    eligible: bool
    reason: str
    target_id: str
    checks: Mapping[str, bool]
    failures: tuple[str, ...]

    def __bool__(self) -> bool:
        """A decision is truthy exactly when the target is eligible."""
        return self.eligible


def _get(source: Any, key: str, default: Any = None) -> Any:
    """Read ``key`` from a mapping or an attribute, so callers can pass either.

    The ranking row may arrive as a CSV dict, a
    :class:`blueprint.ranking.score.TargetScore`, or a pandas row. Accepting all
    three keeps the gate usable without forcing a dependency direction.
    """
    if source is None:
        return default
    if isinstance(source, Mapping):
        value = source.get(key, default)
    else:
        value = getattr(source, key, default)
    return default if value is None else value


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _count_unresolved_critical(audit: Any) -> int:
    """Unresolved ``critical`` findings in one audit record (contract §6).

    A finding counts as unresolved unless it explicitly says otherwise: absence of a
    resolution field means nobody has recorded a resolution, which is not the same as
    the finding having been answered. Failing closed is the only safe default for a
    gate.
    """
    findings = _get(audit, "findings", ()) or ()
    if isinstance(findings, Mapping):
        findings = [findings]
    count = 0
    for finding in findings:
        if str(_get(finding, "severity", "info")) not in BLOCKING_SEVERITIES:
            continue
        if str(_get(finding, "resolution_status", "unresolved")) != "resolved":
            count += 1
    return count


def eligible_for_chemistry(
    target: Any,
    ranking_row: Any = None,
    audits: Sequence[Any] | Any = (),
    *,
    minimum_coverage: float = MINIMUM_COVERAGE,
) -> tuple[bool, str]:
    """Gate G5. Return ``(eligible, reason)`` for one target.

    Args:
        target: The target. A mapping or an object with ``target_id`` / ``symbol``;
            a plain string target id is also accepted.
        ranking_row: The target's row from ``reports/target_ranking_v0_1.csv``, or a
            :class:`blueprint.ranking.score.TargetScore`. Supplies ``coverage``,
            ``red_team_verdict``, ``tier`` and ``unresolved_critical_findings``.
        audits: Audit records covering the target (contract §6), as mappings or
            objects. A single record may be passed instead of a sequence.
        minimum_coverage: Override the coverage floor. Raising it is always allowed;
            lowering it below :data:`MINIMUM_COVERAGE` is refused, because a caller
            that can weaken the gate is not a gate.

    Returns:
        ``(True, reason)`` only when every condition passes; otherwise
        ``(False, reason)`` where ``reason`` names the conditions that failed.

    The conditions, all of which must hold:

    1. **Ranked.** A ranking row exists. A target the integration model never scored
       has not been through causal integration at all.
    2. **Audited.** At least one red-team audit covers it (gate G4, rule V15).
    3. **Not demoted.** No ``deprioritise`` or ``insufficient_evidence`` verdict, in
       the ranking row or in any audit record.
    4. **No unresolved critical finding.** A disputed evidence base is not a
       foundation for chemistry.
    5. **Minimum coverage.** At least ``minimum_coverage`` of the applicable facet
       catalogue assessed.
    6. **Not tiered as insufficient.** The ranking model's own tier must not be
       ``tier_3_insufficient_coverage`` or ``tier_4_deprioritised_by_audit``.

    Example::

        >>> ok, why = eligible_for_chemistry(
        ...     {"target_id": "TGT:EXAMPLE"},
        ...     {"coverage": 0.8, "red_team_verdict": "deprioritise", "tier": "tier_4_deprioritised_by_audit"},
        ...     [{"verdict": "deprioritise"}],
        ... )
        >>> ok
        False
    """
    decision = explain_gate(
        target, ranking_row, audits, minimum_coverage=minimum_coverage
    )
    return decision.eligible, decision.reason


def explain_gate(
    target: Any,
    ranking_row: Any = None,
    audits: Sequence[Any] | Any = (),
    *,
    minimum_coverage: float = MINIMUM_COVERAGE,
) -> GateDecision:
    """The same evaluation as :func:`eligible_for_chemistry`, with every check shown.

    Use this when a refusal has to be explained or logged; use
    :func:`eligible_for_chemistry` for the boolean.
    """
    if minimum_coverage < MINIMUM_COVERAGE:
        raise ValueError(
            f"minimum_coverage={minimum_coverage} is below the gate's floor "
            f"{MINIMUM_COVERAGE}. A caller that can weaken gate G5 is not a gate; raise "
            "the floor if you want to be stricter."
        )

    target_id = (
        target
        if isinstance(target, str)
        else str(_get(target, "target_id", None) or _get(target, "symbol", "unknown target"))
    )
    if isinstance(audits, (Mapping, str)) or not isinstance(audits, Sequence):
        audits = [audits] if audits else []
    audits = [a for a in audits if a]

    verdicts = {str(_get(audit, "verdict", "")) for audit in audits}
    row_verdict = str(_get(ranking_row, "red_team_verdict", "") or "")
    if row_verdict and row_verdict != "not_audited":
        verdicts.add(row_verdict)
    verdicts.discard("")

    coverage = _as_float(_get(ranking_row, "coverage", 0.0))
    tier = str(_get(ranking_row, "tier", "") or "")
    unresolved_from_row = _as_int(_get(ranking_row, "unresolved_critical_findings", 0))
    unresolved_from_audits = sum(_count_unresolved_critical(audit) for audit in audits)
    unresolved = max(unresolved_from_row, unresolved_from_audits)

    has_audit_record = bool(audits) or (bool(row_verdict) and row_verdict != "not_audited")

    checks = {
        "has_ranking_row": ranking_row is not None,
        "has_red_team_audit": has_audit_record,
        "no_demoting_verdict": not (verdicts & DEMOTING_VERDICTS),
        "no_unresolved_critical_finding": unresolved == 0,
        "meets_minimum_coverage": coverage >= minimum_coverage,
        "not_tiered_insufficient": tier
        not in ("tier_3_insufficient_coverage", "tier_4_deprioritised_by_audit"),
    }

    explanations = {
        "has_ranking_row": (
            "no ranking row: the target has not been through causal integration"
        ),
        "has_red_team_audit": (
            "no red-team audit record (gate G4 / validator rule V15 unsatisfied)"
        ),
        "no_demoting_verdict": (
            "red-team verdict is "
            + ", ".join(sorted(verdicts & DEMOTING_VERDICTS))
            + ": the target was demoted by audit"
        ),
        "no_unresolved_critical_finding": (
            f"{unresolved} unresolved critical red-team finding(s): the evidence base is "
            "under active dispute"
        ),
        "meets_minimum_coverage": (
            f"facet coverage {coverage:.2f} is below the required {minimum_coverage:.2f}: "
            "too little of the facet catalogue was assessed for the ranking to mean anything"
        ),
        "not_tiered_insufficient": (
            f"ranking tier is {tier!r}: the integration model itself does not regard this "
            "row as a basis for prioritising work"
        ),
    }

    failures = tuple(name for name, passed in checks.items() if not passed)
    if failures:
        reason = (
            f"{target_id} is NOT eligible for virtual pharmacology (gate G5). "
            + " ".join(f"({index}) {explanations[name]}." for index, name in enumerate(failures, 1))
        )
        return GateDecision(False, reason, target_id, checks, failures)

    reason = (
        f"{target_id} passes gate G5: ranked by causal integration, audited by the red team "
        f"with no demoting verdict and no unresolved critical finding, facet coverage "
        f"{coverage:.2f} >= {minimum_coverage:.2f}, tier {tier!r}. This permits IN-SILICO "
        "analysis only; it is not a claim that the target is validated or that modulating it "
        "is safe, and nothing downstream may produce a protocol, dose, route or sourcing route."
    )
    return GateDecision(True, reason, target_id, checks, ())
