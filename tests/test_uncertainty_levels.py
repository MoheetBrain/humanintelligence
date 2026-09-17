"""Tests for the level -> Beta mapping and the properties the spec claims for it.

``models/uncertainty/uncertainty_spec_v0_1.yaml`` asserts several properties in prose
(monotone means, ``not_assessed`` widest, counter-evidence lowering and narrowing,
"tested and contradicted" below "nothing found"). Prose assertions rot. These tests
turn each of them into a check against the file as loaded, so editing the
pseudo-counts without thinking breaks the build instead of quietly changing what the
model means.
"""

from __future__ import annotations

import numpy as np
import pytest

from blueprint.ranking.rubric import LEVELS, SpecError, load_model_spec
from blueprint.ranking.uncertainty import beta_draws, quantile, rng_for

REPO_ROOT = None  # resolved by load_model_spec's default (the repository root)


@pytest.fixture(scope="module")
def spec():
    return load_model_spec(REPO_ROOT)


def _mean(spec, level, counter=None) -> float:
    alpha, beta = spec.beta_parameters(level, counter)
    return alpha / (alpha + beta)


def _variance(spec, level, counter=None) -> float:
    alpha, beta = spec.beta_parameters(level, counter)
    total = alpha + beta
    return (alpha * beta) / (total * total * (total + 1.0))


def test_every_level_and_not_assessed_has_beta_parameters(spec) -> None:
    for level in LEVELS:
        alpha, beta = spec.beta_parameters(level, None)
        assert alpha > 0 and beta > 0
    assert spec.beta_parameters(None, None) == (1.0, 1.0)


def test_not_assessed_is_the_uniform_prior(spec) -> None:
    """Contract P8: unknown is first-class. The maximum-entropy choice on [0,1] is
    Beta(1,1), which smuggles in no base rate."""
    assert spec.beta_parameters(None, None) == (1.0, 1.0)
    assert _mean(spec, None) == pytest.approx(0.5)


def test_means_increase_strictly_with_level(spec) -> None:
    means = [_mean(spec, level) for level in LEVELS]
    assert means == sorted(means)
    assert all(b > a for a, b in zip(means, means[1:], strict=False))


def test_not_assessed_is_strictly_the_widest_distribution(spec) -> None:
    """The mechanical form of "unknown widens rather than lowers"."""
    unknown = _variance(spec, None)
    for level in LEVELS:
        assert _variance(spec, level) < unknown


def test_not_assessed_does_not_outscore_moderate_evidence(spec) -> None:
    """Absence of assessment must not be rewarded above a genuine level 2."""
    assert _mean(spec, None) <= _mean(spec, 2)


def test_level_zero_is_narrower_than_not_assessed_but_lower(spec) -> None:
    """"Searched, nothing found" is real evidence: informative (narrower) and
    unfavourable (lower). Contract §5.2 forbids collapsing it into not_assessed."""
    assert _variance(spec, 0) < _variance(spec, None)
    assert _mean(spec, 0) < _mean(spec, None)


def test_higher_levels_are_narrower_from_level_one_up(spec) -> None:
    variances = [_variance(spec, level) for level in (1, 2, 3, 4)]
    assert all(b < a for a, b in zip(variances, variances[1:], strict=False))


def test_no_level_approaches_certainty(spec) -> None:
    """A level-4 grade must not read as near-certainty: replicated human results in
    this literature are routinely overturned."""
    assert _mean(spec, 4) < 0.9
    assert _mean(spec, 0) > 0.05


# ---------------------------------------------------------------------------
# counter_level
# ---------------------------------------------------------------------------


def test_counter_evidence_lowers_the_mean_monotonically(spec) -> None:
    means = [_mean(spec, 3, counter) for counter in LEVELS]
    assert all(b < a for a, b in zip(means, means[1:], strict=False))


def test_counter_evidence_narrows_as_well_as_lowers(spec) -> None:
    """"Tested and contested" is a different epistemic state from "unstudied", and
    must not look like it: contradiction adds information."""
    assert _variance(spec, 3, 3) < _variance(spec, 3, None)


def test_tested_and_contradicted_sits_below_nothing_found(spec) -> None:
    """The distinction the contract demands (§5.2): level 1 with strong counter
    evidence must score below level 0 with none."""
    assert _mean(spec, 1, 3) < _mean(spec, 0, None)


def test_counter_level_zero_is_not_the_same_as_absent(spec) -> None:
    """Both map to zero additional pseudo-counts in v0.1, which is a deliberate
    simplification worth pinning: "searched for contradicting evidence and found
    none" is currently treated as neutral, not as support."""
    assert spec.beta_parameters(3, 0) == spec.beta_parameters(3, None)


def test_counter_pseudo_counts_mirror_the_supporting_ladder(spec) -> None:
    """The spec claims counter-evidence uses the same ladder on the failure side."""
    supporting = [spec.beta_parameters(level, None)[0] - 1.0 for level in LEVELS]
    counter = [float(spec.counter_pseudo_counts[str(level)]) for level in LEVELS]
    assert supporting == counter


# ---------------------------------------------------------------------------
# The sampler agrees with the parameters
# ---------------------------------------------------------------------------


def test_sampled_medians_track_the_declared_ladder(spec) -> None:
    """The documented medians are not decoration: sampling must reproduce them."""
    medians = []
    for level in LEVELS:
        alpha, beta = spec.beta_parameters(level, None)
        draws = beta_draws(alpha, beta, 200_000, rng_for(spec.seed, f"level{level}"))
        medians.append(quantile(draws, 0.5))
    assert all(b > a for a, b in zip(medians, medians[1:], strict=False))

    declared = spec.raw["uncertainty"]["level_to_beta"]
    for level, sampled in zip(LEVELS, medians, strict=True):
        stated = float(declared[level]["median"])
        assert sampled == pytest.approx(stated, abs=0.005)


def test_sampled_widths_match_the_declared_standard_deviations(spec) -> None:
    declared = spec.raw["uncertainty"]["level_to_beta"]
    for key, level in [("not_assessed", None), *[(level, level) for level in LEVELS]]:
        alpha, beta = spec.beta_parameters(level, None)
        draws = beta_draws(alpha, beta, 200_000, rng_for(spec.seed, f"sd{key}"))
        assert float(np.std(draws)) == pytest.approx(float(declared[key]["sd"]), abs=0.005)


# ---------------------------------------------------------------------------
# The loader defends the ladder's properties
# ---------------------------------------------------------------------------


def test_loader_rejects_a_non_monotone_ladder(tmp_path, spec) -> None:
    """A spec edit that broke monotonicity must fail loudly at load time."""
    import shutil

    import yaml

    root = tmp_path / "repo"
    for name in ("rubric", "ranking", "uncertainty"):
        source = spec.paths[name]
        destination = root / _relpath(name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)

    path = root / _relpath("uncertainty")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["level_to_beta"][3]["alpha"] = 1  # make level 3 worse than level 2
    path.write_text(yaml.safe_dump(document), encoding="utf-8")

    with pytest.raises(SpecError, match="increase strictly with level"):
        load_model_spec(root)


def _relpath(name: str) -> str:
    return {
        "rubric": "models/ranking/facet_rubric_v0_1.yaml",
        "ranking": "models/ranking/ranking_spec_v0_1.yaml",
        "uncertainty": "models/uncertainty/uncertainty_spec_v0_1.yaml",
    }[name]
