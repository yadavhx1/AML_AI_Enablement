# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_FINAL_DATA_MONTH_ROLLUP_UPDATED_BUSINESS_RULES_v2

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 4, metric `nps_dashboard_legacy`.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** SHA AML NPS by reported month, account subtype and Academic / Community group
**Common analyses:** aml_nps_by_account, aml_nps_indexing

## Grain

One row per reported month x account subtype (one NULL row for a month with no SHA starts). (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 94-101)

## Primary keys or entity keys

MONTH_REPO + ACCT_SUB_TYPE.

## Row meaning

Starts in one month at one account subtype.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. Counts DISTINCT patient x backbone x line start x subtype rows of the dashboard temp view by month of line start.
2. Academic = Elite Oncology Center or Academic Teaching Hospital; every other subtype, including Not Available and Federal, = Community.

## Join guidance

MONTH_REPO to the index table.

## Caveats

1. Every line, both intensities, no gates, despite 1L_IC_INELIG in the name.
2. Same spark.stop() ordering issue as the index table.
3. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
4. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
5. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
6. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 94-101

**Source document:** the notebook above (annotated team code).
