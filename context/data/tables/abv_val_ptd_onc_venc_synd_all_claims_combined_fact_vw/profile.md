# abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw

**Family:** APLD
**Contains:** claim-level RX/PX/SX APLD for the Venclexta patient universe with episode, regimen, backbone and line of therapy already mapped on
**Common analyses:** hcp_competitor_trx_gpo, sha_persistency, patient_flow_sequencing, time_to_treatment, sha_nps_by_product, sha_nps_by_regimen, cll_lot_base

## Grain

Not stated as a single sentence. One row per claim per patient surrogate key: claim_id is "the finest-grain uniqueness token on the claim", and patient_sk maintains "the granularity in the dimension table at the source flag and source market level". (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)

## Primary keys or entity keys

claim_id (uniqueness token); patient_sk (patient grain). Stated as such rather than declared keys. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)

## Row meaning

A claim-level RX, PX or SX activity record for a patient in the VENCLEXTA Point-of-Interest, with treatment episode, regimen and line of therapy already mapped on. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx · Use Case)

## Refresh

Not stated.

## Mandatory filters

SOURCE_FLAG = SHA / KOMODO / Purple Labs, SOURCE_MARKET = ONC, and MARKET_CODE = VENC_CLL / VENC_AML. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx · Use Case)\nEvery supplied verified-query library query uses the SHA form: source_flag='SHA_PTD' AND source_market='ONC' AND market_code='VENC_CLL'. Persistency additionally widens to market_code IN ('VENC_CLL','VENC_AML','VENC_CLL_AML_OTHERS') when resolving IND_FINAL. (SHA- Persistency.sql; SHA NPS by Product (HCP Attributes Mapped).txt)

## Business rules

1. PATIENT_GID is derived, not stored: "Strip the literal prefix of data source 'SHA_PTDONC' (REPLACE(patient_sk,'SHA_PTDONC','')) to derive PATIENT_GID". (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n2. The episode, regimen and line-of-therapy values are INHERITED from this processed view, not computed at query time. The custom_field columns carry them: custom_field_name_3 = episode start date, custom_field_value_4 = episode end date, custom_field_value_5 = regimen start date, custom_field_value_6 = regimen end date, custom_field_value_7 = derived regimen; `regimen`, `backbone`, `lot` and `mastered_indication` are the mastered columns. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n3. mastered_product_name is "aliased to FINAL_PRODUCT_NAME downstream" and mdm_npi_number "aliased to NPI_NUMBER"; the 'mdm_' prefix "indicates the value has already passed through master data management rather than being the raw claim NPI". (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n4. backbone groups regimens "into categories such as CIT, BTKi and BCL2". The supplied verified-query library mapping is: CIT = FLUDARABINE, TREANDA, VINCRISTINE, CHLORAMBUCIL, GAZYVA, RITUXAN, CYCLOPHOSPHAMIDE, ARZERRA, CAMPATH; BTKi = IMBRUVICA, CALQUENCE, BRUKINSA, JAYPIRCA; BCL2 = VENCLEXTA; I+V = 'IMBRUVICA+VENCLEXTA'; ELSE 'OTHERS'. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx; SHA-Time to Treatment.sql)\n5. source_type distinguishes claim type "such as pharmacy (RX), procedure (PX), surgical (SX), or diagnosis (DX)". The queries compare it against the literal 'RX FACT'. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx; SHA- Persistency.sql)\n6. PRODUCT_QTY_DISPENSED is "primarily for AML analyses" and "Not used in CLL analyses"; SOURCE_PATIENT_HIPAA_BIRTH_YEAR is likewise "primarily for AML analyses" and "not used for CLL analyses". (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)

## Join guidance

PATIENT_GID (derived from patient_sk) is the join key to dx_fact_vw, the Rx/Mx activity frequency tables, the GPO dispense table's sha_patient_id and the GPO regimen tables. mdm_npi_number → ABV_DDS_SYND.CUSTOMER_TBL.NPI_NUMBER for ABBOTT_CUSTOMER_ID, and → z_abv_cws_mabi_onc_analytics.HCP_Attributes_table_final for HCP attributes. The supplied NPS queries join HCP attributes twice — once by ABBOTT_CUSTOMER_ID and once by NPI_NUMBER — de-duplicating each side with ROW_NUMBER() = 1 and then COALESCE-ing. (SHA NPS by Product (HCP Attributes Mapped).txt)

## Caveats

1. "SHA and KOMODO feeds are not fully interchangeable and may differ in structure and available fields; downstream logic may need to change when switching sources." (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n2. "LOT is claims-derived and should not be interpreted as a direct representation of physician-documented clinical lines; assignment depends on the underlying LOT rules." (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n3. "Claims-based regimen identification may not capture the complete clinical intent or actual administration sequence." (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n4. PRODUCT_DAYS_SUPPLY "may be missing or unreliable for certain products/claim types and may require product-specific rules or imputation" — hence the per-product DOS rules in the NPS queries. (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n5. market_code "Represents a broader market basket and should not be treated as a single-product flag". (abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx)\n6. SHA capture is partial: "Rx data: 65 – 70% data capture" and "Hospital and Procedure data: 30 - 40% data"; "SHA is a Switch and collects data from other Switches" and "Might lead to incomplete longitudinal journeys if patients use different switches". (Notes_Data Sources_1.pdf · page 2)\n7. market_code values: VENC_CLL, VENC_AML, VENC_CLL_AML_OTHER (singular; the plural is a typo). Activity tables use 'ONC' (SME Q-09). Activity-table schema: `abv_val_ptd_synd` (SME Q-08).\n9. Refresh: monthly for SHA and KOMODO, 2-month data lag; a Sep'26 refresh carries SHA data ending Jul'26 (SME Q-01). The view applies no enrollment screen (SME Q-55), and the upstream build ran on unfiltered history (SME Q-56).\n10. patient_sk carries the source suffix, e.g. 217656241SHA_PTDONC; strip 'SHA_PTDONC' for PATIENT_GID. The suffix is common to all VAL tables (SME Q-22).\n8. MIN_CLL_DX is selected by SHA-Time to Treatment.sql but is not in the supplied column list. See Q-06.

## Raw feed fields

The raw SHA PTD and Komodo field behind each column used by the base layer is in
`context/data/source_dictionaries/view_column_lineage.tsv`. The full vendor layouts are in
`context/data/source_dictionaries/` (SHA_Data_Dictionary.xlsx, Komodo_Data_Dictionary.xlsx).

## Pipeline and lineage

The primary APLD source for VENCLEXTA PoI analyses across CLL and AML; upstream of the SHA persistency, patient-flow, time-to-treatment and NPS query set, and of the CLL LoT report

**Produced by:** Upstream VAL (processed APLD) view — not produced by any supplied code. Its episode, regimen and LoT columns are produced by the upstream VAL build, whose rules are documented in CLL_LoT_Business_rules_v1_ZS.pptx and AML SHA Business Rules Guide V5.pptx.

**Source document:** abv_val_ptd_onc_venc_synd_all_claims_combined_fact_vw_Data_Dictionary.xlsx
