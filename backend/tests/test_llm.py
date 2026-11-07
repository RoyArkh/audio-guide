import json

import httpx2
import pytest

from app import llm
from app.config import settings
from tests.fake_llm import chat_response, fake_llm_client


@pytest.fixture(autouse=True)
def no_retry_delays(monkeypatch):
    monkeypatch.setattr(llm, "RETRY_DELAYS_S", [0, 0, 0])


def test_chat_sends_model_and_messages_and_returns_the_reply():
    requests = []
    client = fake_llm_client([chat_response("  Hello!  ")], requests)

    reply = llm.chat(client, "Be brief.", "Say hello.")

    assert reply == "Hello!"
    assert requests[0].url.path == "/v1/chat/completions"
    body = json.loads(requests[0].content)
    assert body["model"] == settings.llm_model
    assert body["messages"] == [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "Say hello."},
    ]


def test_chat_retries_rate_limits_and_server_errors():
    requests = []
    client = fake_llm_client([httpx2.Response(429), httpx2.Response(503), chat_response("Finally")], requests)

    assert llm.chat(client, "system", "user") == "Finally"
    assert len(requests) == 3


def test_chat_gives_up_after_the_last_retry():
    requests = []
    client = fake_llm_client([httpx2.Response(429)] * 4, requests)

    with pytest.raises(llm.LLMError, match="429"):
        llm.chat(client, "system", "user")
    assert len(requests) == 4


def test_chat_does_not_retry_other_errors():
    requests = []
    client = fake_llm_client([httpx2.Response(400, json={"error": {"message": "API key not valid"}})], requests)

    with pytest.raises(llm.LLMError, match="API key not valid"):
        llm.chat(client, "system", "user")
    assert len(requests) == 1


def test_chat_raises_when_the_api_key_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")

    with pytest.raises(llm.LLMError, match="LLM_API_KEY is not set"):
        llm.chat(fake_llm_client([]), "system", "user")


def test_chat_raises_on_empty_reply():
    with pytest.raises(llm.LLMError, match="empty"):
        llm.chat(fake_llm_client([chat_response("")]), "system", "user")
