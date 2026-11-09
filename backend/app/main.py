import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import stories
from app.config import settings
from app.db import SessionLocal
from app.routers import audio, health, places, scripts
from app.routers import stories as stories_router
from app.storage import MEDIA_URL_PREFIX, get_storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_storage()  # fail at startup, not on the first story, if the storage settings are wrong
    with SessionLocal() as session:
        interrupted = stories.fail_interrupted_jobs(session)
    if interrupted:
        log.warning("Marked %d jobs interrupted by the restart as failed", interrupted)
    yield


# Everything lives under /api so Caddy can route /api/* here and the rest to the web build.
app = FastAPI(
    title="Virtual Audioguide API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/api")
app.include_router(places.router, prefix="/api")
app.include_router(stories_router.router, prefix="/api")

if settings.app_env == "dev":
    # Single steps of the pipeline, for trying out prompts and voices. Production only
    # exposes /stories, so nobody can spend the API quota on arbitrary text.
    app.include_router(scripts.router, prefix="/api")
    app.include_router(audio.router, prefix="/api")

    # The Expo dev server (localhost:8081) calls the API on another port. In production
    # both come from the same domain, so no CORS is needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.storage == "local":
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    app.mount(MEDIA_URL_PREFIX, StaticFiles(directory=settings.media_dir), name="media")
