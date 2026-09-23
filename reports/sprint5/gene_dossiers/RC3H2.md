# RC3H2 (Roquin-2): literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `CODING_CAUSAL_LOF_ONLY` (DEVELOPMENTAL flag false; expression class `DEVELOPMENTAL`).**
- This is the most fragile rare-coding gene in the batch. The whole cognition claim rests on **16 UKB PTV carriers** for VNR, with a very large effect (−1.13 SD).
- EDU is only nominal (p 0.016) and RT is null (p 0.43). There is no Mendelian neurodevelopmental disease, and the RC3H2 literature is almost entirely immunological.
- The signal is compatible with a real effect, and equally with winner's-curse inflation in a tiny carrier set.

## 2. Our computed evidence (packet; unchanged)

| Item | Value |
|---|---|
| Locus | none. Panel B. rank_B 20, rank_E 8, rank_D 1 (P2). |
| GTEx adult-brain TPM | 5.97. Developmental class `DEVELOPMENTAL`. |
| Chen 2023 PTV VNR/FI | beta −1.126 (SE 0.23), p 9.32e-7, **16 carriers**, exome-wide |
| Chen 2023 PTV EDU | beta −0.337 (SE 0.14), p 0.016, 34 carriers |
| Chen 2023 PTV RT | beta +0.132 (SE 0.168), p 0.43, 34 carriers |
| Genebass pLoF FI | burden p 1.56e-6 (suggestive; same UKB) |
| Replication | Not at gene level. Only the 8-gene set replicated. |
| Disease | none in DDG2P |
| Modifiability | RING E3 ligase and ROQ/HEPN RNA-binding domains; P-bodies. No pocket or probes. LOEUF 0.309 (constrained). |

## 3. Three separate questions

- **A. Causal cognition gene? WEAKLY SUPPORTED (UKB LoF only).**
  - One phenotype in 16 carriers is exome-wide. The other two phenotypes are nominal or null.
  - There is no disease evidence.
  - Constraint (LOEUF 0.31) is consistent with dosage sensitivity, but that is indirect.
- **B. Natural high-cognition gene? NOT SUPPORTED.** No common locus exists.
- **C. Adult-modifiable? NOT TESTABLE.** No neural perturbation study of Rc3h2 exists in any species.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| Rare PTV → RC3H2 LoF | EVIDENCED (assumed) | PTV burden |
| RC3H2 → neural mRNA targets | MISSING | Constitutive-decay-element (CDE) targets are characterised in T cells, macrophages and mast cells, not neurons |
| Cell type | MISSING | Expressed in brain (TPM ~6). No neural cell-type function studied. |
| Direction LoF → lower VNR | EVIDENCED in 16 UKB carriers | Chen 2023 |
| Independence from immune/inflammatory route | MISSING | Paralog-redundant immune brake (Roquin-1/2) |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Chen CY 2023 Nat Genet, PMID 37231097 | PTV and VNR exome-wide (16 carriers) | SUPPORTING | [UKB-shared A] |
| Karczewski 2022 Genebass, doi:10.1016/j.xgen.2022.100168 | pLoF FI p 1.6e-6 | NON-INDEPENDENT | [A] |
| Wilkerson 2023 Biol Psychiatry, PMID 38141912, doi:10.1016/j.biopsych.2023.12.008 | RC3H2 is one of 19 genes enriched for uncommon variants in suicide attempt (Army STARRS WGS, n = 13,584) | DISEASE_ONLY | **Independent of UKB**. A psychiatric phenotype, not cognition. Single study. |
| Vogel 2013 Immunity, PMID 23583643, doi:10.1016/j.immuni.2012.12.004 | Roquin-1/2 redundantly repress Icos/Ox40. No unique Roquin-2 role in T cells. | MECHANISTIC_ONLY | Paralog redundancy |
| Pratama 2013 Immunity, PMID 23583642 | Roquin-2 compensates for Roquin-1 in repressing ICOS and TNF | MECHANISTIC_ONLY | Immune |
| Zhang 2015 Sci Rep, PMID 26489670, doi:10.1038/srep15660 | Crystal structures of the RC3H2 ROQ/HEPN RNA-binding region. E3 activity cross-talks with RNA binding. | MECHANISTIC_ONLY | Structure exists (RNA-binding region) |
| Hirata 2024 Free Radic Biol Med, PMID 38729452 | Roquin-2 promotes oxidative-stress cell death by degrading TAK1 | MECHANISTIC_ONLY | Non-neural |
| Heger 2025 Eur J Immunol, PMID 41416953 | ROQUIN paralogs are required for serosal mast cells | MECHANISTIC_ONLY | Immune |

**Forward citations and alternatives:**
- I found no RC3H2 neurodevelopmental case series and no de novo enrichment report.
- Rc3h1 (the paralog) germline knockout is perinatal-lethal in mouse (Bertossi 2011, PMID 21844204 via web). I did not establish Rc3h2 germline lethality in this session.

## 6. Modifiability characterisation (facts only)

- **Protein:** a cytoplasmic RNA-binding protein and RING-type E3 ubiquitin ligase (Roquin-2). It binds CDE stem-loops in 3′UTRs and promotes deadenylation and decay (targets include ICOS, TNF, OX40, NFKBIZ and IER3).
- **Structure:** crystal structures of the RNA-binding ROQ/HEPN region exist (PMID 26489670).
- **Pockets, probes, drugs, clinical programmes:** none.
- **Activity regulation:** MALT1 protease cleaves Roquins on antigen-receptor stimulation. This is an endogenous regulator in immune cells.
- **Companies or patents:** none found for neural indications.

## 7. Pleiotropy and safety

- Roquin-1/2 are posttranscriptional brakes on T follicular helper (Tfh) cell differentiation and inflammation. Combined loss causes T-cell activation and autoimmune-prone phenotypes in mouse.
- They also have roles in mast cells, macrophage TNF and cardiac remodelling.
- High constraint (LOEUF 0.31).
- Any change in RC3H2 dosage would have an immune-tolerance liability. That is a characterisation fact, not a recommendation.

## 8. Largest contradiction

An exome-wide VNR effect of −1.13 SD in 16 carriers sits beside a null RT result (34 carriers) and a nominal EDU result, with no DD/ID disease link. For the other seven Chen genes, EDU and RT generally move together. For RC3H2 the phenotype pattern is internally inconsistent, which is typical of winner's-curse inflation at a small carrier count.

## 9. Missing arrow and single best next computation

- **Missing arrow:** any UKB-independent LoF–cognition evidence, and any neural mechanism.
- **Best next computation:**
  - Apply a conditional-likelihood winner's-curse correction (Zhong & Prentice style, at Chen's per-phenotype threshold 4.2e-6) to the 16-carrier VNR estimate.
  - Report the corrected effect and interval next to EDU and RT.
  - Pull the RC3H2 de novo PTV and missense counts and DeNovoWEST P from the Kaplanis 2020 DDD supplementary tables.
