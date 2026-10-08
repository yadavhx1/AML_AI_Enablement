# AML base-layer refresh

**Cadence:** monthly, after the SHA refresh (2-month lag).
**Notebooks:** `scripts/Notebooks/` all five notebooks, in order.

## Purpose

Rebuild the AML episode, regimen, intensity, line-of-therapy and eligibility tables that AML KPIs
(NPS share, SCT, BMB, LoT mix) are filtered from.

## Run order and outputs

| Step | Notebook | Reads | Writes |
|---:|---|---|---|
| 1 | AML_LOT_TX_TABLE | all_claims_combined_fact_vw, dx_fact_curated_vw | TX table, TX final table (`_v2`) |
| 2 | AML_LOT_SOB_EPISODE | TX final | SOB, episode (`_v2`) |
| 3 | AML_LOT_REGIMEN | episode | regimen (`_v2`) |
| 4 | AML_LOT_PATIENT_INTENSITY_LOT | regimen, TX final, claims view, dx view | patient cohort, IC LoT x2, combined LoT, LoT grouping, new-definition classes (`_v2`; `_NEWDEF` when `intensity_definition: new`) |
| 5 | AML_PATIENT_ELIGIBILITY | combined LoT, episode, new-definition classes, activity sources | activity tables, first Dx/Tx, flag tables, final flags (un-suffixed) |

## Prerequisite

Every notebook runs `spark.sparkContext.addPyFile("pldlib.egg")`. Copy `scripts/pldlib/pldlib.egg`
into the notebook's working directory (or change the path in that cell) before running.

## Parameters

Every hardcoded value in the five notebooks is parameterized in `config/`: `common.yaml` plus
`tx_table.yaml` … `eligibility.yaml`. Load them with `config/load_config.py`
(`load_config("<notebook>.yaml")`). Change a run's build suffix, data cut (`data_cut.override_max_date`) or
Spark size there, not in the notebook. `tools/check_config.py` confirms the YAML still matches the
notebook code. `config/HARDCODED_INVENTORY.md` lists each value, its cell and the inconsistencies found.

## Semester methodology

`AML_PATIENT_ELIGIBILITY` reads `semester.semester_type` from `config/eligibility.yaml`:

```yaml
semester:
  semester_type: calendar        # every flag on calendar halves (Jan-Jun / Jul-Dec)
# or
  semester_type: actual          # every flag on rolling 6-month windows from the patient's anchor
# or, per flag group (the shipped default, which reproduces the original build):
  semester_type:
    dx_lookback: actual
    journey_continuity: actual
    ven_lookback: calendar
```

Change the value and re-run `AML_PATIENT_ELIGIBILITY`; the notebook is the same in both modes. The output
tables and their schema do not change. Record the setting in the run header.
`python tools/test_semester.py` checks the boundary rules and the generated SQL without Spark.

## IC Eligible / Ineligible definition

`run.intensity_definition` in `config/common.yaml` chooses the definition for the LoT build and
everything after it:

```yaml
run:
  intensity_definition: legacy   # default: product-only legacy rule (production)
# or
  intensity_definition: new      # age + product new definition
```

- **legacy**: the notebooks run and write exactly as before.
- **new**: run steps 4 and 5 (and the NPS dashboard) again with the setting changed.
  - `AML_LOT_PATIENT_INTENSITY_LOT` builds legacy lines into `_P1LEGACY` scratch tables, classifies
    patients with the new definition from that line 1, then rebuilds the lines.
  - Every definition-dependent table is written with `_NEWDEF`. Eligibility and the dashboard read
    and write `_NEWDEF` tables too, so legacy tables and published figures are never overwritten.
  - Steps 1-3 (TX, SOB/episode, regimen) do not depend on the definition and are not re-run.
- Use the new definition only when it is explicitly requested, and record the setting in the run header.
- `python tools/test_intensity_definition.py` checks both settings without Spark.

## Execution checks

1. Confirm the SHA refresh: MAX(claim_date) of VENC_AML 'RX FACT' claims (AML_PATIENT_ELIGIBILITY MAX MONTH cell).
2. Before step 5, set AML_PATIENT_ELIGIBILITY's table-name globals to the build you are refreshing (OI-02);
   otherwise it reads the un-suffixed Aug'26 tables.
3. After each step, compare COUNT(DISTINCT PATIENT_GID) with the previous step (TX final = SOB =
   episode = regimen = combined LoT).
4. After step 1: zero NULL DOS / grace rows; 28 distinct products.
5. After step 4: IC_ELIG + IC_INELIG = total; zero NULL backbones.
6. After step 5: zero NULL FIRST_DX / LAST_TX; flag pass counts in line with the previous run.
7. Record the run date, data cut, `exc_dt` and suffix in the run header.

The NPS dashboard notebook runs after this workflow, once step 5 has finished; see
`workflows/aml_nps_dashboard_legacy.md`.

AML_LOT_SOB_EPISODE and AML_LOT_PATIENT_INTENSITY_LOT rely on temp views created in the same notebook (`sob_df`, `ic_inelig_cons_final`,
`patient_pool`, `fst_dx_tx_tbl`, `spark_df_LOT_REGIMEN_GROUP`); run each notebook top to bottom in one
session.
