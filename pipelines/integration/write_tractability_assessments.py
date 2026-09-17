#!/usr/bin/env python3
"""Write `tractability` facet assessments from the pinned Open Targets release.

Offline. Reads only ``data/interim/opentargets_tractability.jsonl`` — itself rebuilt
from the immutable snapshots under ``data/raw/opentargets/`` — and writes one
assessment per target to ``atlases/integration/assessments/{SYMBOL}.yaml``.

Why this is a generator and not hand-authored
---------------------------------------------
The grade is a deterministic reading of a pinned database release against the rubric's
level criteria. Hand-copying 31 grades would introduce transcription error and would
let the assessments drift from the release they claim to rest on. Generating them means
the audit trail is complete: snapshot -> derived index -> assessment, each step
rebuildable with no network.

Legality (R7, ``docs/blackboard/RESOLUTIONS.md``; contract §2, §5.2)
-------------------------------------------------------------------
* ``atlases/integration/assessments/{SYMBOL}.yaml`` is a legal location for a
  non-domain agent that owns facets.
* ``tractability`` is the only facet flagged ``database_gradable: true`` in
  ``models/ranking/facet_rubric_v0_1.yaml``, so it may cite ``source_refs`` in place of
  ``claim_refs`` while carrying ``evidence_basis: database_release``.
* The rationale names the exact ``(modality, label)`` buckets that produced the grade
  and the data version, as §5.2 requires.

This agent writes ``tractability`` and nothing else. Every other facet for these
targets belongs to another agent and is absent by design (validator rule V11).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from blueprint.ranking.rubric import load_model_spec  # noqa: E402

TRACTABILITY_INDEX = REPO_ROOT / "data" / "interim" / "opentargets_tractability.jsonl"
ASSESSMENT_DIR = REPO_ROOT / "atlases" / "integration" / "assessments"
FACET = "tractability"

#: Seed symbols are the ranking cohort. A complex's member genes are annotated
#: individually by Open Targets and are NOT seed targets, so they are skipped: writing
#: an assessment for a symbol absent from the registry would create a record nothing
#: ranks and nothing audits.
SEED_REGISTRY = REPO_ROOT / "targets" / "seed_registry.yaml"


def _seed_symbols() -> set[str]:
    import yaml

    registry = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8")) or {}
    return {
        str(entry.get("symbol") or str(entry.get("target_id", "")).removeprefix("TGT:"))
        for entry in registry.get("targets") or []
    }


def _load_rows() -> list[dict[str, Any]]:
    if not TRACTABILITY_INDEX.is_file():
        raise SystemExit(
            f"{TRACTABILITY_INDEX} does not exist.\n"
            "Run `make fetch-tractability` (network) or "
            "`pipelines/integration/fetch_target_annotations.py --offline` first."
        )
    return [
        json.loads(line)
        for line in TRACTABILITY_INDEX.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rationale(row: dict[str, Any]) -> str:
    """The §5.2-required rationale: exact buckets, data version, and what they license."""
    clinical = row.get("clinical_buckets") or []
    tools = row.get("tool_buckets") or []
    predicted = row.get("predicted_buckets") or []
    probes = int(row.get("n_high_quality_probes") or 0)
    probe_ids = row.get("high_quality_probe_ids") or []
    level = int(row["suggested_level"])

    parts = [
        f"Graded from Open Targets Platform data version {row['data_version']} "
        f"(source {row['source_id']}, snapshot {row['snapshot']}), api version "
        f"{row.get('api_version')}, for Ensembl gene {row.get('ensembl_gene_id')}."
    ]
    if clinical:
        parts.append(f"Clinical or approved buckets positive: {', '.join(clinical)}.")
    if tools:
        parts.append(f"Characterised tool buckets positive: {', '.join(tools)}.")
    if predicted:
        parts.append(
            f"Prediction, family-membership or localisation buckets positive: "
            f"{', '.join(predicted)}."
        )
    if not (clinical or tools or predicted):
        parts.append("No tractability bucket is positive in this release.")
    parts.append(
        f"High-quality chemical probes: {probes}"
        + (f" ({', '.join(probe_ids)})." if probe_ids else ".")
    )

    if level == 3:
        approved = [b for b in clinical if "Approved Drug" in b]
        parts.append(
            "Level 3 under the rubric: clinical precedence for this target or a close "
            "family member. Level 4 is NOT reachable from this source, which reports "
            "neither a published family selectivity profile nor documented human CNS "
            "exposure."
        )
        parts.append(
            "CAVEAT, READ THIS BEFORE READING ANY D5 OR D6 SCORE FOR THIS TARGET: "
            + (
                f"the {', '.join(approved)} bucket means A MOLECULE TOUCHES THIS PROTEIN "
                "FAMILY. "
                if approved
                else "the clinical bucket above means a molecule has reached humans against "
                "this target or a close family member. "
            )
            + "It establishes NOTHING about direction (whether the molecule agonises, "
            "antagonises or modulates), NOTHING about selectivity within the family, and "
            "NOTHING about whether the available direction is the direction this "
            "project's control-point hypothesis requires. A level-3 tractability grade is "
            "therefore compatible with there being no usable tool for the modulation "
            "actually wanted. `tractability` carries weight 0.25 in D6 (human "
            "translation) and 0.15 in D5 (safe controllable window), so this caveat is "
            "load-bearing for both dimensions."
        )
    elif level == 2:
        parts.append(
            "Level 2 under the rubric: a characterised chemical or structural tool "
            "exists, with no clinical precedent in this release."
        )
    elif level == 1:
        parts.append(
            "Level 1 under the rubric: prediction or family membership only. Being a "
            "member of a druggable family is a PRIOR, not a tool, and the antibody and "
            "PROTAC buckets here are localisation and half-life predictions rather than "
            "characterised modulators."
        )
    else:
        parts.append(
            "Level 0 under the rubric: searched the pinned release and found no positive "
            "tractability bucket and no chemical probe."
        )
    parts.append(
        "Modality maturity only. A tractability bucket says a means of modulation "
        "exists; it is never evidence that engaging the target does anything "
        "(contract rule V16)."
    )
    return " ".join(parts)


#: The tractability bucket universe this release returns, named so that a `level: 0`
#: says "this release has no signal for this target" rather than "nobody looked".
_BUCKET_UNIVERSE = (
    "28 tractability buckets across four modalities — SM (small molecule: Approved Drug, "
    "Advanced Clinical, Phase 1 Clinical, High-Quality Ligand, Structure with Ligand, "
    "High-Quality Pocket, Med-Quality Pocket, Druggable Family), AB (antibody: UniProt "
    "loc high/med conf, GO CC high/med conf, UniProt SigP or TMHMM, Human Protein Atlas "
    "loc), PR (PROTAC: Literature, Small Molecule Binder, Database/UniProt "
    "Ubiquitination, Half-life Data) and OC (other clinical: Approved Drug, Advanced "
    "Clinical) — plus the `chemicalProbes` list filtered to `isHighQuality: true`"
)


def _search_basis(row: dict[str, Any]) -> str:
    """What was searched, at what scope, and what would have counted as a hit (R11).

    Required by the schema whenever ``level: 0``, and written here for every level
    because for a database-derived grade it is genuinely informative rather than
    boilerplate: it names the release, the exact bucket universe inspected, and the
    hit criterion, so a zero is a statement about the release and not about the effort.
    """
    level = int(row["suggested_level"])
    scope = (
        f"Scope: the complete tractability annotation for Ensembl gene "
        f"{row.get('ensembl_gene_id')} in Open Targets Platform data version "
        f"{row['data_version']} (api {row.get('api_version')}), retrieved by the pinned "
        f"GraphQL operation TargetAnnotations and snapshotted immutably at "
        f"{row['snapshot']}. Searched: {_BUCKET_UNIVERSE}."
    )
    hit = (
        "What would have counted as a hit, in rubric order: any of SM/OC Approved Drug, "
        "Advanced Clinical or Phase 1 Clinical, or PR/Literature -> level 3; any of "
        "SM High-Quality Ligand, Structure with Ligand or High-Quality Pocket, or one or "
        "more high-quality chemical probes -> level 2; any AB localisation bucket, any "
        "PR flag, SM Druggable Family or SM Med-Quality Pocket -> level 1."
    )
    if level == 0:
        return (
            f"{scope} {hit} Result: EVERY ONE OF THE 28 BUCKETS IS FALSE for this target "
            "in this release and no chemical probe is listed, so the level-0 grade means "
            "'this release carries no tractability signal for this target', NOT 'nobody "
            "looked'. It is also not a claim that the target is intractable: Open Targets "
            "reports what has been annotated, and a protein with no annotation may simply "
            "be unstudied."
        )
    positive = row.get("positive_buckets") or []
    return (
        f"{scope} {hit} Result: {len(positive)} of the 28 buckets are true "
        f"({', '.join(positive)}), and {int(row.get('n_high_quality_probes') or 0)} "
        "high-quality chemical probe(s) are listed."
    )


def _limiting_factor(row: dict[str, Any]) -> str:
    level = int(row["suggested_level"])
    if level == 3:
        return (
            "no published family selectivity profile and no documented human CNS exposure "
            "in this source; both are required for level 4"
        )
    if level == 2:
        return "no clinical precedence for this target or a close family member in this release"
    if level == 1:
        return "no characterised ligand, pocket or high-quality chemical probe in this release"
    return "no positive tractability bucket in this release; no modality is characterised"


def _document(row: dict[str, Any], spec) -> dict[str, Any]:
    symbol = row["symbol"]
    return {
        "target_id": f"TGT:{symbol}",
        "assessed_by": "agent:integration",
        "assessed_on": row["derived_at"][:10],
        "rubric": "facet_rubric_v0_1",
        "schema_version": "0.1.0",
        "notes": (
            "GENERATED by pipelines/integration/write_tractability_assessments.py from "
            f"{TRACTABILITY_INDEX.relative_to(REPO_ROOT)}; do not hand-edit. "
            "agent:integration owns exactly one facet, `tractability` (contract §5). "
            "Every other facet for this target belongs to the lead atlas, "
            "agent:alphacognition or agent:red_team and is absent by design, not by "
            "omission. run_id sprint1-integration-01"
        ),
        "facets": [
            {
                "facet": FACET,
                "assessment_status": "assessed",
                "level": int(row["suggested_level"]),
                "rationale": _rationale(row),
                "search_basis": _search_basis(row),
                "claim_refs": [],
                "source_refs": [row["source_id"]],
                "evidence_basis": "database_release",
                "counter_level": 0,
                "counter_rationale": (
                    "Searched the same pinned release for evidence that adequate modulation "
                    "is NOT achievable — a documented failure to obtain family selectivity, "
                    "or a dose-limiting adverse effect below the CNS-active exposure range — "
                    "and found none reported. This is a statement about the release, not "
                    "about the chemistry: Open Targets does not report selectivity failures, "
                    "so counter_level 0 here means 'this source is silent', and it must not "
                    "be read as evidence that selective modulation is achievable."
                ),
                "counter_claim_refs": [],
                "limiting_factor": _limiting_factor(row),
            }
        ],
    }


def _member_genes(symbol: str) -> tuple[str, ...]:
    """Member genes of a complex seed target, from the seed registry."""
    import yaml

    registry = yaml.safe_load(SEED_REGISTRY.read_text(encoding="utf-8")) or {}
    for entry in registry.get("targets") or []:
        entry_symbol = str(entry.get("symbol") or "")
        if entry_symbol == symbol:
            return tuple(str(g) for g in (entry.get("member_genes") or ()))
    return ()


def _complex_document(symbol: str, member_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """An explicit `not_assessed` record for a complex, with the member grades named.

    This is the honest output, not a shortfall. Open Targets annotates genes; a
    multi-gene functional unit has no bucket table of its own, and collapsing five
    member-gene grades into one complex grade would require deciding which subunit the
    modality acts on. That is a curatorial judgement about the mechanism, not a reading
    of a database, and contract §5.2 says an unreviewed facet is `not_assessed` with
    `level: null` rather than a guess.
    """
    grades = ", ".join(
        f"{member}={row['suggested_level']}" for member, row in sorted(member_rows.items())
    )
    versions = sorted({row["data_version"] for row in member_rows.values()})
    return {
        "target_id": f"TGT:{symbol}",
        "assessed_by": "agent:integration",
        "assessed_on": next(iter(member_rows.values()))["derived_at"][:10],
        "rubric": "facet_rubric_v0_1",
        "schema_version": "0.1.0",
        "notes": (
            "GENERATED by pipelines/integration/write_tractability_assessments.py; do not "
            "hand-edit. run_id sprint1-integration-01"
        ),
        "facets": [
            {
                "facet": FACET,
                "assessment_status": "not_assessed",
                "level": None,
                "rationale": (
                    f"NOT ASSESSED, deliberately. {symbol} is a multi-gene functional unit "
                    f"with no single Ensembl gene id, so the Open Targets release "
                    f"{', '.join(versions)} annotates its member genes individually and the "
                    f"complex not at all. Member-gene tractability levels under this rubric "
                    f"would be: {grades}. Collapsing those into one grade for the complex "
                    "requires deciding which subunit the modality acts on — for a decameric "
                    "GEF a modulator may bind at a subunit interface rather than within any "
                    "one subunit — and that is a curatorial judgement about the mechanism, "
                    "not a reading of a bucket table. Contract §5.2: a facet the agent did "
                    "not review is `not_assessed` with `level: null`, never a guess. The "
                    "uncertainty model therefore treats this as wide and uninformative "
                    "(contract P8), which is the correct cost of the gap."
                ),
                "search_basis": (
                    f"Scope: Open Targets Platform data version {', '.join(versions)} was "
                    f"searched for a target record for the complex {symbol} itself, and for "
                    f"each of its member genes. Result: the release annotates GENES and has "
                    f"no record for a multi-gene functional unit, so there is no "
                    f"complex-level bucket table to grade; the member genes are annotated "
                    f"individually and their levels are named in the rationale. What is "
                    f"recorded as NOT ASSESSED is therefore not the search — that was "
                    f"complete and its result is stated — but the curatorial judgement "
                    f"about which subunit or interface a modality engages, which cannot be "
                    f"read off a bucket table and which this agent is not entitled to make."
                ),
                "claim_refs": [],
                "source_refs": [f"SRC:DB:opentargets:{versions[0]}"],
                "evidence_basis": "database_release",
                "counter_level": None,
                "counter_claim_refs": [],
                "limiting_factor": (
                    "no complex-level tractability annotation exists; grading it needs a "
                    "curated decision about which subunit or interface a modality engages"
                ),
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    import yaml

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="Report what would be written, write nothing."
    )
    args = parser.parse_args(argv)

    spec = load_model_spec(REPO_ROOT)
    if FACET not in spec.database_gradable_facets:
        raise SystemExit(
            f"{FACET} is not flagged `database_gradable: true` in the rubric, so a "
            "source_refs-only assessment would violate contract §5.2. Refusing to write."
        )

    seeds = _seed_symbols()
    rows = _load_rows()
    written: list[str] = []
    skipped: list[str] = []

    by_symbol = {row["symbol"]: row for row in rows}
    documents: dict[str, dict[str, Any]] = {}

    for row in sorted(rows, key=lambda r: r["symbol"]):
        symbol = row["symbol"]
        if symbol not in seeds:
            skipped.append(symbol)
            continue
        documents[symbol] = _document(row, spec)

    # A complex seed target has no single Ensembl gene id, so Open Targets annotates its
    # member genes individually and the complex itself not at all. Record that as an
    # explicit `not_assessed` with the member grades named, rather than leaving a silent
    # hole: aggregating member-gene tractability into one grade for a complex is a real
    # judgement (which subunit is the target? a modulator may bind at an interface) and
    # this agent is not entitled to make it from a bucket table.
    for symbol in sorted(seeds - set(documents)):
        members = _member_genes(symbol)
        member_rows = {m: by_symbol[m] for m in members if m in by_symbol}
        if not member_rows:
            continue
        documents[symbol] = _complex_document(symbol, member_rows)

    for symbol, document in sorted(documents.items()):
        path = ASSESSMENT_DIR / f"{symbol}.yaml"
        facet = document["facets"][0]
        label = (
            f"level {facet['level']}"
            if facet["assessment_status"] == "assessed"
            else facet["assessment_status"]
        )
        if args.dry_run:
            written.append(f"{symbol} -> {label} (dry run)")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            f"# Tractability facet assessment for TGT:{symbol}.\n"
            "#\n"
            "# GENERATED — do not hand-edit. Regenerate with:\n"
            "#   .venv/bin/python pipelines/integration/write_tractability_assessments.py\n"
            "#\n"
            "# agent:integration owns exactly one facet of the contract's catalogue:\n"
            "# `tractability`. It is graded from a pinned database release rather than from\n"
            "# curated papers, which is why it carries `source_refs` and\n"
            "# `evidence_basis: database_release` instead of `claim_refs` (contract §5.2,\n"
            "# resolution R7). `tractability` is the only facet permitted to do so.\n"
            "#\n"
            "# The grade is modality maturity and nothing else. It is never evidence that\n"
            "# engaging this target does anything (contract rule V16), and it licenses no\n"
            "# statement about a compound, exposure, route or regimen.\n"
        )
        path.write_text(
            header + yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )
        written.append(f"{symbol} -> {label}")

    print(f"wrote {len(written)} tractability assessment(s) to {ASSESSMENT_DIR.relative_to(REPO_ROOT)}/")
    for line in written:
        print(f"  {line}")
    if skipped:
        print(
            f"\nskipped {len(skipped)} annotated symbol(s) absent from the seed registry "
            f"(complex member genes are annotated individually by Open Targets but are not "
            f"seed targets): {', '.join(sorted(skipped))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
