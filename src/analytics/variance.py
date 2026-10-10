"""Variance analytics (WBS 4): variance, volume/spend decomposition, flags, cost per wafer.

Reads the harmonised table, cost behaviour and wafer volumes from the warehouse and writes
four tables back (doc 04 §4.3-4.4, architecture §5.5):
- an_variance        one row per harmonised row, with flexed budget, effects and spend flag
- an_volume_flags    one row per site and period
- an_cost_per_wafer  one row per site and period
- an_flagged_items   the items that need commentary (spend and volume flags together)

Sign convention: a positive variance means cost above plan, which is unfavourable.
"""

import pandas as pd


def calculate_variance(harmonised, behaviour, volumes, spend_abs_eur, spend_pct):
    """Flexed budget, total variance, volume effect, spend effect and spend flag per row."""
    df = harmonised.merge(behaviour, on="group_account", how="left", validate="many_to_one")
    df = df.merge(volumes[["site", "period", "plan_wafers", "actual_wafers"]],
                  on=["site", "period"], how="left", validate="many_to_one")
    if df["variable_share"].isna().any() or df["plan_wafers"].isna().any():
        raise ValueError("Missing cost behaviour or wafer volume for some harmonised rows")

    df["volume_ratio"] = df["actual_wafers"] / df["plan_wafers"]
    df["flexed_eur"] = df["plan_eur"] * ((1 - df["variable_share"]) + df["variable_share"] * df["volume_ratio"])
    df["total_var"] = df["actual_eur"] - df["plan_eur"]           # NULL where actual not posted (C-003)
    df["volume_effect"] = df["flexed_eur"] - df["plan_eur"]       # calculated for every row
    df["spend_effect"] = df["actual_eur"] - df["flexed_eur"]      # NULL where actual not posted
    df["spend_pct"] = df["spend_effect"] / df["flexed_eur"]
    df["spend_flag"] = (
        df["actual_posted"]
        & (df["spend_effect"].abs() >= spend_abs_eur)
        & (df["spend_pct"].abs() >= spend_pct)
    ).fillna(False).astype(bool)
    return df


def calculate_volume_flags(volumes, volume_pct):
    df = volumes[["site", "period", "plan_wafers", "actual_wafers"]].copy()
    df["volume_ratio"] = df["actual_wafers"] / df["plan_wafers"]
    df["volume_dev_pct"] = df["volume_ratio"] - 1
    df["volume_flag"] = df["volume_dev_pct"].abs() >= volume_pct
    return df


def calculate_cost_per_wafer(variance):
    """Plan and actual cost per wafer by site and period. Incomplete if any actual is missing."""
    grouped = variance.groupby(["site", "period"], as_index=False).agg(
        plan_cost_eur=("plan_eur", "sum"),
        actual_cost_eur=("actual_eur", "sum"),
        plan_wafers=("plan_wafers", "first"),
        actual_wafers=("actual_wafers", "first"),
        complete=("actual_posted", "all"),
    )
    grouped["cpw_plan"] = grouped["plan_cost_eur"] / grouped["plan_wafers"]
    grouped["cpw_actual"] = grouped["actual_cost_eur"] / grouped["actual_wafers"]
    return grouped


def list_flagged_items(variance, volume_flags):
    """One row per item that needs commentary, with a stable item_id used by the review store."""
    spend = variance[variance["spend_flag"]].copy()
    spend["item_type"] = "spend"
    spend["item_id"] = ("spend|" + spend["site"] + "|" + spend["period"] + "|"
                        + spend["group_area"] + "|" + spend["group_account"])

    volume = volume_flags[volume_flags["volume_flag"]].copy()
    volume["item_type"] = "volume"
    volume["item_id"] = "volume|" + volume["site"] + "|" + volume["period"]
    volume["group_area"] = None
    volume["group_account"] = None

    columns = ["item_id", "item_type", "site", "period", "group_area", "group_account"]
    items = pd.concat([spend[columns], volume[columns]], ignore_index=True)
    return items.sort_values(["item_type", "site", "period", "group_area"], ignore_index=True)


def run(con, materiality):
    """Read the harmonised data from con, calculate everything and write the an_ tables."""
    harmonised = con.execute("SELECT * FROM rpt_harmonised ORDER BY site, period, group_area, group_account").df()
    behaviour = con.execute(
        "SELECT group_account, CAST(variable_share AS DOUBLE) AS variable_share FROM ref_cost_behaviour").df()
    volumes = con.execute("SELECT * FROM stg_wafer_volumes ORDER BY site, period").df()

    for column in ("plan_eur", "actual_eur"):
        harmonised[column] = harmonised[column].astype("float64")

    variance = calculate_variance(harmonised, behaviour, volumes,
                                  materiality["spend_abs_eur"], materiality["spend_pct"])
    volume_flags = calculate_volume_flags(volumes, materiality["volume_pct"])
    cost_per_wafer = calculate_cost_per_wafer(variance)
    flagged = list_flagged_items(variance, volume_flags)

    for table, frame in {
        "an_variance": variance,
        "an_volume_flags": volume_flags,
        "an_cost_per_wafer": cost_per_wafer,
        "an_flagged_items": flagged,
    }.items():
        con.register("frame", frame)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM frame")
        con.unregister("frame")

    return {"spend_flags": int(variance["spend_flag"].sum()),
            "volume_flags": int(volume_flags["volume_flag"].sum())}
