#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_opentargets_coloc.py
==========================

Annotate a candidate gene list with Open Targets Platform fine-mapping
(credible set) and colocalisation evidence.

Run
---
    python3 pipelines/gene_tournament/fetch_opentargets_coloc.py            # full run
    python3 pipelines/gene_tournament/fetch_opentargets_coloc.py --limit 25 # smoke test
    python3 pipelines/gene_tournament/fetch_opentargets_coloc.py --offline  # rebuild CSVs from cache only

--------------------------------------------------------------------------
1. WHAT THE API LOOKS LIKE (verified by introspection, 2026-09-22 UTC)
--------------------------------------------------------------------------
Endpoint : POST https://api.platform.opentargets.org/api/v4/graphql
apiVersion 26.6.3, dataVersion year=26 month=06.

There is **no** top-level `colocalisation` query and **no** H0/H1/H2 fields.
`Colocalisation` exposes only `h3`, `h4`, `clpp`, `colocalisationMethod`,
`numberColocalisingVariants`, `rightStudyType`, `betaRatioSignAverage`,
`chromosome`, `studyLocusId` and `otherStudyLocus`.  H0/H1/H2 are simply not
served; do not reconstruct them, and do not assume 1 - (h3 + h4) means
anything.

Colocalisation is reachable ONLY through a `CredibleSet`:

    CredibleSet.colocalisation(studyTypes: [StudyTypeEnum], page: Pagination)
        -> Colocalisations { count rows { ... otherStudyLocus { ... } } }

(Note: contrary to some earlier notes, `colocalisation` DOES accept a
`studyTypes` argument as well as `page`.  This script does not use it — it
pulls everything and filters client-side so the cached payload is complete
and re-analysable offline without re-querying.)

The gene-centric entry point is:

    Target.credibleSets(page: Pagination) -> CredibleSets

**`Target.credibleSets` accepts ONLY `page`.**  There is no studyType,
biosample, tissue or p-value argument.  Every kind of filtering — GWAS vs
QTL, brain vs non-brain tissue — must therefore be done client-side after
pulling the full list.  That is why this script pages through everything and
filters in Python.

Empirically (see the report and the `query_status` column), `Target.credibleSets`
returns **only molecular-QTL credible sets** — those whose `study.target` is the
gene itself (eqtl, pqtl, sqtl, tuqtl, sceqtl, scpqtl, scsqtl, sctuqtl).  It does
NOT return GWAS credible sets that merely happen to be assigned to the gene by
locus-to-gene.  The column `n_credible_sets_gwas` is computed honestly from the
returned `studyType` values rather than assumed to be zero, but expect it to be
zero.  GWAS credible sets enter this dataset only as the *other* side of a
colocalisation (`Colocalisation.otherStudyLocus` with `rightStudyType == "gwas"`).

L2G: `CredibleSet.l2GPredictions(page)` exists and returns
`{ score, target { id approvedSymbol } }`.  It is populated for GWAS credible
sets.  Because the credible sets reachable gene-first are QTL credible sets,
L2G is empty for essentially all of them — L2G is a GWAS-locus-to-gene score, and
a QTL credible set has no L2G.  This script records L2G where present
(`max_l2g_on_gene_credible_sets`) and reports it as unavailable otherwise.
`Target.associatedDiseases` exists but returns disease-association scores, not
locus-to-gene scores, so it is not a substitute.

Query-complexity limit: the server rejects requests whose estimated response
is too large with HTTP 400 "Query is too expensive".  Measured safe envelope:
credible-set page size 500 with a coloc `count`-only subquery is fine;
10 aliased `credibleSet` root queries x 500 coloc rows is fine; 10 x 1000 and
200 x 100 are not.  The batch sizes below sit inside that envelope.

--------------------------------------------------------------------------
2. WHAT THE OUTPUT MEANS
--------------------------------------------------------------------------
opentargets_credible_sets.csv  — one row per input gene.
    n_credible_sets_total / _gwas / _qtl / _brain_qtl
        How many fine-mapped credible sets Open Targets holds in which the
        gene is the molecular trait.  This is a measure of how well *studied
        and how well powered* the QTL data for this gene is, in which
        tissues.  It is NOT a measure of the gene's importance.
    n_colocalisations_total, max_h4, max_h4_brain
        Colocalisation posteriors over all credible sets of that gene.
    best_brain_* columns
        The single highest-H4 colocalisation whose QTL side is a brain/neural
        biosample.
    query_status
        'ok'                  -> queried successfully (n_* are real counts,
                                 and 0 genuinely means zero)
        'ok:gene_not_found'   -> the endpoint answered, but `target` was null
                                 for this Ensembl ID (gene retired/unmapped).
                                 Counts are null, NOT zero.
        'error:<reason>'      -> the query failed.  Counts are null.
    The distinction between "queried and found nothing" (0) and "could not
    query" (null) is load-bearing.  Never coerce a null to 0 downstream.

opentargets_cognition_coloc.csv — one row per colocalisation whose *other*
    side is a GWAS of a cognition-related trait (see COGNITION_PATTERNS).

--------------------------------------------------------------------------
3. WHAT THE OUTPUT DOES **NOT** MEAN  (read this before using the numbers)
--------------------------------------------------------------------------
* **Colocalisation is not causality.**  H4 is the posterior probability that
  two association signals share a single causal variant.  Sharing a causal
  variant is consistent with the QTL mediating the GWAS signal, but it is
  equally consistent with horizontal pleiotropy (one variant, two independent
  downstream consequences) and with the gene being a bystander next to the
  real effector.

* **H4 is a posterior under a single-causal-variant assumption that is
  frequently violated.**  Real loci routinely carry multiple independent
  causal variants.  When they do, coloc's model is misspecified and H4 is
  not calibrated — it can be inflated or deflated.  H4 is also sensitive to
  the priors, to LD reference mismatch, and to the QTL study's power: a
  well-powered tissue gets high H4 partly because it is well powered.  H4
  is a ranking aid, not a probability you should quote as if it were one.

