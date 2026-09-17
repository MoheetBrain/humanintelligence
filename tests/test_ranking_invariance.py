"""Invariance properties the ranking model must have (contract P5).

"Paper count is not evidence quality" is a design commitment in README §4 and
contract P5. It is only real if it is tested, because the easiest way to build a
ranking model is to let evidence volume leak into the score. These tests attack that
from both directions: duplicated sources must not move anything, and a pile of weak
claims must not beat a few strong ones.
"""

from __future__ import annotations

import pytest

from blueprint.ranking.rubric import load_model_spec
from blueprint.ranking.score import independent_source_count, score_cohort
from blueprint.ranking.synthetic import ALL_FACETS, claim, make_inputs, make_target

DRAWS = 3000


@pytest.fixture(scope="module")
def spec():
    return load_model_spec()


def _ranks(inputs, spec):
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    return {tid: summary.rank_median for tid, summary in result.ranks.items()}


def _composites(inputs, spec):
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    return {t.target_id: t.composite_median for t in result.targets}


# ---------------------------------------------------------------------------
# Duplicated evidence
# ---------------------------------------------------------------------------


def test_duplicating_a_source_within_a_claim_changes_nothing(spec) -> None:
    """The same source id repeated inside one claim's evidence list.

    This is the shape a careless curation run produces: five evidence items on one
    claim, all pointing at the same paper.
    """
    targets = [
        make_target(
            "TGT:ALPHA",
            levels={"mechanistic_causal_perturbation": 3, "tractability": 2},
            claim_refs={"mechanistic_causal_perturbation": ["CLM:x:001"]},
        ),
        make_target("TGT:BETA", levels={"mechanistic_causal_perturbation": 2}),
    ]
    single = make_inputs(targets, [claim("CLM:x:001", ["SRC:PMID:1"])])
    duplicated = make_inputs(targets, [claim("CLM:x:001", ["SRC:PMID:1"] * 5)])

    assert _ranks(single, spec) == _ranks(duplicated, spec)
    assert _composites(single, spec) == _composites(duplicated, spec)

    target = targets[0]
    assert independent_source_count(single, target) == (1, 1)
    assert independent_source_count(duplicated, target) == (1, 1)


def test_adding_claims_that_cite_the_same_source_changes_no_rank(spec) -> None:
    """N extra claims, all citing one already-cited paper.

    ``independent_source_count`` must stay at 1 while ``claim_count`` grows, and no
    rank may move. The growing gap between the two columns is the report's way of
    showing a target leaning on very few independent observations.
    """
    base_refs = ["CLM:x:001"]
    padded_refs = [f"CLM:x:{n:03d}" for n in range(1, 8)]

    def cohort(refs):
        return make_inputs(
            [
                make_target(
                    "TGT:ALPHA",
                    levels={"mechanistic_causal_perturbation": 3},
                    claim_refs={"mechanistic_causal_perturbation": refs},
                ),
                make_target("TGT:BETA", levels={"mechanistic_causal_perturbation": 3}),
                make_target("TGT:GAMMA", levels={"mechanistic_causal_perturbation": 1}),
            ],
            [claim(ref, ["SRC:PMID:1"]) for ref in refs],
        )

    lean = cohort(base_refs)
    padded = cohort(padded_refs)

    assert _ranks(lean, spec) == _ranks(padded, spec)

    lean_result = score_cohort(lean, spec, n_draws=DRAWS)
    padded_result = score_cohort(padded, spec, n_draws=DRAWS)
    lean_row = next(t for t in lean_result.targets if t.target_id == "TGT:ALPHA")
    padded_row = next(t for t in padded_result.targets if t.target_id == "TGT:ALPHA")

    assert (lean_row.claim_count, lean_row.independent_source_count) == (1, 1)
    assert (padded_row.claim_count, padded_row.independent_source_count) == (7, 1)
    assert lean_row.composite_median == padded_row.composite_median


def test_independent_source_count_counts_distinct_sources_only(spec) -> None:
    """Three claims across two papers is two independent sources, not three."""
    target = make_target(
        "TGT:ALPHA",
        levels={"mechanistic_causal_perturbation": 3, "adult_onset_perturbation": 2},
        claim_refs={
            "mechanistic_causal_perturbation": ["CLM:a:001", "CLM:a:002"],
            "adult_onset_perturbation": ["CLM:a:003"],
        },
    )
    inputs = make_inputs(
        [target],
        [
            claim("CLM:a:001", ["SRC:PMID:1"]),
            claim("CLM:a:002", ["SRC:PMID:1", "SRC:PMID:2"]),
            claim("CLM:a:003", ["SRC:PMID:2"]),
        ],
    )
    assert independent_source_count(inputs, target) == (2, 3)


