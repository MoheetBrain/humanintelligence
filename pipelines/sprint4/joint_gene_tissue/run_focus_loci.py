"""Joint gene/tissue TWAS fine-mapping (FOCUS) at three Sprint-4 cognition loci.

Runs FOCUS (Mancuso et al. 2019 Nat Genet; maintained code base mancusolab/ma-focus, pyfocus
0.803) in single-ancestry mode on the Davies 2018 general-cognitive-function GWAS (GRCh37,
Z + N only) with 1000 Genomes phase-3 EUR LD (503 people) and adult-brain eQTL weights from the
FOCUS authors' pre-built weight database (GTEx v7 PrediXcan elastic-net + CMC DLPFC FUSION).

FOCUS answers the three-way question per risk region:
  (i)   causal gene-tissue model   -> high PIP for one model, small credible set
  (ii)  correlated eQTL passenger  -> gene with large marginal TWAS |z| but low PIP
  (iii) non-mediated / unmodelled  -> high PIP on the NULL model (no modelled gene explains it)
The NULL model cannot separate a truly non-mediated SNP effect from mediation through a gene,
tissue, isoform or developmental stage that has no weight model; the report says so.

Must be run inside the isolated ``hi-focus`` conda env (see provenance JSON for the recipe):

    OMP_NUM_THREADS=3 OPENBLAS_NUM_THREADS=3 MKL_NUM_THREADS=3 VECLIB_MAXIMUM_THREADS=3 \
    DASK_SCHEDULER=synchronous mamba run -n hi-focus python \
        pipelines/sprint4/joint_gene_tissue/run_focus_loci.py --workdir <scratch>/jgt/work \
        --focus-db <scratch>/jgt/weights/focus.db --stage all

Stages: ``prepare`` (GWAS subset + munge, LD subsets, brain-only DB, GRCh37 gene-count prior),
``run`` (FOCUS finemap per locus x configuration), ``collect`` (CSV + provenance JSON).
Large intermediates stay in --workdir (outside the repo); only the CSV and the provenance JSON are
written into the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CODEX = Path("data/external/x01")
DAVIES_INPUT = CODEX / "inputs" / "davies2018_open_complete.txt"
DAVIES_SHA256 = "01990c3e30661db518579d8f84dfddd7f79bc9b476e8a65b45d28c0489ca6573"  # pipelines/sprint4/common.py
DAVIES_N = 282014
BFILE = CODEX / "genetics_tools" / "reference" / "g1000_eur"
GENE_LOC = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "NCBI37.3.gene.loc"

OUT_CSV = REPO_ROOT / "reports" / "sprint4" / "joint_gene_tissue_finemapping.csv"
OUT_PROV = REPO_ROOT / "data" / "sprint4" / "joint_gene_tissue_finemapping_provenance.json"

FOCUS_DB_URL = "https://www.dropbox.com/s/ep3dzlqnp7p8e5j/focus.db?dl=1"
FOCUS_DB_LINKED_FROM = "https://github.com/mancusolab/ma-focus/wiki (Home + Creating-a-weight-database)"
FOCUS_REPO = "https://github.com/mancusolab/ma-focus"
FOCUS_COMMIT = "f3a38fd70e7fa3f3c43a05c641201fdc45f1ab46"
METHOD = "FOCUS"
METHOD_VERSION = f"pyfocus 0.803 (mancusolab/ma-focus@{FOCUS_COMMIT[:7]}, single-ancestry mode)"

# Loci (GRCh37) from research/sprint4/frozen_hypotheses.json "loci".
LOCI = [
    {"locus_id": "L319", "band": "12q13.2", "chr": "12", "lead_snp": "rs772921", "lead_pos": 56403577,
     "lead_effect_allele": "T", "lead_davies_z": 6.46},
    {"locus_id": "L91869", "band": "3p21.1", "chr": "3", "lead_snp": "rs6778735", "lead_pos": 52565100,
     "lead_effect_allele": "T", "lead_davies_z": -7.717},
    {"locus_id": "L257194", "band": "1p31.1", "chr": "1", "lead_snp": "rs3101338", "lead_pos": 72750353,
     "lead_effect_allele": "A", "lead_davies_z": 7.246},
    {"locus_id": "L7009", "band": "12q13.12", "chr": "12", "lead_snp": "rs10875914", "lead_pos": 49422094,
     "lead_effect_allele": "A", "lead_davies_z": -6.443},  # added after Gate C coloc (multi-gene, strong colocs)
    {"locus_id": "L79922", "band": "17q12", "chr": "17", "lead_snp": "rs1005552", "lead_pos": 34949598,
     "lead_effect_allele": "T", "lead_davies_z": -5.532},  # added after Gate C coloc (multi-gene, strong colocs)
    {"locus_id": "L1565", "band": "22q13.2", "chr": "22", "lead_snp": "rs28670611", "lead_pos": 42531210,
     "lead_effect_allele": "T", "lead_davies_z": -6.635},  # added after Gate C coloc (multi-gene, strong colocs)
]

# Adult brain weight sets inside focus.db (refpanel ids). Spinal cord (18) and pituitary (37) are
# excluded on purpose: they are CNS/endocrine but not brain.
BRAIN_REFPANELS = {
    7: "brain_amygdala", 8: "brain_anterior_cingulate_cortex_ba24", 9: "brain_caudate_basal_ganglia",
    10: "brain_cerebellar_hemisphere", 11: "brain_cerebellum", 12: "brain_cortex",
    13: "brain_frontal_cortex_ba9", 14: "brain_hippocampus", 15: "brain_hypothalamus",
    16: "brain_nucleus_accumbens_basal_ganglia", 17: "brain_putamen_basal_ganglia",
    19: "brain_substantia_nigra", 49: "brain_dorsolateral_prefrontal_cortex",
}

# Analysis configurations. db: "brain" (13 adult-brain weight sets) or "all" (52 sets).
CONFIGS = [
    {
        "config": "joint_brain_gene_x_tissue_p1e-3",
        "db": "brain", "tissue": None, "prior": "0.001", "max_genes": 3,
        "description": "Every adult-brain gene-tissue model enters jointly (a gene measured in k brain "
                       "regions contributes k correlated models); prior 1e-3 per model (FOCUS paper default).",
    },
    {
        "config": "brain_prioritized_gene_prior_1_over_ngenes_grch37",
        "db": "brain", "tissue": "brain", "prior": "GENE_PRIOR_TSV", "max_genes": 3,
        "description": "One model per gene: best cv.R2 across the 13 adult-brain weight sets; prior "
                       "1/(number of genes overlapping the LD block) = maintained FOCUS default gene set "
                       "(bundled gencode_map_v38) placed on GRCh37 coordinates from GENCODE v38lift37 "
                       "(the bundled gencode files are GRCh38 while our blocks are GRCh37).",
    },
    {
        "config": "brain_prioritized_gene_p1e-3",
        "db": "brain", "tissue": "brain", "prior": "0.001", "max_genes": 3,
        "description": "As above but prior 1e-3 per gene (prior-sensitivity check).",
    },
    {
        "config": "brain_prioritized_proxy_tissue_fallback_p1e-3",
        "db": "all", "tissue": "brain", "prior": "0.001", "max_genes": 3,
        "description": "One model per gene: adult-brain model if one exists, otherwise the best cv.R2 "
                       "model from any of the other 39 weight sets (non-brain proxy tissue); prior 1e-3.",
    },
    {
        "config": "joint_brain_gene_x_tissue_p1e-3_intercept",
        "db": "brain", "tissue": None, "prior": "0.001", "max_genes": 3, "intercept": True,
        "description": "As joint_brain_gene_x_tissue_p1e-3 but with FOCUS --intercept, which regresses the "
                       "average LD-tagged (non-mediated/pleiotropic) SNP signal out of the TWAS z-scores "
                       "before fine-mapping.",
    },
    {
        "config": "brain_prioritized_gene_p1e-3_intercept",
        "db": "brain", "tissue": "brain", "prior": "0.001", "max_genes": 3, "intercept": True,
        "description": "As brain_prioritized_gene_p1e-3 but with FOCUS --intercept (see above).",
    },
    {
        "config": "gtexv8_eur_brain_cortex_only_p1e-3",
        "db": "gtexv8_cortex", "tissue": None, "prior": "0.001", "max_genes": 3,
        "description": "Independent weight build: GTEx v8 EUR Brain_Cortex FUSION weights (gusevlab; heritable "
                       "genes only, best-cv.R2 model per gene chosen by focus import); single tissue so one model "
                       "per gene; prior 1e-3. Only this one v8 brain tissue was downloadable in the time budget.",
    },
    {
        "config": "gtexv8_eur_brain_cortex_only_p1e-3_intercept",
        "db": "gtexv8_cortex", "tissue": None, "prior": "0.001", "max_genes": 3, "intercept": True,
        "description": "As gtexv8_eur_brain_cortex_only_p1e-3 but with FOCUS --intercept.",
    },
]

THREAD_ENV = {
    "OMP_NUM_THREADS": "3", "OPENBLAS_NUM_THREADS": "3", "MKL_NUM_THREADS": "3",
    "VECLIB_MAXIMUM_THREADS": "3", "NUMEXPR_NUM_THREADS": "3", "DASK_SCHEDULER": "synchronous",
}


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], log: Path, commands: list, cwd: Path | None = None) -> float:
    env = dict(os.environ, **THREAD_ENV)
    t0 = time.time()
    with log.open("w") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, env=env, cwd=cwd)
    dt = time.time() - t0
    commands.append({"cmd": " ".join(cmd), "log": str(log), "exit_code": proc.returncode,
                     "seconds": round(dt, 1), "finished_utc": utc_now()})
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)} -- see {log}")
    return dt


def ld_blocks() -> list[tuple[str, int, int]]:
    import pyfocus  # noqa: F401  (only to locate the bundled BED)
    import pkg_resources

    bed = pkg_resources.resource_filename("pyfocus.data", "ld_blocks/grch37.eur.loci.bed")
    rows = []
    with open(bed) as fh:
        next(fh)
        for line in fh:
            c, s, e = line.split()[:3]
            rows.append((c.replace("chr", ""), int(s), int(e)))
    return rows


def block_for(locus: dict, blocks) -> tuple[int, int]:
    hits = [(s, e) for c, s, e in blocks if c == locus["chr"] and s <= locus["lead_pos"] < e]
    if len(hits) != 1:
        raise ValueError(f"{locus['locus_id']}: expected one Berisa-Pickrell block, got {hits}")
    return hits[0]


# ----------------------------------------------------------------------------------------- prepare
def stage_prepare(args, state: dict) -> None:
    work = Path(args.workdir)
    (work / "logs").mkdir(parents=True, exist_ok=True)
    (work / "ld").mkdir(exist_ok=True)
    blocks = ld_blocks()
    for locus in LOCI:
        locus["block_start"], locus["block_stop"] = block_for(locus, blocks)
    state["loci"] = LOCI

    # 1. GWAS: verify the input hash, then keep only SNPs inside the three LD blocks.
    state["inputs"]["davies_sha256_observed"] = sha256_file(DAVIES_INPUT)
    if state["inputs"]["davies_sha256_observed"] != DAVIES_SHA256:
        raise RuntimeError("Davies input sha256 differs from the value recorded in pipelines/sprint4/common.py")
    raw = work / "davies2018_focus_blocks.raw.txt"
    want = {(lc["chr"]): [] for lc in LOCI}
    for lc in LOCI:
        want[lc["chr"]].append((lc["block_start"], lc["block_stop"]))
    n_in = n_out = 0
    with DAVIES_INPUT.open() as fh, raw.open("w") as out:
        header = fh.readline().split()
        assert header == ["Chromosome", "Position", "Markername", "Effect_allele", "Other_allele", "P-value",
                          "Zscore"], header
        out.write("CHR\tBP\tSNP\tA1\tA2\tP\tZ\n")
        for line in fh:
            n_in += 1
            f = line.split()
            spans = want.get(f[0])
            if not spans:
                continue
            bp = int(f[1])
            if any(s <= bp <= e for s, e in spans):
                out.write(f"{f[0]}\t{bp}\t{f[2]}\t{f[3].upper()}\t{f[4].upper()}\t{f[5]}\t{f[6]}\n")
                n_out += 1
    state["inputs"]["davies_rows_total"] = n_in
    state["inputs"]["davies_rows_in_blocks"] = n_out
    focus = str(Path(sys.prefix) / "bin" / "focus")
    munged = work / "davies2018_focus_blocks"
    run([focus, "munge", str(raw), "--N", str(DAVIES_N), "--output", str(munged)],
        work / "logs" / "munge.log", state["commands"])
    state["inputs"]["munged_sumstats"] = str(munged) + ".sumstats.gz"
    state["inputs"]["munged_sumstats_sha256"] = sha256_file(Path(str(munged) + ".sumstats.gz"))

    # 2. LD reference: PLINK subset of 1000G EUR per block (source files are read-only).
    plink = shutil.which("plink") or str(Path(sys.prefix) / "bin" / "plink")
    for lc in LOCI:
        out = work / "ld" / f"{lc['locus_id']}_g1000_eur"
        run([plink, "--bfile", str(BFILE), "--chr", lc["chr"], "--from-bp", str(lc["block_start"]),
             "--to-bp", str(lc["block_stop"]), "--make-bed", "--threads", "3", "--memory", "4000",
             "--out", str(out)], work / "logs" / f"plink_{lc['locus_id']}.log", state["commands"])
        lc["ld_prefix"] = str(out)
        lc["ld_n_snps"] = sum(1 for _ in open(str(out) + ".bim"))

    # 3. Weight DBs: full author DB (52 sets) + adult-brain-only copy (13 sets).
    full_db = Path(args.focus_db)
    state["weights"]["focus_db_path"] = str(full_db)
    state["weights"]["focus_db_sha256"] = sha256_file(full_db)
    state["weights"]["focus_db_bytes"] = full_db.stat().st_size
    brain_db = work / "focus_brain_adult.db"
    shutil.copyfile(full_db, brain_db)
    keep = ",".join(str(i) for i in BRAIN_REFPANELS)
    con = sqlite3.connect(brain_db)
    got = dict(con.execute(f"select id, tissue from refpanel where id in ({keep})").fetchall())
    if got != BRAIN_REFPANELS:
        raise RuntimeError(f"refpanel ids in focus.db do not match expectation: {got}")
    t0 = time.time()
    con.executescript(f"""
        DELETE FROM weight WHERE model_id IN (SELECT id FROM model WHERE ref_id NOT IN ({keep}));
        DELETE FROM modelattribute WHERE model_id IN (SELECT id FROM model WHERE ref_id NOT IN ({keep}));
        DELETE FROM model WHERE ref_id NOT IN ({keep});
        DELETE FROM molecularfeature WHERE id NOT IN (SELECT mol_id FROM model);
        DELETE FROM refpanel WHERE id NOT IN ({keep});
    """)
    con.commit()
    con.execute("VACUUM")
    counts = {r[0]: r[1] for r in con.execute(
        "select r.ref_name || ':' || r.tissue, count(*) from model m join refpanel r on r.id=m.ref_id "
        "group by r.id order by r.id")}
    con.close()
    state["weights"]["brain_db_path"] = str(brain_db)
    state["weights"]["brain_db_sha256"] = sha256_file(brain_db)
    state["weights"]["brain_db_models_per_panel"] = counts
    state["weights"]["brain_db_build_seconds"] = round(time.time() - t0, 1)

    # 4. GRCh37 gene-count prior file (FOCUS --prior-prob path format: chrom start stop gene_name).
    # The maintained FOCUS default (--prior-prob gencode38) counts genes of its bundled GENCODE v38
    # table (GRCh38 coordinates) overlapping the block. Our blocks are GRCh37, so we keep exactly the
    # same gene set (gene_id without version) but take GRCh37 coordinates from GENCODE's official
    # v38lift37 GTF.
    import gzip
    import pkg_resources

    g38 = pkg_resources.resource_filename("pyfocus.data", "gencode/gencode_map_v38.tsv")
    with open(g38) as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        gi = hdr.index("gene_id") if "gene_id" in hdr else 4
        focus_ids = {line.rstrip("\n").split("\t")[gi].split(".")[0] for line in fh}
    gtf = Path(args.gencode_lift37_gtf)
    prior = work / "gencode_v38lift37_focus_gene_set_grch37.tsv"
    autos = {f"chr{i}" for i in range(1, 23)}
    seen = set()
    n_written = 0
    with gzip.open(gtf, "rt") as fh, prior.open("w") as out:
        out.write("chrom\tstart\tstop\tgene_name\n")
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.split("\t", 8)
            if f[2] != "gene" or f[0] not in autos:
                continue
            gid = re.search(r'gene_id "([^"]+)"', f[8]).group(1).split(".")[0]
            name = re.search(r'gene_name "([^"]+)"', f[8]).group(1)
            if gid not in focus_ids or gid in seen:
                continue
            seen.add(gid)
            out.write(f"{f[0][3:]}\t{f[3]}\t{f[4]}\t{name}\n")
            n_written += 1
    state["inputs"]["gene_prior_tsv"] = str(prior)
    state["inputs"]["gene_prior_rows"] = n_written
    state["inputs"]["focus_gencode38_gene_ids"] = len(focus_ids)
    state["inputs"]["gencode_lift37_gtf"] = str(gtf)
    state["inputs"]["gencode_lift37_gtf_sha256"] = sha256_file(gtf)
    state["inputs"]["gene_loc_ncbi37_sha256"] = sha256_file(GENE_LOC)
    for lc in LOCI:
        names = set()
        with prior.open() as fh:
            next(fh)
            for line in fh:
                c, s, e, g = line.rstrip("\n").split("\t")
                if c == lc["chr"] and min(int(e), lc["block_stop"]) - max(int(s), lc["block_start"]) > 0:
                    names.add(g)
        lc["gencode38_lift37_genes_in_block"] = len(names)
        n = 0
        with GENE_LOC.open() as fh:
            for line in fh:
                f = line.split()
                if f[1] == lc["chr"] and min(int(f[3]), lc["block_stop"]) - max(int(f[2]), lc["block_start"]) > 0:
                    n += 1
        lc["ncbi37_3_genes_in_block"] = n


# ------------------------------------------------------------------------------------ import GTEx v8
def stage_import_v8(args, state: dict) -> None:
    """Import GTEx v8 EUR Brain_Cortex FUSION weights (genes near the three blocks) with focus import.

    Only genes whose GRCh38 TSS (pos-file P0) lies within 1.5 Mb of a block (GRCh37 bounds; the
    GRCh37->GRCh38 shift here is < 0.5 Mb) are imported; FOCUS then keeps only models whose weight
    SNPs (matched by rsID) fall inside the GRCh37 block, so the margin only avoids missing genes.
    """
    import tarfile

    work = Path(args.workdir)
    arc = Path(args.gtexv8_cortex_archive)
    state["weights"]["gtexv8_cortex_archive"] = str(arc)
    state["weights"]["gtexv8_cortex_archive_sha256"] = sha256_file(arc)
    state["weights"]["gtexv8_cortex_archive_bytes"] = arc.stat().st_size
    out_dir = work / "gtexv8"
    out_dir.mkdir(exist_ok=True)
    with tarfile.open(arc, "r:gz") as tf:
        tf.extractall(out_dir)
    pos = out_dir / "GTExv8.EUR.Brain_Cortex.pos"
    sub = out_dir / "GTExv8.EUR.Brain_Cortex.3blocks.pos"
    margin = 1_500_000
    n = 0
    with pos.open() as fh, sub.open("w") as out:
        out.write(fh.readline())
        for line in fh:
            f = line.rstrip("\n").split("\t")
            for lc in state["loci"]:
                if f[3] == lc["chr"] and lc["block_start"] - margin < int(f[4]) < lc["block_stop"] + margin:
                    out.write(line)
                    n += 1
                    break
    state["weights"]["gtexv8_cortex_genes_imported"] = n
    db = work / "focus_gtexv8_eur_brain_cortex"
    Path(str(db) + ".db").unlink(missing_ok=True)
    focus = str(Path(sys.prefix) / "bin" / "focus")
    run([focus, "import", str(sub), "fusion", "--tissue", "brain_cortex", "--name", "gtexv8_eur", "--assay",
         "rnaseq", "--use-ens-id", "--from-gencode", "--output", str(db)],
        work / "logs" / "import_gtexv8_cortex.log", state["commands"])
    state["weights"]["gtexv8_cortex_db_path"] = str(db) + ".db"
    state["weights"]["gtexv8_cortex_db_sha256"] = sha256_file(Path(str(db) + ".db"))


# --------------------------------------------------------------------------------------------- run
def stage_run(args, state: dict) -> None:
    work = Path(args.workdir)
    (work / "focus_out").mkdir(exist_ok=True)
    focus = str(Path(sys.prefix) / "bin" / "focus")
    state["runs"] = []
    for lc in state["loci"]:
        for cfg in CONFIGS:
            db = {"brain": state["weights"]["brain_db_path"], "all": state["weights"]["focus_db_path"],
                  "gtexv8_cortex": state["weights"].get("gtexv8_cortex_db_path")}[cfg["db"]]
            if db is None:
                continue
            prior = state["inputs"]["gene_prior_tsv"] if cfg["prior"] == "GENE_PRIOR_TSV" else cfg["prior"]
            out = work / "focus_out" / f"{lc['locus_id']}.{cfg['config']}"
            # --start/--stop bracket the lead SNP so exactly the one LD block containing it is analysed.
            cmd = [focus, "finemap", state["inputs"]["munged_sumstats"], lc["ld_prefix"], db,
                   "--locations", "37:EUR", "--chr", lc["chr"], "--start", str(lc["lead_pos"]),
                   "--stop", str(lc["lead_pos"] + 1), "--prior-prob", prior,
                   "--max-genes", str(cfg["max_genes"]), "--credible-level", "0.9",
                   "--trait", "davies2018_cognition", "--verbose", "--out", str(out)]
            if cfg["tissue"]:
                cmd += ["--tissue", cfg["tissue"]]
            if cfg.get("intercept"):
                cmd += ["--intercept"]
            log = work / "logs" / f"focus_{lc['locus_id']}.{cfg['config']}.log"
            dt = run(cmd, log, state["commands"])
            tsv = Path(str(out) + ".focus.tsv")
            state["runs"].append({"locus_id": lc["locus_id"], "config": cfg["config"], "db": cfg["db"],
                                  "prior_arg": prior, "output": str(tsv), "log": str(log),
                                  "seconds": round(dt, 1),
                                  "output_sha256": sha256_file(tsv) if tsv.exists() else None})


# ----------------------------------------------------------------------------------------- collect
def _warnings(log: Path) -> list[str]:
    keep = []
    for line in log.read_text().splitlines():
        if re.search(r"WARNING|ERROR|Skipping", line) and "Skipping if following" not in line \
                and "will skip if following" not in line:
            msg = re.sub(r"^\S+ \S+ - ", "", line).strip()
            if msg not in keep:
                keep.append(msg)
    return keep


def _prior_from_log(log: Path) -> str:
    m = re.search(r"Using (?:fixed numeric|gencode file) prior probability ([0-9.eE-]+)", log.read_text())
    return m.group(1) if m else ""


def weights_source(ref_name: str, inference: str) -> str:
    if ref_name == "gtex":
        return f"GTEx v7 PredictDB {inference} weights (tw_0.5_signif) via FOCUS pre-built focus.db"
    if ref_name == "gtexv8_eur":
        return (f"GTEx v8 EUR Brain_Cortex FUSION weights (gusevlab.org; best model: {inference}) imported with "
                f"focus import")
    if ref_name == "cmc":
        return f"CommonMind DLPFC FUSION weights (best model: {inference}) via FOCUS pre-built focus.db"
    return f"{ref_name.upper()} FUSION weights ({inference}) via FOCUS pre-built focus.db"


class LeadTagging:
    """Diagnostic: correlation in 1000G EUR between a model's predicted expression and the lead SNP.

    r = corr(sum_j w_j * g_j_std, g_lead) on standardized genotypes (the scale FOCUS uses for its TWAS
    z = w'z / sqrt(w'Rw)), restricted - like FOCUS - to weight SNPs inside the LD block and present in
    the LD panel. |r| near 1 means the expression model is an almost perfect proxy of the lead SNP, so
    summary data cannot tell mediation through that gene from a non-mediated effect of the lead SNP.
    pandas_plink counts the bim a1 allele (column 6; verified against plink --freq), so each weight is
    oriented to a1 and r is finally signed relative to the Davies effect allele of the lead SNP. Then
    sign(TWAS z) should equal sign(r * lead z) when the lead SNP drives the model's association.
    """

    COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}

    def __init__(self, ld_prefix: str, lead_snp: str, lead_effect_allele: str, con: sqlite3.Connection,
                 chrom: str, start: int, stop: int):
        import numpy as np
        import pandas as pd
        from pandas_plink import read_plink

        bim, _, bed = read_plink(ld_prefix, verbose=False)
        G = np.asarray(bed.compute(), dtype=float)  # snps x samples
        mu = np.nanmean(G, axis=1, keepdims=True)
        G = np.where(np.isnan(G), mu, G)
        sd = G.std(axis=1, keepdims=True)
        sd[sd == 0] = np.nan
        self.Z = (G - G.mean(axis=1, keepdims=True)) / sd
        self.np = np
        self.idx = dict(zip(bim["snp"].values, bim["i"].values))
        self.a0 = dict(zip(bim["snp"].values, bim["a0"].astype(str).values))
        self.a1 = dict(zip(bim["snp"].values, bim["a1"].astype(str).values))
        self.lead = lead_snp
        self.lead_sign = 1.0 if self.a1.get(lead_snp) == lead_effect_allele else -1.0
        w = pd.read_sql(
            "select mf.ens_gene_id, r.tissue, r.ref_name, m.inference, w.snp, w.effect_allele, w.alt_allele, "
            "w.effect from weight w join model m on m.id=w.model_id join molecularfeature mf on mf.id=m.mol_id "
            "join refpanel r on r.id=m.ref_id where w.chrom=? and w.pos between ? and ?",
            con, params=(chrom, start, stop))
        self.w = {k: list(zip(g.snp, g.effect_allele, g.alt_allele, g.effect))
                  for k, g in w.groupby(["ens_gene_id", "tissue", "ref_name", "inference"])}

    def r(self, key) -> tuple[float | None, int]:
        np = self.np
        if self.lead not in self.idx:
            return None, 0
        lead = self.Z[self.idx[self.lead]]
        pred = None
        n = 0
        for snp, ea, oa, wt in self.w.get(key, []):
            if snp not in self.idx:
                continue
            a0, a1 = self.a0[snp], self.a1[snp]
            if {ea, oa} == {a0, a1}:
                sign = 1.0 if ea == a1 else -1.0
            elif {self.COMP.get(ea), self.COMP.get(oa)} == {a0, a1}:
                sign = 1.0 if self.COMP.get(ea) == a1 else -1.0
            else:
                continue
            g = self.Z[self.idx[snp]]
            if np.isnan(g).any():
                continue
            pred = sign * wt * g if pred is None else pred + sign * wt * g
            n += 1
        if pred is None or pred.std() == 0 or np.isnan(lead).any():
            return None, n
        return float(self.lead_sign * np.corrcoef(pred, lead)[0, 1]), n


def stage_collect(args, state: dict) -> None:
    import pandas as pd

    for lc in state["loci"]:  # carry static locus fields added after the prepare stage was run
        src = next(x for x in LOCI if x["locus_id"] == lc["locus_id"])
        for k, v in src.items():
            lc.setdefault(k, v)
    con_full = sqlite3.connect(state["weights"]["focus_db_path"])
    cons = {"brain": con_full, "all": con_full}
    if state["weights"].get("gtexv8_cortex_db_path"):
        cons["gtexv8_cortex"] = sqlite3.connect(state["weights"]["gtexv8_cortex_db_path"])
    taggers = {(lc["locus_id"], k): LeadTagging(lc["ld_prefix"], lc["lead_snp"], lc["lead_effect_allele"], c,
                                                lc["chr"], lc["block_start"], lc["block_stop"])
               for lc in state["loci"] for k, c in cons.items() if k != "all"}
    taggers.update({(lc["locus_id"], "all"): taggers[(lc["locus_id"], "brain")] for lc in state["loci"]})
    r_cache: dict = {}

    rows = []
    cfg_by = {c["config"]: c for c in CONFIGS}
    loci = {lc["locus_id"]: lc for lc in state["loci"]}
    for r in state["runs"]:
        lc = loci[r["locus_id"]]
        cfg = cfg_by[r["config"]]
        log = Path(r["log"])
        warns = _warnings(log)
        prior = _prior_from_log(log)
        r["warnings"] = warns
        r["prior_used"] = prior
        wbuild = ("GTEx v8 source is GRCh38 (SNP positions, gene TSS); matched to the GRCh37 GWAS/LD by rsID only"
                  if cfg["db"] == "gtexv8_cortex" else "GRCh37/hg19 (SNPs matched by rsID)")
        base = {"locus_id": r["locus_id"], "method": METHOD, "method_version": METHOD_VERSION,
                "analysis_config": r["config"], "weights_build": wbuild,
                "ld_reference": "1000G phase3 EUR (n=503), GRCh37; FOCUS ridge 0.1",
                "ld_block_grch37": f"{lc['chr']}:{lc['block_start']}-{lc['block_stop']}",
                "lead_snp": f"{lc['lead_snp']} (effect allele {lc['lead_effect_allele']}, Davies z {lc['lead_davies_z']})",
                "prior_prob_per_model": prior}
        tsv = Path(r["output"])
        if not tsv.exists() or tsv.stat().st_size == 0:
            rows.append(dict(base, weights_source="", tissue="", gene="", ens_gene_id="", model_inference="",
                             cv_r2="", cv_r2_pval="", twas_z="", gene_pip="", in_credible_set="",
                             null_model_pip="", n_models_in_region="", status="BLOCKED",
                             blocker="FOCUS produced no fine-mapping output for this block; log: "
                                     + " | ".join(warns[-3:]),
                             notes=cfg["description"]))
            continue
        df = pd.read_csv(tsv, sep="\t")
        null = df[df["ens_gene_id"] == "NULL.MODEL"]
        null_pip = float(null["pips_pop1"].iloc[0])
        genes = df[df["ens_gene_id"] != "NULL.MODEL"].copy()
        genes = genes.sort_values("pips_pop1", ascending=False)
        r["n_models"] = int(len(genes))
        r["null_pip"] = null_pip
        r["credible_set"] = [f"{g.mol_name}|{g.tissue}" for g in genes.itertuples() if int(g.in_cred_set_pop1) == 1]
        null_in_cs = int(null["in_cred_set_pop1"].iloc[0]) == 1
        for g in genes.itertuples():
            key = (r["locus_id"], cfg["db"], g.ens_gene_id, g.tissue, g.ref_name, g.inference_pop1)
            if key not in r_cache:
                r_cache[key] = taggers[(r["locus_id"], cfg["db"])].r(key[2:])
            r_lead, n_w = r_cache[key]
            inter_z = df.loc[g.Index, "inter_z_pop1"] if "inter_z_pop1" in df.columns else None
            rows.append(dict(base, r_pred_expr_vs_lead_effect_allele=("" if r_lead is None else round(r_lead, 4)),
                             n_weight_snps_in_ld_ref=n_w,
                             intercept_z=("" if inter_z is None or pd.isna(inter_z) else round(float(inter_z), 4)),
                             weights_source=weights_source(g.ref_name, g.inference_pop1),
                             tissue=f"{g.ref_name}:{g.tissue}", gene=g.mol_name, ens_gene_id=g.ens_gene_id,
                             model_inference=g.inference_pop1,
                             cv_r2=float(df.loc[g.Index, "cv.R2_pop1"]),
                             cv_r2_pval=float(df.loc[g.Index, "cv.R2.pval_pop1"]),
                             twas_z=round(float(g.twas_z_pop1), 4),
                             gene_pip=float(g.pips_pop1), in_credible_set=int(g.in_cred_set_pop1),
                             null_model_pip=null_pip, n_models_in_region=len(genes), status="RUN", blocker="",
                             notes=cfg["description"]))
        rows.append(dict(base, weights_source="(null model)", tissue="", gene="NULL.MODEL", ens_gene_id="NULL.MODEL",
                         model_inference="", cv_r2="", cv_r2_pval="", twas_z=0.0, gene_pip=null_pip,
                         in_credible_set=int(null_in_cs), null_model_pip=null_pip,
                         n_models_in_region=len(genes), status="RUN", blocker="",
                         notes="Posterior that no modelled gene-tissue expression explains the block signal "
                               "(non-mediated SNP effect OR mediation via an unmodelled gene/tissue/isoform/stage). "
                               + ("Warnings: " + " | ".join(warns) if warns else "")))

    for lc in state["loci"]:
        for m in BLOCKED_METHODS:
            rows.append({"locus_id": lc["locus_id"], "method": m["method"], "method_version": m["method_version"],
                         "analysis_config": "not_run", "weights_source": m["weights_source"],
                         "weights_build": m["weights_build"], "ld_reference": "", "ld_block_grch37": "",
                         "lead_snp": lc["lead_snp"], "prior_prob_per_model": "", "tissue": "", "gene": "",
                         "ens_gene_id": "", "model_inference": "", "cv_r2": "", "cv_r2_pval": "", "twas_z": "",
                         "gene_pip": "", "in_credible_set": "", "null_model_pip": "", "n_models_in_region": "",
                         "status": "BLOCKED", "blocker": m["blocker"], "notes": m["notes"]})

    cols = ["locus_id", "method", "method_version", "analysis_config", "weights_source", "weights_build", "tissue",
            "gene", "ens_gene_id", "gene_pip", "in_credible_set", "null_model_pip", "twas_z", "model_inference",
            "cv_r2", "cv_r2_pval", "n_models_in_region", "prior_prob_per_model", "intercept_z",
            "r_pred_expr_vs_lead_effect_allele", "n_weight_snps_in_ld_ref", "ld_block_grch37", "lead_snp",
            "ld_reference", "status", "blocker", "notes"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            for k in ("gene_pip", "null_model_pip"):
                if isinstance(row.get(k), float):
                    row[k] = f"{row[k]:.6g}"
            w.writerow(row)
    for c in set(cons.values()):
        c.close()
    state["outputs"] = {"csv": str(OUT_CSV.relative_to(REPO_ROOT)), "csv_rows": len(rows),
                        "csv_sha256": sha256_file(OUT_CSV)}


BLOCKED_METHODS = [
    {
        "method": "TGFM", "method_version": "BennyStrobes/TGFM v1.0 (Zenodo 10.5281/zenodo.13823621)",
        "weights_source": "none distributed (gene-tissue SuSiE eQTL models must be fit by the user)",
        "weights_build": "n/a (would be GTEx v8 GRCh38 in the published analysis)",
        "blocker": "TGFM ships no pre-fit gene-tissue models (Zenodo record contains only a 128 kB code zip). "
                   "Step 1 (susie_eqtl_fine_mapping_for_tgfm.py) needs either individual-level eQTL genotypes + "
                   "expression, or full eQTL summary statistics PLUS in-sample eQTL genotypes; for GTEx brain "
                   "tissues both require dbGaP phs000424 controlled access (registration/approval not allowed "
                   "here). Step 2 requires GWAS in-sample LD (the published analysis used UK Biobank genotypes; "
                   "Davies 2018 has no in-sample LD, only 1000G EUR n=503), and Step 4 learns tissue priors "
                   "genome-wide across all loci.",
        "notes": "Not substituted with any weaker method.",
    },
    {
        "method": "cTWAS", "method_version": "xinhe-lab/ctwas (not installed)",
        "weights_source": "would be PredictDB GTEx v7 brain elastic-net (GRCh37 rsIDs) or GTEx v8 mashr (GRCh38)",
        "weights_build": "n/a",
        "blocker": "Scope/time blocker, not an access blocker: cTWAS separates mediated from non-mediated "
                   "(SNP) effects only after genome-wide estimation of gene and SNP prior inclusion "
                   "probabilities and effect variances over all ~1,700 LD blocks, which needs genome-wide "
                   "region/SNP maps and LD for every block plus multi-tissue weights; this did not fit the "
                   "~90 min / 3-thread budget alongside the running MAGMA job. A locus-only run with fixed "
                   "priors would not be cTWAS as published.",
        "notes": "Recommended next method: it is the one maintained tool that explicitly models non-mediated "
                 "SNP effects rather than folding them into a NULL model.",
    },
]


def env_versions() -> dict:
    out = {"python": platform.python_version(), "platform": platform.platform()}
    for mod in ("numpy", "pandas", "scipy", "sqlalchemy", "pandas_plink", "pyfocus", "dask"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception as e:  # pragma: no cover
            out[mod] = f"unavailable: {e}"
    try:
        out["plink"] = subprocess.run([shutil.which("plink") or "plink", "--version"], capture_output=True,
                                      text=True).stdout.strip()
    except Exception as e:  # pragma: no cover
        out["plink"] = f"unavailable: {e}"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--focus-db", required=True)
    ap.add_argument("--gencode-lift37-gtf", required=True,
                    help="gencode.v38lift37.annotation.gtf.gz from ftp.ebi.ac.uk GENCODE release_38/GRCh37_mapping")
    ap.add_argument("--stage", choices=["prepare", "import_v8", "run", "collect", "all"], default="all")
    ap.add_argument("--gtexv8-cortex-archive", default=None,
                    help="GTExv8.EUR.Brain_Cortex.tar.gz from https://s3.us-west-1.amazonaws.com/gtex.v8.fusion/EUR/")
    ap.add_argument("--extra-provenance", default=None, help="JSON with download records to merge")
    args = ap.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    state_path = work / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() and args.stage != "prepare" and \
        args.stage != "all" else {"started_utc": utc_now(), "inputs": {}, "weights": {}, "commands": []}
    t0 = time.time()
    if args.stage in ("prepare", "all"):
        stage_prepare(args, state)
        state_path.write_text(json.dumps(state, indent=2))
    if args.stage == "import_v8" or (args.stage == "all" and args.gtexv8_cortex_archive):
        stage_import_v8(args, state)
        state_path.write_text(json.dumps(state, indent=2))
    if args.stage in ("run", "all"):
        stage_run(args, state)
        state_path.write_text(json.dumps(state, indent=2))
    if args.stage in ("collect", "all"):
        stage_collect(args, state)
        state["finished_utc"] = utc_now()
        state["environment"] = env_versions()
        state["thread_env"] = THREAD_ENV
        state["configs"] = CONFIGS
        state["blocked_methods"] = BLOCKED_METHODS
        state["focus_source"] = {"repo": FOCUS_REPO, "commit": FOCUS_COMMIT,
                                 "db_url": FOCUS_DB_URL, "db_linked_from": FOCUS_DB_LINKED_FROM}
        if args.extra_provenance:
            state["extra"] = json.loads(Path(args.extra_provenance).read_text())
        state_path.write_text(json.dumps(state, indent=2))
    state.setdefault("stage_seconds", {})[args.stage] = round(time.time() - t0, 1)
    state_path.write_text(json.dumps(state, indent=2))
    if args.stage in ("collect", "all"):
        OUT_PROV.parent.mkdir(parents=True, exist_ok=True)
        OUT_PROV.write_text(json.dumps(state, indent=2) + "\n")


if __name__ == "__main__":
    main()
