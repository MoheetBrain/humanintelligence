#!/usr/bin/env python3
"""Sprint 3 — developmental-versus-adult classification of the protein-coding genome.

Why this file exists
====================
A gene can rank near the top for *explaining natural variation* in a cognitive trait and
near the bottom as an *adult intervention target*, because the window in which it acts has
already closed. ``GRIN2B`` and ``DCC`` are the canonical worry: both are heavily
implicated in cognitive phenotypes, and both are transcriptionally front-loaded onto fetal
brain development. A ranking that cannot tell those genes apart from a gene that is
transcriptionally busy in the adult cortex is producing one number where two are required.

This script builds the artefact that separates the two rankings. It produces one row per
HGNC-approved protein-coding gene and assigns a ``developmental_class`` from **explicit
thresholds on two independent datasets whose numbers are never merged**.

Output: ``data/gene_tournament/developmental_classification.parquet``


What the two datasets are, and why their numbers are kept apart
===============================================================
**GTEx v10** (adult, bulk, **TPM**, GENCODE **v39**, GRCh38). 13 brain tissues, median TPM
per tissue across donors. Donor ages are released only as 10-year brackets; in the v10
subject annotation those brackets run ``20-29`` through ``70-79``. GTEx documents its
donor population as adults aged 20-70, so the ``70-79`` bracket holds donors at the 70
boundary. **There are no paediatric and no prenatal donors in GTEx**, which is exactly why
a second dataset is required.

**BrainSpan Developmental Transcriptome** (prenatal -> 40 yr, bulk, **RPKM**, GENCODE
**v10**, RNA-Seq summarised to genes). 524 samples, 42 donors, 26 named structures.

These are different quantification units (TPM vs RPKM), different GENCODE annotations
(v39 vs v10), different library preparations, and different post-mortem pipelines. A TPM
and an RPKM for the same gene are **not** comparable, and a ratio taken across the two
datasets would be an artefact of the annotation and the normalisation, not of biology.
So:

* Every **developmental** contrast (prenatal vs postnatal, the ``log2`` ratios, the peak
  window) is computed **entirely inside BrainSpan**, in RPKM.
* Every **adult expression** statement (``adult_expressed``, ``adult_brain_max_tpm``, the
  per-tissue columns) is computed **entirely inside GTEx**, in TPM.
* The two are combined only as *logical* conditions (AND / OR of booleans), never as a
  shared numeric scale. No column in the output is a function of both a TPM and an RPKM.


Four methodological points that are built into the artefact, not merely noted
============================================================================
**1. "Adult-expressed" is necessary but nowhere near sufficient for "adult-modifiable".**
``adult_expressed`` says one thing only: a transcript for this gene is detectable in adult
post-mortem brain tissue. It says nothing about whether the protein is made, whether it is
in a cell type that matters, whether its function is still plastic, whether a ligand or a
molecule can reach it, or whether changing it in an adult would change anything at all.
Most of the genome is "adult-expressed" by this definition. The column is a *filter that
removes obviously hopeless targets*, not evidence for a viable one. Downstream code must
not treat ``adult_expressed == True`` as a positive signal for tractability. This is
recorded in the artefact itself as ``adult_expressed_is_necessary_not_sufficient`` in the
summary JSON so the caveat travels with the data.

**2. BrainSpan's adult coverage is thin and its adolescent coverage is thinner.** The
per-window donor counts are computed and written out (``brainspan_window_counts``). The
adult window rests on 6 donors and the adolescent window on 4. Any class whose *decisive
contrast* depends on the adolescent or adult window therefore has its
``classification_confidence`` capped at ``medium`` — ``ADOLESCENT`` and ``ADULT_DYNAMIC``
can never be ``high`` in this build. That is a deliberate structural cap, not a per-gene
judgement.

**3. Bulk tissue expression is not cell-type expression.** Every number here is an average
over a homogenate. A gene transcribed at high level in 1% of cells is indistinguishable
from a gene transcribed at low level in every cell. Interneuron-restricted and
glia-restricted genes are systematically diluted; a gene can be called ``MIXED`` here
purely because the cell-type composition of the tissue changes with age while the gene's
own per-cell expression does not. Nothing in this file can detect that. Resolving it
requires single-cell data and is out of scope.

**4. Structure composition changes with age, so the primary comparison controls for it.**
BrainSpan samples 26 structures, but 10 of them (``MGE``, ``LGE``, ``CGE``, ``URL``,
``DTH``, ``CB``, and the coarse prenatal dissections ``Ocx``, ``PCx``, ``TCx``,
``M1C-S1C``) exist **only in the prenatal window** — the ganglionic eminences and rhombic
lip are transient progenitor zones that have no postnatal counterpart. Pooling all
structures would credit progenitor-zone biology to "prenatal" as a time effect when it is
really an anatomy effect. The **primary** windows are therefore computed over the
**16 structures sampled in all four windows**; the all-structures variant is computed too
and reported as a sensitivity analysis (``sensitivity`` in the summary JSON).


Age windows — the exact mapping from BrainSpan's age strings
============================================================
BrainSpan age strings take three forms. They are converted to years-from-birth:

* ``"N pcw"`` post-conceptional weeks -> ``(N - 40) / 52`` years (negative = before birth;
  40 pcw is taken as term birth)
* ``"N mos"`` postnatal months        -> ``N / 12`` years
* ``"N yrs"`` postnatal years         -> ``N``

Windows (half-open, on years-from-birth ``y``):

* ``prenatal``         ``y <  0``    all 8-37 pcw samples
* ``early_postnatal``  ``0 <= y < 12``  4 mos - 11 yrs
* ``adolescent``       ``12 <= y < 20`` 13 - 19 yrs
* ``adult``            ``y >= 20``      21 - 40 yrs

The 12 and 20 year cut-points are conventional, not derived from the data; the 20 year
boundary is fixed by the brief. Sensitivity to them is reported.


The classification rules, verbatim
==================================
Let, **within BrainSpan only**, over the 16 common structures:

    P = mean RPKM over prenatal samples
    E = mean RPKM over early_postnatal samples
    D = mean RPKM over adolescent samples
    A = mean RPKM over adult samples
    peak_window = argmax(P, E, D, A)
    peak_value  = max(P, E, D, A)

    prenatal_adult_log2_ratio = log2((P + PSEUDOCOUNT) / (A + PSEUDOCOUNT))

with ``PSEUDOCOUNT = 0.1`` RPKM, which bounds the ratio for genes that are near zero in
one window and stops 0.001 vs 0.000 from producing an infinite fold change.

And, **within GTEx only**, over the 13 brain tissues:

    adult_brain_max_tpm    = max median TPM across the 13 tissues
    adult_brain_median_tpm = median of the 13 per-tissue median TPMs
    adult_expressed        = adult_brain_max_tpm >= 1.0

Thresholds (all arbitrary in the sense that they are conventions, not estimates; all
varied in the sensitivity analysis):

    DETECT_RPKM   = 1.0   a window mean at or above this counts as "expressed"
    STRONG_LOG2   = 1.0   a 2.0x contrast
    WEAK_LOG2     = 0.585 a 1.5x contrast
    TPM_EXPRESSED = 1.0   GTEx brain expression threshold

Assignment, in order; the first matching rule wins:

    R0  no row in GTEx AND no row in BrainSpan
            -> UNKNOWN, basis "no_expression_data"
            Absence of measurement is not a measurement.

    R1  row in GTEx but no row in BrainSpan
            -> UNKNOWN, basis "gtex_only_no_developmental_data"
            The adult value is kept and is usable, but no developmental trajectory was
            ever measured for this gene, so no developmental class can be honestly
            assigned. This is NOT the same as "no data" and is labelled differently.

    R2  row in BrainSpan, but peak_value < DETECT_RPKM
            -> UNKNOWN, basis "measured_below_detection_in_brain"
            The gene was measured across development and is off in every window. It has a
            measurement; it has no trajectory to classify.

    R3  log2((P+c)/(max(E,D,A)+c)) >= STRONG_LOG2
            -> PRENATAL_DOMINANT
            Prenatal mean is at least 2x every postnatal window.

    R4  not R3 AND log2((max(P,E)+c)/(max(D,A)+c)) >= WEAK_LOG2
            -> DEVELOPMENTAL
            The developmental side of life (fetal or childhood) exceeds the mature side
            (adolescent or adult) by at least 1.5x, but not by enough, or not
            specifically enough to the prenatal window, to be prenatal-dominant.

    R5  not R3,R4 AND peak_window == adolescent
        AND D >= 1.5x P AND D >= 1.5x E AND D >= 1.5x A
            -> ADOLESCENT
            A genuine adolescent-specific peak: higher than childhood on one side AND
            higher than adulthood on the other. Rare, and it should be rare.

    R6  not R3,R4,R5 AND log2((A+c)/(P+c)) >= WEAK_LOG2
            -> ADULT_DYNAMIC
            The adult level is at least 1.5x the prenatal level. Reached only after R4
            has already failed, i.e. the developmental side is NOT the heavier one.

    R7  anything else that is expressed
            -> MIXED
            Expressed somewhere, but neither side of life is heavier by the required
            margin: a flat trajectory. MIXED is the honest residual, not a dustbin — it
            means "measured, expressed, and genuinely not time-specific".

Why R6 is tested on ``A vs P`` and not on ``max(D,A) vs max(P,E)``
-----------------------------------------------------------------
Two earlier drafts of this rule were wrong, and known-biology positive controls caught
both. They are recorded here because the failure modes are instructive:

* **Draft 1 required ``peak_window == adult``.** ``MBP``, ``MOG``, ``GFAP`` and ``SYP``
  peak in the *adolescent* window — myelination runs well past childhood — and then
  plateau. They failed the adult-peak test and fell into MIXED despite prenatal-to-adult
  log2 ratios near -5.9. Plainly wrong.
* **Draft 2 made R6 the exact mirror of R4** (``max(D,A)`` vs ``max(P,E)``). That fixed
  the myelin genes but broke the very common "rises through childhood and stays up"
  shape: ``KCNJ3`` (4.4 -> 13.0 -> 13.5 -> 17.1 RPKM) and ``GABRA5`` have an
  early-postnatal value close to their adult value, so ``max(P,E) ~ max(D,A)`` and they
  collapsed into MIXED — even though ``KCNJ3`` is 3.9x higher in adult than prenatal.
  ADULT_DYNAMIC fell from 1,878 genes to 778, which is not credible.

``A vs P`` compares the two windows that are actually well anchored and furthest apart,
and it is only reached after R4 has already ruled out a developmentally-heavier profile,
so the precedence order does the work that a symmetric mirror could not. The asymmetry
between R4 and R6 is therefore deliberate: they answer different questions, and the
ordering makes the outcome deterministic.

``developmental_class`` is therefore never assigned by a score, a rank, or a model. Every
assignment is a conjunction of thresholded comparisons that can be recomputed by hand from
the columns in the output file.


classification_confidence
=========================
    none    every UNKNOWN row.
    low     BrainSpan contributed but GTEx did not (no independent adult check), OR the
            class is MIXED (by construction MIXED means no contrast cleared a threshold).
    medium  both datasets contributed, but the peak is modest (peak_value < 5 RPKM), or
            the margin is under 2x, or the class is ADOLESCENT (capped, see below).
    high    both datasets contributed, peak_value >= 5 RPKM, decisive log2 contrast
            >= 1.0 (2x), AND one of:
              * the class is PRENATAL_DOMINANT or DEVELOPMENTAL, whose decisive contrast
                is anchored on the two well-sampled windows (20 and 12 donors); or
              * the class is ADULT_DYNAMIC *and* GTEx independently shows >= 5 TPM in
                adult brain. BrainSpan's adult window is only 6 donors, so an
                adult-weighted call is allowed to be "high" only when a ~900-donor adult
                dataset agrees the gene really is well expressed in adult brain. This is
                a boolean corroboration between datasets, not a numeric merge of RPKM
                with TPM.
            ADOLESCENT can NEVER be high: GTEx contains no adolescent donors at all, so
            there is nothing in this build that could corroborate an adolescent peak.

classification_basis
====================
    "gtex_v10+brainspan"               both sources had a row for this gene
    "brainspan_only"                   developmental trajectory only
    "gtex_only_no_developmental_data"  adult only; class is UNKNOWN
    "no_expression_data"               neither; class is UNKNOWN


Gene universe
=============
The spine is the HGNC complete set filtered to ``status == Approved`` and
``locus_group == "protein-coding gene"`` with a non-empty ``ensembl_gene_id``: 19,254
genes. That is the "~18,000 genes" the tournament ranks. Non-coding genes present in GTEx
or BrainSpan are deliberately NOT carried; the count of such genes is reported so the
exclusion is visible rather than silent.

Joins are on **unversioned** Ensembl gene IDs. GTEx v10 IDs carry a version suffix
(``ENSG00000223972.5``) which is stripped; the 45 ``_PAR_Y`` pseudo-autosomal duplicate
rows are dropped in favour of their X-linked primary entry. After that there are no
duplicate Ensembl IDs in either source.

**Ensembl IDs are not stable across 14 years of GENCODE, so the join is not
Ensembl-only.** BrainSpan is annotated against GENCODE v10 (2011) and the spine against
the current HGNC release. A gene whose Ensembl ID was retired and reissued in between
silently fails an Ensembl-only join, and it fails *specifically* for genes that have been
re-annotated — which is not a random subset. ``GRIN2B`` is the worked example: BrainSpan
carries it as ``ENSG00000150086``, current HGNC as ``ENSG00000273079``, and an
Ensembl-only join drops one of the most developmentally interesting genes in the whole
tournament to ``UNKNOWN``. Entrez ``2904`` is the same in both.

The join is therefore tiered, and the tier used is recorded per gene in
``brainspan_join_route`` / ``gtex_join_route``:

    1. ``ensembl``  unversioned Ensembl gene ID
    2. ``entrez``   NCBI Entrez Gene ID (BrainSpan only; GTEx carries no Entrez ID)
    3. ``symbol``   HGNC approved symbol against the source's own symbol column

Each tier is applied only to spine genes still unmatched after the previous one, and any
candidate that would match more than one spine gene, or more than one source row, is
**discarded rather than guessed** — the count of such ambiguous drops is reported in the
summary as ``ambiguous_dropped``. A wrong gene rescued by a sloppy symbol match is worse
than an honest ``UNKNOWN``.


Inputs
======
    data/raw/brain_expression/2026-09-22/GTEx_Analysis_v10_RNASeQCv2.4.2_gene_median_tpm.gct.gz
    data/raw/brain_expression/2026-09-22/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz  (cross-check only)
    data/raw/brain_expression/2026-09-22/GTEx_Analysis_v10_Annotations_SampleAttributesDS.txt
    data/raw/brain_expression/2026-09-22/GTEx_Analysis_v10_Annotations_SubjectPhenotypesDS.txt
    data/raw/brain_expression/2026-09-22/brainspan_genes_matrix_csv.zip
    data/raw/hgnc_complete/2026-09-22/hgnc_complete_set.txt.gz   (identity spine)

Outputs
=======
    data/gene_tournament/developmental_classification.parquet
    data/gene_tournament/developmental_classification_summary.json

Usage
=====
    python pipelines/gene_tournament/build_developmental_classification.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "brain_expression" / "2026-09-22"
HGNC_PATH = REPO_ROOT / "data" / "raw" / "hgnc_complete" / "2026-09-22" / "hgnc_complete_set.txt.gz"
OUT_DIR = REPO_ROOT / "data" / "gene_tournament"

GTEX_V10 = RAW_DIR / "GTEx_Analysis_v10_RNASeQCv2.4.2_gene_median_tpm.gct.gz"
GTEX_V8 = RAW_DIR / "GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz"
GTEX_SAMPLE_ATTR = RAW_DIR / "GTEx_Analysis_v10_Annotations_SampleAttributesDS.txt"
GTEX_SUBJECT_PHENO = RAW_DIR / "GTEx_Analysis_v10_Annotations_SubjectPhenotypesDS.txt"
BRAINSPAN_ZIP = RAW_DIR / "brainspan_genes_matrix_csv.zip"

# ---------------------------------------------------------------------------
# Thresholds. Every one of these is a convention, not an estimate. All are varied
# in the sensitivity analysis at the end of the run.
# ---------------------------------------------------------------------------
PSEUDOCOUNT = 0.1        # RPKM added to both sides of every developmental ratio
DETECT_RPKM = 1.0        # window mean at/above this counts as expressed (BrainSpan)
STRONG_LOG2 = 1.0        # 2.0x contrast
WEAK_LOG2 = 0.5849625007211562   # log2(1.5)
TPM_EXPRESSED = 1.0      # GTEx brain expression threshold
HIGH_CONF_PEAK_RPKM = 5.0

# The 13 brain tissues, canonical key -> (v10 column, v8 column)
BRAIN_TISSUES: dict[str, tuple[str, str]] = {
    "cortex": ("Brain_Cortex", "Brain - Cortex"),
    "frontal_cortex_ba9": ("Brain_Frontal_Cortex_BA9", "Brain - Frontal Cortex (BA9)"),
    "anterior_cingulate_ba24": (
        "Brain_Anterior_cingulate_cortex_BA24",
        "Brain - Anterior cingulate cortex (BA24)",
    ),
    "hippocampus": ("Brain_Hippocampus", "Brain - Hippocampus"),
    "amygdala": ("Brain_Amygdala", "Brain - Amygdala"),
    "caudate": ("Brain_Caudate_basal_ganglia", "Brain - Caudate (basal ganglia)"),
    "putamen": ("Brain_Putamen_basal_ganglia", "Brain - Putamen (basal ganglia)"),
    "nucleus_accumbens": (
        "Brain_Nucleus_accumbens_basal_ganglia",
        "Brain - Nucleus accumbens (basal ganglia)",
    ),
    "hypothalamus": ("Brain_Hypothalamus", "Brain - Hypothalamus"),
    "substantia_nigra": ("Brain_Substantia_nigra", "Brain - Substantia nigra"),
    "cerebellum": ("Brain_Cerebellum", "Brain - Cerebellum"),
    "cerebellar_hemisphere": ("Brain_Cerebellar_Hemisphere", "Brain - Cerebellar Hemisphere"),
    "spinal_cord_c1": ("Brain_Spinal_cord_cervical_c-1", "Brain - Spinal cord (cervical c-1)"),
}

WINDOWS = ["prenatal", "early_postnatal", "adolescent", "adult"]

SANITY_GENES = [
    "DCC", "NEGR1", "MEF2C", "GRIN2B", "HCN1",
    "GABRA5", "BSN", "CRTC1", "KCNJ3", "SYN1",
]


# ---------------------------------------------------------------------------
# Identity spine
# ---------------------------------------------------------------------------
def load_hgnc_spine() -> pd.DataFrame:
    """HGNC approved protein-coding genes with an Ensembl gene ID."""
    rows = []
    with gzip.open(HGNC_PATH, "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("status") != "Approved":
                continue
            if row.get("locus_group") != "protein-coding gene":
                continue
            ensg = (row.get("ensembl_gene_id") or "").strip()
            if not ensg:
                continue
            entrez = (row.get("entrez_id") or "").strip()
            rows.append(
                {
                    "ensembl_gene_id": ensg,
                    "gene_symbol": row["symbol"],
                    "entrez_id": entrez or None,
                    "hgnc_id": row.get("hgnc_id") or None,
                }
            )
    frame = pd.DataFrame(rows).drop_duplicates(subset="ensembl_gene_id")
    return frame.reset_index(drop=True)


# ---------------------------------------------------------------------------
# GTEx
# ---------------------------------------------------------------------------
def load_gtex(path: Path, column_index: int) -> pd.DataFrame:
    """Read a GTEx median-TPM GCT and return the 13 brain tissues, indexed by ENSG.

    ``column_index`` selects which element of the ``BRAIN_TISSUES`` tuples names the
    columns in this file (0 = v10 naming, 1 = v8 naming).
    """
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        fh.readline()  # "#1.2"
        fh.readline()  # "<nrows>\t<ncols>"
        header = fh.readline().rstrip("\n").split("\t")
        wanted = {BRAIN_TISSUES[k][column_index]: k for k in BRAIN_TISSUES}
        missing = set(wanted) - set(header)
        if missing:
            raise SystemExit(f"{path.name}: missing brain tissue columns {sorted(missing)}")
        idx = {header.index(col): key for col, key in wanted.items()}
        order = sorted(idx)
        keys = [idx[i] for i in order]

        ids: list[str] = []
        descs: list[str] = []
        values: list[list[float]] = []
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            name = parts[0]
            if name.endswith("_PAR_Y"):
                continue  # duplicate of the X-linked primary entry
            ids.append(name.split(".")[0])
            descs.append(parts[1])
            values.append([float(parts[i]) for i in order])

    frame = pd.DataFrame(values, columns=[f"adult_tpm_{k}" for k in keys])
    frame.insert(0, "gtex_description", descs)
    frame.insert(0, "ensembl_gene_id", ids)
    if frame["ensembl_gene_id"].duplicated().any():
        dupes = frame.loc[frame["ensembl_gene_id"].duplicated(), "ensembl_gene_id"].tolist()
        raise SystemExit(f"{path.name}: duplicate Ensembl IDs after version strip: {dupes[:5]}")
    tissue_cols = [f"adult_tpm_{k}" for k in BRAIN_TISSUES]
    frame = frame.reindex(columns=["ensembl_gene_id", "gtex_description", *tissue_cols])
    frame["adult_brain_max_tpm"] = frame[tissue_cols].max(axis=1)
    frame["adult_brain_median_tpm"] = frame[tissue_cols].median(axis=1)
    return frame


def gtex_brain_sample_counts() -> dict[str, int]:
    """Samples behind each brain-tissue median, from the v10 sample annotation."""
    v10_to_key = {BRAIN_TISSUES[k][0]: k for k in BRAIN_TISSUES}
    # SMTSD holds the human-readable tissue detail, which matches the v8 naming style.
    v8_to_key = {BRAIN_TISSUES[k][1]: k for k in BRAIN_TISSUES}
    counts: Counter[str] = Counter()
    with open(GTEX_SAMPLE_ATTR, encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            smtsd = (row.get("SMTSD") or "").strip()
            if row.get("SMAFRZE") != "RNASEQ":
                continue
            key = v8_to_key.get(smtsd) or v10_to_key.get(smtsd)
            if key:
                counts[key] += 1
    return dict(counts)


def gtex_donor_age_brackets() -> dict[str, int]:
    counts: Counter[str] = Counter()
    with open(GTEX_SUBJECT_PHENO, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            counts[row["AGE"]] += 1
    return dict(sorted(counts.items()))


# ---------------------------------------------------------------------------
# BrainSpan
# ---------------------------------------------------------------------------
def brainspan_age_to_years(age: str) -> float:
    """BrainSpan age string -> years from birth (negative before birth, 40 pcw = term)."""
    number, unit = age.strip().strip('"').split()
    n = float(number)
    if unit == "pcw":
        return (n - 40.0) / 52.0
    if unit == "mos":
        return n / 12.0
    if unit == "yrs":
        return n
    raise ValueError(f"unrecognised BrainSpan age unit in {age!r}")


def assign_window(years: float, adolescent_start: float = 12.0, adult_start: float = 20.0) -> str:
    if years < 0.0:
        return "prenatal"
    if years < adolescent_start:
        return "early_postnatal"
    if years < adult_start:
        return "adolescent"
    return "adult"


def load_brainspan() -> tuple[pd.DataFrame, list[dict], dict]:
    """Return (rows_metadata, columns_metadata, {'matrix': ndarray}) from the zip."""
    with zipfile.ZipFile(BRAINSPAN_ZIP) as zf:
        with zf.open("rows_metadata.csv") as fh:
            rows_meta = pd.read_csv(io.TextIOWrapper(fh, "utf-8"), dtype=str)
        with zf.open("columns_metadata.csv") as fh:
            cols_meta = list(csv.DictReader(io.TextIOWrapper(fh, "utf-8")))
        with zf.open("expression_matrix.csv") as fh:
            matrix = pd.read_csv(
                io.TextIOWrapper(fh, "utf-8"), header=None, index_col=0, dtype=np.float32
            ).to_numpy()
    if matrix.shape[0] != len(rows_meta) or matrix.shape[1] != len(cols_meta):
        raise SystemExit(
            f"BrainSpan shape mismatch: matrix {matrix.shape}, "
            f"rows_metadata {len(rows_meta)}, columns_metadata {len(cols_meta)}"
        )
    return rows_meta, cols_meta, {"matrix": matrix}


def brainspan_window_means(
    matrix: np.ndarray,
    cols_meta: list[dict],
    restrict_structures: set[str] | None,
    adolescent_start: float = 12.0,
    adult_start: float = 20.0,
) -> tuple[dict[str, np.ndarray], dict[str, dict]]:
    """Mean RPKM per gene per age window, plus the sample/donor/structure counts."""
    sel: dict[str, list[int]] = {w: [] for w in WINDOWS}
    donors: dict[str, set] = {w: set() for w in WINDOWS}
    structures: dict[str, set] = {w: set() for w in WINDOWS}
    for j, col in enumerate(cols_meta):
        acronym = col["structure_acronym"].strip('"')
        if restrict_structures is not None and acronym not in restrict_structures:
            continue
        window = assign_window(
            brainspan_age_to_years(col["age"]), adolescent_start, adult_start
        )
        sel[window].append(j)
        donors[window].add(col["donor_id"])
        structures[window].add(acronym)

    means = {}
    counts = {}
    for window in WINDOWS:
        cols = sel[window]
        if not cols:
            means[window] = np.full(matrix.shape[0], np.nan, dtype=np.float64)
        else:
            means[window] = matrix[:, cols].mean(axis=1).astype(np.float64)
        counts[window] = {
            "n_samples": len(cols),
            "n_donors": len(donors[window]),
            "n_structures": len(structures[window]),
            "structures": sorted(structures[window]),
        }
    return means, counts


def tiered_join(spine: pd.DataFrame, source: pd.DataFrame,
                tiers: list[tuple[str, str, str]]) -> tuple[pd.Series, dict]:
    """Map each spine row to at most one source row using ``tiers`` in order.

    ``tiers`` is a list of ``(route_name, spine_column, source_column)``. A tier is
    applied only to spine rows still unmatched. Within a tier, any key that is duplicated
    on either side is dropped rather than guessed, and counted as ambiguous.

    Returns (source_row_index_per_spine_row, stats).
    """
    assigned = pd.Series(pd.NA, index=spine.index, dtype="object")
    route = pd.Series(pd.NA, index=spine.index, dtype="object")
    used_source: set = set()
    stats: dict = {"matched_by": {}, "ambiguous_dropped": {}}

    for route_name, spine_col, source_col in tiers:
        todo = assigned.isna()
        if not todo.any():
            break
        s_keys = spine.loc[todo, spine_col].astype("string").str.strip()
        t_keys = source[source_col].astype("string").str.strip()

        s_valid = s_keys.notna() & (s_keys != "") & (s_keys.str.lower() != "nan")
        t_valid = t_keys.notna() & (t_keys != "") & (t_keys.str.lower() != "nan")
        # a source row already consumed by an earlier tier cannot be reused
        t_free = ~source.index.isin(used_source)

        s_keys = s_keys[s_valid]
        t_sub = t_keys[t_valid & pd.Series(t_free, index=source.index)]

        s_dup = set(s_keys[s_keys.duplicated(keep=False)])
        t_dup = set(t_sub[t_sub.duplicated(keep=False)])
        bad = s_dup | t_dup

        lookup = {k: i for i, k in t_sub.items() if k not in bad}
        hits = {i: lookup[k] for i, k in s_keys.items() if k not in bad and k in lookup}

        n_amb = sum(1 for k in s_keys if k in bad and k in set(t_sub))
        stats["matched_by"][route_name] = len(hits)
        stats["ambiguous_dropped"][route_name] = int(n_amb)

        for spine_i, source_i in hits.items():
            assigned.at[spine_i] = source_i
            route.at[spine_i] = route_name
            used_source.add(source_i)

    stats["unmatched"] = int(assigned.isna().sum())
    return assigned, route, stats


def attach_source(spine: pd.DataFrame, source: pd.DataFrame,
                  tiers: list[tuple[str, str, str]], columns: list[str],
                  route_col: str, flag_col: str) -> tuple[pd.DataFrame, dict]:
    """Tiered-join ``source`` onto ``spine`` and copy ``columns`` across."""
    assigned, route, stats = tiered_join(spine, source, tiers)
    out = spine.copy()
    out[route_col] = route
    out[flag_col] = assigned.notna()
    positions = assigned.map(lambda i: source.index.get_loc(i) if pd.notna(i) else -1)
    positions = positions.to_numpy(dtype=int)
    take = np.where(positions >= 0, positions, 0)
    for col in columns:
        values = source[col].to_numpy()
        picked = values[take]
        if picked.dtype.kind in "fiu":
            picked = picked.astype(float)
            picked = np.where(positions >= 0, picked, np.nan)
        else:
            picked = np.where(positions >= 0, picked, None)
        out[col] = picked
    return out, stats


def structures_in_all_windows(cols_meta: list[dict]) -> set[str]:
    per_window: dict[str, set] = defaultdict(set)
    for col in cols_meta:
        window = assign_window(brainspan_age_to_years(col["age"]))
        per_window[window].add(col["structure_acronym"].strip('"'))
    return set.intersection(*(per_window[w] for w in WINDOWS))


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def _log2_ratio(a: np.ndarray | float, b: np.ndarray | float, c: float = PSEUDOCOUNT):
    return np.log2((np.asarray(a, dtype=float) + c) / (np.asarray(b, dtype=float) + c))


def classify(frame: pd.DataFrame,
             detect_rpkm: float = DETECT_RPKM,
             strong_log2: float = STRONG_LOG2,
             weak_log2: float = WEAK_LOG2,
             tpm_expressed: float = TPM_EXPRESSED) -> pd.DataFrame:
    """Apply rules R0-R7 verbatim. Returns class / confidence / basis / margin columns."""
    n = len(frame)
    has_gtex = frame["has_gtex"].to_numpy()
    has_bs = frame["has_brainspan"].to_numpy()

    P = frame["brainspan_prenatal_mean_rpkm"].to_numpy(dtype=float)
    E = frame["brainspan_early_postnatal_mean_rpkm"].to_numpy(dtype=float)
    D = frame["brainspan_adolescent_mean_rpkm"].to_numpy(dtype=float)
    A = frame["brainspan_adult_mean_rpkm"].to_numpy(dtype=float)
    stack = np.vstack([P, E, D, A])
    peak_value = np.nanmax(np.where(np.isnan(stack), -np.inf, stack), axis=0)
    peak_value = np.where(has_bs, peak_value, np.nan)
    peak_idx = np.argmax(np.where(np.isnan(stack), -np.inf, stack), axis=0)
    peak_window = np.array(WINDOWS, dtype=object)[peak_idx]
    peak_window = np.where(has_bs, peak_window, None)

    max_post = np.maximum(np.maximum(E, D), A)
    max_dev = np.maximum(P, E)
    max_late = np.maximum(D, A)

    prenatal_vs_postnatal = _log2_ratio(P, max_post)
    dev_vs_late = _log2_ratio(max_dev, max_late)
    late_vs_dev = _log2_ratio(max_late, max_dev)
    adol_vs_pre = _log2_ratio(D, P)
    adol_vs_adult = _log2_ratio(D, A)
    adult_vs_pre = _log2_ratio(A, P)

    adult_expressed = frame["adult_brain_max_tpm"].to_numpy(dtype=float) >= tpm_expressed
    adult_expressed = np.where(has_gtex, adult_expressed, False)

    classes = np.full(n, "UNKNOWN", dtype=object)
    basis = np.full(n, "no_expression_data", dtype=object)
    margin = np.full(n, np.nan, dtype=float)

    basis = np.where(has_gtex & has_bs, "gtex_v10+brainspan", basis)
    basis = np.where(has_bs & ~has_gtex, "brainspan_only", basis)
    basis = np.where(has_gtex & ~has_bs, "gtex_only_no_developmental_data", basis)

    expressed = has_bs & (peak_value >= detect_rpkm)
    basis = np.where(has_bs & ~expressed, "measured_below_detection_in_brain", basis)

    # R3 PRENATAL_DOMINANT
    r3 = expressed & (prenatal_vs_postnatal >= strong_log2)
    # R4 DEVELOPMENTAL  -- exact mirror of R6
    r4 = expressed & ~r3 & (dev_vs_late >= weak_log2)
    # R5 ADOLESCENT -- a genuine adolescent-specific peak
    r5 = (
        expressed
        & ~r3
        & ~r4
        & (peak_window == "adolescent")
        & (adol_vs_pre >= weak_log2)
        & (_log2_ratio(D, E) >= weak_log2)
        & (adol_vs_adult >= weak_log2)
    )
    # R6 ADULT_DYNAMIC -- adult level well above prenatal
    r6 = expressed & ~r3 & ~r4 & ~r5 & (adult_vs_pre >= weak_log2)
    # R7 MIXED
    r7 = expressed & ~r3 & ~r4 & ~r5 & ~r6

    classes = np.where(r3, "PRENATAL_DOMINANT", classes)
    classes = np.where(r4, "DEVELOPMENTAL", classes)
    classes = np.where(r5, "ADOLESCENT", classes)
    classes = np.where(r6, "ADULT_DYNAMIC", classes)
    classes = np.where(r7, "MIXED", classes)

    margin = np.where(r3, prenatal_vs_postnatal, margin)
    margin = np.where(r4, dev_vs_late, margin)
    margin = np.where(r5, np.minimum(adol_vs_pre, adol_vs_adult), margin)
    margin = np.where(r6, adult_vs_pre, margin)
    margin = np.where(r7, 0.0, margin)

    # ---- confidence -------------------------------------------------------
    conf = np.full(n, "none", dtype=object)
    classified = r3 | r4 | r5 | r6 | r7
    both = has_gtex & has_bs
    conf = np.where(classified, "low", conf)                       # MIXED / brainspan-only
    conf = np.where(classified & both, "medium", conf)
    # "high" requires a 2x margin, a solid peak, and BOTH datasets.
    #   R3/R4: the decisive contrast is anchored on the well-sampled prenatal (20 donors)
    #          and early-postnatal (12 donors) windows -> allowed.
    #   R6:    the decisive contrast leans on BrainSpan's 6-donor adult window, so it is
    #          allowed to reach "high" ONLY when GTEx independently corroborates strong
    #          adult brain expression (>= 5 TPM across ~900 donors). This is a boolean
    #          corroboration, not a numeric merge of RPKM with TPM.
    #   R5:    never. GTEx has no adolescent donors, so nothing can corroborate an
    #          adolescent peak. Capped at medium by construction.
    gtex_corroborates = frame["adult_brain_max_tpm"].to_numpy(dtype=float) >= 5.0
    gtex_corroborates = np.where(has_gtex, gtex_corroborates, False)
    high = (
        both
        & (peak_value >= HIGH_CONF_PEAK_RPKM)
        & (margin >= strong_log2)
        & ((r3 | r4) | (r6 & gtex_corroborates))
    )
    conf = np.where(high, "high", conf)
    conf = np.where(r7, "low", conf)                               # MIXED never above low
    conf = np.where(~classified, "none", conf)

    out = frame.copy()
    out["developmental_class"] = classes
    out["classification_confidence"] = conf
    out["classification_basis"] = basis
    out["classification_margin_log2"] = margin
    out["brainspan_peak_window"] = peak_window
    out["brainspan_peak_mean_rpkm"] = peak_value
    out["adult_expressed"] = adult_expressed
    out["prenatal_adult_log2_ratio"] = np.where(has_bs, _log2_ratio(P, A), np.nan)
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build() -> tuple[pd.DataFrame, dict]:
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print("=" * 78)
    print("developmental classification build")
    print("=" * 78)

    spine = load_hgnc_spine()
    print(f"\nHGNC spine (approved protein-coding, has Ensembl ID): {len(spine):,} genes")

    gtex10 = load_gtex(GTEX_V10, column_index=0)
    print(f"GTEx v10 median TPM: {gtex10.shape[0]:,} genes x 13 brain tissues")
    gtex8 = load_gtex(GTEX_V8, column_index=1)
    print(f"GTEx v8  median TPM: {gtex8.shape[0]:,} genes x 13 brain tissues  (cross-check only)")

    rows_meta, cols_meta, payload = load_brainspan()
    matrix = payload["matrix"]
    print(f"BrainSpan matrix: {matrix.shape[0]:,} genes x {matrix.shape[1]:,} samples (RPKM)")

    common = structures_in_all_windows(cols_meta)
    print(f"BrainSpan structures sampled in all four windows: {len(common)} -> {sorted(common)}")

    means_common, counts_common = brainspan_window_means(matrix, cols_meta, common)
    means_all, counts_all = brainspan_window_means(matrix, cols_meta, None)

    print("\nBrainSpan sample counts per age window")
    print(f"{'window':<18}{'PRIMARY (16 common structures)':<38}{'all 26 structures'}")
    for w in WINDOWS:
        c, a = counts_common[w], counts_all[w]
        print(
            f"{w:<18}"
            f"{f'samples={c['n_samples']:4d}  donors={c['n_donors']:3d}':<38}"
            f"samples={a['n_samples']:4d}  donors={a['n_donors']:3d}"
        )

    bs = pd.DataFrame(
        {
            "ensembl_gene_id": rows_meta["ensembl_gene_id"].str.strip('"'),
            "brainspan_gene_symbol": rows_meta["gene_symbol"].str.strip('"'),
            "brainspan_entrez_id": rows_meta["entrez_id"].str.strip('"'),
        }
    )
    for w in WINDOWS:
        bs[f"brainspan_{w}_mean_rpkm"] = means_common[w]
        bs[f"brainspan_{w}_mean_rpkm_allstruct"] = means_all[w]
    bs = bs.drop_duplicates(subset="ensembl_gene_id")

    # ---- assemble (tiered join; see docstring) ---------------------------
    tissue_cols = [f"adult_tpm_{k}" for k in BRAIN_TISSUES]
    frame, gtex_stats = attach_source(
        spine,
        gtex10,
        tiers=[
            ("ensembl", "ensembl_gene_id", "ensembl_gene_id"),
            ("symbol", "gene_symbol", "gtex_description"),
        ],
        columns=[*tissue_cols, "adult_brain_max_tpm", "adult_brain_median_tpm",
                 "gtex_description"],
        route_col="gtex_join_route",
        flag_col="has_gtex",
    )

    bs_cols = ["brainspan_gene_symbol", "brainspan_entrez_id"]
    for w in WINDOWS:
        bs_cols += [f"brainspan_{w}_mean_rpkm", f"brainspan_{w}_mean_rpkm_allstruct"]
    frame, bs_stats = attach_source(
        frame,
        bs,
        tiers=[
            ("ensembl", "ensembl_gene_id", "ensembl_gene_id"),
            ("entrez", "entrez_id", "brainspan_entrez_id"),
            ("symbol", "gene_symbol", "brainspan_gene_symbol"),
        ],
        columns=bs_cols,
        route_col="brainspan_join_route",
        flag_col="has_brainspan",
    )
    print("\nJoin routes (spine -> source)")
    print(f"  GTEx v10 : matched {gtex_stats['matched_by']}  "
          f"ambiguous_dropped={gtex_stats['ambiguous_dropped']}  "
          f"unmatched={gtex_stats['unmatched']}")
    print(f"  BrainSpan: matched {bs_stats['matched_by']}  "
          f"ambiguous_dropped={bs_stats['ambiguous_dropped']}  "
          f"unmatched={bs_stats['unmatched']}")

    # entrez: HGNC first, BrainSpan as fallback
    frame["entrez_id"] = frame["entrez_id"].fillna(
        pd.Series(frame["brainspan_entrez_id"], index=frame.index)
    )
    frame = frame.drop(columns=["brainspan_entrez_id"])

    classified = classify(frame)

    # v8 cross-check column, kept explicitly separate from the v10 numbers
    v8_max = gtex8.set_index("ensembl_gene_id")["adult_brain_max_tpm"]
    classified["adult_brain_max_tpm_gtex_v8"] = classified["ensembl_gene_id"].map(v8_max)

    tissue_cols = [f"adult_tpm_{k}" for k in BRAIN_TISSUES]
    ordered = [
        "ensembl_gene_id", "gene_symbol", "entrez_id", "hgnc_id",
        "developmental_class", "classification_confidence", "classification_basis",
        "classification_margin_log2",
        "adult_expressed", "adult_brain_max_tpm", "adult_brain_median_tpm",
        *tissue_cols,
        "brainspan_prenatal_mean_rpkm", "brainspan_early_postnatal_mean_rpkm",
        "brainspan_adolescent_mean_rpkm", "brainspan_adult_mean_rpkm",
        "prenatal_adult_log2_ratio", "brainspan_peak_window", "brainspan_peak_mean_rpkm",
        "brainspan_prenatal_mean_rpkm_allstruct",
        "brainspan_early_postnatal_mean_rpkm_allstruct",
        "brainspan_adolescent_mean_rpkm_allstruct",
        "brainspan_adult_mean_rpkm_allstruct",
        "adult_brain_max_tpm_gtex_v8",
        "has_gtex", "has_brainspan", "gtex_join_route", "brainspan_join_route",
        "gtex_description", "brainspan_gene_symbol",
    ]
    classified = classified.reindex(columns=ordered)

    # ---- sensitivity ----------------------------------------------------
    sensitivity = run_sensitivity(frame, means_all, bs, gtex10)

    summary = {
        "generated_utc": started,
        "n_genes": int(len(classified)),
        "gene_universe": (
            "HGNC complete set, status=Approved, locus_group=protein-coding gene, "
            "non-empty ensembl_gene_id"
        ),
        "adult_source": {
            "dataset": "GTEx Analysis v10",
            "unit": "median TPM per tissue",
            "gencode": "v39",
            "genome_build": "GRCh38/hg38",
            "donor_age_brackets": gtex_donor_age_brackets(),
            "documented_age_range": "adults 20-70 yr (released in 10-year brackets)",
            "brain_tissues": list(BRAIN_TISSUES),
            "brain_rnaseq_sample_counts": gtex_brain_sample_counts(),
        },
        "developmental_source": {
            "dataset": "BrainSpan Developmental Transcriptome, RNA-Seq summarised to genes",
            "unit": "RPKM",
            "gencode": "v10",
            "n_samples_total": int(matrix.shape[1]),
            "n_genes_total": int(matrix.shape[0]),
            "primary_structures": sorted(common),
        },
        "units_are_never_merged": (
            "Every developmental contrast is computed inside BrainSpan in RPKM; every "
            "adult-expression statement is computed inside GTEx in TPM. The two are "
            "combined only as boolean conditions. No column is a function of both."
        ),
        "adult_expressed_is_necessary_not_sufficient": (
            "adult_expressed means only that a transcript is detectable in adult "
            "post-mortem bulk brain. It is not evidence that the gene is modifiable in an "
            "adult, and must not be used as a positive tractability signal."
        ),
        "bulk_not_cell_type": (
            "All values are homogenate averages. A gene high in 1% of cells is "
            "indistinguishable from a gene low in all cells. Cell-type-restricted genes "
            "are systematically diluted and may be called MIXED for compositional reasons."
        ),
        "age_window_definition": {
            "prenatal": "years_from_birth < 0 (all 'N pcw' samples; 40 pcw taken as term)",
            "early_postnatal": "0 <= years < 12",
            "adolescent": "12 <= years < 20",
            "adult": "years >= 20",
        },
        "thresholds": {
            "PSEUDOCOUNT_RPKM": PSEUDOCOUNT,
            "DETECT_RPKM": DETECT_RPKM,
            "STRONG_LOG2": STRONG_LOG2,
            "WEAK_LOG2": WEAK_LOG2,
            "TPM_EXPRESSED": TPM_EXPRESSED,
            "HIGH_CONF_PEAK_RPKM": HIGH_CONF_PEAK_RPKM,
            "note": "all conventions, not estimates; see 'sensitivity'",
        },
        "brainspan_window_counts_primary": {
            w: {k: v for k, v in counts_common[w].items() if k != "structures"}
            for w in WINDOWS
        },
        "brainspan_window_counts_all_structures": {
            w: {k: v for k, v in counts_all[w].items() if k != "structures"}
            for w in WINDOWS
        },
        "class_distribution": {
            str(k): int(v)
            for k, v in classified["developmental_class"].value_counts().items()
        },
        "confidence_distribution": {
            str(k): int(v)
            for k, v in classified["classification_confidence"].value_counts().items()
        },
        "basis_distribution": {
            str(k): int(v)
            for k, v in classified["classification_basis"].value_counts().items()
        },
        "coverage": {
            "with_adult_data_gtex_v10": int(classified["has_gtex"].sum()),
            "with_developmental_data_brainspan": int(classified["has_brainspan"].sum()),
            "with_both": int((classified["has_gtex"] & classified["has_brainspan"]).sum()),
            "with_neither": int(
                (~classified["has_gtex"] & ~classified["has_brainspan"]).sum()
            ),
            "gtex_genes_off_spine": int(
                len(set(gtex10["ensembl_gene_id"]) - set(spine["ensembl_gene_id"]))
            ),
            "brainspan_genes_off_spine": int(
                len(set(bs["ensembl_gene_id"]) - set(spine["ensembl_gene_id"]))
            ),
        },
        "join_routes": {
            "why_tiered": (
                "BrainSpan is GENCODE v10 (2011); the spine is current HGNC. Ensembl gene "
                "IDs are not stable across that gap and the failures are not random -- "
                "GRIN2B alone moves ENSG00000150086 -> ENSG00000273079. Ambiguous "
                "candidates are dropped, not guessed."
            ),
            "gtex_v10": gtex_stats,
            "brainspan": bs_stats,
        },
        "sensitivity": sensitivity,
    }
    return classified, summary


def run_sensitivity(frame: pd.DataFrame, means_all: dict, bs: pd.DataFrame,
                    gtex10: pd.DataFrame) -> dict:
    """How much do the class counts move when the arbitrary thresholds move?"""
    out: dict = {}

    def dist(df):
        return {
            str(k): int(v) for k, v in df["developmental_class"].value_counts().items()
        }

    out["baseline"] = dist(classify(frame))
    for name, kwargs in [
        ("DETECT_RPKM=0.5", dict(detect_rpkm=0.5)),
        ("DETECT_RPKM=2.0", dict(detect_rpkm=2.0)),
        ("STRONG_LOG2=0.585 (1.5x)", dict(strong_log2=WEAK_LOG2)),
        ("STRONG_LOG2=1.585 (3x)", dict(strong_log2=math.log2(3.0))),
        ("WEAK_LOG2=0.322 (1.25x)", dict(weak_log2=math.log2(1.25))),
        ("WEAK_LOG2=1.0 (2x)", dict(weak_log2=1.0)),
        ("TPM_EXPRESSED=0.5", dict(tpm_expressed=0.5)),
        ("TPM_EXPRESSED=5.0", dict(tpm_expressed=5.0)),
    ]:
        out[name] = dist(classify(frame, **kwargs))

    # structure-pooling sensitivity: recompute with all 26 structures
    alt = frame.copy()
    for w in WINDOWS:
        alt[f"brainspan_{w}_mean_rpkm"] = alt[f"brainspan_{w}_mean_rpkm_allstruct"]
    out["ALL 26 structures (vs 16 common)"] = dist(classify(alt))
    return out


def print_sanity(frame: pd.DataFrame) -> None:
    sub = frame[frame["gene_symbol"].isin(SANITY_GENES)].copy()
    sub["_o"] = sub["gene_symbol"].map({g: i for i, g in enumerate(SANITY_GENES)})
    sub = sub.sort_values("_o")
    print("\n" + "=" * 78)
    print("SANITY-CHECK GENES")
    print("=" * 78)
    hdr = (
        f"{'symbol':<9}{'class':<19}{'conf':<8}"
        f"{'preRPKM':>9}{'earRPKM':>9}{'adoRPKM':>9}{'adtRPKM':>9}"
        f"{'log2P/A':>9}{'maxTPM':>9}{'adultExp':>9}"
    )
    print(hdr)
    print("-" * len(hdr))
    for _, r in sub.iterrows():
        print(
            f"{r['gene_symbol']:<9}{r['developmental_class']:<19}"
            f"{r['classification_confidence']:<8}"
            f"{r['brainspan_prenatal_mean_rpkm']:>9.2f}"
            f"{r['brainspan_early_postnatal_mean_rpkm']:>9.2f}"
            f"{r['brainspan_adolescent_mean_rpkm']:>9.2f}"
            f"{r['brainspan_adult_mean_rpkm']:>9.2f}"
            f"{r['prenatal_adult_log2_ratio']:>9.2f}"
            f"{r['adult_brain_max_tpm']:>9.2f}"
            f"{str(bool(r['adult_expressed'])):>9}"
        )
    missing = set(SANITY_GENES) - set(sub["gene_symbol"])
    if missing:
        print(f"NOT FOUND on spine: {sorted(missing)}")


def main() -> int:
    frame, summary = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_parquet = OUT_DIR / "developmental_classification.parquet"
    frame.to_parquet(out_parquet, index=False)
    (OUT_DIR / "developmental_classification_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )

    print("\n" + "=" * 78)
    print(f"WROTE {out_parquet}")
    print(f"shape: {frame.shape[0]:,} rows x {frame.shape[1]} columns")
    print("=" * 78)

    print("\nCLASS DISTRIBUTION")
    for k, v in sorted(summary["class_distribution"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20}{v:>7,}  {100*v/len(frame):5.1f}%")
    print("\nCONFIDENCE")
    for k, v in sorted(summary["confidence_distribution"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20}{v:>7,}")
    print("\nBASIS")
    for k, v in sorted(summary["basis_distribution"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20}{v:>7,}")
    print("\nCOVERAGE")
    for k, v in summary["coverage"].items():
        print(f"  {k:<36}{v:>8,}")

    print("\nSENSITIVITY OF CLASS COUNTS TO THE ARBITRARY THRESHOLDS")
    labels = ["PRENATAL_DOMINANT", "DEVELOPMENTAL", "ADOLESCENT",
              "ADULT_DYNAMIC", "MIXED", "UNKNOWN"]
    head = f"{'variant':<34}" + "".join(f"{l[:9]:>10}" for l in labels)
    print(head)
    print("-" * len(head))
    for name, d in summary["sensitivity"].items():
        print(f"{name:<34}" + "".join(f"{d.get(l, 0):>10,}" for l in labels))

    print_sanity(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main())
