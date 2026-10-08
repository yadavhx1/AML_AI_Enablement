-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_REG_NPI_ACI
-- QUESTION: Which HCP is the initiating prescriber of each AML line in the NPS dashboard?
-- PRIMARY_KBT: 6
-- SECONDARY_KBTS: 4
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Joins each line to its backbone-product claims inside the line dates; the NPI on the first backbone claim (date ASC, NPI DESC, claim id) becomes NPI_REGIMEN, mapped to the Abbott customer id.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: LOT_TBL (temp view); abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw; ABV_DDS_SYND.CUSTOMER_TBL
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: first-backbone-claim NPI attribution, NPI to ABBOTT_CUSTOMER_ID
-- KNOWN_ISSUE: Claim grain (one row per backbone claim in the line; the LEFT join keeps lines with none). REG_NUM is LOT here. Claims filter: ONC / SHA_PTD / VENC_AML, no FILGRASTIM, NPI not null. updated_tx_tbl is in a commented-out FROM ('tO BE CONFIRMED'); the claims view is read instead. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_NPS_DASHBOARD_REG_NPI_ACI_MAPPING_UPDATED_BUSINESS_RULES_v2_SATEEK.
-- SOURCE: scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

WITH REGIMEN_LOT_TBL AS (
    -- cell 26: every line (not only 1L) with the legacy-rule intensity group
    SELECT A.*, B.PATIENT_INTENSITY_GROUP
    FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2_SATEEK A
    LEFT JOIN (SELECT * FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL_v2) B
    ON A.PATIENT_GID = B.PATIENT_GID_RGMN
),
LOT_PRODUCTS AS (
    -- SQL EQUIVALENT of cell 29 (pandas get_backbone): rank each product of the line on the patient's list.
    -- Anything other than IC_ELIG, including no cohort row, uses the IC_INELIG list.
    SELECT R.*, TRIM(P) AS PRODUCT,
    CASE
        WHEN R.PATIENT_INTENSITY_GROUP = 'IC_ELIG' THEN
            ARRAY_POSITION(ARRAY('S-DAC', 'HI-DAC', 'VANFLYTA', 'VYXEOS', 'CYCLOPHOSPHAMIDE', 'VINCRISTINE', 'FLUDARABINE',
                           'IDARUBICIN', 'DAUNORUBICIN', 'MITOXANTRONE', 'RYDAPT', 'VENCLEXTA', 'XOSPATA', 'TIBSOVO',
                           'REZLIDHIA', 'IDHIFA', 'MYLOTARG', 'DAURISMO', 'ONUREG', 'INQOVI', 'NEXAVAR', 'ETOPOSIDE',
                           'CLADRIBINE', 'CLOFARABINE', 'AZACITIDINE', 'DECITABINE', 'L-DAC', 'ARSENIC_TRIOXIDE'), TRIM(P))
        ELSE
            ARRAY_POSITION(ARRAY('VENCLEXTA', 'TIBSOVO', 'REZLIDHIA', 'IDHIFA', 'XOSPATA', 'DAURISMO', 'L-DAC',
                           'AZACITIDINE', 'DECITABINE', 'INQOVI', 'ONUREG'), TRIM(P))
    END AS PRODUCT_RANK   -- 0 = product not on the list
    FROM REGIMEN_LOT_TBL R
    LATERAL VIEW EXPLODE(SPLIT(R.LOT_REGIMEN_GROUP, ',')) E AS P
),
LOT_TBL AS (
    -- Backbone = highest-ranked product of the line (named product, not 'HMA'); 'UNKNOWN' if none is listed
    SELECT PATIENT_GID, LOT, LOT_START_DATE, LOT_END_DATE, LOT_REGIMEN_GROUP, PATIENT_INTENSITY_GROUP,
    COALESCE(MAX(CASE WHEN RN = 1 AND PRODUCT_RANK > 0 THEN PRODUCT END), 'UNKNOWN') AS BACKBONE
    FROM
    (
        SELECT *,
        ROW_NUMBER() OVER (PARTITION BY PATIENT_GID, LOT
                           ORDER BY CASE WHEN PRODUCT_RANK > 0 THEN PRODUCT_RANK ELSE 999 END) AS RN
        FROM LOT_PRODUCTS
    )A
    GROUP BY PATIENT_GID, LOT, LOT_START_DATE, LOT_END_DATE, LOT_REGIMEN_GROUP, PATIENT_INTENSITY_GROUP
)
SELECT B.*,
C.ABBOTT_CUSTOMER_ID AS ABBOTT_CUSTOMER_ID_REGIMEN
FROM
(
    SELECT *,
    MAX(NPI_INT) OVER (PARTITION BY PATIENT_GID, REG_NUM) AS NPI_REGIMEN
    FROM
    (
        SELECT *,
        CASE
            WHEN RNO_BKBONE = 1 THEN NPI_NUMBER
            ELSE NULL
        END AS NPI_INT
        FROM
        (
            SELECT *,
            CASE
                WHEN FINAL_PRODuct_NAME_updated = BACKBONE THEN RNO_PROD --FIRST CLAIM FOR BACKBONE PRODUCT
                ELSE 0
            END AS RNO_BKBONE
            FROM
            (
                SELECT *,
                ROW_NUMBER() OVER (PARTITION BY PATIENT_GID, REG_NUM, FINAL_PROD_NAME ORDER BY CLAIM_DATE ASC, NPI_NUMBER DESC, CLAIM_ID) AS RNO_PROD,
                ROW_NUMBER() OVER (PARTITION BY PATIENT_GID, REG_NUM ORDER BY CLAIM_DATE ASC, NPI_NUMBER DESC, CLAIM_ID) AS RNO_DATE --FIRST CLAIM BY DATE WITHIN REGIMEN

                FROM
                (
                    SELECT *,
                    -- Hypomethylating agents are grouped as HMA
                    CASE
                        WHEN FINAL_PRODUCT_NAME_UPDATED IN ('AZACITIDINE','DECITABINE', 'ONUREG', 'INQOVI') THEN 'HMA'
                        ELSE FINAL_PRODUCT_NAME_UPDATED
                    END AS FINAL_PROD_NAME
                    FROM
                    (
                        SELECT A.*,
                        B.CLAIM_DATE, B.CLAIM_ID, B.FINAL_PRODUCT_NAME_UPDATED, B.NPI_NUMBER
                        FROM
                        (
                            --SELECT PATIENT_GID, REGIMEN, REGIMEN_START_DATE, REGIMEN_END_DATE, BACKBONE, REG_NUM, LOT
                            --FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL
                            SELECT PATIENT_GID, LOT_REGIMEN_GROUP AS REGIMEN, LOT_START_DATE AS REGIMEN_START_DATE,
                             LOT_END_DATE AS REGIMEN_END_DATE, BACKBONE, LOT AS REG_NUM, LOT
                            FROM LOT_TBL
                            --WHERE LOT = 1
                        )A
                        LEFT JOIN
                        (
                            SELECT DISTINCT PATIENT_SK AS PATIENT_GID, CLAIM_ID, CLAIM_DATE,
                            PROCEDURE_CODE AS PRODUCT_CODE, MASTERED_PRODUCT_NAME AS FINAL_PRODUCT_NAME_UPDATED, MDM_NPI_NUMBER AS NPI_NUMBER
                            -- tO BE CONFIRMED
                            --FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2_SATEEK
                            FROM abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw

                            where source_market  =  'ONC'
                            and source_flag  =  'SHA_PTD'
                            and market_code = 'VENC_AML'
                            -- Filgrastim is supportive care, not a treatment product
                            AND MASTERED_PRODUCT_NAME <> "FILGRASTIM"
                            AND MDM_NPI_NUMBER IS NOT NULL
                        )B
                        ON A.PATIENT_GID = B.PATIENT_GID
                        AND A.BACKBONE = B.FINAL_PRODUCT_NAME_UPDATED
                        AND TO_DATE(B.CLAIM_DATE) >= TO_DATE(A.REGIMEN_START_DATE)
                        AND TO_DATE(B.CLAIM_DATE) <= TO_DATE(A.REGIMEN_END_DATE)
                    )A
                )A
            )A
        )A
    )A
)B
LEFT JOIN
(
    SELECT DISTINCT ABBOTT_CUSTOMER_ID, NPI_NUMBER
    FROM ABV_DDS_SYND.CUSTOMER_TBL
    WHERE DDS_ACTIVE_FLAG = 'Y'
)C
ON B.NPI_REGIMEN = C.NPI_NUMBER
