/*  ============================================================
    DIMENSION: dim.Calendar
    ------------------------------------------------------------
    Shared date dimension for PBI cross-filtering.
    Both FinalTable and CallDetail relate to this via date columns.

    Relationships in PBI:
      dim.Calendar[calendar_date] 1──* FinalTable[activity_month_start]
      dim.Calendar[calendar_date] 1──* CallDetail[call_month_start]

    Both are Many-to-One (date dim is the "one" side).
    This avoids the Many-to-Many problem between fact tables.
    ============================================================ */

DROP TABLE IF EXISTS dim.Calendar;

CREATE TABLE dim.Calendar
AS
SELECT
    calendar_date,
    YEAR(calendar_date)                          AS cal_year,
    MONTH(calendar_date)                         AS cal_month,
    DAY(calendar_date)                           AS cal_day,
    CAST(DATENAME(MONTH, calendar_date) AS varchar(20))
                                                 AS cal_month_name,
    DATEFROMPARTS(YEAR(calendar_date), MONTH(calendar_date), 1)
                                                 AS cal_month_start,
    CAST(CASE
        WHEN MONTH(calendar_date) <= 3 THEN 'Q1'
        WHEN MONTH(calendar_date) <= 6 THEN 'Q2'
        WHEN MONTH(calendar_date) <= 9 THEN 'Q3'
        ELSE 'Q4'
    END AS varchar(5))                           AS cal_quarter,
    CAST(CONCAT('FY', CASE
        WHEN MONTH(calendar_date) >= 4
            THEN YEAR(calendar_date) + 1
        ELSE YEAR(calendar_date)
    END) AS varchar(10))                         AS cal_fy
FROM (
    SELECT CAST(DATEADD(DAY, n, '2025-01-01') AS DATE) AS calendar_date
    FROM (
        SELECT TOP 1096 ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM dbo.ActivityType a
        CROSS JOIN dbo.ActivityType b
    ) nums
) dates
WHERE calendar_date <= '2027-12-31';
