#!/usr/bin/env python3
"""Regression tests for the trait-eligibility guard on the generated facet rules.

Why this file exists
--------------------
`atlases/alphacognition/cognitive_trait_panel.yaml` marked "mathematical ability"
(EFO_0004875) as `use_in_ranking: supporting` with the explicit note that it is "never a
stand-alone basis for a facet level". `build_assessments.py` branched on `phenotype_class`
alone and never read `use_in_ranking`, so the guard was inert. The association records behind
that trait are "Self-reported math ability" and "Highest math class taken" from PMID 30038396
— a 1.1-million-person **educational attainment** GWAS — and they were awarding
fluid-reasoning-grade facet levels. That is the
`educational_attainment_mistaken_for_intelligence` failure that principle P4 exists to block,
and it survived because the guard lived in data while the decision lived in code.

The guard now lives in one function (`_common.trait_use` / `partition_by_eligibility`) and the
rules live in two pure functions (`build_assessments.genetic_association_level` /
`causal_attribution_level`). This file fails if any of them stops firing. The generated rule is
applied identically to 27 targets and 108 facet grades, so a systematic error in it replicates
silently: it needs a test, not a spot-check.

Run
---
    .venv/bin/python pipelines/alphacognition/test_facet_guardrails.py      # standalone
    .venv/bin/python -m pytest pipelines/alphacognition/test_facet_guardrails.py

It is in this agent's lane rather than under `tests/` because `docs/OWNERSHIP.yaml` assigns
`tests/**` to agent:ontology (with carve-outs only for agent:integration). Relocation under a
carve-out is requested in docs/blackboard/schema_change_requests/alphacognition-001.yaml.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _common import (  # type: ignore[import-not-found]  # noqa: E402
    REPO_ROOT,
    load_panel,
    partition_by_eligibility,
    trait_use,
)
from build_assessments import (  # type: ignore[import-not-found]  # noqa: E402
    causal_attribution_level,
    genetic_association_level,
)

# The exact record that got through: a fluid-reasoning-classed trait, marked `supporting`,
# whose reported trait is an educational-attainment item from an educational-attainment GWAS.
MATHS_ROW: dict[str, Any] = {
    "gene_symbol": "CRTC1",
    "efo_id": "EFO_0004875",
    "efo_label": "mathematical ability",
    "phenotype_class": "fluid_reasoning",
    "use_in_ranking": "supporting",
    "is_educational_attainment": False,
    "reported_trait": ["Self-reported math ability"],
    "pubmed_id": "30038396",
}
EA_ROW: dict[str, Any] = {
    "efo_label": "educational attainment",
    "phenotype_class": "educational_attainment",
    "use_in_ranking": "proxy_only",
    "is_educational_attainment": True,
}
INTELLIGENCE_ROW: dict[str, Any] = {
    "efo_label": "intelligence",
    "phenotype_class": "g_factor",
    "use_in_ranking": "primary",
    "is_educational_attainment": False,
}
MEMORY_ROW: dict[str, Any] = {
    "efo_label": "episodic memory",
    "phenotype_class": "episodic_memory",
    "use_in_ranking": "primary",
    "is_educational_attainment": False,
}
EMPTY = {
    "primary_direct": [],
    "primary_domain": [],
    "supporting_direct": [],
    "supporting_domain": [],
    "proxy": [],
    "eligible_other_class": [],
}


# ---------------------------------------------------------------- the guard itself ----
def test_trait_use_fails_closed() -> None:
    """An unknown or missing eligibility must be treated as `proxy_only`, never as permissive."""
    assert trait_use({}) == "proxy_only"
    assert trait_use({"use_in_ranking": None}) == "proxy_only"
    assert trait_use({"use_in_ranking": ""}) == "proxy_only"
    assert trait_use({"use_in_ranking": "primary_ish"}) == "proxy_only"
    assert trait_use({"use_in_ranking": "excluded"}) == "proxy_only"
    # and the three legal values survive round-tripping
    assert trait_use({"use_in_ranking": "primary"}) == "primary"
    assert trait_use({"use_in_ranking": "supporting"}) == "supporting"
    assert trait_use({"use_in_ranking": "proxy_only"}) == "proxy_only"


def test_partition_routes_by_use_not_by_phenotype_class() -> None:
    """A `supporting` fluid-reasoning trait must NOT land in the bucket that carries a grade."""
    part = partition_by_eligibility([MATHS_ROW])
    assert part["primary_direct"] == [], (
        "mathematical ability is `supporting`; routing it to primary_direct is the original bug"
    )
    assert part["supporting_direct"] == [MATHS_ROW]
    # a proxy_only trait must not reach any eligible bucket at all
    proxy_part = partition_by_eligibility([EA_ROW])
    assert proxy_part["proxy"] == [EA_ROW]
    assert not any(proxy_part[k] for k in ("primary_direct", "primary_domain", "supporting_direct", "supporting_domain"))


# ----------------------------------------------- supporting may never carry a level ----
def test_supporting_trait_alone_cannot_produce_a_facet_level() -> None:
    """THE REGRESSION. Old behaviour returned 3 here; the panel says it may never carry a level."""
    part = partition_by_eligibility([MATHS_ROW])
    level = genetic_association_level(part, has_l2g=False, has_any_catalogued=True)
    assert level == 1, f"a `supporting` trait alone produced level {level}; it may only corroborate"


def test_supporting_trait_may_corroborate_a_primary_trait() -> None:
    """Corroboration is allowed: the primary trait sets the level, the supporting one does not lower it."""
    primary_only = partition_by_eligibility([INTELLIGENCE_ROW])
    with_support = partition_by_eligibility([INTELLIGENCE_ROW, MATHS_ROW])
    assert genetic_association_level(primary_only, has_l2g=False, has_any_catalogued=True) == 3
    assert genetic_association_level(with_support, has_l2g=False, has_any_catalogued=True) == 3


def test_primary_single_domain_trait_gives_level_two_not_three() -> None:
    part = partition_by_eligibility([MEMORY_ROW])
    assert genetic_association_level(part, has_l2g=False, has_any_catalogued=True) == 2


# ------------------------------------ proxy_only may not contribute to the facet at all ----
def test_proxy_only_trait_cannot_contribute_to_an_intelligence_relevant_facet() -> None:
    part = partition_by_eligibility([EA_ROW])
    assert genetic_association_level(part, has_l2g=False, has_any_catalogued=True) == 1, (
        "educational attainment must not raise an intelligence-relevant facet above the "
        "weak/indirect floor"
    )
    # and it must never license causal_gene_attribution, however much of it there is
    l2g_part = partition_by_eligibility([EA_ROW, EA_ROW, EA_ROW])
    assert causal_attribution_level(EMPTY, l2g_part, has_coloc=False) == 0


def test_l2g_candidacy_on_supporting_or_proxy_traits_does_not_attribute_a_gene() -> None:
    """Resolving the gene behind an EA signal is not resolving an intelligence signal."""
    l2g_part = partition_by_eligibility([MATHS_ROW, EA_ROW])
    assert causal_attribution_level(EMPTY, l2g_part, has_coloc=False) == 0
    # with a genuine primary association present, positional attribution earns 1 and no more
    gwas_part = partition_by_eligibility([INTELLIGENCE_ROW])
    assert causal_attribution_level(gwas_part, l2g_part, has_coloc=False) == 1


def test_l2g_on_a_primary_trait_attributes_and_coloc_raises_it() -> None:
    l2g_part = partition_by_eligibility([INTELLIGENCE_ROW])
    assert causal_attribution_level(EMPTY, l2g_part, has_coloc=False) == 2
    assert causal_attribution_level(EMPTY, l2g_part, has_coloc=True) == 3


def test_nothing_found_is_level_zero_not_level_one() -> None:
    """`level: 0` means searched and found nothing; it must stay distinct from weak evidence."""
    assert genetic_association_level(EMPTY, has_l2g=False, has_any_catalogued=False) == 0
    assert causal_attribution_level(EMPTY, EMPTY, has_coloc=False) == 0


# -------------------------------------------- the panel and the code must not diverge ----
def test_every_panel_trait_declares_an_eligibility() -> None:
    """A trait with no `use_in_ranking` would be silently demoted; make it a visible failure."""
    missing = [t["efo_id"] for t in load_panel() if t.get("use_in_ranking") not in
               {"primary", "supporting", "proxy_only", "excluded"}]
    assert not missing, f"panel traits with no usable use_in_ranking: {missing}"


def test_educational_attainment_traits_are_all_proxy_only() -> None:
    """Contract P4 / §4.2: EA is never an intelligence endpoint, enforced at the panel level."""
    offenders = [
        t["efo_id"]
        for t in load_panel()
        if (t.get("is_educational_attainment") or t["phenotype_class"] == "educational_attainment")
        and t["use_in_ranking"] not in {"proxy_only", "excluded"}
    ]
    assert not offenders, f"educational-attainment traits not marked proxy_only: {offenders}"


def test_generated_assessments_contain_no_supporting_only_grade_above_one() -> None:
    """End-to-end: no shipped grade may rest solely on a `supporting` or `proxy_only` trait."""
    table = REPO_ROOT / "data" / "interim" / "gwas_catalog_associations.jsonl"
    l2g_table = REPO_ROOT / "data" / "interim" / "opentargets_l2g.jsonl"
    assess_dir = REPO_ROOT / "atlases" / "alphacognition" / "assessments"
    if not table.exists() or not assess_dir.exists():
        return  # nothing built yet; the unit tests above still constrain the rule
    rows = [json.loads(line) for line in table.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_gene: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_gene.setdefault(str(row["gene_symbol"]), []).append(row)
    # A primary signal can come from either table: the GWAS Catalog association sweep or Open
    # Targets locus-to-gene candidacy. Checking only the first would fail targets whose grade
    # legitimately rests on the second (GABRA5 is the live example).
    l2g_by_gene: dict[str, list[dict[str, Any]]] = {}
    if l2g_table.exists():
        for line in l2g_table.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for hit in row.get("seed_gene_l2g_hits") or []:
                l2g_by_gene.setdefault(str(hit["symbol"]), []).append(row)
    registry = yaml.safe_load((REPO_ROOT / "targets" / "seed_registry.yaml").read_text(encoding="utf-8"))
    for target in registry["targets"]:
        symbol = str(target["symbol"])
        genes = [str(m) for m in (target.get("member_genes") or [])] or [symbol]
        part = partition_by_eligibility([r for g in genes for r in by_gene.get(g, [])])
        l2g_part = partition_by_eligibility([r for g in genes for r in l2g_by_gene.get(g, [])])
        has_primary = any(
            bucket[key]
            for bucket in (part, l2g_part)
            for key in ("primary_direct", "primary_domain")
        )
        if has_primary:
            continue  # a primary trait is in evidence, so a grade above 1 is legitimate
        path = assess_dir / f"{symbol}.yaml"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for facet in doc["facets"]:
            if facet["facet"] in {"human_genetic_association", "causal_gene_attribution",
                                  "human_phenotype_specificity"}:
                assert (facet["level"] or 0) <= 1, (
                    f"{symbol}/{facet['facet']} is graded {facet['level']} but this target's only "
                    f"panel associations are supporting or proxy_only traits"
                )


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
