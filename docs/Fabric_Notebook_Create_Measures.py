"""
Fabric Notebook — Bulk Create DAX Measures via Semantic Link (sempy)
====================================================================
HOW TO USE:
1. In Fabric portal → New → Notebook
2. Attach to your Lakehouse/Warehouse
3. Paste this entire script into a cell
4. Update DATASET_NAME to match your semantic model name
5. Run the cell — all measures are created at once

Prerequisites:
- pip install semantic-link (pre-installed in Fabric notebooks)
- Semantic model must exist in the same workspace
"""

import sempy.fabric as fabric

# ── UPDATE THIS ──────────────────────────────────────────────
DATASET_NAME = "Skill-Lync-Master-Report"  # Your semantic model name
# ─────────────────────────────────────────────────────────────

# Helper to define measures
measures = []

def add(table, name, expression, folder="", fmt=None):
    measures.append({
        "table": table,
        "name": name,
        "expression": expression,
        "folder": folder,
        "format": fmt
    })

# =============================================================
# FINALTABLE MEASURES
# =============================================================

# ── 1. Core Funnel ───────────────────────────────────────────

add("FinalTable", "Leads", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "Lead Capture"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Webinar_Scheduled", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "Demo Scheduled"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Tech_Scheduled", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "SE Marked Demo Schedule"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Scheduled", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] IN {
        "Demo Scheduled", "SE Marked Demo Schedule"
    }
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Webinar_Completed", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "Demo Completed - Webinars"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Tech_Completed", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "SE Marked Demo Completed"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Demos_Completed", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] IN {
        "Demo Completed - Webinars", "SE Marked Demo Completed"
    }
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Enrolls", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Same_Month_Enrolls", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[activity_type_category] = "Lead Capture",
    FinalTable[SameMonthEnrolls] = "Enrolls"
)""", "1. Core Funnel", "#,##0")

add("FinalTable", "Revenue", """SUM(FinalTable[sale_value])""", "1. Core Funnel", "₹#,##0")

# ── 2. Funnel Ratios ────────────────────────────────────────

add("FinalTable", "L2D%", """DIVIDE([Demos_Scheduled], [Leads], 0)""", "2. Funnel Ratios", "0.0%")
add("FinalTable", "L2E%", """DIVIDE([Enrolls], [Leads], 0)""", "2. Funnel Ratios", "0.0%")
add("FinalTable", "D2E%", """DIVIDE([Enrolls], [Demos_Scheduled], 0)""", "2. Funnel Ratios", "0.0%")
add("FinalTable", "SM_L2E%", """DIVIDE([Same_Month_Enrolls], [Leads], 0)""", "2. Funnel Ratios", "0.0%")
add("FinalTable", "DS2DC%", """DIVIDE([Demos_Completed], [Demos_Scheduled], 0)""", "2. Funnel Ratios", "0.0%")
add("FinalTable", "Avg_Sale_Per_Enroll", """DIVIDE([Revenue], [Enrolls], 0)""", "2. Funnel Ratios", "₹#,##0")

# ── 3. Product Split ────────────────────────────────────────

add("FinalTable", "Enrolls_PG", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[sale_ind_pg] = "PG"
)""", "3. Product Split", "#,##0")

add("FinalTable", "Enrolls_Individual", """
CALCULATE(
    DISTINCTCOUNT(FinalTable[lead_id]),
    FinalTable[Is_Valid_Enroll] = 1,
    FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"}
)""", "3. Product Split", "#,##0")

add("FinalTable", "Revenue_PG", """
CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] = "PG")
""", "3. Product Split", "₹#,##0")

add("FinalTable", "Revenue_Individual", """
CALCULATE(SUM(FinalTable[sale_value]), FinalTable[sale_ind_pg] IN {"Individual Course", "Combined Individual"})
""", "3. Product Split", "₹#,##0")

# ── 4. Lead Segment ─────────────────────────────────────────

