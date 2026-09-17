"""Input types for the ranking model, decoupled from repository storage.

Why this module exists
----------------------
The ranking model must be testable and reviewable independently of how records are
stored on disk. ``agent:ontology`` owns the schemas, loaders and validators
(``blueprint.loaders``, ``blueprint.records``, ``graph/validate_graph.py``); those
modules are being written in parallel with this one and may not exist yet. So the
mathematics in :mod:`blueprint.ranking.score` and
:mod:`blueprint.ranking.uncertainty` consumes only the frozen dataclasses defined
here, and storage is reached through exactly two adapters:

``from_repository(root)``
    The intended production path. Lazily imports ``blueprint.loaders`` and raises
    :class:`RepositoryLoaderUnavailable` with an actionable message when it is not
    importable yet.

``from_repository_direct(root)``
    A contract-literal fallback that reads the YAML layout described in
    ``docs/DATA_CONTRACT.md`` §2 and §5 with PyYAML only. It exists so the CLI can
    run end-to-end before the shared loaders land. It performs *no* schema
    validation: that is the validator's job, and anything it reads is marked
    ``reader: direct_yaml_fallback`` in the report sidecar so a reviewer can see
    which path produced a number.

Neither adapter invents data. A repository with no facet assessments yields zero
targets with assessments, and the caller is expected to stop and say so.

Nothing in this module grades, scores or interprets evidence. It carries ordinal
levels exactly as the owning agents recorded them.
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "AssessmentStatus",
    "NON_COUNTING_CLAIM_TYPES",
    "AuditAdjustment",
    "AuditSummary",
    "ClaimRecord",
    "FacetAssessment",
    "RepositoryInputs",
    "RepositoryLoaderUnavailable",
    "TargetInput",
    "from_repository",
    "from_repository_direct",
]

AssessmentStatus = Literal["assessed", "not_assessed", "not_applicable"]

#: Red-team verdicts that demote a target outright (contract §6).
DEMOTING_VERDICTS = frozenset({"deprioritise", "insufficient_evidence"})

#: Claim types that are COVERAGE GAPS, not evidence against anything.
#:
#: ``evidence_gap`` means "the study never measured this endpoint" — the question was
#: not asked. It is categorically different from a tested null, where the question was
#: asked and answered negatively, and it may never contribute to any facet's
#: ``counter_level`` (contract §4.1 as amended). Counting it would turn "nobody
#: measured it" into "it was tested and failed", which is the exact conflation contract
#: §5.2 exists to prevent — and would penalise a target for a gap in the literature.
NON_COUNTING_CLAIM_TYPES = frozenset({"evidence_gap"})

#: Levels are ordinal grades on ``evidence_strength_v1`` (contract §5.3).
LEVEL_MIN = 0
LEVEL_MAX = 4


class RepositoryLoaderUnavailable(RuntimeError):
    """Raised when ``blueprint.loaders`` is not importable yet.

    Carries an actionable message rather than a bare ``ImportError`` so that a CLI
    user is told what to do instead of what failed.
    """


@dataclass(frozen=True, slots=True)
class FacetAssessment:
    """One graded facet for one target, exactly as its owning agent recorded it.

    Attributes:
        facet: Facet name from the contract §5 facet catalogue.
        assessment_status: ``assessed`` | ``not_assessed`` | ``not_applicable``.
        level: Supporting-evidence grade in ``0..4``; ``None`` iff not assessed.
        counter_level: Contradicting-evidence grade in ``0..4``; may be ``None``.
        claim_refs: Claim ids supporting the facet proposition.
        counter_claim_refs: Claim ids contradicting it.
        source_refs: Source ids supporting it, permitted in place of ``claim_refs``
            only for a ``database_gradable`` facet carrying
            ``evidence_basis: database_release`` (contract §5.2, R7).
        evidence_basis: ``database_release`` when the grade rests on a pinned database
            release rather than on curated claims; ``None`` otherwise.
        assessed_by: Agent id that graded it (ownership is checked elsewhere).
        rationale: The grader's stated reason. Carried for reporting, never parsed.
        counter_rationale: The grader's reason for ``counter_level``.
        limiting_factor: The named missing study design, per rubric guidance.
    """

    facet: str
    assessment_status: AssessmentStatus = "not_assessed"
    level: int | None = None
    counter_level: int | None = None
    claim_refs: tuple[str, ...] = ()
    counter_claim_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    evidence_basis: str | None = None
    assessed_by: str | None = None
    rationale: str | None = None
    counter_rationale: str | None = None
    limiting_factor: str | None = None

    def __post_init__(self) -> None:
        if self.assessment_status not in ("assessed", "not_assessed", "not_applicable"):
            raise ValueError(f"{self.facet}: illegal assessment_status {self.assessment_status!r}")
        if self.assessment_status == "assessed":
            if self.level is None:
                raise ValueError(f"{self.facet}: assessed facet must carry a level (contract §5.2)")
        elif self.level is not None:
            raise ValueError(
                f"{self.facet}: level must be null unless assessment_status is 'assessed' "
                "— writing 0 for unexamined evidence is a contract violation (§5.2)"
            )
        for name, value in (("level", self.level), ("counter_level", self.counter_level)):
            if value is not None and not (LEVEL_MIN <= int(value) <= LEVEL_MAX):
                raise ValueError(f"{self.facet}: {name}={value!r} outside 0..4 (contract V10)")

    @property
    def is_assessed(self) -> bool:
        """True when the owning agent actually reviewed this facet."""
        return self.assessment_status == "assessed"

    @property
    def is_applicable(self) -> bool:
        """True unless the facet was explicitly recorded as not applicable."""
        return self.assessment_status != "not_applicable"

    def with_level(self, level: int | None) -> FacetAssessment:
        """Return a copy at ``level``, used for perturbation analysis only.

        Setting a level on a ``not_assessed`` facet promotes its status to
        ``assessed`` so the result stays contract-legal; setting ``None`` returns it
        to ``not_assessed``. This is a *hypothetical*, never written to disk.
        """
        if level is None:
            return replace(self, assessment_status="not_assessed", level=None)
        if self.assessment_status == "not_applicable":
            return self
        return replace(self, assessment_status="assessed", level=int(level))


@dataclass(frozen=True, slots=True)
class AuditAdjustment:
    """A red-team downgrade of one facet level (contract §6, rule V12).

    ``to_level < from_level`` always: the contract forbids upgrades, and this class
    enforces it so a malformed audit cannot silently raise a score.
    """

    audit_id: str
    target_id: str
    facet: str
    from_level: int
    to_level: int
    reason: str = ""

    def __post_init__(self) -> None:
        if int(self.to_level) >= int(self.from_level):
            raise ValueError(
                f"{self.audit_id}: adjustment on {self.facet} is not a downgrade "
                f"({self.from_level} -> {self.to_level}); contract rule V12 permits downgrades only"
            )


@dataclass(frozen=True, slots=True)
class AuditSummary:
    """What the red team concluded about a target.

    Attributes:
        verdict: ``retain`` | ``retain_with_downgrade`` | ``deprioritise``
            | ``insufficient_evidence``; ``None`` when the target is unaudited.
        audit_ids: Every audit record covering this target.
        adjustments: Downgrade-only facet adjustments to apply to the inputs.
        unresolved_critical_findings: Count of ``severity: critical`` findings that
            no later audit has recorded as resolved.
        findings_by_severity: Counts per severity, for reporting.
        checks_present: Which mandatory checks appeared (contract §6 catalogue).
    """

    verdict: str | None = None
    audit_ids: tuple[str, ...] = ()
    adjustments: tuple[AuditAdjustment, ...] = ()
    unresolved_critical_findings: int = 0
    findings_by_severity: Mapping[str, int] = field(default_factory=dict)
    checks_present: tuple[str, ...] = ()

    @property
    def is_audited(self) -> bool:
        """True when at least one audit record covers the target (gate G4/V15)."""
        return bool(self.audit_ids)

    @property
    def is_demoted(self) -> bool:
        """True when the verdict demotes the target outright."""
        return self.verdict in DEMOTING_VERDICTS

    @property
    def n_downgrades(self) -> int:
        """Number of facet downgrades applied to this target."""
        return len(self.adjustments)


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    """The part of a claim the ranking model needs: its identity and its sources.

    The model never reads a claim's ``statement``. It needs claim -> source
    resolution only so that ``independent_source_count`` can deduplicate at source
    level (contract P5: paper count is not evidence quality).
    """

    claim_id: str
    source_ids: tuple[str, ...] = ()
    status: str = "active"
    created_by: str | None = None
    phylogenetic_control: str | None = None
    claim_type: str | None = None

    @property
    def is_active(self) -> bool:
        """True unless the claim was contested, downgraded or withdrawn."""
        return self.status == "active"

    @property
    def is_evidence_gap(self) -> bool:
        """True when the claim records that an endpoint was never measured.

        Such a claim is graph-inert and counts towards a coverage gap, never towards
        counter-evidence. See :data:`NON_COUNTING_CLAIM_TYPES`.
        """
        return self.claim_type in NON_COUNTING_CLAIM_TYPES

    @property
    def has_weak_phylogenetic_control(self) -> bool:
        """True when comparative ancestry was not modelled, or it is unknown whether it was.

        ``atlases/comparative/phylogenetic_controls.md`` §4 caps a facet resting only on
        such claims at level 2. ``not_reported`` is treated alongside ``none``
        deliberately: not knowing whether ancestry was modelled is not evidence that it
        was. A claim carrying no ``phylogenetic_control`` field at all is NOT weak by
        this test — the field is a comparative-claim field, and its absence on a
        rodent-pharmacology claim means the question does not apply rather than that the
        answer is bad.
        """
        return self.phylogenetic_control in ("none", "not_reported")


@dataclass(frozen=True, slots=True)
class TargetInput:
    """Everything the ranking model consumes about one target."""

    target_id: str
    symbol: str
    lead_atlas: str | None = None
    dossier_depth: str | None = None
    dossier_status: str | None = None
    facets: Mapping[str, FacetAssessment] = field(default_factory=dict)
    audit: AuditSummary = field(default_factory=AuditSummary)

    def facet(self, name: str) -> FacetAssessment:
        """The assessment for ``name``, or an unassessed placeholder.

        A facet nobody wrote down is ``not_assessed``, never level 0 (contract P8).
        """
        found = self.facets.get(name)
        return found if found is not None else FacetAssessment(facet=name)

    @property
    def has_any_assessment(self) -> bool:
        """True when at least one facet was actually graded."""
        return any(a.is_assessed for a in self.facets.values())

    def referenced_claim_ids(self) -> tuple[str, ...]:
        """Distinct claim ids referenced by this target's facets, sorted."""
        seen: set[str] = set()
        for assessment in self.facets.values():
            seen.update(assessment.claim_refs)
            seen.update(assessment.counter_claim_refs)
        return tuple(sorted(seen))

    def with_evidence_gaps_neutralised(
        self, claims: Mapping[str, ClaimRecord]
    ) -> tuple[TargetInput, tuple[str, ...]]:
        """Drop ``counter_level`` where the only counter-evidence is an evidence gap.

        ``claim_type: evidence_gap`` records that a study never measured an endpoint.
        The question was not asked, so it is not evidence against anything and may
        never contribute to a ``counter_level`` (contract §4.1 as amended). Counting it
        would turn "nobody measured it" into "it was tested and failed" and would
        penalise a target for a gap in the literature — the opposite of what a gap
        means.

        A facet keeps its ``counter_level`` whenever at least one referenced
        counter-claim is a real result: the grade may rest on that one.

        Args:
            claims: The claim index, for resolving ``counter_claim_refs``.

        Returns:
            ``(target, neutralised_facets)`` — the facet names whose ``counter_level``
            was dropped, so the count can be reported as a coverage gap rather than
            vanishing silently.
        """
        neutralised: list[str] = []
        facets = dict(self.facets)
        for name, assessment in self.facets.items():
            if assessment.counter_level is None or not assessment.counter_claim_refs:
                continue
            resolved = [
                claims[claim_id]
                for claim_id in assessment.counter_claim_refs
                if claim_id in claims
            ]
            if not resolved or not all(claim.is_evidence_gap for claim in resolved):
                continue
            facets[name] = replace(assessment, counter_level=None)
            neutralised.append(name)
        if not neutralised:
            return self, ()
        return replace(self, facets=facets), tuple(sorted(neutralised))

    def with_audit_adjustments_applied(self) -> TargetInput:
        """Apply the red team's downgrades to the facet levels.

        Downgrades are applied to the *inputs*, before any scoring, because they
        change the evidence grade itself rather than capping a score. When several
        audits touch the same facet the lowest ``to_level`` wins, so provenance is
        append-only and re-auditing can only ratchet a grade down (contract P6).
        """
        if not self.audit.adjustments:
            return self
        lowest: dict[str, int] = {}
        for adjustment in self.audit.adjustments:
            current = lowest.get(adjustment.facet)
            level = int(adjustment.to_level)
            lowest[adjustment.facet] = level if current is None else min(current, level)
        facets = dict(self.facets)
        for name, level in lowest.items():
            existing = facets.get(name, FacetAssessment(facet=name))
            if existing.assessment_status == "not_applicable":
                continue
            if existing.level is not None and existing.level <= level:
                continue
            facets[name] = replace(existing, assessment_status="assessed", level=level)
        return replace(self, facets=facets)


