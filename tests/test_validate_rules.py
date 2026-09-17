"""One test per implemented contract rule, each against a minimal fixture tree.

Why it is shaped this way
-------------------------
A rule that never fires is indistinguishable from a rule that does not exist. Each test
here points the validator at a tree built to break exactly one rule and asserts that the
rule fires — and, for the rules where it matters, that the MESSAGE says what to do,
because a domain agent fixes its records against that message and never reads this file.

``tests/fixtures/valid_minimal`` is the control: it must pass every rule under
``--strict``. If it ever fails, a rule has become stricter than the contract, and the
rule is what needs looking at.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from blueprint import validate
from blueprint.violations import Violation

RootFactory = Callable[[str | None], Path]


def run_case(make_root: RootFactory, case: str | None, *, rule: str | None = None,
             strict: bool = True) -> validate.ValidationReport:
    """Validate a fixture tree, optionally restricted to one rule."""
    root = make_root(case)
    only = (rule,) if rule else None
    return validate.run(root, strict=strict, only=only)


def rules_fired(report: validate.ValidationReport) -> set[str]:
    return {violation.rule for violation in report.violations}


def messages(report: validate.ValidationReport, rule: str) -> list[str]:
    return [v.message for v in report.violations if v.rule == rule]


def for_rule(report: validate.ValidationReport, rule: str) -> list[Violation]:
    return [v for v in report.violations if v.rule == rule]


# ------------------------------------------------------------------ controls -----

def test_empty_repository_passes(make_root: RootFactory) -> None:
    """Zero records is a CORRECT state for Sprint 1, not a missing one."""
    report = run_case(make_root, None)
    assert report.ok, [str(v) for v in report.violations]
    assert report.counts["claims"] == 0
    assert report.counts["sources"] == 0
    # The type system is still validated even with no records.
    # Derived, not hard-coded: the state model grows by approved amendment
    # (R3 added one), and a literal would fail on the next legitimate addition.
    assert report.counts["state_variables"] >= 100
    assert report.counts["definitional_edges"] > 0


def test_minimal_valid_repository_passes_under_strict(make_root: RootFactory) -> None:
    """The control. A failure here means a rule outgrew the contract."""
    report = run_case(make_root, "valid_minimal")
    assert report.ok, [str(v) for v in report.violations]
    assert report.counts["claims"] == 1
    assert report.counts["sources"] == 1


def test_every_registered_rule_runs_on_the_control(make_root: RootFactory) -> None:
    """A rule that is registered but never executed protects nothing."""
    report = run_case(make_root, "valid_minimal")
    assert set(report.rules_run) == set(validate.REGISTRY)
    assert len(report.rules_run) >= 24


# ------------------------------------------------------------- V1: schemas -------

def test_v1_schema_failure_is_reported(make_root: RootFactory) -> None:
    """A record that breaks its schema must be reported against V1."""
    report = run_case(make_root, "v8_incomplete_translation", rule="V1")
    assert "V1" in rules_fired(report)
    assert any("translation" in m or "Field required" in m for m in messages(report, "V1"))


# ------------------------------------------------------------ V2: node ids -------

def test_v2_malformed_node_id(make_root: RootFactory) -> None:
    """A lower-case gene symbol is not an HGNC-approved symbol (contract §1)."""
    report = run_case(make_root, "v2_malformed_id", rule="V2")
    assert "V2" in rules_fired(report)
    message = messages(report, "V2")[0]
    assert "GENE:lowercase_is_not_an_hgnc_symbol" in message
    assert "id_pattern" in message or "node type" in message


# --------------------------------------------------------- V3: legal triples -----

def test_v3_illegal_triple_names_the_alternatives(make_root: RootFactory) -> None:
    """The message must name the triple, the failing side and the legal relations.

    Domain agents fix records against this message, so its content is part of the
    contract's usability, not a nicety.
    """
    report = run_case(make_root, "v3_illegal_triple", rule="V3")
    assert "V3" in rules_fired(report)
    violation = for_rule(report, "V3")[0]
    assert violation.record_id == "CLM:ontology:PLACEHOLDER:001"
    assert "GENE:PLACEHOLDER -TARGETS-> CELL:placeholder_cell" in violation.message
    assert "not a legal subject" in violation.message
    assert "Relations legal for" in violation.message or "NO relation connects" in violation.message


def test_v3_accepts_the_contract_example_triple() -> None:
    """The contract's own example must be legal, or the ontology contradicts it."""
    from blueprint import ontology

    index = ontology.load()
    assert index.is_legal_triple("Gene", "NEGATIVELY_REGULATES", "StateVariable")


# ---------------------------------------------------- V4: cross-references -------

def test_v4_dangling_source_reference(make_root: RootFactory) -> None:
    """A claim citing an unregistered source is the commonest real failure."""
    report = run_case(make_root, "v4_dangling_reference", rule="V4")
    assert "V4" in rules_fired(report)
    message = messages(report, "V4")[0]
    assert "SRC:PMID:00000001" in message
    assert "does not exist" in message


def test_v4_suggests_the_closest_declared_id(make_root: RootFactory) -> None:
    """A near-miss id is usually a wrong domain segment; naming the neighbour fixes it."""
    from blueprint.validate import _nearest

    universe = {"SV:stability.arousal_level", "SV:cognition.processing_speed"}
    assert _nearest("SV:cognition.arousal_level", universe) == ["SV:stability.arousal_level"]


def test_v4_allows_duplicate_registration_across_agents(
    make_root: RootFactory, tmp_path: Path
) -> None:
    """Contract §1.3: duplicate registration across agents is allowed and PREFERRED.

    It keeps each agent's claims self-contained so no agent depends on a file it cannot
    edit. Treating it as a violation once pushed an agent into deleting its own
    registrations and pointing its claims at another agent's file.
    """
    root = make_root("valid_minimal")
    original = (root / "evidence" / "sources" / "ontology.yaml").read_text(encoding="utf-8")
    (root / "evidence" / "sources" / "brakes.yaml").write_text(original, encoding="utf-8")

    report = validate.run(root, strict=True)
    assert report.ok, [str(v) for v in report.violations]

    from blueprint import loaders

    repo = loaders.load_repository(root)
    assert repo.shared_sources == {
        "SRC:PMID:00000001": ("evidence/sources/brakes.yaml", "evidence/sources/ontology.yaml")
    }
    assert repo.counts()["shared_sources"] == 1


