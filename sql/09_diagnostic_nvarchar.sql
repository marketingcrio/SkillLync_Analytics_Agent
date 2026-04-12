/*  ============================================================
    DIAGNOSTIC: Find nvarchar columns in prep views
    ------------------------------------------------------------
    Run this if the CTAS fails with "nvarchar(4000) not supported".
    It checks every column in every prep view for nvarchar types.
    ============================================================ */

SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'prep'
  AND DATA_TYPE LIKE '%nvarchar%'
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;
