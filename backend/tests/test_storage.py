import pytest
from botocore.stub import Stubber

from app.config import settings
from app.storage import R2_LINK_LIFETIME_S, LocalStorage, R2Storage, make_r2_client


def test_local_storage_saves_into_subfolders_and_builds_the_url(tmp_path):
    storage = LocalStorage(tmp_path)

    storage.save("audio/abc.mp3", b"mp3 data")

    assert (tmp_path / "audio" / "abc.mp3").read_bytes() == b"mp3 data"
    assert storage.url("audio/abc.mp3") == "/api/media/audio/abc.mp3"


def r2_storage(monkeypatch) -> R2Storage:
    monkeypatch.setattr(settings, "r2_account_id", "account")
    monkeypatch.setattr(settings, "r2_access_key_id", "key-id")
    monkeypatch.setattr(settings, "r2_secret_access_key", "secret")
    monkeypatch.setattr(settings, "r2_bucket", "audio-guide")
    return R2Storage(make_r2_client(), settings.r2_bucket)


def test_r2_storage_uploads_with_the_right_content_type(monkeypatch):
    storage = r2_storage(monkeypatch)

    with Stubber(storage.client) as stubber:
        expected = {"Bucket": "audio-guide", "Key": "audio/abc.mp3", "Body": b"mp3 data", "ContentType": "audio/mpeg"}
        stubber.add_response("put_object", {}, expected)
        storage.save("audio/abc.mp3", b"mp3 data")
        stubber.assert_no_pending_responses()


def test_r2_storage_links_are_signed_and_expire(monkeypatch):
    url = r2_storage(monkeypatch).url("audio/abc.mp3")

    assert url.startswith("https://")
    assert "account.r2.cloudflarestorage.com" in url
    assert "audio-guide" in url and "audio/abc.mp3" in url
    assert "X-Amz-Signature=" in url
    assert f"X-Amz-Expires={R2_LINK_LIFETIME_S}" in url


def test_r2_storage_needs_its_settings(monkeypatch):
    monkeypatch.setattr(settings, "r2_secret_access_key", "")

    with pytest.raises(RuntimeError, match="R2_SECRET_ACCESS_KEY"):
        make_r2_client()
