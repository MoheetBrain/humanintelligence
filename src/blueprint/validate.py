"""The rule engine: contract rules V1-V21 as small, registered functions.

Design rules
------------
* **One function per rule, in a registry.** A rule is
  ``(ValidationContext) -> list[Violation]``. Phase 2 and later agents add rules by
  writing a function and decorating it with :func:`rule`; nothing else changes. The
  registry is ordered by rule id so reports are stable.
* **Rules never raise.** A rule that cannot evaluate reports a violation saying so. One
  broken rule must not take down the report that an agent needs to fix its records.
* **Rules never mutate.** The context is read-only; ``--update-lock`` is the CLI's job,
  not a rule's.
* **Severity is a judgement about the repository, not about the rule.** ``error`` means
  the record is wrong. ``warning`` means the condition may legitimately hold while the
  repository is incomplete (no verification index yet, no audits yet) and ``--strict``
  escalates it. Nothing that would corrupt provenance is ever a warning.
* **Every message names the contract clause and says what to do.** The audience is an
  agent that has to fix a record without reading this file.

Implementation status is recorded honestly in docs/ONTOLOGY_NOTES.md: some rules are
PARTIAL in Phase 1 because their subject matter (the compiled graph, the ranking model,
the audit corpus) arrives in Phase 2 or from another agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from blueprint import ids, loaders, ontology, paths, policy, schemas, verification, vocab
from blueprint.violations import Violation, error, info, warning

# Prefixes for which snapshot verification is the correct and sufficient check.
SNAPSHOT_PREFIX_HINT = " or ".join(
    prefix.rstrip(":") for prefix in verification.SNAPSHOT_VERIFIABLE_PREFIXES
)

Rule = Callable[["ValidationContext"], list[Violation]]

# rule id -> (function, one-line description)
REGISTRY: dict[str, tuple[Rule, str]] = {}


def rule(rule_id: str, description: str) -> Callable[[Rule], Rule]:
    """Register a rule function under a contract rule id."""

    def decorate(function: Rule) -> Rule:
        if rule_id in REGISTRY:
            raise ValueError(f"rule {rule_id} is already registered")
        REGISTRY[rule_id] = (function, description)
        return function

    return decorate


@dataclass
class ValidationContext:
    """Everything a rule may read: the records, the ontology and the indexes."""

    root: Path
    repo: loaders.Repository
    onto: ontology.Ontology
    verification: verification.VerificationIndex
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def claims(self) -> dict[str, loaders.LoadedRecord]:
        return self.repo.claims

    @property
    def sources(self) -> dict[str, loaders.LoadedRecord]:
        return self.repo.sources

    def node_type_of(self, node_id: str) -> str | None:
        """The single node type of ``node_id``, or ``None`` when ambiguous/unknown.

        A ``PROT:`` id legally denotes Protein and four specialisations, so this returns
        the most general matching type, which is what triple legality needs.
        """
        candidates = ids.node_types_for(node_id, self.root) if ids.is_valid(node_id, self.root) else []
        if not candidates:
            return None
        general = [name for name in candidates if self.onto.nodes[name].parent is None]
        return sorted(general)[0] if general else sorted(candidates)[0]

    def claim_of(self, claim_id: str) -> dict[str, Any] | None:
        """The raw claim mapping for ``claim_id``, or ``None``."""
        record = self.repo.claims.get(claim_id)
        return record.raw if record else None


def build_context(root: Path | str | None = None) -> ValidationContext:
    """Load everything a validation run needs."""
    resolved = paths.resolve_root(root)
    return ValidationContext(
        root=resolved,
        repo=loaders.load_repository(resolved),
        onto=ontology.load(resolved),
        verification=verification.load(resolved),
    )


# =============================================================== V1: schemas ===

@rule("V1", "Every record validates against its JSON Schema.")
def check_schemas(ctx: ValidationContext) -> list[Violation]:
    """Validate every loaded record against its schema.

    Loading violations are NOT emitted here. They carry their own rule ids (a duplicate
    source id is V4, a domain mismatch is V2) and :func:`run` contributes them directly,
    so ``--rule V4`` shows a V4 loading violation instead of silently hiding it behind
    whether V1 happened to be selected.
    """
    out: list[Violation] = []
    groups: list[tuple[str, list[loaders.LoadedRecord]]] = [
        ("source", list(ctx.repo.sources.values())),
        ("claim", list(ctx.repo.claims.values())),
        ("target", list(ctx.repo.targets.values())),
        ("assessment", ctx.repo.assessments),
        ("audit", list(ctx.repo.audits.values())),
        ("intervention", list(ctx.repo.interventions.values())),
        ("state_variable", list(ctx.repo.state_variables.values())),
        ("state_variable_annotation", ctx.repo.state_variable_annotations),
        ("edge", ctx.repo.definitional_edges),
    ]
    for kind, items in groups:
        for item in items:
            out.extend(
                schemas.validate_record(
                    item.raw,
                    kind,
                    source_path=item.path,
                    record_id=item.record_id,
                    root=ctx.root,
                )
            )
    for source_id, record in ctx.verification.records.items():
        out.extend(
            schemas.validate_record(
                record,
                "verification",
                source_path="data/interim/source_verification.jsonl",
                record_id=source_id,
                root=ctx.root,
            )
        )
    return out


# ============================================================== V2: node ids ===

_ID_FIELDS: tuple[tuple[str, str], ...] = (
    ("subject", "claim subject"),
    ("object", "claim object"),
)


@rule("V2", "Every node id matches its prefix pattern and the prefix is legal for the node type.")
def check_node_ids(ctx: ValidationContext) -> list[Violation]:
    """Check identifier well-formedness wherever a record names a node."""
    out: list[Violation] = []

    def check(node_id: Any, locator: str, record_id: str | None, what: str) -> None:
        if not isinstance(node_id, str) or not node_id:
            return
        try:
            ids.parse(node_id, ctx.root)
        except ids.IdError as exc:
            out.append(error("V2", locator, f"{what}: {exc}", record_id=record_id))
            return
        if not ids.node_types_for(node_id, ctx.root):
            prefix = ids.prefix_of(node_id, ctx.root)
            legal = sorted(ctx.onto.node_types_for_prefix(prefix))
            patterns = sorted({ctx.onto.nodes[n].id_pattern for n in legal})
            out.append(
                error(
                    "V2",
                    locator,
                    f"{what} {node_id!r} carries a declared prefix {prefix!r} but matches "
                    f"no node type's id_pattern. Node types for that prefix: {legal}; "
                    f"expected form(s): {patterns} (contract §1).",
                    record_id=record_id,
                )
            )

    for claim_id, record in ctx.claims.items():
        for field_name, what in _ID_FIELDS:
            check(record.raw.get(field_name), f"{record.path}#/{field_name}", claim_id, what)
        context = record.raw.get("context") or {}
        if isinstance(context, dict):
            for key in ("species", "brain_regions", "cell_types"):
                for index, value in enumerate(context.get(key) or []):
                    check(value, f"{record.path}#/context/{key}/{index}", claim_id, f"context.{key}")
    for target_id, record in ctx.repo.targets.items():
        check(target_id, f"{record.path}#/target_id", target_id, "target id")
        for index, value in enumerate(record.raw.get("represented_entities") or []):
            check(value, f"{record.path}#/represented_entities/{index}", target_id, "represented entity")
        for index, value in enumerate(record.raw.get("known_liabilities") or []):
            check(value, f"{record.path}#/known_liabilities/{index}", target_id, "known liability")
    for source_id, record in ctx.sources.items():
        check(source_id, f"{record.path}#/source_id", source_id, "source id")
    for audit_id, record in ctx.repo.audits.items():
        check(audit_id, f"{record.path}#/audit_id", audit_id, "audit id")
    for sv_id, record in ctx.repo.state_variables.items():
        check(sv_id, f"{record.path}#/id", sv_id, "state variable id")
    for record in ctx.repo.definitional_edges:
        check(record.raw.get("subject"), f"{record.path}#/subject", None, "axiom subject")
        check(record.raw.get("object"), f"{record.path}#/object", None, "axiom object")
    return out


# ============================================================ V3: legal triples ===

@rule("V3", "Every (subject, predicate, object) triple is legal per ontology/edges.yaml.")
def check_triples(ctx: ValidationContext) -> list[Violation]:
    """Check triple legality for claims and for the definitional axioms."""
    out: list[Violation] = []

    def check(raw: dict[str, Any], locator: str, record_id: str | None) -> None:
        subject, predicate, obj = raw.get("subject"), raw.get("predicate"), raw.get("object")
        if not all(isinstance(v, str) and v for v in (subject, predicate, obj)):
            return
        subject_type = ctx.node_type_of(subject)
        object_type = ctx.node_type_of(obj)
        if subject_type is None or object_type is None:
            # V2 already reported the malformed id; do not double-report.
            return
        explanation = ctx.onto.explain_triple(subject_type, predicate, object_type)
        if explanation is None:
            return
        hint = ""
        if predicate in ctx.onto.edges:
            alternatives = ctx.onto.legal_predicates(subject_type, object_type)
            hint = (
                f" Relations legal for ({subject_type} -> {object_type}): "
                f"{list(alternatives)}."
                if alternatives
                else f" NO relation connects {subject_type} to {object_type}; the triple "
                "may be at the wrong level of the causal chain."
            )
        out.append(
            error(
                "V3",
                locator,
                f"illegal triple {subject} -{predicate}-> {obj}: {explanation}.{hint}",
                record_id=record_id,
                context={"subject_type": subject_type, "object_type": object_type},
            )
        )

    for claim_id, record in ctx.claims.items():
        check(record.raw, record.path, claim_id)
    for record in ctx.repo.definitional_edges:
        check(record.raw, record.path, None)
    return out


# ========================================================== V4: cross-references ===

def _nearest(value: str, universe: set[str], *, limit: int = 3) -> list[str]:
    """Closest declared ids to a dangling reference, for an actionable message.

    Two failure modes dominate in practice and both are cheap to diagnose: the same
    local name declared under a different prefix segment (``SV:cognition.arousal_level``
    when the declared id is ``SV:stability.arousal_level``), and a near-miss spelling.
    Naming the nearest candidates turns "does not exist" into a one-line fix.
    """
    from difflib import get_close_matches

    tail = value.rsplit(".", 1)[-1].rsplit(":", 1)[-1]
    same_tail = sorted(
        candidate
        for candidate in universe
        if candidate.rsplit(".", 1)[-1].rsplit(":", 1)[-1] == tail
    )
    if same_tail:
        return same_tail[:limit]
    return get_close_matches(value, sorted(universe), n=limit, cutoff=0.75)


@rule("V4", "All cross-references resolve (claim->source, assessment->claim, audit->claim/target, ...).")
def check_cross_references(ctx: ValidationContext) -> list[Violation]:
    """Every id a record points at must exist."""
    out: list[Violation] = []
    claim_ids = set(ctx.claims)
    source_ids = set(ctx.sources)
    target_ids = set(ctx.repo.targets)
    sv_ids = set(ctx.repo.state_variables)
    primitive_ids = set(ctx.onto.primitives)

    def resolve(
        value: Any, universe: set[str], kind: str, locator: str, record_id: str | None,
        *, severity_error: bool = True,
    ) -> None:
        if not isinstance(value, str) or value in universe:
            return
        message = (
            f"references {kind} {value!r}, which does not exist in this repository. "
            "Every cross-reference must resolve (rule V4); a dangling reference is "
            "indistinguishable from an invented one."
        )
        hint = _nearest(value, universe)
        if hint:
            message += f" Closest declared id(s): {hint}."
        out.append(
            (error if severity_error else warning)("V4", locator, message, record_id=record_id)
        )

    for claim_id, record in ctx.claims.items():
        for index, item in enumerate(record.raw.get("evidence") or []):
            if isinstance(item, dict):
                resolve(item.get("source_id"), source_ids, "source",
                        f"{record.path}#/evidence/{index}/source_id", claim_id)
        for index, dependency in enumerate(record.raw.get("dependencies") or []):
            resolve(dependency, claim_ids, "claim",
                    f"{record.path}#/dependencies/{index}", claim_id)
        release = (record.raw.get("provenance") or {}).get("database_release")
        resolve(release, source_ids, "source (provenance.database_release)",
                f"{record.path}#/provenance/database_release", claim_id)

    for record in ctx.repo.assessments:
        for index, facet in enumerate(record.raw.get("facets") or []):
            if not isinstance(facet, dict):
                continue
            for key in ("claim_refs", "counter_claim_refs"):
                for position, claim_ref in enumerate(facet.get(key) or []):
                    resolve(claim_ref, claim_ids, "claim",
                            f"{record.path}#/facets/{index}/{key}/{position}", record.record_id)
        resolve(record.raw.get("target_id"), target_ids, "target",
                f"{record.path}#/target_id", record.record_id)

    for audit_id, record in ctx.repo.audits.items():
        scope = record.raw.get("scope") or {}
        if scope.get("kind") == "claim":
            resolve(scope.get("id"), claim_ids, "claim", f"{record.path}#/scope/id", audit_id)
        elif scope.get("kind") == "target":
            resolve(scope.get("id"), target_ids, "target", f"{record.path}#/scope/id", audit_id)
        for index, change in enumerate(record.raw.get("claim_status_changes") or []):
            if isinstance(change, dict):
                resolve(change.get("claim_id"), claim_ids, "claim",
                        f"{record.path}#/claim_status_changes/{index}/claim_id", audit_id)
        for index, adjustment in enumerate(record.raw.get("adjustments") or []):
            if not isinstance(adjustment, dict):
                continue
            resolve(adjustment.get("target_id"), target_ids, "target",
                    f"{record.path}#/adjustments/{index}/target_id", audit_id)
            resolve(adjustment.get("claim_id"), claim_ids, "claim",
                    f"{record.path}#/adjustments/{index}/claim_id", audit_id)

    for target_id, record in ctx.repo.targets.items():
        hypothesis = record.raw.get("control_point_hypothesis") or {}
        for index, claim_ref in enumerate(hypothesis.get("mechanism_chain") or []):
            resolve(claim_ref, claim_ids, "claim",
                    f"{record.path}#/control_point_hypothesis/mechanism_chain/{index}", target_id)
        for index, link in enumerate(hypothesis.get("state_variables") or []):
            if not isinstance(link, dict):
                continue
            resolve(link.get("id"), sv_ids, "state variable",
                    f"{record.path}#/control_point_hypothesis/state_variables/{index}/id", target_id)
            for position, claim_ref in enumerate(link.get("claim_refs") or []):
                resolve(claim_ref, claim_ids, "claim",
                        f"{record.path}#/control_point_hypothesis/state_variables/{index}/claim_refs/{position}",
                        target_id)
        for index, primitive in enumerate(hypothesis.get("computational_primitives") or []):
            resolve(primitive, primitive_ids, "computational primitive",
                    f"{record.path}#/control_point_hypothesis/computational_primitives/{index}", target_id)

    for record in ctx.repo.state_variable_annotations:
        resolve(record.raw.get("state_variable_id"), sv_ids, "state variable",
                f"{record.path}#/state_variable_id", record.record_id)
        for index, claim_ref in enumerate(record.raw.get("claim_refs") or []):
            resolve(claim_ref, claim_ids, "claim", f"{record.path}#/claim_refs/{index}",
                    record.record_id)

    for record in ctx.repo.interventions.values():
        for index, claim_ref in enumerate(record.raw.get("claim_refs") or []):
            resolve(claim_ref, claim_ids, "claim", f"{record.path}#/claim_refs/{index}",
                    record.record_id)

    # State-variable definitions may reference primitives; the primitives reference
    # state variables. Both directions must resolve or the ontology is inconsistent.
    for sv_id, record in ctx.repo.state_variables.items():
        for index, primitive in enumerate(record.raw.get("related_primitives") or []):
            resolve(primitive, primitive_ids, "computational primitive",
                    f"{record.path}#/related_primitives/{index}", sv_id)
    for primitive_id, primitive in ctx.onto.primitives.items():
        for index, sv_ref in enumerate(primitive.related_state_variables):
            resolve(sv_ref, sv_ids, "state variable",
                    f"ontology/computational_primitives.yaml#/{primitive_id}/related_state_variables/{index}",
                    primitive_id)
    return out


# ============================================================== V5: evidence ===

@rule("V5", "Every claim has >=1 evidence item; every evidence item names a registered source.")
def check_evidence_present(ctx: ValidationContext) -> list[Violation]:
    """A claim with no evidence is not a claim (contract P2)."""
    out: list[Violation] = []
    for claim_id, record in ctx.claims.items():
        evidence = record.raw.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            out.append(
                error(
                    "V5",
                    f"{record.path}#/evidence",
                    "claim has no evidence item. A claim without at least one evidence "
                    "item bound to a registered, machine-verified source is invalid "
                    "(contract P2, rule V5). Withdraw the claim rather than leaving it "
                    "unsupported.",
                    record_id=claim_id,
                )
            )
            continue
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or not item.get("source_id"):
                out.append(
                    error(
                        "V5",
                        f"{record.path}#/evidence/{index}",
                        "evidence item names no source_id; evidence is always attached "
                        "to a registered source (rule V5).",
                        record_id=claim_id,
                    )
                )
    return out


# ========================================================== V6: source verification ===

@rule("V6", "Every registered source has a verification record with status = verified.")
def check_source_verification(ctx: ValidationContext) -> list[Violation]:
    """Rule V6, reported per source, with the index's own problems included."""
    out: list[Violation] = []
    out.extend(verification.index_violations(ctx.verification))
    out.extend(
        verification.missing_index_violation(
            ctx.verification, source_count=len(ctx.sources)
        )
    )
    if not ctx.verification.available:
        return out
    snapshot_only = set(
        vocab.subset("verification_status", "snapshot_verified_values", ctx.root)
    )
    for source_id, record in ctx.sources.items():
        status = ctx.verification.status_for(source_id)
        if status is None:
            out.append(
                warning(
                    "V6",
                    f"{record.path}#/source_id",
                    f"{source_id} has no verification record. It cannot be distinguished "
                    "from a fabricated identifier until it is checked against its "
                    "registry (contract §7). Run `make fetch-sources`, or "
                    "`scripts/fetch_source_metadata.py --all --offline` to rebuild from "
                    "the committed snapshots.",
                    record_id=source_id,
                )
            )
            continue
        if ctx.verification.is_verified(source_id, ctx.root):
            continue
        detail = ctx.verification.record_for(source_id) or {}
        extra = ""
        if status in snapshot_only:
            # Snapshot verification is the right check for a database release and the
            # WRONG check for a paper: a paper has a registry that can confirm it.
            extra = (
                f" That status means the pinned snapshot exists and still matches its "
                "checksum, which is the correct check for a database release or dataset "
                f"but not for {source_id.split(':', 2)[1]}: a source with a literature or "
                "trial registry must be confirmed against that registry. Register it "
                f"under a {SNAPSHOT_PREFIX_HINT} prefix if it really is a release."
            )
        elif status == "title_mismatch":
            extra = (
                f" Registry title: {detail.get('registry_title')!r}; recorded title: "
                f"{record.raw.get('title')!r}. Either the identifier is wrong or the "
                "title was not copied from the registry."
            )
        elif status == "year_mismatch":
            extra = (
                f" Registry year: {detail.get('registry_year')!r}; recorded year: "
                f"{record.raw.get('year')!r}."
            )
        elif status == "retracted":
            extra = " THE SOURCE IS RETRACTED; any claim resting on it must be withdrawn."
        elif status == "snapshot_missing_or_altered":
            extra = (
                " The snapshot this release was verified against is missing or its "
                "checksum no longer matches. This deliberately overlaps rule V19: the "
                "release is both unverified and a broken immutability guarantee."
            )
        elif status == "not_found":
            extra = (
                " The identifier did not resolve at its registry, which is what a "
                "fabricated identifier looks like."
            )
        if detail.get("_row_count"):
            extra += (
                f" (Worst status across {detail['_row_count']} rows from "
                f"{detail.get('_agents')}; duplication across agents is expected and the "
                "worst status wins.)"
            )
        out.append(
            error(
                "V6",
                f"{record.path}#/source_id",
                f"{source_id} has verification status {status!r}, which does not pass "
                f"rule V6.{extra}",
                record_id=source_id,
                context={"status": status},
            )
        )
    return out


