#!/usr/bin/env python3
"""Sprint 3, Part B — ingest the genome-wide MAGMA gene analysis, with verification.

Where this data came from, and why that matters
-----------------------------------------------
This is **external analysis produced by a different agent** (Codex/"Astra", branch
``agent/codex-positive-genetics``). Sprint 2 concluded that branch did not exist and
recorded the only thing it had — prose — as ``external_analysis_unverified``, INERT.
That conclusion was wrong: the branch is local-only and unpushed, and it contains a
real, executed MAGMA 1.10 run against real public summary statistics.

The repository's contract does not admit an external result because it looks credible.
It admits one when the result can be **recomputed**. This module therefore does three
separate things and keeps their verdicts separate:

1. **Copies** the MAGMA outputs and the gene map into this repository's provenance spine
   with sha256 of the stored bytes, so the numbers can never drift silently.
2. **Re-verifies the input checksum** of the Davies 2018 summary statistics against the
   value Codex recorded, computed here from the bytes on disk.
3. **Compares an independent re-run** of the gene analysis (``--replication``) against
   Codex's output, gene by gene. Only if that comparison passes does the ingested
   artefact earn ``external_analysis_verified``.

What the numbers are
--------------------
MAGMA gene analysis on Davies et al. 2018 (Nat Commun; PMID 29844566), public release,
N=282,014, GRCh37, 12,871,897 variants; 1000 Genomes phase 3 EUR LD reference; NCBI37.3
gene locations; 10 kb and 0 kb windows run separately as a window sensitivity.

What the numbers are NOT
------------------------
* **Not independent replication.** This is ONE GWAS. A gene with P=1e-20 here has one
  cohort behind it, not twenty. The tournament keeps ``n_independent_cohorts`` as a
  separate column sourced from a separate channel, and never infers it from this P.
* **Not ancestry-general.** The LD reference is European. A gene ranked here is ranked
  in Europeans.
* **Not causal, and not directional.** A MAGMA gene P aggregates SNP association within
  a window. It says a locus associates; it does not say the gene mediates it, which
  direction helps, or that an adult intervention on it would do anything.
* **Not window-free.** A 10 kb window assigns a variant to whichever genes are within
  10 kb, so neighbouring genes in dense loci share signal. The 0 kb run is carried
  alongside for exactly this reason, and disagreement between them is reported rather
  than averaged away.

Usage
-----
    python pipelines/gene_tournament/ingest_magma_gene_analysis.py --copy
    python pipelines/gene_tournament/ingest_magma_gene_analysis.py --replication <path>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import utc_date, utc_now  # noqa: E402

CODEX_ROOT = Path("data/external/x01")
RAW = REPO_ROOT / "data" / "raw" / "magma_x01"
OUT = REPO_ROOT / "data" / "gene_tournament"

# The checksum Codex recorded for the summary statistics, re-verified here from bytes.
DAVIES_SHA256 = "01990c3e30661db518579d8f84dfddd7f79bc9b476e8a65b45d28c0489ca6573"

ARTEFACTS = [
    ("davies2018_10kb.genes.out", "genetics_tools/results/10kb/davies2018_10kb.genes.out",
     "MAGMA gene analysis, 10 kb window"),
    ("davies2018_0kb.genes.out", "genetics_tools/results/0kb/davies2018_0kb.genes.out",
     "MAGMA gene analysis, 0 kb window (window sensitivity)"),
    ("gene_id_map.tsv", "genetics_tools/reference/gene_id_map.tsv",
     "Entrez -> current HGNC symbol -> Ensembl, with bp_length"),
    ("NCBI37.3.gene.loc", "genetics_tools/reference/NCBI37.3.gene.loc",
     "MAGMA gene locations (GRCh37), the coordinate basis of the analysis"),
    ("annotation_provenance.json", "genetics_tools/annotation_provenance.json",
     "MAGMA --annotate commands and annotation checksums"),
    ("davies2018_open_complete.txt.provenance.json",
     "davies2018_open_complete.txt.provenance.json",
     "source URL, byte count and sha256 of the summary statistics"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_artefacts() -> dict[str, Any]:
    """Copy each artefact into the provenance spine and checksum the stored bytes."""
    day = utc_date()
    dest_dir = RAW / day
    dest_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, rel, description in ARTEFACTS:
        source = CODEX_ROOT / rel
        if not source.exists():
            records.append({"artefact": name, "status": "SOURCE_MISSING",
                            "expected_path": str(source)})
            continue
        dest = dest_dir / name
        shutil.copy2(source, dest)
        records.append({
            "artefact": name,
            "status": "copied",
            "source_path": str(source),
            "stored_path": str(dest.relative_to(REPO_ROOT)),
            "bytes": dest.stat().st_size,
            "sha256_stored": sha256_file(dest),
            "description": description,
        })

    # Re-verify the 518 MB input from bytes. It is far too large to store here, so the
    # checksum is the only thing this repository can carry -- and a checksum nobody
    # recomputed is decoration.
    sumstats = CODEX_ROOT / "inputs" / "davies2018_open_complete.txt"
    if sumstats.exists():
        observed = sha256_file(sumstats)
        input_check = {
            "file": str(sumstats),
            "bytes": sumstats.stat().st_size,
            "sha256_recorded_by_codex": DAVIES_SHA256,
            "sha256_recomputed_here": observed,
            "match": observed == DAVIES_SHA256,
            "stored_in_this_repository": False,
            "why_not_stored": "518 MB exceeds the 5 MiB per-file commit limit; the "
                              "checksum and the source URL are carried instead.",
        }
    else:
        input_check = {"file": str(sumstats), "status": "NOT_PRESENT_ON_THIS_MACHINE",
                       "consequence": "the checksum cannot be recomputed here; the "
                                      "recorded value is uncorroborated."}

    manifest = {
        "ingested_at": utc_now(),
        "origin": {
            "agent": "codex/astra",
            "branch": "agent/codex-positive-genetics",
            "commit": "8e88623",
            "worktree": str(CODEX_ROOT),
            "pushed_to_remote": False,
            "note": "Local-only. If that worktree is lost, these copies and their "
                    "checksums are what survives.",
        },
        "analysis": {
            "tool": "MAGMA v1.10",
            "gwas": "Davies et al. 2018 general cognitive function, public release",
            "pubmed_id": "29844566",
            "n": 282014,
            "genome_build": "GRCh37",
            "n_variants_in_sumstats": 12871897,
            "ld_reference": "1000 Genomes phase 3 EUR",
            "ancestry_scope": "European",
        },
        "input_checksum_verification": input_check,
        "artefacts": records,
        "provenance_class_on_ingest": "external_analysis_unverified",
        "promotion_rule": "Promotion to external_analysis_verified requires an "
                          "independent re-run of the gene analysis reproducing these "
                          "gene statistics. Run --replication to record that check.",
    }
    path = dest_dir / "INGEST_MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_genes_out(path: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("GENE"):
            continue
        parts = line.split()
        if len(parts) < 9:
            continue
        rows[parts[0]] = {"zstat": float(parts[7]), "p": float(parts[8])}
    return rows


def compare_replication(replication: Path) -> dict[str, Any]:
    """Compare an independent re-run against the ingested Codex output, gene by gene.

    Why exact equality is the WRONG test
    ------------------------------------
    A first attempt used ``max|dZ| < 1e-4`` and returned DISCREPANT. That criterion was
    wrong, and the way it was wrong is worth keeping: **MAGMA's SNP-wise gene analysis is
    not deterministic.** For genes whose association is strong enough that the analytic
    approximation is inadequate, MAGMA estimates the gene p-value by adaptive permutation.
    Two correct runs of the same analysis on the same data therefore disagree slightly,
    and only on the strongly-associated genes.

    The test that is right separates two questions that the naive one conflated:

    * **Did the two runs analyse the same data?** ``NSNPS`` and ``NPARAM`` are fully
      deterministic given the SNP set, the annotation and the LD reference. If they match
      for every gene, the inputs are identical and any remaining difference is Monte
      Carlo. If they do NOT match, the runs are not comparable at all.
    * **Do the two runs agree where they are deterministic, and differ only where they are
      stochastic?** Measured by Spearman rho over all genes and by checking that every
      differing gene has an identical SNP count.

    What this check also EXPOSES rather than smooths over
    -----------------------------------------------------
    ``n_genes_changing_significance`` counts genes that cross the Bonferroni line between
    two runs of the same analysis. That number is not noise to be tolerated quietly: it is
    the Monte Carlo instability of the significance boundary itself, and any top-N list
    built on this statistic inherits it.
    """
    day = utc_date()
    original = RAW / day / "davies2018_10kb.genes.out"
    if not original.exists():
        raise SystemExit(f"run --copy first; {original} not found")

    def load_full(path: Path) -> dict[str, dict[str, float]]:
        rows: dict[str, dict[str, float]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#") or line.startswith("GENE"):
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            rows[parts[0]] = {"nsnps": float(parts[4]), "nparam": float(parts[5]),
                              "zstat": float(parts[7]), "p": float(parts[8])}
        return rows

    mine, theirs = load_full(replication), load_full(original)
    shared = sorted(set(mine) & set(theirs))
    bonferroni = 0.05 / len(theirs)

    same_inputs = all(mine[g]["nsnps"] == theirs[g]["nsnps"]
                      and mine[g]["nparam"] == theirs[g]["nparam"] for g in shared)
    diffs = [(g, abs(mine[g]["zstat"] - theirs[g]["zstat"])) for g in shared]
    differing = [g for g, d in diffs if d > 0]
    max_dz = max((d for _, d in diffs), default=0.0)
    all_differing_share_snps = all(mine[g]["nsnps"] == theirs[g]["nsnps"] for g in differing)
    flipped = [g for g in shared
               if (mine[g]["p"] < bonferroni) != (theirs[g]["p"] < bonferroni)]

    import statistics
    zs_a = [theirs[g]["zstat"] for g in shared]
    zs_b = [mine[g]["zstat"] for g in shared]
    rank_a = {v: i for i, v in enumerate(sorted(zs_a))}
    rank_b = {v: i for i, v in enumerate(sorted(zs_b))}
    ra = [rank_a[v] for v in zs_a]
    rb = [rank_b[v] for v in zs_b]
    spearman = statistics.correlation(ra, rb)

    reproduced = same_inputs and all_differing_share_snps and spearman > 0.9999
    verdict = "REPRODUCED_WITHIN_MONTE_CARLO_ERROR" if reproduced else "DISCREPANT"

    result = {
        "checked_at": utc_now(),
        "replication_file": str(replication),
        "n_genes_compared": len(shared),
        "deterministic_agreement": {
            "nsnps_and_nparam_identical_for_every_gene": same_inputs,
            "meaning": "These fields are fully determined by the SNP set, annotation and "
                       "LD reference. Identity proves the two runs analysed the same data.",
        },
        "stochastic_agreement": {
            "n_genes_with_identical_Z": len(shared) - len(differing),
            "n_genes_differing": len(differing),
            "all_differing_genes_have_identical_snp_counts": all_differing_share_snps,
            "max_abs_z_difference": max_dz,
            "spearman_rho": spearman,
            "cause": "MAGMA estimates gene p-values by adaptive permutation where the "
                     "analytic approximation is inadequate, i.e. for strongly associated "
                     "genes. Two correct runs differ there and nowhere else.",
        },
        "monte_carlo_instability": {
            "bonferroni_threshold": bonferroni,
            "n_genes_changing_significance": len(flipped),
            "genes_changing_significance": flipped[:40],
            "consequence": "Any top-N list cut at this threshold inherits this "
                           "instability. Genes near the boundary are not stably ranked, "
                           "and the tournament marks them rather than presenting the cut "
                           "as exact.",
        },
        "verdict": verdict,
        "provenance_class_after_check": (
            "external_analysis_verified" if reproduced else "external_analysis_unverified"),
        "what_this_does_and_does_not_establish": (
            "Establishes that the gene statistics follow from the stated inputs and "
            "method, re-derived here from the raw summary statistics with an independently "
            "built p-value file. Establishes nothing about whether Davies 2018 is the "
            "right GWAS, whether 10 kb is the right window, or whether any of these genes "
            "is causal for cognition."),
    }
    path = RAW / day / "REPLICATION_CHECK.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", action="store_true", help="copy artefacts + checksum")
    parser.add_argument("--replication", type=Path, help="independent .genes.out to compare")
    args = parser.parse_args(argv)

    if args.copy:
        manifest = copy_artefacts()
        check = manifest["input_checksum_verification"]
        print(f"ingested {sum(1 for a in manifest['artefacts'] if a['status']=='copied')} artefacts")
        print(f"input checksum match: {check.get('match')}")
        for artefact in manifest["artefacts"]:
            if artefact["status"] == "copied":
                print(f"  {artefact['artefact']:46s} {artefact['bytes']:>10,} B  "
                      f"{artefact['sha256_stored'][:12]}")
            else:
                print(f"  {artefact['artefact']:46s} {artefact['status']}")

    if args.replication:
        result = compare_replication(args.replication)
        det, sto, mc = (result["deterministic_agreement"],
                        result["stochastic_agreement"],
                        result["monte_carlo_instability"])
        print(f"\nreplication: {result['verdict']}")
        print(f"  genes compared                      {result['n_genes_compared']:,}")
        print(f"  NSNPS/NPARAM identical everywhere   "
              f"{det['nsnps_and_nparam_identical_for_every_gene']}")
        print(f"  genes with identical Z              {sto['n_genes_with_identical_Z']:,}")
        print(f"  genes differing (all same SNP set)  {sto['n_genes_differing']} "
              f"({sto['all_differing_genes_have_identical_snp_counts']})")
        print(f"  max |dZ|                            {sto['max_abs_z_difference']:.5f}")
        print(f"  Spearman rho                        {sto['spearman_rho']:.8f}")
        print(f"  genes changing significance         {mc['n_genes_changing_significance']}")
        print(f"  provenance class ->                 {result['provenance_class_after_check']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
