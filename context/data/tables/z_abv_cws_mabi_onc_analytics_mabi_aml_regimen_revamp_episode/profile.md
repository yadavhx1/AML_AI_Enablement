# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_EPISODE_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_REGIMEN_REVAMP_EPISODE_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `02` (`scripts/Notebooks/`); KBT 2.

**Family:** APLD (AML base layer)
**Contains:** AML product episodes built by pldlib stencil.sob + stencil.episode on the AML treatment claims
**Common analyses:** aml_persistency, aml_days_on_therapy, ven_start_end, source_of_business

## Grain

One row per patient x product x episode (pldlib episode output groups the SOB rows). (scripts/Notebooks/AML_LOT_SOB_EPISODE.ipynb cells 61-69)

## Primary keys or entity keys

PATIENT_GID + FINAL_PRODUCT_NAME + EPISODE_NUM_DRVD.

## Row meaning

One continuous same-product treatment episode.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None.

## Business rules

1. `stencil.sob(grace='GRACE_VALUE', lookback='360', dedup_type_vl='yesremove')`: same patient/product/day keeps the larger DOS (`DOS_FINAL DESC, CLAIM_ID`).
2. `stencil.episode`: consecutive same-product claims join while each falls inside the previous claim's DOS + grace window.
3. EPISODE_END_DATE1_DRVD = end of last claim; EPISODE_END_DATE2_DRVD = end of last claim + grace; EPISODE_END_DATE3_DRVD = last claim date (taxonomy).
4. VEN_START / VEN_END on the first Dx/Tx table = MIN(EPISODE_START_DATE_DRVD) / MAX(EPISODE_END_DATE1_DRVD) where FINAL_PRODUCT_NAME = 'VENCLEXTA'.

## Join guidance

PATIENT_GID to the regimen and LoT tables.

## Caveats

1. Full output schema from the pldlib episode SQL (`verified_queries/kbt-02/aml_episode.sql`); the earlier claim-level description was wrong - there is no CLAIM_ID / CLAIM_DATE / DOS_FINAL on this table.
2. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
3. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
4. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_SOB_EPISODE.ipynb cells 61-69; pldlib stencil

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
