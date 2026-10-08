# AML patient eligibility flags

**Definition id:** `aml_eligibility_flags`
**Aliases:** DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, TX_POST_DX_FLG, ARSENIC_FLG, TX_TXL_MX_ELIG_FLG, TX_TXL_RX_ELIG_FLG, TX_MX_LB_ELIG_VEN_FLG, TX_RX_LB_ELIG_VEN_FLG, TX_TXL_MX_ELIG_VEN_FLG, TX_TXL_RX_ELIG_VEN_FLG, SCT_PX_FLG, SCT_DX_FLG, SCT_DX_PX_FLG, MX_ACTIVITY_FINAL_FLAG, RX_ACTIVITY_FINAL_FLAG, VEN_POST_DX_FLG, 2M LF, 2M_LF, PATIENT_INTENSITY, PATIENT_COHORT, PATIENT_COHORT_UPDATED, Patient Cohort Intensity Flag, IC Elig, IC Inelig, IC Eligible, IC Ineligible
**Working behavior:** Read the flags from the production flags table. Derive VEN_POST_DX_FLG and 2M_LF at query time because they are not stored.

## Definition
The AML eligibility flags are a second gate applied per KPI on top of population membership. They never
change the patient pool. Each flag answers whether the patient's record is complete enough for the KPI.
There is one row per patient in
`Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL`
(columns: PATIENT_GID, FIRST_DX, FIRST_TX, LAST_TX, the flags below, PATIENT_COHORT,
PATIENT_COHORT_UPDATED).

| Stored flag | V5 guide name | Rule as coded (1 = passes) |
|---|---|---|
| DX_LB_ELIG_FLG | DX_LB_ELIG_FLG | Any Mx **or** Rx claim in [FIRST_DX − 6m, FIRST_DX) **and** any Mx or Rx claim in [FIRST_DX − 12m, FIRST_DX − 6m). Exact claim dates, two rolling 6-month windows. |
| TX_TXL_MX_ELIG_FLG | MX_ACTIVITY_FINAL_FLAG | Mx activity in every rolling 6-month interval from FIRST_TX to LAST_TX (anchored on FIRST_TX + n×6 months). A span shorter than 6 months passes automatically. |
| TX_TXL_RX_ELIG_FLG | RX_ACTIVITY_FINAL_FLAG | Same as above, on Rx activity. |
| TX_MX_LB_ELIG_VEN_FLG | (new) | Mx activity in every **calendar** semester from the semester of VEN_START − 12m to the semester of VEN_START, capped at the last complete semester (`exc_dt`). |
| TX_RX_LB_ELIG_VEN_FLG | (new) | Same, on Rx activity. |
| TX_TXL_MX_ELIG_VEN_FLG | (new) | Mx activity in every rolling 6-month interval from VEN_START to VEN_END. A span under 6 months, or no Venclexta at all, passes. |
| TX_TXL_RX_ELIG_VEN_FLG | (new) | Same, on Rx activity. |
| DX_TX_DIFF_FLG | DX_TX_DIFF_FLG | 0 ≤ DATEDIFF(FIRST_TX, FIRST_DX) ≤ 60. |
| TX_POST_DX_FLG | (new) | FIRST_TX ≥ FIRST_DX. A 0 is a data-quality signal. |
| ARSENIC_FLG | ARSENIC_FLG | **1 = no arsenic trioxide in any regimen** (keep), 0 = arsenic exposure (likely APL, exclude). COALESCE to 1 when the patient has no regimen rows. |
| SCT_PX_FLG | (new) | First SCT procedure (51-code list, Sx or Px fact) ≥ FIRST_DX. |
| SCT_DX_FLG | (new) | First SCT-history diagnosis (Z94.84, V42.82) ≥ FIRST_DX. |
| SCT_DX_PX_FLG | (new) | Either of the two. |
| PATIENT_COHORT | PATIENT_INTENSITY | legacy-rule intensity (IC_ELIG / IC_INELIG); see `reference_codes_and_mappings.md`. |
| PATIENT_COHORT_UPDATED | (new) | new-definition intensity (age + line-1 product). |
| — not stored — | VEN_POST_DX_FLG | "VEN start should be post first AML Dx": derive as VEN_START ≥ FIRST_DX (VEN_START from `MABI_AML_LOT_PAT_FST_DX_TX_TBL_*`). |
| — not stored — | 2M LF | "At least 2M gap between VEN start and data end": derive as ADD_MONTHS(VEN_START, 2) ≤ data cut. |

TX_MX_LB_ELIG_FLG and TX_RX_LB_ELIG_FLG (lookback from AML treatment start) are commented out and do not
exist in the table.

