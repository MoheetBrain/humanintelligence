# Sprint 5: rare-coding and positive-dosage research log

Branch: `sprint-5/causal-cognition-gene-resolution`. Session date: 2026-09-23 (UTC). All downloads are listed in
`data/raw/sprint5/rare_coding/PROVENANCE.json` with URL, UTC time, bytes and sha256. No accounts were created, nobody logged in, and no terms were accepted.

Outputs:
- `reports/sprint5/rare_coding_evidence.csv` has 50 rows, one per (gene or set, study, phenotype).
- `reports/sprint5/cnv_positive_dosage.csv` has 19 rows.
- `data/sprint5/rare_coding_gene_sets.json` holds the gene sets for the convergence tests.

Standing rules applied throughout:
- Loss-of-function (LoF) impairment evidence is never recoded as enhancement.
- Educational attainment (EA) is labelled `EA_PROXY`.
- Every gene-level exome result below was discovered in UK Biobank (UKB). Later UKB re-analyses (Genebass, Wu 2025) use the same people, so they confirm a result but do not replicate it.

---

## S1. 2026-09-23T21:05Z: Chen et al. 2023, verify the eight genes
- **Question:** Which genes are exome-wide significant, for which phenotype, in which direction, with how many carriers, and did they replicate?
- **Search:** EuropePMC title search, which returned PMID 37231097, PMC10260403 and doi 10.1038/s41588-023-01398-8. I downloaded the full-text XML and the supplementary zip (30 MB, moved to interim). The xlsx files were parsed with zipfile+xml because openpyxl is not installed in the .venv.
- **Sources inspected:**
  - Main-text Table 1
  - Supplementary tables S3 (FDR genes), S5 (carriers), S8 (replication) and S23 (Genebass comparison)
- **Accepted:**
  - The eight genes are confirmed: ADGRB2, KDM5B, GIGYF1, ANKRD12, SLC8A1, RC3H2, CACNA1A and BCAS3.
  - The test is PTV burden only (MAF<1e-5) with regenie. Discovery is UKB EUR: 393,758 (EDU), 394,600 (RT) and 159,026 (VNR).
  - Significance by phenotype:
    - EDU only (EA_PROXY-only genes): ADGRB2, GIGYF1, SLC8A1, BCAS3.
    - VNR: ANKRD12, RC3H2, CACNA1A.
    - All three phenotypes (EDU, RT and VNR): KDM5B.
  - Every effect is deleterious: carriers have lower EDU and VNR and slower RT.
- **Flags found by reading the numbers, not the prose:**
  - BCAS3 (EDU p=1.99e-6) passes only the per-phenotype Bonferroni threshold (3.17e-6). It fails the study-wide threshold (1.15e-6) and is not flagged "a" in Table 1.
  - CACNA1A VNR has p=1.33e-6 but IS flagged "a". That p-value is above the stated 1.15e-6, so this is an internal inconsistency. The gene is retained on the per-phenotype VNR threshold (4.20e-6).
  - FDR-only genes: NDUFA6 (EDU), ARHGEF7 (VNR), C11orf94 (VNR), KIF26A (VNR) and MAP1A (EDU).
  - **C11orf94 PTV carriers score HIGHER on VNR** (beta=+1.204, n=11, FDR Q=0.028). RT points the same way, faster (beta −0.474, p=0.046). This is the only positive-direction gene-level signal in the paper. It is LoF, FDR-only, and not supported in Genebass (FI pLoF burden p=0.36).
- **Replication:**
  - Gene level: nothing significant outside UKB.
  - Set level: the 8-gene PTV set replicated in SUPER-Finland for EDU (β=−0.424, p=0.0021), academic performance (p=0.0125) and DD/ID (OR 4.8). It also replicated in NFID for DD/ID (OR 4.97, p=3.6e-5).
  - Single genes in NFID DD/ID: KDM5B OR 4.78 (p=0.02) and GIGYF1 OR 6.15 (p=0.011), both nominal.
  - MGBB EDU: p=0.50, with only 8 carriers.
