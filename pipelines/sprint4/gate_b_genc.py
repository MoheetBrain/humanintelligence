#!/usr/bin/env python3
"""Sprint 4, Gate B — independent non-UKB cognitive evidence: NIHR BioResource Genes & Cognition.

Source: Zenodo 10.5281/zenodo.11066096 (Rahman et al. 2026 Nat Commun, "Genetic landscape of adult
executive function reveals a cell-type-specific developmental origin"). ONLY the G&C-only files
(``t{ma,mn,md}_gwas_gc.txt``) are used; the UKB-only and meta-analysis files are forbidden as
independence evidence and this script refuses to read them.

Phenotypes (verified from the paper, see research/sprint4/literature_facts.md): TMN = trail 1 (numeric),
TMA = trail 2 (alphanumeric; primary, EXECUTIVE_FUNCTION), TMD = TMA - TMN; higher = SLOWER (worse).
So the cognition-aligned statistic is -BETA/SE for the cognition-increasing allele.
File columns: SNP CHR BP A1 A2 A1FREQ INFO CHISQ P BETA SE N (BOLT-LMM; A1 = effect allele), GRCh37.

Steps (all rules from the frozen protocol):
  1. md5 check against the Zenodo listing; forbidden-file guard.
  2. MAGMA gene analysis with the Sprint-3 settings, per phenotype; conditioned SynGO gene-set analysis
     with the frozen covariates -> six frozen sets.
  3. Locus lookups at the 159 frozen lead SNPs (proxy r2 >= 0.8 within 500 kb when absent), allele-
     harmonised, cognition-aligned; G&C_SUPPORTED per the frozen rule; sign-concordance tests.
  4. NT5DC2 rs7639267 positive control against the published G&C estimate.
Set classification needs the pre-data calibration (n=9,997, f=f_gc_lower); it is applied by
``decide.py`` once the calibration exists. Outputs go to data/sprint4/ and reports/sprint4/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import loci_tools as LT  # noqa: E402

GENC_DIR = C.WORK / "genc"
PHENOS = {"TMA": "tma_gwas_gc.txt", "TMN": "tmn_gwas_gc.txt", "TMD": "tmd_gwas_gc.txt"}
PRIMARY = "TMA"
HIGHER_IS_WORSE = True  # "higher scores on all three TM measures indicate slower task completion"
PUBLISHED_NT5DC2 = {"snp": "rs7639267", "phenotype": "TMA", "effect_allele": "G", "other_allele": "T",
                    "beta": 0.0062, "se": 0.0020, "P": 0.0018,
                    "source": "Rahman et al. 2026 Nat Commun Table 5 (G&C column)"}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def guard_and_verify(frozen: dict) -> dict:
    rules = frozen["rules"]["gate_b"]
    forbidden = set(rules["forbidden_for_independence"])
    out = {}
    for pheno, name in PHENOS.items():
        if name in forbidden:
            raise SystemExit(f"{name} is forbidden as independence evidence")
        path = GENC_DIR / name
        if not path.exists():
            out[pheno] = {"file": name, "status": "ABSENT"}
            continue
        got = "md5:" + md5(path)
        exp = rules["independent_files"][name]
        out[pheno] = {"file": name, "md5": got, "expected": exp, "status": "OK" if got == exp else "MD5_MISMATCH",
                      "bytes": path.stat().st_size, "sha256": C.sha256_file(path)}
    return out


def read_genc(pheno: str, cols=("SNP", "CHR", "BP", "A1", "A2", "A1FREQ", "INFO", "P", "BETA", "SE", "N")) -> pd.DataFrame:
    name = PHENOS[pheno]
    assert "_gc" in name and "ukb" not in name and "meta" not in name
    return pd.read_csv(GENC_DIR / name, sep="\t", usecols=list(cols), dtype={"CHR": str})


def magma_gene(pheno: str) -> Path:
    out = GENC_DIR / f"{pheno.lower()}_10kb"
    if out.with_suffix(".genes.raw").exists():
        return out
    d = read_genc(pheno, ("SNP", "P", "N"))
    d = d.drop_duplicates("SNP", keep=False)
    pfile = GENC_DIR / f"{pheno.lower()}.pval"
    d.to_csv(pfile, sep="\t", index=False)
    subprocess.run([str(C.MAGMA_BIN), "--bfile", str(C.BFILE), "--pval", str(pfile), "ncol=N",
                    "--gene-settings", f"snp-exclude={C.SNP_EXCLUDE}", "--gene-annot", str(C.GENE_ANNOT_10KB),
                    "--out", str(out)], capture_output=True, text=True, timeout=14400, check=False)
    pfile.unlink(missing_ok=True)
    if not out.with_suffix(".genes.raw").exists():
        raise RuntimeError(f"MAGMA gene analysis failed for {pheno}; see {out}.log")
    return out


def magma_sets(gene_out: Path, covar: Path, tag: str) -> pd.DataFrame:
    out = Path(str(gene_out) + f".syngo_{tag}")
    gsa = Path(str(out) + ".gsa.out")  # not with_suffix: the tag itself contains a dot-free suffix
    if not gsa.exists():
        names = covar.read_text(encoding="utf-8").splitlines()[0].split("\t")[1:]
        names = [n for n in names if n in ("log_annotation_density", "log_LOEUF")]
        subprocess.run([str(C.MAGMA_BIN), "--gene-results", str(gene_out.with_suffix(".genes.raw")),
                        "--set-annot", str(C.SETS_FILE), "--gene-covar", str(covar), "--model", "analyse=sets",
                        "condition-hide=" + ",".join(names), "--out", str(out)],
                       capture_output=True, text=True, timeout=3600, check=False)
    t = pd.read_csv(gsa, sep=r"\s+", comment="#")
    return t[t.VARIABLE.isin(C.FROZEN_SETS)].assign(spec=tag)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-magma", action="store_true")
    args = ap.parse_args(argv)
    frozen = C.load_frozen()
    C.DATA.mkdir(parents=True, exist_ok=True)
    C.OUT.mkdir(parents=True, exist_ok=True)
    files = guard_and_verify(frozen)
    ok = [p for p, v in files.items() if v["status"] == "OK"]

    # --- 2. gene and gene-set analysis ---------------------------------------------------
    set_rows = []
    gene_outs = {}
    if not args.skip_magma:
        with ThreadPoolExecutor(max_workers=3) as ex:
            for pheno, out in zip(ok, ex.map(magma_gene, ok)):
                gene_outs[pheno] = out
    else:
        gene_outs = {p: GENC_DIR / f"{p.lower()}_10kb" for p in ok}
    raw_dir = C.REPO_ROOT / "data" / "raw" / "sprint4" / "genc_magma"
    raw_dir.mkdir(parents=True, exist_ok=True)
    full_cov = C.REPO_ROOT / "data" / "sprint3_1" / "gene_covariates_full.txt"
    for pheno, out in gene_outs.items():
        gout = out.with_suffix(".genes.out")
        (raw_dir / gout.name).write_bytes(gout.read_bytes())
        for tag, cov in (("frozen_sprint3_spec", C.COVARIATES), ("sensitivity_full_universe_D", full_cov)):
            t = magma_sets(out, cov, tag)
            for r in t.itertuples():
                set_rows.append({"phenotype": pheno, "phenotype_class": "EXECUTIVE_FUNCTION",
                                 "primary": pheno == PRIMARY, "spec": tag, "set": r.VARIABLE,
                                 "ngenes": r.NGENES, "beta": r.BETA, "se": r.SE, "P": r.P})
    sets = pd.DataFrame(set_rows)
    sets.to_csv(C.DATA / "genc_set_results_raw.csv", index=False)

    # --- 3. loci ----------------------------------------------------------------------------
    loci = pd.DataFrame(frozen["loci"])
    per = {}
    for pheno in ok:
        d = read_genc(pheno)
        per[pheno] = LT.lookup_loci(loci, d.rename(columns={"A1": "EA", "A2": "OA", "A1FREQ": "EAF"}),
                                    higher_is_better=not HIGHER_IS_WORSE, label=pheno)
    rows = []
    for _, l in loci.iterrows():
        rec = {"locus_id": l.locus_id, "chr": l.chr, "top_gene": l.top_gene,
               "bonferroni_genes": ";".join(g["symbol"] for g in l.bonferroni_genes),
               "lead_snp": l.lead_snp, "cognition_increasing_allele": l.cognition_increasing_allele,
               "davies_z": l.lead_davies_z, "davies_p": l.lead_davies_p,
               "cohort": "NIHR BioResource Genes & Cognition (G&C-only; UKB-free by design)",
               "phenotype_class": "EXECUTIVE_FUNCTION (trail making), not GENERAL_COGNITION"}
        for pheno in ok:
            r = per[pheno].loc[l.locus_id]
            for k in ("status", "used_snp", "proxy_r2", "aligned_z", "one_sided_P"):
                rec[f"{pheno}_{k}"] = r[k]
        ps = [rec.get(f"{p}_one_sided_P") for p in ok]
        ps = [p for p in ps if p is not None and not pd.isna(p)]
        prim = rec.get(f"{PRIMARY}_one_sided_P")
        testable = rec.get(f"{PRIMARY}_status") == "TESTABLE" or any(
            rec.get(f"{p}_status") == "TESTABLE" for p in ok)
        if not testable:
            rec["gate_b_locus_class"] = "NOT_TESTABLE"
        elif (prim is not None and not pd.isna(prim) and prim < 0.05) or (ps and min(ps) * 3 < 0.05):
            rec["gate_b_locus_class"] = "G&C_SUPPORTED"
        else:
            rec["gate_b_locus_class"] = "NOT_SUPPORTED_AT_THIS_POWER"
        rows.append(rec)
    lt = pd.DataFrame(rows)
    tp = lt[lt[f"{PRIMARY}_status"] == "TESTABLE"]
    lt["gate_b_FDR_primary"] = np.nan
    q = LT.bh(tp[f"{PRIMARY}_one_sided_P"].to_numpy()) if len(tp) else []
    lt.loc[tp.index, "gate_b_FDR_primary"] = q
    lt.to_csv(C.OUT / "genc_independent_loci.csv", index=False, float_format="%.5g")

    # global locus tests (primary phenotype)
    conc = int((tp[f"{PRIMARY}_aligned_z"] > 0).sum())
    n = int(len(tp))
    n_gc = 9932
    f_lower = 0.752
    davies_all = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Zscore"]).Zscore.to_numpy()[::50]
    mu = LT.tweedie(davies_all, np.abs(tp.davies_z.to_numpy()))
    n_gc = 9932
    f_lower = 0.752
    expected = {f"f={f}": float(stats.norm.cdf(np.clip(mu, 0, None) * f * np.sqrt(n_gc / C.DAVIES_N)).mean())
                for f in (1.0, f_lower)}
    # x must be the Davies z of the COGNITION-INCREASING allele (|z|), matching the aligned G&C z
    slope = LT.ivw_slope(np.abs(tp.davies_z.to_numpy()), tp[f"{PRIMARY}_aligned_z"].to_numpy())
    slope["expected_if_f1"] = float(np.sqrt(n_gc / C.DAVIES_N))
    slope["expected_if_f_lower"] = float(f_lower * np.sqrt(n_gc / C.DAVIES_N))
    slope["note"] = "expectations ignore winner's curse, so they are upper bounds"
    summary = {
        "computed_at": C.utc_now(), "code_commit": C.git_head(), "files": files,
        "primary_phenotype": PRIMARY, "direction_rule": "higher TM = slower; aligned z = -BETA/SE for the "
                                                          "cognition-increasing allele",
        "loci": {"n": int(len(lt)), "n_testable_primary": n,
                 "status_counts_primary": lt[f"{PRIMARY}_status"].value_counts().to_dict(),
                 "n_concordant_primary": conc,
                 "binomial_P_one_sided": float(stats.binomtest(conc, n, 0.5, alternative="greater").pvalue) if n else None,
                 "expected_concordance_fraction": expected,
                 "n_GC_SUPPORTED": int((lt.gate_b_locus_class == "G&C_SUPPORTED").sum()),
                 "n_GC_SUPPORTED_expected_under_null": round(0.05 * n + 0.05 * n, 1),
                 "slope_aligned_z_on_davies_z": slope,
                 "spearman_abs_davies_z_vs_aligned_z": float(stats.spearmanr(np.abs(tp.davies_z), tp[f"{PRIMARY}_aligned_z"]).statistic) if n > 2 else None},
        "positive_control": LT.positive_control(read_genc(PUBLISHED_NT5DC2["phenotype"]), PUBLISHED_NT5DC2),
    }
    (C.DATA / "gate_b_summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary["loci"], indent=1, default=str))
    print(json.dumps(summary["positive_control"], indent=1, default=str))
    print(sets.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
