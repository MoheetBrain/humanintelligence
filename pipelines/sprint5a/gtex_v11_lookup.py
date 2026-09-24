#!/usr/bin/env python3
"""Sprint 5A — GTEx V11 (GENCODE v47; open release 2026-01-15) brain eQTL / sQTL / SuSiE lookup of the cognition
credible-set variants (GRCh38), and comparison with the Sprint-4 gene-level adult-brain directions.

V11 open files are SIGNIFICANT pairs (permutation q<=0.05 eGenes, nominal p <= gene threshold) + SuSiE credible sets.
All-pairs statistics are in the requester-pays bucket gs://gtex-resources -> not fetched (blocker), so V11 cannot
be colocalised here; this is a lead-variant / credible-set LOOKUP, not a coloc.

Slope is per ALT allele of chr_pos_REF_ALT_b38 (GTEx convention, README_eQTL_v11.txt). aligned_slope = slope for the
cognition-increasing allele. Palindromic (A/T, C/G) variants are kept but excluded from the direction majority.

Outputs: reports/sprint5a/gtex_v11_lookup.csv (variant x gene x tissue x qtl_type rows),
         reports/sprint5a/gtex_v11_gene_direction.csv (locus x gene summary vs Sprint 4).
"""
from __future__ import annotations

import gzip
import io
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "pipelines" / "sprint5"))
import brainscope_lookup as BL  # noqa: E402
from brainscope_typed_evidence import query_variants  # noqa: E402

V11 = ROOT / "data/interim/sprint5a/gtex_v11"
OUT = ROOT / "reports/sprint5a"


def parse_vid(s: pd.Series) -> pd.DataFrame:
    p = s.str.split("_", expand=True)
    return pd.DataFrame({"chr": p[0].str.replace("chr", "", regex=False), "pos": p[1].astype(np.int64), "ref": p[2],
                         "alt": p[3]})


