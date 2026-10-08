# Analysis outputs

Every file generated while answering a question goes here, never elsewhere in the pack.

```
outputs/
  <YYYY-MM-DD>_<short-topic>/   one folder per analysis
    README.md                   question, KBT, data source, build suffix, period, gates, assumptions
    *.sql                       the working SQL actually run
    *.csv / *.xlsx / *.png      aggregated results and charts
  _scratch/                     temporary files; safe to delete at any time
```

- Folder name: run date plus a short kebab-case topic, e.g. `2026-10-08_ven-nps-share-1l`.
- Aggregates only. No patient identifiers, NPIs or patient-level extracts in any file.
- Never overwrite a reference file (`verified_queries/`, `config/`, `context/`) with an output.
- Notebook exports (e.g. the NPS dashboard `.xlsx` / `index_map_*.csv`) are written to the notebook's
  working directory; move them here, or set the export path to this folder, after the run.
- `tools/validate_pack.py` skips this folder. Clear `_scratch/` before sharing or zipping the pack.
