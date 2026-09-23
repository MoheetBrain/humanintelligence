# Sprint 5 — gene dossier working notes, batch 3

Agent: literature red-team subagent, batch 3. Genes: GOSR1, CYP2D6, ZFTRAF1, DHRS11, WBP2NL, NAGA.
Session window: **2026-09-23 22:18 UTC – 2026-09-23 23:5x UTC** (first tool timestamp `date -u` = 2026-09-23T22:18:38Z).
Scope respected: target characterisation and evidence appraisal only. No compound design, dosing, docking, gene-therapy or
self-use content was produced. Existing drugs/probes are listed as facts in section 6 of each dossier and explicitly not
recommended. No accounts, sign-ins or terms acceptances. No commits, pushes or branch changes. Files written: the six dossiers
under `reports/sprint5/gene_dossiers/` and this file. `/Users/moheet/Documents/ChatGPT/intelligence-codex` was **not** touched
(it is referenced read-only inside `pipelines/sprint5/brainscope_ld.py`; I did not read from it).

## Shared inputs read (all genes)

- `data/sprint5/dossier_evidence_packets.json` (all six packets, verbatim)
- `reports/sprint5/causal_gene_evidence_matrix.csv` (all rows at L1565, L65265, L79922, L84282)
- `reports/sprint5/opentargets_refresh.csv` (the four locus rows, printed in full)
- `reports/sprint4/joint_gene_tissue_finemapping.csv` (per-configuration FOCUS PIP sums — the configuration-instability finding)
- `reports/sprint4/directionality_resolution.csv`, `reports/sprint4/direct_effect_survivors.csv`
- `reports/sprint5/cell_specific_directionality.csv` (all SIGNIFICANT rows + per-gene summary fields)
- `reports/sprint5/locus_confidence_rank.csv`, `reports/sprint5/brainscope_variant_summary.csv`,
  `reports/sprint5/brainscope_enhancer_gene_links.csv`, `data/sprint5/v2g_rows_opentargets.parquet`
- `data/raw/sprint5/rare_coding/DDG2P_panel_DD_download.csv`, `Collins_rCNV_2022.dosage_sensitivity_scores.tsv.gz`,
  `data/sprint5/rare_coding_gene_sets.json`
- `data/gene_tournament/study_classification.csv` (to resolve GCST accessions to studies/channels)

## Computed lookups performed (not from our tables)

Ensembl REST, queried 2026-09-23:
- Gene coordinates (GRCh38): WBP2NL 22:41,998,725–42,058,456; NAGA 22:42,032,595–42,071,198; CYP2D6 22:42,120,962–42,131,727;
  **CYP2D7 22:42,140,203–42,149,500**; CYP2D8P 22:42,149,886–42,155,001; SEPTIN3 22:41,969,443–41,998,221;
  ZFTRAF1 8:144,447,345–144,462,908; KIFC2 8:144,465,940–144,474,202; GOSR1 17:30,477,362–30,528,309;
  DHRS11 17:36,591,782–36,600,809; plus 17q11.2 and 17q12 neighbours (SLC6A4, NF1, CRLF3, EFCAB5, ATAD5, TEFM, ZNHIT3, GGNBP2,
  MYO19, PIGW, MRM1).
- Variant annotation: rs28670611 22:42,135,201 intron; rs5758550 22:42,016,707; rs133333 22:42,016,361; rs16947 22:42,127,941
  stop_gained/missense; rs133330 22:42,013,452 (MAF 0.486); rs5758605 22:42,145,348 intergenic (MAF 0.333);
  rs1135840 22:42,126,611 missense; rs1801311 22:42,090,719 missense; rs1005552 17:36,593,168; rs7212107 17:30,493,029;
  rs2054847 17:30,204,995.
