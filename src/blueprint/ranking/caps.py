"""The single polarity-aware implementation of methodological-weakness caps.

Contract §5.4. This module exists because the naive implementation of a
methodological cap is wrong in a way that flatters targets, and it was wrong in
practice: ``agent:comparative`` applied the rule "a claim with
``phylogenetic_control: none`` may not be graded above level 2" to
``human_lineage_divergence_risk``, which is inverse-polarity. Capping the *risk*
grade made a target with documented human/mouse physiological divergence look **more**
translatable than its evidence supports. The methodological weakness had been
converted into an optimistic conclusion.

The rule
--------
A methodological cap applies **only in the direction that disfavours the target**:

============================  =========================  ================================
polarity                      cap constrains             cap must never touch
============================  =========================  ================================
``normal``                    ``level``                  ``counter_level``
``inverse``                   ``counter_level``          ``level``
============================  =========================  ================================

Read as sentences:

* *A weak method cannot establish strong support.* So on a normal-polarity facet the
  cap limits how strongly the evidence can be said to support the proposition.
* *A weak method cannot establish the absence of a risk.* So on an inverse-polarity
  facet the cap limits ``counter_level`` — the grade for "we looked for the risk and
  it is not there" — and leaves the risk grade itself untouched.

Why there is exactly one implementation
---------------------------------------
The contract requires caps to go through a polarity-aware helper "rather than ad hoc
clipping". Ad hoc clipping is how the original bug happened: ``min(level, 2)`` reads
as obviously correct at a call site and is obviously correct only for half the
facets. Every caller in this repository — and any future caller in another lane —
must call :func:`apply_methodological_cap`, which cannot be invoked without a facet
spec and therefore cannot be invoked without knowing the polarity.

The asymmetry has a cost, and the cost is measured
--------------------------------------------------
Contract §5.4 also records what the polarity-aware rule buys and what it costs.
Because caps bite only in the favourable direction, methodologically weak evidence can
raise doubt about a target while being unable to establish support for it. That is a
precautionary choice for a project whose dominant risk is over-optimism about cognitive
enhancement, and it is **not neutral**: it systematically under-ranks a genuinely
promising target whose evidence base happens to be weak in *both* directions.

So this module implements two modes, and the ranking run reports both:

``polarity_aware`` (the default, and what §5.4 mandates)
    Caps the favourable field only, as above.

``symmetric``
    Caps ``level`` and ``counter_level`` alike. This is the **counterfactual, not an
    alternative policy**: it exists so the size of the precautionary asymmetry's effect
    on ranks can be measured rather than assumed
    (``ranking_spec_v0_1.yaml`` -> ``cap_variants``). No report is ever produced under
    it as the primary ranking.

Where the caps come from
------------------------
:func:`derive_phylogenetic_caps` reads them off the evidence's own method:
``context.phylogenetic_control`` on each claim a facet cites
(``atlases/comparative/phylogenetic_controls.md`` §4). Deriving rather than declaring
matters — a cap is a statement about how a study was done, so it should be read from
the study record, not from a hand-maintained list that can drift from it.

One useful consequence: the grading agent already applies the polarity-aware cap when
it writes a level, so re-deriving and re-applying in ``polarity_aware`` mode should be
a **no-op**. When it is not a no-op, the grader did not apply the rule, and that
discrepancy is worth reporting rather than silently correcting.

Distinction from the gates in ``ranking_spec_v0_1.yaml``
--------------------------------------------------------
These are different mechanisms and must not be conflated:

* A **methodological cap** (here) constrains an *input grade* because of how the
  underlying study was done. It changes what the evidence is taken to show.
* A **gate** (``blueprint.ranking.score``) caps a *dimension or composite score*
  because of what the grades say. It changes what the model is willing to conclude.

A cap is upstream of a gate, and a cap is never applied to a score.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from blueprint.ranking.inputs import FacetAssessment, RepositoryInputs, TargetInput
from blueprint.ranking.rubric import ModelSpec, SpecError

__all__ = [
    "CAP_MODES",
    "CapApplication",
    "CapMode",
    "MethodologicalCap",
    "PHYLOGENETIC_CAP_LEVEL",
    "WEAK_PHYLOGENETIC_CONTROLS",
    "apply_methodological_cap",
    "apply_methodological_caps",
    "cap_field_for",
    "cap_cohort",
    "cap_fields_for",
    "caps_from_records",
    "derive_caps_for_cohort",
    "derive_phylogenetic_caps",
]

#: The two cap modes. ``polarity_aware`` is the policy (contract §5.4);
#: ``symmetric`` exists only as the sensitivity counterfactual.
CapMode = Literal["polarity_aware", "symmetric"]
CAP_MODES: tuple[str, ...] = ("polarity_aware", "symmetric")

#: ``context.phylogenetic_control`` values that trigger the comparative cap
#: (``atlases/comparative/phylogenetic_controls.md`` §4).
WEAK_PHYLOGENETIC_CONTROLS = frozenset({"none", "not_reported"})

#: The level that rule caps at. Declared by the comparative atlas, not by this module.
PHYLOGENETIC_CAP_LEVEL = 2


@dataclass(frozen=True, slots=True)
class MethodologicalCap:
    """A cap to impose on one facet because its underlying method is weak.

    Attributes:
        facet: Facet name the cap applies to.
        max_level: The highest grade the weak method can support, in ``0..4``.
        reason: Why the cap applies, e.g. ``"phylogenetic_control: none"``. Required:
            an unexplained cap is not auditable.
        imposed_by: Agent id that imposed it.
    """

    facet: str
    max_level: int
    reason: str
    imposed_by: str | None = None

    def __post_init__(self) -> None:
        if not 0 <= int(self.max_level) <= 4:
            raise ValueError(f"{self.facet}: max_level {self.max_level!r} outside 0..4")
        if not str(self.reason).strip():
            raise ValueError(f"{self.facet}: a methodological cap must state its reason")


@dataclass(frozen=True, slots=True)
class CapApplication:
    """What a cap actually did to one facet assessment.

    ``field_capped`` is always the field contract §5.4 mandates for this facet's
    polarity, whatever mode was used, so a reader can tell at a glance what the policy
    would have done. ``fields_capped`` is what the mode actually touched: the same
    single field under ``polarity_aware``, and both fields under ``symmetric``.
    """

    facet: str
    polarity: str
    field_capped: str
    max_level: int
    reason: str
    before_level: int | None
    after_level: int | None
    before_counter_level: int | None
    after_counter_level: int | None
    applied: bool
    mode: str = "polarity_aware"
    fields_capped: tuple[str, ...] = ()

    @property
    def summary(self) -> str:
        """A one-line, log-ready description naming every field that actually moved."""
        head = f"{self.facet} ({self.polarity}, mode={self.mode})"
        if not self.applied:
            return f"{head}: cap at {self.max_level} not binding [{self.reason}]"
        before = {"level": self.before_level, "counter_level": self.before_counter_level}
        after = {"level": self.after_level, "counter_level": self.after_counter_level}
        moves = ", ".join(
            f"{field} {before[field]} -> {after[field]}" for field in self.fields_capped
        )
        return f"{head}: {moves} at cap {self.max_level} [{self.reason}]"


def cap_field_for(polarity: str) -> str:
    """The assessment field a methodological cap may constrain, per contract §5.4.

    Args:
        polarity: ``normal`` or ``inverse`` (``direct`` is accepted as a deprecated
            alias for ``normal``).

    Returns:
        ``"level"`` for normal polarity, ``"counter_level"`` for inverse polarity.

    Raises:
        SpecError: On an unrecognised polarity. Guessing would reintroduce the exact
            failure mode this module exists to prevent.
    """
    normalised = "normal" if polarity == "direct" else polarity
    if normalised == "normal":
        return "level"
    if normalised == "inverse":
        return "counter_level"
    raise SpecError(
        f"unknown polarity {polarity!r}; contract §5.4 defines `normal` and `inverse` only"
    )


def cap_fields_for(polarity: str, mode: CapMode = "polarity_aware") -> tuple[str, ...]:
    """The assessment fields a cap may touch, given a polarity and a mode.

    Args:
        polarity: ``normal`` or ``inverse`` (``direct`` is a deprecated alias).
        mode: ``polarity_aware`` (contract §5.4 policy) or ``symmetric`` (the
            sensitivity counterfactual).

    Returns:
        ``("level",)`` or ``("counter_level",)`` under ``polarity_aware``; both fields
        under ``symmetric``.

    Raises:
        SpecError: On an unrecognised polarity or mode.
    """
    if mode not in CAP_MODES:
        raise SpecError(f"unknown cap mode {mode!r}; expected one of {CAP_MODES}")
    if mode == "symmetric":
        # Validate the polarity anyway, so a typo cannot slip through in either mode.
        cap_field_for(polarity)
        return ("level", "counter_level")
    return (cap_field_for(polarity),)


def apply_methodological_cap(
    spec: ModelSpec,
    assessment: FacetAssessment,
    cap: MethodologicalCap,
    *,
    mode: CapMode = "polarity_aware",
) -> tuple[FacetAssessment, CapApplication]:
    """Apply one methodological cap to one facet assessment, polarity-aware.

    Args:
        spec: The loaded model specification (supplies the facet's polarity).
        assessment: The facet assessment to cap.
        cap: The cap to impose.

    Returns:
        ``(capped_assessment, record)``. The assessment is returned unchanged when the
        cap is not binding, and ``record.applied`` says which happened.

    Raises:
        SpecError: If the facet is not in the rubric, or its polarity is unrecognised.

    The two branches:

    * **normal polarity** — ``level = min(level, max_level)``; ``counter_level``
      untouched. A weak method cannot establish strong support.
    * **inverse polarity** — ``counter_level = min(counter_level, max_level)``;
      ``level`` untouched, always. A weak method cannot establish the absence of a
      risk, so the risk grade stands and only the "we checked and it is fine" grade is
      limited.

    An unassessed facet is never capped into being assessed: a cap constrains a grade
    that exists, and manufacturing one would turn "nobody looked" into "someone looked
    and found at most this much", which is a different and stronger statement.
    """
    facet_spec = spec.facets.get(cap.facet)
    if facet_spec is None:
        raise SpecError(
            f"cannot cap unknown facet {cap.facet!r}; it is not in {spec.versions.get('rubric_version')}"
        )
    if assessment.facet != cap.facet:
        raise SpecError(
            f"cap targets {cap.facet!r} but was given an assessment of {assessment.facet!r}"
        )

    policy_field = cap_field_for(facet_spec.polarity)
    fields = cap_fields_for(facet_spec.polarity, mode)
    limit = int(cap.max_level)
    before_level, before_counter = assessment.level, assessment.counter_level

    capped = assessment
    touched: list[str] = []
    if "level" in fields and capped.is_assessed and capped.level is not None and capped.level > limit:
        capped = replace(capped, level=limit)
        touched.append("level")
    if "counter_level" in fields and capped.counter_level is not None and capped.counter_level > limit:
        capped = replace(capped, counter_level=limit)
        touched.append("counter_level")

    record = CapApplication(
        facet=cap.facet,
        polarity=facet_spec.polarity,
        field_capped=policy_field,
        max_level=limit,
        reason=cap.reason,
        before_level=before_level,
        after_level=capped.level,
        before_counter_level=before_counter,
        after_counter_level=capped.counter_level,
        applied=bool(touched),
        mode=mode,
        fields_capped=tuple(touched),
    )
    return capped, record


def apply_methodological_caps(
    spec: ModelSpec,
    target: TargetInput,
    caps: Iterable[MethodologicalCap],
    *,
    mode: CapMode = "polarity_aware",
) -> tuple[TargetInput, tuple[CapApplication, ...]]:
    """Apply a set of methodological caps to one target, polarity-aware.

    Args:
        spec: The loaded model specification.
        target: The target whose facets to cap.
        caps: Caps to impose. Several caps on one facet are allowed; the lowest limit
            wins, so caps can only ever ratchet a grade further down.
        mode: ``polarity_aware`` (the policy) or ``symmetric`` (the counterfactual
            used to measure the cost of the policy's asymmetry).

    Returns:
        ``(capped_target, records)`` with one record per cap considered, in the order
        given, so a report can show what each cap did — including the ones that did
        nothing.
    """
    lowest: dict[str, MethodologicalCap] = {}
    for cap in caps:
        current = lowest.get(cap.facet)
        if current is None or int(cap.max_level) < int(current.max_level):
            lowest[cap.facet] = cap

    facets: dict[str, FacetAssessment] = dict(target.facets)
    records: list[CapApplication] = []
    for facet_name in sorted(lowest):
        cap = lowest[facet_name]
        assessment = facets.get(facet_name) or target.facet(facet_name)
        capped, record = apply_methodological_cap(spec, assessment, cap, mode=mode)
        facets[facet_name] = capped
        records.append(record)

    return replace(target, facets=facets), tuple(records)


def caps_from_records(records: Iterable[Mapping[str, object]]) -> tuple[MethodologicalCap, ...]:
    """Build caps from curated records (e.g. a comparative agent's cap declarations).

    Expects each mapping to carry ``facet``, ``max_level`` and ``reason``; anything
    without all three is skipped rather than defaulted, because a cap with an invented
    limit or an unstated reason is worse than no cap.
    """
    caps: list[MethodologicalCap] = []
    for record in records:
        facet = record.get("facet")
        max_level = record.get("max_level")
        reason = record.get("reason")
        if not facet or max_level is None or not reason:
            continue
        caps.append(
            MethodologicalCap(
                facet=str(facet),
                max_level=int(max_level),  # type: ignore[arg-type]
                reason=str(reason),
                imposed_by=str(record["imposed_by"]) if record.get("imposed_by") else None,
            )
        )
    return tuple(caps)


def derive_phylogenetic_caps(
    spec: ModelSpec,
    target: TargetInput,
    inputs: RepositoryInputs,
    *,
    cap_level: int = PHYLOGENETIC_CAP_LEVEL,
) -> tuple[MethodologicalCap, ...]:
    """Derive comparative methodological caps from the claims a facet actually cites.

    The rule is the comparative atlas's
    (``atlases/comparative/phylogenetic_controls.md`` §4): a facet resting only on
    claims whose ``context.phylogenetic_control`` is ``none`` or ``not_reported`` may
    not be graded above level 2, because a comparative pattern that has not survived
    phylogenetic correction may be an artefact of shared ancestry rather than a
    conserved rule.

    Args:
        spec: The loaded model specification.
        target: The target whose facets to examine.
        inputs: The cohort, for claim lookup.
        cap_level: The cap the rule imposes. Declared by the comparative atlas; it is a
            parameter here only so a caller can tighten it.

    Returns:
        One cap per facet the rule applies to, sorted by facet name.

    Derivation, not declaration: a cap is a statement about how a study was done, so it
    is read from the study record rather than from a hand-maintained list that can drift
    from it. A facet is capped only when **every** claim it cites carries a weak
    control — one properly controlled claim in the set is enough to lift the cap, since
    the grade may rest on that claim.

    Facets whose claims carry no ``phylogenetic_control`` field at all are not capped.
    The field is a comparative-claim field, and its absence on (say) a rodent
    pharmacology claim means the question does not apply, not that the answer is bad.
    """
    caps: list[MethodologicalCap] = []
    for facet_name in spec.facet_names:
        assessment = target.facet(facet_name)
        referenced = [
            inputs.claims[claim_id]
            for claim_id in (*assessment.claim_refs, *assessment.counter_claim_refs)
            if claim_id in inputs.claims
        ]
        graded = [claim for claim in referenced if claim.phylogenetic_control is not None]
        if not graded:
            continue
        if not all(claim.has_weak_phylogenetic_control for claim in graded):
            continue
        controls = sorted({str(claim.phylogenetic_control) for claim in graded})
        caps.append(
            MethodologicalCap(
                facet=facet_name,
                max_level=int(cap_level),
                reason=(
                    f"phylogenetic_control in {controls} on all {len(graded)} comparative "
                    "claim(s) cited by this facet "
                    "(atlases/comparative/phylogenetic_controls.md §4)"
                ),
                imposed_by="agent:comparative",
            )
        )
    return tuple(caps)


def derive_caps_for_cohort(
    spec: ModelSpec,
    inputs: RepositoryInputs,
) -> dict[str, tuple[MethodologicalCap, ...]]:
    """Derived methodological caps per target id, for the whole cohort.

    Only the comparative phylogenetic rule is implemented in v0.1. Adding a second rule
    means adding a ``derive_*`` function and calling it here; every rule must state its
    polarity handling (contract §5.4), and all of them go through
    :func:`apply_methodological_cap`.
    """
    return {
        target.target_id: derive_phylogenetic_caps(spec, target, inputs)
        for target in inputs.targets
    }


def cap_cohort(
    spec: ModelSpec,
    inputs: RepositoryInputs,
    *,
    mode: CapMode = "polarity_aware",
    caps_by_target: Mapping[str, Sequence[MethodologicalCap]] | None = None,
) -> tuple[RepositoryInputs, dict[str, tuple[CapApplication, ...]]]:
    """Apply derived methodological caps across a cohort under one mode.

    Args:
        spec: The loaded model specification.
        inputs: The cohort.
        mode: ``polarity_aware`` or ``symmetric``.
        caps_by_target: Override the derived caps, e.g. in a test.

    Returns:
        ``(capped_inputs, records_by_target_id)``. Targets with no derived cap are
        returned unchanged and carry no records.
    """
    caps_by_target = caps_by_target or derive_caps_for_cohort(spec, inputs)
    capped_targets: list[TargetInput] = []
    records: dict[str, tuple[CapApplication, ...]] = {}
    for target in inputs.targets:
        caps = tuple(caps_by_target.get(target.target_id, ()))
        if not caps:
            capped_targets.append(target)
            continue
        capped, applications = apply_methodological_caps(spec, target, caps, mode=mode)
        capped_targets.append(capped)
        if applications:
            records[target.target_id] = applications
    return replace(inputs, targets=tuple(capped_targets)), records
