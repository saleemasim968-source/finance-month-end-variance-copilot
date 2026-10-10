-- Reference inputs needed by the site staging: monthly FX rates and wafer volumes.
-- strptime() fails loudly on any period that is not in the expected format.

CREATE OR REPLACE TABLE stg_fx_rates AS
SELECT
    strftime(strptime(period, '%Y-%m'), '%Y-%m') AS period,
    CAST(myr_per_eur AS DECIMAL(10, 4))          AS myr_per_eur
FROM raw_fx_rates;

CREATE OR REPLACE TABLE stg_wafer_volumes AS
SELECT
    site,
    strftime(strptime(period, '%Y-%m'), '%Y-%m') AS period,
    CAST(plan_wafers AS INTEGER)                 AS plan_wafers,
    CAST(actual_wafers AS INTEGER)               AS actual_wafers,
    source_file,
    source_line
FROM raw_wafer_volumes;
