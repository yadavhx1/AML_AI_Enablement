-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_LOT_MONTH_SUMMARY
-- QUESTION: What are AML NPS volume and Venclexta / HMA / other share by line of therapy and month?
-- PRIMARY_KBT: 6
-- SECONDARY_KBTS: 4
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: NPS volume and share by DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT, year and month. The published Summary sheet is DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1, PATIENT_COHORT = IC_INELIG, LOT = 1, rolled up to semesters.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_UPDATED_BUSINESS_RULES_v2_SATEEK; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL
-- METRICS: nps_dashboard_legacy, nps_count
-- REUSABLE_COMPONENTS: flags kept as dimensions, unmatched-flag labelling, monthly volume and share
-- KNOWN_ISSUE: PARTLY SQL EQUIVALENT: cell 72 is PySpark and is reproduced here; cell 80 is team SQL. Rendered with the shipped SUMMARY_TIME_BASIS = 'END' (month of line END, OI-17) and SUMMARY_START_YEAR = 2019. ARSENIC_FLG is not read; Legacy rule puts arsenic patients in IC_ELIG, so the IC_INELIG slice has none. The flags table is the un-suffixed Aug'26 build while the lines come from _v2 (OI-02). TOTAL_NPS is per slice; summing slices double-counts. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_LOT_MONTH_NPS_SUMMARY_UPDATED_BUSINESS_RULES_v2_SATEEK.
-- SOURCE: scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH elig_flag_df AS (
    -- cell 68
    SELECT DISTINCT patient_gid, dx_lb_elig_flg, dx_tx_diff_flg, patient_cohort
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL
),
dash_tbl_lot AS (
    -- SQL EQUIVALENT of cell 72 (PySpark): LEFT join to the flags, unmatched patients labelled -1 /
    -- 'Not Available', calendar parts of the regimen (= line) start and end dates
    SELECT D.*,
    CASE WHEN E.patient_cohort IS NULL THEN 0 ELSE 1 END AS FLAGS_MATCHED,
    COALESCE(E.dx_lb_elig_flg, -1) AS DX_LB_ELIG_FLG,
    COALESCE(E.dx_tx_diff_flg, -1) AS DX_TX_DIFF_FLG,
    COALESCE(E.patient_cohort, 'Not Available') AS PATIENT_COHORT,
    YEAR(D.REGIMEN_START_DATE) AS REGIMEN_START_YEAR,
    MONTH(D.REGIMEN_START_DATE) AS REGIMEN_START_MONTH,
    CONCAT(YEAR(D.REGIMEN_START_DATE), '-', LPAD(CAST(MONTH(D.REGIMEN_START_DATE) AS STRING), 2, '0')) AS REGIMEN_START_YEAR_MONTH,
    YEAR(D.REGIMEN_END_DATE) AS REGIMEN_END_YEAR,
    MONTH(D.REGIMEN_END_DATE) AS REGIMEN_END_MONTH,
    CONCAT(YEAR(D.REGIMEN_END_DATE), '-', LPAD(CAST(MONTH(D.REGIMEN_END_DATE) AS STRING), 2, '0')) AS REGIMEN_END_YEAR_MONTH
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_UPDATED_BUSINESS_RULES_v2_SATEEK D
    LEFT JOIN elig_flag_df E
    ON D.PATIENT_GID = E.patient_gid
)
-- Step 10: NPS volume and share by eligibility, cohort, line of therapy, year and month

    SELECT DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT, TIME_YEAR, TIME_MONTH, TIME_YEAR_MONTH,
    SUM(VEN_FLAG) AS VEN_NPS,
    SUM(HMA_FLAG) AS HMA_NPS,
    SUM(OTH_FLAG) AS OTHERS_NPS,
    COUNT(*) AS TOTAL_NPS,
    SUM(VEN_FLAG)/COUNT(*) AS VEN_SHARE,
    SUM(HMA_FLAG)/COUNT(*) AS HMA_SHARE,
    SUM(OTH_FLAG)/COUNT(*) AS OTHERS_SHARE
    FROM
    (
        -- One new patient start per patient and line of therapy
        SELECT DISTINCT PATIENT_GID, DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT,
        REGIMEN_END_YEAR AS TIME_YEAR,
        REGIMEN_END_MONTH AS TIME_MONTH,
        REGIMEN_END_YEAR_MONTH AS TIME_YEAR_MONTH,
        CASE WHEN BACKBONE_GROUP = 'VENCLEXTA' THEN 1 ELSE 0 END AS VEN_FLAG,
        CASE WHEN BACKBONE_GROUP = 'HMA' THEN 1 ELSE 0 END AS HMA_FLAG,
        CASE WHEN BACKBONE_GROUP = 'OTHER NOVEL AGENTS' THEN 1 ELSE 0 END AS OTH_FLAG
        FROM dash_tbl_lot
        WHERE REGIMEN_END_YEAR >= 2019
    )A
    GROUP BY DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT, TIME_YEAR, TIME_MONTH, TIME_YEAR_MONTH
