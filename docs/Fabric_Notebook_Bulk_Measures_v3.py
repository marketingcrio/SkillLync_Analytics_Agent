# ============================================================
# Fabric Notebook — Bulk Create DAX Measures via TOM API (v3)
# ============================================================
# 1. Fabric portal → New → Notebook
# 2. Update DATASET_NAME below
# 3. Paste into Cell 1 → Run
# ============================================================

import sempy.fabric as fabric
import Microsoft.AnalysisServices.Tabular as TOM

# ── UPDATE THIS ──────────────────────────────────────────────
DATASET_NAME = "SkillLync-Growth-Master_Report"
# ─────────────────────────────────────────────────────────────

measures = [
    # (table, name, expression, folder, format)

    # ── 1. Core Funnel ───────────────────────────────────────
    ("FinalTable", "Leads", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Webinar_Scheduled", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Demo Scheduled")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Tech_Scheduled", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "SE Marked Demo Schedule")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Scheduled", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] IN {"Demo Scheduled", "SE Marked Demo Schedule"})', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Webinar_Completed", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Demo Completed - Webinars")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Tech_Completed", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "SE Marked Demo Completed")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Demos_Completed", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] IN {"Demo Completed - Webinars", "SE Marked Demo Completed"})', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Enrolls", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1)', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Same_Month_Enrolls", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[SameMonthEnrolls] = "Enrolls")', "1. Core Funnel", "#,##0"),
    ("FinalTable", "Revenue", 'SUM(FinalTable[sale_value])', "1. Core Funnel", "₹#,##0"),

    # ── 2. Funnel Ratios ─────────────────────────────────────
    ("FinalTable", "L2D%", 'DIVIDE([Demos_Scheduled], [Leads], 0)', "2. Funnel Ratios", "0.0%"),
    ("FinalTable", "L2E%", 'DIVIDE([Enrolls], [Leads], 0)', "2. Funnel Ratios", "0.0%"),
    ("FinalTable", "D2E%", 'DIVIDE([Enrolls], [Demos_Scheduled], 0)', "2. Funnel Ratios", "0.0%"),
    ("FinalTable", "SM_L2E%", 'DIVIDE([Same_Month_Enrolls], [Leads], 0)', "2. Funnel Ratios", "0.0%"),
    ("FinalTable", "DS2DC%", 'DIVIDE([Demos_Completed], [Demos_Scheduled], 0)', "2. Funnel Ratios", "0.0%"),
    ("FinalTable", "Avg_Sale_Per_Enroll", 'DIVIDE([Revenue], [Enrolls], 0)', "2. Funnel Ratios", "₹#,##0"),

    # ── 3. Product Split ─────────────────────────────────────
    ("FinalTable", "Enrolls_PG", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[sale_ind_pg] = "PG")', "3. Product Split", "#,##0"),
    ("FinalTable", "Enrolls_Individual", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"})', "3. Product Split", "#,##0"),
    ("FinalTable", "Revenue_PG", 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] = "PG")', "3. Product Split", "₹#,##0"),
    ("FinalTable", "Revenue_Individual", 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"})', "3. Product Split", "₹#,##0"),

    # ── 4. Lead Segment ──────────────────────────────────────
    ("FinalTable", "Leads_New", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "New Lead")', "4. Lead Segment", "#,##0"),
    ("FinalTable", "Leads_Old_Capture", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "Old Lead - Capture")', "4. Lead Segment", "#,##0"),
    ("FinalTable", "Enrolls_New", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "New Lead")', "4. Lead Segment", "#,##0"),
    ("FinalTable", "Enrolls_Old_Capture", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old Lead - Capture")', "4. Lead Segment", "#,##0"),
    ("FinalTable", "Enrolls_Old_Others", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old - Others")', "4. Lead Segment", "#,##0"),
    ("FinalTable", "L2E%_New", 'DIVIDE([Enrolls_New], [Leads_New], 0)', "4. Lead Segment", "0.0%"),
    ("FinalTable", "L2E%_Old_Capture", 'DIVIDE([Enrolls_Old_Capture], [Leads_Old_Capture], 0)', "4. Lead Segment", "0.0%"),

    # ── 5. Enrollment Cohort ─────────────────────────────────
    ("FinalTable", "Enrolls_M0", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+0")', "5. Enrollment Cohort", "#,##0"),
    ("FinalTable", "Enrolls_M1", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+1")', "5. Enrollment Cohort", "#,##0"),
    ("FinalTable", "Enrolls_M2", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+2")', "5. Enrollment Cohort", "#,##0"),
    ("FinalTable", "Enrolls_M3", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+3")', "5. Enrollment Cohort", "#,##0"),
    ("FinalTable", "Cumulative_Enrolls_M3", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] IN {"M+0","M+1","M+2","M+3"})', "5. Enrollment Cohort", "#,##0"),
    ("FinalTable", "Cumulative_L2E%_M3", 'DIVIDE([Cumulative_Enrolls_M3], [Leads], 0)', "5. Enrollment Cohort", "0.0%"),

    # ── 6. Assignment ────────────────────────────────────────
    ("FinalTable", "Leads_Assigned", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Assigned_This_Month] = 1)', "6. Assignment", "#,##0"),
    ("FinalTable", "Leads_Assigned_First", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)', "6. Assignment", "#,##0"),
    ("FinalTable", "Leads_Assigned_New", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "New")', "6. Assignment", "#,##0"),
    ("FinalTable", "Leads_Assigned_Others", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "Others")', "6. Assignment", "#,##0"),
    ("FinalTable", "Assignment_Coverage%", 'DIVIDE([Leads_Assigned], [Leads], 0)', "6. Assignment", "0.0%"),
    ("FinalTable", "LA2E%", 'DIVIDE([Enrolls], [Leads_Assigned], 0)', "6. Assignment", "0.0%"),

    # ── 7. Star Rank ─────────────────────────────────────────
    ("FinalTable", "Leads_Assigned_FourStar", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "FourStar")', "7. Star Rank", "#,##0"),
    ("FinalTable", "Leads_Assigned_ThreeStar", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "ThreeStar")', "7. Star Rank", "#,##0"),
    ("FinalTable", "Leads_Assigned_TwoStar", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "TwoStar")', "7. Star Rank", "#,##0"),
    ("FinalTable", "Leads_Assigned_OneStar", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "OneStar")', "7. Star Rank", "#,##0"),
    ("FinalTable", "Star_Match_Count", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[Is_Star_Match] = 1)', "7. Star Rank", "#,##0"),
    ("FinalTable", "Star_Match%", 'DIVIDE([Star_Match_Count], [Leads_Assigned_First], 0)', "7. Star Rank", "0.0%"),
    ("FinalTable", "Enrolls_FourStar", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_star_rank_at_assign] = "FourStar")', "7. Star Rank", "#,##0"),
    ("FinalTable", "L2E%_FourStar", 'DIVIDE([Enrolls_FourStar], [Leads_Assigned_FourStar], 0)', "7. Star Rank", "0.0%"),
    ("FinalTable", "Avg_P1_Score_At_Assign", 'CALCULATE(AVERAGE(FinalTable[p1_score_at_assign]), FinalTable[Is_First_Assignment_Per_Month] = 1)', "7. Star Rank", "#,##0.0"),
    ("FinalTable", "Revenue_FourStar", 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[lead_star_rank_at_assign] = "FourStar")', "7. Star Rank", "₹#,##0"),

    # ── 8. BDA Performance ───────────────────────────────────
    ("FinalTable", "Leads_Per_BDA", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_name]))', "8. BDA Performance", "#,##0"),
    ("FinalTable", "Enrolls_Per_BDA", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_name]))', "8. BDA Performance", "#,##0"),
    ("FinalTable", "Revenue_Per_BDA", 'CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[bda_name]))', "8. BDA Performance", "₹#,##0"),
    ("FinalTable", "Active_BDAs", 'CALCULATE(DISTINCTCOUNT(FinalTable[bda_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)', "8. BDA Performance", "#,##0"),
    ("FinalTable", "BDA_L2E%", 'DIVIDE([Enrolls_Per_BDA], [Leads_Per_BDA], 0)', "8. BDA Performance", "0.0%"),

    # ── 9. BDA Tier ──────────────────────────────────────────
    ("FinalTable", "Leads_by_Tier", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_tier]))', "9. BDA Tier", "#,##0"),
    ("FinalTable", "Enrolls_by_Tier", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_tier]))', "9. BDA Tier", "#,##0"),
    ("FinalTable", "L2E%_by_Tier", 'DIVIDE([Enrolls_by_Tier], [Leads_by_Tier], 0)', "9. BDA Tier", "0.0%"),

    # ── 10. Source ───────────────────────────────────────────
    ("FinalTable", "Leads_by_Source", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[source_attribution_final]))', "10. Source", "#,##0"),
    ("FinalTable", "Enrolls_by_Source", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[source_attribution_final]))', "10. Source", "#,##0"),
    ("FinalTable", "L2E%_by_Source", 'DIVIDE([Enrolls_by_Source], [Leads_by_Source], 0)', "10. Source", "0.0%"),

    # ── 11. MoM ──────────────────────────────────────────────
    ("FinalTable", "Leads_PM", 'CALCULATE([Leads], DATEADD(FinalTable[activity_month_start], -1, MONTH))', "11. MoM", "#,##0"),
    ("FinalTable", "Enrolls_PM", 'CALCULATE([Enrolls], DATEADD(FinalTable[activity_month_start], -1, MONTH))', "11. MoM", "#,##0"),
    ("FinalTable", "Leads_MoM%", 'DIVIDE([Leads] - [Leads_PM], [Leads_PM], 0)', "11. MoM", "0.0%"),
    ("FinalTable", "Enrolls_MoM%", 'DIVIDE([Enrolls] - [Enrolls_PM], [Enrolls_PM], 0)', "11. MoM", "0.0%"),

    # ── 12. Domain ───────────────────────────────────────────
    ("FinalTable", "Leads_by_Domain", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[Domain_group]))', "12. Domain", "#,##0"),
    ("FinalTable", "Enrolls_by_Domain", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[Domain_group]))', "12. Domain", "#,##0"),

    # ── 13. Data Quality ─────────────────────────────────────
    ("FinalTable", "Total_Rows", 'COUNTROWS(FinalTable)', "13. Data Quality", "#,##0"),
    ("FinalTable", "Unique_Leads", 'DISTINCTCOUNT(FinalTable[lead_id])', "13. Data Quality", "#,##0"),

    # ── 14. Customer Profile ─────────────────────────────────
    ("FinalTable", "Leads_Job_Seeker", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "JOB SEEKER")', "14. Customer Profile", "#,##0"),
    ("FinalTable", "Leads_Student", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "STUDENT")', "14. Customer Profile", "#,##0"),
    ("FinalTable", "Leads_Working_Professional", 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "WORKING PROFESSIONAL")', "14. Customer Profile", "#,##0"),

    # ── CallDetail ───────────────────────────────────────────
    ("CallDetail", "Dials", 'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1)', "1. Core Calling", "#,##0"),
    ("CallDetail", "Dialled_Leads", 'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1)', "1. Core Calling", "#,##0"),
    ("CallDetail", "Connected_Leads", 'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)', "1. Core Calling", "#,##0"),
    ("CallDetail", "Connected_Calls", 'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)', "1. Core Calling", "#,##0"),
    ("CallDetail", "DNP_Leads", 'CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)', "1. Core Calling", "#,##0"),
    ("CallDetail", "Connectivity%", 'DIVIDE([Connected_Leads], [Dialled_Leads], 0)', "2. Calling Ratios", "0.0%"),
    ("CallDetail", "DNP_Rate", 'DIVIDE([DNP_Leads], [Dialled_Leads], 0)', "2. Calling Ratios", "0.0%"),
    ("CallDetail", "CC_per_Lead", 'DIVIDE([Connected_Calls], [Connected_Leads], 0)', "2. Calling Ratios", "#,##0.0"),
    ("CallDetail", "Avg_Call_Duration_Sec", 'CALCULATE(AVERAGE(CallDetail[call_duration_sec]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)', "3. Duration", "#,##0"),
    ("CallDetail", "Quality_Call%", 'DIVIDE(CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, CallDetail[call_duration_sec] > 60), CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1), 0)', "3. Duration", "0.0%"),
    ("CallDetail", "Active_Calling_BDAs", 'CALCULATE(DISTINCTCOUNT(CallDetail[se_user_id]), CallDetail[Is_Valid_Call] = 1)', "4. BDA Calling", "#,##0"),
    ("CallDetail", "Dials_per_BDA", 'DIVIDE([Dials], [Active_Calling_BDAs], 0)', "4. BDA Calling", "#,##0.0"),
    ("CallDetail", "Dials_Manual", 'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = TRUE())', "5. Manual vs Auto", "#,##0"),
    ("CallDetail", "Dials_Auto", 'CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = FALSE())', "5. Manual vs Auto", "#,##0"),
    ("CallDetail", "Manual_Call%", 'DIVIDE([Dials_Manual], [Dials], 0)', "5. Manual vs Auto", "0.0%"),
]

# =============================================================
# EXECUTE via TOM API (no context manager)
# =============================================================

print(f"Connecting to '{DATASET_NAME}'...")
print(f"Total measures: {len(measures)}")
print()

tom = fabric.create_tom_server(readonly=False)
try:
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
            print(f"  ✅ [{table_name}] {name}")

        except Exception as e:
            failed += 1
            print(f"  ❌ [{table_name}] {name} — {str(e)[:120]}")

    print(f"\nSaving {success} measures to model...")
    model.SaveChanges()
    print(f"✅ Done! {success} created, {failed} failed.")

finally:
    tom.Disconnect()
    print("Disconnected.")
