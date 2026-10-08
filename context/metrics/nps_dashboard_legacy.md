# AML NPS dashboard share (legacy IC definition)

**Metric id:** `nps_dashboard_legacy`
**Aliases:** NPS dashboard, NPS share, VEN share, VEN NPS share, HMA share, NPS by LoT, NPS by account, NPS by HCP, NPS by segment, NPS by decile, initiating HCP, Power BI dataset, Ipsos index, reported NPS, legacy IC definition
**Working behavior:** Use the documented definition and calculation.
**Primary KBT:** 4 (lines, intensity). Gates come from KBT 5. There is no separate NPS KBT: this file is the
method for every NPS dashboard question.

## Definition
New patient starts into a line of therapy, grouped by the line's legacy backbone (Venclexta, HMA, other
novel agents), with the share of each group among all starts in the same slice and month. The published
figure is the IC Ineligible 1L share for gated patients. Built by
`scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb`, which runs after the
full base layer (after AML_PATIENT_ELIGIBILITY).

## Calculation
```text
LINE_BACKBONE  = highest-ranked product of LOT_REGIMEN_GROUP on the IC_ELIG (28) / IC_INELIG (11) rank list
BACKBONE_GROUP = VENCLEXTA | HMA (AZACITIDINE, DECITABINE, ONUREG, INQOVI) | OTHER NOVEL AGENTS
start          = DISTINCT PATIENT_GID x LOT, month of LOT_END_DATE (shipped) or LOT_START_DATE
VEN_NPS        = starts with BACKBONE_GROUP = VENCLEXTA        (HMA_NPS, OTHERS_NPS alike)
VEN_SHARE      = VEN_NPS / TOTAL_NPS within one DX_LB_ELIG_FLG x DX_TX_DIFF_FLG x PATIENT_COHORT x LOT x month
Published      = DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1, PATIENT_COHORT = 'IC_INELIG', LOT = 1,
                 months summed to semesters, share recomputed
Index          = reported VEN_NPS / TOTAL_NPS (repository) vs SHA counts by month of line start (ungated)
```

## Method
1. Lines: one row per patient × LOT from `MABI_AML_PATS_LOT_GROUPING_TBL_*` (every line, not only 1L),
   with the cohort's `PATIENT_INTENSITY_GROUP` (legacy rule by default; the new definition in a
   `_NEWDEF` build). Line construction is KBT 4.
2. Legacy line backbone: the highest-ranked product of the whole line (`LOT_REGIMEN_GROUP`) on the
   IC_ELIG list (28 products, S-DAC first) or the IC_INELIG list (11, VENCLEXTA first). Any intensity other
   than IC_ELIG, including no cohort row, uses the IC_INELIG list. Products are named (AZACITIDINE, not
   HMA); none listed → `UNKNOWN`. The lists are in `config/nps_dashboard_legacy.yaml` `line_backbone`.
   This is not the KBT 4 `BACKBONE`, which is per regimen and groups HMAs.
3. Initiating HCP: the NPI on the first backbone-product claim inside the line dates (claim date ASC,
   NPI DESC, claim id); ONC / SHA_PTD / VENC_AML claims, no FILGRASTIM, NPI not null. Mapped to the
   Abbott customer id through `CUSTOMER_TBL`.
4. Account subtype per HCP: ONH2 HCI-HCP affiliations, Reltio for HCPs without one, joined to
   `heme_account`; the lowest-ranked subtype wins (Elite Oncology Center 1 … DOD 8). The rollup groups
   Elite + Academic Teaching Hospital as Academic and everything else as Community.
5. Segments: UNI_DECILE and ABOVE_BRAND_SEGMENT, plus EXECUTION_SEGMENT from the GNE `_BKP` table, all
   on NPI. Missing values become `Not Available`.
6. Backbone group: VENCLEXTA; AZACITIDINE / DECITABINE / ONUREG / INQOVI = HMA; everything else
   (UNKNOWN too) = OTHER NOVEL AGENTS.
7. Summary: DISTINCT patient × line starts by DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT and
   month. The flags (KBT 5) are LEFT-joined; unmatched patients get -1 / `Not Available`. Share = group
   starts / all starts in the slice and month. The month is the line END month as shipped
   (`SUMMARY_TIME_BASIS = 'END'`, OI-17), from 2019.
8. Published slice: `DX_LB_ELIG_FLG = 1`, `DX_TX_DIFF_FLG = 1`, `PATIENT_COHORT = 'IC_INELIG'`,
   `LOT = 1`. Sum the months to semesters and recompute the share; never average monthly shares.
