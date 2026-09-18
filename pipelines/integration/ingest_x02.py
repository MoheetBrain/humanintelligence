#!/usr/bin/env python3
"""Ingest an external X02-shaped delivery (fine mapping → QTL → colocalisation).

What this is for
----------------
An external agent (Codex/GPT-6 Astra) runs the analysis; this repository has to decide
whether to believe it. The decision is mechanical: recompute the checksums, validate
every row against its schema, check that every direction carries the allele it is
relative to, and confirm that negative results were actually delivered. Prose is not
consulted.

The asymmetry is deliberate. A delivery that passes becomes
``provenance_class: external_analysis_verified`` and is evidential like any other
source. A delivery that fails, or has not arrived, stays
``external_analysis_unverified``: visible, attributed and **inert** — no facet grade, no
biological-layer support edge, no rank movement (rule V-EXT).

Checks, and why each exists
---------------------------
=========================== ====================================================
check                       why
=========================== ====================================================
manifest present/parsable   an analysis with no manifest has no provenance
checksum recompute          the only way to know the artefact is the one analysed
row schema validation       a column that means something else is worse than absent
effect allele present       a beta without its allele inverts silently
allele sanity               strand/allele flips are invisible later
full posterior vector       H3 vs H4 is the whole question in colocalisation
priors stated               p12 drives H4 and is a choice, not a fact
developmental stage         a fetal QTL is not evidence about adult modifiability
negatives non-empty         "not tested" and "tested and null" are different states
gene-direction consistency  a direction that disagrees with its own beta is an error
=========================== ====================================================

Usage
-----
    python pipelines/integration/ingest_x02.py --delivery <dir>            # check only
    python pipelines/integration/ingest_x02.py --delivery <dir> --emit     # + write records
    python pipelines/integration/ingest_x02.py --self-test                 # fixture check

Exit 0 when the delivery would be accepted, 1 when it would be refused. The report is
printed and, with ``--json``, emitted machine-readably.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from blueprint import schemas as schema_module  # noqa: E402

TABLES: dict[str, tuple[str, bool]] = {
    # filename -> (schema kind, mandatory)
    "credible_sets.tsv": ("x02_credible_set", True),
    "credible_set_variants.tsv": ("x02_credible_set_variant", True),
    "qtl_colocalisation.tsv": ("x02_qtl_colocalisation", True),
    "regulatory_predictions.tsv": ("x02_regulatory_prediction", False),
    "negative_results.tsv": ("x02_negative_result", True),
}

NUMERIC_FIELDS = {
    "pip", "coverage", "purity_min_r2", "beta", "se", "p_value", "eaf",
    "pp_h0", "pp_h1", "pp_h2", "pp_h3", "pp_h4",
    "prior_p1", "prior_p2", "prior_p12", "threshold_used",
    "qtl_beta", "qtl_se", "score", "percentile", "observed_value",
}
INTEGER_FIELDS = {"n_variants", "n_snps_overlap", "n"}

COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}


@dataclass
class Report:
    """Outcome of checking one delivery."""

    delivery: str
    accepted: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    checksums: dict[str, str] = field(default_factory=dict)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "delivery": self.delivery,
            "accepted": self.accepted,
            "errors": self.errors,
            "warnings": self.warnings,
            "counts": self.counts,
            "checksums": self.checksums,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _coerce(row: dict[str, str]) -> dict[str, Any]:
    """Turn TSV strings into typed values, leaving empty cells as ``None``.

    A blank cell is ``None``, never ``0`` and never ``""``: the difference between
    "not reported" and "reported as zero" is exactly the kind of collapse this
    repository has had to correct five times.
    """
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            continue
        text = (value or "").strip()
        if text == "" or text.upper() in {"NA", "NAN", "NULL", "."}:
            out[key] = None
        elif key in INTEGER_FIELDS:
            try:
                out[key] = int(text)
            except ValueError:
                out[key] = text
        elif key in NUMERIC_FIELDS:
            try:
                out[key] = float(text)
            except ValueError:
                out[key] = text
        else:
            out[key] = text
    return out


def read_table(path: Path) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return [_coerce(row) for row in csv.DictReader(handle, delimiter="\t")]


def check_manifest(delivery: Path, report: Report) -> dict[str, Any] | None:
    manifest_path = delivery / "analysis_manifest.json"
    if not manifest_path.is_file():
        report.error(
            "analysis_manifest.json is missing. Without a manifest there is no genome "
            "build, no software version, no parameter record and no input checksum, so "
            "nothing here can be verified (handoff contract §2)."
        )
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError as error:
        report.error(f"analysis_manifest.json is not valid JSON: {error}")
        return None

    for required in ("analysis_id", "agent", "genome_build", "software", "inputs", "outputs"):
        if not manifest.get(required):
            report.error(f"manifest is missing required key '{required}' (handoff contract §2).")
    if manifest.get("genome_build") not in {"GRCh37", "GRCh38", "T2T-CHM13", None}:
        report.error(f"manifest genome_build {manifest.get('genome_build')!r} is not a recognised build.")
    if manifest.get("negative_results_included") is not True:
        report.error(
            "manifest does not assert negative_results_included: true. An analysis that "
            "reports only its hits cannot be ingested, because 'tested and null' and "
            "'never tested' become indistinguishable (handoff contract §2)."
        )
    for entry in manifest.get("software") or []:
        if not entry.get("version"):
            report.warn(
                f"software '{entry.get('name')}' has no pinned version; 'default settings' "
                "is not a parameter record because defaults change between versions."
            )
    return manifest


def check_checksums(delivery: Path, manifest: dict[str, Any], report: Report) -> None:
    for group in ("inputs", "outputs"):
        for entry in manifest.get(group) or []:
            declared = entry.get("sha256")
            rel = entry.get("path")
            if not rel:
                # An input may legitimately live outside the delivery — a public GWAS
                # download is not shipped with the analysis. It must still be
                # IDENTIFIABLE: a source_url plus a declared sha256 can be re-downloaded
                # and checked. Neither a path nor a (url, sha256) pair means the input
                # cannot be pinned down at all, which is fatal for an input and for an
                # output alike.
                label = entry.get("role") or entry.get("description")
                if group == "inputs" and entry.get("source_url") and entry.get("sha256"):
                    report.warn(
                        f"input {label!r} is external to the delivery; its checksum "
                        "cannot be recomputed here and must be checked on re-download."
                    )
                else:
                    report.error(
                        f"{group} entry {label!r} has neither a local path nor a "
                        "(source_url, sha256) pair, so the artefact it was computed "
                        "from cannot be identified."
                    )
                continue
            path = (delivery / rel) if not Path(rel).is_absolute() else Path(rel)
            if not path.is_file():
                # An input may legitimately live outside the delivery (a public GWAS
                # download). Its checksum is then unverifiable here, which is a warning
                # for inputs and an error for outputs the delivery claims to contain.
                message = (
                    f"{group} path {rel!r} is not present in the delivery, so its "
                    "checksum cannot be recomputed."
                )
                (report.warn if group == "inputs" else report.error)(message)
                continue
            actual = sha256_file(path)
            report.checksums[rel] = actual
            if not declared:
                report.error(f"{group} {rel!r} declares no sha256; recomputed {actual}.")
            elif declared != actual:
                report.error(
                    f"CHECKSUM MISMATCH for {rel!r}: manifest says {declared}, file is "
                    f"{actual}. The artefact is not the one the manifest describes, so "
                    "nothing from this delivery is ingested."
                )


def check_rows(delivery: Path, report: Report) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {}
    for filename, (kind, mandatory) in TABLES.items():
        path = delivery / filename
        if not path.is_file():
            if mandatory:
                report.error(f"mandatory table {filename} is missing (handoff contract §5).")
            tables[filename] = []
            continue
        rows = read_table(path)
        tables[filename] = rows
        report.counts[filename] = len(rows)
        if mandatory and not rows:
            report.error(
                f"{filename} is present but empty. For negative_results.tsv in "
                "particular this is refused: an X02-shaped analysis with no negatives "
                "has either not searched or not reported, and the difference matters."
                if filename == "negative_results.tsv"
                else f"{filename} is present but empty."
            )
        for index, row in enumerate(rows, start=2):  # line 1 is the header
            for violation in schema_module.validate_record(
                row, kind, source_path=f"{filename}:{index}"
            ):
                report.error(violation.message)
    return tables


def check_directions(tables: dict[str, list[dict[str, Any]]], report: Report) -> None:
    """Direction integrity: the checks that silently invert a conclusion when skipped."""
    for index, row in enumerate(tables.get("credible_set_variants.tsv") or [], start=2):
        effect, other = row.get("effect_allele"), row.get("other_allele")
        if row.get("beta") is not None and not effect:
            report.error(
                f"credible_set_variants.tsv:{index} has a beta but no effect_allele. A "
                "direction without the allele it is relative to is meaningless and "
                "inverts silently under a strand flip."
            )
        if effect and other and effect == other:
            report.error(
                f"credible_set_variants.tsv:{index} effect_allele and other_allele are "
                f"both {effect!r}."
            )
        if effect and other and COMPLEMENT.get(effect) == other and len(effect) == 1:
            report.warn(
                f"credible_set_variants.tsv:{index} is a strand-ambiguous "
                f"{effect}/{other} variant; confirm harmonisation against eaf rather "
                "than trusting the alleles."
            )

    for index, row in enumerate(tables.get("qtl_colocalisation.tsv") or [], start=2):
        posteriors = [row.get(f"pp_h{n}") for n in range(5)]
        if any(value is None for value in posteriors):
            report.error(
                f"qtl_colocalisation.tsv:{index} does not report the full posterior "
                "vector pp_h0..pp_h4. H3 versus H4 is the distinction between two "
                "independent signals and one shared causal variant; without it a "
                "colocalisation claim is unfalsifiable."
            )
        else:
            total = sum(float(value) for value in posteriors)
            if abs(total - 1.0) > 0.05:
                report.warn(
                    f"qtl_colocalisation.tsv:{index} posteriors sum to {total:.3f}, not ~1."
                )
        direction, beta = row.get("direction_on_gene"), row.get("qtl_beta")
        if direction in {"increases", "decreases"}:
            if not row.get("qtl_effect_allele"):
                report.error(
                    f"qtl_colocalisation.tsv:{index} states direction_on_gene="
                    f"{direction!r} with no qtl_effect_allele. The direction is relative "
                    "to an allele or it is not a direction."
                )
            if beta is not None:
                expected = "increases" if float(beta) > 0 else "decreases"
                if expected != direction:
                    report.error(
                        f"qtl_colocalisation.tsv:{index} states direction_on_gene="
                        f"{direction!r} but qtl_beta={beta}. The stated direction "
                        "contradicts its own effect size."
                    )
        if row.get("qtl_type") == "sqtl" and not row.get("intron_id"):
            report.error(
                f"qtl_colocalisation.tsv:{index} is an sQTL with no intron_id. A "
                "splicing result with no named junction is not a splicing result."
            )
        if row.get("outcome") == "colocalised":
            threshold = row.get("threshold_used")
            if threshold is not None and row.get("pp_h4") is not None:
                if float(row["pp_h4"]) < float(threshold):
                    report.error(
                        f"qtl_colocalisation.tsv:{index} is marked colocalised with "
                        f"pp_h4={row['pp_h4']} below its own threshold {threshold}."
                    )
        if row.get("developmental_stage") == "unknown":
            report.warn(
                f"qtl_colocalisation.tsv:{index} has developmental_stage=unknown. "
                "Unknown is not adult: this row cannot support an adult-modifiability "
                "grade."
            )

    tested = {
        (row.get("credible_set_id"), row.get("gene_id"))
        for row in tables.get("qtl_colocalisation.tsv") or []
    }
    if tested and not any(
        row.get("outcome") in {"tested_not_colocalised", "tested_indeterminate"}
        for row in tables.get("qtl_colocalisation.tsv") or []
    ):
        report.warn(
            "every colocalisation row is a positive outcome. That is possible, but an "
            "analysis of this shape normally tests many pairs that do not colocalise; "
            "confirm the negatives were not filtered out before delivery."
        )


def check_cross_references(tables: dict[str, list[dict[str, Any]]], report: Report) -> None:
    sets = {row.get("credible_set_id") for row in tables.get("credible_sets.tsv") or []}
    for index, row in enumerate(tables.get("credible_set_variants.tsv") or [], start=2):
        if row.get("credible_set_id") not in sets:
            report.error(
                f"credible_set_variants.tsv:{index} references credible set "
                f"{row.get('credible_set_id')!r}, which credible_sets.tsv does not declare."
            )
    for index, row in enumerate(tables.get("qtl_colocalisation.tsv") or [], start=2):
        if row.get("credible_set_id") not in sets:
            report.error(
                f"qtl_colocalisation.tsv:{index} references credible set "
                f"{row.get('credible_set_id')!r}, which credible_sets.tsv does not declare."
            )
    # PIPs within a credible set should not exceed 1 in total by much.
    totals: dict[str, float] = {}
    for row in tables.get("credible_set_variants.tsv") or []:
        if row.get("pip") is not None:
            totals[str(row.get("credible_set_id"))] = totals.get(
                str(row.get("credible_set_id")), 0.0
            ) + float(row["pip"])
    for set_id, total in sorted(totals.items()):
        if total > 1.25:
            report.warn(
                f"credible set {set_id} has PIPs summing to {total:.2f}; a single "
                "credible set's PIPs should sum to about 1."
            )


def check_delivery(delivery: Path) -> Report:
    report = Report(delivery=str(delivery))
    manifest = check_manifest(delivery, report)
    if manifest is not None:
        check_checksums(delivery, manifest, report)
    tables = check_rows(delivery, report)
    check_directions(tables, report)
    check_cross_references(tables, report)
    report.accepted = not report.errors
    return report


def render(report: Report) -> str:
    lines = [f"delivery: {report.delivery}"]
    if report.counts:
        lines.append("rows: " + ", ".join(f"{k}={v}" for k, v in sorted(report.counts.items())))
    for message in report.errors:
        lines.append(f"  ERROR   {message}")
    for message in report.warnings:
        lines.append(f"  warning {message}")
    verdict = (
        "ACCEPTED — would be ingested as external_analysis_verified"
        if report.accepted
        else "REFUSED — stays external_analysis_unverified and inert (rule V-EXT)"
    )
    lines.append(f"{verdict}: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--delivery", help="directory containing analysis_manifest.json and the tables")
    group.add_argument(
        "--self-test",
        action="store_true",
        help="check the synthetic fixture under tests/fixtures/x02_delivery_valid/",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    parser.add_argument(
        "--emit",
        action="store_true",
        help="on acceptance, write the canonical external-analysis record (not implemented "
        "until a real delivery exists; refuses rather than guessing a shape)",
    )
    args = parser.parse_args(argv)

    delivery = (
        REPO_ROOT / "tests" / "fixtures" / "x02_delivery_valid"
        if args.self_test
        else Path(args.delivery)
    )
    if not delivery.is_dir():
        print(f"no such delivery directory: {delivery}", file=sys.stderr)
        return 1

    report = check_delivery(delivery)
    print(json.dumps(report.as_dict(), indent=2) if args.json else render(report))

    if args.emit:
        print(
            "\n--emit is deliberately not implemented: the canonical record's shape "
            "depends on what a real delivery contains, and generating one from a "
            "fixture would bake a guess into the repository. Re-run with --emit once "
            "an actual X02 delivery is present.",
            file=sys.stderr,
        )
        return 1 if not report.accepted else 0
    return 0 if report.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
