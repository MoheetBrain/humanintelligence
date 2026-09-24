#!/usr/bin/env python3
"""Sprint 5A — fetch the small open files of Zenodo record 12729266 (Wen et al. 2024 developing-brain xQTLs):
permutation (eGene-level) tables, the EUR/ALL variant .bim (A1 = effect allele, hg19) and READMEs.
Large nominal files are streamed + gene-filtered by devbrain_stream_filter.sh instead."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_util import ROOT, fetch  # noqa: E402

Z = "https://zenodo.org/api/records/12729266/files/{}/content"
DEST = ROOT / "data/interim/sprint5a/psychencode_dev"
FILES = ["README.md", "Variants_README.txt",
         "devBrain_eQTL_EUR_permutation_50HCP_FDR_0.05.txt.gz", "devBrain_eQTL_ALL_permutation_90HC_FDR_0.05.txt.gz",
         "devBrain_eQTL_AFR_permutation_25HCP_FDR_0.05.txt.gz", "devBrain_eQTL_AMR_permutation_15HCP_FDR_0.05.txt.gz",
         "trimester1_eQTL_EUR_permutation_FDR_0.05.txt", "trimester2_eQTL_EUR_permutation_FDR_0.05.txt",
         "devBrain_isoQTL_ALL_grouped_permutation_70HCP_FDR0.05.txt.gz",
         "Variants_for_EUR_xQTLmapping_A1effect_A2other.hg19.sorted.removeRel.bim.gz",
         "Variants_for_ALL_xQTLmapping_A1effect_A2other.hg19.sorted.removeRel.bim.gz"]
if __name__ == "__main__":
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(lambda f: fetch(Z.format(f), DEST / f, DEST / "download_log.jsonl"), FILES):
            print(r["status"], r["file"], r.get("bytes"))
