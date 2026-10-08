-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_IPSOS_INDEX
-- QUESTION: How does the SHA Venclexta NPS share compare with the reported (Ipsos) share by month?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 5
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Reported VEN and total NPS per month from the dashboard repository, next to the SHA VEN and total counts from the dashboard table by month of line start, from Jan 2019.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REPOSITORY; dash_tbl (temp view of Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK)
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: reported vs observed month join, MM/dd/yyyy month keys
-- KNOWN_ISSUE: SHA counts are rows of dash_tbl: every line, both intensities, no gates, not de-duplicated (a segment fan-out counts twice). The cell sits after spark.stop() (cell 88), so it fails in a top-to-bottom run and the dash_tbl temp view is gone; run it before cell 88. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_UPDATED_BUSINESS_RULES_v2.
-- SOURCE: scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH dash_tbl AS (
    -- cell 60 (temp view): backbone group and explicit "Not Available"
    SELECT *,
    CASE
        -- BACKBONE carries drug names, so HMA agents are listed explicitly
        WHEN BACKBONE = 'VENCLEXTA' THEN 'VENCLEXTA'
        WHEN BACKBONE IN ('AZACITIDINE','DECITABINE','ONUREG','INQOVI') THEN 'HMA'
        ELSE 'OTHER NOVEL AGENTS' --MIGHT INCLUDE SOME NON-NOVEL AGENTS AS WELL
    END AS BACKBONE_GROUP,
    CASE WHEN NPI_REGIMEN IS NULL THEN "Not Available" ELSE NPI_REGIMEN END AS NPI_REGIMEN_2,
    CASE WHEN ABBOTT_CUSTOMER_ID_REGIMEN IS NULL THEN "Not Available" ELSE ABBOTT_CUSTOMER_ID_REGIMEN END AS ABBOTT_CUSTOMER_ID_REGIMEN_2,
    CASE WHEN (UNI_DECILE IS NULL OR UNI_DECILE="-") THEN "Not Available" ELSE UNI_DECILE END AS UNI_DECILE_2,
    CASE WHEN ABOVE_BRAND_SEGMENT IS NULL THEN "Not Available" ELSE ABOVE_BRAND_SEGMENT END AS ABOVE_BRAND_SEGMENT_2,
    CASE WHEN EXECUTION_SEGMENT IS NULL THEN "Not Available" ELSE EXECUTION_SEGMENT END AS EXECUTION_SEGMENT_2,
    CASE WHEN FINAL_ACCOUNT_TYPE_2 IS NULL THEN "Not Available" ELSE FINAL_ACCOUNT_TYPE_2 END AS FINAL_ACCOUNT_TYPE_2_UPD
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
    -- All lines of therapy retained; do not reinstate the 1L filter below
    --WHERE REG_NUM = 1
    --AND PATIENT_GID IN
    --(
       -- SELECT DISTINCT PATIENT_GID
       -- FROM elig_flags_final
       -- WHERE DX_LB_ELIG_FLG = 1
        --AND TX_MX_LB_ELIG_FLG = 1 AND TX_RX_LB_ELIG_FLG = 1
        --AND DX_TX_DIFF_FLG = 1 AND SCT_DX_PX_FLG = 0 AND ARSENIC_FLG = 1
        --AND YEAR(FIRST_DX) >= 2019
        --AND PATIENT_COHORT = 'IC_INELIG'
    --)
)
-- Step 8: Index the reported NPS share against the share observed in SHA claims

    SELECT MONTH_REPO,
    VEN_NPS AS VEN_NPS_REP, TOTAL_NPS AS TOTAL_NPS_REP,
    VEN_NPS_SHA, TOTAL_NPS_SHA
    FROM
    (
        SELECT A.*, B.VEN_NPS_SHA, B.TOTAL_NPS_SHA, B.SHARE_SHA
        FROM
        (
            SELECT TO_DATE(CAST(UNIX_TIMESTAMP(MONTH_REP, 'MM/dd/yyyy') AS TIMESTAMP)) AS MONTH_REPO,
            VEN_NPS, TOTAL_NPS,
            (VEN_NPS/TOTAL_NPS) AS SHARE_REP
            FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REPOSITORY
        )A
        LEFT JOIN
        (
            SELECT DISTINCT TO_DATE(CAST(UNIX_TIMESTAMP(REGIMEN_MONTH, 'MM/dd/yyyy') AS TIMESTAMP)) AS REGIMEN_MONTH_SHA,
            VEN_NPS_SHA, TOTAL_NPS_SHA, (VEN_NPS_SHA/TOTAL_NPS_SHA) AS SHARE_SHA
            FROM
            (
                SELECT REGIMEN_MONTH,
                SUM(VEN_FLAG) AS VEN_NPS_SHA,
                COUNT(VEN_FLAG) AS TOTAL_NPS_SHA
                FROM
                (
                    SELECT *,
                    CASE WHEN BACKBONE='VENCLEXTA' THEN 1 ELSE 0 END AS VEN_FLAG
                    FROM
                    (
                        SELECT *,
                        CASE
                            WHEN MONTH(REGIMEN_START_DATE) > 9 THEN CONCAT(MONTH(REGIMEN_START_DATE),'/01/',YEAR(REGIMEN_START_DATE))
                            ELSE CONCAT('0', MONTH(REGIMEN_START_DATE),'/01/',YEAR(REGIMEN_START_DATE))
                        END AS REGIMEN_MONTH
                        FROM
                        (
                            SELECT *
                            FROM dash_tbl
                        )
                    )
                )
                GROUP BY 1
            )
        )B
        ON A.MONTH_REPO=B.REGIMEN_MONTH_SHA
    )A
    -- USER INPUT REQUIRED: reporting floor, Jan 2019
    WHERE MONTH_REPO >= TO_DATE('2019-01-01')
