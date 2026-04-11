# Shared Architecture — Skill-Lync Warehouse

> **Last updated:** 2026-04-10. Complete rewrite based on Crio reference + raw warehouse exploration.
> **Rebuild status:** PLANNING — existing fact.Final_Table is untrusted, building new pipeline from scratch.

---

## Connection

- **Fabric tenant:** same as Crio (same service principal)
- **SQL endpoint:** `twwfdlzo7soexar7f7tzk7wuo4-k6jathn5r3uehhmbl5juoq54da.datawarehouse.fabric.microsoft.com`
- **Database:** `Skill-lync Warehouse` (lowercase 'l', hyphen, space → `{...}` in ODBC)
- **Auth:** `ActiveDirectoryServicePrincipal` via `POWERBI_CLIENT_ID` / `POWERBI_CLIENT_SECRET`
- **Timestamps:** IST (confirmed by user)
- **Refresh:** Daily ~6 AM IST via Fabric pipeline (full rebuild)

---

## Target Architecture (Crio-aligned)

```
LAYER 1 — RAW TABLES
─────────────────────
dbo.ActivityBase          Raw activity log
dbo.ActivityType          Activity code → display name
dbo.Activity_extension    mx_custom1..65 per activity
dbo.Leads                 Lead master (29M rows)
dbo.LeadsExtension        mx_* lead attributes (6.5M)
dbo.lead_filtered_view    Star rank source (4.3M)
dbo.[User]                BDA/user master (6k, bracket required)
dbo.BDATierClassification BDA tier A/B/C/New (42 rows)
dbo.SkillLyncSalesData    Sales truth (999 rows, manual)
dbo.lead_assignment_history Assignment log (955k)
dbo.Call                  Call detail records (357k)
dbo.LeadCaptureMessage    Lead capture messages
dbo.lead_capture_message_metadata  Source/program from messages

LAYER 2 — PREP VIEWS (cleaning + decoding)
───────────────────────────────────────────
prep.unified_leads           Leads + Extension + lead_filtered_view
prep.unified_activity        ActivityBase + ActivityType + Activity_extension
prep.vw_LeadAssignmentActivity  Assignment history (hardcodes code=2200)
prep.vw_unified_activity_appended  unified_activity UNION ALL assignments
prep.unified_lead_capture_message  LeadCaptureMessage + metadata
prep.vw_unified_activity_with_source_attribution  Activity + LCM source

LAYER 3 — FACT TABLE (new build)
────────────────────────────────
fact.Final_Table (rebuilt from scratch)
  - Grain: one row per activity event per lead
  - Activity classification (fixed codes)
  - Source bucket chain
  - Lead join + Domain_group
  - Enrollment from SkillLyncSalesData (first sale per lead by email)
  - BDA: month-level + latest + unified COALESCE
  - All precomputed flags
  - Revenue on enrollment-activity rows ONLY (Crio pattern)
  - Call status from dbo.Call join
  - Test/internal lead exclusion

LAYER 4 — PBI SEMANTIC MODEL (future)
──────────────────────────────────────
fact.Final_Table → DirectLake → PBI → DAX measures → Report pages
```

---

## Key Design Decisions (Crio-aligned)

### Revenue: NO replication
Crio puts sale_amt on the Sales Booking row ONLY. SL must do the same:
- sale_value populated ONLY on rows where `Is_Valid_Enroll = 1` AND the row is the enrollment-trigger row
- Simple `SUM(sale_value)` works without double-counting
- This is the #1 architectural fix

### Activity classification: Fixed bugs
- Demo Scheduled → bifurcated: 'Demo Scheduled - Webinar' (920) + 'Demo Scheduled - Tech' (393)
- Demo Completed → bifurcated: 'Demo Completed - Webinar' (342,921,397) + 'Demo Completed - Tech' (395)
- Demo Rescheduled (318) → own category (was dead code)
- Demo Cancelled (319) → own category
- Call Activity → include codes 506, 507, 777, 2500, 2502
- Junk codes (295, 298, 433, 434, 436) → excluded

### Test/internal exclusion
Email domains to exclude:
- `@skill-lync.com`
- `@cybermindworks.com`
- `@criodo.com`
- `@criodo.co.in`