add("FinalTable", "Leads_New", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "New Lead")
""", "4. Lead Segment", "#,##0")

add("FinalTable", "Leads_Old_Capture", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[lead_segment] = "Old Lead - Capture")
""", "4. Lead Segment", "#,##0")

add("FinalTable", "Enrolls_New", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "New Lead")
""", "4. Lead Segment", "#,##0")

add("FinalTable", "Enrolls_Old_Capture", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old Lead - Capture")
""", "4. Lead Segment", "#,##0")

add("FinalTable", "Enrolls_Old_Others", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_segment] = "Old - Others")
""", "4. Lead Segment", "#,##0")

add("FinalTable", "L2E%_New", """DIVIDE([Enrolls_New], [Leads_New], 0)""", "4. Lead Segment", "0.0%")
add("FinalTable", "L2E%_Old_Capture", """DIVIDE([Enrolls_Old_Capture], [Leads_Old_Capture], 0)""", "4. Lead Segment", "0.0%")

# ── 5. Enrollment Cohort Lag ─────────────────────────────────

for i in range(4):
    add("FinalTable", f"Enrolls_M{i}", f"""
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] = "M+{i}")
""", "5. Enrollment Cohort", "#,##0")

add("FinalTable", "Cumulative_Enrolls_M3", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Enroll_Month_Bucket_Capped] IN {"M+0","M+1","M+2","M+3"})
""", "5. Enrollment Cohort", "#,##0")

add("FinalTable", "Cumulative_L2E%_M3", """DIVIDE([Cumulative_Enrolls_M3], [Leads], 0)""", "5. Enrollment Cohort", "0.0%")

# ── 6. Assignment ────────────────────────────────────────────

add("FinalTable", "Leads_Assigned", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Assigned_This_Month] = 1)
""", "6. Assignment", "#,##0")

add("FinalTable", "Leads_Assigned_First", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)
""", "6. Assignment", "#,##0")

add("FinalTable", "Leads_Assigned_New", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "New")
""", "6. Assignment", "#,##0")

add("FinalTable", "Leads_Assigned_Others", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[assignment_type_month] = "Others")
""", "6. Assignment", "#,##0")

add("FinalTable", "Assignment_Coverage%", """DIVIDE([Leads_Assigned], [Leads], 0)""", "6. Assignment", "0.0%")
add("FinalTable", "LA2E%", """DIVIDE([Enrolls], [Leads_Assigned], 0)""", "6. Assignment", "0.0%")

# ── 7. Star Rank ─────────────────────────────────────────────

for rank in ["FourStar", "ThreeStar", "TwoStar", "OneStar"]:
    add("FinalTable", f"Leads_Assigned_{rank}", f"""
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[lead_star_rank_at_assign] = "{rank}")
""", "7. Star Rank", "#,##0")

add("FinalTable", "Star_Match_Count", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, FinalTable[Is_Star_Match] = 1)
""", "7. Star Rank", "#,##0")

add("FinalTable", "Star_Match%", """DIVIDE([Star_Match_Count], [Leads_Assigned_First], 0)""", "7. Star Rank", "0.0%")

add("FinalTable", "Enrolls_FourStar", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_star_rank_at_assign] = "FourStar")
""", "7. Star Rank", "#,##0")

add("FinalTable", "Enrolls_ThreeStar", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, FinalTable[lead_star_rank_at_assign] = "ThreeStar")
""", "7. Star Rank", "#,##0")

add("FinalTable", "L2E%_FourStar", """DIVIDE([Enrolls_FourStar], [Leads_Assigned_FourStar], 0)""", "7. Star Rank", "0.0%")
add("FinalTable", "L2E%_ThreeStar", """DIVIDE([Enrolls_ThreeStar], [Leads_Assigned_ThreeStar], 0)""", "7. Star Rank", "0.0%")

add("FinalTable", "Avg_P1_Score_At_Assign", """
CALCULATE(AVERAGE(FinalTable[p1_score_at_assign]), FinalTable[Is_First_Assignment_Per_Month] = 1)
""", "7. Star Rank", "#,##0.0")

add("FinalTable", "Revenue_FourStar", """
CALCULATE(SUM(FinalTable[sale_value]), FinalTable[lead_star_rank_at_assign] = "FourStar")
""", "7. Star Rank", "₹#,##0")

# ── 8. BDA Performance ──────────────────────────────────────

add("FinalTable", "Leads_Per_BDA", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_name]))
""", "8. BDA Performance", "#,##0")

