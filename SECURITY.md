# Security and sensitive data

Please report suspected credentials, private documents or participant records privately through [GitHub private vulnerability reporting](https://github.com/MoheetBrain/humanintelligence/security/advisories/new) if enabled, or the contact published on the [Hamiltonian Labs website](https://www.hamiltonianlabs.co/). Do not open a public issue containing the sensitive value. A file path, commit identifier, service name and redacted description are sufficient initially.

Maintainers should revoke/rotate exposed credentials first, contain the current tree, and review every reachable branch/tag and release artifact. Deleting the latest file does not remove history. History rewrites, force-pushes and branch deletions require explicit owner approval. See [audit](docs/security/AUDIT.md) and [history-cleaning procedure](docs/security/HISTORY_CLEANUP.md).

Release scope: no credential patterns were detected in fetched history. One personal author email remains in initial commit metadata, and historical branches retain personal machine paths and unnecessary public-source contacts. The working release minimises those details. This is **ACTION REQUIRED for an owner decision about historical privacy**, not a claim that credentials were exposed or that Git history is globally clean.
