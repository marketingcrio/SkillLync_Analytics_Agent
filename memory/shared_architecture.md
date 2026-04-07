# Shared Architecture — Skill-Lync Warehouse

**Source of truth (DDL):** `/Users/lakshmana/Claude/Skill-Lync Power BI/Final_Table_Create.sql` and `sp_Refresh_Final_Table.sql`
**View definitions:** `unified_leads_view.sql`, `vw_unified_activity_appended.sql` in the same folder.

---

## Connection

- **Fabric tenant:** same as Crio (same service principal)
- **SQL endpoint:** `twwfdlzo7soexar7f7tzk7wuo4-k6jathn5r3uehhmbl5juoq54da.datawarehouse.fabric.microsoft.com`
- **Database:** `Skill-lync Warehouse` (note: lowercase 'l', hyphen, space — must be wrapped in `{...}` in ODBC)
- **Auth:** `ActiveDirectoryServicePrincipal` using `POWERBI_CLIENT_ID` + `POWERBI_CLIENT_SECRET`
- **Refresh:** `EXEC fact.sp_Refresh_Final_Table;` runs daily ~6:00 AM IST via Fabric pipeline `PL_Refresh_SkillLync_Final_Table` (full rebuild — DROP + CREATE).

---

## Data Pipeline

```
Raw LSQ tables (Leads, LeadsExtension, unified_activity, ...)
    │
    ├─► prep.unified_leads                     (view — leads + extension + lead_filtered_view)
    ├─► prep.vw_unified_activity_appended      (view — unified_activity ∪ vw_LeadAssignmentActivity)
    └─► prep.vw_unified_activity_with_source_attribution
                │
                ▼
         fact.Final_Table  (full rebuild via sp_Refresh_Final_Table, daily 6 AM IST)
                │
                ▼
         Power BI dataset
```

---

## Tables & Views

### Fact
| Table | Purpose | Notes |
|-------|---------|-------|
| `fact.Final_Table` | The single denormalized table you query for funnel analysis | Activity-grain. One row per activity. Lead + BDA + enroll columns joined in. Rebuilt fully each day. |

### Prep Views (don't query directly unless debugging)
| View | Purpose |
|------|---------|
| `prep.unified_leads` | Leads + LeadsExtension + lead_filtered_view (for star rank) |
| `prep.vw_unified_activity_appended` | Activities ∪ Lead Assignment Activities |
| `prep.vw_unified_activity_with_source_attribution` | Adds source bucket attribution to activities |
| `prep.vw_LeadAssignmentActivity` | Source for assignment activity rows |

### Dim / Lookup Tables
| Table | Purpose |
|-------|---------|
| `dbo.[User]` | BDA / activity owner lookup (`first_name`, `last_name`, `email`, `id`) — **bracket [User] always** |
| `dbo.BDATierClassification` | BDA tier + status, joined on email |
| `dbo.SkillLyncSalesData` | Sales / enrollment ground truth (joined on email) — source of `sale_value`, `sale_program`, `enroll_date` |
| `dbo.lead_filtered_view` | Star rank source |

---

## fact.Final_Table — Key Columns

### Identifiers
- `lead_id` — the prospect ID (use this for DISTINCTCOUNT)
- `prospect_id` — same thing in some contexts
- `email_address`
- `created_at` — activity timestamp

### Activity classification
- `activity_type_activity_code` — raw LSQ code (integer)
- `activity_type_display_name` — raw LSQ name
- `activity_type_category` — **bucketed** (the column you should filter on). Possible values:
  - `'Lead Capture'` — 50+ codes (form fills, page visits, etc.)
  - `'Demo Scheduled'` — codes 315, 316, 259, 290, 920
  - `'Demo Cancelled'` — code 319
  - `'Demo Rescheduled'` — code 318
  - `'Demo Completed - Webinars'` — codes 342, 921, 397
  - `'SE Marked Demo Schedule'` — code 393
  - `'SE Marked Demo Completed'` — code 395
  - `'Payment Activity'` — codes 98, 9629
  - `'Call Activity'` — code 506
  - `'Page Visit'` — codes 2, 510
  - `'Lead Assignment Activity'` — code 2200
  - `'Other / Unknown'` — anything else

