#!/usr/bin/env python3
"""Sprint 5 — Open Targets current-release refresh at the variant level.

Release check first: the current Platform release is recorded (meta.dataVersion); if it equals the
Sprint-3 release (26.06), "refresh" means the fields Sprint 3 did not pull, not new data.

Per query variant (data/sprint5/query_variants_cognition.csv, GRCh38 ids built from the Ensembl allele
string; every alt allele tried) this fetches:
  * most severe consequence and transcript consequences (coding classes, LOFTEE, SIFT/PolyPhen);
  * variantEffect functional predictions;
  * enhancerToGenes (E2G intervals: target, biosample, score, datasource);
  * every credible set containing the variant (GWAS, eQTL, sQTL, pQTL, sc-eQTL, sc-sQTL, ...), with this
    variant's PIP inside the set, the QTL gene and biosample, and for GWAS sets the top-5 L2G genes with
    every feature's value and SHAP contribution.
Raw JSON responses are cached under data/interim/sprint5/opentargets/ (gitignored); sha256 of the
concatenated cache is recorded in data/sprint5/opentargets_provenance.json.

Output: data/sprint5/ot_variant_annotation.parquet, data/sprint5/ot_variant_credible_sets.parquet,
        data/sprint5/ot_l2g_features.parquet, data/sprint5/ot_e2g.parquet, data/sprint5/ot_variant_effect.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

API = "https://api.platform.opentargets.org/api/v4/graphql"
CACHE = C.WORK / "opentargets"
CACHE.mkdir(parents=True, exist_ok=True)

VARIANT_FIELDS = """
  id rsIds chromosome position referenceAllele alternateAllele
  mostSevereConsequence { id label }
  transcriptConsequences { target { id approvedSymbol } isEnsemblCanonical impact consequenceScore
      aminoAcidChange lofteePrediction siftPrediction polyphenPrediction distanceFromTss
      variantConsequences { id label } }
  variantEffect { method assessment assessmentFlag score normalisedScore target { id approvedSymbol } }
  enhancerToGenes(page: {index: 0, size: 500}) { count rows { target { id approvedSymbol } biosampleName
      biosample { biosampleId } datasourceId intervalType score resourceScore { name value } distanceToTss start end studyId } }
  credibleSets(page: {index: 0, size: 500}) { count rows {
      studyLocusId studyType finemappingMethod confidence qtlGeneId isTransQtl pValueMantissa pValueExponent
      beta zScore credibleSetlog10BF purityMinR2
      variant { id }
      study { id traitFromSource studyType projectId nSamples pubmedId cohorts
              biosample { biosampleId biosampleName } target { id approvedSymbol } }
      locus(variantIds: [$VID]) { rows { posteriorProbability is95CredibleSet is99CredibleSet beta variant { id } } }
  } }
