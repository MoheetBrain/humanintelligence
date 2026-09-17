"""Node identifier parsing, validation and construction (contract §1).

Design rules:

* Prefixes are CLOSED. They come from ``ontology/nodes.yaml``, never from a literal in
  this module, so adding a prefix is an ontology change and not a code change.
* Prefix resolution is LONGEST-MATCH, because the source prefixes have two segments
  (``SRC:PMID`` must win over a hypothetical ``SRC``).
* Every id is validated against the ``id_pattern`` of the node type it is used as, not
  merely against its prefix. ``PROT:P31644`` is a legal Protein id and a legal Receptor
  id; ``GENE:GABRA5`` is neither, and that is rule V2.
* Construction helpers exist so an agent never has to remember a format. They validate
  their output and raise, because a malformed id written into a record is far more
  expensive than a failed call.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from blueprint import ontology

# Contract §1 declares the local_id charset as [A-Za-z0-9._:+-]+, but two of the
# contract's OWN identifier forms cannot be written inside it:
#
#   * EVD ids are `{claim_local}#{n}` (§1.3) and need '#';
#   * DOIs contain '/' (and, per the DOI grammar, may contain ()<>[];), so
#     `SRC:DOI:10.1101/2021.01.01.425001` — the contract's own example — is
#     unwritable under the declared charset.
#
# This regex is therefore the declared set PLUS the characters the contract's examples
# require. It is a coarse gate against whitespace and control characters; the real gate
# is each node type's `id_pattern`, which is far narrower. Recorded as a deviation in
# docs/blackboard/schema_change_requests/ontology-001.yaml.
LOCAL_ID_CHARSET = re.compile(r"^[A-Za-z0-9._:+#/()<>\[\];-]+$")

# UniProt accession grammar, used to report how much of the graph is accession-grade
# rather than to accept or reject an id.
UNIPROT_RE = re.compile(
    r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[0-9]+)?$"
)

# Registry accession forms that the contract prefers over a slug fallback.
PREFERRED_ACCESSION_RE: dict[str, re.Pattern[str]] = {
    "PROT": UNIPROT_RE,
    "PROC": re.compile(r"^GO:[0-9]{7}$"),
    "PATHWAY": re.compile(r"^REACT:R-[A-Z]{3}-[0-9]+$"),
    "CELL": re.compile(r"^CL:[0-9]{7}$"),
    "REGION": re.compile(r"^UBERON:[0-9]{7}$"),
    "TX": re.compile(r"^ENST[0-9]{11}(?:\.[0-9]+)?$"),
    "VAR": re.compile(r"^rs[0-9]+$"),
    "CPD": re.compile(r"^CHEMBL[0-9]+$"),
    "DRUG": re.compile(r"^CHEMBL[0-9]+$"),
    "SPECIES": re.compile(r"^NCBITaxon:[0-9]+$"),
}


class IdError(ValueError):
    """Raised when an identifier is malformed or incompatible with a node type."""


class ParsedId(NamedTuple):
    """An identifier split into its prefix and local part."""

    node_id: str
    prefix: str
    local_id: str


@lru_cache(maxsize=8)
def _prefixes_longest_first(root: Path | str | None = None) -> tuple[str, ...]:
    """Declared prefixes, longest first, so ``SRC:PMID`` beats any shorter match."""
    return tuple(sorted(ontology.load(root).prefixes, key=len, reverse=True))


def parse(node_id: str, root: Path | str | None = None) -> ParsedId:
    """Split ``node_id`` into prefix and local id.

    Raises :class:`IdError` when the string carries no declared prefix, has an empty
    local part, or uses characters outside the contract's local-id charset.
    """
    if not isinstance(node_id, str) or not node_id:
        raise IdError(f"not an identifier: {node_id!r}")
    for prefix in _prefixes_longest_first(root):
        if node_id.startswith(prefix + ":"):
            local = node_id[len(prefix) + 1 :]
            if not local:
                raise IdError(f"{node_id!r} has prefix {prefix!r} but an empty local id")
            if not LOCAL_ID_CHARSET.match(local):
                raise IdError(
                    f"{node_id!r} local id {local!r} uses characters outside the "
                    "contract §1 charset [A-Za-z0-9._:+#-]"
                )
            return ParsedId(node_id=node_id, prefix=prefix, local_id=local)
    raise IdError(
        f"{node_id!r} does not start with a declared prefix. Prefixes are closed "
        "(contract §1); adding one is an ontology change."
    )


def prefix_of(node_id: str, root: Path | str | None = None) -> str:
    """The declared prefix of ``node_id``."""
    return parse(node_id, root).prefix


def local_id_of(node_id: str, root: Path | str | None = None) -> str:
    """The local part of ``node_id``."""
    return parse(node_id, root).local_id


def is_valid(node_id: str, root: Path | str | None = None) -> bool:
    """Whether ``node_id`` carries a declared prefix and a well-formed local id."""
    try:
        parse(node_id, root)
    except IdError:
        return False
    return True


def node_types_for(node_id: str, root: Path | str | None = None) -> list[str]:
    """Node type names whose prefix list and ``id_pattern`` both accept ``node_id``.

    An empty result means the id is syntactically parseable but matches no node type,
    which is exactly the rule V2 failure mode ("prefix legal, form wrong").
    """
    index = ontology.load(root)
    prefix = parse(node_id, root).prefix
    return [
        name
        for name in index.node_types_for_prefix(prefix)
        if index.compiled_id_pattern(name).match(node_id)
    ]


def is_compatible(node_id: str, node_type: str, root: Path | str | None = None) -> bool:
    """Whether ``node_id`` may be used as an instance of ``node_type``.

    Accepts a subtype's id for its parent type only through the node type's own
    declared prefixes and pattern; it does NOT accept a parent's id where a subtype is
    required, because a Protein is not thereby a Receptor.
    """
    index = ontology.load(root)
    if node_type not in index.nodes:
        raise IdError(f"unknown node type {node_type!r}")
    try:
        prefix = parse(node_id, root).prefix
    except IdError:
        return False
    if prefix not in index.nodes[node_type].id_prefixes:
        return False
    return bool(index.compiled_id_pattern(node_type).match(node_id))


def require_compatible(node_id: str, node_type: str, root: Path | str | None = None) -> None:
    """Raise :class:`IdError` with an actionable message when incompatible."""
    index = ontology.load(root)
    if node_type not in index.nodes:
        raise IdError(f"unknown node type {node_type!r}")
    spec = index.nodes[node_type]
    if is_compatible(node_id, node_type, root):
        return
    try:
        prefix = parse(node_id, root).prefix
    except IdError as exc:
        raise IdError(f"{node_id!r} cannot be a {node_type}: {exc}") from exc
    if prefix not in spec.id_prefixes:
        raise IdError(
            f"{node_id!r} uses prefix {prefix!r}, but node type {node_type} accepts "
            f"{sorted(spec.id_prefixes)}. Legal types for {prefix!r}: "
            f"{sorted(index.node_types_for_prefix(prefix))}"
        )
    raise IdError(
        f"{node_id!r} has the right prefix for {node_type} but does not match its "
        f"id_pattern {spec.id_pattern!r} (contract §1)"
    )


def uses_preferred_accession(node_id: str, root: Path | str | None = None) -> bool:
    """Whether ``node_id`` uses the registry accession the contract prefers.

    Reporting only. Several prefixes permit a slug fallback; this distinguishes
    ``PROT:P31644`` from ``PROT:GABRA5`` so coverage of accession-grade identifiers can
    be counted honestly instead of assumed.
    """
    parsed = parse(node_id, root)
    pattern = PREFERRED_ACCESSION_RE.get(parsed.prefix)
    if pattern is None:
        return True
    return bool(pattern.match(parsed.local_id))


# ------------------------------------------------------------- constructors ------

def _built(node_id: str, node_type: str, root: Path | str | None) -> str:
    """Validate a constructed id against its node type before returning it."""
    require_compatible(node_id, node_type, root)
    return node_id


def gene_id(symbol: str, root: Path | str | None = None) -> str:
    """``GENE:{symbol}`` from an HGNC-approved symbol (uppercased)."""
    return _built(f"GENE:{symbol.strip().upper()}", "Gene", root)


def target_id(symbol: str, root: Path | str | None = None) -> str:
    """``TGT:{symbol}`` from a gene symbol or complex slug (uppercased)."""
    return _built(f"TGT:{symbol.strip().upper()}", "Target", root)


def state_variable_id(domain: str, name: str, root: Path | str | None = None) -> str:
    """``SV:{domain}.{name}`` for a declared state domain."""
    return _built(f"SV:{domain.strip()}.{name.strip()}", "StateVariable", root)


def state_domain_id(domain: str, root: Path | str | None = None) -> str:
    """``SVDOM:{domain}`` for a declared state domain."""
    return _built(f"SVDOM:{domain.strip()}", "StateDomain", root)


def primitive_id(name: str, root: Path | str | None = None) -> str:
    """``PRIM:{name}`` for a computational primitive."""
    return _built(f"PRIM:{name.strip()}", "ComputationalPrimitive", root)


def species_id(taxid: int | str, root: Path | str | None = None) -> str:
    """``SPECIES:NCBITaxon:{taxid}``; the taxid must come from a tool response."""
    return _built(f"SPECIES:NCBITaxon:{taxid}", "Species", root)


def pmid_source_id(pmid: int | str, root: Path | str | None = None) -> str:
    """``SRC:PMID:{pmid}``. Preferred over DOI whenever a PMID exists (§1.3)."""
    return _built(f"SRC:PMID:{pmid}", "Paper", root)


def doi_source_id(doi: str, root: Path | str | None = None) -> str:
    """``SRC:DOI:{doi}`` with the DOI lowercased, as the contract requires."""
    return _built(f"SRC:DOI:{doi.strip().lower()}", "Paper", root)


def nct_source_id(nct: str, root: Path | str | None = None) -> str:
    """``SRC:NCT:{nct}`` for a registered clinical trial."""
    return _built(f"SRC:NCT:{nct.strip().upper()}", "ClinicalTrial", root)


def claim_id(domain: str, topic: str, number: int, root: Path | str | None = None) -> str:
    """``CLM:{domain}:{topic}:{nnn}`` with ``number`` zero-padded to three digits."""
    return _built(f"CLM:{domain}:{topic}:{number:03d}", "Claim", root)


def evidence_id(claim: str, index: int, root: Path | str | None = None) -> str:
    """``EVD:{claim_local}#{index}`` derived from a claim id — never hand-written."""
    parsed = parse(claim, root)
    if parsed.prefix != "CLM":
        raise IdError(f"evidence ids derive from a claim id, got {claim!r}")
    if index < 1:
        raise IdError(f"evidence index is 1-based, got {index!r}")
    return _built(f"EVD:{parsed.local_id}#{index}", "Measurement", root)


def audit_id(auditor: str, scope_slug: str, number: int, root: Path | str | None = None) -> str:
    """``AUD:{auditor}:{scope_slug}:{nnn}``."""
    return _built(f"AUD:{auditor}:{scope_slug}:{number:03d}", "Audit", root)


def claim_id_of_evidence(evidence: str, root: Path | str | None = None) -> str:
    """Recover the parent claim id from an evidence item id."""
    parsed = parse(evidence, root)
    if parsed.prefix != "EVD" or "#" not in parsed.local_id:
        raise IdError(f"not an evidence item id: {evidence!r}")
    return f"CLM:{parsed.local_id.split('#', 1)[0]}"
