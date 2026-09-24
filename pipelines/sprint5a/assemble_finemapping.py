#!/usr/bin/env python3
"""Sprint 5A, Goal A — merge the LD-panel sensitivities into the Goal-A outputs.

Inputs
  reports/sprint5a/functional_finemapping.parquet        1000G-LD plain + PolyFun fits (polyfun_susie.py)
  data/interim/sprint5a/ukb_ld_sensitivity.parquet       UKB-LD, same SNPs, same settings (ukb_ld_sensitivity.py run)
  data/interim/sprint5a/finemapper_ukbld.parquet         PolyFun finemapper.py, UKB LD (ukb_ld_sensitivity.py finemapper)
Outputs (rewritten in place; 1000G rows are never modified)
  reports/sprint5a/functional_finemapping.parquet  + sensitivity rows (method column distinguishes them)
  reports/sprint5a/functional_finemapping_summary.csv  + one row per locus x sensitivity method, and for every
      variant reaching PIP > 0.5 under PolyFun+1000G its PIP under every other method (robustness columns).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from polyfun_susie import PRIORITY, vep  # noqa: E402

OUT = REPO / "reports" / "sprint5a"
BASE_METHODS = {"SuSiE_plain_1000G", "PolyFun+SuSiE_1000G"}


def full_pip(lid: str) -> dict[str, dict[str, float]]:
    """Per-SNP PIP for every sensitivity run at a locus (not only CS members)."""
    import json
    out: dict[str, dict[str, float]] = {}
    d = REPO / "data" / "interim" / "sprint5a" / "susie_ukbld" / lid
    if (d / "fit_sprint5a.json").exists():
        snps = pd.read_csv(d / "snps.tsv", sep="\t").snp.tolist()
        fit = json.loads((d / "fit_sprint5a.json").read_text())
        for k, meth in (("plain", "SuSiE_plain_UKBLD_sameSNPs"), ("polyfun", "PolyFun+SuSiE_UKBLD_sameSNPs")):
            if "pip" in fit[k]:
                out[meth] = dict(zip(snps, fit[k]["pip"]))
    fm = REPO / "data" / "interim" / "sprint5a" / "finemapper_ukbld"
    for tag in ("funct", "nonfunct"):
        f = fm / f"{lid}.{tag}.gz"
        if f.exists():
            t = pd.read_csv(f, sep="\t")
            out[f"PolyFun_finemapper_{tag}_UKBLD"] = dict(zip(t.SNP, t.PIP))
    return out


def main() -> int:
    base = pd.read_parquet(OUT / "functional_finemapping.parquet")
    base = base[base.method.isin(BASE_METHODS)]
    summ = pd.read_csv(OUT / "functional_finemapping_summary.csv")
    summ = summ[summ.method.isin(BASE_METHODS)]
    extra, srows = [], []
    ukb_p = REPO / "data" / "interim" / "sprint5a" / "ukb_ld_sensitivity.parquet"
    fm_p = REPO / "data" / "interim" / "sprint5a" / "finemapper_ukbld.parquet"
    if ukb_p.exists():
        u = pd.read_parquet(ukb_p)
        if "error" in u:
            for r in u[u.error.notna()].itertuples():
                srows.append({"locus_id": r.locus_id, "method": "UKBLD_sameSNPs (plain and PolyFun)", "error": r.error})
            u = u[u.error.isna()]
        for (lid, meth), g in u.groupby(["locus_id", "method"]):
            cs = g[~g.credible_set.isin(["max_pip"])]
            mx = g[g.credible_set == "max_pip"].iloc[0]
            sizes = cs.groupby("credible_set").size()
            fp = full_pip(lid).get(meth, {})
            gt = {v: q for v, q in fp.items() if q > 0.5}
            srows.append({"locus_id": lid, "method": meth, "n_cs": len(sizes), "cs_sizes": ";".join(map(str, sizes)),
                          "total_cs_variants": int(sizes.sum()), "max_pip_variant": mx.variant, "max_pip": mx.pip,
                          "variants_pip_gt_0.5": ";".join(f"{v}({q:.2f})" for v, q in gt.items()) or None,
                          "n_pip_gt_0.5": len(gt),
                          "n_snps": mx.n_snps, "estimate_s_rss": mx.estimate_s_rss, "converged": mx.converged,
                          "ld_panel": f"UKB 337K British ({mx.ukb_region})"})
            rows = cs.copy()
            if mx.variant not in set(cs.variant):
                rows = pd.concat([rows, pd.DataFrame([{**mx.to_dict(), "credible_set": "none"}])])
            extra.append(rows)
    if fm_p.exists():
        f = pd.read_parquet(fm_p)
        if "error" in f:
            for r in f[f.error.notna()].drop_duplicates("locus_id").itertuples():
                srows.append({"locus_id": r.locus_id, "method": "PolyFun_finemapper_UKBLD", "error": r.error})
            f = f[f.error.isna()]
        fm_dir = REPO / "data" / "interim" / "sprint5a" / "finemapper_ukbld"
        for (lid, meth), g in f.groupby(["locus_id", "method"]):
            extra.append(g)
        for lid in sorted(set(f.locus_id)):
            for tag in ("funct", "nonfunct"):
                fo = fm_dir / f"{lid}.{tag}.gz"
                if not fo.exists():
                    continue
                t = pd.read_csv(fo, sep="\t")  # full per-SNP output (not only CS / PIP>=0.1 rows)
                sizes = t[t.CREDIBLE_SET > 0].groupby("CREDIBLE_SET").size()
                j = t.PIP.idxmax()
                gt = t[t.PIP > 0.5]
                srows.append({"locus_id": lid, "method": f"PolyFun_finemapper_{tag}_UKBLD", "n_cs": len(sizes),
                              "cs_sizes": ";".join(map(str, sizes)), "total_cs_variants": int(sizes.sum()),
                              "max_pip_variant": t.SNP[j], "max_pip": float(t.PIP[j]),
                              "variants_pip_gt_0.5": ";".join(f"{v}({q:.2f})" for v, q in zip(gt.SNP, gt.PIP)) or None,
                              "n_pip_gt_0.5": len(gt), "n_snps": len(t),
                              "ld_panel": "UKB 337K British (PolyFun finemapper; susieR 0.11.92; resid. var. estimated)"})
    ex = pd.concat(extra, ignore_index=True) if extra else pd.DataFrame()
    if len(ex):
        known = base.drop_duplicates("variant").set_index("variant")
        new = sorted(set(ex.variant) - set(known.index))
        ann = vep(new) if new else {}
        for c in ("vep_most_severe", "vep_most_severe_genes", "vep_coding", "vep_regulatory", "vep_motif"):
            ex[c] = ex.variant.map(lambda v: known[c].get(v) if v in known.index else ann.get(v, {}).get(c))
        ex["priority_locus"] = ex.locus_id.isin(PRIORITY)
        ex["priority_label"] = ex.locus_id.map(PRIORITY)
        ex = ex.drop(columns=[c for c in ("n_snps", "n_snps_1000g", "estimate_s_rss", "ukb_region", "converged", "error")
                              if c in ex.columns])
    allr = pd.concat([base, ex], ignore_index=True)
    allr.to_parquet(OUT / "functional_finemapping.parquet", index=False)
    s = pd.concat([summ.assign(ld_panel="1000G EUR (n=503)"), pd.DataFrame(srows)], ignore_index=True)
    s["priority_label"] = s.locus_id.map(PRIORITY)
    # robustness of every variant with PIP > 0.5 under either 1000G fit
    pf = base[base.pip > 0.5]
    rob = []
    for r in pf.drop_duplicates(["locus_id", "variant"]).itertuples():
        both = (base[(base.locus_id == r.locus_id) & (base.variant == r.variant)]
                .sort_values("pip", ascending=False).drop_duplicates("method").set_index("method"))
        pp = both.pip.get("PolyFun+SuSiE_1000G", both.pip_other_method.get("SuSiE_plain_1000G", np.nan))
        pq = both.pip.get("SuSiE_plain_1000G", both.pip_other_method.get("PolyFun+SuSiE_1000G", np.nan))
        d = {"locus_id": r.locus_id, "priority_label": PRIORITY.get(r.locus_id), "variant": r.variant,
             "pip_plain_1000G": pq, "pip_PolyFun_1000G": pp,
             "vep": r.vep_coding if pd.notna(r.vep_coding) else r.vep_most_severe,
             "vep_genes": r.vep_most_severe_genes, "prior_rel_to_uniform": r.prior_rel_to_uniform, "z": r.z_a1}
        for meth, pip in full_pip(r.locus_id).items():
            d[f"pip_{meth}"] = pip.get(r.variant, np.nan)
        rob.append(d)
    pd.DataFrame(rob).to_csv(OUT / "functional_finemapping_pip05_robustness.csv", index=False)
    s.to_csv(OUT / "functional_finemapping_summary.csv", index=False)
    print(len(allr), "variant rows;", len(s), "summary rows;", len(rob), "PolyFun PIP>0.5 variants checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