@dataclass(frozen=True, slots=True)
class RepositoryInputs:
    """A whole cohort plus the claim index needed for source deduplication."""

    targets: tuple[TargetInput, ...] = ()
    claims: Mapping[str, ClaimRecord] = field(default_factory=dict)
    reader: str = "synthetic"
    root: str | None = None
    loaded_on: str = field(default_factory=lambda: _dt.date.today().isoformat())
    notes: tuple[str, ...] = ()

    @property
    def targets_with_assessments(self) -> tuple[TargetInput, ...]:
        """Targets that carry at least one graded facet."""
        return tuple(t for t in self.targets if t.has_any_assessment)

    def source_ids_for(self, claim_ids: Iterable[str]) -> tuple[str, ...]:
        """Distinct source ids behind ``claim_ids``, deduplicated at source level.

        This is the mechanism behind contract P5. Citing one paper from five claims
        contributes one source id, so duplicated evidence cannot inflate a count.
        Claim ids that do not resolve are skipped and are visible as a gap between
        ``claim_count`` and ``independent_source_count`` in the report.
        """
        seen: set[str] = set()
        for claim_id in claim_ids:
            record = self.claims.get(claim_id)
            if record is None:
                continue
            seen.update(record.source_ids)
        return tuple(sorted(seen))

    def with_audit_adjustments_applied(self) -> RepositoryInputs:
        """Cohort copy with every target's red-team downgrades applied."""
        return replace(
            self,
            targets=tuple(t.with_audit_adjustments_applied() for t in self.targets),
        )

    def with_evidence_gaps_neutralised(self) -> tuple[RepositoryInputs, Mapping[str, tuple[str, ...]]]:
        """Cohort copy with evidence-gap-only ``counter_level`` grades dropped.

        Returns:
            ``(inputs, {target_id: neutralised_facet_names})``. The mapping is reported
            so the neutralisation is visible as a coverage gap rather than silent.
        """
        targets: list[TargetInput] = []
        neutralised: dict[str, tuple[str, ...]] = {}
        for target in self.targets:
            updated, facets = target.with_evidence_gaps_neutralised(self.claims)
            targets.append(updated)
            if facets:
                neutralised[target.target_id] = facets
        return replace(self, targets=tuple(targets)), neutralised

    def evidence_gap_claim_ids(self) -> tuple[str, ...]:
        """Every ``evidence_gap`` claim in the cohort, sorted. A coverage statistic."""
        return tuple(sorted(c.claim_id for c in self.claims.values() if c.is_evidence_gap))


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------

