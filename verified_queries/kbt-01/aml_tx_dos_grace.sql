-- VERIFIED QUERY REFERENCE
-- QUERY: AML_TX_DOS_GRACE
-- QUESTION: How are days of supply and grace assigned to AML treatment claims?
-- PRIMARY_KBT: 1
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: TX final table: Filgrastim removed, NATIVE_TYPE to RX/PX, DOS_FINAL (Rx claim DOS or 28 when NULL/<=0; fixed per product for PX) and per-product GRACE_VALUE.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: none
-- REUSABLE_COMPONENTS: Per-product grace CASE, Rx/PX DOS rule, Filgrastim exclusion
-- KNOWN_ISSUE: Oral products have no PX DOS branch; a PX claim for one would get NULL DOS (none observed in the Aug'26 QC). Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_FINAL_BUSINESS_RULE_CHANGE_VAL_v2.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT *
    FROM
    (
        SELECT *,
        CASE
            WHEN FINAL_PRODUCT_NAME IN ('ARSENIC_TRIOXIDE', 'AZACITIDINE', 'DAURISMO', 'DECITABINE', 'IDHIFA', 'L-DAC', 'REZLIDHIA', 'RYDAPT', 'TIBSOVO', 'VENCLEXTA', 'XOSPATA') THEN 60
            WHEN FINAL_PRODUCT_NAME IN ('ONUREG', 'VINCRISTINE', 'INQOVI', 'VANFLYTA') THEN 28
            WHEN FINAL_PRODUCT_NAME IN ('NEXAVAR') THEN 18
            WHEN FINAL_PRODUCT_NAME IN ('CLADRIBINE', 'HI-DAC', 'MYLOTARG', 'S-DAC') THEN 7
            WHEN FINAL_PRODUCT_NAME IN ('CLOFARABINE', 'CYCLOPHOSPHAMIDE','DAUNORUBICIN', 'ETOPOSIDE', 'FLUDARABINE', 'IDARUBICIN', 'VYXEOS') THEN 5
            WHEN FINAL_PRODUCT_NAME IN ('MITOXANTRONE') THEN 3
            ELSE NULL
        END AS GRACE_VALUE
        FROM
        (
            SELECT *,
            CASE
                WHEN NATIVE_TYPE = 'RX' THEN 
                    CASE
                        WHEN (PRODUCT_DAYS_SUPPLY IS NULL OR PRODUCT_DAYS_SUPPLY <= 0) THEN 28
                        ELSE PRODUCT_DAYS_SUPPLY
                    END
                WHEN NATIVE_TYPE = 'PX' THEN
                    CASE
                        WHEN FINAL_PRODUCT_NAME = 'ARSENIC_TRIOXIDE' THEN 28 --28D CYCLE
                        WHEN FINAL_PRODUCT_NAME = 'AZACITIDINE' THEN 28 --28D CYCLE
                        WHEN FINAL_PRODUCT_NAME = 'CLADRIBINE' THEN 1
                        WHEN FINAL_PRODUCT_NAME = 'CLOFARABINE' THEN 1
                        WHEN FINAL_PRODUCT_NAME = 'CYCLOPHOSPHAMIDE' THEN 1
                        WHEN FINAL_PRODUCT_NAME IN ('L-DAC', 'S-DAC', 'HI-DAC') THEN 1
                        WHEN FINAL_PRODUCT_NAME = 'DAUNORUBICIN' THEN 1 --GRACE 5
                        WHEN FINAL_PRODUCT_NAME = 'DECITABINE' THEN 28 --28D CYCLE
                        WHEN FINAL_PRODUCT_NAME = 'ETOPOSIDE' THEN 1 --GRACE 5
                        WHEN FINAL_PRODUCT_NAME = 'FLUDARABINE' THEN 1
                        WHEN FINAL_PRODUCT_NAME = 'IDARUBICIN' THEN 1 --GRACE 5
                        WHEN FINAL_PRODUCT_NAME = 'MITOXANTRONE' THEN 1
                        WHEN FINAL_PRODUCT_NAME = 'MYLOTARG' THEN 1 --GRACE 7
                        WHEN FINAL_PRODUCT_NAME = 'VINCRISTINE' THEN 1 --GRACE 28
                        WHEN FINAL_PRODUCT_NAME = 'VYXEOS' THEN 1
                    END
            END AS DOS_FINAL
            FROM
            (
                SELECT DISTINCT PATIENT_GID, PRODUCT_QTY_DISPENSED, NPI_NUMBER,
                CASE
                    WHEN NATIVE_TYPE LIKE '%RX%' THEN 'RX'
                    ELSE 'PX'
                END AS NATIVE_TYPE,
                CLAIM_ID, CLAIM_DATE, PRODUCT_CODE, FINAL_PRODUCT_NAME AS FINAL_PRODUCT_NAME, 
                PRODUCT_DAYS_SUPPLY AS PRODUCT_DAYS_SUPPLY
                FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_UPDATED_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2
                WHERE FINAL_PRODUCT_NAME <> 'FILGRASTIM'
            )A
        )A
    )A
