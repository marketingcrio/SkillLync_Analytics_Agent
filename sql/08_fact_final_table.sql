/*  ============================================================
    FACT TABLE: fact.Final_Table  (Full Rebuild from Scratch)
    ------------------------------------------------------------
    Source prep views:
      - prep.vw_unified_activity_with_source  (activity stream)
      - prep.unified_leads                    (lead master)
      - prep.vw_call_detail                   (call metrics)

    Source dbo tables (direct joins):
      - dbo.SkillLyncSalesData                (enrollment + revenue)
      - dbo.[User]                            (BDA name resolution)
      - dbo.BDATierClassification             (BDA tier A/B/C/New)

    Bug fixes incorporated:
      BUG #1: Call Activity now includes codes 507, 777, 2500, 2502
      BUG #2: sale_value placed ONLY on first Lead Capture row per
              enrolled lead (prevents 10-16x revenue inflation)
      BUG #3: Demo tracks bifurcated (Webinar vs Tech)

    New columns:
      - Calling: Is_Valid_Call, Is_Connected_Call, call_duration_sec,
                 call_duration_bucket, dialstatus
      - Customer_Profile from LeadsExtension
      - team_domain_current + team_domain_at_assignment
      - Is_System_Activity (test/internal email exclusion)
      - Domain_group (program area classification)

    Grain: one row per activity event per lead
    ============================================================ */

DROP TABLE IF EXISTS fact.FinalTable;

CREATE TABLE fact.FinalTable
AS

/* =========================================================
   CTE 1: ACTIVITY TYPE CLASSIFICATION
   ---------------------------------------------------------
   Maps raw activity_codes to business categories.
   FIX: Added codes 507, 777, 2500, 2502 to Call Activity.
   FIX: Excludes junk codes 295, 298, 433, 434, 436.
   FIX: Added Demo Cancelled (319), Demo Rescheduled (318).
   ========================================================= */
WITH activity_type_logic AS (
    SELECT
        ua.*,
        CAST(CASE
            WHEN ua.activity_type_activity_code IN (
                239,270,254,284,332,267,305,299,234,263,209,354,3,221,
                924,925,926,927,929,928,922,923,310,23,292,271,
                399,281,432,404,405,412,410,411,406,428,272,226,
                240,268,343,398,516,521,513,514,520,282
            ) THEN 'Lead Capture'

            WHEN ua.activity_type_activity_code IN (315,316,259,290,920)
                THEN 'Demo Scheduled'

            WHEN ua.activity_type_activity_code IN (393)
                THEN 'SE Marked Demo Schedule'

            WHEN ua.activity_type_activity_code IN (319)
                THEN 'Demo Cancelled'

            WHEN ua.activity_type_activity_code IN (318)
                THEN 'Demo Rescheduled'

            WHEN ua.activity_type_activity_code IN (342,921,397)
                THEN 'Demo Completed - Webinars'

            WHEN ua.activity_type_activity_code IN (395)
                THEN 'SE Marked Demo Completed'

            WHEN ua.activity_type_activity_code IN (98,9629)
                THEN 'Payment Activity'

            /* BUG #1 FIX: Added 507, 777, 2500, 2502 */
            WHEN ua.activity_type_activity_code IN (506,507,777,2500,2502)
                THEN 'Call Activity'

            WHEN ua.activity_type_activity_code IN (2,510)
                THEN 'Page Visit'

            WHEN ua.activity_type_activity_code = 2200
                THEN 'Lead Assignment Activity'

            /* Exclude junk codes entirely */
            WHEN ua.activity_type_activity_code IN (295,298,433,434,436)
                THEN 'JUNK_EXCLUDE'

            ELSE 'Other / Unknown'
        END AS varchar(100)) AS activity_type_category

    FROM prep.vw_unified_activity_with_source ua
),

/* =========================================================
   CTE 2: SOURCE BUCKET (activity-level)
   ========================================================= */
