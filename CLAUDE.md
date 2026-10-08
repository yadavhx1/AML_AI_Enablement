# AML base-layer analytics copilot

Brand: Venclexta (venetoclax). Indication: AML. This project contains the AML base layer: patient pool,
treatment claims, SOB/episode, regimen, patient intensity, line of therapy and patient eligibility,
built by five notebooks in `scripts/Notebooks/` on SHA patient-level data, plus the AML NPS dashboard
(legacy IC definition) built by `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated` after the eligibility
notebook (the last base-layer step).

## Required workflow for every analytical question

1. Identify the user's analytical objective and select one primary KBT from `.claude/skills/`.
   Each KBT matches one base-layer notebook stage (TX table, SOB/episode, regimen, intensity/LoT,
   eligibility). NPS dashboard questions have no KBT of their own: use KBT 4 and follow
   `context/metrics/nps_dashboard_legacy.md`.
2. Load that KBT before drafting SQL. Use its method as the step order.
3. Read only the context required by those steps:
   - `context/data/table_index.tsv`, then the exact table profile and compact `analysis_columns.tsv`;
     search the full `columns.tsv` only when a required field is absent from the compact file;
   - `context/metrics/index.tsv`, then the exact metric file;
   - the relevant domain or assumption file;
   - `verified_queries/index.tsv`, then at most the one or two most relevant SQL files.
4. Prefer a verified query when it closely matches. Reuse useful filters, joins, CASE logic,
   cohort construction, grain, and metric formulas when it partially matches.
5. Write the working query, run it, inspect the output, and repair ordinary SQL or data issues in
   the same flow.
6. Validate grain, joins, denominator, period completeness, and reasonableness.
7. Return the answer and disclose material assumptions, data limitations, and any query adaptation.

## No analytical dead ends

Do not interrupt the workflow solely because a period, threshold, metric variant, table version,
cohort detail, or business definition is missing, ambiguous, or conflicting.

Use this priority order:

1. The user's explicit instruction.
2. The convention in the most relevant verified query.
3. The default in the selected KBT.
4. `context/assumptions/defaults.yaml`.
5. A neutral analytical convention.

Proceed with the selected assumption and record it. Ask a follow-up only when the user explicitly
requests a choice before execution or when no executable or proxy path exists after reasonable
fallback attempts. Open items are listed in `context/assumptions/open_items.md`.

A technical failure is not an analytical dead end. Try the documented fallback table or column,
inspect the relevant profile, adapt the SQL, and retry. If execution remains impossible, return the
best working SQL and the exact technical limitation without inventing schema or results.

## KBT selection

- Select one primary KBT based on the pipeline stage that produces the field the answer needs.
- Pool, TX claims, basket, DOS, grace → KBT 1. Episodes, Venclexta start/end → KBT 2.
  Regimen mix → KBT 3. Intensity, backbone, line of therapy, 1L starts → KBT 4.
  Eligibility gates, anchor dates, SCT/BMB cohorts, Dx-to-Tx timing → KBT 5.
  NPS dashboard share (VEN / HMA / other), NPS by HCP, account or segment, Ipsos index → KBT 4 with the
  `nps_dashboard_legacy` metric (method, defaults and QC are in the metric file).
- A KBT may borrow a definition, table, or SQL pattern from another KBT without starting a second
  analytical workflow. A gated KPI by line uses KBT 4 and borrows the KBT 5 gates.
- For a genuinely multi-part request, complete each part sequentially and state the KBT used for each.
- Use `kbts/index.md` when the intended KBT is unclear.

## Latency discipline

- Do not scan the full pack.
- Read the selected KBT and compact indexes first.
- Batch independent context reads together.
- Read no more than two verified-query files before drafting SQL.
- Do not use subagents for context retrieval or query selection.
- Reuse context already loaded in the conversation instead of reopening it.

## Verified-query reuse

