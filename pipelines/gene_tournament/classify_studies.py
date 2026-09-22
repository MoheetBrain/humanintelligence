#!/usr/bin/env python3
"""Sprint 3 — classify every study before any gene is allowed to count it.

The rule this enforces
----------------------
A study counts as **direct cognition evidence** only if it measured cognitive
performance in a general-population sample, as a single trait, without borrowing power
from educational attainment. Everything else is kept, labelled, and counted in a separate
column — never discarded silently and never summed into the direct count.

Tiers (assigned by explicit, auditable text rules; no judgement calls hidden in code)
------------------------------------------------------------------------------------
``direct_strict``
    Direct-cognition channel; none of the flags below.
``direct_mtag``
    Direct channel, but an MTAG analysis. MTAG borrows statistical power from genetically
    correlated traits -- in practice educational attainment and cognitive performance --
    so a hit may be carried by the EA input. Counted in the lenient tier only.
``direct_clinical_or_ageing``
    Direct channel, but measured in a clinical population, in an Alzheimer's/ageing
    pathology cohort, as decline/resilience/change, or as an interaction. These are real
    cognitive measurements answering a different question (what protects a failing brain,
    not what raises ability in a healthy one).
``excluded_ea_or_cross_trait``
    Filed under a direct-cognition EFO term but EA-derived (e.g. GenomicSEM "cognitive
    aspects of educational attainment") or a cross-trait/multivariate/pleiotropy scan.
    These are the leak that a trait-label filter cannot see.
``proxy``
    Educational attainment or clinical-composite channel. Never direct.

Cohort independence -- what can and cannot be said
--------------------------------------------------
The Catalog's ``cohort`` field is populated for 271 of 419 studies. UK Biobank is never
named in a sample description. So UKB participation can be CONFIRMED (``listed``) but
never EXCLUDED from these records; a study with no cohort field is ``unknown``, not
UKB-free. The ``exclude UKB`` kill test in Part P uses only studies whose cohort list is
present and lacks UKB -- the strict reading, which undercounts UKB-free evidence rather
than overcounting it.

An ``independence_unit`` is the sorted cohort list when present, else the PubMed ID. It
is an UPPER BOUND on independent samples: two differently-labelled cohort sets can still
share people, and the Catalog cannot show it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "gene_tournament"
CHANNELS = REPO_ROOT / "atlases" / "gene_tournament" / "phenotype_channels.yaml"

RULES = {
    "mtag": r"\bMTAG\b",
    "ea_derived": r"educational|education\b|schooling|years of school|college|"
                  r"cognitive aspects|non-?cognitive",
    # Only explicit multi-trait designs. A bare "or" is handled separately below, AFTER
    # the clinical check, because "cognition in schizophrenia or bipolar disorder" joins
    # two POPULATIONS (a clinical study), not two TRAITS (a cross-trait scan).
    "multitrait_design": r"multivariate|pleiotrop|multiple traits|shared genetic|"
                         r"genomic sem|common factor|\bfactor\b",
    "bare_or": r"\bor\b",
    "clinical_population": r"schizophren|bipolar|psychos|alzheimer|dementia|\bMCI\b|"
                           r"mild cognitive impairment|parkinson|autis|ADHD|attention[- ]deficit|"
                           r"\bHIV\b|stroke|dyslexi|epilep|depress|multiple sclerosis|"
                           r"amyloid|\btau\b|apoe|down syndrome|22q11|delirium|cancer|chemotherapy",
    "decline_or_resilience": r"resilien|decline|change|slope|longitudinal|progression|"
                             r"conversion|trajector",
    "interaction": r"\bx\b|interaction|gene-environment|\bGxE\b",
}
PATHOLOGY_COHORTS = {"ADNI", "ROSMAP", "NACC", "MARS", "ACT", "A4", "EMIF", "ADSP",
                     "ADGC", "WRAP", "BIOCARD", "MAP", "ROS", "BLSA", "WHICAP"}
EA_DECOMPOSITION_PMIDS = {"33414549"}   # Demange 2021: cognitive/non-cognitive aspects of EA


def classify(row: dict, channel_class: dict[str, str], study_channels: set[str]) -> dict:
    # Trait rules read the TRAIT text only. Matching them against the sample description
    # was a bug found on audit: "... individuals or ..." in a sample string sent verbal
    # memory studies to the excluded tier.
    text = " ".join(str(row.get(k) or "") for k in ("reported_trait", "disease_trait"))
    flags = {name: bool(re.search(rx, text, re.I)) for name, rx in RULES.items()}
    if row.get("pubmed_id") in EA_DECOMPOSITION_PMIDS:
        flags["ea_derived"] = True
    cohorts = set(row.get("cohort") or [])
    flags["pathology_cohort"] = bool(cohorts & PATHOLOGY_COHORTS)
    flags["cases_in_sample"] = bool(re.search(r"\bcases\b", str(row.get("initial_sample_size") or ""), re.I))

    classes = {channel_class.get(c) for c in study_channels}
    if "direct_cognition" not in classes:
        tier = "proxy"
    elif flags["ea_derived"] or flags["multitrait_design"]:
        tier = "excluded_ea_or_cross_trait"
    elif (flags["clinical_population"] or flags["decline_or_resilience"] or flags["interaction"]
          or flags["pathology_cohort"] or flags["cases_in_sample"]):
        tier = "direct_clinical_or_ageing"
    elif flags["bare_or"]:
        tier = "excluded_ea_or_cross_trait"   # "trait A or trait B" in a healthy sample
    elif flags["mtag"]:
        tier = "direct_mtag"
    else:
        tier = "direct_strict"

    if not cohorts or cohorts <= {"NR", "other"}:
        ukb = "unknown"
    elif "UKB" in cohorts:
        ukb = "listed"
    else:
        ukb = "not_listed"
    real = sorted(cohorts - {"NR", "other"})
    unit = "COHORTS:" + "+".join(real) if real else f"PMID:{row.get('pubmed_id')}"
    return {"tier": tier, "ukb_status": ukb, "independence_unit": unit,
            **{f"flag_{k}": v for k, v in flags.items()}}


def main() -> int:
    import glob, gzip
    spec = yaml.safe_load(CHANNELS.read_text(encoding="utf-8"))
    trait_to_channel = {e: ch for ch, b in spec["channels"].items() for e in b["traits"]}
    channel_class = {c: k for k, b in spec["evidence_classes"].items() for c in b["channels"]}

    study_channels: dict[str, set[str]] = {}
    for path in glob.glob(str(REPO_ROOT / "data/raw/gwas_catalog_tournament/*/EFO_*.json.gz")):
        for a in (json.loads(gzip.open(path, "rt").read()).get("_embedded") or {}).get("associations") or []:
            for t in a.get("efo_traits") or []:
                ch = trait_to_channel.get(t.get("efo_id"))
                if ch:
                    study_channels.setdefault(a.get("accession_id"), set()).add(ch)

    meta = [json.loads(l) for l in (DATA / "study_metadata.jsonl").open(encoding="utf-8")]
    out = []
    for row in meta:
        chans = study_channels.get(row["accession_id"], set())
        out.append({"accession_id": row["accession_id"], "pubmed_id": row.get("pubmed_id"),
                    "first_author": row.get("first_author"),
                    "reported_trait": row.get("reported_trait"),
                    "initial_sample_size": row.get("initial_sample_size"),
                    "cohort": "|".join(row.get("cohort") or []),
                    "channels": "|".join(sorted(chans)),
                    **classify(row, channel_class, chans)})
    frame = pd.DataFrame(out)
    frame.to_csv(DATA / "study_classification.csv", index=False)
    print(frame.tier.value_counts().to_string())
    print("\nUKB status:", frame.ukb_status.value_counts().to_dict())
    print("independence units among direct_strict:",
          frame[frame.tier == "direct_strict"].independence_unit.nunique(),
          "of", int((frame.tier == "direct_strict").sum()), "studies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
