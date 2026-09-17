"""Identifier parsing, prefix/type compatibility and construction (contract §1).

Rejection cases matter more than acceptance cases here. An id that parses when it
should not is how a malformed node reaches the graph, and once there it looks exactly
like a real one.
"""

from __future__ import annotations

import pytest

from blueprint import ids, ontology


# ------------------------------------------------------------------ parsing ------

@pytest.mark.parametrize(
    ("node_id", "prefix", "local"),
    [
        ("GENE:GABRA5", "GENE", "GABRA5"),
        ("VAR:rs141426703", "VAR", "rs141426703"),
        ("VAR:chr1_1000_A_T", "VAR", "chr1_1000_A_T"),
        ("TX:ENST00000370447", "TX", "ENST00000370447"),
        ("PROT:P31644", "PROT", "P31644"),
        ("COMPLEX:eif2b", "COMPLEX", "eif2b"),
        ("PROC:GO:0006413", "PROC", "GO:0006413"),
        ("PATHWAY:REACT:R-HSA-72613", "PATHWAY", "REACT:R-HSA-72613"),
        ("CELL:CL:0000679", "CELL", "CL:0000679"),
        ("REGION:UBERON:0001954", "REGION", "UBERON:0001954"),
        ("SV:plasticity.ltp_threshold", "SV", "plasticity.ltp_threshold"),
        ("SVDOM:power", "SVDOM", "power"),
        ("PRIM:pattern_separation", "PRIM", "pattern_separation"),
        ("SPECIES:NCBITaxon:9606", "SPECIES", "NCBITaxon:9606"),
        # Two-segment source prefixes must win over any shorter match.
        ("SRC:PMID:29942086", "SRC:PMID", "29942086"),
        ("SRC:DOI:10.1038/s41588-018-0152-6", "SRC:DOI", "10.1038/s41588-018-0152-6"),
        ("SRC:NCT:NCT02024789", "SRC:NCT", "NCT02024789"),
        ("SRC:GCST:GCST006269", "SRC:GCST", "GCST006269"),
        ("SRC:DB:gwas_catalog:2026-09-13", "SRC:DB", "gwas_catalog:2026-09-13"),
        ("CLM:brakes:GABRA5:001", "CLM", "brakes:GABRA5:001"),
        ("EVD:brakes:GABRA5:001#1", "EVD", "brakes:GABRA5:001#1"),
        ("AUD:red_team:GABRA5:001", "AUD", "red_team:GABRA5:001"),
    ],
)
def test_parse_accepts_contract_examples(node_id: str, prefix: str, local: str) -> None:
    """Every identifier form the contract gives as an example must parse."""
    parsed = ids.parse(node_id)
    assert parsed.prefix == prefix
    assert parsed.local_id == local
    assert parsed.node_id == node_id


def test_slash_is_admitted_for_dois_only_at_the_charset_level() -> None:
    """A slash passes the coarse charset gate but not a node type's own pattern.

    Contract §1's declared charset omits ``/`` even though its own DOI examples need
    it, so the charset gate admits it (see the note in blueprint.ids) and the narrow
    ``id_pattern`` is what refuses it where it does not belong.
    """
    assert ids.is_valid("GENE:GAB/RA5"), "the coarse charset gate admits it"
    assert not ids.is_compatible("GENE:GAB/RA5", "Gene"), "the Gene pattern refuses it"
    assert ids.node_types_for("GENE:GAB/RA5") == []


@pytest.mark.parametrize(
    ("bad", "why"),
    [
        ("", "empty string"),
        ("GABRA5", "no prefix at all"),
        ("NOTAPREFIX:x", "undeclared prefix; prefixes are closed"),
        ("GENE:", "empty local id"),
        ("GENE", "prefix with no separator"),
        ("gene:GABRA5", "prefix is case-sensitive"),
        ("GENE:GAB RA5", "space is outside the local-id charset"),
        ("GENE:GAB\tRA5", "tab is outside the local-id charset"),
        ("GENE:GAB\nRA5", "newline is outside the local-id charset"),
        ("SRC:PMID:", "empty local id under a two-segment prefix"),
    ],
)
def test_parse_rejects(bad: str, why: str) -> None:
    """A malformed id must raise rather than be quietly accepted."""
    with pytest.raises(ids.IdError):
        ids.parse(bad)
    assert not ids.is_valid(bad), why


