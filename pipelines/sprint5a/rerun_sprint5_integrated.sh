#!/usr/bin/env bash
# Sprint 5A section 10/12 — rerun the FROZEN Sprint-5 classification chain (unchanged code and rules) on the
# Sprint-5A inputs: within-family lineage (Gate A), single-cell eQTL colocs, AlphaGenome agreeing with measured QTL.
# Sprint-5 inputs are staged (copied) into the 5A directories so Sprint-5 outputs are never modified.
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=reports/sprint5a/s5_integrated; DAT=data/sprint5a/s5_integrated
mkdir -p "$OUT/gene_dossiers" "$DAT"
cp reports/sprint5/*.csv reports/sprint5/*.parquet reports/sprint5/*.json "$OUT/" 2>/dev/null || true
cp reports/sprint5/gene_dossiers/*.md "$OUT/gene_dossiers/"
cp data/sprint5/*.csv data/sprint5/*.parquet data/sprint5/*.json "$DAT/"
export S5_OUT="$PWD/$OUT" S5_DATA="$PWD/$DAT" S5A_INTEGRATION=1 PYTHONPATH=src
for s in locus_confidence build_evidence_graph classify_genes write_sprint5_tables decide_sprint5; do
  echo "== $s"; .venv/bin/python pipelines/sprint5/$s.py > "$DAT/run_$s.log" 2>&1 || { echo "FAILED $s"; tail -20 "$DAT/run_$s.log"; exit 1; }
done
.venv/bin/python pipelines/sprint5a/compare_classes.py
