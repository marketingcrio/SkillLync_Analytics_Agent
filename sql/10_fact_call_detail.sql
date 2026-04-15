/*  ============================================================
    FACT TABLE: fact.CallDetail
    ------------------------------------------------------------
    Source: prep.vw_call_detail + prep.unified_leads + dbo.[User]
             + dbo.BDATierClassification

    Purpose: Dedicated calling metrics table.
    - One row per call event from dbo.Call
    - JSON-parsed duration/status from dbo.CallEvent
    - Dummy-call filtering (Is_Valid_Call)
    - Connected/DNP flags
    - BDA + lead enrichment

    PBI model: fact.FinalTable (funnel) + fact.CallDetail (calling)
               linked on prospect_id / lead_id

    All calling measures (Dials, Connected_Leads, Connectivity%,
    Avg Duration, CC/Lead, DNP Rate) query THIS table,
    filtering on Is_Valid_Call = 1.
    ============================================================ */

DROP TABLE IF EXISTS fact.CallDetail;

CREATE TABLE fact.CallDetail
AS
SELECT
    /* --- Call grain --- */
    cd.call_id,
    cd.prospect_id,
    cd.se_user_id,
    cd.created_at,
    cd.updated_at,
    cd.call_status,
    cd.direction,
    cd.is_manual_call_done,
    cd.original_call_status,
    cd.comments,
    cd.platform_type,

    /* --- Call event detail (from JSON) --- */
    cd.call_duration_sec,
    cd.status1,
    cd.status2,
    cd.dialstatus,
    cd.caller_phone,
    cd.receiver_phone,

    /* --- Computed flags --- */
    cd.Is_Valid_Call,
    cd.Is_Connected_Call,
    cd.Is_DNP_Call,
    CAST(cd.call_duration_bucket AS varchar(20)) AS call_duration_bucket,
    cd.prev_call_created_at,

    /* --- Calendar decomposition --- */
    YEAR(cd.created_at)              AS call_year,
    MONTH(cd.created_at)             AS call_month,
    DAY(cd.created_at)               AS call_day,
    DATEFROMPARTS(YEAR(cd.created_at), MONTH(cd.created_at), 1)
                                     AS call_month_start,

    /* --- Lead enrichment --- */
    ul.id                            AS lead_id,
    ul.first_name                    AS lead_first_name,
    ul.last_name                     AS lead_last_name,
    ul.email_address                 AS lead_email,
    ul.prospect_stage,
    ul.is_customer,
    ul.city                          AS lead_city,
    ul.state                         AS lead_state,
    ul.country                       AS lead_country,
    ul.mx_domain,
    ul.Customer_Profile,
    ul.lead_star_rank,
    ul.le_team_domain                AS team_domain_current,

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
    END AS varchar(100)) AS Domain_group,

    /* --- Is test/internal lead --- */
    CASE
        WHEN LOWER(ul.email_address) LIKE '%@skill-lync.com%' THEN 1
        WHEN LOWER(ul.email_address) LIKE '%@cybermindworks.com%' THEN 1
        WHEN LOWER(ul.email_address) LIKE '%@criodo.com%' THEN 1
        WHEN LOWER(ul.email_address) LIKE '%@criodo.co.in%' THEN 1
        ELSE 0
    END AS Is_System_Activity,

    /* --- BDA (caller) enrichment --- */
    (ubda.first_name + ' ' + ubda.last_name)
                                     AS bda_name,
    ubda.email                       AS bda_email,
    ubda.role                        AS bda_role,
    ubda.region                      AS bda_region,
    bt.[Tier]                        AS bda_tier,
    bt.[Status]                      AS bda_status,

    /* --- BDA hierarchy --- */
    ubda.dm                          AS bda_dm_workforce_id,
    ubda.rsm                         AS bda_rsm_workforce_id,
    ubda.ad                          AS bda_ad_workforce_id

FROM prep.vw_call_detail cd

LEFT JOIN prep.unified_leads ul
    ON cd.prospect_id = ul.id

LEFT JOIN dbo.[User] ubda
    ON cd.se_user_id = ubda.id

LEFT JOIN dbo.BDATierClassification bt
    ON LOWER(ubda.email) = LOWER(bt.[Email]);
