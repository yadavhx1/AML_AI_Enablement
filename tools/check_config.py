"""Check config/*.yaml against the hardcoded values in scripts/Notebooks/*.ipynb."""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep config/ free of __pycache__

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "config"))
from load_config import load_config  # noqa: E402

NB = ROOT / "scripts/Notebooks"
errors = []


def src(name):
    cells = json.loads((NB / name).read_text(encoding="utf-8"))["cells"]
    return ["".join(c["source"]) for c in cells]


def quoted(text):
    return re.findall(r"'([^']*)'", text)


def check(cond, msg):
    if not cond:
        errors.append(msg)


c1 = load_config("tx_table.yaml")
c4 = load_config("intensity_lot.yaml")
c5 = load_config("eligibility.yaml")
RUN_ORDER = ["AML_LOT_TX_TABLE", "AML_LOT_SOB_EPISODE", "AML_LOT_REGIMEN", "AML_LOT_PATIENT_INTENSITY_LOT",
             "AML_PATIENT_ELIGIBILITY"]
n1, n2, n3, n4, n5 = (src(f"{name}.ipynb") for name in RUN_ORDER)


def cell4(marker):
    """LoT notebook cell containing `marker` (cells are found by content, not position)."""
    found = [c for c in n4 if marker in c]
    if not found:
        errors.append(f"LoT notebook cell with {marker!r} not found")
        return ""
    return found[0]

# Table names: every notebook global must equal the config name for that notebook's suffix.
for name, cells, cfg in [("01", n1, c1), ("04", n4, c4), ("05", n5, c5)]:
    g = next(s for s in cells if "tx_tbl_name =" in s)
    for var, tmpl in re.findall(r"^(\w+)\s*=\s*'(\{cws\}\.[^']+)'", g, re.M):
        actual = tmpl.replace("{cws}", cfg["schemas"]["cws"])
        expected = cfg["tables"].get(var) or cfg["schemas"].get(var)
        check(actual == expected, f"{name}: table {var}: notebook {actual} != config {expected}")

# Codes.
check(quoted(re.search(r"IN\s*\((.*?)\)", n1[8], re.S).group(1)) == c1["codes"]["aml_dx_full"], "aml_dx_full")
check(list(eval(re.search(r"aml_dx = (\(.*?\))", n1[5]).group(1))) == c1["codes"]["aml_dx_rr"], "aml_dx_rr")
check(quoted(re.search(r"mastered_product_name IN \((.*?)\)", n1[13], re.S).group(1)) == c1["products"]["basket"],
      "basket")

# Grace and PX DOS.
g = {}
for prods, val in re.findall(r"WHEN FINAL_PRODUCT_NAME IN \(([^)]*)\) THEN (\d+)\s*\n", n1[18].split("END AS GRACE_VALUE")[0]):
    for p in quoted(prods):
        g[p] = int(val)
check(g == c1["grace_days"], f"grace mismatch: {set(g.items()) ^ set(c1['grace_days'].items())}")
px_block = n1[18].split("WHEN NATIVE_TYPE = 'PX'")[1].split("END AS DOS_FINAL")[0]
d = {}
for lhs, val in re.findall(r"WHEN FINAL_PRODUCT_NAME (?:=|IN) (\('[^)]*\)|'[^']*') THEN (\d+)", px_block):
    for p in quoted(lhs):
        d[p] = int(val)
check(d == c1["dos"]["px"], f"PX DOS mismatch: {set(d.items()) ^ set(c1['dos']['px'].items())}")

# Backbone hierarchies (first-match order).
inelig = [(p, v) for p, v in re.findall(r"^\s*WHEN REGIMEN RLIKE '([^']+)' THEN '([^']+)'", cell4("REGIMEN RLIKE 'VENCLEXTA'"), re.M)]
check(inelig == [(ps[0], v) for ps, v in c4["ic_inelig"]["backbone_hierarchy"]], "IC_INELIG backbone order")
elig = [(tuple(re.findall(r"LIKE '%([^%]+)%'", cond)), v)
        for cond, v in re.findall(r"^\s*WHEN (REGIMEN LIKE .*?) THEN\s+'([^']+)'", cell4("WHEN REGIMEN LIKE '%HI-DAC%' OR REGIMEN LIKE '%S-DAC%'"), re.M)]
check(elig == [(tuple(ps), v) for ps, v in c4["ic_elig"]["backbone_hierarchy"]], "IC_ELIG backbone order")

# legacy rule list (active, de-duplicated, in order).
ra = []
for p in re.findall(r"^\s*WHEN REGIMEN LIKE '%([^%]+)%' THEN 0", cell4("CREATE TABLE {patient_group}"), re.M):
    if p not in ra:
        ra.append(p)
check(ra == c4["intensity_rule_a"]["ic_elig_only_products"], "legacy rule product list")

# new definition.
check(eval(re.search(r"IC_ELIG_PRODUCTS = (\{.*?\})", cell4("IC_ELIG_PRODUCTS = {"), re.S).group(1))
      == set(c4["intensity_rule_b"]["ic_elig_products"]), "new definition IC_ELIG set")
