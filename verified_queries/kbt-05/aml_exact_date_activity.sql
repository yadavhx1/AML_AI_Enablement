-- VERIFIED QUERY REFERENCE
-- QUERY: AML_EXACT_DATE_ACTIVITY
-- QUESTION: How are the Mx and Rx exact-date activity tables for AML eligibility built?
-- PRIMARY_KBT: 5
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Distinct patient x claim date of Mx activity (PX/SX/DX claims plus all dx_fact_curated_vw rows) and Rx activity, for patients on the combined LoT table.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw; abv_val_ptd_onc_synd.dx_fact_curated_vw; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
-- METRICS: none
-- REUSABLE_COMPONENTS: source_type LIKE patterns for Mx and Rx
-- KNOWN_ISSUE: No source_flag / source_market / market_code filter, so Mx activity is not ONC-limited (OI-07). Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_MX_ACT_TBL_AML_EXACT_DATES_KA_v2 and Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

-- Mx activity
       
        SELECT DISTINCT PATIENT_SK AS PATIENT_GID, CLAIM_DATE
        FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw  
        WHERE PATIENT_SK IN (
          SELECT DISTINCT PATIENT_GID
          FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
        )
          AND (SOURCE_TYPE LIKE '%PX%' OR SOURCE_TYPE LIKE '%SX%' OR SOURCE_TYPE LIKE '%DX%')
          --Dx fact is currentlty not in VAL all claims -- 
          union
         SELECT DISTINCT PATIENT_SK AS PATIENT_GID, CLAIM_DATE
        FROM abv_val_ptd_onc_synd.dx_fact_curated_vw  
        WHERE PATIENT_SK IN (
          SELECT DISTINCT PATIENT_GID
          FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
        );

-- Rx activity
       
        SELECT DISTINCT PATIENT_SK AS PATIENT_GID, CLAIM_DATE
        FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw  
        WHERE PATIENT_SK IN (
          SELECT DISTINCT PATIENT_GID 
          FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
        )
          AND SOURCE_TYPE LIKE '%RX%';
