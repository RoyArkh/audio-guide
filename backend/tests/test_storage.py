from app.storage import LocalStorage


def test_local_storage_saves_into_subfolders_and_builds_the_url(tmp_path):
    storage = LocalStorage(tmp_path)

    storage.save("audio/abc.mp3", b"mp3 data")

    assert (tmp_path / "audio" / "abc.mp3").read_bytes() == b"mp3 data"
    assert storage.url("audio/abc.mp3") == "/api/media/audio/abc.mp3"
