"""Semester methodology for AML patient eligibility (AML_PATIENT_ELIGIBILITY).

Each activity flag asks: did the patient have Mx or Rx activity in every 6-month period around an
anchor date? A period ("semester") can be built two ways. `semester.semester_type` in
config/eligibility.yaml chooses the method, either for all flag groups or per group.

calendar  Fixed calendar halves. Jan-Jun = S1 (starts YYYY-01-01) and Jul-Dec = S2 (starts YYYY-07-01),
          decided by the month of the claim date. The anchor only decides which halves are tested.

actual    Rolling 6-month windows measured from the patient's own anchor date, so a window can start on
          any day and can cross a year end. The anchors are FIRST_DX, FIRST_TX->LAST_TX and
          VEN_START->VEN_END.

Flag groups and the anchors they use:
  dx_lookback         DX_LB_ELIG_FLG                    12 months before FIRST_DX
  journey_continuity  TX_TXL_MX/RX_ELIG_FLG             FIRST_TX -> LAST_TX
                      TX_TXL_MX/RX_ELIG_VEN_FLG         VEN_START -> VEN_END
  ven_lookback        TX_MX/RX_LB_ELIG_VEN_FLG          12 months before VEN_START

Boundary rules are the ones the notebook already used, so the default config reproduces existing
results:
  - actual lookback windows:   [anchor-(k+1)*6m, anchor-k*6m)   start included, end excluded
  - actual continuity windows: (start+(n-1)*6m, start+n*6m]     start excluded, end included;
                               a journey with fewer than two window points passes automatically
  - calendar lookback:         every calendar semester from semester(anchor-12m) to semester(anchor),
                               keeping only those on or before the last complete semester (exc_dt)
  - calendar continuity:       every calendar semester from semester(start) to semester(end); a
                               journey inside one semester passes automatically

This module holds two implementations that follow the same rules: Spark SQL builders (used by the
notebook) and pure-Python reference functions (used by tools/test_semester.py, which needs no Spark).
Keep them in step when editing.
"""
import calendar as _cal
from datetime import date

SEMESTER_TYPES = ("calendar", "actual")
FLAG_GROUPS = ("dx_lookback", "journey_continuity", "ven_lookback")
# Methodology each group used before semester_type existed; also the fallback for any group missing
# from the config.
LEGACY_SEMESTER_TYPES = {"dx_lookback": "actual", "journey_continuity": "actual", "ven_lookback": "calendar"}


def resolve_semester_types(semester_cfg):
    """semester_cfg = the `semester:` block of eligibility.yaml -> {group: 'calendar'|'actual'}.

    `semester_type` may be a single string (applies to every group) or a mapping per group.
    A missing key keeps that group's legacy methodology. Unknown groups or values raise ValueError.
    """
    st = (semester_cfg or {}).get("semester_type", LEGACY_SEMESTER_TYPES)
    if isinstance(st, str):
        types = {g: st for g in FLAG_GROUPS}
    elif isinstance(st, dict):
        unknown = set(st) - set(FLAG_GROUPS)
        if unknown:
            raise ValueError(f"Unknown semester_type group(s) {sorted(unknown)}; use {FLAG_GROUPS}")
        types = {**LEGACY_SEMESTER_TYPES, **st}
    else:
        raise ValueError("semester_type must be 'calendar', 'actual' or a mapping per flag group")
    for g, v in types.items():
        if v not in SEMESTER_TYPES:
            raise ValueError(f"Unsupported semester_type {v!r} for {g}; use one of {SEMESTER_TYPES}")
    return types


# ======================================================================= pure Python reference

def add_months(d, n):
    """Spark 3 ADD_MONTHS: same day of month, clipped to the target month's last day."""
    if d is None:
        return None
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, _cal.monthrange(y, m)[1]))


def months_between(d1, d2):
    """Spark MONTHS_BETWEEN(d1, d2) for dates."""
    whole = (d1.year - d2.year) * 12 + (d1.month - d2.month)
    last1 = d1.day == _cal.monthrange(d1.year, d1.month)[1]
    last2 = d2.day == _cal.monthrange(d2.year, d2.month)[1]
    if d1.day == d2.day or (last1 and last2):
        return float(whole)
    return round(whole + (d1.day - d2.day) / 31.0, 8)


