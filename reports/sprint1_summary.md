# Sprint 1 Summary — Intelligence Blueprint

**Status: PRELIMINARY.** Nothing in this document or in `reports/` is a safety claim, an
efficacy claim, or a recommendation to modulate anything. All work was computational
(`docs/COMPUTATIONAL_ONLY_POLICY.md`).

*Generated 2026-09-17 by `agent:orchestrator`. Every number below was produced by a
command that was executed; commands and results are in `docs/PROJECT_LEDGER.md`.*

---

## 1. What the sprint was for

Build the instrument, not the answer: an evidence layer strict enough that a claim about
adult cognitive capacity cannot enter it without machine-verified provenance, plus the
ontology, state model, graph and uncertainty machinery needed to reason over it. The
first scientific milestone — **AlphaCognition v0.1** — was to rank candidate
adult-modifiable causal control points and be honest about how little the ranking can
support.

## 2. The scientific result is negative, and it is the most useful thing here

**No target in this repository currently has a defensible causal case for adult cognitive
enhancement.**

| Measure | Result |
|---|---|
| Seed targets at `causal_gene_attribution` **level 0** | **17 of 27** |
| Highest causal-gene level anywhere in the cohort | **2** (nothing at 3 or 4) |
| Targets with molecular-QTL colocalisation supporting their gene assignment | **0** |
| Targets reaching `tier_1_analyse_next` | **0** — the tier is empty |
| Highest D1 (causal cognition relevance) median | 0.544 (HCN1); cohort median 0.346 |
| Red-team verdicts | 20 retain-with-downgrade · 4 retain · 3 deprioritise · 2 insufficient-evidence |
| Brake-atlas facet levels reaching 4 | **0** |

Three findings drive that.

**The α5-GABA-A human null is replicated.** `agent:brakes` could not retrieve one
completed trial's results and refused to guess, leaving a claim id deliberately unused
and writing down exactly what would settle it. `agent:red_team` retrieved it: a treatment
difference of **+0.28 MCCB composite T-score points (95% CI −1.47 to +2.02, p = 0.793)**
on a scale whose population SD is 10, with target engagement demonstrated in the
companion trial. That is not absence of evidence; it is a *precise* null. With CLEMATIS,
the human null on this mechanism is replicated — on the most-studied brake target in the
seed list.

**Educational attainment had been laundered into fluid reasoning.** An eligibility flag
marked "mathematical ability" as never a stand-alone basis for a grade; the code that
generated grades never read the field. The underlying records are "Self-reported math
ability" and "Highest math class taken" from a 1.1-million-person educational-attainment
GWAS. Correcting it moved 10 facet grades, **all downward**, and revealed that of the 12
genes previously reported as having locus-to-gene candidacy on a cognitive trait, only
**6** actually do.

**Power is not demonstrably limiting in healthy adults.** `agent:power` could not reject
the null that healthy, rested, well-fed adult cognition is not power-limited: pooled human
RCTs are null at normal baseline, benefit appears only in low-baseline or stressed states,
and adult-onset creatine-transporter deletion produces no learning deficit where
developmental loss does. `THEORY.md` §1.4 states the consequence for the project's own
organising hypothesis rather than burying it.

**Paper count did not survive contact with evidence quality.** GABRA5 ranks 18th holding
the cohort's second-largest source count, and CKB ranks 22nd holding the largest — both
well studied *because* their nulls are well characterised. That inversion is principle P5
working as designed.

## 3. What exists

| Layer | Contents |
|---|---|
| Ontology | node/edge type system with domain/range constraints, 27 computational primitives, state-variable type system, controlled vocabularies, 125 definitional edges |
| Schemas | 12 JSON Schemas + pydantic models; **32-rule validator** |
| State model | **101 state variables** across 8 domains + `dynamics.yaml` (no `F` fitted) |
| Evidence | **182 sources** (all verified or release-verified), **293 claims**, **400 evidence items**, 27 dossiers, **405 assessment rows**, **30 audits** |
| Graph | **1284 nodes / 1703 edges** — evidence 905/1256, biological 304/366, intervention 75/81 |
| Store | DuckDB + Parquet: 11 tables + provenance, 12 views |
| Models | facet rubric, facet→dimension spec, ordinal→Beta mapping, Monte Carlo rank intervals, polarity-aware caps, information-gain, conjunctive composite |
| Reports | interactive graph (1.67 MB, **zero remote references**), ranked table, red-team audit, integration narrative |
| Tests | **832 passing, 0 failing** |

