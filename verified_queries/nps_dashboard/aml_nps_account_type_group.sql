-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_ACCOUNT_TYPE_GROUP
-- QUESTION: How is the account type and account group of an AML NPS prescriber assigned?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 5
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Account subtype per HCP from the ONH2 HCI-HCP affiliations (Reltio for HCPs without one) joined to heme_account; the lowest-ranked subtype wins. Groups: Academic, Academic Satellite, Larger / Smaller Community (max child decile >= 8), Federal, Not Available.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK; ABV_ADS_SYND.DIM_ACCOUNT_AFFILIATIONS_TBL; ABV_MA360_MHCDM.MHCD_RLTN_ALL_ORG_CUSTOMR_WKLY_TBL; Z_ABV_CWS_MABI_ONC_ANALYTICS.heme_account; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_CHILD_ACCOUNT_DECILE
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: account subtype hierarchy, Reltio fallback, decile split of Community
-- KNOWN_ISSUE: heme_abbott_account_group is a temp view, inlined. The group table is written but no later cell reads it: the dashboard and rollup use the subtype (FINAL_ACCOUNT_TYPE_2) only, and the rollup re-groups it as Academic / Community. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_ACCT_TYPE_GRP_UPDATED_BUSINESS_RULES_v2_SATEEK.
-- SOURCE: scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH reg_npi_aci AS (
    SELECT * FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK
),
heme_abbott_account_group AS (
    -- cell 42 (temp view): same, keeping the child account id
    SELECT DISTINCT ABBOTT_CUSTOMER_ID, CHILD_ABBOTT_ACCOUNT_ID, FINAL_ACCOUNT_TYPE_2, FINAL_ACCOUNT_TYPE_2_HIER
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
SELECT DISTINCT ABBOTT_CUSTOMER_ID, FINAL_ACCOUNT_TYPE_GROUP_2,
CASE
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Academic' THEN 1
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Academic Satellite' THEN 2
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Larger Community' THEN 3
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Smaller Community' THEN 4
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Federal' THEN 5
    WHEN FINAL_ACCOUNT_TYPE_GROUP_2 = 'Not Available' THEN 6
END AS FINAL_ACCOUNT_TYPE_GROUP_2_HIER
FROM
(
    SELECT *,
    CASE
        WHEN MAX_ACCOUNT_DECILE IS NULL AND FINAL_ACCOUNT_TYPE_GROUP = 'Community' THEN 'Smaller Community'
        WHEN MAX_ACCOUNT_DECILE IS NOT NULL AND FINAL_ACCOUNT_TYPE_GROUP = 'Community' THEN
            CASE
                WHEN MAX_ACCOUNT_DECILE >= 8 THEN 'Larger Community'
                ELSE 'Smaller Community'
            END
        WHEN FINAL_ACCOUNT_TYPE_GROUP IS NULL THEN 'Not Available'
        ELSE FINAL_ACCOUNT_TYPE_GROUP
    END AS FINAL_ACCOUNT_TYPE_GROUP_2
    FROM
    (
        SELECT *,
        MAX(ACCOUNT_DECILE) OVER (PARTITION BY ABBOTT_CUSTOMER_ID) AS MAX_ACCOUNT_DECILE
        FROM
        (
            SELECT A.*, B.DECILE AS ACCOUNT_DECILE
            FROM
            (
                SELECT *,
                CASE
                    WHEN FINAL_ACCOUNT_TYPE_2 IN ('Elite Oncology Center','Academic Teaching Hospital') THEN 'Academic'
                    WHEN FINAL_ACCOUNT_TYPE_2 IN ('IDN - Academic Affiliated') THEN 'Academic Satellite'
                    WHEN FINAL_ACCOUNT_TYPE_2 IN ('IDN - Community Affiliated','Corporate','Other Community') THEN 'Community'
                    WHEN FINAL_ACCOUNT_TYPE_2 IN ('VA','DOD') THEN 'Federal'
                    ELSE NULL
                END AS FINAL_ACCOUNT_TYPE_GROUP
                FROM heme_abbott_account_group
            )A
            LEFT JOIN
            (
                SELECT *
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_CHILD_ACCOUNT_DECILE
            )B
            ON CAST(A.CHILD_ABBOTT_ACCOUNT_ID AS BIGINT)=CAST(B.ABBOTT_ACCOUNT_ID AS BIGINT)
        )A
    )A
)A
