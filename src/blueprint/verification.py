"""Read the source-verification index and answer "is this source verified?" (rule V6).

Design rules:

* OFFLINE. This module never touches the network. The index under
  ``data/interim/source_verification/{agent}.jsonl`` is derived by
  ``scripts/fetch_source_metadata.py`` from the immutable snapshots in ``data/raw/`` and
  is rebuildable offline (contract P7). Every file in that directory is read, because
  each agent verifies the sources it cites.
* A MISSING INDEX IS NOT AN ERROR AND NOT A PASS. It means "no verification available",
  which :func:`missing_index_violation` reports as a warning that ``--strict`` turns
  into an error. Crashing would make an incomplete repository unvalidatable; treating it
  as a pass would defeat the anti-fabrication mechanism entirely.
* DUPLICATES FAIL CLOSED. Two agents citing the same paper legitimately produce two
  rows that differ in ``agent`` and ``claimed_title``; that is the normal case, not a
  problem. So rows are grouped by ``source_id`` and:

  - if the REGISTRY fields disagree between rows, that is a hard error, because it means
    one row was built from a different record and the identifier is ambiguous; and
  - otherwise the WORST status across rows wins. An earlier implementation let the last
    line win, which could silently hide a ``title_mismatch`` behind a later ``verified``
    row — failing open on exactly the check that exists to catch fabrication.

* DATABASE RELEASES ARE VERIFIED DIFFERENTLY. A ``SRC:DB:*`` or ``SRC:DATASET:*`` source
  has no literature registry to check against, so it is verified against its own
  immutable snapshot (``release_verified_by_snapshot``). That status passes V6 for those
  two prefixes ONLY: accepting it for a paper would let an unverifiable PMID through.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from blueprint import paths, vocab
from blueprint.violations import Violation, error, warning

# Registry fields that must agree between rows describing the same source. A
# disagreement means the rows were built from different records.
REGISTRY_FIELDS: tuple[str, ...] = ("registry_title", "registry_year", "registry_doi")

# Status severity, worst first. Grouping takes the worst status so duplication can only
# make the answer stricter, never laxer.
STATUS_SEVERITY: tuple[str, ...] = (
    "retracted",
    "snapshot_missing_or_altered",
    "not_found",
    "title_mismatch",
    "year_mismatch",
    "unsupported_registry",
    "not_checked",
    "release_verified_by_snapshot",
    "verified",
)

# Source prefixes for which snapshot verification is the correct and sufficient check.
SNAPSHOT_VERIFIABLE_PREFIXES: tuple[str, ...] = ("SRC:DB:", "SRC:DATASET:")


def _worst(statuses: list[str]) -> str:
    """The worst status in ``statuses``, by :data:`STATUS_SEVERITY`.

    An unrecognised status is treated as the worst of all: a status this module does not
    understand must never be silently accepted.
    """
    ranked = [(STATUS_SEVERITY.index(s) if s in STATUS_SEVERITY else -1, s) for s in statuses]
    return min(ranked)[1] if ranked else "not_checked"


@dataclass(frozen=True)
class VerificationIndex:
    """The verification records available for one repository root."""

    root: Path
    records: dict[str, dict]
    rows: dict[str, tuple[dict, ...]] = field(default_factory=dict)
    files: tuple[Path, ...] = ()
    registry_conflicts: tuple[tuple[str, tuple[dict, ...]], ...] = ()
    malformed: tuple[tuple[str, str], ...] = ()

    @property
    def available(self) -> bool:
        """Whether any index file was found at all."""
        return bool(self.files)

    def status_for(self, source_id: str) -> str | None:
        """Worst verification status recorded for ``source_id``, or ``None``.

        ``None`` means "nobody checked", which is different from ``not_checked``
        (checked and deliberately skipped) and must not be collapsed into it.
        """
        record = self.records.get(source_id)
        return None if record is None else str(record.get("status", "not_checked"))

    def record_for(self, source_id: str) -> dict | None:
        """The merged verification record for ``source_id``, or ``None``."""
        return self.records.get(source_id)

    def rows_for(self, source_id: str) -> tuple[dict, ...]:
        """Every row describing ``source_id``, in file order."""
        return self.rows.get(source_id, ())

    def is_verified(self, source_id: str, root: Path | str | None = None) -> bool:
        """Whether ``source_id`` passes rule V6, respecting the prefix restriction."""
        status = self.status_for(source_id)
        if status is None:
            return False
        where = root or self.root
        passing = set(vocab.subset("verification_status", "passing_values", where))
        snapshot_only = set(
            vocab.subset("verification_status", "snapshot_verified_values", where)
        )
        if status in snapshot_only:
            return source_id.startswith(SNAPSHOT_VERIFIABLE_PREFIXES)
        return status in passing

    def summary(self) -> dict[str, int]:
        """Count of sources per (worst) status, for the validator's honest summary."""
        counts: dict[str, int] = {}
        for record in self.records.values():
            key = str(record.get("status", "not_checked"))
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))


