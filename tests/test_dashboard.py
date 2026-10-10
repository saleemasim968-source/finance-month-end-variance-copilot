"""Quality gate for WBS 6, backend and frontend (document 03 section 7).

Every dashboard figure must equal the value in the variance table. Five values are
spot-checked by name, and the sums behind every view are compared with the variance table
(FR-15). The synthetic-data notice must be on every screen (NFR-08). Review actions go
through the API (FR-13, FR-14).
"""

import pytest
from fastapi.testclient import TestClient

from app.backend import main as backend

TOOL_DOWN = "spend|FAB_NORTH|2026-05|Lithography|Maintenance"


@pytest.fixture(scope="module")
def client(built, tmp_path_factory):
    review = tmp_path_factory.mktemp("api") / "review.duckdb"
    import shutil
    shutil.copy(built["review_path"], review)
    backend.configure(warehouse_path=built["db_path"], review_path=review,
                      log_path=review.parent / "llm_log.jsonl")
    with TestClient(backend.app) as test_client:
        yield test_client


def value(con, sql, params=()):
    return con.execute(sql, list(params)).fetchone()[0]


# --- Five spot checks against the variance table --------------------------------------------

def test_spot_1_overview_total_variance(client, warehouse):
    con, _ = warehouse
    api = client.get("/api/overview").json()["totals"]["total_var"]
    assert api == pytest.approx(value(con, "SELECT SUM(total_var) FROM an_variance WHERE actual_posted"))


def test_spot_2_site_spend_effect_in_july(client, warehouse):
    con, _ = warehouse
    rows = client.get("/api/overview?period=2026-07").json()["by_site"]
    alps = next(r for r in rows if r["site"] == "FAB_ALPS")
    assert alps["spend_effect"] == pytest.approx(value(con, """
        SELECT SUM(spend_effect) FROM an_variance WHERE site = 'FAB_ALPS' AND period = '2026-07' AND actual_posted
    """))


def test_spot_3_bridge_maintenance_spend_effect(client, warehouse):
    con, _ = warehouse
    data = client.get("/api/bridge?site=FAB_NORTH&period=2026-05").json()
    maintenance = next(r for r in data["by_account"] if r["group_account"] == "Maintenance")
    assert maintenance["spend_effect"] == pytest.approx(value(con, """
        SELECT SUM(spend_effect) FROM an_variance
        WHERE site = 'FAB_NORTH' AND period = '2026-05' AND group_account = 'Maintenance'
    """))


def test_spot_4_cost_per_wafer_of_one_site_and_month(client, warehouse):
    con, _ = warehouse
    rows = client.get("/api/sites?period=2026-08").json()["cost_per_wafer"]
    asia = next(r for r in rows if r["site"] == "FAB_ASIA")
    assert asia["cpw_actual"] == pytest.approx(value(con, """
        SELECT cpw_actual FROM an_cost_per_wafer WHERE site = 'FAB_ASIA' AND period = '2026-08'
    """))


def test_spot_5_flagged_item_figure(client, warehouse):
    con, _ = warehouse
    item = next(i for i in client.get("/api/flags").json() if i["item_id"] == TOOL_DOWN)
    spend = value(con, """
        SELECT spend_effect FROM an_variance
        WHERE site = 'FAB_NORTH' AND period = '2026-05' AND group_area = 'Lithography' AND group_account = 'Maintenance'
    """)
    assert item["figures"]["spend_effect_teur"] == round(spend / 1000)


# --- Every view adds up to the variance table -----------------------------------------------

def test_bridge_closes_from_plan_to_actual(client):
    for site in ("all", "FAB_NORTH", "FAB_ALPS", "FAB_ASIA"):
        data = client.get(f"/api/bridge?site={site}").json()
        t = data["totals"]
        spend = sum(r["spend_effect"] for r in data["by_account"])
        assert t["plan_eur"] + t["volume_effect"] + spend == pytest.approx(t["actual_eur"]), site


