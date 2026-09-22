# Codex / GPT-6 Astra branch audit

**Audit date:** 2026-09-18
**Auditor:** `agent:orchestrator` (Claude), read-only
> ## CORRECTION — 2026-09-22 (Sprint 3): THIS VERDICT WAS WRONG
>
> **The branch exists.** `agent/codex-positive-genetics` (commits `9be87c2`, `8e88623`; 764 files,
> 736,637 lines) is a **local, never-pushed linked worktree** at
> `/Users/moheet/Documents/ChatGPT/intelligence-codex`, registered in the canonical clone's
> `.git/worktrees` and visible to `git worktree list` from
> `/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠`.
>
> **Why the search below missed it.** (1) It ran from a different clone
> (`/Users/moheet/humanintelligence`, since removed) whose `.git` did not register this worktree;
> (2) a linked worktree's `.git` is a *file*, not a directory; (3) the filesystem sweep was
> depth-limited. The GitHub API check was correct — the branch was never pushed — and "not on
> GitHub" was read as "does not exist".
>
> **What the read-only Sprint-3 audit found.** X01 is a real, executed MAGMA 1.10 analysis on
> checksum-verified public data (Davies 2018 open subset; gnomAD v2.1.1), with an unusually complete
> provenance record (171/171 SHA256 hashes in its handoff manifest). Its gene-level layer has since
> been **independently re-derived and reproduced** in this repository
> (`data/raw/magma_x01/2026-09-22/REPLICATION_CHECK.json`). GRM3/ADGRB1/GABBR1 came from a separate
> Savage 2018 supplementary screen, not from X01. X02 does not exist — it was only ever proposed.
> `analyses/external/X01_cell_type_enrichment.yaml` carries the corrected record.
>
> The original text is kept below unchanged, as the record of the error.

**Verdict (2026-09-18, SUPERSEDED): THE BRANCH DOES NOT EXIST IN THIS REPOSITORY OR ANYWHERE REACHABLE FROM IT.**

Nothing was merged, cherry-picked, rebased or modified, because there was nothing to
act on. This document records the search so the negative result is auditable and so a
later reader does not assume the audit was skipped.

---

## 1. What was expected

The Sprint-2 brief described an independent research branch, expected to be named
something like `agent/astra-extreme-cognition`, containing:

* an extreme-cognition evidence map (~60 studies, with cohort-reuse tracking);
* human-genetics audits surfacing `GRM3`, `ADGRB1`, `GABBR1`;
* the Huguet 2024 2q12.3 duplication watchlist entry;
* **analysis X01** — conditional modern-human cell-type enrichment on the full public
  Davies cognition GWAS (~12.87 M variants, N ≈ 282,014) against Siletti and Allen
  human brain references;
* **analysis X02** — in progress: GWAS → fine mapping → adult brain QTL →
  colocalisation → gene → direction → AlphaGenome.

## 2. What the search actually found

| Check | Command | Result |
|---|---|---|
| Local branches | `git branch --all -vv` | only `main` and `sprint-1/foundation` |
| Remote branches (git) | `git fetch --all --prune` then `git for-each-ref` | only `main`, `sprint-1/foundation` |
| Remote branches (GitHub API) | `gh api repos/MoheetBrain/humanintelligence/branches` | `main` @ `9f0d5521`, `sprint-1/foundation` @ `24f4f922` — **two branches total** |
| Worktrees | `git worktree list` | one: the main checkout |
| Stashes | `git stash list` | empty |
| Unreachable objects | `git fsck --lost-found` | dangling **blobs/trees only**, all attributable to this session's own `git add` operations; **no dangling commits** |
| Commit authorship | `git log --all --format='%an <%ae>' \| sort -u` | two identities, both the repository owner's; **no Codex/Astra-authored commit** |
| Patch/bundle transfer | `find` for `*.bundle`, `*astra*`, `*codex*patch` | only unrelated projects (`hamiltonian_lang_m1*.bundle`, `hamiltonian_chess_astra_bridge`) |
| Other clones on disk | `find / -maxdepth 3 -name .git` | 13 repositories, **none a clone of `humanintelligence`** |
| Codex session history | grep `~/.codex/session_index.jsonl` for `humanintelligence` | **no session references this repository** |
| Codex session history | grep for `astra`, `extreme.cognition`, `alphamath`, `X01`, `X02` | one hit: a thread named "Build ASTRA cognitive substrate", `updated_at` 2026-09-11 — **six days before this repository's initial commit (2026-09-17)** and a different project |

## 3. Audit fields, answered

The brief asked for specific fields. Answering them honestly:

