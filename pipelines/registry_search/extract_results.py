#!/usr/bin/env python3
"""Extract posted cognitive results for trials the registry search queued.

Why a separate step
-------------------
``search_registry.py`` refuses to guess whether a trial was positive or null. It can see
that a cognitive outcome exists and that results were posted; deciding the direction
needs the results section read. This script fetches that section and records, verbatim,
what the registry actually posted:

* the cognitive outcome measures and their class (primary / secondary);
* per-group values and dispersion, as strings, exactly as posted;
* any statistical analysis rows the sponsor supplied — p-values, CIs, method.

It records those as **strings in ``as_reported``**, never as typed numbers, and it
assigns no classification. A row becomes ``tested_and_positive`` or ``tested_and_null``
only when a human or the red team reads the extracted values and says so with a reason,
because "positive" is a judgement about a prespecified endpoint, an effect direction and
a comparison — not a regex over a results table.

Usage
-----
    python pipelines/registry_search/extract_results.py --queued
    python pipelines/registry_search/extract_results.py --nct NCT02953639
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import http_get_json, utc_now, write_snapshot  # noqa: E402

CTGOV = "https://clinicaltrials.gov/api/v2/studies"
SEARCH_DIR = REPO_ROOT / "evidence" / "registry_searches"
OUT_DIR = REPO_ROOT / "evidence" / "registry_searches" / "results"



def _keyword_pattern(keywords: list[str]) -> "re.Pattern[str]":
    """Compile keywords with word boundaries.

    Substring matching is wrong here and the failure is not hypothetical: `wais` (the
    Wechsler scale) matches inside "waist circumference", which classified three
    metabolic secondary outcomes as cognitive and queued three trials for cognitive
    results extraction. Short instrument acronyms — wais, wisc, iq, moca, mmse — are
    exactly the keywords most likely to appear inside an unrelated word, so every
    keyword is anchored at both ends. Multi-word phrases keep their internal spaces.
    """
    parts = [rf"\b{re.escape(keyword)}\b" for keyword in keywords]
    return re.compile("|".join(parts), re.IGNORECASE)

def load_terms_keywords() -> tuple[list[str], list[str]]:
    config = yaml.safe_load(
        (REPO_ROOT / "pipelines" / "registry_search" / "target_search_terms.yaml").read_text()
    )
    return (
        [k.lower() for k in config["cognitive_endpoint_keywords"]],
        [k.lower() for k in config["non_cognitive_lookalikes"]],
    )


def fetch_study(nct: str) -> dict[str, Any]:
    url = f"{CTGOV}/{nct}"
    payload = http_get_json(url)
    write_snapshot("ctgov_v2", payload, url=url, query={"nct_id": nct}, name_hint=f"full_{nct}")
    time.sleep(0.35)
    return payload


def _is_cognitive(title: str, keywords: list[str], lookalikes: list[str]) -> bool:
    if _keyword_pattern(lookalikes).search(title):
        return False
    return bool(_keyword_pattern(keywords).search(title))


def extract(nct: str, keywords: list[str], lookalikes: list[str]) -> dict[str, Any]:
    payload = fetch_study(nct)
    protocol = payload.get("protocolSection") or {}
    results = payload.get("resultsSection") or {}
    ident = protocol.get("identificationModule") or {}
    status = protocol.get("statusModule") or {}

    outcomes: list[dict[str, Any]] = []
    for entry in (results.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []:
        title = str(entry.get("title") or "")
        if not _is_cognitive(title, keywords, lookalikes):
            continue
        groups = {
            str(g.get("id")): str(g.get("title") or "")
            for g in entry.get("groups") or []
        }
        values: list[str] = []
        for cls in entry.get("classes") or []:
            for category in cls.get("categories") or []:
                for measurement in category.get("measurements") or []:
                    group = groups.get(str(measurement.get("groupId")), str(measurement.get("groupId")))
                    parts = [f"value={measurement.get('value')}"]
                    for key in ("spread", "lowerLimit", "upperLimit"):
                        if measurement.get(key) is not None:
                            parts.append(f"{key}={measurement.get(key)}")
                    values.append(f"{group}: " + ", ".join(parts))
        analyses: list[str] = []
        for analysis in entry.get("analyses") or []:
            bits = []
            for key in ("pValue", "pValueComment", "statisticalMethod", "paramType",
                        "paramValue", "ciLowerLimit", "ciUpperLimit", "ciPctValue"):
                if analysis.get(key) not in (None, ""):
                    bits.append(f"{key}={analysis.get(key)}")
            if bits:
                analyses.append("; ".join(bits))
        outcomes.append(
            {
                "title": title,
                "outcome_class": entry.get("type"),
                "time_frame": entry.get("timeFrame"),
                "population_description": entry.get("populationDescription"),
                "unit_of_measure": entry.get("unitOfMeasure"),
                "param_type": entry.get("paramType"),
                "dispersion_type": entry.get("dispersionType"),
                "values_as_reported": values[:24],
                "analyses_as_reported": analyses[:12],
            }
        )

    return {
        "nct_id": nct,
        "official_title": ident.get("officialTitle") or ident.get("briefTitle"),
        "overall_status": status.get("overallStatus"),
        "why_stopped": status.get("whyStopped"),
        "results_posted": bool(payload.get("hasResults")),
        "cognitive_outcomes_with_posted_results": outcomes,
        "n_cognitive_outcomes_extracted": len(outcomes),
        "classification": "extracted_awaiting_judgement",
        "classification_note": (
            "Direction NOT assigned by this pipeline. tested_and_positive versus "
            "tested_and_null is a judgement about a prespecified endpoint, an effect "
            "direction and a comparison, and a regex over a results table cannot make "
            "it. The red team assigns it, with a reason, from the values above."
        ),
        "extracted_by": "agent:orchestrator",
        "extracted_on": utc_now(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--queued", action="store_true", help="extract every queued NCT")
    group.add_argument("--nct", help="extract one NCT id")
    args = parser.parse_args(argv)

    keywords, lookalikes = load_terms_keywords()
    queue: dict[str, list[str]] = {}
    if args.queued:
        for path in sorted(glob.glob(str(SEARCH_DIR / "*.yaml"))):
            record = yaml.safe_load(Path(path).read_text())
            if record.get("results_extraction_queue"):
                queue[record["symbol"]] = record["results_extraction_queue"]
    else:
        queue["adhoc"] = [args.nct]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    extracted = 0
    for symbol, ncts in sorted(queue.items()):
        payloads = []
        for nct in ncts:
            try:
                payloads.append(extract(nct, keywords, lookalikes))
            except Exception as error:
                payloads.append(
                    {
                        "nct_id": nct,
                        "error": f"{type(error).__name__}: {error}",
                        "classification": "extraction_failed",
                    }
                )
            extracted += 1
        path = OUT_DIR / f"{symbol}.yaml"
        path.write_text(
            "# Posted cognitive results, extracted verbatim. Generated by\n"
            "# pipelines/registry_search/extract_results.py — do not hand-edit.\n"
            "#\n"
            "# Every value is a STRING exactly as the registry posted it. No direction is\n"
            "# assigned here: positive-versus-null is the red team's judgement, with a reason.\n"
            + yaml.safe_dump(
                {"symbol": symbol, "trials": payloads},
                sort_keys=False, allow_unicode=True, width=100,
            ),
            encoding="utf-8",
        )
        summary = ", ".join(
            f"{p['nct_id']}({p.get('n_cognitive_outcomes_extracted', 'err')})" for p in payloads
        )
        print(f"{symbol:14s} {summary}")
    print(f"\n{extracted} trial(s) extracted to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
