# abv_val_ptd_onc_venc_synd.dx_fact_vw

**Family:** APLD
**Contains:** patient diagnosis claims with first-position ICD-9/ICD-10 codes
**Common analyses:** time_to_treatment

## Grain

Not stated in sources. Diagnosis claim/event level; mx_claim_id is "the finest-grain uniqueness token on the claim". (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)

## Primary keys or entity keys

mx_claim_id; PATIENT_SK. (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)

## Row meaning

A diagnosis event for a patient. "Curated diagnosis-level claims view containing patient-level diagnosis activity, including diagnosis codes and associated claim/service information." (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx · Use Case)

## Refresh

Not stated.

## Mandatory filters

Use SOURCE_FLAG = SHA / KOMODO / Purple Labs, SOURCE_MARKET = ONC, and MARKET_CODE = VENC_CLL / VENC_AML. (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx · Use Case). SHA-Time to Treatment.sql applies only the diagnosis-code filter and restricts the patient set by sub-query instead.

## Business rules

1. SOURCE_DIAGNOSIS_CODE_1 "holds a mixture of ICD-9 and ICD-10 codes in dotted format ('205.00' alongside 'C92.00')". (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)\n2. The KOMODO feed stores diagnoses differently: custom_field_value_1 is a "Multi-valued diagnosis code field used by the KOMODO feed, holding several diagnosis codes concatenated in one string with a pipe delimiter. Code to split it (split(custom_field_value_1, '\\|')) and posexplodes it into one row per code plus its ordinal position". (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)\n3. First CLL diagnosis date is MIN(CLAIM_DATE) over the CLL code set. (SHA-Time to Treatment.sql)

## Join guidance

PATIENT_SK → strip the 'SHA_PTDONC' source tag (e.g. 217656241SHA_PTDONC → 217656241) to obtain PATIENT_GID, then join to all_claims_combined_fact_vw. The SME confirmed the same convention holds on all VAL tables (Q-22). (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx; SHA-Time to Treatment.sql)

## Caveats

1. Only the first-position code is read: the "'SOURCE_' prefix and the '_1' ordinal indicate it is the raw first-position code rather than a mastered or mapped value, implying further positional code columns exist (_2, _3, ...) that this code does not read - so a diagnosis recorded only in a secondary position would be missed". (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)\n2. "Diagnosis codes represent observed claims activity and may not always reflect confirmed clinical diagnosis or the exact date of disease onset." (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx · Use Case)\n3. "Diagnosis field structure can differ by source; SHA and KOMODO diagnosis feeds may require different parsing/business rules." (abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx)

## Raw feed fields

The raw SHA PTD and Komodo field behind each column used by the base layer is in
`context/data/source_dictionaries/view_column_lineage.tsv`. The full vendor layouts are in
`context/data/source_dictionaries/` (SHA_Data_Dictionary.xlsx, Komodo_Data_Dictionary.xlsx).

## Pipeline and lineage

Diagnosis layer for indication assignment, CLL/SLL eligibility and time-to-treatment

**Produced by:** Upstream VAL view — not produced by any supplied code.

**Source document:** abv_val_ptd_onc_venc_synd_dx_fact_vw_Data_Dictionary.xlsx
