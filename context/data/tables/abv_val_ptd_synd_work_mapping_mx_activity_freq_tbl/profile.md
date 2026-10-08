# abv_val_ptd_synd.mapping_mx_activity_freq_tbl

Also catalogued as `abv_val_ptd_synd_work.mapping_mx_activity_freq_tbl` (fallback schema; SME Q-08).

**Family:** APLD
**Contains:** per-patient medical-activity periods used as the Mx half of the eligibility test
**Common analyses:** sha_nps_by_product, sha_nps_by_regimen, gpo_nps_by_product, gpo_nps_by_regimen

## Grain

Patient × frequency period. FREQUENCY_START_DATE "Represents the derived activity period rather than an individual claim date". (abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx)

## Primary keys or entity keys

PATIENT_SK + FREQUENCY_START_DATE + FREQUENCY + OFFSET. (stated as usage, not as declared keys)

## Row meaning

Captures any and all medical (MX) activity for patients in the VENCLEXTA PoI, enabling patient activity, eligibility, persistence, and treatment journey analyses. (abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx · Use Case)

## Refresh

Not stated.

## Mandatory filters

frequency = 'semesterly' AND `OFFSET` = '0' AND source_flag = 'SHA_PTD' AND source_market = 'ONC' AND market_code = 'ONC' (market_code filter required, SME Q-09/Q-10). (abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx; SHA NPS by Product (HCP Attributes Mapped).txt)

## Business rules

1. Same frequency and offset conventions as the Rx spine. (abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx)\n2. This table is the Mx half of the 3-year eligibility rule. \n3. Derivation, verbatim: "Mx Activity Table: SHA does not provide Mx activity table, it is derived by combining Px, Sx and Dx claims. Mx activity table contains Market (ONC) claims only." (AML SHA Business Rules Guide V5.pptx · slide 17)

## Join guidance

PATIENT_SK → strip 'SHA_PTDONC' to obtain PATIENT_GID; FREQUENCY_START_DATE joins to the semester spine. (SHA NPS by Product (HCP Attributes Mapped).txt)

## Caveats

1. Mx activity is ONC-market only, so non-oncology medical activity cannot establish eligibility through this table. (AML SHA Business Rules Guide V5.pptx · slide 17)\n2. The supplied dictionary duplicates the description text into the usage-notes cell for FREQUENCY_START_DATE.\n3. Schema: per SME Q-08 `abv_val_ptd_synd` is correct across all code; try it first and fall back to `abv_val_ptd_synd_work` (the name catalogued here) if not found, disclosing the fallback. (abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx)

AML base layer: the VEN lookback flags read this table from `abv_val_ptd_synd_work` without the `market_code='ONC'` filter. The AML continuity flags do not use it; they use exact-date activity tables (see `context/domain/aml_eligibility_flags.md`).

## Pipeline and lineage

Patient eligibility layer for NPS, persistency and the CLL LoT report

**Produced by:** Upstream VAL working-layer build — not produced by any supplied code.

**Source document:** abv_val_ptd_synd_work_mapping_mx_activity_freq_tbl_data_dictionary.xlsx