- Pairwise LD, 1000 Genomes phase 3 **CEU** (r², D'): rs28670611–rs1135840 **1.000/1.000**; –rs1058164 0.980/1.000;
  –rs133330 0.863/0.978; –rs5758605 0.842/0.956; –rs2142694 0.842/0.956; –rs16947 0.367/1.000; –rs1801311 0.327/0.956;
  –rs1065852 0.246/1.000; –rs3892097 0.226/1.000; –rs5758550 0.167/0.926; –rs133333 0.167/0.926; –rs28371725 0.106/1.000.
  rs133330–rs1801311 0.364/0.958; rs5758550–rs133330 0.215/1.000; rs16947–rs133330 0.285/0.838.
  rs1005552–rs12937411 0.861/1.000. rs7212107–rs2054847 0.372/0.797.
  (The Ensembl LD endpoint returned intermittent HTTP 500s; every value above came from a response that parsed with an `r2`
  field. Values not obtained: none that I relied on.)
- `ENSG00000232710` = lncRNA 22:42,136,433–42,139,927 (inside the CYP2D6/CYP2D7 interval); `ENSG00000270083` = lncRNA
  22:42,089,630–42,090,028, sense-intronic to NDUFA6. Both are FOCUS winners in the GTEx-cortex-only configuration at L1565.

## Per-gene search log

### GOSR1 — notes written ~2026-09-23 23:1x UTC
Search terms: `GOSR1`; `GS28 AND (SNARE OR Golgi) AND (neuron OR brain)`; `Gosr1 knockout OR Gos28 knockout`;
`GOSR2 North Sea progressive myoclonus epilepsy`; `syntaxin-5 SNARE Golgi neurodegeneration`;
`GOSR1 AND (disease OR variant OR patient OR mutation)`; web: "GOSR1 GWAS 17q11.2 cognitive/EA/schizophrenia eQTL";
WebFetch of PMC5454371 (Lu 2017) for the 17q11.2 eQTL detail.
Accepted: 10198168 (founding characterisation), 12388752 + 15215310 (SNARE complex), 21860593 (only neuronal GOSR1 study),
28516910 (independent brain GWAS with GOSR1 cis-eQTL p 5.5e-12 — accepted but demoted after LD showed r²=0.37 to our lead),
23449775 + 41261947 (GOSR2 paralog disease, accepted only as plausibility), 31010806 (CRISPR/autophagy),
28638266/22397410/21696638 (oncology, safety context).
Rejected: 31312847 (stress urinary incontinence expression review — no relevance); 23698072 (Sézary 6q rearrangements — GOSR1
mentioned incidentally); 34944796, 32185116, 24124410 (no cognition or neural content); the entire GOSR2 clinical-management
literature beyond the two anchors (paralog, and clinical management is out of scope).
Judgement call recorded: I did **not** count Lu 2017 as replication of our locus, because rs2054847 vs rs7212107 r²=0.372.

### CYP2D6 — notes written ~2026-09-23 23:2x UTC
Search terms: `CYP2D6 expression enhancer rs5758550 regulatory variants`; `CYP2D6[Title] AND brain[Title]`;
`CYP2D6 AND (eQTL OR expression quantitative trait) AND (schizophrenia OR GWAS OR 22q13)`;
`CYP2D6 hybrid CYP2D7 structural variants long-read`; `Gaedigk CYP2D7 CYP2D6 hybrid`; `CYP2D7 138delT brain`;
`CYP2D6 tyramine dopamine formation`; `CYP2D6 5-methoxytryptamine serotonin regeneration`;
`CYP2D6 anticholinergic burden ActiFE cognitive`; `CYP2D6 neural substrates sustained attention`;
web: "CYP2D6 metabolizer status cognitive performance / UK Biobank".
Accepted: 23985325 + 30520769 (the real regulatory variants, and their weak LD to our lead is the point), 29875422 + 33631352
(CNV/hybrid mis-calling — the central methodological contradiction), 16169517 and 15051713 (the contested CYP2D7-protein pair;
both recorded, neither relied on), 11337939 + 12354285 (brain expression), 20368706 + 33024081 (CNS function, opposite
direction; treated as ONE evidence line, same group), 42547570 (ActiFE null after adjustment), 21958961 (ontogeny/PD),
32761352 (humanised-mouse brain CYP2D6, non-cognitive endpoint), 32767519 (explicit cognition null), 34025403 (ADR/dizziness),
34605737 + 12618595 (endogenous substrate chemistry, section 6 facts only), 27046643 (Davies 2016 — accepted but marked
NON-INDEPENDENT because it is UK Biobank).
Rejected: 42153180 (rat mTBI + melatonin/vitamin C — animal drug-metabolism, and supplement-adjacent, deliberately excluded);
24232670 (liver aQTL mediation, not brain); 34061827 (EHR ADR GWAS — CYP2D6 opioid ADR, not cognition); 42128045 (migraine
cell-type MR listing CYP2D6 as "druggable" — automated screen, phenotype irrelevant, and its drug framing is out of scope);
27918912 (perfusion-image classifier — methodological, same group as 20368706); the broad pharmacogenomics-guideline
literature (AMP/CPIC allele-selection papers) — relevant to genotyping practice but not to our causal question.
Deliberate omission: I did not search for or list dosing, dose-adjustment or prescribing guidance of any kind.

### WBP2NL — notes written ~2026-09-23 23:3x UTC
Search terms: `WBP2NL` (45 records, all 45 titles screened); `PAWP knockout mice egg activation`; `Satouh Y[Author] AND PAWP`;
`positive directional selection human male reproductive genes WBP2NL`.
Accepted: 28663133 (Xenopus neural/non-neural ectoderm — the only neural-development evidence), 26377222 (null mouse —
the key contradiction), 32219949 (PLCζ vs PAWP review), 28444612 + 29271520 (negative sperm-phenotype pair, counted once),
30010725 (WBP2 paralog redundancy), 38501904 (endoxifen GWAS hitting WBP2NL/TCF20 through CYP2D6 LD — the named artefact),
31344832 (non-CYP2D6 22q variants improving tamoxifen prediction), 42337223 (cognitive-frailty MR — accepted but marked
NON-INDEPENDENT and low quality), 32054438 (positive selection).
Rejected: the large ICSI/sperm-marker literature (27089467, 28076980, 29397567, 30882161, 38461455, 34762184, 31597592,
38628496, 37212058, 26780328, 28247051, 27932551, 30939204, 41800501 …) — same fertility question, many overlapping cohorts,
none informative for brain; 41465363 (flatworm feeding behaviour); 38937575 (hen fertility GWAS); 36340761 (aneurysm ML
feature selection); 41577206 (vitisin B/senescence — recorded in section 6 as a fact, explicitly not endorsed, and not counted
as evidence).

### NAGA — notes written ~2026-09-23 23:3x UTC
Search terms: `NAGA[Title] AND (brain OR neuro OR expression OR crystal structure)`; `Schindler disease`; `Kanzaki disease`;
`"alpha-N-acetylgalactosaminidase"[Title] AND (deficiency OR mutation)`; plus the DDG2P file and an LD check of rs1801311.
Accepted: 33931730 (Li 2021 — the strongest external mechanism; accepted with three explicit caveats incl. r²=0.327 to our
lead), 31468281 (intrafamilial heterogeneity — the strongest contradiction), 19683538 (structure), 23045655 (pharmacological
chaperones; section 6 facts only), 15136691 (Kanzaki neurology), 35521802 + 36102137 (plasma α-NAGA in psychiatric illness —
counted as one line, direction opposite to Li 2021), 42008923 + 32517081 (glycoproteinose landscape), DDG2P G2P00058.
Rejected: every non-human-gene "NAGA" hit (NaGa inorganic chemistry, Naga Jolokia chilli, bacterial NagA, Ao-Naga sociology —
the symbol is badly polluted in free-text search); 40994616 (α-NAGA in cancer diagnostics); 35025955 (schistosome SmNAGAL);
32169671, 34826537, 19502354 (bacterial/structural homologues); mass-spectrometry glycourinomics series (25243357, 26443390,
28338252, 28370531, 24788891 — assay development).
Judgement call: Li 2021 is the only paper in this batch I was tempted to call independent replication. I did not, because its
brain-eQTL panels overlap ours and its causal variant is a distinguishable signal (r²=0.33).

### DHRS11 — notes written ~2026-09-23 23:4x UTC
Search terms: `DHRS11` (18 records screened); `DHRS11 brain`; `DHRS11 novel 17beta-hydroxysteroid dehydrogenase Endo`;
`ZNHIT3 AND PEHO`; `Znhit3 cerebellar granule cell p53 p21`; `17q12 deletion AND (intellectual disability OR autism OR
schizophrenia)`.
Accepted: 26920053 + 31926269 (enzymology; one group, counted once with the packet text), 36430833 + 41015102 + 41679198
(Kobochromone/WH23 inhibitor series — section 6 tractability facts only, explicitly not recommended), 36759259 (brain pQTL MR,
MS phenotype), 37639066 (the failed ALS replication — same pQTL panels, so a genuine internal contradiction), 28335020 +
41857137 (ZNHIT3/PEHO — the alternative-gene case), 38216274 (17q12 deletion geography, used to *prevent* a wrong attribution).
Rejected: 42617929, 40963625, 40857880, 40205951, 38674383, 35027621, 33919636, 33505433, 30338214 (cancer/cardiac/fish/plant
transcriptomics with DHRS11 as an incidental feature — no relevance to brain or cognition).

### ZFTRAF1 (formerly CYHR1) — notes written ~2026-09-23 23:4x UTC
Search terms: `ZFTRAF1 OR CYHR1` (21 records screened); `KIFC2` (for the rival gene); plus a targeted grep of
`data/raw/sprint5/rare_coding/DDG2P_panel_DD_download.csv` for both symbols, and of
`Collins_rCNV_2022.dosage_sensitivity_scores.tsv.gz` for both symbols.
Accepted: 38641995 (Asif 2024 — biallelic LoF neurodevelopmental disorder; the single most important finding of this batch),
DDG2P G2P03563 (confidence "limited", previous symbol CYHR1), 10745073 + 12765788 (galectin-3 binding; one line),
21900684 (importin-α2 interactome), 26676980 + 41859033 (oncology, safety context), Open Targets rank-1 majority row.
Rejected as NON-INDEPENDENT/irrelevant: the cattle and sheep milk-production GWAS cluster (31576624, 30639022, 38203848,
39378607, 15566480, 15147413) — one BTA14 LD block near DGAT1, repeatedly re-reported; 41436687, 41130353, 41074104, 38925350,
33554123, 23674496, 27127921 (unrelated cancer/CRISPR-screen/saliva/oocyte transcriptomics).
Two self-checks that changed the dossier: (1) the symbol CYHR1 is what both DDG2P *evidence* and the Collins rCNV table key on,
so symbol-keyed joins in the packet build miss this gene — pTriplo 0.715 was recovered only by grepping the old symbol;
(2) our brainSCOPE GRN table assigns a 21-cell-type promoter element to CYHR1 at rs11784118/rs1985022 with
`target_in_candidate_list = False`, i.e. that evidence exists in our own files but never reaches the ENHANCER_LINK class,
which is built from Open Targets ENCODE-rE2G only.

## Cross-cutting observations (for the parent agent)

1. **FOCUS configuration instability.** At L1565 WBP2NL wins 4 of 8 configurations (PIP 0.857–0.915) while CYP2D6 wins 2
   (0.760–0.811) and two lncRNAs win the GTEx-cortex-only pair. At L79922 DHRS11 wins 3, ZNHIT3 1, GGNBP2 2. The packets quote a
   single "primary" PIP without a sensitivity band. This is a presentation issue, not a data error, but it changes how three of
   my six verdicts read.
2. **L65265 and L84282 have no FOCUS rows at all**, so `focus_primary_pip = 0.0` for GOSR1 and ZFTRAF1 means "not evaluated".
   Both dossiers say so explicitly; the matrix does not distinguish the two cases.
3. **Alias handling.** CYHR1→ZFTRAF1 is one confirmed instance where symbol-keyed joins drop real evidence; the fix should be
   applied across all 20 dossier genes.
4. **22q13.2 non-independence.** brainSCOPE contains CMC_MSSM and ROSMAP donors, so at L1565 the "2–3 cohort units" behind
   CYP2D6/NAGA/WBP2NL directions are partly the same people. At L84282 and L79922 the bulk unit is GTEx, which is
   donor-disjoint from brainSCOPE, so those pairings are cleaner — the independence caveat is not uniform across loci and our
   `bulk_independence_note` uses identical wording everywhere.
