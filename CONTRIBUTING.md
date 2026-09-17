# Contributing

This repository has an unusual contribution rule: **the burden of proof is on the
contributor, and it is mechanical**. A claim that cannot be verified by a script does
not enter the repository, regardless of how confident anyone is.

---

## 1. Ground rules

1. **Computational work only.** Read `docs/COMPUTATIONAL_ONLY_POLICY.md`. Nothing here
   plans, requests, designs or advises any wet-lab, in-vitro, ex-vivo, animal or human
   experiment — including self-experimentation.
2. **Provenance or silence.** No claim without a machine-verified source.
3. **No hand-written numbers.** Curated records carry ordinal evidence levels; numbers
   come from models under `models/` and carry a calibration status.
4. **Stay in your lane.** `docs/OWNERSHIP.yaml` assigns paths. Disagreement is
   expressed as a new artefact (contradicting claim, audit finding, schema-change
   request), never by editing someone else's record.
5. **`unknown` is a real answer.** Coverage gaps are recorded, not filled.

## 2. Setup

```bash
make setup     # .venv + editable install + pytest
make hooks     # install the pre-commit gate
make test      # offline test suite must pass before you start
```

## 3. Adding a claim — the required sequence

```bash
# 1. FIND the source with a tool, never from memory.
#    (PubMed / ClinicalTrials.gov / GWAS Catalog / Open Targets / HGNC)
# 2. Register the source in your own file:
#    evidence/sources/<agent>.yaml
# 3. Verify it against its registry of record:
.venv/bin/python scripts/fetch_source_metadata.py --agent <agent>
#    -> every source must reach status: verified.
#       title_mismatch means you mis-transcribed it, or it is not the paper you think.
#       not_found means the identifier does not exist. Do not "fix" it by guessing.
# 4. Write the claim in evidence/claims/<agent>/<TARGET>.yaml following
#    docs/DATA_CONTRACT.md §4. Fill EVERY required distinction field:
#      claim_type, causal_attribution.basis, context.life_stage,
#      context.baseline_context, phenotype_class, translation.*
# 5. Validate:
make validate
# 6. Check your lane:
.venv/bin/python scripts/check_ownership.py --agent <agent>
```

**What makes a claim acceptable**

| Requirement | Why |
|-------------|-----|
| The statement is your own one-sentence paraphrase | no copied source text enters the repository |
| It says *who measured what, in which species, at which life stage* | prevents species/age laundering |
| `extraction.basis` is honest (`abstract` vs `full_text` vs `database_record`) | the red team downgrades unchecked content automatically |
| Effect sizes only in `as_reported`, verbatim | no invented precision |
| Null and contradicting results recorded with the same care | the ranking depends on them |

**What gets a claim rejected**

* An identifier you did not see in a tool response during this session.
* A mechanism you are confident about but the retrieved text does not state.
* An effect size reconstructed from memory.
* A rodent memory result described as an intelligence effect.
* An educational-attainment result described as an intelligence result.
* A developmental result described as adult-modifiable.
* A binding affinity presented as evidence of efficacy.

## 4. Adding a facet assessment

Facets are the only place to express a graded judgement, and only for facets you own
(`docs/DATA_CONTRACT.md` §5.2). Every level needs a rubric reference, a rationale, and
claim references. A level that cannot name the claims supporting it is invalid.

## 5. Red-team contributions

The red team may **downgrade** and must **never delete**. An audit record names the
facet or claim, the old and new level, and the reason. Provenance is append-only:
`evidence/claims/claim_registry.lock` records every claim id ever created, and the
validator fails if one disappears.

## 6. Commit protocol

Every commit must satisfy the Commit Continuity Protocol; the pre-commit hook enforces
it (`.githooks/pre-commit`).

1. Inspect the real state: branch, last commit, staged and unstaged diffs, and run the
   tests relevant to the change.
2. Rewrite `docs/PROJECT_STATUS.md` so it is a complete, current snapshot of the whole
   project — not a description of the newest change.
3. Append exactly one entry to `docs/PROJECT_LEDGER.md` (append-only).
4. Stage both documents with the implementation change.
5. Use the commit message format in the protocol (`Stage / Objective / Changes /
   Verification / Project state after this commit / Risks-limitations / Next`).
6. **Never claim a test passed unless it was executed.** "Not run" is a valid and
   required answer. Record failures, blockers and uncertainty explicitly.
7. Never bypass the hooks; never commit secrets, `.env` files, virtualenvs, caches or
   large generated artefacts.

## 7. Review checklist

* Does every new claim have a `verified` source and a filled-in `translation` block?
* Does any number appear that no model produced?
* Could a reader mistake a rodent result for a human result anywhere in the diff?
* Does the change add evidence that merely repeats an existing source (duplicate
  evidence inflation)?
* If the change raises a target's rank, which facet moved, and does the cited claim
  actually support that level?
* Does any prose imply efficacy, safety or a protocol?
* Are generated artefacts regenerable offline (`make build` with no network)?
