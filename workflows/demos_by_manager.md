# Workflow: Demos by Manager Level

**When to use:** User asks any of these:
- "Demos scheduled / completed by BDA / DM / RSM / AD"
- "Manager-level view of demos"
- "How are [Siva's / Sakthi's / Thameem's] teams doing on demos"
- "Tech demos by manager"

**Scope:** Tech demos only (SE-marked 1:1). Webinar auto-logs are excluded because they bypass the BDA attribution chain and break scheduled→completed sanity (Completed > Scheduled).

---

## Definitions

| Term | SQL |
|---|---|
| **Tech Demos Scheduled** | `COUNT(DISTINCT lead_id) WHERE activity_type_category='SE Marked Demo Schedule'` |
| **Tech Demos Completed** | `COUNT(DISTINCT lead_id) WHERE activity_type_category='SE Marked Demo Completed'` |

Both are **unique-lead counts** — matches DAX measures `Demos_Tech_Scheduled` / `Demos_Tech_Completed` in `docs/PBI_DAX_Measures.dax`.

## Hierarchy

Resolved via `dim.[User]` (see `sql/12_dim_user.sql`). Current manager only — no point-in-time / at-assignment attribution.

```
BDA (role='se') → DM → RSM → AD
```

A user with `role='dm'` who runs demos themselves is attributed to **their own name** at the DM level (not bumped up to their RSM).

## Reports

```bash
python tools/query_warehouse.py --report demos_by_bda --month <M> --year <Y>
python tools/query_warehouse.py --report demos_by_dm  --month <M> --year <Y>
python tools/query_warehouse.py --report demos_by_rsm --month <M> --year <Y>
python tools/query_warehouse.py --report demos_by_ad  --month <M> --year <Y>
```

Each returns `Demos_Tech_Scheduled` and `Demos_Tech_Completed` as distinct-lead counts.

`demos_by_bda` also includes the BDA's current DM for context.

## Steps

1. **Confirm period.** Ask if month/year is not specified.
2. **Pick level.** Default to DM if user says "manager"; confirm if ambiguous between DM/RSM/AD.
3. **Run the report.** Use the pre-built function — do not write ad-hoc SQL.
4. **Validate:**
   - Completed ≤ Scheduled per row (must hold for tech-only).
   - `(Unassigned)` row should be small — if > 5% of grand total, investigate `bda_id IS NULL` rows or users missing from `dim.[User]`.
   - Sum of rows may exceed grand total — this is correct (same lead worked across teams). Do not "fix" via arbitrary assignment.
5. **Present:**
   - Lead with the headline (top DM / top BDA by scheduled).
   - Show SQL in a code block.
   - Totals row at bottom.
   - Add DS2DC% (Completed ÷ Scheduled) column if helpful.

## Out of scope

- Webinar demos by manager — webinars have no BDA attribution. Add as a separate request only if needed.
- Historical (at-time-of-activity) attribution — not built; would require snapshotting `dbo.[User].dm` over time.
- Multi-month trend in one report — run the monthly report multiple times, or extend with a `start_month`/`end_month` variant if repeatedly needed.
