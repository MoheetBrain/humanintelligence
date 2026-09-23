"""Sprint 5 math-53 extraction + overlap with general-cognition loci.

Inputs (all local):
  data/raw/sprint5/math/giannelis2025_tableS2.csv <- Supp Table S2 of Giannelis et al. 2025 (Mol Psychiatry), extracted verbatim
  data/raw/sprint5/math/ensembl_variation_grch3{7,8}_math53.json
  research/sprint4/frozen_hypotheses.json   (159 loci: chr/start/end GRCh37, lead_pos_grch37)
  data/raw/magma_x01/2026-09-22/NCBI37.3.gene.loc
  Davies 2018 open sumstats (READ ONLY, intelligence-codex)
  data/interim/sumstats/GCST90042726 / GCST90042729 (UKB FI item 1 numeric addition / item 4 positional arithmetic)
"""
import json, sys, hashlib, datetime
import numpy as np, pandas as pd
from scipy import stats

S = sys.argv[1] if len(sys.argv) > 1 else "/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠/data/raw/sprint5/math"
ROOT = "/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠"
DAVIES = "/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/inputs/davies2018_open_complete.txt"
FI = {"fi1_numeric_addition": f"{ROOT}/data/interim/sumstats/GCST90042726_FI1_numeric_addition.tsv.gz",
      "fi4_positional_arithmetic": f"{ROOT}/data/interim/sumstats/GCST90042729_FI4_positional_arithmetic.tsv.gz"}
RNG = np.random.default_rng(20260923)
NPERM = 10000
WIN = 500_000
COMP = str.maketrans("ACGT", "TGCA")

s2 = pd.read_csv(f"{S}/giannelis2025_tableS2.csv")
s2.columns = ["rsid", "chr", "pos", "A1", "A2", "eaf", "beta", "se", "p", "qsnp", "qsnp_p",
              "cojo_beta", "cojo_se", "cojo_p", "ld_r_next", "pops_gene", "enriched_set_npd"]
s2["chr"] = s2.chr.astype(str)
s2["z"] = s2.beta / s2.se
s2["math_increasing_allele"] = np.where(s2.beta > 0, s2.A1, s2.A2)
s2["palindromic"] = [set([a, b]) in ({"A", "T"}, {"C", "G"}) for a, b in zip(s2.A1, s2.A2)]

# ---- Ensembl mapping
def ens(path, asm):
    d = json.load(open(path))
    rows = []
    for rs in s2.rsid:
        v = d.get(rs)
        if not v:
            rows.append({"rsid": rs}); continue
        m = [x for x in v["mappings"] if x["assembly_name"] == asm and "_" not in x["seq_region_name"]
             and "PATCH" not in x["seq_region_name"]]
        rows.append({"rsid": rs, f"chr_{asm}": m[0]["seq_region_name"] if m else None,
                     f"pos_{asm}": m[0]["start"] if m else None,
                     f"allele_string_{asm}": m[0]["allele_string"] if m else None,
                     f"current_rsid_{asm}": v.get("name"), f"maf_{asm}": v.get("MAF"),
                     f"minor_allele_{asm}": v.get("minor_allele"),
                     f"consequence_{asm}": v.get("most_severe_consequence"),
                     f"n_mappings_{asm}": len(m)})
    return pd.DataFrame(rows)

e38 = ens(f"{ROOT}/data/raw/sprint5/math/ensembl_variation_grch38_math53.json", "GRCh38")
e37 = ens(f"{ROOT}/data/raw/sprint5/math/ensembl_variation_grch37_math53.json", "GRCh37")
s2 = s2.merge(e38, on="rsid", how="left").merge(e37, on="rsid", how="left")
s2["build_check"] = np.where((s2.chr_GRCh37 == s2.chr) & (s2.pos_GRCh37 == s2.pos), "TableS2_pos==Ensembl_GRCh37",
                             "MISMATCH_vs_Ensembl_GRCh37")
print(s2.build_check.value_counts())