def calendar_semester_start(d, split_month=6):
    """Date -> first day of its calendar semester (YYYY-01-01 or YYYY-07-01). None stays None."""
    if d is None:
        return None
    return date(d.year, 1 if d.month <= split_month else split_month + 1, 1)


def calendar_semester_label(d, split_month=6):
    """Date -> 'YYYY - S1' / 'YYYY - S2'. None stays None."""
    if d is None:
        return None
    return f"{d.year} - S{1 if d.month <= split_month else 2}"


def _calendar_range(start, end, exc_dt, split_month, months):
    if start is None or end is None or end < start:
        return []
    cur, last, out = calendar_semester_start(start, split_month), calendar_semester_start(end, split_month), []
    while cur <= last:
        if exc_dt is None or cur <= exc_dt:
            out.append(cur)
        cur = add_months(cur, months)
    return out


def calendar_lookback_semesters(anchor, lookback_months=12, exc_dt=None, split_month=6, months=6):
    """Calendar semesters a lookback flag tests: semester(anchor-lookback) .. semester(anchor), <= exc_dt."""
    if anchor is None:
        return []
    return _calendar_range(add_months(anchor, -lookback_months), anchor, exc_dt, split_month, months)


def calendar_continuity_semesters(start, end, exc_dt=None, split_month=6, months=6):
    """Calendar semesters spanning a journey: semester(start) .. semester(end), <= exc_dt when given."""
    return _calendar_range(start, end, exc_dt, split_month, months)


def actual_lookback_windows(anchor, n_windows=2, months=6):
    """Rolling lookback windows before the anchor, newest first, as [start, end) pairs."""
    if anchor is None:
        return []
    return [(add_months(anchor, -(k + 1) * months), add_months(anchor, -k * months)) for k in range(n_windows)]


def actual_continuity_windows(start, end, months=6):
    """Rolling journey windows exactly as the notebook builds them:
    points p_n = ADD_MONTHS(start, n*months) for n = 0 .. CAST(MONTHS_BETWEEN(end, start)/months AS INT)
    with p_n <= end; window n = (p_{n-1}, p_n]. Fewer than two points -> no windows (passes)."""
    if start is None or end is None:
        return []
    k = int(months_between(end, start) / months)
    pts = [p for p in (add_months(start, n * months) for n in range(0, k + 1)) if p <= end]
    return list(zip(pts[:-1], pts[1:]))


def in_lookback_window(claim, window):
    return claim is not None and window[0] <= claim < window[1]


def in_continuity_window(claim, window):
    return claim is not None and window[0] < claim <= window[1]


def passes_calendar(periods, claim_dates, pass_if_le_one_period=False, split_month=6):
    """True when every calendar period has at least one claim in it."""
    if pass_if_le_one_period and len(periods) <= 1:
        return True
    if not periods:
        return False
    active = {calendar_semester_start(c, split_month) for c in claim_dates if c is not None}
    return all(p in active for p in periods)


def passes_actual_lookback(windows, claim_dates):
    return bool(windows) and all(any(in_lookback_window(c, w) for c in claim_dates) for w in windows)


def passes_actual_continuity(windows, claim_dates):
    return all(any(in_continuity_window(c, w) for c in claim_dates) for w in windows)


# ======================================================================= Spark SQL builders

def sql_calendar_semester_start(col, split_month=6):
    """Spark SQL expression: date -> DATE of its calendar semester start. NULL stays NULL."""
    return (f"CASE WHEN {col} IS NULL THEN NULL "
            f"WHEN MONTH({col}) <= {split_month} THEN TO_DATE(CONCAT(CAST(YEAR({col}) AS STRING), '-01-01')) "
            f"ELSE TO_DATE(CONCAT(CAST(YEAR({col}) AS STRING), '-{split_month + 1:02d}-01')) END")


def sql_calendar_semester_label(col, split_month=6):
    """Spark SQL expression: date -> 'YYYY - S1' / 'YYYY - S2'. NULL stays NULL."""
    return (f"CASE WHEN {col} IS NULL THEN NULL "
            f"ELSE CONCAT(CAST(YEAR({col}) AS STRING), ' - S', "
            f"CASE WHEN MONTH({col}) <= {split_month} THEN '1' ELSE '2' END) END")


