-- Reconciliation (doc 04 §4.2, C-002, D-014): per site, period and measure,
--   source total = harmonised total + logged corrections, within the configured tolerance.
-- The source total sums every source line in EUR, duplicates included; the corrections
-- are the amounts of the removed duplicate lines. Missing actuals add nothing to either side.

CREATE OR REPLACE TABLE dq_reconciliation AS
WITH source_totals AS (
    SELECT site, period, measure, SUM(amount_eur) AS source_total_eur
    FROM stg_all_lines
    GROUP BY site, period, measure
),
harmonised_totals AS (
    SELECT site, period, 'plan' AS measure, SUM(plan_eur) AS harmonised_total_eur
    FROM rpt_harmonised GROUP BY site, period
    UNION ALL
    SELECT site, period, 'actual', SUM(actual_eur)
    FROM rpt_harmonised GROUP BY site, period
),
corrections AS (
    SELECT site, period, measure, SUM(amount_eur) AS corrections_eur
    FROM stg_all_lines
    WHERE occurrence > 1
    GROUP BY site, period, measure
),
compared AS (
    SELECT
        site, period, measure,
        COALESCE(s.source_total_eur, 0)     AS source_total_eur,
        COALESCE(h.harmonised_total_eur, 0) AS harmonised_total_eur,
        COALESCE(c.corrections_eur, 0)      AS corrections_eur
    FROM source_totals AS s
    FULL JOIN harmonised_totals AS h USING (site, period, measure)
    LEFT JOIN corrections AS c USING (site, period, measure)
)
SELECT
    *,
    source_total_eur - harmonised_total_eur - corrections_eur AS difference_eur,
    (source_total_eur - harmonised_total_eur - corrections_eur) / NULLIF(source_total_eur, 0) AS difference_pct,
    abs(source_total_eur - harmonised_total_eur - corrections_eur)
        <= getvariable('reconciliation_tolerance_pct') * abs(source_total_eur) AS passed
FROM compared
ORDER BY site, period, measure DESC;
