# Open items - AML base layer

Raised while documenting the base layer and splitting the notebooks. Each one has a non-blocking
default; none of them stops an analysis. Items OI-01 and OI-03 to OI-11 were carried over from the
Venclexta pack (BL-01 to BL-10, renumbered).

| Id | Question | Default |
|---|---|---|
| OI-01 | Patient pool: 2+ AML diagnosis claims (`_v2`, 57,697) or market_code VENC_AML (Aug'26, 84,199)? Which feeds the published KPIs? | `AML_PATIENT_POOL` |
| OI-02 | The four AML_LOT notebooks write `_v2` tables, AML_PATIENT_ELIGIBILITY reads/writes un-suffixed tables. Should AML_PATIENT_ELIGIBILITY read the `_v2` outputs? | `TABLE_SUFFIX_ALIGNMENT` |
| OI-03 | No formal version id for the 2026 AML rules. | `AML_LOT_RULE_VERSION` |
| OI-04 | No check for a competing non-AML primary diagnosis: intended? | None applied |
| OI-05 | New definition (age + line-1 product) cutover date; should it use the whole journey as the business-rules page says? | `AML_INTENSITY_RULE` (legacy rule) |
| OI-06 | The production SCT flag checks 51 of the 110 guide codes: intended? | `AML_SCT_CODE_SET` (51) |
| OI-07 | Continuity flags pass automatically under 6 months and for non-VEN patients (VEN flags); exact-date Mx activity is not ONC-limited; VEN lookback activity omits `market_code='ONC'` (Q-10). Intended? | Use as built; disclose |
| OI-08 | The relapse/remission 1L -> 2L+ refinement (`MABI_AML_PATS_LOT_RR_12M_UPD`) is only in the original team notebook `Patient Eligibility.ipynb` (not in this pack) and reads a legacy diagnosis table. Should it join the split pipeline? | Raw LOT; 1L vs 2L+ from LOT |
| OI-09 | Combination-regimen attribution (e.g. VEN + HMA NPS): which product gets the event? | Backbone; disclose |
| OI-10 | S-DAC / HI-DAC 7-day grace vs L-DAC 60: clinically reviewed? | Use code values |
| OI-11 | VEN_POST_DX_FLG and 2M_LF are not stored. Is the derivation (VEN_START >= FIRST_DX; VEN_START + 2 months <= data cut) right? | Derive as stated |
| OI-12 | ~~The SOB / episode / regimen SQL is not in the supplied material.~~ **Closed 2026-10-07:** `pldlib.egg` added (`scripts/pldlib/`); the generated SQL is rendered in the verified queries. | — |
| OI-14 | The business-rules page (2026-10-07 revision) lists ICD-9 206.00/206.01/207.00/207.20/207.21 as AML codes. The 37-code set used by the pool and FIRST_DX has no 206.x or 207.x. Should they be added? | Code's 37-code set |
| OI-15 | The page no longer documents the SCT/timing flags, the arsenic default, the two VEN continuity flags, the KPI outputs or its own open items. The code still produces them. Removed on purpose, or just trimmed from the page? | Use as built (documented from code) |
| OI-13 | pldlib computes source-of-business labels with the 360-day lookback at every episode start, but the AML line logic ignores them. Should AML NPS use `episode_first_sob` (NTB) rather than the line-1 start? | Line-1 start (`nps_count.md`) |
| OI-16 | The NPS dashboard notebook reads a personal copy of the LoT grouping table (`..._v2_SATEEK`) and writes `_UPDATED_BUSINESS_RULES_v2[_SATEEK]` tables, not the pack build suffix. Which tables are the published dashboard source? | Names in `config/nps_dashboard_legacy.yaml`; state them |
| OI-17 | The NPS summary dates each start by the line END month (`SUMMARY_TIME_BASIS = 'END'`), while `nps_count` and the index/rollup use the line START month. Which basis does the published Summary sheet use? | END, as shipped; disclose, give START on request |
| OI-18 | The SHA and Komodo dictionaries carry claim status (SHA `CLAIM_STATUS_CODE` / `PTD_FINAL_CLAIM`, Komodo `TRANSACTION_RESULT`), but `all_claims_combined_fact_vw` exposes none and the notebooks apply no status filter. Does the view already hold approved / paid claims only? | Assume yes; disclose when counts look high |
