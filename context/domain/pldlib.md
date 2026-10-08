# pldlib (stencil) - the team's PLD library

The base-layer notebooks load the library with `spark.sparkContext.addPyFile("pldlib.egg")` and
`from pldlib import stencil`, and call `stencil.init(spark).<function>(**params)`.

- Package: `scripts/pldlib/pldlib.egg` (the file the notebooks load; put it in the notebook's
  working directory).
- Readable source: `scripts/pldlib/source/` (the `.py` files extracted from the egg; the `.pyc`
  copies are left inside the egg).
- `pldlib` 0.0.1, "Patient level data analysis pyspark library", created by ZS Associates for the "MABI
  DL TRANSITION Project". The SQL modules are headed "Created by :- ABHISAX", 15 Nov 2018 (SOB),
  30 Nov 2018 (episode), 15 Dec 2018 (regimen).

## How a call works

1. `stencil.init(spark).<fn>(**kwargs)` calls `common_utilities.df_generator_utility.df_generator`.
2. Arguments not listed for that function in `common_utilities/ruleEngine.py` are silently dropped.
   Any listed argument that is missing raises "additional keys were expected". Values are checked
   (`nullable`, `string_flag`, `integer_flag`, `specific_value`).
3. `businessLogic/businessLogic_<fn>.py` fills the arguments into one SQL template with
   `str.format(**kwargs)` and returns `spark.sql(...)` as a DataFrame. The arguments are pasted
   straight into the SQL, so a column name, table name or a bracketed `(SELECT ...)` all work as
   `src_input_tbl`.

The SQL each AML call generates is rendered in full in `verified_queries/kbt-02/aml_sob.sql`,
`kbt-02/aml_episode.sql` and `kbt-03/aml_regimen.sql`.

## Functions

| Function | Used by the AML base layer | Purpose |
|---|---|---|
| `sob` | AML_LOT_SOB_EPISODE | Claim-level source of business, episode numbering and episode dates |
| `episode` | AML_LOT_SOB_EPISODE | One row per patient x product x episode from the `sob` output |
| `regimen` | AML_LOT_REGIMEN | Regimens from overlapping episodes |
| `eligibility` | no | Lookback / look-forward activity eligibility flags |
| `patientSelection` | no | Criteria-based patient selection |
| `episodePersistency`, `patientPersistency` | no | Persistency curves |
| `oneNdone` | no | One-and-done patients |
| `compliance` | no | Compliance / MPR |

## sob - what it computes (AML parameters)

Input `src_input_tbl` = TX final table plus `DATA_PERIOD = '202210'`; `grace = GRACE_VALUE` (per
product), `lookback = 360`, `dos_clmn = DOS_FINAL`, `dedup_type_vl = 'yesremove'`,
`data_end_required = 'no'`, `required_grace = '0'`.

1. **De-duplication.** `row_number()` over patient x product x claim date, ordered `DOS_FINAL DESC,
   CLAIM_ID`; only rank 1 is kept (`yesremove`). `yesadd` would sum DOS instead.
2. **Claim metrics.** These cover claim end (date + DOS), previous/next claim of the same product,
   previous/next claim of any product, and their DOS.
3. **Episode break.** `is_episode_start = 1` when there is no previous same-product claim, or when
   `gap_from_prev_claim_drvd` = claim date − (previous claim date + previous DOS) is greater than the
   **previous** claim's grace. `episode_num_drvd` = running sum of episode starts per patient x product.
4. **Episode dates.**
   - `episode_start_date_drvd` = first claim date.
   - `episode_end_date1_drvd` = last claim date + last claim DOS.
   - `episode_end_date2_drvd` = end1 + last claim grace.
   - `episode_end_date3_drvd` = last claim date (NULL for a single-claim episode).
   - `episode_end_date4_drvd` = first claim date + episode length.
5. **Episode length.** `episode_days` per claim = days to the next claim when that claim falls within
   DOS + grace; otherwise DOS + `required_grace` (0 here). `episode_length` = their sum. The
   `data_end_required` branch, which caps the last claim at the data end, is off.
