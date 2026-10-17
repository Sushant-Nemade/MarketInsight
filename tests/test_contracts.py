from uuid import UUID

import pytest
from pydantic import ValidationError

from config.config import ResearchRequest, ResearchResult, Source
from MarketInsight.sample import sample_reports


@pytest.mark.parametrize(
    "ticker", ["../AAPL", "AAPL/../../", "<script>", "aapl", "X" * 21, "https://evil.test"]
)
def test_unsafe_tickers_rejected(ticker):
    with pytest.raises(ValidationError):
        ResearchRequest(ticker=ticker)


def test_duplicate_sections_and_long_questions_rejected():
    with pytest.raises(ValidationError):
        ResearchRequest(ticker="AAPL", sections=["overview", "overview"])
    with pytest.raises(ValidationError):
        ResearchRequest(ticker="AAPL", question="X" * 1201)


def test_samples_are_finite_explicit_and_complete():
    reports = sample_reports()
    assert len(reports) == 3
    for report in reports:
        assert UUID(report.id).version == 5
        assert report.mode == "sample" and report.analysis_kind == "reference"
        assert len(report.history) > 60 and len(report.tables) == 11
        assert "fictional" in report.description.lower()
        assert ResearchResult.model_validate_json(report.model_dump_json()).ticker == report.ticker


def test_nonfinite_and_credential_urls_rejected():
    with pytest.raises(ValidationError):
        Source(name="bad", url="https://user:pass@evil.test", observed_at="2026-10-01")
    content = sample_reports()[0].model_dump()
    content["price"] = float("nan")
    with pytest.raises(ValidationError):
        ResearchResult.model_validate(content)
