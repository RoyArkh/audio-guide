"""Minimal client for any OpenAI-compatible chat API (Gemini, OpenAI, Ollama)."""

import logging
import time
from collections.abc import Iterator

import httpx2

from app.config import settings

log = logging.getLogger(__name__)

# Rate limits (429) and overloaded servers (5xx) usually clear up after a short wait.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS_S = [2, 8, 30]


class LLMError(Exception):
    pass


def make_client() -> httpx2.Client:
    return httpx2.Client(
        base_url=settings.llm_base_url,
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        timeout=120.0,
    )


def get_client() -> Iterator[httpx2.Client]:
    """FastAPI dependency; tests override it with a mock client."""
    with make_client() as client:
        yield client


def chat(client: httpx2.Client, system_prompt: str, user_prompt: str) -> str:
    """Send a system and a user message, and return the model's reply."""
    if not settings.llm_api_key:
        raise LLMError("LLM_API_KEY is not set: add it to .env (for Ollama, any value works)")

    body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    started = time.monotonic()
    response = _post_with_retries(client, body)
    if response.is_error:
        raise LLMError(f"LLM returned {response.status_code}: {response.text[:500]}")

    try:
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"Unexpected LLM response: {response.text[:500]}") from exc
    if not reply:  # e.g. blocked by a safety filter
        raise LLMError(f"LLM returned an empty reply: {response.text[:500]}")

    usage = data.get("usage", {})
    log.info(
        "%s replied in %.1f s (%s tokens in, %s out)",
        settings.llm_model, time.monotonic() - started,
        usage.get("prompt_tokens"), usage.get("completion_tokens"),
    )
    return reply.strip()


def _post_with_retries(client: httpx2.Client, body: dict) -> httpx2.Response:
    for delay_s in RETRY_DELAYS_S:
        response = _post(client, body)
        if response.status_code not in RETRYABLE_STATUS_CODES:
            return response
        log.warning("LLM returned %d, retrying in %d s", response.status_code, delay_s)
        time.sleep(delay_s)
    return _post(client, body)


def _post(client: httpx2.Client, body: dict) -> httpx2.Response:
    try:
        return client.post("/chat/completions", json=body)
    except httpx2.HTTPError as exc:
        raise LLMError(f"Request to the LLM failed: {exc}") from exc
