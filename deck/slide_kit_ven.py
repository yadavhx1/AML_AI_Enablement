"""
slide_kit - fills the VENCLEXTA slide template. Content-agnostic by design.

PACK COPY: as received from the VEN team ("slide_kit_ven 1.py", 2026-09-29), renamed so
it imports. One change, marked "PACK FIX" in Deck._no_bullet(). Everything else is verbatim.

THE TEMPLATE IS THE DECK. This module never draws brand furniture and never
builds a presentation from scratch. Deck() opens VEN_TEMPLATE.pptx, fills the
slides already in it, and adds further slides from its own layouts. Everything
the brand file carries is inherited, untouched:

    top-right swoosh + VENCLEXTA mark  . . . . master "corner art" picture
    yellow footer rule, AbbVie + VENCLEXTA logos . . master / layout pictures
    cover waves, confidentiality line  . . . . . . "2_Title Slide" layout
    yellow breaker wave  . . . . . . . . . . . . . "Breaker Slide" layout

So a slide this kit produces holds your content, a title, and a page number -
nothing else. Nothing is traced by hand, nothing can drift from the brand file,
and a template re-issue flows straight through with no code change.

The template is required. If it is not found, Deck() raises rather than quietly
producing an unbranded deck.

Existing slides are filled in order: the first .title_slide() fills the
template's cover, the first .slide() fills its empty content slide, and anything
further is appended from the matching layout. Shells you never fill are dropped
on save, and slides are written out in the order you created them.

About the template file: it carries FOUR slide masters (one plain Office master
plus three VENCLEXTA ones) and several layout names occur more than once
("2_Title Slide", "Title Only", "Two Content" ...). Layouts are therefore
resolved master-aware, see Deck._layout(): the template's own slides win, then
the master that holds the content slide, then the other VENCLEXTA masters, and
the plain Office master only as a last resort.

What the kit adds on top: the layout engine, the palette read off the template's
own theme ("Venclexta 2": deep teal 005570, yellow FFCE00, teal 00BCB5, pale
yellow FFE680, light teal 86DCD9, grey 808080), component styling matched to
the template, and the save-time layout check.

Fonts are Arial, per the template theme (major and minor). Arial renders
true-to-width in LibreOffice, so a PDF-converted QA pass shows real text fit.

This module owns only the things that must never change: the palette, the page
geometry, the layout engine and the save-time safety net. WHAT goes on a slide
is decided per use case at call time by composing the components below - it is
not a funnel library, and nothing here is specific to any one analysis.

Design goals
------------
1. Declarative: describe WHAT is on the slide, never WHERE. Components stack
   themselves down the content area via an internal y-cursor; pass x/y/w only
   when you deliberately want manual placement.
2. Honest by default: any value passed as None renders "TBD", never a made-up
   number. Pass (value, True) to mark a number as documented (gets a "*").
3. Safe: Deck.save() validates every shape against the printable area and warns
   on overflow, text under the corner art, missing footers and (opt-in) text
   collisions.

Component menu - pick per use case
----------------------------------
    text / eyebrow / bullets     prose, section labels, lists
    panel                        boxed heading + (head, body) pairs
    callout                      emphasis bar; solid=True for the yellow band
    chip                         corner label (auto from Deck(brand=))
    kpis                         row of headline metric cards
    stack                        vertical labelled bands  -> funnels, attrition,
                                 ranked lists, layered logic  (taper/arrows/show)
    funnel                       preset: stack(taper, arrows, % of base)
    steps                        left-to-right process chain
    split                        fan out from one point into N boxes
    table                        hand-drawn grid, zebra rows, total row
    chart                        native editable pptx chart (see CHART_KINDS)
    matrix                       grid of cells -> 2x2, feature comparison
    timeline                     horizontal milestone track
    legend                       colour key
    divider / gap / cols / at    layout control; cols() returns [(x, w), ...]

Every component returns its own bottom y, so anything can be nested inside a
column from cols() or stacked manually.

Usage
-----
    from slide_kit_ven import Deck

    deck = Deck(brand="Project | Client | 2026")   # opens the VENCLEXTA template
    deck.title_slide("Deck title", "May 5, 2026", team="APEX Analytics")
    s = deck.slide("Slide title", "kicker | context | date")
    left, right = s.cols([7, 5])
    s.kpis([("Label", 1234, "sub note"), ("Unknown", None, "not yet sourced")])
    s.chart("column", ["Q1", "Q2"], {"A": [1, 2], "B": [3, 4]}, x=left[0], w=left[1])
    s.footer(["Source: ..."])
    deck.save("My_Deck.pptx", check_collisions=True)

Run with:  PYTHONPATH=.pylibs python3 your_script.py
"""
import copy as _copy
import os as _os
import re as _re

from pptx import Presentation
from pptx.oxml.ns import qn as _qn
from pptx.oxml import parse_xml as _parse_xml
from pptx.opc.constants import RELATIONSHIP_TYPE as _RT
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_MARK

# =====================================================================================
# DESIGN TOKENS  -  VENCLEXTA brand theme
# =====================================================================================
# Sourced from VEN_TEMPLATE.pptx: theme "Venclexta 2" colour scheme (shared by the
# three VENCLEXTA masters), the master title/body styles and the layouts.
#
#   dk2     005570 deep teal   (titles, tx2, bullets on the master)
#   accent1 FFCE00 yellow      accent4 FFE680 pale yellow
#   accent3 00BCB5 teal        accent5 86DCD9 light teal
#   accent6 808080 grey        (accent2 repeats dk2)
#   layout bullet glyphs: accent3 teal; master title: 20pt tx2, not bold
#
# Names are by ROLE, not by hue, so the next rebrand is a change of hex values in
# this block only. Values marked "derived" are tints/shades of a theme colour
# (the theme has no such swatch); everything else is the template's own hex.
PRIMARY     = RGBColor(0x00, 0x55, 0x70)   # dk2 deep teal: titles, dark bands
PRIMARY_DK  = RGBColor(0x00, 0x3A, 0x4D)   # derived: deeper teal for heavy fills
PRIMARY_LT  = RGBColor(0x86, 0xDC, 0xD9)   # accent5 light teal: soft text on teal
PRIMARY_BG  = RGBColor(0xEB, 0xF3, 0xF5)   # derived: faint teal wash
ACCENT      = RGBColor(0x00, 0xBC, 0xB5)   # accent3 teal: bullets, arrows, dots
ACCENT_DK   = RGBColor(0x00, 0x87, 0x82)   # derived: teal dark enough for small text
ACCENT_LT   = RGBColor(0xC9, 0xEF, 0xED)   # derived: pale teal (from accent5)
ACCENT_BG   = RGBColor(0xEC, 0xF9, 0xF8)   # derived: teal tint panel fill
ACCENT_SOFT = RGBColor(0x86, 0xDC, 0xD9)   # accent5: de-emphasised bars
HIGHLIGHT   = RGBColor(0xFF, 0xCE, 0x00)   # accent1 yellow: the brand signature
HIGHLIGHT_LT= RGBColor(0xFF, 0xE6, 0x80)   # accent4 pale yellow
HIGHLIGHT_BG= RGBColor(0xFF, 0xF8, 0xDB)   # derived: yellow tint panel fill
NEUTRAL     = RGBColor(0xF2, 0xF4, 0xF5)   # derived: cool neutral panel
NEUTRAL_LN  = RGBColor(0xDD, 0xE3, 0xE6)   # derived: neutral hairline
STONE       = RGBColor(0x80, 0x80, 0x80)   # accent6 grey
COVER_INK   = RGBColor(0x15, 0x60, 0x82)   # the cover's own title / team colour
                                           # (inherited from the cover master's
                                           # theme; set to PRIMARY to unify)
AMBER       = RGBColor(0xB0, 0x6A, 0x0F)   # decisions / confirm
AMBER_DK    = RGBColor(0x8A, 0x53, 0x0C)
AMBER_BG    = RGBColor(0xFD, 0xF6, 0xEC)
AMBER_LN    = RGBColor(0xEB, 0xDC, 0xC4)
RED         = RGBColor(0xB0, 0x2E, 0x34)   # risk / drop
RISK_BG     = RGBColor(0xFC, 0xEE, 0xEE)
RISK_LN     = RGBColor(0xF0, 0xC4, 0xC6)
GREEN       = RGBColor(0x0E, 0x7C, 0x4A)   # good / retained
GREEN_BG    = RGBColor(0xEF, 0xF7, 0xF1)
GREEN_LN    = RGBColor(0xC9, 0xE4, 0xD5)
BLUE        = PRIMARY
GREY_BASE   = RGBColor(0x59, 0x59, 0x59)   # base / universe / total rows
INK         = RGBColor(0x00, 0x00, 0x00)   # tx1 primary text (template body = black)
INK_SOFT    = RGBColor(0x59, 0x59, 0x59)   # secondary text
INK_LIGHT   = RGBColor(0x8C, 0x8C, 0x8C)   # footnotes
RULE        = RGBColor(0xD9, 0xD9, 0xD9)   # hairlines
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
BLACK       = RGBColor(0x00, 0x00, 0x00)
BG_NOTE     = NEUTRAL                       # neutral panel fill
ARROW       = ACCENT                        # connectors / flow arrows

# Fonts: the VENCLEXTA theme sets Arial for both major and minor fonts.
FONT       = "Arial"    # body
FONT_HEAD  = "Arial"    # slide titles, section labels


def set_fonts(body=None, head=None):
    """Override the typefaces at runtime."""
    global FONT, FONT_HEAD
    if body:
        FONT = body
        if head is None:
            FONT_HEAD = body
    if head:
        FONT_HEAD = head


# Named tones for panels / callouts / kpis: (fill, line, heading, body)
TONES = {
    "neutral":   (NEUTRAL,      NEUTRAL_LN,   PRIMARY,   INK_SOFT),
    "brand":     (PRIMARY_BG,   PRIMARY_LT,   PRIMARY,   INK_SOFT),
    "accent":    (ACCENT_BG,    ACCENT_LT,    ACCENT_DK, INK_SOFT),
    "highlight": (HIGHLIGHT_BG, HIGHLIGHT_LT, PRIMARY,   INK_SOFT),
    "warn":      (AMBER_BG,     AMBER_LN,     AMBER_DK,  INK_SOFT),
    "good":      (GREEN_BG,     GREEN_LN,     GREEN,     INK_SOFT),
    "risk":      (RISK_BG,      RISK_LN,      RED,       INK_SOFT),
    "dark":      (PRIMARY,      None,         WHITE,     PRIMARY_LT),
    "plain":     (None,         None,         INK,       INK_SOFT),
}
# Chart series follow the theme's accent order: teal, yellow, bright teal, ...
SERIES_COLORS = [PRIMARY, HIGHLIGHT, ACCENT, ACCENT_SOFT, STONE, HIGHLIGHT_LT,
                 PRIMARY_DK, GREY_BASE]

# Back-compat aliases: scripts written against the ELAHERE kit (and the older
# purple/teal kit before it) keep working and pick up the VENCLEXTA palette.
PLUM, PLUM_DK, PLUM_LT, PLUM_BG = PRIMARY, PRIMARY_DK, PRIMARY_LT, PRIMARY_BG
CORAL, CORAL_DK, CORAL_LT, CORAL_BG = ACCENT, ACCENT_DK, ACCENT_LT, ACCENT_BG
PINK, BLUSH, WARM, WARM_LN, NAVY = ACCENT_SOFT, RISK_BG, NEUTRAL, NEUTRAL_LN, PRIMARY_DK
PURPLE, PURPLE_DK, PURPLE_LT, PURPLE_BG = PRIMARY, PRIMARY_DK, PRIMARY_LT, PRIMARY_BG
TEAL, TEAL_DK, TEAL_LT, TEAL_BG = ACCENT, ACCENT_DK, ACCENT_LT, ACCENT_BG


def ramp(n, start=PRIMARY_DK, end=ACCENT_DK):
    """n colours interpolated along the brand teal ramp. Used by .funnel(). Ends
    on ACCENT_DK rather than ACCENT so white band text stays readable."""
    if n <= 1:
        return [start]
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(RGBColor(*(round(a + (b - a) * t) for a, b in
                             zip((start[0], start[1], start[2]),
                                 (end[0], end[1], end[2])))))
    return out

# Chart kinds exposed by Slide.chart(); native, editable pptx charts.
CHART_KINDS = {
    "column":             XL_CHART_TYPE.COLUMN_CLUSTERED,
    "column_stacked":     XL_CHART_TYPE.COLUMN_STACKED,
    "column_stacked_100": XL_CHART_TYPE.COLUMN_STACKED_100,
    "bar":                XL_CHART_TYPE.BAR_CLUSTERED,
    "bar_stacked":        XL_CHART_TYPE.BAR_STACKED,
    "bar_stacked_100":    XL_CHART_TYPE.BAR_STACKED_100,
    "line":               XL_CHART_TYPE.LINE,
    "line_markers":       XL_CHART_TYPE.LINE_MARKERS,
    "area":               XL_CHART_TYPE.AREA,
    "area_stacked":       XL_CHART_TYPE.AREA_STACKED,
    "pie":                XL_CHART_TYPE.PIE,
    "doughnut":           XL_CHART_TYPE.DOUGHNUT,
}

# Content box geometry (16:9, 13.333 x 7.5 in). Read off the VENCLEXTA content
# layout "1_Title and Content": title at x=0.778 y=0.194, yellow footer rule at
# y=6.86, logos and page number below it, corner art top-right.
MARGIN_X   = 0.778
CONTENT_W  = 11.777    # symmetric margins: 0.778 .. 12.555
CONTENT_T  = 1.30      # first usable y, below the title block and chip
CONTENT_B  = 6.40      # last usable y; footnotes sit between here and the rule
FOOTER_RULE= 6.86      # top of the template's yellow footer line
GUTTER     = 0.28

# Positions read off the masters, used only to place content relative to their
# chrome. The chrome itself is the template's - nothing here draws it.
TITLE_Y    = 0.25
TITLE_W    = 8.50      # title stops short of the corner art (starts x=9.32)
TITLE_SIZE = 20        # master title style: 20pt, deep teal, regular
TITLE_BOLD = False
CORNER_ART = (9.30, 0.0, 13.333, 0.92)             # keep text out of this box
TAG_XY     = (10.30, 0.97, 2.255, 0.28)            # chip, just under the corner art
PAGE_XY    = (12.944, 7.174, 0.278)                # only if a layout has no
                                                   # slide-number placeholder

# The brand file. Searched for next to this module and in the working directory;
# pass Deck(template="path/to/file.pptx") to point elsewhere.
TEMPLATE   = "VEN_TEMPLATE.pptx"

# Layout names inside that file, by role. A value may also be a tuple
# (master_index, layout_name) to pin one master explicitly.
LAYOUTS = {
    "title":      "2_Title Slide",        # the template's own cover
    "content":    "1_Title and Content",  # the template's own content slide
    "section":    "Breaker Slide",        # yellow-wave divider
    "title_only": "Title Only",
    "columns":    "Two Content",
}


# =====================================================================================
# FORMATTING
# =====================================================================================
def fmt_n(v, prefix="n = ", tbd="TBD", pct_of=None):
    """None-safe count formatter. Never invents a number."""
    if v is None:
        return f"{prefix}{tbd}"
    if isinstance(v, float) and not v.is_integer():
        s = f"{v:,.1f}"
    else:
        s = f"{int(v):,}"
    if pct_of:
        s += f"  ({v / pct_of:.0%})"
    return f"{prefix}{s}"


def fmt_pct(v, dp=1):
    return "TBD" if v is None else f"{v * 100:.{dp}f}%"


def fmt_delta(v, dp=0, suffix=""):
    if v is None:
        return "TBD"
    return f"{'+' if v > 0 else ''}{v:,.{dp}f}{suffix}"


def _clean(v):
    """Unwrap (value, documented_flag) tuples."""
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], bool):
        return v[0], v[1]
    return v, False


def _norm(items, keys):
    """Accept dicts, tuples or bare strings for any component's item list."""
    out = []
    for it in items:
        if isinstance(it, dict):
            d = dict(it)
        elif isinstance(it, (list, tuple)):
            d = {k: v for k, v in zip(keys, it)}
        else:
            d = {keys[0]: it}
        for k in keys:
            d.setdefault(k, None)
        out.append(d)
    return out


def _on_dark(fill):
    """Readable secondary-text colour to sit on a brand fill."""
    if _lum(fill) >= 0.62:
        return INK_SOFT
    if fill in (PRIMARY, PRIMARY_DK):
        return PRIMARY_LT
    if fill in (ACCENT, ACCENT_DK):
        return ACCENT_LT
    if fill == RED:
        return RISK_BG
    return RGBColor(0xE8, 0xE8, 0xE8)


# =====================================================================================
# LOW-LEVEL PRIMITIVES
# =====================================================================================
def _no_shadow(sh):
    """No drop shadow. The VENCLEXTA theme's effect style carries one, so besides
    the empty effect list the shape's style reference is pointed at 'no effect'
    (some renderers read the style reference and ignore the empty list)."""
    sh.shadow.inherit = False
    style = sh._element.find(_qn("p:style"))
    if style is not None:
        ref = style.find(_qn("a:effectRef"))
        if ref is not None:
            ref.set("idx", "0")
    return sh


