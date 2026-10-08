-- VERIFIED QUERY REFERENCE
-- QUERY: AML_REGIMEN_PATIENT_COUNT
-- QUESTION: How many patients reach the regimen table (row-count QC)?
-- PRIMARY_KBT: 3
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Patient-count QC on the regimen table; compare with the TX final, SOB and episode counts (57,697 in the May'26 run).
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: none
-- REUSABLE_COMPONENTS: patient-count QC
-- KNOWN_ISSUE: QC only.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT COUNT(DISTINCT PATIENT_GID_RGMN) FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL_v2
