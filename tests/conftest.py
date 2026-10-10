"""Shared fixtures: one pipeline run per test session, opened read-only.

Tests always use the template writer, so they never call a paid API, and they use temporary
review and log files, so they never touch the real approvals in data/review/.
"""

import os
import time

import duckdb
import pytest

os.environ["LLM_PROVIDER"] = "template"

from src.pipeline import run as pipeline  # noqa: E402


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Paths of a fresh warehouse, review store and log, plus the run time in seconds."""
    folder = tmp_path_factory.mktemp("run")
    paths = {"db_path": folder / "variance.duckdb", "review_path": folder / "review.duckdb",
             "log_path": folder / "llm_log.jsonl"}
    start = time.perf_counter()
    pipeline.run(**paths)
    return {**paths, "elapsed": time.perf_counter() - start}


@pytest.fixture(scope="session")
def warehouse(built):
    """(read-only connection, run time in seconds) for the fresh warehouse."""
    with duckdb.connect(str(built["db_path"]), read_only=True) as con:
        yield con, built["elapsed"]
