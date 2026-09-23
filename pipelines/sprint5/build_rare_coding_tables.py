import csv, json, hashlib, os, datetime, glob

ROOT = "/Users/moheet/Documents/ChatGPT/HUMAN INTELLIGENCE 🧠"
RAW = f"{ROOT}/data/raw/sprint5/rare_coding"
# DDG2P dump is kept local-only (licence); re-download URL + sha256 in data/raw/sprint5/rare_coding/PROVENANCE.json
DDG2P = f"{ROOT}/data/interim/sprint5/literature_local_only/rare_coding__DDG2P_panel_DD_download.csv"
INT = f"{ROOT}/data/interim/sprint5/rare_coding"

def se_from_ci(lo, hi):
    return f"{(hi - lo) / (2 * 1.96):.3f}"

# ------------------------------------------------------------------ TASK A rows
cols = ["gene", "study", "pmid_or_doi", "cohort", "uk_biobank_contributes", "n", "ancestry", "phenotype",
        "phenotype_class", "variant_class", "direction", "effect", "se", "p", "exome_wide_significant",
        "replicated", "disease_association", "evidence_type", "notes"]
rows = []

CHEN = dict(study="Chen CY et al. 2023 Nat Genet (rare coding variants & adult cognition)",
            pmid_or_doi="PMID:37231097; doi:10.1038/s41588-023-01398-8; PMC10260403",
            cohort="UK Biobank WES (discovery, related EUR, regenie PTV burden, MAF<1e-5)",
            uk_biobank_contributes="Y", ancestry="EUR (SAS n=9,224 / AFR n=8,406 analysed separately, underpowered)")
N = {"EDU": "393,758", "RT": "394,600", "VNR": "159,026"}
THR = {"EDU": 3.17e-6, "RT": 3.16e-6, "VNR": 4.20e-6}
PH = {"EDU": ("educational attainment (years of schooling; UKB)", "EA_PROXY"),
      "RT": ("reaction time (UKB field 20023; higher = slower)", "REACTION_TIME"),
      "VNR": ("verbal-numerical reasoning / fluid intelligence (UKB field 20016)", "GENERAL_COGNITION")}
REPL_SET = ("N at gene level (replication cohorts too small); 8-gene PTV SET replicated: SUPER-Finland EDU beta=-0.424 p=0.0021, "
            "academic performance beta=-0.338 p=0.0125, DD/ID OR=4.81 p=8.3e-4; NFID DD/ID OR=4.97 p=3.6e-5; MGBB EDU p=0.50 (8 carriers)")
DIS = {
    "ADGRB2": "none in DDG2P (download 2026-09-23); PheWAS: impaired cognitive function R41.8, chlorpromazine use",
    "KDM5B": "DDG2P KDM5B-related NDD (biallelic & monoallelic; strong; LoF); OMIM 618109 AR intellectual developmental disorder-65",
    "GIGYF1": "DDG2P GIGYF1-related DD (monoallelic; limited; LoF); PheWAS T2D",
    "ANKRD12": "none in DDG2P; SCZ exome signal (per Chen); PheWAS dysarthria/anarthria; BRaVa 2026: asthma/COPD",
    "SLC8A1": "none in DDG2P",
    "RC3H2": "none in DDG2P",
    "CACNA1A": "DDG2P CACNA1A-related epileptic encephalopathy (monoallelic; strong); OMIM SCA6, episodic ataxia 2, FHM1, DEE42 (LoF and GoF both pathogenic)",
    "BCAS3": "DDG2P BCAS3-related NDD (biallelic; strong; LoF); OMIM 619641 Hengel-Maroofian-Schols syndrome",
}
t1 = {  # gene: {pheno: (beta, lo, hi, p, ncarrier, flag)}
    "ADGRB2": {"EDU": (-0.664, -0.854, -0.473, 8.55e-12, 71, "a"), "RT": (0.159, -0.070, 0.388, 0.174, 70, ""), "VNR": (-0.615, -0.976, -0.255, 8.28e-4, 25, "")},
    "KDM5B": {"EDU": (-0.307, -0.419, -0.195, 8.68e-8, 204, "a"), "RT": (0.447, 0.311, 0.582, 9.60e-11, 201, "a"), "VNR": (-0.547, -0.750, -0.344, 1.24e-7, 79, "a")},
    "GIGYF1": {"EDU": (-0.492, -0.660, -0.324, 9.80e-9, 91, "a"), "RT": (0.275, 0.076, 0.473, 6.78e-3, 93, ""), "VNR": (-0.490, -0.771, -0.209, 6.43e-4, 41, "")},
    "ANKRD12": {"EDU": (-0.310, -0.445, -0.176, 6.26e-6, 142, "FDR"), "RT": (0.101, -0.057, 0.260, 0.210, 146, ""), "VNR": (-0.694, -0.941, -0.447, 3.77e-8, 53, "a")},
    "SLC8A1": {"EDU": (-0.992, -1.371, -0.613, 2.84e-7, 18, "a"), "RT": (0.202, -0.250, 0.654, 0.381, 18, "")},
    "RC3H2": {"EDU": (-0.337, -0.612, -0.062, 0.016, 34, ""), "RT": (0.132, -0.196, 0.461, 0.430, 34, ""), "VNR": (-1.126, -1.576, -0.676, 9.32e-7, 16, "a")},
    "CACNA1A": {"EDU": (-0.210, -0.391, -0.029, 0.023, 78, ""), "RT": (0.352, 0.129, 0.575, 1.95e-3, 74, ""), "VNR": (-0.824, -1.159, -0.490, 1.33e-6, 29, "a")},
    "BCAS3": {"EDU": (-0.419, -0.592, -0.246, 1.99e-6, 86, "pheno"), "RT": (0.207, -0.003, 0.417, 0.054, 83, ""), "VNR": (-0.361, -0.670, -0.053, 0.022, 34, "")},
}
indiv_repl = {"KDM5B": "; NFID individual gene DD/ID OR=4.78 p=0.02 (nominal)", "GIGYF1": "; NFID individual gene DD/ID OR=6.15 p=0.011 (nominal)",
              "ADGRB2": "; NFID DD/ID OR=1.34 p=0.55", "ANKRD12": "; NFID DD/ID OR=2.39 p=0.24"}
