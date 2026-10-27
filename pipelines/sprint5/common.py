"""Shared paths and helpers for Sprint 5 (causal cognition gene resolution).

Sprint 5 reads Sprint-3/4 outputs as inputs and never rewrites them. Every evidence class,
ranking stratum and gate used to label a candidate is fixed in ``research/sprint5/protocol.md``
(and its machine-readable twin ``research/sprint5/protocol_rules.json``) before the new data
streams were integrated; :func:`load_rules` refuses to return if that JSON's sha256 differs from
the last hash recorded in the protocol.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "pipelines" / "sprint4"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import os as _os
# Sprint 5A reruns this frozen pipeline into its own directories (S5_OUT / S5_DATA); defaults = Sprint 5.
OUT = Path(_os.environ.get("S5_OUT", REPO_ROOT / "reports" / "sprint5"))
DATA = Path(_os.environ.get("S5_DATA", REPO_ROOT / "data" / "sprint5"))
S5A = _os.environ.get("S5A_INTEGRATION") == "1"   # enables the Sprint-5A-only inputs (within-family, sc-eQTL coloc)
RAW = REPO_ROOT / "data" / "raw" / "sprint5"
WORK = REPO_ROOT / "data" / "interim" / "sprint5"
RESEARCH = REPO_ROOT / "research" / "sprint5"
PROTOCOL_MD = RESEARCH / "protocol.md"
RULES_JSON = RESEARCH / "protocol_rules.json"

S4_OUT = REPO_ROOT / "reports" / "sprint4"
S4_DATA = REPO_ROOT / "data" / "sprint4"
S4_WORK = REPO_ROOT / "data" / "interim" / "sprint4"
GT_DATA = REPO_ROOT / "data" / "gene_tournament"
GT_OUT = REPO_ROOT / "reports" / "gene_tournament"
DAVIES_GENES_OUT = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "davies2018_10kb.genes.out"
GENE_LOC = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "NCBI37.3.gene.loc"

R_ENV = Path(os.environ.get("COGNITION_R_ENV", str(REPO_ROOT / "data/external/r-env")))
RSCRIPT = R_ENV / "bin" / "Rscript"
TABIX = R_ENV / "bin" / "tabix"

for d in (OUT, DATA, RAW, WORK, RESEARCH, OUT / "gene_dossiers"):
    d.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


_HASH_RX = re.compile(r"RULES_JSON_SHA256:\s*([0-9a-f]{64})")


def recorded_rules_hash() -> str | None:
    if not PROTOCOL_MD.exists():
        return None
    found = _HASH_RX.findall(PROTOCOL_MD.read_text())
    return found[-1] if found else None


def load_rules() -> dict:
    """Return the frozen Sprint-5 rules; raise if the JSON changed after the recorded freeze."""
    rec = recorded_rules_hash()
    got = sha256_file(RULES_JSON)
    if rec != got:
        raise RuntimeError(f"protocol_rules.json sha256 {got} != recorded {rec}; amend the protocol "
                           "with a dated block and a new RULES_JSON_SHA256 line instead of editing silently")
    return json.loads(RULES_JSON.read_text())


def http_json(url: str, payload: dict | None = None, headers: dict | None = None, tries: int = 4,
              timeout: int = 120):
    """GET (payload None) or POST JSON with retries; stdlib only (the venv has no requests)."""
    import urllib.error
    import urllib.request
    h = {"Accept": "application/json", "Content-Type": "application/json",
         "User-Agent": "humanintelligence-sprint5/1.0 (computational research)", **(headers or {})}
    data = json.dumps(payload).encode() if payload is not None else None
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300]!r}"
            if e.code in (429,) or e.code >= 500:
                time.sleep(3 * (i + 1) + float(e.headers.get("Retry-After", 0) or 0))
                continue
            raise RuntimeError(f"{url}: {last}") from e
        except Exception as e:  # noqa: BLE001 - network retry loop
            last = repr(e)
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {last}")
