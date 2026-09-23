# CACNA1A (CaV2.1, P/Q-type α1A): literature red-team dossier (Sprint 5, batch 2)

Written 2026-09-23 (UTC). This covers target characterisation and evidence appraisal only. It contains no compound design, dosing, intervention or self-use content. LoF evidence is never inverted into enhancement.

## 1. Verdict

**Class: `CODING_CAUSAL_LOF_ONLY` (DEVELOPMENTAL flag false; `ADULT_DYNAMIC`).**
- CACNA1A has the best disease-level support in the batch: haploinsufficiency causes cognitive impairment, ADHD/ASD and absence epilepsy in families, and mouse LoF reproduces the cognitive deficits.
- Our UKB VNR association is marginal: p 1.33e-6 is above Chen's stated study-wide threshold.
- **Both GoF and LoF variants cause severe neurodevelopmental disease.** The dosage–cognition relation is therefore not monotonic, and "more channel" is not a beneficial direction.

## 2. Our computed evidence (packet; unchanged)

| Item | Value |
|---|---|
| Locus | none. Panel B. rank_B 18, rank_E 6, rank_D 1 (P2). |
| GTEx adult-brain TPM | 13.34. `ADULT_DYNAMIC`. |
| Chen 2023 PTV VNR/FI | beta −0.824 (SE 0.171), p 1.33e-6, 29 carriers. **Discrepancy:** flagged exome-wide, but p exceeds the stated 1.15e-6. It passes only the per-phenotype 4.20e-6. |
| Chen 2023 PTV RT | beta +0.352 (SE 0.114), p 0.00195, 74 carriers |
| Chen 2023 PTV EDU | beta −0.21 (SE 0.092), p 0.023, 78 carriers |
| Genebass pLoF FI | burden p 1.54e-5 (suggestive; same UKB) |
| Disease | DDG2P CACNA1A-related epileptic encephalopathy (strong). OMIM EA2, SCA6, FHM1, DEE42. LoF and GoF both pathogenic. |
| Common-variant MAGMA | nominal P < 0.05 (`common_rare_convergence.csv`). No genome-wide locus in our set. |
| Modifiability | Voltage-gated Ca²⁺ channel pore subunit. Membrane. "Approved Drug; Druggable Family". 11 clinical candidates (OT/ChEMBL target CHEMBL4266). LOEUF 0.331. |

## 3. Three separate questions

- **A. Causal cognition gene? SUPPORTED (LoF impairs; disease-grade human evidence independent of UKB).**
  - Families with PTVs or deletions show ID, executive dysfunction and ADHD (Damaj 2015).
  - LoF knock-in and conditional mice show cognitive deficits.
  - The UKB population effect itself is marginal.
- **B. Natural high-cognition gene? NOT SUPPORTED.**
  - No genome-wide common locus; MAGMA is only nominal.
  - GoF variants are more severe than LoF, not beneficial (Kessi 2023; Lipman 2022; Jiang 2019).
- **C. Adult-modifiable? NOT TESTABLE for a beneficial direction; adult circuit rescue is shown for LoF deficits.**
  - Chemogenetic activation of PV interneurons in adult frontal cortex rescued Cacna1a-haploinsufficient deficits (Lupien-Meilleur 2021).
  - That rescue acts downstream of the channel. It does not show that modulating CACNA1A itself in adults changes cognition.

## 4. Causal chain

| Arrow | Status | Basis |
|---|---|---|
| Rare PTV → CaV2.1 haploinsufficiency | EVIDENCED | Human iPSC CACNA1A+/- (Hommersom 2025). Family PTVs. |
| → Cell type | EVIDENCED (mouse) | PV-interneuron GABA release is reduced. Pyramidal-cell deletion has no behavioural effect (Lupien-Meilleur 2021). Cerebellar Purkinje cells for ataxia. |
| → Circuit | EVIDENCED (mouse) | Frontal perisomatic disinhibition leads to deficits in attention and reversal learning |
| Direction LoF → worse cognition | EVIDENCED | Families; mouse; UKB (marginal) |
| Direction GoF → better | CONTRADICTED | GoF causes severe DEE and ID |
| Isoform: α1ACT second cistron | caveat | C-terminal PTVs may affect the α1ACT transcription factor differently (Du 2013) |

## 5. Literature red-team

