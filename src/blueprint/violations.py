"""The single violation type used by every validator rule.

Design rules:

* A violation is DATA, not an exception. The validator collects them all and reports
  them grouped by rule; it does not stop at the first problem, because an agent fixing
  records needs the whole list.
* ``rule`` is a contract rule id (``V5``, ``V16``, ...) or a rule id defined by this
  repository (``ONT1`` for ontology self-consistency). ``path`` is a
  filesystem-or-record locator precise enough to fix the problem without searching.
* ``severity`` is ``error``, ``warning`` or ``info``. Under ``--strict`` a WARNING is
  treated as an error; ``info`` never is. A rule author chooses ``warning`` only when
  the condition may legitimately hold in an incomplete repository, and ``info`` when the
  finding is worth surfacing but is not a defect in any state of the repository —
  anything that would corrupt provenance is an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True, order=True)
class Violation:
    """One rule failure, at one location, with one message.

    Ordering is ``(rule, path, message)`` so that report output is deterministic
    regardless of the order rules happen to run in.
    """

    rule: str
    severity: Severity
    path: str
    message: str
    record_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict[str, Any]:
        """JSON-ready form, with sorted context keys for deterministic output."""
        payload: dict[str, Any] = {
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.record_id is not None:
            payload["record_id"] = self.record_id
        if self.context:
            payload["context"] = {k: self.context[k] for k in sorted(self.context)}
        return payload

    def __str__(self) -> str:
        prefix = f"{self.rule} [{self.severity}]"
        located = f"{prefix} {self.path}"
        if self.record_id:
            located = f"{located} ({self.record_id})"
        return f"{located}: {self.message}"


def error(rule: str, path: str, message: str, **kwargs: Any) -> Violation:
    """Construct an ``error``-severity violation."""
    return Violation(rule=rule, severity="error", path=path, message=message, **kwargs)


def warning(rule: str, path: str, message: str, **kwargs: Any) -> Violation:
    """Construct a ``warning``-severity violation (``--strict`` escalates it)."""
    return Violation(rule=rule, severity="warning", path=path, message=message, **kwargs)


def info(rule: str, path: str, message: str, **kwargs: Any) -> Violation:
    """Construct an ``info``-severity finding, which never fails a run.

    For findings that are worth surfacing but are not a defect in any state of the
    repository — a source registered but not yet cited, for instance. Escalating those
    under ``--strict`` would make the gate fire on a repository that is merely
    incomplete.
    """
    return Violation(rule=rule, severity="info", path=path, message=message, **kwargs)
