# How this team presents work

**No sample decks were supplied as formatting references.** At Step 0 the user confirmed that every
uploaded deck is a knowledge source, not a style reference. So this file records only conventions the
material actually evidences, and says plainly where it has no source. Nothing below is a preference —
where there is no evidence, there is no rule.

The companion module `output_style_deck.py` ships with `SOURCE_DECKS = []` for the same reason. See
Q-68 for the request for 5–10 representative decks.

## Titles

**No source.** None of the supplied decks is a Venclexta AML output deliverable whose titling convention
could be observed. The business-rules and training decks use descriptive section headers
("EPISODE BUILDING", "REGIMEN CONSOLIDATION", "D3 | Line of Therapy Assignment"), but those are
methodology documentation, not analytical output, so they are not evidence of how a finding is titled.

Do not invent a title convention. Ask, or follow the requester's own wording.

## Charts

**Chart types — no source** for a house convention. What the material does evidence is the *shape of
the analysis*, which constrains the sensible chart rather than stating a preference:

- Persistency is reported as a **curve over a 30-day period axis**, x = `month_number`
  (`period_number + 1`, so month 1 is the first 30 days), one series per starting semester.
- New patient starts are reported **by reporting month against account type**, with a claims-based
  series and a vendor-reported series shown together for indexing.
- AML line-of-therapy distributions use the buckets **1L / 2L+**.

**Colour — no source.** No palette, brand colour or series-colour convention appears in any supplied
material. Do not adopt one.

**Labelling, legends and axes — partial source.** Two rules are evidenced, and both come from the
data rather than from taste:

- A month on a persistency or DoT axis is a **30-day period from therapy start**, not a calendar
  month. Label it so; the two axes are not interchangeable.
- Sort order on account and specialty cuts is carried by the `*_hier` columns, which are
  "Sort only, not a filter." Use them for ordering rather than sorting alphabetically:
  account groups run Academic, Community, Federal, Not Available; account sub-types run
  Elite Oncology Center through DOD to Not Available.

**Incomplete periods.** The most recent period is short because of claims lag, not because the market
moved. Either exclude it or show it visibly flagged — GG-22 requires this of the answer, and a chart
is an answer.

## Tables

**Density and rounding — no source.** No rounding convention appears anywhere in the material.

What is evidenced:

- **Units must be stated, and they differ between adjacent columns.**
  `total_quantity_dispensed` is in "Units, not milligrams". A quantity column that does not label its
  unit is ambiguous in a way that matters (SG-26).
- **The unknown bucket is reported, never redistributed or hidden.** The dashboards carry
  'Not Available' and '-' as explicit values, and GG-10 forbids reading either as zero. A table that
  drops them misstates its own denominator.
- **Percentages are not summed.** Recompute from numerator and denominator at the level shown
  (GG-14), and name the denominator (GG-15).
- Patient counts are `COUNT(DISTINCT ...)`, because "a patient can appear for several products and
  new-start dates".

## Language

**Partial source.** Team vocabulary, taken from the supplied documents rather than chosen:

- The brand is **Venclexta** in prose and **VEN** in table and column names. The generic name is
  **venetoclax**. *(Venclexta Overview.pptx)*
- The indication is **AML**. Intensity groups are **IC Eligible** and **IC Ineligible**.
- Say **new patient starts** or **NPS**, not "new starts" or "patient adds".
- Say **TRx** and state that it is normalized, because it is: "Normalized Trx = Pill Count / Norm
  Factors". A bare "prescriptions" figure invites the wrong reading (SG-09).
- Say **line of therapy** or **LoT**; the AML buckets are 1L and 2L+.
- Prefer **observed** or **reported** over "actual" for claims-derived figures. Claims describe what
  was billed, not what happened: GG-28 and SG-10 both bear on this, and "actual" asserts more than
  the data carries.
- Say **modelled** or **estimated** for anything derived from SD indication splits or SHA demand —
  those are factor outputs, not measurements (SG-08).
- Say **claims-derived** for line of therapy. It "should not be interpreted as a direct
  representation of physician-documented clinical lines" (SG-12).

**Banned by guardrail rather than by style:** do not present a claims-derived count as complete
(SG-10), and do not quote a figure from a PLD 10x, IQVIA 101 or Symphony training deck as a
Venclexta number (SG-27).

## What every output must carry

Not a style rule — a floor, assembled from the guardrails that bind presentation:

| Element | Rule |
|---|---|
| Unit on every figure | GG-04, SG-26 |
| Period covered | GG-05 |
| Population and filters | GG-06 |
| Data-as-of date | GG-21; no cataloged table publishes one, so state it from the run |
| Source combination | SG-01 |
| Table version, where the table is dated | SG-22 |
| Eligibility rule applied | SG-11 |
| Every conflict reported with all variants | GG-23 |

## Gaps in this file

| Section | State |
|---|---|
| Titles | no source |
| Chart types | no source for a house convention |
| Colour | no source |
| Table density and rounding | no source |
| Labelling and sort order | partial — sort order evidenced, formatting not |
| Language | partial — vocabulary evidenced, tone and structure not |

Closing these needs 5–10 representative Venclexta output decks. See Q-68.
