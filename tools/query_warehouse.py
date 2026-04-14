"""
Tool: query_warehouse.py
Purpose: Connect to Skill-Lync Warehouse (Microsoft Fabric SQL endpoint) and run queries.
Used by: All Skill-Lync data analysis workflows.

Usage:
    python tools/query_warehouse.py --query "SELECT TOP 10 * FROM fact.Final_Table"
    python tools/query_warehouse.py --report funnel --month 3 --year 2026
    python tools/query_warehouse.py --report funnel --month 3 --year 2026 --json

Notes:
    - Same Fabric tenant + service principal as Crio_PowerBI_Agent.
    - Different warehouse: "Skill-lync Warehouse" (note the space and hyphen).
    - Schema is DIFFERENT from Crio. Fact table is fact.Final_Table (underscore),
      not fact.FinalTable. See memory/shared_architecture.md.
"""

import pyodbc
import os
import re
import json
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Connection ────────────────────────────────────────────────────────────────

SQL_ENDPOINT = os.getenv(
    "SQL_ENDPOINT",
    "twwfdlzo7soexar7f7tzk7wuo4-k6jathn5r3uehhmbl5juoq54da.datawarehouse.fabric.microsoft.com",
)
# Default DB name has a space and a hyphen — wrapped in {} in the conn string.
DATABASE = os.getenv("WAREHOUSE_DB", "Skill-lync Warehouse")

MAX_RESULT_ROWS = int(os.getenv("MAX_RESULT_ROWS", "50000"))

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 5

# ── SQL Safety Guard ─────────────────────────────────────────────────────────
# Blocks write/DDL ops. Strips strings + comments first to avoid false positives.

_WRITE_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
    'TRUNCATE', 'EXEC', 'EXECUTE', 'MERGE', 'GRANT', 'REVOKE',
}

_WRITE_PATTERN = re.compile(
    r'\b(' + '|'.join(_WRITE_KEYWORDS) + r')\b',
    re.IGNORECASE,
)

_STRING_LITERAL = re.compile(r"'[^']*'")
_LINE_COMMENT = re.compile(r'--[^\n]*')
_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)


def _check_sql_safety(sql):
    """Raise ValueError if SQL contains a write/DDL operation."""
    cleaned = _BLOCK_COMMENT.sub('', sql)
    cleaned = _LINE_COMMENT.sub('', cleaned)
    cleaned = _STRING_LITERAL.sub('', cleaned)

    match = _WRITE_PATTERN.search(cleaned)
    if match:
        raise ValueError(
            f"Write operation blocked. Only SELECT queries are allowed. "
            f"Detected: {match.group()}"
        )


def get_connection(database=None):
    """Return a live pyodbc connection. Retries once on transient failures."""
    client_id = os.getenv("POWERBI_CLIENT_ID")
    client_secret = os.getenv("POWERBI_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("POWERBI_CLIENT_ID and POWERBI_CLIENT_SECRET must be set in .env")

    db = database or DATABASE
    # Wrap DB in braces because the name contains a space and a hyphen.
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={SQL_ENDPOINT};"
        f"Database={{{db}}};"
        "Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={client_id};"
        f"PWD={client_secret};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return pyodbc.connect(conn_str, timeout=60)
        except pyodbc.Error as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    raise ConnectionError(
        f"Failed to connect to {db} after {MAX_RETRIES} attempts. "
        f"Check credentials and Fabric workspace status. Error: {last_error}"
    )


def run_query(sql, conn=None, report_name=None):
    """Run a read-only SQL query and return list of dicts."""
    _check_sql_safety(sql)

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        start = time.time()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]

        rows = []
        for i, row in enumerate(cursor):
            if i >= MAX_RESULT_ROWS:
                log_query(sql, MAX_RESULT_ROWS, int((time.time() - start) * 1000),
                          report_name, error=f"TRUNCATED: Hit {MAX_RESULT_ROWS} row limit")
                break
            rows.append(dict(zip(columns, row)))

        duration_ms = int((time.time() - start) * 1000)
        log_query(sql, len(rows), duration_ms, report_name)
        return rows

    except pyodbc.Error as e:
        log_query(sql, 0, 0, report_name, error=str(e))
        raise RuntimeError(f"Query failed: {e}\nSQL: {sql[:200]}...")
    finally:
        if close_conn:
            conn.close()


def run_parameterized_query(sql, params, conn=None, report_name=None):
    """Run a parameterized SQL query (safe from injection via values)."""
    _check_sql_safety(sql)

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        start = time.time()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]

        rows = []
        for i, row in enumerate(cursor):
            if i >= MAX_RESULT_ROWS:
                break
            rows.append(dict(zip(columns, row)))

        duration_ms = int((time.time() - start) * 1000)
        log_query(f"{sql} [params: {len(params)} values]", len(rows), duration_ms, report_name)
        return rows

    except pyodbc.Error as e:
        log_query(sql, 0, 0, report_name, error=str(e))
        raise RuntimeError(f"Parameterized query failed: {e}\nSQL: {sql[:200]}...")
    finally:
        if close_conn:
            conn.close()


