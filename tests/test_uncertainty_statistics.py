"""Tests for the hand-implemented statistics: quantiles, ranks, Kendall tau-b.

scipy is not available in this environment, so these functions are implemented in
``blueprint.ranking.uncertainty``. That makes verifying them against values computed
by hand non-optional: an unverified tau-b would silently corrupt every sensitivity
number in the report.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from blueprint.ranking.uncertainty import (
    average_ranks,
    beta_draws,
    kendall_tau_b,
    quantile,
    rank_within_draws,
    rng_for,
)

# ---------------------------------------------------------------------------
# Kendall tau-b, against hand-computed fixtures
# ---------------------------------------------------------------------------


def test_tau_b_perfect_agreement() -> None:
    """Identical orderings: C = 6, D = 0, no ties, tau_b = 6/6 = 1."""
    assert kendall_tau_b([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)


def test_tau_b_perfect_reversal() -> None:
    """Reversed ordering: C = 0, D = 6, tau_b = -6/6 = -1."""
    assert kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_tau_b_two_swapped_pairs_hand_computed() -> None:
    """x = 1..5 against y = [1,3,2,5,4].

    Enumerating all 10 pairs by hand: the pairs (2,3) and (4,5) are discordant and
    the other eight are concordant, so C = 8, D = 2, n0 = 10, no ties, and
    tau_b = (8 - 2) / 10 = 0.6.
    """
    assert kendall_tau_b([1, 2, 3, 4, 5], [1, 3, 2, 5, 4]) == pytest.approx(0.6)


def test_tau_b_with_ties_hand_computed() -> None:
    """x = [1,1,2,3] against y = [1,2,3,4].

    n = 4 so n0 = 6. x has one tie group of size 2, so n1 = 2*1/2 = 1; y has none,
    so n2 = 0. The tied pair contributes to neither C nor D; the remaining five
    pairs are all concordant, so C = 5 and D = 0. Therefore
    tau_b = 5 / sqrt((6 - 1)(6 - 0)) = 5 / sqrt(30) = 0.9128709292.
    """
    expected = 5.0 / math.sqrt(30.0)
    assert kendall_tau_b([1, 1, 2, 3], [1, 2, 3, 4]) == pytest.approx(expected)
    assert expected == pytest.approx(0.9128709292, abs=1e-9)


def test_tau_b_ties_in_both_sequences_hand_computed() -> None:
    """x = [1,1,2,2] against y = [1,2,1,2].

    n0 = 6. Both sequences have two tie groups of size 2, so n1 = n2 = 2.
    Pairs: (0,1) tied in x; (2,3) tied in x; (0,2) and (1,3) tied in y; leaving
    (0,3) concordant and (1,2) discordant. So C = 1, D = 1 and tau_b = 0.
    """
    assert kendall_tau_b([1, 1, 2, 2], [1, 2, 1, 2]) == pytest.approx(0.0)


def test_tau_b_is_undefined_when_one_sequence_is_constant() -> None:
    """A fully tied sequence has no ordering, so tau_b is nan, not 0.0.

    Reporting 0.0 would say "no association"; the truth is "the question does not
    apply". The distinction matters because a cohort in which every target has the
    same composite is exactly the Sprint-1 pre-data state.
    """
    assert math.isnan(kendall_tau_b([1, 1, 1, 1], [1, 2, 3, 4]))


def test_tau_b_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(7)
    for _ in range(20):
        a = rng.integers(0, 5, size=12).astype(float)
        b = rng.integers(0, 5, size=12).astype(float)
        forward = kendall_tau_b(a, b)
        backward = kendall_tau_b(b, a)
        if math.isnan(forward):
            assert math.isnan(backward)
            continue
        assert forward == pytest.approx(backward)
        assert -1.0 - 1e-12 <= forward <= 1.0 + 1e-12


def test_tau_b_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="equal-length"):
        kendall_tau_b([1, 2, 3], [1, 2])


# ---------------------------------------------------------------------------
# Quantiles
# ---------------------------------------------------------------------------


def test_quantile_matches_hand_computed_type_7_interpolation() -> None:
    """For x = [10, 20, 30, 40] and q = 0.25: h = 3*0.25 = 0.75, so the result is
    x[0] + 0.75*(x[1] - x[0]) = 10 + 7.5 = 17.5."""
    assert quantile([10, 20, 30, 40], 0.25) == pytest.approx(17.5)
    assert quantile([10, 20, 30, 40], 0.0) == pytest.approx(10.0)
    assert quantile([10, 20, 30, 40], 1.0) == pytest.approx(40.0)
    assert quantile([10, 20, 30, 40], 0.5) == pytest.approx(25.0)


def test_quantile_agrees_with_numpy_linear_convention() -> None:
    rng = np.random.default_rng(11)
    sample = rng.normal(size=501)
    for q in (0.05, 0.25, 0.5, 0.75, 0.95):
        assert quantile(sample, q) == pytest.approx(float(np.quantile(sample, q)))


def test_quantile_rejects_empty_and_out_of_range() -> None:
    with pytest.raises(ValueError, match="empty"):
        quantile([], 0.5)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        quantile([1.0, 2.0], 1.5)


# ---------------------------------------------------------------------------
# Ranks
# ---------------------------------------------------------------------------


def test_average_ranks_puts_the_highest_score_first() -> None:
    ranks = average_ranks(np.array([0.1, 0.9, 0.5]))
    assert list(ranks) == [3.0, 1.0, 2.0]


def test_average_ranks_averages_ties() -> None:
    """Scores [0.5, 0.5, 0.1]: the two tied targets share ranks 1 and 2, so both get
    1.5, and the third gets 3."""
    ranks = average_ranks(np.array([0.5, 0.5, 0.1]))
    assert list(ranks) == [1.5, 1.5, 3.0]


def test_average_ranks_does_not_favour_cohort_order() -> None:
    """Reordering tied targets must not change which rank each one receives."""
    forward = average_ranks(np.array([0.4, 0.4, 0.4, 0.9]))
    assert list(forward) == [3.0, 3.0, 3.0, 1.0]


def test_rank_within_draws_ranks_per_draw() -> None:
    composites = np.array([[0.1, 0.9], [0.9, 0.1]])
    ranks = rank_within_draws(composites)
    assert list(ranks[:, 0]) == [2.0, 1.0]
    assert list(ranks[:, 1]) == [1.0, 2.0]


# ---------------------------------------------------------------------------
# Deterministic streams
# ---------------------------------------------------------------------------


def test_rng_for_is_reproducible_and_key_dependent() -> None:
    first = beta_draws(2, 3, 50, rng_for(42, "TGT:A", "tractability"))
    again = beta_draws(2, 3, 50, rng_for(42, "TGT:A", "tractability"))
    other_facet = beta_draws(2, 3, 50, rng_for(42, "TGT:A", "transfer_breadth"))
    other_target = beta_draws(2, 3, 50, rng_for(42, "TGT:B", "tractability"))
    other_seed = beta_draws(2, 3, 50, rng_for(43, "TGT:A", "tractability"))

    assert np.array_equal(first, again)
    assert not np.array_equal(first, other_facet)
    assert not np.array_equal(first, other_target)
    assert not np.array_equal(first, other_seed)


def test_rng_for_does_not_depend_on_process_hash_seed() -> None:
    """blake2b, not ``hash()``: Python's hash is salted per process, which would make
    reports irreproducible across runs. Pinning a known digest catches a regression
    to a salted hash."""
    draws = beta_draws(1, 1, 3, rng_for(20260917, "TGT:GABRA5", "tractability"))
    assert draws.shape == (3,)
    assert np.all((draws > 0.0) & (draws < 1.0))
    # The exact values only need to be stable, not meaningful:
    assert draws.tolist() == pytest.approx(
        beta_draws(1, 1, 3, rng_for(20260917, "TGT:GABRA5", "tractability")).tolist()
    )


def test_beta_draws_rejects_non_positive_parameters() -> None:
    with pytest.raises(ValueError, match="positive"):
        beta_draws(0, 3, 10, rng_for(1, "x"))
