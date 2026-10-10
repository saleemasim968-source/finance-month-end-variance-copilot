"""Context builder (WBS 5.1, FR-11, NFR-04).

Builds the complete, pre-rounded set of figures for one flagged item. This context is the
only information the language model receives, and it is also the list of numbers that the
number check accepts in the commentary. Amounts are in thousands of EUR (whole numbers),
percentages have one decimal (doc 04 §4.5). Only aggregated figures are included: no
source file names, line numbers or person-level data.
"""

MONTHS_EN = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]


def period_label(period, language="en"):
    year, month = period.split("-")
    months = MONTHS_DE if language == "de" else MONTHS_EN
    return f"{months[int(month) - 1]} {year}"


def teur(amount_eur):
    """EUR -> whole thousands of EUR."""
    return int(round(amount_eur / 1000))


def pct(fraction):
    """Fraction -> percentage with one decimal."""
    return round(fraction * 100, 1)


def _one(con, sql, params):
    cursor = con.execute(sql, params)
    columns = [d[0] for d in cursor.description]
    row = cursor.fetchone()
    if row is None:
        raise KeyError(f"No data for {params}")
    return dict(zip(columns, row))


def _spend_figures(con, item):
    row = _one(con, """
        SELECT plan_eur, actual_eur, flexed_eur, total_var, volume_effect, spend_effect, spend_pct,
               local_cost_centre, local_account_code
        FROM an_variance
        WHERE site = ? AND period = ? AND group_area = ? AND group_account = ?
    """, [item["site"], item["period"], item["group_area"], item["group_account"]])
    figures = {
        "plan_teur": teur(row["plan_eur"]),
        "actual_teur": teur(row["actual_eur"]),
        "flexed_budget_teur": teur(row["flexed_eur"]),
        "total_variance_teur": teur(row["total_var"]),
        "volume_effect_teur": teur(row["volume_effect"]),
        "spend_effect_teur": teur(row["spend_effect"]),
        "spend_effect_pct_of_flexed_budget": pct(row["spend_pct"]),
    }
    codes = {"local_cost_centre": row["local_cost_centre"], "local_account_code": row["local_account_code"]}
    return figures, codes


def _volume_figures(con, item):
    volume = _one(con, """
        SELECT plan_wafers, actual_wafers, volume_dev_pct FROM an_volume_flags WHERE site = ? AND period = ?
    """, [item["site"], item["period"]])
    totals = _one(con, """
        SELECT SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur, SUM(total_var) AS total_var,
               SUM(volume_effect) AS volume_effect, SUM(spend_effect) AS spend_effect
        FROM an_variance WHERE site = ? AND period = ? AND actual_posted
    """, [item["site"], item["period"]])
    cost_per_wafer = _one(con, """
        SELECT cpw_plan, cpw_actual FROM an_cost_per_wafer WHERE site = ? AND period = ?
    """, [item["site"], item["period"]])
    figures = {
        "plan_wafers": int(volume["plan_wafers"]),
        "actual_wafers": int(volume["actual_wafers"]),
        "wafer_deviation_pct": pct(volume["volume_dev_pct"]),
        "site_plan_cost_teur": teur(totals["plan_eur"]),
        "site_actual_cost_teur": teur(totals["actual_eur"]),
        "site_total_variance_teur": teur(totals["total_var"]),
        "site_volume_effect_teur": teur(totals["volume_effect"]),
        "site_spend_effect_teur": teur(totals["spend_effect"]),
        "cost_per_wafer_plan_eur": int(round(cost_per_wafer["cpw_plan"])),
        "cost_per_wafer_actual_eur": int(round(cost_per_wafer["cpw_actual"])),
    }
    return figures, {}


def build_context(con, item_id, owner_cause=None):
    """Context for one flagged item from an_flagged_items, read from the warehouse connection."""
    item = _one(con, "SELECT * FROM an_flagged_items WHERE item_id = ?", [item_id])
    if item["item_type"] == "spend":
        figures, codes = _spend_figures(con, item)
    else:
        figures, codes = _volume_figures(con, item)
    return {
        "item_id": item_id,
        "item_type": item["item_type"],
        "site": item["site"],
        "period": item["period"],
        "group_area": item["group_area"],
        "group_account": item["group_account"],
        **codes,
        "figures": figures,
        "owner_cause": owner_cause or None,
    }
