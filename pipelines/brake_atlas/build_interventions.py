#!/usr/bin/env python3
"""Emit one intervention-entity record per compound or probe the brake atlas cites.

Rules this module enforces (contract sections 1.2 and 8, rule V16):

* ``chembl_id`` is only populated where a ChEMBL identifier was returned by a
  ChEMBL tool call in the curation session; otherwise it is ``null`` and
  ``identifier_provenance`` says so. No identifier is written from memory.
* ``max_clinical_phase`` and ``approval`` fields carry ``as_reported`` values and
  name the source that reported them. Where no retrieved source stated a phase,
  the field is ``null``.
* ``blood_brain_barrier`` is ``unknown`` unless a retrieved source stated it. For
  every compound in this atlas no retrieved source stated it, so every record says
  ``unknown``. Central activity inferred from a behavioural result is recorded as
  ``inferred_from_central_effect`` in ``notes``, not as a BBB fact.
* A mechanism record is never efficacy evidence. ``supports_effect_claims`` lists
  the claim ids that carry any effect assertion for this entity, and those claims
  are of type ``causal_perturbation``, ``pharmacodynamic``, ``clinical_efficacy``,
  ``clinical_null`` or ``safety`` -- never ``pharmacology_binding``.

Usage
-----
    .venv/bin/python pipelines/brake_atlas/build_interventions.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "atlases" / "brakes" / "interventions"
CLAIMS_DIR = REPO / "evidence" / "claims" / "brakes"

AGENT = "agent:brakes"
TODAY = "2026-09-17"
RUN_ID = "sprint1-brakes-01"

CHEMBL_PROV = "chembl_compound_search_2026-09-17"
NO_CHEMBL = "not_retrievable_by_name_via_chembl_compound_search_2026-09-17"

ENTITIES: list[dict] = [
    {
        "id": "CPD:CHEMBL3681419",
        "preferred_name": "basmisanil",
        "modality": "small_molecule",
        "mechanism": "MECH:alpha5_gabaa_negative_allosteric_modulation",
        "acts_on_target": "TGT:GABRA5",
        "chembl_id": "CHEMBL3681419",
        "identifier_provenance": CHEMBL_PROV,
        "max_clinical_phase": {
            "value": 2,
            "as_reported": "max_phase: 2",
            "source": "ChEMBL compound record retrieved 2026-09-17",
        },
        "approval": {"status": "not_approved", "as_reported": "first_approval: null", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "synonyms_as_reported": ["RG-1662", "RO5186582"],
        "blood_brain_barrier": "unknown",
        "notes": "Central receptor occupancy and EEG target engagement were reported in the retrieved human sources; that is inferred central activity, not a barrier-permeability measurement.",
        "supports_effect_claims": ["CLM:brakes:GABRA5:004"],
    },
    {
        "id": "CPD:ono_8590580",
        "preferred_name": "ONO-8590580",
        "modality": "small_molecule",
        "mechanism": "MECH:alpha5_gabaa_negative_allosteric_modulation",
        "acts_on_target": "TGT:GABRA5",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "Hippocampal receptor occupancy after oral dosing in rat was reported in the retrieved source, which implies central exposure in that species.",
        "supports_effect_claims": ["CLM:brakes:GABRA5:005"],
    },
    {
        "id": "CPD:l_655_708",
        "preferred_name": "L-655,708",
        "modality": "small_molecule",
        "mechanism": "MECH:alpha5_gabaa_negative_allosteric_modulation",
        "acts_on_target": "TGT:GABRA5",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "Also used in tritiated form as a radioligand to quantify alpha5 receptor density, which is why it appears in this atlas both as a probe and as an assay reagent.",
        "supports_effect_claims": ["CLM:brakes:GABRA5:007"],
    },
    {
        "id": "DRUG:CHEMBL113",
        "preferred_name": "caffeine",
        "modality": "small_molecule",
        "mechanism": "MECH:non_selective_adenosine_receptor_antagonism",
        "acts_on_target": "TGT:ADORA1",
        "chembl_id": "CHEMBL113",
        "identifier_provenance": CHEMBL_PROV,
        "max_clinical_phase": {"value": 4, "as_reported": "max_phase: 4", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "approval": {"status": "approved", "as_reported": "first_approval: 1948", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "synonyms_as_reported": ["anhydrous caffeine", "caffeine citrate (CHEMBL1200569, same parent)"],
        "blood_brain_barrier": "unknown",
        "notes": "Not selective for ADORA1: it antagonises A1 and A2A receptors and at higher concentrations inhibits phosphodiesterases. No claim in this atlas treats a caffeine result as an ADORA1-specific result.",
        "supports_effect_claims": [
            "CLM:brakes:ADORA1:003",
            "CLM:brakes:ADORA1:004",
            "CLM:brakes:ADORA1:005",
            "CLM:brakes:ADORA1:006",
        ],
    },
    {
        "id": "CPD:isrib",
        "preferred_name": "integrated stress response inhibitor (ISRIB)",
        "modality": "small_molecule",
        "mechanism": "MECH:eif2b_decamer_stabilisation",
        "acts_on_target": "TGT:EIF2B_COMPLEX",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "A retrieved structural source describes the molecule as bridging two eIF2B tetramers to stabilise the active decamer. Systemic administration changed rodent learning, which implies central exposure in that species.",
        "supports_effect_claims": [
            "CLM:brakes:EIF2B_COMPLEX:001",
            "CLM:brakes:EIF2B_COMPLEX:002",
            "CLM:brakes:EIF2B_COMPLEX:003",
        ],
    },
    {
        "id": "CPD:dnl343",
        "preferred_name": "DNL343",
        "modality": "small_molecule",
        "mechanism": "MECH:eif2b_activation",
        "acts_on_target": "TGT:EIF2B_COMPLEX",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {
            "value": 3,
            "as_reported": "phase: [PHASE2, PHASE3]",
            "source": "ClinicalTrials.gov record NCT05842941 retrieved 2026-09-17",
        },
        "approval": {"status": "not_approved", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "The registry record for the phase 2/3 regimen specifies motor-function and mortality primary outcomes and no cognitive endpoint. Registry exclusion criteria include a diagnosis of epilepsy or a seizure within six months of randomisation, which this atlas records as an observed design fact and not as a safety conclusion.",
        # Deliberately empty: this compound carries no claim in this atlas, because the
        # only human trial of the mechanism measured no cognitive endpoint (rule V16b).
        "supports_effect_claims": [],
    },
    {
        "id": "CPD:trichostatin_a",
        "preferred_name": "trichostatin A",
        "modality": "small_molecule",
        "mechanism": "MECH:non_selective_histone_deacetylase_inhibition",
        "acts_on_target": "TGT:HDAC2",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "Broad-spectrum inhibitor; it does not isolate HDAC2 and is used here only as a class probe in adult rat in vivo work.",
        "supports_effect_claims": ["CLM:brakes:HDAC2:003"],
    },
    {
        "id": "CPD:frm_0334",
        "preferred_name": "FRM-0334",
        "modality": "small_molecule",
        "mechanism": "MECH:non_selective_histone_deacetylase_inhibition",
        "acts_on_target": "TGT:HDAC2",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {
            "value": 2,
            "as_reported": "phase 2a safety, tolerability, and pharmacodynamic clinical study",
            "source": "PMID 34559230 abstract retrieved 2026-09-17",
        },
        "approval": {"status": "not_approved", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "The retrieved trial report states that plasma exposure did not increase in proportion to dose and that the null result could reflect insufficient exposure or low bioavailability. Central penetration is therefore not established by this source in either direction.",
        "supports_effect_claims": ["CLM:brakes:HDAC2:004"],
    },
    {
        "id": "DRUG:CHEMBL109",
        "preferred_name": "valproic acid",
        "modality": "small_molecule",
        "mechanism": "MECH:non_selective_histone_deacetylase_inhibition",
        "acts_on_target": "TGT:HDAC2",
        "chembl_id": "CHEMBL109",
        "identifier_provenance": CHEMBL_PROV,
        "max_clinical_phase": {"value": 4, "as_reported": "max_phase: 4", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "approval": {"status": "approved", "as_reported": "first_approval: 1978", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "synonyms_as_reported": ["valproate sodium (CHEMBL433)", "divalproex sodium (CHEMBL2105613)"],
        "blood_brain_barrier": "unknown",
        "notes": "ChEMBL records a black-box warning for this compound and its salts. Its anticonvulsant activity is not attributable to deacetylase inhibition, so it is a poor probe for the HDAC2 mechanism and is used here only for human tolerability data.",
        "supports_effect_claims": ["CLM:brakes:HDAC2:005"],
    },
    {
        "id": "CPD:tc_2153",
        "preferred_name": "TC-2153",
        "modality": "small_molecule",
        "mechanism": "MECH:step_phosphatase_inhibition",
        "acts_on_target": "TGT:PTPN5",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": ["8-(trifluoromethyl)-1,2,3,4,5-benzopentathiepin-6-amine hydrochloride"],
        "blood_brain_barrier": "unknown",
        "notes": "A reversible covalent inhibitor acting on the catalytic cysteine, built on a cyclic polysulfide pharmacophore. The retrieved source reports specificity testing against homologous phosphatases and in knockout animals; a reactive covalent chemotype nevertheless carries off-target risk this atlas does not resolve.",
        "supports_effect_claims": ["CLM:brakes:PTPN5:001", "CLM:brakes:PTPN5:002"],
    },
    {
        "id": "DRUG:CHEMBL193240",
        "preferred_name": "roflumilast",
        "modality": "small_molecule",
        "mechanism": "MECH:pan_pde4_inhibition",
        "acts_on_target": "TGT:PDE4B",
        "chembl_id": "CHEMBL193240",
        "identifier_provenance": CHEMBL_PROV,
        "max_clinical_phase": {"value": 4, "as_reported": "max_phase: 4", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "approval": {"status": "approved", "as_reported": "first_approval: 2010", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "synonyms_as_reported": ["Daxas", "Daliresp", "Zoryve"],
        "blood_brain_barrier": "unknown",
        "notes": "Pan-PDE4 inhibitor: it is not selective for PDE4B and this atlas attributes none of its cognitive effects to PDE4B specifically. Its approved indications are respiratory and dermatological, which means the human exposure and tolerability record was accumulated for reasons unrelated to cognition.",
        "supports_effect_claims": ["CLM:brakes:PDE4B:001", "CLM:brakes:PDE4B:002", "CLM:brakes:PDE4B:003"],
    },
    {
        "id": "DRUG:CHEMBL41355",
        "preferred_name": "ezogabine (retigabine)",
        "modality": "small_molecule",
        "mechanism": "MECH:kcnq_channel_opening",
        "acts_on_target": "TGT:KCNQ2",
        "chembl_id": "CHEMBL41355",
        "identifier_provenance": CHEMBL_PROV,
        "max_clinical_phase": {"value": 4, "as_reported": "max_phase: 4", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "approval": {"status": "approved", "as_reported": "first_approval: 2011", "source": "ChEMBL compound record retrieved 2026-09-17"},
        "synonyms_as_reported": ["Potiga", "Trobalt", "D-23129", "XEN-496"],
        "blood_brain_barrier": "unknown",
        "notes": "Acts in the opposite direction to brake release: it opens KCNQ channels and so strengthens the M-current. The ChEMBL record carries black_box_warning true and availability_type 0; this atlas records those field values as retrieved and does not interpret the availability code. Its clinical liabilities are recorded because they constrain the channel as a target in either direction.",
        "supports_effect_claims": ["CLM:brakes:KCNQ2:003"],
    },
    {
        "id": "CPD:zd7288",
        "preferred_name": "ZD7288",
        "modality": "small_molecule",
        "mechanism": "MECH:hcn_channel_block",
        "acts_on_target": "TGT:HCN1",
        "chembl_id": None,
        "identifier_provenance": NO_CHEMBL,
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "An h-channel blocker used in the retrieved sources as a slice and ex vivo probe only; it does not discriminate HCN1 from other HCN subunits.",
        "supports_effect_claims": ["CLM:brakes:HCN1:002", "CLM:brakes:HCN1:003"],
    },
    {
        "id": "BIO:otx2_rk_peptide",
        "preferred_name": "OTX2 RK glycosaminoglycan-binding-domain peptide",
        "modality": "biologic",
        "mechanism": "MECH:otx2_perineuronal_net_capture_blockade",
        "acts_on_target": "TGT:OTX2",
        "chembl_id": None,
        "identifier_provenance": "not_applicable_peptide_probe",
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": ["RK peptide"],
        "blood_brain_barrier": "unknown",
        "notes": "Delivered by direct intracortical infusion in the retrieved source, which bypasses the barrier entirely. Alanine-substituted and scrambled sequences were reported as inactive controls.",
        "supports_effect_claims": ["CLM:brakes:OTX2:001"],
    },
    {
        "id": "BIO:ngr1_decoy_fragment",
        "preferred_name": "function-blocking NgR1 ectodomain fragment",
        "modality": "biologic",
        "mechanism": "MECH:ngr1_ligand_sequestration",
        "acts_on_target": "TGT:RTN4R",
        "chembl_id": None,
        "identifier_provenance": "not_applicable_protein_probe",
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": [],
        "blood_brain_barrier": "unknown",
        "notes": "Delivered intracerebroventricularly in the retrieved rat study, so it does not address barrier penetration. The retrieved evidence is for post-infarction repair with a motor endpoint, not for cognition.",
        "supports_effect_claims": ["CLM:brakes:RTN4R:004"],
    },
    {
        "id": "BIO:osteocalcin",
        "preferred_name": "osteocalcin",
        "modality": "biologic",
        "mechanism": "MECH:gpr158_agonism_by_osteocalcin",
        "acts_on_target": "TGT:GPR158",
        "chembl_id": None,
        "identifier_provenance": "not_applicable_endogenous_hormone",
        "max_clinical_phase": {"value": None, "as_reported": None, "source": None},
        "approval": {"status": "unknown", "as_reported": None, "source": None},
        "synonyms_as_reported": ["OCN"],
        "blood_brain_barrier": "unknown",
        "notes": "An endogenous bone-derived hormone, delivered peripherally in the retrieved source with a central memory readout in aged mice. It is included as an intervention entity because it is the ligand through which GPR158's memory role was demonstrated, and because that role is the opposite sign to the brake framing.",
        "supports_effect_claims": ["CLM:brakes:GPR158:003"],
    },
]


# Per-entity canonical slots and honest scoping, added after the ontology architect
# widened the intervention schema. `first_approval_year` is the canonical integer slot for
# the ChEMBL first-approval fact; `role_in_atlas`, `scope_limits` and `direction_warning`
# exist so a reader cannot mistake a registered probe for a validated intervention.
EXTRAS: dict[str, dict] = {
    "CPD:CHEMBL3681419": {
        "first_approval_year": None,
        "role_in_atlas": "The only alpha5-selective negative allosteric modulator with randomised human cognitive endpoint data located by this atlas.",
        "scope_limits": "Shows that the mechanism can be dosed in humans with measurable EEG target engagement. It does NOT show a cognitive benefit: the trial's primary composite and every secondary cognitive measure were unchanged.",
    },
    "CPD:ono_8590580": {
        "first_approval_year": None,
        "role_in_atlas": "Adult oral pharmacological probe with dose-occupancy data for the alpha5 mechanism in rat.",
        "scope_limits": "Its cognitive readouts are reversal of scopolamine- and MK-801-induced deficits, which is deficit reversal and not enhancement of an intact baseline.",
    },
    "CPD:l_655_708": {
        "first_approval_year": None,
        "role_in_atlas": "Alpha5-selective negative allosteric modulator used both as a pharmacological probe and, in tritiated form, as a radioligand for receptor density.",
        "scope_limits": "The effect recorded here is restoration of potentiation and memory in a mutant with abnormally elevated tonic inhibition. No wild-type effect is reported in the retrieved text.",
    },
    "DRUG:CHEMBL113": {
        "first_approval_year": 1948,
        "role_in_atlas": "The only widely consumed antagonist of this atlas's arousal brake, and the reason the withdrawal-reversal question is answerable at all.",
        "scope_limits": "Not selective for ADORA1: it antagonises A1 and A2A receptors and at higher concentrations inhibits phosphodiesterases. No human caffeine result in this atlas isolates ADORA1, and none tests a caffeine-naive adult.",
        "direction_warning": "Every located human study dosed habitual consumers after abstinence, so the measured direction may be reversal of a withdrawal deficit rather than a gain above an intact baseline.",
    },
    "CPD:isrib": {
        "first_approval_year": None,
        "role_in_atlas": "The compound that defines the translational brake: it enhanced learning in healthy mice and its structure on the human complex supplies the mechanism.",
        "scope_limits": "Rodent behaviour and purified-protein structure only. Its action disappears above a threshold of stress-response activation, so it is state-gated rather than generally active.",
    },
    "CPD:dnl343": {
        "first_approval_year": None,
        "role_in_atlas": "Registered as the evidence that eIF2B activation can be dosed in humans at scale.",
        "scope_limits": "Carries NO claim in this atlas. The phase 2/3 regimen specified motor-function and mortality outcomes and no cognitive endpoint, and an endpoint that was never measured must not become an edge (rule V16b).",
    },
    "CPD:trichostatin_a": {
        "first_approval_year": None,
        "role_in_atlas": "Adult in vivo class probe for the transcriptional brake.",
        "scope_limits": "Broad-spectrum: it does not isolate HDAC2. Its effect was confined to an intermediate phase of potentiation lasting days and was absent from the phase lasting weeks.",
    },
    "CPD:frm_0334": {
        "first_approval_year": None,
        "role_in_atlas": "The only randomised trial of an HDAC inhibitor in a CNS indication located by this atlas.",
        "scope_limits": "Not HDAC2-selective, and the endpoint was a protein biomarker rather than cognition. It failed to move that biomarker, and the authors attribute the null partly to exposure, so it is a programme failure and not necessarily a target failure.",
    },
    "DRUG:CHEMBL109": {
        "first_approval_year": 1978,
        "role_in_atlas": "Source of the only human dose-escalation tolerability data for deacetylase inhibition in healthy adults.",
        "scope_limits": "Its anticonvulsant activity is not attributable to deacetylase inhibition, so it is a poor probe for the HDAC2 mechanism. Cognitive testing in that study was a safety measure and cannot detect enhancement.",
    },
    "CPD:tc_2153": {
        "first_approval_year": None,
        "role_in_atlas": "The only STEP inhibitor with in vivo cognitive data located by this atlas.",
        "scope_limits": "Both results are deficit reversal in disease models from one laboratory, with no healthy-baseline arm and no human exposure. A reversible covalent cyclic-polysulfide pharmacophore carries off-target reactivity risk this atlas does not resolve.",
    },
    "DRUG:CHEMBL193240": {
        "first_approval_year": 2010,
        "role_in_atlas": "The source of the only above-baseline cognitive improvement in healthy human adults anywhere in this atlas.",
        "scope_limits": "Pan-PDE4: it does not isolate PDE4B. The benefit is confined to verbal recall, absent on spatial and working-memory tasks, and all three located studies have overlapping authorship. Its approvals are respiratory and dermatological.",
        "direction_warning": "The benefit appeared at the LOWEST of three doses, with adverse events and no benefit at the highest, so exposure cannot be titrated upward toward a larger effect.",
    },
    "DRUG:CHEMBL41355": {
        "first_approval_year": 2011,
        "role_in_atlas": "Registered because it is the only clinical-stage modulator of this atlas's M-current brake, and because its liabilities constrain the channel as a target.",
        "scope_limits": "No cognitive endpoint in either direction. The ChEMBL record carries black_box_warning true and availability_type 0; this atlas records those field values as retrieved and does not interpret the availability code.",
        "direction_warning": "Acts in the OPPOSITE direction to brake release: it OPENS KCNQ channels and so strengthens the M-current. Its urinary-retention liability constrains the strengthening direction, not the release direction, and must not be read as a brake-release liability.",
    },
    "CPD:zd7288": {
        "first_approval_year": None,
        "role_in_atlas": "Slice and ex vivo h-current blocker used to attribute dendritic effects to the current.",
        "scope_limits": "Does not discriminate HCN1 from other HCN subunits, and was used only ex vivo.",
    },
    "BIO:otx2_rk_peptide": {
        "first_approval_year": None,
        "role_in_atlas": "The only adult manipulation in this atlas that reopened a cortical critical period.",
        "scope_limits": "Delivered by direct intracortical infusion, which bypasses the barrier entirely, and measured on a sensory rather than a cognitive endpoint.",
        "direction_warning": "Its consequence was state-dependent within a single study: reopened plasticity degraded acuity in healthy adults under deprivation and restored binocular vision in amblyopic animals. There is no fixed direction of benefit.",
    },
    "BIO:ngr1_decoy_fragment": {
        "first_approval_year": None,
        "role_in_atlas": "Evidence that the structural-plasticity brake is pharmacologically accessible in adults.",
        "scope_limits": "Post-infarction repair with a motor endpoint, delivered intracerebroventricularly. Nothing here shows a cognitive effect in intact tissue, and the loss-of-function cognitive evidence for this receptor runs the other way.",
    },
    "BIO:osteocalcin": {
        "first_approval_year": None,
        "role_in_atlas": "The ligand through which GPR158's role in hippocampal memory was demonstrated, and the reason this atlas records the target's sign as unresolved.",
        "scope_limits": "An endogenous hormone given peripherally to aged mice with declining circulating levels, so the result is restoration toward a younger setpoint rather than enhancement.",
        "direction_warning": "This pathway makes GPR158 memory-PROMOTING in CA3, the opposite sign to the prefrontal excitability-brake literature. GPR158 has no single direction in this atlas.",
    },
}


def main() -> int:
    known: dict[str, str] = {}
    for path in sorted(CLAIMS_DIR.glob("*.yaml")):
        for claim in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            known[claim["claim_id"]] = claim["claim_type"]

    errors = []
    for e in ENTITIES:
        for cid in e["supports_effect_claims"]:
            if cid not in known:
                errors.append(f"{e['id']}: unknown claim {cid}")
            elif known[cid] == "pharmacology_binding":
                errors.append(f"{e['id']}: claim {cid} is pharmacology_binding and cannot carry an effect (rule V16)")
    if errors:
        for err in errors:
            print(f"ERROR {err}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for e in ENTITIES:
        local = e["id"].split(":", 1)[1]
        extras = EXTRAS[e["id"]]
        notes = [e["notes"]]
        if e["approval"].get("as_reported"):
            notes.append(f'ChEMBL approval field as returned: {e["approval"]["as_reported"]} '
                         f'(status {e["approval"]["status"]}). Approval somewhere for some '
                         f'indication is never evidence of cognitive efficacy.')
        doc = {
            "schema_version": "0.1.0",
            "id": e["id"],
            "preferred_name": e["preferred_name"],
            "modality": e["modality"],
            "mechanism": e["mechanism"],
            "acts_on_target": e["acts_on_target"],
            "identifiers": {
                "chembl_id": e["chembl_id"],
                "identifier_provenance": e["identifier_provenance"],
            },
            # Canonical database-fact slots (rule V9). Their numbers are admissible only
            # because `max_clinical_phase.source` names where they came from.
            "max_clinical_phase": e["max_clinical_phase"],
            "first_approval_year": extras["first_approval_year"],
            "synonyms_as_reported": e["synonyms_as_reported"],
            "blood_brain_barrier": e["blood_brain_barrier"],
            "role_in_atlas": extras["role_in_atlas"],
            "scope_limits": extras["scope_limits"],
            **({"direction_warning": extras["direction_warning"]} if "direction_warning" in extras else {}),
            "notes": notes,
            "supports_effect_claims": e["supports_effect_claims"],
            "recorded_by": AGENT,
            "recorded_on": TODAY,
            "provenance": {"created_by": AGENT, "created_on": TODAY, "run_id": RUN_ID, "method": "database_ingestion"},
        }
        (OUT / f"{local}.yaml").write_text(
            "# Intervention entity — written by agent:brakes (Cognitive Brake Atlas).\n"
            "# Generated by pipelines/brake_atlas/build_interventions.py; edit the builder.\n"
            "# A mechanism or binding record is never efficacy evidence (contract rule V16).\n"
            "# `blood_brain_barrier` is `unknown` unless a retrieved source stated it.\n"
            + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )
    print(f"wrote {len(ENTITIES)} intervention entities to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
