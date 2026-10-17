import asyncio

import pytest

from config.config import ResearchRequest
from MarketInsight.research import ReportStore, ResearchService, ai_configuration, evidence_summary
from MarketInsight.sample import sample_reports


def test_store_roundtrip_persistence_and_clear(tmp_path):
    store = ReportStore(tmp_path / "data/reports.sqlite")
    report = sample_reports()[0]
    store.save(report)
    assert ReportStore(store.path).get(report.id).ticker == report.ticker
    assert store.list()[0]["id"] == report.id
    assert store.get("' OR 1=1 --") is None
    store.clear()
    assert store.list() == []


def test_sample_service_is_complete_and_not_ai():
    service = ResearchService()
    try:
        report = asyncio.run(service.research(ResearchRequest(ticker="DEMO-A")))
        assert report.mode == "sample" and report.analysis_kind == "reference"
        assert report.question == "Summarize the available evidence and its limitations."
        assert report.price is not None and len(report.tables) == 11
    finally:
        service.close()


def test_live_disabled_does_not_call_provider(monkeypatch):
    monkeypatch.delenv("MARKET_LIVE_DATA", raising=False)

    class Provider:
        def research(self, request):
            pytest.fail("Unexpected live lookup")

    service = ResearchService(provider=Provider())
    try:
        with pytest.raises(ValueError, match="disabled"):
            asyncio.run(service.research(ResearchRequest(ticker="AAPL", data_mode="live")))
    finally:
        service.close()


def test_live_result_is_not_fabricated_when_provider_fails(monkeypatch):
    monkeypatch.setenv("MARKET_LIVE_DATA", "1")

    class Provider:
        def research(self, request):
            raise ValueError("Unavailable data")

    service = ResearchService(provider=Provider())
    try:
        with pytest.raises(ValueError, match="Unavailable"):
            asyncio.run(service.research(ResearchRequest(ticker="AAPL", data_mode="live")))
    finally:
        service.close()


def test_provider_credentials_are_origin_specific(monkeypatch):
    monkeypatch.setenv("MARKET_PROVIDER", "thesys")
    monkeypatch.setenv("OPENAI_API_KEY", "not-for-thesys")
    monkeypatch.delenv("THESYS_API_KEY", raising=False)
    monkeypatch.setenv("MARKET_MODEL", "example-model")
    with pytest.raises(ValueError):
        ai_configuration()
    monkeypatch.setenv("MARKET_PROVIDER", "openai")
    assert ai_configuration()[0] == "https://api.openai.com/v1"


def test_evidence_summary_does_not_claim_inference():
    assert "not an AI answer" in evidence_summary(sample_reports()[0], "Explain this evidence")
