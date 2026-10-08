"""Boundary tests for the semester methodology (config/semester.py). No Spark needed.

    python tools/test_semester.py

1. Pure-Python reference rules: calendar labels, actual windows, boundaries, year/leap transitions,
   NULLs, config resolution.
2. The Spark SQL the notebook runs, translated to SQLite and executed on a small patient set, compared
   with the reference rules for both methodologies and all three flag groups. Only the Spark date
   functions used (ADD_MONTHS, MONTHS_BETWEEN, SEQUENCE/EXPLODE, TO_DATE, YEAR, MONTH) are emulated, so
   this checks the SQL logic, not Spark itself.
3. The default config reproduces the original notebook's windows (legacy rules re-implemented from the
   original cells).
"""
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "config"))
import semester as S  # noqa: E402
from load_config import load_config  # noqa: E402

failures = []


def eq(got, want, msg):
    if got != want:
        failures.append(f"{msg}: got {got!r}, want {want!r}")


D = date.fromisoformat

# ---------------------------------------------------------------- 1. reference rules
# Calendar labels: the four required boundaries, NULL, year transition, leap day.
for d, want in [("2026-01-01", "2026 - S1"), ("2026-03-03", "2026 - S1"), ("2026-06-30", "2026 - S1"),
                ("2026-07-01", "2026 - S2"), ("2026-12-31", "2026 - S2"), ("2027-01-01", "2027 - S1"),
                ("2024-02-29", "2024 - S1"), ("2025-12-31", "2025 - S2")]:
    eq(S.calendar_semester_label(D(d)), want, f"calendar label {d}")
eq(S.calendar_semester_label(None), None, "calendar label NULL")
eq(S.calendar_semester_start(D("2026-06-30")), D("2026-01-01"), "calendar start 06-30")
eq(S.calendar_semester_start(D("2026-07-01")), D("2026-07-01"), "calendar start 07-01")
eq(S.calendar_semester_start(None), None, "calendar start NULL")

# ADD_MONTHS end-of-month clipping, including leap years.
eq(S.add_months(D("2024-08-31"), -6), D("2024-02-29"), "add_months leap clip")
eq(S.add_months(D("2025-08-31"), -6), D("2025-02-28"), "add_months non-leap clip")
eq(S.add_months(D("2024-02-29"), 12), D("2025-02-28"), "add_months leap +12")

# Actual lookback: [anchor-6m, anchor) and [anchor-12m, anchor-6m); exact start in, exact end out.
a = D("2026-03-15")
w0, w1 = S.actual_lookback_windows(a)
eq((w0, w1), ((D("2025-09-15"), D("2026-03-15")), (D("2025-03-15"), D("2025-09-15"))), "lookback windows")
eq(S.in_lookback_window(D("2025-09-15"), w0), True, "lookback exact start")
eq(S.in_lookback_window(D("2025-09-14"), w0), False, "lookback day before start")
eq(S.in_lookback_window(D("2025-09-14"), w1), True, "lookback day before start -> previous window")
eq(S.in_lookback_window(D("2026-03-14"), w0), True, "lookback day before end")
eq(S.in_lookback_window(D("2026-03-15"), w0), False, "lookback exact end (anchor) excluded")
eq(S.in_lookback_window(None, w0), False, "lookback NULL claim")
eq(S.actual_lookback_windows(None), [], "lookback NULL anchor")
# Year-crossing lookback window.
eq(S.actual_lookback_windows(D("2026-02-10"))[0], (D("2025-08-10"), D("2026-02-10")), "lookback crosses year")

# Actual continuity: (start+(n-1)6m, start+n6m]; exact start out, exact end in; consecutive windows.
ws = S.actual_continuity_windows(D("2025-10-01"), D("2026-10-15"))
eq(ws, [(D("2025-10-01"), D("2026-04-01")), (D("2026-04-01"), D("2026-10-01"))], "continuity windows")
eq(S.in_continuity_window(D("2025-10-01"), ws[0]), False, "continuity exact start excluded")
eq(S.in_continuity_window(D("2025-10-02"), ws[0]), True, "continuity day after start")
eq(S.in_continuity_window(D("2026-04-01"), ws[0]), True, "continuity exact end included")
eq(S.in_continuity_window(D("2026-04-01"), ws[1]), False, "continuity end not double counted")
eq(S.in_continuity_window(D("2026-04-02"), ws[1]), True, "continuity day after end -> next window")
eq(ws[0][0].year != ws[0][1].year, True, "continuity window crosses year")
eq(S.actual_continuity_windows(D("2026-01-10"), D("2026-07-09")), [], "journey < 6m: no windows (passes)")
eq(len(S.actual_continuity_windows(D("2026-01-10"), D("2026-07-10"))), 1, "journey exactly 6m: one window")
eq(S.actual_continuity_windows(None, D("2026-07-10")), [], "continuity NULL start")

