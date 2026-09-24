#!/usr/bin/env python3
"""Sprint 5A (agent A) — post-reboot integrity check: re-hash every file recorded in the agent-A download logs and
compare sha256 + bytes with the log; also re-verify the Sprint-5 brainSCOPE files. Writes
data/interim/sprint5a/agentA_reverify.json. Uses <= 3 worker threads (machine shared with MAGMA)."""
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I = ROOT / "data/interim/sprint5a"
LOGS = [I / "brainscope/download_log.jsonl", I / "gtex_v11/download_log.jsonl", I / "gencode/download_log.jsonl",
        I / "liftover/download_log.jsonl", I / "psychencode_dev/download_log.jsonl"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 22), b""):
            h.update(ch)
    return h.hexdigest()


def check(rec):
    p = ROOT / rec["file"]
    if not p.exists():
        return {**rec, "verify": "MISSING"}
    if rec.get("status", "").startswith("OK_PARALLEL"):  # filtered subset: compare filtered sha
        return {"file": rec["file"], "verify": "MATCH" if sha(p) == rec["filtered_sha256"] else "MISMATCH"}
    if "sha256" not in rec:
        return {"file": rec["file"], "verify": "NO_HASH_IN_LOG"}
    ok = p.stat().st_size == rec["bytes"] and sha(p) == rec["sha256"]
    return {"file": rec["file"], "verify": "MATCH" if ok else "MISMATCH", "bytes": p.stat().st_size}


if __name__ == "__main__":
    recs = []
    for lg in LOGS:
        for x in lg.read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                if r.get("status", "") in ("OK", "EXISTING_VERIFIED", "OK_TAR_MEMBER_BY_RANGE") or r.get("status", "").startswith("OK_PARALLEL"):
                    recs.append(r)
    latest = {}
    for r in recs:
        latest[r["file"]] = r
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(check, latest.values()))
    from collections import Counter
    print(Counter(r["verify"] for r in res))
    for r in res:
        if r["verify"] != "MATCH":
            print(r["verify"], r["file"])
    (I / "agentA_reverify.json").write_text(json.dumps(res, indent=1))
