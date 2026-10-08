---
name: kbt-05-patient-eligibility
description: Use for AML base-layer questions about patient eligibility flags, diagnosis lookback, Mx/Rx activity continuity, Venclexta-anchored lookback or continuity, first diagnosis and first treatment dates, time from diagnosis to treatment, arsenic/APL exclusion, stem cell transplant flags, SCT or BMB rate cohorts, or which patients a KPI may count (`AML_PATIENT_ELIGIBILITY`).
user-invocable: true
---


# KBT 5 - Patient eligibility (AML_PATIENT_ELIGIBILITY)

## Analytical intent

Use this KBT when the output depends on which patients pass the AML KPI gates, on the anchor dates
(first diagnosis, first/last treatment, Venclexta start/end), or on the transplant and arsenic flags.
This includes SCT and BMB rates, diagnosis-to-treatment timing, and gated new-patient-start or share
figures.

Notebook: `scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb`.

## Method

1. Anchor dates (`MABI_AML_LOT_PAT_FST_DX_TX_TBL_*`):
   - FIRST_DX = earliest diagnosis on the 37 AML codes.
   - FIRST_TX / LAST_TX = MIN regimen start / MAX regimen end.
   - VEN_START / VEN_END = Venclexta episode bounds (NULL without Venclexta).
2. Exact-date activity tables: Mx = PX/SX/DX claims plus all diagnosis rows; Rx = RX claims. Both cover
   patients on the combined LoT table.
3. Flags (1 = passes). The 6-month periods follow `semester.semester_type` (`calendar` or `actual`, per
   flag group, in `config/eligibility.yaml`). The defaults are shown and reproduce the original build:
   - DX_LB_ELIG_FLG (`dx_lookback`, default actual): activity in both [FIRST_DX − 6m, FIRST_DX) and
     [FIRST_DX − 12m, FIRST_DX − 6m). In calendar mode: every calendar semester from
     semester(FIRST_DX − 12m) to semester(FIRST_DX).
   - TX_TXL_MX/RX_ELIG_FLG (`journey_continuity`, default actual): activity in every rolling 6-month
     interval from FIRST_TX to LAST_TX. In calendar mode: every calendar semester in that span.
   - TX_TXL_MX/RX_ELIG_VEN_FLG (`journey_continuity`): the same from VEN_START to VEN_END.
   - TX_MX/RX_LB_ELIG_VEN_FLG (`ven_lookback`, default calendar): activity in every calendar semester
     of the 12 months up to VEN_START, capped at `{exc_dt}`. In actual mode: the two rolling 6-month
     windows before VEN_START.
   - DX_TX_DIFF_FLG: 0 ≤ FIRST_TX − FIRST_DX ≤ 60 days.
   - TX_POST_DX_FLG: FIRST_TX ≥ FIRST_DX.
   - ARSENIC_FLG: 1 = no arsenic trioxide (keep).
   - SCT_PX_FLG / SCT_DX_FLG / SCT_DX_PX_FLG: SCT on or after FIRST_DX.
   - PATIENT_COHORT (the build's intensity: legacy rule by default) / PATIENT_COHORT_UPDATED
     (new-definition class).
4. Apply the KPI's gate set (`AML_KPI_FLAG_SET`):
   - NPS share: ARSENIC_FLG, DX_LB_ELIG_FLG, DX_TX_DIFF_FLG.
   - SCT: the NPS-share set plus TX_TXL_MX_ELIG_FLG and TX_TXL_RX_ELIG_FLG.
   - BMB: the SCT set plus the derived VEN_POST_DX_FLG (VEN_START ≥ FIRST_DX) and 2M_LF
     (VEN_START + 2 months ≤ data cut).
5. VEN-based rates: the denominator is patients with VEN_START in the period ("Overall #VEN Patients").
   Filter VEN_START IS NOT NULL before using the VEN continuity flags, because non-VEN patients pass
   them.
6. Report the share removed by each flag, and flag any screen removing more than 20%.
7. Validate: no NULL FIRST_DX / LAST_TX; flag counts against the reference counts in the flags profile.

## Working defaults

- Gate set: by KPI as above. ARSENIC_FLG = 1 always.
- Semester methodology: the shipped config (actual / actual / calendar). State the methodology used,
  and never compare flag counts built under different `semester_type` settings without saying so.
- `{exc_dt}`: first day of the last semester with complete data (2025-07-01 in the Aug'26 run).
- SCT codes: the production 51-code procedure list plus Z94.84 / V42.82 (`AML_SCT_CODE_SET`).
- Table suffix: AML_PATIENT_ELIGIBILITY reads and writes un-suffixed `_BUSINESS_RULE_CHANGE_VAL` tables, while
  the four AML_LOT notebooks write `_v2`. Align the suffix before running (OI-02).
- Rates by semester when monthly bases are small.

## Context to read

- `context/domain/aml_eligibility_flags.md`
- `context/metrics/sct_rate.md`, `bmb_rate.md` as needed
- `context/domain/time_to_treatment.md` as needed
- `context/domain/reference_codes_and_mappings.md` (SCT, BMB, AML diagnosis codes)
- Profiles for the first Dx/Tx, activity and flags tables
- `context/data/source_dictionaries/` (README "Points that matter") only when the question goes below
  the view:
  - FIRST_DX reads the first-position diagnosis only (SHA has 11 positions);
  - SHA birth year is adjusted for age 76 and over, which matters for age cuts above 75;
  - activity, coverage or enrollment screens: SHA panels, Komodo `MX_CLOSED` / `RX_CLOSED`, none used
    by the base layer;
  - Komodo diagnosis parsing.
  Never query the raw tables.

## Verified-query candidates

- `AML_FIRST_DX_TX`, `AML_EXACT_DATE_ACTIVITY`, `AML_DX_LOOKBACK_ELIG`, `AML_TXL_MX_ELIG`,
  `AML_TXL_RX_ELIG`, `AML_TXL_MX_VEN_ELIG`, `AML_TXL_RX_VEN_ELIG`, `AML_VEN_MX_LOOKBACK_ELIG`,
  `AML_VEN_RX_LOOKBACK_ELIG`, `AML_FINAL_ELIG_FLAGS`.

## Minimum QC

- The gate set is named, and the removal share is reported for each flag.
- ARSENIC_FLG polarity is correct (1 = keep).
- The denominator does not depend on having the procedure (SCT/BMB).
- The build suffix is consistent across all joined tables.


## Output contract

Return the requested result first. State the data source, gates applied, denominator, period, build
suffix and material assumptions. Keep patient identifiers out of the response.
End with the `How this answer was generated` provenance table and append it to `outputs/response_log.md` (`context/response_provenance.md`).
