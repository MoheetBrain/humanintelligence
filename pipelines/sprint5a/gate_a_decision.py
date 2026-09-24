#!/usr/bin/env python3
"""Apply the FROZEN Sprint-4 decision precedence (research/sprint4/frozen_hypotheses.json rules.decision) now that
Gate A is testable. pipelines/sprint4/decide.py hard-codes the Gate-A-untestable branch (pivot_a = False; otherwise
"UNDETERMINED") and re-runs the fetch, so it cannot be used as is; this script evaluates the same frozen rules
literally from the Gate-A/Gate-B outputs without changing any threshold. Output: reports/sprint4/decision_gate_a_update.json"""
import json
import sys
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "pipelines/sprint4"))
import common as C4  # noqa: E402

frozen = C4.load_frozen()
rules = frozen["rules"]["decision"]
a = pd.read_csv(R / "reports/sprint4/within_family_synaptic_sets.csv")
b = pd.read_csv(R / "reports/sprint4/genc_independent_synaptic_sets.csv")
gb = json.loads((R / "data/sprint4/gate_b_summary.json").read_text())
cal = json.loads((R / "reports/sprint4/within_family_power_calibration.json").read_text())
dirr = pd.read_csv(R / "reports/sprint4/directionality_resolution.csv")
bcol = "classification" if "classification" in b.columns else next(c for c in b.columns if "class" in c.lower())
bp = b[(b.get("primary_phenotype", True) == True) & (b.get("spec", "frozen_sprint3_spec") == "frozen_sprint3_spec")] if "spec" in b.columns else b
a_beyond = int(((a.classification == "INCONSISTENT") & (a.subtype == "BEYOND_EXPECTED_NOISE")).sum())
a_power_ok = bool((a.power_f078.fillna(0) >= 0.5).all())
pivot_a = a_beyond >= 3 and a_power_ok
b_beyond = int(((bp[bcol] == "INCONSISTENT") & (bp.get("subtype", "") == "BEYOND_EXPECTED_NOISE")).sum())
pivot_b = b_beyond >= 3 and bool((bp.get("power_f_lower", pd.Series([0])).fillna(0) >= 0.5).all())
retry_nt = bool((a.classification == "NOT_TESTABLE").all())
a_direct = a[a.classification == "DIRECT_EFFECT_SUPPORTED"].set.tolist()
b_indep = bp[bp[bcol] == "INDEPENDENT_SUPPORT"].set.tolist() if "set" in bp.columns else []
locus_p = gb["loci"]["binomial_P_one_sided"]
cont = bool(a_direct) and (bool(b_indep) or locus_p < 0.05 or (dirr.label == "DIRECTION_RESOLVED").any())
if pivot_a and pivot_b:
    decision = "STOP_CURRENT_HYPOTHESIS"
elif pivot_a or pivot_b:
    decision = "PIVOT"
elif retry_nt:
    decision = "RETRY"
elif cont:
    decision = "CONTINUE"
else:
    decision = "RETRY (ambiguous)"
out = {"decided_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "primary_decision": decision,
       "precedence": rules["precedence"],
       "evaluation": {"STOP_CURRENT_HYPOTHESIS": pivot_a and pivot_b,
                      "PIVOT": {"gate_a_beyond_noise": a_beyond, "gate_a_power_ok": a_power_ok, "gate_b_beyond_noise": b_beyond, "met": pivot_a or pivot_b},
                      "RETRY_IF_GATE_A_UNTESTABLE": retry_nt,
                      "CONTINUE": {"gate_a_direct_effect_sets": a_direct, "gate_b_independent_support_sets": b_indep,
                                   "gate_b_locus_binomial_P": locus_p, "met": cont}},
       "gate_a_summary": cal["summary"],
       "caveat": ("The qualifying Gate-A set (GO_0045202 synapse) has within-family P=0.018 (nominal; 6 sets tested; "
                  "Bonferroni 0.0083 not met) with simulated power 7.5% — the set-level CONTINUE is fragile. The robust "
                  "within-family result is locus-level: 109/146 lead alleles concordant (binomial P=1e-9), slope 0.69."),
       "chemistry_gate": "CLOSED (safety is never auto-cleared; no gene meets all five Sprint-4 criteria — see Sprint 5A report)",
       "note": "decide.py hard-codes the untestable branch; this script applies the same frozen rules literally"}
(R / "reports/sprint4/decision_gate_a_update.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print(json.dumps({k: out[k] for k in ("primary_decision", "evaluation")}, indent=1, default=str))
