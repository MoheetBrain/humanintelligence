#!/usr/bin/env python3
"""Sprint 5A section 3 — one canonical, frozen list of human genetic inputs (panels A-F).
Anchor gene names are LABELS ONLY. Output: data/sprint5a/canonical_inputs.csv + sha256 in data/sprint5a/canonical_inputs.json"""
import hashlib
import json
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
rows = []
loci = pd.read_csv(R / "reports/sprint4/genc_independent_loci.csv")
lc = pd.read_csv(R / "reports/sprint5/locus_confidence_rank.csv")
strat = {lid: r.locus_stratum for r in lc.itertuples() for lid in str(r.labels).split(";")}
for r in loci.itertuples():
    rows.append({"panel": "A_159_cognition_loci", "id": r.locus_id, "label_only": r.top_gene, "variant": r.lead_snp,
                 "allele": r.cognition_increasing_allele, "source": "Sprint-3 Davies 2018 LD loci",
                 "flags": ";".join(x for x in ["B_GC_SUPPORTED" if r.gate_b_locus_class == "G&C_SUPPORTED" else "",
                                               f"S5_{strat.get(r.locus_id, 'NA')}"] if x)})
for r in loci[loci.gate_b_locus_class == "G&C_SUPPORTED"].itertuples():
    rows.append({"panel": "B_GC_supported_loci", "id": r.locus_id, "label_only": r.top_gene, "variant": r.lead_snp,
                 "allele": r.cognition_increasing_allele, "source": "Sprint-4 Gate B", "flags": ""})
for g in ["DCC", "EXOC4", "NEGR1", "SYT1", "NT5DC2", "STAB1", "GNL3", "NEK4", "PPM1M", "RPS26", "SUOX", "ERBB3",
          "RHEBL1", "PFKM", "DDN", "WBP2NL", "CYP2D6", "NAGA", "MEF2C", "BSN", "CADM2", "SLC39A8", "TUFM", "SH2B1",
          "EIF3C", "AKAP6", "NPAS3", "KIFC2", "DNPH1"]:
    rows.append({"panel": "C_stress_tests", "id": g, "label_only": g, "variant": "", "allele": "",
                 "source": "Sprint 3-5 leads/contested assignments", "flags": ""})
for g in ["ADGRB2", "KDM5B", "GIGYF1", "ANKRD12", "SLC8A1", "RC3H2", "CACNA1A", "BCAS3"]:
    rows.append({"panel": "D_rare_coding", "id": g, "label_only": g, "variant": "", "allele": "",
                 "source": "Chen 2023 (+Genebass/Wu 2025)",
                 "flags": "EA_PROXY_ONLY" if g in ("ADGRB2", "GIGYF1", "SLC8A1", "BCAS3") else "COGNITION_EXOME_WIDE"})
cnv = pd.read_csv(R / "reports/sprint5/cnv_positive_dosage.csv")
for r in cnv[cnv.verdict.astype(str).str.startswith(("NOMINAL", "SUPPORTED"))].itertuples():
    rows.append({"panel": "E_positive_perturbation", "id": r.region_or_gene, "label_only": r.genes, "variant": "",
                 "allele": "", "source": r.study, "flags": r.verdict})
m = pd.read_csv(R / "data/sprint5/math53_variants.csv")
for r in m.itertuples():
    rows.append({"panel": "F_math53", "id": r.rsid, "label_only": "", "variant": r.rsid, "allele": r.math_increasing_allele,
                 "source": "Giannelis 2025 Supp Table S2", "flags": "QUANTITATIVE_ABILITY_PROXY"})
df = pd.DataFrame(rows)
out = R / "data/sprint5a/canonical_inputs.csv"
df.to_csv(out, index=False)
h = hashlib.sha256(out.read_bytes()).hexdigest()
(R / "data/sprint5a/canonical_inputs.json").write_text(json.dumps({"sha256": h, "counts": df.panel.value_counts().to_dict(),
                                                                    "note": "anchor gene names are labels only"}, indent=1))
print(df.panel.value_counts().to_dict(), h[:12])
