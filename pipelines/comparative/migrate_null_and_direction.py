#!/usr/bin/env python3
"""Apply the two migrations approved in docs/blackboard/RESOLUTIONS.md R9 and R10.

Why this is a script and not a hand edit
----------------------------------------
Both migrations were approved before the ontology and schema support existed. Applying
them early would take `evidence/claims/comparative/` from zero validator violations to
at least three, because:

* `schemas/claim.schema.json` sets `additionalProperties: false` at claim level, so
  writing `negated_relation` or `direction_context` before they are declared is a hard
  V1 schema failure, not a forward-compatible annotation; and
* `NO_DETECTED_EFFECT_ON`'s domain does not yet include `BrainRegion`, so repointing
  `CLM:comparative:SELF_REGULATION:002` at it is a V3 illegal-triple failure.

Writing fields the contract has not declared is also exactly the improvisation
`docs/BLACKBOARD_PROTOCOL.md` §2.3 forbids. So this script encodes the migrations,
refuses to run until it can prove the support has landed, and applies them in one step
when it has. The intent is that nobody has to remember the decision — they only have to
run this.

    python pipelines/comparative/migrate_null_and_direction.py            # check + apply
    python pipelines/comparative/migrate_null_and_direction.py --dry-run  # report only

Exit status: 0 when the migrations are applied or already applied, 2 when the required
ontology/schema support is still missing (with a per-precondition report), 1 on an
unexpected state that needs a human.

R9 — V16b-sym: the null relation must be expressible wherever the positive is
-----------------------------------------------------------------------------
`CLM:comparative:SELF_REGULATION:002` becomes
`REGION:brain -NO_DETECTED_EFFECT_ON-> PRIM:distractor_suppression` with
`negated_relation: CONSTRAINS`. It is a performed cross-clade test in which absolute
brain volume predicted nothing about detour-task performance: three corvid species
matched published great-ape scores with brains reported as 26 to 94 times smaller. It
already carries `effect_direction: no_change` and `evidence_role: contradicts`, and its
`claim_type: association` is permitted by the relation.

THE OTHER THREE CANDIDATES WERE RE-CHECKED AS R9 ASKED, AND STILL DO NOT MIGRATE.
Eligibility under the widened domain is necessary but not sufficient: V16b requires a
MEASURED ABSENCE, and these three report measured presences.

* `CLM:comparative:NEURON_SCALING:003` — the elephant cortex holds about a third of the
  human cortical neuron count. That is a difference detected, not an effect absent.
* `CLM:comparative:NEURON_SCALING:005` — the isotropic fractionator and stereology
  disagree roughly fourfold on the same species. A measurement conflict, not a null.
* `CLM:comparative:SELF_REGULATION:003` — reinforcing a fixed motor response improved
  detour scores. A positive effect, and the claim's whole point.

`CLM:comparative:CEPHALOPOD_GENOME:001` is eligible today and is deliberately NOT
migrated; R9 upholds that refusal. Nobody tested whether protocadherin expansion affects
structural plasticity rate, so a null edge there would manufacture a finding out of a
gap.

R10 — `state_dependent` means a known and specified dependency
--------------------------------------------------------------
`CLM:comparative:HCN1:004` becomes `direction: state_dependent` with
`direction_context` naming the dependency: h-current's human-versus-rodent difference
reverses sign between supragranular layers (stronger in human) and layer 5 (HCN
conductance below the mammalian allometric prediction). `unclear` is now reserved for
genuine ignorance, and this claim is not ignorant — it is characterised.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = REPO_ROOT / "evidence" / "claims" / "comparative"
EDGES = REPO_ROOT / "ontology" / "edges.yaml"
CLAIM_SCHEMA = REPO_ROOT / "schemas" / "claim.schema.json"
VOCAB = REPO_ROOT / "ontology" / "vocabularies.yaml"

NULL_RELATION = "NO_DETECTED_EFFECT_ON"
DIRECTION_CONTEXT = (
    "cortical layer: the human-versus-rodent difference in h-current reverses sign "
    "between supragranular layers, where h-channel-dependent membrane properties are "
    "stronger in human than mouse, and layer 5, where human HCN conductance falls below "
    "the mammalian allometric prediction. The dependency is on laminar position, not on "
    "physiological state."
)


# ------------------------------------------------------------------ preconditions
def relation(name: str) -> dict | None:
    doc = yaml.safe_load(EDGES.read_text(encoding="utf-8"))
    for value in doc.values():
        if isinstance(value, list) and value and isinstance(value[0], dict) and "name" in value[0]:
            for edge in value:
                if edge.get("name") == name:
                    return edge
    return None


def preconditions() -> list[tuple[str, bool, str]]:
    """Each precondition as (label, satisfied, detail)."""
    checks: list[tuple[str, bool, str]] = []

    rel = relation(NULL_RELATION)
    if rel is None:
        checks.append((f"{NULL_RELATION} exists in ontology/edges.yaml", False, "relation not found"))
        domain_ok = range_ok = False
    else:
        domain = set(rel.get("domain") or [])
        rng = set(rel.get("range") or [])
        domain_ok = "BrainRegion" in domain
        range_ok = "ComputationalPrimitive" in rng
        checks.append((f"{NULL_RELATION} exists", True, "found"))
        checks.append((
            f"{NULL_RELATION} domain includes BrainRegion (R9 / V16b-sym)",
            domain_ok,
            "present" if domain_ok else f"domain is {sorted(domain)}",
        ))
        checks.append((
            f"{NULL_RELATION} range includes ComputationalPrimitive",
            range_ok,
            "present" if range_ok else f"range is {sorted(rng)}",
        ))

    schema = json.loads(CLAIM_SCHEMA.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    negated_ok = "negated_relation" in props
    dircx_ok = "direction_context" in props
    checks.append((
        "claim.schema.json declares negated_relation (R9)",
        negated_ok,
        "declared" if negated_ok else "absent; additionalProperties is "
        f"{schema.get('additionalProperties')}, so writing it now is a hard V1 failure",
    ))
    checks.append((
        "claim.schema.json declares direction_context (R10)",
        dircx_ok,
        "declared" if dircx_ok else "absent; same hard-failure reason as above",
    ))

    if rel is not None:
        allowed = set(rel.get("allowed_claim_types") or [])
        ok = "association" in allowed
        checks.append((
            f"{NULL_RELATION} permits claim_type association",
            ok,
            "permitted" if ok else f"allowed_claim_types is {sorted(allowed)}",
        ))
    return checks


def already_applied(claims_text: dict[str, str]) -> bool:
    return (
        f"predicate: {NULL_RELATION}" in claims_text.get("SELF_REGULATION.yaml", "")
        and "direction: state_dependent" in claims_text.get("HCN1.yaml", "")
    )


# ---------------------------------------------------------------------- migration
def migrate_self_regulation(text: str) -> str:
    """R9: repoint SELF_REGULATION:002 at the null relation."""
    old = """  subject: REGION:brain
  predicate: CONSTRAINS
  object: PRIM:distractor_suppression
  claim_type: association
  direction: unclear"""
    new = f"""  subject: REGION:brain
  predicate: {NULL_RELATION}
  negated_relation: CONSTRAINS
  object: PRIM:distractor_suppression
  claim_type: association
  direction: no_change"""
    # Only the SECOND claim in the file carries `direction: unclear` on this triple;
    # :001 has `direction: increases` and must not be touched.
    if old not in text:
        raise SystemExit(
            "SELF_REGULATION:002 does not have the expected shape; migrate by hand and "
            "record why (the file may have been edited since 2026-09-17)."
        )
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly 1 match for the SELF_REGULATION:002 triple, found {text.count(old)}")
    text = text.replace(old, new, 1)

    blocked_note = re.search(
        r'\n    - "WOULD BE A NO_DETECTED_EFFECT_ON EDGE IF THE ONTOLOGY ALLOWED IT\..*?comparative-002\.yaml\."',
        text,
        re.S,
    )
    migrated_note = (
        '\n    - "MIGRATED TO NO_DETECTED_EFFECT_ON on the landing of V16b-sym '
        "(docs/blackboard/RESOLUTIONS.md R9), with negated_relation: CONSTRAINS. This claim "
        "previously compiled as a CONSTRAINS edge with direction: unclear, so a traversal that "
        "ignored `direction` could read a deflationary result as SUPPORT for "
        "'bigger brain implies better inhibition'. It is now a null edge, which no traversal may "
        'count as support. `direction` is `no_change`, matching the evidence item."'
    )
    if blocked_note:
        text = text[: blocked_note.start()] + migrated_note + text[blocked_note.end() :]
    else:
        raise SystemExit("could not find the blocked-migration note to replace in SELF_REGULATION.yaml")
    return text


def migrate_hcn1(text: str) -> str:
    """R10: state_dependent with a named context for HCN1:004."""
    old = """  subject: PROT:HCN1
  predicate: MODULATES
  object: CELL:cortical_pyramidal_neuron
  claim_type: theoretical_construct
  direction: unclear"""
    new = f"""  subject: PROT:HCN1
  predicate: MODULATES
  object: CELL:cortical_pyramidal_neuron
  claim_type: theoretical_construct
  direction: state_dependent
  direction_context: >-
    {DIRECTION_CONTEXT}"""
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly 1 match for the HCN1:004 triple, found {text.count(old)}")
    text = text.replace(old, new, 1)

    rejected = re.search(
        r'\n    - "`direction: state_dependent` was considered and rejected\..*?no single direction is supported\."',
        text,
        re.S,
    )
    accepted = (
        '\n    - "`direction` CHANGED FROM `unclear` TO `state_dependent` on the landing of the '
        "R10 vocabulary amendment (docs/blackboard/RESOLUTIONS.md R10). Under the original wording "
        "`state_dependent` meant a dependency on physiological state, so a laminar dependency did "
        "not qualify and `unclear` was the honest value. R10 widened it to a KNOWN AND SPECIFIED "
        "dependency, including cortical layer, and added the required `direction_context`. The "
        'claim is characterised, not ignorant, and now records that."'
    )
    if rejected:
        text = text[: rejected.start()] + accepted + text[rejected.end() :]
    else:
        raise SystemExit("could not find the state_dependent rejection note to replace in HCN1.yaml")
    return text


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report readiness and planned edits, change nothing")
    args = parser.parse_args(argv)

    texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(CLAIMS_DIR.glob("*.yaml"))}
    if already_applied(texts):
        print("both migrations are already applied; nothing to do.")
        return 0

    checks = preconditions()
    print("preconditions (docs/blackboard/RESOLUTIONS.md R9, R10):")
    for label, ok, detail in checks:
        print(f"  [{'ok  ' if ok else 'WAIT'}] {label}\n         {detail}")
    missing = [label for label, ok, _ in checks if not ok]

    if missing:
        print(
            f"\n{len(missing)} precondition(s) not yet met — agent:ontology has not landed the "
            "R9/R10 support.\nNOT MIGRATING. Applying these edits now would fail V1 (undeclared "
            "properties under\n`additionalProperties: false`) and V3 (BrainRegion outside the null "
            "relation's domain),\ntaking agent:comparative from 0 validator violations to at least "
            "3, and would be the\nschema improvisation BLACKBOARD_PROTOCOL §2.3 forbids. Re-run "
            "this script once the\nontology and schema land; it is idempotent.",
            file=sys.stderr,
        )
        return 2

    print("\nall preconditions met; applying R9 and R10 migrations.")
    planned = {
        "SELF_REGULATION.yaml": migrate_self_regulation(texts["SELF_REGULATION.yaml"]),
        "HCN1.yaml": migrate_hcn1(texts["HCN1.yaml"]),
    }
    if args.dry_run:
        print("--dry-run: both migrations applied cleanly in memory; no file written.")
        return 0
    for name, new_text in planned.items():
        (CLAIMS_DIR / name).write_text(new_text, encoding="utf-8")
        print(f"  migrated {name}")
    print(
        "\nDone. Now re-run, in this order:\n"
        "  .venv/bin/python scripts/fetch_source_metadata.py --agent comparative\n"
        "  .venv/bin/python graph/validate_graph.py --strict\n"
        "  .venv/bin/python pipelines/comparative/check_phylogenetic_cap.py\n"
        "and update atlases/comparative/README.md §6.7 and the handoff, which both still "
        "describe SELF_REGULATION:002 as blocked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
