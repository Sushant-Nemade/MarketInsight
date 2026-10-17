from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Scalar = str | int | float | None
Section = Literal["overview", "financials", "ownership", "events", "analysts", "news"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ResearchRequest(Contract):
    ticker: str = Field(pattern=r"^[A-Z0-9^][A-Z0-9.^=-]{0,19}$")
    question: str = Field(
        default="Summarize the available evidence and its limitations.", min_length=1, max_length=1200
    )
    sections: list[Section] = Field(default_factory=lambda: ["overview"], min_length=1, max_length=6)
    analysis: Literal["evidence", "ai"] = "evidence"
    data_mode: Literal["sample", "live"] = "sample"

    @field_validator("sections")
    @classmethod
    def distinct_sections(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Sections must be unique")
        return value


class PricePoint(Contract):
    date: date
    close: float = Field(ge=0)
    volume: int | None = Field(default=None, ge=0)


class Metric(Contract):
    label: str = Field(max_length=80)
    value: Scalar
    unit: str = Field(default="", max_length=20)


class DataTable(Contract):
    id: str = Field(pattern=r"^[a-z_-]{1,50}$")
    title: str = Field(max_length=100)
    columns: list[str] = Field(max_length=8)
    rows: list[list[Scalar]] = Field(max_length=30)
    status: Literal["available", "unavailable"] = "available"
    note: str = Field(default="", max_length=300)

    @field_validator("rows")
    @classmethod
    def bounded_rows(cls, value):
        if any(len(row) > 8 for row in value):
            raise ValueError("Too many table cells")
        return value


class Source(Contract):
    name: str = Field(max_length=160)
    url: str = Field(max_length=1000)
    observed_at: str = Field(max_length=40)

    @field_validator("url")
    @classmethod
    def public_https(cls, value):
        from urllib.parse import urlsplit

        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Source URL must be HTTPS without credentials")
        return value


class NewsItem(Contract):
    title: str = Field(max_length=300)
    publisher: str = Field(max_length=120)
    url: str = Field(max_length=1000)
    published_at: str = Field(default="", max_length=40)


class ResearchResult(Contract):
    question: str = Field(default="", max_length=1200)
    id: str = Field(pattern=r"^[a-f0-9-]{36}$")
    created_at: str
    mode: Literal["sample", "live"]
    ticker: str = Field(max_length=20)
    name: str = Field(max_length=160)
    currency: str = Field(max_length=12)
    description: str = Field(max_length=2400)
    sector: str = Field(default="", max_length=100)
    price: float | None = Field(default=None, ge=0)
    previous_close: float | None = Field(default=None, ge=0)
    price_as_of: str = Field(default="", max_length=40)
    price_kind: str = Field(default="unavailable", max_length=40)
    history: list[PricePoint] = Field(default_factory=list, max_length=260)
    metrics: list[Metric] = Field(default_factory=list, max_length=16)
    tables: list[DataTable] = Field(default_factory=list, max_length=16)
    news: list[NewsItem] = Field(default_factory=list, max_length=8)
    summary: str = Field(default="", max_length=16000)
    analysis_kind: Literal["reference", "evidence", "ai"] = "evidence"
    sources: list[Source] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=24)
