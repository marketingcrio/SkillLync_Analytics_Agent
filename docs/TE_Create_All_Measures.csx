// ============================================================
// Tabular Editor C# Script — Bulk Create ALL DAX Measures
// ============================================================
// HOW TO USE:
// 1. Download Tabular Editor 2 (free) from https://tabulareditor.com
// 2. Connect to your Fabric semantic model via XMLA endpoint
//    (Workspace Settings → Premium → XMLA Endpoint → copy the URL)
// 3. Open Advanced Scripting pane (View → Advanced Scripting)
// 4. Paste this entire script
// 5. Click Run (▶)
// 6. Save (Ctrl+S) to push all measures to the model
// ============================================================

var ft = Model.Tables["FinalTable"];
var cd = Model.Tables["CallDetail"];

// Helper: create measure if it doesn't exist, update if it does
Action<Table, string, string, string, string> AddMeasure = (table, name, expression, folder, format) => {
    Measure m;
    if (table.Measures.Contains(name)) {
        m = table.Measures[name];
    } else {
        m = table.AddMeasure(name);
    }
    m.Expression = expression;
    m.DisplayFolder = folder;
    if (format != null) m.FormatString = format;
};


// =============================================================
// FINALTABLE MEASURES
// =============================================================

// ── Section 1: Core Funnel ──────────────────────────────────

AddMeasure(ft, "Leads",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Webinar_Scheduled",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Demo Scheduled""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Tech_Scheduled",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""SE Marked Demo Schedule""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Scheduled",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] IN {
        ""Demo Scheduled"", ""SE Marked Demo Schedule""
    }
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Webinar_Completed",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Demo Completed - Webinars""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Tech_Completed",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""SE Marked Demo Completed""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Demos_Completed",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] IN {
        ""Demo Completed - Webinars"", ""SE Marked Demo Completed""
    }
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Enrolls",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Same_Month_Enrolls",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[SameMonthEnrolls] = ""Enrolls""
)",
    "1. Core Funnel", "#,##0");

AddMeasure(ft, "Revenue",
    @"SUM(FinalTable[sale_value])",
    "1. Core Funnel", "₹#,##0");

AddMeasure(ft, "Revenue_Formatted",
    @"VAR rev = [Revenue]
RETURN
    IF(rev >= 100000, FORMAT(rev / 100000, ""#,##0.00"") & "" L"",
    IF(rev >= 1000, FORMAT(rev / 1000, ""#,##0.0"") & "" K"",
    FORMAT(rev, ""#,##0"")))",
    "1. Core Funnel", null);


// ── Section 2: Funnel Ratios ────────────────────────────────

AddMeasure(ft, "L2D%",
    @"DIVIDE([Demos_Scheduled], [Leads], 0)",
    "2. Funnel Ratios", "0.0%");

AddMeasure(ft, "L2E%",
    @"DIVIDE([Enrolls], [Leads], 0)",
    "2. Funnel Ratios", "0.0%");

AddMeasure(ft, "D2E%",
    @"DIVIDE([Enrolls], [Demos_Scheduled], 0)",
    "2. Funnel Ratios", "0.0%");

AddMeasure(ft, "SM_L2E%",
    @"DIVIDE([Same_Month_Enrolls], [Leads], 0)",
    "2. Funnel Ratios", "0.0%");

AddMeasure(ft, "DS2DC%",
    @"DIVIDE([Demos_Completed], [Demos_Scheduled], 0)",
    "2. Funnel Ratios", "0.0%");

AddMeasure(ft, "Avg_Sale_Per_Enroll",
    @"DIVIDE([Revenue], [Enrolls], 0)",
    "2. Funnel Ratios", "₹#,##0");


// ── Section 3: Product Split ────────────────────────────────

AddMeasure(ft, "Enrolls_PG",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[sale_ind_pg] = ""PG""
)",
    "3. Product Split", "#,##0");

AddMeasure(ft, "Enrolls_Individual",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[sale_ind_pg] IN {""Individual Course"", ""Combined Individual""}
)",
    "3. Product Split", "#,##0");

AddMeasure(ft, "Revenue_PG",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    FinalTable[sale_ind_pg] = ""PG""
)",
    "3. Product Split", "₹#,##0");

AddMeasure(ft, "Revenue_Individual",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    FinalTable[sale_ind_pg] IN {""Individual Course"", ""Combined Individual""}
)",
    "3. Product Split", "₹#,##0");

AddMeasure(ft, "D2E%_PG",
    @"DIVIDE([Enrolls_PG], [Demos_Scheduled], 0)",
    "3. Product Split", "0.0%");


// ── Section 4: Lead Segment ─────────────────────────────────

AddMeasure(ft, "Leads_New",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[lead_segment] = ""New Lead""
)",
    "4. Lead Segment", "#,##0");

