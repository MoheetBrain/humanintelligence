"""Shared provenance helpers for the network-fetching scripts.

Design rules (see docs/DATA_CONTRACT.md §7):

* Every network response is written verbatim to ``data/raw/<registry>/<UTC date>/``
  and recorded in ``data/raw/MANIFEST.jsonl`` with a sha256. Raw data is immutable:
  a file is never rewritten, only added.
* Derived indexes live under ``data/interim/`` and are always rebuildable from the
  snapshots with no network access.
* No credentials are ever written to disk. API keys are read from the environment
  (``NCBI_API_KEY``) and never logged.

Standard library only (plus PyYAML where a caller needs it), so these scripts stay
usable before the ``blueprint`` package is installed.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

TOOL_NAME = "intelligence-blueprint"
TOOL_VERSION = "0.1.0"
USER_AGENT = f"{TOOL_NAME}/{TOOL_VERSION} (computational research; +local)"

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
INTERIM_DIR = REPO_ROOT / "data" / "interim"
MANIFEST_PATH = RAW_DIR / "MANIFEST.jsonl"


def utc_date() -> str:
    """Current UTC date as ``YYYY-MM-DD``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_now() -> str:
    """Current UTC timestamp as an ISO-8601 string with seconds precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FetchResult:
    """One network response plus the snapshot path it was persisted to."""

    payload: Any
    snapshot: Path
    url: str


def http_get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 45,
    retries: int = 3,
    backoff: float = 2.0,
) -> Any:
    """GET ``url`` and parse the body as JSON, with bounded retries.

    Raises the final :class:`urllib.error.URLError` / :class:`OSError` if every
    attempt fails, so callers can record an explicit failure rather than a guess.
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request_headers.update(headers or {})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as error:  # noqa: PERF203
            last_error = error
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    assert last_error is not None
    raise last_error


def sha256_bytes(data: bytes) -> str:
    """Hex sha256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def write_snapshot(
    registry: str,
    payload: Any,
    *,
    url: str,
    query: dict[str, Any],
    name_hint: str | None = None,
    date: str | None = None,
) -> Path:
    """Persist ``payload`` immutably under ``data/raw/<registry>/<date>/``.

    The filename is derived from the query so that re-running on the same day is
    idempotent: an identical query overwrites nothing and re-registers nothing.
    """
    day = date or utc_date()
    body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = sha256_bytes(json.dumps(query, sort_keys=True).encode("utf-8"))[:12]
    stem = f"{name_hint}_{digest}" if name_hint else digest
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", stem)
    path = RAW_DIR / registry / day / f"{stem}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and sha256_bytes(path.read_bytes()) == sha256_bytes(body):
        return path
    if path.exists():
        # Same query, different content on the same day: keep both, never overwrite.
        path = path.with_name(f"{path.stem}-{sha256_bytes(body)[:8]}.json")
    path.write_bytes(body)
    _manifest_append(
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256_bytes(body),
            "bytes": len(body),
            "registry": registry,
            "retrieved_at": utc_now(),
            "endpoint": url,
            "query": query,
            "tool": f"{TOOL_NAME}/{TOOL_VERSION}",
        }
    )
    return path


def _manifest_append(entry: dict[str, Any]) -> None:
    """Append one manifest line under an exclusive lock (parallel-agent safe)."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n"
    with open(MANIFEST_PATH, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(line)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def iter_snapshots(registry: str) -> list[Path]:
    """All snapshot files for ``registry``, oldest date first (offline rebuilds)."""
    base = RAW_DIR / registry
    if not base.exists():
        return []
    return sorted(base.glob("*/*.json"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write ``rows`` as deterministic JSONL (sorted keys, LF endings)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


_PUNCT = re.compile(r"[^a-z0-9 ]+")
_WS = re.compile(r"\s+")


def normalise_title(title: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace for title matching."""
    text = title.strip().lower().rstrip(".")
    text = _PUNCT.sub(" ", text)
    return _WS.sub(" ", text).strip()


def title_similarity(left: str, right: str) -> float:
    """Similarity in [0, 1] between two titles after normalisation."""
    if not left or not right:
        return 0.0
    return round(SequenceMatcher(None, normalise_title(left), normalise_title(right)).ratio(), 4)


def ncbi_params(extra: dict[str, Any]) -> dict[str, Any]:
    """NCBI E-utilities parameters including tool identification and optional key.

    An API key raises the rate limit from 3 to 10 requests/second. It is read from
    ``NCBI_API_KEY`` and never persisted to any artefact.
    """
    params: dict[str, Any] = {"tool": TOOL_NAME, **extra}
    api_key = os.environ.get("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    return params


def ncbi_sleep() -> None:
    """Respect NCBI rate limits (10/s with a key, 3/s without)."""
    time.sleep(0.11 if os.environ.get("NCBI_API_KEY") else 0.35)


def scrub_query(query: dict[str, Any]) -> dict[str, Any]:
    """Remove credentials from a query dict before it reaches the manifest."""
    return {k: v for k, v in query.items() if k not in {"api_key", "email"}}
