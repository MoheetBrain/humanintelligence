# KDM5B: literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC) by a literature red-team subagent. This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. Loss-of-function (LoF) evidence is never read as evidence that more of the gene would help.

## 1. Verdict

**Class: `CODING_CAUSAL_LOF_ONLY`, with `DEVELOPMENTAL_CAUSAL_ONLY_flag = true`.** This is the strongest rare-coding cognition gene in the batch. PTV carriers in UK Biobank are worse on education, reaction time and verbal-numerical reasoning (VNR), and there is an established recessive intellectual-disability syndrome, so the case that "LoF impairs cognition" is solid. Nothing supports a natural high-cognition allele or any adult direction other than LoF. The literature also partly contradicts our developmental-only flag, because knocking the gene down in adult mouse hippocampus impairs memory.

## 2. Our computed evidence (from `dossier_evidence_packets.json`; numbers unchanged)

| Item | Value |
|---|---|
| Locus | none (no common cognition locus). Panel B only. |
| rank_B / rank_E / rank_D | 19 / 7 / 1 (P2) |
| GTEx adult-brain median TPM | 3.50. Developmental class `PRENATAL_DOMINANT`. |
| Chen 2023 PTV, EDU (EA proxy) | beta −0.307 (SE 0.057), p 8.68e-8, 204 carriers, exome-wide |
| Chen 2023 PTV, reaction time | beta +0.447 (SE 0.069), p 9.6e-11, 201 carriers, exome-wide (higher = slower) |
| Chen 2023 PTV, VNR / fluid intelligence | beta −0.547 (SE 0.104), p 1.24e-7, 79 carriers, exome-wide |
| Genebass pLoF, reaction time | burden p 1.33e-12. Same UKB participants. |
| Genebass pLoF, FI | burden p 1.38e-6 (suggestive) |
| Wu 2025 pLoF+missense, EduYears | p 3.26e-9. EA/SES proxy only. |
| Replication | Not replicated at gene level. Only the 8-gene set replicated (SUPER-Finland, NFID). NFID single-gene DD/ID OR 4.78, p 0.02 (nominal). |
| Disease | DDG2P KDM5B-related NDD (strong, LoF). OMIM 618109 (AR IDD-65). |
| Modifiability | Chromatin regulator (JmjC H3K4me1/2/3 demethylase). Nuclear. Structure with ligand; 1 high-quality chemical probe (inhibitor); 0 clinical candidates. gnomAD LOEUF 0.858. |

**Common-variant check I ran for this dossier (read-only):**
- The common SNP rs10920444 sits beside KDM5B and is the index SNP Wu 2025 mentions. It is null for cognition: Davies 2018 p = 0.84, Savage 2018 p = 0.50, from local sumstats.
- `common_rare_convergence.csv` lists KDM5B among genes with a nominal MAGMA P < 0.05. That is not Bonferroni-significant.

## 3. Three separate questions

- **A. Causal cognition gene? SUPPORTED (LoF direction only).**
  - Exome-wide PTV burden on three phenotypes in UKB.
  - Established recessive and dominant NDD in clinical cohorts, which are independent of UKB.
  - Mouse LoF phenocopies the memory deficit.
  - The gene-level replication outside UKB is only nominal (NFID DD/ID p = 0.02).
- **B. Natural high-cognition gene? NOT SUPPORTED.**
  - No common locus: rs10920444 is null in Davies and Savage.
  - No gain-of-function (GoF) or enhancing allele is known.
- **C. Adult-modifiable? NOT TESTABLE for enhancement; adult function is plausible.**
  - Adult hippocampal knockdown in mouse impairs memory and LTP and causes seizures (Pérez-Sisqués 2024). The adult brain therefore needs KDM5B, but that is LoF only.
  - An injury model (neonatal sevoflurane) reported rescue with a KDM5B inhibitor (Wang 2024). That points the other way, but only in a pathological context. It is not evidence for healthy adults.
  - No human adult-direction data exist.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| Variant (rare PTV) → gene | EVIDENCED | PTV burden (Chen 2023; Genebass) |
