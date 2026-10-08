-- VERIFIED QUERY REFERENCE
-- QUERY: AML_NPS_LINE_BACKBONE
-- QUESTION: How does the legacy NPS dashboard pick the backbone of each AML line?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 5
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: One row per patient x LOT from the LoT grouping table, with legacy-rule intensity and the legacy backbone: the highest-ranked product of the whole line on the IC_ELIG (28) or IC_INELIG (11) rank list. Named products (AZACITIDINE, not HMA).
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2_SATEEK; Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: nps_dashboard_legacy
-- REUSABLE_COMPONENTS: line-level backbone from rank lists, legacy-rule intensity join
-- KNOWN_ISSUE: SQL EQUIVALENT, not team code: the notebook does this in pandas (cell 29, get_backbone) and keeps it as the LOT_TBL temp view. Reads the personal _v2_SATEEK copy of the grouping table (OI-16). Patients with no cohort row use the IC_INELIG list. A line with no listed product gets UNKNOWN, which then has no backbone claim and so no NPI.
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
SELECT *
FROM LOT_TBL
