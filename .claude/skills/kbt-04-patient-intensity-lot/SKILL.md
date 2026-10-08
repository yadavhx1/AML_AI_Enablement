---
name: kbt-04-patient-intensity-lot
description: Use for AML base-layer questions about IC eligible versus IC ineligible patient intensity, the backbone hierarchy, backbone product, line of therapy (LoT) assignment, the 90-day gap rule, the Venclexta-HMA same-line exception, line distribution, products per line, the age-plus-product new intensity definition, AML new patient starts (NPS) by line, or the AML NPS dashboard - VEN / HMA / other NPS share by line and month, the line-level legacy backbone, NPS by initiating HCP, account, decile or segment, the Power BI dataset or the Ipsos index (`AML_LOT_PATIENT_INTENSITY_LOT`; dashboard method in the `nps_dashboard_legacy` metric).
user-invocable: true
---


# KBT 4 - Patient intensity and line of therapy (AML_LOT_PATIENT_INTENSITY_LOT)

## Analytical intent

Use this KBT when the output depends on patient intensity (IC_ELIG / IC_INELIG), the backbone, or the
line of therapy: line distribution, regimen or product by line, 1L starts, time on line, or why a line
changed. Use KBT 3 for regimen mix without lines and KBT 5 for eligibility gates.

NPS questions also run here. Line-1 starts follow `context/metrics/nps_count.md` (step 7). NPS dashboard
figures (share by line and month, legacy line backbone, HCP / account / segment, Ipsos index) follow the
method, defaults and QC in `context/metrics/nps_dashboard_legacy.md`, which reads this KBT's LoT grouping
table and the KBT 5 flags.

Notebook: `scripts/Notebooks/AML_LOT_PATIENT_INTENSITY_LOT.ipynb`.

## Method

1. Choose the IC Eligible / IC Ineligible definition. **Use the legacy rule unless the user explicitly
   asks for the new definition**, and name the one used.
   - **Legacy rule** (production, default): a patient is `IC_ELIG` if any regimen in the journey
     contains an IC-Eligible-only product, otherwise `IC_INELIG`. It is decided once per patient
     (`PATIENT_INTENSITY_GROUP`). INQOVI and ONUREG count as IC-Ineligible products.
   - **New definition** (age + product): see step 6.
2. Backbone: highest-ranked product in the regimen on the patient's hierarchy. IC_INELIG has 11 products
   (no Rydapt or Mylotarg). IC_ELIG has 28, with S-DAC/HI-DAC grouped. AZACITIDINE, DECITABINE,
   INQOVI and ONUREG resolve to `HMA` in both.
3. Line change: first regimen → line 1. Gap since the previous regimen's end > 90 days → new line.
   Gap ≤ 90 days: same backbone → same line; VENCLEXTA ↔ HMA in either direction → same line; any other
   backbone change → new line. LOT = running sum of line changes.
4. All regimens are kept. There is no consolidation and no minimum-length filter.
5. Combined LoT (`MABI_AML_PATS_COMB_LOT_TBL_*`): union of both intensity groups, with
   `TYPE` = the run's intensity class. Line bounds: MIN regimen start / MAX regimen end within patient ×
   LOT, or read `MABI_AML_PATS_LOT_GROUPING_TBL_*`, which also carries `LOT_REGIMEN_GROUP` (sorted
   product union).
6. New definition (age + product): evaluated on the legacy line-1 product group.
   - Any IC-Eligible product → IC_ELIG.
   - All products in {AZACITIDINE, DECITABINE, ONUREG, INQOVI, TIBSOVO, IDHIFA} → IC_INELIG.
   - Otherwise age at first diagnosis ≤ 65 → IC_ELIG, > 65 → IC_INELIG. No age → IC_INELIG.
   - Use it only when asked, and label it "new definition".
   - Which table to read: in a legacy build the class is `PATIENT_INTENSITY_UPDATED` in
     `PATIENT_INTENSITY_BASED_ON_AGE_N_PRODUCT_*`; the lines themselves are still legacy-rule lines. For
     lines built with the new definition, read the `_NEWDEF` tables of a new-definition run (step 9).
7. AML new patient starts = line-1 start (`LOT = 1`, REG_NUM = 1 regimen of line 1), counted once per
   patient. Apply the KBT 5 gates when the question is a published KPI.
8. Validate: no NULL backbones; LOT starts at 1 for every patient; patient count reconciles to the
   regimen table; IC_ELIG + IC_INELIG = total.
9. Running the notebook with a chosen definition: set `run.intensity_definition` in
   `config/common.yaml` (`legacy`, the default, or `new`), then run `AML_LOT_PATIENT_INTENSITY_LOT`.
   `AML_PATIENT_ELIGIBILITY` and the NPS dashboard pick up the same setting.
   - A `new` run builds legacy lines first (`_P1LEGACY` scratch tables), classifies patients with the
     new definition from that line 1, then rebuilds the lines.
   - It writes `_NEWDEF` tables, so legacy tables and published figures are never overwritten.
   - Only change the setting when the user explicitly asks for a new-definition build.

## Working defaults

- Intensity: legacy rule, everywhere, unless the user explicitly asks for the new definition
  (`AML_INTENSITY_RULE`; build setting `run.intensity_definition: legacy`).
- Never mix the two definitions in one figure or trend.
- Line group: 1L vs 2L+ from LOT (this build has no relapse/remission refinement; see OI-08).
- Exclude arsenic (APL) patients via KBT 5 `ARSENIC_FLG = 1` for any KPI.
- Rule version: 2026 AML base layer (`AML_LOT_RULE_VERSION`); flag trends crossing it.
- Small cells: report n and roll up when thin.

## Context to read

- `context/domain/reference_codes_and_mappings.md` (backbone hierarchies, intensity lists)
- `context/domain/key_concepts.md` (LoT rules)
- `context/domain/rule_change_history.md`
- `context/domain/line_of_therapy.md`, `patient_intensity.md`, `days_on_therapy.md`
- `context/metrics/nps_count.md`; `context/metrics/nps_dashboard_legacy.md` for dashboard figures
- Profiles for the cohort, IC LoT, combined LoT, grouping and new-definition tables

## Verified-query candidates

- `AML_PATIENT_INTENSITY_RULE_A`, `AML_LOT_IC_INELIG`, `AML_LOT_IC_ELIG`, `AML_COMBINED_LOT`,
  `AML_LOT_REGIMEN_GROUPING` (SQL equivalent of the pandas step), `AML_RULE_B_INPUTS`.
- NPS dashboard (`verified_queries/nps_dashboard/`): `AML_NPS_LINE_BACKBONE`, `AML_NPS_REG_NPI_ACI`,
  `AML_NPS_ACCOUNT_TYPE_GROUP`, `AML_NPS_HCP_INFO_MAP`, `AML_NPS_DASH_PBI_DATA`,
  `AML_NPS_LOT_MONTH_SUMMARY`, `AML_NPS_IPSOS_INDEX`, `AML_NPS_ACCT_MONTH_ROLLUP`.

## Minimum QC

- The intensity definition (legacy rule or new definition) is named.
- The VEN ↔ HMA exception is applied in both directions.
- Lines are counted at patient × LOT grain.
- The rule-version caveat is included when comparing with pre-2026 figures.


## Output contract

Return the requested result first. State the data source, grain, intensity definition (legacy rule or
new definition), line definition, period, build suffix and material assumptions. Keep patient
identifiers out of the response.
End with the `How this answer was generated` provenance table and append it to `outputs/response_log.md` (`context/response_provenance.md`).
