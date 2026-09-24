#!/usr/bin/env python3
"""Sprint 5A Goal B — multi-trait colocalisation (HyPrColoc) at the 16 L1/L2 loci + 6 named loci.

Traits (all aligned to the Davies 2018 EFFECT allele; sign convention "higher = better cognition"):
  COG_davies    Davies 2018 general cognition, z -> standardised beta (gwas_beta; N = 282,014)
  TMA_gc        G&C trail-making A (N = 9,932; BOLT BETA per A1; higher = slower -> SIGN FLIPPED)
  PIQ_genlang   GenLang performance IQ GCST90104472 (N ~ 18.7k; beta per effect_allele)
  XIQ_zabaneh   Zabaneh 2018 extreme high IQ, log(OR) per effect_allele (1,238 cases / 8,172 controls)
  FI4_ukb       UKB FI4 positional arithmetic GCST90042729 (Jiang 2021 fastGWA-GLMM, binary; 102,666 cases /
                12,637 controls; cases presumed = correct answer — direction used for labels only)
  eQTL:<gene>@<dataset>  up to 3 adult-brain gene-level eQTL traits per locus from the Sprint-4 eQTL
                Catalogue r7 files (ALT = effect allele): the 3 genes with the highest Sprint-4 coloc.abf
                PP.H4 vs Davies at that locus, each at its best adult 'ge' dataset. Selection uses the
                Sprint-4 pairwise result, so this is a follow-up of pre-existing signals, not a blind scan.

SNPs: 1000G-EUR SNPs of the Sprint-4 SuSiE window (lead +/- 500 kb, GRCh37) present in EVERY trait of the
run (HyPrColoc needs a complete matrix). Palindromic SNPs with 1000G MAF > 0.40 dropped; strand flips only
for non-palindromic SNPs.

HyPrColoc (jrs95/hyprcoloc 0.0.2 @0348bbd, Eigen-cast patch pipelines/sprint5a/hyprcoloc_eigen_cast.patch)
with package defaults: prior.1 = 1e-4, prior.c = 0.02, reg.thresh = align.thresh = 0.5 (uniform priors),
binary.outcomes flagged for XIQ_zabaneh and FI4_ukb. Two runs per locus: ALL traits, and GWAS-only.

SAMPLE OVERLAP — HyPrColoc assumes independent studies; these are NOT independent:
  Davies ⊃ UK Biobank (FI4 is UKB), HRS (Zabaneh controls are HRS), BATS (GenLang includes BATS);
  G&C (TMA) is independent of UKB. Overlap inflates shared-signal evidence between overlapping GWAS, so a
  cluster of COG_davies with FI4_ukb / XIQ_zabaneh / PIQ_genlang is labelled OVERLAP_CONFOUNDED_POSSIBLE,
  and only clusters that include TMA_gc or an eQTL trait add evidence beyond Davies itself.

Outputs: reports/sprint5a/multitrait_coloc.csv (+ data/interim/sprint5a/hyprcoloc/ inputs)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "pipelines" / "sprint4"))
import common as C  # noqa: E402
import loci_tools as LT  # noqa: E402

WORK = REPO / "data" / "interim" / "sprint5a" / "hyprcoloc"
OUT = REPO / "reports" / "sprint5a"
L1L2 = ["L51327", "L64067", "L91869", "L51460", "L1803", "L3123", "L2131", "L60412", "L1630", "L3760", "L64116",
        "L7009", "L9975", "L100132074", "L7324", "L64288"]
EXTRA = ["L257194", "L7009", "L79922", "L1565", "L319", "L65265", "L55168"]
LOCI = list(dict.fromkeys(L1L2 + EXTRA))
WIN = 500_000
GWAS_FILES = {
    "TMA_gc": REPO / "data/interim/sprint4/genc/tma_gwas_gc.txt",
    "PIQ_genlang": REPO / "data/interim/sprint5/genlang/GCST90104472_buildGRCh37.tsv",
    "XIQ_zabaneh": REPO / "data/interim/sumstats/GCST005626_zabaneh_extremeIQ_b37.tsv.gz",
    "FI4_ukb": REPO / "data/interim/sumstats/GCST90042729_FI4_positional_arithmetic.tsv.gz",
}
COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}


def read_window_gwas(name: str, chrom: str, lo: int, hi: int, cache: dict) -> pd.DataFrame:
    """Return rsid, ea, oa, beta, se (beta in the file's own effect-allele, 'higher = better' sign)."""
    if name not in cache:
        f = GWAS_FILES[name]
        if name == "TMA_gc":
            d = pd.read_csv(f, sep="\t", dtype={"CHR": str})
            d = d.rename(columns={"SNP": "rsid", "CHR": "chr", "BP": "pos", "A1": "ea", "A2": "oa", "BETA": "beta",
                                  "SE": "se"})
            d["beta"] = -d.beta            # higher TMA time = slower = worse -> flip so higher = better
        elif name == "PIQ_genlang":
            d = pd.read_csv(f, sep="\t", dtype={"chromosome": str})
            d = d.rename(columns={"variant_id": "rsid", "chromosome": "chr", "base_pair_location": "pos",
                                  "effect_allele": "ea", "other_allele": "oa", "standard_error": "se"})
        elif name == "XIQ_zabaneh":
            d = pd.read_csv(f, sep="\t", dtype={"chromosome": str})
            d = d.rename(columns={"variant_id": "rsid", "chromosome": "chr", "base_pair_location": "pos",
                                  "effect_allele": "ea", "other_allele": "oa", "standard_error": "se"})
            d["beta"] = np.log(d.odds_ratio)
        else:
            d = pd.read_csv(f, sep="\t", dtype={"chromosome": str},
                            usecols=["chromosome", "variant_id", "base_pair_location", "effect_allele",
                                     "other_allele", "beta", "standard_error"])
            d = d.rename(columns={"variant_id": "rsid", "chromosome": "chr", "base_pair_location": "pos",
                                  "effect_allele": "ea", "other_allele": "oa", "standard_error": "se"})
        d = d[["rsid", "chr", "pos", "ea", "oa", "beta", "se"]]
        d = d[np.isfinite(d.beta) & np.isfinite(d.se) & (d.se > 0)]
        d["ea"], d["oa"] = d.ea.astype(str).str.upper(), d.oa.astype(str).str.upper()
        cache[name] = d.drop_duplicates("rsid", keep=False)
    d = cache[name]
    return d[(d.chr.astype(str) == chrom) & d.pos.between(lo, hi)]


def align(t: pd.DataFrame, ref: pd.DataFrame) -> pd.Series:
    """Beta of trait t re-expressed for the Davies effect allele; index = rsid. ref: snp, EA, OA, maf."""
    m = t.merge(ref, left_on="rsid", right_on="snp")
    pal = np.array([frozenset({a, b}) in LT.PALINDROMIC for a, b in zip(m.EA, m.OA)])
    s = np.where((m.ea == m.EA) & (m.oa == m.OA), 1, np.where((m.ea == m.OA) & (m.oa == m.EA), -1, 0))
    fe, fo = m.ea.map(COMP), m.oa.map(COMP)
    s = np.where((s == 0) & ~pal & (fe == m.EA) & (fo == m.OA), 1, s)
    s = np.where((s == 0) & ~pal & (fe == m.OA) & (fo == m.EA), -1, s)
    keep = (s != 0) & ~(pal & (m.maf > 0.40))
    m = m[keep].assign(b=m.beta[keep] * s[keep])
    return m.set_index("rsid")[["b", "se"]]


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = C.load_frozen()
    davies = pd.read_csv(C.DAVIES_INPUT, sep=r"\s+", usecols=["Markername", "Effect_allele", "Other_allele",
                                                               "Zscore"]).drop_duplicates("Markername", keep=False)
    davies["Effect_allele"], davies["Other_allele"] = davies.Effect_allele.str.upper(), davies.Other_allele.str.upper()
    prov = json.loads((REPO / "data/raw/sprint4/eqtl_catalogue/PROVENANCE.json").read_text())["loci"]["items"]
    lead = {it["locus_id"]: it for it in prov}
    s4 = pd.read_parquet(C.OUT / "adult_brain_susie_coloc.parquet")
    meta = pd.read_csv(C.DATA / "eqtl_catalogue_brain_datasets.csv")
    adult_ge = set(meta[(meta.adult_status == "ADULT") & (meta.quant_method == "ge")].dataset_id)
    lab = meta.set_index("dataset_id").apply(lambda r: f"{r.study_label}:{r.tissue_label}", axis=1).to_dict()
    q = pd.read_csv(C.DATA / "gate_c_query_genes.csv")
    sym = dict(zip(q.ensembl_gene_id, q.gene))
    s4 = s4[s4.method.str.startswith("coloc.abf") & s4.dataset_id.isin(adult_ge)]
    cache: dict = {}
    manifest = []
    for loc in LOCI:
        it = lead[loc]
        chrom, p37 = str(it["chr"]), int(it["lead_pos_grch37"])
        snps = pd.read_csv(C.WORK / "susie" / loc / "snps.tsv", sep="\t")
        ref = snps.merge(davies, left_on="snp", right_on="Markername")
        ref = ref.rename(columns={"Effect_allele": "EA", "Other_allele": "OA", "maf_1000g": "maf"})
        pal = np.array([frozenset({a, b}) in LT.PALINDROMIC for a, b in zip(ref.EA, ref.OA)])
        ref = ref[~(pal & (ref.maf > 0.40))]
        z = ref.Zscore.to_numpy(float)
        maf = ref.maf.clip(1e-4, 0.5).to_numpy(float)
        denom = np.sqrt(2 * maf * (1 - maf) * (C.DAVIES_N + z ** 2))
        traits = {"COG_davies": pd.DataFrame({"b": z / denom, "se": 1 / denom}, index=ref.snp.values)}
        for name in GWAS_FILES:
            t = read_window_gwas(name, chrom, p37 - WIN, p37 + WIN, cache)
            traits[name] = align(t, ref[["snp", "EA", "OA", "maf"]])
        # eQTL traits: top-3 genes by Sprint-4 coloc.abf PP.H4, each at its best adult ge dataset
        e = s4[s4.locus_id == loc].sort_values("PP.H4", ascending=False).drop_duplicates("gene_id").head(3)
        eqtl_meta = []
        for r in e.itertuples():
            f = C.WORK / "eqtl" / f"{loc}__{r.dataset_id}.parquet"
            if not f.exists():
                continue
            x = pd.read_parquet(f)
            x = x[x.molecular_trait_id == r.molecular_trait_id].drop_duplicates(["variant"]).drop_duplicates("rsid",
                                                                                                           keep=False)
            x = x.rename(columns={"alt": "ea", "ref": "oa"})[["rsid", "ea", "oa", "beta", "se"]]
            x = x[np.isfinite(x.beta) & (x.se > 0)]
            x["ea"], x["oa"] = x.ea.str.upper(), x.oa.str.upper()
            nm = f"eQTL:{sym.get(r.gene_id, r.gene_id)}@{r.dataset_id}"
            traits[nm] = align(x, ref[["snp", "EA", "OA", "maf"]])
            eqtl_meta.append({"trait": nm, "gene_id": r.gene_id, "dataset": r.dataset_id,
                              "dataset_label": lab.get(r.dataset_id),
                              "s4_coloc_abf_pp_h4": float(e.loc[r.Index, "PP.H4"])})
        for run, names in (("ALL", list(traits)), ("GWAS_ONLY", [k for k in traits if not k.startswith("eQTL:")])):
            common = set.intersection(*[set(traits[k].index) for k in names])
            common = [s for s in ref.snp if s in common]
            B = pd.DataFrame({k: traits[k].loc[common, "b"].values for k in names}, index=common)
            S = pd.DataFrame({k: traits[k].loc[common, "se"].values for k in names}, index=common)
            B.to_csv(WORK / f"{loc}.{run}.betas.tsv", sep="\t")
            S.to_csv(WORK / f"{loc}.{run}.ses.tsv", sep="\t")
            manifest.append({"locus_id": loc, "run": run, "n_snps": len(common), "traits": ";".join(names),
                             "n_snps_per_trait": ";".join(f"{k}={len(traits[k])}" for k in names),
                             "max_abs_z_by_trait": ";".join(f"{k}={np.nanmax(np.abs(B[k] / S[k])):.2f}"
                                                            for k in names) if len(common) else "",
                             "aligned_z_at_davies_lead": ";".join(
                                 f"{k}={(B.loc[it['lead_snp'], k] / S.loc[it['lead_snp'], k]):.2f}"
                                 for k in names) if it["lead_snp"] in B.index else "lead SNP not in complete set",
                             "eqtl_traits": json.dumps(eqtl_meta)})
        print(loc, {k: len(v) for k, v in traits.items()}, flush=True)
    man = pd.DataFrame(manifest)
    man.to_csv(WORK / "manifest.csv", index=False)
    rs = subprocess.run([str(C.RSCRIPT), str(REPO / "pipelines/sprint5a/multitrait_coloc.R"), str(WORK)],
                        capture_output=True, text=True, timeout=7200)
    print(rs.stdout[-3000:], rs.stderr[-3000:])
    res = pd.read_csv(WORK / "hyprcoloc_results.tsv", sep="\t")
    res = res.merge(man[["locus_id", "run", "n_snps", "traits", "max_abs_z_by_trait", "aligned_z_at_davies_lead",
                          "eqtl_traits"]], on=["locus_id", "run"], how="left")
    loc_meta = pd.read_csv(REPO / "reports/sprint5/locus_confidence_rank.csv")[["labels", "top_gene_labels",
                                                                                "locus_stratum"]]
    res = res.merge(loc_meta.rename(columns={"labels": "locus_id", "top_gene_labels": "locus_label"}), on="locus_id",
                    how="left")

    def overlap_label(tr: str) -> str:
        if not isinstance(tr, str) or tr == "None":
            return "NO_CLUSTER"
        t = tr.split(", ")
        has_cog = "COG_davies" in t
        indep = [x for x in t if x == "TMA_gc" or x.startswith("eQTL:")]
        overl = [x for x in t if x in ("FI4_ukb", "XIQ_zabaneh", "PIQ_genlang")]
        if has_cog and indep:
            return "COG_WITH_INDEPENDENT_TRAIT (" + ",".join(indep) + ")" + (
                "; also overlapping GWAS " + ",".join(overl) if overl else "")
        if has_cog and overl:
            return "COG_WITH_OVERLAPPING_GWAS_ONLY (OVERLAP_CONFOUNDED_POSSIBLE)"
        return "CLUSTER_WITHOUT_COG"

    res["overlap_assessment"] = res.traits_clustered.map(overlap_label)
    res["cog_and_eqtl_cluster"] = res.traits_clustered.fillna("").str.contains("COG_davies") & \
        res.traits_clustered.fillna("").str.contains("eQTL:")
    res["independence_caveat"] = ("HyPrColoc assumes independent studies; Davies ⊃ UKB/HRS/BATS; FI4 = UKB ⊂ Davies; "
                                  "Zabaneh controls = HRS ⊂ Davies; GenLang shares BATS with Davies; eQTL cohorts "
                                  "(GTEx/CommonMind/ROSMAP/Braineac2/Young2019) independent of the GWAS")
    res.to_csv(OUT / "multitrait_coloc.csv", index=False)
    print(res[["locus_id", "locus_label", "run", "n_snps", "cluster", "traits_clustered", "posterior_prob",
               "regional_prob", "candidate_snp", "posterior_explained_by_snp", "overlap_assessment"]].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