check(eval(re.search(r"FORCED_INELIG_PRODUCTS = (\{.*?\})", cell4("IC_ELIG_PRODUCTS = {")).group(1))
      == set(c4["intensity_rule_b"]["forced_inelig_products"]), "new definition forced set")
check(eval(re.search(r"ic_elig_hierarchy = (\[.*?\])", cell4("ic_elig_hierarchy = ["), re.S).group(1)) == c4["intensity_rule_b"]["ic_elig_rank"],
      "new definition elig rank")
check(eval(re.search(r"ic_inelig_hierarchy = (\[.*?\])", cell4("ic_elig_hierarchy = ["), re.S).group(1))
      == c4["intensity_rule_b"]["ic_inelig_rank"], "new definition inelig rank")
check("age <= 65" in cell4("IC_ELIG_PRODUCTS = {") and c4["intensity_rule_b"]["age_threshold"] == 65, "new definition age threshold")
check("PREV_GAP > 90" in cell4("REGIMEN RLIKE 'VENCLEXTA'") and c4["lot"]["gap_new_line_days"] == 90, "90-day gap")

# AML_LOT_SOB_EPISODE / 03 pldlib arguments.
sob_src = n2[9]
for k, v in load_config("sob_episode.yaml")["sob"].items():
    if isinstance(v, str) and k not in ("src_input_table", "temp_view", "output_table", "data_period"):
        check(f"{k}='{v}'" in sob_src.replace(" ", "").replace("\t", "") or f"{k}='{v}'".replace(" ", "")
              in sob_src.replace(" ", "").replace("\t", ""), f"sob arg {k}")
check('"202210"' in sob_src, "sob DATA_PERIOD")
reg_src = n3[8].replace(" ", "").replace("\t", "")
for k, v in load_config("regimen.yaml")["regimen"].items():
    if k in ("src_input_tbl", "temp_view", "output_table"):
        continue
    check(f"{k}='{v}'".replace(" ", "") in reg_src, f"regimen arg {k}={v}")

# AML_PATIENT_ELIGIBILITY. Cells are located by content (the semester refactor changed their positions).
def cell5(marker):
    found = [s for s in n5 if marker in s]
    check(bool(found), f"eligibility notebook cell with {marker!r} not found")
    return found[0] if found else ""


final_cell = cell5("SURGICAL_code IN")
sct = quoted(re.search(r"SURGICAL_code IN\s*\((.*?)\)", final_cell, re.S).group(1)) if final_cell else []
check(sct == c5["final_flags"]["sct"]["px_codes"], f"SCT px codes ({len(sct)})")
check("<= 60" in final_cell and c5["final_flags"]["dx_tx_diff_max_days"] == 60, "Dx-Tx 60 days")
check("months=-6" in cell5("relativedelta(months=-6)") and c5["data_cut"]["exclusion_offset_months"] == -6,
      "exc_dt offset")
mx_tbl, rx_tbl = (c5["activity_tables"][k].split(".")[1] for k in ("mx_exact", "rx_exact"))
check(bool(cell5(f"CREATE TABLE Z_ABV_CWS_MABI_ONC_ANALYTICS.{mx_tbl} AS")), "mx exact-date table")
check(bool(cell5(f"CREATE TABLE Z_ABV_CWS_MABI_ONC_ANALYTICS.{rx_tbl} AS")), "rx exact-date table")
check(f"MX_ACT = 'Z_ABV_CWS_MABI_ONC_ANALYTICS.{mx_tbl}'" in cell5("MX_ACT = "), "semester setup Mx table")
check(f"RX_ACT = 'Z_ABV_CWS_MABI_ONC_ANALYTICS.{rx_tbl}'" in cell5("RX_ACT = "), "semester setup Rx table")

# Semester methodology: the notebook reads semester_type from eligibility.yaml and every flag goes through it.
import semester as sem  # noqa: E402

check(sem.resolve_semester_types(c5.get("semester")) is not None, "semester_type resolves")
check("resolve_semester_types(elig_cfg.get('semester'))" in cell5("resolve_semester_types"),
      "notebook reads semester_type from config")
calls = re.findall(r"build_flag\('(\w+)', '(\w+)'", "\n".join(n5))
expected = {"elig_pats": "dx_lookback", "elig_pats_tx_txl_mx": "journey_continuity",
            "elig_pats_tx_txl_rx": "journey_continuity", "elig_pats_tx_ven": "ven_lookback",
            "elig_pats_tx_rx_ven": "ven_lookback", "elig_pats_tx_txl_mx_ven": "journey_continuity",
            "elig_pats_tx_txl_rx_ven": "journey_continuity"}
check(dict(calls) == expected and len(calls) == 7, f"7 flag checks routed by semester_type: {calls}")
check(not any("toPandas()" in s and "remaining_patients_to_be_checked" in s for s in n5),
      "continuity flags no longer use the pandas merge")