## Calculation
```text
# Which flags gate which KPI. The guide's table is mapped onto the stored columns.
# Y = filter = 1 (ARSENIC_FLG = 1 means "no arsenic").
# flag (stored name)                         | NPS Share | SCT | BMB
# DX_LB_ELIG_FLG                             |     Y     |  Y  |  Y
# DX_TX_DIFF_FLG                             |     Y     |  Y  |  Y
# ARSENIC_FLG                                |     Y     |  Y  |  Y
# TX_TXL_MX_ELIG_FLG (MX_ACTIVITY_FINAL)     |     N     |  Y  |  Y
# TX_TXL_RX_ELIG_FLG (RX_ACTIVITY_FINAL)     |     N     |  Y  |  Y
# VEN_POST_DX_FLG (derive)                   |     N     |  N  |  Y
# 2M_LF (derive)                             |     N     |  N  |  Y
# PATIENT_COHORT (intensity cut)             |     Y     |  Y  |  Y
#
# The VEN-anchored flags (TX_*_VEN_FLG) are not assigned to a KPI in the guide. Use them when the KPI is
# measured from Venclexta start rather than from AML treatment start, and name the anchor.
#
# Activity sources used by the production build:
#   Mx exact dates: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_MX_ACT_TBL_AML_EXACT_DATES_KA_v2
#        = DISTINCT (patient, claim_date) of claims-view rows with source_type LIKE '%PX%'/'%SX%'/'%DX%'
#          UNION abv_val_ptd_onc_synd.dx_fact_curated_vw (no market filter)
#   Rx exact dates: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA
#        = DISTINCT (patient, claim_date) of claims-view rows with source_type LIKE '%RX%'
#   (the claims-view reads for these two tables have no source_flag/source_market filter)
#   VEN lookback flags: semesterly activity from abv_val_ptd_synd_work.mapping_mx/rx_activity_freq_tbl
#        (source_flag='SHA_PTD', source_market='ONC', FREQUENCY='SEMESTERLY', OFFSET='0'; no
#        market_code filter in this build) against the calendar-semester spine of VENC_AML 'RX FACT' claims.
```

## Grain and dimensions
One row of flags per patient (PATIENT_GID with the `SHA_PTDONC` suffix kept)

AML base-layer cohort; SHA_PTD. The Aug'26 build has 84,199 patients. Production pass counts (Aug'26):
DX_LB_ELIG 66,568; TX_TXL_MX 80,765; TX_TXL_RX 77,879; TX_TXL_MX_VEN 82,940; TX_TXL_RX_VEN 84,012.

## Source tables
Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL (and the
`_v2` validation copy); inputs are listed in `context/data/tables/z_abv_cws_mabi_onc_analytics_mabi_aml_lot_pat_elig_flags_final/profile.md`.

## Caveats
- **Calendar vs actual (configurable).** `semester.semester_type` in `config/eligibility.yaml` chooses
  how each flag group's 6-month periods are built. The logic is in `config/semester.py`.
  - `calendar`: fixed Jan–Jun / Jul–Dec halves, taken from the claim date.
  - `actual`: rolling 6-month windows from each patient's anchor.
  - The groups are `dx_lookback` (DX_LB), `journey_continuity` (the four TXL flags) and `ven_lookback`
    (TX_MX/RX_LB_ELIG_VEN).
  - The default (actual / actual / calendar) reproduces the original build exactly. A single value
    (`semester_type: calendar`) switches every flag.
  - The business-rules page describes semesters, which matches only the VEN lookback default. Name the
    methodology in any answer.
- **Page coverage.** The page's current revision describes five flags: DX_LB, TX_TXL_MX, TX_TXL_RX and
  TX_MX/RX_LB_ELIG_VEN. It no longer describes the two VEN continuity flags, DX_TX_DIFF_FLG,
  TX_POST_DX_FLG, the SCT flags or the ARSENIC_FLG default. All of these are still produced by
  `AML_PATIENT_ELIGIBILITY`, and the definitions above come from the code (OI-15).
- **Short spans pass.** Patients whose AML (or VEN) journey is under 6 months pass the continuity flags
  without any test. In the Aug'26 build that was 47,195 of 84,199 for the AML journey and 75,238 for the
  VEN journey. Patients who never took Venclexta pass both TXL VEN flags, so filter on VEN_START IS NOT
  NULL before using them.
- **Mx activity is not market-limited here.** The exact-date Mx table includes every PX/SX/DX claim and
  all `dx_fact_curated_vw` rows. This is wider than the V5 rule "Mx activity table contains Market
  (ONC) claims only". The semesterly activity tables used by the VEN lookback flags are ONC-scoped but
  omit `market_code='ONC'`, which SME Q-10 requires elsewhere.
- **ARSENIC_FLG polarity.** 1 means no arsenic. Filter `ARSENIC_FLG = 1` to exclude likely-APL patients.
- **TX_POST_DX_FLG vs DX_TX_DIFF_FLG.** The second implies the first. Use DX_TX_DIFF_FLG for KPIs.
- **Do not mix with CLL rules.** These flags are not interchangeable with the CLL three-year eligibility
  rule (Venclexta pack): "AML analyses require a shorter lookback and post treatment history to capture a complete cycle,
  whereas CLL needs a longer timeframe to avoid dropping patients prematurely".
- Report the share removed by each applied flag; flag any screen removing more than 20% (SME Q-63).

## Source lineage
- original team notebook Patient Eligibility.ipynb · cells 138–312
- scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb (all flags)
- AML_Base_Business_Rule.html · Section 10 (eligibility flags);
  the SCT/timing/arsenic flags are in Section 10 of the archived 2026-10-01 revision (removed from the pack; a copy is in `aml_context_pack_kbt.zip`)
- AML SHA Business Rules Guide V5.pptx · slides 16, 17 and 18 (flag-to-KPI table)
