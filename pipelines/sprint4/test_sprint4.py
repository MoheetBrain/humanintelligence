"""Sprint 4 guards. Offline; synthetic fixtures where real data are restricted.

Covers the brief's list: frozen-set hashes; population/within-family dataset identity; effect-allele
harmonisation; no EA leakage; no UKB file counted as G&C independence; power-calibration
reproducibility; colocalisation direction logic; NOT_TESTABLE vs NO_EFFECT; the direction threshold
cannot change after result ingestion.
"""

from __future__ import annotations

import gzip
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import classify as K  # noqa: E402
import common as C  # noqa: E402
import loci_tools as LT  # noqa: E402


# ------------------------------------------------------------------ frozen protocol
def test_frozen_json_hash_matches_protocol():
    assert C.sha256_file(C.FROZEN_JSON) == C.recorded_frozen_hash()
    C.load_frozen()  # must not raise


def test_frozen_set_membership_hashes_recompute():
    frozen = C.load_frozen()
    sets = C.read_setannot()
    assert [s["set_id"] for s in frozen["frozen_sets"]] == list(C.FROZEN_SETS)
    for s in frozen["frozen_sets"]:
        assert C.gene_list_hash(sets[s["set_id"]]) == s["gene_list_sha256"], s["set_id"]
        assert C.gene_list_hash(s["entrez_ids"]) == s["gene_list_sha256"]


def test_changed_threshold_is_refused(tmp_path, monkeypatch):
    """Editing a threshold after the freeze must make every analysis refuse to run."""
    j = json.loads(C.FROZEN_JSON.read_text())
    j["rules"]["gate_c"]["direction_rule"]["min_sign_agreement"] = 0.75   # the NEGR1 temptation
    fake = tmp_path / "frozen.json"
    fake.write_text(json.dumps(j))
    monkeypatch.setattr(C, "FROZEN_JSON", fake)
    with pytest.raises(RuntimeError, match="changed since the freeze"):
        C.load_frozen()


def test_direction_threshold_values_are_the_sprint3_ones():
    d = C.load_frozen()["rules"]["gate_c"]["direction_rule"]
    assert (d["min_strong_gene_level_colocs"], d["min_sign_agreement"], d["strength_threshold"]) == (3, 0.8, 0.8)
    assert d["unchanged_from_sprint3"] is True


# ------------------------------------------------------------------ dataset identity
def test_opengwas_identity_matches_frozen_metadata():
    meta = json.loads((C.REPO_ROOT / "data/raw/sprint4/opengwas_metadata/gwasinfo_ieu-b-4837_4838.json").read_text())
    ds = C.load_frozen()["rules"]["gate_a"]["datasets"]
    for role in ("within_family", "population"):
        exp = ds[role]
        got = meta["entries"][exp["opengwas_id"]]
        for k in ("trait", "note", "sample_size", "build", "consortium", "author", "year"):
            assert got[k] == exp[k], (role, k)
    assert ds["within_family"]["note"] == "Sibling estimate" and ds["population"]["note"] == "Population estimate"


def _write_vcf(path: Path, sample_id: str, rows: list[tuple]) -> None:
    with gzip.open(path, "wt") as fh:
        fh.write("##fileformat=VCFv4.2\n")
        fh.write(f"##SAMPLE=<ID={sample_id},TotalVariants=3,StudyType=Continuous>\n")
        fh.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + sample_id + "\n")
        for chrom, pos, rsid, ref, alt, es, se, lp, af, ss in rows:
            fh.write(f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t.\tPASS\t.\tES:SE:LP:AF:SS:ID\t"
                     f"{es}:{se}:{lp}:{af}:{ss}:{rsid}\n")


