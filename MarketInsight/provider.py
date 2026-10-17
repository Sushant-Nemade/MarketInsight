import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from config.config import DataTable, Metric, NewsItem, PricePoint, ResearchRequest, ResearchResult, Source

ALLOWED_YAHOO_HOSTS = frozenset(
    {
        "query1.finance.yahoo.com",
        "query2.finance.yahoo.com",
        "fc.yahoo.com",
        "finance.yahoo.com",
        "www.yahoo.com",
        "guce.yahoo.com",
    }
)


def text(value, limit=1000):
    return " ".join(str(value or "").split())[:limit]


def number(value):
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) else None


def scalar(value):
    if value is None:
        return None
    if isinstance(value, (str, datetime)):
        return text(value, 300)
    return number(value)


def utc_timestamp(value):
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def bounded_session():
    from curl_cffi import requests

    class Session(requests.Session):
        def __init__(self):
            bundle = os.environ.get("MARKET_CA_BUNDLE", "")
            if bundle and (not Path(bundle).is_file() or Path(bundle).stat().st_size > 5_000_000):
                raise ValueError("Configured CA bundle is missing or oversized")
            super().__init__(impersonate="chrome", verify=bundle or True)
            self.calls = 0
            self.deadline = time.monotonic() + 40

        def request(self, method, url, *args, **kwargs):
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or parsed.hostname not in ALLOWED_YAHOO_HOSTS
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Unexpected market-data origin")
            remaining = self.deadline - time.monotonic()
            if self.calls >= 24 or remaining <= 0:
                raise ValueError("Market-data request budget exhausted")
            self.calls += 1
            kwargs["timeout"] = max(0.1, min(8, remaining))
            kwargs["allow_redirects"] = False
            return super().request(method, url, *args, **kwargs)

    return Session()


def dataframe_table(identifier, title, frame, *, statement=False, currency=""):
    if frame is None or getattr(frame, "empty", True):
        return DataTable(
            id=identifier,
            title=title,
            columns=[],
            rows=[],
            status="unavailable",
            note="Provider returned no data.",
        )
    if getattr(frame, "ndim", 2) == 1:
        frame = frame.tail(20).to_frame(name="Value")
    frame = frame.iloc[:20, :3] if statement else frame.iloc[:20, :7]
    if statement:
        columns = ["Metric"] + [text(column, 40)[:10] for column in frame.columns]
        rows = [
            [text(index, 120)] + [scalar(value) for value in row]
            for index, row in zip(frame.index, frame.itertuples(index=False, name=None), strict=True)
        ]
    else:
        normalized = frame.reset_index().iloc[:20, :8]
        columns = [text(column, 80) for column in normalized.columns]
        rows = [[scalar(value) for value in row] for row in normalized.itertuples(index=False, name=None)]
    note = (
        ("Provider-reported values; reporting currency: " + (currency or "not supplied") + ".")
        if statement
        else ""
    )
    return DataTable(id=identifier, title=title, columns=columns, rows=rows, note=note)


