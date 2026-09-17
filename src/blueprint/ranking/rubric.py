"""Load and cross-validate the ranking model's three specification files.

The model has no numeric constants of its own. Every weight, cap, threshold,
pseudo-count and Monte Carlo setting comes from:

* ``models/ranking/facet_rubric_v0_1.yaml``   — per-facet level criteria and polarity
* ``models/ranking/ranking_spec_v0_1.yaml``   — facet -> dimension weights and gates
* ``models/uncertainty/uncertainty_spec_v0_1.yaml`` — level -> Beta and Monte Carlo

This module loads them, hashes them for provenance, and refuses to run when they
disagree. The cross-checks are deliberately strict: a facet present in the spec but
missing from the rubric is an error, not a warning, because the resulting score would
be a number nobody defined criteria for.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "AGGREGATIONS",
    "DEFAULT_MODEL_ROOT",
    "FacetSpec",
    "Gate",
    "ModelSpec",
    "SpecError",
    "load_model_spec",
]

#: Facet catalogue paths, relative to the repository root.
RUBRIC_RELPATH = Path("models/ranking/facet_rubric_v0_1.yaml")
RANKING_RELPATH = Path("models/ranking/ranking_spec_v0_1.yaml")
UNCERTAINTY_RELPATH = Path("models/uncertainty/uncertainty_spec_v0_1.yaml")

#: Repository root inferred from this file's location (src/blueprint/ranking/).
DEFAULT_MODEL_ROOT = Path(__file__).resolve().parents[3]

#: The four facets whose propositions are about humans (contract §5.3).
HUMAN_PROPOSITION_FACETS = frozenset(
    {
        "human_genetic_association",
        "human_phenotype_specificity",
        "human_intervention_evidence",
        "adult_expression_and_timing",
    }
)

DIMENSION_IDS = ("D1", "D2", "D3", "D4", "D5", "D6")
LEVELS = (0, 1, 2, 3, 4)

#: Aggregation operators the implementation knows.
#:
#: ``product`` is the conjunctive primary: the six dimensions are CONDITIONS THAT MUST
#: ALL HOLD, so the composite is their joint probability under an explicit (and false,
#: in a known direction) independence assumption. ``weighted_additive`` is the
#: compensatory counterfactual and ``minimum`` the strictest conjunction.
#: ``geometric_mean`` is available but is order-equivalent to ``product``, so the loader
#: refuses to carry both.
AGGREGATIONS = frozenset({"product", "minimum", "weighted_additive", "geometric_mean"})


class SpecError(ValueError):
    """Raised when the specification files are missing, malformed or inconsistent."""


@dataclass(frozen=True, slots=True)
class FacetSpec:
    """A facet's rubric entry plus the dimension weights it carries."""

    facet: str
    owner: str
    polarity: str
    human_proposition: bool
    feeds: tuple[str, ...]
    weights: Mapping[str, float]
    proposition: str
    level_criteria: Mapping[int, str]
    counter_level_guidance: str
    methodological_cap_applies_to: str = "level"
    database_gradable: bool = False
    gate: str | None = None

    @property
    def is_inverse(self) -> bool:
        """True when higher evidence on this facet *reduces* its dimension."""
        return self.polarity == "inverse"


