#!/usr/bin/env python3
"""Build MAGMA ``--set-annot`` gene-set files from downloaded pathway annotations.

WHAT THIS FILE IS
-----------------
MAGMA 1.10 competitive gene-set analysis needs gene sets in a plain whitespace
format, one set per line::

    SET_NAME  entrez1 entrez2 entrez3 ...

Gene identifiers must be **NCBI Entrez Gene IDs (integers)**, because the
upstream gene analysis used MAGMA's NCBI37.3 gene location file, which is
Entrez-keyed. This script converts the raw annotation releases acquired into
``data/raw/pathway_annotations/<date>/`` into that format, and writes a
companion ``<file>.names.tsv`` giving ``set_name -> description -> n_genes`` so
the accessions in the ``.setannot`` file stay human-interpretable.

Sources consumed (see PROVENANCE.json in the raw directory for exact URLs,
timestamps, byte counts and SHA256 digests):

  * ``NCBI2Reactome_All_Levels.txt``  - Reactome, Entrez -> pathway, CC0.
  * ``gene2go_human_9606.tsv.gz``     - NCBI gene2go, human subset, public domain.
  * ``go-basic.obo``                  - GO ontology, term names + namespaces, CC BY 4.0.
  * ``syngo1.3_complete_data.zip``    - SynGO 1.3 ontologies sheet (rolled-up sets).

LIMITATIONS YOU MUST STATE WHEN REPORTING RESULTS
-------------------------------------------------
1. **Annotation bias is the dominant confounder.** GO, Reactome and SynGO
   annotation density tracks *how much a gene has been studied*, not how
   biologically important it is. Genes discovered early, genes with commercial
   or disease relevance, and genes tractable to classical assays carry far more
   annotations than equally important but understudied genes. A gene set that
   comes out "enriched" may simply be a set of well-studied genes. MAGMA's
   competitive test conditions on gene size, gene density and LD - it does
   **not** condition on annotation density or study bias. This is a real,
   unmodelled confounder and must be reported alongside any enrichment result.
2. **Evidence codes are heterogeneous.** Most GO annotations are IEA
   (Inferred from Electronic Annotation): never manually reviewed. Restricting
   to experimental codes reduces noise but *increases* study bias, because
   experimental annotation is concentrated on well-studied genes. Neither
   choice is neutral, so ``--go-evidence`` is an explicit parameter and the
   chosen value is recorded in the build report. There is no silent default.
3. **The GO/Reactome hierarchies are redundant.** Parent and child terms share
   genes, so sets are heavily overlapping and their p-values are correlated.
   Multiple-testing correction that assumes independence will be anticonservative.
   Reactome "All Levels" deliberately includes every hierarchy level.
4. **NOT-qualified GO annotations are excluded** (they assert a gene is *not*
   involved); counting them as membership would be a straightforward error.
5. **Size filtering changes the answer.** Sets below ``--min-set-size`` give an
   unreliable competitive test; sets above ``--max-set-size`` are too diffuse to
   interpret. Both bounds are explicit parameters and counts are reported before
   and after filtering.
6. **Species filtering is by source annotation**, not by ortholog projection.
   Only records the upstream release itself labels human are used.

USAGE
-----
    python build_pathway_sets.py --offline

``--offline`` performs a strict local rebuild and never touches the network.
Without it the script additionally issues HTTP HEAD requests to warn when the
local raw copy looks stale; it never re-downloads silently. Acquisition is a
separate, provenance-recorded step.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
import sys
import zipfile
from collections import defaultdict

# --- Explicit, documented parameters -----------------------------------------
DEFAULT_MIN_SET_SIZE = 10      # below this MAGMA's competitive test is unreliable
DEFAULT_MAX_SET_SIZE = 2000    # above this a set is too diffuse to interpret
DEFAULT_TAX_ID = "9606"        # Homo sapiens
DEFAULT_REACTOME_SPECIES = "Homo sapiens"

# GO evidence code groupings (Gene Ontology Consortium definitions).
EVIDENCE_EXPERIMENTAL = {"EXP", "IDA", "IPI", "IMP", "IGI", "IEP",
                         "HTP", "HDA", "HMP", "HGI", "HEP"}
EVIDENCE_ELECTRONIC = {"IEA"}
EVIDENCE_COMPUTATIONAL = {"ISS", "ISO", "ISA", "ISM", "IGC",
                          "IBA", "IBD", "IKR", "IRD", "RCA"}
EVIDENCE_AUTHOR_CURATOR = {"TAS", "NAS", "IC", "ND"}

GO_NAMESPACE_TO_KEY = {
    "biological_process": "bp",
    "molecular_function": "mf",
    "cellular_component": "cc",
}
# gene2go 'Category' column -> GO namespace
GO_CATEGORY_TO_NAMESPACE = {
    "Process": "biological_process",
    "Function": "molecular_function",
    "Component": "cellular_component",
}

SAFE_TOKEN = re.compile(r"[^A-Za-z0-9_.:-]+")
QUALIFIER_SPLIT = re.compile(r"[|,\s]+")


def safe_set_name(accession: str) -> str:
    """Turn an accession into a whitespace-free MAGMA set token.

    ``GO:0007268`` -> ``GO_0007268``;  ``R-HSA-112316`` stays as-is.
    """
    return SAFE_TOKEN.sub("_", accession.replace(":", "_").strip())


# --- Parsers -----------------------------------------------------------------

def parse_go_obo(path):
    """Return {go_id: (name, namespace)} for non-obsolete terms in go-basic.obo."""
    terms = {}
    cur, in_term = None, False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "[Term]":
                in_term, cur = True, {"id": None, "name": None, "ns": None, "obs": False}
                continue
            if line.startswith("["):          # e.g. [Typedef] - leave term context
                if in_term and cur and cur["id"] and not cur["obs"]:
                    terms[cur["id"]] = (cur["name"], cur["ns"])
                in_term, cur = False, None
                continue
            if not in_term or cur is None:
                continue
            if not line:                       # blank line closes the stanza
                if cur["id"] and not cur["obs"]:
                    terms[cur["id"]] = (cur["name"], cur["ns"])
                cur = {"id": None, "name": None, "ns": None, "obs": False}
                continue
            if line.startswith("id: "):
                cur["id"] = line[4:].strip()
            elif line.startswith("name: "):
                cur["name"] = line[6:].strip()
            elif line.startswith("namespace: "):
                cur["ns"] = line[11:].strip()
            elif line.startswith("is_obsolete: true"):
                cur["obs"] = True
    if in_term and cur and cur["id"] and not cur["obs"]:
        terms[cur["id"]] = (cur["name"], cur["ns"])
    return terms


def parse_gene2go(path, tax_id, evidence_policy):
    """Parse the human gene2go subset.

    Returns (sets_by_namespace, stats). ``sets_by_namespace`` maps
    'bp'/'mf'/'cc' -> {go_id: set(entrez_int)}.
    Rows whose Qualifier contains NOT are always excluded.
    """
    sets = {"bp": defaultdict(set), "mf": defaultdict(set), "cc": defaultdict(set)}
    g2g_names = {}
    stats = {
        "rows_total": 0, "rows_wrong_tax": 0, "rows_not_qualified": 0,
        "rows_unknown_category": 0, "rows_kept": 0, "rows_dropped_by_policy": 0,
        "evidence_counts": defaultdict(int),
        "evidence_counts_kept": defaultdict(int),
    }
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 8:
                continue
            tax, gene_id, go_id, evidence, qualifier, term_name, _pmid, category = parts[:8]
            stats["rows_total"] += 1
            if tax != tax_id:
                stats["rows_wrong_tax"] += 1
                continue
            stats["evidence_counts"][evidence] += 1
            # NOT-qualified annotations assert non-involvement: never membership.
            # gene2go writes these space-separated ("NOT involved_in"); GAF-style
            # sources use a pipe ("NOT|involved_in"). Split on both, plus commas,
            # so the exclusion cannot silently match nothing.
            if "NOT" in QUALIFIER_SPLIT.split(qualifier.upper().strip()):
                stats["rows_not_qualified"] += 1
                continue
            if not _evidence_allowed(evidence, evidence_policy):
                stats["rows_dropped_by_policy"] += 1
                continue
            ns = GO_CATEGORY_TO_NAMESPACE.get(category)
            key = GO_NAMESPACE_TO_KEY.get(ns) if ns else None
            if key is None:
                stats["rows_unknown_category"] += 1
                continue
            try:
                sets[key][go_id].add(int(gene_id))
            except ValueError:
                continue
            g2g_names.setdefault(go_id, term_name.strip())
            stats["rows_kept"] += 1
            stats["evidence_counts_kept"][evidence] += 1
    stats["evidence_counts"] = dict(stats["evidence_counts"])
    stats["evidence_counts_kept"] = dict(stats["evidence_counts_kept"])
    return sets, g2g_names, stats


def _evidence_allowed(code, policy):
    if policy == "all":
        return True
    if policy == "no-iea":
        return code not in EVIDENCE_ELECTRONIC
    if policy == "experimental":
        return code in EVIDENCE_EXPERIMENTAL
    raise ValueError(f"unknown evidence policy: {policy}")


def summarise_evidence(counts):
    """Group raw evidence-code counts into interpretable buckets."""
    out = defaultdict(int)
    for code, n in counts.items():
        if code in EVIDENCE_ELECTRONIC:
            out["electronic_IEA"] += n
        elif code in EVIDENCE_EXPERIMENTAL:
            out["experimental"] += n
        elif code in EVIDENCE_COMPUTATIONAL:
            out["computational_similarity"] += n
        elif code in EVIDENCE_AUTHOR_CURATOR:
            out["author_or_curator"] += n
        else:
            out["other"] += n
    out["total"] = sum(counts.values())
    return dict(out)


def parse_reactome(path, species):
    """Parse NCBI2Reactome*.txt -> ({pathway_id: set(entrez)}, {pathway_id: name}, stats)."""
    sets, names = defaultdict(set), {}
    stats = {"rows_total": 0, "rows_wrong_species": 0, "rows_kept": 0, "rows_bad_gene_id": 0}
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            gene_id, pathway_id, _url, pathway_name, _evidence, sp = parts[:6]
            stats["rows_total"] += 1
            if sp.strip() != species:
                stats["rows_wrong_species"] += 1
                continue
            try:
                sets[pathway_id].add(int(gene_id))
            except ValueError:
                stats["rows_bad_gene_id"] += 1
                continue
            names.setdefault(pathway_id, pathway_name.strip())
            stats["rows_kept"] += 1
    return sets, names, stats


def parse_syngo(zip_path):
    """Parse SynGO ontologies sheet -> ({go_id: set(entrez)}, {go_id: name}, stats).

    The ontologies table already contains the *hierarchical rollup* (a parent term
    lists genes annotated to its children), which is what a gene-set test needs.
    The annotations table does not, so it is deliberately not used here.
    """
    try:
        import openpyxl
    except ImportError:
        return None, None, {"error": "openpyxl not installed; SynGO sets not built"}
    sets, names = defaultdict(set), {}
    stats = {"terms_total": 0, "terms_kept": 0, "bad_gene_ids": 0}
    with zipfile.ZipFile(zip_path) as zf:
        member = next((n for n in zf.namelist() if n.endswith("ontologies.xlsx")), None)
        if member is None:
            return None, None, {"error": "ontologies.xlsx not found in SynGO archive"}
        tmp = os.path.join(os.path.dirname(zip_path), ".syngo_ontologies.xlsx")
        with open(tmp, "wb") as out:
            out.write(zf.read(member))
    try:
        wb = openpyxl.load_workbook(tmp, read_only=True)
        ws = wb[wb.sheetnames[0]]
        rows = ws.iter_rows(values_only=True)
        header = [str(c).strip() if c is not None else "" for c in next(rows)]
        idx = {h: i for i, h in enumerate(header)}
        for row in rows:
            if row is None or all(c is None for c in row):
                continue
            stats["terms_total"] += 1
            go_id = str(row[idx["id"]]).strip()
            name = str(row[idx["name"]]).strip()
            raw = row[idx["entrez_id"]]
            if not go_id or raw is None:
                continue
            for tok in str(raw).replace(";", ",").split(","):
                tok = tok.strip()
                if not tok or tok.lower() in {"none", "nan"}:
                    continue
                try:
                    sets[go_id].add(int(float(tok)))
                except ValueError:
                    stats["bad_gene_ids"] += 1
            names[go_id] = name
            stats["terms_kept"] += 1
        wb.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return sets, names, stats


# --- Writer ------------------------------------------------------------------

def write_setannot(sets, names, out_path, min_size, max_size, describe):
    """Write a MAGMA .setannot plus its .names.tsv. Returns a stats dict."""
    before_sets = len(sets)
    before_genes = set()
    for genes in sets.values():
        before_genes |= genes

    kept = {sid: g for sid, g in sets.items() if min_size <= len(g) <= max_size}
    after_genes = set()
    for genes in kept.values():
        after_genes |= genes

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        for sid in sorted(kept, key=lambda s: (-len(kept[s]), s)):
            gene_list = " ".join(str(g) for g in sorted(kept[sid]))
            fh.write(f"{safe_set_name(sid)} {gene_list}\n")

    names_path = out_path + ".names.tsv"
    with open(names_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["set_name", "accession", "description", "n_genes"])
        for sid in sorted(kept, key=lambda s: (-len(kept[s]), s)):
            w.writerow([safe_set_name(sid), sid,
                        (names.get(sid) or "").strip() or "NA", len(kept[sid])])

    return {
        "file": out_path,
        "names_file": names_path,
        "description": describe,
        "n_sets_before_filter": before_sets,
        "n_sets_after_filter": len(kept),
        "n_sets_removed_too_small": sum(1 for g in sets.values() if len(g) < min_size),
        "n_sets_removed_too_large": sum(1 for g in sets.values() if len(g) > max_size),
        "n_distinct_genes_before_filter": len(before_genes),
        "n_distinct_genes_after_filter": len(after_genes),
        "min_set_size": min_size,
        "max_set_size": max_size,
    }


def check_staleness(raw_dir, report):
    """Non-offline mode: HEAD upstream URLs and warn if the local copy looks stale."""
    import urllib.request
    prov = os.path.join(os.path.dirname(raw_dir.rstrip("/")), "PROVENANCE.json")
    if not os.path.exists(prov):
        report["staleness_check"] = "skipped: PROVENANCE.json not found"
        return
    try:
        with open(prov, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        report["staleness_check"] = f"skipped: could not read PROVENANCE.json ({exc})"
        return
    notes = []
    for entry in data.get("files", []):
        url, recorded = entry.get("url"), entry.get("http_last_modified")
        if not url:
            continue
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "intelligence-blueprint/0.1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                upstream = resp.headers.get("Last-Modified")
            if recorded and upstream and upstream != recorded:
                notes.append(f"STALE? {entry.get('name')}: local={recorded} upstream={upstream}")
            else:
                notes.append(f"ok {entry.get('name')}")
        except Exception as exc:
            notes.append(f"unchecked {entry.get('name')}: {exc}")
    report["staleness_check"] = notes


# --- Main --------------------------------------------------------------------

def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    # here = <repo>/pipelines/gene_tournament -> repo root is two levels up
    repo = os.path.dirname(os.path.dirname(here))
    ap = argparse.ArgumentParser(
        description="Build MAGMA --set-annot gene-set files from raw pathway annotations.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--raw-dir",
                    default=os.path.join(repo, "data", "raw", "pathway_annotations", "2026-09-22"),
                    help="Directory holding the downloaded raw annotation files.")
    ap.add_argument("--out-dir", default=os.path.join(repo, "data", "gene_tournament", "pathway_sets"),
                    help="Directory to write .setannot and .names.tsv files into.")
    ap.add_argument("--min-set-size", type=int, default=DEFAULT_MIN_SET_SIZE,
                    help="Smallest gene set to keep (MAGMA is unreliable below this).")
    ap.add_argument("--max-set-size", type=int, default=DEFAULT_MAX_SET_SIZE,
                    help="Largest gene set to keep (above this a set is uninformative).")
    ap.add_argument("--tax-id", default=DEFAULT_TAX_ID, help="NCBI tax_id to retain.")
    ap.add_argument("--reactome-species", default=DEFAULT_REACTOME_SPECIES,
                    help="Reactome species string to retain.")
    ap.add_argument("--reactome-file", default="NCBI2Reactome_All_Levels.txt",
                    help="Which Reactome mapping to build from.")
    ap.add_argument("--go-evidence", choices=["all", "no-iea", "experimental"], default="all",
                    help="GO evidence-code policy. Explicit by design; not a silent default.")
    ap.add_argument("--offline", action="store_true",
                    help="Strict local rebuild; never touch the network.")
    args = ap.parse_args(argv)

    raw, out = args.raw_dir, args.out_dir
    os.makedirs(out, exist_ok=True)
    report = {
        "parameters": {
            "min_set_size": args.min_set_size, "max_set_size": args.max_set_size,
            "tax_id": args.tax_id, "reactome_species": args.reactome_species,
            "reactome_file": args.reactome_file, "go_evidence_policy": args.go_evidence,
            "offline": args.offline,
        },
        "raw_dir": raw, "out_dir": out, "outputs": [],
    }

    if not args.offline:
        check_staleness(raw, report)
    else:
        report["staleness_check"] = "skipped: --offline"

    # GO term names / namespaces
    obo_path = os.path.join(raw, "go-basic.obo")
    go_terms = parse_go_obo(obo_path) if os.path.exists(obo_path) else {}
    report["go_obo_terms_parsed"] = len(go_terms)

    # ---- GO ----
    g2g = os.path.join(raw, "gene2go_human_9606.tsv.gz")
    if os.path.exists(g2g):
        go_sets, g2g_names, go_stats = parse_gene2go(g2g, args.tax_id, args.go_evidence)
        report["gene2go_stats"] = {k: v for k, v in go_stats.items()
                                  if k not in ("evidence_counts", "evidence_counts_kept")}
        report["go_evidence_breakdown_all_human_rows"] = summarise_evidence(go_stats["evidence_counts"])
        report["go_evidence_breakdown_kept_rows"] = summarise_evidence(go_stats["evidence_counts_kept"])
        report["go_evidence_codes_raw"] = go_stats["evidence_counts"]

        name_src = {"from_obo": 0, "from_gene2go_fallback": 0, "unnamed": 0}
        ns_mismatch = []
        for key, label in [("bp", "Biological Process"), ("cc", "Cellular Component"),
                           ("mf", "Molecular Function")]:
            names = {}
            for gid in go_sets[key]:
                obo_name, obo_ns = go_terms.get(gid, (None, None))
                if obo_name:
                    names[gid] = obo_name
                    name_src["from_obo"] += 1
                elif g2g_names.get(gid):
                    names[gid] = g2g_names[gid]
                    name_src["from_gene2go_fallback"] += 1
                else:
                    names[gid] = "NA"
                    name_src["unnamed"] += 1
                if obo_ns and GO_NAMESPACE_TO_KEY.get(obo_ns) != key:
                    ns_mismatch.append({"go_id": gid, "gene2go_category_key": key,
                                        "obo_namespace": obo_ns})
            report["outputs"].append(write_setannot(
                go_sets[key], names, os.path.join(out, f"go_{key}_human.setannot"),
                args.min_set_size, args.max_set_size,
                f"GO {label}, human (tax_id {args.tax_id}), evidence policy '{args.go_evidence}'"))
        report["go_term_name_source"] = name_src
        report["go_namespace_mismatches_gene2go_vs_obo"] = {
            "count": len(ns_mismatch), "examples": ns_mismatch[:10]}
    else:
        report["outputs"].append({"file": "go_*_human.setannot", "error": f"missing {g2g}"})

    # ---- Reactome ----
    rx = os.path.join(raw, args.reactome_file)
    if os.path.exists(rx):
        rx_sets, rx_names, rx_stats = parse_reactome(rx, args.reactome_species)
        report["reactome_stats"] = rx_stats
        report["outputs"].append(write_setannot(
            rx_sets, rx_names, os.path.join(out, "reactome_human.setannot"),
            args.min_set_size, args.max_set_size,
            f"Reactome pathways, {args.reactome_species}, from {args.reactome_file}"))
    else:
        report["outputs"].append({"file": "reactome_human.setannot", "error": f"missing {rx}"})

    # ---- SynGO ----
    sg = os.path.join(raw, "syngo1.3_complete_data.zip")
    if os.path.exists(sg):
        sg_sets, sg_names, sg_stats = parse_syngo(sg)
        report["syngo_stats"] = sg_stats
        if sg_sets:
            report["outputs"].append(write_setannot(
                sg_sets, sg_names, os.path.join(out, "syngo.setannot"),
                args.min_set_size, args.max_set_size,
                "SynGO 1.3 synaptic terms (hierarchically rolled-up ontologies table)"))
    else:
        report["syngo_stats"] = {"error": f"missing {sg}; SynGO sets not built"}

    rpath = os.path.join(out, "BUILD_REPORT.json")
    with open(rpath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)

    for o in report["outputs"]:
        if "error" in o:
            print(f"ERROR {o['file']}: {o['error']}")
        else:
            print(f"{os.path.basename(o['file']):28s} "
                  f"sets {o['n_sets_before_filter']:6d} -> {o['n_sets_after_filter']:6d}   "
                  f"genes {o['n_distinct_genes_before_filter']:6d} -> "
                  f"{o['n_distinct_genes_after_filter']:6d}")
    print(f"\nBuild report: {rpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
