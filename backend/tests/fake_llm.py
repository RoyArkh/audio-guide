"""A fake OpenAI-compatible chat API so tests don't need a real LLM."""

import json

import httpx2


def chat_response(content: str) -> httpx2.Response:
    return httpx2.Response(200, json={"choices": [{"message": {"role": "assistant", "content": content}}]})


def fake_llm_client(responses: list[httpx2.Response],
                    requests: list[httpx2.Request] | None = None) -> httpx2.Client:
    """Returns the responses in order, and records each request if a list is given."""
    remaining = list(responses)

    def handler(request: httpx2.Request) -> httpx2.Response:
        if requests is not None:
            requests.append(request)
        return remaining.pop(0)

    return httpx2.Client(base_url="https://llm.test/v1", transport=httpx2.MockTransport(handler))


def user_prompt(request: httpx2.Request) -> str:
    return json.loads(request.content)["messages"][1]["content"]