def test_v4_rejects_divergent_duplicate_registration(make_root: RootFactory) -> None:
    """Duplicate registration is fine; DISAGREEING about the registry is not."""
    root = make_root("valid_minimal")
    original = (root / "evidence" / "sources" / "ontology.yaml").read_text(encoding="utf-8")
    diverged = original.replace(
        "Synthetic placeholder title for fixture purposes only",
        "A completely different synthetic title",
    )
    assert diverged != original
    (root / "evidence" / "sources" / "brakes.yaml").write_text(diverged, encoding="utf-8")

    report = validate.run(root, strict=True)
    assert "V4" in rules_fired(report)
    message = next(m for m in messages(report, "V4") if "DIFFERENT registry fields" in m)
    assert "evidence/sources/brakes.yaml" in message
    assert "evidence/sources/ontology.yaml" in message
    assert "title:" in message


def test_v4_rejects_duplicate_registration_within_one_file(make_root: RootFactory) -> None:
    """Twice in one file is a bookkeeping mistake with no upside."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "sources" / "ontology.yaml"
    body = path.read_text(encoding="utf-8")
    record = body[body.index("- schema_version") :]
    path.write_text(body + "\n" + record, encoding="utf-8")

    report = validate.run(root, strict=True, only=("V4",))
    assert any("registered twice in" in m for m in messages(report, "V4"))


# -------------------------------------------------------------- V5: evidence -----

def test_v5_claim_without_evidence(make_root: RootFactory) -> None:
    """Contract P2: a claim with no evidence item is not a claim."""
    report = run_case(make_root, "v5_claim_without_evidence", rule="V5")
    assert "V5" in rules_fired(report)
    message = messages(report, "V5")[0]
    assert "no evidence item" in message
    assert "Withdraw the claim" in message


# -------------------------------------------------- V6: source verification ------

def test_v6_unverified_source(make_root: RootFactory) -> None:
    """A title mismatch means the identifier or the title is wrong; both are fatal."""
    report = run_case(make_root, "v6_unverified_source", rule="V6")
    assert "V6" in rules_fired(report)
    message = messages(report, "V6")[0]
    assert "title_mismatch" in message
    assert "Registry title" in message


def test_v6_missing_index_is_a_warning_that_strict_escalates(make_root: RootFactory) -> None:
    """No index means "not checked", which is neither a pass nor a crash."""
    root = make_root("valid_minimal")
    for path in (root / "data" / "interim" / "source_verification").glob("*.jsonl"):
        path.unlink()

    lenient = validate.run(root, strict=False, only=("V6",))
    assert lenient.ok, "a missing index must not fail a non-strict run"
    assert [v.severity for v in lenient.violations] == ["warning"]
    assert "unverified source is indistinguishable from a fabricated one" in lenient.violations[0].message

    strict = validate.run(root, strict=True, only=("V6",))
    assert not strict.ok, "--strict must escalate it"


def test_v6_takes_the_worst_status_across_agents(make_root: RootFactory) -> None:
    """Duplication must only ever make the answer stricter (fail closed)."""
    import json

    root = make_root("valid_minimal")
    directory = root / "data" / "interim" / "source_verification"
    bad = {
        "source_id": "SRC:PMID:00000001",
        "status": "title_mismatch",
        "registry": "pubmed",
        "registry_title": "Synthetic placeholder title for fixture purposes only",
        "registry_year": 2020,
        "registry_doi": None,
        "agent": "brakes",
    }
    # Written AFTER the verified row: a last-line-wins implementation would pass.
    (directory / "zz_brakes.jsonl").write_text(json.dumps(bad, sort_keys=True) + "\n", encoding="utf-8")

    from blueprint import verification

    index = verification.load(root)
    assert index.status_for("SRC:PMID:00000001") == "title_mismatch"
    report = validate.run(root, strict=True, only=("V6",))
    assert not report.ok, "the worst status must win, not the last line"


def test_v6_accepts_snapshot_verified_releases_for_db_prefixes_only(
    make_root: RootFactory,
) -> None:
    """A release has no literature registry; a paper does, so the check differs."""
    import json

    from blueprint import verification

    root = make_root("valid_minimal")
    directory = root / "data" / "interim" / "source_verification"
    (directory / "releases.jsonl").write_text(
        "\n".join(
            json.dumps(row, sort_keys=True)
            for row in (
                {"source_id": "SRC:DB:opentargets:26.06",
                 "status": "release_verified_by_snapshot", "snapshot_count": 1},
                {"source_id": "SRC:DATASET:gtex_v8_brain",
                 "status": "release_verified_by_snapshot", "snapshot_count": 1},
                {"source_id": "SRC:PMID:00000002",
                 "status": "release_verified_by_snapshot", "snapshot_count": 1},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    index = verification.load(root)
    assert index.is_verified("SRC:DB:opentargets:26.06", root)
    assert index.is_verified("SRC:DATASET:gtex_v8_brain", root)
    assert not index.is_verified("SRC:PMID:00000002", root), (
        "accepting snapshot verification for a paper would let an unverifiable PMID through"
    )


def test_v6_rejects_altered_snapshots(make_root: RootFactory) -> None:
    """``snapshot_missing_or_altered`` deliberately overlaps rule V19."""
    import json

    from blueprint import verification

    root = make_root("valid_minimal")
    (root / "data" / "interim" / "source_verification" / "releases.jsonl").write_text(
        json.dumps(
            {"source_id": "SRC:DB:opentargets:26.06", "status": "snapshot_missing_or_altered"},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assert not verification.load(root).is_verified("SRC:DB:opentargets:26.06", root)


# ------------------------------------------- V7: required distinctions ----------

def test_v7_phenotype_class_required_for_cognitive_objects(make_root: RootFactory) -> None:
    """P4 becomes a required field, not a prose caveat."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("object: CELL:placeholder_cell", "object: PHENO:placeholder_phenotype")
    body = body.replace("predicate: EXPRESSED_IN", "predicate: ASSOCIATED_WITH")
    body = body.replace("claim_type: expression", "claim_type: association")
    path.write_text(body, encoding="utf-8")

    report = validate.run(root, strict=True, only=("V7",))
    assert "V7" in rules_fired(report)
    message = messages(report, "V7")[0]
    assert "phenotype_class is mandatory" in message
    assert "educational attainment" in message


# --------------------------------------------------------- V8: translation ------

def test_v8_incomplete_translation(make_root: RootFactory) -> None:
    """`unknown` is allowed and explicit; a MISSING key is not (contract P8)."""
    report = run_case(make_root, "v8_incomplete_translation", rule="V8")
    assert "V8" in rules_fired(report)
    fired = {m.split("translation.")[1].split(" ")[0] for m in messages(report, "V8")}
    assert fired == {"human_relevance", "general_intelligence_relevance"}
    assert any("an absent key reads as 'not applicable'" in m for m in messages(report, "V8"))


# ----------------------------------------------------- V9: no fake precision ----