add("FinalTable", "Enrolls_Per_BDA", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_name]))
""", "8. BDA Performance", "#,##0")

add("FinalTable", "Revenue_Per_BDA", """
CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[bda_name]))
""", "8. BDA Performance", "₹#,##0")

add("FinalTable", "Active_BDAs", """
CALCULATE(DISTINCTCOUNT(FinalTable[bda_id]), FinalTable[Is_First_Assignment_Per_Month] = 1)
""", "8. BDA Performance", "#,##0")

add("FinalTable", "Avg_Enrolls_Per_BDA", """DIVIDE([Enrolls_Per_BDA], [Active_BDAs], 0)""", "8. BDA Performance", "#,##0.0")
add("FinalTable", "BDA_L2E%", """DIVIDE([Enrolls_Per_BDA], [Leads_Per_BDA], 0)""", "8. BDA Performance", "0.0%")

# ── 9. BDA Tier ──────────────────────────────────────────────

add("FinalTable", "Leads_by_Tier", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[bda_tier]))
""", "9. BDA Tier", "#,##0")

add("FinalTable", "Enrolls_by_Tier", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[bda_tier]))
""", "9. BDA Tier", "#,##0")

add("FinalTable", "Revenue_by_Tier", """
CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[bda_tier]))
""", "9. BDA Tier", "₹#,##0")

add("FinalTable", "L2E%_by_Tier", """DIVIDE([Enrolls_by_Tier], [Leads_by_Tier], 0)""", "9. BDA Tier", "0.0%")

add("FinalTable", "BDAs_per_Tier", """
CALCULATE(DISTINCTCOUNT(FinalTable[bda_id]), FinalTable[Is_First_Assignment_Per_Month] = 1, NOT ISBLANK(FinalTable[bda_tier]))
""", "9. BDA Tier", "#,##0")

# ── 10. Source ───────────────────────────────────────────────

add("FinalTable", "Leads_by_Source", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[source_attribution_final]))
""", "10. Source", "#,##0")

add("FinalTable", "Enrolls_by_Source", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[source_attribution_final]))
""", "10. Source", "#,##0")

add("FinalTable", "L2E%_by_Source", """DIVIDE([Enrolls_by_Source], [Leads_by_Source], 0)""", "10. Source", "0.0%")

# ── 11. MoM ──────────────────────────────────────────────────

add("FinalTable", "Leads_PM", """CALCULATE([Leads], DATEADD(FinalTable[activity_month_start], -1, MONTH))""", "11. MoM", "#,##0")
add("FinalTable", "Enrolls_PM", """CALCULATE([Enrolls], DATEADD(FinalTable[activity_month_start], -1, MONTH))""", "11. MoM", "#,##0")
add("FinalTable", "Revenue_PM", """CALCULATE([Revenue], DATEADD(FinalTable[activity_month_start], -1, MONTH))""", "11. MoM", "₹#,##0")
add("FinalTable", "Leads_MoM%", """DIVIDE([Leads] - [Leads_PM], [Leads_PM], 0)""", "11. MoM", "0.0%")
add("FinalTable", "Enrolls_MoM%", """DIVIDE([Enrolls] - [Enrolls_PM], [Enrolls_PM], 0)""", "11. MoM", "0.0%")
add("FinalTable", "Revenue_MoM%", """DIVIDE([Revenue] - [Revenue_PM], [Revenue_PM], 0)""", "11. MoM", "0.0%")

# ── 12. Domain ───────────────────────────────────────────────

add("FinalTable", "Leads_by_Domain", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", NOT ISBLANK(FinalTable[Domain_group]))
""", "12. Domain", "#,##0")

