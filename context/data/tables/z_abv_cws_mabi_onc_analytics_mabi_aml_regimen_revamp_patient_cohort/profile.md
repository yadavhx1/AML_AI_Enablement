# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_PATIENT_COHORT_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** legacy rule patient intensity (IC_ELIG / IC_INELIG) per AML patient, decided once over the whole journey
**Common analyses:** aml_intensity_split, aml_lot_base

## Grain

One row per patient. (scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cell 80)

## Primary keys or entity keys

PATIENT_GID_RGMN.

## Row meaning

The patient's product-only intensity class.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. LOW_INTENSITY = 0 when any regimen contains an IC-Eligible-only product (ARSENIC_TRIOXIDE, CLADRIBINE, CLOFARABINE, CYCLOPHOSPHAMIDE, S-DAC, HI-DAC, DAUNORUBICIN, ETOPOSIDE, FLUDARABINE, IDARUBICIN, MITOXANTRONE, MYLOTARG, NEXAVAR, RYDAPT, VANFLYTA, VINCRISTINE, VYXEOS), else 1; patient value = MIN over regimens.
2. PATIENT_INTENSITY_GROUP = 'IC_INELIG' when LOW_INTENSITY = 1, else 'IC_ELIG'.
3. INQOVI and ONUREG count as IC-Ineligible products since the 2026 change.

## Join guidance

PATIENT_GID_RGMN = PATIENT_GID.

## Caveats

1. Aug'26 split: 60,839 IC_INELIG / 23,360 IC_ELIG. `_v2`: 43,194 / 14,503.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cell 80; scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cell 42

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