AddMeasure(ft, "Leads_Old_Capture",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[lead_segment] = ""Old Lead - Capture""
)",
    "4. Lead Segment", "#,##0");

AddMeasure(ft, "Enrolls_New",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[lead_segment] = ""New Lead""
)",
    "4. Lead Segment", "#,##0");

AddMeasure(ft, "Enrolls_Old_Capture",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[lead_segment] = ""Old Lead - Capture""
)",
    "4. Lead Segment", "#,##0");

AddMeasure(ft, "Enrolls_Old_Others",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[lead_segment] = ""Old - Others""
)",
    "4. Lead Segment", "#,##0");

AddMeasure(ft, "L2E%_New",
    @"DIVIDE([Enrolls_New], [Leads_New], 0)",
    "4. Lead Segment", "0.0%");

AddMeasure(ft, "L2E%_Old_Capture",
    @"DIVIDE([Enrolls_Old_Capture], [Leads_Old_Capture], 0)",
    "4. Lead Segment", "0.0%");


// ── Section 5: Enrollment Cohort Lag ────────────────────────

AddMeasure(ft, "Enrolls_M0",
    @"CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = ""M+0"")",
    "5. Enrollment Cohort", "#,##0");

AddMeasure(ft, "Enrolls_M1",
    @"CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = ""M+1"")",
    "5. Enrollment Cohort", "#,##0");

AddMeasure(ft, "Enrolls_M2",
    @"CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = ""M+2"")",
    "5. Enrollment Cohort", "#,##0");

AddMeasure(ft, "Enrolls_M3",
    @"CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = ""M+3"")",
    "5. Enrollment Cohort", "#,##0");

AddMeasure(ft, "Cumulative_Enrolls_M3",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Enroll_Month_Bucket_Capped] IN {""M+0"",""M+1"",""M+2"",""M+3""}
)",
    "5. Enrollment Cohort", "#,##0");

AddMeasure(ft, "Cumulative_L2E%_M3",
    @"DIVIDE([Cumulative_Enrolls_M3], [Leads], 0)",
    "5. Enrollment Cohort", "0.0%");


// ── Section 6: Assignment & Lead Allocation ─────────────────

AddMeasure(ft, "Leads_Assigned",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Assigned_This_Month] = 1
)",
    "6. Assignment", "#,##0");

AddMeasure(ft, "Leads_Assigned_First",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1
)",
    "6. Assignment", "#,##0");

AddMeasure(ft, "Leads_Assigned_New",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[assignment_type_month] = ""New""
)",
    "6. Assignment", "#,##0");

AddMeasure(ft, "Leads_Assigned_Others",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[assignment_type_month] = ""Others""
)",
    "6. Assignment", "#,##0");

AddMeasure(ft, "Assignment_Coverage%",
    @"DIVIDE([Leads_Assigned], [Leads], 0)",
    "6. Assignment", "0.0%");

AddMeasure(ft, "LA2E%",
    @"DIVIDE([Enrolls], [Leads_Assigned], 0)",
    "6. Assignment", "0.0%");


// ── Section 7: Star Rank & Quality Matching ─────────────────

AddMeasure(ft, "Leads_Assigned_FourStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[lead_star_rank_at_assign] = ""FourStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Leads_Assigned_ThreeStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[lead_star_rank_at_assign] = ""ThreeStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Leads_Assigned_TwoStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[lead_star_rank_at_assign] = ""TwoStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Leads_Assigned_OneStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[lead_star_rank_at_assign] = ""OneStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Star_Match_Count",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    FinalTable[Is_Star_Match] = 1
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Star_Match%",
    @"DIVIDE([Star_Match_Count], [Leads_Assigned_First], 0)",
    "7. Star Rank", "0.0%");

AddMeasure(ft, "Enrolls_FourStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[lead_star_rank_at_assign] = ""FourStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "Enrolls_ThreeStar",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[lead_star_rank_at_assign] = ""ThreeStar""
)",
    "7. Star Rank", "#,##0");

AddMeasure(ft, "L2E%_FourStar",
    @"DIVIDE([Enrolls_FourStar], [Leads_Assigned_FourStar], 0)",
    "7. Star Rank", "0.0%");