* **A high H4 with a brain eQTL does not tell you which direction of
  expression change helps cognition.**  It tells you the two signals look
  like the same variant.  It says nothing on its own about sign.  Direction
  requires jointly interpreting the QTL beta, the GWAS beta, and *the allele
  each beta is expressed with respect to* — and both must be on the same
  effect allele.  This script records every direction field the API serves
  (`qtl_beta`, `gwas_beta`, `beta_ratio_sign_average`, and the alleles) and
  computes NOTHING from them beyond a labelled, explicitly-caveated
  concordance flag.  See the direction notes in the CSV header comments.

* A gene appearing here at all means it has QTL data in Open Targets.  Genes
  absent from the colocalisation output may be absent because nothing
  colocalises, or because nobody has run a well-powered QTL study in the
  relevant tissue.  Absence of evidence, etc.

* The brain-tissue filter is a string match on biosample names (see
  BRAIN_PATTERNS).  It is deliberately auditable: the set of biosample
  strings actually matched is written to brain_biosamples_matched.txt.
  It will include some non-neuronal cells resident in brain and may miss
  idiosyncratically-named samples.

--------------------------------------------------------------------------
4. POLITENESS / REPRODUCIBILITY
--------------------------------------------------------------------------
Requests are batched (aliased GraphQL root fields), separated by
REQUEST_DELAY seconds, and retried with exponential backoff on transient
failures.  Every raw response is cached as gzipped JSON under
data/raw/opentargets_tournament/<RUN_DATE>/ so the run can be re-analysed
offline (`--offline`) without touching the network.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
RUN_DATE = "2026-09-22"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IN_CSV = os.path.join(ROOT, "data", "gene_tournament", "candidate_genes_for_annotation.csv")
OUT_DIR = os.path.join(ROOT, "data", "gene_tournament")
OUT_CS = os.path.join(OUT_DIR, "opentargets_credible_sets.csv")
OUT_COG = os.path.join(OUT_DIR, "opentargets_cognition_coloc.csv")
OUT_BIOS = os.path.join(OUT_DIR, "brain_biosamples_matched.txt")
OUT_PROV = os.path.join(OUT_DIR, "opentargets_provenance.json")
CACHE_DIR = os.path.join(ROOT, "data", "raw", "opentargets_tournament", RUN_DATE)

REQUEST_DELAY = 0.15          # seconds a worker waits after each HTTP request
MAX_RETRIES = 5
WORKERS = 4                   # concurrent HTTP workers (kept low deliberately)
CS_PAGE_SIZE = 500            # credible sets per page (within complexity limit)

# Colocalisation paging.  Two hard limits discovered by probing, both of which
# have to be respected or the run silently corrupts:
#   * "Query is too expensive" (HTTP 400) when aliases x page_size is too big
#     for the requested field set.  ~2500 rows/request is safe for the full
#     field set; 10 aliases x 500 on a 17q21.31 gene is not.
#   * A page size above ~3000 makes the server return `credibleSet: null`
#     with HTTP 200 and NO error - a silent failure that looks like "gene has
#     no colocalisations".  Null nodes are therefore treated as errors, never
#     as zero.
COLOC_PAGE_SIZE = 250         # coloc rows per credible set per page
COLOC_ROW_BUDGET = 2500       # max total rows requested in one HTTP request
MAX_ALIASES = 20              # max aliased credibleSet root fields per request
TIMEOUT = 300

# QTL study types per StudyTypeEnum (everything that is not 'gwas')
QTL_TYPES = {"eqtl", "pqtl", "sqtl", "tuqtl", "sceqtl", "scpqtl", "scsqtl", "sctuqtl"}

# --------------------------------------------------------------------------
# Brain / neural biosample filter.  Applied case-insensitively to
# study.biosample.biosampleName.  Every distinct matched string is written to
# brain_biosamples_matched.txt so the filter is auditable.
# --------------------------------------------------------------------------
# Open Targets serves only 98 distinct biosample names across the credible
# sets of these 400 genes, so the brain filter is an explicit CURATED
# allowlist rather than a bare keyword regex.  Two reasons:
#   * a keyword regex produces false positives - "cortex of kidney" and
#     "adrenal cortex" both contain "cortex"; "tibial nerve" is peripheral;
#   * and false negatives - "Ammon's horn" IS the hippocampus but contains
#     none of the obvious keywords.  A pure regex silently drops it.
# The regex below is retained only as a fallback for biosample names that are
# not in the reviewed set (e.g. if a future data release adds one); anything
# it decides is written to the audit file under "UNREVIEWED" so the filter
# never changes silently.
BRAIN_BIOSAMPLES = {
    # --- CNS regions -------------------------------------------------------
    "Ammon's horn",                      # hippocampus proper
    "amygdala",
    "anterior cingulate cortex",
    "caudate nucleus",
    "cerebellum",
    "dorsolateral prefrontal cortex",
    "frontal cortex",
    "hypothalamus",
    "neocortex",
    "nucleus accumbens",
    "putamen",
    "substantia nigra",
    "C1 segment of cervical spinal cord",
    # --- neural / glial cell types ----------------------------------------
    "astrocyte",
    "dopaminergic neuron",
    "ependymal cell",
    "floor plate",                       # neural-tube derived
    "microglial cell",
    "neural progenitor cell",
    "neuron",
    "sensory neuron",                    # peripheral (DRG) but neuronal
    "serotonergic neuron",
}

# Reviewed and deliberately EXCLUDED, with the reason.  Listed explicitly so
# the exclusion is a visible decision rather than an accident of regex.
NONBRAIN_REVIEWED = {
    "cortex of kidney": "renal cortex, not brain",
    "tibial nerve": "peripheral nerve, not CNS",
    "pituitary gland": "endocrine gland; anterior lobe is epithelial, not neural tissue",
}

# Fallback keyword regex, applied ONLY to biosample names not reviewed above.
BRAIN_PATTERNS = [
    "brain", "cortex", "cortical", "cerebell", "cerebral", "hippocamp",
    "amygdala", "caudate", "putamen", "nucleus accumbens", "accumbens",
    "hypothalamus", "substantia nigra", "spinal cord", "dlpfc",
    "prefrontal", "frontal lobe", "anterior cingulate", "basal ganglia",
    "neuron", "neuronal", "astrocyte", "microglia", "microglial",
    "oligodendrocyte", "glial", "glia", "neural",
]
BRAIN_RE = re.compile("|".join(re.escape(p) for p in BRAIN_PATTERNS), re.I)

