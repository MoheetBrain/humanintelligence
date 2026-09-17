# Roadmap

Sprint 1 builds the instrument. Later sprints use it. The sequencing rule is that no
sprint may prioritise interventions over targets whose causal case has not survived
audit — the failure mode this project is designed to avoid is a confident chemistry
programme aimed at a target that was never established.

---

## Sprint 1 — Infrastructure and first evidence ingestion *(in progress)*

**Milestone: AlphaCognition v0.1** — a ranked, audited, explicitly uncalibrated table
of candidate adult-modifiable control points, with every row traceable to verified
sources.

| # | Deliverable | State |
|---|-------------|-------|
| 1 | `README.md` — objective, constraint, architecture, evidence principles | done (revised at sprint close) |
| 2 | `THEORY.md` — Cognitive Power Envelope + OPEN→WRITE→SELECT→LOCK, as conceptual models | pending (integration) |
| 3 | Formal ontology (`ontology/`) | pending (ontology) |
| 4 | JSON Schemas + validators (`schemas/`, `graph/validate_graph.py`) | pending (ontology) |
| 5 | Graph compiler (NetworkX, three layers) | pending (ontology, phase 2) |
| 6 | DuckDB/Parquet evidence store | pending (ontology, phase 2) |
| 7 | Seed dataset, 15–30 targets with verified evidence | pending (atlases) |
| 8 | Red-team audit of every seed target | pending (red team) |
| 9 | `reports/intelligence_graph_v0_1.html` | pending |
| 10 | `reports/target_ranking_v0_1.csv` (PRELIMINARY) | pending |

**Explicit non-goals for Sprint 1:** no molecule design, no dose-response fitting, no
calibrated probabilities, no claim that any target is worth modulating.

---

## Sprint 2 — AlphaCognition v0.2: from association to causal gene

The point of this sprint is to replace positional gene mapping with real causal
attribution, which is the weakest link in v0.1.

1. **Fine mapping** — ingest credible sets for cognitive-ability GWAS (SuSiE/FINEMAP
   outputs where published; Open Targets credible sets otherwise), and record
   posterior inclusion probabilities as *source-reported model outputs*, never as our
   own probabilities.
2. **AlphaGenome integration** — variant-effect prediction for credible-set variants in
   brain-relevant regulatory contexts. *Blocked on `ALPHAGENOME_API_KEY`.* The
   architecture and offline cache layout are specified in
   `docs/ALPHACOGNITION_ARCHITECTURE.md`; no key exists in the current environment.
3. **Brain QTL colocalisation** — GTEx brain tissues, PsychENCODE, MetaBrain; eQTL and
   sQTL; coloc posteriors recorded with the method and its assumptions attached.
4. **Mendelian randomisation** — where valid instruments exist, with the standard
   sensitivity analyses and an explicit record of which MR assumption is most at risk.
5. **Adult cell-type expression** — Allen/Human Brain Cell Atlas adult data, to
   separate "expressed in adult human cortex in the relevant cell type" from
   "expressed in the developing brain only".
6. **Rare-variant and monogenic evidence** — to test whether a control point matters
   causally, while keeping the rescue-vs-enhancement distinction intact.

**Exit criterion:** every target in the top 25 has an explicit causal-gene attribution
level that is not `gwas_association_only`, or is demoted.

---

## Sprint 3 — The dynamic state model becomes quantitative

1. Identify which state variables have usable human proxies (31P-MRS phosphocreatine,
   ASL cerebral blood flow, FDG/glucose, MRS lactate, pupillometry for arousal, EEG
   measures for workspace stability) and which remain theoretical constructs.
2. Fit no-free-lunch baselines for `F` on public longitudinal cognitive/imaging data
   before attempting anything mechanistic; report predictive failure honestly.
3. Formalise the competing power-limitation hypotheses from
   `atlases/power/competing_models.yaml` as models with discriminating predictions, and
   test which public datasets could distinguish them.
4. Build the inverted-U/threshold response-shape library: for each state variable,
   record what shape the evidence actually supports, not what would be convenient.
5. Sensitivity and identifiability analysis: which control parameters are even
   identifiable from available data? Unidentifiable parameters are demoted regardless
   of biological appeal.

---

## Sprint 4 — Virtual pharmacology *(gated)*

Runs only for targets that survived causal integration **and** red-team review
(`blueprint.pharmacology.gates.eligible_for_chemistry`). Everything remains in silico.

1. Structure retrieval (PDB, AlphaFold), pocket detection, conformational analysis.
2. ChEMBL/bioactivity landscape per target; selectivity liabilities across the family.
3. QSAR, pharmacophore modelling, docking, then molecular dynamics for the survivors.
4. BBB and ADMET prediction; multi-objective optimisation where safety constraints are
   hard constraints rather than penalties.
5. Adversarial review of every selectivity and safety claim before any candidate is
   written down.

**Nothing in this sprint produces a protocol, a dose, or a sourcing route.**

---

## Sprint 5 — Comparative and evolutionary tests

1. Phylogenetically controlled analysis of candidate mechanisms across the species
   panel; convergence must survive phylogenetic correction to count.
2. Human-lineage divergence audit for every top target: where human biology differs,
   rodent causal evidence is discounted explicitly rather than silently.
3. Test the "expanded computation needs expanded power" hypothesis against comparative
   metabolic and neuron-count data, including the cases that contradict it.

---

## Continuous obligations

* **Red team runs every sprint**, not once. Downgrades are expected outputs.
* **Negative evidence is ingested with the same effort as positive evidence**; a sprint
  that adds no null results has probably searched badly.
* **The ranking model is re-tested for invariance** (duplicated evidence, paper count,
  single-cohort dependence) whenever it changes.
* **Every report keeps its calibration status visible.** When a probability becomes
  calibrated, it must say against what.

## What would falsify the framework

Recorded here so it cannot be quietly forgotten:

1. If the "control parameter" framing is wrong — if adult cognitive capacity is set by
   distributed, highly redundant architecture with no small controlling set — then the
   ranked table will keep shrinking in confidence as causal evidence improves, and the
   top targets will not converge. That pattern is the signature of failure.
2. If power is not limiting in healthy, rested, well-fed adults, the power atlas should
   show null or inverted-U effects on cognition in exactly the conditions where supply
   is already adequate.
3. If every "brake" release trades directly against a safety constraint at the same
   effect size, the "safe controllable window" dimension collapses and the programme's
   premise is undermined.