for g, d in t1.items():
    for ph, (b, lo, hi, p, nc, flag) in d.items():
        sig = p < THR[ph]
        if ph == "EDU":
            dirn = "PTV carriers fewer years of education (EA proxy, not cognition)" if b < 0 else "PTV carriers more education"
        elif ph == "RT":
            dirn = "PTV carriers slower reaction time" if b > 0 else "PTV carriers faster reaction time"
        else:
            dirn = "PTV carriers lower VNR/fluid intelligence" if b < 0 else "PTV carriers higher VNR"
        note = f"PTV carriers n={nc}; beta in SD of rank-INT phenotype (95% CI {lo} to {hi}). "
        if flag == "a":
            note += "Table 1 marks this as exome-wide significant across all tests (stated threshold P<1.15e-6). "
        if g == "CACNA1A" and ph == "VNR":
            note += "DISCREPANCY: P=1.33e-6 is ABOVE the stated study-wide 1.15e-6 yet flagged 'a' in Table 1; it passes only the per-phenotype VNR threshold 4.20e-6. "
        if flag == "pheno":
            note += "Passes per-phenotype Bonferroni (3.17e-6) but NOT study-wide 1.15e-6 (not flagged 'a'). "
        if flag == "FDR":
            note += "EDU association FDR-significant only. "
        if ph == "EDU" and g in ("ADGRB2", "GIGYF1", "SLC8A1", "BCAS3"):
            note += "Gene's only exome-wide significant phenotype is EDU -> EA_PROXY-only gene in Chen 2023. "
        if g == "KDM5B":
            note += "Mouse Kdm5b +/- and -/- show dose-dependent memory deficits (LoF dosage, not enhancement). "
        if g == "SLC8A1" and ph == "RT":
            note += "VNR not tested (<10 carriers). "
        rows.append(dict(gene=g, **CHEN, n=N[ph], phenotype=PH[ph][0], phenotype_class=PH[ph][1],
                         variant_class="PTV (pLoF, MAF<1e-5)", direction=dirn, effect=f"beta={b}", se=se_from_ci(lo, hi),
                         p=f"{p:.3g}", exome_wide_significant="Y" if sig else "N",
                         replicated=REPL_SET + indiv_repl.get(g, "") if sig else "NOT_TESTED (phenotype not significant in discovery)",
                         disease_association=DIS[g], evidence_type="CODING_CAUSAL_LOF_ONLY", notes=note.strip()))
    if g == "SLC8A1":
        rows.append(dict(gene=g, **CHEN, n=N["VNR"], phenotype=PH["VNR"][0], phenotype_class="GENERAL_COGNITION",
                         variant_class="PTV (pLoF, MAF<1e-5)", direction="not tested", effect="NA", se="NA", p="NA",
                         exome_wide_significant="N", replicated="NOT_TESTED", disease_association=DIS[g],
                         evidence_type="CODING_CAUSAL_LOF_ONLY", notes="Only 4 VNR PTV carriers; excluded (<10)."))

fdr = [("NDUFA6", "EDU", -0.750, -1.077, -0.423, 6.98e-6, 0.0157, 24, "DDG2P NDUFA6-related mitochondrial complex I deficiency (biallelic; strong; LoF); OMIM nuclear mito complex I deficiency 33"),
       ("ARHGEF7", "VNR", -0.974, -1.410, -0.538, 1.22e-5, 0.0276, 17, "none in DDG2P"),
       ("C11orf94", "VNR", 1.204, 0.661, 1.746, 1.39e-5, 0.0276, 11, "none in DDG2P"),
       ("KIF26A", "VNR", -0.644, -0.944, -0.344, 2.57e-5, 0.0437, 36, "not in DDG2P download under this symbol (2026-09-23)"),
       ("MAP1A", "EDU", -0.381, -0.554, -0.207, 1.77e-5, 0.0349, 85, "none in DDG2P; ASD exome signal (per Chen Table S3)")]
for g, ph, b, lo, hi, p, q, nc, dis in fdr:
    if ph == "EDU":
        dirn = "PTV carriers fewer years of education (EA proxy)"
    elif b > 0:
        dirn = "PTV carriers HIGHER VNR (positive direction; LoF, n=11)"
    else:
        dirn = "PTV carriers lower VNR/fluid intelligence"
    note = f"FDR-significant only (Q={q}); PTV carriers n={nc}; 95% CI {lo} to {hi}. Supplementary Table S3."
    if g == "C11orf94":
        note += (" RARE POSITIVE-DIRECTION LoF SIGNAL: loss-of-function carriers scored higher (RT beta=-0.474 p=0.046 also 'better'; EDU +0.219 p=0.27). "
                 "11 carriers, FDR only; Genebass (MAF<1%, overlapping UKB) FI pLoF burden p=0.36 (beta +, tiny) -> not supported. "
                 "This is LoF, NOT gain-of-function; do not label enhancement.")
    if g == "MAP1A":
        note += " Genebass RT pLoF burden p=8.1e-6 (slower), UKB-overlapping."
    if g == "ARHGEF7":
        note += " Genebass FI pLoF burden p=5.2e-4 (lower), UKB-overlapping."
    rows.append(dict(gene=g, **CHEN, n=N[ph], phenotype=PH[ph][0], phenotype_class=PH[ph][1], variant_class="PTV (pLoF, MAF<1e-5)",
                     direction=dirn, effect=f"beta={b}", se=se_from_ci(lo, hi), p=f"{p:.3g}", exome_wide_significant="N",
                     replicated="N (5 FDR genes + 8 genes 13-gene set replicated at set level only; KIF26A NFID OR=0 p=1)",
                     disease_association=dis, evidence_type="CODING_CAUSAL_LOF_ONLY" if b < 0 or ph == "EDU" else "CODING_LOF_POSITIVE_DIRECTION_SUGGESTIVE",
                     notes=note))

