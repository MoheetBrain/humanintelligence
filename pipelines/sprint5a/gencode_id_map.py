#!/usr/bin/env python3
"""Sprint 5A — explicit GENCODE gene-ID map (v26 / v29lift37 / v39 / v40 / v47) for every candidate gene used
across sources: Sprint-4 Gate-C query genes (Ensembl IDs), the Sprint-5A candidate list, genes carrying brainSCOPE
QTL evidence (symbols only) and GTEx V11 hits (v47 IDs) at the Gate-C loci.

Source releases: GTEx v8 = GENCODE v26; devBrain (Wen 2024) = v29lift37 (STAR; Salmon index v33lift37 per GitHub);
GTEx v10 + eQTL Catalogue r7 = v39; v40 = requested comparison release; GTEx V11 = v47.
brainSCOPE publishes gene SYMBOLS only (annotation release not stated) -> symbol matching, flagged.

Input: data/interim/sprint5a/gencode/genes_<rel>.tsv (gencode_fetch.py). Output: data/sprint5a/gencode_id_map.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "data/interim/sprint5a/gencode"
RELS = ["v26", "v29lift37", "v39", "v40", "v47"]
CANDIDATES = "NT5DC2 DNPH1 RHEBL1 CLCN2 DCC EXT1 MEF2C KDM5B EXOC4 AKAP6 NPAS3 TUFM SH2B1 EIF3C KIFC2 SLC39A8".split()


def main() -> None:
    ann = {}
    for r in RELS:
        d = pd.read_csv(G / f"genes_{r}.tsv", sep="\t", dtype=str)
        d["ensg"] = d.gene_id.str.split(".").str[0]
        d = d[~d.gene_id.str.endswith("_PAR_Y")]
        ann[r] = d
    keys: dict[str, set] = {}

    def add(ensg, src):
        keys.setdefault(ensg, set()).add(src)

    q = pd.read_csv(ROOT / "data/sprint4/gate_c_query_genes.csv")
    for e in q.ensembl_gene_id.dropna():
        add(e, "sprint4_gate_c_query_genes")
    sym_sources = {}
    for s in CANDIDATES:
        sym_sources.setdefault(s, set()).add("sprint5a_candidate_list")
    bs = ROOT / "reports/sprint5a/brainscope_gene_summary.csv"
    if bs.exists():
        b = pd.read_csv(bs)
        b = b[b.gate_c_locus & b.best_evidence_type.isin(["DIRECT_VARIANT_GENE_OVERLAP", "CELL_SPECIFIC_QTL_SUPPORT"])]
        for s in b.gene.dropna().unique():
            sym_sources.setdefault(s, set()).add("brainscope_symbol_qtl_evidence")
    v11 = ROOT / "reports/sprint5a/gtex_v11_lookup.csv"
    if v11.exists():
        l = pd.read_csv(v11, usecols=["gate_c_locus", "gene_id_v47"])
        for e in l[l.gate_c_locus].gene_id_v47.dropna().unique():
            add(e.split(".")[0], "gtex_v11_lookup")
    # symbols -> ENSG via v47 first, then older releases
    unresolved = []
    for s, src in sym_sources.items():
        hit = None
        for r in ["v47", "v40", "v39", "v26", "v29lift37"]:
            m = ann[r][ann[r].gene_name == s]
            if len(m):
                hit = sorted(m.ensg.unique())
                break
        if hit is None:
            unresolved.append((s, ";".join(sorted(src))))
            continue
        for e in hit:
            for x in src:
                add(e, f"{x}:{s}")
    rows = []
    for e, src in sorted(keys.items()):
        row = {"ensembl_gene_id": e, "sources": ";".join(sorted(src))}
        names = []
        for r in RELS:
            m = ann[r][ann[r].ensg == e]
            row[f"{r}_gene_id"] = ";".join(m.gene_id) if len(m) else None
            row[f"{r}_symbol"] = ";".join(m.gene_name.unique()) if len(m) else None
            if r == "v47":
                row["v47_gene_type"] = ";".join(m.gene_type.unique()) if len(m) else None
                row["v47_chr"] = m.chr.iloc[0] if len(m) else None
            if len(m):
                names += list(m.gene_name.unique())
        row["present_in"] = ";".join(r for r in RELS if row[f"{r}_gene_id"])
        row["absent_from"] = ";".join(r for r in RELS if not row[f"{r}_gene_id"]) or None
        row["symbol_changed_across_releases"] = len(set(names)) > 1
        row["version_changed_across_releases"] = len({row[f"{r}_gene_id"] for r in RELS if row[f"{r}_gene_id"]}) > 1
        cur = row.get("v47_symbol") or next((row[f"{r}_symbol"] for r in reversed(RELS) if row[f"{r}_symbol"]), None)
        row["symbol_current"] = cur
        # symbol collisions: does this symbol map to >1 ENSG in v47?
        if cur:
            row["v47_symbol_maps_to_n_ensg"] = int(ann["v47"][ann["v47"].gene_name == cur].ensg.nunique())
        rows.append(row)
    out = pd.DataFrame(rows)
    for s, src in unresolved:
        out = pd.concat([out, pd.DataFrame([{"ensembl_gene_id": None, "sources": src, "symbol_current": s,
                                             "present_in": None, "absent_from": ";".join(RELS)}])], ignore_index=True)
    # brainSCOPE symbol presence (pseudobulk matrices, Sprint-5 reduced gene lists)
    pb = ROOT / "data/interim/sprint5/brainscope/pseudobulk_genes"
    bsyms = set()
    for f in pb.glob("*.genes.tsv"):
        bsyms |= set(pd.read_csv(f, sep="\t").iloc[:, 3].astype(str))
    out["brainscope_symbol_present"] = out.symbol_current.isin(bsyms)
    out["brainscope_symbol_matched_alias"] = [next((n for r in RELS for n in str(rw.get(f"{r}_symbol") or "").split(";")
                                                    if n in bsyms), None) for rw in out.to_dict("records")]
    out["is_sprint5a_candidate"] = out.symbol_current.isin(CANDIDATES)
    cols = ["symbol_current", "ensembl_gene_id", "is_sprint5a_candidate", "sources", "v26_gene_id", "v26_symbol",
            "v29lift37_gene_id", "v29lift37_symbol", "v39_gene_id", "v39_symbol", "v40_gene_id", "v40_symbol",
            "v47_gene_id", "v47_symbol", "v47_gene_type", "v47_chr", "present_in", "absent_from",
            "symbol_changed_across_releases", "version_changed_across_releases", "v47_symbol_maps_to_n_ensg",
            "brainscope_symbol_present", "brainscope_symbol_matched_alias"]
    out = out.reindex(columns=cols).sort_values(["is_sprint5a_candidate", "symbol_current"], ascending=[False, True])
    (ROOT / "data/sprint5a").mkdir(parents=True, exist_ok=True)
    out.to_csv(ROOT / "data/sprint5a/gencode_id_map.csv", index=False)
    print(len(out), "genes;", int(out.symbol_changed_across_releases.fillna(False).sum()), "symbol changes;",
          out.absent_from.notna().sum(), "absent from >=1 release")
    print(out[out.is_sprint5a_candidate][["symbol_current", "v26_gene_id", "v39_gene_id", "v47_gene_id",
                                          "brainscope_symbol_present"]].to_string())
    print(out[out.symbol_changed_across_releases.fillna(False).astype(bool)][
        ["symbol_current", "v26_symbol", "v39_symbol", "v47_symbol"]].to_string())


if __name__ == "__main__":
    main()