def test_v9_handwritten_probability(make_root: RootFactory) -> None:
    """Contract P3: 0.85 never appears because it "feels right"."""
    report = run_case(make_root, "v9_handwritten_probability", rule="V9")
    assert "V9" in rules_fired(report)
    violation = next(v for v in for_rule(report, "V9") if "0.85" in v.message)
    assert violation.severity == "error"
    assert "hand-written probability" in violation.message
    assert "ordinal rubric level" in violation.message


def test_v9_permits_effect_sizes_copied_verbatim(make_root: RootFactory) -> None:
    """A number read verbatim from a source is the ONE legitimate free number."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "effect_size: {metric: not_extracted, as_reported: null, value: null,",
        'effect_size: {metric: cohens_d, as_reported: "d = 0.42", value: 0.42,',
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V9",))
    assert report.ok, [str(v) for v in report.violations]


def test_v9_database_facts_need_a_named_release(make_root: RootFactory) -> None:
    """A database number is admissible because its provenance is VISIBLE."""
    root = make_root("valid_minimal")
    directory = root / "atlases" / "power" / "interventions"
    directory.mkdir(parents=True, exist_ok=True)
    unattributed = """
schema_version: "0.1.0"
id: DRUG:placeholder_drug
node_type: Drug
label: "placeholder drug"
max_clinical_phase: {value: 4, as_reported: "max_phase: 4"}
provenance: {created_by: agent:power, created_on: "2026-09-17", run_id: fixture}
"""
    path = directory / "placeholder.yaml"
    path.write_text(unattributed.lstrip(), encoding="utf-8")
    report = validate.run(root, strict=True, only=("V9",))
    assert "V9" in rules_fired(report)
    assert any("names no database release" in m for m in messages(report, "V9"))

    path.write_text(
        unattributed.replace(
            'max_clinical_phase: {value: 4, as_reported: "max_phase: 4"}',
            'max_clinical_phase: {value: 4, as_reported: "max_phase: 4"}\n'
            "database_source_id: SRC:DB:chembl:34",
        ).lstrip(),
        encoding="utf-8",
    )
    report = validate.run(root, strict=True, only=("V9",))
    assert report.ok, [str(v) for v in report.violations]


# ------------------------------------------------- V10: ordinal uncertainty -----

def test_v10_numeric_uncertainty_representation(make_root: RootFactory) -> None:
    """Curated records may express uncertainty only as an ordinal grade."""
    report = run_case(make_root, "v10_numeric_uncertainty", rule="V10")
    assert "V10" in rules_fired(report)
    message = messages(report, "V10")[0]
    assert "model_distribution" in message
    assert "not to a curated claim" in message


def test_v10_rejects_a_float_level_at_the_model_layer() -> None:
    """A float that happens to be integral is still not an ordinal grade."""
    from blueprint import records

    base = {
        "representation": "ordinal_grade",
        "scale": "evidence_strength_v1",
        "rationale": "fixture",
        "calibration_status": "uncalibrated_subjective",
    }
    records.Uncertainty(level=2, **base)
    for bad in (0.85, 2.0, True):
        with pytest.raises(Exception):
            records.Uncertainty(level=bad, **base)


# ------------------------------------------------------ V11: facet ownership ----

def test_v11_agent_may_not_grade_another_agents_facet(make_root: RootFactory) -> None:
    """Disagreement is a new artefact, never a grade on somebody else's facet."""
    report = run_case(make_root, "v11_facet_not_owned", rule="V11")
    assert "V11" in rules_fired(report)
    message = messages(report, "V11")[0]
    assert "agent:brakes" in message and "human_genetic_association" in message
    assert "agent:alphacognition" in message
    assert "contradicting claim" in message


# --------------------------------------------------- V12: downgrade-only --------

def test_v12_audit_may_not_upgrade_a_facet(make_root: RootFactory) -> None:
    """Contract P6: the red team can downgrade, never upgrade."""
    report = run_case(make_root, "v12_audit_upgrade", rule="V12")
    assert "V12" in rules_fired(report)
    message = messages(report, "V12")[0]
    assert "not a downgrade" in message
    assert "counter_level" in message, "the message should name the correct alternative"


def test_v12_counter_level_may_be_raised() -> None:
    """Raising the contradicting grade IS a downgrade of the target's standing."""
    from blueprint import records

    records.AuditAdjustment(
        kind="facet", facet="tractability", field="counter_level",
        from_level=1, to_level=3, reason="fixture",
    )
    with pytest.raises(Exception):
        records.AuditAdjustment(
            kind="facet", facet="tractability", field="counter_level",
            from_level=3, to_level=1, reason="fixture",
        )


# ------------------------------------------------------- V13: registry lock -----

def test_v13_deleted_claim_still_in_the_lock(make_root: RootFactory) -> None:
    """Provenance is append-only: a locked claim id may never disappear."""
    report = run_case(make_root, "v13_deleted_claim_in_lock", rule="V13")
    assert "V13" in rules_fired(report)
    message = messages(report, "V13")[0]
    assert "CLM:ontology:PLACEHOLDER:999" in message
    assert "APPEND-ONLY" in message
    assert "status: withdrawn" in message


# --------------------------------------------------------- V14: withdrawal ------

def test_v14_withdrawal_needs_a_superseding_audit(make_root: RootFactory) -> None:
    """A withdrawal is an audited decision, not a self-service edit."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "status: active",
        'status: withdrawn\n  status_reason: "fixture withdrawal with no audit behind it"',
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V14",))
    assert "V14" in rules_fired(report)
    assert any("no audit record carries a superseding" in m for m in messages(report, "V14"))


# ----------------------------------------------------- V15: audit coverage ------

def test_v15_seed_target_without_an_audit_is_a_warning(make_root: RootFactory) -> None:
    """Gate G4 is a warning while the red team has not run; --strict escalates it."""
    root = make_root("valid_minimal")
    (root / "targets").mkdir(exist_ok=True)
    (root / "targets" / "seed_registry.yaml").write_text(
        'schema_version: 0.1.0\ntargets:\n  - target_id: TGT:PLACEHOLDER\n    symbol: PLACEHOLDER\n',
        encoding="utf-8",
    )
    lenient = validate.run(root, strict=False, only=("V15",))
    assert [v.severity for v in lenient.violations] == ["warning"]
    assert lenient.ok
    assert not validate.run(root, strict=True, only=("V15",)).ok


def test_v15_audit_must_carry_the_whole_check_catalogue(make_root: RootFactory) -> None:
    """`not_applicable` is a legitimate result but silence is not (contract §6)."""
    root = make_root("v12_audit_upgrade")
    (root / "targets" / "seed_registry.yaml").write_text(
        'schema_version: 0.1.0\ntargets:\n  - target_id: TGT:PLACEHOLDER\n    symbol: PLACEHOLDER\n',
        encoding="utf-8",
    )
    report = validate.run(root, strict=True, only=("V15",))
    assert "V15" in rules_fired(report)
    message = messages(report, "V15")[0]
    assert "omits" in message and "mandatory check" in message
    assert "silence is not" in message


# --------------------------------------------- V16: binding is not efficacy -----

def test_v16_binding_claim_cannot_license_an_effect(make_root: RootFactory) -> None:
    """The narrowest gate in the ontology."""
    report = run_case(make_root, "v16_efficacy_from_binding", rule="V16")
    assert "V16" in rules_fired(report)
    message = messages(report, "V16")[0]
    assert "BINDING IS NEVER EFFICACY" in message
    assert "pharmacology_binding" in message


def test_v16_gates_a_regulation_relation_reaching_a_phenotype(make_root: RootFactory) -> None:
    """An agent must not route round the gate by writing NEGATIVELY_REGULATES."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("predicate: EXPRESSED_IN", "predicate: NEGATIVELY_REGULATES")
    body = body.replace("object: CELL:placeholder_cell", "object: PHENO:placeholder_phenotype")
    body = body.replace("claim_type: expression", "claim_type: expression")
    body = body.replace("  direction: unclear", "  direction: decreases\n  phenotype_class: g_factor")
    path.write_text(body, encoding="utf-8")

    report = validate.run(root, strict=True, only=("V16",))
    assert "V16" in rules_fired(report)
    assert any("efficacy-grade assertion" in m for m in messages(report, "V16"))


