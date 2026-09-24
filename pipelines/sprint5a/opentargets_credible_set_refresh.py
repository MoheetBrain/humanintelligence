#!/usr/bin/env python3
"""Sprint 5A section 5 — Open Targets 26.06 per-credible-set refresh (re-verified live, not cached Sprint-3/4).

For every cognition-study GWAS credible set that contains a Sprint-5 query variant (979 studyLocusIds from
data/sprint5/ot_variant_credible_sets.parquet; Sprint-3 study tiers), fetch: all credible-set variants + PIPs,
top-5 L2G genes with every feature value/SHAP, and ALL molecular colocalisations (eQTL, sQTL, tuQTL, pQTL,
sc-eQTL, sc-sQTL, trans flag) with H4/CLPP, QTL gene, biosample, beta-ratio sign. Raw responses cached under
data/interim/sprint5a/ot_cs/ (gitignored). L2G calls are labelled DISTANCE/GENE_DENSITY-driven vs biological.

Output: reports/sprint5a/opentargets_2606_refresh.parquet (one row per credible set x L2G gene, with nested
JSON of variants and colocs), reports/sprint5a/opentargets_2606_colocs.parquet (one row per coloc),
data/sprint5a/opentargets_2606_provenance.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "pipelines/sprint5"))
import common as C  # noqa: E402  (Sprint-5 helpers: http_json, utc_now)
from build_opentargets_refresh import feature_class  # noqa: E402

API = "https://api.platform.opentargets.org/api/v4/graphql"
CACHE = R / "data/interim/sprint5a/ot_cs"
CACHE.mkdir(parents=True, exist_ok=True)
Q = """query Q($id: String!, $ci: Int!) { credibleSet(studyLocusId: $id) {
  studyLocusId studyId finemappingMethod confidence credibleSetlog10BF purityMinR2
  study { id traitFromSource nSamples pubmedId cohorts }
  locus(page: {index: 0, size: 500}) { count rows { variant { id rsIds } posteriorProbability is95CredibleSet beta } }
  l2GPredictions(page: {index: 0, size: 5}) { rows { score shapBaseValue target { id approvedSymbol }
      features { name value shapValue } } }
  colocalisation(studyTypes: [eqtl, sqtl, pqtl, sceqtl, scsqtl, tuqtl, sctuqtl, scpqtl], page: {index: $ci, size: 250}) { count rows { colocalisationMethod h3 h4 clpp betaRatioSignAverage
      numberColocalisingVariants rightStudyType
      otherStudyLocus { studyLocusId studyType isTransQtl qtlGeneId
        study { id projectId studyType biosample { biosampleName } target { id approvedSymbol } } } } }
} }"""


def fetch(slid: str) -> dict:
    fn = CACHE / f"{slid}.json"
    if fn.exists():
        return json.loads(fn.read_text())
    res = C.http_json(API, {"query": Q, "variables": {"id": slid, "ci": 0}}, timeout=240)
    cs = (res.get("data") or {}).get("credibleSet") or {}
    col = cs.get("colocalisation") or {}
    n, rows, page = col.get("count") or 0, list(col.get("rows") or []), 1
    while len(rows) < n and page < 40:
        r2 = C.http_json(API, {"query": Q, "variables": {"id": slid, "ci": page}}, timeout=240)
        more = (((r2.get("data") or {}).get("credibleSet") or {}).get("colocalisation") or {}).get("rows") or []
        if not more:
            break
        rows += more
        page += 1
    if cs:
        cs["colocalisation"] = {"count": n, "rows": rows}
    fn.write_text(json.dumps(res))
    return res


def main() -> int:
    meta = C.http_json(API, {"query": "{ meta { apiVersion { x y z } dataVersion { year month } dataPrefix } }"})["data"]["meta"]
    cs = pd.read_parquet(R / "data/sprint5/ot_variant_credible_sets.parquet")
    sc = pd.read_csv(R / "data/gene_tournament/study_classification.csv").set_index("accession_id")
    cs["tier"] = cs.study_id.map(sc.tier)
    qv = pd.read_csv(R / "data/sprint5/query_variants_cognition.csv")
    locus_of = qv.groupby("rsid").locus_id.apply(lambda s: ";".join(sorted(set(s)))).to_dict()
    cog = cs[(cs.study_type == "gwas") & cs.tier.notna()]
    slids = sorted(set(cog.studyLocusId))
    loc_of_set = cog.assign(locus=cog.rsid.map(locus_of)).groupby("studyLocusId").locus.apply(
        lambda s: ";".join(sorted({x for v in s.dropna() for x in v.split(";")}))).to_dict()
    print(meta, len(slids), "credible sets", flush=True)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(fetch, slids))
    rows, colocs = [], []
    for slid, r in zip(slids, res):
        c = (r.get("data") or {}).get("credibleSet")
        if not c:
            continue
        st = c.get("study") or {}
        variants = [{"variant": (x["variant"] or {}).get("id"), "rsids": (x["variant"] or {}).get("rsIds"),
                     "pip": x.get("posteriorProbability")} for x in (c.get("locus") or {}).get("rows") or []]
        top = max(variants, key=lambda v: v["pip"] or 0, default={})
        for co in (c.get("colocalisation") or {}).get("rows") or []:
            o = co.get("otherStudyLocus") or {}
            ost = o.get("study") or {}
            colocs.append({"studyLocusId": slid, "locus_ids": loc_of_set.get(slid), "gwas_study": st.get("id"),
                           "trait": st.get("traitFromSource"), "method": co.get("colocalisationMethod"),
                           "h4": co.get("h4"), "clpp": co.get("clpp"), "beta_ratio_sign": co.get("betaRatioSignAverage"),
                           "n_coloc_variants": co.get("numberColocalisingVariants"), "qtl_type": o.get("studyType"),
                           "is_trans": o.get("isTransQtl"), "qtl_project": ost.get("projectId"), "qtl_study": ost.get("id"),
                           "biosample": (ost.get("biosample") or {}).get("biosampleName"),
                           "qtl_gene": (ost.get("target") or {}).get("approvedSymbol"), "qtl_gene_id": o.get("qtlGeneId")})
        for rank, p in enumerate((c.get("l2GPredictions") or {}).get("rows") or [], 1):
            feats = {f["name"]: (f.get("value"), f.get("shapValue")) for f in p.get("features") or []}
            by = {}
            for k, (v, sh) in feats.items():
                by[feature_class(k)] = by.get(feature_class(k), 0.0) + (sh or 0.0)
            pos = by.get("POSITIONAL", 0.0)
            bio = sum(v for k, v in by.items() if k in ("CODING", "QTL", "ENHANCER") and v > 0)
            rows.append({"studyLocusId": slid, "locus_ids": loc_of_set.get(slid), "study_id": st.get("id"),
                         "trait": st.get("traitFromSource"), "n_samples": st.get("nSamples"),
                         "cohorts": ";".join(st.get("cohorts") or []), "method": c.get("finemappingMethod"),
                         "confidence": c.get("confidence"), "log10BF": c.get("credibleSetlog10BF"),
                         "n_variants": len(variants), "lead_variant": top.get("variant"), "lead_pip": top.get("pip"),
                         "variants_json": json.dumps(variants), "l2g_rank": rank,
                         "gene": (p.get("target") or {}).get("approvedSymbol"), "l2g_score": p.get("score"),
                         **{f"shap_{k.lower()}": round(v, 4) for k, v in by.items()},
                         "driver": ("DISTANCE_GENE_DENSITY" if pos > bio else "BIOLOGICAL") if (pos or bio) else "NONE",
                         "features_json": json.dumps(feats)})
    out = pd.DataFrame(rows)
    out.to_parquet(C.OUT.parent / "sprint5a" / "opentargets_2606_refresh.parquet", index=False)
    cdf = pd.DataFrame(colocs)
    cdf.to_parquet(C.OUT.parent / "sprint5a" / "opentargets_2606_colocs.parquet", index=False)
    h = hashlib.sha256()
    for s in slids:
        f = CACHE / f"{s}.json"
        if f.exists():
            h.update(f.read_bytes())
    prov = {"retrieved_utc": C.utc_now(), "endpoint": API, "release_meta": meta, "n_credible_sets": len(slids),
            "n_l2g_rows": int(len(out)), "n_coloc_rows": int(len(cdf)), "raw_cache": str(CACHE.relative_to(R)),
            "raw_cache_sha256_concat": h.hexdigest(), "query": Q}
    (R / "data/sprint5a/opentargets_2606_provenance.json").write_text(json.dumps(prov, indent=2, default=str))
    r1 = out[out.l2g_rank == 1]
    print("rank-1 L2G driver:", r1.driver.value_counts().to_dict())
    print("colocs:", cdf.qtl_type.value_counts().to_dict() if len(cdf) else {})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