_LOADER_HELP = (
    "blueprint.loaders is not usable for ranking inputs.\n"
    "\n"
    "The ranking model reads the repository through the shared loaders owned by\n"
    "agent:ontology (src/blueprint/loaders.py), which must expose either\n"
    "`load_ranking_inputs(root)` or `load_repository(root)`. While it does not:\n"
    "  * run the ranking CLI with --reader direct to use the contract-literal YAML\n"
    "    fallback in blueprint.ranking.inputs.from_repository_direct, or\n"
    "  * construct blueprint.ranking.inputs.RepositoryInputs yourself (this is what\n"
    "    the test suite does), or\n"
    "  * wait for agent:ontology to land the entry point and re-run `make rank`.\n"
    "No data is invented in any of those cases."
)


def from_repository(root: str | Path) -> RepositoryInputs:
    """Load cohort inputs through the shared repository loaders.

    Two entry points are accepted, in order of preference:

    ``loaders.load_ranking_inputs(root)``
        A purpose-built adapter, if ``agent:ontology`` provides one. It may return a
        :class:`RepositoryInputs` directly, or any object/mapping exposing
        ``targets`` and ``claims`` of the types defined in this module.

    ``loaders.load_repository(root)``
        The general repository loader. Its ``Repository`` carries ``seed_registry``,
        ``targets``, ``assessments``, ``audits`` and ``claims`` as ``LoadedRecord``
        objects, and this function projects them onto the ranking model's input
        types. Only the fields the model actually needs are read — ordinal levels,
        claim -> source links, audit verdicts and adjustments — and record legality
        remains the validator's business, not this function's.

    Args:
        root: Repository root directory.

    Returns:
        The cohort as :class:`RepositoryInputs`, with ``reader`` naming the entry
        point that supplied it.

    Raises:
        RepositoryLoaderUnavailable: If ``blueprint.loaders`` cannot be imported, or
            exposes neither entry point. The message names the concrete
            alternatives; this function never falls back silently, because a report
            must say which reader produced it.
    """
    root = Path(root)
    try:
        from blueprint import loaders  # noqa: PLC0415  (deliberately lazy)
    except ImportError as error:  # pragma: no cover - depends on a parallel agent
        raise RepositoryLoaderUnavailable(f"{_LOADER_HELP}\n\nunderlying import error: {error}") from error

    adapter = getattr(loaders, "load_ranking_inputs", None)
    if adapter is not None:
        loaded = adapter(root)
        if isinstance(loaded, RepositoryInputs):
            return replace(loaded, reader="blueprint.loaders.load_ranking_inputs", root=str(root))
        return _coerce_loaded(loaded, root=root, reader="blueprint.loaders.load_ranking_inputs")

    general = getattr(loaders, "load_repository", None)
    if general is None:
        raise RepositoryLoaderUnavailable(
            "blueprint.loaders exposes neither load_ranking_inputs(root) nor "
            "load_repository(root).\n" + _LOADER_HELP
        )
    return _from_loaded_repository(general(root), root=root)


