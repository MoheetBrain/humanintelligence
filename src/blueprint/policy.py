"""Computational-only policy checks (contract P1, rule V20).

What this module enforces
-------------------------
``docs/COMPUTATIONAL_ONLY_POLICY.md``: this project performs, plans, designs and
recommends NO wet-lab, in-vitro, ex-vivo, animal or human experiment, including
self-experimentation, and produces no dose, route, regimen or protocol. Existing
experimental results are ingested as evidence, which is a computational act.

Two mechanisms, deliberately different in kind:

1. **The closed ``action_type`` enum** (:func:`action_types`, :func:`check_action_type`).
   Loaded at runtime from ``docs/TASK_DAG.yaml``. Structural, exact, no false
   positives: a record proposing work must name an action type, and every legal value
   is computational.
2. **Text heuristics** (:func:`scan_text`). Free prose can propose prohibited work
   whatever the structured fields say, so the prose is scanned too.

The heuristic is deliberately narrow
------------------------------------
The hard part is that a legitimate claim statement DESCRIBES somebody else's animal or
dosing study — "mice received a single injection before training" is exactly what a
faithful evidence record looks like. Flagging that would make the rule unusable and
would push agents to launder their statements.

So a pattern fires only when a PROPOSAL CUE (first person plural intent, an
imperative, a "next step", a recommendation) co-occurs within a short window with a
PROHIBITED ACTION CUE (administering, dosing, injecting, recruiting, culturing,
sacrificing, self-experimenting). A second family of patterns catches
reader-directed instructions ("take N mg daily"), which are prohibited regardless of
framing.

This still has false positives — "we will analyse published dose-response data" is
computational and could trip a naive reading, which is why "analys*", "review*",
"ingest*", "extract*" and similar computational verbs are treated as exculpatory
context. Known limitations are recorded in docs/ONTOLOGY_NOTES.md. When the heuristic
is wrong, the fix is to sharpen the pattern, not to lower the severity: a record that
proposes prohibited work must fail the build.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import yaml

from blueprint import paths
from blueprint.violations import Violation, error

# --- 1. the closed action_type enum -------------------------------------------------

@lru_cache(maxsize=8)
def action_types(root: Path | str | None = None) -> tuple[str, ...]:
    """The closed ``action_type`` enum from ``docs/TASK_DAG.yaml``.

    Returns an empty tuple when the file is absent, and callers then skip the check
    rather than inventing an enum: a fabricated allow-list is worse than no check.
    """
    path = paths.task_dag_file(root)
    if not path.is_file():
        return ()
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return tuple(document.get("action_type_enum") or ())


def check_action_type(
    value: str, *, path: str, record_id: str | None = None, root: Path | str | None = None
) -> list[Violation]:
    """Reject an ``action_type`` outside the closed computational enum."""
    allowed = action_types(root)
    if not allowed or value in allowed:
        return []
    return [
        error(
            "V20",
            path,
            f"action_type {value!r} is not in the closed computational enum in "
            f"docs/TASK_DAG.yaml. Every legal value is a computational action; adding a "
            f"laboratory, animal or human action type is a policy violation "
            f"(docs/COMPUTATIONAL_ONLY_POLICY.md). Allowed: {list(allowed)}",
            record_id=record_id,
        )
    ]


# --- 2. text heuristics -------------------------------------------------------------

# Cues that the text is PROPOSING something rather than reporting it.
PROPOSAL_CUES = (
    r"we (?:will|should|plan to|propose to|intend to|aim to|are going to)",
    r"(?:i|we)(?:'ll| will) (?:then )?",
    r"(?:the )?next (?:step|phase|experiment)s? (?:is|are|will be|should be)?",
    r"future (?:work|experiments?) (?:will|should)",
    # "we recommend" is a proposal; a bare "the recommended dose was ..." is a
    # QUOTATION from a source, and treating it as a proposal made the rule fire on
    # faithful evidence records. Reader-directed recommendations of an amount are
    # caught by DIRECT_INSTRUCTION_PATTERNS instead.
    r"(?:we|i) recommend(?:ed|s|ing)? (?:that )?",
    r"it is recommended that (?:we|you|one|the reader)",
    r"(?:you|the reader|users?|the maintainer) (?:should|could|can|may)",
    r"(?:proposed|planned|suggested) (?:experiment|study|protocol|trial)",
    r"let(?:'s| us)",
    r"to test this,? (?:we|one)",
)

# Cues naming an action this project may never perform.
PROHIBITED_ACTION_CUES = (
    r"administer(?:ed|ing|s)?",
    r"dos(?:e|es|ed|ing)",
    r"inject(?:ed|ing|ion|s)?",
    r"infus(?:e|ed|ion)",
    r"gavage",
    r"recruit(?:ed|ing|ment|s)?",
    r"enrol(?:l)?(?:ed|ing|ment|s)?",
    r"randomis(?:e|ed|ing|ation)|randomiz(?:e|ed|ing|ation)",
    r"sacrific(?:e|ed|ing)",
    r"euthanis(?:e|ed)|euthaniz(?:e|ed)",
    r"cultur(?:e|ed|ing)\s+(?:cells?|neurons?|slices?|organoids?)",
    r"transfect(?:ed|ing|ion)?",
    r"electroporat(?:e|ed|ion)",
    r"stereotax(?:ic|ically)",
    r"implant(?:ed|ing|ation|s)?",
    r"perfus(?:e|ed|ion)",
    r"dissect(?:ed|ing|ion)?",
    r"western blot",
    r"patch[- ]clamp",
    r"in\s+vivo\s+(?:experiment|study|recording)s?",
    r"in\s+vitro\s+(?:experiment|assay|study)s?",
    r"ex\s+vivo\s+(?:experiment|preparation|study)s?",
    r"animal (?:experiment|study|work|model)s?",
    r"(?:human|clinical) (?:trial|experiment|study) (?:of|in|on)",
    r"self[- ]experiment(?:ation|ing|s)?",
    r"self[- ]administer(?:ing|ed)?",
    r"(?:take|taking|took|supplement(?:ing|ed)?) (?:it|this|the compound|the drug)",
    r"biopsy|biopsies",
    r"blood draw|venepuncture|venipuncture",
    r"knock(?:ing)?[- ]?(?:out|down) (?:the |this )?(?:gene|mice|mouse|animals?)",
)

# Reader-directed instructions: prohibited whatever the framing.
#
# Every pattern here requires a DIRECTIVE, not merely a quantity. A faithful evidence
# record quotes published doses constantly ("the effective dose was 140 mg/kg", "5 to
# 100 mg improved performance"), and flagging those would make the rule unusable and
# would push agents to launder their statements. So a bare quantity-plus-unit near a
# temporal word is NOT a finding, and "effective/suggested dose" is descriptive prose
# about somebody else's study. What IS a finding is an instruction to a reader.
DIRECT_INSTRUCTION_PATTERNS = (
    # an ingestion/administration verb aimed at a reader, with an amount
    r"\b(?:take|takes|taking|consume|consuming|ingest|ingesting|inject|injecting|apply|"
    r"applying|administer|administering|supplement\s+with)\b[^.]{0,40}"
    r"\b[0-9]+(?:\.[0-9]+)?\s*(?:mg|g|mcg|µg|ug|ml|mL|iu|IU)\b",
    # a recommendation of an amount, which is a protocol however it is phrased
    r"\b(?:recommended|advised|prescribed)\s+(?:daily\s+)?dos(?:e|age|ing)\b",
    r"\b(?:you|the reader|users?|the maintainer)\s+(?:should|must|can|could|may)\b"
    r"[^.]{0,60}\b(?:take|consume|ingest|inject|administer|dose|dosing)\b",
    r"\bstack(?:ing)?\s+(?:with|of)\b[^.]{0,40}\b(?:mg|g|dose|doses)\b",
    r"\bhow (?:to|much) (?:take|dose|source|obtain|buy)\b",
    r"\bwhere to (?:buy|source|obtain|get)\b",
)

# Record fields that hold VERBATIM source or database text. A dose quoted there is
# faithful evidence recording, not an instruction, so the reader-directed check is not
# applied to them. The proposal check still is: nobody quotes a source proposing that
# THIS project run an experiment.
VERBATIM_FIELD_SUFFIXES: tuple[str, ...] = (
    "/effect_size/as_reported",
    "/sample_size/reported_as",
    "/population",
    "/endpoint",
    "/registry_title",
    "/identifier_provenance",
    "/mechanism_as_reported",
)

# Computational verbs that make a nearby prohibited-action word descriptive rather than
# proposing. "We will analyse the published dose-response data" is computational.
EXCULPATORY_CUES = (
    r"analys(?:e|ed|es|ing|is)",
    r"analyz(?:e|ed|es|ing)",
    r"review(?:ed|ing|s)?",
    r"ingest(?:ed|ing|s)?\s+(?:as\s+)?(?:evidence|data|records?)",
    r"extract(?:ed|ing|s)?",
    r"curat(?:e|ed|ing|ion)",
    r"synthesis(?:e|ed|ing)?|synthesiz(?:e|ed|ing)?",
    r"model(?:led|ing|s)?\s+(?:computationally|in silico)",
    r"in\s+silico",
    r"simulat(?:e|ed|ing|ion)",
    r"published|reported|literature|meta[- ]analys",
    r"computational(?:ly)?",
    r"never|no\s+(?:dose|route|regimen|protocol)|forbidden|prohibited|must not|may not",
)

_PROPOSAL_RE = re.compile("|".join(PROPOSAL_CUES), re.IGNORECASE)
_PROHIBITED_RE = re.compile("|".join(PROHIBITED_ACTION_CUES), re.IGNORECASE)
_INSTRUCTION_RE = re.compile("|".join(DIRECT_INSTRUCTION_PATTERNS), re.IGNORECASE)
_EXCULPATORY_RE = re.compile("|".join(EXCULPATORY_CUES), re.IGNORECASE)

# How close a proposal cue and a prohibited action cue must be, in characters, to count
# as one statement. Roughly one sentence.
PROXIMITY_WINDOW = 160


def scan_text(text: str, *, verbatim: bool = False) -> list[tuple[str, str]]:
    """Find prohibited-work proposals in ``text``.

    Returns ``(finding_kind, quoted_excerpt)`` pairs, where ``finding_kind`` is
    ``proposes_prohibited_work`` or ``reader_directed_instruction``. An empty list means
    the text did not trip any pattern — not that it is certainly clean.

    ``verbatim=True`` marks text copied from a source or a database record, which
    suppresses the reader-directed-instruction check: a published dose quoted in
    ``effect_size.as_reported`` is evidence, not a protocol.
    """
    findings: list[tuple[str, str]] = []
    if not text:
        return findings

    if not verbatim:
        for match in _INSTRUCTION_RE.finditer(text):
            findings.append(
                ("reader_directed_instruction", _excerpt(text, match.start(), match.end()))
            )

    for proposal in _PROPOSAL_RE.finditer(text):
        window_start = proposal.start()
        window_end = min(len(text), proposal.end() + PROXIMITY_WINDOW)
        window = text[window_start:window_end]
        action = _PROHIBITED_RE.search(window)
        if action is None:
            continue
        if _EXCULPATORY_RE.search(window):
            # A computational verb in the same sentence makes this a description of
            # analysis, not a proposal to perform the action.
            continue
        findings.append(("proposes_prohibited_work", _excerpt(text, window_start, window_start + action.end())))
    return findings


def _excerpt(text: str, start: int, end: int, *, pad: int = 20) -> str:
    """A short quoted excerpt around a match, for the violation message."""
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    snippet = " ".join(text[left:right].split())
    prefix = "..." if left > 0 else ""
    suffix = "..." if right < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def iter_strings(record: Any, pointer: str = "") -> Iterator[tuple[str, str]]:
    """Yield ``(json_pointer, string)`` for every string leaf in a record."""
    if isinstance(record, str):
        yield pointer or "/", record
    elif isinstance(record, dict):
        for key, value in record.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from iter_strings(value, f"{pointer}/{escaped}")
    elif isinstance(record, list):
        for index, value in enumerate(record):
            yield from iter_strings(value, f"{pointer}/{index}")


def check_record(
    record: Any,
    *,
    path: str,
    record_id: str | None = None,
    root: Path | str | None = None,
) -> list[Violation]:
    """Apply rule V20 to one record: the ``action_type`` enum plus the text scan."""
    out: list[Violation] = []
    if isinstance(record, dict) and isinstance(record.get("action_type"), str):
        out.extend(
            check_action_type(
                record["action_type"],
                path=f"{path}#/action_type",
                record_id=record_id,
                root=root,
            )
        )
    for pointer, text in iter_strings(record):
        verbatim = pointer.endswith(VERBATIM_FIELD_SUFFIXES) or "/database_record/" in pointer
        for kind, excerpt in scan_text(text, verbatim=verbatim):
            if kind == "reader_directed_instruction":
                message = (
                    f"text reads as a dose, route or regimen directed at a reader: "
                    f"{excerpt!r}. This repository produces no dose, route, regimen or "
                    "protocol for anyone, including the maintainer "
                    "(docs/COMPUTATIONAL_ONLY_POLICY.md, rule V20)."
                )
            else:
                message = (
                    f"text reads as a PROPOSAL to perform prohibited work: {excerpt!r}. "
                    "This project performs no wet-lab, in-vitro, ex-vivo, animal or "
                    "human experiment. Describing somebody else's published experiment "
                    "is fine — say who did it, in the past tense, and record it as "
                    "evidence (rule V20)."
                )
            out.append(
                error("V20", f"{path}#{pointer}", message, record_id=record_id,
                      context={"finding": kind})
            )
    return out
