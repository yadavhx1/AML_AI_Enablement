# abv_val_ptd_synd.mapping_rx_activity_freq_tbl

Also catalogued as `abv_val_ptd_synd_work.mapping_rx_activity_freq_tbl` (fallback schema; SME Q-08).

**Family:** APLD
**Contains:** per-patient pharmacy-activity periods used as the Rx half of the eligibility test
**Common analyses:** sha_persistency, sha_nps_by_product, sha_nps_by_regimen, gpo_nps_by_product, gpo_nps_by_regimen

## Grain

Patient × frequency period. FREQUENCY_START_DATE "Represents the derived activity period rather than an individual claim date". (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx)

## Primary keys or entity keys

PATIENT_SK + FREQUENCY_START_DATE + FREQUENCY + OFFSET. (stated as usage, not as declared keys)

## Row meaning

Captures any and all medical (RX) activity for patients in the VENCLEXTA PoI, enabling patient activity, eligibility, persistence, and treatment journey analyses. (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx · Use Case)

## Refresh

Not stated.

## Mandatory filters

frequency = 'semesterly' AND `OFFSET` = '0' AND source_flag = 'SHA_PTD' AND source_market = 'ONC'. (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx; SHA- Persistency.sql; SHA NPS by Product (HCP Attributes Mapped).txt)\nmarket_code = 'ONC' is also REQUIRED (SME Q-09/Q-10). 'ONC' is correct here because the activity tables are scoped by therapeutic area, not brand basket. The supplied persistency query omits the filter and its denominator is too wide. (SHA NPS by Product (HCP Attributes Mapped).txt vs SHA- Persistency.sql)

## Business rules

1. FREQUENCY selects the granularity, "e.g., frequency = 'semesterly' for 3-year patient eligibility calculations". (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx)\n2. OFFSET selects the period version, "commonly OFFSET = '0'". (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx)\n3. This table is one of the two inputs to the 3-year patient eligibility rule: a patient is eligible when Rx or Mx activity is present in more than 5 of the 6 semesters preceding the new-start semester. (.xlsx · PATIENT_ELIG; SHA NPS by Product (HCP Attributes Mapped).txt)\n4. "Rx Activity Table: SHA provides Rx Market (ONC) and Rx-nonmarket (Non ONC) claims". (AML SHA Business Rules Guide V5.pptx · slide 17)

## Join guidance

PATIENT_SK → strip 'SHA_PTDONC' to obtain PATIENT_GID; FREQUENCY_START_DATE joins to the semester spine derived from CLAIM_DATE (month <= 6 → YYYY-01-01, month > 6 → YYYY-07-01). (SHA NPS by Product (HCP Attributes Mapped).txt)

## Caveats

1. "Patient matching depends on consistent patient identifiers across sources." (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx)\n2. The supplied dictionary duplicates the description text into the usage-notes cell for FREQUENCY_START_DATE. (abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx)\n3. Schema: the SME answer to Q-08 is that `abv_val_ptd_synd` is correct and should be used across all code (SHA- Persistency.sql already does). The SHA NPS queries and this catalog name `abv_val_ptd_synd_work`. Try `abv_val_ptd_synd` first and fall back to `abv_val_ptd_synd_work` if the object is not found, disclosing the fallback.

AML base layer: the VEN lookback flags read this table from `abv_val_ptd_synd_work` without the `market_code='ONC'` filter. The AML continuity flags do not use it; they use exact-date activity tables (see `context/domain/aml_eligibility_flags.md`).

## Pipeline and lineage

Patient eligibility layer for NPS, persistency and the CLL LoT report

**Produced by:** Upstream VAL working-layer build — not produced by any supplied code.

**Source document:** abv_val_ptd_synd_work_mapping_rx_activity_freq_tbl_data_dictionary.xlsx
