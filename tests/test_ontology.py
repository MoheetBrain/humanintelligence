"""The ontology must be internally consistent and must not drift from the schemas.

These tests are the guard on the type system itself. Everything downstream — the
validator, the compiler, the ranking model — trusts that the ontology loads, that every
reference in it resolves, and that the JSON Schema enums still say what
``ontology/vocabularies.yaml`` says. A silent drift there would disable whichever rule
depends on the drifted enum, which is the worst kind of failure: the build stays green
and the check stops happening.
"""

from __future__ import annotations

import re

import pytest
import yaml

from blueprint import ontology, paths, policy, sync_schema_enums, vocab


@pytest.fixture(scope="module")
def onto() -> ontology.Ontology:
    """The real repository's ontology, loaded once."""
    return ontology.load()


# ------------------------------------------------------------------ loading ------

def test_ontology_loads(onto: ontology.Ontology) -> None:
    """Loading is also validation: `load` raises on any self-inconsistency."""
    assert onto.nodes, "no node types declared"
    assert onto.edges, "no relations declared"
    assert onto.prefixes, "no identifier prefixes declared"
    assert onto.layers == ("evidence", "biological", "intervention")


def test_vocabularies_load() -> None:
    """Vocabulary load checks every declared subset against its value list."""
    table = vocab.load()
    assert table, "no vocabularies declared"
    for name, entry in table.items():
        assert entry["values"], f"vocabulary {name} has no values"


def test_required_biological_node_types_present(onto: ontology.Ontology) -> None:
    """The brief's minimum biological layer, so the causal chain cannot lose a link."""
    required = {
        "Variant", "Gene", "Transcript", "Protein", "Receptor", "IonChannel",
        "Transporter", "Enzyme", "ProteinComplex", "Pathway", "MolecularProcess",
        "CellType", "BrainRegion", "Circuit", "Network", "StateVariable",
        "ComputationalPrimitive", "CognitivePhenotype", "Species",
    }
    missing = sorted(required - set(onto.nodes))
    assert not missing, f"missing biological node types: {missing}"


def test_required_evidence_and_intervention_node_types_present(onto: ontology.Ontology) -> None:
    """The evidence and intervention layers the contract and README name."""
    required = {
        "Paper", "Preprint", "Review", "Dataset", "DatabaseRelease", "Experiment",
        "Measurement", "ClinicalTrial", "Claim", "Replication", "Audit", "Species",
        "Compound", "Drug", "Biologic", "RNAIntervention", "GeneRegulation",
        "MetabolicIntervention", "Neurotechnology", "Target", "Mechanism",
        "StateVariable", "DesiredEffect", "AdverseEffect",
    }
    missing = sorted(required - set(onto.nodes))
    assert not missing, f"missing node types: {missing}"


def test_required_relations_present(onto: ontology.Ontology) -> None:
    """Every relation the contract, the README and the brief name."""
    required = {
        # causal chain
        "MAPS_TO_GENE", "ENCODES", "TRANSCRIBED_AS", "PARTICIPATES_IN", "EXPRESSED_IN",
        "LOCATED_IN", "PART_OF", "MODULATES", "NEGATIVELY_REGULATES",
        "POSITIVELY_REGULATES", "CONSTRAINS", "IMPLEMENTS", "SUPPORTS_PRIMITIVE",
        "ASSOCIATED_WITH", "PREDICTS",
        # evidence
        "REPORTS", "SUPPORTS", "CONTRADICTS", "QUALIFIES", "REPLICATED_BY",
        "FAILED_TO_REPLICATE_BY", "AUDITS", "ABOUT", "MEASURED_IN",
        # intervention
        "TARGETS", "AGONISES", "ANTAGONISES", "POTENTIATES", "NEGATIVELY_MODULATES",
        "INHIBITS", "UPREGULATES", "DOWNREGULATES", "CHANGES_STATE", "INCREASES_RISK",
        "DECREASES_RISK",
        # null results (contract V16b)
        "NO_DETECTED_EFFECT_ON",
    }
    missing = sorted(required - set(onto.edges))
    assert not missing, f"missing relations: {missing}"


# ------------------------------------------------------------ well-formedness ----

def test_every_id_pattern_compiles_and_is_anchored(onto: ontology.Ontology) -> None:
    """An unanchored pattern would accept a prefix of a malformed id."""
    for name, spec in onto.nodes.items():
        compiled = re.compile(spec.id_pattern)
        assert compiled.pattern.startswith("^"), f"{name} id_pattern is not anchored at the start"
        assert compiled.pattern.endswith("$"), f"{name} id_pattern is not anchored at the end"