- Verified SQL is rendered from the six notebooks (five base-layer, one NPS dashboard) and can be reused.
- Files marked `SQL EQUIVALENT` reconstruct a pandas step; validate them against the persisted table.
- pldlib steps (sob, episode, regimen) carry the call parameters and the SQL pldlib generates
  (`context/domain/pldlib.md`, source in `scripts/pldlib/`); read their persisted tables.
- Correct documented issues in the new working query; do not overwrite the reference file.
- Notebook parameters (table names, suffix, code lists, DOS/grace, backbones, thresholds, dates) are in
  `config/` (`common.yaml` + one YAML per notebook; `config/HARDCODED_INVENTORY.md` maps each to its cell).
  Take parameter values from there rather than re-reading notebook cells.

## Analysis and output rules

- Know the row grain before counting. Patient counts are `COUNT(DISTINCT PATIENT_GID)`.
- Use one table-name suffix per query: `_BUSINESS_RULE_CHANGE_VAL_v2` (the four AML_LOT notebooks) or
  `_BUSINESS_RULE_CHANGE_VAL` (AML_PATIENT_ELIGIBILITY / Aug'26 build). Name the suffix in the answer.
  The NPS dashboard tables carry personal suffixes; take their names from
  `config/nps_dashboard_legacy.yaml`.
- IC Eligible / Ineligible: apply the **legacy rule** (product-only) everywhere unless the user
  explicitly asks for the **new definition** (age + product). Label the new definition when
  used and never mix the two. The LoT build follows `run.intensity_definition` in
  `config/common.yaml` (default `legacy`; `new` writes separate `_NEWDEF` tables).
- Every AML KPI applies `ARSENIC_FLG = 1` plus the KPI's flag set (`AML_KPI_FLAG_SET`), and reports
  the share each flag removes.
- Lines: gap > 90 days or backbone change = new line, except VENCLEXTA <-> HMA. Lines are
  claims-derived, not clinical lines.
- State the data source (SHA), build suffix, period, grain, intensity definition and gates.
- Flag incomplete periods (2-month SHA lag) rather than treating them as market movement.
- Do not expose patient identifiers. Run patient-level logic internally and return aggregated output.
- There is no fixed minimum cell size. Report the base (n) with each cell, flag small-base cuts, and
  roll up when a cut is too thin to interpret.
- Never fabricate query output. If a query was not successfully executed, label the result as SQL or
  methodology only.

## Generated files

- Write every generated file to `outputs/`, never elsewhere in the pack.
  - One folder per analysis: `outputs/<YYYY-MM-DD>_<short-topic>/`. It holds the working SQL that was
    run, the aggregated result tables and charts, and a `README.md` (question, KBT, source, build
    suffix, period, gates, assumptions, `## Provenance` table).
  - `outputs/response_log.md`: append-only provenance log, one entry per answer.
  - Temporary files go in `outputs/_scratch/`; delete them when the analysis is done.
- Build every `.pptx` on the VENCLEXTA template with the kit in `deck/` (rules in `deck/README.md`).
- Files hold aggregates only: no patient identifiers, NPIs or patient-level extracts.
- Do not write outputs into `verified_queries/`, `config/`, `context/`, `scripts/` or `deck/`.

## Final response format

Lead with the requested result or insight. Then include, when relevant:

- KBT and notebook stage used.
- Data source, build suffix and period.
- Material assumptions.
- Material data limitations or query adaptations.

Avoid dumping implementation details unless the user asks for code or methodology.

Do not narrate the working process. No "Let me…" / "I'll check…" preambles, no commentary between
tool calls, no account of query drafts or retries. Work silently and return only the final answer in
the format above plus the provenance table below. Show SQL or method steps only when asked.

## Response provenance (every answer)

End every answer about the repo, its data or its analyses with a `How this answer was generated` table,
and append the same entry to `outputs/response_log.md`. Follow `context/response_provenance.md`.
Rows: prior context reused, skill (KBT), files opened, verified queries, data, execution status,
assumptions (basis + effect) and outputs written. List only what was actually used. This table is the
only allowed account of the working process.
