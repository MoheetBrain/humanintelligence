"""Sprint-4 virtual pharmacology — typed interfaces, deliberately inactive.

Every function here raises :class:`NotImplementedError` naming gate G5 and the sprint
that owns it. The signatures exist so that Sprint-4 work has a shape to fill and a
contract to respect; the bodies do not exist because the gate has not opened, and
because writing them now would invite running them now.

Two rules bind every function in this module, without exception:

**Everything stays in silico.** These are structural bioinformatics, cheminformatics
and simulation interfaces. Nothing here performs, plans, designs, requests or
recommends any wet-lab, in-vitro, ex-vivo, animal or human experiment, including
self-experimentation (``docs/COMPUTATIONAL_ONLY_POLICY.md``).

**No output is ever a protocol, a dose, a route, a regimen or a sourcing route.**
Not for anyone, not as an example, not in a docstring, not in a test fixture. The
return types below are deliberately shaped so that the natural output is a model
artefact — a pose, a score, a predicted property, a Pareto set — and never an
instruction. `ADMETPrediction` carries predicted properties, not human exposures;
`DockingResult` carries poses and scores, not recommendations.

The gate
--------
Nothing in this module may be called for a target that has not passed
:func:`blueprint.pharmacology.gates.eligible_for_chemistry`. Every function takes a
``gate`` argument for exactly that reason: the gate decision is a *parameter*, so a
caller cannot forget it, and :func:`require_gate` refuses a decision that is not a
pass.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from blueprint.pharmacology.gates import GateDecision

__all__ = [
    "ADMETPrediction",
    "BBBPrediction",
    "BioactivityLandscape",
    "DockingResult",
    "GateNotPassedError",
    "GenerativeProposal",
    "Ligand",
    "MDTrajectorySummary",
    "MultiObjectiveResult",
    "NOT_IMPLEMENTED_MESSAGE",
    "Pharmacophore",
    "Pocket",
    "QSARModel",
    "SelectivityProfile",
    "Structure",
    "bbb_permeability",
    "chembl_landscape",
    "detect_pockets",
    "dock_ligands",
    "fit_qsar",
    "generate_candidates",
    "molecular_dynamics",
    "multi_objective_optimise",
    "pharmacophore_model",
    "predict_admet",
    "require_gate",
    "retrieve_ligands",
    "retrieve_structures",
    "selectivity_profile",
]

#: The message every stub raises. It names the gate, the sprint and the owner so a
#: caller who hits it knows what has to happen before this code can exist.
NOT_IMPLEMENTED_MESSAGE = (
    "{name} is an interface only and is not implemented. Virtual pharmacology is "
    "gated behind G5 (docs/BLACKBOARD_PROTOCOL.md §3) and scheduled for Sprint 4 "
    "(ROADMAP.md), owned by agent:integration. Sprint 4 runs only for targets that "
    "survived causal integration AND red-team review, everything in it stays in "
    "silico, and no output of it is ever a protocol, dose, route or sourcing route "
    "(docs/COMPUTATIONAL_ONLY_POLICY.md)."
)


class GateNotPassedError(PermissionError):
    """Raised when a pharmacology interface is called without a passing gate G5."""


def require_gate(gate: GateDecision | None, *, what: str) -> GateDecision:
    """Refuse to proceed unless ``gate`` is a passing G5 decision.

    Args:
        gate: The decision from
            :func:`blueprint.pharmacology.gates.explain_gate`.
        what: What was being attempted, for the error message.

    Returns:
        The decision, unchanged, when it is a pass.

    Raises:
        GateNotPassedError: If ``gate`` is missing, is not a
            :class:`~blueprint.pharmacology.gates.GateDecision`, or is a refusal. A
            truthy duck-typed stand-in is rejected too: a gate that can be spoofed by
            passing ``True`` is not a gate.
    """
    if not isinstance(gate, GateDecision):
        raise GateNotPassedError(
            f"{what} requires a GateDecision from blueprint.pharmacology.gates."
            f"explain_gate(); got {type(gate).__name__}. Gate G5 cannot be satisfied by "
            "passing a truthy value."
        )
    if not gate.eligible:
        raise GateNotPassedError(f"{what} refused by gate G5. {gate.reason}")
    return gate


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Structure:
    """One retrieved or predicted protein structure. Provenance is mandatory."""

    identifier: str
    source: Literal["pdb", "alphafold", "homology_model"]
    resolution_angstrom: float | None = None
    method: str | None = None
    chains: tuple[str, ...] = ()
    coverage_residues: tuple[int, int] | None = None
    confidence: Mapping[str, float] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Pocket:
    """A detected binding site. A pocket is geometry, never a claim of druggability."""

    pocket_id: str
    structure_identifier: str
    residues: tuple[str, ...]
    volume_cubic_angstrom: float | None = None
    detector: str | None = None
    detector_score: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Ligand:
    """A retrieved ligand. Identifiers are fetched, never typed (contract §7)."""

    chembl_id: str | None = None
    smiles: str | None = None
    inchikey: str | None = None
    name: str | None = None
    max_phase: int | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BioactivityLandscape:
    """Summary of the measured bioactivity around one target, as reported."""

    target_id: str
    n_ligands: int
    n_activities: int
    assay_types: tuple[str, ...] = ()
    potency_summary: Mapping[str, float] = field(default_factory=dict)
    data_version: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QSARModel:
    """A fitted structure-activity model, with its validation, never without."""

    model_id: str
    algorithm: str
    n_training: int
    features: tuple[str, ...] = ()
    validation: Mapping[str, float] = field(default_factory=dict)
    applicability_domain: Mapping[str, Any] = field(default_factory=dict)
    calibration_status: str = "uncalibrated_subjective"
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DockingResult:
    """Poses and scores for one ligand against one pocket.

    A docking score is a ranking device for further simulation. It is not a binding
    affinity, and it is never evidence of an effect (contract rule V16).
    """

    ligand: Ligand
    pocket_id: str
    scores: tuple[float, ...]
    pose_artefacts: tuple[str, ...] = ()
    software: str | None = None
    scoring_function: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MDTrajectorySummary:
    """Summary statistics of a simulation. The trajectory itself is an artefact path."""

    system_id: str
    n_replicas: int
    simulated_ns: float
    force_field: str | None = None
    observables: Mapping[str, float] = field(default_factory=dict)
    convergence: Mapping[str, Any] = field(default_factory=dict)
    artefact_paths: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Pharmacophore:
    """A pharmacophore hypothesis: features and geometry, plus how it was validated."""

    model_id: str
    features: tuple[Mapping[str, Any], ...] = ()
    tolerance_angstrom: float | None = None
    derived_from: tuple[str, ...] = ()
    validation: Mapping[str, float] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GenerativeProposal:
    """A generated structure proposal. In-silico only, and never a synthesis route.

    ``synthetic_accessibility`` is a model score. It is not a route, and no field of
    this class may ever carry reagents, conditions or a procedure.
    """

    proposal_id: str
    smiles: str
    generator: str
    objective_scores: Mapping[str, float] = field(default_factory=dict)
    novelty: Mapping[str, float] = field(default_factory=dict)
    synthetic_accessibility: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BBBPrediction:
    """Predicted blood-brain-barrier behaviour. A prediction, not an exposure."""

    ligand: Ligand
    predicted_class: str
    model_id: str
    uncertainty: Mapping[str, float] = field(default_factory=dict)
    applicability: str | None = None
    calibration_status: str = "uncalibrated_subjective"
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ADMETPrediction:
    """Predicted ADMET properties.

    Properties only. This class carries no human exposure, no dose, no route and no
    schedule, and must never be extended to carry one.
    """

    ligand: Ligand
    properties: Mapping[str, float] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    model_ids: tuple[str, ...] = ()
    calibration_status: str = "uncalibrated_subjective"
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SelectivityProfile:
    """Predicted or measured activity across a family, with the off-targets named."""

    ligand: Ligand
    on_target: str
    family_members: tuple[str, ...] = ()
    margins: Mapping[str, float] = field(default_factory=dict)
    liabilities: tuple[str, ...] = ()
    evidence_basis: str = "predicted"
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MultiObjectiveResult:
    """A Pareto set under objectives, with safety expressed as CONSTRAINTS.

    ``constraints_enforced`` is not a courtesy field. README §3 and
    ``ranking_spec_v0_1.yaml`` §4 both require safety to be a constraint rather than a
    cost, and an optimiser that put a safety term in ``objectives`` with a weight
    would be violating that. Any implementation must reject such a configuration.
    """

    pareto_front: tuple[Mapping[str, float], ...] = ()
    objectives: tuple[str, ...] = ()
    constraints_enforced: tuple[str, ...] = ()
    infeasible_count: int = 0
    provenance: Mapping[str, Any] = field(default_factory=dict)


class ProvenanceSink(Protocol):
    """Anything that can record a provenance entry for a pharmacology artefact."""

    def record(self, entry: Mapping[str, Any]) -> None:  # pragma: no cover - protocol
        ...


# ---------------------------------------------------------------------------
# Interfaces (all inactive)
# ---------------------------------------------------------------------------


def retrieve_structures(
    target_id: str,
    gate: GateDecision,
    *,
    sources: Sequence[str] = ("pdb", "alphafold"),
    snapshot_dir: str | None = None,
) -> tuple[Structure, ...]:
    """Retrieve experimental and predicted structures for a target.

    Sprint 4. Snapshots every response immutably under ``data/raw/`` per contract P7,
    so that all downstream structural work is rebuildable offline.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="retrieve_structures")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="retrieve_structures"))


def detect_pockets(
    structures: Sequence[Structure],
    gate: GateDecision,
    *,
    detector: str = "unspecified",
    min_volume_cubic_angstrom: float | None = None,
) -> tuple[Pocket, ...]:
    """Detect candidate binding pockets. Geometry only; never a druggability claim.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="detect_pockets")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="detect_pockets"))


def retrieve_ligands(
    target_id: str,
    gate: GateDecision,
    *,
    include_inactives: bool = True,
    max_records: int | None = None,
) -> tuple[Ligand, ...]:
    """Retrieve known ligands for a target from a pinned ChEMBL release.

    ``include_inactives`` defaults to ``True`` on purpose: a landscape built only from
    actives is a biased landscape, and inactives are what make a QSAR model honest.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="retrieve_ligands")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="retrieve_ligands"))


def chembl_landscape(
    target_id: str,
    gate: GateDecision,
    *,
    data_version: str | None = None,
) -> BioactivityLandscape:
    """Summarise the measured bioactivity landscape around a target.

    Binding and mechanism records are never efficacy evidence (contract rule V16); the
    returned object is a description of what has been measured, nothing more.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="chembl_landscape")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="chembl_landscape"))


def fit_qsar(
    landscape: BioactivityLandscape,
    gate: GateDecision,
    *,
    algorithm: str = "unspecified",
    split: str = "scaffold",
    seed: int | None = None,
) -> QSARModel:
    """Fit a structure-activity model, reporting validation and applicability domain.

    ``split`` defaults to ``scaffold`` because a random split over congeneric series
    reports a performance the model does not have.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="fit_qsar")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="fit_qsar"))


