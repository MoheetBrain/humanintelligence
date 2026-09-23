"""Sprint 4 — shared locus tools: allele harmonisation, LD proxies, winner's-curse shrinkage.

Harmonisation rules are the frozen ones (research/sprint4/protocol.md):
  * match on rsID; alleles compared case-insensitively;
  * strand flips allowed only for non-palindromic SNPs;
  * palindromic (A/T, C/G) SNPs with effect-allele frequency in [0.40, 0.60] are
    UNRESOLVED_HARMONISATION (their strand cannot be inferred from frequency);
  * a lead absent from the target data is replaced by its best 1000G-EUR proxy with r^2 >= 0.8
    within 500 kb that is present in the target, the proxy allele being chosen by the sign of r;
  * otherwise NOT_TESTABLE — never "no effect".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import common as C

COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}
PALINDROMIC = {frozenset("AT"), frozenset("CG")}
PROXY_R2, PROXY_KB = 0.8, 500


def bh(p) -> np.ndarray:
    p = np.asarray(p, float)
    if len(p) == 0:
        return p
    order = np.argsort(p)
    q = p[order] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1)
    return out


def tweedie(z_all: np.ndarray, z_eval: np.ndarray) -> np.ndarray:
    """E[mu | z] = z + d/dz log f(z); f = Gaussian KDE of genome-wide z (frozen: every 50th SNP)."""
    kde = stats.gaussian_kde(z_all)
    h = 1e-3
    return z_eval + (np.log(kde(z_eval + h)) - np.log(kde(z_eval - h))) / (2 * h)


def ivw_slope(x: np.ndarray, y: np.ndarray) -> dict:
    """Slope through the origin of y on x (both z-scores; y has unit noise variance)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3:
        return {"slope": None, "se": None, "n": int(len(x))}
    b = float((x * y).sum() / (x * x).sum())
    se = float(1 / np.sqrt((x * x).sum()))
    return {"slope": b, "se": se, "z": b / se, "P_two_sided": float(2 * stats.norm.sf(abs(b / se))), "n": int(len(x))}


def align_sign(ea: str, oa: str, eaf: float, target: str, other: str) -> tuple[int, str]:
    """+1 if the sumstat effect allele is `target`, -1 if it is `other`, 0 with a reason otherwise."""
    ea, oa, target, other = (str(a).upper() for a in (ea, oa, target, other))
    if frozenset({target, other}) in PALINDROMIC:
        if eaf is not None and not pd.isna(eaf) and 0.40 <= float(eaf) <= 0.60:
            return 0, "UNRESOLVED_HARMONISATION"
        if ea == target and oa == other:
            return 1, "OK_PALINDROMIC_BY_FREQUENCY_BAND"
        if ea == other and oa == target:
            return -1, "OK_PALINDROMIC_BY_FREQUENCY_BAND"
        return 0, "ALLELE_MISMATCH"
    if ea == target and oa == other:
        return 1, "OK"
    if ea == other and oa == target:
        return -1, "OK"
    if COMP.get(ea) == target and COMP.get(oa) == other:
        return 1, "OK_STRAND_FLIP"
    if COMP.get(ea) == other and COMP.get(oa) == target:
        return -1, "OK_STRAND_FLIP"
    return 0, "ALLELE_MISMATCH"


_BIM = None


def bim() -> pd.DataFrame:
    global _BIM
    if _BIM is None:
        _BIM = pd.read_csv(str(C.BFILE) + ".bim", sep="\t", header=None, usecols=[0, 1, 3, 4, 5],
                           names=["chr", "snp", "pos", "a1", "a2"], dtype={"chr": str})
        _BIM["bed_index"] = np.arange(len(_BIM))
    return _BIM


