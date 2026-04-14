/*  ============================================================
    DIMENSION: dim.User
    ------------------------------------------------------------
    Flattens the sales org hierarchy from dbo.[User] so activity
    rows can be rolled up BDA → DM → RSM → AD in one join.

    Source hierarchy (dbo.[User]):
      role='se'  has dm  = workforce_id of their DM
      role='dm'  has rsm = workforce_id of their RSM
      role='rsm' has ad  = workforce_id of their AD
      role='ad'  top

    Resolution rule (per user directive 2026-04-14):
      - Current manager only (hierarchy as it stands today).
      - Walk up through each LEVEL's own pointer, not the cached
        value on the SE row (SE rows often have stale rsm/ad).

    Materialized as a TABLE (not view) because Power BI DirectLake
    only exposes physical tables. Matches dim.Calendar pattern.
    Re-run this script whenever the hierarchy changes (daily
    alongside the fact rebuild is safe — ~6k rows).

    Relationship in Power BI:
      dim.User[user_id] 1──* fact.Final_Table[bda_id]

    Notes:
      - A row with role='dm' is its OWN dm_name (DMs who run demos
        themselves get attributed to themselves, not their RSM).
      - is_deleted=1 users are kept (historical BDAs still appear
        in fact rows); the table flags them via `is_deleted`.
    ============================================================ */

DROP TABLE IF EXISTS dim.[User];

CREATE TABLE dim.[User]
AS
SELECT
    CAST(u.id AS varchar(50))                                   AS user_id,
    CAST(TRIM(CONCAT(u.first_name,' ',u.last_name)) AS varchar(200)) AS user_name,
    CAST(u.email AS varchar(200))                               AS user_email,
    CAST(u.role AS varchar(20))                                 AS user_role,
    u.workforce_id                                              AS user_workforce_id,
    u.is_deleted                                                AS is_deleted,

    /* DM level: if u IS a DM, point at self; else resolve via u.dm */
    CAST(CASE WHEN u.role='dm' THEN u.id ELSE dm_u.id END AS varchar(50))  AS dm_id,
    CAST(CASE WHEN u.role='dm' THEN TRIM(CONCAT(u.first_name,' ',u.last_name))
         ELSE TRIM(CONCAT(dm_u.first_name,' ',dm_u.last_name)) END AS varchar(200)) AS dm_name,

    /* RSM level: resolved through the DM's OWN rsm pointer */
    CAST(CASE WHEN u.role='rsm' THEN u.id
              WHEN u.role='dm'  THEN rsm_via_self.id
              ELSE rsm_via_dm.id END AS varchar(50))            AS rsm_id,
    CAST(CASE WHEN u.role='rsm' THEN TRIM(CONCAT(u.first_name,' ',u.last_name))
              WHEN u.role='dm'  THEN TRIM(CONCAT(rsm_via_self.first_name,' ',rsm_via_self.last_name))
              ELSE TRIM(CONCAT(rsm_via_dm.first_name,' ',rsm_via_dm.last_name)) END AS varchar(200)) AS rsm_name,

    /* AD level: resolved through the RSM's OWN ad pointer */
    CAST(CASE WHEN u.role='ad'  THEN u.id
              WHEN u.role='rsm' THEN ad_via_self.id
              WHEN u.role='dm'  THEN ad_via_dm_rsm.id
              ELSE ad_via_se_rsm.id END AS varchar(50))         AS ad_id,
    CAST(CASE WHEN u.role='ad'  THEN TRIM(CONCAT(u.first_name,' ',u.last_name))
              WHEN u.role='rsm' THEN TRIM(CONCAT(ad_via_self.first_name,' ',ad_via_self.last_name))
              WHEN u.role='dm'  THEN TRIM(CONCAT(ad_via_dm_rsm.first_name,' ',ad_via_dm_rsm.last_name))
              ELSE TRIM(CONCAT(ad_via_se_rsm.first_name,' ',ad_via_se_rsm.last_name)) END AS varchar(200)) AS ad_name

FROM dbo.[User] u

/* SE → DM */
LEFT JOIN dbo.[User] dm_u
       ON dm_u.workforce_id = u.dm AND dm_u.role = 'dm'

/* SE → DM → RSM (resolve through DM's own rsm, not SE's cached rsm) */
LEFT JOIN dbo.[User] rsm_via_dm
       ON rsm_via_dm.workforce_id = dm_u.rsm AND rsm_via_dm.role = 'rsm'

/* If u IS a DM, walk to its own RSM */
LEFT JOIN dbo.[User] rsm_via_self
       ON rsm_via_self.workforce_id = u.rsm AND rsm_via_self.role = 'rsm'

/* SE → DM → RSM → AD (through RSM's own ad) */
LEFT JOIN dbo.[User] ad_via_se_rsm
       ON ad_via_se_rsm.workforce_id = rsm_via_dm.ad AND ad_via_se_rsm.role = 'ad'

/* If u is a DM, walk its RSM's ad */
LEFT JOIN dbo.[User] ad_via_dm_rsm
       ON ad_via_dm_rsm.workforce_id = rsm_via_self.ad AND ad_via_dm_rsm.role = 'ad'

/* If u is an RSM, walk its own ad */
LEFT JOIN dbo.[User] ad_via_self
       ON ad_via_self.workforce_id = u.ad AND ad_via_self.role = 'ad';