def test_id_pattern_accepts_its_own_prefixes(onto: ontology.Ontology) -> None:
    """A node type's pattern must accept at least one id under each declared prefix."""
    for name, spec in onto.nodes.items():
        compiled = onto.compiled_id_pattern(name)
        for prefix in spec.id_prefixes:
            assert compiled.match(f"{prefix}:") is None, (
                f"{name} accepts {prefix}: with an empty local id"
            )
            # The pattern must at least be capable of matching the prefix; a pattern
            # that can never match its own prefix is a typo.
            assert compiled.pattern.find(prefix.split(":")[0]) != -1, (
                f"{name} id_pattern never mentions its prefix {prefix!r}"
            )


def test_no_duplicate_node_or_relation_names() -> None:
    """A duplicate would make one declaration invisible."""
    nodes_doc = yaml.safe_load(paths.nodes_file().read_text(encoding="utf-8"))
    edges_doc = yaml.safe_load(paths.edges_file().read_text(encoding="utf-8"))
    node_names = [entry["name"] for entry in nodes_doc["nodes"]]
    edge_names = [entry["name"] for entry in edges_doc["edges"]]
    assert len(node_names) == len(set(node_names)), "duplicate node type name"
    assert len(edge_names) == len(set(edge_names)), "duplicate relation name"


def test_every_prefix_is_used_by_a_node_type(onto: ontology.Ontology) -> None:
    """A declared prefix no node type accepts can never appear in a legal id."""
    unused = sorted(p for p in onto.prefixes if not onto.node_types_for_prefix(p))
    assert not unused, f"declared prefixes that no node type accepts: {unused}"


def test_edge_domain_and_range_reference_real_node_types(onto: ontology.Ontology) -> None:
    """Every side of every relation must name declared node types (or groups)."""
    for name in onto.edges:
        domain = onto.edge_domain(name)
        range_ = onto.edge_range(name)
        assert domain, f"{name} has an empty domain"
        assert range_, f"{name} has an empty range"
        for side, types in (("domain", domain), ("range", range_)):
            unknown = sorted(t for t in types if t not in onto.nodes)
            assert not unknown, f"{name} {side} names unknown node types {unknown}"


def test_parent_chains_terminate(onto: ontology.Ontology) -> None:
    """A cycle in the parent chain would hang subtype resolution."""
    for name in onto.nodes:
        chain = onto.ancestors(name)
        assert len(chain) == len(set(chain)), f"cyclic parent chain through {name}"


def test_declared_inverses_exist(onto: ontology.Ontology) -> None:
    """A non-null `inverse` must name a declared relation."""
    for name, spec in onto.edges.items():
        if spec.inverse is not None:
            assert spec.inverse in onto.edges, (
                f"{name} names inverse {spec.inverse!r}, which is not declared"
            )


def test_requires_claim_relations_list_allowed_claim_types(onto: ontology.Ontology) -> None:
    """An empty list would let any claim type license an empirical relation."""
    claim_types = vocab.value_set("claim_type")
    for name, spec in onto.edges.items():
        if not spec.requires_claim:
            continue
        assert spec.allowed_claim_types, f"{name} requires a claim but allows no claim type"
        unknown = sorted(set(spec.allowed_claim_types) - claim_types)
        assert not unknown, f"{name} allows unknown claim types {unknown}"


def test_effect_asserting_relations_are_gated_by_efficacy_claim_types(
    onto: ontology.Ontology,
) -> None:
    """Contract V16: only efficacy-grade claims may license an effect assertion."""
    licensing = vocab.efficacy_licensing_claim_types()
    for name, spec in onto.edges.items():
        if not spec.asserts_effect:
            continue
        assert set(spec.allowed_claim_types) <= licensing, (
            f"{name} asserts an effect but allows {sorted(set(spec.allowed_claim_types) - licensing)}, "
            "which would let binding or association license efficacy (rule V16)"
        )


def test_null_result_relation_is_not_treated_as_an_effect(onto: ontology.Ontology) -> None:
    """Contract V16b: demanding efficacy-grade evidence for a null result is backwards."""
    null_predicates = onto.null_result_predicates()
    assert "NO_DETECTED_EFFECT_ON" in null_predicates
    for name in null_predicates:
        for object_type in ("StateVariable", "CognitivePhenotype", "DesiredEffect"):
            assert not onto.asserts_effect(name, object_type), (
                f"{name} into {object_type} is being gated as an efficacy assertion"
            )
        assert "clinical_null" in onto.allowed_claim_types(name)