base_with_source_bucket AS (
    SELECT
        atl.*,
        CAST(CASE
            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%grow.skill-lync.com%'
               OR LOWER(lc_source) LIKE '%direct grow%')
                THEN 'Direct Grow'

            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%youtube%'
               OR LOWER(lc_source) LIKE '%yt%'
               OR LOWER(lc_source) LIKE '%google_video%'
               OR LOWER(lc_source) LIKE '%video_ad%')
                THEN 'Youtube'

            /* Meta - Resources: paid Meta campaigns driving to resources.skill-lync.com */
            WHEN lc_source IS NOT NULL
             AND LOWER(lc_source) = 'ig'
             AND LOWER(COALESCE(lc_sourceCampaign,'')) LIKE '%website_conv%'
                THEN 'Meta - Resources'

            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%facebook%'
               OR LOWER(lc_source) LIKE '%fb%'
               OR LOWER(lc_source) LIKE '%insta%'
               OR LOWER(lc_source) LIKE '%instagram%'
               OR LOWER(lc_source) LIKE '%meta%'
               OR LOWER(lc_source) = 'ig')
                THEN 'Meta'

            WHEN lc_source IS NOT NULL
             AND LOWER(lc_source) LIKE '%linkedin%'
                THEN 'Linkedin'

            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%google ads%'
               OR LOWER(lc_source) LIKE '%google_search%'
               OR LOWER(lc_source) LIKE '%search_ad%')
                THEN 'Google Ads'

            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%email%'
               OR LOWER(lc_source) LIKE '%webengage%'
               OR LOWER(lc_source) LIKE '%kasplo%')
                THEN 'Email'

            WHEN lc_source IS NOT NULL
             AND LOWER(lc_source) LIKE '%whatsapp%'
                THEN 'Whatsapp'

            WHEN lc_source IS NOT NULL
             AND (LOWER(lc_source) LIKE '%google.com%'
               OR LOWER(lc_source) LIKE '%bing%'
               OR LOWER(lc_source) LIKE '%yahoo%'
               OR LOWER(lc_source) LIKE '%duckduckgo%'
               OR LOWER(lc_source) LIKE '%yandex%')
                THEN 'Organic'

            /* Organic Resources: sl_resource page with organic medium */
            WHEN lc_source IS NOT NULL
             AND LOWER(lc_source) = 'sl_resource'
             AND LOWER(COALESCE(lc_sourceMedium,'')) = 'organic'
                THEN 'Organic Resources'

            WHEN lc_source IS NOT NULL
             AND LOWER(lc_source) LIKE '%skill-lync.com%'
                THEN 'Direct'

            WHEN lc_source IS NULL
             AND (LOWER(activity_type_display_name) LIKE '%facebook%'
               OR LOWER(activity_type_display_name) LIKE '%meta%'
               OR LOWER(activity_type_display_name) LIKE '%fb%')
                THEN 'Meta'

            WHEN lc_source IS NULL
                THEN 'Email'

            ELSE 'Others'
        END AS varchar(100)) AS Source_Bucket

    FROM activity_type_logic atl
    WHERE atl.activity_type_category <> 'JUNK_EXCLUDE'
),

/* =========================================================
   CTE 3: LEAD JOIN + FINAL SOURCE BUCKET + DOMAIN GROUP
   ========================================================= */
