/*  ============================================================
    PREP VIEW 5: prep.vw_unified_activity_appended
    ------------------------------------------------------------
    UNION ALL: prep.unified_activity + prep.vw_lead_assignment_activity
    Purpose: Single stream of ALL events (real activities +
             synthetic assignment activities).

    Column alignment is explicit — NULLs padded where one side
    doesn't have the column.
    ============================================================ */

DROP VIEW IF EXISTS prep.vw_unified_activity_appended;
GO

CREATE VIEW prep.vw_unified_activity_appended AS

-- Real activities from ActivityBase
SELECT
    ua.activity_id,
    ua.prospect_id,
    ua.type_id,
    ua.created_at,
    ua.updated_at,
    ua.activity_date,
    ua.created_by_id,
    ua.modified_by_id,
    ua.activity_source,
    ua.activity_source_medium,
    ua.activity_source_campaign,
    ua.form_name,
    ua.activity_score,
    ua.activity_note,
    ua.web_url,
    ua.web_referrer,

    ua.activity_type_activity_code,
    ua.activity_type_display_name,
    ua.activity_type_direction,
    ua.is_done_by_system,

    ua.activity_owner_id           AS owner_id,
    ua.extension_status,
    ua.mx_custom39,

    -- Assignment fields NULL for real activities
    CAST(NULL AS varchar(8000))    AS selected_user_id_assign,
    CAST(NULL AS varchar(8000))    AS from_user_id,
    CAST(NULL AS decimal(18,6))    AS priority_score1,
    CAST(NULL AS decimal(18,6))    AS priority_score2,
    CAST(NULL AS varchar(8000))    AS prospect_star_rank_at_assign,
    CAST(NULL AS varchar(8000))    AS selected_user_rank,
    CAST(NULL AS varchar(8000))    AS assignment_type,
    CAST(NULL AS varchar(8000))    AS assignment_team_domain,
    CAST(NULL AS varchar(8000))    AS prospect_domain,
    CAST(NULL AS int)              AS source_score,
    CAST(NULL AS int)              AS lead_type_score

FROM prep.unified_activity ua

UNION ALL

-- Assignment pseudo-activities
SELECT
    la.activity_id,
    la.prospect_id,
    CAST(NULL AS varchar(8000))    AS type_id,
    la.created_at,
    la.updated_at,
    CAST(NULL AS datetime2(6))        AS activity_date,
    la.created_by_id,
    CAST(NULL AS varchar(8000))    AS modified_by_id,
    CAST(NULL AS varchar(8000))    AS activity_source,
    CAST(NULL AS varchar(8000))    AS activity_source_medium,
    CAST(NULL AS varchar(8000))    AS activity_source_campaign,
    CAST(NULL AS varchar(8000))    AS form_name,
    CAST(NULL AS int)              AS activity_score,
    CAST(NULL AS varchar(8000))    AS activity_note,
    CAST(NULL AS varchar(8000))    AS web_url,
    CAST(NULL AS varchar(8000))    AS web_referrer,

    la.activity_type_activity_code,
    la.activity_type_display_name,
    la.activity_type_direction,
    la.is_done_by_system,

    la.selected_user_id_assign     AS owner_id,
    CAST(NULL AS varchar(8000))    AS extension_status,
    CAST(NULL AS varchar(8000))    AS mx_custom39,

    -- Assignment-specific fields
    la.selected_user_id_assign,
    la.from_user_id,
    la.priority_score1,
    la.priority_score2,
    la.prospect_star_rank_at_assign,
    la.selected_user_rank,
    la.assignment_type,
    la.assignment_team_domain,
    la.prospect_domain,
    la.source_score,
    la.lead_type_score

FROM prep.vw_lead_assignment_activity la;
GO