- **Conclusion:**
  - The genes with a direct cognitive measure (not EA) are KDM5B, ANKRD12, RC3H2 and CACNA1A.
  - All of them are UKB discoveries with LoF-to-worse direction.
  - None of this is evidence of gain of function.
- **Uncertainty:**
  - The CACNA1A threshold inconsistency.
  - Chen tested PTVs only at gene level, so there is no damaging-missense gene discovery.
- **Next:** find newer exome studies.

## S2. 21:07Z: newer exome/WGS studies of cognition (2023–2026)
- **Searches:**
  - PubMed MCP, three queries: exome / rare variant / PTV × cognition / EA / intelligence / reaction time × UKB/biobank, 2021–2026, with title-field restriction.
  - WebSearch: "rare coding variants cognitive function exome 2025 … All of Us/MVP/deCODE"; "exome-wide association fluid intelligence 2024/2025"; "deCODE 2024/2025 rare variants cognitive ability".
- **Accepted:**
  - **Wu XR et al. 2025 PNAS** (PMID 39772748). UKB White British. EduYears hits: GIGYF1 (pLoF, p=2.2e-10), KDM5B (pLoF+missense, p=3.3e-9) and ADGRB2 (pLoF, p=6.8e-9). Income and TDI hits include ANKRD12 and GIGYF1. Same UKB participants as Chen, so this is not independent. EA_PROXY and SES only.
  - **Chakraborty & Kahali 2023 HGG Adv** (PMID 37305557). UKB, 157,067. APOC1 and LRP1 come from a candidate-gene SKAT test over all variants, including common ones. APOC1 is ~5 kb from APOE. Recorded as a weak candidate association. I did not adopt the claimed "514 exome-wide gene hits": they use an all-variant SKAT and were not parsed.
  - **Kingdom et al. 2024 Nat Genet** (PMID 38637616). Set-level only: 599 dominant DDG2P genes, additive burden, lower fluid intelligence and SES.
  - **Mol Psychiatry 2026** (PMID 41963674). Set-level: SCZ genes vs g, UKB 76,783.
  - **Malawsky et al. 2026 Nat Hum Behav** (PMID 42432050). ALSPAC, **not UKB**, 6,495 children. The pLoF-burden association with cognition weakens with age. Set-level only.
- **Rejected or not relevant:**
  - BRaVa 2026 (medRxiv; 1.2M across 10 biobanks). Clinical endpoints plus 11 quantitative traits, apparently with no cognitive trait. Its ANKRD12 finding is for asthma/COPD, which I recorded as pleiotropy.
  - Weiner 2023 Nature (PMID 36755099). EuropePMC returned no full text, and I did not pursue gene-level cognition hits.
  - Retina, AD, alcohol and loneliness exome papers were off-target. The alcohol and loneliness papers do re-hit GIGYF1 and ANKRD12, which again points to pleiotropy.
  - The Long Life Family Study "rare protective variants" item (Innov Aging 2025) is a conference abstract (GWAS, 3 variants, no gene-level exome). I noted it and did not include it.
  - I found no deCODE, All of Us or MVP exome or WGS gene-level cognition paper through 2026-09-23. That is a negative search result, not proof that none exist.
- **Next:** check Genebass directly.

## S3. 21:10Z: Genebass (open API, CC BY 4.0)
- **Access:**
  - The bundle JS exposed `https://main.genebass.org/api/...`.
  - The terms page says the data are "released openly and publicly" under CC BY 4.0. No login and no click-through.
  - The Genebass paper's thresholds are SKAT-O 2.5e-7 and burden 6.7e-7 (Karczewski 2022, PMC9903662).
- **Phenotypes available:**
  - 20016 fluid intelligence (n=128,302)
  - 20191 online fluid intelligence (n=100,900)
  - 20023 reaction time (n=392,194)
  - 20018 prospective memory (n=131,007)
  - No EA phenotype is available.
