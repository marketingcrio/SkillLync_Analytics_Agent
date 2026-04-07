# Shared Business Context — Skill-Lync

> **Status: STUB.** Fill this in as you learn from the user. Do not guess.

---

## Company

Skill-Lync is an upskilling company. Sister company to Crio. (TODO: confirm — products, target audience, competitive position.)

## Products / Programs

TODO: list of programs/courses sold. The fact table has `Program_Interested`, `sale_program`, and `mx_interested_courses` — running `SELECT DISTINCT sale_program FROM fact.Final_Table WHERE Is_Valid_Enroll=1` would give a starting list.

Known program patterns from the DDL:
- IIT Jammu Design
- IIT Jammu EV
- (others — TBD)

## Pricing

TODO: typical ticket sizes, payment plans (full vs EMI vs MOF), discount structure.

## Funnel

Skill-Lync uses a **3-stage funnel**:

```
Lead Capture  ──►  Demo Scheduled  ──►  Demo Completed  ──►  Enroll (Valid)
```

- **Lead Capture:** any of ~50 LSQ activity codes representing form fills, downloads, page visits with intent. Bucketed as `activity_type_category = 'Lead Capture'`.
- **Demo Scheduled:** demo booked. `activity_type_category = 'Demo Scheduled'`.
- **Demo Completed:** demo actually attended. `activity_type_category IN ('Demo Completed - Webinars', 'SE Marked Demo Completed')`.
- **Enroll:** `Is_Valid_Enroll = 1`. Backed by a sale row in `dbo.SkillLyncSalesData`.

Compared to Crio's 7-stage funnel (App → TA → 1:1 → QL → PE → Enroll), this is much simpler. There is no "trial workshop" concept here, no qualified-lead split, no provisional enrollment phase.

## Lead Segments

- **New Lead** — captured this month, lead_created_on is also this month
- **Old Lead – Capture** — captured this month but lead_created_on is earlier (re-engaged)
- **Old – Others** — no capture this month, but enrolled this month (attribution falls to last_lead_capture_source)

## Sources

Bucketed source values seen in `Source_Bucket_Final`:
- Direct Grow
- Youtube
- Meta
- Linkedin
- Google Ads
- Email
- Whatsapp
- Organic
- Direct
- Others

## Team

TODO: BDA team structure, tiers, leadership. The fact table has `bda_tier` and `bda_status` from `dbo.BDATierClassification`.

The xlsx files in `/Users/lakshmana/Claude/Skill-Lync Data Analysis/` may have more context:
- `SL_BDA_Performance_Scorecard.xlsx`
- `SL_BDA_Tier_Classification.xlsx`
- `SL_Lead_Strategy_L2E_Targets.xlsx`
- `SL_Operations_Playbook_PowerBI_Spec.xlsx`

When the user asks for team-level analysis, read these first.

## Reporting Cadence

TODO: who needs what report, how often, what format.

## Stakeholders

TODO: names, roles, communication preferences.
