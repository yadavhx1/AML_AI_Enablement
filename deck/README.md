# Deck kit - VENCLEXTA PowerPoint template

Every `.pptx` the pack generates is built on the VENCLEXTA brand template with this kit. Do not draw decks
from scratch with raw python-pptx, and do not hand-draw brand elements (logos, swoosh, footer rule).

| File | What it is |
|---|---|
| `VEN_TEMPLATE.pptx` | The brand file: cover, content and breaker layouts, logos, footer rule, theme colours. **The template is the deck**: the kit fills it, it never replaces it. |
| `slide_kit_ven.py` | The VEN team's kit, verbatim (one documented `PACK FIX`). Layout engine, palette, components, save-time layout check. |
| `output_style_deck.py` | AML pack conventions on top of the kit: `new_deck()`, `carry_lines()` footer, category orders, `sort_categories()`, `out_path()`. |
| `example_deck.py` | Worked example and smoke test (placeholders only). `python deck/example_deck.py` writes `outputs/_scratch/example_deck.pptx`; exit 1 on any layout warning. |
| `example_deck_original.py` | The VEN team's example as received (CLL pack, imports from a different folder). Reference only. |

Requires `python-pptx` (and PyYAML, already used by `config/`).

## How to build a deck

```python
import sys; sys.path.insert(0, "deck")            # from the pack root; or the absolute path
from output_style_deck import new_deck, carry_lines, out_path, LOT_ORDER, BACKBONE_GROUP_ORDER

deck = new_deck(brand="VEN | AML | <topic>")       # chip shown under the corner art
deck.title_slide("Title", "Month DD, YYYY", meta=["SHA | claims to YYYY-MM-DD"], team="MABI Oncology Analytics")
deck.section("Findings", number=1)                 # optional yellow-wave divider

s = deck.slide("Slide title", "kicker | context")
s.kpis([("VEN NPS", 10158, "gated IC_INELIG 1L"), ("Share", "58.9%", "of gated 1L NPS")])
left, right = s.cols([7, 5]); top = s.y
s.chart("column", list(LOT_ORDER), {"BASE": [...], "ALT": [...]}, x=left[0], w=left[1], y=top, h=3.0)
s.table(rows, header=[...], x=right[0], w=right[1], y=top, total=True)
s.at(top + 3.16)
s.footer(carry_lines(build="_BUSINESS_RULE_CHANGE_VAL", period="2019-2026", population="...",
                     gates="DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1", kbt=4))   # every slide

deck.save(out_path("<topic>", "<Deck_Name>.pptx"), check_collisions=True)
```

## Rules

- **Template only.** `new_deck()` opens `deck/VEN_TEMPLATE.pptx`; the first `title_slide()` fills its cover and
  the first `slide()` its content slide. Change brand art in the template, never in code.
- **Native charts and tables.** Use `s.chart()` (editable PowerPoint charts, brand series colours) and
  `s.table()`. Insert a matplotlib image only when no chart kind fits; then use the kit palette
  (`PRIMARY`, `HIGHLIGHT`, `ACCENT`, ... from `slide_kit_ven`).
- **No invented numbers.** Pass `None` for anything not computed; it renders `TBD`. Every figure must come
  from a query that actually ran.
- **Footer on every content slide**: `s.footer(carry_lines(...))` gives source, build, period, population,
  gates, intensity, the claims-derived LoT caveat and the page number. A missing footer is a save warning.
- **Clean save.** `deck.save(..., check_collisions=True)` must report 0 warnings (overflow, text under the
  corner art, text crossing the footer rule, overlaps). Fix the layout rather than ignoring a warning.
- **Category order**: `LOT_ORDER`, `COHORT_ORDER`, `BACKBONE_GROUP_ORDER`, `ACCOUNT_GROUP_ORDER` (read from
  `config/nps_dashboard_legacy.yaml`), via `sort_categories()`; catch-alls (Other / Not Available / Total) go last.
- **Where it goes**: `out_path(topic, file)` = `outputs/<YYYY-MM-DD>_<topic>/<file>.pptx`. Aggregates only;
  no patient identifiers or NPIs on any slide.
- **QA**: LibreOffice is not installed on the edge node, so slides cannot be rendered here. Rely on the save
  check, and ask the user to open the deck once before sharing.

## Components (see the `slide_kit_ven.py` docstring for arguments)

`text`, `eyebrow`, `bullets`, `panel`, `callout` (`solid=True` for the yellow band), `kpis`, `stack`, `funnel`,
`steps`, `split`, `table`, `chart` (`column`, `column_stacked`, `column_stacked_100`, `bar`, `bar_stacked`,
`line`, `line_markers`, `area`, `pie`, `doughnut`), `matrix`, `timeline`, `legend`; layout with `cols`, `gap`,
`at`, `divider`. Each returns its bottom y, so components can be stacked or placed side by side.
