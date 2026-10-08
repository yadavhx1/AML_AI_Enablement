-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_DASH_PBI_DATA
-- QUESTION: What is in the legacy AML NPS Power BI dataset?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 5
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Power BI input: one row per patient x LOT with backbone, BACKBONE_GROUP (VENCLEXTA / HMA / OTHER NOVEL AGENTS), line dates, NPI, Abbott id, decile, segments and account subtype with its rank.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: backbone group CASE, Not Available handling, account subtype rank
-- KNOWN_ISSUE: Despite 1L_IC_INELIG in the table name, the 1L, intensity and eligibility filters are commented out: every line, both intensities, no gates. OTHER NOVEL AGENTS includes UNKNOWN and non-novel backbones. dash_tbl (cell 60) is a temp view, inlined. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_UPDATED_BUSINESS_RULES_v2_SATEEK.
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
-- Step 7: Power BI dataset - one row per patient and line of therapy

    SELECT *,
    CASE
        WHEN ACCT_SUBTYPE = 'Elite Oncology Center'  THEN 1 --CASE CHECK
        WHEN ACCT_SUBTYPE = 'Academic Teaching Hospital' THEN 2
        WHEN ACCT_SUBTYPE = 'IDN - Academic Affiliated' THEN 3
        WHEN ACCT_SUBTYPE = 'IDN - Community Affiliated' THEN 4
        WHEN ACCT_SUBTYPE = 'Corporate' THEN 5
        WHEN ACCT_SUBTYPE = 'Other Community' THEN 6
        WHEN ACCT_SUBTYPE = 'VA'THEN 7
        WHEN ACCT_SUBTYPE = 'DOD'THEN 8
        ELSE 9
    END AS ACCT_SUBTYPE_HIER
    FROM
    (
        -- LOT keeps the lot grain; without it DISTINCT would collapse lines of therapy
        SELECT DISTINCT PATIENT_GID, LOT, REGIMEN, BACKBONE, BACKBONE_GROUP,
        REGIMEN_START_DATE, REGIMEN_END_DATE,
        UNI_DECILE_2 AS UNI_DECILE,
        NPI_REGIMEN_2 AS NPI, ABBOTT_CUSTOMER_ID_REGIMEN_2 AS ABBOTT_ID,
        ABOVE_BRAND_SEGMENT_2 AS ABOVE_BRAND_SEGMENT, EXECUTION_SEGMENT_2 AS GNE_SEGMENT,
        FINAL_ACCOUNT_TYPE_2_UPD AS ACCT_SUBTYPE
        FROM dash_tbl
    )A
