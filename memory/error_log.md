# Error Log — Skill-Lync Agent

Append every error + fix here. Format:

```
## YYYY-MM-DD — short title
**Query / context:** ...
**Error:** ...
**Root cause:** ...
**Fix:** ...
```

---

## 2026-04-10 — Demos_SE returns ZERO for recent months (BUG #1)
**Query / context:** `report_funnel` for Jan/Feb/Mar 2026 returns Demos_SE = 0.
**Error:** The SQL filter `activity_type_category = 'Demo Scheduled'` only matches code 920 (Sales webinar scheduled, 749 rows total). The tech-demo scheduling track is in a SEPARATE category `'SE Marked Demo Schedule'` (code 393, 4,794 rows). Code 920 has zero rows in Jan/Feb/Mar 2026.
**Root cause:** The DAX Demos_SE measure and the SQL translation both only reference 'Demo Scheduled'. The tech demo track was not included.
**Fix:** User confirmed these are two separate demo tracks. Demos_SE should be bifurcated:
- Webinar Demos Scheduled: `activity_type_category = 'Demo Scheduled'`
- Tech Demos Scheduled: `activity_type_category = 'SE Marked Demo Schedule'`
- Combined Demos Scheduled: both categories, DISTINCTCOUNT to avoid double-counting leads with both.

## 2026-04-10 — Revenue is ~10-16x inflated (BUG #2)
**Query / context:** `report_funnel` Total_Sale_Value for all months is wildly overcounted.
**Error:** `SUM(CASE WHEN Is_Valid_Enroll=1 THEN sale_value END)` sums sale_value across ALL rows of an enrolled lead. Each enrolled lead averages 15.65 rows with Is_Valid_Enroll=1 (max 169). So SUM multiplies true revenue by ~15x.
**Root cause:** sale_value is joined from SkillLyncSalesData onto every activity row for the lead. Is_Valid_Enroll=1 fires on multiple rows (every Lead Capture + other activity rows for enrolled leads). Naive SUM double/triple/15x counts.
**Proof:**
- SkillLyncSalesData total (all-time): ₹4.23 crore
- Fact naive SUM(IVE=1): ₹42.20 crore (10x!)
- Fact SUM(IVE=1 AND atc='Lead Capture'): ₹4.24 crore (matches!)
- Fact MAX-per-lead aggregation: ₹2.69 crore for period (reconciles to ~96% of source)
- User confirmed: correct monthly revenue is ₹25-40 lakh range
**Fix:** Use MAX-per-lead pre-aggregation for any revenue measure:
```sql
WITH per_lead AS (
  SELECT activity_year, activity_month, lead_id, MAX(sale_value) AS sale
  FROM fact.Final_Table WHERE Is_Valid_Enroll=1
  GROUP BY activity_year, activity_month, lead_id
)
SELECT SUM(sale) ...
```
Or as a simpler approximation: add `AND activity_type_category='Lead Capture'` filter.

## 2026-04-10 — Call Activity category undercounts by ~610k rows (BUG #3)
**Query / context:** Profiling activity_type_category distribution.
**Error:** Call Activity only contains code 506 (Kaleyra Outbound, 665k rows). Codes 507 (Manual Outbound, 8.9k), 777 (Priority Call, 117k), 2500 (DNP, 472k), 2502 (DNP-Within Limit, 12k) are all in "Other / Unknown".
**Root cause:** The activity_type_category CASE statement in the SP only maps code 506 to 'Call Activity'. The other call-related codes were not included.
**Fix:** User confirmed this is NOT intentional. These codes need to be reclassified to 'Call Activity' in the SP rebuild. Total call volume = ~1.27M rows (not 665k).

## 2026-04-10 — Junk activity codes confirmed
**Query / context:** Codes 295 (szcfds), 298 (zxc), 433 (hkj), 434 (sdf), 436 (hgvugvhg hj).
**Error:** These are test/junk entries in dbo.ActivityType.
**Root cause:** Test data from LSQ setup.
**Fix:** Exclude from any pipeline rebuild. They don't appear in the current fact table (already filtered), but document them as known junk.
