import sqlite3
from uuid import uuid4

import pytest

from MarketInsight.research import ReportStore
from MarketInsight.sample import sample_reports


def test_failed_insert_preserves_existing_reports(tmp_path):
    store = ReportStore(tmp_path / "reports.sqlite")
    report = sample_reports()[0]
    store.save(report)
    with pytest.raises(sqlite3.IntegrityError):
        store.save(report)
    assert len(store.list()) == 1
    assert store.get(report.id).name == report.name


def test_report_retention_is_bounded(tmp_path):
    store = ReportStore(tmp_path / "reports.sqlite")
    report = sample_reports()[0]
    for index in range(103):
        store.save(
            report.model_copy(
                update={
                    "id": str(uuid4()),
                    "created_at": f"2026-10-17T12:{index // 60:02d}:{index % 60:02d}Z",
                }
            )
        )
    assert len(store.list()) == 100
