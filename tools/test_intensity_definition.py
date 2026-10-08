"""Check the IC eligible / ineligible definition switch (run.intensity_definition) without Spark.

    python tools/test_intensity_definition.py

The three affected notebooks are executed cell by cell against a stub Spark session that records
every SQL statement instead of running it. That checks:

1. legacy (default): the SQL the notebooks send is identical to the notebooks before the switch was
   added (backups in ../backup_pre_intensity_definition/), so a legacy run is unchanged;
2. new: the LoT notebook writes scratch (_P1LEGACY) then _NEWDEF tables and never touches a legacy
   output; eligibility and the NPS dashboard read and write _NEWDEF tables only;
3. the new-definition pass 2 rebuilds lines from the new cohort (PATIENT_INTENSITY_UPDATED) with the same
   line SQL as the legacy cells;
4. config resolution (default legacy, unknown value raises).

pandas steps run on a tiny frame so the classification code executes. No database is touched.
"""
import contextlib
import io
import json
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT.parent / "backup_pre_intensity_definition" / "notebooks"
NBDIR = ROOT / "scripts" / "Notebooks"
sys.path.insert(0, str(ROOT / "config"))
import intensity_definition as idef  # noqa: E402

import pandas as pd  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


# ------------------------------------------------------------------ stub Spark
class StubDF:
    def __init__(self, log, sql=""):
        self.log, self.sql = log, sql

    def createOrReplaceTempView(self, name):
        self.log.append(("VIEW", name))

    def toPandas(self):
        # Enough columns for every pandas step in these notebooks.
        return pd.DataFrame({
            "PATIENT_GID": ["P1", "P2"], "LOT": [1, 1],
            "REGIMEN": ["AZACITIDINE, VENCLEXTA", "S-DAC"],
            "REGIMEN_START_DATE": [pd.Timestamp("2025-01-01")] * 2,
            "REGIMEN_END_DATE": [pd.Timestamp("2025-06-01")] * 2,
            "LOT_REGIMEN_GROUP": ["AZACITIDINE, VENCLEXTA", "S-DAC"],
            "LOT_START_DATE": [pd.Timestamp("2025-01-01")] * 2, "LOT_END_DATE": [pd.Timestamp("2025-06-01")] * 2,
            "SOURCE_PATIENT_HIPAA_BIRTH_YEAR": ["1950", "1980"],
            "FIRST_DX": [pd.Timestamp("2024-12-01")] * 2,
            "PATIENT_INTENSITY_GROUP": ["IC_INELIG", "IC_ELIG"],
            "CLAIM_DATE": [pd.Timestamp("2025-02-01")] * 2,
            "PATIENT_TO_BE_ELIG_PERIOD": [pd.Timestamp("2025-06-01")] * 2,
            "PREV_PATIENT_TO_BE_ELIG_PERIOD": [pd.Timestamp("2025-01-01")] * 2,
            "ELIG_START": [pd.Timestamp("2025-01-01")] * 2, "ELIG_END": [pd.Timestamp("2025-06-01")] * 2,
        })

    def first(self):
        return [__import__("datetime").date(2026, 6, 30)]

    def show(self, *a, **k):
        pass

    def __getattr__(self, name):  # any other DataFrame method is a no-op returning self
        return lambda *a, **k: self


class StubSpark:
    def __init__(self, log):
        self.log = log
        self.sparkContext = types.SimpleNamespace(addPyFile=lambda *a: None)
        self.conf = types.SimpleNamespace(set=lambda *a: None)

    def sql(self, q):
        q = re.sub(r"--[^\n]*", "", q)  # drop SQL line comments: they are not executed
        self.log.append(("SQL", " ".join(q.split())))
        return StubDF(self.log, q)

    def createDataFrame(self, df):
        return StubDF(self.log)


