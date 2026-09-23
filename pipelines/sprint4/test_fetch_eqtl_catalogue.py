#!/usr/bin/env python3
"""Offline tests for pipelines/sprint4/fetch_eqtl_catalogue.py (no network).

Covers the parts whose silent failure would corrupt colocalisation input: which datasets count as
adult brain, which quant methods are gene-level, tabix-row parsing / gene + window filtering, the
streaming lbf line filter (chunk boundaries, multi-member gzip), and loci/window handling.

Run
---
    .venv/bin/python -m pytest pipelines/sprint4/test_fetch_eqtl_catalogue.py -q
"""

from __future__ import annotations

import gzip
import io
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_eqtl_catalogue as F  # noqa: E402

PATHS_TSV = """study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tftp_path\tftp_cs_path\tftp_lbf_path
QTS000015\tQTD000171\tGTEx\tbrain_cortex\tUBERON_0001870\tbrain (cortex)\tnaive\t205\tge\tftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/QTS000015/QTD000171/QTD000171.all.tsv.gz\tftp://x/cs.tsv.gz\tftp://x/lbf.txt.gz
QTS000015\tQTD000172\tGTEx\tbrain_cortex\tUBERON_0001870\tbrain (cortex)\tnaive\t205\texon\tftp://x/QTD000172.cc.tsv.gz\tftp://x/cs\tftp://x/lbf
QTS000015\tQTD000286\tGTEx\tnerve_tibial\tUBERON_0001323\ttibial nerve\tnaive\t532\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000015\tQTD000301\tGTEx\tpituitary\tUBERON_0000007\tpituitary\tnaive\t237\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000015\tQTD000116\tGTEx\tadipose_subcutaneous\tUBERON_0001013\tadipose\tnaive\t581\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000005\tQTD000051\tBrainSeq\tbrain\tUBERON_0009834\tbrain (DLPFC)\tnaive\t479\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000034\tQTD000579\tWalker_2019\tNeocortex\tUBERON_0001950\tneocortex\tnaive\t211\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000031\tQTD000559\tYoung_2019\tmicroglia_naive\tCL_0000129\tmicroglia\tnaive\t104\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000099\tQTD009999\tNewStudy_2030\tbrain_insula\tUBERON_0002022\tbrain (insula)\tnaive\t300\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000098\tQTD009998\tOrganoid_2031\tcortical_organoid_d90\tUBERON_9999999\tneural organoid\tnaive\t50\tge\tftp://x/a\tftp://x/b\tftp://x/c
QTS000006\tQTD000060\tSomeArray\tbrain_frontal\tUBERON_0009834\tbrain (DLPFC)\tnaive\t100\tmicroarray\tftp://x/a\tftp://x/b\tftp://x/c
"""
META_TSV = "dataset_id\tpmid\tstudy_type\nQTD000171\t32913098\tbulk\nQTD000051\t30050107\tbulk\n"

HEADER = F.SUMSTATS_COLUMNS


def _row(gene, pos, ref="A", alt="G", rsid="rs1", r2="NA", chrom="12", beta="0.1"):
    return "\t".join([gene, chrom, str(pos), ref, alt, f"chr{chrom}_{pos}_{ref}_{alt}", "5", "0.02",
                      "0.5", beta, "0.2", "SNP", "7", "410", r2, gene, gene, "10.5", rsid])


@pytest.fixture()
def table() -> pd.DataFrame:
    paths = pd.read_csv(io.StringIO(PATHS_TSV), sep="\t", dtype=str)
    meta = pd.read_csv(io.StringIO(META_TSV), sep="\t", dtype=str)
    return F.build_dataset_table(paths, meta).set_index("dataset_id")


# ---------------------------------------------------------------- tissue + adult classification
def test_tissue_class_keeps_only_nervous_system():
    assert F.tissue_class("UBERON_0001870", "brain (cortex)") == "BRAIN"
    assert F.tissue_class("UBERON_0006469", "brain (spinal cord)") == "SPINAL_CORD"
    assert F.tissue_class("UBERON_0001323", "tibial nerve") == "PERIPHERAL_NERVE"
    assert F.tissue_class("CL_0000129", "microglia") == "NEURAL_CELL_TYPE"
    assert F.tissue_class("UBERON_0000007", "pituitary") is None
    assert F.tissue_class("UBERON_0001013", "adipose") is None
    assert F.tissue_class("UBERON_0001225", "kidney (cortex)") is None
    assert F.tissue_class("UBERON_0002022", "brain (insula)") == "BRAIN"  # unseen id, brain label


