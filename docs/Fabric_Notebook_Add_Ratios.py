# ============================================================
# Fabric Notebook — Add Assignment-Based & PG/Individual Ratios
# ============================================================
# Run AFTER the main measures notebook (v3)
# ============================================================

import sempy.fabric as fabric

DATASET_NAME = "SkillLync-Growth-Master_Report"

measures = [
    # ── Leads Assigned as Denominator ────────────────────────
    # LA = Leads Assigned based ratios

    ("FinalTable", "LA2D%",
     'DIVIDE([Demos_Scheduled], [Leads_Assigned], 0)',
     "2. Funnel Ratios", "0.0%"),

    ("FinalTable", "LA2DC%",
     'DIVIDE([Demos_Completed], [Leads_Assigned], 0)',
     "2. Funnel Ratios", "0.0%"),

    # LA2E% already exists — skip

    # ── PG Ratios (P) ───────────────────────────────────────

    ("FinalTable", "L2E(P)%",
     'DIVIDE([Enrolls_PG], [Leads], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "D2E(P)%",
     'DIVIDE([Enrolls_PG], [Demos_Scheduled], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "LA2E(P)%",
     'DIVIDE([Enrolls_PG], [Leads_Assigned], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "SM_L2E(P)%",
     'DIVIDE(CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[SameMonthEnrolls] = "Enrolls", FinalTable[sale_ind_pg] = "PG"), [Leads], 0)',
     "3. Product Split", "0.0%"),

    # ── Individual Ratios (I) ────────────────────────────────

    ("FinalTable", "L2E(I)%",
     'DIVIDE([Enrolls_Individual], [Leads], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "D2E(I)%",
     'DIVIDE([Enrolls_Individual], [Demos_Scheduled], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "LA2E(I)%",
     'DIVIDE([Enrolls_Individual], [Leads_Assigned], 0)',
     "3. Product Split", "0.0%"),

    # ── Demos Completed as Denominator ───────────────────────

    ("FinalTable", "DC2E%",
     'DIVIDE([Enrolls], [Demos_Completed], 0)',
     "2. Funnel Ratios", "0.0%"),

    ("FinalTable", "DC2E(P)%",
     'DIVIDE([Enrolls_PG], [Demos_Completed], 0)',
     "3. Product Split", "0.0%"),

    ("FinalTable", "DC2E(I)%",
     'DIVIDE([Enrolls_Individual], [Demos_Completed], 0)',
     "3. Product Split", "0.0%"),

    # ── Full Assigned-Based Funnel ───────────────────────────
    # For the Leads → Assigned → Demo → Enroll waterfall

    ("FinalTable", "Demos_from_Assigned",
     'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] IN {"Demo Scheduled", "SE Marked Demo Schedule"}, FinalTable[Is_Assigned_This_Month] = 1)',
     "6. Assignment", "#,##0"),

    ("FinalTable", "Enrolls_from_Assigned",
     'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[Is_Assigned_This_Month] = 1)',
     "6. Assignment", "#,##0"),

    ("FinalTable", "Enrolls_PG_from_Assigned",
     'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[Is_Assigned_This_Month] = 1, FinalTable[sale_ind_pg] = "PG")',
     "6. Assignment", "#,##0"),

    ("FinalTable", "Revenue_from_Assigned",
     'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[Is_Assigned_This_Month] = 1)',
     "6. Assignment", "₹#,##0"),

    # ── Avg Revenue per Enroll by Product ────────────────────

    ("FinalTable", "Avg_Sale_PG",
     'DIVIDE([Revenue_PG], [Enrolls_PG], 0)',
     "3. Product Split", "₹#,##0"),

    ("FinalTable", "Avg_Sale_Individual",
     'DIVIDE([Revenue_Individual], [Enrolls_Individual], 0)',
     "3. Product Split", "₹#,##0"),
]

# =============================================================
# EXECUTE
# =============================================================

print(f"Adding {len(measures)} ratio measures...")

tom = fabric.create_tom_server(readonly=False)
try:
    import Microsoft.AnalysisServices.Tabular as TOM
    db = tom.Databases.GetByName(DATASET_NAME)
    model = db.Model
    success = 0

    for table_name, name, expression, folder, fmt in measures:
        try:
            table = model.Tables.Find(table_name)
            if table is None:
                print(f"  ⚠️  Table '{table_name}' not found")
                continue

            existing = table.Measures.Find(name)
            if existing is not None:
                table.Measures.Remove(existing)

            m = TOM.Measure()
            m.Name = name
            m.Expression = expression
            m.DisplayFolder = folder
            if fmt:
                m.FormatString = fmt
            table.Measures.Add(m)
            success += 1
            print(f"  ✅ {name}")

        except Exception as e:
            print(f"  ❌ {name} — {str(e)[:120]}")

    model.SaveChanges()
    print(f"\n✅ Done! {success} measures added.")

finally:
    tom.Disconnect()