# ================================================= V7: phenotype class / attribution ===

@rule("V7", "phenotype_class present for cognitive objects; causal_attribution present on all claims.")
def check_required_distinctions(ctx: ValidationContext) -> list[Violation]:
    """The contract's required distinctions must be fields, not prose."""
    out: list[Violation] = []
    cognitive_sv_domains = {"cognition", "workspace", "consolidation"}
    for claim_id, record in ctx.claims.items():
        if not record.raw.get("causal_attribution"):
            out.append(
                error(
                    "V7",
                    f"{record.path}#/causal_attribution",
                    "causal_attribution is mandatory on every claim (rule V7): "
                    "association is not causation, and the basis field is where that "
                    "distinction lives.",
                    record_id=claim_id,
                )
            )
        obj = record.raw.get("object")
        if not isinstance(obj, str):
            continue
        object_type = ctx.node_type_of(obj)
        needs_class = object_type == "CognitivePhenotype"
        if object_type == "StateVariable" and obj.startswith("SV:"):
            domain = obj.split(":", 1)[1].split(".", 1)[0]
            needs_class = needs_class or domain in cognitive_sv_domains
        if needs_class and not record.raw.get("phenotype_class"):
            out.append(
                error(
                    "V7",
                    f"{record.path}#/phenotype_class",
                    f"object {obj} is a cognitive endpoint, so phenotype_class is "
                    "mandatory (rule V7). It is how the graph keeps 'animal memory is "
                    "not human intelligence' and 'educational attainment is not "
                    "intelligence' visible instead of letting them fade into prose.",
                    record_id=claim_id,
                )
            )
    return out


# =========================================================== V8: translation block ===

@rule("V8", "translation.* fully populated on every claim (unknown is allowed and explicit).")
def check_translation(ctx: ValidationContext) -> list[Violation]:
    """Every translation key must be present; `unknown` is a legitimate value."""
    required = (
        "adult_relevance",
        "healthy_baseline",
        "supra_normal",
        "human_relevance",
        "general_intelligence_relevance",
    )
    out: list[Violation] = []
    for claim_id, record in ctx.claims.items():
        translation = record.raw.get("translation")
        if not isinstance(translation, dict):
            out.append(
                error(
                    "V8",
                    f"{record.path}#/translation",
                    "translation block is missing. All five keys are required on every "
                    "claim (rule V8); `unknown` is allowed and explicit, a missing key "
                    "is not.",
                    record_id=claim_id,
                )
            )
            continue
        for key in required:
            if translation.get(key) in (None, ""):
                out.append(
                    error(
                        "V8",
                        f"{record.path}#/translation/{key}",
                        f"translation.{key} is missing or empty. Use the explicit "
                        "`unknown`/`untested` value: an absent key reads as 'not "
                        "applicable', which is a different and usually false statement "
                        "(rule V8, contract P8).",
                        record_id=claim_id,
                    )
                )
    return out


# ========================================================= V9: no fake precision ===

