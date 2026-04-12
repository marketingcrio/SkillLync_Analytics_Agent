/*  ============================================================
    PREP VIEW 1: prep.unified_activity
    ------------------------------------------------------------
    Joins: dbo.ActivityBase + dbo.ActivityType + dbo.Activity_extension
    Purpose: Single clean activity stream with decoded type info
             and activity owner from extension table.

    Run this FIRST — other prep views depend on it.
    ============================================================ */

DROP VIEW IF EXISTS prep.unified_activity;
GO

CREATE VIEW prep.unified_activity AS
SELECT
    ab.id                          AS activity_id,
    ab.prospect_id,
    ab.type_id,
    ab.event_id,
    ab.created_at,
    ab.updated_at,
    ab.activity_date,
    ab.created_by_id,
    ab.modified_by_id,
    ab.source                      AS activity_source,
    ab.source_medium               AS activity_source_medium,
    ab.source_campaign             AS activity_source_campaign,
    ab.form_name,
    ab.score                       AS activity_score,
    ab.activity_note,
    ab.web_url,
    ab.web_referrer,

    -- ActivityType decode
    at.activity_code               AS activity_type_activity_code,
    at.display_name                AS activity_type_display_name,
    at.direction                   AS activity_type_direction,
    at.is_done_by_system,

    -- Activity_extension: owner + key mx_custom fields
    ae.owner_id                    AS activity_owner_id,
    ae.status                      AS extension_status,
    ae.mx_custom39

FROM dbo.ActivityBase ab
INNER JOIN dbo.ActivityType at
    ON ab.type_id = at.id
LEFT JOIN dbo.Activity_extension ae
    ON ab.id = ae.related_activity_id;
GO
