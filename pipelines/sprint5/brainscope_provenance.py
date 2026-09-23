#!/usr/bin/env python3
"""Write data/raw/sprint5/brainscope/PROVENANCE.json and data/sprint5/brainscope_datasets.csv.

Combines (i) every download record in data/interim/sprint5/brainscope/download_log.jsonl, (ii) facts verified
from the primary paper / supplement / portal / code (with source URLs), (iii) per-cell-type sample sizes and
cohort composition computed from the public QTL covariate files, and (iv) access blockers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brainscope_data as BD  # noqa: E402
import common as C  # noqa: E402

OUT_DIR = C.RAW / "brainscope"
PORTAL = "https://brainscope.gersteinlab.org"
SRC = {
    "paper": "https://doi.org/10.1126/science.adi5199 (Emani PS et al., Science 384:eadi5199, 2024; PMID 38781369; "
             "PMC11365579 full text read via NCBI efetch)",
    "preprint": "https://doi.org/10.1101/2024.03.18.585576 (PMC10983939)",
    "supplement": "https://www.biorxiv.org/content/biorxiv/early/2024/03/19/2024.03.18.585576/DC1/embed/media-1.pdf "
                  "(bioRxiv v1 supplementary materials; sections 1 'Genotype QC and imputation', 4.1 'scQTLs', "
                  "4.5 isoQTLs, 5 GRNs)",
    "portal_outputs": f"{PORTAL}/integrative_files.html",
    "portal_sigqtl": f"{PORTAL}/output-sig-eQTL.html",
    "portal_raw": f"{PORTAL}/raw_data_files.html",
    "code_scqtl": f"{PORTAL}/code/core_scqtl_processing_code.tar.gz",
    "github": "https://github.com/gersteinlab/PsychENCODE_SingleCell_Integrative (scQTL Pipeline/README.md; "
              "LICENSE = 'MIT License for Academic Use')",
    "sample_metadata": f"{PORTAL}/data/sample_metadata/PEC2_sample_metadata.txt",
    "covariates": f"{PORTAL}/data/qtl_covariates/",
}


def load_log() -> list[dict]:
    recs = [json.loads(line) for line in (BD.BS / "download_log.jsonl").read_text().splitlines() if line.strip()]
    last: dict[str, dict] = {}
    for r in recs:  # keep the latest OK record per file
        if r.get("status") == "OK" or r["file"] not in last:
            last[r["file"]] = r
    return list(last.values())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    recs = load_log()
    meta = pd.read_csv(BD.BS / "PEC2_sample_metadata.txt", sep="\t")
    cov = {ct: BD.covariates(ct) for ct in BD.ALL_CT}
    union = sorted({s for ct in BD.SIG_CT for s in cov[ct]["sample_ids"]})
    union_cohort = {}
    for ct in BD.SIG_CT:
        pass
    # cohort of each QTL sample from the covariate indicator rows
    samp_cohort: dict[str, str] = {}
    for ct in BD.ALL_CT:
        pcs = BD.COV_PCS.get(ct, 100)
        d = pd.read_csv(BD.BS / "qtl_covariates" / f"{ct}.cov.{pcs}_expr_PCs.bed", sep="\t", index_col=0)
        rows = [r for r in d.index if r.startswith("cohort")]
        num = d.loc[rows].apply(pd.to_numeric, errors="coerce")
        for s in d.columns:
            flagged = [r.replace("cohort_is_", "").replace("cohort_", "") for r in rows if num.loc[r, s] == 1]
            samp_cohort.setdefault(s, flagged[0] if len(flagged) == 1 else ("MULTIPLE" if flagged else "REFERENCE_LEVEL"))
    for s in union:
        union_cohort[samp_cohort.get(s, "NA")] = union_cohort.get(samp_cohort.get(s, "NA"), 0) + 1
    pb = {}
    for r in recs:
        if r["file"].startswith("pseudobulk_genes/"):
            pb[r["file"].split("/")[1].replace(".genes.tsv", "")] = r
    egenes = BD.egenes()
    facts = {
        "study": "brainSCOPE (PsychENCODE Consortium phase II integrative analysis)",
        "citation": "Emani PS, Liu JJ, Clarke D, et al. Single-cell genomics and regulatory networks for 388 human "
                    "brains. Science 384, eadi5199 (2024). doi:10.1126/science.adi5199",
        "tissue": "adult dorsolateral prefrontal cortex (DLPFC), post-mortem; all samples >= 13 years (supp. §1)",
        "n_individuals_resource": 388,
        "n_individuals_genotyped": 383,
        "n_individuals_in_any_core_scQTL_celltype": len(union),
        "core_scQTL_union_by_cohort_indicator": union_cohort,
        "diagnoses": "182 controls + schizophrenia, bipolar disorder, ASD, Alzheimer's disease, PTSD and others "
                     "(diagnosis is a QTL covariate)",
        "cohorts_12": {"PsychENCODE (8)": ["CMC", "UCLA-ASD", "SZBDMulti-Seq", "MultiomeBrain", "DevBrain", "IsoHuB",
                                           "PTSDBrainomics", "LIBD"],
                       "external (4)": ["ROSMAP (AMP-AD)", "Ma-Sestan", "Velmeshev", "Girgenti-snMultiome"]},
        "sample_metadata_cohort_counts": meta.Cohort.value_counts().to_dict(),
        "sample_metadata_ancestry_counts": meta["1000G_ancestry"].value_counts().to_dict(),
        "sample_metadata_cmc_id_prefix": "all 100 CMC individuals carry CMC_MSSM_* IDs (Mount Sinai brain bank)",
        "genome_build": "GRCh38/hg38 (genotypes lifted to hg38, REF fixed to hg38 with plink2; supp. §1). Verified "
                        "empirically: 108,485 brainSCOPE core pairs match eQTL Catalogue GRCh38 chr:pos:REF:ALT with "
                        "99.99% sign concordance (data/sprint5/brainscope_allele_check.json)",
        "genotypes": "SNP array / WES / WGS / snRNA-derived calls, merged, TOPMed imputation server (Minimac4, Eagle "
                     "2.4, R2>0.3); post-imputation MAF>=0.05 and present in all samples: 1.95M SNPs, 383 samples "
                     "(supp. §1). Public candidate SNP lists contain 1,953,861 IDs per cell type (L6b).",
        "gene_annotation": "NOT STATED for the scQTL gene coordinates. Genes are identified by SYMBOL only; TSS from a "
                           "'genes.gtf' (build_gene_info_file.py). snRNA counts from CellRanger v6.0 (supp. §2); the "
                           "10x reference/GENCODE release used is not given in the supplement text searched. GENCODE "
                           "43 is cited only for conservation annotations. Treat symbol matching as approximate.",
        "expression_unit": "pseudobulk mean UMI per individual & cell type (>50 nuclei of that type, >300 nuclei total), "
                           "log2(CPM+1), genes with >10% non-zero samples; QTLtools --normal (rank-normal) phenotype",
        "scQTL_method": "QTLtools cis, 1 Mb up/downstream of TSS; covariates sex, age, diagnosis, cohort, 5 genotype "
                        "PCs, 100 expression PCs (20 for small cell types); 10,000 permutations; beta-approximated "
                        "gene p; Storey q<=0.05 per cell type; per-gene nominal threshold F^-1(pt) (GTEx scheme).",
        "significance_scope": "SIGNIFICANT PAIRS ONLY are public (eGene q<=0.05 and pair nominal p <= gene threshold). "
                              "No full nominal (all tested pairs) summary statistics are published on the portal; the "
                              "supplement and portal list none. Tested SNP lists and pseudobulk matrices ARE public, so "
                              "'tested' status is known; genotypes are controlled-access, so full statistics cannot be "
                              "regenerated.",
        "effect_allele": "slope per copy of the ALT allele of variant ID chr:pos:REF:ALT (hg38). Basis: QTLtools uses VCF "
                         "ALT dosage; empirically 99.99% sign concordance with eQTL Catalogue (ALT-coded) bulk brain "
                         "eQTLs for 5,602 unique gene-variant pairs.",
        "cell_types": {"core_callsets_17": BD.SIG_CT,
                       "no_published_core_callset_7": BD.NOCALL_CT,
                       "why_7_missing": "covariate files show residual df <= 21 (Endo__VLMC 3, Sncg 21) or negative "
                                        "(Immune, L5.ET, L6.IT.Car3, Pax6, SMC); the paper reports core scQTLs for 17 "
                                        "cell types. These are NOT 'tested, no eQTL'.",
                       "aggregated_classes": ["excitatory", "inhibitory", "non_neuronal"]},
        "per_celltype_n": {ct: {"n_individuals": cov[ct]["n"], "n_expr_pcs": cov[ct]["n_expr_pcs"],
                                "residual_df_used_for_SE": cov[ct]["df_resid"],
                                "cohort_counts": {k: v for k, v in cov[ct]["cohort_counts"].items() if v},
                                "n_genes_tested": pb.get(ct, {}).get("n_genes"),
                                "n_samples_in_pseudobulk_matrix": pb.get(ct, {}).get("n_samples_in_matrix"),
                                "n_eGenes": len(egenes.get(ct, [])) if ct in egenes else None}
                           for ct in BD.ALL_CT},
        "qtl_types_public": {
            "cell-type eQTL (core, QTLtools)": "17 cell types, significant pairs",
            "cell-type eQTL (LD-pruned genotypes)": "17 cell types, significant pairs",
            "cell-class eQTL (aggregated excitatory/inhibitory/non-neuronal)": "VERIFIED NOT A SEPARATE ANALYSIS: "
                "sorted contents are byte-identical to concatenations of the per-cell-type core files (excitatory = 7 "
                "excitatory types; inhibitory = 5 inhibitory types; non_neuronal = Astro+OPC+Oligo+Micro.PVM); "
                "excluded from the lookup",
            "conditional eQTL": "top variant per independent signal, 17 cell types",
            "Bayesian LMM scQTL": "24 cell types; posterior mean + SD; significant only",
            "dynamic eQTL (pseudotime, excitatory)": "not used here",
            "isoform-usage QTL (sQTLseekeR2)": "22 cell types; isoGenes with beta p<0.05 (unfiltered for FDR; only 21 "
                                               "isoGenes at FDR<0.05 per paper); unsigned; TSS +/-5 kb window",
            "caQTL": "NONE published (no chromatin-accessibility QTLs in brainSCOPE)",
            "sQTL (leafcutter-style splicing)": "NONE published; isoform-usage QTLs are the closest analogue",
        },
        "regulatory_annotations_public": {
            "scCRE peaks": "snATAC/snMultiome peak calls for 7 classes (Astro, Endo, Exc, Inh, Micro, OPC, Oligo) + "
                           "union; hg38 BED",
            "GRNs": "23 cell-type TF-enhancer-promoter-target gene networks (SCENIC + scGRNom + snATAC links); "
                    "enhancer->target gene links used as enhancer-gene links",
            "eQTL_edge": "scQTLs overlapping GRN enhancer/promoter elements, 24 GRN cell types",
        },
        "licence_terms": "Portal states output files are 'fully open source'; files are served without login or "
                         "click-through. No explicit data licence found. Code: MIT License for Academic Use (commercial "
                         "use: contact M. Gerstein).",
        "overlap_with_project_bulk_eqtl": {
            "CommonMind (eQTL Catalogue QTD000075, n=586 DLPFC)": "LIKELY OVERLAP: brainSCOPE CMC cohort = 100 "
                "CMC_MSSM_* donors (the core scQTL covariates flag 25-93 CMC samples per cell type); CommonMind bulk "
                "DLPFC eQTLs include MSSM donors. Individual-level overlap cannot be confirmed without controlled IDs.",
            "ROSMAP (eQTL Catalogue ROSMAP brain_naive)": "LIKELY OVERLAP: brainSCOPE includes 46 ROSMAP individuals "
                "(ROS*/MAP* IDs; 1-43 per cell type in QTL covariates).",
            "GTEx": "NO OVERLAP expected: no GTEx cohort in brainSCOPE.",
            "SZBDMulti-Seq": "72 donors (24 control / 24 schizophrenia / 24 bipolar; 'SZBD-Kellis', supp. §4.3). "
                             "Brain bank not stated in the supplement; the design resembles the McLean (HBTRC) "
                             "cohort of Ruzicka et al. 2024 (PMID 38781388), so overlap with CommonMind MSSM donors "
                             "is judged unlikely but is UNVERIFIED.",
            "LIBD": "10 LIBD donors (Br* IDs) - LIBD/BrainSeq bulk data are not among the project's bulk eQTL "
                    "sources (BrainSeq is NON_ADULT-labelled in the Sprint-4 eQTL Catalogue table).",
            "consequence": "agreement between brainSCOPE and CommonMind/ROSMAP bulk directions is not independent "
                           "replication.",
        },
        "sources": SRC,
    }
    blockers = [
        {"item": "individual imputed genotypes (VCF) for PsychENCODE cohorts",
         "url": "https://www.synapse.org/#!Synapse:syn51111084 (PEC Capstone II; doi:10.7303/SYN51111084.1)",
         "needs": "Synapse account + PsychENCODE controlled-access approval (data use certificate)",
         "impact": "full per-variant scQTL statistics (needed for coloc.abf / coloc.susie) cannot be regenerated"},
        {"item": "ROSMAP raw data, genotypes and single-cell matrices",
         "url": "https://adknowledgeportal.synapse.org (syn53479857; doi:10.7303/SYN53479857.1)",
         "needs": "Synapse account + AD Knowledge Portal data use agreement", "impact": "as above"},
        {"item": "raw FASTQ (snRNA-seq, snATAC-seq, snMultiome)", "url": f"{PORTAL}/raw_data_files.html",
         "needs": "Synapse controlled access", "impact": "not needed for this analysis"},
        {"item": "full nominal scQTL summary statistics (all tested pairs)",
         "url": "not published on brainscope.gersteinlab.org; no public location found (portal, supplement, GitHub)",
         "needs": "would require request to authors or re-analysis with controlled genotypes",
         "impact": "colocalisation NOT_TESTABLE; only lead-variant lookup + LD proxies possible"},
    ]
    prov = {"created_utc": C.utc_now(), "script": "pipelines/sprint5/brainscope_provenance.py",
            "download_dir": str(BD.BS.relative_to(C.REPO_ROOT)) + " (gitignored)",
            "downloads": recs,
            "n_downloads_ok": sum(r.get("status") == "OK" for r in recs),
            "total_bytes_stored": int(sum(r.get("bytes", 0) for r in recs if r.get("status") == "OK")),
            "total_source_bytes_streamed_not_stored": int(sum(r.get("source_bytes", 0) for r in recs)),
            "documents_fetched_for_verification": [
                {"url": "https://www.biorxiv.org/content/biorxiv/early/2024/03/19/2024.03.18.585576/DC1/embed/media-1.pdf",
                 "file": "emani_biorxiv_supp_media1.pdf", "sha256": C.sha256_file(BD.BS / "emani_biorxiv_supp_media1.pdf")
                 if (BD.BS / "emani_biorxiv_supp_media1.pdf").exists() else None},
                {"url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC11365579&rettype=xml",
                 "file": "PMC11365579.xml", "sha256": C.sha256_file(BD.BS / "PMC11365579.xml")
                 if (BD.BS / "PMC11365579.xml").exists() else None}],
            "verified_facts": facts, "access_blockers": blockers}
    (OUT_DIR / "PROVENANCE.json").write_text(json.dumps(prov, indent=2, default=str))

    # ---------------------------------------------------------------- datasets table
    rows = []
    byfile = {r["file"]: r for r in recs}

    def add(did, qtype, ct, rel, scope, eff, notes, access="PUBLIC", n=None, assay="snRNA-seq pseudobulk (10x)"):
        r = byfile.get(rel, {})
        rows.append({"dataset_id": did, "qtl_type": qtype, "cell_type": ct, "cell_class": BD.CELL_CLASS.get(ct, "NA"),
                     "n_individuals": n if n is not None else (cov[ct]["n"] if ct in cov else None),
                     "genome_build": "GRCh38", "gene_annotation": "gene symbols; release not stated (CellRanger v6.0)",
                     "assay": assay, "significance_scope": scope, "effect_allele_definition": eff,
                     "url": r.get("url"), "sha256": r.get("sha256"), "bytes": r.get("bytes"),
                     "access": access if r.get("status", "OK") == "OK" else "FAILED", "notes": notes})
    ALT = "ALT allele of chr:pos:REF:ALT (hg38); slope per ALT copy (verified vs eQTL Catalogue)"
    for ct in BD.SIG_CT:
        add(f"brainscope_core_{ct}", "cell-type eQTL (core)", ct, "sig_QTLs.zip",
            f"significant pairs only (q<=0.05 eGenes; {len(egenes[ct])} eGenes)", ALT,
            f"inside sig_QTLs.zip; tested SNP list candidate_SNPs/{ct}.SNPs.dat.gz; pseudobulk genes streamed")
        add(f"brainscope_ldpruned_{ct}", "cell-type eQTL (LD-pruned genotypes)", ct,
            f"sig_QTLs_LD_pruned/{ct}_sig_QTLs.dat", "significant pairs only", ALT, "alternative callset")
        add(f"brainscope_conditional_top_{ct}", "cell-type eQTL conditional top variants", ct,
            f"conditional_top_hits/conditional_top_variants_per_signal_{ct}.txt", "top variant per signal", ALT, "")
    for ct in BD.ALL_CT:
        add(f"brainscope_tested_snps_{ct}", "tested variant list", ct, f"candidate_SNPs/{ct}.SNPs.dat.gz",
            "all tested variant IDs", "n/a", "used to decide 'variant tested'")
        add(f"brainscope_covariates_{ct}", "QTL covariates", ct, f"qtl_covariates/{ct}.cov.{BD.COV_PCS.get(ct, 100)}_expr_PCs.bed",
            "n/a", "n/a", "N and cohort composition per cell type; residual df for derived SE")
        r = pb.get(ct)
        rows.append({"dataset_id": f"brainscope_pseudobulk_genes_{ct}", "qtl_type": "tested gene list", "cell_type": ct,
                     "cell_class": BD.CELL_CLASS.get(ct), "n_individuals": r.get("n_samples_in_matrix") if r else None,
                     "genome_build": "GRCh38", "gene_annotation": "gene symbols; TSS coordinates",
                     "assay": "snRNA-seq pseudobulk", "significance_scope": "n/a", "effect_allele_definition": "n/a",
                     "url": r.get("url") if r else None, "sha256": r.get("sha256") if r else None,
                     "bytes": r.get("bytes") if r else None, "access": "PUBLIC" if r else "NOT_DOWNLOADED",
                     "notes": ("STREAMED; stored file is the REDUCED gene-coordinate table; source sha256 "
                               f"{r.get('source_sha256')} ({r.get('source_bytes')} bytes)") if r else ""})
        if ct in BD.NOCALL_CT:
            rows.append({"dataset_id": f"brainscope_core_{ct}", "qtl_type": "cell-type eQTL (core)", "cell_type": ct,
                         "cell_class": BD.CELL_CLASS.get(ct), "n_individuals": cov[ct]["n"], "genome_build": "GRCh38",
                         "gene_annotation": "", "assay": "snRNA-seq pseudobulk", "significance_scope":
                             "NO PUBLISHED CALLSET", "effect_allele_definition": "", "url": None, "sha256": None,
                         "bytes": None, "access": "NOT_PUBLISHED",
                         "notes": f"residual df {cov[ct]['df_resid']} with {cov[ct]['n_expr_pcs']} expression PCs; "
                                  "no core scQTLs reported; not 'tested-null'"})
    for ct, fn in BD.AGG_CT.items():
        add(f"brainscope_aggregated_{ct}", "cell-class eQTL (aggregated)", ct, f"aggregated_qtl/{fn}",
            "significant pairs only", ALT, "DUPLICATE of core files: sorted content byte-identical to the "
            "concatenation of the per-cell-type core callsets of this class; excluded from analysis", n=None)
    add("brainscope_bayesian_all", "Bayesian LMM scQTL", "24 cell types", "bayesian_scQTLs.dat",
        "significant only (posterior)", ALT + " (posterior mean)", "no p-values; posterior SD", n=None)
    for p in sorted((BD.BS / "isoqtls").glob("*.txt")):
        ct = p.name.replace("_significant_sCQTLs_p0.05.txt", "")
        add(f"brainscope_isoqtl_{ct}", "isoform-usage QTL (sQTLseekeR2)", ct, f"isoqtls/{p.name}",
            "isoGenes with permuted beta p<0.05 (not FDR filtered)", "unsigned (no allelic direction)",
            "TSS +/-5 kb window", n=None)
    for p in sorted((BD.BS / "eQTL_edge").glob("*.txt")):
        ct = p.name.replace(".eqtl_edge.txt", "")
        add(f"brainscope_eqtl_edge_{ct}", "scQTL x GRN enhancer/promoter overlap", ct, f"eQTL_edge/{p.name}",
            "n/a", "n/a", "", n=None, assay="snATAC + snRNA GRN")
    for p in sorted((BD.BS / "GRNs").glob("*_GRN.txt")):
        ct = p.name.replace("_GRN.txt", "")
        add(f"brainscope_grn_{ct}", "enhancer-gene links (GRN)", ct, f"GRNs/{p.name}", "n/a", "n/a",
            "TF-enhancer-promoter-target edges", n=None, assay="snATAC + snRNA GRN")
    add("brainscope_scCRE_peaks", "scATAC peaks (scCREs)", "7 classes + union", "scCRE.PeakCalls.zip", "n/a", "n/a",
        "", n=None, assay="snATAC-seq / snMultiome")
    add("brainscope_sample_metadata", "metadata", "all", "PEC2_sample_metadata.txt", "n/a", "n/a",
        "388 individuals, cohort/ancestry/diagnosis", n=388, assay="metadata")
    for b in blockers:
        rows.append({"dataset_id": "BLOCKED_" + b["item"].split(" (")[0].replace(" ", "_")[:60], "qtl_type": "blocked",
                     "cell_type": "all", "cell_class": "NA", "n_individuals": None, "genome_build": "GRCh38",
                     "gene_annotation": "", "assay": "", "significance_scope": "", "effect_allele_definition": "",
                     "url": b["url"], "sha256": None, "bytes": None, "access": "BLOCKED",
                     "notes": f"needs: {b['needs']}; impact: {b['impact']}"})
    pd.DataFrame(rows).to_csv(C.DATA / "brainscope_datasets.csv", index=False)
    print("PROVENANCE.json and brainscope_datasets.csv written;", len(rows), "dataset rows")


if __name__ == "__main__":
    main()