9. Index and rollup: reported VEN and total NPS per month from the repository next to SHA counts by month
   of line START. These count every line and both intensities without gates.
10. Validate: patient count equals the grouping table; `UNKNOWN` backbones and NULL `NPI_REGIMEN` on
    LOT = 1 counted; unmatched-flag starts counted; month volumes sum to the published semesters for the
    published slice; LOT volume falls steeply after 1L.

## Working defaults
- Slice: the published slice (method step 8) unless the question names another. Name the slice.
- IC definition: legacy rule unless the user explicitly asks for the new definition. A new-definition
  dashboard needs the full base layer run with `run.intensity_definition: new`; it reads and writes
  `_NEWDEF` tables, and the published legacy dashboard tables are untouched.
- Time basis: line END month, as shipped. Say so, and give the START-month figure if the user means
  start (`nps_count.md` uses the line-1 start).
- Arsenic: the notebook does not read ARSENIC_FLG. The legacy rule puts arsenic patients in IC_ELIG, so the
  IC_INELIG slice is unaffected. Apply `ARSENIC_FLG = 1` (KBT 5) for IC_ELIG or all-intensity cuts.
- Tables: read the names in `config/nps_dashboard_legacy.yaml` (personal `_SATEEK` suffixes, OI-16).
  Lines are `_v2`, flags are the un-suffixed Aug'26 build (OI-02).
- Combination lines attribute to the legacy backbone (OI-09).
- Small cells: report n and roll months up to semesters when thin.

## Context to read
- `context/metrics/nps_count.md` (line-1 start definition)
- `context/domain/aml_eligibility_flags.md` (DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT)
- `context/domain/reference_codes_and_mappings.md` (rank lists, HMA products)
- Profiles for the dashboard, summary and HCP tables (`family = aml_nps_dashboard` in
  `context/data/table_index.tsv`)
- `workflows/aml_nps_dashboard_legacy.md` for a dashboard refresh
- `context/data/source_dictionaries/` (README points 4 and 6, `view_column_lineage.tsv` row
  `mdm_npi_number`) only for HCP attribution questions: why starts have no NPI, or whether rejected or
  reversed claims can drive an attribution. Never query the raw tables.

## Verified queries
In `verified_queries/nps_dashboard/` (indexed under KBT 4, metric `nps_dashboard_legacy`):
`AML_NPS_LINE_BACKBONE` (SQL equivalent of the pandas step), `AML_NPS_REG_NPI_ACI`,
`AML_NPS_ACCOUNT_TYPE_GROUP`, `AML_NPS_HCP_INFO_MAP`, `AML_NPS_DASH_PBI_DATA`,
`AML_NPS_LOT_MONTH_SUMMARY`, `AML_NPS_IPSOS_INDEX`, `AML_NPS_ACCT_MONTH_ROLLUP`.

## Grain and dimensions
One row per patient x line; cut by month or semester, LOT, legacy-rule cohort, eligibility flags, backbone
group, account subtype or group, HCP decile and segment

## Source tables
MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_*; MABI_AML_NPS_DASHBOARD_LOT_MONTH_NPS_SUMMARY_*;
MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_*; MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_FINAL_DATA_MONTH_ROLLUP_*

## Minimum QC
- The slice (flags, cohort, LOT) and the time basis (start or end month) are named.
- The share is recomputed from volumes for every roll-up.
- Totals are not summed across slices or flag values.
- The legacy line backbone is not mixed with the KBT 4 regimen backbone in one figure.
- Index and rollup figures are labelled as ungated, all lines.

## Caveats
Differs from `nps_count` in three ways: the backbone is chosen over the whole line from rank lists (not
the regimen backbone), every line counts as a start (2L+ reported alongside 1L), and the shipped month is
the line end month (OI-17). ARSENIC_FLG is not applied; it has no effect on the IC_INELIG slice. Flags come
from the un-suffixed Aug'26 build while lines come from `_v2` (OI-02). The index and account rollup are
ungated and count every line. Table names carry personal suffixes (OI-16).

## Output contract
Return the requested result first. State the data source, slice, line, time basis, period, input table
names and material assumptions. Keep patient identifiers and NPIs out of the response; report HCP results
at account, decile or segment level.
End with the `How this answer was generated` provenance table and append it to `outputs/response_log.md` (`context/response_provenance.md`).

## Source lineage
- scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (cells 26-101)
- Summary sheet of `2026-07-24_aml_nps_summary_by_lot_month_*.xlsx`, as described in notebook cell 75