UNREVIEWED_BIOSAMPLES: dict[str, bool] = {}


def is_brain_biosample(name: str | None) -> bool:
    if not name:
        return False
    if name in BRAIN_BIOSAMPLES:
        return True
    if name in NONBRAIN_REVIEWED:
        return False
    verdict = bool(BRAIN_RE.search(name))
    UNREVIEWED_BIOSAMPLES[name] = verdict
    return verdict


# --------------------------------------------------------------------------
# Cognition trait filter, applied to the *other* (GWAS) study's
# traitFromSource.  Deliberately broad on recall, then every matched trait
# string is dumped in the output so it can be manually vetted.
# --------------------------------------------------------------------------
# Matched against the *other* (GWAS) study's traitFromSource.
# Word boundaries are REQUIRED: a bare "cognition" substring also matches
# "re-cognition" inside "Signal recognition particle 19 kDa protein levels"
# and "Nuclear prelamin A recognition factor protein level", both of which are
# pQTL protein-level traits and emphatically not cognition phenotypes.
COGNITION_PATTERNS = [
    r"\bcognitive\b", r"\bcognition\b", r"\bnoncognitive\b",
    r"\bintelligence\b", r"\bIQ\b",
    r"\beducational attainment\b", r"\beducation attainment\b",
    r"\byears of (education|schooling)\b", r"\bschooling\b",
    r"\bqualifications?\b", r"\bcollege completion\b",
    r"\buniversity degree\b", r"\bfull[- ]time education\b",
    r"\breaction time\b", r"\bprocessing speed\b", r"\bprocessing accuracy\b",
    r"\breasoning\b", r"\bverbal[- ]numerical\b",
    r"\bmemory\b", r"\bpairs matching\b", r"\bpaired associate\b",
    r"\bmath\b", r"\bmaths\b", r"\bmathematics?\b", r"\bmathematical\b",
    r"\barithmetic\b", r"\bnumeracy\b",
    r"\btrail making\b", r"\bsymbol digit\b", r"\bdigit span\b",
    r"\bexecutive function\b", r"\bfluid intelligence\b",
    r"\bmatrix pattern\b", r"\btower rearranging\b", r"\bword interpolation\b",
    r"\bFI\d+:", r"\bg[- ]factor\b", r"\bgeneral cognitive ability\b",
]
COGNITION_RE = re.compile("|".join(COGNITION_PATTERNS), re.I)

# Traits that survive the patterns above but are NOT cognition phenotypes of
# the individual.  Each is a deliberate, reviewed exclusion.
COGNITION_EXCLUDE = [
    # immune cell-type traits that contain the word "memory"
    r"memory (T|B|CD4|CD8)", r"memory (cell|regulatory)", r"immunological memory",
    r"central memory", r"effector memory", r"\bmemory (B|T) cell\b",
    # a leisure activity, not a cognitive measure
    r"leisure/social activities",
    # area-level (ecological) deprivation index, not an individual phenotype
    r"education score england", r"education score scotland", r"education score wales",
    # the phenotype is neuroticism, merely conditioned on a cognitive trait
    r"^neuroticism conditioned on",
]
COGNITION_EXCLUDE_RE = re.compile("|".join(COGNITION_EXCLUDE), re.I)


def is_cognition_trait(trait: str | None) -> bool:
    if not trait:
        return False
    if COGNITION_EXCLUDE_RE.search(trait):
        return False
    return bool(COGNITION_RE.search(trait))


# --------------------------------------------------------------------------
# GraphQL queries (verbatim; also written to the provenance JSON)
# --------------------------------------------------------------------------
Q_META = """query Meta {
  meta { name apiVersion { x y z } dataVersion { year month } }
}"""

Q_GENE_CS = """query GeneCredibleSets($ensemblId: String!, $index: Int!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    credibleSets(page: { index: $index, size: $size }) {
      count
      rows {
        studyLocusId studyType finemappingMethod region chromosome position
        beta zScore standardError pValueMantissa pValueExponent
        effectAlleleFrequencyFromSource isTransQtl qtlGeneId confidence
        credibleSetIndex
        variant { id rsIds referenceAllele alternateAllele }
        study {
          id projectId studyType traitFromSource nSamples nCases pubmedId condition
          biosample { biosampleId biosampleName }
          target { id approvedSymbol }
        }
        l2GPredictions(page: { index: 0, size: 3 }) {
          count
          rows { score target { id approvedSymbol } }
        }
        colocalisation(page: { index: 0, size: 1 }) { count }
      }
    }
  }
}"""

# Built dynamically: N aliased credibleSet root fields per request.
COLOC_FRAGMENT = """{
      studyLocusId
      colocalisation(page: { index: %(idx)d, size: %(size)d }) {
        count
        rows {
          colocalisationMethod h3 h4 clpp betaRatioSignAverage
          numberColocalisingVariants rightStudyType chromosome
          otherStudyLocus {
            studyLocusId studyType beta standardError pValueMantissa pValueExponent
            effectAlleleFrequencyFromSource finemappingMethod
            variant { id rsIds referenceAllele alternateAllele }
            study {
              id projectId studyType traitFromSource nSamples nCases pubmedId
              publicationFirstAuthor publicationDate
              biosample { biosampleId biosampleName }
              target { id approvedSymbol }
            }
          }
        }
      }
    }"""


def build_coloc_query(jobs):
    """jobs: list of (studyLocusId, page_index, page_size). Returns (query, variables)."""
    sig = ", ".join(f"$s{i}: String!" for i in range(len(jobs)))
    parts = []
    for i, (_slid, page_idx, page_sz) in enumerate(jobs):
        frag = COLOC_FRAGMENT % {"idx": page_idx, "size": page_sz}
        parts.append(f"  cs{i}: credibleSet(studyLocusId: $s{i}) {frag}")
    q = "query ColocBatch(%s) {\n%s\n}" % (sig, "\n".join(parts))
    variables = {f"s{i}": jobs[i][0] for i in range(len(jobs))}
    return q, variables