# ---- loci
fz = json.load(open(f"{ROOT}/research/sprint4/frozen_hypotheses.json"))
loci = pd.DataFrame([{k: l[k] for k in ["locus_id", "chr", "start", "end", "top_gene", "lead_snp", "lead_pos_grch37",
                                        "lead_davies_z"]} for l in fz["loci"]])
loci["chr"] = loci.chr.astype(str)
assert len(loci) == 159

def locus_hits(chrom, pos):
    L = loci[loci.chr == chrom]
    inside = L[(L.start <= pos) & (L.end >= pos)]
    near = L[(L.lead_pos_grch37.notna()) & ((L.lead_pos_grch37 - pos).abs() <= WIN)]
    return inside, near

# ---- genes
gl = pd.read_csv(f"{ROOT}/data/raw/magma_x01/2026-09-22/NCBI37.3.gene.loc", sep="\t", header=None,
                 names=["entrez", "chr", "start", "end", "strand", "symbol"])
gl["chr"] = gl.chr.astype(str)

def genes_near(chrom, pos):
    g = gl[(gl.chr == chrom) & (gl.start <= pos + WIN) & (gl.end >= pos - WIN)].copy()
    g["dist"] = np.where((g.start <= pos) & (g.end >= pos), 0, np.minimum((g.start - pos).abs(), (g.end - pos).abs()))
    return g.sort_values(["dist", "start"])

# ---- Davies (read once, full)
dv = pd.read_csv(DAVIES, sep=" ", usecols=["Chromosome", "Position", "Markername", "Effect_allele", "Other_allele",
                                             "P-value", "Zscore"], dtype={"Chromosome": str})
print("davies rows", len(dv))
dv["Effect_allele"] = dv.Effect_allele.str.upper(); dv["Other_allele"] = dv.Other_allele.str.upper()

def align(ea, oa, z, target):
    """return z for the target allele, and how it was aligned"""
    if target == ea: return z, "direct"
    if target == oa: return -z, "direct_flipped"
    t = target.translate(COMP)
    if t == ea: return z, "strand_complement"
    if t == oa: return -z, "strand_complement_flipped"
    return np.nan, "allele_mismatch"

dsub = dv[dv.Markername.isin(set(s2.rsid))].set_index("Markername")
dz, dp, dhow, dpos = [], [], [], []
for r in s2.itertuples():
    if r.rsid in dsub.index:
        x = dsub.loc[r.rsid]
        z, how = align(x.Effect_allele, x.Other_allele, x.Zscore, r.math_increasing_allele)
        # sanity: other allele must also be consistent
        dz.append(z); dp.append(x["P-value"]); dhow.append(how); dpos.append(int(x.Position))
    else:
        dz.append(np.nan); dp.append(np.nan); dhow.append("not_in_davies"); dpos.append(np.nan)
s2["davies_z_aligned_to_math_increasing_allele"] = dz
s2["davies_p"] = dp
s2["davies_alignment"] = dhow
s2["davies_pos"] = dpos

# ---- UKB FI arithmetic items (objective but UKB, heavily g-loaded)
fi_full = {}
for lab, path in FI.items():
    f = pd.read_csv(path, sep="\t", usecols=["chromosome", "variant_id", "base_pair_location", "effect_allele",
                                              "other_allele", "N", "effect_allele_frequency", "beta",
                                              "standard_error", "p_value"], dtype={"chromosome": str})
    fi_full[lab] = f
    sub = f[f.variant_id.isin(set(s2.rsid))].drop_duplicates("variant_id").set_index("variant_id")
    zz, pp, nn = [], [], []
    for r in s2.itertuples():
        if r.rsid in sub.index:
            x = sub.loc[r.rsid]
            z, how = align(x.effect_allele, x.other_allele, x.beta / x.standard_error, r.math_increasing_allele)
            zz.append(z); pp.append(x.p_value); nn.append(x.N)
        else:
            zz.append(np.nan); pp.append(np.nan); nn.append(np.nan)
    s2[f"{lab}_z_aligned"] = zz; s2[f"{lab}_p"] = pp; s2[f"{lab}_N"] = nn

