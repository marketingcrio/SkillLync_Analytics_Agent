/*  ============================================================
    PREP VIEW 7: prep.vw_call_detail
    ------------------------------------------------------------
    Joins: dbo.Call + dbo.CallEvent (JSON parsed)
    Purpose: Single source for ALL calling analysis.
             - Parses JSON from CallEvent.event_data
             - Computes dummy-call flag (Is_Valid_Call)
             - Computes connectivity flags
             - Computes duration buckets

    The dummy-call logic comes from SL ops team's PostgreSQL
    queries: filter rapid re-dials within 5 seconds.
    ============================================================ */

DROP VIEW IF EXISTS prep.vw_call_detail;
GO

CREATE VIEW prep.vw_call_detail AS
WITH call_with_events AS (
    SELECT
        c.id                           AS call_id,
        c.prospect_id,
        c.user_id                      AS se_user_id,
        c.created_at,
        c.updated_at,
        c.call_status,
        c.direction,
        c.is_manual_call_done,
        c.original_call_status,
        c.comments,
        c.platform_type,

        -- JSON-parsed fields from CallEvent (CAST to varchar — JSON_VALUE returns nvarchar)
        TRY_CAST(JSON_VALUE(ce.event_data, '$.duration') AS INT)
                                       AS call_duration_sec,
        CAST(JSON_VALUE(ce.event_data, '$.status1') AS varchar(50))
                                       AS status1,
        CAST(JSON_VALUE(ce.event_data, '$.status2') AS varchar(50))
                                       AS status2,
        CAST(JSON_VALUE(ce.event_data, '$.dialstatus') AS varchar(50))
                                       AS dialstatus,
        CAST(JSON_VALUE(ce.event_data, '$.caller') AS varchar(50))
                                       AS caller_phone,
        CAST(JSON_VALUE(ce.event_data, '$.receiver') AS varchar(50))
                                       AS receiver_phone

    FROM dbo.Call c
    LEFT JOIN (
        -- Dedup: one completed event per call
        SELECT
            call_id,
            event_data,
            ROW_NUMBER() OVER (
                PARTITION BY call_id
                ORDER BY created_at DESC
            ) AS rn
        FROM dbo.CallEvent
        WHERE event_type = 'completed'
    ) ce
        ON c.id = ce.call_id AND ce.rn = 1
)
SELECT
    cwe.*,

    -- Previous call timestamp for dummy-call detection
    LAG(cwe.created_at) OVER (
        PARTITION BY cwe.se_user_id, cwe.prospect_id
        ORDER BY cwe.created_at ASC
    ) AS prev_call_created_at,

    -- Is_Valid_Call: excludes ghost calls and rapid re-dials
    CASE
        WHEN NULLIF(TRIM(cwe.status1), '') IS NULL THEN 0
        WHEN LAG(cwe.created_at) OVER (
            PARTITION BY cwe.se_user_id, cwe.prospect_id
            ORDER BY cwe.created_at ASC
        ) IS NULL THEN 1
        WHEN DATEDIFF(SECOND,
            LAG(cwe.created_at) OVER (
                PARTITION BY cwe.se_user_id, cwe.prospect_id
                ORDER BY cwe.created_at ASC
            ),
            cwe.created_at) > 5 THEN 1
        ELSE 0
    END AS Is_Valid_Call,

    -- Is_Connected_Call: actual conversation happened
    CASE
        WHEN cwe.status1 = 'Connected' AND cwe.status2 = 'Connected' THEN 1
        ELSE 0
    END AS Is_Connected_Call,

    -- Is_DNP_Call: did not pick up
    CASE
        WHEN cwe.call_status IN ('dnp', 'dnpWithinLimit') THEN 1
        ELSE 0
    END AS Is_DNP_Call,

    -- Call duration bucket
    CAST(CASE
        WHEN cwe.call_duration_sec IS NULL THEN NULL
        WHEN cwe.call_duration_sec < 30 THEN '<30s'
        WHEN cwe.call_duration_sec BETWEEN 30 AND 60 THEN '30-60s'
        WHEN cwe.call_duration_sec BETWEEN 61 AND 180 THEN '60-180s'
        ELSE '>180s'
    END AS varchar(20)) AS call_duration_bucket

FROM call_with_events cwe;
GO
