"""Quality gate for WBS 3, ELT pipeline (document 03 section 7).

Runs the real pipeline on the generated data and checks the requirements of document 05
that WP 3 delivers: FR-01 to FR-06, NFR-02 and NFR-03.
"""

import csv
import re
import shutil
import time
from decimal import Decimal

import duckdb
import pytest

from src.pipeline import ingest, run as pipeline
from src.pipeline.quality import UnmappedCodesError

ROOT = pipeline.ROOT
SITE_DELIMITERS = {
    "data/raw/fab_north_costs.csv": ",",
    "data/raw/fab_alps_kosten.csv": ";",
    "data/raw/fab_asia_gl_export.csv": ",",
}


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("warehouse") / "variance.duckdb"
    start = time.perf_counter()
    pipeline.run(db_path=db_path)
    elapsed = time.perf_counter() - start
    with duckdb.connect(str(db_path), read_only=True) as con:
        yield con, elapsed


def query(con, sql):
    return con.execute(sql).fetchall()


def test_fr01_raw_tables_have_one_row_per_file_line(warehouse):
    con, _ = warehouse
    for table, (relative_path, _) in ingest.SOURCES.items():
        with (ROOT / relative_path).open(encoding="utf-8") as handle:
            file_rows = sum(1 for _ in handle) - 1
        assert query(con, f"SELECT COUNT(*) FROM {table}")[0][0] == file_rows, table


def test_fr02_nine_periods_per_site_in_yyyy_mm(warehouse):
    con, _ = warehouse
    rows = query(con, "SELECT site, COUNT(DISTINCT period) FROM rpt_harmonised GROUP BY site")
    assert dict(rows) == {"FAB_NORTH": 9, "FAB_ALPS": 9, "FAB_ASIA": 9}
    periods = [p for (p,) in query(con, "SELECT DISTINCT period FROM rpt_harmonised")]
    assert all(re.fullmatch(r"2026-0[1-9]", p) for p in periods)


def test_fr03_reconciliation_passes_for_every_site_period_and_measure(warehouse):
    con, _ = warehouse
    assert query(con, "SELECT COUNT(*), COUNT(*) FILTER (WHERE passed) FROM dq_reconciliation")[0] == (54, 54)


def test_fr03_alps_thousands_are_converted_to_eur(warehouse):
    con, _ = warehouse
    with (ROOT / "data/raw/fab_alps_kosten.csv").open(encoding="utf-8") as handle:
        first = next(csv.DictReader(handle, delimiter=";"))
    expected = Decimal(first["Plan_TEUR"].replace(",", ".")) * 1000
    plan = query(con, "SELECT plan_eur FROM rpt_harmonised WHERE site = 'FAB_ALPS' AND source_line_plan = 2")
    assert plan[0][0] == expected


def test_fr03_asia_ringgit_are_converted_at_the_monthly_rate(warehouse):
    con, _ = warehouse
    with (ROOT / "data/reference/fx_rates.csv").open(encoding="utf-8") as handle:
        rates = {r["period"]: Decimal(r["myr_per_eur"]) for r in csv.DictReader(handle)}
    with (ROOT / "data/raw/fab_asia_gl_export.csv").open(encoding="utf-8") as handle:
        first = next(csv.DictReader(handle))
    expected = (Decimal(first["Amount"]) / rates["2026-01"]).quantize(Decimal("0.01"))
    plan = query(con, "SELECT plan_eur FROM rpt_harmonised WHERE site = 'FAB_ASIA' AND source_line_plan = 2")
    assert plan[0][0] == expected


def test_fr04_every_row_is_mapped_to_the_group_structure(warehouse):
    con, _ = warehouse
    total, mapped = query(con, """
        SELECT COUNT(*), COUNT(*) FILTER (WHERE group_area IS NOT NULL AND group_account IS NOT NULL)
        FROM rpt_harmonised
    """)[0]
    assert total == mapped == 648


