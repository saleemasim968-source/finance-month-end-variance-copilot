-- Data-quality report (doc 04 §4.2, FR-06): one row per finding.
--   duplicate_removed  an exact duplicate source line, left out of the harmonised table
--   actual_not_posted  a missing actual; the row is kept and excluded from variance flags

CREATE OR REPLACE TABLE dq_report AS
SELECT
    'duplicate_removed' AS finding,
    site, period, local_cost_centre, local_account_code, source_file, source_line,
    'Exact duplicate of an earlier line; removed and logged as a correction' AS detail
FROM (
    SELECT DISTINCT site, period, local_cost_centre, local_account_code, source_file, source_line
    FROM stg_all_lines
    WHERE occurrence > 1
)

UNION ALL

SELECT
    'actual_not_posted',
    site, period, local_cost_centre, local_account_code, source_file, source_line_actual,
    'Actual value missing; row kept and excluded from variance flags'
FROM rpt_harmonised
WHERE NOT actual_posted

ORDER BY finding, site, period, source_line;