def load(root: Path | str | None = None) -> VerificationIndex:
    """Load every verification index file for ``root`` and merge rows per source.

    Never raises for a missing or partially malformed index: a malformed line is
    recorded and reported by :func:`index_violations`, so one bad line cannot hide the
    rest of the index.
    """
    resolved = paths.resolve_root(root)
    files = tuple(paths.source_verification_paths(resolved))
    grouped: dict[str, list[dict]] = {}
    malformed: list[tuple[str, str]] = []

    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:  # pragma: no cover - unreadable file
            malformed.append((str(path), f"could not be read: {exc}"))
            continue
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed.append((f"{path}:{number}", f"not valid JSON: {exc}"))
                continue
            if not isinstance(payload, dict) or "source_id" not in payload:
                malformed.append((f"{path}:{number}", "no source_id field"))
                continue
            grouped.setdefault(str(payload["source_id"]), []).append(payload)

    merged: dict[str, dict] = {}
    conflicts: list[tuple[str, tuple[dict, ...]]] = []
    for source_id, rows in sorted(grouped.items()):
        signatures = {
            tuple(str(row.get(key)) for key in REGISTRY_FIELDS) for row in rows
        }
        if len(signatures) > 1:
            conflicts.append((source_id, tuple(rows)))
        worst = _worst([str(row.get("status", "not_checked")) for row in rows])
        # Present the row carrying the worst status, so a caller reading
        # registry_title sees the row that produced the verdict.
        chosen = next(
            (row for row in rows if str(row.get("status", "not_checked")) == worst), rows[0]
        )
        record = dict(chosen)
        record["status"] = worst
        if len(rows) > 1:
            record["_row_count"] = len(rows)
            record["_agents"] = sorted({str(row.get("agent")) for row in rows if row.get("agent")})
        merged[source_id] = record

    return VerificationIndex(
        root=resolved,
        records=merged,
        rows={k: tuple(v) for k, v in sorted(grouped.items())},
        files=files,
        registry_conflicts=tuple(conflicts),
        malformed=tuple(malformed),
    )


def status_for(source_id: str, root: Path | str | None = None) -> str | None:
    """Convenience wrapper: worst verification status of one source, or ``None``."""
    return load(root).status_for(source_id)


def missing_index_violation(
    index: VerificationIndex, *, source_count: int
) -> list[Violation]:
    """Report an absent index as a warning that ``--strict`` escalates.

    Returns nothing when the index exists, or when there are no sources to verify:
    an empty repository with no index is a correct state, not a problem.
    """
    if index.available or source_count == 0:
        return []
    return [
        warning(
            "V6",
            "data/interim/source_verification/",
            f"no source-verification index found, so none of the {source_count} "
            "registered source(s) can be checked against its registry. Run "
            "`make fetch-sources` (network), or "
            "`scripts/fetch_source_metadata.py --all --offline` to rebuild from the "
            "committed snapshots. Under --strict this is an error: an unverified source "
            "is indistinguishable from a fabricated one (contract §7, rule V6).",
        )
    ]


def index_violations(index: VerificationIndex) -> list[Violation]:
    """Report malformed lines and registry-field conflicts in the index itself.

    Cross-agent duplication is NOT reported: two agents citing the same paper is the
    normal case, and :func:`load` already takes the worst status across their rows.
    What is reported is a disagreement about what the registry said, which means the
    rows describe different records under one identifier.
    """
    out: list[Violation] = []
    for locator, reason in index.malformed:
        out.append(
            error(
                "V6",
                locator,
                f"verification index line {reason}. The index is machine-generated; a "
                "malformed line means the generator or the file is corrupt, and it must "
                "not be silently skipped.",
            )
        )
    for source_id, rows in index.registry_conflicts:
        detail = "; ".join(
            f"{row.get('agent') or 'unknown agent'}: "
            + ", ".join(f"{key}={row.get(key)!r}" for key in REGISTRY_FIELDS)
            for row in rows
        )
        out.append(
            error(
                "V6",
                "data/interim/source_verification/",
                f"{source_id} has verification rows that DISAGREE about what the registry "
                f"said ({detail}). Two agents citing the same source is expected and fine; "
                "two different registry answers under one identifier is not — one row was "
                "built from a different record, so the identifier is ambiguous. Rebuild the "
                "index from the snapshots.",
                record_id=source_id,
            )
        )
    return out
