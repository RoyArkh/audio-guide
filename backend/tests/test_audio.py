import pytest

from app import audio
from app.scripts import Mood
from app.tts import SAMPLE_RATE
from tests.fake_tts import FakeTTS


def test_short_script_is_one_chunk_and_blank_lines_are_dropped():
    assert audio.split_into_chunks("First.\n\n\n  Second.  \n") == ["First.\n\nSecond."]


def test_paragraphs_are_grouped_up_to_the_chunk_size(monkeypatch):
    monkeypatch.setattr(audio, "MAX_CHUNK_CHARS", 30)

    chunks = audio.split_into_chunks("A" * 10 + "\n" + "B" * 10 + "\n" + "C" * 10)

    assert chunks == ["A" * 10 + "\n\n" + "B" * 10, "C" * 10]


def test_paragraph_longer_than_a_chunk_is_split_between_sentences(monkeypatch):
    monkeypatch.setattr(audio, "MAX_CHUNK_CHARS", 30)

    chunks = audio.split_into_chunks("This is sentence one. This is sentence two! Is this three?")

    assert chunks == ["This is sentence one.", "This is sentence two!", "Is this three?"]


def test_make_audio_speaks_each_chunk_in_the_mood_style_and_joins_them(monkeypatch):
    monkeypatch.setattr(audio, "MAX_CHUNK_CHARS", 30)
    fake_tts = FakeTTS()

    result = audio.make_audio(fake_tts, "A" * 20 + "\n\n" + "B" * 20, Mood.ROMANTIC)

    assert fake_tts.calls == [
        ("A" * 20, audio.VOICE_STYLES[Mood.ROMANTIC]),
        ("B" * 20, audio.VOICE_STYLES[Mood.ROMANTIC]),
    ]
    assert result.chunks == 2
    assert result.duration_seconds == 2 + audio.PAUSE_BETWEEN_CHUNKS_S
    assert result.mp3.startswith(b"ID3")


def test_make_audio_rejects_an_empty_script():
    with pytest.raises(audio.AudioError, match="empty"):
        audio.make_audio(FakeTTS(), " \n\n ", Mood.HISTORICAL)


def test_encode_mp3_uses_about_64_kbps():
    two_seconds = b"\x00\x00" * SAMPLE_RATE * 2

    mp3 = audio.encode_mp3(two_seconds)

    assert mp3.startswith(b"ID3")
    assert 12_000 < len(mp3) < 20_000  # 64 kbps * 2 s = 16 KB
