import pytest
from fastapi.testclient import TestClient

from main import create_app
from MarketInsight.research import ReportStore

TOKEN = "fixture-" + "X" * 40
HEADERS = {"Authorization": "Bearer " + TOKEN}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKET_API_TOKEN", TOKEN)
    monkeypatch.delenv("MARKET_LIVE_DATA", raising=False)
    monkeypatch.delenv("MARKET_PROVIDER", raising=False)
    with TestClient(create_app(store=ReportStore(tmp_path / "reports.sqlite"))) as connection:
        yield connection


def test_public_sample_and_health_do_not_need_credentials(client):
    assert client.get("/health").status_code == 200
    response = client.get("/api/sample")
    assert response.status_code == 200 and len(response.json()) == 3
    assert all(report["mode"] == "sample" for report in response.json())


def test_reports_are_private(client):
    assert client.get("/api/reports").status_code == 401
    assert client.post("/api/research", json={"ticker": "DEMO-A"}).status_code == 401
    assert client.delete("/api/reports").status_code == 401


def test_complete_research_save_reopen_clear_workflow(client):
    response = client.post("/api/research", json={"ticker": "DEMO-A"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["analysis_kind"] == "reference"
    assert client.get("/api/reports", headers=HEADERS).json()[0]["id"] == report["id"]
    assert client.get("/api/reports/" + report["id"], headers=HEADERS).json()["ticker"] == "DEMO-A"
    assert client.delete("/api/reports", headers=HEADERS).status_code == 200
    assert client.get("/api/reports", headers=HEADERS).json() == []


def test_live_and_ai_fail_closed(client):
    assert (
        client.post(
            "/api/research", json={"ticker": "AAPL", "data_mode": "live"}, headers=HEADERS
        ).status_code
        == 503
    )
    assert (
        client.post("/api/research", json={"ticker": "DEMO-A", "analysis": "ai"}, headers=HEADERS).status_code
        == 503
    )
    assert client.get("/api/search?query=Apple", headers=HEADERS).status_code == 503


def test_search_is_authenticated_and_bounded(client):
    assert client.get("/api/search?query=Apple").status_code == 401
    assert client.get("/api/search?query=https://evil.example", headers=HEADERS).status_code == 422


def test_malformed_and_oversized_requests_are_bounded(client):
    assert client.post("/api/research", json={"ticker": "../etc"}, headers=HEADERS).status_code == 422
    assert client.post("/api/research", content=b"X" * 20_000, headers=HEADERS).status_code == 413
    assert client.get("/api/reports/not-a-uuid", headers=HEADERS).status_code == 422


def test_cors_and_security_headers(client):
    response = client.options(
        "/api/research", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"}
    )
    assert "access-control-allow-origin" not in response.headers
    response = client.get("/api/sample")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_rate_limit_is_enforced(client):
    for _ in range(12):
        assert client.post("/api/research", json={"ticker": "DEMO-A"}, headers=HEADERS).status_code == 200
    assert client.post("/api/research", json={"ticker": "DEMO-A"}, headers=HEADERS).status_code == 429


def test_invalid_token_and_missing_configuration(client, monkeypatch):
    assert client.get("/api/reports", headers={"Authorization": "Bearer wrong"}).status_code == 401
    monkeypatch.delenv("MARKET_API_TOKEN", raising=False)
    assert client.get("/api/reports").status_code == 503
