# Release security, privacy and data-rights audit

Audit date: **27 October 2026**. Research basis: `49effbaa3bcde35f58bc770d0e122a57c05e526d`.

**Status: ACTION REQUIRED — owner decision about historical privacy. No confirmed credential exposure was found in fetched Git history.** Safe working-tree preparation and publication do not remove older copies.

## Scope and method

- Fetched every advertised branch and tag, plus available pull-request heads. Eight remote branches, no tags/releases at audit start, no extra PR heads, and 20 reachable commits. All research branch tips are ancestors of the completed Sprint 5A snapshot; no historical branch was blindly merged or deleted.
- Inspected all 3,930 reachable Git objects: 20 commits, 526 trees and 3,384 blobs. The supplemental object scanner decoded gzip payloads and checked known JWT, Google API-key, GitHub-token and private-key formats plus email, personal-path and private-document indicators. It examined author/committer metadata as well as file content. A separate pass decoded all 36 historical Parquet blobs and found no credential or personal-path pattern. No secret values were printed or placed in reports.
- Gitleaks **8.30.1**, downloaded from its official GitHub release with SHA-256 checksum verification, scanned `git --all` and the release directory with full redaction. **30 alerts** were reviewed: **18 public accession identifiers and 12 ClinicalTrials.gov pagination cursors**. None was an authentication credential. [Redacted review locations](gitleaks_review.json).
- Reviewed file inventory and provenance for private correspondence, CV/identity/financial records, intervention-design assets and redistribution constraints. No controlled participant genotypes/clinical records or new unpublished intervention designs were identified. The `.bed` file is a published LD-block interval list, not participant genotypes. Parquet fields resembling sample identifiers were Open Targets biosample ontology labels, not donor IDs.
- The current-tree supplemental scan also decoded **878 gzip files and 53 Parquet files**, finding no credential patterns or personal machine paths. [Runnable scanner](../../scripts/release/audit_tree.py). No GitHub release assets or Actions artifacts existed at the audit start.

## Actions taken

- Removed personal machine prefixes from current code, logs, provenance and prose; added portable external-data/runtime boundaries. The frozen Sprint-4 JSON had only machine paths changed, with a dated checksum amendment; no scientific thresholds, memberships or seeds changed.
- Minimized unnecessary public-source email/telephone/address fields in ClinicalTrials.gov snapshots and email text in other raw snapshots. Preserved source URLs, scientific values and original acquisition hashes. These were public professional contacts, not evidence of private participant disclosure.
- Removed an unnecessary CC-BY-NC-ND full-text article XML instead of redistributing a modified article. Kept its citation, original checksum and approved acquisition pointer.
- Recorded **316 sanitation/removal entries** in the [transformation ledger](sanitisation_manifest.json). The raw manifest now verifies the distributed bytes and retains `original_download_sha256`/byte size when redaction changed a download. Per-source provenance retains original acquisition records. The strict validator still checks actual hashes; no integrity rule was disabled.
- Kept credentials out of `.env.example`; ignored external data and environment files. Used a public GitHub noreply identity for release commits.
- Scoped MIT to project-authored code. [Data rights](../../DATA_LICENSE.md) retain upstream restrictions, including BrainSpan noncommercial derivatives, source-specific QTL terms and external-tool licences. No controlled-access source was downloaded or republished for the release. No service terms or new account consent was accepted.

## Remaining historical privacy

The initial commit contains a personal author email. Historical branches/commits also retain machine paths and public-source contacts that are minimized in the new tree. The sensitive value is not reproduced here. Author identity and Hamiltonian Labs affiliation remain public as requested.

Only the owner can decide whether that historical metadata warrants a rewrite. [Concrete cleanup procedure](HISTORY_CLEANUP.md) is prepared. **No force-push, history rewrite, branch deletion or replacement repository was performed.** A rewrite cannot guarantee removal from forks, caches, clones or earlier downloads.

No OpenGWAS JWT, AlphaGenome key, GitHub credential or private key pattern was confirmed. Therefore this audit does not assert a service-specific leak or mandatory rotation based on Git evidence. Credentials used elsewhere should still be revoked if exposure is suspected outside this scope.

## Limits of assurance

Pattern scanning and targeted source review are not a proof that arbitrary secrets, every possible personal fact or every legal restriction are absent. This audit covers fetched reachable objects and accessible artifacts, not unreachable server objects, other users' private forks, caches or external local worktrees. Full third-party commercial reuse clearance and patentability opinions are not provided. Historical source assertions remain distinguishable from independently reproduced results.
