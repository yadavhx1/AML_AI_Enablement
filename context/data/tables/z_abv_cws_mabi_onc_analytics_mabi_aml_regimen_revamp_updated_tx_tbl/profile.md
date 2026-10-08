# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2

**Notebook:** `01` (`scripts/Notebooks/`); KBT 1.

**Family:** APLD (AML base layer)
**Contains:** Raw AML treatment claims for pool patients on the 28-product basket, before DOS/grace
**Common analyses:** aml_tx_build

## Grain

One row per distinct claim (patient, claim, date, product, NPI, product code, source type).

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

Raw AML treatment claims for pool patients on the 28-product basket, before DOS/grace.

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. DISTINCT claims from all_claims_combined_fact_vw (SHA_PTD, ONC) for patient_pool patients and the 28 basket products; market_code filter commented out.
2. Columns renamed: patient_sk -> PATIENT_GID, mastered_product_name -> FINAL_PRODUCT_NAME, MDM_NPI_NUMBER -> NPI_NUMBER, PROCEDURE_CODE -> PRODUCT_CODE, source_type -> NATIVE_TYPE.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_LOT_TX_TABLE.
