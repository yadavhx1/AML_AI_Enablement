-- VERIFIED QUERY REFERENCE
-- QUERY: AML_LOT_REGIMEN_GROUPING
-- QUESTION: What products make up each AML line of therapy?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: One row per patient x LOT: LOT_START_DATE, LOT_END_DATE and LOT_REGIMEN_GROUP (sorted, de-duplicated union of products). The notebook does this in pandas; this is the SQL equivalent.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: none
-- REUSABLE_COMPONENTS: line start/end, product union per line
-- KNOWN_ISSUE: SQL EQUIVALENT, not team code: the notebook builds this table in pandas (merge_regimens) and writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2. ARRAY_JOIN(ARRAY_SORT(ARRAY_DISTINCT(...))) reproduces the sorted unique product list.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT PATIENT_GID, LOT,
       MIN(REGIMEN_START_DATE) AS LOT_START_DATE,
       MAX(REGIMEN_END_DATE) AS LOT_END_DATE,
       ARRAY_JOIN(ARRAY_SORT(ARRAY_DISTINCT(FLATTEN(COLLECT_LIST(
           TRANSFORM(SPLIT(REGIMEN, ','), x -> TRIM(x)))))), ', ') AS LOT_REGIMEN_GROUP
FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2
GROUP BY PATIENT_GID, LOT
