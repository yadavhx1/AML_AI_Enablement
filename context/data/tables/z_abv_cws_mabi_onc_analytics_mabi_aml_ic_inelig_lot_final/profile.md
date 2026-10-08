# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_INELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** Regimen-level LoT for IC Ineligible AML patients (11-product backbone hierarchy)
**Common analyses:** aml_lot_build

## Grain

One row per IC Ineligible patient regimen.

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

Regimen-level LoT for IC Ineligible AML patients (11-product backbone hierarchy).

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. Backbone CASE (RLIKE): VENCLEXTA, TIBSOVO, REZLIDHIA, IDHIFA, XOSPATA, DAURISMO, L-DAC, then AZACITIDINE/DECITABINE/INQOVI/ONUREG -> HMA.
2. LINE_CHANGE: REG_NUM=1 -> 1; PREV_GAP > 90 -> 1; same backbone -> 0; VENCLEXTA<->HMA -> 0; else 1. LOT = running sum.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_LOT_PATIENT_INTENSITY_LOT.
