-- VERIFIED QUERY REFERENCE
-- QUERY: AML_DX_LOOKBACK_ELIG
-- QUESTION: Which AML patients pass the diagnosis lookback eligibility (DX_LB_ELIG_FLG)?
-- PRIMARY_KBT: 5
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Mx or Rx activity in both [FIRST_DX-6m, FIRST_DX) and [FIRST_DX-12m, FIRST_DX-6m), exact dates.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_MX_ACT_TBL_AML_EXACT_DATES_KA_v2; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA
-- METRICS: none
-- REUSABLE_COMPONENTS: 6m / 12m lookback windows, exact-date activity joins
-- KNOWN_ISSUE: Rolling exact-date windows, not calendar semesters. Left joins fan out per claim before DISTINCT. Writes MABI_AML_LOT_PAT_DX_LB_ELIG_TBL_BUSINESS_RULE_CHANGE_VAL.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH period_to_be_elig AS (
SELECT *,
MIN_CLM_DT, MIN_CLM_DT_6M_LB, MIN_CLM_DT_12M_LB
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
        TO_DATE(MIN(CLAIM_DATE)) AS MIN_CLM_DT,   
        TO_DATE(MAX(CLAIM_DATE)) AS MAX_CLM_DT
        FROM
        (
            --CHANGE SOURCE TABLE HERE
            SELECT DISTINCT PATIENT_GID, FIRST_DX AS CLAIM_DATE
            FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL
        )A
        GROUP BY 1
    )A
)A
)
SELECT DISTINCT PATIENT_GID
    FROM
    (
        SELECT *,
               CASE 
                 WHEN (ACTIVE_FLAG_MX_PREV_6M >= 1 OR ACTIVE_FLAG_RX_PREV_6M >= 1)
                      AND (ACTIVE_FLAG_MX_PREV_12M >= 1 OR ACTIVE_FLAG_RX_PREV_12M >= 1)
                 THEN 1
                 ELSE 0
               END AS ELIG_FLG
        FROM
        (
            SELECT A.*, 
                   COALESCE(B.ACTIVE_FLAG_MX_PREV_6M,0) AS ACTIVE_FLAG_MX_PREV_6M,
                   COALESCE(C.ACTIVE_FLAG_RX_PREV_6M,0) AS ACTIVE_FLAG_RX_PREV_6M,
                   COALESCE(D.ACTIVE_FLAG_MX_PREV_12M,0) AS ACTIVE_FLAG_MX_PREV_12M,
                   COALESCE(E.ACTIVE_FLAG_RX_PREV_12M,0) AS ACTIVE_FLAG_RX_PREV_12M
            FROM
            (
                SELECT PATIENT_GID, MIN_CLM_DT, MIN_CLM_DT_6M_LB, MIN_CLM_DT_12M_LB
                FROM period_to_be_elig
            ) A
            LEFT JOIN (
                SELECT PATIENT_GID, CLAIM_DATE, 1 AS ACTIVE_FLAG_MX_PREV_6M
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_MX_ACT_TBL_AML_EXACT_DATES_KA_v2
            ) B
              ON A.PATIENT_GID = B.PATIENT_GID
             AND A.MIN_CLM_DT > B.CLAIM_DATE
             AND A.MIN_CLM_DT_6M_LB <= B.CLAIM_DATE
            LEFT JOIN (
                SELECT PATIENT_GID, CLAIM_DATE, 1 AS ACTIVE_FLAG_RX_PREV_6M
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA
            ) C
              ON A.PATIENT_GID = C.PATIENT_GID
             AND A.MIN_CLM_DT > C.CLAIM_DATE
             AND A.MIN_CLM_DT_6M_LB <= C.CLAIM_DATE
            LEFT JOIN (
                SELECT PATIENT_GID, CLAIM_DATE, 1 AS ACTIVE_FLAG_MX_PREV_12M
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_MX_ACT_TBL_AML_EXACT_DATES_KA_v2
            ) D
              ON A.PATIENT_GID = D.PATIENT_GID
             AND A.MIN_CLM_DT_12M_LB <= D.CLAIM_DATE
             AND A.MIN_CLM_DT_6M_LB > D.CLAIM_DATE
            LEFT JOIN (
                SELECT PATIENT_GID, CLAIM_DATE, 1 AS ACTIVE_FLAG_RX_PREV_12M
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA
            ) E
              ON A.PATIENT_GID = E.PATIENT_GID
             AND A.MIN_CLM_DT_12M_LB <= E.CLAIM_DATE
             AND A.MIN_CLM_DT_6M_LB > E.CLAIM_DATE
        ) A
    ) B
    WHERE ELIG_FLG = 1
