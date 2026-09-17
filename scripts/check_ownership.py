#!/usr/bin/env python3
"""Check that changed paths respect the blackboard ownership map.

The blackboard architecture only works if agents write where they are supposed to.
This script compares the working tree (or a given set of paths) against
``docs/OWNERSHIP.yaml`` and reports any path that no owner claims, or that is claimed
by an owner other than the one named with ``--agent``.

Usage
-----
    python scripts/check_ownership.py                    # classify all changed paths
    python scripts/check_ownership.py --agent brakes     # fail if a path is not brakes'
    python scripts/check_ownership.py --paths a/b.yaml   # classify specific paths
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = REPO_ROOT / "docs" / "OWNERSHIP.yaml"


def load_ownership() -> tuple[dict[str, list[str]], list[str], list[str]]:
    data = yaml.safe_load(OWNERSHIP.read_text(encoding="utf-8"))
    return (
        {owner: list(globs) for owner, globs in (data.get("owners") or {}).items()},
        list(data.get("shared_append_only") or []),
        list(data.get("generated_only") or []),
    )


def changed_paths() -> list[str]:
    """Tracked + untracked changes in the working tree, repo-relative."""
    out = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"'))
    return paths


def matches(path: str, globs: list[str]) -> bool:
    for pattern in globs:
        if fnmatch.fnmatch(path, pattern):
            return True
        # treat "a/**" as also matching "a/b/c"
        if pattern.endswith("/**") and path.startswith(pattern[:-3] + "/"):
            return True
    return False


def owner_of(path: str, owners: dict[str, list[str]], shared: list[str], generated: list[str]) -> str:
    for pattern in generated:
        if matches(path, [pattern]):
            return "generated_only"
    for pattern in shared:
        concrete = pattern.replace("{agent}", "*")
        if matches(path, [concrete]):
            return "shared_append_only"
    claimants = [owner for owner, globs in owners.items() if matches(path, globs)]
    if len(claimants) == 1:
        return claimants[0]
    if len(claimants) > 1:
        # most specific (longest matching glob) wins; report ambiguity explicitly
        return "AMBIGUOUS:" + ",".join(sorted(claimants))
    return "UNCLAIMED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent", help="agent name (without the 'agent:' prefix) to check against")
    parser.add_argument("--paths", nargs="*", help="paths to classify (default: working-tree changes)")
    args = parser.parse_args(argv)

    owners, shared, generated = load_ownership()
    # .gitkeep placeholders are structural, not content: they belong to whoever
    # created the directory and are never a lane violation.
    paths = [p for p in (args.paths or changed_paths()) if Path(p).name != ".gitkeep"]
    if not paths:
        print("no changed paths")
        return 0

    expected = f"agent:{args.agent}" if args.agent else None
    violations: list[tuple[str, str]] = []
    for path in sorted(paths):
        owner = owner_of(path, owners, shared, generated)
        flag = " "
        if owner.startswith(("UNCLAIMED", "AMBIGUOUS")):
            flag = "!"
            violations.append((path, owner))
        elif expected and owner not in {expected, "shared_append_only"}:
            flag = "!"
            violations.append((path, owner))
        print(f" {flag} {owner:28s} {path}")

    if violations:
        print(f"\n{len(violations)} ownership violation(s)")
        if expected:
            print(f"expected owner: {expected} (or shared_append_only)")
        return 1
    print(f"\nall {len(paths)} path(s) owned as expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
