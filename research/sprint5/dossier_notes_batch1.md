# Dossier notes — literature red-team batch 1

Genes: KIFC2, DNPH1, TUFM, DCC, RHEBL1, RPS26, SUOX
Agent: literature red-team subagent. Scope: target characterisation and evidence appraisal only. We made no compound design,
dosing or intervention suggestions.
Session window (UTC): about 2026-09-23T21:55Z to 2026-09-23T22:40Z. The per-gene times below mark when each gene's search block ran.
Tools: PubMed E-utilities (MCP), WebSearch, ChEMBL target search (MCP), ClinicalTrials.gov (MCP), and local repo files. We did not
query IMPC, gnomAD, GWAS Catalog or OMIM directly. OMIM and ClinGen facts come from web-search snippets or from knowledge
confirmed by PubMed abstracts.

Internal inputs read (not modified): `data/sprint5/dossier_evidence_packets.json`, `reports/sprint5/causal_gene_evidence_matrix.csv`,
`reports/sprint5/opentargets_refresh.csv`, `reports/sprint4/joint_gene_tissue_finemapping.csv`,
`reports/sprint5/cell_specific_directionality.csv`, `reports/sprint5/brainscope_variant_summary.csv`,
`reports/sprint5/brainscope_variant_lookup.csv`, `data/sprint5/evidence_units.parquet`, `data/sprint5/ot_l2g_features.parquet`,
`research/sprint5/protocol.md`, `research/sprint5/protocol_rules.json`.

Cross-cutting observation: the packet reports FOCUS primary PIP 0.0 for KIFC2, DNPH1, TUFM and DCC, but
`joint_gene_tissue_finemapping.csv` has no rows for their loci (L65265, L55168, L51327, L1630). The dossiers read these values as
"not evaluated", not as evidence against the gene.

---

## KIFC2 (~22:00Z)
- Searches: PubMed "KIFC2 kinesin" (20 hits, 15 reviewed); WebSearch "KIFC2 FOXH1 8q24.3 GWAS cognitive ability OR intelligence OR educational attainment locus"; PubMed "Saito N[Author] AND Hirokawa N[Author] AND KIFC2".
- Accepted: PMID 9115736 (neuronal dendritic MVB motor); 11259594 (knockout normal, the key contradiction); 32294442 (knockdown dendrite defects); 42511647 (microglial KIFC2 and pain-related cognitive deficit; kept as MECHANISTIC only, since it is single-study and disease-model); cancer papers 37716704, 40299549, 38658471, 37904433 (DISEASE_ONLY context); internal OT/matrix ZFTRAF1 rows.
- Rejected: 40299423 (KIFC3, wrong gene); 32084403 (KIFC3); 23460941 (dynein mutant expression survey, not informative); 9858832 (KIF5A mapping); 12759371 and 15181154 (liver endocytic vesicles, only tangential; 15181154 cited only for Rab4 regulation); 41520472 (palmitoylation bioinformatics).
- No GWAS paper naming KIFC2 for cognition was found.

## DNPH1 (~22:03Z)
- Searches: PubMed "DNPH1 OR RCL deoxynucleoside hydrolase" (47); PubMed "(DNPH1 OR Rcl) AND (brain OR neuron OR knockout OR cognition OR schizophrenia OR pQTL)" (72; the "RC" synonym expansion polluted this with cannabis and other off-topic hits, all rejected); WebSearch Fugger 2021; WebSearch TTBK1.
- Accepted: 33833118 (function); 41231215 (mechanism); 41194588, 41531952, 41183227 (inhibitors and PROTACs, as pharmacology facts); 41847111, 42772593 (oncology); 41571964 (UKB AD × air pollution; NON-INDEPENDENT); 42145630, 41367007, 41398839 (plasma-protein MR/coloc mentions, verified in abstracts; used only in the pleiotropy section); TTBK1 web sources (OMIM *619415, PMC7684928) as the alternative gene.
- Rejected: all "RC"-polluted hits (42512504, 41923624, 41895140, 41688423, 41582809, 40874463, 40775197, 40532064, 40437758, 40160459); 40807411, 39941055 (not specific); 39933395 (duplicate MR context).
- No DNPH1 neural or behavioural study was found.

## TUFM (~22:08Z)
- Searches: PubMed "TUFM mitochondrial elongation factor Tu deficiency OR TUFM brain" (40); PubMed "TUFM[Title] OR 'combined oxidative phosphorylation deficiency 4'" (42, 20 reviewed); PubMed "TUFM AND (GWAS OR eQTL OR TWAS OR Mendelian randomization) AND (schizophrenia OR cognitive OR intelligence OR obesity OR Parkinson)" (11); WebSearch "distal 16p11.2 deletion SH2B1 ATXN2L TUFM ...".
- Accepted: 38434247 (SH2B1 fluid intelligence, the key alternative gene); 25955518 (LD block width); 39896714 (UKB, NON-INDEPENDENT); 17160893 (COXPD4); 41866827; 26449484 and 34494379 (multi-gene eQTL/meQTL); 41904133 (review); 39496783 (TBI); 37461298 (POI); ClinGen ISCA-37486.
- Rejected: virology and cancer mechanism papers (42106683, 41935318, 41929492, 41736317, 38084826, 39189526, 41165841, 40246816, 40585970, 42082827), which are not neural or genetic; 41071439 (drug neuroprotection study, not target genetics); 26771213, 24956270, 21779089, 29854750 (peripheral eQTL/obesity, redundant).
- Internal finding: brainSCOPE credible variants tag SH2B1 (71 SIGNIFICANT rows, all HIGHER) and NPIPB9. TUFM is not in any matrix. SH2B1 has 0 classes in the matrix.