def run_notebook(path, intensity, cell_limit=None):
    """Execute code cells; return the recorded log. Cells that fail on stub data are skipped."""
    nb = json.loads(path.read_bytes().decode("utf-8"))
    log = []
    spark = StubSpark(log)
    fake = {
        "findspark": types.SimpleNamespace(init=lambda *a: None),
        "pyspark": types.ModuleType("pyspark"),
        "pyspark.sql": types.SimpleNamespace(SparkSession=None),
        "pyspark.sql.functions": types.SimpleNamespace(year=None, month=None, col=None),
        "pldlib": types.SimpleNamespace(stencil=None),
    }
    saved = {k: sys.modules.get(k) for k in fake}
    sys.modules.update(fake)
    import load_config as lc
    real_load = lc.load_config

    def load_with_override(name, overrides=None):
        o = {"run": {"intensity_definition": intensity}}
        if overrides:
            o.update(overrides)
        return real_load(name, o)

    lc.load_config = load_with_override
    g = {"spark": spark, "pd": pd, "__name__": "__nb__"}
    skipped = []
    try:
        for i, c in enumerate(nb["cells"]):
            if c["cell_type"] != "code" or (cell_limit and i >= cell_limit):
                continue
            src = "".join(c["source"])
            src = re.sub(r"^\s*!.*$", "", src, flags=re.M)                      # shell lines
            src = src.replace("spark= SparkSession.builder", "_unused = None and SparkSession")
            src = re.sub(r"spark\s*=\s*SparkSession\.builder.*?getOrCreate\(\)", "pass", src, flags=re.S)
            if "SparkSession" in src and "getOrCreate" in src:
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(src, f"{path.name}[{i}]", "exec"), g)
            except Exception as e:  # noqa: BLE001 - stub data cannot satisfy every pandas step
                skipped.append((i, type(e).__name__))
    finally:
        lc.load_config = real_load
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return log, skipped, g


def sqls(log):
    return [q for kind, q in log if kind == "SQL"]


def written(log):
    out = []
    for q in sqls(log):
        m = re.match(r"CREATE TABLE\s+([\w.]+)", q, re.I)
        if m:
            out.append(m.group(1))
    return out


def read_tables(log):
    out = set()
    for q in sqls(log):
        out |= set(re.findall(r"(?:FROM|JOIN)\s+(Z_ABV_CWS_MABI_ONC_ANALYTICS\.\w+)", q, re.I))
    return out


LOT = "AML_LOT_PATIENT_INTENSITY_LOT.ipynb"
ELIG = "AML_PATIENT_ELIGIBILITY.ipynb"
DASH = "AML_NPS_Code_for_LEGACY_definition_of_IC_elig_inelig_Annotated.ipynb"

# 4. Config resolution.
check(idef.definition({"run": {}}) == "legacy", "missing intensity_definition defaults to legacy")
check(idef.definition({"run": {"intensity_definition": "new"}}) == "new", "new resolves")
try:
    idef.definition({"run": {"intensity_definition": "rule_b"}})
    failures.append("unknown intensity_definition did not raise")
except ValueError:
    pass
from load_config import load_config  # noqa: E402

for f in ("intensity_lot.yaml", "eligibility.yaml", "nps_dashboard_legacy.yaml"):
    check(idef.definition(load_config(f)) == "legacy", f"shipped config default is legacy ({f})")

# 1. Legacy run == pre-change notebooks.
for name in (LOT, ELIG, DASH):
    if not (BACKUP / name).exists():
        failures.append(f"backup missing for {name}; cannot compare legacy SQL")
        continue
    before, _, _ = run_notebook(BACKUP / name, "legacy")
    after, skipped, _ = run_notebook(NBDIR / name, "legacy")
    check(sqls(before) == sqls(after),
          f"{name}: legacy SQL differs from the pre-change notebook "
          f"({len(sqls(before))} vs {len(sqls(after))} statements)")
    check(not any("_NEWDEF" in t or "_P1LEGACY" in t for t in written(after)), f"{name}: legacy run writes tagged tables")

