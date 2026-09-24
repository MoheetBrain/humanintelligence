#!/usr/bin/env python3
"""Sprint 5A, Goal A — functionally informed fine-mapping (PolyFun approach 1 + SuSiE-RSS) vs plain SuSiE.

What is held fixed (identical to the Sprint-4 sensitivity fits, pipelines/sprint4/gate_c_finemap.py):
  * the 36 Gate-C loci, window lead +/- 500 kb, Davies 2018 z (n = 282,014);
  * the SNP set and the LD matrix (1000 Genomes phase 3 EUR, 503 people, MAF >= 0.01), rebuilt with the
    Sprint-4 function ``locus_inputs`` and checked SNP-for-SNP against data/interim/sprint4/susie/<locus>/snps.tsv;
  * susieR::susie_rss(L = 10, coverage = 0.95, min_abs_corr = 0.5, estimate_residual_variance = FALSE,
    max_iter = 1000), same susieR build (0.14.2, hi-sprint4 env).
What changes: ``prior_weights`` = PolyFun precomputed per-SNP heritabilities (``snpvar_meta.chr*.parquet``,
meta-analysis of 15 UK Biobank traits, baseline-LF functional model; omerwe/polyfun @ 8b17b4e, MIT licence),
with the same max/min ratio truncation (q = 100) that PolyFun's ``extract_snpvar.py`` applies.

Missing priors: PolyFun's ``extract_snpvar.py`` refuses to run when SNPs lack a precomputed prior (or, with
--allow-missing, silently drops them). Neither is acceptable here because the SNP set must match the plain fit,
so a SNP absent from the 19M-SNP PolyFun set receives the genome-wide floor prior (max/100, i.e. the lowest bin
after truncation). This can only down-weight such a SNP relative to annotated SNPs; the count of such SNPs is
reported per locus and any CS variant carrying the floor-imputed prior is flagged.

The priors are functional enrichment priors estimated in UK Biobank (15 traits, not cognition). They are
NOT causal evidence and must not be used as such: a PIP increase driven by the prior says only that the data
are compatible with a functionally annotated variant, conditional on out-of-sample (1000G) LD.

Outputs
  reports/sprint5a/functional_finemapping.parquet   (locus, method, CS, variant, pip, prior, ...)
  reports/sprint5a/functional_finemapping_summary.csv
  data/interim/sprint5a/susie/<locus>/               (z, prior, fit json; R.bin deleted after use)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
import common as C  # noqa: E402
from gate_c_finemap import locus_inputs  # noqa: E402

POLYFUN_DIR = REPO / "data" / "interim" / "sprint5a" / "tools" / "polyfun"
POLYFUN_COMMIT = "8b17b4ec87fde11f8d216c049c08d1420cd25de6"
WORK = REPO / "data" / "interim" / "sprint5a" / "susie"
S4_WORK = REPO / "data" / "interim" / "sprint4" / "susie"
OUT = REPO / "reports" / "sprint5a"
R_SCRIPT = HERE / "polyfun_susie.R"
Q = 100  # PolyFun extract_snpvar.py default: max ratio between largest and smallest prior
PRIORITY = {  # 16 L1/L2 loci of reports/sprint5/locus_confidence_rank.csv + NEGR1, KIFC2, DNPH1
    "L51327": "ATXN2L", "L64067": "AKAP6", "L91869": "NT5DC2", "L51460": "SFMBT1", "L1803": "DPP4",
    "L3123": "BTN2A1", "L2131": "EXT1", "L60412": "EXOC4", "L1630": "DCC", "L3760": "KCNJ3",
    "L64116": "SLC39A8", "L7009": "DDN", "L9975": "NKIRAS1", "L100132074": "FOXO6", "L7324": "UBE2E1",
    "L64288": "ZSCAN31", "L257194": "NEGR1", "L65265": "KIFC2 (anchor FOXH1)", "L55168": "DNPH1 (anchor CUL9)"}
CODING = {"missense_variant", "stop_gained", "stop_lost", "start_lost", "frameshift_variant",
          "inframe_insertion", "inframe_deletion", "splice_acceptor_variant", "splice_donor_variant",
          "protein_altering_variant", "splice_region_variant", "synonymous_variant"}


def load_priors() -> pd.DataFrame:
    """Both PolyFun meta files, truncated exactly as extract_snpvar.py does (genome-wide, q=100)."""
    df = pd.concat([pd.read_parquet(POLYFUN_DIR / f) for f in
                    ("snpvar_meta.chr1_7.parquet", "snpvar_meta.chr8_22.parquet")], ignore_index=True)
    v = df["snpvar_bin"].astype(np.float64)
    min_v = v.max() / Q
    total = v.sum()
    v = v.where(v >= min_v, min_v)
    v *= total / v.sum()
    df["snpvar"] = v
    df["floor"] = float(v.min())
    a1, a2 = df.A1.astype(str), df.A2.astype(str)
    first = (a1 < a2) | (a1.str.len() > 1) | (a2.str.len() > 1)
    df["key"] = (df.CHR.astype(str) + "." + df.BP.astype(str) + "." + np.where(first, a1, a2) + "."
                 + np.where(first, a2, a1))
    return df[["key", "SNP", "snpvar", "floor"]]


def attach_prior(m: pd.DataFrame, pri: pd.DataFrame) -> pd.DataFrame:
    a1, a2 = m.a1.astype(str), m.a2.astype(str)
    first = a1 < a2
    key = m.chr.astype(str) + "." + m.pos.astype(str) + "." + np.where(first, a1, a2) + "." + np.where(first, a2, a1)
    got = pri.set_index("key").reindex(key)
    m = m.copy()
    m["polyfun_snpvar"] = got.snpvar.to_numpy()
    m["polyfun_rsid"] = got.SNP.to_numpy()
    m["prior_source"] = np.where(m.polyfun_snpvar.isna(), "FLOOR_IMPUTED_NOT_IN_POLYFUN", "POLYFUN_UKB_META15")
    m["polyfun_snpvar"] = m.polyfun_snpvar.fillna(float(pri["floor"].iloc[0]))
    m["prior"] = m.polyfun_snpvar / m.polyfun_snpvar.sum()
    return m


def vep(rsids: list[str]) -> dict[str, dict]:
    """Ensembl GRCh37 VEP REST (public, no key): most severe consequence + regulatory overlap."""
    out: dict[str, dict] = {}
    url = "https://grch37.rest.ensembl.org/vep/human/id"
    for i in range(0, len(rsids), 150):
        chunk = rsids[i:i + 150]
        data = None
        for attempt in range(4):
            req = urllib.request.Request(url, data=json.dumps({"ids": chunk}).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read())
                break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(5 * (attempt + 1))
        if data is None:
            for s in chunk:
                out[s] = {"vep_most_severe": "VEP_UNAVAILABLE"}
            continue
        for rec in data:
            tc = rec.get("transcript_consequences", []) or []
            coding = sorted({(t.get("gene_symbol"), c, t.get("amino_acids")) for t in tc
                             for c in t.get("consequence_terms", []) if c in CODING and c != "synonymous_variant"},
                            key=str)
            reg = sorted({t.get("biotype", "") for t in rec.get("regulatory_feature_consequences", []) or []})
            motif = bool(rec.get("motif_feature_consequences"))
            ms = rec.get("most_severe_consequence")
            ms_genes = sorted({t.get("gene_symbol") or "" for t in tc if ms in t.get("consequence_terms", [])} - {""})
            out[rec["input"]] = {"vep_most_severe": ms, "vep_most_severe_genes": ";".join(ms_genes) or None,
                                 "vep_coding": ";".join(f"{g}:{c}:{aa}" for g, c, aa in coding) or None,
                                 "vep_regulatory": ";".join(x for x in reg if x) or None,
                                 "vep_motif": motif}
        time.sleep(0.5)
    return out


def summarise(locus: str, method: str, fit: dict, m: pd.DataFrame, plain_pip: np.ndarray) -> dict:
    pip = np.asarray(fit["pip"], float)
    sets = fit.get("cs", [])
    sizes = [len(np.atleast_1d(c["idx"])) for c in sets]
    j = int(np.argmax(pip))
    jp = int(np.argmax(plain_pip))
    cross = [f"{m.snp[i]}({pip[i]:.2f})" for i in np.where(pip > 0.5)[0]]
    return {"locus_id": locus, "method": method, "n_cs": len(sets), "cs_sizes": ";".join(map(str, sizes)),
            "total_cs_variants": int(sum(sizes)), "min_cs_size": min(sizes) if sizes else None,
            "max_pip_variant": m.snp[j], "max_pip": float(pip[j]), "max_pip_prior_rel": float(m.prior[j] * len(m)),
            "plain_top_variant": m.snp[jp], "pip_of_plain_top_variant": float(pip[jp]),
            "variants_pip_gt_0.5": ";".join(cross) or None, "n_pip_gt_0.5": len(cross),
            "converged": fit.get("converged")}


def run(loci_ids: list[str], rscript: Path) -> None:
    frozen = C.load_frozen()
    loci = [l for l in frozen["loci"] if l["locus_id"] in set(loci_ids)]
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    davies = davies.drop_duplicates("Markername", keep=False)
    bim = pd.read_csv(str(C.BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                      names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
    bim["bed_index"] = np.arange(len(bim))
    pri = load_priors()
    rows, summ, diag = [], [], []
    for l in loci:
        lid = l["locus_id"]
        d = WORK / lid
        d.mkdir(parents=True, exist_ok=True)
        m, r = locus_inputs(l["chr"], int(l["lead_pos_grch37"]), davies, bim)
        s4 = pd.read_csv(S4_WORK / lid / "snps.tsv", sep="\t")
        same = len(s4) == len(m) and (s4.snp.to_numpy() == m.snp.to_numpy()).all() and \
            np.allclose(s4.z_a1.to_numpy(), m.z_a1.to_numpy(), atol=1e-3)
        if not same:
            raise SystemExit(f"{lid}: rebuilt SNP set differs from Sprint 4 — refusing to compare")
        m = attach_prior(m, pri)
        np.savetxt(d / "z.txt", m.z_a1.to_numpy())
        np.savetxt(d / "prior.txt", m.polyfun_snpvar.to_numpy())
        r.T.tofile(d / "R.bin")
        proc = subprocess.run([str(rscript), str(R_SCRIPT), str(d), str(C.DAVIES_N)], capture_output=True,
                              text=True, timeout=7200)
        (d / "R.bin").unlink(missing_ok=True)
        if not (d / "fit_sprint5a.json").exists():
            raise SystemExit(f"{lid}: R failed: {proc.stderr[-800:]}")
        fit = json.loads((d / "fit_sprint5a.json").read_text())
        m[["snp", "chr", "pos", "a1", "a2", "z_a1", "maf_1000g", "polyfun_snpvar", "prior", "prior_source"]].to_csv(
            d / "snps_priors.tsv", sep="\t", index=False)
        s4pip = np.asarray(json.loads((S4_WORK / lid / "fit.json").read_text())["pip"], float)
        plain_pip = np.asarray(fit["plain"]["pip"], float)
        repro = float(np.max(np.abs(plain_pip - s4pip)))
        diag.append({"locus_id": lid, "n_snps": len(m), "n_floor_imputed": int((m.prior_source != "POLYFUN_UKB_META15").sum()),
                     "estimate_s_rss": fit.get("s"), "ld_mismatch_flag": bool(fit.get("s") is not None and fit["s"] > 0.2),
                     "plain_vs_sprint4_max_abs_pip_diff": repro, "susieR": fit.get("susieR_version"),
                     "prior_max_over_min_in_locus": float(m.polyfun_snpvar.max() / m.polyfun_snpvar.min())})
        for method, key in (("SuSiE_plain_1000G", "plain"), ("PolyFun+SuSiE_1000G", "polyfun")):
            f = fit[key]
            if "error" in f:
                summ.append({"locus_id": lid, "method": method, "error": f["error"]})
                continue
            pip = np.asarray(f["pip"], float)
            other = np.asarray(fit["polyfun" if key == "plain" else "plain"]["pip"], float)
            summ.append(summarise(lid, method, f, m, plain_pip))
            incs = set()
            for cs in f.get("cs", []):
                idx = np.atleast_1d(np.array(cs["idx"])) - 1
                for i in idx:
                    incs.add(i)
                    rows.append({"locus_id": lid, "method": method, "credible_set": cs["name"], "cs_size": len(idx),
                                 "cs_min_abs_corr": cs.get("min_abs_corr"), "cs_coverage": cs.get("coverage"), "i": i})
            for i in np.where(pip >= 0.1)[0]:
                if i not in incs:
                    rows.append({"locus_id": lid, "method": method, "credible_set": "none", "cs_size": None,
                                 "cs_min_abs_corr": None, "cs_coverage": None, "i": i})
            for rr in rows:
                if rr["locus_id"] == lid and rr["method"] == method and "variant" not in rr:
                    i = rr.pop("i")
                    rr.update({"variant": m.snp[i], "chr": l["chr"], "pos_grch37": int(m.pos[i]), "a1": m.a1[i],
                               "a2": m.a2[i], "z_a1": float(m.z_a1[i]), "pip": float(pip[i]),
                               "pip_other_method": float(other[i]), "prior": float(m.prior[i]),
                               "prior_rel_to_uniform": float(m.prior[i] * len(m)),
                               "polyfun_snpvar": float(m.polyfun_snpvar[i]), "prior_source": m.prior_source[i]})
        print(diag[-1], flush=True)
    res = pd.DataFrame(rows)
    ann = vep(sorted(set(res.variant)))
    for c in ("vep_most_severe", "vep_most_severe_genes", "vep_coding", "vep_regulatory", "vep_motif"):
        res[c] = res.variant.map(lambda v: ann.get(v, {}).get(c))
    res["priority_locus"] = res.locus_id.isin(PRIORITY)
    res["priority_label"] = res.locus_id.map(PRIORITY)
    OUT.mkdir(parents=True, exist_ok=True)
    res.to_parquet(OUT / "functional_finemapping.parquet", index=False)
    sm = pd.DataFrame(summ).merge(pd.DataFrame(diag), on="locus_id", how="left")
    # locus-level comparison columns
    comp = []
    for lid, g in sm.groupby("locus_id"):
        p = g[g.method == "SuSiE_plain_1000G"].iloc[0]
        f = g[g.method == "PolyFun+SuSiE_1000G"].iloc[0]
        rp = res[(res.locus_id == lid) & (res.method == "PolyFun+SuSiE_1000G")]
        rq = res[(res.locus_id == lid) & (res.method == "SuSiE_plain_1000G")]
        cod_f = rp[rp.vep_coding.notna() & (rp.pip > rp.pip_other_method)]
        comp.append({"locus_id": lid,
                     "delta_n_cs": int(f.n_cs - p.n_cs) if pd.notna(f.n_cs) and pd.notna(p.n_cs) else None,
                     "delta_total_cs_variants": (f.total_cs_variants - p.total_cs_variants)
                     if pd.notna(f.get("total_cs_variants")) and pd.notna(p.get("total_cs_variants")) else None,
                     "max_pip_variant_changed": p.max_pip_variant != f.max_pip_variant,
                     "pip_shift_plain_top": f.pip_of_plain_top_variant - p.max_pip,
                     "new_pip_gt_0.5_under_polyfun": ";".join(sorted(set(str(f["variants_pip_gt_0.5"]).split(";"))
                                                                  - set(str(p["variants_pip_gt_0.5"]).split(";"))
                                                                  - {"None", "nan"})) or None,
                     "coding_variants_rising_in_polyfun_cs": ";".join(
                         f"{v}[{c}] {po:.3f}->{pf:.3f}" for v, c, po, pf in
                         zip(cod_f.variant, cod_f.vep_coding, cod_f.pip_other_method, cod_f.pip)) or None,
                     "coding_variants_in_plain_cs": ";".join(sorted(set(rq[rq.vep_coding.notna() & (rq.credible_set != 'none')].variant))) or None,
                     "coding_variants_in_polyfun_cs": ";".join(sorted(set(rp[rp.vep_coding.notna() & (rp.credible_set != 'none')].variant))) or None})
    sm = sm.merge(pd.DataFrame(comp), on="locus_id", how="left")
    sm["priority_label"] = sm.locus_id.map(PRIORITY)
    sm["polyfun_commit"] = POLYFUN_COMMIT
    sm.to_csv(OUT / "functional_finemapping_summary.csv", index=False)
    print(f"{len(res)} variant rows; {sm.locus_id.nunique()} loci")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--loci", default=str(C.DATA / "gate_c_loci.csv"))
    ap.add_argument("--rscript", default=str(C.RSCRIPT), help="Rscript with susieR (default: hi-sprint4 env)")
    a = ap.parse_args(argv)
    run(list(pd.read_csv(a.loci).locus_id), Path(a.rscript))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
