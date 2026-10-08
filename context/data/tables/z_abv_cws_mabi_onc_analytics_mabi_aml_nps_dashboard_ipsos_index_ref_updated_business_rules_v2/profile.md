# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_UPDATED_BUSINESS_RULES_v2

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 4, metric `nps_dashboard_legacy`.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** Reported (Ipsos) Venclexta and total AML NPS per month next to the SHA counts from the dashboard
**Common analyses:** aml_nps_indexing

## Grain

One row per reported month from 2019-01. (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 89-93)

## Primary keys or entity keys

MONTH_REPO.

## Row meaning

Reported vs observed new patient starts for one month.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. Reported values from MABI_AML_NPS_DASHBOARD_REPOSITORY (MONTH_REP as MM/dd/yyyy); reload it before the run.
2. SHA values: rows of the dashboard temp view by month of line start; VEN = BACKBONE VENCLEXTA.

## Join guidance

MONTH_REPO to the rollup table.

## Caveats

1. SHA counts are every line, both intensities, no gates, not de-duplicated; not comparable to the gated 1L share.
2. The building cell sits after spark.stop() (cell 88); in a top-to-bottom run it fails and the table keeps last run values.
3. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
4. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
5. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
6. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 89-93

**Source document:** the notebook above (annotated team code).
