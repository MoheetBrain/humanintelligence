"""The state model must conform to its type system and assert no dynamics.

The central test here is :func:`test_no_invented_dose_response_curves`. Everything else
in this file supports it. The project's whole position on state variables is that
MAXIMISING IS NOT ASSUMED TO BE GOOD and that a response shape is an empirical claim, so
a shape other than ``unknown`` appearing with the default basis is not a small
bookkeeping slip — it is the exact failure the design exists to prevent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from blueprint import loaders, paths, records, vocab


@pytest.fixture(scope="module")
def domains() -> dict[str, dict]:
    """Each state-model domain file, keyed by its declared domain."""
    out: dict[str, dict] = {}
    for path in paths.state_domain_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        out[document["domain"]] = document
    return out


@pytest.fixture(scope="module")
def variables(domains: dict[str, dict]) -> list[dict]:
    """Every state-variable definition, sorted by id."""
    out: list[dict] = []
    for document in domains.values():
        out.extend(document.get("variables") or [])
    return sorted(out, key=lambda v: v["id"])


@pytest.fixture(scope="module")
def parsed(variables: list[dict]) -> list[records.StateVariable]:
    """Every definition as a validated model."""
    return [records.StateVariable(**variable) for variable in variables]


# ------------------------------------------------------------- completeness -----

def test_all_eight_domains_present(domains: dict[str, dict]) -> None:
    """A missing domain would silently drop a whole dimension of the state model."""
    assert sorted(domains) == sorted(vocab.values("state_domain"))
    assert len(domains) == 8


def test_every_domain_has_variables(domains: dict[str, dict]) -> None:
    """An empty domain file is indistinguishable from a forgotten one."""
    for domain, document in domains.items():
        assert document.get("variables"), f"domain {domain} declares no variables"


def test_domain_file_declares_its_domain_and_provenance(domains: dict[str, dict]) -> None:
    """Every file says who defined it and on what basis."""
    for domain, document in domains.items():
        assert document["domain"] == domain
        assert document["defined_by"] == "agent:ontology"
        assert len(str(document.get("description", ""))) > 60


def test_brief_named_power_variables_present(domains: dict[str, dict]) -> None:
    """The power domain's variable list is the one the project brief names."""
    names = {v["id"].split(".", 1)[1] for v in domains["power"]["variables"]}
    required = {
        "atp_adp_ratio", "phosphocreatine_reserve", "mitochondrial_spare_capacity",
        "glucose_oxidation_rate", "lactate_flux", "ketone_utilisation_capacity",
        "astrocytic_glycogen_reserve", "cerebral_blood_flow",
        "oxygen_extraction_fraction", "neurovascular_coupling_gain",
        "ros_production_rate", "thermal_burden",
    }
    assert required <= names, f"missing power variables: {sorted(required - names)}"


def test_brief_named_safety_variables_present(domains: dict[str, dict]) -> None:
    """The safety domain's variable list is the one the project brief names."""
    names = {v["id"].split(".", 1)[1] for v in domains["safety"]["variables"]}
    required = {
        "seizure_risk", "psychosis_risk", "mania_risk", "anxiety_risk",
        "addiction_risk", "insomnia_risk", "excitotoxicity_risk",
        "oxidative_stress_burden", "pain_risk", "cardiovascular_burden",
        "proliferative_risk",
    }
    assert required <= names, f"missing safety variables: {sorted(required - names)}"


def test_ids_are_unique(variables: list[dict]) -> None:
    """A duplicate id would make one definition invisible."""
    ids = [variable["id"] for variable in variables]
    assert len(ids) == len(set(ids)), "duplicate state-variable id"


def test_id_domain_matches_its_file(domains: dict[str, dict]) -> None:
    """The domain is part of the identifier, so the two can never disagree."""
    for domain, document in domains.items():
        for variable in document["variables"]:
            declared = variable["id"].split(":", 1)[1].split(".", 1)[0]
            assert declared == domain, (
                f"{variable['id']} is declared in the {domain} file"
            )


# --------------------------------------------------------- type conformance -----

def test_every_variable_conforms_to_the_type_system(parsed: list[records.StateVariable]) -> None:
    """Parsing is validation: the model enforces what the type system declares."""
    assert len(parsed) >= 92


