-- VERIFIED QUERY REFERENCE
-- QUERY: AML_TX_TABLE
-- QUESTION: How is the AML treatment-claims table built?
-- PRIMARY_KBT: 1
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: DISTINCT SHA_PTD/ONC claims for pool patients on the 28 AML basket products, renaming mastered columns to the base-layer names.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw; patient_pool (temp view)
-- METRICS: none
-- REUSABLE_COMPONENTS: 28-product basket, pool filter, column renames (patient_sk->PATIENT_GID, mastered_product_name->FINAL_PRODUCT_NAME, MDM_NPI_NUMBER->NPI_NUMBER, PROCEDURE_CODE->PRODUCT_CODE, source_type->NATIVE_TYPE)
-- KNOWN_ISSUE: market_code = 'VENC_AML' is commented out; the pool alone restricts the population. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH patient_pool AS (
SELECT distinct PATIENT_SK from
(
    select patient_sk, count(distinct mx_claim_id) as Count_of_claims
    FROM abv_val_ptd_onc_synd.dx_fact_curated_vw
    WHERE SOURCE_DIAGNOSIS_CODE_1 IN 
    (
        '205', '205.0', '205.00', '205.01', '205.02', 'C92', 'C92.9', 'C92.0', 'C92.00', 'C92.01', 
        'C92.02', 'C92.5', 'C92.50', 'C92.51', 'C92.52', 'C92.6', 'C92.60', 'C92.61', 'C92.62', 'C92.90', 
        'C92.A', 'C92.A0', 'C92.A1', 'C92.A2', 'C92.Z0', 'C93', 'C93.0', 'C93.00', 'C93.01', 'C93.02', 
        'C94.0', 'C94.00', 'C94.01', 'C94.2', 'C94.20', 'C94.21', 'C94.22'
    )
    and source_flag='SHA_PTD'
    group by 1
)
where count_of_claims>1
)

          select distinct patient_sk as patient_gid, PRODUCT_QTY_DISPENSED, PRODUCT_DAYS_SUPPLY, 
          mastered_product_name as final_product_name, claim_date, claim_id, MDM_NPI_NUMBER as npi_number, PROCEDURE_CODE as product_code, source_type as native_type
          FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw
            where source_flag = 'SHA_PTD'
            and source_market = 'ONC'
            --and market_code = 'VENC_AML'   
            and patient_sk in (
                select patient_sk
                from patient_pool
            )
            and mastered_product_name IN (
                'AZACITIDINE','DAURISMO','DECITABINE','IDHIFA','L-DAC','TIBSOVO','VENCLEXTA',
                'XOSPATA','REZLIDHIA','MYLOTARG','RYDAPT','ARSENIC_TRIOXIDE','CLADRIBINE','CLOFARABINE','CYCLOPHOSPHAMIDE',
                'DAUNORUBICIN','ETOPOSIDE','FLUDARABINE','HI-DAC','IDARUBICIN','MITOXANTRONE','NEXAVAR','ONUREG','INQOVI',
                'S-DAC','VINCRISTINE','VANFLYTA','VYXEOS'
            )
