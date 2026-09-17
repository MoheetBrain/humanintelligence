"""Causal-integration ranking model (``agent:integration``).

An **evidence-accounting device**, not a causal estimator. It converts the ordinal
facet grades recorded by the domain atlases and the red team into six explicitly
uncalibrated dimensions, aggregates them under a declared subjective weighting,
applies un-tradeable gates, and reports a rank *interval* per target plus the facet
whose resolution would most reduce that interval.

Nothing in this package estimates a causal effect (see ``models/causal/README.md``),
and no output is a claim about biology, efficacy or safety, or a protocol, dose,
route or regimen (``docs/COMPUTATIONAL_ONLY_POLICY.md``).

Module map:

* :mod:`blueprint.ranking.inputs` — input types and the repository adapters
* :mod:`blueprint.ranking.rubric` — load and cross-validate the three spec files
* :mod:`blueprint.ranking.uncertainty` — Beta draws, quantiles, ranks, Kendall tau-b
* :mod:`blueprint.ranking.score` — dimensions, gates, composite, rank distribution
* :mod:`blueprint.ranking.information_gain` — what to resolve next
* :mod:`blueprint.ranking.convergence` — convergence and centrality over the graph
* :mod:`blueprint.ranking.report` — the CSV and its provenance sidecar
* :mod:`blueprint.ranking.cli` — the ``make rank`` entry point
"""

from __future__ import annotations

__all__ = ["MODEL_ID", "MODEL_VERSION"]

MODEL_ID = "ranking_spec_v0_1"
MODEL_VERSION = "0.1.0"
