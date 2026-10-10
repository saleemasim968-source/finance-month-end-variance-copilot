-- FAB_ASIA: GL export in MYR, period as Mon-YY, plan (BUD) and actual (ACT) on separate lines.
-- Each line is converted at the monthly rate (EUR = MYR / myr_per_eur) and rounded to cents,
-- then the BUD and ACT lines are combined into one row with both source lines kept (C-001).
-- A missing FX rate or an unknown version stops the run instead of silently dropping data.

CREATE OR REPLACE TABLE stg_fab_asia_lines AS
SELECT
    'FAB_ASIA'                                              AS site,
    strftime(strptime(r.Period, '%b-%y'), '%Y-%m')          AS period,
    r.CC                                                    AS local_cost_centre,
    r."GL Account"                                          AS local_account_code,
    CASE WHEN r.Version IN ('BUD', 'ACT') THEN r.Version
         ELSE error('Unknown version "' || r.Version || '" in ' || r.source_file
                    || ' line ' || r.source_line) END       AS version,
    CAST(r.Amount AS DECIMAL(18, 2))                        AS amount_myr,
    CASE WHEN fx.myr_per_eur IS NULL
         THEN error('No FX rate for period ' || r.Period)
         ELSE CAST(round(CAST(r.Amount AS DECIMAL(18, 2)) / fx.myr_per_eur, 2) AS DECIMAL(18, 2))
    END                                                     AS amount_eur,
    r.source_file,
    r.source_line,
    ROW_NUMBER() OVER (
        PARTITION BY r.Period, r.CC, r."GL Account", r."GL Description", r.Version, r.Amount
        ORDER BY r.source_line
    ) AS occurrence
FROM raw_fab_asia AS r
LEFT JOIN stg_fx_rates AS fx
    ON fx.period = strftime(strptime(r.Period, '%b-%y'), '%Y-%m');

CREATE OR REPLACE TABLE stg_fab_asia AS
SELECT
    site, period, local_cost_centre, local_account_code,
    SUM(amount_eur)  FILTER (WHERE version = 'BUD') AS plan_eur,
    SUM(amount_eur)  FILTER (WHERE version = 'ACT') AS actual_eur,
    source_file,
    MIN(source_line) FILTER (WHERE version = 'BUD') AS source_line_plan,
    MIN(source_line) FILTER (WHERE version = 'ACT') AS source_line_actual
FROM stg_fab_asia_lines
WHERE occurrence = 1
GROUP BY site, period, local_cost_centre, local_account_code, source_file;
