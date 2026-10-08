-- VERIFIED QUERY REFERENCE
-- QUERY: AML_VEN_MX_LOOKBACK_ELIG
-- QUESTION: Which AML patients pass TX_MX_LB_ELIG_VEN_FLG?
-- PRIMARY_KBT: 5
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Activity in every calendar semester (Jan-Jun / Jul-Dec) from the semester of VEN_START - 12 months to the semester of VEN_START, capped at the last complete semester.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL; abv_val_ptd_synd_work.mapping_mx_activity_freq_tbl; abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw
-- METRICS: none
-- REUSABLE_COMPONENTS: calendar-semester spine, semesterly activity join, {exc_dt} cap
-- KNOWN_ISSUE: PARAMETER {exc_dt} = first day of the last semester with complete data (set by the MAX MONTH cell; 2025-07-01 in the Aug'26 run). Activity table read from abv_val_ptd_synd_work without market_code = 'ONC' (OI-07). Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_VEN_TX_MX_LB_ELIG_TBL_BUSINESS_RULE_CHANGE_VAL.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH period_to_be_elig AS (
SELECT *,
CASE WHEN MONTH(MIN_CLM_DT_12M_LB) <= 6 THEN CONCAT(CAST(YEAR(MIN_CLM_DT_12M_LB) AS STRING),'-01-01')                         WHEN MONTH(MIN_CLM_DT_12M_LB) > 6 THEN CONCAT(CAST(YEAR(MIN_CLM_DT_12M_LB) AS STRING),'-07-01')                    END AS ELIG_START,                    CASE WHEN MONTH(MIN_CLM_DT) <= 6 THEN CONCAT(CAST(YEAR(MIN_CLM_DT) AS STRING),'-01-01')                         WHEN MONTH(MIN_CLM_DT) > 6 THEN CONCAT(CAST(YEAR(MIN_CLM_DT) AS STRING),'-07-01')                    END AS ELIG_END
FROM
(
    SELECT PATIENT_GID,
    MIN_CLM_DT,  
    MAX_CLM_DT,
    ADD_MONTHS(MIN_CLM_DT, -6) AS MIN_CLM_DT_6M_LB,
    ADD_MONTHS(MIN_CLM_DT, -12) AS MIN_CLM_DT_12M_LB,
    ADD_MONTHS(MIN_CLM_DT, -18) AS MIN_CLM_DT_18M_LB,
    ADD_MONTHS(MIN_CLM_DT, -24) AS MIN_CLM_DT_24M_LB,
    ADD_MONTHS(MIN_CLM_DT, -36) AS MIN_CLM_DT_36M_LB,
    ADD_MONTHS(MIN_CLM_DT, 6) AS MIN_CLM_DT_6M_LF,
    ADD_MONTHS(MIN_CLM_DT, 12) AS MIN_CLM_DT_12M_LF,
    ADD_MONTHS(MAX_CLM_DT, 3) AS MAX_CLM_DT_QTR_EC
    FROM
    (
        SELECT PATIENT_GID, 
        TO_DATE(MIN(TX_CLAIM_DATE)) AS MIN_CLM_DT, 
        TO_DATE(MAX(TX_CLAIM_DATE)) AS MAX_CLM_DT
        FROM
        (
            --CHANGE SOURCE TABLE HERE
            SELECT DISTINCT PATIENT_GID, VEN_START AS TX_CLAIM_DATE
            FROM fst_dx_tx_tbl
        )A
        GROUP BY 1
    )A
)A
)
SELECT DISTINCT PATIENT_GID
FROM
(
	SELECT PATIENT_GID, PERIOD_TO_BE_ELIG_CT, ELIG_PERIOD_CT,
	CASE WHEN PERIOD_TO_BE_ELIG_CT = ELIG_PERIOD_CT THEN 1 ELSE 0 END AS ELIG_FLG_TX
	FROM
	(
		SELECT PATIENT_GID, COUNT(DISTINCT PATIENT_TO_BE_ELIG_PERIOD) AS PERIOD_TO_BE_ELIG_CT, SUM(ACTIVE_FLAG) AS ELIG_PERIOD_CT
		FROM
		(
			SELECT C.*,
			CASE WHEN D.ACTIVE_FLAG IS NULL THEN 0 ELSE D.ACTIVE_FLAG END AS ACTIVE_FLAG
			FROM
			(
				SELECT A.*, B.PATIENT_TO_BE_ELIG_PERIOD
				FROM
				(
					SELECT PATIENT_GID, ELIG_START, ELIG_END
					FROM period_to_be_elig
				)A
				LEFT JOIN
				(
					SELECT DISTINCT 
					CASE WHEN MONTH(CLAIM_DATE) <= 6 THEN CONCAT(CAST(YEAR(CLAIM_DATE) AS STRING),'-01-01')                 WHEN MONTH(CLAIM_DATE) > 6 THEN CONCAT(CAST(YEAR(CLAIM_DATE) AS STRING),'-07-01')            END AS PATIENT_TO_BE_ELIG_PERIOD
					FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw
        			where source_flag  =  'SHA_PTD'
        			and source_market  =  'ONC'
        			AND market_code = 'VENC_AML' 
					AND source_type = 'RX FACT'
				)B
				ON A.ELIG_START <= B.PATIENT_TO_BE_ELIG_PERIOD
				AND A.ELIG_END >= B.PATIENT_TO_BE_ELIG_PERIOD
                AND B.PATIENT_TO_BE_ELIG_PERIOD <= TO_DATE('{exc_dt}')
			)C
			LEFT JOIN
			(
				SELECT DISTINCT PATIENT_SK AS PATIENT_GID, TO_DATE(frequency_start_date) AS FREQ_START_DATE, 1 AS ACTIVE_FLAG				FROM abv_val_ptd_synd_work.mapping_mx_activity_freq_tbl where source_flag  =  'SHA_PTD' and source_market  =  'ONC'				and UPPER(FREQUENCY) = 'SEMESTERLY'				AND `OFFSET` = '0'
			)D
			ON C.PATIENT_GID = D.PATIENT_GID
			AND C.PATIENT_TO_BE_ELIG_PERIOD = D.FREQ_START_DATE
		)E
        WHERE PATIENT_TO_BE_ELIG_PERIOD IS NOT NULL
		GROUP BY 1
	)F
)G 
where elig_flg_tx=1
