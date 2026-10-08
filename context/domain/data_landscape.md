## Data landscape - AML base layer

The AML base layer reads **SHA (Symphony Health) APLD only** (`source_flag = 'SHA_PTD'`, `source_market = 'ONC'`). SHA is a sample, not a census: "Rx data: 65 – 70% data capture", "Hospital and Procedure data: 30 - 40% data"; "SHA is a Switch and collects data from other Switches" and so "Might lead to incomplete longitudinal journeys if patients use different switches". This is why the eligibility flags (KBT 5) exist.

**Data lag and refresh cadence (SME-confirmed, Q-51 and Q-01).** Use these values to decide which
recent period is incomplete:

| Source | Data lag | Refresh |
|---|---|---|
| SHA (incl. `all_claims_combined_fact_vw`, SHA and KOMODO) | 2 months — e.g. a Sep'26 refresh carries SHA data ending Jul'26 | Monthly |
| GPO (incl. the `_0602_` GPO/EMR claims and LoT tables) | 2 months | Monthly |
| Optum / Truven | 1 month (onboarding notes; not restated by the SME) | Monthly |

The earlier documents disagreed (SP-SD_Latest.pptx gave SP/SD 1 week; IQVIA_Latest.pptx slide 11
gave SHA and IQVIA 1 month). The SME answer supersedes them.

**Patient keys.** SHA patients carry the source prefix in `patient_sk`, e.g. `217656241SHA_PTDONC`;
the `SHA_PTDONC` suffix is the source tag on every VAL table. Strip it with
`REPLACE(patient_sk,'SHA_PTDONC','')` to join across VAL tables, including `dx_fact_vw` (SME Q-22).

**Schemas.** The Rx and Mx activity frequency tables live in `abv_val_ptd_synd`, which the SME
confirmed is correct and should be used across all code (Q-08). Earlier SHA NPS queries used
`abv_val_ptd_synd_work`; fall back to it only if the object is not found, and disclose the fallback. `CL_NPP_TRANSACTION` lives in the
`NPP` schema — `HCP_CONS_PROD.NPP.CL_NPP_TRANSACTION`, beside `CL_NPP_AGGREGATED` (SME Q-67).

**Raw feed layouts.** `context/data/source_dictionaries/` holds the SHA PTD and Komodo data dictionaries.
Points that matter for AML:
- SHA birth year is adjusted for patients aged 76 and over.
- The view reads only the first-position diagnosis.
- Neither the view nor the notebooks filter on claim status (SHA `CLAIM_STATUS_CODE`, Komodo
  `TRANSACTION_RESULT`).
- Medical claims have no days supply in either feed.

**Claim types**, verbatim: "Rx - Retail prescriptions · Mx – Medical claim · Hx – Hospital claim ·
Px – Procedure claim · Sx – Surgery claim". Medical claims arrive on "CMS-1450 / CMS-1500 form / 837
billing file" and pharmacy claims on the "Standard NCPDP layout".
*(Notes_Data Sources_1.pdf · page 3; AML SHA Business Rules Guide V5.pptx · slides 5–6)*

**One derivation worth knowing up front:** "SHA does not provide Mx activity table, it is derived by
combining Px, Sx and Dx claims. Mx activity table contains Market (ONC) claims only." So medical
activity outside oncology cannot establish patient eligibility.
*(AML SHA Business Rules Guide V5.pptx · slide 17)*

**One derivation worth knowing up front:** "SHA does not provide Mx activity table, it is derived by
combining Px, Sx and Dx claims. Mx activity table contains Market (ONC) claims only." So medical
activity outside oncology cannot establish patient eligibility.
*(AML SHA Business Rules Guide V5.pptx · slide 17)*

## Pipeline

```
all_claims_combined_fact_vw + dx_fact_curated_vw (SHA_PTD, ONC)
  -> 01 patient pool, TX table, DOS + grace
  -> 02 pldlib sob -> episode
  -> 03 pldlib regimen
  -> 04 patient intensity (legacy rule) -> IC_INELIG / IC_ELIG LoT -> combined LoT -> LoT grouping -> new definition
  -> 05 exact-date activity -> first Dx/Tx -> eligibility flags -> final flags table
  -> 06 NPS dashboard (legacy IC definition): line backbone -> initiating HCP -> account / segments
        -> Power BI dataset -> NPS by LoT x month, Ipsos index, account rollup
  -> other AML KPIs (SCT, BMB, LoT mix) - not built in this pack
```

The shared library is the team's `pldlib`, imported as `stencil`: "Stencil library provides the SOB /
episode / regimen builders". The library and its source are in `scripts/pldlib/`; what each function computes is in `pldlib.md`. The platform is Spark SQL on YARN from Jupyter (HUE/Impala data lake).
