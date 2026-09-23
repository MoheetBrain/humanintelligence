#!/usr/bin/env python3
"""Sprint 5 — target characterisation ("modifiability map") for promoted genes. CHARACTERISATION ONLY:
no compound design, no docking, no dosing, no gene-therapy proposals, no self-use recommendations.

Promoted genes = the frozen deep-dive rule (CAUSAL_GENE_MODERATE+, direction D1-D3, perturbation P1-P3) plus
every Top-20 research-priority gene. Source: Open Targets Platform 26.06 target annotations (target class,
tractability buckets incl. structure/pocket/ligand evidence, chemical probes, clinical candidates count,
safety liabilities, subcellular location, LoF constraint, function description). A curated protein-type
column maps the ChEMBL target class to the brief's categories (enzyme, ion channel, GPCR, transporter,
receptor, scaffold, transcription factor, chromatin regulator, adhesion, secreted, other).

Output: reports/sprint5/modifiability_map.csv, data/sprint5/ot_target_annotations.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

API = "https://api.platform.opentargets.org/api/v4/graphql"
Q = """query T($id: String!) { target(ensemblId: $id) { id approvedSymbol approvedName biotype
  functionDescriptions
  targetClass { label level }
  tractability { label modality value }
  chemicalProbes { id isHighQuality mechanismOfAction }
  safetyLiabilities { event datasource }
  subcellularLocations { location source }
  geneticConstraint { constraintType oe oeUpper score }
  drugAndClinicalCandidates { count }
} }"""


def ensembl_id(sym: str) -> str | None:
    r = C.http_json(API, {"query": "query S($q:String!){ search(queryString:$q, entityNames:[\"target\"]) { hits { id name } } }",
                          "variables": {"q": sym}})
    for h in r["data"]["search"]["hits"]:
        if h["name"] == sym:
            return h["id"]
    return None


def protein_type(classes: list[str], fn: str, sym: str) -> str:
    c = " ".join(classes).lower()
    f = (fn or "").lower()
    if "ion channel" in c or "channel" in f and "voltage" in f:
        return "ion channel"
    if "gpcr" in c or "g-protein coupled" in f:
        return "GPCR"
    if "transporter" in c:
        return "transporter"
    if "kinase" in c or "enzyme" in c or "protease" in c or "hydrolase" in c or "oxidoreductase" in c or "transferase" in c:
        return "enzyme"
    if "transcription factor" in c:
        return "transcription factor"
    if "epigenetic" in c or "histone" in f or "chromatin" in f or "demethylase" in f:
        return "chromatin regulator"
    if "adhesion" in c or "cell adhesion" in f:
        return "adhesion protein"
    if "secreted" in c:
        return "secreted factor"
    if "receptor" in c:
        return "receptor"
    if "structural" in c or "scaffold" in f or "adapter" in f:
        return "scaffold"
    if "enzyme" in f or "catalyzes" in f or "catalyses" in f:
        return "enzyme"
    return "other/unclassified"


# Curated protein types where the ChEMBL class is missing/uninformative (basis: UniProt/HGNC function text,
# recorded per gene; curated by the orchestrator, characterisation only).
CURATED = {
    "SLC39A8": ("transporter", "ZIP8 metal-ion (Mn2+/Zn2+/Fe2+/Cd2+) importer; rs13107325 = A391T"),
    "DCC": ("receptor", "netrin-1 receptor; Ig-superfamily single-pass transmembrane; axon guidance"),
    "NEGR1": ("adhesion protein", "IgLON family GPI-anchored cell-adhesion molecule"),
    "KIFC2": ("other (motor protein)", "kinesin-14 family minus-end motor; neuronal dendrite transport"),
    "RC3H2": ("enzyme (E3 ubiquitin ligase / RNA-binding)", "Roquin-2; RING E3 ligase, mRNA decay"),
    "ANKRD12": ("chromatin regulator (transcriptional co-repressor)", "ankyrin-repeat nuclear co-repressor"),
    "GOSR1": ("other (Golgi SNARE)", "GS28 Qb-SNARE, ER-Golgi trafficking"),
    "RHEBL1": ("enzyme (small GTPase)", "Ras-homolog enriched in brain-like 1"),
    "WBP2NL": ("other (signalling adaptor)", "WW-domain binding protein 2 N-terminal like; sperm/oocyte (PAWP)"),
    "SEPTIN10": ("other (cytoskeletal GTPase)", "septin filament GTPase"),
    "SH3RF3": ("enzyme (E3 ubiquitin ligase / scaffold)", "SH3 domain RING finger"),
    "SOWAHC": ("other/unclassified", "ankyrin-repeat protein of unknown function"),
    "EDAR": ("receptor", "ectodysplasin-A TNF-family receptor"),
    "ZNF92": ("transcription factor", "KRAB zinc-finger"),
    "EIF3C": ("other (translation initiation factor)", "eIF3 subunit C"),
    "TUFM": ("other (mitochondrial translation factor)", "mitochondrial EF-Tu"),
    "CRB1": ("adhesion protein", "Crumbs homolog 1, apical polarity"),
    "RPS26": ("other (ribosomal protein)", "40S ribosomal protein S26; 'approved drug' tractability reflects ribosome-binding antibiotics, not target-selective agents"),
    "RIMS1": ("scaffold", "RIM1 active-zone scaffold"),
    "ZFTRAF1": ("other/unclassified", "zinc-finger TRAF-type 1 (CYHR1)"),
}


def main() -> int:
    C.load_rules()
    m = pd.read_csv(C.OUT / "causal_gene_evidence_matrix.csv")
    top = pd.read_csv(C.OUT / "_top20_core.csv")
    promo = m[m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"]) | m.direction_stratum.isin(["D1", "D2", "D3"])
              | m.perturbation_stratum.isin(["P1", "P2", "P3"])].gene.tolist()
    genes = sorted({g for g in promo + top[top.entity_type == "GENE"].gene.tolist()} | {"SLC39A8"})
    genes = [g.split(" (")[0] for g in genes]
    out, raw = [], {}
    for g in genes:
        eid = ensembl_id(g)
        if not eid:
            out.append({"gene": g, "status": "NOT_FOUND_IN_OPEN_TARGETS"})
            continue
        t = C.http_json(API, {"query": Q, "variables": {"id": eid}})["data"]["target"]
        raw[g] = t
        classes = [x["label"] for x in (t.get("targetClass") or [])]
        tr = t.get("tractability") or []
        sm = [x["label"] for x in tr if x["modality"] == "SM" and x["value"]]
        ab = [x["label"] for x in tr if x["modality"] == "AB" and x["value"]]
        pr = [x["label"] for x in tr if x["modality"] == "PR" and x["value"]]
        oc = [x["label"] for x in tr if x["modality"] == "OC" and x["value"]]
        loc = sorted({x["location"] for x in (t.get("subcellularLocations") or [])})
        lof = next((x for x in (t.get("geneticConstraint") or []) if x["constraintType"] == "lof"), {})
        fn = " ".join(t.get("functionDescriptions") or [])[:600]
        out.append({
            "gene": g, "ensembl_id": eid, "approved_name": t.get("approvedName"), "biotype": t.get("biotype"),
            "chembl_target_class": ";".join(classes),
            "protein_type": CURATED[g][0] if g in CURATED else protein_type(classes, fn, g),
            "protein_type_basis": ("curated: " + CURATED[g][1]) if g in CURATED else "ChEMBL target class / function text",
            "structure_or_pocket_evidence": ";".join(x for x in sm if any(k in x.lower() for k in ("structure", "pocket", "ligand"))) or "none recorded",
            "small_molecule_tractability": ";".join(sm) or "none",
            "antibody_tractability": ";".join(ab) or "none",
            "protac_tractability": ";".join(pr) or "none",
            "other_modalities": ";".join(oc) or "none",
            "extracellular_or_membrane": any(k in " ".join(loc).lower() for k in ("membrane", "extracellular", "secreted", "cell surface")),
            "subcellular_locations": ";".join(loc)[:300],
            "high_quality_chemical_probes": sum(1 for x in (t.get("chemicalProbes") or []) if x.get("isHighQuality")),
            "chemical_probe_moa": ";".join(sorted({str(x.get("mechanismOfAction")) for x in (t.get("chemicalProbes") or []) if x.get("mechanismOfAction")}))[:200],
            "clinical_candidates_count": (t.get("drugAndClinicalCandidates") or {}).get("count"),
            "safety_liabilities": ";".join(sorted({x["event"] for x in (t.get("safetyLiabilities") or []) if x.get("event")}))[:300],
            "lof_oe_upper": lof.get("oeUpper"),
            "function_summary": fn,
            "gene_class_sprint5": m.set_index("gene").gene_class.get(g),
            "note": "characterisation only; no compound design, dosing, gene therapy or self-use recommendation",
        })
    df = pd.DataFrame(out)
    df.to_csv(C.OUT / "modifiability_map.csv", index=False)
    (C.DATA / "ot_target_annotations.json").write_text(json.dumps({"retrieved_utc": C.utc_now(), "release": "26.06",
                                                                   "targets": raw}, indent=1, default=str))
    print(df[["gene", "protein_type", "chembl_target_class", "small_molecule_tractability", "clinical_candidates_count",
              "high_quality_chemical_probes"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