| Gene → element | not applicable | coding |
| Gene → cell type | INFERRED | broad neural expression. Adult hippocampal requirement shown in mouse only. |
| Direction (less KDM5B → worse) | EVIDENCED (LoF) | UKB burden, NDD, mouse |
| Direction (more KDM5B → better) | MISSING | no GoF data. H3K4 demethylase dosage is bidirectionally sensitive (KDM5 inhibitor/injury data). |
| Gene → cognition in humans independent of UKB | INFERRED/weak | recessive IDD families and NFID nominal only |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Chen CY 2023 Nat Genet, PMID 37231097, doi:10.1038/s41588-023-01398-8 | Exome-wide PTV burden for EDU, RT and VNR | SUPPORTING | Discovery data. **[UKB-shared: A]** |
| Karczewski 2022 Cell Genomics (Genebass), doi:10.1016/j.xgen.2022.100168 | pLoF burden RT p 1.3e-12 | NON-INDEPENDENT | Same UKB exomes as Chen. **[A]** |
| Wu XR 2025 PNAS, PMID 39772748 | pLoF+missense and EduYears | NON-INDEPENDENT | SES proxy, not cognition. **[A]** |
| Martin HC 2018 Science, PMID 30409806 | KDM5B among recessive DD genes | DISEASE_ONLY | Independent of UKB. Biallelic LoF. |
| Faundes 2018 AJHG, PMID 29276005 | KMT/KDM haploinsufficiency in DD. Heterozygous KDM5B PTVs also seen in unaffected parents and controls. | DISEASE_ONLY / CONTRADICTING (penetrance) | Monoallelic penetrance is incomplete. |
| Borroto 2024 Genes, PMID 39202393 | 21-person series. Dominant missense variants likely pathogenic, and some dominant PTVs are found in unaffected people. | DISEASE_ONLY | Confirms variable heterozygous penetrance |
| Sabetfakhri 2025, PMID 40657596 | Heterozygous PTV with ASD/OCD. Heterozygous PTV phenotypes "inconsistent" | DISEASE_ONLY | Case report |
| Albert 2013 PLoS Genet, PMID 23637629 | Kdm5b-/- mice: neonatal lethality and neural-tube and cranial-nerve defects | MECHANISTIC_ONLY | Strong developmental role |
| Pérez-Sisqués 2024 J Neurosci, PMID 38575342, doi:10.1523/JNEUROSCI.1544-23.2024 | Demethylase-dead mice and adult hippocampal knockdown: LTM and LTP deficits, seizures | SUPPORTING (LoF) / MECHANISTIC | Adult requirement. **Contradicts the developmental-only flag.** |
| Wang 2024 Front Mol Neurosci, PMID 39664113 | A KDM5B inhibitor partially rescued sevoflurane-induced deficits in neonatal rats | CONTRADICTING (direction, context-specific) | Injury model, small rodent study. Not an enhancement claim. |
| Fernandez 2023 PLoS One, PMID 37788244 | De novo damaging variants in motor stereotypies | DISEASE_ONLY | Small trio study |

**Forward citations and failed replications:**
- I found no published gene-level replication of the adult-cognition PTV effect outside UKB.
- The only independent test is Chen's own set-level NFID and SUPER-Finland replication.

## 6. Modifiability characterisation (facts only)

- **Protein:** JmjC-domain Fe(II)/2-oxoglutarate-dependent histone H3K4 demethylase (KDM5 family), with ARID and PHD domains. It is nuclear.
- **Enzymatic activity:** yes. The catalytic pocket is structurally characterised, with ligand-bound structures (OT tractability: "Structure with Ligand; High-Quality Ligand").
- **Known modulators (all inhibitors; listed as facts):**
  - Pan-KDM5 tool compounds CPI-455 and KDOAM-25. OT records 1 high-quality chemical probe with MoA "inhibitor".
  - GS-5801, a liver-targeted KDM5 prodrug from Gilead, entered phase 1 for chronic hepatitis B, and that programme was terminated in 2018 (PLoS One 2022, PMID 36477212; AdisInsight).
  - No activators are known.
- **Other properties:** no extracellular domain. The PROTAC flag rests on ubiquitination data.
- **Companies (one line):** oncology and virology KDM5 programmes (Gilead; Constellation, origin of CPI-455). None target cognition.

## 7. Pleiotropy and safety

- **Oncology:** KDM5B is a breast-cancer oncogene and drug-tolerance factor, and a possible melanoma tumour suppressor. Its role depends on context.
- **Development:** it is essential for development. Complete loss in mice is neonatal-lethal.
- **Stem cells:** it has roles in ES cells and in the oocyte-to-embryo transition.
- **Circadian:** it represses CLOCK-BMAL1 (UniProt summary in the packet).
- **Heterozygous LoF in humans:** penetrance for ID and ASD is incomplete and variable.
- **Direction:** both LoF and inhibitor-associated effects are documented. The dosage direction is not monotonic across contexts.

## 8. Largest contradiction

Our packet flags KDM5B as `DEVELOPMENTAL_CAUSAL_ONLY` because its expression is prenatal-dominant. Pérez-Sisqués 2024 shows that adult-restricted hippocampal knockdown alone causes memory and LTP deficits. A secondary point is that heterozygous PTVs appear in unaffected people (Faundes 2018; Borroto 2024), so the UKB effect is an average over carriers with heterogeneous penetrance.

## 9. Missing arrow and single best next computation

- **Missing arrow:** a UKB-independent gene-level human LoF → adult-cognition estimate, and any evidence of a gain direction.
- **Best next computation:**
  - Pull the per-gene de novo PTV and missense counts and DeNovoWEST P for KDM5B from the Kaplanis 2020 DDD supplementary tables (31,058 trios) and from the Fu 2022 NDD/ASD tables.
  - Compare them with the mutation-rate expectation.
  - Separately, pull the Genebass per-variant pLoF carriers for KDM5B and compute a leave-one-variant-out burden, to check that no single recurrent variant drives the effect.
