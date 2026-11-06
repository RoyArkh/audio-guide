"""App settings, read from environment variables (see .env.example at the repo root)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # e.g. postgresql+psycopg://user:password@db:5432/audioguide
    # ("db" is the Postgres service name on the Docker Compose network).
    database_url: str
    app_env: str = "dev"


settings = Settings()
