-- VERIFIED QUERY REFERENCE
-- QUERY: AML_PRODUCT_CODE_LOOKUPS
-- QUESTION: Which NDC / procedure codes identify Onureg, Inqovi, Rezlidhia and Vanflyta in SHA?
-- PRIMARY_KBT: 1
-- SECONDARY_KBTS: 
-- DIALECT: Databricks / Spark SQL
-- PURPOSE: The four product-code lookups run in the globals cell (NDC from dim_product_vw by generic name + oral form, plus procedure codes by description).
-- DATA_SOURCE: SHA (SHA_PTD)
-- TABLES: abv_val_ptd_onc_synd.dim_product_vw; abv_val_ptd_onc_synd.px_fact_curated_vw
-- METRICS: none
-- REUSABLE_COMPONENTS: generic-name and form filters, procedure-description LIKE patterns
-- KNOWN_ISSUE: The resulting code lists (onureg_codes etc.) are not used by any later step in the five notebooks: products come from mastered_product_name. Kept as a mapping reference.
-- SOURCE: scripts/Notebooks (rendered with the notebook's table-name globals; CREATE TABLE wrappers removed so the reference only reads).
-- USE: Reuse fully when the request matches, or copy relevant components into a new working query.
-- ADAPTATION: Correct documented issues in the working query and disclose material changes; do not overwrite this reference.

-- ONUREG
select distinct source_product_ndc_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.dim_product_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%AZACITIDINE%') 
          AND SOURCE_DRUG_FORM IN ('TAB','CAP')
                                        
                                        UNION ALL
                                 select distinct procedure_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.px_fact_curated_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and UPPER(PROCEDURE_DESCription) LIKE ('%ONUREG%');

-- INQOVI
select distinct source_product_ndc_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.dim_product_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%DECITABINE/CEDAZURIDINE%') 
          AND SOURCE_DRUG_FORM IN ('TAB','CAP')        
                                 
                                       
                                        UNION ALL
                                        select distinct procedure_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.px_fact_curated_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and (UPPER(PROCEDURE_DESCription) LIKE ('%INQOVI%') or UPPER(PROCEDURE_DESCription) LIKE ('%DECITABINE/CEDAZURIDINE%'));

-- REZLIDHIA
select distinct source_product_ndc_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.dim_product_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and (UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%OLUTASIDENIB%') or UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%REZLIDHIA%'))

                                        
                                        UNION ALL
                                    select distinct procedure_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.px_fact_curated_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and (UPPER(PROCEDURE_DESCription) LIKE ('%REZLIDHIA%') or UPPER(PROCEDURE_DESCription) LIKE ('%OLUTASIDENIB%'));

-- VANFLYTA
select distinct source_product_ndc_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.dim_product_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and (UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%QUIZARTINIB%') or UPPER(SOURCE_DRUG_GENERIC_NAME) LIKE ('%VANFLYTA%'))


                                         
                                        UNION ALL
                                   select distinct procedure_code as PRODUCT_NDC_CODE
          from abv_val_ptd_onc_synd.px_fact_curated_vw
          where source_market = 'ONC'
          and source_flag = 'SHA_PTD'
          and (UPPER(PROCEDURE_DESCription) LIKE ('%VANFLYTA%') or UPPER(PROCEDURE_DESCription) LIKE ('%QUIZARTINIB%'));