def _coerce_loaded(loaded: Any, *, root: Path, reader: str) -> RepositoryInputs:
    """Accept a loader payload that is a mapping or an object with the same fields."""
    if isinstance(loaded, Mapping):
        targets = loaded.get("targets", ())
        claims = loaded.get("claims", {})
    else:
        targets = getattr(loaded, "targets", ())
        claims = getattr(loaded, "claims", {})
    if not all(isinstance(t, TargetInput) for t in targets):
        raise RepositoryLoaderUnavailable(
            f"{reader} returned targets that are not blueprint.ranking.inputs.TargetInput "
            "instances; the ranking model will not guess their shape."
        )
    if isinstance(claims, Mapping):
        claim_map = {k: v for k, v in claims.items() if isinstance(v, ClaimRecord)}
    else:
        claim_map = {c.claim_id: c for c in claims if isinstance(c, ClaimRecord)}
    return RepositoryInputs(
        targets=tuple(targets),
        claims=claim_map,
        reader=reader,
        root=str(root),
    )


def _from_loaded_repository(repository: Any, *, root: Path) -> RepositoryInputs:
    """Project ``blueprint.loaders.Repository`` onto the ranking model's inputs.

    Reads ``LoadedRecord.raw`` rather than the parsed pydantic models, so that this
    projection does not depend on another agent's model field names. The shapes it
    relies on are the contract's own (§4, §5, §6), which is the shared authority.
    """
    notes: list[str] = []
    violations = list(getattr(repository, "violations", ()) or ())
    if violations:
        # Summarised, not enumerated: record legality is the validator's job
        # (`graph/validate_graph.py --strict`), and echoing hundreds of other agents'
        # violations here would bury this run's own warnings. The count is reported
        # so a reader knows the inputs were not clean.
        examples = "; ".join(str(v) for v in violations[:3])
        notes.append(
            f"{len(violations)} loader violation(s) in the curated records; the ranking model "
            f"read them anyway and does not adjudicate record legality — run "
            f"`graph/validate_graph.py --strict` for the authoritative list. First: {examples}"
        )

    raw_records = _raw_by_symbol(repository)
    seed_registry = getattr(repository, "seed_registry", {}) or {}
    seeds = [t for t in (seed_registry.get("targets") or []) if isinstance(t, Mapping)]

    claims: dict[str, ClaimRecord] = {}
    for record in _iter_records(getattr(repository, "claims", {})):
        raw = record.get("raw", record)
        claim_id = raw.get("claim_id")
        if not claim_id:
            continue
        source_ids = sorted(
            {
                str(item["source_id"])
                for item in raw.get("evidence") or []
                if isinstance(item, Mapping) and item.get("source_id")
            }
        )
        provenance = raw.get("provenance")
        context = raw.get("context")
        claims[str(claim_id)] = ClaimRecord(
            claim_id=str(claim_id),
            source_ids=tuple(source_ids),
            status=str(raw.get("status", "active")),
            created_by=provenance.get("created_by") if isinstance(provenance, Mapping) else None,
            phylogenetic_control=(
                str(context["phylogenetic_control"])
                if isinstance(context, Mapping) and context.get("phylogenetic_control")
                else None
            ),
            claim_type=(str(raw["claim_type"]) if raw.get("claim_type") else None),
        )

    targets: list[TargetInput] = []
    for seed in seeds:
        symbol = str(seed.get("symbol") or str(seed.get("target_id", "")).removeprefix("TGT:"))
        if not symbol:
            continue
        dossier = raw_records["dossiers"].get(symbol, {})
        facets: dict[str, FacetAssessment] = {}
        for document in raw_records["assessments"].get(symbol, []):
            assessed_by = document.get("assessed_by")
            for raw in document.get("facets") or []:
                if not isinstance(raw, Mapping) or "facet" not in raw:
                    continue
                try:
                    facets[str(raw["facet"])] = FacetAssessment(
                        facet=str(raw["facet"]),
                        assessment_status=str(raw.get("assessment_status", "not_assessed")),  # type: ignore[arg-type]
                        level=_as_level(raw.get("level")),
                        counter_level=_as_level(raw.get("counter_level")),
                        claim_refs=_as_tuple(raw.get("claim_refs")),
                        counter_claim_refs=_as_tuple(raw.get("counter_claim_refs")),
                        source_refs=_as_tuple(raw.get("source_refs")),
                        evidence_basis=(
                            str(raw["evidence_basis"]) if raw.get("evidence_basis") else None
                        ),
                        assessed_by=raw.get("assessed_by") or assessed_by,
                        rationale=raw.get("rationale"),
                        counter_rationale=raw.get("counter_rationale"),
                        limiting_factor=raw.get("limiting_factor"),
                    )
                except ValueError as error:
                    notes.append(f"rejected facet for {symbol}: {error}")

        audit = AuditSummary()
        for raw in raw_records["audits"].get(symbol, []):
            audit = _merge_audit(audit, raw, symbol, notes)

        targets.append(
            TargetInput(
                target_id=str(seed.get("target_id") or f"TGT:{symbol}"),
                symbol=symbol,
                lead_atlas=seed.get("lead_atlas") or dossier.get("lead_atlas"),
                dossier_depth=dossier.get("dossier_depth") or seed.get("dossier_depth"),
                dossier_status=dossier.get("status"),
                facets=facets,
                audit=audit,
            )
        )

    notes.extend(
        _orphan_notes(
            assessed_symbols=set(raw_records["assessments"]),
            ranked_symbols={t.symbol for t in targets},
        )
    )
    return RepositoryInputs(
        targets=tuple(targets),
        claims=claims,
        reader="blueprint.loaders.load_repository",
        root=str(root),
        notes=tuple(notes),
    )