def plan_coloc_jobs(cs_rows):
    """Expand credible sets into (slid, page_index, page_size) paging jobs."""
    jobs = []
    for r in cs_rows:
        cnt = ((r.get("colocalisation") or {}).get("count")) or 0
        for page in range((cnt + COLOC_PAGE_SIZE - 1) // COLOC_PAGE_SIZE):
            jobs.append((r["studyLocusId"], page, COLOC_PAGE_SIZE))
    return jobs


def group_jobs(jobs):
    """Group paging jobs into HTTP requests inside the complexity envelope."""
    groups, cur, budget = [], [], 0
    for j in jobs:
        if cur and (budget + j[2] > COLOC_ROW_BUDGET or len(cur) >= MAX_ALIASES):
            groups.append(cur); cur, budget = [], 0
        cur.append(j); budget += j[2]
    if cur:
        groups.append(cur)
    return groups


# --------------------------------------------------------------------------
# HTTP with retry/backoff + gzipped response cache
# --------------------------------------------------------------------------
class ApiError(Exception):
    pass


_stats = {"http": 0, "cache_hits": 0, "retries": 0, "bytes": 0}
_lock_stats = Lock()


def _cache_path(tag: str, key: str) -> str:
    h = hashlib.sha1(key.encode()).hexdigest()[:20]
    d = os.path.join(CACHE_DIR, tag)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{tag}_{h}.json.gz")


def graphql(query: str, variables: dict, tag: str, cache_key: str, offline: bool = False):
    """POST a GraphQL query, with on-disk gzip cache and retry/backoff."""
    path = _cache_path(tag, cache_key)
    if os.path.exists(path):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            with _lock:
                _stats["cache_hits"] += 1
            return json.load(fh)["response"]
    if offline:
        raise ApiError("offline mode and response not in cache")

    payload = json.dumps({"query": query, "variables": variables}).encode()
    last = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                ENDPOINT, data=payload,
                headers={"Content-Type": "application/json",
                         "Accept": "application/json",
                         "User-Agent": "gene-tournament-annotation/1.0 (read-only research query)"},
            )
            raw = urllib.request.urlopen(req, timeout=TIMEOUT).read()
            with _lock:
                _stats["http"] += 1
                _stats["bytes"] += len(raw)
            body = json.loads(raw.decode("utf-8"))
            if "errors" in body and not body.get("data"):
                raise ApiError("graphql_errors:" + json.dumps(body["errors"])[:200])
            record = {
                "fetched_utc": datetime.now(timezone.utc).isoformat(),
                "endpoint": ENDPOINT,
                "query": query,
                "variables": variables,
                "response": body,
            }
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                json.dump(record, fh)
            time.sleep(REQUEST_DELAY)
            return body
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            last = f"http_{exc.code}:{detail}"
            if exc.code in (400, 404):      # deterministic; do not retry
                raise ApiError(last)
            _stats["retries"] += 1
            time.sleep(min(2 ** attempt, 30))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last = f"{type(exc).__name__}:{str(exc)[:120]}"
            _stats["retries"] += 1
            time.sleep(min(2 ** attempt, 30))
        except ApiError as exc:
            last = str(exc)
            _stats["retries"] += 1
            time.sleep(min(2 ** attempt, 30))
    raise ApiError(last or "unknown")


# --------------------------------------------------------------------------
# Pass A — credible sets per gene
# --------------------------------------------------------------------------
def fetch_gene_credible_sets(ensembl_id: str, offline: bool = False):
    """Return (status, symbol, rows). status is 'ok' / 'ok:gene_not_found' / 'error:...'"""
    rows, index, symbol = [], 0, None
    while True:
        try:
            body = graphql(Q_GENE_CS,
                           {"ensemblId": ensembl_id, "index": index, "size": CS_PAGE_SIZE},
                           "gene_cs", f"{ensembl_id}|{index}|{CS_PAGE_SIZE}", offline)
        except ApiError as exc:
            return f"error:{exc}"[:200], symbol, []
        tgt = (body.get("data") or {}).get("target")
        if tgt is None:
            return "ok:gene_not_found", None, []
        symbol = tgt.get("approvedSymbol")
        cs = tgt.get("credibleSets") or {}
        page_rows = cs.get("rows") or []
        rows.extend(page_rows)
        total = cs.get("count") or 0
        if len(rows) >= total or not page_rows:
            break
        index += 1
        if index > 40:                       # hard stop; 20k credible sets
            break
    return "ok", symbol, rows


# --------------------------------------------------------------------------
# Pass B — colocalisation rows for a set of credible sets
# --------------------------------------------------------------------------
_lock = Lock()


def _run_group(group, offline):
    """
    Execute one grouped HTTP request.  Returns (rows_by_slid, errors_by_slid).

    On "too expensive" (400) the group is split and retried; a group of one
    is retried with a halved page size.  A `null` credibleSet node is an
    ERROR, never an empty result - the API returns null with HTTP 200 when the
    page size is too large, and treating that as zero would silently fabricate
    measured-absence.
    """
    out, errs = {}, {}
    query, variables = build_coloc_query(group)
    key = "|".join(f"{s}:{p}:{z}" for s, p, z in group)
    try:
        body = graphql(query, variables, "coloc", key, offline)
    except ApiError as exc:
        msg = str(exc)
        too_big = "too expensive" in msg or "http_400" in msg
        if too_big and len(group) > 1:                       # split the batch
            mid = len(group) // 2
            for half in (group[:mid], group[mid:]):
                o, e = _run_group(half, offline)
                for k, v in o.items():
                    out.setdefault(k, []).extend(v)
                errs.update(e)
            return out, errs
        if too_big and len(group) == 1 and group[0][2] > 25:  # shrink the page
            slid, page_idx, page_sz = group[0]
            new_sz = page_sz // 2
            factor = page_sz // new_sz
            sub = [(slid, page_idx * factor + k, new_sz) for k in range(factor)]
            for one in sub:
                o, e = _run_group([one], offline)
                for k, v in o.items():
                    out.setdefault(k, []).extend(v)
                errs.update(e)
            return out, errs
        for slid, _p, _z in group:
            errs[slid] = f"error:{msg}"[:200]
        return out, errs

    data = body.get("data") or {}
    for i, (slid, page_idx, page_sz) in enumerate(group):
        node = data.get(f"cs{i}")
        if node is None:
            # Silent-null. Retry this one alone at a smaller page size.
            if page_sz > 25:
                new_sz = page_sz // 2
                factor = page_sz // new_sz
                for k in range(factor):
                    o, e = _run_group([(slid, page_idx * factor + k, new_sz)], offline)
                    for kk, vv in o.items():
                        out.setdefault(kk, []).extend(vv)
                    errs.update(e)
            else:
                errs[slid] = "error:credibleSet_null_node"
            continue
        out.setdefault(slid, []).extend(((node.get("colocalisation") or {}).get("rows")) or [])
    return out, errs


