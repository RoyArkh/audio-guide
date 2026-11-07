# Official image (multi-arch) + extensions from the PostgreSQL apt repo it already uses.
FROM postgres:18-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-${PG_MAJOR}-postgis-3 \
        postgresql-${PG_MAJOR}-pgvector \
    && rm -rf /var/lib/apt/lists/*
