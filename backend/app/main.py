import logging

from fastapi import FastAPI

from app.routers import health, places

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
