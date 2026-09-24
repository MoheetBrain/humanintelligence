#!/usr/bin/env python3
"""Sprint 5A — GTEx V11 (released 2026-01-15, GENCODE v47) OPEN files from the public GCS bucket adult-gtex.

The per-release tar archives are not indexed, so the tar headers are walked with HTTP Range requests (512-byte
reads) to build a member index, and ONLY the brain-tissue members are fetched by byte range. The index (member
name, offset, size) and the archive's GCS md5 are recorded; each fetched member gets its own sha256.
All-pairs (nominal) statistics are in a REQUESTER-PAYS bucket (gtex-resources) -> recorded as a blocker.

Outputs: data/interim/sprint5a/gtex_v11/ (gitignored), download_log.jsonl there.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_util import ROOT, fetch, utc  # noqa: E402

GCS = "https://storage.googleapis.com/adult-gtex/"
DEST = ROOT / "data/interim/sprint5a/gtex_v11"
LOG = DEST / "download_log.jsonl"
TARS = ["bulk-qtl/v11/single-tissue-cis-qtl/GTEx_Analysis_v11_eQTL.tar",
        "bulk-qtl/v11/single-tissue-cis-qtl/GTEx_Analysis_v11_sQTL.tar"]
WHOLE = ["bulk-qtl/v11/susie-qtl/GTEx_Analysis_v11_eQTL_SuSiE.tar",
         "bulk-qtl/v11/single-tissue-cis-qtl/README_eQTL_v11.txt",
         "bulk-gex/v11/rna-seq/GTEx_Analysis_2025-08-22_v11_RNASeQCv2.4.3_gene_median_tpm.gct.gz"]


def rng(url: str, start: int, end: int) -> bytes:
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def tar_index(url: str) -> list[dict]:
    out, off = [], 0
    while True:
        h = rng(url, off, off + 511)
        if len(h) < 512 or h == b"\0" * 512:
            break
        name = h[0:100].rstrip(b"\0").decode()
        prefix = h[345:500].rstrip(b"\0").decode()
        size = int(h[124:136].rstrip(b"\0 ").decode() or "0", 8)
        typ = h[156:157]
        if typ == b"L":  # GNU long name: next block(s) hold the name
            data = rng(url, off + 512, off + 512 + size - 1)
            longname = data.rstrip(b"\0").decode()
            off += 512 + ((size + 511) // 512) * 512
            h = rng(url, off, off + 511)
            size = int(h[124:136].rstrip(b"\0 ").decode() or "0", 8)
            name, prefix, typ = longname, "", h[156:157]
        full = f"{prefix}/{name}" if prefix else name
        out.append({"name": full, "data_offset": off + 512, "size": size, "type": typ.decode(errors="replace")})
        off += 512 + ((size + 511) // 512) * 512
    return out


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for rel in WHOLE:
        r = fetch(GCS + rel, DEST / Path(rel).name, LOG)
        print(r["status"], r["file"], r.get("bytes"))
    for rel in TARS:
        url = GCS + rel
        idx = tar_index(url)
        (DEST / (Path(rel).stem + ".tar_index.json")).write_text(json.dumps({"utc": utc(), "url": url, "members": idx}, indent=1))
        for m in idx:
            if "Brain" not in m["name"] or m["size"] == 0:
                continue
            p = DEST / Path(rel).stem / Path(m["name"]).name
            p.parent.mkdir(parents=True, exist_ok=True)
            t0 = utc()
            if not (p.exists() and p.stat().st_size == m["size"]):
                data = rng(url, m["data_offset"], m["data_offset"] + m["size"] - 1)
                assert len(data) == m["size"], (m["name"], len(data))
                p.write_bytes(data)
            rec = {"url": url, "member": m["name"], "byte_range": [m["data_offset"], m["data_offset"] + m["size"] - 1],
                   "file": str(p.relative_to(ROOT)), "utc": t0, "status": "OK_TAR_MEMBER_BY_RANGE",
                   "bytes": m["size"], "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            with open(LOG, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(rec["status"], m["name"], m["size"])


if __name__ == "__main__":
    main()
