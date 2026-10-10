"""Raw load (WBS 3.1): copy every input file into DuckDB unchanged.

Every value is stored as text exactly as it appears in the file, plus the file path and
the physical line number (header = line 1), so each figure can be traced back to its
source (NFR-03, D-020). Typing and cleaning happen later, in the staging SQL.
"""

import csv
from pathlib import Path

# Table name -> (file path relative to the project root, delimiter).
SOURCES = {
    "raw_fab_north": ("data/raw/fab_north_costs.csv", ","),
    "raw_fab_alps": ("data/raw/fab_alps_kosten.csv", ";"),
    "raw_fab_asia": ("data/raw/fab_asia_gl_export.csv", ","),
    "raw_wafer_volumes": ("data/raw/wafer_volumes.csv", ","),
    "raw_fx_rates": ("data/reference/fx_rates.csv", ","),
    "ref_account_mapping": ("data/reference/account_mapping.csv", ","),
    "ref_cost_centre_mapping": ("data/reference/cost_centre_mapping.csv", ","),
    "ref_cost_behaviour": ("data/reference/cost_behaviour.csv", ","),
}


def load_file(con, table, path, source_file, delimiter):
    """Load one CSV file into a table of text columns plus source_file and source_line."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader)
        rows = []
        for values in reader:
            if len(values) != len(header):
                raise ValueError(f"{source_file} line {reader.line_num}: expected {len(header)} fields, "
                                 f"found {len(values)}")
            rows.append([*values, source_file, reader.line_num])

    columns = ", ".join(f'"{name}" VARCHAR' for name in header)
    con.execute(f"CREATE OR REPLACE TABLE {table} ({columns}, source_file VARCHAR, source_line INTEGER)")
    placeholders = ", ".join("?" * (len(header) + 2))
    con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    return len(rows)


def load_all(con, root):
    """Load every source file below root. Returns the row count per table."""
    return {
        table: load_file(con, table, Path(root) / relative_path, relative_path, delimiter)
        for table, (relative_path, delimiter) in SOURCES.items()
    }
