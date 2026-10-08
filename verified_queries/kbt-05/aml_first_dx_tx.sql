-- VERIFIED QUERY REFERENCE
-- QUERY: AML_FIRST_DX_TX
-- QUESTION: What are each AML patient's first diagnosis, first/last treatment and Venclexta start/end dates?
-- PRIMARY_KBT: 5
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: FIRST_DX (37 AML codes), FIRST_TX / LAST_TX (regimens), VEN_START / VEN_END (Venclexta episodes).
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_EPISODE_BUSINESS_RULE_CHANGE_VAL; abv_val_ptd_onc_synd.dx_fact_curated_vw
-- METRICS: none
-- REUSABLE_COMPONENTS: first Dx, first/last Tx, VEN start/end
-- KNOWN_ISSUE: FIRST_DX has no source_flag filter. VEN_START is NULL for patients without Venclexta. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT *
FROM
(
    SELECT A.PATIENT_GID,
           B.FIRST_DX,
           A.FIRST_TX,
           A.LAST_TX,
           C.VEN_START,
           C.VEN_END
    FROM
    (
        SELECT PATIENT_GID,
               MIN(TO_DATE(regimen_start_date)) AS FIRST_TX,
               MAX(TO_DATE(regimen_end_date)) AS LAST_TX
        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
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
        --AND CLAIM_DATE >= '2019-12-01'
        --AND CLAIM_DATE <= '2026-03-06'
        GROUP BY PATIENT_SK
    ) B
    ON A.PATIENT_GID = B.PATIENT_GID
    LEFT JOIN
    (
        SELECT PATIENT_GID, 
               MIN(EPISODE_START_DATE_DRVD) AS VEN_START,
               MAX(EPISODE_END_DATE1_DRVD) AS VEN_END
        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_EPISODE_BUSINESS_RULE_CHANGE_VAL     
        WHERE FINAL_PRODUCT_NAME = 'VENCLEXTA'   
        GROUP BY PATIENT_GID            
    ) C  
    ON A.PATIENT_GID = C.PATIENT_GID                    
) A