def _activity_union(activity_sources, cols):
    """UNION of activity sources. A source is either an exact-date table name (PATIENT_GID, CLAIM_DATE)
    or {'semester_select': SQL} returning PATIENT_GID, PERIOD_START (already semester-level, e.g. the
    SEMESTERLY activity-frequency tables). Semester-level sources only make sense for calendar periods."""
    parts = []
    for s in activity_sources:
        if isinstance(s, dict):
            if "PERIOD_START" not in cols:
                raise ValueError("semester-level activity can only be used with calendar semesters")
            parts.append(f"SELECT DISTINCT PATIENT_GID, TO_DATE(PERIOD_START) AS PERIOD_START FROM ({s['semester_select']}) SS")
        else:
            parts.append(f"SELECT DISTINCT PATIENT_GID, {cols} FROM {s} WHERE CLAIM_DATE IS NOT NULL")
    return "\n    UNION\n    ".join(parts)


def sql_calendar_periods(anchor_select, exc_dt=None, split_month=6, months=6, spine_select=None):
    """Spark SQL: one row per patient x calendar semester to test.

    anchor_select: a SELECT returning PATIENT_GID, P_START, P_END (dates). Every calendar semester
    from semester(P_START) to semester(P_END) is generated, keeping those <= exc_dt when given.
    spine_select: optional SELECT returning PERIOD_START; only semesters in it are kept (the VEN lookback
    has always tested only semesters present in the VENC_AML 'RX FACT' data).
    Columns: PATIENT_GID, PERIOD_START, PERIOD_LABEL ('YYYY - Sn').
    """
    s0 = sql_calendar_semester_start("P_START", split_month)
    s1 = sql_calendar_semester_start("P_END", split_month)
    conds = []
    if exc_dt:
        conds.append(f"PERIOD_START <= TO_DATE('{exc_dt}')")
    if spine_select:
        conds.append(f"PERIOD_START IN (SELECT TO_DATE(PERIOD_START) FROM ({spine_select}) SP)")
    cutoff = ("WHERE " + " AND ".join(conds)) if conds else ""
    return f"""
SELECT PATIENT_GID, PERIOD_START, {sql_calendar_semester_label('PERIOD_START', split_month)} AS PERIOD_LABEL
FROM (
    SELECT PATIENT_GID, EXPLODE(SEQUENCE({s0}, {s1}, INTERVAL {months} MONTH)) AS PERIOD_START
    FROM (SELECT PATIENT_GID, TO_DATE(P_START) AS P_START, TO_DATE(P_END) AS P_END FROM ({anchor_select}) SRC) A
    WHERE P_START IS NOT NULL AND P_END IS NOT NULL AND P_START <= P_END
) S
{cutoff}"""


def sql_calendar_activity_check(anchor_select, activity_tables, exc_dt=None, pass_if_le_one_period=False,
                                split_month=6, months=6, spine_select=None):
    """Spark SQL: DISTINCT PATIENT_GID of patients with activity in every calendar semester.

    anchor_select returns PATIENT_GID, P_START, P_END. activity_tables are exact-date tables with
    PATIENT_GID, CLAIM_DATE; several tables are OR-ed (any of them counts as activity).
    pass_if_le_one_period: patients with 0 or 1 semester pass without a test (continuity rule).
    """
    sem = sql_calendar_semester_start("TO_DATE(CLAIM_DATE)", split_month)
    activity = _activity_union(activity_tables, f"{sem} AS PERIOD_START")
    passthrough = ""
    if pass_if_le_one_period:
        passthrough = """
UNION
SELECT A.PATIENT_GID
FROM (SELECT DISTINCT PATIENT_GID FROM ANCHORS) A
LEFT JOIN CHECKED C ON C.PATIENT_GID = A.PATIENT_GID
WHERE COALESCE(C.N_PERIODS, 0) <= 1"""
    return f"""
WITH ANCHORS AS ({anchor_select}),
PERIODS AS ({sql_calendar_periods('SELECT * FROM ANCHORS', exc_dt, split_month, months, spine_select)}),
ACTIVITY AS (
    {activity}
),
CHECKED AS (
    SELECT P.PATIENT_GID,
           COUNT(*) AS N_PERIODS,
           SUM(CASE WHEN A.PATIENT_GID IS NULL THEN 0 ELSE 1 END) AS N_ACTIVE
    FROM PERIODS P
    LEFT JOIN ACTIVITY A
      ON A.PATIENT_GID = P.PATIENT_GID
     AND A.PERIOD_START = P.PERIOD_START
    GROUP BY P.PATIENT_GID
)
SELECT DISTINCT PATIENT_GID FROM CHECKED WHERE N_PERIODS = N_ACTIVE{passthrough}"""