def test_gwas_vcf_parse_identity_and_effective_n(tmp_path):
    import gate_a_within_family as GA
    rows_p = [(1, 100, "rs1", "A", "G", 0.02, 0.010, 1.3, 0.30, 22593),
              (1, 200, "rs2", "C", "T", -0.01, 0.012, 0.5, 0.50, 22593),
              (2, 300, "rs3", "G", "A", 0.00, 0.011, 0.1, 0.02, 22593)]
    rows_w = [(c, p, r, a, b, es / 2, se * 1.5, lp, af, 9997) for c, p, r, a, b, es, se, lp, af, ss in rows_p]
    _write_vcf(tmp_path / "pop.vcf.gz", "ieu-b-4838", rows_p)
    _write_vcf(tmp_path / "wf.vcf.gz", "ieu-b-4837", rows_w)
    pop, hp = GA.parse_gwas_vcf(tmp_path / "pop.vcf.gz")
    wf, hw = GA.parse_gwas_vcf(tmp_path / "wf.vcf.gz")
    assert GA.identity_check(hp, "ieu-b-4838") and GA.identity_check(hw, "ieu-b-4837")
    assert not GA.identity_check(hw, "ieu-b-4838"), "a swapped file must fail identity"
    assert pop.loc[0, "EA"] == "G" and pop.loc[0, "OA"] == "A", "ES refers to ALT"
    assert abs(pop.loc[0, "P"] - 10 ** -1.3) < 1e-12
    # SE ratio 1.5 on the two common SNPs -> N_eff = 22593 / 2.25
    assert abs(GA.effective_n(pop, wf, 22593) - 22593 / 2.25) < 1e-6


def test_gate_a_fetch_blocks_without_token(monkeypatch):
    import gate_a_within_family as GA
    monkeypatch.delenv("OPENGWAS_JWT", raising=False)
    st = GA.fetch()
    assert st["status"] == "BLOCKED" and "OPENGWAS_JWT" in st["blocker"]
    assert "minimal_user_action" in st


# ------------------------------------------------------------------ harmonisation
@pytest.mark.parametrize("ea,oa,eaf,target,other,exp", [
    ("A", "G", 0.3, "A", "G", 1), ("G", "A", 0.3, "A", "G", -1),
    ("T", "C", 0.3, "A", "G", 1),            # strand flip, non-palindromic
    ("A", "T", 0.45, "A", "T", 0),           # palindromic in the ambiguous band
    ("A", "T", 0.20, "A", "T", 1),           # palindromic outside the band
    ("A", "C", 0.3, "A", "G", 0)])           # mismatch
def test_align_sign(ea, oa, eaf, target, other, exp):
    assert LT.align_sign(ea, oa, eaf, target, other)[0] == exp


def test_trail_making_direction_is_inverted_for_cognition():
    """Higher trail-making time = worse: the cognition allele's aligned z is -BETA/SE."""
    loci = pd.DataFrame([{"locus_id": "L1", "lead_snp": "rs1", "cognition_increasing_allele": "A",
                          "lead_effect_allele": "A", "lead_other_allele": "G"}])
    ss = pd.DataFrame([{"SNP": "rs1", "EA": "A", "OA": "G", "EAF": 0.3, "BETA": -0.01, "SE": 0.005}])
    r = LT.lookup_loci(loci, ss, higher_is_better=False, label="TMA").loc["L1"]
    assert r.status == "TESTABLE" and r.aligned_z == pytest.approx(2.0)


# ------------------------------------------------------------------ independence / EA leakage
def test_ukb_and_meta_files_are_forbidden_for_independence():
    import gate_b_genc as GB
    rules = C.load_frozen()["rules"]["gate_b"]
    assert all("_gc" in f for f in rules["independent_files"])
    assert set(rules["forbidden_for_independence"]) >= {"tma_meta.txt", "tma_gwas_ukb.txt"}
    assert all(name not in rules["forbidden_for_independence"] for name in GB.PHENOS.values())
    assert all("ukb" not in n and "meta" not in n for n in GB.PHENOS.values())


def test_no_educational_attainment_input():
    frozen = C.load_frozen()
    blob = json.dumps(frozen["inputs"]).lower()
    assert "educational" not in blob and "attainment" not in blob
    sys.path.insert(0, str(C.REPO_ROOT / "pipelines" / "gene_tournament"))
    import build_consensus as bc
    assert bc.classify_trait("Educational attainment (years of education)") != "direct_cognition"
    assert bc.classify_trait("Intelligence") == "direct_cognition"


# ------------------------------------------------------------------ calibration reproducibility
def test_ld_noise_is_reproducible_and_ld_shaped():
    import power_calibration as PC
    bim = LT.bim()
    sub = bim[(bim.chr == "22") & (bim.pos.between(20_000_000, 20_050_000))].head(60).copy()
    sub["sign"] = 1
    sub["block"] = 7
    sub = sub.reset_index(drop=True)
    e1 = PC.ld_noise(sub, reps=3, seed=20260923)
    e2 = PC.ld_noise(sub, reps=3, seed=20260923)
    assert np.array_equal(e1, e2), "same seed must give identical noise"
    e3 = PC.ld_noise(sub, reps=3, seed=1)
    assert not np.array_equal(e1, e3)


