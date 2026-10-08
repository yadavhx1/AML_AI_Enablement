# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_PATS_COMB_LOT_TBL_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `04` (`scripts/Notebooks/`); KBT 4.

**Family:** APLD (AML base layer)
**Contains:** AML regimen-level line of therapy with backbone, gap-and-backbone line-change flag and patient intensity (union of IC_ELIG and IC_INELIG builds)
**Common analyses:** aml_lot_distribution, aml_nps_by_lot, aml_regimen_by_line, aml_days_on_therapy

## Grain

One row per patient regimen. (scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 96-118)

## Primary keys or entity keys

PATIENT_GID + REG_NUM (or REGIMEN_START_DATE).

## Row meaning

A regimen with its backbone and the line of therapy it belongs to.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

Join the eligibility flags table and apply the KPI's flag set; filter TYPE for an intensity cut.

## Business rules

1. BACKBONE = highest-ranked product on the patient's intensity hierarchy (IC_INELIG 11 products, IC_ELIG 28; HMAs resolve to 'HMA'; S-DAC/HI-DAC grouped). See `reference_codes_and_mappings.md`.
2. LINE_CHANGE: REG_NUM = 1 -> 1; gap since previous regimen end > 90 days -> 1; gap <= 90 and same backbone -> 0; VENCLEXTA <-> HMA either way -> 0; any other backbone change -> 1.
3. LOT = running SUM(LINE_CHANGE) by patient in regimen-start order.
4. TYPE = legacy-rule intensity (IC_ELIG / IC_INELIG).
5. Every regimen is kept: the 2026 build removed short-regimen consolidation and the minimum-length filter.

## Join guidance

PATIENT_GID to `MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_*` (flags) and `MABI_AML_LOT_PAT_FST_DX_TX_TBL_*` (anchor dates).

## Caveats

1. LOT here is the raw gap/backbone line; the published 1L / 2L+ split adds the relapse/remission promotion in `MABI_AML_PATS_LOT_RR_12M_UPD_*` (LOT_REF).
2. A line distribution crossing the 2026 base-layer change mixes methods (see `rule_change_history.md`).
3. ARSENIC_TRIOXIDE regimens remain in the table; exclude via ARSENIC_FLG = 1.
4. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
5. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
6. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 96-118; scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb cells 60-85

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
