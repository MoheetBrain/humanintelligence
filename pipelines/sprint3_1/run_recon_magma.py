#!/usr/bin/env python3
"""Sprint 3.1 — MAGMA gene-set runs for the synaptic recon pass.

All runs use the Davies 2018 gene-level results (the same ``.genes.raw`` as Sprint 3) and the
full 18,418-gene universe, so specifications differ ONLY in their covariates:

    A   MAGMA internal covariates only (gene size, density, inverse MAC and their logs)
    B   A + log annotation density
    C   A + log LOEUF
    D   A + annotation density + LOEUF                (Sprint-3 covariates, fixed universe)
    E   D + generic neuronal expression (Siletti level + neuron-vs-glia specificity)
    E2  E + GTEx adult-brain expression level
    D_S3  exact Sprint-3 reproduction (its covariate file drops 1,349 unannotated genes)

Single-set (marginal, one-sided) runs cover SynGO, propagated GO BP/CC/MF, Reactome and the
recon sets. Joint and contrast models (two-sided) run on the recon sets only.

Outputs are written to ``data/interim/sprint3_1/magma`` and collected by
``analyse_recon.py``.
"""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MAGMA = Path("data/external/x01/"
             "genetics_tools/bin/magma")
GENES_RAW = REPO / "data" / "interim" / "magma_replication" / "davies2018_10kb.genes.raw"
D31 = REPO / "data" / "sprint3_1"
S3_SETS = REPO / "data" / "gene_tournament" / "pathway_sets"
S3_COVAR = REPO / "data" / "interim" / "magma_sets" / "gene_covariates.txt"
WORK = REPO / "data" / "interim" / "sprint3_1" / "magma"

SPECS = {
    "A": [],
    "B": ["log_annotation_density"],
    "C": ["log_LOEUF"],
    "D": ["log_annotation_density", "log_LOEUF"],
    "E": ["log_annotation_density", "log_LOEUF", "neuron_expr", "neuron_specificity"],
    "E2": ["log_annotation_density", "log_LOEUF", "neuron_expr", "neuron_specificity", "brain_expr_gtex"],
}
COLLECTIONS = {
    "syngo": S3_SETS / "syngo.setannot",
    "go_bp_prop": D31 / "go_bp_prop.setannot",
    "go_cc_prop": D31 / "go_cc_prop.setannot",
    "go_mf_prop": D31 / "go_mf_prop.setannot",
    "reactome": S3_SETS / "reactome_human.setannot",
    "recon": D31 / "recon_sets.setannot",
}
JOINT_MODELS = [
    "PRE POST",
    "PRE_ONLY POST_ONLY PRE_AND_POST",
    "PRE_ONLY PRE_AND_POST PRE_OR_POST",          # PRE_ONLY coef = pre-only minus post-only
    "POST_ONLY PRE_AND_POST PRE_OR_POST",         # POST_ONLY coef = post-only minus pre-only
    "PRE SYNAPSE",
    "POST SYNAPSE",
    "PRE NEURON_SPECIFIC_TOP20",
    "POST NEURON_SPECIFIC_TOP20",
    "SYNAPSE NEURON_SPECIFIC_TOP20",
    "SYNAPSE BRAIN_EXPRESSED_TOP50",
    "SYNAPSE THEME_neuron_projection",
    "PREMEMB POSTMEMB",
    "PREMEMB_ONLY PREPOSTMEMB_BOTH PREPOSTMEMB_UNION",
    "PRE_PROCESS POST_PROCESS",
    "PREPROC_ONLY PREPOSTPROC_BOTH PREPOSTPROC_UNION",
    "PSD PRE",
    "GOCC_PRESYNAPSE_PROP GOCC_POSTSYNAPSE_PROP",
    "RELEASE_MACHINERY ORGANISATION_TRAFFICKING",
    "RELEASE_ONLY RELEASE_AND_ORG RELEASE_OR_ORG",  # RELEASE_ONLY coef = release-only minus organisation-only
]


def magma_cmd(set_file: Path, spec: str, out: Path, joint: Path | None = None) -> list[str]:
    cmd = [str(MAGMA), "--gene-results", str(GENES_RAW), "--set-annot", str(set_file), "--out", str(out)]
    # analyse=sets keeps covariates out of the output; MAGMA forbids it alongside joint=.
    model = ["analyse=sets"] if (spec != "A" and joint is None) else []
    if spec == "D_S3":
        cmd += ["--gene-covar", str(S3_COVAR)]
        model += ["condition-hide=log_annotation_density,log_LOEUF"]
    elif SPECS.get(spec):
        cmd += ["--gene-covar", str(D31 / "gene_covariates_full.txt")]
        model += ["condition-hide=" + ",".join(SPECS[spec])]
    if joint is not None:
        model += [f"joint={joint}", "direction=both"]
    if model:
        cmd += ["--model"] + model
    return cmd


def run(cmd_out: tuple[list[str], Path]) -> tuple[str, bool, str]:
    cmd, out = cmd_out
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    ok = out.with_suffix(".gsa.out").exists()
    return out.name, ok, "" if ok else (proc.stdout + proc.stderr)[-600:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--only", default="", help="comma-separated job-name substrings")
    args = ap.parse_args(argv)
    WORK.mkdir(parents=True, exist_ok=True)
    joint_file = WORK / "joint_models.txt"
    joint_file.write_text("\n".join(JOINT_MODELS) + "\n", encoding="utf-8")

    jobs = []
    for spec in list(SPECS) + ["D_S3"]:
        for coll, path in COLLECTIONS.items():
            if spec == "D_S3" and coll not in ("syngo", "recon"):
                continue
            out = WORK / f"{coll}__{spec}"
            jobs.append((magma_cmd(path, spec, out), out))
        out = WORK / f"recon_joint__{spec}"
        jobs.append((magma_cmd(COLLECTIONS["recon"], spec, out, joint=joint_file), out))
    if args.only:
        keys = args.only.split(",")
        jobs = [j for j in jobs if any(k in j[1].name for k in keys)]
    print(f"{len(jobs)} MAGMA jobs, {args.workers} workers")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for name, ok, err in ex.map(run, jobs):
            print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else "\n" + err))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