# Calendar lookback: semester(anchor-12m) .. semester(anchor), capped at exc_dt.
eq(S.calendar_lookback_semesters(D("2026-03-15")), [D("2025-01-01"), D("2025-07-01"), D("2026-01-01")],
   "calendar lookback semesters")
eq(S.calendar_lookback_semesters(D("2026-03-15"), exc_dt=D("2025-07-01")), [D("2025-01-01"), D("2025-07-01")],
   "calendar lookback exc_dt cap")
eq(S.calendar_lookback_semesters(D("2026-07-01")), [D("2025-07-01"), D("2026-01-01"), D("2026-07-01")],
   "calendar lookback anchor on S2 boundary")
eq(S.calendar_lookback_semesters(None), [], "calendar lookback NULL anchor")
eq(S.calendar_continuity_semesters(D("2025-12-31"), D("2026-01-01")), [D("2025-07-01"), D("2026-01-01")],
   "calendar continuity across year end")

# Config resolution.
eq(S.resolve_semester_types({"semester_type": "calendar"}),
   {"dx_lookback": "calendar", "journey_continuity": "calendar", "ven_lookback": "calendar"}, "global calendar")
eq(S.resolve_semester_types({}), S.LEGACY_SEMESTER_TYPES, "missing key -> legacy")
eq(S.resolve_semester_types({"semester_type": {"ven_lookback": "actual"}})["dx_lookback"], "actual", "partial map")
for bad in [{"semester_type": "monthly"}, {"semester_type": {"dx_lookback": "x"}}, {"semester_type": {"foo": "actual"}}]:
    try:
        S.resolve_semester_types(bad)
        failures.append(f"no error for {bad}")
    except ValueError:
        pass
eq(S.resolve_semester_types(load_config("eligibility.yaml")["semester"]), S.LEGACY_SEMESTER_TYPES,
   "shipped config = legacy behaviour")

# ---------------------------------------------------------------- 2. SQL executed (SQLite emulation)


def _d(x):
    return None if x is None else D(str(x)[:10])


def f_add_months(d, n):
    r = S.add_months(_d(d), int(n))
    return None if r is None else r.isoformat()


def f_months_between(a, b):
    a, b = _d(a), _d(b)
    return None if a is None or b is None else S.months_between(a, b)


def to_sqlite(sql):
    s = sql
    s = re.sub(r"TO_DATE\(CONCAT\(CAST\(YEAR\((.+?)\) AS STRING\), '-(\d\d)-01'\)\)",
               r"(CAST(YEAR(\1) AS TEXT) || '-\2-01')", s)
    s = re.sub(r"CONCAT\(CAST\(YEAR\((\w+)\) AS STRING\), ' - S', ", r"(CAST(YEAR(\1) AS TEXT) || ' - S' || ", s)
    s = s.replace("TO_DATE(", "DATE(").replace("AS STRING", "AS TEXT")
    s = re.sub(r"CAST\((MONTHS_BETWEEN\([^)]*\)) / (\d+) AS INT\)", r"CAST(\1 / \2 AS INT)", s)
    s = s.replace("GREATEST(", "MAX(")
    # EXPLODE(SEQUENCE(a, b[, INTERVAL n MONTH])) -> join on a numbers table (rewritten per pattern below)
    return s


