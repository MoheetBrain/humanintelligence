# Data, documentation and third-party rights

[MIT](LICENSE) covers project-authored source code and scripts only. It does **not** relicense third-party data, software, articles, annotations, model predictions or derivative columns. Original project documentation and original curatorial text are offered under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), to the extent Hamiltonian Labs owns them; quoted/source material is excluded.

There is deliberately no blanket permissive data licence for the combined tables. Original project classifications may be reused with attribution, but source-derived columns retain upstream terms. See the [source manifest](data/release/source_manifest.json), [dataset guide](DATASETS.md) and per-file [provenance index](data/release/provenance_index.json).

| Resource | Release treatment |
|---|---|
| Davies public subset; Bryois; devBrain; SingleBrain | Source CC-BY-4.0 terms recorded in provenance; cite the dataset and publication, preserve attribution and indicate transformations. Full bulk files are generally acquired separately. |
| GWAS Catalog | Metadata follows EMBL-EBI terms. Summary-statistic licences are accession-specific; newer submissions commonly CC0, older files may have other terms. Do not infer the data licence from the article. [Official guidance](https://www.ebi.ac.uk/gwas/docs/faq/). |
| GTEx | Portal licence, required attribution and no implied endorsement. **These are frozen V10/V11-era results and do not reflect the most current/accurate GTEx data.** The data used for the analyses described here were obtained from the GTEx Portal on 22–24 September 2026 (release/source timestamps in provenance). [Terms](https://gtexportal.org/home/license). |
| BrainSpan / Allen Institute | Research/noncommercial redistribution and derivatives under [Allen terms](https://alleninstitute.org/legal/terms-of-use). This applies to `data/gene_tournament/developmental_classification.parquet`, BrainSpan-derived developmental columns, and downstream tables retaining them. Commercial permission is not granted by this repository. |
| brainSCOPE / CommonMind / ROSMAP | Only public summary results and derived annotations retained. Their original source/access terms remain; controlled participant/genotype files are not included. No sublicence is asserted. |
| Open Targets / eQTL Catalogue / HGNC / pathway and safety databases | Preserve source attribution and source-specific reuse conditions. Aggregation does not erase underlying study restrictions. |
| AlphaGenome | Historical service-derived summaries retain service/model terms; directions are unresolved and excluded from release voting. No blanket commercial or redistribution permission is asserted. |
| PoPS | External code GPL-3.0. Large feature matrices are not bundled because a separate data licence was not established. Project wrappers do not relicense PoPS. |
| MAGMA / reference genotypes | Download separately under upstream terms. No MAGMA binary or human participant/reference genotype files are bundled. |
| Published articles | Unnecessary CC-BY-NC-ND full-text XML removed; original hashes and acquisition URL retained in the sanitation ledger. Other copyrighted PDFs/XLSX were already external. |

The small [HyPrColoc compatibility patch](pipelines/sprint5a/hyprcoloc_eigen_cast.patch) must be applied to separately acquired upstream software under its own licence; MIT does not override that upstream licence. No third-party executables are included.

The research archive is suitable for inspection and noncommercial research subject to these terms. For a permissive software-only archive, include source, tests and original documentation, and point to independently acquired data. A DOI deposit of the whole mixed-rights archive must accurately represent these restrictions; see [Zenodo](docs/ZENODO.md).
