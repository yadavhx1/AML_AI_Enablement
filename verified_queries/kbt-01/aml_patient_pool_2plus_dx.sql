-- VERIFIED QUERY REFERENCE
-- QUERY: AML_PATIENT_POOL_2PLUS_DX
-- QUESTION: Which patients enter the AML base-layer pool (2+ AML diagnosis claims)?
-- PRIMARY_KBT: 1
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: Patients with more than one distinct AML-coded diagnosis claim ever, on the 37-code AML set, SHA_PTD only.
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: abv_val_ptd_onc_synd.dx_fact_curated_vw
-- METRICS: none
-- REUSABLE_COMPONENTS: 37-code AML diagnosis list, COUNT(DISTINCT mx_claim_id) > 1
-- KNOWN_ISSUE: Created as the temp view patient_pool; it is not persisted. No recency, competing-diagnosis or treatment requirement (open item OI-04). The Aug'26 eligibility build used market_code = 'VENC_AML' instead (OI-01).
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

SELECT distinct PATIENT_SK from
(
    select patient_sk, count(distinct mx_claim_id) as Count_of_claims
    FROM abv_val_ptd_onc_synd.dx_fact_curated_vw
    WHERE SOURCE_DIAGNOSIS_CODE_1 IN 
    (
        '205', '205.0', '205.00', '205.01', '205.02', 'C92', 'C92.9', 'C92.0', 'C92.00', 'C92.01', 
        'C92.02', 'C92.5', 'C92.50', 'C92.51', 'C92.52', 'C92.6', 'C92.60', 'C92.61', 'C92.62', 'C92.90', 
        'C92.A', 'C92.A0', 'C92.A1', 'C92.A2', 'C92.Z0', 'C93', 'C93.0', 'C93.00', 'C93.01', 'C93.02', 
        'C94.0', 'C94.00', 'C94.01', 'C94.2', 'C94.20', 'C94.21', 'C94.22'
    )
    and source_flag='SHA_PTD'
    group by 1
)
where count_of_claims>1
