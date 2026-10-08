-- VERIFIED QUERY REFERENCE
-- QUERY: AML_COMBINED_LOT
-- QUESTION: What is the combined AML regimen-level line-of-therapy table?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: UNION of the IC Eligible and IC Ineligible LoT tables with TYPE = legacy-rule intensity.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_ELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_INELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: none
-- REUSABLE_COMPONENTS: IC_ELIG / IC_INELIG union, TYPE column
-- KNOWN_ISSUE: Raw LOT; no relapse/remission refinement in this build (that step is only in the original team notebook Patient Eligibility.ipynb, not in this pack). Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT * 
    FROM
	(
		SELECT PATIENT_GID_RGMN AS PATIENT_GID, REGIMEN, REGIMEN_START_DATE, REGIMEN_END_DATE, BACKBONE, PREV_BACKBONE, REG_NUM, LINE_CHANGE, LOT, 'IC_ELIG' AS TYPE
		FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_ELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2 -- SOME PATIENTS MAY HAVE ARSENIC REGIMENS

		UNION
		
		SELECT PATIENT_GID, REGIMEN, REGIMEN_START_DATE, REGIMEN_END_DATE, BACKBONE, PREV_BACKBONE, REG_NUM, LINE_CHANGE, LOT, 'IC_INELIG' AS TYPE
		FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_INELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2
	)
