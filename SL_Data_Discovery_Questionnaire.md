# Skill-Lync — Data Discovery Questionnaire (V2)

**Purpose:** Build a structured analytics database and AI agent for Skill-Lync, matching Crio's analytics maturity.

**Context:** This questionnaire is based on a thorough exploration of the `Skill-lync Warehouse` on Fabric. Every question references actual tables, columns, and data values found in the warehouse. Nothing is hypothetical.

**Explored:**
- 21 tables + 17 views across `dbo`, `prep`, `fact` schemas
- 130+ activity types in `dbo.ActivityType`
- 132 columns in `fact.Final_Table` (the active fact table per DAX)
- 13 DAX measures from `Skill-Lync-Master-Report` semantic model
- Row counts: Leads 29.5M, ActivityBase 7.5M, Activity_extension 110M, fact.Final_Table 8.5M

---

## Section 1 — Fact Table Disambiguation

Three fact tables exist in the warehouse. The DAX measures reference `Final_Table`. We need to settle this definitively.

| Table | Rows | Schema |
|-------|------|--------|
| `fact.FinalTable` | 5,946,538 | 92 columns (matches `fact.FinalTable` in DAX of Skill-Lync-Master-Report's older version?) |
| `fact.Final_Table` | 8,520,491 | 132 columns (DAX measures reference THIS table) |
| `fact.Final_Table_New` | 6,750,648 | Unknown — possibly a WIP replacement |

**Q1.** Is `fact.Final_Table` (8.5M rows, 132 columns) the canonical, production fact table that the PBI report currently uses?

**Q2.** What is the purpose of the other two?
- `fact.FinalTable` (5.9M) — older version? Different time window? Can it be dropped?
- `fact.Final_Table_New` (6.8M) — work-in-progress replacement? Testing? Can it be dropped?

**Q3.** Is there a stored procedure or notebook that refreshes `fact.Final_Table`? If yes — where is it (Fabric notebook name or stored procedure name), and how often does it run?

**Q4.** `fact.fact_lead_activity` is a view in the fact schema. Is this an older/alternative pipeline, or does it feed into one of the fact tables?

---

## Section 2 — Funnel Stage Definitions (Locking the Numbers)

The DAX measures define SL's funnel as: **Leads_New → Leads Assigned → Demos Scheduled → Demo_SE / Demo_Webinar → Enrolls**. Each stage uses the `activity_type_category` column. We need to confirm the mapping from raw activity codes to these categories, and identify what's missing.

### 2A — Activity Type Category Mapping

The fact table has 10 distinct `activity_type_category` values. The warehouse has 130+ raw `activity_code` values in `dbo.ActivityType`.

**Q5.** Below is the mapping we ASSUME based on naming. Confirm or correct each row, and fill in the raw activity codes that map to each category:

| activity_type_category | Assumed raw activity_codes | Confirm? (Y/N) | Corrections / Notes |
|---|---|---|---|
| Lead Capture | 23 (Lead Capture), 209 (Facebook Lead Ads), 279 (Lead Ads), 292 (LinkedIn), 293 (Quora), 310 (Google), 322 (Career360), 414 (Affiliate), 513 (Grow Lead Capture) | | |
| Call Activity | 22 (Outbound), 21 (Inbound), 206 (Had a phone call), 207/214-218 (DNP 1-5), 241 (Busy), 242 (Not Reachable), 506 (Kaleyra Outbound), 507 (Manual Outbound), 777 (Priority Call), 2500-2502 (DNP/DNP System/DNP Within Limit) | | |
| Demo Scheduled | 259 (Demo Scheduled), 315 (Demo Booked), 384 (Spot Demo Booked), 290 (Schedule Demo), 262 (House Demo Scheduled) | | |
| SE Marked Demo Schedule | ??? (How does this differ from "Demo Scheduled"? Is this a BDA booking that an SE confirms?) | | |
| SE Marked Demo Completed | 317 (Demo Conducted)? 213 (Attended Demo Session)? | | |
| Demo Completed - Webinars | 203 (View Demo)? 509 (Joined Interactive Session)? Which webinar/session codes? | | |
| Lead Assignment Activity | Derived from `dbo.lead_assignment_history`? Or activity_code 4000 (Owner Change)? | | |
| Payment Activity | 98 (Payment), 263 (Initiated Direct Payment), 264 (Completed Direct Payment), 388 (Portal Payment Received) | | |
| Page Visit | 2 (Website Page Visited) | | |
| Other / Unknown | Everything else | | |

**Q6.** There are activity codes that look important but don't appear in any category:
- **276 (Started a Course Trial)** — Is this tracked? Should it be a funnel stage?
- **316 (Demo Confirmed)** — What does "confirmed" mean operationally? Lead confirmed attendance?
- **318 (Demo Rescheduled)** / **319 (Demo Cancelled)** — Are these tracked for conversion analysis?
- **393-396 (Tech Demo lifecycle: Scheduled/Rescheduled/Conducted/Cancelled)** — How does "Tech Demo" differ from regular Demo? Is it the DE equivalent?
- **326 (Sales Confirmation Call Done)** — Is this a post-enrollment verification? Should it be tracked?
- **336-338 (Reactivated 1/2/3)** — What do the numbers mean? Reactivation attempts?

**Q7.** There are garbage activity codes in the system: 295 (`szcfds`), 298 (`zxc`), 433 (`hkj`), 434 (`sdf`), 436 (`hgvugvhg hj`). Can these be confirmed as test/junk entries and excluded from all analysis?

### 2B — Leads_New (Application Equivalent)

**Q8.** The DAX measure `Leads_New` counts distinct leads with `activity_type_category = "Lead Capture"`. In Crio, the equivalent is "Apps" (Application Filled — a deliberate form submission by the lead).

- Does "Lead Capture" in SL mean the same thing — a lead intentionally submitted a form?
- Or does it include system-generated captures (imports, scraped leads, bulk uploads)?
- Are there lead quality distinctions like Crio's FullFill vs HalfFill vs OtherLead?
- Activity code 23 (Lead Capture) has `is_done_by_system = true` — does this mean ALL lead captures are system-generated? If so, which activity codes represent a human-initiated application?

**Q9.** `dbo.LeadCaptureMessage` (10.6M rows) contains JSON messages like:
```json
{"email": "...", "phone": "...", "source": "crm", "firstName": "...", "domain": null, ...}
```
- Is the `source` field inside this JSON the ground truth for lead source attribution?
- What are the possible values of `source` in this JSON? (We saw "crm" — are there "website", "facebook", etc.?)
- There are 10+ prep views parsing this JSON (`vw_LeadCaptureMessage_*`). Which one is the canonical, current version used by the fact table?

### 2C — Demo / 1:1 Sessions

**Q10.** The DAX separates demos into three measures:
- `Demo_SE` → "SE Marked Demo Completed"
- `Demo_Webinar` → "Demo Completed - Webinars"
- `Demos_New` = Demo_SE + Demo_Webinar

Questions:
- What is an "SE Marked Demo"? Is this a 1:1 session where the SE (sales executive) manually marks it as conducted in the CRM?
- What is a "Webinar Demo"? Is it a group session (like Crio's Trial Workshop) vs. a 1:1?
- Can a lead have BOTH a Demo_SE and a Demo_Webinar in the same month? If so, do they count twice in Demos_New (same as Crio's QL = TAs + 1:1s)?
- The `dbo.Call` table has 357K rows with `call_status`. Are demos tracked there too, or only in ActivityBase?

**Q11.** The demo lifecycle has multiple stages:
```
Demo Scheduled → Demo Booked → Demo Confirmed → Demo Conducted → (or) Demo Rescheduled / Cancelled
```
Plus a parallel "Tech Demo" lifecycle (393-396). Questions:
- What is the difference between "Demo Scheduled" (259) and "Demo Booked" (315)?
- What is the difference between a regular Demo and a Tech Demo? Is Tech Demo = DE (Demo Engineer) session?
- Is "Spot Demo Booked" (384) an immediate/walk-in demo vs. a scheduled one?
- For the demo conversion funnel (Scheduled → Conducted), which codes mark "actually attended"?

### 2D — Enrollment

**Q12.** Enrollment data exists in TWO places:
1. `fact.Final_Table` — columns: `Is_Valid_Enroll`, `sale_value`, `sale_program`, `sale_ind_pg`, `enroll_date`
2. `dbo.SalesData` — 1,010 rows with: `Name`, `Email`, `Program`, `Sale Value`, `Type of Purchase`, `SE Name/Email`, `Date`, `PE`

Questions:
- Which is the source of truth for enrollment count?
- How does `Is_Valid_Enroll` get computed? What makes an enrollment "valid" vs "invalid"? Is it based on activity_type_category = "Payment Activity"? Or matched against SalesData?
- Is `dbo.SalesData` manually maintained (e.g., someone enters rows in a spreadsheet)? How often is it updated?
- The `sale_value` column in the fact table — is it reliably populated for all enrollments? (In Crio, `sale_amt` is undercounted)

**Q13.** The `sale_ind_pg` column has 4 values: `PG`, `Individual Course`, `Combined Individual`, empty string.
- What is a "Combined Individual"? Multiple individual courses sold as a bundle?
- The DAX ratio `D2E%` uses `Enrolls PG` (not total Enrolls) as the numerator. Is the business intent to track PG conversions only? Or should total Enrolls be the primary metric?

**Q14.** The `SalesData.Type` column uses month-based naming: "April - Individual", "August 2025 - Individual", "AUG - Upskilling", etc.
- Is this the enrollment cohort month?
- "Upskilling" vs "Individual" — what's the business difference?
- The inconsistent naming (e.g., "Full Payment" vs "Full payment" in `Type of Purchase`) — is this a known issue?

**Q15.** The `SalesData.PE` column contains email addresses (e.g., `sakthi.maheswari@skill-lync.com`). Is this the "Payment Executive" who processed the enrollment? And does SL have a "Provisional Enrollment" stage like Crio (payment intent captured but not yet collected)?

### 2E — Calling Metrics

**Q16.** The DAX only tracks `Leads Called`, `Calls Total`, and `Call Frequency`. Crio tracks 7 calling metrics: Dials, Dialled_Leads, Connected_leads, %Connectivity, Bookings, %C2B, CC/lead.

SL has the data to support these. The `dbo.Call` table (357K rows) has:
- `call_status`: connected, disconnected, dnp, dnpWithinLimit
- `direction`: inbound/outbound
- `is_manual_call_done`: manual vs auto-dialer

Questions:
- Should "Connected" = `call_status = 'connected'`? Or is there a secondary definition?
- Should DNP (Did Not Pick) include both `dnp` AND `dnpWithinLimit`? What does "Within Limit" mean — DNP within the daily retry limit?
- Does the `dbo.Call` table contain ALL calls, or only Kaleyra/platform calls? Are manual calls (activity_code 507) also in this table?
- Is there a call-to-demo booking linkage? (i.e., after a connected call, the BDA schedules a demo — can we trace this?)

**Q17.** The fact table has no call connectivity columns. The `activity_type_category = "Call Activity"` is a flat bucket. To build Crio-level calling metrics, we'd need to join `dbo.Call` or decode `mx_custom39` (the only mx_custom in the fact table).
- What does `mx_custom39` represent in the context of the fact table?
- Should call connectivity be added to the fact table pipeline, or computed at query time?

---

## Section 3 — Attribution & Source Tracking

**Q18.** The fact table has FOUR source-related columns:
- `Lead_Source` — 14 clean values (Google Search Ads, Facebook Lead Ads, Organic, Referral, etc.)
- `Source_Bucket` / `Source_Bucket_Final` — unknown bucketing logic
- `source_attribution_final` — unknown
- `first_lead_capture_source_of_month` / `last_lead_capture_source` — first/last capture in month
- `lc_source` / `lc_sourceCampaign` / `lc_sourceMedium` — from LeadCaptureMessage

Questions:
- Which column is the canonical "lead source" used for reporting? Is it `Lead_Source`?
- What is the difference between `Source_Bucket` and `Source_Bucket_Final`? Is one a fallback?
- What does `source_attribution_final` contain? Is it the settled, definitive source after all fallback logic?
- Does SL use first-touch or last-touch attribution? Or a hybrid?

**Q19.** How is marketing spend data tracked?
- Is there a `Daily_Spends` equivalent table in the warehouse? (We didn't find one)
- Is spend tracked via Windsor.ai, Google Sheets, or another system?
- Can we compute CPL (Cost Per Lead), CPD (Cost Per Demo), CPE (Cost Per Enrollment) today?

---

## Section 4 — Team Structure & Assignment

**Q20.** The `dbo.User` table (6,012 rows) has a clear hierarchy:
- `role`: se, dm, rsm, ad, admin
- `dm` (int), `rsm` (int), `ad` (int) — these are foreign keys to other User rows

Questions:
- Confirm the hierarchy: **SE** (Sales Executive / BDA) → **DM** (Direct Manager) → **RSM** (Regional Sales Manager) → **AD** (Area Director)?
- The `dm`/`rsm`/`ad` columns are integers, but the User `id` is varchar. How do they map? Is `dm` referencing `workforce_id` (which IS int)?
- Are there other roles beyond sales? (e.g., Demo Engineers, Quality Auditors, Collection team)
- The `region` column — what regions exist and how are they used?
- `platform` column in User table — what values does it take?

**Q21.** The `dbo.BDATierClassification` table (42 rows) has:
- Tiers: A, B, C, New
- Statuses: Active, Inactive

Questions:
- What determines a BDA's tier? Performance-based? Tenure-based?
- Is tier classification monthly (like Crio's `BDA_Mapping`) or relatively static?
- The fact table has `assigned_bda_tier` AND `latest_bda_tier` AND `bda_tier` — three different tier columns. Confirm:
  - `assigned_bda_tier` = tier at the time of assignment (point-in-time)?
  - `latest_bda_tier` = current tier (snapshot)?
  - `bda_tier` = tier of the BDA who performed this specific activity?

**Q22.** The `dbo.lead_assignment_history` table (973K rows) has sophisticated lead scoring:
- `priority_score1`, `priority_score2`, `persona_score2` (decimals)
- `source_score`, `lead_type_score`, `current_week_activity_score` (integers)
- `assignment_type`: "New" or "Others"
- `prospect_rank`, `selected_user_rank`
- `team_domain`, `prospect_star_rank`

Questions:
- Is lead assignment automated (rule-based scoring) or manual?
- What determines "New" vs "Others" assignment type?
- Is there a daily lead assignment SOP like Crio's 10:30 AM process?
- What does `team_domain` represent? (We also see it in LeadsExtension and the fact table)
- What do the star ranks mean (prospect_star_rank, selected_user_rank)?

---

## Section 5 — Snapshot vs. Point-in-Time (Critical for Accuracy)

This is the #1 source of wrong numbers in Crio. SL's fact table shows awareness of this problem (assigned_bda vs latest_bda) but we need to confirm the full picture.

**Q23.** Confirm which columns in `fact.Final_Table` are **snapshots** (reflect current state, change on update) vs. **point-in-time** (frozen at the time of activity):

| Column | Assumed Type | Confirm? |
|---|---|---|
| `prospect_stage` | SNAPSHOT (from Leads table, changes) | |
| `lead_owner_id` | SNAPSHOT (current owner) | |
| `assigned_bda_id/name/tier/status` | POINT-IN-TIME (at assignment) | |
| `latest_bda_id/name/tier/status` | SNAPSHOT (current BDA) | |
| `bda_id/name/tier/status` | ??? (what is this — activity-level?) | |
| `activity_owner_name` | ??? (owner at time of activity, or current?) | |
| `mx_domain` / `mx_department` | SNAPSHOT (from LeadsExtension) | |
| `is_customer` | SNAPSHOT (current state) | |

**Q24.** `dbo.ProspectStageChange` (155K rows) tracks stage transitions with `old_value` → `new_value`. But no DAX measures use it. Questions:
- Is this table reliably populated for ALL stage changes?
- Should stage change analysis (e.g., "how many leads moved from Discovery to Demo this month?") use this table or the fact table?
- The `purchase_id` and `lead_capture_message_id` columns — what do these reference?

---

## Section 6 — Data Quality & Known Issues

**Q25.** The `dbo.Leads` table has 29.5M rows — 12x Crio's lead volume. Questions:
- Is there significant duplication? (same person, multiple lead records)
- What percentage of leads are Indian? (Crio filters by +91)
- Are there test/internal leads that should be excluded? (e.g., @skill-lync.com emails)
- The `moved_from_lsq` flag — does this mean leads migrated from LeadSquared? How many?

**Q26.** The `dbo.Activity_extension` table has 110M rows with 65 `mx_custom` columns. The fact table only uses `mx_custom39`. Questions:
- What does `mx_custom39` represent?
- Is there a field-mapping document (like Crio's mx_Custom mapping) that defines what each mx_custom column means per activity type?
- Are the other 64 mx_custom columns needed for analytics, or are they CRM-internal?

**Q27.** Program naming in `dbo.SalesData` is highly inconsistent. Examples of the SAME program with different names:
- "PG IN CAD", "PG IN CAD - WO CS", "PG IN CAD WO CS", "PG IN CAD - CAREER SERVICES", "Post Graduate Program in CAD"
- "Automotive sheet metal design using CATIA V5", "Automotive Sheet Metal Design using CATIA V5", "Automotive Sheet metal Design using CATIA V5"
- "Introduction to Model Based Development using MATLAB and Simulink" appears in 5+ casing/punctuation variants

Questions:
- Is there a canonical program list / product master? How many distinct programs does SL actually sell?
- The fact table has `sale_program` and `Program_Interested` — are these cleaned/normalized, or do they carry the same inconsistencies?
- What is the `Domain_group` column? Is this the top-level program classification (e.g., CAD, CAE, CFD, EV, Embedded, Civil)?

**Q28.** `mx_year_of_passing` in LeadsExtension — what format is it in? Examples: "2022", "2023", or does it have mixed formats like Crio's "6/2025" problem?

**Q29.** Timestamps — what timezone are `created_at` / `activity_date` stored in? UTC or IST? Is there a Business Date concept (activities before a certain time count for the previous day)?

---

## Section 7 — Operational Processes

**Q30.** Does SL have a daily calling SOP like Crio's? Specifically:
- Is there a morning lead assignment process?
- Is there a calling start time (Crio uses 10:30 AM IST)?
- Are there calling sprints / daily quotas?
- Is there a "Business Date" rule where early-morning activities count for the previous day?

**Q31.** What is the demo scheduling workflow?
```
Lead captured → Assigned to BDA → BDA calls → Call connected → Demo scheduled → Demo conducted → Enrollment
```
- Is this accurate?
- Who schedules the demo — the BDA during the call, or the lead themselves (self-booking)?
- Who conducts the demo — the same BDA (SE), or a separate Demo Engineer?
- Activity code 367 "Directly booked a demo from Schedule A Demo Page" — how common is self-booking?

**Q32.** What is the enrollment workflow?
- Does the lead pay online (activity 264 "Completed Direct Payment")?
- Or does the SE collect payment (via link, UPI, bank transfer)?
- Is there a "Provisional Enrollment" stage (intent captured, payment pending)?
- What role does the PE (from SalesData) play — are they a separate "Payment Executive" team?
- Is enrollment confirmed only when payment clears, or at booking time?

**Q33.** Quality auditing — several activity codes relate to call auditing:
- 320 (Manager Call Audit Done)
- 340 (Audit done by quality team)
- 401 (QA Call Audit)
- 429 (DM Call Audit Done)
- 430 (RSM Call Audit Done)
- LeadsExtension has 30+ `mx_*` audit checklist fields (e.g., `mx_was_the_eligibility_checked`, `mx_did_the_se_pitch_the_pricing`)

Is call quality audit a formal process? Should audit scores/results be tracked in analytics?

---

## Section 8 — What Reports Exist Today & Trust Level

**Q34.** The `Skill-Lync-Master-Report` PBI report uses these 13 DAX measures. What pages/tabs does the report have?

| Page/Tab Name | What it shows | Trusted? (Y/N/Partially) | Known issues |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**Q35.** Are there other SL reports in this workspace or elsewhere? The workspace also contains:
- `SKILL LYNK` dataset (separate from `Skill-Lync-Master-Report`) — what is this?
- The quarterly "Master report-New" datasets (Oct-Dec 24, Jan-Mar 25, etc.) — are these historical SL reports or Crio-only?

**Q36.** Which numbers do people currently argue about? Examples:
- "Marketing says X leads but sales says Y"
- "PBI enrollment count doesn't match finance"
- "Demo conducted count doesn't match what the team reports manually"

List specific disagreements:
1. ___
2. ___
3. ___

---

## Section 9 — Missing Structure (What Crio Has That SL Needs)

Based on the warehouse exploration, these are the structural gaps. Confirm which ones should be prioritized.

**Q37.** Rate each gap as **HIGH** (needed immediately), **MEDIUM** (needed but not urgent), or **LOW** (nice to have):

| Gap | Description | Priority (H/M/L) |
|---|---|---|
| Connected call metrics | No DAX measure for call connectivity. Call table has `call_status` data. | |
| Call-to-booking conversion | Can't trace: connected call → demo scheduled → demo conducted | |
| Trial/workshop tracking | Activity code 276 exists but isn't in any measure | |
| PE (Provisional Enrollment) stage | SalesData has PE column but no analytics pipeline | |
| Program name normalization | 200+ free-text variants need mapping to canonical program list | |
| Daily run rate / pacing | No daily tracking to answer "are we on track this month?" | |
| Month-over-month trend | No MoM comparison in current DAX | |
| BDA leaderboard | No per-BDA performance measures (calls, demos, enrolls per BDA) | |
| Stage change analysis | ProspectStageChange table unused — no funnel flow tracking | |
| Marketing spend / ROI | No spend table — can't compute CPL, CPD, CPE | |
| Enrollment lag / sales cycle | Data exists (lead_created_on vs enroll_date) but no measure | |
| Calendar / date dimension | No `dim.Calendar` equivalent for time intelligence | |

**Q38.** Beyond analytics, should the SL agent also handle:
- [ ] Daily lead assignment (like Crio's `lead_assignment.py`)
- [ ] Email reports (like Crio's `send_email.py`)
- [ ] GA4 integration (traffic / campaign analysis)
- [ ] Data validation / health checks (like Crio's `daily_sprint.py`)
- [ ] Other: ___

---

## Next Steps After This Questionnaire

Once answered, the build sequence is:

1. **Fact table stabilization** — Confirm `fact.Final_Table` as canonical, drop the others, document the refresh pipeline
2. **Measure dictionary** — Lock every metric definition (DAX + SQL parity), signed off by stakeholders
3. **Gap closure** — Add missing computed columns (call connectivity, Business_Date, PE flag, program normalization)
4. **Agent scaffolding** — Build SL Agent structure: `CLAUDE.md`, `memory/`, `workflows/`, `tools/`
5. **Tool layer** — Fork `query_warehouse.py` pointed at `Skill-lync Warehouse`, build pre-built report functions
6. **Validation** — Cross-check agent output against existing PBI reports, resolve discrepancies
7. **Workflow SOPs** — Write step-by-step workflows for each report type

---

*Generated from live exploration of `Skill-lync Warehouse` on Fabric (2026-04-10). All table names, column names, row counts, and data values are verified against the actual warehouse.*