def test_v16_accepts_a_causal_perturbation_claim(make_root: RootFactory) -> None:
    """The gate must admit the evidence grade the contract names."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("predicate: EXPRESSED_IN", "predicate: NEGATIVELY_REGULATES")
    body = body.replace("object: CELL:placeholder_cell", "object: PHENO:placeholder_phenotype")
    body = body.replace("claim_type: expression", "claim_type: causal_perturbation")
    body = body.replace("  direction: unclear", "  direction: decreases\n  phenotype_class: g_factor")
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V16",))
    assert report.ok, [str(v) for v in report.violations]


# ---------------------------------------- V16b: null results are findings -------

def test_v16b_null_edge_needs_null_evidence(make_root: RootFactory) -> None:
    """A null edge asserts a PERFORMED attempt, never absence of evidence."""
    report = run_case(make_root, "v16b_null_without_null_evidence", rule="V16b")
    assert "V16b" in rules_fired(report)
    message = messages(report, "V16b")[0]
    assert "NO_DETECTED_EFFECT_ON" in message
    assert "ABSENCE of an edge" in message


def test_v16b_accepts_a_reported_null(make_root: RootFactory) -> None:
    """A well-powered null must be representable, or the graph drifts positive."""
    root = make_root("v16b_null_without_null_evidence")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "evidence_role: supports", "evidence_role: null_result"
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V16b", "V16"))
    assert report.ok, [str(v) for v in report.violations]


# ------------------------------------------------ V17: edge provenance ----------

def test_v17_definitional_edges_carry_a_legal_provenance_class(make_root: RootFactory) -> None:
    """Every axiom in the real ontology must satisfy V17."""
    report = run_case(make_root, "valid_minimal", rule="V17")
    assert report.ok, [str(v) for v in report.violations]


def test_v17_rejects_an_axiom_on_an_empirical_relation(make_root: RootFactory) -> None:
    """An empirical relation cannot be introduced as an axiom."""
    root = make_root("valid_minimal")
    path = root / "ontology" / "definitional_edges.yaml"
    assert path.is_symlink() or path.is_file()
    # The fixture root symlinks ontology/, so write a real copy before editing it.
    import shutil

    link = root / "ontology"
    if link.is_symlink():
        target = link.resolve()
        link.unlink()
        shutil.copytree(target, link)
    path = root / "ontology" / "definitional_edges.yaml"
    body = path.read_text(encoding="utf-8")
    extra = """
  - subject: GENE:PLACEHOLDER
    predicate: EXPRESSED_IN
    object: CELL:placeholder_cell
    provenance_class: ontology_axiom
    basis: "fixture: expression is empirical and cannot be an axiom"
    defined_by: agent:ontology

"""
    # The file ends with a `counts:` block, so the edge goes before it, not after.
    marker = "\ncounts:"
    assert marker in body
    path.write_text(body.replace(marker, extra + marker, 1), encoding="utf-8")
    from tests.conftest import _clear_caches

    _clear_caches()
    report = validate.run(root, strict=True, only=("V17",))
    assert "V17" in rules_fired(report)
    assert any("may only carry" in m for m in messages(report, "V17"))


# ---------------------------------------------------------- V18: secrets --------

def test_v18_detects_a_credential(make_root: RootFactory) -> None:
    """No credential may ever enter a tracked file."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        'rationale: "synthetic fixture, no real evidence"',
        'rationale: "fixture with NCBI_API_KEY=deadbeefdeadbeefdeadbeef embedded"',
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V18",))
    assert "V18" in rules_fired(report)
    assert "API key" in messages(report, "V18")[0]


def test_v18_does_not_fire_on_secreted_proteins(make_root: RootFactory) -> None:
    """A rule that cries wolf is a rule agents learn to ignore.

    Substring matching was tried first and flagged "secreted protein" for containing
    "secret", so every marker is now word-bounded.
    """
    from blueprint import validate as v

    root = make_root("valid_minimal")
    path = root / "targets" / "candidates" / "PLACEHOLDER.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
