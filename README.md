# AML base-layer KBT-first analytics context pack **[View Business Rules](https://yadavhx1.github.io/AML_AI_Enablement/AML_Base_Business_Rule.html)**

This pack is for Claude Code in VS Code. It follows the layout of the Venclexta KBT-first pack and
covers the AML base layer and the AML NPS dashboard: six KBTs, one per notebook, with targeted context
and reusable SQL.

## Runtime flow

1. Understand the analytical question.
2. Select one primary KBT from `.claude/skills/` (the notebook stage that produces the needed field).
3. Follow the analytical steps in that KBT.
4. Read only the table, column, metric, domain, and assumption context needed for those steps.
5. Check `verified_queries/index.tsv` and reuse a relevant query fully or partially.
6. Write and run the working SQL.
7. Resolve ambiguity with a documented assumption instead of interrupting the analysis.
8. Validate the result and return the answer with material assumptions.

## How to use

1. Open the folder `aml_context_pack_kbt` itself in VS Code.
2. Start Claude Code from that folder.
3. Ask the analytical question in natural language.

Claude loads the relevant KBT skill automatically. For testing, invoke one explicitly, for example
`/kbt-04-patient-intensity-lot`.

## KBTs and notebooks

| KBT | Skill | Notebook (`scripts/Notebooks/`) |
|---:|---|---|
| 1 | `kbt-01-tx-table-build` | `AML_LOT_TX_TABLE.ipynb` |
| 2 | `kbt-02-sob-episode` | `AML_LOT_SOB_EPISODE.ipynb` |
| 3 | `kbt-03-regimen` | `AML_LOT_REGIMEN.ipynb` |
| 4 | `kbt-04-patient-intensity-lot` | `AML_LOT_PATIENT_INTENSITY_LOT.ipynb` |
| 5 | `kbt-05-patient-eligibility` | `AML_PATIENT_ELIGIBILITY.ipynb` |
| 6 | `kbt-06-nps-dashboard-legacy` | `AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb` (runs after KBT 5, the last base-layer step) |

## Important folders

- `.claude/skills/`: KBT methodology, loaded only when relevant.
- `context/data/table_index.tsv`: compact table directory (base-layer outputs in pipeline order, then
  source views).
- `context/data/tables/`: one profile, compact analysis-column file, and complete column file per table.
- `context/data/source_dictionaries/`: SHA PTD and Komodo raw-feed data dictionaries, plus view-to-raw
  column lineage.
- `context/metrics/`: the reported KPIs only (NPS: `nps_count`, `nps_dashboard_legacy`; `sct_rate`;
  `bmb_rate`), indexed in `index.tsv`. Building-block definitions (eligibility flags, line of therapy,
  intensity, patient pool, days on therapy, time to treatment) are in `context/domain/`.
- `context/domain/`: brand, data landscape, key concepts, AML code sets, and rule history.
- `context/assumptions/`: defaults, policy, open items, and the SME answers reused from the Venclexta pack.
- `verified_queries/`: one SQL reference per pipeline step, plus a searchable index.
- `workflows/`: the base-layer refresh procedure (the five notebooks in run order) and the separate
  NPS dashboard refresh (`aml_nps_dashboard_legacy.md`).
- `evals/`: example questions and expected KBT selection.
- `tools/validate_pack.py`: structural validation for the pack.
- `outputs/`: every file generated during an analysis (one dated folder per analysis; temporary files
  in `outputs/_scratch/`). Aggregates only; skipped by the validator.
- `AML_Base_Business_Rule.html`: the AML base-layer business-rules page (current revision, 2026-10-07).
- `scripts/`: the five base-layer notebooks and the NPS dashboard notebook (`Notebooks/`), the
  `pldlib.egg` library the base-layer notebooks load plus its
  extracted source (`pldlib/`). Table dictionaries live in `context/data/tables/`.

## Design principles

- One primary KBT per question, matching one notebook stage.
- The base-layer tables are read, not rebuilt, unless the user asks for a rule simulation.
- Notebook code wins where it disagrees with the business-rules page.
- Missing or conflicting inputs create assumptions, not dead ends.
- Patient identifiers are never returned in user-facing output.

## Review and testing

- `python tools/validate_pack.py`: structural validation of the pack.
- `python tools/check_config.py`: confirms `config/` still matches the notebook code.
- `evals/kbt_selection_cases.yaml`: example questions with the expected KBT.
- `PACK_CHANGELOG.md`: what changed in the pack, and where its content came from.
