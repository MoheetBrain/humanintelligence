#!/usr/bin/env python3
"""Sprint 4 — pre-data power calibration for Gates A and B (frozen method, frozen grid).

Question answered BEFORE any within-family or G&C value is read:
    "What gene-set result would we expect in a sample of size n if the Sprint-3 synaptic
     signal were a direct genetic effect of fraction f of the population effect?"

Method (frozen in research/sprint4/protocol.md): LD-aware summary-statistic subsampling in
the manner of PUMAS (Zhao et al. 2021, Nat Commun 12:7299). For a random subsample of size
n from a GWAS of size N, z_n = sqrt(n/N) z_N + sqrt(1 - n/N) e with e ~ N(0, R), R the SNP
correlation (LD) matrix. Scaling the signal by f gives
    z_sim = f sqrt(n/N) z_obs + sqrt(1 - f^2 n/N) e.
e is generated as X' u / sqrt(503) from standardised 1000 Genomes EUR genotypes (the same
reference MAGMA uses), independently per LDetect EUR block, and aligned to the Davies effect
allele, so its covariance is exactly the reference LD that MAGMA models. The same noise draws
are reused across scenarios (common random numbers). Each simulated GWAS then goes through the
identical MAGMA gene analysis and conditioned SynGO gene-set analysis as Sprint 3.

Limits recorded with the output: Davies-based expectations assume the target sample carries
the same per-person signal as Davies (a meta-analysis of different cognitive tests); for
trail making this is an upper bound scaled by f. The null scenario (f=0) is exact under the
reference LD model.

Usage: power_calibration.py [--reps 40] [--workers 14] [--frozen PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠")
CODEX = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01")
MAGMA = CODEX / "genetics_tools/bin/magma"
REF = CODEX / "genetics_tools/reference"
BFILE = REF / "g1000_eur"
ANNOT = REF / "annotations/genes_10kb.genes.annot"
SNP_EXCLUDE = REF / "position_mismatch_snps.txt"
DAVIES = CODEX / "inputs/davies2018_open_complete.txt"
N_DAVIES = 282014
LDETECT = REPO / "data/raw/sprint4/ldetect/EUR_fourier_ls-all.bed"
LDETECT_SHA = "b6cb0a108b88bc56d4a4b19f3e5c5a4b75562e346d0e096d286c228d4d6a1561"
SETS = REPO / "data/gene_tournament/pathway_sets/syngo.setannot"
COVAR = REPO / "data/sprint4/gene_covariates.txt"
COVAR_SHA = "1335148e378429414dd269c87e8d16df1beed200e21a8e80ce8e905552d6b1bc"
WORK = REPO / "data/interim/sprint4/calibration"
FROZEN_SHA = "44eb27217ec4c7a718b59a9f34ef6fde87c4ff0814c4cfa1691f16ccd9ccbff3"
FROZEN6 = ["GO_0042734", "GO_0099560", "GO_0099056", "GO_0099508", "GO_0045202", "SYNGO_synprocess"]


def scenarios(frozen: dict) -> list[tuple[int, float]]:
    cal = frozen["rules"]["gate_a"]["calibration"]
    grid = [(n, f) for n in cal["n_grid_pre_data"] for f in cal["f_grid"] if f > 0]
    grid.append((cal["n_grid_pre_data"][0], 0.0))  # f=0 is n-independent: the null
    # Gate B's frozen rule needs n=9,997 at f = f_gc_lower (verified rg, see sprint4 facts)
    grid.append((9997, 0.752))
    return grid


def load_inputs(source: pd.DataFrame | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    """source: optional DataFrame with Markername, Effect_allele, Other_allele, Zscore (default Davies)."""
    annot_snps: set[str] = set()
    with ANNOT.open() as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            annot_snps.update(line.split()[2:])
    bim = pd.read_csv(str(BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                      names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
    bim["bed_index"] = np.arange(len(bim))
    bim = bim[bim.snp.isin(annot_snps)]
    dav = source if source is not None else pd.read_csv(
        DAVIES, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    dav = dav.drop_duplicates("Markername", keep=False)
    m = bim.merge(dav, left_on="snp", right_on="Markername", how="inner")
    ea, oa = m.Effect_allele.str.upper(), m.Other_allele.str.upper()
    m["sign"] = np.where((ea == m.a1) & (oa == m.a2), 1, np.where((ea == m.a2) & (oa == m.a1), -1, 0))
    m = m[m.sign != 0].sort_values("bed_index").reset_index(drop=True)
    blocks = pd.read_csv(LDETECT, sep=r"\s+")
    blocks.columns = [c.strip() for c in blocks.columns]
    blocks["chr"] = blocks["chr"].str.replace("chr", "", regex=False).str.strip()
    # vectorised: per chromosome, searchsorted on block starts; SNPs before the first block
    # join it, SNPs after the last join the last (LDetect covers the chromosomes end to end)
    m["block"] = -1
    blocks["start"] = blocks["start"].astype(int)
    for c, cb in blocks.groupby("chr"):
        sel = (m.chr == c).to_numpy()
        if not sel.any():
            continue
        starts = cb.start.to_numpy()
        pos_idx = np.searchsorted(starts, m.pos.to_numpy()[sel], side="right") - 1
        pos_idx = np.clip(pos_idx, 0, len(starts) - 1)
        m.loc[sel, "block"] = cb.index.to_numpy()[pos_idx]
    return m, blocks


def ld_noise(m: pd.DataFrame, reps: int, seed: int) -> np.ndarray:
    from bed_reader import open_bed
    e = np.empty((len(m), reps), dtype=np.float32)
    with open_bed(str(BFILE) + ".bed") as bed:
        n_ref = bed.iid_count
        for blk, g in m.groupby("block"):
            idx = g.bed_index.to_numpy()
            lo, hi = idx.min(), idx.max() + 1
            x = bed.read(index=np.s_[:, lo:hi], dtype="float32")[:, idx - lo]
            mu = np.nanmean(x, axis=0)
            x = np.where(np.isnan(x), mu, x) - mu
            sd = x.std(axis=0)
            ok = sd > 0
            x[:, ok] /= sd[ok]
            rng = np.random.default_rng([seed, int(blk)])
            u = rng.standard_normal((n_ref, reps)).astype(np.float32)
            eb = (x.T @ u) / np.sqrt(n_ref)
            if (~ok).any():  # monomorphic in the reference: no LD information, independent noise
                eb[~ok] = rng.standard_normal(((~ok).sum(), reps)).astype(np.float32)
            e[g.index.to_numpy()] = eb * g.sign.to_numpy()[:, None]
    return e


def write_pvals(path: Path, snps: np.ndarray, z: np.ndarray) -> None:
    import pyarrow as pa
    import pyarrow.csv as pc
    from scipy.special import ndtr
    p = 2 * ndtr(-np.abs(z.astype(np.float64)))
    p = np.clip(p, 1e-300, 1.0)
    # pyarrow quotes header names even with quoting_style="none"; MAGMA then cannot find SNP.
    with open(path, "wb") as fh:
        fh.write(b"SNP\tP\n")
        pc.write_csv(pa.table({"SNP": snps, "P": p}), fh,
                     pc.WriteOptions(include_header=False, delimiter="\t", quoting_style="none"))


def run_job(args) -> tuple[str, bool]:
    tag, pfile, n = args
    out = WORK / tag
    if (Path(str(out) + ".syngo.gsa.out")).exists():
        return tag, True
    # tags contain dots (f0.78), so never use Path.with_suffix on them
    raw = Path(str(out) + ".genes.raw")
    r1 = None if raw.exists() else subprocess.run([str(MAGMA), "--bfile", str(BFILE), "--pval", str(pfile), f"N={n}",
                         "--gene-settings", f"snp-exclude={SNP_EXCLUDE}", "--gene-annot", str(ANNOT),
                         "--out", str(out)], capture_output=True, text=True, timeout=14400)
    if not raw.exists():
        (WORK / f"{tag}.FAILED").write_text((r1.stdout[-2000:] + r1.stderr[-2000:]) if r1 else "no genes.raw")
        return tag, False
    subprocess.run([str(MAGMA), "--gene-results", str(raw), "--set-annot", str(SETS),
                    "--gene-covar", str(COVAR), "--model", "analyse=sets",
                    "condition-hide=log_annotation_density,log_LOEUF",
                    "--out", str(out) + ".syngo"], capture_output=True, text=True, timeout=3600)
    ok = Path(str(out) + ".syngo.gsa.out").exists()
    if ok:
        pfile.unlink(missing_ok=True)
        for suffix in (".genes.raw",):
            Path(str(out) + suffix).unlink(missing_ok=True)
    return tag, ok


def collect(grid, reps) -> pd.DataFrame:
    rows = []
    for (n, f) in grid:
        for k in range(reps):
            tag = f"n{n}_f{f:g}_r{k:02d}"
            path = Path(str(WORK / tag) + ".syngo.gsa.out")
            if not path.exists():
                continue
            t = pd.read_csv(path, sep=r"\s+", comment="#")
            t = t[t.VARIABLE.isin(FROZEN6)]
            for r in t.itertuples():
                rows.append({"n": n, "f": f, "rep": k, "set": r.VARIABLE, "beta": r.BETA, "se": r.SE, "P": r.P})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    global LDETECT, COVAR, WORK
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--frozen", default=str(REPO / "research/sprint4/frozen_hypotheses.json"))
    ap.add_argument("--collect-only", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="one replicate of one scenario, for timing")
    ap.add_argument("--ldetect", default=str(LDETECT))
    ap.add_argument("--covar", default=str(COVAR))
    ap.add_argument("--source-vcf", default=None,
                    help="post-data calibration: a GWAS-VCF (e.g. the Howe population estimate) as the source")
    ap.add_argument("--source-n", type=int, default=N_DAVIES)
    ap.add_argument("--grid", default=None, help="comma list n:f overriding the frozen grid (post-data use)")
    ap.add_argument("--work-dir", default=None)
    ap.add_argument("--reverse", action="store_true",
                    help="queue replicates from the last to the first (a second process meeting the first "
                         "half-way; tags already started or finished are skipped)")
    args = ap.parse_args(argv)
    frozen_bytes = Path(args.frozen).read_bytes()
    if hashlib.sha256(frozen_bytes).hexdigest() != FROZEN_SHA:
        raise SystemExit("frozen protocol hash mismatch")
    frozen = json.loads(frozen_bytes)
    cal = frozen["rules"]["gate_a"]["calibration"]
    reps = args.reps or cal["replicates_per_scenario"]
    grid = scenarios(frozen)
    LDETECT, COVAR = Path(args.ldetect), Path(args.covar)
    for path, sha in ((LDETECT, LDETECT_SHA), (COVAR, COVAR_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise SystemExit(f"input hash mismatch: {path}")
    if args.grid:
        grid = [(int(float(a)), float(b)) for a, b in (x.split(":") for x in args.grid.split(","))]
    if args.work_dir:
        WORK = Path(args.work_dir)
    if args.smoke:
        grid, reps, WORK = grid[:1], 1, WORK / "smoke"
    source, n_src = None, N_DAVIES
    if args.source_vcf:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gate_a_within_family as GA
        df, _ = GA.parse_gwas_vcf(Path(args.source_vcf))
        source = pd.DataFrame({"Markername": df.SNP, "Effect_allele": df.EA, "Other_allele": df.OA,
                               "Zscore": df.BETA / df.SE})
        n_src = args.source_n
    WORK.mkdir(parents=True, exist_ok=True)
    if not args.collect_only:
        t0 = time.time()
        m, _ = load_inputs(source)
        print(f"{len(m):,} SNPs aligned; {m.block.nunique()} blocks; {time.time() - t0:.0f}s", flush=True)
        e = ld_noise(m, reps, cal["seed"])
        print(f"noise generated {e.shape}; {time.time() - t0:.0f}s", flush=True)
        z = m.Zscore.to_numpy(np.float64)
        snps = m.snp.to_numpy()
        (WORK / "alignment.json").write_text(json.dumps({"n_snps": int(len(m)), "n_blocks": int(m.block.nunique()),
                                                          "n_flipped": int((m.sign < 0).sum())}) + "\n")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = []
            for k in (range(reps - 1, -1, -1) if args.reverse else range(reps)):
                for (n, f) in grid:
                    tag = f"n{n}_f{f:g}_r{k:02d}"
                    # skip tags finished OR started by another process (its .pval or .log exists)
                    if Path(str(WORK / tag) + ".syngo.gsa.out").exists():
                        continue
                    if Path(str(WORK / tag) + ".genes.raw").exists():   # gene analysis done: set step only
                        futures.append(ex.submit(run_job, (tag, WORK / f"{tag}.pval", n)))
                        continue
                    pfile = WORK / f"{tag}.pval"
                    zs = f * np.sqrt(n / n_src) * z + np.sqrt(1 - f * f * n / n_src) * e[:, k]
                    write_pvals(pfile, snps, zs)
                    futures.append(ex.submit(run_job, (tag, pfile, n)))
                    # keep disk bounded: never more than ~2x workers pending files
                    while sum(not fu.done() for fu in futures) > 2 * args.workers:
                        time.sleep(5)
                print(f"replicate {k} queued; {time.time() - t0:.0f}s", flush=True)
            for fu in futures:
                tag, ok = fu.result()
                if not ok:
                    print("FAILED", tag, flush=True)
    res = collect(grid, reps)
    res.to_csv(WORK / "calibration_replicates.csv", index=False)
    if res.empty:
        print("no completed replicates", flush=True)
        return 1
    print(res.groupby(["n", "f", "set"]).agg(n_reps=("beta", "size"), median_beta=("beta", "median"),
                                             power=("P", lambda p: float((p < 0.05).mean()))).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
