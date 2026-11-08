"""Where audio files are kept: a local folder in dev. Cloudflare R2 comes with the deploy (M6)."""

import logging
from pathlib import Path
from typing import Protocol

from app.config import settings

log = logging.getLogger(__name__)

MEDIA_URL_PREFIX = "/api/media"


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


def get_storage() -> Storage:
    """FastAPI dependency; tests override it with a temporary folder."""
    return LocalStorage(Path(settings.media_dir))