AddMeasure(ft, "L2E%_ThreeStar",
    @"DIVIDE([Enrolls_ThreeStar], [Leads_Assigned_ThreeStar], 0)",
    "7. Star Rank", "0.0%");

AddMeasure(ft, "Avg_P1_Score_At_Assign",
    @"CALCULATE(
    AVERAGE(FinalTable[p1_score_at_assign]),
    FinalTable[Is_First_Assignment_Per_Month] = 1
)",
    "7. Star Rank", "#,##0.0");

AddMeasure(ft, "Revenue_FourStar",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    FinalTable[lead_star_rank_at_assign] = ""FourStar""
)",
    "7. Star Rank", "₹#,##0");


// ── Section 8: BDA Performance ──────────────────────────────

AddMeasure(ft, "Leads_Per_BDA",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    NOT ISBLANK(FinalTable[bda_name])
)",
    "8. BDA Performance", "#,##0");

AddMeasure(ft, "Enrolls_Per_BDA",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    NOT ISBLANK(FinalTable[bda_name])
)",
    "8. BDA Performance", "#,##0");

AddMeasure(ft, "Revenue_Per_BDA",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    NOT ISBLANK(FinalTable[bda_name])
)",
    "8. BDA Performance", "₹#,##0");

AddMeasure(ft, "Active_BDAs",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[bda_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1
)",
    "8. BDA Performance", "#,##0");

AddMeasure(ft, "Avg_Enrolls_Per_BDA",
    @"DIVIDE([Enrolls_Per_BDA], [Active_BDAs], 0)",
    "8. BDA Performance", "#,##0.0");

AddMeasure(ft, "BDA_L2E%",
    @"DIVIDE([Enrolls_Per_BDA], [Leads_Per_BDA], 0)",
    "8. BDA Performance", "0.0%");


// ── Section 9: BDA Tier ─────────────────────────────────────

AddMeasure(ft, "Leads_by_Tier",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    NOT ISBLANK(FinalTable[bda_tier])
)",
    "9. BDA Tier", "#,##0");

AddMeasure(ft, "Enrolls_by_Tier",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    NOT ISBLANK(FinalTable[bda_tier])
)",
    "9. BDA Tier", "#,##0");

AddMeasure(ft, "Revenue_by_Tier",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    NOT ISBLANK(FinalTable[bda_tier])
)",
    "9. BDA Tier", "₹#,##0");

AddMeasure(ft, "L2E%_by_Tier",
    @"DIVIDE([Enrolls_by_Tier], [Leads_by_Tier], 0)",
    "9. BDA Tier", "0.0%");

AddMeasure(ft, "BDAs_per_Tier",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[bda_id]),
    FinalTable[Is_First_Assignment_Per_Month] = 1,
    NOT ISBLANK(FinalTable[bda_tier])
)",
    "9. BDA Tier", "#,##0");


// ── Section 10: Source Attribution ───────────────────────────

AddMeasure(ft, "Leads_by_Source",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    NOT ISBLANK(FinalTable[source_attribution_final])
)",
    "10. Source", "#,##0");

AddMeasure(ft, "Enrolls_by_Source",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    NOT ISBLANK(FinalTable[source_attribution_final])
)",
    "10. Source", "#,##0");

AddMeasure(ft, "L2E%_by_Source",
    @"DIVIDE([Enrolls_by_Source], [Leads_by_Source], 0)",
    "10. Source", "0.0%");


// ── Section 11: MoM Comparison ──────────────────────────────

AddMeasure(ft, "Leads_PM",
    @"CALCULATE([Leads], DATEADD(FinalTable[activity_month_start], -1, MONTH))",
    "11. MoM", "#,##0");

AddMeasure(ft, "Enrolls_PM",
    @"CALCULATE([Enrolls], DATEADD(FinalTable[activity_month_start], -1, MONTH))",
    "11. MoM", "#,##0");

AddMeasure(ft, "Revenue_PM",
    @"CALCULATE([Revenue], DATEADD(FinalTable[activity_month_start], -1, MONTH))",
    "11. MoM", "₹#,##0");

AddMeasure(ft, "Leads_MoM%",
    @"DIVIDE([Leads] - [Leads_PM], [Leads_PM], 0)",
    "11. MoM", "0.0%");

AddMeasure(ft, "Enrolls_MoM%",
    @"DIVIDE([Enrolls] - [Enrolls_PM], [Enrolls_PM], 0)",
    "11. MoM", "0.0%");

