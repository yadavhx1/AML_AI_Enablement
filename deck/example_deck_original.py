"""example_deck.py — worked example and smoke test for the VEN deck kit.

Builds a short deck on deck/VEN_TEMPLATE.pptx that exercises every major component and the
pack's own conventions (sort orders, TBD for unknowns, the footer floor). EVERY VALUE IS A
PLACEHOLDER (None -> "TBD"). Do not reuse any figure from it; there are none.

    python deck/example_deck.py [out.pptx]

Exit code 1 if the kit's save-time layout check raises any warning.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from output_style_deck import (  # noqa: E402
    new_deck, carry_lines, sort_categories, ACCOUNT_GROUP_ORDER, LOT_ORDER,
)

out = sys.argv[1] if len(sys.argv) > 1 else "example_deck.pptx"

deck = new_deck(brand="VEN | CLL | EXAMPLE")
deck.title_slide("Venclexta example deck", "Placeholder values only",
                 meta=["Built with deck/slide_kit_ven.py"], team="MABI Oncology Analytics")

deck.section("Headline metrics", sub="Every value below is TBD by design", number=1)

s = deck.slide("CLL new patient starts by line of therapy", "Claims-derived LoT | SHA+GPO | TBD period")
s.kpis([("VEN NPS", None, "patients"), ("NPS share", None, "% of market NPS"),
        ("Accounts", None, "L5 parent accounts")])
left, right = s.cols([7, 5])
top = s.y                                   # side-by-side: both columns start here
s.chart("column_stacked", list(LOT_ORDER), {"VEN": [None] * 3, "Other": [None] * 3},
        x=left[0], w=left[1], y=top, h=3.0)
groups = sort_categories(["Community", "Not Available", "Academic", "Federal"], ACCOUNT_GROUP_ORDER)
s.table([[g, None, None] for g in groups] + [["Total", None, None]],
        header=["Account group", "VEN NPS (patients)", "Share (%)"],
        x=right[0], w=right[1], y=top, total=True)
s.at(top + 3.16)
s.footer(carry_lines(source="SHA+GPO", population="CLL, eligible patients (pat_elig_final = 1)",
                     eligibility="CLL regime", extra="Line of therapy is claims-derived (SG-12)."))

s = deck.slide("Example process and callout", "Component demo")
s.steps([("Frame", "cohort"), ("Episodes", "60-day grace"), ("LoT", "CLL rules"), ("Output", None)],
        numbered=True)
s.callout("Placeholder callout: the most recent period is incomplete due to claims lag.", label="Note")
s.footer(carry_lines())

deck.save(out, check_collisions=True)
sys.exit(1 if deck.warnings else 0)
