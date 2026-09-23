#!/usr/bin/env python3
"""Sprint 5 — the cognition variant query list (GRCh38) used by every per-variant layer.

Sources (no new association testing here; this only assembles and re-coordinates variants):
  * SuSiE-RSS credible-set variants on the 36 Sprint-4 Gate-C loci (Davies 2018, GRCh37);
  * Open Targets GWAS credible-set lead variants for the same loci (Sprint 3, GRCh38 ids);
  * the lead SNP of every one of the 159 Sprint-3 LD loci (so locus-level lookups cover them all).
rsIDs are mapped to GRCh38 with Ensembl REST POST /variation (batched, 200 ids per call); every
unmapped id is kept with status UNMAPPED rather than dropped.

Output: data/sprint5/query_variants_cognition.csv, data/sprint5/query_variants_provenance.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

ENSEMBL = "https://rest.ensembl.org/variation/homo_sapiens"


def ensembl_grch38(rsids: list[str]) -> pd.DataFrame:
    rows = []
    ids = sorted(set(r for r in rsids if isinstance(r, str) and r.startswith("rs")))
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        res = C.http_json(ENSEMBL, {"ids": batch})
        for rid in batch:
            rec = res.get(rid)
            if not rec:
                rows.append({"rsid": rid, "grch38_status": "UNMAPPED"})
                continue
            maps = [m for m in rec.get("mappings", []) if m.get("assembly_name") == "GRCh38"
                    and str(m.get("seq_region_name")) in {str(c) for c in list(range(1, 23)) + ["X"]}]
            if not maps:
                rows.append({"rsid": rid, "grch38_status": "NO_PRIMARY_MAPPING"})
                continue
            m = maps[0]
            rows.append({"rsid": rid, "current_rsid": rec.get("name", rid), "chr38": str(m["seq_region_name"]),
                         "pos38": int(m["start"]), "allele_string": m.get("allele_string"),
                         "maf_ensembl": rec.get("MAF"), "minor_allele": rec.get("minor_allele"),
                         "most_severe_consequence": rec.get("most_severe_consequence"),
                         "grch38_status": "MAPPED" if len(maps) == 1 else "MULTI_MAPPED_FIRST_USED"})
        print(f"  ensembl {min(i + 200, len(ids))}/{len(ids)}", flush=True)
    return pd.DataFrame(rows)


def main() -> int:
    fm = pd.read_parquet(C.S4_OUT / "locus_finemapping.parquet")
    fm["pip"] = pd.to_numeric(fm["pip"], errors="coerce")
    su = fm[fm.source.str.contains("SuSiE")].copy()
    su = su.rename(columns={"variant": "rsid", "credible_set": "susie_cs", "pip": "susie_pip",
                            "pos_grch37": "pos37", "chr": "chr37", "effect_allele": "davies_effect_allele"})
    su["origin"] = "SUSIE_CS_DAVIES"
    ot = fm[~fm.source.str.contains("SuSiE")].copy()
    ot = ot.rename(columns={"variant": "rsid", "pip": "ot_pip", "study_id": "ot_study_id", "trait": "ot_trait"})
    ot["origin"] = "OT_CREDIBLE_SET_SPRINT3"
    loci = pd.read_csv(C.S4_OUT / "genc_independent_loci.csv")
    lead = loci[["locus_id", "top_gene", "lead_snp", "cognition_increasing_allele", "davies_z",
                 "gate_b_locus_class", "gate_b_FDR_primary"]].rename(columns={"lead_snp": "rsid"})
    lead["origin"] = "SPRINT3_LOCUS_LEAD"
    allv = pd.concat([su[["locus_id", "rsid", "origin", "susie_cs", "susie_pip", "chr37", "pos37",
                          "davies_z", "davies_effect_allele", "cs_size"]],
                      ot[["locus_id", "rsid", "origin", "ot_study_id", "ot_trait", "ot_pip",
                          "lead_variant_grch38", "top_l2g_gene", "l2g_driver"]],
                      lead], ignore_index=True)
    mp = ensembl_grch38(allv.rsid.dropna().tolist())
    allv = allv.merge(mp, on="rsid", how="left")
    # OT variant ids are already GRCh38 chr_pos_ref_alt; fall back to them when Ensembl has none
    miss = allv.pos38.isna() & allv.lead_variant_grch38.notna()
    parts = allv.loc[miss, "lead_variant_grch38"].str.split("_", expand=True)
    if len(parts):
        allv.loc[miss, "chr38"] = parts[0]
        allv.loc[miss, "pos38"] = pd.to_numeric(parts[1])
        allv.loc[miss, "grch38_status"] = "FROM_OT_VARIANT_ID"
    allv["top_gene_label"] = allv.locus_id.map(loci.drop_duplicates("locus_id").set_index("locus_id").top_gene)
    allv.to_csv(C.DATA / "query_variants_cognition.csv", index=False)
    prov = {"created_utc": C.utc_now(), "script": "pipelines/sprint5/build_query_variants.py",
            "ensembl_endpoint": ENSEMBL, "n_rows": int(len(allv)), "n_unique_rsid": int(allv.rsid.nunique()),
            "status_counts": allv.drop_duplicates("rsid").grch38_status.value_counts(dropna=False).to_dict(),
            "inputs": {p: C.sha256_file(C.REPO_ROOT / p) for p in
                       ["reports/sprint4/locus_finemapping.parquet", "reports/sprint4/genc_independent_loci.csv"]}}
    (C.DATA / "query_variants_provenance.json").write_text(json.dumps(prov, indent=2, default=str))
    print(json.dumps(prov, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