def best_proxy(lead: str, cog: str, other: str, present: set[str]) -> dict | None:
    """Best proxy (r^2 >= 0.8, +/-500 kb) present in the target; returns its tagging alleles."""
    from bed_reader import open_bed
    b = bim()
    hit = b[b.snp == lead]
    if hit.empty:
        return None
    h = hit.iloc[0]
    win = b[(b.chr == h.chr) & (b.pos.between(h.pos - PROXY_KB * 1000, h.pos + PROXY_KB * 1000))
            & (b.snp.isin(present)) & (b.snp != lead)]
    if win.empty:
        return None
    idx = np.concatenate([[h.bed_index], win.bed_index.to_numpy()])
    with open_bed(str(C.BFILE) + ".bed") as bed:
        lo, hi = idx.min(), idx.max() + 1
        g = bed.read(index=np.s_[:, lo:hi], dtype="float32")[:, idx - lo]
    g = np.where(np.isnan(g), np.nanmean(g, axis=0), g)
    g = g - g.mean(axis=0)
    sd = g.std(axis=0)
    ok = sd > 0
    if not ok[0]:
        return None
    r = (g[:, 1:].T @ g[:, 0]) / (len(g) * sd[1:].clip(1e-12) * sd[0])
    r[~ok[1:]] = 0
    j = int(np.argmax(r ** 2))
    if r[j] ** 2 < PROXY_R2:
        return None
    s_lead = 1 if str(cog).upper() == h.a1 else (-1 if str(cog).upper() == h.a2 else 0)
    if s_lead == 0:
        return None
    p = win.iloc[j]
    tag_is_a1 = (r[j] * s_lead) > 0
    return {"snp": p.snp, "r2": float(r[j] ** 2), "tag": p.a1 if tag_is_a1 else p.a2,
            "other": p.a2 if tag_is_a1 else p.a1}


def lookup_loci(loci: pd.DataFrame, ss: pd.DataFrame, higher_is_better: bool, label: str) -> pd.DataFrame:
    """ss columns: SNP, EA, OA, EAF (optional), BETA, SE (or Z). Returns per-locus aligned z."""
    ss = ss.drop_duplicates("SNP", keep=False).set_index("SNP")
    present = set(ss.index)
    out = []
    for _, l in loci.iterrows():
        rec = {"locus_id": l.locus_id, "status": "NOT_TESTABLE", "used_snp": None, "proxy_r2": None,
               "aligned_z": np.nan, "one_sided_P": np.nan}
        cog = l.cognition_increasing_allele
        other = l.lead_other_allele if str(cog).upper() == str(l.lead_effect_allele).upper() else l.lead_effect_allele
        snp, target, tother, r2 = l.lead_snp, cog, other, 1.0
        if snp not in present:
            px = best_proxy(l.lead_snp, cog, other, present)
            if px is None:
                rec["status"] = "NOT_TESTABLE_ABSENT_NO_PROXY"
                out.append(rec)
                continue
            snp, target, tother, r2 = px["snp"], px["tag"], px["other"], px["r2"]
        row = ss.loc[snp]
        s, why = align_sign(row.EA, row.OA, row.get("EAF", np.nan), target, tother)
        rec.update({"used_snp": snp, "proxy_r2": r2 if snp != l.lead_snp else None})
        if s == 0:
            rec["status"] = why
            out.append(rec)
            continue
        z = float(row.Z) if "Z" in row.index and not pd.isna(row.get("Z", np.nan)) else float(row.BETA / row.SE)
        pol = 1 if higher_is_better else -1
        az = s * z * pol
        ab = s * float(row.BETA) * pol if "BETA" in row.index and not pd.isna(row.get("BETA", np.nan)) else np.nan
        rec.update({"status": "TESTABLE", "aligned_z": az, "one_sided_P": float(stats.norm.sf(az)),
                    "aligned_beta": ab, "se": float(row.SE) if "SE" in row.index else np.nan,
                    "harmonisation": why})
        out.append(rec)
    return pd.DataFrame(out).set_index("locus_id")


def positive_control(ss: pd.DataFrame, pub: dict) -> dict:
    hit = ss[ss.SNP == pub["snp"]]
    if hit.empty:
        return {"status": "ABSENT", "published": pub}
    r = hit.iloc[0]
    s, why = align_sign(r.A1, r.A2, r.A1FREQ, pub["effect_allele"], pub["other_allele"])
    beta = s * float(r.BETA)
    ok = (s != 0 and np.sign(beta) == np.sign(pub["beta"])
          and abs(beta - pub["beta"]) <= 0.1 * abs(pub["beta"]) + 0.001
          and 0.5 * pub["P"] <= float(r.P) <= 2 * pub["P"])
    return {"status": "PASS" if ok else "FAIL", "published": pub,
            "ours": {"effect_allele": pub["effect_allele"], "beta": beta, "se": float(r.SE), "P": float(r.P),
                     "file_A1": r.A1, "file_A2": r.A2, "A1FREQ": float(r.A1FREQ), "harmonisation": why},
            "rule": "same sign, |dbeta| <= 0.1|beta_pub| + 0.001, P within x2 (frozen)"}