def sql_actual_lookback_check(anchor_select, activity_tables, n_windows=2, months=6):
    """Spark SQL: DISTINCT PATIENT_GID of patients with activity in every rolling lookback window
    [ANCHOR-(k+1)*months, ANCHOR-k*months), k = 0..n_windows-1, on exact claim dates.

    anchor_select returns PATIENT_GID, ANCHOR. A NULL anchor means no windows, so the patient fails
    (as in the calendar lookback).
    """
    activity = _activity_union(activity_tables, "TO_DATE(CLAIM_DATE) AS CLAIM_DATE")
    return f"""
WITH ANCHORS AS (
    SELECT DISTINCT PATIENT_GID, TO_DATE(ANCHOR) AS ANCHOR FROM ({anchor_select}) SRC WHERE ANCHOR IS NOT NULL
),
PERIODS AS (
    SELECT PATIENT_GID, K,
           ADD_MONTHS(ANCHOR, -(K + 1) * {months}) AS PERIOD_START,
           ADD_MONTHS(ANCHOR, -K * {months})       AS PERIOD_END
    FROM ANCHORS
    LATERAL VIEW EXPLODE(SEQUENCE(0, {n_windows - 1})) T AS K
),
ACTIVITY AS (
    {activity}
),
CHECKED AS (
    SELECT P.PATIENT_GID, P.K,
           MAX(CASE WHEN A.PATIENT_GID IS NULL THEN 0 ELSE 1 END) AS ACTIVE
    FROM PERIODS P
    LEFT JOIN ACTIVITY A
      ON A.PATIENT_GID = P.PATIENT_GID
     AND A.CLAIM_DATE >= P.PERIOD_START
     AND A.CLAIM_DATE <  P.PERIOD_END
    GROUP BY P.PATIENT_GID, P.K
)
SELECT PATIENT_GID FROM CHECKED GROUP BY PATIENT_GID HAVING MIN(ACTIVE) = 1"""


def sql_actual_continuity_check(anchor_select, activity_tables, months=6):
    """Spark SQL: DISTINCT PATIENT_GID passing the rolling journey-continuity test.

    anchor_select returns PATIENT_GID, P_START, P_END (journey start/end, e.g. FIRST_TX/LAST_TX).
    Points p_n = ADD_MONTHS(P_START, n*months) for n = 0..CAST(MONTHS_BETWEEN(P_END, P_START)/months AS INT)
    with p_n <= P_END; window n = (p_{n-1}, p_n]. Every window needs a claim. Patients with fewer than
    two points (journey under one window) pass automatically, as in the original pandas step. A NULL end
    (e.g. no Venclexta) also passes, as before. Pure Spark; replaces the toPandas() merge.
    """
    activity = _activity_union(activity_tables, "TO_DATE(CLAIM_DATE) AS CLAIM_DATE")
    return f"""
WITH ANCHORS AS (
    SELECT DISTINCT PATIENT_GID, TO_DATE(P_START) AS P_START, TO_DATE(P_END) AS P_END FROM ({anchor_select}) SRC
),
POINTS AS (
    SELECT PATIENT_GID, N, ADD_MONTHS(P_START, N * {months}) AS PT
    FROM (
        SELECT PATIENT_GID, P_START, P_END,
               EXPLODE(SEQUENCE(0, GREATEST(CAST(MONTHS_BETWEEN(P_END, P_START) / {months} AS INT), 0))) AS N
        FROM ANCHORS
        WHERE P_START IS NOT NULL AND P_END IS NOT NULL
    ) X
    WHERE ADD_MONTHS(P_START, N * {months}) <= P_END
),
PERIODS AS (
    SELECT PATIENT_GID, N,
           LAG(PT) OVER (PARTITION BY PATIENT_GID ORDER BY N) AS PERIOD_START,
           PT AS PERIOD_END
    FROM POINTS
),
ACTIVITY AS (
    {activity}
),
CHECKED AS (
    SELECT P.PATIENT_GID, P.N,
           MAX(CASE WHEN A.PATIENT_GID IS NULL THEN 0 ELSE 1 END) AS ACTIVE
    FROM PERIODS P
    LEFT JOIN ACTIVITY A
      ON A.PATIENT_GID = P.PATIENT_GID
     AND A.CLAIM_DATE >  P.PERIOD_START
     AND A.CLAIM_DATE <= P.PERIOD_END
    WHERE P.PERIOD_START IS NOT NULL
    GROUP BY P.PATIENT_GID, P.N
)
SELECT A.PATIENT_GID
FROM (SELECT DISTINCT PATIENT_GID FROM ANCHORS) A
LEFT JOIN (SELECT PATIENT_GID, MIN(ACTIVE) AS ALL_ACTIVE FROM CHECKED GROUP BY PATIENT_GID) C
  ON C.PATIENT_GID = A.PATIENT_GID
WHERE COALESCE(C.ALL_ACTIVE, 1) = 1"""


