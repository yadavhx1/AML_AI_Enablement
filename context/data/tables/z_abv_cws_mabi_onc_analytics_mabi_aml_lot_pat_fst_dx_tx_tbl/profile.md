# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_FST_DX_TX_TBL_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `05` (`scripts/Notebooks/`); KBT 5.

**Family:** APLD (AML base layer)
**Contains:** Per-patient AML anchor dates: first AML diagnosis, first and last treatment, Venclexta start and end
**Common analyses:** aml_time_to_treatment, ven_start_cohorts, aml_eligibility

## Grain

One row per patient. (scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb cells 146-150)

## Primary keys or entity keys

PATIENT_GID.

## Row meaning

The anchor dates every AML eligibility flag and VEN-based KPI is measured from.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. FIRST_DX = MIN(CLAIM_DATE) on the 37 AML codes in `abv_val_ptd_onc_synd.dx_fact_curated_vw` (no source filter).
2. FIRST_TX / LAST_TX = MIN regimen start / MAX regimen end from the combined LoT table.
3. VEN_START / VEN_END = MIN Venclexta episode start / MAX Venclexta EPISODE_END_DATE1_DRVD; NULL for patients without Venclexta.

## Join guidance

PATIENT_GID to the LoT and flags tables.

## Caveats

1. QC: no NULL FIRST_DX or LAST_TX (Aug'26). The `_v2` copy omits VEN_START / VEN_END.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb cells 146-150; scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb cell 94

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