GB = dict(study="Karczewski KJ et al. 2022 Cell Genomics - Genebass browser (SAIGE-GENE, 394,841 UKB exomes)",
          pmid_or_doi="PMID:36778668; doi:10.1016/j.xgen.2022.100168; data https://main.genebass.org/api (CC BY 4.0)",
          cohort="UK Biobank WES 394,841 (SAME participants as Chen 2023 -> not independent)", uk_biobank_contributes="Y",
          ancestry="EUR (Genebass European-ancestry analysis)")
GBTHR = "Genebass thresholds SKAT-O 2.5e-7, burden 6.7e-7. Burden beta is on Genebass weighted-burden scale (direction usable, magnitude not comparable to Chen)."
gb = [
    ("ANKRD12", "fluid intelligence score (20016, irnt)", "GENERAL_COGNITION", "128,302", "pLoF MAF<1%", "pLoF carriers lower fluid intelligence", -0.0285, "burden 5.28e-14; SKAT-O 1.15e-13", "Y", ""),
    ("KDM5B", "mean time to correctly identify matches (20023, irnt)", "REACTION_TIME", "392,194", "pLoF MAF<1%", "pLoF carriers slower reaction time", 0.0171, "burden 1.33e-12; SKAT-O 1.69e-13", "Y", ""),
    ("KDM5B", "fluid intelligence score (20016, irnt)", "GENERAL_COGNITION", "128,302", "pLoF MAF<1%", "pLoF carriers lower fluid intelligence", -0.0223, "burden 1.38e-6; SKAT-O 6.10e-6", "N", "suggestive"),
    ("RC3H2", "fluid intelligence score (20016, irnt)", "GENERAL_COGNITION", "128,302", "pLoF MAF<1%", "pLoF carriers lower fluid intelligence", -0.0528, "burden 1.56e-6; SKAT-O 6.73e-6", "N", "suggestive"),
    ("CACNA1A", "fluid intelligence score (20016, irnt)", "GENERAL_COGNITION", "128,302", "pLoF MAF<1%", "pLoF carriers lower fluid intelligence", -0.0311, "burden 1.54e-5; SKAT-O 4.15e-5", "N", "suggestive"),
    ("ANKRD12", "fluid intelligence score, online follow-up (20191, irnt)", "GENERAL_COGNITION", "100,900", "pLoF MAF<1%", "pLoF carriers lower fluid intelligence", -0.0235, "burden 2.44e-5; SKAT-O 5.44e-5", "N", "partly the same participants as 20016"),
    ("ADAMTS6", "fluid intelligence score (20016, irnt)", "GENERAL_COGNITION", "128,302", "missense|LC MAF<1%", "missense carriers lower fluid intelligence", -0.0036, "burden 2.45e-7; SKAT-O 8.96e-7", "Y", "passes burden threshold only (SKAT-O 8.96e-7 > 2.5e-7); missense-driven; pLoF burden p=0.71; not reported by Chen (PTV-only design)"),
    ("MAP1A", "mean time to correctly identify matches (20023, irnt)", "REACTION_TIME", "392,194", "pLoF MAF<1%", "pLoF carriers slower reaction time", 0.0161, "burden 8.14e-6; SKAT-O 3.21e-5", "N", "Chen FDR gene for EDU"),
    ("BRPF1", "prospective memory result (20018, raw 0/1/2)", "MEMORY", "131,007", "pLoF MAF<1%", "direction NOT interpretable (UKB data-coding 18: 0=not recalled, 1=correct 1st attempt, 2=correct 2nd attempt; non-monotone)", -0.0583, "burden 5.47e-7; SKAT-O 1.45e-6", "Y", "burden threshold only; DDG2P BRPF1 syndromic ID with ptosis (definitive, LoF)"),
    ("ASAP1", "prospective memory result (20018, raw 0/1/2)", "MEMORY", "131,007", "pLoF MAF<1%", "direction NOT interpretable (non-monotone coding)", -0.0108, "SKAT-O 8.14e-10; burden 0.020", "Y", "SKAT-driven (burden p=0.02) -> likely one or few variants; treat as artefact-prone"),
    ("NACC1", "prospective memory result (20018, raw 0/1/2)", "MEMORY", "131,007", "missense|LC MAF<1%", "direction NOT interpretable (non-monotone coding)", -0.0036, "SKAT-O 1.70e-9; burden 3.40e-8", "Y", "DDG2P NACC1-related infantile epilepsy/cataract/profound DD (definitive, GAIN of function) -- missense in a GoF disease gene; direction unknown"),
    ("AC011448.1", "mean time to correctly identify matches (20023, irnt)", "REACTION_TIME", "392,194", "missense|LC MAF<1%", "missense carriers marginally FASTER reaction time (beta<0)", -0.0022, "SKAT-O 1.35e-7; burden 2.45e-6", "Y", "chr19:19.51 Mb (GRCh38) next to YJEFN3 (SKAT-O 3.6e-7, not sig) / CILP2 / GATAD2A -- pleiotropic 19p13.11 GWAS region; SKAT-driven; likely LD with a common/low-frequency signal; do NOT treat as causal gene or enhancement"),
]
for g, ph, pc, n, vc, dirn, b, p, sig, extra in gb:
    ev = "CODING_CAUSAL_LOF_ONLY" if vc.startswith("pLoF") else "CODING_MISSENSE_ASSOCIATION"
    if g == "AC011448.1":
        ev = "CODING_ASSOCIATION_LIKELY_LD_ARTEFACT"
    rows.append(dict(gene=g, **GB, n=n, phenotype=ph, phenotype_class=pc, variant_class=vc, direction=dirn, effect=f"burden beta={b}",
                     se="NA", p=p, exome_wide_significant=sig,
                     replicated="N (UKB re-analysis; overlaps Chen discovery samples)" if g in ("ANKRD12", "KDM5B", "RC3H2", "CACNA1A", "MAP1A") else "NOT_TESTED",
                     disease_association=DIS.get(g, {"ADAMTS6": "none in DDG2P", "MAP1A": "none in DDG2P", "BRPF1": "DDG2P BRPF1 syndromic ID with ptosis (monoallelic; definitive; LoF)",
                                                     "ASAP1": "none in DDG2P", "NACC1": "DDG2P NACC1-related infantile epilepsy, cataracts, profound DD (monoallelic; definitive; GAIN of function)",
                                                     "AC011448.1": "none"}.get(g, "")),
                     evidence_type=ev, notes=(extra + ". " if extra else "") + GBTHR))

