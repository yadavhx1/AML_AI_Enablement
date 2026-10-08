---
name: kbt-01-tx-table-build
description: Use for AML base-layer questions about the patient pool (2+ AML diagnoses), the AML treatment-claims (TX) table, the 28-product AML market basket, product code lookups, days of supply, grace periods, Filgrastim exclusion, or how a claim becomes a FINAL_PRODUCT_NAME (`AML_LOT_TX_TABLE`).
user-invocable: true
---


# KBT 1 - Patient pool, TX table, and DOS/grace (AML_LOT_TX_TABLE)

## Analytical intent

Use this KBT when the question is about the first stage of the AML base layer: who enters the patient
pool, which claims enter the treatment frame, and how each claim gets its days of supply (DOS) and
grace. Questions about episodes start at KBT 2; questions about regimens at KBT 3.

Notebook: `scripts/Notebooks/AML_LOT_TX_TABLE.ipynb`.

## Method

1. Patient pool: patients with more than one distinct AML diagnosis claim (`mx_claim_id`) ever on the
   37-code AML set in `abv_val_ptd_onc_synd.dx_fact_curated_vw`, `source_flag = 'SHA_PTD'`. No recency,
   competing-diagnosis or treatment requirement. It is a temp view (`patient_pool`) and is not persisted.
2. TX table: DISTINCT claims from `abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw` with
   `source_flag = 'SHA_PTD'`, `source_market = 'ONC'`, pool patients only, `mastered_product_name` in the
   28 basket products. `market_code = 'VENC_AML'` is commented out.
3. Column renames: `patient_sk` → `PATIENT_GID` (suffix `SHA_PTDONC` kept), `mastered_product_name` →
   `FINAL_PRODUCT_NAME`, `MDM_NPI_NUMBER` → `NPI_NUMBER`, `PROCEDURE_CODE` → `PRODUCT_CODE`,
   `source_type` → `NATIVE_TYPE`.
4. TX final table: drop `FILGRASTIM`; `NATIVE_TYPE` = 'RX' when source_type LIKE '%RX%', else 'PX';
   `DOS_FINAL` = Rx claim days supply (28 when NULL or ≤ 0) or the fixed PX value; `GRACE_VALUE` per
   product (3–60 days).
5. For DOS/grace values, read `context/domain/reference_codes_and_mappings.md` rather than re-deriving
   them from the CASE.
6. Product-code lookups (Onureg, Inqovi, Rezlidhia, Vanflyta) run in the globals cell but are not used
   downstream; product identity comes from `mastered_product_name`.
7. Validate: patient count is the same across the TX final, SOB and episode tables; there are no NULL
   DOS or grace rows; there are 28 distinct products.

## Working defaults

- Pool: 2+ AML diagnosis claims (this build). The Aug'26 eligibility build used `market_code = 'VENC_AML'`
  instead (`AML_PATIENT_POOL`, OI-01).
- Rx DOS fallback: 28 days.
- Grace is independent of DOS; Venclexta 60, Inqovi/Onureg/Vanflyta/Vincristine 28.
- Output tables: `..._BUSINESS_RULE_CHANGE_VAL_v2` suffix.

## Context to read

- `context/domain/reference_codes_and_mappings.md` (AML diagnosis codes, basket, DOS/grace)
- `context/data/tables/<tx table>/profile.md`
- `context/data/tables/abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw/profile.md` when a source
  field is needed
- `context/data/source_dictionaries/` (README "Points that matter", then `view_column_lineage.tsv`) only
  when the question goes below the view:
  - why a claim has no NPI or days supply;
  - why the pool misses a patient (first-position diagnosis only);
  - claim status (rejected / reversed);
  - whether a payer or enrollment cut is possible;
  - running on Komodo instead of SHA.
  The lineage is mostly inferred from names; say so. Never query the raw tables.

## Verified-query candidates

- `AML_PATIENT_POOL_2PLUS_DX`, `AML_TX_TABLE`, `AML_TX_DOS_GRACE`, `AML_PRODUCT_CODE_LOOKUPS`.

## Minimum QC

- Pool rule and build suffix are named.
- Filgrastim is excluded before counting products or claims.
- DOS and grace are taken from the documented table; no NULLs.
- Patient counts are `COUNT(DISTINCT PATIENT_GID)`.


## Output contract

Return the requested result first. State the data source, grain, pool rule, period and material
assumptions. Mention a verified query only when it was reused or materially adapted. Keep patient
identifiers out of the response.
