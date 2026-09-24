#!/usr/bin/env python3
"""Sprint 5A (agent A) — write committed PROVENANCE.json files for every download made by the agent-A pipelines
(brainSCOPE gap-fill, devBrain / PsychENCODE developmental, GTEx V11, GENCODE). Each file lists URL, UTC timestamp,
bytes and sha256 as recorded at download time (the raw files live under gitignored data/interim/sprint5a/)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I = ROOT / "data/interim/sprint5a"


def log(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(dest: Path, obj: dict) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(obj, indent=2, default=str))
    print("wrote", dest.relative_to(ROOT))


def main() -> None:
    rev = json.loads((I / "brainscope/sprint5_reverify.json").read_text())
    from collections import Counter
    write(ROOT / "data/raw/sprint5a/brainscope/PROVENANCE.json", {
        "created_utc": now(),
        "scripts": ["pipelines/sprint5a/brainscope_gapfill_fetch.py", "pipelines/sprint5a/brainscope_typed_evidence.py"],
        "source": "PsychENCODE brainSCOPE portal https://brainscope.gersteinlab.org/data/ (Emani et al., Science 2024; "
                  "PMID 38781369). Open Apache directory listing, no login / terms click-through.",
        "download_dir": "data/interim/sprint5a/brainscope (gitignored)",
        "availability_recheck_utc": "2026-09-24T08:36Z (directory listings of /data/ and sub-directories)",
        "requested_items": {
            "PEC2_sample_metadata.txt": "PUBLIC - already downloaded in Sprint 5 (sha256 re-verified MATCH)",
            "[ct]_sig_QTLs.dat": "PUBLIC - Sprint 5 (sig_QTLs.zip, 17 cell types; re-verified)",
            "[ct]_sig_eGenes.dat": "PUBLIC - Sprint 5 (sig_eGenes.zip; re-verified)",
            "[ct].SNPs.dat.gz": "PUBLIC - Sprint 5 (candidate_SNPs_for_QTL_calls, 24 cell types; re-verified)",
            "conditional.[ct].txt": "PUBLIC - NEWLY downloaded here (17 cell types, 230 MB)",
            "conditional_top_variants_per_signal_[ct].txt": "PUBLIC - Sprint 5 (re-verified)",
            "bayesian_scQTLs.dat": "PUBLIC - Sprint 5 (re-verified)",
            "metaQTLs.txt": "PUBLIC - NEWLY downloaded here (/data/meta_qtls/, 208 MB)",
            "adult_bcCREs.bed": "PUBLIC - NEWLY downloaded here (/data/bcCRE/, 253,638 b-cCREs, hg38)",
            "cell-type scCRE peak calls": "PUBLIC - Sprint 5 (scCRE.PeakCalls.zip = the 8 /data/atac_peaks/*.bed files; re-verified)",
            "[ct]_GRN.txt": "PUBLIC - Sprint 5 (/data/GRNs/, 23 cell types; re-verified)",
            "[ct].eqtl_edge.txt": "PUBLIC - Sprint 5 (/data/eQTL_edge/, 24 cell types; re-verified)",
            "crispr_validation_results.xlsx": "PUBLIC - NEWLY downloaded here (/data/validation/; 4 enhancer KOs: NGEF, RORB, PLEKHO1, TOM1L2; enhancers given as ENCODE EH37E IDs without coordinates)",
            "starrseq_enhancers_merged.bed": "PUBLIC - NEWLY downloaded here (supplementary annotation)",
            "snrna_expr_matrices.zip (7.8 GB)": "PUBLIC but deliberately NOT downloaded (instruction)",
        },
        "sprint5_file_reverification": {"counts": dict(Counter(r["verify"] for r in rev["records"])),
                                        "utc": rev["utc"],
                                        "note": "REDUCED_FILE_SKIPPED = pseudobulk gene lists stored in reduced form in Sprint 5"},
        "downloads": log(I / "brainscope/download_log.jsonl"),
        "auxiliary_downloads": {
            "ucsc_liftover_chain": log(I / "liftover/download_log.jsonl"),
            "note": "hg38->hg19 point liftover used to map brainSCOPE signal variants and query variants to 1000G EUR "
                    "(GRCh37) PLINK IDs by position + allele set, because Ensembl REST overlap calls were timing out "
                    "(>30 s per call, 2026-09-24 ~09:45 UTC). Validated: 1351/1354 query variants lift to their recorded "
                    "GRCh37 position."},
        "post_reboot_reverification": {
            "script": "pipelines/sprint5a/verify_agentA_downloads.py -> data/interim/sprint5a/agentA_reverify.json",
            "result": dict(Counter(r["verify"] for r in json.loads((I / "agentA_reverify.json").read_text()))),
            "note": "machine rebooted mid-run (~10:00 UTC); all completed downloads re-hashed; the interrupted "
                    "devBrain Tri1 filter output was deleted and regenerated from the md5-verified full file; Tri2 "
                    "was re-downloaded from scratch"},
        "blockers": [
            {"item": "full nominal scQTL statistics (all tested variant-gene pairs)",
             "status": "NOT PUBLISHED anywhere public (portal, supplement, GitHub)",
             "needed_for": "coloc.abf / coloc.susie", "user_action": "request from the brainSCOPE authors, or apply for "
             "controlled genotypes (Synapse syn51111084 PsychENCODE Data Use Certificate; AD Knowledge Portal "
             "syn53479857 for ROSMAP) and re-run QTLtools", "requires_PI_approval_or_secure_compute": True},
        ],
    })
    dev = log(I / "psychencode_dev/download_log.jsonl")
    write(ROOT / "data/raw/sprint5a/psychencode_dev/PROVENANCE.json", {
        "created_utc": now(),
        "scripts": ["pipelines/sprint5a/devbrain_fetch_small.py", "pipelines/sprint5a/devbrain_parallel_fetch.py",
                    "pipelines/sprint5a/devbrain_timing.py"],
        "source": "Wen C. et al. 'Cross-ancestry atlas of gene, isoform, and splicing regulation in the developing human "
                  "brain', Science 384:eadh0829 (2024), PMID 38781368, PMC12147038. Zenodo record 12729266 "
                  "('devBrain_xQTL_sumstats_part1', CC-BY-4.0, published 2024-07-11), open, no login.",
        "dataset_facts": {
            "samples": "672 unique developing neocortex samples, 654 with genotype+RNA after QC, 4-39 PCW "
                       "(Tri1 N=216, Tri2 N=433 across ancestries); EUR N=292, AMR 164, AFR 145, SEA 29, EA 24",
            "trimester_eQTL": "EUR only: Tri1 (4-13 PCW) N=143, Tri2 (14-26 PCW) N=145; Tri3 N=4 not analysed",
            "build": "hg19 / GRCh37 (variant .bim files, 'BP_hg19'); RNA aligned to GRCh37 with GENCODE v29lift37 "
                     "(paper Methods); GitHub README states Salmon index GENCODE v33lift37",
            "method": "FastQTL, 1 Mb cis window, covariates sex, age, 5 genotype PCs, HCP factors; eGene = beta-approx "
                      "permutation q < 0.05",
            "effect_allele": "A1 of Variants_for_<anc>_xQTLmapping_A1effect_A2other.hg19...bim.gz (README)",
            "nominal_files": "FULL cis nominal statistics (all tested pairs; p up to 1.0 verified in the first 400 kB "
                             "of each file) despite 'FDR_0.05' in the file names",
        },
        "downloads": dev,
        "stored_policy": "Nominal files (2-4 GB each) were downloaded in parallel byte ranges, md5-verified against "
                         "Zenodo, hashed (sha256), filtered to the 249 query Ensembl gene IDs, then deleted.",
        "resources_reviewed_not_downloaded": [
            {"resource": "devBrain isoQTL nominal (ALL 16.2 GB, AFR 15.1 GB)", "status": "OPEN (Zenodo)", "reason":
             "size; gene-level eQTL answers the timing question; isoQTL grouped-permutation table downloaded"},
            {"resource": "devBrain sQTL summary statistics", "status": "NOT in Zenodo part 1; listed on Galaxy history "
             "usegalaxy.org/u/cindywen/h/devbrainsumstats and Synapse syn50897018 (sign-in required)",
             "user_action": "Synapse: create account + accept terms (not done by agent); Galaxy public history not probed further"},
            {"resource": "devBrainHub portal API (devbrainhub.gandallab.org/api/devmeta/{eqtl,isoqtl,sqtl}/extra/<gene>)",
             "status": "OPEN, per-gene JSON (full cis table: beta, -log10 p, rsID, hg19 pos_ref_alt)",
             "use": "not used for inference (analysis/ancestry set behind 'devmeta' undocumented); Zenodo files used"},
            {"resource": "Synapse syn50897018 (PsychENCODE devBrain xQTL)", "status": "CONTROLLED (Synapse sign-in)",
             "user_action": "Synapse account + PsychENCODE data-use terms; PI approval may be required"},
            {"resource": "BrainSpan / PsychENCODE Phase-I developmental (Li 2018) eQTLs", "status": "not re-acquired",
             "reason": "BrainSeq (prenatal-85 y) and Walker 2019 fetal already analysed in Sprint 5 via eQTL Catalogue r7"},
        ],
        "independence_note": "Walker 2019 fetal neocortex (Sprint 5, eQTL Catalogue QTD) samples are a SUBSET of the "
                             "devBrain meta-dataset; the two are not independent replications.",
    })
    gt = log(I / "gtex_v11/download_log.jsonl")
    write(ROOT / "data/raw/sprint5a/gtex_v11/PROVENANCE.json", {
        "created_utc": now(), "scripts": ["pipelines/sprint5a/gtex_v11_fetch.py", "pipelines/sprint5a/gtex_v11_lookup.py"],
        "source": "GTEx Analysis V11 (open access; GCS bucket gs://adult-gtex, objects created 2026-01-15; "
                  "GENCODE v47; same donors/samples as V10). Tar members fetched by HTTP byte range (brain tissues only).",
        "downloads": gt,
        "blockers": [{"item": "V11 all-pairs (nominal) eQTL/sQTL/apaQTL statistics",
                      "status": "REQUESTER-PAYS bucket gs://gtex-resources (per GTEx description.tsv)",
                      "user_action": "Google Cloud account with billing enabled (egress charges); not a controlled-access "
                                     "approval, but requires the user to create/attach billing - not done by agent",
                      "requires_PI_approval_or_secure_compute": False},
                     {"item": "individual-level V11 genotypes/expression", "status": "CONTROLLED (dbGaP phs000424 / AnVIL)",
                      "requires_PI_approval_or_secure_compute": True}],
    })
    write(ROOT / "data/raw/sprint5a/gencode/PROVENANCE.json", {
        "created_utc": now(), "scripts": ["pipelines/sprint5a/gencode_fetch.py", "pipelines/sprint5a/gencode_id_map.py"],
        "source": "GENCODE human gene annotation GTFs, EBI FTP (open)", "downloads": log(I / "gencode/download_log.jsonl"),
    })


if __name__ == "__main__":
    main()
