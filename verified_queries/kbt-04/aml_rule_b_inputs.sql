-- VERIFIED QUERY REFERENCE
-- QUERY: AML_RULE_B_INPUTS
-- QUESTION: What inputs does the age + product (new definition) intensity use?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Line-1 regimen group joined to birth year and first AML diagnosis; the input frame the pandas new-definition classifier runs on.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2; abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2; abv_val_ptd_onc_synd.dx_fact_curated_vw; patient_pool
-- METRICS: none
-- REUSABLE_COMPONENTS: line-1 filter, birth-year join, first Dx/Tx
-- KNOWN_ISSUE: AML_LOT_PATIENT_INTENSITY_LOT cell 44 was fixed (2026-10-07) to .format() the grouping table name; it previously sent {lot_regimen_group} to Spark literally. The classifier itself is Python (rules listed in reference_codes_and_mappings.md). Birth-year join is DISTINCT patient_sk + birth year; a patient with two birth years duplicates. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_v2 after classification.
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
),
fst_dx_tx_tbl AS (
SELECT *
FROM
(
    SELECT A.PATIENT_GID,
           B.FIRST_DX,
           A.FIRST_TX,
           A.LAST_TX
    FROM
    (
        SELECT PATIENT_GID,
               MIN(TO_DATE(regimen_start_date)) AS FIRST_TX,
               MAX(TO_DATE(regimen_end_date)) AS LAST_TX
        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2
        GROUP BY PATIENT_GID
    ) A
    LEFT JOIN
    (
        SELECT PATIENT_SK AS PATIENT_GID,
               MIN(TO_DATE(CLAIM_DATE)) AS FIRST_DX
        FROM abv_val_ptd_onc_synd.dx_fact_curated_vw
        WHERE SOURCE_DIAGNOSIS_CODE_1 IN 
        (
            '205', '205.0', '205.00', '205.01', '205.02', 'C92', 'C92.9', 'C92.0', 'C92.00', 'C92.01', 
            'C92.02', 'C92.5', 'C92.50', 'C92.51', 'C92.52', 'C92.6', 'C92.60', 'C92.61', 'C92.62', 'C92.90', 
            'C92.A', 'C92.A0', 'C92.A1', 'C92.A2', 'C92.Z0', 'C93', 'C93.0', 'C93.00', 'C93.01', 'C93.02', 
            'C94.0', 'C94.00', 'C94.01', 'C94.2', 'C94.20', 'C94.21', 'C94.22'
        )
        
        GROUP BY PATIENT_SK
    ) B
    ON A.PATIENT_GID = B.PATIENT_GID
                      
) A
)
SELECT 
    a.PATIENT_GID, 
    a.LOT_REGIMEN_GROUP, 
    a.LOT_START_DATE, 
    A.LOT_END_DATE,
    b.SOURCE_PATIENT_HIPAA_BIRTH_YEAR, 
    c.FIRST_DX
FROM (
    SELECT 
        PATIENT_GID, LOT_START_DATE, LOT_END_DATE, 
        LOT_REGIMEN_GROUP
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2
    WHERE LOT = 1
) a
LEFT JOIN (
    SELECT DISTINCT 
        PATIENT_SK, 
        SOURCE_PATIENT_HIPAA_BIRTH_YEAR
    FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw
    WHERE source_flag = 'SHA_PTD'
      AND source_market = 'ONC'
      --AND market_code = 'VENC_AML'
      and patient_sk in (
    select patient_sk
    from patient_pool
)


) b 
    ON a.PATIENT_GID = b.PATIENT_SK
LEFT JOIN fst_dx_tx_tbl c 
    ON a.PATIENT_GID = c.PATIENT_GID
