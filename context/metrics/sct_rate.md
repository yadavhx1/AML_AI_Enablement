# SCT rate (stem cell transplant)

**Metric id:** `sct_rate`
**Aliases:** SCT Rate, SCT rate, SCT for a given semester
**Working behavior:** Use the documented definition and calculation.

## Definition
SCT for a given semester (based on VEN Tx start date) = # SCT Patients / Overall #VEN Patients

## Calculation
```text
numerator:   # SCT Patients   -- "the count of those who have undergone SCT (SCT post first
                              --  AML diagnosis)" among patients initiating VEN in the semester
denominator: Overall #VEN Patients  -- "The number of patients initiating a VEN regimen in a
                                    --  given semester"
# Final SCT date per patient, verbatim:
#   "Primary Source: If SCT from Tx is present, consider first SCT date from here.
#    Secondary Source: If SCT from Tx is missing but SCT from Dx is available, then consider
#    first SCT date from Dx table.
#    Fallback Value: If neither SCT from Tx nor from Dx is available, then no SCT date
#    information exists."
# VEN Start Date = "the minimum regimen start date among all VEN regimens for a given patient"
```

## Grain and dimensions
One rate per semester, based on VEN Tx start date

Filters applied: ARSENIC_FLG (= 1, no arsenic), DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, MX_ACTIVITY_FINAL_FLAG (stored as TX_TXL_MX_ELIG_FLG), RX_ACTIVITY_FINAL_FLAG (stored as TX_TXL_RX_ELIG_FLG), LOT (Optional)

## Source tables
AML base layer: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*` (SCT_PX_FLG,
SCT_DX_FLG, SCT_DX_PX_FLG and the gating flags) joined to `MABI_AML_LOT_PAT_FST_DX_TX_TBL_*` (VEN_START
for the semester). SCT procedure source: `abv_val_ptd_onc_synd.sx_fact_curated_vw` and
`px_fact_curated_vw`. SCT Dx source: `dx_fact_curated_vw`.

## Caveats
Denominator: "Overall #VEN Patients" is the intended denominator for procedure rates, because every VEN patient could in principle receive one. It is the EL-4 definition for the procedure-rate family only (SME Q-60). "Can be done semesterly if low n size" — the semester grain exists because monthly bases are too small. SCT must be looked for in both tables in the stated order; checking only one understates the rate. SCT code lists are in context/domain/reference_codes_and_mappings.md. The production SCT_PX_FLG uses 51 of the 110 Tx codes (default `AML_SCT_CODE_SET`); use 110 only as a sensitivity. The stored SCT flags need SCT on or after FIRST_DX; that is the "SCT post first AML diagnosis" condition. Restrict to VEN_START IS NOT NULL for the denominator.

## Source lineage
- AML SHA Business Rules Guide V5.pptx · slide 20
- scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb (SCT_PX/DX flags). The business-rules page
  section on SCT flags was removed in the 2026-10-07 revision; it is in the archived 2026-10-01 revision (removed from the pack; a copy is in `aml_context_pack_kbt.zip`).
