# Verified-query library

One SQL reference per AML base-layer and NPS dashboard step, rendered from the six notebooks in
`scripts/Notebooks/` with their table-name globals resolved. Search `index.tsv` by KBT,
question, table, metric or reusable component. Read at most the one or two closest files before
drafting SQL.

Three kinds of reference:

- **Team SQL** - the notebook's own statement, with `CREATE TABLE ... AS (` removed so it only reads.
- **pldlib SQL** - `sob`, `episode` and `regimen` are pldlib library calls. The file records the exact
  call parameters as comments, followed by the SQL pldlib generates for them, rendered from the library
  source in `scripts/pldlib/`. This is the statement the notebook runs.
- **SQL equivalents** - steps the notebooks do in pandas or PySpark (LoT regimen grouping, the
  continuity-flag interval check, the NPS line backbone, the NPS flag join). These are labelled `SQL EQUIVALENT` in `KNOWN_ISSUE`; they are reconstructions,
  not team code. Validate them against the published table before relying on them.

Temp views the notebooks create in one cell and read in another are inlined as CTEs. The four AML_LOT notebooks
write `_BUSINESS_RULE_CHANGE_VAL_v2` tables; AML_PATIENT_ELIGIBILITY reads and writes the un-suffixed
`_BUSINESS_RULE_CHANGE_VAL` tables (open item OI-02). Keep the suffix consistent in a working query. The NPS dashboard queries (`kbt-06/`) use the
notebook's personal table names (OI-16).
