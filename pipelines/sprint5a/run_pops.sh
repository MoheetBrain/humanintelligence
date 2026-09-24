#!/usr/bin/env bash
# Sprint 5A, Goal B — PoPS (Weeks et al. 2023) on Davies 2018 general cognition, leave-one-chromosome-out.
#
# PoPS is an ORTHOGONAL, GENOME-WIDE gene-prioritisation layer: it regresses MAGMA gene z-scores on ~57k
# gene features (expression, single-cell, pathways, PPI) and scores every gene by its features. It is NOT
# local causal evidence and must NOT be counted as a variant-to-gene vote in the Sprint-5 evidence matrix.
#
# Environment: conda env hi-pops (python 3.9, numpy 1.21.6, pandas 1.3.5, scipy 1.7.3, scikit-learn 0.24.2 —
# scikit-learn pinned to PoPS' requirements.txt; numpy/pandas/scipy are the closest osx-arm64 builds).
# Code: FinucaneLab/pops @ 76eb86c (GPL-3.0). Features: PoPS.features.txt.gz (57,742 features; see
# data/raw/sprint5a/pops/PROVENANCE.json). MAGMA: our Davies 10-kb MAGMA v1.10 results re-keyed to Ensembl.
#
# LOCO: for chromosome k, feature selection, covariate projection and ridge training use genes on the other
# 21 autosomes only; the PoPS score of a gene on chromosome k is taken from the model that never saw chr k.
# All other settings are PoPS defaults (feature_selection_p_cutoff 0.05, RidgeCV 25 alphas, MAGMA covariates
# projected out, MAGMA error covariance used, HLA removed, control features = features_jul17_control.txt).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
# BLAS: chr1-5 ran in env hi-pops (OpenBLAS 0.3.25). From chr6 on (2026-09-24 ~10:50Z) env hi-pops-accel (identical
# python/numpy/pandas/scipy/scikit-learn versions, Apple Accelerate BLAS/LAPACK), ~2.5-3x faster per thread; it
# reproduces PoPS' shipped example output to 4e-15 and chr1 is re-run in both envs as a direct check.
PY="${POPS_PY:-/opt/homebrew/Caskroom/miniforge/base/envs/hi-pops-accel/bin/python}"
POPS="$REPO/data/interim/sprint5a/tools/pops"
W="$REPO/data/interim/sprint5a/pops"
FEAT="$W/features_munged/pops_features"
# Resource cap (coordinator, 2026-09-24): at most 3 threads/processes for PoPS while MAGMA calibration runs.
# Default = 1 chromosome at a time with 3 BLAS/OpenMP threads. Each pops.py holds ~10 GB (dense 17.5k x 17.5k
# MAGMA error covariance + its whitening + 18k x ~13k selected features); 3 in parallel swapped heavily.
PAR="${PARALLEL:-1}"
export OMP_NUM_THREADS="${POPS_THREADS:-3}" OPENBLAS_NUM_THREADS="${POPS_THREADS:-3}" \
       MKL_NUM_THREADS="${POPS_THREADS:-3}" VECLIB_MAXIMUM_THREADS="${POPS_THREADS:-3}"

[ -f "$W/davies2018_10kb_ensg.genes.raw" ] || "$PY" "$REPO/pipelines/sprint5a/pops_prep.py" magma
[ -f "$FEAT.rows.txt" ] || "$PY" "$REPO/pipelines/sprint5a/pops_prep.py" features
NCH=$(ls "$FEAT".mat.*.npy | wc -l | tr -d ' ')
mkdir -p "$W/loco"

run_chr() {
  k=$1
  # resume: a chromosome is complete only when .marginals (written last) exists and .preds has all 18,383 genes
  if [ -f "$W/loco/chr$k.marginals" ] && [ "$(wc -l < "$W/loco/chr$k.preds")" -eq 18384 ]; then return 0; fi
  rm -f "$W/loco/chr$k".{preds,coefs,marginals}
  others=$(for c in $(seq 1 22); do [ "$c" != "$k" ] && printf "%s " "$c"; done)
  "$PY" "$POPS/pops.py" \
    --gene_annot_path "$POPS/example/data/utils/gene_annot_jun10.txt" \
    --feature_mat_prefix "$FEAT" --num_feature_chunks "$NCH" \
    --magma_prefix "$W/davies2018_10kb_ensg" \
    --control_features_path "$POPS/example/data/utils/features_jul17_control.txt" \
    --project_out_covariates_chromosomes $others \
    --feature_selection_chromosomes $others \
    --training_chromosomes $others \
    --random_seed 42 --verbose \
    --out_prefix "$W/loco/chr$k" > "$W/loco/chr$k.log" 2>&1
}
export -f run_chr; export PY POPS W FEAT NCH
seq 1 22 | xargs -P "$PAR" -I{} bash -c 'run_chr {}'

"$REPO/.venv/bin/python" "$REPO/pipelines/sprint5a/pops_collect.py"
