#!/usr/bin/env python3
"""Sprint 5A (Goal A) — fetch open single-nucleus brain eQTL summary statistics for the Gate-C loci.

Two open (CC-BY-4.0, no login) Zenodo resources:

1. Bryois et al. 2022 Nat Neurosci — record 10.5281/zenodo.7276971 (concept 10.5281/zenodo.5543734).
   One gzip file per cell type x chromosome (8 cell types + 'pb' tissue-like pseudo-bulk added Feb 2023),
   columns (no header): Gene_id (SYMBOL_ENSG), SNP_id (rsID), distance to TSS, nominal p, beta.
   snp_pos.txt.gz: SNP, SNP_id_hg38, SNP_id_hg19, effect_allele, other_allele, MAF — beta is per copy of
   effect_allele. Only the chromosomes carrying a Gate-C locus are downloaded (whole files; md5 verified
   against the Zenodo record, sha256 recorded).

2. SingleBrain (Humphrey/Raj lab 2025) — record 10.5281/zenodo.14908182: mmQTL meta-analysis of Fujita
   (ROSMAP), Mathys (ROSMAP), Gabitto (SEA-AD) and Bryois (Roche) snRNA-seq eQTLs; 983 samples /
   757 unique donors; hg38; BGZF-compressed, sorted by chr/pos, ~4.5 GB per major cell type.
   Downloading 7 x 4.5 GB at the ~1.6 MB/s Zenodo allows is impractical, so the BGZF structure is used:
   byte-range probes locate each locus window (GRCh38 lead +/- 500 kb, from the Sprint-4 eQTL Catalogue
   provenance), and only those byte ranges are fetched and decompressed. Whole-file sha256 is therefore
   NOT available for SingleBrain; each fetched range is recorded with its byte offsets and sha256, and
   the Zenodo md5 of the whole file is recorded as the file identity.

Outputs (gitignored): data/interim/sprint5a/bryois/*.gz, data/interim/sprint5a/singlebrain/<ct>__<locus>.tsv
Provenance (tracked): data/raw/sprint5a/bryois2022/PROVENANCE.json, data/raw/sprint5a/singlebrain/PROVENANCE.json
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import struct
import sys
import threading
import time
import urllib.request
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INTERIM = REPO / "data" / "interim" / "sprint5a"
RAW = REPO / "data" / "raw" / "sprint5a"
S4_PROV = REPO / "data" / "raw" / "sprint4" / "eqtl_catalogue" / "PROVENANCE.json"

BRYOIS_RECORD = "7276971"
BRYOIS_CELLTYPES = ["Astrocytes", "Endothelial.cells", "Excitatory.neurons", "Inhibitory.neurons", "Microglia",
                    "Oligodendrocytes", "OPCs...COPs", "Pericytes", "pb"]
SB_RECORD = "14908182"
SB_CELLTYPES = ["Ext", "IN", "Ast", "OD", "OPC", "MG", "End"]
PRIORITY = {"L51327", "L64067", "L91869", "L51460", "L1803", "L3123", "L2131", "L60412", "L1630", "L3760", "L64116",
            "L7009", "L9975", "L100132074", "L7324", "L64288", "L257194", "L79922", "L1565", "L319", "L65265",
            "L55168"}
UA = {"User-Agent": "HI-sprint5a-research/1.0 (academic; urllib)"}


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def zenodo_files(record: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(f"https://zenodo.org/api/records/{record}", headers=UA),
                                timeout=120) as r:
        d = json.load(r)
    return {f["key"]: f for f in d["files"]}, d


def loci_windows() -> list[dict]:
    items = json.loads(S4_PROV.read_text())["loci"]["items"]
    out = []
    for it in items:
        c, rng = it["window_grch38"].split(":")
        a, b = rng.split("-")
        out.append({"locus_id": it["locus_id"], "chr": str(it["chr"]), "start38": int(a), "end38": int(b),
                    "lead_snp": it["lead_snp"], "lead_pos_grch37": int(it["lead_pos_grch37"]),
                    "lead_pos_grch38": int(it["lead_pos_grch38"])})
    return out


# ------------------------------------------------------------------------------------------------ Bryois
def _download(url: str, dest: Path, md5_expected: str | None) -> dict:
    t0 = utc()
    h256, hmd5, n = hashlib.sha256(), hashlib.md5(), 0
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(5):
        try:
            h256, hmd5, n = hashlib.sha256(), hashlib.md5(), 0
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(tmp, "wb") as fh:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    fh.write(b)
                    h256.update(b)
                    hmd5.update(b)
                    n += len(b)
            break
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, flush=True)
            time.sleep(10 * (attempt + 1))
    else:
        return {"url": url, "error": "download failed after 5 attempts", "utc_start": t0}
    md5 = hmd5.hexdigest()
    ok = md5_expected is None or md5_expected.split(":")[-1] == md5
    if ok:
        tmp.rename(dest)
    return {"url": url, "path": str(dest.relative_to(REPO)), "utc_start": t0, "utc_end": utc(), "bytes": n,
            "sha256": h256.hexdigest(), "md5": md5, "md5_zenodo": md5_expected, "md5_ok": ok}


def fetch_bryois(workers: int) -> None:
    files, rec = zenodo_files(BRYOIS_RECORD)
    chroms = sorted({w["chr"] for w in loci_windows()}, key=int)
    want = ["snp_pos.txt.gz"] + [f"{ct}.{c}.gz" for ct in BRYOIS_CELLTYPES for c in chroms]
    dest_dir = INTERIM / "bryois"
    dest_dir.mkdir(parents=True, exist_ok=True)
    prov_path = RAW / "bryois2022" / "PROVENANCE.json"
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    done = {f["path"]: f for f in prov.get("files", []) if f.get("md5_ok")}
    todo = []
    for k in want:
        dest = dest_dir / k
        if str(dest.relative_to(REPO)) in done and dest.exists():
            continue
        todo.append((files[k]["links"]["self"], dest, files[k]["checksum"]))
    print(len(want), "wanted;", len(todo), "to download", flush=True)
    lock = threading.Lock()
    results = list(done.values())

    def save():
        prov.update({
            "resource": "Bryois et al. 2022 Nat Neurosci 25:1104 — cell-type-specific cis-eQTLs, 8 brain cell types",
            "zenodo_record": f"https://zenodo.org/records/{BRYOIS_RECORD}", "doi": rec.get("doi"),
            "concept_doi": rec.get("conceptdoi"), "license": rec["metadata"].get("license"),
            "record_title": rec["metadata"]["title"],
            "selection": f"snp_pos.txt.gz + {len(BRYOIS_CELLTYPES)} cell types (incl. pb pseudo-bulk) x chromosomes {chroms}",
            "columns": "Gene_id SNP_id distance_to_TSS nominal_p beta (no header); beta per copy of snp_pos effect_allele",
            "build": "snp_pos.txt has both hg38 and hg19 positions; Davies is GRCh37 — joined on rsID, hg19 checked",
            "files": sorted(results, key=lambda x: x.get("path", "")),
        })
        prov_path.write_text(json.dumps(prov, indent=1) + "\n")

    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(_download, u, d, m): d for u, d, m in todo}
        for f in cf.as_completed(futs):
            r = f.result()
            with lock:
                results.append(r)
                save()
            print(r.get("path"), r.get("bytes"), r.get("md5_ok"), r.get("error", ""), flush=True)
    save()


# ------------------------------------------------------------------------------------------- SingleBrain
BGZF_MAGIC = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff\x06\x00BC\x02\x00"


class RateLimited:
    """<= max_per_min requests per minute to Zenodo (limit advertised: 133/min)."""

    def __init__(self, max_per_min: int = 100):
        self.gap = 60.0 / max_per_min
        self.last = 0.0
        self.lock = threading.Lock()
        self.n = 0

    def get(self, url: str, start: int, end: int) -> bytes:
        for attempt in range(8):
            with self.lock:
                wait = self.last + self.gap - time.time()
                if wait > 0:
                    time.sleep(wait)
                self.last = time.time()
                self.n += 1
            try:
                req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
                with urllib.request.urlopen(req, timeout=600) as r:
                    return r.read()
            except Exception as e:  # noqa: BLE001
                print("range retry", start, end, e, flush=True)
                time.sleep(15 * (attempt + 1))
        raise RuntimeError(f"range {start}-{end} failed")


def _blocks(buf: bytes, first: int):
    """Yield (offset, decompressed) for complete BGZF blocks in buf starting at the first magic >= first."""
    i = buf.find(BGZF_MAGIC, first)
    while i >= 0 and i + 18 <= len(buf):
        bsize = struct.unpack("<H", buf[i + 16:i + 18])[0] + 1
        if i + bsize > len(buf):
            return
        try:
            data = zlib.decompress(buf[i + 18:i + bsize - 8], -15)
        except zlib.error:
            i = buf.find(BGZF_MAGIC, i + 1)
            continue
        yield i, bsize, data
        i += bsize
        if buf[i:i + 16] != BGZF_MAGIC:
            i = buf.find(BGZF_MAGIC, i)


def chr_key(c: str) -> int:
    c = c.replace("chr", "")
    return {"X": 23, "Y": 24, "M": 25, "MT": 25}.get(c, int(c) if c.isdigit() else 99)


def probe(client: RateLimited, url: str, off: int, size: int, cache: dict):
    """(block_offset, (chr_key, pos)) of the first complete line in the first full BGZF block at/after off."""
    if off in cache:
        return cache[off]
    buf = client.get(url, off, min(size - 1, off + 262143))
    for i, _, data in _blocks(buf, 0):
        lines = data.split(b"\n")
        for ln in lines[1:-1]:          # skip the partial first line and partial last line
            f = ln.split(b"\t")
            if len(f) > 4 and f[2].startswith(b"chr"):
                cache[off] = (off + i, (chr_key(f[2].decode()), int(f[3])))
                return cache[off]
    cache[off] = (off, None)
    return cache[off]


def locate(client, url, size, target, cache, lo=0, hi=None, res=1 << 20):
    """Largest probed block offset whose first record is < target (chr_key, pos) — a safe start."""
    hi = size if hi is None else hi
    while hi - lo > res:
        mid = (lo + hi) // 2
        _, key = probe(client, url, mid, size, cache)
        if key is None or key >= target:
            hi = mid
        else:
            lo = mid
    return lo


def fetch_singlebrain(cts: list[str], only: list[str] | None, rate: int) -> None:
    files, rec = zenodo_files(SB_RECORD)
    wins = loci_windows()
    if only:
        wins = [w for w in wins if w["locus_id"] in only]
    # priority loci (L1/L2 strata + named Goal-B loci) first, then the rest in genome order
    wins.sort(key=lambda w: (w["locus_id"] not in PRIORITY, chr_key(w["chr"]), w["start38"]))
    out_dir = INTERIM / "singlebrain"
    out_dir.mkdir(parents=True, exist_ok=True)
    prov_path = RAW / "singlebrain" / "PROVENANCE.json"
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {"ranges": []}
    client = RateLimited(rate)
    state: dict = {}

    def ct_state(ct):
        if ct not in state:
            key = f"{ct}_eqtl_full_assoc.tsv.gz"
            meta = files[key]
            url, size = meta["links"]["self"], int(meta["size"])
            cache: dict = {}
            # coarse grid first (shared by all windows of this file), then refine per window
            for g in [int(size * k / 64) for k in range(64)]:
                probe(client, url, g, size, cache)
            pts = sorted((o, k) for o, (bo, k) in cache.items() if k is not None)
            state[ct] = (key, meta, url, size, cache, pts)
        return state[ct]

    for w in wins:  # window-major so priority loci finish for every cell type first
        for ct in cts:
            dest = out_dir / f"{ct}__{w['locus_id']}.tsv"
            if dest.exists() and dest.stat().st_size > 0:
                continue
            key, meta, url, size, cache, pts = ct_state(ct)
            ck = chr_key(w["chr"])
            t_lo, t_hi = (ck, w["start38"]), (ck, w["end38"] + 1)
            lo = max([o for o, k in pts if k < t_lo] or [0])
            hi = min([o for o, k in pts if k > t_hi] or [size])
            start = locate(client, url, size, t_lo, cache, lo, hi, res=1 << 19)
            hi2 = min([o for o, (bo, k) in cache.items() if k is not None and k > t_hi] or [size])
            end = hi2 + 262144
            t0 = utc()
            rows, nbytes = [], 0
            h = hashlib.sha256()
            pos = start
            header = None
            carry = b""
            done = False
            while pos < min(end, size) and not done:
                chunk_end = min(size - 1, pos + (3 << 20) - 1)
                buf = client.get(url, pos, chunk_end)
                h.update(buf)
                nbytes += len(buf)
                last = 0
                for i, bsize, data in _blocks(buf, 0 if pos > start else 0):
                    last = i + bsize
                    text = carry + data
                    lines = text.split(b"\n")
                    carry = lines.pop()
                    for ln in lines:
                        f = ln.split(b"\t")
                        if len(f) < 5 or not f[2].startswith(b"chr"):
                            if f and f[0] == b"feature":
                                header = ln
                            continue
                        k = (chr_key(f[2].decode()), int(f[3]))
                        if k > t_hi:
                            done = True
                            break
                        if k >= t_lo:
                            rows.append(ln)
                    if done:
                        break
                if last == 0:
                    break
                pos += last
            hdr = (b"feature\tvariant_id\tchr\tpos\tref\talt\tAllele\tbeta_tissue_0\tsd_tissue_0\tz_tissue_0\t"
                   b"beta_tissue_1\tsd_tissue_1\tz_tissue_1\tbeta_tissue_2\tsd_tissue_2\tz_tissue_2\tbeta_tissue_3\t"
                   b"sd_tissue_3\tz_tissue_3\tfixed_beta\tfixed_sd\tfixed_z\tRandom_Z\tFixed_P\tRandom_P\tFixed_bonf\t"
                   b"Random_bonf\tFixed_FDR\tRandom_FDR")
            dest.write_bytes(hdr + b"\n" + b"\n".join(rows) + (b"\n" if rows else b""))
            complete = done  # True only if a record past the window end was seen (window fully covered)
            prov["ranges"].append({"file": key, "url": url, "zenodo_md5_whole_file": meta["checksum"],
                                   "whole_file_bytes": size, "locus_id": w["locus_id"],
                                   "window_grch38": f"{w['chr']}:{w['start38']}-{w['end38']}",
                                   "byte_start": start, "byte_end_fetched": pos, "bytes_fetched": nbytes,
                                   "sha256_of_fetched_bytes": h.hexdigest(), "utc_start": t0, "utc_end": utc(),
                                   "rows_in_window": len(rows), "window_end_reached": complete,
                                   "output": str(dest.relative_to(REPO))})
            prov.update({"resource": "SingleBrain snRNA-seq eQTL meta-analysis (mmQTL; Fujita+Mathys [ROSMAP], "
                                     "Gabitto [SEA-AD], Bryois [Roche]); 983 samples / 757 unique donors",
                         "zenodo_record": f"https://zenodo.org/records/{SB_RECORD}", "doi": rec.get("doi"),
                         "license": rec["metadata"].get("license"),
                         "access_method": "HTTP byte ranges on the BGZF file (whole-file sha256 not computed; "
                                          "Zenodo md5 recorded as file identity)",
                         "requests_made": client.n})
            prov_path.write_text(json.dumps(prov, indent=1) + "\n")
            print(ct, w["locus_id"], len(rows), "rows", nbytes, "bytes", "complete" if complete else "INCOMPLETE",
                  "requests", client.n, flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("what", choices=["bryois", "singlebrain"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--celltypes", default=",".join(SB_CELLTYPES))
    ap.add_argument("--loci", default="")
    ap.add_argument("--rate", type=int, default=90)
    a = ap.parse_args(argv)
    if a.what == "bryois":
        fetch_bryois(a.workers)
    else:
        fetch_singlebrain(a.celltypes.split(","), [x for x in a.loci.split(",") if x] or None, a.rate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
