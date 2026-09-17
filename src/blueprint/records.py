"""Pydantic v2 models for every record type.

Why both these models and the JSON Schemas
------------------------------------------
The JSON Schemas are the portable contract: any tool in any language can check a record
against them, and they are what contract rule V1 refers to. These models add the
constraints JSON Schema cannot express, and they give the rest of the library typed
objects instead of dictionaries.

Enforced here and NOT in JSON Schema:

* **Ordinal-only uncertainty (V10).** ``representation`` must be ``ordinal_grade`` and
  ``level`` an integer 0-4 — expressible in JSON Schema, but also enforced here so that
  a record constructed in Python cannot bypass it.
* **No hand-written probability (V9).** ``level`` must be an ``int``, not a float that
  happens to be integral: ``level: 0.85`` is exactly the failure mode contract P3
  exists to prevent, and ``bool`` is rejected as well.
* **Downgrade-only audit adjustments (V12).** Comparing two sibling fields
  (``to_level`` against ``from_level``) is impossible in JSON Schema. For
  ``field: level`` a downgrade means ``to_level < from_level``; for
  ``field: counter_level`` it means ``to_level > from_level``, because RAISING the
  contradicting-evidence grade is a downgrade of the target's standing.
* **Assessment status consistency (§5.2).** ``not_assessed`` requires ``level: null``;
  an assessed facet requires an integer level and a rationale. Writing ``0`` for a facet
  nobody examined is refused, because "nobody looked" and "searched and found nothing"
  are different facts.
* **Evidence-item identity.** ``evidence_id`` is derived from the parent claim id and
  the item's position; a hand-written one that disagrees is refused.
* **Withdrawal needs a reason** (the superseding audit itself is cross-record and is
  checked by rule V14 in :mod:`blueprint.validate`).

Design rules:

* ``extra="forbid"`` everywhere, mirroring ``additionalProperties: false``. Agents must
  not smuggle fields past the contract.
* Enum values are NOT duplicated here. Vocabulary membership is checked by the JSON
  Schemas, whose enums are generated from ``ontology/vocabularies.yaml``; duplicating
  them in Python would create a third representation to drift.
* Models are permissive about OPTIONAL structure and strict about MEANING. Their job is
  to make a dishonest record impossible to construct, not to re-implement the schema.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STRICT = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)


def _is_real_int(value: Any) -> bool:
    """True for a genuine integer; ``bool`` and float are both rejected.

    ``True`` is an ``int`` in Python and ``3.0`` compares equal to ``3``; neither is an
    acceptable ordinal grade, so both are refused explicitly (contract P3).
    """
    return isinstance(value, int) and not isinstance(value, bool)


class Provenance(BaseModel):
    """Who wrote a record, when and how."""

    model_config = STRICT

    created_by: str
    created_on: str
    method: str | None = None
    run_id: str | None = None
    pipeline: str | None = None
    database_release: str | None = None
    supporting_pubmed_ids: list[str] = Field(default_factory=list)
    supporting_study_ids: list[str] = Field(default_factory=list)
    supporting_study_locus_ids: list[str] = Field(default_factory=list)
    supporting_accessions: list[str] = Field(default_factory=list)


class Retrieval(BaseModel):
    """How a source identifier reached the repository."""

    model_config = STRICT

    method: str


class SourceIdentifiers(BaseModel):
    """Registry identifiers for a source, each seen in a tool response."""

    model_config = STRICT

    pmid: str | None = None
    doi: str | None = None
    nct_id: str | None = None
    nct: str | None = None
    gcst: str | None = None
    pmcid: str | None = None
    pmc: str | None = None
    url: str | None = None
    dataset_id: str | None = None
    database_release: str | None = None

    @property
    def trial_id(self) -> str | None:
        """The trial accession under whichever accepted spelling was used."""
        return self.nct_id or self.nct

    @property
    def pmc_id(self) -> str | None:
        """The PubMed Central id under whichever accepted spelling was used."""
        return self.pmcid or self.pmc


class Source(BaseModel):
    """One registered source (contract §3)."""

    model_config = STRICT

    schema_version: str | None = None
    source_id: str
    source_type: str
    title: str
    year: int
    first_author: str
    container: str
    identifiers: SourceIdentifiers = Field(default_factory=SourceIdentifiers)
    added_by: str
    added_on: str
    retrieval: Retrieval
    notes: str | None = None

    @model_validator(mode="after")
    def _identifier_matches_the_source_id(self) -> Source:
        """The identifier implied by the source-id prefix must be present and equal.

        A ``SRC:NCT:NCT02024789`` source must carry ``identifiers.nct_id:
        "NCT02024789"``. A mismatch means the record was assembled from two different
        sources, which is the same class of error as the registry-field divergence rule
        in contract §1.3 — and it is invisible without this check, because both halves
        look well-formed on their own.
        """
        parts = self.source_id.split(":", 2)
        if len(parts) != 3 or parts[0] != "SRC":
            return self
        registry, local = parts[1], parts[2]
        expected = {
            "PMID": ("pmid", self.identifiers.pmid),
            "NCT": ("nct_id", self.identifiers.trial_id),
            "GCST": ("gcst", self.identifiers.gcst),
            "DOI": ("doi", self.identifiers.doi),
        }.get(registry)
        if expected is None:
            return self
        field_name, recorded = expected
        if recorded is None:
            raise ValueError(
                f"{self.source_id} is registered under the {registry} registry but "
                f"`identifiers.{field_name}` is empty. The identifier that DEFINES the "
                "source must be recorded, not only encoded in the id."
            )
        if registry == "DOI":
            matches = str(recorded).lower() == local.lower()
        else:
            matches = str(recorded) == local
        if not matches:
            raise ValueError(
                f"{self.source_id} encodes {local!r} but `identifiers.{field_name}` is "
                f"{recorded!r}. The record was assembled from two different sources, so "
                "the identifier is ambiguous (same class of error as the registry-field "
                "divergence rule in contract §1.3)."
            )
        return self


class EffectSize(BaseModel):
    """Effect size copied verbatim from a source — the only free-number slot."""

    model_config = STRICT

    metric: str
    as_reported: str | None = None
    value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    p_value: float | None = None

    @model_validator(mode="after")
    def _value_needs_reported_text(self) -> EffectSize:
        """A number with no ``as_reported`` text cannot have been copied (P3, V9)."""
        numeric = [self.value, self.ci_lower, self.ci_upper, self.p_value]
        if any(v is not None for v in numeric) and not self.as_reported:
            raise ValueError(
                "effect_size carries a number but as_reported is empty: a number may "
                "only appear when it was read verbatim from the source (contract P3, "
                "rule V9). Use metric: not_extracted and leave the numbers null."
            )
        if self.metric == "not_extracted" and any(v is not None for v in numeric):
            raise ValueError(
                "effect_size.metric is not_extracted but numbers are present; name the "
                "metric that was actually extracted"
            )
        return self


class SampleSize(BaseModel):
    """Sample size as reported; never estimated."""

    model_config = STRICT

    reported_as: str | None = None
    value: int | None = Field(default=None, ge=0)
    unit: str | None = None

    @property
    def value_lacks_reported_text(self) -> bool:
        """Whether a number is present without the source's own wording.

        Contract §4 permits ``reported_as: null`` alongside an integer ``value``, so
        this is NOT rejected here. :mod:`blueprint.validate` reports it as a V9 warning
        instead, because a copied number normally arrives with the text it was copied
        from and its absence is worth seeing.
        """
        return self.value is not None and not self.reported_as


class Extraction(BaseModel):
    """Provenance of the extraction itself."""

    model_config = STRICT

    basis: str
    extracted_by: str
    extracted_on: str
    content_checked: bool


class EvidenceItem(BaseModel):
    """One measurement or experiment supporting a claim (contract §4)."""

    model_config = STRICT

    evidence_id: str | None = None
    source_id: str
    design: str
    species: str | None = None
    population: str | None = None
    sample_size: SampleSize = Field(default_factory=SampleSize)
    endpoint: str | None = None
    endpoint_category: str
    endpoint_measured: str = "unknown"
    effect_direction: str
    effect_size: EffectSize
    replication_status: str
    evidence_role: str
    extraction: Extraction
    note: str | None = None
    database_record: dict[str, Any] | None = None


class ClaimContext(BaseModel):
    """Where and in what state the evidence was obtained."""

    model_config = STRICT

    species: list[str] = Field(default_factory=list)
    life_stage: str
    baseline_context: str
    brain_regions: list[str] = Field(default_factory=list)
    cell_types: list[str] = Field(default_factory=list)
    species_count: int | None = None
    phylogenetic_control: str | None = None
    phylogenetic_control_basis: str | None = None


class CausalAttribution(BaseModel):
    """What licenses (or fails to license) a causal reading."""

    model_config = STRICT

    basis: str
    locus_to_gene_resolved: str
    alternative_explanations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _catch_yaml_boolean(cls, data: Any) -> Any:
        """Explain the YAML 1.1 boolean trap instead of reporting a type error.

        ``locus_to_gene_resolved: no`` parses as ``False`` under YAML 1.1, so the value
        never reaches the enum. The generic message ("input should be a valid string")
        sends a curator looking in the wrong place, so name the real cause.
        """
        if isinstance(data, dict) and isinstance(data.get("locus_to_gene_resolved"), bool):
            literal = "yes" if data["locus_to_gene_resolved"] else "no"
            raise ValueError(
                f"locus_to_gene_resolved parsed as the boolean "
                f"{data['locus_to_gene_resolved']!r}: unquoted `{literal}` is a boolean "
                f'in YAML 1.1. Write `locus_to_gene_resolved: "{literal}"` with quotes. '
                "LOCUS IS NOT GENE is a required field (contract P4), so it may not be "
                "left ambiguous."
            )
        return data


class Translation(BaseModel):
    """The five translation-distance fields; all required (rule V8)."""

    model_config = STRICT

    adult_relevance: str
    healthy_baseline: str
    supra_normal: str
    human_relevance: str
    general_intelligence_relevance: str


class Uncertainty(BaseModel):
    """Ordinal uncertainty only (rules V9, V10)."""

    model_config = STRICT

    representation: Literal["ordinal_grade"]
    scale: str
    level: int
    rationale: str
    calibration_status: str
    model_outputs: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _model_outputs_are_attributed(self) -> Uncertainty:
        """Every carried model number names its model and its interpretation limits.

        Contract P3 permits a number that is a named model's output. An output with no
        attribution, or with no statement of what it does not mean, becomes a fake
        probability the moment somebody reads it, so both are required (rule V9).
        """
        for index, output in enumerate(self.model_outputs):
            if not str(output.get("derived_from", "")).strip():
                raise ValueError(
                    f"uncertainty.model_outputs[{index}] carries numbers with no "
                    "`derived_from`; a number may only appear as a NAMED model's output "
                    "(contract P3, rule V9)"
                )
            if len(str(output.get("interpretation_limits", "")).strip()) < 40:
                raise ValueError(
                    f"uncertainty.model_outputs[{index}] has no usable "
                    "`interpretation_limits`; state explicitly what the number is not "
                    "(not this project's probability, not calibrated, not a decision "
                    "threshold)"
                )
        return self

    @model_validator(mode="before")
    @classmethod
    def _reject_non_integer_level(cls, data: Any) -> Any:
        """Refuse a float level before coercion can hide it (contract P3)."""
        if isinstance(data, dict) and "level" in data and not _is_real_int(data["level"]):
            raise ValueError(
                f"uncertainty.level must be an integer rubric level 0-4, got "
                f"{data['level']!r}. A probability or score is forbidden in a curated "
                "record (contract P3, rules V9/V10)."
            )
        return data

    @model_validator(mode="after")
    def _level_in_range(self) -> Uncertainty:
        if not 0 <= self.level <= 4:
            raise ValueError(
                f"uncertainty.level must be 0..4 on evidence_strength_v1, got {self.level}"
            )
        return self


class Claim(BaseModel):
    """One machine-readable assertion plus its evidence (contract §4)."""

    model_config = STRICT

    schema_version: str | None = None
    claim_id: str
    statement: str
    subject: str
    predicate: str
    object: str
    claim_type: str
    direction: str | None = None
    direction_context: str | None = None
    negated_relation: str | None = None
    context: ClaimContext | None = None
    phenotype_class: str | None = None
    causal_attribution: CausalAttribution
    evidence: list[EvidenceItem] = Field(min_length=1)
    translation: Translation
    uncertainty: Uncertainty
    risks: list[str] = Field(default_factory=list)
    confounders: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    status: str
    status_reason: str | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def _state_dependent_names_its_context(self) -> Claim:
        """R10: `state_dependent` means a KNOWN dependency, so it must say which.

        `unclear` is reserved for genuine ignorance. Without this, "we know it varies
        and we know what with" is recorded identically to "we do not know", which is
        the difference between a characterised interaction and a shrug.
        """
        if self.direction == "state_dependent" and not (self.direction_context or "").strip():
            raise ValueError(
                "direction is state_dependent but direction_context is empty: name what "
                "the sign depends on (physiological state, cell subpopulation, cortical "
                "layer, compartment, task condition). Use `unclear` if the dependency is "
                "genuinely unknown."
            )
        if self.direction != "state_dependent" and self.direction_context:
            raise ValueError(
                f"direction_context is set but direction is {self.direction!r}; the field "
                "names the dependency that makes a sign state-dependent"
            )
        return self

    @model_validator(mode="after")
    def _evidence_ids_are_derived(self) -> Claim:
        """A stated ``evidence_id`` must equal the id derived from the claim."""
        local = self.claim_id.split(":", 1)[1] if ":" in self.claim_id else self.claim_id
        for index, item in enumerate(self.evidence, start=1):
            if item.evidence_id is None:
                continue
            expected = f"EVD:{local}#{index}"
            if item.evidence_id != expected:
                raise ValueError(
                    f"evidence[{index - 1}].evidence_id is {item.evidence_id!r} but is "
                    f"derived, not hand-written: it must be {expected!r} (contract §1.3)"
                )
        return self

    @property
    def status_change_lacks_reason(self) -> bool:
        """Whether a non-active status was recorded with no stated reason.

        Contract §4 does not define a ``status_reason`` field, so this is NOT rejected
        here: the authority for a status change is the superseding audit finding that
        rule V14 looks for. :mod:`blueprint.validate` reports a missing in-record reason
        as a warning, which keeps the signal without inventing a required field.
        """
        return self.status != "active" and not self.status_reason


class FacetAssessment(BaseModel):
    """One graded facet, with evidence and counter-evidence graded separately (§5.2)."""

    model_config = STRICT

    facet: str
    assessment_status: str
    level: int | None = None
    rationale: str | None = None
    # nullability is deliberate: `counter_rationale: null` is the right record when
    # counter_level is 0 or null, and forcing the key to be absent instead would make
    # "no contradicting evidence found" indistinguishable from "not considered".
    claim_refs: list[str] = Field(default_factory=list)
    counter_level: int | None = None
    counter_rationale: str | None = None
    counter_claim_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_basis: str | None = None
    search_basis: str | None = None
    reporting_gap_refs: list[str] = Field(default_factory=list)
    limiting_factor: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _reject_non_integer_levels(cls, data: Any) -> Any:
        """Refuse a float level or counter_level before coercion hides it (P3)."""
        if not isinstance(data, dict):
            return data
        for field in ("level", "counter_level"):
            value = data.get(field)
            if value is not None and not _is_real_int(value):
                raise ValueError(
                    f"{field} must be an integer 0-4 on evidence_strength_v1, got "
                    f"{value!r}. Facet grades are ordinal, never probabilities "
                    "(contract P3, §5.3)."
                )
        return data

    @model_validator(mode="after")
    def _status_consistency(self) -> FacetAssessment:
        """Enforce the §5.2 relationship between status, level and rationale."""
        for field, value in (("level", self.level), ("counter_level", self.counter_level)):
            if value is not None and not 0 <= value <= 4:
                raise ValueError(f"{field} must be 0..4, got {value}")
        if self.assessment_status in {"not_assessed", "not_applicable"}:
            if self.level is not None or self.counter_level is not None:
                raise ValueError(
                    f"facet {self.facet!r} is {self.assessment_status} but carries a "
                    "level. An unexamined facet is level: null — writing 0 says "
                    "'searched and found nothing', which is a different fact (§5.2)."
                )
        elif self.assessment_status == "assessed":
            if self.level is None:
                raise ValueError(
                    f"facet {self.facet!r} is assessed but level is null; use "
                    "assessment_status: not_assessed if it was not examined"
                )
            if not self.rationale:
                raise ValueError(
                    f"facet {self.facet!r} is assessed with no rationale; every grade "
                    "needs a stated reason (§5.2)"
                )
        if self.level == 0:
            # Level 0 means SEARCHED AND FOUND NOTHING, so there is nothing to cite.
            # Demanding a citation for the absence of evidence pushes an agent into
            # inventing a tangential one, or into downgrading a truthful 0 to
            # `not_assessed` — a different epistemic state the contract keeps distinct.
            # The zero stays accountable through `search_basis` instead.
            if not (self.search_basis or "").strip():
                raise ValueError(
                    f"facet {self.facet!r} is graded 0 with no `search_basis`. Level 0 "
                    "means SEARCHED AND FOUND NOTHING, so no citation is asked for — but "
                    "the zero must still be accountable: name what was searched, at what "
                    "scope, and what would have counted as a hit (contract §5.2)."
                )
        elif self.level is not None and self.level >= 1:
            if not (self.claim_refs or self.source_refs):
                raise ValueError(
                    f"facet {self.facet!r} is graded {self.level} but cites neither "
                    "claim_refs nor source_refs. A level of 1 or more asserts that "
                    "supporting evidence exists, so it must say which."
                )
        if self.reporting_gap_refs and not (self.search_basis or "").strip():
            # R14: the refs EXPLAIN a zero, they do not replace the explanation. A
            # reporting gap is a finding about the evidence base, not about the target,
            # so it may appear at any level and may never raise counter_level.
            raise ValueError(
                f"facet {self.facet!r} lists reporting_gap_refs but has no "
                "`search_basis`. Registered interventions that completed without posted "
                "results explain a grade; they do not replace the account of what was "
                "searched (contract §5.2, R14)."
            )
        if self.counter_level is not None and self.counter_level >= 1 and not self.counter_claim_refs:
            raise ValueError(
                f"facet {self.facet!r} has counter_level {self.counter_level} but cites no "
                "counter_claim_refs; contradicting evidence must be identified, not just "
                "described"
            )
        if self.source_refs and not self.evidence_basis:
            raise ValueError(
                f"facet {self.facet!r} cites source_refs but declares no evidence_basis; "
                "database-derived grading must say so (contract §5.2, R7)"
            )
        if self.counter_level is not None and self.counter_level > 0 and not self.counter_rationale:
            raise ValueError(
                f"facet {self.facet!r} has counter_level {self.counter_level} with no "
                "counter_rationale; contradicting evidence must be described"
            )
        return self


class Assessment(BaseModel):
    """Facet assessments for one target (contract §5.2)."""

    model_config = STRICT

    schema_version: str | None = None
    target_id: str
    assessed_by: str
    assessed_on: str
    rubric: str
    scale: str | None = None
    run_id: str | None = None
    facets: list[FacetAssessment] = Field(min_length=1)
    facets_not_owned_by_this_agent: list[str] = Field(default_factory=list)
    notes: str | None = None
    provenance: Provenance | None = None

    @model_validator(mode="after")
    def _no_duplicate_facets(self) -> Assessment:
        """One grade per facet per record: a duplicate hides one of them."""
        seen: set[str] = set()
        for facet in self.facets:
            if facet.facet in seen:
                raise ValueError(
                    f"facet {facet.facet!r} is graded twice in one assessment for "
                    f"{self.target_id}; a facet has exactly one grade per record"
                )
            seen.add(facet.facet)
        return self


class TargetStateVariableLink(BaseModel):
    """A state-variable link asserted by a control-point hypothesis."""

    model_config = STRICT

    id: str
    asserted_relation: str
    direction: str
    response_shape: str
    claim_refs: list[str] = Field(default_factory=list)


class ControlPointHypothesis(BaseModel):
    """A hypothesis about how a target could act as a control point."""

    model_config = STRICT

    statement: str
    proposed_modulation: str
    mechanism_chain: list[str] = Field(default_factory=list)
    state_variables: list[TargetStateVariableLink] = Field(default_factory=list)
    computational_primitives: list[str] = Field(default_factory=list)


class TargetIdentifiers(BaseModel):
    """Machine-filled identifiers; empty when an agent authors the dossier."""

    model_config = STRICT

    hgnc_id: str | None = None
    ensembl_gene_id: str | None = None
    uniprot_ids: list[str] = Field(default_factory=list)
    entrez_id: str | None = None
    identifier_provenance: str | None = None


class Target(BaseModel):
    """One target dossier (contract §5.1)."""

    model_config = STRICT

    schema_version: str | None = None
    target_id: str
    symbol: str
    lead_atlas: str
    seed_origin: str
    dossier_depth: str
    identifiers: TargetIdentifiers = Field(default_factory=TargetIdentifiers)
    target_class: str | None = None
    represented_entities: list[str] = Field(default_factory=list)
    member_genes: list[str] = Field(default_factory=list)
    control_point_hypothesis: ControlPointHypothesis | None = None
    known_liabilities: list[str] = Field(default_factory=list)
    developmental_confound: str | None = None
    developmental_confound_rationale: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    brake_class: str | None = None
    power_node: str | None = None
    modulator_class: str | None = None
    primary_state_domains: list[str] = Field(default_factory=list)
    status: str
    provenance: Provenance

    @model_validator(mode="after")
    def _confound_grade_needs_rationale(self) -> Target:
        """A stated developmental-confound grade needs its rationale (§5.1)."""
        if (
            self.developmental_confound in {"high", "moderate", "low"}
            and not self.developmental_confound_rationale
        ):
            raise ValueError(
                f"developmental_confound is {self.developmental_confound!r} with no "
                "rationale; the development-versus-adulthood distinction is a required "
                "field, not a caveat (contract P4)"
            )
        return self


class AuditCheck(BaseModel):
    """One entry from the mandatory check catalogue."""

    model_config = STRICT

    check: str
    result: str
    note: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class AuditFinding(BaseModel):
    """One audit finding."""

    model_config = STRICT

    finding_id: str
    severity: str
    category: str
    description: str
    evidence_refs: list[str] = Field(default_factory=list)


class AuditAdjustment(BaseModel):
    """A downgrade-only adjustment to a facet, claim status or dossier status (V12)."""

    model_config = STRICT

    kind: str
    target_id: str | None = None
    claim_id: str | None = None
    facet: str | None = None
    field: str = "level"
    from_level: int | None = None
    to_level: int | None = None
    reason: str

    @model_validator(mode="after")
    def _downgrade_only(self) -> AuditAdjustment:
        """The red team may downgrade, never upgrade (contract P6, rule V12)."""
        if self.kind != "facet":
            return self
        if self.facet is None:
            raise ValueError("a facet adjustment must name the facet it adjusts")
        if self.from_level is None or self.to_level is None:
            raise ValueError(
                f"facet adjustment on {self.facet!r} needs both from_level and to_level"
            )
        if self.field == "level" and self.to_level >= self.from_level:
            raise ValueError(
                f"audit adjustment on facet {self.facet!r} moves level "
                f"{self.from_level} -> {self.to_level}, which is not a downgrade. The "
                "red team may downgrade, never upgrade (contract P6, rule V12). To "
                "record contradicting evidence, raise counter_level instead "
                "(field: counter_level)."
            )
        if self.field == "counter_level" and self.to_level <= self.from_level:
            raise ValueError(
                f"audit adjustment on facet {self.facet!r} moves counter_level "
                f"{self.from_level} -> {self.to_level}. Lowering the "
                "contradicting-evidence grade would be an upgrade of the target's "
                "standing, which the red team may not do (contract P6, rule V12)."
            )
        return self


class ClaimStatusChange(BaseModel):
    """A recorded change of a claim's status.

    ``from`` is a Python keyword, so the field is ``from_`` with an alias; the alias is
    what appears in YAML and ``populate_by_name`` lets Python callers use either.
    """

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, str_strip_whitespace=True
    )

    claim_id: str
    from_: str = Field(alias="from")
    to: str
    reason: str


class AuditScope(BaseModel):
    """What an audit is about."""

    model_config = STRICT

    kind: str
    id: str


class Audit(BaseModel):
    """One red-team audit record (contract §6)."""

    model_config = STRICT

    schema_version: str | None = None
    audit_id: str
    scope: AuditScope
    audited_by: str
    audited_on: str
    checks: list[AuditCheck] = Field(min_length=1)
    findings: list[AuditFinding] = Field(default_factory=list)
    adjustments: list[AuditAdjustment] = Field(default_factory=list)
    claim_status_changes: list[ClaimStatusChange] = Field(default_factory=list)
    verdict: str
    provenance: Provenance

    @model_validator(mode="after")
    def _findings_belong_to_this_audit(self) -> Audit:
        """Finding ids are derived from the audit id (``{audit_id}#f{n}``)."""
        for finding in self.findings:
            if not finding.finding_id.startswith(f"{self.audit_id}#f"):
                raise ValueError(
                    f"finding id {finding.finding_id!r} does not derive from audit "
                    f"{self.audit_id!r}; it must be {self.audit_id}#f<n>"
                )
        return self

    @model_validator(mode="after")
    def _status_changes_are_not_deletions(self) -> Audit:
        """A status change must actually change the status, and never erase it."""
        for change in self.claim_status_changes:
            if change.from_ == change.to:
                raise ValueError(
                    f"claim_status_change for {change.claim_id} records "
                    f"{change.from_!r} -> {change.to!r}, which is not a change"
                )
        return self


class MeasurementProxy(BaseModel):
    """One way a state variable can be measured, with its honest grade."""

    model_config = STRICT

    name: str
    modality: str
    status: str


class ResponseShape(BaseModel):
    """The shape of a state variable's relation to cognitive output."""

    model_config = STRICT

    shape: str
    basis: str
    claim_refs: list[str] = Field(default_factory=list)
    rationale: str | None = None

    @model_validator(mode="after")
    def _shape_requires_its_basis(self) -> ResponseShape:
        """No invented dose-response curves (README §3)."""
        if self.basis == "default_no_evidence_yet":
            if self.shape != "unknown":
                raise ValueError(
                    f"response_shape.shape is {self.shape!r} with basis "
                    "default_no_evidence_yet. A shape other than `unknown` is an "
                    "empirical claim and needs basis `claim_supported` with claim_refs, "
                    "or `definitional` (README §3)."
                )
            if self.claim_refs:
                raise ValueError(
                    "response_shape carries claim_refs but its basis is "
                    "default_no_evidence_yet; name the basis the claims support"
                )
        if self.basis == "claim_supported" and not self.claim_refs:
            raise ValueError(
                "response_shape.basis is claim_supported but claim_refs is empty; a "
                "claim-supported shape must name its claims (contract P2)"
            )
        return self


class StateVariableProvenance(BaseModel):
    """Who defined a state variable and on what basis."""

    model_config = STRICT

    defined_by: str
    basis: str


class StateVariable(BaseModel):
    """One state-variable definition from ``state_model/{domain}.yaml``."""

    model_config = STRICT

    id: str
    name: str
    definition: str
    aliases: list[str] = Field(default_factory=list)
    kind: str
    timescale: str
    level: str
    units: str | None = None
    measurement_proxies: list[MeasurementProxy] = Field(default_factory=list)
    response_shape: ResponseShape
    desirability: str
    polarity: str | None = None
    polarity_note: str | None = None
    safety_coupling: list[str] = Field(default_factory=list)
    safety_coupling_basis: str
    related_primitives: list[str] = Field(default_factory=list)
    status: str
    notes: str | None = None
    provenance: StateVariableProvenance

    @property
    def domain(self) -> str:
        """The state domain segment of the identifier."""
        return self.id.split(":", 1)[1].split(".", 1)[0]

    @model_validator(mode="after")
    def _coupling_basis_consistency(self) -> StateVariable:
        """An unasserted coupling list must be empty (no invented relationships)."""
        if self.safety_coupling_basis == "not_asserted_pending_claims" and self.safety_coupling:
            raise ValueError(
                f"{self.id} lists safety couplings with basis "
                "not_asserted_pending_claims. Which variables push which safety "
                "constraints is empirical: assert it through a state-variable "
                "annotation with claim refs, not in the definition."
            )
        return self

    @model_validator(mode="after")
    def _polarity_matches_the_naming_convention(self) -> StateVariable:
        """R4: the risk/margin convention is enforced, not merely documented.

        `direction: increases` means opposite things against a threshold and against a
        risk. The brake atlas had to invert six coupling directions by hand after
        re-pointing a seizure THRESHOLD to a seizure RISK, and that error is silent — so
        the convention is checked rather than trusted.
        """
        if self.domain not in {"safety", "stability"}:
            if self.polarity is not None:
                raise ValueError(
                    f"{self.id} declares polarity {self.polarity!r}, but only safety and "
                    "stability variables have a risk/margin reading"
                )
            return self
        if self.polarity is None:
            raise ValueError(
                f"{self.id} is a {self.domain} variable and must declare "
                "polarity: risk | margin (R4)"
            )
        name = self.id.rsplit(".", 1)[-1]
        if name.endswith("_margin") and self.polarity != "margin":
            raise ValueError(
                f"{self.id} is named `..._margin` but declares polarity "
                f"{self.polarity!r}; a margin is headroom, so a higher value is less harm"
            )
        if name.endswith(("_risk", "_burden")) and self.polarity != "risk":
            raise ValueError(
                f"{self.id} is named `..._{name.rsplit('_', 1)[-1]}` but declares "
                f"polarity {self.polarity!r}; a risk is harm, so a higher value is worse"
            )
        return self

    @model_validator(mode="after")
    def _safety_variables_are_constraints(self) -> StateVariable:
        """Safety variables are constraints, not quantities to optimise (README §3)."""
        if self.domain == "safety":
            if self.kind != "constraint":
                raise ValueError(
                    f"{self.id} is in the safety domain but kind is {self.kind!r}; "
                    "safety variables are constraints (README §3)"
                )
            if self.polarity == "margin":
                # A MARGIN in the safety domain is headroom, and more headroom is
                # better within a range nobody has established (R3). It is still a
                # constraint: it bounds the admissible region, it is not an objective.
                allowed = {"higher_is_better_within_range", "constraint_to_respect"}
            else:
                allowed = {"constraint_to_respect"}
            if self.desirability not in allowed:
                raise ValueError(
                    f"{self.id} is a safety variable with polarity {self.polarity!r} but "
                    f"desirability is {self.desirability!r}; allowed: {sorted(allowed)}. A "
                    "risk must be constraint_to_respect so that no aggregation can trade "
                    "it against a benefit."
                )
        return self


class SafetyCouplingEntry(BaseModel):
    """One claim-backed coupling from a state variable to a safety constraint."""

    model_config = STRICT

    couples_to: str
    direction: str | None = None
    note: str | None = None
    claim_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coupling_needs_claims(self) -> SafetyCouplingEntry:
        """A coupling is empirical; asserting one with no claim is invention."""
        if not self.claim_refs:
            raise ValueError(
                f"safety coupling to {self.couples_to} cites no claim. Which variables "
                "push which safety constraints is an empirical question (contract P2)."
            )
        return self


class SafetyCouplingGroup(BaseModel):
    """Several couplings sharing one basis and one claim set."""

    model_config = STRICT

    # `couplings: []` with basis `not_asserted_pending_claims` is the honest record for
    # "looked, nothing to assert yet", so an empty list is accepted rather than forcing
    # the agent to omit the field or invent a coupling.
    couplings: list[SafetyCouplingEntry] = Field(default_factory=list)
    basis: str | None = None
    rationale: str | None = None
    claim_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _empty_group_declares_why(self) -> SafetyCouplingGroup:
        """An empty coupling list must say it is pending, not merely be empty."""
        if not self.couplings and self.basis != "not_asserted_pending_claims":
            raise ValueError(
                "a safety-coupling group with no couplings must declare "
                "`basis: not_asserted_pending_claims`, which records 'looked, nothing to "
                "assert yet'. An empty group with any other basis says nothing at all."
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def _push_group_claims_down(cls, data: Any) -> Any:
        """Normalise bare ids to entries and let group-level claims stand in.

        The grouped form states one basis and one claim set covering several
        couplings, which is a legitimate and less repetitive record. Each coupling
        still has to be claim-backed, so the group's claims are copied down before
        :class:`SafetyCouplingEntry` enforces that.
        """
        if not isinstance(data, dict):
            return data
        shared = data.get("claim_refs") or []
        couplings = data.get("couplings")
        if not isinstance(couplings, list):
            return data
        data = dict(data)
        normalised: list[Any] = []
        for entry in couplings:
            # A bare state-variable id is the concise form: the group's basis, claims
            # and rationale already cover it, so repeating them per entry would be
            # noise. Expand it here so one model validates both spellings.
            if isinstance(entry, str):
                entry = {"couples_to": entry}
            if isinstance(entry, dict):
                entry = {**entry, "claim_refs": entry.get("claim_refs") or list(shared)}
            normalised.append(entry)
        data["couplings"] = normalised
        return data


class StateVariableAnnotation(BaseModel):
    """A domain agent's claim-backed annotation on a state variable.

    The only route by which empirical content reaches a state variable. Accepts both
    field spellings that the atlases used for the annotated variable, and both the
    single-entry and list forms of ``safety_coupling``.
    """

    model_config = STRICT

    schema_version: str | None = None
    state_variable: str | None = None
    state_variable_id: str | None = None
    domain: str | None = None
    relation: str | None = None
    annotated_by: str | None = None
    annotated_on: str | None = None
    run_id: str | None = None
    claim_refs: list[str] = Field(default_factory=list)
    rationale: str | None = None
    proposed_response_shape: str | None = None
    shape_rationale: str | None = None
    response_shape: ResponseShape | None = None
    desirability_note: str | None = None
    measurability_note: str | None = None
    safety_coupling: (
        SafetyCouplingGroup | SafetyCouplingEntry | list[SafetyCouplingEntry] | None
    ) = None
    couples_to_targets: list[str] = Field(default_factory=list)
    measurement_proxy: MeasurementProxy | None = None
    linked_nodes: list[str] = Field(default_factory=list)
    note: str | None = None

    @property
    def variable_id(self) -> str | None:
        """The annotated variable, under whichever field name was used."""
        return self.state_variable or self.state_variable_id

    @property
    def safety_couplings(self) -> list[SafetyCouplingEntry]:
        """``safety_coupling`` normalised to a list."""
        if self.safety_coupling is None:
            return []
        if isinstance(self.safety_coupling, list):
            return list(self.safety_coupling)
        if isinstance(self.safety_coupling, SafetyCouplingGroup):
            return list(self.safety_coupling.couplings)
        return [self.safety_coupling]

    @model_validator(mode="after")
    def _variable_is_named(self) -> StateVariableAnnotation:
        """The annotated variable must be identified."""
        if not self.variable_id:
            raise ValueError(
                "annotation names no state variable; use `state_variable` with an "
                "SV:{domain}.{name} id"
            )
        return self

    @model_validator(mode="after")
    def _domain_matches_id(self) -> StateVariableAnnotation:
        """A stated domain must agree with the identifier's domain segment."""
        variable = self.variable_id or ""
        if self.domain and variable.startswith("SV:"):
            id_domain = variable.split(":", 1)[1].split(".", 1)[0]
            if id_domain != self.domain:
                raise ValueError(
                    f"annotation says domain {self.domain!r} but {variable} is in "
                    f"{id_domain!r}; the domain is part of the identifier"
                )
        return self

    @model_validator(mode="after")
    def _shape_proposal_needs_claims(self) -> StateVariableAnnotation:
        """No invented dose-response curves, at the annotation layer (README §3)."""
        if self.proposed_response_shape and self.proposed_response_shape != "unknown":
            if not self.claim_refs:
                raise ValueError(
                    f"annotation proposes response shape "
                    f"{self.proposed_response_shape!r} for {self.variable_id} but cites "
                    "no claim. A shape other than `unknown` is an empirical assertion "
                    "(contract P2, README §3)."
                )
            if not self.shape_rationale:
                raise ValueError(
                    f"annotation proposes response shape "
                    f"{self.proposed_response_shape!r} with no shape_rationale; state "
                    "why the cited evidence implies that shape rather than another"
                )
        return self

    @property
    def all_claim_refs(self) -> list[str]:
        """Every claim this annotation cites, at the record or the assertion level.

        Claims may be attached PER ASSERTION (inside ``response_shape`` and
        ``safety_coupling``) rather than in one flat list, which is more precise: it
        says which claims support which assertion. Both spellings are accepted.
        """
        refs = list(self.claim_refs)
        if self.response_shape is not None:
            refs.extend(self.response_shape.claim_refs)
        for coupling in self.safety_couplings:
            refs.extend(coupling.claim_refs)
        if isinstance(self.safety_coupling, SafetyCouplingGroup):
            refs.extend(self.safety_coupling.claim_refs)
        return sorted(set(refs))

    @property
    def asserts_anything(self) -> bool:
        """Whether this annotation actually asserts something about the world.

        The presence of a ``response_shape`` or ``safety_coupling`` block is NOT an
        assertion: ``shape: unknown`` with the default basis, and an empty coupling list
        with ``basis: not_asserted_pending_claims``, are the honest records for "looked,
        nothing to assert yet". Demanding a citation for those would be demanding a
        citation for the absence of evidence, which pushes an agent into inventing a
        tangential one — the same failure mode as asking a level-0 facet for a claim.
        """
        shape = self.response_shape
        shape_asserts = shape is not None and (
            shape.shape != "unknown" or shape.basis != "default_no_evidence_yet"
        )
        proposed_asserts = bool(
            self.proposed_response_shape and self.proposed_response_shape != "unknown"
        )
        coupling_asserts = bool(self.safety_couplings)
        # `desirability_note` is deliberately NOT an assertion. In practice it is used
        # to say why nothing is being asserted ("cheap is not the same as better, and no
        # claim links sparseness to performance"), and requiring a citation for it would
        # be requiring a citation for the absence of evidence — the same failure mode as
        # asking a level-0 facet for a claim. A note that DOES assert something is
        # caught by the positive fields below.
        return any(
            (
                proposed_asserts,
                shape_asserts,
                coupling_asserts,
                self.measurement_proxy is not None,
                bool(self.linked_nodes),
            )
        )

    @model_validator(mode="after")
    def _assertions_need_claims(self) -> StateVariableAnnotation:
        """Everything except a bare note asserts something and needs a claim (P2)."""
        if self.asserts_anything and not self.all_claim_refs:
            raise ValueError(
                f"annotation on {self.variable_id} asserts something about the world "
                "and must cite at least one claim, either in `claim_refs` or inside the "
                "assertion it supports (contract P2: provenance or silence)"
            )
        return self


class ApprovalStatus(BaseModel):
    """Approval somewhere for some indication, with its source."""

    model_config = STRICT

    status: str
    source_id: str


class MechanismOfAction(BaseModel):
    """One mechanism of action, copied from a drug database with its provenance.

    Kept structured rather than flattened to a string: ``target_chembl_id`` and
    ``mechanism_ref_pmid`` are what make the annotation checkable, and a string would
    discard them.
    """

    model_config = STRICT

    mechanism_of_action: str
    action_type: str | None = None
    target_chembl_id: str | None = None
    direct_interaction: bool | None = None
    disease_efficacy: bool | None = None
    mechanism_ref_pmid: str | None = None
    source_id: str | None = None
    mechanism_id: str | None = None
    note: str | None = None


class InterventionIdentifiers(BaseModel):
    """Identifiers for an intervention entity."""

    model_config = STRICT

    chembl_id: str | None = None
    inn: str | None = None
    identifier_provenance: str | None = None


class Intervention(BaseModel):
    """One intervention entity in the intervention layer."""

    model_config = STRICT

    schema_version: str | None = None
    id: str | None = None
    intervention_id: str | None = None
    node_type: str | None = None
    label: str | None = None
    preferred_name: str | None = None
    name: str | None = None
    domain: str | None = None
    added_by: str | None = None
    added_on: str | None = None
    claim_refs: list[str] = Field(default_factory=list)
    efficacy_status: str | None = None
    chembl_max_phase: int | float | str | None = None
    chembl_first_approval: int | str | None = None
    first_approval_year: int | None = None
    database_source_id: str | None = None
    exemplar_interventions: list[str] = Field(default_factory=list)
    description: str | None = None
    modality: str | None = None
    acts_on_target: str | None = None
    chembl_id: str | None = None
    identifier_provenance: str | None = None
    blood_brain_barrier: str | None = None
    max_clinical_phase: dict[str, Any] = Field(default_factory=dict)
    approval: dict[str, Any] = Field(default_factory=dict)
    synonyms_as_reported: list[str] = Field(default_factory=list)
    related_probes_named_in_retrieved_text: list[str] = Field(default_factory=list)
    supports_effect_claims: list[str] = Field(default_factory=list)
    dose_response_note: str | None = None
    recorded_by: str | None = None
    recorded_on: str | None = None
    identifiers: InterventionIdentifiers = Field(default_factory=InterventionIdentifiers)
    active_moiety: str | None = None
    mechanism: str | None = None
    mechanism_class: str | None = None
    mechanism_as_reported: str | None = None
    mechanisms: list[MechanismOfAction] = Field(default_factory=list)
    acts_through: list[str] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    state_variables_touched: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus | None = None
    approved_indication_note: str | None = None
    known_liabilities: list[str] = Field(default_factory=list)
    cited_by_claims: list[str] = Field(default_factory=list)
    human_evidence_summary: str | None = None
    role_in_atlas: str | None = None
    scope_limits: str | None = None
    direction_warning: str | None = None
    conflict_of_interest_note: str | None = None
    vector_serotype: str | None = None
    chembl_fields_as_returned: dict[str, Any] = Field(default_factory=dict)
    dose_information: Literal["omitted_by_policy"] | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    notes: str | list[str] | None = None
    provenance: Provenance | None = None

    @property
    def database_facts_are_attributed(self) -> bool:
        """Whether the database-derived numbers name the release they came from.

        Rule V9 exempts ``max_clinical_phase.value`` and ``first_approval_year`` only
        when this is true: a database fact is admissible because its provenance is
        visible, never because it is a number somebody trusts.
        """
        return bool(
            self.database_source_id
            or (self.provenance and self.provenance.database_release)
            or (self.max_clinical_phase or {}).get("source")
        )

    @property
    def entity_id(self) -> str | None:
        """The node id, under whichever field the authoring atlas used."""
        return self.id or self.intervention_id

    @property
    def display_name(self) -> str | None:
        """The entity's name, under whichever field the authoring atlas used."""
        return self.label or self.preferred_name or self.name

    @model_validator(mode="after")
    def _mechanism_needs_class(self) -> Intervention:
        """A Mechanism record must name the class of molecular action it denotes."""
        if self.node_type == "Mechanism" and not self.mechanism_class:
            raise ValueError(
                f"{self.entity_id} is a Mechanism but names no mechanism_class"
            )
        return self

    @model_validator(mode="after")
    def _must_be_named(self) -> Intervention:
        """An entity must be named, under either accepted field name.

        Two atlases independently chose ``label`` and ``preferred_name`` for the same
        thing. Both are accepted in v0.1.0 rather than invalidating 24 existing
        records; docs/ONTOLOGY_NOTES.md records that v0.2.0 must settle on ``label``.
        """
        if not self.entity_id:
            raise ValueError(
                "intervention record has no `id` (nor the accepted alias "
                "`intervention_id`); it cannot be referenced or compiled"
            )
        if not self.display_name:
            raise ValueError(
                f"{self.entity_id} has no `label` (nor the accepted aliases "
                "`preferred_name` / `name`); an intervention entity must be named"
            )
        if not (self.provenance or self.added_by or self.recorded_by):
            raise ValueError(
                f"{self.entity_id} records no authorship; use `provenance`, or "
                "`added_by`/`added_on`, or `recorded_by`/`recorded_on`"
            )
        return self


class VerificationRecord(BaseModel):
    """One line of the source-verification index (contract §7)."""

    model_config = STRICT

    source_id: str
    status: str
    registry: str | None = None
    registry_title: str | None = None
    registry_year: int | None = None
    registry_container: str | None = None
    registry_doi: str | None = None
    title_similarity: float | None = None
    publication_types: list[str] = Field(default_factory=list)
    retraction_flag: bool | None = None
    snapshot: str | None = None
    checked_at: str | None = None
    note: str | None = None

    @property
    def is_verified(self) -> bool:
        """Whether this record passes rule V6."""
        return self.status == "verified"


class GraphEdge(BaseModel):
    """One compiled graph edge, or one entry of ``definitional_edges.yaml``."""

    model_config = STRICT

    subject: str
    predicate: str
    object: str
    provenance_class: str
    claim_refs: list[str] = Field(default_factory=list)
    basis: str | None = None
    reference_source: str | None = None
    direction: str | None = None
    defined_by: str | None = None
    layer: str | None = None

    @model_validator(mode="after")
    def _provenance_consistency(self) -> GraphEdge:
        """Rule V17, expressed on the object rather than only in the schema."""
        if self.provenance_class == "claim_derived" and not self.claim_refs:
            raise ValueError(
                f"edge {self.subject} -{self.predicate}-> {self.object} is "
                "claim_derived but cites no claim (rule V17)"
            )
        if self.provenance_class == "ontology_axiom":
            if not self.basis:
                raise ValueError(
                    f"edge {self.subject} -{self.predicate}-> {self.object} is an "
                    "ontology_axiom but states no basis; an axiom must be attackable"
                )
            if self.claim_refs:
                raise ValueError(
                    f"edge {self.subject} -{self.predicate}-> {self.object} is an "
                    "ontology_axiom but cites claims; if it needs evidence it is not "
                    "an axiom"
                )
        if self.provenance_class == "reference_data" and not self.reference_source:
            raise ValueError(
                f"edge {self.subject} -{self.predicate}-> {self.object} is "
                "reference_data but names no pinned release; reproducibility requires "
                "the release (contract P7)"
            )
        return self


# Record kind -> model, used by the loaders and by tests that parametrise over kinds.
MODEL_FOR_KIND: dict[str, type[BaseModel]] = {
    "source": Source,
    "claim": Claim,
    "evidence": EvidenceItem,
    "target": Target,
    "assessment": Assessment,
    "audit": Audit,
    "intervention": Intervention,
    "state_variable": StateVariable,
    "state_variable_annotation": StateVariableAnnotation,
    "verification": VerificationRecord,
    "edge": GraphEdge,
}