AddMeasure(ft, "Revenue_MoM%",
    @"DIVIDE([Revenue] - [Revenue_PM], [Revenue_PM], 0)",
    "11. MoM", "0.0%");


// ── Section 12: Domain / Program ────────────────────────────

AddMeasure(ft, "Leads_by_Domain",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    NOT ISBLANK(FinalTable[Domain_group])
)",
    "12. Domain", "#,##0");

AddMeasure(ft, "Enrolls_by_Domain",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    NOT ISBLANK(FinalTable[Domain_group])
)",
    "12. Domain", "#,##0");

AddMeasure(ft, "Enrolls_by_Program",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    NOT ISBLANK(FinalTable[sale_program])
)",
    "12. Domain", "#,##0");

AddMeasure(ft, "Revenue_by_Program",
    @"CALCULATE(
    SUM(FinalTable[sale_value]),
    NOT ISBLANK(FinalTable[sale_program])
)",
    "12. Domain", "₹#,##0");


// ── Section 13: Data Quality ────────────────────────────────

AddMeasure(ft, "System_Leads",
    @"CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_System_Activity] = 1)",
    "13. Data Quality", "#,##0");

AddMeasure(ft, "Total_Rows",
    @"COUNTROWS(FinalTable)",
    "13. Data Quality", "#,##0");

AddMeasure(ft, "Unique_Leads",
    @"DISTINCTCOUNT(FinalTable[lead_id])",
    "13. Data Quality", "#,##0");

AddMeasure(ft, "Latest_Activity_Date",
    @"MAX(FinalTable[created_at])",
    "13. Data Quality", null);


// ── Section 14: Customer Profile ────────────────────────────

AddMeasure(ft, "Leads_Job_Seeker",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[Customer_Profile] = ""JOB SEEKER""
)",
    "14. Customer Profile", "#,##0");

AddMeasure(ft, "Leads_Student",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[Customer_Profile] = ""STUDENT""
)",
    "14. Customer Profile", "#,##0");

AddMeasure(ft, "Leads_Working_Professional",
    @"CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = ""Lead Capture"",
    FinalTable[Customer_Profile] = ""WORKING PROFESSIONAL""
)",
    "14. Customer Profile", "#,##0");


// ── Section 15: KPI Cards ───────────────────────────────────

AddMeasure(ft, "KPI_Leads_MoM_Arrow",
    @"IF([Leads_MoM%] > 0, ""▲ "" & FORMAT([Leads_MoM%], ""0.0%""),
IF([Leads_MoM%] < 0, ""▼ "" & FORMAT([Leads_MoM%], ""0.0%""),
""─ 0.0%""))",
    "15. KPI Cards", null);

AddMeasure(ft, "KPI_Enrolls_MoM_Arrow",
    @"IF([Enrolls_MoM%] > 0, ""▲ "" & FORMAT([Enrolls_MoM%], ""0.0%""),
IF([Enrolls_MoM%] < 0, ""▼ "" & FORMAT([Enrolls_MoM%], ""0.0%""),
""─ 0.0%""))",
    "15. KPI Cards", null);


// =============================================================
// CALLDETAIL MEASURES
// =============================================================

// ── Core Calling ────────────────────────────────────────────

AddMeasure(cd, "Dials",
    @"CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1)",
    "1. Core Calling", "#,##0");

AddMeasure(cd, "Dialled_Leads",
    @"CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1)",
    "1. Core Calling", "#,##0");

AddMeasure(cd, "Connected_Leads",
    @"CALCULATE(
    DISTINCTCOUNT(CallDetail[lead_id]),
    CallDetail[Is_Valid_Call] = 1,
    CallDetail[Is_Connected_Call] = 1
)",
    "1. Core Calling", "#,##0");

AddMeasure(cd, "Connected_Calls",
    @"CALCULATE(
    COUNT(CallDetail[call_id]),
    CallDetail[Is_Valid_Call] = 1,
    CallDetail[Is_Connected_Call] = 1
)",
    "1. Core Calling", "#,##0");

AddMeasure(cd, "DNP_Leads",
    @"CALCULATE(
    DISTINCTCOUNT(CallDetail[lead_id]),
    CallDetail[Is_Valid_Call] = 1,
    CallDetail[Is_DNP_Call] = 1
)",
    "1. Core Calling", "#,##0");

AddMeasure(cd, "DNP_Calls",
    @"CALCULATE(
    COUNT(CallDetail[call_id]),
    CallDetail[Is_Valid_Call] = 1,
    CallDetail[Is_DNP_Call] = 1
)",
    "1. Core Calling", "#,##0");


