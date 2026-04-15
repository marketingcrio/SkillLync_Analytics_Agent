# ============================================================
# Fabric Notebook — Daily Warehouse Refresh
# ------------------------------------------------------------
# Schedule: 05:00 IST daily (set in Fabric notebook scheduler)
# Rebuilds:  dim.User, fact.Final_Table, fact.CallDetail
# Gate:      aborts if dbo.ActivityBase is >1 day stale
# Failure:   raises — wrap in a Fabric Data Pipeline with an
#            Office365 Outlook "On Failure" email activity.
# ============================================================

import os
import time
import pyodbc
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# ── Configuration ───────────────────────────────────────────
# Store POWERBI_CLIENT_ID / POWERBI_CLIENT_SECRET in Fabric
# workspace key vault and reference as environment variables.

SQL_ENDPOINT = os.getenv(
    "SQL_ENDPOINT",
    "twwfdlzo7soexar7f7tzk7wuo4-k6jathn5r3uehhmbl5juoq54da.datawarehouse.fabric.microsoft.com",
)
DATABASE = os.getenv("WAREHOUSE_DB", "Skill-lync Warehouse")
CLIENT_ID = os.environ["POWERBI_CLIENT_ID"]
CLIENT_SECRET = os.environ["POWERBI_CLIENT_SECRET"]

# SQL files hosted in Fabric Files area (sync'd from git). Adjust to
# wherever the repo is mounted in the workspace — e.g. OneLake Files or
# a lakehouse attachment. Each file must contain a single, idempotent
# CTAS script (DROP TABLE IF EXISTS + CREATE TABLE AS SELECT).
REPO_SQL_DIR = os.getenv("REPO_SQL_DIR", "/lakehouse/default/Files/Skill_Lync_Agent/sql")

DAILY_JOBS = [
    ("dim.User",          f"{REPO_SQL_DIR}/12_dim_user.sql"),
    ("fact.Final_Table",  f"{REPO_SQL_DIR}/08_fact_final_table.sql"),
    ("fact.CallDetail",   f"{REPO_SQL_DIR}/10_fact_call_detail.sql"),
]

FRESHNESS_MAX_LAG_DAYS = 1   # fail if dbo.ActivityBase max(created_at) < today - 1
POST_CHECK_MAX_LAG_DAYS = 1  # fail if fact.Final_Table max(created_at) < today - 1

# IST today (Fabric runtime may be UTC — convert explicitly)
IST = timezone(timedelta(hours=5, minutes=30))
TODAY_IST = datetime.now(IST).date()


# ── Connection helper ──────────────────────────────────────

def get_conn():
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={SQL_ENDPOINT};"
        f"Database={{{DATABASE}}};"
        "Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={CLIENT_ID};"
        f"PWD={CLIENT_SECRET};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    # autocommit required — CTAS cannot run inside a transaction on Fabric
    return pyodbc.connect(conn_str, timeout=60, autocommit=True)


def run_scalar(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchone()[0]


# ── Step 1: Source freshness gate ───────────────────────────

print("=" * 60)
print(f"STEP 1: Source freshness check — today IST = {TODAY_IST}")
print("=" * 60)

with get_conn() as conn:
    src_max = run_scalar(conn, "SELECT MAX(created_at) FROM dbo.ActivityBase")

if src_max is None:
    raise RuntimeError("dbo.ActivityBase is empty — source ingestion broken.")

src_max_date = src_max.date() if hasattr(src_max, "date") else src_max
lag_days = (TODAY_IST - src_max_date).days

print(f"  dbo.ActivityBase max(created_at) = {src_max}")
print(f"  Lag from today IST               = {lag_days} day(s)")

if lag_days > FRESHNESS_MAX_LAG_DAYS:
    raise RuntimeError(
        f"Source stale: dbo.ActivityBase max is {src_max_date}, "
        f"{lag_days} days behind today ({TODAY_IST}). "
        f"Upstream LSQ→Fabric pipeline likely failed. Aborting rebuild."
    )

print("  ✅ Source is fresh — proceeding.")


# ── Step 2: Parallel rebuild ────────────────────────────────

print()
print("=" * 60)
print("STEP 2: Rebuilding tables in parallel")
print("=" * 60)


def run_job(name, path):
    start = time.time()
    with open(path, "r", encoding="utf-8") as f:
        sql_text = f.read()

    with get_conn() as conn:
        cur = conn.cursor()
        # Fabric warehouse supports multi-statement batches separated by ; —
        # but DROP TABLE + CREATE TABLE in one execute works fine.
        cur.execute(sql_text)

    return name, time.time() - start


failures = []
with ThreadPoolExecutor(max_workers=len(DAILY_JOBS)) as pool:
    futures = {pool.submit(run_job, n, p): n for n, p in DAILY_JOBS}
    for fut in as_completed(futures):
        name = futures[fut]
        try:
            _, elapsed = fut.result()
            print(f"  ✅ {name:20s}  {elapsed:6.1f}s")
        except Exception as e:
            print(f"  ❌ {name:20s}  {type(e).__name__}: {e}")
            failures.append((name, e))

if failures:
    raise RuntimeError(
        f"{len(failures)} job(s) failed: "
        + ", ".join(n for n, _ in failures)
    )


# ── Step 3: Post-check — did fact.Final_Table actually land? ─

print()
print("=" * 60)
print("STEP 3: Post-refresh verification")
print("=" * 60)

with get_conn() as conn:
    fact_max = run_scalar(conn, "SELECT MAX(created_at) FROM fact.Final_Table")
    fact_rows = run_scalar(conn, "SELECT COUNT(*) FROM fact.Final_Table")
    dim_rows = run_scalar(conn, "SELECT COUNT(*) FROM dim.[User]")
    call_max = run_scalar(conn, "SELECT MAX(created_at) FROM fact.CallDetail")

fact_max_date = fact_max.date() if hasattr(fact_max, "date") else fact_max
fact_lag = (TODAY_IST - fact_max_date).days

print(f"  fact.Final_Table rows    = {fact_rows:,}")
print(f"  fact.Final_Table max     = {fact_max}  ({fact_lag} day(s) lag)")
print(f"  fact.CallDetail max      = {call_max}")
print(f"  dim.User rows            = {dim_rows:,}")

if fact_lag > POST_CHECK_MAX_LAG_DAYS:
    raise RuntimeError(
        f"Post-check failed: fact.Final_Table max = {fact_max_date}, "
        f"{fact_lag} days behind today. Rebuild wrote but data is stale."
    )

if fact_rows < 1_000_000:
    raise RuntimeError(
        f"Post-check failed: fact.Final_Table has only {fact_rows:,} rows — "
        "rebuild likely truncated. Expected ≥1M."
    )

print()
print("✅ Daily refresh complete.")