# ------------------------------------------------------------------ classification / NOT_TESTABLE
def test_not_testable_is_never_no_effect():
    frozen = C.load_frozen()
    assert K.classify_set(None, None, None, frozen)["class"] == K.NOT_TESTABLE
    assert K.classify_locus_wf(float("nan"), None, "NOT_TESTABLE_ABSENT_NO_PROXY") == K.NOT_TESTABLE
    for f in ("within_family_synaptic_sets.csv", "within_family_locus_concordance.csv",
              "genc_independent_synaptic_sets.csv", "genc_independent_loci.csv", "direct_effect_survivors.csv",
              "negative_results.csv"):
        p = C.OUT / f
        if p.exists():
            t = pd.read_csv(p)
            for col in t.columns:
                if col in ("never_read_as",):
                    continue
                assert not t[col].astype(str).str.fullmatch("NO_EFFECT").any(), (f, col)


def test_set_classification_rules():
    frozen = C.load_frozen()
    exp = {"n_reps": 40, "median": 0.3, "q_low": 0.05, "q_high": 0.6, "power": 0.3}
    assert K.classify_set(0.2, 0.01, exp, frozen)["class"] == "DIRECT_EFFECT_SUPPORTED"
    assert K.classify_set(0.2, 0.2, exp, frozen)["class"] == "CONCORDANT_BUT_UNDERPOWERED"
    r = K.classify_set(-0.3, 0.9, exp, frozen)
    assert r["class"] == "INCONSISTENT" and r["subtype"] == "BEYOND_EXPECTED_NOISE"
    assert r["can_drive_pivot"] is False, "underpowered inconsistency cannot drive PIVOT"
    exp_lo = dict(exp, q_low=-0.5)
    r = K.classify_set(-0.1, 0.7, exp_lo, frozen)
    assert r["subtype"] == "SIGN_DISCORDANT_WITHIN_NOISE" and not r["can_drive_pivot"]
    assert K.classify_set(0.2, 0.01, exp, frozen, supported_label="INDEPENDENT_SUPPORT")["class"] == "INDEPENDENT_SUPPORT"


# ------------------------------------------------------------------ colocalisation direction logic
def test_coloc_harmonisation_expresses_qtl_effect_for_the_gwas_effect_allele():
    import gate_c_coloc as GC
    davies = pd.DataFrame([{"Markername": "rs1", "Effect_allele": "a", "Other_allele": "g", "Zscore": 5.0},
                           {"Markername": "rs2", "Effect_allele": "c", "Other_allele": "t", "Zscore": -5.0}])
    qtl = pd.DataFrame([{"rsid": "rs1", "ref": "G", "alt": "A", "beta": 0.4, "se": 0.1, "maf": 0.3},
                        {"rsid": "rs2", "ref": "C", "alt": "T", "beta": 0.4, "se": 0.1, "maf": 0.3}])
    h = GC.harmonise(qtl, davies).set_index("rsid")
    assert h.loc["rs1", "beta2"] == pytest.approx(0.4)    # ALT = effect allele
    assert h.loc["rs2", "beta2"] == pytest.approx(-0.4)   # ALT = other allele -> sign flipped
    # rs2: the effect allele C lowers cognition (z<0), so the cognition allele is T, whose QTL effect is +0.4
    cog_effect = h.loc["rs2", "beta2"] * (1 if h.loc["rs2", "Zscore"] > 0 else -1)
    assert cog_effect == pytest.approx(0.4)


def test_direction_rule_on_units():
    import gate_c_direction as GD
    rows = pd.DataFrame({"gene": ["G"] * 4, "dataset_id": ["d1", "d2", "d3", "d4"],
                         "cohort": ["gtex", "gtex", "rosmap", "rosmap"], "sign": [1, 1, 1, -1]})
    r = GD.resolve(rows, C.load_frozen())
    assert r["n_rows"] == 4 and r["row_agreement"] == 0.75 and not r["resolved_rows"]
    rows2 = rows.assign(sign=[1, 1, 1, 1], cohort=["gtex", "gtex", "rosmap", "rosmap"])
    r2 = GD.resolve(rows2, C.load_frozen())
    assert r2["resolved_rows"] and not r2["resolved_units"] and r2["label"] == "RESOLVED_ON_ROWS_ONLY_NOT_ROBUST"
