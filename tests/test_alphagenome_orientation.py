"""Regression for the sign-squared defect found during the public release audit."""
import numpy as np
import pandas as pd
import pytest
from pipelines.sprint5a.alphagenome_summarise import summarise

@pytest.mark.parametrize("raw_score,increasing,expected", [
    (2., "G", "UP"), (-2., "G", "DOWN"), (2., "A", "DOWN"), (-2., "A", "UP"),
    (0., "G", "NA"),
])
def test_signed_score_is_oriented_exactly_once(raw_score, increasing, expected):
    base = dict(rsid="rs_test", gene_name="TEST", ref="A", alt="G", raw_score=raw_score,
                quantile_score=.999, brain_tier="BRAIN", biosample_name="brain", assay="test",
                histone_mark=np.nan, transcription_factor=np.nan, track_name="feature")
    raw = pd.DataFrame([{**base, "scorer": s} for s in ["RNA_SEQ", "ATAC", "AVI_SCORE", "AVI_SCORE_FEATURE_IMPORTANCE"]])
    pred, var = summarise(raw, "regression", {"rs_test": increasing})
    signed = pred[pred.modality.isin(["EXPRESSION_RNA_SEQ", "CHROMATIN"])]
    assert set(signed.direction_cognition_allele) == {expected}
    assert var.top_expression_direction.iloc[0] == expected


def test_gene_graph_cannot_consume_unvalidated_historical_agreement():
    from pathlib import Path
    text = (Path(__file__).parents[1] / "pipelines/sprint5/build_evidence_graph.py").read_text()
    assert 'pd.read_csv(agv)' not in text
    assert 'UNRESOLVED_DIRECTION_AGGREGATION' in text
