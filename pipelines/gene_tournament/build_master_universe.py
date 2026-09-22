#!/usr/bin/env python3
"""Sprint 3, Part A — the master cognition gene universe.

What this builds
----------------
One row per gene, with provenance kept SEPARATE for every phenotype channel, so that a
later rank can never accidentally sum educational attainment into direct cognition. The
output is ``data/gene_tournament/master_gene_universe.parquet``.

Three things this file is careful about
---------------------------------------
**1. Symbol identity is resolved, not assumed.** GWAS Catalog ``mapped_genes`` are free
text: they contain withdrawn symbols, previous symbols, aliases, and entries that are not
genes in the HGNC sense at all (``Y_RNA``, ``RNA5SP38``). Every symbol is resolved against
the HGNC complete set. A symbol that resolves through an alias to MORE THAN ONE approved
gene is **not** resolved — it is recorded as ambiguous and kept under its original string,
because silently picking one of two genes is how a ranking acquires a wrong gene at the
top.

**2. Educational attainment never touches direct cognition.** Channels are assigned from
``atlases/gene_tournament/phenotype_channels.yaml``. Direct and proxy counts are computed
in separate columns and never added. A gene supported only by EA has
``n_direct_studies == 0`` and will rank last in every direct rank — correctly.

**3. A study is not a cohort, and this file does not pretend otherwise.** Three separate
counts are carried: associations, distinct GWAS Catalog study accessions (GCST), and
distinct PubMed IDs. None of them is a cohort count. Cohort structure is resolved in a
separate step (``fetch_study_metadata.py``) from each study's own sample description, and
the column it produces is named for what it measures.

Hard limits inherited from the source, repeated in the artefact
---------------------------------------------------------------
* **Positional mapping.** A gene is here because an associated variant lies in or near it.
  This is size-biased: long genes and gene-dense loci accumulate hits for reasons that are
  not biology. ``bp_length`` is carried so that every downstream analysis can condition on
  it, and any rank that does not is marked as not having done so.
* **Ascertainment.** Only variants that passed a significance filter in a curated paper
  are here. A gene's absence is absence of *measurement*, never measured absence.
* **No gene-based test.** Nothing in this file is a gene-level association statistic.
  Those come from MAGMA in Part B, from a different source, and are joined in later.

Usage
-----
    python pipelines/gene_tournament/build_master_universe.py
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from _provenance import iter_snapshots, read_snapshot, utc_now  # noqa: E402

CHANNELS = REPO_ROOT / "atlases" / "gene_tournament" / "phenotype_channels.yaml"
OUT_DIR = REPO_ROOT / "data" / "gene_tournament"
REGISTRY = "gwas_catalog_tournament"

# "0.25 unit increase" / "0.31 unit decrease" / "1.04 unit increase" -- the Catalog's
# beta field is a rendered string, so direction is parsed from the words, not the sign.
DIRECTION = re.compile(r"\b(increase|decrease)\b", re.IGNORECASE)


def load_hgnc() -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    """Return (approved-symbol record map, alias/previous -> approved symbols).

    The second map deliberately holds a SET: an alias pointing at two approved genes is
    ambiguous and must stay that way.
    """
    path = sorted((REPO_ROOT / "data" / "raw" / "hgnc_complete").glob("*/hgnc_complete_set.txt.gz"))[-1]
    approved: dict[str, dict[str, Any]] = {}
    secondary: dict[str, set[str]] = collections.defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if (row.get("status") or "").strip() != "Approved":
                continue
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue
            approved[symbol] = {
                "hgnc_id": row.get("hgnc_id") or "",
                "approved_symbol": symbol,
                "locus_group": row.get("locus_group") or "",
                "locus_type": row.get("locus_type") or "",
                "entrez_id": (row.get("entrez_id") or "").strip(),
                "ensembl_gene_id": (row.get("ensembl_gene_id") or "").strip(),
                "chromosome_band": row.get("location") or "",
            }
            for field in ("alias_symbol", "prev_symbol"):
                for alt in (row.get(field) or "").split("|"):
                    alt = alt.strip()
                    if alt:
                        secondary[alt].add(symbol)
    return approved, secondary


def resolve(symbol: str, approved: dict[str, dict[str, Any]],
            secondary: dict[str, set[str]]) -> dict[str, Any]:
    if symbol in approved:
        return {**approved[symbol], "resolution": "approved_symbol",
                "input_symbol": symbol}
    candidates = secondary.get(symbol) or set()
    if len(candidates) == 1:
        only = next(iter(candidates))
        return {**approved[only], "resolution": "alias_or_previous_symbol",
                "input_symbol": symbol}
    if len(candidates) > 1:
        return {"hgnc_id": "", "approved_symbol": symbol, "locus_group": "",
                "locus_type": "", "entrez_id": "", "ensembl_gene_id": "",
                "chromosome_band": "", "input_symbol": symbol,
                "resolution": "ambiguous_alias",
                "ambiguous_between": sorted(candidates)}
    return {"hgnc_id": "", "approved_symbol": symbol, "locus_group": "",
            "locus_type": "", "entrez_id": "", "ensembl_gene_id": "",
            "chromosome_band": "", "input_symbol": symbol,
            "resolution": "not_in_hgnc"}


def trait_channel_map() -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    spec = yaml.safe_load(CHANNELS.read_text(encoding="utf-8"))
    trait_to_channel: dict[str, str] = {}
    for channel, body in spec["channels"].items():
        for efo in body["traits"]:
            trait_to_channel[efo] = channel
    channel_class: dict[str, str] = {}
    for klass, body in spec["evidence_classes"].items():
        for channel in body["channels"]:
            channel_class[channel] = klass
    return trait_to_channel, channel_class, spec


def iter_associations() -> Any:
    for path in iter_snapshots(REGISTRY):
        if "release" in path.name:
            continue
        payload = read_snapshot(path)
        for assoc in (payload.get("_embedded") or {}).get("associations") or []:
            yield assoc


def blank_channel() -> dict[str, Any]:
    return {"n_assoc": 0, "studies": set(), "pmids": set(), "best_p": None,
            "best_rsid": None, "best_effect_allele": None, "best_study": None,
            "n_increase": 0, "n_decrease": 0, "n_direction_unknown": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    approved, secondary = load_hgnc()
    trait_to_channel, channel_class, spec = trait_channel_map()
    tiers: dict[str, dict[str, str]] = {}
    tier_file = OUT_DIR / "study_classification.csv"
    if tier_file.exists():
        with tier_file.open(encoding="utf-8") as handle:
            for rec in csv.DictReader(handle):
                tiers[rec["accession_id"]] = rec
    else:
        print("! study_classification.csv absent: strict-tier columns will be empty")
    print(f"HGNC: {len(approved):,} approved symbols, {len(secondary):,} alias/previous strings")

    genes: dict[str, dict[str, Any]] = {}
    seen_assoc: set[int] = set()
    n_assoc = n_skipped_no_channel = 0

    for assoc in iter_associations():
        aid = assoc.get("association_id")
        if aid in seen_assoc:      # the same association appears under each of its traits
            continue
        seen_assoc.add(aid)
        n_assoc += 1

        efos = [t.get("efo_id") for t in (assoc.get("efo_traits") or []) if t.get("efo_id")]
        channels = {trait_to_channel[e] for e in efos if e in trait_to_channel}
        if not channels:
            n_skipped_no_channel += 1
            continue

        p = assoc.get("p_value")
        try:
            p = float(p) if p is not None else None
        except (TypeError, ValueError):
            p = None
        study = assoc.get("accession_id")
        pmid = str(assoc.get("pubmed_id") or "")
        alleles = assoc.get("snp_allele") or []
        rsid = alleles[0].get("rs_id") if alleles else None
        effect_allele = alleles[0].get("effect_allele") if alleles else None
        beta_text = str(assoc.get("beta") or "")
        hit = DIRECTION.search(beta_text)
        direction = hit.group(1).lower() if hit else None

        for symbol in assoc.get("mapped_genes") or []:
            symbol = (symbol or "").strip()
            if not symbol:
                continue
            entry = genes.setdefault(symbol, {
                "channels": collections.defaultdict(blank_channel),
                "co_reported_efo": set(), "locations": set(),
                "tier_studies": collections.defaultdict(set),
                "strict_units": set(), "strict_ukb_free_units": set(),
                "strict_channels": set(), "strict_best_p": None,
                "strict_increase": 0, "strict_decrease": 0,
            })
            tier_rec = tiers.get(study or "", {})
            tier = tier_rec.get("tier", "unclassified")
            entry["tier_studies"][tier].add(study)
            if tier == "direct_strict":
                entry["strict_units"].add(tier_rec.get("independence_unit"))
                if tier_rec.get("ukb_status") == "not_listed":
                    entry["strict_ukb_free_units"].add(tier_rec.get("independence_unit"))
                entry["strict_channels"].update(
                    c for c in channels if channel_class.get(c) == "direct_cognition")
                if p is not None and (entry["strict_best_p"] is None or p < entry["strict_best_p"]):
                    entry["strict_best_p"] = p
                if direction == "increase":
                    entry["strict_increase"] += 1
                elif direction == "decrease":
                    entry["strict_decrease"] += 1
            entry["co_reported_efo"].update(efos)
            for loc in assoc.get("locations") or []:
                entry["locations"].add(str(loc))
            for channel in channels:
                slot = entry["channels"][channel]
                slot["n_assoc"] += 1
                if study:
                    slot["studies"].add(study)
                if pmid:
                    slot["pmids"].add(pmid)
                if p is not None and (slot["best_p"] is None or p < slot["best_p"]):
                    slot.update(best_p=p, best_rsid=rsid, best_effect_allele=effect_allele,
                                best_study=study)
                if direction == "increase":
                    slot["n_increase"] += 1
                elif direction == "decrease":
                    slot["n_decrease"] += 1
                else:
                    slot["n_direction_unknown"] += 1

    print(f"associations: {n_assoc:,} distinct; {n_skipped_no_channel:,} carried no panel trait")
    print(f"raw mapped-gene strings: {len(genes):,}")

    direct_channels = spec["evidence_classes"]["direct_cognition"]["channels"]
    proxy_channels = spec["evidence_classes"]["proxy"]["channels"]

    rows: list[dict[str, Any]] = []
    resolutions = collections.Counter()
    for symbol, entry in genes.items():
        ident = resolve(symbol, approved, secondary)
        resolutions[ident["resolution"]] += 1
        row: dict[str, Any] = {
            "input_symbol": symbol,
            "approved_symbol": ident["approved_symbol"],
            "hgnc_id": ident["hgnc_id"],
            "entrez_id": ident["entrez_id"],
            "ensembl_gene_id": ident["ensembl_gene_id"],
            "locus_group": ident["locus_group"],
            "locus_type": ident["locus_type"],
            "chromosome_band": ident["chromosome_band"],
            "symbol_resolution": ident["resolution"],
            "ambiguous_between": "|".join(ident.get("ambiguous_between", [])),
            "locations": "|".join(sorted(entry["locations"])[:6]),
        }
        direct_studies: set[str] = set()
        direct_pmids: set[str] = set()
        proxy_studies: set[str] = set()
        best_direct_p = None
        best_direct_channel = None
        for channel in list(spec["channels"]):
            slot = entry["channels"].get(channel) or blank_channel()
            row[f"{channel}__n_assoc"] = slot["n_assoc"]
            row[f"{channel}__n_studies"] = len(slot["studies"])
            row[f"{channel}__n_pmids"] = len(slot["pmids"])
            row[f"{channel}__best_p"] = slot["best_p"]
            row[f"{channel}__best_rsid"] = slot["best_rsid"] or ""
            row[f"{channel}__best_effect_allele"] = slot["best_effect_allele"] or ""
            row[f"{channel}__best_study"] = slot["best_study"] or ""
            row[f"{channel}__n_increase"] = slot["n_increase"]
            row[f"{channel}__n_decrease"] = slot["n_decrease"]
            row[f"{channel}__studies"] = "|".join(sorted(slot["studies"]))
            if channel in direct_channels:
                direct_studies |= slot["studies"]
                direct_pmids |= slot["pmids"]
                if slot["best_p"] is not None and (best_direct_p is None or slot["best_p"] < best_direct_p):
                    best_direct_p, best_direct_channel = slot["best_p"], channel
            elif channel in proxy_channels:
                proxy_studies |= slot["studies"]

        row["n_direct_channels"] = sum(
            1 for c in direct_channels if (entry["channels"].get(c) or {}).get("n_assoc", 0) > 0)
        row["n_direct_studies"] = len(direct_studies)
        row["n_direct_pmids"] = len(direct_pmids)
        row["direct_studies"] = "|".join(sorted(direct_studies))
        row["best_direct_p"] = best_direct_p
        row["best_direct_channel"] = best_direct_channel or ""
        row["best_direct_neglog10p"] = (
            -math.log10(best_direct_p) if best_direct_p and best_direct_p > 0 else None)
        row["n_proxy_studies"] = len(proxy_studies)
        ts = entry["tier_studies"]
        row["n_strict_studies"] = len(ts.get("direct_strict", ()))
        row["n_strict_independence_units"] = len(entry["strict_units"])
        row["n_strict_ukb_free_units"] = len(entry["strict_ukb_free_units"])
        row["n_strict_channels"] = len(entry["strict_channels"])
        row["strict_channels"] = "|".join(sorted(entry["strict_channels"]))
        row["best_strict_p"] = entry["strict_best_p"]
        row["best_strict_neglog10p"] = (-math.log10(entry["strict_best_p"])
                                        if entry["strict_best_p"] else None)
        row["n_strict_increase"] = entry["strict_increase"]
        row["n_strict_decrease"] = entry["strict_decrease"]
        row["n_mtag_studies"] = len(ts.get("direct_mtag", ()))
        row["n_clinical_ageing_studies"] = len(ts.get("direct_clinical_or_ageing", ()))
        row["n_excluded_ea_cross_trait_studies"] = len(ts.get("excluded_ea_or_cross_trait", ()))
        row["strict_studies"] = "|".join(sorted(ts.get("direct_strict", ())))
        row["direct_evidence_present"] = row["n_direct_studies"] > 0
        row["proxy_only"] = row["n_direct_studies"] == 0 and row["n_proxy_studies"] > 0
        rows.append(row)

    rows.sort(key=lambda r: (-r["n_direct_studies"], -(r["best_direct_neglog10p"] or 0),
                             r["input_symbol"]))

    import pandas as pd  # imported late so the docstring is readable without pandas
    frame = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT_DIR / "master_gene_universe.parquet", index=False)

    summary = {
        "built_at": utc_now(),
        "n_rows": len(rows),
        "n_distinct_associations": n_assoc,
        "n_associations_without_panel_trait": n_skipped_no_channel,
        "symbol_resolution": dict(resolutions),
        "n_with_direct_evidence": int(sum(r["direct_evidence_present"] for r in rows)),
        "n_proxy_only": int(sum(r["proxy_only"] for r in rows)),
        "n_with_strict_direct_evidence": int(sum(r["n_strict_studies"] > 0 for r in rows)),
        "n_direct_only_via_nonstrict_tiers": int(sum(
            r["direct_evidence_present"] and r["n_strict_studies"] == 0 for r in rows)),
        "n_protein_coding": int(sum(r["locus_group"] == "protein-coding gene" for r in rows)),
        "channels": {c: int(sum(1 for r in rows if r[f"{c}__n_assoc"] > 0))
                     for c in spec["channels"]},
        "what_this_is_not": [
            "not a causal gene list",
            "not a gene-based association test",
            "not a cohort count",
            "absence of a gene is absence of measurement",
        ],
    }
    (OUT_DIR / "master_gene_universe_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"\nrows: {len(rows):,}   protein-coding: {summary['n_protein_coding']:,}")
    print(f"with direct-cognition evidence: {summary['n_with_direct_evidence']:,}")
    print(f"proxy-only (EA/clinical, no direct): {summary['n_proxy_only']:,}")
    print(f"with STRICT direct evidence: {summary['n_with_strict_direct_evidence']:,}")
    print(f"direct only via MTAG/clinical/excluded tiers: {summary['n_direct_only_via_nonstrict_tiers']:,}")
    print("symbol resolution:", dict(resolutions))
    print("per channel (genes with >=1 association):")
    for channel, count in sorted(summary["channels"].items(), key=lambda kv: -kv[1]):
        print(f"  {channel:32s} {count:6,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