| Field | Value |
|---|---|
| Exact branch name | **none found** |
| Base commit | n/a |
| Commit count | **0** |
| Changed paths | none |
| Scientific analyses completed | **none present in this repository** |
| Raw datasets used | none present; no Davies GWAS download, no Siletti/Allen reference, no MAGMA/LDSC-style intermediates anywhere under `data/` |
| Provenance available | **none** — no checksums, no software versions, no parameter files, no logs |
| Reproducibility status | **cannot be assessed**; nothing to reproduce |
| Files safe to ingest | **none** |
| Files requiring verification | **all X01/X02 claims**, because the only record of them is the prose of the Sprint-2 brief |
| Methodological contradictions with Claude | cannot be assessed from prose alone; see §5 for the one substantive interaction |
| Overlapping evidence/cohorts | **unresolvable**, and this matters — see §6 |
| Schema incompatibilities | unknown; `docs/integration/CODEX_HANDOFF_CONTRACT.md` now specifies what must arrive so this becomes checkable |

## 4. What this repository will *not* do with the X01 numbers

The brief states X01's results in prose: Siletti β ≈ 0.097 and Allen β ≈ 0.086, both at
nominal *P* ≈ 0.011, with a dependence-safe corrected replication value of ≈ 0.08, and
no broad cell class meeting the prespecified corrected criterion.

Those figures are recorded in this repository as an **unverified external report**, not
as an analysis result, and the distinction is enforced rather than annotated:
`analyses/external/X01_cell_type_enrichment.yaml` carries
`verification_status: unverified_external_report` and
`provenance_class: external_analysis_unverified`.

The reasoning is the same reasoning the brief itself applies to X02 — *"Claude should be
able to ingest X02 without trusting prose summaries"* — and it applies with equal force
to X01. Principle **P2** of `docs/DATA_CONTRACT.md` requires every substantive claim to
bind to a machine-verified source. A number transcribed from a task description has no
source artefact, no checksum, no software version and no way to fail a check. Ingesting
it as a finding would mean this repository's provenance guarantees stop meaning anything
at exactly the point where an external collaborator is involved — which is the point
where they matter most.

The consequence is deliberate and asymmetric: **X01 currently supports no facet grade,
contributes no graph edge in the biological layer, and moves no target's rank.** It is
visible, attributed, and inert until artefacts arrive.

## 5. The one X01 conclusion that *is* actionable without the data

X01's stated negative result carries an instruction that costs nothing to honour and
would be expensive to get wrong:

> Do not filter future human genetics through a pyramidal-only gate.

This is adopted. It constrains *our* future analyses rather than asserting a biological
claim, so it needs no provenance to be safe — the cautious action and the unverified
claim point the same way. `docs/integration/CODEX_HANDOFF_CONTRACT.md` records it as a
standing methodological constraint on Claude-side genetics work, and Task E's discovery
sweep is genome-wide by construction.

Note also what X01 reportedly does *not* establish, because the brief is right that both
over-readings are available and both are wrong: a corrected *P* ≈ 0.08 is not "pyramidal
cells do not matter", and two nominal *P* ≈ 0.011 values are not "pyramidal cells are
proven intelligence cells". The repository records the asymmetric-power interpretation —
insufficient power to exclude modest specificity — as the honest reading.

## 6. The unresolvable risk this creates

Cross-agent evidence dependence is one of the orchestrator's owned responsibilities, and
it **cannot currently be discharged**. Codex reportedly assembled ~60 extreme-cognition
studies and tracked cohort reuse. This repository independently holds 182 sources, of
which the cognition-genetics subset draws heavily on UK Biobank and on the same Davies
and Savage GWAS lineage that X01 used as its input.

Without Codex's source list we cannot tell whether:

* its ~60 studies and our 182 sources overlap (near-certainly they do, at least on
  Davies/Savage);
* its "independent" replication across Siletti and Allen references is independent of
  evidence already counted in our facet grades;
* a future convergence claim between Codex's findings and ours would be genuine
  convergence or the same cohort counted twice.

**Any convergence claim spanning Codex output and Claude output is therefore
unverifiable today, and is refused rather than caveated.** `reports/project_truth_table.md`
records evidence dependencies per hypothesis precisely so this cannot be quietly
forgotten when the artefacts do arrive.

## 7. Blocker, stated plainly

This is the brief's own "inaccessible branch" condition. It blocks:

* **Task A** beyond this negative audit;
* **Task C** as an *ingestion* task — the machinery is built and X01 is registered as an
  unverified external report, but no verified analysis result exists to ingest;
* any independent verification of X01's method, inputs or code;
* any cross-agent evidence-dependence resolution (§6).

It does **not** block Tasks B, D, E, F, G, H, I or J, all of which were executed. The
repository is now strictly readier to receive Codex output than it was before this audit,
which is the most useful thing this task could produce given the branch's absence.

## 8. What would close this out

1. Push the branch to `origin`, or provide a `git bundle`, or a path to a local clone.
2. Deliver X01's artefacts per `docs/integration/CODEX_HANDOFF_CONTRACT.md` §4:
   the gene-level association input, the expression reference matrices and versions, the
   per-cell-class effect table, the correction procedure and its code, and checksums.
3. Deliver Codex's source list for the extreme-cognition map, so cohort overlap with
   this repository's 182 sources can be computed rather than assumed.

Until then, `analyses/external/X01_cell_type_enrichment.yaml` is the whole of X01's
presence here, and it is marked as such.
