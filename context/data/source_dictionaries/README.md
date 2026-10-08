# Source data dictionaries - SHA and Komodo

Vendor layouts for the two claims feeds behind the VAL views (`source_flag = 'SHA_PTD'` and `'KOMODO'`).
The AML base layer never reads these raw tables. It reads the processed views
(`abv_val_ptd_onc_venc_synd.all_claims_combined_fact_vw`, `abv_val_ptd_onc_synd.dx_fact_curated_vw`, ...),
which are built from them upstream. Use these files to explain where a view column comes from, what a
raw code means, or what a feed can and cannot provide. Do not query the raw table names.

| Folder | Source file | Content |
|---|---|---|
| `sha_ptd/` | `SHA_Data_Dictionary.xlsx`, sheet "File Layout" ("ABBVIE ONC PTD LAYOUT") | 30 tables, 277 columns: patient, Rx claims, Dx, Px, Sx, drug, plan, practitioner, panels and code tables |
| `komodo/` | `Komodo_Data_Dictionary.xlsx`, sheet "EXTERNAL FACING Data Dictionary" | 7 tables, 90 columns: pharmacy events, medical events, plans, providers, patient demographics, geography and enrollment |

Each folder has `columns.tsv` (`table_name`, `column_name`, `data_type`, `description`, `notes`).
Values are copied from the workbooks with whitespace normalised. SHA notes come from the NOTES column;
Komodo notes merge `additional_notes` with any `treatment` other than "No change". Komodo's
`column_fill_rate` column is empty in the source and is not carried over.
`view_column_lineage.tsv` maps the view columns the base layer uses to the likely raw field in each feed.

## SHA (Symphony Health PTD) - tables

| Group | Tables |
|---|---|
| Patient | PTD_PATIENT, PTD_PATIENT_MEDIGAP, PTD_PATIENT_ACTIVITY, PTD_PATIENT_MPD, PTD_NEW_PATIENTS |
| Rx claims | PTD_RX_CLAIM_MARKET (40 columns), PTD_RX_CLAIM_NON_MARKET |
| Medical claims | PTD_DIAGNOSIS, PTD_PROCEDURE, PTD_PHYSICIAN_ROLE, PTD_SURGICAL_PROCEDURE |
| Dimensions | PTD_DRUG, PTD_PLAN, PTD_PHYSICIAN, PTD_PHYSICIAN_PANEL, PTD_RX_STORE_PANEL |
| Code tables | PTD_DIAGNOSIS_CODE, PTD_PROCEDURE_CODE, PTD_SURGICAL_CODE, PTD_REJECT_CODE, PTD_DAW_CODE, LOCATION_OF_SERVICE_CODE, PHYSICIAN_ROLE_CODE, HH_INCOME_CODE, SOURCE_OF_PAY_CODE, PATIENT_SOURCE_OF_ADMISSION, PATIENT_TYPE_OF_ADMISSION, PATIENT_DISCHARGE_STATUS, REVENUE_CODE, PROCEDURE_MODIFIER_CODE |

## Komodo - tables

| Table | Grain | Key columns |
|---|---|---|
| PHARMACY_EVENTS | one Rx transaction | PHARMACY_EVENT_ID, PATIENT_ID, FILL_DATE, NDC11, PRESCRIBER_NPI, DAYS_SUPPLY, TRANSACTION_RESULT |
| MEDICAL_EVENTS | one medical service line | MEDICAL_EVENT_ID, PATIENT_ID, SERVICE_DATE, PROCEDURE_CODE, NDC11, RENDERING_NPI, DIAGNOSIS_CODES |
| PLANS | one plan | KH_PLAN_ID |
| PROVIDERS | one NPI | NPI, HCO_PRIMARY_NPI |
| PATIENT_DEMOGRAPHICS | one patient | PATIENT_ID, PATIENT_YOB |
| PATIENT_GEOGRAPHY | patient × location span | PATIENT_ID, VALID_FROM_DATE, VALID_TO_DATE |
| PATIENT_ENROLLMENT | patient × payer span | PATIENT_ID, START_DATE, END_DATE, MX_CLOSED, RX_CLOSED |

## Points that matter for AML analysis

