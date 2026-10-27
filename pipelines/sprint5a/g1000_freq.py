#!/usr/bin/env python3
"""A1 allele frequencies of the project's 1000G EUR LD reference (503 individuals, GRCh37) from the PLINK .bed.

Needed because the Howe 2022 GWAS-VCFs (ieu-b-4837/4838) carry no AF field, while the frozen Sprint-4 Gate-A
rules use ALT frequency for the effective-N filter and the palindromic-SNP rule. PLINK1 2-bit codes:
00 = hom A1, 01 = missing, 10 = het, 11 = hom A2. Output: data/interim/sprint5a/g1000_eur_a1freq.parquet
(snp, a1, a2, a1_freq, n_called).
"""
from pathlib import Path

import numpy as np
import pandas as pd

REF = Path("data/external/x01/genetics_tools/reference/g1000_eur")
OUT = Path(__file__).resolve().parents[2] / "data/interim/sprint5a/g1000_eur_a1freq.parquet"


def main() -> int:
    bim = pd.read_csv(f"{REF}.bim", sep="\t", header=None, usecols=[1, 4, 5], names=["snp", "a1", "a2"])
    n = sum(1 for _ in open(f"{REF}.fam"))
    bps = (n + 3) // 4
    # per-byte lookup: (#A1 alleles, #called) over the 4 genotypes packed in the byte, masked for padding later
    a1c = np.zeros((256, 4), np.int8)
    cal = np.zeros((256, 4), np.int8)
    for b in range(256):
        for k in range(4):
            code = (b >> (2 * k)) & 3
            a1c[b, k] = {0: 2, 1: 0, 2: 1, 3: 0}[code]
            cal[b, k] = 0 if code == 1 else 1
    valid = np.ones(bps * 4, bool)
    valid[n:] = False
    valid = valid.reshape(bps, 4)
    a1_by_byte = (a1c[:, None, :] * 1)  # placeholder to keep shapes explicit
    raw = np.memmap(f"{REF}.bed", dtype=np.uint8, mode="r", offset=3)
    m = len(bim)
    freq = np.empty(m, np.float32)
    ncall = np.empty(m, np.int32)
    step = 200_000
    for s in range(0, m, step):
        e = min(m, s + step)
        blk = np.asarray(raw[s * bps:e * bps]).reshape(e - s, bps)
        A = (a1c[blk] * valid[None]).sum(axis=(1, 2))
        Cn = (cal[blk] * valid[None]).sum(axis=(1, 2))
        freq[s:e] = np.where(Cn > 0, A / (2.0 * np.maximum(Cn, 1)), np.nan)
        ncall[s:e] = Cn
    del a1_by_byte
    pd.DataFrame({"snp": bim.snp, "a1": bim.a1.str.upper(), "a2": bim.a2.str.upper(), "a1_freq": freq,
                  "n_called": ncall}).to_parquet(OUT, index=False)
    print(m, "SNPs; n individuals", n, "->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
