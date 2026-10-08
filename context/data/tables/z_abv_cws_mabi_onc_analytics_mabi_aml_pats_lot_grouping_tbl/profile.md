# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_LOT_GROUPING_TBL_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** One row per AML patient line: line start/end and the union of every product used in the line
**Common analyses:** aml_regimen_by_line, aml_days_on_therapy, aml_intensity_rule_b

## Grain

One row per patient x LOT. (scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 122-127)

## Primary keys or entity keys

PATIENT_GID + LOT.

## Row meaning

A complete line of therapy summarized across its regimens.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. LOT_START_DATE = MIN(REGIMEN_START_DATE); LOT_END_DATE = MAX(REGIMEN_END_DATE) within the line.
2. LOT_REGIMEN_GROUP = alphabetically sorted, de-duplicated union of products across the line's regimens.
3. Built in pandas from the combined LoT table, then written back.

## Join guidance

PATIENT_GID + LOT to the combined LoT table.

## Caveats

1. The `_v2` notebook writes this table with an unformatted `{lot_regimen_group}` placeholder in the DROP/CREATE statement; confirm the `_v2` table exists before reading it.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 122-127; scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 89-92

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
