# Shared Measures — Skill-Lync

**Source of truth:** `/Users/lakshmana/Claude/Skill-Lync Power BI/PowerBI_DAX_Measures.dax`

All SQL definitions below are direct translations of the DAX measures used in the existing Skill-Lync Power BI report. Do NOT change these without cross-checking the DAX file.

> **Status:** v1 measures translated from DAX. **Not yet validated against a known month** — the first run of `report_funnel` should be cross-checked against the PBI report to confirm parity.

---

## Funnel Measures (the only ones supported in v1)

### Leads
**Definition:** Unique leads with a Lead Capture event in the period.
**DAX:** `CALCULATE(DISTINCTCOUNT(Final_Table[lead_id]), Final_Table[activity_type_category] = "Lead Capture")`
**SQL:**
```sql
COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture' THEN lead_id END)
```

### Demos_SE (Demos Scheduled)
**DAX:** `CALCULATE(DISTINCTCOUNT(Final_Table[lead_id]), Final_Table[activity_type_category] = "Demo Scheduled")`
**SQL:**
```sql
COUNT(DISTINCT CASE WHEN activity_type_category = 'Demo Scheduled' THEN lead_id END)
```

### Demos_Completed
**DAX:** `CALCULATE(DISTINCTCOUNT(Final_Table[lead_id]), Final_Table[activity_type_category] IN {"Demo Completed - Webinars", "SE Marked Demo Completed"})`
**SQL:**
```sql
COUNT(DISTINCT CASE WHEN activity_type_category IN
    ('Demo Completed - Webinars', 'SE Marked Demo Completed')
    THEN lead_id END)
```

### Enrolls
**Definition:** Unique leads with a valid enrollment in the period (across all lead segments).
**DAX:** `CALCULATE(DISTINCTCOUNT(Final_Table[lead_id]), Final_Table[Is_Valid_Enroll] = 1)`
**SQL:**
```sql
COUNT(DISTINCT CASE WHEN Is_Valid_Enroll = 1 THEN lead_id END)
```
**⚠️ Do NOT** use `enroll_date IS NOT NULL` — that includes pre-capture enrollments which are not attributable to the activity month. The `Is_Valid_Enroll` flag handles this correctly.

### Same_Month_Enrolls
**Definition:** Lead Capture rows where the same lead enrolled in the same month, on or after the first capture date. Excludes the `Old – Others` segment.
**DAX:** `CALCULATE(DISTINCTCOUNT(Final_Table[lead_id]), Final_Table[activity_type_category] = "Lead Capture", Final_Table[SameMonthEnrolls] = "Enrolls")`
**SQL:**
```sql
COUNT(DISTINCT CASE WHEN activity_type_category = 'Lead Capture'
    AND SameMonthEnrolls = 'Enrolls'
    THEN lead_id END)
```

### Total_Sale_Value (Revenue)
**DAX:** `CALCULATE(SUM(Final_Table[sale_value]), Final_Table[Is_Valid_Enroll] = 1)`
**SQL:**
```sql
SUM(CASE WHEN Is_Valid_Enroll = 1 THEN sale_value END)
```
**Caveat:** `sale_value` comes from `dbo.SkillLyncSalesData` joined on email. If a sale row is missing for a lead, revenue is undercounted but the enrollment count is unaffected.

### Derived Ratios
- **L2D%** = `Demos_SE / Leads`
- **L2E%** = `Enrolls / Leads`
- **D2E%** = `Enrolls / Demos_SE` (note: denominator is Demos_SE, not Demos_Completed)

---

## Measures NOT yet ported (deferred until needed)

These exist in the DAX file but aren't wired into any v1 report. When the user asks for them, port them then — don't speculatively translate.

- `Enrolls_by_Bucket` — for cohort waterfall (needs `Enroll_Month_Bucket_Capped` axis)
- `Cumulative_Enrolls`, `Cumulative_L2E%` — running totals
- `New_Leads`, `New_Lead_Enrolls`, `Old_Lead_Recaptures`, `Old_Lead_Enrolls` — segment splits
- `Total_Realized_Amount` — needs `sale_realized_amount` column
- `Revenue_Per_Lead`, `Avg_Sale_Per_Enroll`
- `Leads_Assigned`, `Enrolls_from_Assigned`, `Assignment_to_Enroll%`
- Star rank measures: `4_Star_Assigned`, `3_Star_Assigned`, `2_Star_Assigned`, `1_Star_Assigned`, `Leads_Assigned_by_Star`, `Enrolls_by_Star`, `Star_Rank_Conversion%`, `Avg_P1_Score`, `Revenue_by_Star`

When porting, follow the same pattern: copy the DAX, translate to SQL, add a `report_*()` function, document here.