def sql_flag_check(group, semester_type, anchor_select, activity_tables, exc_dt=None, cfg=None,
                   calendar_activity=None, calendar_spine=None):
    """Dispatch: the Spark SQL for one flag group under the chosen methodology.

    group             dx_lookback | journey_continuity | ven_lookback
    anchor_select     lookback groups: SELECT PATIENT_GID, ANCHOR ...
                      journey_continuity: SELECT PATIENT_GID, P_START, P_END ...
    activity_tables   exact-date (PATIENT_GID, CLAIM_DATE) tables; activity in any one counts
    exc_dt            last complete semester; applied only to the calendar VEN lookback, as before
    cfg               eligibility config dict (months, split month, lookback length, windows)
    calendar_activity optional activity sources used instead of activity_tables in calendar mode,
                      e.g. [{'semester_select': ...}] for the SEMESTERLY frequency tables the VEN lookback
                      has always read. Ignored in actual mode, which needs exact claim dates.
    calendar_spine    optional SELECT returning PERIOD_START; calendar mode keeps only those semesters.
    """
    if semester_type == "calendar" and calendar_activity:
        activity_tables = calendar_activity
    cfg = cfg or {}
    months = cfg.get("txl_continuity", {}).get("interval_months", 6)
    split = cfg.get("semester", {}).get("split_month", 6)
    if semester_type not in SEMESTER_TYPES:
        raise ValueError(f"Unsupported semester_type {semester_type!r}")
    if group in ("dx_lookback", "ven_lookback"):
        if group == "dx_lookback":
            lb_months = max(cfg.get("dx_lookback", {}).get("windows_months", [6, 12]))
        else:
            lb_months = cfg.get("ven_lookback", {}).get("lookback_months", 12)
        if semester_type == "actual":
            return sql_actual_lookback_check(anchor_select, activity_tables, lb_months // months, months)
        lb_select = (f"SELECT PATIENT_GID, ADD_MONTHS(TO_DATE(ANCHOR), -{lb_months}) AS P_START, "
                     f"TO_DATE(ANCHOR) AS P_END FROM ({anchor_select}) LB")
        cut = exc_dt if (group == "ven_lookback" and cfg.get("ven_lookback", {}).get("apply_exclusion_cutoff", True)) else None
        return sql_calendar_activity_check(lb_select, activity_tables, cut, False, split, months, calendar_spine)
    if group == "journey_continuity":
        if semester_type == "actual":
            return sql_actual_continuity_check(anchor_select, activity_tables, months)
        return sql_calendar_activity_check(anchor_select, activity_tables, None, True, split, months, calendar_spine)
    raise ValueError(f"Unknown flag group {group!r}; use {FLAG_GROUPS}")
