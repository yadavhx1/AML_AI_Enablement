# Days on therapy / line duration (AML)

**Definition id:** `days_on_therapy`
**Aliases:** DOT, DoT, days on therapy, line length, LINE_LENGTH, REGIMEN_LENGTH, EPISODE_LENGTH, Time on Line, length of therapy
**Working behavior:** Use the documented definition and calculation.

## Definition
Elapsed days between the start and end of an AML episode, regimen or line of therapy.

## Calculation
```text
EPISODE_LENGTH = DATEDIFF(EPISODE_END_DATE1_DRVD, EPISODE_START_DATE_DRVD)        -- KBT 2
REGIMEN_LENGTH = DATEDIFF(REGIMEN_END_DATE, REGIMEN_START_DATE)                     -- KBT 3/4
LINE_LENGTH    = DATEDIFF(LOT_END_DATE, LOT_START_DATE)                             -- KBT 4
  LOT_START_DATE = MIN(REGIMEN_START_DATE), LOT_END_DATE = MAX(REGIMEN_END_DATE) per patient x LOT
  (stored on MABI_AML_PATS_LOT_GROUPING_TBL)
GAP_TO_NEXT_LINE = DATEDIFF(next LOT_START_DATE, LOT_END_DATE)
```

## Grain and dimensions
One value per patient per episode / regimen / line

## Source tables
MABI_AML_REGIMEN_REVAMP_EPISODE_*; MABI_AML_PATS_COMB_LOT_TBL_*; MABI_AML_PATS_LOT_GROUPING_TBL_*

## Caveats
Lines are claims-derived, not physician-documented. An episode or line still open at the data cut is
right-censored: flag it rather than treating its end as a stop. A gap of up to 90 days stays inside a
line, so line length includes treatment gaps. AML is "Acute, fast-progressing" with "Short treatment
cycles" and "High early mortality": short durations are expected, and a short line is not on its own a
data-quality issue. Report median and mean with the distribution.

## Source lineage
- scripts/Notebooks/02, 04
