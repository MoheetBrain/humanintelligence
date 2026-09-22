#!/usr/bin/env python3
"""Sprint 3 — LD-aware locus blocks, so a ranked list is not a list of one signal.

The problem this solves
-----------------------
Ranking genes by a gene-based P and reading off the top 25 produces something that looks
like 25 findings and is not. The Davies 2018 MAGMA run puts five chromosome-16p11.2 genes
(SH2B1, ATXN2L, RABEP2, CD19, SULT1A2) and nine chromosome-3p21 genes in its top 25.
Those are not fifteen independent pieces of evidence. They are two.

MAGMA already computes what is needed to see this. ``--gene-results`` writes a
``.genes.raw`` file whose trailing columns are the **LD-induced correlations between each
gene's association statistic and those of the preceding genes** in the same block. Those
correlations are exactly the dependence that a naive top-N list ignores.

What this builds
----------------
An undirected graph with one node per gene and an edge wherever |r| >= a threshold, then
its connected components. Each component is an **LD locus block**. Downstream, a rank may
report at most one representative per block, or report the block, but it may not count
block members as independent.

Why a threshold and not a model
-------------------------------
Connected components at a fixed |r| are crude: a chain of moderately correlated genes can
merge two blocks that a human would call separate. That is a known and deliberate bias
toward *fewer, larger* blocks, i.e. toward under-counting independent signals. This errs
in the conservative direction — the direction that makes the evidence look weaker — which
is the correct way for this bias to point. Three thresholds are computed so the
sensitivity is visible rather than assumed.

Usage
-----
    python pipelines/gene_tournament/build_ld_loci.py --genes-raw <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import utc_now  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "gene_tournament"
THRESHOLDS = (0.1, 0.2, 0.4)


def parse_genes_raw(path: Path) -> tuple[list[int], list[list[float]]]:
    """Return gene ids in file order and, per gene, its correlations with PRECEDING genes.

    Format (MAGMA v1.10): ``GENE CHR START STOP NSNPS NPARAM N MAC ZSTAT r_1 ... r_k``
    where ``r_j`` is the correlation with the j-th preceding gene in the same block, so
    the last correlation is with the immediately preceding gene. Verified against
    ``.genes.out``: column 9 reproduces ZSTAT for all 18,418 genes.
    """
    ids: list[int] = []
    corrs: list[list[float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        ids.append(int(parts[0]))
        corrs.append([float(v) for v in parts[9:]])
    return ids, corrs


def components(ids: list[int], corrs: list[list[float]], threshold: float) -> dict[int, int]:
    parent = {gid: gid for gid in ids}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for index, row in enumerate(corrs):
        # row[j] pairs with the gene (len(row) - j) positions earlier in the file.
        for j, value in enumerate(row):
            if abs(value) >= threshold:
                other = index - (len(row) - j)
                if 0 <= other < index:
                    union(ids[index], ids[other])
    return {gid: find(gid) for gid in ids}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genes-raw", type=Path, required=True)
    args = parser.parse_args(argv)

    ids, corrs = parse_genes_raw(args.genes_raw)
    print(f"parsed {len(ids):,} genes from {args.genes_raw.name}")

    assignments: dict[str, dict[int, int]] = {}
    stats = {}
    for threshold in THRESHOLDS:
        mapping = components(ids, corrs, threshold)
        roots = {}
        for gid in ids:
            roots.setdefault(mapping[gid], []).append(gid)
        sizes = sorted((len(v) for v in roots.values()), reverse=True)
        assignments[str(threshold)] = mapping
        stats[str(threshold)] = {
            "n_blocks": len(roots),
            "n_singletons": sum(1 for s in sizes if s == 1),
            "largest_block": sizes[0],
            "blocks_over_10_genes": sum(1 for s in sizes if s > 10),
            "mean_block_size": round(len(ids) / len(roots), 3),
        }
        print(f"  |r|>={threshold}: {len(roots):,} blocks, largest {sizes[0]}, "
              f"{stats[str(threshold)]['n_singletons']:,} singletons")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    primary = assignments["0.2"]
    rows = [{"GENE": gid,
             "ld_block_r0.1": assignments["0.1"][gid],
             "ld_block_r0.2": assignments["0.2"][gid],
             "ld_block_r0.4": assignments["0.4"][gid]} for gid in ids]
    import pandas as pd
    pd.DataFrame(rows).to_parquet(OUT_DIR / "ld_loci.parquet", index=False)

    (OUT_DIR / "ld_loci_summary.json").write_text(json.dumps({
        "built_at": utc_now(),
        "source": str(args.genes_raw),
        "n_genes": len(ids),
        "thresholds": stats,
        "primary_threshold": 0.2,
        "bias_direction": "Connected components merge chained correlations, so blocks are "
                          "if anything too LARGE and independent signals too FEW. The bias "
                          "understates evidence, which is the safe direction.",
        "what_a_block_is_not": "A block is not a gene's causal locus. Membership says two "
                               "gene statistics are correlated through LD, not that one "
                               "gene explains the other.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote ld_loci.parquet ({len(set(primary.values())):,} blocks at |r|>=0.2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
