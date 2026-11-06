"""Database engine, session factory, and the declarative base for models."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# A small pool: the production server has 1 GB RAM and Postgres is capped
# at a low max_connections, so we only keep a few connections open.
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,  # drop dead connections (e.g. after a DB restart) before use
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """All ORM models inherit from this, which lets Alembic discover them."""


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed afterwards."""
    with SessionLocal() as session:
        yield session
