# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_LOT_PAT_ELIG_FLAGS_FINAL_BUSINESS_RULE_CHANGE_VAL_v2` where the May'26 build writes one (see caveats).

**Notebook:** `05` (`scripts/Notebooks/`); KBT 5.

**Family:** APLD (AML base layer)
**Contains:** Per-patient AML eligibility, timing, transplant and intensity flags that gate the AML KPIs (NPS share, SCT, BMB)
**Common analyses:** aml_nps_share, sct_rate, bmb_rate, aml_eligibility

## Grain

One row per patient. (scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb cells 138-311)

## Primary keys or entity keys

PATIENT_GID.

## Row meaning

Which KPI gates the patient passes, plus SCT and intensity attributes.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

Apply the KPI's flag set (see `context/domain/aml_eligibility_flags.md`).

## Business rules

1. Flag rules, KPI mapping and the derivation of the two unstored flags (VEN_POST_DX_FLG, 2M_LF) are in `context/domain/aml_eligibility_flags.md`.
2. ARSENIC_FLG = 1 means no arsenic trioxide (keep).
3. SCT_PX_FLG uses 51 SCT procedure codes from `sx_fact_curated_vw` and `px_fact_curated_vw` (SHA_PTD, ONC); SCT_DX_FLG uses Z94.84 / V42.82 from `dx_fact_curated_vw`; both must be on or after FIRST_DX.

## Join guidance

PATIENT_GID to the combined LoT / RR LoT tables and to the first Dx/Tx table (VEN_START).

## Caveats

1. Continuity flags pass automatically for spans under 6 months and for patients without Venclexta (VEN flags); see the metric caveats.
2. Production pass counts (Aug'26, 84,199 patients): DX_LB 66,568; TX_TXL_MX 80,765; TX_TXL_RX 77,879; TX_TXL_MX_VEN 82,940; TX_TXL_RX_VEN 84,012.
3. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
5. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** scripts/Notebooks/AML_PATIENT_ELIGIBILITY.ipynb cells 138-311

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
