#!/usr/bin/env python3
"""Sprint 3.1, parts 4 and 6 — synaptic system map and the adult-evidence hierarchy.

``reports/sprint3_1/synaptic_system_map.csv``
    One row per (gene, machinery category) for the named genes. Evidence comes from two
    independent layers kept in separate columns:
      * annotation: membership of the pre-registered SynGO/propagated-GO category sets
        (``data/sprint3_1/recon_sets.setannot``);
      * literature: ``data/sprint3_1/literature_curation.json`` (PMID-verified, species and
        evidence type recorded) when present.
    Genetic evidence (Davies MAGMA P, Bonferroni, LD locus, fine-mapping driver, colocalisation
    audit) is attached per gene.

``reports/sprint3_1/adult_evidence_hierarchy.csv``
    Replaces the Sprint-3 "adult-modifiable" wording with a five-tier hierarchy, each tier a
    separate boolean so that no tier is inferred from a lower one:
      ADULT_EXPRESSED            GTEx v10 adult brain expression (Sprint-3 flag)
      ADULT_EXPRESSION_DYNAMIC   Sprint-3 developmental class ADULT_DYNAMIC
      ADULT_FUNCTIONAL_EVIDENCE  curated adult-age functional evidence (any species; species stated)
      ADULT_CAUSAL_EVIDENCE      human causal chain in adults: direction-resolved adult-brain
                                 colocalisation AND independent-cohort support (none yet)
      ADULT_INTERVENTION_READY   never assigned by this project
    Expression timing and functional timing are separate columns (DCC is the test case).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "reports" / "sprint3_1"
D31 = REPO / "data" / "sprint3_1"
S3 = REPO / "reports" / "gene_tournament"
MAP_GENES = ["NEGR1", "EXOC4", "BSN", "SYT1", "NSF", "DCC", "RIMS2", "CADM2", "PTPRT", "GRIA4", "KCNJ3",
             "ERBB3", "MEF2C", "NT5DC2", "RPS26"]
CATEGORIES = ["synapse_formation_adhesion", "active_zone_organisation", "vesicle_cycle_trafficking",
              "vesicle_docking_priming", "ca_triggered_release", "snare_cycle", "receptor_trafficking",
              "postsynaptic_plasticity_structure", "activity_dependent_remodelling", "non_synaptic_or_other"]
LIT_ALIASES = {"vesicle_trafficking": "vesicle_cycle_trafficking", "snare_recycling": "snare_cycle",
               "dendritic_postsynaptic_plasticity": "postsynaptic_plasticity_structure",
               "activity_dependent_remodelling": "activity_dependent_remodelling"}


def read_setannot(path: Path) -> dict[str, set[int]]:
    return {p[0]: {int(g) for g in p[1:]} for p in
            (ln.split() for ln in path.read_text(encoding="utf-8").splitlines()) if p}


def literature() -> dict:
    path = D31 / "literature_curation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def lit_entries(lit: dict) -> dict[str, dict]:
    out = {}
    for entry in lit.get("system_map", []) or []:
        gene = str(entry.get("gene", "")).upper()
        if gene:
            out[gene] = entry
    return out


def lit_categories(entry: dict) -> dict[str, list[dict]]:
    """{category: [evidence dicts]} from the curation's nested category -> evidence layout."""
    cats: dict[str, list[dict]] = {}
    for c in entry.get("categories") or []:
        if not isinstance(c, dict):
            continue
        name = LIT_ALIASES.get(str(c.get("category", "")), str(c.get("category", "")))
        for ev in c.get("evidence") or [c]:
            cats.setdefault(name, []).append({**ev, "strength": c.get("strength", "")})
    return cats


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sets = read_setannot(D31 / "recon_sets.setannot")
    rank = pd.read_csv(S3 / "direct_cognition_rank.csv")
    rank = rank[rank.gene.isin(MAP_GENES)].drop_duplicates("gene").set_index("gene")
    dev = pd.read_parquet(REPO / "data/gene_tournament/developmental_classification.parquet")
    dev = dev[dev.gene_symbol.isin(MAP_GENES)].drop_duplicates("gene_symbol").set_index("gene_symbol")
    fm = pd.read_csv(S3 / "fine_mapping_support.csv").drop_duplicates("gene").set_index("gene")
    recount = pd.read_csv(OUT / "direction_rule_recount_all_genes.csv").set_index("gene")
    top_h = pd.read_csv(S3 / "TOP50_HUMAN_COGNITION_GENES.csv").set_index("gene")
    top_a = pd.read_csv(S3 / "TOP50_ADULT_MODIFIABLE_GENES.csv").set_index("gene")
    lit = literature()
    lit_g = lit_entries(lit)

    rows, tiers = [], []
    for gene in MAP_GENES:
        r = rank.loc[gene] if gene in rank.index else None
        eid = int(r.entrez_id) if r is not None and pd.notna(r.entrez_id) else None
        compartment = ("both" if eid in sets["PRE_AND_POST"] else "presynaptic" if eid in sets["PRE"]
                       else "postsynaptic" if eid in sets["POST"] else
                       "synaptic (unassigned)" if eid in sets["SYNAPSE"] else "not in SynGO")
        entry = lit_g.get(gene, {})
        lcats = lit_categories(entry)
        base = {
            "gene": gene, "entrez_id": eid,
            "davies_magma_P": float(r.gene_P) if r is not None else np.nan,
            "bonferroni_davies": bool(r.bonferroni_davies) if r is not None else False,
            "direct_cognition_rank": int(r.direct_cognition_rank) if r is not None else None,
            "ld_block_r0.2": int(r["ld_block_r0.2"]) if r is not None and pd.notna(r["ld_block_r0.2"]) else None,
            "top50_natural_rank": int(top_h.loc[gene, "consensus_rank"]) if gene in top_h.index else None,
            "top50_adult_rank": int(top_a.loc[gene, "consensus_rank"]) if gene in top_a.index else None,
            "syngo_compartment": compartment,
            "literature_primary_compartment": entry.get("primary_compartment", "NOT_CURATED" if not lit else ""),
            "literature_function": entry.get("canonical_function", entry.get("function", "")),
            "literature_critical_note": entry.get("critical_note", ""),
            "fine_mapping_driver": (fm.loc[gene, "supported_call_drivers"] if gene in fm.index
                                    and pd.notna(fm.loc[gene, "supported_call_drivers"]) else
                                    ("positional only" if gene in fm.index else "no GWAS credible set")),
            "direction_rows_sprint3": int(recount.loc[gene, "sprint3_rows"]) if gene in recount.index else 0,
            "direction_strict_gene_level_rows": int(recount.loc[gene, "strict_gene_level_rows"]) if gene in recount.index else 0,
            "direction_independent_units_upper_bound": int(recount.loc[gene, "max_units_upper_bound"]) if gene in recount.index else 0,
            "direction_resolved_on_units": bool(recount.loc[gene, "resolved_on_units"]) if gene in recount.index else False,
        }
        for cat in CATEGORIES:
            ann = eid in sets.get(f"CAT_{cat}", set())
            ev = lcats.get(cat, [])
            pmids = sorted({str(e.get("pmid")) for e in ev if e.get("pmid")})
            species = sorted({str(e.get("species_system", e.get("species", ""))) for e in ev if e})
            strength = sorted({str(e.get("strength", "")) for e in ev if e.get("strength")})
            rows.append({**base, "category": cat, "annotation_member": ann,
                         "literature_supported": bool(ev), "literature_pmids": ";".join(pmids),
                         "literature_species": ";".join(s for s in species if s),
                         "literature_strength": ";".join(strength),
                         "support": ("annotation+literature" if ann and ev else "annotation only" if ann
                                     else "literature only" if ev else "none")})

        d = dev.loc[gene] if gene in dev.index else None
        adult_fun = []
        if gene == "DCC":
            adult_fun = [e for e in (lit.get("dcc_adult_function", {}) or {}).get("items", [])
                         if "ADULT_FUNCTIONAL" in str(e.get("evidence_tier", "")) or
                         "ADULT_CAUSAL" in str(e.get("evidence_tier", ""))]
        # The system-map curation records mechanism, not age window, so only DCC (curated for age)
        # can be scored on this tier; other genes are NOT_CURATED_FOR_AGE, never False.
        age_curated = gene == "DCC"
        tiers.append({
            "gene": gene,
            "expression_timing": d.developmental_class if d is not None else "UNKNOWN",
            "ADULT_EXPRESSED": bool(d.adult_expressed) if d is not None else False,
            "ADULT_EXPRESSION_DYNAMIC": bool(d is not None and d.developmental_class == "ADULT_DYNAMIC"),
            "ADULT_FUNCTIONAL_EVIDENCE": (bool(adult_fun) if age_curated else None) if lit else None,
            "adult_functional_pmids": ";".join(sorted({str(e.get("pmid")) for e in adult_fun if e.get("pmid")})),
            "adult_functional_species": ";".join(sorted({str(e.get("species_system", e.get("species", "")))[:60]
                                                         for e in adult_fun})),
            "ADULT_CAUSAL_EVIDENCE": False,
            "adult_causal_note": ("direction-resolved on independent adult-brain QTL units but NO independent-"
                                  "cohort cognition support yet (Sprint-4 Gate B/C)" if base["direction_resolved_on_units"]
                                  else "no direction-resolved adult-brain chain"),
            "ADULT_INTERVENTION_READY": False,
            "sprint3_label": "adult-modifiable (Sprint 3)" if gene in top_a.index else "",
            "corrected_label": "ADULT-EXPRESSION-COMPATIBLE" if (d is not None and bool(d.adult_expressed)) else
                               "NOT ADULT-EXPRESSION-COMPATIBLE",
            "functional_timing": ("adult functional evidence in rodents; developmental in humans (see PMIDs)"
                                  if adult_fun else ("NOT_CURATED_FOR_AGE" if not age_curated else
                                                     "no adult functional evidence found")),
        })
    pd.DataFrame(rows).to_csv(OUT / "synaptic_system_map.csv", index=False, float_format="%.4g")
    tiers = pd.DataFrame(tiers)
    # every adult top-50 gene gets the corrected label even if not in the named list
    extra = [{"gene": g, "expression_timing": top_a.loc[g, "developmental_class"],
              "ADULT_EXPRESSED": True, "ADULT_EXPRESSION_DYNAMIC": top_a.loc[g, "developmental_class"] == "ADULT_DYNAMIC",
              "ADULT_FUNCTIONAL_EVIDENCE": None, "ADULT_CAUSAL_EVIDENCE": False, "ADULT_INTERVENTION_READY": False,
              "sprint3_label": "adult-modifiable (Sprint 3)", "corrected_label": "ADULT-EXPRESSION-COMPATIBLE",
              "functional_timing": "not curated in Sprint 3.1"}
             for g in top_a.index if g not in set(tiers.gene)]
    tiers = pd.concat([tiers, pd.DataFrame(extra)], ignore_index=True)
    tiers.to_csv(OUT / "adult_evidence_hierarchy.csv", index=False)
    print(pd.DataFrame(rows).groupby("gene").agg(ann=("annotation_member", "sum"),
                                                 lit=("literature_supported", "sum")).to_string())
    print(tiers.head(16).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