- **Results:**
  - ANKRD12 FI pLoF: 5e-14.
  - KDM5B RT pLoF: 1e-12, slower.
  - Suggestive: KDM5B, RC3H2 and CACNA1A for FI.
  - New significant hits not reported by Chen:
    - ADAMTS6: missense, FI, burden 2.5e-7, lower.
    - BRPF1: pLoF, prospective memory.
    - ASAP1: SKAT-O only, prospective memory.
    - NACC1: missense, prospective memory. NACC1 is a DDG2P gene whose disease mechanism is gain of function.
    - AC011448.1: missense, RT, in the pleiotropic 19p13.11 region. Likely an LD artefact.
  - The UKB showcase confirms that 20018 uses data-coding 18 (0 = not recalled, 1 = correct first try, 2 = correct second try). That coding is non-monotone, so **the direction of prospective-memory hits cannot be interpreted.**
- **Conclusion:** Genebass adds no independent replication (same UKB participants). The new hits are single-cohort and have caveats, so they are classed as suggestive.

## S4. 21:13Z: 2q12.3 duplication audit
- **Sources:**
  - The repo already holds the snapshot PMC11701252.xml. I also downloaded its supplement: Table S1, "CNV-GWAS details (FDR)".
  - EuropePMC forward citations of PMID 39667348: 5 items. Two were read in full: Kazem 2026 Nat Commun (UKB plus All of Us functional burden) and Poulain 2025 Transl Psychiatry (UKB CNVs, sleep and cognition).
  - WebSearch "2q12.3 duplication higher cognitive replication".
- **Findings:**
  - Table S1 gene-level results:
    - SOWAHC: z=+0.434, p=7.58e-3, FDR q=0.0373, n=36.
    - SEPT10: z=+0.496, p=3.46e-3, q=0.0172, n=33.
    - EDAR and SH3RF3: z=+0.460, p=8.63e-3, q=0.0418, n=31.
  - It is the **only positive-effect CNV** among the 13 FDR-significant CNVs. The other six duplications (1q21.1 TAR, 15q13.3, 16p13.11, 16p11.2, 17q12, 22q11.2) all lower cognition.
  - **Correction to the atlas:** the atlas says no corrected p-value was found. Table S1 does report FDR q values of 0.017–0.042. The FDR is lenient, though, because every gene inside a large pathogenic CNV counts as its own test and those tests are highly correlated. The locus is still not Bonferroni-significant (8.4e-5).
  - UKB supplies 238,176 of the 258,292 people (92%). The post-hoc t-test was run in UKB White British only.
  - **Replication: none found.** Neither citing paper mentions 2q12.3, EDAR, SH3RF3, SEPT10 or SOWAHC.
  - Triplosensitivity, from Collins 2022 pTriplo (Zenodo 6347673): EDAR 0.197, SH3RF3 0.595, **SEPT10 0.983**, SOWAHC 0.343. This is the metric the atlas said it lacked. SEPT10's high pTriplo predicts that duplication is not tolerated, which is in tension with a benefit. It is a model prediction, not cognition data.
  - ClinGen: all four genes remain uncurated (checked against the local 2026-09-22 file).
  - Loss-of-function evidence for the genes: EDAR LoF causes hypohidrotic ectodermal dysplasia (DDG2P, definitive), and Sh3rf3 knockout mice show autism-like behaviour (Mol Psychiatry 2025/26). Neither says anything about the benefit of a duplication.
  - Genebass coding tests of all four genes against FI and RT: all p>0.01.
- **Verdict:** NOMINAL_UNREPLICATED.

