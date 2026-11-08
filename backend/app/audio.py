"""Turn a script into one MP3: split it into chunks, speak each chunk, join them and encode."""

import logging
import re
import subprocess
from dataclasses import dataclass

from app.scripts import Mood
from app.tts import BYTES_PER_SECOND, SAMPLE_RATE, TTSProvider

log = logging.getLogger(__name__)

# About 500 words or 3 minutes of speech; one TTS call returns at most about 8 minutes.
MAX_CHUNK_CHARS = 3000
PAUSE_BETWEEN_CHUNKS_S = 0.6
MP3_BITRATE = "64k"  # plenty for a single voice

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

VOICE_STYLES = {
    Mood.HISTORICAL: "calm, clear and informative, like a museum guide",
    Mood.HISTORICAL_EMOTIONAL: "warm and engaging, with gentle humour and heartfelt moments",
    Mood.ROMANTIC: "warm, soft and tender",
}


class AudioError(Exception):
    pass


@dataclass(frozen=True)
class Audio:
    mp3: bytes
    duration_seconds: float
    chunks: int


def make_audio(tts: TTSProvider, script: str, mood: Mood) -> Audio:
    chunks = split_into_chunks(script)
    if not chunks:
        raise AudioError("The script is empty")

    spoken = []
    for number, chunk in enumerate(chunks, start=1):
        log.info("Speaking chunk %d of %d (%d characters)", number, len(chunks), len(chunk))
        spoken.append(tts.synthesize(chunk, VOICE_STYLES[mood]))

    pcm = silence(PAUSE_BETWEEN_CHUNKS_S).join(spoken)
    mp3 = encode_mp3(pcm)
    duration_s = len(pcm) / BYTES_PER_SECOND
    log.info("Made %.1f s of audio from %d chunks (%d KB MP3)", duration_s, len(chunks), len(mp3) // 1024)
    return Audio(mp3=mp3, duration_seconds=round(duration_s, 1), chunks=len(chunks))


def split_into_chunks(script: str) -> list[str]:
    """Group paragraphs into chunks of up to MAX_CHUNK_CHARS.
    A paragraph that is too long on its own is split between sentences."""
    pieces = []
    for line in script.splitlines():
        paragraph = line.strip()
        if len(paragraph) > MAX_CHUNK_CHARS:
            pieces.extend(SENTENCE_END.split(paragraph))
        elif paragraph:
            pieces.append(paragraph)

    chunks = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = piece
        elif current:
            current += "\n\n" + piece
        else:
            current = piece
    if current:
        chunks.append(current)
    return chunks


def silence(seconds: float) -> bytes:
    return b"\x00\x00" * int(seconds * SAMPLE_RATE)


def encode_mp3(pcm: bytes) -> bytes:
    command = [
        "ffmpeg", "-loglevel", "error",
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "pipe:0",  # raw PCM in
        "-b:a", MP3_BITRATE, "-f", "mp3", "pipe:1",  # MP3 out
    ]
    try:
        result = subprocess.run(command, input=pcm, capture_output=True)
    except FileNotFoundError as exc:
        raise AudioError("ffmpeg is not installed") from exc
    if result.returncode != 0:
        raise AudioError(f"ffmpeg failed: {result.stderr.decode(errors='replace')[:500]}")
    return result.stdout
