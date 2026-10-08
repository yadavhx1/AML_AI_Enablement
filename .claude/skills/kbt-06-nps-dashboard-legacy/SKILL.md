---
name: kbt-06-nps-dashboard-legacy
description: Use for AML NPS dashboard questions on the legacy IC eligible / ineligible definition - Venclexta, HMA or other-novel-agent new patient start volume and share by line of therapy and month, the published IC Ineligible 1L NPS share, the line-level backbone picked from the product rank lists, the initiating HCP (NPI) of a start, account type or Academic / Community group, HCP decile or segment, the Power BI dataset, or the Ipsos reported-versus-SHA index (`AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated`).
user-invocable: true
---


# KBT 6 - AML NPS dashboard, legacy IC definition (AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated)

## Analytical intent

Use this KBT when the answer is a dashboard NPS figure: VEN / HMA / other share of new patient starts by
month, line or slice, starts by initiating HCP, account type, decile or segment, or the reported (Ipsos)
versus SHA index. It runs after the full base layer (after AML_PATIENT_ELIGIBILITY) and reads the LoT
grouping, the legacy-rule cohort (KBT 4) and the final eligibility flags (KBT 5). Use KBT 4 for line construction, intensity and the line-change
backbone, and KBT 5 for the gates themselves.

Notebook: `scripts/Notebooks/AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb`.

## Method

1. Lines: one row per patient × LOT from `MABI_AML_PATS_LOT_GROUPING_TBL_*` (every line, not only 1L),
   with the cohort's `PATIENT_INTENSITY_GROUP` (legacy rule by default; the new definition in a
   `_NEWDEF` build).
2. Legacy backbone (the "legacy definition"): the highest-ranked product of the whole line
   (`LOT_REGIMEN_GROUP`) on the IC_ELIG list (28 products, S-DAC first) or the IC_INELIG list (11,
   VENCLEXTA first). Any intensity other than IC_ELIG, including no cohort row, uses the IC_INELIG list.
   Products are named (AZACITIDINE, not HMA). None listed → `UNKNOWN`. The lists equal the new-definition rank
   lists (`config/nps_dashboard_legacy.yaml` `line_backbone`). This is not the KBT 4 `BACKBONE`, which
   is per regimen and groups HMAs.
3. Initiating HCP: the NPI on the first backbone-product claim inside the line dates (claim date ASC,
   NPI DESC, claim id); ONC / SHA_PTD / VENC_AML claims, no FILGRASTIM, NPI not null. Mapped to the
   Abbott customer id through `CUSTOMER_TBL`.
4. Account subtype per HCP: ONH2 HCI-HCP affiliations, Reltio for HCPs without one, joined to
   `heme_account`; the lowest-ranked subtype wins (Elite Oncology Center 1 … DOD 8). The rollup groups
   Elite + Academic Teaching Hospital as Academic and everything else as Community.
5. Segments: UNI_DECILE and ABOVE_BRAND_SEGMENT, plus EXECUTION_SEGMENT from the GNE `_BKP` table, all
   on NPI. Missing values become `Not Available`.
6. Backbone group: VENCLEXTA; AZACITIDINE / DECITABINE / ONUREG / INQOVI = HMA; everything else
   (UNKNOWN too) = OTHER NOVEL AGENTS.
7. Summary: DISTINCT patient × line starts by DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT, LOT and
   month. The flags are LEFT-joined; unmatched patients get -1 / `Not Available`. VEN / HMA / other
   share = group starts / all starts in the slice and month. The month is the line END month as
   shipped (`SUMMARY_TIME_BASIS = 'END'`, OI-17), from 2019.
8. Published NPS share slice: `DX_LB_ELIG_FLG = 1`, `DX_TX_DIFF_FLG = 1`, `PATIENT_COHORT = 'IC_INELIG'`,
   `LOT = 1`. Sum the months to semesters and recompute the share; never average monthly shares.
9. Index and rollup: reported VEN and total NPS per month from the repository next to SHA counts by month
   of line START. These count every line and both intensities without gates.
10. Validate: patient count equals the grouping table; `UNKNOWN` backbones and NULL `NPI_REGIMEN` on
    LOT = 1 counted (cell 35); unmatched-flag starts counted; month volumes sum to the published
    semesters for the published slice; LOT volume falls steeply after 1L.

## Working defaults

- Slice: the published slice (step 8) unless the question names another. Name the slice in the answer.
- IC definition: legacy rule unless the user explicitly asks for the new definition. A new-definition
  dashboard needs the full base layer run with `run.intensity_definition: new`. It then reads and
  writes `_NEWDEF` tables, and the published legacy dashboard tables are untouched.
- Time basis: line END month, as shipped. Say so, and give the START-month figure if the user means
  start (`nps_count.md` uses the line-1 start).
- Arsenic: the notebook does not read ARSENIC_FLG. The legacy rule puts arsenic patients in IC_ELIG, so the
  IC_INELIG slice is unaffected. Apply `ARSENIC_FLG = 1` from KBT 5 for IC_ELIG or all-intensity cuts.
- Tables: read the names in `config/nps_dashboard_legacy.yaml` (personal `_SATEEK` suffixes, OI-16).
  Lines are `_v2`, flags are the un-suffixed Aug'26 build (OI-02).
- Combination lines attribute to the legacy backbone (OI-09).
- Small cells: report n and roll months up to semesters when thin.

## Context to read

- `context/metrics/nps_dashboard_legacy.md`, `nps_count.md`
- `context/domain/aml_eligibility_flags.md` (DX_LB_ELIG_FLG, DX_TX_DIFF_FLG, PATIENT_COHORT)
- `context/domain/reference_codes_and_mappings.md` (rank lists, HMA products)
- Profiles for the dashboard, summary and HCP tables (`family = aml_nps_dashboard` in
  `context/data/table_index.tsv`)
- `context/data/source_dictionaries/` (README points 6 and 4, `view_column_lineage.tsv` row
  `mdm_npi_number`) only when the question is about HCP attribution:
  - why starts have no NPI (SHA NPI is an optional field on the practitioner table; Komodo has
    `PRESCRIBER_NPI` with a confidence flag);
  - whether rejected or reversed claims can drive an attribution.
  Never query the raw tables.

## Verified-query candidates

- `AML_NPS_LINE_BACKBONE` (SQL equivalent of the pandas step), `AML_NPS_REG_NPI_ACI`,
  `AML_NPS_ACCOUNT_TYPE_GROUP`, `AML_NPS_HCP_INFO_MAP`, `AML_NPS_DASH_PBI_DATA`,
  `AML_NPS_LOT_MONTH_SUMMARY`, `AML_NPS_IPSOS_INDEX`, `AML_NPS_ACCT_MONTH_ROLLUP`.

## Minimum QC

- The slice (flags, cohort, LOT) and the time basis (start or end month) are named.
- The share is recomputed from volumes for every roll-up.
- Totals are not summed across slices or flag values.
- The legacy line backbone is not mixed with the KBT 4 regimen backbone in one figure.
- Index and rollup figures are labelled as ungated, all lines.


## Output contract

Return the requested result first. State the data source, slice, line, time basis, period, input table
names and material assumptions. Keep patient identifiers and NPIs out of the response; report HCP results
at account, decile or segment level.
