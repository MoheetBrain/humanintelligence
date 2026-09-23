#!/usr/bin/env python3
"""Sprint 4, step 1 — freeze the primary hypothesis before any new result is loaded.

Writes ``research/sprint4/frozen_hypotheses.json`` from Sprint-3 artefacts only:

* the six gene sets that survived the conditioned global-FDR MAGMA analysis, with their
  exact Entrez membership and an order-free sha256 per set;
* the 159 independent Sprint-3 loci (LD blocks at |r|>=0.2 holding a Bonferroni gene) with a
  lead SNP chosen from Davies 2018 by a rule fixed here;
* every threshold and classification rule used by Gates A, B and C and by the decision;
* sha256 of every input file the analyses depend on.

Nothing in this script reads the within-family (Howe 2022) or Genes & Cognition data. The
protocol.md records the JSON's sha256; ``common.load_frozen`` refuses to run analyses if the
JSON changes afterwards.

Usage:  python pipelines/sprint4/freeze_protocol.py [--no-hash-bed]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

SPRINT3_COMMIT = "04c70efe4eecadf41a0aee3beedf3d0dc2f9f868"
BONFERRONI_GENES = 0.05 / 18418


def frozen_sets() -> list[dict]:
    sets = C.read_setannot()
    enr = pd.read_csv(C.REPO_ROOT / "reports" / "gene_tournament" / "pathway_enrichment.csv")
    enr = enr[(enr.conditioning == "cond_annotation") & (enr.source_file == "syngo")].set_index("SET")
    sym = pd.read_csv(C.GENE_MAP, sep="\t", usecols=["GENE", "current_symbol"])
    sym = dict(zip(sym.GENE, sym.current_symbol))
    out = []
    for sid in C.FROZEN_SETS:
        genes = sorted(set(sets[sid]))
        row = enr.loc[sid]
        if not (row.FDR_global < 0.05):
            raise SystemExit(f"{sid} did not survive global FDR in Sprint 3 -- refusing to freeze it")
        out.append({
            "set_id": sid, "name": str(row.NAME), "source_file": "syngo.setannot",
            "n_genes_in_set_file": len(genes),
            "n_genes_tested_sprint3": int(row.NGENES),
            "gene_list_sha256": C.gene_list_hash(genes),
            "entrez_ids": genes,
            "symbols": [str(sym.get(g, "")) for g in genes],
            "sprint3_discovery": {"gwas": "Davies 2018 open subset, N=282,014",
                                  "beta": float(row.BETA), "se": float(row.SE),
                                  "P": float(row.P), "FDR_global": float(row.FDR_global)},
        })
    return out


def loci(davies: pd.DataFrame) -> list[dict]:
    g = pd.read_csv(C.DAVIES_GENES_OUT, sep=r"\s+")
    bonf = g[g.P < BONFERRONI_GENES]
    ld = pd.read_parquet(C.LD_LOCI)[["GENE", "ld_block_r0.2"]]
    bonf = bonf.merge(ld, on="GENE", how="left")
    loc = pd.read_csv(C.GENE_LOC, sep="\t", header=None, names=["GENE", "CHR", "START", "STOP", "STRAND", "SYMBOL"])
    loc["CHR"] = loc.CHR.astype(str)
    bonf = bonf.drop(columns=["CHR", "START", "STOP"]).merge(loc, on="GENE", how="left")
    sym = pd.read_csv(C.GENE_MAP, sep="\t", usecols=["GENE", "current_symbol"])
    bonf = bonf.merge(sym, on="GENE", how="left")
    rows = []
    for block, grp in bonf.groupby("ld_block_r0.2"):
        chrom = str(grp.CHR.iloc[0])
        start, stop = int(grp.START.min()) - 10_000, int(grp.STOP.max()) + 10_000
        d = davies[(davies.Chromosome == chrom) & (davies.Position >= start) & (davies.Position <= stop)]
        if d.empty:
            lead = None
        else:
            d = d.assign(absz=d.Zscore.abs()).sort_values(["P-value", "absz", "Position"],
                                                            ascending=[True, False, True])
            lead = d.iloc[0]
        top = grp.sort_values("P").iloc[0]
        rows.append({
            "locus_id": f"L{int(block)}", "ld_block_r0.2": int(block), "chr": chrom,
            "start": start, "end": stop,
            "bonferroni_genes": [{"entrez": int(r.GENE), "symbol": str(r.current_symbol),
                                  "magma_P": float(r.P)} for r in grp.sort_values("P").itertuples()],
            "top_gene": str(top.current_symbol), "top_gene_P": float(top.P),
            "lead_snp": None if lead is None else str(lead.Markername),
            "lead_pos_grch37": None if lead is None else int(lead.Position),
            "lead_effect_allele": None if lead is None else str(lead.Effect_allele).upper(),
            "lead_other_allele": None if lead is None else str(lead.Other_allele).upper(),
            "lead_davies_z": None if lead is None else float(lead.Zscore),
            "lead_davies_p": None if lead is None else float(lead["P-value"]),
            "cognition_increasing_allele": None if lead is None else (
                str(lead.Effect_allele).upper() if lead.Zscore > 0 else str(lead.Other_allele).upper()),
        })
    rows.sort(key=lambda r: (r["lead_davies_p"] if r["lead_davies_p"] is not None else 1.0))
    return rows


def rules() -> dict:
    return {
        "gene_analysis": {
            "software": "MAGMA v1.10 (same binary as Sprint 3)",
            "model": "SNP-wise mean (MAGMA default), 10 kb window, NCBI37.3 gene locations",
            "ld_reference": "1000 Genomes phase 3 EUR (g1000_eur, 503 individuals), GRCh37",
            "command": "magma --bfile g1000_eur --pval <file> ncol=N|N=<n> --gene-settings "
                       "snp-exclude=position_mismatch_snps.txt --gene-annot genes_10kb.genes.annot --out <out>",
            "snp_matching": "by rsID against g1000_eur.bim; files without rsIDs are mapped by GRCh37 "
                            "chr:pos:alleles to the bim; GRCh38 inputs must be lifted or rsID-mapped before use",
            "n_rule": "per-SNP N column when present, else the dataset-level N from verified metadata",
        },
        "gene_set_model": {
            "set_file": "data/gene_tournament/pathway_sets/syngo.setannot (full file; each set tested separately)",
            "covariates": "data/sprint4/gene_covariates.txt (log_annotation_density, log_LOEUF)",
            "command": "magma --gene-results <genes.raw> --set-annot syngo.setannot --gene-covar "
                       "gene_covariates.txt --model condition-hide=log_annotation_density,log_LOEUF --out <out>",
            "test": "competitive, one-sided (beta > 0)",
            "what_sign_means": "MAGMA gene statistics are unsigned (from P-values). A positive set beta means "
                               "set genes carry MORE association than matched genes, in either allelic "
                               "direction. It is enrichment concordance, not allele-direction concordance. "
                               "Allele direction is tested separately at the locus level.",
        },
        "gate_a": {
            "datasets": {
                "within_family": {"opengwas_id": "ieu-b-4837", "trait": "Cognitive function",
                                  "note": "Sibling estimate", "sample_size": 9997,
                                  "build": "HG19/GRCh37", "consortium": "Within family GWAS consortium",
                                  "author": "Howe LJ", "year": 2022},
                "population": {"opengwas_id": "ieu-b-4838", "trait": "Cognitive function",
                               "note": "Population estimate", "sample_size": 22593,
                               "build": "HG19/GRCh37", "consortium": "Within family GWAS consortium",
                               "author": "Howe LJ", "year": 2022},
                "identity_check": "all listed fields must equal the verified metadata AND the VCF header "
                                  "must carry the same dataset ID; a mismatch makes Gate A NOT_TESTABLE",
            },
            "access": "OpenGWAS automated download requires a JWT in OPENGWAS_JWT. No account is created "
                      "and no website download is automated on the user's behalf.",
            "vcf_fields": "ES (effect of ALT), SE, LP (-log10 P), AF (ALT frequency), SS (per-SNP N if present)",
            "effective_n_rule": "N_eff(WF) = N(pop) x median over SNPs with 0.05<=AF<=0.95 of "
                                "(SE_pop/SE_wf)^2. Depends on sampling design only, never on effect sizes.",
            "howe_shrinkage_f": 0.78,
            "howe_shrinkage_status": "brief states ~22% genome-wide shrinkage for cognition; to be checked "
                                     "against Howe 2022 text. A literature correction is allowed as a recorded "
                                     "pre-data amendment ONLY while no within-family association value has been read.",
            "calibration": {
                "method": "LD-aware summary-statistic subsampling (PUMAS-style; Zhao et al. 2021 Nat Commun): "
                          "z_sim = f*sqrt(n/N)*z_obs + sqrt(1 - f^2*n/N)*e, e ~ N(0, R_block) generated as "
                          "X_block' u / sqrt(503) from standardised g1000_eur genotypes with independent "
                          "u ~ N(0, I) per LDetect EUR block (Berisa & Pickrell 2016), e aligned to the "
                          "summary-statistic effect allele. Same noise draws reused across scenarios "
                          "(common random numbers). Each replicate goes through the identical MAGMA gene "
                          "and gene-set pipeline.",
                "pre_data_source": "Davies 2018 open subset (N=282,014): expectation available now",
                "post_data_source": "Howe population estimate ieu-b-4838 subsampled to N_eff(WF): primary "
                                    "expectation once the data exist",
                "n_grid_pre_data": [22593, 9997, 4999],
                "n_grid_note": "22,593 = Howe population N; 9,997 = Howe sibling N (individuals); 4,999 = "
                               "~half, the effective N of a sibling-difference design with pairs",
                "f_grid": [1.0, 0.78, 0.0],
                "replicates_per_scenario": 40,
                "seed": 20260923,
            },
            "set_classification": {
                "alpha_one_sided": 0.05,
                "expected_quantile_low": 0.025,
                "DIRECT_EFFECT_SUPPORTED": "P_wf < 0.05 (MAGMA competitive, one-sided)",
                "CONCORDANT_BUT_UNDERPOWERED": "beta_wf > 0, P_wf >= 0.05, and beta_wf >= 2.5th percentile "
                                               "of the simulated distribution at N_eff(WF) with f = howe_shrinkage_f",
                "INCONSISTENT": "beta_wf < 2.5th percentile of that distribution (BEYOND_EXPECTED_NOISE), or "
                                "beta_wf <= 0 inside it (SIGN_DISCORDANT_WITHIN_NOISE; cannot drive PIVOT)",
                "NOT_TESTABLE": "data absent, identity check failed, harmonisation failed, or set absent",
                "adequate_power": "simulated P(P_wf < 0.05 | f = howe_shrinkage_f) >= 0.5",
                "attenuation_ratio": "beta_wf / beta_pop (Howe); 95% CI by parametric bootstrap "
                                     "(10,000 draws, independent normals: conservative because the two "
                                     "estimates share individuals); Fieller CI when |beta_pop/SE_pop| > 2",
            },
            "locus_rules": {
                "lead_snp": "min-P Davies SNP within [min gene start - 10 kb, max gene stop + 10 kb] of the "
                            "locus's Bonferroni genes (ties: larger |Z|, then lower position)",
                "harmonisation": "match on rsID; alleles compared case-insensitively; strand flip allowed "
                                 "for non-palindromic SNPs only; palindromic (A/T, C/G) SNPs with ALT "
                                 "frequency in [0.40, 0.60] are UNRESOLVED_HARMONISATION",
                "proxy": "if the lead is absent, best g1000_eur proxy with r^2 >= 0.8 within 500 kb; "
                         "otherwise NOT_TESTABLE",
                "cognition_allele": "the Davies allele with positive Z (Davies: higher = better cognition)",
                "winners_curse": "expected WF z uses Tweedie's formula E[mu|z] = z + d/dz log f(z), with f a "
                                 "Gaussian KDE of Davies Z over every 50th SNP genome-wide",
                "classes": {"DIRECT_SUPPORTED": "aligned WF z > 0 and one-sided P < 0.05",
                            "CONCORDANT_UNDERPOWERED": "aligned WF z > 0 and one-sided P >= 0.05",
                            "DISCORDANT_WITHIN_NOISE": "aligned WF z <= 0 and >= expected - 1.96",
                            "DISCORDANT_BEYOND_NOISE": "aligned WF z < expected - 1.96",
                            "NOT_TESTABLE": "absent, no proxy, or unresolved harmonisation"},
                "global_tests": ["binomial sign concordance vs 0.5 over testable loci",
                                 "expected concordance under f=1 and f=howe_shrinkage_f",
                                 "slope of beta_wf on beta_pop through the origin (inverse-variance)",
                                 "Spearman of Davies |z| rank vs aligned WF z"],
            },
        },
        "gate_b": {
            "source": "Zenodo 10.5281/zenodo.11066096 (record 11066096, published 2024-04-25)",
            "independent_files": {"tma_gwas_gc.txt": "md5:22d0c69c32bd4f330436727a408bcced",
                                  "tmn_gwas_gc.txt": "md5:a26d41df1878f2852a2f36082bb364d7",
                                  "tmd_gwas_gc.txt": "md5:cde0c49276bf6018586e7127bb0ebb93"},
            "forbidden_for_independence": ["tma_meta.txt", "tmn_meta.txt", "tmd_meta.txt",
                                           "tma_gwas_ukb.txt", "tmn_gwas_ukb.txt", "tmd_gwas_ukb.txt"],
            "primary_phenotype": "TMA",
            "primary_phenotype_note": "TMA is treated as the executive-function (alphanumeric switching) "
                                      "trail-making condition. If the source defines the files otherwise, the "
                                      "primary becomes the alphanumeric condition, recorded as a pre-data "
                                      "amendment before any association value is read.",
            "phenotype_class": "EXECUTIVE_FUNCTION (not GENERAL_COGNITION)",
            "direction": "set from the phenotype definition only: if a higher value is slower/worse, the "
                         "cognition-aligned z is -z. Never inferred from the data or from NT5DC2.",
            "set_classification": {
                "INDEPENDENT_SUPPORT": "P_gc < 0.05 (one-sided competitive), primary phenotype; Bonferroni "
                                       "over 6 sets (0.05/6) reported alongside",
                "CONCORDANT_BUT_UNDERPOWERED": "beta_gc > 0, P_gc >= 0.05",
                "INCONSISTENT": "beta_gc < 2.5th percentile of the simulated distribution at n=9,997 with "
                                "f = f_gc_lower (BEYOND_EXPECTED_NOISE); beta_gc <= 0 inside it is "
                                "SIGN_DISCORDANT_WITHIN_NOISE",
                "NOT_TESTABLE": "file absent, md5 mismatch, direction undeterminable, or set absent",
                "f_gc_upper": 1.0,
                "f_gc_lower_rule": "rg(primary phenotype, general cognition) if verified from the source "
                                   "paper; otherwise 0.5",
                "expectation_note": "Davies-subsampled expectations assume the trail-making phenotype carried "
                                    "the full general-cognition signal (f=1): an upper bound, not a prediction",
            },
            "locus_support": "G&C_SUPPORTED if aligned one-sided P < 0.05 in the primary phenotype OR "
                             "min over the 3 phenotypes of aligned one-sided P x 3 < 0.05; BH-FDR across "
                             "testable loci reported as confidence, not used as the gate",
            "positive_control": {"locus": "NT5DC2", "snp": "rs7639267",
                                 "pass_rule": "our harmonised G&C estimate has the published sign and "
                                              "|beta_ours - beta_pub| <= 0.1*|beta_pub| + 0.001 and P within "
                                              "a factor of 2 of the published P",
                                 "note": "a pipeline check; NT5DC2 is prenatal-dominant (Sprint 3) and is "
                                         "not promoted to an adult target by replicating"},
        },
        "survivors": {
            "A": "locus DIRECT_SUPPORTED in Gate A",
            "B": "locus G&C_SUPPORTED in Gate B",
            "C": "exceptionally strong prior human evidence (Davies lead P < 1e-15 AND a biology-driven "
                 "(non-positional) L2G call in fine_mapping_support.csv) AND Gate-A locus "
                 "CONCORDANT_UNDERPOWERED",
            "stress_tests": ["NEGR1", "SYT1"],
            "stress_test_rule": "always carried into Gate C, labelled STRESS_TEST; not survivors unless A/B/C holds",
            "positive_control": "NT5DC2 (developmental timing kept explicit)",
            "not_used": "paper counts, top-50 membership, Sprint-1 seed status, theory nodes",
        },
        "gate_c": {
            "fine_mapping": {
                "primary": "Open Targets GWAS credible sets already fetched in Sprint 3 (study-first)",
                "susie_sensitivity": "susieR::susie_rss on Davies z (n=282,014), window lead +/- 500 kb, "
                                     "LD from g1000_eur, L=10, coverage 0.95, min_abs_corr 0.5, "
                                     "estimate_residual_variance=FALSE",
                "ld_mismatch_flag": "susieR::estimate_s_rss s > 0.2 flags the locus; kriging outliers "
                                    "(logLR > 2 and |z| > 2) counted",
                "never": "lead SNP or nearest gene is never equated with the causal gene",
            },
            "qtl_resources": "eQTL Catalogue (public API/FTP; GTEx v8 brain, BrainSeq, ROSMAP, CommonMind or "
                             "others as listed by its metadata), adult samples only; MetaBrain only if "
                             "already accessible",
            "adult_rule": "a QTL dataset counts as adult brain only if its donors are adults; datasets "
                          "including prenatal or childhood samples are flagged and excluded from direction",
            "coloc": {"priors": {"p1": 1e-4, "p2": 1e-4, "p12": 5e-6},
                      "strong_pp_h4": 0.8, "moderate_pp_h4": 0.5,
                      "method_order": "coloc.susie when both sides have SuSiE fits with >=1 credible set; "
                                      "coloc.abf otherwise (reported as single-signal)"},
            "direction_rule": {
                "unchanged_from_sprint3": True,
                "min_strong_gene_level_colocs": 3,
                "min_sign_agreement": 0.8,
                "strength_threshold": 0.8,
                "eligible_qtl_types": "eqtl|pqtl, gene-level only (exon/transcript/splice excluded)",
                "polarity": "sign(beta_QTL / beta_GWAS) x trait polarity (-1 for reaction time, time to "
                            "complete, decline, errors)",
                "counting_unit_primary": "colocalisation rows, as in Sprint 3",
                "counting_unit_secondary": "distinct adult-brain QTL dataset x tissue (majority sign per "
                                           "dataset); a robustness flag, never a relaxation",
                "not_relaxed_for": "NEGR1 (3/4 = 75% in Sprint 3) or any other gene",
                "evidence_pooling": "a (gene, dataset) pair is strong if the Open Targets COLOC h4 >= 0.8 OR "
                                    "our coloc PP.H4 >= 0.8; polarity from our harmonised analysis when "
                                    "available, else OT betaRatioSignAverage; disagreement between the two "
                                    "is reported and the pair counted as disagreeing",
            },
            "joint_gene_tissue": "attempt FOCUS or TGFM on <= 5 loci where one signal colocalises with "
                                 ">1 gene; if software/data make it impossible, record the blocker and "
                                 "make no substitute claim",
        },
        "decision": {
            "precedence": ["STOP_CURRENT_HYPOTHESIS", "PIVOT", "RETRY_IF_GATE_A_UNTESTABLE", "CONTINUE",
                           "ESCALATE", "RETRY"],
            "CONTINUE": ">=1 frozen set DIRECT_EFFECT_SUPPORTED in Gate A AND (>=1 frozen set "
                        "INDEPENDENT_SUPPORT in Gate B OR the Gate-B locus sign-concordance binomial P < 0.05 "
                        "OR >=1 survivor with a direction-resolved adult-brain chain)",
            "PIVOT": ">=3 of 6 frozen sets INCONSISTENT (BEYOND_EXPECTED_NOISE) in an adequately powered "
                     "Gate A, OR >=3 of 6 INCONSISTENT (BEYOND_EXPECTED_NOISE) in Gate B with simulated power "
                     ">= 0.5 at f_gc_lower",
            "STOP_CURRENT_HYPOTHESIS": "the PIVOT condition holds in BOTH Gate A and Gate B",
            "RETRY_IF_GATE_A_UNTESTABLE": "all six sets NOT_TESTABLE in Gate A (access, download, "
                                          "harmonisation or technical failure)",
            "ESCALATE": "synaptic biology survives the direct/independent tests but no survivor gene is "
                        "direction-resolved because the available adult-brain QTL data are inadequate; the "
                        "resolving dataset must be named",
            "RETRY": "anything else ambiguous (underpowered, mixed)",
        },
        "chemistry_gate": {
            "default": "CLOSED",
            "opens_only_if_one_gene_has_all": ["independently supported cognition association (Gate B or "
                                               "Gate A DIRECT_SUPPORTED)",
                                               "credible locus-to-gene evidence (non-positional L2G driver "
                                               "or joint gene-tissue fine-mapping)",
                                               "adult human brain molecular evidence (strong coloc)",
                                               "consistent direction (direction rule met)",
                                               "no disqualifying safety or pleiotropy signal"],
            "label_if_met": "CAUSAL_TARGET_ADJUDICATION_CANDIDATE (never 'drug target', never efficacy)",
        },
        "never": ["NOT_TESTABLE is never reported as NO_EFFECT",
                  "educational attainment is never direct cognition evidence",
                  "UKB-containing files are never counted as G&C independence",
                  "no new pathways are added; no new genome-wide tournament; no new weighted score",
                  "theory nodes (Selective Encoding, Goal-Gated Plasticity) select nothing",
                  "animal-memory data never rescue a failed human locus",
                  "the chemistry gate stays closed unless every criterion above is met"],
    }


def input_hashes(hash_bed: bool) -> dict:
    files = {
        "magma_binary": C.MAGMA_BIN, "syngo.setannot": C.SETS_FILE, "gene_covariates.txt": C.COVARIATES,
        "NCBI37.3.gene.loc": C.GENE_LOC, "genes_10kb.genes.annot": C.GENE_ANNOT_10KB,
        "position_mismatch_snps.txt": C.SNP_EXCLUDE, "g1000_eur.bim": C.BFILE.with_suffix(".bim"),
        "g1000_eur.fam": C.BFILE.with_suffix(".fam"),
        "davies2018_10kb.genes.out": C.DAVIES_GENES_OUT, "ld_loci.parquet": C.LD_LOCI,
        "ldetect_EUR_fourier_ls-all.bed": C.REPO_ROOT / "data/raw/sprint4/ldetect/EUR_fourier_ls-all.bed",
    }
    if hash_bed:
        files["g1000_eur.bed"] = C.BFILE.with_suffix(".bed")
    return {k: {"path": str(v), "sha256": C.sha256_file(v)} for k, v in files.items()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-hash-bed", action="store_true")
    args = ap.parse_args(argv)

    davies_sha = C.sha256_file(C.DAVIES_INPUT)
    if davies_sha != C.DAVIES_SHA256:
        raise SystemExit(f"Davies input sha256 mismatch: {davies_sha}")
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", dtype={"Chromosome": str},
                         usecols=["Chromosome", "Position", "Markername", "Effect_allele",
                                  "Other_allele", "P-value", "Zscore"])
    frozen = {
        "protocol_version": "1.0.0",
        "frozen_at_utc": C.utc_now(),
        "frozen_from_sprint3_commit": SPRINT3_COMMIT,
        "primary_question": ("Does the Sprint-3 synaptic/presynaptic signal represent a direct inherited "
                             "cognition effect rather than a signal materialised by population structure, "
                             "assortative mating, indirect family effects or shared UK-Biobank sampling?"),
        "new_data_read_before_freeze": "none. Metadata only: the public OpenGWAS gwasinfo.json entries for "
                                       "ieu-b-4837/4838 and the Zenodo 11066096 file listing (names, sizes, md5).",
        "frozen_sets": frozen_sets(),
        "loci": loci(davies),
        "rules": rules(),
        "inputs": {"davies2018_open_complete.txt": {"path": str(C.DAVIES_INPUT), "sha256": davies_sha,
                                                    "n": C.DAVIES_N, "build": "GRCh37",
                                                    "effect_allele_column": "Effect_allele (Zscore signed to it)"},
                   **input_hashes(not args.no_hash_bed)},
    }
    n_loci = len(frozen["loci"])
    if n_loci != 159:
        raise SystemExit(f"expected 159 Sprint-3 loci, found {n_loci}")
    C.FROZEN_JSON.parent.mkdir(parents=True, exist_ok=True)
    C.FROZEN_JSON.write_text(json.dumps(frozen, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {C.FROZEN_JSON} ({n_loci} loci, {len(frozen['frozen_sets'])} sets)")
    print("sha256", C.sha256_file(C.FROZEN_JSON))
    for s in frozen["frozen_sets"]:
        print(f"  {s['set_id']:18s} n={s['n_genes_in_set_file']:5d} {s['gene_list_sha256'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
