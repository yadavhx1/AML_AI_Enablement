# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_FINAL_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_FINAL_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `01` (`scripts/Notebooks/`); KBT 1.

**Family:** APLD (AML base layer)
**Contains:** AML base-layer treatment claims for the 28-product basket with per-claim DOS and grace attached
**Common analyses:** aml_lot_base, aml_persistency, aml_hcp_affiliations

## Grain

One row per distinct claim (patient, claim_id, claim_date, product, NPI, product code, native type). (scripts/Notebooks/AML_LOT_TX_TABLE.ipynb cells 37-49)

## Primary keys or entity keys

PATIENT_GID + CLAIM_ID + FINAL_PRODUCT_NAME.

## Row meaning

A single Rx or PX/SX treatment claim for an AML basket product, after Filgrastim removal, with DOS_FINAL and GRACE_VALUE assigned.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None beyond the build: the upstream TX table already applies `source_flag='SHA_PTD'`, `source_market='ONC'` and the pool rule.

## Business rules

1. Source: `abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw`; `mastered_product_name` -> FINAL_PRODUCT_NAME, `MDM_NPI_NUMBER` -> NPI_NUMBER, `PROCEDURE_CODE` -> PRODUCT_CODE, `source_type` -> NATIVE_TYPE.
2. NATIVE_TYPE = 'RX' when source_type LIKE '%RX%', else 'PX'.
3. DOS_FINAL: Rx = PRODUCT_DAYS_SUPPLY, or 28 when NULL/<=0; PX = fixed per product (1 or 28). GRACE_VALUE per product (3-60). Full table in `reference_codes_and_mappings.md`.
4. FILGRASTIM is excluded. 28 products remain.

## Join guidance

NPI_NUMBER -> ABV_DDS_SYND.CUSTOMER_TBL.NPI_NUMBER for ABBOTT_CUSTOMER_ID (as the affiliations step does).

## Caveats

1. QC in the Aug'26 run: 0 NULL DOS rows, 0 NULL grace rows, 28 distinct products, claim dates 2010-01-01 to 2026-07-03.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_TX_TABLE.ipynb cells 37-49; scripts/Notebooks/AML_LOT_TX_TABLE.ipynb cells 12-17

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
