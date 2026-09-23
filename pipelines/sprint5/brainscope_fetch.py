#!/usr/bin/env python3
"""Sprint 5 — fetch the PUBLIC PsychENCODE brainSCOPE (Emani et al., Science 2024) scQTL files.

Only files served openly (no login, no click-through) from https://brainscope.gersteinlab.org/ are fetched.
Controlled items (imputed genotypes, FASTQs on Synapse syn51111084 / AD Knowledge Portal) are NOT touched;
they are recorded as access blockers in PROVENANCE.json by brainscope_provenance.py.

Everything lands in data/interim/sprint5/brainscope/ (gitignored). Each download is appended to
data/interim/sprint5/brainscope/download_log.jsonl with URL, UTC timestamp, bytes and sha256.
The pseudobulk expression matrices (709 MB) are NOT stored: they are streamed and reduced to their
gene-coordinate columns + sample count (sha256 recorded is that of the reduced file, flagged as such).

Usage: python pipelines/sprint5/brainscope_fetch.py [--skip-existing]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

BASE = "https://brainscope.gersteinlab.org"
DEST = C.WORK / "brainscope"
LOG = DEST / "download_log.jsonl"

SIG_CT = ["Astro", "Chandelier__Pvalb", "L2.3.IT", "L4.IT", "L5.6.NP", "L5.IT", "L6.CT", "L6.IT", "L6b",
          "Lamp5.Lhx6", "Lamp5", "Micro.PVM", "OPC", "Oligo", "PC", "Sst__Sst.Chodl", "Vip"]
ALL_CT = SIG_CT + ["Endo__VLMC", "Immune", "L5.ET", "L6.IT.Car3", "Pax6", "SMC", "Sncg"]
EDGE_CT = ["Ast", "Chandelier", "End", "Immune", "L2.3.IT", "L4.IT", "L5.6.NP", "L5.ET", "L5.IT", "L6.CT",
           "L6.IT.Car3", "L6.IT", "L6b", "Lamp5.Lhx6", "Lamp5", "Mic", "OPC", "Oli", "Pax6", "Pvalb", "Sncg", "Sst",
           "VLMC", "Vip"]
ISO_CT = ["Astro", "Chandelier_Pvalb", "Endo_VLMC", "Immune", "L2_3_IT", "L4_IT", "L5_6_NP", "L5_ET", "L5_IT",
          "L6_CT", "L6_IT_Car3", "L6_IT", "L6b", "Lamp5_Lhx6", "Lamp5", "Micro", "OPC", "Oligo", "PC", "Pax6",
          "SMC", "Sncg"]
GRN_CT = ["Ast", "Chandelier", "End", "Immune", "L2.3.IT", "L4.IT", "L5.6.NP", "L5.ET", "L5.IT", "L6.CT",
          "L6.IT.Car3", "L6.IT", "L6b", "Lamp5", "Mic", "OPC", "Oli", "Pax6", "Pvalb", "Sncg", "Sst", "VLMC", "Vip"]
COV_PCS = {"Immune": 20, "L5.ET": 20, "PC": 20, "Pax6": 20, "SMC": 20}


def manifest() -> list[tuple[str, str]]:
    """(url, relative destination) for every stored file."""
    m = [(f"{BASE}/data/sig_QTLs.zip", "sig_QTLs.zip"),
         (f"{BASE}/data/sig_eGenes.zip", "sig_eGenes.zip"),
         (f"{BASE}/data/sample_metadata/PEC2_sample_metadata.txt", "PEC2_sample_metadata.txt"),
         (f"{BASE}/data/sample_metadata/PEC2_sample_mapping.xlsx", "PEC2_sample_mapping.xlsx"),
         (f"{BASE}/code/core_scqtl_processing_code.tar.gz", "code/core_scqtl_processing_code.tar.gz"),
         (f"{BASE}/data/bayesian_qtl/bayesian_scQTLs.dat", "bayesian_scQTLs.dat"),
         (f"{BASE}/data/qtl_enrich/scQTL_disease_overlap.txt", "scQTL_disease_overlap.txt"),
         (f"{BASE}/data/atac_peaks/scCRE.PeakCalls.zip", "scCRE.PeakCalls.zip"),
         (f"{BASE}/data/validation/starrseq_enhancers_merged_sig_qtls_fdr_0.05.bed",
          "starrseq_enhancers_merged_sig_qtls_fdr_0.05.bed")]
    for agg in ("excitatory", "inhibatory", "non_neuronal"):
        m.append((f"{BASE}/data/aggregated_qtl/{agg}__sig_QTLs.dat", f"aggregated_qtl/{agg}__sig_QTLs.dat"))
    for ct in SIG_CT:
        m.append((f"{BASE}/data/conditional_qtls_top_hits/conditional_top_variants_per_signal_{ct}.txt",
                  f"conditional_top_hits/conditional_top_variants_per_signal_{ct}.txt"))
        m.append((f"{BASE}/data/sig_QTLs_LD_pruned/{ct}_sig_QTLs.dat", f"sig_QTLs_LD_pruned/{ct}_sig_QTLs.dat"))
    for ct in ALL_CT:
        m.append((f"{BASE}/data/candidate_SNPs_for_QTL_calls/{ct}.SNPs.dat.gz", f"candidate_SNPs/{ct}.SNPs.dat.gz"))
        pcs = COV_PCS.get(ct, 100)
        m.append((f"{BASE}/data/qtl_covariates/{ct}.cov.{pcs}_expr_PCs.bed", f"qtl_covariates/{ct}.cov.{pcs}_expr_PCs.bed"))
    for ct in EDGE_CT:
        m.append((f"{BASE}/data/eQTL_edge/{ct}.eqtl_edge.txt", f"eQTL_edge/{ct}.eqtl_edge.txt"))
    for ct in ISO_CT:
        m.append((f"{BASE}/data/isoqtls_permuted/{ct}_significant_sCQTLs_p0.05.txt",
                  f"isoqtls/{ct}_significant_sCQTLs_p0.05.txt"))
    for ct in GRN_CT:  # cell-type GRNs: TF - enhancer - promoter - target-gene links (enhancer-gene links)
        m.append((f"{BASE}/data/GRNs/{ct}_GRN.txt", f"GRNs/{ct}_GRN.txt"))
    return m


_LOCK = threading.Lock()


def log(rec: dict) -> None:
    with _LOCK, LOG.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")


def already_ok(rel: str) -> bool:
    """True if the log holds an OK record for rel whose recorded size matches the file on disk."""
    out = DEST / rel
    if not (out.exists() and LOG.exists()):
        return False
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r.get("file") == rel and r.get("status") == "OK" and r.get("bytes") == out.stat().st_size:
            return True
    return False


def fetch(url: str, rel: str, skip: bool) -> None:
    out = DEST / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if skip and already_ok(rel):
        return
    ts = C.utc_now()
    r = subprocess.run(["curl", "-sS", "-f", "-L", "--retry", "3", "-o", str(out), url], capture_output=True, text=True)
    if r.returncode != 0:
        log({"url": url, "file": rel, "utc": ts, "status": "FAILED", "error": r.stderr.strip()})
        print("FAILED", url, r.stderr.strip())
        return
    log({"url": url, "file": rel, "utc": ts, "status": "OK", "bytes": out.stat().st_size,
         "sha256": C.sha256_file(out), "stored": "full file"})
    print("ok", rel, out.stat().st_size, flush=True)


def stream_pseudobulk(ct: str, skip: bool) -> None:
    """Stream <ct>.expr.bed.gz; keep only #chr,start,end,gene,length,strand + N samples (not the expression)."""
    rel = f"pseudobulk_genes/{ct}.genes.tsv"
    out = DEST / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    if skip and already_ok(rel):
        return
    url = f"{BASE}/data/pseudobulk_expr/{ct}.expr.bed.gz"
    ts = C.utc_now()
    h_src = hashlib.sha256()
    nbytes = 0
    with urllib.request.urlopen(url, timeout=600) as resp:
        raw = resp.read()
    h_src.update(raw)
    nbytes = len(raw)
    lines = []
    n_samples = None
    with gzip.open(io.BytesIO(raw), "rt") as fh:
        for i, line in enumerate(fh):
            f = line.rstrip("\n").split("\t")
            if i == 0:
                n_samples = len(f) - 6
                lines.append("\t".join(f[:6]) + "\n")
            else:
                lines.append("\t".join(f[:6]) + "\n")
    out.write_text("".join(lines))
    log({"url": url, "file": rel, "utc": ts, "status": "OK", "stored": "REDUCED (gene coordinate columns only; "
         "expression values discarded)", "source_bytes": nbytes, "source_sha256": h_src.hexdigest(),
         "bytes": out.stat().st_size, "sha256": C.sha256_file(out), "n_samples_in_matrix": n_samples,
         "n_genes": len(lines) - 1})
    print("ok (reduced)", rel, n_samples, len(lines) - 1, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--no-pseudobulk", action="store_true")
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch, url, rel, a.skip_existing) for url, rel in manifest()]
        if not a.no_pseudobulk:
            futs += [ex.submit(stream_pseudobulk, ct, a.skip_existing) for ct in ALL_CT]
        for f in futs:
            f.result()


if __name__ == "__main__":
    main()
