"""Quality gate for WBS 4, variance analytics (document 03 section 7).

Volume effect + spend effect = total variance on every row, and exactly the three planted
business events are flagged (FR-07 to FR-10, SC-4).
"""

import pandas as pd
import pytest

from src.analytics import variance

MATERIALITY = {"spend_abs_eur": 50_000, "spend_pct": 0.05, "volume_pct": 0.05}


def query(con, sql):
    return con.execute(sql).fetchall()


# --- Unit tests on a hand-calculated example -------------------------------------------------

def example_inputs():
    harmonised = pd.DataFrame([
        {"site": "S", "period": "2026-01", "group_area": "A", "group_account": "Materials",
         "plan_eur": 100_000.0, "actual_eur": 95_000.0, "actual_posted": True},
        {"site": "S", "period": "2026-01", "group_area": "A", "group_account": "Personnel",
         "plan_eur": 200_000.0, "actual_eur": None, "actual_posted": False},
    ])
    behaviour = pd.DataFrame([{"group_account": "Materials", "variable_share": 0.9},
                              {"group_account": "Personnel", "variable_share": 0.0}])
    volumes = pd.DataFrame([{"site": "S", "period": "2026-01", "plan_wafers": 1000, "actual_wafers": 800}])
    return harmonised, behaviour, volumes


def test_flexed_budget_and_effects_match_a_hand_calculation():
    # Volume ratio 0.8. Flexed = 100,000 x (0.1 + 0.9 x 0.8) = 82,000.
    # Volume effect = 82,000 - 100,000 = -18,000. Spend effect = 95,000 - 82,000 = 13,000.
    df = variance.calculate_variance(*example_inputs(), **{k: MATERIALITY[k] for k in ("spend_abs_eur", "spend_pct")})
    row = df.iloc[0]
    assert row["flexed_eur"] == pytest.approx(82_000)
    assert row["total_var"] == pytest.approx(-5_000)
    assert row["volume_effect"] == pytest.approx(-18_000)
    assert row["spend_effect"] == pytest.approx(13_000)
    assert not row["spend_flag"]  # 13,000 is below the EUR 50,000 threshold


def test_missing_actual_has_volume_effect_but_no_spend_effect_or_flag():
    df = variance.calculate_variance(*example_inputs(), 50_000, 0.05)
    row = df.iloc[1]
    assert row["volume_effect"] == pytest.approx(0)  # personnel is fully fixed
    assert pd.isna(row["total_var"]) and pd.isna(row["spend_effect"])
    assert not row["spend_flag"]


def test_spend_flag_needs_both_the_amount_and_the_percentage():
    harmonised, behaviour, volumes = example_inputs()
    # Spend effect 13,000 = 15.9 % of flexed: passes the percentage, fails the amount.
    assert not variance.calculate_variance(harmonised, behaviour, volumes, 50_000, 0.05)["spend_flag"].iloc[0]
    # Lower the amount threshold: now both conditions hold.
    assert variance.calculate_variance(harmonised, behaviour, volumes, 10_000, 0.05)["spend_flag"].iloc[0]
    # Raise the percentage threshold above 15.9 %: no flag.
    assert not variance.calculate_variance(harmonised, behaviour, volumes, 10_000, 0.20)["spend_flag"].iloc[0]


# --- Tests on the real generated data ----------------------------------------------------------

def test_fr07_total_variance_is_actual_minus_plan(warehouse):
    con, _ = warehouse
    worst = query(con, "SELECT MAX(ABS(total_var - (actual_eur - plan_eur))) FROM an_variance WHERE actual_posted")
    assert worst[0][0] < 1e-6
    assert query(con, "SELECT COUNT(*) FROM an_variance")[0][0] == 648


def test_fr08_volume_plus_spend_equals_total_on_every_posted_row(warehouse):
    con, _ = warehouse
    rows, worst = query(con, """
        SELECT COUNT(*), MAX(ABS(volume_effect + spend_effect - total_var))
        FROM an_variance WHERE actual_posted
    """)[0]
    assert rows == 647
    assert worst < 1e-6


def test_fr09_exactly_the_three_planted_spend_events_are_flagged(warehouse):
    con, _ = warehouse
    flagged = query(con, """
        SELECT site, period, group_area, group_account FROM an_variance WHERE spend_flag ORDER BY ALL
    """)
    assert flagged == [
        ("FAB_ALPS", "2026-07", "Facilities", "Energy"),
        ("FAB_ALPS", "2026-08", "Facilities", "Energy"),
        ("FAB_NORTH", "2026-05", "Lithography", "Maintenance"),
    ]


def test_fr09_exactly_the_three_planted_volume_events_are_flagged(warehouse):
    con, _ = warehouse
    flagged = query(con, "SELECT site, period FROM an_volume_flags WHERE volume_flag ORDER BY ALL")
    assert flagged == [("FAB_ASIA", "2026-07"), ("FAB_ASIA", "2026-08"), ("FAB_ASIA", "2026-09")]


def test_planted_events_have_the_expected_size(warehouse):
    con, _ = warehouse
    tool_down = query(con, """
        SELECT spend_effect FROM an_variance
        WHERE site = 'FAB_NORTH' AND period = '2026-05' AND group_area = 'Lithography'
          AND group_account = 'Maintenance'
    """)[0][0]
    assert 440_000 < tool_down < 520_000  # "about EUR 480,000"
    spikes = [pct for (pct,) in query(con, """
        SELECT spend_pct FROM an_variance
        WHERE site = 'FAB_ALPS' AND period IN ('2026-07', '2026-08') AND group_account = 'Energy'
    """)]
    assert len(spikes) == 8 and all(0.19 < pct < 0.25 for pct in spikes)  # "about 22 % in all areas"
    shortfalls = [dev for (dev,) in query(con, "SELECT volume_dev_pct FROM an_volume_flags WHERE volume_flag")]
    assert all(-0.16 < dev < -0.12 for dev in shortfalls)  # "about 14 % below plan"


def test_flagged_items_list_has_six_items_with_unique_ids(warehouse):
    con, _ = warehouse
    items = query(con, "SELECT item_id, item_type FROM an_flagged_items")
    assert len(items) == len({item_id for item_id, _ in items}) == 6
    assert sorted(t for _, t in items) == ["spend"] * 3 + ["volume"] * 3


def test_fr10_cost_per_wafer_equals_total_cost_divided_by_wafers(warehouse):
    con, _ = warehouse
    expected = dict(((s, p), (plan, actual)) for s, p, plan, actual in query(con, """
        SELECT v.site, v.period, SUM(v.plan_eur) / w.plan_wafers, SUM(v.actual_eur) / w.actual_wafers
        FROM an_variance v JOIN stg_wafer_volumes w USING (site, period)
        GROUP BY v.site, v.period, w.plan_wafers, w.actual_wafers
    """))
    rows = query(con, "SELECT site, period, cpw_plan, cpw_actual FROM an_cost_per_wafer")
    assert len(rows) == 27
    for site, period, cpw_plan, cpw_actual in rows:
        assert cpw_plan == pytest.approx(expected[site, period][0])
        assert cpw_actual == pytest.approx(expected[site, period][1])


def test_cost_per_wafer_is_marked_incomplete_where_an_actual_is_missing(warehouse):
    con, _ = warehouse
    assert query(con, "SELECT site, period FROM an_cost_per_wafer WHERE NOT complete") == [("FAB_ALPS", "2026-09")]


def test_thresholds_are_read_from_configuration():
    from src.pipeline.run import load_config
    assert load_config()["materiality"] == MATERIALITY
