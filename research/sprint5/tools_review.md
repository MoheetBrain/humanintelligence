# Sprint 5: tools review for variant-to-gene resolution (2025–2026)

Written 2026-09-23 UTC. Licences and last-push dates come from the GitHub API, queried at about 21:33 UTC. "Not verified"
means I did not check it.

Some facts come from prior knowledge and were not re-fetched in this session:

- BrainMeta v2 N≈2,865;
- Genebass containing UKB field 20016 (fluid intelligence);
- the UKB-PPP and deCODE access terms;
- the SMR licence.

Check each of these before relying on it.

## Baseline already run by the project

- SuSiE-RSS with 1000G EUR LD;
- coloc.abf and coloc.susie against eQTL Catalogue summary statistics (590 pairs, 28 loci in Sprint 4);
- FOCUS gene-level fine-mapping.

Two limits of this baseline decide which new tools add inference:

1. **LD mismatch.** The GWAS is dominated by UK Biobank but the LD reference is 1000G. Out-of-sample LD degrades both
   SuSiE-RSS credible sets and coloc.susie.
2. **Donor overlap between QTL sources.** eQTL Catalogue brain datasets are bulk tissue, and several share donors. Under the
   Sprint-5 protocol, FOCUS, TGFM and cTWAS are contradiction checks only, not independent votes.

## Recommendations