def run_sqlite(spark_sql, tables):
    """Execute the notebook's Spark SQL in SQLite by rewriting the non-portable constructs."""
    con = sqlite3.connect(":memory:")
    con.create_function("ADD_MONTHS", 2, f_add_months)
    con.create_function("MONTHS_BETWEEN", 2, f_months_between)
    con.create_function("YEAR", 1, lambda d: None if d is None else int(str(d)[:4]))
    con.create_function("MONTH", 1, lambda d: None if d is None else int(str(d)[5:7]))
    con.execute("CREATE TABLE NUMS (N INTEGER)")
    con.executemany("INSERT INTO NUMS VALUES (?)", [(i,) for i in range(0, 400)])
    for name, (cols, rows) in tables.items():
        con.execute(f"CREATE TABLE {name} ({', '.join(cols)})")
        con.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})", rows)
    s = to_sqlite(spark_sql)
    # LATERAL VIEW EXPLODE(SEQUENCE(0, k)) T AS K  ->  JOIN NUMS T ON T.N BETWEEN 0 AND k ; alias K
    s = re.sub(r"FROM ANCHORS\s+LATERAL VIEW EXPLODE\(SEQUENCE\(0, (\d+)\)\) T AS K",
               r"FROM ANCHORS JOIN (SELECT N AS K FROM NUMS WHERE N BETWEEN 0 AND \1) T", s)
    # SELECT ..., EXPLODE(SEQUENCE(0, expr)) AS N FROM ANCHORS WHERE ...  (continuity points)
    s = re.sub(r"SELECT PATIENT_GID, P_START, P_END,\s+EXPLODE\(SEQUENCE\(0, (MAX\(.*?, 0\))\)\) AS N\s+FROM ANCHORS",
               r"SELECT PATIENT_GID, P_START, P_END, NUMS.N AS N FROM ANCHORS JOIN NUMS ON NUMS.N BETWEEN 0 AND \1",
               s, flags=re.S)
    # SELECT PATIENT_GID, EXPLODE(SEQUENCE(s0, s1, INTERVAL 6 MONTH)) AS PERIOD_START FROM (...) A WHERE ...
    m = re.search(r"SELECT PATIENT_GID, EXPLODE\(SEQUENCE\((.*?), (CASE WHEN P_END.*?END), INTERVAL (\d+) MONTH\)\) AS PERIOD_START\s+FROM",
                  s, flags=re.S)
    if m:
        s0, s1, mo = m.group(1), m.group(2), m.group(3)
        s = s.replace(m.group(0),
                      f"SELECT PATIENT_GID, ADD_MONTHS({s0}, NUMS.N * {mo}) AS PERIOD_START FROM NUMS, ", 1)
        s = re.sub(r"(ADD_MONTHS\(CASE WHEN P_START.*?NUMS\.N \* \d+\) AS PERIOD_START FROM NUMS, \s*\(SELECT PATIENT_GID.*?\) A\s+WHERE P_START IS NOT NULL AND P_END IS NOT NULL AND P_START <= P_END)",
                   lambda mm: mm.group(1) + f" AND ADD_MONTHS({s0}, NUMS.N * {mo}) <= {s1}", s, flags=re.S)
    return {r[0] for r in con.execute(s).fetchall()}


# Test patients: (id, anchor/start, end, claim dates)
P = [
    ("lb_both", "2026-03-15", None, ["2025-09-15", "2025-03-15"]),          # both windows, exact starts
    ("lb_end_only", "2026-03-15", None, ["2026-03-15", "2025-06-01"]),      # recent claim on the anchor (excluded)
    ("lb_yearcross", "2026-02-10", None, ["2025-12-31", "2025-04-01"]),
    ("lb_leap", "2024-08-31", None, ["2024-02-29", "2023-09-01"]),
    ("lb_null", None, None, ["2025-01-01"]),
    ("lb_gap", "2026-03-15", None, ["2025-10-01"]),                          # older window empty
    ("cal_s1s2", "2026-07-01", None, ["2025-07-01", "2026-01-01", "2026-07-01"]),
    # Calendar VEN lookback with exc_dt = 2026-01-01: the anchor's own semester (2026-S2) is past the cap,
    # so it is not tested and the patient passes; without the cap it would fail.
    ("cal_capped", "2026-08-15", None, ["2025-08-01", "2026-02-01"]),
    ("ct_full", "2025-10-01", "2026-10-15", ["2026-04-01", "2026-10-01"]),   # both window ends (inclusive)
    ("ct_start_only", "2025-10-01", "2026-10-15", ["2025-10-01", "2026-10-01"]),  # exact start excluded
    ("ct_short", "2026-01-10", "2026-07-09", []),                            # < 6m passes
    ("ct_cal_one_sem", "2026-01-10", "2026-06-30", []),                      # one calendar semester passes
    ("ct_cal_span", "2025-12-31", "2026-01-01", ["2025-12-31"]),             # spans 2 semesters, one empty
    ("ct_null_end", "2025-01-01", None, []),                                 # e.g. no VEN: passes continuity
]


