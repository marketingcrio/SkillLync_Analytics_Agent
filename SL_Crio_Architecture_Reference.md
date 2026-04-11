# Crio Analytics Agent — Architecture Reference for Skill-Lync Rebuild

**Purpose:** This document answers every structural question the SL Agent needs to rebuild Skill-Lync's analytics from clean foundations. Every column name, SQL snippet, and design decision is from the live Crio system as of 2026-04-10.

**How to use this document:** Read it section by section before building each layer. Cross-reference against [SL_Data_Discovery_Questionnaire.md](SL_Data_Discovery_Questionnaire.md) for the SL-specific gaps and questions that need business answers before implementation.

---

## Critical Warnings Before You Start

1. **Do not patch the existing SL structure.** There are 3 competing fact tables, 10+ duplicate prep views, and a 1,010-row manual SalesData spreadsheet. Rebuild from clean foundations.

2. **Build one layer at a time.** First lock the raw-to-prep pipeline, then build ONE fact table, then define measures on top. Do not attempt all layers simultaneously.

3. **The biggest risk is measure definition ambiguity.** Crio spent months discovering that `SameMonthEnrolls='Enrolls'` is NOT the same as `ActivityName='Sales Booking'`. SL's `Is_Valid_Enroll = 1` flag is a single point of failure — if its computation logic is undocumented or wrong, every downstream number is wrong and nobody will know. Document the EXACT logic and cross-validate against `dbo.SalesData` before trusting it.

4. **Revenue double-counting.** SL's `fact.Final_Table` appears to have `sale_value` populated on multiple activity rows for the same lead. A naive `SUM(sale_value)` will massively overcount. Either: (a) ensure `sale_value` is NULL on all non-enrollment rows, or (b) ALWAYS filter with `WHERE Is_Valid_Enroll = 1` when summing. **Verify this immediately before building anything else.**

---

## A. Fact Table Structure

### A1. Full Column List — Crio's `fact.FinalTable` (119 columns)

#### Identity & Activity (the grain)

These columns define what each row IS — one activity event for one lead.

| Column | Type | Description |
|--------|------|-------------|
| `RelatedProspectId` | varchar | Lead/prospect UUID — the primary key for lead-level analysis |
| `RelatedProspectActivityId` | varchar | Unique activity row ID |
| `ActivityEvent` | int | Numeric activity type code (e.g., 22 = Outbound Call, 30 = Sales Booking) |
| `ActivityName` | varchar | Human-readable activity name (decoded from ActivityEvent) |
| `owner_Id` | varchar | UUID of the user who performed this activity |
| `Activity_date` | datetime2 | Timestamp of the activity (IST, converted from UTC in prep layer) |
| `ActivityYM` | int | Activity year-month as YYYYMM integer (e.g., 202604) |
| `LeadYM` | int | Lead creation year-month as YYYYMM integer |

**SL equivalent:** Your `fact.Final_Table` uses `prospect_id` (= RelatedProspectId), `activity_type_activity_code` (= ActivityEvent), `activity_type_display_name` (= ActivityName), `created_at` / `activity_date` (= Activity_date). You have `activity_year` + `activity_month` instead of a single `ActivityYM` — both work, but a combined YYYYMM integer is handy for quick comparisons like `LeadYM = ActivityYM`.

---

#### Activity-Specific Fields (decoded from mx_Custom per activity type)

These columns are the result of decoding generic `mx_Custom_1..30` columns into named fields. **Different activity types use the same mx_Custom column for different purposes** — the prep layer handles this mapping.

| Column | Populated On (Activity Type) | Source mx_Custom | Description |
|--------|------------------------------|-----------------|-------------|
| `session_duration` | Trial (267) | mx_Custom_2 | Trial session duration in minutes |
| `session_date` | Call Attempt (428) | mx_Custom_4 | Date of booked session (non-null = booking exists) |
| `sale_amt` | Sales Booking (30) | mx_Custom_2 | Full booked sale amount (NOT installment) |
| `date_of_completion` | Various | varies | Completion date for certain activities |
| `source` | App Fill (262) | mx_Custom_5 | UTM source at app fill |
| `campaign` | App Fill (262) | mx_Custom_8 | UTM campaign at app fill |
| `medium` | App Fill (262) | mx_Custom_9 | UTM medium at app fill |
| `program_interested` | App Fill (262), Booking (30) | mx_Custom_19 / mx_Custom_1 | Product UUID or program name |
| `content` | App Fill (262) | mx_Custom_6 | UTM content |
| `status` | App Fill (262), Call (22) | mx_Custom_1 / mx_Custom_7 | App: 'FullFill'/'HalfFill'/'OtherLead'. Call: 'Answered'/etc. |
| `session_type` | Session (417) | mx_Custom_5 | 'SALES_DEMO_DE', 'SALES_DEMO_SE', 'ONBOARDING', etc. |
| `session_name` | Session (417), Trial (267) | mx_Custom_3 | Name of the session |
| `type` | Payment Capture (256) | mx_Custom field | 'Provisional Enrollment' for PEs |
| `lead_stage_change` | Stage Change (355) | mx_Custom_16 | Stage transition value |
| `reason_for_marking_as_dnd` | Stage Change (355) | mx_Custom_17 | DND reason |
| `reason_for_marking_as_irrelevant` | Stage Change (355) | mx_Custom_14 | Irrelevant reason |
| `reason_for_marking_as_Cold` | Stage Change (355) | mx_Custom_15 | Cold reason |
| `se_name` | Assignment (384), Booking (30) | mx_Custom_1 / mx_Custom_4 | BDA assigned to (384) or BDA who worked the lead (30) |
| `se_email` | Assignment (384) | mx_Custom_2 | BDA email assigned to |
| `ME_ID` | ME_Completion (268) | mx_Custom field | Micro Experience identifier |
| `nuture_call_Status` | Call Attempt (428) | mx_Custom_2 | 'Connected'/'Not Connected'/etc. |
| `Comms_Type` | Reactivation Comms (486) | mx_Custom field | Communication type |
| `Comms_CTA` | Reactivation Comms (486) | mx_Custom field | Call-to-action type |
| `Reactivation_Notes` | Reactivation (486) | mx_Custom field | Notes on reactivation |

