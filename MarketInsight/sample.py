import math
from datetime import date, timedelta
from uuid import NAMESPACE_URL, uuid5

from config.config import ResearchResult


def sample_reports() -> list[ResearchResult]:
    reports = []
    for index, (ticker, name, sector, base) in enumerate(
        [
            ("DEMO-A", "Northstar Systems", "Technology", 142.0),
            ("DEMO-B", "Cedar Energy", "Energy", 76.0),
            ("DEMO-C", "Meridian Health", "Healthcare", 218.0),
        ]
    ):
        points = []
        day = date(2026, 6, 1)
        while day <= date(2026, 10, 1):
            if day.weekday() < 5:
                step = len(points)
                close = round(
                    base
                    + step * (0.18 + index * 0.03)
                    + math.sin(step / 5) * 3.4
                    + math.cos(step / 11) * 1.8,
                    2,
                )
                points.append({"date": day.isoformat(), "close": close, "volume": 1_000_000 + step * 1237})
            day += timedelta(days=1)

        def table(identifier, title, columns, rows):
            return {"id": identifier, "title": title, "columns": columns, "rows": rows}

        reports.append(
            ResearchResult.model_validate(
                {
                    "id": str(uuid5(NAMESPACE_URL, "market-insight-reference/" + ticker)),
                    "created_at": "2026-10-01T16:00:00Z",
                    "mode": "sample",
                    "ticker": ticker,
                    "name": name,
                    "currency": "USD",
                    "description": f"Fictional {sector.lower()} company used to demonstrate evidence-based research. All prices, financial statements and ownership records in this sample are invented.",
                    "sector": sector,
                    "price": points[-1]["close"],
                    "previous_close": points[-2]["close"],
                    "price_as_of": "2026-10-01T16:00:00Z",
                    "price_kind": "synthetic",
                    "history": points,
                    "metrics": [
                        {"label": "Market cap", "value": 28_400_000_000 * (index + 1), "unit": "USD"},
                        {"label": "P/E ratio", "value": 24.6 + index, "unit": "x"},
                        {"label": "Revenue", "value": 9_200_000_000 * (index + 1), "unit": "USD"},
                        {"label": "Employees", "value": 14500 + index * 3000},
                    ],
                    "tables": [
                        table(
                            "income",
                            "Income statement",
                            ["Metric", "FY 2025", "FY 2024"],
                            [
                                ["Revenue", 9_200_000_000, 8_400_000_000],
                                ["Operating income", 1_820_000_000, 1_560_000_000],
                                ["Net income", 1_220_000_000, 1_080_000_000],
                            ],
                        ),
                        table(
                            "balance",
                            "Balance sheet",
                            ["Metric", "FY 2025", "FY 2024"],
                            [
                                ["Total assets", 18_000_000_000, 17_000_000_000],
                                ["Total liabilities", 7_800_000_000, 7_600_000_000],
                                ["Stockholder equity", 10_200_000_000, 9_400_000_000],
                            ],
                        ),
                        table(
                            "cashflow",
                            "Cash flow",
                            ["Metric", "FY 2025", "FY 2024"],
                            [
                                ["Operating cash flow", 2_100_000_000, 1_800_000_000],
                                ["Capital expenditure", -640_000_000, -590_000_000],
                            ],
                        ),
                        table(
                            "institutional",
                            "Institutional holders",
                            ["Holder", "Shares", "Ownership"],
                            [
                                ["Sample Capital", 8_400_000, "6.2%"],
                                ["Example Index Fund", 6_200_000, "4.6%"],
                            ],
                        ),
                        table(
                            "major",
                            "Major shareholders",
                            ["Group", "Ownership"],
                            [["Institutions", "64%"], ["Insiders", "8%"]],
                        ),
                        table(
                            "mutual",
                            "Mutual fund holders",
                            ["Holder", "Shares"],
                            [["Fictional Equity Fund", 2_100_000]],
                        ),
                        table(
                            "insiders",
                            "Insider transactions",
                            ["Date", "Action", "Shares"],
                            [["2026-09-01", "Sample purchase", 2000]],
                        ),
                        table(
                            "recommendations",
                            "Analyst coverage",
                            ["Period", "Strong buy", "Buy", "Hold", "Sell"],
                            [["Sample month", 2, 5, 7, 1]],
                        ),
                        table(
                            "analyst_summary",
                            "Coverage summary",
                            ["Metric", "Value"],
                            [["Fictional analyst count", 15]],
                        ),
                        table(
                            "dividends",
                            "Dividend history",
                            ["Date", "Amount"],
                            [["2026-08-15", 0.42], ["2026-05-15", 0.40]],
                        ),
                        table(
                            "splits", "Stock splits", ["Date", "Ratio"], [["2024-06-01", "2:1 (fictional)"]]
                        ),
                    ],
                    "news": [
                        {
                            "title": "Fictional quarterly update published",
                            "publisher": "Synthetic reference",
                            "url": "https://github.com/Sushant-Nemade/MarketInsight",
                            "published_at": "2026-09-25",
                        }
                    ],
                    "summary": f"{name} is a fictional company. Its sample quote is {points[-1]['close']:.2f} USD as of October 1, 2026. The included statements demonstrate comparative research, not a verified investment opportunity. Review the financial, ownership and event tables alongside their source labels. No live market data or AI inference is used in this reference.",
                    "analysis_kind": "reference",
                    "sources": [
                        {
                            "name": "Authored synthetic reference dataset",
                            "url": "https://github.com/Sushant-Nemade/MarketInsight",
                            "observed_at": "2026-10-01T16:00:00Z",
                        }
                    ],
                    "limitations": [
                        "All sample companies and figures are fictional.",
                        "No live market lookup or AI inference occurred.",
                        "Educational research only; not investment advice.",
                    ],
                }
            )
        )
    return reports
