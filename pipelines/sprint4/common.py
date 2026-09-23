"""Shared paths, hashing and frozen-protocol access for Sprint 4.

Everything that decides a Sprint-4 verdict reads its thresholds from
``research/sprint4/frozen_hypotheses.json`` through :func:`load_frozen`, which refuses to
return if the file's sha256 differs from the hash recorded in ``research/sprint4/protocol.md``
at freeze time. A threshold therefore cannot drift after results have been seen without the
drift being visible in git and failing the test suite.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

CODEX = Path("/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01")
TOOLS = CODEX / "genetics_tools"
MAGMA_BIN = TOOLS / "bin" / "magma"
REF = TOOLS / "reference"
BFILE = REF / "g1000_eur"
GENE_ANNOT_10KB = REF / "annotations" / "genes_10kb.genes.annot"
SNP_EXCLUDE = REF / "position_mismatch_snps.txt"
DAVIES_INPUT = CODEX / "inputs" / "davies2018_open_complete.txt"
DAVIES_SHA256 = "01990c3e30661db518579d8f84dfddd7f79bc9b476e8a65b45d28c0489ca6573"
DAVIES_N = 282014

SETS_FILE = REPO_ROOT / "data" / "gene_tournament" / "pathway_sets" / "syngo.setannot"
COVARIATES = REPO_ROOT / "data" / "sprint4" / "gene_covariates.txt"
GENE_LOC = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "NCBI37.3.gene.loc"
GENE_MAP = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "gene_id_map.tsv"
DAVIES_GENES_OUT = REPO_ROOT / "data" / "raw" / "magma_x01" / "2026-09-22" / "davies2018_10kb.genes.out"
LD_LOCI = REPO_ROOT / "data" / "gene_tournament" / "ld_loci.parquet"

PROTOCOL_MD = REPO_ROOT / "research" / "sprint4" / "protocol.md"
FROZEN_JSON = REPO_ROOT / "research" / "sprint4" / "frozen_hypotheses.json"
OUT = REPO_ROOT / "reports" / "sprint4"
DATA = REPO_ROOT / "data" / "sprint4"
RAW = REPO_ROOT / "data" / "raw" / "sprint4"
WORK = REPO_ROOT / "data" / "interim" / "sprint4"

R_ENV = Path("/opt/homebrew/Caskroom/miniforge/base/envs/hi-sprint4")
RSCRIPT = R_ENV / "bin" / "Rscript"
TABIX = R_ENV / "bin" / "tabix"

FROZEN_SETS = ("GO_0042734", "GO_0099560", "GO_0099056", "GO_0099508", "GO_0045202", "SYNGO_synprocess")


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def gene_list_hash(genes) -> str:
    """Order-free hash of a gene set: sorted Entrez ids, one per line, trailing newline."""
    ids = sorted({int(g) for g in genes})
    return sha256_text("\n".join(str(i) for i in ids) + "\n")


def read_setannot(path: Path = SETS_FILE) -> dict[str, list[int]]:
    sets: dict[str, list[int]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if parts:
            sets[parts[0]] = [int(g) for g in parts[1:]]
    return sets


def recorded_frozen_hash() -> str:
    """The sha256 of frozen_hypotheses.json as written into protocol.md at freeze time."""
    text = PROTOCOL_MD.read_text(encoding="utf-8")
    # Amendments append a new line; the LAST one is authoritative, earlier ones stay as history.
    found = re.findall(r"FROZEN_JSON_SHA256:\s*`?([0-9a-f]{64})`?", text)
    if not found:
        raise RuntimeError("protocol.md carries no FROZEN_JSON_SHA256 line")
    return found[-1]


def load_frozen(verify: bool = True) -> dict:
    if verify:
        actual = sha256_file(FROZEN_JSON)
        expected = recorded_frozen_hash()
        if actual != expected:
            raise RuntimeError(
                f"frozen_hypotheses.json has changed since the freeze (sha256 {actual} != "
                f"recorded {expected}). Thresholds may not be edited after results are seen; "
                "record an amendment instead.")
    return json.loads(FROZEN_JSON.read_text(encoding="utf-8"))


def utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_head() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # pragma: no cover - git absent
        return "unknown"
