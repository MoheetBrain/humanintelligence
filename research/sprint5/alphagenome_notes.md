# AlphaGenome and AlphaGenome Atlas: access audit (Sprint 5)

Checked 2026-09-23, 21:00–21:20 UTC. No account was created, no key was requested and no terms were accepted.
The machine-readable record is `data/sprint5/alphagenome_provenance.json`.

## Bottom line

- **Access status: BLOCKED_API_KEY.** Tissue- and track-level AlphaGenome scores are available only through the
  authenticated AlphaGenome API. This covers both the precomputed Atlas and live model inference.
  - The Atlas paper's Data Availability table lists "Raw Atlas Features: API only".
  - Authentication is a gRPC header `x-goog-api-key` sent to `gdmscience.googleapis.com:443`.
- **One-line user action:** sign in at https://deepmind.google.com/science/alphagenome/api, accept the AlphaGenome
  Terms (non-commercial), create a free key, then run:
  `ALPHAGENOME_API_KEY=<key> python pipelines/sprint5/alphagenome_query.py --variants data/sprint5/query_variants_cognition.csv`.
  This needs `pip install 'alphagenome>=0.9.0'`, which is not in the project venv.
- **Precomputed scores public without login:** no official route was found.
  - The downloads page (https://deepmind.google.com/science/alphagenome/downloads) lists three files:
    - AVI SNV scores: 88.5 GB, "Permissive Use".
    - Merged splicing scores: 20.6 GB, non-commercial.
    - AVI SHAP scores: 283.9 GB, non-commercial.
  - Unauthenticated requests to all three returned HTTP 500 "Internal Server Error" (UploadServer), both from curl and from an
    in-browser fetch while not signed in.
  - The page shows a "Sign in" link, and a third-party mirror says the source "is behind a sign-in". I interpret this as
    sign-in required, but I did not confirm it directly.
- **Unofficial Hugging Face mirrors (AVI only):**
  - The mirrors are `just-dna-seq/alphagenome_avi` (parquet, 29.8 GB) and `luoyiming1991/alphagenome-avi-grch38`
    (tabix VCF, 75.8 GB; remote region queries possible).
  - Both are ungated and both state that use means agreeing to the AlphaGenome Output Terms.
  - **I did not use them.** Using them means accepting terms. Their checksums also cannot be checked against the official
    file, and they contain only AVI, not brain tracks. The user has to decide.

## Facts (verified from source code, docs and paper)

- **Client.** PyPI `alphagenome` 0.9.0 was released 2026-09-08 (0.0.1 was 2025-06-25). The code is Apache-2.0.
  - 0.9.0 added `alphagenome.atlas.atlas` with `create(api_key)` and `AtlasClient`.
  - `AtlasClient` provides `query_variant`, `query_variants`, `query_interval` and `scorer_metadata`, backed by the
    `ListDenseVariantScores`, `GetDenseVariantScores` and `ListVariantScoresMetadata` RPCs.
  - I inspected repo commit b9fb2a1 (2026-09-18).
- **Limits.** The API is free for non-commercial use and "query rates vary based on demand".
  - Live predictions are suited to thousands of predictions and are "likely not suitable" above 1 million.
  - Atlas queries typically allow a larger rate.
  - No numeric quota is published.
- **Terms.** Outputs are non-commercial only. The exception is the "Permissive Use Downloadable Artifacts", which means the
  AVI SNV score download.
  - Outputs must not be used to train variant-effect models, and must not be used for clinical decisions.
  - Redistribution must carry the Output Terms notice.
  - Model weights are on Kaggle and on Hugging Face (`google/alphagenome-all-folds`, gated "auto"), under separate model terms.
- **Build and annotation.** GRCh38 (GRCh38.p13) with GENCODE v46; mouse uses mm10. hg19 is not supported.
- **Variant input and the Atlas lookup key.**
  - Input is `genome.Variant(chromosome='chr16', position=<1-based>, reference_bases, alternate_bases)`.
  - The Atlas key is chr:pos:ref>alt with REF taken implicitly from GRCh38, so a swapped REF/ALT is a lookup miss.
  - The Atlas covers all SNVs (8,812,917,339 scored alleles according to the mirror manifests).
  - More than 100M biobank indels were scored in the paper, but the downloads are SNV-only for now.
- **Modalities.** RNA-seq, CAGE, PRO-cap, DNase, ATAC, histone ChIP, TF ChIP, splice sites, splice-site usage, splice
  junctions and contact maps, plus a polyadenylation scorer.
- **Recommended scorers** (`variant_scorers.RECOMMENDED_VARIANT_SCORERS`):

  | Scorer | Window or mask | Score | Signed |
  |---|---|---|---|
  | RNA_SEQ | exon mask | log(mean ALT + 0.001) − log(mean REF + 0.001) | yes |
  | CAGE, PRO-cap, DNase, ATAC, TF ChIP | 501 bp | log2((ΣALT + 1)/(ΣREF + 1)) | yes |
  | Histone ChIP | 2001 bp | log2((ΣALT + 1)/(ΣREF + 1)) | yes |
  | Splice sites / splice-site usage | gene body | max\|ALT − REF\| | no |
  | Splice junctions | top-k splice sites of the gene | max\|log ALT − log REF\| of junction counts | no |
  | Polyadenylation | 400 bp at PAS | max\|LFC\| of distal/proximal isoform ratio | no |
  | Contact maps | 1 Mb | mean\|ALT − REF\| | no |
  | "Active allele" variants | as above | max(agg ALT, agg REF) | no |

- **Quantile score.** This is the rank of the raw score against about 300k common variants (MAF > 0.01 in any gnomAD v3
  population), computed per scorer and per track.
  - Signed scorers are mapped to [−1, 1]. The cap is ±0.99999.
  - Quantiles exist only for the recommended scorers.
  - The docs advise using the quantile to decide whether an effect is unusually large, and the raw score for its magnitude.
  - The Sprint-5 protocol threshold |quantile| ≥ 0.99 in a brain track uses this scale.
- **AVI** (from the Atlas paper, Methods).
  - **Inputs:** a neural network with an encoder, a hypernetwork producing non-negative weights, and a linear part. It uses
    18 features:
    - 10 AlphaGenome modality features, each the per-variant maximum effect across all tissues;
    - AlphaMissense;
    - 3 VEP protein-termination flags;
    - PhastCons 470-way and Cactus 241-way conservation;
    - 2 indel flags.
  - **Training labels:** gnomAD v4.1 proxy labels. Impactful means FAF95_GRPMAX < 0.001; neutral means 0.001–0.999.
    Samples are trinucleotide-matched.
  - **PHRED:** the genome-wide rank of the raw logit among all hg38 SNVs (10 = top 10%, 20 = top 1%).
  - **Attribution:** expected-gradients SHAP. The 18 values sum to the raw AVI.
  - **Caveat for us:** AVI is trained to separate rare from common variants and has no tissue or direction content. Common
    GWAS credible-set SNPs are expected to have low AVI by construction. AVI is not the right statistic for cognition loci;
    brain-track raw and quantile scores are.
- **Feature attribution and ISM.**
  - Live API: `score_ism_variants` and `alphagenome.interpretation.ism`. ALT-allele ISM has been available since 0.5.0.
  - Atlas: precomputed ISM motif maps (>2,500 motifs) in the portal. Bulk motif download is "coming soon".

## Brain and neural coverage (live-model track metadata)

- **Source.** `alphagenome_research` commit 0db53bd, `OutputMetadataResponse_ORGANISM_HOMO_SAPIENS.textproto`.
  - Local copy: `data/raw/sprint5/alphagenome/`, sha256 413b4063…49e8.
  - Derived table: `alphagenome_brain_tracks_human.csv`.
- **Counts.** There are 5,196 non-padding human tracks, of which 381 have a brain or neural ontology term.
- **CORTEX tier** (DLPFC UBERON:0009834, frontal cortex UBERON:0001870, temporal lobe, middle frontal gyrus, ACC,
  glutamatergic neuron CL:0000679, cortical astrocyte CL:0002605):
  - 11 RNA-seq tracks (ENCODE total RNA-seq; GTEx Brain_Cortex, Frontal_Cortex_BA9 and ACC_BA24);
  - 14 splice-usage, 8 CAGE, 3 DNase, 11 histone and 6 TF tracks;
  - 0 ATAC tracks.
- **Other brain tissue and cell types:**
  - Brain UBERON:0000955 and GTEx caudate, putamen, amygdala, nucleus accumbens, hypothalamus, hippocampus, cerebellum
    and substantia nigra;
  - neuron CL:0000540, astrocyte CL:0000127 and OPC CL:0002453.
- **Neural lines and progenitors:** SK-N-SH (31 TF tracks), neural progenitors and NT2/D1.
- **Missing:** brain ATAC, brain PRO-cap, brain contact maps, microglia and GABAergic interneurons.
- **Uncertainty.** The track list served by the Atlas has not been checked (that needs a key). The paper says the Atlas uses
  the same default scorers, run on the distilled model.

## Script: `pipelines/sprint5/alphagenome_query.py`

- **Input.** A CSV with `rsid, chr38, pos38, allele_string` in Ensembl allele order (GRCh38 REF first). Each ALT is scored.
  `cognition_increasing_allele` is carried through if present.
- **Modes:**
  - `atlas` (default) queries the precomputed Atlas. It is SNV-only and filters to the 48 brain and neural ontology terms
    listed in the script. Use `--all-tissues` to switch the filter off.
  - `model` runs live inference (`score_variant`) on a 1 Mb interval with the recommended scorers.
- **Output.** Parquet with one row per variant × scorer × gene × track. Columns include `raw_score`, `quantile_score`,
  `direction_alt_vs_ref` and `direction_for_cognition_increasing_allele`, plus a `.status.json` file.
- **What was actually run:**
  - `env -u ALPHAGENOME_API_KEY .venv/bin/python pipelines/sprint5/alphagenome_query.py --variants data/sprint5/query_variants_cognition.csv --limit 3`
    - Exit code 3 with NOT_TESTABLE.
    - 4 variant alleles were parsed: rs113029997 T>C, rs11860513 C>G and C>T, rs2008514 G>A.
  - An offline mock of the Atlas gRPC stub, using the real alphagenome 0.9.0 protobufs in a scratch venv.
    - The tidy step, brain filter, direction logic and parquet round-trip all behaved as expected.
    - The mock values are synthetic and are not results.
- **Not run:** any real API call. Atlas scorer names, including whether AVI is exposed as a scorer, are read at run time and
  have not been verified.
