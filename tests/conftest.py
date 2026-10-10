"""Shared fixtures: one pipeline run per test session, opened read-only."""

import time

import duckdb
import pytest

from src.pipeline import run as pipeline


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory):
    """(connection, run time in seconds) for a fresh warehouse built from the committed data."""
    db_path = tmp_path_factory.mktemp("warehouse") / "variance.duckdb"
    start = time.perf_counter()
    pipeline.run(db_path=db_path)
    elapsed = time.perf_counter() - start
    with duckdb.connect(str(db_path), read_only=True) as con:
        yield con, elapsed
