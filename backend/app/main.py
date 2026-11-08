import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import audio, health, places, scripts
from app.storage import MEDIA_URL_PREFIX

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Everything lives under /api so Caddy can route /api/* here and the rest to the web build.
app = FastAPI(
    title="Virtual Audioguide API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.include_router(health.router, prefix="/api")
app.include_router(places.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(audio.router, prefix="/api")

Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount(MEDIA_URL_PREFIX, StaticFiles(directory=settings.media_dir), name="media")
