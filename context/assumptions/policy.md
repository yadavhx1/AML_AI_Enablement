# Assumption policy

Ambiguity should normally change the disclosure, not halt the analysis.

## Priority order

1. User instruction.
2. Most relevant verified-query convention.
3. Selected KBT default.
4. Registered default in `defaults.yaml`.
5. A neutral analytical default.

## Common neutral defaults

- Period: latest 12 complete months; SHA lag is 2 months (Q-51).
- Data cut: maximum available claim date after the analysis filters.
- Build: one table suffix per query (`TABLE_SUFFIX_ALIGNMENT`).
- Intensity: the legacy rule unless the user explicitly asks for the new definition (`AML_INTENSITY_RULE`).
- KPI gates: `AML_KPI_FLAG_SET`; always `ARSENIC_FLG = 1`.
- Duration summary: median and mean, always with the distribution (Q-61).
- Missing values: an explicit unknown bucket.
- Active patients and open lines: censor at the data cut.
- Small cells: no fixed threshold; flag small bases and roll up (Q-62).
- Screens removing more than 20% of the cohort: flag, and show with and without (Q-63).

## Recording assumptions

Put material assumptions in a SQL header and in the final response. Do not list immaterial coding
choices. Example:

```sql
-- ASSUMPTIONS
-- 1. Build = _BUSINESS_RULE_CHANGE_VAL_v2 (2+ AML Dx pool).
-- 2. Intensity = legacy rule (product-only).
-- 3. Gates = ARSENIC_FLG, DX_LB_ELIG_FLG, DX_TX_DIFF_FLG.
```
