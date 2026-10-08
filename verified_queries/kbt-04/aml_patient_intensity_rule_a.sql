-- VERIFIED QUERY REFERENCE
-- QUERY: AML_PATIENT_INTENSITY_RULE_A
-- QUESTION: How is each AML patient classified IC Eligible or IC Ineligible (production rule)?
-- PRIMARY_KBT: 4
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Legacy rule: LOW_INTENSITY = 0 when any regimen contains an IC-Eligible-only product; patient class = MIN over regimens; IC_INELIG when 1, else IC_ELIG.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL_v2
-- METRICS: none
-- REUSABLE_COMPONENTS: IC-Eligible-only product CASE, MIN over the journey
-- KNOWN_ISSUE: INQOVI and ONUREG are IC-Ineligible since the 2026 change; the RYD_MYL_FLG exception is commented out. Writes Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL_v2. May'26 run: 43,194 IC_INELIG / 14,503 IC_ELIG.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT A.*,
           CASE WHEN PATIENT_INTENSITY = 'IC_INELIG' THEN 'IC_INELIG'
           ELSE 'IC_ELIG'
           END AS PATIENT_INTENSITY_GROUP
    FROM
    (
        SELECT *
        FROM
        (
            SELECT *,
            CASE
                WHEN LOW_INTENSITY = 1 THEN 'IC_INELIG'
                ELSE 'IC_ELIG'
            END AS PATIENT_INTENSITY
            FROM
            (
                SELECT PATIENT_GID_RGMN, MIN(LOW_INTENSITY_INT) AS LOW_INTENSITY
                FROM
                (

                    --Simplified the code as well
          
                    SELECT *, LOW_INTENSITY AS LOW_INTENSITY_INT
                    
                    
                    --SELECT *,
                    --CASE    
                    --    WHEN LOW_INTENSITY = 0 THEN 0
                    --    WHEN LOW_INTENSITY = 0 AND RYD_MYL_FLG = 1 THEN 1
                    --    ELSE LOW_INTENSITY
                    --END AS LOW_INTENSITY_INT


                    FROM
                    (
                        SELECT *,
                        CASE 
          
                            WHEN REGIMEN LIKE '%ARSENIC_TRIOXIDE%' THEN 0
                            WHEN REGIMEN LIKE '%CLADRIBINE%' THEN 0
                            WHEN REGIMEN LIKE '%CLOFARABINE%' THEN 0
                            WHEN REGIMEN LIKE '%CYCLOPHOSPHAMIDE%' THEN 0
                            WHEN REGIMEN LIKE '%S-DAC%' THEN 0
                            WHEN REGIMEN LIKE '%HI-DAC%' THEN 0
                            WHEN REGIMEN LIKE '%DAUNORUBICIN%' THEN 0
                            WHEN REGIMEN LIKE '%ETOPOSIDE%' THEN 0
                            WHEN REGIMEN LIKE '%FILGRASTIM%' THEN 0
                            WHEN REGIMEN LIKE '%FLUDARABINE%' THEN 0
                            WHEN REGIMEN LIKE '%IDARUBICIN%' THEN 0
                            --WHEN REGIMEN LIKE '%INQOVI%' THEN 0  --NOW INQOVI CONSIDERED AS IC INELIG
                            WHEN REGIMEN LIKE '%MITOXANTRONE%' THEN 0
                            WHEN REGIMEN LIKE '%MYLOTARG%' THEN 0
                            WHEN REGIMEN LIKE '%NEXAVAR%' THEN 0
                            --WHEN REGIMEN LIKE '%ONUREG%' THEN 0  --NOW ONUREG CONSIDERED AS IC INELIG
                            WHEN REGIMEN LIKE '%RYDAPT%' THEN 0
                            WHEN REGIMEN LIKE '%VANFLYTA%' THEN 0
                            WHEN REGIMEN LIKE '%VINCRISTINE%' THEN 0
                            WHEN REGIMEN LIKE '%VYXEOS%' THEN 0
                            WHEN REGIMEN LIKE '%RYDAPT%' THEN 0
                            WHEN REGIMEN LIKE '%MYLOTARG%' THEN 0
                            ELSE 1
                        END AS LOW_INTENSITY

                        --Special condition for Rydapt and Mylotarg removed since they are considered only as IC Elig
                        --,CASE 
                        --    WHEN REGIMEN = ('RYDAPT, VENCLEXTA') OR REGIMEN = ('MYLOTARG, VENCLEXTA') 
                        --    OR REGIMEN = ('AZACITIDINE, RYDAPT') OR REGIMEN = ('DECITABINE, RYDAPT') 
                        --    OR REGIMEN = ('DECITABINE, MYLOTARG') OR REGIMEN = ('AZACITIDINE, MYLOTARG') THEN 1 
                        --    ELSE 0
                        --END AS RYD_MYL_FLG

                        FROM 
                        (
                            SELECT DISTINCT PATIENT_GID_RGMN, REGIMEN, REGIMEN_START_DATE, REGIMEN_END_DATE
                            FROM Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL_v2
                        )A
                    )A
                )A
                GROUP BY 1
            )A
        )A
    )A