WU = dict(study="Wu XR et al. 2025 PNAS (exome SES: EduYears, income, occupation, TDI)",
          pmid_or_doi="PMID:39772748; doi:10.1073/pnas.2414018122; PMC11745334",
          cohort="UK Biobank WES, unrelated White British (SAIGE-GENE+ SKAT-O; Bonferroni 8.49e-8)", uk_biobank_contributes="Y", ancestry="EUR (White British)")
wu = [("GIGYF1", "years of education (EduYears)", "297,089", "pLoF MAF<1e-4", "pLoF carriers fewer years of education", "beta=-0.119", "0.020", "2.16e-10", "MAC=98; LOVO robust (multiple variants)"),
      ("KDM5B", "years of education (EduYears)", "297,089", "pLoF+missense MAF<1e-4", "carriers fewer years of education", "beta=-0.023", "0.006", "3.26e-09", "MAC=1,155; significant only when missense added; LOVO robust; common index SNP rs10920444 nearby"),
      ("ADGRB2", "years of education (EduYears)", "297,089", "pLoF MAF<1e-4", "pLoF carriers fewer years of education", "beta=-0.100", "0.020", "6.78e-09", "MAC=97; single-variant driven per LOVO (not in robust list); EA GWAS SNP rs2050256 nearby"),
      ("ANKRD12", "household income (SES, not EA)", "258,589", "pLoF MAF<1e-4", "pLoF carriers lower household income", "beta=-0.027", "0.003", "2.33e-16", "SES outcome; also TDI beta=+0.071 p=4.6e-18; P changed minimally after geographic adjustment")]
for g, ph, n, vc, dirn, b, se, p, extra in wu:
    rows.append(dict(gene=g, **WU, n=n, phenotype=ph, phenotype_class="EA_PROXY", variant_class=vc, direction=dirn, effect=b, se=se, p=p,
                     exome_wide_significant="Y", replicated="N (same UKB participants as Chen 2023; confirmation, not independent replication)",
                     disease_association=DIS[g], evidence_type="CODING_CAUSAL_LOF_ONLY",
                     notes=extra + ". EA_PROXY/SES only -- not a cognition measurement."))

CK = dict(study="Chakraborty S & Kahali B 2023 HGG Advances (exome-wide cognition, APOE-context)",
          pmid_or_doi="PMID:37305557; doi:10.1016/j.xhgg.2023.100208; PMC10248556",
          cohort="UK Biobank WES 157,067 (rvtests SKAT/SKAT-O, all coding variants incl. common)", uk_biobank_contributes="Y", ancestry="EUR (UKB; per paper)")
for g, ph, pc in [("APOC1", "complex processing speed & visual attention", "EXECUTIVE"), ("LRP1", "visual attention (HDL-adjusted)", "EXECUTIVE")]:
    rows.append(dict(gene=g, **CK, n="157,067", phenotype=ph, phenotype_class=pc, variant_class="gene-based SKAT/SKAT-O over all coding variants (not rare-only)",
                     direction="not signed (kernel test)", effect="NA", se="NA", p="candidate-pathway threshold p<0.0025 (Table S14; exact p not extracted)",
                     exome_wide_significant="N", replicated="NOT_TESTED", disease_association="APOC1 lies ~5 kb from APOE (LD with APOE e4 likely)",
                     evidence_type="WEAK_CANDIDATE_GENE_ASSOCIATION",
                     notes="Candidate-gene test in APOE pathways, includes common variants; APOC1 signal likely APOE-region LD. The paper also claims 514 exome-wide gene hits across 6 domains (Tables S15-S21, not parsed) from all-variant SKAT; not treated as rare-coding causal evidence."))

SETROWS = [
    ("SET:599 dominant DDG2P genes", "Kingdom R et al. 2024 Nat Genet", "PMID:38637616; doi:10.1038/s41588-024-01710-0; PMC11096126",
     "UK Biobank WES/array 419,854 EUR", "Y", "419,854", "EUR", "fluid intelligence, EA, income, TDI and DD diagnoses", "GENERAL_COGNITION",
     "rare pLoF / REVEL>0.7 missense (AC<=5) + syndromic CNVs", "more rare damaging DD-gene variants -> lower fluid intelligence and SES; higher EA-PGS partially offsets",
     "additive per extra variant (see paper Fig. 1)", "NA", "see paper", "N (set-level)", "NOT_TESTED", "DDG2P dominant DD genes",
     "SET_LEVEL_LOF_ONLY", "Set-level only; no gene-level hits. 50,395 single carriers; 3,831 with two; 219 with >=3."),
    ("SET:SCZ-implicated genes (LoF-intolerant)", "Mol Psychiatry 2026 (rare coding variants in SCZ genes and g, UKB)", "PMID:41963674; doi:10.1038/s41380-026-03601-8; PMC7619269",
     "UK Biobank WES 76,783 without SCZ", "Y", "76,783", "EUR (per paper; not verified)", "general cognition g", "GENERAL_COGNITION",
     "PTV + deleterious missense (MAC<=5)", "carriers lower g", "see paper", "NA", "see paper", "N (set-level)", "NOT_TESTED", "SCZ risk genes",
     "SET_LEVEL_LOF_ONLY", "Set-level; abstract only read."),
    ("SET:exome-wide pLoF burden", "Malawsky DS et al. 2026 Nat Hum Behav (ALSPAC)", "PMID:42432050; doi:10.1038/s41562-026-02491-8; PMC13590407",
     "ALSPAC children (UK birth cohort; NOT UK Biobank)", "N", "6,495", "EUR", "childhood cognitive ability across ages", "GENERAL_COGNITION",
     "rare pLoF burden (RVB_pLoF)", "higher pLoF burden -> lower childhood cognition, attenuating with age", "RVB_pLoF x age per 10 y = +0.0239 [0.0110, 0.0368]",
     "NA", "see paper", "N (set-level)", "NOT_TESTED", "none", "SET_LEVEL_LOF_ONLY", "Independent of UKB; burden-level only; attenuation with age strongest at low end of distribution."),
]
for r in SETROWS:
    rows.append(dict(zip(cols, r)))

