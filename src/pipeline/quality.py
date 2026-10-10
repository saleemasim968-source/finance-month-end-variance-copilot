"""Data-quality checks and reconciliation (WBS 3.4, FR-06).

Three steps, each backed by a SQL file in sql/checks or sql/quality:
- the mapping gate stops the run if any local code has no mapping, listing all of them (D-021);
- the data-quality report lists removed duplicates and missing actuals;
- the reconciliation proves, per site, period and measure, that no amount was lost or added.
"""

from pathlib import Path

SQL_DIR = Path(__file__).parent / "sql"


class UnmappedCodesError(Exception):
    """Raised when staged data contains local codes that the mapping tables do not cover."""


class ReconciliationError(Exception):
    """Raised when a source total does not equal the harmonised total plus logged corrections."""


def check_mappings(con):
    unmapped = con.execute((SQL_DIR / "checks" / "unmapped_codes.sql").read_text()).fetchall()
    if unmapped:
        listing = "\n".join(f"  - {site}: {code_type} {code} (in {source_file})"
                            for code_type, site, code, source_file in unmapped)
        raise UnmappedCodesError(
            f"{len(unmapped)} local code(s) without a mapping. Add them to data/reference/ and rerun:\n{listing}")


def build_reports(con, tolerance_pct):
    """Create dq_report and dq_reconciliation."""
    con.execute(f"SET VARIABLE reconciliation_tolerance_pct = {float(tolerance_pct)}")
    for path in sorted((SQL_DIR / "quality").glob("*.sql")):
        con.execute(path.read_text())


def check_reconciliation(con):
    failures = con.execute("""
        SELECT site, period, measure, difference_eur, difference_pct
        FROM dq_reconciliation WHERE NOT passed
    """).fetchall()
    if failures:
        listing = "\n".join(f"  - {site} {period} {measure}: difference EUR {diff} ({pct:.4%})"
                            for site, period, measure, diff, pct in failures)
        raise ReconciliationError(f"{len(failures)} reconciliation check(s) failed:\n{listing}")
