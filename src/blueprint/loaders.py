"""Load every curated record in the repository into typed collections.

Design rules:

* **An empty repository is valid.** Sprint 1 starts with zero records. Every loader
  returns an empty collection; none raises for a missing directory or file. The
  alternative — a build that fails until records exist — pressures agents into writing
  records to make it pass, which is the opposite of what the contract wants.
* **Both forms are kept.** Each loaded record carries its RAW mapping (what JSON Schema
  rule V1 validates) and, when it parses, its PYDANTIC MODEL (what the semantic rules
  use). A record that fails to parse still contributes its raw form, so V1 can report
  the real schema error instead of a Python traceback.
* **Loading never throws.** Unreadable YAML, a wrong top-level shape, a duplicate id and
  a model-validation failure are all VIOLATIONS attached to the collection. The
  validator reports them with everything else.
* **Deterministic.** Files are visited in sorted order and every mapping is returned in
  sorted key order, so two runs produce identical reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from blueprint import paths, records
from blueprint.violations import Violation, error


@dataclass(frozen=True)
class LoadedRecord:
    """One record, in both raw and parsed form, with where it came from."""

    kind: str
    raw: dict[str, Any]
    path: str
    record_id: str | None = None
    model: BaseModel | None = None

    @property
    def parsed(self) -> bool:
        """Whether the record satisfied its pydantic model."""
        return self.model is not None


@dataclass
class Repository:
    """Every curated record in one repository root, plus loading violations."""

    root: Path
    sources: dict[str, LoadedRecord] = field(default_factory=dict)
    claims: dict[str, LoadedRecord] = field(default_factory=dict)
    targets: dict[str, LoadedRecord] = field(default_factory=dict)
    assessments: list[LoadedRecord] = field(default_factory=list)
    audits: dict[str, LoadedRecord] = field(default_factory=dict)
    interventions: dict[str, LoadedRecord] = field(default_factory=dict)
    state_variables: dict[str, LoadedRecord] = field(default_factory=dict)
    state_variable_annotations: list[LoadedRecord] = field(default_factory=list)
    definitional_edges: list[LoadedRecord] = field(default_factory=list)
    external_analyses: dict[str, LoadedRecord] = field(default_factory=dict)
    seed_registry: dict[str, Any] = field(default_factory=dict)
    lock_claim_ids: tuple[str, ...] = ()
    shared_sources: dict[str, tuple[str, ...]] = field(default_factory=dict)
    violations: list[Violation] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        """Record counts, for the validator's summary line."""
        return {
            "sources": len(self.sources),
            "claims": len(self.claims),
            "evidence_items": sum(
                len(r.raw.get("evidence") or []) for r in self.claims.values()
            ),
            "targets": len(self.targets),
            "external_analyses": len(self.external_analyses),
            "assessments": len(self.assessments),
            "audits": len(self.audits),
            "interventions": len(self.interventions),
            "state_variables": len(self.state_variables),
            "state_variable_annotations": len(self.state_variable_annotations),
            "definitional_edges": len(self.definitional_edges),
            "seed_targets": len(self.seed_registry.get("targets") or []),
            "locked_claim_ids": len(self.lock_claim_ids),
            "shared_sources": len(self.shared_sources),
        }

    def is_empty(self) -> bool:
        """Whether the repository holds no curated evidence records at all."""
        return not (self.sources or self.claims or self.targets or self.audits)

    def relative(self, path: Path) -> str:
        """A repository-relative string for ``path``, for violation locators."""
        try:
            return str(path.relative_to(self.root))
        except ValueError:  # pragma: no cover - path outside the root
            return str(path)