| Source | Claim | Category | Note |
|---|---|---|---|
| Chen CY 2023 Nat Genet, PMID 37231097 | PTV and VNR (29 carriers) | SUPPORTING (marginal) | Threshold inconsistency. [UKB-shared A] |
| Karczewski 2022 Genebass | pLoF FI p 1.5e-5 | NON-INDEPENDENT | [A] |
| Damaj 2015 EJHG, PMID 25735478, doi:10.1038/ejhg.2015.21 | CACNA1A haploinsufficiency causes ID, executive dysfunction, ADHD/ASD and absence EE with mild cerebellar signs (16 people, 4 families) | SUPPORTING (disease) | Independent of UKB. LoF. |
| Lupien-Meilleur 2021 Mol Psychiatry, PMID 34127816, doi:10.1038/s41380-021-01175-1 | PV-restricted Cacna1a haploinsufficiency gives impulsivity, cognitive rigidity and inattention, rescued by PV-IN chemogenetics | MECHANISTIC (LoF) | Mouse. Cell-type specificity. |
| Hommersom 2025 Brain, PMID 39460936, doi:10.1093/brain/awae330 | Human iPSC CACNA1A+/-: synaptic deficits plus increased intrinsic excitability | MECHANISTIC_ONLY | LoF |
| Niu 2026 Brain, PMID 41699918, doi:10.1093/brain/awag066 | D1634N LoF: patient ID; knock-in mice with ataxia, absence epilepsy and cognitive deficits | SUPPORTING (LoF) / MECHANISTIC | |
| Jiang 2019 Epilepsia, PMID 31468518, doi:10.1111/epi.16316 | **Both GoF and LoF** de novo variants cause severe DEE | CONTRADICTING (monotonic dosage) | Key for direction |
| Kessi 2023 Front Mol Neurosci, PMID 37555011 | Across 187 people with GDD/ID, GoF variants give more severe ID than LoF | CONTRADICTING (monotonic dosage) | Literature pooled |
| Lipman 2022 Clin Genet, PMID 35722745 | 47 people; DD/ID in 96%; predicted GoF more severe | DISEASE_ONLY | Ascertained clinical cohort |
| Du X 2013 Cell, PMID 23827678, doi:10.1016/j.cell.2013.05.059 | A second cistron encodes the α1ACT transcription factor (cerebellar development, SCA6) | MECHANISTIC_ONLY | Isoform/cistron caveat for PTV position |
| Wong-Spracklen 2022 AJMG-A, PMID 36063114 | Biallelic variants with severe DEE; heterozygous parents unaffected | CONTRADICTING (penetrance) | Some heterozygous LoF is tolerated |
| Hidalgo 2021 Neurobiol Dis, PMID 34015490 | Drosophila cac LoF impairs memory, sleep and circadian rhythm | MECHANISTIC_ONLY | Ortholog also covers CaV2.2 |

**Forward citations:** CACNA1A Foundation trial-readiness programmes (Fox 2024, PMID 38681799). I found no failed replication of the LoF–ID link; the disease link is robust.

## 6. Modifiability characterisation (facts only)

- **Protein and structure:** the pore-forming α1 subunit of CaV2.1 (24 TM segments in 4 domains; voltage sensors S1–S4, pore S5–S6). It assembles with β and α2δ subunits. Presynaptic, triggering fast glutamate and GABA release. Ligand-bound structures are recorded (OT). Extracellular loops exist.
- **Endogenous ligand:** none. It is voltage-gated and Ca²⁺-permeant.
- **Known modulators (facts):**
  - ω-agatoxin IVA (a selective P-type spider toxin, research tool).
  - ω-conotoxin MVIIC (a P/Q/N-type toxin).
  - Various non-selective small-molecule VGCC blockers (ChEMBL CHEMBL4266; OT counts 11 clinical candidates).
  - Roscovitine analogues, reported as CaV2 gating modifiers.
  - Insensitive to dihydropyridines.
- **Disease-context clinical programmes (facts):**
  - 4-aminopyridine for EA2. It acts on K⁺ channels, not on CaV2.1, and its phase 2 NCT01543750 was withdrawn.
  - Acetazolamide for EA2.
  - N-acetyl-L-leucine phase 3 in CACNA1A disorders (NCT07221292, IntraBio, recruiting).
  - Troriluzole in SCA, including SCA6 (Biohaven).
  - None aim at cognition in healthy people.

## 7. Pleiotropy and safety

- **Neurological spectrum:** ataxia (EA2, SCA6), hemiplegic migraine (FHM1, GoF), absence and refractory epilepsy, paroxysmal tonic upgaze, and neuromuscular-junction effects (CaV2.1 at the NMJ; Lambert–Eaton antibodies target P/Q channels).
- **Both directions of dosage are pathogenic.** That is the dominant safety fact.

## 8. Largest contradiction

- CACNA1A is a textbook dosage-sensitive gene in *both* directions: GoF causes FHM1 and DEE, often with more severe ID than LoF.
- Our UKB PTV association is also statistically marginal (p 1.33e-6, above the stated study-wide threshold).
- It is a well-supported LoF → cognition gene but has no coherent "beneficial" direction.

## 9. Missing arrow and single best next computation

- **Missing arrow:** whether the UKB PTV signal reflects typical haploinsufficiency (NMD) or is driven by a few C-terminal or NMD-escaping variants, and whether carriers have undiagnosed EA2 or epilepsy.
- **Best next computation:**
  - Download the Genebass variant-level pLoF results for CACNA1A (FI, RT, EDU).
  - Map each PTV to its protein position and NMD-escape status (last exon or 50-nt rule), and to the α1ACT cistron region.
  - Recompute burden excluding NMD-escape and α1ACT-region PTVs.
