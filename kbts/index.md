# KBT index

Select one primary KBT based on the pipeline stage that produces the field the answer needs. The descriptions below are also the automatic skill-selection descriptions used by Claude Code.

| KBT | Skill | Use for |
|---:|---|---|
| 1 | `/kbt-01-tx-table-build` | Use for AML base-layer questions about the patient pool (2+ AML diagnoses), the AML treatment-claims (TX) table, the 28-product AML market basket, product code lookups, days of supply, grace periods, Filgrastim exclusion, or how a claim becomes a FINAL_PRODUCT_NAME (`AML_LOT_TX_TABLE`). |
| 2 | `/kbt-02-sob-episode` | Use for AML base-layer questions about the pldlib SOB step, same-day claim de-duplication, the 360-day lookback, episode construction, episode start/end dates, DOS-plus-grace joining, episode length, persistency on an AML product, or Venclexta episode start/end (`AML_LOT_SOB_EPISODE`). |
| 3 | `/kbt-03-regimen` | Use for AML base-layer questions about regimens, which products are given together, combination regimens such as Venclexta plus azacitidine, regimen start and end dates, regimen counts or regimen mix, built by the pldlib regimen step from episodes (`AML_LOT_REGIMEN`). |
| 4 | `/kbt-04-patient-intensity-lot` | Use for AML base-layer questions about IC eligible versus IC ineligible patient intensity, the backbone hierarchy, backbone product, line of therapy (LoT) assignment, the 90-day gap rule, the Venclexta-HMA same-line exception, line distribution, products per line, the age-plus-product new intensity definition, or AML new patient starts by line (`AML_LOT_PATIENT_INTENSITY_LOT`). |
| 5 | `/kbt-05-patient-eligibility` | Use for AML base-layer questions about patient eligibility flags, diagnosis lookback, Mx/Rx activity continuity, Venclexta-anchored lookback or continuity, first diagnosis and first treatment dates, time from diagnosis to treatment, arsenic/APL exclusion, stem cell transplant flags, SCT or BMB rate cohorts, or which patients a KPI may count (`AML_PATIENT_ELIGIBILITY`). |

There is no NPS KBT. NPS is covered by two metrics in `context/metrics/`: `nps_count` (line-1 new patient
starts) and `nps_dashboard_legacy` (the dashboard: VEN / HMA / other share by line and month, line backbone,
initiating HCP, account, decile, segment, Power BI dataset, Ipsos index). Both run under KBT 4.

## Selection rules

- Pool, basket, TX claims, DOS and grace → KBT 1.
- Episode dates, episode length, Venclexta start/end, same-day de-duplication → KBT 2.
- Regimen mix, combinations, regimen counts → KBT 3.
- IC Eligible / Ineligible, backbone, line of therapy, line distribution, 1L starts, legacy rule vs new definition → KBT 4.
- Eligibility gates, anchor dates, diagnosis-to-treatment timing, arsenic, SCT/BMB cohorts → KBT 5.
- NPS dashboard figures: VEN / HMA / other share by month or line, the published IC Ineligible 1L share,
  NPS by initiating HCP, account type, decile or segment, the Power BI dataset, the Ipsos index → KBT 4,
  following `context/metrics/nps_dashboard_legacy.md` (its method, defaults and QC replace a separate KBT).
- A gated KPI by line or intensity built from the base layer (e.g. NPS share by regimen backbone with
  the published gates) uses KBT 4 and borrows the gates from KBT 5. A question about the dashboard
  figure itself, or that needs the legacy line backbone or the HCP / account attributes, also uses KBT 4
  with the `nps_dashboard_legacy` metric. An SCT or BMB rate uses KBT 5 and borrows lines from KBT 4.
- A question about why a number changed after the 2026 rule change uses the KBT of the stage whose rule
  changed (pool → 1, consolidation/backbone/line → 4, flags → 5).