def test_classify_adult_registry_and_guards():
    assert F.classify_adult("GTEx")[0] == F.ADULT
    assert F.classify_adult("ROSMAP")[0] == F.ADULT
    status, basis = F.classify_adult("BrainSeq")
    assert status == F.NON_ADULT and "495" in basis and "412" in basis
    assert F.classify_adult("Walker_2019")[0] == F.NON_ADULT
    assert F.classify_adult("Jerber_2021")[0] == F.NON_ADULT
    # unreviewed study: keyword guard or UNCERTAIN — never ADULT by default
    assert F.classify_adult("X_2030", "fetal_cortex", "neocortex")[0] == F.NON_ADULT
    assert F.classify_adult("X_2030", "iPSC_neuron_D30", "neuron")[0] == F.NON_ADULT
    assert F.classify_adult("X_2030", "brain_insula", "brain (insula)")[0] == F.UNCERTAIN


def test_every_registry_basis_cites_a_source():
    for study, (status, basis) in F.STUDY_AGE_EVIDENCE.items():
        assert status in (F.ADULT, F.NON_ADULT, F.UNCERTAIN), study
        assert "PMID" in basis or "GTEx Portal" in basis, study


def test_gene_level_flag():
    assert F.is_gene_level("ge") and F.is_gene_level("microarray")
    for q in ("exon", "tx", "txrev", "leafcutter", "aptamer", "majiq"):
        assert not F.is_gene_level(q)


def test_dataset_table_filters_and_flags(table):
    assert set(table.index) == {"QTD000171", "QTD000172", "QTD000286", "QTD000051", "QTD000579",
                                "QTD000559", "QTD009999", "QTD009998", "QTD000060"}  # no pituitary/adipose
    assert list(table.reset_index().columns) == F.TABLE_COLUMNS
    assert table.loc["QTD000171", "fetch_eligible"]
    assert table.loc["QTD000171", "sumstats_url"].startswith("https://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/")
    assert table.loc["QTD000171", "pmid"] == "32913098"
    assert not table.loc["QTD000172", "fetch_eligible"] and "not gene-level" in table.loc["QTD000172", "fetch_exclusion_reason"]
    assert not table.loc["QTD000286", "fetch_eligible"] and "peripheral nerve" in table.loc["QTD000286", "fetch_exclusion_reason"]
    assert table.loc["QTD000051", "adult_status"] == F.NON_ADULT and not table.loc["QTD000051", "fetch_eligible"]
    assert table.loc["QTD000579", "adult_status"] == F.NON_ADULT
    assert table.loc["QTD000559", "adult_status"] == F.ADULT and table.loc["QTD000559", "fetch_eligible"]
    assert table.loc["QTD009999", "adult_status"] == F.UNCERTAIN and not table.loc["QTD009999", "fetch_eligible"]
    assert table.loc["QTD009998", "adult_status"] == F.NON_ADULT  # organoid label guard
    assert table.loc["QTD000060", "gene_level_quant"] and table.loc["QTD000060", "adult_status"] == F.UNCERTAIN
    assert table["sample_size"].dtype.name == "Int64"


# ---------------------------------------------------------------- sumstats parsing
def test_header_check():
    assert F.parse_header_line("\t".join(HEADER) + "\n") == HEADER
    assert F.parse_header_line("\t".join(HEADER) + "\r\n") == HEADER  # real r7 files: CRLF header
    with pytest.raises(ValueError):
        F.parse_header_line("\t".join(reversed(HEADER)))


def test_parse_sumstats_filters_gene_and_window_and_types():
    text = "\n".join([
        _row("ENSG_A", 100, r2="0.95", rsid="rs1"),
        _row("ENSG_A", 100, r2="0.95", rsid="rs1b"),       # duplicate variant, second rsid: kept
        _row("ENSG_B", 150),                                # gene not listed
        _row("ENSG_A", 250),                                # outside window
        _row("ENSG_C", 200, chrom="12", beta="-0.3"),
    ]) + "\n"
    df = F.parse_sumstats_text(text, HEADER, ["ENSG_A", "ENSG_C"], "L1", "QTD1", "12", 50, 200)
    assert list(df.columns) == F.OUTPUT_COLUMNS
    assert len(df) == 3 and set(df["gene_id"]) == {"ENSG_A", "ENSG_C"}
    assert df["position"].between(50, 200).all()
    assert df.loc[df["gene_id"] == "ENSG_A", "r2"].eq(0.95).all()
    assert df.loc[df["gene_id"] == "ENSG_C", "r2"].isna().all()
    assert df.loc[df["gene_id"] == "ENSG_C", "beta"].iloc[0] == pytest.approx(-0.3)
    assert df["an"].dtype.name == "Int64" and df["position"].dtype.name == "int64"
    assert (df["locus_id"] == "L1").all() and (df["dataset_id"] == "QTD1").all()
    assert set(df["alt"]) == {"G"}  # ALT is the effect allele; kept verbatim


