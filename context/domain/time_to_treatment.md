# Time to treatment (AML)

**Definition id:** `time_to_treatment`
**Aliases:** TIME_TO_TREATMENT, time to treatment, Dx to Tx, DX_TX_DIFF
**Working behavior:** Use the documented definition and calculation.

## Definition
Elapsed days between a patient's first AML diagnosis and first AML treatment.

## Calculation
```text
TIME_TO_TREATMENT = DATEDIFF(FIRST_TX, FIRST_DX)          -- MABI_AML_LOT_PAT_FST_DX_TX_TBL_*
DX_TX_DIFF_FLG    = 1 when 0 <= TIME_TO_TREATMENT <= 60   -- flags table
```

## Grain and dimensions
One value per patient

## Source tables
MABI_AML_LOT_PAT_FST_DX_TX_TBL_*; MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*

## Caveats
FIRST_DX is the earliest claim on the 37 AML codes (first-position code only), not the onset date.
Negative values (treatment before the first observed diagnosis) are a data-quality signal
(TX_POST_DX_FLG = 0); isolate them. Report median and mean with the distribution.

## Source lineage
- scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb
