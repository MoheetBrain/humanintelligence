# Blackboard Protocol v0.1.0

The Git repository is the blackboard. Agents do not converse; they read and write
structured artefacts. This document defines how.

## 1. Roles (Sprint 1)

| # | Role | Agent id | Spawned |
|---|------|----------|---------|
| 1 | Orchestrator | `agent:orchestrator` | — (the session itself) |
| 2 | Ontology / Graph Architect | `agent:ontology` | yes |
| 3 | AlphaCognition (human genetics) | `agent:alphacognition` | yes |
| 4 | Cognitive Brake Atlas | `agent:brakes` | yes |
| 5 | Cognitive Power Atlas | `agent:power` | yes |
| 6 | Comparative Intelligence | `agent:comparative` | yes |
| 7 | Causal Integration / Ranking | `agent:integration` | yes |
| 8 | Red Team / Evidence Auditor | `agent:red_team` | yes |

Hard cap: 8 roles, 7 spawned subagents. No agent may spawn subagents of its own.

## 2. Communication rules

1. **Write only what you own.** `docs/OWNERSHIP.yaml` maps path globs to owners.
   `scripts/check_ownership.py` reports violations; the orchestrator reverts them.
2. **Never edit another agent's records.** Disagreement is expressed as a *new*
   artefact: a contradicting claim, an audit finding, or a schema-change request.
3. **No schema improvisation.** If the contract cannot express something, write
   `docs/blackboard/schema_change_requests/{agent}-{nnn}.yaml`
   (`{request, motivation, proposed_change, blocking: true|false}`) and continue with
   the existing fields, marking affected records `status: active` with a note.
4. **No git operations.** Agents never run `git commit`, `git push`, `git checkout`,
   `git reset`, `git stash`, or `git rebase`. Only the orchestrator commits.
5. **No dependency installs.** Use `.venv/bin/python`. Needing a new dependency is a
   blocking schema-change request.
6. **Report by handoff note.** Every agent finishes by writing
   `docs/blackboard/handoffs/{agent}.md`: what was produced, counts, what was
   verified and how, what failed, what is uncertain, what the next agent needs to know.
   The handoff note is the only "message" an agent sends.
7. **Provenance or silence.** If you cannot verify a source, do not assert the claim.
   `status: withdrawn` plus a note is always better than an unverifiable claim.

## 3. Gates

| Gate | Condition | Enforced by |
|------|-----------|-------------|
| G1 schema freeze | ontology + schemas + validators pass their own tests | orchestrator runs `make validate test` before spawning domain agents |
| G2 format compliance | domain records validate under `--strict` | `make validate`; non-compliant records are not merged or committed |
| G3 provenance | every source `status: verified` | `make fetch-sources` then `make validate` |
| G4 audit coverage | every seed target has a full red-team audit | validator rule V15 |
| G5 chemistry gate | virtual pharmacology may only act on targets that survived integration **and** red-team review | `blueprint.pharmacology.gates.eligible_for_chemistry()` |

## 4. Work cycle

```
orchestrator: scaffold + contracts
        │
        ├─► ontology architect ──► G1 ──┐
        │                               │
        │   (after G1, in parallel)     │
        ├─► alphacognition ─────────────┤
        ├─► brakes ─────────────────────┤──► G2/G3 ──► red team ──► G4 ──► integration
        ├─► power ──────────────────────┤                                   │
        ├─► comparative ────────────────┤                                   ▼
        └─► integration (model code) ───┘                        orchestrator: build,
                                                                 reports, tests, commit
```

The red team runs **after** the domain atlases and searches independently; it does not
read the domain agents' conclusions as authority, only as targets for falsification.

## 5. Anti-hallucination rules (all agents)

1. Every citation is found through a tool call (PubMed/ClinicalTrials.gov/GWAS
   Catalog/Open Targets/HGNC), never from memory. If you recall a paper, you must
   still locate it with a search and verify its identifiers.
2. Claim content must be supported by text you actually retrieved (abstract, full text
   or database record). Set `extraction.basis` accordingly and
   `extraction.content_checked: false` if you could not read enough to be sure — the
   red team downgrades those automatically.
3. Never write an identifier (PMID, DOI, NCT, HGNC, Ensembl, UniProt, NCBI taxid,
   ChEMBL, GCST) that you have not seen in a tool response in this run.
4. Numbers: only copy effect sizes/sample sizes that appear verbatim in the retrieved
   text, into `as_reported`. Otherwise `not_extracted` / `null`.
5. Prefer fewer, better-verified claims. Coverage gaps are recorded as gaps, not filled
   with plausible-sounding assertions.
6. Cite negative and null results with the same rigour as positive ones; a domain
   agent that finds a failed human trial for its own target must record it.
