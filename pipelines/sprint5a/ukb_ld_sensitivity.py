#!/usr/bin/env python3
"""Sprint 5A, Goal A sensitivity — swap the LD panel (1000G EUR, n=503) for PolyFun's published UK Biobank
LD (N=337K unrelated British-ancestry; s3://broad-alkesgroup-ukbb-ld/UKBB_LD/, AWS Open Data, public).

Why: the Davies 2018 GWAS is ~79% UK Biobank (222,543 of 282,014), so UKB LD is much closer to in-sample LD than
1000G; out-of-sample LD is the main failure mode of SuSiE-RSS at N=282k. Two runs per priority locus:

  UKB-LD, same SNPs   exactly the SNPs of the 1000G fit (those present in the UKB LD file, allele-matched), the
                      same Davies z, the same polyfun_susie.R (frozen Sprint-4 settings; plain and PolyFun
                      priors). Only the LD panel changes (plus loss of SNPs absent from the UKB panel).
  finemapper          PolyFun's own finemapper.py (--method susie, its defaults: residual variance estimated,
                      max_iter 100) with L=10, all Davies SNPs in lead +/- 500 kb present in the UKB LD file,
                      functional (SNPVAR from extract_snpvar.py --allow-missing) and --non-funct. finemapper.py
                      calls susieR::susie_suff_stat(bhat=, shat=, R=) — the pre-0.12 API — so it is run with
                      susieR 0.11.92 (CRAN archive) from a private R library (R_LIBS), in env hi-polyfun.

Downloads: region chr{c}_{s}_{s+3Mb} with the lead in the middle Mb (PolyFun convention), .npz + .gz,
recorded in data/raw/sprint5a/ukb_ld/PROVENANCE.json; files kept under data/interim/sprint5a/ukb_ld/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
from polyfun_susie import PRIORITY  # noqa: E402

BASE = "https://broad-alkesgroup-ukbb-ld.s3.amazonaws.com/UKBB_LD/"
LD_DIR = REPO / "data" / "interim" / "sprint5a" / "ukb_ld"
PROV = REPO / "data" / "raw" / "sprint5a" / "ukb_ld" / "PROVENANCE.json"
S5A = REPO / "data" / "interim" / "sprint5a" / "susie"
WORK = REPO / "data" / "interim" / "sprint5a" / "susie_ukbld"
R_SCRIPT = HERE / "polyfun_susie.R"
WIN = 500_000


def region(lead_pos: int, chrom: str) -> str:
    s = ((lead_pos - 1) // 1_000_000) * 1_000_000 + 1 - 1_000_000
    return f"chr{chrom}_{max(s, 1)}_{max(s, 1) + 3_000_000}"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def download(regions: list[str]) -> None:
    LD_DIR.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    prov = json.loads(PROV.read_text()) if PROV.exists() else {
        "resource": "PolyFun UK Biobank summary LD matrices (N=337K unrelated British-ancestry), 3 Mb regions",
        "bucket": "s3://broad-alkesgroup-ukbb-ld/UKBB_LD/ (AWS Open Data Program; public HTTPS, no account)",
        "documentation": "https://github.com/omerwe/polyfun/wiki/3.-Functionally-informed-fine-mapping-with-finemapper",
        "licence_note": "Distributed by the Alkes Price group via the AWS Open Data Program for public use; derived from "
                        "UK Biobank but summary-level (no individual data); no terms accepted to download.",
        "files": []}
    done = {f["file"] for f in prov["files"]}
    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock()

    def one(fn: str) -> None:
        url = BASE + fn
        t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # S3 throttles single connections to ~0.2 MB/s from here; aria2c splits into parallel range requests
        rc = subprocess.run(["aria2c", "-q", "-x16", "-s16", "-k1M", "--max-tries=10", "--retry-wait=5",
                             "--allow-overwrite=true", "-d", str(LD_DIR), "-o", fn, url]).returncode
        if rc != 0:  # aria2c exit 3 = resource not found (HTTP 404)
            with lock:
                prov.setdefault("not_available", []).append({"file": fn, "url": url, "checked_utc": t0,
                                                             "aria2c_exit": rc})
                PROV.write_text(json.dumps(prov, indent=1) + "\n")
            return
        p = LD_DIR / fn
        rec = {"file": fn, "url": url, "retrieved_utc": t0, "bytes": p.stat().st_size, "sha256": sha256(p)}
        with lock:
            prov["files"].append(rec)
            PROV.write_text(json.dumps(prov, indent=1) + "\n")
            print(fn, rec["bytes"], flush=True)

    todo = [f"{r}.{ext}" for r in regions for ext in ("gz", "npz")
            if not (f"{r}.{ext}" in done and (LD_DIR / f"{r}.{ext}").exists())]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(one, todo))


def load_ld(prefix: Path, keep_bp: tuple[int, int]) -> tuple[pd.DataFrame, np.ndarray]:
    from scipy import sparse
    snps = pd.read_csv(str(prefix) + ".gz", sep=r"\s+")
    snps = snps.rename(columns={"allele1": "A1", "allele2": "A2", "position": "BP", "chromosome": "CHR", "rsid": "SNP"})
    idx = np.where(snps.BP.between(*keep_bp))[0]
    M = sparse.load_npz(str(prefix) + ".npz").tocsr()
    sub = M[idx][:, idx].toarray().astype(np.float64)
    sub = sub + sub.T
    assert np.allclose(np.diag(sub), 1.0), "UKB LD diagonal is not 1"
    return snps.iloc[idx].reset_index(drop=True), sub


QC_R = 0.8  # allele-coding QC: |r| > 0.8 in BOTH panels with opposite sign cannot be real LD


def run(loci_ids: list[str], rscript: Path) -> pd.DataFrame:
    """UKB-LD refit on the 1000G SNP set, after an allele-coding QC.

    QC (added 2026-09-24 after the first UKB run gave estimate_s_rss 0.82-0.88 at 3p21.1): a SNP is dropped
    when, for at least one partner SNP, |r| > 0.8 in both 1000G and UKB LD but with opposite sign after the
    alleles are aligned by name. Such a pattern is an allele-coding inconsistency in one panel, not LD
    (at L91869 the Davies z are sign-consistent with 1000G for 100% of the affected pairs and with UKB for 0%).
    The same SNPs are dropped from both the plain and the PolyFun fit; counts are reported.
    """
    from gate_c_finemap import locus_inputs
    frozen = {l["locus_id"]: l for l in C.load_frozen()["loci"]}
    dav = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    dav = dav.drop_duplicates("Markername", keep=False)
    bim = pd.read_csv(str(C.BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                      names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
    bim["bed_index"] = np.arange(len(bim))
    out = []
    qc_rows = []
    for lid in loci_ids:
        l = frozen[lid]
        lead = int(l["lead_pos_grch37"])
        reg = region(lead, l["chr"])
        s1 = pd.read_csv(S5A / lid / "snps_priors.tsv", sep="\t")
        if not (LD_DIR / f"{reg}.npz").exists():
            out.append({"locus_id": lid, "method": "UKBLD_sameSNPs", "error": f"UKB LD {reg}.npz not published (HTTP 404)"})
            print(lid, reg, "SKIPPED: no UKB LD npz", flush=True)
            continue
        ld_snps, R = load_ld(LD_DIR / reg, (lead - WIN, lead + WIN))
        key = lambda c, p, a, b: f"{c}.{p}.{min(a, b)}.{max(a, b)}"  # noqa: E731
        ld_snps["key"] = [key(c, p, a, b) for c, p, a, b in zip(ld_snps.CHR, ld_snps.BP, ld_snps.A1, ld_snps.A2)]
        s1["key"] = [key(c, p, a, b) for c, p, a, b in zip(s1.chr, s1.pos, s1.a1, s1.a2)]
        ld_snps = ld_snps.drop_duplicates("key", keep=False)
        pos = dict(zip(ld_snps.key, ld_snps.index))  # index == row of R (load_ld resets it; duplicates dropped after)
        s1["ld_i"] = s1.key.map(pos)
        m = s1[s1.ld_i.notna()].copy()
        m["ld_i"] = m.ld_i.astype(int)
        # z in s1 is for the 1000G bim a1; orient to UKB allele1 (R is invariant to a common flip)
        a1_ukb = ld_snps.A1.loc[m.ld_i].to_numpy()  # label lookup: index == R row
        flip = np.where(m.a1.to_numpy() == a1_ukb, 1.0, -1.0)
        m["z_ukb"] = flip * m.z_a1
        # allele-coding QC against the 1000G LD of the same SNPs (in 1000G a1 coding)
        g, R1 = locus_inputs(l["chr"], lead, dav, bim)
        assert (g.snp.to_numpy() == s1.snp.to_numpy()).all()
        keep1 = s1.ld_i.notna().to_numpy()
        A = R1[np.ix_(keep1, keep1)]
        Bq = R[np.ix_(m.ld_i.to_numpy(), m.ld_i.to_numpy())] * np.outer(flip, flip)
        disc = (np.abs(A) > QC_R) & (np.abs(Bq) > QC_R) & (np.sign(A) != np.sign(Bq))
        nd = disc.sum(1)
        drop = np.zeros(len(m), bool)
        while disc[np.ix_(~drop, ~drop)].any():  # greedily drop the SNP with most discordant partners
            cnt = np.where(drop, -1, disc[:, ~drop].sum(1))
            drop[int(np.argmax(cnt))] = True
        qc_rows.append({"locus_id": lid, "ukb_region": reg, "n_1000g": len(s1), "n_in_ukb": len(m),
                        "n_dropped_allele_discordant": int(drop.sum()),
                        "dropped": ";".join(f"{v}({c})" for v, c in zip(m.snp[drop], nd[drop])) or None,
                        "discordant_pairs_before": int(disc.sum() // 2)})
        m = m[~drop].copy()
        Rm = R[np.ix_(m.ld_i.to_numpy(), m.ld_i.to_numpy())]
        d = WORK / lid
        d.mkdir(parents=True, exist_ok=True)
        np.savetxt(d / "z.txt", m.z_ukb.to_numpy())
        np.savetxt(d / "prior.txt", m.polyfun_snpvar.to_numpy())
        Rm.T.tofile(d / "R.bin")
        subprocess.run([str(rscript), str(R_SCRIPT), str(d), str(C.DAVIES_N)], capture_output=True, text=True,
                       timeout=7200)
        (d / "R.bin").unlink(missing_ok=True)
        fit = json.loads((d / "fit_sprint5a.json").read_text())
        m[["snp", "chr", "pos", "a1", "a2", "z_ukb", "polyfun_snpvar", "prior_source"]].to_csv(d / "snps.tsv", sep="\t",
                                                                                              index=False)
        m = m.reset_index(drop=True)
        for method, k in (("SuSiE_plain_UKBLD_sameSNPs", "plain"), ("PolyFun+SuSiE_UKBLD_sameSNPs", "polyfun")):
            f = fit[k]
            if "error" in f:
                out.append({"locus_id": lid, "method": method, "error": f["error"]})
                continue
            pip = np.asarray(f["pip"], float)
            for cs in f.get("cs", []):
                idx = np.atleast_1d(np.array(cs["idx"])) - 1
                for i in idx:
                    out.append({"locus_id": lid, "method": method, "credible_set": cs["name"], "cs_size": len(idx),
                                "cs_min_abs_corr": cs.get("min_abs_corr"), "variant": m.snp[i], "chr": l["chr"],
                                "pos_grch37": int(m.pos[i]), "pip": float(pip[i]),
                                "prior": float(m.polyfun_snpvar[i] / m.polyfun_snpvar.sum()),
                                "prior_source": m.prior_source[i]})
            j = int(np.argmax(pip))
            out.append({"locus_id": lid, "method": method, "credible_set": "max_pip", "variant": m.snp[j],
                        "chr": l["chr"], "pos_grch37": int(m.pos[j]), "pip": float(pip[j]),
                        "prior": float(m.polyfun_snpvar[j] / m.polyfun_snpvar.sum()), "prior_source": m.prior_source[j],
                        "n_snps": len(m), "n_snps_1000g": len(s1), "estimate_s_rss": fit.get("s"),
                        "ukb_region": reg, "converged": f.get("converged")})
        print(lid, reg, len(s1), "->", len(m), "QC dropped", int(drop.sum()), "s=", fit.get("s"), flush=True)
    pd.DataFrame(qc_rows).to_csv(REPO / "data" / "interim" / "sprint5a" / "ukb_ld_allele_qc.csv", index=False)
    return pd.DataFrame(out)


FM_OUT = REPO / "data" / "interim" / "sprint5a" / "finemapper_ukbld"
POLYFUN = REPO / "data" / "interim" / "sprint5a" / "tools" / "polyfun"
HI_POLYFUN = Path("/opt/homebrew/Caskroom/miniforge/base/envs/hi-polyfun/bin/python")
RLIB_OLD = REPO / "data" / "interim" / "sprint5a" / "tools" / "Rlib_susie0.11.92"


def run_finemapper(loci_ids: list[str]) -> pd.DataFrame:
    import os
    frozen = {l["locus_id"]: l for l in C.load_frozen()["loci"]}
    dav = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Chromosome", "Position", "Markername", "Effect_allele",
                                                           "Other_allele", "Zscore"])
    dav = dav.drop_duplicates("Markername", keep=False)
    base_env = {k: v for k, v in os.environ.items() if v.isascii()}  # R chokes on the emoji repo path in $_
    env = dict(base_env, R_LIBS=str(RLIB_OLD), LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8",
               R_HOME=str(HI_POLYFUN.parents[1] / "lib" / "R"),
               PATH=str(HI_POLYFUN.parent) + ":" + os.environ.get("PATH", ""))
    FM_OUT.mkdir(parents=True, exist_ok=True)
    res = []
    for lid in loci_ids:
        l = frozen[lid]
        lead = int(l["lead_pos_grch37"])
        reg = region(lead, l["chr"])
        st, en = lead - WIN, lead + WIN
        if not (LD_DIR / f"{reg}.npz").exists():
            res.append({"locus_id": lid, "method": "PolyFun_finemapper_UKBLD", "error": f"UKB LD {reg}.npz not published (HTTP 404)"})
            print(lid, reg, "SKIPPED: no UKB LD npz", flush=True)
            continue
        ss = dav[(dav.Chromosome.astype(str) == str(l["chr"])) & dav.Position.between(st, en)]
        ss = pd.DataFrame({"SNP": ss.Markername, "CHR": ss.Chromosome.astype(int), "BP": ss.Position.astype(int),
                           "A1": ss.Effect_allele.str.upper(), "A2": ss.Other_allele.str.upper(), "Z": ss.Zscore})
        ss = ss[ss.A1.str.len().eq(1) & ss.A2.str.len().eq(1)]
        qc = REPO / "data" / "interim" / "sprint5a" / "ukb_ld_allele_qc.csv"
        if qc.exists():
            q = pd.read_csv(qc).set_index("locus_id")
            if lid in q.index and isinstance(q.loc[lid, "dropped"], str):
                bad = {x.split("(")[0] for x in q.loc[lid, "dropped"].split(";")}
                ss = ss[~ss.SNP.isin(bad)]  # same allele-coding QC as run(); non-1000G SNPs cannot be checked
        f_in = FM_OUT / f"{lid}.sumstats.txt"
        ss.to_csv(f_in, sep="\t", index=False)
        f_sv = FM_OUT / f"{lid}.snpvar.gz"
        if not f_sv.exists():
            subprocess.run([str(HI_POLYFUN), str(POLYFUN / "extract_snpvar.py"), "--sumstats", str(f_in), "--out",
                            str(f_sv), "--allow-missing"], check=True, capture_output=True, text=True, env=env,
                           cwd=str(POLYFUN))
        for tag, extra in (("funct", []), ("nonfunct", ["--non-funct"])):
            out = FM_OUT / f"{lid}.{tag}.gz"
            pr = subprocess.run([str(HI_POLYFUN), str(POLYFUN / "finemapper.py"), "--method", "susie",
                                 "--sumstats", str(f_sv), "--chr", str(l["chr"]), "--start", str(st), "--end", str(en),
                                 "--n", str(C.DAVIES_N), "--ld", str(LD_DIR / reg), "--out", str(out),
                                 "--max-num-causal", "10", "--allow-missing"] + extra,
                                capture_output=True, text=True, env=env, cwd=str(POLYFUN))
            (FM_OUT / f"{lid}.{tag}.log").write_text(pr.stdout[-20000:] + "\n" + pr.stderr[-20000:])
            if not out.exists():
                res.append({"locus_id": lid, "method": f"PolyFun_finemapper_{tag}_UKBLD", "error": pr.stderr[-400:]})
                print(lid, tag, "FAILED", pr.stderr[-300:], flush=True)
                continue
            d = pd.read_csv(out, sep="\t")
            for r in d[(d.CREDIBLE_SET > 0) | (d.PIP >= 0.1)].itertuples():
                res.append({"locus_id": lid, "method": f"PolyFun_finemapper_{tag}_UKBLD",
                            "credible_set": f"L{int(r.CREDIBLE_SET)}" if r.CREDIBLE_SET > 0 else "none",
                            "variant": r.SNP, "chr": l["chr"], "pos_grch37": int(r.BP), "pip": float(r.PIP),
                            "prior": float(getattr(r, "SNPVAR", np.nan)), "n_snps": len(d), "ukb_region": reg})
            print(lid, tag, len(d), "SNPs; max PIP", d.PIP.max(), flush=True)
    return pd.DataFrame(res)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["download", "run", "finemapper"])
    ap.add_argument("--loci", nargs="*", default=list(PRIORITY))
    ap.add_argument("--rscript", default=str(C.RSCRIPT))
    a = ap.parse_args(argv)
    frozen = {l["locus_id"]: l for l in C.load_frozen()["loci"]}
    regs = list(dict.fromkeys(region(int(frozen[x]["lead_pos_grch37"]), frozen[x]["chr"]) for x in a.loci))
    if a.step == "download":
        download(regs)
    elif a.step == "finemapper":
        df = run_finemapper(a.loci)
        df.to_parquet(REPO / "data" / "interim" / "sprint5a" / "finemapper_ukbld.parquet", index=False)
    else:
        df = run(a.loci, Path(a.rscript))
        df.to_parquet(REPO / "data" / "interim" / "sprint5a" / "ukb_ld_sensitivity.parquet", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
