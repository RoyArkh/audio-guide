import json

import httpx2
import pytest

from app import tts
from app.config import settings
from tests.fake_http import scripted_client
from tests.fake_tts import interaction_response, wav_file


def gemini(responses: list[httpx2.Response], requests: list | None = None) -> tts.GeminiTTS:
    return tts.GeminiTTS(scripted_client(responses, requests, base_url="https://gemini.test/v1beta"))


def test_synthesize_sends_text_style_voice_and_model_and_returns_pcm():
    requests = []

    pcm = gemini([interaction_response(wav_file(seconds=1.5))], requests).synthesize("Hello there.", "warm")

    assert len(pcm) == 1.5 * tts.BYTES_PER_SECOND
    assert requests[0].url.path == "/v1beta/interactions"
    body = json.loads(requests[0].content)
    assert body["model"] == settings.tts_model
    assert body["generation_config"]["speech_config"] == [{"voice": settings.tts_voice}]
    text_block = body["input"][0]["content"][0]
    assert text_block["text"] == "Hello there."
    assert text_block["annotations"] == [{"type": "speech_metadata", "style": "warm"}]


def test_synthesize_uses_the_last_audio_block():
    response = interaction_response(wav_file(seconds=1), wav_file(seconds=2))

    pcm = gemini([response]).synthesize("Hello", "warm")

    assert len(pcm) == 2 * tts.BYTES_PER_SECOND


def test_synthesize_retries_rate_limits():
    requests = []

    gemini([httpx2.Response(429), interaction_response(wav_file(seconds=1))], requests).synthesize("Hi", "warm")

    assert len(requests) == 2


def test_error_status_raises_tts_error():
    response = httpx2.Response(400, json={"error": {"message": "Unknown voice"}})

    with pytest.raises(tts.TTSError, match="Unknown voice"):
        gemini([response]).synthesize("Hi", "warm")


def test_response_without_audio_raises_tts_error():
    response = httpx2.Response(200, json={"steps": [
        {"type": "model_output", "content": [{"type": "text", "text": "Sorry, I can't."}]},
    ]})

    with pytest.raises(tts.TTSError, match="No audio"):
        gemini([response]).synthesize("Hi", "warm")


def test_audio_that_is_not_a_wav_file_raises_tts_error():
    with pytest.raises(tts.TTSError, match="not return a valid WAV"):
        gemini([interaction_response(b"\x00" * 100)]).synthesize("Hi", "warm")


def test_audio_with_an_unexpected_sample_rate_raises_tts_error():
    response = interaction_response(wav_file(seconds=1, sample_rate=16_000))

    with pytest.raises(tts.TTSError, match="16000"):
        gemini([response]).synthesize("Hi", "warm")


def test_missing_api_key_raises_tts_error(monkeypatch):
    monkeypatch.setattr(settings, "tts_api_key", "")

    with pytest.raises(tts.TTSError, match="TTS_API_KEY is not set"):
        gemini([]).synthesize("Hi", "warm")