def fetch_coloc(jobs, offline: bool = False, workers: int = WORKERS):
    """
    jobs: list of (studyLocusId, page_index, page_size).
    Returns (dict slid -> coloc rows, dict slid -> error string).
    """
    out, errs = {}, {}
    groups = group_jobs(jobs)
    if not groups:
        return out, errs
    if offline or workers <= 1:
        results = [_run_group(g, offline) for g in groups]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda g: _run_group(g, offline), groups))
    for o, e in results:
        for k, v in o.items():
            out.setdefault(k, []).extend(v)
        errs.update(e)
    return out, errs


# --------------------------------------------------------------------------
# Aggregation helpers
# --------------------------------------------------------------------------
def pval(mantissa, exponent):
    if mantissa is None or exponent is None:
        return None
    try:
        return float(mantissa) * (10 ** int(exponent))
    except (TypeError, ValueError, OverflowError):
        return None


def direction_note(qtl_beta, gwas_beta):
    """
    Label the sign relationship between the two betas WITHOUT interpreting it.

    This is NOT 'more expression is better'.  The two betas are reported with
    respect to each study's own effect allele, and Open Targets does not
    guarantee those alleles are harmonised across the two credible sets.  The
    variant alleles for both sides are emitted alongside so a human can
    harmonise them before drawing any conclusion.
    """
    if qtl_beta is None or gwas_beta is None:
        return "unknown:missing_beta"
    if qtl_beta == 0 or gwas_beta == 0:
        return "unknown:zero_beta"
    return "same_sign_unharmonised" if (qtl_beta > 0) == (gwas_beta > 0) else "opposite_sign_unharmonised"


CS_FIELDS = [
    "GENE", "current_symbol", "ensembl_gene_id", "ot_approved_symbol", "CHR", "ZSTAT", "P",
    "query_status", "coloc_scan_status",
    "n_credible_sets_total", "n_credible_sets_gwas", "n_credible_sets_qtl",
    "n_credible_sets_brain_qtl",
    "n_colocalisations_total", "n_colocalisations_fetched",
    "max_h4", "max_h4_brain", "max_clpp",
    "n_coloc_h4_gt_0.8", "n_brain_coloc_h4_gt_0.8",
    "best_brain_h4", "best_brain_clpp", "best_brain_method", "best_brain_biosample",
    "best_brain_qtl_study_type", "best_brain_qtl_study_id", "best_brain_qtl_beta",
    "best_brain_other_study_id", "best_brain_other_study_type",
    "best_brain_other_trait", "best_brain_other_pubmedId", "best_brain_other_nSamples",
    "best_brain_other_beta", "best_brain_variant_id", "best_brain_variant_rsid",
    "best_brain_beta_ratio_sign_average", "best_brain_direction_note",
    "n_cognition_coloc", "max_h4_cognition", "max_h4_cognition_brain",
    "finemapping_methods_seen", "qtl_study_types_seen",
    "brain_biosamples_matched", "n_distinct_biosamples",
    "max_l2g_on_gene_credible_sets",
    "coloc_pages_incomplete", "coloc_error_detail",
]

COG_FIELDS = [
    "GENE", "current_symbol", "ensembl_gene_id", "ot_approved_symbol", "CHR", "ZSTAT", "P",
    "h4", "h3", "clpp", "colocalisation_method", "number_colocalising_variants",
    "qtl_study_locus_id", "qtl_study_type", "qtl_study_id", "qtl_project_id",
    "qtl_biosample_id", "qtl_biosample_name", "qtl_is_brain",
    "qtl_molecular_trait", "qtl_target_id", "qtl_target_symbol",
    "qtl_n_samples", "qtl_finemapping_method",
    "qtl_beta", "qtl_standard_error", "qtl_pvalue",
    "qtl_variant_id", "qtl_variant_rsid", "qtl_ref_allele", "qtl_alt_allele",
    "qtl_effect_allele_frequency",
    "gwas_study_locus_id", "gwas_study_id", "gwas_project_id", "gwas_trait",
    "gwas_pubmed_id", "gwas_n_samples", "gwas_n_cases",
    "gwas_publication_first_author", "gwas_publication_date",
    "gwas_beta", "gwas_standard_error", "gwas_pvalue",
    "gwas_variant_id", "gwas_variant_rsid", "gwas_ref_allele", "gwas_alt_allele",
    "gwas_effect_allele_frequency", "gwas_finemapping_method",
    "beta_ratio_sign_average", "direction_note", "direction_caveat",
]

