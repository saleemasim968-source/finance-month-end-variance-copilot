"""Run the whole pipeline with one command (WBS 3, NFR-02).

Deletes the warehouse and rebuilds it from the raw files, so every run starts from the
same state and gives the same result:
raw load -> staging -> mapping gate -> harmonised table -> data-quality report -> reconciliation
-> variance analytics -> commentary drafts for new flagged items (template if no LLM key).

Usage: python -m src.pipeline.run
"""

import sys
import time
from pathlib import Path

import duckdb
import yaml

from src.analytics import variance
from src.commentary import run as commentary
from src.pipeline import ingest, quality

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = Path(__file__).parent / "sql"


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def run_sql_folder(con, folder):
    for path in sorted((SQL_DIR / folder).glob("*.sql")):
        con.execute(path.read_text(encoding="utf-8"))


def run(root=ROOT, db_path=None, review_path=None, log_path=None, draft_commentary=True):
    """Rebuild the warehouse from the files below root, then draft missing commentary.

    Returns a short summary. Tests pass their own paths so they never touch the real
    review store or log.
    """
    config = load_config()
    db_path = Path(db_path or Path(root) / config["warehouse_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    with duckdb.connect(str(db_path)) as con:
        raw_counts = ingest.load_all(con, root)
        run_sql_folder(con, "staging")
        quality.check_mappings(con)
        run_sql_folder(con, "reporting")
        quality.build_reports(con, config["reconciliation_tolerance_pct"])
        quality.check_reconciliation(con)
        flags = variance.run(con, config["materiality"])

        summary = {
            "db_path": db_path,
            "raw_rows": raw_counts,
            "harmonised_rows": con.execute("SELECT COUNT(*) FROM rpt_harmonised").fetchone()[0],
            "findings": dict(con.execute("SELECT finding, COUNT(*) FROM dq_report GROUP BY finding").fetchall()),
            "reconciliation_checks": con.execute("SELECT COUNT(*) FROM dq_reconciliation").fetchone()[0],
            **flags,
        }

    summary["new_drafts"] = 0
    if draft_commentary:
        settings = config["commentary"]
        drafted = commentary.draft_all(db_path,
                                       review_path or Path(root) / settings["review_path"],
                                       log_path or Path(root) / settings["log_path"],
                                       settings["language"])
        summary["new_drafts"] = len(drafted)
    return summary


def main():
    from src.commentary.llm import load_env_file
    load_env_file()
    start = time.perf_counter()
    try:
        summary = run()
    except (quality.UnmappedCodesError, quality.ReconciliationError) as error:
        print(f"RUN STOPPED\n{error}", file=sys.stderr)
        sys.exit(1)

    print("Raw rows loaded:")
    for table, rows in summary["raw_rows"].items():
        print(f"  {table:<24} {rows:>4}")
    print(f"Harmonised rows:          {summary['harmonised_rows']:>4}")
    for finding, count in sorted(summary["findings"].items()):
        print(f"Data-quality finding:     {count:>4}  {finding}")
    print(f"Reconciliation checks:    {summary['reconciliation_checks']:>4}  all passed")
    print(f"Spend flags:              {summary['spend_flags']:>4}")
    print(f"Volume flags:             {summary['volume_flags']:>4}")
    print(f"New commentary drafts:    {summary['new_drafts']:>4}  (writer: {commentary.llm.provider()})")
    print(f"Warehouse:                {summary['db_path'].relative_to(ROOT)}")
    print(f"Run time:                 {time.perf_counter() - start:.2f} s")


if __name__ == "__main__":
    main()
