"""Shared test fixtures: build throwaway repository roots from small fixture trees.

Design rules:

* A fixture tree under ``tests/fixtures/`` holds ONLY the records under test. The
  ontology, schemas and state model are shared from the real repository by symlink, so
  a fixture is a handful of lines rather than a copy of ``ontology/``. A fixture that
  duplicated the ontology would drift from it, and then the tests would be testing the
  copy.
* Each test gets its own ``tmp_path`` root, marked with ``.blueprint-root`` so
  :func:`blueprint.paths.find_repo_root` stops there. Nothing a test does can touch the
  real repository.
* Caches are cleared per root, because :mod:`blueprint.ontology` and
  :mod:`blueprint.vocab` cache by root and a test that pointed at a mutated tree would
  otherwise see stale data.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Directories shared from the real repository into every fixture root. These are the
# type system and the contract, which fixtures test against rather than replace.
SHARED_DIRS: tuple[str, ...] = ("ontology", "schemas", "state_model", "docs")


def _clear_caches() -> None:
    """Drop every per-root cache in the library."""
    from blueprint import ids, ontology, policy, schemas, vocab

    for cached in (
        ontology.load,
        vocab.load,
        policy.action_types,
        schemas.load_schema,
        schemas.validator_for,
        ids._prefixes_longest_first,
    ):
        cached.cache_clear()


def build_root(destination: Path, case: str | None = None) -> Path:
    """Create a repository root at ``destination``, optionally seeded from a fixture.

    ``case`` names a directory under ``tests/fixtures/``. Its files are laid over the
    shared type system, so a fixture may deliberately override a shared file when a
    test needs a broken ontology or state model.

    A shared directory is SYMLINKED when the fixture does not touch it and COPIED when
    it does. That distinction is load-bearing: an earlier version symlinked
    unconditionally, and copying a fixture file into the symlinked ``state_model/``
    wrote straight through the link and overwrote the real repository's file. Every
    write is additionally checked to land inside ``destination``, so the failure mode
    cannot come back by another route.
    """
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / ".blueprint-root").write_text(
        "# Marker: blueprint.paths.find_repo_root treats this directory as a "
        "repository root.\n# Created by tests/conftest.py; never present in the real "
        "repository.\n",
        encoding="utf-8",
    )

    case_dir = FIXTURES / case if case is not None else None
    if case_dir is not None and not case_dir.is_dir():
        raise AssertionError(f"fixture case not found: {case_dir}")

    fixture_files = (
        [item for item in sorted(case_dir.rglob("*")) if item.is_file()]
        if case_dir is not None
        else []
    )
    overridden = {
        item.relative_to(case_dir).parts[0]
        for item in fixture_files
        if item.relative_to(case_dir).parts
    }

    for name in SHARED_DIRS:
        source = REPO_ROOT / name
        if not source.is_dir():
            continue
        target = destination / name
        if name in overridden:
            # The fixture writes here, so give it real files to write over.
            shutil.copytree(source, target, symlinks=False)
        else:
            target.symlink_to(source, target_is_directory=True)

    for item in fixture_files:
        relative = item.relative_to(case_dir)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        resolved_parent = target.parent.resolve()
        if destination != resolved_parent and destination not in resolved_parent.parents:
            raise AssertionError(
                f"refusing to write fixture file outside the test root: {target} "
                f"resolves to {resolved_parent}"
            )
        shutil.copy2(item, target)

    _clear_caches()
    return destination


@pytest.fixture
def make_root(tmp_path: Path) -> Callable[[str | None], Path]:
    """Factory returning a fresh repository root, optionally seeded from a fixture."""
    counter = {"n": 0}

    def factory(case: str | None = None) -> Path:
        counter["n"] += 1
        destination = tmp_path / f"root{counter['n']}"
        return build_root(destination, case)

    yield factory
    _clear_caches()


@pytest.fixture
def empty_root(make_root: Callable[[str | None], Path]) -> Path:
    """A repository root with the type system and no records at all."""
    return make_root(None)


@pytest.fixture(autouse=True)
def _isolate_caches():
    """Clear library caches around every test so roots never leak into each other."""
    _clear_caches()
    yield
    _clear_caches()
