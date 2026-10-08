# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_UPDATED_BUSINESS_RULES_v2_SATEEK

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 6.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** Legacy AML NPS Power BI dataset: every line with backbone group, initiating HCP, segments and account subtype
**Common analyses:** aml_nps_dashboard, aml_nps_by_backbone, aml_nps_by_account, aml_nps_by_segment

## Grain

One row per patient x LOT (DISTINCT on the listed columns). (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 60-67)

## Primary keys or entity keys

PATIENT_GID + LOT.

## Row meaning

One new patient start into a line, as shown on the NPS dashboard.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. BACKBONE_GROUP: VENCLEXTA; AZACITIDINE / DECITABINE / ONUREG / INQOVI = HMA; everything else (UNKNOWN too) = OTHER NOVEL AGENTS.
2. NULL NPI, Abbott id, decile (or '-'), segments and subtype become 'Not Available'.
3. ACCT_SUBTYPE_HIER: Elite Oncology Center 1 ... DOD 8, else 9.

## Join guidance

PATIENT_GID to the eligibility flags table for gates and PATIENT_COHORT.

## Caveats

1. Despite 1L_IC_INELIG in the name, the 1L, intensity and eligibility filters are commented out: every line, both intensities, no gates. Apply them at query time.
2. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
3. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
5. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 60-67

**Source document:** the notebook above (annotated team code).
