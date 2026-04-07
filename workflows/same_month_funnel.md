# Workflow: Same-Month Funnel

**When to use:** User asks any of these:
- "What's the funnel for [month]?"
- "How many leads / demos / enrolls in [month]?"
- "Show me [month]'s numbers"
- "L2D% / D2E% / L2E% for [month]"
- "Funnel by source / segment for [month]"
- "How are we doing this month?" (after confirming they mean full month, not daily)

**Out of scope (in v1):**
- Daily run rate (no `daily` report yet)
- Cohort lag (no `cohort` report yet — would need `Enroll_Month_Bucket_Capped`)
- BDA performance (no `bda` report yet — would need star rank measures)
- Campaign ROI (no spend data wired in)

If the user asks for any of those, say: "That workflow isn't built yet for Skill-Lync — only same-month funnel is supported in v1. Want me to extend the agent?"

---

## Steps

### 1. Confirm the period
If the user didn't specify a month + year, **ASK**. Do not assume current month.

### 2. Read shared memory (every session)
- `memory/shared_rules.md`
- `memory/shared_measures.md`
- `memory/shared_architecture.md`

### 3. Run the report
For the overall funnel:
```bash
python tools/query_warehouse.py --report funnel --month <M> --year <Y> --json
```

For source breakdown:
```bash
python tools/query_warehouse.py --report funnel_by_source --month <M> --year <Y> --json
```

For segment breakdown (New / Old Capture / Old – Others):
```bash
python tools/query_warehouse.py --report funnel_by_segment --month <M> --year <Y> --json
```

If the user asks for both overall + a breakdown, run the relevant pre-built reports — do not write custom SQL.

### 4. Compute derived ratios in your response
The pre-built reports return raw counts. Calculate ratios in the answer:
- **L2D%** = `Demos_SE / Leads`
- **L2E%** = `Enrolls / Leads`
- **D2E%** = `Enrolls / Demos_SE`
- **Same-Month L2E%** = `Same_Month_Enrolls / Leads`

Format ratios with 1 decimal place (e.g., `12.4%`).

### 5. Validate
- Leads > 0? If not, the month may have no data — check freshness (`check_data_freshness()`).
- Enrolls <= Leads? Should be — if not, something is broken in the report query.
- Total_Sale_Value > 0 if Enrolls > 0? If 0, note that `sale_value` may be missing for some enrollments (missing rows in `dbo.SkillLyncSalesData`).
- Ratios between 0% and 100%?
- For breakdowns: include a totals row.

### 6. Present
- Lead with the answer (the headline number — usually Enrolls or Leads).
- Show the SQL in a code block.
- Show a table with: Leads, Demos_SE, Demos_Completed, Same_Month_Enrolls, Enrolls, Total_Sale_Value, L2D%, D2E%, L2E%.
- For breakdowns, sort rows by Leads descending and add a Total row.
- Caveats:
  - "Revenue is from `dbo.SkillLyncSalesData` joined on email — undercounted if any sale row is missing."
  - If freshness warning: surface it prominently.

### 7. (Optional) Compare to prior month
If the user asks "how does this compare to last month?", run the report twice (current + prior) and present side-by-side with delta and delta-%.

---

## Key reminders

- **Do not** filter on `enroll_date` for enroll counts — use `Is_Valid_Enroll = 1`.
- **Do not** use `activity_type_display_name` — use `activity_type_category` (the bucketed column).
- **Do not** use `lead_segment` for source attribution — use `source_attribution_final`.
- **Same_Month_Enrolls < Enrolls** is normal — the former excludes `Old – Others`.
- The fact table is rebuilt fully every day at 6 AM IST. Same-day data is stale.