@dataclass(frozen=True, slots=True)
class Gate:
    """One hard cap on a dimension or on the composite."""

    gate_id: str
    dimension: str
    cap: float
    condition: Mapping[str, Any]
    rationale: str = ""
    cap_scale: str = "absolute"

    def cap_for(self, aggregation: str) -> float:
        """The cap on the composite's own scale under ``aggregation``.

        ``cap_scale: absolute`` returns the cap unchanged, which is what a dimension
        gate wants: dimensions all live on [0, 1] whatever the composite operator is.

        ``cap_scale: dimension_equivalent`` means the declared value is a DIMENSION
        level, and the cap is the composite value a uniform dimension vector at that
        level would produce. Under ``product`` that is ``cap ** 6``; under ``minimum``,
        ``geometric_mean`` and ``weighted_additive`` a uniform vector at ``c`` yields
        ``c``, so the cap passes through. Without this, a composite cap calibrated for
        one operator silently stops binding under another — enforcement that looks
        present and is not.
        """
        if self.cap_scale != "dimension_equivalent":
            return self.cap
        if aggregation == "product":
            return float(self.cap) ** len(DIMENSION_IDS)
        return self.cap


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """The loaded, cross-validated model specification.

    Every numeric parameter the implementation uses is reachable from here, and
    ``sha256`` carries one digest per source file so a report can pin exactly which
    specification produced it.
    """

    facets: Mapping[str, FacetSpec]
    dimension_weights: Mapping[str, float]
    gates: tuple[Gate, ...]
    level_alpha_beta: Mapping[str, tuple[float, float]]
    counter_pseudo_counts: Mapping[str, float]
    n_draws: int
    seed: int
    quantiles: tuple[float, float, float]
    tiers: Mapping[str, Any]
    information_gain: Mapping[str, Any]
    cap_variants: Mapping[str, Any]
    primary_aggregation: str
    alternative_aggregations: tuple[str, ...]
    versions: Mapping[str, str]
    sha256: Mapping[str, str]
    paths: Mapping[str, str]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    # -- derived views -----------------------------------------------------
    @property
    def facet_names(self) -> tuple[str, ...]:
        """All facet names, sorted, for deterministic iteration."""
        return tuple(sorted(self.facets))

    @property
    def database_gradable_facets(self) -> tuple[str, ...]:
        """Facets that may be graded from ``source_refs`` alone (R7, contract §5.2).

        Published for ``agent:ontology``'s schema generator, which reads the flag from
        the rubric rather than hard-coding a facet name.
        """
        return tuple(sorted(name for name, facet in self.facets.items() if facet.database_gradable))

    def facets_for(self, dimension: str) -> tuple[FacetSpec, ...]:
        """Facets feeding ``dimension``, sorted by facet name."""
        return tuple(
            self.facets[name]
            for name in self.facet_names
            if self.facets[name].weights.get(dimension, 0.0) > 0.0
        )

    def beta_parameters(self, level: int | None, counter_level: int | None) -> tuple[float, float]:
        """Beta parameters for one facet grade.

        Args:
            level: Supporting-evidence level in ``0..4``, or ``None`` for
                ``not_assessed``.
            counter_level: Contradicting-evidence level in ``0..4``, or ``None``.

        Returns:
            ``(alpha, beta)`` with the counter-evidence pseudo-counts already added
            to ``beta``. ``not_assessed`` returns the uninformative Beta(1, 1).
        """
        key = "not_assessed" if level is None else str(int(level))
        try:
            alpha, beta = self.level_alpha_beta[key]
        except KeyError as error:  # pragma: no cover - guarded by _validate
            raise SpecError(f"no Beta parameters for level {level!r}") from error
        counter_key = "null" if counter_level is None else str(int(counter_level))
        beta = beta + float(self.counter_pseudo_counts.get(counter_key, 0.0))
        return float(alpha), float(beta)

    def gates_for(self, dimension: str) -> tuple[Gate, ...]:
        """Gates that cap ``dimension`` (use ``'COMPOSITE'`` for composite caps)."""
        return tuple(g for g in self.gates if g.dimension == dimension)