def _orphan_notes(*, assessed_symbols: set[str], ranked_symbols: set[str]) -> list[str]:
    """Warn about assessments for symbols the seed registry does not list.

    Silently ignoring them would mean a curated assessment vanishes from every
    report with no trace, which is how curation work gets lost.
    """
    orphans = sorted(assessed_symbols - ranked_symbols)
    if not orphans:
        return []
    return [
        "facet assessments exist for symbols absent from the seed registry "
        f"(not ranked): {', '.join(orphans)}"
    ]


def _iter_records(collection: Any) -> list[dict[str, Any]]:
    """Yield ``{'raw': ...}``-shaped dicts from a loader collection.

    Handles both the ``dict[str, LoadedRecord]`` and ``list[LoadedRecord]`` shapes
    the loaders use, and tolerates a plain mapping in case the shape changes.
    """
    items = collection.values() if isinstance(collection, Mapping) else (collection or ())
    output: list[dict[str, Any]] = []
    for item in items:
        raw = getattr(item, "raw", None)
        if isinstance(raw, Mapping):
            output.append({"raw": dict(raw), "path": getattr(item, "path", "")})
        elif isinstance(item, Mapping):
            output.append({"raw": dict(item), "path": ""})
    return output


def _raw_by_symbol(repository: Any) -> dict[str, dict[str, Any]]:
    """Group dossiers, assessments and audits by target symbol."""
    dossiers: dict[str, dict[str, Any]] = {}
    assessments: dict[str, list[dict[str, Any]]] = {}
    audits: dict[str, list[dict[str, Any]]] = {}

    for record in _iter_records(getattr(repository, "targets", {})):
        raw = record["raw"]
        symbol = str(raw.get("symbol") or str(raw.get("target_id", "")).removeprefix("TGT:"))
        if symbol:
            dossiers[symbol] = raw

    for record in _iter_records(getattr(repository, "assessments", [])):
        raw = record["raw"]
        symbol = str(raw.get("target_id", "")).removeprefix("TGT:")
        if symbol:
            assessments.setdefault(symbol, []).append(raw)

    for record in _iter_records(getattr(repository, "audits", {})):
        raw = record["raw"]
        scope = raw.get("scope") or {}
        if not isinstance(scope, Mapping) or scope.get("kind") != "target":
            continue
        symbol = str(scope.get("id", "")).removeprefix("TGT:")
        if symbol:
            audits.setdefault(symbol, []).append(raw)

    return {"dossiers": dossiers, "assessments": assessments, "audits": audits}


