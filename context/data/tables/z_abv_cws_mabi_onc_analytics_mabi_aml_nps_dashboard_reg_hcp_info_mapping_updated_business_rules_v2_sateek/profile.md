# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 6.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** AML lines with the initiating HCP, decile, above-brand and execution segment and account subtype
**Common analyses:** aml_nps_by_segment, aml_nps_by_account

## Grain

One row per patient x LOT (more when an NPI repeats in a segment table). (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 49-53)

## Primary keys or entity keys

PATIENT_GID + LOT.

## Row meaning

A line of therapy with its initiating HCP attributes.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. UNI_DECILE and ABOVE_BRAND_SEGMENT from the above-brand table on NPI; EXECUTION_SEGMENT from the GNE segment _BKP table on NPI.
2. FINAL_ACCOUNT_TYPE_2 = winning account subtype of ABBOTT_CUSTOMER_ID_REGIMEN.

## Join guidance

PATIENT_GID + LOT to the dashboard table.

## Caveats

1. Segment tables are joined without de-duplication; check PATIENT_GID x LOT uniqueness.
2. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
3. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
5. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 49-53

**Source document:** the notebook above (annotated team code).