| Tool | What it adds beyond the baseline | Inputs | Are the inputs public for us? | Licence | Recommendation |
|---|---|---|---|---|---|
| **RSparsePro_LD** (Zhang et al., bioRxiv 2024.10.29.620968) | Fine-mapping that is robust to reference-LD mismatch; it models the mismatch that SuSiE-RSS ignores | z-scores + reference LD | Yes (Davies z + 1000G LD) | CC-BY-4.0 (repo); pushed 2026-06 | **ADOPT_NOW**, as a sensitivity rerun on the 36 Gate-C loci. Credible sets that change are LD-fragile. |
| **SuSiE-inf / FINEMAP-inf** (Cui et al., Nat Genet 2024; FinucaneLab/fine-mapping-inf) | Models infinitesimal background effects; fewer spurious high-PIP variants in polygenic traits like cognition | z + LD (in-sample is best) | Partly. With 1000G LD the gain is uncertain because the methods assume in-sample LD. | GPL-3.0 | ADOPT_IF_DATA (in-sample or UKB LD matrices, e.g. the PolyFun UKB LD blocks) |
| **PolyFun + SuSiE** (Weissbrod 2020) | Functionally informed priors (baseline-LF annotations) that sharpen PIPs | Summary statistics + UKB-derived LD (public on AWS) + baseline-LF | Yes. The precomputed UKB LD matrices are in the public S3 bucket `broad-alkesgroup-ukbb-ld` (anonymous listing worked at 21:37 UTC) and match the UKB-dominated GWAS better than 1000G. | MIT; last push 2024-12 | **ADOPT_NOW**. It also removes the 1000G mismatch by using UKB LD. |
| **CARMA** (Yang et al., Nat Genet 2023; ZikunY/CARMA) | Bayesian model that detects and removes LD-inconsistent variants and allows annotations | z + LD | Yes | GPL-3.0 | ADOPT_IF_DATA. It overlaps RSparsePro's purpose; run one of the two, not both. |
| **SharePro** (Zhang 2023) | Colocalisation that is robust to multiple causal variants and LD grouping | Two sets of summary statistics + LD | Yes | Not verified | NOT_NEEDED. coloc.susie already covers multi-signal colocalisation. |
| **ColocBoost** (Cao et al. 2025, medRxiv 10.1101/2025.04.17.25326042; CRAN 1.0.10) | Joint colocalisation across many QTL contexts in one model (e.g. bulk cortex + 8 brain cell types + GWAS), which avoids pairwise multiplicity | GWAS + multiple QTL sets + LD | Yes, if cell-type QTL sets are added (below) | MIT (CRAN DESCRIPTION: "MIT + file LICENSE", v1.0.10, 2026-09-09) | ADOPT_IF_DATA. Adopt once brain single-cell QTLs are in. |
| **eCAVIAR** | CLPP colocalisation | Same as coloc | Yes | Not verified | NOT_NEEDED (superseded by coloc.susie) |
| **SMR/HEIDI** (Zhu 2016) with **BrainMeta v2** cortex eQTL/sQTL (Qi 2022, N≈2,865) | A pleiotropic-association test on a much larger cortex eQTL panel than eQTL Catalogue brain sets. HEIDI flags linkage. | GWAS + BESD eQTL | BrainMeta BESD files are downloadable from the SMR data page (site reachable, HTTP 200). Terms not re-checked. | SMR binary: free for academic use (not verified) | **ADOPT_NOW**. Use it as a directional check. Donor overlap with eQTL Catalogue brain sets means it collapses into the QTL class. |
| **FLAMES** (Schipper et al., Nat Genet 2025;57:323) | Integrates fine-mapped SNP-to-gene features with PoPS-style network convergence into one effector-gene score per locus | Credible sets (SuSiE) + MAGMA z + PoPS features | Yes (public annotations; bundled downloads) | MIT; pushed 2026-08 | ADOPT_IF_DATA. Useful, but PoPS and MAGMA convergence reuse the same GWAS, so treat it as a label, like L2G. |
| **cTWAS / multi-group cTWAS** (Zhao 2024 Nat Genet; xinhe-lab) | Adjusts TWAS for nearby genes and variants, and can jointly model several tissues or modalities | GWAS + PredictDB-format weights + LD | Yes (GTEx v8 brain PredictDB weights) | MIT; pushed 2026-09 | NOT_NEEDED as a vote (protocol: contradiction check only). Optional check if FOCUS disagrees with coloc. |
| **TGFM** (Strober et al.; BennyStrobes/TGFM) | Joint fine-mapping of gene–tissue pairs and non-mediated variants | GWAS + in-sample-matched LD + gene models | Partly (needs UKB-scale LD) | No licence file | NOT_NEEDED. It duplicates FOCUS/cTWAS in role and is a contradiction check only. |
| **MA-FOCUS** (Lu 2022; mancusolab/ma-focus) | Multi-ancestry FOCUS | Multi-ancestry GWAS + weights | No (no large non-EUR cognition GWAS) | GPL-3.0 | NOT_NEEDED |
| **Brain single-cell eQTL** – Bryois et al. 2022 (8 brain cell types, Zenodo 10.5281/zenodo.7276971, open) | Cell-type resolution (excitatory, inhibitory neurons, astrocytes, oligodendrocytes, OPC, microglia, endothelial, pericytes) that bulk eQTL Catalogue lacks | Nominal cis-eQTL summary statistics (full) | **Yes – open** | Zenodo open access | **ADOPT_NOW** with coloc.susie/ColocBoost. Donors partly overlap ROSMAP and other bulk sources, so under the protocol it is the same QTL class. |
| **PsychENCODE brainSCOPE** (Emani 2024) | Single-cell eQTL across about 28 brain cell types in about 388 donors | Summary statistics | Named in the Sprint-5 protocol. The site did not answer a curl HEAD request here (status 000), so access was not verified. | Not verified | ADOPT_IF_DATA (already planned) |
| **Fujita 2024 ROSMAP sn-eQTL** | Aged-cortex cell-type eQTL, 7 types | Summary statistics | Synapse / AD Knowledge Portal (registration) | Data-use terms | ADOPT_IF_DATA. The user must register. |
| **SAIGE-QTL / jaxQTL** | Single-cell QTL mapping frameworks | Individual-level scRNA + genotypes | No (no individual-level data) | – | NOT_NEEDED |
| **AlphaGenome (Atlas + API)** | Allele-specific, tissue-resolved regulatory predictions (RNA, splicing, CAGE, DNase, histone, TF) for every credible-set SNV, with direction. Orthogonal to QTL because it is sequence-based. | GRCh38 variants | **API key required** (see `alphagenome_notes.md`) | Non-commercial terms; client Apache-2.0 | **ADOPT_NOW once the key exists.** The script is ready: `pipelines/sprint5/alphagenome_query.py`. Rule: \|quantile\| ≥ 0.99 in a brain track; never used alone. |
| **Borzoi / Flashzoi** (calico/borzoi) | Sequence-to-RNA-coverage model with open weights; runs locally with no key. Cortex tracks come from GTEx/ENCODE RNA-seq. | Sequence (hg38) | Yes (weights public; GPU recommended) | Apache-2.0; pushed 2026-09 | ADOPT_IF_DATA, as a fallback SEQUENCE_MODEL if the AlphaGenome key is refused. Needs compute. |
| **Enformer** | Earlier sequence model (≈100 kb) | Sequence | Yes | Apache-2.0 | NOT_NEEDED (superseded by Borzoi and AlphaGenome) |
| **ChromBPNet** (kundajelab) | Base-resolution chromatin accessibility effects, cell-type specific if trained on brain snATAC | snATAC fragments or pretrained models | Only if pretrained brain-cell-type models are published (not verified here) | MIT; pushed 2026-06 | ADOPT_IF_DATA |
| **pQTL:** UKB-PPP (Sun 2023) plasma cis-pQTL; deCODE (Ferkingstad 2021) | Protein-level colocalisation, a different molecular layer from eQTL | Summary statistics | UKB-PPP on Synapse (registration); deCODE requires accepting terms. Brain and CSF pQTL sets are mostly restricted. | Data-use terms | ADOPT_IF_DATA. Plasma relevance to cognition is limited, and UKB-PPP is UKB-lineage (irrelevant for V2G, but noted). |
| **Genebass** (UKB 394k exome gene-burden, including fluid intelligence) | RARE_CODING convergence (common–rare tests T1–T5) | Public browser and Hail tables on public cloud | Yes (public) | Open | **ADOPT_NOW** for the RARE_CODING class. UKB-lineage, so it contributes to convergence only, never to association replication. |
| **GeneBayes s_het / gnomAD constraint** | Gene-level dosage and LoF intolerance priors | Public tables | Yes | Open | ADOPT_NOW (context only, as in the protocol) |
| **CNV:** ClinGen dosage (already cached in `data/raw/clingen`), AnnotSV/ClassifyCNV | Interpretation of individual CNVs | CNV calls | Not applicable to common-SNP loci | Open | NOT_NEEDED beyond the planned CNV re-audit |

