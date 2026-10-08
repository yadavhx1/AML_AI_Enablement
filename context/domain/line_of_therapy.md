# Line of therapy (AML)

**Definition id:** `line_of_therapy`
**Aliases:** LOT, LoT, line of therapy, 1L, 2L+, line distribution, LINE_CHANGE, LoT mix
**Working behavior:** Use the documented definition and calculation.

## Definition
A run of regimens counted as one continuous course of treatment. A new line starts on a gap of more
than 90 days, or on a backbone change within 90 days unless the change is VENCLEXTA <-> HMA.

## Calculation
```text
LINE_CHANGE = CASE WHEN REG_NUM = 1 THEN 1
                   WHEN PREV_GAP > 90 THEN 1
                   WHEN BACKBONE = PREV_BACKBONE THEN 0
                   WHEN VENCLEXTA <-> HMA (either direction) THEN 0
                   ELSE 1 END
PREV_GAP    = DATEDIFF(REGIMEN_START_DATE, previous REGIMEN_END_DATE)
LOT         = SUM(LINE_CHANGE) over the patient's regimens in start order
LoT mix     = share of active patients in 1L vs 2L+ at a point in time, by backbone
```

## Grain and dimensions
Regimen rows on the combined LoT table; count lines at patient x LOT

## Source tables
MABI_AML_PATS_COMB_LOT_TBL_* (TYPE, BACKBONE, LOT); MABI_AML_PATS_LOT_GROUPING_TBL_* (line bounds)

## Caveats
Backbone hierarchies differ by intensity (reference_codes_and_mappings.md). No consolidation: every
regimen counts, so lines change more often than in pre-2026 builds (rule_change_history.md). Claims-
derived, not clinical lines. AML line groups use 1L and 2L+.

## Source lineage
- scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb
