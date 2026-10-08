-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_HCP_INFO_MAP
-- QUESTION: Which HCP decile, above-brand and execution segment and account subtype attach to each AML line?
-- PRIMARY_KBT: 6
-- SECONDARY_KBTS: 4
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: One row per patient x LOT with the initiating NPI, Abbott id, UNI_DECILE, ABOVE_BRAND_SEGMENT, EXECUTION_SEGMENT (GNE) and FINAL_ACCOUNT_TYPE_2.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_NPI_ABOVE_BRAND_SEGMENT; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_NPI_GNE_BRAND_SEGMENT_BKP; heme_abbott_account (temp view)
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: segment joins on NPI, account subtype join on Abbott id
-- KNOWN_ISSUE: heme_abbott_account is a temp view, inlined. The segment tables are joined without de-duplication; an NPI listed twice duplicates the line. The GNE segment comes from the _BKP table ('15k AML Segmented HCPs'), not _v2. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_HCP_INFO_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK.
-- SOURCE: scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH reg_npi_aci AS (
    SELECT * FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
),
heme_abbott_account AS (
    -- cell 39 (temp view): one account subtype per HCP, lowest rank wins
    SELECT DISTINCT ABBOTT_CUSTOMER_ID, FINAL_ACCOUNT_TYPE_2, FINAL_ACCOUNT_TYPE_2_HIER
    FROM
    (
        SELECT *,
        MIN(FINAL_ACCOUNT_TYPE_2_HIER) OVER (PARTITION BY ABBOTT_CUSTOMER_ID) AS FIN_AC_TYPE
        FROM
        (
            SELECT *,
            CASE
                WHEN FINAL_ACCOUNT_TYPE_2 = 'Elite Oncology Center'  THEN 1 --CASE CHECK
                WHEN FINAL_ACCOUNT_TYPE_2 = 'Academic Teaching Hospital' THEN 2
                WHEN FINAL_ACCOUNT_TYPE_2 = 'IDN - Academic Affiliated' THEN 3
                WHEN FINAL_ACCOUNT_TYPE_2 = 'IDN - Community Affiliated' THEN 4
                WHEN FINAL_ACCOUNT_TYPE_2 = 'Corporate' THEN 5
                WHEN FINAL_ACCOUNT_TYPE_2 = 'Other Community' THEN 6
                WHEN FINAL_ACCOUNT_TYPE_2 = 'VA'THEN 7
                WHEN FINAL_ACCOUNT_TYPE_2 = 'DOD'THEN 8
                WHEN FINAL_ACCOUNT_TYPE_2 is NULL THEN 9
            END AS FINAL_ACCOUNT_TYPE_2_HIER
            FROM
            (
                SELECT A.ABBOTT_CUSTOMER_ID, A.CHILD_ABBOTT_ACCOUNT_ID,
                TRIM(B.FINAL_ACCOUNT_TYPE_) AS FINAL_ACCOUNT_TYPE_2
                FROM
                (
                    SELECT ABBOTT_CUSTOMER_ID, CHILD_ABBOTT_ACCOUNT_ID
                    FROM ABV_ADS_SYND.DIM_ACCOUNT_AFFILIATIONS_TBL --UPDATED
                    WHERE UNIVERSE_NAME='1VIEW_ONCOLOGY'
                    AND AFFILIATION_TYPE = 'HCI-HCP'
                    AND SALES_FORCE_CODE = 'ONH2'
                    AND DDS_ACTIVE_FLAG = 'Y'
                    AND ABBOTT_CUSTOMER_ID IN
                    (
                        SELECT DISTINCT ABBOTT_CUSTOMER_ID_REGIMEN
                        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
                    )

                    UNION

                    SELECT ABBOTT_CUSTOMER_ID, ORGANIZATION_ABBOTT_ACCOUNT_ID
                    FROM ABV_MA360_MHCDM.MHCD_RLTN_ALL_ORG_CUSTOMR_WKLY_TBL
                    WHERE ADS_ACTIVE_FLAG = 'Y'
                    AND VALUATION_INCLUDE_FLAG = 'Y'
                    AND ABBOTT_CUSTOMER_ID IN
                    (
                        SELECT DISTINCT ABBOTT_CUSTOMER_ID_REGIMEN
                        FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
                    )
                    AND ABBOTT_CUSTOMER_ID NOT IN
                    (
                        SELECT DISTINCT ABBOTT_CUSTOMER_ID
                        FROM ABV_ADS_SYND.DIM_ACCOUNT_AFFILIATIONS_TBL
                        WHERE UNIVERSE_NAME='1VIEW_ONCOLOGY'
                        AND AFFILIATION_TYPE = 'HCI-HCP'
                        AND SALES_FORCE_CODE = 'ONH2'
                        AND DDS_ACTIVE_FLAG = 'Y'
                    )
                )A
                LEFT JOIN
                (
                    SELECT *
                    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.heme_account
                )B
                ON CAST(A.CHILD_ABBOTT_ACCOUNT_ID AS BIGINT)=CAST(B.CHILD_ACCOUNT_ID AS BIGINT)
            )C
        )C
    )C
    WHERE FIN_AC_TYPE = FINAL_ACCOUNT_TYPE_2_HIER
)
SELECT A.*,
B.UNI_DECILE, B.ABOVE_BRAND_SEGMENT,
C.AML_EXECUTION_SEGMENT AS EXECUTION_SEGMENT,
D.FINAL_ACCOUNT_TYPE_2
FROM
(
    SELECT DISTINCT PATIENT_GID, REG_NUM, LOT, REGIMEN_START_DATE, REGIMEN_END_DATE,
    REGIMEN, BACKBONE, NPI_REGIMEN, ABBOTT_CUSTOMER_ID_REGIMEN
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
)A
LEFT JOIN
(
    SELECT *
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_NPI_ABOVE_BRAND_SEGMENT
)B
ON A.NPI_REGIMEN=B.NPI
LEFT JOIN
(
    SELECT *
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_NPI_GNE_BRAND_SEGMENT_BKP
)C
ON A.NPI_REGIMEN=C.NPI
LEFT JOIN
(
    SELECT *
    FROM heme_abbott_account
)D
ON A.ABBOTT_CUSTOMER_ID_REGIMEN=D.ABBOTT_CUSTOMER_ID
