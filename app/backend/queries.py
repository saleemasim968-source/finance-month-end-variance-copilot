"""Read-only queries that feed the dashboard (WBS 6, FR-15).

Every figure the frontend shows comes from these functions, which read the analytics
tables (an_*) and quality tables (dq_*) as they are. Nothing is recalculated here except
sums over the selected slice, so dashboard values equal the variance table (doc 03 §7, WBS 6).

Variance views use posted rows only, so that plan + volume effect + spend effect = actual
holds; the one row whose actual is not posted is reported separately.
"""


def _rows(con, sql, params=()):
    cursor = con.execute(sql, list(params))
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _period_filter(period):
    """SQL condition and parameters for 'all' or one period."""
    return ("TRUE", []) if period in (None, "", "all") else ("period = ?", [period])


def meta(con):
    return {
        "sites": [r["site"] for r in _rows(con, "SELECT DISTINCT site FROM an_variance ORDER BY site")],
        "periods": [r["period"] for r in _rows(con, "SELECT DISTINCT period FROM an_variance ORDER BY period")],
        "group_accounts": [r["group_account"] for r in _rows(
            con, "SELECT DISTINCT group_account FROM an_variance ORDER BY group_account")],
        "variable_shares": {r["group_account"]: float(r["variable_share"]) for r in _rows(
            con, "SELECT group_account, variable_share FROM ref_cost_behaviour ORDER BY group_account")},
    }


def not_posted(con, period=None):
    where, params = _period_filter(period)
    return _rows(con, f"""
        SELECT site, period, group_area, group_account, local_cost_centre, local_account_code, plan_eur
        FROM an_variance WHERE NOT actual_posted AND {where} ORDER BY site, period
    """, params)


def overview(con, period=None):
    where, params = _period_filter(period)
    totals = _rows(con, f"""
        SELECT SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur, SUM(total_var) AS total_var,
               SUM(volume_effect) AS volume_effect, SUM(spend_effect) AS spend_effect
        FROM an_variance WHERE actual_posted AND {where}
    """, params)[0]
    flags = _rows(con, f"""
        SELECT item_type, COUNT(*) AS n FROM an_flagged_items WHERE {where} GROUP BY item_type
    """, params)
    by_site = _rows(con, f"""
        SELECT site, SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur, SUM(total_var) AS total_var,
               SUM(volume_effect) AS volume_effect, SUM(spend_effect) AS spend_effect,
               SUM(total_var) / SUM(plan_eur) AS total_var_pct,
               COUNT(*) FILTER (WHERE spend_flag) AS spend_flags
        FROM an_variance WHERE actual_posted AND {where}
        GROUP BY site ORDER BY site
    """, params)
    volume_flags = {r["site"]: r["n"] for r in _rows(con, f"""
        SELECT site, COUNT(*) AS n FROM an_volume_flags WHERE volume_flag AND {where} GROUP BY site
    """, params)}
    for row in by_site:
        row["volume_flags"] = volume_flags.get(row["site"], 0)
    monthly = _rows(con, """
        SELECT period, SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur, SUM(total_var) AS total_var,
               SUM(volume_effect) AS volume_effect, SUM(spend_effect) AS spend_effect
        FROM an_variance WHERE actual_posted GROUP BY period ORDER BY period
    """)
    return {"totals": totals, "flags": {r["item_type"]: r["n"] for r in flags},
            "by_site": by_site, "monthly": monthly, "not_posted": not_posted(con, period)}


def sites(con, period=None):
    where, params = _period_filter(period)
    cost_per_wafer = _rows(con, f"""
        SELECT site, SUM(plan_cost_eur) / SUM(plan_wafers) AS cpw_plan,
               SUM(actual_cost_eur) / SUM(actual_wafers) AS cpw_actual,
               SUM(plan_wafers) AS plan_wafers, SUM(actual_wafers) AS actual_wafers,
               BOOL_AND(complete) AS complete
        FROM an_cost_per_wafer WHERE {where} GROUP BY site ORDER BY site
    """, params)
    trend = _rows(con, """
        SELECT site, period, cpw_plan, cpw_actual, complete FROM an_cost_per_wafer ORDER BY site, period
    """)
    heatmap = _rows(con, f"""
        SELECT site, group_account, SUM(plan_eur) AS plan_eur, SUM(total_var) AS total_var,
               SUM(total_var) / SUM(plan_eur) AS total_var_pct
        FROM an_variance WHERE actual_posted AND {where}
        GROUP BY site, group_account ORDER BY site, group_account
    """, params)
    return {"cost_per_wafer": cost_per_wafer, "trend": trend, "heatmap": heatmap}


def bridge(con, site=None, period=None):
    """Plan -> volume effect -> spend effect per group account -> actual."""
    where, params = _period_filter(period)
    if site not in (None, "", "all"):
        where += " AND site = ?"
        params.append(site)
    totals = _rows(con, f"""
        SELECT SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur, SUM(volume_effect) AS volume_effect
        FROM an_variance WHERE actual_posted AND {where}
    """, params)[0]
    by_account = _rows(con, f"""
        SELECT group_account, SUM(spend_effect) AS spend_effect, SUM(volume_effect) AS volume_effect,
               SUM(total_var) AS total_var
        FROM an_variance WHERE actual_posted AND {where}
        GROUP BY group_account ORDER BY group_account
    """, params)
    rows = _rows(con, f"""
        SELECT site, period, group_area, group_account, local_cost_centre, local_account_code,
               plan_eur, flexed_eur, actual_eur, total_var, volume_effect, spend_effect, spend_pct, spend_flag,
               actual_posted, source_file, source_line_plan, source_line_actual
        FROM an_variance WHERE {where}
        ORDER BY ABS(COALESCE(total_var, 0)) DESC, site, period, group_area, group_account
    """, params)
    return {"totals": totals, "by_account": by_account, "rows": rows}


def data_quality(con):
    return {
        "raw_rows": _rows(con, """
            SELECT 'FAB_NORTH' AS site, COUNT(*) AS n FROM raw_fab_north
            UNION ALL SELECT 'FAB_ALPS', COUNT(*) FROM raw_fab_alps
            UNION ALL SELECT 'FAB_ASIA', COUNT(*) FROM raw_fab_asia
        """),
        "harmonised_rows": _rows(con, "SELECT COUNT(*) AS n FROM rpt_harmonised")[0]["n"],
        "mapped_rows": _rows(con, """
            SELECT COUNT(*) AS n FROM rpt_harmonised WHERE group_area IS NOT NULL AND group_account IS NOT NULL
        """)[0]["n"],
        "findings": _rows(con, "SELECT * FROM dq_report ORDER BY finding, site, period"),
        "reconciliation": _rows(con, "SELECT * FROM dq_reconciliation ORDER BY site, period, measure DESC"),
    }


def flagged_items(con):
    return _rows(con, "SELECT * FROM an_flagged_items ORDER BY item_type, site, period, group_area")