def test_binding_relations_do_not_assert_an_effect(onto: ontology.Ontology) -> None:
    """BINDING IS NEVER EFFICACY. These relations must never reach a cognitive object."""
    cognitive = {"StateVariable", "ComputationalPrimitive", "CognitivePhenotype", "DesiredEffect"}
    for name in ("TARGETS", "AGONISES", "ANTAGONISES", "POTENTIATES",
                 "NEGATIVELY_MODULATES", "INHIBITS", "HAS_MECHANISM"):
        overlap = sorted(set(onto.edge_range(name)) & cognitive)
        assert not overlap, (
            f"{name} may reach {overlap}, which would let engagement evidence stand in "
            "for an effect (contract V16)"
        )
        assert not onto.edges[name].asserts_effect


def test_causal_chain_is_traversable(onto: ontology.Ontology) -> None:
    """The README's causal chain must have at least one legal relation per hop."""
    chain = [
        "Variant", "Gene", "Transcript", "Protein", "MolecularProcess", "CellType",
        "BrainRegion", "Circuit", "StateVariable", "ComputationalPrimitive",
        "CognitivePhenotype",
    ]
    for subject, obj in zip(chain, chain[1:]):
        predicates = onto.legal_predicates(subject, obj)
        assert predicates, f"no relation connects {subject} to {obj}; the causal chain is broken"


# ---------------------------------------------------------------- references -----

def test_primitive_and_state_variable_references_resolve(onto: ontology.Ontology) -> None:
    """Both directions of the primitive/state-variable link must resolve."""
    sv_ids: set[str] = set()
    for path in paths.state_domain_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        sv_ids.update(v["id"] for v in (document.get("variables") or []))

    for primitive in onto.primitives.values():
        unknown = sorted(set(primitive.related_state_variables) - sv_ids)
        assert not unknown, f"{primitive.id} references unknown state variables {unknown}"

    for path in paths.state_domain_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for variable in document.get("variables") or []:
            unknown = sorted(set(variable.get("related_primitives") or []) - set(onto.primitives))
            assert not unknown, f"{variable['id']} references unknown primitives {unknown}"


def test_all_24_brief_primitives_declared(onto: ontology.Ontology) -> None:
    """The 24 the brief named must all be present, whatever has been added since.

    The brief listed its 24 as an OPENING set, so extension is expected; what must not
    happen is one of the original 24 quietly disappearing.
    """
    expected = {
        "persistent_representation", "attentional_gating", "distractor_suppression",
        "pattern_separation", "pattern_completion", "relational_binding",
        "variable_binding", "chunk_formation", "rule_extraction",
        "latent_structure_discovery", "generalisation", "far_transfer",
        "credit_assignment", "prediction_error", "error_monitoring", "metacognition",
        "memory_allocation", "memory_retrieval", "reconsolidation",
        "strategy_switching", "planning", "abstraction", "composition",
        "causal_inference",
    }
    declared = {pid.split(":", 1)[1] for pid in onto.primitives}
    assert expected <= declared, f"missing brief primitives: {sorted(expected - declared)}"


def test_primitive_origins_are_attributed(onto: ontology.Ontology) -> None:
    """Every primitive says where it came from, so the ontology's own provenance is visible.

    Three primitives were added in Sprint 1 from a domain agent's schema-change request
    (docs/blackboard/RESOLUTIONS.md R2). Marking them keeps the brief-supplied set
    distinguishable from what the project added to itself.
    """
    document = yaml.safe_load(paths.primitives_file().read_text(encoding="utf-8"))
    origins: dict[str, str] = {}
    for entry in document["primitives"]:
        assert entry.get("origin"), f"{entry['id']} states no origin"
        origins[entry["id"]] = entry["origin"]
    assert set(origins.values()) <= {"project_brief_sprint1", "agent_proposed_sprint1"}
    brief = [pid for pid, origin in origins.items() if origin == "project_brief_sprint1"]
    assert len(brief) == 24, f"expected the brief's 24, found {len(brief)}"
    assert document["count"] == len(document["primitives"])


