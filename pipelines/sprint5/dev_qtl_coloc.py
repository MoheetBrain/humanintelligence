#!/usr/bin/env python3
"""Sprint 5 — developmental / non-adult brain eQTL colocalisation on the 36 Sprint-4 Gate-C loci.

Keeps DEVELOPMENTAL evidence separate from ADULT evidence (protocol: questions A/B vs C never merged).
Datasets (eQTL Catalogue r7, gene-level `ge`, the ones Sprint 4 excluded as NON_ADULT):
  * Walker_2019 neocortex — fetal (DEVELOPMENTAL_FETAL)
  * Aygun_2021 neural progenitor / neuron — fetal-derived in vitro (DEVELOPMENTAL_IN_VITRO)
  * BrainSeq DLPFC — prenatal-to-85 y mixed (MIXED_AGE_SENSITIVITY, never counted as developmental-only)
Fetching reuses pipelines/sprint4/fetch_eqtl_catalogue.fetch_sumstats_dataset (tabix byte-range reads,
ALT = effect allele); colocalisation reuses the Sprint-4 coloc.abf code path unchanged (same priors,
harmonisation, palindromic rule, strong = PP.H4 >= 0.8).

Output: reports/sprint5/developmental_qtl_coloc.csv, data/sprint5/developmental_qtl_provenance.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402  (Sprint-5 common)

# Load the Sprint-4 modules with THEIR own `common` (both sprints name it common.py).
_s5_common = sys.modules.pop("common")
sys.path.insert(0, str(C.REPO_ROOT / "pipelines" / "sprint4"))
import fetch_eqtl_catalogue as FE  # noqa: E402
import gate_c_coloc as GC  # noqa: E402
sys.modules["common_sprint4"] = sys.modules.pop("common")
sys.modules["common"] = _s5_common
sys.path.pop(0)

DEV = {"Walker_2019": "DEVELOPMENTAL_FETAL", "Aygun_2021": "DEVELOPMENTAL_IN_VITRO",
       "BrainSeq": "MIXED_AGE_SENSITIVITY"}
EQTL_DIR = C.WORK / "eqtl_dev"


def loci() -> list:
    prov = json.loads((C.REPO_ROOT / "data/raw/sprint4/eqtl_catalogue/PROVENANCE.json").read_text())
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    genes = q.groupby("locus_id").apply(lambda g: dict(zip(g.ensembl_gene_id, g.gene))).to_dict()
    out = []
    for it in prov["loci"]["items"]:
        if it["locus_id"] not in genes or not it.get("lead_pos_grch38"):
            continue
        loc = FE.Locus(it["locus_id"], str(it["chr"]), it["lead_snp"], int(it["lead_pos_grch37"]),
                       genes[it["locus_id"]], lead_pos_grch38=int(it["lead_pos_grch38"]))
        FE.set_window(loc, prov["loci"]["window_kb_each_side"])
        out.append(loc)
    return out


def fetch(meta: pd.DataFrame, lc: list) -> list[dict]:
    lim = FE.RateLimiter(2.0)
    recs = []
    for _, ds in meta.iterrows():
        recs += FE.fetch_sumstats_dataset(ds, lc, EQTL_DIR, EQTL_DIR / ".tbi_cache", lim, False)
    return recs


def coloc(meta: pd.DataFrame) -> pd.DataFrame:
    frozen = C.load_rules  # noqa: F841 - rules file must be intact before labelling
    pri = {"p1": 1e-4, "p2": 1e-4, "p12": 5e-6}  # Sprint-4 frozen coloc priors, unchanged
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    davies = pd.read_csv(GC.C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele", "Zscore"])
    davies = davies.drop_duplicates("Markername", keep=False)
    work = C.WORK / "coloc_dev"
    work.mkdir(parents=True, exist_ok=True)
    (work / "coloc.R").write_text(GC.R_COLOC)
    results = []
    for locus_id, lq in q.groupby("locus_id"):
        genes = set(lq.ensembl_gene_id)
        frames = []
        for ds in meta.dataset_id:
            f = EQTL_DIR / f"{locus_id}__{ds}.parquet"
            if not f.exists():
                continue
            e = pd.read_parquet(f)
            e = e[e.gene_id.str.split(".").str[0].isin(genes)]
            if e.empty:
                continue
            if not e.rsid.isin(davies.Markername).any():
                continue
            h = GC.harmonise(e, davies)
            if h.empty:
                continue
            h["n2"] = (h.an.max() / 2) if "an" in h and h.an.notna().any() else np.nan
            h["maf1"] = h.maf
            b1, v1 = GC.gwas_beta(h.Zscore.to_numpy(float), h.maf.clip(1e-4, 0.5).to_numpy(float), GC.C.DAVIES_N)
            h["beta1"], h["varbeta1"], h["n1"], h["maf2"] = b1, v1, GC.C.DAVIES_N, h.maf
            h["pair_id"] = locus_id + "|" + ds + "|" + h.molecular_trait_id.astype(str)
            frames.append(h[["pair_id", "rsid", "beta1", "varbeta1", "maf1", "n1", "beta2", "varbeta2", "maf2", "n2",
                             "Zscore", "Effect_allele", "Other_allele", "gene_id"]].rename(columns={"rsid": "snp"}))
        if not frames:
            continue
        long = pd.concat(frames, ignore_index=True).drop_duplicates(["pair_id", "snp"])
        inp, outp = work / f"{locus_id}.in.tsv", work / f"{locus_id}.out.tsv"
        long.to_csv(inp, sep="\t", index=False)
        subprocess.run([str(C.RSCRIPT), str(work / "coloc.R"), str(inp), str(outp), str(pri["p1"]), str(pri["p2"]),
                        str(pri["p12"])], capture_output=True, text=True, timeout=7200, check=False)
        if not outp.exists() or outp.stat().st_size == 0:
            continue
        r = pd.read_csv(outp, sep="\t")
        top = long.set_index(["pair_id", "snp"])
        gene_of = long.drop_duplicates("pair_id").set_index("pair_id").gene_id
        for row in r.to_dict("records"):
            key = (row["pair_id"], row["top_snp"])
            qtl_cog = np.nan
            if key in top.index:
                t = top.loc[key]
                if isinstance(t, pd.DataFrame):
                    t = t.iloc[0]
                qtl_cog = float(t.beta2) * (1 if float(t.Zscore) > 0 else -1)
            _, ds, trait = row["pair_id"].split("|", 2)
            results.append({"locus_id": locus_id, "dataset_id": ds, "molecular_trait_id": trait,
                            "gene_id": str(gene_of[row["pair_id"]]).split(".")[0],
                            "method": "coloc.abf (single-signal)", "nsnps": row["nsnps"],
                            **{k: row[k] for k in ("PP.H0", "PP.H1", "PP.H2", "PP.H3", "PP.H4")},
                            "top_snp": row["top_snp"], "qtl_effect_of_cognition_allele_at_top": qtl_cog})
    return pd.DataFrame(results)


def main() -> int:
    C.load_rules()
    meta = pd.read_csv(C.S4_DATA / "eqtl_catalogue_brain_datasets.csv")
    meta = meta[meta.study_label.isin(DEV) & (meta.quant_method == "ge")].copy()
    meta["stage_class"] = meta.study_label.map(DEV)
    lc = loci()
    print(f"{len(meta)} datasets x {len(lc)} loci", flush=True)
    recs = fetch(meta, lc)
    res = coloc(meta)
    q = pd.read_csv(C.S4_DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    if len(res):
        res["gene"] = res.gene_id.map(sym)
        m = meta.set_index("dataset_id")
        for col in ("study_label", "tissue_label", "sample_group", "sample_size", "stage_class"):
            res[col] = res.dataset_id.map(m[col])
        res["strong"] = res["PP.H4"] >= 0.8
        res["direction"] = np.where(res.qtl_effect_of_cognition_allele_at_top > 0, "cognition allele -> HIGHER",
                                    np.where(res.qtl_effect_of_cognition_allele_at_top < 0, "cognition allele -> LOWER", "NA"))
    res.to_csv(C.OUT / "developmental_qtl_coloc.csv", index=False, float_format="%.4g")
    prov = {"created_utc": C.utc_now(), "script": "pipelines/sprint5/dev_qtl_coloc.py", "eqtl_catalogue_release": "r7",
            "datasets": meta[["dataset_id", "study_label", "tissue_label", "sample_group", "sample_size",
                              "stage_class", "adult_status_basis", "sumstats_url"]].to_dict("records"),
            "n_loci": len(lc), "fetch_records": recs, "n_coloc_rows": int(len(res)),
            "n_strong": int(res["strong"].sum()) if len(res) else 0,
            "priors": {"p1": 1e-4, "p2": 1e-4, "p12": 5e-6}}
    (C.DATA / "developmental_qtl_provenance.json").write_text(json.dumps(prov, indent=2, default=str))
    if len(res):
        print(res[res.strong][["locus_id", "gene", "study_label", "sample_group", "PP.H4", "direction"]].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