def load_model_spec(root: str | Path | None = None) -> ModelSpec:
    """Load, hash and cross-validate the three specification files.

    Args:
        root: Repository root. Defaults to the repository containing this module.

    Returns:
        A validated :class:`ModelSpec`.

    Raises:
        SpecError: If a file is missing or malformed, or if the rubric and the
            ranking spec disagree about which facets exist, which dimensions a facet
            feeds, or a facet's polarity.
    """
    import yaml  # noqa: PLC0415

    base = Path(root) if root is not None else DEFAULT_MODEL_ROOT
    paths = {
        "rubric": base / RUBRIC_RELPATH,
        "ranking": base / RANKING_RELPATH,
        "uncertainty": base / UNCERTAINTY_RELPATH,
    }
    documents: dict[str, Any] = {}
    digests: dict[str, str] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise SpecError(
                f"specification file missing: {path}\n"
                "The ranking model has no built-in defaults by design: every weight and "
                "prior must be readable, versioned and hashable."
            )
        payload = path.read_bytes()
        digests[name] = hashlib.sha256(payload).hexdigest()
        try:
            documents[name] = yaml.safe_load(payload.decode("utf-8"))
        except yaml.YAMLError as error:
            raise SpecError(f"{path} is not valid YAML: {error}") from error

    rubric = documents["rubric"] or {}
    ranking = documents["ranking"] or {}
    uncertainty = documents["uncertainty"] or {}

    facet_weights = ranking.get("facet_weights") or {}
    if not facet_weights:
        raise SpecError(f"{paths['ranking']}: facet_weights is empty")

    # facet -> {dimension: weight}
    per_facet_weights: dict[str, dict[str, float]] = {}
    for dimension, weights in facet_weights.items():
        if dimension not in DIMENSION_IDS:
            raise SpecError(f"unknown dimension {dimension!r} in facet_weights")
        if not isinstance(weights, Mapping):
            raise SpecError(f"facet_weights.{dimension} must be a mapping of facet -> weight")
        for facet, weight in weights.items():
            value = float(weight)
            if value <= 0.0:
                raise SpecError(
                    f"facet_weights.{dimension}.{facet} = {weight!r}: weights must be positive. "
                    "Remove the facet instead of giving it a zero weight, so the "
                    "facet -> dimension edge set stays explicit."
                )
            per_facet_weights.setdefault(facet, {})[dimension] = value

    rubric_entries = {
        str(entry["facet"]): entry
        for entry in (rubric.get("facets") or [])
        if isinstance(entry, Mapping) and entry.get("facet")
    }

    missing_from_rubric = sorted(set(per_facet_weights) - set(rubric_entries))
    if missing_from_rubric:
        raise SpecError(
            "facets weighted in ranking_spec but absent from facet_rubric: "
            f"{', '.join(missing_from_rubric)}. A weighted facet with no level criteria "
            "would produce a number nobody defined."
        )
    missing_from_spec = sorted(set(rubric_entries) - set(per_facet_weights))
    if missing_from_spec:
        raise SpecError(
            "facets defined in facet_rubric but never weighted in ranking_spec: "
            f"{', '.join(missing_from_spec)}. Every facet must feed a dimension or be "
            "removed from the catalogue."
        )

    facets: dict[str, FacetSpec] = {}
    for name, entry in sorted(rubric_entries.items()):
        # Contract §5.4 vocabulary is `normal` | `inverse`. `direct` is accepted as a
        # deprecated alias and normalised here, so a checker written against the
        # earlier spelling keeps working while the canonical value is the contract's.
        polarity = str(entry.get("polarity", "normal"))
        if polarity == "direct":
            polarity = "normal"
        if polarity not in ("normal", "inverse"):
            raise SpecError(
                f"{name}: polarity must be 'normal' or 'inverse' (contract §5.4), got {polarity!r}"
            )

        # Contract §5.4: the field a methodological-weakness cap may constrain is
        # fixed by the polarity and may not be chosen per facet. Stated per facet in
        # the rubric so other agents' checkers can read it without knowing the rule,
        # and verified here so it cannot contradict the rule.
        declared_cap_field = str(entry.get("methodological_cap_applies_to", ""))
        expected_cap_field = "counter_level" if polarity == "inverse" else "level"
        if not declared_cap_field:
            raise SpecError(
                f"{name}: methodological_cap_applies_to is required (contract §5.4); "
                f"for polarity {polarity} it must be {expected_cap_field!r}"
            )
        if declared_cap_field != expected_cap_field:
            raise SpecError(
                f"{name}: methodological_cap_applies_to is {declared_cap_field!r} but polarity "
                f"{polarity} requires {expected_cap_field!r} (contract §5.4). Capping `level` on "
                "an inverse-polarity facet would turn a methodological weakness into an "
                "optimistic conclusion."
            )

        human_proposition = bool(entry.get("human_proposition", False))
        expected_human = name in HUMAN_PROPOSITION_FACETS
        if human_proposition != expected_human:
            raise SpecError(
                f"{name}: human_proposition={human_proposition} contradicts contract §5.3, "
                f"which fixes the human-proposition facet set to {sorted(HUMAN_PROPOSITION_FACETS)}"
            )

        criteria_raw = entry.get("level_criteria") or {}
        criteria = {int(k): str(v) for k, v in criteria_raw.items()}
        missing_levels = [level for level in LEVELS if level not in criteria]
        if missing_levels:
            raise SpecError(f"{name}: level_criteria missing levels {missing_levels}")

        feeds = tuple(str(d) for d in (entry.get("feeds") or ()))
        weights = per_facet_weights[name]
        if set(feeds) != set(weights):
            raise SpecError(
                f"{name}: rubric `feeds` {sorted(feeds)} disagrees with the dimensions "
                f"weighted in ranking_spec {sorted(weights)}"
            )

        facets[name] = FacetSpec(
            facet=name,
            owner=str(entry.get("owner", "unknown")),
            polarity=polarity,
            human_proposition=human_proposition,
            feeds=tuple(sorted(feeds)),
            weights=dict(sorted(weights.items())),
            proposition=str(entry.get("proposition", "")).strip(),
            level_criteria=criteria,
            counter_level_guidance=str(entry.get("counter_level_guidance", "")).strip(),
            methodological_cap_applies_to=expected_cap_field,
            database_gradable=bool(entry.get("database_gradable", False)),
            gate=(str(entry["gate"]) if entry.get("gate") else None),
        )

    declared_count = rubric.get("facet_count")
    if declared_count is not None and int(declared_count) != len(facets):
        raise SpecError(
            f"{paths['rubric']}: facet_count says {declared_count} but {len(facets)} facets are defined"
        )

    # R7 / contract §5.2: `source_refs`-only grading is permitted ONLY for facets the
    # rubric flags `database_gradable: true`. agent:ontology reads this flag from here
    # rather than hard-coding a facet name, so the set is published deliberately and
    # kept narrow: a facet graded from a database annotation cannot satisfy the claim
    # requirements that make a grade traceable to biological evidence.
    database_gradable = {name for name, facet in facets.items() if facet.database_gradable}
    if not database_gradable <= {"tractability"}:
        raise SpecError(
            "database_gradable is flagged on "
            f"{sorted(database_gradable)}; contract §5.2 permits it for `tractability` "
            "only at present. Widening it needs a schema-change request, because a "
            "database annotation cannot carry the provenance a claim reference does."
        )

    # The flat polarity index is published for consumers that do not walk the facet
    # list (contract §5.4 makes this file the polarity authority). It must not drift.
    polarity_index = rubric.get("polarity_index")
    if polarity_index is None:
        raise SpecError(f"{paths['rubric']}: polarity_index is required (contract §5.4)")
    normalised_index = {
        str(k): ("normal" if str(v) == "direct" else str(v)) for k, v in polarity_index.items()
    }
    declared_polarities = {name: facet.polarity for name, facet in facets.items()}
    if normalised_index != declared_polarities:
        difference = {
            name: (normalised_index.get(name), declared_polarities.get(name))
            for name in set(normalised_index) | set(declared_polarities)
            if normalised_index.get(name) != declared_polarities.get(name)
        }
        raise SpecError(
            f"{paths['rubric']}: polarity_index disagrees with facets[].polarity "
            f"(index, facet): {difference}"
        )

    composite = ranking.get("composite") or {}
    primary = composite.get("primary") or {}
    primary_aggregation = str(primary.get("id", ""))
    if primary_aggregation not in AGGREGATIONS:
        raise SpecError(
            f"composite.primary.id must be one of {sorted(AGGREGATIONS)}, got "
            f"{primary_aggregation!r}"
        )
    for dimension in DIMENSION_IDS:
        if not facet_weights.get(dimension):
            raise SpecError(f"dimension {dimension} has no facets feeding it")

    variants = tuple(
        str(entry["id"])
        for entry in (composite.get("variants_for_sensitivity") or [])
        if isinstance(entry, Mapping) and entry.get("id")
    )
    if not variants:
        raise SpecError(
            "composite.variants_for_sensitivity is empty; sensitivity analysis is mandatory"
        )
    unknown_variants = sorted(set(variants) - AGGREGATIONS)
    if unknown_variants:
        raise SpecError(f"unknown sensitivity variant(s) {unknown_variants}")
    if primary_aggregation in variants:
        raise SpecError(
            f"{primary_aggregation!r} is both the primary and a sensitivity variant; "
            "comparing an operator with itself measures nothing"
        )
    # `geometric_mean` is a strictly monotone transform of `product`, so it induces an
    # identical ordering and an identical tau-b. Carrying both would overstate how many
    # independent operators the ordering has been tested against.
    if {"product", "geometric_mean"} <= {primary_aggregation, *variants}:
        raise SpecError(
            "product and geometric_mean induce the same ordering (geometric_mean is a "
            "strictly monotone transform of product), so comparing them is a tautology. "
            "Declare one of them, not both."
        )

    # Dimension weights belong to whichever aggregation actually uses them. Under the
    # conjunctive primary (`product`) that is the `weighted_additive` variant; the
    # primary is unweighted because a conjunction has no weights.
    weight_source: Mapping[str, Any] = primary
    if not primary.get("weights"):
        for entry in composite.get("variants_for_sensitivity") or []:
            if isinstance(entry, Mapping) and entry.get("weights"):
                weight_source = entry
                break
    dimension_weights = {str(k): float(v) for k, v in (weight_source.get("weights") or {}).items()}
    if sorted(dimension_weights) != sorted(DIMENSION_IDS):
        raise SpecError(
            f"dimension weights must cover exactly {list(DIMENSION_IDS)}, got "
            f"{sorted(dimension_weights)}. They may live on composite.primary or on the "
            "variant that uses them, but the weighted aggregation needs all six."
        )

    gates: list[Gate] = []
    for entry in ranking.get("gates") or []:
        if not isinstance(entry, Mapping):
            continue
        dimension = str(entry.get("dimension", ""))
        if dimension not in (*DIMENSION_IDS, "COMPOSITE"):
            raise SpecError(f"gate {entry.get('id')!r}: unknown dimension {dimension!r}")
        cap = entry.get("cap")
        if cap is None or not (0.0 <= float(cap) <= 1.0):
            raise SpecError(f"gate {entry.get('id')!r}: cap must be in [0, 1], got {cap!r}")
        condition = entry.get("condition") or {}
        if not isinstance(condition, Mapping) or not condition:
            raise SpecError(f"gate {entry.get('id')!r}: condition is empty")
        cap_scale = str(entry.get("cap_scale", "absolute"))
        if cap_scale not in ("absolute", "dimension_equivalent"):
            raise SpecError(
                f"gate {entry.get('id')!r}: cap_scale must be 'absolute' or "
                f"'dimension_equivalent', got {cap_scale!r}"
            )
        if dimension != "COMPOSITE" and cap_scale != "absolute":
            raise SpecError(
                f"gate {entry.get('id')!r}: only a COMPOSITE gate may use a "
                "dimension-equivalent cap scale; dimensions all live on [0, 1]"
            )
        gates.append(
            Gate(
                gate_id=str(entry.get("id", f"gate_{len(gates)}")),
                dimension=dimension,
                cap=float(cap),
                condition=dict(condition),
                rationale=str(entry.get("rationale", "")).strip(),
                cap_scale=cap_scale,
            )
        )
    if not gates:
        raise SpecError("ranking_spec declares no gates; at least the D2 confound gate is required")

    level_map_raw = uncertainty.get("level_to_beta") or {}
    level_alpha_beta: dict[str, tuple[float, float]] = {}
    for key, entry in level_map_raw.items():
        if not isinstance(entry, Mapping):
            continue
        name = "not_assessed" if str(key) == "not_assessed" else str(int(key))
        alpha, beta = float(entry["alpha"]), float(entry["beta"])
        if alpha <= 0 or beta <= 0:
            raise SpecError(f"level_to_beta.{key}: alpha and beta must be positive")
        level_alpha_beta[name] = (alpha, beta)
    required_keys = {"not_assessed", *(str(level) for level in LEVELS)}
    missing_keys = sorted(required_keys - set(level_alpha_beta))
    if missing_keys:
        raise SpecError(f"level_to_beta missing entries for {missing_keys}")
    _check_level_ladder(level_alpha_beta)

    counter_raw = (uncertainty.get("counter_level_to_pseudo_counts") or {}).get("values") or {}
    counter_pseudo_counts: dict[str, float] = {}
    for key, value in counter_raw.items():
        name = "null" if key is None or str(key) in ("null", "None", "~") else str(int(key))
        counter_pseudo_counts[name] = float(value)
    missing_counter = sorted({"null", *(str(level) for level in LEVELS)} - set(counter_pseudo_counts))
    if missing_counter:
        raise SpecError(f"counter_level_to_pseudo_counts.values missing entries for {missing_counter}")
    ladder = [counter_pseudo_counts[str(level)] for level in LEVELS]
    if any(b < a for a, b in zip(ladder, ladder[1:], strict=False)):
        raise SpecError(f"counter-evidence pseudo-counts must be non-decreasing in level, got {ladder}")

    monte_carlo = uncertainty.get("monte_carlo") or {}
    n_draws = int(monte_carlo.get("n_draws", 0))
    if n_draws < 100:
        raise SpecError(f"monte_carlo.n_draws must be at least 100, got {n_draws}")
    seed = int(monte_carlo.get("seed", -1))
    if seed < 0:
        raise SpecError("monte_carlo.seed must be a non-negative integer (determinism requirement)")

    quantile_list = (uncertainty.get("intervals") or {}).get("reported_quantiles") or []
    if len(quantile_list) != 3:
        raise SpecError(f"intervals.reported_quantiles must have exactly 3 entries, got {quantile_list!r}")
    quantiles = tuple(float(q) for q in quantile_list)
    if not 0.0 < quantiles[0] < quantiles[1] < quantiles[2] < 1.0:
        raise SpecError(f"intervals.reported_quantiles must be strictly increasing in (0,1): {quantiles}")

    tiers = ranking.get("tiers") or {}
    for key in ("min_coverage", "top_fraction", "mid_fraction"):
        if key not in tiers:
            raise SpecError(f"tiers.{key} is required")
        if not 0.0 < float(tiers[key]) <= 1.0:
            raise SpecError(f"tiers.{key} must be in (0, 1]")

    information_gain = ranking.get("information_gain") or {}
    multipliers = information_gain.get("unresolved_multiplier") or {}
    for key in ("not_assessed", "assessed", "not_applicable"):
        if key not in multipliers:
            raise SpecError(f"information_gain.unresolved_multiplier.{key} is required")

    # Contract §5.4 obliges the spec to carry a `symmetric_caps` sensitivity variant so
    # the cost of the precautionary cap asymmetry is measured rather than assumed.
    cap_variants = ranking.get("cap_variants") or {}
    variant_ids = {
        str(entry.get("id"))
        for entry in (cap_variants.get("variants") or [])
        if isinstance(entry, Mapping)
    }
    if not {"polarity_aware", "symmetric_caps"} <= variant_ids:
        raise SpecError(
            "cap_variants.variants must declare both `polarity_aware` and "
            "`symmetric_caps` (contract §5.4: the asymmetry's effect on ranks must be "
            f"measured, not assumed); found {sorted(variant_ids)}"
        )
    threshold = (cap_variants.get("sensitivity_threshold") or {}).get("rank_positions")
    if threshold is None or float(threshold) <= 0:
        raise SpecError(
            "cap_variants.sensitivity_threshold.rank_positions must be a positive number "
            "(contract §5.4 requires a stated threshold for flagging cap-sensitive ranks)"
        )

    return ModelSpec(
        facets=facets,
        dimension_weights=dict(sorted(dimension_weights.items())),
        gates=tuple(gates),
        level_alpha_beta=level_alpha_beta,
        counter_pseudo_counts=counter_pseudo_counts,
        n_draws=n_draws,
        seed=seed,
        quantiles=(quantiles[0], quantiles[1], quantiles[2]),
        tiers=dict(tiers),
        information_gain=dict(information_gain),
        cap_variants=dict(cap_variants),
        alternative_aggregations=variants,
        primary_aggregation=primary_aggregation,
        versions={
            "rubric_version": str(rubric.get("rubric_version", "unknown")),
            "ranking_spec_version": str(ranking.get("spec_version", "unknown")),
            "uncertainty_spec_version": str(uncertainty.get("spec_version", "unknown")),
            "calibration_status": str(ranking.get("calibration_status", "uncalibrated_subjective")),
            "scale": str(rubric.get("scale", "evidence_strength_v1")),
        },
        sha256=dict(sorted(digests.items())),
        paths={name: str(path) for name, path in sorted(paths.items())},
        raw={"rubric": rubric, "ranking": ranking, "uncertainty": uncertainty},
    )