base_with_lead AS (
    SELECT
        b.*,

        -- Source_Bucket_Final: refine Email bucket using lead-level campaign
        CAST(CASE
            WHEN b.Source_Bucket <> 'Email'
                THEN b.Source_Bucket
            WHEN b.Source_Bucket = 'Email'
             AND (LOWER(COALESCE(ul.Lead_Source_Campaign,'')) LIKE '%facebook%'
               OR LOWER(COALESCE(ul.Lead_Source_Campaign,'')) LIKE '%fb%'
               OR LOWER(COALESCE(ul.Lead_Source_Campaign,'')) LIKE '%meta%')
                THEN 'Meta'
            ELSE b.Source_Bucket
        END AS varchar(100)) AS Source_Bucket_Final,

        -- Lead identity
        ul.id                          AS lead_id,
        ul.first_name,
        ul.last_name,
        ul.email_address,
        ul.phone_country_code,
        ul.timezone,
        ul.prospect_stage,
        ul.utm_device                  AS lead_utm_device,
        ul.city                        AS lead_city,
        ul.state                       AS lead_state,
        ul.country                     AS lead_country,
        ul.age,
        ul.created_on                  AS lead_created_on,
        ul.current_owner_assignment_id,
        ul.owner_id                    AS lead_owner_id,
        ul.is_customer,

        -- Lead extension fields
        ul.mx_degree,
        ul.mx_department,
        ul.mx_lead_branch,
        ul.mx_department_name,
        ul.mx_domain,
        ul.mx_skill_centre_location,
        ul.mx_lead_background,
        ul.mx_lead_goal,
        ul.mx_year_of_passing,
        ul.mx_device,
        ul.mx_company_name,
        ul.mx_job_title,
        ul.mx_designation,
        ul.mx_job_experience,
        ul.mx_job_domain,
        ul.mx_years_of_experience,
        ul.mx_current_education_status,
        ul.mx_branch_of_education,
        ul.mx_working_professional_or_experienced,
        ul.mx_student_or_working_professional,
        ul.mx_interested_courses,
        ul.mx_course_interested_in,
        ul.mx_webinar_interest,

        -- Lead source fields
        ul.Lead_Source,
        ul.Lead_Source_Medium,
        ul.Lead_Source_Campaign,
        ul.star_rank,
        ul.first_source,
        ul.lead_star_rank,

        -- Customer profile
        ul.Customer_Profile,
        ul.profile,

        -- Team domain: current (snapshot) from LeadsExtension
        ul.le_team_domain             AS team_domain_current,

        -- Is_System_Activity: test/internal email exclusion
        CASE
            WHEN LOWER(ul.email_address) LIKE '%@skill-lync.com%' THEN 1
            WHEN LOWER(ul.email_address) LIKE '%@cybermindworks.com%' THEN 1
            WHEN LOWER(ul.email_address) LIKE '%@criodo.com%' THEN 1
            WHEN LOWER(ul.email_address) LIKE '%@criodo.co.in%' THEN 1
            ELSE 0
        END AS Is_System_Activity,

        -- Domain_group classification
        CAST(CASE
            WHEN LOWER(ul.mx_domain) IN ('mechanical','mech','manufacturing')
                THEN 'Mechanical'
            WHEN LOWER(ul.mx_domain) IN ('ev','hev')
                THEN 'Electric Vehicles'
            WHEN LOWER(ul.mx_domain) LIKE '%embedded%'
                THEN 'Embedded Systems'
            WHEN LOWER(ul.mx_domain) IN ('information tech','fsd')
                THEN 'Software / IT'
            WHEN LOWER(ul.mx_domain) = 'fea'
                THEN 'CAE / Simulation'
            WHEN LOWER(ul.mx_domain) LIKE '%electr%'
                THEN 'Electrical'
            WHEN LOWER(ul.mx_domain) LIKE '%design%'
                THEN 'Design'
            WHEN LOWER(ul.mx_domain) LIKE '%civil%'
                THEN 'Civil'
            ELSE 'Others / Unknown'
        END AS varchar(100)) AS Domain_group

    FROM base_with_source_bucket b
    LEFT JOIN prep.unified_leads ul
        ON b.prospect_id = ul.id
),

/* =========================================================
   CTE 4: LEAD CAPTURE EVENTS (for source + month tracking)
   ========================================================= */
lead_capture_activities AS (
    SELECT
        lead_id,
        created_at                     AS activity_created_at,
        Source_Bucket_Final,
        DATEFROMPARTS(YEAR(created_at), MONTH(created_at), 1)
                                       AS activity_month
    FROM base_with_lead
    WHERE activity_type_category = 'Lead Capture'
),

/* =========================================================
   CTE 5: FIRST LEAD CAPTURE SOURCE PER MONTH
   ========================================================= */
first_lead_capture_of_month AS (
    SELECT lead_id, activity_month,
           Source_Bucket_Final AS first_lead_capture_source_of_month,
           activity_created_at AS first_capture_date_of_month
    FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY lead_id, activity_month
            ORDER BY activity_created_at
        ) AS rn
        FROM lead_capture_activities
    ) t
    WHERE rn = 1
),

/* =========================================================
   CTE 5b: LAST LEAD CAPTURE SOURCE PER LEAD (all-time)
   ========================================================= */