// ── Calling Ratios ──────────────────────────────────────────

AddMeasure(cd, "Connectivity%",
    @"DIVIDE([Connected_Leads], [Dialled_Leads], 0)",
    "2. Calling Ratios", "0.0%");

AddMeasure(cd, "DNP_Rate",
    @"DIVIDE([DNP_Leads], [Dialled_Leads], 0)",
    "2. Calling Ratios", "0.0%");

AddMeasure(cd, "CC_per_Lead",
    @"DIVIDE([Connected_Calls], [Connected_Leads], 0)",
    "2. Calling Ratios", "#,##0.0");

AddMeasure(cd, "Dials_per_Lead",
    @"DIVIDE([Dials], [Dialled_Leads], 0)",
    "2. Calling Ratios", "#,##0.0");


// ── Duration ────────────────────────────────────────────────

AddMeasure(cd, "Avg_Call_Duration_Sec",
    @"CALCULATE(
    AVERAGE(CallDetail[call_duration_sec]),
    CallDetail[Is_Valid_Call] = 1,
    CallDetail[Is_Connected_Call] = 1
)",
    "3. Duration", "#,##0");

AddMeasure(cd, "Avg_Call_Duration_Formatted",
    @"VAR secs = [Avg_Call_Duration_Sec]
RETURN
    IF(ISBLANK(secs), ""-"",
    FORMAT(INT(secs / 60), ""0"") & "":"" & FORMAT(MOD(INT(secs), 60), ""00""))",
    "3. Duration", null);

AddMeasure(cd, "Quality_Call%",
    @"DIVIDE(
    CALCULATE(
        COUNT(CallDetail[call_id]),
        CallDetail[Is_Valid_Call] = 1,
        CallDetail[Is_Connected_Call] = 1,
        CallDetail[call_duration_sec] > 60
    ),
    [Connected_Calls],
    0
)",
    "3. Duration", "0.0%");


// ── BDA Calling Performance ─────────────────────────────────

AddMeasure(cd, "Active_Calling_BDAs",
    @"CALCULATE(DISTINCTCOUNT(CallDetail[se_user_id]), CallDetail[Is_Valid_Call] = 1)",
    "4. BDA Calling", "#,##0");

AddMeasure(cd, "Dials_per_BDA",
    @"DIVIDE([Dials], [Active_Calling_BDAs], 0)",
    "4. BDA Calling", "#,##0.0");

AddMeasure(cd, "Connected_per_BDA",
    @"DIVIDE([Connected_Calls], [Active_Calling_BDAs], 0)",
    "4. BDA Calling", "#,##0.0");

AddMeasure(cd, "Dialled_Leads_per_BDA",
    @"DIVIDE([Dialled_Leads], [Active_Calling_BDAs], 0)",
    "4. BDA Calling", "#,##0.0");


// ── Manual vs Auto ──────────────────────────────────────────

AddMeasure(cd, "Dials_Manual",
    @"CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = TRUE())",
    "5. Manual vs Auto", "#,##0");

AddMeasure(cd, "Dials_Auto",
    @"CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = FALSE())",
    "5. Manual vs Auto", "#,##0");

AddMeasure(cd, "Manual_Call%",
    @"DIVIDE([Dials_Manual], [Dials], 0)",
    "5. Manual vs Auto", "0.0%");


// ── MoM Calling ─────────────────────────────────────────────

AddMeasure(cd, "Dials_PM",
    @"CALCULATE([Dials], DATEADD(CallDetail[call_month_start], -1, MONTH))",
    "6. MoM Calling", "#,##0");

AddMeasure(cd, "Connected_Leads_PM",
    @"CALCULATE([Connected_Leads], DATEADD(CallDetail[call_month_start], -1, MONTH))",
    "6. MoM Calling", "#,##0");

AddMeasure(cd, "Dials_MoM%",
    @"DIVIDE([Dials] - [Dials_PM], [Dials_PM], 0)",
    "6. MoM Calling", "0.0%");


// ── KPI Cards ───────────────────────────────────────────────

AddMeasure(cd, "KPI_Dials_MoM_Arrow",
    @"IF([Dials_MoM%] > 0, ""▲ "" & FORMAT([Dials_MoM%], ""0.0%""),
IF([Dials_MoM%] < 0, ""▼ "" & FORMAT([Dials_MoM%], ""0.0%""),
""─ 0.0%""))",
    "7. KPI Cards", null);
