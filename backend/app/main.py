from fastapi import FastAPI

from app.routers import health

# Every route lives under /api so that, in production, Caddy can send /api/*
# to this app and everything else to the static web build.
app = FastAPI(
    title="Virtual Audioguide API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.include_router(health.router, prefix="/api")
