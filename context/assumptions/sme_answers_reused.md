# SME answers reused from the Venclexta pack

The AML pack cites these SME resolutions (September 2026 round, recorded in the Venclexta pack's
SME resolutions file (context/assumptions/sme_resolutions.md in that pack)). Only the ones that bear on the AML base layer are listed.

| Q | Decision |
|---|---|
| Q-01 | `all_claims_combined_fact_vw` refreshes monthly (SHA and KOMODO) with a 2-month lag. No version constant. |
| Q-08 | Activity frequency tables: schema `abv_val_ptd_synd` (fall back to `_work` if not found). The base layer reads `abv_val_ptd_synd_work`. |
| Q-09 | Claims-view market_code values: VENC_CLL, VENC_AML, VENC_CLL_AML_OTHER (singular). Activity tables use 'ONC'. |
| Q-10 | The activity-table `market_code = 'ONC'` filter is required. |
| Q-16 | `aml_lot_group` uses '1L' and '2L+'. |
| Q-22 | SHA `patient_sk` carries the `SHA_PTDONC` source tag on all VAL tables. |
| Q-35 | `source_type` values carry the ' FACT' suffix ('RX FACT', 'PX FACT', ...). |
| Q-51 | SHA lag 2 months (monthly refresh). |
| Q-55 / Q-56 | The processed view applies no enrollment screen and was built on unfiltered history. |
| Q-60 | "Overall #VEN Patients" is the denominator for procedure rates (SCT, BMB) only. |
| Q-61 | Always report both mean and median, with the distribution. |
| Q-62 | No fixed minimum cell size; flag small bases and roll up. |
| Q-63 | Flag any screen removing more than 20% of the cohort. |
| Q-65 | pldlib `sob` is the intended source-of-business classification (in the base layer it is also the episode pre-step). |

Open Venclexta questions cited here: Q-06, Q-28, Q-38, Q-41, Q-67, Q-69 (see the Venclexta pack).
