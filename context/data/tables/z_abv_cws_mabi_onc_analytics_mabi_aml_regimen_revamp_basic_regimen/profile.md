# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_BASIC_REGIMEN_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `03` (`scripts/Notebooks/`); KBT 3.

**Family:** APLD (AML base layer)
**Contains:** AML regimens: overlapping product episodes combined into one comma-joined regimen per period
**Common analyses:** aml_regimen_mix, aml_lot_base

## Grain

One row per patient regimen period. (scripts/Notebooks/AML_LOT_REGIMEN.ipynb cells 73-76)

## Primary keys or entity keys

PATIENT_GID_RGMN + REGIMEN_START_DATE.

## Row meaning

A period during which a fixed set of products was active for the patient.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. `stencil.regimen(collect_type_rgmn_vl='COLLECT_SET', clean_up_type_vl='no', regimen_threshold_vl='5000', regimen_removal_vl='0,1')` on the episode output.
2. REGIMEN names every product active at once, alphabetically sorted and comma-joined (e.g. 'AZACITIDINE, VENCLEXTA'). Cut points are episode starts and EPISODE_END_DATE1_DRVD; each interval takes the products whose episode covers its midpoint (`context/domain/pldlib.md`). Full output schema from the pldlib SQL.
3. No consolidation of short regimens is applied downstream (commented out in the 2026 build).

## Join guidance

PATIENT_GID_RGMN = PATIENT_GID on the LoT and cohort tables.

## Caveats

1. Patient key column is PATIENT_GID_RGMN here, PATIENT_GID elsewhere.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_REGIMEN.ipynb cells 73-76; pldlib stencil

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