with open(f"{ROOT}/reports/sprint5/rare_coding_evidence.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("rare rows", len(rows))

# ------------------------------------------------------------------ TASK B rows
ccols = ["region_or_gene", "genes", "build_coords", "cnv_type", "direction", "phenotype", "study", "pmid_or_doi", "n_carriers", "effect", "p",
         "replicated", "uk_biobank_contributes", "clingen_dosage", "verdict", "notes"]
H24 = ("Huguet G et al. 2024 Cell Genomics (CNV-GWAS, 258,292 general-population individuals)", "PMID:39667348; doi:10.1016/j.xgen.2024.100721; PMC11701252 (Table S1)")
cr = []
cr.append(dict(region_or_gene="2q12.3 duplication (hg19 band; lies in 2q13 on GRCh38)", genes="EDAR; SH3RF3; SEPTIN10 (SEPT10); SOWAHC",
               build_coords="hg19 chr2:109,510,927-110,376,563 (~865 kb)", cnv_type="duplication",
               direction="duplication carriers HIGHER general cognitive ability", phenotype="general cognitive ability z (NVIQ / Moray House / FI / g-factor, z-scored within cohort)",
               study=H24[0], pmid_or_doi=H24[1], n_carriers="36 (SOWAHC); 33 (SEPT10); 31 (EDAR, SH3RF3); reciprocal deletion 12",
               effect="z=+0.434 (SOWAHC); +0.496 (SEPT10); +0.460 (EDAR/SH3RF3); dosage model +0.415 SD per copy (p=2.65e-3); reciprocal deletion z=-0.526 (p=0.058)",
               p="7.58e-3 (SOWAHC; FDR q=0.0373); 3.46e-3 (SEPT10; q=0.0172); 8.63e-3 (EDAR/SH3RF3; q=0.0418); post-hoc UKB White-British t-test p=0.001",
               replicated="N - no independent replication found (EuropePMC forward citations checked 2026-09-23: 5 citing items, none re-tests the locus; Kazem 2026 UKB+All of Us functional-burden paper and Poulain 2025 UKB paper do not mention 2q12.3/EDAR/SH3RF3/SEPT10/SOWAHC)",
               uk_biobank_contributes="Y (UKB 238,176 of 258,292 = 92%; post-hoc test UKB White British only)",
               clingen_dosage="ClinGen gene curation (local file 2026-09-22): EDAR, SH3RF3, SEPTIN10, SOWAHC all UNCURATED; nearest region ISCA-37405 2q13 NPHP1 (TS=40) outside interval. Collins 2022 pTriplo (model-predicted): EDAR 0.197, SH3RF3 0.595, SEPT10 0.983, SOWAHC 0.343",
               verdict="NOMINAL_UNREPLICATED",
               notes=("Only positive-effect CNV among all FDR-significant CNVs in Table S1 (all 6 deletions and other 6 duplications are negative). "
                      "The reported FDR q<0.05 is lenient: each gene of multigenic CNVs is a separate, highly correlated test and ~120+ genes from known pathogenic CNVs contribute very small p-values; not Bonferroni-significant across 596 duplication genes (8.4e-5). "
                      "CORRECTION for atlas: the atlas states no corrected p was found; Table S1 does report FDR q values (0.017-0.042). "
                      "Tension: SEPT10 pTriplo 0.98 predicts duplication intolerance (disease-model prediction, not cognition data). "
                      "Gene-level loss evidence is NOT support for duplication benefit: EDAR LoF causes hypohidrotic ectodermal dysplasia (DDG2P definitive); Sh3rf3 knockout mice show autism-like behaviour (Yuan 2025/2026 Mol Psychiatry) -- loss harmful does not imply gain beneficial. "
                      "Genebass rare coding tests of all four genes vs FI/RT: all p>0.01 (no coding convergence). "
                      "Median cohort age 60.7 y; authors raise 'neuroprotective' alternative. Winner's curse likely.")))

negdups = [("1q21.1 TAR (proximal) duplication", "HFE2..GPR89A (15 genes listed)", "hg19 chr1:145.41-145.83 Mb (gene spans, Table S1)", "143-247", "z=-0.27 to -0.31", "1.1e-4 to 1.3e-6", "ClinGen ISCA-37428 TS=1 (little evidence)"),
           ("15q13.3 BP4-BP5 duplication", "FAN1; MTMR10; TRPM1; KLF13; OTUD7A", "hg19 chr15:31.20-32.16 Mb", "150-153", "z=-0.36 to -0.38", "1.3e-6 to 4.6e-6", "ClinGen ISCA-37411 TS=1"),
           ("16p13.11 duplication", "NTAN1; RRN3; NDE1; MYH11; ABCC1 ...", "hg19 chr16:15.02-16.32 Mb", "112-458", "z=-0.21 to -0.41", "1.1e-7 to 2.6e-4", "ClinGen ISCA-37415 TS=2 (some evidence)"),
           ("16p11.2 proximal (BP4-BP5) duplication", "SPN..CORO1A (27 genes incl. KCTD13, TAOK2, MAPK3)", "hg19 chr16:29.67-30.20 Mb", "54-74", "z=-0.83 to -0.94", "2.8e-16 to 3.4e-10", "ClinGen ISCA-37400 TS=3 (sufficient)"),
           ("17q12 duplication", "ZNHIT3..HNF1B", "hg19 chr17:34.84-36.11 Mb (Table S1 coords)", "46-48", "z=-0.58 to -0.65", "3.3e-6 to 4.7e-5", "ClinGen ISCA-37432 TS=3 (sufficient)"),
           ("22q11.2 proximal duplication", "DGCR6..; PRODH; DGCR2; HIRA; UFD1L; CDC45 ...", "hg19 chr22:18.9-19.5 Mb (partial listing)", "~150-263", "z=-0.23 (DGCR6, n=253) to -0.54", "1.5e-4 to 1.6e-11", "ClinGen ISCA-37446 TS=3 (sufficient)")]
for reg, genes, co, n, eff, p, cg in negdups:
    note = "Duplication (increased dosage) associated with LOWER cognition in general population -> contradicts positive dosage."
    if reg.startswith("22q11.2"):
        note += " 22q11.2 duplication is often described as protective against schizophrenia (literature claim not re-verified here), yet carriers have LOWER cognition: protection from a disease is not cognitive enhancement."
    cr.append(dict(region_or_gene=reg, genes=genes, build_coords=co, cnv_type="duplication", direction="duplication carriers LOWER general cognitive ability",
                   phenotype="general cognitive ability z", study=H24[0], pmid_or_doi=H24[1], n_carriers=n, effect=eff, p=p,
                   replicated="Y (negative effect previously published per authors; persisted in meta-analysis across 9 sub-cohorts)",
                   uk_biobank_contributes="Y", clingen_dosage=cg, verdict="CONTRADICTED", notes=note))

cr.append(dict(region_or_gene="ZNF92 deletion", genes="ZNF92", build_coords="GRCh38 chr7:65,373,799-65,401,136 (gene; 7q11.21) - CNV breakpoints not extracted",
               cnv_type="deletion", direction="deletion carriers HIGHER general cognitive ability (loss of dosage, not gain)", phenotype="general cognitive ability (UKB)",
               study="Poulain C et al. 2025 Transl Psychiatry (CNVs, sleep, cognition; 498,852 UKB)", pmid_or_doi="PMID:41053002; doi:10.1038/s41398-025-03579-x; PMC12501278",
               n_carriers=">10 (exact count in eTable 5, not parsed)", effect="beta=+0.08", p="8.30e-3", replicated="N (authors: 'further studies are required to replicate')",
               uk_biobank_contributes="Y (UKB only)", clingen_dosage="not in local ClinGen region file under ZNF92 (not curated)", verdict="NOMINAL_UNREPLICATED",
               notes="Only positive association among 29 recurrent NDD CNV loci tested; nominal p, no multiple-testing survival stated; DELETION, so it is not positive-dosage evidence; previously linked (per authors' ref 43) to reduced schizophrenia risk."))

cr.append(dict(region_or_gene="GENOME-WIDE duplications (intolerant genes)", genes="all genes in CNVs >50 kb", build_coords="hg19 genome-wide", cnv_type="duplication (and deletion)",
               direction="duplication of LoF-intolerant genes LOWERS IQ (~0.8 IQ points per intolerant gene); deletions ~2.6 points",
               phenotype="general intelligence (IQ / g)", study="Huguet G et al. 2021 Mol Psychiatry (24,092 individuals); also Huguet 2018 JAMA Psychiatry (rare duplications not associated with PIQ)",
               pmid_or_doi="PMID:33414497; doi:10.1038/s41380-020-00985-z; PMID:29562078", n_carriers="genome-wide", effect="-0.8 IQ points per intolerant duplicated gene", p="see paper",
               replicated="Y (no heterogeneity across cohorts; extended in Huguet 2024)", uk_biobank_contributes="N (2021 cohorts pre-UKB; UKB added in 2024)",
               clingen_dosage="NA", verdict="CONTRADICTED", notes="Average effect of increased dosage on cognition is negative; no gene set reported as positive in these abstracts."))
cr.append(dict(region_or_gene="GENOME-WIDE functional-burden (172 tissue/cell-type gene sets)", genes="all protein-coding CNVs", build_coords="genome-wide", cnv_type="deletion and duplication",
               direction="most gene-dosage responses NON-monotonic: deletions and duplications show SAME-direction (harmful) effects; duplication pleiotropy lower than deletion",
               phenotype="43 traits incl. fluid intelligence, EA, TDI, VSWM", study="Kazem S et al. 2026 Nat Commun", pmid_or_doi="PMID:42736290; doi:10.1038/s41467-026-76676-0; PMC13575219",
               n_carriers="~500,000 UKB; replication All of Us", effect="duplication effect sizes UKB vs AoU r=0.42 (deletions r=0.91)", p="see paper",
               replicated="Y (All of Us, set level)", uk_biobank_contributes="Y (+ All of Us replication)", clingen_dosage="NA", verdict="CONTRADICTED",
               notes="Set-level; does not mention 2q12.3. Duplications replicate less well across cohorts than deletions."))
cr.append(dict(region_or_gene="PANEL of 33-53 neurodevelopmental CNVs", genes="recurrent pathogenic CNVs", build_coords="various", cnv_type="deletion and duplication",
               direction="24/33 CNVs associated with reduced cognitive performance or functioning; none reported as improving", phenotype="7 UKB cognitive tests, EA, occupation, income",
               study="Kendall KM et al. 2017 Biol Psychiatry; Kendall KM et al. 2019 Br J Psychiatry", pmid_or_doi="PMID:27773354; PMID:30767844; PMC6520248",
               n_carriers="1,087 SCZ-CNV + 484 other NDD-CNV carriers (2017)", effect="Z reductions 0.01-0.51; avg -0.13 SD (2019)", p="see papers", replicated="Y (consistent with other cohorts)",
               uk_biobank_contributes="Y", clingen_dosage="varies", verdict="CONTRADICTED", notes="No positive-direction CNV found in text searches of the 2019 full text."))
cr.append(dict(region_or_gene="PANEL of ASD/SCZ-risk CNVs", genes="recurrent CNVs", build_coords="various", cnv_type="deletion and duplication",
               direction="carriers without diagnosis perform worse on cognitive tests", phenotype="cognitive tests in controls", study="Stefansson H et al. 2014 Nature (deCODE, Iceland)",
               pmid_or_doi="PMID:24352232; doi:10.1038/nature12818", n_carriers="see paper", effect="see paper", p="see paper", replicated="Y (UKB Kendall 2017/2019 concordant)",
               uk_biobank_contributes="N (Iceland)", clingen_dosage="varies", verdict="CONTRADICTED", notes="Independent of UKB; abstract level only."))
cr.append(dict(region_or_gene="GENOME-WIDE CNV burden (Mb)", genes="all CNVs", build_coords="genome-wide", cnv_type="deletion and duplication",
               direction="higher CNV burden -> fewer years of education (EA_PROXY) and lower income", phenotype="educational attainment (EA_PROXY), income, TDI",
               study="Auwerx C et al. 2022 AJHG", pmid_or_doi="PMID:35240056; doi:10.1016/j.ajhg.2022.02.010; PMC9069145", n_carriers="UKB ~330k", effect="EA beta=-0.07 years/Mb",
               p="4.4e-11", replicated="NOT_TESTED", uk_biobank_contributes="Y", clingen_dosage="NA", verdict="CONTRADICTED", notes="EA_PROXY only; no positive cognitive CNV found in text search."))

cr.append(dict(region_or_gene="RIMS1 p.Arg820His (formerly R844H; CORD7 kindred)", genes="RIMS1", build_coords="GRCh38 6:72251007 G>A (ENST00000521978.5:c.2459G>A; mapped via Ensembl REST)",
               cnv_type="missense (not CNV; putative functional change)", direction="affected kindred members scored higher on verbal IQ / memory", phenotype="neuropsychological tests (verbal IQ, memory)",
               study="Sisodiya SM et al. 2007 J Med Genet; follow-ups Martin-Gutierrez 2022 IOVS; Paul 2022 Brain (Drosophila)", pmid_or_doi="PMID:17237123; PMID:35947379; PMID:35022694",
               n_carriers="single kindred (count not in abstract)", effect="see paper", p="see paper",
               replicated="N - no population association with common RIMS1 variation (same paper); no rare-variant population test found",
               uk_biobank_contributes="N", clingen_dosage="RIMS1 no gene dosage curation relevant; Collins pTriplo 0.955 (model)", verdict="NOMINAL_UNREPLICATED",
               notes=("ATTRIBUTION UNDERMINED: Martin-Gutierrez 2022 (Genomics England WGS) found the CORD7 retinal dystrophy fully explained by co-inherited PROM1 p.Arg373Cys; one affected member lacks the RIMS1 variant; RIMS1 p.Arg820His carrier frequency >1:5,000 in Europeans. "
                      "The cognitive claim is therefore a single-family observation confounded by a second segregating variant and by visual impairment. Drosophila knock-in shows increased release (mechanistic plausibility only). "
                      "Population test blocked: Genebass site 6-72251007-G-A has AN=15,628 and AC=0 (poorly captured in UKB exomes).")))
cr.append(dict(region_or_gene="CRB1 retinopathy (biallelic LoF)", genes="CRB1", build_coords="NA", cnv_type="biallelic LoF (disease)", direction="CRB1 retinopathy patients higher memory / verbal IQ than other retinopathies and norms",
               phenotype="list learning, verbal fluency, verbal IQ", study="Wright GA et al. 2024 Genes (Basel)", pmid_or_doi="PMID:38927596; doi:10.3390/genes15060660",
               n_carriers="small clinic sample (n not in abstract)", effect="see paper", p="0.001-0.037 (vs non-CRB1 retinopathy)", replicated="N", uk_biobank_contributes="N",
               clingen_dosage="DDG2P CRB1-related Leber congenital amaurosis (biallelic; definitive; LoF)", verdict="NOMINAL_UNREPLICATED",
               notes="Same London group/paradigm as RIMS1; small clinical sample; visual-impairment compensation confound (non-CRB1 retinopathy patients also exceeded norms). LoF disease -- not positive dosage."))
cr.append(dict(region_or_gene="APP A673T", genes="APP", build_coords="APP p.Ala673Thr", cnv_type="missense (reduces BACE1 cleavage / Abeta)", direction="carriers protected from AD and from age-related cognitive decline in elderly",
               phenotype="AD risk; cognitive decline in elderly without AD", study="Jonsson T et al. 2012 Nature (deCODE)", pmid_or_doi="PMID:22801501; doi:10.1038/nature11283",
               n_carriers="see paper (Nordic-enriched; rare elsewhere)", effect="see paper", p="see paper",
               replicated="Partial: Finnish elderly (Kero 2013, PMID:23102935); rare/absent in US and Chinese samples (PMID:25531812, 24126161)", uk_biobank_contributes="N",
               clingen_dosage="21q21.3 APP region TS=3 (APP duplication causes early-onset AD)", verdict="DISEASE_ONLY_NOT_POSITIVE",
               notes="Protection against neurodegeneration, not higher baseline cognition. Note the mirror: APP DUPLICATION (increased dosage) is pathogenic (ClinGen TS=3)."))
cr.append(dict(region_or_gene="APOE3 Christchurch (R136S)", genes="APOE", build_coords="APOE p.Arg136Ser", cnv_type="missense", direction="homozygote/heterozygotes with PSEN1-E280A show delayed cognitive impairment",
               phenotype="age at onset of ADAD dementia", study="Arboleda-Velasquez 2019; Quiroz YT et al. 2024 NEJM", pmid_or_doi="PMID:38899694; doi:10.1056/NEJMoa2308583",
               n_carriers="kindred-based (see paper)", effect="delayed onset (see paper)", p="see paper", replicated="Partial (heterozygote series in same kindred)", uk_biobank_contributes="N",
               clingen_dosage="NA", verdict="DISEASE_ONLY_NOT_POSITIVE", notes="Resilience to autosomal-dominant AD; not enhancement of normal cognition."))
cr.append(dict(region_or_gene="RELN-COLBOS (H3447R)", genes="RELN", build_coords="RELN p.His3447Arg", cnv_type="missense (reported gain of function of Reelin signalling)",
               direction="one PSEN1-E280A carrier cognitively intact to 67 y", phenotype="ADAD onset", study="Lopera F et al. 2023 Nat Med", pmid_or_doi="PMID:37188781; doi:10.1038/s41591-023-02318-3",
               n_carriers="1 (case report)", effect="NA", p="NA", replicated="N", uk_biobank_contributes="N", clingen_dosage="NA", verdict="DISEASE_ONLY_NOT_POSITIVE",
               notes="Single case; protection against ADAD only; RELN LoF causes lissencephaly -- a GoF claim resting on n=1."))
cr.append(dict(region_or_gene="KLOTHO KL-VS heterozygosity", genes="KL", build_coords="rs9536314 (F352V) + rs9527025 (C370S) haplotype", cnv_type="common coding haplotype (not rare, not CNV)",
               direction="claimed: heterozygotes better cognition; population replication null or opposite", phenotype="cognitive tests in older adults",
               study="Dubal DB et al. 2014 Cell Rep (claim); Mueller BW et al. 2021 Sci Rep (null); de Vries CF 2017 Neurobiol Aging (mixed)", pmid_or_doi="PMID:24813892; PMID:34226614; PMID:28431289",
               n_carriers="Mueller 2021: 1,812 subjects", effect="Mueller 2021: heterozygotes slightly LOWER (Z -0.04 to -0.17)", p="NS (Mueller 2021)",
               replicated="N (inconsistent)", uk_biobank_contributes="N", clingen_dosage="NA", verdict="CONTRADICTED",
               notes="Included because it is the most cited 'protective/enhancing' variant claim; largest population test found here does not support enhancement."))

with open(f"{ROOT}/reports/sprint5/cnv_positive_dosage.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=ccols)
    w.writeheader()
    for r in cr:
        w.writerow(r)
print("cnv rows", len(cr))

# ------------------------------------------------------------------ TASK C gene sets
import csv as _c
dd = list(_c.DictReader(open(DDG2P, encoding="utf-8")))
ID_HPO = {"HP:0001249", "HP:0001256", "HP:0002342", "HP:0010864", "HP:0002187", "HP:0006889", "HP:0001263", "HP:0011344", "HP:0011342", "HP:0011343"}
conf_ok = {"definitive", "strong"}
dd_conf = sorted({r["gene symbol"] for r in dd if r["confidence"] in conf_ok})
dd_id = sorted({r["gene symbol"] for r in dd if r["confidence"] in conf_ok and ID_HPO & {x.strip() for x in r["phenotypes"].split(";")}})
sha = hashlib.sha256(open(DDG2P, "rb").read()).hexdigest()
gs = {
    "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "definitions": {
        "exome_wide_cognition": "Gene with an exome-wide significant rare-coding association to a DIRECT cognitive measure (VNR/fluid intelligence, reaction time) in Chen 2023 (per-phenotype Bonferroni) or Genebass (SKAT-O 2.5e-7 / burden 6.7e-7) for fluid intelligence or reaction time. All are UK Biobank discoveries. Direction in every case: LoF/damaging carriers perform WORSE.",
        "exome_wide_cognition_incl_EA_proxy": "Above plus genes significant only for educational attainment (EA_PROXY) in Chen 2023 or Wu 2025.",
        "suggestive_cognition": "Chen 2023 FDR-only genes (NDUFA6, MAP1A are EDU; ARHGEF7, C11orf94, KIF26A are VNR) plus Genebass-only single-cohort hits with interpretability problems (ADAMTS6 missense FI; prospective-memory hits BRPF1, ASAP1, NACC1 with non-monotone phenotype coding). C11orf94 carriers scored HIGHER (LoF, FDR only).",
    },
    "exome_wide_cognition": ["ANKRD12", "CACNA1A", "KDM5B", "RC3H2"],
    "exome_wide_cognition_incl_EA_proxy": ["ADGRB2", "ANKRD12", "BCAS3", "CACNA1A", "GIGYF1", "KDM5B", "RC3H2", "SLC8A1"],
    "suggestive_cognition": ["ADAMTS6", "ARHGEF7", "ASAP1", "BRPF1", "C11orf94", "KIF26A", "MAP1A", "NACC1", "NDUFA6"],
    "excluded_with_reason": {
        "AC011448.1": "Genebass RT missense SKAT-O hit in pleiotropic 19p13.11 region; likely LD artefact",
        "APOC1/LRP1": "Chakraborty & Kahali 2023 candidate-gene all-variant SKAT; not rare-coding exome-wide",
        "CACNA1A_caveat": "Chen Table 1 flags CACNA1A VNR as study-wide significant although P=1.33e-6 > stated 1.15e-6; retained on per-phenotype Bonferroni",
        "BCAS3_caveat": "EDU only; passes per-phenotype Bonferroni (3.17e-6) not study-wide 1.15e-6",
    },
    "independence_note": "Every exome-wide gene here was discovered in UK Biobank; Genebass and Wu 2025 re-analyse the SAME participants. Gene-level replication outside UKB: none significant (only 8-gene SET replication in Finnish cohorts; KDM5B and GIGYF1 nominal for DD/ID in NFID).",
    "dd_id_genes_source": f"Gene2Phenotype DD panel CSV, https://www.ebi.ac.uk/gene2phenotype/api/panel/DD/download/ (retrieved 2026-09-23; sha256 {sha}; 2,866 records)",
    "dd_confirmed_definitive_or_strong": dd_conf,
    "dd_id_confirmed": dd_id,
    "dd_id_confirmed_definition": "DDG2P DD-panel genes with confidence definitive/strong AND at least one explicitly listed HPO term among intellectual disability (HP:0001249 and mild/moderate/severe/profound/borderline children) or global developmental delay (HP:0001263, HP:0011342-4). HPO descendants beyond this explicit list were NOT expanded; genes whose ID is encoded only by other terms are missed.",
    "counts": {"dd_confirmed_definitive_or_strong": len(dd_conf), "dd_id_confirmed": len(dd_id)},
}
ov = {g: (g in dd_conf, g in dd_id) for g in gs["exome_wide_cognition_incl_EA_proxy"] + gs["suggestive_cognition"]}
gs["overlap_with_ddg2p"] = {g: {"dd_confirmed": a, "dd_id_confirmed": b} for g, (a, b) in ov.items()}
os.makedirs(f"{ROOT}/data/sprint5", exist_ok=True)
json.dump(gs, open(f"{ROOT}/data/sprint5/rare_coding_gene_sets.json", "w"), indent=2)
print("dd_conf", len(dd_conf), "dd_id", len(dd_id), ov)
