-- Harmonised reporting table (doc 04 §4.1, with C-001): one row per site, period, group area
-- and group account. Local codes stay on every row (FR-05) next to the group codes (FR-04),
-- and both source lines are kept for traceability (NFR-03).
-- Runs only after the mapping gate has passed, so the inner joins cannot drop rows.

CREATE OR REPLACE TABLE rpt_harmonised AS
SELECT
    s.site,
    s.period,
    c.group_area,
    a.group_account,
    s.local_cost_centre,
    s.local_account_code,
    s.plan_eur,
    s.actual_eur,
    s.actual_eur IS NOT NULL AS actual_posted,
    s.source_file,
    s.source_line_plan,
    s.source_line_actual
FROM stg_all_sites AS s
JOIN ref_cost_centre_mapping AS c
    ON c.site = s.site AND c.local_cost_centre = s.local_cost_centre
JOIN ref_account_mapping AS a
    ON a.site = s.site AND a.local_account_code = s.local_account_code
ORDER BY s.site, s.period, c.group_area, a.group_account;
