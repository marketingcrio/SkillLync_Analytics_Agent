# ============================================================
# Fabric Notebook — Bulk Create ALL DAX Measures via TMSL
# ============================================================
# HOW TO USE:
# 1. Fabric portal → New → Notebook
# 2. Paste this into Cell 1 → Run
# 3. All 100+ measures created in one shot
#
# UPDATE the dataset name below before running!
# ============================================================

import sempy.fabric as fabric
import json

# ── UPDATE THIS ──────────────────────────────────────────────
DATASET_NAME = "Skill-Lync-Master-Report"   # <── your semantic model name
# ─────────────────────────────────────────────────────────────

# ── Measure definitions ──────────────────────────────────────

measures = {
    "FinalTable": [

        # ── 1. Core Funnel ───────────────────────────────────
        {
            "name": "Leads",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Webinar_Scheduled",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Demo Scheduled")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Tech_Scheduled",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "SE Marked Demo Schedule")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Scheduled",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] IN {"Demo Scheduled", "SE Marked Demo Schedule"})',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Webinar_Completed",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Demo Completed - Webinars")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Tech_Completed",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "SE Marked Demo Completed")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Demos_Completed",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] IN {"Demo Completed - Webinars", "SE Marked Demo Completed"})',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Enrolls",
            "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1)",
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Same_Month_Enrolls",
            "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[SameMonthEnrolls] = "Enrolls")',
            "displayFolder": "1. Core Funnel",
            "formatString": "#,##0"
        },
        {
            "name": "Revenue",
            "expression": "SUM(FinalTable[sale_value])",
            "displayFolder": "1. Core Funnel",
            "formatString": "₹#,##0"
        },

        # ── 2. Funnel Ratios ─────────────────────────────────
        {"name": "L2D%", "expression": "DIVIDE([Demos_Scheduled], [Leads], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "0.0%"},
        {"name": "L2E%", "expression": "DIVIDE([Enrolls], [Leads], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "0.0%"},
        {"name": "D2E%", "expression": "DIVIDE([Enrolls], [Demos_Scheduled], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "0.0%"},
        {"name": "SM_L2E%", "expression": "DIVIDE([Same_Month_Enrolls], [Leads], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "0.0%"},
        {"name": "DS2DC%", "expression": "DIVIDE([Demos_Completed], [Demos_Scheduled], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "0.0%"},
        {"name": "Avg_Sale_Per_Enroll", "expression": "DIVIDE([Revenue], [Enrolls], 0)", "displayFolder": "2. Funnel Ratios", "formatString": "₹#,##0"},

        # ── 3. Product Split ─────────────────────────────────
        {"name": "Enrolls_PG", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[sale_ind_pg] = "PG")', "displayFolder": "3. Product Split", "formatString": "#,##0"},
        {"name": "Enrolls_Individual", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"})', "displayFolder": "3. Product Split", "formatString": "#,##0"},
        {"name": "Revenue_PG", "expression": 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] = "PG")', "displayFolder": "3. Product Split", "formatString": "₹#,##0"},
        {"name": "Revenue_Individual", "expression": 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"})', "displayFolder": "3. Product Split", "formatString": "₹#,##0"},

        # ── 4. Lead Segment ──────────────────────────────────
        {"name": "Leads_New", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "New Lead")', "displayFolder": "4. Lead Segment", "formatString": "#,##0"},
        {"name": "Leads_Old_Capture", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "Old Lead - Capture")', "displayFolder": "4. Lead Segment", "formatString": "#,##0"},
        {"name": "Enrolls_New", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "New Lead")', "displayFolder": "4. Lead Segment", "formatString": "#,##0"},
        {"name": "Enrolls_Old_Capture", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old Lead - Capture")', "displayFolder": "4. Lead Segment", "formatString": "#,##0"},
        {"name": "Enrolls_Old_Others", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old - Others")', "displayFolder": "4. Lead Segment", "formatString": "#,##0"},
        {"name": "L2E%_New", "expression": "DIVIDE([Enrolls_New], [Leads_New], 0)", "displayFolder": "4. Lead Segment", "formatString": "0.0%"},
        {"name": "L2E%_Old_Capture", "expression": "DIVIDE([Enrolls_Old_Capture], [Leads_Old_Capture], 0)", "displayFolder": "4. Lead Segment", "formatString": "0.0%"},

        # ── 5. Enrollment Cohort ─────────────────────────────
        {"name": "Enrolls_M0", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+0")', "displayFolder": "5. Enrollment Cohort", "formatString": "#,##0"},
        {"name": "Enrolls_M1", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+1")', "displayFolder": "5. Enrollment Cohort", "formatString": "#,##0"},
        {"name": "Enrolls_M2", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+2")', "displayFolder": "5. Enrollment Cohort", "formatString": "#,##0"},
        {"name": "Enrolls_M3", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+3")', "displayFolder": "5. Enrollment Cohort", "formatString": "#,##0"},
        {"name": "Cumulative_Enrolls_M3", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] IN {"M+0","M+1","M+2","M+3"})', "displayFolder": "5. Enrollment Cohort", "formatString": "#,##0"},
        {"name": "Cumulative_L2E%_M3", "expression": "DIVIDE([Cumulative_Enrolls_M3], [Leads], 0)", "displayFolder": "5. Enrollment Cohort", "formatString": "0.0%"},

        # ── 6. Assignment ────────────────────────────────────
        {"name": "Leads_Assigned", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Assigned_This_Month] = 1)", "displayFolder": "6. Assignment", "formatString": "#,##0"},
        {"name": "Leads_Assigned_First", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)", "displayFolder": "6. Assignment", "formatString": "#,##0"},
        {"name": "Leads_Assigned_New", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "New")', "displayFolder": "6. Assignment", "formatString": "#,##0"},
        {"name": "Leads_Assigned_Others", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "Others")', "displayFolder": "6. Assignment", "formatString": "#,##0"},
        {"name": "Assignment_Coverage%", "expression": "DIVIDE([Leads_Assigned], [Leads], 0)", "displayFolder": "6. Assignment", "formatString": "0.0%"},
        {"name": "LA2E%", "expression": "DIVIDE([Enrolls], [Leads_Assigned], 0)", "displayFolder": "6. Assignment", "formatString": "0.0%"},

        # ── 7. Star Rank ─────────────────────────────────────
        {"name": "Leads_Assigned_FourStar", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "FourStar")', "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "Leads_Assigned_ThreeStar", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "ThreeStar")', "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "Leads_Assigned_TwoStar", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "TwoStar")', "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "Leads_Assigned_OneStar", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "OneStar")', "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "Star_Match_Count", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[Is_Star_Match] = 1)", "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "Star_Match%", "expression": "DIVIDE([Star_Match_Count], [Leads_Assigned_First], 0)", "displayFolder": "7. Star Rank", "formatString": "0.0%"},
        {"name": "Enrolls_FourStar", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_star_rank_at_assign] = "FourStar")', "displayFolder": "7. Star Rank", "formatString": "#,##0"},
        {"name": "L2E%_FourStar", "expression": "DIVIDE([Enrolls_FourStar], [Leads_Assigned_FourStar], 0)", "displayFolder": "7. Star Rank", "formatString": "0.0%"},
        {"name": "Avg_P1_Score_At_Assign", "expression": "CALCULATE(AVERAGE(FinalTable[p1_score_at_assign]), FinalTable[Is_First_Assignment_Per_Month] = 1)", "displayFolder": "7. Star Rank", "formatString": "#,##0.0"},
        {"name": "Revenue_FourStar", "expression": 'CALCULATE(SUM(FinalTable[sale_value]), FinalTable[lead_star_rank_at_assign] = "FourStar")', "displayFolder": "7. Star Rank", "formatString": "₹#,##0"},

        # ── 8. BDA Performance ───────────────────────────────
        {"name": "Leads_Per_BDA", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_name]))', "displayFolder": "8. BDA Performance", "formatString": "#,##0"},
        {"name": "Enrolls_Per_BDA", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_name]))", "displayFolder": "8. BDA Performance", "formatString": "#,##0"},
        {"name": "Revenue_Per_BDA", "expression": "CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[bda_name]))", "displayFolder": "8. BDA Performance", "formatString": "₹#,##0"},
        {"name": "Active_BDAs", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[bda_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)", "displayFolder": "8. BDA Performance", "formatString": "#,##0"},
        {"name": "Avg_Enrolls_Per_BDA", "expression": "DIVIDE([Enrolls_Per_BDA], [Active_BDAs], 0)", "displayFolder": "8. BDA Performance", "formatString": "#,##0.0"},
        {"name": "BDA_L2E%", "expression": "DIVIDE([Enrolls_Per_BDA], [Leads_Per_BDA], 0)", "displayFolder": "8. BDA Performance", "formatString": "0.0%"},

        # ── 9. BDA Tier ──────────────────────────────────────
        {"name": "Leads_by_Tier", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_tier]))', "displayFolder": "9. BDA Tier", "formatString": "#,##0"},
        {"name": "Enrolls_by_Tier", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_tier]))", "displayFolder": "9. BDA Tier", "formatString": "#,##0"},
        {"name": "Revenue_by_Tier", "expression": "CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[bda_tier]))", "displayFolder": "9. BDA Tier", "formatString": "₹#,##0"},
        {"name": "L2E%_by_Tier", "expression": "DIVIDE([Enrolls_by_Tier], [Leads_by_Tier], 0)", "displayFolder": "9. BDA Tier", "formatString": "0.0%"},
        {"name": "BDAs_per_Tier", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[bda_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, NOT ISBLANK(FinalTable[bda_tier]))", "displayFolder": "9. BDA Tier", "formatString": "#,##0"},

        # ── 10. Source ───────────────────────────────────────
        {"name": "Leads_by_Source", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[source_attribution_final]))', "displayFolder": "10. Source", "formatString": "#,##0"},
        {"name": "Enrolls_by_Source", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[source_attribution_final]))", "displayFolder": "10. Source", "formatString": "#,##0"},
        {"name": "L2E%_by_Source", "expression": "DIVIDE([Enrolls_by_Source], [Leads_by_Source], 0)", "displayFolder": "10. Source", "formatString": "0.0%"},

        # ── 11. MoM ──────────────────────────────────────────
        {"name": "Leads_PM", "expression": "CALCULATE([Leads], DATEADD(FinalTable[activity_month_start], -1, MONTH))", "displayFolder": "11. MoM", "formatString": "#,##0"},
        {"name": "Enrolls_PM", "expression": "CALCULATE([Enrolls], DATEADD(FinalTable[activity_month_start], -1, MONTH))", "displayFolder": "11. MoM", "formatString": "#,##0"},
        {"name": "Revenue_PM", "expression": "CALCULATE([Revenue], DATEADD(FinalTable[activity_month_start], -1, MONTH))", "displayFolder": "11. MoM", "formatString": "₹#,##0"},
        {"name": "Leads_MoM%", "expression": "DIVIDE([Leads] - [Leads_PM], [Leads_PM], 0)", "displayFolder": "11. MoM", "formatString": "0.0%"},
        {"name": "Enrolls_MoM%", "expression": "DIVIDE([Enrolls] - [Enrolls_PM], [Enrolls_PM], 0)", "displayFolder": "11. MoM", "formatString": "0.0%"},
        {"name": "Revenue_MoM%", "expression": "DIVIDE([Revenue] - [Revenue_PM], [Revenue_PM], 0)", "displayFolder": "11. MoM", "formatString": "0.0%"},

        # ── 12. Domain ───────────────────────────────────────
        {"name": "Leads_by_Domain", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[Domain_group]))', "displayFolder": "12. Domain", "formatString": "#,##0"},
        {"name": "Enrolls_by_Domain", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[Domain_group]))", "displayFolder": "12. Domain", "formatString": "#,##0"},
        {"name": "Enrolls_by_Program", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[sale_program]))", "displayFolder": "12. Domain", "formatString": "#,##0"},
        {"name": "Revenue_by_Program", "expression": "CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[sale_program]))", "displayFolder": "12. Domain", "formatString": "₹#,##0"},

        # ── 13. Data Quality ─────────────────────────────────
        {"name": "System_Leads", "expression": "CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_System_Activity] = 1)", "displayFolder": "13. Data Quality", "formatString": "#,##0"},
        {"name": "Total_Rows", "expression": "COUNTROWS(FinalTable)", "displayFolder": "13. Data Quality", "formatString": "#,##0"},
        {"name": "Unique_Leads", "expression": "DISTINCTCOUNT(FinalTable[lead_id])", "displayFolder": "13. Data Quality", "formatString": "#,##0"},
        {"name": "Latest_Activity_Date", "expression": "MAX(FinalTable[created_at])", "displayFolder": "13. Data Quality"},

        # ── 14. Customer Profile ─────────────────────────────
        {"name": "Leads_Job_Seeker", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "JOB SEEKER")', "displayFolder": "14. Customer Profile", "formatString": "#,##0"},
        {"name": "Leads_Student", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "STUDENT")', "displayFolder": "14. Customer Profile", "formatString": "#,##0"},
        {"name": "Leads_Working_Professional", "expression": 'CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "WORKING PROFESSIONAL")', "displayFolder": "14. Customer Profile", "formatString": "#,##0"},

        # ── 15. KPI Cards ────────────────────────────────────
        {"name": "KPI_Leads_MoM_Arrow", "expression": 'IF([Leads_MoM%] > 0, "▲ " & FORMAT([Leads_MoM%], "0.0%"), IF([Leads_MoM%] < 0, "▼ " & FORMAT([Leads_MoM%], "0.0%"), "─ 0.0%"))', "displayFolder": "15. KPI Cards"},
        {"name": "KPI_Enrolls_MoM_Arrow", "expression": 'IF([Enrolls_MoM%] > 0, "▲ " & FORMAT([Enrolls_MoM%], "0.0%"), IF([Enrolls_MoM%] < 0, "▼ " & FORMAT([Enrolls_MoM%], "0.0%"), "─ 0.0%"))', "displayFolder": "15. KPI Cards"},
    ],

    "CallDetail": [
        # ── 1. Core Calling ──────────────────────────────────
        {"name": "Dials", "expression": "CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},
        {"name": "Dialled_Leads", "expression": "CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},
        {"name": "Connected_Leads", "expression": "CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},
        {"name": "Connected_Calls", "expression": "CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},
        {"name": "DNP_Leads", "expression": "CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},
        {"name": "DNP_Calls", "expression": "CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)", "displayFolder": "1. Core Calling", "formatString": "#,##0"},

        # ── 2. Calling Ratios ────────────────────────────────
        {"name": "Connectivity%", "expression": "DIVIDE([Connected_Leads], [Dialled_Leads], 0)", "displayFolder": "2. Calling Ratios", "formatString": "0.0%"},
        {"name": "DNP_Rate", "expression": "DIVIDE([DNP_Leads], [Dialled_Leads], 0)", "displayFolder": "2. Calling Ratios", "formatString": "0.0%"},
        {"name": "CC_per_Lead", "expression": "DIVIDE([Connected_Calls], [Connected_Leads], 0)", "displayFolder": "2. Calling Ratios", "formatString": "#,##0.0"},
        {"name": "Dials_per_Lead", "expression": "DIVIDE([Dials], [Dialled_Leads], 0)", "displayFolder": "2. Calling Ratios", "formatString": "#,##0.0"},

        # ── 3. Duration ──────────────────────────────────────
        {"name": "Avg_Call_Duration_Sec", "expression": "CALCULATE(AVERAGE(CallDetail[call_duration_sec]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)", "displayFolder": "3. Duration", "formatString": "#,##0"},
        {"name": "Avg_Call_Duration_Formatted", "expression": 'VAR secs = [Avg_Call_Duration_Sec] RETURN IF(ISBLANK(secs), "-", FORMAT(INT(secs / 60), "0") & ":" & FORMAT(MOD(INT(secs), 60), "00"))', "displayFolder": "3. Duration"},
        {"name": "Quality_Call%", "expression": "DIVIDE(CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, CallDetail[call_duration_sec] > 60), [Connected_Calls], 0)", "displayFolder": "3. Duration", "formatString": "0.0%"},

        # ── 4. BDA Calling ───────────────────────────────────
        {"name": "Active_Calling_BDAs", "expression": "CALCULATE(DISTINCTCOUNT(CallDetail[se_user_id]), CallDetail[Is_Valid_Call] = 1)", "displayFolder": "4. BDA Calling", "formatString": "#,##0"},
        {"name": "Dials_per_BDA", "expression": "DIVIDE([Dials], [Active_Calling_BDAs], 0)", "displayFolder": "4. BDA Calling", "formatString": "#,##0.0"},
        {"name": "Connected_per_BDA", "expression": "DIVIDE([Connected_Calls], [Active_Calling_BDAs], 0)", "displayFolder": "4. BDA Calling", "formatString": "#,##0.0"},

        # ── 5. Manual vs Auto ────────────────────────────────
        {"name": "Dials_Manual", "expression": "CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = TRUE())", "displayFolder": "5. Manual vs Auto", "formatString": "#,##0"},
        {"name": "Dials_Auto", "expression": "CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = FALSE())", "displayFolder": "5. Manual vs Auto", "formatString": "#,##0"},
        {"name": "Manual_Call%", "expression": "DIVIDE([Dials_Manual], [Dials], 0)", "displayFolder": "5. Manual vs Auto", "formatString": "0.0%"},

        # ── 6. MoM Calling ───────────────────────────────────
        {"name": "Dials_PM", "expression": "CALCULATE([Dials], DATEADD(CallDetail[call_month_start], -1, MONTH))", "displayFolder": "6. MoM Calling", "formatString": "#,##0"},
        {"name": "Dials_MoM%", "expression": "DIVIDE([Dials] - [Dials_PM], [Dials_PM], 0)", "displayFolder": "6. MoM Calling", "formatString": "0.0%"},
    ]
}


# =============================================================
# BUILD TMSL & EXECUTE
# =============================================================

for table_name, table_measures in measures.items():
    for m in table_measures:
        tmsl = {
            "createOrReplace": {
                "object": {
                    "database": DATASET_NAME,
                    "table": table_name,
                    "measure": m["name"]
                },
                "measure": {
                    "name": m["name"],
                    "expression": m["expression"],
                    "displayFolder": m.get("displayFolder", ""),
                }
            }
        }
        if "formatString" in m and m["formatString"]:
            tmsl["createOrReplace"]["measure"]["formatString"] = m["formatString"]

        try:
            fabric.execute_tmsl(DATASET_NAME, json.dumps(tmsl))
            print(f"  ✅ [{table_name}] {m['name']}")
        except Exception as e:
            print(f"  ❌ [{table_name}] {m['name']} — {str(e)[:100]}")

print(f"\nDone! {sum(len(v) for v in measures.values())} measures processed.")
