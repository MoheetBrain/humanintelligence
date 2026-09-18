"""Repository-root discovery and canonical paths.

Design rules:

* Every accessor takes an optional ``root`` so tests can run the whole library against
  a fixture tree. When ``root`` is omitted the repository root is discovered by walking
  up from this file looking for the marker files that define the blackboard.
* Accessors return paths that may not exist. Callers decide whether a missing path is
  an empty collection (usually) or a violation (rarely). Nothing here creates
  directories: creating a directory in another agent's lane would be an ownership
  violation.
* Record directories are listed here once, so a new record location is a one-line
  change rather than a grep.
"""

from __future__ import annotations

from pathlib import Path

# Files whose joint presence identifies the repository root. The data contract alone
# is not enough: a fixture tree may legitimately carry a partial copy.
ROOT_MARKERS: tuple[str, ...] = ("docs/DATA_CONTRACT.md", "ontology")

# Fixture trees are minimal; this marker is what makes a directory usable as a root.
FIXTURE_MARKER = ".blueprint-root"


def find_repo_root(start: Path | str | None = None) -> Path:
    """Return the repository root, walking up from ``start``.

    A directory is the root when it contains every entry in :data:`ROOT_MARKERS`, or
    when it contains :data:`FIXTURE_MARKER` (how a test fixture tree declares itself).
    Falls back to the installed package's grandparent, which is correct for both an
    editable install and a ``src`` layout used via ``PYTHONPATH``.
    """
    here = Path(start).resolve() if start is not None else Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if not candidate.is_dir():
            continue
        if (candidate / FIXTURE_MARKER).exists():
            return candidate
        if all((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    # src/blueprint/paths.py -> src/blueprint -> src -> <root>
    return Path(__file__).resolve().parents[2]


def resolve_root(root: Path | str | None = None) -> Path:
    """Normalise a caller-supplied root, discovering it when ``None``."""
    return find_repo_root() if root is None else Path(root).resolve()


# --------------------------------------------------------------------- ontology ---

def ontology_dir(root: Path | str | None = None) -> Path:
    """Directory holding the node/edge/vocabulary type system."""
    return resolve_root(root) / "ontology"


def nodes_file(root: Path | str | None = None) -> Path:
    """``ontology/nodes.yaml`` — node type declarations."""
    return ontology_dir(root) / "nodes.yaml"


def edges_file(root: Path | str | None = None) -> Path:
    """``ontology/edges.yaml`` — relation declarations."""
    return ontology_dir(root) / "edges.yaml"


def vocabularies_file(root: Path | str | None = None) -> Path:
    """``ontology/vocabularies.yaml`` — the single source of truth for enums."""
    return ontology_dir(root) / "vocabularies.yaml"


def primitives_file(root: Path | str | None = None) -> Path:
    """``ontology/computational_primitives.yaml`` — the 24 working definitions."""
    return ontology_dir(root) / "computational_primitives.yaml"


def state_variable_types_file(root: Path | str | None = None) -> Path:
    """``ontology/state_variables.yaml`` — the state-variable type system."""
    return ontology_dir(root) / "state_variables.yaml"


def definitional_edges_file(root: Path | str | None = None) -> Path:
    """``ontology/definitional_edges.yaml`` — claim-free ontology axioms."""
    return ontology_dir(root) / "definitional_edges.yaml"


# ----------------------------------------------------------------- state model ---

def state_model_dir(root: Path | str | None = None) -> Path:
    """Directory holding one state-variable file per domain plus ``dynamics.yaml``."""
    return resolve_root(root) / "state_model"


def dynamics_file(root: Path | str | None = None) -> Path:
    """``state_model/dynamics.yaml`` — formal structure of the state model."""
    return state_model_dir(root) / "dynamics.yaml"


def state_domain_files(root: Path | str | None = None) -> list[Path]:
    """Existing per-domain state-variable files, sorted; ``dynamics.yaml`` excluded."""
    directory = state_model_dir(root)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.yaml") if p.name != "dynamics.yaml")


# --------------------------------------------------------------------- schemas ---

def schemas_dir(root: Path | str | None = None) -> Path:
    """Directory holding the JSON Schemas."""
    return resolve_root(root) / "schemas"


def schema_file(name: str, root: Path | str | None = None) -> Path:
    """Path to one schema by bare name (``"claim"`` -> ``claim.schema.json``)."""
    stem = name if name.endswith(".schema.json") else f"{name}.schema.json"
    return schemas_dir(root) / stem


def schema_files(root: Path | str | None = None) -> list[Path]:
    """Every existing ``*.schema.json``, sorted."""
    directory = schemas_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.schema.json"))


# --------------------------------------------------------------------- records ---

def evidence_dir(root: Path | str | None = None) -> Path:
    """``evidence/`` — sources, claims and audits."""
    return resolve_root(root) / "evidence"


def sources_dir(root: Path | str | None = None) -> Path:
    """``evidence/sources/`` — one YAML list per agent."""
    return evidence_dir(root) / "sources"


def claims_dir(root: Path | str | None = None) -> Path:
    """``evidence/claims/`` — one directory per agent."""
    return evidence_dir(root) / "claims"


def audits_dir(root: Path | str | None = None) -> Path:
    """``evidence/audits/`` — one directory per auditor."""
    return evidence_dir(root) / "audits"


def claim_registry_lock(root: Path | str | None = None) -> Path:
    """``evidence/claims/claim_registry.lock`` — append-only claim id ledger.

    Not owned by ``agent:ontology``; created on demand by
    ``graph/validate_graph.py --update-lock`` and never rewritten in place.
    """
    return claims_dir(root) / "claim_registry.lock"


def targets_dir(root: Path | str | None = None) -> Path:
    """``targets/`` — seed registry plus per-target dossiers."""
    return resolve_root(root) / "targets"


def seed_registry_file(root: Path | str | None = None) -> Path:
    """``targets/seed_registry.yaml`` — the orchestrator's work assignment."""
    return targets_dir(root) / "seed_registry.yaml"


def target_candidates_dir(root: Path | str | None = None) -> Path:
    """``targets/candidates/`` — one dossier per target."""
    return targets_dir(root) / "candidates"


def atlases_dir(root: Path | str | None = None) -> Path:
    """``atlases/`` — per-domain assessments, interventions and annotations."""
    return resolve_root(root) / "atlases"


def assessment_files(root: Path | str | None = None) -> list[Path]:
    """Every ``atlases/*/assessments/*.yaml``, sorted."""
    directory = atlases_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/assessments/*.yaml"))


def intervention_files(root: Path | str | None = None) -> list[Path]:
    """Every ``atlases/*/interventions/*.yaml``, sorted."""
    directory = atlases_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/interventions/*.yaml"))


def state_variable_annotation_files(root: Path | str | None = None) -> list[Path]:
    """Every ``atlases/*/state_variable_annotations.yaml``, sorted."""
    directory = atlases_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/state_variable_annotations.yaml"))


def source_files(root: Path | str | None = None) -> list[Path]:
    """Every ``evidence/sources/*.yaml``, sorted."""
    directory = sources_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.yaml"))


def claim_files(root: Path | str | None = None) -> list[Path]:
    """Every ``evidence/claims/*/*.yaml``, sorted."""
    directory = claims_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/*.yaml"))


def audit_files(root: Path | str | None = None) -> list[Path]:
    """Every ``evidence/audits/*/*.yaml``, sorted."""
    directory = audits_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/*.yaml"))


def external_analysis_files(root: Path | str | None = None) -> list[Path]:
    """Every ``analyses/external/*.yaml``, sorted.

    An external agent's analysis record. Kept in its own directory rather than mixed
    into ``evidence/`` because its verification state, not its content, is what a reader
    must see first: everything here is inert until artefacts arrive.
    """
    directory = resolve_root(root) / "analyses" / "external"
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.yaml"))


def target_files(root: Path | str | None = None) -> list[Path]:
    """Every ``targets/candidates/*.yaml``, sorted."""
    directory = target_candidates_dir(root)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.yaml"))


# ------------------------------------------------------------------------ data ---

def data_dir(root: Path | str | None = None) -> Path:
    """``data/`` — raw snapshots, interim indexes, processed tables."""
    return resolve_root(root) / "data"


def raw_dir(root: Path | str | None = None) -> Path:
    """``data/raw/`` — immutable network snapshots."""
    return data_dir(root) / "raw"


def raw_manifest(root: Path | str | None = None) -> Path:
    """``data/raw/MANIFEST.jsonl`` — one checksum line per snapshot."""
    return raw_dir(root) / "MANIFEST.jsonl"


def interim_dir(root: Path | str | None = None) -> Path:
    """``data/interim/`` — derived, rebuildable indexes."""
    return data_dir(root) / "interim"


def gene_identifiers_file(root: Path | str | None = None) -> Path:
    """``data/interim/gene_identifiers.jsonl`` — HGNC-resolved gene identifiers."""
    return interim_dir(root) / "gene_identifiers.jsonl"


def source_verification_paths(root: Path | str | None = None) -> list[Path]:
    """Every existing source-verification index file, sorted.

    Contract §7 names ``data/interim/source_verification.jsonl``; the orchestrator's
    brief also refers to a ``data/interim/source_verification/*.jsonl`` directory. Both
    are read (see docs/blackboard/schema_change_requests/ontology-003.yaml), so a
    sharded index and a single file behave identically.
    """
    interim = interim_dir(root)
    found: list[Path] = []
    single = interim / "source_verification.jsonl"
    if single.is_file():
        found.append(single)
    sharded = interim / "source_verification"
    if sharded.is_dir():
        found.extend(sorted(sharded.glob("*.jsonl")))
    return found


# ------------------------------------------------------------------------ docs ---

def docs_dir(root: Path | str | None = None) -> Path:
    """``docs/`` — contracts, protocol, status, ledger."""
    return resolve_root(root) / "docs"


def task_dag_file(root: Path | str | None = None) -> Path:
    """``docs/TASK_DAG.yaml`` — the closed ``action_type`` enum lives here."""
    return docs_dir(root) / "TASK_DAG.yaml"


def data_contract_file(root: Path | str | None = None) -> Path:
    """``docs/DATA_CONTRACT.md`` — the authoritative contract."""
    return docs_dir(root) / "DATA_CONTRACT.md"


def ownership_file(root: Path | str | None = None) -> Path:
    """``docs/OWNERSHIP.yaml`` — path-to-owner map."""
    return docs_dir(root) / "OWNERSHIP.yaml"


def facet_rubric_file(root: Path | str | None = None) -> Path:
    """``models/ranking/facet_rubric_v0_1.yaml`` — owned by ``agent:integration``.

    Read, never written, by this package. The ``database_gradable`` flag that licenses
    ``source_refs``-only facet grading lives there, so rule V11 reads the rubric rather
    than hard-coding a facet name (contract §5.2).
    """
    return models_dir(root) / "ranking" / "facet_rubric_v0_1.yaml"


def models_dir(root: Path | str | None = None) -> Path:
    """``models/`` — the only place a number may be derived from (contract P3)."""
    return resolve_root(root) / "models"
