# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_RR_12M_UPD_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_RR_12M_UPD_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** none of the five pack notebooks; built only by the original team notebook `Patient Eligibility.ipynb` (not part of this pack; kept in the source `base_layer/` folder).

**Family:** APLD (AML base layer)
**Contains:** AML regimen-level LoT with the relapse/remission promotion applied, giving the 1L / 2L+ group
**Common analyses:** aml_lot_distribution, aml_nps_by_lot, aml_lot_group

## Grain

One row per patient regimen (same rows as the combined LoT table). (original team notebook Patient Eligibility.ipynb cells 314-318)

## Primary keys or entity keys

PATIENT_GID + REG_NUM.

## Row meaning

A regimen with its raw LOT and its relapse/remission-refined line.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

As for the combined LoT table.

## Business rules

1. REG_LKBK = REGIMEN_START_DATE - 12 months. MAX_RR_DIAG_DT = latest diagnosis on one of the 13 AML relapse/remission codes in [REG_LKBK, REGIMEN_START_DATE], from `SHA_PTD_MABI_ONC_SYND.MABI_DX_TBL`.
2. MIN_RR_DT = MIN(MAX_RR_DIAG_DT) over the patient's regimens.
3. LOT_REF_INT = LOT + 1 when LOT = 1 and REGIMEN_START_DATE >= MIN_RR_DT, else LOT.
4. LOT_REF = '1L' when LOT_REF_INT = 1, '2L+' when > 1. This is the AML line group (`aml_lot_group` buckets 1L / 2L+).

## Join guidance

PATIENT_GID to the flags and first Dx/Tx tables.

## Caveats

1. The step runs after `spark.stop()` in the Aug'26 notebook and reads the legacy `SHA_PTD_MABI_ONC_SYND.MABI_DX_TBL`; confirm the table was refreshed with the current LoT build before using it.
2. Only line 1 is promoted; later lines keep LOT.
3. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
5. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** original team notebook Patient Eligibility.ipynb cells 314-318

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