## DCC (~22:12Z)
- Searches: PubMed "DCC[Title] AND (mirror movements OR split-brain OR agenesis corpus callosum OR synaptic plasticity adult OR depression OR prefrontal adolescence)" (56; 25 reviewed); PubMed author-targeted query for the foundational papers (8); WebSearch "DCC locus pleiotropic GWAS ... 18q21.2 cross-disorder"; ClinicalTrials.gov intervention "NP137 OR netrin-1 antibody" (8 trials).
- Accepted: 20431009, 28250456, 28250454, 29068161, 36889039, 33209984 (Mendelian lineage); 23291093 (adult synaptic, SUPPORTING mechanistic); 27773352, 33384174, 31659271 (psychiatric/dopamine); PGC-CDG 2019 (doi 10.1016/j.cell.2019.11.020; PMC7077032); 32184385; 35115383; 39353037 (WRC mechanism); NP137 trials as facts.
- Rejected: DCC-acronym collisions (39487080 cystic fibrosis "Daily Care Check-In"; 35952931 "Depression Cohort in China"); herbal or traditional-medicine pathway papers (40058944, 39476759, 37934907), which are low-quality and irrelevant to target genetics; 41659277 (no abstract; not assessed).
- Note: 2 NP137 trials in the listing were TERMINATED or UNKNOWN; only three are cited.

## RHEBL1 (~22:17Z)
- Searches: PubMed "RHEBL1 OR Rheb2 OR 'Rheb like 1'" (47; 20 reviewed); PubMed "dendrin DDN dendritic spine OR PFKM brain OR 12q13.12 cognitive GWAS" (too broad at 3,565 hits; not used); WebSearch "Rhebl1 knockout mice phenotype mTORC1 brain ..."; PubMed "Zou J Rheb1 mTORC1 myelination".
- Accepted: 42386913 (temperament GWAS, RHEBL1 cortex eQTL coloc PP 0.93); 42393086 (reading/ADHD T-SEM; RHEBL1 and LMBR1L); 33263727 (bipolar, Han Chinese); 21238928 (Rheb1 not Rheb2 essential; CONTRADICTING); 32518628, 38338768 (reviews); 40369227, 42332182 (oncology); 33574130 (SmgGDS).
- Rejected: 36297114 (DASH diet GWAS; RHEBL1 not in the abstract, so removed after verification); 36944699, 36386821, 34262492 (bioinformatic biomarker lists); 40159627, 35115527 (muscle TAZ); 40121052, 39122135, 38538289 (non-neural cell mechanisms); 36579460 (IRF3 screen).
- Not done: LD between rs7969091 (published) and rs10875914 (our lead). This is listed as a next computation.

## RPS26 (~22:22Z)
- Searches: PubMed "RPS26 AND (eQTL OR rs1131017 OR colocalization OR trans-eQTL OR 'type 1 diabetes')" (23; 20 reviewed); PubMed "RPS26 Diamond-Blackfan anemia OR RPS26 Kozak translation OR RPS26 neuron" (34; 12 reviewed); PubMed Ferretti/Kozak.
- Accepted: 38812329 (RPS26 = 32.9% of RP GWAS–eQTL pairs; the key contradiction); 23900168; 38453145; 28248954; 37072791; 33664499; 39510315; 40739630; 42386713; 20116044; 28759050.
- Rejected: 41915616, 38526030, 38457382, 39719581, 40245477, 41350606, 40445995 (further pleiotropy/MR listings, redundant with 38812329; 40445995 is kept in the SUOX dossier); 22685416 (older brain eGWAS, redundant); 41303667 (PCOS locus; gene names stripped from the abstract, not assessable); 34704236, 38041572 (redundant).

## SUOX (~22:28Z)
- Searches: PubMed "(isolated sulfite oxidase deficiency SUOX) OR (RPS26 Diamond-Blackfan Doherty 2010)" (44; 9 reviewed); ChEMBL target search SUOX (0 human records returned); local `ot_l2g_features.parquet` to decompose the Open Targets pQTL feature.
- Accepted: 28980090, 12112661, 36303223 (ISOD lineage); 33664499, 40445995 (co-nomination, NON-INDEPENDENT); 42200276 (vascular mechanism); Open Targets pQTL-coloc H4 0.82–0.95 (internal file).
- Rejected: 39676698 (no abstract, late-onset case report, redundant); 34025712, 36709936 (case reports, redundant with the review).
- Fact recorded without a PubMed fetch: fosdenopterin approval for MoCD type A (general regulatory knowledge; not SUOX-targeted).

---

## Flags for the coordinator (no files outside scope were changed)
1. **TUFM / L51327:** our own brainSCOPE data favour SH2B1 (and NPIPB9), not TUFM, and Du 2023 supplies SH2B1 cognition-relevant mouse genetics. The label is already UNRESOLVED; but rank-E #1 should be presented as a locus priority, not TUFM as a gene.
2. **RHEBL1 / L7009:** escapes CONTESTED by 0.02 (FOCUS 0.22 vs PFKM 0.77; threshold < 0.2). Open Targets now assigns DDN, and DDN holds the only E2G link (0.994). The rank-C #1 direction belongs to a fragile gene assignment.
3. **SUOX / L319:** the Open Targets pQTL-coloc (H4 up to 0.95) is a molecular layer where SUOX has evidence and RPS26 does not. The passenger label is still defensible (FOCUS 0.015; locus discordant), but the disagreement should be recorded.
4. **KIFC2 and DNPH1:** MODERATE calls rest on unreplicated single-lineage evidence at L3 loci. ZFTRAF1 has more eQTL rows than KIFC2 (2 vs 1), and TTBK1 is a neuron-specific alternative to DNPH1. Neither call is contradicted by literature; neither is supported by it.
5. **FOCUS 0.0 in packets** for loci that were never run should probably read NA rather than 0.0.
