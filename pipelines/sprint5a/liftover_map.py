"""Sprint 5A — offline hg38 -> hg19 point liftover (UCSC hg38ToHg19.over.chain.gz) and hg38 variant ->
1000G EUR rsID mapping by (chr, hg19 pos, alleles) against the GRCh37 PLINK .bim. Replaces Ensembl REST
(which was timing out, 2026-09-24 ~09:45 UTC). Strand: 1000G .bim alleles are forward-strand, hg38 REF/ALT are
forward-strand; alleles must match as a set (a chain block on the '-' strand is complemented)."""
from __future__ import annotations

import bisect
import gzip
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAIN = ROOT / "data/interim/sprint5a/liftover/hg38ToHg19.over.chain.gz"
BIM = Path("data/external/x01/genetics_tools/"
           "reference/g1000_eur.bim")
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}


class Lift:
    def __init__(self, chain: Path = CHAIN):
        self.blocks: dict[str, list] = {}
        with gzip.open(chain, "rt") as fh:
            cur = None
            for line in fh:
                f = line.split()
                if not f:
                    continue
                if f[0] == "chain":
                    tname, tstart = f[2], int(f[5])
                    qname, qsize, qstrand, qstart = f[7], int(f[8]), f[9], int(f[10])
                    cur = [tname, tstart, qname, qsize, qstrand, qstart]
                    continue
                size = int(f[0])
                tname, t, qname, qsize, qstrand, q = cur
                self.blocks.setdefault(tname, []).append((t, t + size, qname, qstrand, q, qsize))
                if len(f) == 3:
                    cur[1] = t + size + int(f[1])
                    cur[5] = q + size + int(f[2])
        for k in self.blocks:
            self.blocks[k].sort()
        self.starts = {k: [b[0] for b in v] for k, v in self.blocks.items()}

    def point(self, chrom: str, pos1: int):
        """1-based hg38 position -> (hg19 chr, 1-based pos, strand) or None."""
        c = chrom if chrom.startswith("chr") else "chr" + chrom
        bl = self.blocks.get(c)
        if not bl:
            return None
        p0 = pos1 - 1
        i = bisect.bisect_right(self.starts[c], p0) - 1
        # chains can overlap; scan a few blocks back
        for j in range(i, max(-1, i - 50), -1):
            t0, t1, qn, qs, q0, qsize = bl[j]
            if t0 <= p0 < t1:
                off = p0 - t0
                if qs == "+":
                    return qn.replace("chr", ""), q0 + off + 1, "+"
                return qn.replace("chr", ""), qsize - (q0 + off), "-"
        return None


def map_to_1000g(var_ids: list[str], tmpdir: Path) -> dict[str, str | None]:
    """'chrC:pos:REF:ALT' (hg38) -> 1000G rsID (GRCh37 bim match on chr+pos+allele set), else None."""
    lf = Lift()
    lifted = {}
    for v in var_ids:
        c, p, ref, alt = v.split(":")
        r = lf.point(c, int(p))
        if r:
            lifted[v] = (r[0], r[1], ref.upper(), alt.upper(), r[2])
    want = {(c, p) for c, p, *_ in lifted.values()}
    tmp = tmpdir / "_lift_positions.txt"
    tmp.write_text("\n".join(f"{c}\t{p}" for c, p in sorted(want)) + "\n")
    cmd = ["awk", "BEGIN{FS=\"\\t\"} NR==FNR{w[$1\":\"$2]=1; next} (($1\":\"$4) in w){print $1\"\\t\"$4\"\\t\"$2\"\\t\"$5\"\\t\"$6}",
           str(tmp), str(BIM)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    bim: dict[tuple[str, int], list] = {}
    for line in out.splitlines():
        c, p, rs, a1, a2 = line.split("\t")
        bim.setdefault((c, int(p)), []).append((rs, a1.upper(), a2.upper()))
    res = {}
    for v in var_ids:
        res[v] = None
        if v not in lifted:
            continue
        c, p, ref, alt, strand = lifted[v]
        if strand == "-":
            if not all(ch in COMP for ch in ref + alt):
                continue
            ref, alt = "".join(COMP[ch] for ch in ref), "".join(COMP[ch] for ch in alt)
        for rs, a1, a2 in bim.get((c, p), []):
            if {a1, a2} == {ref, alt}:
                res[v] = rs
                break
    return res
