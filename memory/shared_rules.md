# Shared Rules — Skill-Lync Warehouse

These are operating rules and known mistakes. Read every session.

---

## Schema Rules

### Rule S1: Use schema prefixes always
Every table reference must have a schema prefix: `fact.`, `dbo.`, or `prep.`. Never just `Final_Table`.

Examples:
- `fact.Final_Table` ✓
- `Final_Table` ✗
- `dbo.[User]` ✓ (User is a reserved word — bracket it)
- `prep.unified_leads` ✓
- `dbo.SkillLyncSalesData` ✓
- `dbo.BDATierClassification` ✓

### Rule S2: Fact table name has an underscore
It is `fact.Final_Table` (with underscore). The Crio equivalent is `fact.FinalTable` (no underscore). Do NOT confuse them.

### Rule S3: The database name has a space and a hyphen
`Skill-lync Warehouse` (with space, with hyphen, lowercase 'l'). In ODBC connection strings it must be wrapped in `{...}`. The connection helper in `tools/query_warehouse.py` already handles this — do not bypass it.

---

## Measure Rules

### Rule M1: Use precomputed flags, NOT hand-rolled date joins
The fact table already includes:
- `Is_Valid_Enroll` (1/0) — correct enroll attribution across all lead segments
- `SameMonthEnrolls` ('Enrolls'/'Leads') — same-month enroll flag for Lead Capture rows
- `Enroll_Month_Bucket_Capped` ('M+0' … 'M+12') — cohort lag buckets
- `lead_segment` ('New Lead' / 'Old Lead – Capture' / 'Old – Others')
- `source_attribution_final` (handles New vs Old source attribution)
- `Is_First_Assignment_Per_Month` (1/0) — first BDA assignment per lead per month

NEVER rebuild these in your own SQL. The logic is non-trivial (e.g. Old – Others enrolls require a window function over capture-presence per month). Use the columns.

### Rule M2: Enrolls = Is_Valid_Enroll, not enroll_date IS NOT NULL
A row with `enroll_date IS NOT NULL` may be invalid (e.g. enrolled BEFORE the capture date — those are pre-existing customers, not attributable to this month). Always filter on `Is_Valid_Enroll = 1` for enrollment counts.

### Rule M3: Demos has two flavors
- `Demos_SE` (Scheduled): `activity_type_category = 'Demo Scheduled'`
- `Demos_Completed`: `activity_type_category IN ('Demo Completed - Webinars', 'SE Marked Demo Completed')`

The DAX `D2E%` measure uses `Demos_SE` as denominator. If the user asks for "demo to enroll", ask which one they mean.

### Rule M4: Same Month Enrolls is a subset of Enrolls
`Same_Month_Enrolls` filters on `activity_type_category='Lead Capture'` AND `SameMonthEnrolls='Enrolls'`. This excludes `Old – Others` segment enrollments. `Enrolls` (using `Is_Valid_Enroll=1`) is the broader count that INCLUDES Old – Others.

If a user asks "how many enrolls in March?", clarify whether they want:
- All valid enrolls in March (use `Is_Valid_Enroll=1`), or
- Only New + Old Lead – Capture enrolls (use `SameMonthEnrolls='Enrolls'`)

---

## Time Rules

### Rule T1: Use activity_year + activity_month columns
The fact table has precomputed `activity_year` and `activity_month` integers (along with `activity_month_start` for date filtering). Use these in WHERE clauses — do NOT call `YEAR(created_at)` repeatedly.

### Rule T2: Filter on activity_month, not enroll_month, for funnel reports
The funnel measures count leads/demos/enrolls **in the activity month**. The `enroll_date` is a separate column for cohort-lag analysis only. For "March 2026 funnel", filter on `activity_year=2026 AND activity_month=3`.

---

## BDA / Owner Rules

### Rule B1: Two BDA columns exist — pick the right one
- `bda_id` / `bda_name` — month-level first, falls back to latest (use this by default)
- `assigned_bda_id` / `assigned_bda_name` — strictly the BDA who got the lead THIS month (NULL if no assignment that month)
- `latest_bda_id` / `latest_bda_name` — most recent BDA ever (always populated if ever assigned)

For "performance this month" use `assigned_bda_*`. For "current owner" use `latest_bda_*`. For most cases use the unified `bda_*`.

### Rule B2: BDA tier is joined from BDATierClassification
`bda_tier` and `bda_status` come from `dbo.BDATierClassification` joined on email. Already on the fact row.

---

## Mistakes Log
*(Append every new mistake here as you discover it. Date + what you did wrong + what's right.)*

- *(none yet — agent is in v1)*
