# Virtual pharmacology interfaces — gate G5

**Status: interface only. Nothing in `src/blueprint/pharmacology/` is implemented, and
nothing in it may run in Sprint 1.** Every function raises `NotImplementedError` naming
the gate and the sprint.

---

## 1. The two rules that bind everything here

### Everything stays in silico

No wet-lab work. No in-vitro experiment. No ex-vivo experiment. No animal experiment.
No human experimentation, clinical intervention or recruitment. No
self-experimentation, for anyone, including the maintainer. Nothing in this layer
performs, plans, designs, requests or recommends any of it
([`docs/COMPUTATIONAL_ONLY_POLICY.md`](COMPUTATIONAL_ONLY_POLICY.md)).

What this layer will eventually do is computational: structure retrieval, pocket
detection, ligand retrieval, bioactivity landscape description, QSAR, docking,
molecular dynamics, pharmacophore modelling, generative proposals, BBB and ADMET
prediction, selectivity profiling, multi-objective optimisation. All of it operates on
files and models. None of it touches a bench.

### No output is ever a dose, a route, a regimen or a sourcing path

Not as a result, not as an example, not in a docstring, not in a test fixture, not as
an inference a reader could draw. This is a constraint on the **output shape**, not
just on intent, and it is enforced structurally:

| Return type | Carries | Deliberately cannot carry |
|---|---|---|
| `ADMETPrediction` | predicted molecular properties, flags, model ids | any human exposure, dose, route or schedule |
| `BBBPrediction` | a predicted class with uncertainty and applicability | a statement about what happens in a person |
| `DockingResult` | poses, scores, software, scoring function | a binding affinity, or an effect |
| `GenerativeProposal` | SMILES, objective scores, novelty, a synthetic-accessibility **score** | reagents, conditions, a procedure, a route |
| `SelectivityProfile` | named family members and margins | a claim that a ligand is "safe" or "selective enough" |
| `MultiObjectiveResult` | a Pareto front, objectives, `constraints_enforced` | a safety term traded against a benefit |

`tests/test_ranking_pharmacology_gate.py` asserts that no public signature in the
module mentions dose, regimen, route of administration, posology or sourcing. The
shape of an API is what invites the next person to fill it in, so the shape is part of
the policy.

Two further boundaries, both already contract rules rather than preferences:

* **Binding is not efficacy.** A docking score, a bioactivity record and a
  tractability bucket all say a modality exists. None of them says that engaging the
  target does anything (contract rule V16).
* **Safety is a constraint, not a cost.** `multi_objective_optimise` takes `objectives`
  and `hard_constraints` as separate parameters, and any implementation must refuse a
  configuration that puts a safety term among the objectives with a weight. An
  optimiser that can trade safety away is the wrong optimiser whatever weight is
  chosen (README §3).

---

## 2. Gate G5

`docs/BLACKBOARD_PROTOCOL.md` §3: *virtual pharmacology may only act on targets that
survived causal integration **and** red-team review.* The executable form is
`blueprint.pharmacology.gates.eligible_for_chemistry(target, ranking_row, audits)`,
returning `(eligible, reason)`.

### The conditions

All six must hold. Each failure returns a sentence naming the specific condition,
because a refusal nobody understands gets worked around.

| # | Condition | Why |
|---|---|---|
| 1 | **Ranked** — a row exists in `reports/target_ranking_v0_1.csv` | A target the integration model never scored has not been through causal integration at all. |
| 2 | **Audited** — at least one red-team audit covers it | Gate G4 and validator rule V15. Until it is audited, its rank is not a basis for prioritising work however good it looks. |
| 3 | **Not demoted** — no `deprioritise` or `insufficient_evidence` verdict, in the ranking row *or* in any audit record | A red-team demotion is categorical, not a numeric adjustment. A stale ranking row saying `retain` does not override an audit saying otherwise: disagreement fails closed. |
| 4 | **No unresolved critical finding** | A disputed evidence base is not a foundation for chemistry. A finding counts as unresolved unless it explicitly records a resolution — absence of a resolution field is not an answer. |
| 5 | **Minimum facet coverage** (0.40) | Deliberately the same threshold the ranking spec uses for `tier_3_insufficient_coverage`, so a target the ranking model itself calls under-curated cannot pass here. It is a floor, not an endorsement. |
| 6 | **Not tiered insufficient or deprioritised** | If the integration model does not regard the row as a basis for prioritising work, neither does this gate. |

