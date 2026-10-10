-- FAB_ALPS: German layout, decimal comma, amounts in thousands of EUR, period as MM.YYYY.
-- TEUR values carry three decimals, so multiplying by 1,000 gives exact euro amounts.
-- An empty Ist_TEUR becomes NULL: the row is kept as "actual not posted" (doc 04 §4.2).

CREATE OR REPLACE TABLE stg_fab_alps_lines AS
SELECT
    'FAB_ALPS'                                         AS site,
    strftime(strptime(Periode, '%m.%Y'), '%Y-%m')      AS period,
    Kostenstelle                                       AS local_cost_centre,
    Kontonummer                                        AS local_account_code,
    CAST(CAST(replace(Plan_TEUR, ',', '.') AS DECIMAL(18, 3)) * 1000 AS DECIMAL(18, 2)) AS plan_eur,
    CAST(CAST(replace(NULLIF(trim(Ist_TEUR), ''), ',', '.') AS DECIMAL(18, 3)) * 1000
         AS DECIMAL(18, 2))                            AS actual_eur,
    source_file,
    source_line,
    ROW_NUMBER() OVER (
        PARTITION BY Periode, Kostenstelle, Kontonummer, Kontobezeichnung, Plan_TEUR, Ist_TEUR
        ORDER BY source_line
    ) AS occurrence
FROM raw_fab_alps;

CREATE OR REPLACE TABLE stg_fab_alps AS
SELECT
    site, period, local_cost_centre, local_account_code, plan_eur, actual_eur,
    source_file,
    source_line AS source_line_plan,
    source_line AS source_line_actual
FROM stg_fab_alps_lines
WHERE occurrence = 1;
