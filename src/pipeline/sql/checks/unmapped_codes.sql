-- Mapping gate (doc 04 §4.2, D-021): every local account and cost centre in the staged data
-- must have a row in the maintained mapping tables. Returns all unmapped codes at once.

SELECT DISTINCT 'account' AS code_type, s.site, s.local_account_code AS local_code, s.source_file
FROM stg_all_sites AS s
LEFT JOIN ref_account_mapping AS m
    ON m.site = s.site AND m.local_account_code = s.local_account_code
WHERE m.site IS NULL

UNION ALL

SELECT DISTINCT 'cost centre', s.site, s.local_cost_centre, s.source_file
FROM stg_all_sites AS s
LEFT JOIN ref_cost_centre_mapping AS m
    ON m.site = s.site AND m.local_cost_centre = s.local_cost_centre
WHERE m.site IS NULL

ORDER BY ALL;