# ── Query Logger ─────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', '.tmp', 'logs')


def log_query(sql, result_count, duration_ms, report_name=None, error=None):
    """Append every query to .tmp/logs/ for audit trail."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        entry = {
            'timestamp': datetime.now().isoformat(),
            'report': report_name,
            'sql': sql[:500],
            'rows_returned': result_count,
            'duration_ms': duration_ms,
        }
        if error:
            entry['error'] = error[:200]
        log_file = os.path.join(LOG_DIR, f"queries_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


# ── Data Freshness Check ─────────────────────────────────────────────────────

def check_data_freshness(conn=None):
    """Check if fact.Final_Table data is current. Returns warning string or None."""
    result = run_query(
        "SELECT MAX(created_at) AS latest FROM fact.Final_Table",
        conn=conn, report_name="freshness_check",
    )
    if not result or not result[0].get('latest'):
        return "WARNING: fact.Final_Table appears empty."

    latest = result[0]['latest']
    if isinstance(latest, str):
        latest = datetime.fromisoformat(latest)

    days_old = (datetime.now() - latest).days
    if days_old > 2:
        return (
            f"WARNING: Data may be stale. Latest activity is "
            f"{latest.strftime('%Y-%m-%d')}, which is {days_old} days ago."
        )
    return None


# ── Pre-built Reports ─────────────────────────────────────────────────────────
#
# All measure definitions below are direct SQL translations of the DAX measures
# in /Users/lakshmana/Claude/Skill-Lync Power BI/PowerBI_DAX_Measures.dax.
# DO NOT modify without cross-checking memory/shared_measures.md.
# ──────────────────────────────────────────────────────────────────────────────

def report_funnel(month, year, conn=None):
    """Same-month funnel: Leads → Demos Scheduled → Demos Completed → Enrolls.

    Direct SQL translation of DAX measures: Leads, Demos_SE, Demos_Completed,
    Enrolls, Same_Month_Enrolls, Total_Sale_Value (+ derived L2D%, L2E%, D2E%).

    Filter is on activity_month / activity_year columns (precomputed in
    fact.Final_Table) — these reflect the activity row's created_at month.
    """
    return run_query(f"""
        SELECT
            COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture'
                THEN lead_id END) AS Leads,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Demo Scheduled'
                THEN lead_id END) AS Demos_SE,

            COUNT(DISTINCT CASE WHEN activity_type_category IN
                ('Demo Completed - Webinars', 'SE Marked Demo Completed')
                THEN lead_id END) AS Demos_Completed,

            COUNT(DISTINCT CASE WHEN Is_Valid_Enroll = 1
                THEN lead_id END) AS Enrolls,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture'
                AND SameMonthEnrolls = 'Enrolls'
                THEN lead_id END) AS Same_Month_Enrolls,

            SUM(CASE WHEN Is_Valid_Enroll = 1 THEN sale_value END) AS Total_Sale_Value
        FROM fact.Final_Table
        WHERE activity_year = {int(year)} AND activity_month = {int(month)}
    """, conn=conn, report_name="funnel")


def report_funnel_by_source(month, year, conn=None):
    """Same-month funnel broken out by source_attribution_final.

    Uses the precomputed source_attribution_final column which already handles
    New Lead → first capture source, Old – Others → last capture source.
    """
    return run_query(f"""
        SELECT
            COALESCE(source_attribution_final, '(none)') AS Source,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture'
                THEN lead_id END) AS Leads,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Demo Scheduled'
                THEN lead_id END) AS Demos_SE,

            COUNT(DISTINCT CASE WHEN Is_Valid_Enroll = 1
                THEN lead_id END) AS Enrolls,

            SUM(CASE WHEN Is_Valid_Enroll = 1 THEN sale_value END) AS Total_Sale_Value
        FROM fact.Final_Table
        WHERE activity_year = {int(year)} AND activity_month = {int(month)}
        GROUP BY source_attribution_final
        ORDER BY Leads DESC
    """, conn=conn, report_name="funnel_by_source")


def report_funnel_by_segment(month, year, conn=None):
    """Same-month funnel by lead_segment (New Lead / Old Lead – Capture / Old – Others)."""
    return run_query(f"""
        SELECT
            lead_segment AS Segment,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture'
                THEN lead_id END) AS Leads,

            COUNT(DISTINCT CASE WHEN activity_type_category = 'Demo Scheduled'
                THEN lead_id END) AS Demos_SE,

            COUNT(DISTINCT CASE WHEN Is_Valid_Enroll = 1
                THEN lead_id END) AS Enrolls,

            SUM(CASE WHEN Is_Valid_Enroll = 1 THEN sale_value END) AS Total_Sale_Value
        FROM fact.Final_Table
        WHERE activity_year = {int(year)} AND activity_month = {int(month)}
        GROUP BY lead_segment
        ORDER BY Leads DESC
    """, conn=conn, report_name="funnel_by_segment")


# ── Manager-level Demo Reports ────────────────────────────────────────────────
#
# Tech Demo = SE-marked demo (1:1, code 393/395). Excludes webinar auto-logs.
# Counts are DISTINCTCOUNT(lead_id) to match DAX measures Demos_Tech_Scheduled /
# Demos_Tech_Completed in docs/PBI_DAX_Measures.dax.
#
# Hierarchy is resolved via dim.[User] (see sql/12_dim_user.sql — deploy first).
# Rollups use CURRENT manager (not manager-at-time-of-activity).
#
# Note on summation: sum of per-DM rows may exceed the grand total when a single
# lead is worked by SEs under different DMs. This is correct and matches PBI.
# ──────────────────────────────────────────────────────────────────────────────

_DEMO_METRICS_SQL = """
    COUNT(DISTINCT CASE WHEN f.activity_type_category = 'SE Marked Demo Schedule'
        THEN f.lead_id END) AS Demos_Tech_Scheduled,

    COUNT(DISTINCT CASE WHEN f.activity_type_category = 'SE Marked Demo Completed'
        THEN f.lead_id END) AS Demos_Tech_Completed
