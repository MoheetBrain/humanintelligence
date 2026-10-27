# Zenodo archival procedure

The repository contains `CITATION.cff`, a versioned changelog, locked release dependencies, source provenance and `RELEASE_MANIFEST.json`. **No Zenodo connection or DOI was created.**

1. Sign in to Zenodo and connect the existing GitHub repository, or create a manual software deposit for tag `v0.1.0`. Review exactly which archive is deposited before publishing.
2. Prefer a software/documentation deposit with links to separately licensed data when a uniform permissive licence is required. A full repository deposit contains mixed rights, including BrainSpan noncommercial derivatives; do not label the whole archive MIT or CC0. Use appropriate component-specific licence metadata and attach `DATA_LICENSE.md`.
3. Title: *Hamiltonian Labs — Human Cognition Genetics*. Version: `0.1.0`. Creator: Hamiltonian Labs / MoheetBrain as in `CITATION.cff`. Research snapshot: 24 September 2026; release: 27 October 2026. Resource type: software. Add the repository/tag URL and original dataset DOIs as related identifiers, with their correct relation types.
4. Upload the release manifest and validation/correction notes. Verify checksums, preview metadata, and publish once the licence selection and contents are correct. Do not describe the deposit as peer reviewed.
5. Add the actual version DOI and concept DOI to `CITATION.cff`/README in a later commit. Never invent a DOI or use a reserved draft DOI as if published.

GitHub remains the release location until this owner-controlled archival step is completed.