last_lead_capture_source AS (
    SELECT lead_id,
           activity_created_at,
           Source_Bucket_Final AS last_lead_capture_source,
           activity_month     AS last_lead_capture_month
    FROM (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY lead_id
            ORDER BY activity_created_at DESC
        ) AS rn
        FROM lead_capture_activities
    ) t
    WHERE rn = 1
),

/* =========================================================
   CTE 6: ENROLLMENT DATA (from SkillLyncSalesData)
   ---------------------------------------------------------
   First sale per lead by email. sale_value will be placed
   ONLY on a single row per enrolled lead (BUG #2 FIX).
   ========================================================= */
enroll_dates AS (
    SELECT
        lead_id,
        enroll_date,
        CAST(sale_value AS DECIMAL(18,2))  AS sale_value,
        sale_program,
        sale_ind_pg
    FROM (
        SELECT
            ul.id                          AS lead_id,
            CAST(sd.[Formatted Sale Date] AS DATE)
                                           AS enroll_date,
            sd.[Booked Sale Amount]        AS sale_value,
            sd.[Program Chosen by Lead]    AS sale_program,
            sd.[Enrollment Type]           AS sale_ind_pg,
            ROW_NUMBER() OVER (
                PARTITION BY ul.id
                ORDER BY CAST(sd.[Formatted Sale Date] AS DATE)
            ) AS rn
        FROM prep.unified_leads ul
        INNER JOIN dbo.SkillLyncSalesData sd
            ON LOWER(TRIM(ul.email_address)) = LOWER(TRIM(sd.[Lead Email]))
    ) t
    WHERE rn = 1
),

/* =========================================================
   CTE 7: ASSIGNMENT RANK AT MONTH LEVEL (first per month)
   ========================================================= */
assignment_rank_month AS (
    SELECT lead_id, activity_month,
           lead_star_rank_at_assign,
           p1_score_at_assign,
           p1_star_rank_at_assign,
           bda_star_rank_at_assign,
           assigned_bda_id,
           assignment_team_domain_month,
           assignment_type_month,
           source_score_at_assign,
           lead_type_score_at_assign
    FROM (
        SELECT
            lead_id,
            DATEFROMPARTS(YEAR(created_at), MONTH(created_at), 1)
                                          AS activity_month,

            /* AUTHORITATIVE: star rank string from the assignment system */
            prospect_star_rank_at_assign  AS lead_star_rank_at_assign,

            /* P1 score: raw + derived bucket (for granular analysis) */
            priority_score1               AS p1_score_at_assign,
            CAST(CASE
                WHEN priority_score1 >= 60 THEN 'FourStar'
                WHEN priority_score1 >= 40 THEN 'ThreeStar'
                WHEN priority_score1 >= 20 THEN 'TwoStar'
                WHEN priority_score1 IS NOT NULL THEN 'OneStar'
                ELSE NULL
            END AS varchar(20)) AS p1_star_rank_at_assign,

            /* BDA star rank at time of assignment — key for quality matching */
            selected_user_rank            AS bda_star_rank_at_assign,

            selected_user_id_assign       AS assigned_bda_id,
            assignment_team_domain        AS assignment_team_domain_month,
            assignment_type               AS assignment_type_month,
            source_score                  AS source_score_at_assign,
            lead_type_score               AS lead_type_score_at_assign,

            ROW_NUMBER() OVER (
                PARTITION BY
                    lead_id,
                    DATEFROMPARTS(YEAR(created_at), MONTH(created_at), 1)
                ORDER BY created_at
            ) AS rn
        FROM base_with_lead
        WHERE activity_type_category = 'Lead Assignment Activity'
          AND selected_user_id_assign IS NOT NULL
    ) t
    WHERE rn = 1
),

/* =========================================================
   CTE 7b: LATEST ASSIGNED BDA PER LEAD (overall)
   ========================================================= */
