# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_ACCT_TYPE_GRP_UPDATED_BUSINESS_RULES_v2_SATEEK

**Notebook:** `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` (`scripts/Notebooks/`); KBT 6.

**Family:** APLD (AML NPS dashboard, legacy IC definition)
**Contains:** Account type group (Academic / Academic Satellite / Larger or Smaller Community / Federal) per initiating AML NPS HCP
**Common analyses:** aml_nps_by_account

## Grain

One row per ABBOTT_CUSTOMER_ID (more if an HCP has two groups on the winning subtype). (scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 39-47)

## Primary keys or entity keys

ABBOTT_CUSTOMER_ID.

## Row meaning

The account group of an initiating HCP.

## Refresh

Rebuilt by the NPS dashboard notebook each cycle (DROP + CREATE), after the full base-layer refresh (after AML_PATIENT_ELIGIBILITY)
(`workflows/aml_nps_dashboard_legacy.md`). State the input table names and data cut in the run header.

## Mandatory filters

None stored. Apply the line, intensity and gates the question needs at query time.

## Business rules

1. Subtype from the ONH2 HCI-HCP affiliations (1VIEW_ONCOLOGY, DDS_ACTIVE_FLAG = Y), or Reltio (ADS_ACTIVE_FLAG and VALUATION_INCLUDE_FLAG = Y) for HCPs with no ONH2 affiliation, joined to heme_account on child account id.
2. Lowest-ranked subtype wins: Elite Oncology Center 1 ... DOD 8, NULL 9.
3. Community splits on MAX child-account decile: >= 8 Larger Community, else or NULL Smaller Community.

## Join guidance

ABBOTT_CUSTOMER_ID to ABBOTT_CUSTOMER_ID_REGIMEN / ABBOTT_ID.

## Caveats

1. No later cell reads this table: the dashboard and rollup use the subtype only, and the rollup groups it as Academic / Community.
2. The table name carries the notebook author's personal suffix (`_SATEEK`, or `_UPDATED_BUSINESS_RULES_v2`), not the pack build suffix. Confirm the name in `config/nps_dashboard_legacy.yaml` before reading it (OI-16).
3. Lines come from the personal `_v2_SATEEK` copy of the LoT grouping table and the legacy-rule cohort `_v2`; the eligibility flags come from the un-suffixed Aug'26 build (OI-02).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix. Patient identifiers never leave the working query; return aggregates only.
5. Data types are inferred from the SQL that builds the table; no DDL was supplied.

## Pipeline and lineage

AML base layer (KBT 1-5) -> LoT grouping + legacy-rule cohort + eligibility flags -> legacy line backbone ->
initiating HCP -> account and segments -> dashboard table -> LoT x month summary, Ipsos index, account
rollup. See `context/metrics/nps_dashboard_legacy.md`.

**Produced by:** scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb cells 39-47

**Source document:** the notebook above (annotated team code).
