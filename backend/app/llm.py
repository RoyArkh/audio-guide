"""Minimal client for any OpenAI-compatible chat API (Gemini, OpenAI, Ollama)."""

import logging
import time
from collections.abc import Iterator

import httpx2

from app import retry
from app.config import settings

log = logging.getLogger(__name__)


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
    try:
        response = retry.post_with_retries(client, "/chat/completions", body)
    except httpx2.HTTPError as exc:
        raise LLMError(f"Request to the LLM failed: {exc}") from exc
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
