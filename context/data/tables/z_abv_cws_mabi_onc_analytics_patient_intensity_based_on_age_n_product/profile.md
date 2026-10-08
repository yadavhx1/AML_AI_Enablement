# Z_ABV_CWS_MABI_ONC_ANALYTICS.PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_v2` where the May'26 build writes one (see caveats).

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** new definition (age + line-1 product) AML patient intensity and the matching line-1 backbone
**Common analyses:** aml_intensity_rule_b, aml_intensity_comparison

## Grain

One row per patient (line 1). (scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 129-136)

## Primary keys or entity keys

PATIENT_GID.

## Row meaning

The patient's line-1 regimen group with new-definition intensity and backbone.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. Rule order: any IC-Eligible product in line 1 -> IC_ELIG; all line-1 products in {AZACITIDINE, DECITABINE, ONUREG, INQOVI, TIBSOVO, IDHIFA} -> IC_INELIG; else age = YEAR(FIRST_DX) - birth year, <= 65 -> IC_ELIG, > 65 -> IC_INELIG; no age -> IC_INELIG.
2. BACKBONE = lowest-rank product on the new-definition rank list for the class; 'UNKNOWN' when no product is on it. Rank lists keep HMAs as named products and rank S-DAC and HI-DAC separately.
3. SOURCE_PATIENT_HIPAA_BIRTH_YEAR from the claims view (SHA_PTD, ONC).

## Join guidance

PATIENT_GID to the flags table (surfaces as PATIENT_COHORT_UPDATED).

## Caveats

1. Not the production intensity: the LoT tables still split on legacy rule. Label any new definition figure as 'new definition (age + product)'.
2. BACKBONE vocabulary differs from the SQL LoT tables; do not union them.
3. The birth-year join is DISTINCT on patient_sk + birth year; a patient with two recorded birth years would duplicate. Check uniqueness before counting.
4. Written with the `_v2` name (`PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_v2`) by the May'26 build.
5. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
6. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
7. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 129-136; scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 94-101

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
