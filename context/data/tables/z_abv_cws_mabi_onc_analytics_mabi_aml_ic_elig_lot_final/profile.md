# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_IC_ELIG_LOT_FINAL_BUSINESS_RULE_CHANGE_VAL_v2

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** Regimen-level LoT for IC Eligible AML patients (28-product backbone hierarchy)
**Common analyses:** aml_lot_build

## Grain

One row per IC Eligible patient regimen.

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

Regimen-level LoT for IC Eligible AML patients (28-product backbone hierarchy).

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. Backbone CASE (LIKE, branch order = hierarchy): S-DAC/HI-DAC first ... ARSENIC_TRIOXIDE last; HMAs -> 'HMA'.
2. Same LINE_CHANGE / LOT rules as the IC Ineligible table. Patient key is PATIENT_GID_RGMN.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_LOT_PATIENT_INTENSITY_LOT.