class YahooProvider:
    def __init__(self, ticker_factory=None, session_factory=None):
        self.ticker_factory = ticker_factory
        self.session_factory = session_factory or bounded_session

    def search(self, query: str):
        import re

        import yfinance as yf

        with self.session_factory() as session:
            result = yf.Search(query, max_results=6, news_count=0, timeout=8, session=session)
            matches = []
            for quote in result.quotes[:6]:
                symbol = quote.get("symbol", "")
                if re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,19}", symbol):
                    matches.append(
                        {
                            "ticker": symbol,
                            "name": text(quote.get("shortname") or quote.get("longname") or symbol, 160),
                            "exchange": text(quote.get("exchange"), 60),
                        }
                    )
            return matches

    def research(self, request: ResearchRequest) -> ResearchResult:
        import yfinance as yf

        now = datetime.now(timezone.utc).isoformat()
        limitations = [
            "Yahoo Finance data may be delayed, incomplete or revised.",
            "Research only; not investment advice or a trading instruction.",
        ]
        with self.session_factory() as session:
            stock = (self.ticker_factory or yf.Ticker)(request.ticker, session=session)
            info = {}
            history = []
            tables = []
            news = []
            try:
                info = stock.get_info() or {}
                if not isinstance(info, dict):
                    info = {}
            except Exception:
                limitations.append("Company overview/quote lookup was unavailable.")
            try:
                frame = stock.history(period="1y", interval="1d", timeout=8, raise_errors=True)
                for index, row in frame.tail(260).iterrows():
                    close = number(row.get("Close"))
                    volume = number(row.get("Volume"))
                    if close is not None and close >= 0:
                        history.append(
                            PricePoint(
                                date=index.date(),
                                close=close,
                                volume=int(volume) if volume is not None and volume >= 0 else None,
                            )
                        )
            except Exception:
                limitations.append("Historical prices were unavailable.")
            specifications = {
                "financials": [
                    ("balance", "Balance sheet", "get_balance_sheet", True),
                    ("income", "Income statement", "get_income_stmt", True),
                    ("cashflow", "Cash flow", "get_cash_flow", True),
                ],
                "ownership": [
                    ("institutional", "Institutional holders", "get_institutional_holders", False),
                    ("major", "Major shareholders", "get_major_holders", False),
                    ("mutual", "Mutual fund holders", "get_mutualfund_holders", False),
                    ("insiders", "Insider transactions", "get_insider_transactions", False),
                ],
                "events": [
                    ("dividends", "Dividend history", "get_dividends", False),
                    ("splits", "Stock splits", "get_splits", False),
                ],
                "analysts": [
                    ("recommendations", "Analyst coverage", "get_recommendations", False),
                    ("analyst_summary", "Coverage summary", "get_recommendations_summary", False),
                ],
            }
            for section in request.sections:
                for identifier, title, method, statement in specifications.get(section, []):
                    try:
                        tables.append(
                            dataframe_table(
                                identifier,
                                title,
                                getattr(stock, method)(),
                                statement=statement,
                                currency=text(info.get("financialCurrency"), 12),
                            )
                        )
                    except Exception:
                        tables.append(
                            DataTable(
                                id=identifier,
                                title=title,
                                columns=[],
                                rows=[],
                                status="unavailable",
                                note="Lookup failed or the bounded request budget was exhausted.",
                            )
                        )
            if "news" in request.sections:
                try:
                    for item in (stock.get_news(count=6) or [])[:6]:
                        content = item.get("content", item)
                        url = (content.get("canonicalUrl") or {}).get("url", content.get("link", ""))
                        parsed = urlsplit(url)
                        if (
                            parsed.scheme != "https"
                            or not parsed.hostname
                            or parsed.username
                            or parsed.password
                        ):
                            continue
                        news.append(
                            NewsItem(
                                title=text(content.get("title"), 300),
                                publisher=text(
                                    (content.get("provider") or {}).get(
                                        "displayName", content.get("publisher", "")
                                    ),
                                    120,
                                ),
                                url=url[:1000],
                                published_at=text(content.get("pubDate", ""), 40),
                            )
                        )
                except Exception:
                    limitations.append("News lookup was unavailable.")
            price = number(info.get("regularMarketPrice"))
            kind = "provider_quote" if price is not None and price >= 0 else "unavailable"
            as_of = utc_timestamp(info.get("regularMarketTime"))
            if price is None or price < 0:
                price = history[-1].close if history else None
                kind = "historical_close" if history else "unavailable"
                as_of = history[-1].date.isoformat() if history else ""
            metrics = []
            for label, key, unit in [
                ("Market cap", "marketCap", ""),
                ("P/E ratio", "trailingPE", "x"),
                ("Revenue", "totalRevenue", ""),
                ("Employees", "fullTimeEmployees", ""),
            ]:
                reported_unit = (
                    text(info.get("financialCurrency"), 12)
                    if key == "totalRevenue"
                    else text(info.get("currency"), 12)
                    if key == "marketCap"
                    else unit
                )
                metrics.append(Metric(label=label, value=number(info.get(key)), unit=reported_unit))
            if not info and not history:
                raise ValueError(
                    "No market data was available; check the symbol, provider availability and quotas"
                )
            return ResearchResult(
                id=str(uuid4()),
                created_at=now,
                mode="live",
                ticker=request.ticker,
                name=text(info.get("longName") or info.get("shortName") or request.ticker, 160),
                currency=text(info.get("currency") or "", 12),
                description=text(info.get("longBusinessSummary"), 2400),
                sector=text(info.get("sector"), 100),
                price=price,
                previous_close=number(info.get("previousClose")),
                price_as_of=as_of,
                price_kind=kind,
                history=history,
                metrics=metrics,
                tables=tables,
                news=news,
                sources=[
                    Source(
                        name="Yahoo Finance via yfinance",
                        url=f"https://finance.yahoo.com/quote/{request.ticker}/",
                        observed_at=now,
                    )
                ],
                limitations=limitations,
            )
