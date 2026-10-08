# Analysis outputs

Every file generated while answering a question goes here, never elsewhere in the pack.

```
outputs/
  response_log.md               append-only provenance log, one table per answer
  <YYYY-MM-DD>_<short-topic>/   one folder per analysis
    README.md                   question, KBT, data source, build suffix, period, gates, assumptions,
                                ## Provenance table
    *.sql                       the working SQL actually run
    *.csv / *.xlsx / *.png      aggregated results and charts
    *.pptx                      decks, built on the VENCLEXTA template with deck/ (see deck/README.md)
  _scratch/                     temporary files; safe to delete at any time
```

- Folder name: run date plus a short kebab-case topic, e.g. `2026-10-08_ven-nps-share-1l`.
- `response_log.md` records how each answer was produced: prior context reused, skill, files opened,
  verified queries, data, execution status, assumptions and outputs. The format is in
  `context/response_provenance.md`. Append new entries only; never edit past ones.
- Aggregates only. No patient identifiers, NPIs or patient-level extracts in any file.
- Never overwrite a reference file (`verified_queries/`, `config/`, `context/`) with an output.
- Notebook exports (e.g. the NPS dashboard `.xlsx` / `index_map_*.csv`) are written to the notebook's
  working directory; move them here, or set the export path to this folder, after the run.
- `tools/validate_pack.py` skips this folder. Clear `_scratch/` before sharing or zipping the pack.