# Record paths where a number is legitimate, as (kind, pointer-suffix) fragments.
_NUMERIC_ALLOWED_SUFFIXES: tuple[str, ...] = (
    "/effect_size/value",
    "/effect_size/ci_lower",
    "/effect_size/ci_upper",
    "/effect_size/p_value",
    "/sample_size/value",
    "/year",
    "/registry_year",
    "/uncertainty/level",
    "/level",
    "/counter_level",
    "/from_level",
    "/to_level",
    "/context/species_count",
    "/title_similarity",
    "/claimed_year",
    "/enrollment",
)

# Numeric slots that hold a DATABASE FACT rather than a judgement. They are exempt from
# rule V9 only when the record names the pinned release the fact came from, so the
# exemption buys visibility rather than trust.
_DATABASE_FACT_SUFFIXES: tuple[str, ...] = (
    "/max_clinical_phase/value",
    "/first_approval_year",
    "/chembl_max_phase",
    "/chembl_first_approval",
)


def _names_a_database_source(record: dict[str, Any]) -> bool:
    """Whether a record names the database release its numeric facts came from."""
    provenance = record.get("provenance") or {}
    return bool(
        record.get("database_source_id")
        or provenance.get("database_release")
        or provenance.get("pipeline")
        or (record.get("max_clinical_phase") or {}).get("source")
        or record.get("identifier_provenance")
    )


