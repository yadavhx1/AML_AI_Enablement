# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_LOT_MONTH_NPS_SUMMARY_UPDATED_BUSINESS_RULES_v2_SATEEK

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 4, metric `nps_dashboard_legacy`.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** AML NPS volume and VEN / HMA / other share by eligibility flags, legacy-rule cohort, line of therapy and month
**Common analyses:** aml_nps_by_lot, aml_nps_share, aml_nps_dashboard

## Grain

One row per DX_LB_ELIG_FLG x DX_TX_DIFF_FLG x PATIENT_COHORT x LOT x month. (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 75-85)

## Primary keys or entity keys

All dimension columns.

## Row meaning

Starts and shares for one slice in one month.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. Counts DISTINCT patient x line rows of the dashboard table, flags LEFT-joined from the eligibility table (-1 / Not Available when unmatched).
2. Month = line END month in the shipped notebook (SUMMARY_TIME_BASIS = 'END'), from 2019 (OI-17).
3. Published Summary sheet: DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1, PATIENT_COHORT = 'IC_INELIG', LOT = 1, months summed to semesters and shares recomputed.

## Join guidance

None; aggregate table.

## Caveats

1. TOTAL_NPS is per slice: filter to one slice before summing. Never average monthly shares; recompute from volumes.
2. ARSENIC_FLG is not applied. For IC_INELIG this has no effect (legacy rule puts arsenic patients in IC_ELIG); apply it for IC_ELIG.
3. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
4. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
5. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
6. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 75-85

**Source document:** the notebook above (annotated team code).