@pytest.mark.parametrize(
    ("field", "vocabulary"),
    [
        ("kind", "state_variable_kind"),
        ("timescale", "state_variable_timescale"),
        ("level", "state_variable_level"),
        ("desirability", "desirability"),
        ("status", "state_variable_status"),
        ("safety_coupling_basis", "safety_coupling_basis"),
    ],
)
def test_enum_fields_use_declared_values(
    variables: list[dict], field: str, vocabulary: str
) -> None:
    """Every enumerated field must use a value the vocabulary declares."""
    allowed = vocab.value_set(vocabulary)
    for variable in variables:
        assert variable[field] in allowed, (
            f"{variable['id']}.{field} = {variable[field]!r} is not in {vocabulary}"
        )


def test_required_fields_present(variables: list[dict]) -> None:
    """The type system's required instance fields, checked against the declaration."""
    types_doc = yaml.safe_load(paths.state_variable_types_file().read_text(encoding="utf-8"))
    required = set(types_doc["instance_required_fields"])
    for variable in variables:
        missing = sorted(required - set(variable))
        assert not missing, f"{variable['id']} is missing {missing}"


def test_definitions_are_substantive(variables: list[dict]) -> None:
    """A one-word definition is not a definition."""
    for variable in variables:
        definition = str(variable["definition"]).strip()
        assert len(definition) >= 40, f"{variable['id']} has a stub definition"
        assert definition[0].isupper(), f"{variable['id']} definition does not read as a sentence"


def test_measurement_proxies_are_typed(variables: list[dict]) -> None:
    """A proxy must declare its modality and its honest measurability grade."""
    modalities = vocab.value_set("measurement_modality")
    statuses = vocab.value_set("measurability")
    for variable in variables:
        for proxy in variable["measurement_proxies"]:
            assert set(proxy) == {"name", "modality", "status"}, (
                f"{variable['id']} proxy has unexpected keys {sorted(proxy)}"
            )
            assert proxy["modality"] in modalities
            assert proxy["status"] in statuses


def test_units_are_a_string_or_explicitly_null(variables: list[dict]) -> None:
    """``units: null`` means "no agreed unit", NOT "dimensionless"."""
    for variable in variables:
        assert "units" in variable
        assert variable["units"] is None or isinstance(variable["units"], str)


# ------------------------------------ THE CENTRAL TEST: no invented dynamics ----

def test_no_invented_dose_response_curves(variables: list[dict]) -> None:
    """Every response shape is ``unknown`` unless it states a non-default basis.

    README §3: the shape defaults to ``unknown`` until evidence says otherwise, and
    ``unknown`` is NOT a synonym for linear. A plausible-looking curve written into a
    definition would be read as a finding by everything downstream, so the default basis
    admits only ``unknown``.
    """
    for variable in variables:
        shape = variable["response_shape"]
        assert set(shape) >= {"shape", "basis", "claim_refs"}
        if shape["basis"] == "default_no_evidence_yet":
            assert shape["shape"] == "unknown", (
                f"{variable['id']} declares shape {shape['shape']!r} with the default "
                "basis; a shape other than `unknown` is an empirical claim and needs "
                "basis `claim_supported` with claim_refs, or `definitional`"
            )
            assert shape["claim_refs"] == [], (
                f"{variable['id']} cites claims under the default basis"
            )
        else:
            assert shape["basis"] in vocab.value_set("response_shape_basis")
            if shape["basis"] == "claim_supported":
                assert shape["claim_refs"], (
                    f"{variable['id']} claims a claim-supported shape but cites no claim"
                )


def test_agent_ontology_declares_no_shape_at_all(variables: list[dict]) -> None:
    """agent:ontology has no evidence, so it may not set any shape.

    This is stronger than the rule above and is the honest state of Sprint 1: the
    ontology architect writes definitions, and every shape is left for a domain agent
    to propose through a claim-backed annotation.
    """
    shaped = [
        variable["id"]
        for variable in variables
        if variable["response_shape"]["shape"] != "unknown"
    ]
    assert not shaped, (
        f"agent:ontology has asserted a response shape for {shaped}; it holds no "
        "evidence, so every shape must stay `unknown` until an annotation proposes one"
    )


