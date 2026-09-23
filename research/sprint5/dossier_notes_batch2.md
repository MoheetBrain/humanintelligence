# Sprint 5 gene-dossier literature notes: batch 2

These notes cover KDM5B, ANKRD12, RC3H2, CACNA1A, NEGR1, SLC39A8 and NT5DC2.

**Session and scope**
- Author: a literature red-team subagent.
- Time: all work was done in one session on 2026-09-23 (UTC). The system clock read 22:25Z mid-session and 22:31Z when these notes were written. The per-gene times below are approximate and in work order.
- Scope: target characterisation and evidence appraisal only. No compound design, dosing, intervention or self-use content.
- Files written: `reports/sprint5/gene_dossiers/{KDM5B,ANKRD12,RC3H2,CACNA1A,NEGR1,SLC39A8,NT5DC2}.md` and this file. Nothing was committed, and no branch was switched.

**Tools**
- PubMed MCP (search and metadata), plus NCBI E-utilities via curl (esearch, esummary, efetch, elink to PMC full text).
- WebSearch, the ClinicalTrials.gov MCP, and the ChEMBL MCP (target lookup only).

**Local read-only look-ups** (no project files modified):
- `data/sprint5/dossier_evidence_packets.json`, `reports/sprint5/*.csv`, `reports/sprint4/joint_gene_tissue_finemapping.csv`, `data/sprint5/evidence_units.parquet` and `data/sprint5/ot_l2g_features.parquet`.
- Local sumstats:
  - Savage 2018: `data/interim/sumstats/savage/...`
  - GenLang PIQ: `data/interim/sprint5/genlang/GCST90104472_buildGRCh37.tsv`
  - G&C TMA: `data/interim/sprint4/genc/tma_gwas_gc.txt`
  - MAGMA SNP p-values: `data/interim/magma_replication/*.pval.tsv`

**Exploratory arithmetic done here** (not a protocol test; assumes both betas are in SD units): the heterogeneity z between Savage and GenLang is (b1−b2)/√(se1²+se2²).
- rs13107325: z −2.80, p 0.005
- rs6778735: z −1.87, p 0.06
- rs3101338: z 1.64, p 0.10

## KDM5B (~22:05Z)

**Search terms**
- "KDM5B intellectual disability variants"
- `Kdm5b[tiab] AND (memory OR learning OR behavior)`
- `(Kdm5b OR Jarid1b OR Plu-1) AND (neonatal lethality OR embryonic OR knockout)`
- "KDM5B recessive developmental disorder 2018"
- Web: "GS-5801 KDM5 inhibitor hepatitis B ... CPI-455 KDOAM-25"
- Web: "Jarid1b knockout neonatal lethality Albert 2013"
- ClinicalTrials: intervention "GS-5801" (0 hits registered under that string)

**Local check.** rs10920444, the common index SNP next to KDM5B named by Wu 2025, has Davies p 0.84 and Savage p 0.50. There is no common cognition signal.

**Accepted**
- PMIDs 37231097, 30409806, 29276005, 39202393, 40657596, 23637629, 38575342, 39664113, 37788244, 39772748, 36477212
- Genebass doi:10.1016/j.xgen.2022.100168

**Rejected (with reason)**
- PMIDs 42736294, 42259546, 41508086, 41427248, 40908175, 40282252, 39263286: off-target (immunity, cancer, TCM, AML, SSCs, Kawasaki).
- PMIDs 42166402 and 41648108: Drosophila Kdm5 gut-microbiota/social behaviour. It is the ortholog, but the phenotype is not cognition; kept out of the table for brevity.
- PMID 35278764: frameshift plus an SCN-cluster deletion, so the phenotype is confounded.
- PMID 34573379 (a compound-heterozygous family) and PMID 30217758 (splice variants): redundant with DDG2P/OMIM.
- PMID 28720891: Saudi ASD trios, not specific.

## ANKRD12 (~22:09Z)

**Search terms**
- `ANKRD12[Title/Abstract]` (all 23 hits screened)
- Web: "ANKRD12 protein-truncating variants cognitive ability exome replication All of Us OR FinnGen OR SPARK 2025"

