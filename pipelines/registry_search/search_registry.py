#!/usr/bin/env python3
"""Target-directed clinical-trial registry search, with honest classification.

The problem this solves
-----------------------
Three atlases graded ``human_intervention_evidence: 0`` after searching only the
literature. A registry holds interventions that were *performed and never published* —
the one category a translation facet most depends on and the one a literature search
cannot return. When the power atlas finally ran registry searches it overturned two of
its own published statements.

So this pipeline asks the registry directly, per target, and classifies what comes back
into the seven states the Sprint-2 brief specifies:

===== ================================ =====================================================
code  state                            how it is decided
===== ================================ =====================================================
A     tested_and_positive              cognitive outcome + results posted + a reported
                                       positive effect (never inferred; requires extraction)
B     tested_and_null                  cognitive outcome + results posted + reported null
C     tested_wrong_endpoint            trial RAN (status in RAN_STATUSES), recorded
                                       outcome measures, none of them cognitive
D     completed_unreported             cognitive outcome, completed, no results posted
E     terminated                       overallStatus TERMINATED / SUSPENDED
F     withdrawn                        overallStatus WITHDRAWN (often zero enrolment)
G     no_matching_trial_found          no record matched these terms in this registry,
                                       within the records examined
N     not_yet_run                      status not in RAN_STATUSES (NOT_YET_RECRUITING and
                                       similar) — has measured nothing at all
U     outcomes_not_recorded            no outcome measures in the registry entry; the
                                       protocol is unknown, not known to lack cognition
===== ================================ =====================================================

**G, N and U are statements about records, not about biology.** Each was once collapsed
into a stronger state, and each collapse manufactured a null out of a gap:

* **G** was named `no_trial_identified` and its record text read "NOBODY HAS TESTED THIS".
  That is a claim about the world drawn from one registry, one set of terms and — before
  this pipeline paginated — a truncated slice of even that. Six other registries are not
  searched, and unregistered work is invisible.
* **N** did not exist: 20 not-yet-recruiting trials were classified C,
  `tested_wrong_endpoint`, which reads as a completed trial that measured something else.
* **U** did not exist: 5 trials with an EMPTY outcomes module were classified C, inferring
  a fact about a protocol from a hole in a record.

None of the three may raise any facet's `counter_level`, and the facet-update guidance
derived from this pipeline never converts them into biological nulls.

A and B are deliberately NOT decided automatically. Distinguishing a positive from a
null needs the results section read with judgement — effect direction, the endpoint that
mattered, whether the comparison was prespecified. Rows that reach that point are
classified ``results_posted_extraction_pending`` and listed for extraction, because a
regex that guesses "positive" from a results table is exactly the kind of automation this
repository refuses.

Usage
-----
    python pipelines/registry_search/search_registry.py --all
    python pipelines/registry_search/search_registry.py --target TGT:GABRA5
    python pipelines/registry_search/search_registry.py --offline   # rebuild from snapshots
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import http_get_json, utc_now, write_snapshot  # noqa: E402

CTGOV = "https://clinicaltrials.gov/api/v2/studies"
TERMS_FILE = REPO_ROOT / "pipelines" / "registry_search" / "target_search_terms.yaml"
OUT_DIR = REPO_ROOT / "evidence" / "registry_searches"
PAGE_SIZE = 200
# A cap, not a screening decision. Terms like "caffeine" return thousands of records,
# almost all irrelevant, and fetching them all would cost far more than it informs. When
# the cap binds, the record says `coverage: partial_capped` and no absence may be read
# from it. The cap is generous enough that every term in target_search_terms.yaml except
# the broadest few is screened to exhaustion.
MAX_RECORDS_PER_TERM = 1000

# Only the modules classification needs. A search snapshot that stores whole study
# records cost 6.4 MB for one query and 66 MB for the run, which the commit guard
# rightly refused; field selection brings the same query to 473 KB with nothing lost
# that this pipeline reads.
SEARCH_FIELDS = (
    "protocolSection.identificationModule,"
    "protocolSection.statusModule,"
    "protocolSection.designModule,"
    "protocolSection.outcomesModule,"
    "protocolSection.armsInterventionsModule,"
    "hasResults"
)

TERMINATED_STATUSES = {"TERMINATED", "SUSPENDED"}
WITHDRAWN_STATUSES = {"WITHDRAWN"}
RAN_STATUSES = {
    "COMPLETED", "TERMINATED", "SUSPENDED", "ACTIVE_NOT_RECRUITING",
    "RECRUITING", "ENROLLING_BY_INVITATION", "UNKNOWN",
}



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

def load_terms() -> dict[str, Any]:
    return yaml.safe_load(TERMS_FILE.read_text(encoding="utf-8"))


def search_term(term: str) -> dict[str, Any]:
    """One registry query, paginated to exhaustion or to MAX_RECORDS, snapshotted.

    WHY THIS PAGINATES
    ------------------
    The first version of this function fetched ONE page of 50 and then recorded the
    registry's `totalCount` as `total_hits`. The resulting records read as though a
    whole result set had been screened:

        total_hits: 1934
        kept: 25

    when in fact 25 had been kept out of the **50** records actually examined and 1884
    were never fetched. Every downstream count — `n_studies_classified`, the A-G
    classification tallies, the reporting-gap list, and above all `no_matching_trial_found`
    — inherited that false denominator. A completed trial with posted cognitive results
    sitting at rank 51 was indistinguishable from one that did not exist.

    This is the same bug class the repository keeps meeting from a new direction:
    absence of measurement presented as measured absence. Here the un-examined records
    were silently converted into screened-and-rejected ones.

    The fix has two halves, and the second matters as much as the first: paginate, AND
    record how much of the result set was actually seen, so a partial screen can never
    again be read as a complete one.
    """
    collected: list[dict[str, Any]] = []
    total: int | None = None
    token: str | None = None
    pages = 0
    while True:
        params: dict[str, Any] = {
            "query.term": term,
            "pageSize": PAGE_SIZE,
            "countTotal": "true",
            "fields": SEARCH_FIELDS,
        }
        if token:
            params["pageToken"] = token
        payload = http_get_json(CTGOV, params=params)
        write_snapshot(
            "ctgov_v2",
            payload,
            url=CTGOV,
            query={"query.term": term, "pageSize": PAGE_SIZE, "page": pages,
                   "fields": SEARCH_FIELDS},
            name_hint=f"search_{urllib.parse.quote_plus(term)[:36]}_p{pages}",
            compress=True,
        )
        if total is None:
            total = payload.get("totalCount")
        collected.extend(payload.get("studies") or [])
        token = payload.get("nextPageToken")
        pages += 1
        time.sleep(0.35)
        if not token or len(collected) >= MAX_RECORDS_PER_TERM:
            break
    # `coverage` is the honest half of the fix. `complete` means the whole result set was
    # examined and a "not found" is therefore a real absence WITHIN THIS REGISTRY.
    # `partial_capped` means the screen stopped early and NO absence may be inferred.
    complete = total is not None and len(collected) >= total
    return {
        "studies": collected,
        "totalCount": total,
        "n_examined": len(collected),
        "pages_fetched": pages,
        "coverage": "complete" if complete else "partial_capped",
    }


def outcome_measures(protocol: dict[str, Any]) -> list[str]:
    module = protocol.get("outcomesModule") or {}
    measures: list[str] = []
    for key in ("primaryOutcomes", "secondaryOutcomes", "otherOutcomes"):
        for entry in module.get(key) or []:
            if isinstance(entry, dict) and entry.get("measure"):
                measures.append(str(entry["measure"]))
    return measures


def measures_cognitive(measures: list[str], keywords: list[str], lookalikes: list[str]) -> tuple[bool, list[str]]:
    """Does this trial measure cognition, and which measures made us say so?

    A measure that only matches a `non_cognitive_lookalike` (Vineland, PANSS, CGI) does
    not count: adaptive behaviour and symptom severity are not cognition, and counting
    them is how "tested and null" is manufactured out of "tested something else".
    """
    good = _keyword_pattern(keywords)
    bad = _keyword_pattern(lookalikes)
    hits: list[str] = []
    for measure in measures:
        if bad.search(measure):
            continue
        if good.search(measure):
            hits.append(measure)
    return bool(hits), hits


def classify(study: dict[str, Any], keywords: list[str], lookalikes: list[str]) -> dict[str, Any]:
    protocol = study.get("protocolSection") or {}
    ident = protocol.get("identificationModule") or {}
    status_module = protocol.get("statusModule") or {}
    design = protocol.get("designModule") or {}
    status = status_module.get("overallStatus")
    measures = outcome_measures(protocol)
    cognitive, cognitive_measures = measures_cognitive(measures, keywords, lookalikes)
    has_results = bool(study.get("hasResults"))

    if status in WITHDRAWN_STATUSES:
        code, state = "F", "withdrawn"
    elif status in TERMINATED_STATUSES:
        code, state = "E", "terminated"
    elif status not in RAN_STATUSES:
        # A trial that has not started cannot have "tested the wrong endpoint". Before
        # this branch existed, RAN_STATUSES was defined and never referenced — a dead
        # safety constant — and 20 NOT_YET_RECRUITING trials were filed as C,
        # `tested_wrong_endpoint`, which reads as a completed trial that measured
        # something else. It is a trial that has measured nothing at all.
        code, state = "N", "not_yet_run"
    elif not measures:
        # No outcome measures recorded in the registry entry. Concluding "measured no
        # cognitive outcome" from an EMPTY outcomes module is inferring a fact about the
        # protocol from a gap in the record.
        code, state = "U", "outcomes_not_recorded"
    elif not cognitive:
        code, state = "C", "tested_wrong_endpoint"
    elif status == "COMPLETED" and not has_results:
        code, state = "D", "completed_unreported"
    elif status == "COMPLETED" and has_results:
        code, state = "AB", "results_posted_extraction_pending"
    else:
        code, state = "R", "ongoing_or_not_yet_reported"

    return {
        "nct_id": ident.get("nctId"),
        "brief_title": ident.get("briefTitle"),
        "official_title": ident.get("officialTitle"),
        "overall_status": status,
        "why_stopped": status_module.get("whyStopped"),
        "phases": design.get("phases") or [],
        "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
        "has_results": has_results,
        "measures_cognition": cognitive,
        "cognitive_outcome_measures": cognitive_measures[:6],
        "n_outcome_measures": len(measures),
        "classification_code": code,
        "classification": state,
    }


def relevant(study: dict[str, Any], term: str) -> bool:
    """Keep a study only when the search term actually appears in its intervention or title.

    A free-text registry query matches anywhere, so a search for a gene symbol returns
    trials that merely mention a pathway in a description. Requiring the term in the
    title or an intervention name keeps the classification about this target rather than
    about the literature's vocabulary.
    """
    protocol = study.get("protocolSection") or {}
    ident = protocol.get("identificationModule") or {}
    arms = protocol.get("armsInterventionsModule") or {}
    haystack = " ".join(
        [
            str(ident.get("briefTitle") or ""),
            str(ident.get("officialTitle") or ""),
            *[str(i.get("name") or "") for i in arms.get("interventions") or []],
            *[str(i.get("description") or "") for i in arms.get("interventions") or []],
        ]
    ).lower()
    if not term:
        return False
    # ALL tokens of the term must appear, each on a word boundary, in any order.
    #
    # Two failures drove this rule. Matching only the term's first token turned
    # "integrated stress response" into a hit on a "Community Reintegration Workshop" —
    # a behavioural trial with no pharmacological relation to the target. Requiring the
    # exact phrase then dropped a genuinely relevant trial titled "...Dopamine Receptor 1
    # Partial Agonist...", because registries do not phrase mechanisms the way we do.
    # All-tokens-any-order keeps the recall while refusing the accidental match.
    tokens = [t for t in re.split(r"[\s,()]+", term) if len(t) > 1]
    if not tokens:
        return False
    pattern_cache = _keyword_pattern
    return all(pattern_cache([token]).search(haystack) for token in tokens)


def search_target(target_id: str, config: dict[str, Any], keywords: list[str], lookalikes: list[str]) -> dict[str, Any]:
    studies: dict[str, dict[str, Any]] = {}
    per_term: list[dict[str, Any]] = []
    for entry in config.get("terms") or []:
        term = entry["term"]
        try:
            payload = search_term(term)
        except Exception as error:  # a failed query is recorded, never guessed
            per_term.append(
                {
                    "term": term,
                    "provenance": entry.get("provenance"),
                    "error": f"{type(error).__name__}: {error}",
                    "total_hits": None,
                    "kept": 0,
                }
            )
            continue
        total = payload.get("totalCount")
        kept = 0
        for study in payload.get("studies") or []:  # noqa: B007
            if not relevant(study, term):
                continue
            record = classify(study, keywords, lookalikes)
            nct = record.get("nct_id")
            if not nct:
                continue
            record["matched_terms"] = sorted(
                set(studies.get(nct, {}).get("matched_terms", [])) | {term}
            )
            studies[nct] = record
            kept += 1
        per_term.append(
            {
                "term": term,
                "provenance": entry.get("provenance"),
                "total_hits": total,
                # n_examined is the real denominator. `kept` is out of THIS, never out
                # of total_hits.
                "n_examined": payload.get("n_examined"),
                "pages_fetched": payload.get("pages_fetched"),
                "coverage": payload.get("coverage"),
                "kept": kept,
            }
        )
    coverages = {t.get("coverage") for t in per_term if t.get("coverage")}
    return {
        "per_term": per_term,
        "studies": studies,
        # The whole target's screen is only complete if every term's screen was.
        "coverage": "complete" if coverages == {"complete"} else "partial_capped",
    }


def summarise(studies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for record in studies.values():
        counts[record["classification"]] = counts.get(record["classification"], 0) + 1
    return counts


def write_record(target_id: str, symbol: str, result: dict[str, Any]) -> Path:
    studies = result["studies"]
    counts = summarise(studies)
    extraction_queue = sorted(
        nct for nct, record in studies.items()
        if record["classification"] == "results_posted_extraction_pending"
    )
    unreported = sorted(
        nct for nct, record in studies.items() if record["classification"] == "completed_unreported"
    )
    payload = {
        "schema_version": "0.2.0",
        "target_id": target_id,
        "symbol": symbol,
        "registry": "clinicaltrials_gov_v2",
        "searched_by": "agent:orchestrator",
        "searched_on": utc_now(),
        "search_terms": result["per_term"],
        "n_studies_classified": len(studies),
        "classification_counts": counts,
        # Renamed from `no_trial_identified`. The old name, and the old interpretation
        # string, asserted that NOBODY HAD TESTED the target — a claim about the world
        # inferred from a query over one registry with one set of terms, and (before the
        # pagination fix above) over a truncated slice of even that. The field can only
        # ever support the weaker statement its new name makes.
        "no_matching_trial_found": len(studies) == 0,
        "screen_coverage": result.get("coverage"),
        "registries_searched": ["clinicaltrials_gov_v2"],
        "registries_not_searched": ["EudraCT", "ISRCTN", "jRCT", "ChiCTR", "ANZCTR", "CTRI"],
        "interpretation": (
            "NO TRIAL MATCHED THESE TERMS in ClinicalTrials.gov within the records examined. "
            "This is a statement about one registry and one set of search terms, NOT a "
            "biological null and NOT a claim that the target is untested: other registries "
            "were not searched, unregistered work is invisible here, and a trial phrased "
            "differently would not match. It may not be recorded as evidence against the "
            "target, and it may not raise any facet's counter_level."
            if not studies
            else
            "Classified registry hits. `completed_unreported` entries are reporting gaps and "
            "belong in a facet's reporting_gap_refs, never in counter_level. "
            "`results_posted_extraction_pending` entries are the only ones that can become "
            "tested-and-positive or tested-and-null, and only after the results section is "
            "read: this pipeline does not guess a direction from a results table."
        ),
        "reporting_gap_candidates": unreported,
        "results_extraction_queue": extraction_queue,
        "studies": dict(sorted(studies.items())),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{symbol}.yaml"
    path.write_text(
        "# Target-directed registry search. Generated by "
        "pipelines/registry_search/search_registry.py — do not hand-edit.\n"
        "#\n"
        "# `no_matching_trial_found: true` means NO RECORD MATCHED THESE TERMS in this one\n"
        "# registry, within the records examined. It is not a tested null, and it is not\n"
        "# evidence that nobody has tested the target. Check `screen_coverage`: where it\n"
        "# reads `partial_capped`, the result set was NOT screened to exhaustion and no\n"
        "# absence of any kind may be inferred.\n"
        "#\n"
        "# `kept` is out of `n_examined`, NEVER out of `total_hits`.\n"
        + yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="search every configured target")
    group.add_argument("--target", help="search one target id, e.g. TGT:GABRA5")
    args = parser.parse_args(argv)

    config = load_terms()
    keywords = [k.lower() for k in config["cognitive_endpoint_keywords"]]
    lookalikes = [k.lower() for k in config["non_cognitive_lookalikes"]]
    targets = config["targets"]
    selected = sorted(targets) if args.all else [args.target]

    total_written = 0
    for target_id in selected:
        entry = targets.get(target_id)
        if entry is None:
            print(f"! {target_id} is not configured in {TERMS_FILE.name}", file=sys.stderr)
            return 1
        result = search_target(target_id, entry, keywords, lookalikes)
        path = write_record(target_id, entry["symbol"], result)
        counts = summarise(result["studies"])
        flag = "NO TRIAL IDENTIFIED" if not result["studies"] else ", ".join(
            f"{state}={n}" for state, n in sorted(counts.items())
        )
        print(f"{entry['symbol']:16s} {len(result['studies']):3d} studies  {flag}")
        total_written += 1
    print(f"\n{total_written} record(s) written to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