def main() -> None:
    qv = query_variants()
    qv = qv[qv.trait.str.startswith("cognition")]
    keys = set(zip(qv.chr38, qv.pos38))
    sym = {}
    rows = []
    for kind, sub, suffix in (("eQTL", "GTEx_Analysis_v11_eQTL", ".v11.eQTLs.signif_pairs.parquet"),
                              ("sQTL", "GTEx_Analysis_v11_sQTL", ".v11.sQTLs.signif_pairs.parquet")):
        for f in sorted((V11 / sub).glob(f"*{suffix}")):
            tissue = f.name.replace(suffix, "")
            eg = f.parent / f.name.replace(suffix, ".v11.eGenes.txt.gz" if kind == "eQTL" else ".v11.sGenes.txt.gz")
            if eg.exists():
                e = pd.read_csv(eg, sep="\t", usecols=["gene_id", "gene_name"])
                sym.update(dict(zip(e.gene_id, e.gene_name)))
            d = pd.read_parquet(f)
            v = parse_vid(d.variant_id)
            m = np.fromiter(((c, p) in keys for c, p in zip(v.chr, v.pos)), bool, len(v))
            d, v = d[m].reset_index(drop=True), v[m].reset_index(drop=True)
            d = pd.concat([d, v], axis=1)
            d["gene_id"] = d.group_id if kind == "sQTL" else d.phenotype_id
            d["tissue"], d["qtl_type"] = tissue, kind
            rows.append(d)
    hits = pd.concat(rows, ignore_index=True)
    out = []
    qi = qv.set_index(["chr38", "pos38"])
    for h in hits.itertuples(index=False):
        for r in qi.loc[[(h.chr, h.pos)]].reset_index().itertuples(index=False):
            st, inc = BL.match_alleles(r.increasing_allele, r.other_allele_trait, h.ref, h.alt)
            if st == "ALLELE_MISMATCH":
                continue
            s = 1 if inc == h.alt else (-1 if inc == h.ref else 0)
            out.append({"locus_id": r.locus_id, "gate_c_locus": r.gate_c_locus, "rsid": r.rsid, "origin": r.origin,
                        "susie_pip_gwas": r.susie_pip, "chr38": h.chr, "pos38": h.pos, "ref": h.ref, "alt": h.alt,
                        "cognition_increasing_allele": r.increasing_allele, "alignment_status": st,
                        "qtl_type": h.qtl_type, "tissue": h.tissue, "gene_id_v47": h.gene_id,
                        "gene": sym.get(h.gene_id), "phenotype_id": h.phenotype_id, "af_alt": h.af,
                        "pval_nominal": h.pval_nominal, "slope_alt": h.slope, "slope_se": h.slope_se,
                        "pval_beta_gene": h.pval_beta, "aligned_slope": h.slope * s if s else np.nan})
    lk = pd.DataFrame(out)
    # SuSiE credible-set membership (brain tissues)
    sus = []
    with tarfile.open(V11 / "GTEx_Analysis_v11_eQTL_SuSiE.tar") as tf:
        for mbr in tf.getmembers():
            if "Brain" not in mbr.name:
                continue
            d = pd.read_parquet(io.BytesIO(tf.extractfile(mbr).read()))
            d["tissue"] = Path(mbr.name).name.replace(".v11.eQTLs.SuSiE_summary.parquet", "")
            sus.append(d)
    sus = pd.concat(sus, ignore_index=True).rename(columns={"phenotype_id": "gene_id"})
    sv = parse_vid(sus.variant_id)
    sus = pd.concat([sus, sv], axis=1)
    sus = sus[[(c, p) in keys for c, p in zip(sus.chr, sus.pos)]]
    sk = sus.set_index(["tissue", "gene_id", "chr", "pos"])
    lk["v11_susie_cs"] = [f"cs{int(sk.loc[k].cs_id if not isinstance(sk.loc[k], pd.DataFrame) else sk.loc[k].cs_id.iloc[0])}"
                          if k in sk.index else None
                          for k in zip(lk.tissue, lk.gene_id_v47, lk.chr38, lk.pos38)]
    lk["v11_susie_pip"] = [float(sk.loc[k].pip if not isinstance(sk.loc[k], pd.DataFrame) else sk.loc[k].pip.max())
                           if k in sk.index else np.nan for k in zip(lk.tissue, lk.gene_id_v47, lk.chr38, lk.pos38)]
    lk.loc[lk.qtl_type == "sQTL", ["v11_susie_cs", "v11_susie_pip"]] = [None, np.nan]
    lk["aligned_direction"] = np.where(lk.aligned_slope > 0, "HIGHER", np.where(lk.aligned_slope < 0, "LOWER", None))
    lk.loc[lk.alignment_status == "PALINDROMIC_AMBIGUOUS", "aligned_direction"] = "AMBIGUOUS_PALINDROMIC"
    lk = lk.sort_values(["locus_id", "gene", "qtl_type", "tissue", "pval_nominal"])
    lk.to_parquet(OUT / "gtex_v11_lookup_full.parquet", index=False)  # eQTL + sQTL, all columns
    slim = lk[lk.qtl_type == "eQTL"][["locus_id", "gate_c_locus", "rsid", "chr38", "pos38", "ref", "alt",
                                      "cognition_increasing_allele", "alignment_status", "tissue", "gene", "gene_id_v47",
                                      "pval_nominal", "slope_alt", "slope_se", "aligned_slope", "aligned_direction",
                                      "v11_susie_cs", "v11_susie_pip"]].copy()
    slim["tissue"] = slim.tissue.str.replace("Brain_", "", regex=False)
    slim.to_csv(OUT / "gtex_v11_lookup.csv", index=False, float_format="%.3g")  # eQTL rows, < 5 MiB
    # SuSiE-only credible-set rows for query variants (for completeness)
    sus.to_csv(OUT / "gtex_v11_susie_query_overlap.csv", index=False, float_format="%.4g")

    # gene-level direction vs Sprint 4
    s4 = pd.read_csv(ROOT / "reports/sprint4/directionality_resolution.csv")
    e = lk[(lk.qtl_type == "eQTL") & lk.aligned_direction.isin(["HIGHER", "LOWER"])]
    gs = []
    for (loc, gene), g in e.groupby(["locus_id", "gene"]):
        # one call per tissue (majority of the credible-set variants significant in that tissue)
        tcalls = {t: ("HIGHER" if (gg.aligned_direction == "HIGHER").sum() > (gg.aligned_direction == "LOWER").sum()
                      else "LOWER" if (gg.aligned_direction == "LOWER").sum() > (gg.aligned_direction == "HIGHER").sum()
                      else "TIE") for t, gg in g.groupby("tissue")}
        vals = [v for v in tcalls.values() if v != "TIE"]
        nh = vals.count("HIGHER")
        v11dir = "HIGHER" if vals and nh == len(vals) else ("LOWER" if vals and nh == 0 else ("MIXED" if vals else "TIE"))
        cs_t = sorted(set(g[g.v11_susie_cs.notna()].tissue))
        r4 = s4[(s4.gene == gene) & (s4.locus_id == loc)]
        lab4 = r4.label.iloc[0] if len(r4) else "GENE_NOT_IN_SPRINT4_TABLE"
        maj4 = r4.rows_majority_sign.iloc[0] if len(r4) else np.nan
        s4dir = "HIGHER" if maj4 == 1 else ("LOWER" if maj4 == -1 else "NONE")
        if s4dir == "NONE":
            change = "NO_SPRINT4_DIRECTION (V11 adds rows-level evidence only)"
        elif v11dir in ("HIGHER", "LOWER"):
            change = "AGREES" if v11dir == s4dir else "CONFLICTS"
        else:
            change = f"V11_{v11dir}"
        gs.append({"locus_id": loc, "gene": gene, "gate_c_locus": bool(g.gate_c_locus.iloc[0]),
                   "n_tissues_sig": len(tcalls), "tissues": ";".join(sorted(tcalls)),
                   "tissue_calls": ";".join(f"{k}:{v}" for k, v in sorted(tcalls.items())),
                   "v11_direction_cognition_allele": v11dir, "n_query_variants_sig": g.rsid.nunique(),
                   "min_p": g.pval_nominal.min(), "v11_susie_cs_tissues": ";".join(cs_t) or None,
                   "max_v11_susie_pip_query_variant": g.v11_susie_pip.max(),
                   "sprint4_label": lab4, "sprint4_majority_direction": s4dir, "v11_vs_sprint4": change})
    gd = pd.DataFrame(gs).sort_values(["gate_c_locus", "locus_id", "gene"], ascending=[False, True, True])
    gd.to_csv(OUT / "gtex_v11_gene_direction.csv", index=False, float_format="%.4g")
    print(lk.qtl_type.value_counts(), lk.locus_id.nunique(), lk.gene.nunique())
    print(gd[gd.gate_c_locus].to_string(max_colwidth=40))


if __name__ == "__main__":
    main()