add("FinalTable", "Enrolls_by_Domain", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[Domain_group]))
""", "12. Domain", "#,##0")

add("FinalTable", "Enrolls_by_Program", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_Valid_Enroll] = 1, NOT ISBLANK(FinalTable[sale_program]))
""", "12. Domain", "#,##0")

add("FinalTable", "Revenue_by_Program", """
CALCULATE(SUM(FinalTable[sale_value]), NOT ISBLANK(FinalTable[sale_program]))
""", "12. Domain", "₹#,##0")

# ── 13. Data Quality ────────────────────────────────────────

add("FinalTable", "System_Leads", """CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[Is_System_Activity] = 1)""", "13. Data Quality", "#,##0")
add("FinalTable", "Total_Rows", """COUNTROWS(FinalTable)""", "13. Data Quality", "#,##0")
add("FinalTable", "Unique_Leads", """DISTINCTCOUNT(FinalTable[lead_id])""", "13. Data Quality", "#,##0")
add("FinalTable", "Latest_Activity_Date", """MAX(FinalTable[created_at])""", "13. Data Quality", None)

# ── 14. Customer Profile ────────────────────────────────────

add("FinalTable", "Leads_Job_Seeker", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "JOB SEEKER")
""", "14. Customer Profile", "#,##0")

add("FinalTable", "Leads_Student", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "STUDENT")
""", "14. Customer Profile", "#,##0")

add("FinalTable", "Leads_Working_Professional", """
CALCULATE(DISTINCTCOUNT(FinalTable[lead_id]), FinalTable[activity_type_category] = "Lead Capture", FinalTable[Customer_Profile] = "WORKING PROFESSIONAL")
""", "14. Customer Profile", "#,##0")

# ── 15. KPI Cards ────────────────────────────────────────────

add("FinalTable", "KPI_Leads_MoM_Arrow", """
IF([Leads_MoM%] > 0, "▲ " & FORMAT([Leads_MoM%], "0.0%"),
IF([Leads_MoM%] < 0, "▼ " & FORMAT([Leads_MoM%], "0.0%"),
"─ 0.0%"))""", "15. KPI Cards", None)

add("FinalTable", "KPI_Enrolls_MoM_Arrow", """
IF([Enrolls_MoM%] > 0, "▲ " & FORMAT([Enrolls_MoM%], "0.0%"),
IF([Enrolls_MoM%] < 0, "▼ " & FORMAT([Enrolls_MoM%], "0.0%"),
"─ 0.0%"))""", "15. KPI Cards", None)


# =============================================================
# CALLDETAIL MEASURES
# =============================================================

add("CallDetail", "Dials", """CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1)""", "1. Core Calling", "#,##0")
add("CallDetail", "Dialled_Leads", """CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1)""", "1. Core Calling", "#,##0")
add("CallDetail", "Connected_Leads", """CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)""", "1. Core Calling", "#,##0")
add("CallDetail", "Connected_Calls", """CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)""", "1. Core Calling", "#,##0")
add("CallDetail", "DNP_Leads", """CALCULATE(DISTINCTCOUNT(CallDetail[lead_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)""", "1. Core Calling", "#,##0")
add("CallDetail", "DNP_Calls", """CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_DNP_Call] = 1)""", "1. Core Calling", "#,##0")

add("CallDetail", "Connectivity%", """DIVIDE([Connected_Leads], [Dialled_Leads], 0)""", "2. Calling Ratios", "0.0%")
add("CallDetail", "DNP_Rate", """DIVIDE([DNP_Leads], [Dialled_Leads], 0)""", "2. Calling Ratios", "0.0%")
add("CallDetail", "CC_per_Lead", """DIVIDE([Connected_Calls], [Connected_Leads], 0)""", "2. Calling Ratios", "#,##0.0")
add("CallDetail", "Dials_per_Lead", """DIVIDE([Dials], [Dialled_Leads], 0)""", "2. Calling Ratios", "#,##0.0")