# ---- per-SNP locus / genes
rows = []
for r in s2.itertuples():
    inside, near = locus_hits(r.chr, r.pos)
    g = genes_near(r.chr, r.pos)
    rows.append({
        "rsid": r.rsid,
        "in_cognition_locus": ";".join(inside.locus_id) if len(inside) else "",
        "in_cognition_locus_top_gene": ";".join(inside.top_gene) if len(inside) else "",
        "within_500kb_of_sprint3_lead": ";".join(f"{a}({b},{int(abs(c - r.pos))}bp)" for a, b, c in
                                                zip(near.locus_id, near.lead_snp, near.lead_pos_grch37)) if len(near) else "",
        "nearest_gene_label_only": g.symbol.iloc[0] if len(g) else "",
        "nearest_gene_distance_bp": int(g.dist.iloc[0]) if len(g) else np.nan,
        "n_genes_within_500kb": len(g),
        "genes_within_500kb_by_distance": ";".join(g.symbol.head(15)) + (";..." if len(g) > 15 else ""),
    })
s2 = s2.merge(pd.DataFrame(rows), on="rsid")

# ---- classification
BONF = 0.05 / 53
def cls(r):
    if r.qsnp_p < 5e-8:
        return "MATH_PROXY_ONLY", "QSNP P<5e-8: indicator effects not mediated by the factor (opposite signs on SRM vs HM)"
    if pd.notna(r.davies_p) and r.davies_p < BONF:
        return "GENERAL_G_SHARED", f"Davies P={r.davies_p:.2g} < 0.05/53"
    anyloc = bool(r.in_cognition_locus) or bool(r.within_500kb_of_sprint3_lead)
    if pd.notna(r.davies_p) and r.davies_p >= 0.05 and not anyloc:
        return "MATH_SPECIFIC_ORTHOGONAL", f"Davies P={r.davies_p:.2g} >= 0.05 and outside all 159 loci / >500kb from leads"
    if pd.isna(r.davies_p):
        return "MATH_PROXY_ONLY", "not in Davies file; g-sharing untestable"
    why = []
    if r.davies_p < 0.05: why.append(f"nominal Davies P={r.davies_p:.2g}")
    if anyloc: why.append("inside/near a Sprint-3 g locus without SNP-level Bonferroni g signal")
    return "MATH_PROXY_ONLY", "; ".join(why)
c = s2.apply(cls, axis=1, result_type="expand"); s2["overlap_class"] = c[0]; s2["overlap_class_reason"] = c[1]
print(s2.overlap_class.value_counts())

# ---- null model for locus overlap
dv = dv[dv.Chromosome.isin([str(i) for i in range(1, 23)])].copy()
dv["Position"] = dv.Position.astype(np.int64)
def in_intervals(df, iv):
    out = np.zeros(len(df), bool)
    for ch, grp in iv.groupby("chr"):
        m = (df.Chromosome == ch).values
        pos = df.Position.values[m]
        st = np.sort(grp.s.values); en = grp.e.values[np.argsort(grp.s.values)]
        # merge
        ms, me = [], []
        for a, b in zip(st, en):
            if ms and a <= me[-1]: me[-1] = max(me[-1], b)
            else: ms.append(a); me.append(b)
        ms, me = np.array(ms), np.array(me)
        k = np.searchsorted(ms, pos, side="right") - 1
        hit = (k >= 0) & (pos <= me[np.clip(k, 0, None)])
        out[np.where(m)[0]] = hit
    return out
iv_locus = loci.rename(columns={"start": "s", "end": "e"})[["chr", "s", "e"]]
iv_lead = loci.dropna(subset=["lead_pos_grch37"]).assign(s=lambda d: d.lead_pos_grch37 - WIN,
                                                          e=lambda d: d.lead_pos_grch37 + WIN)[["chr", "s", "e"]]
