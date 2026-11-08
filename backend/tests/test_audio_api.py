from pathlib import Path

from fastapi.testclient import TestClient

from app import tts
from app.main import app
from app.storage import LocalStorage, get_storage
from tests.fake_tts import FailingTTS, FakeTTS


def api_client(tts_provider, storage) -> TestClient:
    app.dependency_overrides[tts.get_tts] = lambda: tts_provider
    app.dependency_overrides[get_storage] = lambda: storage
    return TestClient(app)


def test_create_audio_saves_an_mp3_and_returns_its_url(tmp_path):
    client = api_client(FakeTTS(), LocalStorage(tmp_path))

    response = client.post("/api/audio", json={"text": "Welcome.\n\nIt was built in 1889.", "mood": "historical"})

    assert response.status_code == 200
    body = response.json()
    assert body["chunks"] == 1
    assert body["duration_seconds"] == 1.0
    assert body["audio_url"].startswith("/api/media/audio/")
    saved_file = tmp_path / body["audio_url"].removeprefix("/api/media/")
    assert saved_file.read_bytes().startswith(b"ID3")


def test_create_audio_returns_502_and_saves_nothing_when_tts_fails(tmp_path):
    client = api_client(FailingTTS(), LocalStorage(tmp_path))

    response = client.post("/api/audio", json={"text": "Welcome.", "mood": "historical"})

    assert response.status_code == 502
    assert "503" in response.json()["detail"]
    assert list(tmp_path.iterdir()) == []


def test_create_audio_rejects_blank_text(tmp_path):
    client = api_client(FakeTTS(), LocalStorage(tmp_path))

    response = client.post("/api/audio", json={"text": "   ", "mood": "historical"})

    assert response.status_code == 422


def test_saved_audio_is_served_at_its_url():
    storage = get_storage()
    key = "audio/test-served.mp3"
    storage.save(key, b"fake mp3")
    try:
        response = TestClient(app).get(storage.url(key))
    finally:
        (Path(storage.folder) / key).unlink()

    assert response.status_code == 200
    assert response.content == b"fake mp3"
    assert response.headers["content-type"] == "audio/mpeg"