def _read_yaml(path: Path, collected: list[Violation], root: Path) -> Any:
    """Read one YAML file, reporting a parse failure instead of raising."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        try:
            locator = str(path.relative_to(root))
        except ValueError:  # pragma: no cover
            locator = str(path)
        collected.append(
            error("V1", locator, f"could not be read as YAML: {exc}")
        )
        return None


def _parse(
    kind: str,
    raw: Any,
    locator: str,
    id_field: str | None,
    collected: list[Violation],
) -> LoadedRecord | None:
    """Build a :class:`LoadedRecord`, reporting a non-mapping or a model failure."""
    if not isinstance(raw, dict):
        collected.append(
            error(
                "V1",
                locator,
                f"expected a mapping for a {kind} record, got {type(raw).__name__}. "
                "Source, claim, audit and annotation files are YAML LISTS of mappings; "
                "target, assessment and intervention files are single YAML documents "
                "(contract §2).",
            )
        )
        return None
    record_id = raw.get(id_field) if id_field else None
    record_id = str(record_id) if record_id is not None else None
    model: BaseModel | None = None
    model_class = records.MODEL_FOR_KIND.get(kind)
    if model_class is not None:
        try:
            model = model_class(**raw)
        except ValidationError as exc:
            for detail in exc.errors():
                pointer = "/" + "/".join(str(part) for part in detail["loc"])
                collected.append(
                    error(
                        "V1",
                        f"{locator}#{pointer}",
                        detail["msg"],
                        record_id=record_id,
                        context={"kind": kind, "type": detail["type"]},
                    )
                )
    return LoadedRecord(
        kind=kind,
        raw={k: raw[k] for k in sorted(raw)},
        path=locator,
        record_id=record_id,
        model=model,
    )


def _load_list_files(
    files: list[Path],
    kind: str,
    id_field: str,
    root: Path,
    collected: list[Violation],
) -> list[LoadedRecord]:
    """Load every record from files that each hold a YAML list of mappings."""
    out: list[LoadedRecord] = []
    for path in files:
        locator = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        document = _read_yaml(path, collected, root)
        if document is None:
            continue
        if isinstance(document, dict):
            # Tolerate a wrapper mapping with a single list under a plural key, since
            # that is a natural mistake; report it so the shape gets fixed.
            candidates = [v for v in document.values() if isinstance(v, list)]
            if len(candidates) == 1:
                collected.append(
                    error(
                        "V1",
                        locator,
                        f"a {kind} file is a YAML LIST of records at the top level "
                        "(contract §2); this file wraps the list in a mapping",
                    )
                )
                document = candidates[0]
            else:
                document = [document]
        if not isinstance(document, list):
            collected.append(
                error("V1", locator, f"expected a YAML list of {kind} records")
            )
            continue
        for index, raw in enumerate(document):
            item_locator = f"{locator}#/{index}"
            loaded = _parse(kind, raw, item_locator, id_field, collected)
            if loaded is not None:
                out.append(loaded)
    return out


def _load_document_files(
    files: list[Path],
    kind: str,
    id_field: str | None,
    root: Path,
    collected: list[Violation],
) -> list[LoadedRecord]:
    """Load every record from files that each hold one YAML document."""
    out: list[LoadedRecord] = []
    for path in files:
        locator = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        document = _read_yaml(path, collected, root)
        if document is None:
            continue
        loaded = _parse(kind, document, locator, id_field, collected)
        if loaded is not None:
            out.append(loaded)
    return out


def _load_annotation_files(
    root: Path, collected: list[Violation]
) -> list[LoadedRecord]:
    """Load state-variable annotations, accepting both file shapes in use.

    An annotation file is either a bare YAML list of annotations, or a mapping with an
    ``annotations`` list plus file-level metadata (``run_id``, ``annotation_scope``,
    ``coverage_summary``). Both are legitimate and both are in the repository, so both
    are read rather than one being reported as an error.
    """
    out: list[LoadedRecord] = []
    for path in paths.state_variable_annotation_files(root):
        locator = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        document = _read_yaml(path, collected, root)
        if document is None:
            continue
        if isinstance(document, dict):
            items = document.get("annotations")
            if not isinstance(items, list):
                collected.append(
                    error(
                        "V1",
                        locator,
                        "a state-variable annotation file is either a YAML list of "
                        "annotations or a mapping with an `annotations` list; this file "
                        "is a mapping with no `annotations` list",
                    )
                )
                continue
            prefix = f"{locator}#/annotations"
        elif isinstance(document, list):
            items = document
            prefix = locator
        else:
            collected.append(
                error("V1", locator, "expected a YAML list or an `annotations` mapping")
            )
            continue
        for index, raw in enumerate(items):
            if isinstance(raw, dict) and isinstance(document, dict):
                # The wrapper form states annotated_by / annotated_on / run_id once for
                # the whole file. Inherit them so each annotation is complete without
                # the author having to repeat them on every entry.
                raw = {
                    **{
                        key: document[key]
                        for key in ("annotated_by", "annotated_on", "run_id", "schema_version")
                        if key in document and key not in raw
                    },
                    **raw,
                }
            loaded = _parse(
                "state_variable_annotation",
                raw,
                f"{prefix}/{index}",
                "state_variable",
                collected,
            )
            if loaded is not None:
                out.append(loaded)
    return out


# Source-record fields that are the agent's belief about what the registry says.
# Contract §1.3: two agents may register the same source, but they may not disagree
# about these, because a disagreement means one registration was written from a
# different record.
_REGISTRY_BELIEF_FIELDS: tuple[str, ...] = ("year",)

# Fields compared after NORMALISATION rather than raw. The divergence rule exists to
# catch a registration written from a DIFFERENT record; comparing raw titles made it
# fire on a trailing full stop, because one agent kept PubMed's and the other did not.
_NORMALISED_BELIEF_FIELDS: tuple[str, ...] = ("title",)

# How close two renderings of a title must be before they count as the same record.
#
# Two normalisations were tried first and both failed on real records. Exact equality on
# raw titles fired on a trailing full stop (one agent kept PubMed's, the other did not).
# Exact equality on punctuation-stripped titles then fired on `M(1)` versus `M1`, which
# normalise to `m 1` and `m1`. Subscripts, superscripts, spelled-out Greek letters,
# en-dashes and "(1)" forms will keep producing these, and each costs an agent a round
# trip for no epistemic gain.
#
# So the check is: identical after removing ALL whitespace (which makes `m(1)` and `m1`
# the same string, and is principled rather than a tuned constant), and failing that,
# similarity >= this threshold. 0.98 is tight enough that two different papers cannot
# pass it — even a shared title stem diverges far faster than 2% — and loose enough to
# absorb typography. `registry_year` and `doi` are compared EXACTLY, because those are
# structured fields where a difference really does mean a different record.
TITLE_SIMILARITY_THRESHOLD = 0.98


def _doi_of(record: dict[str, Any]) -> str | None:
    """The DOI an agent recorded for a source, lowercased for comparison."""
    identifiers = record.get("identifiers") or {}
    doi = identifiers.get("doi") if isinstance(identifiers, dict) else None
    return str(doi).lower() if doi else None


def _provenance_helpers() -> tuple[Any, Any]:
    """``(normalise_title, title_similarity)`` from ``scripts/_provenance.py``.

    Reused rather than reimplemented so the divergence check and the registry
    title-similarity check can never disagree about what counts as the same title.
    Falls back to local equivalents when the scripts directory is not importable, which
    keeps the library usable on its own.
    """
    try:
        import sys

        scripts = paths.resolve_root() / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from _provenance import normalise_title, title_similarity  # type: ignore[import-not-found]

        return normalise_title, title_similarity
    except Exception:  # noqa: BLE001 - the fallbacks must behave identically
        import re as _re
        from difflib import SequenceMatcher

        def normalise_title(title: str) -> str:
            text = title.strip().lower().rstrip(".")
            text = _re.sub(r"[^a-z0-9 ]+", " ", text)
            return _re.sub(r"\s+", " ", text).strip()

        def title_similarity(left: str, right: str) -> float:
            if not left or not right:
                return 0.0
            return round(
                SequenceMatcher(None, normalise_title(left), normalise_title(right)).ratio(), 4
            )

        return normalise_title, title_similarity


def _normalise_title(text: Any) -> str:
    """Normalise a title for comparison (lowercase, strip punctuation, collapse space)."""
    if not isinstance(text, str):
        return ""
    normalise, _ = _provenance_helpers()
    return normalise(text)


def _titles_agree(left: Any, right: Any) -> bool:
    """Whether two renderings of a title describe the same record.

    See :data:`TITLE_SIMILARITY_THRESHOLD` for why this is not exact equality.
    """
    if not isinstance(left, str) or not isinstance(right, str):
        return left == right
    normalise, similarity = _provenance_helpers()
    left_n, right_n = normalise(left), normalise(right)
    if left_n.replace(" ", "") == right_n.replace(" ", ""):
        return True
    return similarity(left, right) >= TITLE_SIMILARITY_THRESHOLD


def _index_sources(
    loaded: list[LoadedRecord], collected: list[Violation]
) -> tuple[dict[str, LoadedRecord], dict[str, tuple[str, ...]]]:
    """Index source records, allowing cross-agent duplication (contract §1.3).

    Duplicate registration across agents is ALLOWED AND PREFERRED: it keeps each
    agent's claims self-contained so no agent depends on a file it cannot edit.
    Treating it as a violation once pushed an agent into deleting its own
    registrations and pointing its claims at another agent's file — a cross-lane
    dependency that would silently break those claims if the other agent withdrew the
    source. Deduplication for counting belongs to the store and the graph compiler,
    never to the registry.

    Three cases:

    * same id in DIFFERENT files, agreeing on the registry fields -> not a violation;
      recorded in ``shared_sources`` because the red team's citation-dependence check
      wants to know which sources are shared;
    * same id in different files DISAGREEING on title, year or DOI -> hard error, both
      files and both values named;
    * same id TWICE IN ONE FILE -> error. It is a bookkeeping mistake with no upside.
    """
    by_id: dict[str, list[LoadedRecord]] = {}
    for record in loaded:
        if record.record_id is None:
            collected.append(error("V1", record.path, "source record has no source_id"))
            continue
        by_id.setdefault(record.record_id, []).append(record)

    index: dict[str, LoadedRecord] = {}
    shared: dict[str, tuple[str, ...]] = {}
    for source_id, group in sorted(by_id.items()):
        index[source_id] = group[0]
        if len(group) == 1:
            continue

        def owning_file(record: LoadedRecord) -> str:
            return record.path.split("#", 1)[0]

        files = [owning_file(record) for record in group]
        shared[source_id] = tuple(sorted(set(files)))

        seen_files: set[str] = set()
        for record in group:
            owner = owning_file(record)
            if owner in seen_files:
                collected.append(
                    error(
                        "V4",
                        record.path,
                        f"{source_id} is registered twice in {owner}. Registering the "
                        "same source in two DIFFERENT agents' files is allowed and "
                        "preferred (contract §1.3), but twice in one file is a "
                        "bookkeeping mistake with no upside.",
                        record_id=source_id,
                    )
                )
            seen_files.add(owner)

        first = group[0]
        for record in group[1:]:
            disagreements: list[str] = []
            for field_name in _REGISTRY_BELIEF_FIELDS:
                left, right = first.raw.get(field_name), record.raw.get(field_name)
                if left != right:
                    disagreements.append(f"{field_name}: {left!r} vs {right!r}")
            for field_name in _NORMALISED_BELIEF_FIELDS:
                left, right = first.raw.get(field_name), record.raw.get(field_name)
                if not _titles_agree(left, right):
                    disagreements.append(f"{field_name}: {left!r} vs {right!r}")
            left_doi, right_doi = _doi_of(first.raw), _doi_of(record.raw)
            if left_doi and right_doi and left_doi != right_doi:
                disagreements.append(f"doi: {left_doi!r} vs {right_doi!r}")
            if not disagreements:
                continue
            collected.append(
                error(
                    "V4",
                    record.path,
                    f"{source_id} is registered in {owning_file(first)} and "
                    f"{owning_file(record)} with DIFFERENT registry fields "
                    f"({'; '.join(disagreements)}). Duplicate registration is fine; "
                    "divergence is not — one of the two was written from a different "
                    "record, so the identifier is ambiguous (contract §1.3). Re-fetch "
                    "the metadata and correct the registration that is wrong.",
                    record_id=source_id,
                )
            )
    return dict(sorted(index.items())), dict(sorted(shared.items()))


def _index_by_id(
    loaded: list[LoadedRecord], kind: str, collected: list[Violation]
) -> dict[str, LoadedRecord]:
    """Index records by id, reporting duplicates rather than silently overwriting."""
    out: dict[str, LoadedRecord] = {}
    for record in loaded:
        if record.record_id is None:
            collected.append(
                error("V1", record.path, f"{kind} record has no identifier field")
            )
            continue
        existing = out.get(record.record_id)
        if existing is not None:
            collected.append(
                error(
                    "V4",
                    record.path,
                    f"duplicate {kind} id {record.record_id!r}, already defined in "
                    f"{existing.path}. Ids are unique across the repository: a "
                    "duplicate means one of the two records is invisible.",
                    record_id=record.record_id,
                )
            )
            continue
        out[record.record_id] = record
    return dict(sorted(out.items()))


def load_lock(root: Path | str | None = None) -> tuple[str, ...]:
    """Claim ids recorded in ``evidence/claims/claim_registry.lock``.

    Comment lines (``#``) and blank lines are ignored. A missing lock is an empty
    tuple: on a fresh repository the lock does not exist until
    ``graph/validate_graph.py --update-lock`` creates it.
    """
    path = paths.claim_registry_lock(root)
    if not path.is_file():
        return ()
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.append(stripped.split()[0])
    return tuple(ids)


def load_state_variables(
    root: Path | str | None = None,
) -> tuple[list[LoadedRecord], list[Violation]]:
    """Load every state-variable definition from ``state_model/{domain}.yaml``.

    Also reports a variable whose id domain segment disagrees with the file it is
    declared in, which would otherwise make the domain silently ambiguous.
    """
    resolved = paths.resolve_root(root)
    collected: list[Violation] = []
    out: list[LoadedRecord] = []
    for path in paths.state_domain_files(resolved):
        locator = str(path.relative_to(resolved))
        document = _read_yaml(path, collected, resolved)
        if not isinstance(document, dict):
            if document is not None:
                collected.append(
                    error("V1", locator, "a state-model file is a YAML mapping with a "
                          "`domain` and a `variables` list")
                )
            continue
        file_domain = document.get("domain") or path.stem
        for index, raw in enumerate(document.get("variables") or []):
            item_locator = f"{locator}#/variables/{index}"
            loaded = _parse("state_variable", raw, item_locator, "id", collected)
            if loaded is None:
                continue
            declared = str(loaded.record_id or "")
            if declared.startswith("SV:"):
                id_domain = declared.split(":", 1)[1].split(".", 1)[0]
                if id_domain != file_domain:
                    collected.append(
                        error(
                            "V2",
                            item_locator,
                            f"{declared} declares domain {id_domain!r} but is defined in "
                            f"the {file_domain!r} file. The domain is part of the "
                            "identifier (ontology/state_variables.yaml), so the two can "
                            "never disagree.",
                            record_id=declared,
                        )
                    )
            out.append(loaded)
    return out, collected


def load_definitional_edges(
    root: Path | str | None = None,
) -> tuple[list[LoadedRecord], list[Violation]]:
    """Load ``ontology/definitional_edges.yaml`` as edge records."""
    resolved = paths.resolve_root(root)
    collected: list[Violation] = []
    out: list[LoadedRecord] = []
    path = paths.definitional_edges_file(resolved)
    if not path.is_file():
        return out, collected
    locator = str(path.relative_to(resolved))
    document = _read_yaml(path, collected, resolved)
    if not isinstance(document, dict):
        return out, collected
    for index, raw in enumerate(document.get("edges") or []):
        loaded = _parse("edge", raw, f"{locator}#/edges/{index}", None, collected)
        if loaded is not None:
            out.append(loaded)
    return out, collected


def load_seed_registry(root: Path | str | None = None) -> dict[str, Any]:
    """Load ``targets/seed_registry.yaml``, or ``{}`` when it does not exist."""
    path = paths.seed_registry_file(root)
    if not path.is_file():
        return {}
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return document if isinstance(document, dict) else {}


def load_repository(root: Path | str | None = None) -> Repository:
    """Load every curated record under ``root`` into one :class:`Repository`.

    Tolerant of an empty repository by design: on today's tree this returns a
    ``Repository`` with zero sources and zero claims and no violations.
    """
    resolved = paths.resolve_root(root)
    collected: list[Violation] = []

    sources = _load_list_files(
        paths.source_files(resolved), "source", "source_id", resolved, collected
    )
    claims = _load_list_files(
        paths.claim_files(resolved), "claim", "claim_id", resolved, collected
    )
    audits = _load_list_files(
        paths.audit_files(resolved), "audit", "audit_id", resolved, collected
    )
    annotations = _load_annotation_files(resolved, collected)
    targets = _load_document_files(
        paths.target_files(resolved), "target", "target_id", resolved, collected
    )
    assessments = _load_document_files(
        paths.assessment_files(resolved), "assessment", "target_id", resolved, collected
    )
    interventions = _load_document_files(
        paths.intervention_files(resolved), "intervention", "id", resolved, collected
    )
    # Three atlases chose `id` and `intervention_id` independently; index by whichever
    # the record used, so an aliased record is still referenceable (deviation D8).
    interventions = [
        record
        if record.record_id is not None
        else LoadedRecord(
            kind=record.kind,
            raw=record.raw,
            path=record.path,
            record_id=(
                str(record.raw["intervention_id"])
                if isinstance(record.raw.get("intervention_id"), str)
                else None
            ),
            model=record.model,
        )
        for record in interventions
    ]
    external_analyses = _load_document_files(
        paths.external_analysis_files(resolved),
        "external_analysis",
        "analysis_id",
        resolved,
        collected,
    )
    state_variables, sv_violations = load_state_variables(resolved)
    collected.extend(sv_violations)
    axioms, axiom_violations = load_definitional_edges(resolved)
    collected.extend(axiom_violations)

    source_index, shared_sources = _index_sources(sources, collected)
    return Repository(
        root=resolved,
        sources=source_index,
        claims=_index_by_id(claims, "claim", collected),
        targets=_index_by_id(targets, "target", collected),
        assessments=sorted(assessments, key=lambda r: (r.path, r.record_id or "")),
        audits=_index_by_id(audits, "audit", collected),
        interventions=_index_by_id(interventions, "intervention", collected),
        state_variables=_index_by_id(state_variables, "state_variable", collected),
        state_variable_annotations=sorted(
            annotations, key=lambda r: (r.path, r.record_id or "")
        ),
        definitional_edges=axioms,
        external_analyses=_index_by_id(external_analyses, "external_analysis", collected),
        seed_registry=load_seed_registry(resolved),
        lock_claim_ids=load_lock(resolved),
        shared_sources=shared_sources,
        violations=collected,
    )
