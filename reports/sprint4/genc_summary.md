# Gate B — independent Genes & Cognition summary

- **Cohort:** NIHR BioResource Genes & Cognition, N=9,932, G&C-only files.
  - UK Biobank and meta-analysis files are forbidden by test.
  - UKB-free by recruitment; the source paper gives no explicit no-overlap statement.
- **Phenotype:** EXECUTIVE_FUNCTION (trail making), not GENERAL_COGNITION.
  - TMA (alphanumeric) is primary; TMN and TMD are secondary.
  - Higher values are slower.
  - rg(TMA, intelligence) = −0.752.

- **Positive control:** NT5DC2 rs7639267 → **PASS**.
  - Ours: β=0.00616, P=0.0018.
  - Published: β=0.0062, P=0.0018.
- **Loci:**
  - 109/145 concordant, binomial P=5.0e-10.
  - Slope 0.122 (SE 0.014).
  - G&C_SUPPORTED: 33 (~14.5 expected by chance).
  - Status counts: {'TESTABLE': 145, 'UNRESOLVED_HARMONISATION': 10, 'NOT_TESTABLE_ABSENT_NO_PROXY': 4}.

## Frozen sets

| phenotype | spec | set | β | P | class |
|---|---|---|---|---|---|
| TMA | frozen_sprint3_spec | GO_0045202 | +0.027 | 0.137 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | frozen_sprint3_spec | SYNGO_synprocess | +0.052 | 0.031 | INDEPENDENT_SUPPORT  |
| TMA | frozen_sprint3_spec | GO_0042734 | +0.050 | 0.238 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | frozen_sprint3_spec | GO_0099056 | +0.059 | 0.226 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | frozen_sprint3_spec | GO_0099560 | -0.093 | 0.761 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMA | frozen_sprint3_spec | GO_0099508 | +0.336 | 0.068 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | sensitivity_full_universe_D | GO_0045202 | +0.017 | 0.248 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | sensitivity_full_universe_D | SYNGO_synprocess | +0.042 | 0.063 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | sensitivity_full_universe_D | GO_0042734 | +0.043 | 0.272 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | sensitivity_full_universe_D | GO_0099056 | +0.050 | 0.261 | CONCORDANT_BUT_UNDERPOWERED  |
| TMA | sensitivity_full_universe_D | GO_0099560 | -0.089 | 0.753 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMA | sensitivity_full_universe_D | GO_0099508 | +0.332 | 0.070 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | frozen_sprint3_spec | GO_0045202 | +0.004 | 0.439 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | frozen_sprint3_spec | SYNGO_synprocess | -0.015 | 0.702 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMN | frozen_sprint3_spec | GO_0042734 | +0.007 | 0.460 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | frozen_sprint3_spec | GO_0099056 | +0.002 | 0.491 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | frozen_sprint3_spec | GO_0099560 | -0.060 | 0.676 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMN | frozen_sprint3_spec | GO_0099508 | +0.142 | 0.263 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | sensitivity_full_universe_D | GO_0045202 | +0.005 | 0.418 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | sensitivity_full_universe_D | SYNGO_synprocess | -0.020 | 0.763 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMN | sensitivity_full_universe_D | GO_0042734 | +0.005 | 0.474 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | sensitivity_full_universe_D | GO_0099056 | +0.001 | 0.497 | CONCORDANT_BUT_UNDERPOWERED  |
| TMN | sensitivity_full_universe_D | GO_0099560 | -0.049 | 0.648 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMN | sensitivity_full_universe_D | GO_0099508 | +0.139 | 0.268 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | frozen_sprint3_spec | GO_0045202 | +0.027 | 0.138 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | frozen_sprint3_spec | SYNGO_synprocess | +0.006 | 0.421 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | frozen_sprint3_spec | GO_0042734 | +0.079 | 0.129 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | frozen_sprint3_spec | GO_0099056 | +0.066 | 0.197 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | frozen_sprint3_spec | GO_0099560 | -0.019 | 0.558 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMD | frozen_sprint3_spec | GO_0099508 | -0.007 | 0.512 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMD | sensitivity_full_universe_D | GO_0045202 | +0.018 | 0.235 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | sensitivity_full_universe_D | SYNGO_synprocess | -0.006 | 0.585 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMD | sensitivity_full_universe_D | GO_0042734 | +0.076 | 0.140 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | sensitivity_full_universe_D | GO_0099056 | +0.063 | 0.210 | CONCORDANT_BUT_UNDERPOWERED  |
| TMD | sensitivity_full_universe_D | GO_0099560 | -0.031 | 0.593 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
| TMD | sensitivity_full_universe_D | GO_0099508 | -0.015 | 0.527 | INCONSISTENT SIGN_DISCORDANT_WITHIN_NOISE |
