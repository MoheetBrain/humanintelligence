#!/usr/bin/env python3
"""Sprint 4, Gate A — within-sibship direct-effect test (Howe et al. 2022, Within Family GWAS Consortium).

Datasets (identity verified from the public OpenGWAS gwasinfo.json before the freeze):
    ieu-b-4837  Cognitive function, SIBLING (within-family) estimate, N=9,997, HG19/GRCh37
    ieu-b-4838  Cognitive function, POPULATION estimate (same siblings), N=22,593, HG19/GRCh37
UK Biobank contributes 8,061 of the 27,638 individuals in Howe's cognition analysis, so Gate A tests
DIRECT vs POPULATION effects; it is NOT an independence test (that is Gate B).

Access boundary
---------------
OpenGWAS automated download requires a JWT (env OPENGWAS_JWT). This project does not create accounts.
``fetch`` stops at that boundary and records the blocker; everything after it (VCF parsing, identity
check, MAGMA, calibration, classification, locus concordance, attenuation) is implemented and tested on
synthetic GWAS-VCF fixtures, and runs unchanged once the two VCFs are present in
``data/interim/sprint4/opengwas/``.

Usage
-----
    python pipelines/sprint4/gate_a_within_family.py fetch      # needs OPENGWAS_JWT
    python pipelines/sprint4/gate_a_within_family.py analyse    # runs, or writes NOT_TESTABLE outputs
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify as K  # noqa: E402
import common as C  # noqa: E402
import loci_tools as LT  # noqa: E402

API = "https://api.opengwas.io/api"
IDS = {"within_family": "ieu-b-4837", "population": "ieu-b-4838"}
VCF_DIR = C.WORK / "opengwas"
USER_ACTION = ("Set OPENGWAS_JWT (a token from https://api.opengwas.io/profile/ after signing in) in the shell "
               "environment, then run: python pipelines/sprint4/gate_a_within_family.py fetch && "
               "python pipelines/sprint4/gate_a_within_family.py analyse")
ALT_USER_ACTION = ("Or, without any token: open https://gwas.mrcieu.ac.uk/datasets/ieu-b-4837/ and "
                   "https://gwas.mrcieu.ac.uk/datasets/ieu-b-4838/, click 'VCF Files', and save both .vcf.gz "
                   "files into data/interim/sprint4/opengwas/ (the website allows 20 datasets/day), then run "
                   "the analyse command.")


# ------------------------------------------------------------------ fetch (access boundary)
def _api(path: str, token: str, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{API}/{path}", data=data, method="POST" if data else "GET",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def fetch() -> dict:
    token = os.environ.get("OPENGWAS_JWT", "").strip()
    status = {"checked_at": C.utc_now(), "env_var": "OPENGWAS_JWT", "present": bool(token)}
    if not token:
        status.update({"status": "BLOCKED", "blocker": "OPENGWAS_JWT absent; OpenGWAS automated download requires "
                       "a JWT and this project does not create accounts or automate website downloads.",
                       "minimal_user_action": USER_ACTION, "alternative_user_action": ALT_USER_ACTION})
        return status
    VCF_DIR.mkdir(parents=True, exist_ok=True)
    got = {}
    for role, gid in IDS.items():
        try:
            info = _api(f"gwasinfo/{gid}", token)
            urls = _api("gwasinfo/files", token, {"id": [gid]})
            vcf = [u for u in (urls if isinstance(urls, list) else urls.get(gid, [])) if ".vcf.gz" in u
                   and not u.endswith(".tbi")]
            if not vcf:
                raise RuntimeError(f"no VCF URL returned for {gid}")
            dest = VCF_DIR / f"{gid}.vcf.gz"
            urllib.request.urlretrieve(vcf[0], dest)
            got[role] = {"id": gid, "metadata": info, "file": str(dest), "sha256": C.sha256_file(dest),
                         "bytes": dest.stat().st_size}
        except (urllib.error.URLError, RuntimeError, ValueError) as exc:
            got[role] = {"id": gid, "error": str(exc)}
    status.update({"status": "FETCHED" if all("file" in v for v in got.values()) else "FAILED", "datasets": got})
    return status


# ------------------------------------------------------------------ GWAS-VCF parsing
def parse_gwas_vcf(path: Path) -> tuple[pd.DataFrame, dict]:
    """GWAS-VCF (MRCIEU spec 1.0): ES is the effect of ALT; LP = -log10 P; AF = ALT frequency."""
    opener = gzip.open if str(path).endswith(".gz") else open
    header: dict = {"sample_ids": []}
    rows = []
    with opener(path, "rt") as fh:
        for line in fh:
            if line.startswith("##"):
                if line.startswith("##SAMPLE=<"):
                    header["sample_ids"] += [kv.split("=", 1)[1] for kv in line[10:-2].split(",")
                                             if kv.startswith("ID=")]
                continue
            if line.startswith("#CHROM"):
                header["columns"] = line.lstrip("#").rstrip("\n").split("\t")
                continue
            p = line.rstrip("\n").split("\t")
            fmt = p[8].split(":")
            val = dict(zip(fmt, p[9].split(":")))
            rows.append({"CHR": p[0], "BP": int(p[1]), "SNP": p[2] if p[2] != "." else val.get("ID", "."),
                         "OA": p[3], "EA": p[4], "BETA": float(val.get("ES", "nan")),
                         "SE": float(val.get("SE", "nan")),
                         "P": 10 ** (-float(val["LP"])) if val.get("LP", ".") not in (".", "") else np.nan,
                         "EAF": float(val["AF"]) if val.get("AF", ".") not in (".", "") else np.nan,
                         "N": float(val["SS"]) if val.get("SS", ".") not in (".", "") else np.nan})
    return pd.DataFrame(rows), header


def identity_check(header: dict, expected_id: str) -> bool:
    return expected_id in header.get("sample_ids", [])


def effective_n(pop: pd.DataFrame, wf: pd.DataFrame, n_pop: int) -> float:
    """Frozen: N_eff(WF) = N_pop x median over SNPs with 0.05<=AF<=0.95 of (SE_pop/SE_wf)^2."""
    m = pop.merge(wf, on="SNP", suffixes=("_p", "_w"))
    m = m[(m.EAF_p >= 0.05) & (m.EAF_p <= 0.95) & (m.SE_w > 0)]
    return float(n_pop * np.median((m.SE_p / m.SE_w) ** 2))


# ------------------------------------------------------------------ outputs
def not_testable_outputs(frozen: dict, access: dict, calib: dict) -> None:
    reason = f"Gate A data unavailable: {access.get('blocker', access.get('status'))}"
    sets = pd.DataFrame([{"set": s["set_id"], "name": s["name"], "population_beta": None, "population_se": None,
                          "population_P": None, "within_family_beta": None, "within_family_se": None,
                          "within_family_P": None, "sign_concordance": None, "attenuation_ratio": None,
                          "attenuation_ci95": None, "expected_beta_if_direct_f1": calib.get(s["set_id"], {}).get("f1"),
                          "expected_beta_if_direct_f078": calib.get(s["set_id"], {}).get("f078"),
                          "power_if_direct_f078": calib.get(s["set_id"], {}).get("power_f078"),
                          "classification": K.NOT_TESTABLE, "reason": reason,
                          "never_read_as": "NO_EFFECT"} for s in frozen["frozen_sets"]])
    sets.to_csv(C.OUT / "within_family_synaptic_sets.csv", index=False)
    loci = pd.DataFrame([{"locus_id": l["locus_id"], "top_gene": l["top_gene"], "lead_snp": l["lead_snp"],
                          "cognition_increasing_allele": l["cognition_increasing_allele"],
                          "classification": K.NOT_TESTABLE, "reason": reason} for l in frozen["loci"]])
    loci.to_csv(C.OUT / "within_family_locus_concordance.csv", index=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["fetch", "analyse"])
    args = ap.parse_args(argv)
    frozen = C.load_frozen()
    C.DATA.mkdir(parents=True, exist_ok=True)
    C.OUT.mkdir(parents=True, exist_ok=True)
    access_path = C.DATA / "gate_a_access.json"
    if args.cmd == "fetch":
        st = fetch()
        access_path.write_text(json.dumps(st, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in st.items() if k != "datasets"}, indent=1))
        return 0
    access = json.loads(access_path.read_text()) if access_path.exists() else fetch()
    vcfs = {role: VCF_DIR / f"{gid}.vcf.gz" for role, gid in IDS.items()}
    calib_path = C.DATA / "power_calibration_summary.json"
    calib = json.loads(calib_path.read_text()).get("per_set_compact", {}) if calib_path.exists() else {}
    if not all(p.exists() for p in vcfs.values()):
        not_testable_outputs(frozen, access, calib)
        print("Gate A: NOT_TESTABLE (data absent); outputs written with explicit reason")
        return 0
    # --- data present: full analysis (exercised by tests on synthetic VCFs) -------------------
    parsed = {role: parse_gwas_vcf(p) for role, p in vcfs.items()}
    for role, (df, hdr) in parsed.items():
        if not identity_check(hdr, IDS[role]):
            access["identity_failure"] = role
            not_testable_outputs(frozen, {"blocker": f"identity check failed for {role}"}, calib)
            return 0
    pop, wf = parsed["population"][0], parsed["within_family"][0]
    analyse_present(frozen, pop, wf, access, work=C.WORK / "gate_a", out=C.OUT, reps=None)
    return 0


def _magma(df: pd.DataFrame, tag: str, n_default: int, work: Path) -> pd.DataFrame:
    work.mkdir(parents=True, exist_ok=True)
    out = work / f"{tag}_10kb"
    if not out.with_suffix(".genes.raw").exists():
        d = df[["SNP", "P", "N"]].copy()
        d["N"] = d.N.fillna(n_default)
        d = d.dropna(subset=["P"]).drop_duplicates("SNP", keep=False)
        pfile = work / f"{tag}.pval"
        d.to_csv(pfile, sep="\t", index=False)
        subprocess.run([str(C.MAGMA_BIN), "--bfile", str(C.BFILE), "--pval", str(pfile), "ncol=N",
                        "--gene-settings", f"snp-exclude={C.SNP_EXCLUDE}", "--gene-annot", str(C.GENE_ANNOT_10KB),
                        "--out", str(out)], capture_output=True, text=True, timeout=14400, check=False)
        pfile.unlink(missing_ok=True)
    so = Path(str(out) + ".syngo")
    if not so.with_suffix(".gsa.out").exists():
        subprocess.run([str(C.MAGMA_BIN), "--gene-results", str(out.with_suffix(".genes.raw")), "--set-annot",
                        str(C.SETS_FILE), "--gene-covar", str(C.COVARIATES), "--model", "analyse=sets",
                        "condition-hide=log_annotation_density,log_LOEUF", "--out", str(so)],
                       capture_output=True, text=True, timeout=3600, check=False)
    t = pd.read_csv(so.with_suffix(".gsa.out"), sep=r"\s+", comment="#")
    return t[t.VARIABLE.isin(C.FROZEN_SETS)].set_index("VARIABLE")


def analyse_present(frozen: dict, pop: pd.DataFrame, wf: pd.DataFrame, access: dict, work: Path, out: Path,
                    reps: int | None, pop_vcf: Path | None = None) -> dict:
    """Full Gate A once both GWAS are available (also used for the synthetic dry run)."""
    rules = frozen["rules"]["gate_a"]
    n_pop = rules["datasets"]["population"]["sample_size"]
    n_eff = effective_n(pop, wf, n_pop)
    f_h = float(rules["howe_shrinkage_f"])
    sets_pop = _magma(pop, "population", n_pop, work)
    sets_wf = _magma(wf, "within_family", rules["datasets"]["within_family"]["sample_size"], work)
    # post-data calibration: population GWAS subsampled to N_eff(WF) (frozen primary)
    cal_dir = work / "calibration"
    grid = ",".join(f"{round(n_eff)}:{f}" for f in (1.0, f_h, 0.0))
    cmd = [sys.executable, str(Path(__file__).resolve().parent / "power_calibration.py"),
           "--source-vcf", str(pop_vcf or (VCF_DIR / f"{IDS['population']}.vcf.gz")), "--source-n", str(n_pop),
           "--grid", grid, "--work-dir", str(cal_dir), "--workers", "8"]
    if reps:
        cmd += ["--reps", str(reps)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=72000, check=False)
    sims = pd.read_csv(cal_dir / "calibration_replicates.csv") if (cal_dir / "calibration_replicates.csv").exists() \
        else pd.DataFrame(columns=["n", "f", "set", "beta", "P"])
    t = K.thresholds(frozen)
    rows = []
    for s in frozen["frozen_sets"]:
        sid = s["set_id"]
        bp, sp, pp = (float(sets_pop.loc[sid, c]) for c in ("BETA", "SE", "P"))
        bw, sw, pw = (float(sets_wf.loc[sid, c]) for c in ("BETA", "SE", "P"))
        exp = {f: K.expected_distribution(sims[(sims.set == sid) & np.isclose(sims.f, f)].beta,
                                          sims[(sims.set == sid) & np.isclose(sims.f, f)].P, t["q_low"], t["alpha"])
               for f in (1.0, f_h, 0.0)}
        cls = K.classify_set(bw, pw, exp[f_h], frozen)
        att = K.attenuation(bw, sw, bp, sp, seed=int(rules["calibration"]["seed"]))
        exp_ratio = (exp[1.0]["median"] / bp) if exp[1.0].get("n_reps") and bp else None
        rows.append({"set": sid, "name": s["name"], "population_beta": bp, "population_se": sp, "population_P": pp,
                     "within_family_beta": bw, "within_family_se": sw, "within_family_P": pw,
                     "sign_concordance": bool(np.sign(bw) == np.sign(bp)),
                     "attenuation_ratio": att.get("ratio"), "attenuation_boot_ci95": att.get("boot_ci95"),
                     "attenuation_fieller_ci95": att.get("fieller_ci95"),
                     "expected_ratio_if_fully_direct": exp_ratio,
                     "expected_wf_beta_f1_median": exp[1.0].get("median"),
                     "expected_wf_beta_f078_q025": exp[f_h].get("q_low"),
                     "expected_wf_beta_f078_median": exp[f_h].get("median"),
                     "power_f078": exp[f_h].get("power"), "power_f1": exp[1.0].get("power"),
                     "null_q975": exp[0.0].get("q_high"),
                     "compatible_with_howe_shrinkage": bool(exp[f_h].get("n_reps") and
                                                            exp[f_h]["q_low"] <= bw <= exp[f_h]["q_high"]),
                     "classification": cls["class"], "subtype": cls["subtype"],
                     "can_drive_pivot": cls["can_drive_pivot"], "N_eff_wf": n_eff})
    sets = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    sets.to_csv(out / "within_family_synaptic_sets.csv", index=False, float_format="%.5g")
    # loci
    loci = pd.DataFrame(frozen["loci"])
    lp = LT.lookup_loci(loci, pop, higher_is_better=True, label="pop")
    lw = LT.lookup_loci(loci, wf, higher_is_better=True, label="wf")
    davies_all = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Zscore"]).Zscore.to_numpy()[::50]
    mu = LT.tweedie(davies_all, np.abs(loci.lead_davies_z.to_numpy()))
    lrows = []
    for i, l in loci.iterrows():
        a, b = lp.loc[l.locus_id], lw.loc[l.locus_id]
        expz = f_h * max(mu[i], 0) * np.sqrt(n_eff / C.DAVIES_N)
        lrows.append({"locus_id": l.locus_id, "top_gene": l.top_gene, "lead_snp": l.lead_snp,
                      "cognition_increasing_allele": l.cognition_increasing_allele, "used_snp": b.used_snp,
                      "pop_aligned_z": a.aligned_z, "wf_aligned_z": b.aligned_z,
                      "pop_aligned_beta": a.get("aligned_beta"), "wf_aligned_beta": b.get("aligned_beta"),
                      "wf_se": b.get("se"), "expected_wf_z_f078": expz,
                      "classification": K.classify_locus_wf(b.aligned_z, expz, b.status), "status": b.status})
    lt = pd.DataFrame(lrows)
    lt.to_csv(out / "within_family_locus_concordance.csv", index=False, float_format="%.5g")
    tl = lt[lt.status == "TESTABLE"]
    from scipy import stats
    conc = int((tl.wf_aligned_z > 0).sum())
    w = 1 / tl.wf_se ** 2
    slope = float((w * tl.pop_aligned_beta * tl.wf_aligned_beta).sum() / (w * tl.pop_aligned_beta ** 2).sum()) \
        if len(tl) else None
    summary = {"N_eff_wf": n_eff, "n_testable_loci": int(len(tl)), "n_concordant": conc,
               "binomial_P": float(stats.binomtest(conc, len(tl), 0.5, alternative="greater").pvalue) if len(tl) else None,
               "slope_beta_wf_on_beta_pop": slope,
               "spearman_rank_preservation": float(stats.spearmanr(np.abs(tl.pop_aligned_z), tl.wf_aligned_z).statistic)
               if len(tl) > 2 else None,
               "locus_classes": lt.classification.value_counts().to_dict(),
               "set_classes": sets.classification.value_counts().to_dict()}
    (out / "within_family_power_calibration.json").write_text(json.dumps(
        {"post_data_calibration": {"grid": grid, "n_sims": int(len(sims))}, "summary": summary}, indent=1,
        default=str) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