"""


def meta() -> dict:
    q = "{ meta { name apiVersion { x y z } dataVersion { year month iteration } dataPrefix } }"
    return C.http_json(API, {"query": q})["data"]["meta"]


def variant_ids(row) -> list[str]:
    a = str(row.allele_string or "")
    if not a or "/" not in a or pd.isna(row.pos38):
        return []
    al = a.split("/")
    ref, alts = al[0], al[1:]
    ch = str(row.chr38).removesuffix(".0")
    return [f"{ch}_{int(row.pos38)}_{ref}_{alt}" for alt in alts if alt not in ("-",) and ref not in ("-",)]


def fetch_one(vid: str) -> dict:
    fn = CACHE / f"{vid}.json"
    if fn.exists():
        return json.loads(fn.read_text())
    q = ("query V($id: String!, $VID: String!) { variant(variantId: $id) {" +
         VARIANT_FIELDS.replace("[$VID]", "[$VID]") + "} }")
    q = q.replace("$VID: String!", "$VID: String!")
    res = C.http_json(API, {"query": q.replace("variantIds: [$VID]", "variantIds: [$VID]"),
                            "variables": {"id": vid, "VID": vid}}, timeout=180)
    if "errors" in res:
        res = {"error": res["errors"][:2], "data": res.get("data")}
    fn.write_text(json.dumps(res))
    return res


L2G_Q = """query L($id: String!) { credibleSet(studyLocusId: $id) { studyLocusId
  l2GPredictions(page: {index: 0, size: 5}) { rows { score shapBaseValue target { id approvedSymbol }
    features { name value shapValue } } } } }"""


def fetch_l2g(slid: str) -> dict:
    fn = CACHE / "l2g" / f"{slid}.json"
    fn.parent.mkdir(exist_ok=True)
    if fn.exists():
        return json.loads(fn.read_text())
    res = C.http_json(API, {"query": L2G_Q, "variables": {"id": slid}}, timeout=180)
    fn.write_text(json.dumps(res))
    return res


def cognition_study_ids() -> set[str]:
    sc = pd.read_csv(C.GT_DATA / "study_classification.csv")
    return set(sc.accession_id)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default=str(C.DATA / "query_variants_cognition.csv"))
    ap.add_argument("--prefix", default="ot")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    m = meta()
    print("Open Targets release:", m)
    qv = pd.read_csv(a.variants).drop_duplicates("rsid")
    ids = sorted({v for r in qv.itertuples() for v in variant_ids(r)})
    rs_of = {v: r.rsid for r in qv.itertuples() for v in variant_ids(r)}
    print(f"{len(ids)} candidate GRCh38 variant ids from {len(qv)} rsIDs", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(fetch_one, ids))
    ann, cs, l2g, e2g, ve = [], [], [], [], []
    for vid, r in zip(ids, res):
        v = (r.get("data") or {}).get("variant") if isinstance(r, dict) else None
        if not v:
            continue
        rsid = rs_of[vid]
        tcs = v.get("transcriptConsequences") or []
        coding = sorted({(t["target"] or {}).get("approvedSymbol") for t in tcs
                         if any(c["label"] in C_CODING for c in t.get("variantConsequences") or [])} - {None})
        ann.append({"rsid": rsid, "variant_id": vid, "most_severe": (v.get("mostSevereConsequence") or {}).get("label"),
                    "coding_genes": ";".join(coding),
                    "loftee_hc": ";".join(sorted({(t["target"] or {}).get("approvedSymbol") or "" for t in tcs
                                                  if t.get("lofteePrediction") == "HC"})),
                    "n_credible_sets": (v.get("credibleSets") or {}).get("count"),
                    "n_e2g": (v.get("enhancerToGenes") or {}).get("count")})
        for x in v.get("variantEffect") or []:
            ve.append({"rsid": rsid, "variant_id": vid, **{k: x.get(k) for k in
                       ("method", "assessment", "assessmentFlag", "score", "normalisedScore")},
                       "gene": (x.get("target") or {}).get("approvedSymbol")})
        for x in (v.get("enhancerToGenes") or {}).get("rows") or []:
            e2g.append({"rsid": rsid, "variant_id": vid, "gene": (x.get("target") or {}).get("approvedSymbol"),
                        "ensembl_id": (x.get("target") or {}).get("id"), "biosample": x.get("biosampleName"),
                        "biosample_id": (x.get("biosample") or {}).get("biosampleId"),
                        "datasource": x.get("datasourceId"), "interval_type": x.get("intervalType"),
                        "score": x.get("score"), "resource_score": json.dumps(x.get("resourceScore")),
                        "distance_to_tss": x.get("distanceToTss"), "study_id": x.get("studyId")})
        for c in (v.get("credibleSets") or {}).get("rows") or []:
            st = c.get("study") or {}
            lr = ((c.get("locus") or {}).get("rows") or [{}])
            pp = lr[0].get("posteriorProbability") if lr else None
            cs.append({"rsid": rsid, "variant_id": vid, "studyLocusId": c["studyLocusId"],
                       "study_type": c.get("studyType"), "study_id": st.get("id"),
                       "trait": st.get("traitFromSource"), "project": st.get("projectId"),
                       "n_samples": st.get("nSamples"), "pubmed": st.get("pubmedId"),
                       "cohorts": ";".join(st.get("cohorts") or []),
                       "biosample": (st.get("biosample") or {}).get("biosampleName"),
                       "qtl_gene": (st.get("target") or {}).get("approvedSymbol"),
                       "qtl_gene_id": c.get("qtlGeneId"), "is_trans": c.get("isTransQtl"),
                       "method": c.get("finemappingMethod"), "confidence": c.get("confidence"),
                       "lead_variant": (c.get("variant") or {}).get("id"),
                       "variant_pip": pp, "variant_beta_in_set": lr[0].get("beta") if lr else None,
                       "lead_beta": c.get("beta"), "lead_z": c.get("zScore"),
                       "log10BF": c.get("credibleSetlog10BF"), "purity_min_r2": c.get("purityMinR2"),
                       "p": (c.get("pValueMantissa") or 0) * 10 ** (c.get("pValueExponent") or 0)})
    csdf = pd.DataFrame(cs)
    cog = cognition_study_ids()
    slids = sorted(set(csdf.loc[(csdf.study_type == "gwas") & csdf.study_id.isin(cog), "studyLocusId"])) if len(csdf) else []
    print(f"L2G pass: {len(slids)} cognition-study credible sets", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        lres = list(ex.map(fetch_l2g, slids))
    st_of = csdf.drop_duplicates("studyLocusId").set_index("studyLocusId")[["study_id", "trait"]].to_dict("index") if slids else {}
    for slid, r in zip(slids, lres):
        cset = (r.get("data") or {}).get("credibleSet") or {}
        for rank, p in enumerate((cset.get("l2GPredictions") or {}).get("rows") or [], 1):
            feats = p.get("features") or []
            top = max(feats, key=lambda f: f.get("shapValue") or -9, default={})
            l2g.append({"studyLocusId": slid, "study_id": st_of[slid]["study_id"], "trait": st_of[slid]["trait"],
                        "rank": rank, "gene": (p.get("target") or {}).get("approvedSymbol"),
                        "ensembl_id": (p.get("target") or {}).get("id"), "score": p.get("score"),
                        "shap_base": p.get("shapBaseValue"), "top_shap_feature": top.get("name"),
                        "top_shap_value": top.get("shapValue"),
                        "features_json": json.dumps({f["name"]: [f.get("value"), f.get("shapValue")] for f in feats})})
    out = {"annotation": pd.DataFrame(ann), "credible_sets": csdf,
           "l2g_features": pd.DataFrame(l2g).drop_duplicates(["studyLocusId", "gene"]) if l2g else pd.DataFrame(),
           "e2g": pd.DataFrame(e2g), "variant_effect": pd.DataFrame(ve)}
    for k, df in out.items():
        df.to_parquet(C.DATA / f"{a.prefix}_{'variant_' if k in ('annotation', 'credible_sets', 'effect') else ''}{k}.parquet", index=False)
        print(k, df.shape)
    h = hashlib.sha256()
    for vid in ids:
        fn = CACHE / f"{vid}.json"
        if fn.exists():
            h.update(fn.read_bytes())
    prov_fn = C.DATA / "opentargets_provenance.json"
    prov = json.loads(prov_fn.read_text()) if prov_fn.exists() else {}
    prov[a.prefix] = {"retrieved_utc": C.utc_now(), "endpoint": API, "release_meta": m,
                      "sprint3_release": "26.06 (API 26.6.3, retrieved 2026-09-22)",
                      "same_release_as_sprint3": m["dataVersion"]["year"] == "26" and m["dataVersion"]["month"] == "06",
                      "variants_input": a.variants, "n_rsid": int(len(qv)), "n_variant_ids_tried": len(ids),
                      "n_variants_found": int(len(ann)), "raw_cache": str(CACHE.relative_to(C.REPO_ROOT)),
                      "raw_cache_sha256_concat": h.hexdigest(), "query_fields": VARIANT_FIELDS.strip()}
    prov_fn.write_text(json.dumps(prov, indent=2))
    return 0


C_CODING = {"missense_variant", "stop_gained", "frameshift_variant", "splice_donor_variant",
            "splice_acceptor_variant", "start_lost", "stop_lost", "inframe_insertion", "inframe_deletion",
            "protein_altering_variant"}

if __name__ == "__main__":
    raise SystemExit(main())
