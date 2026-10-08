# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_TX_RX_TXL_ELIG_TBL_BUSINESS_RULE_CHANGE_VAL

**Notebook:** `05` (`scripts/Notebooks/`); KBT 5.

**Family:** APLD (AML base layer)
**Contains:** Patients passing Rx continuity over the AML journey (TX_TXL_RX_ELIG_FLG)
**Common analyses:** aml_eligibility_flags

## Grain

One row per passing patient.

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

Patients passing Rx continuity over the AML journey (TX_TXL_RX_ELIG_FLG).

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. Built in AML_PATIENT_ELIGIBILITY, section 'First and last Tx (Rx)'. Rule in context/domain/aml_eligibility_flags.md.
2. Presence = pass; joined into the final flags table as 1/0.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_PATIENT_ELIGIBILITY.
