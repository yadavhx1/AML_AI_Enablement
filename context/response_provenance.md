# Response provenance log

Every answer to a question about this repo, its data or its analyses ends with a provenance table
that shows how the answer was produced. The same table goes into the response log file. The only
exception is a pure acknowledgement with no content, such as "ok, done".

## Where it goes

1. **In the response.** Add a final section titled `How this answer was generated` that holds the table.
   It comes after the answer, assumptions and limitations, so the answer still comes first.
2. **In the log file.** Append one entry per answer to `outputs/response_log.md`, newest last. Create the
   file with the heading `# Response log` if it does not exist. Never rewrite or delete past entries.
3. **In the analysis folder.** When the answer creates an `outputs/<YYYY-MM-DD>_<topic>/` folder, its
   `README.md` also carries the table under `## Provenance`.

Log entry layout:

```
## <YYYY-MM-DD HH:MM> | <short question, max ~15 words>

| Type | Item | How it was used |
|---|---|---|
| ... | ... | ... |
```

## Table columns

| Column | Content |
|---|---|
| Type | One of the row types below |
| Item | File path (repo-relative), skill name, table name, or short assumption statement |
| How it was used | What it provided, or for an assumption its basis and its effect on the result |

## Row types (in this order)

| Type | What to list |
|---|---|
| Prior context | What was already available before this answer and was reused without re-reading: `CLAUDE.md` (always loaded), earlier turns in the conversation, files read in earlier turns, the user's IDE selection or open file. Name each item. |
| Skill | The KBT skill loaded (`kbt-0N-...`), or `none`, with the reason. Name any borrowed KBT (e.g. KBT 5 gates). |
| File | Each context, config, metric, domain, assumption or script file actually opened for this answer. |
| Verified query | Each `verified_queries/` file used, with `as-is`, `adapted` or `pattern only`. |
| Data | Each table queried, with its build suffix. |
| Execution | Whether the SQL or code was run (`executed`, `failed: <reason>`, or `not run - SQL/method only`). |
| Assumption | Each assumption made. Give its basis by priority level: `user`, `verified query`, `KBT default`, `defaults.yaml`, `neutral convention`. Also give its effect on the result. |
| Output | Each file written to `outputs/`. |

Leave out a row type that does not apply. Do not add an empty row for it.

## Rules

- **Truthful only.** List only files, skills and queries that were actually opened or used in this answer.
  Do not list files to look thorough, and do not leave out a file that shaped the answer. Context reused
  from earlier turns goes under `Prior context`, not `File`.
- **Assumptions are complete.** Every assumption that could change a number, cohort, period or definition
  gets a row, including ones already stated in the answer body.
- **No identifiers.** No patient identifiers, NPIs or patient-level values in the table or the log.
- **Short.** One line per row. Paths, not file contents.
- The table is the only allowed account of the working process. The ban on narration in `CLAUDE.md`
  still applies to everything else.
