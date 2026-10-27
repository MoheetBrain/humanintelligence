# Optional history privacy cleanup — approval required

No history rewrite or force-push was performed. The initial commit contains a personal author email; historical research branches contain machine paths and public-source contact fields. These are already public. No credential-format finding was confirmed by this audit, so no service-specific rotation is required on evidence from Git. Revoke OpenGWAS/AlphaGenome credentials if there was exposure elsewhere; never place a token in an issue or shell argument.

If the owner chooses historical removal:

1. Make a private mirror backup and record all branch/tag heads. Coordinate a push freeze with collaborators. Review forks, pull-request refs, cached release archives and external copies.
2. In a disposable local mirror, use `git-filter-repo` with a private mailmap to replace only the affected author/committer email with the public GitHub noreply identity. For file-content privacy, use explicit path/content callbacks and preserve the scientific columns. Do not include the original email in a committed mailmap or report.
3. Re-run object, gzip and Parquet scans and compare scientific data/protocol thresholds. Verify every rewritten branch/tag and regenerate content manifests.
4. Review the ref-by-ref diff and obtain explicit approval for the exact force-push. Do not bulk-delete branches. Ask GitHub Support about cached/PR references if necessary.
5. Instruct collaborators to reclone or carefully rebase; an old branch can reintroduce removed data. Rotate actual exposed credentials regardless of rewrite success.

A rewrite cannot guarantee removal from forks, caches, clones or downloads. The current release uses a public noreply commit identity and leaves the historical decision to the owner.
