"""Tests for the transformation layer's guard rails.

These do not exercise the SQL. They check that a stale or missing extract
produces an actionable error rather than a binder exception raised several
call frames below the caller.
"""

import pytest

from src import config, transform


def test_required_columns_cover_every_extract():
    assert set(transform.REQUIRED_COLUMNS) == {
        "institutions", "enrollment", "finance", "completions",
    }


def test_finance_requires_the_category_column():
    # 'category' was added when the full GASB revenue schedule was loaded.
    # An extract written before that change is unusable, and the guard exists
    # so the failure says so.
    assert "category" in transform.REQUIRED_COLUMNS["finance"]


def test_missing_extract_names_the_ingest_command(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROCESSED", tmp_path)
    transform.connect.cache_clear()
    with pytest.raises(FileNotFoundError, match="python -m src.ingest"):
        transform.connect()
    transform.connect.cache_clear()
