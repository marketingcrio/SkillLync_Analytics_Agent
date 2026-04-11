# Shared Business Context — Skill-Lync

> **Last updated:** 2026-04-10. Answers from user/data owner interview.

---

## Company

Skill-Lync is an upskilling company. Sister company to Crio. Same Fabric tenant + service principal, different warehouse.

## Products / Programs

Two product categories:
- **PG (Post Graduate Programs)** — higher ticket (₹65k–₹1.2L), sold via tiers:
  - Ultra (premium), Pro (mid), Basic (entry), Upskilling, Student (discounted)
  - Top sellers: PG IN CAD (173 enrolls), PG IN EV (24), PG IN CFD (16), PG IN CAE (16)
- **Individual Courses** — lower ticket (₹5k–₹50k), standalone courses
  - E.g., "Introduction to GUI based CFD", "Python for mechanical engineers"
- **Combined Individual** — bundle of multiple individual courses (34 enrolls)

`sale_ind_pg` in fact table: 'PG' / 'Individual Course' / 'Combined Individual'.

Program naming is inconsistent (e.g., "PG IN CAD" vs "PG CAD" both exist). No canonical program master — user said to ignore normalization for now.

## Pricing / Payment

- **Payment methods** (from SalesDataSumit):
  - Full Payment (most common, ~53%)
  - Subscription/EMI (~30%)
  - Loan (~16%)
  - Split Payment, One-shot (rare)
- **Enrollment is confirmed ONLY when payment is received** — booking = payment event. No "provisional enrollment" stage.
- `dbo.SkillLyncSalesData` is the source of truth for sales. **Manually maintained** (spreadsheet upload). 999 rows total, Feb 2025 – Apr 2026.

## Funnel

Skill-Lync uses a **3-stage funnel with 2 demo tracks**:

```
Lead Capture ──► Webinar Demo Scheduled ──► Webinar Demo Completed ──► Enroll (Valid)
             ──► Tech Demo Scheduled    ──► Tech Demo Conducted    ──►
```

- **Lead Capture:** 28 activity codes (form fills, downloads, pop-ups, etc.). `activity_type_category = 'Lead Capture'`.
- **Demo Scheduled** — TWO separate tracks:
  - Webinar: `activity_type_category = 'Demo Scheduled'` (code 920, group webinar booking)
  - Tech Demo: `activity_type_category = 'SE Marked Demo Schedule'` (code 393, 1:1 with Demo Engineer)
- **Demo Completed** — TWO separate tracks:
  - Webinar: `activity_type_category = 'Demo Completed - Webinars'` (codes 342, 397, 921)
  - Tech Demo: `activity_type_category = 'SE Marked Demo Completed'` (code 395)
- **Enroll:** `Is_Valid_Enroll = 1`. Backed by a sale row in `dbo.SkillLyncSalesData`.

**IMPORTANT:** A lead CAN have both Webinar + Tech Demo in the same month, but should NOT be double-counted in a combined "Demos" metric. Use DISTINCTCOUNT(lead_id).

**Demos are conducted by a separate Demo Engineer, NOT the BDA.**

Lead quality distinctions exist among Lead Capture codes (e.g., "Schedule Career Counselling" = high intent vs "Pop-up Registration" = low intent) but **no way to identify this programmatically yet**.

## Lead Segments

- **New Lead** — captured this month, lead_created_on is also this month
- **Old Lead – Capture** — captured this month but lead_created_on is earlier (re-engaged)
- **Old – Others** — no capture this month, but enrolled this month (attribution falls to last_lead_capture_source)

## Sources

`source_attribution_final` values (from Lead Capture rows, ordered by volume):
- Meta (25k leads, largest)
- Email (20.5k)
- Skill-Lync-Resources (10k) — not documented previously
- Organic (4.9k)
- Youtube (3.7k)
- Others (2.3k)
- Direct (1.8k)
- Direct Grow (490)
- Google Ads (239)
- Linkedin (143)
- Whatsapp (42)

Marketing spend data is tracked in **Windsor.ai** and populated into the warehouse.

## Team

**BDA team** (Business Development Associates):
- 42 BDAs in `dbo.BDATierClassification`
- Tier A: 11 active (top performers)
- Tier B: 9 active + 2 inactive
- Tier C: 7 active + 5 inactive
- New: 8 active (recent joinees)
- Total: 35 active / 7 inactive
- **Tier is performance-based** (not tenure)

**Hierarchy** (from `dbo.[User]`):
- SE (Sales Executive / BDA): 5,942 total (most historical)
- DM (Direct Manager): 12
- RSM (Regional Sales Manager): 2
- AD (Area Director): 4
- Regions: Domestic, International
- `dm`, `rsm`, `ad` columns are integer IDs referencing `workforce_id`

**Lead assignment is automated** (scoring-based using priority_score1, prospect_star_rank).

**`team_domain` = program category** (the domain/program area assigned to the lead).

## Operational Facts

- **Timestamps are in IST** (not UTC)
- **No daily calling SOP** — no morning assignment, no daily quotas
- **No formal QA call auditing process**
- **ProspectStageChange is no longer populated** — ignore it
- **prospect_stage, is_customer, lead_owner_id are snapshot (current state)** not point-in-time
- **Test/internal leads exist** and should be excluded (`@skill-lync.com`, `@cybermindworks.com`, etc.)

## Agent Scope

- Analytics engine for same-month funnel + data validation/health checks
- NOT responsible for: daily lead assignment, email reports, GA4 integration