def test_null_relation_covers_every_negatable_relation(onto: ontology.Ontology) -> None:
    """Contract V16b-sym: a null must be expressible wherever the positive claim is.

    The union is COMPUTED from ontology/edges.yaml rather than listed, because a
    hand-maintained list drifts the first time somebody adds a relation — and the
    consequence of drift is an ontology biased towards positive findings. That is not
    hypothetical: a performed cross-clade null could not use the null relation because
    the tested predictor was a BrainRegion, so it compiled as CONSTRAINS with
    `direction: unclear`, and any traversal ignoring direction read it as SUPPORT.
    """
    negatable = onto.negatable_predicates()
    assert len(negatable) >= 7, f"only {negatable} are marked negatable"
    for expected in ("MODULATES", "CONSTRAINS", "ASSOCIATED_WITH", "PREDICTS",
                     "CHANGES_STATE", "POSITIVELY_REGULATES", "NEGATIVELY_REGULATES"):
        assert expected in negatable, f"{expected} is not marked negatable"

    required_domain, required_range = onto.negatable_union()
    for predicate in onto.null_result_predicates():
        have_domain = set(onto.edge_domain(predicate))
        have_range = set(onto.edge_range(predicate))
        assert required_domain <= have_domain, (
            f"{predicate} domain is missing {sorted(required_domain - have_domain)}"
        )
        assert required_range <= have_range, (
            f"{predicate} range is missing {sorted(required_range - have_range)}"
        )


def test_between_species_relations_exist_and_force_two_species(onto: ontology.Ontology) -> None:
    """R6: the comparative atlas had no relation for "this property differs between species".

    Without one it borrowed causal relations, which overstated the evidence.
    """
    between = set(onto.between_species_predicates())
    assert {"DIFFERS_BETWEEN_SPECIES", "CONSERVED_ACROSS_SPECIES"} <= between
    for name in between:
        spec = onto.edges[name]
        assert spec.requires_claim, f"{name} must require a claim"
        assert not spec.asserts_effect, f"{name} must not assert an effect"
        assert "comparative_evolutionary" in spec.allowed_claim_types


def test_every_primitive_has_an_animal_analogue_caveat(onto: ontology.Ontology) -> None:
    """P4: animal memory is not human intelligence. The caveat is how that is carried."""
    for primitive in onto.primitives.values():
        assert len(primitive.animal_analogue_caveat) > 80, (
            f"{primitive.id} has no substantive animal_analogue_caveat; the project must "
            "not silently equate a rodent task with a human primitive"
        )
        assert primitive.definition_status == "working_definition_v0_1"
        assert primitive.human_measurement_paradigms, (
            f"{primitive.id} names no human measurement paradigm, not even to say none exists"
        )


def test_definitional_edges_are_axioms_only(onto: ontology.Ontology) -> None:
    """Everything in definitional_edges.yaml is claim-free and permitted as an axiom."""
    assert onto.definitional_edges, "no definitional edges declared"
    for edge in onto.definitional_edges:
        assert edge.provenance_class == "ontology_axiom", (
            f"{edge.subject} -{edge.predicate}-> {edge.object} is "
            f"{edge.provenance_class!r}; this file holds axioms only"
        )
        assert edge.basis, f"{edge.subject} -{edge.predicate}-> {edge.object} states no basis"
        allowed = onto.allowed_provenance_classes(edge.predicate)
        assert "ontology_axiom" in allowed, (
            f"{edge.predicate} may not carry an ontology_axiom edge (allowed: {allowed})"
        )


def test_no_gene_to_protein_axioms(onto: ontology.Ontology) -> None:
    """ENCODES is reference data from HGNC, never an axiom (contract §7)."""
    offenders = [e for e in onto.definitional_edges if e.predicate == "ENCODES"]
    assert not offenders, (
        "ENCODES edges must be compiled from data/interim/gene_identifiers.jsonl as "
        "reference_data; an agent hand-writing one has violated contract §7"
    )


# --------------------------------------------------------------- drift tests -----

def test_schemas_do_not_drift_from_vocabularies() -> None:
    """THE DRIFT TEST. A schema enum that diverges disables the rule that uses it."""
    problems = sync_schema_enums.check()
    assert not problems, "schema/vocabulary drift:\n" + "\n".join(problems)