**Accepted**
- PMIDs 37231097, 39772748, 39511343, 39472661, 38177695, 38982111, 39031522, 39842675, 42238450 (BRaVa), 31291891, 31185953, 36428974
- Genebass

**Rejected**
- PMIDs 41580787 (stroke miRNA), 40281492 and 36923096 (ESCC signatures), 36216793 (HPV fusion), 35774514 (DLBCL), 33107222 (PDX), 39258138 (PD expression) and 38474122 (pig splicing): expression or marker studies with no causal or neural relevance.
- PMID 36440791: the same group's BD serum follow-up, redundant with 31291891.
- Web: ANKRD11/ANKRD17 case reports (paralogs; not transferable).

**Gap.** No non-UKB gene-level cognition replication and no DD de novo report were found. The DDD/Kaplanis tables were not queried in this session.

## RC3H2 (~22:13Z)

**Search terms**
- `(RC3H2 OR Roquin-2) AND (neuron* OR brain OR neurodevelopment* OR intellectual)` (3 hits)
- `RC3H2 OR roquin-2` in Title/Abstract (26 hits screened)
- Web: "RC3H2 de novo variant neurodevelopmental disorder" (no RC3H2-specific result)
- Web: "Roquin Rc3h1 Rc3h2 neurons brain knockout perinatal lethality"

**Accepted**
- PMIDs 37231097, 38141912, 23583643, 23583642, 26489670, 38729452, 41416953
- PMID 21844204 (Rc3h1 paralog lethality, via web)

**Rejected**
- PMIDs 41294801 (cardiac), 40687373 (ALS circRNA, RC3H2 not central), 40535770 (HCC doxorubicin GWAS), 39188927 (dermatitis network), 37326104 (ceRNA osteoporosis), 34931590 (curcumin Tfh), 32727592 (PDLSC ageing): off-target or low evidential value.

**Gap.** No neural study of Roquin-2 exists. Rc3h2 germline-knockout viability was not established in this session.

## CACNA1A (~22:16Z)

**Search terms**
- `CACNA1A[Title] AND (cognitive OR intellectual disability) AND (haploinsufficiency OR loss-of-function OR truncating)` (11 hits, all screened)
- ClinicalTrials: condition "CACNA1A OR episodic ataxia type 2 OR spinocerebellar ataxia type 6"
- ChEMBL target_search gene CACNA1A (CHEMBL4266; the complexes CHEMBL3988640 and CHEMBL2363032)

**Accepted**
- PMIDs 37231097, 25735478, 34127816, 39460936, 41699918, 31468518, 37555011, 35722745, 36063114, 34015490, 38681799
- PMID 23827678 (α1ACT; recalled and PMID-verified via esummary)
- Trials NCT07221292, NCT01543750 and NCT03701399

**Rejected**
- PMID 31574590: a Malan-syndrome 19p13 deletion including NFIX, so it is confounded by NFIX.
- Trials: DBS, stem-cell and natural-history trials are not relevant to the gene's pharmacology.

**Note.** 4-aminopyridine and acetazolamide are EA2 symptomatic treatments. 4-AP acts on K⁺ channels, not CaV2.1.

## NEGR1 (~22:19Z)

**Search terms**
- `Negr1[tiab] AND (knockout OR deficient OR mice) AND (behavior OR cognitive OR memory OR neurogenesis)` (30 hits; the top 15 were screened)
- `NEGR1[tiab] AND (deletion OR copy number) AND (obesity OR BMI OR intellectual)` (11 hits)
- `(rs3101339 OR rs3101336 OR rs2815752 OR rs1432639) AND NEGR1`
- `NEGR1[ti] AND (FGFR2 OR NPC2)`
- Web: "rs3101336 NEGR1 BMI Locke 2015 lead SNP 45-kb deletion"

**Local check.** Savage 2018 at rs3101339: allele a has z −7.76, so C is intelligence-increasing. Zhang 2025 calls C the MDD-risk, NEGR1-up allele. That is the dossier's main contradiction. I did not verify LD between rs3101339 and rs3101338, but their Savage directions are internally consistent with the rows.

**Accepted**
- PMIDs 29942086, 19079261, 23563609, 32375678, 40382479, 41588420, 39170714, 22844493, 32209393, 27617112, 36552158, 25072390, 30059965, 27940359

