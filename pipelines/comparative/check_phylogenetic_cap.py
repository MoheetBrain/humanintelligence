#!/usr/bin/env python3
"""Enforce the comparative atlas's phylogenetic-control cap, polarity-aware.

The rule
--------
`atlases/comparative/phylogenetic_controls.md` commits this atlas to one hard cap:

    A claim whose proposition is a BETWEEN-SPECIES comparison and which reports
    `context.phylogenetic_control` of `none` or `not_reported` may not be graded
    above ordinal level 2.

Species are not independent observations. Closely related species resemble each other
because of descent, so an uncontrolled cross-species regression can be driven entirely
by one clade, and adding more species from that clade makes the result look stronger
while adding no independent information. Without a cap, "28 species" reads as better
evidence than "4 species", when the 28-species study may carry fewer independent
contrasts.

POLARITY (contract §5.4)
------------------------
A cap imposed because the evidence is methodologically weak applies **only in the
direction that favours the target**:

* **Normal-polarity facet** (e.g. `cross_species_convergence`) → cap `level`. Weak
  method cannot establish strong support. `counter_level` is NOT capped: weak method
  is no reason to discount evidence against the target.
* **Inverse-polarity facet** (`human_lineage_divergence_risk`,
  `safety_liability_burden`, `developmental_confound_risk`) → cap `counter_level`,
  **never** `level`. Weak method cannot establish the *absence* of a risk.

This distinction exists because of a defect this checker's first version had. It applied
the cap uniformly to `level` on every facet, which held
`atlases/comparative/assessments/HCN1.yaml`'s `human_lineage_divergence_risk` at 2 when
the evidence read as 3 — converting a methodological weakness into the conclusion that
HCN1 is *more* translatable than its evidence supports, because that facet feeds
dimension D6 inversely. `agent:comparative` escalated it; the contract was amended;
§5.4 is the fix. Run `--legacy-rule` to see the old behaviour fail against the corrected
records.

`models/ranking/facet_rubric_v0_1.yaml` is the SOURCE OF TRUTH for facet polarity once
`agent:integration` publishes it. Until then `FACET_POLARITY` below mirrors the
inverse-polarity list in contract §5.4 and is read from that file automatically if it
appears, so this checker stops being the authority the moment a better one exists.

The cap is deliberately NOT applied to single-species claims. A claim with
`context.species_count == 1` makes no between-species comparison, so shared ancestry is
not a confound for it and there is nothing for a phylogenetic model to control. The
worked example is `CLM:comparative:SELF_REGULATION:003`: a randomised training
experiment in one bird species, plus a within-species trial-order reanalysis, showing
that detour-task scores index motor response learning. That claim is graded 3 on
converging designs, and the cap correctly does not touch it — it is evidence about a
measurement instrument, not about a species difference. A MISSING `species_count` (an
unenumerated multi-species study, where the key is omitted because the schema requires an
integer and none could be verified) IS capped, because absence of a count is not evidence
of a single species.

This script exists so that the rule is executable rather than rhetorical, and so the
red team can re-derive it without trusting this agent's prose. It reads only files
owned by agent:comparative and writes nothing.

Usage
-----
    python pipelines/comparative/check_phylogenetic_cap.py
    python pipelines/comparative/check_phylogenetic_cap.py --verbose
    python pipelines/comparative/check_phylogenetic_cap.py --legacy-rule

Exit status is 0 when every claim and facet respects the cap, 1 otherwise.
``--legacy-rule`` is expected to exit 1: it demonstrates that the pre-§5.4 behaviour is
now a violation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = REPO_ROOT / "evidence" / "claims" / "comparative"
ASSESSMENTS_DIR = REPO_ROOT / "atlases" / "comparative" / "assessments"
RUBRIC_PATH = REPO_ROOT / "models" / "ranking" / "facet_rubric_v0_1.yaml"

CAP = 2

# Facet polarity per contract §5.4. `inverse` means a higher level is WORSE for the
# target. Overridden by models/ranking/facet_rubric_v0_1.yaml when that file exists.
FACET_POLARITY: dict[str, str] = {
    "human_genetic_association": "normal",
    "causal_gene_attribution": "normal",
    "human_phenotype_specificity": "normal",
    "adult_expression_and_timing": "normal",
    "mechanistic_causal_perturbation": "normal",
    "adult_onset_perturbation": "normal",
    "above_baseline_enhancement": "normal",
    "transfer_breadth": "normal",
    "dose_response_knowledge": "normal",
    "human_intervention_evidence": "normal",
    "cross_species_convergence": "normal",
    "tractability": "normal",
    "human_lineage_divergence_risk": "inverse",
    "safety_liability_burden": "inverse",
    "developmental_confound_risk": "inverse",
}

# Facets this agent owns and therefore checks. Others are validated for polarity
# bookkeeping only if they appear in files this agent owns (they should not).
OWNED_FACETS = {"cross_species_convergence", "human_lineage_divergence_risk"}

# Vocabulary is schemas/claim.schema.json (context.phylogenetic_control), which is
# authoritative. agent:ontology added the field with this enum in response to
# docs/blackboard/schema_change_requests/comparative-001.yaml.
VALID_CONTROLS = {
    "none",
    "outgroup_comparison",
    "sister_taxon_comparison",
    "phylogenetic_comparative_model",
    "ancestral_state_reconstruction",
    "other",
    "not_reported",
}

# `not_reported` is capped alongside `none`. Not knowing whether ancestry was modelled
# cannot count for more than knowing it was not: an unverified control is not a control.
# The two values are kept distinct because conflating "the authors report an uncontrolled
# analysis" with "the retrieved text does not say" would be false precision (contract P3).
UNCONTROLLED = {"none", "not_reported"}


def load_polarity() -> tuple[dict[str, str], str]:
    """Facet polarity, preferring the ranking rubric once agent:integration writes it."""
    if RUBRIC_PATH.exists():
        try:
            doc = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return dict(FACET_POLARITY), f"{RUBRIC_PATH.name} unparseable; using contract §5.4 table"
        found: dict[str, str] = {}
        facets = doc.get("facets")
        if isinstance(facets, dict):
            items = facets.items()
        elif isinstance(facets, list):
            items = [(f.get("facet") or f.get("name"), f) for f in facets if isinstance(f, dict)]
        else:
            items = []
        for name, body in items:
            if not name or not isinstance(body, dict):
                continue
            pol = body.get("polarity")
            if pol in {"normal", "inverse"}:
                found[str(name)] = pol
        if found:
            merged = dict(FACET_POLARITY)
            merged.update(found)
            return merged, f"{RUBRIC_PATH.relative_to(REPO_ROOT)} ({len(found)} facets)"
    return dict(FACET_POLARITY), "contract §5.4 table (rubric not published yet)"


def load_claims() -> dict[str, dict]:
    """All comparative claims, keyed by claim_id."""
    claims: dict[str, dict] = {}
    for path in sorted(CLAIMS_DIR.glob("*.yaml")):
        for claim in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            claim["_file"] = path.name
            claims[claim["claim_id"]] = claim
    return claims


def is_between_species(claim: dict) -> bool:
    """True when the claim's proposition compares two or more species.

    A missing `species_count` counts as between-species: an unenumerated multi-species
    study must not escape the cap by omitting its own species count.
    """
    count = claim.get("context", {}).get("species_count")
    if count is None:
        return True
    return int(count) >= 2


def capped_field(facet_name: str, polarity: dict[str, str]) -> str:
    """Which field the methodological cap constrains for this facet (contract §5.4)."""
    return "counter_level" if polarity.get(facet_name) == "inverse" else "level"


def check(*, verbose: bool = False, legacy: bool = False) -> list[str]:
    """Return a list of violations. ``legacy=True`` reinstates the pre-§5.4 behaviour."""
    claims = load_claims()
    polarity, _ = load_polarity()
    problems: list[str] = []

    # ---- claim-level cap. Claims have no polarity, so this is unchanged by §5.4. ----
    for claim_id, claim in sorted(claims.items()):
        control = claim.get("context", {}).get("phylogenetic_control")
        level = claim.get("uncertainty", {}).get("level")
        if control not in VALID_CONTROLS:
            problems.append(f"{claim_id}: phylogenetic_control {control!r} is not a recognised value")
            continue
        if not claim.get("context", {}).get("phylogenetic_control_basis"):
            problems.append(f"{claim_id}: phylogenetic_control has no phylogenetic_control_basis")
        if control in UNCONTROLLED and not (claim.get("causal_attribution", {}).get("alternative_explanations")):
            problems.append(
                f"{claim_id}: phylogenetic_control {control} requires at least one stated "
                f"alternative explanation (shared ancestry, allometry, sampling bias)"
            )
        capped = control in UNCONTROLLED and is_between_species(claim)
        if capped and isinstance(level, int) and level > CAP:
            problems.append(
                f"{claim_id}: level {level} exceeds the cap of {CAP} for a between-species "
                f"claim with phylogenetic_control: {control}"
            )
        if verbose:
            mark = "CAPPED" if capped else "exempt"
            n = claim.get("context", {}).get("species_count")
            print(f"  {claim_id:<48} control={control:<20} n_species={str(n):<5} level={level} [{mark}]")

    # ---- facet-level cap, polarity-aware ----
    for path in sorted(ASSESSMENTS_DIR.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for facet in doc.get("facets", []) or []:
            name = facet.get("facet")
            if name not in OWNED_FACETS:
                continue
            if name not in polarity:
                problems.append(f"{path.name} facet {name}: no polarity known; cannot apply §5.4 safely")
                continue
            field = "level" if legacy else capped_field(name, polarity)
            refs_key = "claim_refs" if field == "level" else "counter_claim_refs"
            value = facet.get(field)
            refs = facet.get(refs_key) or []
            if not isinstance(value, int) or value <= CAP:
                continue
            uncontrolled = [
                r
                for r in refs
                if r in claims
                and claims[r].get("context", {}).get("phylogenetic_control") in UNCONTROLLED
                and is_between_species(claims[r])
            ]
            if refs and uncontrolled and len(uncontrolled) == len(refs):
                problems.append(
                    f"{path.name} facet {name}: {field} {value} exceeds the cap of {CAP}; "
                    f"every supporting claim is uncontrolled ({', '.join(uncontrolled)})"
                )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="print the cap status of every claim and facet")
    parser.add_argument(
        "--legacy-rule",
        action="store_true",
        help="reinstate the pre-contract-§5.4 behaviour (cap `level` on every facet) to "
        "demonstrate that it is now a violation; expected to exit 1",
    )
    args = parser.parse_args(argv)

    polarity, polarity_source = load_polarity()
    if args.legacy_rule:
        print("RUNNING THE PRE-§5.4 RULE: cap applied to `level` on every facet regardless of polarity.")
        print("This is the behaviour contract §5.4 forbids. It is expected to fail.\n")
    if args.verbose:
        print(f"facet polarity source: {polarity_source}")
        print("phylogenetic-control cap status per claim:")

    problems = check(verbose=args.verbose, legacy=args.legacy_rule)

    if args.verbose:
        print("\ncap target per graded facet (contract §5.4):")
        for path in sorted(ASSESSMENTS_DIR.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for facet in doc.get("facets", []) or []:
                name = facet.get("facet")
                if name not in OWNED_FACETS or facet.get("assessment_status") != "assessed":
                    continue
                pol = polarity.get(name, "?")
                field = "level" if args.legacy_rule else capped_field(name, polarity)
                print(
                    f"  {doc['target_id']:<14} {name:<32} polarity={pol:<7} "
                    f"cap constrains {field:<13} level={facet.get('level')} counter_level={facet.get('counter_level')}"
                )

    claims = load_claims()
    capped = sum(1 for c in claims.values() if c["context"]["phylogenetic_control"] in UNCONTROLLED and is_between_species(c))
    controlled = sum(1 for c in claims.values() if c["context"]["phylogenetic_control"] not in UNCONTROLLED)
    print(
        f"\n{len(claims)} comparative claims: {controlled} report a phylogenetic control, "
        f"{capped} are between-species with none/not_reported and are capped at level {CAP}."
    )
    if problems:
        print(f"\n{len(problems)} cap violation(s):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        if args.legacy_rule:
            print(
                "\nThe violation(s) above are the point: under the pre-§5.4 rule the corrected\n"
                "records fail, because that rule capped a RISK facet and so understated the risk.",
                file=sys.stderr,
            )
        return 1
    print("cap respected by every claim and facet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
