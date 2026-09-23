#!/usr/bin/env python3
"""Sprint 4 — fetch ADULT HUMAN BRAIN molecular-QTL full summary statistics from the eQTL Catalogue.

Purpose: raw material for colocalisation at a handful of GWAS loci. This script only FETCHES data;
it performs no colocalisation and reads no GWAS results other than the lead-SNP ids/positions in
the loci CSV.

Source facts (verified 2026-09-23, recorded again in PROVENANCE.json on every run)
---------------------------------------------------------------------------------
* The eQTL Catalogue REST API (``https://www.ebi.ac.uk/eqtl/api/v2/...``) is DEPRECATED and returns
  HTTP 410 ("This API is no longer available"). Supported access is FTP/HTTPS files + tabix
  (https://www.ebi.ac.uk/eqtl/Data_access/). There is therefore no REST fallback; a failed tabix
  query is recorded as a failure, never skipped.
* Release used: **r7** (June 2024; files dated 2023-04-06 / 2024-05-20), the latest release whose
  bulk sumstats are tabix-indexed TSVs. The r8 pre-release (``/r8_beta/``, adds GTEx v10) ships
  parquet only and is NOT used here.
* Dataset enumeration: ``tabix/tabix_ftp_paths.tsv`` (per-dataset metadata + sumstats / SuSiE
  credible-set / SuSiE lbf URLs) and ``data_tables/dataset_metadata_r7.tsv`` (pmid, study_type) from
  github.com/eQTL-Catalogue/eQTL-Catalogue-resources, pinned to commit ``RESOURCES_COMMIT``.
* Sumstats URL pattern (gene-level ``ge`` / ``microarray``):
  ``https://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/<study_id>/<dataset_id>/<dataset_id>.all.tsv.gz``
  (+ ``.tbi``). Coordinates are GRCh38. Columns (tabix/Columns.md): molecular_trait_id chromosome
  position ref alt variant ma_samples maf pvalue beta se type ac an r2 molecular_trait_object_id
  gene_id median_tpm rsid.
* **Effect allele: ALT.** "The ALT allele is always the effect allele" (Data_access FAQ); Columns.md:
  "alt - GRCh38 alternative allele (also the effect allele)". ``ac`` = ALT allele count, ``an`` =
  allele number (autosomes: an/2 = sample size). ``maf`` is the MINOR allele frequency, which is not
  necessarily ALT (ALT frequency = ac/an).
* One rsid per row: a variant mapping to several dbSNP-151 rsids appears on several rows; rows are
  kept verbatim here, so de-duplicate on (molecular_trait_id, variant) before colocalisation.
* EBI warns that frequent tabix requests can be treated as a DoS and get the IP blacklisted; every
  tabix launch is therefore spaced by ``--min-interval`` seconds (default 2) with <= ``--workers``
  (default 3) in flight. Remote ``.tbi`` indexes are downloaded once and passed via ``URL##idx##path``.
* SuSiE outputs (``--lbf``): ``susie/<study>/<dataset>/<dataset>.lbf_variable.txt.gz`` and
  ``.credible_sets.tsv.gz`` are public, but they are plain gzip (not BGZF), have NO ``.tbi``, and
  lbf rows are ordered by fine-mapped gene with chromosomes interleaved, so no region query is
  possible. ``--lbf`` therefore streams each whole lbf file once (30 MB - 3.5 GB compressed per brain
  dataset; ~1.5 MB/s per connection observed from EBI) and keeps rows for the listed genes inside
  the window. Credible-set files (<~50 MB) are downloaded whole and filtered to the listed genes.

Adult classification is curated per study (``STUDY_AGE_EVIDENCE``) from the study papers and the
eQTL Catalogue QC reports; any nervous-system study not in the registry is UNCERTAIN, never ADULT.

Outputs
-------
* ``data/sprint4/eqtl_catalogue_brain_datasets.csv`` — every nervous-system dataset (all quant methods)
* ``data/interim/sprint4/eqtl/<locus_id>__<dataset_id>.parquet`` — full cis sumstats in window
* ``data/interim/sprint4/eqtl_lbf/<locus_id>__<dataset_id>.parquet`` (+ ``.credible_sets.parquet``)
* ``data/raw/sprint4/eqtl_catalogue/PROVENANCE.json`` (+ ``metadata/`` snapshots of the source tables)

Usage
-----
    .venv/bin/python pipelines/sprint4/fetch_eqtl_catalogue.py                      # default loci
    .venv/bin/python pipelines/sprint4/fetch_eqtl_catalogue.py --loci other.csv --lbf
    .venv/bin/python pipelines/sprint4/fetch_eqtl_catalogue.py --table-only          # no sumstats
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

# ----------------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------------
RELEASE = "r7"
FTP_HTTPS = "https://ftp.ebi.ac.uk/pub/databases/spot/eQTL"
REST_API_V2 = "https://www.ebi.ac.uk/eqtl/api/v2/datasets"  # probed only, to record that it is gone
DATA_ACCESS_DOC = "https://www.ebi.ac.uk/eqtl/Data_access/"
RESOURCES_REPO = "eQTL-Catalogue/eQTL-Catalogue-resources"
RESOURCES_COMMIT = "19cc5da6f86d30ba18cbb495bbfb0606172553dd"  # master HEAD on 2026-09-23
RESOURCES_RAW = f"https://raw.githubusercontent.com/{RESOURCES_REPO}/{RESOURCES_COMMIT}"
METADATA_FILES = {
    "tabix_ftp_paths.tsv": f"{RESOURCES_RAW}/tabix/tabix_ftp_paths.tsv",
    "dataset_metadata_r7.tsv": f"{RESOURCES_RAW}/data_tables/dataset_metadata_r7.tsv",
    "Columns.md": f"{RESOURCES_RAW}/tabix/Columns.md",
}
ENSEMBL_REST = "https://rest.ensembl.org"
ENSEMBL_REST_GRCH37 = "https://grch37.rest.ensembl.org"
USER_AGENT = "HUMAN-INTELLIGENCE-sprint4-eqtl-fetch/1.0 (research; python-urllib)"

SUMSTATS_COLUMNS = [
    "molecular_trait_id", "chromosome", "position", "ref", "alt", "variant", "ma_samples", "maf",
    "pvalue", "beta", "se", "type", "ac", "an", "r2", "molecular_trait_object_id", "gene_id",
    "median_tpm", "rsid",
]
OUTPUT_COLUMNS = [
    "locus_id", "dataset_id", "molecular_trait_id", "gene_id", "variant", "rsid", "chromosome",
    "position", "ref", "alt", "beta", "se", "pvalue", "maf", "an", "ac", "r2", "type", "ma_samples",
    "median_tpm",
]
LBF_ID_COLUMNS = ["molecular_trait_id", "region", "variant", "chromosome", "position"]
GENE_LEVEL_QUANT = frozenset({"ge", "microarray"})

TABLE_COLUMNS = [
    "dataset_id", "study_id", "study_label", "tissue_id", "tissue_label", "condition_label",
    "sample_group", "quant_method", "sample_size", "adult_status", "adult_status_basis",
    "gene_level_quant", "tissue_class", "fetch_eligible", "fetch_exclusion_reason", "release",
    "study_type", "pmid", "sumstats_url", "credible_sets_url", "lbf_url",
]

# ----------------------------------------------------------------------------------------------
# Nervous-system tissue classes (tissue ids as used by the eQTL Catalogue)
# ----------------------------------------------------------------------------------------------
BRAIN_TISSUE_IDS = frozenset({
    "UBERON_0001870",  # brain (cortex)
    "UBERON_0001873",  # caudate
    "UBERON_0001874",  # putamen
    "UBERON_0001876",  # amygdala
    "UBERON_0001882",  # nucleus accumbens
    "UBERON_0001898",  # hypothalamus
    "UBERON_0001950",  # neocortex
    "UBERON_0001954",  # hippocampus
    "UBERON_0002037",  # cerebellum
    "UBERON_0002038",  # substantia nigra
    "UBERON_0009834",  # DLPFC
    "UBERON_0009835",  # anterior cingulate cortex
})
SPINAL_CORD_TISSUE_IDS = frozenset({"UBERON_0006469"})
PERIPHERAL_NERVE_TISSUE_IDS = frozenset({"UBERON_0001323"})  # tibial nerve
NEURAL_CELL_TISSUE_IDS = frozenset({
    "CL_0000540",      # neuron
    "CL_0000101",      # sensory neuron
    "CL_0000700",      # dopaminergic neuron
    "CL_0000850",      # serotonergic neuron
    "CL_0000127",      # astrocyte
    "CL_0000129",      # microglia
    "CL_0000065",      # ependymal cell
    "CL_0011020",      # neural progenitor
    "UBERON_0003079",  # floor plate progenitor
    "BTO_0000930",     # neuroblast
})
# NB: bare "cortex" is deliberately absent — it matches "kidney (cortex)" / adrenal cortex.
NEURAL_LABEL_TERMS = ("brain", "neur", "glia", "astrocyte", "spinal", "nerve", "neocortex",
                      "cerebell", "hippocamp", "ependym", "floor plate")


def tissue_class(tissue_id: str, tissue_label: str) -> str | None:
    """Nervous-system class of an eQTL Catalogue tissue, or None when not nervous system.

    Pituitary (UBERON_0000007) is deliberately NOT nervous system: the GTEx sample is dominated by
    the glandular anterior lobe.
    """
    tid = str(tissue_id).strip()
    label = str(tissue_label).strip().lower()
    if tid in SPINAL_CORD_TISSUE_IDS:
        return "SPINAL_CORD"
    if tid in PERIPHERAL_NERVE_TISSUE_IDS:
        return "PERIPHERAL_NERVE"
    if tid in BRAIN_TISSUE_IDS:
        return "BRAIN"
    if tid in NEURAL_CELL_TISSUE_IDS:
        return "NEURAL_CELL_TYPE"
    if tid == "UBERON_0000007":
        return None
    if label.startswith("brain"):
        return "BRAIN"
    if any(term in label for term in NEURAL_LABEL_TERMS):
        return "NEURAL_OTHER_UNREVIEWED"
    return None


# ----------------------------------------------------------------------------------------------
# Adult classification — curated per study from primary sources (checked 2026-09-23)
# ----------------------------------------------------------------------------------------------
ADULT, NON_ADULT, UNCERTAIN = "ADULT", "NON_ADULT", "UNCERTAIN"

STUDY_AGE_EVIDENCE: dict[str, tuple[str, str]] = {
    "GTEx": (ADULT,
             "GTEx v8 postmortem donors, all in age brackets 20-29..70-79 (GTEx Portal API "
             "datasetId=gtex_v8 subject table: 979 donors, 0 outside 20-79); GTEx Consortium 2020 "
             "Science PMID 32913098."),
    "GTEx_v10": (ADULT,
                 "GTEx v10 postmortem donors, all in age brackets 20-79 (GTEx Portal API "
                 "datasetId=gtex_v10: 980 donors); r8 pre-release parquet only."),
    "ROSMAP": (ADULT,
               "ROS/MAP: older adults, non-demented at enrolment, autopsy DLPFC (Ng 2017 Nat Neurosci "
               "PMID 28869584; mean enrolment ages 75.6 / 80.0 y per Fromer 2016 PMID 27668389). NOTE: "
               "ageing / Alzheimer's-pathology cohort — elderly and pathology-enriched brains."),
    "CommonMind": (ADULT,
                   "CommonMind MSSM/Penn/Pitt DLPFC: eQTL Catalogue N=590 matches this cohort (Hoffman "
                   "2019 Sci Data PMID 31551426 Table 1: ~601 samples, bank mean ages 45-79 y), not "
                   "NIMH-HBCC (+~385, younger); youngest SCZ/control age at death 20 y (Fromer 2016 "
                   "PMID 27668389). NOTE: SCZ/BP cases included; HBCC exclusion inferred from N."),
    "Braineac2": (ADULT,
                  "UKBEC neurologically healthy donors, putamen + substantia nigra (Guelfi 2020 Nat "
                  "Commun PMID 32098967, Supplementary Data 1: 117 donors aged 16-85 y). NOTE: 2/117 "
                  "donors are late adolescents (16 and 17 y); no prenatal or childhood donors."),
    "Young_2019": (ADULT,
                   "Primary CD11b+ microglia isolated ex vivo (uncultured) from ADULT neurosurgical "
                   "resection tissue (Young 2021 Nat Genet PMID 34083789, Methods: 'Adult brain tissue "
                   "biopsies'). NOTE: purified cell type; living patients with tumour/trauma/"
                   "haemorrhage/hydrocephalus/epilepsy pathology."),
    "BrainSeq": (NON_ADULT,
                 "Childhood- and prenatal-inclusive. eQTL Catalogue BrainSeq QC report: 495 samples "
                 "before QC, 479 after (no age filter) = the full BrainSeq Phase 1 polyA DLPFC set, "
                 "which spans second-trimester fetal to 85 y (Jaffe 2018 Nat Neurosci PMID 30050107); "
                 "only 412 of those 495 donors were aged >13 y, so >=67 of the 479 retained samples "
                 "are aged <=13 y (fetal/infant/child)."),
    "Walker_2019": (NON_ADULT,
                    "Fetal: 201 mid-gestational human neocortex samples (Walker 2019 Cell PMID 31626773)."),
    "Aygun_2021": (NON_ADULT,
                   "Fetal-derived in vitro: cultured primary human neural progenitors and their "
                   "differentiated neuronal progeny (Aygun 2021 AJHG PMID 34416157)."),
    "Schwartzentruber_2018": (NON_ADULT,
                              "iPSC-derived sensory neurons (Schwartzentruber 2018 Nat Genet "
                              "PMID 29229984)."),
    "Jerber_2021": (NON_ADULT,
                    "iPSC-derived midbrain/dopaminergic differentiation, scRNA-seq pseudobulk at "
                    "days 11-52 in vitro (Jerber 2021 Nat Genet PMID 33664506)."),
}
NON_ADULT_TERMS = ("fetal", "foetal", "prenatal", "embryo", "ipsc", "ips-derived", "organoid",
                   "progenitor", "neuroblast", "differentiat")


def classify_adult(study_label: str, sample_group: str = "", tissue_label: str = "",
                   condition_label: str = "") -> tuple[str, str]:
    """(adult_status, basis). Curated registry first; an unreviewed study is never called ADULT.

    Keyword guard: a dataset whose own labels say fetal / iPSC / progenitor / differentiation is
    NON_ADULT even if its study is missing from the registry.
    """
    study = str(study_label).strip()
    if study in STUDY_AGE_EVIDENCE:
        return STUDY_AGE_EVIDENCE[study]
    text = " ".join(str(x) for x in (sample_group, tissue_label, condition_label)).lower()
    hits = [t for t in NON_ADULT_TERMS if t in text]
    if hits:
        return NON_ADULT, (f"Study not in curated registry; dataset labels contain {hits} "
                           "(fetal / iPSC / in-vitro differentiated). Verify from the paper.")
    return UNCERTAIN, ("Study not in curated age registry (STUDY_AGE_EVIDENCE); donor ages not "
                       "verified. Check the study paper before treating as adult.")


def is_gene_level(quant_method: str) -> bool:
    return str(quant_method).strip().lower() in GENE_LEVEL_QUANT


def ftp_to_https(url: str) -> str:
    url = str(url).strip()
    if url.startswith("ftp://"):
        return "https://" + url[len("ftp://"):]
    return url


def build_dataset_table(paths: pd.DataFrame, meta: pd.DataFrame | None = None,
                        release: str = RELEASE) -> pd.DataFrame:
    """Nervous-system subset of the eQTL Catalogue dataset list with adult/gene-level flags."""
    df = paths.copy()
    for col in ("study_id", "dataset_id", "study_label", "sample_group", "tissue_id", "tissue_label",
                "condition_label", "quant_method"):
        df[col] = df[col].astype(str).str.strip()
    if meta is not None and len(meta):
        extra = meta[["dataset_id"] + [c for c in ("pmid", "study_type") if c in meta.columns]]
        df = df.merge(extra.drop_duplicates("dataset_id"), on="dataset_id", how="left")
    for col in ("pmid", "study_type"):
        if col not in df.columns:
            df[col] = pd.NA
    df["tissue_class"] = [tissue_class(t, lab) for t, lab in zip(df["tissue_id"], df["tissue_label"])]
    df = df[df["tissue_class"].notna()].copy()
    cls = [classify_adult(r.study_label, r.sample_group, r.tissue_label, r.condition_label)
           for r in df.itertuples(index=False)]
    df["adult_status"] = [c[0] for c in cls]
    df["adult_status_basis"] = [c[1] for c in cls]
    df["gene_level_quant"] = df["quant_method"].map(is_gene_level)
    reasons = []
    for r in df.itertuples(index=False):
        why = []
        if r.adult_status != ADULT:
            why.append(f"adult_status={r.adult_status}")
        if not r.gene_level_quant:
            why.append(f"quant_method={r.quant_method} (not gene-level)")
        if r.tissue_class == "PERIPHERAL_NERVE":
            why.append("peripheral nerve, not brain")
        if r.tissue_class == "NEURAL_OTHER_UNREVIEWED":
            why.append("unreviewed nervous-system tissue label")
        reasons.append("; ".join(why))
    df["fetch_exclusion_reason"] = reasons
    df["fetch_eligible"] = df["fetch_exclusion_reason"].eq("")
    df["release"] = release
    df["sumstats_url"] = df["ftp_path"].map(ftp_to_https) if "ftp_path" in df else pd.NA
    df["credible_sets_url"] = df["ftp_cs_path"].map(ftp_to_https) if "ftp_cs_path" in df else pd.NA
    df["lbf_url"] = df["ftp_lbf_path"].map(ftp_to_https) if "ftp_lbf_path" in df else pd.NA
    df["sample_size"] = pd.to_numeric(df["sample_size"], errors="coerce").astype("Int64")
    return df[TABLE_COLUMNS].sort_values(["study_label", "sample_group", "quant_method"]).reset_index(
        drop=True)


# ----------------------------------------------------------------------------------------------
# Loci
# ----------------------------------------------------------------------------------------------
@dataclass
class Locus:
    locus_id: str
    chrom: str
    lead_snp: str
    lead_pos_grch37: int
    genes: dict[str, str]  # ensembl_gene_id -> symbol
    lead_pos_grch38: int | None = None
    window_start: int | None = None
    window_end: int | None = None
    lookup: dict = field(default_factory=dict)

    @property
    def region(self) -> str:
        return f"{self.chrom}:{self.window_start}-{self.window_end}"


def load_loci(path: Path) -> list[Locus]:
    df = pd.read_csv(path, dtype=str)
    need = {"locus_id", "chr", "lead_snp", "lead_pos_grch37", "ensembl_gene_id"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"loci CSV {path} lacks columns {sorted(missing)}")
    gene_col = "gene" if "gene" in df.columns else "ensembl_gene_id"
    loci = []
    for lid, g in df.groupby("locus_id", sort=False):
        first = g.iloc[0]
        for col in ("chr", "lead_snp", "lead_pos_grch37"):
            if g[col].nunique() != 1:
                raise ValueError(f"locus {lid}: inconsistent {col} across rows")
        genes = {e.strip(): s for e, s in zip(g["ensembl_gene_id"], g[gene_col]) if str(e).strip()}
        loc = Locus(str(lid), str(first["chr"]).removeprefix("chr"), str(first["lead_snp"]).strip(),
                    int(first["lead_pos_grch37"]), genes)
        if "lead_pos_grch38" in g.columns and pd.notna(first["lead_pos_grch38"]):
            loc.lead_pos_grch38 = int(first["lead_pos_grch38"])
            loc.lookup = {"source": "input CSV column lead_pos_grch38"}
        loci.append(loc)
    return loci


def set_window(loc: Locus, window_kb: int) -> None:
    half = int(window_kb) * 1000
    loc.window_start = max(1, loc.lead_pos_grch38 - half)
    loc.window_end = loc.lead_pos_grch38 + half


# ----------------------------------------------------------------------------------------------
# HTTP helpers
# ----------------------------------------------------------------------------------------------
def http_get(url: str, *, headers: dict | None = None, timeout: int = 120, retries: int = 3,
             method: str = "GET") -> tuple[bytes, dict, int]:
    hdrs = {"User-Agent": USER_AGENT}
    hdrs.update(headers or {})
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), dict(resp.headers), resp.status
        except urllib.error.HTTPError as exc:  # 4xx is final (except 429)
            if exc.code != 429 and exc.code < 500:
                raise
            last = exc
        except Exception as exc:  # noqa: BLE001 — network errors are retried then re-raised
            last = exc
        time.sleep(5 * attempt)
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last}")


def http_head(url: str) -> dict:
    _, headers, _ = http_get(url, method="HEAD", timeout=60)
    return {"content_length": int(headers.get("Content-Length", -1)),
            "last_modified": headers.get("Last-Modified")}


def probe_rest_api() -> dict:
    try:
        body, _, status = http_get(REST_API_V2 + "?size=1", retries=1, timeout=30)
        return {"url": REST_API_V2, "status": status, "body_prefix": body[:200].decode("utf-8", "replace")}
    except urllib.error.HTTPError as exc:
        return {"url": REST_API_V2, "status": exc.code,
                "body_prefix": exc.read()[:200].decode("utf-8", "replace")}
    except Exception as exc:  # noqa: BLE001
        return {"url": REST_API_V2, "status": None, "error": repr(exc)}


class RateLimiter:
    """At most one request START per ``interval`` seconds across all threads."""

    def __init__(self, interval: float):
        self.interval = float(interval)
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._next:
                time.sleep(self._next - now)
                now = time.monotonic()
            self._next = now + self.interval


# ----------------------------------------------------------------------------------------------
# Ensembl lead-SNP lookup
# ----------------------------------------------------------------------------------------------
def ensembl_variation(rsid: str, server: str) -> dict:
    body, _, _ = http_get(f"{server}/variation/human/{rsid}?content-type=application/json",
                          headers={"Content-Type": "application/json"}, timeout=60)
    return json.loads(body)


def chromosome_mapping(record: dict, assembly: str, chrom: str) -> dict | None:
    hits = [m for m in record.get("mappings", [])
            if m.get("assembly_name") == assembly and m.get("coord_system", "chromosome") == "chromosome"
            and str(m.get("seq_region_name")) == str(chrom)]
    return hits[0] if len(hits) == 1 else None


def resolve_lead_grch38(loc: Locus) -> None:
    rec38 = ensembl_variation(loc.lead_snp, ENSEMBL_REST)
    m38 = chromosome_mapping(rec38, "GRCh38", loc.chrom)
    if m38 is None:
        raise RuntimeError(f"{loc.lead_snp}: no unique GRCh38 chr{loc.chrom} mapping in Ensembl")
    rec37 = ensembl_variation(loc.lead_snp, ENSEMBL_REST_GRCH37)
    m37 = chromosome_mapping(rec37, "GRCh37", loc.chrom)
    grch37_ok = m37 is not None and int(m37["start"]) == loc.lead_pos_grch37
    loc.lead_pos_grch38 = int(m38["start"])
    loc.lookup = {
        "source": f"{ENSEMBL_REST}/variation/human/{loc.lead_snp}",
        "ensembl_name": rec38.get("name"),
        "synonyms": rec38.get("synonyms", []),
        "grch38": {"chr": m38["seq_region_name"], "start": m38["start"], "end": m38["end"],
                   "allele_string": m38.get("allele_string")},
        "grch37_check_source": f"{ENSEMBL_REST_GRCH37}/variation/human/{loc.lead_snp}",
        "grch37_ensembl_start": None if m37 is None else int(m37["start"]),
        "grch37_input": loc.lead_pos_grch37,
        "grch37_matches_input": grch37_ok,
    }
    if not grch37_ok:
        raise RuntimeError(f"{loc.lead_snp}: Ensembl GRCh37 position {loc.lookup['grch37_ensembl_start']} "
                           f"!= input lead_pos_grch37 {loc.lead_pos_grch37}")


def ensembl_release() -> str | None:
    try:
        body, _, _ = http_get(f"{ENSEMBL_REST}/info/data?content-type=application/json", timeout=30)
        return ",".join(str(r) for r in json.loads(body).get("releases", []))
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------------------------------------
# Sumstats parsing (pure; unit-tested offline)
# ----------------------------------------------------------------------------------------------
def parse_header_line(first_line: str) -> list[str]:
    cols = first_line.rstrip("\r\n").split("\t")  # the r7 header line ends in CRLF
    if cols != SUMSTATS_COLUMNS:
        raise ValueError(f"unexpected sumstats header {cols}; expected {SUMSTATS_COLUMNS}")
    return cols


def parse_sumstats_text(text: str, header: list[str], gene_ids, locus_id: str, dataset_id: str,
                        chrom: str | None = None, start: int | None = None,
                        end: int | None = None) -> pd.DataFrame:
    """Parse tabix output (no header) and keep the listed genes (and window, when given)."""
    lines = [ln.rstrip("\r") for ln in text.splitlines() if ln and not ln.startswith("molecular_trait_id\t")]
    bad = [ln for ln in lines if ln.count("\t") != len(header) - 1]
    if bad:
        raise ValueError(f"{len(bad)} malformed rows (expected {len(header)} fields), e.g. {bad[0][:200]!r}")
    df = pd.read_csv(io.StringIO("\n".join(lines)), sep="\t", header=None, names=header,
                     dtype={"chromosome": str, "molecular_trait_id": str, "gene_id": str, "rsid": str,
                            "r2": str, "variant": str, "ref": str, "alt": str, "type": str,
                            "molecular_trait_object_id": str},
                     na_values=["NA"], keep_default_na=False) if lines else pd.DataFrame(columns=header)
    df = df[df["gene_id"].isin(set(gene_ids))].copy()
    if chrom is not None:
        df = df[df["chromosome"].astype(str) == str(chrom)]
    if start is not None:
        df = df[pd.to_numeric(df["position"]) >= int(start)]
    if end is not None:
        df = df[pd.to_numeric(df["position"]) <= int(end)]
    df["locus_id"] = locus_id
    df["dataset_id"] = dataset_id
    df["r2"] = pd.to_numeric(df["r2"], errors="coerce")
    for col, typ in (("position", "int64"), ("an", "Int64"), ("ac", "Int64"), ("ma_samples", "Int64")):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(typ)
    for col in ("beta", "se", "pvalue", "maf", "median_tpm"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    for col in ("chromosome", "molecular_trait_id", "gene_id", "variant", "rsid", "ref", "alt", "type"):
        df[col] = df[col].astype("string")
    return df[OUTPUT_COLUMNS].sort_values(["gene_id", "position", "variant", "rsid"]).reset_index(drop=True)


# ----------------------------------------------------------------------------------------------
# LBF streaming filter (pure core unit-tested offline)
# ----------------------------------------------------------------------------------------------
class LineFilter:
    """Incrementally keep lines whose first tab-field is in ``keys`` from a byte stream."""

    def __init__(self, keys):
        self.keys = {k.encode() if isinstance(k, str) else k for k in keys}
        self.header: bytes | None = None
        self.kept: list[bytes] = []
        self._carry = b""
        self.n_lines = 0

    def feed(self, chunk: bytes) -> None:
        buf = self._carry + chunk
        cut = buf.rfind(b"\n")
        if cut < 0:
            self._carry = buf
            return
        body, self._carry = buf[:cut + 1], buf[cut + 1:]
        if self.header is None:
            nl = body.find(b"\n")
            self.header, body = body[:nl], body[nl + 1:]
        self.n_lines += body.count(b"\n")
        if not any(k in body for k in self.keys):
            return
        for line in body.split(b"\n"):
            if line and line.split(b"\t", 1)[0] in self.keys:
                self.kept.append(line)

    def close(self) -> None:
        if self._carry:
            self.feed(b"\n")


def lbf_frame(header: bytes, lines: list[bytes]) -> pd.DataFrame:
    cols = header.decode().rstrip("\r").split("\t")
    if cols[:5] != LBF_ID_COLUMNS or not all(c.startswith("lbf_variable") for c in cols[5:]):
        raise ValueError(f"unexpected lbf header {cols}")
    text = b"\n".join(lines).decode()
    if not text:
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(io.StringIO(text), sep="\t", header=None, names=cols,
                     dtype={"chromosome": str, "molecular_trait_id": str, "region": str, "variant": str})
    return df


def stream_gzip_lines(url: str, keys, progress_every: int = 256 << 20) -> tuple[LineFilter, dict]:
    """Stream a (multi-member) gzip over HTTPS, filtering lines; returns filter + transfer stats."""
    flt = LineFilter(keys)
    sha = hashlib.sha256()
    n_bytes = 0
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        expected = int(resp.headers.get("Content-Length", -1))
        dec = zlib.decompressobj(wbits=zlib.MAX_WBITS | 16)
        next_report = progress_every
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            sha.update(chunk)
            n_bytes += len(chunk)
            data = chunk
            while data:
                flt.feed(dec.decompress(data))
                data = dec.unused_data
                if data:  # next gzip member
                    dec = zlib.decompressobj(wbits=zlib.MAX_WBITS | 16)
            if n_bytes >= next_report:
                rate = n_bytes / max(time.time() - t0, 1e-6) / 1e6
                print(f"    .. {url.rsplit('/', 1)[-1]}: {n_bytes / 1e6:,.0f}/{expected / 1e6:,.0f} MB "
                      f"({rate:.1f} MB/s)", flush=True)
                next_report += progress_every
        flt.feed(dec.flush())
        flt.close()
    if expected >= 0 and n_bytes != expected:
        raise RuntimeError(f"truncated download of {url}: {n_bytes} of {expected} bytes")
    return flt, {"bytes": n_bytes, "sha256_compressed_file": sha.hexdigest(),
                 "seconds": round(time.time() - t0, 1), "lines_scanned": flt.n_lines}


# ----------------------------------------------------------------------------------------------
# Fetch workers
# ----------------------------------------------------------------------------------------------
def write_parquet(df: pd.DataFrame, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)
    return {"path": str(path.relative_to(C.REPO_ROOT)), "n_rows": int(len(df)),
            "sha256": C.sha256_file(path)}


def read_gz_first_line(url: str) -> str:
    body, _, _ = http_get(url, headers={"Range": "bytes=0-65535"}, timeout=60)
    dec = zlib.decompressobj(wbits=zlib.MAX_WBITS | 16)
    text = dec.decompress(body).decode("utf-8", "replace")
    return text.split("\n", 1)[0]


def fetch_sumstats_dataset(ds: pd.Series, loci: list[Locus], out_dir: Path, idx_dir: Path,
                           limiter: RateLimiter, force: bool) -> list[dict]:
    """All loci for one dataset (sequential, so the index is downloaded once)."""
    records: list[dict] = []
    url = ds["sumstats_url"]
    base = {"kind": "sumstats", "dataset_id": ds["dataset_id"], "study_label": ds["study_label"],
            "sample_group": ds["sample_group"], "quant_method": ds["quant_method"], "source_url": url}
    todo = [loc for loc in loci if force or not (out_dir / f"{loc.locus_id}__{ds['dataset_id']}.parquet").exists()]
    for loc in loci:
        if loc not in todo:
            path = out_dir / f"{loc.locus_id}__{ds['dataset_id']}.parquet"
            df = pd.read_parquet(path)
            records.append({**base, "locus_id": loc.locus_id, "region_grch38": loc.region,
                            "status": "CACHED_EXISTING", "path": str(path.relative_to(C.REPO_ROOT)),
                            "n_rows": int(len(df)), "sha256": C.sha256_file(path),
                            "n_rows_per_gene": {k: int(v) for k, v in df["gene_id"].value_counts().items()},
                            "genes_without_rows": sorted(set(loc.genes) - set(df["gene_id"]))})
    if not todo:
        return records
    try:
        limiter.wait()
        head = http_head(url)
        limiter.wait()
        idx_path = idx_dir / f"{ds['dataset_id']}.all.tsv.gz.tbi"
        if not idx_path.exists():
            body, _, _ = http_get(url + ".tbi", timeout=300)
            idx_path.parent.mkdir(parents=True, exist_ok=True)
            idx_path.write_bytes(body)
        idx_sha = C.sha256_file(idx_path)
        limiter.wait()
        header = parse_header_line(read_gz_first_line(url))
    except Exception as exc:  # noqa: BLE001 — recorded, never silently skipped
        for loc in todo:
            records.append({**base, "locus_id": loc.locus_id, "status": "FAILED",
                            "error": f"dataset setup: {exc!r}", "fetched_at": C.utc_now()})
        return records
    for loc in todo:
        rec = {**base, "locus_id": loc.locus_id, "region_grch38": loc.region,
               "remote_content_length": head["content_length"], "remote_last_modified": head["last_modified"],
               "tbi_sha256": idx_sha}
        out = out_dir / f"{loc.locus_id}__{ds['dataset_id']}.parquet"
        err = None
        for attempt in range(1, 4):
            limiter.wait()
            proc = subprocess.run([str(C.TABIX), f"{url}##idx##{idx_path}", loc.region],
                                  capture_output=True, text=True, timeout=900)
            stderr = proc.stderr.strip()
            if proc.returncode == 0 and "[E::" not in stderr:
                try:
                    df = parse_sumstats_text(proc.stdout, header, loc.genes.keys(), loc.locus_id,
                                             ds["dataset_id"], loc.chrom, loc.window_start, loc.window_end)
                except Exception as exc:  # noqa: BLE001
                    err = f"parse: {exc!r}"
                else:
                    n_region = proc.stdout.count("\n")
                    rec.update(write_parquet(df, out))
                    rec.update({"status": "OK" if len(df) else "OK_NO_ROWS_FOR_LISTED_GENES",
                                "attempts": attempt, "fetched_at": C.utc_now(),
                                "n_rows_region_all_genes": n_region,
                                "n_genes_in_region_all": int(len({ln.split("\t", 17)[16] for ln in proc.stdout.splitlines() if ln})),
                                "n_rows_per_gene": {k: int(v) for k, v in df["gene_id"].value_counts().items()},
                                "genes_without_rows": sorted(set(loc.genes) - set(df["gene_id"].dropna()))})
                    if stderr:
                        rec["tabix_stderr"] = stderr[:500]
                    err = None
                    break
            else:
                err = f"tabix rc={proc.returncode}: {stderr[:500]}"
            time.sleep(5 * attempt)
        if err is not None:
            rec.update({"status": "FAILED", "error": err, "fetched_at": C.utc_now()})
        records.append(rec)
        print(f"  {ds['dataset_id']} {loc.locus_id}: {rec['status']} n_rows={rec.get('n_rows')}", flush=True)
    return records


def fetch_susie_dataset(ds: pd.Series, loci: list[Locus], lbf_dir: Path, force: bool) -> list[dict]:
    """One full lbf stream + one credible-set download per dataset, split by locus."""
    records: list[dict] = []
    all_genes = sorted({g for loc in loci for g in loc.genes})
    base = {"dataset_id": ds["dataset_id"], "study_label": ds["study_label"],
            "sample_group": ds["sample_group"], "quant_method": ds["quant_method"]}
    # credible sets (small): whole file, keep listed genes (all their credible sets, no window cut)
    cs_url = ds["credible_sets_url"]
    try:
        body, headers, _ = http_get(cs_url, timeout=600)
        cs = pd.read_csv(io.BytesIO(body), sep="\t", compression="gzip",
                         dtype={"molecular_trait_id": str, "gene_id": str, "cs_id": str, "variant": str,
                                "rsid": str, "region": str})
        for loc in loci:
            sub = cs[cs["gene_id"].isin(set(loc.genes))].copy()
            sub.insert(0, "dataset_id", ds["dataset_id"])
            sub.insert(0, "locus_id", loc.locus_id)
            rec = {**base, "kind": "credible_sets", "locus_id": loc.locus_id, "source_url": cs_url,
                   "source_sha256": hashlib.sha256(body).hexdigest(), "source_bytes": len(body),
                   "remote_last_modified": headers.get("Last-Modified"), "fetched_at": C.utc_now()}
            rec.update(write_parquet(sub, lbf_dir / f"{loc.locus_id}__{ds['dataset_id']}.credible_sets.parquet"))
            rec["status"] = "OK" if len(sub) else "OK_NO_CREDIBLE_SETS_FOR_LISTED_GENES"
            rec["genes_with_cs"] = sorted(sub["gene_id"].unique().tolist())
            records.append(rec)
    except Exception as exc:  # noqa: BLE001
        for loc in loci:
            records.append({**base, "kind": "credible_sets", "locus_id": loc.locus_id, "source_url": cs_url,
                            "status": "FAILED", "error": repr(exc), "fetched_at": C.utc_now()})
    # lbf: full stream (no index exists)
    lbf_url = ds["lbf_url"]
    outs = {loc.locus_id: lbf_dir / f"{loc.locus_id}__{ds['dataset_id']}.parquet" for loc in loci}
    if not force and all(p.exists() for p in outs.values()):
        for loc in loci:
            df = pd.read_parquet(outs[loc.locus_id])
            records.append({**base, "kind": "lbf", "locus_id": loc.locus_id, "source_url": lbf_url,
                            "status": "CACHED_EXISTING", "path": str(outs[loc.locus_id].relative_to(C.REPO_ROOT)),
                            "n_rows": int(len(df)), "sha256": C.sha256_file(outs[loc.locus_id])})
        return records
    try:
        print(f"  lbf stream start {ds['dataset_id']} ({ds['study_label']} {ds['sample_group']})", flush=True)
        flt, stats = stream_gzip_lines(lbf_url, all_genes)
        lbf = lbf_frame(flt.header, flt.kept)
        for loc in loci:
            sub = lbf[lbf["molecular_trait_id"].isin(set(loc.genes))
                      & (lbf["chromosome"].astype(str) == loc.chrom)
                      & lbf["position"].between(loc.window_start, loc.window_end)].copy()
            sub.insert(0, "dataset_id", ds["dataset_id"])
            sub.insert(0, "locus_id", loc.locus_id)
            rec = {**base, "kind": "lbf", "locus_id": loc.locus_id, "source_url": lbf_url,
                   "region_grch38": loc.region, "fetched_at": C.utc_now(), **{f"stream_{k}": v for k, v in stats.items()},
                   "n_rows_listed_genes_whole_region": int(lbf["molecular_trait_id"].isin(set(loc.genes)).sum())}
            rec.update(write_parquet(sub, outs[loc.locus_id]))
            rec["status"] = "OK" if len(sub) else "OK_NO_LBF_ROWS_FOR_LISTED_GENES"
            rec["genes_with_lbf"] = sorted(sub["molecular_trait_id"].unique().tolist())
            records.append(rec)
        print(f"  lbf stream done {ds['dataset_id']}: {stats['bytes'] / 1e6:,.0f} MB in {stats['seconds']} s", flush=True)
    except Exception as exc:  # noqa: BLE001
        for loc in loci:
            records.append({**base, "kind": "lbf", "locus_id": loc.locus_id, "source_url": lbf_url,
                            "status": "FAILED", "error": repr(exc), "fetched_at": C.utc_now()})
    return records


# ----------------------------------------------------------------------------------------------
# Provenance
# ----------------------------------------------------------------------------------------------
def merge_file_records(old: list[dict], new: list[dict]) -> list[dict]:
    key = lambda r: (r.get("kind"), r.get("locus_id"), r.get("dataset_id"))  # noqa: E731
    merged = {key(r): r for r in old}
    for r in new:
        merged[key(r)] = r
    return sorted(merged.values(), key=lambda r: tuple(str(x) for x in key(r)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--loci", type=Path, default=C.DATA / "gate_c_query_genes_prespecified.csv")
    ap.add_argument("--window-kb", type=int, default=500, help="half-window around the GRCh38 lead")
    ap.add_argument("--table-out", type=Path, default=C.DATA / "eqtl_catalogue_brain_datasets.csv")
    ap.add_argument("--out-dir", type=Path, default=C.WORK / "eqtl")
    ap.add_argument("--lbf-dir", type=Path, default=C.WORK / "eqtl_lbf")
    ap.add_argument("--raw-dir", type=Path, default=C.RAW / "eqtl_catalogue")
    ap.add_argument("--datasets", nargs="*", help="restrict to these dataset_ids (must be fetch-eligible)")
    ap.add_argument("--lbf", action="store_true", help="also stream SuSiE lbf + credible sets (heavy)")
    ap.add_argument("--no-sumstats", action="store_true", help="skip the tabix sumstats step")
    ap.add_argument("--table-only", action="store_true", help="write the dataset table and stop")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--min-interval", type=float, default=2.0, help="seconds between EBI request starts")
    ap.add_argument("--force", action="store_true", help="refetch even if outputs exist")
    args = ap.parse_args(argv)
    if args.workers > 3:
        ap.error("--workers > 3 is not allowed (EBI DoS guidance and shared machine)")

    started = C.utc_now()
    raw_dir: Path = args.raw_dir
    meta_dir = raw_dir / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    prov_path = raw_dir / "PROVENANCE.json"
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    failures: list[dict] = []

    # 1. metadata snapshots
    meta_records = {}
    for name, url in METADATA_FILES.items():
        body, _, _ = http_get(url)
        (meta_dir / name).write_bytes(body)
        meta_records[name] = {"url": url, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                              "path": str((meta_dir / name).relative_to(C.REPO_ROOT))}
    paths = pd.read_csv(meta_dir / "tabix_ftp_paths.tsv", sep="\t", dtype=str)
    meta = pd.read_csv(meta_dir / "dataset_metadata_r7.tsv", sep="\t", dtype=str)
    table = build_dataset_table(paths, meta)
    args.table_out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.table_out, index=False)
    elig = table[table["fetch_eligible"]].copy()
    if args.datasets:
        unknown = set(args.datasets) - set(elig["dataset_id"])
        if unknown:
            ap.error(f"not fetch-eligible / unknown dataset ids: {sorted(unknown)}")
        elig = elig[elig["dataset_id"].isin(args.datasets)]
    print(f"dataset table: {len(table)} nervous-system datasets; {len(elig)} fetch-eligible "
          f"(ADULT, gene-level, CNS) -> {args.table_out}")

    prov.update({
        "description": "eQTL Catalogue adult-brain gene-level eQTL fetch for Sprint-4 colocalisation loci",
        "script": "pipelines/sprint4/fetch_eqtl_catalogue.py",
        "eqtl_catalogue_release": RELEASE,
        "release_note": ("r7 = latest release with tabix-indexed TSV sumstats (June 2024; FTP files dated "
                         "2023-04-06/2024-05-20). r8 pre-release (/r8_beta/, GTEx v10) is parquet-only and not used."),
        "sources_not_used": {
            "r8_beta_GTEx_v10": ("GTEx v10 brain ge datasets (same dataset ids QTD000146..QTD000206; N 193-315 per "
                                 "region vs 114-209 in r7 GTEx v8) exist only as parquet under "
                                 f"{FTP_HTTPS}/r8_beta/sumstats/QTS000015/<dataset_id>/<dataset_id>.all.parquet "
                                 "(pre-release; no tabix). Not fetched."),
            "imported_GTEx_V8": ("tabix/tabix_ftp_paths_imported.tsv lists GTEx-original (non-uniformly processed) "
                                 "GTEx_V8 brain files; same donors as the uniformly processed r7 GTEx datasets, so "
                                 "not fetched."),
        },
        "rest_api": {"base": REST_API_V2, "probe": probe_rest_api(),
                     "note": "deprecated; Data_access page states the RESTful API is no longer available"},
        "data_access_doc": DATA_ACCESS_DOC,
        "resources_repo": {"repo": RESOURCES_REPO, "commit": RESOURCES_COMMIT, "files": meta_records},
        "url_patterns": {
            "sumstats": f"{FTP_HTTPS}/sumstats/<study_id>/<dataset_id>/<dataset_id>.all.tsv.gz (+.tbi)",
            "credible_sets": f"{FTP_HTTPS}/susie/<study_id>/<dataset_id>/<dataset_id>.credible_sets.tsv.gz",
            "lbf": f"{FTP_HTTPS}/susie/<study_id>/<dataset_id>/<dataset_id>.lbf_variable.txt.gz",
            "tabix_query": "tabix '<sumstats_url>##idx##<local .tbi>' <chr>:<start>-<end>",
        },
        "effect_allele": ("ALT. beta is per copy of the ALT allele (eQTL Catalogue Data_access FAQ: 'The ALT "
                          "allele is always the effect allele'; Columns.md: 'alt - GRCh38 alternative allele "
                          "(also the effect allele)'). ac = ALT allele count, an = allele number; maf is the "
                          "minor-allele frequency (ALT frequency = ac/an)."),
        "coordinates": "GRCh38 (eQTL Catalogue variant ids chr<chr>_<pos>_<ref>_<alt>)",
        "duplicate_rows_note": ("one rsid per row: a variant with several dbSNP-151 rsids is repeated; "
                                "de-duplicate on (molecular_trait_id, variant) before colocalisation"),
        "susie_access": {
            "public": True, "tabix_indexed": False,
            "why_no_region_query": ("lbf_variable.txt.gz and credible_sets.tsv.gz have no .tbi on the FTP; lbf "
                                    "files are plain gzip (not BGZF: gzip FLG byte 0x00, no BC extra field) and "
                                    "rows are grouped by fine-mapped gene with chromosomes interleaved, so a "
                                    "remote region query is impossible; the whole file must be streamed."),
            "lbf_columns": "molecular_trait_id region variant chromosome position lbf_variable1..lbf_variable10",
            "lbf_to_cs": "lbf_variableK corresponds to credible-set index L<K> (cs_id <trait>_L<K>) in credible_sets",
        },
        "dataset_table": {"path": str(args.table_out.relative_to(C.REPO_ROOT)), "n_rows": int(len(table)),
                          "sha256": C.sha256_file(args.table_out), "n_fetch_eligible": int(table["fetch_eligible"].sum())},
    })
    prov.setdefault("runs", []).append({"started_at": started, "argv": sys.argv[1:] if argv is None else argv,
                                        "git_head": C.git_head()})
    if args.table_only:
        prov_path.write_text(json.dumps(prov, indent=2, default=str) + "\n")
        return 0

    # 2. loci: GRCh38 lead positions
    loci = load_loci(args.loci)
    ok_loci = []
    for loc in loci:
        try:
            if loc.lead_pos_grch38 is None:
                resolve_lead_grch38(loc)
            set_window(loc, args.window_kb)
            ok_loci.append(loc)
        except Exception as exc:  # noqa: BLE001
            failures.append({"stage": "lead_lookup", "locus_id": loc.locus_id, "error": repr(exc)})
            print(f"  FAILED lead lookup {loc.locus_id}: {exc}", flush=True)
        time.sleep(0.2)
    prov["loci"] = {
        "input": str(args.loci.resolve().relative_to(C.REPO_ROOT)) if args.loci.resolve().is_relative_to(C.REPO_ROOT) else str(args.loci),
        "input_sha256": C.sha256_file(args.loci), "window_kb_each_side": args.window_kb,
        "ensembl_release": ensembl_release(),
        "items": [{"locus_id": l.locus_id, "chr": l.chrom, "lead_snp": l.lead_snp,
                   "lead_pos_grch37": l.lead_pos_grch37, "lead_pos_grch38": l.lead_pos_grch38,
                   "window_grch38": l.region if l.window_start else None, "genes": l.genes,
                   "lookup": l.lookup} for l in loci],
    }
    for l in ok_loci:
        print(f"  locus {l.locus_id} {l.lead_snp}: GRCh37 {l.lead_pos_grch37} -> GRCh38 {l.lead_pos_grch38}; "
              f"window {l.region}; {len(l.genes)} genes", flush=True)

    records: list[dict] = []
    limiter = RateLimiter(args.min_interval)
    # 3. sumstats via tabix
    if not args.no_sumstats and ok_loci:
        idx_dir = args.out_dir / ".tbi_cache"
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(fetch_sumstats_dataset, ds, ok_loci, args.out_dir, idx_dir, limiter, args.force):
                    ds["dataset_id"] for _, ds in elig.iterrows()}
            for fut in as_completed(futs):
                try:
                    records.extend(fut.result())
                except Exception as exc:  # noqa: BLE001
                    records.append({"kind": "sumstats", "dataset_id": futs[fut], "locus_id": None,
                                    "status": "FAILED", "error": repr(exc)})
    # 4. SuSiE lbf + credible sets
    if args.lbf and ok_loci:
        sizes = {}
        for _, ds in elig.iterrows():  # largest streams first, so the slowest file is not last
            limiter.wait()
            try:
                sizes[ds["dataset_id"]] = http_head(ds["lbf_url"])["content_length"]
            except Exception:  # noqa: BLE001 — the stream itself will record the failure
                sizes[ds["dataset_id"]] = -1
        elig = elig.assign(lbf_bytes=elig["dataset_id"].map(sizes)).sort_values("lbf_bytes", ascending=False)
        print(f"lbf streams: {len(elig)} files, {elig['lbf_bytes'].clip(lower=0).sum() / 1e9:.1f} GB total", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {}
            for _, ds in elig.iterrows():
                limiter.wait()
                futs[pool.submit(fetch_susie_dataset, ds, ok_loci, args.lbf_dir, args.force)] = ds["dataset_id"]
            for fut in as_completed(futs):
                try:
                    records.extend(fut.result())
                except Exception as exc:  # noqa: BLE001
                    records.append({"kind": "lbf", "dataset_id": futs[fut], "locus_id": None,
                                    "status": "FAILED", "error": repr(exc)})

    failures.extend({"stage": r.get("kind"), "locus_id": r.get("locus_id"), "dataset_id": r.get("dataset_id"),
                     "error": r.get("error")} for r in records if r.get("status") == "FAILED")
    prov["files"] = merge_file_records(prov.get("files", []), records)
    prov["runs"][-1].update({"finished_at": C.utc_now(), "n_records": len(records), "failures": failures})
    prov["failures_latest_run"] = failures
    prov_path.write_text(json.dumps(prov, indent=2, default=str) + "\n")
    n_ok = sum(r.get("status", "").startswith(("OK", "CACHED")) for r in records)
    print(f"done: {n_ok}/{len(records)} file records OK; {len(failures)} failures -> {prov_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