def _check_level_ladder(level_alpha_beta: Mapping[str, tuple[float, float]]) -> None:
    """Assert the level -> Beta ladder has the properties the spec claims.

    The spec file asserts three properties in prose. They are checked here so that
    editing the pseudo-counts without thinking cannot silently break the model's
    stated semantics:

    1. Means increase strictly with level (higher grade is more favourable).
    2. ``not_assessed`` is strictly the widest distribution (contract P8).
    3. The ``not_assessed`` mean does not exceed the level-2 mean, so absence of
       assessment is never rewarded above moderate real evidence.
    """

    def mean(key: str) -> float:
        alpha, beta = level_alpha_beta[key]
        return alpha / (alpha + beta)

    def variance(key: str) -> float:
        alpha, beta = level_alpha_beta[key]
        total = alpha + beta
        return (alpha * beta) / (total * total * (total + 1.0))

    means = [mean(str(level)) for level in LEVELS]
    if any(b <= a for a, b in zip(means, means[1:], strict=False)):
        raise SpecError(f"level_to_beta means must increase strictly with level, got {means}")

    unknown_variance = variance("not_assessed")
    for level in LEVELS:
        if variance(str(level)) >= unknown_variance:
            raise SpecError(
                "level_to_beta: not_assessed must be strictly the widest distribution "
                f"(contract P8); level {level} has variance {variance(str(level)):.4f} >= "
                f"{unknown_variance:.4f}"
            )
    if mean("not_assessed") > mean("2"):
        raise SpecError(
            "level_to_beta: the not_assessed mean exceeds the level-2 mean, which would "
            "reward absence of assessment over moderate real evidence"
        )
