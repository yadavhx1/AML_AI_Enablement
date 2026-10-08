# Non-blocking analytical guidance

These rules guide implementation and validation. They do not create analytical dead ends.

## Privacy and output

- Never expose patient identifiers or attempt re-identification. PATIENT_GID / patient_sk stay inside
  the working query.
- No fixed minimum cell size (Q-62). Report the base (n), flag small-base cuts, and roll up to a coarser
  grain (e.g. semester instead of month) when a cut is too thin.

## Grain and counting

- Identify the table row grain before counting: claim (TX), claim/episode (SOB, episode), regimen
  (regimen, LoT tables), patient x line (grouping), patient (cohort, first Dx/Tx, flags).
- Deduplicate at the requested entity-time grain. Patient counts are COUNT(DISTINCT PATIENT_GID).
- The regimen and IC_ELIG tables key on PATIENT_GID_RGMN; rename before joining.
- Check whether joins multiply rows by comparing pre- and post-join patient counts.
- Name every denominator and keep numerator and denominator on the same gated frame.

## Cohorts and filters

- One build per query (`TABLE_SUFFIX_ALIGNMENT`). Name the suffix.
- Apply `ARSENIC_FLG = 1` and the KPI's gate set before computing a KPI; report the share removed.
- Intensity: the legacy rule unless the user explicitly asks for the new definition.
- When a required value is missing, use the assumption hierarchy and continue.

## Dates and freshness

- State the period and data cut (MAX(claim_date)). SHA lag is 2 months (Q-51); flag the latest two
  months as incomplete.
- AML line groups are null before Jan 2019; use SHA data from 2019 onwards for AML KPIs.
- Do not compare periods built under different business rules without naming the 2026 change.
- Flag any eligibility or censoring screen that removes more than 20% of the cohort (Q-63).

## Source interpretation

- SHA is partial capture (Rx 65-70%, hospital/procedure 30-40%); figures are claims-derived and
  unprojected.
- Claims-derived line of therapy is an analytical construct, not a clinical line.
- SOB = the pldlib source-of-business step: it de-duplicates claims, numbers episodes and labels each
  episode start (`sob_lvl7`, 360-day lookback). The AML line logic does not use those labels.
