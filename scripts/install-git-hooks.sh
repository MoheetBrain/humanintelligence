#!/usr/bin/env bash
# Install the repository's version-controlled git hooks.
#
# Points git at .githooks/ so the pre-commit gate (Commit Continuity Protocol
# fallback + blackboard format gate) runs for every commit in this clone,
# including commits made outside Claude Code.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks

echo "core.hooksPath -> .githooks"
echo "installed hooks:"
ls -1 .githooks
echo
echo "The gate refuses a commit unless docs/PROJECT_STATUS.md and docs/PROJECT_LEDGER.md"
echo "are updated and staged, and (when evidence records change) the validator passes."
