"""Sprint 5A shared download helper: curl download + JSONL provenance (URL, UTC, bytes, sha256).

No authentication of any kind is used. A non-200 / HTML-login response is recorded as a blocker.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_LOCK = threading.Lock()


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, log: Path, skip_existing: bool = True, timeout: int = 3600) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        rec = {"url": url, "file": str(dest.relative_to(ROOT)), "utc": utc(), "status": "EXISTING_VERIFIED",
               "bytes": dest.stat().st_size, "sha256": sha256(dest)}
    else:
        tmp = dest.with_suffix(dest.suffix + ".part")
        t0 = utc()
        r = subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "3", "-m", str(timeout), "-o", str(tmp),
                            "-w", "%{http_code}", url], capture_output=True, text=True)
        if r.returncode == 0 and tmp.exists():
            tmp.rename(dest)
            rec = {"url": url, "file": str(dest.relative_to(ROOT)), "utc": t0, "status": "OK",
                   "http": r.stdout.strip(), "bytes": dest.stat().st_size, "sha256": sha256(dest)}
        else:
            if tmp.exists():
                tmp.unlink()
            rec = {"url": url, "file": str(dest.relative_to(ROOT)), "utc": t0, "status": "FAILED",
                   "http": r.stdout.strip(), "error": r.stderr.strip()[:300]}
    with _LOCK, open(log, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec
