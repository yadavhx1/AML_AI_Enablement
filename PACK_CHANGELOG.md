# Pack changelog

## Sources of the pack content

- **KBTs 1-5, verified queries:** the five notebooks in `scripts/Notebooks/`. They were split from
  the team's `AML_LOT_VAL.ipynb` and `Patient Eligibility.ipynb`, which stay in `base_layer/` outside the
  pack. SQL equivalents were written for the pandas steps.
- **Business rules:** `Business_Rules/index.html`. Where it disagrees with the
  notebooks, the code wins.
- **Code sets, hierarchies, DOS/grace, metrics, profiles, taxonomy, defaults:** the AML sections of the
  Venclexta KBT-first pack (updated 2026-10-01), which cite the AML SHA Business Rules Guide V5.
- **Source-view profiles:** the Venclexta pack's table profiles and data dictionaries, carried as
  `context/data/tables/<table>/` (profile, analysis and full column files). The raw `.xlsx`
  dictionaries were removed on 2026-10-07 as duplicates; the originals stay in the Venclexta pack.
- **pldlib and the SOB/episode/regimen SQL:** `scripts/pldlib/`.
- **SME answers:** `context/assumptions/sme_answers_reused.md`.

## Answer-only responses (2026-10-07)

- `CLAUDE.md` "Final response format" forbids narrating the working process (preambles, interim
  commentary, file reads, retries). Only the final answer is returned; SQL and method steps appear
  only on request.
- New `.claude/settings.json` turns off extended thinking (`alwaysThinkingEnabled: false`) and
  thinking summaries (`showThinkingSummaries: false`) for this project only.

## IC Eligible / Ineligible: legacy rule vs new definition (2026-10-07)

- **Naming.** "Rule A" / "Rule B" are now the **legacy rule** (product-only, production) and the
  **new definition** (age + product) in every KBT, metric, default, profile, workflow and
  verified-query note. Query names (`AML_PATIENT_INTENSITY_RULE_A`, `AML_RULE_B_INPUTS`), file names and
  SQL columns are unchanged, so references still resolve.
- **Default.** The legacy rule applies everywhere unless the user explicitly asks for the new
  definition (`CLAUDE.md`, KBT 4/5/6, `AML_INTENSITY_RULE`).
- **Run option.** New setting `run.intensity_definition` in `config/common.yaml`: `legacy` (default) or
  `new`. It is resolved by the new `config/intensity_definition.py`.
  - `AML_LOT_PATIENT_INTENSITY_LOT` (`legacy`): runs exactly as before.
  - `AML_LOT_PATIENT_INTENSITY_LOT` (`new`):
    1. Pass 1 builds legacy lines into `_P1LEGACY` scratch tables.
    2. The new definition classifies each patient from that legacy line 1.
    3. Pass 2 rebuilds the IC_ELIG / IC_INELIG lines, the combined LoT and the grouping with the new
       classes. It uses the legacy line SQL, and the grouping step moves from pandas to Spark SQL.
    4. Outputs carry `_NEWDEF`. The cohort table keeps the legacy class in
       `PATIENT_INTENSITY_GROUP_LEGACY`.
  - `AML_PATIENT_ELIGIBILITY` and the NPS dashboard follow the same setting. In a new run they read
    and write `_NEWDEF` tables, so `PATIENT_COHORT` and the dashboard slices use the new definition.
    Legacy tables and published figures are never overwritten.
- **Tests.** New `tools/test_intensity_definition.py` (no Spark) executes the three notebooks against a
  recording Spark stub. It checks that:
  - legacy SQL is identical to the pre-change notebooks;
  - a new run never writes a legacy table, and downstream reads only `_NEWDEF` inputs;
  - the new cohort takes the new class.
  - Deliberately broken versions of each were all caught.
- `tools/check_config.py` now finds LoT and dashboard cells by content and checks the switch.
- Pre-change files are in `../backup_pre_intensity_definition/`.

## Outputs folder added (2026-10-08)

- New `outputs/` (with `README.md` and `_scratch/`) for files generated during analyses: one dated
  folder per analysis, aggregates only. `CLAUDE.md` has a new "Generated files" section;
  `tools/validate_pack.py` skips `outputs/`.
- `CLAUDE.md` was emptied by a failed write when the disk filled up; it was restored from
  `aml_context_pack_kbt.zip` plus the closing "Do not narrate" paragraph, then this section was added.

## DOS/grace update skill removed (2026-10-08)

- Deleted the `update-dos-grace` skill (`.claude/skills/update-dos-grace/`) and its helper script (tools/update_dos_grace.py); the README entry
  was removed. DOS and grace values are unchanged in `config/tx_table.yaml`, the `AML_LOT_TX_TABLE`
  notebook and `reference_codes_and_mappings.md`. Change them by hand in all three, then run
  `tools/check_config.py`.

## Business-rules page moved to the pack root (2026-10-08)

- `Business_Rules/index.html` is now `AML_Base_Business_Rule.html` at the pack root (content unchanged).
- The `Business_Rules/` folder was deleted, including the archived 2026-10-01 revision
  (`archive/AML_Base_Layer_Business_Rules_v1_2026-10-01.html`); a copy is in `aml_context_pack_kbt.zip`.
- Every reference was repointed; `tools/validate_pack.py` checks the page exists.
- Entries below still describe the folder as it was when they were written.

## Metrics folder limited to reported KPIs (2026-10-08)

- `context/metrics/` now holds only `nps_count`, `nps_dashboard_legacy`, `sct_rate` and `bmb_rate`.
- `aml_eligibility_flags`, `days_on_therapy`, `line_of_therapy`, `patient_intensity`, `patient_pool` and
  `time_to_treatment` moved, unchanged apart from the id label, to `context/domain/`. They are the
  definitions the KPIs build on. Their rows were removed from `context/metrics/index.tsv`.
- Every path reference was repointed (KBT 2, 4, 5 and 6 skills, table profiles, key concepts, verified
  query 25). Verified-query `METRICS` tags now list only the four KPIs; queries tagged with a moved
  definition show `none`.

## SHA and Komodo data dictionaries added (2026-10-07)

- New `context/data/source_dictionaries/` from `SHA_Data_Dictionary.xlsx` (30 tables, 277 columns) and
  `Komodo_Data_Dictionary.xlsx` (7 tables, 90 columns), as `columns.tsv` per feed, plus a README and
  `view_column_lineage.tsv` (view column -> raw SHA / Komodo field; mostly inferred by name). No similar
  files existed: the table profiles cover the processed views, not the raw feeds.
- Linked from `context/data/README.md`, the claims and dx view profiles, `data_landscape.md` and
  `README.md`. New open item OI-18 (claim status filtering).
- KBT 1, 5 and 6 list the dictionaries under "Context to read", for questions that go below the view
  (source fields, missing NPI or days supply, diagnosis position, birth year, claim status, feed choice).

## NPS dashboard run order corrected (2026-10-07)

- The NPS dashboard notebook runs after the full base layer, once AML_PATIENT_ELIGIBILITY has finished.
  Earlier text said "after AML_LOT_PATIENT_INTENSITY_LOT". The workflow, KBT 6, config, profiles, README,
  CLAUDE.md and key concepts were updated.

## NPS dashboard notebook and KBT 6 added (2026-10-07)

- Added `scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb` from the team, code unchanged. Saved
  outputs were cleared because four cells printed patient identifiers. It runs after
  AML_LOT_PATIENT_INTENSITY_LOT and reads the final eligibility flags.
- New KBT 6 `kbt-06-nps-dashboard-legacy`, with 8 verified queries in `verified_queries/kbt-06/`. Two are
  SQL equivalents: the line backbone (a pandas step) and the flag join (a PySpark step).
- Separate workflow `workflows/aml_nps_dashboard_legacy.md`. The base-layer refresh points to it.
- New config `config/nps_dashboard_legacy.yaml` (checked by `tools/check_config.py`), metric
  `nps_dashboard_legacy`, seven table profiles (`family = aml_nps_dashboard`), default
  `AML_NPS_DASHBOARD_SLICE`, open items OI-16 and OI-17, taxonomy terms and four eval prompts.
- `tools/validate_pack.py` now expects six KBTs.

## Data_Sources renamed to scripts (2026-10-07)

- The `Data_Sources/` folder is now `scripts/` (notebooks and pldlib, unchanged). Every reference in
  the pack was repointed to `scripts/...`.

## Business-rules page renamed (2026-10-07)

- The current page is now `Business_Rules/index.html` (same content as before). All references were
  repointed. The archived revision is unchanged in `Business_Rules/archive/`.

## Configurable semester methodology for patient eligibility (2026-10-07)

