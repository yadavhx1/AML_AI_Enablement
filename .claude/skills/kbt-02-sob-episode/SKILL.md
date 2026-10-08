---
name: kbt-02-sob-episode
description: Use for AML base-layer questions about the pldlib SOB step, same-day claim de-duplication, source of business (NTB/RS/switch/add-on), episode construction, episode start/end dates, DOS-plus-grace joining, episode length, persistency on an AML product, or Venclexta episode start/end (`AML_LOT_SOB_EPISODE`).
user-invocable: true
---


# KBT 2 - SOB and episode (AML_LOT_SOB_EPISODE)

## Analytical intent

Use this KBT when the output depends on same-product treatment episodes: how claims join into an
episode, when an episode starts and ends, episode duration, or Venclexta start/end. Use KBT 3 when
several products are active at once (regimens), and KBT 4 for lines of therapy.

Notebook: `scripts/Notebooks/AML_LOT_SOB_EPISODE.ipynb`.

## Method

1. Input: the TX final table from KBT 1 (`DOS_FINAL`, `GRACE_VALUE`).
2. `stencil.sob` (claim level): same patient, product and day keeps the claim with the larger DOS
   (`DOS_FINAL DESC, CLAIM_ID`). A new episode starts when claim date − (previous claim date + previous
   DOS) exceeds the previous claim's grace. Each episode start gets a source-of-business label
   (`sob_lvl7`: NTB NAIVE, NTB/RS SWITCH, NTB/RS ADDON, RS SAME; continuing claims = C) using the
   360-day lookback. The lookback affects only these labels, never the episode breaks.
3. `stencil.episode` (reads the `sob_df` temp view) groups to **one row per patient × product ×
   episode**, adding `episode_first_sob`, `first_claim_id_drvd` and the last claim's grace.
4. Episode columns: `EPISODE_NUM_DRVD`, `EPISODE_START_DATE_DRVD`, `EPISODE_END_DATE1_DRVD` (end of the
   last claim), `EPISODE_END_DATE2_DRVD` (end + grace), `EPISODE_END_DATE3_DRVD` (last claim date).
5. For durations, use `EPISODE_END_DATE1_DRVD − EPISODE_START_DATE_DRVD` and censor episodes that are
   still open at the data cut (end + grace beyond the data cut).
6. Venclexta start/end for a patient = MIN episode start / MAX `EPISODE_END_DATE1_DRVD` where
   `FINAL_PRODUCT_NAME = 'VENCLEXTA'`. This is `VEN_START` / `VEN_END` in KBT 5.
7. Validate: patient count equals the TX final table; start ≤ end; one episode number sequence per
   patient-product.

## Working defaults

- Episode end: `EPISODE_END_DATE1_DRVD`.
- Grace is per product, so a multi-product cohort has no single stop rule.
- SOB and episode must run in one session (episode reads the `sob_df` temp view).
- The SQL pldlib generates is rendered in `AML_SOB` / `AML_EPISODE` (library source in
  `scripts/pldlib/`). Read the persisted tables; re-run the SQL only for a rule simulation.
- Source of business: use `sob_lvl7` / `sob_lvl4` / `sob_lvl2_1` on the SOB table, or
  `episode_first_sob` on the episode table.
- Duration summary: median and mean with the distribution.

## Context to read

- `context/domain/key_concepts.md` (pipeline, SOB and episode)
- `context/domain/pldlib.md` (what the sob and episode functions compute)
- `context/domain/days_on_therapy.md`
- Profiles for the SOB and episode tables

## Verified-query candidates

- `AML_SOB`, `AML_EPISODE`.

## Minimum QC

- Episode end column is named.
- Open episodes are censored at the data cut, not given an artificial end.
- "SOB" is read as the pldlib step and its source-of-business labels (NTB/RS), not "start of bucket".


## Output contract

Return the requested result first. State the data source, grain, period, build suffix and material
assumptions. Keep patient identifiers out of the response.
End with the `How this answer was generated` provenance table and append it to `outputs/response_log.md` (`context/response_provenance.md`).
