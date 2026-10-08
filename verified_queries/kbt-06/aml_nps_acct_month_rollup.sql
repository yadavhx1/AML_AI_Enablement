-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_ACCT_MONTH_ROLLUP
-- QUESTION: What are AML NPS counts by month and account subtype / group for the dashboard?
-- PRIMARY_KBT: 6
-- SECONDARY_KBTS: 4
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Venclexta, HMA, other-novel and total SHA NPS by month of line start, account subtype and Academic / Community group, on the reported months of the index table.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_UPDATED_BUSINESS_RULES_v2; dash_tbl (temp view of Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK)
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: Academic / Community regroup, backbone group flags by month
-- KNOWN_ISSUE: Counts DISTINCT patient x backbone x line start x subtype rows: every line, both intensities, no gates. Academic = Elite Oncology Center or Academic Teaching Hospital; everything else, including Not Available and Federal, is Community. Same spark.stop() ordering issue as AML_NPS_IPSOS_INDEX. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_FINAL_DATA_MONTH_ROLLUP_UPDATED_BUSINESS_RULES_v2.
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
-- Step 9: FINAL ROLLUP - NPS counts by month, account subtype and account group

    SELECT INDX.*,
    SHS.ACCT_SUB_TYPE_GRP, SHS.ACCT_SUB_TYPE,
    SHS.VEN_NPS_SHA, SHS.HMA_NPS_SHA, SHS.NOV_NPS_SHA, SHS.TOTAL_NPS_SHA,
    CASE
        WHEN ACCT_SUB_TYPE = 'Elite Oncology Center'  THEN 1 --CASE CHECK
        WHEN ACCT_SUB_TYPE = 'Academic Teaching Hospital' THEN 2
        WHEN ACCT_SUB_TYPE = 'IDN - Academic Affiliated' THEN 3
        WHEN ACCT_SUB_TYPE = 'IDN - Community Affiliated' THEN 4
        WHEN ACCT_SUB_TYPE = 'Corporate' THEN 5
        WHEN ACCT_SUB_TYPE = 'Other Community' THEN 6
        WHEN ACCT_SUB_TYPE = 'VA'THEN 7
        WHEN ACCT_SUB_TYPE = 'DOD'THEN 8
        ELSE 9
    END AS ACCT_SUB_TYPE_HIER,
    CASE
        WHEN ACCT_SUB_TYPE_GRP = 'Academic' THEN 1
        WHEN ACCT_SUB_TYPE_GRP = 'Community' THEN 2
    END AS ACCT_SUB_TYPE_GRP_HIER
    FROM
    (
        SELECT DISTINCT MONTH_REPO
        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_UPDATED_BUSINESS_RULES_v2
    )INDX
    LEFT JOIN
    (
        SELECT DISTINCT TO_DATE(CAST(UNIX_TIMESTAMP(REGIMEN_MONTH, 'MM/dd/yyyy') AS TIMESTAMP)) AS REGIMEN_MONTH_SHA,
        ACCT_SUB_TYPE_GRP,
        ACCT_SUB_TYPE,
        SUM(VEN_FLAG) AS VEN_NPS_SHA,
        SUM(HMA_FLAG) AS HMA_NPS_SHA,
        SUM(NOV_FLAG) AS NOV_NPS_SHA,
        COUNT(VEN_FLAG) AS TOTAL_NPS_SHA
        FROM
        (
            SELECT *,
            CASE
                WHEN MONTH(REGIMEN_START_DATE) > 9 THEN CONCAT(MONTH(REGIMEN_START_DATE),'/01/',YEAR(REGIMEN_START_DATE))
                ELSE CONCAT('0', MONTH(REGIMEN_START_DATE),'/01/',YEAR(REGIMEN_START_DATE))
            END AS REGIMEN_MONTH,
            -- Venclexta, HMA and other novel agent starts counted separately
            CASE WHEN BACKBONE_GROUP='VENCLEXTA' THEN 1 ELSE 0 END AS VEN_FLAG,
            CASE WHEN BACKBONE_GROUP='HMA' THEN 1 ELSE 0 END AS HMA_FLAG,
            CASE WHEN BACKBONE_GROUP='OTHER NOVEL AGENTS' THEN 1 ELSE 0 END AS NOV_FLAG,
            CASE
                WHEN ACCT_SUB_TYPE IN ('Elite Oncology Center', 'Academic Teaching Hospital') THEN 'Academic'
                ELSE 'Community'
            END AS ACCT_SUB_TYPE_GRP
            FROM
            (
                SELECT DISTINCT PATIENT_GID, BACKBONE, BACKBONE_GROUP, REGIMEN_START_DATE, FINAL_ACCOUNT_TYPE_2_UPD AS ACCT_SUB_TYPE
                FROM dash_tbl
            )A
        )A
        GROUP BY 1,2,3
    )SHS
    ON INDX.MONTH_REPO = SHS.REGIMEN_MONTH_SHA