def test_parse_rejects_non_strings() -> None:
    """A non-string cannot be an identifier."""
    for value in (None, 42, [], {}):
        with pytest.raises(ids.IdError):
            ids.parse(value)  # type: ignore[arg-type]


# ------------------------------------------------- prefix/type compatibility -----

@pytest.mark.parametrize(
    ("node_id", "node_type"),
    [
        ("GENE:GABRA5", "Gene"),
        ("PROT:P31644", "Protein"),
        ("PROT:P31644", "Receptor"),
        ("PROT:P31644", "IonChannel"),
        ("PROT:GABRA5", "Protein"),
        ("SV:safety.seizure_risk", "StateVariable"),
        ("PRIM:pattern_separation", "ComputationalPrimitive"),
        ("SRC:PMID:29942086", "Paper"),
        ("SRC:NCT:NCT02024789", "ClinicalTrial"),
        ("CLM:brakes:GABRA5:001", "Claim"),
        ("EVD:brakes:GABRA5:001#1", "Measurement"),
        ("EVD:brakes:GABRA5:001#1", "Replication"),
        ("TGT:EIF2B_COMPLEX", "Target"),
        ("EFFECT:increased_working_memory_capacity", "DesiredEffect"),
        ("AE:seizure", "AdverseEffect"),
    ],
)
def test_compatible(node_id: str, node_type: str) -> None:
    """An id must be usable as the node type whose prefix and pattern accept it."""
    assert ids.is_compatible(node_id, node_type)
    ids.require_compatible(node_id, node_type)


@pytest.mark.parametrize(
    ("node_id", "node_type", "why"),
    [
        ("GENE:GABRA5", "Protein", "GENE is not a PROT prefix"),
        ("PROT:P31644", "Gene", "PROT is not a GENE prefix"),
        ("GENE:gabra5", "Gene", "HGNC symbols are upper case"),
        ("SV:notadomain.x", "StateVariable", "the domain segment is closed"),
        ("SV:safety", "StateVariable", "no name segment"),
        ("PRIM:PatternSeparation", "ComputationalPrimitive", "primitives are snake_case"),
        ("SPECIES:9606", "Species", "taxid must carry the NCBITaxon prefix"),
        ("SRC:NCT:NCT123", "ClinicalTrial", "an NCT id is eight digits"),
        ("SRC:PMID:29942086", "ClinicalTrial", "a PMID is not a trial registration"),
        ("CLM:brakes:GABRA5:1", "Claim", "the claim counter is zero-padded to three"),
        ("EVD:brakes:GABRA5:001", "Measurement", "an evidence id carries #n"),
        ("TX:ENST123", "Transcript", "an Ensembl transcript id is eleven digits"),
        ("REGION:uberon:0001954", "BrainRegion", "the UBERON prefix is upper case"),
    ],
)
def test_incompatible(node_id: str, node_type: str, why: str) -> None:
    """A wrong prefix or a malformed local id must be refused."""
    assert not ids.is_compatible(node_id, node_type), why
    with pytest.raises(ids.IdError):
        ids.require_compatible(node_id, node_type)


def test_subtype_is_not_a_supertype_shortcut() -> None:
    """A Protein id is legal as a Receptor because they SHARE a prefix and pattern.

    This is a deliberate consequence of the contract: ``PROT`` covers Protein and its
    four specialisations, so identifier compatibility cannot tell them apart. The
    distinction is carried by the record's declared node type, and triple legality
    resolves subtyping in :mod:`blueprint.ontology` — not here.
    """
    assert ids.is_compatible("PROT:P31644", "Protein")
    assert ids.is_compatible("PROT:P31644", "Enzyme")
    index = ontology.load()
    assert index.is_subtype_of("Enzyme", "Protein")
    assert not index.is_subtype_of("Protein", "Enzyme")


def test_require_compatible_message_is_actionable() -> None:
    """A curator fixing a record reads this message, not this file."""
    with pytest.raises(ids.IdError) as caught:
        ids.require_compatible("GENE:GABRA5", "Protein")
    message = str(caught.value)
    assert "GENE" in message and "Protein" in message
    assert "PROT" in message, "the message should name the prefix the node type accepts"


