"""Text-to-speech providers. Every provider returns 16-bit mono PCM at SAMPLE_RATE,
so chunks can be joined and encoded the same way whatever the provider."""

import base64
import io
import logging
import time
import wave
from collections.abc import Iterator
from typing import Protocol

import httpx2

from app import retry
from app.config import settings

log = logging.getLogger(__name__)

SAMPLE_RATE = 24_000
SAMPLE_WIDTH = 2  # bytes, i.e. 16-bit
BYTES_PER_SECOND = SAMPLE_RATE * SAMPLE_WIDTH  # mono

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"


class TTSError(Exception):
    pass


class TTSProvider(Protocol):
    def synthesize(self, text: str, style: str) -> bytes:
        """Speak the text in a style such as "warm and friendly"; returns PCM."""
        ...


class GeminiTTS:
    """Gemini TTS via the Interactions API: https://aistudio.google.com/docs/speech-generation"""

    def __init__(self, client: httpx2.Client):
        self.client = client

    def synthesize(self, text: str, style: str) -> bytes:
        if not settings.tts_api_key:
            raise TTSError("TTS_API_KEY is not set: add it to .env")

        body = {
            "model": settings.tts_model,
            "input": [{
                "type": "user_input",
                "content": [{
                    "type": "text",
                    "text": text,
                    "annotations": [{"type": "speech_metadata", "style": style}],
                }],
            }],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": settings.tts_voice}]},
        }
        started = time.monotonic()
        try:
            response = retry.post_with_retries(self.client, "/interactions", body)
        except httpx2.HTTPError as exc:
            raise TTSError(f"Request to Gemini TTS failed: {exc}") from exc
        if response.is_error:
            raise TTSError(f"Gemini TTS returned {response.status_code}: {response.text[:500]}")

        try:
            data = response.json()
        except ValueError as exc:
            raise TTSError(f"Gemini TTS returned invalid JSON: {response.text[:500]}") from exc

        pcm = wav_to_pcm(find_audio(data))
        log.info(
            "%s spoke %d characters as %.1f s of audio, in %.1f s",
            settings.tts_model, len(text), len(pcm) / BYTES_PER_SECOND, time.monotonic() - started,
        )
        return pcm


def find_audio(data: dict) -> bytes:
    """The last audio block in the model's output, decoded from base64."""
    audio = None
    for step in data.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for block in step.get("content", []):
            if block.get("type") == "audio":
                audio = block.get("data")

    if not audio:
        raise TTSError(f"No audio in the Gemini TTS response: {str(data)[:500]}")
    return base64.b64decode(audio)


def wav_to_pcm(wav_file: bytes) -> bytes:
    """Check the WAV has the format we join and encode, and return its samples."""
    try:
        with wave.open(io.BytesIO(wav_file)) as wav:
            audio_format = (wav.getframerate(), wav.getsampwidth(), wav.getnchannels())
            pcm = wav.readframes(wav.getnframes())
    except (wave.Error, EOFError) as exc:
        raise TTSError(f"Gemini TTS did not return a valid WAV file: {exc}") from exc

    expected = (SAMPLE_RATE, SAMPLE_WIDTH, 1)
    if audio_format != expected:
        raise TTSError(f"Expected audio as (rate, sample width, channels) {expected}, got {audio_format}")
    return pcm


def get_tts() -> Iterator[TTSProvider]:
    """FastAPI dependency; tests override it with a fake provider."""
    headers = {"x-goog-api-key": settings.tts_api_key}
    with httpx2.Client(base_url=GEMINI_API, headers=headers, timeout=180.0) as client:
        yield GeminiTTS(client)
