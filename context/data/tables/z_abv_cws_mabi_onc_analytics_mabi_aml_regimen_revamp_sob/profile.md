# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_SOB_BUSINESS_RULE_CHANGE_VAL_v2

**Notebook:** `02` (`scripts/Notebooks/`); KBT 2.

**Family:** APLD (AML base layer)
**Contains:** pldlib stencil.sob output: de-duplicated AML treatment claims with episode numbers, episode dates and source-of-business labels
**Common analyses:** aml_episode_build

## Grain

One row per kept claim (same-day duplicates for a product removed).

## Primary keys or entity keys

PATIENT_GID (plus claim/date columns where present).

## Row meaning

pldlib stencil.sob output: de-duplicated AML treatment claims prepared for episode building.

## Refresh

Rebuilt (DROP + CREATE) each time the notebook runs. State the run date and data cut.

## Mandatory filters

None beyond the build.

## Business rules

1. stencil.sob(grace='GRACE_VALUE', lookback='360', dedup_type_vl='yesremove'), dedup partition PATIENT_GID, FINAL_PRODUCT_NAME, CLAIM_DATE ordered DOS_FINAL DESC, CLAIM_ID.
2. Output schema taken from the pldlib SQL (`verified_queries/kbt-02/aml_sob.sql`; `context/domain/pldlib.md`): input columns plus derived claim, episode and SOB columns.

## Join guidance

PATIENT_GID keeps the `SHA_PTDONC` suffix; join directly to other base-layer tables.

## Caveats

1. Intermediate table; prefer the downstream final table for analysis.
2. Patient identifiers never leave the working query.
3. Suffix: the four AML_LOT notebooks write `_v2`, AML_PATIENT_ELIGIBILITY writes the un-suffixed name (OI-02).

## Pipeline and lineage

See `context/domain/key_concepts.md` (AML base layer pipeline).

**Produced by:** `scripts/Notebooks/` AML_LOT_SOB_EPISODE.
