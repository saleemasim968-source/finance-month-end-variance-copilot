"""Compare the KNIME rebuild with the Python/SQL pipeline (WBS 7.2, NFR-06).

The KNIME workflow described in knime/README.md writes knime/output/harmonised_totals_knime.csv
with the columns site, period, rows, plan_eur, actual_eur. This script compares it with
knime/expected_harmonised_totals.csv, which the SQL pipeline produced, and passes only if
every site and period matches: same row count, totals within EUR 0.01.

Usage: python knime/check_parity.py [path to the KNIME output]
       python knime/check_parity.py --export-expected   (refresh the expected file from the warehouse)
"""

import csv
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOLERANCE = Decimal("0.01")


def read(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return {(r["site"], r["period"]): r for r in csv.DictReader(handle)}


def amount(value):
    return Decimal(value) if value not in ("", None) else Decimal(0)


def compare(expected, actual):
    problems = []
    for key in sorted(set(expected) | set(actual)):
        if key not in actual:
            problems.append(f"{key}: missing in KNIME output")
            continue
        if key not in expected:
            problems.append(f"{key}: not expected")
            continue
        e, a = expected[key], actual[key]
        if int(e["rows"]) != int(a["rows"]):
            problems.append(f"{key}: rows {a['rows']} instead of {e['rows']}")
        for column in ("plan_eur", "actual_eur"):
            difference = abs(amount(e[column]) - amount(a[column]))
            if difference > TOLERANCE:
                problems.append(f"{key}: {column} differs by EUR {difference}")
    return problems


def export_expected():
    import duckdb
    root = HERE.parent
    with duckdb.connect(str(root / "data" / "warehouse" / "variance.duckdb"), read_only=True) as con:
        con.execute(f"""
            COPY (SELECT site, period, COUNT(*) AS rows, SUM(plan_eur) AS plan_eur, SUM(actual_eur) AS actual_eur
                  FROM rpt_harmonised GROUP BY site, period ORDER BY site, period)
            TO '{HERE / "expected_harmonised_totals.csv"}' (HEADER, DELIMITER ',')
        """)
    print("Wrote knime/expected_harmonised_totals.csv")


def main():
    if sys.argv[1:] == ["--export-expected"]:
        export_expected()
        return
    knime_output = sys.argv[1] if len(sys.argv) > 1 else HERE / "output" / "harmonised_totals_knime.csv"
    if not Path(knime_output).exists():
        print(f"No KNIME output at {knime_output}. Build and run the workflow first (see knime/README.md).")
        sys.exit(2)
    problems = compare(read(HERE / "expected_harmonised_totals.csv"), read(knime_output))
    if problems:
        print("KNIME parity check FAILED:")
        print("\n".join(f"  - {p}" for p in problems))
        sys.exit(1)
    print("KNIME parity check passed: all 27 site-periods match the SQL pipeline.")


if __name__ == "__main__":
    main()