## S5. 21:15Z: CNV–cognition population studies
- **Search:** PubMed title query for CNV × cognition, IQ or EA (2013–2026), which returned 37 hits. I also read the full texts of Kendall 2019, Saarentaus 2021, Zaks 2025, Auwerx 2022, the 22q11.2 AJHG 2023 paper and the UKB 470k WGS CNV PheWAS (Nature 2026). Huguet 2018 and 2021, Mollon 2023 and Stefansson 2014 were read as abstracts only.
- **Findings:**
  - No study except Huguet 2024 reports a duplication associated with higher cognition.
  - Huguet 2021: duplicating LoF-intolerant genes costs about 0.8 IQ points per gene.
  - Kazem 2026: most dosage responses are non-monotonic, with deletions and duplications harmful in the same direction. Duplication effects replicate poorly between UKB and All of Us (r=0.42).
  - Poulain 2025: the only positive result is a **ZNF92 deletion** (β=+0.08, p=8.3e-3, UKB, nominal). It is a loss of dosage, not a gain.
  - The UKB 470k WGS CNV PheWAS has no cognitive traits in its text.
  - I found no deCODE 2024 CNV–cognition paper. Only Stefansson 2014 was found.
- **Not inspected:** "The impact of rare pathogenic CNVs is exacerbated by assortative mating" (medRxiv 2025).

## S6. 21:16Z: RIMS1, protective and gain-of-function variants
- **Sources:**
  - PubMed: "RIMS1 AND cognition…" and a positive-cognition/GoF query.
  - EuropePMC forward citations of Sisodiya 2007 (PMID 17237123): 25 items.
- **Findings:**
  - **Martin-Gutierrez 2022 IOVS (PMID 35947379)** found the CORD7 retinal dystrophy fully explained by co-inherited PROM1 p.Arg373Cys. One affected member lacks the RIMS1 variant. The RIMS1 p.Arg820His carrier frequency is above 1 in 5,000 in Europeans. The claim that this RIMS1 variant enhances cognition therefore rests on one kindred and is confounded.
  - Paul 2022 Brain gives Drosophila mechanistic plausibility only.
  - The variant maps (Ensembl) to GRCh38 6:72251007 G>A. In Genebass that site has AN=15,628 and AC=0, so it is poorly captured and **a population test was blocked**.
  - CRB1 retinopathy with "enhanced memory" (Wright 2024) is a small clinical sample with a visual-impairment confound, and the variants are LoF.
  - APP A673T, APOE Christchurch and RELN-COLBOS protect against dementia; they do not enhance cognition. APP *duplication* is pathogenic (ClinGen TS=3).
  - KL-VS: the population study (Mueller 2021, n=1,812) was null or slightly negative, so the verdict is CONTRADICTED.

## S7. 21:19Z: DDG2P
- The Gene2Phenotype DD panel CSV is at `https://www.ebi.ac.uk/gene2phenotype/api/panel/DD/download/` and was retrieved openly (2,866 records). The old `/downloads/DDG2P.csv.gz` URL now returns an HTML page.
- 2,005 genes are rated definitive or strong.
- 877 of those carry an explicitly listed ID or global-developmental-delay HPO term. HPO descendants were not expanded, so this is an undercount.
- Overlaps with the cognition gene sets:
  - Both the definitive/strong list and the ID-term list: KDM5B, CACNA1A, BRPF1, NACC1.
  - Definitive/strong list only: BCAS3, NDUFA6.

## Blockers
- **AZ PheWAS portal:** it states that users agree to its terms of use, so it was not accessed. Its UKB data would not be independent of UKB anyway.
- **openpyxl** is missing from the .venv. Worked around with a zipfile+xml parser.
- **RIMS1 p.Arg820His** cannot be tested in Genebass (site barely captured).
- **Weiner 2023:** full text not retrievable from EuropePMC.
- **Chakraborty & Kahali 2023:** supplementary tables not parsed.
- **Huguet 2024:** per-cohort carrier breakdown for 2q12.3 not found in the text or Table S1.

## Remaining uncertainty and next searches
1. Test the 2q12.3 duplication outside UKB. The candidates are All of Us CNV calls (Kazem 2026 used them; access requires registration, so it is out of scope here), and Generation Scotland and CARTaGENE, whose per-cohort z values are in Huguet Fig. 1G and were not extracted.
2. Look for a non-UKB exome study of cognition, for example Finnish (FinnGen WES is not public), MVP or All of Us. None was found.
3. C11orf94 is a positive-direction LoF signal with 11 carriers. It needs any independent cohort.