**SL equivalent:** Your `dbo.Activity_extension` has `mx_custom1..65` (even more than Crio's 30). The critical gap is: **you need a mapping document that says "for activity_code X, mx_custom1 = Y, mx_custom2 = Z"**. Without this, the mx_custom columns are useless noise. Your `fact.Final_Table` seems to have already decoded some (e.g., `activity_type_category`, `program_name`, `course_id`), but the fact table only carries `mx_custom39` from the 65 available — meaning 64 columns of potential signal are being lost.

---

#### Lead Master Fields (SNAPSHOT — from dbo.Leads join)

These are joined from the Leads table during the fact table build. **They reflect CURRENT state and change when the lead is updated.** NEVER use these for historical/time-based analysis.

| Column | Type | Description | SNAPSHOT? |
|--------|------|-------------|:---------:|
| `lead_createdOn_date` | datetime2 | When the lead was first created | No (immutable) |
| `mx_Working_Status` | varchar | 'CWP' / 'NWP' / 'STU' / null | YES |
| `mx_Program_Interested` | varchar | Current program interest | YES |
| `EmailAddress` | varchar | Lead's email | No (immutable) |
| `ProspectStage` | varchar | Current stage (Discovery, Prospect, Closed Won, etc.) | YES |
| `mx_location` | varchar | Location | YES |
| `mx_City` | varchar | City | YES |
| `Grad_Year` | varchar | Raw graduation year | No (rarely changes) |
| `Highest_Qualification` | varchar | Education level | YES |
| `mx_Job_Domain` | varchar | Job domain | YES |
| `Job_Role` | varchar | Current job role | YES |
| `mx_Cohort` | varchar | Cohort classification | YES |
| `Current_Owner` | varchar | Current CRM owner UUID | YES |
| `Current_OwnerName` | varchar | Current owner name | YES |
| `Current_OwnerEmail` | varchar | Current owner email | YES |
| `MobileNumber` | varchar | Phone number | No |

**SL equivalent:** Your `fact.Final_Table` similarly joins lead fields: `prospect_stage`, `lead_owner_id`, `mx_degree`, `mx_department`, etc. These are snapshots too. Your triple-BDA columns (`assigned_bda_*` vs `latest_bda_*` vs `bda_*`) show you're already aware of the snapshot problem for BDA attribution — good. Apply the same discipline to ALL lead-level fields.

---

#### Calendar Decomposition

| Column | Description |
|--------|-------------|
| `Year` | Activity year (e.g., 2026) |
| `MonthNo` | Activity month number (1-12) |
| `Month` | Activity month name ('January', 'February', etc.) |
| `QuarterNo` | Quarter number (1-4) |
| `Quarter` | Quarter label ('Q1', 'Q2', etc.) |
| `Day` | Day of month (1-31) |
| `Activity_Hour` | Hour of activity (0-23) |
| `WeekOfMonth` | Week number within the month (1-5) |

**Business Date columns (Crio-specific):**

| Column | Description |
|--------|-------------|
| `Business_Date` | Activities before 10:30 AM IST are moved to the PREVIOUS day |
| `Business_Year` | Year from Business_Date |
| `Business_MonthNo` | Month from Business_Date |
| `Business_Month` | Month name from Business_Date |
| `Business_Day` | Day from Business_Date |

The Business_Date logic:
```sql
CASE WHEN DATEPART(HOUR, Activity_date) * 60 + DATEPART(MINUTE, Activity_date) < 630
     THEN DATEADD(DAY, -1, CAST(Activity_date AS DATE))
     ELSE CAST(Activity_date AS DATE)
END
```

**SL consideration:** Does SL have a calling SOP with a similar time cutoff? If BDAs start calling at a specific time, early-morning activities from the previous night's late shift should count for the previous day. If not needed, skip these columns.

---

#### Precomputed Date Fields (per-lead, per-month windows)

These are computed via window functions during the fact table build. They enable enrollment lag, pipeline aging, and conversion analysis without re-computing at query time.

| Column | Description |
|--------|-------------|
| `App_Date` | Date of app fill activity (on app fill rows only) |
| `FirstAppFillDate` | First-ever app fill date for this lead |
| `Enroll_Date` | Date of Sales Booking activity |
| `OneToOne_Date` | Date of 1:1 session |
| `First_OneToOne_Date` | First-ever 1:1 date for this lead (all-time) |
| `Latest_OneToOne_Date` | Most recent 1:1 date for this lead (all-time) |
| `First_OneToOne_Date_Monthly` | First 1:1 in this activity month |
| `Latest_OneToOne_Date_Monthly` | Latest 1:1 in this activity month |
| `Provisional_Date` | Date of Provisional Enrollment activity |
| `Lead_Qual_Date` | Date of Lead Qualification Activity |
| `LatestTrialDate` | Most recent trial date |
| `FirstAppWeek` | Week number of first app fill |
| `Trial_SessionDuration_MaxPerLeadMonth` | Max trial duration per lead per month |

**SL equivalent:** Your fact table has `enroll_date`, `enroll_year/month/day`, `lead_created_month`, `latest_assignment_date`. You're missing the 1:1 session date tracking (first/latest demo dates) and the trial date tracking, which are needed for pipeline aging and conversion lag analysis.

---

#### Precomputed Flag Columns

These are the columns that make the fact table powerful. Each one encodes a business rule that would otherwise need to be re-implemented in every query.

| Column | Values | Logic | What It Enables |
|--------|--------|-------|-----------------|
| `SameMonthApps` | 'Applications' / 'Leads' | Lead had an app fill (FullFill or OtherLead) in this ActivityYM | SMApp measure — the top of the funnel |
| `SameMonthEnrolls` | 'Enrolls' / 'Leads' | Lead enrolled in this ActivityYM (Enroll_Date month = ActivityYM) | Same-month enrollment attribution |
| `SameMonthOne_to_One` | 'One-to-One' / 'Leads' | Lead had a 1:1 session in this ActivityYM | Same-month session tracking |
| `SameMonthProvisional` | 'Provisional' / 'Leads' | Lead had PE in this ActivityYM | Same-month PE tracking |
| `SameMonthQualified` | 'Qualified' / 'Leads' | Lead had Lead Qualification Activity in this ActivityYM | **NOT the same as QL** |
| `New_Lead_Segment` | 'New Lead' / 'Old Lead - App Fill' / 'Old Lead - Others' | Based on LeadYM vs ActivityYM comparison | Lead recency segmentation |
| `New_Lead_Segment_V2` | Same + reactivation logic | V2 adds reactivation classification | Refined segmentation |
| `Is_System_Activity` | 0 / 1 | owner_Id matches one of 15 known system UUIDs | Excluding bot/system activities from BDA analysis |
| `Has_Assignment_This_Month` | 0 / 1 | Lead was assigned to a BDA in this month | Assignment coverage tracking |
| `HasTrialThisMonth` | 0 / 1 | Lead attended a trial this month | Trial tracking |
| `HasSessionThisMonth` | 0 / 1 | Lead had a SALES_DEMO session this month (excludes ONBOARDING) | 1:1 tracking |
| `HasTrialBeforeThisMonth` | 0 / 1 | Lead attended trial in a prior month | Repeat trial identification |
| `Reactivated_Lead` | 0 / 1 | Per-ROW flag for gap > 90 days | **UNRELIABLE for lead-level analysis** |
| `Enrolled_SameWeek` | 0 / 1 | Enrolled in same week as first app fill | Speed-to-enroll analysis |
| `Enrolled_ComingWeeks` | 0 / 1 | Enrolled in subsequent weeks | Lag analysis |
| `Enrolled_SameMonth` | 0 / 1 | Enrolled in same month as app fill | Same-month conversion |
| `Valid_Mobile_Flag` | 0 / 1 | Lead has a valid Indian mobile number (+91) | Filtering for calling analysis |
| `Trial_Lead_Flag` | 'SQL_trial' / 'MQL_trial' / null | SQL = BDA booked + attended; MQL = attended without booking | Marketing vs sales qualified |
| `Priority_Leads` | varchar | Lead priority classification | Lead prioritization |
| `App_Assignment_Status` | varchar | Status of lead relative to assignment flow | Assignment tracking |
| `BDA_Category` | 'Platinum' / 'Gold' / 'Silver' / 'Bronze' | Monthly BDA tier from dbo.BDA_Mapping | BDA performance segmentation |

**SL equivalent columns you already have:**
- `Is_Valid_Enroll` (0/1) — similar to SameMonthEnrolls but binary
- `Is_First_Assignment_Per_Month` (0/1) — similar to Has_Assignment_This_Month
- `has_lead_capture_in_month` (0/1) — similar to SameMonthApps
- `lead_segment` ('New Lead' / 'Old Lead – Capture' / 'Old – Others') — maps to New_Lead_Segment
- `SameMonthEnrolls` — you have this too

**SL gaps — columns you need to add:**
- `Is_System_Activity` — you have no way to exclude system/bot activities
- `HasSessionThisMonth` / trial flags — demo tracking flags
- `Trial_Lead_Flag` — MQL vs SQL classification
- `Sales_Cycle_Days` / bucketing — enrollment lag columns
- `Business_Date` — if SL has a calling time cutoff
- BDA tier on fact table — you have `assigned_bda_tier` already, which is good

---

#### Derived Bucketing Columns

These enable grouping and visualization without runtime computation.

| Column | Values | Logic |
|--------|--------|-------|
| `Enroll_Month_Bucket_Capped` | 'M+0', 'M+1', 'M+2', 'M+3', 'M+4', 'M+5' | Months between first app fill and enrollment date |
| `Sales_Cycle_Days` | integer | Days from first app fill to Sales Booking date |
| `Sales_Cycle_Bucket` | '0-7 days', '8-14 days', '15-30 days', '31-60 days', '60+ days' | Bucketed Sales_Cycle_Days |
| `Days_Session_To_Enroll` | integer | Days from 1:1 session to enrollment |
| `Session_To_Enroll_Bucket` | varchar | Bucketed session-to-enroll days |
| `Session_To_Enroll_Sort` | int | Sort order for the bucket |
| `Days_Session_To_Enroll_Monthly` | integer | Monthly variant |
| `Session_To_Enroll_Bucket_Monthly` | varchar | Monthly variant |
| `Days_Since_Latest_OneToOne` | integer | Pipeline aging: days since last 1:1 |
| `OneToOne_Aging_Bucket` | varchar | '0-7 days', '8-14 days', '15-30 days', '31-60 days', '60+ days' |
| `OneToOne_Aging_Sort` | int | Sort order |
| `OneToOne_Conversion_Status` | 'Converted' / 'Open' | Global: did the lead who had a 1:1 eventually enroll? |
| `OneToOne_Conversion_Status_Monthly` | 'Converted' / 'Open' | Monthly variant (resets each month) |
| `Total_OneToOne_Sessions` | integer | Count of 1:1 sessions per lead |
| `AttendCategory` / `AttendCategory_V2` | varchar | Attendance classification |
| `CallDurationCategory` | varchar | Call duration bucketing |
| `Clean_Grad_Year` | varchar | Cleaned graduation year (handles M/YYYY format) |
| `Grad_Year_Bucket` | varchar | '2025', '2026', '2024 or earlier', etc. |
| `Lead_Intent_Team` | varchar | Derived from mx_Working_Status + Grad_Year |
| `TrialWorkshop_Duration_Bucket` | '<30 min', '30-60 min', '> 60 min' | Trial quality classification |
| `ProgramCategory_LeadLevel` | varchar | Program category at lead level |
| `Source_Bucket` | varchar | Source classification bucket |

**SL equivalent:** You have `Enroll_Month_Bucket_Capped` and `Domain_group`. You're missing all the session-to-enroll lag columns, pipeline aging columns, and call duration buckets.

---

#### Attribution Columns

| Column | Description |
|--------|-------------|
| `SourceCampaign_AtAppFill` | Campaign key from the app fill activity row — used for joining with Daily_Spends |
| `AppFillSourceFinal` | Canonical lead-level source: first-touch at app fill, with IVR fallback, then 'No APP/IVR' |

**Attribution logic:**

| Priority | Condition | Value |
|----------|-----------|-------|
| 1 | Lead has App Fill (AE 262) with status IN ('FullFill','OtherLead') | `source` from that row |
| 2 | Lead has IVR Communication (AE 444) but no app fill | 'IVR' |
| 3 | Fallback | 'No APP/IVR' |

**SL equivalent:** You have `Lead_Source`, `Source_Bucket`, `Source_Bucket_Final`, `source_attribution_final`, `first_lead_capture_source_of_month`, `last_lead_capture_source`. That's 6 source columns. **Pick ONE as canonical and deprecate the rest.** Recommendation: make `source_attribution_final` the canonical one and document its exact computation.

---

#### BDA Hierarchy Columns

| Column | Source | Description |
|--------|--------|-------------|
| `ActivityOwnerEmail` | Computed (snapshot) | Lead's current owner email — 100% populated but changes on reassignment |
| `ActivityOwnerName` | Computed (snapshot) | Lead's current owner name — mostly empty (~1-4%), DO NOT USE |
| `UserID` | dbo.Users join | User UUID for the activity owner |
| `emailaddressug` | dbo.Users join | User email from Users table |
| `GroupName` | dbo.UserGroups join | Team/group name |
| `BDM` | dbo.BDA_Mapping join | Direct Manager name |
| `RBM` | dbo.BDA_Mapping join | Regional Business Manager |
| `AD` | dbo.BDA_Mapping join | Area Director |
| `BDA_DM` | dbo.BDA_Mapping join | BDA's DM (different join path) |
| `BDA_RBM` | dbo.BDA_Mapping join | BDA's RBM |
| `BDA_AD` | dbo.BDA_Mapping join | BDA's AD |
| `BDA_Category` | dbo.BDA_Mapping join | Monthly tier: Platinum/Gold/Silver/Bronze |

**SL equivalent:** Your `dbo.User` table has `role` (se/dm/rsm/ad/admin) and integer FK columns (`dm`, `rsm`, `ad`) pointing to `workforce_id`. Your fact table has `assigned_bda_id/name/tier/status`, `latest_bda_id/name/tier/status`, and `bda_id/name/tier/status`. This triple-column pattern is actually clearer than Crio's approach — keep it, but document which one to use for which analysis type.

---

### A2. Grain of fact.FinalTable

**One row per activity event per lead.**

Each row represents one activity (call, app fill, enrollment, session, stage change, etc.) for one `RelatedProspectId`. A lead with 15 activities in a month has 15 rows. Lead-level fields (mx_Working_Status, EmailAddress, ProspectStage, etc.) are replicated across all rows from a JOIN to dbo.Leads during the build.

Revenue (`sale_amt`) sits on the `Sales Booking` activity row ONLY. It is NOT replicated. So `SUM(CASE WHEN ActivityName='Sales Booking' THEN sale_amt END)` naturally avoids double-counting.

---

### A3. How fact.FinalTable Is Built

**Architecture: 4 prep views feeding into 1 stored procedure.**

```
LAYER 1 — RAW TABLES (from CRM sync)
───────────────────────────────────────
dbo.Activity          Raw activity log, UTC timestamps, mx_Custom_1..30
dbo.Leads             Lead master data (2.5M rows, full CRM)
dbo.Users             User/BDA master
dbo.UserGroups        User-to-group mapping
dbo.BDA_Mapping       Monthly BDA category + hierarchy
dbo.Daily_Spends      Marketing spend (separate, lags 3-4 weeks)

LAYER 2 — PREP VIEWS (cleaning + decoding)
───────────────────────────────────────
prep.vw_ActivityUnified
  - UTC → IST timezone conversion
  - mx_Custom_1..30 decoded into named columns PER activity type
  - Example: for AE 22 (Outbound Call), mx_Custom_7 → 'status' (call status)
  -          for AE 262 (App Fill), mx_Custom_5 → 'source' (UTM source)

prep.vw_LeadsClean
  - Grad year cleanup (handles "6/2025" → "2025")
  - Mobile number coalesce (multiple phone fields → single clean number)

prep.vw_UnifiedUsers
  - Users + UserGroups → user-to-team mapping

prep.vw_BDA_Mapping
  - Monthly BDA category + manager hierarchy

LAYER 3 — FACT TABLE (the stored procedure)
───────────────────────────────────────
fact.RefreshFinalTable (1,207 lines, ~50K characters)
  Step 1: JOIN all prep views
  Step 2: Compute flag columns (SameMonthApps, New_Lead_Segment, etc.)
  Step 3: Compute bucketing columns (Sales_Cycle_Days, OneToOne_Aging_Bucket, etc.)
  Step 4: Compute owner resolution (5-layer COALESCE for ActivityOwnerEmail)
  Step 5: Window functions for per-lead-per-month first/latest dates
  Step 6: TRUNCATE + INSERT into fact.FinalTable (last 6 months only)

LAYER 4 — PBI SEMANTIC MODEL
───────────────────────────────────────
fact.FinalTable → DirectLake → PBI semantic model → DAX measures → Report pages
```

**Refresh schedule:** Daily (automated Fabric pipeline).

**Time window:** Last 6 months only. For longer history, query `dbo.Activity` + `dbo.Leads` directly.

**SL rebuild recommendation:** Use a Fabric Notebook (not a stored procedure) — easier to debug cell-by-cell:
- Cell 0: `prep.unified_activity` (decode mx_custom per activity_code)
- Cell 1: `prep.unified_leads` (clean lead data)
- Cell 2: `prep.unified_users` (user hierarchy resolution)
- Cell 3: `fact.sl_final_table` (join + compute all flags)
- Cell 4: OPTIMIZE + freshness check

---

### A4. Revenue Handling

Revenue (`sale_amt`) exists ONLY on `Sales Booking` activity rows. Every report function uses:

```sql
SUM(CASE WHEN ActivityName='Sales Booking' THEN sale_amt END) AS Revenue
```

This avoids double-counting because each lead has one `Sales Booking` row per enrollment, and the CASE WHEN filter ensures only that row contributes.

**Caveat always included in output:** "Revenue is undercounted — sale_amt is not populated for all enrollments."

---

## B. Funnel Measures — Complete Definitions

### B1. Core Funnel Stages

Every count uses `COUNT(DISTINCT RelatedProspectId)` unless noted.

#### SMApp (Same Month Applications) — Top of Funnel
```sql
COUNT(DISTINCT CASE WHEN SameMonthApps='Applications'
  THEN RelatedProspectId END) AS SMApp
```
Uses the precomputed flag. "Applications" = lead had a FullFill or OtherLead app fill in this month.

**SL equivalent:** `Leads_New` uses `activity_type_category = 'Lead Capture'`. Different concept — SL counts lead captures while Crio counts app fills. Ensure SL's "Lead Capture" truly means an intentional form submission, not a system-generated import.

#### TAs (Trial Attendees)
```sql
COUNT(DISTINCT CASE WHEN ActivityName='Trial Workshop Attended'
  THEN RelatedProspectId END) AS TAs
```

**SL equivalent:** No trial tracking exists in SL's current DAX. Activity code 276 (Started a Course Trial) exists in the warehouse but isn't measured.

#### 1:1s (One-to-One Sessions)
```sql
COUNT(DISTINCT CASE WHEN ActivityName='Session_Attended'
  AND session_type IN (
    'SALES_DEMO_DE','SALES_DEMO_SE',
    'SALES_DEMO_DE_NO_RECORDING','SALES_DEMO_SE_NO_RECORDING',
    'SALES_DEMO_DE_NR','SALES_DEMO_SE_NR'
  ) THEN RelatedProspectId END) AS OneToOnes
```
Excludes ONBOARDING sessions (post-enrollment).

**SL equivalent:** `Demo_SE` uses `activity_type_category = 'SE Marked Demo Completed'`. Similar concept but different tracking mechanism.

#### QL (Qualified Leads)
```sql
-- QL = TAs + 1:1s (two separate DISTINCTCOUNT values ADDED together)
QL = [TAs_count] + [OneToOnes_count]
```

**CRITICAL:** A lead in BOTH TAs and 1:1s counts once in each. QL CAN be higher than unique qualified leads. This is by design.

**SL equivalent:** `Demos_New = Demo_SE + Demo_Webinar`. Same additive pattern.

#### PEs (Provisional Enrollments)
```sql
COUNT(DISTINCT CASE WHEN ActivityName='Payment Capture'
  AND type='Provisional Enrollment'
  THEN RelatedProspectId END) AS PEs
```

**SL equivalent:** No PE measure exists in SL's DAX. The `SalesData.PE` column contains email addresses (payment executives), not a PE stage flag.

#### Enrolls
```sql
COUNT(DISTINCT CASE WHEN ActivityName='Sales Booking'
  THEN RelatedProspectId END) AS Enrolls
```

**SL equivalent:** `Enrolls` uses `Is_Valid_Enroll = 1`. The critical question: what exactly makes an enrollment "valid"?

#### Revenue
```sql
SUM(CASE WHEN ActivityName='Sales Booking' THEN sale_amt END) AS Revenue
```

### B2. Calling Metrics

All computed at query time from fact table rows — NOT precomputed columns.

```sql
-- Dials (total call count, NOT unique leads)
COUNT(CASE WHEN ActivityName IN ('Call Attempt Activity','Outbound Call Activity')
  THEN 1 END) AS Dials

-- Dialled_Leads (unique leads called)
COUNT(DISTINCT CASE WHEN ActivityName IN ('Call Attempt Activity','Outbound Call Activity')
  THEN RelatedProspectId END) AS Dialled_Leads

-- Connected_Leads (unique leads reached)
COUNT(DISTINCT CASE WHEN
  (ActivityName='Outbound Call Activity' AND status='Answered')
  OR (ActivityName='Call Attempt Activity' AND nuture_call_Status='Connected')
  THEN RelatedProspectId END) AS Connected_Leads

-- Bookings (unique leads with demo session booked)
COUNT(DISTINCT CASE WHEN ActivityName='Call Attempt Activity'
  AND session_date IS NOT NULL
  THEN RelatedProspectId END) AS Bookings
```

**SL equivalent:** SL has `Leads Called` and `Calls Total` but NO connectivity metrics. SL's `dbo.Call` table has `call_status` (connected/dnp/disconnected) — this needs to be brought into the analysis either by joining at query time or enriching the fact table.

### B3. Additional Measures

```sql
-- MEs (Micro Experience Completions)
COUNT(DISTINCT CASE WHEN ActivityName='ME_Completion' THEN RelatedProspectId END)

-- TAs with 30+ min duration
COUNT(DISTINCT CASE WHEN ActivityName='Trial Workshop Attended'
  AND TrialWorkshop_Duration_Bucket IN ('30-60 min', '> 60 min')
  THEN RelatedProspectId END)

-- Leads Assigned (with valid BDA)
COUNT(DISTINCT CASE WHEN ActivityName='Lead Assignment Activity'
  AND se_email IS NOT NULL THEN RelatedProspectId END)

-- Active BDAs (those who actually made calls)
COUNT(DISTINCT CASE WHEN ActivityName='Outbound Call Activity' THEN owner_Id END)

-- IVR Leads
COUNT(DISTINCT CASE WHEN ActivityName='IVR Communication Sent'
  AND session_date IS NOT NULL THEN RelatedProspectId END)
```

### B4. All Derived Ratios

| Ratio | Formula | Description |
|-------|---------|-------------|
| A2Q% | QL / SMApp | App-to-Qualified rate |
| Q2E% | Enrolls / QL | Qualified-to-Enroll rate |
| A2E% | Enrolls / SMApp | App-to-Enroll rate (end-to-end) |
| TA2O% | 1:1s / TAs | Trial-to-1:1 conversion |
| O2E% | Enrolls / 1:1s | 1:1-to-Enroll conversion |
| TA2E% | Enrolls / TAs | Trial-to-Enroll |
| %Connectivity | Connected_Leads / Dialled_Leads | Call connectivity rate |
| %C2B | Bookings / Connected_Leads | Connected-to-Booking |
| A2B% | Bookings / SMApp | App-to-Booking |
| CC/lead | Connected_Calls / Connected_Leads | Calls per connected lead |
| TA>30min% | TAs_30PlusMin / TAs | Quality trial ratio |
| L2Q% | QL / Leads_Assigned | Lead-to-Qualification |
| SM-A2E% | SMEnroll / DISTINCTCOUNT(leads) | Same-month A2E |
| SMQ2E% | SMEnroll / SMQL | Same-month Q-to-E |
| LA-2-SQLTA% | SQL_TAs / Leads_Assigned | Assigned-to-SQL-trial |
| SQL-TAs/BDA | SQL_TAs / Active_BDAs | Per-BDA SQL trial productivity |
| 1:1/BDA | 1:1s / Active_BDAs | Per-BDA session productivity |
| 1:1 cov | 1:1_Converted / 1:1s | Pipeline conversion coverage |
| Call freq | Dials / SMApp | Call intensity per app |

**SL currently tracks:** L2D% (Leads→Demo), D2E% (Demo→Enroll), L2E% (Leads→Enroll), LA2E% (Assigned→Enroll), Call Frequency. Missing: connectivity %, booking %, pipeline aging ratios, per-BDA productivity ratios.

### B5. Product Type Bifurcation

Crio uses `Enroll_Program` (resolved from UUID to name) and `ProgramCategory_LeadLevel` for program-level breakdowns. But primary funnel ratios are computed at AGGREGATE level — not split by product.

SL's `sale_ind_pg` (PG / Individual / Combined Individual) is used in `D2E%` with `Enrolls PG` as numerator. Consider whether the business wants PG-only ratios or total Enrolls for core funnel ratios.

---

## C. Source Attribution

**Model:** First-touch at app fill.

**Canonical column:** `AppFillSourceFinal`

**Computation:**
```
1. If lead has App Fill (AE 262) with status IN ('FullFill','OtherLead')
   → Use `source` from that app fill row
2. Else if lead has IVR (AE 444)
   → 'IVR'
3. Else
   → 'No APP/IVR'
```

**14 distinct values:** Google, Facebook, Direct, Organic, LinkedIn, WhatsApp, Referral, IVR, and others.

**Campaign-level:** `SourceCampaign_AtAppFill` stores the campaign key from the app fill row, used for joining with `Daily_Spends` and `dim_campaign` for spend attribution.

**No multi-step refinement chain.** One column, computed once, used everywhere.

---

## D. Lead Segmentation

**Column:** `New_Lead_Segment`

| Value | Logic | SQL |
|-------|-------|-----|
| New Lead | Lead created this month | `LeadYM = ActivityYM` |
| Old Lead - App Fill | Existed before, came back with app fill | `LeadYM < ActivityYM AND FirstAppFillDate IS NOT NULL` |
| Old Lead - Others | Everyone else | `LeadYM < ActivityYM AND no app fill AND not reactivated` |

**V2/V3 variants** add reactivation classification:
- V3: If no "Outbound Call Activity" in last 30 days AND has a "Reactivated Lead Assignment Activity" → reactivated

**SL equivalent:** `lead_segment` has 'New Lead', 'Old Lead – Capture', 'Old – Others'. Structurally the same concept.

---

## E. BDA / SE Assignment & Owner Resolution

### Owner Resolution Rules

Different activity types require different BDA attribution logic. This is the hardest part of the data model.

| Activity Type | Best BDA Column | How Resolved | Accuracy |
|---|---|---|---|
| **Calls** (AE 22, 428) | `owner_Id` → JOIN `dbo.Users` on `UserID` | BDA who made the call | 100% |
| **Assignments** (AE 384) | `se_name` / `se_email` on the row | BDA assigned TO (not the system) | 100% |
| **Sales Booking** (AE 30) | `se_name` (UUID) → JOIN `dbo.Users` on `UserID` | Actual BDA who worked the lead (not the puncher — 22% are manager-punched) | 100% |
| **App Fill** (AE 262) | Cascading COALESCE (see below) | Stable, survives reassignment | 100% |
| **1:1 Sessions** (AE 417) | `ActivityOwnerEmail` | Snapshot (changes on reassignment) | 96% |
| **TAs** (AE 267) | `ActivityOwnerEmail` | Snapshot; 42.5% are MQL (no BDA) | 100% |
| **PEs** (AE 256) | `ActivityOwnerEmail` | Snapshot | 100% |

### App Fill Cascading Owner Resolution

```sql
COALESCE(
    -- 1. Last assignment se_email BEFORE app fill date
    pre_assign.se_email,
    -- 2. First assignment se_email AFTER app fill date
    post_assign.se_email,
    -- 3. Fallback to ActivityOwnerEmail snapshot
    f.ActivityOwnerEmail
)
```

### System Emails to Exclude

When computing BDA metrics, exclude these system accounts:
- `sales-admin@criodo.com`
- `delivery-lsq@criodo.com`
- `ai-call-agent@criodo.com`
- `category@criodo.com`
- Plus 15 system UUIDs in the `_SYSTEM_IDS_SQL` constant

### BDA Tier Classification

Source: `dbo.BDA_Mapping` (monthly, performance-based)

| Tier | Share | Specialization |
|------|-------|---------------|
| Platinum | ~20% | Best performers, highest CWP allocation |
| Gold | ~20% | Strong performers |
| Silver | ~20% | Intermediate |
| Bronze | ~40% | Lowest + OJT trainees |

Resets monthly based on previous month's enrollment performance. Joined into fact table as `BDA_Category`.

**SL equivalent:** `dbo.BDATierClassification` with tiers A/B/C/New. Simpler but same concept.

---

## F. Calling Metrics — Detailed

All calling metrics are computed **at query time** from fact table rows. No separate calls table needed — call activities are rows in the fact table with `ActivityName IN ('Outbound Call Activity', 'Call Attempt Activity')`.

**SL difference:** SL has a separate `dbo.Call` table with `call_status`. The fact table's `activity_type_category = "Call Activity"` is a flat bucket with no connectivity. Two options:
1. Join `dbo.Call` at query time (cleaner but slower)
2. Bring `call_status` into the fact table during the build (faster queries)

Recommendation: Option 2 — add `call_status` as a column in the fact table build.

---

## G. Reports & Query Tool

### G1. All 28 Pre-built Report Functions

Each function takes `(month, year)` and returns a list of dicts or a dict of lists.

| Function | Parameters | Returns |
|----------|-----------|---------|
| `report_full` | month, year | All reports combined |
| `report_funnel` | month, year | Single row: SMApp, TAs, 1:1s, QL, PEs, Enrolls, Revenue |
| `report_enrollments` | month, year | Single row: Enrollments, Revenue, Avg_Deal_Size |
| `report_daily` | month, year | Daily trend by day |
| `report_programs` | month, year | Enrollments by Program |
| `report_pipeline` | month, year | Pipeline by ProspectStage |
| `report_sessions` | month, year | Session counts by session_type |
| `report_sources` | month, year | Full funnel by source |
| `report_spend` | month, year | Marketing spend by channel |
| `report_mom` | year | Month-over-month for full year |
| `report_sales_reps` | month, year, top_n=15 | Top N BDAs by enrollments |
| `report_same_month` | month, year | Dict: by_source + by_working_status + by_grad_year |
| `report_daily_apps` | month, year | Dict: by_source + by_working_status + daily_total |
| `report_daily_compare` | month, year | Dict: current vs previous month cumulative |
| `report_enrollment_lag` | month, year | Cohort lag M+0 to M+5 by source |
| `report_sales_cycle` | month, year | Sales cycle bucket distribution |
| `report_trial_funnel` | month, year | Dict: overall + by_trial_type + by_profile + by_source |
| `report_pipeline_aging` | month, year | Dict: summary (aging buckets) + per_se |
| `report_calling_metrics` | month, year | BDA calling leaderboard |
| `report_de_performance` | month, year | DE demo counts per email |
| `report_provisional` | month, year | Dict: by_source + by_working_status PE counts |
| `report_inactive` | month, year | Inactive leads by source |
| `report_funnel_by_segment` | month, year | Dict: by_lead_segment + by_attend_category |
| `report_bda_funnel` | month, year | Full funnel per BDA (complex owner resolution) |
| `report_weekly_cohort` | months, year | Weekly cohort analysis |
| `report_masterclass_attribution` | start, end, amount | Masterclass GA+LSQ attribution |
| `report_lead_assignment_trend` | start, end | Lead assignment volume trend |
| `report_cwp_nwp_pool_split` | start, end | CWP vs NWP pool split |

### G2. Query Execution Pattern

```python
# Integer parameters — f-string with int() casting (safe)
def report_funnel(month, year, conn=None):
    sql = f"""
    SELECT
        COUNT(DISTINCT CASE WHEN SameMonthApps='Applications'
            THEN RelatedProspectId END) AS SMApp,
        ...
    FROM fact.FinalTable
    WHERE Year={int(year)} AND MonthNo={int(month)}
    """
    return run_query(sql, conn)

# String parameters — use parameterized queries
def run_parameterized_query(sql, params, conn=None):
    cursor.execute(sql, params)  # params as tuple, ? placeholders
```

**SL implementation:** Fork this pattern. Use `int()` casting for month/year. Use `run_parameterized_query()` for any string inputs.

### G3. Data Freshness Check

```python
def check_data_freshness(conn=None):
    sql = "SELECT MAX(Activity_date) AS latest FROM fact.FinalTable"
    result = run_query(sql, conn)
    # Returns None if < 2 days old
    # Returns warning string if > 2 days stale
    # Returns special warning if table empty
```

Called automatically by every report function. Warning prepended to results if stale.

### G4. Totals Row

**NOT in SQL.** Report functions return grouped data without totals. The CLAUDE.md validation checklist requires "Total row exists in every table you present" — the agent adds it when formatting the response.

---

## H. Workflows

15 workflow SOPs in `workflows/`:

| File | Trigger Patterns | What It Does |
|------|-----------------|--------------|
| `same_month_funnel.md` | "monthly numbers", "funnel", "A2Q%" | Full funnel + by source + by segment |
| `daily_runrate.md` | "today", "daily", "run rate" | Daily pacing vs previous month |
| `campaign_attribution.md` | "campaign", "CPE", "spend" | Spend + ROI by channel |
| `enrollment_lag.md` | "sales cycle", "cohort", "M+0" | Cohort enrollment lag analysis |
| `trial_analysis.md` | "trial", "TA2O%", "session duration" | Trial funnel deep dive |
| `pipeline_aging.md` | "pipeline", "aging", "stale" | Open 1:1 pipeline by aging bucket |
| `team_performance.md` | "BDA leaderboard", "top performers" | Per-BDA calling + conversion metrics |
| `provisional_enrollment.md` | "PE", "provisional", "payment" | PE tracking by source/status |
| `inactive_leads.md` | "inactive", "dormant" | App-filled leads with no progress |
| `ga_lsq_attribution.md` | "masterclass", "real source" | GA + CRM attribution reconciliation |
| `lead_assignment.md` | "assign leads", "morning leads" | Daily BDA assignment pipeline |
| `analyze_growth_report.md` | "growth report", "monthly report" | Full monthly report generation |
| `number_mismatch_debug.md` | "numbers don't match" | PBI vs SQL discrepancy investigation |
| `pbi_page_spec.md` | "dashboard", "PBI page" | PBI page blueprint design |
| `adhoc_question.md` | (last resort) | Ad-hoc data questions |

Each workflow file contains step-by-step instructions: which report functions to call, what to validate, how to present results, and what caveats to include.

---

## I. Data Exclusions

### In the Fact Table Build

- **Time window:** Last 6 months only
- **System flag:** `Is_System_Activity = 1` for 15 known system UUIDs
- **Business Date:** Activities before 10:30 AM → previous day

### At Query Time

- **System emails excluded:** `sales-admin@criodo.com`, `delivery-lsq@criodo.com`, `ai-call-agent@criodo.com`, `category@criodo.com`
- **System UUIDs excluded:** 15 UUIDs in `_SYSTEM_IDS_SQL` constant (for BDA analysis only)

### Lead Assignment Eligibility (separate from fact table)

- Indian mobile: contains +91
- Not internal: email NOT containing `criodo.com`, `criodo.co.in`, `crio-users.in`, `skill-lync.com`
- Not in excluded stages: Irrelevant, Closed Won, Placed
- Not school-level education

**SL action needed:** Identify SL's system accounts and internal email domains for exclusion.

---

## J. Operational Details

### J1. File Structure (for SL to replicate)

```
SL Agent/                              # New repo for Skill-Lync
├── CLAUDE.md                          # SL-specific operating instructions
├── .env                               # WAREHOUSE_DB=Skill-lync Warehouse
├── requirements.txt
├── memory/
│   ├── MEMORY.md                      # Auto-memory index
│   ├── shared_rules.md                # SL-specific SQL mistakes
│   ├── shared_measures.md             # SL metric definitions (DAX + SQL)
│   ├── shared_business_context.md     # SL products, funnel, teams
│   ├── shared_architecture.md         # SL pipeline, schema, columns
│   ├── error_log.md                   # Persistent error + fix log
│   └── local_preferences.md.example
├── workflows/
│   ├── same_month_funnel.md           # SL funnel: Leads → Demo → Enroll
│   ├── daily_runrate.md
│   ├── team_performance.md
│   ├── ... (SL-specific workflows)
│   └── adhoc_question.md
├── tools/
│   ├── query_warehouse.py             # SL report functions + run_query
│   ├── validate_result.py             # SL validation checks
│   ├── daily_sprint.py                # SL health check
│   ├── send_email.py                  # Email reports
│   └── push_memory.py
├── tests/
│   └── test_reports.py
├── data/
│   ├── golden_baseline.json
│   └── sprint_log.md
└── docs/
    ├── ARCHITECTURE.md
    └── business_logic.md
```

### J2. Validation Checklist (adapt for SL)

Before showing ANY number to the user:

- [ ] Enrollments > 0 for any recent month
- [ ] Revenue > 0 if enrollments > 0
- [ ] Ratios between 0% and 100% (L2D%, D2E%, L2E%)
- [ ] Demos_New >= Demo_SE and Demos_New >= Demo_Webinar (additive sum check)
- [ ] Total row exists in every table
- [ ] Data freshness warning shown if stale
- [ ] sale_value caveat noted if applicable
- [ ] Schema prefix on every table reference
- [ ] Specify which fact table is being queried (CRITICAL — SL has 3)

### J3. Golden Baseline Format

```json
{
  "generated": "2026-04-10T13:01:07",
  "month": 4,
  "year": 2026,
  "enrolls": 78,
  "revenue": 8580941.0,
  "prev_enrolls": 215,
  "prev_revenue": 23230824.0,
  "total_rows": 19553288,
  "unique_leads": 835481,
  "max_date": "2026-04-10 10:50:37"
}
```

Sprint compares current values against baseline. Alerts on >30% swings.

### J4. Error Log Format

```markdown
### YYYY-MM-DD — [Short description]
- **Query:** (what was attempted)
- **Error:** (the error message)
- **Fix:** (what resolved it)
- **Root cause:** (why it happened)
- **New rule?** (Y/N — did this lead to a shared_rules.md update?)
```

### J5. .env Structure

```env
POWERBI_TENANT_ID=<same tenant>
POWERBI_CLIENT_ID=<same client>
POWERBI_CLIENT_SECRET=<same secret>

SQL_ENDPOINT=twwfdlzo7soexar7f7tzk7wuo4-k6jathn5r3uehhmbl5juoq54da.datawarehouse.fabric.microsoft.com
WAREHOUSE_DB=Skill-lync Warehouse

GMAIL_ADDRESS=<SL report sender email>
GMAIL_APP_PASSWORD=<app password>
```

Both databases are on the SAME Fabric server. Same service principal works.

### J6. Data Freshness Warning Format

Standard format in agent responses:
```
Data may be stale -- last refresh was 2026-04-08, which is 2 days ago.
Numbers may not reflect the last 2 days.
```

### J7. "Old Lead" Enrollment Attribution

When a lead enrolls but had no lead capture in the current month:
- They fall into `lead_segment = 'Old – Others'`
- They still count in Enrolls (the enrollment filter doesn't care about segment)
- The enrollment counts in the month the payment/booking happened
- `Enroll_Month_Bucket_Capped` tracks the lag from first lead capture to enrollment

No special "credit" logic — the enrollment counts where it happened.

### J8. Calendar / Date Dimension

Crio has BOTH:
- `dim.Calendar` table in the warehouse (for PBI time intelligence / slicers)
- Computed columns on fact table: Year, MonthNo, Month, Day, WeekOfMonth, etc.

SQL queries use fact table columns directly. `dim.Calendar` is PBI-only.

SL should create a `dim.Calendar` for PBI but can use computed columns for SQL queries.

---

## Appendix: Crio's 19 Documented SQL Mistakes

These are the mistakes that produced wrong numbers. SL should learn from them proactively.

| # | Mistake | Correct Approach |
|---|---------|-----------------|
| 1 | Used `Reactivated_Lead = 1` for new/old segmentation | Use `New_Lead_Segment` column |
| 2 | Used `ProspectStage` for historical analysis | Use `lead_stage_change` with window functions |
| 3 | Combined multi-flag columns in single WHERE | Use CTE pattern (get lead IDs first, then JOIN) |
| 4 | Missing schema prefix (`FinalTable` instead of `fact.FinalTable`) | Always use schema prefix |
| 5 | Wrong values for SameMonthEnrolls ('Yes' instead of 'Enrolls') | Check actual column values |
| 6 | Wrong values for SameMonthApps ('Yes' instead of 'Applications') | Check actual column values |
| 7 | DAX API returns 401 | Always use ODBC SQL directly |
| 8 | Calling SOP: assumed >3 calls = good | 3 = compliant, >3 = over-calling |
| 9 | Used `owner_Id` on assignment rows for BDA name | Use `se_name`/`se_email` (the assigned BDA) |
| 10 | Used `ActivityOwnerName` for BDA identification | Mostly empty — use `ActivityOwnerEmail` |
| 11 | Used SameMonth flags for main measures | Use ActivityName-based definitions |
| 12 | Used `Current_Owner` for historical analysis | It's a snapshot — changes on reassignment |
| 13 | Grad year parsing: `LEFT(mx_Grad_Year, 4)` fails on "6/2025" | Add `RIGHT(mx_Grad_Year, 4)` for M/YYYY format |
| 14 | Write operations without user permission | Never execute INSERT/UPDATE/DELETE without approval |
| 15 | FILTER inside CALCULATE doesn't inherit ALL() context | Use CALCULATETABLE instead |
| 16 | TREATAS doesn't propagate date context | Only maps specified columns — dates don't flow |
| 17 | `se_name` on Sales Booking is a UUID but IS the actual BDA | JOIN dbo.Users to resolve |
| 18 | `ActivityOwnerEmail` is a snapshot, not point-in-time | Acceptable for current month; drifts historically |
| 19 | `ActivityOwnerName` mostly empty | Use `ActivityOwnerEmail` instead |

**SL-specific risks to watch for:**
- SL's `dbo.Activity_extension` has 65 mx_custom columns with NO documented mapping — this is Mistake 0 waiting to happen
- SL has 3 fact tables — querying the wrong one is an instant error
- SL's `SalesData` (manual, 1,010 rows) may contradict fact table enrollment counts — reconcile immediately
- SL's `Is_Valid_Enroll` is undocumented — could be SL's Mistake 11 equivalent

---

*Generated 2026-04-10. Source: live Crio Analytics Agent (PBI Agent repo), verified against CrioWarehouse and all memory files.*