# 2/3. New-definition run.
lot_log, lot_skipped, lot_g = run_notebook(NBDIR / LOT, "new")
w = written(lot_log)
legacy_outputs = {lot_g["final_patient_group"].replace("_NEWDEF", ""), lot_g["final_pat_comb_lot"].replace("_NEWDEF", ""),
                  lot_g["final_lot_regimen_group"].replace("_NEWDEF", ""),
                  lot_g["final_ic_elig_final"].replace("_NEWDEF", ""), lot_g["final_ic_inelig_final"].replace("_NEWDEF", ""),
                  lot_g["final_patient_intensity_tbl"].replace("_NEWDEF", "")}
check(not (set(w) & legacy_outputs), f"new run overwrote a legacy table: {set(w) & legacy_outputs}")
for t in ("final_patient_group", "final_ic_inelig_final", "final_ic_elig_final", "final_pat_comb_lot",
          "final_lot_regimen_group", "final_patient_intensity_tbl"):
    check(lot_g[t] in w and lot_g[t].endswith("_NEWDEF"), f"new run writes {t} ({lot_g[t]})")
check(any(t.endswith("_P1LEGACY") for t in w), "new run builds pass-1 legacy scratch tables")
cohort_sql = next((q for q in sqls(lot_log) if q.startswith(f"CREATE TABLE {lot_g['final_patient_group']}")), "")
check(lot_g["final_patient_intensity_tbl"] in cohort_sql, "new cohort joins the new-definition class table")
# The class must actually come from PATIENT_INTENSITY_UPDATED, not just mention it.
cls_expr = re.search(r"SELECT (.*?) AS PATIENT_INTENSITY_GROUP,", cohort_sql)
check(bool(cls_expr) and "PATIENT_INTENSITY_UPDATED" in cls_expr.group(1),
      f"new cohort PATIENT_INTENSITY_GROUP is the new-definition class "
      f"({cls_expr.group(1).split(',')[-1].strip() if cls_expr else 'not found'})")
p2 = [q for q in sqls(lot_log) if lot_g["final_patient_group"] in q and "PATIENT_INTENSITY_GROUP = 'IC_" in q]
check(len(p2) == 2, f"pass 2 rebuilds IC_INELIG and IC_ELIG lines from the new cohort ({len(p2)})")
legacy_lot, _, _ = run_notebook(NBDIR / LOT, "legacy")
leg_elig = next(q for q in sqls(legacy_lot) if q.startswith("CREATE TABLE") and "_IC_ELIG_LOT_FINAL" in q)
new_elig = next(q for q in sqls(lot_log) if q.startswith(f"CREATE TABLE {lot_g['final_ic_elig_final']}"))
norm = lambda q: re.sub(r"Z_ABV_CWS_MABI_ONC_ANALYTICS\.\w+", "T", q)  # noqa: E731
check(norm(leg_elig) == norm(new_elig), "pass-2 IC_ELIG line SQL is the legacy line SQL")
check(not [s for s in lot_skipped if s[0] >= 50], f"pass-2 cells failed on stub: {[s for s in lot_skipped if s[0] >= 50]}")

for name in (ELIG, DASH):
    log, skipped, g = run_notebook(NBDIR / name, "new")
    w = written(log)
    check(w and all("_NEWDEF" in t for t in w if t.startswith("Z_ABV_CWS_MABI_ONC_ANALYTICS.MABI_AML_")
                    and "EXACT_DATES" not in t), f"{name}: new run writes untagged base-layer tables: {w}")
    reads = read_tables(log)
    dep = [t for t in reads if re.search(r"(PATS_COMB_LOT|PATS_LOT_GROUPING|PATIENT_COHORT|ELIG_FLAGS_FINAL|"
                                          r"PATIENT_INTENSITY_BASED)", t)]
    check(dep and all(t.endswith("_NEWDEF") for t in dep), f"{name}: new run reads legacy LoT/cohort/flags: {dep}")

if failures:
    print("intensity definition tests: FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("intensity definition tests: PASS")
