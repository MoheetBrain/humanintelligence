#!/usr/bin/env bash
# Reproduce the Sprint-4 joint gene/tissue fine-mapping (FOCUS) run end to end.
#
# Everything heavy lives under $SCRATCH (outside the repository). Only
#   reports/sprint4/joint_gene_tissue_finemapping.csv
#   data/sprint4/joint_gene_tissue_finemapping_provenance.json
# are written into the repository. At most 3 BLAS/OpenMP threads are used.
#
# The steps below are the ones executed on 2026-09-23 (individually, not as one invocation of
# this file); expected sha256 values are asserted so a changed upstream file stops the run.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRATCH="${SCRATCH:?set SCRATCH to a writable directory outside the repository}"
mkdir -p "$SCRATCH/weights" "$SCRATCH/gtexv8" "$SCRATCH/work"
export OMP_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3 MKL_NUM_THREADS=3 VECLIB_MAXIMUM_THREADS=3 \
       NUMEXPR_NUM_THREADS=3 DASK_SCHEDULER=synchronous

sha_check() { echo "$2  $1" | shasum -a 256 -c -; }

# 1. Isolated environment (python 3.10: pandas-plink on osx-arm64 has no py3.8 build).
if ! mamba env list | grep -q '^ *hi-focus '; then
  mamba create -y -n hi-focus -c conda-forge -c bioconda python=3.10 "numpy<1.24" "pandas<2" scipy \
    "sqlalchemy<1.4" "matplotlib>=3.1" seaborn pandas-plink py-opencv plink "setuptools<70" pip
  # pandas-plink 2.3 imports pandera; pandera >=0.20 requires pandas >=2.1 -> pin an older pandera.
  mamba install -y -n hi-focus -c conda-forge "pandera<0.20" "pandera-core<0.20"
  # only needed for `focus import ... fusion` (GTEx v8 FUSION weights)
  mamba install -y -n hi-focus -c conda-forge -c bioconda rpy2 mygene "pandas<2" "numpy<1.24" "sqlalchemy<1.4"
fi

# 2. FOCUS / MA-FOCUS source at the audited commit (maintained repo; bogdanlab/focus is deprecated).
if [ ! -d "$SCRATCH/ma-focus" ]; then
  git clone https://github.com/mancusolab/ma-focus.git "$SCRATCH/ma-focus"
fi
git -C "$SCRATCH/ma-focus" checkout -q f3a38fd70e7fa3f3c43a05c641201fdc45f1ab46
(cd "$SCRATCH/ma-focus" && mamba run -n hi-focus pip install --no-deps --no-build-isolation .)

# 3. Weights and annotation.
#    focus.db (497,758,208 bytes) = FOCUS authors' pre-built DB: GTEx v7 PrediXcan (48 tissues) +
#    CMC DLPFC / METSIM / NTR / YFS FUSION weights; link published on the ma-focus wiki.
[ -f "$SCRATCH/weights/focus.db" ] || \
  curl -sSL -o "$SCRATCH/weights/focus.db" "https://www.dropbox.com/s/ep3dzlqnp7p8e5j/focus.db?dl=1"
sha_check "$SCRATCH/weights/focus.db" 492a8a21ffdc0a1e05c1d15261d808f6f813ef0b4302072869bcf35760b0170f
#    GENCODE v38 lifted to GRCh37 (61,226,201 bytes; MD5 checked against the release MD5SUMS).
G=https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_38/GRCh37_mapping
[ -f "$SCRATCH/weights/gencode.v38lift37.annotation.gtf.gz" ] || \
  curl -sS -o "$SCRATCH/weights/gencode.v38lift37.annotation.gtf.gz" "$G/gencode.v38lift37.annotation.gtf.gz"
sha_check "$SCRATCH/weights/gencode.v38lift37.annotation.gtf.gz" \
  c0bc102ae79ebcf1144097d419d7dfa6672475c9a65a5e5b21a00d6212e74455
#    GTEx v8 EUR Brain_Cortex FUSION weights (220,442,096 bytes; ~10 min at the observed ~375 kB/s).
[ -f "$SCRATCH/gtexv8/GTExv8.EUR.Brain_Cortex.tar.gz" ] || \
  curl -sS -o "$SCRATCH/gtexv8/GTExv8.EUR.Brain_Cortex.tar.gz" \
    https://s3.us-west-1.amazonaws.com/gtex.v8.fusion/EUR/GTExv8.EUR.Brain_Cortex.tar.gz
sha_check "$SCRATCH/gtexv8/GTExv8.EUR.Brain_Cortex.tar.gz" \
  3f37aadc19f96ebae32be0c4a304e2d7ccf62911a38e75f13f438b2524adccb2

# 4. Pipeline: prepare -> import_v8 -> run -> collect.
cd "$REPO"
for st in prepare import_v8 run collect; do
  mamba run -n hi-focus python pipelines/sprint4/joint_gene_tissue/run_focus_loci.py \
    --workdir "$SCRATCH/work" --focus-db "$SCRATCH/weights/focus.db" \
    --gencode-lift37-gtf "$SCRATCH/weights/gencode.v38lift37.annotation.gtf.gz" \
    --gtexv8-cortex-archive "$SCRATCH/gtexv8/GTExv8.EUR.Brain_Cortex.tar.gz" \
    ${EXTRA_PROVENANCE:+--extra-provenance "$EXTRA_PROVENANCE"} --stage "$st"
done
