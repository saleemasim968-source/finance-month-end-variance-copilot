-- FAB_NORTH: English layout, amounts already in EUR, period already YYYY-MM.
-- stg_fab_north_lines keeps one typed row per source line; occurrence > 1 marks an
-- exact duplicate of an earlier line (doc 04 §4.2), which staging then leaves out.

CREATE OR REPLACE TABLE stg_fab_north_lines AS
SELECT
    'FAB_NORTH'                                       AS site,
    strftime(strptime(period, '%Y-%m'), '%Y-%m')      AS period,
    cost_center                                       AS local_cost_centre,
    account_code                                      AS local_account_code,
    CAST(plan AS DECIMAL(18, 2))                      AS plan_eur,
    CAST(NULLIF(trim(actual), '') AS DECIMAL(18, 2))  AS actual_eur,
    source_file,
    source_line,
    ROW_NUMBER() OVER (
        PARTITION BY period, cost_center, account_code, account_name, plan, actual
        ORDER BY source_line
    ) AS occurrence
FROM raw_fab_north;

CREATE OR REPLACE TABLE stg_fab_north AS
SELECT
    site, period, local_cost_centre, local_account_code, plan_eur, actual_eur,
    source_file,
    source_line AS source_line_plan,
    source_line AS source_line_actual
FROM stg_fab_north_lines
WHERE occurrence = 1;