1. **Birth year (new definition age).**
   - SHA `PATIENT_HIPAA_BIRTH_YEAR` "is adjusted as necessary for patients >=76 only"; pediatric patients show the actual birth year.
   - Komodo `PATIENT_YOB` is a date, `'YYYY-01-01'`.
   - New definition splits at age 65, so the ≥76 adjustment does not change any classification. Do not use the field for ages above 75. The view column `SOURCE_PATIENT_HIPAA_BIRTH_YEAR` is typed as a date or timestamp; take `YEAR()` of it.
2. **Diagnosis position.**
   - SHA `PTD_DIAGNOSIS` has one row per code, with `DIAGNOSIS_TYPE_CODE` giving the position: 0001 principal, 0002-0009 other codes 1-8, 0010 admitting, 0011 external cause.
   - Komodo packs every code into `MEDICAL_EVENTS.DIAGNOSIS_CODES`.
   - The view's `SOURCE_DIAGNOSIS_CODE_1` is the first-position code only, so the AML pool and `FIRST_DX` miss diagnoses held only in a secondary position.
3. **Komodo diagnosis delimiter.** The Komodo dictionary says `DIAGNOSIS_CODES` is "separated by *" but searchable with `LIKE '%|xxx|%'`. The dx view profile splits `custom_field_value_1` on `|`. Check a sample before parsing raw Komodo codes.
4. **Claim status.**
   - SHA Rx claims carry `CLAIM_STATUS_CODE` (0 rejection, 1 approval, 2 reversal) and `PTD_FINAL_CLAIM` (1 final, 0 non-final, NULL direct feed; direct-feed claims are approvals only).
   - Komodo has `TRANSACTION_RESULT` (PAID, REJECTED, REVERSED) and `TRANSACTION_STATUS`.
   - Neither the claims view nor the base-layer notebooks expose or filter a status. The pack assumes the view already holds paid or approved claims only; this is not documented anywhere.
5. **Claim ids.** SHA: "Rx Encrypted Claim ID and Mx or Hx Encrypted Claim IDs CANNOT be linked". Dx and Px rows of one medical claim share a claim id. The base layer uses `claim_id` only as a uniqueness token, which is consistent with this.
6. **Prescriber.**
   - SHA claims carry `PHYSICIAN_KEY` (DS writer id). The NPI sits on `PTD_PHYSICIAN` and is an optional, paid field; one person (`PHYSICIAN_GID`) can have several keys.
   - Komodo carries NPIs directly: `PRESCRIBER_NPI` for pharmacy, and rendering / referring / billing NPI for medical, with `PRESCRIBER_CONFIDENCE` and `BILLING_NPI_CONFIDENCE`.
   - The view's `mdm_npi_number` is MDM-resolved, so NULLs (dropped by the NPS dashboard's HCP attribution) can come from either feed.
7. **Days supply and units.**
   - SHA Rx: `PRODUCT_DAYS_SUPPLY` NUMBER(3) and `PRODUCT_QTY_DISPENSED`.
   - SHA Px: `SERVICE_UNIT_NUMBER` / `CALCULATED_SERVICE_UNIT_NUMBER`, with no days supply.
   - Komodo: `DAYS_SUPPLY`, `QUANTITY`, and `UNITS` / `UNIT_TYPE` on medical events.
   - Medical claims carry no days supply in either feed, which is why the TX table assigns PX DOS by product (`config/tx_table.yaml`).
8. **Patient keys.** SHA `PATIENT_GID` VARCHAR(22) is encrypted. Komodo `PATIENT_ID` is hashed and converted "to kernel patient ID". In the views both are in `patient_sk` with a source suffix (`SHA_PTDONC` for SHA). The two feeds' patients are not linked by these keys.
9. **Coverage.** SHA has panel tables (`PTD_PATIENT_ACTIVITY`, `PTD_PHYSICIAN_PANEL`, `PTD_RX_STORE_PANEL`, `MPD_PATIENT_PANEL_FLAG`) for activity and capture. Komodo has enrollment spans with closed-claims flags (`MX_CLOSED`, `RX_CLOSED`). The base layer uses neither. It uses the Mx/Rx activity tables and the KBT 5 continuity flags instead (no enrollment screen, SME Q-55).