# NPS dashboard notebook (metric nps_dashboard_legacy): table names, rank lists, summary settings.
c6 = load_config("nps_dashboard_legacy.yaml")
n6 = src("AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb")

def cell6(marker):
    """Dashboard notebook cell containing `marker` (cells are found by content, not position)."""
    found = [c for c in n6 if marker in c]
    if not found:
        errors.append(f"dashboard notebook cell with {marker!r} not found")
        return ""
    return found[0]

g6 = cell6("reg_npi_aci='{cws}")
for var, tmpl in re.findall(r"^(\w+)\s*=\s*'(\{cws\}\.[^']+)'", g6, re.M):
    actual = tmpl.replace("{cws}", c6["schemas"]["cws"])
    expected = c6["tables"].get(var) or c6["schemas"].get(var)
    check(actual == expected, f"06: table {var}: notebook {actual} != config {expected}")
check(f"reltio_tbl = '{c6['schemas']['reltio_tbl']}'" in g6, "06: reltio_tbl")
# Inputs are set once in the definition setup cell (legacy names) and used in the LoT / flags cells.
dash_setup = cell6("INTENSITY_DEFINITION = idef.definition(dcfg)")
check(c6["tables"]["lot_regimen_group"].split(".")[1] in dash_setup
      and c6["tables"]["patient_group"].split(".")[1] in dash_setup, "06: legacy LoT grouping / cohort inputs")
check(c6["tables"]["elig_flags_final"].split(".")[1] in dash_setup, "06: legacy flags input")
check("from {lot_grouping_in} A" in cell6("REGIMEN_LOT_TBL = spark.sql("), "06: LoT cell uses lot_grouping_in")
check("from {flags_in}" in cell6("elig_flag_df = spark.sql("), "06: flags cell uses flags_in")
check(eval(re.search(r"ic_elig_hierarchy = (\[.*?\])", cell6("ic_elig_hierarchy = ["), re.S).group(1)) == c6["line_backbone"]["ic_elig_rank"],
      "06: IC_ELIG rank list")
check(eval(re.search(r"ic_inelig_hierarchy = (\[.*?\])", cell6("ic_elig_hierarchy = ["), re.S).group(1))
      == c6["line_backbone"]["ic_inelig_rank"], "06: IC_INELIG rank list")
check(f'return "{c6["line_backbone"]["unmatched_backbone"]}"' in cell6("ic_elig_hierarchy = ["), "06: unmatched backbone")
hma = quoted(re.search(r"BACKBONE IN \((.*?)\) THEN 'HMA'", cell6("BACKBONE IN (")).group(1))
check(hma == c6["backbone_group"]["hma"] and sorted(hma) == sorted(c6["hcp_attribution"]["hma_products"]), "06: HMA products")
check(f"SUMMARY_START_YEAR = {c6['summary']['start_year']}" in cell6("SUMMARY_TIME_BASIS = "), "06: summary start year")
check(f"SUMMARY_TIME_BASIS = '{c6['summary']['time_basis']}'" in cell6("SUMMARY_TIME_BASIS = "), "06: summary time basis")
check(f"SUMMARY_DIMS = {c6['summary']['dims']}" in cell6("SUMMARY_TIME_BASIS = "), "06: summary dims")
check(any(f"TO_DATE('{c6['indexing']['reporting_floor']}')" in c for c in n6), "06: reporting floor")
check(f">= {c6['account_type']['larger_community_min_decile']} THEN 'Larger Community'" in cell6("THEN 'Larger Community'"), "06: decile cut")

# IC Eligible / Ineligible definition switch (run.intensity_definition, default legacy).
import intensity_definition as idef  # noqa: E402

for f in ("intensity_lot.yaml", "eligibility.yaml", "nps_dashboard_legacy.yaml"):
    check(idef.definition(load_config(f)) == "legacy", f"intensity_definition default is legacy ({f})")
check("INTENSITY_DEFINITION = idef.definition(cfg)" in "\n".join(n4), "LoT notebook reads intensity_definition")
check(any("if INTENSITY_DEFINITION == 'new':" in s and "final_patient_group" in s and "PATIENT_INTENSITY_UPDATED" in s
          for s in n4), "LoT notebook has the new-definition pass 2")
check("INTENSITY_DEFINITION = idef.definition(icfg)" in "\n".join(n5), "eligibility notebook reads intensity_definition")
check("FROM {rule_b_tbl}" in "\n".join(n5), "eligibility reads the definition-aware class table")
check("INTENSITY_DEFINITION = idef.definition(dcfg)" in "\n".join(n6), "dashboard notebook reads intensity_definition")
check(any("from {lot_grouping_in} A" in s and "SELECT * FROM {cohort_in}" in s for s in n6),
      "dashboard reads definition-aware grouping and cohort")
check(any("from {flags_in}" in s for s in n6), "dashboard reads definition-aware flags")

print("config check:", "PASS" if not errors else "FAIL")
for e in errors:
    print("  -", e)
sys.exit(1 if errors else 0)