add("CallDetail", "Avg_Call_Duration_Sec", """
CALCULATE(AVERAGE(CallDetail[call_duration_sec]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1)
""", "3. Duration", "#,##0")

add("CallDetail", "Avg_Call_Duration_Formatted", """
VAR secs = [Avg_Call_Duration_Sec]
RETURN IF(ISBLANK(secs), "-", FORMAT(INT(secs / 60), "0") & ":" & FORMAT(MOD(INT(secs), 60), "00"))
""", "3. Duration", None)

add("CallDetail", "Quality_Call%", """
DIVIDE(
    CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[Is_Connected_Call] = 1, CallDetail[call_duration_sec] > 60),
    [Connected_Calls], 0)
""", "3. Duration", "0.0%")

add("CallDetail", "Active_Calling_BDAs", """CALCULATE(DISTINCTCOUNT(CallDetail[se_user_id]), CallDetail[Is_Valid_Call] = 1)""", "4. BDA Calling", "#,##0")
add("CallDetail", "Dials_per_BDA", """DIVIDE([Dials], [Active_Calling_BDAs], 0)""", "4. BDA Calling", "#,##0.0")
add("CallDetail", "Connected_per_BDA", """DIVIDE([Connected_Calls], [Active_Calling_BDAs], 0)""", "4. BDA Calling", "#,##0.0")
add("CallDetail", "Dialled_Leads_per_BDA", """DIVIDE([Dialled_Leads], [Active_Calling_BDAs], 0)""", "4. BDA Calling", "#,##0.0")

add("CallDetail", "Dials_Manual", """CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = TRUE())""", "5. Manual vs Auto", "#,##0")
add("CallDetail", "Dials_Auto", """CALCULATE(COUNT(CallDetail[call_id]), CallDetail[Is_Valid_Call] = 1, CallDetail[is_manual_call_done] = FALSE())""", "5. Manual vs Auto", "#,##0")
add("CallDetail", "Manual_Call%", """DIVIDE([Dials_Manual], [Dials], 0)""", "5. Manual vs Auto", "0.0%")

add("CallDetail", "Dials_PM", """CALCULATE([Dials], DATEADD(CallDetail[call_month_start], -1, MONTH))""", "6. MoM Calling", "#,##0")
add("CallDetail", "Connected_Leads_PM", """CALCULATE([Connected_Leads], DATEADD(CallDetail[call_month_start], -1, MONTH))""", "6. MoM Calling", "#,##0")
add("CallDetail", "Dials_MoM%", """DIVIDE([Dials] - [Dials_PM], [Dials_PM], 0)""", "6. MoM Calling", "0.0%")


# =============================================================
# EXECUTE — Create all measures via TOM API
# =============================================================

import sempy.fabric as fabric
from sempy.fabric import FabricRestClient

client = FabricRestClient()

# Get the dataset ID
datasets = fabric.list_datasets()
dataset_row = datasets[datasets["Dataset Name"] == DATASET_NAME]
if dataset_row.empty:
    print(f"ERROR: Semantic model '{DATASET_NAME}' not found.")
    print(f"Available models: {datasets['Dataset Name'].tolist()}")
else:
    print(f"Found semantic model: {DATASET_NAME}")
    print(f"Total measures to create: {len(measures)}")
    print()
    print("NOTE: sempy's TOM API for measure creation requires")
    print("Tabular Editor or XMLA write access.")
    print()
    print("ALTERNATIVE: Copy the measures from")
    print("docs/PBI_DAX_Measures.dax and docs/PBI_DAX_Measures_CallDetail.dax")
    print("into the Fabric web model editor, or use Tabular Editor")
    print("with the .csx script (docs/TE_Create_All_Measures.csx).")
    print()
    print("Measure definitions generated successfully:")
    for m in measures:
        print(f"  [{m['table']}] {m['name']}")
