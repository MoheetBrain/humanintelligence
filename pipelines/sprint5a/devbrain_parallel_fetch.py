#!/usr/bin/env python3
"""Sprint 5A — download large OPEN Zenodo files (record 12729266, Wen et al. 2024) with parallel HTTP Range
requests (single-connection throughput ~0.6 MB/s), verify against the Zenodo md5, record sha256/bytes, filter
to the query Ensembl gene IDs, then DELETE the full file (only the filtered subset is kept).

Usage: python pipelines/sprint5a/devbrain_parallel_fetch.py <file-name> [...]
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_util import ROOT, utc  # noqa: E402

REC = "https://zenodo.org/api/records/12729266"
DEST = ROOT / "data/interim/sprint5a/psychencode_dev"
LOG = DEST / "download_log.jsonl"
NPART = 2  # post-reboot: machine shared with MAGMA (<= 3 workers)


def meta() -> dict:
    out = subprocess.run(["curl", "-sS", "-m", "60", REC], capture_output=True, text=True, check=True).stdout
    return {f["key"]: f for f in json.loads(out)["files"]}


def get_part(url: str, path: Path, a: int, b: int) -> None:
    for _ in range(5):
        subprocess.run(["curl", "-sS", "-L", "--retry", "5", "-r", f"{a}-{b}", "-o", str(path), url], check=False)
        if path.exists() and path.stat().st_size == b - a + 1:
            return
    raise RuntimeError(f"part failed {path}")


def main(files: list[str]) -> None:
    m = meta()
    genes = set((DEST / "query_gene_ids.txt").read_text().split())
    for fn in files:
        size, md5 = m[fn]["size"], m[fn]["checksum"].split(":")[1]
        url = f"{REC}/files/{fn}/content"
        full = DEST / fn
        t0 = utc()
        if not (full.exists() and full.stat().st_size == size):
            step = size // NPART + 1
            parts = [(DEST / f".{fn}.part{i:02d}", i * step, min(size, (i + 1) * step) - 1) for i in range(NPART)]
            with ThreadPoolExecutor(NPART) as ex:
                list(ex.map(lambda p: get_part(url, *p), parts))
            with open(full, "wb") as out:
                for p, _, _ in parts:
                    out.write(p.read_bytes())
                    p.unlink()
        h5, h256 = hashlib.md5(), hashlib.sha256()
        with open(full, "rb") as fh:
            for ch in iter(lambda: fh.read(1 << 22), b""):
                h5.update(ch)
                h256.update(ch)
        ok = h5.hexdigest() == md5
        dest = DEST / f"filtered__{fn.replace('.gz', '')}"
        n = 0
        opener = gzip.open if fn.endswith(".gz") else open
        # grep is far faster than python for 100M+ lines
        # awk hash lookup on column 1 (BSD grep -F -w -f is CPU-bound on multi-GB input)
        cmd = (f"{'gunzip -c' if fn.endswith('.gz') else 'cat'} '{full}' | LC_ALL=C awk "
               f"'NR==FNR{{g[$1]; next}} ($1 in g)' '{DEST / 'query_gene_ids.txt'}' - > '{dest}'")
        subprocess.run(cmd, shell=True, check=False)
        with opener(full, "rt") as fh:
            header = fh.readline().rstrip("\n")
        n = sum(1 for _ in open(dest))
        rec = {"url": url, "file": str(dest.relative_to(ROOT)), "utc": t0, "status": "OK_PARALLEL_RANGE_THEN_FILTERED",
               "bytes": size, "zenodo_md5": md5, "md5_match": ok, "sha256": h256.hexdigest(),
               "first_line_of_full_file": header[:200],
               "stored": f"rows for {len(genes)} query Ensembl gene IDs only ({n} rows); full file deleted after hashing",
               "filtered_sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
        with open(LOG, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        full.unlink()
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
