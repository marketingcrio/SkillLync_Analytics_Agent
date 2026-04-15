# ============================================================
# Fabric Notebook — CallDetail: Relationship + All Measures
# ============================================================
# Run AFTER fact.CallDetail is created in the warehouse
# and the table appears in the semantic model.
# ============================================================

import sempy.fabric as fabric

DATASET_NAME = "SkillLync-Growth-Master_Report"

# =============================================================
# STEP 1: CREATE RELATIONSHIP (FinalTable → CallDetail on lead_id)
# =============================================================

print("=" * 60)
print("STEP 1: Creating relationship")
print("=" * 60)

tom = fabric.create_tom_server(readonly=False)
try:
    import Microsoft.AnalysisServices.Tabular as TOM
    db = tom.Databases.GetByName(DATASET_NAME)
    model = db.Model

    ft = model.Tables.Find("FinalTable")
    cd = model.Tables.Find("CallDetail")

    if ft is None:
        print("❌ FinalTable not found in model")
    elif cd is None:
        print("❌ CallDetail not found in model — add it to the semantic model first")
    else:
        # Check if relationship already exists
        rel_exists = False
        for rel in model.Relationships:
            if (rel.FromTable.Name == "CallDetail" and rel.ToTable.Name == "FinalTable"):
                rel_exists = True
                break
            if (rel.FromTable.Name == "FinalTable" and rel.ToTable.Name == "CallDetail"):
                rel_exists = True
                break

        if rel_exists:
            print("✅ Relationship already exists — skipping")
        else:
            # Create: CallDetail[lead_id] *──1 FinalTable[lead_id]
            # Many-to-many since both tables have multiple rows per lead
            try:
                rel = TOM.SingleColumnRelationship()
                rel.Name = "CallDetail_to_FinalTable_lead_id"
                rel.FromColumn = cd.Columns.Find("lead_id")
                rel.ToColumn = ft.Columns.Find("lead_id")
                rel.CrossFilteringBehavior = TOM.CrossFilteringBehavior.BothDirections
                rel.IsActive = False  # Inactive — use USERELATIONSHIP in DAX when needed
                model.Relationships.Add(rel)
                print("✅ Relationship created (inactive — use USERELATIONSHIP when needed)")
                print("   CallDetail[lead_id] → FinalTable[lead_id]")
            except Exception as e:
                print(f"⚠️  Relationship creation failed: {str(e)[:200]}")
                print("   You can create it manually in the model editor:")
                print("   CallDetail[lead_id] → FinalTable[lead_id], Many-to-Many, Both directions")

        model.SaveChanges()
        print("✅ Model saved")

finally:
    tom.Disconnect()

# =============================================================
# STEP 2: CREATE ALL CALLDETAIL MEASURES
# =============================================================

print()
print("=" * 60)
print("STEP 2: Creating CallDetail measures")
print("=" * 60)