schema_version: "0.1.0"
target_id: TGT:PLACEHOLDER
symbol: PLACEHOLDER
lead_atlas: ontology
seed_origin: agent_proposed
dossier_depth: shallow
target_class: "secreted hormone; secretase substrate; secretory pathway"
identifiers: {}
status: seed_hypothesis
provenance: {created_by: agent:ontology, created_on: "2026-09-17", run_id: fixture}
""".lstrip(),
        encoding="utf-8",
    )
    report = v.run(root, strict=True, only=("V18",))
    assert report.ok, [str(x) for x in report.violations]


# ------------------------------------------------- V19: raw immutability --------

def test_v19_detects_an_altered_snapshot(make_root: RootFactory, tmp_path: Path) -> None:
    """A changed byte breaks offline reproducibility (contract P7)."""
    import hashlib
    import json

    root = make_root("valid_minimal")
    raw = root / "data" / "raw" / "fake_registry" / "2026-09-17"
    raw.mkdir(parents=True, exist_ok=True)
    snapshot = raw / "payload.json"
    snapshot.write_text('{"synthetic": true}', encoding="utf-8")
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    manifest = root / "data" / "raw" / "MANIFEST.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "path": "data/raw/fake_registry/2026-09-17/payload.json",
                "sha256": digest,
                "bytes": snapshot.stat().st_size,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    assert validate.run(root, strict=True, only=("V19",)).ok

    snapshot.write_text('{"synthetic": true, "altered": true}', encoding="utf-8")
    report = validate.run(root, strict=True, only=("V19",))
    assert "V19" in rules_fired(report)
    assert "has been modified" in messages(report, "V19")[0]


def test_v19_detects_a_deleted_snapshot(make_root: RootFactory) -> None:
    """Raw snapshots are append-only and never deleted."""
    import json

    root = make_root("valid_minimal")
    manifest = root / "data" / "raw" / "MANIFEST.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({"path": "data/raw/gone/2026-09-17/x.json", "sha256": "0" * 64}, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    report = validate.run(root, strict=True, only=("V19",))
    assert any("missing from the working tree" in m for m in messages(report, "V19"))


# --------------------------------------------------- V20: prohibited work -------

def test_v20_record_proposing_prohibited_work(make_root: RootFactory) -> None:
    """Contract P1: this project proposes no human or animal experiment."""
    report = run_case(make_root, "v20_prohibited_work", rule="V20")
    assert "V20" in rules_fired(report)
    message = messages(report, "V20")[0]
    assert "PROPOSAL to perform prohibited work" in message
    assert "Describing somebody else's published experiment is fine" in message


def test_v20_does_not_fire_on_faithful_evidence_recording(make_root: RootFactory) -> None:
    """A published dose quoted in a record is evidence, not a protocol.

    This is the single most important false-positive guard in the repository: if
    recording somebody else's dosing study tripped the policy rule, agents would be
    pushed into laundering their statements, which is far worse than the risk.
    """
    from blueprint import policy

    faithful = [
        "Adult male mice received a single systemic injection before training.",
        "The effective dose in the healthy study was 140 mg/kg.",
        "Doses from 5 to 100 mg all affected performance with a flat dose-response curve.",
        "Participants were randomised and enrolled by the trial investigators in 2014.",
        "We will analyse the published dose-response data in silico.",
        "Future work will review animal studies of this transporter.",
    ]
    for text in faithful:
        assert policy.scan_text(text) == [], f"false positive on: {text}"

    prohibited = [
        "We will administer the compound to adult mice and measure memory.",
        "Next step is to recruit 40 healthy participants for a crossover trial.",
        "Take 5 g creatine monohydrate daily for two weeks.",
        "Recommended dose: 300 mg daily before the task.",
        "You should take 300 mg before the task.",
        "where to buy the compound",
    ]
    for text in prohibited:
        assert policy.scan_text(text), f"false negative on: {text}"


def test_v20_verbatim_fields_are_exempt_from_the_instruction_check() -> None:
    """A dose in ``effect_size.as_reported`` is a quotation, by construction."""
    from blueprint import policy

    quoted = "the recommended dose was 300 mg daily"
    assert policy.scan_text(quoted, verbatim=False)
    assert policy.scan_text(quoted, verbatim=True) == []


def test_v20_rejects_a_non_computational_action_type(make_root: RootFactory) -> None:
    """The action_type enum is closed and every value is computational."""
    from blueprint import policy

    violations = policy.check_action_type(
        "animal_experiment", path="fixture.yaml", root=make_root(None)
    )
    assert violations and violations[0].rule == "V20"
    assert "closed computational enum" in violations[0].message
    assert policy.check_action_type("literature_synthesis", path="fixture.yaml") == []


# ------------------------------------- V21: human-proposition facets -----------

def test_v21_human_facet_needs_human_evidence(make_root: RootFactory) -> None:
    """Contract §5.3: a level 3-4 on a human proposition needs human evidence."""
    report = run_case(make_root, "v21_human_facet_without_human_evidence", rule="V21")
    assert "V21" in rules_fired(report)
    violation = for_rule(report, "V21")[0]
    assert "human_genetic_association" in violation.message
    assert "graded level 4" in violation.message
    assert "human_genetic" in violation.message
    assert "Grade it lower, or cite the human claim" in violation.message


def test_v21_accepts_a_human_claim(make_root: RootFactory) -> None:
    """The rule must admit the evidence it asks for."""
    root = make_root("v21_human_facet_without_human_evidence")
    path = root / "evidence" / "claims" / "alphacognition" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "human_relevance: rodent_only", "human_relevance: human_genetic"
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V21",))
    assert report.ok, [str(v) for v in report.violations]


def test_v21_ignores_low_grades(make_root: RootFactory) -> None:
    """Below the threshold the rule must stay silent: a 2 needs no human evidence."""
    root = make_root("v21_human_facet_without_human_evidence")
    path = root / "atlases" / "alphacognition" / "assessments" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace("level: 4", "level: 2")
    path.write_text(body, encoding="utf-8")
    assert validate.run(root, strict=True, only=("V21",)).ok


# ------------------------------------------------ ONT*: ontology self-checks ----

def test_ont1_reports_schema_vocabulary_drift(make_root: RootFactory) -> None:
    """The drift check must run as part of validation, not only in the test suite."""
    report = run_case(make_root, "valid_minimal", rule="ONT1")
    assert report.ok, [str(v) for v in report.violations]


def test_ont2_rejects_an_invented_response_shape(make_root: RootFactory) -> None:
    """NO INVENTED DOSE-RESPONSE CURVES (README §3)."""
    report = run_case(make_root, "ont2_invented_response_shape", rule="ONT2")
    assert "ONT2" in rules_fired(report)
    message = messages(report, "ONT2")[0]
    assert "inverted_u" in message
    assert "MAXIMISING IS NOT ASSUMED TO BE GOOD" in message


def test_ont2_requires_every_state_domain(make_root: RootFactory) -> None:
    """A state model missing a whole domain would silently lose a dimension."""
    import shutil

    root = make_root(None)
    link = root / "state_model"
    target = link.resolve()
    link.unlink()
    shutil.copytree(target, link)
    (link / "safety.yaml").unlink()
    from tests.conftest import _clear_caches

    _clear_caches()
    report = validate.run(root, strict=True, only=("ONT2",))
    assert any("has no variables" in m for m in messages(report, "ONT2"))


# ------------------------------------------------------- engine behaviour -------

def test_a_failing_rule_does_not_abort_the_run(make_root: RootFactory) -> None:
    """One broken rule must not take down the report an agent needs."""

    def exploding(_ctx: validate.ValidationContext) -> list[Violation]:
        raise RuntimeError("synthetic rule failure")

    validate.REGISTRY["ZZTEST"] = (exploding, "synthetic failing rule")
    try:
        report = validate.run(make_root("valid_minimal"), strict=True)
        assert "ZZTEST" in rules_fired(report)
        violation = for_rule(report, "ZZTEST")[0]
        assert "validator bug, not a record problem" in violation.message
        assert not report.ok
    finally:
        del validate.REGISTRY["ZZTEST"]


def test_report_is_deterministic(make_root: RootFactory) -> None:
    """Two runs over one tree must produce identical reports."""
    root = make_root("v3_illegal_triple")
    first = validate.run(root, strict=True)
    second = validate.run(root, strict=True)
    assert [v.as_dict() for v in first.violations] == [v.as_dict() for v in second.violations]


def test_strict_escalates_warnings(make_root: RootFactory) -> None:
    """`--strict` is what gates G2 and G3 run with."""
    root = make_root("valid_minimal")
    for path in (root / "data" / "interim" / "source_verification").glob("*.jsonl"):
        path.unlink()
    assert validate.run(root, strict=False).ok
    assert not validate.run(root, strict=True).ok


def test_every_violation_names_a_rule_and_a_path(make_root: RootFactory) -> None:
    """A violation with no locator cannot be acted on."""
    report = validate.run(make_root("v3_illegal_triple"), strict=True)
    for violation in report.violations:
        assert violation.rule
        assert violation.path
        assert violation.message
        assert violation.severity in {"error", "warning"}


# ============ R5/V16c: a measured absence is not an absence of measurement ========

def test_v16c_unmeasured_endpoint_must_be_an_evidence_gap(make_root: RootFactory) -> None:
    """The most consequential amendment in Sprint 1.

    The contract could express "tested and found no effect" but not "the only human
    trial of this mechanism never measured a cognitive endpoint". Two brake-atlas claims
    were typed ``clinical_null`` when they were the latter, and read mechanically they
    looked like failed trials.
    """
    report = run_case(make_root, "v16c_unmeasured_endpoint", rule="V16c")
    assert "V16c" in rules_fired(report)
    message = messages(report, "V16c")[0]
    assert "ABSENCE OF MEASUREMENT" in message
    assert "evidence_gap" in message
    assert "graph-inert" in message


def test_v16c_accepts_a_correctly_typed_evidence_gap(make_root: RootFactory) -> None:
    """A gap must be recordable, or agents will type it as a null instead."""
    report = run_case(make_root, "v16c_evidence_gap_accepted")
    assert report.ok, [str(v) for v in report.violations]


def test_v16c_rejects_an_evidence_gap_that_measured_something(make_root: RootFactory) -> None:
    """The conflation is refused in BOTH directions."""
    root = make_root("v16c_evidence_gap_accepted")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "endpoint_measured: not_measured_in_protocol", "endpoint_measured: measured"
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V16c",))
    assert "V16c" in rules_fired(report)
    assert any("not every evidence item reports an unmeasured endpoint" in m
               for m in messages(report, "V16c"))


def test_evidence_gap_is_graph_inert_for_v16(make_root: RootFactory) -> None:
    """A graph-inert claim compiles to no edge, so the efficacy gate has nothing to gate."""
    from blueprint import vocab

    assert vocab.subset("claim_type", "graph_inert_values") == ["evidence_gap"]
    report = run_case(make_root, "v16c_evidence_gap_accepted", rule="V16")
    assert report.ok, [str(v) for v in report.violations]


# ============ R9/V16b-sym: a null must be expressible wherever the positive is ====

def test_v16b_sym_ontology_satisfies_the_derived_union(make_root: RootFactory) -> None:
    """The real ontology must already satisfy the symmetry requirement."""
    root = make_root(None)
    report = validate.run(root, strict=True, only=("V16b-sym",))
    ontology_problems = [v for v in report.violations if "edges.yaml" in v.path]
    assert not ontology_problems, [str(v) for v in ontology_problems]


def test_v16b_sym_brain_region_null_is_expressible() -> None:
    """The case that motivated R9: a cross-clade null with a BrainRegion predictor.

    It previously could not use the null relation, so it compiled as ``CONSTRAINS`` with
    ``direction: unclear`` — and any traversal ignoring direction read the comparative
    atlas's most-cited deflationary result as SUPPORT.
    """
    from blueprint import ontology

    index = ontology.load()
    assert index.is_legal_triple("BrainRegion", "PREDICTS", "CognitivePhenotype")
    assert index.is_legal_triple("BrainRegion", "NO_DETECTED_EFFECT_ON", "CognitivePhenotype")


def test_v16b_sym_requires_the_negated_relation(make_root: RootFactory) -> None:
    """A null edge should say what was tested, not merely that something was absent."""
    root = make_root("v16c_unmeasured_endpoint")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace("  negated_relation: CHANGES_STATE\n", "")
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V16b-sym",))
    assert "V16b-sym" in rules_fired(report)
    assert any("names no `negated_relation`" in m for m in messages(report, "V16b-sym"))


def test_v16b_sym_rejects_an_illegal_negated_triple(make_root: RootFactory) -> None:
    """A null must negate a statement that could have been made."""
    root = make_root("v16c_unmeasured_endpoint")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "  negated_relation: CHANGES_STATE", "  negated_relation: EXPRESSED_IN"
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V16b-sym",))
    assert any("not legal under the relation it claims to negate" in m
               for m in messages(report, "V16b-sym"))


# ============ R10/V-DIR: a characterised interaction versus a shrug ==============

def test_vdir_state_dependent_needs_its_context(make_root: RootFactory) -> None:
    """"We know it varies and we know what with" must not equal "we do not know"."""
    report = run_case(make_root, "vdir_state_dependent_without_context", rule="V-DIR")
    assert "V-DIR" in rules_fired(report)
    message = messages(report, "V-DIR")[0]
    assert "cortical layer" in message
    assert "`unclear` is the honest value" in message


def test_vdir_accepts_a_named_context(make_root: RootFactory) -> None:
    """The rule must admit what it asks for."""
    root = make_root("vdir_state_dependent_without_context")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "  direction: state_dependent",
        '  direction: state_dependent\n  direction_context: "cortical layer of the recorded population"',
    )
    path.write_text(body, encoding="utf-8")
    assert validate.run(root, strict=True, only=("V-DIR",)).ok


def test_vdir_rejects_a_context_without_state_dependence(make_root: RootFactory) -> None:
    """The field names the dependency that makes a sign state-dependent, nothing else."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "  direction: unclear",
        '  direction: unclear\n  direction_context: "a context that does not belong here"',
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V-DIR",))
    assert "V-DIR" in rules_fired(report)


# ============ R6/V3b: between-species claims need at least two species ===========

def test_v3b_between_species_needs_two_species(make_root: RootFactory) -> None:
    """A between-species statement with one species has nothing to compare."""
    report = run_case(make_root, "v3b_between_species_one_species", rule="V3b")
    assert "V3b" in rules_fired(report)
    assert any("needs at least two" in m for m in messages(report, "V3b"))


def test_v3b_warns_when_phylogenetic_control_is_absent(make_root: RootFactory) -> None:
    """A result that survived a mixed model and an uncontrolled regression must differ."""
    root = make_root("v3b_between_species_one_species")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "    species: [SPECIES:NCBITaxon:9606]",
        "    species: [SPECIES:NCBITaxon:9606, SPECIES:NCBITaxon:10090]\n    species_count: 2",
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V3b",))
    assert any("NOT CONVERGENCE" in m for m in messages(report, "V3b"))
    assert [v.severity for v in for_rule(report, "V3b")] == ["warning"]

    body = path.read_text(encoding="utf-8").replace(
        "    species_count: 2",
        "    species_count: 2\n    phylogenetic_control: none\n"
        '    phylogenetic_control_basis: "two species compared with no phylogenetic model"',
    )
    path.write_text(body, encoding="utf-8")
    assert validate.run(root, strict=True, only=("V3b",)).ok


