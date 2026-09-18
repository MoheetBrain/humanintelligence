# Convergence across evidence modalities — v0.2

**Sprint 2, 2026-09-18.** Machine-readable rules:
[`atlases/convergence/dependency_rules.yaml`](../atlases/convergence/dependency_rules.yaml).

> **Headline.** After removing double-counted evidence, **no target in this repository
> reaches more than three independent evidence modalities**, and the three are always the
> same three: human genetics, human intervention, animal causal. The repository has no
> target whose case rests on genuinely diverse ways of knowing — and the apparent breadth
> before the correction was largely an artefact of filing one observation in two places.

---

## 1. What this layer is for, and why it nearly produced a false result

Convergence is the strongest argument this project can make. If human genetics, an
intervention in humans, animal causal work and comparative biology all point the same way,
the conclusion survives the failure of any one method.

It is also the easiest argument to fake by accident. The same dataset, read through two
pipelines and filed in two atlases, is indistinguishable from two observations at the point
where someone counts columns.

The first pass of this audit produced a matrix in which **all 27 targets appeared in two or
more modalities**, and several in five. That looked like a strong result. It was an
artefact. Every one of the mechanisms below was found in the repository's actual records,
not hypothesised:

| # | Mechanism | What it did to the count |
|---|---|---|
| D001 | Atlas facet assessments counted beside the claims they are *computed from* | Added a phantom modality to every brake- and power-atlas target |
| D002 | One dataset replicated across targets | One GTEx v8 run populated the molecular column for essentially all 27 |
| D003 | Same summary statistics, two pipelines | GWAS Catalog and Open Targets L2G double-counted for 11 targets |
| D004 | A null trial filed as its own modality | Added a phantom modality to exactly the targets with the best evidence |
| D005 | Same cohort, different PMIDs | UK Biobank recurs under many source ids |
| D006 | Same trial reached by two retrieval routes | Read as replication when it verified a method |
| D007 | One paper registered by two atlases | Three of HCN1's five marks trace to two papers |

**The correction bites hardest where the temptation is strongest.** D001 and D004 remove a
modality precisely from the targets whose evidence is richest, because those are the ones
filed in the most places.

### The single most instructive case

HCN1 is the repository's best-covered target — facet coverage 1.00, the only target with
no unassessed facet — and it touched five apparent modalities. Three of those five marks
trace to **two papers** (`SRC:PMID:30392798`, `SRC:PMID:34759318`), each of which supplies
molecular, animal *and* comparative records. The best-covered target is the clearest case
of the artefact.

---

## 2. What a modality is

A modality is an independent **way of knowing**, not a folder. Two records belong to the
same modality if a single methodological failure could take both down.

Three things that look like modalities and are not:

* **The brake and power atlases.** They are *views over* the claim base, not sources of
  evidence. Their facet grades cite the same `CLM:` records that supply the animal and
  intervention modalities.
* **Clinical failure.** A failed trial is a human-intervention observation with a negative
  sign. It is a *value*, not an axis.
* **Theory.** Theory nodes — including `THEORY:selective_encoding` — are not evidence and
  may never contribute to a count, however well a candidate fits them.

---

## 3. Corrected convergence

| Independent modalities | Targets |
|---|---|
| **3** (genetics + intervention + animal) | CKB, DRD1, GRIN2B, GRM5, HTR2A, HDAC2, SLC16A1, GABRA5, EIF2S1, EIF2B_COMPLEX, GPR158, KCNQ3, HCN1 |
| **2** | CHRM1, ADORA1, KCNQ2, KL, PTPN5, RGS14 *(intervention + animal)*; CRTC1, OTX2, SLC16A7, SLC6A8 *(genetics + animal)*; PDE4B *(genetics + intervention)* |
| **1** — animal only | HCAR1, SLC16A3, RTN4R |
| **0** | none |

**Three qualifications, without which this table is misleading.**

1. **Breadth is not direction.** GABRA5 reaches three modalities and its human-intervention
   leg is a *replicated null*. Reaching three modalities is not a strength signal; it is a
   statement about how many ways a question has been asked.
2. **A present modality can be weak.** The genetics leg of most three-modality targets is
   positional GWAS mapping with causal-gene attribution 0–2 and **zero molecular-QTL
   colocalisation anywhere in the repository** (70/70 L2G records carry an empty
   colocalisation list — measured and absent, not unexamined).
3. **The ceiling is three, and it is the same three every time.** No target has comparative,
   extreme-cognition or positive-genetics evidence contributing to its count. The
   repository is not converging from many directions; it is converging from one triangle.

---

## 4. Modalities that contribute nothing

* **Extreme cognition — zero artefacts.** No claim, source, assessment or target record
  exists. Its only trace is an outstanding deliverable attributed to a branch that
  [`CODEX_BRANCH_AUDIT.md`](../docs/integration/CODEX_BRANCH_AUDIT.md) establishes does not
  exist. **This is a gap, not a null.**
* **Comparative — 23 of 27 assessments are `not_assessed`.** Only HCN1, RGS14, KCNQ2 and
  KCNQ3 are graded, and the comparative claim base is mostly non-target topics.
* **Positive genetics — orphaned.** The 2q12.3 record's eight genes have zero overlap with
  the 27 candidates, so it contributes to no convergence anywhere. Its independence from
  the genetics modality is also **unresolved**: its own red-team list asks how much of its
  258,292-person cohort is UK Biobank, and that question is unanswered. Unknown overlap is
  not zero overlap, so it is scored `dependence_unknown`, never independent.
* **Human molecular — no causal layer.** One bulk-tissue expression dataset. No QTL, no
  colocalisation, no evidential cell-type record. The one cell-type analysis (X01) is inert
  by contract and enforced inert by validator rule V-EXT.

---

## 5. The honest limitation of this layer

**These rules were applied by hand.** No validator enforces them and no script recomputes
the corrected counts from the records. `independent_source_count` de-duplicates by
`source_id` only, which catches the same PMID cited twice and misses every mechanism in the
table above.

A future agent can therefore reintroduce all seven double-counts without any check firing.
That is the largest piece of technical debt Sprint 2 created, and it is recorded here
rather than left implicit. The fix is a convergence scorer that walks `claim_refs`, applies
D001–D009 and emits `corrected_independent_modalities` per target, plus a validator rule
forbidding any convergence statement not produced by it.

---

## 6. One correction this audit forced elsewhere

`docs/PROJECT_STATUS.md` previously described the GABRA5 basmisanil null as
**"independently re-retrieved"** by a second route. Both routes terminate on the same
trial, **NCT02953639**. That is a retrieval-method check, not an independent replication,
and the wording could be read as a second item of evidence. Corrected 2026-09-18.

The α5-GABA-A null *does* have a genuine replication — but it is a **different trial**,
NCT02484703, and that is what the claim should rest on.
