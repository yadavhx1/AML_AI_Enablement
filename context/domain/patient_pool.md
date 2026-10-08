# AML patient pool

**Definition id:** `patient_pool`
**Aliases:** patient pool, AML 2+, 2+ Dx, AML population, cohort
**Working behavior:** Use the documented definition and name the build.

## Definition
Patients with two or more AML-coded diagnosis claims, ever. This is the entire population gate: there
is no recency window, no competing-diagnosis check and no treatment requirement.

## Calculation
```text
COUNT(DISTINCT mx_claim_id) > 1 per patient_sk
  on SOURCE_DIAGNOSIS_CODE_1 IN (37 AML codes), source_flag = 'SHA_PTD'
  from abv_val_ptd_onc_synd.dx_fact_curated_vw
```

## Grain and dimensions
One row per patient

## Source tables
abv_val_ptd_onc_synd.dx_fact_curated_vw

## Caveats
May'26 build: 57,697 patients in the TX final table. The Aug'26 eligibility build used
market_code = 'VENC_AML' instead (84,199 patients) (OI-01). Name the build. A single AML claim is
excluded as too thin.

The business-rules page shows 13 ICD-10 codes plus 7 legacy ICD-9 codes (205.00/.01, 206.00/.01,
207.00/.20/.21) as the AML codes. The code uses the 37-code set instead, which has no 206.x or 207.x, so
pre-2015 patients coded only that way are not in the pool (OI-14). The full list and crosswalk are in
`context/domain/reference_codes_and_mappings.md`.

## Source lineage
- scripts/Notebooks/AML_LOT_TX_TABLE.ipynb
- AML_Base_Business_Rule.html · Section 03
