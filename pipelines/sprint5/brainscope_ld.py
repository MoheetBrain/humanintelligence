"""LD helpers for the brainSCOPE lookup: hg38 variant -> rsID (Ensembl REST) and r^2 in 1000G EUR (GRCh37).

* rsID mapping: GET https://rest.ensembl.org/overlap/region/human/<chr>:<pos>-<pos>?feature=variation
  (GRCh38), keeping rs IDs whose allele set contains both REF and ALT. Responses cached in
  data/interim/sprint5/brainscope/ensembl_rsid_cache.json.
* r^2: genotypes read directly from the PLINK .bed of the 1000 Genomes EUR reference used by MAGMA
  (intelligence-codex, read-only; 503 individuals, GRCh37). Pearson r^2 of allele dosages, missing excluded.
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

try:
    import common as C  # type: ignore
except ImportError:  # pragma: no cover
    from . import common as C  # type: ignore

BFILE = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/genetics_tools/"
             "reference/g1000_eur")
CACHE = C.WORK / "brainscope" / "ensembl_rsid_cache.json"


def _get(url: str, tries: int = 4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (k + 1))
    return None


def hg38_to_rsid(variants: list[tuple[str, int, str, str]]) -> dict[str, str | None]:
    """variants: (chr, pos, ref, alt) -> {'chr:pos:ref:alt': rsid or None}."""
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [v for v in variants if f"{v[0]}:{v[1]}:{v[2]}:{v[3]}" not in cache]

    def one(v):
        c, p, ref, alt = v
        js = _get(f"https://rest.ensembl.org/overlap/region/human/{c}:{p}-{p}?feature=variation")
        time.sleep(0.07)
        rs = None
        if js:
            for x in js:
                al = set(x.get("alleles") or [])
                if x.get("id", "").startswith("rs") and ref in al and alt in al and x.get("start") == p:
                    rs = x["id"]
                    break
        return f"{c}:{p}:{ref}:{alt}", rs

    with ThreadPoolExecutor(max_workers=6) as ex:
        for k, rs in ex.map(one, todo):
            cache[k] = rs
    CACHE.write_text(json.dumps(cache))
    return {f"{v[0]}:{v[1]}:{v[2]}:{v[3]}": cache.get(f"{v[0]}:{v[1]}:{v[2]}:{v[3]}") for v in variants}


class Plink:
    def __init__(self, bfile: Path = BFILE):
        self.bfile = bfile
        self.n = sum(1 for _ in open(f"{bfile}.fam"))
        self.bpv = (self.n + 3) // 4
        self.bed = np.memmap(f"{bfile}.bed", dtype=np.uint8, mode="r")
        assert self.bed[0] == 0x6C and self.bed[1] == 0x1B and self.bed[2] == 0x01, "not a SNP-major .bed"
        self.index: dict[str, tuple[int, str, str, str, int]] = {}

    def load_rsids(self, rsids: set[str]) -> None:
        """Index bim rows for the requested rsIDs (awk scan of the 20M-row bim)."""
        need = sorted(r for r in rsids if r and r not in self.index)
        if not need:
            return
        tmp = C.WORK / "brainscope" / "_ld_rsids.txt"
        tmp.write_text("\n".join(need) + "\n")
        cmd = ["awk", "BEGIN{FS=\"\\t\"} NR==FNR{want[$1]=1; next} ($2 in want){print FNR-1\"\\t\"$0}",
               str(tmp), f"{self.bfile}.bim"]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            i, c, rs, _, bp, a1, a2 = line.split("\t")
            self.index.setdefault(rs, (int(i), c, a1, a2, int(bp)))

    def dosage(self, rsid: str) -> np.ndarray | None:
        if rsid not in self.index:
            return None
        i = self.index[rsid][0]
        off = 3 + i * self.bpv
        raw = np.asarray(self.bed[off: off + self.bpv])
        codes = np.unpackbits(raw[:, None], axis=1, bitorder="little").reshape(-1, 4, 2)
        g = (codes[:, :, 0] + 2 * codes[:, :, 1]).reshape(-1)[: self.n]  # 0 homA1, 1 missing, 2 het, 3 homA2
        d = np.full(self.n, np.nan)
        d[g == 0] = 2.0
        d[g == 2] = 1.0
        d[g == 3] = 0.0
        return d

    def r2(self, a: str, b: str) -> float | None:
        if a == b:
            return 1.0
        x, y = self.dosage(a), self.dosage(b)
        if x is None or y is None:
            return None
        ok = ~np.isnan(x) & ~np.isnan(y)
        if ok.sum() < 50 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
            return None
        return float(np.corrcoef(x[ok], y[ok])[0, 1] ** 2)
