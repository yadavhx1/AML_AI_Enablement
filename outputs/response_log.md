# Response log

Append-only. One entry per answer. Format: `context/response_provenance.md`.

## 2026-10-08 | Add response provenance logging to the pack

| Type | Item | How it was used |
|---|---|---|
| Prior context | `CLAUDE.md` | Auto-loaded project instructions; read again in full to edit |
| Prior context | User request | Asked for a table logging prior context, assumptions, skills and files for each answer |
| Skill | none | Pack-maintenance request, not an analytical question; no KBT applies |
| File | `context/output_style.md` | Checked for existing response-format rules; none conflict |
| File | `outputs/README.md`, `README.md`, `PACK_CHANGELOG.md` | Updated to document the log |
| File | `.claude/settings.json`, `.gitignore` | Checked settings; added git exception for the log |
| File | `.claude/skills/*/SKILL.md`, `context/metrics/nps_dashboard_legacy.md` | Output contracts extended with the provenance line |
| File | `tools/validate_pack.py` | CLAUDE.md line limit and core-file list updated |
| File | `outputs/2026-10-08_dos-gap-distribution/README.md` | Example of an existing analysis README; used to place `## Provenance` |
| Execution | `python3 tools/validate_pack.py` | Executed after the edits |
| Assumption | Log location `outputs/response_log.md` | Neutral convention: CLAUDE.md requires all generated files in `outputs/`; tracked in git so history is kept |
| Assumption | Table shown in every answer, not only in the log | Neutral convention: the user asked to log how each answer was generated; showing it inline makes it visible |
| Assumption | Answer-only rule kept, with the table as the one exception | Keeps the 2026-10-07 rule against narration; provenance stays in one structured block |
| Assumption | Validator limit raised 130 -> 145 lines | Needed for the new CLAUDE.md section; detail kept in a separate file to limit growth |
| Output | `context/response_provenance.md`, `outputs/response_log.md` | New spec file and log |

## 2026-10-08 | How to handle patients restarting the same therapy after the grace period

| Type | Item | How it was used |
|---|---|---|
| Prior context | `CLAUDE.md`, `context/response_provenance.md` | Loaded or written in the previous turn; reused for workflow and this table |
| Skill | `kbt-02-sob-episode` | Primary: episode break and SOB restart labels. Borrowed the KBT 4 line rule |
| File | `verified_queries/index.tsv`, `kbts/index.md` | Located KBT 2 queries; confirmed KBT choice |
| File | `config/sob_episode.yaml` | sob parameters: grace = GRACE_VALUE, lookback 360, required_grace 0 |
| File | `config/tx_table.yaml` | Per-product grace and DOS values (e.g. VENCLEXTA 60, AZACITIDINE 60, DAUNORUBICIN 5) |
| File | `context/domain/pldlib.md`, `context/domain/key_concepts.md` | sob/episode/regimen behaviour; lookback affects labels only |
| File | `context/domain/line_of_therapy.md` | LINE_CHANGE rule: gap > 90 days = new line |
| File | `context/assumptions/open_items.md`, `sme_answers_reused.md`, `defaults.yaml`, `context/domain/rule_change_history.md` | Searched for restart rules; none found beyond grace notes |
| Verified query | `verified_queries/kbt-02/aml_sob.sql` | Pattern only: read the is_episode_start and sob_lvl7 CASE logic |
| Data | none | No table queried |
| Execution | not run - methodology only | The question is about rules; no counts were asked for |
| Assumption | "Same therapy" = same `FINAL_PRODUCT_NAME` | Neutral convention; episodes are built per product. A same-regimen restart follows the same rules through regimen and LoT |
| Assumption | Build suffix `_BUSINESS_RULE_CHANGE_VAL_v2` | Verified query `AML_SOB` convention; rules are the same in both builds |
| Assumption | Current notebook code is the rule, no new rule proposed | CLAUDE.md: code wins over business-rules page; >90-day relabel left as an SME choice |
| Output | none | No files written besides this log entry |

## 2026-10-08 | How product-level grace periods affect regimen continuity and LoT; push to GitHub

| Type | Item | How it was used |
|---|---|---|
| Prior context | `CLAUDE.md`, `context/response_provenance.md` | Workflow and this table; loaded in earlier turns |
| Prior context | Previous answer (restart after grace) | Reused the episode-break logic, grace values and `sob` parameters already read (`config/sob_episode.yaml`, `config/tx_table.yaml` grace, `pldlib.md`, `line_of_therapy.md`, `aml_sob.sql`) |
| Skill | `kbt-03-regimen` | Primary: how episodes become regimens. Borrowed the KBT 4 line rule and backbone hierarchies |
| Skill | `kbt-04-patient-intensity-lot` | Method only (backbone choice, LINE_CHANGE, no consolidation) |
| File | `config/regimen.yaml` | Regimen uses `EPISODE_END_DATE1_DRVD` (no grace); no clean-up |
| File | `config/intensity_lot.yaml` | 90-day gap, VEN <-> HMA exception, IC_ELIG / IC_INELIG backbone hierarchies |
| File | `config/tx_table.yaml` (PX DOS block) | Fixed DOS per PX product (HMA 28, chemo 1) |
| File | `context/domain/rule_change_history.md` | Consolidation removed; INQOVI grace 60 -> 28 |
| File | `outputs/2026-10-08_dos-gap-distribution/data/dos_cycle.csv` | Earlier executed result: share of refill gaps within DOS + grace per product |
| Verified query | `verified_queries/index.tsv` (KBT 4 rows) | Listed LoT queries; none opened |
| Execution | not run - methodology only | No new query run; coverage figures come from the earlier executed analysis |
| Assumption | Coverage % from the dos-gap analysis is representative of episode breaks | That analysis counted index claims without claim-level DoS; for PX chemo this is nearly all claims. Effect: % are indicative, not exact |
| Assumption | Legacy intensity, `_v2` suffix | KBT 4 default; the `_v2` build was used in the coverage analysis |
| Assumption | Number of extra lines caused by fragmentation not quantified | No query run; offered as a follow-up |
| Assumption | Push includes all pending working-tree changes, not only this session's | User asked to push "the changes"; earlier staged work (KBT 6 removal, deck kit, HTML revision) is documented in PACK_CHANGELOG |
| Output | Local commit on `main`; push to `origin` failed (no GitHub credentials in this environment) | `outputs/` analysis folders stay git-ignored; only `outputs/README.md` and `response_log.md` tracked |