def tables_for(rows):
    act = [(pid, c) for pid, _, _, cs in rows for c in cs]
    return {
        "ANCH": (["PATIENT_GID", "ANCHOR", "P_START", "P_END"], [(pid, a, a, e) for pid, a, e, _ in rows]),
        "ACT": (["PATIENT_GID", "CLAIM_DATE"], act),
    }


def ref_pass(group, stype, a, e, claims, exc=None):
    a, e = _d(a), _d(e)
    cl = [D(c) for c in claims]
    if group == "lookback":
        if stype == "actual":
            return S.passes_actual_lookback(S.actual_lookback_windows(a), cl)
        return S.passes_calendar(S.calendar_lookback_semesters(a, exc_dt=exc), cl)
    if a is None or e is None:
        return True
    if stype == "actual":
        return S.passes_actual_continuity(S.actual_continuity_windows(a, e), cl)
    return S.passes_calendar(S.calendar_continuity_semesters(a, e), cl, pass_if_le_one_period=True)


cfg = load_config("eligibility.yaml")
exc = "2026-01-01"
for stype in S.SEMESTER_TYPES:
    for group, anchor_sql, sql_group, exc_dt in [
        ("lookback", "SELECT PATIENT_GID, ANCHOR FROM ANCH", "dx_lookback", None),
        ("lookback", "SELECT PATIENT_GID, ANCHOR FROM ANCH", "ven_lookback", exc),
        ("continuity", "SELECT PATIENT_GID, P_START, P_END FROM ANCH", "journey_continuity", None),
    ]:
        sql = S.sql_flag_check(sql_group, stype, anchor_sql, ["ACT"], exc_dt=exc_dt, cfg=cfg)
        try:
            got = run_sqlite(sql, tables_for(P))
        except Exception as ex:  # noqa: BLE001
            failures.append(f"SQL {sql_group}/{stype} did not run: {ex}")
            continue
        cap = D(exc) if (sql_group == "ven_lookback" and stype == "calendar") else None
        want = {pid for pid, a, e, cs in P if ref_pass(group, stype, a, e, cs, cap)}
        eq(sorted(got), sorted(want), f"SQL vs reference {sql_group}/{stype}")

# ---------------------------------------------------------------- 3. default config == original notebook


def legacy_dx_lookback(anchor, claims):
    """Original cell 28: activity in [a-6m, a) AND in [a-12m, a-6m), exact dates."""
    if anchor is None:
        return False
    a6, a12 = S.add_months(anchor, -6), S.add_months(anchor, -12)
    return any(a6 <= c < anchor for c in claims) and any(a12 <= c < a6 for c in claims)


def legacy_txl(start, end, claims):
    """Original cells 38-55: LEAD-based periods ADD_MONTHS(start, n*6), pandas interval (prev, cur]."""
    if start is None or end is None:
        return True
    k = int(S.months_between(end, start) / 6)
    pts = [S.add_months(start, n * 6) for n in range(0, k + 1)]
    pts = [p for p in pts if p <= end]
    if len(pts) <= 1:
        return True
    return all(any(p0 < c <= p1 for c in claims) for p0, p1 in zip(pts[:-1], pts[1:]))


for pid, a, e, cs in P:
    a_, e_, cl = _d(a), _d(e), [D(c) for c in cs]
    eq(S.passes_actual_lookback(S.actual_lookback_windows(a_), cl), legacy_dx_lookback(a_, cl), f"legacy DX_LB {pid}")
    if a_ is not None and e_ is not None:
        eq(S.passes_actual_continuity(S.actual_continuity_windows(a_, e_), cl), legacy_txl(a_, e_, cl),
           f"legacy TXL {pid}")

# ---------------------------------------------------------------- report
if failures:
    print("semester tests: FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("semester tests: PASS")
