"""Virtual pharmacology — interface-only, gated behind G5 (Sprint 4).

Nothing in this package is implemented. It exists so that Sprint-4 work has a shape to
fill and a gate to pass, and so that the boundary is recorded before anyone crosses it.

Two rules bind everything here, without exception:

* **Everything stays in silico.** No wet-lab, in-vitro, ex-vivo, animal or human work
  is performed, planned, designed, requested or recommended, including
  self-experimentation (``docs/COMPUTATIONAL_ONLY_POLICY.md``).
* **No output is ever a protocol, a dose, a route, a regimen or a sourcing route.**

See ``docs/PHARMACOLOGY_INTERFACES.md`` for the full statement, and
:mod:`blueprint.pharmacology.gates` for gate G5.
"""

from __future__ import annotations

__all__ = ["GATE_ID", "SPRINT"]

#: The gate that must pass before anything in this package may run.
GATE_ID = "G5"

#: The sprint that owns the implementation.
SPRINT = 4
