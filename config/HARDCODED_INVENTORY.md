# Hardcoded values in the AML base-layer notebooks

This inventory covers every hardcoded value in the five notebooks in `scripts/Notebooks/`: run
settings, table names, code lists, business-rule constants and dates. Each value now has a parameter in
`config/`. Values were copied exactly as coded, and the notebooks themselves are unchanged.

| File | Covers |
|---|---|
| `config/common.yaml` | Spark session, pldlib, schemas, source filters, build suffix, every table name, the 37 AML Dx codes, the 13 RR codes, the 28-product basket |
| `config/tx_table.yaml` | patient pool rule, TX column map, DOS and grace per product, NDC lookups |
| `config/sob_episode.yaml` | every `stencil.sob` / `stencil.episode` argument, including `DATA_PERIOD` |
| `config/regimen.yaml` | every `stencil.regimen` argument |
| `config/intensity_lot.yaml` | Legacy rule product list, 90-day gap and the VEN↔HMA exception, both backbone hierarchies, new definition lists and age threshold |
| `config/eligibility.yaml` | data-cut rule, activity sources, lookback windows, Dx-to-Tx window, SCT codes, arsenic default |
| `config/nps_dashboard_legacy.yaml` | AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated: input and output table names, line-backbone rank lists, HCP attribution, account hierarchy, backbone groups, summary slice and time basis, export names |
| `config/load_config.py` | loader (`load_config`) and SQL helpers (`sql_list`, `case_map`, `backbone_case`) |

Use the YAML values as the pack's parameters for these notebooks when you explain or reproduce a step.
A different value is a rule change (see `context/domain/rule_change_history.md`).

## Hardcoded values found

Cell numbers are the cell indices in each notebook.

### Repeated in every notebook (now in `common.yaml`)

| What | Where | Parameter |
|---|---|---|
| Spark executors/memory/cores, app name, master | all five notebooks cell 2 (AML_PATIENT_ELIGIBILITY uses 15 / 12g) | `spark.*`; override in `eligibility.yaml` |
| `pldlib.egg` path | all five notebooks cell 3 | `pldlib.egg_path` |
| Schema `Z_ABV_CWS_MABI_ONC_ANALYTICS` | the four AML_LOT notebooks cell 5, AML_PATIENT_ELIGIBILITY cell 11; also typed out literally in AML_PATIENT_ELIGIBILITY cells 13–16, 28, 44, 72, 114, 140, 156 | `schemas.cws` |
| 26 table names with the `_BUSINESS_RULE_CHANGE_VAL_v2` suffix | the four AML_LOT notebooks cell 5 | `tables.*` + `run.build_suffix` |
| The same names **without** `_v2` | AML_PATIENT_ELIGIBILITY cell 11 | `eligibility.yaml` `run.build_suffix` |
| `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT` (`_v2` in the four AML_LOT notebooks, no suffix in AML_PATIENT_ELIGIBILITY) | the four AML_LOT notebooks cell 5, AML_PATIENT_ELIGIBILITY cell 156 | `tables.patient_intensity_based_on_age_n_product`; `final_flags.rule_b_table` |
| Source views (claims, dx, px, sx, dim_product) | AML_LOT_TX_TABLE cells 5, 8, 13; AML_LOT_PATIENT_INTENSITY_LOT cells 33, 42, 44; AML_PATIENT_ELIGIBILITY cells 5–6, 13–14, 19, 93, 100, 156 | `schemas.*` |
| `source_flag='SHA_PTD'`, `source_market='ONC'`, `market_code='VENC_AML'` | throughout | `source_filters.*` |
| 37 AML Dx codes, inline | AML_LOT_TX_TABLE cell 8, AML_LOT_PATIENT_INTENSITY_LOT cells 33 and 42, AML_PATIENT_ELIGIBILITY cell 19 | `codes.aml_dx_full` |
| 13 RR Dx codes (`aml_dx`) | the four AML_LOT notebooks cell 5, AML_PATIENT_ELIGIBILITY cell 11 | `codes.aml_dx_rr` |
| 28-product basket | AML_LOT_TX_TABLE cell 13 | `products.basket` |
| `FILGRASTIM` exclusion, `VENCLEXTA`, `ARSENIC_TRIOXIDE` literals | AML_LOT_TX_TABLE cell 18; AML_PATIENT_ELIGIBILITY cells 19, 156 | `products.*` |

### Notebook-specific

