---
name: kbt-03-regimen
description: Use for AML base-layer questions about regimens, which products are given together, combination regimens such as Venclexta plus azacitidine, regimen start and end dates, regimen counts or regimen mix, built by the pldlib regimen step from episodes (`AML_LOT_REGIMEN`).
user-invocable: true
---


# KBT 3 - Regimen (AML_LOT_REGIMEN)

## Analytical intent

Use this KBT when the output is about regimens: the set of products a patient is on at the same time,
regimen mix, regimen counts, or regimen dates. Use KBT 4 for line of therapy, backbone or intensity.

Notebook: `scripts/Notebooks/AML_LOT_REGIMEN.ipynb`.

## Method

1. Input: the persisted episode table from KBT 2.
2. `stencil.regimen` with `COLLECT_SET`, `clean_up_type_vl = 'no'`, `regimen_threshold_vl = '5000'`:
   every episode start and `EPISODE_END_DATE1_DRVD` is a cut point. Each interval between cut points
   takes every product whose episode covers the interval midpoint. Uncovered intervals (treatment
   gaps) drop out, and single-day episodes (start = end) never form a regimen.
3. `REGIMEN` is the alphabetically sorted, comma-joined product set (e.g. `AZACITIDINE, VENCLEXTA`).
   Match a product with `LIKE '%PRODUCT%'`; an exact regimen can be matched on the sorted string.
   Use `REGIMEN`, not `UPDATED_REGIMEN` (threshold 5000 makes the update flags meaningless here).
4. The patient key here is `PATIENT_GID_RGMN`; rename it to `PATIENT_GID` when joining to other tables.
5. No consolidation is applied at any later step: short regimens stay as their own rows (the 2026 rule
   change). Regimen counts are therefore higher than in pre-2026 builds.
6. For regimen mix, count distinct patients per regimen; for a time cut, assign each regimen to its
   start month or semester.
7. Validate: patient count equals the episode table; each regimen start ≤ end.

## Working defaults

- Regimen label = the stored string (alphabetical product order).
- Regimen mix basis: distinct patients.
- Combination attribution to one product: by backbone (KBT 4), disclosed (OI-09).

## Context to read

- `context/domain/key_concepts.md` (regimen step)
- `context/domain/pldlib.md` (what the regimen function computes)
- `context/data/tables/<regimen table>/profile.md`
- `context/domain/reference_codes_and_mappings.md` (product names)

## Verified-query candidates

- `AML_REGIMEN`, `AML_REGIMEN_PATIENT_COUNT`.

## Minimum QC

- Product matching uses LIKE on the regimen string.
- Patient counts are distinct and reconcile to the episode table.
- The no-consolidation rule is disclosed when comparing with older numbers.


## Output contract

Return the requested result first. State the data source, grain, period, build suffix and material
assumptions. Keep patient identifiers out of the response.
End with the `How this answer was generated` provenance table and append it to `outputs/response_log.md` (`context/response_provenance.md`).
