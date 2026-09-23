#!/usr/bin/env python3
"""Build reports/project_truth_table.{md,csv} — one row per tracked hypothesis.

Why this is a script and not a hand-written document
----------------------------------------------------
A truth table is only useful if it is CURRENT. A hand-written one drifts from the
records the moment anything changes, and the drift is invisible because the document
still reads as authoritative. Defining the rows as data and emitting both formats from
one source means the markdown and the CSV can never disagree with each other, and a
change of status shows up as a diff.

The rows are curated, not derived
---------------------------------
The per-row judgements below were made by reading the repository's own records — claims,
facet assessments, red-team audits, registry searches, ranking outputs — and every
`why` field points at the artefact it rests on. They are NOT automatically computed from
the graph, and pretending otherwise would be the more dangerous lie: `current_status` is
a judgement, and it is recorded as one.

What the statuses mean
----------------------
SUPPORTED                        adult human causal evidence, replicated
PROMISING_BUT_UNRESOLVED         real evidence, decisive question still open
UNRESOLVED                       insufficient evidence either way
DOWNGRADED                       was rated higher; a specific finding lowered it
CONTRADICTED_IN_STUDIED_CONTEXT  tested in humans and failed IN THAT CONTEXT — which is
                                 not the same as "the biology is wrong"
NOT_ASSESSED                     no evidence in this repository at all

The distinction that does the most work is between the last two. A null trial in
schizophrenia does not refute a mechanism in healthy adults, and an empty row does not
refute anything at all.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MD = REPO_ROOT / "reports" / "project_truth_table.md"
CSV = REPO_ROOT / "reports" / "project_truth_table.csv"
UPDATED = "2026-09-18"

COLUMNS = [
    "hypothesis", "supporting_evidence", "contradictory_evidence", "human_genetics",
    "human_molecular", "human_intervention", "animal_causal", "comparative",
    "adult_relevance", "developmental_relevance", "replication", "current_status",
    "why", "next_kill_test", "evidence_dependencies", "last_updated",
]

# Vocabulary for the per-modality columns. These are three DIFFERENT states and the
# repository's recurring bug is collapsing them:
#   none            no evidence of this kind exists here
#   not_measured    the studies exist but did not measure this
#   measured_null   measured, and the answer was no
NOT_ASSESSED = "none"

ROWS: list[dict[str, str]] = [

    # ------------------------------------------- architecture-level hypotheses -------
    # These are the field-level claims the project's target selection silently assumes.
    # Several are assessed here for the first time, and most come back thinner than the
    # confidence with which they are usually asserted.
    dict(
        hypothesis="COGNITION IS SUBSTANTIALLY GENETIC (population variance in cognitive "
                   "ability has a large heritable component)",
        supporting_evidence="the repository's entire genetics base presupposes and is "
                            "consistent with it: 10,741 cognition-trait associations across "
                            "4,459 mapped genes, GWAS Catalog release 2026-09-13, plus "
                            "Open Targets L2G credible sets",
        contradictory_evidence="none in this repository",
        human_genetics="extensive, and POLYGENIC — the architecture is thousands of "
                       "small-effect loci, which is itself the result",
        human_molecular="one bulk-tissue expression dataset; no QTL or colocalisation",
        human_intervention="not applicable — this is a claim about variance, not a target",
        animal_causal="not applicable", comparative="not applicable",
        adult_relevance="LOW — heritability of a trait says nothing about whether an adult "
                        "can change it",
        developmental_relevance="unresolved; heritability estimates do not localise to a "
                                "life stage",
        replication="the most replicated finding the repository touches",
        current_status="SUPPORTED",
        why="THE ONLY `SUPPORTED` ROW IN THIS TABLE — and it licenses nothing. This project "
            "did not itself test heritability; it ingested association data that presupposes "
            "it. More importantly, heritability is a statement about variance in a "
            "population, not about modifiability in an individual, and a highly heritable "
            "trait can be highly modifiable. The one hypothesis that survives is the one "
            "that cannot tell you what to do.",
        next_kill_test="Not worth attacking. The productive question is the next row down: "
                       "whether that polygenic architecture contains any single adult-"
                       "modifiable control parameter.",
        evidence_dependencies="evidence/claims/alphacognition/gwas_catalog_derived.yaml; "
                              "opentargets_l2g_derived.yaml",
    ),
    dict(
        hypothesis="A SINGLE GENIUS GENE — one gene of large effect substantially determines "
                   "cognitive ability",
        supporting_evidence="none",
        contradictory_evidence="a genome-wide sweep maps 10,741 cognition associations to "
                               "4,459 distinct genes; the strongest seed gene (CKB) appears "
                               "in 5 studies and would rank outside the top 500; no gene in "
                               "the repository has causal-gene attribution above level 2",
        human_genetics="polygenic architecture with thousands of small-effect loci — this "
                       "is measured, not assumed",
        human_molecular="no colocalisation anywhere to nominate a dominant gene",
        human_intervention="not applicable",
        animal_causal="single-gene manipulations produce effects in animals and none has "
                      "transferred to adult humans",
        comparative="not applicable",
        adult_relevance="not applicable", developmental_relevance="not applicable",
        replication="the polygenic result is replicated across every cognitive GWAS here",
        current_status="CONTRADICTED_IN_STUDIED_CONTEXT",
        why="Contradicted for common variation in studied populations, which is where the "
            "data are. Stated precisely, because the strict version is NOT refuted: rare "
            "large-effect variants exist (GRIN2B de novo variants, 86 individuals), and they "
            "act in the DELETERIOUS direction and cause neurodevelopmental disorder. Large "
            "single-gene effects on cognition are real and they break things.",
        next_kill_test="None needed. The row exists so the project cannot drift back toward "
                       "single-gene thinking without passing it.",
        evidence_dependencies="pipelines/discovery/sweep_cognition_genes.py; "
                              "targets/discovered/discovered_registry.yaml; reports/sprint1_summary.md",
    ),
    dict(
        hypothesis="EXTREME COGNITION IS QUALITATIVELY DISTINCT from ordinary-range cognition",
        supporting_evidence="none in this repository",
        contradictory_evidence="none in this repository",
        human_genetics="not assessed here", human_molecular="not assessed here",
        human_intervention="not applicable", animal_causal="not applicable",
        comparative="not applicable",
        adult_relevance="unknown", developmental_relevance="unknown",
        replication="not applicable",
        current_status="NOT_ASSESSED",
        why="ZERO ARTEFACTS. And this matters more than an empty row usually would: X01 "
            "adopted the CONTINUOUS assumption as a working constraint, taken from unverified "
            "external prose plus an unreferenced appeal to 'this repository's polygenic "
            "picture' with no claim id behind it. So the project is currently operating on an "
            "assumed answer to an unassessed question. The red team flagged this (finding f11) "
            "and it is not yet fixed.",
        next_kill_test="Assemble the extreme-cognition evidence map independently, or obtain "
                       "the external source list. Until then the assumption should be moved "
                       "out of `methodological_constraints_adopted`.",
        evidence_dependencies="analyses/external/X01_cell_type_enrichment.yaml; "
                              "evidence/audits/red_team/SPRINT2_ARTEFACTS.yaml#f11",
    ),
    dict(
        hypothesis="PYRAMIDAL-CELL SPECIFICITY — cognition-associated variation acts "
                   "preferentially through excitatory pyramidal neurons",
        supporting_evidence="X01 reports a pyramidal association (beta ~0.097, nominal "
                            "P ~0.011) — INERT, unverified, cited by nothing",
        contradictory_evidence="a second reported figure is P=0.08",
        human_genetics="cohort overlap with this repository's base is unresolvable",
        human_molecular="INERT — the only cell-type analysis is "
                        "external_analysis_unverified, excluded from evidential classes and "
                        "enforced inert by validator rule V-EXT. No evidential cell-type "
                        "record exists at all",
        human_intervention="not applicable", animal_causal="not assessed",
        comparative="not assessed",
        adult_relevance="unstated in the source", developmental_relevance="unstated",
        replication="none; no artefacts delivered",
        current_status="UNRESOLVED",
        why="Both over-readings are refused. Two nominal P-values near 0.011 are not proof "
            "that pyramidal cells are the locus; P=0.08 is not proof that they do not matter. "
            "Following X01's own methodological instruction, the discovery sweep was run "
            "CELL-CLASS-AGNOSTIC and genome-wide with no pyramidal gate — the one X01 "
            "constraint that is safe to adopt before verification, because it only widens "
            "what gets examined.",
        next_kill_test="An independent, verifiable cell-type enrichment with its conditioning "
                       "specification and source list — enough to make cohort overlap "
                       "computable.",
        evidence_dependencies="analyses/external/X01_cell_type_enrichment.yaml; V-EXT",
    ),
    dict(
        hypothesis="SYNAPTIC BIOLOGY is the dominant locus of cognition-relevant variation",
        supporting_evidence="the overwhelming majority of this repository's targets and "
                            "claims are synaptic — receptors, channels, plasticity machinery",
        contradictory_evidence="that majority is a SELECTION ARTEFACT: the seed list was "
                               "supplied, and the discovery sweep found only 9 of 31 seed "
                               "genes anywhere in 10,741 cognition associations, with 151 "
                               "non-seed genes carrying 10 or more distinct studies",
        human_genetics="positional mapping implicates many non-synaptic genes (FOXO3, EXOC4, "
                       "ZNF638, MMS22L, ARHGAP15) that no atlas covers",
        human_molecular="bulk expression only; no cell-type or QTL layer to localise anything",
        human_intervention="every registry-searched target is synaptic, which is circular",
        animal_causal="strong and synaptic — and the animal literature is itself "
                      "synapse-biased",
        comparative="not assessed",
        adult_relevance="synaptic mechanisms are the most plausibly adult-modifiable class, "
                        "which is precisely why they were selected — and why their prevalence "
                        "here is not evidence",
        developmental_relevance="several leading synaptic targets act developmentally",
        replication="not testable from a biased sample",
        current_status="UNRESOLVED",
        why="This repository CANNOT currently test this hypothesis, and that is the finding. "
            "Its evidence base was assembled by selecting synaptic targets, so the "
            "preponderance of synaptic evidence measures the selection criterion. The "
            "discovery sweep is the first unbiased look and it does not support synaptic "
            "dominance — it mostly implicates genes the atlases have never examined.",
        next_kill_test="Pathway-annotate the 4,459 swept genes and ask whether synaptic terms "
                       "are enriched above a gene-size and gene-density matched background. "
                       "This is cheap and has not been done.",
        evidence_dependencies="pipelines/discovery/sweep_cognition_genes.py; "
                              "targets/discovered/discovered_registry.yaml; targets/seed_registry.yaml",
    ),
    dict(
        hypothesis="DEVELOPMENTAL WIRING — adult cognitive capacity is largely set during "
                   "development",
        supporting_evidence="this is the repository's most persistent empirical pattern. "
                            "GRIN2B: human variants act prenatally and cause "
                            "neurodevelopmental disorder. RGS14: the protein is undetectable "
                            "at birth and its only causal evidence is a germline knockout. "
                            "OTX2 and RTN4R: critical-period mechanisms. Four red-team "
                            "findings of `developmental_effect_mistaken_for_adult`",
        contradictory_evidence="adult-onset perturbations DO produce effects in animals "
                               "(CRTC1, GPR158, HCN1, EIF2B, KL) — the adult brain is not "
                               "fixed",
        human_genetics="the only locus-to-gene-resolved human genetics in the repository "
                       "(GRIN2B de novo and rare-variant burden) is developmental and "
                       "deleterious",
        human_molecular="the NR2B-to-NR2A switch is direct evidence that adult and juvenile "
                        "synaptic biology differ",
        human_intervention="no adult intervention has demonstrated durable gain",
        animal_causal="strong for the developmental side; weaker and thinner for adult-onset",
        comparative="not assessed",
        adult_relevance="THIS IS THE CRUX OF THE WHOLE PROJECT",
        developmental_relevance="extensive",
        replication="the pattern recurs across four independent targets",
        current_status="PROMISING_BUT_UNRESOLVED",
        why="Uncomfortable for the project's premise and the evidence keeps pointing at it. "
            "Every time a target's causal evidence is examined closely, the perturbation "
            "turns out to have happened during development even when the read-out was adult. "
            "That does not prove adult capacity is fixed — adult-onset manipulations do work "
            "in animals — but the ASYMMETRY in evidence quality is real and systematic, and "
            "the project's ranking model already caps targets for it.",
        next_kill_test="For any leading target, an adult-onset, time-restricted perturbation "
                       "with a cognitive read-out. This single design would resolve more here "
                       "than any new target would.",
        evidence_dependencies="AUD:red_team:{GRIN2B,RGS14,OTX2,RTN4R}:001; "
                              "CLM:alphacognition:GRIN2B:004-006",
    ),
    dict(
        hypothesis="ADULT SYNAPTIC CONTROL — adult cognitive capacity can be raised by "
                   "modulating synaptic parameters in the adult brain",
        supporting_evidence="adult-inducible and adult-pharmacological animal perturbations "
                            "exist for CRTC1, GPR158, HCN1, EIF2B and KL; PDE4B and CHRM1 "
                            "have human cognitive results in adults",
        contradictory_evidence="no target has causal-gene attribution above level 2; "
                               "`tier_1_analyse_next` is EMPTY; the best-evidenced human "
                               "test of an adult synaptic manipulation (GABRA5) is a "
                               "replicated NULL; CHRM1's supporting trial was withdrawn "
                               "before enrolment over an animal toxicology finding",
        human_genetics="no adult-specific causal gene assignment anywhere",
        human_molecular="no colocalisation; nothing localises an adult mechanism",
        human_intervention="PDE4B (roflumilast, pan-PDE4) and CHRM1 (one unreplicated "
                           "developer-affiliated secondary analysis) are the only positive "
                           "adult human cognitive results, and neither is target-selective",
        animal_causal="present, and repeatedly shown not to transfer",
        comparative="mouse and rat carry 1:1 orthologues for 96% of targets, so transfer "
                    "failures are NOT orthology failures — they are physiology and timing",
        adult_relevance="the entire hypothesis",
        developmental_relevance="confounds much of the supporting animal evidence",
        replication="no positive adult human cognitive result in this repository has replicated",
        current_status="UNRESOLVED",
        why="THE PROJECT'S CENTRAL HYPOTHESIS, and after two sprints it is neither supported "
            "nor refuted. The honest summary: the adult brain is demonstrably modifiable in "
            "animals, and no one has yet shown a durable above-baseline gain in healthy adult "
            "humans from any target here. The orthology audit sharpens the diagnosis — the "
            "genes are present one-to-one in the model species, so the failure is not a "
            "missing gene but a different physiology, which is a more tractable problem.",
        next_kill_test="Raise any single target to causal-gene level 3 with adult human "
                       "evidence. Everything downstream, including chemistry, waits on this.",
        evidence_dependencies="reports/target_ranking_v0_1.csv; reports/sprint1_summary.md; "
                              "atlases/comparative_v2/orthology.yaml",
    ),
    dict(
        hypothesis="ASTROCYTE DOMINANCE — astrocytic support, notably lactate shuttling, "
                   "limits cognitive performance",
        supporting_evidence="the power atlas holds astrocyte-neuron lactate shuttle claims "
                            "and the MCT transporter family (SLC16A1/3/7)",
        contradictory_evidence="one paper (PMID 21376239) supplies the claims for FOUR "
                               "'separate' targets, so the apparent breadth is one source "
                               "counted four times; SLC16A1 carries red-team findings of both "
                               "`publication_bias` and `systemic_adverse_effects`; the ANLS "
                               "model is contested in its own literature",
        human_genetics="SLC16A1 has monogenic human evidence; causal-gene attribution 0",
        human_molecular="bulk expression only",
        human_intervention="none — the power-atlas targets carry no registry search at all "
                           "and their zeros come from a Sprint-1 literature route",
        animal_causal="present, and concentrated in a small shared source set",
        comparative="not assessed",
        adult_relevance="plausible and untested",
        developmental_relevance="not the main issue",
        replication="poor — the same few sources recur across the family",
        current_status="UNRESOLVED",
        why="The clearest case in the repository of `duplicated_evidence`: three transporters "
            "and a pathway claim that look like four lines of support and are one. Nothing "
            "here refutes astrocytic involvement; there is simply much less independent "
            "evidence than the target count suggests.",
        next_kill_test="Run target-directed registry searches for the seven power-atlas "
                       "targets, which have never had one; and count independent sources "
                       "after applying convergence rule D002.",
        evidence_dependencies="evidence/claims/power/*.yaml; "
                              "atlases/convergence/dependency_rules.yaml D002",
    ),
    dict(
        hypothesis="ENERGY DOMINANCE — metabolic supply is a binding constraint on adult "
                   "cognitive performance (the COGNITIVE POWER ENVELOPE)",
        supporting_evidence="the power atlas: 10 interventions, 7 assessments, creatine and "
                            "MCT human work, a coherent theoretical model in THEORY.md §1",
        contradictory_evidence="Sprint 1's own conclusion that the POWER factor MAY NOT BE "
                               "LIMITING AT ALL in healthy adults — THEORY.md §1.4 is titled "
                               "exactly that. Multiplicativity is declared a modelling "
                               "choice, not a law",
        human_genetics="SLC16A1 and SLC6A8 have monogenic evidence; both are "
                       "rescue-of-deficit, not enhancement",
        human_molecular="bulk expression only",
        human_intervention="present for creatine; graded 2/counter 3 with a "
                           "`rescue_mistaken_for_enhancement` finding",
        animal_causal="present", comparative="not assessed",
        adult_relevance="adult human creatine data exist and are about repletion",
        developmental_relevance="SLC6A8 deficiency is developmental",
        replication="the rescue findings replicate; the enhancement findings do not exist",
        current_status="DOWNGRADED",
        why="Downgraded by the project's own theory document before any red team touched it. "
            "The recurring pattern is that metabolic interventions help where something is "
            "DEPLETED — creatine in vegetarians, in sleep deprivation, in transporter "
            "deficiency — and do little at a healthy adult baseline. A constraint that is not "
            "binding cannot be relaxed to gain anything. This is also the finding that makes "
            "the goal-gated interface hypothesis interesting: an interface limit would still "
            "bind when no capacity is exhausted.",
        next_kill_test="A healthy, non-depleted, non-sleep-deprived adult baseline with a "
                       "cognitive endpoint. Most existing evidence fails this design.",
        evidence_dependencies="THEORY.md §1.4; atlases/power/; AUD:red_team:{SLC6A8,SLC16A1}:001",
    ),
    dict(
        hypothesis="MYELIN AND NETWORK TIMING — conduction speed and temporal precision limit "
                   "cognitive capacity",
        supporting_evidence="none in this repository",
        contradictory_evidence="none in this repository",
        human_genetics=NOT_ASSESSED, human_molecular=NOT_ASSESSED,
        human_intervention=NOT_ASSESSED, animal_causal=NOT_ASSESSED,
        comparative=NOT_ASSESSED,
        adult_relevance="unknown — myelination continues into adulthood, which makes this "
                        "one of the few plausibly adult-modifiable structural parameters",
        developmental_relevance="unknown",
        replication="not applicable",
        current_status="NOT_ASSESSED",
        why="ZERO ARTEFACTS — no target, claim, atlas or state variable addresses white "
            "matter, conduction velocity or oligodendrocyte biology. This is a whole axis of "
            "cognitive neuroscience the project has simply not touched, and its absence is a "
            "selection artefact of the supplied seed list rather than a judgement. Notably, "
            "adult myelination is activity-dependent, which places it squarely inside the "
            "activity-gated mechanism class the theory nodes point at.",
        next_kill_test="Ask whether the swept cognition genes are enriched for "
                       "oligodendrocyte and myelin annotations. The data are already in hand.",
        evidence_dependencies="none — this row records an absence",
    ),
    dict(
        hypothesis="CLASSICAL NEUROMODULATOR DOMINANCE — dopaminergic, serotonergic, "
                   "cholinergic and adenosinergic tone are the main levers",
        supporting_evidence="the largest human intervention literature in the repository by "
                            "far — ADORA1 434 studies, HTR2A 316, DRD1 47, CHRM1 38 — plus "
                            "the only healthy-adult human cognitive result (CHRM1)",
        contradictory_evidence="EVERY ONE of these targets is downgraded, and for four "
                               "different reasons: ADORA1 `rescue_mistaken_for_enhancement`, "
                               "DRD1 `dose_response_inversion` and `psychiatric_liability`, "
                               "HTR2A `psychiatric_liability`, CHRM1 the heaviest systemic "
                               "liability burden in the cohort (safety level 4) with its key "
                               "trial withdrawn over animal toxicology",
        human_genetics="weak across all four; none above causal-gene level 0 except by "
                       "positional mapping",
        human_molecular="bulk expression only",
        human_intervention="by far the most-tested class in humans — and the testing has "
                           "mostly not measured cognition, or has measured rescue",
        animal_causal="extensive", comparative="not assessed",
        adult_relevance="high — these are the classes with real adult human exposure",
        developmental_relevance="not the main issue for this class",
        replication="extensive replication of clinical effects; no replicated healthy-adult "
                    "cognitive enhancement",
        current_status="DOWNGRADED",
        why="The most-tested hypothesis in the repository and the one with the clearest "
            "verdict: decades of human exposure, enormous trial volume, and no replicated "
            "above-baseline cognitive gain in healthy adults. The recurring failure mode is "
            "that neuromodulator manipulations move state — arousal, motivation, mood — and "
            "state changes are read as capacity changes. Where a baseline is depleted "
            "(caffeine after withdrawal) the benefit is restoration.",
        next_kill_test="Nothing new. The informative work is re-reading the 40 trials with "
                       "posted cognitive results already sitting in the extraction queue, "
                       "51 of which belong to this class.",
        evidence_dependencies="AUD:red_team:{ADORA1,DRD1,HTR2A,CHRM1}:001; "
                              "evidence/registry_searches/{ADORA1,HTR2A,DRD1,CHRM1}.yaml",
    ),
    dict(
        hypothesis="MATHEMATICAL BIOLOGY BEYOND g — mathematical ability has biology "
                   "separable from general cognitive ability",
        supporting_evidence="'mathematical ability' appears as a distinct trait in Open "
                            "Targets L2G credible sets for CRTC1, GRIN2B and PDE4B",
        contradictory_evidence="those rows come from EDUCATIONAL-ATTAINMENT GWAS. CRTC1's "
                               "entire human genetic grade rested on a single 'self-reported "
                               "maths ability' association and was downgraded 3 to 1 by the "
                               "cohort's only unresolved CRITICAL red-team finding",
        human_genetics="present but confounded — the trait panel marks educational "
                       "attainment `use_in_ranking: proxy_only` precisely because of this",
        human_molecular="not assessed", human_intervention="not assessed",
        animal_causal="not applicable — there is no animal model of mathematics",
        comparative="not assessed",
        adult_relevance="unknown", developmental_relevance="schooling is the obvious confound",
        replication="no",
        current_status="NOT_ASSESSED",
        why="The repository holds maths-ability associations but has never asked whether they "
            "are separable from g, and cannot: self-reported mathematical ability inside an "
            "educational-attainment GWAS is a measure of schooling, self-concept and "
            "attainment as much as of arithmetic biology. Treating it as a distinct cognitive "
            "phenotype is exactly the endpoint substitution that produced this project's only "
            "critical audit finding.",
        next_kill_test="Genetic correlation between a properly measured mathematical "
                       "phenotype and g, in a cohort where both are directly assessed rather "
                       "than self-reported.",
        evidence_dependencies="AUD:red_team:CRTC1:001; "
                              "atlases/alphacognition/cognitive_trait_panel.yaml",
    ),
    dict(
        hypothesis="ACTIVITY-GATED PLASTICITY — the useful mechanism class is one whose "
                   "effect is gated by recent neural activity rather than set by exposure",
        supporting_evidence="synaptic tagging and capture and neuronal memory allocation are "
                            "the mechanism families the theory nodes point at; CRTC1, HDAC2 "
                            "and GRIN2B are the repository's bearing targets",
        contradictory_evidence="none — and no support either. NO TARGET IN THIS REPOSITORY "
                               "HAS BEEN ASSESSED FOR ACTIVITY-GATING AT ALL",
        human_genetics="not assessed", human_molecular="not assessed",
        human_intervention="not_measured — no study here separated prioritised from "
                           "incidental material, which is the measurement this requires",
        animal_causal="the bearing targets have adult-onset animal evidence, none of which "
                      "tested selectivity",
        comparative="not assessed",
        adult_relevance="adult by construction",
        developmental_relevance="not applicable",
        replication="not applicable",
        current_status="NOT_ASSESSED",
        why="This is where both project-lead theory nodes converge — SE2 'activity as the "
            "address' and C1 'gating' are the same requirement stated from opposite ends. It "
            "is also where this project came closest to fooling itself: the selective-encoding "
            "node originally used this idea to EXCLUDE tonically acting candidates as a class, "
            "which inverted its own guard and converted 'not assessed here' into 'this "
            "molecule acts tonically'. Retracted 2026-09-18. The corrected form is a "
            "measurement demand, not a filter.",
        next_kill_test="For any bearing target, an animal study testing whether enhancement "
                       "is confined to task-engaged representations — the SE6 contrast. No "
                       "such study has been identified for any target here.",
        evidence_dependencies="theory/selective_encoding_criteria.yaml; "
                              "theory/goal_gated_plasticity_retrieval.yaml; "
                              "evidence/audits/red_team/SPRINT2_ARTEFACTS.yaml#f3",
    ),

    # ------------------------------------------------------------------ theory ------
    dict(
        hypothesis="SELECTIVE ENCODING — an enhancer should raise the contrast between "
                   "prioritised and incidental encoding, not memory globally",
        supporting_evidence="none in this repository; the hypothesis is a specification, "
                            "recorded as THEORY:selective_encoding",
        contradictory_evidence="none — no study in the repository measured the decisive quantity",
        human_genetics=NOT_ASSESSED, human_molecular=NOT_ASSESSED,
        human_intervention="not_measured — no repository study separated prioritised from "
                           "incidental material",
        animal_causal="partially bearing: CRTC1, HDAC2, GRIN2B (SE2/SE3), none tested for selectivity",
        comparative=NOT_ASSESSED,
        adult_relevance="adult by construction",
        developmental_relevance="not applicable",
        replication="not applicable — no result to replicate",
        current_status="NOT_ASSESSED",
        why="All seven criteria SE1-SE7 are not_assessed_in_repository or "
            "partially_addressed. The hypothesis changes the MEASURED QUANTITY to a "
            "difference-in-differences, which makes most existing enhancer evidence "
            "not_assessable rather than supportive. A global memory enhancer scores zero "
            "on it however large its main effect.",
        next_kill_test="Find or design a study with within-session manipulation of item "
                       "value, retention tested separately for prioritised and incidental "
                       "items, at a consolidation-relevant delay. Absent that design, no "
                       "candidate can be scored either way.",
        evidence_dependencies="theory/selective_encoding_criteria.yaml; no claim records",
    ),

    dict(
        hypothesis="GOAL-GATED PLASTICITY & RETRIEVAL — cognitive capacity is limited by an "
                   "imperfect interface between conscious goals and the plasticity and "
                   "retrieval machinery, not only by the machinery's capacity",
        supporting_evidence="none in this repository; recorded as "
                            "THEORY:goal_gated_plasticity_retrieval. The phenomena it "
                            "appeals to (one-shot encoding under imposed salience, expert "
                            "chunking, cue-triggered reconstruction) are marked "
                            "appealed_to_not_verified — the repository holds no evidence "
                            "for any of them",
        contradictory_evidence="none — `control_gap` has never been measured here",
        human_genetics=NOT_ASSESSED, human_molecular=NOT_ASSESSED,
        human_intervention="not_measured — and notably, the decisive test requires NO "
                           "intervention",
        animal_causal="not applicable as posed — the claim is about volitional control",
        comparative=NOT_ASSESSED,
        adult_relevance="adult by construction",
        developmental_relevance="not applicable",
        replication="not applicable — no result to replicate",
        current_status="NOT_ASSESSED",
        why="Relocates the deficit from capacity to CONTROLLABILITY, which makes the "
            "opposite prediction about headroom: peak involuntary performance becomes a "
            "demonstration of capacity that volition cannot reach, rather than evidence of "
            "a ceiling. It separates three channels — C1 gating, C2 persistence, C3 "
            "retrieval — and the repository has NO retrieval-oriented target at all, which "
            "under this framing is a structural gap rather than an oversight. It is also a "
            "live successor to Sprint 1's finding that the POWER envelope may not be "
            "limiting in healthy adults: an interface limit would still bind when no "
            "capacity is exhausted.",
        next_kill_test="Estimate `control_gap` = performance under IMPOSED salience minus "
                       "performance under merely INTENDED salience, matched for effort, "
                       "arousal and time-on-task. Cheapest first: test whether existing "
                       "study strategies already close it, which would make the hypothesis "
                       "true and uninteresting.",
        evidence_dependencies="theory/goal_gated_plasticity_retrieval.yaml; no claim records",
    ),

    # -------------------------------------------------------- positive genetics ------
    dict(
        hypothesis="2q12.3 DUPLICATION is associated with higher cognitive performance",
        supporting_evidence="one CNV-GWAS association, N=258,292 (Huguet 2024, PMID 39667348), "
                            "verified independently via PubMed",
        contradictory_evidence="none identified — and no replication either",
        human_genetics="CNV association only; breakpoints, carrier count and effect size all "
                       "UNKNOWN to this repository; driver gene unresolved across 8 "
                       "protein-coding genes in a 2 Mb cytoband",
        human_molecular=NOT_ASSESSED,
        human_intervention="not applicable — a natural variant, not an intervention",
        animal_causal=NOT_ASSESSED, comparative=NOT_ASSESSED,
        adult_relevance="not stated in the retrieved source",
        developmental_relevance="not stated",
        replication="NONE — described by its authors as first-of-its-kind",
        current_status="UNRESOLVED",
        why="The rarest and most valuable KIND of evidence available (a variant associated "
            "with HIGHER performance), and currently a single unreplicated association with "
            "no effect size in hand. LOEUF was recorded for the eight genes and is the WRONG "
            "METRIC — it measures loss-of-function intolerance and the variant is a "
            "duplication; triplosensitivity is the right metric and is absent.",
        next_kill_test="Obtain the supplementary CNV coordinates, carrier count and effect "
                       "size; then ask whether the cohort overlaps this repository's "
                       "existing cognitive-GWAS base, which would make it non-independent.",
        evidence_dependencies="atlases/positive_genetics/2q12_3_duplication.yaml; SRC:PMID:39667348",
    ),

    # ------------------------------------------------- externally nominated genes ----
    dict(
        hypothesis="GRM3 is a cognition-relevant target",
        supporting_evidence="GWAS Catalog: 4 distinct studies, 5 associations, strongest "
                            "p=4e-13 — independently checked in this repository",
        contradictory_evidence="one contributing study (PMID 30038396) is an EDUCATIONAL "
                               "ATTAINMENT GWAS, not an intelligence GWAS",
        human_genetics="positional mapping only; causal_attribution basis "
                       "gwas_association_only, locus_to_gene_resolved: no",
        human_molecular=NOT_ASSESSED, human_intervention=NOT_ASSESSED,
        animal_causal=NOT_ASSESSED, comparative=NOT_ASSESSED,
        adult_relevance="unknown — an association says nothing about when a gene acts",
        developmental_relevance="unknown",
        replication="4 studies, but cohort overlap uncomputed; the sweep's publication set "
                    "is small and heavily shared",
        current_status="UNRESOLVED",
        why="Variant-level support is real and is the strongest of the three externally "
            "nominated genes. It is still positional: no causal gene, no direction, no "
            "adult mechanism. Entered the registry as an UNRANKED hypothesis.",
        next_kill_test="Fine-map the loci and test whether GRM3 rather than a neighbour "
                       "carries the signal; and re-run the association count excluding "
                       "educational-attainment studies.",
        evidence_dependencies="targets/discovered/discovered_registry.yaml; GWAS Catalog 2026-09-13",
    ),
    dict(
        hypothesis="ADGRB1 is a cognition-relevant target (nominated externally)",
        supporting_evidence="a gene-based claim attributed to an external analysis whose "
                            "artefacts have never been delivered",
        contradictory_evidence="this repository's own check found ONE association, one study, "
                               "p=2e-07 — BELOW the 5e-08 genome-wide threshold",
        human_genetics="one sub-threshold variant-level association; positional only",
        human_molecular=NOT_ASSESSED, human_intervention=NOT_ASSESSED,
        animal_causal=NOT_ASSESSED, comparative=NOT_ASSESSED,
        adult_relevance="unknown", developmental_relevance="unknown",
        replication="none",
        current_status="DOWNGRADED",
        why="A gene-based test can be significant where no single variant is, so the "
            "sub-threshold variant evidence does not refute the external claim. But this "
            "repository's own variant-level evidence is WEAK and must not be described as "
            "strong until the gene-based result is delivered and verified. The branch that "
            "was to deliver it does not exist.",
        next_kill_test="Obtain the gene-based statistic with its artefact and cohort; "
                       "until then the claim is unverifiable rather than wrong.",
        evidence_dependencies="targets/discovered/discovered_registry.yaml; "
                              "docs/integration/CODEX_BRANCH_AUDIT.md",
    ),

    # --------------------------------------------------------------- seed targets ----
    dict(
        hypothesis="PDE4B inhibition enhances adult human memory",
        supporting_evidence="two randomised human studies with cognitive endpoints "
                            "(roflumilast, healthy young adults and 60-80s); "
                            "human_intervention_evidence level 3 — the joint-highest here",
        contradictory_evidence="a clinical null in schizophrenia (working memory); "
                               "benefit occurred at the LOWEST of three doses",
        human_genetics="positional GWAS; causal_gene_attribution level 1; three of four "
                       "credible sets are educational attainment",
        human_molecular="bulk expression only; no QTL colocalisation",
        human_intervention="measured, positive in healthy adults; 141 registry studies, "
                           "113 tested a non-cognitive endpoint",
        animal_causal="weak — no PDE4B-SELECTIVE perturbation evidence (level 1)",
        comparative=NOT_ASSESSED,
        adult_relevance="DEMONSTRATED IN ADULTS — the strongest adult evidence in the cohort",
        developmental_relevance="low risk (developmental_confound_risk level 0 / counter 3)",
        replication="two studies, same compound class, same group lineage",
        current_status="PROMISING_BUT_UNRESOLVED",
        why="Ranks first in the cohort and still cannot be promoted. Roflumilast is a PAN-PDE4 "
            "inhibitor: as evidence about the ENDPOINT it is directly relevant, as evidence "
            "about THIS GENE it is not — which is why above_baseline_enhancement was "
            "downgraded 3->2. The dose-response inversion is unexplained and is the kind of "
            "finding that usually means the mechanism is not what it appears.",
        next_kill_test="A PDE4B-SELECTIVE agent with a cognitive endpoint in healthy adults. "
                       "Until one exists, the gene attribution is family-level, not gene-level.",
        evidence_dependencies="CLM:brakes:PDE4B:001-003; AUD:red_team:PDE4B:001; "
                              "evidence/registry_searches/PDE4B.yaml",
    ),
    dict(
        hypothesis="GABRA5 (alpha5-GABA-A) negative allosteric modulation enhances cognition",
        supporting_evidence="conditional CA1 deletion and NAM pharmacology in rodents; "
                            "16 independent sources, the second-largest evidence base here",
        contradictory_evidence="REPLICATED HUMAN NULL. Basmisanil phase 2b in CIAS: MCCB "
                               "composite treatment differences -0.36 (p=0.730) and +0.28 "
                               "(p=0.793). A second independently reported trial also failed. "
                               "Two rodent compounds acting as POSITIVE modulators improved "
                               "memory in aged rats — the opposite direction.",
        human_genetics="positional; causal_gene_attribution 2 / counter 2",
        human_molecular="bulk expression only",
        human_intervention="MEASURED AND NULL, replicated. level 1 / counter 4 — the counter "
                           "was raised by red-team audit",
        animal_causal="strong but contradicted (level 3 / counter 2); one rodent claim records "
                      "a COST — impaired context discrimination",
        comparative=NOT_ASSESSED,
        adult_relevance="adult human trials",
        developmental_relevance="animal perturbation is conditional-developmental",
        replication="THE NULL IS REPLICATED — two trials, not one trial reached twice",
        current_status="CONTRADICTED_IN_STUDIED_CONTEXT",
        why="The most informative result in the repository, and it is negative. This is not "
            "absence of evidence; it is a PRECISE null that bounds the effect below roughly "
            "0.2 SD in the studied population. The status says 'in studied context' "
            "deliberately: the trials were in cognitive impairment associated with "
            "schizophrenia and Down syndrome, so they do not strictly refute the mechanism "
            "in healthy adults — but nobody may cite the rodent data as though the human "
            "trials had not happened.",
        next_kill_test="Already run, twice. The only remaining question is whether healthy "
                       "adults differ from the studied populations, and that question does "
                       "not justify a new trial on this evidence.",
        evidence_dependencies="CLM:red_team:GABRA5:001; SRC:NCT:NCT02953639; SRC:NCT:NCT02484703; "
                              "evidence/registry_searches/results/GABRA5.yaml",
    ),
    dict(
        hypothesis="HCN1 blockade enhances adult human cognition (dendritic brake)",
        supporting_evidence="the repository's best-covered target — facet coverage 1.00, "
                            "21 claims, 15 independent sources; adult-inducible rodent "
                            "perturbation; comparative evidence assessed",
        contradictory_evidence="adult human layer-5 dendrites couple more weakly to the soma "
                               "and carry LOWER channel density than rat, measured directly; "
                               "the two direct human-versus-rodent h-current comparisons "
                               "DISAGREE IN SIGN by cortical layer; adult HCN1-null mice are "
                               "more seizure-susceptible",
        human_genetics="L2G ranks HCN1 at 2 credible sets with a COMPETING candidate gene "
                       "(MRPS30) at the same loci and no QTL corroboration; "
                       "causal_gene_attribution 2 / counter 2",
        human_molecular="no colocalisation (measured and absent)",
        human_intervention="none — 1 registry study, non-cognitive endpoint; the only tool "
                           "compound (ZD7288) is not a clinical agent",
        animal_causal="strong (level 3 / counter 2), including adult-inducible",
        comparative="ASSESSED — cross_species_convergence 2 / counter 3; "
                    "human_lineage_divergence_risk 3",
        adult_relevance="adult-inducible rodent perturbation exists",
        developmental_relevance="one key knockout is forebrain-restricted but NOT "
                                "time-restricted to adulthood",
        replication="within rodents yes; across species the sign is contested",
        current_status="DOWNGRADED",
        why="The best-covered target is also the clearest case of two failures. Its "
            "comparative counter-evidence is HIGHER than its supporting level, and the "
            "human-versus-rodent dendritic difference caps translation of its strongest "
            "animal evidence. Separately, three of its five apparent evidence modalities "
            "trace to two papers, so its breadth is partly double-counting.",
        next_kill_test="Resolve the layer-specific sign disagreement in human tissue before "
                       "any further investment; and resolve HCN1 vs MRPS30 at the credible sets.",
        evidence_dependencies="CLM:brakes:HCN1:001-006; CLM:comparative:HCN1:001-004; "
                              "AUD:red_team:HCN1:001; atlases/convergence/dependency_rules.yaml D007",
    ),
    dict(
        hypothesis="RGS14 suppression enhances adult cognition (CA2 plasticity brake)",
        supporting_evidence="germline knockout mice show enhanced CA2 LTP and enhanced "
                            "spatial and object-recognition memory",
        contradictory_evidence="RGS14 protein is UNDETECTABLE in mouse brain at birth and "
                               "rises through the first postnatal weeks — the knockout removes "
                               "it during the period it is being installed",
        human_genetics="measured and ABSENT — an explicit evidence_gap claim records that a "
                       "systematic sweep across 22 cognitive traits returned no association",
        human_molecular="bulk expression only",
        human_intervention="none — 1 registry study, non-cognitive endpoint; NO intervention "
                           "record exists for RGS14 anywhere in the repository",
        animal_causal="germline knockout ONLY; adult_onset_perturbation level 0",
        comparative="assessed — convergence 2, divergence risk 1 / counter 2",
        adult_relevance="read-out is adult; the PERTURBATION is lifelong",
        developmental_relevance="HIGH RISK — developmental_confound_risk level 3 / counter 0",
        replication="one 2010 paper supplies three claims across two atlases",
        current_status="DOWNGRADED",
        why="The headline finding is the life-stage mismatch: lifelong absence of a plasticity "
            "brake during the window when it is normally installed is a DEVELOPMENTAL "
            "manipulation, and an adult test of it says nothing about blocking the protein in "
            "an adult brain. Its only human-relevant evidence is a single review presenting "
            "no human cognitive phenotype.",
        next_kill_test="An adult-onset, time-restricted RGS14 suppression in animals. Without "
                       "it, nothing here transfers to an adult intervention.",
        evidence_dependencies="CLM:brakes:RGS14:001-004; AUD:red_team:RGS14:001; SRC:PMID:20837545",
    ),
    dict(
        hypothesis="CRTC1 activation enhances memory (allocation / CREB coactivation)",
        supporting_evidence="two adult-inducible AAV overexpression studies in mouse dentate "
                            "gyrus — the cleanest ADULT-ONSET animal perturbation in the cohort",
        contradictory_evidence="its human genetic support was a single 'self-reported maths "
                               "ability' association from an educational-attainment GWAS",
        human_genetics="DOWNGRADED 3->1 by a CRITICAL red-team finding; no non-education "
                       "corroboration; causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="NO MATCHING TRIAL FOUND — complete screen of ClinicalTrials.gov "
                           "(21 records examined, 21 total). NOT a biological null: nobody "
                           "has tested it, so there is nothing to have failed",
        animal_causal="adult-inducible overexpression (level 2); transfer_breadth 0; "
                      "dose_response_knowledge 0",
        comparative=NOT_ASSESSED,
        adult_relevance="adult-onset perturbation demonstrated in animals",
        developmental_relevance="low risk (level 0 / counter 2)",
        replication="two studies from a closely related line of work",
        current_status="DOWNGRADED",
        why="Carries the cohort's only unresolved CRITICAL red-team finding — educational "
            "attainment mistaken for intelligence — which gated its composite score. It is "
            "simultaneously the target the selective-encoding hypothesis most directly names "
            "(SE2, activity as the address) and one with essentially no human evidence. That "
            "combination is exactly what the hypothesis's guards exist to stop from becoming "
            "a promotion.",
        next_kill_test="Any human genetic association with a NON-EDUCATION cognitive measure; "
                       "and an animal study measuring whether enhancement is confined to "
                       "task-engaged representations (the SE6 test).",
        evidence_dependencies="CLM:alphacognition:CRTC1:001-003; AUD:red_team:CRTC1:001; "
                              "evidence/registry_searches/CRTC1.yaml",
    ),
    dict(
        hypothesis="GPR158 antagonism enhances adult cognition",
        supporting_evidence="germline knockout, ADULT-INDUCIBLE genetic perturbation, and an "
                            "osteocalcin-CA3 memory pathway in aged animals",
        contradictory_evidence="THE DIRECTION IS UNRESOLVED: one literature makes GPR158 an "
                               "excitability brake (suppress it), another makes it the receptor "
                               "for a memory-PROMOTING hormone (preserve it). One of its two "
                               "level-3 genetic records is an MTAG combining education and "
                               "intelligence.",
        human_genetics="positional plus one L2G credible set on intelligence; "
                       "causal_gene_attribution 2",
        human_molecular="bulk expression only",
        human_intervention="not_measured — 33 registry studies, 29 tested a non-cognitive "
                           "endpoint; human_intervention_evidence level 0",
        animal_causal="present including adult-inducible; above_baseline_enhancement level 0 / counter 1",
        comparative=NOT_ASSESSED,
        adult_relevance="adult-inducible perturbation exists",
        developmental_relevance="HIGH RISK — developmental_confound_risk level 3",
        replication="no",
        current_status="DOWNGRADED",
        why="Deprioritised by audit for overclaiming. A target whose DESIRABLE DIRECTION OF "
            "MANIPULATION is unknown cannot be a candidate, whatever its evidence volume — "
            "you cannot design an intervention when agonism and antagonism are both defensible.",
        next_kill_test="Resolve the direction: an adult-onset manipulation that measures "
                       "cognition while distinguishing the brake role from the osteocalcin-"
                       "receptor role.",
        evidence_dependencies="CLM:brakes:GPR158:001-003; AUD:red_team:GPR158:001",
    ),
    dict(
        hypothesis="EIF2B / integrated stress response modulation enhances adult memory",
        supporting_evidence="ISRIB-class adult PHARMACOLOGICAL perturbation in rodents; an "
                            "ADULT-ONSET human monogenic disease (vanishing white matter, 33 "
                            "genetically confirmed patients) — the complex's only "
                            "locus-to-gene-resolved human record",
        contradictory_evidence="two terminated fosigotifator trials (ALS, major depressive "
                               "disorder) that no atlas had recorded until the red team found them",
        human_genetics="monogenic disease only; NO GWAS-level support; causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="not_measured — 6 registry studies, all non-cognitive endpoints. "
                           "The ALS platform trial specified ALSFRS, NOT a cognitive endpoint, "
                           "so it is an evidence_gap and explicitly NOT a clinical null",
        animal_causal="adult pharmacological plus conditional knockout",
        comparative=NOT_ASSESSED,
        adult_relevance="adult-onset human disease; adult rodent pharmacology",
        developmental_relevance="one knockout is developmental, read out in adults",
        replication="no human cognitive test has been run",
        current_status="UNRESOLVED",
        why="Mechanistically the best-motivated candidate for converting transient encoding "
            "into a durable trace (SE3), and the one where the human cognitive question has "
            "simply never been asked. Its retyping from clinical_null to evidence_gap is the "
            "correct call and matters: a trial that never measured cognition cannot have "
            "failed at it. Tractability is the only 'not_assessed' in the cohort.",
        next_kill_test="Any ISR-modulating agent with a cognitive primary endpoint in adults. "
                       "The two terminated trials tell us about ALS and depression, not memory.",
        evidence_dependencies="CLM:brakes:EIF2B_COMPLEX:001-006; AUD:red_team:EIF2B_COMPLEX:001",
    ),
    dict(
        hypothesis="EIF2S1 (eIF2alpha) modulation enhances adult memory",
        supporting_evidence="conditional developmental knockout and in-vitro pharmacodynamics",
        contradictory_evidence="none directly — the problem is absence, not contradiction",
        human_genetics="MEASURED AND ABSENT — an explicit evidence_gap claim records a "
                       "systematic sweep of GWAS Catalog across 22 cognitive traits and of "
                       "Open Targets L2G returning no association",
        human_molecular="bulk expression only",
        human_intervention="not_measured — 10 registry studies, none with a cognitive endpoint",
        animal_causal="developmental conditional knockout only; adult_onset_perturbation level 0",
        comparative=NOT_ASSESSED,
        adult_relevance="plausible but untested",
        developmental_relevance="the only causal evidence is developmental",
        replication="no",
        current_status="UNRESOLVED",
        why="Audited as insufficient_evidence with zero contradicted facets — nothing is "
            "wrong with it, there is simply not enough. It also should not be counted as "
            "independent support for the ISR hypothesis: EIF2S1 and EIF2B_COMPLEX are the "
            "SUBSTRATE and the GEF of one pathway and share their mechanistic rationale.",
        next_kill_test="An adult-onset perturbation with a cognitive read-out. The "
                       "developmental knockout cannot answer the adult question.",
        evidence_dependencies="CLM:alphacognition:gap.EIF2S1:001; AUD:red_team:EIF2S1:001",
    ),
    dict(
        hypothesis="Klotho (KL) elevation enhances adult and aged cognition",
        supporting_evidence="human observational association with executive function; "
                            "mouse overexpression; administration in AGED NON-HUMAN PRIMATES; "
                            "adult_onset_perturbation level 3",
        contradictory_evidence="DOSE-RESPONSE INVERSION — benefit at a low dose and NONE at a "
                               "high dose in primates, on a study with a commercially "
                               "interested author. A 527-person cohort found the same KL-VS "
                               "variant reported as protective elsewhere associated in the "
                               "OPPOSITE direction. Its lead claim is flagged `contested`.",
        human_genetics="MEASURED AND ABSENT on the cognitive panel (explicit evidence_gap "
                       "claim); support is candidate-variant association only; "
                       "causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="A completed early-phase-1 study in 14 adults aged 50-80 DOES exist "
                           "(NCT07285629) with five NIH Toolbox cognitive secondary outcomes — "
                           "NO RESULTS POSTED. Graded 0, and the grading reasons are recorded "
                           "so a later agent can disagree with them",
        animal_causal="mouse and non-human primate; above_baseline_enhancement 2 / counter 3",
        comparative=NOT_ASSESSED,
        adult_relevance="adult and aged throughout — its strongest feature",
        developmental_relevance="not a developmental confound",
        replication="contradicted rather than replicated in human cohorts",
        current_status="DOWNGRADED",
        why="The adult-relevance profile is the best in the cohort and the evidence quality "
            "does not match it. A non-monotonic dose response with a conflicted author, plus "
            "an opposite-direction human cohort, is the signature of a finding that will not "
            "replicate. Its stated mechanism is synaptic and glutamatergic, which does not "
            "link it to any power-domain state variable the atlas placed it in.",
        next_kill_test="The posted results of NCT07285629; and an independent replication of "
                       "the KL-VS cognitive association in a cohort that did not generate it.",
        evidence_dependencies="CLM:power:KL:001-004; AUD:red_team:KL:001; SRC:NCT:NCT07285629",
    ),
    dict(
        hypothesis="CHRM1 (M1 muscarinic) agonism enhances adult human cognition",
        supporting_evidence="THE REPOSITORY'S ONLY HEALTHY-ADULT HUMAN COGNITIVE RESULT — "
                            "HTL0018318 improved working memory in 36 healthy young and 50 "
                            "healthy elderly adults; xanomeline efficacy in Alzheimer's; "
                            "adult_expression_and_timing level 3",
        contradictory_evidence="the phase 2 of that very compound was WITHDRAWN BEFORE "
                               "ENROLLING ANYONE, pending an unexpected animal toxicology "
                               "finding. 52% of patients in a high-dose arm discontinued for "
                               "adverse events. A clinical-harm meta-analysis. M1-null mice "
                               "show a BIDIRECTIONAL phenotype including normal or enhanced "
                               "memory on some tasks.",
        human_genetics="MEASURED AND ABSENT on the cognitive panel; causal_gene_attribution 0",
        human_molecular="bulk expression only; the largest human M1 dataset by sample size "
                        "measured NO cognitive endpoint at all — a gap, not a null",
        human_intervention="MEASURED AND POSITIVE in healthy adults, level 3, but the result "
                           "is a single exploratory, unreplicated, developer-affiliated "
                           "secondary analysis carrying three facets",
        animal_causal="germline knockout, bidirectional",
        comparative=NOT_ASSESSED,
        adult_relevance="healthy young and elderly adults — the cleanest adult relevance here",
        developmental_relevance="not a developmental confound",
        replication="NONE — one secondary analysis",
        current_status="DOWNGRADED",
        why="Carries the heaviest systemic liability burden in the cohort (safety level 4: "
            "the full peripheral cholinergic toxidrome plus liver-failure annotations, "
            "corroborated by 52% discontinuation) and is the only target gated on safety "
            "alone. The single most promising human cognitive result in the repository sits "
            "on top of a withdrawn trial and a toxicology signal.",
        next_kill_test="The outcome of the toxicology investigation, and any replication of "
                       "the healthy-adult working-memory effect by a non-affiliated group.",
        evidence_dependencies="CLM:alphacognition:CHRM1:001-005; AUD:red_team:CHRM1:001; "
                              "SRC:NCT:NCT03592862",
    ),
    dict(
        hypothesis="GRIN2B (NR2B) elevation enhances adult human cognition",
        supporting_evidence="forebrain NR2B overexpression enhances rodent memory across "
                            "three claims; 19 claims total",
        contradictory_evidence="HUMAN VARIANTS IN THE SAME GENE CAUSE NEURODEVELOPMENTAL "
                               "DISORDER — 86 individuals with de novo pathogenic variants, "
                               "plus a rare-variant burden result, both "
                               "locus-to-gene-resolved and both in the DELETERIOUS direction",
        human_genetics="the only target here with resolved rare-variant human genetics — and "
                       "it is developmental and deleterious; GWAS is positional, L2G sets are "
                       "educational attainment and mathematical ability; "
                       "causal_gene_attribution 1",
        human_molecular="bulk expression; the NR2B-to-NR2A developmental switch is itself "
                        "evidence that adult and juvenile biology differ",
        human_intervention="not_measured for enhancement — 257 registry studies, 141 with "
                           "non-cognitive endpoints, 17 completed-unreported reporting gaps, "
                           "27 with posted results awaiting extraction",
        animal_causal="strong (level 3 / counter 2) but adult_onset_perturbation only level 1",
        comparative=NOT_ASSESSED,
        adult_relevance="animal read-out is adult; the manipulation is constitutive",
        developmental_relevance="HIGHEST RISK — developmental_confound_risk level 3; the human "
                                "genetics is prenatal and postnatal-developmental",
        replication="rodent enhancement replicated; human direction is opposite",
        current_status="DOWNGRADED",
        why="The repository's CLEAREST life-stage mismatch. Constitutive developmental "
            "overexpression enhances rodent memory while human variants in the same gene "
            "cause neurodevelopmental disorder. Both can be true — dose and direction and "
            "timing differ — but the animal result cannot be cited as adult human evidence.",
        next_kill_test="Adult-onset, time-restricted NR2B elevation with a cognitive read-out "
                       "and a safety assessment; and extraction of the 27 trials with posted "
                       "results already in the queue.",
        evidence_dependencies="CLM:alphacognition:GRIN2B:001-006; AUD:red_team:GRIN2B:001",
    ),
    dict(
        hypothesis="HDAC2 inhibition enhances adult memory (transcriptional gating)",
        supporting_evidence="germline knockout and acute circuit perturbation in adult rats; "
                            "adult_onset_perturbation level 2",
        contradictory_evidence="trichostatin A enhanced an intermediate phase of LTP but had "
                               "NO EFFECT on persistence — the property SE3 actually requires. "
                               "A phase 2a null (FRM-0334) — on a MOLECULAR readout, not cognition",
        human_genetics="MEASURED AND ABSENT on the cognitive panel; L2G support is "
                       "educational-attainment-only; causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="not_measured — 159 registry studies, 117 non-cognitive endpoints. "
                           "The four terminations are ADMINISTRATIVE (recruitment, staffing, "
                           "mis-registration), not mechanism failures",
        animal_causal="level 2 / counter 1; above_baseline_enhancement only level 1",
        comparative=NOT_ASSESSED,
        adult_relevance="adult rodent and adult human records",
        developmental_relevance="moderate (level 2 / counter 2)",
        replication="no",
        current_status="UNRESOLVED",
        why="Liability is INHERITED FROM THE ONCOLOGY HDAC-INHIBITOR CLASS — thrombocytopenia, "
            "hepatotoxicity, fatigue, hypoacusis — while target-level annotation returns "
            "nothing, so the safety picture looks cleaner at the gene than it is in practice. "
            "The trichostatin result is the more interesting problem: potentiation that "
            "decays is not enhancement.",
        next_kill_test="An HDAC2-selective agent (not a pan-inhibitor) with a persistence "
                       "endpoint at a consolidation-relevant delay.",
        evidence_dependencies="CLM:brakes:HDAC2:001-005; AUD:red_team:HDAC2:001",
    ),
    dict(
        hypothesis="GRM5 (mGluR5) modulation enhances cognition",
        supporting_evidence="animal causal evidence and positional human genetics "
                            "(causal_gene_attribution 2)",
        contradictory_evidence="AFQ056 in 148 adults with fragile X: study treatment FAILED to "
                               "demonstrate efficacy. Carries a CRITICAL "
                               "model_organism_translation_failure finding",
        human_genetics="positional; causal_gene_attribution 2 / counter 2",
        human_molecular="bulk expression only",
        human_intervention="MEASURED AND NULL in the studied population; level 0 / counter 3",
        animal_causal="present and strongly contradicted by the human result",
        comparative=NOT_ASSESSED,
        adult_relevance="adult human trial",
        developmental_relevance="fragile X is a developmental condition",
        replication="the mGluR5 programme failed broadly across sponsors",
        current_status="CONTRADICTED_IN_STUDIED_CONTEXT",
        why="One of the most-cited model-to-human translation failures in neuroscience: a "
            "mechanism with excellent mouse data that did not transfer. Deprioritised by "
            "audit with its composite gated by an unresolved critical finding.",
        next_kill_test="None warranted on current evidence. The informative work is "
                       "post-mortem: WHY the mouse-to-human transfer failed, since that "
                       "lesson generalises to other targets here.",
        evidence_dependencies="CLM:red_team:GRM5:001; SRC:NCT:NCT01348087; AUD:red_team:GRM5:001",
    ),
    dict(
        hypothesis="OTX2 modulation reopens adult plasticity",
        supporting_evidence="developmental critical-period biology; human_genetic_association level 3",
        contradictory_evidence="a major developmental_effect_mistaken_for_adult finding; "
                               "gated by developmental_confound_caps_d2",
        human_genetics="level 3 association but causal_gene_attribution 1; no signal in the "
                       "current Open Targets release",
        human_molecular="bulk expression only",
        human_intervention="NO MATCHING TRIAL FOUND — complete screen (2 records examined, "
                           "2 total). Nobody has tested it",
        animal_causal="developmental",
        comparative=NOT_ASSESSED,
        adult_relevance="the core problem — the biology is a CRITICAL-PERIOD mechanism",
        developmental_relevance="the evidence IS developmental",
        replication="not applicable",
        current_status="DOWNGRADED",
        why="Deprioritised by audit. Critical-period biology describes how plasticity CLOSES "
            "during development; reopening it in an adult is a different intervention with "
            "different risks, and the developmental evidence does not license it.",
        next_kill_test="An adult-onset manipulation demonstrating reopened plasticity WITHOUT "
                       "loss of stability — SE7 in the selective-encoding framing.",
        evidence_dependencies="AUD:red_team:OTX2:001; evidence/registry_searches/OTX2.yaml",
    ),
    dict(
        hypothesis="RTN4R (Nogo receptor) blockade reopens adult plasticity",
        supporting_evidence="animal causal evidence only — the sole modality it has",
        contradictory_evidence="a major developmental_effect_mistaken_for_adult finding",
        human_genetics="none on the cognitive panel; causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="NO MATCHING TRIAL FOUND — complete screen (15 records examined, "
                           "15 total)",
        animal_causal="present — and it is the ONLY evidence modality for this target",
        comparative=NOT_ASSESSED,
        adult_relevance="unestablished",
        developmental_relevance="the evidence is developmental",
        replication="no",
        current_status="UNRESOLVED",
        why="One of three targets resting on a SINGLE evidence modality after the convergence "
            "correction. Animal-only evidence for a developmental mechanism is the weakest "
            "configuration in the repository.",
        next_kill_test="Any human evidence of any kind.",
        evidence_dependencies="AUD:red_team:RTN4R:001; evidence/registry_searches/RTN4R.yaml",
    ),
    dict(
        hypothesis="ADORA1 (adenosine A1) antagonism enhances cognition",
        supporting_evidence="animal causal work and a large human intervention literature "
                            "(caffeine and relatives); level 2",
        contradictory_evidence="a major RESCUE-MISTAKEN-FOR-ENHANCEMENT finding — reversing a "
                               "deficit is not raising a healthy baseline; counter level 3",
        human_genetics="none; causal_gene_attribution 0",
        human_molecular="bulk expression only",
        human_intervention="the largest registry footprint in the repository — 434 studies, "
                           "323 with non-cognitive endpoints, 37 COMPLETED-UNREPORTED "
                           "reporting gaps, 3 with posted results awaiting extraction",
        animal_causal="present", comparative=NOT_ASSESSED,
        adult_relevance="adult human exposure is ubiquitous",
        developmental_relevance="not the issue here",
        replication="extensive, and mostly on the wrong question",
        current_status="DOWNGRADED",
        why="The clearest case of restoration being read as enhancement: most human adenosine "
            "cognitive data compares caffeine against a withdrawn or sleep-deprived baseline, "
            "which measures rescue. It also has the repository's largest reporting-gap burden "
            "— 37 completed trials with cognitive outcomes in protocol and nothing posted. "
            "This is the ONLY target whose registry screen remains partial (1,000-record cap).",
        next_kill_test="A non-withdrawn, non-sleep-deprived healthy-adult baseline with a "
                       "cognitive endpoint; and retrieval of the 37 unreported results.",
        evidence_dependencies="CLM:brakes:ADORA1:001-007; AUD:red_team:ADORA1:001; "
                              "evidence/registry_searches/ADORA1.yaml",
    ),

    # ------------------------------------------------------- cross-cutting claims ----
    dict(
        hypothesis="CONVERGENCE — the repository's targets are supported by multiple "
                   "independent evidence modalities",
        supporting_evidence="before correction, all 27 targets appeared in two or more "
                            "modalities and several in five",
        contradictory_evidence="after removing double-counting, NO target exceeds THREE "
                               "independent modalities, and three targets rest on animal "
                               "evidence alone",
        human_genetics="largely one or two cohorts; UK Biobank recurs under many source ids",
        human_molecular="ONE GTEx v8 bulk-tissue run populates the column for essentially "
                        "every target",
        human_intervention="present for 20 of 27; power-atlas targets were searched by a "
                           "different route and carry no A-G code",
        animal_causal="the most widely present modality, and the least transferable",
        comparative="23 of 27 assessments are not_assessed",
        adult_relevance="not applicable",
        developmental_relevance="not applicable",
        replication="seven distinct double-counting mechanisms identified and verified",
        current_status="DOWNGRADED",
        why="The apparent breadth was an artefact of filing one observation in two places: "
            "atlas facet grades counted beside the claims they are computed FROM, one "
            "expression dataset counted per target, GWAS Catalog and Open Targets L2G "
            "counted as two observations of the same summary statistics, and null trials "
            "counted as a separate modality. The correction removes a modality precisely "
            "from the best-evidenced targets.",
        next_kill_test="Build the convergence scorer and the validator rule. The rules are "
                       "encoded but NOT enforced, so the double-counts can be reintroduced "
                       "with nothing firing.",
        evidence_dependencies="atlases/convergence/dependency_rules.yaml; reports/convergence_v0_2.md",
    ),
    dict(
        hypothesis="COMPARATIVE CONVERGENCE — mechanisms recruited independently in "
                   "cognitively specialised lineages are general requirements of cognition",
        supporting_evidence="none — no selection scan or convergence analysis has been run",
        contradictory_evidence="not applicable",
        human_genetics="not applicable", human_molecular="not applicable",
        human_intervention="not applicable",
        animal_causal="not applicable",
        comparative="PANEL DEFINED, ANALYSIS NOT RUN. 11 of 13 non-human panel species have "
                    "orthology available in Ensembl Compara",
        adult_relevance="not applicable", developmental_relevance="not applicable",
        replication="not applicable",
        current_status="NOT_ASSESSED",
        why="BOTH avian convergence candidates — New Caledonian crow and budgerigar — are "
            "absent from Ensembl Compara, while BOTH avian controls — chicken and zebra "
            "finch — are present. The available birds are the uninformative ones, so a scan "
            "would return a null for birds that is absence of MEASUREMENT of the specialised "
            "species. Octopus, the most independent lineage available anywhere, sits in a "
            "different resource entirely. Trait covariates are deliberately not ingested "
            "rather than recalled.",
        next_kill_test="An orthology resource covering corvids and parrots. Without one, the "
                       "avian arm is inoperable and no avian statement may be made in either "
                       "direction.",
        evidence_dependencies="atlases/comparative_v2/species_registry.yaml; "
                              "selection_signals.yaml (NOT_COMPUTED)",
    ),
    dict(
        hypothesis="EXTREME COGNITION provides evidence about enhancement mechanisms",
        supporting_evidence="none",
        contradictory_evidence="not applicable",
        human_genetics=NOT_ASSESSED, human_molecular=NOT_ASSESSED,
        human_intervention=NOT_ASSESSED, animal_causal=NOT_ASSESSED,
        comparative=NOT_ASSESSED,
        adult_relevance="not applicable", developmental_relevance="not applicable",
        replication="not applicable",
        current_status="NOT_ASSESSED",
        why="ZERO ARTEFACTS. No claim, source, assessment or target record exists. The only "
            "trace in the repository is an outstanding deliverable attributed to a branch "
            "that the branch audit establishes DOES NOT EXIST. This is a gap, not a null, "
            "and it is the largest single hole in the evidence base.",
        next_kill_test="Obtain the source list, or build the evidence map independently.",
        evidence_dependencies="docs/integration/CODEX_BRANCH_AUDIT.md; "
                              "analyses/external/X01_cell_type_enrichment.yaml",
    ),
    dict(
        hypothesis="X01 — cell-type enrichment implicates specific neuronal populations",
        supporting_evidence="an external analysis reporting a pyramidal-cell association "
                            "(beta ~0.097, nominal P ~0.011) in one dataset",
        contradictory_evidence="a second reported figure is P=0.08, which is not evidence of "
                               "absence any more than P=0.011 is proof of presence",
        human_genetics="cohort overlap with this repository's genetics base is "
                       "UNRESOLVABLE pending a source list",
        human_molecular="INERT — provenance_class external_analysis_unverified, excluded from "
                        "evidential_classes and enforced inert by validator rule V-EXT",
        human_intervention="not applicable", animal_causal="not applicable",
        comparative="not applicable",
        adult_relevance="unstated", developmental_relevance="unstated",
        replication="none; no artefacts delivered",
        current_status="UNRESOLVED",
        why="Recorded verbatim, cited by nothing, and mechanically prevented from supporting "
            "any claim, facet or assessment. Two nominal P-values near 0.011 are not proof, "
            "and P=0.08 is not a demonstration that pyramidal cells do not matter. Two of its "
            "METHODOLOGICAL instructions were adopted as safe before verification (no "
            "pyramidal-only gate; extreme cognition treated as continuous) because they only "
            "ever WIDEN what gets examined.",
        next_kill_test="Delivery of the artefacts named in the handoff contract, with the "
                       "source list that would make cohort overlap resolvable.",
        evidence_dependencies="analyses/external/X01_cell_type_enrichment.yaml; V-EXT",
    ),
    dict(
        hypothesis="Any current target is ready for chemistry, docking or a lead compound",
        supporting_evidence="none",
        contradictory_evidence="highest causal-gene attribution anywhere in the cohort is 2; "
                               "17 of 27 seed targets sit at level 0; tier_1_analyse_next is "
                               "EMPTY; zero molecular-QTL colocalisation repository-wide",
        human_genetics="no target has a defensible adult causal gene assignment",
        human_molecular="no colocalisation anywhere — measured and absent (70/70 L2G records)",
        human_intervention="the best human evidence is a replicated NULL (GABRA5)",
        animal_causal="strong and repeatedly shown not to transfer",
        comparative="not computed",
        adult_relevance="no target has demonstrated adult causal control",
        developmental_relevance="several leading targets are developmental mechanisms",
        replication="not applicable",
        current_status="CONTRADICTED_IN_STUDIED_CONTEXT",
        why="This row exists to be cited when the question is asked. Virtual pharmacology "
            "remains gated, and the gate is not procedural caution — it is that no target "
            "has a causal gene assignment strong enough to design against. Docking a molecule "
            "into a protein this repository cannot show is the right protein would produce "
            "confident output with no epistemic content.",
        next_kill_test="Raise ANY target to causal-gene level 3 with adult human evidence. "
                       "Nothing downstream is justified before that.",
        evidence_dependencies="reports/sprint1_summary.md; reports/target_ranking_v0_1.csv",
    ),
]


# ============================================================================ SPRINT 3 ==
# Sprint-3 updates are applied as a LAYER over the Sprint-2 rows rather than by rewriting
# them, so the earlier judgement stays readable next to the evidence that changed it. Each
# update names its artefacts. Status changes are listed in reports/GENE_TOURNAMENT_FINAL.md.
SPRINT3_UPDATED = "2026-09-22"
_T = "reports/gene_tournament/"
_MAGMA = ("MAGMA gene-level, Davies 2018 general cognitive function (N=282,014), run VERIFIED by "
          "independent recomputation in this repository")
SPRINT3_UPDATES: dict[str, dict[str, str]] = {
    "A SINGLE GENIUS GENE": {
        "why_prefix": "SPRINT 3 reinforces this: the extreme-IQ sample (IQ~170) has ZERO genome-wide "
                      "significant genes at gene level; 375 genes pass Bonferroni in population "
                      "cognition, collapsing to 159 independent LD loci; the largest biological module "
                      "holds 32% of FDR<0.01 gene-level evidence, and no gene dominates.",
        "deps": _T + "direct_cognition_rank.csv; " + _T + "extreme_tail_summary.json"},
    "EXTREME COGNITION IS QUALITATIVELY DISTINCT": {
        "current_status": "CONTRADICTED_IN_STUDIED_CONTEXT",
        "why_prefix": "SPRINT 3 ASSESSED IT. At gene level, for common variants in European-ancestry "
                      "summary data, extreme cognition is CONTINUOUS with population cognition: among the "
                      "375 population-significant genes the extreme-IQ shift is 1.13x what pure power "
                      "scaling predicts (observed mean Z 0.985 vs 0.910); 121/159 independent loci carry "
                      "positive extreme-tail signal (P=9.2e-05); Mann-Whitney P=9e-26; size-matched "
                      "permutation P<0.0005. No distinct tail gene set is seen. Context limits: common "
                      "variants only; possible HRS/CHARGE sample overlap is unresolved and would bias "
                      "toward this answer; rare-variant tail untested (no individual-level access).",
        "human_genetics": "Zabaneh 2018 extreme IQ (1,238 cases, N_eff 4,300) vs Davies 2018 population cognition, gene level",
        "replication": "single extreme-tail GWAS; no second extreme-IQ sample with open data exists",
        "next_kill_test": "Resolve HRS/CHARGE overlap; then repeat with any second extreme-tail sample, and "
                          "test rare-variant burden if individual-level TIP genotypes ever become accessible.",
        "deps": _T + "extreme_tail_summary.json; " + _T + "extreme_tail_rank.csv"},
    "PYRAMIDAL-CELL SPECIFICITY": {
        "why_prefix": "SPRINT 3: X01's artefacts were found (the Codex branch exists) and its GENE-LEVEL layer "
                      "was independently reproduced. Its cell-type layer shows pyramidal enrichment nominal "
                      "in all four atlas x model combinations (P 2e-05 to 0.019) -- but cortical interneurons "
                      "are equally strong marginally (P=2.3e-05). The signal is NEURONAL rather than "
                      "pyramidal-specific, and X01's own verdict is 'inconclusive' (corrected P=0.08).",
        "deps": _T + "pathway_hypothesis_panel.csv; analyses/external/X01_cell_type_enrichment.yaml"},
    "SYNAPTIC BIOLOGY is the dominant locus": {
        "current_status": "PROMISING_BUT_UNRESOLVED",
        "why_prefix": "SPRINT 3 RAN THE UNBIASED TEST this row asked for. MAGMA competitive gene-set "
                      "analysis over 6,200 sets, conditioned on gene size, gene density, LD, annotation "
                      "density and LoF constraint, GLOBAL FDR: the ONLY 6 sets surviving are synaptic "
                      "(presynaptic membrane, synaptic membrane adhesion, presynaptic voltage-gated channels, "
                      "synapse, process in the synapse); postsynaptic density does not survive. Reproduced "
                      "in Savage 2018 (6/6, same sign; overlapping sample). NOT independently replicated: "
                      "UKB-free extreme-IQ sample 6/6 same sign, 0/6 significant at 65x less power. "
                      "'Dominant' is overstated: the synaptic module holds 32% of FDR<0.01 evidence -- the "
                      "largest share, not a majority -- and its boundaries are unstable.",
        "human_genetics": "unbiased gene-set enrichment, conditioned, global FDR: synaptic sets only (6/6,200)",
        "replication": "reproduced in an overlapping meta-analysis; independent (UKB-free) test underpowered",
        "next_kill_test": "Test the six synaptic sets in a large cognition GWAS WITHOUT UK Biobank "
                          "(or in within-sibship data, which needs an OpenGWAS registration).",
        "deps": _T + "pathway_enrichment.csv; " + _T + "pathway_replication.csv; " + _T + "module_report.md"},
    "DEVELOPMENTAL WIRING": {
        "why_prefix": "SPRINT 3 GENETICS DOES NOT DECIDE IT: the 375 Bonferroni cognition genes are neither "
                      "enriched for prenatal/developmental expression (OR 1.16, P=0.12) nor for adult-dynamic "
                      "expression (OR 1.30, P=0.06). The top two loci split: DCC prenatal-dominant, NEGR1 "
                      "adult-dynamic.",
        "deps": _T + "TOP50_HUMAN_COGNITION_GENES.csv; data/gene_tournament/developmental_classification.parquet"},
    "ASTROCYTE DOMINANCE": {
        "current_status": "DOWNGRADED",
        "why_prefix": "SPRINT 3 GENETIC TEST: GO astrocyte sets are null after conditioning (astrocyte "
                      "projection P=0.85, activation P=0.98); X01 astrocyte cell-type enrichment is "
                      "inconsistent (null marginally in one atlas P=0.59, null jointly in the other P=0.21, "
                      "significant only in one joint model P=0.0013 -- a conditioning artefact signature). "
                      "This tests astrocytic GENETIC involvement, not lactate-shuttle physiology.",
        "deps": _T + "pathway_hypothesis_panel.csv"},
    "ENERGY DOMINANCE": {
        "why_prefix": "SPRINT 3 GENETICS AGREES WITH THE DOWNGRADE: oxidative phosphorylation P=0.37 "
                      "(conditioned); 0 of 11 mitochondrial-family sets even nominal; a mitochondrial "
                      "module exists (11% of evidence) but its label is not enriched (global FDR 0.9999) -- "
                      "mitochondrial genes appear at their base rate.",
        "deps": _T + "pathway_hypothesis_panel.csv; " + _T + "module_report.md"},
    "MYELIN AND NETWORK TIMING": {
        "current_status": "UNRESOLVED",
        "why_prefix": "SPRINT 3 ASSESSED IT (previously zero artefacts). GO myelination P=0.16 and "
                      "oligodendrocyte differentiation P=0.43 after conditioning -- null. But X01's "
                      "oligodendrocyte-lineage EXPRESSION enrichment is nominal in joint models in both "
                      "atlases (P=0.012, 0.019; OPC P=4e-04 marginal in the cortex atlas). Mixed, not "
                      "surviving correction. Conduction timing itself is not assessable by gene sets.",
        "deps": _T + "pathway_hypothesis_panel.csv"},
    "CLASSICAL NEUROMODULATOR DOMINANCE": {
        "why_prefix": "SPRINT 3 GENETICS: neurotransmitter receptor activity P=0.12 and GPCR activity "
                      "P=0.81 after conditioning; serotonin-receptor sets nominal only (5 of 28 at P<0.05 "
                      "vs 1.4 expected); nothing survives correction.",
        "deps": _T + "pathway_hypothesis_panel.csv"},
    "MATHEMATICAL BIOLOGY BEYOND g": {
        "current_status": "UNRESOLVED",
        "why_prefix": "SPRINT 3 ASSESSED IT; NOT IDENTIFIABLE WITH OPEN DATA. 0 math-specific genes. The "
                      "only open objective arithmetic phenotype (UKB item FI4, N~115k) has 0 genome-wide "
                      "significant genes and correlates with g at rho=0.11; its top residual genes are "
                      "keratins (an LD artefact). The catalog 'maths' channel is 99.8% one 23andMe paper of "
                      "self-report/course-taking; the only g-orthogonal maths GWAS (2025) rests on restricted "
                      "23andMe data.",
        "next_kill_test": "Apply for the 23andMe maths summary statistics, or find a cohort with an "
                          "objective multi-item maths test and genotypes.",
        "deps": _T + "math_gene_rank.csv"},
    "2q12.3 DUPLICATION": {
        "why_prefix": "SPRINT 3 RESOLVED THE UNKNOWNS FROM THE FULL TEXT -- and found the Sprint-2 gene "
                      "list was WRONG (hg38 cytoband used for an hg19 label). The duplication is "
                      "chr2:109,510,927-110,376,563 (hg19), 865 kb, EDAR/SH3RF3/SEPTIN10/SOWAHC; 36 "
                      "carriers of 258,292; z=0.434 (~6.5 IQ points), p=7.6e-03 (nominal; not Bonferroni "
                      "across 596 duplicated genes); reciprocal deletion trends negative (p=0.058); "
                      "per-copy dosage p=2.65e-03. All four genes ClinGen-uncurated. Weak convergence: "
                      "SOWAHC/SEPTIN10 nominal common-variant signal (P 0.0014, 0.0022). No replication.",
        "deps": "atlases/positive_genetics/2q12_3_duplication.yaml; " + _T + "positive_human_perturbations.csv"},
    "GRM3 is a cognition-relevant target": {
        "why_prefix": "SPRINT 3: " + _MAGMA + " gives GRM3 P=2.2e-05, rank 543/18,418 -- NOT Bonferroni. "
                      "Attribution corrected: the nomination came from a Codex screen of Savage 2018 "
                      "supplementary tables (published P=4.8e-08), not from X01.",
        "deps": _T + "direct_cognition_rank.csv"},
    "ADGRB1 is a cognition-relevant target": {
        "current_status": "UNRESOLVED",
        "why_prefix": "SPRINT 3 REVERSES THE SPRINT-2 DOWNGRADE. " + _MAGMA + " gives ADGRB1 P=1.6e-07, "
                      "rank 238/18,418 -- PASSES Bonferroni. Sprint 2 tested single variants; a gene-based "
                      "test is the appropriate one. Still no causal-gene resolution and no direction.",
        "deps": _T + "direct_cognition_rank.csv"},
    "EXTREME COGNITION provides evidence about enhancement mechanisms": {
        "current_status": "UNRESOLVED",
        "why_prefix": "SPRINT 3 ASSESSED IT. At gene level the extreme tail is the SAME architecture as "
                      "population cognition (see the continuity row), so it adds power-limited information "
                      "about the same genes rather than distinct mechanisms; its one reported locus (ADAM12) "
                      "is nominal here and unreplicated. The rare-variant tail is untested.",
        "deps": _T + "extreme_tail_summary.json"},
    "X01 — cell-type enrichment": {
        "why_prefix": "SPRINT 3: the artefacts exist (local, unpushed Codex worktree). X01's GENE-LEVEL "
                      "layer was reproduced here by independent recomputation; its cell-property layer is "
                      "not yet re-derived, so the record is artefacts_received_pending_check. X01 did NOT "
                      "nominate GRM3/ADGRB1/GABBR1.",
        "deps": "analyses/external/X01_cell_type_enrichment.yaml; data/raw/magma_x01/2026-09-22/REPLICATION_CHECK.json"},
}
_SEED_MAGMA = {  # gene-level results from the verified run, appended to human_genetics
    "PDE4B": "P=0.105, rank 7,081", "GABRA5": "P=0.38, rank 12,413", "HCN1": "P=0.36, rank 12,124",
    "RGS14": "P=0.040, rank 4,723", "CRTC1": "P=0.74, rank 16,505", "GPR158": "P=0.0014, rank 1,561",
    "EIF2S1": "P=0.72, rank 16,362", "Klotho": "KL P=0.18, rank 8,894", "CHRM1": "P=0.056, rank 5,397",
    "GRIN2B": "P=0.068, rank 5,851", "HDAC2": "P=0.23, rank 9,908", "GRM5": "P=0.51, rank 14,085",
    "OTX2": "P=0.13, rank 7,670", "RTN4R": "P=0.041, rank 4,762", "ADORA1": "P=0.0067, rank 2,447",
}


def apply_sprint3(rows: list[dict[str, str]]) -> None:
    for row in rows:
        h = row["hypothesis"]
        for prefix, upd in SPRINT3_UPDATES.items():
            if h.startswith(prefix):
                old = row["current_status"]
                if "current_status" in upd and upd["current_status"] != old:
                    row["why"] = (f"{upd['why_prefix']} [STATUS CHANGED IN SPRINT 3: {old} -> "
                                  f"{upd['current_status']}.] PREVIOUSLY: {row['why']}")
                    row["current_status"] = upd["current_status"]
                else:
                    row["why"] = f"{upd['why_prefix']} PREVIOUSLY: {row['why']}"
                for col in ("human_genetics", "replication", "next_kill_test"):
                    if col in upd:
                        row[col] = upd[col]
                row["evidence_dependencies"] = f"{row['evidence_dependencies']}; {upd['deps']}"
                row["last_updated"] = SPRINT3_UPDATED
        for key, res in _SEED_MAGMA.items():
            if h.startswith(key):
                row["human_genetics"] = (f"{row['human_genetics']} | SPRINT 3 {_MAGMA}: {res} of 18,418 "
                                         "(Bonferroni needs P<2.7e-06)")
                row["last_updated"] = SPRINT3_UPDATED


apply_sprint3(ROWS)


# ---------------------------------------------------------------------------------------------
# Sprint 3.1 layer (2026-09-23): synaptic recon / correction pass. Applied AFTER Sprint 3 so both
# judgements stay readable. Evidence: reports/sprint3_1/.
# ---------------------------------------------------------------------------------------------
SPRINT31_UPDATED = "2026-09-23"
_R31 = "reports/sprint3_1/"
SPRINT31_UPDATES: dict[str, dict[str, str]] = {
    "SYNAPTIC BIOLOGY is the dominant locus": {
        "why_prefix": "SPRINT 3.1 CORRECTS THE SHAPE OF THE SIGNAL. Direct pre-vs-post tests (MAGMA joint and "
                      "contrast models) find NO presynaptic skew: postsynapse >= presynapse in every "
                      "specification, pre-only minus post-only contrast null. What survives every covariate "
                      "specification (incl. generic neuronal expression) and leave-one-locus-out is the "
                      "synaptic-MEMBRANE / trans-synaptic ADHESION core (CDH9, PTPRF, CADM2, NCAM1, PTPRD, "
                      "LRRC4; channels KCNJ3, SCN2A). Release machinery (active zone, vesicle cycle, priming, "
                      "Ca-triggered release, SNARE) is NOT enriched. Generic neuronal expression absorbs ~55% of "
                      "the broad synapse effect. Sprint 3's GO sets were unpropagated; with propagated GO, CNS "
                      "neuron differentiation and neuron migration ALSO survive global FDR in every "
                      "specification, so 'synaptic biology is the only survivor' is withdrawn.",
        "human_genetics": "broad synaptic enrichment concentrated in synaptic-membrane/adhesion genes; no "
                          "presynaptic skew; neurodevelopmental sets also robust (single UKB-containing lineage)",
        "deps": _R31 + "pre_vs_post_joint_tests.csv; " + _R31 + "pathway_conditioning_sensitivity.csv; "
                + _R31 + "leave_one_locus_out.csv"},
    "EXTREME COGNITION IS QUALITATIVELY DISTINCT": {
        "why_prefix": "SPRINT 3.1 REPLACES THE EVIDENCE, NOT THE VERDICT. The '1.13x power-scaling' ratio is "
                      "withdrawn as proof: under plausible ascertainment and winner's-curse assumptions it spans "
                      "0.61-1.25. The '121/159 loci same sign' was an UNSIGNED gene-level statistic. A genuine "
                      "allele-direction test: 112/136 testable Sprint-3 lead SNPs have the cognition-increasing "
                      "allele also raising extreme-IQ odds (binomial P=4e-15), inside the 72-84% continuity "
                      "predicts. Wording now: no strong evidence for a distinct common-variant architecture; "
                      "magnitudes not identified; HRS overlap still unresolved and biases toward this answer.",
        "deps": _R31 + "extreme_tail_reassessment.md; " + _R31 + "extreme_tail_locus_direction.csv"},
    "DEVELOPMENTAL WIRING": {
        "why_prefix": "SPRINT 3.1: with GO propagated on the ontology (Sprint 3 used direct annotations: "
                      "'neurogenesis' had 79 genes vs 1,010 propagated), CNS neuron differentiation and neuron "
                      "migration survive global FDR in all six covariate specifications. Pathway-level genetic "
                      "support for neurodevelopmental processes -- which does not say WHEN they act.",
        "deps": _R31 + "pathway_conditioning_sensitivity.csv"},
    "ADULT SYNAPTIC CONTROL": {
        "why_prefix": "SPRINT 3.1: the surviving synaptic signal is structural (membrane/adhesion), not release "
                      "machinery, and 'adult-modifiable' is relabelled ADULT-EXPRESSION-COMPATIBLE (expression "
                      "is not modifiability). No gene has ADULT_CAUSAL_EVIDENCE. On independent adult-brain QTL "
                      "units, only RPS26 (12q13.2) meets the unchanged direction threshold -- a ubiquitous "
                      "ribosomal eQTL at a pleiotropic locus, a Sprint-4 Gate-C test case, not a control parameter.",
        "deps": _R31 + "adult_evidence_hierarchy.csv; " + _R31 + "direction_rule_recount_all_genes.csv"},
    "CONVERGENCE": {
        "why_prefix": "SPRINT 3.1 DEPENDENCE AUDIT: in the Top-50 lists direct association, replication, "
                      "fine-mapping, the GWAS half of colocalisation and direction all descend from one "
                      "UKB-containing GWAS lineage; leaving it out keeps 5/50 (natural) and 14/50 (adult); only "
                      "MACROD2 has a verified UKB-free cohort unit. A pipeline defect ('UKB ' with a trailing "
                      "space) had counted Perry 2025 as UKB-free for 11 natural Top-50 genes.",
        "deps": _R31 + "rank_dependency_audit.csv; " + _R31 + "rank_dependency_audit_summary.json"},
    "ENERGY DOMINANCE": {
        "why_prefix": "SPRINT 3.1: re-tested with propagated GO under six covariate specifications -- "
                      "mitochondrion and oxidative phosphorylation null in all (absence of common-variant "
                      "enrichment, not proof of irrelevance).",
        "deps": _R31 + "pathway_conditioning_sensitivity.csv"},
    "MYELIN AND NETWORK TIMING": {
        "why_prefix": "SPRINT 3.1: propagated myelination (84 genes) null in all six specifications.",
        "deps": _R31 + "pathway_conditioning_sensitivity.csv"},
}


def apply_sprint31(rows: list[dict[str, str]]) -> None:
    for row in rows:
        for prefix, upd in SPRINT31_UPDATES.items():
            if row["hypothesis"].startswith(prefix):
                old = row["current_status"]
                if "current_status" in upd and upd["current_status"] != old:
                    row["why"] = (f"{upd['why_prefix']} [STATUS CHANGED IN SPRINT 3.1: {old} -> "
                                  f"{upd['current_status']}.] PREVIOUSLY: {row['why']}")
                    row["current_status"] = upd["current_status"]
                else:
                    row["why"] = f"{upd['why_prefix']} PREVIOUSLY: {row['why']}"
                for col in ("human_genetics", "replication", "next_kill_test"):
                    if col in upd:
                        row[col] = upd[col]
                row["evidence_dependencies"] = f"{row['evidence_dependencies']}; {upd['deps']}"
                row["last_updated"] = SPRINT31_UPDATED


apply_sprint31(ROWS)


def build() -> int:
    for row in ROWS:
        row.setdefault("last_updated", UPDATED)
        missing = [c for c in COLUMNS if c not in row]
        if missing:
            print(f"ERROR: row '{row['hypothesis'][:40]}' missing {missing}", file=sys.stderr)
            return 1

    CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in ROWS:
            writer.writerow({c: row[c] for c in COLUMNS})

    by_status: dict[str, list[dict[str, str]]] = {}
    for row in ROWS:
        by_status.setdefault(row["current_status"], []).append(row)

    order = ["SUPPORTED", "PROMISING_BUT_UNRESOLVED", "DOWNGRADED", "UNRESOLVED",
             "CONTRADICTED_IN_STUDIED_CONTEXT", "NOT_ASSESSED"]

    lines: list[str] = []
    lines.append("# Project truth table\n")
    lines.append(f"**Generated {UPDATED}, Sprint-3 layer applied {SPRINT3_UPDATED}, by `pipelines/reports/build_truth_table.py` — "
                 "do not hand-edit.** Machine-readable twin: "
                 "[`project_truth_table.csv`](project_truth_table.csv).\n")
    lines.append("> One row per tracked hypothesis, stating what is established, what "
                 "contradicts it, and what would kill it. The statuses are judgements made "
                 "by reading the repository's records; every row names the artefacts it "
                 "rests on.\n")
    lines.append("## The headline\n")
    supported = len(by_status.get("SUPPORTED", []))
    lines.append(
        f"**`SUPPORTED`: {supported} of {len(ROWS)} — and it is the one that licenses "
        "nothing.** The single supported hypothesis is *cognition is substantially "
        "genetic*, which is a claim about variance in a population, not about "
        "modifiability in a person. **No hypothesis about an intervention target has "
        "replicated adult human causal evidence.** The strongest *human* result in the "
        "repository is a replicated **null** (GABRA5). That is not a failure of the "
        "search — it is the finding.\n")
    lines.append("| status | n | meaning |\n|---|---|---|")
    meaning = {
        "SUPPORTED": "adult human causal evidence, replicated",
        "PROMISING_BUT_UNRESOLVED": "real evidence, decisive question still open",
        "DOWNGRADED": "was rated higher; a specific finding lowered it",
        "UNRESOLVED": "insufficient evidence either way",
        "CONTRADICTED_IN_STUDIED_CONTEXT": "tested in humans and failed **in that context**",
        "NOT_ASSESSED": "no evidence in this repository at all",
    }
    for status in order:
        lines.append(f"| `{status}` | {len(by_status.get(status, []))} | {meaning[status]} |")
    lines.append("")
    lines.append("**The two states that are easiest to confuse** are the last two. "
                 "`CONTRADICTED_IN_STUDIED_CONTEXT` means someone looked and the answer was "
                 "no, in a specific population. `NOT_ASSESSED` means nobody looked. Neither "
                 "is a statement that the biology is wrong, and collapsing them is this "
                 "project's most persistent bug.\n")
    lines.append("---\n")

    for status in order:
        rows = by_status.get(status, [])
        if not rows:
            lines.append(f"## {status} — none\n")
            continue
        lines.append(f"## {status} ({len(rows)})\n")
        for row in rows:
            lines.append(f"### {row['hypothesis']}\n")
            lines.append(f"**Why:** {row['why']}\n")
            lines.append(f"**Supporting:** {row['supporting_evidence']}\n")
            lines.append(f"**Contradictory:** {row['contradictory_evidence']}\n")
            lines.append("| modality | state |\n|---|---|")
            for col, label in [
                ("human_genetics", "human genetics"), ("human_molecular", "human molecular"),
                ("human_intervention", "human intervention"), ("animal_causal", "animal causal"),
                ("comparative", "comparative"), ("adult_relevance", "adult relevance"),
                ("developmental_relevance", "developmental relevance"),
                ("replication", "replication"),
            ]:
                lines.append(f"| {label} | {row[col]} |")
            lines.append("")
            lines.append(f"**Next kill test:** {row['next_kill_test']}\n")
            lines.append(f"**Depends on:** `{row['evidence_dependencies']}`\n")
    lines.append("---\n")
    lines.append("*Statuses are judgements, not computed values. They are recorded as such "
                 "so they can be disagreed with — each row names the artefacts a "
                 "disagreement would have to engage.*\n")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(ROWS)} rows -> {MD.relative_to(REPO_ROOT)} and {CSV.relative_to(REPO_ROOT)}")
    for status in order:
        print(f"  {status:34s} {len(by_status.get(status, []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