dv["in_locus"] = in_intervals(dv, iv_locus)
dv["near_lead"] = in_intervals(dv, iv_lead)
dv["any"] = dv.in_locus | dv.near_lead
# gene density (genes overlapping +-500kb)
dv["gdens"] = 0
for ch, grp in gl.groupby("chr"):
    m = (dv.Chromosome == ch).values
    pos = dv.Position.values[m]
    ns = np.searchsorted(np.sort(grp.start.values), pos + WIN, side="right")
    ne = np.searchsorted(np.sort(grp.end.values), pos - WIN, side="left")
    dv.loc[m, "gdens"] = ns - ne
# MAF from UKB FI1 file (EAF), merged by rsid
maf = fi_full["fi1_numeric_addition"][["variant_id", "effect_allele_frequency"]].drop_duplicates("variant_id")
maf["maf"] = np.minimum(maf.effect_allele_frequency, 1 - maf.effect_allele_frequency)
dv = dv.merge(maf[["variant_id", "maf"]], left_on="Markername", right_on="variant_id", how="left")
pool = dv[dv.maf >= 0.01].copy()
maf_edges = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5001]
gd_edges = np.unique(np.quantile(pool.gdens, [0, .2, .4, .6, .8, 1.0]))
gd_edges[-1] += 1
pool["mbin"] = np.digitize(pool.maf, maf_edges) ; pool["gbin"] = np.digitize(pool.gdens, gd_edges)
s2m = s2[["rsid", "chr", "pos", "eaf"]].copy()
s2m["maf"] = np.minimum(s2m.eaf, 1 - s2m.eaf)
s2m = s2m.merge(dv[["Markername", "gdens", "in_locus", "near_lead", "any"]], left_on="rsid", right_on="Markername", how="left")
# math SNPs missing from davies -> compute directly
for i, r in s2m[s2m.gdens.isna()].iterrows():
    g = gl[(gl.chr == r.chr) & (gl.start <= r.pos + WIN) & (gl.end >= r.pos - WIN)]
    s2m.loc[i, "gdens"] = len(g)
s2m["mbin"] = np.digitize(s2m.maf, maf_edges); s2m["gbin"] = np.digitize(s2m.gdens, gd_edges)
obs = {k: int(s2[k2].astype(bool).sum()) for k, k2 in []}
obs_in = int((s2.in_cognition_locus != "").sum())
obs_near = int((s2.within_500kb_of_sprint3_lead != "").sum())
obs_any = int(((s2.in_cognition_locus != "") | (s2.within_500kb_of_sprint3_lead != "")).sum())
groups = {k: g.index.values for k, g in pool.groupby(["mbin", "gbin"])}
inl, nel, anyl = pool.in_locus.values, pool.near_lead.values, pool["any"].values
idx_map = {k: np.searchsorted(pool.index.values, v) for k, v in groups.items()}
null_in, null_near, null_any = np.zeros(NPERM, int), np.zeros(NPERM, int), np.zeros(NPERM, int)
for r in s2m.itertuples():
    cand = idx_map[(r.mbin, r.gbin)]
    pick = cand[RNG.integers(0, len(cand), NPERM)]
    null_in += inl[pick]; null_near += nel[pick]; null_any += anyl[pick]
