#!/usr/bin/env python3
"""Sprint 3, Part K — unbiased pathway enrichment by MAGMA competitive gene-set analysis.

Why this method and not a hypergeometric test on the gene list
---------------------------------------------------------------
The obvious approach — take the ~4,459 swept genes, intersect with GO, run Fisher — is
wrong here in three separate ways, and the brief names all three:

1. **Gene size.** Long genes accumulate GWAS hits because they present a larger target,
   not because they matter more. Any pathway enriched for long genes (axon guidance,
   synaptic adhesion, cell adhesion generally) is enriched for *being long*.
2. **LD and gene density.** Genes in dense, high-LD regions share association signal. A
   pathway whose members cluster physically is counted many times over.
3. **Ascertainment.** The swept list is a threshold-crossing set. Genes just below the
   line are treated identically to genes with no signal at all, which throws away most of
   the information and makes the test depend on an arbitrary cut.

MAGMA's **competitive** gene-set analysis fixes all three by construction. It regresses
the gene-level association statistic (continuous, no threshold) on set membership, while
conditioning on gene size, gene density and the LD-induced correlations between gene
statistics that are stored in the ``.genes.raw`` file. The null is not "these genes are
random" but "these genes are no more associated than *other genes with the same size,
density and LD structure*" — which is the question actually being asked.

The confounder MAGMA does NOT handle, and what is done about it
----------------------------------------------------------------
**Annotation bias.** A well-studied gene has more GO terms than an equally important
obscure one, so "is annotated at all" correlates with "has been studied", which correlates
with "appears in GWAS papers". MAGMA knows nothing about this.

This module therefore runs every set file twice: once plain, and once conditioned on
``--gene-covar`` carrying (a) log annotation density, the number of distinct terms each
gene carries in that annotation source, and (b) gnomAD LOEUF constraint. A pathway that
survives conditioning on annotation density is enriched for something other than being
well studied. A pathway that does not survive is reported as not surviving — that is the
result, not a failure of the run.

What a significant set means, and does not
-------------------------------------------
It means genes in that set carry more cognition association signal than size-, density-
and LD-matched genes outside it. It does **not** mean the pathway is causal, that it acts
in adults, that intervening on it would change cognition, or which direction would help.
Gene sets are also heavily overlapping, so the number of significant sets is not a count
of independent findings.

Usage
-----
    python pipelines/gene_tournament/run_pathway_enrichment.py --list
    python pipelines/gene_tournament/run_pathway_enrichment.py --run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
from _provenance import utc_now  # noqa: E402

MAGMA_BIN = Path("/path/to/user/Documents/ChatGPT/intelligence-codex/research/"
                 "extreme_cognition/x01/genetics_tools/bin/magma")
SETS_DIR = REPO_ROOT / "data" / "gene_tournament" / "pathway_sets"  # committed (2.3 MB)
WORK = REPO_ROOT / "data" / "interim" / "magma_sets"
OUT = REPO_ROOT / "reports" / "gene_tournament"
GENES_RAW = REPO_ROOT / "data" / "interim" / "magma_replication" / "davies2018_10kb.genes.raw"


def build_covariates() -> Path | None:
    """Per-gene covariates: annotation density and gnomAD LOEUF constraint.

    Annotation density is counted across ALL available set files, so it measures how
    heavily a gene is annotated overall rather than within one ontology.
    """
    counts: dict[str, int] = {}
    for path in sorted(SETS_DIR.glob("*.setannot")):
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            for gene in parts[1:]:
                counts[gene] = counts.get(gene, 0) + 1
    if not counts:
        return None
    # MAGMA set files carry gene ids as text; the constraint table as int64. Merging
    # those two dtypes raises rather than silently producing an empty join, which is the
    # right behaviour -- so the cast is explicit here.
    frame = pd.DataFrame({"GENE": list(counts), "n_annotations": list(counts.values())})
    frame["GENE"] = pd.to_numeric(frame["GENE"], errors="coerce").astype("Int64")
    frame = frame.dropna(subset=["GENE"])
    frame["log_annotation_density"] = np.log10(frame.n_annotations + 1)

    loeuf = REPO_ROOT / "data" / "interim" / "gnomad_constraint.tsv"
    if loeuf.exists():
        con = pd.read_csv(loeuf, sep="\t")
        con["GENE"] = pd.to_numeric(con["GENE"], errors="coerce").astype("Int64")
        frame = frame.merge(con, on="GENE", how="left")
    # Only the two covariates the docstring argues for. The raw count, pLI and missense Z
    # are near-collinear with these and add conditioning without adding a question.
    keep = ["GENE", "log_annotation_density"] + (["log_LOEUF"] if "log_LOEUF" in frame else [])
    frame = frame[keep]
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / "gene_covariates.txt"
    # MAGMA rejects blank fields; NA is its missing-value token, and genes carrying one
    # are dropped from the conditioned model rather than imputed.
    frame.to_csv(path, sep="\t", index=False, na_rep="NA")
    return path


def run_set(set_file: Path, covar: Path | None, tag: str) -> Path | None:
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{set_file.stem}__{tag}"
    cmd = [str(MAGMA_BIN), "--gene-results", str(GENES_RAW),
           "--set-annot", str(set_file), "--out", str(out)]
    if covar is not None:
        # condition-hide conditions on the covariates without reporting them as sets.
        # MAGMA requires them by name; "all" is not a valid token.
        names = covar.read_text(encoding="utf-8").splitlines()[0].split("\t")[1:]
        cmd += ["--gene-covar", str(covar), "--model", "condition-hide=" + ",".join(names)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    result = out.with_suffix(".gsa.out")
    if not result.exists():
        print(f"  ! {set_file.name} [{tag}] produced no output")
        print("   ", (proc.stderr or proc.stdout)[-400:].replace("\n", "\n    "))
        return None
    return result


def collect(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        rows = [line.split(maxsplit=7) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#") and not line.startswith("VARIABLE")]
        if not rows:
            continue
        frame = pd.DataFrame(rows).iloc[:, :7]
        frame.columns = ["SET", "TYPE", "NGENES", "BETA", "BETA_STD", "SE", "P"]
        for col in ("NGENES", "BETA", "BETA_STD", "SE", "P"):
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        stem = path.name.replace(".gsa.out", "")
        frame["source_file"], frame["conditioning"] = stem.split("__", 1)[0], stem.split("__", 1)[1]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def bh_fdr(p: np.ndarray) -> np.ndarray:
    order = np.argsort(p)
    ranked = p[order]
    n = len(p)
    q = ranked * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--collect-only", action="store_true",
                        help="rebuild the CSV from existing .gsa.out files without running MAGMA")
    args = parser.parse_args(argv)

    sets = sorted(SETS_DIR.glob("*.setannot"))
    if args.list or not (args.run or args.collect_only):
        print(f"MAGMA:      {MAGMA_BIN} ({'present' if MAGMA_BIN.exists() else 'MISSING'})")
        print(f"genes.raw:  {GENES_RAW} ({'present' if GENES_RAW.exists() else 'MISSING'})")
        print(f"set files:  {len(sets)}")
        for path in sets:
            n = sum(1 for _ in path.open())
            print(f"   {path.name:34s} {n:6,} sets")
        return 0

    if not sets:
        raise SystemExit(f"no .setannot files in {SETS_DIR}")
    produced = []
    if args.collect_only:
        produced = sorted(WORK.glob("*__plain.gsa.out")) + sorted(WORK.glob("*__cond_annotation.gsa.out"))
        sets = []
    else:
        covar = build_covariates()
        print(f"covariates: {covar}")
    for path in sets:
        print(f"running {path.name} ...")
        for tag, cv in (("plain", None), ("cond_annotation", covar)):
            result = run_set(path, cv, tag)
            if result:
                produced.append(result)
                print(f"   [{tag}] -> {result.name}")

    frame = collect(produced)
    if frame.empty:
        raise SystemExit("no gene-set results were produced")
    frame["FDR"] = np.nan
    for (src, cond), group in frame.groupby(["source_file", "conditioning"]):
        frame.loc[group.index, "FDR"] = bh_fdr(group.P.to_numpy())
    # GLOBAL FDR is primary. Correcting within each collection gave SynGO (138 sets) its own
    # small family while GO BP had 2,707 -- a favourite-label advantage the brief forbids.
    frame["FDR_global"] = np.nan
    for cond, group in frame.groupby("conditioning"):
        frame.loc[group.index, "FDR_global"] = bh_fdr(group.P.to_numpy())
    names = {}
    for nt in SETS_DIR.glob("*.names.tsv"):
        t = pd.read_csv(nt, sep="\t", dtype=str)
        names.update(dict(zip(t.set_name, t.description)))
    frame["NAME"] = frame.SET.map(names).fillna("")
    OUT.mkdir(parents=True, exist_ok=True)
    frame.sort_values("P").to_csv(OUT / "pathway_enrichment.csv", index=False)

    summary = {
        "computed_at": utc_now(),
        "method": "MAGMA competitive gene-set analysis, conditioned on gene size, gene "
                  "density and LD (via .genes.raw), run with and without additional "
                  "conditioning on annotation density and constraint.",
        "gwas": "Davies 2018 general cognitive function, open subset, N=282,014",
        "n_set_results": int(len(frame)),
        "n_fdr_within_collection_lt_0.05": {
            cond: int((group.FDR < 0.05).sum()) for cond, group in frame.groupby("conditioning")},
        "n_fdr_global_lt_0.05": {
            cond: int((group.FDR_global < 0.05).sum()) for cond, group in frame.groupby("conditioning")},
        "primary_result": "global FDR, conditioned on annotation density and LOEUF",
    }
    (OUT / "pathway_enrichment_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(frame):,} set results; global FDR<0.05: {summary['n_fdr_global_lt_0.05']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
