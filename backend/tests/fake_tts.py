"""Fake text-to-speech so tests never call Gemini."""

import base64
import io
import wave

import httpx2

from app.tts import SAMPLE_RATE, TTSError


def wav_file(seconds: float, sample_rate: int = SAMPLE_RATE) -> bytes:
    """A 16-bit mono WAV file of silence."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return buffer.getvalue()


def interaction_response(*audio_files: bytes) -> httpx2.Response:
    """A Gemini Interactions API response with one audio block per file."""
    audio_blocks = [{"type": "audio", "data": base64.b64encode(f).decode()} for f in audio_files]
    return httpx2.Response(200, json={"steps": [
        {"type": "user_input", "content": [{"type": "text", "text": "The script"}]},
        {"type": "model_output", "content": audio_blocks},
    ]})


class FakeTTS:
    """Speaks every chunk as one second of silence and records each call."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, style: str) -> bytes:
        self.calls.append((text, style))
        return b"\x00\x00" * SAMPLE_RATE


class FailingTTS:
    def synthesize(self, text: str, style: str) -> bytes:
        raise TTSError("Gemini TTS returned 503")