def test_harmonised_table_has_one_row_per_site_period_area_account(warehouse):
    con, _ = warehouse
    distinct = query(con, """
        SELECT COUNT(*) FROM (SELECT DISTINCT site, period, group_area, group_account FROM rpt_harmonised)
    """)[0][0]
    assert distinct == 648


def test_fr04_unknown_codes_stop_the_run_and_are_all_reported(tmp_path):
    shutil.copytree(ROOT / "data" / "raw", tmp_path / "data" / "raw")
    shutil.copytree(ROOT / "data" / "reference", tmp_path / "data" / "reference")
    with (tmp_path / "data/raw/fab_north_costs.csv").open("a", encoding="utf-8") as handle:
        handle.write("2026-09,CC9999,999999,Unknown account,100.00,100.00\n")

    with pytest.raises(UnmappedCodesError) as error:
        pipeline.run(root=tmp_path, db_path=tmp_path / "test.duckdb")
    message = str(error.value)
    assert "FAB_NORTH: account 999999" in message
    assert "FAB_NORTH: cost centre CC9999" in message


def test_fr05_local_codes_are_kept_on_every_row(warehouse):
    con, _ = warehouse
    empty = query(con, """
        SELECT COUNT(*) FROM rpt_harmonised
        WHERE COALESCE(local_cost_centre, '') = '' OR COALESCE(local_account_code, '') = ''
    """)[0][0]
    assert empty == 0


def test_fr06_exactly_the_two_planted_data_issues_are_reported(warehouse):
    con, _ = warehouse
    findings = query(con, """
        SELECT finding, site, period, local_cost_centre, local_account_code FROM dq_report ORDER BY finding
    """)
    assert findings == [
        ("actual_not_posted", "FAB_ALPS", "2026-09", "KST-220", "6500"),
        ("duplicate_removed", "FAB_ASIA", "2026-06", "MY-ETC", "M400"),
    ]


def test_fr06_removed_duplicate_is_logged_as_a_correction(warehouse):
    con, _ = warehouse
    corrections = query(con, "SELECT site, period, measure FROM dq_reconciliation WHERE corrections_eur <> 0")
    assert corrections == [("FAB_ASIA", "2026-06", "actual")]


def test_missing_actual_row_is_kept_and_marked(warehouse):
    con, _ = warehouse
    rows = query(con, "SELECT actual_eur, plan_eur IS NOT NULL FROM rpt_harmonised WHERE NOT actual_posted")
    assert rows == [(None, True)]


def test_nfr03_every_row_points_to_its_source_lines(warehouse):
    """Open each source file at the recorded line and check it holds the same local codes."""
    con, _ = warehouse
    files = {}
    for path, delimiter in SITE_DELIMITERS.items():
        with (ROOT / path).open(encoding="utf-8", newline="") as handle:
            files[path] = list(csv.reader(handle, delimiter=delimiter))

    rows = query(con, """
        SELECT source_file, source_line_plan, source_line_actual, local_cost_centre, local_account_code
        FROM rpt_harmonised
    """)
    assert len(rows) == 648
    for source_file, line_plan, line_actual, cost_centre, account in rows:
        for line in (line_plan, line_actual):
            assert line is not None
            fields = files[source_file][line - 1]
            assert cost_centre in fields and account in fields, (source_file, line)


def test_nfr02_two_runs_give_identical_results(tmp_path):
    tables = ["rpt_harmonised", "dq_report", "dq_reconciliation", "stg_wafer_volumes"]
    results = []
    for name in ("first", "second"):
        db_path = tmp_path / f"{name}.duckdb"
        pipeline.run(db_path=db_path)
        with duckdb.connect(str(db_path), read_only=True) as con:
            results.append({t: query(con, f"SELECT * FROM {t} ORDER BY ALL") for t in tables})
    assert results[0] == results[1]


def test_nfr02_run_takes_under_two_minutes(warehouse):
    _, elapsed = warehouse
    assert elapsed < 120