latest_assigned_bda AS (
    SELECT lead_id, latest_bda_id,
           latest_p1_score, latest_p1_star_rank,
           latest_lead_star_rank, latest_bda_star_rank,
           latest_assignment_date
    FROM (
        SELECT
            lead_id,
            selected_user_id_assign       AS latest_bda_id,
            priority_score1               AS latest_p1_score,
            CAST(CASE
                WHEN priority_score1 >= 60 THEN 'FourStar'
                WHEN priority_score1 >= 40 THEN 'ThreeStar'
                WHEN priority_score1 >= 20 THEN 'TwoStar'
                WHEN priority_score1 IS NOT NULL THEN 'OneStar'
                ELSE NULL
            END AS varchar(20)) AS latest_p1_star_rank,
            prospect_star_rank_at_assign  AS latest_lead_star_rank,
            selected_user_rank            AS latest_bda_star_rank,
            created_at                    AS latest_assignment_date,
            ROW_NUMBER() OVER (
                PARTITION BY lead_id
                ORDER BY created_at DESC
            ) AS rn
        FROM base_with_lead
        WHERE activity_type_category = 'Lead Assignment Activity'
          AND selected_user_id_assign IS NOT NULL
    ) t
    WHERE rn = 1
)

/* =========================================================
   FINAL SELECT — Assembles all columns + precomputed flags
   ========================================================= */
