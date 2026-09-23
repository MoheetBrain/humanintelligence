# Sprint 5 protocol — Human cognition causal gene resolution

*Frozen 2026-09-23 (UTC) on branch `sprint-5/causal-cognition-gene-resolution`, branched from
`sprint-4/causal-synapse-bridge` @ `e50eb4f`. All work is computational. Chemistry / intervention gate
CLOSED unless the adult intervention gate below is met, and even then only after human safety review.*

## What was known at freeze

Sprint 1–4 results (loci, G&C replication, Sprint-4 colocalisation, FOCUS, direction rule outcomes) were
known. **Not yet seen at freeze:** the current Open Targets release, brainSCOPE single-cell QTLs,
AlphaGenome predictions, the rare-coding tables, the CNV re-audit, the verified math-ability variants,
and developmental QTL colocalisations. The rules below were written before any of these were integrated.
The Chen 2023 exome gene list was known from the brief, and from the literature.

## Central question

Which human genes have the strongest statistically defensible evidence of a causal role in cognitive
ability? Which of those have an adult-relevant, directionally interpretable mechanism?

Three questions are kept separate for every candidate:

- **A: causal cognition gene.**
- **B: natural high-cognition gene.**
- **C: adult-modifiable gene.**

"LOCUS REAL, GENE UNRESOLVED" is an acceptable answer.

## Independence (the rule that governs everything)

**Association lineages.**

- UK-Biobank-lineage analyses never replicate each other. This covers Davies 2018, Savage 2018, UKB math factors and EA.
- Replication lineages:
  - G&C (UKB-free; slope 0.122 fixed from Sprint 4);
  - within-family data (NOT_TESTABLE while no JWT);
  - any Sprint-5 dataset whose cohort list excludes UKB, HRS, 23andMe and every Davies 2018 cohort.
- Zabaneh 2018 is sensitivity-only, because its HRS controls are inside Davies.

**Variant-to-gene (V2G) independence classes:**

- CODING
- RARE_CODING
- QTL
- ENHANCER_LINK
- SEQUENCE_MODEL
- DOSAGE_CNV

Definitions are in `protocol_rules.json`. The following are **not** independent votes:

- **Open Targets L2G** is assigned to the class of its top SHAP driver.
- **FOCUS/TGFM/cTWAS** is a contradiction check only, because it reuses the same eQTL cohorts.
- **Nearest gene** is a label only.
- **Module/pathway membership** is context only.

Bulk and single-cell brain QTLs collapse into one QTL class when donors overlap.

## Rankings (no arbitrary weighted totals)

- **A. Locus confidence.** The summed log10 Bayes factor of replication over independent lineages, with parametric rank intervals.
- **B. Causal-gene confidence.** Ordinal V2G strata (the class precedence in the JSON), then the count of distinct classes.
- **C. Adult direction.** The unchanged Sprint-4 rule (≥3 strong gene-level adult-brain colocs, ≥80% agreement, on rows **and** on independent cohort units), stratified D1–D5.
- **D. Human perturbation.** Strata P1–P5. Disease-LoF is never inverted into enhancement.
- **E. Research priority.** Pareto (non-dominated) layers over A–D. The Top-20 is taken from successive layers.

## Tests fixed in advance

The following test definitions are in `protocol_rules.json`:

- **Common–rare convergence:** T1–T5, each against a matched null.
- **Math cross-domain:** M1–M3.
- **AlphaGenome:** strong effect means |quantile| ≥ 0.99 in a brain track, and is never ranked alone.
- **Open Targets refresh flags.**
- **Deep-dive promotion rule.**
- **Adult intervention gate:** 7 criteria. Safety is never auto-cleared, so the chemistry gate stays CLOSED.

## Amendments

Any change after freeze is appended here with a date, the reason, and a new hash line. The **last**
hash line is authoritative. `pipelines/sprint5/common.py:load_rules` refuses to run on a mismatch.

RULES_JSON_SHA256: 0f4642189e623a07736c484909c3527606286616bacc3e9a909059d2ead3d0eb