`minimum_coverage` may be **raised** by a caller and never lowered: attempting to lower
it raises `ValueError`. A caller that can weaken the gate is not a gate.

### Reading a pass

A pass means: *the evidence accounting for this target is complete enough, and has
survived enough adversarial review, that spending computational chemistry effort on it
is defensible.* The reason string says so explicitly, because it may be the only thing
a downstream reader sees:

> `TGT:X passes gate G5: ranked by causal integration, audited by the red team with no
> demoting verdict and no unresolved critical finding, facet coverage 0.80 >= 0.40, tier
> 'tier_1_analyse_next'. This permits IN-SILICO analysis only; it is not a claim that the
> target is validated or that modulating it is safe, and nothing downstream may produce a
> protocol, dose, route or sourcing route.`

A pass is **not**: target validation, a safety statement, a claim that a modality
exists that is good enough, or permission for anything outside a computer.

### The gate is a parameter, not a convention

Every interface function takes a `gate: GateDecision` argument and calls
`require_gate()` before anything else, so a caller cannot forget it.
`require_gate()` rejects anything that is not a `GateDecision` — including a bare
`True` — so the gate cannot be satisfied by a truthy value.

```python
from blueprint.pharmacology.gates import explain_gate
from blueprint.pharmacology.interfaces import retrieve_structures

decision = explain_gate(target, ranking_row, audits)
if not decision:
    print(decision.reason)      # names every failing condition
else:
    retrieve_structures(target["target_id"], decision)   # NotImplementedError, Sprint 4
```

---

## 3. The interfaces

Grouped by the Sprint-4 stage they belong to (`ROADMAP.md` Sprint 4). Every one is
gated, every one is inactive, and every return type is a model artefact.

**Structure.** `retrieve_structures` (PDB, AlphaFold, homology models, each with
provenance and confidence) · `detect_pockets` (geometry only — a pocket is never a
claim of druggability).

**Chemistry landscape.** `retrieve_ligands` (from a pinned ChEMBL release;
`include_inactives` defaults to `True`, because a landscape built only from actives is
a biased landscape) · `chembl_landscape` (a description of what has been measured).

**Modelling.** `fit_qsar` (validation and applicability domain are part of the result,
and `split` defaults to `scaffold` because a random split over congeneric series
reports a performance the model does not have) · `pharmacophore_model` ·
`dock_ligands` (scores rank candidates for further simulation) · `molecular_dynamics`
(replica count and convergence diagnostics are part of the result, because one
unconverged trajectory is an anecdote).

**Prediction.** `bbb_permeability` · `predict_admet` · `selectivity_profile`
(off-targets are *named*, not summarised into a score: "selective" without a list of
what was tested is not a finding).

**Generation and optimisation.** `generate_candidates` · `multi_objective_optimise`.

---

## 4. What still has to be true before any of this is written

1. Gate G5 passes for the target — which currently requires a red-team audit that does
   not yet exist for any target in the cohort.
2. `ROADMAP.md` Sprint 2's exit criterion is met for it: a causal-gene attribution that
   is not `gwas_association_only`, or the target is demoted.
3. The causal-model boundary in [`models/causal/README.md`](../models/causal/README.md)
   is respected: the ranking model is an evidence-accounting device, and a rank is not
   an estimate of anything.

Until then this document, the gate and the signatures are the whole deliverable, and
that is the intended state.