def test_v3b_rejects_an_understated_species_count(make_root: RootFactory) -> None:
    """The count must not understate the comparison it describes."""
    root = make_root("v3b_between_species_one_species")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8").replace(
        "    species: [SPECIES:NCBITaxon:9606]",
        "    species: [SPECIES:NCBITaxon:9606, SPECIES:NCBITaxon:10090]\n"
        "    species_count: 1\n    phylogenetic_control: none\n"
        '    phylogenetic_control_basis: "synthetic fixture"',
    )
    path.write_text(body, encoding="utf-8")
    report = validate.run(root, strict=True, only=("V3b",))
    assert any("must not understate" in m for m in messages(report, "V3b"))


# ============ R7: database-derived facet grading ================================

def test_r7_source_refs_only_on_a_non_gradable_facet(make_root: RootFactory) -> None:
    """Database-derived grading is licensed by the rubric, not by the agent."""
    report = run_case(make_root, "r7_source_refs_not_gradable", rule="V11")
    assert "V11" in rules_fired(report)
    message = next(m for m in messages(report, "V11") if "source_refs" in m)
    assert "database_gradable" in message
    assert "facet_rubric_v0_1.yaml" in message or "rubric" in message


def test_r7_gradable_facets_are_read_from_the_rubric(make_root: RootFactory) -> None:
    """The flag is the authority; the facet name is never hard-coded."""
    from blueprint.validate import _database_gradable_facets

    root = make_root(None)
    rubric = root / "models" / "ranking"
    rubric.mkdir(parents=True, exist_ok=True)
    (rubric / "facet_rubric_v0_1.yaml").write_text(
        "facets:\n  tractability:\n    database_gradable: true\n"
        "  transfer_breadth:\n    database_gradable: false\n",
        encoding="utf-8",
    )
    flagged, readable = _database_gradable_facets(root)
    assert readable
    assert flagged == {"tractability"}


def test_r7_missing_rubric_is_a_warning_not_a_crash(make_root: RootFactory) -> None:
    """The rubric belongs to another agent; its absence must not break validation."""
    from blueprint.validate import _database_gradable_facets

    flagged, readable = _database_gradable_facets(make_root(None))
    assert flagged == set()
    assert readable is False


def test_r7_facet_must_cite_something(make_root: RootFactory) -> None:
    """An assessed facet with neither claim_refs nor source_refs is a bare judgement."""
    from blueprint import records

    with pytest.raises(Exception):
        records.FacetAssessment(
            facet="tractability", assessment_status="assessed", level=3,
            rationale="a grade with nothing behind it",
        )
    records.FacetAssessment(
        facet="tractability", assessment_status="assessed", level=3,
        rationale="graded from a pinned release",
        source_refs=["SRC:DB:placeholder_db:2026-09-17"],
        evidence_basis="database_release",
    )


# ============ R13/V23: animal harm must not wear a clinical label ================

def test_v23_clinical_harm_needs_human_evidence(make_root: RootFactory) -> None:
    """R13: `clinical_harm` is reserved for harm observed IN HUMANS.

    An agent had to record increased seizure susceptibility in mice as `clinical_harm`
    because nothing else fitted, and flagged the forced label itself. Over-stating a
    harm is not the safe error: it misprices every safety constraint that rests on it.
    """
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("  claim_type: expression", "  claim_type: clinical_harm")
    body = body.replace("SPECIES:NCBITaxon:9606", "SPECIES:NCBITaxon:10090")
    body = body.replace("human_relevance: computational_only", "human_relevance: rodent_only")
    path.write_text(body, encoding="utf-8")

    report = validate.run(root, strict=True, only=("V23",))
    assert "V23" in rules_fired(report)
    message = messages(report, "V23")[0]
    assert "preclinical_harm" in message
    assert "laundering" in message


def test_v23_accepts_preclinical_harm_for_animal_evidence(make_root: RootFactory) -> None:
    """The label the agent needed must exist, or the forced choice recurs."""
    from blueprint import vocab

    assert "preclinical_harm" in vocab.values("claim_type")
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("  claim_type: expression", "  claim_type: preclinical_harm")
    body = body.replace("SPECIES:NCBITaxon:9606", "SPECIES:NCBITaxon:10090")
    body = body.replace("human_relevance: computational_only", "human_relevance: rodent_only")
    path.write_text(body, encoding="utf-8")
    assert validate.run(root, strict=True, only=("V23",)).ok


def test_v23_accepts_clinical_harm_with_human_evidence(make_root: RootFactory) -> None:
    """The rule must not fire on the case the label is for."""
    root = make_root("valid_minimal")
    path = root / "evidence" / "claims" / "ontology" / "PLACEHOLDER.yaml"
    body = path.read_text(encoding="utf-8")
    body = body.replace("  claim_type: expression", "  claim_type: clinical_harm")
    body = body.replace("human_relevance: computational_only", "human_relevance: human_observational")
    path.write_text(body, encoding="utf-8")
    assert validate.run(root, strict=True, only=("V23",)).ok


# ============ V22: registered but uncited sources (informational) ================

def test_v22_reports_uncited_sources(make_root: RootFactory) -> None:
    """A registered source implies somebody thought it mattered."""
    root = make_root("valid_minimal")
    source = (root / "evidence" / "sources" / "ontology.yaml").read_text(encoding="utf-8")
    extra = source.replace("SRC:PMID:00000001", "SRC:PMID:00000002").replace(
        'pmid: "00000001"', 'pmid: "00000002"'
    )
    (root / "evidence" / "sources" / "ontology.yaml").write_text(
        source + "\n" + extra[extra.index("- schema_version") :], encoding="utf-8"
    )
    report = validate.run(root, strict=True, only=("V22",))
    assert "V22" in rules_fired(report)
    violation = for_rule(report, "V22")[0]
    assert violation.severity == "info"
    assert "SRC:PMID:00000002" in violation.message
    assert "agent:ontology" in violation.message