def test_parse_sumstats_empty_and_malformed():
    empty = F.parse_sumstats_text("", HEADER, ["ENSG_A"], "L1", "QTD1", "12", 1, 10)
    assert empty.empty and list(empty.columns) == F.OUTPUT_COLUMNS
    with pytest.raises(ValueError):
        F.parse_sumstats_text("ENSG_A\t12\t100\n", HEADER, ["ENSG_A"], "L1", "QTD1")


# ---------------------------------------------------------------- lbf streaming filter
LBF_HEADER = "\t".join(F.LBF_ID_COLUMNS + [f"lbf_variable{i}" for i in range(1, 11)])


def _lbf_line(gene, pos, chrom="3"):
    return "\t".join([gene, f"chr{chrom}:1-2000000", f"chr{chrom}_{pos}_A_G", chrom, str(pos)]
                     + [f"{-0.1 * i:.3f}" for i in range(1, 11)])


def test_line_filter_across_chunk_boundaries():
    payload = (LBF_HEADER + "\n" + "\n".join(
        [_lbf_line("ENSG_X", p) for p in range(1, 50)] + [_lbf_line("ENSG_KEEP", p) for p in (10, 20)]
        + [_lbf_line("ENSG_KEEPX", 30)]) + "\n").encode()
    for size in (1, 7, 64, 1000, len(payload)):
        flt = F.LineFilter(["ENSG_KEEP"])
        for i in range(0, len(payload), size):
            flt.feed(payload[i:i + size])
        flt.close()
        assert flt.header.decode() == LBF_HEADER
        assert len(flt.kept) == 2, size  # exact first-field match: ENSG_KEEPX excluded
        df = F.lbf_frame(flt.header, flt.kept)
        assert list(df["position"]) == [10, 20] and df.shape[1] == 15


def test_stream_gzip_multi_member_via_file_url(tmp_path):
    part1 = (LBF_HEADER + "\n" + _lbf_line("ENSG_KEEP", 5) + "\n").encode()
    part2 = (_lbf_line("ENSG_OTHER", 6) + "\n" + _lbf_line("ENSG_KEEP", 7) + "\n").encode()
    path = tmp_path / "x.lbf_variable.txt.gz"
    path.write_bytes(gzip.compress(part1) + gzip.compress(part2))  # two gzip members
    flt, stats = F.stream_gzip_lines(path.as_uri(), ["ENSG_KEEP"])
    assert len(flt.kept) == 2 and stats["bytes"] == path.stat().st_size
    assert stats["lines_scanned"] == 3


def test_lbf_frame_rejects_unexpected_header():
    with pytest.raises(ValueError):
        F.lbf_frame(b"gene\tpos", [])


# ---------------------------------------------------------------- loci + provenance helpers
def test_load_loci_and_window(tmp_path):
    csv = tmp_path / "loci.csv"
    csv.write_text("locus_id,chr,lead_snp,lead_pos_grch37,gene,ensembl_gene_id,lead_pos_grch38\n"
                   "L1,12,rs1,56403577,RPS26,ENSG00000197728,56009793\n"
                   "L1,12,rs1,56403577,ERBB3,ENSG00000065361,56009793\n"
                   "L2,chr1,rs2,72750353,NEGR1,ENSG00000172260,400000\n")
    loci = F.load_loci(csv)
    assert [l.locus_id for l in loci] == ["L1", "L2"]
    assert loci[0].genes == {"ENSG00000197728": "RPS26", "ENSG00000065361": "ERBB3"}
    F.set_window(loci[0], 500)
    assert loci[0].region == "12:55509793-56509793"
    F.set_window(loci[1], 500)
    assert loci[1].chrom == "1" and loci[1].window_start == 1  # clipped at chromosome start


def test_load_loci_rejects_inconsistent_lead(tmp_path):
    csv = tmp_path / "loci.csv"
    csv.write_text("locus_id,chr,lead_snp,lead_pos_grch37,ensembl_gene_id\n"
                   "L1,12,rs1,100,ENSG1\nL1,12,rs9,100,ENSG2\n")
    with pytest.raises(ValueError):
        F.load_loci(csv)


def test_default_loci_file_parses():
    loci = F.load_loci(F.C.DATA / "gate_c_query_genes_prespecified.csv")
    assert {l.locus_id for l in loci} == {"L257194", "L6857", "L91869", "L319"}


def test_ftp_to_https_and_merge_records():
    assert F.ftp_to_https("ftp://ftp.ebi.ac.uk/a/b.gz") == "https://ftp.ebi.ac.uk/a/b.gz"
    old = [{"kind": "sumstats", "locus_id": "L1", "dataset_id": "D1", "status": "FAILED"}]
    new = [{"kind": "sumstats", "locus_id": "L1", "dataset_id": "D1", "status": "OK"},
           {"kind": "lbf", "locus_id": "L1", "dataset_id": "D1", "status": "OK"}]
    merged = F.merge_file_records(old, new)
    assert len(merged) == 2 and all(r["status"] == "OK" for r in merged)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
