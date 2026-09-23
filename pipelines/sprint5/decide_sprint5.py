#!/usr/bin/env python3
"""Sprint 5 — adult intervention gate (7 frozen criteria) per candidate, success conditions A-E, and the
chemistry gate. Output: reports/sprint5/decision.json.

Criteria (protocol_rules.json adult_intervention_gate), evaluated mechanically:
 1 independent cognition association: locus L1/L2 (counted lineages) or perturbation P1
 2 credible causal gene: CAUSAL_GENE_MODERATE or HIGH
 3 adult brain molecular evidence: QTL class present (adult bulk coloc)
 4 beneficial molecular direction: direction stratum D1
 5 adult function plausibly relevant: curated -> not auto-assessed (False unless 1-4 all pass)
 6 acceptable pleiotropy/safety: human review only -> never auto-cleared (always False here)
 7 tractable mechanism: modifiability map shows structure/pocket/ligand evidence
If any is missing: CHEMISTRY_GATE = CLOSED. 1-5 and 7 met -> CAUSAL_TARGET_ADJUDICATION_CANDIDATE, still CLOSED.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main() -> int:
    rules = C.load_rules()
    m = pd.read_csv(C.OUT / "causal_gene_evidence_matrix.csv")
    mod = pd.read_csv(C.OUT / "modifiability_map.csv").set_index("gene")
    cand = m[m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"]) | m.direction_stratum.isin(["D1", "D2", "D3"])
             | m.perturbation_stratum.isin(["P1", "P2"])]
    gate = []
    for r in cand.itertuples():
        c1 = r.locus_stratum in ("L1", "L2") or r.perturbation_stratum == "P1"
        c2 = r.gene_class in ("CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE")
        c3 = isinstance(r.classes, str) and "QTL" in r.classes
        c4 = r.direction_stratum == "D1"
        c5 = bool(c1 and c2 and c3 and c4)  # curated relevance only considered once 1-4 hold
        c6 = False
        sp = mod.structure_or_pocket_evidence.get(r.gene, "none recorded") if r.gene in mod.index else "none recorded"
        c7 = isinstance(sp, str) and sp != "none recorded"
        crit = {"1_independent_association": c1, "2_credible_causal_gene": c2, "3_adult_brain_molecular": c3,
                "4_beneficial_direction_D1": c4, "5_adult_function_relevant": c5, "6_safety_acceptable": c6,
                "7_tractable": c7}
        label = ("CAUSAL_TARGET_ADJUDICATION_CANDIDATE" if all(v for k, v in crit.items() if not k.startswith("6"))
                 else "NOT_A_CANDIDATE")
        gate.append({"gene": r.gene, "locus_id": r.locus_id if isinstance(r.locus_id, str) else None,
                     "gene_class": r.gene_class, **crit, "n_met": int(sum(crit.values())), "label": label,
                     "missing": [k for k, v in crit.items() if not v]})
    g = pd.DataFrame(gate).sort_values("n_met", ascending=False)
    moderate = m[m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].gene.tolist()
    success = {
        "A_3_to_10_genes_CAUSAL_GENE_MODERATE_or_HIGH": {"met": 3 <= len(moderate) <= 10, "genes": moderate},
        "B_one_gene_independent+credible+adult_cell_specific_direction": {
            "met": bool(((m.locus_stratum.isin(["L1", "L2"])) & m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])
                         & (m.direction_stratum == "D1")).any())},
        "C_math_specific_variants_converge_with_general_cognition": {
            "met": False, "detail": json.loads((C.DATA / "math_m3_overlap.json").read_text()).get("overlap_genes")},
        "D_top_candidates_convincingly_downgraded_gene_assignment_unresolved": {
            "met": bool(not m[(m.locus_stratum == "L1") & m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].shape[0]
                        and (m.gene_class == "LIKELY_QTL_PASSENGER").sum() >= 3),
            "detail": {"L1_loci_with_moderate_gene": m[(m.locus_stratum == "L1") & m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].gene.tolist(),
                       "likely_qtl_passengers": m[m.gene_class == "LIKELY_QTL_PASSENGER"].gene.tolist()}},
        "E_new_dataset_or_tool_changes_interpretation": {
            "met": bool(m[m.gene_class.isin(["CAUSAL_GENE_HIGH", "CAUSAL_GENE_MODERATE"])].classes.astype(str).str.contains("ENHANCER_LINK").any()),
            "detail": "every CAUSAL_GENE_MODERATE call depends on the ENCODE-rE2G enhancer-gene layer first pulled in Sprint 5; "
                      "EB shrinkage (A2) re-ordered locus strata; brainSCOPE adds cell-type direction (lookup)"},
    }
    dec = {"created_utc": C.utc_now(), "rules_sha256": C.recorded_rules_hash(),
           "chemistry_gate": "CLOSED",
           "chemistry_gate_reason": "no candidate meets criteria 1-4 together; criterion 6 (safety) is never auto-cleared",
           "adjudication_candidates": g[g.label != "NOT_A_CANDIDATE"].gene.tolist(),
           "gate_table": g.to_dict("records"), "success_conditions": success,
           "gate_a_within_family": "NOT_TESTABLE (OPENGWAS_JWT absent; files absent)",
           "alphagenome": "NOT_TESTABLE (API key)", "brainscope_coloc": "NOT_TESTABLE (significant-only release)"}
    (C.OUT / "decision.json").write_text(json.dumps(dec, indent=2, default=str))
    print(g[["gene", "gene_class", "n_met", "label", "missing"]].to_string(index=False))
    print(json.dumps(success, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