frac_in, frac_near, frac_any = pool.in_locus.mean(), pool.near_lead.mean(), pool["any"].mean()
fracall = dv.in_locus.mean(), dv.near_lead.mean(), dv["any"].mean()
def emp(o, n): return float((1 + (n >= o).sum()) / (1 + len(n)))
null = {
    "n_math_snps": 53,
    "observed": {"inside_locus_interval": obs_in, "within_500kb_of_lead": obs_near, "either": obs_any},
    "null_A_snp_fraction_unmatched": {
        "definition": "fraction of all autosomal Davies-2018 SNPs (MAF>=0.01 by UKB FI1 EAF) falling in the category; expected = 53*fraction; one-sided binomial P",
        "fraction": {"inside": frac_in, "near_lead": frac_near, "either": frac_any},
        "fraction_all_davies_snps_no_maf_filter": {"inside": fracall[0], "near_lead": fracall[1], "either": fracall[2]},
        "expected": {"inside": 53 * frac_in, "near_lead": 53 * frac_near, "either": 53 * frac_any},
        "binom_p_one_sided": {"inside": float(stats.binomtest(obs_in, 53, frac_in, "greater").pvalue),
                              "near_lead": float(stats.binomtest(obs_near, 53, frac_near, "greater").pvalue),
                              "either": float(stats.binomtest(obs_any, 53, frac_any, "greater").pvalue)}},
    "null_B_matched": {
        "definition": f"{NPERM} random sets of 53 Davies SNPs, each drawn from the same MAF bin {maf_edges[:-1]}+ (UKB FI1 EAF) x gene-density quintile (NCBI37.3 genes overlapping +-500kb; edges {gd_edges.tolist()}) as the corresponding math SNP. LD-score matching NOT done (no LD-score reference in repo). Sampled SNPs are not LD-pruned against each other (conservative only in that independence of draws is assumed).",
        "mean": {"inside": float(null_in.mean()), "near_lead": float(null_near.mean()), "either": float(null_any.mean())},
        "p95": {"inside": float(np.quantile(null_in, .95)), "near_lead": float(np.quantile(null_near, .95)), "either": float(np.quantile(null_any, .95))},
        "empirical_p_one_sided": {"inside": emp(obs_in, null_in), "near_lead": emp(obs_near, null_near), "either": emp(obs_any, null_any)},
        "fold_enrichment": {"inside": obs_in / null_in.mean(), "near_lead": obs_near / null_near.mean(), "either": obs_any / null_any.mean()}},
}
# sign concordance
ok = s2[s2.davies_z_aligned_to_math_increasing_allele.notna()]
def signtest(d, lab):
    pos = int((d.davies_z_aligned_to_math_increasing_allele > 0).sum()); n = len(d)
    return {"subset": lab, "n": n, "n_positive": pos,
            "binom_p_two_sided": float(stats.binomtest(pos, n, 0.5).pvalue) if n else None,
            "mean_aligned_z": float(d.davies_z_aligned_to_math_increasing_allele.mean()) if n else None,
            "median_aligned_z": float(d.davies_z_aligned_to_math_increasing_allele.median()) if n else None}
nonpal = ok[~ok.palindromic]
sign = [signtest(ok, "all_found"), signtest(nonpal, "non_palindromic"),
        signtest(ok[ok.davies_p < 0.05], "davies_p<0.05"), signtest(ok[ok.davies_p < BONF], "davies_p<0.05/53"),
        signtest(ok[ok.qsnp_p >= 5e-8], "excluding_QSNP_SNP")]
fi_sign = {}
for lab in FI:
    d = s2[s2[f"{lab}_z_aligned"].notna()]
    fi_sign[lab] = {"n": len(d), "n_positive": int((d[f"{lab}_z_aligned"] > 0).sum()),
                    "binom_p_two_sided": float(stats.binomtest(int((d[f"{lab}_z_aligned"] > 0).sum()), len(d), .5).pvalue),
                    "mean_aligned_z": float(d[f"{lab}_z_aligned"].mean()),
                    "n_p_lt_0.05": int((d[f"{lab}_p"] < .05).sum()),
                    "n_p_lt_0.05_and_positive": int(((d[f"{lab}_p"] < .05) & (d[f"{lab}_z_aligned"] > 0)).sum())}
summary = {"created_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "davies_n_found": int(len(ok)), "n_palindromic": int(s2.palindromic.sum()),
           "classes": s2.overlap_class.value_counts().to_dict(), "null": null, "sign_concordance_davies": sign,
           "ukb_fluid_item_arithmetic_lookup": fi_sign,
           "davies_bonferroni_count": int((s2.davies_p < BONF).sum()), "davies_gws_count": int((s2.davies_p < 5e-8).sum()),
           "davies_nominal_count": int((s2.davies_p < 0.05).sum()),
           "corr_math_z_vs_davies_aligned_z_abs": None}
json.dump(summary, open(f"{ROOT}/data/sprint5/math53_summary.json", "w"), indent=1, default=float)
# (scratch pickle dropped when moved into the repo)
print(json.dumps(summary, indent=1, default=float))
