#!/usr/bin/env python3
"""Sprint 5A section 6 — summarise AlphaGenome Atlas predictions (alphagenome 0.9.0; run with the user's API key via
environment only) and compare them with OBSERVED human molecular data.

AlphaGenome is PREDICTIVE. Frozen rule (Sprint-5 protocol, alphagenome): strong effect = |quantile score| >= 0.99 in
>= 1 brain/neural track (tiers CORTEX or BRAIN; NEURAL_DEV_OR_LINE and SPINAL_PERIPHERAL reported separately);
never ranked alone. A prediction gets weight only if an observed human QTL agrees on gene AND direction.

Per variant x gene: RNA-seq expression prediction (signed; direction for the cognition-increasing allele), best
brain tracks, splicing (junctions/site usage; unsigned), chromatin (DNase/ATAC; signed), histone/TF (signed), AVI.
Observed comparators: Sprint-4 adult bulk coloc direction (reports/sprint4/directionality_resolution.csv),
brainSCOPE cell-type direction (reports/sprint5/cell_specific_directionality.csv), Open Targets 26.06 brain eQTL
colocs (reports/sprint5a/opentargets_2606_colocs.parquet; beta-ratio sign relative to the GWAS effect).

Outputs: reports/sprint5a/alphagenome_variant_predictions.parquet, reports/sprint5a/alphagenome_cognition_variants.parquet,
reports/sprint5a/alphagenome_math53.csv, reports/sprint5a/alphagenome_vs_observed.csv, data/sprint5a/alphagenome_provenance.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
OUT = R / "reports/sprint5a"
BRAIN = {"CORTEX", "BRAIN"}
STRONG = 0.99
BRAIN_RX = re.compile(r"brain|cortex|gyrus|caudate|neur|astrocyte|hippoc|cerebell|putamen|frontal|amygdal|accumbens|"
                      r"hypothalam|substantia|nigra|thalam|glutamat", re.I)


def cog_sign(row) -> float:
    d = row.direction_for_cognition_increasing_allele
    return 1.0 if d == "UP" else -1.0 if d == "DOWN" else np.nan


def summarise(raw: pd.DataFrame, label: str, allele_map: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = raw.copy()
    if allele_map:
        # recompute the increasing-allele orientation from REF/ALT directly (fills alleles missing at query time)
        inc = raw.rsid.map(allele_map).astype("string").str.upper()
        alt, ref = raw.alt.astype("string").str.upper(), raw.ref.astype("string").str.upper()
        e_alt = (inc == alt).fillna(False).to_numpy(bool)
        e_ref = (inc == ref).fillna(False).to_numpy(bool)
        orient = pd.Series(np.where(e_alt, 1.0, np.where(e_ref, -1.0, np.nan)), index=raw.index)
        raw["direction_for_cognition_increasing_allele"] = np.where(
            orient.isna(), "ALLELE_MISMATCH", np.where(np.sign(raw.raw_score) * orient > 0, "UP",
                                                       np.where(np.sign(raw.raw_score) * orient < 0, "DOWN", "ZERO")))
    raw["cog_sign"] = raw.apply(cog_sign, axis=1)
    raw["abs_q"] = raw.quantile_score.abs()
    # keep the row whose ALT is the (cognition/math)-increasing allele or its complement pairing, i.e. drop
    # ALLELE_MISMATCH rows (other ALT of a multi-allelic site) when a matching row exists
    raw = raw[raw.direction_for_cognition_increasing_allele.astype(str) != "ALLELE_MISMATCH"]
    brain = raw[raw.brain_tier.isin(BRAIN)]
    rows = []
    rna = brain[brain.scorer == "RNA_SEQ"].dropna(subset=["gene_name"])
    for (rsid, gene), g in rna.groupby(["rsid", "gene_name"]):
        top = g.loc[g.abs_q.idxmax()]
        signs = np.sign(g.raw_score) * g.cog_sign
        strong = g[g.abs_q >= STRONG]
        rows.append({"set": label, "rsid": rsid, "gene": gene, "modality": "EXPRESSION_RNA_SEQ",
                     "max_abs_quantile": float(top.abs_q), "n_brain_tracks": int(len(g)),
                     "n_strong_tracks": int(len(strong)), "strong": bool(len(strong)),
                     "top_track": f"{top.biosample_name} | {top.assay}",
                     "direction_cognition_allele": ("UP" if np.nansum(np.sign(strong.raw_score) * strong.cog_sign) > 0 else
                                                    "DOWN" if np.nansum(np.sign(strong.raw_score) * strong.cog_sign) < 0 else
                                                    ("UP" if top.raw_score * top.cog_sign > 0 else "DOWN" if top.raw_score * top.cog_sign < 0 else "NA")),
                     "sign_consistency_strong": float(np.nanmean(np.sign(strong.raw_score) * strong.cog_sign > 0)) if len(strong) else np.nan,
                     "median_sign_all_tracks": float(np.nanmedian(signs)) if len(signs) else np.nan})
    for mod, scorers in (("SPLICING", ["SPLICE_JUNCTIONS", "SPLICE_SITE_USAGE", "SPLICE_SITES"]),):
        sp = brain[brain.scorer.isin(scorers)].dropna(subset=["gene_name"])
        for (rsid, gene), g in sp.groupby(["rsid", "gene_name"]):
            top = g.loc[g.abs_q.idxmax()]
            rows.append({"set": label, "rsid": rsid, "gene": gene, "modality": mod, "max_abs_quantile": float(top.abs_q),
                         "n_brain_tracks": int(len(g)), "n_strong_tracks": int((g.abs_q >= STRONG).sum()),
                         "strong": bool((g.abs_q >= STRONG).any()), "top_track": f"{top.biosample_name} | {top.scorer}",
                         "direction_cognition_allele": "UNSIGNED"})
    for mod, scorers in (("CHROMATIN", ["DNASE", "ATAC"]), ("HISTONE", ["CHIP_HISTONE"]), ("TF", ["CHIP_TF"]), ("CAGE", ["CAGE"])):
        ch = brain[brain.scorer.isin(scorers)]
        for rsid, g in ch.groupby("rsid"):
            top = g.loc[g.abs_q.idxmax()]
            rows.append({"set": label, "rsid": rsid, "gene": None, "modality": mod, "max_abs_quantile": float(top.abs_q),
                         "n_brain_tracks": int(len(g)), "n_strong_tracks": int((g.abs_q >= STRONG).sum()),
                         "strong": bool((g.abs_q >= STRONG).any()),
                         "top_track": f"{top.biosample_name} | {top.assay} {'' if pd.isna(top.histone_mark) else top.histone_mark}{'' if pd.isna(top.transcription_factor) else top.transcription_factor}",
                         "direction_cognition_allele": ("NA" if pd.isna(top.cog_sign) else "UP" if top.raw_score * top.cog_sign > 0 else "DOWN" if top.raw_score * top.cog_sign < 0 else "NA")})
    pred = pd.DataFrame(rows)
    avi = raw[raw.scorer == "AVI_SCORE"].groupby("rsid").agg(avi_raw=("raw_score", "max"), avi_quantile=("quantile_score", "max"))
    fi = raw[raw.scorer == "AVI_SCORE_FEATURE_IMPORTANCE"]
    feat = fi.assign(a=fi.raw_score.abs()).sort_values("a", ascending=False).groupby("rsid").apply(
        lambda g: ";".join(f"{t}:{v:.2f}" for t, v in zip(g.track_name.astype(str).head(3), g.raw_score.head(3))))
    var = pred.groupby("rsid").apply(lambda g: pd.Series({
        "n_strong_expression_genes": int(g[(g.modality == "EXPRESSION_RNA_SEQ") & g.strong].gene.nunique()),
        "top_expression_gene": (g[g.modality == "EXPRESSION_RNA_SEQ"].sort_values("max_abs_quantile", ascending=False).gene.head(1).tolist() or [None])[0],
        "top_expression_quantile": g[g.modality == "EXPRESSION_RNA_SEQ"].max_abs_quantile.max(),
        "top_expression_direction": (g[g.modality == "EXPRESSION_RNA_SEQ"].sort_values("max_abs_quantile", ascending=False).direction_cognition_allele.head(1).tolist() or [None])[0],
        "strong_splicing": bool(g[(g.modality == "SPLICING")].strong.any()),
        "strong_chromatin": bool(g[(g.modality == "CHROMATIN")].strong.any()),
        "strong_histone_or_tf": bool(g[g.modality.isin(["HISTONE", "TF"])].strong.any()),
        "any_strong_brain": bool(g.strong.any())})).reset_index()
    var = var.merge(avi, on="rsid", how="left")
    var["avi_top_features"] = var.rsid.map(feat)
    var["set"] = label
    return pred, var


def observed() -> pd.DataFrame:
    rows = []
    d = pd.read_csv(R / "reports/sprint4/directionality_resolution.csv")
    for r in d[d.rows_n_rows > 0].itertuples():
        rows.append({"gene": r.gene, "source": f"adult bulk coloc ({r.label})",
                     "obs_direction": "UP" if r.rows_majority_sign > 0 else "DOWN" if r.rows_majority_sign < 0 else "NA"})
    s = pd.read_csv(R / "reports/sprint5/cell_specific_directionality.csv")
    s = s[(s.status == "SIGNIFICANT") & s.ld_tagging.isin(["EQTL_LEAD_IN_GWAS_CREDIBLE_SET", "EQTL_LEAD_TAGS_GWAS_LEAD_R2_GE_0.8"])]
    for (g, dr), x in s.groupby(["gene", "aligned_direction"]):
        if dr in ("HIGHER", "LOWER"):
            rows.append({"gene": g, "source": f"brainSCOPE ({len(x)} cell types)", "obs_direction": "UP" if dr == "HIGHER" else "DOWN"})
    dv = pd.read_csv(R / "reports/sprint5/developmental_qtl_coloc.csv")
    dv = dv[dv["PP.H4"] >= 0.8]
    for (g, dr), x in dv.groupby(["gene", "direction"]):
        rows.append({"gene": g, "source": f"developmental coloc ({';'.join(sorted(set(x.study_label)))})",
                     "obs_direction": "UP" if "HIGHER" in dr else "DOWN" if "LOWER" in dr else "NA"})
    sc = OUT / "sc_eqtl_coloc_summary.csv"
    if sc.exists():
        z = pd.read_csv(sc)
        dcol = next((c_ for c_ in z.columns if "direction" in c_.lower()), None)
        gcol = next((c_ for c_ in ("gene", "gene_name", "symbol") if c_ in z.columns), None)
        if dcol and gcol:
            for r in z.dropna(subset=[dcol]).itertuples():
                dd = str(getattr(r, dcol)).upper()
                if "HIGH" in dd or "LOW" in dd or dd in ("UP", "DOWN"):
                    rows.append({"gene": getattr(r, gcol), "source": "single-cell eQTL coloc (Sprint 5A)",
                                 "obs_direction": "UP" if ("HIGH" in dd or dd == "UP") else "DOWN"})
    c = pd.read_parquet(OUT / "opentargets_2606_colocs.parquet")
    c = c[(c.qtl_type.isin(["eqtl", "sceqtl"])) & (c.h4 >= 0.8) & c.biosample.astype(str).str.contains(BRAIN_RX)
          & c.beta_ratio_sign.notna() & (c.is_trans != True)]
    import sys
    sys.path.insert(0, str(R / "pipelines/gene_tournament"))
    from build_consensus import NEG_POLARITY_RX  # Sprint-3 trait-polarity rule (higher = worse traits)
    pol = np.where(c.trait.astype(str).str.contains(NEG_POLARITY_RX), -1, 1)
    c = c.assign(sgn=np.sign(c.beta_ratio_sign) * pol)
    for (g, sgn), x in c.groupby(["qtl_gene", "sgn"]):
        # OT beta ratio sign = sign(QTL beta / GWAS beta), flipped for higher-is-worse cognition traits
        rows.append({"gene": g, "source": f"SECONDARY Open Targets brain coloc ({len(x)} rows; sign varies by study)",
                     "obs_direction": "UP" if sgn > 0 else "DOWN"})
    return pd.DataFrame(rows)


def main() -> int:
    cog = pd.read_parquet(R / "data/interim/sprint5a/alphagenome_cognition_raw.parquet")
    qa = pd.read_csv(R / "data/sprint5a/alphagenome_query_cognition.csv")
    pc, vc = summarise(cog, "cognition_credible", dict(zip(qa.rsid, qa.cognition_increasing_allele)))
    mf = R / "data/interim/sprint5a/alphagenome_math53_raw.parquet"
    qm = pd.read_csv(R / "data/sprint5a/alphagenome_query_math53.csv")
    pm, vm = summarise(pd.read_parquet(mf), "math53_increasing_allele", dict(zip(qm.rsid, qm.cognition_increasing_allele))) \
        if mf.exists() else (pd.DataFrame(), pd.DataFrame())
    pred = pd.concat([pc, pm], ignore_index=True)
    pred.to_parquet(OUT / "alphagenome_variant_predictions.parquet", index=False)
    q = pd.read_csv(R / "data/sprint5a/alphagenome_query_cognition.csv")
    vc = vc.merge(q[["rsid", "locus_id", "cognition_increasing_allele"]], on="rsid", how="left")
    vc.to_parquet(OUT / "alphagenome_cognition_variants.parquet", index=False)
    if len(vm):
        mm = pd.read_csv(R / "reports/sprint5/math53_gene_mapping.csv")[["rsid", "overlap_class", "nearest_gene_label_only", "v2g_nonpositional_genes"]]
        vm.merge(mm, on="rsid", how="left").to_csv(OUT / "alphagenome_math53.csv", index=False)
    # compare strong expression predictions (cognition set) with observed QTL direction
    obs = observed()
    se = pc[(pc.modality == "EXPRESSION_RNA_SEQ") & pc.strong].merge(q[["rsid", "locus_id"]], on="rsid", how="left")
    cmp_ = se.merge(obs, on="gene", how="left")
    cmp_["agreement"] = np.where(cmp_.obs_direction.isna(), "NO_OBSERVED_QTL_FOR_GENE",
                                 np.where(cmp_.obs_direction == cmp_.direction_cognition_allele, "AGREE", "DISAGREE"))
    cmp_["comparator_tier"] = np.where(cmp_.source.astype(str).str.startswith("SECONDARY"), "SECONDARY_OT", "PRIMARY_MEASURED")
    cmp_.to_csv(OUT / "alphagenome_vs_observed.csv", index=False)
    st = json.loads((R / "data/interim/sprint5a/alphagenome_cognition_raw.status.json").read_text())
    prov = {"client": "alphagenome 0.9.0 (Atlas, precomputed)", "status_cognition": {k: v for k, v in st.items() if "key" not in k.lower()},
            "api_key": "supplied by the user via environment variable only; never written to disk",
            "variants_queried": {"cognition": int(len(q)), "math53": int(len(vm))},
            "strong_threshold": STRONG, "brain_tiers_used": sorted(BRAIN),
            "n_strong_expression_pairs": int(len(se)),
            "agreement_counts_primary_measured": cmp_[cmp_.comparator_tier == "PRIMARY_MEASURED"].agreement.value_counts().to_dict(),
            "agreement_counts_secondary_ot": cmp_[cmp_.comparator_tier == "SECONDARY_OT"].agreement.value_counts().to_dict()}
    (R / "data/sprint5a/alphagenome_provenance.json").write_text(json.dumps(prov, indent=2, default=str))
    print(json.dumps(prov, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