### Precomputed flags (SL needs)
From Crio reference, SL equivalents to build:
- `Is_Valid_Enroll` (0/1) — same-month enrollment attribution
- `SameMonthEnrolls` ('Enrolls'/'Leads') — Lead Capture rows only
- `lead_segment` ('New Lead'/'Old Lead – Capture'/'Old – Others')
- `has_lead_capture_in_month` (0/1)
- `Is_First_Assignment_Per_Month` (0/1)
- `Is_System_Activity` (0/1) — NEW, for excluding system accounts
- `Enroll_Month_Bucket_Capped` ('M+0'..'M+12')

### Ratios: All bifurcated
Every ratio computed for: Total, PG-only, Individual-only
- L2D% = Demos / Leads
- D2E% = Enrolls / Demos
- L2E% = Enrolls / Leads

---

## Existing Tables in Warehouse (verified 2026-04-10)

### fact schema
| Table | Rows | Status |
|---|---:|---|
| `fact.Final_Table` | 8,441,612 | UNTRUSTED — to be rebuilt |
| `fact.FinalTable` | 5,946,538 | OLD version, can be dropped |
| `fact.Final_Table_New` | 6,750,648 | STAGING artifact, can be dropped |
| `fact.fact_lead_activity` | 7,547,361 | Simplified view, not used |

### dbo schema (raw)
| Table | Rows | Notes |
|---|---:|---|
| `dbo.Leads` | 29,444,317 | Raw LSQ leads |
| `dbo.LeadsExtension` | 6,466,615 | mx_* attributes |
| `dbo.ActivityBase` | 7,486,971 | Raw activity events |
| `dbo.ActivityType` | — | Code→name lookup |
| `dbo.Activity_extension` | — | mx_custom1..65 |
| `dbo.SkillLyncSalesData` | 999 | Sales truth (manual) |
| `dbo.SalesData` | 1,010 | NOT used (legacy) |
| `dbo.SalesDataSumit` | 1,212 | NOT used (legacy, richer) |
| `dbo.BDATierClassification` | 42 | BDA tier dim |
| `dbo.[User]` | 6,012 | User/BDA master |
| `dbo.Call` | 357,264 | Call detail records |
| `dbo.lead_assignment_history` | 954,641 | Assignment log |
| `dbo.lead_filtered_view` | 4,323,478 | Star rank source |
| `dbo.LeadCaptureMessage` | — | Lead capture messages |
| `dbo.lead_capture_message_metadata` | — | Source/program metadata |

### prep schema (views)
All existing prep views are REFERENCE ONLY — may need cleanup during rebuild.

---

## Crio vs Skill-Lync Structural Mapping

| Concept | Crio | SL (new) |
|---------|------|----------|
| Fact table | `fact.FinalTable` (119 cols) | `fact.Final_Table` (rebuild, ~160 cols) |
| Grain | 1 row per activity per lead | Same |
| Funnel | App→TA→1:1→QL→PE→Enroll | Lead Capture→Demo(Web+Tech)→Enroll |
| Enrollment | `ActivityName='Sales Booking'`, sale_amt on that row only | `Is_Valid_Enroll=1`, sale_value on enroll rows only |
| Revenue column | `sale_amt` (single row) | `sale_value` (must be single-row) |
| Source | `AppFillSourceFinal` (1 column) | `source_attribution_final` (keep as canonical) |
| Lead segment | `New_Lead_Segment` | `lead_segment` |
| BDA | `ActivityOwnerEmail` + cascading COALESCE | `bda_id/name` (month→latest COALESCE) |
| BDA tier | `BDA_Category` (Platinum/Gold/Silver/Bronze) | `bda_tier` (A/B/C/New) |
| Calling | Query-time from fact rows | Bring call_status into fact table |
| Demo | Trials + 1:1 Sessions | Webinar Demo + Tech Demo |
| Time window | 6 months | TBD |
| System exclusion | `Is_System_Activity` flag | New: add based on email domain |
| Business Date | Yes (10:30 AM cutoff) | No (user confirmed no calling SOP) |
| Report functions | 28 | Start with ~10, grow |
| Workflows | 15 | Start with ~5, grow |
