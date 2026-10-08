# Metrics

Search `index.tsv` by metric name or alias, then read only the linked metric file. A metric with
multiple variants or incomplete documentation still remains executable: apply the selected KBT and
assumption policy, calculate the most appropriate documented variant, and disclose it.

This folder holds the reported KPIs only: NPS (`nps_count`, `nps_dashboard_legacy`), SCT rate and BMB
rate. The definitions they build on are in `context/domain/`: `aml_eligibility_flags.md`,
`line_of_therapy.md`, `patient_intensity.md`, `patient_pool.md`, `days_on_therapy.md`,
`time_to_treatment.md`.
