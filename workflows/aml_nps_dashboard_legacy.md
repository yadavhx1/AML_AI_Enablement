# AML NPS dashboard refresh (legacy IC definition)

**Cadence:** monthly, once the full base-layer refresh (`workflows/aml_base_layer_refresh.md`) has finished,
AML_PATIENT_ELIGIBILITY included.
**Notebook:** `scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb`.
**KBT:** none of its own. Run under KBT 4 (`/kbt-04-patient-intensity-lot`); method, defaults and QC are in
`context/metrics/nps_dashboard_legacy.md`.

## Purpose

Rebuild the AML NPS dashboard on the legacy IC eligible / ineligible definition: the Power BI dataset,
the NPS volume and share by line of therapy and month, the Ipsos index and the account rollup.

## Position in the pipeline

Run it last, after the whole base-layer refresh (`workflows/aml_base_layer_refresh.md`, steps 1-5). The
final step, AML_PATIENT_ELIGIBILITY, must have finished. The notebook reads outputs from two base-layer steps:

| Base-layer step | Table read here | Used in |
|---:|---|---|
| 4 AML_LOT_PATIENT_INTENSITY_LOT | LoT grouping (`MABI_AML_PATS_LOT_GROUPING_TBL_*`), patient cohort (`MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_*`) | cell 26 |
| 5 AML_PATIENT_ELIGIBILITY | final eligibility flags (`MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*`) | cell 68 |

```
1 TX table -> 2 SOB/episode -> 3 regimen -> 4 intensity/LoT -> 5 eligibility  ->  this notebook
```

Do not start it before step 5 has finished. Otherwise the summary joins this refresh's lines to the
previous refresh's flags: patients new this month fall into `Not Available` / -1, and the gated slice
is understated.

## Inputs to confirm before the run

| Input | Where | Note |
|---|---|---|
| LoT grouping table | cell 26 (typed inline) | `MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2_SATEEK`, a personal copy. Point it at the table step 4 wrote (OI-16). |
| Patient cohort (legacy rule; `_NEWDEF` when `intensity_definition: new`) | cell 26 (inline) | `MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL_v2` |
| Eligibility flags | cells 6 and 68 (inline) | un-suffixed Aug'26 build (OI-02) |
| Output table names | cell 6 | `_UPDATED_BUSINESS_RULES_v2[_SATEEK]`; change them so a run does not overwrite someone else's tables |
| Ipsos repository | `MABI_AML_NPS_DASHBOARD_REPOSITORY` | reload with the latest reported NPS before the run |
| Static mappings | `heme_account`, above-brand and GNE `_BKP` segment tables, child account decile | uploaded by CoE; confirm they are current |
| Backbone rank lists | cell 29 | must match `config/nps_dashboard_legacy.yaml` `line_backbone` |
| Summary time basis | cell 77 `SUMMARY_TIME_BASIS` | `END` as shipped; `START` for line-start months (OI-17) |
| Export file names | cells 74, 83, 93, 98 | dated names; change every run |

All values are listed in `config/nps_dashboard_legacy.yaml`. `tools/check_config.py` confirms the YAML still
matches the notebook.

## Run order and outputs

| Step | Cells | Reads | Writes |
|---:|---|---|---|
| 1 | 26-31 | LoT grouping, patient cohort | `LOT_TBL` temp view (line backbone, pandas) |
| 2 | 33-35 | `LOT_TBL`, claims view, CUSTOMER_TBL | `..._REG_NPI_ACI_MAPPING_...` |
| 3 | 39-47 | step 2, affiliations, Reltio, heme_account, decile | `heme_abbott_account` view, `..._ACCT_TYPE_GRP_...` |
| 4 | 49-53 | step 2, segment tables, `heme_abbott_account` | `..._REG_HCP_INFO_MAPPING_...` |
| 5 | 60-67 | step 4 | `dash_tbl` view, `..._1L_IC_INELIG_PBI_DATA_...` (Power BI) |
| 6 | 68-74 | step 5, eligibility flags | `dash_tbl_df` (flags, calendar parts); optional extract |
| 7 | 77-85 | step 6 | `..._LOT_MONTH_NPS_SUMMARY_...`, summary `.xlsx`, QC prints |
| 8 | 91-93 | Ipsos repository, `dash_tbl` | `..._IPSOS_INDEX_REF_...`, `index_map_*.csv` |
| 9 | 96-101 | step 8, `dash_tbl` | `..._FINAL_DATA_MONTH_ROLLUP_...`, `index_map_acct_*.csv` |

**Run-order issue.** Cell 88 calls `spark.stop()` before steps 8 and 9, and cell 87 is an unfinished
`sel` query that errors. In a top-to-bottom run, skip cells 87-88. Otherwise steps 8-9 fail, and the index
and rollup tables keep the previous run's values. Steps 8-9 also need the `dash_tbl` temp view from step 5
in the same session.

Cell 26 pulls the whole grouping table to the driver (`toPandas()`); size the driver for it.

## Execution checks

1. Step 1: patient count of `LOT_TBL` = grouping table; `UNKNOWN` backbones should be zero. The IC_ELIG
   list holds all 28 basket products, and the legacy rule leaves IC_INELIG patients only the 11 products on their
   list. An `UNKNOWN` means a patient has no cohort row (the grouping copy and the cohort table are from
   different builds) or the basket changed.
2. Step 2: cell 35, patients with LOT = 1 and NULL `NPI_REGIMEN`; compare with the previous run.
3. Steps 3-4: account subtype distribution (cell 40, 47); patients with a subtype (cell 52).
4. Step 5: COUNT(DISTINCT PATIENT_GID) equals step 1 (cell 66); PATIENT_GID × LOT is unique.
5. Step 6: rows with no eligibility match (cell 72); they appear as `Not Available` / -1, not blanks.
   A jump against the previous run usually means the flags table is from an older refresh than the lines.
6. Step 7 (cell 85): published-slice months roll up to the published semesters; LOT volume falls steeply
   after 1L; max LOT is plausible.
7. Steps 8-9: reported months from 2019-01 present; rollup totals (cell 99) against the dashboard table.
8. Record the run date, input table names, time basis and data cut in the run header.

## Patient-level output

The notebook prints patient-level frames (cells 27, 29, 31, 70) and can export a patient-level extract.
Clear outputs before sharing the notebook, and keep extracts inside the governed area.