Provenance split across graph edges: 636 claim-derived, 942 reference-data,
125 ontology-axiom. Of the claim-derived edges, only **130 count as support** and **34
assert an effect**; 10 are null results, rendered distinctly in the report with a legend.

**The graph is sparse, and that is the answer.** A contract that refuses an edge without
provenance, refuses efficacy from binding, refuses a null recorded as a gap and refuses a
direction nobody stated produces a small graph. `make graph` prints that note itself.

## 4. What the machinery caught that a human reviewer would likely have missed

* A fabricated identifier cannot enter: every PMID/NCT/GCST is checked against its
  registry, titles matched by similarity, with immutable snapshots. 117/117 sources
  rebuilt **offline** from committed snapshots; one independent spot-check confirmed an
  exact match against live PubMed.
* **Five contract constraints turned out to forbid a true record** and had to be fixed
  (R5, R11, R14, V16b-sym, `sample_size` minimum ≥ 1, which forbade a withdrawn trial's
  zero enrolment). See D014: the same conflation — *"we looked and found nothing"* used
  for *"there was nothing to look for"* — occurred five times across four agents and the
  contract itself.
* Requiring a zero to declare `search_basis` made one atlas discover its zeros were
  literature-only, and **overturn two of its own published statements**.
* A composite gate was inert (a 0.35 cap cannot bind a product of six sub-unit
  dimensions); fixed and now firing on exactly the 3 critical-finding targets, where as a
  raw threshold it would have bound on 0 of 27 rows.
* A "sensitivity variant" was a tautology (`geometric_mean` is a monotone transform of
  the product, so it agreed by construction).
* The ranking model was **silently discarding red-team downgrades** — three of five
  adjustments raise `counter_level` rather than lowering `level`, and its input type
  rejected those as forbidden upgrades. It failed closed and logged nothing; only
  reconciling counts against the audit surfaced it.
* The validator CLI was mislabelling every `info` finding as a warning.

## 5. Honest limitations

1. **Three of four atlases never ran a registry search.** Four of the red team's five
   headline findings came from `whyStopped` and `resultsSection` fields no literature
   search returns. Every `human_intervention_evidence: 0` in those atlases carries the
   exposure that let the power atlas overturn itself. **This is the top Sprint-2 task.**
2. **The ordering is materially operator-dependent**: Kendall tau-b 0.719
   (product/minimum), 0.765 (product/additive), **0.473** (minimum/additive).
3. **Every reported interval is too narrow** by an unquantified amount: the composite
   assumes independence between dimensions that demonstrably share evidence.
4. **Principle P8 does not hold at the composite.** Under a product, interval width is
   dominated by the smallest factor's magnitude, not its uncertainty, so a level-0 facet
   yields a wider relative interval than an unassessed one. "Unknown widens" holds at
   facet and dimension level only — which is why the **rank interval**, not the composite,
   is the headline output, and why `coverage` is a required column.
5. **All probabilities are uncalibrated subjective priors** from a documented
   ordinal→Beta mapping. They are not empirical probabilities and are labelled
   `uncalibrated_subjective` in every row.
6. **The seed list is the brief's, not a discovery.** Coverage is uneven by construction:
   the comparative atlas could honestly assess only 4 of 27 targets.
7. 5 `causal_perturbation` claims still carry `direction: unclear` where a measured
   direction should exist; 10 contract deviations survive in the implementation
   (`docs/ONTOLOGY_NOTES.md` §4), two material.
8. AlphaGenome was never called — no API key in this environment. The module is
   interface-only and cannot emit a number.

## 6. Agent usage

Blackboard architecture, 8 roles, **7 spawned subagents**, no agent-to-agent messaging,
disjoint path ownership, all commits by the orchestrator. Roles and outcomes are in
`docs/AGENT_REGISTRY.yaml`; every schema-change request and its ruling is in
`docs/blackboard/RESOLUTIONS.md` (R1–R19).

Nineteen contract rulings were required, **most triggered by agents hitting real defects
in a contract written before any data existed**. That is the strongest available evidence
for the blackboard choice over a swarm: the defects surfaced as filed requests with
worked examples and documented workarounds, not as drift.

## 7. Next actions

See `docs/PROJECT_STATUS.md` for the current snapshot and `ROADMAP.md` for the sprint
plan. The top item is not a feature: **run target-directed registry searches across the
three atlases that never did**, because the repository's zeros are currently less
trustworthy than its ones.