def from_repository_direct(root: str | Path) -> RepositoryInputs:
    """Read cohort inputs straight from the curated YAML layout.

    Contract-literal fallback. It reads exactly the paths ``docs/DATA_CONTRACT.md``
    §2 specifies and nothing else:

    * ``targets/seed_registry.yaml`` — the cohort and each target's lead atlas
    * ``targets/candidates/{SYMBOL}.yaml`` — dossier depth and status
    * ``atlases/*/assessments/{SYMBOL}.yaml`` — facet assessments
    * ``evidence/audits/*/*.yaml`` — audits, adjustments, findings, verdicts
    * ``evidence/claims/*/*.yaml`` — claim -> source resolution

    It does **not** validate records. ``graph/validate_graph.py --strict`` is the
    only authority on record legality; this reader will happily read a record that
    the validator would reject, so reports produced from it carry
    ``reader: direct_yaml_fallback`` in the sidecar.

    Args:
        root: Repository root directory.

    Returns:
        The cohort as :class:`RepositoryInputs`. Missing directories yield empty
        collections rather than errors: an empty repository is a legitimate state
        in Sprint 1 and the caller must handle it, not this function.
    """
    import yaml  # noqa: PLC0415  (kept local so the dataclasses import cleanly)

    root = Path(root)
    notes: list[str] = []

    def _read(path: Path) -> Any:
        """Parse a YAML file. A file that does not exist is absent, not an error."""
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except (OSError, yaml.YAMLError) as error:
            notes.append(f"unreadable: {path.relative_to(root)}: {error}")
            return None

    # -- cohort ------------------------------------------------------------
    registry = _read(root / "targets" / "seed_registry.yaml") or {}
    seeds: list[Mapping[str, Any]] = [t for t in (registry.get("targets") or []) if isinstance(t, Mapping)]

    # -- facet assessments, keyed by symbol --------------------------------
    assessments: dict[str, dict[str, FacetAssessment]] = {}
    for path in sorted((root / "atlases").glob("*/assessments/*.yaml")):
        document = _read(path)
        if not isinstance(document, Mapping):
            continue
        symbol = str(document.get("target_id", "")).removeprefix("TGT:") or path.stem
        assessed_by = document.get("assessed_by")
        bucket = assessments.setdefault(symbol, {})
        for raw in document.get("facets") or []:
            if not isinstance(raw, Mapping) or "facet" not in raw:
                continue
            try:
                bucket[str(raw["facet"])] = FacetAssessment(
                    facet=str(raw["facet"]),
                    assessment_status=str(raw.get("assessment_status", "not_assessed")),  # type: ignore[arg-type]
                    level=_as_level(raw.get("level")),
                    counter_level=_as_level(raw.get("counter_level")),
                    claim_refs=_as_tuple(raw.get("claim_refs")),
                    counter_claim_refs=_as_tuple(raw.get("counter_claim_refs")),
                    source_refs=_as_tuple(raw.get("source_refs")),
                    evidence_basis=(
                        str(raw["evidence_basis"]) if raw.get("evidence_basis") else None
                    ),
                    assessed_by=raw.get("assessed_by") or assessed_by,
                    rationale=raw.get("rationale"),
                    counter_rationale=raw.get("counter_rationale"),
                    limiting_factor=raw.get("limiting_factor"),
                )
            except ValueError as error:
                notes.append(f"rejected facet in {path.relative_to(root)}: {error}")

    # -- audits, keyed by symbol -------------------------------------------
    audits: dict[str, AuditSummary] = {}
    for path in sorted((root / "evidence" / "audits").glob("*/*.yaml")):
        document = _read(path)
        records = document if isinstance(document, list) else [document]
        for record in records:
            if not isinstance(record, Mapping):
                continue
            scope = record.get("scope") or {}
            if not isinstance(scope, Mapping) or scope.get("kind") != "target":
                continue
            symbol = str(scope.get("id", "")).removeprefix("TGT:")
            if not symbol:
                continue
            audits[symbol] = _merge_audit(audits.get(symbol), record, symbol, notes)

    # -- claims -> sources --------------------------------------------------
    claims: dict[str, ClaimRecord] = {}
    for path in sorted((root / "evidence" / "claims").glob("*/*.yaml")):
        document = _read(path)
        records = document if isinstance(document, list) else [document]
        for record in records:
            if not isinstance(record, Mapping) or "claim_id" not in record:
                continue
            source_ids = sorted(
                {
                    str(item["source_id"])
                    for item in record.get("evidence") or []
                    if isinstance(item, Mapping) and item.get("source_id")
                }
            )
            claim_id = str(record["claim_id"])
            context = record.get("context")
            claims[claim_id] = ClaimRecord(
                claim_id=claim_id,
                source_ids=tuple(source_ids),
                status=str(record.get("status", "active")),
                created_by=(record.get("provenance") or {}).get("created_by")
                if isinstance(record.get("provenance"), Mapping)
                else None,
                phylogenetic_control=(
                    str(context["phylogenetic_control"])
                    if isinstance(context, Mapping) and context.get("phylogenetic_control")
                    else None
                ),
                claim_type=(str(record["claim_type"]) if record.get("claim_type") else None),
            )

    # -- assemble -----------------------------------------------------------
    targets: list[TargetInput] = []
    for seed in seeds:
        symbol = str(seed.get("symbol") or str(seed.get("target_id", "")).removeprefix("TGT:"))
        if not symbol:
            continue
        dossier = _read(root / "targets" / "candidates" / f"{symbol}.yaml")
        dossier = dossier if isinstance(dossier, Mapping) else {}
        targets.append(
            TargetInput(
                target_id=str(seed.get("target_id") or f"TGT:{symbol}"),
                symbol=symbol,
                lead_atlas=seed.get("lead_atlas") or dossier.get("lead_atlas"),
                dossier_depth=dossier.get("dossier_depth") or seed.get("dossier_depth"),
                dossier_status=dossier.get("status"),
                facets=assessments.get(symbol, {}),
                audit=audits.get(symbol, AuditSummary()),
            )
        )

    notes.extend(
        _orphan_notes(
            assessed_symbols=set(assessments),
            ranked_symbols={t.symbol for t in targets},
        )
    )
    return RepositoryInputs(
        targets=tuple(targets),
        claims=claims,
        reader="direct_yaml_fallback",
        root=str(root),
        notes=tuple(notes),
    )


