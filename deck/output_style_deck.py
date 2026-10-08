"""output_style_deck - AML pack conventions on top of slide_kit_ven.

slide_kit_ven.py is the VEN team's kit and stays verbatim: it owns the template, palette, geometry,
components and the save-time layout check. This module only adds what is specific to this pack:

    new_deck()          Deck on deck/VEN_TEMPLATE.pptx (found from any working directory)
    carry_lines()       the standard footer lines every analysis slide must carry
    sort_categories()   stable category order for tables and charts
    *_ORDER             the pack's category orders (LoT, cohort, backbone group, account group)
    out_path()          where a generated deck goes: outputs/<YYYY-MM-DD>_<topic>/<file>.pptx

Unknown values render "TBD", never an invented figure (the kit's convention). Orders that exist in
config/ are read from there, so they cannot drift from the notebooks.
"""
import datetime as _dt
import os as _os

from slide_kit_ven import Deck

HERE = _os.path.dirname(_os.path.abspath(__file__))
PACK = _os.path.dirname(HERE)
TEMPLATE_PATH = _os.path.join(HERE, "VEN_TEMPLATE.pptx")


def _config_list(file, *keys, default=()):
    """A list from config/<file> (read only); the default if PyYAML or the key is missing."""
    try:
        import yaml
        with open(_os.path.join(PACK, "config", file), encoding="utf-8") as fh:
            node = yaml.safe_load(fh)
        for k in keys:
            node = node[k]
        return tuple(node)
    except Exception:
        return tuple(default)


# ------------------------------------------------------------------ category orders
LOT_ORDER = ("1L", "2L", "3L", "4L+")                       # lines bucketed at 4L+
COHORT_ORDER = ("IC_INELIG", "IC_ELIG")                      # published cohort first
BACKBONE_GROUP_ORDER = ("VENCLEXTA", "HMA", "OTHER NOVEL AGENTS")
ACCOUNT_GROUP_ORDER = _config_list(                          # dashboard account groups
    "nps_dashboard_legacy.yaml", "account_type", "group_hierarchy",
    default=("Academic", "Academic Satellite", "Larger Community", "Smaller Community",
             "Federal", "Not Available"))
ACCOUNT_ROLLUP_ORDER = ("Academic", "Community", "Not Available")   # Ipsos / month rollup
LAST = ("Other", "OTHER", "Unknown", "UNKNOWN", "Not Available", "TBD", "Total")


def sort_categories(items, order=(), last=LAST):
    """Known categories in `order`, then unlisted ones alphabetically, then catch-alls
    (Other / Unknown / Not Available / Total) at the end in that order."""
    items = list(dict.fromkeys(items))
    rank = {v: i for i, v in enumerate(order)}
    tail = {v: i for i, v in enumerate(last)}
    return sorted(items, key=lambda v: (
        2 if v in tail and v not in rank else (0 if v in rank else 1),
        rank.get(v, tail.get(v, 0)), str(v)))


# ------------------------------------------------------------------ footer
def carry_lines(source="SHA (SHA_PTD)", build=None, period=None, population=None,
                gates=None, intensity="legacy rule", kbt=None, extra=None):
    """Standard footer for an analysis slide (CLAUDE.md "State the data source ..." rule).
    Every argument left as None prints TBD, except `extra` and `kbt`, which are optional."""
    tbd = lambda v: "TBD" if v in (None, "") else v
    lines = [f"Source: {tbd(source)} | build {tbd(build)} | period {tbd(period)}",
             f"Population: {tbd(population)} | gates: {tbd(gates)} | intensity: {tbd(intensity)}"
             + (f" | KBT {kbt}" if kbt else "")]
    if extra:
        lines += [extra] if isinstance(extra, str) else list(extra)
    lines.append("Lines of therapy are claims-derived, not physician-documented. Aggregates only.")
    return lines


# ------------------------------------------------------------------ deck + output location
def new_deck(brand="VEN | AML", template=TEMPLATE_PATH):
    """A Deck on the pack's copy of the VENCLEXTA template."""
    return Deck(brand=brand, template=template)


def out_path(topic, filename, date=None):
    """outputs/<YYYY-MM-DD>_<topic>/<filename>, created if missing (CLAUDE.md "Generated files")."""
    date = date or _dt.date.today().isoformat()
    folder = _os.path.join(PACK, "outputs", f"{date}_{topic}")
    _os.makedirs(folder, exist_ok=True)
    return _os.path.join(folder, filename)