## Three most useful additions

1. **Open brain single-cell eQTL (Bryois 2022, Zenodo, open) + coloc.susie/ColocBoost.** This gives cell-type resolution
   (excitatory vs inhibitory neurons, glia) at the 28 coloc loci, which bulk eQTL Catalogue cannot provide.
   - It needs no registration.
   - Under the protocol it stays in the same QTL class as bulk brain eQTL wherever donors overlap.
2. **AlphaGenome (Atlas via API).** This is the only SEQUENCE_MODEL-class evidence available: allele-specific, directional,
   brain-track predictions for every credible-set SNV, including splicing and TSS effects that eQTL cohorts miss.
   - It is blocked on a user-obtained API key.
   - Borzoi is the key-free local fallback.
3. **LD-robust re-fine-mapping (PolyFun with public UKB LD, or RSparsePro).** This tests whether the Sprint-4 credible sets
   and colocalisations survive the move from 1000G to UKB-matched LD.
   - It is the cheapest check on a known weakness of the whole V2G stack.
   - It changes which SNVs are then sent to AlphaGenome.

**Not needed:** SharePro, eCAVIAR, TGFM, MA-FOCUS, Enformer, SAIGE-QTL/jaxQTL. They either duplicate what coloc.susie and
FOCUS already do, or need data we do not have.
