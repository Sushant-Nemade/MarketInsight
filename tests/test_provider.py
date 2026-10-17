from contextlib import nullcontext

import pandas as pd
import pytest

from config.config import ResearchRequest
from MarketInsight.provider import YahooProvider, bounded_session, dataframe_table


class Ticker:
    def __init__(self, symbol, session=None):
        self.symbol = symbol

    def get_info(self):
        return {
            "longName": "Actual provider fixture",
            "currency": "USD",
            "regularMarketPrice": 123.5,
            "regularMarketTime": 1780000000,
            "previousClose": 120.0,
        }

    def history(self, **kwargs):
        return pd.DataFrame(
            {"Close": [121.0, 123.0], "Volume": [1000, 1200]},
            index=pd.to_datetime(["2026-09-30", "2026-10-01"]),
        )

    def get_dividends(self):
        return pd.Series([0.5], index=pd.to_datetime(["2026-09-01"]))

    def get_splits(self):
        return pd.Series(dtype=float)


def test_live_adapter_has_dates_and_serializable_series_tables():
    provider = YahooProvider(ticker_factory=Ticker, session_factory=lambda: nullcontext(object()))
    report = provider.research(
        ResearchRequest(ticker="AAPL", data_mode="live", sections=["events", "financials"])
    )
    assert report.mode == "live" and report.price == 123.5
    assert report.price_as_of and len(report.history) == 2
    dividend = next(table for table in report.tables if table.id == "dividends")
    assert dividend.status == "available" and dividend.rows[0][-1] == 0.5
    balance = next(table for table in report.tables if table.id == "balance")
    assert balance.status == "unavailable"
    assert report.sources[0].url.startswith("https://finance.yahoo.com/")


def test_missing_quote_is_explicit_historical_close():
    class NoQuote(Ticker):
        def get_info(self):
            return {}

    provider = YahooProvider(ticker_factory=NoQuote, session_factory=lambda: nullcontext(object()))
    report = provider.research(ResearchRequest(ticker="AAPL", data_mode="live"))
    assert report.price_kind == "historical_close" and report.price == 123


@pytest.mark.parametrize(
    "url",
    [
        "http://query1.finance.yahoo.com/",
        "https://evil.example/",
        "https://user:pass@query1.finance.yahoo.com/",
    ],
)
def test_market_origin_guards(url):
    with bounded_session() as session:
        with pytest.raises(ValueError):
            session.get(url)


def test_request_budget_rejects_further_network_calls():
    with bounded_session() as session:
        session.calls = 24
        with pytest.raises(ValueError, match="budget"):
            session.get("https://query1.finance.yahoo.com/v8/finance/chart/AAPL")


def test_custom_ca_bundle_must_exist(monkeypatch):
    monkeypatch.setenv("MARKET_CA_BUNDLE", "nonexistent-owner-ca-bundle.pem")
    with pytest.raises(ValueError, match="CA bundle"):
        bounded_session()


def test_statement_currency_is_explicit_not_inferred_from_quote():
    frame = pd.DataFrame({"2025-09-30": [100]}, index=["Revenue"])
    table = dataframe_table("income", "Income statement", frame, statement=True, currency="EUR")
    assert "EUR" in table.note
    missing = dataframe_table("income", "Income statement", frame, statement=True)
    assert "not supplied" in missing.note
