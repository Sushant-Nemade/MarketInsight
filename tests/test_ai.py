import asyncio
import json

import httpx
import pytest
from openai import AsyncOpenAI

from MarketInsight import research
from MarketInsight.sample import sample_reports


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("MARKET_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    monkeypatch.setenv("MARKET_MODEL", "fixture-model")


def test_actual_sdk_request_is_grounded_bounded_and_fixed_origin(configured, monkeypatch):
    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "id": "fixture",
                "object": "chat.completion",
                "created": 1,
                "model": "fixture-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "Evidence-grounded fixture summary."},
                    }
                ],
            },
        )

    def client():
        return AsyncOpenAI(
            api_key="fixture",
            base_url="https://api.openai.com/v1",
            max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        )

    monkeypatch.setattr(research, "ai_client", client)
    answer = asyncio.run(research.synthesize(sample_reports()[0], "Summarize this evidence"))
    assert answer == "Evidence-grounded fixture summary."
    assert captured[0].url.host == "api.openai.com"
    body = json.loads(captured[0].content)
    assert body["max_completion_tokens"] == 2048
    assert "Source" not in body.get("tools", {})
    assert "Evidence JSON" in body["messages"][1]["content"]
    assert "untrusted" in body["messages"][0]["content"]


def test_truncated_ai_output_is_not_published(configured, monkeypatch):
    def client():
        return AsyncOpenAI(
            api_key="fixture",
            base_url="https://api.openai.com/v1",
            max_retries=0,
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(
                        200,
                        json={
                            "id": "fixture",
                            "object": "chat.completion",
                            "created": 1,
                            "model": "fixture",
                            "choices": [
                                {
                                    "index": 0,
                                    "finish_reason": "length",
                                    "message": {"role": "assistant", "content": "Incomplete"},
                                }
                            ],
                        },
                    )
                )
            ),
        )

    monkeypatch.setattr(research, "ai_client", client)
    with pytest.raises(ValueError, match="truncated"):
        asyncio.run(research.synthesize(sample_reports()[0], "Research"))


def test_provider_errors_are_redacted(configured, monkeypatch):
    def client():
        return AsyncOpenAI(
            api_key="fixture",
            base_url="https://api.openai.com/v1",
            max_retries=0,
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(
                        401,
                        json={
                            "error": {"message": "secret-provider-details", "type": "authentication_error"}
                        },
                    )
                )
            ),
        )

    monkeypatch.setattr(research, "ai_client", client)
    with pytest.raises(ValueError) as caught:
        asyncio.run(research.synthesize(sample_reports()[0], "Research"))
    assert "secret-provider-details" not in str(caught.value)