def _as_level(value: Any) -> int | None:
    """Coerce a YAML level to ``int`` or ``None`` without inventing a value."""
    if value is None or value == "":
        return None
    return int(value)


def _as_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a YAML list of ids to a tuple of strings."""
    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    return ()


def _merge_audit(
    existing: AuditSummary | None,
    record: Mapping[str, Any],
    symbol: str,
    notes: list[str],
) -> AuditSummary:
    """Fold one audit record into a target's :class:`AuditSummary`.

    Several audits may cover one target (the red team runs every sprint). The merge
    rules are append-only, matching contract P6: audit ids and adjustments
    accumulate, findings accumulate, and the verdict of the *latest* record by
    ``audited_on`` wins — except that a demoting verdict is never overwritten by a
    later non-demoting one without an explicit resolution, which this reader cannot
    verify, so demotion is sticky.
    """
    existing = existing or AuditSummary()
    audit_id = str(record.get("audit_id", f"AUD:unknown:{symbol}"))

    adjustments = list(existing.adjustments)
    for raw in record.get("adjustments") or []:
        if not isinstance(raw, Mapping) or raw.get("kind") != "facet":
            continue
        try:
            adjustments.append(
                AuditAdjustment(
                    audit_id=audit_id,
                    target_id=str(raw.get("target_id") or f"TGT:{symbol}"),
                    facet=str(raw["facet"]),
                    from_level=int(raw["from_level"]),
                    to_level=int(raw["to_level"]),
                    reason=str(raw.get("reason", "")),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            notes.append(f"rejected adjustment in {audit_id}: {error}")

    severities = dict(existing.findings_by_severity)
    critical = existing.unresolved_critical_findings
    for finding in record.get("findings") or []:
        if not isinstance(finding, Mapping):
            continue
        severity = str(finding.get("severity", "info"))
        severities[severity] = severities.get(severity, 0) + 1
        if severity == "critical" and str(finding.get("resolution_status", "unresolved")) != "resolved":
            critical += 1

    checks = set(existing.checks_present)
    for check in record.get("checks") or []:
        if isinstance(check, Mapping) and check.get("check"):
            checks.add(str(check["check"]))

    verdict = record.get("verdict") or existing.verdict
    if existing.verdict in DEMOTING_VERDICTS:
        verdict = existing.verdict  # demotion is sticky; only an explicit audit can lift it

    return AuditSummary(
        verdict=str(verdict) if verdict else None,
        audit_ids=tuple(sorted({*existing.audit_ids, audit_id})),
        adjustments=tuple(adjustments),
        unresolved_critical_findings=critical,
        findings_by_severity=severities,
        checks_present=tuple(sorted(checks)),
    )
