#!/usr/bin/env python3
"""Self-check the Cognitive Brake Atlas against the contract, schemas and ontology.

This exists so that the claims agent:brakes makes about its own output are
reproducible by anyone, especially the red team. It runs offline and performs no
network access. It is not a substitute for ``graph/validate_graph.py`` (owned by
agent:ontology); it is the subset of checks this agent can run on its own lane, plus
the coverage arithmetic quoted in the handoff note.

Checks
------
S  every brakes record validates against its JSON Schema in ``schemas/``
O1 every ``(subject, predicate, object)`` triple is legal per ``ontology/edges.yaml``
O2 every ``claim_type`` is admissible for its predicate per ``ontology/edges.yaml``
O3 every ``SV:`` and ``PRIM:`` id used is declared by agent:ontology
X  every claim id, source id and dependency referenced resolves
V6 every registered source reached ``status: verified``
F  facet rules: owned facets present; assessed facets carry 0..4 levels and claim refs;
   ``not_assessed`` carries null levels; only owned facets are written
D  declared dossier depth is met (deep >= 4 claims, shallow >= 2)
A  every state-variable annotation carries claim refs

Usage
-----
    .venv/bin/python pipelines/brake_atlas/check_atlas.py
    .venv/bin/python pipelines/brake_atlas/check_atlas.py --coverage
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import warnings
from pathlib import Path

import yaml

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

AGENT = "agent:brakes"
OWNED_FACETS = {
    "mechanistic_causal_perturbation",
    "adult_onset_perturbation",
    "above_baseline_enhancement",
    "transfer_breadth",
    "dose_response_knowledge",
    "human_intervention_evidence",
}
SYMBOLS = [
    "GABRA5", "RGS14", "EIF2S1", "EIF2B_COMPLEX", "PTPN5", "HCN1", "KCNQ2",
    "KCNQ3", "RTN4R", "OTX2", "ADORA1", "HDAC2", "PDE4B", "GPR158",
]
HUMAN_RELEVANT = {"direct_human_interventional", "human_genetic", "human_observational", "nonhuman_primate"}


def load(path: str | Path):
    return yaml.safe_load(Path(REPO / path).read_text(encoding="utf-8"))


def schema_errors() -> list[str]:
    from jsonschema import Draft202012Validator, RefResolver

    sd = REPO / "schemas"
    if not sd.exists():
        return ["schemas/ not present yet; agent:ontology has not published them"]
    store = {}
    for p in sd.glob("*.json"):
        s = json.loads(p.read_text())
        if "$id" in s:
            store[s["$id"]] = s
        store[p.name] = s

    def run(name, docs, label):
        s = json.loads((sd / name).read_text())
        v = Draft202012Validator(s, resolver=RefResolver(base_uri=s.get("$id", ""), referrer=s, store=store))
        return [f"S {label}[{i}] {'/'.join(map(str, e.path))}: {e.message}" for i, d in enumerate(docs) for e in v.iter_errors(d)]

    claims = [c for p in sorted(glob.glob(str(REPO / "evidence/claims/brakes/*.yaml"))) for c in yaml.safe_load(Path(p).read_text())]
    targets = [d for d in (load(p) for p in sorted(glob.glob("targets/candidates/*.yaml"))) if d.get("lead_atlas") == "brakes"]
    out: list[str] = []
    out += run("source.schema.json", load("evidence/sources/brakes.yaml"), "sources")
    out += run("claim.schema.json", claims, "claims")
    out += run("target.schema.json", targets, "targets")
    out += run("assessment.schema.json", [load(p) for p in sorted(glob.glob("atlases/brakes/assessments/*.yaml"))], "assessments")
    out += run("intervention.schema.json", [load(p) for p in sorted(glob.glob("atlases/brakes/interventions/*.yaml"))], "interventions")
    out += run("state_variable_annotation.schema.json", load("atlases/brakes/state_variable_annotations.yaml"), "sv_annotations")
    return out


def ontology_errors() -> list[str]:
    try:
        from blueprint import ontology as O
    except Exception as exc:  # ontology not published yet
        return [f"ontology module unavailable: {type(exc).__name__}: {exc}"]
    ont = O.load()

    def types_of(nid: str):
        best = None
        for pfx in ont.prefixes:
            if nid.startswith(pfx + ":") and (best is None or len(pfx) > len(best)):
                best = pfx
        return list(ont.node_types_for_prefix(best)) if best else []

    out: list[str] = []
    declared_sv, declared_prim = set(), set()

    def harvest(o, acc, prefix):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "id" and isinstance(v, str) and v.startswith(prefix):
                    acc.add(v)
                harvest(v, acc, prefix)
        elif isinstance(o, list):
            for x in o:
                harvest(x, acc, prefix)

    for p in list((REPO / "state_model").glob("*.yaml")) + [REPO / "ontology/state_variables.yaml"]:
        if p.exists():
            harvest(yaml.safe_load(p.read_text()), declared_sv, "SV:")
    cp = REPO / "ontology/computational_primitives.yaml"
    if cp.exists():
        harvest(yaml.safe_load(cp.read_text()), declared_prim, "PRIM:")

    used_sv, used_prim = set(), set()
    for p in sorted(glob.glob(str(REPO / "evidence/claims/brakes/*.yaml"))):
        for c in yaml.safe_load(Path(p).read_text()):
            st, ot = types_of(c["subject"]), types_of(c["object"])
            if not any(ont.is_legal_triple(a, c["predicate"], b) for a in st for b in ot):
                why = ont.explain_triple(st[0] if st else "?", c["predicate"], ot[0] if ot else "?")
                out.append(f"O1 {c['claim_id']}: illegal triple {c['subject']} -{c['predicate']}-> {c['object']}: {why}")
            # An EMPTY allowed_claim_types means the relation places no claim-type
            # restriction (the evidence-layer relations ABOUT / REPORTS / QUALIFIES), not
            # that nothing is allowed. This mirrors the graph validator's own behaviour.
            allowed = set(ont.allowed_claim_types(c["predicate"]))
            # `preclinical_harm` (contract 4.1, resolution R13) is admitted by
            # graph/validate_graph.py wherever `clinical_harm` is, but ontology/edges.yaml
            # does not yet list it in any relation's allowed_claim_types. The authoritative
            # validator wins; this mirrors it so the local check does not contradict it.
            # Remove this once edges.yaml lists the new type.
            if "clinical_harm" in allowed:
                allowed.add("preclinical_harm")
            if allowed and c["claim_type"] not in allowed:
                out.append(f"O2 {c['claim_id']}: claim_type {c['claim_type']} not admissible for {c['predicate']}")
            if c["object"].startswith("SV:"):
                used_sv.add(c["object"])
    for p in sorted(glob.glob("targets/candidates/*.yaml")):
        d = load(p)
        if d.get("lead_atlas") != "brakes":
            continue
        for sv in d["control_point_hypothesis"]["state_variables"]:
            used_sv.add(sv["id"])
        used_prim |= set(d["control_point_hypothesis"]["computational_primitives"])
    for a in load("atlases/brakes/state_variable_annotations.yaml"):
        used_sv.add(a["state_variable"])
        if a.get("safety_coupling"):
            used_sv.add(a["safety_coupling"]["couples_to"])
    for sv in sorted(used_sv - declared_sv):
        out.append(f"O3 state variable {sv} is not declared by agent:ontology")
    for pr in sorted(used_prim - declared_prim):
        out.append(f"O3 primitive {pr} is not declared by agent:ontology")
    return out


def crossref_and_coverage() -> tuple[list[str], dict]:
    out: list[str] = []
    sources = {s["source_id"] for s in load("evidence/sources/brakes.yaml")}

    verif_path = REPO / "data/interim/source_verification/brakes.jsonl"
    verified = set()
    if verif_path.exists():
        for line in verif_path.read_text().splitlines():
            row = json.loads(line)
            if row.get("status") == "verified":
                verified.add(row["source_id"])
        for s in sorted(sources - verified):
            out.append(f"V6 source {s} did not reach status: verified")
    else:
        out.append("V6 no verification index; run scripts/fetch_source_metadata.py --agent brakes")

    claims: dict[str, dict] = {}
    per_target: dict[str, list[dict]] = {}
    for p in sorted(glob.glob(str(REPO / "evidence/claims/brakes/*.yaml"))):
        sym = Path(p).stem
        docs = yaml.safe_load(Path(p).read_text())
        per_target[sym] = docs
        for c in docs:
            claims[c["claim_id"]] = c
            for e in c["evidence"]:
                if e["source_id"] not in sources:
                    out.append(f"X {c['claim_id']} cites unregistered source {e['source_id']}")
    for c in claims.values():
        for d in c.get("dependencies") or []:
            if d not in claims:
                out.append(f"X {c['claim_id']} depends on unknown claim {d}")
        # V16c: a null edge needs a MEASURED, reported attempt behind it.
        if c["predicate"] == "NO_DETECTED_EFFECT_ON":
            ok = any(e.get("endpoint_measured") == "measured"
                     and e["evidence_role"] in ("null_result", "contradicts")
                     for e in c["evidence"])
            if not ok:
                out.append(f"V16c {c['claim_id']} uses NO_DETECTED_EFFECT_ON with no evidence "
                           f"item that is both endpoint_measured=measured and a null/contradicting "
                           f"role; it should be claim_type evidence_gap")
        if c["claim_type"] == "evidence_gap" and c["predicate"] == "NO_DETECTED_EFFECT_ON":
            out.append(f"V16c {c['claim_id']} is an evidence_gap but uses a null edge")
        # every evidence item must state whether the endpoint was measured at all
        for e in c["evidence"]:
            if e.get("endpoint_measured") not in ("measured", "not_measured_in_protocol",
                                                  "measured_but_not_reported", "unknown"):
                out.append(f"E {c['claim_id']} evidence item {e['source_id']} has "
                           f"endpoint_measured={e.get('endpoint_measured')!r}")

    coverage = {}
    for sym in SYMBOLS:
        docs = per_target.get(sym)
        if docs is None:
            out.append(f"D no claim file for {sym}")
            continue
        dossier = load(f"targets/candidates/{sym}.yaml")
        depth = dossier["dossier_depth"]
        need = 4 if depth == "deep" else 2
        if len(docs) < need:
            out.append(f"D {sym} declares depth {depth} but has only {len(docs)} claims (needs {need})")

        assessment = load(f"atlases/brakes/assessments/{sym}.yaml")
        names = {f["facet"] for f in assessment["facets"]}
        if names - OWNED_FACETS:
            out.append(f"F {sym} writes facets it does not own: {sorted(names - OWNED_FACETS)}")
        if OWNED_FACETS - names:
            out.append(f"F {sym} is missing owned facets: {sorted(OWNED_FACETS - names)}")
        graded = 0
        for f in assessment["facets"]:
            if f["assessment_status"] == "assessed":
                graded += 1
                for key in ("level", "counter_level"):
                    if f.get(key) not in (0, 1, 2, 3, 4):
                        out.append(f"F {sym}.{f['facet']}: {key}={f.get(key)!r} is not an ordinal 0..4")
                if (f.get("level") or 0) > 0 and not f.get("claim_refs"):
                    out.append(f"F {sym}.{f['facet']}: level>0 with no claim_refs")
                if (f.get("counter_level") or 0) > 0 and not f.get("counter_claim_refs"):
                    out.append(f"F {sym}.{f['facet']}: counter_level>0 with no counter_claim_refs")
            else:
                if f.get("level") is not None or f.get("counter_level") is not None:
                    out.append(f"F {sym}.{f['facet']}: not_assessed must carry null levels")
            for ref in (f.get("claim_refs") or []) + (f.get("counter_claim_refs") or []):
                if ref not in claims:
                    out.append(f"X {sym}.{f['facet']} references unknown claim {ref}")
                elif claims[ref]["claim_type"] == "evidence_gap":
                    # contract 4.1 / R5: graph-inert, never counter-evidence, counts as a
                    # coverage gap instead. It must be named in prose, not cited.
                    out.append(f"G {sym}.{f['facet']} cites evidence_gap claim {ref}; an "
                               f"absence of measurement is neither support nor refutation")

        coverage[sym] = {
            "depth": depth,
            "claims": len(docs),
            "contradicting_evidence_items": sum(1 for c in docs for e in c["evidence"] if e["evidence_role"] == "contradicts"),
            "null_result_evidence_items": sum(1 for c in docs for e in c["evidence"] if e["evidence_role"] == "null_result"),
            "no_detected_effect_claims": sum(1 for c in docs if c["predicate"] == "NO_DETECTED_EFFECT_ON"),
            "evidence_gap_claims": sum(1 for c in docs if c["claim_type"] == "evidence_gap"),
            "null_or_harm_claims": sum(1 for c in docs if c["claim_type"] in ("clinical_null", "clinical_harm", "preclinical_harm")),
            "human_relevant_claim": any(c["translation"]["human_relevance"] in HUMAN_RELEVANT for c in docs),
            "facets_graded": graded,
            "facets_not_assessed": [f["facet"] for f in assessment["facets"] if f["assessment_status"] != "assessed"],
        }

    for a in load("atlases/brakes/state_variable_annotations.yaml"):
        if not a.get("claim_refs"):
            out.append(f"A annotation {a['state_variable']} carries no claim refs")
        for ref in a.get("claim_refs") or []:
            if ref not in claims:
                out.append(f"X annotation {a['state_variable']} references unknown claim {ref}")
    return out, coverage


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coverage", action="store_true", help="also print the coverage table")
    args = ap.parse_args(argv)

    problems = schema_errors() + ontology_errors()
    xrefs, coverage = crossref_and_coverage()
    problems += xrefs

    for p in problems:
        print(f"FAIL {p}")
    if args.coverage:
        print()
        w = max(len(s) for s in coverage) if coverage else 8
        print(f"| {'target'.ljust(w)} | depth   | claims | contra | null_res | null/harm | no_effect | human | facets |")
        print(f"|{'-' * (w + 2)}|---------|--------|--------|----------|-----------|-----------|-------|--------|")
        for sym in sorted(coverage, key=lambda s: (coverage[s]['depth'] != 'deep', s)):
            c = coverage[sym]
            print(f"| {sym.ljust(w)} | {c['depth'].ljust(7)} | {c['claims']:>6} | {c['contradicting_evidence_items']:>6} "
                  f"| {c['null_result_evidence_items']:>8} | {c['null_or_harm_claims']:>9} | {c['no_detected_effect_claims']:>9} "
                  f"| {'yes' if c['human_relevant_claim'] else 'no':<5} | {c['facets_graded']}/6    |")
        print()
        print("totals:",
              f"claims={sum(c['claims'] for c in coverage.values())}",
              f"contradicting_evidence_items={sum(c['contradicting_evidence_items'] for c in coverage.values())}",
              f"null_result_evidence_items={sum(c['null_result_evidence_items'] for c in coverage.values())}",
              f"NO_DETECTED_EFFECT_ON_claims={sum(c['no_detected_effect_claims'] for c in coverage.values())}",
              f"evidence_gap_claims={sum(c['evidence_gap_claims'] for c in coverage.values())}",
              f"null_or_harm_claims={sum(c['null_or_harm_claims'] for c in coverage.values())}",
              f"targets_with_human_claim={sum(1 for c in coverage.values() if c['human_relevant_claim'])}/{len(coverage)}",
              f"facets_graded={sum(c['facets_graded'] for c in coverage.values())}/{6 * len(coverage)}")

    print()
    print(f"{'PASS' if not problems else 'FAIL'}: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
