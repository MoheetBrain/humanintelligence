#!/usr/bin/env python3
"""Sprint 5 — AlphaGenome per-variant scores for brain-relevant tracks (Atlas or live model).

Access status (verified 2026-09-23, see data/sprint5/alphagenome_provenance.json):
  * Tissue/track-level AlphaGenome Atlas scores ("Raw Atlas Features") are served ONLY through the
    AlphaGenome API (gRPC ``gdmscience.googleapis.com``), which requires an API key sent as
    ``x-goog-api-key``. There is no public bucket / Zenodo / login-free download of these scores.
  * The static AVI tabix (88.5 GB) is behind a Google sign-in on the downloads page; it holds one
    genome-wide AVI score per SNV, not per-tissue scores, so it is not what this script extracts.
  * This script therefore needs ``ALPHAGENOME_API_KEY`` in the environment. If it is absent the
    script writes a status JSON and exits with code 3 and the message ``NOT_TESTABLE``.
    It never requests, creates or stores a key.

Modes
  --mode atlas  (default) precomputed AlphaGenome Atlas scores via ``alphagenome.atlas.atlas``
                (alphagenome>=0.9.0). SNVs only; the ALT allele must be relative to GRCh38 REF
                (the Atlas key is chr:pos:ref>alt; swapped alleles are lookup misses).
  --mode model  live AlphaGenome inference via ``dna_client.score_variant`` on a 1 Mb interval with
                the recommended scorers (slower, rate-limited; supports indels).

Input CSV columns: rsid, chr38, pos38, allele_string (Ensembl order: GRCh38 REF first, e.g. "T/C").
Every ALT in allele_string is scored separately. Optional column cognition_increasing_allele is
carried through so direction can be re-expressed for the cognition-increasing allele.

Output parquet (one row per variant x scorer x [gene] x track):
  rsid, variant_id, chr38, pos38, ref, alt, source, scorer, output_type, is_signed, gene_id,
  gene_name, gene_strand, junction_start, junction_end, track_name, track_strand, ontology_curie,
  brain_tier, biosample_name, biosample_type, gtex_tissue, assay, transcription_factor,
  histone_mark, raw_score, quantile_score, direction_alt_vs_ref, cognition_increasing_allele,
  direction_for_cognition_increasing_allele

``direction_alt_vs_ref`` = UP if raw_score > 0, DOWN if < 0, ZERO if == 0, for signed scorers
only; UNSIGNED for magnitude-only scorers (splicing max|ALT-REF|, contact maps, active-allele).

Usage
  ALPHAGENOME_API_KEY=... python pipelines/sprint5/alphagenome_query.py \
      --variants data/sprint5/query_variants_cognition.csv --limit 3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "data" / "interim" / "sprint5" / "alphagenome" / "alphagenome_scores.parquet"
API_KEY_ENV = "ALPHAGENOME_API_KEY"
EXIT_NOT_TESTABLE = 3
MIN_CLIENT_VERSION_ATLAS = (0, 9, 0)

# Brain / neural biosamples present in the AlphaGenome human output metadata
# (google-deepmind/alphagenome_research, OutputMetadataResponse_ORGANISM_HOMO_SAPIENS.textproto,
# commit 0db53bd). Tiers are ours, fixed here so the filter is auditable.
BRAIN_ONTOLOGY = {
    # CORTEX: adult cerebral cortex tissue and cortical cell types
    "UBERON:0009834": ("dorsolateral prefrontal cortex", "CORTEX"),
    "UBERON:0001870": ("frontal cortex (incl. GTEx Brain_Cortex)", "CORTEX"),
    "UBERON:0001871": ("temporal lobe", "CORTEX"),
    "UBERON:0002702": ("middle frontal gyrus", "CORTEX"),
    "UBERON:0009835": ("anterior cingulate cortex (GTEx BA24)", "CORTEX"),
    "CL:0000679": ("glutamatergic neuron", "CORTEX"),
    "CL:0002605": ("astrocyte of the cerebral cortex", "CORTEX"),
    # BRAIN: whole brain, other regions, generic neural cell types
    "UBERON:0000955": ("brain", "BRAIN"),
    "UBERON:0001873": ("caudate nucleus", "BRAIN"),
    "UBERON:0002626": ("head of caudate nucleus", "BRAIN"),
    "UBERON:0001874": ("putamen", "BRAIN"),
    "UBERON:0001876": ("amygdala", "BRAIN"),
    "UBERON:0001882": ("nucleus accumbens", "BRAIN"),
    "UBERON:0001897": ("dorsal plus ventral thalamus", "BRAIN"),
    "UBERON:0001898": ("hypothalamus", "BRAIN"),
    "UBERON:0001954": ("Ammon's horn (GTEx Brain_Hippocampus)", "BRAIN"),
    "UBERON:0002305": ("layer of hippocampus", "BRAIN"),
    "UBERON:0002037": ("cerebellum", "BRAIN"),
    "UBERON:0002129": ("cerebellar cortex", "BRAIN"),
    "UBERON:0002245": ("cerebellar hemisphere", "BRAIN"),
    "UBERON:0002038": ("substantia nigra", "BRAIN"),
    "CL:0000540": ("neuron", "BRAIN"),
    "CL:0000127": ("astrocyte", "BRAIN"),
    "CL:0002603": ("astrocyte of the cerebellum", "BRAIN"),
    "CL:0002604": ("astrocyte of the hippocampus", "BRAIN"),
    "CL:0002453": ("oligodendrocyte precursor cell", "BRAIN"),
    "CL:2000043": ("brain pericyte", "BRAIN"),
    "CL:2000044": ("brain microvascular endothelial cell", "BRAIN"),
    "CL:0002590": ("smooth muscle cell of the brain vasculature", "BRAIN"),
    # NEURAL_DEV_OR_LINE: progenitors, in-vitro neural cells, neuroblastoma / NT2 lines
    "CL:0000047": ("neuronal stem cell", "NEURAL_DEV_OR_LINE"),
    "CL:0011020": ("neural progenitor cell", "NEURAL_DEV_OR_LINE"),
    "CL:0002319": ("neural cell", "NEURAL_DEV_OR_LINE"),
    "CL:0011012": ("neural crest cell", "NEURAL_DEV_OR_LINE"),
    "NTR:0000427": ("neurosphere", "NEURAL_DEV_OR_LINE"),
    "NTR:0000474": ("ecto neural progenitor cell", "NEURAL_DEV_OR_LINE"),
    "EFO:0003072": ("SK-N-SH", "NEURAL_DEV_OR_LINE"),
    "EFO:0002860": ("SK-N-MC", "NEURAL_DEV_OR_LINE"),
    "EFO:0005721": ("SK-N-DZ", "NEURAL_DEV_OR_LINE"),
    "EFO:0005725": ("BE2C", "NEURAL_DEV_OR_LINE"),
    "EFO:0005236": ("NT2/D1", "NEURAL_DEV_OR_LINE"),
    # SPINAL_PERIPHERAL: spinal cord, motor neurons, nerves, pituitary
    "UBERON:0002240": ("spinal cord", "SPINAL_PERIPHERAL"),
    "UBERON:0006469": ("C1 segment of cervical spinal cord", "SPINAL_PERIPHERAL"),
    "CL:0002606": ("astrocyte of the spinal cord", "SPINAL_PERIPHERAL"),
    "CL:0000100": ("motor neuron", "SPINAL_PERIPHERAL"),
    "UBERON:0001323": ("tibial nerve", "SPINAL_PERIPHERAL"),
    "UBERON:0001322": ("sciatic nerve", "SPINAL_PERIPHERAL"),
    "UBERON:0000941": ("cranial nerve II", "SPINAL_PERIPHERAL"),
    "UBERON:0000007": ("pituitary gland", "SPINAL_PERIPHERAL"),
}

TRACK_COLS = {  # AlphaGenome track-metadata column -> output column
    "name": "track_name", "strand": "track_strand", "ontology_curie": "ontology_curie",
    "biosample_name": "biosample_name", "biosample_type": "biosample_type",
    "gtex_tissue": "gtex_tissue", "Assay title": "assay", "assay": "assay",
    "transcription_factor": "transcription_factor", "histone_mark": "histone_mark",
}
OUT_COLS = [
    "rsid", "variant_id", "chr38", "pos38", "ref", "alt", "source", "scorer", "output_type",
    "is_signed", "gene_id", "gene_name", "gene_strand", "junction_start", "junction_end",
    "track_name", "track_strand", "ontology_curie", "brain_tier", "biosample_name",
    "biosample_type", "gtex_tissue", "assay", "transcription_factor", "histone_mark",
    "raw_score", "quantile_score", "direction_alt_vs_ref", "cognition_increasing_allele",
    "direction_for_cognition_increasing_allele",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_status(out: Path, status: dict) -> Path:
    path = out.with_suffix(".status.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2) + "\n")
    return path


# --------------------------------------------------------------------------- input


def load_variants(path: Path, limit: int | None, snv_only: bool) -> pd.DataFrame:
    """One row per (rsid, ALT allele) with GRCh38 REF taken from Ensembl allele_string."""
    df = pd.read_csv(path, dtype={"chr38": str, "cognition_increasing_allele": str, "allele_string": str})
    need = {"rsid", "chr38", "pos38", "allele_string"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"input {path} lacks columns {sorted(missing)}")
    keep = ["rsid", "chr38", "pos38", "allele_string"]
    if "cognition_increasing_allele" in df.columns:
        keep.append("cognition_increasing_allele")
    df = df[keep].dropna(subset=["chr38", "pos38", "allele_string"]).drop_duplicates("rsid")
    if limit:
        df = df.head(limit)
    rows = []
    for r in df.itertuples(index=False):
        alleles = str(r.allele_string).split("/")
        ref, alts = alleles[0], alleles[1:]
        for alt in alts:
            if alt in {"-", ""} or ref in {"-", ""}:
                continue  # Ensembl '-' notation for indels needs left-normalised VCF alleles
            if snv_only and (len(ref) != 1 or len(alt) != 1):
                continue
            rows.append({
                "rsid": r.rsid, "chr38": str(r.chr38).removeprefix("chr"), "pos38": int(float(r.pos38)),
                "ref": ref, "alt": alt,
                "cognition_increasing_allele": getattr(r, "cognition_increasing_allele", None),
            })
    out = pd.DataFrame(rows, columns=["rsid", "chr38", "pos38", "ref", "alt",
                                      "cognition_increasing_allele"])
    cia = out["cognition_increasing_allele"]
    out["cognition_increasing_allele"] = cia.astype(object).where(cia.notna(), None)
    return out


# --------------------------------------------------------------------------- tidy


def _direction(score: float, signed: bool) -> str:
    if not signed:
        return "UNSIGNED"
    if pd.isna(score):
        return "NA"
    return "UP" if score > 0 else "DOWN" if score < 0 else "ZERO"


def tidy_atlas_anndata(scorer: str, adata, is_signed: bool) -> pd.DataFrame:
    """Long table from one Atlas AnnData (obs = variant[/gene], var = tracks)."""
    import numpy as np

    n_obs, n_var = adata.shape
    if n_obs == 0 or n_var == 0:
        return pd.DataFrame()
    obs = adata.obs.reset_index(drop=True)
    var = adata.var.reset_index(drop=True)
    raw = np.asarray(adata.X, dtype="float64")
    q = adata.layers["quantiles"] if "quantiles" in adata.layers else None
    long = pd.DataFrame({
        "obs_i": np.repeat(np.arange(n_obs), n_var),
        "var_i": np.tile(np.arange(n_var), n_obs),
        "raw_score": raw.reshape(-1),
        "quantile_score": np.asarray(q, dtype="float64").reshape(-1) if q is not None else np.nan,
    })
    o = obs.rename(columns={"strand": "gene_strand", "junction_Start": "junction_start",
                            "junction_End": "junction_end"})
    o["variant_id"] = o["variant"].astype(str)
    long = long.join(o.drop(columns=["variant"]), on="obs_i")
    v = var.rename(columns={k: val for k, val in TRACK_COLS.items() if k in var.columns})
    v = v.loc[:, ~v.columns.duplicated()]
    long = long.join(v, on="var_i", rsuffix="_track")
    long["scorer"] = scorer
    long["is_signed"] = bool(is_signed)
    return long.drop(columns=["obs_i", "var_i"])


def finalise(long: pd.DataFrame, variants: pd.DataFrame, source: str, all_tissues: bool) -> pd.DataFrame:
    if long.empty:
        return pd.DataFrame(columns=OUT_COLS)
    vk = variants.assign(variant_id="chr" + variants["chr38"] + ":" + variants["pos38"].astype(str)
                         + ":" + variants["ref"] + ">" + variants["alt"])
    long = long.merge(vk, on="variant_id", how="left")
    long["source"] = source
    if "ontology_curie" not in long.columns:
        long["ontology_curie"] = pd.NA
    long["brain_tier"] = long["ontology_curie"].map(lambda c: BRAIN_ONTOLOGY.get(c, (None, None))[1])
    if not all_tissues:
        # keep brain tracks, plus scorers that carry no ontology (e.g. contact maps / AVI aggregates)
        long = long[long["brain_tier"].notna() | long["ontology_curie"].isna()]
    long["direction_alt_vs_ref"] = [
        _direction(s, sg) for s, sg in zip(long["raw_score"], long["is_signed"])]

    def cog_dir(row) -> str:
        d, cia = row["direction_alt_vs_ref"], row.get("cognition_increasing_allele")
        if d not in {"UP", "DOWN"} or not isinstance(cia, str):
            return "NA"
        if cia == row["alt"]:
            return d
        if cia == row["ref"]:
            return "DOWN" if d == "UP" else "UP"
        return "ALLELE_MISMATCH"

    long["direction_for_cognition_increasing_allele"] = long.apply(cog_dir, axis=1)
    for c in OUT_COLS:
        if c not in long.columns:
            long[c] = pd.NA
    extra = [c for c in long.columns if c not in OUT_COLS]
    out = long[OUT_COLS + extra]
    obj = out.select_dtypes(include="object").columns
    out[obj] = out[obj].astype("string")
    return out


# --------------------------------------------------------------------------- backends


def client_version() -> tuple[int, ...]:
    try:
        v = importlib_metadata.version("alphagenome")
    except importlib_metadata.PackageNotFoundError:
        return ()
    return tuple(int(x) for x in v.split(".")[:3] if x.isdigit())


def run_atlas(api_key: str, variants: pd.DataFrame, scorers: list[str] | None,
              all_tissues: bool, workers: int) -> tuple[pd.DataFrame, dict]:
    from alphagenome.atlas import atlas
    from alphagenome.data import genome

    client = atlas.create(api_key)
    meta = client.scorer_metadata()  # authenticated call; lists every Atlas scorer
    names = scorers or sorted(meta)
    unknown = sorted(set(names) - set(meta))
    if unknown:
        raise SystemExit(f"unknown Atlas scorers {unknown}; available: {sorted(meta)}")
    gv = [genome.Variant(chromosome="chr" + r.chr38, position=int(r.pos38),
                         reference_bases=r.ref, alternate_bases=r.alt)
          for r in variants.itertuples(index=False)]
    ontology_terms = None if all_tissues else sorted(BRAIN_ONTOLOGY)
    res = client.query_variants(gv, requested_scorers=names, ontology_terms=ontology_terms,
                                max_workers=workers)
    parts = [tidy_atlas_anndata(n, ad, meta[n].is_signed) for n, ad in res.items()]
    info = {"atlas_scorers_available": {n: {"is_signed": m.is_signed,
                                            "n_tracks": int(len(m.track_metadata))}
                                        for n, m in meta.items()},
            "atlas_scorers_requested": names}
    return (pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()), info


def run_model(api_key: str, variants: pd.DataFrame, all_tissues: bool) -> tuple[pd.DataFrame, dict]:
    from alphagenome.data import genome
    from alphagenome.models import dna_client, variant_scorers

    model = dna_client.create(api_key)
    recs = variant_scorers.get_recommended_scorers(dna_client.Organism.HOMO_SAPIENS)
    frames = []
    for r in variants.itertuples(index=False):
        v = genome.Variant(chromosome="chr" + r.chr38, position=int(r.pos38),
                           reference_bases=r.ref, alternate_bases=r.alt)
        interval = v.reference_interval.resize(dna_client.SEQUENCE_LENGTH_1MB)
        scores = model.score_variant(interval=interval, variant=v, variant_scorers=recs)
        t = variant_scorers.tidy_scores(scores, match_gene_strand=True)
        if t is not None:
            frames.append(t)
    if not frames:
        return pd.DataFrame(), {}
    t = pd.concat(frames, ignore_index=True)
    t = t.rename(columns={"variant_scorer": "scorer", "Assay title": "assay"})
    t["variant_id"] = t["variant_id"].astype(str)
    # signed = LFC / log2-ratio scorers; magnitude-only = splicing, contact maps, active-allele
    unsigned_kw = ("SPLIC", "CONTACT", "ACTIVE", "POLYADENYLATION")
    t["is_signed"] = ~t["scorer"].str.upper().str.contains("|".join(unsigned_kw))
    return t, {"recommended_scorers": [str(s) for s in recs]}


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variants", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--mode", choices=["atlas", "model"], default="atlas")
    ap.add_argument("--limit", type=int, default=None, help="first N unique rsids only")
    ap.add_argument("--scorers", nargs="*", default=None, help="Atlas scorer names (default: all)")
    ap.add_argument("--all-tissues", action="store_true", help="do not restrict to brain tracks")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)

    status = {"script": "pipelines/sprint5/alphagenome_query.py", "started_utc": utc_now(),
              "mode": a.mode, "variants_csv": str(a.variants), "limit": a.limit,
              "alphagenome_client_version": ".".join(map(str, client_version())) or None}
    variants = load_variants(a.variants, a.limit, snv_only=(a.mode == "atlas"))
    status["n_variant_alleles"] = int(len(variants))

    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        status.update(result="NOT_TESTABLE", reason=(
            f"{API_KEY_ENV} is not set. AlphaGenome Atlas track-level scores and live model "
            "predictions are only served through the authenticated AlphaGenome API; no public "
            "login-free copy exists."),
            user_action=("Obtain a free non-commercial AlphaGenome API key at "
                         "https://deepmind.google.com/science/alphagenome/api (Google sign-in + "
                         "acceptance of the AlphaGenome Terms), then export ALPHAGENOME_API_KEY."),
            finished_utc=utc_now())
        p = write_status(a.out, status)
        print(f"NOT_TESTABLE: {status['reason']}\nUser action: {status['user_action']}\nstatus -> {p}")
        return EXIT_NOT_TESTABLE

    if not status["alphagenome_client_version"]:
        raise SystemExit("alphagenome is not installed: pip install 'alphagenome>=0.9.0'")
    if a.mode == "atlas" and client_version() < MIN_CLIENT_VERSION_ATLAS:
        raise SystemExit("Atlas API needs alphagenome>=0.9.0 (released 2026-09-08)")

    if a.mode == "atlas":
        long, info = run_atlas(api_key, variants, a.scorers, a.all_tissues, a.workers)
    else:
        long, info = run_model(api_key, variants, a.all_tissues)
    out = finalise(long, variants, a.mode, a.all_tissues)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(a.out, index=False)
    status.update(info)
    status.update(result="OK", n_rows=int(len(out)),
                  n_variants_with_scores=int(out["variant_id"].nunique()) if len(out) else 0,
                  n_genes=int(out["gene_name"].nunique()) if len(out) else 0,
                  output=str(a.out), finished_utc=utc_now())
    p = write_status(a.out, status)
    print(json.dumps({k: status[k] for k in ("result", "n_rows", "n_variants_with_scores", "n_genes")}))
    print(f"parquet -> {a.out}\nstatus -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
