# Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_HCP_AFFILIATIONS

Validation copy: `Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_HCP_AFFILIATIONS_v2` where the May'26 build writes one (see caveats).

**Notebook:** none of the five pack notebooks; built only by the original team notebook `Patient Eligibility.ipynb` (not part of this pack; kept in the source `base_layer/` folder).

**Family:** APLD (AML base layer)
**Contains:** NPIs on AML treatment claims mapped to Abbott customer ID, child account and site-of-care group
**Common analyses:** aml_site_of_care, aml_hcp_account_mapping

## Grain

One row per NPI x ABBOTT_CUSTOMER_ID x CHILD_ABBOTT_ACCOUNT_ID x site-of-care group (multiple affiliations retained). (original team notebook Patient Eligibility.ipynb cells 321-329)

## Primary keys or entity keys

NPI_NUMBER + CHILD_ABBOTT_ACCOUNT_ID.

## Row meaning

An AML treating prescriber's account affiliation and site of care.

## Refresh

Rebuilt by the AML base-layer notebook each cycle (DROP + CREATE). The Aug'26 run read SHA data through
2026-06-30. State the build suffix and data cut in the run header.

## Mandatory filters

None; NPIs without a customer ID keep NULL attributes.

## Business rules

1. NPI -> ABBOTT_CUSTOMER_ID via `ABV_DDS_SYND.CUSTOMER_TBL` (`DDS_ACTIVE_FLAG='Y'`).
2. Child account from `ABV_ADS_SYND.DIM_ACCOUNT_AFFILIATIONS_TBL` (`UNIVERSE_NAME='1VIEW_ONCOLOGY'`, `SALES_FORCE_CODE='ONH2'`, `DDS_ACTIVE_FLAG='Y'`), else Reltio `ABV_MHCD_SYND.MHCD_RLTN_ALL_ORG_CUSTOMR_WKLY_TBL` (`ADS_ACTIVE_FLAG='Y'`, `VALUATION_INCLUDE_FLAG='Y'`) for customers not in the first.
3. Site of care: highest-priority `heme_account` FINAL_ACCOUNT_TYPE_2 per HCP (Elite Oncology Center > Academic Teaching Hospital > IDN - Academic Affiliated > IDN - Community Affiliated > Corporate > Other Community > VA > DOD > NULL), grouped Academic / Academic Satellite / Community / Federal / Not Available; Community -> Larger Community when max child-account decile >= 8 (`MABI_AML_CHILD_ACCOUNT_DECILE`), else Smaller Community.

## Join guidance

NPI_NUMBER to the AML treatment claims NPI; ABBOTT_CUSTOMER_ID to the HCP tables in the HCP/account KBT of the Venclexta pack.

## Caveats

1. Not built in the `_v2` notebook. Upstream `heme_account` (COE-uploaded) and `MABI_AML_CHILD_ACCOUNT_DECILE` are not cataloged.
2. Rows multiply when an HCP has several child accounts; deduplicate before counting HCPs.
3. Two builds exist: the Aug'26 build writes the `_BUSINESS_RULE_CHANGE_VAL` suffix (84,199 patients, pool = `market_code='VENC_AML'`); the May'26 validation build writes `_BUSINESS_RULE_CHANGE_VAL_v2` (57,697 patients, pool = 2+ AML diagnosis claims). It is not stated which one is published; name the suffix you read (see `context/domain/key_concepts.md`, AML base layer).
4. PATIENT_GID keeps the `SHA_PTDONC` suffix (it is `patient_sk` renamed). Join to VAL tables on `patient_sk` directly, or strip the suffix on both sides.
5. Patient identifiers never leave the working query; return aggregates only.

## Pipeline and lineage

AML base layer: claims -> DOS/grace -> stencil sob/episode -> regimen -> intensity -> LoT -> RR
refinement -> first Dx/Tx -> eligibility flags -> HCP affiliations. See
`context/domain/key_concepts.md` (AML base layer).

**Produced by:** original team notebook Patient Eligibility.ipynb cells 321-329

**Source document:** AML_Base_Business_Rule.html; the notebooks above (code wins where they differ).