DIRECTION_CAVEAT = (
    "betas are on each study's own effect allele and are NOT harmonised by this script; "
    "sign agreement does not imply more-expression-is-better"
)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="only process the N most significant genes (by P)")
    ap.add_argument("--offline", action="store_true",
                    help="use the response cache only; never hit the network")
    ap.add_argument("--workers", type=int, default=WORKERS,
                    help="concurrent HTTP workers (default %d)" % WORKERS)
    args = ap.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    # ---- provenance: API version --------------------------------------
    meta = graphql(Q_META, {}, "meta", "meta", args.offline)
    m = meta["data"]["meta"]
    api_version = f"{m['apiVersion']['x']}.{m['apiVersion']['y']}.{m['apiVersion']['z']}"
    data_version = f"{m['dataVersion']['year']}.{m['dataVersion']['month']}"
    print(f"[meta] apiVersion={api_version} dataVersion={data_version}", flush=True)

    # ---- input, prioritised by P --------------------------------------
    with open(IN_CSV, newline="", encoding="utf-8") as fh:
        genes = list(csv.DictReader(fh))
    def pkey(g):
        try:
            return float(g["P"])
        except (TypeError, ValueError):
            return float("inf")
    genes.sort(key=pkey)
    if args.limit:
        genes = genes[:args.limit]
    print(f"[input] {len(genes)} genes (sorted by P ascending)", flush=True)

    ckpt_path = os.path.join(CACHE_DIR, "gene_rows_checkpoint.jsonl")
    ckpt = open(ckpt_path, "a", encoding="utf-8")
    gene_rows, cog_rows = [], []
    brain_biosamples_global = {}
    cog_traits_global = {}
    noncog_traits_global = {}
    t0 = time.time()

    for n, g in enumerate(genes, 1):
        eid = (g.get("ensembl_gene_id") or "").strip()
        base = {
            "GENE": g.get("GENE"), "current_symbol": g.get("current_symbol"),
            "ensembl_gene_id": eid, "CHR": g.get("CHR"),
            "ZSTAT": g.get("ZSTAT"), "P": g.get("P"),
        }

        if not eid or not eid.startswith("ENSG"):
            gene_rows.append({**base, "ot_approved_symbol": None,
                              "query_status": "error:no_ensembl_id_in_input"})
            continue

        status, symbol, cs_rows = fetch_gene_credible_sets(eid, args.offline)
        row = {**base, "ot_approved_symbol": symbol, "query_status": status}

        if status.startswith("error"):
            # every count stays blank -> null.  NEVER zero.
            gene_rows.append(row)
            ckpt.write(json.dumps(row, default=str) + "\n"); ckpt.flush()
            print(f"[{n}/{len(genes)}] {g.get('current_symbol')} {eid} {status}", flush=True)
            continue
        if status == "ok:gene_not_found":
            gene_rows.append(row)
            ckpt.write(json.dumps(row, default=str) + "\n"); ckpt.flush()
            print(f"[{n}/{len(genes)}] {g.get('current_symbol')} {eid} gene_not_found", flush=True)
            continue

        # ---- credible-set level counts (real measurements) -------------
        n_total = len(cs_rows)
        n_gwas = sum(1 for r in cs_rows if r.get("studyType") == "gwas")
        n_qtl = sum(1 for r in cs_rows if r.get("studyType") in QTL_TYPES)
        brain_cs, brain_names = [], set()
        biosamples = set()
        for r in cs_rows:
            bname = (((r.get("study") or {}).get("biosample")) or {}).get("biosampleName")
            if bname:
                biosamples.add(bname)
            if r.get("studyType") in QTL_TYPES and is_brain_biosample(bname):
                brain_cs.append(r)
                brain_names.add(bname)
                brain_biosamples_global[bname] = brain_biosamples_global.get(bname, 0) + 1
        methods = sorted({r.get("finemappingMethod") for r in cs_rows if r.get("finemappingMethod")})
        sts = sorted({r.get("studyType") for r in cs_rows if r.get("studyType")})
        l2g_scores = [p.get("score") for r in cs_rows
                      for p in (((r.get("l2GPredictions") or {}).get("rows")) or [])
                      if p.get("score") is not None
                      and ((p.get("target") or {}).get("id") == eid)]

        # ---- Pass B: colocalisation ------------------------------------
        expected = {r["studyLocusId"]: (((r.get("colocalisation") or {}).get("count")) or 0)
                    for r in cs_rows}
        jobs = plan_coloc_jobs(cs_rows)
        coloc_by_slid, coloc_errs = fetch_coloc(jobs, args.offline, args.workers) if jobs else ({}, {})

        cs_by_id = {r["studyLocusId"]: r for r in cs_rows}
        n_expected = sum(expected.values())
        n_fetched = sum(len(v) for v in coloc_by_slid.values())

        max_h4 = max_h4_brain = max_clpp = None
        max_h4_cog = max_h4_cog_brain = None
        n_h4_08 = n_brain_h4_08 = 0
        n_cog = 0
        best_brain = None

        for slid, rows_ in coloc_by_slid.items():
            cs = cs_by_id.get(slid) or {}
            study = cs.get("study") or {}
            bios = study.get("biosample") or {}
            bname = bios.get("biosampleName")
            cs_is_brain = cs.get("studyType") in QTL_TYPES and is_brain_biosample(bname)
            for c in rows_:
                h4, clpp = c.get("h4"), c.get("clpp")
                if h4 is not None:
                    max_h4 = h4 if max_h4 is None else max(max_h4, h4)
                    if h4 > 0.8:
                        n_h4_08 += 1
                    if cs_is_brain:
                        max_h4_brain = h4 if max_h4_brain is None else max(max_h4_brain, h4)
                        if h4 > 0.8:
                            n_brain_h4_08 += 1
                if clpp is not None:
                    max_clpp = clpp if max_clpp is None else max(max_clpp, clpp)

                osl = c.get("otherStudyLocus") or {}
                ostudy = osl.get("study") or {}
                if cs_is_brain and h4 is not None and (best_brain is None or h4 > best_brain[0]):
                    best_brain = (h4, c, cs)

                # ---- cognition GWAS colocalisations --------------------
                if (c.get("rightStudyType") == "gwas" or ostudy.get("studyType") == "gwas") \
                        and not is_cognition_trait(ostudy.get("traitFromSource")):
                    _t = ostudy.get("traitFromSource")
                    if _t:
                        noncog_traits_global[_t] = noncog_traits_global.get(_t, 0) + 1
                if (c.get("rightStudyType") == "gwas" or ostudy.get("studyType") == "gwas") \
                        and is_cognition_trait(ostudy.get("traitFromSource")):
                    n_cog += 1
                    if h4 is not None:
                        max_h4_cog = h4 if max_h4_cog is None else max(max_h4_cog, h4)
                        if cs_is_brain:
                            max_h4_cog_brain = h4 if max_h4_cog_brain is None else max(max_h4_cog_brain, h4)
                    trait = ostudy.get("traitFromSource")
                    cog_traits_global[trait] = cog_traits_global.get(trait, 0) + 1
                    cvar = cs.get("variant") or {}
                    ovar = osl.get("variant") or {}
                    cog_rows.append({
                        **base, "ot_approved_symbol": symbol,
                        "h4": h4, "h3": c.get("h3"), "clpp": clpp,
                        "colocalisation_method": c.get("colocalisationMethod"),
                        "number_colocalising_variants": c.get("numberColocalisingVariants"),
                        "qtl_study_locus_id": slid,
                        "qtl_study_type": cs.get("studyType"),
                        "qtl_study_id": study.get("id"),
                        "qtl_project_id": study.get("projectId"),
                        "qtl_biosample_id": bios.get("biosampleId"),
                        "qtl_biosample_name": bname,
                        "qtl_is_brain": cs_is_brain,
                        "qtl_molecular_trait": study.get("traitFromSource"),
                        "qtl_target_id": (study.get("target") or {}).get("id"),
                        "qtl_target_symbol": (study.get("target") or {}).get("approvedSymbol"),
                        "qtl_n_samples": study.get("nSamples"),
                        "qtl_finemapping_method": cs.get("finemappingMethod"),
                        "qtl_beta": cs.get("beta"),
                        "qtl_standard_error": cs.get("standardError"),
                        "qtl_pvalue": pval(cs.get("pValueMantissa"), cs.get("pValueExponent")),
                        "qtl_variant_id": cvar.get("id"),
                        "qtl_variant_rsid": ";".join(cvar.get("rsIds") or []),
                        "qtl_ref_allele": cvar.get("referenceAllele"),
                        "qtl_alt_allele": cvar.get("alternateAllele"),
                        "qtl_effect_allele_frequency": cs.get("effectAlleleFrequencyFromSource"),
                        "gwas_study_locus_id": osl.get("studyLocusId"),
                        "gwas_study_id": ostudy.get("id"),
                        "gwas_project_id": ostudy.get("projectId"),
                        "gwas_trait": trait,
                        "gwas_pubmed_id": ostudy.get("pubmedId"),
                        "gwas_n_samples": ostudy.get("nSamples"),
                        "gwas_n_cases": ostudy.get("nCases"),
                        "gwas_publication_first_author": ostudy.get("publicationFirstAuthor"),
                        "gwas_publication_date": ostudy.get("publicationDate"),
                        "gwas_beta": osl.get("beta"),
                        "gwas_standard_error": osl.get("standardError"),
                        "gwas_pvalue": pval(osl.get("pValueMantissa"), osl.get("pValueExponent")),
                        "gwas_variant_id": ovar.get("id"),
                        "gwas_variant_rsid": ";".join(ovar.get("rsIds") or []),
                        "gwas_ref_allele": ovar.get("referenceAllele"),
                        "gwas_alt_allele": ovar.get("alternateAllele"),
                        "gwas_effect_allele_frequency": osl.get("effectAlleleFrequencyFromSource"),
                        "gwas_finemapping_method": osl.get("finemappingMethod"),
                        "beta_ratio_sign_average": c.get("betaRatioSignAverage"),
                        "direction_note": direction_note(cs.get("beta"), osl.get("beta")),
                        "direction_caveat": DIRECTION_CAVEAT,
                    })

        bb_h4, bb_c, bb_cs = (best_brain if best_brain else (None, {}, {}))
        bb_osl = (bb_c.get("otherStudyLocus") or {}) if bb_c else {}
        bb_ostudy = bb_osl.get("study") or {}
        bb_study = (bb_cs.get("study") or {}) if bb_cs else {}
        bb_var = bb_osl.get("variant") or {}

        # Completeness of the colocalisation scan for this gene.  If it is not
        # 'complete', the h4/cognition columns are a LOWER BOUND, not a
        # measurement of absence.
        if coloc_errs:
            scan_status = f"incomplete:{len(coloc_errs)}_credible_sets_failed"
        elif n_fetched < n_expected:
            scan_status = f"incomplete:fetched_{n_fetched}_of_{n_expected}"
        else:
            scan_status = "complete"

        row.update({
            "coloc_scan_status": scan_status,
            "n_credible_sets_total": n_total,
            "n_credible_sets_gwas": n_gwas,
            "n_credible_sets_qtl": n_qtl,
            "n_credible_sets_brain_qtl": len(brain_cs),
            "n_colocalisations_total": n_expected,
            "n_colocalisations_fetched": n_fetched,
            "max_h4": max_h4, "max_h4_brain": max_h4_brain, "max_clpp": max_clpp,
            "n_coloc_h4_gt_0.8": n_h4_08,
            "n_brain_coloc_h4_gt_0.8": n_brain_h4_08,
            "best_brain_h4": bb_h4,
            "best_brain_clpp": bb_c.get("clpp") if bb_c else None,
            "best_brain_method": bb_c.get("colocalisationMethod") if bb_c else None,
            "best_brain_biosample": (bb_study.get("biosample") or {}).get("biosampleName"),
            "best_brain_qtl_study_type": bb_cs.get("studyType") if bb_cs else None,
            "best_brain_qtl_study_id": bb_study.get("id"),
            "best_brain_qtl_beta": bb_cs.get("beta") if bb_cs else None,
            "best_brain_other_study_id": bb_ostudy.get("id"),
            "best_brain_other_study_type": bb_c.get("rightStudyType") if bb_c else None,
            "best_brain_other_trait": bb_ostudy.get("traitFromSource"),
            "best_brain_other_pubmedId": bb_ostudy.get("pubmedId"),
            "best_brain_other_nSamples": bb_ostudy.get("nSamples"),
            "best_brain_other_beta": bb_osl.get("beta"),
            "best_brain_variant_id": bb_var.get("id"),
            "best_brain_variant_rsid": ";".join(bb_var.get("rsIds") or []),
            "best_brain_beta_ratio_sign_average": bb_c.get("betaRatioSignAverage") if bb_c else None,
            "best_brain_direction_note": direction_note(bb_cs.get("beta") if bb_cs else None,
                                                        bb_osl.get("beta")),
            "n_cognition_coloc": n_cog,
            "max_h4_cognition": max_h4_cog,
            "max_h4_cognition_brain": max_h4_cog_brain,
            "finemapping_methods_seen": ";".join(methods),
            "qtl_study_types_seen": ";".join(sts),
            "brain_biosamples_matched": ";".join(sorted(brain_names)),
            "n_distinct_biosamples": len(biosamples),
            "max_l2g_on_gene_credible_sets": max(l2g_scores) if l2g_scores else None,
            "coloc_pages_incomplete": len(coloc_errs),
            "coloc_error_detail": ";".join(sorted(set(coloc_errs.values())))[:300],
        })
        gene_rows.append(row)
        ckpt.write(json.dumps(row, default=str) + "\n"); ckpt.flush()
        if n % 10 == 0 or n == len(genes):
            print(f"[{n}/{len(genes)}] {symbol} cs={n_total} coloc={n_expected} "
                  f"cog={n_cog} ({round(time.time()-t0)}s, {_stats['http']} http)", flush=True)

    ckpt.close()

    # ---- write outputs -------------------------------------------------
    with open(OUT_CS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CS_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in gene_rows:
            w.writerow({k: r.get(k) for k in CS_FIELDS})

    cog_rows.sort(key=lambda r: (-(r["h4"] if r["h4"] is not None else -1)))
    with open(OUT_COG, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COG_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in cog_rows:
            w.writerow({k: r.get(k) for k in COG_FIELDS})

    with open(OUT_BIOS, "w", encoding="utf-8") as fh:
        fh.write("# AUDIT: exact biosample strings counted as brain/neural in this run.\n")
        fh.write("# Format: <count of QTL credible sets>\\t<biosampleName>\n\n")
        fh.write("## MATCHED AS BRAIN (curated allowlist)\n")
        for name, cnt in sorted(brain_biosamples_global.items(), key=lambda kv: -kv[1]):
            fh.write(f"{cnt}\t{name}\n")
        fh.write("\n\n## REVIEWED AND EXCLUDED (matched a brain keyword but is not CNS/neural)\n")
        for name, why in sorted(NONBRAIN_REVIEWED.items()):
            fh.write(f"-\t{name}\t# {why}\n")
        fh.write("\n\n## UNREVIEWED biosample names decided by the fallback regex\n")
        fh.write("## (empty = every biosample encountered was in the curated set)\n")
        for name, verdict in sorted(UNREVIEWED_BIOSAMPLES.items()):
            fh.write(f"{'BRAIN' if verdict else 'not-brain'}\t{name}\n")
        fh.write("\n\n## COGNITION GWAS TRAITS MATCHED (count\\ttrait)\n")
        for t, c in sorted(cog_traits_global.items(), key=lambda kv: -kv[1]):
            fh.write(f"{c}\t{t}\n")
        fh.write("\n\n## GWAS TRAITS SEEN BUT NOT COUNTED AS COGNITION (top 200 by frequency)\n")
        fh.write("## Provided so the recall of the cognition filter is auditable.\n")
        for t, c in sorted(noncog_traits_global.items(), key=lambda kv: -kv[1])[:200]:
            fh.write(f"{c}\t{t}\n")

    ok = sum(1 for r in gene_rows if r["query_status"] == "ok")
    nf = sum(1 for r in gene_rows if r["query_status"] == "ok:gene_not_found")
    er = sum(1 for r in gene_rows if str(r["query_status"]).startswith("error"))
    prov = {
        "endpoint": ENDPOINT, "method": "POST",
        "api_version": api_version, "data_version": data_version,
        "api_name": m["name"],
        "run_started_utc": started,
        "run_finished_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": IN_CSV, "genes_in_input": len(genes),
        "genes_ok": ok, "genes_not_found": nf, "genes_error": er,
        "genes_coloc_scan_complete": sum(1 for r in gene_rows
                                         if r.get("coloc_scan_status") == "complete"),
        "genes_coloc_scan_incomplete": sum(1 for r in gene_rows
                                           if str(r.get("coloc_scan_status", "")).startswith("incomplete")),
        "colocalisations_expected": sum(int(r.get("n_colocalisations_total") or 0) for r in gene_rows),
        "colocalisations_fetched": sum(int(r.get("n_colocalisations_fetched") or 0) for r in gene_rows),
        "workers": args.workers,
        "http_requests": _stats["http"], "cache_hits": _stats["cache_hits"],
        "retries": _stats["retries"], "bytes_downloaded": _stats["bytes"],
        "request_delay_s": REQUEST_DELAY, "max_retries": MAX_RETRIES,
        "cs_page_size": CS_PAGE_SIZE, "coloc_page_size": COLOC_PAGE_SIZE,
        "coloc_row_budget": COLOC_ROW_BUDGET, "max_aliases": MAX_ALIASES,
        "raw_cache_dir": CACHE_DIR,
        "queries": {"meta": Q_META, "gene_credible_sets": Q_GENE_CS,
                    "coloc_batch_template": COLOC_FRAGMENT,
                    "coloc_batch_example": build_coloc_query([("<studyLocusId>", 0, COLOC_PAGE_SIZE)])[0]},
        "brain_biosamples_allowlist": sorted(BRAIN_BIOSAMPLES),
        "brain_reviewed_exclusions": NONBRAIN_REVIEWED,
        "brain_fallback_patterns": BRAIN_PATTERNS,
        "brain_unreviewed_decisions": UNREVIEWED_BIOSAMPLES,
        "cognition_patterns": COGNITION_PATTERNS, "cognition_exclude": COGNITION_EXCLUDE,
        "notes": [
            "Target.credibleSets accepts only `page`; all study-type and tissue filtering is client-side.",
            "Target.credibleSets returns only molecular-QTL credible sets, never GWAS credible sets.",
            "No h0/h1/h2 fields exist on Colocalisation in this API version.",
            "query_status 'ok' with n_coloc=0 means measured zero; blank counts mean not measured.",
        ],
    }
    with open(OUT_PROV, "w", encoding="utf-8") as fh:
        json.dump(prov, fh, indent=2)

    print(f"\n[done] genes ok={ok} not_found={nf} error={er}")
    print(f"[done] {len(cog_rows)} cognition colocalisation rows")
    print(f"[done] http={_stats['http']} cache_hits={_stats['cache_hits']} "
          f"retries={_stats['retries']} bytes={_stats['bytes']}")
    print(f"[done] wrote:\n  {OUT_CS}\n  {OUT_COG}\n  {OUT_BIOS}\n  {OUT_PROV}")


if __name__ == "__main__":
    sys.exit(main())
