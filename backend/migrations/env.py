"""Alembic environment: tells Alembic how to connect and which models to compare against."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Models register themselves on Base.metadata; `alembic revision --autogenerate`
# compares this metadata with the live database to draft a migration.
target_metadata = Base.metadata

# Tables created by extensions (not by us). Without this, autogenerate would
# propose dropping PostGIS's `spatial_ref_sys` table.
EXTENSION_TABLES = {"spatial_ref_sys"}


def include_name(name, type_, parent_names):
    if type_ == "table":
        return name not in EXTENSION_TABLES
    return True


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        include_name=include_name,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    engine = create_engine(settings.database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