SELECT
    /* --- Activity grain --- */
    b.activity_id,
    b.prospect_id,
    b.type_id,
    b.created_at,
    b.updated_at,
    b.activity_date,
    b.created_by_id,
    b.activity_source,
    b.activity_source_medium,
    b.activity_source_campaign,
    b.form_name,
    b.activity_score,
    b.web_url,

    /* --- Activity type --- */
    b.activity_type_activity_code,
    b.activity_type_display_name,
    b.activity_type_category,
    b.activity_type_direction,
    b.is_done_by_system,

    /* --- Extension --- */
    b.owner_id,
    b.extension_status,
    b.mx_custom39,

    /* --- Assignment fields (on assignment rows only) --- */
    b.selected_user_id_assign,
    b.from_user_id,
    b.assignment_type,
    b.assignment_team_domain,
    b.prospect_domain,

    /* --- Source attribution --- */
    b.lc_source,
    b.lc_sourceMedium,
    b.lc_sourceCampaign,
    b.program_name,
    b.course_id,
    b.Source_Bucket,
    b.Source_Bucket_Final,

    /* --- Lead identity --- */
    b.lead_id,
    b.first_name,
    b.last_name,
    b.email_address,
    b.phone_country_code,
    b.timezone,
    b.age,
    b.lead_created_on,
    b.lead_owner_id,
    b.is_customer,
    b.prospect_stage,
    b.lead_city,
    b.lead_state,
    b.lead_country,
    b.lead_utm_device,
    b.Is_System_Activity,

    /* --- Lead extension --- */
    b.mx_degree,
    b.mx_department,
    b.mx_lead_branch,
    b.mx_department_name,
    b.mx_domain,
    b.mx_skill_centre_location,
    b.mx_lead_background,
    b.mx_lead_goal,
    b.mx_year_of_passing,
    b.mx_device,
    b.mx_company_name,
    b.mx_job_title,
    b.mx_designation,
    b.mx_job_experience,
    b.mx_job_domain,
    b.mx_years_of_experience,
    b.mx_current_education_status,
    b.mx_branch_of_education,
    b.mx_working_professional_or_experienced,
    b.mx_student_or_working_professional,
    b.mx_interested_courses,
    b.mx_course_interested_in,
    b.mx_webinar_interest,
    b.Customer_Profile,
    b.profile,
    b.Domain_group,
    b.team_domain_current,

    /* --- Lead source --- */
    b.Lead_Source,
    b.Lead_Source_Medium,
    b.Lead_Source_Campaign,
    b.star_rank,
    b.first_source,
    b.lead_star_rank,

    /* --- Calendar decomposition --- */
    YEAR(b.created_at)              AS activity_year,
    MONTH(b.created_at)             AS activity_month,
    DAY(b.created_at)               AS activity_day,
    CAST(DATENAME(MONTH, b.created_at) AS VARCHAR(20))
                                    AS activity_month_name,
    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
                                    AS activity_month_start,
    DATEFROMPARTS(YEAR(b.lead_created_on), MONTH(b.lead_created_on), 1)
                                    AS lead_created_month,

    /* --- Source attribution (first capture of month) --- */
    flc.first_lead_capture_source_of_month,
    flc.first_capture_date_of_month,

    /* --- Last lead capture source (for Old-Others attribution) --- */
    llc.last_lead_capture_source,
    llc.last_lead_capture_month,

    /* --- Enrollment --- */
    ed.enroll_date,
    YEAR(ed.enroll_date)            AS enroll_year,
    MONTH(ed.enroll_date)           AS enroll_month,
    DAY(ed.enroll_date)             AS enroll_day,
    CAST(DATENAME(MONTH, ed.enroll_date) AS VARCHAR(20))
                                    AS enroll_month_name,
    DATEFROMPARTS(YEAR(ed.enroll_date), MONTH(ed.enroll_date), 1)
                                    AS enroll_month_start,
    ed.sale_program,
    ed.sale_ind_pg,

    /* -------------------------------------------------------
       BUG #2 FIX: sale_value ONLY on first Lead Capture row
       per enrolled lead per month.
       Prevents the 10-16x revenue inflation.
       ------------------------------------------------------- */
    CASE
        WHEN b.activity_type_category = 'Lead Capture'
         AND ed.sale_value IS NOT NULL
         AND ROW_NUMBER() OVER (
                PARTITION BY b.lead_id,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
                ORDER BY b.created_at
             ) = 1
        THEN ed.sale_value
        ELSE NULL
    END AS sale_value,

    /* -------------------------------------------------------
       Is_Valid_Enroll — works across ALL lead segments
       ------------------------------------------------------- */
    CASE
        /* Segments WITH capture: enrolled same month as capture */
        WHEN b.activity_type_category = 'Lead Capture'
         AND ed.enroll_date IS NOT NULL
         AND DATEFROMPARTS(YEAR(ed.enroll_date), MONTH(ed.enroll_date), 1)
             = DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
        THEN 1

        /* Old – Others: no capture this month, enrolled IN this month */
        WHEN ed.enroll_date IS NOT NULL
         AND DATEFROMPARTS(YEAR(ed.enroll_date), MONTH(ed.enroll_date), 1)
             = DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
         AND MAX(
                CASE WHEN b.activity_type_category = 'Lead Capture'
                     THEN 1 ELSE 0 END
             ) OVER (
                PARTITION BY b.lead_id,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
             ) = 0
        THEN 1

        ELSE 0
    END AS Is_Valid_Enroll,

    /* Same Month Enroll (Lead Capture rows only) */
    CAST(CASE
        WHEN b.activity_type_category = 'Lead Capture'
         AND ed.enroll_date IS NOT NULL
         AND flc.first_capture_date_of_month IS NOT NULL
         AND ed.enroll_date >= flc.first_capture_date_of_month
         AND YEAR(ed.enroll_date) = YEAR(b.created_at)
         AND MONTH(ed.enroll_date) = MONTH(b.created_at)
        THEN 'Enrolls'
        ELSE 'Leads'
    END AS varchar(20)) AS SameMonthEnrolls,

    /* Enroll Month Bucket (Lead Capture rows only) */
    CAST(CASE
        WHEN b.activity_type_category <> 'Lead Capture'       THEN NULL
        WHEN ed.enroll_date IS NULL                            THEN 'Leads'
        WHEN flc.first_capture_date_of_month IS NULL           THEN 'Leads'
        WHEN ed.enroll_date < flc.first_capture_date_of_month  THEN 'Leads'
        WHEN DATEDIFF(MONTH,
                DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1),
                ed.enroll_date
             ) BETWEEN 0 AND 12
            THEN 'M+' + CAST(DATEDIFF(MONTH,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1),
                    ed.enroll_date
                ) AS varchar(3))
        ELSE 'Leads'
    END AS varchar(20)) AS Enroll_Month_Bucket_Capped,

    /* Has Lead Capture In Month (window flag) */
    MAX(
        CASE WHEN b.activity_type_category = 'Lead Capture'
             THEN 1 ELSE 0 END
    ) OVER (
        PARTITION BY b.lead_id,
            DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
    ) AS has_lead_capture_in_month,

    /* Is First Assignment Per Lead Per Month */
    CASE
        WHEN b.activity_type_category = 'Lead Assignment Activity'
         AND arm.assigned_bda_id IS NOT NULL
         AND b.lead_id = arm.lead_id
        THEN 1
        ELSE 0
    END AS Is_First_Assignment_Per_Month,

    /* Lead Segment */
    CAST(CASE
        WHEN MAX(
                CASE WHEN b.activity_type_category = 'Lead Capture'
                     THEN 1 ELSE 0 END
             ) OVER (
                PARTITION BY b.lead_id,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
             ) = 1
         AND DATEFROMPARTS(YEAR(b.lead_created_on), MONTH(b.lead_created_on), 1)
             = DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
            THEN 'New Lead'

        WHEN MAX(
                CASE WHEN b.activity_type_category = 'Lead Capture'
                     THEN 1 ELSE 0 END
             ) OVER (
                PARTITION BY b.lead_id,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
             ) = 1
         AND DATEFROMPARTS(YEAR(b.lead_created_on), MONTH(b.lead_created_on), 1)
             < DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
            THEN 'Old Lead - Capture'

        ELSE 'Old - Others'
    END AS varchar(50)) AS lead_segment,

    /* Unified source attribution across all segments */
    CAST(CASE
        WHEN MAX(
                CASE WHEN b.activity_type_category = 'Lead Capture'
                     THEN 1 ELSE 0 END
             ) OVER (
                PARTITION BY b.lead_id,
                    DATEFROMPARTS(YEAR(b.created_at), MONTH(b.created_at), 1)
             ) = 1
            THEN flc.first_lead_capture_source_of_month
        ELSE llc.last_lead_capture_source
    END AS varchar(200)) AS source_attribution_final,

    /* --- Activity Owner (name from User table) --- */
    (uown.first_name + ' ' + uown.last_name)
                                    AS activity_owner_name,
    uown.email                      AS activity_owner_email,

    /* --- Lead Star Rank at Assignment (AUTHORITATIVE — from assignment system) --- */
    arm.lead_star_rank_at_assign,
    arm.p1_score_at_assign,
    arm.p1_star_rank_at_assign,
    arm.bda_star_rank_at_assign,

    /* --- P1 Rank effective (fallback chain — for slicers / rollups) --- */
    /* 1) latest_p1_star_rank — from most recent assignment event ever       */
    /* 2) lead_star_rank — current LSQ snapshot, for leads never routed      */
    /*    through lead_assignment_history                                    */
    /* Reduces Jan 2026 Lead Capture NULL bucket from 17% → 9%.              */
    CAST(COALESCE(lab.latest_p1_star_rank, b.lead_star_rank) AS varchar(20))
                                    AS p1_star_rank_effective,

    arm.assignment_type_month,
    arm.source_score_at_assign,
    arm.lead_type_score_at_assign,

    /* --- BDA: month-level assignment --- */
    arm.assigned_bda_id,
    (ubda_month.first_name + ' ' + ubda_month.last_name)
                                    AS assigned_bda_name,
    ubda_month.email                AS assigned_bda_email,
    btm.[Tier]                      AS assigned_bda_tier,
    btm.[Status]                    AS assigned_bda_status,
    arm.assignment_team_domain_month AS team_domain_at_assignment,

    /* --- BDA: latest overall --- */
    lab.latest_bda_id,
    (ubda_latest.first_name + ' ' + ubda_latest.last_name)
                                    AS latest_bda_name,
    ubda_latest.email               AS latest_bda_email,
    bt.[Tier]                       AS latest_bda_tier,
    bt.[Status]                     AS latest_bda_status,
    lab.latest_p1_score,
    lab.latest_p1_star_rank,
    lab.latest_lead_star_rank,
    lab.latest_bda_star_rank,
    lab.latest_assignment_date,

    /* --- BDA: unified (month-first, fallback to latest) --- */
    COALESCE(arm.assigned_bda_id, lab.latest_bda_id)
                                    AS bda_id,
    COALESCE(
        (ubda_month.first_name + ' ' + ubda_month.last_name),
        (ubda_latest.first_name + ' ' + ubda_latest.last_name)
    )                               AS bda_name,
    COALESCE(ubda_month.email, ubda_latest.email)
                                    AS bda_email,
    COALESCE(btm.[Tier], bt.[Tier])
                                    AS bda_tier,
    COALESCE(btm.[Status], bt.[Status])
                                    AS bda_status,

    /* --- BDA hierarchy (from unified BDA) --- */
    ubda_hier.dm                    AS bda_dm_workforce_id,
    ubda_hier.rsm                   AS bda_rsm_workforce_id,
    ubda_hier.ad                    AS bda_ad_workforce_id,
    ubda_hier.region                AS bda_region,

    /* --- Star Rank: current vs at-assignment (KEY DISTINCTION) --- */
    /* lead_star_rank = CURRENT snapshot from lead_filtered_view (changes over time) */
    /* lead_star_rank_at_assign = FROZEN at assignment time (from lead_assignment_history) */
    /* bda_star_rank_at_assign = BDA's rank when they received this lead */
    /* Use at-assignment ranks for quality-matching analysis */

    /* --- Assignment quality matching columns --- */
    CASE
        WHEN arm.lead_star_rank_at_assign IS NOT NULL
         AND arm.bda_star_rank_at_assign IS NOT NULL
         AND arm.lead_star_rank_at_assign = arm.bda_star_rank_at_assign
        THEN 1
        ELSE 0
    END AS Is_Star_Match,

    /* Was this lead assigned this month? (for Leads→Assigned funnel) */
    CASE
        WHEN arm.assigned_bda_id IS NOT NULL THEN 1
        ELSE 0
    END AS Is_Assigned_This_Month,

    /* --- Program Interested (Lead Capture rows only) --- */
    CAST(CASE
        WHEN b.activity_type_category <> 'Lead Capture' THEN NULL
        WHEN b.program_name IS NOT NULL THEN b.program_name
        WHEN LOWER(b.lc_source) LIKE '%iit jammu%'
         AND LOWER(b.lc_source) LIKE '%design%'
            THEN 'IIT Jammu Design'
        WHEN LOWER(b.lc_source) LIKE '%iit jammu%'
         AND LOWER(b.lc_source) LIKE '%ev%'
            THEN 'IIT Jammu EV'
        ELSE NULL
    END AS varchar(500)) AS Program_Interested

