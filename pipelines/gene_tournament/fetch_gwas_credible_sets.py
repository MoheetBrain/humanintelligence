#!/usr/bin/env python3
"""Sprint 3, Part G -- GWAS credible sets and locus-to-gene for STRICT cognition studies.

Why this exists
---------------
The first Open Targets pass went gene-first through ``Target.credibleSets``. That field
returns only QTL credible sets in which the gene is the molecular trait -- never a GWAS
credible set -- so it could not answer Part G at all: every gene came back with 0 GWAS
credible sets and no L2G. This module goes study-first, which is the direction the
Platform's data model actually supports:

    study (strict-tier cognition GWAS) -> credible sets (SuSiE-inf / PICS)
        -> lead variant, lead-variant PIP, most severe consequence
        -> L2G predictions, with each prediction's feature SHAP values

Two things it refuses to do
---------------------------
* **Nearest gene is never enough.** For every L2G call the dominant SHAP feature is
  recorded. A call whose largest positive contributor is a DISTANCE feature is labelled
  ``positional_driven`` (distance or local gene density) and does not count as causal-gene
  support in the gene summary.
* **Studies are not loci.** The same locus is fine-mapped in Savage, Davies, Lee and UKB
  fluid intelligence. Credible sets are clustered by lead-variant position (1 Mb windows on
  the same chromosome) and a gene's support is counted in DISTINCT LOCI, with the number of
  studies reported separately.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
CACHE = REPO_ROOT / "data" / "raw" / "opentargets_gwas_cs" / "2026-09-22"
DATA = REPO_ROOT / "data" / "gene_tournament"
OUT = REPO_ROOT / "reports" / "gene_tournament"
PAGE = 40
# Positional priors: distance to the sentinel/TSS and local gene density. A call these
# dominate is a nearest-gene call, however it is dressed. (proteinGeneCount500kb was
# added on audit: it drove 311 of 1,890 top calls and is gene density, not biology.)
POSITIONAL_FEATURES = ("distance", "proteingenecount")
ENHANCER_FEATURES = ("e2g",)
CODING_FEATURES = ("vep",)

Q = """query S($id:String!,$i:Int!,$n:Int!){ study(studyId:$id){ id traitFromSource nSamples pubmedId
 credibleSets(page:{index:$i,size:$n}){ count rows{ studyLocusId finemappingMethod chromosome position
  confidence pValueMantissa pValueExponent
  locus(page:{index:0,size:1}){ rows{ variant{id} posteriorProbability } }
  variant{ id rsIds mostSevereConsequence{label} }
  l2GPredictions(page:{index:0,size:3}){ rows{ target{id approvedSymbol} score features{name value shapValue} } } } } } }"""


def gq(variables: dict) -> dict:
    key = hashlib.sha256(json.dumps(variables, sort_keys=True).encode()).hexdigest()[:20]
    path = CACHE / f"{variables['id']}_{variables['i']}_{key}.json.gz"
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    body = json.dumps({"query": Q, "variables": variables}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
            data = json.loads(urllib.request.urlopen(req, timeout=180).read())
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(json.dumps(data).encode(), mtime=0))
            return data
        except Exception:  # noqa: BLE001 -- retried, then recorded as an error, never as empty
            time.sleep(2 ** attempt)
    return {"errors": [{"message": "request failed after retries"}]}


def main() -> int:
    tiers = pd.read_csv(DATA / "study_classification.csv")
    studies = sorted(set(tiers[tiers.tier == "direct_strict"].accession_id) | {"GCST005626"})
    rows, status = [], {}
    for sid in studies:
        i, total = 0, None
        while True:
            d = gq({"id": sid, "i": i, "n": PAGE})
            st = (d.get("data") or {}).get("study")
            if d.get("errors") and not st:
                status[sid] = "error"; break
            if not st:
                status[sid] = "not_in_open_targets"; break
            cs = st["credibleSets"]; total = cs["count"]
            for r in cs["rows"]:
                lead = (r.get("locus") or {}).get("rows") or []
                base = {"study_id": sid, "trait": st["traitFromSource"], "n_samples": st["nSamples"],
                        "study_locus_id": r["studyLocusId"], "method": r["finemappingMethod"],
                        "chromosome": r["chromosome"], "position": r["position"],
                        "confidence": r.get("confidence"),
                        "lead_variant": r["variant"]["id"], "lead_rsids": "|".join(r["variant"].get("rsIds") or []),
                        "lead_pip": lead[0]["posteriorProbability"] if lead else None,
                        "lead_consequence": (r["variant"].get("mostSevereConsequence") or {}).get("label")}
                preds = (r.get("l2GPredictions") or {}).get("rows") or []
                if not preds:
                    rows.append({**base, "l2g_rank": None, "gene": None, "ensembl_id": None, "l2g_score": None})
                for k, p in enumerate(preds, 1):
                    feats = p.get("features") or []
                    pos = sorted((f for f in feats if (f.get("shapValue") or 0) > 0), key=lambda f: -f["shapValue"])
                    top = pos[0]["name"] if pos else None
                    coding = max((f.get("value") or 0 for f in feats if f["name"].lower().startswith(CODING_FEATURES)), default=0)
                    coloc = max((f.get("value") or 0 for f in feats if "Coloc" in f["name"] and "Neighbourhood" not in f["name"]), default=0)
                    rows.append({**base, "l2g_rank": k, "gene": p["target"]["approvedSymbol"],
                                 "ensembl_id": p["target"]["id"], "l2g_score": p["score"],
                                 "dominant_shap_feature": top,
                                 "positional_driven": bool(top and top.lower().startswith(POSITIONAL_FEATURES)),
                                 "enhancer_feature_max": max((f.get("value") or 0 for f in feats if f["name"].lower().startswith(ENHANCER_FEATURES)), default=0),
                                 "coding_feature_max": coding, "qtl_coloc_feature_max": coloc})
            i += 1
            if i * PAGE >= total:
                status[sid] = f"ok:{total}"; break
            time.sleep(0.1)
    cs = pd.DataFrame(rows)
    # Rows with no L2G prediction leave these blank; an object column makes `~` return -2/-1
    # (both truthy) -- the bug that first reported 602 supported genes instead of 160.
    cs["positional_driven"] = cs.positional_driven.fillna(False).astype(bool)
    cs.to_csv(DATA / "gwas_credible_sets_l2g.csv", index=False)

    # locus clustering: lead positions within 1 Mb on the same chromosome form one locus
    leads = cs.drop_duplicates("study_locus_id").sort_values(["chromosome", "position"])
    locus_id, last = {}, (None, -10 ** 12)
    n = 0
    for _, r in leads.iterrows():
        if r.chromosome != last[0] or r.position - last[1] > 1_000_000:
            n += 1
        locus_id[r.study_locus_id] = f"L{n:04d}"
        last = (r.chromosome, r.position)
    cs["locus"] = cs.study_locus_id.map(locus_id)

    top = cs[cs.l2g_rank == 1]
    g = []
    for gene, grp in cs[cs.gene.notna()].groupby("gene"):
        t1 = grp[grp.l2g_rank == 1]
        sup = t1[(t1.l2g_score >= 0.5) & (~t1.positional_driven)]
        g.append({"gene": gene, "n_credible_sets_any_rank": grp.study_locus_id.nunique(),
                  "n_credible_sets_top_l2g": t1.study_locus_id.nunique(),
                  "n_supported_credible_sets": sup.study_locus_id.nunique(),
                  "n_supported_loci": sup.locus.nunique(), "n_supporting_studies": sup.study_id.nunique(),
                  "max_l2g": grp.l2g_score.max(),
                  "summed_top_l2g_per_locus": float(t1.groupby("locus").l2g_score.max().sum()),
                  "max_lead_pip_where_top": t1.lead_pip.max() if len(t1) else None,
                  "n_top_calls_positional_driven": int(t1.positional_driven.sum()),
                  # Support flags describe what DROVE the supported calls, not whether a
                  # feature was merely non-zero (a first version counted any VEP value > 0,
                  # which made "coding support" true for almost every gene).
                  "coding_support": bool(sup.dominant_shap_feature.fillna("").str.lower().str.startswith("vep").any()
                                         or sup.lead_consequence.fillna("").str.contains("missense|stop_gained|frameshift|splice_donor|splice_acceptor").any()),
                  "chromatin_contact_support": bool(sup.dominant_shap_feature.fillna("").str.lower().str.startswith("e2g").any()),
                  "qtl_coloc_support_in_l2g": bool(sup.dominant_shap_feature.fillna("").str.contains("Coloc").any()),
                  "supported_call_drivers": "|".join(sorted(set(sup.dominant_shap_feature.dropna()))),
                  "nearest_gene_used_as_sufficient": False})
    gs = pd.DataFrame(g)
    gs["fine_mapping_score"] = gs.summed_top_l2g_per_locus.where(gs.n_supported_loci > 0, 0.0)
    gs["fine_mapping_rank"] = gs.fine_mapping_score.rank(ascending=False, method="min").astype(int)
    gs.sort_values("fine_mapping_rank").to_csv(OUT / "fine_mapping_support.csv", index=False)
    prov = {"retrieved_utc": utc_now(), "endpoint": ENDPOINT, "query": Q, "studies": status,
            "n_credible_sets": int(cs.study_locus_id.nunique()), "n_loci": int(cs.locus.nunique()),
            "n_genes_with_supported_locus": int((gs.n_supported_loci > 0).sum()),
            "n_top_calls": int(len(top)), "n_top_calls_positional_driven": int(top.positional_driven.sum()),
            "dominant_feature_counts_top_calls": top.dominant_shap_feature.value_counts().to_dict(),
            "cache": str(CACHE.relative_to(REPO_ROOT))}
    (DATA / "gwas_credible_sets_provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    print(json.dumps({k: v for k, v in prov.items() if k not in ("query", "studies")}, indent=1))
    print("studies:", pd.Series(status).str.split(":").str[0].value_counts().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
