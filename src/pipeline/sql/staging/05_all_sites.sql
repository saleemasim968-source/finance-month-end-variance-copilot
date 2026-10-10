-- The three site tables in one common layout, input to the mapping gate and the reporting table.

CREATE OR REPLACE VIEW stg_all_sites AS
SELECT * FROM stg_fab_north
UNION ALL BY NAME
SELECT * FROM stg_fab_alps
UNION ALL BY NAME
SELECT * FROM stg_fab_asia;

-- Every source line as one amount per measure (plan or actual), duplicates included.
-- Used for the source totals in the reconciliation and for the duplicate corrections.

CREATE OR REPLACE VIEW stg_all_lines AS
SELECT site, period, local_cost_centre, local_account_code, source_file, source_line, occurrence,
       'plan' AS measure, plan_eur AS amount_eur
FROM stg_fab_north_lines
UNION ALL
SELECT site, period, local_cost_centre, local_account_code, source_file, source_line, occurrence,
       'actual', actual_eur
FROM stg_fab_north_lines
UNION ALL
SELECT site, period, local_cost_centre, local_account_code, source_file, source_line, occurrence,
       'plan', plan_eur
FROM stg_fab_alps_lines
UNION ALL
SELECT site, period, local_cost_centre, local_account_code, source_file, source_line, occurrence,
       'actual', actual_eur
FROM stg_fab_alps_lines
UNION ALL
SELECT site, period, local_cost_centre, local_account_code, source_file, source_line, occurrence,
       CASE version WHEN 'BUD' THEN 'plan' ELSE 'actual' END, amount_eur
FROM stg_fab_asia_lines;