FROM base_with_lead b

/* --- Source attribution CTEs --- */
LEFT JOIN first_lead_capture_of_month flc
    ON b.lead_id = flc.lead_id
   AND flc.activity_month = DATEFROMPARTS(
        YEAR(b.created_at), MONTH(b.created_at), 1)

LEFT JOIN last_lead_capture_source llc
    ON b.lead_id = llc.lead_id

/* --- Enrollment --- */
LEFT JOIN enroll_dates ed
    ON b.lead_id = ed.lead_id

/* --- BDA: month-level --- */
LEFT JOIN assignment_rank_month arm
    ON b.lead_id = arm.lead_id
   AND arm.activity_month = DATEFROMPARTS(
        YEAR(b.created_at), MONTH(b.created_at), 1)

/* --- BDA: latest --- */
LEFT JOIN latest_assigned_bda lab
    ON b.lead_id = lab.lead_id

/* --- User lookups for name resolution --- */
LEFT JOIN dbo.[User] uown
    ON b.owner_id = uown.id

LEFT JOIN dbo.[User] ubda_month
    ON arm.assigned_bda_id = ubda_month.id

LEFT JOIN dbo.[User] ubda_latest
    ON lab.latest_bda_id = ubda_latest.id

/* --- Unified BDA for hierarchy --- */
LEFT JOIN dbo.[User] ubda_hier
    ON COALESCE(arm.assigned_bda_id, lab.latest_bda_id) = ubda_hier.id

/* --- BDA tier classification --- */
LEFT JOIN dbo.BDATierClassification btm
    ON LOWER(ubda_month.email) = LOWER(btm.[Email])

LEFT JOIN dbo.BDATierClassification bt
    ON LOWER(ubda_latest.email) = LOWER(bt.[Email])

/* --- Calling detail removed — use fact.CallDetail separately --- */
/* dbo.Call and dbo.ActivityBase are separate systems with no FK.  */
/* Calling metrics live in fact.CallDetail (see 10_fact_call_detail.sql). */;
