/*  ============================================================
    PREP VIEW 3: prep.unified_lead_capture_message
    ------------------------------------------------------------
    Joins: dbo.LeadCaptureMessage + dbo.lead_capture_message_metadata
    Purpose: Enriches each lead capture event with parsed source,
             campaign, medium, program from metadata table.

    Dedup guard: metadata is deduped per lead_capture_message_id
    using ROW_NUMBER to prevent fan-out.
    ============================================================ */

DROP VIEW IF EXISTS prep.unified_lead_capture_message;
GO

CREATE VIEW prep.unified_lead_capture_message AS
SELECT
    lcm.id                         AS lcm_id,
    lcm.created_at                 AS lcm_created_at,
    lcm.prospect_id                AS lcm_prospect_id,
    lcm.activity_id                AS lcm_activity_id,
    lcm.message                    AS lcm_message_raw,

    -- Parsed metadata (deduped — first row per message)
    md.source                      AS lc_source,
    md.source_medium               AS lc_sourceMedium,
    md.source_campaign             AS lc_sourceCampaign,
    md.program_name,
    md.course_id

FROM dbo.LeadCaptureMessage lcm
LEFT JOIN (
    SELECT
        lead_capture_message_id,
        source,
        source_medium,
        source_campaign,
        program_name,
        course_id,
        ROW_NUMBER() OVER (
            PARTITION BY lead_capture_message_id
            ORDER BY created_at DESC
        ) AS rn
    FROM dbo.lead_capture_message_metadata
) md
    ON lcm.id = md.lead_capture_message_id
   AND md.rn = 1;
GO
