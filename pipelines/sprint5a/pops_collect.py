#!/usr/bin/env python3
"""Sprint 5A, Goal B — collect leave-one-chromosome-out PoPS scores and rank genes within the 159 loci.

Locus membership (union, tagged by source):
  * BONFERRONI  — the MAGMA Bonferroni genes of each of the 159 frozen loci (research/sprint4/frozen_hypotheses.json,
                  identical to reports/sprint4/genc_independent_loci.csv bonferroni_genes), Entrez -> Ensembl via
                  data/raw/magma_x01/2026-09-22/gene_id_map.tsv (unique mappings only);
  * QUERY_WINDOW — the Gate-C query genes of the 36 fine-mapped loci (data/sprint4/gate_c_query_genes.csv).
rank_in_locus is computed over member genes that have a PoPS score (genes absent from PoPS' 18,383-gene
annotation have no score and no rank).

PoPS is genome-wide feature-based prioritisation: NOT local causal evidence, NOT a variant-to-gene vote.

Output: reports/sprint5a/pops_scores.csv; data/interim/sprint5a/pops/pops_loco_genomewide.tsv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
import common as C  # noqa: E402

W = REPO / "data" / "interim" / "sprint5a" / "pops"
ANNOT = REPO / "data" / "interim" / "sprint5a" / "tools" / "pops" / "example" / "data" / "utils" / "gene_annot_jun10.txt"
OUT = REPO / "reports" / "sprint5a"


def main() -> int:
    annot = pd.read_csv(ANNOT, sep="\t")
    annot["CHR"] = annot.CHR.astype(str)
    parts, fits = [], []
    for k in range(1, 23):
        p = pd.read_csv(W / "loco" / f"chr{k}.preds", sep="\t")
        g = set(annot[annot.CHR == str(k)].ENSGID)
        parts.append(p[p.ENSGID.isin(g)][["ENSGID", "PoPS_Score", "Y", "Y_proj"]])
        coefs = pd.read_csv(W / "loco" / f"chr{k}.coefs", sep="\t", index_col=0)
        marg = pd.read_csv(W / "loco" / f"chr{k}.marginals", sep="\t", index_col=0)
        fits.append({"held_out_chr": k, "alpha": float(coefs.loc["SELECTED_CV_ALPHA", "beta"]),
                     "best_cv_score": float(coefs.loc["BEST_CV_SCORE", "beta"]),
                     "n_features_selected": int(marg.selected.sum()), "n_features_tested": int(len(marg))})
    gw = pd.concat(parts, ignore_index=True).merge(annot[["ENSGID", "NAME", "CHR", "TSS"]], on="ENSGID", how="left")
    gw["pops_genomewide_percentile"] = gw.PoPS_Score.rank(pct=True)
    gw["pops_genomewide_rank"] = gw.PoPS_Score.rank(ascending=False, method="min").astype(int)
    gw.to_csv(W / "pops_loco_genomewide.tsv", sep="\t", index=False)
    pd.DataFrame(fits).to_csv(W / "pops_loco_fits.csv", index=False)

    gm_all = pd.read_csv(C.GENE_MAP, sep="\t")
    sym = dict(zip(gm_all.GENE.astype(int), gm_all.annotation_symbol))  # frozen JSON stores one symbol as "nan"
    gm = gm_all[gm_all.mapping_status == "unique"]
    e2g = dict(zip(gm.GENE.astype(int), gm.ensembl_gene_id))
    frozen = C.load_frozen()["loci"]
    rows = []
    for l in frozen:
        for g in l["bonferroni_genes"]:
            symbol = g["symbol"] if str(g["symbol"]) not in ("nan", "None", "") else sym.get(int(g["entrez"]))
            rows.append({"locus_id": l["locus_id"], "gene": symbol, "entrez": int(g["entrez"]),
                         "ensembl": e2g.get(int(g["entrez"])), "membership": "BONFERRONI",
                         "locus_top_magma_gene": l["top_gene"], "chr": l["chr"], "lead_snp": l["lead_snp"]})
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    lead = {l["locus_id"]: l for l in frozen}
    for r in q.itertuples():
        rows.append({"locus_id": r.locus_id, "gene": r.gene, "entrez": int(r.entrez) if pd.notna(r.entrez) else None,
                     "ensembl": r.ensembl_gene_id, "membership": "QUERY_WINDOW",
                     "locus_top_magma_gene": lead[r.locus_id]["top_gene"], "chr": lead[r.locus_id]["chr"],
                     "lead_snp": lead[r.locus_id]["lead_snp"]})
    mem = pd.DataFrame(rows)
    mem = (mem.groupby(["locus_id", "gene"], as_index=False)
              .agg(entrez=("entrez", "first"), ensembl=("ensembl", "first"),
                   membership=("membership", lambda s: ";".join(sorted(set(s)))),
                   locus_top_magma_gene=("locus_top_magma_gene", "first"), chr=("chr", "first"),
                   lead_snp=("lead_snp", "first")))
    df = mem.merge(gw.rename(columns={"ENSGID": "ensembl", "PoPS_Score": "pops_score", "Y": "magma_z_used",
                                      "NAME": "pops_annot_symbol"})[
        ["ensembl", "pops_score", "magma_z_used", "pops_annot_symbol", "pops_genomewide_percentile",
         "pops_genomewide_rank"]], on="ensembl", how="left")
    df["rank_in_locus"] = df.groupby("locus_id").pops_score.rank(ascending=False, method="min")
    df["n_scored_genes_in_locus"] = df.groupby("locus_id").pops_score.transform("count")
    df["top_in_locus"] = df.rank_in_locus == 1
    # context: Sprint-5 anchor labels and classes (NOT used to compute anything above)
    rank = pd.read_csv(REPO / "reports" / "sprint5" / "locus_confidence_rank.csv")
    anch = {}
    for r in rank.itertuples():
        for lid, g in zip(str(r.labels).split(";"), str(r.top_gene_labels).split(";")):
            anch[lid] = (g, r.locus_stratum, r.rank)
    df["sprint5_anchor_label"] = df.locus_id.map(lambda x: anch.get(x, (None,))[0])
    df["sprint5_locus_stratum"] = df.locus_id.map(lambda x: anch.get(x, (None, None))[1])
    ev = pd.read_csv(REPO / "reports" / "sprint5" / "causal_gene_evidence_matrix.csv")
    ev = ev[["gene", "locus_id", "gene_class", "classes", "n_classes"]].rename(
        columns={"gene_class": "sprint5_gene_class", "classes": "sprint5_evidence_classes",
                 "n_classes": "sprint5_n_classes"})
    df = df.merge(ev, on=["gene", "locus_id"], how="left")
    df["evidence_role"] = "ORTHOGONAL_GENOME_WIDE_PRIORITISATION_NOT_V2G_NOT_CAUSAL"
    df = df.sort_values(["locus_id", "rank_in_locus", "gene"]).reset_index(drop=True)
    cols = ["gene", "ensembl", "pops_score", "locus_id", "rank_in_locus", "top_in_locus", "n_scored_genes_in_locus",
            "membership", "entrez", "chr", "lead_snp", "locus_top_magma_gene", "sprint5_anchor_label",
            "sprint5_locus_stratum", "sprint5_gene_class", "sprint5_evidence_classes", "sprint5_n_classes",
            "magma_z_used", "pops_genomewide_percentile", "pops_genomewide_rank", "pops_annot_symbol", "evidence_role"]
    OUT.mkdir(parents=True, exist_ok=True)
    df["unscored_reason"] = np.where(df.pops_score.notna(), None,
                                     np.where(df.ensembl.isna(), "NO_UNIQUE_ENTREZ_TO_ENSEMBL_MAPPING",
                                              "NOT_IN_POPS_GENE_ANNOTATION_OR_MAGMA_REKEY"))
    cols.append("unscored_reason")
    df[cols].to_csv(OUT / "pops_scores.csv", index=False)
    print(json.dumps({"rows": len(df), "loci": int(df.locus_id.nunique()), "scored_rows": int(df.pops_score.notna().sum()),
                      "genes_unscored": sorted(df[df.pops_score.isna()].gene.unique().tolist())[:50]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
