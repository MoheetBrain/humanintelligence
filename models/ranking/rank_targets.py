#!/usr/bin/env python3
"""CLI entry point for the ranking model — the target of ``make rank``.

Thin wrapper so that the Makefile's ``$(PY) models/ranking/rank_targets.py`` works
whether or not the ``blueprint`` package has been installed into the environment:
the repository's ``src/`` directory is put on ``sys.path`` when the import fails.

All behaviour, options and exit codes live in :mod:`blueprint.ranking.cli`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    from blueprint.ranking.cli import main
except ModuleNotFoundError:  # pragma: no cover - depends on install state
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from blueprint.ranking.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