6. **Source of business (`sob_lvl7`).** It is assigned at each episode start, using `lookback = 360`
   days:
   - `NTB NAIVE`: no earlier claim of any product, or a gap of more than 360 days since the previous
     claim of any product.
   - `RS SAME`: the previous claim was the same product.
   - `NTB SWITCH` / `RS SWITCH`: the previous product's episode ended before this claim.
   - `NTB ADDON` / `RS ADDON`: it had not ended.
   - NTB vs RS: whether this product was seen in the previous 360 days.
   - `C`: continuing claims, not an episode start.

   Rollups: `sob_lvl4` (NTB / SWITCH / REINITIATING / C), `sob_lvl2_1` (INFLOW / NON INFLOW),
   `sob_lvl2_2` (NEW / C/REINITIATING), and `NTB_FLAG`.
7. **Flags.** `dos_null_flag`, `dos_pat_prd_null_flag` and `dos_pat_prd_epsd_null_flag` are 1 when DOS is NULL at
   claim / patient-product / episode level.

So in the AML base layer the 360-day lookback affects only the SOB labels. Episodes break on grace
alone. The labels are computed but not used by the line-of-therapy logic (which uses backbone and the
90-day regimen gap). They are available for source-of-business questions (SME Q-65).

## episode - what it computes

The input is the `sob` output (the `sob_df` temp view in AML_LOT_SOB_EPISODE). It groups to **one row per patient
x product x episode** with these columns:

- `PATIENT_GID`, `FINAL_PRODUCT_NAME`, `drug_class_epsd` ('NA'), `ntb_rnk`, `ntb_flag`, `episode_num_drvd`
- `episode_start_date_drvd`, `EPISODE_END_DATE1/2/3_DRVD`, `episode_length`, `episode_length_overlap`
- `episode_first_sob` (the `sob_lvl7` of the first claim)
- `dos_wo_last_claim`, `dos_wo_last_claim_no_overlap`, `dos_last_claim`, the three DOS-null flags
- `first_claim_id_drvd`, `last_claims_grace_drvd`, `last_claims_lookback_drvd`

The notebook also passes `metric_ordering_by_clmns`; the rule engine drops it.

## regimen - what it computes (AML parameters)

Input = the episode table; `episode_start_dt_clmn = EPISODE_START_DATE_DRVD`,
`episode_end_dt_clmn = EPISODE_END_DATE1_DRVD`, `COLLECT_SET`, `clean_up_type_vl = 'no'`,
`regimen_threshold_vl = '5000'`, `regimen_removal_vl = '0,1'`, `data_end_dt_vl = '2400-01-01'`.

1. **Cut points.** Every episode start date and every end1 date becomes a cut point per patient.
   Episodes whose start date equals their end1 date (to_date) are skipped entirely.
2. **Intervals.** Consecutive cut points form intervals [cut point, next cut point). The interval after
   the last cut point ends at 2400-01-01.
3. **Products.** Each interval takes every product whose episode covers the interval's midpoint
   (start ≤ midpoint < end1). Intervals no episode covers drop out, so a treatment gap ends a regimen
   rather than creating an empty one.
4. **Regimen label.** `REGIMEN = concat_ws(', ', sort_array(collect_set(product)))`, so products appear
   **alphabetically**, e.g. `AZACITIDINE, VENCLEXTA`. That means an exact match is possible, although LIKE
   is safer.
5. **Threshold flags.** `regimen_threshold_flag = 1` when the length is under the threshold (5000 days,
   so almost always). Effects:
   - `regimen_valid_flag = 'Invalid'` when a neighbour is also flagged.
   - `UPDATED_REGIMEN` takes the next regimen for flagged, gap-free, non-last regimens.
   - With clean-up off and removal `0,1`, nothing is removed.
   - The AML base layer reads `REGIMEN`, not `UPDATED_REGIMEN`, so these flags have no effect
     downstream.
6. **Output columns.** `patient_gid_rgmn`, `final_indication_drvd` ('TEST'), `regimen_start_date`,
   `regimen_end_date`, `regimen_threshold`, `regimen_length`, `regimen_threshold_flag`,
   `regimen_remove_flag`, `regimen_valid_flag`, `clean_up_type`, `gap_to_next_regimen`, `regimen`,
   `drug_regimen`, `drug_regimen_2`, `updated_regimen`, `updated_drug_regimen`,
   `updated_drug_regimen_2`.

## Known library quirks

- `common_utilities/dataChecks.py` uses `value is 'None'`, which raises a SyntaxWarning on load (seen in
  the notebooks) and never matches. The `nullable` check therefore never fails.
- `parameterValidator/` is an older copy of `common_utilities/` validation code. It is not imported.
- The egg also contains compiled `.pyc` files; the Spark driver uses those when the Python version
  matches.
