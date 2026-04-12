/*  ============================================================
    PREP VIEW 4: prep.vw_lead_assignment_activity
    ------------------------------------------------------------
    Source: dbo.lead_assignment_history
    Purpose: Wraps assignment events with a synthetic activity_code
             (2200) so they can UNION into the activity stream.

    This lets the fact table treat assignments as activity rows
    alongside calls, demos, lead captures, etc.
    ============================================================ */

DROP VIEW IF EXISTS prep.vw_lead_assignment_activity;
GO

CREATE VIEW prep.vw_lead_assignment_activity AS
SELECT
    lah.id                         AS activity_id,
    lah.prospect_id,
    lah.created_at,
    lah.updated_at,
    lah.created_by_id,

    -- Synthetic activity type fields
    2200                           AS activity_type_activity_code,
    CAST('Lead Assignment Activity' AS varchar(200)) AS activity_type_display_name,
    CAST(NULL AS varchar(8000))    AS activity_type_direction,
    CAST(0 AS bit)                 AS is_done_by_system,

    -- Assignment-specific fields
    lah.selected_user_id           AS selected_user_id_assign,
    lah.from_user_id,
    lah.priority_score1,
    lah.priority_score2,
    lah.prospect_star_rank         AS prospect_star_rank_at_assign,
    lah.selected_user_rank,
    lah.assignment_type,
    lah.team_domain                AS assignment_team_domain,
    lah.prospect_domain,
    lah.prospect_rank,
    lah.current_stage              AS assignment_current_stage,
    lah.source_score,
    lah.lead_type_score,
    lah.current_week_activity_score

FROM dbo.lead_assignment_history lah;
GO
