#!/usr/bin/env python3
"""Sprint 5A — brainSCOPE gap-fill: fetch the public files Sprint 5 did not download, and re-verify (sha256)
the Sprint-5 files that are reused. Never downloads snrna_expr_matrices (7.8 GB).

New files -> data/interim/sprint5a/brainscope/ (gitignored); log -> download_log.jsonl there.
Usage: python pipelines/sprint5a/brainscope_gapfill_fetch.py [--verify-only]
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_util import ROOT, fetch, sha256, utc  # noqa: E402

BASE = "https://brainscope.gersteinlab.org/data"
DEST = ROOT / "data/interim/sprint5a/brainscope"
LOG = DEST / "download_log.jsonl"
S5 = ROOT / "data/interim/sprint5/brainscope"
SIG_CT = ["Astro", "Chandelier__Pvalb", "L2.3.IT", "L4.IT", "L5.6.NP", "L5.IT", "L6.CT", "L6.IT", "L6b",
          "Lamp5.Lhx6", "Lamp5", "Micro.PVM", "OPC", "Oligo", "PC", "Sst__Sst.Chodl", "Vip"]


def manifest():
    m = [(f"{BASE}/meta_qtls/metaQTLs.txt", "meta_qtls/metaQTLs.txt"),
         (f"{BASE}/bcCRE/adult_bcCREs.bed", "bcCRE/adult_bcCREs.bed"),
         (f"{BASE}/validation/crispr_validation_results.xlsx", "validation/crispr_validation_results.xlsx"),
         (f"{BASE}/validation/starrseq_enhancers_merged.bed", "validation/starrseq_enhancers_merged.bed")]
    for ct in SIG_CT:
        m.append((f"{BASE}/conditional_qtls/conditional.{ct}.txt", f"conditional_qtls/conditional.{ct}.txt"))
    return m


def verify_sprint5():
    """Re-hash every Sprint-5 file listed in its download log; report mismatches."""
    out = []
    for line in open(S5 / "download_log.jsonl"):
        r = json.loads(line)
        p = S5 / r["file"]
        if r.get("status") != "OK" or not p.exists() or "sha256" not in r:
            out.append({**r, "verify": "MISSING_OR_NOT_STORED" if not p.exists() else "NO_HASH"})
            continue
        if r.get("stored", "full file") != "full file":
            out.append({"file": r["file"], "verify": "REDUCED_FILE_SKIPPED"})
            continue
        h = sha256(p)
        out.append({"file": r["file"], "url": r["url"], "verify": "MATCH" if h == r["sha256"] else "MISMATCH",
                    "sha256": h})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    ver = verify_sprint5()
    (DEST / "sprint5_reverify.json").write_text(json.dumps({"utc": utc(), "records": ver}, indent=1))
    from collections import Counter
    print("sprint5 re-verify:", Counter(v["verify"] for v in ver))
    if not a.verify_only:
        with ThreadPoolExecutor(8) as ex:
            for r in ex.map(lambda t: fetch(t[0], DEST / t[1], LOG), manifest()):
                print(r["status"], r["file"], r.get("bytes"))
