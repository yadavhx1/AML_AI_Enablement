# New patient starts (AML base layer)

**Metric id:** `nps_count`
**Aliases:** NPS, NPS Volume, new patient start, new start, 1L start, NPS by regimen, NPS by backbone
**Working behavior:** Use the documented definition and calculation.

## Definition
A patient beginning their first line of therapy (LOT = 1), counted once per patient at the line-1
start, by regimen or backbone and month. "NPS start date = 1L treatment start date for a given
patient"; "NPS Volume for a given regimen = Count of patients for a given regimen".

## Calculation
```text
NPS_START_DATE = MIN(REGIMEN_START_DATE) WHERE LOT = 1     -- MABI_AML_PATS_COMB_LOT_TBL_*
NPS volume     = COUNT(DISTINCT PATIENT_GID) by start month and regimen/backbone of the first regimen
Gate (published NPS share): ARSENIC_FLG = 1, DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1 (flags table, KBT 5)
NPS share      = product (or backbone) NPS / all gated AML NPS in the same period
```

## Grain and dimensions
One row per patient (line-1 start); cut by start month/semester, regimen, backbone, intensity (TYPE)

## Source tables
MABI_AML_PATS_COMB_LOT_TBL_*; MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*

## Caveats
Not the CLL 36-month new-start rule; AML uses the line-1 start. A later line change is never a new
start. For combination regimens the start attributes to the backbone (open item OI-09) unless the
question asks for the regimen. AML line groups are null before Jan 2019 (FDA approval floor); SHA data
from 2019 onwards is used. The five-notebook build has no relapse/remission refinement (OI-08).
The NPS dashboard (`nps_dashboard_legacy.md`, run under KBT 4) uses a line-level legacy backbone, counts every line
and dates starts by line end month as shipped; use that metric for dashboard figures.

## Source lineage
- AML_Base_Layer_Business_Rules_v1_2026-10-01.html, the archived 2026-10-01 revision (removed from the pack; a copy is in `aml_context_pack_kbt.zip`) (Section 13,
  "What comes out"). The current revision dropped that section and only says KPIs are "a filter and a
  count against the finished line-of-therapy table". The definition here is unchanged.
- scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb (LOT assignment)
- AML SHA Business Rules Guide V5.pptx (via the Venclexta pack)