def test_no_invented_safety_couplings(variables: list[dict]) -> None:
    """Which variables push which safety constraints is EMPIRICAL, so it is empty here.

    Several couplings look obvious. Pre-filling them would be exactly the
    plausible-sounding invention contract P2 and P3 forbid, so the field is a slot that
    domain agents fill through claim-backed annotations.
    """
    for variable in variables:
        basis = variable["safety_coupling_basis"]
        coupling = variable["safety_coupling"]
        if basis == "not_asserted_pending_claims":
            assert coupling == [], (
                f"{variable['id']} asserts safety couplings {coupling} with basis "
                "not_asserted_pending_claims; assert a coupling through an annotation "
                "with claim refs, never in the definition"
            )
        else:
            assert basis in vocab.value_set("safety_coupling_basis")


def test_definitions_reference_no_other_state_variable(variables: list[dict]) -> None:
    """A definition may not assert a relationship to another variable.

    Relationships are claims or annotations with provenance. A definition that names
    another variable is smuggling a dependency past the evidence machinery.
    """
    for variable in variables:
        text = str(variable["definition"])
        assert "SV:" not in text, (
            f"{variable['id']} names another state variable in its definition; "
            "relationships are claims, not definitions"
        )


def test_definitions_name_no_gene_or_intervention(variables: list[dict]) -> None:
    """A definition may not tie a variable to a gene, drug or target."""
    for variable in variables:
        text = str(variable["definition"])
        for prefix in ("GENE:", "PROT:", "TGT:", "DRUG:", "CPD:", "CLM:", "PMID"):
            assert prefix not in text, (
                f"{variable['id']} definition names {prefix}; a definition carries no "
                "empirical content"
            )


# ------------------------------------------- safety variables are constraints ---

def test_safety_variables_are_constraints(domains: dict[str, dict]) -> None:
    """README §3: safety variables are constraints, not costs to be traded away.

    One exception is approved and is itself a constraint: a dose-limiting tolerability
    MARGIN is headroom, so more of it is better within a range nobody has established
    (R3). It still bounds the admissible region rather than being an objective.
    """
    for variable in domains["safety"]["variables"]:
        assert variable["kind"] == "constraint", (
            f"{variable['id']} is in the safety domain but kind is {variable['kind']!r}"
        )
        allowed = (
            {"constraint_to_respect", "higher_is_better_within_range"}
            if variable["polarity"] == "margin"
            else {"constraint_to_respect"}
        )
        assert variable["desirability"] in allowed, (
            f"{variable['id']} has polarity {variable['polarity']!r} and desirability "
            f"{variable['desirability']!r}; allowed: {sorted(allowed)}"
        )


def test_only_safety_variables_are_constraint_kind(variables: list[dict]) -> None:
    """``constraint`` is reserved for the safety domain, so the two cannot diverge."""
    for variable in variables:
        domain = variable["id"].split(":", 1)[1].split(".", 1)[0]
        if variable["kind"] == "constraint":
            assert domain == "safety", (
                f"{variable['id']} is kind: constraint outside the safety domain"
            )


def test_no_safety_risk_is_higher_is_better(domains: dict[str, dict]) -> None:
    """A safety RISK must never be phrased as something to maximise.

    A safety MARGIN may be, because more headroom is better — which is exactly why the
    polarity field exists: without it, "maximise the margin" and "maximise the risk"
    are indistinguishable to an aggregation.
    """
    for variable in domains["safety"]["variables"]:
        if variable["polarity"] == "risk":
            assert variable["desirability"] == "constraint_to_respect", (
                f"{variable['id']} is a risk and must be constraint_to_respect"
            )


def test_desirability_defaults_are_uninformative(variables: list[dict]) -> None:
    """The project does not know the direction of benefit for most variables.

    Anything claiming ``higher_is_better_within_range`` would be asserting one, so no
    definition may: that judgement belongs to an annotation with claim references.
    """
    optimistic = [
        variable["id"]
        for variable in variables
        if variable["desirability"] == "higher_is_better_within_range"
        and variable.get("polarity") != "margin"
    ]
    assert not optimistic, (
        f"{optimistic} are declared higher-is-better in their definitions; that is a "
        "judgement about benefit and needs evidence. The only permitted case is a "
        "declared `margin`, where more headroom is better by the definition of headroom."
    )


# --------------------------------------------------------------- provenance -----