def _iter_numbers(node: Any, pointer: str = "") -> list[tuple[str, Any]]:
    """Every numeric leaf in a record, with its pointer. ``bool`` is not a number."""
    found: list[tuple[str, Any]] = []
    if isinstance(node, bool):
        return found
    if isinstance(node, (int, float)):
        found.append((pointer or "/", node))
    elif isinstance(node, dict):
        for key, value in node.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            found.extend(_iter_numbers(value, f"{pointer}/{escaped}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_iter_numbers(value, f"{pointer}/{index}"))
    return found


@rule("V9", "No hand-written probability or score outside effect_size / model outputs.")
def check_no_fake_precision(ctx: ValidationContext) -> list[Violation]:
    """Contract P3 made executable.

    A number in a curated record is acceptable only when it is (a) an effect size or
    sample size copied verbatim, (b) a structural integer such as a year or an ordinal
    grade, (c) a field of a verbatim database record whose provenance is pinned, or
    (d) a named model's output carrying its interpretation limits. Anything else — and
    in particular any float strictly between 0 and 1 — is the fake precision the
    contract exists to prevent.
    """
    out: list[Violation] = []
    groups: list[tuple[str, list[loaders.LoadedRecord]]] = [
        ("claim", list(ctx.claims.values())),
        ("target", list(ctx.repo.targets.values())),
        ("assessment", ctx.repo.assessments),
        ("audit", list(ctx.repo.audits.values())),
        ("intervention", list(ctx.repo.interventions.values())),
        ("state_variable_annotation", ctx.repo.state_variable_annotations),
    ]
    for kind, items in groups:
        for item in items:
            provenance = item.raw.get("provenance") or {}
            pinned = bool(provenance.get("database_release") or provenance.get("pipeline"))
            attributed = _names_a_database_source(item.raw)
            for pointer, value in _iter_numbers(item.raw):
                if any(pointer.endswith(suffix) for suffix in _NUMERIC_ALLOWED_SUFFIXES):
                    continue
                if any(pointer.endswith(suffix) for suffix in _DATABASE_FACT_SUFFIXES):
                    if attributed:
                        continue
                    out.append(
                        error(
                            "V9",
                            f"{item.path}#{pointer}",
                            f"database fact {value!r} is recorded but the record names no "
                            "database release it came from. Add `database_source_id` (a "
                            "SRC:DB:* id) or `provenance.database_release`: a database "
                            "number is admissible because its provenance is VISIBLE, not "
                            "because it is a number (contract P3/P7, rule V9).",
                            record_id=item.record_id,
                        )
                    )
                    continue
                if "/chembl_fields_as_returned/" in pointer and attributed:
                    # Verbatim database payload from a named release: the numbers are
                    # the database's, not the agent's.
                    continue
                if "/database_record/" in pointer or pointer.endswith("/database_record"):
                    if pinned:
                        continue
                    out.append(
                        error(
                            "V9",
                            f"{item.path}#{pointer}",
                            f"number {value!r} sits inside a verbatim database_record, but "
                            "the record's provenance names neither a `database_release` "
                            "nor a `pipeline`. Numbers copied from a database are only "
                            "admissible when the release they came from is pinned "
                            "(contract P3/P7, rule V9).",
                            record_id=item.record_id,
                        )
                    )
                    continue
                if "/model_outputs/" in pointer:
                    # The model-output contract is enforced by the schema and the
                    # pydantic model (derived_from + interpretation_limits required).
                    continue
                if isinstance(value, float) and 0.0 < value < 1.0:
                    out.append(
                        error(
                            "V9",
                            f"{item.path}#{pointer}",
                            f"hand-written probability/score {value!r} in a {kind} record. "
                            "Numbers appear only as effect sizes copied verbatim from a "
                            "source (`as_reported`) or as the output of a named model "
                            "under models/ (contract P3, rule V9). Express a judgement as "
                            "an ordinal rubric level instead.",
                            record_id=item.record_id,
                        )
                    )
                    continue
                # A non-probability number in an unapproved slot is reported as a
                # WARNING rather than an error, and --strict escalates it. The contract
                # says "any numeric field not accompanied by derived_from ... is a
                # failure"; taken literally that fails honest integer counts
                # (coverage_summary.power_domain_variables_total, max_clinical_phase 4)
                # while the danger contract P3 names is the fabricated PROBABILITY,
                # which stays an error above. The narrowing is recorded as deviation D7
                # in docs/ONTOLOGY_NOTES.md.
                out.append(
                    warning(
                        "V9",
                        f"{item.path}#{pointer}",
                        f"numeric value {value!r} in a field that is not an approved "
                        "numeric slot and carries no `derived_from` pointing at a model "
                        "under models/ (rule V9). Approved slots: effect_size.*, "
                        "sample_size.value, year, ordinal levels, context.species_count, "
                        "uncertainty.model_outputs[*]. If this is a count copied from a "
                        "database, keep it inside `database_record` or `max_clinical_phase` "
                        "so its provenance is visible; if it is a judgement, express it as "
                        "an ordinal level.",
                        record_id=item.record_id,
                    )
                )
    # Advisory: a copied number normally arrives with the text it was copied from.
    for claim_id, record in ctx.claims.items():
        for index, item in enumerate(record.raw.get("evidence") or []):
            if not isinstance(item, dict):
                continue
            sample = item.get("sample_size") or {}
            if sample.get("value") == 0 and item.get("evidence_role") == "supports":
                out.append(
                    warning(
                        "V9",
                        f"{record.path}#/evidence/{index}",
                        "sample_size.value is 0 with evidence_role: supports. An "
                        "enrolment of zero is a real and important fact — a programme "
                        "registered and never run — but it cannot SUPPORT a claim about "
                        "what happens. `null_result` or `qualifies` is almost always the "
                        "honest role.",
                        record_id=claim_id,
                    )
                )
            if sample.get("value") is not None and not sample.get("reported_as"):
                out.append(
                    warning(
                        "V9",
                        f"{record.path}#/evidence/{index}/sample_size",
                        f"sample_size.value is {sample['value']!r} with no `reported_as` "
                        "text. Contract §4 permits this, but a copied sample size normally "
                        "arrives with the source's own wording; without it the number "
                        "cannot be audited against the source.",
                        record_id=claim_id,
                    )
                )
    return out


# ====================================================== V10: ordinal uncertainty ===

@rule("V10", "uncertainty.representation is ordinal_grade only; level in 0..4.")
def check_ordinal_uncertainty(ctx: ValidationContext) -> list[Violation]:
    """Curated records express uncertainty as an ordinal grade, never as a number."""
    out: list[Violation] = []
    allowed = set(vocab.subset("uncertainty_representation", "allowed_in_curated_records", ctx.root))
    levels = set(vocab.values("evidence_strength_v1", ctx.root))
    for claim_id, record in ctx.claims.items():
        uncertainty = record.raw.get("uncertainty")
        if not isinstance(uncertainty, dict):
            out.append(
                error("V10", f"{record.path}#/uncertainty",
                      "uncertainty block is missing; every claim carries an ordinal "
                      "uncertainty grade (rule V10).", record_id=claim_id)
            )
            continue
        representation = uncertainty.get("representation")
        if representation not in allowed:
            out.append(
                error(
                    "V10",
                    f"{record.path}#/uncertainty/representation",
                    f"representation is {representation!r}; curated records may use "
                    f"{sorted(allowed)} only. A distribution or a probability belongs to a "
                    "model under models/, not to a curated claim (rule V10).",
                    record_id=claim_id,
                )
            )
        level = uncertainty.get("level")
        if isinstance(level, bool) or not isinstance(level, int) or level not in levels:
            out.append(
                error(
                    "V10",
                    f"{record.path}#/uncertainty/level",
                    f"level is {level!r}; it must be an integer in {sorted(levels)} on "
                    "the evidence_strength_v1 scale (contract §5.3). It is a rubric "
                    "position, not a probability.",
                    record_id=claim_id,
                )
            )
    return out


# ============================================================= V11: facet ownership ===

def _database_gradable_facets(root: Path) -> tuple[set[str], bool]:
    """Facets the rubric flags ``database_gradable: true``, and whether it was readable.

    Read from ``models/ranking/facet_rubric_v0_1.yaml`` rather than hard-coded: the
    contract names ``tractability`` as the only current case, but the flag is the
    authority and the rubric belongs to ``agent:integration``.
    """
    import yaml as _yaml

    path = paths.facet_rubric_file(root)
    if not path.is_file():
        return set(), False
    try:
        document = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - another agent's file; report, never crash
        return set(), False
    entries = document.get("facets")
    flagged: set[str] = set()
    if isinstance(entries, dict):
        for name, spec in entries.items():
            if isinstance(spec, dict) and spec.get("database_gradable") is True:
                flagged.add(str(name))
    elif isinstance(entries, list):
        for spec in entries:
            if isinstance(spec, dict) and spec.get("database_gradable") is True:
                flagged.add(str(spec.get("facet")))
    return flagged, True


@rule("V11", "Facet names, owners and levels conform to the catalogue; an agent writes only its own facets.")
def check_facet_ownership(ctx: ValidationContext) -> list[Violation]:
    """Only the owning agent may grade a facet, and only on evidence it may cite.

    Also enforces R7: a facet may cite ``source_refs`` in place of ``claim_refs`` only
    when the rubric flags it ``database_gradable: true``. Forcing a druggability
    annotation into a claim record — inventing a triple, a claim type and meaningless
    translation values — makes a non-biological annotation look like biological
    evidence, and is prohibited.
    """
    out: list[Violation] = []
    catalogue = vocab.facet_catalogue(ctx.root)
    gradable, rubric_readable = _database_gradable_facets(ctx.root)
    for record in ctx.repo.assessments:
        author = record.raw.get("assessed_by")
        target_id = record.raw.get("target_id")
        lead = None
        target = ctx.repo.targets.get(str(target_id))
        if target is not None:
            lead_atlas = target.raw.get("lead_atlas")
            lead = f"agent:{lead_atlas}" if lead_atlas else None
        for index, facet in enumerate(record.raw.get("facets") or []):
            if not isinstance(facet, dict):
                continue
            name = facet.get("facet")
            entry = catalogue.get(str(name))
            if entry is None:
                out.append(
                    error(
                        "V11",
                        f"{record.path}#/facets/{index}/facet",
                        f"{name!r} is not in the facet catalogue (contract §5.2). The "
                        f"catalogue is closed: {sorted(catalogue)}.",
                        record_id=record.record_id,
                    )
                )
                continue
            owners = list(entry.get("owners") or [])
            permitted = {owner for owner in owners if owner != "lead_atlas"}
            if "lead_atlas" in owners and lead is not None:
                permitted.add(lead)
            if "lead_atlas" in owners and lead is None:
                out.append(
                    warning(
                        "V11",
                        f"{record.path}#/facets/{index}",
                        f"facet {name!r} is owned by the lead atlas, but target "
                        f"{target_id!r} has no dossier in this repository, so ownership "
                        "cannot be checked.",
                        record_id=record.record_id,
                    )
                )
                continue
            claim_refs = [c for c in (facet.get("claim_refs") or []) if isinstance(c, str)]
            source_refs = [c for c in (facet.get("source_refs") or []) if isinstance(c, str)]
            basis = facet.get("evidence_basis")
            if source_refs and not claim_refs:
                if not rubric_readable:
                    out.append(
                        warning(
                            "V11",
                            f"{record.path}#/facets/{index}/source_refs",
                            f"facet {name!r} is graded from source_refs alone, but "
                            "models/ranking/facet_rubric_v0_1.yaml could not be read, so "
                            "the `database_gradable` flag that licenses it cannot be "
                            "checked.",
                            record_id=record.record_id,
                        )
                    )
                elif str(name) not in gradable:
                    out.append(
                        error(
                            "V11",
                            f"{record.path}#/facets/{index}/source_refs",
                            f"facet {name!r} is graded from source_refs with no "
                            "claim_refs, but the rubric does not flag it "
                            f"`database_gradable: true` (flagged: {sorted(gradable) or 'none'}). "
                            "Database-derived grading is permitted only for facets the "
                            "rubric allows it for; every other facet needs claim "
                            "references (contract §5.2, R7).",
                            record_id=record.record_id,
                        )
                    )
                allowed_bases = set(
                    vocab.subset("evidence_basis", "source_refs_only_values", ctx.root)
                )
                if basis not in allowed_bases:
                    out.append(
                        error(
                            "V11",
                            f"{record.path}#/facets/{index}/evidence_basis",
                            f"facet {name!r} cites source_refs alone but declares "
                            f"evidence_basis {basis!r}; it must be one of "
                            f"{sorted(allowed_bases)} so a reader can see the grade rests "
                            "on a pinned database release rather than on curated papers.",
                            record_id=record.record_id,
                        )
                    )
            if author not in permitted:
                out.append(
                    error(
                        "V11",
                        f"{record.path}#/facets/{index}",
                        f"{author} graded facet {name!r}, which is owned by "
                        f"{sorted(permitted)} (contract §5.2, rule V11). Disagreement is "
                        "expressed as a new artefact — a contradicting claim or an audit "
                        "finding — never by grading another agent's facet.",
                        record_id=record.record_id,
                    )
                )
    return out


# ========================================================= V12: downgrade-only audits ===

@rule("V12", "Audit adjustments are downgrades only and reference existing facets/claims.")
def check_downgrade_only(ctx: ValidationContext) -> list[Violation]:
    """The red team may downgrade, never upgrade (contract P6)."""
    out: list[Violation] = []
    catalogue = vocab.facet_catalogue(ctx.root)
    for audit_id, record in ctx.repo.audits.items():
        for index, adjustment in enumerate(record.raw.get("adjustments") or []):
            if not isinstance(adjustment, dict):
                continue
            locator = f"{record.path}#/adjustments/{index}"
            if adjustment.get("kind") != "facet":
                continue
            facet = adjustment.get("facet")
            if str(facet) not in catalogue:
                out.append(
                    error("V12", f"{locator}/facet",
                          f"adjustment names facet {facet!r}, which is not in the "
                          "catalogue (contract §5.2).", record_id=audit_id)
                )
            field_name = adjustment.get("field", "level")
            from_level, to_level = adjustment.get("from_level"), adjustment.get("to_level")
            if not isinstance(from_level, int) or not isinstance(to_level, int):
                out.append(
                    error("V12", locator,
                          "facet adjustment needs integer from_level and to_level "
                          "(rule V12).", record_id=audit_id)
                )
                continue
            if field_name == "level" and to_level >= from_level:
                out.append(
                    error(
                        "V12",
                        locator,
                        f"adjustment moves facet {facet!r} level {from_level} -> "
                        f"{to_level}, which is not a downgrade. The red team can "
                        "downgrade, never upgrade (contract P6, rule V12). To record "
                        "contradicting evidence, raise counter_level with "
                        "`field: counter_level`.",
                        record_id=audit_id,
                    )
                )
            elif field_name == "counter_level" and to_level <= from_level:
                out.append(
                    error(
                        "V12",
                        locator,
                        f"adjustment moves facet {facet!r} counter_level {from_level} -> "
                        f"{to_level}. Lowering the contradicting-evidence grade is an "
                        "upgrade of the target's standing, which the red team may not do "
                        "(contract P6, rule V12).",
                        record_id=audit_id,
                    )
                )
    return out


# ============================================================ V13: claim registry lock ===

@rule("V13", "Every claim id in evidence/claims/claim_registry.lock still exists.")
def check_claim_lock(ctx: ValidationContext) -> list[Violation]:
    """Provenance is append-only: a locked claim id may never disappear."""
    out: list[Violation] = []
    present = set(ctx.claims)
    for claim_id in ctx.repo.lock_claim_ids:
        if claim_id not in present:
            out.append(
                error(
                    "V13",
                    "evidence/claims/claim_registry.lock",
                    f"{claim_id} is recorded in the lock but no longer exists. "
                    "PROVENANCE IS APPEND-ONLY (contract P6): a claim is withdrawn with "
                    "`status: withdrawn` and a superseding audit finding, never deleted. "
                    "Restore the record.",
                    record_id=claim_id,
                )
            )
    return out


# ================================================================ V14: withdrawal ===

@rule("V14", "Withdrawal requires status: withdrawn AND a superseding audit finding.")
def check_withdrawal(ctx: ValidationContext) -> list[Violation]:
    """A withdrawal is a recorded decision with an audit behind it."""
    out: list[Violation] = []
    audited_withdrawals: set[str] = set()
    for record in ctx.repo.audits.values():
        for change in record.raw.get("claim_status_changes") or []:
            if isinstance(change, dict) and change.get("to") in {"withdrawn", "downgraded", "contested"}:
                audited_withdrawals.add(str(change.get("claim_id")))
    for claim_id, record in ctx.claims.items():
        status = record.raw.get("status")
        if status == "withdrawn" and claim_id not in audited_withdrawals:
            out.append(
                error(
                    "V14",
                    f"{record.path}#/status",
                    "claim is withdrawn but no audit record carries a superseding "
                    "claim_status_change for it (rule V14). A withdrawal is an audited "
                    "decision, not a self-service edit.",
                    record_id=claim_id,
                )
            )
        elif status in {"contested", "downgraded"} and claim_id not in audited_withdrawals:
            out.append(
                warning(
                    "V14",
                    f"{record.path}#/status",
                    f"claim status is {status!r} with no audit record recording the "
                    "change. Self-declared contestation is allowed, but the red team's "
                    "audit is what makes it reviewable.",
                    record_id=claim_id,
                )
            )
        if record.model is not None and getattr(record.model, "status_change_lacks_reason", False):
            out.append(
                warning(
                    "V14",
                    f"{record.path}#/status_reason",
                    f"claim status is {status!r} with no in-record reason. The contract "
                    "does not require the field, but a status change with no stated "
                    "reason cannot be reviewed without hunting for the audit.",
                    record_id=claim_id,
                )
            )
    return out


# =========================================================== V15: audit coverage ===

@rule("V15", "Every seed target has >=1 audit record with the full mandatory check catalogue.")
def check_audit_coverage(ctx: ValidationContext) -> list[Violation]:
    """Gate G4. A warning until the red team has run; `--strict` escalates it."""
    out: list[Violation] = []
    catalogue = set(vocab.values("audit_check", ctx.root))
    seed_targets = [
        str(entry.get("target_id"))
        for entry in (ctx.repo.seed_registry.get("targets") or [])
        if isinstance(entry, dict) and entry.get("target_id")
    ]
    audits_by_target: dict[str, list[loaders.LoadedRecord]] = {}
    for record in ctx.repo.audits.values():
        scope = record.raw.get("scope") or {}
        if scope.get("kind") == "target":
            audits_by_target.setdefault(str(scope.get("id")), []).append(record)

    for target_id in sorted(seed_targets):
        audits = audits_by_target.get(target_id, [])
        if not audits:
            out.append(
                warning(
                    "V15",
                    "targets/seed_registry.yaml",
                    f"seed target {target_id} has no audit record. Gate G4 requires a "
                    "full red-team audit per seed target before integration; this is a "
                    "warning while the red team has not run and an error under --strict.",
                    record_id=target_id,
                )
            )
            continue
        for record in audits:
            performed = {
                str(check.get("check"))
                for check in (record.raw.get("checks") or [])
                if isinstance(check, dict)
            }
            missing = sorted(catalogue - performed)
            if missing:
                out.append(
                    error(
                        "V15",
                        f"{record.path}#/checks",
                        f"audit of {target_id} omits {len(missing)} mandatory check(s): "
                        f"{missing}. Every check in the catalogue must appear; "
                        "`not_applicable` is a legitimate result but silence is not "
                        "(contract §6, rule V15).",
                        record_id=record.record_id,
                    )
                )
    return out


# ======================================================== V16: binding is not efficacy ===

@rule("V16", "No efficacy assertion from binding alone (CHANGES_STATE / edges into EFFECT:*).")
def check_efficacy_gate(ctx: ValidationContext) -> list[Violation]:
    """The narrowest gate in the ontology.

    An edge that asserts an effect — ``CHANGES_STATE``, or any relation whose object is
    a ``DesiredEffect`` — may only be licensed by a claim whose ``claim_type`` is in the
    relation's ``allowed_claim_types``, which for those relations is the
    efficacy-licensing set. Binding, mechanism, expression, association and theoretical
    claims can never license it.
    """
    out: list[Violation] = []
    effect_predicates = set(ctx.onto.effect_asserting_predicates())
    licensing = vocab.efficacy_licensing_claim_types(ctx.root)

    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        obj = record.raw.get("object")
        claim_type = record.raw.get("claim_type")
        if not isinstance(predicate, str) or not isinstance(obj, str):
            continue
        graph_inert = set(vocab.subset("claim_type", "graph_inert_values", ctx.root))
        if claim_type in graph_inert:
            # An evidence_gap is GRAPH-INERT: it compiles to an evidence-layer record
            # and no biological or intervention edge, so there is no effect edge for
            # V16 to gate. Rule V16c is what keeps it honest, by checking that every
            # evidence item really does report an unmeasured endpoint.
            continue
        object_type = ctx.node_type_of(obj)
        if not ctx.onto.asserts_effect(predicate, object_type):
            continue
        # An effect assertion is licensed only by the intersection of the relation's
        # own allowed_claim_types and the efficacy-licensing set. Binding, mechanism,
        # expression, association and theory can never license it.
        allowed = set(ctx.onto.allowed_claim_types(predicate)) & licensing or licensing
        if claim_type in allowed:
            continue
        reason = (
            f"relation {predicate} asserts an effect"
            if predicate in effect_predicates
            else f"object {obj} is a {object_type}, so a {predicate} edge into it is an "
                 "efficacy-grade assertion"
        )
        out.append(
            error(
                "V16",
                f"{record.path}#/claim_type",
                f"{reason}, but claim_type is {claim_type!r}. BINDING IS NEVER EFFICACY "
                f"(contract V16): only {sorted(licensing)} can license it. A "
                "pharmacology_binding or mechanistic claim supports a TARGETS / "
                "AGONISES / INHIBITS edge, not a change of state.",
                record_id=claim_id,
                context={"predicate": predicate, "claim_type": claim_type},
            )
        )

    # Target dossiers must not reach a DesiredEffect through binding claims alone.
    for target_id, record in ctx.repo.targets.items():
        hypothesis = record.raw.get("control_point_hypothesis") or {}
        chain = [str(c) for c in (hypothesis.get("mechanism_chain") or [])]
        if not chain:
            continue
        types = {
            str((ctx.claim_of(claim_id) or {}).get("claim_type"))
            for claim_id in chain
            if ctx.claim_of(claim_id) is not None
        }
        for index, link in enumerate(hypothesis.get("state_variables") or []):
            if not isinstance(link, dict):
                continue
            if link.get("direction") in {None, "unclear"}:
                continue
            refs = [str(c) for c in (link.get("claim_refs") or [])]
            link_types = {
                str((ctx.claim_of(claim_id) or {}).get("claim_type"))
                for claim_id in refs
                if ctx.claim_of(claim_id) is not None
            } or types
            if link_types and not (link_types & licensing):
                out.append(
                    error(
                        "V16",
                        f"{record.path}#/control_point_hypothesis/state_variables/{index}",
                        f"the dossier asserts direction {link.get('direction')!r} on "
                        f"{link.get('id')} but the cited claims are of type(s) "
                        f"{sorted(link_types)}, none of which can license an effect. "
                        f"Only {sorted(licensing)} can (rule V16). Set direction to "
                        "`unclear` or cite perturbation evidence.",
                        record_id=target_id,
                    )
                )
    return out


# ============================ V3c: a claim type must be one its relation permits ===

@rule("V3c", "A claim's claim_type must be in its relation's allowed_claim_types.")
def check_claim_type_permitted(ctx: ValidationContext) -> list[Violation]:
    """Enforce ``allowed_claim_types`` for EVERY relation that declares one.

    This was the gap behind a real divergence: ``preclinical_harm`` was accepted on
    ``INCREASES_RISK`` by the validator and rejected by ``ontology/edges.yaml``, because
    rule V16 only ever checked the EFFECT-asserting relations and nothing enforced the
    declared list for the rest. An agent then built a local check mirroring the
    validator, and a record could pass one tool and fail another depending on which
    agent ran which. The contract's own preamble applies between the validator and the
    ontology as much as between the validator and the contract: where they disagree,
    that is a bug.

    A `claim_type: evidence_gap` on a causal or interventional relation is a CORRECT
    failure of this rule, not an exemption to add. A gap is graph-inert, so attaching it
    to MODULATES or CONSTRAINS would assert exactly what the record is refusing to
    assert. Its home is the evidence-layer relation ABOUT, whose natural triple makes
    the claim its own subject.
    """
    out: list[Violation] = []
    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        claim_type = record.raw.get("claim_type")
        if not isinstance(predicate, str) or predicate not in ctx.onto.edges:
            continue
        allowed = ctx.onto.allowed_claim_types(predicate)
        if not allowed:
            # The relation is reference-data-only; a claim should not be licensing it.
            if ctx.onto.requires_claim(predicate):
                continue
            continue
        if claim_type in allowed:
            continue
        out.append(
            error(
                "V3c",
                f"{record.path}#/claim_type",
                f"claim_type {claim_type!r} is not in {predicate}'s allowed_claim_types "
                f"{sorted(allowed)} (ontology/edges.yaml). The relation declares which "
                "evidence grades may license it; if the grade is right and the list is "
                "wrong, that is an ontology bug to report rather than a record to bend.",
                record_id=claim_id,
                context={"predicate": predicate, "claim_type": claim_type},
            )
        )
    return out


# ==================================================== V16b: null results are findings ===

@rule("V16b", "A NO_DETECTED_EFFECT_ON claim needs >=1 null_result or contradicts evidence item.")
def check_null_result_edges(ctx: ValidationContext) -> list[Violation]:
    """Contract V16b: a null edge reports a performed attempt, never a gap.

    Without this relation the graph drifts positive: a positive trial compiles into an
    edge and an equally well-powered null trial of the same intervention compiles into
    nothing. Allowing the relation creates the opposite risk — writing a null edge for
    a relationship nobody tested, which manufactures a finding out of a gap. This rule
    closes that hole by requiring evidence that an attempt was made and reported.
    """
    out: list[Violation] = []
    null_predicates = set(ctx.onto.null_result_predicates())
    if not null_predicates:
        return out
    accepted_roles = {"null_result", "contradicts"}
    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        if predicate not in null_predicates:
            continue
        roles = [
            str(item.get("evidence_role"))
            for item in (record.raw.get("evidence") or [])
            if isinstance(item, dict)
        ]
        if set(roles) & accepted_roles:
            continue
        out.append(
            error(
                "V16b",
                f"{record.path}#/evidence",
                f"claim uses {predicate} but no evidence item has evidence_role in "
                f"{sorted(accepted_roles)} (found {roles or 'none'}). A null edge asserts "
                "that an attempt WAS PERFORMED AND REPORTED and detected no effect; it "
                "must never encode absence of evidence. An untested relationship is "
                "represented by the ABSENCE of an edge (contract V16b).",
                record_id=claim_id,
                context={"predicate": predicate, "roles": roles},
            )
        )
    return out


# ============================== V16c: a measured absence is not an absence of measurement ===

@rule("V16c", "A null relation needs a MEASURED endpoint; an unmeasured one is an evidence_gap.")
def check_measured_absence(ctx: ValidationContext) -> list[Violation]:
    """Contract V16c, the most consequential amendment in Sprint 1.

    The contract could express "tested and found no effect" but not "the only human
    trial of this mechanism never measured a cognitive endpoint". Two brake-atlas claims
    were typed ``clinical_null`` when they were the latter, and read mechanically they
    looked like failed trials. This rule separates the two states, and the message says
    which one the record is actually in, because that is the whole point.
    """
    out: list[Violation] = []
    null_predicates = set(ctx.onto.null_result_predicates())
    if not null_predicates:
        return out
    measured = set(vocab.subset("endpoint_measured", "measured_values", ctx.root))
    gap = set(vocab.subset("endpoint_measured", "gap_values", ctx.root))
    accepted_roles = {"null_result", "contradicts"}

    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        claim_type = record.raw.get("claim_type")
        items = [i for i in (record.raw.get("evidence") or []) if isinstance(i, dict)]
        if not items:
            continue
        states = [str(i.get("endpoint_measured", "unknown")) for i in items]
        roles = [str(i.get("evidence_role")) for i in items]
        all_unmeasured = bool(states) and all(state in gap for state in states)

        if predicate in null_predicates:
            qualifying = [
                index
                for index, item in enumerate(items)
                if str(item.get("endpoint_measured", "unknown")) in measured
                and str(item.get("evidence_role")) in accepted_roles
            ]
            if qualifying:
                continue
            if all_unmeasured:
                diagnosis = (
                    "EVERY evidence item says the endpoint was not measured in the "
                    "protocol, so this record is an ABSENCE OF MEASUREMENT, not a "
                    "measured absence. Re-type it as claim_type: evidence_gap, which is "
                    "graph-inert: it creates an evidence-layer record and no biological "
                    "or intervention edge, because a gap is not a finding about biology."
                )
            else:
                diagnosis = (
                    f"no evidence item has BOTH endpoint_measured in {sorted(measured)} "
                    f"and evidence_role in {sorted(accepted_roles)} (states: {states}, "
                    f"roles: {roles}). A null edge asserts that the endpoint WAS measured "
                    "and no effect was detected; if it was never measured, the claim is "
                    "an evidence_gap instead."
                )
            out.append(
                error("V16c", f"{record.path}#/evidence", diagnosis, record_id=claim_id,
                      context={"endpoint_measured": states, "evidence_role": roles})
            )
            continue

        if claim_type == "evidence_gap":
            if not all_unmeasured:
                out.append(
                    error(
                        "V16c",
                        f"{record.path}#/claim_type",
                        f"claim_type is evidence_gap, but not every evidence item reports "
                        f"an unmeasured endpoint (states: {states}). An evidence_gap "
                        "records that the endpoint was NOT MEASURED; a study that measured "
                        "it and found nothing is a null result, and the two must not be "
                        "conflated in either direction.",
                        record_id=claim_id,
                    )
                )
            continue

        if all_unmeasured and claim_type in {"clinical_null", "clinical_efficacy", "pharmacodynamic"}:
            out.append(
                error(
                    "V16c",
                    f"{record.path}#/claim_type",
                    f"every evidence item reports endpoint_measured in {sorted(gap)}, but "
                    f"claim_type is {claim_type!r}. A trial that never measured the "
                    "endpoint is NOT a failed trial; read mechanically this record looks "
                    "like one. Use claim_type: evidence_gap.",
                    record_id=claim_id,
                )
            )
    return out


# ================== V16b-sym: a null must be expressible wherever the positive is ===

@rule("V16b-sym", "The null relation's domain/range covers every relation it can negate.")
def check_null_symmetry(ctx: ValidationContext) -> list[Violation]:
    """Contract V16b-sym.

    An ontology in which a positive edge is expressible and its corresponding null is
    not is structurally biased towards positive findings. That is not hypothetical: a
    performed cross-clade null (absolute brain volume predicted nothing about
    self-regulation) could not use the null relation because the tested predictor is a
    BrainRegion, so it compiled as CONSTRAINS with direction: unclear — and any
    traversal that ignores direction reads the comparative atlas's most-cited
    deflationary result as SUPPORT.

    The union is DERIVED from the ``negatable`` flag, never listed: a hand-maintained
    list would drift the first time somebody added a relation.
    """
    out: list[Violation] = []
    null_predicates = ctx.onto.null_result_predicates()
    if not null_predicates:
        return out
    required_domain, required_range = ctx.onto.negatable_union()
    for predicate in null_predicates:
        have_domain = set(ctx.onto.edge_domain(predicate))
        have_range = set(ctx.onto.edge_range(predicate))
        for side, required, have in (
            ("domain", required_domain, have_domain),
            ("range", required_range, have_range),
        ):
            missing = sorted(set(required) - have)
            if missing:
                out.append(
                    error(
                        "V16b-sym",
                        f"ontology/edges.yaml#{predicate}/{side}",
                        f"{predicate} {side} is missing {missing}, which appear in the "
                        f"{side} of relations it can negate "
                        f"({list(ctx.onto.negatable_predicates())}). A null must be "
                        "expressible wherever the corresponding positive claim is, or the "
                        "ontology is biased towards positive findings (contract V16b-sym).",
                    )
                )

    # Every null claim must name what it negates, and the triple must be legal there.
    negatable = set(ctx.onto.negatable_predicates())
    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        if predicate not in set(null_predicates):
            continue
        negated = record.raw.get("negated_relation")
        if not negated:
            out.append(
                error(
                    "V16b-sym",
                    f"{record.path}#/negated_relation",
                    f"claim uses {predicate} but names no `negated_relation`. A null edge "
                    "should say WHAT WAS TESTED and found absent, not merely that "
                    f"something was absent. Negatable relations: {sorted(negatable)}.",
                    record_id=claim_id,
                )
            )
            continue
        if negated not in negatable:
            out.append(
                error(
                    "V16b-sym",
                    f"{record.path}#/negated_relation",
                    f"negated_relation {negated!r} is not a negatable relation "
                    f"(negatable: {sorted(negatable)}).",
                    record_id=claim_id,
                )
            )
            continue
        subject_type = ctx.node_type_of(str(record.raw.get("subject")))
        object_type = ctx.node_type_of(str(record.raw.get("object")))
        if subject_type is None or object_type is None:
            continue
        explanation = ctx.onto.explain_triple(subject_type, negated, object_type)
        if explanation is not None:
            out.append(
                error(
                    "V16b-sym",
                    f"{record.path}#/negated_relation",
                    f"the triple is not legal under the relation it claims to negate "
                    f"({negated}): {explanation}. A null must negate a statement that "
                    "could have been made.",
                    record_id=claim_id,
                )
            )
    return out


# ===================================== V3b: between-species claims need two species ===

@rule("V3b", "A between-species relation needs >=2 species in context.species.")
def check_between_species_claims(ctx: ValidationContext) -> list[Violation]:
    """R6: a between-species statement with one species is meaningless.

    The comparative atlas previously had no relation for "this property differs between
    species" and borrowed causal relations, which overstated the evidence. The relations
    now exist; this rule keeps them honest, including the phylogenetic-control field
    without which a result that survived a mixed model and an uncontrolled cross-species
    regression look identical.
    """
    out: list[Violation] = []
    between = set(ctx.onto.between_species_predicates())
    if not between:
        return out
    for claim_id, record in ctx.claims.items():
        predicate = record.raw.get("predicate")
        if predicate not in between:
            continue
        context = record.raw.get("context") or {}
        species = [s for s in (context.get("species") or []) if isinstance(s, str)]
        if len(species) < 2:
            out.append(
                error(
                    "V3b",
                    f"{record.path}#/context/species",
                    f"claim uses {predicate} with {len(species)} species "
                    f"({species}). A between-species statement needs at least two: with "
                    "one species there is nothing to compare.",
                    record_id=claim_id,
                )
            )
        declared = context.get("species_count")
        if isinstance(declared, int) and not isinstance(declared, bool) and declared < len(species):
            out.append(
                error(
                    "V3b",
                    f"{record.path}#/context/species_count",
                    f"species_count is {declared} but context.species names "
                    f"{len(species)} species; the count must not understate the comparison.",
                    record_id=claim_id,
                )
            )
        if not context.get("phylogenetic_control"):
            out.append(
                warning(
                    "V3b",
                    f"{record.path}#/context/phylogenetic_control",
                    f"claim uses {predicate} but declares no phylogenetic_control. "
                    "AN UNCONTROLLED CROSS-SPECIES CORRELATION IS NOT CONVERGENCE: "
                    "related species share traits by descent, so `none` is an honest and "
                    "common answer — and it is a different answer from `not_reported`.",
                    record_id=claim_id,
                )
            )
    return out


# ============================== V-DIR: a state-dependent sign must name its context ===

@rule("V-DIR", "direction: state_dependent requires a non-empty direction_context.")
def check_direction_context(ctx: ValidationContext) -> list[Violation]:
    """R10: `state_dependent` is a characterised interaction, `unclear` is a shrug.

    An agent once declined `state_dependent` for a claim whose sign depends on cortical
    layer, because the vocabulary said "physiological state" — correct under the wording,
    but the result was that "we know it varies and we know what with" was recorded
    identically to "we do not know".
    """
    out: list[Violation] = []
    for claim_id, record in ctx.claims.items():
        direction = record.raw.get("direction")
        context = str(record.raw.get("direction_context") or "").strip()
        if direction == "state_dependent" and not context:
            out.append(
                error(
                    "V-DIR",
                    f"{record.path}#/direction_context",
                    "direction is state_dependent but direction_context is empty. Name "
                    "what the sign depends on — physiological state, cell subpopulation, "
                    "cortical layer, compartment or task condition. If the dependency is "
                    "genuinely unknown, `unclear` is the honest value.",
                    record_id=claim_id,
                )
            )
        elif direction != "state_dependent" and context:
            out.append(
                error(
                    "V-DIR",
                    f"{record.path}#/direction_context",
                    f"direction_context is set but direction is {direction!r}; the field "
                    "names the dependency that makes a sign state-dependent.",
                    record_id=claim_id,
                )
            )
    return out


# ==================================================== V17: compiled edge provenance ===

@rule("V17", "Compiled graph edges carry a provenance_class and, when claim_derived, resolvable claims.")
def check_edge_provenance(ctx: ValidationContext) -> list[Violation]:
    """PARTIAL in Phase 1: the compiled graph arrives in Phase 2.

    What is checkable now is every edge-shaped record that already exists — the
    definitional axioms in ``ontology/definitional_edges.yaml`` — plus the consistency
    of each relation's declared ``allowed_provenance_classes``.
    """
    out: list[Violation] = []
    declared = set(ctx.onto.provenance_classes)
    for record in ctx.repo.definitional_edges:
        raw = record.raw
        locator = record.path
        provenance_class = raw.get("provenance_class")
        if provenance_class not in declared:
            out.append(
                error("V17", f"{locator}#/provenance_class",
                      f"provenance_class {provenance_class!r} is not one of {sorted(declared)} "
                      "(rule V17).")
            )
            continue
        predicate = raw.get("predicate")
        if not isinstance(predicate, str) or predicate not in ctx.onto.edges:
            continue
        allowed = set(ctx.onto.allowed_provenance_classes(predicate))
        if provenance_class not in allowed:
            out.append(
                error(
                    "V17",
                    f"{locator}#/provenance_class",
                    f"relation {predicate} may only carry {sorted(allowed)} but this edge "
                    f"is {provenance_class!r} (ontology/edges.yaml). An empirical relation "
                    "cannot be introduced as an axiom.",
                )
            )
        if provenance_class == "claim_derived":
            refs = [str(c) for c in (raw.get("claim_refs") or [])]
            missing = [c for c in refs if c not in ctx.claims]
            if not refs:
                out.append(
                    error("V17", locator,
                          f"claim_derived edge {raw.get('subject')} -{predicate}-> "
                          f"{raw.get('object')} cites no claim (rule V17).")
                )
            for claim_id in missing:
                out.append(
                    error("V17", locator,
                          f"claim_derived edge cites {claim_id}, which does not resolve "
                          "(rules V4, V17).", record_id=claim_id)
                )
    return out


# ================================================================== V18: secrets ===

# Credential markers, as ANCHORED patterns. Substring matching was tried first and
# flagged "secreted protein" for containing "secret"; a rule that cries wolf is a rule
# agents learn to ignore, so every marker here is word-bounded.
_SECRET_MARKERS: tuple[tuple[str, str], ...] = (
    (r"\bapi[_-]?keys?\b", "an API key field"),
    (r"\bsecrets?\b(?!ase|ed|ing|ion|ory)", "a secret field"),
    (r"\bbearer\s+[A-Za-z0-9._~+/-]{16,}", "a bearer token"),
    (r"\bncbi_api_key\b", "the NCBI API key"),
    (r"\balphagenome_api_key\b", "the AlphaGenome API key"),
    (r"\baws_(?:access|secret)_key\b", "an AWS key"),
    (r"\bprivate_key\b", "a private key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a PEM private-key block"),
    (r"\bgh[pousr]_[A-Za-z0-9]{16,}", "a GitHub token"),
    (r"\bsk-[A-Za-z0-9]{20,}", "an API secret key"),
)
_SECRET_RES: tuple[tuple[Any, str], ...] = ()


@rule("V18", "No secrets: no API keys, tokens or .env content in any curated record.")
def check_no_secrets(ctx: ValidationContext) -> list[Violation]:
    """Scan curated record text for credential markers.

    Scoped to curated records rather than the whole tree: the repository's own
    ``.gitignore`` and the pre-commit hook cover untracked files, and scanning
    ``data/raw/`` would be both slow and outside this rule's purpose.
    """
    out: list[Violation] = []
    groups: list[list[loaders.LoadedRecord]] = [
        list(ctx.sources.values()),
        list(ctx.claims.values()),
        list(ctx.repo.targets.values()),
        ctx.repo.assessments,
        list(ctx.repo.audits.values()),
        list(ctx.repo.interventions.values()),
        ctx.repo.state_variable_annotations,
    ]
    import re as _re

    compiled = [(_re.compile(pattern, _re.IGNORECASE), what) for pattern, what in _SECRET_MARKERS]
    for items in groups:
        for item in items:
            for pointer, text in policy.iter_strings(item.raw):
                for pattern, what in compiled:
                    match = pattern.search(text)
                    if match is None:
                        continue
                    out.append(
                        error(
                            "V18",
                            f"{item.path}#{pointer}",
                            f"text looks like it contains {what} (matched "
                            f"{match.group(0)[:24]!r}). No credential may ever enter a "
                            "tracked file (rule V18); keys are read from the environment "
                            "and never persisted.",
                            record_id=item.record_id,
                        )
                    )
                    break
    return out


# ============================================================= V19: raw immutability ===

@rule("V19", "data/raw/ checksums match MANIFEST.jsonl (immutability).")
def check_raw_immutability(ctx: ValidationContext) -> list[Violation]:
    """Snapshots are immutable: a changed byte breaks offline reproducibility (P7)."""
    import hashlib
    import json as _json

    out: list[Violation] = []
    manifest = paths.raw_manifest(ctx.root)
    if not manifest.is_file():
        if paths.raw_dir(ctx.root).is_dir() and any(paths.raw_dir(ctx.root).glob("*/*/*")):
            out.append(
                error("V19", "data/raw/MANIFEST.jsonl",
                      "snapshots exist under data/raw/ but there is no manifest, so their "
                      "immutability cannot be checked (contract P7, rule V19).")
            )
        return out
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = _json.loads(line)
        except _json.JSONDecodeError as exc:
            out.append(
                error("V19", f"data/raw/MANIFEST.jsonl:{number}", f"not valid JSON: {exc}")
            )
            continue
        relative = str(entry.get("path", ""))
        path = ctx.root / relative
        if not path.is_file():
            out.append(
                error("V19", relative,
                      "listed in MANIFEST.jsonl but missing from the working tree. Raw "
                      "snapshots are append-only and never deleted (contract P7).")
            )
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            out.append(
                error(
                    "V19",
                    relative,
                    f"sha256 is {digest[:16]}... but MANIFEST.jsonl records "
                    f"{str(entry.get('sha256'))[:16]}.... A raw snapshot has been "
                    "modified; derived artefacts are no longer reproducible from it "
                    "(contract P7, rule V19).",
                )
            )
    return out


# ============================================================ V20: prohibited work ===

@rule("V20", "No record proposes wet-lab, in-vitro, ex-vivo, animal or human experimentation.")
def check_prohibited_work(ctx: ValidationContext) -> list[Violation]:
    """Contract P1 and the computational-only policy, applied to every record."""
    out: list[Violation] = []
    groups: list[list[loaders.LoadedRecord]] = [
        list(ctx.sources.values()),
        list(ctx.claims.values()),
        list(ctx.repo.targets.values()),
        ctx.repo.assessments,
        list(ctx.repo.audits.values()),
        list(ctx.repo.interventions.values()),
        ctx.repo.state_variable_annotations,
        list(ctx.repo.state_variables.values()),
    ]
    for items in groups:
        for item in items:
            out.extend(
                policy.check_record(
                    item.raw, path=item.path, record_id=item.record_id, root=ctx.root
                )
            )
    return out


# ===================================================== V21: human-proposition facets ===

@rule("V21", "A level 3-4 on a human-proposition facet requires a human-evidence claim reference.")
def check_human_proposition_facets(ctx: ValidationContext) -> list[Violation]:
    """Contract §5.3, added by the amendment to §5.2/§5.3.

    ``human_genetic_association``, ``human_phenotype_specificity``,
    ``human_intervention_evidence`` and ``adult_expression_and_timing`` make claims about
    humans. A substantial or strong grade on one of them must cite at least one claim
    whose ``translation.human_relevance`` is human evidence — otherwise the grade rests
    on animal or in-vitro work and says something the evidence does not.
    """
    out: list[Violation] = []
    human_facets = set(vocab.subset("facet", "human_proposition_facets", ctx.root))
    human_values = vocab.human_evidence_values(ctx.root)
    threshold = vocab.meta("evidence_strength_v1", "human_evidence_required_at_or_above", ctx.root)
    threshold = threshold if isinstance(threshold, int) else 3

    for record in ctx.repo.assessments:
        for index, facet in enumerate(record.raw.get("facets") or []):
            if not isinstance(facet, dict):
                continue
            name = str(facet.get("facet"))
            level = facet.get("level")
            if name not in human_facets or not isinstance(level, int) or isinstance(level, bool):
                continue
            if level < threshold:
                continue
            refs = [str(c) for c in (facet.get("claim_refs") or [])]
            found: list[str] = []
            unresolved: list[str] = []
            for claim_id in refs:
                claim = ctx.claim_of(claim_id)
                if claim is None:
                    unresolved.append(claim_id)
                    continue
                relevance = (claim.get("translation") or {}).get("human_relevance")
                if relevance in human_values:
                    found.append(claim_id)
            if found:
                continue
            detail = (
                f"cited claims: {refs}" if refs else "no claims are cited at all"
            )
            if unresolved:
                detail += f"; unresolved: {unresolved}"
            out.append(
                error(
                    "V21",
                    f"{record.path}#/facets/{index}",
                    f"facet {name!r} is graded level {level}, but its proposition is about "
                    f"HUMANS and no cited claim carries "
                    f"translation.human_relevance in {sorted(human_values)} ({detail}). "
                    f"Levels {threshold}+ on a human-proposition facet require human "
                    "evidence (contract §5.3, rule V21). Grade it lower, or cite the "
                    "human claim.",
                    record_id=record.record_id,
                    context={"facet": name, "level": level},
                )
            )
    return out


# ============== V-DIR2: `no_change` means MEASURED and no change was found =========

@rule("V-DIR2", "direction: no_change must be a MEASURED null, and never on a directionless claim.")
def check_measured_null_direction(ctx: ValidationContext) -> list[Violation]:
    """`no_change` is a finding. Two ways a record can misuse it, both checked.

    1. **Nothing was measured.** `no_change` means MEASURED AND NO CHANGE WAS FOUND, so
       at least one evidence item must report `endpoint_measured: measured`. Without
       that, a record nobody measured reads as a measured null.
    2. **The claim asserts no direction at all.** An `expression` claim says a gene is
       expressed somewhere; a `theoretical_construct` defines a notion; a
       `methodological` claim is about a method. None of them has a sign. Here the
       endpoint genuinely WAS measured — expression was measured in a tissue — so limb 1
       passes and the record still says the wrong thing: `no_change` claims a null result
       the study never reported. `direction: not_applicable` is the value for this.

    Reported as WARNINGS and deliberately so. The affected records are in finished
    atlases, and re-opening three of them to correct a latent misread is a worse use of
    the remaining sprint than finishing the ranking. A warning keeps the debt in front of
    anyone who runs the validator instead of buried in a summary — which is the whole
    difference between tracked debt and an unrecorded defect.

    This is the FIFTH place in one sprint where a "we looked and found nothing" value was
    pressed into service for "there was nothing to look for" (after V16c, R11, R14 and
    the state-variable annotation checks). The recurrence is the finding; the rule is
    only the fix.
    """
    out: list[Violation] = []
    measured_nulls = set(vocab.subset("direction", "measured_null_values", ctx.root))
    measured = set(vocab.subset("endpoint_measured", "measured_values", ctx.root))
    directionless = set(vocab.meta("direction", "directionless_claim_types", ctx.root) or [])
    if not measured_nulls:
        return out

    unmeasured: list[tuple[str, str, str]] = []
    directionless_hits: list[tuple[str, str, str]] = []
    for claim_id, record in ctx.claims.items():
        raw = record.raw
        if raw.get("direction") not in measured_nulls:
            continue
        claim_type = str(raw.get("claim_type"))
        items = [i for i in (raw.get("evidence") or []) if isinstance(i, dict)]
        any_measured = any(
            str(i.get("endpoint_measured", "unknown")) in measured for i in items
        )
        if claim_type in directionless:
            directionless_hits.append((claim_id, record.path, claim_type))
        elif not any_measured:
            unmeasured.append((claim_id, record.path, claim_type))

    total = len(unmeasured) + len(directionless_hits)

    for claim_id, path, claim_type in directionless_hits:
        out.append(
            warning(
                "V-DIR2",
                f"{path}#/direction",
                f"direction is `no_change` on a {claim_type} claim, which asserts NO "
                "DIRECTION AT ALL. `no_change` means measured and no change was found, so "
                "this record claims a null result the study never reported — the same "
                "conflation rule V16c prevents one level up, one level down. Set "
                "`direction: not_applicable`. TRACKED DEBT: "
                f"{len(directionless_hits)} directionless claim(s) are in this state "
                f"({total} V-DIR2 findings in total); they are a latent misread rather "
                "than a wrong fact, and are warnings so finished atlases are not "
                "re-opened mid-sprint.",
                record_id=claim_id,
                context={
                    "claim_type": claim_type,
                    "reason": "directionless_claim_type",
                    "affected_total": total,
                },
            )
        )

    for claim_id, path, claim_type in unmeasured:
        out.append(
            warning(
                "V-DIR2",
                f"{path}#/direction",
                f"direction is `no_change` but no evidence item reports "
                f"endpoint_measured in {sorted(measured)}. `no_change` means MEASURED AND "
                "NO CHANGE WAS FOUND; without a measured endpoint this reads as a "
                "measured null that nobody performed. Either add the evidence item that "
                "found no change, or use `unclear` if a direction exists and is unknown. "
                f"TRACKED DEBT: {total} V-DIR2 finding(s) repository-wide.",
                record_id=claim_id,
                context={
                    "claim_type": claim_type,
                    "reason": "no_measured_endpoint",
                    "affected_total": total,
                },
            )
        )
    return out


# ================================ V-EXT: unverified external analysis stays inert ===

@rule(
    "V-EXT",
    "An unverified external analysis may not be cited as evidence by any record.",
)
def check_external_analysis_inertness(ctx: ValidationContext) -> list[Violation]:
    """Keep an unverified external result out of the evidence chain, mechanically.

    An external agent's analysis whose only record is prose has no artefact to check, so
    it cannot fail a check — which is exactly why it must not be citable. If a claim
    could name ``ANALYSIS:X01`` as its evidence, a number transcribed from a task
    description would acquire the authority of a measured result, and this repository's
    provenance guarantees would stop meaning anything at the point where an external
    collaborator is involved.

    Verified external analyses are unaffected: once checksums recompute and schemas
    validate, ``external_analysis_verified`` is an evidential provenance class like any
    other.
    """
    violations: list[Violation] = []
    unverified = {
        analysis_id: record
        for analysis_id, record in ctx.repo.external_analyses.items()
        if record.raw.get("verification_status") != "verified"
    }
    if not unverified:
        return violations

    def _cites(value: object) -> set[str]:
        if isinstance(value, str):
            return {value} & unverified.keys()
        if isinstance(value, list):
            found: set[str] = set()
            for item in value:
                found |= _cites(item)
            return found
        return set()

    # Claims: no evidence item, no provenance field, may reach an unverified analysis.
    for claim_id, record in ctx.claims.items():
        hits: set[str] = set()
        for item in record.raw.get("evidence") or []:
            if isinstance(item, dict):
                hits |= _cites(item.get("source_id"))
                hits |= _cites(item.get("analysis_id"))
        hits |= _cites((record.raw.get("provenance") or {}).get("analysis_id"))
        for analysis_id in sorted(hits):
            violations.append(
                Violation(
                    "V-EXT",
                    "error",
                    f"{record.path}#/{claim_id}",
                    f"claim cites {analysis_id}, whose verification_status is "
                    f"'{unverified[analysis_id].raw.get('verification_status')}'. An "
                    "external analysis known only from prose has no artefact to verify "
                    "and cannot fail a check, so it may not support a claim (contract "
                    "P2). Record it in analyses/external/ and leave it inert until the "
                    "artefacts in its outstanding_artefacts list arrive.",
                    record_id=claim_id,
                )
            )

    # Facet assessments: neither claim_refs nor source_refs may reach one.
    for record in ctx.repo.assessments:
        for index, facet in enumerate(record.raw.get("facets") or []):
            if not isinstance(facet, dict):
                continue
            hits = _cites(facet.get("claim_refs")) | _cites(facet.get("source_refs"))
            hits |= _cites(facet.get("counter_claim_refs"))
            for analysis_id in sorted(hits):
                violations.append(
                    Violation(
                        "V-EXT",
                        "error",
                        f"{record.path}#/facets/{index}",
                        f"facet '{facet.get('facet')}' cites {analysis_id}, an "
                        "unverified external analysis. A facet level may not rest on a "
                        "figure that has no artefact behind it; that is what "
                        "verification_status exists to prevent.",
                        record_id=record.record_id,
                    )
                )

    # Self-consistency of the record itself.
    for analysis_id, record in unverified.items():
        for index, result in enumerate(record.raw.get("reported_results") or []):
            if isinstance(result, dict) and (result.get("claim_refs") or []):
                violations.append(
                    Violation(
                        "V-EXT",
                        "error",
                        f"{record.path}#/reported_results/{index}",
                        f"{analysis_id} is unverified but its reported result "
                        f"'{result.get('result_id')}' names claim_refs. An unverified "
                        "result may not license a claim in either direction.",
                        record_id=analysis_id,
                    )
                )
        if record.raw.get("provenance_class") != "external_analysis_unverified":
            violations.append(
                Violation(
                    "V-EXT",
                    "error",
                    f"{record.path}#/provenance_class",
                    f"{analysis_id} has verification_status "
                    f"'{record.raw.get('verification_status')}' but provenance_class "
                    f"'{record.raw.get('provenance_class')}'. Anything short of "
                    "verified must carry external_analysis_unverified, which is "
                    "excluded from the vocabulary's evidential_classes and is therefore "
                    "what keeps the graph compiler and the ranking model from reading "
                    "it as support.",
                    record_id=analysis_id,
                )
            )
    return violations


# ======================================= V22: sources registered but never cited ===

@rule("V22", "Sources registered but cited by no claim (informational).")
def check_uncited_sources(ctx: ValidationContext) -> list[Violation]:
    """Surface registered-but-uncited sources. INFORMATIONAL, never a failure.

    A registered source implies somebody thought it mattered, so an uncited one is
    either a leftover from a dropped claim or a claim that was meant to exist. Both are
    worth seeing. Neither is a defect: registering a source before writing the claim is
    a legitimate working order, which is why this never escalates under ``--strict``.
    """
    cited: set[str] = set()
    for record in ctx.claims.values():
        for item in record.raw.get("evidence") or []:
            if isinstance(item, dict) and isinstance(item.get("source_id"), str):
                cited.add(item["source_id"])
        provenance = record.raw.get("provenance") or {}
        if isinstance(provenance.get("database_release"), str):
            cited.add(provenance["database_release"])
    for record in ctx.repo.assessments:
        for facet in record.raw.get("facets") or []:
            if isinstance(facet, dict):
                cited.update(c for c in (facet.get("source_refs") or []) if isinstance(c, str))
    for record in ctx.repo.interventions.values():
        approval = record.raw.get("approval_status") or {}
        if isinstance(approval.get("source_id"), str):
            cited.add(approval["source_id"])
        if isinstance(record.raw.get("database_source_id"), str):
            cited.add(record.raw["database_source_id"])

    # Attribution is PER REGISTERING FILE, not per indexed record. Duplicate
    # registration across agents is allowed (contract §1.3), so one source_id can be
    # registered in several files; the loader keeps one record per id, and reading
    # `added_by` off that survivor attributed a shared uncited source to whichever agent
    # happened to sort first while telling the other nothing. An agent can only edit its
    # own file, so it has to be told about its own registration.
    by_file: dict[str, list[str]] = {}
    for source_id, record in ctx.sources.items():
        if source_id in cited:
            continue
        files = ctx.repo.shared_sources.get(source_id) or (record.path.split("#", 1)[0],)
        for owning_file in files:
            by_file.setdefault(owning_file, []).append(source_id)

    return [
        info(
            "V22",
            owning_file,
            f"{len(source_ids)} source(s) registered in {owning_file} are cited by no "
            f"claim, assessment or intervention: {sorted(source_ids)}. Either a claim was "
            "dropped and left its source behind, or a claim was meant to exist. Neither "
            "is an error — registering before curating is a legitimate order of work. "
            "Reported per FILE because a source registered by two agents (which the "
            "contract prefers) must be reported to both: each can only edit its own.",
            record_id=owning_file,
        )
        for owning_file, source_ids in sorted(by_file.items())
    ]


# =============================== V23: animal harm must not wear a clinical label ===

@rule("V23", "clinical_harm requires human evidence; non-human harm is preclinical_harm.")
def check_harm_labelling(ctx: ValidationContext) -> list[Violation]:
    """R13: ``clinical_harm`` is reserved for harm observed in humans.

    An agent had to record increased seizure susceptibility in MICE as ``clinical_harm``
    because nothing else fitted, and flagged the forced label itself. This is the
    laundering direction contract P4 exists to block, and the one easiest to let slide
    because over-stating a harm feels like the safe error. It is not: a graph in which
    animal harm reads as clinical harm misprices every safety constraint that rests on it.
    """
    out: list[Violation] = []
    human_values = vocab.human_evidence_values(ctx.root)
    human_taxon = "SPECIES:NCBITaxon:9606"
    for claim_id, record in ctx.claims.items():
        if record.raw.get("claim_type") != "clinical_harm":
            continue
        translation = record.raw.get("translation") or {}
        if translation.get("human_relevance") in human_values:
            continue
        context = record.raw.get("context") or {}
        species = [s for s in (context.get("species") or []) if isinstance(s, str)]
        item_species = [
            item.get("species")
            for item in (record.raw.get("evidence") or [])
            if isinstance(item, dict) and isinstance(item.get("species"), str)
        ]
        all_species = species + item_species
        if human_taxon in all_species:
            continue
        out.append(
            error(
                "V23",
                f"{record.path}#/claim_type",
                f"claim_type is clinical_harm but no evidence is human: species "
                f"{sorted(set(all_species)) or 'none recorded'}, "
                f"translation.human_relevance "
                f"{translation.get('human_relevance')!r}. `clinical_harm` is reserved for "
                "harm observed IN HUMANS; harm in a non-human model is "
                "`preclinical_harm`. Animal evidence wearing a clinical label is the "
                "laundering direction contract P4 blocks, and over-stating a harm is not "
                "the safe error — it misprices every safety constraint that rests on it.",
                record_id=claim_id,
            )
        )
    return out


# ======================================================= ONT*: ontology self-checks ===

@rule("ONT1", "The ontology and the JSON Schema enums agree (no vocabulary drift).")
def check_schema_vocabulary_drift(ctx: ValidationContext) -> list[Violation]:
    """A drifted enum silently disables whichever rule depends on it."""
    from blueprint import sync_schema_enums

    return [
        error("ONT1", "schemas/", problem)
        for problem in sync_schema_enums.check(ctx.root)
    ]


@rule("ONT2", "State-variable definitions conform to the type system and assert no dynamics.")
def check_state_variable_types(ctx: ValidationContext) -> list[Violation]:
    """Defends the "no invented dose-response curves" rule at validation time."""
    out: list[Violation] = []
    declared_domains = set(vocab.values("state_domain", ctx.root))
    seen_domains: set[str] = set()
    for sv_id, record in ctx.repo.state_variables.items():
        raw = record.raw
        domain = sv_id.split(":", 1)[1].split(".", 1)[0] if ":" in sv_id else ""
        seen_domains.add(domain)
        if domain not in declared_domains:
            out.append(
                error("ONT2", f"{record.path}#/id",
                      f"{sv_id} is in domain {domain!r}, which is not one of "
                      f"{sorted(declared_domains)}.", record_id=sv_id)
            )
        shape = raw.get("response_shape") or {}
        if shape.get("basis") == "default_no_evidence_yet" and shape.get("shape") != "unknown":
            out.append(
                error(
                    "ONT2",
                    f"{record.path}#/response_shape",
                    f"{sv_id} declares shape {shape.get('shape')!r} with basis "
                    "default_no_evidence_yet. A response shape other than `unknown` is an "
                    "empirical claim and needs basis `claim_supported` with claim_refs, or "
                    "`definitional` (README §3). MAXIMISING IS NOT ASSUMED TO BE GOOD.",
                    record_id=sv_id,
                )
            )
        if shape.get("basis") == "claim_supported" and not (shape.get("claim_refs") or []):
            out.append(
                error("ONT2", f"{record.path}#/response_shape/claim_refs",
                      f"{sv_id} claims a claim-supported response shape but cites no "
                      "claim (contract P2).", record_id=sv_id)
            )
        if raw.get("safety_coupling_basis") == "not_asserted_pending_claims" and (
            raw.get("safety_coupling") or []
        ):
            out.append(
                error("ONT2", f"{record.path}#/safety_coupling",
                      f"{sv_id} lists safety couplings with basis "
                      "not_asserted_pending_claims; assert a coupling through an "
                      "annotation with claim refs, not in the definition.",
                      record_id=sv_id)
            )
        if domain in {"safety", "stability"}:
            polarity = raw.get("polarity")
            name = sv_id.rsplit(".", 1)[-1]
            if polarity not in {"risk", "margin"}:
                out.append(
                    error("ONT2", f"{record.path}#/polarity",
                          f"{sv_id} is a {domain} variable and must declare "
                          "polarity: risk | margin. `direction: increases` means OPPOSITE "
                          "things against a threshold and against a risk, and an "
                          "annotation read against the wrong polarity is silently "
                          "inverted (R4).", record_id=sv_id)
                )
            elif name.endswith("_margin") and polarity != "margin":
                out.append(
                    error("ONT2", f"{record.path}#/polarity",
                          f"{sv_id} is named `..._margin` but declares polarity "
                          f"{polarity!r}; a margin is headroom, so a higher value is "
                          "less harm.", record_id=sv_id)
                )
            elif name.endswith(("_risk", "_burden")) and polarity != "risk":
                out.append(
                    error("ONT2", f"{record.path}#/polarity",
                          f"{sv_id} is named `..._{name.rsplit('_', 1)[-1]}` but declares "
                          f"polarity {polarity!r}; a risk is harm, so a higher value is "
                          "worse.", record_id=sv_id)
                )
        elif raw.get("polarity") is not None:
            out.append(
                error("ONT2", f"{record.path}#/polarity",
                      f"{sv_id} declares polarity {raw['polarity']!r}, but only safety and "
                      "stability variables have a risk/margin reading.", record_id=sv_id)
            )
        if domain == "safety":
            if raw.get("kind") != "constraint":
                out.append(
                    error("ONT2", f"{record.path}#/kind",
                          f"{sv_id} is a safety variable but kind is {raw.get('kind')!r}; "
                          "safety variables are constraints (README §3).", record_id=sv_id)
                )
            # A MARGIN in the safety domain is headroom, and more headroom is better
            # within a range nobody has established (R3). It is still a constraint: it
            # bounds the admissible region rather than being an objective.
            allowed_desirability = (
                {"higher_is_better_within_range", "constraint_to_respect"}
                if raw.get("polarity") == "margin"
                else {"constraint_to_respect"}
            )
            if raw.get("desirability") not in allowed_desirability:
                out.append(
                    error("ONT2", f"{record.path}#/desirability",
                          f"{sv_id} is a safety variable with polarity "
                          f"{raw.get('polarity')!r} but desirability is "
                          f"{raw.get('desirability')!r}; allowed: "
                          f"{sorted(allowed_desirability)}. A RISK must be "
                          "constraint_to_respect so no aggregation can trade it against "
                          "a benefit.",
                          record_id=sv_id)
                )
    if ctx.repo.state_variables:
        missing = sorted(declared_domains - seen_domains)
        for domain in missing:
            out.append(
                error("ONT2", "state_model/",
                      f"state domain {domain!r} is declared in "
                      "ontology/state_variables.yaml but has no variables; the state "
                      f"model would be missing a whole domain.")
            )
    return out


# ============================================================== the run itself ===

@dataclass
class ValidationReport:
    """The outcome of one validation run."""

    root: Path
    violations: list[Violation]
    counts: dict[str, int]
    verification_summary: dict[str, int]
    rules_run: tuple[str, ...]
    strict: bool

    @property
    def errors(self) -> list[Violation]:
        """Violations that fail the run.

        ``--strict`` escalates warnings, never ``info``: an informational finding is not
        a defect in any state of the repository, so escalating it would make the gate
        fire on a repository that is merely incomplete.
        """
        if self.strict:
            return [v for v in self.violations if v.severity in {"error", "warning"}]
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "warning"]

    @property
    def infos(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "info"]

    @property
    def ok(self) -> bool:
        """Whether the run passes."""
        return not self.errors

    def by_rule(self) -> dict[str, list[Violation]]:
        """Violations grouped by rule id, each group sorted deterministically."""
        grouped: dict[str, list[Violation]] = {}
        for violation in self.violations:
            grouped.setdefault(violation.rule, []).append(violation)
        return {rule_id: sorted(items) for rule_id, items in sorted(grouped.items())}

    def as_dict(self) -> dict[str, Any]:
        """Machine-readable report for ``--json``."""
        return {
            "ok": self.ok,
            "strict": self.strict,
            "root": str(self.root),
            "counts": self.counts,
            "verification": self.verification_summary,
            "rules_run": list(self.rules_run),
            "totals": {
                "violations": len(self.violations),
                "errors": len([v for v in self.violations if v.severity == "error"]),
                "warnings": len(self.warnings),
                "info": len(self.infos),
                "failing": len(self.errors),
            },
            "by_rule": {
                rule_id: {
                    "description": REGISTRY[rule_id][1] if rule_id in REGISTRY else "",
                    "count": len(items),
                    "violations": [v.as_dict() for v in items],
                }
                for rule_id, items in self.by_rule().items()
            },
        }


def run(
    root: Path | str | None = None,
    *,
    strict: bool = False,
    only: tuple[str, ...] | None = None,
) -> ValidationReport:
    """Run every registered rule over the repository at ``root``.

    ``only`` restricts the run to the named rule ids, which is how the tests exercise
    one rule at a time. A rule that raises is reported as a violation against itself
    rather than aborting the run.
    """
    ctx = build_context(root)
    selected = [
        rule_id for rule_id in sorted(REGISTRY) if only is None or rule_id in only
    ]
    # Violations raised while LOADING (unreadable YAML, a duplicate id, a model
    # rejection) already name the rule they break, so they are contributed here under
    # their own rule id rather than from inside whichever rule function happens to run.
    violations: list[Violation] = [
        violation
        for violation in ctx.repo.violations
        if only is None or violation.rule in only
    ]
    for rule_id in selected:
        function, _ = REGISTRY[rule_id]
        try:
            violations.extend(function(ctx))
        except Exception as exc:  # noqa: BLE001 - a rule must never abort the run
            violations.append(
                error(
                    rule_id,
                    "blueprint/validate.py",
                    f"rule {rule_id} raised {type(exc).__name__}: {exc}. This is a "
                    "validator bug, not a record problem; report it rather than editing "
                    "records to work around it.",
                )
            )
    return ValidationReport(
        root=ctx.root,
        violations=sorted(violations),
        counts=ctx.repo.counts(),
        verification_summary=ctx.verification.summary(),
        rules_run=tuple(selected),
        strict=strict,
    )


def rule_catalogue() -> dict[str, str]:
    """Rule id -> description, for the CLI's ``--list-rules`` and for the handoff."""
    return {rule_id: REGISTRY[rule_id][1] for rule_id in sorted(REGISTRY)}
