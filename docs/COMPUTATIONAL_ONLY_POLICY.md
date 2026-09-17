# Computational-Only Policy

**This project performs computational work exclusively.**

## What this repository does

Computational analysis, data integration, causal inference over existing data,
knowledge-graph construction, structural bioinformatics, cheminformatics, virtual
screening, molecular simulation, machine learning, statistical genetics, comparative
genomics, and literature/evidence synthesis.

## What this repository never does

* No wet-lab work of any kind.
* No in-vitro experiments.
* No ex-vivo experiments.
* No animal experiments performed by or for this project.
* No human experimentation, no clinical intervention, no recruitment.
* No self-experimentation planning, dosing guidance, protocols, sourcing or
  administration advice for any compound — for anyone, including the maintainer.

Existing wet-lab, animal and clinical results are **ingested as evidence**, with
provenance. Ingesting a result is a computational act; it never implies that this
project endorses repeating it, extending it, or acting on it.

## How the policy is enforced

| Layer | Mechanism |
|-------|-----------|
| Task planning | `action_type` in `docs/TASK_DAG.yaml` is a closed enum of computational actions. Adding a laboratory action type is a policy violation. |
| Evidence records | `evidence.design` describes **who else** ran a study, never work performed here. Records carry `extraction.basis` (what was read), not protocols. |
| Red-team audit | The mandatory check `proposes_prohibited_work` fails any record, document or model that proposes prohibited work. |
| Chemistry gate | `blueprint.pharmacology.gates.eligible_for_chemistry()` restricts virtual pharmacology to targets that survived causal integration and red-team review — and virtual pharmacology stays *virtual*. |
| Outputs | Reports rank **candidate control points for further computational analysis**. No report contains a dose, a route, a regimen or a protocol. |

## Framing of results

Nothing in this repository is medical advice, a therapeutic recommendation, or an
enhancement protocol. A high rank means "this control point deserves more
computational scrutiny", never "this is safe or effective to modulate". The absence of
evidence of harm is never recorded as evidence of safety.