**Rejected**
- PMIDs 41914288, 41888955, 41545566, 41440084, 40886916, 40698360, 40388597, 39558356, 39349721: further Negr1-/- mouse phenotypes (stress, proteome, MK-801, isolation, testosterone, gut). Consistent with, and redundant to, the accepted knockout rows.
- PMIDs 37488273 (Lithuanian selection), 37058410 (adipose exercise), 33299884 (cancer survival), 28428959 (Mexican child CNV): off-target.
- PMID 33911383: a large 1p31 deletion including NFIA, so it is confounded.

## SLC39A8 (~22:23Z)

**Search terms**
- `rs13107325[tiab] OR (SLC39A8[tiab] AND (A391T OR Ala391Thr))` (62 hits; all titles screened via esummary)
- Abstracts fetched for 12
- PMC full text of PMID 36056013 (PMC9440106) grepped for behavioural results

**Local check.** Savage: T z −9.49. GenLang: T +0.0069 (p 0.74). G&C: C −0.0071 (p 0.056). The direction is consistent with the packet: C increases cognition.

**Accepted**
- PMIDs 29844566, 29942086, 40530585 (published version of medRxiv 39371177), 26637978, 26637979, 32897876, 35260802, 36056013, 33608496, 38821503, 27182965, 26006263, 30649180, 33790950, 33139556, 40963256, 40956895
- Internal: `research/sprint5/math_audit.md`

**Rejected**
- Duplicate: PMID 39371177, the medRxiv version of 40530585.
- Off-target for cognition, used only for the pleiotropy summary: PMIDs 41349715, 41097903, 41078934, 41033407, 36376028, 36292594, 35273636, 34703283, 34068824, 32247823, 31513097, 30301978.
- PMIDs 30619481 and 31233999 (child Mn and neurodevelopment): not fully read (the abstract was truncated in the fetch). Potentially relevant for the direction in children. **Open item.**
- PMID 41955304 (microbiome QTL in PD models): not neural cognition.

## NT5DC2 (~22:27Z)

**Search terms**
- `NT5DC2[tiab]` (about 50 hits screened; about 30 are oncology biomarker papers)
- `(GLT8D1 OR GNL3 OR NEK4 OR SFMBT1 OR ITIH3) AND (schizophrenia OR bipolar OR cognit* OR 3p21.1)` (40 hits screened)

**Local checks**
- `evidence_units.parquet`: NT5DC2 has 5 E2G units, and STAB1/UQCC5 share 3 of them.
- L2G features: eQTL/sQTL H4 is about 0.99 for both NT5DC2 and STAB1.
- Sumstats: see the header.

**Accepted**
- PMIDs 42069759, 31279527, 32778969, 38382359, 40751758, 33462198, 39362218, 29483533, 34978167, 32826963, 31723243, 25136889
- Oncology PMIDs 32382041 and 30978441, cited as a class only

**Rejected**
- Most NT5DC2 oncology prognostic-signature papers (e.g. 40591089, 40465746, 37800836, 37576396, 36820551, 35047040): non-neural.
- NEK4 drug-target MR papers (39950180, 38869147) and the NEK4 circadian mouse paper (39448584): relevant to an alternative gene, but outside this gene's dossier. They are noted as NEK4 support in spirit only.
- PMID 42771993 (cataract GWAS): off-target.

## Cross-gene flags (for the lead, not acted on)

1. **KDM5B.** `DEVELOPMENTAL_CAUSAL_ONLY_flag = true` is contradicted by adult hippocampal knockdown causing memory deficits (Pérez-Sisqués 2024, mouse). This is a flag only; the class stands.
2. **RC3H2.** The VNR estimate rests on 16 carriers. The winner's-curse correction has not been done.
3. **CACNA1A.** The exome-wide status depends on the per-phenotype threshold (a known discrepancy, already recorded).
4. **NEGR1.** The direction label conflicts with the functional literature (Zhang 2025), and dosage is inverted-U in mouse.
5. **SLC39A8.** The frozen rule cannot credit a PIP ≈ 1 missense without a second class. Separately, the non-UKB lineages are heterogeneous (GenLang p ≈ 0.005). There is no reason to promote it.
6. **NT5DC2.** The label should not be read as a gene call. Rahman 2026 shares data with our G&C lineage.
