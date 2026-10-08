"""example_deck.py - worked example and smoke test for the VEN deck kit (AML pack).

Adapted from the VEN team's example (kept verbatim as example_deck_original.py, which targets the
CLL pack). Builds a short deck on deck/VEN_TEMPLATE.pptx that exercises the main components and the
pack's conventions (category orders, TBD for unknowns, the footer on every slide).
EVERY VALUE IS A PLACEHOLDER (None -> "TBD"). Do not reuse any figure from it; there are none.

    python deck/example_deck.py [out.pptx]      # default: outputs/_scratch/example_deck.pptx

Exit code 1 if the kit's save-time layout check raises any warning.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from output_style_deck import (  # noqa: E402
    PACK, new_deck, carry_lines, sort_categories, ACCOUNT_ROLLUP_ORDER, BACKBONE_GROUP_ORDER, LOT_ORDER,
)

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PACK, "outputs", "_scratch", "example_deck.pptx")
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

deck = new_deck(brand="VEN | AML | EXAMPLE")
deck.title_slide("Venclexta AML example deck", "Placeholder values only",
                 meta=["Built with deck/slide_kit_ven.py"], team="MABI Oncology Analytics")

deck.section("Headline metrics", sub="Every value below is TBD by design", number=1)

s = deck.slide("AML new patient starts by line of therapy", "Claims-derived LoT | SHA | TBD period")
s.kpis([("VEN NPS", None, "gated IC_INELIG 1L starts"), ("VEN share", None, "% of gated 1L NPS"),
        ("Accounts", None, "initiating accounts")])
left, right = s.cols([7, 5])
top = s.y                                   # side-by-side: both columns start here
s.chart("column_stacked", list(LOT_ORDER),
        {g: [None] * len(LOT_ORDER) for g in BACKBONE_GROUP_ORDER}, x=left[0], w=left[1], y=top, h=3.0)
groups = sort_categories(["Community", "Not Available", "Academic"], ACCOUNT_ROLLUP_ORDER)
s.table([[g, None, None] for g in groups] + [["Total", None, None]],
        header=["Account group", "VEN NPS (patients)", "Share (%)"],
        x=right[0], w=right[1], y=top, total=True)
s.at(top + 3.16)
s.footer(carry_lines(population="AML, 2+ AML diagnoses", gates="DX_LB_ELIG_FLG = 1, DX_TX_DIFF_FLG = 1",
                     kbt=4, extra="Published slice: IC_INELIG, LOT = 1; metric nps_dashboard_legacy."))

s = deck.slide("Example process and callout", "Component demo")
s.steps([("TX table", "DOS + grace"), ("Episodes", "pldlib sob"), ("Regimens", "pldlib regimen"),
         ("LoT", "90-day gap"), ("NPS", None)], numbered=True)
s.callout("Placeholder callout: the most recent semester is incomplete (2-month SHA lag).", label="Note")
s.footer(carry_lines())

deck.save(out, check_collisions=True)
sys.exit(1 if deck.warnings else 0)
