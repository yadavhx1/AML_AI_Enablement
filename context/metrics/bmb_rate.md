# BMB rate (bone marrow biopsy)

**Metric id:** `bmb_rate`
**Aliases:** BMB Rate, BMB rate, VEN Cycle 1 BMB rate, VEN Overall BMB rate
**Working behavior:** Use the documented definition and calculation.

## Definition
VEN Cycle 1 BMB rate for a given semester (based on VEN Tx start date) = # VEN Cycle 1 Patients / Overall #VEN Patients. VEN Overall BMB rate for a given semester (based on VEN Tx start date) = # VEN BMB Patients / Overall #VEN Patients.

## Calculation
```text
# Cycle 1 test, verbatim:
#   "If the 1st BMB date for a given patient is <=45 days after VEN start date means that
#    patient has underwent VEN Cycle 1 BMB. Any other BMB instance later than 45 days should
#    still be counted as BMB done in subsequent cycles."
# Window, verbatim:
#   "BMB claim date should be between the VEN start and VEN end date to ensure the BMB
#    procedure is used to assess the impact of VEN based therapy"
# Multiplicity, verbatim:
#   "There can be multiple more than 1 instances of BMB for a given patient. Flag the BMB
#    dates in patient journey and calculate the gap between VEN start date and different BMB
#    instances."
```

## Grain and dimensions
One rate per semester, based on VEN Tx start date

Filters applied: ARSENIC_FLG (= 1), DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, VEN_POST_DX_FLG (derive: VEN_START >= FIRST_DX), MX_ACTIVITY_FINAL_FLAG (TX_TXL_MX_ELIG_FLG), RX_ACTIVITY_FINAL_FLAG (TX_TXL_RX_ELIG_FLG), 2M_LF (derive: ADD_MONTHS(VEN_START, 2) <= data cut), LOT (Optional)

## Source tables
Cohort and gates: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*` and
`MABI_AML_LOT_PAT_FST_DX_TX_TBL_*` (VEN_START, VEN_END, FIRST_DX). The BMB claims (20 codes) are not
built into the base layer; read them from the procedure/surgical fact views.

## Caveats
Denominator: "Overall #VEN Patients", the EL-4 definition for the procedure-rate family (SME Q-60). Two distinct rates share the name BMB rate — the Cycle 1 rate and the Overall rate — and they differ only in numerator. State which one is meant. "Can be done semesterly if low n size". The BMB filter set is stricter than the SCT set: it adds VEN_POST_DX_FLG and 2M_LF, so BMB and SCT rates are computed on different denominators and must not be compared directly. BMB code list (20 codes) is in context/domain/reference_codes_and_mappings.md. VEN_POST_DX_FLG and 2M_LF are not stored in the flags table and must be derived (open item OI-11).

## Source lineage
- AML SHA Business Rules Guide V5.pptx · slide 21