def test_v22_never_fails_a_run_even_under_strict(make_root: RootFactory) -> None:
    """`--strict` escalates warnings, never info.

    An informational finding is not a defect in any state of the repository, so
    escalating it would make the gate fire on a repository that is merely incomplete.
    """
    root = make_root("valid_minimal")
    source = (root / "evidence" / "sources" / "ontology.yaml").read_text(encoding="utf-8")
    extra = source.replace("SRC:PMID:00000001", "SRC:PMID:00000002").replace(
        'pmid: "00000001"', 'pmid: "00000002"'
    )
    (root / "evidence" / "sources" / "ontology.yaml").write_text(
        source + "\n" + extra[extra.index("- schema_version") :], encoding="utf-8"
    )
    report = validate.run(root, strict=True, only=("V22",))
    assert report.infos
    assert report.ok, [str(v) for v in report.violations]
    assert report.errors == [], "an info finding must never fail a run"


# ============ source id / identifier cross-check =================================

def test_source_identifier_must_match_its_prefix() -> None:
    """A mismatch means the record was assembled from two different sources."""
    from blueprint import records

    base = {
        "source_id": "SRC:NCT:NCT02024789",
        "source_type": "clinical_trial_registration",
        "title": "Synthetic placeholder trial record",
        "year": 2014,
        "first_author": "Placeholder Sponsor",
        "container": "ClinicalTrials.gov",
        "added_by": "agent:ontology",
        "added_on": "2026-09-17",
        "retrieval": {"method": "ctgov_api"},
    }
    records.Source(**base, identifiers={"nct_id": "NCT02024789"})
    records.Source(**base, identifiers={"nct": "NCT02024789"})  # accepted alias

    with pytest.raises(Exception) as missing:
        records.Source(**base, identifiers={})
    assert "identifiers.nct_id` is empty" in str(missing.value)

    with pytest.raises(Exception) as mismatch:
        records.Source(**base, identifiers={"nct_id": "NCT99999999"})
    assert "assembled from two different sources" in str(mismatch.value)


def test_doi_comparison_is_case_insensitive() -> None:
    """A DOI is registered lowercased, but a recorded DOI may differ in case."""
    from blueprint import records

    records.Source(
        source_id="SRC:DOI:10.1038/s41588-018-0152-6",
        source_type="journal_article",
        title="Synthetic placeholder",
        year=2018,
        first_author="Placeholder AB",
        container="Journal of Placeholders",
        added_by="agent:ontology",
        added_on="2026-09-17",
        retrieval={"method": "known_identifier"},
        identifiers={"doi": "10.1038/S41588-018-0152-6"},
    )


# ============ R14: a zero explained by a reporting gap ==========================

def test_reporting_gap_refs_require_a_search_basis(make_root: RootFactory) -> None:
    """R14: the refs EXPLAIN a zero, they do not replace the explanation.

    Found because an agent, forced by R11 to state what it had searched, discovered its
    own zeros were literature-only — and then found a completed human trial it had
    previously reported did not exist. "Graded 0 because a completed trial reported
    nothing" is a different statement from "graded 0 because nobody tried".
    """
    from blueprint import records

    with pytest.raises(Exception):
        records.FacetAssessment(
            facet="human_intervention_evidence",
            assessment_status="assessed",
            level=0,
            rationale="Searched and found nothing usable.",
            reporting_gap_refs=["SRC:NCT:NCT02024789"],
        )
    records.FacetAssessment(
        facet="human_intervention_evidence",
        assessment_status="assessed",
        level=0,
        rationale="Searched and found nothing usable.",
        search_basis=(
            "ClinicalTrials.gov for this mechanism plus PubMed; one completed trial "
            "posted no results, which is recorded as a reporting gap rather than as "
            "absence of an attempt."
        ),
        reporting_gap_refs=["SRC:NCT:NCT02024789"],
    )


def test_reporting_gap_is_not_counter_evidence(make_root: RootFactory) -> None:
    """A reporting gap is a finding about the EVIDENCE BASE, not about the target.

    Letting it raise counter_level would turn "nobody published" into "it was tested and
    failed", which is the same conflation rule V16c exists to prevent one layer down.
    """
    root = make_root("valid_minimal")
    directory = root / "atlases" / "power" / "assessments"
    directory.mkdir(parents=True, exist_ok=True)
    (root / "targets" / "candidates").mkdir(parents=True, exist_ok=True)
    (root / "targets" / "candidates" / "PLACEHOLDER.yaml").write_text(
        'schema_version: "0.1.0"\ntarget_id: TGT:PLACEHOLDER\nsymbol: PLACEHOLDER\n'
        "lead_atlas: power\nseed_origin: agent_proposed\ndossier_depth: shallow\n"
        "identifiers: {}\nstatus: seed_hypothesis\nprovenance: {created_by: agent:power, "
        'created_on: "2026-09-17", run_id: fixture}\n',
        encoding="utf-8",
    )
    (directory / "PLACEHOLDER.yaml").write_text(
        'schema_version: "0.1.0"\ntarget_id: TGT:PLACEHOLDER\nassessed_by: agent:power\n'
        'assessed_on: "2026-09-17"\nrubric: facet_rubric_v0_1\nscale: evidence_strength_v1\n'
        "facets:\n"
        "  - facet: human_intervention_evidence\n"
        "    assessment_status: assessed\n"
        "    level: 0\n"
        '    rationale: "Searched and found nothing usable."\n'
        '    search_basis: "registry plus literature; one completed trial posted no results"\n'
        "    reporting_gap_refs: [SRC:NCT:NCT02024789]\n"
        "    counter_level: 0\n"
        "    counter_rationale: null\n",
        encoding="utf-8",
    )
    report = validate.run(root, strict=True, only=("V1", "V11", "V21"))
    schema_problems = [v for v in report.violations if "reporting_gap" in v.message]
    assert not schema_problems, [str(v) for v in schema_problems]


def test_reporting_gap_refs_may_appear_at_any_level() -> None:
    """A published trial can coexist with unpublished ones; the refs are not level-bound."""
    from blueprint import records

    records.FacetAssessment(
        facet="human_intervention_evidence",
        assessment_status="assessed",
        level=2,
        rationale="one human study with a relevant endpoint",
        claim_refs=["CLM:power:PLACEHOLDER:001"],
        search_basis="registry plus literature; two further trials posted no results",
        reporting_gap_refs=["SRC:NCT:NCT02024789", "SRC:NCT:NCT02024790"],
    )
