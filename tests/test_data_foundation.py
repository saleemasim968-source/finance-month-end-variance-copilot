"""Quality gate for WBS 2, data foundation (document 03 section 7).

Checks that the generated files have the specified row counts, that the reference
tables cover every local code, that the planted data issues are present, and that
no person-level data exists (NFR-01).
"""

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
REFERENCE = ROOT / "data" / "reference"

SITES = ["FAB_NORTH", "FAB_ALPS", "FAB_ASIA"]
GROUP_ACCOUNTS = {"Personnel", "Depreciation", "Energy", "Materials", "Maintenance", "External services"}
GROUP_AREAS = {"Lithography", "Etch", "Diffusion", "Facilities"}

# Site file, delimiter, cost-centre column, account column (document 04 section 3).
SITE_FILES = {
    "FAB_NORTH": ("fab_north_costs.csv", ",", "cost_center", "account_code"),
    "FAB_ALPS": ("fab_alps_kosten.csv", ";", "Kostenstelle", "Kontonummer"),
    "FAB_ASIA": ("fab_asia_gl_export.csv", ",", "CC", "GL Account"),
}


def read_rows(path, delimiter=","):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def read_site(site):
    file_name, delimiter, _, _ = SITE_FILES[site]
    return read_rows(RAW / file_name, delimiter)


@pytest.mark.parametrize("path, delimiter, expected", [
    (RAW / "fab_north_costs.csv", ",", 216),
    (RAW / "fab_alps_kosten.csv", ";", 216),
    (RAW / "fab_asia_gl_export.csv", ",", 433),
    (RAW / "wafer_volumes.csv", ",", 27),
    (REFERENCE / "fx_rates.csv", ",", 9),
])
def test_generated_files_have_specified_row_counts(path, delimiter, expected):
    assert len(read_rows(path, delimiter)) == expected


def test_reference_tables_have_one_row_per_local_code():
    accounts = read_rows(REFERENCE / "account_mapping.csv")
    cost_centres = read_rows(REFERENCE / "cost_centre_mapping.csv")
    behaviour = read_rows(REFERENCE / "cost_behaviour.csv")

    assert len(accounts) == 18
    assert len({(r["site"], r["local_account_code"]) for r in accounts}) == 18
    assert len(cost_centres) == 12
    assert len({(r["site"], r["local_cost_centre"]) for r in cost_centres}) == 12
    assert {r["group_account"] for r in behaviour} == GROUP_ACCOUNTS
    assert len(behaviour) == 6


def test_reference_tables_use_only_group_codes():
    for site in SITES:
        site_accounts = [r for r in read_rows(REFERENCE / "account_mapping.csv") if r["site"] == site]
        site_areas = [r for r in read_rows(REFERENCE / "cost_centre_mapping.csv") if r["site"] == site]
        assert {r["group_account"] for r in site_accounts} == GROUP_ACCOUNTS
        assert {r["group_area"] for r in site_areas} == GROUP_AREAS


def test_variable_shares_are_between_zero_and_one():
    for row in read_rows(REFERENCE / "cost_behaviour.csv"):
        assert 0.0 <= float(row["variable_share"]) <= 1.0


@pytest.mark.parametrize("site", SITES)
def test_reference_tables_cover_every_local_code(site):
    _, _, cost_centre_column, account_column = SITE_FILES[site]
    rows = read_site(site)
    mapped_accounts = {(r["site"], r["local_account_code"]) for r in read_rows(REFERENCE / "account_mapping.csv")}
    mapped_centres = {(r["site"], r["local_cost_centre"]) for r in read_rows(REFERENCE / "cost_centre_mapping.csv")}

    unmapped_accounts = {r[account_column] for r in rows} - {code for s, code in mapped_accounts if s == site}
    unmapped_centres = {r[cost_centre_column] for r in rows} - {cc for s, cc in mapped_centres if s == site}
    assert not unmapped_accounts, f"{site} accounts without mapping: {unmapped_accounts}"
    assert not unmapped_centres, f"{site} cost centres without mapping: {unmapped_centres}"


def test_account_names_match_source_files():
    """The local names in the mapping are informational (D-022) but should not drift from the source."""
    names = {(r["site"], r["local_account_code"]): r["local_account_name"]
             for r in read_rows(REFERENCE / "account_mapping.csv")}
    name_columns = {"FAB_NORTH": "account_name", "FAB_ALPS": "Kontobezeichnung", "FAB_ASIA": "GL Description"}
    for site in SITES:
        account_column = SITE_FILES[site][3]
        for row in read_site(site):
            assert row[name_columns[site]] == names[site, row[account_column]]


def test_planted_missing_actual_is_present_once():
    missing = [r for r in read_site("FAB_ALPS") if r["Ist_TEUR"] == ""]
    assert len(missing) == 1
    row = missing[0]
    assert (row["Periode"], row["Kostenstelle"], row["Kontonummer"]) == ("09.2026", "KST-220", "6500")


def test_planted_duplicate_line_is_present_once():
    lines = [tuple(r.values()) for r in read_site("FAB_ASIA")]
    duplicates = [line for line in set(lines) if lines.count(line) > 1]
    assert len(lines) - len(set(lines)) == 1
    assert len(duplicates) == 1
    assert duplicates[0][:5] == ("Jun-26", "MY-ETC", "M400", "Direct materials", "ACT")


def test_volumes_and_fx_cover_every_site_and_period():
    periods = {f"2026-{month:02d}" for month in range(1, 10)}
    volumes = read_rows(RAW / "wafer_volumes.csv")
    assert {(r["site"], r["period"]) for r in volumes} == {(s, p) for s in SITES for p in periods}
    assert {r["period"] for r in read_rows(REFERENCE / "fx_rates.csv")} == periods


def test_no_person_level_data():
    """NFR-01: cost-centre level only. No column may identify or describe a person."""
    forbidden = ("employee", "person_id", "staff_id", "name_of", "first_name", "last_name",
                 "mitarbeiter", "personalnummer", "salary", "gehalt")
    files = [RAW / f for f in ("fab_north_costs.csv", "fab_alps_kosten.csv",
                               "fab_asia_gl_export.csv", "wafer_volumes.csv")]
    files += sorted(REFERENCE.glob("*.csv"))
    for path in files:
        header = path.read_text(encoding="utf-8").splitlines()[0].lower()
        assert not any(word in header for word in forbidden), f"{path.name}: {header}"


def test_generator_is_deterministic_and_matches_committed_files(tmp_path):
    spec = importlib.util.spec_from_file_location("generate_data", ROOT / "src" / "generate_data.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    for path in generator.main(tmp_path).values():
        committed = ROOT / path.relative_to(tmp_path)
        assert path.read_bytes() == committed.read_bytes(), f"{committed.name} differs from a fresh run"