def dock_ligands(
    ligands: Sequence[Ligand],
    pocket: Pocket,
    gate: GateDecision,
    *,
    software: str | None = None,
    n_poses: int = 1,
    seed: int | None = None,
) -> tuple[DockingResult, ...]:
    """Dock ligands into a pocket. Scores rank candidates for further simulation.

    A docking score is not a binding affinity and not an effect.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="dock_ligands")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="dock_ligands"))


def molecular_dynamics(
    system_id: str,
    gate: GateDecision,
    *,
    n_replicas: int = 1,
    ns_per_replica: float = 0.0,
    force_field: str | None = None,
    seed: int | None = None,
) -> MDTrajectorySummary:
    """Run molecular dynamics on a docked or apo system and summarise it.

    Replica count and convergence diagnostics are part of the result because a single
    unconverged trajectory is an anecdote.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="molecular_dynamics")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="molecular_dynamics"))


def pharmacophore_model(
    ligands: Sequence[Ligand],
    gate: GateDecision,
    *,
    aligned_on: str | None = None,
) -> Pharmacophore:
    """Derive a pharmacophore hypothesis from a ligand set.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="pharmacophore_model")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="pharmacophore_model"))


def generate_candidates(
    pharmacophore: Pharmacophore,
    gate: GateDecision,
    *,
    generator: str = "unspecified",
    n_proposals: int = 0,
    constraints: Mapping[str, Any] | None = None,
    seed: int | None = None,
) -> tuple[GenerativeProposal, ...]:
    """Generate in-silico structure proposals under constraints.

    Proposals are computational objects. This function must never emit a synthesis
    route, reagents, conditions or a procedure, and ``GenerativeProposal`` has no
    field that could carry one.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="generate_candidates")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="generate_candidates"))


def bbb_permeability(
    ligands: Sequence[Ligand],
    gate: GateDecision,
    *,
    model_id: str = "unspecified",
) -> tuple[BBBPrediction, ...]:
    """Predict blood-brain-barrier behaviour, with uncertainty and applicability.

    A prediction about a molecule's properties, never a statement about what would
    happen in a person.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="bbb_permeability")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="bbb_permeability"))


def predict_admet(
    ligands: Sequence[Ligand],
    gate: GateDecision,
    *,
    endpoints: Sequence[str] = (),
) -> tuple[ADMETPrediction, ...]:
    """Predict ADMET properties for a ligand set.

    Properties only. No human exposure, dose, route or schedule is produced, and none
    may be inferred from the output.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="predict_admet")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="predict_admet"))


def selectivity_profile(
    ligand: Ligand,
    target_id: str,
    gate: GateDecision,
    *,
    family_members: Sequence[str] = (),
    basis: Literal["predicted", "measured", "mixed"] = "predicted",
) -> SelectivityProfile:
    """Profile a ligand across its target's family and name the liabilities.

    Off-targets are named, not summarised into a score: "selective" without a list of
    what was tested is not a finding.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="selectivity_profile")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="selectivity_profile"))


def multi_objective_optimise(
    candidates: Sequence[GenerativeProposal],
    gate: GateDecision,
    *,
    objectives: Sequence[str] = (),
    hard_constraints: Sequence[str] = (),
) -> MultiObjectiveResult:
    """Optimise candidates under objectives, with safety as HARD CONSTRAINTS.

    Any implementation must refuse a configuration that places a safety term in
    ``objectives`` rather than in ``hard_constraints``. Safety is a constraint, not a
    cost to be traded away (README §3), and an optimiser that can trade it is the
    wrong optimiser regardless of the weight chosen.

    Sprint 4.

    Raises:
        GateNotPassedError: If ``gate`` is not a passing G5 decision.
        NotImplementedError: Always, once the gate check passes.
    """
    require_gate(gate, what="multi_objective_optimise")
    raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE.format(name="multi_objective_optimise"))
