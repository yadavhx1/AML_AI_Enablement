# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 6.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** AML lines joined to their backbone-product claims, with the initiating NPI and Abbott customer id
**Common analyses:** aml_nps_hcp_attribution

## Grain

One row per patient x LOT x backbone claim inside the line dates; one row with NULL claim fields when the line has no backbone claim. (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 26-35)

## Primary keys or entity keys

PATIENT_GID + LOT (+ CLAIM_ID).

## Row meaning

A backbone-product claim of a line, carrying the line-level initiating NPI.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. Backbone of the line = highest-ranked product of LOT_REGIMEN_GROUP on the IC_ELIG (28) or IC_INELIG (11) rank list (pandas, cell 29).
2. Claims: ONC / SHA_PTD / VENC_AML, MASTERED_PRODUCT_NAME = BACKBONE, claim date within the line, no FILGRASTIM, NPI not null.
3. NPI_REGIMEN = NPI on the first backbone claim (CLAIM_DATE ASC, NPI_NUMBER DESC, CLAIM_ID); ABBOTT_CUSTOMER_ID_REGIMEN from CUSTOMER_TBL (DDS_ACTIVE_FLAG = Y).
4. REG_NUM is a copy of LOT.

## Join guidance

PATIENT_GID + LOT to the grouping table; NPI_REGIMEN to the segment tables; ABBOTT_CUSTOMER_ID_REGIMEN to the account tables.

## Caveats

1. Not one row per line: take DISTINCT PATIENT_GID, LOT, NPI_REGIMEN before counting lines.
2. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
3. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
5. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 26-35

**Source document:** the notebook above (annotated team code).