def test_every_variable_records_its_provenance(variables: list[dict]) -> None:
    """Who defined it and on what basis, on every instance."""
    for variable in variables:
        provenance = variable["provenance"]
        assert provenance["defined_by"] == "agent:ontology"
        assert provenance["basis"], f"{variable['id']} states no basis"


def test_related_primitives_resolve(variables: list[dict]) -> None:
    """A dangling primitive reference is indistinguishable from an invented one."""
    from blueprint import ontology

    known = set(ontology.load().primitives)
    for variable in variables:
        for primitive in variable.get("related_primitives") or []:
            assert primitive in known, f"{variable['id']} references unknown {primitive}"


# ------------------------------------------------------------------ dynamics ----

def test_dynamics_declares_itself_unfitted() -> None:
    """state_model/dynamics.yaml must not be mistakable for a fitted model."""
    document = yaml.safe_load(paths.dynamics_file().read_text(encoding="utf-8"))
    assert document["status"] == "formal_structure_only"
    assert document["fitted"] is False
    assert document["simulated"] is False
    assert document["identified"] is False
    assert document["symbols"]["F"]["status"] == "not_specified"
    assert document["symbols"]["noise"]["status"] == "placeholder"


def test_dynamics_represents_no_dose() -> None:
    """U has no magnitude, so the model cannot express a dose even in principle."""
    document = yaml.safe_load(paths.dynamics_file().read_text(encoding="utf-8"))
    magnitude = document["symbols"]["U"]["range"]["magnitude"]
    assert magnitude["value"] == "not_represented"
    assert "NO DOSE" in magnitude["note"].upper()


def test_power_envelope_is_labelled_a_hypothesis() -> None:
    """The multiplicative form is a conceptual hypothesis, never a law."""
    document = yaml.safe_load(paths.dynamics_file().read_text(encoding="utf-8"))
    hypotheses = {h["id"]: h for h in document["conceptual_hypotheses"]}
    envelope = hypotheses["HYP:power_envelope"]
    assert envelope["status"] == "conceptual_hypothesis_not_a_law"
    assert envelope["fitted"] is False
    assert envelope["tested"] is False
    assert envelope["known_problems"], "a hypothesis with no stated problems is advocacy"


def test_every_hypothesis_states_its_known_problems() -> None:
    """A hypothesis is written down to be attacked, so the attacks are written with it."""
    document = yaml.safe_load(paths.dynamics_file().read_text(encoding="utf-8"))
    for hypothesis in document["conceptual_hypotheses"]:
        assert hypothesis["status"] == "conceptual_hypothesis_not_a_law"
        assert hypothesis["fitted"] is False
        assert hypothesis["tested"] is False
        assert hypothesis["known_problems"], f"{hypothesis['id']} states no known problems"


def test_state_vector_membership_rule_matches_the_vocabulary() -> None:
    """The X/Theta split is declared by timescale; both lists must be vocabulary values."""
    document = yaml.safe_load(paths.dynamics_file().read_text(encoding="utf-8"))
    declared = set(document["symbols"]["X"]["members"]["domains_included"])
    assert declared == set(vocab.values("state_domain"))
    state_values = set(vocab.subset("state_variable_timescale", "state_vector_values"))
    parameter_values = set(vocab.subset("state_variable_timescale", "parameter_values"))
    assert state_values and parameter_values
    assert not (state_values & parameter_values), "a timescale cannot be both X and Theta"


def test_every_variable_timescale_is_classified(variables: list[dict]) -> None:
    """Every declared timescale must fall in X, in Theta, or be explicitly unknown."""
    state_values = set(vocab.subset("state_variable_timescale", "state_vector_values"))
    parameter_values = set(vocab.subset("state_variable_timescale", "parameter_values"))
    for variable in variables:
        timescale = variable["timescale"]
        assert timescale in state_values | parameter_values | {"unknown"}, (
            f"{variable['id']} has timescale {timescale!r}, which the X/Theta split in "
            "state_model/dynamics.yaml does not classify"
        )


# ----------------------------------------------------- loading through the API --

def test_loader_reports_a_domain_mismatch(make_root) -> None:
    """A variable in the wrong file must be reported, not silently accepted."""
    import shutil

    root = make_root(None)
    link = root / "state_model"
    target = link.resolve()
    link.unlink()
    shutil.copytree(target, link)
    path = link / "power.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "  - id: SV:power.atp_adp_ratio", "  - id: SV:cognition.atp_adp_ratio", 1
    )
    path.write_text(body, encoding="utf-8")
    from tests.conftest import _clear_caches

    _clear_caches()
    _, violations = loaders.load_state_variables(root)
    assert any(v.rule == "V2" and "declares domain" in v.message for v in violations)


def test_loader_is_deterministic() -> None:
    """Two loads must produce the same ordering (contract P7).

    The list keeps file order, and files are visited sorted by name, so the sequence is
    reproducible without being globally sorted by id.
    """
    first, _ = loaders.load_state_variables()
    second, _ = loaders.load_state_variables()
    assert [r.record_id for r in first] == [r.record_id for r in second]
    assert [r.path for r in first] == [r.path for r in second]
    domains_in_order = []
    for record in first:
        domain = record.path.split("/")[1].removesuffix(".yaml")
        if domain not in domains_in_order:
            domains_in_order.append(domain)
    assert domains_in_order == sorted(domains_in_order), (
        "domain files must be visited in sorted order"
    )


def test_empty_state_model_loads_without_raising(tmp_path: Path) -> None:
    """A missing state model is an empty collection, not a crash."""
    (tmp_path / ".blueprint-root").write_text("marker\n", encoding="utf-8")
    loaded, violations = loaders.load_state_variables(tmp_path)
    assert loaded == []
    assert violations == []


# ------------------------------------------------- R4: risk/margin polarity -----

def test_safety_and_stability_variables_declare_a_polarity(domains: dict[str, dict]) -> None:
    """``direction: increases`` means OPPOSITE things against a threshold and a risk.

    The brake atlas had to invert six coupling directions by hand after re-pointing a
    seizure THRESHOLD to a seizure RISK, and that error is silent. So the polarity is
    declared, and annotations are read relative to it.
    """
    allowed = vocab.value_set("state_variable_polarity")
    for domain in ("safety", "stability"):
        for variable in domains[domain]["variables"]:
            assert variable.get("polarity") in allowed, (
                f"{variable['id']} declares polarity {variable.get('polarity')!r}"
            )


def test_other_domains_declare_no_polarity(domains: dict[str, dict]) -> None:
    """Only safety and stability variables have a risk/margin reading."""
    for domain, document in domains.items():
        if domain in {"safety", "stability"}:
            continue
        for variable in document["variables"]:
            assert "polarity" not in variable, (
                f"{variable['id']} declares a polarity but is not a safety or stability "
                "variable"
            )


def test_polarity_matches_the_naming_convention(domains: dict[str, dict]) -> None:
    """A convention that is only written down will be broken by the next agent."""
    for domain in ("safety", "stability"):
        for variable in domains[domain]["variables"]:
            name = variable["id"].rsplit(".", 1)[-1]
            if name.endswith("_margin"):
                assert variable["polarity"] == "margin", f"{variable['id']} is misnamed"
            if name.endswith(("_risk", "_burden")):
                assert variable["polarity"] == "risk", f"{variable['id']} is misnamed"


def test_nominal_polarities_say_so(domains: dict[str, dict]) -> None:
    """Where neither reading is honest, the record must admit it rather than imply one.

    Arousal is not monotone in either direction, so neither `risk` nor `margin`
    describes it. It carries a declared reference direction for annotations plus a note
    saying the assignment is nominal, and its response shape stays `unknown`.
    """
    stability = {v["id"].rsplit(".", 1)[-1]: v for v in domains["stability"]["variables"]}
    arousal = stability["arousal_level"]
    assert "NOMINAL" in arousal["polarity_note"].upper()
    assert arousal["response_shape"]["shape"] == "unknown"


def test_dose_limiting_tolerability_margin_exists(domains: dict[str, dict]) -> None:
    """R3: the most decision-relevant safety fact in the brake atlas had nowhere to live.

    Without it the ranking model would have read a narrow safety profile as a
    favourable one, because the constraint was visible only in prose.
    """
    variables = {v["id"]: v for v in domains["safety"]["variables"]}
    margin = variables["SV:safety.dose_limiting_tolerability_margin"]
    assert margin["kind"] == "constraint"
    assert margin["polarity"] == "margin"
    assert margin["desirability"] == "higher_is_better_within_range"
    assert margin["response_shape"]["shape"] == "unknown"
    assert "exposure" in margin["definition"].lower()