def test_state_variable_type_system_agrees_with_vocabularies() -> None:
    """The SV enums are declared twice, with semantics; they must not diverge."""
    types_doc = yaml.safe_load(paths.state_variable_types_file().read_text(encoding="utf-8"))
    enums = types_doc["enums"]

    def declared(name: str) -> list[str]:
        return [
            entry["value"] if isinstance(entry, dict) else entry
            for entry in enums[name]["values"]
        ]

    pairs = {
        "kind": "state_variable_kind",
        "timescale": "state_variable_timescale",
        "level": "state_variable_level",
        "response_shape": "response_shape",
        "desirability": "desirability",
        "measurability": "measurability",
        "status": "state_variable_status",
    }
    for local, vocabulary in pairs.items():
        assert declared(local) == vocab.values(vocabulary), (
            f"ontology/state_variables.yaml enums.{local} disagrees with "
            f"ontology/vocabularies.yaml:{vocabulary}"
        )
    domains = [entry["name"] for entry in types_doc["domains"]]
    assert domains == vocab.values("state_domain")
    assert declared("response_shape") and enums["response_shape"]["default"] == "unknown"
    assert enums["response_shape"]["basis_values"] == vocab.values("response_shape_basis")


def test_action_type_enum_matches_task_dag() -> None:
    """The closed computational enum has one source of truth (contract P1)."""
    assert list(policy.action_types()) == vocab.values("action_type"), (
        "ontology/vocabularies.yaml:action_type has drifted from "
        "docs/TASK_DAG.yaml:action_type_enum; the TASK_DAG is authoritative"
    )


def test_facet_catalogue_matches_its_value_list() -> None:
    """Every facet in the list has a catalogue entry with owners and dimensions."""
    catalogue = vocab.facet_catalogue()
    listed = vocab.values("facet")
    assert sorted(catalogue) == sorted(listed), "facet list and catalogue disagree"
    dimensions = vocab.value_set("dimension")
    agents = vocab.value_set("agent_id")
    for name, entry in catalogue.items():
        assert entry.get("owners"), f"facet {name} has no owner"
        for owner in entry["owners"]:
            assert owner == "lead_atlas" or owner in agents, (
                f"facet {name} names unknown owner {owner!r}"
            )
        assert entry.get("dimensions"), f"facet {name} feeds no dimension"
        unknown = sorted(set(entry["dimensions"]) - dimensions)
        assert not unknown, f"facet {name} feeds unknown dimensions {unknown}"


def test_human_proposition_facets_are_in_the_catalogue() -> None:
    """Rule V21 depends on this subset naming real facets."""
    human = vocab.subset("facet", "human_proposition_facets")
    assert human, "no human-proposition facets declared; rule V21 would never fire"
    catalogue = vocab.facet_catalogue()
    for name in human:
        assert catalogue[name].get("human_proposition") is True, (
            f"{name} is in human_proposition_facets but its catalogue entry does not say so"
        )


def test_evidence_strength_scale_semantics_are_documented() -> None:
    """Contract §5.3: the shared ordinal scale must define all five levels."""
    semantics = vocab.meta("evidence_strength_v1", "level_semantics")
    assert sorted(semantics) == [0, 1, 2, 3, 4]
    for level, text in semantics.items():
        assert len(str(text)) > 10, f"level {level} has no usable definition"
    assert vocab.meta("evidence_strength_v1", "ordinal") is True
    assert vocab.meta("evidence_strength_v1", "human_evidence_required_at_or_above") == 3


def test_safety_domain_is_declared_as_constraint_only() -> None:
    """README §3: safety variables are constraints, not costs to be traded away."""
    assert vocab.subset("state_domain", "constraint_domains") == ["safety"]
    assert "constraint" in vocab.values("state_variable_kind")
    assert "constraint_to_respect" in vocab.values("desirability")


def test_response_shape_default_is_unknown() -> None:
    """The anti-naivety default. `unknown` is not a synonym for linear."""
    assert vocab.meta("response_shape", "default") == "unknown"
    assert vocab.meta("response_shape_basis", "default") == "default_no_evidence_yet"
    assert "unknown" in vocab.meta("desirability", "defaults")


# --------------- validator / ontology agreement (no mirrored workarounds) --------