def textbox(slide, x, y, w, h, text, size=11, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False,
            space_after=0, line_spacing=None, bullet=False, font=None,
            bullet_color=ACCENT):
    """Text box. `text` is a str, or a list of str, or a list of (str, {overrides}).
    font defaults to the body face; pass FONT_HEAD for titles. Bullet glyphs are
    drawn in the brand teal (accent3), as in the template's content layout."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(text, str):
        paras = [(text, {})]
    else:
        paras = [(p, {}) if isinstance(p, str) else p for p in text]
    for i, (s, over) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = over.get("align", align)
        p.space_after = Pt(over.get("space_after", space_after))
        ls = over.get("line_spacing", line_spacing)
        if ls:
            p.line_spacing = ls
        face = over.get("font", font) or FONT
        sz = over.get("size", size)

        def _style(run, col, bold_=None, italic_=None):
            f = run.font
            f.name = face
            f.size = Pt(sz)
            f.bold = over.get("bold", bold) if bold_ is None else bold_
            f.italic = over.get("italic", italic) if italic_ is None else italic_
            f.color.rgb = col

        if over.get("bullet", bullet):
            _style(p.add_run(), over.get("bullet_color", bullet_color), bold_=True)
            p.runs[-1].text = "•  "
        r = p.add_run()
        r.text = s
        _style(r, over.get("color", color))
    return tb


def _place(ph, x=None, y=None, w=None, h=None):
    """Move/resize an inherited placeholder safely.

    A slide placeholder with no <a:xfrm> of its own inherits geometry from the
    layout. Setting just one dimension makes python-pptx write an xfrm whose
    other values default to zero - a zero-width box renders as nothing. So read
    all four first (which resolves the inherited values) and write all four.
    """
    left, top, width, height = ph.left, ph.top, ph.width, ph.height
    ph.left = Inches(x) if x is not None else left
    ph.top = Inches(y) if y is not None else top
    ph.width = Inches(w) if w is not None else width
    ph.height = Inches(h) if h is not None else height
    return ph


def _fill_ph(ph, text, size=11, bold=False, color=INK, font=None,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False,
             line_spacing=None, space_after=0):
    """Write into an inherited placeholder, keeping its position and its link to
    the layout. Used instead of a fresh text box wherever the template already
    provides a slot, so titles and covers stay where the brand file puts them."""
    tf = ph.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = [(text, {})] if isinstance(text, str) else [
        (t, {}) if isinstance(t, str) else t for t in text]
    for i, (t, over) in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = over.get("align", align)
        para.space_after = Pt(over.get("space_after", space_after))
        ls = over.get("line_spacing", line_spacing)
        if ls:
            para.line_spacing = ls
        r = para.add_run()
        r.text = t
        f = r.font
        f.name = over.get("font", font) or FONT
        f.size = Pt(over.get("size", size))
        f.bold = over.get("bold", bold)
        f.italic = over.get("italic", italic)
        f.color.rgb = over.get("color", color)
    return ph


def rect(slide, x, y, w, h, fill, line=None, radius=None, line_w=1):
    """Rectangle; pass radius (0-0.5) for a rounded rectangle."""
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        sh.adjustments[0] = radius
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    sh.text_frame.text = ""
    return _no_shadow(sh)


def num_badge(slide, cx, cy, n, d=0.30, fill=PRIMARY, color=WHITE, size=10.5):
    """Numbered circle - the template's step marker."""
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2),
                                Inches(cy - d / 2), Inches(d), Inches(d))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    _no_shadow(sh)
    textbox(slide, cx - d / 2, cy - d / 2, d, d, str(n), size=size, bold=True,
            color=color, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return sh


def _lum(c):
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def _text_on(fill):
    """White or ink, whichever is readable on `fill`. Matters here because the
    brand palette runs from deep teal to bright yellow."""
    return WHITE if _lum(fill) < 0.62 else INK


def hairline(slide, x, y, w, color=RULE, weight=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Pt(weight))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return _no_shadow(sh)


def vline(slide, x, y, h, color=RULE, weight=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Pt(weight), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return _no_shadow(sh)


def down_arrow(slide, cx, y, color=ARROW, w=0.20, h=0.15):
    sh = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,
                                Inches(cx - w / 2), Inches(y), Inches(w), Inches(h))
    sh.rotation = 180
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return _no_shadow(sh)


def _right_arrow(slide, x, y, w, color=ARROW, h=0.14):
    sh = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE,
                                Inches(x), Inches(y), Inches(max(0.10, w)), Inches(h))
    sh.rotation = 90
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return _no_shadow(sh)


def connect(slide, x1, y1, x2, y2, color=ARROW, weight=1.25):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                   Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(weight)
    return c


