"""Where audio files (and database backups) are kept: a local folder in dev, Cloudflare R2 in production."""

import logging
import mimetypes
from functools import cache
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config

from app.config import settings

log = logging.getLogger(__name__)

MEDIA_URL_PREFIX = "/api/media"
# Long enough to listen; reloading the story page gives a fresh link.
R2_LINK_LIFETIME_S = 24 * 60 * 60


class Storage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...

    def url(self, key: str) -> str: ...


class LocalStorage:
    """Files in a folder that the API serves at MEDIA_URL_PREFIX (see main.py)."""

    def __init__(self, folder: Path):
        self.folder = folder

    def save(self, key: str, data: bytes) -> None:
        path = self.folder / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        log.info("Saved %s (%d KB)", path, len(data) // 1024)

    def url(self, key: str) -> str:
        return f"{MEDIA_URL_PREFIX}/{key}"


class R2Storage:
    """A private R2 bucket. R2 speaks the S3 API, so boto3 works with it.
    Listeners get signed links that expire after R2_LINK_LIFETIME_S."""

    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def save(self, key: str, data: bytes) -> None:
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        log.info("Saved %s to R2 bucket %s (%d KB)", key, self.bucket, len(data) // 1024)

    def url(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=R2_LINK_LIFETIME_S,
        )


def make_r2_client():
    required = {
        "R2_ACCOUNT_ID": settings.r2_account_id,
        "R2_ACCESS_KEY_ID": settings.r2_access_key_id,
        "R2_SECRET_ACCESS_KEY": settings.r2_secret_access_key,
        "R2_BUCKET": settings.r2_bucket,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"STORAGE=r2 needs {', '.join(missing)} in .env")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        config=Config(
            retries={"max_attempts": 5, "mode": "standard"},
            # Skip the newer optional S3 checksum headers, which R2 may not accept.
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


@cache
def get_storage() -> Storage:
    """FastAPI dependency, created once; tests override it with a temporary folder."""
    if settings.storage == "r2":
        return R2Storage(make_r2_client(), settings.r2_bucket)
    if settings.storage == "local":
        return LocalStorage(Path(settings.media_dir))
    raise RuntimeError(f"Unknown STORAGE={settings.storage!r}: use local or r2")