- `AML_PATIENT_ELIGIBILITY` now builds every activity flag's 6-month periods from
  `semester.semester_type` in `config/eligibility.yaml`. The value is `calendar` (Jan–Jun / Jul–Dec
  halves from the claim date) or `actual` (rolling 6-month windows from each patient's anchor). It can
  be set once or per flag group: `dx_lookback`, `journey_continuity`, `ven_lookback`.
- The default reproduces the original build exactly (actual / actual / calendar). The original
  notebook mixed both methods; boundaries and the `exc_dt` cutoff keep their original rules.
- The logic lives in the new `config/semester.py`.
  - In the notebook, the 7 flag sections' period-building cells (161 → 71 cells) are replaced by one
    `build_flag(...)` call each.
  - The DROP/CREATE/COUNT cells, the first Dx/Tx step and the final flags step are unchanged, and so
    are the output schemas.
  - The four continuity flags now run in Spark SQL instead of `toPandas()` + a pandas merge, with the
    same rules.
- Added `tools/test_semester.py` (no Spark needed). It checks:
  - calendar boundaries (01-01, 06-30, 07-01, 12-31), NULL dates, year ends and leap days;
  - actual window start/end and day-before/after, consecutive windows and year-crossing windows;
  - the generated SQL, executed in SQLite, against the reference rules for both modes;
  - that the default rules equal the original notebook's.
  - Deliberately broken boundary, single-period and cutoff rules are all caught.
- `tools/check_config.py` now finds eligibility cells by content and confirms all 7 flags are routed
  through `semester_type`.
- The original notebook, config and check script are kept in `../backup_pre_semester_type/`.

## DOS/grace update skill added (2026-10-07)

- New skill `update-dos-grace` (removed 2026-10-08) and helper `update_dos_grace.py` (removed 2026-10-08):
  - `show` prints the current DOS/grace table.
  - `preview` prints the before/after transition and writes nothing.
  - `apply` writes, only after the user confirms. It updates `config/tx_table.yaml`, the
    `AML_LOT_TX_TABLE` CASE (cell 18) and the reference table, adds an entry here, and runs
    `tools/check_config.py`.
- When the product or value is missing, the skill asks for it.
- `tools/validate_pack.py` now applies the KBT section checks only to `kbt-*` skills.
- No DOS or grace value was changed.

## Pack files trimmed (2026-10-07)

- Removed `LATENCY_DESIGN.md`, `SOURCE_LINEAGE.md`, `TESTING_GUIDE.md` and `VALIDATION_REPORT.txt`.
  - Lineage is summarised above.
  - Testing is `tools/validate_pack.py` plus `tools/check_config.py`, with the eval prompts in `evals/`.
  - The validation report is produced by running the validator.

## Business_Rules moved to the pack root (2026-10-07)

- The Data_Sources/Business_Rules folder moved to `Business_Rules/`, next to `config/` and `context/`.
  `Data_Sources/` (now `scripts/`) then held only the notebooks, pldlib and the data dictionaries.
- Every reference was updated to `Business_Rules/...`. `tools/validate_pack.py` now also checks
  `Business_Rules/` and `config/` paths cited in markdown.

## Business-rules page synced (2026-10-07)

- Stored the revised page (received as `Downloads/AML_Base_Layer_Business_Rule.html`) as
  `AML_Base_Layer_Business_Rules.html`, keeping the existing filename. The 2026-10-01 revision was
  archived as `AML_Base_Layer_Business_Rules_v1_2026-10-01.html`. Both are now under `Business_Rules/`
  (see the move above).
- **What the revision changed:**
  - It dropped the methodology-change notes, the cytarabine grace note, the SCT/timing/arsenic flags
    section, the calendar-semester rule, the "What comes out" KPI section, the rule index, the open
    items table and four glossary entries.
  - It now lists five eligibility flags, where it previously had eight.
  - It added 7 legacy ICD-9 codes.
  - Rx sources are now "retail and mail order".
  - Legacy rule wording now matches the code.
- **Pack updates:**
  - `key_concepts.md`: the disagreement list was rebuilt. Resolved items were removed, new ones added:
    the ICD-9 206/207 codes, the flag count, and the lookback wording.
  - `reference_codes_and_mappings.md`: added the ICD-9 crosswalk, and the cytarabine note now says the
    page agrees with the code.
  - Flags, NPS, SCT, patient pool and intensity metrics: the lineage now points to the notebooks and
    the archive for content the page no longer carries.
  - `config/common.yaml`: added `codes.aml_dx_icd9_page`, which is not used by the code.
  - Open items OI-14 (ICD-9 206/207) and OI-15 (content dropped from the page) were added.
- No notebook, verified query or config value used by the code changed. The page now agrees with the
  code in more places, and nothing in it contradicts a rule the pack takes from code.

## File names simplified (2026-10-07)

- Notebooks: dropped the `01_`-`05_` prefixes and `_VAL_`, giving `AML_LOT_TX_TABLE`,
  `AML_LOT_SOB_EPISODE`, `AML_LOT_REGIMEN`, `AML_LOT_PATIENT_INTENSITY_LOT` and
  `AML_PATIENT_ELIGIBILITY`. Notebook title cells were updated to match.
- Config: dropped the prefixes, giving `tx_table.yaml`, `sob_episode.yaml`, `regimen.yaml`,
  `intensity_lot.yaml` and `eligibility.yaml`.
- Every reference across the pack now uses the new names. "Notebook 01-04" now reads "the four AML_LOT
  notebooks", and "05" now reads "AML_PATIENT_ELIGIBILITY".
- The run order is no longer implied by the file names. It is listed in
  `workflows/aml_base_layer_refresh.md`, and `tools/check_config.py` now loads the notebooks by name in
  that order.
- Table names are unchanged; `_BUSINESS_RULE_CHANGE_VAL` inside table names is part of the database
  object name.

## Notebook parameterization (2026-10-07)

- Inventoried the hardcoded values in the five notebooks and moved each into YAML under `config/`:
  - `common.yaml`: values shared by all notebooks, i.e. Spark, pldlib, schemas, filters, suffix, 26 table
    names, Dx code sets, basket.
  - One file per notebook (`tx_table.yaml` … `eligibility.yaml`).
- Added `config/load_config.py`, which merges common + notebook config, resolves `{cws}`/`{suffix}` and
  cross-references, and provides SQL helpers.
- Added `config/HARDCODED_INVENTORY.md`, which maps each value to its cell and lists six
  inconsistencies the parameterization exposes.
- Added `tools/check_config.py`, which confirms the YAML matches the notebook code: table names, code
  lists, grace/DOS, backbone order, legacy rule/B lists, pldlib arguments, SCT codes and thresholds.
- Notebooks are unchanged; values were copied exactly as coded.

## Initial build (2026-10-07)

- New pack following the Venclexta KBT-first layout, scoped to the AML base layer.
- Five KBTs, one per notebook: TX table, SOB/episode, regimen, patient intensity + LoT, patient
  eligibility.
- 24 verified queries rendered from the notebooks (CREATE wrappers removed, temp views inlined as
  CTEs); 3 labelled SQL equivalents for pandas steps.
- 28 table profiles: 13 base-layer profiles and 4 source-view profiles reused from the Venclexta pack, 11 new.
- 9 metrics (6 reused/adapted from the Venclexta pack, 3 new: line of therapy, patient intensity,
  patient pool).
- Domain, taxonomy, defaults and SME references taken from the Venclexta pack's AML content.
- Open items OI-01 to OI-12 (Venclexta pack BL-01 to BL-10 renumbered, plus the suffix mismatch and
  the pldlib gap).

## Notebook fix applied while building

- `AML_LOT_PATIENT_INTENSITY_LOT.ipynb` cell 44 (new-definition inputs): the query passed
  `{lot_regimen_group}` to Spark without `.format()`, so the cell could not run. It now formats the
  grouping table name. The stray trailing `;` inside the query was also removed. Updated in both
  `base_layer_update/` and `scripts/Notebooks/`.

## pldlib integrated (2026-10-07)

- Added `scripts/pldlib/pldlib.egg` (the library every notebook loads) and its extracted `.py`
  source in `scripts/pldlib/source/`.
- New `context/domain/pldlib.md`: how stencil calls work and what `sob`, `episode` and `regimen`
  compute with the AML parameters.
- `AML_SOB`, `AML_EPISODE`, `AML_REGIMEN` now contain the full SQL pldlib generates for the notebook
  parameters (rendered from the library source), replacing the parameter-only placeholders.
- Corrections found in the library source: the episode table is one row per patient x product x
  episode (not claim level); the SOB table carries source-of-business labels (`sob_lvl7` etc.); the
  360-day lookback affects only those labels, not episode breaks; REGIMEN products are alphabetical;
  single-day episodes never form regimens. SOB, episode and regimen column files rebuilt from the SQL.
- OI-12 closed; OI-13 added (use of pldlib NTB labels for AML NPS).

## Notebook folder flattened (2026-10-07)

- `scripts/Notebooks/` now holds only the five notebooks ; the `Split/` and `Original/`
  subfolders were removed. The original team notebooks (`AML_LOT_VAL.ipynb`, `Patient Eligibility.ipynb`)
  remain in the source `base_layer/` folder outside the pack.
- References to the originals now point to the matching pack notebook. The two tables only the
  original builds (RR LoT refinement, HCP affiliations) are described as "original team notebook, not in
  this pack".

