/*  ============================================================
    PREP VIEW 2: prep.unified_leads
    ------------------------------------------------------------
    Joins: dbo.Leads + dbo.LeadsExtension + dbo.lead_filtered_view
    Purpose: Single clean lead master with all needed attributes.

    Dedup guard: lead_filtered_view is joined with ROW_NUMBER
    to guarantee 1:1 even if source has duplicates.
    ============================================================ */

DROP VIEW IF EXISTS prep.unified_leads;
GO

CREATE VIEW prep.unified_leads AS
SELECT
    -- Lead identity
    l.id,
    l.first_name,
    l.last_name,
    l.email_address,
    l.phone,
    l.national_number,
    l.phone_country_code,
    l.timezone,
    l.age,

    -- Lead dates
    l.created_on,
    l.modified_on,
    l.lead_conversion_date,
    l.current_owner_assignment_date,

    -- Lead status (SNAPSHOT — changes on update)
    l.prospect_stage,
    l.owner_id,
    l.current_owner_assignment_id,
    l.is_customer,
    l.is_lead,
    l.do_not_call,
    l.do_not_email,
    l.do_not_sms,

    -- Lead geography
    l.city,
    l.state,
    l.country,
    l.country_code,

    -- Lead UTM / source
    l.source                       AS lead_source_raw,
    l.source_medium                AS lead_source_medium_raw,
    l.source_campaign              AS lead_source_campaign_raw,
    l.first_source,
    l.first_original_source,
    l.utm_device,
    l.utm_source,

    -- Lead engagement
    l.score                        AS lead_score,
    l.engagement_score,
    l.total_visits,
    l.star_rank,
    l.team_domain                  AS lead_team_domain,
    l.related_prospect_id,
    l.verified_otp,

    -- LeadsExtension attributes
    le.mx_degree,
    le.mx_department,
    le.mx_department_name,
    le.mx_domain,
    le.new_mx_domain,
    le.mx_lead_branch,
    le.mx_skill_centre_location,
    le.mx_lead_background,
    le.mx_lead_goal,
    le.mx_year_of_passing,
    le.mx_device,
    le.mx_company_name,
    le.mx_job_title,
    le.mx_designation,
    le.mx_job_experience,
    le.mx_job_domain,
    le.mx_years_of_experience,
    le.mx_current_education_status,
    le.mx_branch_of_education,
    le.mx_working_professional_or_experienced,
    le.mx_student_or_working_professional,
    le.mx_interested_courses,
    le.mx_course_interested_in,
    le.mx_webinar_interest,
    le.mx_intent,
    le.mx_lead_quality_score,
    le.mx_eligibility_status,
    le.mx_india_or_out_of_india,
    le.team_domain                 AS le_team_domain,

    -- Lead source enrichment from Leads table
    COALESCE(l.source, l.first_source, l.first_original_source) AS Lead_Source,
    l.source_medium                AS Lead_Source_Medium,
    l.source_campaign              AS Lead_Source_Campaign,

    -- Star rank from lead_filtered_view (deduped)
    lfv.latest_star_rank           AS lead_star_rank,

    -- Customer Profile derivation
    CAST(CASE
        WHEN LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%job%'
          OR LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%unemploy%'
          OR LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%fresher%'
            THEN 'JOB SEEKER'
        WHEN LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%student%'
            THEN 'STUDENT'
        WHEN LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%working%'
          OR LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%professional%'
          OR LOWER(COALESCE(le.mx_student_or_working_professional, '')) LIKE '%experience%'
            THEN 'WORKING PROFESSIONAL'
        ELSE 'OTHERS'
    END AS varchar(50)) AS Customer_Profile,

    -- Profile short code (CWP / NWP / STU / NULL)
    -- TBD and NULL both become NULL. Unemployed → NWP (matches Job Seeker semantics).
    CAST(CASE le.mx_student_or_working_professional
        WHEN 'Working Professional' THEN 'CWP'
        WHEN 'Job Seeker'           THEN 'NWP'
        WHEN 'Unemployed'           THEN 'NWP'
        WHEN 'Student'              THEN 'STU'
    END AS varchar(5)) AS profile

FROM dbo.Leads l
LEFT JOIN dbo.LeadsExtension le
    ON l.id = le.prospect_id
LEFT JOIN dbo.lead_filtered_view lfv
    ON l.id = lfv.id;
GO