| What | Notebook / cell | Parameter |
|---|---|---|
| Pool = more than one distinct `mx_claim_id` | AML_LOT_TX_TABLE cell 8; AML_LOT_PATIENT_INTENSITY_LOT cell 33 | `patient_pool.min_claims_exclusive` |
| `market_code` filter commented out on the TX table | AML_LOT_TX_TABLE cell 13 | `tx_table.apply_market_code_filter` |
| Rx DOS fallback 28; PX DOS per product (1 / 28) | AML_LOT_TX_TABLE cell 18 | `dos.*` |
| Grace per product (3–60 days) | AML_LOT_TX_TABLE cell 18 | `grace_days.*` |
| NDC/procedure lookups for Onureg, Inqovi, Rezlidhia, Vanflyta (run, never used) | AML_LOT_TX_TABLE cell 5 | `product_code_lookups.*` (disabled) |
| `DATA_PERIOD = "202210"` literal | AML_LOT_SOB_EPISODE cell 9 | `sob.data_period` |
| `lookback='360'`, dedup ranking, `required_grace='0'` | AML_LOT_SOB_EPISODE cell 9 | `sob.*` |
| `regimen_threshold_vl='5000'`, `regimen_removal_vl='0,1'`, `data_end_dt_vl='2400-01-01'`, `"TEST"` placeholders | AML_LOT_REGIMEN cell 8 | `regimen.*` |
| IC Eligible / Ineligible definition used by the LoT build (legacy rule or new definition) | new setting; read by AML_LOT_PATIENT_INTENSITY_LOT, AML_PATIENT_ELIGIBILITY and the NPS dashboard | `run.intensity_definition` (common.yaml, default `legacy`), `run.new_definition_tag` |
| Legacy rule: IC-Eligible-only product list | AML_LOT_PATIENT_INTENSITY_LOT cell 12 | `intensity_rule_a.ic_elig_only_products` |
| 90-day gap, VEN↔HMA exception | AML_LOT_PATIENT_INTENSITY_LOT cells 21 and 27 | `lot.*` |
| IC_INELIG / IC_ELIG backbone CASE order | AML_LOT_PATIENT_INTENSITY_LOT cells 21 and 27 | `ic_inelig.backbone_hierarchy`, `ic_elig.backbone_hierarchy` |
| Commented-out 28 / 14-day minimum regimen length | AML_LOT_PATIENT_INTENSITY_LOT cell 16 | `ic_inelig.cons_filter` |
| New definition: `LOT = 1`, age ≤ 65, product sets, rank lists, `UNKNOWN` | AML_LOT_PATIENT_INTENSITY_LOT cells 46–49 | `intensity_rule_b.*` |
| Data cut: max VENC_AML `RX FACT` date; −6 months +1 day → `exc_dt` | AML_PATIENT_ELIGIBILITY cells 5–7 | `data_cut.*` |
| Semester split at month 6 (`-01-01` / `-07-01`); semester methodology per flag | AML_PATIENT_ELIGIBILITY semester setup cell (now read from config) | `semester.split_month`, `semester.semester_type` |
| Exact-date activity tables (`..._KA_v2`, `..._KA`) and source-type patterns | AML_PATIENT_ELIGIBILITY cells 13–14 | `activity_tables.*` |
| Frequency tables in `abv_val_ptd_synd_work`, `SEMESTERLY`, `OFFSET='0'` | AML_PATIENT_ELIGIBILITY cells 26, 91, 98, 105 | `activity_tables.freq_*` |
| Legacy `SHA_PTD_MABI_ONC_SYND.MABI_*_ACT_TBL` (strings built, unused) | AML_PATIENT_ELIGIBILITY cells 35, 63, 131 | `activity_tables.legacy_*` |
| Commented Dx window `2019-12-01` – `2026-03-06` | AML_PATIENT_ELIGIBILITY cell 19 | `first_dx_tx.dx_date_window` |
| Lookback windows 6 / 12 months; unused −18/−24/−36/+6/+12/+3 offsets | AML_PATIENT_ELIGIBILITY cells 27–28 (repeated in 36, 64, 92, 99, 106, 132) | `dx_lookback.*` |
| 6-month continuity interval; under 6 months passes | AML_PATIENT_ELIGIBILITY cells 38–55, 66–83, 108–125, 134–151 | `txl_continuity.*` |
| Dx-to-Tx 0–60 days; `COALESCE(ARSENIC_FLG, 1)` | AML_PATIENT_ELIGIBILITY cell 156 | `final_flags.*` |
| SCT codes (2 Dx, 51 Px) | AML_PATIENT_ELIGIBILITY cell 156 | `final_flags.sct.*` |

### AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated (now in `nps_dashboard_legacy.yaml`)

