#!/usr/bin/env python3
"""Sprint 5A, Goal B — prepare PoPS inputs (run by pipelines/sprint5a/run_pops.sh; hi-pops env).

Two steps:
  magma    Re-key our Davies 2018 MAGMA v1.10 gene analysis (10 kb window, 1000G EUR; Entrez ids) to the
           Ensembl ids PoPS uses. Only genes with a UNIQUE Entrez->Ensembl mapping (data/raw/magma_x01/
           2026-09-22/gene_id_map.tsv) whose Ensembl id is in PoPS' gene_annot_jun10.txt are kept; Ensembl ids
           hit by >1 Entrez gene are dropped. The .genes.raw gene-gene correlation lists are rebuilt for the
           retained subset (each MAGMA line stores correlations with the immediately preceding genes; after
           subsetting, each retained gene lists its correlations back to its earliest retained correlated
           predecessor), so PoPS' block-diagonal MAGMA error covariance is the exact sub-matrix of MAGMA's.
  features Stream-munge the published PoPS feature matrix (PoPS.features.txt.gz, 7.55 GB) into the chunked
           NumPy format of munge_feature_directory.py (float64, rows in gene_annot order, 5000 cols/chunk,
           nan_policy=raise) without decompressing it to disk.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MAGMA_OUT = REPO / "data" / "raw" / "magma_x01" / "2026-09-22" / "davies2018_10kb.genes.out"
MAGMA_RAW = REPO / "data" / "interim" / "magma_replication" / "davies2018_10kb.genes.raw"
GENE_MAP = REPO / "data" / "raw" / "magma_x01" / "2026-09-22" / "gene_id_map.tsv"
POPS = REPO / "data" / "interim" / "sprint5a" / "tools" / "pops"
ANNOT = POPS / "example" / "data" / "utils" / "gene_annot_jun10.txt"
WORK = REPO / "data" / "interim" / "sprint5a" / "pops"


def magma(out_prefix: Path) -> dict:
    annot = pd.read_csv(ANNOT, sep="\t")
    gm = pd.read_csv(GENE_MAP, sep="\t")
    gm = gm[gm.mapping_status == "unique"]
    e2g = dict(zip(gm.GENE.astype(str), gm.ensembl_gene_id))
    lines = MAGMA_RAW.read_text().splitlines()
    header, body = lines[:2], [ln.split(" ") for ln in lines[2:]]
    ids = [b[0] for b in body]
    ens = [e2g.get(g) for g in ids]
    in_annot = set(annot.ENSGID)
    cnt = pd.Series([e for e in ens if e in in_annot]).value_counts()
    dup = set(cnt[cnt > 1].index)
    keep = [e is not None and e in in_annot and e not in dup for e in ens]
    out_lines = list(header)
    # per chromosome, rebuild correlation lists over retained genes
    chrom = [b[1] for b in body]
    i = 0
    n_kept = 0
    while i < len(body):
        j = i
        while j < len(body) and chrom[j] == chrom[i]:
            j += 1
        blk = list(range(i, j))
        n = len(blk)
        sig = np.zeros((n, n))
        for a, gi in enumerate(blk):
            c = [float(x) for x in body[gi][9:]]
            if c:
                sig[a, a - len(c):a] = c
        kept = [a for a in range(n) if keep[blk[a]]]
        for pos, a in enumerate(kept):
            b = body[blk[a]]
            prev = kept[:pos]
            corr = [sig[a, p] for p in prev]
            nz = [k for k, v in enumerate(corr) if v != 0.0]
            corr = corr[nz[0]:] if nz else []
            out_lines.append(" ".join([ens[blk[a]]] + b[1:9] + [repr(float(v)) if v != 0 else "0" for v in corr]))
            n_kept += 1
        i = j
    Path(str(out_prefix) + ".genes.raw").write_text("\n".join(out_lines) + "\n")
    go = pd.read_csv(MAGMA_OUT, sep=r"\s+", dtype={"GENE": str})
    go["ENSG"] = go.GENE.map(e2g)
    go = go.set_index("GENE").loc[[g for g, k in zip(ids, keep) if k]].reset_index()
    go["GENE"] = go.ENSG
    go.drop(columns="ENSG").to_csv(str(out_prefix) + ".genes.out", sep=" ", index=False)
    rep = {"magma_genes": len(ids), "unique_entrez_to_ensembl": sum(e is not None for e in ens),
           "in_pops_gene_annot": sum(e in in_annot for e in ens if e), "dropped_duplicate_ensembl": len(dup),
           "kept": n_kept, "pops_gene_annot_genes": len(annot)}
    print(json.dumps(rep))
    return rep


def features(src: Path, save_prefix: Path, max_cols: int = 5000) -> dict:
    annot = pd.read_csv(ANNOT, sep="\t")
    order = {g: k for k, g in enumerate(annot.ENSGID)}
    with gzip.open(src, "rt") as fh:
        cols = fh.readline().rstrip("\n").split("\t")[1:]
        mat = np.full((len(annot), len(cols)), np.nan, dtype=np.float64)
        seen = 0
        extra = 0
        for ln in fh:
            k = ln.find("\t")
            g = ln[:k]
            r = order.get(g)
            if r is None:
                extra += 1
                continue
            vals = ln[k + 1:].rstrip("\n").replace("True", "1").replace("False", "0").split("\t")
            mat[r] = np.array(vals, dtype=np.float64)  # bool columns -> 1/0, as pandas .astype(float64) does
            seen += 1
    if np.isnan(mat).any():
        raise SystemExit(f"Missing genes/values in feature matrix (nan_policy=raise): rows seen {seen}/{len(annot)}")
    np.savetxt(str(save_prefix) + ".rows.txt", annot.ENSGID.values, fmt="%s")
    nchunk = 0
    for s in range(0, len(cols), max_cols):
        np.save(str(save_prefix) + f".mat.{nchunk}.npy", mat[:, s:s + max_cols])
        np.savetxt(str(save_prefix) + f".cols.{nchunk}.txt", np.array(cols[s:s + max_cols]), fmt="%s")
        nchunk += 1
    rep = {"n_features": len(cols), "n_genes": seen, "rows_not_in_annot_skipped": extra, "n_chunks": nchunk}
    print(json.dumps(rep))
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["magma", "features"])
    ap.add_argument("--features_gz", default=str(WORK / "PoPS.features.txt.gz"))
    a = ap.parse_args(argv)
    WORK.mkdir(parents=True, exist_ok=True)
    if a.step == "magma":
        rep = magma(WORK / "davies2018_10kb_ensg")
    else:
        (WORK / "features_munged").mkdir(exist_ok=True)
        rep = features(Path(a.features_gz), WORK / "features_munged" / "pops_features")
    (WORK / f"prep_{a.step}.json").write_text(json.dumps(rep, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