measures = [
    # ── 1. Core Calling ──────────────────────────────────────
    ("CallDetail", "Dials",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1)',
     "1. Core Calling", "#,##0"),

    ("CallDetail", "Dialled_Leads",
     'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1)',
     "1. Core Calling", "#,##0"),

    ("CallDetail", "Connected_Leads",
     'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)',
     "1. Core Calling", "#,##0"),

    ("CallDetail", "Connected_Calls",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)',
     "1. Core Calling", "#,##0"),

    ("CallDetail", "DNP_Leads",
     'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)',
     "1. Core Calling", "#,##0"),

    ("CallDetail", "DNP_Calls",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)',
     "1. Core Calling", "#,##0"),

    # ── 2. Calling Ratios ────────────────────────────────────
    ("CallDetail", "Connectivity%",
     'DIVIDE([Connected_Leads], [Dialled_Leads], 0)',
     "2. Calling Ratios", "0.0%"),

    ("CallDetail", "DNP_Rate",
     'DIVIDE([DNP_Leads], [Dialled_Leads], 0)',
     "2. Calling Ratios", "0.0%"),

    ("CallDetail", "CC_per_Lead",
     'DIVIDE([Connected_Calls], [Connected_Leads], 0)',
     "2. Calling Ratios", "#,##0.0"),

    ("CallDetail", "Dials_per_Lead",
     'DIVIDE([Dials], [Dialled_Leads], 0)',
     "2. Calling Ratios", "#,##0.0"),

    # ── 3. Duration ──────────────────────────────────────────
    ("CallDetail", "Avg_Call_Duration_Sec",
     'CALCULATE(AVERAGE(CallDetail[call_duration_sec]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)',
     "3. Duration", "#,##0"),

    ("CallDetail", "Avg_Call_Duration_Formatted",
     'VAR secs = [Avg_Call_Duration_Sec] RETURN IF(ISBLANK(secs), "-", FORMAT(INT(secs / 60), "0") & ":" & FORMAT(MOD(INT(secs), 60), "00"))',
     "3. Duration", None),

    ("CallDetail", "Quality_Call%",
     'DIVIDE(CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, CallDetail[call_duration_sec] > 60), CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1), 0)',
     "3. Duration", "0.0%"),

    ("CallDetail", "Calls_Under_30s",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[call_duration_bucket] = "<30s")',
     "3. Duration", "#,##0"),

    ("CallDetail", "Calls_30_60s",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[call_duration_bucket] = "30-60s")',
     "3. Duration", "#,##0"),

    ("CallDetail", "Calls_60_180s",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[call_duration_bucket] = "60-180s")',
     "3. Duration", "#,##0"),

    ("CallDetail", "Calls_Over_180s",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[call_duration_bucket] = ">180s")',
     "3. Duration", "#,##0"),

    # ── 4. BDA Calling Performance ───────────────────────────
    ("CallDetail", "Active_Calling_BDAs",
     'CALCULATE(DISTINCTCOUNT(CallDetail[se_user_id]), CallDetail[Is_Valid_Call] = 1)',
     "4. BDA Calling", "#,##0"),

    ("CallDetail", "Dials_per_BDA",
     'DIVIDE([Dials], [Active_Calling_BDAs], 0)',
     "4. BDA Calling", "#,##0.0"),

    ("CallDetail", "Connected_per_BDA",
     'DIVIDE([Connected_Calls], [Active_Calling_BDAs], 0)',
     "4. BDA Calling", "#,##0.0"),

    ("CallDetail", "Dialled_Leads_per_BDA",
     'DIVIDE([Dialled_Leads], [Active_Calling_BDAs], 0)',
     "4. BDA Calling", "#,##0.0"),

    # ── 5. Manual vs Auto ────────────────────────────────────
    ("CallDetail", "Dials_Manual",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = TRUE())',
     "5. Manual vs Auto", "#,##0"),

    ("CallDetail", "Dials_Auto",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = FALSE())',
     "5. Manual vs Auto", "#,##0"),

    ("CallDetail", "Manual_Call%",
     'DIVIDE([Dials_Manual], [Dials], 0)',
     "5. Manual vs Auto", "0.0%"),

    # ── 6. MoM Calling ───────────────────────────────────────
    ("CallDetail", "Dials_PM",
     'CALCULATE([Dials], DATEADD(CallDetail[call_month_start], -1, MONTH))',
     "6. MoM Calling", "#,##0"),

    ("CallDetail", "Connected_Leads_PM",
     'CALCULATE([Connected_Leads], DATEADD(CallDetail[call_month_start], -1, MONTH))',
     "6. MoM Calling", "#,##0"),

    ("CallDetail", "Connectivity%_PM",
     'CALCULATE([Connectivity%], DATEADD(CallDetail[call_month_start], -1, MONTH))',
     "6. MoM Calling", "0.0%"),

    ("CallDetail", "Dials_MoM%",
     'DIVIDE([Dials] - [Dials_PM], [Dials_PM], 0)',
     "6. MoM Calling", "0.0%"),

    # ── 7. By Domain / Profile ───────────────────────────────
    ("CallDetail", "Dials_by_Domain",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, NOT ISBLANK(CallDetail[Domain_group]))',
     "7. By Domain", "#,##0"),

    ("CallDetail", "Connected_by_Domain",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, NOT ISBLANK(CallDetail[Domain_group]))',
     "7. By Domain", "#,##0"),

    ("CallDetail", "Connectivity%_by_Domain",
     'DIVIDE(CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, NOT ISBLANK(CallDetail[Domain_group])), CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, NOT ISBLANK(CallDetail[Domain_group])), 0)',
     "7. By Domain", "0.0%"),

    # ── 8. By BDA Tier ───────────────────────────────────────
    ("CallDetail", "Dials_by_Tier",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, NOT ISBLANK(CallDetail[bda_tier]))',
     "8. By BDA Tier", "#,##0"),

    ("CallDetail", "Connected_by_Tier",
     'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, NOT ISBLANK(CallDetail[bda_tier]))',
     "8. By BDA Tier", "#,##0"),

    ("CallDetail", "Connectivity%_by_Tier",
     'DIVIDE(CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, NOT ISBLANK(CallDetail[bda_tier])), CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, NOT ISBLANK(CallDetail[bda_tier])), 0)',
     "8. By BDA Tier", "0.0%"),

    # ── 9. KPI Cards ─────────────────────────────────────────
    ("CallDetail", "KPI_Dials_MoM_Arrow",
     'IF([Dials_MoM%] > 0, "▲ " & FORMAT([Dials_MoM%], "0.0%"), IF([Dials_MoM%] < 0, "▼ " & FORMAT([Dials_MoM%], "0.0%"), "─ 0.0%"))',
     "9. KPI Cards", None),
]

tom = fabric.create_tom_server(readonly=False)
try:
    import Microsoft.AnalysisServices.Tabular as TOM
    db = tom.Databases.GetByName(DATASET_NAME)
    model = db.Model
    success = 0
    failed = 0

    for table_name, name, expression, folder, fmt in measures:
        try:
            table = model.Tables.Find(table_name)
            if table is None:
                print(f"  ⚠️  Table '{table_name}' not found — skipping {name}")
                failed += 1
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
            failed += 1
            print(f"  ❌ {name} — {str(e)[:120]}")

    print(f"\nSaving {success} measures...")
    model.SaveChanges()
    print(f"✅ Done! {success} created, {failed} failed.")

finally:
    tom.Disconnect()
    print("Disconnected.")
