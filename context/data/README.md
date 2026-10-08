# Data context

Start with `table_index.tsv`. `family = aml_base_layer` tables are written by the five notebooks in `scripts/Notebooks/`
(in pipeline order); `family = aml_nps_dashboard` tables are written by the NPS dashboard notebook (KBT 4, metric `nps_dashboard_legacy`);
`family = source` tables are the SHA views the pipeline reads. For the selected
table, read `profile.md` and `analysis_columns.tsv`; search `columns.tsv` only when a field is not in
the compact set.

`taxonomy.yaml` maps AML base-layer terms and codes.

`source_dictionaries/` holds the vendor layouts of the two raw feeds behind the views: SHA PTD (30
tables) and Komodo (7 tables). It also maps the view columns the base layer uses back to the raw field
in each feed (`view_column_lineage.tsv`). Read it when a question is about what a source field means or
what a feed provides. The base layer never queries these raw tables.

Table-name suffixes: the four AML_LOT notebooks write `..._BUSINESS_RULE_CHANGE_VAL_v2`; AML_PATIENT_ELIGIBILITY reads and
writes `..._BUSINESS_RULE_CHANGE_VAL`. Profiles are filed under the suffix the source pack used; the
`Validation copy` / caveat lines name the other variant.