| What | Cell | Parameter |
|---|---|---|
| Spark 15 executors / 12g / 4g driver / 2g overhead, app name `AML` | 2 | `spark.*` |
| Table names with `_SATEEK` / `_UPDATED_BUSINESS_RULES_v2` suffixes | 6 | `tables.*` |
| Grouping and cohort tables typed inline; flags table typed inline again | 26, 68 | `tables.lot_regimen_group`, `patient_group`, `elig_flags_final` |
| IC_ELIG (28) / IC_INELIG (11) rank lists, `UNKNOWN` | 29 | `line_backbone.*` |
| Claims filter ONC / SHA_PTD / VENC_AML, no FILGRASTIM, HMA products, claim order | 34 | `hcp_attribution.*` |
| CUSTOMER_TBL, affiliations, Reltio, child decile tables inline | 34, 39, 42, 45 | `schemas.*` |
| ONH2 affiliation filter, Reltio flags, subtype hierarchy 1-9, group map, decile >= 8 | 39, 42, 45, 65, 97 | `account_type.*` |
| Backbone groups, `Not Available` labels | 60 | `backbone_group.*` |
| `SUMMARY_START_YEAR = 2019`, `SUMMARY_TIME_BASIS = 'END'`, dims, published slice | 77, 85 | `summary.*` |
| Reporting floor `2019-01-01`, `MM/dd/yyyy` month keys | 92, 97 | `indexing.*` |
| Dated export names | 74, 83, 93, 98 | `exports.*` |

## Inconsistencies the YAML makes visible

1. **Build suffix mismatch.** The four AML_LOT notebooks write `_BUSINESS_RULE_CHANGE_VAL_v2`, but
   AML_PATIENT_ELIGIBILITY reads the same tables with no `_v2` (OI-02). Setting `eligibility.yaml`
   `run.build_suffix` to the common value aligns them.
2. **new-definition table.** AML_LOT_PATIENT_INTENSITY_LOT writes `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_v2`;
   AML_PATIENT_ELIGIBILITY reads `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT`.
3. **Activity tables.** The Mx exact-date table is always `_v2` and the Rx one never is, whatever the
   build.
4. **`DATA_PERIOD = "202210"`** is a stale literal; it has no effect while `data_end_required='no'`.
5. **Dead code that still runs:**
   - the four product-code lookups in AML_LOT_TX_TABLE (each calls `toPandas()`);
   - `backup_dt` and `new_data_date` in AML_PATIENT_ELIGIBILITY run the identical query;
   - the legacy activity strings in AML_PATIENT_ELIGIBILITY are built but never used.
6. **Schema mix.** AML_PATIENT_ELIGIBILITY reads `abv_val_ptd_synd_work` frequency tables without
   `market_code='ONC'`; the pack default (SME Q-08/Q-10) is `abv_val_ptd_synd` with that filter.
7. **Dx codes vs the business-rules page.** The page (2026-10-07 revision) lists ICD-9 206.00/206.01/
   207.00/207.20/207.21, which `codes.aml_dx_full` does not contain. They are recorded as
   `codes.aml_dx_icd9_page` for a sensitivity run only (OI-14).
8. **NPS dashboard notebook.** Its tables carry personal suffixes (OI-16); it declares `updated_tx_tbl` and
   `ic_inelig_final` but never reads them; its `reltio_tbl` (`ABV_MA360_MHCDM`) differs from the unused one in
   `common.yaml`; the summary uses the line END month (OI-17); and cell 88 `spark.stop()` comes before the
   index and rollup cells.

## Using the config in a notebook

```python
import sys; sys.path.append("../../config")        # path from scripts/Notebooks/
from load_config import load_config, sql_list, case_map, backbone_case

cfg = load_config("tx_table.yaml")
t = cfg["tables"]
spark.sql(f"""
SELECT DISTINCT PATIENT_SK FROM (
  SELECT patient_sk, COUNT(DISTINCT {cfg['patient_pool']['count_column']}) AS n
  FROM {cfg['schemas']['dx_view']}
  WHERE {cfg['patient_pool']['dx_code_column']} IN ({sql_list(cfg['codes']['aml_dx_full'])})
    AND source_flag = '{cfg['source_filters']['source_flag']}'
  GROUP BY 1) WHERE n > {cfg['patient_pool']['min_claims_exclusive']}
""")
grace_sql = case_map("FINAL_PRODUCT_NAME", cfg["grace_days"])          # GRACE_VALUE CASE
bb_sql = backbone_case(load_config("intensity_lot.yaml")["ic_elig"]["backbone_hierarchy"])
```
