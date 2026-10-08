# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_RX_ACT_TBL_AML_EXACT_DATES_KA

**Notebook:** `05` (`scripts/Notebooks/`); KBT 5.

**Family:** APLD (AML base layer)
**Contains:** Distinct patient x claim date of pharmacy (Rx) activity for AML base-layer patients
**Common analyses:** aml_eligibility_flags

## Grain

One row per patient per Rx activity date.

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

Distinct patient x claim date of pharmacy (Rx) activity for AML base-layer patients.

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. Claims-view rows with source_type LIKE '%RX%' for patients on the combined LoT table; no source filters.
2. No `_v2` suffix even though the Mx table has one; both are rewritten by AML_PATIENT_ELIGIBILITY.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_PATIENT_ELIGIBILITY.