### Source attribution
- `Source_Bucket` — bucket from activity-level `lc_source` (Direct Grow, Youtube, Meta, Linkedin, Google Ads, Email, Whatsapp, Organic, Direct, Others)
- `Source_Bucket_Final` — same, with Email→Meta override based on Lead_Source_Campaign
- `first_lead_capture_source_of_month` — for lead_segment with capture-this-month
- `last_lead_capture_source` — for `Old – Others`
- `source_attribution_final` — **the unified one** (use this for source breakdowns)

### Lead segment
- `lead_segment` — `'New Lead'` / `'Old Lead – Capture'` / `'Old – Others'`
- `has_lead_capture_in_month` — 1 if the lead has any Lead Capture activity in the activity month

### Enrollment
- `enroll_date` — first sale date for the lead (NULL if never enrolled)
- `sale_value`, `sale_program`, `sale_ind_pg` — joined from SkillLyncSalesData
- `Is_Valid_Enroll` — **THE flag for valid enrolls** (handles all segments correctly). Use this for Enrolls counts.
- `SameMonthEnrolls` — `'Enrolls'` / `'Leads'` (Lead Capture rows only)
- `Enroll_Month_Bucket_Capped` — `'M+0'` … `'M+12'` cohort bucket (Lead Capture rows only)

### Time
- `activity_year`, `activity_month`, `activity_day` — integers, precomputed
- `activity_month_name`, `activity_month_start`
- `lead_created_month`, `enroll_year`, `enroll_month`, `enroll_month_start`

### BDA / Assignment
- `assigned_bda_id`, `assigned_bda_name` — month-level (NULL if no assignment that month)
- `latest_bda_id`, `latest_bda_name` — most recent BDA ever assigned
- `bda_id`, `bda_name` — COALESCE(month, latest) — **use this by default**
- `bda_tier`, `bda_status` — from BDATierClassification
- `assigned_bda_tier`, `assigned_bda_status`, `latest_bda_tier`, `latest_bda_status`
- `Is_First_Assignment_Per_Month` — 1 only on the first assignment row per lead per month
- `assignment_source` — `'From Capture'` / `'Old Lead'` / NULL
- `p1_score_at_assign`, `p1_star_rank_at_assign` — month-specific star rank (4 Star / 3 Star / 2 Star / 1 Star)
- `latest_p1_score`, `latest_p1_star_rank` — latest overall

### Lead attributes (from LeadsExtension)
- `mx_degree`, `mx_department`, `mx_domain`, `mx_year_of_passing`, `mx_company_name`, `mx_job_title`, `mx_designation`, `mx_job_experience`, `mx_current_education_status`, `mx_branch_of_education`, `mx_working_professional_or_experienced`, `mx_years_of_experience`, `mx_student_or_working_professional`, `mx_interested_courses`, `mx_course_interested_in`, `mx_webinar_interest`
- `Domain_group` — bucketed mx_domain (Mechanical, Electric Vehicles, Embedded Systems, Software / IT, CAE / Simulation, Electrical, Design, Civil, Others / Unknown)

### Program
- `Program_Interested` — Lead Capture rows only (parsed from `program_name` or `lc_source`)

---

## Crio vs Skill-Lync Cheat Sheet

Quick reference if you've worked on the Crio agent before:

| Concept | Crio | Skill-Lync |
|---------|------|-----------|
| Fact table | `fact.FinalTable` | `fact.Final_Table` |
| Funnel stages | App → TA → 1:1 → QL → PE → Enroll | Lead → Demo → Enroll |
| Enroll definition | `ActivityName='Sales Booking'` | `Is_Valid_Enroll = 1` |
| Source column | `AppFillSourceFinal` | `source_attribution_final` |
| Lead segment | `New_Lead_Segment` | `lead_segment` |
| Sale amount | `sale_amt` | `sale_value` |
| Activity name col | `ActivityName` | `activity_type_category` |
| Date filter | `Year`, `MonthNo` | `activity_year`, `activity_month` |
| BDA | `se_name`, `owner_Id` | `bda_name`, `bda_id` |
| Star rank | (n/a) | `latest_p1_star_rank` |

**Do not** translate Crio measures to Skill-Lync by analogy. The funnel structure is fundamentally different.
