"""A fake OpenAI-compatible chat API so tests don't need a real LLM."""

import json

import httpx2

from tests.fake_http import scripted_client


def chat_response(content: str) -> httpx2.Response:
    return httpx2.Response(200, json={"choices": [{"message": {"role": "assistant", "content": content}}]})


def fake_llm_client(responses: list[httpx2.Response],
                    requests: list[httpx2.Request] | None = None) -> httpx2.Client:
    return scripted_client(responses, requests, base_url="https://llm.test/v1")


def user_prompt(request: httpx2.Request) -> str:
    return json.loads(request.content)["messages"][1]["content"]