def test_unknown_node_type_raises() -> None:
    """A typo'd node type must not silently pass compatibility."""
    with pytest.raises(ids.IdError):
        ids.is_compatible("GENE:GABRA5", "NotANodeType")


# --------------------------------------------------------------- constructors ----

def test_constructors_build_valid_ids() -> None:
    """Constructors exist so an agent never has to remember a format."""
    assert ids.gene_id("gabra5") == "GENE:GABRA5"
    assert ids.target_id("gabra5") == "TGT:GABRA5"
    assert ids.state_variable_id("plasticity", "ltp_threshold") == "SV:plasticity.ltp_threshold"
    assert ids.state_domain_id("power") == "SVDOM:power"
    assert ids.primitive_id("pattern_separation") == "PRIM:pattern_separation"
    assert ids.species_id(9606) == "SPECIES:NCBITaxon:9606"
    assert ids.pmid_source_id(29942086) == "SRC:PMID:29942086"
    assert ids.nct_source_id("nct02024789") == "SRC:NCT:NCT02024789"
    assert ids.claim_id("brakes", "GABRA5", 1) == "CLM:brakes:GABRA5:001"
    assert ids.audit_id("red_team", "GABRA5", 1) == "AUD:red_team:GABRA5:001"


def test_doi_is_lowercased() -> None:
    """Contract §1.3: a DOI is registered lowercased, so one paper has one id."""
    assert ids.doi_source_id("10.1038/S41588-018-0152-6") == "SRC:DOI:10.1038/s41588-018-0152-6"


def test_evidence_id_is_derived_from_its_claim() -> None:
    """Contract §1.3: an evidence id is derived, never hand-written."""
    claim = ids.claim_id("brakes", "GABRA5", 1)
    assert ids.evidence_id(claim, 1) == "EVD:brakes:GABRA5:001#1"
    assert ids.claim_id_of_evidence("EVD:brakes:GABRA5:001#1") == claim


def test_evidence_id_rejects_a_non_claim_and_a_bad_index() -> None:
    """Deriving an evidence id from anything but a claim is a mistake worth raising on."""
    with pytest.raises(ids.IdError):
        ids.evidence_id("SRC:PMID:29942086", 1)
    with pytest.raises(ids.IdError):
        ids.evidence_id(ids.claim_id("brakes", "GABRA5", 1), 0)


def test_constructors_reject_malformed_input() -> None:
    """A constructor validates its own output rather than emitting a broken id."""
    with pytest.raises(ids.IdError):
        ids.state_variable_id("not_a_domain", "x")
    with pytest.raises(ids.IdError):
        ids.primitive_id("NotSnakeCase")
    with pytest.raises(ids.IdError):
        ids.gene_id("has a space")


# ------------------------------------------------------- accession reporting -----

def test_preferred_accession_detection() -> None:
    """Coverage of accession-grade identifiers must be countable, not assumed."""
    assert ids.uses_preferred_accession("PROT:P31644")
    assert not ids.uses_preferred_accession("PROT:GABRA5")
    assert ids.uses_preferred_accession("PROC:GO:0006413")
    assert not ids.uses_preferred_accession("PROC:translation_initiation")
    assert ids.uses_preferred_accession("REGION:UBERON:0001954")
    assert not ids.uses_preferred_accession("REGION:hippocampus")
    # A prefix with no accession form is always "preferred": there is nothing better.
    assert ids.uses_preferred_accession("SV:power.atp_adp_ratio")


def test_node_types_for_returns_every_accepting_type() -> None:
    """A PROT id denotes Protein and its specialisations; the caller disambiguates."""
    types = set(ids.node_types_for("PROT:P31644"))
    assert {"Protein", "Receptor", "IonChannel", "Transporter", "Enzyme"} <= types
    assert ids.node_types_for("GENE:gabra5") == [], "lower case must match nothing"


def test_fixture_root_is_honoured(empty_root) -> None:
    """Every function takes a root, so a test can point the library at a fixture tree."""
    assert ids.is_valid("GENE:GABRA5", empty_root)
    assert ids.gene_id("gabra5", empty_root) == "GENE:GABRA5"