def _est_lines(text, width_in, size):
    """Rough wrapped-line count: ~1.9 chars per (pt of width / font size)."""
    if not text:
        return 1
    chars_per_line = max(8, int(width_in * 72 / (size * 0.52)))
    return max(1, -(-len(text) // chars_per_line))


# =====================================================================================
# SLIDE
# =====================================================================================
class Slide:
    """A content slide. Components stack down from an internal y-cursor.

    Every component accepts optional x / y / w to override auto-layout, and
    returns its own bottom y. If y is omitted the component starts at the
    cursor and advances it.
    """

    def __init__(self, deck, sl, title=None, kicker=None, brand=None):
        self.deck, self.sl = deck, sl
        self.y = CONTENT_T
        self.x, self.w = MARGIN_X, CONTENT_W
        self._has_footer = False
        if title:
            self._header(title, kicker, brand)

    # -------------------------------------------------- chrome
    def _header(self, title, kicker, brand):
        """Fill the layout's title placeholder where there is one, so the title
        keeps the template's own x-position and inherited style. No underline
        rule: the corner swoosh is the motif and the template leaves the title
        area clean. The title always stops at TITLE_W so it never runs under
        the corner art. `brand` renders as the chip just below that art."""
        tw = TITLE_W
        n_lines = _est_lines(title, tw, TITLE_SIZE)
        lh = 0.37 * TITLE_SIZE / 20            # line pitch at 0.95 spacing
        ph = self._title_ph()
        if ph is None:
            ph = self.deck._clone_layout_ph(self.sl, PP_PLACEHOLDER.TITLE,
                                            PP_PLACEHOLDER.CENTER_TITLE)
        if ph is not None:
            _place(ph, x=MARGIN_X, y=TITLE_Y, w=tw, h=lh * n_lines + 0.08)
            tf = ph.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            para = tf.paragraphs[0]
            para.line_spacing = 0.95
            r = para.add_run()
            r.text = title
            r.font.name, r.font.size = FONT_HEAD, Pt(TITLE_SIZE)
            r.font.bold = TITLE_BOLD
            r.font.color.rgb = PRIMARY
        else:
            textbox(self.sl, MARGIN_X, TITLE_Y, tw, lh * n_lines, title,
                    size=TITLE_SIZE, bold=TITLE_BOLD, color=PRIMARY, font=FONT_HEAD,
                    line_spacing=0.95)
        y = TITLE_Y + lh * n_lines
        if kicker:
            textbox(self.sl, MARGIN_X, y + 0.06, tw, 0.24, kicker,
                    size=10, color=INK_SOFT)
            y += 0.32
        if brand:
            self.chip(brand)
        self.y = max(CONTENT_T, y + 0.14)
        return self.y

    def _title_ph(self):
        """The slide's title placeholder, if its layout provides one."""
        for sh in self.sl.shapes:
            if sh.is_placeholder and sh.placeholder_format.type in (
                    PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                return sh
        return None

    def _ph(self, *types):
        for sh in self.sl.shapes:
            if sh.is_placeholder and sh.placeholder_format.type in types:
                return sh
        return None

    def chip(self, label, xywh=None, tone_fill=NEUTRAL, color=PRIMARY, size=9):
        """Neutral chip holding a workstream or project label. Sits right-aligned
        just under the template's corner art, which owns the top-right corner."""
        cx, cy, cw, ch = xywh or TAG_XY
        rect(self.sl, cx, cy, cw, ch, tone_fill)
        textbox(self.sl, cx + 0.10, cy, cw - 0.20, ch, label, size=size, bold=True,
                italic=True, color=color, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE, font=FONT_HEAD, line_spacing=0.95)
        return cy + ch

    def footer(self, notes=None, page=None):
        """Notes and sources in the strip above the template's yellow footer rule,
        plus the page number as a live PowerPoint field so it survives
        reordering. Call last on the slide. The footer itself - yellow rule,
        AbbVie and VENCLEXTA logos - is the template's and is never redrawn."""
        if notes:
            notes = [notes] if isinstance(notes, str) else notes
            textbox(self.sl, MARGIN_X, CONTENT_B + 0.04, CONTENT_W,
                    FOOTER_RULE - CONTENT_B - 0.08,
                    [(n, {"size": 8, "color": INK_SOFT, "space_after": 1}) for n in notes],
                    line_spacing=1.04)
        self.deck._page_number(self.sl, page)
        self._has_footer = True
        return self

    # -------------------------------------------------- layout
    def gap(self, h=0.16):
        self.y += h
        return self.y

    def at(self, y):
        self.y = y
        return self

    def remaining(self):
        return CONTENT_B - self.y

    def cols(self, spec=2, gutter=GUTTER, x=None, w=None):
        """Split into columns. spec = count (equal) or weights e.g. [7, 5].
        Returns [(x, w), ...]."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        weights = [1] * spec if isinstance(spec, int) else list(spec)
        total = sum(weights)
        avail = w - gutter * (len(weights) - 1)
        out, cx = [], x
        for wt in weights:
            cw = avail * wt / total
            out.append((round(cx, 3), round(cw, 3)))
            cx += cw + gutter
        return out

    def divider(self, y=None, pad=0.10):
        y = self.y if y is None else y
        hairline(self.sl, self.x, y + pad, self.w)
        self.y = y + pad * 2 + 0.02
        return self.y

    # -------------------------------------------------- text
    def text(self, body, y=None, x=None, w=None, h=0.3, **kw):
        """Escape hatch for arbitrary text. Advances cursor by h."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        textbox(self.sl, x, y, w, h, body, **kw)
        if auto:
            self.y = y + h
        return y + h

    def eyebrow(self, label, y=None, x=None, w=None, color=PRIMARY):
        """Small uppercase section label above a block."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        textbox(self.sl, x, y, w, 0.24, label.upper(), size=10, bold=True,
                color=color, font=FONT_HEAD)
        if auto:
            self.y = y + 0.32
        return y + 0.32

    def bullets(self, items, y=None, x=None, w=None, size=10, dense=False):
        """Simple bullet list. items = [str, ...] or [(head, body), ...]."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y0 = self.y if auto else y
        yy = y0
        lh = 0.20 if dense else 0.24
        for it in items:
            if isinstance(it, str):
                n = _est_lines(it, w - 0.25, size)
                textbox(self.sl, x, yy, w, lh * n, it, size=size, color=INK_SOFT,
                        bullet=True, line_spacing=1.05)
                yy += lh * n + (0.02 if dense else 0.06)
            else:
                head, body = it
                textbox(self.sl, x, yy, w, 0.20, head, size=size, bold=True, color=INK)
                n = _est_lines(body, w, size - 0.5)
                textbox(self.sl, x, yy + 0.19, w, 0.20 * n, body, size=size - 0.5,
                        color=INK_SOFT, line_spacing=1.05)
                yy += 0.19 + 0.185 * n + 0.09
        if auto:
            self.y = yy
        return yy

    # -------------------------------------------------- panel
    def panel(self, heading=None, items=None, y=None, x=None, w=None, h=None,
              tone="neutral", body=None, size=9.5):
        """Boxed block: optional eyebrow heading, then (head, body) pairs or plain
        strings. Height auto-computed unless given."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        fill, line, head_c, body_c = TONES[tone]
        if heading:
            self.eyebrow(heading, y=y, x=x, w=w, color=head_c)
            y += 0.32
        items = items or []
        # measure
        inner_w = w - 0.40
        heights = []
        for it in items:
            if isinstance(it, str):
                heights.append(0.185 * _est_lines(it, inner_w, size) + 0.10)
            else:
                heights.append(0.19 + 0.175 * _est_lines(it[1], inner_w, size - 0.5) + 0.13)
        need = sum(heights) + 0.30
        if body:
            need += 0.175 * _est_lines(body, inner_w, size - 1) + 0.14
        box_h = h if h else max(0.5, need)
        if fill is not None:
            rect(self.sl, x, y, w, box_h, fill, line=line, radius=0.03)
        yy = y + 0.15
        for it, ih in zip(items, heights):
            if isinstance(it, str):
                textbox(self.sl, x + 0.20, yy, inner_w, ih, it, size=size,
                        color=body_c, line_spacing=1.05)
            else:
                textbox(self.sl, x + 0.20, yy, inner_w, 0.19, it[0], size=size,
                        bold=True, color=head_c)
                textbox(self.sl, x + 0.20, yy + 0.19, inner_w, ih - 0.19, it[1],
                        size=size - 0.5, color=body_c, line_spacing=1.05)
            yy += ih
        if body:
            textbox(self.sl, x + 0.20, yy, inner_w, box_h - (yy - y) - 0.10, body,
                    size=size - 1, color=INK_LIGHT, line_spacing=1.05)
        bottom = y + box_h
        if auto:
            self.y = bottom + 0.18
        return bottom

    def callout(self, text, y=None, x=None, w=None, tone="brand", label=None,
                size=10, solid=False, fill=None, align=None):
        """Emphasis bar. Default is a tinted panel with a left accent edge;
        solid=True gives a filled VENCLEXTA-yellow band with centred bold text
        (pass fill=PRIMARY for the deep-teal band with reversed text)."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        t_fill, line, head_c, body_c = TONES[tone]
        n = _est_lines(text, w - 0.55, size)
        h = max(0.42, 0.20 * n + 0.24)
        if solid:
            band = fill or HIGHLIGHT
            ink = _text_on(band)
            rect(self.sl, x, y, w, h, band)
            tx, tw = x + 0.22, w - 0.44
            if label:
                textbox(self.sl, tx, y, 1.5, h, label.upper(), size=8.5, bold=True,
                        color=ink, anchor=MSO_ANCHOR.MIDDLE, font=FONT_HEAD)
                tx += 1.5
                tw = x + w - tx - 0.22
            textbox(self.sl, tx, y, tw, h, text, size=size + 1, bold=True, color=ink,
                    align=PP_ALIGN.CENTER if align is None else align,
                    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05, font=FONT_HEAD)
        else:
            rect(self.sl, x, y, w, h, fill or t_fill, line=line, radius=0.03)
            rect(self.sl, x, y, 0.055, h, head_c)
            tx = x + 0.22
            if label:
                textbox(self.sl, tx, y, 1.5, h, label.upper(), size=8.5, bold=True,
                        color=head_c, anchor=MSO_ANCHOR.MIDDLE, font=FONT_HEAD)
                tx += 1.5
            textbox(self.sl, tx, y, x + w - tx - 0.18, h, text, size=size,
                    color=INK, align=align or PP_ALIGN.LEFT,
                    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
        bottom = y + h
        if auto:
            self.y = bottom + 0.16
        return bottom

    # -------------------------------------------------- kpi cards
    def kpis(self, cards, y=None, x=None, w=None, h=1.15, gutter=GUTTER, tone="neutral"):
        """Row of metric cards. cards = [(label, value, sub), ...].
        value may be a number (formatted with commas), a string, or None -> TBD."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        fill, line, head_c, body_c = TONES[tone]
        slots = self.cols(len(cards), gutter=gutter, x=x, w=w)
        for (cx, cw), card in zip(slots, cards):
            label, value, sub = (list(card) + [None, None])[:3]
            val, flagged = _clean(value)
            rect(self.sl, cx, y, cw, h, fill, line=line, radius=0.04)
            rect(self.sl, cx, y, cw, 0.055, HIGHLIGHT if tone == "neutral" else head_c)
            textbox(self.sl, cx + 0.16, y + 0.14, cw - 0.32, 0.22,
                    label.upper(), size=8.5, bold=True, color=head_c,
                    font=FONT_HEAD)
            if val is None:
                shown, vc, vsize = "TBD", INK_LIGHT, 20
            elif isinstance(val, str):
                shown, vc, vsize = val, PRIMARY, 20
            else:
                shown, vc, vsize = f"{val:,}" + ("*" if flagged else ""), PRIMARY, 22
            textbox(self.sl, cx + 0.16, y + 0.36, cw - 0.32, 0.38, shown,
                    size=vsize, bold=True, color=vc, font=FONT_HEAD)
            if sub:
                textbox(self.sl, cx + 0.16, y + h - 0.32, cw - 0.32, 0.26, sub,
                        size=8.5, color=body_c, line_spacing=1.02)
        bottom = y + h
        if auto:
            self.y = bottom + 0.20
        return bottom

    # -------------------------------------------------- stacked bands (funnel / process / rank)
    def stack(self, rows, y=None, x=None, w=None, notes_w=None, bar_h=None,
              show=None, base=None, color=PRIMARY, first_grey=False, taper=0.0,
              arrows=True, reserve=0.0, label_size=12.5, value_size=11.5,
              value_prefix="n = "):
        """Vertical stack of labelled bands. The generic engine behind funnels,
        process chains, ranked lists and attrition views.

        rows: list of dicts (or tuples in this order) with keys
            label   required, bold text in the band
            sub     optional small line under the label
            n       count; None -> "TBD"; (n, True) -> documented, gets "*"
            notes   optional str or [head, body, ...] rendered to the right
            color   optional band colour override
            value   optional str shown instead of the formatted count
        show    None | "pct_base" (% of base) | "pct_prev" (% retained) | "drop"
        taper   0 = equal widths; 0.16 = classic funnel narrowing
        arrows  draw a small arrow between bands
        reserve vertical space to leave free below (e.g. for .split)
        """
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y0 = self.y if auto else y
        rws = _norm(rows, ["label", "sub", "n", "notes"])
        for i, r in enumerate(rws):
            if r.get("color") is None:
                r["color"] = GREY_BASE if (i == 0 and first_grey) else color
        has_notes = any(r["notes"] for r in rws)
        bar_w = (notes_w or 6.05) if has_notes else w
        nx = x + bar_w + 0.95
        nw = x + w - nx
        n = len(rws)
        avail = CONTENT_B - y0 - reserve
        gap = 0.22 if arrows else 0.10
        bh = bar_h or min(0.90, max(0.34, (avail - gap * (n - 1)) / n))
        pitch = bh + gap
        cx = x + bar_w / 2
        if base is None:
            base = _clean(rws[0]["n"])[0]
        prev = None
        for i, r in enumerate(rws):
            yy = y0 + i * pitch
            val, flagged = _clean(r["n"])
            bw = bar_w * (1 - taper * (i / max(1, n - 1)))
            bx = cx - bw / 2
            rect(self.sl, bx, yy, bw, bh, r["color"], radius=0.10)
            ink = _text_on(r["color"])
            soft = _on_dark(r["color"])
            lab_w = bw - 2.25
            if r["sub"]:
                textbox(self.sl, bx + 0.22, yy + 0.06, lab_w, bh - 0.12,
                        [(r["label"], {"size": label_size, "bold": True, "color": ink, "space_after": 1}),
                         (r["sub"], {"size": 8.5, "color": soft})],
                        anchor=MSO_ANCHOR.MIDDLE)
            else:
                textbox(self.sl, bx + 0.22, yy, lab_w, bh, r["label"], size=label_size,
                        bold=True, color=ink, anchor=MSO_ANCHOR.MIDDLE)
            # right-hand value + optional ratio, inside the band
            if r.get("value") is not None:
                shown = str(r["value"])
            else:
                shown = fmt_n(val, prefix=value_prefix) + ("*" if flagged else "")
            vparas = [(shown, {"size": value_size, "bold": True, "color": ink,
                               "align": PP_ALIGN.RIGHT, "space_after": 0})]
            ratio = None
            if show and val is not None:
                if show == "pct_base" and base:
                    ratio = f"{val / base:.1%} of base"
                elif show == "pct_prev" and prev:
                    ratio = f"{val / prev:.1%} retained"
                elif show == "drop" and prev:
                    ratio = f"-{prev - val:,.0f} ({1 - val / prev:.1%})"
            if ratio:
                vparas.append((ratio, {"size": 8.5, "color": soft, "align": PP_ALIGN.RIGHT}))
            textbox(self.sl, bx + bw - 1.95, yy, 1.73, bh, vparas,
                    anchor=MSO_ANCHOR.MIDDLE)
            if r["notes"]:
                nts = [r["notes"]] if isinstance(r["notes"], str) else list(r["notes"])
                paras = [(nts[0], {"size": 9.5, "bold": True, "color": INK, "space_after": 1})]
                paras += [(t, {"size": 8.5, "color": INK_SOFT, "space_after": 1}) for t in nts[1:]]
                vline(self.sl, nx - 0.30, yy + 0.04, bh - 0.08)
                textbox(self.sl, nx, yy - 0.02, nw, bh + 0.04, paras,
                        anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.03)
            if arrows and i < n - 1:
                down_arrow(self.sl, cx, yy + bh + 0.035)
            if val is not None:
                prev = val
        bottom = y0 + (n - 1) * pitch + bh
        if auto:
            self.y = bottom + 0.18
        return bottom

    def funnel(self, stages, gradient=True, **kw):
        """Convenience preset: .stack() with funnel taper, arrows and % of base.
        Bands ramp deep teal -> teal down the funnel, echoing the cover waves;
        pass gradient=False for a single flat colour."""
        kw.setdefault("taper", 0.14)
        kw.setdefault("arrows", True)
        kw.setdefault("first_grey", False)
        kw.setdefault("show", "pct_base")
        if gradient:
            shades = ramp(len(stages))
            rws = _norm(stages, ["label", "sub", "n", "notes"])
            for r, c in zip(rws, shades):
                if r.get("color") is None:
                    r["color"] = c
            stages = rws
        return self.stack(stages, **kw)

    # -------------------------------------------------- horizontal flow
    def steps(self, items, y=None, x=None, w=None, h=0.86, gutter=0.30,
              color=PRIMARY, tone=None, numbered=False, size=10.5, arrows=True,
              show_n=True):
        """Left-to-right process chain. items = [(label, sub, n), ...] or dicts.
        Use tone= for light boxes with dark text instead of solid brand fill.
        show_n=False drops the count line for a chain that carries no counts
        (PACK EXT 2026-09-30); by default a missing count still renders TBD."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        its = _norm(items, ["label", "sub", "n"])
        slots = self.cols(len(its), gutter=gutter, x=x, w=w)
        for i, ((bx, bw), it) in enumerate(zip(slots, its)):
            fill = it.get("color") or color
            if tone:
                tfill, tline, head_c, body_c = TONES[tone]
                rect(self.sl, bx, y, bw, h, tfill, line=tline, radius=0.05)
                rect(self.sl, bx, y, bw, 0.05, head_c)
                lab_c, sub_c = head_c, body_c
            else:
                rect(self.sl, bx, y, bw, h, fill, radius=0.06)
                lab_c, sub_c = _text_on(fill), _on_dark(fill)
            head = f"{i + 1}.  {it['label']}" if numbered else it["label"]
            paras = [(head, {"size": size, "bold": True, "color": lab_c, "space_after": 2})]
            if it["sub"]:
                paras.append((it["sub"], {"size": 8.5, "color": sub_c, "space_after": 1}))
            if show_n and (it["n"] is not None or "n" in it):   # PACK EXT 2026-09-30: show_n
                val, flagged = _clean(it["n"])
                if val is not None or it["n"] is None:
                    paras.append((fmt_n(val) + ("*" if flagged else ""),
                                  {"size": 9, "bold": True, "color": lab_c}))
            textbox(self.sl, bx + 0.16, y + 0.08, bw - 0.32, h - 0.16, paras,
                    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.04)
            if arrows and i < len(its) - 1:
                _right_arrow(self.sl, bx + bw + 0.06, y + h / 2 - 0.07, gutter - 0.12)
        bottom = y + h
        if auto:
            self.y = bottom + 0.20
        return bottom

    # -------------------------------------------------- branch / split
    def split(self, targets, from_xy=None, y=None, x=None, w=None, h=0.70,
              gutter=GUTTER, color=PRIMARY, size=11, size_sub=8.5, connectors=True):
        """Fan out from one point into N boxes laid across the row.
        targets = [(label, sub, n), ...] or dicts (color= per box).
        from_xy = (x, y) origin of the connectors; defaults to centre above."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        tgs = _norm(targets, ["label", "sub", "n"])
        slots = self.cols(len(tgs), gutter=gutter, x=x, w=w)
        ox, oy = from_xy if from_xy else (x + w / 2, y - 0.26)
        for (bx, bw), t in zip(slots, tgs):
            fill = t.get("color") or color
            if connectors:
                connect(self.sl, ox, oy, bx + bw / 2, y - 0.02)
            rect(self.sl, bx, y, bw, h, fill, radius=0.08)
            ink = _text_on(fill)
            soft = _on_dark(fill)
            paras = [(t["label"], {"size": size, "bold": True, "color": ink, "space_after": 1})]
            if t["sub"]:
                paras.append((t["sub"], {"size": size_sub, "color": soft, "space_after": 1}))
            if t["n"] is not None:
                val, flagged = _clean(t["n"])
                paras.append((fmt_n(val) + ("*" if flagged else ""),
                              {"size": 9.5, "bold": True, "color": ink}))
            textbox(self.sl, bx + 0.18, y + 0.06, bw - 0.36, h - 0.12, paras,
                    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.04)
        bottom = y + h
        if auto:
            self.y = bottom + 0.20
        return bottom

    # -------------------------------------------------- table
    def table(self, rows, header=None, y=None, x=None, w=None, widths=None,
              aligns=None, row_h=0.30, header_h=0.32, size=9.5, zebra=True,
              tone="brand", total=False, note_col=None, band=None):
        """Hand-drawn grid (crisper than a native pptx table).
        rows    list of lists; a cell may be str, number, None -> TBD, or (v, True)
        header  list of column titles
        widths  relative weights, e.g. [3, 1, 1, 2]; defaults to equal
        aligns  per column: "l" | "c" | "r"; numbers default to "r"
        total   render the last row as the template's solid grey summary band
        band    header band fill; defaults to deep teal (PRIMARY) for tone "accent"
                or "brand", otherwise the tone's heading colour
        """
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y0 = self.y if auto else y
        ncol = len(header) if header else max(len(r) for r in rows)
        weights = list(widths) if widths else [1] * ncol
        tot = sum(weights)
        xs, cx = [], x
        for wt in weights:
            cw = w * wt / tot
            xs.append((cx, cw))
            cx += cw
        fill, line, head_c, body_c = TONES[tone]
        A = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
        band = band or (PRIMARY if tone in ("accent", "brand") else head_c)
        band_ink = _text_on(band)
        # a column is numeric if its first real value is a number, so TBD cells
        # line up with the figures around them
        numeric = []
        for i in range(ncol):
            vals = [_clean(r[i])[0] for r in rows if i < len(r)]
            vals = [v for v in vals if v is not None]
            numeric.append(bool(vals) and isinstance(vals[0], (int, float)))
        yy = y0
        if header:
            rect(self.sl, x, yy, w, header_h, band, radius=None)
            first = rows[0] if rows else []
            for i, (cxx, cw) in enumerate(xs):
                if aligns:
                    al = A[aligns[i]]
                else:
                    # match the header to whatever its column's data will do,
                    # so numeric columns read right-aligned end to end
                    cell = _clean(first[i])[0] if i < len(first) else None
                    al = (PP_ALIGN.RIGHT if isinstance(cell, (int, float))
                          else PP_ALIGN.LEFT)
                textbox(self.sl, cxx + 0.10, yy, cw - 0.20, header_h, str(header[i]),
                        size=size - 1, bold=True, color=band_ink, align=al,
                        anchor=MSO_ANCHOR.MIDDLE, font=FONT_HEAD)
            yy += header_h
        for ri, row in enumerate(rows):
            is_total = total and ri == len(rows) - 1
            if is_total:
                rect(self.sl, x, yy, w, row_h, GREY_BASE)
            elif zebra and ri % 2 == 1:
                rect(self.sl, x, yy, w, row_h, BG_NOTE)
            for i, (cxx, cw) in enumerate(xs):
                cell = row[i] if i < len(row) else None
                val, flagged = _clean(cell)
                if val is None:
                    shown, c = "TBD", INK_LIGHT
                elif isinstance(val, str):
                    shown, c = val, INK if i == 0 else INK_SOFT
                else:
                    shown, c = f"{val:,}" + ("*" if flagged else ""), INK
                if aligns:
                    al = A[aligns[i]]
                elif val is None:
                    al = PP_ALIGN.RIGHT if numeric[i] else PP_ALIGN.LEFT
                else:
                    al = PP_ALIGN.RIGHT if isinstance(val, (int, float)) else PP_ALIGN.LEFT
                sz = size if (i == 0 or not isinstance(val, str)) else size - 0.5
                if note_col is not None and i == note_col:
                    c, sz = INK_SOFT, size - 1
                textbox(self.sl, cxx + 0.10, yy, cw - 0.20, row_h, shown,
                        size=sz, bold=(i == 0 or is_total),
                        color=(WHITE if is_total else c),
                        align=al, anchor=MSO_ANCHOR.MIDDLE)
            yy += row_h
            if not is_total:
                hairline(self.sl, x, yy, w, color=RULE, weight=0.5)
        if auto:
            self.y = yy + 0.18
        return yy

    # -------------------------------------------------- native chart
    def chart(self, kind, categories, series, y=None, x=None, w=None, h=None,
              legend=None, labels=False, number_format="#,##0", colors=None,
              gap_width=60, overlap=None, gridlines=True, y_axis=True,
              size=9, max_scale=None, min_scale=None, smooth=False):
        """Native editable pptx chart.
        kind        column | column_stacked | column_stacked_100 | bar | bar_stacked
                    | line | line_markers | area | pie | doughnut
        categories  list of category labels
        series      {name: [values]} or [(name, [values]), ...] or a bare list
        colors      list of RGBColor, one per series (per slice for pie)
        """
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        h = h or max(1.6, min(3.6, CONTENT_B - y - 0.10))
        if isinstance(series, dict):
            series = list(series.items())
        elif series and not isinstance(series[0], (tuple, list)):
            series = [("Series 1", list(series))]
        cd = CategoryChartData()
        cd.categories = list(categories)
        for name, vals in series:
            cd.add_series(name, [None if v is None else v for v in vals])
        gf = self.sl.shapes.add_chart(CHART_KINDS[kind], Inches(x), Inches(y),
                                      Inches(w), Inches(h), cd)
        ch = gf.chart
        ch.font.name = FONT
        ch.font.size = Pt(size)
        ch.font.color.rgb = INK_SOFT
        multi = len(series) > 1
        ch.has_legend = multi if legend is None else legend
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
            ch.legend.font.size = Pt(size - 0.5)
        plot = ch.plots[0]
        try:
            plot.gap_width = gap_width
            if overlap is not None:
                plot.overlap = overlap
            elif "stacked" in kind:
                plot.overlap = 100
        except (ValueError, AttributeError):
            pass
        pal = colors or SERIES_COLORS
        if kind in ("pie", "doughnut"):
            pts = plot.series[0].points
            for i, pt in enumerate(pts):
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = pal[i % len(pal)]
                pt.format.line.color.rgb = WHITE
        else:
            for i, ser in enumerate(plot.series):
                col = pal[i % len(pal)]
                if kind.startswith("line"):
                    ser.format.line.color.rgb = col
                    ser.format.line.width = Pt(2)
                    ser.smooth = smooth
                else:
                    ser.format.fill.solid()
                    ser.format.fill.fore_color.rgb = col
                    ser.format.line.fill.background()
        if labels:
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.number_format = "0.0%" if kind in ("pie", "doughnut") and number_format == "%" else number_format
            dl.number_format_is_linked = False
            dl.font.size = Pt(size - 0.5)
            dl.font.bold = True
            try:
                if kind in ("pie", "doughnut"):
                    dl.position = XL_LABEL_POSITION.OUTSIDE_END
                    dl.font.color.rgb = INK
                elif "stacked" in kind:
                    dl.position = XL_LABEL_POSITION.CENTER
                    dl.font.color.rgb = WHITE
                else:
                    dl.position = XL_LABEL_POSITION.OUTSIDE_END
                    dl.font.color.rgb = INK
            except (ValueError, AttributeError):
                pass
        try:
            va, ca = ch.value_axis, ch.category_axis
            va.visible = bool(y_axis)
            va.has_major_gridlines = bool(gridlines)
            if gridlines:
                va.major_gridlines.format.line.color.rgb = RULE
                va.major_gridlines.format.line.width = Pt(0.5)
            va.major_tick_mark = XL_TICK_MARK.NONE
            va.format.line.fill.background()
            va.tick_labels.font.size = Pt(size - 0.5)
            va.tick_labels.number_format = number_format
            va.tick_labels.number_format_is_linked = False
            if max_scale is not None:
                va.maximum_scale = max_scale
            if min_scale is not None:
                va.minimum_scale = min_scale
            ca.major_tick_mark = XL_TICK_MARK.NONE
            ca.format.line.color.rgb = RULE
            ca.tick_labels.font.size = Pt(size - 0.5)
        except (ValueError, AttributeError):
            pass
        bottom = y + h
        if auto:
            self.y = bottom + 0.16
        return bottom

    # -------------------------------------------------- grid of cells / 2x2
    def matrix(self, cells, col_labels=None, row_labels=None, y=None, x=None,
               w=None, h=None, gutter=0.14, tone="neutral", size=9.5, label_w=1.35):
        """Grid of small boxes: feature comparisons, 2x2 quadrants, option maps.
        cells = [[cell, cell, ...], ...] where cell is str, (head, body) or a dict
        with head / body / tone / color.
        """
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y0 = self.y if auto else y
        nrow = len(cells)
        ncol = max(len(r) for r in cells)
        gx = x + (label_w if row_labels else 0)
        gw = w - (label_w if row_labels else 0)
        head_h = 0.26 if col_labels else 0.0
        avail = (h if h else CONTENT_B - y0 - 0.05) - head_h
        ch_ = (avail - gutter * (nrow - 1)) / nrow
        cw_ = (gw - gutter * (ncol - 1)) / ncol
        if col_labels:
            for j, cl in enumerate(col_labels):
                textbox(self.sl, gx + j * (cw_ + gutter), y0, cw_, head_h, str(cl).upper(),
                        size=8.5, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER,
                        font=FONT_HEAD)
        for i, row in enumerate(cells):
            yy = y0 + head_h + i * (ch_ + gutter)
            if row_labels:
                textbox(self.sl, x, yy, label_w - 0.12, ch_, str(row_labels[i]),
                        size=9, bold=True, color=INK, anchor=MSO_ANCHOR.MIDDLE)
            for j in range(ncol):
                cell = row[j] if j < len(row) else None
                if cell is None:
                    d = {"head": None, "body": None}
                elif isinstance(cell, dict):
                    d = dict(cell)
                elif isinstance(cell, (tuple, list)):
                    d = {"head": cell[0], "body": cell[1] if len(cell) > 1 else None}
                else:
                    d = {"head": cell, "body": None}
                fill, line, head_c, body_c = TONES[d.get("tone", tone)]
                if d.get("color"):
                    fill, head_c = d["color"], _text_on(d["color"])
                    body_c = _on_dark(d["color"])
                    line = None
                bx = gx + j * (cw_ + gutter)
                rect(self.sl, bx, yy, cw_, ch_, fill, line=line, radius=0.05)
                paras = []
                if d.get("head"):
                    paras.append((str(d["head"]), {"size": size, "bold": True,
                                                   "color": head_c, "space_after": 2}))
                if d.get("body"):
                    paras.append((str(d["body"]), {"size": size - 1, "color": body_c}))
                if paras:
                    textbox(self.sl, bx + 0.14, yy + 0.10, cw_ - 0.28, ch_ - 0.20, paras,
                            anchor=MSO_ANCHOR.MIDDLE if len(paras) < 2 else MSO_ANCHOR.TOP,
                            line_spacing=1.04)
        bottom = y0 + head_h + nrow * ch_ + gutter * (nrow - 1)
        if auto:
            self.y = bottom + 0.18
        return bottom

    # -------------------------------------------------- timeline
    def timeline(self, milestones, y=None, x=None, w=None, h=1.05, color=ACCENT_DK, size=9):
        """Horizontal track with evenly spaced milestones.
        milestones = [(when, label, sub), ...] or dicts."""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y0 = self.y if auto else y
        ms = _norm(milestones, ["when", "label", "sub"])
        n = len(ms)
        track_y = y0 + 0.34
        hairline(self.sl, x + 0.10, track_y, w - 0.20, color=RULE, weight=1.5)
        step = (w - 0.20) / max(1, n - 1) if n > 1 else 0
        for i, m in enumerate(ms):
            cx = x + 0.10 + i * step if n > 1 else x + w / 2
            half = min(1.5, (step if step else w) / 2 + 0.35)
            # clamp the label block to the content box so end milestones stay on-page
            lx0 = max(x, cx - half)
            lx1 = min(x + w, cx + half)
            lw = lx1 - lx0
            if m["when"]:
                textbox(self.sl, lx0, y0, lw, 0.24, str(m["when"]),
                        size=8.5, bold=True, color=color, align=PP_ALIGN.CENTER,
                        font=FONT_HEAD)
            dot = rect(self.sl, cx - 0.065, track_y - 0.055, 0.13, 0.13,
                       m.get("color") or color, radius=0.5)
            paras = [(str(m["label"]), {"size": size, "bold": True, "color": INK,
                                        "align": PP_ALIGN.CENTER, "space_after": 1})]
            if m["sub"]:
                paras.append((str(m["sub"]), {"size": size - 1, "color": INK_SOFT,
                                              "align": PP_ALIGN.CENTER}))
            textbox(self.sl, lx0, track_y + 0.16, lw, h - 0.50, paras,
                    line_spacing=1.04)
        bottom = y0 + h
        if auto:
            self.y = bottom + 0.16
        return bottom

    # -------------------------------------------------- legend / key
    def legend(self, items, y=None, x=None, w=None, size=8.5, gutter=0.30):
        """Colour key. items = [(label, color), ...]"""
        x = self.x if x is None else x
        w = self.w if w is None else w
        auto = y is None
        y = self.y if auto else y
        cx = x
        for label, col in items:
            rect(self.sl, cx, y + 0.045, 0.135, 0.135, col, radius=0.25)
            tw = max(0.5, len(str(label)) * size / 110)   # Arial caps run wide
            textbox(self.sl, cx + 0.20, y, tw, 0.22, str(label), size=size, color=INK_SOFT)
            cx += 0.20 + tw + gutter
        bottom = y + 0.24
        if auto:
            self.y = bottom + 0.10
        return bottom


# =====================================================================================
# DECK
# =====================================================================================
class Deck:
    """Presentation wrapper: makes slides, numbers them, validates on save."""

    def __init__(self, brand=None, template=TEMPLATE):
        """Open the VENCLEXTA template. Every slide comes from it.

        template  path to the brand file. The default name is searched for next
                  to this module and in the working directory. Missing file
                  raises - this kit fills the template, it does not replace it.
        """
        self.template_path = self._find_template(template)
        self.prs = Presentation(self.template_path)
        self._masters = list(self.prs.slide_masters)
        self._spare = list(self.prs.slides)   # slides already in the template
        # layouts the template's own slides use: these win when a name repeats
        self._shell = {}
        for sl in self._spare:
            self._shell.setdefault(sl.slide_layout.name, sl.slide_layout)
        self._home = self._home_master()
        self.brand = brand          # rendered as the corner chip
        self.slides = []
        self.warnings = []
        self._used = []             # template slides actually filled

    # -------------------------------------------------- template plumbing
    @staticmethod
    def _find_template(template):
        """Locate the brand file, or explain clearly where it was looked for."""
        if not template:
            raise ValueError(
                "slide_kit fills the VENCLEXTA template; template cannot be None. "
                f"Place {TEMPLATE!r} beside slide_kit_ven.py or pass template=<path>.")
        here = _os.path.dirname(_os.path.abspath(__file__))
        cands = [template] if _os.path.isabs(template) else [
            _os.path.join(here, template), _os.path.abspath(template)]
        tried = list(dict.fromkeys(cands))
        for cand in tried:
            if _os.path.exists(cand):
                return cand
        raise FileNotFoundError(
            "VENCLEXTA template not found. Looked in:\n  " + "\n  ".join(tried) +
            f"\nPlace {TEMPLATE!r} beside slide_kit_ven.py, or pass "
            "Deck(template=<path to the .pptx>).")

    @staticmethod
    def _theme_name(master):
        try:
            blob = master.part.part_related_by(_RT.THEME).blob
            m = _re.search(rb'<a:theme [^>]*name="([^"]*)"', blob)
            return m.group(1).decode("utf-8", "replace") if m else ""
        except (KeyError, AttributeError):
            return ""

    def _is_plain_office(self, master):
        return self._theme_name(master).strip().lower() == "office theme"

    def _home_master(self):
        """The master behind the template's own content slide; failing that, the
        first master that is not the plain Office one."""
        want = LAYOUTS["content"]
        for sl in self._spare:
            if sl.slide_layout.name == want:
                return sl.slide_layout.slide_master
        for m in self._masters:
            if not self._is_plain_office(m):
                return m
        return self._masters[0]

    def _master_order(self):
        """Search order for layout names: home master, other brand masters, and
        the plain Office master last (its layouts carry no VENCLEXTA chrome)."""
        rest = [m for m in self._masters if m is not self._home]
        brand = [m for m in rest if not self._is_plain_office(m)]
        plain = [m for m in rest if self._is_plain_office(m)]
        return [self._home] + brand + plain

    def _find_layout(self, spec):
        if isinstance(spec, tuple):
            mi, name = spec
            for l in self._masters[mi].slide_layouts:
                if l.name == name:
                    return l
            return None
        if spec in self._shell:
            return self._shell[spec]
        for m in self._master_order():
            for l in m.slide_layouts:
                if l.name == spec:
                    return l
        return None

    def _layout(self, role):
        """The template layout backing a role (master-aware, see module notes)."""
        lay = self._find_layout(LAYOUTS.get(role, role))
        if lay is None and role != "content":
            lay = self._find_layout(LAYOUTS["content"])
        if lay is None:
            lay = self._home.slide_layouts[0]
        return lay

    def _take(self, role):
        """Reuse an untouched slide already in the template if it is built on this
        role's layout, otherwise add a fresh slide from that layout. This is what
        makes the kit build ON the template instead of alongside it."""
        lay = self._layout(role)
        for sl in self._spare:
            if sl.slide_layout.part is lay.part:
                self._spare.remove(sl)
                self._used.append(sl)
                self._clear(sl)
                return sl
        return self.prs.slides.add_slide(lay)

    @staticmethod
    def _clear(sl):
        """Empty the placeholders of a reused template slide, leaving its layout
        and any non-placeholder brand art untouched."""
        for sh in list(sl.shapes):
            if sh.is_placeholder and sh.has_text_frame:
                sh.text_frame.clear()

    @staticmethod
    def _clone_layout_ph(sl, *types):
        """Give a slide the layout's placeholder of one of `types` when the slide
        itself lacks it (the template's content shell ships with no title). The
        clone keeps its link to the layout, so position and style inherit; the
        layout's prompt text is dropped. Returns the new slide shape or None."""
        for ph in sl.slide_layout.placeholders:
            if ph.placeholder_format.type in types:
                el = _copy.deepcopy(ph._element)
                tx = el.find(_qn("p:txBody"))
                if tx is not None:
                    for p in tx.findall(_qn("a:p")):
                        tx.remove(p)
                    tx.append(_parse_xml(
                        '<a:p xmlns:a="http://schemas.openxmlformats.org/'
                        'drawingml/2006/main"/>'))
                sl.shapes._spTree.append(el)
                for sh in sl.shapes:
                    if sh._element is el:
                        return sh
        return None

    @staticmethod
    def _prune_empty(sl):
        """Remove placeholders left empty (unused body / subtitle slots), so no
        'Click to add text' prompt shows in PowerPoint. Slide numbers stay."""
        keep = (PP_PLACEHOLDER.SLIDE_NUMBER,)
        for sh in list(sl.shapes):
            if not sh.is_placeholder or sh.placeholder_format.type in keep:
                continue
            if getattr(sh, "has_chart", False) or getattr(sh, "has_table", False):
                continue
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                continue
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                sh._element.getparent().remove(sh._element)

    def _page_number(self, sl, page=None):
        """Clone the layout's slide-number placeholder so numbering is a live
        PowerPoint field. Page numbers are the one piece of footer chrome that
        does not inherit - PowerPoint needs the placeholder on the slide itself.
        Static text is used only if a layout has no such placeholder."""
        for ph in sl.slide_layout.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                if any(sh.is_placeholder and sh.placeholder_format.type
                       == PP_PLACEHOLDER.SLIDE_NUMBER for sh in sl.shapes):
                    return None
                el = _copy.deepcopy(ph._element)
                sl.shapes._spTree.append(el)
                return el
        page = self._page_no(sl) if page is None else page
        px, py, pw = PAGE_XY
        return textbox(sl, px, py, pw, 0.16, str(page), size=7,
                       color=PRIMARY, align=PP_ALIGN.CENTER)

    def _reorder(self):
        """Put slides in the order they were created. Needed because a reused
        template slide keeps its original position in the file, so consuming the
        shells out of order would otherwise scramble the deck."""
        ids = self.prs.slides._sldIdLst
        by_id = {el.id: el for el in list(ids)}
        for sl in (s.sl for s in self.slides):
            el = by_id.get(sl.slide_id)
            if el is not None:
                ids.remove(el)
                ids.append(el)

    def _drop_unused(self):
        """Remove template shell slides that were never filled, so the output
        has no stray blanks from the brand file."""
        if not self._spare:
            return
        spare_ids = {sl.slide_id for sl in self._spare}
        sldIdLst = self.prs.slides._sldIdLst
        for el in list(sldIdLst):
            if el.id in spare_ids:
                sldIdLst.remove(el)
        self._spare = []

    # -------------------------------------------------- slide factories
    def _blank(self):
        return self._take("content")

    def slide(self, title=None, kicker=None, brand=None, role="content"):
        s = Slide(self, self._take(role), title, kicker,
                  self.brand if brand is None else brand)
        self.slides.append(s)
        return s

    @staticmethod
    def _team_box(sl):
        """The cover's team / group text box on the yellow band (a plain text box
        in the template, not a placeholder)."""
        for sh in sl.shapes:
            if (not sh.is_placeholder and sh.has_text_frame and sh.top is not None
                    and 4.4 < sh.top.inches < 6.3 and sh.left.inches < 1.5):
                return sh
        return None

    @staticmethod
    def _no_bullet(para):
        pPr = para._p.get_or_add_pPr()
        pPr.set("marL", "0")
        pPr.set("indent", "0")
        for tag in ("a:buChar", "a:buAutoNum", "a:buNone"):
            for el in pPr.findall(_qn(tag)):
                pPr.remove(el)
        # PACK FIX 2026-09-29: buNone must precede tabLst / defRPr / extLst (OOXML sequence);
        # appended after them, PowerPoint ignored it and drew a bullet on the cover team line.
        bu = _parse_xml('<a:buNone xmlns:a="http://schemas.openxmlformats.org/'
                        'drawingml/2006/main"/>')
        after = [pPr.find(_qn(t)) for t in ("a:tabLst", "a:defRPr", "a:extLst")]
        after = [el for el in after if el is not None]
        if after:
            after[0].addprevious(bu)
        else:
            pPr.append(bu)

    def title_slide(self, title, subtitle=None, meta=None, team=None,
                    disclaimer=None, size=40):
        """Fill the template's cover. The yellow and teal waves, the logos and the
        confidentiality line are all on the "2_Title Slide" layout - this writes
        the title, the subtitle / date and the team line and nothing more. To
        change the cover art, change it in the template.

        subtitle  first line under the title (the template's "MONTH" slot)
        meta      further small lines under the subtitle
        team      the bold line on the yellow band (template: "APEX Analytics").
                  None keeps whatever the template has, "" removes it.
        """
        sl = self._take("title")
        s = Slide(self, sl)
        ph = s._title_ph() or self._clone_layout_ph(
            sl, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE)
        tw = 8.463
        n_lines = _est_lines(title, tw, size)
        th = 0.60 * size / 40 * n_lines + 0.08
        ty = max(0.95, 2.76 - th)             # grows upward, clear of the top art
        if ph is not None:
            _place(ph, x=0.444, y=ty, w=tw, h=th)
            _fill_ph(ph, title, size=size, bold=True, color=COVER_INK,
                     font=FONT_HEAD, line_spacing=0.95, anchor=MSO_ANCHOR.BOTTOM)
        else:
            textbox(sl, 0.444, ty, tw, th, title, size=size, bold=True,
                    color=COVER_INK, line_spacing=0.95, font=FONT_HEAD,
                    anchor=MSO_ANCHOR.BOTTOM)
        sub_ph = s._ph(PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY)
        lines = ([subtitle] if isinstance(subtitle, str) else list(subtitle or []))
        lines += [meta] if isinstance(meta, str) else list(meta or [])
        if lines:
            paras = [(lines[0], {"size": 14, "color": INK, "space_after": 4})]
            paras += [(m, {"size": 10, "color": INK_SOFT, "space_after": 2})
                      for m in lines[1:]]
            sh_ = 0.30 + 0.19 * (len(lines) - 1)
            if sub_ph is not None:
                _place(sub_ph, x=0.444, y=2.84, w=tw, h=sh_)
                _fill_ph(sub_ph, paras, size=14, color=INK, font=FONT,
                         line_spacing=1.1)
                for p in sub_ph.text_frame.paragraphs:
                    self._no_bullet(p)
            else:
                textbox(sl, 0.444, 2.84, tw, sh_, paras, line_spacing=1.1)
        box = self._team_box(sl)
        if team == "" and box is not None:
            box._element.getparent().remove(box._element)
        elif team:
            if box is None:
                box = textbox(sl, 0.468, 5.218, 6.444, 1.222, "", anchor=MSO_ANCHOR.MIDDLE)
            _fill_ph(box, team, size=18, bold=True, color=COVER_INK, font=FONT_HEAD,
                     anchor=MSO_ANCHOR.MIDDLE, line_spacing=0.9)
            for p in box.text_frame.paragraphs:
                self._no_bullet(p)
        if disclaimer:
            textbox(sl, 0.444, 0.35, 7.5, 0.30, disclaimer, size=9,
                    color=INK_LIGHT)
        s._has_footer = True
        self.slides.append(s)
        return s

    def section(self, label, sub=None, number=None, size=32):
        """Divider slide, filling the template's "Breaker Slide" layout. The
        yellow wave, footer rule and VENCLEXTA mark come with that layout. The
        layout sets the label in capitals, bottom-anchored at y=3.13."""
        sl = self._take("section")
        s = Slide(self, sl)
        ph = s._title_ph() or self._clone_layout_ph(sl, PP_PLACEHOLDER.TITLE)
        x, w, base = 0.778, 8.30, 3.13
        lab_h = 0.50 * size / 32 * _est_lines(label.upper(), w, size)
        if ph is not None:
            _place(ph, x=x, y=base - lab_h - 0.04, w=w, h=lab_h + 0.04)
            _fill_ph(ph, label, size=size, color=PRIMARY, font=FONT_HEAD,
                     line_spacing=1.0, anchor=MSO_ANCHOR.BOTTOM)
        else:
            textbox(sl, x, base - lab_h, w, lab_h, label.upper(), size=size,
                    color=PRIMARY, line_spacing=1.0, font=FONT_HEAD,
                    anchor=MSO_ANCHOR.BOTTOM)
        if number is not None:
            textbox(sl, x, base - lab_h - 0.62, 3.0, 0.46, f"{number:02d}", size=26,
                    bold=True, color=ACCENT_DK, font=FONT_HEAD)
        if sub:
            textbox(sl, x, base + 0.16, 6.4, 0.7, sub, size=13,
                    color=INK_SOFT, line_spacing=1.15)
        self._page_number(sl)
        s._has_footer = True
        self.slides.append(s)
        return s

    def _page_no(self, sl):
        for i, s in enumerate(self.prs.slides, start=1):
            if s is sl:
                return i
        return 0

    # -------------------------------------------------- validation
    def validate(self, check_collisions=False, verbose=True):
        """Warn on shapes outside the printable area, content past the footer rule
        and (optionally) overlapping text boxes. Returns list of warnings."""
        self.warnings = []
        # text margins: page edge less a hair; the corner art and the yellow
        # footer rule are checked separately below
        L, R, T, B = 0.35, 13.25, 0.05, 7.45
        kx0, ky0, kx1, ky1 = CORNER_ART
        # cover and breaker layouts have their own art; skip the corner check there
        chrome_free = (self._layout("title").part, self._layout("section").part)
        SW = self.prs.slide_width.inches
        SH = self.prs.slide_height.inches
        for idx, s in enumerate(self.slides, start=1):
            boxes = []
            for sh in s.sl.shapes:
                if sh.left is None or sh.top is None:
                    continue
                x0, y0 = sh.left.inches, sh.top.inches
                x1 = x0 + (sh.width.inches if sh.width else 0)
                y1 = y0 + (sh.height.inches if sh.height else 0)
                name = getattr(sh, "text", "") or sh.shape_type
                tag = str(name).replace("\n", " ")[:38]
                is_text = sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX
                if x0 < -0.01 or y0 < -0.01 or x1 > SW + 0.01 or y1 > SH + 0.01:
                    # anything hanging off the physical page is always wrong
                    self.warnings.append(
                        f"slide {idx}: off-slide ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})  [{tag}]")
                elif is_text and (x0 < L - 0.01 or x1 > R + 0.01
                                  or y0 < T - 0.01 or y1 > B + 0.01):
                    # margins apply to text only; full-bleed fills are intentional
                    self.warnings.append(
                        f"slide {idx}: text outside margins ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})  [{tag}]")
                if is_text and s.sl.slide_layout.part not in chrome_free:
                    if x1 > kx0 + 0.01 and y0 < ky1 - 0.01:
                        self.warnings.append(
                            f"slide {idx}: text under the corner art ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f})  [{tag}]")
                    if y0 < FOOTER_RULE - 0.01 < y1 - 0.02:
                        self.warnings.append(
                            f"slide {idx}: text crosses the footer rule at {FOOTER_RULE}in  [{tag}]")
                if is_text:
                    boxes.append((x0, y0, x1, y1, tag))
            if s.y > CONTENT_B + 0.02:
                self.warnings.append(
                    f"slide {idx}: content cursor at {s.y:.2f}in, past the {CONTENT_B}in limit")
            if not s._has_footer:
                self.warnings.append(f"slide {idx}: no .footer() call (no page number / sources)")
            if check_collisions:
                for i in range(len(boxes)):
                    for j in range(i + 1, len(boxes)):
                        ax0, ay0, ax1, ay1, at = boxes[i]
                        bx0, by0, bx1, by1, bt = boxes[j]
                        ox = min(ax1, bx1) - max(ax0, bx0)
                        oy = min(ay1, by1) - max(ay0, by0)
                        # 0.10in slack: text boxes are sized to estimated line
                        # counts, so small nominal overlaps do not render as any
                        if ox > 0.10 and oy > 0.10:
                            self.warnings.append(
                                f"slide {idx}: text overlap {ox:.2f}x{oy:.2f}in  [{at}] / [{bt}]")
        if verbose:
            for wmsg in self.warnings:
                print("  ! " + wmsg)
        return self.warnings

    def save(self, path, validate=True, check_collisions=False, strict=False):
        for s in self.slides:
            self._prune_empty(s.sl)
        self._drop_unused()
        self._reorder()
        if validate:
            self.validate(check_collisions=check_collisions)
            if strict and self.warnings:
                raise ValueError(f"{len(self.warnings)} layout warning(s); refusing to save")
        self.prs.save(path)
        print(f"saved {path}  ({len(self.slides)} slides, {len(self.warnings)} warning(s))")
        return path