"""

_DEMO_FILTER_SQL = """
    f.activity_year = {year} AND f.activity_month = {month}
    AND f.activity_type_category IN ('SE Marked Demo Schedule', 'SE Marked Demo Completed')
"""


def _demos_by_level(month, year, level, conn=None):
    """Shared implementation for BDA / DM / RSM / AD level demo reports.

    level: one of 'bda', 'dm', 'rsm', 'ad'.
    """
    unassigned = "'(Unassigned)'"
    if level == 'bda':
        group_id, group_name = 'u.user_id', 'u.user_name'
        label = 'BDA'
        extra = f", COALESCE(u.dm_name, {unassigned}) AS DM"
    elif level == 'dm':
        group_id, group_name = 'u.dm_id', 'u.dm_name'
        label = 'DM'
        extra = ''
    elif level == 'rsm':
        group_id, group_name = 'u.rsm_id', 'u.rsm_name'
        label = 'RSM'
        extra = ''
    elif level == 'ad':
        group_id, group_name = 'u.ad_id', 'u.ad_name'
        label = 'AD'
        extra = ''
    else:
        raise ValueError(f"Unknown level: {level}")

    bda_extra_group = f", COALESCE(u.dm_name, {unassigned})" if level == 'bda' else ''
    sql = f"""
        SELECT
            COALESCE({group_name}, {unassigned}) AS {label}{extra},
            {_DEMO_METRICS_SQL}
        FROM fact.Final_Table f
        LEFT JOIN dim.[User] u ON u.user_id = f.bda_id
        WHERE {_DEMO_FILTER_SQL.format(year=int(year), month=int(month))}
        GROUP BY COALESCE({group_name}, {unassigned}){bda_extra_group}
        ORDER BY Demos_Tech_Scheduled DESC
    """
    return run_query(sql, conn=conn, report_name=f"demos_by_{level}")


def report_demos_by_bda(month, year, conn=None):
    """Tech demos (scheduled + completed) by BDA, with their current DM.

    Unique-lead counts. SE-marked demos only (excludes webinar auto-logs).
    """
    return _demos_by_level(month, year, 'bda', conn=conn)


def report_demos_by_dm(month, year, conn=None):
    """Tech demos rolled up to current DM. Unique-lead counts."""
    return _demos_by_level(month, year, 'dm', conn=conn)


def report_demos_by_rsm(month, year, conn=None):
    """Tech demos rolled up to current RSM. Unique-lead counts."""
    return _demos_by_level(month, year, 'rsm', conn=conn)


def report_demos_by_ad(month, year, conn=None):
    """Tech demos rolled up to current AD. Unique-lead counts."""
    return _demos_by_level(month, year, 'ad', conn=conn)


# ── CLI ───────────────────────────────────────────────────────────────────────

REPORTS = {
    'funnel': report_funnel,
    'funnel_by_source': report_funnel_by_source,
    'funnel_by_segment': report_funnel_by_segment,
    'demos_by_bda': report_demos_by_bda,
    'demos_by_dm': report_demos_by_dm,
    'demos_by_rsm': report_demos_by_rsm,
    'demos_by_ad': report_demos_by_ad,
}


def main():
    parser = argparse.ArgumentParser(description="Query Skill-Lync Warehouse")
    parser.add_argument('--query', help='Ad-hoc SELECT query to run')
    parser.add_argument('--report', choices=list(REPORTS.keys()),
                        help='Pre-built report name')
    parser.add_argument('--month', type=int, help='Month (1-12) for reports')
    parser.add_argument('--year', type=int, help='Year (e.g. 2026) for reports')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    if not args.query and not args.report:
        parser.error("Provide either --query or --report")

    if args.report:
        if args.month is None or args.year is None:
            parser.error("--report requires --month and --year")
        rows = REPORTS[args.report](args.month, args.year)
    else:
        rows = run_query(args.query)

    if args.json:
        print(json.dumps(rows, default=str, indent=2))
    else:
        if not rows:
            print("(no rows)")
            return
        cols = list(rows[0].keys())
        print(" | ".join(cols))
        print("-" * 80)
        for r in rows:
            print(" | ".join(str(r.get(c, '')) for c in cols))


if __name__ == '__main__':
    main()
