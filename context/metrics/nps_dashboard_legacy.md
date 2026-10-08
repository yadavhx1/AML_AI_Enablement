# AML NPS dashboard share (legacy IC definition)

**Metric id:** `nps_dashboard_legacy`
**Aliases:** NPS dashboard, NPS share, VEN share, VEN NPS share, HMA share, NPS by LoT, NPS by account, Ipsos index, legacy IC definition
**Working behavior:** Use the documented definition and calculation.

## Definition
New patient starts into a line of therapy, grouped by the line's legacy backbone (Venclexta, HMA, other
novel agents), with the share of each group among all starts in the same slice and month. The published
figure is the IC Ineligible 1L share for gated patients.

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

## Grain and dimensions
One row per patient x line; cut by month or semester, LOT, legacy-rule cohort, eligibility flags, backbone
group, account subtype or group, HCP decile and segment

## Source tables
MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_PBI_DATA_*; MABI_AML_NPS_DASHBOARD_LOT_MONTH_NPS_SUMMARY_*;
MABI_AML_NPS_DASHBOARD_IPSOS_INDEX_REF_*; MABI_AML_NPS_DASHBOARD_1L_IC_INELIG_FINAL_DATA_MONTH_ROLLUP_*

## Caveats
Differs from `nps_count` in three ways: the backbone is chosen over the whole line from rank lists (not
the regimen backbone), every line counts as a start (2L+ reported alongside 1L), and the shipped month is
the line end month (OI-17). ARSENIC_FLG is not applied; it has no effect on the IC_INELIG slice. Flags come
from the un-suffixed Aug'26 build while lines come from `_v2` (OI-02). The index and account rollup are
ungated and count every line. Table names carry personal suffixes (OI-16).

## Source lineage
- scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb (cells 26-101)
- Summary sheet of `2026-07-24_aml_nps_summary_by_lot_month_*.xlsx`, as described in notebook cell 75
