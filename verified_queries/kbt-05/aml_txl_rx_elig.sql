-- VERIFIED QUERY REFERENCE
-- QUERY: AML_TXL_RX_ELIG
-- QUESTION: Which AML patients pass TX_TXL_RX_ELIG_FLG (Rx continuity over the AML journey)?
-- PRIMARY_KBT: 5
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: FIRST_TX to LAST_TX: activity in every rolling 6-month interval of the span; spans under 6 months pass automatically.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL (fst_dx_tx_tbl temp view); Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA
-- METRICS: none
-- REUSABLE_COMPONENTS: 6-month interval spine via EXPLODE(sequence()), short-span pass, interval activity check
-- KNOWN_ISSUE: PARTLY SQL EQUIVALENT: the spine and short-span steps are team SQL; the interval check is pandas in the notebook and is reproduced in SQL here. Intervals are anchored on the span start (+n x 6 months), not calendar semesters. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_TX_RX_TXL_ELIG_TBL_BUSINESS_RULE_CHANGE_VAL.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH period_to_be_elig AS (
SELECT *
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
        TO_DATE(MIN(FIRST_TX)) AS MIN_CLM_DT, 
        TO_DATE(MAX(LAST_TX)) AS MAX_CLM_DT
        FROM
        (
            --CHANGE SOURCE TABLE HERE
            SELECT DISTINCT PATIENT_GID, FIRST_TX, LAST_TX
            FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL
        )A
        GROUP BY 1
    )A
)A
),
elig_pats_tx_txl_rx_interim_tbl AS (
SELECT distinct *
    FROM (
        SELECT *,
               LEAD(PATIENT_TO_BE_ELIG_PERIOD, 1) 
                   OVER (
                       PARTITION BY PATIENT_GID 
                       ORDER BY PATIENT_TO_BE_ELIG_PERIOD DESC
                   ) AS PREV_PATIENT_TO_BE_ELIG_PERIOD
        FROM (
            SELECT 
                A.*, 
                B.PATIENT_TO_BE_ELIG_PERIOD
            FROM (
                SELECT 
                    PATIENT_GID, 
                    MIN_CLM_DT AS ELIG_START, 
                    MAX_CLM_DT AS ELIG_END
                FROM period_to_be_elig
            ) A
            LEFT JOIN (
                SELECT DISTINCT 
                    PATIENT_GID,
                    ADD_MONTHS(MIN_CLM_DT, n * 6) AS PATIENT_TO_BE_ELIG_PERIOD
                FROM (
                    SELECT 
                        PATIENT_GID,
                        MIN_CLM_DT,                                                    
                        MAX_CLM_DT,
                        CAST(MONTHS_BETWEEN(MAX_CLM_DT, MIN_CLM_DT) / 6 AS INT) AS periods_needed
                    FROM period_to_be_elig
                ) A
                LATERAL VIEW EXPLODE(sequence(0, periods_needed)) tmp AS n
                WHERE ADD_MONTHS(MIN_CLM_DT, n * 6) <= MAX_CLM_DT
            ) B
            ON A.PATIENT_GID = B.PATIENT_GID
        )
    )
    --WHERE PREV_PATIENT_TO_BE_ELIG_PERIOD IS NOT NULL
),
short_span AS (
select distinct patient_gid from (
              select patient_gid from 
              elig_pats_tx_txl_rx_interim_tbl
          group by 1
          having count(*) = 1
          )
),
remaining_patients_to_be_checked AS (
select * from elig_pats_tx_txl_rx_interim_tbl
          where PREV_PATIENT_TO_BE_ELIG_PERIOD IS NOT NULL
),
-- Equivalent of the pandas interval check (notebook merges activity rows and flags each interval):
interval_check AS (
    SELECT R.PATIENT_GID, R.PATIENT_TO_BE_ELIG_PERIOD,
           MAX(CASE WHEN A.CLAIM_DATE > R.PREV_PATIENT_TO_BE_ELIG_PERIOD
                     AND A.CLAIM_DATE <= R.PATIENT_TO_BE_ELIG_PERIOD THEN 1 ELSE 0 END) AS ACTIVITY_FLAG
    FROM remaining_patients_to_be_checked R
    LEFT JOIN Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA A
      ON A.PATIENT_GID = R.PATIENT_GID
     AND A.CLAIM_DATE >= R.ELIG_START
     AND A.CLAIM_DATE <= R.ELIG_END
    GROUP BY R.PATIENT_GID, R.PATIENT_TO_BE_ELIG_PERIOD
)
SELECT DISTINCT PATIENT_GID FROM (
    SELECT PATIENT_GID FROM interval_check GROUP BY PATIENT_GID HAVING MIN(ACTIVITY_FLAG) = 1
    UNION
    SELECT PATIENT_GID FROM short_span
)
