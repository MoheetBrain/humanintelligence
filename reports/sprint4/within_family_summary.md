# Gate A — within-family (Howe 2022) summary

**Status: NOT_TESTABLE — blocked at the access boundary; not evidence of absence.**

- Checked: `OPENGWAS_JWT` present = False (2026-09-23T15:39:20Z).
- Blocker: OPENGWAS_JWT absent; OpenGWAS automated download requires a JWT and this project does not create accounts or automate website downloads.
- Minimal user action: Set OPENGWAS_JWT (a token from https://api.opengwas.io/profile/ after signing in) in the shell environment, then run: python pipelines/sprint4/gate_a_within_family.py fetch && python pipelines/sprint4/gate_a_within_family.py analyse
- Alternative: Or, without any token: open https://gwas.mrcieu.ac.uk/datasets/ieu-b-4837/ and https://gwas.mrcieu.ac.uk/datasets/ieu-b-4838/, click 'VCF Files', and save both .vcf.gz files into data/interim/sprint4/opengwas/ (the website allows 20 datasets/day), then run the analyse command.

- **Identity (public metadata):**
  - ieu-b-4837: Cognitive function, sibling estimate, N=9,997.
  - ieu-b-4838: population estimate, N=22,593.
  - Howe LJ 2022; Within family GWAS consortium; HG19/GRCh37.
  - UK Biobank contributes 8,061 of the 27,638 individuals in Howe's cognition analysis, so Gate A tests direct vs population effects, not independence.
- **Ready to run:** `gate_a_within_family.py analyse`. It covers:
  - VCF parse and identity check;
  - N_eff from the SE ratio;
  - MAGMA gene and frozen set models;
  - post-data calibration (the Howe population GWAS subsampled to N_eff);
  - set classes, attenuation with bootstrap and Fieller CIs;
  - locus concordance, slope and rank preservation.
- **Pre-data calibration:** see `within_family_power_calibration.json`.