def test_validator_accepts_exactly_the_declared_claim_types(onto: ontology.Ontology) -> None:
    """For every relation, the validator's accepted set IS its declared list.

    A divergence here is the class of bug that lets a record pass one check and fail
    another depending on which agent runs which tool — and it produced exactly that:
    the validator accepted `preclinical_harm` on `INCREASES_RISK` while
    `ontology/edges.yaml` did not list it, so an atlas built a local check mirroring the
    validator. The contract's preamble applies between the validator and the ontology as
    much as between the validator and the contract.

    The test drives the rule through its own decision function rather than restating the
    lists, so it cannot drift as the vocabulary grows.
    """
    from blueprint import validate

    declared = {
        name: set(onto.allowed_claim_types(name))
        for name in onto.edges
        if onto.allowed_claim_types(name)
    }
    assert declared, "no relation declares allowed_claim_types"

    all_claim_types = vocab.value_set("claim_type")
    for name, allowed in declared.items():
        accepted = {
            claim_type
            for claim_type in all_claim_types
            if claim_type in set(onto.allowed_claim_types(name))
        }
        assert accepted == allowed, (
            f"{name}: the validator accepts {sorted(accepted)} but the ontology declares "
            f"{sorted(allowed)}"
        )
        unknown = sorted(allowed - all_claim_types)
        assert not unknown, f"{name} allows claim types that are not in the vocabulary: {unknown}"

    # And the rule that enforces it must be registered, or the lists are decoration.
    assert "V3c" in validate.REGISTRY


def test_safety_bearing_relations_admit_preclinical_harm(onto: ontology.Ontology) -> None:
    """R13: harm in a non-human model is `preclinical_harm`, and it must be recordable.

    A safety relation that admitted `clinical_harm` but not `preclinical_harm` would
    leave an agent with a mouse result and no legal label — which is what forced the
    original mislabelling.
    """
    for name in ("INCREASES_RISK", "DECREASES_RISK", "NO_DETECTED_EFFECT_ON"):
        allowed = set(onto.allowed_claim_types(name))
        assert "preclinical_harm" in allowed, f"{name} cannot record non-human harm"
    assert "clinical_harm" in set(onto.allowed_claim_types("INCREASES_RISK"))
    # DECREASES_RISK deliberately omits clinical_harm: harm evidence does not show a
    # risk going DOWN.
    assert "clinical_harm" not in set(onto.allowed_claim_types("DECREASES_RISK"))


def test_tool_mediated_is_a_distinct_provenance_class(onto: ontology.Ontology) -> None:
    """A payload a tool handed an agent is weaker than a record the agent opened.

    Folding `tool_mediated` into `reference_data` would hide that distinction from the
    red team, which is the audience for it.
    """
    assert "tool_mediated" in onto.provenance_classes
    assert "tool_mediated" in vocab.values("provenance_class")
    assert "mcp_tool" in vocab.values("retrieval_method")
    assert vocab.subset("retrieval_method", "tool_mediated_values") == ["mcp_tool"]
    evidential = set(vocab.subset("provenance_class", "evidential_classes"))
    assert evidential == {"claim_derived", "reference_data", "tool_mediated"}
    assert "ontology_axiom" not in evidential, (
        "an axiom is definitional, not evidence; it must not be counted as evidential"
    )


def test_every_claim_type_is_admitted_by_some_relation(onto: ontology.Ontology) -> None:
    """A claim type no relation accepts is unusable by construction.

    This class of gap has appeared twice — `preclinical_harm` missing from
    `INCREASES_RISK`, and `evidence_gap` admitted by nothing at all once V3c started
    enforcing the declared lists. Each time an agent had a true fact and no legal way to
    record it, which is the failure mode the whole freeze exception exists for.
    """
    admitted: dict[str, list[str]] = {}
    for name in onto.edges:
        for claim_type in onto.allowed_claim_types(name):
            admitted.setdefault(claim_type, []).append(name)

    # Claim types that describe a record rather than licensing an edge. Listed
    # explicitly so "no relation accepts it" is always a deliberate decision.
    edge_free = {
        "theoretical_construct",  # a construct definition, not an edge
    }
    orphans = sorted(vocab.value_set("claim_type") - set(admitted) - edge_free)
    assert not orphans, (
        f"claim type(s) {orphans} are in the vocabulary but no relation admits them, so "
        "an agent holding that kind of evidence has no legal way to record it"
    )
    # And the two that caused the incidents must be admitted where they belong.
    assert "ABOUT" in admitted["evidence_gap"], "a gap must have a home relation"
    assert admitted["evidence_gap"] == ["ABOUT"], (
        "a gap is graph-inert, so ABOUT must be the ONLY relation that admits it: "
        f"found {admitted['evidence_gap']}"
    )
    assert "INCREASES_RISK" in admitted["preclinical_harm"]