def test_monthly_chart_matches_the_variance_table(client, warehouse):
    con, _ = warehouse
    expected = dict(con.execute("""
        SELECT period, SUM(spend_effect) FROM an_variance WHERE actual_posted GROUP BY period
    """).fetchall())
    for month in client.get("/api/overview").json()["monthly"]:
        assert month["spend_effect"] == pytest.approx(expected[month["period"]])


def test_heatmap_matches_the_variance_table(client, warehouse):
    con, _ = warehouse
    for cell in client.get("/api/sites").json()["heatmap"]:
        expected = value(con, """
            SELECT SUM(total_var) / SUM(plan_eur) FROM an_variance
            WHERE site = ? AND group_account = ? AND actual_posted
        """, [cell["site"], cell["group_account"]])
        assert cell["total_var_pct"] == pytest.approx(expected)


def test_row_table_lists_every_row_with_its_source(client):
    rows = client.get("/api/bridge").json()["rows"]
    assert len(rows) == 648
    assert all(r["source_file"] and r["source_line_plan"] for r in rows)


def test_not_posted_row_is_reported_on_the_overview(client):
    rows = client.get("/api/overview?period=2026-09").json()["not_posted"]
    assert [(r["site"], r["local_cost_centre"], r["local_account_code"]) for r in rows] == [("FAB_ALPS", "KST-220", "6500")]


def test_data_quality_view(client):
    data = client.get("/api/data-quality").json()
    assert data["mapped_rows"] == data["harmonised_rows"] == 648
    assert len(data["findings"]) == 2
    assert all(r["passed"] for r in data["reconciliation"]) and len(data["reconciliation"]) == 54


# --- Synthetic-data notice (NFR-08) ------------------------------------------------------------

def test_notice_is_served_and_shown_on_every_screen(client):
    assert "synthetic" in client.get("/api/meta").json()["notice"].lower()
    page = client.get("/").text
    assert 'class="notice"' in page and "Synthetic data." in page
    # The notice sits outside the tab panels, so it is visible on every view.
    assert page.index('class="notice"') < page.index('<nav class="tabs"')


# --- Review actions through the API (FR-13, FR-14) -------------------------------------------

def test_review_workflow_through_the_api(client):
    flag = f"/api/flags/{TOOL_DOWN}"
    assert client.put(f"{flag}/cause", json={"cause": "Scanner lens repair after a tool-down."}).status_code == 200
    draft = client.post(f"{flag}/regenerate", json={"language": "en"}).json()
    assert "Scanner lens repair after a tool-down." in draft["text"] and draft["status"] == "Draft"

    bad = client.put(f"{flag}/text", json={"text": "Overspend of EUR 999k."}).json()
    assert bad["check_passed"] is False
    assert client.post(f"{flag}/approve", json={"reviewer_role": "Manufacturing controller"}).status_code == 409

    client.put(f"{flag}/text", json={"text": "Maintenance overspend of EUR 477k in May 2026."})
    approved = client.post(f"{flag}/approve", json={"reviewer_role": "Manufacturing controller"}).json()
    assert approved["status"] == "Approved" and approved["reviewer_role"] == "Manufacturing controller"

    shown = next(i for i in client.get("/api/flags").json() if i["item_id"] == TOOL_DOWN)
    assert shown["commentary"]["status"] == "Approved"
    assert client.put(f"{flag}/text", json={"text": "late change"}).status_code == 409
    assert client.post(f"{flag}/reopen").json()["status"] == "Draft"


def test_german_draft_through_the_api(client):
    draft = client.post("/api/flags/volume|FAB_ASIA|2026-08/regenerate", json={"language": "de"}).json()
    assert draft["language"] == "de" and draft["check_passed"] and "Wafer" in draft["text"]


def test_unknown_item_returns_404(client):
    assert client.post("/api/flags/spend|NOPE|2026-01|X|Y/regenerate", json={}).status_code == 404