def test_unresolvable_claim_references_do_not_inflate_the_source_count(spec) -> None:
    """A claim id that resolves to nothing contributes no sources.

    The gap between ``claim_count`` and ``independent_source_count`` makes the
    dangling reference visible instead of letting it pass as evidence.
    """
    target = make_target(
        "TGT:ALPHA",
        levels={"mechanistic_causal_perturbation": 3},
        claim_refs={"mechanistic_causal_perturbation": ["CLM:missing:001", "CLM:a:001"]},
    )
    inputs = make_inputs([target], [claim("CLM:a:001", ["SRC:PMID:1"])])
    assert independent_source_count(inputs, target) == (1, 2)


def test_counter_claim_references_count_toward_independent_sources(spec) -> None:
    """Counter-evidence is evidence: its sources count toward the target's
    independent source base, because they are independent observations about it."""
    target = make_target(
        "TGT:ALPHA",
        levels={"mechanistic_causal_perturbation": 3},
        counter_levels={"mechanistic_causal_perturbation": 2},
        claim_refs={"mechanistic_causal_perturbation": ["CLM:a:001"]},
        counter_claim_refs={"mechanistic_causal_perturbation": ["CLM:a:002"]},
    )
    inputs = make_inputs(
        [target],
        [claim("CLM:a:001", ["SRC:PMID:1"]), claim("CLM:a:002", ["SRC:PMID:2"])],
    )
    assert independent_source_count(inputs, target) == (2, 2)


# ---------------------------------------------------------------------------
# Paper count
# ---------------------------------------------------------------------------


def test_many_weak_claims_do_not_outrank_few_strong_ones(spec) -> None:
    """Levels fixed, volume varied: volume must lose.

    ``TGT:VOLUME`` has every facet graded at level 1 and cites ten claims per facet
    (150 claim references over 150 distinct papers). ``TGT:QUALITY`` has every facet
    graded at level 3 and cites one claim per facet. Quality must rank ahead.
    """
    volume_refs = {
        facet: [f"CLM:vol:{facet}:{n:02d}" for n in range(10)] for facet in ALL_FACETS
    }
    quality_refs = {facet: [f"CLM:qual:{facet}"] for facet in ALL_FACETS}

    claims = [
        claim(ref, [f"SRC:PMID:{abs(hash(ref)) % 10**7}"])
        for refs in volume_refs.values()
        for ref in refs
    ]
    claims += [claim(ref, [f"SRC:PMID:9{n:06d}"]) for n, refs in enumerate(quality_refs.values()) for ref in refs]

    inputs = make_inputs(
        [
            make_target(
                "TGT:VOLUME",
                levels=dict.fromkeys(ALL_FACETS, 1),
                claim_refs=volume_refs,
            ),
            make_target(
                "TGT:QUALITY",
                levels=dict.fromkeys(ALL_FACETS, 3),
                claim_refs=quality_refs,
            ),
        ],
        claims,
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    ranks = {tid: s.rank_median for tid, s in result.ranks.items()}
    assert ranks["TGT:QUALITY"] < ranks["TGT:VOLUME"]

    rows = {t.target_id: t for t in result.targets}
    assert rows["TGT:VOLUME"].independent_source_count > rows["TGT:QUALITY"].independent_source_count
    assert rows["TGT:VOLUME"].composite_median < rows["TGT:QUALITY"].composite_median


def test_evidence_volume_is_absent_from_the_score_entirely(spec) -> None:
    """Strongest form of the property: two targets with identical levels and wildly
    different citation volumes must have identical composites, not merely the same
    ordering."""
    inputs = make_inputs(
        [
            make_target(
                "TGT:A",
                levels=dict.fromkeys(ALL_FACETS, 2),
                claim_refs={facet: [f"CLM:a:{facet}:{n}" for n in range(20)] for facet in ALL_FACETS},
            ),
            make_target("TGT:B", levels=dict.fromkeys(ALL_FACETS, 2)),
        ],
        [
            claim(f"CLM:a:{facet}:{n}", [f"SRC:PMID:{n}"])
            for facet in ALL_FACETS
            for n in range(20)
        ],
    )
    result = score_cohort(inputs, spec, n_draws=DRAWS)
    rows = {t.target_id: t for t in result.targets}
    # Different random streams per target id, so compare to Monte Carlo tolerance.
    assert rows["TGT:A"].composite_median == pytest.approx(rows["TGT:B"].composite_median, abs=0.01)
    assert rows["TGT:A"].independent_source_count == 20
    assert rows["TGT:B"].independent_source_count == 0
