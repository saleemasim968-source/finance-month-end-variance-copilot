"""Quality gate for WBS 7, validation and transfer (document 03 section 7).

Covers the KNIME parity check (NFR-06), the synthetic-data notice in the documentation
(NFR-08) and the business case (BR-01, SC-8). The clean one-command run is recorded in
docs/evidence/run_log.txt.
"""

import csv
import importlib.util
import re

from src.pipeline.run import ROOT

KNIME = ROOT / "knime"


def load_parity():
    spec = importlib.util.spec_from_file_location("check_parity", KNIME / "check_parity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_knime_expected_totals_match_a_fresh_pipeline_run(warehouse):
    con, _ = warehouse
    fresh = {(s, p): (n, plan, actual) for s, p, n, plan, actual in con.execute("""
        SELECT site, period, COUNT(*), SUM(plan_eur), SUM(actual_eur) FROM rpt_harmonised GROUP BY site, period
    """).fetchall()}
    with (KNIME / "expected_harmonised_totals.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 27
    for row in rows:
        n, plan, actual = fresh[row["site"], row["period"]]
        assert int(row["rows"]) == n and str(plan) == row["plan_eur"] and str(actual) == row["actual_eur"]


def test_knime_parity_check_passes_on_equal_and_fails_on_different_totals():
    parity = load_parity()
    expected = parity.read(KNIME / "expected_harmonised_totals.csv")
    assert parity.compare(expected, expected) == []

    changed = {key: dict(row) for key, row in expected.items()}
    key = ("FAB_ASIA", "2026-06")
    changed[key]["actual_eur"] = str(parity.amount(changed[key]["actual_eur"]) + 511278)  # duplicate not removed
    del changed[("FAB_NORTH", "2026-01")]
    problems = parity.compare(expected, changed)
    assert any("FAB_ASIA" in p and "actual_eur" in p for p in problems)
    assert any("FAB_NORTH" in p and "missing" in p for p in problems)


def test_readme_and_handover_documents_carry_the_synthetic_notice():
    for path in ("README.md", "docs/business_case.md", "docs/demo_script.md", "knime/README.md",
                 "docs/architecture.md"):
        text = (ROOT / path).read_text(encoding="utf-8").lower()
        assert "synthetic" in text and "independent portfolio project" in text, path


def test_business_case_states_estimates_and_assumptions():
    text = (ROOT / "docs/business_case.md").read_text(encoding="utf-8")
    assert "estimate" in text.lower() and "Assumptions" in text
    hours = re.search(r"\*\*Total\*\* \| \*\*(\d+\.\d)\*\* \| \*\*(\d+\.\d)\*\*", text)
    assert hours, "total row not found"
    rows = re.findall(r"^\| [A-Z][^|]+\| (\d+\.\d) \| (\d+\.\d) \|", text, flags=re.MULTILINE)
    assert abs(sum(float(a) for a, _ in rows) - float(hours.group(1))) < 0.05
    assert abs(sum(float(b) for _, b in rows) - float(hours.group(2))) < 0.05
