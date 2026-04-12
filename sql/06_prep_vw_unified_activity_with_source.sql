/*  ============================================================
    PREP VIEW 6: prep.vw_unified_activity_with_source
    ------------------------------------------------------------
    Joins: prep.vw_unified_activity_appended
           + prep.unified_lead_capture_message (on activity_id)
    Purpose: Attaches parsed source/campaign/program from
             LeadCaptureMessage metadata to each activity row.

    Only Lead Capture activities get non-NULL source values;
    all other activity types get NULLs — this is by design.

    Dedup guard: LCM is deduped per activity_id to prevent
    fan-out if multiple messages exist for one activity.
    ============================================================ */

DROP VIEW IF EXISTS prep.vw_unified_activity_with_source;
GO

CREATE VIEW prep.vw_unified_activity_with_source AS
SELECT
    uaa.*,

    -- Source attribution from LeadCaptureMessage
    lcm_dedup.lc_source,
    lcm_dedup.lc_sourceMedium,
    lcm_dedup.lc_sourceCampaign,
    lcm_dedup.program_name,
    lcm_dedup.course_id

FROM prep.vw_unified_activity_appended uaa
LEFT JOIN (
    SELECT
        lcm_activity_id,
        lc_source,
        lc_sourceMedium,
        lc_sourceCampaign,
        program_name,
        course_id,
        ROW_NUMBER() OVER (
            PARTITION BY lcm_activity_id
            ORDER BY lcm_created_at DESC
        ) AS rn
    FROM prep.unified_lead_capture_message
    WHERE lcm_activity_id IS NOT NULL
) lcm_dedup
    ON uaa.activity_id = lcm_dedup.lcm_activity_id
   AND lcm_dedup.rn = 1;
GO
